import threading
import socket
import os
import json
import datetime
import time
import random
import math

# Variables globales
simulation_inputs = []
frequency = 1.0  # Frecuencia base en segundos

def get_host_name():
    return socket.gethostname()

def receive_simulation_inputs():
    global simulation_inputs
    HOST = get_host_name()
    PORT = int(os.getenv("PORT"))
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"GNSS esperando conexión en {HOST}:{PORT}")
        
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                else:
                    data = data.decode("utf-8")
                    print(f"{datetime.datetime.now()} - He recibido el mensaje: {data}")
                    simulation_inputs.append(json.loads(data))
                    conn.sendall(bytes("ok-" + str(time.time()), "utf-8"))

def simulate_positioning():
    UC_SIMULATOR_HOST = os.getenv("UC_SIMULATOR_HOST")
    UC_SIMULATOR_PORT = int(os.getenv("UC_SIMULATOR_PORT"))
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        time.sleep(5)
        s.connect((UC_SIMULATOR_HOST, UC_SIMULATOR_PORT))
        print(f"Conectado a la Unidad de Control en {UC_SIMULATOR_HOST}:{UC_SIMULATOR_PORT}")
        
        while True:
            for position in simulation_inputs:
                times = math.trunc(position["Time"] / frequency) + 1
                
                while times - 1 > 0:
                    simulated_position = {
                        "Type": "GPS",
                        "Position": position["Origin"],
                        "Speed": position["Speed"],
                        "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                    }
                    
                    s.sendall(bytes(json.dumps(simulated_position), "utf-8"))
                    print(f"{datetime.datetime.now()} - He enviado el mensaje: {simulated_position}")
                    print(f"{datetime.datetime.now()} - Volveré a enviar mensaje en: {frequency} segundos")
                    
                    data = s.recv(1024)
                    time.sleep(frequency)
                    times -= 1
                
                last_position = position["Destination"]
                simulated_position = {
                    "Type": "GPS",
                    "Position": last_position,
                    "Speed": position["Speed"],
                    "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                }
                
                s.sendall(bytes(json.dumps(simulated_position), "utf-8"))
                print(f"{datetime.datetime.now()} - He enviado el mensaje: {simulated_position}")
                print(f"{datetime.datetime.now()} - Volveré a enviar mensaje en: {frequency} segundos")
                
                data = s.recv(1024)
                time.sleep(frequency)

if __name__ == '__main__':
    try:
        t1 = threading.Thread(target=receive_simulation_inputs, daemon=True)
        t2 = threading.Thread(target=simulate_positioning, daemon=True)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
    except Exception as e:
        print(f"Error: {e}")
