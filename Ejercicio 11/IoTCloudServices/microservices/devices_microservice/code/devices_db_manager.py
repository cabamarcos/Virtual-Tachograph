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

def register_new_tachograph(params):
    try:
        mydb = connect_database()
        tachograph_id = params["tachograph_id"]

        with mydb.cursor() as mycursor:
            # Verificar si ya existe
            sql = "SELECT tachograph_id FROM tachographs WHERE tachograph_id = %s"
            mycursor.execute(sql, (tachograph_id,))
            result = mycursor.fetchone()

            if result:
                print(f"Tachograph {tachograph_id} already exists.")
                return False

            # Verificar si está disponible
            sql = "SELECT logic_id FROM available_ids WHERE is_assigned = 0 AND logic_id = %s"
            mycursor.execute(sql, (tachograph_id,))
            result = mycursor.fetchone()

            if result:
                sql_insert = """
                    INSERT INTO tachographs (tachograph_id, telemetry_rate, sensors_sampling_rate, status)
                    VALUES (%s, 1, 1.0, 1)
                """
                mycursor.execute(sql_insert, (tachograph_id,))
                
                sql_update = "UPDATE available_ids SET is_assigned = 1 WHERE logic_id = %s"
                mycursor.execute(sql_update, (tachograph_id,))
                
                mydb.commit()
                print(f"Tachograph {tachograph_id} successfully registered.")
                return True
            else:
                print(f"Tachograph ID {tachograph_id} not available in available_ids.")
                return False
    except Exception as e:
        print("Exception in register_new_tachograph:", e)
        return False


def get_active_tachographs():
    plates = []
    try:
        mydb = connect_database()
        with mydb.cursor() as mycursor:
            sql = "SELECT tachograph_id FROM tachographs WHERE status = 1"
            mycursor.execute(sql)
            myresult = mycursor.fetchall()
            for (tachograph_id,) in myresult:
                plates.append({"tachograph_id": tachograph_id})
            mydb.commit()
    except Exception as e:
        print("Error in get_active_tachographs:", e)
    return plates

def retrieve_tachograph(params):
    tachographs = []
    try:
        mydb = connect_database()
        tachograph_id = params["tachograph_id"]

        with mydb.cursor() as mycursor:
            sql = """
            SELECT tachograph_id, telemetry_rate, tachograph_hostname, sensors_sampling_rate, status 
            FROM tachographs 
            WHERE tachograph_id = %s AND status = 1
            """
            mycursor.execute(sql, (tachograph_id,))
            myresult = mycursor.fetchall()
            for tachograph_id, telemetry_rate, tachograph_hostname, sensors_sampling_rate, status in myresult:
                tachographs.append({
                    "tachograph_id": tachograph_id,
                    "telemetry_rate": telemetry_rate,
                    "sensors_sampling_rate": sensors_sampling_rate,
                    "status": status
                })
            mydb.commit()
    except Exception as e:
        print("Error in retrieve_tachograph:", e)

    if tachographs:
        return tachographs[0]
    else:
        return None
    
def save_tachograph_config(params):
    tachograph_id = params["tachograph_id"]
    telemetry_rate = params["telemetry_rate"]
    sensors_sampling_rate = params["sensors_sampling_rate"]

    mydb = None
    try:
        mydb = connect_database()
        with mydb.cursor() as cursor:
            # Verificar si el tacógrafo está activo
            cursor.execute("""
                SELECT tachograph_hostname FROM tachographs
                WHERE tachograph_id = %s AND status = 1
            """, (tachograph_id,))
            result = cursor.fetchone()

            if not result:
                return "", {}

            hostname = result[0]

            # Actualizar parámetros
            cursor.execute("""
                UPDATE tachographs
                SET telemetry_rate = %s, sensors_sampling_rate = %s
                WHERE tachograph_id = %s
            """, (telemetry_rate, sensors_sampling_rate, tachograph_id))
            mydb.commit()

            config = {
                "Origin": "server",
                "Destination": hostname,
                "Plate": tachograph_id,
                "telemetry_rate": telemetry_rate,
                "sensors_sampling_rate": sensors_sampling_rate
            }

            return hostname, config

    except Exception as e:
        print("Error in save_tachograph_config:", e)
        return "", {}
    finally:
        if mydb:
            mydb.close()
