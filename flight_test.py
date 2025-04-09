import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time

# Headers for scraping and API calls
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

# Ticketmaster API (official, not RapidAPI)
TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
TICKETMASTER_KEY = "G1SnItHhk6foswTJuIHEw7iPa9qwb8Ak"

# Other APIs
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"  # Alternative geocoder
GEOAPIFY_KEY = "YOUR_GEOAPIFY_KEY_HERE"  # Get free key at geoapify.com if needed

# Prompt user for city
city = input("Enter a city (e.g., New York, Chicago): ").strip()

# Get coordinates for weather (Geoapify fallback, or skip if hardcoded)
geocode_params = {
    "text": city,
    "apiKey": GEOAPIFY_KEY,
    "format": "json"
}
try:
    response = requests.get(GEOCODE_URL, params=geocode_params, headers=HEADERS)
    if response.status_code == 200 and response.json()["results"]:
        location = response.json()["results"][0]
        latitude = float(location["lat"])
        longitude = float(location["lon"])
        print(f"Found coordinates for {city}: ({latitude}, {longitude})")
    else:
        print(f"Geocoding failed for {city}. Using New York as default.")
        latitude, longitude = 40.7128, -74.0060  # NYC fallback
except requests.RequestException as e:
    print(f"Geocoding error: {e}. Using New York as default.")
    latitude, longitude = 40.7128, -74.0060

# Dates: April 10-15, 2025
base_date = datetime(2025, 4, 10)
dates = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6)]
event_data = {"dates": dates, "events": ["None"] * 6}
weather_data = {"dates": dates, "temps": [0] * 6}
restaurant_data = []

# Fetch events from Ticketmaster
params = {
    "apikey": TICKETMASTER_KEY,
    "city": city,
    "startDateTime": "2025-04-10T00:00:00Z",
    "endDateTime": "2025-04-15T23:59:59Z",
    "size": "6"  # Limit to 6 events
}
try:
    response = requests.get(TICKETMASTER_URL, params=params, headers=HEADERS)
    print(f"Ticketmaster response: {response.status_code} - {response.text[:200]}")
    if response.status_code == 200:
        data = response.json()
        if "_embedded" in data and "events" in data["_embedded"]:
            events = data["_embedded"]["events"][:6]
            for i, event in enumerate(events[:len(dates)]):
                event_data["events"][i] = event["name"]
                print(f"Event for {dates[i]}: {event_data['events'][i]}")
        else:
            print("No events found in response.")
    else:
        print(f"Ticketmaster Error: {response.status_code}")
except requests.RequestException as e:
    print(f"Ticketmaster request failed: {e}")

# Fetch weather
params = {
    "latitude": latitude,
    "longitude": longitude,
    "daily": "temperature_2m_max",
    "timezone": "auto",
    "start_date": "2025-04-10",
    "end_date": "2025-04-15"
}
try:
    response = requests.get(WEATHER_URL, params=params, timeout=5)
    if response.status_code == 200:
        data = response.json()["daily"]
        weather_data["temps"] = data["temperature_2m_max"]
    else:
        print(f"Weather API Error: {response.status_code}")
except requests.RequestException as e:
    print(f"Weather request failed: {e}")

# Scrape restaurants from OpenTable
opentable_url = f"https://www.opentable.com/s/?covers=2&dateTime=2025-04-10&term={city.replace(' ', '+')}"
try:
    response = requests.get(opentable_url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        restaurant_cards = soup.find_all("div", class_="rest-row-name")[:5]
        if restaurant_cards:
            for card in restaurant_cards:
                name = card.text.strip()
                restaurant_data.append(name)
                print(f"Restaurant: {name}")
        else:
            print("No restaurant names found. Check HTML class.")
    else:
        print(f"OpenTable Error: {response.status_code}")
except requests.RequestException as e:
    print(f"OpenTable request failed: {e}")
time.sleep(2)

# Visualize weather
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(weather_data["dates"], weather_data["temps"], color="red", marker="o", label="Max Temp (°C)")
ax.set_xlabel("Date")
ax.set_ylabel("Max Temperature (°C)", color="red")
ax.tick_params(axis="y", labelcolor="red")
plt.xticks(rotation=45)
plt.title(f"{city.capitalize()} Weather (April 10-15, 2025)")
plt.legend()
plt.tight_layout()
plt.show()

# Print all data
print("\nEvent Data:", event_data)
print("Weather Data:", weather_data)
print("Restaurants:", restaurant_data)