import paho.mqtt.client as mqtt
import time, json, sys, multiprocessing as mp
from datetime import datetime
import sqlite3
from math import radians, cos, sin, asin, sqrt, atan2
from db_rsu import rsu_db_create

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("RSU "+ str(client._client_id.decode("utf-8")) +": Connected OK")
    else:
        print("RSU "+ str(client._client_id.decode("utf-8")) +": Bad connection Returned code=",rc)
    
def on_disconnect(client, userdata, flags, rc=0):
    print("RSU "+ str(client._client_id.decode("utf-8")) +": Disconnected result code "+str(rc))

def on_message(client, userdata, msg):
    topic = msg.topic
    m_decode = str(msg.payload.decode("utf-8", "ignore"))
    cam = None
    denm = None
    # get cam and denm messages
    if topic == "vanetza/out/cam":
        cam = json.loads(m_decode)
    elif topic == "vanetza/out/denm":
        denm = json.loads(m_decode)
    else:
        print("RSU " + str(client._client_id.decode("utf-8")) + " received an unknown message")
        return
    broker = client._client_id.decode("utf-8")
    
    # get the coordinates of this RSU
    conn = sqlite3.connect('rsu.db')
    c = conn.cursor()
    c.execute("SELECT * FROM rsu WHERE ip=?", (broker,)) 
    rsu = c.fetchone()
    conn.close()
    # check if the car is within 50 meters of the RSU and if it is moving (CAM)
    if cam is not None:
        if calculate_distance(rsu[1], rsu[2], cam['latitude'], cam['longitude'])<200 and cam['speed'] > 0:
            print("RSU " + str(client._client_id.decode("utf-8")) + " detected a CAM: id(" + str(cam['stationID']) + "), speed(" + str(cam['speed']) + ") and distance(" + str(calculate_distance(rsu[1], rsu[2], cam['latitude'], cam['longitude'])) + "m)", end=" ")
            #check if exists a ["specialVehicle"]["emergencyContainer"] in the cam message
            if 'emergencyContainer' in cam["specialVehicle"]:
                # check if it is emergency vehicle 
                if cam["specialVehicle"]["emergencyContainer"]["lightBarSirenInUse"]["lightBarActivated"] == True and cam["specialVehicle"]["emergencyContainer"]["lightBarSirenInUse"]["sirenActivated"] == True:
                    print("(Special vehicle in emergency)")
                else:
                    print("(Special vehicle not in emergency)")
            else:
                print("(Normal vehicle)")

    
    # check if the car is within 50 meters of the RSU and if it is moving (DENM)
    if denm is not None:
        if calculate_distance(rsu[1], rsu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])<200 and denm['fields']['denm']['situation']['informationQuality'] == 7:
            print("RSU " + str(client._client_id.decode("utf-8")) + " detected a DENM: id(" + str(denm['fields']['denm']['management']['actionID']["originatingStationID"]) + "), informationQuality(" + str(denm['fields']['denm']['situation']['informationQuality']) + ")", end=" ")
            # check if it is emergency vehicle
            if denm['fields']['denm']['situation']['eventType']['causeCode'] == 4:
                print("and Emergency vehicle (", end="")
                if denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 2:
                    print("Ambulance)")
                elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 3:
                    print("Fire truck)")
                elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 4:
                    print("Police car)")
                else:
                    print("Unknown)")
            else:
                print("and unknown causeCode(" + str(denm['fields']['denm']['situation']['eventType']['causeCode']) + ")")
            
'''
#Use of geographiclib to make geodesic calculations
#Documentation https://geographiclib.sourceforge.io/html/python/index.html
    and https://geographiclib.sourceforge.io/2009-03/classGeographicLib_1_1Geodesic.html
#Author: Charles F. F. Karney (charles@karney.com)
#To install the package 'pip install geographiclib'

#Code:

from geographiclib.geodesic import Geodesic

geod = Geodesic.WGS84

geo = Geodesic.WGS84.Inverse(lat1, long1, lat2, long2)

distance = geo['s12'] #in meters
heading = geo[azi2] #in degrees clockwise

#print test:
print("The distance is {:.3f} m.".format(geo['s12']))
print("The distance is {:.3f} m.".format(geo['azi2']))

geo_cam-rsu = Geodesic.WGS84.Inverse(cam['latitude'], cam['longitude'],rsu[1], rsu[2])

geo_demn-rsu = Geodesic.WGS84.Inverse(denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'], rsu[1], rsu[2])

dist_cam = cam-rsu['s12']
dist_demn = demn-rsu['s12']
head_cam = cam-rsu['azi2']
head_demn = demn-rsu['azi2']
'''




def calculate_distance(lat1, lon1, lat2, lon2):
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Radius of the Earth in meters
    earth_radius = 6371000.0

    # Calculate the differences in latitude and longitude
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Use the Haversine formula to calculate the distance
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = earth_radius * c

    # Return the distance rounded to 3 decimal places
    return round(distance,3)

def rsu_process(broker):
    # Connect to MQTT broker

    client = mqtt.Client(broker) #create new instance
    client.on_connect = on_connect #bind call back function
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    client.loop_start()
    try:
        client.connect(broker) #connect to broker
    except: 
        print("Could not connect to broker " + broker)
        sys.exit(1)
    
    while(True):
        client.subscribe('vanetza/out/cam')
        client.subscribe('vanetza/out/denm')
        time.sleep(0.1)
  

def rsu_sim(brokers):
    processes = []

    print("Starting RSU processes")
    for broker in brokers:
        print("Starting RSU process for broker: " + broker[0])
        p = mp.Process(target=rsu_process, args=[broker[0]])
        p.start()
        processes.append(p)
        
    for p in processes:
        p.join()

    print("RSU processes finished")

if __name__ == "__main__":
    try:
        rsu_db_create()
        rsu_sim([("192.168.98.70", 10), ("192.168.98.80",11)])
    except KeyboardInterrupt:
        print("Received interrupt signal. Stopping RSU processes...")
        for p in mp.active_children():
            p.terminate()
        print("RSU processes stopped")
        sys.exit(0)



    