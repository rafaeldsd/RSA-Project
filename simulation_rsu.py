import paho.mqtt.client as mqtt
import time, json, sys, multiprocessing as mp
from datetime import datetime
import sqlite3, math

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
        if is_within_50m(rsu[2], rsu[1], cam['latitude'], cam['longitude']) and cam['speed'] > 0:
            print("RSU " + str(client._client_id.decode("utf-8")) + " detected movement in the area with id: " + str(cam['stationID']))
            # check if it is emergency vehicle
            if 'specialVehicle' in cam and cam['specialVehicle'] is not None and cam['specialVehicle']['type'] in ['AMBULANCE', 'FIRE', 'POLICE']:
                print("RSU" + str(client._client_id) + " detected an emergency vehicle")            
            else:
                print("RSU " + str(client._client_id.decode("utf-8")) + " detected a car")
    
    # check if the car is within 50 meters of the RSU and if it is moving (DENM)
    if denm is not None:
        if is_within_50m(rsu[2], rsu[1], denm['managment']['eventPosition']['latitude'], denm['managment']['eventPosition']['longitude']) and denm['management']['situation']['informationQuality'] == 7:
            print("RSU " + str(client._client_id.decode("utf-8")) + " detected movement in the area with id: " + str(denm['management']['actionID']['originatingStationID']))
            # check if it is emergency vehicle
            if denm['management']['situation']['eventType']['causeCode'] == 4:
                if denm['management']['situation']['eventType']['subCauseCode'] == 2:
                    print("RSU"+ str(client._client_id) +" detected an ambulance")
                elif denm['management']['situation']['eventType']['subCauseCode'] == 3:
                    print("RSU"+ str(client._client_id) +" detected a fire truck")
                elif denm['management']['situation']['eventType']['subCauseCode'] == 4:
                    print("RSU"+ str(client._client_id) +" detected a police car")
                else:
                    print("RSU"+ str(client._client_id) +" detected an unknown emergency vehicle")
            else:
                print("RSU " + str(client._client_id.decode("utf-8")) + " detected a DENM message with cause code: " + str(denm['management']['situation']['eventType']['causeCode']) + " and subcause code: " + str(denm['management']['situation']['eventType']['subCauseCode']))
            

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000 # multiply by 1000 to get distance in meters

def is_within_50m(lon1, lat1, lon2, lat2):
    """
    Check if the distance between two points is less than 50 meters.
    """
    distance = haversine(lon1, lat1, lon2, lat2)
    return distance < 50

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
        time.sleep(1)
  

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
        rsu_sim([("192.168.98.70", 10), ("192.168.98.80",11)])
    except KeyboardInterrupt:
        print("Received interrupt signal. Stopping RSU processes...")
        for p in mp.active_children():
            p.terminate()
        print("RSU processes stopped")
        sys.exit(0)



    