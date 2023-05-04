import googlemaps
import json
import datetime
from polyline import decode 

gmaps = googlemaps.Client(key='AIzaSyB5IcIzPvGKxfBjbzl6x1f_T_DdABVk-u4')

directions_result = gmaps.directions((40.630519, -8.654069) , (40.633434, -8.658704), mode="driving", departure_time=datetime.datetime.now())
coords_list = []

for step in directions_result[0]['legs'][0]['steps']:
    decoded_points = decode(step['polyline']['points'])
    for lat, lng in decoded_points:
        coords_list.append({"latitude": lat, "longitude": lng})
# write it in the static/coords.json file
with open('static/police_coords.json', 'w') as file:
    json.dump(coords_list, file)