import paho.mqtt.client as mqtt
import time, sys, os, json, random, multiprocessing as mp
from datetime import datetime
import sqlite3

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("OBU"+ str(client._client_id) +": Connected OK")
    else:
        print("OBU"+ str(client._client_id) +": Bad connection Returned code=",rc)

def on_disconnect(client, userdata, flags, rc=0):
    print("OBU"+ str(client._client_id) +": Disconnected result code "+str(rc))

def on_message(client, userdata, msg):  
    topic=msg.topic
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    denm=json.loads(m_decode)
    if denm['fields']['denm']['situation']['eventType']['causeCode'] == 4:
        print("OBU"+ str(client._client_id) +" detected an emergency vehicle in the area")
        if denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 2:
            print("OBU"+ str(client._client_id) +" detected an ambulance")
        elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 3:
            print("OBU"+ str(client._client_id) +" detected a fire truck")
        elif denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 4:
            print("OBU"+ str(client._client_id) +" detected a police car")
        else:
            print("OBU"+ str(client._client_id) +" detected an unknown emergency vehicle")
    else:
        print("OBU"+ str(client._client_id) +" detected a DENM message with cause code: " + str(denm['fields']['denm']['situation']['eventType']['causeCode']) + " and subcause code: " + str(denm['fields']['denm']['situation']['eventType']['subCauseCode']))

def obu_process(broker):
    # Connect to MQTT broker
    obu = mqtt.Client(broker)
    obu.on_connect = on_connect
    obu.on_disconnect = on_disconnect
    obu.on_message = on_message

    obu.loop_start()
    obu.connect(broker)

    # ...

def obu_sim(broker_obus):
    process_obus = []

    for broker in broker_obus:
        p = mp.Process(target=obu_process, args=[broker[0]])
        p.start()
        process_obus.append(p)
    
    for p in process_obus:
        p.join()

if __name__ == '__main__':
    obu_sim([("192.168.98.30",1), ("192.168.98.31",2), ("192.168.98.32",3), ("192.168.98.33",4)])