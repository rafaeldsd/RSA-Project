import paho.mqtt.client as mqtt
import sys, json, multiprocessing as mp
from datetime import datetime
from coordinates import get_coords
import sqlite3, math, time
from db_obu import obu_db_create
from geographiclib.geodesic import Geodesic
from simulation_rsu import *

stop = None
def on_connect(client, userdata, flags, rc):    
    if rc==0:
        print("OBU "+ str(client._client_id.decode("utf-8")) +": Connected OK")
    else:
        print("OBU "+ str(client._client_id.decode("utf-8")) +": Bad connection Returned code=",rc)

def on_disconnect(client, userdata, flags, rc=0):
    print("OBU "+ str(client._client_id.decode("utf-8")) +": Disconnected result code "+str(rc))

def dif_heading (relative_heading, evr_heading):
    if relative_heading >= evr_heading:
        ref_heading=relative_heading-evr_heading
    else:
        ref_heading=evr_heading-relative_heading
    if ref_heading>180:
        ref_heading=360-ref_heading        
    return ref_heading    

def get_obu_signalGoup (camHeading):
    street_headdin_one_way, street_headdin_the_other_way = street_headding()
    if int(camHeading) in range((street_headdin_one_way - 10), (street_headdin_one_way + 10)):
        signalGroup = 0
    elif int(camHeading) in range ((street_headdin_the_other_way - 10), (street_headdin_the_other_way + 10)):
        signalGroup = 2
    elif int(camHeading) in range((street_headdin_one_way - 80), (street_headdin_one_way -100)):
        signalGroup = 1
    elif int(camHeading) in range ((street_headdin_the_other_way - 80), (street_headdin_the_other_way - 100)):
        signalGroup = 3
    else:
        signalGroup = 0
    return signalGroup

def on_message(client, userdata, msg):  
    topic=msg.topic
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    cam = None
    denm = None
    spatem = None
    # get cam and denm messages
    if topic == "vanetza/out/cam":
        cam = json.loads(m_decode)
    elif topic == "vanetza/out/denm":
        denm = json.loads(m_decode)
    elif topic == "vanetza/out/spatem":
        spatem = json.loads(m_decode)
    else:
        print("RSU " + str(client._client_id.decode("utf-8")) + " received an unknown message")
        return
        
    broker = client._client_id.decode("utf-8")

    # get the coordinates of this OBU
    conn = sqlite3.connect('obu.db')
    c = conn.cursor()
    c.execute("SELECT * FROM obu WHERE ip=?", (broker,))
    obu = c.fetchone()
    conn.close()

    if cam != None:
        signalGroup = get_obu_signalGoup(cam['heading'])
    else:
        signalGroup = 0

    # check what type of obu is
    # if it is a car and an emergency vehicle without an emergency
    if obu[6] == "CAR" or (obu[6] in ["AMBULANCE", "FIRE", "POLICE"] and obu[7] == False):               
        if denm != None:
            # check if the car is within 200 meters of the OBU and if it is moving
            if get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]<200 and denm['fields']['denm']['situation']['informationQuality'] == 7:
                print("Other information: ")
                print("\t-Detected a DENM: id(" + str(denm['fields']['denm']['management']['actionID']['originatingStationID']) + "), informationQuality(" + str(denm['fields']['denm']['situation']['informationQuality']) + ")", end=" ")
                # check if it is emergency vehicle
                if denm['fields']['denm']['situation']['eventType']['causeCode'] == 4:
                    print("and Emergency vehicle (", end="")
                    if denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 2:
                        vehicle = "Ambulance"
                        print("Ambulance)")
                        print("\t-An ambulance is " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]) + " meters away in direction " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[1]) + ". Please take precautions!")
                    elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 3:
                        vehicle = "Fire truck"
                        print("Fire truck)")
                        print("\t-A fire truck is " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]) + " meters away in direction " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[1]) + ". Please take precautions!")
                    elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 4:
                        vehicle = "Police car"
                        print("Police car)")
                        print("\t-A police car is " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]) + " meters away in direction " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[1]) + ". Please take precautions!")
                    else:
                        print("Unknown)")
                        vehicle = "Unknown vehicle"

                    # check if the car is within 50 meters of the OBU
                    if get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0] < 50:
                        print('\033[91m' + "\t-ATTENTION! "+ vehicle +" at " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[0]) + " meters in direction " + str(get_dis_dir(obu[1], obu[2], denm['fields']['denm']['management']['eventPosition']['latitude'], denm['fields']['denm']['management']['eventPosition']['longitude'])[1]) + "! Please take precautions immediately!" + '\033[0m')
                    print("\n")
        if cam != None:
            global stop
            # check if the car is within 200 meters of the OBU and if it is moving
            if get_dis_dir(obu[1], obu[2], cam['latitude'], cam['longitude'])[0]<200 and cam['speed'] > 0:
                if 'emergencyContainer' in cam["specialVehicle"]:
                    if cam["specialVehicle"]["emergencyContainer"]["lightBarSirenInUse"]["lightBarActivated"] == True and cam["specialVehicle"]["emergencyContainer"]["lightBarSirenInUse"]["sirenActivated"] == True:
                        print("OBU " + str(client._client_id.decode("utf-8")) + ": " )
                        relative_heading = vehicle_heading(cam['latitude'], cam['longitude'], obu[1], obu[2])
                        print("Displaying emergency vehicle information: ")
                        if get_dis_dir(obu[1], obu[2], cam['latitude'], cam['longitude'])[0]<10:
                            print('\033[91m' + "\t -The emergency response vehicle is next to this veícle" + '\033[0m')
                            stop = True
                        elif dif_heading(relative_heading,int(cam['heading'])) < 60:
                            print('\033[93m' + "\t-There is an emergency response vehicle approaching" + '\033[0m')
                            stop = True
                        elif dif_heading(relative_heading,int(cam['heading'])) > 130:
                            print("\t-The emergency response vehicle is heading away")
                            stop = False
                        else:
                            print("\t-The emergency response vehicle is not coming on this direction")
                            stop = False
    if spatem != None:       
        if spatem['fields']['spat']['intersections'][0]['states'][0]['state-time-speed'][0]['eventState'] == 6:
            print("OBU " + str(client._client_id.decode("utf-8")) + ": " )        
            print("\t-Detected a SPATEM: signalGroup(" + str(spatem['fields']['spat']['intersections'][0]['states'][signalGroup]['signalGroup']) + ") - Displaying traffic light maneuver information: ")
            print('\033[92m' + "\tThe Traffic Light is green, this vehicle can go trought the next crossroad safely\n" + '\033[0m')


