import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

def get_table_counts(db_name="weather.db"):
    """Get row counts for all tables.
    
    Input: db_name (str) - Database file
    Output: Dict of table names and counts
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    tables = ["Cities", "Conditions", "Weather", "Venues", "Events"]
    counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = 0
    # Sample Events data
    cursor.execute("SELECT e.event_id, e.name, e.date, v.venue_name, c.city, e.price_range "
                  "FROM Events e JOIN Venues v ON e.venue_id = v.venue_id "
                  "JOIN Cities c ON v.city_id = c.id LIMIT 5")
    sample_events = cursor.fetchall()
    conn.close()
    return counts, sample_events

def calculate_events_per_day(db_name="weather.db"):
    """Calculate average events per day and return counts.
    
    Input: db_name (str) - Database file
    Output: Tuple of (average events per day, dict of date:count)
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.date, COUNT(e.event_id) 
        FROM Events e
        JOIN Venues v ON e.venue_id = v.venue_id
        JOIN Cities c ON v.city_id = c.id
        GROUP BY e.date
    """)
    counts = dict(cursor.fetchall())
    total_days = len(counts)
    avg_events = sum(counts.values()) / total_days if total_days else 0
    conn.close()
    return avg_events, counts

def get_venue_distribution(db_name="weather.db"):
    """Get count of events per venue.
    
    Input: db_name (str) - Database file
    Output: Dict of venue_name:count
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    conn = sqlite3.connect(db_path)
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

def write_calculations(avg_events, counts, db_name="weather.db", output_file="calculations.txt"):
    """Write calculations to a file.
    
    Input: 
        avg_events (float) - Average events
        counts (dict) - Date:count
        db_name (str) - Database file
        output_file (str) - Output text file
    Output: None
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Events")
    total = cursor.fetchone()[0]
    with open(output_file, "w") as f:
        f.write(f"Average events per day: {avg_events:.2f}\n")
        f.write(f"Total events stored: {total}\n")
        f.write("Events per day:\n")
        for date, count in counts.items():
            f.write(f"  {date}: {count}\n")
    conn.close()

def visualize_data(avg_events, date_counts, venue_dist):
    """Create three visualizations with Matplotlib/Seaborn.
    
    Input: 
        avg_events (float) - Average events
        date_counts (dict) - Date:count
        venue_dist (dict) - Venue:count
    Output: None (shows plots)
    """
    # Bar chart: Events per day
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

    # Pie chart: Venue distribution
    plt.figure(figsize=(8, 8))
    top_venues = dict(sorted(venue_dist.items(), key=lambda x: x[1], reverse=True)[:5])
    plt.pie(top_venues.values(), labels=top_venues.keys(), autopct="%1.1f%%", colors=sns.color_palette("pastel"))
    plt.title("Top 5 Venues by Event Count")
    plt.show()

    # Box plot: Event counts per day
    plt.figure(figsize=(10, 6))
    counts = list(date_counts.values())
    sns.boxplot(y=counts, color="lightblue")
    plt.ylabel("Events per Day")
    plt.title("Distribution of Events per Day")
    plt.show()

def main():
    """Main function to display Ticketmaster data and visualize."""
    counts, sample_events = get_table_counts()
    print("Table counts in weather.db:")
    for table, count in counts.items():
        print(f"  {table}: {count} rows")
    print("\nSample Events (up to 5):")
    if sample_events:
        for event in sample_events:
            print(f"  ID: {event[0]}, Name: {event[1]}, Date: {event[2]}, Venue: {event[3]}, City: {event[4]}, Price: {event[5]}")
    else:
        print("  No events found.")
    
    avg_events, date_counts = calculate_events_per_day()
    venue_dist = get_venue_distribution()
    write_calculations(avg_events, date_counts)
    if date_counts:
        visualize_data(avg_events, date_counts, venue_dist)
    else:
        print("No event data to visualize.")

if __name__ == "__main__":
    main()