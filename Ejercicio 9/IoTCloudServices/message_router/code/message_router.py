import paho.mqtt.client as mqtt
import os
import json
import datetime
import threading
import time
import random
import re

connected_tachographs = []  # Lista de tachographs actualmente conectados

telemetries = []
events = []
mqtt_client = None  # se inicializa en main()


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

def send_configuration_commands():
    print("Starting configuration command sender...")
    while True:
        try:
            if connected_tachographs:
                for tacho in connected_tachographs:
                    hostname = tacho["Hostname"]
                    tachograph_id = tacho["Tachograph_id"]

                    # Valores de configuración aleatorios
                    telemetry_freq = round(random.uniform(5, 60), 2)
                    sampling_freq = round(random.uniform(0, 2), 2)

                    timestamp = datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                    topic = f"/fic/tachographs/{hostname}/config/"

                    # Enviar frecuencia de telemetría
                    msg_telemetry = {
                        "Tachograph_id": tachograph_id,
                        "Config_item": "telemetry_freq",
                        "Config_Value": telemetry_freq,
                        "Timestamp": timestamp
                    }
                    print(f"Sending telemetry config to {tachograph_id}: {msg_telemetry}")
                    mqtt_client.publish(topic, payload=json.dumps(msg_telemetry), qos=1, retain=False)

                    # Enviar frecuencia de muestreo
                    msg_sampling = {
                        "Tachograph_id": tachograph_id,
                        "Config_item": "sampling_freq",
                        "Config_Value": sampling_freq,
                        "Timestamp": timestamp
                    }
                    print(f"Sending sampling config to {tachograph_id}: {msg_sampling}")
                    mqtt_client.publish(topic, payload=json.dumps(msg_sampling), qos=1, retain=False)

                    print(f"Sent config to {tachograph_id} - telemetry_freq: {telemetry_freq}, sampling_freq: {sampling_freq}")

            sleep_time = random.randint(10, 240)
            print(f"Waiting {sleep_time}s before sending next config update...")
            time.sleep(sleep_time)

        except Exception as e:
            print("Error sending configuration commands:", e)

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

        connected_tachographs[:] = [t for t in connected_tachographs if t["Tachograph_id"] != tachograph_id]

        filename = f"disconnect_{tachograph_id}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(session_info, f, indent=2)
        print(f"Session closed for {tachograph_id}, saved in {filename}")

def main():
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set("fic_server", "fic_password")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))

    mqtt_client.connect(MQTT_SERVER, MQTT_PORT, 60)

    # Lanzar hilo de envío de comandos
    print("entrando a send_configuration_commands")
    config_thread = threading.Thread(target=send_configuration_commands, daemon=True)
    config_thread.start()

    mqtt_client.loop_forever()

if __name__ == "__main__":
    main()
