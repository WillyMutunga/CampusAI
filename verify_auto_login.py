import requests
import mysql.connector
import time

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_USER = {
    "student_id": "auto_login_test_user",
    "full_name": "Auto Login Tester",
    "email": "autologin@example.com",
    "password": "password123"
}

def cleanup_db():
    print("Cleaning up previous test data...")
    try:
        conn = mysql.connector.connect(
            host="localhost", user="root", password="", database="CampusAI"
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = %s", (TEST_USER["student_id"],))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Also clean up loginapp users
        conn2 = mysql.connector.connect(
            host="localhost", user="root", password="", database="loginapp"
        )
        cursor2 = conn2.cursor()
        cursor2.execute("DELETE FROM users WHERE student_id = %s", (TEST_USER["student_id"],))
        conn2.commit()
        cursor2.close()
        conn2.close()
        print("Cleanup complete.")
    except Exception as e:
        print(f"Cleanup failed (might be first run): {e}")

def verify_auto_login():
    cleanup_db()
    
    session = requests.Session()
    register_url = f"{BASE_URL}/register"
    
    print(f"Attempting registration for {TEST_USER['student_id']}...")
    try:
        # Perform Registration
        response = session.post(register_url, data=TEST_USER, allow_redirects=True)
        
        print(f"Registration Response Code: {response.status_code}")
        
        # Check if we are redirected to Chat or Dashboard
        # The app should now redirect to 'chat'
        if response.status_code == 200:
            if "CampusAI Assistant" in response.text or "Welcome" in response.text: # Adjust based on chat.html content
                 print("SUCCESS: Registration redirected to a page that looks like Chat/Home.")
            else:
                 print("WARNING: Registration returned 200 but content is unclear.")
                 print("Page snippet:", response.text[:200])
                 
            # Verify Authentication by accessing a protected route
            print("Verifying authentication by accessing /dashboard...")
            dash_response = session.get(f"{BASE_URL}/dashboard")
            
            first_name = TEST_USER["full_name"].split(" ")[0]
            if dash_response.status_code == 200 and (first_name in dash_response.text or "Welcome Back" in dash_response.text):
                print(f"SUCCESS: /dashboard accessible and shows '{first_name}'. Auto-login worked!")
                return True
            elif dash_response.status_code == 302:
                print("FAILURE: /dashboard redirected (probably to login). Auto-login failed.")
                return False
            else:
                print(f"FAILURE: /dashboard returned {dash_response.status_code}")
                return False
                
        else:
            print(f"FAILURE: Registration request failed with {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("CRITICAL: Connection Refused. Is the server running?")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    verify_auto_login()
