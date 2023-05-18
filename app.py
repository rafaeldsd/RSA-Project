import sqlite3
from flask import Flask, render_template, request , jsonify
from db_obu import obu_db_create
from db_rsu import rsu_db_create


app = Flask(__name__)

#GOOGLE_MAPS_API_KEY ="AIzaSyDcLG_2KgktdQJXLaeyQZHJzmvcSjNwoPM"

# Function to fetch updated data from the database
def fetch_data():
    conn_rsu = sqlite3.connect('rsu.db')
    rsu = conn_rsu.execute("SELECT * FROM rsu").fetchall()
    conn_rsu.close()

    conn_obu = sqlite3.connect('obu.db')
    obu = conn_obu.execute("SELECT * FROM obu").fetchall()
    conn_obu.close()

    return rsu, obu

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
    # Create database tables
    obu_db_create()
    rsu_db_create()
    app.run(debug=True)