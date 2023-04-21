import random
import time
from flask import Flask, render_template


app = Flask(__name__)

#GOOGLE_MAPS_API_KEY ="AIzaSyDcLG_2KgktdQJXLaeyQZHJzmvcSjNwoPM"

@app.route("/")
def home():
    # Render home page with Google Maps and location data
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)