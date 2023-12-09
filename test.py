import requests
import json

# files = {'file': open("./genuid.py", 'rb')}

# r = requests.post("http://127.0.0.1:8000/api/fs/put?usr=zeropointnothing&psw=stringcheese&dirfr=python stuf/WEE", files=files)
# #r = requests.post("http://127.0.0.1:8000/api/users/create?usr=zeropointnothing&psw=stringcheese")

# print(r.json())

with open("./fs/zeropointnothing/manifest.json", "r") as f:
    data = json.load(f)

print(data)

for dir in data:
    print(dir)