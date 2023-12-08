"""
Your Backup Tool - SERVER

This is the server-side script for YBT.
"""
import os
import json
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

# API #

app = FastAPI()


@app.get("/")
def root():
    return "Hello, world!"

@app.post("/api/users/create")
def cuser(usr: str, psw: str):
    with open(USR_MANIFEST, "r") as f:
        data = json.load(f)
    
    for user in data["users"]:
        if user["username"] == usr:
            raise HTTPException(409, "Account already exists.")

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

@app.post("/api/fs/put")
def putfile(usr: str, psw: str, dirfr: str = "", file: UploadFile = File(...)):
    """
    Put File.

    The file attached to this request (if it meets the requirements) will be placed inside

    `fs/USERNAME` if the user exists and can be authorized.

    DirFR (Directory From Root) allows for folder creation. It will be appended before the file name.

    ex. / = fs/NAME/FILE, /docs = fs/NAME/docs/FILE
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

    # Make parent dirs if they don't exist already.
    if not os.path.exists(f"./fs/{user.name}/{dirfr}"):
        os.makedirs(f"./fs/{user.name}/{dirfr}")

    # Download the file.    
    try:
        with open(path, 'wb') as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except Exception as e:
        raise HTTPException(400, f"There was an error uploading the file: {e}")
    finally:
        file.file.close()

    # Finally, return a success message and update the manifest.
    # for i, dir in enumerate(path.split("/")):
    #     if i != len(path.split("/")) -1:
    #         manifest[""]

    return {"message": f"Successfully uploaded {file.filename}"}
