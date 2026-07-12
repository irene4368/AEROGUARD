def calculate_maintenance_risk(aircraft):

    hours_since_maintenance = aircraft.total_flight_hours - aircraft.last_maintenance_hours

    risk = 0

    if hours_since_maintenance > 500:
        risk += 30
    elif hours_since_maintenance > 300:
        risk += 20
    else:
        risk += 10

    risk += aircraft.component_wear_score * 0.3

    return risk


def calculate_fatigue_score(crew):

    risk = 0

    if crew.hours_last_7_days > 60:
        risk += 30
    elif crew.hours_last_7_days > 40:
        risk += 20

    if crew.consecutive_days > 7:
        risk += 20

    if crew.last_rest_hours < 6:
        risk += 20

    return risk


def calculate_weather_impact(weather):

    weather_risk = {
        "clear": 5,
        "rain": 15,
        "crosswind": 20,
        "storm": 30
    }

    return weather_risk.get(weather, 10)


def calculate_final_decision(maintenance, fatigue, weather):

    total = maintenance + fatigue + weather

    if total > 80:
        decision = "GROUND FLIGHT"
    elif total > 50:
        decision = "DELAY"
    else:
        decision = "SAFE"

    return total, decision