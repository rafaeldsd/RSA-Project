import paho.mqtt.client as mqtt
import sys, json, multiprocessing as mp
from datetime import datetime
from coordinates import get_coords
import sqlite3, math, time
from db_obu import obu_db_create
from geographiclib.geodesic import Geodesic



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
    conn = sqlite3.connect('obu.db')
    c = conn.cursor()
    c.execute("SELECT * FROM obu WHERE ip=?", (broker,))
    obu = c.fetchone()
    conn.close()
    # check what type of obu is
    # if it is a car and an emergency vehicle without an emergency
    if obu[6] == "CAR" or (obu[6] in ["AMBULANCE", "FIRE", "POLICE"] and obu[7] == False):
        # check if the car is within 50 meters of the OBU and if it is moving
        if get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]<250 and denm['fields']['denm']['situation']['informationQuality'] == 7:
            print("OBU " + str(client._client_id.decode("utf-8")) + " detected a DENM: id(" + str(denm['fields']['denm']['management']['actionID']['originatingStationID']) + "), informationQuality(" + str(denm['fields']['denm']['situation']['informationQuality']) + ")", end=" ")
            # check if it is emergency vehicle
            if denm['fields']['denm']['situation']['eventType']['causeCode'] == 4:
                print("and Emergency vehicle (", end="")
                if denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 2:
                    print("Ambulance)")
                    print("An ambulance is " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]) + " meters away. Please take precautions!")
                elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 3:
                    print("Fire truck)")
                    print("A fire truck is " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]) + " meters away. Please take precautions!")
                elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 4:
                    print("Police car)")
                    print("A police car is " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]) + " meters away. Please take precautions!")
                else:
                    print("Unknown)")

            else:
                print("and unknown causeCode(" + str(denm['fields']['denm']['situation']['eventType']['causeCode']) + ")")

            if get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0] < 100:
                print("ATTENTION! Emergency vehicle less than 50 meters away. Please take precautions immediately.")
            
    
def sendCam(client,obu):
    if obu[6] == "AMBULANCE" or obu[6] == "FIRE" or obu[6] == "POLICE":
        f = open("messages/CAM_emergency.json", "r")
    else:
        f = open("messages/CAM_car.json", "r")
    cam = json.load(f)
    cam['stationID'] = obu[0]
    cam['latitude'] = obu[1]
    cam['longitude'] = obu[2]

    if obu[7] == True:
        cam['specialVehicle']['emergencyContainer']["lightBarSirenInUse"]["lightBarActivated"] = True
        cam['specialVehicle']['emergencyContainer']["lightBarSirenInUse"]["sirenActivated"] = True
    client.publish("vanetza/in/cam", json.dumps(cam))
    # print("Client " + client._client_id.decode("utf-8") + " published a CAM message")
    f.close()  
        
def sendDenm(client,obu):
    # Check what type of vehicle is
    if obu[6] == "AMBULANCE":
        f = open("messages/DENM_ambulance.json", "r")
    elif obu[6] == "FIRE":
        f = open("messages/DENM_firefighters.json", "r")
    elif obu[6] == "POLICE":
        f = open("messages/DENM_police.json", "r")
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
    # print("Client " + client._client_id.decode("utf-8") + " published a DENM message")
    f.close()

def get_dis_dir(lat1, lon1, lat2, lon2):
    geo = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)

    distance = geo['s12'] #in meters
    heading = geo['azi2'] #in degrees clockwise from north

    # heading from -180 to 180
    if heading >-30 and heading <30:
        heading = "North"
    elif heading >30 and heading <60:
        heading = "North-East"
    elif heading >60 and heading <120:
        heading = "East"
    elif heading >120 and heading <150:
        heading = "South-East"
    elif heading >150 or heading <-150:
        heading = "South"
    elif heading >-150 and heading <-120:
        heading = "South-West"
    elif heading >-120 and heading <-60:
        heading = "West"
    elif heading >-60 and heading <-30:
        heading = "North-West"
    else:
        heading = "Unknown"

    return round(distance,3), heading

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
    
    # wait until the connection is established
    while not client.is_connected():
        pass
    time.sleep(0.5)
    
    # read the coordinates from the file
    with open('paths/coords'+str(id)+'.json') as json_file:
        coords = json.load(json_file)
    i = 0
    # until it reaches the end of the path
    while i < len(coords):
        client.subscribe('vanetza/out/denm')
        # get updated latitude and longitude of the OBU from the database
        conn = sqlite3.connect('obu.db')
        c = conn.cursor()
        c.execute("SELECT * FROM obu WHERE id=?", (id,))
        obu = c.fetchone()
        conn.close()

        if (obu[1] != obu[3]) or (obu[2] != obu[4]):
            # update the OBU's position
            conn = sqlite3.connect('obu.db')
            c = conn.cursor()
            c.execute("UPDATE obu SET ilatitude=?, ilongitude=? WHERE id=?", (coords[i]['latitude'], coords[i]['longitude'], id))
            conn.commit()
            conn.close()
        # send CAM messages
        sendCam(client,obu)
        # send DENM messages if the OBU is an emergency vehicle and is in emergency mode
        if obu[6] in ["AMBULANCE", "FIRE", "POLICE"] and obu[7] == True:
            sendDenm(client,obu)
        i += 1
        time.sleep(0.5)
    print("OBU " + str(id) + " finished the path")
    client.loop_stop()
    client.disconnect()

'''
#TO DO!:
#*Calculate the heading of each OBU base on the current coordinates (lat,long) and the previous
#*Pass the heading value to the DENM 'semiMajorOrientation' field and the CAM 'heading' field
#Method:

geo = Geodesic.WGS84.Inverse(obu[1], obu[2], obu[3], obu[4])  #lat1 and long1 are the previous coordinates, lat2 and long2 are the current coordinates of the OBU 

heading = geo[azi2] #in degrees clockwise
distance = geo[s12] #in meters

'''


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
        obu_db_create()
        obu_sim([("192.168.98.30",1), ("192.168.98.40",2), ("192.168.98.50",3), ("192.168.98.60",4)])
    except KeyboardInterrupt:
        print("Received interrupt signal. Stopping OBU processes...")
        for p in mp.active_children():
            p.terminate()
        print("OBU processes stopped")
        sys.exit(0)