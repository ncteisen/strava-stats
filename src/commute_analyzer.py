import json
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

class CommuteAnalyzer:
    def __init__(self, data_file='data/activities.json', start_year=2023):
        self.data_file = data_file
        self.timezone = pytz.timezone('America/Los_Angeles')
        self.start_year = start_year
        self.activities = self._load_data()
        self.commutes = self._filter_commutes()
        self.to_work_commutes = []
        self.from_work_commutes = []
        self._categorize_commutes()
        
    def _load_data(self):
        """Load activities from JSON file"""
        with open(self.data_file, 'r') as f:
            return json.load(f)
    
    def _filter_commutes(self):
        """Filter activities to only include commutes after specified year"""
        filtered_commutes = []
        for activity in self.activities:
            # Check if it's a commute
            if not activity.get('commute'):
                continue
                
            # Check the date is after the start year
            start_date = datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')
            if start_date.year >= self.start_year:
                filtered_commutes.append(activity)
                
        return filtered_commutes
    
    def _categorize_commutes(self):
        """Categorize commutes as to work or from work based on start time"""
        for commute in self.commutes:
            # Convert start date to datetime object with timezone
            start_date = datetime.strptime(commute['start_date'], '%Y-%m-%dT%H:%M:%SZ')
            start_date = pytz.utc.localize(start_date).astimezone(self.timezone)
            
            # If start time is before noon, consider it a commute to work
            if start_date.hour < 12:
                self.to_work_commutes.append(commute)
            else:
                self.from_work_commutes.append(commute)
    
    def _meters_to_miles(self, meters):
        """Convert meters to miles"""
        return meters * 0.000621371
    
    def total_commutes(self):
        """Get total number of commutes"""
        return len(self.commutes)
    
    def total_distance_miles(self):
        """Get total distance of all commutes in miles"""
        total_meters = sum(c['distance'] for c in self.commutes)
        return self._meters_to_miles(total_meters)
    
    def average_commute_to_work(self):
        """Calculate average commute to work in miles and minutes"""
        if not self.to_work_commutes:
            return 0, 0, 0
        
        total_distance = sum(c['distance'] for c in self.to_work_commutes)
        total_moving_time = sum(c['moving_time'] for c in self.to_work_commutes)
        total_elapsed_time = sum(c['elapsed_time'] for c in self.to_work_commutes)
        
        avg_distance = self._meters_to_miles(total_distance / len(self.to_work_commutes))
        avg_moving_time = total_moving_time / len(self.to_work_commutes) / 60  # Convert to minutes
        avg_elapsed_time = total_elapsed_time / len(self.to_work_commutes) / 60  # Convert to minutes
        
        return avg_distance, avg_moving_time, avg_elapsed_time
    
    def average_commute_from_work(self):
        """Calculate average commute from work in miles and minutes"""
        if not self.from_work_commutes:
            return 0, 0, 0
        
        total_distance = sum(c['distance'] for c in self.from_work_commutes)
        total_moving_time = sum(c['moving_time'] for c in self.from_work_commutes)
        total_elapsed_time = sum(c['elapsed_time'] for c in self.from_work_commutes)
        
        avg_distance = self._meters_to_miles(total_distance / len(self.from_work_commutes))
        avg_moving_time = total_moving_time / len(self.from_work_commutes) / 60  # Convert to minutes
        avg_elapsed_time = total_elapsed_time / len(self.from_work_commutes) / 60  # Convert to minutes
        
        return avg_distance, avg_moving_time, avg_elapsed_time
    
    def _calculate_speed(self, commute):
        """Calculate speed in mph for a commute"""
        if commute['moving_time'] == 0:
            return 0
        
        distance_miles = self._meters_to_miles(commute['distance'])
        time_hours = commute['moving_time'] / 3600
        return distance_miles / time_hours
    
    def fastest_commute_to_work(self):
        """Find the fastest commute to work"""
        if not self.to_work_commutes:
            return None
        
        fastest = max(self.to_work_commutes, key=self._calculate_speed)
        return {
            'id': fastest['id'],
            'date': fastest['start_date'],
            'distance': self._meters_to_miles(fastest['distance']),
            'moving_time': fastest['moving_time'] / 60,  # Minutes
            'elapsed_time': fastest['elapsed_time'] / 60,  # Minutes
            'speed': self._calculate_speed(fastest),
            'link': f"https://www.strava.com/activities/{fastest['id']}"
        }
    
    def slowest_commute_to_work(self):
        """Find the slowest commute to work"""
        if not self.to_work_commutes:
            return None
        
        slowest = min(self.to_work_commutes, key=self._calculate_speed)
        return {
            'id': slowest['id'],
            'date': slowest['start_date'],
            'distance': self._meters_to_miles(slowest['distance']),
            'moving_time': slowest['moving_time'] / 60,  # Minutes
            'elapsed_time': slowest['elapsed_time'] / 60,  # Minutes
            'speed': self._calculate_speed(slowest),
            'link': f"https://www.strava.com/activities/{slowest['id']}"
        }
    
    def fastest_commute_from_work(self):
        """Find the fastest commute from work"""
        if not self.from_work_commutes:
            return None
        
        fastest = max(self.from_work_commutes, key=self._calculate_speed)
        return {
            'id': fastest['id'],
            'date': fastest['start_date'],
            'distance': self._meters_to_miles(fastest['distance']),
            'moving_time': fastest['moving_time'] / 60,  # Minutes
            'elapsed_time': fastest['elapsed_time'] / 60,  # Minutes
            'speed': self._calculate_speed(fastest),
            'link': f"https://www.strava.com/activities/{fastest['id']}"
        }
    
    def slowest_commute_from_work(self):
        """Find the slowest commute from work"""
        if not self.from_work_commutes:
            return None
        
        slowest = min(self.from_work_commutes, key=self._calculate_speed)
        return {
            'id': slowest['id'],
            'date': slowest['start_date'],
            'distance': self._meters_to_miles(slowest['distance']),
            'moving_time': slowest['moving_time'] / 60,  # Minutes
            'elapsed_time': slowest['elapsed_time'] / 60,  # Minutes
            'speed': self._calculate_speed(slowest),
            'link': f"https://www.strava.com/activities/{slowest['id']}"
        }
    
    def generate_analysis_text(self):
        """Generate text for commute analysis"""
        lines = []
        lines.append("\n===== STRAVA COMMUTE ANALYSIS =====\n")
        lines.append(f"Analysis for commutes from {self.start_year} onwards\n")
        
        lines.append(f"Total number of commutes: {self.total_commutes()}")
        lines.append(f"Total distance of commutes: {self.total_distance_miles():.2f} miles")
        
        to_work_distance, to_work_moving_time, to_work_elapsed_time = self.average_commute_to_work()
        lines.append(f"\nAverage commute TO work:")
        lines.append(f"  Distance: {to_work_distance:.2f} miles")
        lines.append(f"  Moving time: {to_work_moving_time:.2f} minutes")
        lines.append(f"  Elapsed time: {to_work_elapsed_time:.2f} minutes")
        lines.append(f"  Stop time: {(to_work_elapsed_time - to_work_moving_time):.2f} minutes")
        
        from_work_distance, from_work_moving_time, from_work_elapsed_time = self.average_commute_from_work()
        lines.append(f"\nAverage commute FROM work:")
        lines.append(f"  Distance: {from_work_distance:.2f} miles")
        lines.append(f"  Moving time: {from_work_moving_time:.2f} minutes")
        lines.append(f"  Elapsed time: {from_work_elapsed_time:.2f} minutes")
        lines.append(f"  Stop time: {(from_work_elapsed_time - from_work_moving_time):.2f} minutes")
        
        fastest_to = self.fastest_commute_to_work()
        if fastest_to:
            lines.append(f"\nFastest commute TO work: {fastest_to['speed']:.2f} mph")
            lines.append(f"  Date: {fastest_to['date']}")
            lines.append(f"  Distance: {fastest_to['distance']:.2f} miles")
            lines.append(f"  Moving time: {fastest_to['moving_time']:.2f} minutes")
            lines.append(f"  Elapsed time: {fastest_to['elapsed_time']:.2f} minutes")
            lines.append(f"  Stop time: {(fastest_to['elapsed_time'] - fastest_to['moving_time']):.2f} minutes")
            lines.append(f"  Link: {fastest_to['link']}")
        
        slowest_to = self.slowest_commute_to_work()
        if slowest_to:
            lines.append(f"\nSlowest commute TO work: {slowest_to['speed']:.2f} mph")
            lines.append(f"  Date: {slowest_to['date']}")
            lines.append(f"  Distance: {slowest_to['distance']:.2f} miles")
            lines.append(f"  Moving time: {slowest_to['moving_time']:.2f} minutes")
            lines.append(f"  Elapsed time: {slowest_to['elapsed_time']:.2f} minutes")
            lines.append(f"  Stop time: {(slowest_to['elapsed_time'] - slowest_to['moving_time']):.2f} minutes")
            lines.append(f"  Link: {slowest_to['link']}")
        
        fastest_from = self.fastest_commute_from_work()
        if fastest_from:
            lines.append(f"\nFastest commute FROM work: {fastest_from['speed']:.2f} mph")
            lines.append(f"  Date: {fastest_from['date']}")
            lines.append(f"  Distance: {fastest_from['distance']:.2f} miles")
            lines.append(f"  Moving time: {fastest_from['moving_time']:.2f} minutes")
            lines.append(f"  Elapsed time: {fastest_from['elapsed_time']:.2f} minutes")
            lines.append(f"  Stop time: {(fastest_from['elapsed_time'] - fastest_from['moving_time']):.2f} minutes")
            lines.append(f"  Link: {fastest_from['link']}")
        
        slowest_from = self.slowest_commute_from_work()
        if slowest_from:
            lines.append(f"\nSlowest commute FROM work: {slowest_from['speed']:.2f} mph")
            lines.append(f"  Date: {slowest_from['date']}")
            lines.append(f"  Distance: {slowest_from['distance']:.2f} miles")
            lines.append(f"  Moving time: {slowest_from['moving_time']:.2f} minutes")
            lines.append(f"  Elapsed time: {slowest_from['elapsed_time']:.2f} minutes")
            lines.append(f"  Stop time: {(slowest_from['elapsed_time'] - slowest_from['moving_time']):.2f} minutes")
            lines.append(f"  Link: {slowest_from['link']}")
        
        lines.append("\n===================================\n")
        
        return "\n".join(lines)
    
    def print_commute_analysis(self):
        """Print a text-based analysis of commutes"""
        analysis_text = self.generate_analysis_text()
        print(analysis_text)
        self.save_analysis_to_file(analysis_text)
    
    def save_analysis_to_file(self, analysis_text, filename=None):
        """Save the analysis to a text file"""
        if filename is None:
            # Create a filename with the date and year range
            current_date = datetime.now().strftime("%Y-%m-%d")
            filename = f"output/commute_analysis_{self.start_year}_to_present_{current_date}.txt"
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Write analysis to file
        with open(filename, 'w') as f:
            f.write(analysis_text)
        
        print(f"\nAnalysis saved to {filename}")

def main():
    analyzer = CommuteAnalyzer(start_year=2023)  # Only include commutes from 2023 onwards
    analyzer.print_commute_analysis()

if __name__ == "__main__":
    main() 