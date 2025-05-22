import mysql.connector
import os
import uuid
from datetime import datetime

def connect_database():
    return mysql.connector.connect(
        host=os.getenv('DBHOST'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWORD'),
        database=os.getenv('DBDATABASE')
    )

def register_new_session(tachograph_id, hostname):
    mydb = None
    try:
        mydb = connect_database()
        with mydb.cursor() as cursor:
            # Verifica si el tachograph_id existe
            sql_check = "SELECT COUNT(*) FROM tachographs WHERE tachograph_id = %s"
            cursor.execute(sql_check, (tachograph_id,))
            exists = cursor.fetchone()[0]

            if not exists:
                # Insertar tacógrafo con valores por defecto si no existe
                sql_insert_tacho = """
                    INSERT INTO tachographs (tachograph_id, telemetry_rate, sensors_sampling_rate, status, tachograph_hostname)
                    VALUES (%s, 1, 1.0, 1, %s)
                """
                cursor.execute(sql_insert_tacho, (tachograph_id, hostname))
            else:
                # Actualizar estado y hostname si ya existe
                sql_update = """
                    UPDATE tachographs
                    SET status = 1, tachograph_hostname = %s
                    WHERE tachograph_id = %s
                """
                cursor.execute(sql_update, (hostname, tachograph_id))

            # Crear nueva sesión
            session_id = str(uuid.uuid4())
            sql_insert = """
                INSERT INTO sessions (session_id, tachograph_id, init_date, status)
                VALUES (%s, %s, %s, 1)
            """
            current_time = datetime.now()
            cursor.execute(sql_insert, (session_id, tachograph_id, current_time))

            mydb.commit()
            return session_id
    except Exception as e:
        print(f"❌ ERROR creando sesión para {tachograph_id}: {e}")
        return None
    finally:
        if mydb:
            mydb.close()



def register_session_disconnection(params):
    mydb = None
    try:
        tachograph_id = params.get("tachograph_id")
        if not tachograph_id:
            raise ValueError("Missing 'tachograph_id' in parameters")

        mydb = connect_database()
        with mydb.cursor(dictionary=True) as cursor:
            # Buscar sesión activa
            sql = """
                SELECT * FROM sessions
                WHERE tachograph_id = %s AND status = 1
                ORDER BY init_date DESC
                LIMIT 1
            """
            cursor.execute(sql, (tachograph_id,))
            session = cursor.fetchone()

            if session:
                # Cerrar la sesión activa
                sql_update = """
                    UPDATE sessions
                    SET status = 0, end_date = NOW()
                    WHERE id = %s
                """
                cursor.execute(sql_update, (session["id"],))
                mydb.commit()
                hostname = params.get("tachograph_hostname", "unknown")
                return hostname, session["session_id"]
            else:
                return params.get("tachograph_hostname", "unknown"), None

    except Exception as e:
        print("Error in register_session_disconnection:", e)
        return "unknown", None
    finally:
        if mydb:
            mydb.close()



def is_connected(params):
    mydb = None
    try:
        if params is None or "tachograph_id" not in params:
            print("Missing tachograph_id in request")
            return "", []

        tachograph_id = params["tachograph_id"]

        mydb = connect_database()
        with mydb.cursor() as cursor:
            sql_hostname = """
                SELECT tachograph_hostname FROM tachographs
                WHERE tachograph_id = %s AND status = 1
            """
            cursor.execute(sql_hostname, (tachograph_id,))
            result = cursor.fetchone()

            if not result:
                print(f"Tachograph {tachograph_id} not active")
                return "", []

            hostname = result[0]

            sql_sessions = """
                SELECT session_id FROM sessions
                WHERE tachograph_id = %s AND status = 1
            """
            cursor.execute(sql_sessions, (tachograph_id,))
            sessions = [row[0] for row in cursor.fetchall()]

            return hostname, sessions
    except Exception as e:
        print(f"Error in is_connected: {e}")
        return "", []
    finally:
        if mydb:
            mydb.close()

