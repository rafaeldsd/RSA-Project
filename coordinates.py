import googlemaps
import json
import datetime
from polyline import decode 
import sqlite3

def get_coords(lat1, lon1, lat2, lon2,id):   
    gmaps = googlemaps.Client(key='AIzaSyB5IcIzPvGKxfBjbzl6x1f_T_DdABVk-u4')

    directions_result = gmaps.directions((lat1, lon1),(lat2, lon2),mode="driving",departure_time=datetime.datetime.now())
    coords_list = []

    for step in directions_result[0]['legs'][0]['steps']:
        decoded_points = decode(step['polyline']['points'])
        for lat, lng in decoded_points:
            coords_list.append({"latitude": lat, "longitude": lng})
    # Write it to a file /paths/coords{id}.json
    with open('paths/coords'+str(id)+'.json', 'w') as outfile:
        json.dump(coords_list, outfile)

if __name__ == "__main__":
    # get obu data from db
    conn = sqlite3.connect('obu.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM obu''')
    obus = c.fetchall()
    conn.close()
    # get the coordinates for each obu
    for obu in obus:
        get_coords(obu[1],obu[2],obu[3],obu[4],obu[0])

