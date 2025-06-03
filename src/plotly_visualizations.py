import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pytz
from datetime import datetime
import os

class InteractiveStravaVisualizer:
    def __init__(self, data_file='data/activities.json'):
        self.data_file = data_file
        self.timezone = pytz.timezone('America/New_York')
        self.activities = self._load_data()
        self.df = self._prepare_dataframe()

    def _load_data(self):
        with open(self.data_file, 'r') as f:
            return json.load(f)

    def _prepare_dataframe(self):
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
        df['date'] = df['start_date'].dt.date
        return df

    def create_activity_bubble_chart(self):
        """Create an interactive bubble chart of activities with filters"""
        activity_groups = self.df.groupby('type').agg({
            'distance_miles': 'sum',
            'moving_time_hours': 'sum',
            'elevation_gain_ft': 'sum',
            'speed_mph': 'mean',
            'date': 'count'
        }).reset_index()

        fig = px.scatter(
            activity_groups,
            x='distance_miles',
            y='elevation_gain_ft',
            size='moving_time_hours',
            color='type',
            hover_name='type',
            hover_data={
                'distance_miles': ':.1f',
                'elevation_gain_ft': ':.0f',
                'moving_time_hours': ':.1f',
                'speed_mph': ':.1f',
                'date': ':.0f'
            },
            title='Activity Overview: Distance vs Elevation Gain<br><sup>Bubble size represents time spent</sup>',
            labels={
                'distance_miles': 'Total Distance (miles)',
                'elevation_gain_ft': 'Total Elevation Gain (feet)',
                'moving_time_hours': 'Moving Time (hours)',
                'speed_mph': 'Average Speed (mph)',
                'date': 'Number of Activities'
            }
        )

        fig.update_layout(
            template='plotly_white',
            hovermode='closest',
            showlegend=True,
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    active=0,
                    x=0.57,
                    y=1.2,
                    buttons=list([
                        dict(
                            label="All Activities",
                            method="update",
                            args=[{"visible": [True] * len(activity_groups)}]
                        ),
                        dict(
                            label="Running",
                            method="update",
                            args=[{"visible": [t == "Run" for t in activity_groups['type']]}]
                        ),
                        dict(
                            label="Cycling",
                            method="update",
                            args=[{"visible": [t == "Ride" for t in activity_groups['type']]}]
                        )
                    ]),
                )
            ]
        )

        return fig

    def create_time_distribution_chart(self):
        """Create an interactive polar chart of activity times with filters"""
        hourly_counts = (
            self.df['hour']
            .value_counts()
            .reindex(range(24), fill_value=0)
            .sort_index()
        )

        weekday_counts = (
            self.df[self.df['day_of_week'].isin(
                ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            )]['hour']
            .value_counts()
            .reindex(range(24), fill_value=0)
            .sort_index()
        )

        weekend_counts = (
            self.df[self.df['day_of_week'].isin(['Saturday', 'Sunday'])]['hour']
            .value_counts()
            .reindex(range(24), fill_value=0)
            .sort_index()
        )
        
        fig = go.Figure()
        
        fig.add_trace(go.Barpolar(
            r=hourly_counts.values,
            theta=[i * 15 for i in range(24)],
            name='Activities',
            marker_color='rgb(158,202,225)',
            marker_line_color='rgb(8,48,107)',
            marker_line_width=1.5,
            opacity=0.8,
            hovertemplate="<b>Hour:</b> %{theta}<br>" +
                         "<b>Activities:</b> %{r}<br>" +
                         "<extra></extra>"
        ))
        
        fig.update_layout(
            title='Activity Distribution by Time of Day',
            template='plotly_white',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, hourly_counts.max()]
                ),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                    ticktext=['12 AM', '3 AM', '6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM'],
                    direction='clockwise'
                )
            ),
            showlegend=False,
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    active=0,
                    x=0.57,
                    y=1.2,
                    buttons=list([
                        dict(
                            label="All Days",
                            method="update",
                            args=[{"r": [hourly_counts.values]}]
                        ),
                        dict(
                            label="Weekdays",
                            method="update",
                            args=[{"r": [weekday_counts.values]}]
                        ),
                        dict(
                            label="Weekends",
                            method="update",
                            args=[{"r": [weekend_counts.values]}]
                        )
                    ]),
                )
            ]
        )
        
        return fig

    def create_monthly_stats_chart(self):
        """Create an interactive monthly statistics chart with range slider"""
        monthly_stats = self.df.groupby(self.df['start_date'].dt.to_period('M')).agg({
            'distance_miles': 'sum',
            'moving_time_hours': 'sum',
            'elevation_gain_ft': 'sum',
            'type': 'count',
            'speed_mph': 'mean'
        }).reset_index()
        
        monthly_stats['start_date'] = monthly_stats['start_date'].astype(str)
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Monthly Distance and Elevation', 'Monthly Activity Count and Time'),
            vertical_spacing=0.15
        )
        
        # Add distance bar chart
        fig.add_trace(
            go.Bar(
                x=monthly_stats['start_date'],
                y=monthly_stats['distance_miles'],
                name='Distance (miles)',
                marker_color='rgb(55, 83, 109)',
                hovertemplate="<b>Month:</b> %{x}<br>" +
                             "<b>Distance:</b> %{y:.1f} miles<br>" +
                             "<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Add elevation line
        fig.add_trace(
            go.Scatter(
                x=monthly_stats['start_date'],
                y=monthly_stats['elevation_gain_ft'],
                name='Elevation Gain (feet)',
                line=dict(color='rgb(255, 0, 0)'),
                hovertemplate="<b>Month:</b> %{x}<br>" +
                             "<b>Elevation Gain:</b> %{y:.0f} feet<br>" +
                             "<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Add activity count bar chart
        fig.add_trace(
            go.Bar(
                x=monthly_stats['start_date'],
                y=monthly_stats['type'],
                name='Activity Count',
                marker_color='rgb(26, 118, 255)',
                hovertemplate="<b>Month:</b> %{x}<br>" +
                             "<b>Activities:</b> %{y}<br>" +
                             "<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Add moving time line
        fig.add_trace(
            go.Scatter(
                x=monthly_stats['start_date'],
                y=monthly_stats['moving_time_hours'],
                name='Moving Time (hours)',
                line=dict(color='rgb(0, 128, 0)'),
                hovertemplate="<b>Month:</b> %{x}<br>" +
                             "<b>Moving Time:</b> %{y:.1f} hours<br>" +
                             "<extra></extra>"
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=800,
            title_text='Monthly Activity Statistics',
            template='plotly_white',
            showlegend=True,
            hovermode='x unified',
            xaxis=dict(
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            ),
            xaxis2=dict(
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )
        
        return fig

    def create_activity_heatmap(self):
        """Create an interactive heatmap of activities by day and hour with filters"""
        heatmap_data = pd.pivot_table(
            self.df,
            values='distance_miles',
            index='hour',
            columns='day_of_week',
            aggfunc='count',
            fill_value=0
        )
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data[days]
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='YlOrRd',
            hoverongaps=False,
            text=heatmap_data.values,
            texttemplate='%{text}',
            textfont={"size": 10},
            hovertemplate="<b>Day:</b> %{x}<br>" +
                         "<b>Hour:</b> %{y}:00<br>" +
                         "<b>Activities:</b> %{z}<br>" +
                         "<extra></extra>"
        ))
        
        fig.update_layout(
            title='Activity Heatmap by Day and Hour',
            xaxis_title='Day of Week',
            yaxis_title='Hour of Day',
            template='plotly_white',
            height=600,
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    active=0,
                    x=0.57,
                    y=1.2,
                    buttons=list([
                        dict(
                            label="All Activities",
                            method="update",
                            args=[{"z": [heatmap_data.values]}]
                        ),
                        dict(
                            label="Running",
                            method="update",
                            args=[{"z": [self.df[self.df['type'] == 'Run'].pivot_table(
                                values='distance_miles',
                                index='hour',
                                columns='day_of_week',
                                aggfunc='count',
                                fill_value=0
                            )[days].values]}]
                        ),
                        dict(
                            label="Cycling",
                            method="update",
                            args=[{"z": [self.df[self.df['type'] == 'Ride'].pivot_table(
                                values='distance_miles',
                                index='hour',
                                columns='day_of_week',
                                aggfunc='count',
                                fill_value=0
                            )[days].values]}]
                        )
                    ]),
                )
            ]
        )
        
        return fig

    def save_all_visualizations(self):
        """Save all visualizations as HTML files"""
        os.makedirs('output', exist_ok=True)
        
        # Save bubble chart
        fig_bubble = self.create_activity_bubble_chart()
        fig_bubble.write_html('output/activity_bubbles.html')
        
        # Save time distribution
        fig_time = self.create_time_distribution_chart()
        fig_time.write_html('output/time_distribution.html')
        
        # Save monthly stats
        fig_monthly = self.create_monthly_stats_chart()
        fig_monthly.write_html('output/monthly_stats.html')
        
        # Save heatmap
        fig_heatmap = self.create_activity_heatmap()
        fig_heatmap.write_html('output/activity_heatmap.html')
        
        print("All interactive visualizations have been saved as HTML files in the output directory")

def main():
    visualizer = InteractiveStravaVisualizer()
    visualizer.save_all_visualizations()

if __name__ == "__main__":
    main() 