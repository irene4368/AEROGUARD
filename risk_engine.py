def calculate_maintenance_risk(aircraft):
    hours_since_maintenance = (
        aircraft.total_flight_hours - aircraft.last_maintenance_hours
    )

    risk = 0

    if hours_since_maintenance > 500:
        risk += 50

    risk += aircraft.component_wear_score * 50

    return min(risk, 100)


def calculate_fatigue_score(crew):
    risk = 0

    if crew.hours_last_7_days >= 60:
        risk += 50
    elif crew.hours_last_7_days >= 40:
        risk += 30

    if crew.last_rest_hours < 10:
        risk += 20

    return min(risk, 100)


def calculate_weather_impact(weather):
    weather = weather.lower()

    if weather == "clear":
        return 0
    elif weather == "rain":
        return 10
    elif weather == "storm":
        return 25
    elif weather == "crosswind":
        return 30
    else:
        return 5


def calculate_final_decision(maintenance_risk, fatigue_risk, weather_risk):
    final_score = (
        maintenance_risk * 0.4
        + fatigue_risk * 0.3
        + weather_risk * 0.3
    )

    if final_score < 40:
        decision = "Cleared"
    elif 40 <= final_score <= 70:
        decision = "Delay"
    else:
        decision = "Grounded"

    return round(final_score, 2), decision