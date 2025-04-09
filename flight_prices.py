import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Aviationstack key
ACCESS_KEY = "54b8a42dbd4e8ffbf337320cfabed168"
FLIGHT_URL = "http://api.aviationstack.com/v1/flights"

# Open-Meteo (no key needed)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Dates: April 10-15, 2025
base_date = datetime(2025, 4, 10)
dates = [(base_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6)]
flight_data = {"dates": [], "prices": []}
weather_data = {"dates": [], "temps": []}

# Fetch flight prices
for date in dates:
    params = {
        "access_key": ACCESS_KEY,
        "dep_iata": "DTW",
        "arr_iata": "JFK",
        "flight_date": date,
        "limit": 5
    }
    response = requests.get(FLIGHT_URL, params=params)
    if response.status_code == 200:
        data = response.json().get("data", [])
        if data:
            cheapest_price = min([flight.get("price", float("inf")) or float("inf") for flight in data])
            if cheapest_price != float("inf"):
                flight_data["dates"].append(date)
                flight_data["prices"].append(cheapest_price)
            else:
                flight_data["dates"].append(date)
                flight_data["prices"].append(0)
                print(f"No price for {date}")
    else:
        print(f"Flight API Error: {response.status_code}")

# Fetch weather for JFK
params = {
    "latitude": 40.6413,
    "longitude": -73.7781,
    "daily": "temperature_2m_max",
    "timezone": "America/New_York",
    "start_date": "2025-04-10",
    "end_date": "2025-04-15"
}
response = requests.get(WEATHER_URL, params=params)
if response.status_code == 200:
    data = response.json()["daily"]
    weather_data["dates"] = data["time"]
    weather_data["temps"] = data["temperature_2m_max"]
else:
    print(f"Weather API Error: {response.status_code}")

# Visualize
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.bar(flight_data["dates"], flight_data["prices"], color="skyblue", label="Cheapest Flight Price (USD)")
ax1.set_xlabel("Date")
ax1.set_ylabel("Flight Price (USD)", color="blue")
ax1.tick_params(axis="y", labelcolor="blue")
plt.xticks(rotation=45)

# Second axis for weather
ax2 = ax1.twinx()
ax2.plot(weather_data["dates"], weather_data["temps"], color="red", marker="o", label="Max Temp (°C)")
ax2.set_ylabel("Max Temperature (°C)", color="red")
ax2.tick_params(axis="y", labelcolor="red")

plt.title("DTW to JFK Flights and JFK Weather (April 10-15, 2025)")
fig.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=2)
plt.tight_layout()
plt.show()