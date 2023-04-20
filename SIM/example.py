import json
import paho.mqtt.client as mqtt
import threading
from time import sleep

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")
    # ...

# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))
    
    print('Topic: ' + msg.topic)
    print('Message' + message)

    # lat = message["latitude"]
    # ...

def generate(client):
    f = open('examples/in_cam.json')
    m = json.load(f)
    m["latitude"] = 0
    m["longitude"] = 0
    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()
    sleep(1)

obu = [] # Lista de OBU's
obu[0] = mqtt.Client()
obu[0].on_connect = on_connect
obu[0].on_message = on_message
obu[0].connect("192.168.98.30", 1883, 60)

obu[1] = mqtt.Client()
obu[1].on_connect = on_connect
obu[1].on_message = on_message
obu[1].connect("192.168.98.31", 1883, 60)

obu[2] = mqtt.Client()
obu[2].on_connect = on_connect
obu[2].on_message = on_message
obu[2].connect("192.168.98.32", 1883, 60)
 
for i in obu:
    threading.Thread(target=i.loop_forever).start()

for i in obu:
    threading.Thread(target=i.loop_forever).join()


while(True):
    generate()

for i in obu:
    i.loop_stop()
    print ("Client disconnected")

