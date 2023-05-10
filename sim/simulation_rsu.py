import paho.mqtt.client as mqtt
import time, json, sys, multiprocessing as mp
from datetime import datetime
import sqlite3

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
    cam = json.loads(m_decode)
    broker = client._client_id.decode("utf-8")
    print("RSU " + str(client._client_id.decode("utf-8")) + " received a CAM message")

    if cam['speed'] > 0:
        print("RSU " + str(client._client_id.decode("utf-8")) + " detected movement in the area with id: " + str(cam['stationID']))
        # check if it is emergency vehicle
        if 'specialVehicle' in cam and cam['specialVehicle'] is not None and cam['specialVehicle']['type'] in ['AMBULANCE', 'FIRE', 'POLICE']:
            print("RSU" + str(client._client_id) + " detected an emergency vehicle")
            # send DENM
            sendDenm(client, cam['stationID'])
        else:
            print("RSU " + str(client._client_id.decode("utf-8")) + " detected a car")
    
def sendDenm(rsu,id):
    # Check what type of vehicle is
    if id == 0:
        f = open("../messages/DENM_ambulance.json", "r")
    elif id == 1:
        f = open("../messages/DENM_firefighters.json", "r")
    elif id == 2:
        f = open("../messages/DENM_police.json", "r")
    denm = json.load(f)
    denm['management']['actionID']['sequenceNumber'] += 1
    denm['management']['actionID']['stationID'] = id
    denm['detectionTime'] = datetime.timestamp(datetime.now())
    denm['referenceTime'] = datetime.timestamp(datetime.now())
    rsu.publish("vanetza/in/denm", json.dumps(denm))
    f.close()

def rsu_process(broker):
    # Connect to MQTT broker
    client = mqtt.Client(broker)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.loop_start()
    client.connect(broker) 

    
    while(True):
        client.subscribe('vanetza/out/cam')
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
        rsu_sim([("192.168.98.70", 1), ("192.168.98.80",2)])
    except KeyboardInterrupt:
        print("Received interrupt signal. Stopping RSU processes...")
        for p in mp.active_children():
            p.terminate()
        print("RSU processes stopped")
        sys.exit(0)



    