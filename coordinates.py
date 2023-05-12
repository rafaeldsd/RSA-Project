import googlemaps
import json
import datetime
from polyline import decode 


def get_coords(lat1, lon1, lat2, lon2):   
    gmaps = googlemaps.Client(key='AIzaSyB5IcIzPvGKxfBjbzl6x1f_T_DdABVk-u4')

    directions_result = gmaps.directions((lat1, lon1),(lat2, lon2),mode="driving",departure_time=datetime.datetime.now())
    coords_list = []

    for step in directions_result[0]['legs'][0]['steps']:
        decoded_points = decode(step['polyline']['points'])
        for lat, lng in decoded_points:
            coords_list.append({"latitude": lat, "longitude": lng})

    return coords_list
