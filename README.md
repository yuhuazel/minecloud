<div align="center">

<img src="./minecloud.png" alt="MineCloud Logo" width="180">

# MineCloud
### Secure Google Drive-Based Minecraft Server Cloud Management Platform

<p align="center">
  <strong>Manage, Synchronize, Backup, and Secure your Minecraft Server from Anywhere.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Google%20Drive-API-4285F4?style=for-the-badge&logo=google-drive&logoColor=white">
  <img src="https://img.shields.io/badge/Fernet-Encryption-009688?style=for-the-badge">
  <img src="https://img.shields.io/badge/Platform-Windows-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/License-MIT-success?style=for-the-badge">
</p>

---

A modern cloud-based Minecraft server management platform that securely synchronizes worlds through **Google Drive**, provides **encrypted user management**, **cloud backups**, **permission control**, and a complete **administration console** for managing multiplayer server deployments.

Designed for server owners who want a lightweight alternative to expensive hosting panels while keeping complete control over their own cloud storage.

</div>

---

# ✨ Features

## 🔒 Security

- AES‑grade Fernet encryption
- Encrypted backend database
- Secure Google OAuth authentication
- SHA‑256 password hashing
- One‑time activation strings (no permanent tokens)
- Admin ownership verification (Google Drive folder owner)
- User approval system
- Encrypted local vault
- Cloud permission management
- Audit logging

---

## ☁️ Cloud Infrastructure

- Google Drive integration
- Automatic cloud synchronization
- Incremental world backups
- Backup verification
- Backup rollback via Drive revisions
- Cloud revision history
- Automatic upload/download
- Version tracking (MD5‑based integrity)

---

## 👥 User Management

- Activation‑based registration
- Auto‑approval in public mode
- Manual approval in restricted mode
- Login with Remember Me
- Reauthenticate Account (email mismatch)
- Bulk approve / revoke
- User search and sorting
- Email‑based permissions

---

## 🎮 Minecraft Management

- Launch / Stop server
- Auto‑detect .bat / .jar executables
- Configurable RAM settings (for .bat files)
- Live server console with command input
- Server state monitoring
- Automatic cloud sync (upload)
- Parallel HTTP download for fast world retrieval
- Server location modes: Automatic (AppData) or Manual (custom folder)

---

## ⚙️ Administration

- Infrastructure setup wizard
- Folder permission manager (Public / Restricted)
- Automatic permission migration between modes
- One‑time activation string generation
- Backend reset (repair)
- Configuration backup & restore (includes OAuth secret)
- Audit history
- Revision rollback

---

# 🏗 Architecture

```
                         Google Drive

            ┌────────────────────────────┐
            │      Backend Folder        │
            │────────────────────────────│
            │ accounts.json (encrypted)  │
            │ tokens.json (activation    │
            │            strings)        │
            │ folder_settings.json       │
            │ audit_log.json             │
            │ access_config.enc          │
            └─────────────┬──────────────┘
                          │
                  Fernet Encryption
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
 Master Manager                      Client Console
 (Administrator)                     (Server Owner)
        │                                   │
        └───────────────┬───────────────────┘
                        │
                        ▼
             Google Drive Server Folder
                        │
                world_backup.zip
```

---

# 🖥 Screens

## Master Manager

✔ Infrastructure Setup (Backend/Server folders, OAuth secret)  
✔ Google Drive Authentication (with ownership check)  
✔ Activation String Generation  
✔ User Management (search, approve, reject, revoke)  
✔ Folder Permissions (Public / Restricted toggle)  
✔ Rollback Manager (restore previous world backups)  
✔ Configuration Backup & Import (portable, encrypted)  
✔ Backend Repair & Reset  
✔ Logout & Reauthenticate

---

## Client Console

✔ One‑time Activation (paste string)  
✔ Registration (username, email, password)  
✔ Login with Remember Me  
✔ Server Control (launch, stop, console)  
✔ Cloud Sync (download / upload world)  
✔ Server Location: Auto or Manual mode  
✔ RAM Configuration (for .bat files)  
✔ Reauthenticate Account (on email mismatch)

---

# 🔑 Backend Files

All backend files are encrypted using Fernet encryption (except `audit_log.json` and `access_config.enc`, which is encrypted with a separate activation key).

| File | Purpose |
|------|----------|
| accounts.json | Registered users (username, email, status) |
| tokens.json | List of unused activation strings |
| folder_settings.json | Permission mode (`public` or `restricted`) |
| audit_log.json | Administrative logs (plain JSON) |
| access_config.enc | Bootstrap payload for clients (activation‑key encrypted) |

---

# 🛡 Security

MineCloud uses a layered security model.

- Google OAuth Authentication
- Fernet Encryption (AES‑CBC + HMAC)
- SHA‑256 Password Hashing
- One‑time Activation Strings (single‑use, removed immediately)
- Admin Ownership Verification (Drive folder owner check)
- User Approval Workflow
- Google Drive Permission API
- Encrypted Local Vault (machine‑specific key)
- Audit Logging
- Portable Backup Encryption (fixed application key)

No backend credentials are exposed to end users.

---

# ⚡ Technologies Used

## Language

- Python 3

---

## GUI

- CustomTkinter

