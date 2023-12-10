"""
Y(Your)B(Backup)T(Tool).
---

The Client version of YBT. Uploads select folders to the server version for backups.
"""

import argparse
import requests
import os
import json
import sys
from time import sleep

BASE_URL = "http://192.168.1.189:8000/api/"
# BASE_URL = "http://127.0.0.1:8000/api/"

parser = argparse.ArgumentParser()
parser.add_argument("path", help="The path to backup.")
parser.add_argument("-t","--top", help="For single file uploads, choose the folder to upload into. This will also create the directory if needed.")
args = parser.parse_args()

upload_path = args.path.replace("\\", "/")
endpath = upload_path.split("/")[-1]

print(f"Checking '{upload_path}'...", end=" - ")

if not os.path.exists(upload_path):
    print("FAILED: That path does not exist!")
    sys.exit(1)

print(" OK!")

# Ensure the API is reachable
print("Checking server...", end=" - ")
# Force the output to appear.
sys.stdout.flush()

try:
    r = requests.get(BASE_URL)
except requests.ConnectionError:
    print("FAILED: Check your internet connection and ensure the servers are online.")
    sys.exit(1)
if r.status_code == 200:
    print("OK!")
else:
    print("FAILED: Check your internet connection and ensure the servers are online.")
    print(r.json())

# Check for a user
print("Checking user...", end=" - ")
sys.stdout.flush()

if os.path.exists("./ybt.json"):
    with open("./ybt.json", "r") as f:
        config = json.load(f)
        config: dict

    if config["username"] and config["password"]:
        r = requests.get(BASE_URL+f"users/auth?usr={config["username"]}&psw={config["password"]}")
        if r.status_code == 200:
            print("OK!")
        elif r.status_code == 401:
            print("FAILED: Failed to login user. Ensure both your username and password is correct.")
            sys.exit(1)
        else:
            print("FAILED: Could not authorize for an unknown reason.")
            sys.exit()
    else:
        print("FAILED: Config is invalid.")
        sys.exit(1)

print(f"\nYBT will now upload '{endpath}'")

# Begin the upload procedure.
jobs = []
if os.path.isfile(upload_path):
    print("\npath is file... entering single upload mode.")
    print(f"Uploading {upload_path}...", end=" - ")
    sys.stdout.flush()
    jobs.append({"job": 1, "status": -1})

    file = {'file': open(upload_path, 'rb')}

    if args.top:
        args.top = args.top.replace("\\", "/")
        dirfr = args.top.removeprefix("/")
    else:
        dirfr = ""

    r = requests.post(BASE_URL+f"fs/put?usr={config["username"]}&psw={config["password"]}&dirfr={dirfr}", files=file)
    if r.status_code == 200:
        print("OK!")
        jobs[0]["status"] = 1
    elif r.status_code == 404:
        print(f"FAILED: Unable to locate user backup storage.")
        sys.exit()
    else:
        print(f"FAILED: ({r.json()["detail"]})")
        jobs[0]["status"] = 0

if os.path.isdir(upload_path):
    path_files = []
    print("\npath is directory... entering multiple upload mode.")
    
    # Get EVERY file inside the directory.
    for path, subdirs, files in os.walk(upload_path):
        for name in files:
            path_files.append(os.path.join(path, name))

    # Get the top directory to upload into.
    top_dir = upload_path.split("/")[-1]

    for i, file in enumerate(path_files):
        print(f"Uploading {file}...", end=" - ")
        sys.stdout.flush()

        dirfr: str = top_dir + "/" + os.path.dirname(file.split(upload_path)[1]).removeprefix("\\")
        jobs.append({"job": i, "status": -1})

        file = {'file': open(file, 'rb')}
        r = requests.post(BASE_URL+f"fs/put?usr={config["username"]}&psw={config["password"]}&dirfr={dirfr}", files=file)
        
        if r.status_code == 200:
            print("OK!")
            jobs[i]["status"] = 1
        elif r.status_code == 404:
            print(f"FAILED: Unable to locate user backup storage.")
            sys.exit()
        else:
            print("FAILED")
            jobs[i]["status"] = 0

success = 0
failed = 0
total = 0

for job in jobs:
    if job["status"] == 1:
        success += 1
    elif job["status"] == 0:
        failed += 1
    total += 1

print(f"\nFinished uploading: {success} finished | {failed} failed | {total} total")
