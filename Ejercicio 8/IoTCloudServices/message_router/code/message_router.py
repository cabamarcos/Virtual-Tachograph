import paho.mqtt.client as mqtt
import os
import json
import datetime
import re

connected_tachographs = []  # Lista de tachographs actualmente conectados

telemetries = []
events = []


def find_authorised_tachograph(tachograph_id):
    if re.fullmatch(r"tachograph_control_unit-[0-9]", tachograph_id):
        return True
    return False

def is_connected(tachograph_id):
    for i, t in enumerate(connected_tachographs):
        if t["Tachograph_id"] == tachograph_id:
            return True, i
    return False, -1

def register_tachograph_connection(tachograph_id, hostname):
    connected_tachographs.append({
        "Tachograph_id": tachograph_id,
        "Hostname": hostname
    })


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
                    # Aceptar conexión
                    register_tachograph_connection(tachograph_id, hostname)
                    response = {
                        "Tachograph_id": tachograph_id,
                        "Authorization": "True",
                        "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                    }
                    client.publish(f"/fic/tachographs/{hostname}/config/", json.dumps(response), qos=1, retain=False)
                    print(f"Authorized {tachograph_id}")

                    # Suscribirse a telemetry, events y session
                    for t in ["telemetry", "events", "session"]:
                        topic_sub = f"/fic/tachographs/{hostname}/{t}/"
                        client.subscribe(topic_sub)
                        print(f"Subscribed to {topic_sub}")

                else:
                    # Ya está conectado → rechazo
                    response = {
                        "Tachograph_id": tachograph_id,
                        "Authorization": "False",
                        "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                    }
                    client.publish(f"/fic/tachographs/{hostname}/config/", json.dumps(response), qos=1, retain=False)
                    print(f"{tachograph_id} already connected. Rejected.")
            else:
                # No autorizado → rechazo
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
        telemetries.append(telemetry)
        print(f"Telemetry received from {topic[3]}:", telemetry)

    elif topic[-2] == "events":
        event = json.loads(msg.payload.decode())
        events.append(event)
        print(f"Event received from {topic[3]}:", event)

    elif topic[-2] == "session":
        session_info = json.loads(msg.payload.decode())
        hostname = topic[3]
        timestamp = int(datetime.datetime.now().timestamp())
        tachograph_id = session_info.get("Tachograph_id", "unknown")

        # Eliminar del array de conectados
        connected_tachographs[:] = [t for t in connected_tachographs if t["Tachograph_id"] != tachograph_id]

        # Guardar en archivo
        filename = f"disconnect_{tachograph_id}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(session_info, f, indent=2)
        print(f"Session closed for {tachograph_id}, saved in {filename}")

def main():
    client = mqtt.Client()
    client.username_pw_set("fic_server", "fic_password")
    client.on_connect = on_connect
    client.on_message = on_message

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))

    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()
