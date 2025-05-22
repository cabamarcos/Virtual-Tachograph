from flask import Flask, request
from flask_cors import CORS
import os
from sessions_db_manager import register_new_session, register_session_disconnection, is_connected

app = Flask(__name__)
CORS(app)

@app.route('/sessions/', methods=['PUT'])
def create_session():
    params = request.get_json()
    result = register_new_session(params["tachograph_id"], params["tachograph_hostname"])

    if result:
        print("Session created successfully")
        return {"session_id": result}, 201
    else:
        print("Error creating a new session")
        return {"session_id": "", "Error": "Access not granted"}, 500

@app.route('/sessions/', methods=['POST'])
def close_session():
    params = request.get_json()
    hostname, sessions = register_session_disconnection(params)
    if hostname:
        print("Session closed successfully")
        return {"tachograph_hostname": hostname, "sessions": sessions}, 201
    else:
        print("Error closing a session")
        return {"tachograph_hostname": "", "sessions": []}, 500

@app.route('/sessions/', methods=['GET'])
def check_session():
    params = request.get_json()
    hostname, sessions = is_connected(params)
    if hostname:
        print("Session checked successfully")
        return {"tachograph_hostname": hostname, "sessions": sessions}, 201
    else:
        print("Error checking a session")
        return {"tachograph_hostname": "", "sessions": []}, 500

if __name__ == '__main__':
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    app.run(host=HOST, port=int(PORT))
