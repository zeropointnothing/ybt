# .ybt
Your BackUp Tool. Designed for a PROXMOX server ported forward.

YBT is a file backup service like OneDrive. It runs on a PROXMOX server on a home network, so only authorized sources can access it.

YBT is split into two parts. `ybt_srv` and `ybt_cl`. `ybt_cl` is the Client version of YBT. It will automatically track any differences in synced folders and upload them to `ybt_srv`.

# How To Use

YBT stores your files on a seperate computer. But in order to do this, it needs some help.

This will explain how to properly use YBT.

## Single File Uploads
You can upload just one file to YBT's servers. To do so, simply run the executable like so:

ex. uploading a text file:
```
ybt.exe "C:/Users/me/OneDrive/Desktop/hello.txt"
```
will upload to: root/hello.txt

### NOTE 
YBT will assume you want to upload the file to "root", AKA the top level of your backup folder.

To specify the folder to backup the file to, use the -t or --top argument.

ex.
```
ybt.exe "C:/Users/me/OneDrive/Desktop/hello.txt" -t "Documents/funthings"
```
will upload as: root/Documents/funthings/hello.txt

## Folder Uploads

YBT supports uploading multiple files at once. To do so, supply the folder you wish to upload.

ex. uploading your entire Documents folder.
```
ybt.exe "C:/Users/me/OneDrive/Documents"
```
will upload all files and their folders (and the files inside those too) to: root/Documents

### NOTE
This does not support the -t argument. Supplying it will do nothing.

# File Conflicts

If a file you are uploading already exists in it's YBT backup copy location, it will be overwritten.

As of now, files cannot be removed from YBT servers through the YBT executable. If you would like a file to be removed, please contact me and I will remove it for you.
