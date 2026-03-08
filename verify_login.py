import requests

def verify_login_flow():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()

    # 1. Login with registered user
    login_url = f"{base_url}/login"
    login_data = {
        "student_id": "test_student_01",
        "password": "password123"
    }
    
    print(f"Attempting login for test_student_01...")
    response = session.post(login_url, data=login_data, allow_redirects=True)
    
    if response.status_code == 200:
        print("Login Request Executed.")
        # Check if we landed on the chat page
        if "CampusAI Assistant - Welcome, Test Student 01" in response.text:
            print("SUCCESS: Logged in and redirected to Chat Interface with correct name!")
            return True
        elif "Invalid" in response.text:
             print("FAILED: Login returned invalid credentials error.")
             return False
        else:
             print("WARNING: Landed on unexpected page.")
             print("Page Title/Snippet: ", response.text[:200])
             return False
    else:
        print(f"FAILED: Status {response.status_code}")
        return False

if __name__ == "__main__":
    verify_login_flow()
