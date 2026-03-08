import sys
import os

def check_db():
    print("Checking MySQL Connection...", flush=True)
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="CampusAI"
        )
        if conn.is_connected():
            print("MySQL: SUCCESS", flush=True)
            conn.close()
            return True
    except Exception as e:
        print(f"MySQL FAILED: {e}", flush=True)
        return False

def check_model():
    print("Checking Chatbot Model Loading...", flush=True)
    try:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Suppress TF logging
        import tensorflow as tf
        from tensorflow.keras.models import load_model
        if not os.path.exists("campus_ai_model.h5"):
             print("Model FAILED: File not found.", flush=True)
             return False
        model = load_model("campus_ai_model.h5")
        print("Model: SUCCESS", flush=True)
        return True
    except Exception as e:
        print(f"Model FAILED: {e}", flush=True)
        return False

def check_portal_deps():
    print("Checking Portal Handler Dependencies...", flush=True)
    try:
        import requests
        import bs4
        print("Portal Deps: SUCCESS", flush=True)
        return True
    except ImportError as e:
        print(f"Portal Deps FAILED: Missing {e.name}", flush=True)
        return False
    except Exception as e:
        print(f"Portal Deps FAILED: {e}", flush=True)
        return False

if __name__ == "__main__":
    print("--- SYSTEM HEALTH CHECK ---", flush=True)
    db = check_db()
    model = check_model()
    portal = check_portal_deps()
    
    if db and model and portal:
        print("OVERALL STATUS: HEALTHY", flush=True)
        sys.exit(0)
    else:
        print("OVERALL STATUS: UNHEALTHY", flush=True)
        sys.exit(1)
