import weather
import weather_calc
import sys
import time
import restaurants
import gather_ticketmaster

def main():
    city = input("Enter the city: ")
    date = input("Enter the date (yyyymmdd): ")
    cur, conn = weather.setup_weather_database("weather.db")
    #weather_calc.run_weather_app(city, date)
    #restaurants.restaurants_call(cur,conn,city)
    gather_ticketmaster.fetch_and_visualize_events(city, date)
if __name__ == "__main__":
    main()
