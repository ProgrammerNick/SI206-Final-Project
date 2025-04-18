import weather
import weather_calc
import sys
import time

def main():
    city = input("Enter the city: ")
    date = input("Enter the date (yyyymmdd): ")
    weather_dict = weather.search_for_weather(city)
    if isinstance(weather_dict, str):
        print(weather_dict)
        sys.exit(1)
    cur, conn = weather.setup_weather_database("weather.db")
    weather.create_conditions_table(cur, conn)
    weather.create_cities_table(cur, conn)
    averages = []
    high_and_low = []
    date = int(date)
    for i in range(5):
        #print(date)
        weather.create_weather_table(weather_dict, cur, conn, i)
        averages.append(weather_calc.daily_avg(cur, date, city))
        high_and_low.append(weather_calc.daily_high_and_low(cur, date, city))
        date += 1
        time.sleep(2)
    #print(averages)
    #print(high_and_low)
    weather_calc.create_avg_chart(cur, city, averages)
    weather_calc.write_calculations(averages, high_and_low, "weather_calculations.txt", city)

    #print(weather_dict)

if __name__ == "__main__":
    main()
