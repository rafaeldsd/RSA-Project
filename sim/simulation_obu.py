import paho.mqtt.client as mqtt
import sys, json, multiprocessing as mp
from datetime import datetime
import sqlite3, math, time

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
    # if it is a car and an emergency vehicle without an emergency
    if obu[4] == "CAR" or (obu[4] in ["AMBULANCE", "FIRE", "POLICE"] and obu[5] == False):
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
        
def sendCam(client,obu):
    if obu[4] == "AMBULANCE" or obu[4] == "FIRE" or obu[4] == "POLICE":
        f = open("../messages/CAM_emergency.json", "r")
    else:
        f = open("../messages/CAM_car.json", "r")
    cam = json.load(f)
    cam['stationID'] = obu[0]
    cam['latitude'] = obu[1]
    cam['longitude'] = obu[2]

    if obu[5] == True:
        cam['specialVehicle']['emergencyContainer']["lightBarSirenInUse"]["lightBarActivated"] = True
        cam['specialVehicle']['emergencyContainer']["lightBarSirenInUse"]["sirenActivated"] = True
    client.publish("vanetza/in/cam", json.dumps(cam))
    print("Client " + client._client_id.decode("utf-8") + " published a CAM message")
    f.close()  
        
def sendDenm(client,obu):
    # Check what type of vehicle is
    if obu[4] == "AMBULANCE":
        f = open("../messages/DENM_ambulance.json", "r")
    elif obu[4] == "FIRE":
        f = open("../messages/DENM_firefighters.json", "r")
    elif obu[4] == "POLICE":
        f = open("../messages/DENM_police.json", "r")
    else:
        print("OBU " + str(obu[0]) + " has a invalid type")
        return
    denm = json.load(f)
    denm['management']['actionID']['sequenceNumber'] += 1
    denm['management']['actionID']['originatingStationID'] = obu[0]
    denm['management']['eventPosition']['latitude'] = obu[1]
    denm['management']['eventPosition']['longitude'] = obu[2]
    denm['management']['detectionTime'] = datetime.timestamp(datetime.now())
    denm['management']['referenceTime'] = datetime.timestamp(datetime.now())
    client.publish("vanetza/in/denm", json.dumps(denm))
    print("Client " + client._client_id.decode("utf-8") + " published a DENM message")
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

def obu_process(broker,id):
    # Connect to MQTT broker
    client = mqtt.Client(broker)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.loop_start()
    try:
        client.connect(broker)    
    except:
        print("Could not connect to broker: " + broker)
        sys.exit(1)

    # send CAM messages every 2 seconds and keeps track of the OBU's position
    while True:
        # get updated latitude and longitude of the OBU from the database
        conn = sqlite3.connect('../obu.db')
        c = conn.cursor()
        c.execute("SELECT * FROM obu WHERE id=?", (id,))
        obu = c.fetchone()
        conn.close()
        sendCam(client,obu)
        # send DENM messages if the OBU is an emergency vehicle and is in emergency mode
        if obu[4] in ["AMBULANCE", "FIRE", "POLICE"] and obu[5] == True:
            sendDenm(client,obu)
        time.sleep(2)



def obu_sim(brokers):
    processes = []

    print("Starting OBU processes")
    for broker in brokers:
        print("Starting OBU process for broker: " + broker[0])
        p = mp.Process(target=obu_process, args=[broker[0],broker[1]])
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