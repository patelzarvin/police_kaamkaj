import requests
import sys

def debug_login(password):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://cctv.corp8.cloud/cameras.json",
        "Content-Type": "application/x-www-form-urlencoded"
    })

    login_url = "https://cctv.corp8.cloud/auth/login"
    catalog_url = "https://cctv.corp8.cloud/cameras.json"

    print(f"=== TESTING POST {login_url} WITH PASSWORD '{password}' ===")
    
    # Try POST
    resp_post = session.post(login_url, data={"password": password}, allow_redirects=True, timeout=10)
    print(f"POST Status Code: {resp_post.status_code}")
    print(f"POST Final URL: {resp_post.url}")
    print(f"POST Cookies: {session.cookies.get_dict()}")
    print(f"POST Response Text Snippet (first 400 chars):")
    print(resp_post.text[:400].encode('ascii', 'ignore').decode('ascii'))

    print("\n=== NOW GETTING CATALOGUE WITH AUTHENTICATED SESSION ===")
    resp_cat = session.get(catalog_url, timeout=10)
    print(f"GET Catalogue Status Code: {resp_cat.status_code}")
    print(f"GET Catalogue Content-Type: {resp_cat.headers.get('Content-Type')}")
    if "Sign in" in resp_cat.text:
        print("RESULT: Still showing Sign In page!")
    else:
        print("RESULT: SUCCESS! Unlocked response:")
        print(resp_cat.text[:600].encode('ascii', 'ignore').decode('ascii'))

if __name__ == "__main__":
    pw = sys.argv[1] if len(sys.argv) > 1 else "test_password"
    debug_login(pw)
