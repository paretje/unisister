Unisister, the sister of Unison
===============================
Unisister is a GPLv3+ licensed GUI for synchronization tools, which can synchronize multiple directories with a server, at different intervals and using different backends, although only unison support has been implemented. This makes it a possible replacement for Dropbox. But, using unisiter, you (can) keep your files under your own control, while there are no special requirements for the server, as a simple ssh connection suffices.

GUI
===
Unison started out as a fast written Python script using wxWidget. The script was poorly structured, which made modification and extension more difficult. It has now been rewritten using GTK3, although there is no GUI yet to change the config file.

Supported backends
==================
As said before, currently, Unisister has only support for unison, but csync support is planned for the future. The biggest drawback of unison is the fact it either backups all files, or none, while I would prefer to have only conflicts backupped.

Authentication
==============
Authentication to the SSH server is currently only supported by using SSH keys.

Dependencies
============
 - Python3
 - GTK3
 - Notify
 - zope.event

On Debian, this can be installed using `apt-get install python3 gir1.2-gtk-3.0 gir1.2-notify-0.7 python3-zope.event`

Configuration
=============
The configuration of Unisister should be located at `.config/unisister/syncs.ini`. This file has the following syntax:
```
[sync1]
; Required fields
server_address=server
server_location=cloud
local_location=/home/user/cloud

; Username to use for authentication on the server
server_username=user

; Interval to use between two synchronizations
; 0 indicates that the files are only synchronized when Unisister starts and
; when synchronization is forced manually (default: 0)
interval=25

: Backend to use (default: unison)
backend=unison

; Command to execute for backend
server_backend_location=bin/unison
local_backend_location=bin/unison

; Synchronize modification times with server (default: yes)
backend_synchronize_times=yes
```
