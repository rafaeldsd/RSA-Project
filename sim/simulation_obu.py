import paho.mqtt.client as mqtt
import sys, json, multiprocessing as mp
from datetime import datetime
import sqlite3

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