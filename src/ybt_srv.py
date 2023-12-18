"""
Your Backup Tool - SERVER

Server-side script for YBT. Expects that the `fs` folder is already created.

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
import os
import json
import uvicorn
import logging
import argparse
import hashlib
from fastapi import FastAPI, HTTPException, File, UploadFile

# Force YBT to run inside the src folder.
os.chdir(os.path.dirname(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--test", action="store_true", help="Run in testing mode: Uvicorn Host will be set to localhost instead of 0.0.0.0 (port forward host).")
args = parser.parse_args()

# VARS #

USR_MANIFEST = "./fs/manifest.json"

# CLASSES #

class User():
    """
    User class.

    Contains a FileSystem object for organized file management.

    Calls the authUser() method on creation, but this can be used again. 
    """
    def __init__(self, username: str, password: str) -> None:
        self.name = username
        self.password = password
        self.fs = FileSystem(self)

        # Authorize the user.
        if not self.authUser(username, password):
            raise PermissionError("User failed to auth.")

    def authUser(self, usr: str, psw: str):
        """
        Authorize the user.

        Returns True if the username and password is correct.

        Returns False if the user cannot be found or has an invalid password.
        """
        with open(USR_MANIFEST, "r") as f:
            manifest = json.load(f)

        psw = hashlib.sha384(psw.encode()).hexdigest()

        for user in manifest["users"]:
            if user["password"] == psw and user["username"] == usr:
                return True
        return False


class FileSystem():
    """
    User Filesystem.

    This is used to ensure that all files go to the user's deticated folder.

    One filesystem cannot modify the contents of another.

    All read/write requests should be made from here.
    """
    def __init__(self, user: User) -> None:
        # Internal user variable. Not meant to be accessed from outside.
        self.__user = user

        self.__BASE_PATH = f"./fs/{self.__user.name}"
        self.__man_path = os.path.join(self.__BASE_PATH, f"manifest.json")
        pass

    class NoSuchUser(BaseException):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    def loadManifest(self) -> dict:
        """
        Attempts to load the user's fs Manifest.

        Returns the Manifest data if it can be found and raises NoSuchUser elsewise.
        """
        try:
            with open(self.__man_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise self.NoSuchUser(f"User '{self.__user.name}' does not exist, or their manifest is missing.")
    
    def dumpManifest(self, data: dict) -> dict:
        """
        Same as loadManifest, but dumps instead.
        """
        try:
            with open(self.__man_path, "w") as f:
                return json.dump(data, f, indent=2)
        except FileNotFoundError:
            raise self.NoSuchUser(f"User '{self.__user.name}' does not exist, or their manifest is missing.")

# API #

app = FastAPI()


@app.get("/api")
def root():
    return "Hello, world!"

@app.post("/api/users/create")
def cuser(usr: str, psw: str):
    # Load the UserManifest
    with open(USR_MANIFEST, "r") as f:
        data = json.load(f)
    
    for user in data["users"]:
        if user["username"] == usr:
            raise HTTPException(409, "Account already exists.")

    # Add the new user to the UserManifest
    with open(USR_MANIFEST, "w") as f:
        data["users"].append({"username": usr, "password": hashlib.sha384(psw.encode()).hexdigest()})

        json.dump(data, f, indent=2)

    # Create the user's directory.
    os.mkdir(f"./fs/{usr}")

    # Create their manifest.
    with open(f"./fs/{usr}/manifest.json", "w") as f:
        # Files are organized like so:
        # dict_keys = directory
        # dict_values = files
        #
        # Root is the top level folder.
        json.dump({
            "root": []
        }, f, indent=2)

    return 200

@app.get("/api/users/auth")
def guser(usr: str, psw: str):
    # Load the UserManifest
    with open(USR_MANIFEST, "r") as f:
        data = json.load(f)
    
    for user in data["users"]:
        if user["username"] == usr and user["password"] == hashlib.sha384(psw.encode()).hexdigest():
            return {"content": "Authed user!"}
    
    raise HTTPException(401, "Failed to auth.")

@app.post("/api/fs/put")
def putfile(usr: str, psw: str, dirfr: str = "", file: UploadFile = File(...)):
    """
    Put File.

    The file attached to this request (if it meets the requirements) will be placed inside
    `fs/USERNAME` if the user exists and can be authorized.

    DirFR (Directory From Root) allows for folder creation. It will be appended before the file name.

    ex. / = `fs/NAME/FILE`, /docs = `fs/NAME/docs/FILE`
    """
    try:
        user = User(usr, psw)
    except PermissionError:
        raise HTTPException(401, "Failed to auth.")

    # Load the user's manifest.
    try:
        manifest = user.fs.loadManifest()
    except FileSystem.NoSuchUser:
        raise HTTPException(404, "Could not load user manifest. Aborting.")

    # path.join doesn't work with a leading slash.
    dirfr = dirfr.removeprefix("/")
    if dirfr.startswith("/"):
        return HTTPException(422, "Invalid path name.")

    # Figure out the correct path based on the contents of dirfr.
    path: str = os.path.join(f"./fs/{user.name}", os.path.join(dirfr, file.filename))
    # To prevent weird bugs, replace all backslashes with slashes.
    path = path.replace("\\", "/")
    dirfr = dirfr.replace("\\", "/")

    # Make parent dirs if they don't exist already.
    if not os.path.exists(f"./fs/{user.name}/{dirfr}"):
        os.makedirs(f"./fs/{user.name}/{dirfr}")

    # Reject root level manifest.json files to prevent replacement.
    # print(path)
    if path == f"./fs/{user.name}/manifest.json":
        raise HTTPException(409, "Cannot upload root-level 'manifest.json' file!")

    # Download the file.    
    try:
        with open(path, 'wb') as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except Exception as e:
        # print(e)
        raise HTTPException(400, f"There was an error uploading the file: {e}")
    finally:
        file.file.close()

    # Finally, return a success message and update the manifest.

    # Loop through all the sub dirs minus the three leading dirs since we know those lead to root. (fs/USER)
    # This gets its own variable because I type it out too much lol
    base_split = path.split("/")[2:]
    # TThe first value should be "root". AKA ./fs/USER/
    base_split[0] = ""

    dirs = []
    # For Manifest assembling. This starts at root.
    current_manifest_entry = manifest["root"]
    for i, dir in enumerate(base_split):
        dirs.append(dir)
        joined_path = f"./fs/{user.name}/{'/'.join(dirs)}"
        
        # Use the joined path to determine whether the path is a directory or a file.
        is_dir = os.path.isdir(joined_path)
        is_file = os.path.isfile(joined_path)
        is_root = True if i == 0 else False

        # print(f"File/Directory: {dir}")
        # print(f"Joined path: {joined_path}")
        # print(f"Is dir: {os.path.isdir(joined_path)}")
        # print(f"Is file: {os.path.isfile(joined_path)}")
        # print(f"Is root: {is_root}\n\n")

        # The path is a directory.
        if is_dir:
            # Root already exists. We don't need to make another one.
            if dir == "":
                continue
            
            # print(manifest)
            # print(current_manifest_entry)
            # current_manifest_entry: list

            # Check if the folder exists already. If it does, move into it.
            exists = False
            for i, subdir in enumerate(current_manifest_entry):
                subdir: dict
                if type(subdir) == dict and dir in list(subdir.keys()):
                    current_manifest_entry = current_manifest_entry[i][dir]
                    exists = True
                    break
            if exists:
                continue

            # Add the folder into the manifest.
            current_manifest_entry.append({dir: []})

            # Move the current_manifest_entry inside the list.
            current_manifest_entry = current_manifest_entry[-1][dir]
        # The path is a file.
        elif is_file:
            # If the file already exists in the manifest, there is no point adding it again.
            exists = False
            for subfile in current_manifest_entry:
                if dir == subfile:
                    exists = True
                    break
            if exists:
                continue

            current_manifest_entry.append(dir)

    user.fs.dumpManifest(manifest)
    # for dir in path.split("/")[:len(path.split("/"))-1]:
    #     print(dir)

    return {"message": f"Successfully uploaded {file.filename}"}

@app.get("/api/fs/getmanifest")
def getmanifest(usr: str, psw: str):
    try:
        user = User(usr, psw)
    except PermissionError:
        raise HTTPException(401, "Failed to auth.")
    
    try:
        manifest = user.fs.loadManifest()
    except FileSystem.NoSuchUser:
        raise HTTPException(500, "Unable to find user's manifest. Try again later.")

    return manifest

# # Configure logging to a file
# logging_config = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "default": {
#             "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#         },
#     },
#     "handlers": {
#         "file_handler": {
#             "class": "logging.FileHandler",
#             "formatter": "default",
#             "filename": "uvicorn.log",
#         },
#     },
#     "loggers": {
#         "uvicorn": {
#             "handlers": ["file_handler"],
#             "level": "INFO",
#             "propagate": False,
#         },
#     },
# }

if __name__ == "__main__":
    invalid_manifest = False
    if os.path.exists(USR_MANIFEST):
        with open(USR_MANIFEST, "r") as f:
            data: dict = json.load(f)
        
        if not data.get("users"):
            invalid_manifest = True
    else:
        invalid_manifest = True
    
    if invalid_manifest:
        parent_folder = os.path.dirname(USR_MANIFEST)

        if not os.path.exists(parent_folder): os.makedirs(parent_folder)
        with open(USR_MANIFEST, "w") as f:
            print("fs Manifest was invalid or missing. Recreating.")
            json.dump({
                "users": []
            }, f, indent=2)

    # In case 0.0.0.0 does not loop back through localhost
    if not args.test:
        uvicorn.run(app, host="0.0.0.0")
    else:
        print("WARNING: Running in test mode! This server will not be accessible outside of localhost!")
        uvicorn.run(app)