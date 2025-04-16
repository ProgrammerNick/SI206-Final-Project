import requests
import sqlite3
import os
from datetime import datetime, timedelta
import time

def init_database(db_name="weather.db"):
    """Initialize SQLite database with Events and Venues tables.
    
    Input: db_name (str) - Name of the database file
    Output: None (creates tables if they don't exist)
    """
    path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(path, db_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Ensure Cities table exists (in case weather.py hasn't run)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT UNIQUE
        )
    """)
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
            name TEXT,
            date TEXT,
            venue_id INTEGER,
            price_range TEXT,
            FOREIGN KEY (venue_id) REFERENCES Venues(venue_id)
        )
    """)
    conn.commit()
    print(f"Initialized tables in {db_path}")
    conn.close()

def fetch_ticketmaster_events(city, start_date, end_date, api_key, max_items=25):
    """Fetch events from Ticketmaster API for a city and date range.
    
    Input: 
        city (str) - City name (e.g., 'New York')
        start_date (str) - Start date in YYYY-MM-DD
        end_date (str) - End date in YYYY-MM-DD
        api_key (str) - Ticketmaster API key
        max_items (int) - Max events to fetch per call
    Output: List of (name, date, venue_name, city, price_range) tuples
    """
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": api_key,
        "city": city,
        "startDateTime": f"{start_date}T00:00:00Z",
        "endDateTime": f"{end_date}T23:59:59Z",
        "size": str(max_items),
        "sort": "date,asc"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        print(f"Querying Ticketmaster for city: {city}")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Ticketmaster response status: {response.status_code}")
        print(f"Response body: {response.text[:500]}...")
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
                print(f"Fetched {len(events)} events: {[e[0] for e in events]}")
            else:
                print("No events found in response.")
            return events
        else:
            print(f"Ticketmaster Error: {response.status_code} - {response.text[:200]}")
            return []
    except requests.RequestException as e:
        print(f"Ticketmaster request failed: {e}")
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
    new_cities = 0

    for event in events:
        name, date, venue_name, city, price_range = event
        # Ensure city exists in Cities table
        cursor.execute("SELECT id FROM Cities WHERE city = ?", (city,))
        city_id = cursor.fetchone()
        if not city_id:
            try:
                cursor.execute("INSERT INTO Cities (city) VALUES (?)", (city,))
                new_cities += 1
                cursor.execute("SELECT id FROM Cities WHERE city = ?", (city,))
                city_id = cursor.fetchone()
            except sqlite3.IntegrityError:
                cursor.execute("SELECT id FROM Cities WHERE city = ?", (city,))
                city_id = cursor.fetchone()
        city_id = city_id[0]
        # Insert or get venue_id
        cursor.execute("SELECT venue_id FROM Venues WHERE venue_name = ? AND city_id = ?", (venue_name, city_id))
        venue_id = cursor.fetchone()
        if not venue_id:
            try:
                cursor.execute("INSERT INTO Venues (venue_name, city_id) VALUES (?, ?)", (venue_name, city_id))
                new_venues += 1
                cursor.execute("SELECT venue_id FROM Venues WHERE venue_name = ? AND city_id = ?", (venue_name, city_id))
                venue_id = cursor.fetchone()
            except sqlite3.IntegrityError:
                cursor.execute("SELECT venue_id FROM Venues WHERE venue_name = ? AND city_id = ?", (venue_name, city_id))
                venue_id = cursor.fetchone()
        venue_id = venue_id[0]
        # Insert event if it doesn't exist
        cursor.execute("SELECT event_id FROM Events WHERE name = ? AND date = ? AND venue_id = ?", 
                      (name, date, venue_id))
        if not cursor.fetchone():
            try:
                cursor.execute("INSERT INTO Events (name, date, venue_id, price_range) VALUES (?, ?, ?, ?)",
                              (name, date, venue_id, price_range))
                new_events += 1
            except sqlite3.IntegrityError as e:
                print(f"Failed to insert event '{name}': {e}")
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM Events")
    event_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Venues")
    venue_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Cities")
    city_count = cursor.fetchone()[0]
    print(f"Database stats: {event_count} events, {venue_count} venues, {city_count} cities")
    conn.close()
    return new_events, new_venues, new_cities

def main():
    """Main function to gather Ticketmaster events and store in database."""
    init_database()
    city = input("Enter a city (e.g., New York, Chicago): ").strip().title()
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    api_key = "G1SnItHhk6foswTJuIHEw7iPa9qwb8Ak"
    
    events = fetch_ticketmaster_events(city, start_date, end_date, api_key)
    if events:
        new_events, new_venues, new_cities = store_events(events)
        print(f"Stored {new_events} new events, {new_venues} new venues, {new_cities} new cities.")
    else:
        print("No events fetched. Database remains unchanged.")

if __name__ == "__main__":
    main()