import socket
import json
import threading
import datetime
import os
import time
import requests
from math import acos, cos, sin, radians

positions_to_simulate = []
speeds_to_simulate = []


def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}
    while index < len(polyline_str):
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break
            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)
        lat += changes['latitude']
        lng += changes['longitude']
        coordinates.append((lat / 100000.0, lng / 100000.0))
    return coordinates


def distance(p1, p2):
    earth_radius = {"km": 6371.0087714, "mile": 3959}
    result = earth_radius["km"] * acos(
        cos(radians(p1["latitude"])) * cos(radians(p2["latitude"])) *
        cos(radians(p2["longitude"]) - radians(p1["longitude"])) +
        sin(radians(p1["latitude"])) * sin(radians(p2["latitude"]))
    )
    return result


def generate_positions_speeds(steps):
    global positions_to_simulate, speeds_to_simulate
    for step in steps:
        stepDistance = step["distanceMeters"]
        strStepTime = step["staticDuration"]
        # assumes format like "30s" but idk if it can be different
        stepTime = float(strStepTime[:-1])  
        stepSpeed = stepDistance / stepTime
        substeps = decode_polyline(step["polyline"]["encodedPolyline"])
        index = 0
        p_inicial = 0.0
        while index < len(substeps) - 1:
            if p_inicial == 0.0:
                p_inicial = {"latitude": substeps[index][0], "longitude": substeps[index][1]}
            p2 = {"latitude": substeps[index + 1][0], "longitude": substeps[index + 1][1]}
            points_distance = distance(p_inicial, p2) * 1000
            if points_distance > 1:
                subStepDuration = points_distance / stepSpeed
                subStepSpeed = stepSpeed * 3.6
                new_position = {"Origin": p_inicial, "Destination": p2, "Speed": subStepSpeed, "Time": subStepDuration}
                new_speed = {"Speed": subStepSpeed, "Time": subStepDuration}
                positions_to_simulate.append(new_position)
                speeds_to_simulate.append(new_speed)
            p_inicial = 0.0
            index += 1


def generate_route_simulations(origin_address="Leganés", destination_address="Getafe"):
    print("Asignando una ruta al vehículo")
    my_body = {
        "origin": {"address": origin_address},
        "destination": {"address": destination_address},
        "travelMode": "DRIVE",
        "languageCode": "es-ES",
        "units": "METRIC"
    }
    my_headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': os.getenv("GOOGLE_MAPS_API_KEY"),
        'X-Goog-FieldMask': 'routes.duration,routes.legs'
    }
    api_url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    response = requests.post(api_url, json=my_body, headers=my_headers)
    steps = response.json()["routes"][0]["legs"][0]["steps"]
    generate_positions_speeds(steps)
    return positions_to_simulate, speeds_to_simulate


def send_positions_to_gps_simulator(positions):
    GPS_SIMULATOR_HOST = os.getenv("GPS_SIMULATOR_HOST")
    GPS_SIMULATOR_PORT = int(os.getenv("GPS_SIMULATOR_PORT"))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        time.sleep(5)
        s.connect((GPS_SIMULATOR_HOST, GPS_SIMULATOR_PORT))
        for position in positions:
            s.sendall(bytes(json.dumps(position), "utf-8"))
            data = s.recv(1024)
            print(f"{datetime.datetime.now()} - He enviado el mensaje: {json.dumps(position)}")

def send_speeds_to_odometer_simulator(speeds):
    SPEED_SIMULATOR_HOST = os.getenv("SPEED_SIMULATOR_HOST")
    SPEED_SIMULATOR_PORT = int(os.getenv("SPEED_SIMULATOR_PORT"))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        time.sleep(5)
        s.connect((SPEED_SIMULATOR_HOST, SPEED_SIMULATOR_PORT))
        for speed in speeds:
            s.sendall(bytes(json.dumps(speed), "utf-8"))
            data = s.recv(1024)
            print(f"{datetime.datetime.now()} - He enviado el mensaje: {json.dumps(speed)}")


if __name__ == '__main__':
    try:
        my_route = {"Origin": "Ayuntamiento de Leganés", "Destination": "Ayuntamiento de Getafe"}
        positions, speeds = generate_route_simulations(my_route["Origin"], my_route["Destination"])
        t2 = threading.Thread(target=send_positions_to_gps_simulator, args=(positions,), daemon=True)
        t3 = threading.Thread(target=send_speeds_to_odometer_simulator, args=(speeds,), daemon=True)
        t2.start()
        t3.start()
        t2.join()
        t3.join()
    except Exception as e:
        print(e)
