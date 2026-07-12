from flask import Flask, request, jsonify,redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import render_template
from risk_engine import (
    calculate_maintenance_risk,
    calculate_fatigue_score,
    calculate_weather_impact,
    calculate_final_decision
)

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

    aircraft = Aircraft.query.get(data.get("aircraft_id"))
    crew = Crew.query.get(data.get("crew_id"))

    if not aircraft or not crew:
        return jsonify({"error": "Aircraft or Crew not found"}), 400

    maintenance_risk = calculate_maintenance_risk(aircraft)
    fatigue_risk = calculate_fatigue_score(crew)
    weather_risk = calculate_weather_impact(data.get("weather_condition"))

    alerts = []                                        # ← inside function ✓

    if maintenance_risk > 30:                          # ← inside function ✓
        alerts.append("Aircraft maintenance overdue")
    elif maintenance_risk > 15:
        alerts.append("Aircraft approaching maintenance threshold")

    if fatigue_risk > 30:
        alerts.append("Crew fatigue critical")
    elif fatigue_risk > 15:
        alerts.append("Crew fatigue moderate")

    if weather_risk > 25:
        alerts.append("Severe weather conditions")
    elif weather_risk > 10:
        alerts.append("Moderate weather impact")

    final_score, decision = calculate_final_decision(  # ← inside function ✓
        maintenance_risk,
        fatigue_risk,
        weather_risk
    )

    f = Flight(                                        # ← Flight object was missing!
        aircraft_id=data.get("aircraft_id"),
        crew_id=data.get("crew_id"),
        weather_condition=data.get("weather_condition"),
        risk_score=final_score,
        decision=decision,
    )

    db.session.add(f)
    db.session.commit()

    return jsonify({
        "maintenance_risk": maintenance_risk,
        "fatigue_risk": fatigue_risk,
        "weather_risk": weather_risk,
        "risk_score": final_score,
        "decision": decision,
        "alerts": alerts
    })

@app.route("/dashboard")
def dashboard():

    total_aircraft = Aircraft.query.count()
    total_crew = Crew.query.count()
    total_flights = Flight.query.count()

    high_risk_flights = Flight.query.filter(Flight.risk_score > 70).count()

    flights = Flight.query.order_by(Flight.id.desc()).limit(10).all()

    risk_scores = [f.risk_score for f in flights]
    flight_ids = [f.id for f in flights]

    return render_template(
        "dashboard.html",
        total_aircraft=total_aircraft,
        total_crew=total_crew,
        total_flights=total_flights,
        high_risk_flights=high_risk_flights,
        risk_scores=risk_scores,
        flight_ids=flight_ids
    )

@app.route("/reset", methods=["POST"])
def reset_data():
    Flight.query.delete()
    Crew.query.delete()
    Aircraft.query.delete()
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/data")
def view_all_data():
    aircraft = Aircraft.query.all()
    crew = Crew.query.all()
    flights = Flight.query.order_by(Flight.id.desc()).all()

    aircraft_map = {a.id: a.model for a in aircraft}
    crew_map = {c.id: c.name for c in crew}

    flight_rows = []
    for f in flights:
        flight_rows.append({
            "id": f.id,
            "aircraft_name": aircraft_map.get(f.aircraft_id, "Unknown"),
            "crew_name": crew_map.get(f.crew_id, "Unknown"),
            "weather_condition": f.weather_condition,
            "risk_score": round(f.risk_score, 2),
            "decision": f.decision,
        })

    return render_template(
        "data.html",
        aircraft=aircraft,
        crew=crew,
        flights=flight_rows
    )

@app.route("/aircraft")
def aircraft_page():
    return render_template("add_aircraft.html")


@app.route("/crew")
def crew_page():
    return render_template("add_crew.html")


@app.route("/simulate", methods=["GET","POST"])
def simulate():

    aircraft = Aircraft.query.all()
    crew = Crew.query.all()

    return render_template(
        "simulate.html",
        aircraft=aircraft,
        crew=crew
    )
@app.route("/flights")
def flights():

    flights = Flight.query.order_by(Flight.created_at.desc()).all()

    return render_template(
        "flights.html",
        flights=flights
    )

# ── Run App ──────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database tables created.")
    app.run(debug=True, port=5000)

