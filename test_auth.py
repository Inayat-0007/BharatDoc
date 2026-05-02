import urllib.request
import json

data = json.dumps({"email": "test2@test.com", "password": "password123"}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8000/auth/register", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as f:
        print("Register:", f.read().decode("utf-8"))
except Exception as e:
    print("Error:", e)
