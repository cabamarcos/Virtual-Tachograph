import paho.mqtt.client as mqtt
import os
import json
import datetime
import threading
import requests
from flask import Flask, request
from flask_cors import CORS

connected_tachographs = []
telemetries = []
events = []
mqtt_client = None

# Flask app
app = Flask(__name__)
CORS(app)

# Variables de entorno
SESSIONS_MICROSERVICE_ADDRESS = os.getenv("SESSIONS_MICROSERVICE_ADDRESS")
SESSIONS_MICROSERVICE_PORT = os.getenv("SESSIONS_MICROSERVICE_PORT")
TELEMETRY_MICROSERVICE_ADDRESS = os.getenv("TELEMETRY_MICROSERVICE_ADDRESS")
TELEMETRY_MICROSERVICE_PORT = os.getenv("TELEMETRY_MICROSERVICE_PORT")
EVENTS_MICROSERVICE_ADDRESS = os.getenv("EVENTS_MICROSERVICE_ADDRESS")
EVENTS_MICROSERVICE_PORT = os.getenv("EVENTS_MICROSERVICE_PORT")

# Funciones

def find_authorised_tachograph(tachograph_id):
    return tachograph_id.startswith("tachograph_control_unit-")

def is_connected(tachograph_id):
    for i, t in enumerate(connected_tachographs):
        if t["Tachograph_id"] == tachograph_id:
            return True, i
    return False, -1

def register_tachograph_connection(tachograph_id, hostname):
    session_id = ""

    # Primero registrar el tacógrafo en devices_microservice
    devices_host = os.getenv("DEVICES_MICROSERVICE_ADDRESS")
    devices_port = os.getenv("DEVICES_MICROSERVICE_PORT")
    devices_url = f"http://{devices_host}:{devices_port}/tachographs/"
    devices_data = {
        "tachograph_id": tachograph_id
    }
    try:
        r = requests.post(devices_url, json=devices_data)
        if r.status_code == 201:
            print("{} - ✅ Tacógrafo registrado en devices_microservice".format(datetime.datetime.now()))
        else:
            print("{} - ❌ Error registrando tacógrafo en devices_microservice: {}".format(datetime.datetime.now(), r.text))
            return ""  # ⛔ No continuar si falla
    except Exception as e:
        print("Error calling devices_microservice (POST):", e)
        return ""

    # Después registrar sesión en sessions_microservice
    data = {
        "tachograph_id": tachograph_id,
        "tachograph_hostname": hostname
    }
    print("{} - Solicitando creación de sesión para: {}".format(datetime.datetime.now(), json.dumps(data)))

    sessions_host = os.getenv("SESSIONS_MICROSERVICE_ADDRESS")
    sessions_port = os.getenv("SESSIONS_MICROSERVICE_PORT")
    try:
        r = requests.put(f"http://{sessions_host}:{sessions_port}/sessions/", json=data)
        if r.status_code == 201:
            print("{} - ✅ Tacógrafo conectado y sesión creada".format(datetime.datetime.now()))
            complete_result = r.json()
            session_id = complete_result["session_id"]
        else:
            print("{} - ❌ Error conectando tacógrafo en sessions_microservice".format(datetime.datetime.now()))
    except Exception as e:
        print("Error calling sessions_microservice (PUT):", e)

    return session_id



def register_tachograph_disconnection(tachograph_id, hostname):
    url = f"http://{SESSIONS_MICROSERVICE_ADDRESS}:{SESSIONS_MICROSERVICE_PORT}/sessions/"
    body = {
        "tachograph_id": tachograph_id,
        "tachograph_hostname": hostname
    }
    try:
        response = requests.post(url, json=body)
        print("Session disconnection response:", response.text)
    except Exception as e:
        print("Error calling sessions_microservice (POST):", e)


def store_telemetry(data):
    url = f"http://{TELEMETRY_MICROSERVICE_ADDRESS}:{TELEMETRY_MICROSERVICE_PORT}/telemetry/"
    try:
        response = requests.post(url, json=data)
        print("Telemetry stored response:", response.text)
    except Exception as e:
        print("Error storing telemetry:", e)

