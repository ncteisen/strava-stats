import json
import os
from datetime import datetime, time
import pytz
from dotenv import load_dotenv
import statistics
from collections import namedtuple

DepartureTime = namedtuple('DepartureTime', ['datetime', 'time_string', 'activity_id', 'date'])

class CommuteAnalyzer:
    def __init__(self, data_file='data/activities.json', start_year=2025):
        self.data_file = data_file
        self.timezone = pytz.timezone('America/Los_Angeles')
        self.start_year = start_year
        self.activities = self._load_data()
        self.commutes = self._filter_commutes()
        self.to_work_commutes = []
        self.from_work_commutes = []
        self.to_work_departure_times = []
        self.from_work_departure_times = []
        self._categorize_commutes()
        
    def _format_date(self, iso_date):
        """Convert ISO date to M/D/YYYY format"""
        dt = datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime('%-m/%-d/%Y')
        
    def _format_time_of_day(self, dt):
        """Format datetime to time of day (e.g., '8:30 AM')"""
        return dt.strftime('%-I:%M %p')
        
    def _format_time(self, minutes):
        """Format time in minutes to 'Xmin Ysecs' format with appropriate units for larger time spans"""
        # Constants for time conversions
        MINUTES_IN_HOUR = 60
        HOURS_IN_DAY = 24
        DAYS_IN_YEAR = 365
        
        minutes_total = minutes
        
        # Convert to appropriate units
        if minutes_total < MINUTES_IN_HOUR:
            # Format as minutes and seconds
            mins = int(minutes_total)
            secs = int((minutes_total - mins) * 60)
            
            if mins == 0:
                return f"{secs}s"
            elif secs == 0:
                return f"{mins}m"
            else:
                return f"{mins}m {secs}s"
                
        elif minutes_total < MINUTES_IN_HOUR * HOURS_IN_DAY:
            # Format as hours and minutes
            hours = int(minutes_total / MINUTES_IN_HOUR)
            mins = int(minutes_total % MINUTES_IN_HOUR)
            
            if mins == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {mins}m"
                
        elif minutes_total < MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_YEAR:
            # Format as days and hours
            days = int(minutes_total / (MINUTES_IN_HOUR * HOURS_IN_DAY))
            hours = int((minutes_total % (MINUTES_IN_HOUR * HOURS_IN_DAY)) / MINUTES_IN_HOUR)
            
            if hours == 0:
                return f"{days}d"
            else:
                return f"{days}d {hours}h"
                
        else:
            # Format as years and days
            years = int(minutes_total / (MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_YEAR))
            days = int((minutes_total % (MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_YEAR)) / (MINUTES_IN_HOUR * HOURS_IN_DAY))
            
            if days == 0:
                return f"{years}y"
            else:
                return f"{years}y {days}d"
        
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
            start_date_str = commute['start_date']
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%SZ')
            start_date_tz = pytz.utc.localize(start_date).astimezone(self.timezone)
            
            # Create departure time object
            departure = DepartureTime(
                datetime=start_date_tz,
                time_string=self._format_time_of_day(start_date_tz),
                activity_id=commute['id'],
                date=self._format_date(start_date_str)
            )
            
            # If start time is before noon, consider it a commute to work
            if start_date_tz.hour < 12:
                self.to_work_commutes.append(commute)
                self.to_work_departure_times.append(departure)
            else:
                self.from_work_commutes.append(commute)
                self.from_work_departure_times.append(departure)
    
    def _meters_to_miles(self, meters):
        """Convert meters to miles"""
        return meters * 0.000621371
    
    def _average_time_of_day(self, departure_times):
        """Calculate the average time of day from a list of departure times"""
        if not departure_times:
            return None
            
        # Convert times to minutes since midnight for averaging
        minutes_list = [(dt.datetime.hour * 60 + dt.datetime.minute) for dt in departure_times]
        avg_minutes = sum(minutes_list) / len(minutes_list)
        
        # Convert back to hours and minutes
        hours = int(avg_minutes // 60)
        minutes = int(avg_minutes % 60)
        
        # Create a time object for formatting
        avg_time = time(hour=hours, minute=minutes)
        return avg_time.strftime('%-I:%M %p')
    
    def get_earliest_departure(self, departure_times):
        """Get the earliest departure time"""
        if not departure_times:
            return None
        return min(departure_times, key=lambda x: x.datetime.hour * 60 + x.datetime.minute)
    
    def get_latest_departure(self, departure_times):
        """Get the latest departure time"""
        if not departure_times:
            return None
        return max(departure_times, key=lambda x: x.datetime.hour * 60 + x.datetime.minute)
    
    def total_commutes(self):
        """Get total number of commutes"""
        return len(self.commutes)
    
    def total_distance_miles(self):
        """Get total distance of all commutes in miles"""
        total_meters = sum(c['distance'] for c in self.commutes)
        return self._meters_to_miles(total_meters)
    
    def total_elapsed_time(self):
        """Get total elapsed time of all commutes in minutes"""
        total_seconds = sum(c['elapsed_time'] for c in self.commutes)
        return total_seconds / 60  # Convert to minutes
    
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
        """Calculate speed in mph for a commute using moving time"""
        if commute['moving_time'] == 0:
            return 0
        
        distance_miles = self._meters_to_miles(commute['distance'])
        time_hours = commute['moving_time'] / 3600
        return distance_miles / time_hours
    
    def _calculate_elapsed_time_minutes(self, commute):
        """Calculate elapsed time in minutes for a commute"""
        return commute['elapsed_time'] / 60
    
    def fastest_commute_to_work(self):
        """Find the commute to work with shortest elapsed time"""
        if not self.to_work_commutes:
            return None
        
        # Sort by elapsed time (ascending)
        fastest = min(self.to_work_commutes, key=self._calculate_elapsed_time_minutes)
        moving_time_mins = fastest['moving_time'] / 60
        elapsed_time_mins = fastest['elapsed_time'] / 60
        
        return {
            'id': fastest['id'],
            'date': self._format_date(fastest['start_date']),
            'distance': self._meters_to_miles(fastest['distance']),
            'moving_time': moving_time_mins,
            'moving_time_formatted': self._format_time(moving_time_mins),
            'elapsed_time': elapsed_time_mins,
            'elapsed_time_formatted': self._format_time(elapsed_time_mins),
            'stop_time': elapsed_time_mins - moving_time_mins,
            'stop_time_formatted': self._format_time(elapsed_time_mins - moving_time_mins),
            'speed': self._calculate_speed(fastest),
            'link': f"https://www.strava.com/activities/{fastest['id']}"
        }
    
    def slowest_commute_to_work(self):
        """Find the commute to work with longest elapsed time"""
        if not self.to_work_commutes:
            return None
        
        # Sort by elapsed time (descending)
        slowest = max(self.to_work_commutes, key=self._calculate_elapsed_time_minutes)
        moving_time_mins = slowest['moving_time'] / 60
        elapsed_time_mins = slowest['elapsed_time'] / 60
        
        return {
            'id': slowest['id'],
            'date': self._format_date(slowest['start_date']),
            'distance': self._meters_to_miles(slowest['distance']),
            'moving_time': moving_time_mins,
            'moving_time_formatted': self._format_time(moving_time_mins),
            'elapsed_time': elapsed_time_mins,
            'elapsed_time_formatted': self._format_time(elapsed_time_mins),
            'stop_time': elapsed_time_mins - moving_time_mins,
            'stop_time_formatted': self._format_time(elapsed_time_mins - moving_time_mins),
            'speed': self._calculate_speed(slowest),
            'link': f"https://www.strava.com/activities/{slowest['id']}"
        }
    
    def fastest_commute_from_work(self):
        """Find the commute from work with shortest elapsed time"""
        if not self.from_work_commutes:
            return None
        
        # Sort by elapsed time (ascending)
        fastest = min(self.from_work_commutes, key=self._calculate_elapsed_time_minutes)
        moving_time_mins = fastest['moving_time'] / 60
        elapsed_time_mins = fastest['elapsed_time'] / 60
        
        return {
            'id': fastest['id'],
            'date': self._format_date(fastest['start_date']),
            'distance': self._meters_to_miles(fastest['distance']),
            'moving_time': moving_time_mins,
            'moving_time_formatted': self._format_time(moving_time_mins),
            'elapsed_time': elapsed_time_mins,
            'elapsed_time_formatted': self._format_time(elapsed_time_mins),
            'stop_time': elapsed_time_mins - moving_time_mins,
            'stop_time_formatted': self._format_time(elapsed_time_mins - moving_time_mins),
            'speed': self._calculate_speed(fastest),
            'link': f"https://www.strava.com/activities/{fastest['id']}"
        }
    
    def slowest_commute_from_work(self):
        """Find the commute from work with longest elapsed time"""
        if not self.from_work_commutes:
            return None
        
        # Sort by elapsed time (descending)
        slowest = max(self.from_work_commutes, key=self._calculate_elapsed_time_minutes)
        moving_time_mins = slowest['moving_time'] / 60
        elapsed_time_mins = slowest['elapsed_time'] / 60
        
        return {
            'id': slowest['id'],
            'date': self._format_date(slowest['start_date']),
            'distance': self._meters_to_miles(slowest['distance']),
            'moving_time': moving_time_mins,
            'moving_time_formatted': self._format_time(moving_time_mins),
            'elapsed_time': elapsed_time_mins,
            'elapsed_time_formatted': self._format_time(elapsed_time_mins),
            'stop_time': elapsed_time_mins - moving_time_mins,
            'stop_time_formatted': self._format_time(elapsed_time_mins - moving_time_mins),
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
        lines.append(f"Total elapsed time of commutes: {self._format_time(self.total_elapsed_time())}")

        # Add average departure times
        avg_to_work_time = self._average_time_of_day(self.to_work_departure_times)
        if avg_to_work_time:
            lines.append(f"\nAverage departure time TO work: {avg_to_work_time}")
            
        avg_from_work_time = self._average_time_of_day(self.from_work_departure_times)
        if avg_from_work_time:
            lines.append(f"Average departure time FROM work: {avg_from_work_time}")
        
        # Add earliest and latest departure times for to-work commutes
        earliest_to_work = self.get_earliest_departure(self.to_work_departure_times)
        if earliest_to_work:
            lines.append(f"\nEarliest departure TO work: {earliest_to_work.time_string}")
            lines.append(f"  Date: {earliest_to_work.date}")
            lines.append(f"  Link: https://www.strava.com/activities/{earliest_to_work.activity_id}")
            
        latest_to_work = self.get_latest_departure(self.to_work_departure_times)
        if latest_to_work:
            lines.append(f"\nLatest departure TO work: {latest_to_work.time_string}")
            lines.append(f"  Date: {latest_to_work.date}")
            lines.append(f"  Link: https://www.strava.com/activities/{latest_to_work.activity_id}")
            
        # Add earliest and latest departure times for from-work commutes
        earliest_from_work = self.get_earliest_departure(self.from_work_departure_times)
        if earliest_from_work:
            lines.append(f"\nEarliest departure FROM work: {earliest_from_work.time_string}")
            lines.append(f"  Date: {earliest_from_work.date}")
            lines.append(f"  Link: https://www.strava.com/activities/{earliest_from_work.activity_id}")
            
        latest_from_work = self.get_latest_departure(self.from_work_departure_times)
        if latest_from_work:
            lines.append(f"\nLatest departure FROM work: {latest_from_work.time_string}")
            lines.append(f"  Date: {latest_from_work.date}")
            lines.append(f"  Link: https://www.strava.com/activities/{latest_from_work.activity_id}")
        
        to_work_distance, to_work_moving_time, to_work_elapsed_time = self.average_commute_to_work()
        lines.append(f"\nAverage commute TO work:")
        lines.append(f"  Distance: {to_work_distance:.2f} miles")
        lines.append(f"  Moving time: {self._format_time(to_work_moving_time)}")
        lines.append(f"  Elapsed time: {self._format_time(to_work_elapsed_time)}")
        lines.append(f"  Stop time: {self._format_time(to_work_elapsed_time - to_work_moving_time)}")
        
        from_work_distance, from_work_moving_time, from_work_elapsed_time = self.average_commute_from_work()
        lines.append(f"\nAverage commute FROM work:")
        lines.append(f"  Distance: {from_work_distance:.2f} miles")
        lines.append(f"  Moving time: {self._format_time(from_work_moving_time)}")
        lines.append(f"  Elapsed time: {self._format_time(from_work_elapsed_time)}")
        lines.append(f"  Stop time: {self._format_time(from_work_elapsed_time - from_work_moving_time)}")
        
        fastest_to = self.fastest_commute_to_work()
        if fastest_to:
            lines.append(f"\nQuickest commute TO work (by elapsed time): {fastest_to['elapsed_time_formatted']}")
            lines.append(f"  Date: {fastest_to['date']}")
            lines.append(f"  Distance: {fastest_to['distance']:.2f} miles")
            lines.append(f"  Moving time: {fastest_to['moving_time_formatted']}")
            lines.append(f"  Elapsed time: {fastest_to['elapsed_time_formatted']}")
            lines.append(f"  Stop time: {fastest_to['stop_time_formatted']}")
            lines.append(f"  Link: {fastest_to['link']}")
        
        slowest_to = self.slowest_commute_to_work()
        if slowest_to:
            lines.append(f"\nLongest commute TO work (by elapsed time): {slowest_to['elapsed_time_formatted']}")
            lines.append(f"  Date: {slowest_to['date']}")
            lines.append(f"  Distance: {slowest_to['distance']:.2f} miles")
            lines.append(f"  Moving time: {slowest_to['moving_time_formatted']}")
            lines.append(f"  Elapsed time: {slowest_to['elapsed_time_formatted']}")
            lines.append(f"  Stop time: {slowest_to['stop_time_formatted']}")
            lines.append(f"  Link: {slowest_to['link']}")
        
        fastest_from = self.fastest_commute_from_work()
        if fastest_from:
            lines.append(f"\nQuickest commute FROM work (by elapsed time): {fastest_from['elapsed_time_formatted']}")
            lines.append(f"  Date: {fastest_from['date']}")
            lines.append(f"  Distance: {fastest_from['distance']:.2f} miles")
            lines.append(f"  Moving time: {fastest_from['moving_time_formatted']}")
            lines.append(f"  Elapsed time: {fastest_from['elapsed_time_formatted']}")
            lines.append(f"  Stop time: {fastest_from['stop_time_formatted']}")
            lines.append(f"  Link: {fastest_from['link']}")
        
        slowest_from = self.slowest_commute_from_work()
        if slowest_from:
            lines.append(f"\nLongest commute FROM work (by elapsed time): {slowest_from['elapsed_time_formatted']}")
            lines.append(f"  Date: {slowest_from['date']}")
            lines.append(f"  Distance: {slowest_from['distance']:.2f} miles")
            lines.append(f"  Moving time: {slowest_from['moving_time_formatted']}")
            lines.append(f"  Elapsed time: {slowest_from['elapsed_time_formatted']}")
            lines.append(f"  Stop time: {slowest_from['stop_time_formatted']}")
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
            # Use a fixed filename that will be overwritten each time
            filename = "output/commute_analysis.txt"
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Write analysis to file
        with open(filename, 'w') as f:
            f.write(analysis_text)
        
        print(f"\nAnalysis saved to {filename}")

def main():
    analyzer = CommuteAnalyzer(start_year=2025)  # Only include commutes from 2025 onwards
    analyzer.print_commute_analysis()

if __name__ == "__main__":
    main() 