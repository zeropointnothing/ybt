# ybt
Your BackUp Tool. Designed for a PROXMOX server ported forward.

YBT is a file backup service like OneDrive. It is designed to run on a PROXMOX server on a home network, so only authorized sources can access it.

YBT is split into two parts. `ybt_srv` and `ybt_cl`. `ybt_cl` is the Client version of YBT. It will automatically track any differences in synced folders and upload them to `ybt_srv`.

# How To Use

YBT stores your files on a seperate computer. But in order to do this, it needs some help.

This will explain how to properly use YBT.

## Setup

Before you can use YBT, you will have to tell it where the server is located. To do so, please set the `YBT_SERVER_IP` environment variable for your system to point at the running YBT server.
ex: `http://172.217.22.14:8000/api/` Contact a system administrator or look up the specific method for your OS.


In order to keep everyone's files seperate and safe, your data is protected with an account. That means in order to use YBT, you will have to tell it who you are.

*this also applies to you if you are getting this error when trying to upload: FAILED: Config is invalid.*

To set up YBT, run the executable with the `-s` or `--setup` flag.
```
ybt.exe -s

ybt.exe --setup
```

YBT will walk you through the setup process, and if all goes well, the file `ybt.json` will be created. You can look inside, but be careful! Messing with these values can prevent you from uploading correctly!

*for those who wish to do it themselves, the `ybt.json` file is formatted like so:*
```json
{
    "username": "YOURUSERNAMEHERE",
    "password": "YOURPASSWORDHERE"
}
```

## Single File Uploads
You can upload just one file to YBT's servers. To do so, simply run the executable like so:

ex. uploading a text file:
```
ybt.exe "C:/Users/me/OneDrive/Desktop/hello.txt"
```
this will upload to: root/hello.txt

### NOTE 
YBT will assume you want to upload the file to "root", AKA the top level of your backup folder.

To specify the folder to backup the file to, use the `-t` or `--top` flag.

ex.
```
ybt.exe "C:/Users/me/OneDrive/Desktop/hello.txt" -t "Documents/funthings"
```
this will upload as: root/Documents/funthings/hello.txt

## Folder Uploads

YBT supports uploading multiple files at once. To do so, supply the folder you wish to upload.

ex. uploading your entire Documents folder.
```
ybt.exe "C:/Users/me/OneDrive/Documents"
```
this will upload all files and their folders (and the files inside those too) to: root/Documents

### NOTE
This does not support the `-t` flag. Supplying it will do nothing.

You cannot upload a file named `manifest.json` to the root of your backup folder. This is a system file for YBT and cannot be overwritten. Any attempt to do so will fail.

## The Get Command
If you would like to see the files you have already uploaded to YBT, you can do so with the `-g` or `--get` flag. This will print out a tree view of all your files.


To use this, run the YBT executable like so:
```
ybt.exe -g

ybt.exe --get
```

# File Conflicts

If a file you are uploading already exists in it's YBT backup copy location, it will be overwritten.

As of now, files cannot be removed from YBT servers through the YBT executable. If you would like a file to be removed, please contact me and I will remove it for you.

# Upload Rules
To protect your system (and bandwidth), there are rules hard-coded into YBT that prevent it from uploading certain directories. Here are those rules:

### Linux
- Rule 0: Root (/)
- Rule 1: User(s) folder (/home/**)

### Windows
- Rule 3: Root (*:)
- Rule 4: User(s) folder (*:/Users/**)
- Rule 5: System Folder (*:/Windows)

<details>
  <summary><i>full regex (for developers)</i></summary>

  ```python
  ["^/$", "^/home/?([A-Za-z0-9]+)?/?$", ".:$", "^[A-Za-z]:/Users/?([A-Za-z0-9]+)?/?$", ".:/Windows/?$"]
  ```
</details>

---

Trying to upload to any of these directories will fail, giving you the *"Path violates the following rule(s)"* error
=======
As of now, files cannot be removed from YBT servers through the YBT executable. If you would like a file to be removed, please contact a server admin and they will have to remove it for you.
