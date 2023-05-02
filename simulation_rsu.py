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
    