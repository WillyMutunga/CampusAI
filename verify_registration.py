import requests
import time

def test_registration():
    url = "http://127.0.0.1:5000/register"
    data = {
        "student_id": "test_student_01",
        "full_name": "Test Student 01",
        "email": "test01@example.com",
        "password": "password123"
    }

    try:
        # Restart the app manually or ensure it's running. Assuming existing app process handles reload or is restarted.
        # Since I modified app.py while it was running, Flask debugger should have reloaded it.
        # But to be safe, I'll just clear the previous process and start a new one if needed, 
        # but the environment context says "python app.py" is running.
        # I'll rely on Flask's auto-reload.
        
        print(f"Sending registration request to {url}...")
        response = requests.post(url, data=data, allow_redirects=False)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print("Success! Redirected to login page (or somewhere).")
            print(f"Location: {response.headers.get('Location')}")
            return True
        elif response.status_code == 200:
            if "error" in response.text.lower():
                 print("Failed: Error message found on page.")
                 print(response.text[:500]) # Print first 500 chars
                 return False
            else:
                 print("Warning: Received 200 OK. Check if this is the register page again (failure) or success page.")
                 return False
        else:
            print(f"Failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"Request failed: {e}")
        return False

import mysql.connector
def verify_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="CampusAI"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = 'test_student_01'")
        user = cursor.fetchone()
        if user:
            print(f"Database Verification: User found: {user}")
            # user[4] is password_hash in my schema (id, student_id, full_name, email, password_hash, created_at)
            # wait, schema order depends on creation.
            # let's just print it.
            return True
        else:
            print("Database Verification: User NOT found.")
            return False
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB Verification failed: {e}")
        return False

if __name__ == "__main__":
    if test_registration():
        time.sleep(1)
        verify_db()
