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
lock = threading.Lock()

def get_host_name():
    return socket.gethostname()

def receive_simulation_inputs():
    global simulation_inputs, frequency
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
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    data = data.decode("utf-8")
                    print(f"{datetime.datetime.now()} - He recibido el mensaje: {data}")
                    msg = json.loads(data)

                    # Procesar configuración
                    if msg.get("Type") == "Config" and msg.get("Parameter") == "sampling_freq":
                        with lock:
                            frequency = float(msg.get("Value"))
                        print(f"[CONFIG] Frecuencia de muestreo actualizada a {frequency}s")
                    # Agregar rutas con el formato correcto
                    elif "Origin" in msg and "Destination" in msg and "Speed" in msg and "Time" in msg:
                        position_msg = {
                            "Type": "RouteProfile",
                            "Origin": msg["Origin"],
                            "Destination": msg["Destination"],
                            "Speed": msg["Speed"],
                            "Time": msg["Time"]
                        }
                        simulation_inputs.append(position_msg)
                        print(f"[ROUTE] Añadido nuevo perfil de ruta: {position_msg}")

                    conn.sendall(bytes("ok-" + str(time.time()), "utf-8"))
                except Exception as e:
                    print(f"Error procesando mensaje: {e}")
                    conn.sendall(bytes("error-" + str(e), "utf-8"))

def simulate_positioning():
    global frequency
    UC_SIMULATOR_HOST = os.getenv("UC_SIMULATOR_HOST")
    UC_SIMULATOR_PORT = int(os.getenv("UC_SIMULATOR_PORT"))

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((UC_SIMULATOR_HOST, UC_SIMULATOR_PORT))
                print(f"Conectado a la Unidad de Control en {UC_SIMULATOR_HOST}:{UC_SIMULATOR_PORT}")

                while True:
                    if not simulation_inputs:
                        print("No hay perfiles de ruta disponibles, esperando...")
                        time.sleep(1)
                        continue

                    for position in simulation_inputs:
                        with lock:
                            freq = frequency
                        times = math.trunc(position["Time"] / freq) + 1

                        while times - 1 > 0:
                            try:
                                simulated_position = {
                                    "Type": "GPS",
                                    "Position": position["Origin"],
                                    "Speed": position["Speed"],
                                    "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                                }

                                s.sendall(bytes(json.dumps(simulated_position), "utf-8"))
                                print(f"{datetime.datetime.now()} - Enviado a Control Unit: {simulated_position}")
                                print(f"{datetime.datetime.now()} - Volveré a enviar mensaje en: {freq} segundos")

                                data = s.recv(1024)
                                print(f"{datetime.datetime.now()} - Respuesta de Control Unit: {data.decode('utf-8')}")

                                time.sleep(freq)
                                times -= 1
                            except (socket.error, ConnectionResetError) as e:
                                print(f"Error de conexión al enviar posición: {e}")
                                raise  # This will break the inner while loop and reconnect

                        try:
                            last_position = position["Destination"]
                            simulated_position = {
                                "Type": "GPS",
                                "Position": last_position,
                                "Speed": position["Speed"],
                                "Timestamp": datetime.datetime.timestamp(datetime.datetime.now()) * 1000
                            }

                            s.sendall(bytes(json.dumps(simulated_position), "utf-8"))
                            print(f"{datetime.datetime.now()} - Enviado a Control Unit: {simulated_position}")
                            print(f"{datetime.datetime.now()} - Volveré a enviar mensaje en: {freq} segundos")

                            data = s.recv(1024)
                            print(f"{datetime.datetime.now()} - Respuesta de Control Unit: {data.decode('utf-8')}")

                            time.sleep(freq)
                        except (socket.error, ConnectionResetError) as e:
                            print(f"Error de conexión al enviar posición final: {e}")
                            raise  # This will break the inner while loop and reconnect
        except Exception as e:
            print(f"Error de conexión, reintentando en 5 segundos: {e}")
            time.sleep(5)

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
