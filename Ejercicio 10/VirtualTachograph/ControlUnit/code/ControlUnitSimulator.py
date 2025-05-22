import os
import socket
import threading
import datetime
import random
import time
import subprocess
import json
import paho.mqtt.client as mqtt

# Variables globales
current_state = {"Position": None, "GPSSpeed": 0.0, "Speed": 0.0, "driver_present": None, "Timestamp": 0}
logs = []
state_changed = False
last_time = 0
connection_granted = False
disconnected = False
json_config_received = {}
number_telemetries_sent = 0
number_events_sent = 0
tachograph_id = "tachograph_control_unit-" + str(random.randint(1, 5))
hostname = socket.gethostname()
SESSION_TOPIC = f"/fic/tachographs/{hostname}/session/"
sampling_freq = 1.0  # Valor por defecto para Odómetro y GNSS
telemetry_freq = 5.0  # Valor por defecto para enviar telemetrías

# Lista de conexiones activas para reenviar configuraciones a sensores
sensor_connections = []

class Monitor:
    kill_now = False


monitor = Monitor()


def client_listener(connection, address):
    print(f"{datetime.datetime.now()} - New connection {connection} {address}")
    sensor_connections.append(connection)
    while not monitor.kill_now:
        try:
            data = connection.recv(1024)
            if not data:
                break
            data = data.decode("utf-8")
            process_received_message(data)
            connection.sendall(bytes("ok-" + str(time.time()), "utf-8"))
        except Exception as e:
            print("Sensor connection error:", e)
            break
    sensor_connections.remove(connection)


def process_received_message(data):
    global current_state, logs, state_changed
    try:
        data = json.loads(data)

        if data["Type"] == "GPS":
            print(f"Received GPS data: {data}")
            current_state["Position"] = data["Position"]
            current_state["GPSSpeed"] = data["Speed"]

        elif data["Type"] == "Odometer":
            print(f"Received Odometer data: {data}")
            current_state["Speed"] = data["Speed"]

        elif data["Type"] == "CardReader":
            print(f"Received CardReader data: {data}")
            current_state["driver_present"] = data["driver_present"]

        current_state["Timestamp"] = data["Timestamp"]
        logs.append(current_state.copy())

    except json.JSONDecodeError as e:
        print(f"Error procesando mensaje JSON: {e}")


def data_logger():
    global last_time, state_changed

    while not monitor.kill_now:
        if current_state["Timestamp"] > last_time:
            if current_state["driver_present"] == "None" and current_state["Speed"] > 0.0:
                state_changed = True
                generate_movement_without_driver_warning()

            if current_state["Speed"] > 80.0:
                state_changed = True
                generate_overspeed_warning()

            if abs(current_state["Speed"] - current_state["GPSSpeed"]) > 3.0:
                state_changed = True
                generate_speed_incoherence_warning()

            last_time = datetime.datetime.timestamp(datetime.datetime.now()) * 1000
        time.sleep(1)


def generate_movement_without_driver_warning():
    publish_event_warning("Movement detected without a driver")

def generate_overspeed_warning():
    publish_event_warning("Speed exceeds 80 km/h")

def generate_speed_incoherence_warning():
    publish_event_warning("Speed measurement inconsistency detected")



def mqtt_communications():
    global SESSION_TOPIC

    client = mqtt.Client()
    client.username_pw_set(username="fic_server", password="fic_password")
    client.on_connect = on_connect
    client.on_message = on_message

    # Mensaje en caso de desconexión inesperada
    connection_dict = {
        "Tachograph_id": tachograph_id,
        "Status": "Off - Unregulate Disconnection",
        "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
    }
    connection_str = json.dumps(connection_dict)
    client.will_set(SESSION_TOPIC, connection_str)
    print(f"######### Will set: {SESSION_TOPIC}, payload: {connection_str}")


    MQTT_SERVER = os.getenv("MQTT_SERVER_ADDRESS")
    MQTT_PORT = int(os.getenv("MQTT_SERVER_PORT"))
    client.connect(MQTT_SERVER, MQTT_PORT, 60)

    client.loop_start()

    while not disconnected and not monitor.kill_now:
        if connection_granted:
            publish_telemetry(client)
        else:
            print("Esperando autorización del message router...")
            time.sleep(10)

    client.loop_stop()

def send_sampling_frequency_to_sensors():
    command = json.dumps({
        "Type": "Config",
        "Parameter": "sampling_freq",
        "Value": sampling_freq
    })
    for conn in sensor_connections:
        try:
            conn.sendall(bytes(command, "utf-8"))
            print("Sent sampling_freq config to sensor.")
        except Exception as e:
            print("Failed to send config to sensor:", e)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    if rc == 0:
        REQUEST_ACCESS_TOPIC = f"/fic/tachographs/{hostname}/request_access/"
        request_access_message = {
            "Tachograph_id": tachograph_id,
            "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
        }
        client.publish(REQUEST_ACCESS_TOPIC, payload=json.dumps(request_access_message), qos=1, retain=False)
        print("Published request_access:", request_access_message)

        CONFIG_TOPIC = f"/fic/tachographs/{hostname}/config/"
        client.subscribe(CONFIG_TOPIC)
        print("Subscribed to:", CONFIG_TOPIC)
    else:
        print("Connection failed")


def on_message(client, userdata, msg):
    global connection_granted, json_config_received, telemetry_freq, sampling_freq
    print("Message received:", msg.topic, msg.payload.decode())

    if "config" in msg.topic:
        try:
            config = json.loads(msg.payload.decode("utf-8"))
            if config.get("Authorization") == "True" and config.get("Tachograph_id") == tachograph_id:
                connection_granted = True
                print("Authorization granted.")
                return

            # Procesar comandos de configuración
            if config.get("Tachograph_id") == tachograph_id:
                item = config.get("Config_item")
                value = config.get("Config_Value")
                print(f"Received config: {item} = {value}")

                if item == "telemetry_freq":
                    telemetry_freq = float(value)
                    print(f"Updated telemetry frequency: {telemetry_freq}s")


                elif item == "sampling_freq":
                    sampling_freq = float(value)
                    print(f"Updated sensor sampling frequency: {sampling_freq}s")
                    send_sampling_frequency_to_sensors()

        except json.JSONDecodeError as e:
            print("Error decoding config message:", e)
        except Exception as ex:
            print("Error handling config message:", ex)


def publish_telemetry(client):
    global number_telemetries_sent
    STATE_TOPIC = f"/fic/tachographs/{hostname}/telemetry/"
    while number_telemetries_sent < len(logs):
        client.publish(STATE_TOPIC, payload=json.dumps(logs[number_telemetries_sent]), qos=1, retain=False)
        print(f"######### Published TELEMETRY in topic: {STATE_TOPIC}, payload: {logs[number_telemetries_sent]}")
        number_telemetries_sent += 1
        time.sleep(telemetry_freq)


def publish_event_warning(warning_msg):
    EVENT_TOPIC = f"/fic/tachographs/{hostname}/events/"
    event = {
        "tachograph_id": tachograph_id,
        "position": current_state["Position"],
        "warning": warning_msg,
        "Timestamp": current_state["Timestamp"]
    }

    client = mqtt.Client()
    client.username_pw_set("fic_server", "fic_password")
    client.connect(os.getenv("MQTT_SERVER_ADDRESS"), int(os.getenv("MQTT_SERVER_PORT")))
    client.loop_start()
    client.publish(EVENT_TOPIC, payload=json.dumps(event), qos=1, retain=False)
    print(f"######### Published EVENT in topic: {EVENT_TOPIC}, payload: {event}")
    client.loop_stop()



def start_tcp_server():
    PORT = int(os.getenv("PORT"))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((hostname, PORT))
        s.listen(3)
        while True:
            print(f"{datetime.datetime.now()} - Waiting for connection...")
            connection, address = s.accept()
            threading.Thread(target=client_listener, args=(connection, address), daemon=True).start()


if __name__ == '__main__':
    try:
        t1 = threading.Thread(target=data_logger, daemon=True)
        t2 = threading.Thread(target=mqtt_communications, daemon=True)
        t3 = threading.Thread(target=start_tcp_server, daemon=True)

        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()

    except Exception as e:
        print(e)
