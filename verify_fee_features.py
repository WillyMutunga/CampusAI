import requests
import os

def verify_admin_upload_and_chat():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    # 1. Login as Admin
    print("Logging in as admin (test_student_01)...")
    session.post(f"{base_url}/login", data={"student_id": "test_student_01", "password": "password123"})
    
    # 2. Upload Fee Structure
    print("Uploading fee structure...")
    files = {'file': ('test_fee_structure.pdf', b'%PDF-1.4 dummy content', 'application/pdf')}
    response = session.post(f"{base_url}/admin/upload", files=files)
    
    if "Fee structure uploaded successfully!" in response.text:
        print("SUCCESS: Admin upload worked.")
    else:
        print("FAILED: Admin upload failed.")
        print(response.text[:200])
        return False

    # 3. Simulate Chat Query for Fee Structure
    print("Querying chat for fee structure...")
    chat_response = session.post(f"{base_url}/get", json={"message": "fee structure"}).json()
    print(f"Bot Response: {chat_response['response']}")
    
    if "fee_structure.pdf" in chat_response['response']:
        print("SUCCESS: Chat returned fee structure link.")
    else:
        print("FAILED: Chat did not return link.")
        return False

    # 4. Simulate Chat Query for Fee Balance
    print("Querying chat for fee balance...")
    chat_response = session.post(f"{base_url}/get", json={"message": "check my fee balance"}).json()
    print(f"Bot Response: {chat_response['response']}")
    
    if "visit the student portal" in chat_response['response']:
        print("SUCCESS: Chat returned portal advice.")
    else:
        print("FAILED: Chat did not return portal advice.")
        return False
        
    return True

if __name__ == "__main__":
    verify_admin_upload_and_chat()
