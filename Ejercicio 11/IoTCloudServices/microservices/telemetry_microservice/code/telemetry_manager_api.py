from flask import Flask, request
from flask_cors import CORS
import os
from telemetry_db_manager import *

app = Flask(__name__)
CORS(app)

@app.route('/telemetry/', methods=['POST'])
def create_telemetry():
    params = request.get_json()
    print("Received telemetry data:", params)
    success = register_new_telemetry(params)
    if success:
        print("Telemetry registered successfully")
        return {"result": "Telemetry registered"}, 201
    else:
        print("Error registering telemetries")
        return {"result": "Error registering telemetries"}, 500

@app.route('/telemetry/', methods=['GET'])
def get_telemetry():
    params = request.args()
    print("📩 Telemetry GET recibido con params:", params.to_dict())
    telemetry_list = query_telemetry(params)
    if telemetry_list is not None:
        print("Telemetry retrieved successfully")
        return telemetry_list, 201
    else:
        print("Error querying telemetries")
        return {"result": "Error querying telemetries"}, 500

@app.route('/telemetry/positions/', methods=['GET'])
def get_last_positions():
    error_message, result = retrieve_vehicles_last_position()
    if error_message == "":
        print("Last positions retrieved successfully")
        return result, 201
    else:
        print("Error retrieving last positions")
        return {"Error Message": error_message}, 500

if __name__ == "__main__":
    HOST = os.getenv('HOST')
    PORT = int(os.getenv('PORT'))
    app.run(host=HOST, port=PORT)
