import requests
import sqlite3
from datetime import datetime, timedelta
import time

def init_database(db_name="events.db"):
    """Initialize SQLite database with Events and Venues tables.
    
    Input: db_name (str) - Name of the database file
    Output: None (creates tables if they don't exist)
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Venues (
            venue_id INTEGER PRIMARY KEY,
            venue_name TEXT UNIQUE,
            city TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            venue_id INTEGER,
            price_range TEXT,
            FOREIGN KEY (venue_id) REFERENCES Venues (venue_id)
        )
    """)
    conn.commit()
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
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            events = []
            if "_embedded" in data and "events" in data["_embedded"]:
                for event in data["_embedded"]["events"]:
                    name = event["name"]
                    date = event["dates"]["start"]["localDate"]
                    venue = event["_embedded"]["venues"][0]["name"] if event["_embedded"].get("venues") else "Unknown"
                    city = event["_embedded"]["venues"][0]["city"]["name"] if event["_embedded"].get("venues") else city
                    price = event.get("priceRanges", [{}])[0].get("min", "N/A")
                    price_range = str(price) if price != "N/A" else "N/A"
                    events.append((name, date, venue, city, price_range))
            return events
        else:
            print(f"Ticketmaster Error: {response.status_code} - {response.text[:200]}")
            return []
    except requests.RequestException as e:
        print(f"Ticketmaster request failed: {e}")
        return []

def store_events(events, db_name="events.db"):
    """Store events in SQLite database, avoiding duplicates.
    
    Input: 
        events (list) - List of (name, date, venue_name, city, price_range) tuples
        db_name (str) - Database file
    Output: Number of new events stored
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    new_events = 0

    for event in events:
        name, date, venue_name, city, price_range = event
        # Insert or get venue_id
        cursor.execute("SELECT venue_id FROM Venues WHERE venue_name = ?", (venue_name,))
        venue_id = cursor.fetchone()
        if not venue_id:
            cursor.execute("INSERT INTO Venues (venue_name, city) VALUES (?, ?)", (venue_name, city))
            cursor.execute("SELECT venue_id FROM Venues WHERE venue_name = ?", (venue_name,))
            venue_id = cursor.fetchone()
        venue_id = venue_id[0]
        # Insert event if it doesn't exist
        cursor.execute("SELECT event_id FROM Events WHERE name = ? AND date = ? AND venue_id = ?", 
                      (name, date, venue_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Events (name, date, venue_id, price_range) VALUES (?, ?, ?, ?)",
                          (name, date, venue_id, price_range))
            new_events += 1
    conn.commit()
    conn.close()
    return new_events

def main():
    """Main function to gather Ticketmaster events and store in database."""
    init_database()
    city = input("Enter a city (e.g., New York): ")
    start_date = "2025-04-16"
    end_date = "2025-04-21"
    api_key = "G1SnItHhk6foswTJuIHEw7iPa9qwb8Ak"
    
    events = fetch_ticketmaster_events(city, start_date, end_date, api_key)
    if events:
        new_count = store_events(events)
        print(f"Stored {new_count} new events in database.")
    else:
        print("No events fetched.")

if __name__ == "__main__":
    main()