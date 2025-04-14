import requests
import sqlite3
import json
import os
def search_restaurants(city):
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchLocation"

    querystring = {"query":city}

    headers = {
	    "x-rapidapi-key": "758e598c8fmshb7d3bf640dcdc09p195b67jsn08fee0e48bee",
	    "x-rapidapi-host": "tripadvisor16.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    r = response.json()['data'][0]['locationId']


    url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"

    querystring = {"locationId":r}

    headers = {
	    "x-rapidapi-key": "758e598c8fmshb7d3bf640dcdc09p195b67jsn08fee0e48bee",
	    "x-rapidapi-host": "tripadvisor16.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    print(response.json())
    return response.json()


def setup_database(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path + "/" + db_name)
    cur = conn.cursor()
    return cur, conn
def create_cuisines_table(restaurants,cur,conn):
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Cuisines (id INTEGER PRIMARY KEY, cuisine TEXT UNIQUE)"
    )
    data=restaurants['data']['data']
    for i in range(25):
        cuisine=data[i]['establishmentTypeAndCuisineTags'][0]
        cur.execute("INSERT OR IGNORE INTO Cuisines(cuisine) VALUES (?)", (cuisine,))
        conn.commit()


def create_restaurants_table(restaurants,cur,conn):
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Restaurants (id INTEGER PRIMARY KEY, name TEXT UNIQUE, city_id INTEGER, rating INTEGER, user_review_count INTEGER, cuisine_id INTEGER,FOREIGN KEY (city_id) REFERENCES Cities(id),FOREIGN KEY (cuisine_id) REFERENCES Cuisines(id))"
    )
    data=restaurants['data']['data']
    for i in range(25):
        rest=data[i]
        name=rest['name']
        rating=rest['averageRating']
        r_count=rest['userReviewCount']
        cuisine=rest['establishmentTypeAndCuisineTags'][0]
        city=rest['parentGeoName']
        cur.execute("SELECT id FROM Cities WHERE city = ?",(city,))
        city_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM Cuisines WHERE cuisine = ?",(cuisine,))
        cuisine_id = cur.fetchone()[0]
        cur.execute("""
                    INSERT OR IGNORE INTO Restaurants(name,city_id, rating , user_review_count , 
                    cuisine_id) VALUES (?,?,?,?,?)""",(name,city_id,rating,r_count,cuisine_id))
        conn.commit()


cur,conn = setup_database("weather.db")
data=search_restaurants("Chicago")
create_cuisines_table(data,cur,conn)
create_restaurants_table(data,cur,conn)

    


