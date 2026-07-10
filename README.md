<div align="center">

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

- AES-grade Fernet encryption
- Encrypted backend database
- Secure Google OAuth authentication
- Password hashing
- Invitation-only registration
- User approval system
- Session encryption
- Cloud permission management
- Audit logging

---

## ☁️ Cloud Infrastructure

- Google Drive integration
- Automatic cloud synchronization
- Incremental world backups
- Backup verification
- Backup rollback
- Cloud revision history
- Automatic upload/download
- Synchronization state tracking

---

## 👥 User Management

- Invitation token system
- User registration
- Login system
- Remember Me
- Pending approval queue
- Bulk user approval
- Bulk revoke
- User search
- User sorting
- Email permissions

---

## 🎮 Minecraft Management

- Launch server
- Stop server
- Send console commands
- Live server console
- Server state monitoring
- Automatic backup generation
- Cloud sync
- Synchronized multiplayer deployments

---

## ⚙️ Administration

- Infrastructure setup wizard
- Folder permission manager
- Public / Restricted server modes
- Automatic permission migration
- Client key generation
- Backend reset
- Audit history
- Revision rollback

---

# 🏗 Architecture

```
                         Google Drive

            ┌────────────────────────────┐
            │      Backend Folder        │
            │────────────────────────────│
            │ accounts.json              │
            │ tokens.json                │
            │ folder_settings.json       │
            │ audit_log.json             │
            └─────────────┬──────────────┘
                          │
                  Encrypted JSON
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
 Master Manager                      Minecraft Client
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

# 📂 Project Structure

```
MineCloud/
│
├── master_manager.py          # Administrator Console
├── mc_manager.py              # Minecraft Client Console
│
├── client_access.key
├── config.json
├── session.json
├── token.json
│
├── world_backup.zip
├── sync_version.dat
│
└── README.md
```

---

# 🖥 Screens

## Master Manager

✔ Infrastructure Configuration

✔ Google Drive Authentication

✔ Token Generation

✔ User Management

✔ Folder Permissions

✔ Rollback Manager

✔ Client Key Export

---

## Client Console

✔ Login

✔ Registration

✔ Remember Me

✔ Server Control

✔ Live Console

✔ Cloud Synchronization

✔ Backup Manager

---

# 🔑 Backend Files

All backend files are encrypted using Fernet encryption.

| File | Purpose |
|------|----------|
| accounts.json | Registered users |
| tokens.json | Invitation tokens |
| folder_settings.json | Permission mode |
| audit_log.json | Administrative logs |

---

# 🛡 Security

MineCloud uses a layered security model.

- Google OAuth Authentication
- Fernet Encryption
- SHA-256 Password Hashing
- Invitation Tokens
- User Approval Workflow
- Google Drive Permission API
- Encrypted Sessions
- Audit Logging

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
- gc
- time

---

# 📦 Installation

## Clone the repository

```bash
git clone https://github.com/yourusername/MineCloud.git

cd MineCloud
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

or

```bash
pip install customtkinter

pip install google-api-python-client

pip install google-auth

pip install google-auth-oauthlib

pip install cryptography
```

---

# 🔧 Google Cloud Setup

1. Create a Google Cloud Project

2. Enable

- Google Drive API

3. Create OAuth Desktop Credentials

4. Download

```
client_secret.json
```

5. Configure the Master Manager

6. Select

- Backend Folder
- Server Folder
- OAuth Client Secret

7. Initialize Infrastructure

---

# 🚀 Running

## Administrator

```bash
python master_manager.py
```

---

## Client

```bash
python mc_manager.py
```

---

# 🔄 Synchronization Flow

```
Local Server

      │

      ▼

Generate Backup

      │

      ▼

Calculate SHA256 Signature

      │

      ▼

Compare MD5

      │

      ▼

Upload if Changed

      │

      ▼

Store Revision

      │

      ▼

Cloud Backup Updated
```

---

# 🔐 Registration Workflow

```
Admin

↓

Generate Invitation Token

↓

User Registers

↓

Token Validation

↓

Create Account

↓

Pending / Approved

↓

Login

↓

Minecraft Dashboard
```

---

# 📖 Permission Modes

## 🌍 Public

Anyone with the link can access the server folder.

Accounts are automatically approved.

---

## 🔒 Restricted

Only approved users receive Google Drive permissions.

Accounts require administrator approval.

---

# 💾 Backup System

MineCloud automatically

- Compresses the server
- Uploads backups
- Tracks cloud revisions
- Prevents duplicate uploads
- Verifies integrity
- Supports rollback
- Downloads latest backup automatically

---

# 📈 Current Features

- ✅ Google Drive Cloud Storage
- ✅ Automatic World Backup
- ✅ Cloud Synchronization
- ✅ User Authentication
- ✅ Registration Tokens
- ✅ Permission Management
- ✅ Audit Logging
- ✅ Backup Rollback
- ✅ Live Server Console
- ✅ Server Launcher
- ✅ Session Management
- ✅ Remember Me
- ✅ Folder Permission Control
- ✅ Encrypted Backend
- ✅ Client Key Distribution

---

# 🛣 Roadmap

- [ ] Automatic scheduled backups
- [ ] Real-time synchronization
- [ ] Discord integration
- [ ] Multi-server support
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
