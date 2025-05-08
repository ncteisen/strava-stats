import os
import json
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class StravaDataCollector:
    def __init__(self):
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        self.access_token = None
        self.activities = []
        
        # Validate environment variables
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.error("Missing required environment variables. Please check your .env file.")
            raise ValueError("Missing required environment variables")

    def get_access_token(self):
        """Get a new access token using the refresh token"""
        logger.info("Attempting to get new access token...")
        response = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            logger.info("Successfully obtained new access token")
            return True
        logger.error(f"Failed to get access token. Status code: {response.status_code}")
        return False

    def fetch_activities(self, per_page=100, max_pages=100):
        """Fetch activities from Strava API"""
        logger.info(f"Starting to fetch activities (per_page={per_page}, max_pages={max_pages})")
        
        if not self.access_token and not self.get_access_token():
            raise Exception("Failed to get access token")

        headers = {'Authorization': f'Bearer {self.access_token}'}
        page = 1
        total_activities = 0
        
        while page <= max_pages:
            logger.info(f"Fetching page {page} of activities...")
            response = requests.get(
                'https://www.strava.com/api/v3/athlete/activities',
                headers=headers,
                params={'per_page': per_page, 'page': page}
            )
            
            if response.status_code != 200:
                logger.error(f"Error fetching page {page}. Status code: {response.status_code}")
                break
                
            activities = response.json()
            if not activities:
                logger.info("No more activities to fetch")
                break
                
            self.activities.extend(activities)
            total_activities += len(activities)
            logger.info(f"Successfully fetched {len(activities)} activities from page {page}")
            page += 1

        logger.info(f"Completed fetching activities. Total activities collected: {total_activities}")

    def save_activities(self, filename='data/activities.json'):
        """Save activities to a JSON file"""
        logger.info(f"Attempting to save activities to {filename}")
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(self.activities, f, indent=2)
            logger.info(f"Successfully saved {len(self.activities)} activities to {filename}")
        except Exception as e:
            logger.error(f"Error saving activities to file: {str(e)}")
            raise

def main():
    try:
        logger.info("Starting Strava data collection process")
        collector = StravaDataCollector()
        collector.fetch_activities()
        collector.save_activities()
        logger.info("Data collection process completed successfully")
    except Exception as e:
        logger.error(f"An error occurred during data collection: {str(e)}")
        raise

if __name__ == "__main__":
    main() 