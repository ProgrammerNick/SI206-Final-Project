import sqlite3
import json
import os
import requests
import re
from datetime import datetime
import sys

API_KEY = 'GLVTG3EDCK29FQPYLQLS6Q3F4'

def read_data_from_file(filename):
    """
    Reads data from a file with the given filename.

    Parameters
    -----------------------
    filename: str
        The name of the file to read

    Returns
    -----------------------
    dict:
        Parsed JSON data from the file
    """
    full_path = os.path.join(os.path.dirname(__file__), filename)
    f = open(full_path, encoding="utf-8-sig")
    file_data = f.read()
    f.close()
    json_data = json.loads(file_data)
    return json_data

def setup_weather_database(db_name):
    """
    Sets up a SQLite database connection and cursor.

    Parameters
    -----------------------
    db_name: str
        The name of the SQLite database

    Returns
    -----------------------
    Tuple (cursor, connection):
        A tuple containing the database cursor and connection objects.
    """
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    return cur, conn

def search_for_weather(city):

    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}"

    querystring = {"key": API_KEY, "include" : ["hours", "fcst", "alerts"]}

    response = requests.get(url, params=querystring)

    if response.status_code == 200:
        #with open("weather.json", 'w', encoding="utf-8") as f:
            #json.dump(response.json(), f, indent=4)
        return response.json()
    else:
        return f"Error {response.status_code}"
    
def days_from_date(date1_int, date2_int):
    try:
        date1 = datetime.strptime(str(date1_int), "%Y%m%d")
        date2 = datetime.strptime(str(date2_int), "%Y%m%d")
        delta = date2 - date1
        return delta.days
    except ValueError:
        return None
   
def create_weather_table(data, cur, conn, days):
    """
    Creates weather table from data from weather API

    Params:

    data: dictionary 
    Dictionary formed from the weather api call

    cur: database cursor
    conn: database connection object

    days: int 
    Days from current day to collect weather data from
    """
    cur.execute("""CREATE TABLE IF NOT EXISTS Weather 
                (weather_id INTEGER PRIMARY KEY, city_id INTEGER, temperature REAL, humidity REAL, wind_speed REAL, 
                uv_index REAL, chance_of_precipitation REAL, conditions_id INTEGER, date INTEGER, time INTEGER)""")
    try:
        cur.execute("SELECT weather_id FROM Weather ORDER BY weather_id DESC LIMIT 1")
        weather_id = int(cur.fetchone()[0])
    except:
        weather_id = 0
    cur.execute("SELECT id FROM Cities WHERE city = ?", (data['address'],))

    if cur.fetchone() == None:
        cur.execute("SELECT id FROM Cities ORDER BY id DESC LIMIT 1")
        city_id = int(cur.fetchone()[0]) + 1
        cur.execute("INSERT OR IGNORE INTO Cities (id, city) VALUES (?,?)", (city_id, data['address']))
    else:
        cur.execute("SELECT id FROM Cities WHERE city = ?", (data['address'],))
        city_id = int(cur.fetchone()[0])
    date = data["days"][0]["datetime"]
    date = re.sub(r'-', '', date)
    date = int(date)
    date_i = days_from_date(date, days)
    if date_i > 15 or date_i < 0 or date_i == None:
        print("Error: Please submit a date between today's date and the date 10 days from today.")
        sys.exit(1)
    date = data["days"][date_i]["datetime"]
    date = re.sub(r'-', '', date)
    date = int(date)
    cur.execute("SELECT city_id, date FROM Weather WHERE city_id = ? AND date = ?", (city_id, date))
    if cur.fetchone() != None:
        return
    for temp_dict in data["days"][date_i]["hours"]:
        cur.execute("SELECT id FROM Cities WHERE city = ?", (data['address'],))
        city_id = int(cur.fetchone()[0])
        temp = float(temp_dict["temp"])
        humidity = float(temp_dict["humidity"])
        wind_speed = float(temp_dict["windspeed"])
        uv_index = float(temp_dict["uvindex"])
        chance_of_precip = float(temp_dict["precipprob"])
        conditions = temp_dict['conditions'].split(',')
        cur.execute("SELECT id FROM Conditions WHERE description = ?", (conditions[0],))
        conditions_id = int(cur.fetchone()[0])
        if conditions_id == None:
            cur.execute("SELECT id FROM Conditions ORDER BY id DESC LIMIT 1")
            conditions_id = int(cur.fetchone()) + 1
            cur.execute("INSERT OR IGNORE INTO Conditions (id, description) VALUES (?,?)", (conditions_id, conditions[0]))
        time = temp_dict['datetime']
        time = re.search(r'\d{2}', time).group()
        time = int(time)
        cur.execute("""INSERT OR IGNORE INTO Weather (weather_id, city_id, temperature, humidity, 
                    wind_speed, uv_index, chance_of_precipitation, conditions_id, date, time)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                    (weather_id, city_id, temp, humidity, wind_speed, uv_index, chance_of_precip,
                     conditions_id, date, time))
        #print((weather_id, city_id, humidity, wind_speed, uv_index, chance_of_precip,
        #        conditions_id, date, time))
        weather_id += 1
    conn.commit()


def create_conditions_table(cur, conn):
    lst = ['Cloudy', 'Partially cloudy', 'Snow', 'Rain', 'Clear', 'Overcast', 'Hail', 'Sleet', 'Storm']
    cur.execute("CREATE TABLE IF NOT EXISTS Conditions (id INTEGER PRIMARY KEY, description TEXT)")
    for i in range(len(lst)):
        cur.execute("INSERT OR IGNORE INTO Conditions (id, description) VALUES (?,?)", (i, lst[i]))
    conn.commit()

def create_cities_table(cur, conn):
    with open("cities.csv", 'r') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]
        cur.execute("CREATE TABLE IF NOT EXISTS Cities (id INTEGER PRIMARY KEY, city TEXT)")
        for i in range(len(lines)):
            cur.execute("INSERT OR IGNORE INTO Cities (id, city) VALUES (?,?)", (i, lines[i]))
        conn.commit()

"""def main():
    weather_dict = search_for_weather("Ann Arbor")
    cur, conn = setup_weather_database("weather.db")
    create_conditions_table(cur, conn)
    create_cities_table(cur, conn)
    averages = []
    high_and_low = []
    date = 20250416
    for i in range(5):
        print(date)
        create_weather_table(weather_dict, cur, conn, i)
        averages.append(daily_avg(cur, date, "Ann Arbor"))
        high_and_low.append(daily_high_and_low(cur, date, "Ann Arbor"))
        date += 1
        time.sleep(2)
    print(averages)
    print(high_and_low)
    create_avg_chart(cur, "Ann Arbor", averages)

    #print(weather_dict)

if __name__ == "__main__":
    main()"""