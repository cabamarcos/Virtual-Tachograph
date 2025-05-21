import threading
import socket
import os
import json
import datetime
import time
import random
import math

# Variables globales
speed_inputs = []
frequency = 1.0  # Frecuencia base en segundos

def get_host_name():
    return socket.gethostname()

def receive_speed_inputs():
    global speed_inputs
    HOST = get_host_name()
    PORT = int(os.getenv("PORT"))
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Odómetro esperando conexión en {HOST}:{PORT}")
        
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
                    speed_inputs.append(json.loads(data))
                    conn.sendall(bytes("ok-" + str(time.time()), "utf-8"))

def simulate_current_speed():
    time.sleep(5)
    UC_SIMULATOR_HOST = os.getenv("UC_SIMULATOR_HOST") #session01_Positioning_System_Simulator
    UC_SIMULATOR_PORT = int(os.getenv("UC_SIMULATOR_PORT"))
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        time.sleep(5)
        s.connect((UC_SIMULATOR_HOST, UC_SIMULATOR_PORT))
        print(f"Conectado a la Unidad de Control en {UC_SIMULATOR_HOST}:{UC_SIMULATOR_PORT}")
        
        while True:
            for speed in speed_inputs:
                times = math.trunc(speed["Time"] / frequency) + 1
                random_speed = speed["Speed"] + random.uniform(-5.0, 5.0)
                
                while times > 0:
                    if times != math.trunc(speed["Time"] / frequency):
                        random_speed += random.uniform(-5.0, 5.0)
                    
                    simulated_speed = {
                        "Type": "Odometer",
                        "Speed": random_speed,
                        "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                    }
                    
                    s.sendall(bytes(json.dumps(simulated_speed), "utf-8"))
                    print(f"{datetime.datetime.now()} - He enviado el mensaje: {simulated_speed}")
                    
                    data = s.recv(1024)
                    print(f"{datetime.datetime.now()} - Respuesta recibida: {data.decode('utf-8')}")
                    
                    time.sleep(frequency)
                    times -= 1

if __name__ == '__main__':
    try:
        t1 = threading.Thread(target=receive_speed_inputs, daemon=True)
        t2 = threading.Thread(target=simulate_current_speed, daemon=True)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
    except Exception as e:
        print(f"Error: {e}")
