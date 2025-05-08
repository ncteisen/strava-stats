# Better Strava Wrapped

A Python project that creates enhanced visualizations of your Strava activity data.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your Strava credentials:
```
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REFRESH_TOKEN=your_refresh_token
```

## Usage

1. Run the data collection script to fetch your Strava activities:
```bash
python src/data_collection.py
```

2. Generate visualizations:
```bash
python src/visualization.py
```

## Project Structure

- `src/`: Source code directory
  - `data_collection.py`: Fetches and stores Strava activity data
  - `visualization.py`: Generates visualizations from the collected data
- `data/`: Directory for storing activity data
- `output/`: Directory for generated visualizations 