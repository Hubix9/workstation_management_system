# User friendly usage and management system for virtual workstations

## Description
This repository contains code for a Workstation Management System used as basis of thesis "User friendly usage and management system for virtual workstations".

Repository features both frontend and backend components of the system. To use the system as is, it is required to setup the following third party software in addition:
- Proxmox VE
- Websockify Proxy
- Web server hosting static files (If debug is enabled, the Django provided one can be used instead).
- Reverse proxy providing TLS termination for ex. NGINX (can also act as static file server).

### System features
- Ability to reserve and use workstations.
- Simple and easy to understand end user interface.
- On demand workstation provisioning.
- Custom workstation template configuration.
- Extensible support for workstation platforms (currently only Proxmox VE is implemented).
- Workstation search based on user's feature requirements.

### File structure

**workstation_management** <-- main project directory

Folders contained in main project directory:

**main_server** <-- Component of the system responsible for handling API requests and serving end user interface.

**workstation_coordinator** <-- Component acting as central authority on all workstation related operations. Handles whole workstation lifecycle.

**engines** <-- Workstation engine implementations, api servers and client modules. Used by workstation coordinator to communicate with workstation provisioning platforms (ex. Proxmox VE) configured in the system.

**utils** <-- Common modules used by components of the system.
