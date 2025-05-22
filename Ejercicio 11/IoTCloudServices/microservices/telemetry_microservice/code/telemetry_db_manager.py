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

def register_new_telemetry(params):
    mydb = None
    try:
        mydb = connect_database()
        with mydb.cursor() as cursor:

            # Extraer valores del JSON recibido
            tachograph_id = params.get("Tachograph_id")
            gps_speed = params.get("GPSSpeed")
            speed = params.get("Speed")
            driver = params.get("driver_present")
            timestamp = params.get("Timestamp")

            # Puede que Position sea None
            position = params.get("Position")
            latitude = position.get("latitude") if position else None
            longitude = position.get("longitude") if position else None

            # Debug para ver qué llega realmente
            print("📡 Insertando telemetría:", {
                "tachograph_id": tachograph_id,
                "latitude": latitude,
                "longitude": longitude,
                "gps_speed": gps_speed,
                "current_speed": speed,
                "current_driver_id": driver,
                "time_stamp": timestamp
            })

            sql = """
                INSERT INTO telemetry (
                    tachograph_id,
                    latitude,
                    longitude,
                    gps_speed,
                    current_speed,
                    current_driver_id,
                    time_stamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                tachograph_id,
                latitude,
                longitude,
                gps_speed,
                speed,
                driver,
                timestamp
            )

            cursor.execute(sql, values)
            mydb.commit()
            return True

    except Exception as e:
        print("❌ Error registering telemetry:", e)
        return False
    finally:
        if mydb:
            mydb.close()



def query_telemetry(params):
    mydb = None
    try:
        mydb = connect_database()
        with mydb.cursor(dictionary=True) as cursor:
            sql = """
                SELECT * FROM telemetry
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
        print(f"Error querying telemetry: {e}")
        return None
    finally:
        if mydb:
            mydb.close()

def retrieve_vehicles_last_position():
    mydb = None
    try:
        mydb = connect_database()
        with mydb.cursor(dictionary=True) as cursor:
            sql = """
                SELECT t1.tachograph_id, t1.latitude, t1.longitude
                FROM telemetry t1
                INNER JOIN (
                    SELECT tachograph_id, MAX(time_stamp) AS last_time
                    FROM telemetry
                    GROUP BY tachograph_id
                ) t2
                ON t1.tachograph_id = t2.tachograph_id AND t1.time_stamp = t2.last_time
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            return "", result
    except Exception as e:
        print(f"Error retrieving last positions: {e}")
        return str(e), []
    finally:
        if mydb:
            mydb.close()
