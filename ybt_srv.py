"""
Your Backup Tool - SERVER

This is the server-side script for YBT.
"""
import os
import json
import uvicorn
import genuid
import hashlib
from fastapi import FastAPI, HTTPException, File, UploadFile

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
    if dirfr.startswith("/"):
        return HTTPException(422, "Invalid path name.")

    # Figure out the correct path based on the contents of dirfr.
    path: str = os.path.join(f"./fs/{user.name}", os.path.join(dirfr, file.filename))
    # For ease of use, make all slashes normal slashes.
    path = path.replace("\\", "/")

    # Make parent dirs if they don't exist already.
    if not os.path.exists(f"./fs/{user.name}/{dirfr}"):
        os.makedirs(f"./fs/{user.name}/{dirfr}")

    # Download the file.    
    try:
        with open(path, 'wb') as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except Exception as e:
        print(e)
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")