# .ybt
Your BackUp Tool. Designed for a PROXMOX server ported forward.

YBT is a file backup service like OneDrive. It runs on a PROXMOX server on a home network, so only authorized sources can access it.

YBT is split into two parts. `ybt_srv` and `ybt_cl`. `ybt_cl` is the Client version of YBT. It will automatically track any differences in synced folders and upload them to `ybt_srv`.
