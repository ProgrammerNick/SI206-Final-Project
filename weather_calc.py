import weather
from collections import Counter
import matplotlib
import matplotlib.pyplot as plt
import time
import sys

def daily_high_and_low(cur, date, city):
    cur.execute("SELECT id from Cities WHERE city = ?", (city,))
    city_id = int(cur.fetchone()[0])
    cur.execute("SELECT MIN(temperature) from Weather WHERE city_id = ? AND date = ?", (city_id, date))
    min_temp = int(cur.fetchone()[0])
    cur.execute("SELECT MAX(temperature) from Weather WHERE city_id = ? AND date = ?", (city_id, date))
    max_temp = int(cur.fetchone()[0])
    return max_temp, min_temp, date

def daily_avg(cur, day, city):
    cur.execute("SELECT id from Cities WHERE city = ?", (city,))
    city_id = int(cur.fetchone()[0])
    cur.execute("""SELECT temperature, humidity, wind_speed, uv_index, chance_of_precipitation, 
                conditions_id FROM Weather
                WHERE city_id = ? AND date = ?""", (city_id, day))
    data = cur.fetchall()
    temp = round(sum(x[0] for x in data) / 24, 1)
    humidity = round(sum(x[1] for x in data) / 24, 1)
    wind_speed = round(sum(x[2] for x in data) / 24, 1)
    uv_index = round(sum(x[3] for x in data) / 24, 1)
    precip = round(sum(x[4] for x in data) / 24, 1)
    conditions_lst = [x[5] for x in data]
    con_id = Counter(conditions_lst).most_common(1)[0][0]
    cur.execute("SELECT description from Conditions WHERE id = ?", (con_id,))
    conditions = cur.fetchone()[0]
    return temp, humidity, wind_speed, uv_index, precip, conditions, day

def create_avg_chart(cur, city, data):
    cur.execute("""SELECT DISTINCT Weather.date, Cities.city 
                FROM Weather 
                JOIN Cities ON Weather.city_id = Cities.id
                WHERE Cities.city = ?
                ORDER BY Weather.date DESC LIMIT 5""", (city,))

    dates = [row[0] for row in cur.fetchall()]
    dates.reverse()
    temp = [row[0] for row in data]
    humidity = [row[1] for row in data]
    #print(dates)
    #print(temp)
    fig, ax1 = plt.subplots()

    ax1.plot(dates, temp, 'r-', label='Temperature (°F)')
    ax1.set_ylabel('Temperature (°F)', color='r')
    ax1.tick_params(axis='y', labelcolor='r')

    ax1.set_xlabel("Date")

    ax2 = ax1.twinx()

    # Plot humidity on the right Y-axis
    ax2.plot(dates, humidity, 'b--', label='Humidity (%)')
    ax2.set_ylabel('Humidity (%)', color='b')
    ax2.tick_params(axis='y', labelcolor='b')

    plt.title(f'Weather Trends in {city}')
    plt.savefig("weather_line_graph.png")
    plt.show()

def write_calculations(avg_data, temp_data, filename, city):
    with open(filename, 'w') as f:
        lines = []
        lines.append(f"Weather data for {city}\n\n")
        for tple in temp_data:
            date_str = str(tple[2])
            year = date_str[0:4]
            month = date_str[5:7]
            day = date_str[-2:]
            lines.append(f"Maximum temperature for {month}/{day}/{year} in {city}: {tple[0]}.\n")
            lines.append(f"Minimum temperature for {month}/{day}/{year} in {city}: {tple[1]}.\n\n")
        for tple in avg_data:
            #temp, humidity, wind_speed, uv_index, precip, conditions, day
            date_str = str(tple[6])
            year = date_str[0:4]
            month = date_str[5:7]
            day = date_str[-2:]
            lines.append(f"Average temperature for {month}/{day}/{year} in {city}: {tple[0]}.\n")
            lines.append(f"Average humidity for {month}/{day}/{year} in {city}: {tple[1]}.\n")
            lines.append(f"Average wind speed for {month}/{day}/{year} in {city}: {tple[2]}.\n")
            lines.append(f"Average UV index for {month}/{day}/{year} in {city}: {tple[3]}.\n")
            lines.append(f"Average chance of precipitation for {month}/{day}/{year} in {city}: {tple[4]}.\n")
            lines.append(f"Most common conditions for {month}/{day}/{year} in {city}: {tple[5]}.\n\n")
        #print(lines)
        f.writelines(lines)

def run_weather_app(city, date):
    cur, conn = weather.setup_weather_database("weather.db")
    weather.create_conditions_table(cur, conn)
    weather.create_cities_table(cur, conn)
    averages = []
    high_and_low = []
    date = int(date)
    for i in range(5):
         #print(date)
        weather_dict = weather.search_for_weather(city)
        if isinstance(weather_dict, str):
            print(weather_dict)
            sys.exit(1)
        weather.create_weather_table(weather_dict, cur, conn, i)
        averages.append(daily_avg(cur, date, city))
        high_and_low.append(daily_high_and_low(cur, date, city))
        date += 1
        time.sleep(2)
    #print(averages)
    #print(high_and_low)
    create_avg_chart(cur, city, averages)
    write_calculations(averages, high_and_low, "weather_calculations.txt", city)

    #print(weather_dict)

"""def main():
    weather_dict = weather.search_for_weather("Ann Arbor")
    cur, conn = weather.setup_weather_database("weather.db")
    weather.create_conditions_table(cur, conn)
    weather.create_cities_table(cur, conn)
    averages = []
    high_and_low = []
    date = 20250418
    for i in range(5):
        print(date)
        weather.create_weather_table(weather_dict, cur, conn, i)
        averages.append(daily_avg(cur, date, "Ann Arbor"))
        high_and_low.append(daily_high_and_low(cur, date, "Ann Arbor"))
        date += 1
        time.sleep(2)
    print(averages)
    print(high_and_low)
    create_avg_chart(cur, "Ann Arbor", averages)
    write_calculations(averages, high_and_low, "Calculations.txt", "Ann Arbor")

    #print(weather_dict)

if __name__ == "__main__":
    main()"""
