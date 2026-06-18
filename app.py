import datetime
import certifi
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

MONGO_URI = "mongodb+srv://dhatchina:Dhatchina%4005@cluster0.ld8bscl.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), tls=True, tlsAllowInvalidCertificates=True)

try:
    client.admin.command('ping')
    print("MongoDB Connected ✅")
except Exception as e:
    print("MongoDB Failed ❌", e)

db = client["smart_campus"]
locations_collection = db["locations"]

CAMPUS_POLYGON = [
    (10.816112, 78.673231),
    (10.816724, 78.673584),
    (10.817008, 78.674302),
    (10.816893, 78.675114),
    (10.816221, 78.675643),
    (10.815339, 78.675721),
    (10.814601, 78.675480),
    (10.813975, 78.674942),
    (10.813621, 78.674141),
    (10.813852, 78.673402),
    (10.814734, 78.673063),
    (10.815623, 78.673098),
]

def point_in_polygon(lat, lng, polygon):
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > lng) != (yj > lng)) and \
           (lat < (xj - xi) * (lng - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# ── DEBUG route — shows all students with raw GPS ──────────
@app.route("/debug")
def debug_page():
    return render_template("dashboard_debug.html")

@app.route("/get_locations")
def get_locations():
    students = list(locations_collection.find({}, {"_id": 0}))
    for s in students:
        s["inside_campus"] = point_in_polygon(
            s["latitude"], s["longitude"], CAMPUS_POLYGON
        )
    return jsonify(students)

# ── DEBUG API — raw data no geofence filter ─────────────────
@app.route("/debug_locations")
def debug_locations():
    students = list(locations_collection.find({}, {"_id": 0}))
    result = []
    for s in students:
        inside = point_in_polygon(s["latitude"], s["longitude"], CAMPUS_POLYGON)
        result.append({
            "student_id":   s["student_id"],
            "latitude":     s["latitude"],
            "longitude":    s["longitude"],
            "inside_campus": inside,
            "updated_at":   str(s.get("updated_at",""))
        })
    return jsonify(result)


@app.route("/update_location", methods=["POST"])
def update_location():
    data = request.json
    sid  = data.get("student_id")
    lat  = data.get("latitude")
    lng  = data.get("longitude")

    if not sid or lat is None or lng is None:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    locations_collection.update_one(
        {"student_id": sid},
        {"$set": {
            "student_id": sid,
            "latitude":   lat,
            "longitude":  lng,
            "updated_at": datetime.datetime.utcnow()
        }},
        upsert=True
    )
    print(f"✅ Saved: {sid} → lat={lat}, lng={lng}")
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)