def sendCam(client,obu,next_coord):
    if obu[6] == "AMBULANCE" or obu[6] == "FIRE" or obu[6] == "POLICE":
        f = open("messages/CAM_emergency.json", "r")
    else:
        f = open("messages/CAM_car.json", "r")
    cam = json.load(f)
    cam['stationID'] = obu[0]
    cam['heading'] = vehicle_heading(obu[1], obu[2], next_coord['latitude'],next_coord['longitude'])
    cam['latitude'] = obu[1]
    cam['longitude'] = obu[2]    
    if obu[7] == True:
        cam['specialVehicle']['emergencyContainer']["lightBarSirenInUse"]["lightBarActivated"] = True
        cam['specialVehicle']['emergencyContainer']["lightBarSirenInUse"]["sirenActivated"] = True
    client.publish("vanetza/in/cam", json.dumps(cam))
    # print("Client " + client._client_id.decode("utf-8") + " published a CAM message")
    f.close()  
        
def sendDenm(client,obu,next_coord):
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
    denm['management']['eventPosition']['positionConfidenceEllipse']['semiMajorOrientation'] = vehicle_heading(obu[1], obu[2], next_coord['latitude'],next_coord['longitude'])
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

def vehicle_heading(lat1,lon1,lat2,lon2):
    # only get values 0-360
    degree = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)['azi2']
    # cast degree to int
    degree = int(round(degree,0))
    if degree < 0:        
        degree += 360        
    # not valid degree
    if degree not in range(0,360):
        degree = 361  
    return degree
    

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

    client.subscribe('vanetza/out/denm')  
    client.subscribe('vanetza/out/cam')
    client.subscribe('vanetza/out/spatem')
    # read the coordinates from the file
    with open('paths/coords'+str(id)+'.json') as json_file:
        coords = json.load(json_file)
    i = 0
    print("\n")
    # until it reaches the end of the path
    while i < len(coords): 

        # get updated latitude and longitude of the OBU from the database
        conn = sqlite3.connect('obu.db')
        c = conn.cursor()
        c.execute("SELECT * FROM obu WHERE id=?", (id,))
        obu = c.fetchone()
        conn.close()
        # Obu has not finished the path yet
        if (obu[1] != obu[3]) or (obu[2] != obu[4]):
            # No emergency vehicle
            if(obu[7] == False):
                # Emergency vehicle nearby
                if(stop == True):
                    # send CAM messages
                    sendCam(client,obu,coords[i])
                else:
                    # update the OBU's position
                    conn = sqlite3.connect('obu.db')
                    c = conn.cursor()
                    c.execute("UPDATE obu SET ilatitude=?, ilongitude=? WHERE id=?", (coords[i]['latitude'], coords[i]['longitude'], id))
                    conn.commit()
                    conn.close() 
                    # send CAM messages
                    sendCam(client,obu,coords[i])
                    i += 1
            # Emergency vehicle
            if(obu[7] == True):
                # update the OBU's position
                conn = sqlite3.connect('obu.db')
                c = conn.cursor()
                c.execute("UPDATE obu SET ilatitude=?, ilongitude=? WHERE id=?", (coords[i]['latitude'], coords[i]['longitude'], id))
                conn.commit()
                conn.close() 
                # send CAM messages
                sendCam(client,obu,coords[i])
                # send DENM messages
                sendDenm(client,obu,coords[i])
                i += 1

        time.sleep(0.7)
    print("OBU " + str(id) + " finished the path at " + str(datetime.now().time())[:8])
    client.loop_stop()
    client.disconnect()

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