import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import patheffects as pe


def _format_total_minutes(total_minutes: float) -> str:
    """Format a duration in minutes to a human friendly string."""
    minutes = int(total_minutes)
    years, minutes = divmod(minutes, 525600)  # 365*24*60
    days, minutes = divmod(minutes, 1440)  # 24*60
    hours, minutes = divmod(minutes, 60)
    parts = []
    if years:
        parts.append(f"{years}y")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "0m"


def generate_wrapped_image(data_file: str = "data/activities.json", output_file: str = "output/strava_wrapped.png") -> None:
    """Generate a summary image of lifetime Strava statistics."""
    with open(data_file, "r") as f:
        activities = json.load(f)

    df = pd.DataFrame(activities)
    if df.empty:
        raise ValueError("No activity data found")

    df["distance_miles"] = df["distance"] * 0.000621371
    total_activities = len(df)
    total_bike = df[df["type"] == "Ride"]["distance_miles"].sum()
    total_run = df[df["type"] == "Run"]["distance_miles"].sum()
    total_time_min = df["moving_time"].sum() / 60
    total_elev = df["total_elevation_gain"].sum() * 3.28084
    total_kudos = df["kudos_count"].sum()
    total_photos = df.get("total_photo_count", pd.Series([0]*len(df))).fillna(0).sum()

    most_common_type = df["type"].mode()[0]

    stats = [
        ("Total Activities", f"{total_activities:,}"),
        ("Bike Miles", f"{total_bike:,.0f}"),
        ("Run Miles", f"{total_run:,.0f}"),
        ("Moving Time", _format_total_minutes(total_time_min)),
        ("Elevation Gain (ft)", f"{total_elev:,.0f}"),
        ("Kudos", f"{int(total_kudos):,}"),
        ("Photos", f"{int(total_photos):,}"),
        ("Most Common", most_common_type),
    ]

    plt.figure(figsize=(6,8), dpi=200)
    ax = plt.gca()
    ax.axis("off")
    ax.set_facecolor("#f5f5f5")

    plt.title("Strava Lifetime Stats", fontsize=24, weight="bold", pad=20)

    y_start = 0.85
    dy = 0.1
    for i, (label, value) in enumerate(stats):
        y = y_start - i*dy
        txt = plt.text(0.05, y, f"{label}: {value}", fontsize=16, ha="left", va="top")
        txt.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    generate_wrapped_image()
