from flask import Flask, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/tachographs/active/', methods=['GET'])
def get_active_tachographs():
    host = os.getenv('TELEMETRY_MICROSERVICE_ADDRESS')
    port = os.getenv('TELEMETRY_MICROSERVICE_PORT')
    try:
        result = requests.get(f'http://{host}:{port}/telemetry/positions/')
        if result.status_code == 201:
            return result.json(), 201
        else:
            return {"result": "Error: Tachographs information is not available"}, 500
    except Exception as e:
        print(f"Error contacting telemetry microservice: {e}")
        return {"result": "Error contacting telemetry microservice"}, 500


@app.route('/tachographs/telemetry/', methods=['GET'])
def get_tachograph_telemetry():
    tachograph_id = request.args.get('tachograph_id')
    params = {"tachograph_id": tachograph_id}

    host = os.getenv('TELEMETRY_MICROSERVICE_ADDRESS')
    port = os.getenv('TELEMETRY_MICROSERVICE_PORT')
    try:
        result = requests.get(f'http://{host}:{port}/telemetry/', params=params)
        return result.json(), result.status_code
    except Exception as e:
        print(f"Error contacting telemetry microservice: {e}")
        return {"result": "Error retrieving telemetry data"}, 500


@app.route('/tachographs/events/', methods=['GET'])
def get_tachograph_events():
    tachograph_id = request.args.get('tachograph_id')
    params = {"tachograph_id": tachograph_id}

    host = os.getenv('EVENTS_MICROSERVICE_ADDRESS')
    port = os.getenv('EVENTS_MICROSERVICE_PORT')
    try:
        result = requests.get(f'http://{host}:{port}/events/', params=params)

        return result.json(), result.status_code
    except Exception as e:
        print(f"Error contacting events microservice: {e}")
        return {"result": "Error retrieving events"}, 500

@app.route('/tachographs/configuration/', methods=['GET'])
def get_tachograph_configuration():
    tachograph_id = request.args.get('tachograph_id')
    params = {"tachograph_id": tachograph_id}

    host = os.getenv('DEVICES_MICROSERVICE_ADDRESS')
    port = os.getenv('DEVICES_MICROSERVICE_PORT')
    try:
        result = requests.get(f'http://{host}:{port}/tachographs/params/', params=params)
        return result.json(), result.status_code
    except Exception as e:
        print(f"Error contacting devices microservice: {e}")
        return {"result": "Error retrieving configuration"}, 500

@app.route('/tachographs/configuration/', methods=['POST'])
def update_tachograph_configuration():
    my_tachograph = request.args.get('tachograph_id')
    my_sensor_sampling = request.args.get('sampling')
    my_telemetry_rate = request.args.get('rate')

    params = {
        "tachograph_id": my_tachograph,
        "sensors_sampling_rate": my_sensor_sampling,
        "telemetry_rate": my_telemetry_rate
    }

    host = os.getenv('DEVICES_MICROSERVICE_ADDRESS')
    port = os.getenv('DEVICES_MICROSERVICE_PORT')
    try:
        r = requests.post(f'http://{host}:{port}/tachographs/params/', params=params)
        if r.status_code == 201:
            return {"result": "Success: Tachograph params updated"}, 201
        else:
            return {"result": "Error: Tachograph params not updated"}, 500
    except Exception as e:
        print(f"Error contacting devices microservice: {e}")
        return {"result": "Error contacting devices microservice"}, 500

if __name__ == '__main__':
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(host=HOST, port=int(PORT))

