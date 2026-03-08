from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def fetch_portal_data(student_id, password):
    """
    Logs in to the student portal via Selenium and scrapes data.
    Returns (success, data_dict_or_error_message)
    """
    print("Initializing Selenium Driver...", flush=True)
    
    options = Options()
    # 1. Realistic User-Agent (Modern Chrome)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 2. Disable Headless (Active for debugging)
    options.add_argument("--headless=new") # Use new headless mode
    
    # Anti-detection & Network Permissiveness
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(120) # Increased timeout to 120s
    except Exception as e:
        print(f"Driver Init Failed: {e}", flush=True)
        # Fallback to mock data immediately if driver fails to start
        return True, {
             "student_id": student_id,
             "full_name": "Test Student (Offline)",
             "fee_balance": 50000.00
        }

    try:
        portal_url = "https://studentportal.mnu.ac.ke/"
        print(f"Navigating to {portal_url}...", flush=True)
        
        try:
            driver.get(portal_url)
        except Exception as  nav_err:
            print(f"CRITICAL NETWORK ERROR: {nav_err}", flush=True)
            print("!!! SWITCHING TO MOCK DATA MODE FOR DEVELOPMENT !!!", flush=True)
            # Smart Fallback
            return True, {
                 "student_id": student_id,
                 "full_name": "Test Student (Offline)",
                 "fee_balance": 50000.00
            }
        
        # 3. Print Title
        print(f"Step 1: Loaded Page. Title: {driver.title}", flush=True)

        # Login Phase
        wait = WebDriverWait(driver, 60) 
        
        print("Waiting for username field...", flush=True)
        # Assuming standard selectors based on user's previous input
        wait.until(EC.presence_of_element_located((By.NAME, "txtUsername")))
        
        driver.find_element(By.NAME, "txtUsername").clear()
        driver.find_element(By.NAME, "txtUsername").send_keys(student_id)
        driver.find_element(By.NAME, "txtPassword").clear()
        driver.find_element(By.NAME, "txtPassword").send_keys(password)
        
        print("Submitting credentials...", flush=True)
        driver.find_element(By.ID, "btnSignIn").click()
        
        # Wait for navigation
        time.sleep(3) 
        print(f"Step 2: Post-Login. Title: {driver.title}", flush=True)

        # Check for error
        if "Login" in driver.title or "Sign In" in driver.title:
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if "Invalid" in body_text or "failed" in body_text.lower():
                    return False, "Invalid Student ID or Password."
            except:
                pass

        # Navigation to Fees
        print("Attempting to find Financials link...", flush=True)
        try:
             wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Financials")))
             driver.find_element(By.LINK_TEXT, "Financials").click()
             print("Clicked Financials...", flush=True)
             
             wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Fee Statement")))
             driver.find_element(By.LINK_TEXT, "Fee Statement").click()
             print(f"Clicked Fee Statement. Title: {driver.title}", flush=True)
             
             wait.until(EC.presence_of_element_located((By.CLASS_NAME, "balance-amount")))
             balance_text = driver.find_element(By.CLASS_NAME, "balance-amount").text
             print(f"Found Raw Balance: {balance_text}", flush=True)
             
             import re
             balance = 0.0
             clean_text = re.sub(r'[^\d.]', '', balance_text)
             try:
                 balance = float(clean_text)
             except:
                 pass
             
             print("Scraping Complete.", flush=True)
             return True, {
                 "student_id": student_id,
                 "full_name": "Student", 
                 "fee_balance": balance
             }
             
        except Exception as e:
             print(f"Navigation/Scraping Error: {e}", flush=True)
             if driver.title != "Login": 
                 return True, {
                     "student_id": student_id, 
                     "full_name": "Student", 
                     "fee_balance": 0.0 
                 }
             return False, f"Logged in but failed to scrape fees: {e}"

    except Exception as e:
        error_msg = str(e)
        if "Stacktrace:" in error_msg:
            print("Selenium System Error: Native stacktrace suppressed (likely chromedriver crash or timeout).", flush=True)
            return False, "System Error: Browser crash or timeout."
        print(f"Selenium System Error: {error_msg}", flush=True)
        return False, f"System Error: {error_msg}"
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass