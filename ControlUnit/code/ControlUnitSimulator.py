import os
import socket
import threading
import datetime
import random
import time
import subprocess
import json

# Variables globales
current_state = {"Position": None, "GPSSpeed": 0.0, "Speed": 0.0, "driver_present": None, "Timestamp": 0}
logs = []
state_changed = False
last_time = 0

class Monitor:
    kill_now = False

monitor = Monitor()
def client_listener(connection, address):
    print(f"{datetime.datetime.now()} - New connection {connection} {address}")
    while not monitor.kill_now:
        data = connection.recv(1024)
        if not data:
            break
        else:
            data = data.decode("utf-8")
            print(f"{datetime.datetime.now()} - He recibido el mensaje: {data}")
            process_received_message(data)
            connection.sendall(bytes("ok-" + str(time.time()), "utf-8"))
    #connection.close()

def process_received_message(data):
    global current_state, logs, state_changed
    try:
        data = json.loads(data)

        if data["Type"] == "GPS":
            current_state["Position"] = data["Position"]
            current_state["GPSSpeed"] = data["Speed"]

        elif data["Type"] == "Odometer":
            current_state["Speed"] = data["Speed"]

        elif data["Type"] == "CardReader":
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
    print("WARNING: Movement detected without a driver!")

def generate_overspeed_warning():
    print("WARNING: Speed exceeds 80 km/h!")

def generate_speed_incoherence_warning():
    print("WARNING: Speed measurement inconsistency detected!")


def get_host_name():
    bashCommandName = 'echo $HOSTNAME'
    host = subprocess \
    .check_output(['bash','-c', bashCommandName]) \
    .decode("utf-8")[0:-1]
    return host

if __name__ == '__main__':
    try:
        t1 = threading.Thread(target=data_logger, daemon=True)
        t1.start()

        HOST = get_host_name()
        PORT = int(os.getenv("PORT"))

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(3)
            while True:
                print("{} - Waiting for connection...".format(datetime.datetime.now()))
                connection, address = s.accept()
                threading.Thread(target=client_listener, args=(connection, address)).start()
        
        t1.join()
    except Exception as e:
        print(e)