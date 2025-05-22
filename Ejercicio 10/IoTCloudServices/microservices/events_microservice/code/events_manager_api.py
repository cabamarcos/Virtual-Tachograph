from flask import Flask, request
from flask_cors import CORS
import os
from events_db_manager import *

app = Flask(__name__)
CORS(app)

@app.route('/event/', methods=['POST'])
def create_event():
    params = request.get_json()
    success = register_new_event(params)
    if success:
        print("Event registered successfully")
        return {"result": "Event registered"}, 201
    else:
        print("Error registering an event")
        return {"result": "Error registering an event"}, 500

@app.route('/telemetry/', methods=['GET'])
def get_events():
    params = request.get_json()
    events = query_events(params)
    if events is not None:
        print("Events retrieved successfully")
        return events, 201
    else:
        print("Error querying events")
        return {"result": "Error querying events"}, 500

if __name__ == "__main__":
    HOST = os.getenv('HOST')
    PORT = int(os.getenv('PORT'))
    app.run(host=HOST, port=PORT)
