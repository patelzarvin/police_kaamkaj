import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://cctv.corp8.cloud"
CATALOGUE_URL = f"{BASE_URL}/cameras.json"
LOGIN_URL = f"{BASE_URL}/auth/login"
REGISTER_URL = f"{BASE_URL}/auth/register"
HLS_PASSWORD = os.getenv("SENTINEL_HLS_PASSWORD", "")

def test_catalogue():
    print(f"=== TESTING OFFICIAL SENTINEL CATALOGUE: {CATALOGUE_URL} ===")
    session = requests.Session()
    session.headers.update({"User-Agent": "Sentinel-Police-AI/1.0"})

    # Step 1: Check if password provided in .env and attempt login
    if HLS_PASSWORD:
        print(f"Attempting login to {LOGIN_URL} with SENTINEL_HLS_PASSWORD...")
        resp = session.post(LOGIN_URL, data={"password": HLS_PASSWORD})
        print(f"Login POST Response: {resp.status_code}, URL: {resp.url}")

    # Step 2: Fetch cameras.json using authenticated session
    response = session.get(CATALOGUE_URL, timeout=10)
    print(f"Catalogue GET HTTP Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")

    if "Sign in" in response.text or "login" in response.text.lower():
        print("\n[AUTHENTICATION REQUIRED]")
        print("The Sentinel server requires an Access Password.")
        print("Form Target: POST https://cctv.corp8.cloud/auth/login")
        print("Field: password (format: XXXX-XXXX-XXXX)")
        print("\nPlease set SENTINEL_HLS_PASSWORD=<your_password> in .env file.")
        return False, "AUTH_REQUIRED"

    try:
        data = response.json()
        print("\n[SUCCESS] Catalogue JSON parsed successfully!")
        print(f"Total cameras discovered: {len(data)}")
        for cam in data[:5]:
            print(f" - {cam}")
        return True, data
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return False, response.text

if __name__ == "__main__":
    test_catalogue()
