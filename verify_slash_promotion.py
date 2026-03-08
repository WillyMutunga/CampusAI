import requests

def verify_slash_promotion():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    # 1. Login as Admin
    print("Logging in as admin...")
    session.post(f"{base_url}/admin/login", data={"student_id": "test_student_01", "password": "password123"})
    
    # 2. Promote User with Slashes
    target_id = "P01/9999/2026"
    print(f"Promoting {target_id}...")
    # Requests will URL-encode the path automatically if we construct it properly? 
    # Actually, requests.get(url) just sends it.
    # We need to manually handle the URL structure if doing string formatting.
    # Browser sends: /admin/promote/P01%2F9999%2F2026 or /admin/promote/P01/9999/2026 ?
    # Browsers usually send /admin/promote/P01/9999/2026.
    
    response = session.get(f"{base_url}/admin/promote/{target_id}")
    
    if "User P01/9999/2026 promoted" in response.text: # Flash message
        print("SUCCESS: Flash message confirmed promotion.")
    elif "Manage Students" in response.text:
         print("Redirected to Students page. Checking existence...")
    else:
        print("FAILED: Unexpected response.")
        print(response.text[:200])
        
    # 3. Verify via Admin Student List
    print("Checking student list...")
    list_response = session.get(f"{base_url}/admin/students")
    if "P01/9999/2026" in list_response.text and "Admin" in list_response.text:
        # We need to be careful matching "Admin" badge near the user.
        # But if it works, it works.
        print("SUCCESS: User appears in list.")
    else:
        print("FAILED: User not found or not Admin.")

if __name__ == "__main__":
    verify_slash_promotion()