---

## Google APIs

- Google Drive API
- OAuth2

---

## Cryptography

- cryptography
- Fernet Encryption

---

## Standard Libraries

- json
- hashlib
- threading
- subprocess
- zipfile
- os
- io
- time

---

# 🔧 Google Cloud Setup

1. **Create a Google Cloud Project** – Go to the [Google Cloud Console](https://console.cloud.google.com/), create a new project (or use an existing one).

2. **Enable the Google Drive API** – In the project, navigate to **APIs & Services > Library**, search for "Google Drive API", and enable it.

3. **Configure the OAuth consent screen**  
   - Go to **APIs & Services > OAuth consent screen**.  
   - Choose **External** user type and click **Create**.  
   - Fill in the required fields (app name, user support email, developer contact email).  
   - On the **Scopes** page, add the following scope:  
     `https://www.googleapis.com/auth/drive`  
   - On the **Test users** page, add **your own email address** (the admin account).  
   - Save and continue.  
   - **Publish the app**: After saving, go back to the OAuth consent screen, click **Publish App** under **Publishing status**. This moves the app to "In production" and allows any Google user to authenticate without you having to manually add their emails – they will see an unverified app warning, but can still proceed.

4. **Create OAuth 2.0 Client ID**  
   - Go to **APIs & Services > Credentials**.  
   - Click **Create Credentials > OAuth client ID**.  
   - Choose **Desktop app** as the application type.  
   - Name it (e.g., "MineCloud Master").  
   - Click **Create** and download the resulting `client_secret.json` file.  

5. **Open the Master Manager** and fill in the following:
   - **Backend Folder ID** – the ID of the Google Drive folder that will store the encrypted configuration files.
   - **Server Folder ID** – the ID of the Google Drive folder where the world backup (`world_backup.zip`) will be stored.
   - **OAuth Secret JSON** – browse and select the `client_secret.json` file you downloaded.

6. Click **Initialize Infrastructure**. The app will authenticate you via Google, verify that your account is the owner of the Backend folder, and complete the setup.

> **Note:** For the **Client Console**, each end user will need to authenticate with their own Google account when they activate the software. Because the OAuth app is in production, they only need to accept the unverified app warning – no manual email additions are required.

---

# 🔄 Synchronization Flow

```
Local Server World
        │
        ▼
Generate ZIP Backup
        │
        ▼
Calculate SHA256 Signature
        │
        ▼
Compare MD5 with Cloud Version
        │
        ▼
Upload if Changed (new revision)
        │
        ▼
Cloud Backup Updated
```

---

# 🔐 Activation & Registration Workflow

```
Admin (Master Manager)
        │
        ▼
Generate Activation String
        │
        ▼
User (Client) Pastes String
        │
        ▼
String Validated & Removed from Cloud
        │
        ▼
User Registers / Logs In
        │
        ▼
Auto‑Approved (if Public) or Pending (if Restricted)
        │
        ▼
Minecraft Dashboard
```

---

# 📖 Permission Modes

## 🌍 Public

- Anyone with the link can edit the server folder.
- Newly registered accounts are **automatically approved**.
- No admin interaction required for user access.

---

## 🔒 Restricted

- Only specifically approved users receive Google Drive write permissions.
- New accounts enter a **pending queue** until an admin approves them.
- Ideal for private, invite‑only servers.

---

# 💾 Backup System

MineCloud automatically:

- Compresses the server world
- Uploads to Google Drive
- Tracks cloud revisions (full history)
- Prevents duplicate uploads via MD5 comparison
- Verifies integrity with version files
- Supports instant rollback to any previous revision
- Downloads the latest backup automatically on version mismatch

The **Master Manager** can also create a portable encrypted backup of the entire configuration (keys, folder IDs, OAuth secret) for disaster recovery.

---

# 📈 Current Features

- ✅ Google Drive Cloud Storage
- ✅ Automatic World Backup & Sync
- ✅ One‑time Activation Strings
- ✅ User Authentication & Registration
- ✅ Permission Management (Public/Restricted)
- ✅ Audit Logging
- ✅ Backup Rollback (Revision History)
- ✅ Live Server Console
- ✅ Server Launcher with Executable Detection
- ✅ RAM Configuration for .bat Servers
- ✅ Session Management & Remember Me
- ✅ Encrypted Backend & Local Vault
- ✅ Admin Ownership Verification
- ✅ Portable Configuration Backup & Import
- ✅ Parallel Fast Download
- ✅ Auto/Manual Server Location Modes

---

# 🛣 Roadmap

- [ ] Automatic scheduled backups
- [ ] Real‑time synchronization
- [ ] Discord integration
- [ ] Multi‑server support
- [ ] Plugin management
- [ ] Server statistics dashboard
- [ ] Automatic update checker
- [ ] Web administration panel
- [ ] Linux support
- [ ] Docker deployment

---

# 🤝 Contributing

Contributions, suggestions, and feature requests are welcome.

Feel free to open an Issue or submit a Pull Request.

---

# 📄 License

This project is licensed under the MIT License.

---

<div align="center">

## ⭐ If you like MineCloud, consider giving the repository a star!

Built with ❤️ using Python, Google Drive API, and CustomTkinter.

</div>
