import socket
import os
import json
import datetime
import time
import random
import math

def simulate_current_driver():
    is_driver = 0
    driver_present = 0
    UC_SIMULATOR_HOST = os.getenv("UC_SIMULATOR_HOST") #session01_Positioning_System_Simulator
    UC_SIMULATOR_PORT = int(os.getenv("UC_SIMULATOR_PORT"))
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        time.sleep(5)
        s.connect((UC_SIMULATOR_HOST, UC_SIMULATOR_PORT))
        print("Empieza CardReader")
        while True:
            is_driver = math.trunc(random.uniform(0.5, 1.5))
            if is_driver == 1:
                driver_present = math.trunc(random.uniform(1.5, 3.5))
                simulated_driver = {
                    "Type": "CardReader",
                    "is_driver": is_driver,
                    "driver_present": f"Driver {driver_present}",
                    "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                }
            else:
                simulated_driver = {
                    "Type": "CardReader",
                    "is_driver": is_driver,
                    "driver_present": "None",
                    "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                }

            s.sendall(bytes(json.dumps(simulated_driver), "utf-8"))
            print(f"{datetime.datetime.now()} - He enviado el mensaje: {simulated_driver}")
            
            data = s.recv(1024)
            print(f"{datetime.datetime.now()} - Respuesta recibida: {data.decode('utf-8')}")
            
            frequency = random.uniform(5.0, 60.0)
            print(f"{datetime.datetime.now()} - Volveré a enviar mensaje en: {frequency:.2f} segundos")
            time.sleep(frequency)

if __name__ == '__main__':
    try:
        simulate_current_driver()
    except Exception as e:
        print(e)
