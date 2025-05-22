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
lock = threading.Lock()

def get_host_name():
    return socket.gethostname()

def receive_speed_inputs():
    global speed_inputs, frequency
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
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    data = data.decode("utf-8")
                    print(f"{datetime.datetime.now()} - He recibido el mensaje: {data}")
                    msg = json.loads(data)

                    # Si es configuración, actualizar frecuencia
                    if msg.get("Type") == "Config" and msg.get("Parameter") == "sampling_freq":
                        with lock:
                            frequency = float(msg.get("Value"))
                        print(f"[CONFIG] Nueva frecuencia de muestreo: {frequency}s")
                    # Si es velocidad, guardar en lista con el formato correcto
                    elif "Speed" in msg and "Time" in msg:
                        speed_msg = {
                            "Type": "SpeedProfile",
                            "Speed": msg["Speed"],
                            "Time": msg["Time"]
                        }
                        speed_inputs.append(speed_msg)
                        print(f"[SPEED] Añadido nuevo perfil de velocidad: {speed_msg}")

                    conn.sendall(bytes("ok-" + str(time.time()), "utf-8"))
                except Exception as e:
                    print(f"Error procesando mensaje: {e}")
                    conn.sendall(bytes("error-" + str(e), "utf-8"))

def simulate_current_speed():
    global frequency
    time.sleep(5)
    UC_SIMULATOR_HOST = os.getenv("UC_SIMULATOR_HOST")
    UC_SIMULATOR_PORT = int(os.getenv("UC_SIMULATOR_PORT"))

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((UC_SIMULATOR_HOST, UC_SIMULATOR_PORT))
                print(f"Conectado a la Unidad de Control en {UC_SIMULATOR_HOST}:{UC_SIMULATOR_PORT}")

                while True:
                    if not speed_inputs:
                        print("No hay perfiles de velocidad disponibles, esperando...")
                        time.sleep(1)
                        continue

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

                            try:
                                s.sendall(bytes(json.dumps(simulated_speed), "utf-8"))
                                print(f"{datetime.datetime.now()} - Enviado a Control Unit: {simulated_speed}")

                                data = s.recv(1024)
                                print(f"{datetime.datetime.now()} - Respuesta de Control Unit: {data.decode('utf-8')}")

                                with lock:
                                    delay = frequency
                                time.sleep(delay)
                                times -= 1
                            except (socket.error, ConnectionResetError) as e:
                                print(f"Error de conexión al enviar velocidad: {e}")
                                raise  # This will break the inner while loop and reconnect
        except Exception as e:
            print(f"Error de conexión, reintentando en 5 segundos: {e}")
            time.sleep(5)

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
