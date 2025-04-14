import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from datetime import datetime

def calculate_events_per_day(db_name="events.db"):
    """Calculate average events per day and return counts.
    
    Input: db_name (str) - Database file
    Output: Tuple of (average events per day, dict of date:count)
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.date, COUNT(e.event_id) 
        FROM Events e
        JOIN Venues v ON e.venue_id = v.venue_id
        GROUP BY e.date
    """)
    counts = dict(cursor.fetchall())
    total_days = len(counts)
    avg_events = sum(counts.values()) / total_days if total_days else 0
    conn.close()
    return avg_events, counts

def get_venue_distribution(db_name="events.db"):
    """Get count of events per venue.
    
    Input: db_name (str) - Database file
    Output: Dict of venue_name:count
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.venue_name, COUNT(e.event_id)
        FROM Events e
        JOIN Venues v ON e.venue_id = v.venue_id
        GROUP BY v.venue_name
    """)
    distribution = dict(cursor.fetchall())
    conn.close()
    return distribution

def write_calculations(avg_events, db_name="events.db", output_file="calculations.txt"):
    """Write average events per day to a file.
    
    Input: 
        avg_events (float) - Average events
        db_name (str) - Database file
        output_file (str) - Output text file
    Output: None
    """
    with open(output_file, "w") as f:
        f.write(f"Average events per day: {avg_events:.2f}\n")
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Events")
        total = cursor.fetchone()[0]
        f.write(f"Total events stored: {total}\n")
        conn.close()

def visualize_data(avg_events, date_counts, venue_dist):
    """Create three visualizations with Matplotlib/Seaborn.
    
    Input: 
        avg_events (float) - Average events
        date_counts (dict) - Date:count
        venue_dist (dict) - Venue:count
    Output: None (shows plots)
    """
    # 1. Bar chart: Events per day
    plt.figure(figsize=(10, 6))
    sns.barplot(x=list(date_counts.keys()), y=list(date_counts.values()), hue=list(date_counts.keys()), palette="viridis", legend=False)
    plt.axhline(avg_events, color="red", linestyle="--", label=f"Avg: {avg_events:.2f}")
    plt.xlabel("Date")
    plt.ylabel("Number of Events")
    plt.title("Events per Day (Ticketmaster)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # 2. Pie chart: Venue distribution
    plt.figure(figsize=(8, 8))
    top_venues = dict(sorted(venue_dist.items(), key=lambda x: x[1], reverse=True)[:5])
    plt.pie(top_venues.values(), labels=top_venues.keys(), autopct="%1.1f%%", colors=sns.color_palette("pastel"))
    plt.title("Top 5 Venues by Event Count")
    plt.show()

    # 3. Box plot: Event counts per day (simulated variation)
    plt.figure(figsize=(10, 6))
    counts = list(date_counts.values())
    sns.boxplot(y=counts, color="lightblue")
    plt.ylabel("Events per Day")
    plt.title("Distribution of Events per Day")
    plt.show()

def main():
    """Main function to process and visualize Ticketmaster data."""
    avg_events, date_counts = calculate_events_per_day()
    venue_dist = get_venue_distribution()
    write_calculations(avg_events)
    visualize_data(avg_events, date_counts, venue_dist)

if __name__ == "__main__":
    main()