import requests

files = {'file': open("./requirements.txt", 'rb')}

r = requests.post("http://127.0.0.1:8000/api/fs/put?usr=zeropointnothing&psw=stringcheese&dirfr=/docs/important files", files=files)
# r = requests.post("http://127.0.0.1:8000/api/users/create?usr=zeropointnothing&psw=stringcheese")

print(r.json())
