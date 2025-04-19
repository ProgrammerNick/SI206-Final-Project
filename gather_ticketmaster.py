import requests
import sqlite3
import os
from datetime import datetime
import re
from display_ticketmaster import visualize_data

def init_database(db_name="weather.db"):
    """Initialize SQLite database with Events and Venues tables.
    
    Input: db_name (str) - Name of the database file
    Output: None (creates tables if they don't exist)
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Venues (
            venue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue_name TEXT UNIQUE,
            city_id INTEGER,
            FOREIGN KEY (city_id) REFERENCES Cities(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            date TEXT,
            venue_id INTEGER,
            price_range TEXT,
            FOREIGN KEY (venue_id) REFERENCES Venues(venue_id)
        )
    """)
    conn.commit()
    conn.close()

def fetch_ticketmaster_events(city, event_date, api_key, max_items=25):
    """Fetch events from Ticketmaster API for a city and single date.
    
    Input: 
        city (str) - City name (e.g., 'New York')
        event_date (str) - Event date in YYYY-MM-DD
        api_key (str) - Ticketmaster API key
        max_items (int) - Max events to fetch per call
    Output: List of (name, date, venue_name, city, price_range) tuples
    """
    url = "https://app.ticketmaster.com/discovery/v2/events.json"

    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, event_date):
        year = event_date[:4]
        month = event_date[4:6]
        day = event_date[6:]
    else:
        year, month, day = event_date.split('-')

    params = {
        "apikey": api_key,
        "city": city,
        "startDateTime": f"{year}-{month}-{day}T00:00:00Z",
        "endDateTime": f"{year}-{month}-{day}T23:59:59Z",
        "size": str(max_items),
        "sort": "date,asc"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = []
            if "_embedded" in data and "events" in data["_embedded"]:
                for event in data["_embedded"]["events"]:
                    name = event.get("name", "Unknown Event")
                    date = event["dates"]["start"].get("localDate", "Unknown Date")
                    venue = event["_embedded"]["venues"][0].get("name", "Unknown Venue") if event["_embedded"].get("venues") else "Unknown Venue"
                    city_name = event["_embedded"]["venues"][0]["city"].get("name", city) if event["_embedded"].get("venues") else city
                    price = event.get("priceRanges", [{}])[0].get("min", "N/A")
                    price_range = str(price) if price != "N/A" else "N/A"
                    events.append((name, date, venue, city_name, price_range))
            return events
        return []
    except requests.RequestException:
        return []

def store_events(events, db_name="weather.db"):
    """Store events in SQLite database, avoiding duplicates, using Cities table.
    
    Input: 
        events (list) - List of (name, date, venue_name, city, price_range) tuples
        db_name (str) - Database file
    Output: Tuple of (new events stored, new venues stored, new cities stored)
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    new_events = 0
    new_venues = 0

    # Only get the first 25 events and store them in the database if they don't already exist
    for event in events[:25]:

        name, date, venue_name, city, price_range = event
        cursor.execute("SELECT id FROM Cities WHERE city = ?", (city,))
        city_row = cursor.fetchone()

        # if the city id is not in our database, look for another event.
        if not city_row:
            continue

        city_id = city_row[0]

        cursor.execute("INSERT OR IGNORE INTO Venues (venue_name, city_id) VALUES (?, ?)", (venue_name, city_id))

        if cursor.rowcount > 0:
            new_venues += 1

        cursor.execute("SELECT venue_id FROM Venues WHERE venue_name = ? AND city_id = ?", (venue_name, city_id))
        venue_id = cursor.fetchone()
        venue_id = venue_id[0]
        
        cursor.execute("INSERT OR IGNORE INTO Events (name, date, venue_id, price_range) VALUES (?, ?, ?, ?)",
                        (name, date, venue_id, price_range))
        
        if cursor.rowcount > 0:
            new_events += 1


    conn.commit()
    conn.close()
    return new_events, new_venues

def gather_events(city, event_date, db_name="weather.db"):
    """Gather and store Ticketmaster events for a city and date.
    
    Input:
        city (str) - City name (e.g., 'New York')
        event_date (str) - Event date in YYYY-MM-DD
        db_name (str) - Database file
    Output: Tuple of (new events stored, new venues stored, new cities stored)
    """
    if not city or not isinstance(city, str) or not city.strip():
        return 0, 0, 0
    city = city.strip().title()

    init_database(db_name)
    api_key = "G1SnItHhk6foswTJuIHEw7iPa9qwb8Ak"
    events = fetch_ticketmaster_events(city, event_date, api_key)


    return store_events(events, db_name)

def fetch_and_visualize_events(city, event_date, db_name="weather.db"):
    """Fetch events and generate visualizations for dashboard.
    
    Input:
        city (str) - City name (e.g., 'New York')
        event_date (str) - Event date in YYYY-MM-DD
        db_name (str) - Database file
    Output: Tuple of (new_events, new_venues, new_cities, table_counts, sample_events, viz_images)
    """
    new_events, new_venues = gather_events(city, event_date, db_name)
    table_counts, sample_events, viz_images = visualize_data(db_name)
    print(f"Stored {new_events} new events, and {new_venues} new venues.")