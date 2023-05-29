import sqlite3
from flask import Flask, render_template, request , jsonify
from db_rsu import rsu_db_create
import json
import paho.mqtt.client as mqtt

app = Flask(__name__)

#GOOGLE_MAPS_API_KEY ="AIzaSyDcLG_2KgktdQJXLaeyQZHJzmvcSjNwoPM"

obu_data = []

# Function to fetch updated data
def fetch_data():
    # Connect to database
    conn = sqlite3.connect("rsu.db")
    c = conn.cursor()
    rsu_data = c.execute("SELECT * FROM rsu").fetchall()
    conn.close()
    return rsu_data, obu_data

def on_message(client,userdata,msg):
    topic = msg.topic
    m_decode = str(msg.payload.decode("utf-8","ignore"))
    cam = None
    denm = None
    # get cam and denm messages
    if topic == "vanetza/out/cam":
        cam = json.loads(m_decode)
    """
    elif topic == "vanetza/out/denm":
        denm = json.loads(m_decode)
    """
    if cam is not None:
        id = cam["stationID"]
        # Check if the OBU entry exists in obu_data list
        if id <= len(obu_data):
            obu_data[id - 1][0] = cam["latitude"]
            obu_data[id - 1][1] = cam["longitude"]
        else:
            # Create a new OBU entry
            new_entry = [None] * 2
            new_entry[0] = cam["latitude"]
            new_entry[1] = cam["longitude"]
            obu_data.append(new_entry)
    """
    if denm is not None:
        id = denm["management"]["actionID"]["originatingStationID"]
    """    


@app.route("/")
def home():
    # Fetch the latest data from the database
    rsu, obu = fetch_data()

    # Render home page with Google Maps and location data
    return render_template("home.html", rsu=rsu, obu=obu)

# API endpoint to retrieve updated data
@app.route("/get_data", methods=["GET"])
def get_data():
    # Fetch the latest data from the database
    rsu, obu = fetch_data()
    # Return the updated data as JSON
    return jsonify(rsu=rsu, obu=obu)

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