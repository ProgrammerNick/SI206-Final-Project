import sqlite3
import json
import os
import requests
import re

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
        with open("weather.json", 'w', encoding="utf-8") as f:
            json.dump(response.json(), f, indent=4)
        return response.json()
    else:
        return f"Error {response.status_code}"
   
def create_weather_table(data, cur, conn):
    cur.execute("""CREATE TABLE IF NOT EXISTS Weather 
                (weather_id INTEGER PRIMARY KEY, city_id INTEGER, temperature REAL, humidity REAL, wind_speed REAL, 
                uv_index REAL, chance_of_precipitation REAL, conditions_id INTEGER, date_id INTEGER, time INTEGER)""")
    try:
        cur.execute("SELECT weather_id FROM Weather ORDER BY weather_id DESC LIMIT 1")
        weather_id = int(cur.fetchone())
    except:
        weather_id = 0
    for day in data['days']:
        try:
            cur.execute("SELECT date_id FROM Weather ORDER BY date_id DESC LIMIT 1")
            date_id = int(cur.fetchone()[0])
            date_id += 1 
        except:
            date_id = 1
        for temp_dict in day["hours"]:
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
            time = temp_dict['datetime']
            time = re.search(r'\d{2}', time).group()
            time = int(time)
            cur.execute("""INSERT OR IGNORE INTO Weather (weather_id, city_id, humidity, wind_speed,
                        uv_index, chance_of_precipitation, conditions_id, date_id, time)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""", 
                        (weather_id, city_id, temp, humidity, wind_speed, uv_index, chance_of_precip,
                         conditions_id, date_id, time))
            print((weather_id, city_id, humidity, wind_speed, uv_index, chance_of_precip,
                    conditions_id, date_id, time))
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


def main():
    weather_dict = search_for_weather("London")
    cur, conn = setup_weather_database("weather.db")
    create_conditions_table(cur, conn)
    create_cities_table(cur, conn)
    create_weather_table(weather_dict, cur, conn)

    #print(weather_dict)

if __name__ == "__main__":
    main()