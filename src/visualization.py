import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import pytz
import numpy as np
from matplotlib.patches import Circle
import matplotlib.colors as mcolors

class StravaVisualizer:
    def __init__(self, data_file='data/activities.json'):
        self.data_file = data_file
        self.timezone = pytz.timezone('America/New_York')  # Adjust this to your timezone
        self.activities = self._load_data()
        self.df = self._prepare_dataframe()

    def _load_data(self):
        """Load activities from JSON file"""
        with open(self.data_file, 'r') as f:
            return json.load(f)

    def _prepare_dataframe(self):
        """Convert activities to pandas DataFrame with proper timezone handling"""
        df = pd.DataFrame(self.activities)
        df['start_date'] = pd.to_datetime(df['start_date']).dt.tz_convert(self.timezone)
        df['distance_miles'] = df['distance'] * 0.000621371  # Convert meters to miles
        df['moving_time_hours'] = df['moving_time'] / 3600
        df['elevation_gain_ft'] = df['total_elevation_gain'] * 3.28084  # Convert meters to feet
        df['speed_mph'] = df['distance_miles'] / df['moving_time_hours']  # Speed in mph
        df['year'] = df['start_date'].dt.year
        df['month'] = df['start_date'].dt.month
        df['day_of_week'] = df['start_date'].dt.day_name()
        df['hour'] = df['start_date'].dt.hour
        return df

    def plot_activity_bubbles(self):
        """Create a bubble chart of activities by type and distance"""
        plt.figure(figsize=(15, 10))
        
        # Group by activity type
        activity_groups = self.df.groupby('type').agg({
            'distance_miles': 'sum',
            'moving_time_hours': 'sum',
            'elevation_gain_ft': 'sum'
        }).reset_index()
        
        # Create bubble sizes based on total time
        bubble_sizes = activity_groups['moving_time_hours'] * 100
        
        # Create scatter plot
        scatter = plt.scatter(
            activity_groups['distance_miles'],
            activity_groups['elevation_gain_ft'],
            s=bubble_sizes,
            alpha=0.6,
            c=range(len(activity_groups)),
            cmap='viridis'
        )
        
        # Add labels
        for i, row in activity_groups.iterrows():
            plt.annotate(
                f"{row['type']}\n{row['distance_miles']:.0f}mi\n{row['moving_time_hours']:.0f}h",
                (row['distance_miles'], row['elevation_gain_ft']),
                ha='center',
                va='center'
            )
        
        plt.title('Activity Overview: Distance vs Elevation Gain\n(Bubble size = Time spent)')
        plt.xlabel('Total Distance (miles)')
        plt.ylabel('Total Elevation Gain (feet)')
        plt.grid(True, alpha=0.3)
        
        plt.savefig('output/activity_bubbles.png')
        plt.close()

    def plot_time_distribution(self):
        """Create a polar plot showing activity distribution by time of day"""
        plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, projection='polar')
        
        # Create 24-hour clock
        hours = np.linspace(0, 2*np.pi, 24, endpoint=False)
        
        # Count activities by hour
        activity_counts = self.df['hour'].value_counts().sort_index()
        
        # Create bars
        bars = ax.bar(hours, activity_counts, width=2*np.pi/24, alpha=0.7)
        
        # Customize the plot
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_xticks(hours)
        ax.set_xticklabels([f'{i}:00' for i in range(24)])
        ax.set_title('Activity Distribution by Time of Day')
        
        plt.savefig('output/time_distribution.png')
        plt.close()

    def plot_weekly_heatmap(self):
        """Create an enhanced heatmap of activities by day and hour"""
        df = self.df.copy()
        
        # Create pivot table for heatmap
        heatmap_data = pd.pivot_table(
            df,
            values='distance_miles',  # Changed from distance_km
            index='hour',
            columns='day_of_week',
            aggfunc='count',
            fill_value=0
        )
        
        # Reorder days of week
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data[days]
        
        plt.figure(figsize=(15, 10))
        sns.heatmap(
            heatmap_data,
            cmap='YlOrRd',
            annot=True,
            fmt='.0f',
            linewidths=.5,
            cbar_kws={'label': 'Number of Activities'}
        )
        plt.title('Activity Heatmap by Day and Hour')
        plt.xlabel('Day of Week')
        plt.ylabel('Hour of Day')
        plt.tight_layout()
        
        plt.savefig('output/weekly_heatmap.png')
        plt.close()

    def plot_monthly_stats(self):
        """Create a monthly statistics visualization"""
        monthly_stats = self.df.groupby(self.df['start_date'].dt.to_period('M')).agg({
            'distance_miles': 'sum',
            'moving_time_hours': 'sum',
            'elevation_gain_ft': 'sum',
            'type': 'count'
        }).reset_index()
        
        monthly_stats['start_date'] = monthly_stats['start_date'].astype(str)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Plot 1: Distance and Elevation
        ax1.bar(monthly_stats['start_date'], monthly_stats['distance_miles'], 
                label='Distance (miles)', alpha=0.7)
        ax1_twin = ax1.twinx()
        ax1_twin.plot(monthly_stats['start_date'], monthly_stats['elevation_gain_ft'], 
                     'r-', label='Elevation Gain (feet)')
        
        ax1.set_title('Monthly Distance and Elevation Gain')
        ax1.set_ylabel('Distance (miles)')
        ax1_twin.set_ylabel('Elevation Gain (feet)')
        ax1.legend(loc='upper left')
        ax1_twin.legend(loc='upper right')
        
        # Plot 2: Number of Activities and Time
        ax2.bar(monthly_stats['start_date'], monthly_stats['type'], 
                label='Number of Activities', alpha=0.7)
        ax2_twin = ax2.twinx()
        ax2_twin.plot(monthly_stats['start_date'], monthly_stats['moving_time_hours'], 
                     'g-', label='Moving Time (hours)')
        
        ax2.set_title('Monthly Activity Count and Moving Time')
        ax2.set_ylabel('Number of Activities')
        ax2_twin.set_ylabel('Moving Time (hours)')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        
        plt.tight_layout()
        plt.savefig('output/monthly_stats.png')
        plt.close()

    def generate_fun_stats(self):
        """Generate and save fun statistics about activities"""
        stats = {
            'Total Activities': len(self.df),
            'Total Distance (miles)': self.df['distance_miles'].sum(),
            'Total Moving Time (hours)': self.df['moving_time_hours'].sum(),
            'Total Elevation Gain (feet)': self.df['elevation_gain_ft'].sum(),
            'Average Speed (mph)': self.df['speed_mph'].mean(),
            'Most Active Day': self.df['day_of_week'].mode()[0],
            'Most Active Hour': f"{self.df['hour'].mode()[0]}:00",
            'Favorite Activity Type': self.df['type'].mode()[0],
            'Longest Activity (miles)': self.df['distance_miles'].max(),
            'Highest Elevation Gain (feet)': self.df['elevation_gain_ft'].max()
        }
        
        with open('output/fun_stats.txt', 'w') as f:
            f.write("Fun Strava Statistics\n")
            f.write("====================\n\n")
            for key, value in stats.items():
                if isinstance(value, float):
                    f.write(f"{key}: {value:.2f}\n")
                else:
                    f.write(f"{key}: {value}\n")

    def generate_all_visualizations(self):
        """Generate all visualizations"""
        os.makedirs('output', exist_ok=True)
        self.plot_activity_bubbles()
        self.plot_time_distribution()
        self.plot_weekly_heatmap()
        self.plot_monthly_stats()
        self.generate_fun_stats()
        print("All visualizations have been generated in the output directory")

def main():
    visualizer = StravaVisualizer()
    visualizer.generate_all_visualizations()

if __name__ == "__main__":
    main() 