def store_event(data):
    url = f"http://{EVENTS_MICROSERVICE_ADDRESS}:{EVENTS_MICROSERVICE_PORT}/event/"
    try:
        response = requests.post(url, json=data)
        print("Event stored response:", response.text)
    except Exception as e:
        print("Error storing event:", e)

# MQTT callbacks

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    if rc == 0:
        INIT_TOPIC = "/fic/tachographs/+/request_access/"
        client.subscribe(INIT_TOPIC)
        print("Subscribed to", INIT_TOPIC)

def on_message(client, userdata, msg):
    topic = msg.topic.split("/")
    print("Message received:", msg.topic, msg.payload.decode())

    if "request_access" in msg.topic:
        try:
            received_request_access = json.loads(msg.payload.decode())
            tachograph_id = received_request_access["Tachograph_id"]
            hostname = topic[3]

            if find_authorised_tachograph(tachograph_id):
                found, _ = is_connected(tachograph_id)
                if not found:
                    connected_tachographs.append({
                        "Tachograph_id": tachograph_id,
                        "Hostname": hostname
                    })
                    register_tachograph_connection(tachograph_id, hostname)
                    response = {
                        "Tachograph_id": tachograph_id,
                        "Authorization": "True",
                        "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                    }
                    client.publish(f"/fic/tachographs/{hostname}/config/", json.dumps(response), qos=1, retain=False)
                    print(f"Authorized {tachograph_id}")

                    for t in ["telemetry", "events", "session"]:
                        topic_sub = f"/fic/tachographs/{hostname}/{t}/"
                        client.subscribe(topic_sub)
                        print(f"Subscribed to {topic_sub}")
                else:
                    response = {
                        "Tachograph_id": tachograph_id,
                        "Authorization": "False",
                        "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                    }
                    client.publish(f"/fic/tachographs/{hostname}/config/", json.dumps(response), qos=1, retain=False)
                    print(f"{tachograph_id} already connected. Rejected.")
            else:
                response = {
                    "Tachograph_id": tachograph_id,
                    "Authorization": "False",
                    "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                }
                client.publish(f"/fic/tachographs/{hostname}/config/", json.dumps(response), qos=1, retain=False)
                print(f"{tachograph_id} is not preauthorized. Rejected.")
        except Exception as e:
            print("Error processing access request:", e)

    elif topic[-2] == "telemetry":
        telemetry = json.loads(msg.payload.decode())
        hostname = topic[3]

        tachograph_id = None
        for t in connected_tachographs:
            if t["Hostname"] == hostname:
                tachograph_id = t["Tachograph_id"]
                break

        if tachograph_id:
            telemetry["Tachograph_id"] = tachograph_id
        else:
            print(f"WARNING: Tachograph_id not found for hostname {hostname}")

        telemetries.append(telemetry)

        store_telemetry(telemetry)  

    elif topic[-2] == "events":
        event = json.loads(msg.payload.decode())
        store_event(event)

    elif topic[-2] == "session":
        session_info = json.loads(msg.payload.decode())
        hostname = topic[3]
        tachograph_id = session_info.get("Tachograph_id", "unknown")
        register_tachograph_disconnection(tachograph_id, hostname) 
        connected_tachographs[:] = [t for t in connected_tachographs if t["Tachograph_id"] != tachograph_id]


# Función de configuración manual por API

@app.route('/tachographs/params/', methods=['POST'])
def update_tachograph_params():
    params = request.get_json()
    try:
        route = {
            "Origin": params["Origin"],
            "Destination": params["Destination"]
        }
        plate = params["Plate"]
        topic = f"/fic/vehicles/{plate}/routes"

        mqtt_client.publish(topic, json.dumps(route), qos=1, retain=False)
        return {"Result": "Route successfully sent"}, 201
    except Exception as e:
        print("Error sending route:", e)
        return {"Result": "Internal Server Error"}, 500

# Lanzar Flask API

def start_flask_api():
    HOST = os.getenv("HOST")
    PORT = int(os.getenv("PORT"))
    app.run(host=HOST, port=PORT, debug=True, use_reloader=False)

# Main

def main():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set("fic_server", "fic_password")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))

    mqtt_client.connect(MQTT_SERVER, MQTT_PORT, 60)

    threading.Thread(target=start_flask_api, daemon=True).start()

    mqtt_client.loop_forever()

if __name__ == "__main__":
    main()
