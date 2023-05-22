import googlemaps
import json
import datetime
from polyline import decode 


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
    get_coords(40.635427,-8.655346,40.629565, -8.660002,1)
    get_coords(40.627138,-8.661054,40.638840, -8.657047,2)
    get_coords(40.630633,-8.653882,40.637057, -8.653239,3)
    get_coords(40.631635,-8.657348,40.638562, -8.656779,4)
