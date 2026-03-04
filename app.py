from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///aviation.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ── Home Route ───────────────────────────────────────────

@app.route("/")
def home():
    return "AeroGuard Backend Running 🚀"

# ── Models ───────────────────────────────────────────────

class Aircraft(db.Model):
    __tablename__ = "aircraft"
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)
    total_flight_hours = db.Column(db.Float, default=0.0)
    last_maintenance_hours = db.Column(db.Float, default=0.0)
    component_wear_score = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "model": self.model,
            "total_flight_hours": self.total_flight_hours,
            "last_maintenance_hours": self.last_maintenance_hours,
            "component_wear_score": self.component_wear_score,
        }

class Crew(db.Model):
    __tablename__ = "crew"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hours_last_7_days = db.Column(db.Float, default=0.0)
    consecutive_days = db.Column(db.Integer, default=0)
    last_rest_hours = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hours_last_7_days": self.hours_last_7_days,
            "consecutive_days": self.consecutive_days,
            "last_rest_hours": self.last_rest_hours,
        }

class Flight(db.Model):
    __tablename__ = "flights"
    id = db.Column(db.Integer, primary_key=True)
    aircraft_id = db.Column(db.Integer, db.ForeignKey("aircraft.id"), nullable=False)
    crew_id = db.Column(db.Integer, db.ForeignKey("crew.id"), nullable=False)
    weather_condition = db.Column(db.String(50), nullable=False)
    risk_score = db.Column(db.Float, default=0.0)
    decision = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "aircraft_id": self.aircraft_id,
            "crew_id": self.crew_id,
            "weather_condition": self.weather_condition,
            "risk_score": self.risk_score,
            "decision": self.decision,
            "created_at": self.created_at.isoformat(),
        }

# ── Aircraft Routes ──────────────────────────────────────

@app.route("/api/aircraft/", methods=["GET"])
def list_aircraft():
    return jsonify([a.to_dict() for a in Aircraft.query.all()])

@app.route("/api/aircraft/", methods=["POST"])
def add_aircraft():
    data = request.get_json()
    if not data or not data.get("model"):
        return jsonify({"error": "model is required"}), 400

    a = Aircraft(
        model=data["model"],
        total_flight_hours=data.get("total_flight_hours", 0.0),
        last_maintenance_hours=data.get("last_maintenance_hours", 0.0),
        component_wear_score=data.get("component_wear_score", 0.0),
    )
    db.session.add(a)
    db.session.commit()
    return jsonify(a.to_dict()), 201

# ── Crew Routes ──────────────────────────────────────────

@app.route("/api/crew/", methods=["GET"])
def list_crew():
    return jsonify([c.to_dict() for c in Crew.query.all()])

@app.route("/api/crew/", methods=["POST"])
def add_crew():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    c = Crew(
        name=data["name"],
        hours_last_7_days=data.get("hours_last_7_days", 0.0),
        consecutive_days=data.get("consecutive_days", 0),
        last_rest_hours=data.get("last_rest_hours", 0.0),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

# ── Flight Routes ────────────────────────────────────────

@app.route("/api/flights/", methods=["GET"])
def list_flights():
    return jsonify([f.to_dict() for f in Flight.query.all()])

@app.route("/api/flights/", methods=["POST"])
def log_flight():
    data = request.get_json()

    for field in ["aircraft_id", "crew_id", "weather_condition"]:
        if not data or field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    Aircraft.query.get_or_404(data["aircraft_id"])
    Crew.query.get_or_404(data["crew_id"])

    f = Flight(
        aircraft_id=data["aircraft_id"],
        crew_id=data["crew_id"],
        weather_condition=data["weather_condition"],
        risk_score=data.get("risk_score", 0.0),
        decision=data.get("decision", "pending"),
    )
    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict()), 201

# ── Run App ──────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database tables created.")
    app.run(debug=True, port=5000)