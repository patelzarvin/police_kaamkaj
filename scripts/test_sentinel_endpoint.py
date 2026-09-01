import requests

def test_conn():
    res = requests.post("http://localhost:8000/api/sentinel/connect", json={"password": "sample_password_123"})
    print("STATUS CODE:", res.status_code)
    print("RESPONSE JSON:", res.json())

if __name__ == "__main__":
    test_conn()
