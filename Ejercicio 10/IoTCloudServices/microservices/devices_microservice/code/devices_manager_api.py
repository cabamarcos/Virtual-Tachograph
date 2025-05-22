from flask import Flask, request
from flask_cors import CORS
import os
from devices_db_manager import register_new_tachograph, get_active_tachographs, retrieve_tachograph, save_tachograph_config
import requests

app = Flask(__name__)
CORS(app)

@app.route('/tachographs/', methods=['POST'])
def post_tachograph():
    params = request.get_json()
    print(f"Received request to register tachograph: {params}")
    if register_new_tachograph(params):
        print("Tachograph registered successfully")
        return {"tachograph_id": params["tachograph_id"]}, 201
    else:
        print(f"Failed to register tachograph {params.get('tachograph_id')}")
        return {"result": "error inserting a new tachograph"}, 500


@app.route('/tachographs/', methods=['GET'])
def get_tachographs():
    active_tachographs = get_active_tachographs()
    print("Active tachographs retrieved successfully")
    return active_tachographs, 200

@app.route('/tachographs/params/', methods=['GET'])
def get_tachograph_params():
    params = request.get_json()
    result = retrieve_tachograph(params)
    if result:
        print("Tachograph params retrieved successfully")
        return result, 200
    else:
        print("Error retrieving tachograph params")
        return {"result": "Error: Tachograph not found"}, 500

@app.route('/tachographs/params/', methods=['POST'])
def update_tachograph_params():
    params = request.get_json()

    hostname, configuration = save_tachograph_config(params)

    if configuration != {}:
        host = os.getenv('MESSAGE_ROUTER_ADDRESS')
        port = os.getenv('MESSAGE_ROUTER_PORT')

        try:
            r = requests.post(f'http://{host}:{port}/tachographs/params/', json=configuration)
            if r.status_code == 201:
                print("Tachograph params updated successfully")
                return {"result": "Success: Tachograph params updated"}, 201
            else:
                print("Error updating tachograph params")
                return {"result": "Error: Tachograph params not updated"}, 500
        except Exception as e:
            print("Error calling Message Router:", e)
            return {"result": "Error: Tachograph params not updated"}, 500
    else:
        print("Error updating tachograph params")
        return {"result": "Error: Tachograph params not updated"}, 500


if __name__ == '__main__':
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(host=HOST, port=int(PORT), debug=True, use_reloader=False)