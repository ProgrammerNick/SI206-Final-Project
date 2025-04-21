import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import Counter
from io import BytesIO

def calculate_events_per_day(city_id, db_name="weather.db"):
    """Calculate average events per day and return counts.
    
    Input: db_name (str) - Database file
    Output: Tuple of (average events per day, dict of date:count)
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT e.date, COUNT(e.event_id) 
        FROM Events e
        JOIN (
            SELECT * FROM Cities WHERE id = ?
        ) c ON e.city_id = c.id
        GROUP BY e.date
        """, (city_id,))

        counts = dict(cursor.fetchall())
        total_days = len(counts)
        avg_events = sum(counts.values()) / total_days if total_days else 0
        conn.close()
        return avg_events, counts
    except sqlite3.Error:
        return 0, {}

def get_venue_distribution(city_id, db_name="weather.db"):
    """Get count of events per venue.
    
    Input: db_name (str) - Database file
    Output: Dict of venue_name:count
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.venue_name, COUNT(e.event_id)
            FROM Events e
            JOIN (
            SELECT * FROM Cities WHERE id = ?
            ) c ON e.city_id = c.id
            JOIN Venues v ON e.venue_id = v.venue_id
            GROUP BY v.venue_name
        """, (city_id,))
        distribution = dict(cursor.fetchall())
        conn.close()
        return distribution
    except sqlite3.Error:
        return {}

def write_calculations(city_id, city_name, avg_events, counts, db_name="weather.db", output_file="events.txt"):
    """Write city-specific calculations to a file.
    
    Input: 
        city_id (int) - City ID
        city_name (str) - City name for output clarity
        avg_events (float) - Average events per day
        counts (dict) - Date:count
        db_name (str) - Database file
        output_file (str) - Output text file
    Output: None
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Events e
            JOIN Venues v ON e.venue_id = v.venue_id
            JOIN Cities c ON v.city_id = c.id
            WHERE c.id = ?
        """, (city_id,))
        total = cursor.fetchone()[0]
        with open(output_file, "a") as f:
            f.write(f"\nCity: {city_name}\n")
            f.write(f"Average events per day: {avg_events:.2f}\n")
            f.write(f"Total events stored: {total}\n")
            f.write("Events per day:\n")
            for date, count in counts.items():
                f.write(f"  {date[:4] + "-" + date[4:6] + "-" + date[6:]}: {count}\n")
        conn.close()
    except sqlite3.Error:
        pass

def visualize_data(city_id, city_name, db_name="weather.db"):
    """Create three visualizations and return data for dashboard.
    
    Input: db_name (str) - Database file
    Output: None
    """

    avg_events, date_counts = calculate_events_per_day(city_id, db_name)
    venue_dist = get_venue_distribution(city_id, db_name)
    write_calculations(city_id, city_name, avg_events, date_counts, db_name)

    if date_counts:
        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(20, 6))

        # Visualization 1
        x_vals = [date[:4] + "-" + date[4:6] + "-" + date[6:] for date in date_counts.keys()]
        y_vals = list(date_counts.values())
        axs[0].bar(x_vals, y_vals, color="red")
        axs[0].axhline(avg_events, color="red", linestyle="--", label=f"Avg: {avg_events:.2f}")
        axs[0].set_xlabel("Date")
        axs[0].set_ylabel("Number of Events")
        axs[0].set_title(f"Events per Day in {city_name}")
        axs[0].tick_params(axis='x', rotation=45)
        axs[0].legend()

        # Visualization 2
        top_venues = dict(sorted(venue_dist.items(), key=lambda x: x[1], reverse=True)[:5])
        axs[1].pie(
            top_venues.values(),
            labels=top_venues.keys(),
            autopct="%1.1f%%",
            colors=sns.color_palette("pastel")
        )
        axs[1].set_title(f"Top 5 Venues by Count in {city_name}")

        plt.tight_layout()
        plt.savefig("events.png")
        plt.show()