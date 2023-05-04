import paho.mqtt.client as mqtt
import time, sys, os, json, random, multiprocessing as mp
from datetime import datetime
import sqlite3

emergency = []

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
    print("OBU"+ str(client._client_id) +": message received",m_decode)
    denm = json.loads(m_decode)
    if denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 2 or denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 3 or denm['fields']['denm']['situation']['eventType']['subCauseCode'] == 4:
        emergency[ int(client._client_id) - 1 ] = True
    else:
        emergency[ int(client._client_id) - 1 ] = False
    
