import sqlite3
from flask import Flask, render_template, request , jsonify
from db_obu import obu_db_create
from db_rsu import rsu_db_create


app = Flask(__name__)

#GOOGLE_MAPS_API_KEY ="AIzaSyDcLG_2KgktdQJXLaeyQZHJzmvcSjNwoPM"

@app.route("/")
def home():
    # Connect to database
    conn_rsu = sqlite3.connect('rsu.db')
    rsu =  conn_rsu.execute("SELECT * FROM rsu").fetchall()
    print(rsu)

    if request.is_json:
        conn_obu = sqlite3.connect('obu.db')
        obu = conn_obu.execute("SELECT * FROM rsu").fetchall()
        obu_json = {}

        for row in obu:
            obu_json.update({row[0]:{"latitude":row[1], "longitude":row[2]}})
        
        return jsonify(obu_json)

    # Render home page with Google Maps and location data
    return render_template("home.html", rsu=rsu)

if __name__ == "__main__":
    # Create database tables
    obu_db_create()
    rsu_db_create()
    app.run(debug=True)