import requests
import sqlite3
import json
import os
import matplotlib.pyplot as plt
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

def restaurant_calc(city,cur,conn):
    cur.execute("SELECT id, cuisine FROM Cuisines")
    cuisines = cur.fetchall()
    l_cuisine=[]
    l_count=[]
    l_rating=[]
    f=open("RestaurantsReport.txt","w")
    f.write(f"Restaurants Report for {city}\n\n")
    for cid, cname in cuisines:
        cur.execute("SELECT ROUND(AVG(rating),1) FROM Restaurants JOIN Cities ON Restaurants.City_id = Cities.id WHERE Cities.city= ? and Restaurants.cuisine_id = ? ",(city,cid))
        result1 = cur.fetchone()[0]
        cur.execute("SELECT ROUND(AVG(user_review_count)) FROM Restaurants JOIN Cities ON Restaurants.City_id = Cities.id WHERE Cities.city= ? and Restaurants.cuisine_id = ? ",(city,cid))
        result2 = cur.fetchone()[0]
        cur.execute("SELECT name FROM Restaurants JOIN Cities ON Restaurants.City_id = Cities.id WHERE Cities.city= ? and Restaurants.cuisine_id = ? ORDER BY Restaurants.rating DESC LIMIT 1",(city,cid))
        result3 = cur.fetchone()
        if result1:
            f.write(f"{cname} Restaurants\n")
            f.write(f"Average Rating: {result1}\n")
            f.write(f"Average number of User Reviews: {result2}\n")
            f.write(f"Highest-rated Restaurant: {result3[0]}\n\n")
            l_cuisine.append(cname)
            l_rating.append(result1)
            cur.execute("SELECT COUNT(*) FROM Restaurants JOIN Cities ON Restaurants.City_id = Cities.id WHERE Cities.city= ? and Restaurants.cuisine_id = ? ",(city,cid))
            l_count.append(cur.fetchone()[0])
    f.close()
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.bar(l_cuisine, l_rating, color='skyblue')
    plt.ylim(0, 5)
    plt.title("Average Rating per Cuisine")
    plt.xlabel("Cuisine")
    plt.ylabel("Avg Rating")
    plt.xticks(rotation=45, ha='right')
    plt.subplot(1, 2, 2)
    plt.pie(l_count, labels=l_cuisine, autopct='%1.0f%%', startangle=90, labeldistance=1.1)
    plt.title("Cuisine Popularity")
    plt.tight_layout()
    plt.show()
def restaurants_call(cur,conn,city):
    cur.execute("SELECT city_id FROM Restaurants JOIN Cities ON Cities.id = Restaurants.city_id WHERE Cities.city=?",(city,))
    check=cur.fetchone()
    if(not check):
        data=search_restaurants(city)
        create_cuisines_table(data,cur,conn)
        create_restaurants_table(data,cur,conn)
    restaurant_calc(city,cur,conn)





