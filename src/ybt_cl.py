"""
Y(Your)B(Backup)T(Tool).
---

The Client version of YBT. Uploads select folders to the server version for backups.

Copyright (C) 2023  ZeroPointNothing

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import requests
import os
import json
import sys
from time import sleep

# This should be http://YBTSERVERIP:8000/api/
BASE_URL = os.environ.get("YBT_SERVER_IP", None)
# For debugging:
# BASE_URL = "http://127.0.0.1:8000/api/"

if not BASE_URL:
    print("Unable to determine YBT server IP! Please set it with the \"YBT_SERVER_IP\" env variable!")
    sys.exit()


# Ensure we run from the location of the executable.
os.chdir(os.path.dirname(__file__))

# CLI Arguments.
parser = argparse.ArgumentParser()
parser.add_argument("path", nargs='?', default=None, help="The path to backup.")
parser.add_argument("-t","--top", help="For single file uploads, choose the folder to upload into. This will also create the directory if needed.")
parser.add_argument("-g", "--get", action="store_true", help="Get a list of all files currently uploaded to YBT's server.")
parser.add_argument("-s", "--setup", action="store_true", help="Enter setup mode to create or log into an account.")
args = parser.parse_args()

# FUNCTIONS #
def exc(exc_type, exc_value, exc_tb):
    """
    Exception handler.
    """
    # Ignore all KeyboardInterrupt errors and simply close instead.
    if exc_type == KeyboardInterrupt:
        print("\nabort signal recieved.\n")
        sys.exit(0)

    print("\n\nEncountered an unrecoverable error!")
    print(f"Report this to the creator: {exc_type.__name__} (line: {exc_tb.tb_lineno}): {exc_value}")
    # Make sure we exit here.
    sys.exit(1)

sys.excepthook = exc

def authorizeUser():
    """
    Attempts to authorize the user.

    Returns config.
    """
    if os.path.exists("./ybt.json"):
        with open("./ybt.json", "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print("FAILED: Config is invalid.")
                sys.exit()
            config: dict

        if config.get("username") and config.get("password"):
            r = requests.get(BASE_URL+f"users/auth?usr={config["username"]}&psw={config["password"]}")
            if r.status_code == 200:
                print("OK!")
            elif r.status_code == 401:
                print("FAILED: Failed to login user. Ensure both your username and password is correct.")
                sys.exit(1)
            elif r.status_code == 500:
                print("FAILED: Internal Server Error.")
                sys.exit(1)
            else:
                print("FAILED: Could not authorize for an unknown reason.")
                sys.exit()
        else:
            print("FAILED: Config is invalid.")
            sys.exit(1)

        return config
    else:
        print("FAILED: Could not find the ybt.json config file! Please run YBT with the -s flag to create it.")
        sys.exit()

def makeAPIRequest(url: str = "", post: bool = False) -> any:
    """
    Make an API request and print either OK or FAILED based on the result.

    Set post to True to make a post request.
    
    Returns r.json().
    """
    # Flush stdout to ensure all print statements are shown.
    sys.stdout.flush()

    try:
        if post:
            r = requests.post(BASE_URL+url)
        else:
            r = requests.get(BASE_URL+url)
    except requests.ConnectionError:
        print("FAILED: Check your internet connection and ensure the servers are online.")
        sys.exit(1)

    if r.status_code == 200:
        print("OK!")
    elif r.status_code == 401:
        print("FAILED: Failed to auth.")
        sys.exit(1)
    elif r.status_code == 500:
        print("FAILED: Internal Server Error.")
        sys.exit(1)
    elif r.status_code == 404:
        print("FAILED: Failed to locate resource.")
        sys.exit(1)
    elif r.status_code == 409:
        print("FAILED: Data conflict. Try something else!")
        sys.exit(1)
    else:
        print(f"FAILED: Unexpected response from server! {r.status_code}")
        sys.exit(1)

    return r.json()
    
def print_tree(data: dict, indent=''):
    """
    Iterate through a dictionary and print out a Tree structured version of it.

    Dictionaries count as sub-folders, and their contents will cause an indent.
    """
    for name, contents in data.items():
        print(f"{indent}└── {name}")
        # print(value)
        if isinstance(contents, list):
            size = len(contents)-1
            for i, subcontents in enumerate(contents):
                # If the item is a dictionary AKA a folder, start iterating through it instead.
                if isinstance(subcontents, dict):
                    print_tree(subcontents, indent + "    ")
                    size -= 1
                    continue
                elif i != size:
                    print(f"{indent}    ├── {subcontents}")
                else:
                    print(f"{indent}    └── {subcontents}")

def cls():
    os.system('cls' if os.name=='nt' else 'clear')
###

if args.get:
    print("Checking server...", end=" ")
    makeAPIRequest()

    print("Checking user...", end=" ")
    config = authorizeUser()

    print("Fetching file manifest...", end=" ")
    manifest = makeAPIRequest(f"fs/getmanifest?usr={config["username"]}&psw={config["password"]}")

    print("\n\n= = Current Backup Storage Contents ==")

    # Print the manifest in tree form.
    print_tree(manifest)
    # pprint(manifest, sort_dicts=True, indent=2)

    sys.exit(0)
elif args.setup:
    print("Checking server...", end=" ")
    makeAPIRequest()

    while True:
        print("Are you creating an account or logging in?")
        print("\na) Log In")
        print("b) Create An Account")
        user_input = input("\nEnter a response: > ")

        if user_input.lower() in ["1", "a", "l", "log in"]:
            create_account = False
        elif user_input.lower() in ["2", "b", "c", "create"]:
            create_account = True
        else:
            print("\nPlease enter a valid response!")
            sleep(2)
            cls()
            continue
            
        username = input("\nEnter your username (must be all lowercase and greater than three characters): ").replace(" ", "")
        password = input("\bEnter your password (must be greater than 5 characters): ").replace(" ", "")

        if (not username or len(username) < 3) or (not password or len(password) < 5):
            print("Please enter valid credentials!")
            sleep(2)
            sys.exit()
        break
    

    if create_account:
        print("\nCreating account...", end=" ")
        makeAPIRequest(f"users/create?usr={username}&psw={password}", True)
    else:
        print("\nLogging in...", end=" ")
        makeAPIRequest(f"users/auth?usr={username}&psw={password}")

    # Create the user's login info for automatic login.
    with open("./ybt.json", "w") as f:
        json.dump({
            "username": username,
            "password": password
            }, f, indent=2)
    sys.exit(0)

# Operations requiring path.

if not args.path:
    print("Please supply a path!")
    sys.exit(1)

upload_path = args.path.replace("\\", "/")
endpath = upload_path.split("/")[-1]

print(f"Checking '{upload_path}'...", end=" ")

if not os.path.exists(upload_path):
    print("FAILED: That path does not exist!")
    sys.exit(1)

print("OK!")

# Ensure the API is reachable
print("Checking server...", end=" ")
# Force the output to appear.
makeAPIRequest()

# Check for a user
print("Checking user...", end=" ")
sys.stdout.flush()

config = authorizeUser()

print(f"\nYBT will now upload '{endpath}'")

# Begin the upload procedure.
jobs = []
if os.path.isfile(upload_path):
    print("\npath is file... entering single upload mode.")
    print(f"Uploading {upload_path}...", end=" ")
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
        print(f"Uploading {file}...", end=" ")
        sys.stdout.flush()

        # DirectoryFromRoot. This will place the file in subfolders instead of just in root.
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
