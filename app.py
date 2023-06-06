import sqlite3
from flask import Flask, render_template, request , jsonify
from db_rsu import rsu_db_create
import json
import paho.mqtt.client as mqtt

app = Flask(__name__)

#GOOGLE_MAPS_API_KEY ="AIzaSyDcLG_2KgktdQJXLaeyQZHJzmvcSjNwoPM"

obu_data_cam = []
obu_data_denm = []

# Function to fetch updated data
def fetch_data():
    # Connect to database
    conn = sqlite3.connect("rsu.db")
    c = conn.cursor()
    rsu_data = c.execute("SELECT * FROM rsu").fetchall()
    conn.close()
    return rsu_data, obu_data_cam, obu_data_denm

def on_message(client,userdata,msg):
    topic = msg.topic
    m_decode = str(msg.payload.decode("utf-8","ignore"))
    cam = None
    denm = None
    # get cam and denm messages
    if topic == "vanetza/out/cam":
        cam = json.loads(m_decode)
    
    elif topic == "vanetza/out/denm":
        denm = json.loads(m_decode)
    
    if cam is not None:
        id = cam["stationID"]
        # Check if the OBU entry exists in obu_data_cam list
        if id <= len(obu_data_cam):
            obu_data_cam[id - 1][0] = round(cam["latitude"],5)
            obu_data_cam[id - 1][1] = round(cam["longitude"],5)
        else:
            # Create a new OBU entry
            new_entry = [None] * 2
            new_entry[0] = round(cam["latitude"],5)
            new_entry[1] = round(cam["longitude"],5)
            obu_data_cam.append(new_entry)
   
    if denm is not None:
        id = denm['fields']['denm']["management"]["actionID"]["originatingStationID"]
        # Check if the OBU entry exists in obu_data_denm list
        if id <= len(obu_data_denm):
            obu_data_denm[id - 1][0] = round(denm['fields']['denm']['management']['eventPosition']['latitude'],5)
            obu_data_denm[id - 1][1] = round(denm['fields']['denm']['management']['eventPosition']['longitude'],5)
        else:
            # Create a new OBU entry
            new_entry = [None] * 2
            new_entry[0] = round(denm['fields']['denm']['management']['eventPosition']['latitude'],5)
            new_entry[1] = round(denm['fields']['denm']['management']['eventPosition']['longitude'],5)
            obu_data_denm.append(new_entry)


@app.route("/")
def home():
    # Fetch the latest data from the database
    rsu, cam, denm = fetch_data()

    # Render home page with Google Maps and location data
    return render_template("home.html", rsu=rsu, cam=cam, denm=denm)

# API endpoint to retrieve updated data
@app.route("/get_data", methods=["GET"])
def get_data():
    # Fetch the latest data from the database
    rsu, cam, denm = fetch_data()
    # Return the updated data as JSON
    return jsonify(rsu=rsu, cam=cam, denm=denm)

if __name__ == "__main__":
    # Create MQTT client and connect to broker
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("192.168.98.70", 1883, 60)
    client.subscribe("vanetza/out/cam")
    client.subscribe("vanetza/out/denm")
    client.loop_start()
    
    # Create database tables
    rsu_db_create()
    app.run(debug=True)