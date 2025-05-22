import mysql.connector
import os

def connect_database():
    mydb = mysql.connector.connect(
        host=os.getenv('DBHOST'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWORD'),
        database=os.getenv('DBDATABASE')
    )
    return mydb

from datetime import datetime

def register_new_event(params):
    mydb = None
    try:
        mydb = connect_database()
        with mydb.cursor() as cursor:
            tachograph_id = params.get("tachograph_id")
            warning = params.get("warning")

            position = params.get("position", {})
            latitude = position.get("Latitude") or position.get("latitude")
            longitude = position.get("Longitude") or position.get("longitude")

            timestamp_raw = params.get("Timestamp") or params.get("timestamp")

            # 🔄 Conversión robusta del timestamp
            if isinstance(timestamp_raw, (int, float)):
                timestamp = datetime.fromtimestamp(float(timestamp_raw) / 1000.0)
            elif isinstance(timestamp_raw, str):
                try:
                    timestamp = datetime.strptime(timestamp_raw, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    timestamp = datetime.fromtimestamp(float(timestamp_raw) / 1000.0)
            else:
                raise ValueError("Formato de timestamp no reconocido")

            print("📥 Registrando evento:", {
                "tachograph_id": tachograph_id,
                "latitude": latitude,
                "longitude": longitude,
                "warning": warning,
                "timestamp": timestamp
            })

            sql = """
                INSERT INTO events (tachograph_id, latitude, longitude, warning, time_stamp)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (tachograph_id, latitude, longitude, warning, timestamp)
            cursor.execute(sql, values)
            mydb.commit()
            return True

    except Exception as e:
        print("❌ Error registering event:", e)
        return False
    finally:
        if mydb:
            mydb.close()


def query_events(params):
    mydb = None
    try:
        mydb = connect_database()
        with mydb.cursor(dictionary=True) as cursor:
            sql = """
                SELECT * FROM events
                WHERE tachograph_id = %s
                AND time_stamp BETWEEN %s AND %s
                ORDER BY time_stamp ASC
            """
            values = (
                params["Tachograph_id"],
                params["init_interval"],
                params["end_interval"]
            )
            cursor.execute(sql, values)
            result = cursor.fetchall()
            return result
    except Exception as e:
        print(f"Error querying events: {e}")
        return None
    finally:
        if mydb:
            mydb.close()
