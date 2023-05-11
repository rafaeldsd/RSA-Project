import paho.mqtt.client as mqtt
import sys, json, multiprocessing as mp
from datetime import datetime
import sqlite3, math

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("OBU "+ str(client._client_id.decode("utf-8")) +": Connected OK")
    else:
        print("OBU "+ str(client._client_id.decode("utf-8")) +": Bad connection Returned code=",rc)

def on_disconnect(client, userdata, flags, rc=0):
    print("OBU "+ str(client._client_id.decode("utf-8")) +": Disconnected result code "+str(rc))

def on_message(client, userdata, msg):  
    topic=msg.topic
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    denm=json.loads(m_decode)
    broker = client._client_id.decode("utf-8")

    # get the coordinates of this OBU
    conn = sqlite3.connect('../obu.db')
    c = conn.cursor()
    c.execute("SELECT * FROM obu WHERE ip=?", (broker,))
    obu = c.fetchone()
    conn.close()

    # check what type of obu is
    # if it is a car and an emergency veicle without an emergency
    if obu[4] == "CAR" or (obu[4] in ["AMBULANCE", "FIRE", "POLICE"] and obu[5] == 0):
        # check if the car is within 50 meters of the OBU and if it is moving
        if is_within(obu[2], obu[1], denm['management']['eventPosition']['latitude'], denm['management']['eventPosition']['longitude'],50) and denm['management']['situation']['informationQuality'] == 7:
            print("OBU " + str(client._client_id.decode("utf-8")) + " detected movement in the area with id: " + str(denm['management']['actionID']['originatingStationID']))
            # check if it is emergency vehicle
            if denm['management']['situation']['eventType']['causeCode'] == 4:
                if denm['management']['situation']['eventType']['subCauseCode'] == 2:
                    print("OBU"+ str(client._client_id) +" detected an ambulance")
                elif denm['management']['situation']['eventType']['subCauseCode'] == 3:
                    print("OBU"+ str(client._client_id) +" detected a fire truck")
                elif denm['management']['situation']['eventType']['subCauseCode'] == 4:
                    print("OBU"+ str(client._client_id) +" detected a police car")
                else:
                    print("OBU"+ str(client._client_id) +" detected an unknown emergency vehicle")
                # Print a alert message to the driver of the car, telling him to get out of the way
                print("PLEASE GET OUT OF THE WAY OF THE EMERGENCY VEHICLE!")
                if is_within(obu[2], obu[1], denm['management']['eventPosition']['latitude'], denm['management']['eventPosition']['longitude'],25):
                    print("YOU ARE TOO CLOSE TO THE EMERGENCY VEHICLE!")
                    print("MOVE IMMEDIATELY!")
            else:
                print("OBU " + str(client._client_id.decode("utf-8")) + " detected a DENM message with cause code: " + str(denm['management']['situation']['eventType']['causeCode']) + " and subcause code: " + str(denm['management']['situation']['eventType']['subCauseCode']))
    if obu[4] in ["AMBULANCE", "FIRE", "POLICE"] and obu[5] == 1:
        sendDenm(client, obu)
        


def sendDenm(client, obu):
    # Check what type of vehicle is
    if obu[4] == "AMBULANCE":
        f = open("../messages/DENM_ambulance.json", "r")
    elif obu[4] == "FIRE":
        f = open("../messages/DENM_firefighters.json", "r")
    elif obu[4] == "POLICE":
        f = open("../messages/DENM_police.json", "r")
    else:
        print("OBU " + str(client._client_id.decode("utf-8")) + " has an invalid type")
        return
    denm = json.load(f)
    denm['management']['actionID']['sequenceNumber'] += 1
    denm['management']['actionID']['originatingStationID'] = obu[0]
    denm['management']['eventPosition']['latitude'] = obu[1]
    denm['management']['eventPosition']['longitude'] = obu[2]
    denm['management']['detectionTime'] = datetime.timestamp(datetime.now())
    denm['management']['referenceTime'] = datetime.timestamp(datetime.now())
    obu.publish("vanetza/in/denm", json.dumps(denm))
    f.close()

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

def is_within(lon1, lat1, lon2, lat2, dist):
    """
    Check if the distance between two points is less than a given distance
    """
    distance = haversine(lon1, lat1, lon2, lat2)
    return distance < dist

def obu_process(broker):
    # Connect to MQTT broker
    client = mqtt.Client(broker)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.loop_start()
    client.connect(broker)

    # ...

    client.loop_stop()
    client.disconnect()

def obu_sim(brokers):
    processes = []

    print("Starting OBU processes")
    for broker in brokers:
        print("Starting OBU process for broker: " + broker[0])
        p = mp.Process(target=obu_process, args=[broker[0]])
        p.start()
        processes.append(p)
        
    for p in processes:
        p.join()

    print("OBU processes finished")

if __name__ == '__main__':
    try:
        obu_sim([("192.168.98.30",1), ("192.168.98.40",2), ("192.168.98.50",3), ("192.168.98.60",4)])
    except KeyboardInterrupt:
        print("Received interrupt signal. Stopping OBU processes...")
        for p in mp.active_children():
            p.terminate()
        print("OBU processes stopped")
        sys.exit(0)