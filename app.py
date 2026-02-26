import certifi

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from flask import request
import math

app = Flask(__name__)
CORS(app)

# MongoDB Atlas connection
MONGO_URI = "mongodb+srv://dhatchinak05_db_user:Dhatchina05@cluster0.d1uhy06.mongodb.net/smart_campus?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI,tlsCAFile =certifi.where(),tls=True,tlsAllowInvalidCertificates=True)

# Test connection
try:
    client.admin.command('ping')
    print("MongoDB Connected Successfully ✅")
except Exception as e:
    print("MongoDB Connection Failed ❌", e)

db = client["smart_campus"]
locations_collection = db["locations"]

# --------------------------
# Geofence Settings
# --------------------------
CAMPUS_LAT = 11.0168
CAMPUS_LNG = 76.9558
RADIUS = 1000  


def check_geofence(lat, lng):
    R = 6371000
    dLat = math.radians(lat - CAMPUS_LAT)
    dLon = math.radians(lng - CAMPUS_LNG)

    a = math.sin(dLat/2)**2 + math.cos(math.radians(CAMPUS_LAT)) * \
        math.cos(math.radians(lat)) * math.sin(dLon/2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return distance <= RADIUS


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/get_locations")
def get_locations():
    students = list(locations_collection.find({}, {"_id": 0}))

    for student in students:
        inside = check_geofence(student["latitude"], student["longitude"])
        student["inside_campus"] = inside

    return jsonify(students)


@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.json
    print("Received:", data)  
    student_id = data.get("student_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not student_id or latitude is None or longitude is None:
        return jsonify({"status": "error"}), 400

    locations_collection.update_one(
        {"student_id": student_id},
        {
            "$set": {
                "student_id": student_id,
                "latitude": latitude,
                "longitude": longitude
            }
        },
        upsert=True
    )

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)