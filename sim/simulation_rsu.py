import paho.mqtt.client as mqtt
import time, sys, os, json, random, multiprocessing as mp
from datetime import datetime
import sqlite3

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("RSU"+ str(client._client_id) +": Connected OK")
    else:
        print("RSU"+ str(client._client_id) +": Bad connection Returned code=",rc)

def on_disconnect(client, userdata, flags, rc=0):
    print("RSU"+ str(client._client_id) +": Disconnected result code "+str(rc))

def on_message(client, userdata, msg):  
    topic=msg.topic
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    cam=json.loads(m_decode)
    broker = client._client_id.decode("utf-8")
    print("RSU"+ str(client._client_id) +": Message received-> " + m_decode)

    if cam['speed'] > 0:
        print("RSU"+ str(client._client_id) +" detected movement in the area with id: " + str(cam['stationID']))
        #check if it is emergency vehicle
        if cam['specialVehicle']['type'] == 'AMBULANCE' or cam['specialVehicle']['type'] == 'FIRE' or cam['specialVehicle']['type'] == 'POLICE':
            print("RSU"+ str(client._client_id) +" detected an emergency vehicle")
            #send DENM
            sendDenm(client, cam['stationID'])
    
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
    client.on_connect=on_connect
    client.on_disconnect=on_disconnect
    client.on_message=on_message

    client.loop_start()
    client.connect(broker)

    while(True):
        client.subscribe("vanetza/out/cam")
        time.sleep(1)
    print("RSU"+ str(client._client_id) +": Process finished")
    client.loop_stop()
    client.disconnect()

def rsu_sim(broker_rsus):
    mqtt.Client.dcnt_flag = True

    proc_list = []

    for broker in broker_rsus:
        proc = mp.Process(target=rsu_process, args=(broker[0],))
        proc_list.append(proc)
        proc.start()

    for proc in proc_list:
        proc.join()

if __name__ == "__main__":
    rsu_sim([("192.168.98.15", 1), ("192.168.98.16",2), ("192.168.98.17",3), ("192.168.98.18",4), ("192.168.98.19",5)])

    

    