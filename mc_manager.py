# mc_manager.py – Smart Sync Edition (3-Folder Progressive Security Architecture)
# Version with pre-filled login, no auto-login, and safe logout.

import os
import json
import time
import zipfile
import subprocess
import threading
import gc
import hashlib
import base64
import io
from tkinter import filedialog, messagebox
import customtkinter as ctk
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from cryptography.fernet import Fernet

SCOPES = ['https://www.googleapis.com/auth/drive']
BACKUP_NAME = 'world_backup.zip'
CONFIG_FILE = 'config.json'
SESSION_FILE = 'session.json'
VERSION_FILE = 'sync_version.dat'
ACCOUNTS_NAME = 'accounts.json'
TOKENS_NAME = 'tokens.json'
AUDIT_LOG_NAME = 'audit_log.json'
FOLDER_SETTINGS_NAME = 'folder_settings.json'

CLIENT_KEY_SEED = b"MinecraftCloudSyncPro_InternalObfuscationStandardSeed_2026"

class UltimateMinecraftManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Process & Sync Flags ---
        self.process = None
        self.drive_service = None
        self.authenticated_user = None
        self.user_email = None
        self.allow_sync = False
        self.monitor_id = None
        self.current_state = "LOCKED"   # LOCKED, IDLE, SYNCING, RUNNING

        # --- Decrypted infrastructure ---
        self.fernet_key = None
        self.backend_folder_id = None
        self.server_folder_id = None
        self.client_config = None
        self.running_exec_is_bat = False

        # --- Window setup ---
        self.title("MineCloud - Client Console")
        self.geometry("700x800")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Main container ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=25, pady=25)

        # --- Header ---
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 15))
        self.title_label = ctk.CTkLabel(self.header_frame, text="MineCloud", font=("Segoe UI", 28, "bold"))
        self.title_label.pack(side="left")
        self.status_badge = ctk.CTkLabel(self.header_frame, text=" LOCKED ", font=("Segoe UI", 12, "bold"),
                                         fg_color="#7A1C1C", text_color="#FFFFFF", corner_radius=8)
        self.status_badge.pack(side="right", pady=10)

        # --- Configuration card ---
        self.config_card = ctk.CTkFrame(self.main_container, fg_color="#1E1E24", corner_radius=12,
                                        border_width=1, border_color="#2D2D34")
        self.config_card.pack(fill="x", pady=(0, 15))
        self.cfg_title = ctk.CTkLabel(self.config_card, text="System Configuration", font=("Segoe UI", 14, "bold"),
                                      text_color="#7FA8E0")
        self.cfg_title.grid(row=0, column=0, columnspan=4, padx=20, pady=(15, 10), sticky="w")

        # Client key row
        lbl_key = ctk.CTkLabel(self.config_card, text="Client Key File:", font=("Segoe UI", 12))
        lbl_key.grid(row=1, column=0, padx=(20, 10), pady=8, sticky="w")
        self.key_entry = ctk.CTkEntry(self.config_card, placeholder_text="Select client_access.key file...",
                                      fg_color="#141416", border_color="#333333", show="*")
        self.key_entry.grid(row=1, column=1, pady=8, sticky="ew")
        self.key_eye = ctk.CTkButton(self.config_card, text="👁", width=35, fg_color="#3A3A42",
                                     hover_color="#4F4F59", command=self.toggle_key_visibility)
        self.key_eye.grid(row=1, column=2, padx=(5, 2), pady=8, sticky="e")
        self.key_browse = ctk.CTkButton(self.config_card, text="•••", width=35, fg_color="#3A3A42",
                                        hover_color="#4F4F59", command=self.browse_client_key)
        self.key_browse.grid(row=1, column=3, padx=(2, 20), pady=8, sticky="e")

        # Server directory row
        self.setup_input_row("Server Folder:", 2, "dir_entry", "Select server root directory...", True, self.browse_directory)
        # Executable row
        self.setup_input_row("Executable File:", 3, "exec_entry", "Select server.jar or run.bat...", True, self.browse_executable)
        self.config_card.columnconfigure(1, weight=1)

        # --- Dynamic display frame ---
        self.dynamic_display_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.dynamic_display_frame.pack(fill="both", expand=True)

        # Load saved config
        self.load_saved_config()

        # Always show the auth UI (no auto-login)
        self.show_auth_ui()

    # ------------------------------------------------------------------------
    #   UI helpers
    # ------------------------------------------------------------------------
    def setup_input_row(self, label_text, row, entry_name, placeholder, has_btn=False, btn_cmd=None):
        lbl = ctk.CTkLabel(self.config_card, text=label_text, font=("Segoe UI", 12))
        lbl.grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
        entry = ctk.CTkEntry(self.config_card, placeholder_text=placeholder, fg_color="#141416", border_color="#333333")
        entry.grid(row=row, column=1, pady=8, sticky="ew")
        setattr(self, entry_name, entry)
        if has_btn:
            btn = ctk.CTkButton(self.config_card, text="•••", width=40, command=btn_cmd, fg_color="#3A3A42",
                                hover_color="#4F4F59")
            btn.grid(row=row, column=2, columnspan=2, padx=(5, 20), pady=8, sticky="e")
        else:
            entry.grid(row=row, column=1, columnspan=3, padx=(0, 20), pady=8, sticky="ew")

    def toggle_key_visibility(self):
        if self.key_entry.cget("show") == "*":
            self.key_entry.configure(show="")
        else:
            self.key_entry.configure(show="*")

    def browse_client_key(self):
        path = filedialog.askopenfilename(title="Select Client Access Key", filetypes=[("Client Key", "*.key")])
        if path:
            self.key_entry.delete(0, "end")
            self.key_entry.insert(0, os.path.normpath(path))
            self.save_current_config()
            # Re-show auth UI so credentials can be pre-filled if a session exists
            self.show_auth_ui()

    def browse_directory(self):
        path = filedialog.askdirectory(title="Select Server Directory")
        if path:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, os.path.normpath(path))
            self.save_current_config()

    def browse_executable(self):
        init_dir = self.dir_entry.get() or os.getcwd()
        path = filedialog.askopenfilename(title="Select Executable", initialdir=init_dir,
                                          filetypes=[("Server Core", "*.jar *.bat")])
        if path:
            self.exec_entry.delete(0, "end")
            self.exec_entry.insert(0, os.path.normpath(path))
            if not self.dir_entry.get():
                self.dir_entry.insert(0, os.path.normpath(os.path.dirname(path)))
            self.save_current_config()

    def load_saved_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f)
                    self.key_entry.insert(0, d.get('key_path', ''))
                    self.dir_entry.insert(0, d.get('server_dir', ''))
                    self.exec_entry.insert(0, d.get('exec_path', ''))
            except:
                pass

    def save_current_config(self):
        data = {
            'key_path': self.key_entry.get().strip(),
            'server_dir': self.dir_entry.get().strip(),
            'exec_path': self.exec_entry.get().strip()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    # ------------------------------------------------------------------------
    #   Crypto & Google Drive helpers
    # ------------------------------------------------------------------------
    def decrypt_client_key(self):
        key_path = self.key_entry.get().strip()
        if not key_path or not os.path.exists(key_path):
            return None
        try:
            with open(key_path, 'rb') as f:
                encrypted_bytes = f.read()
            hasher = hashlib.sha256(CLIENT_KEY_SEED)
            cipher = Fernet(base64.urlsafe_b64encode(hasher.digest()))
            decrypted = cipher.decrypt(encrypted_bytes)
            payload = json.loads(decrypted.decode('utf-8'))
            self.client_config = payload['client_config']
            self.backend_folder_id = payload['backend_folder_id']
            raw_key = payload['fernet_key']
            if isinstance(raw_key, str):
                raw_key = raw_key.encode('utf-8')
            self.fernet_key = Fernet(raw_key)
            return payload
        except Exception as e:
            messagebox.showerror("Key Error", f"Failed to load client_access.key: {e}")
            return None

    def authenticate_gdrive(self):
        try:
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.client_config:
                        return False
                    flow = InstalledAppFlow.from_client_config(self.client_config, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            self.drive_service = build('drive', 'v3', credentials=creds)
            return True
        except Exception:
            return False

    def encrypt_backend_data(self, data: dict) -> bytes:
        if not self.fernet_key:
            raise Exception("Fernet key not available")
        return self.fernet_key.encrypt(json.dumps(data, indent=4).encode('utf-8'))

    def decrypt_backend_data(self, encrypted_bytes: bytes) -> dict:
        if not self.fernet_key:
            raise Exception("Fernet key not available")
        return json.loads(self.fernet_key.decrypt(encrypted_bytes).decode('utf-8'))

    def pull_encrypted_file(self, filename, default_structure):
        if not self.drive_service or not self.backend_folder_id:
            return default_structure
        results = self.drive_service.files().list(
            q=f"'{self.backend_folder_id}' in parents and name='{filename}' and trashed = false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])
        if not files:
            self.push_encrypted_file(filename, default_structure)
            return default_structure
        file_id = files[0]['id']
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return self.decrypt_backend_data(fh.read())

    def push_encrypted_file(self, filename, data):
        if not self.drive_service or not self.backend_folder_id:
            return
        encrypted = self.encrypt_backend_data(data)
        media = MediaIoBaseUpload(io.BytesIO(encrypted), mimetype='application/octet-stream', resumable=True)
        results = self.drive_service.files().list(
            q=f"'{self.backend_folder_id}' in parents and name='{filename}' and trashed = false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])
        if files:
            self.drive_service.files().update(fileId=files[0]['id'], media_body=media).execute()
        else:
            file_metadata = {'name': filename, 'parents': [self.backend_folder_id]}
            self.drive_service.files().create(body=file_metadata, media_body=media).execute()

    def push_file_to_server_folder(self, filename, data_bytes):
        """Upload a raw (non-encrypted) file to the server's Google Drive folder.
        Creates or updates the file and returns the API response (containing md5Checksum)."""
        if not self.drive_service or not self.server_folder_id:
            self.log("Drive service or server folder not available.")
            return None
        try:
            media = MediaIoBaseUpload(io.BytesIO(data_bytes),
                                      mimetype='application/zip',
                                      resumable=True)
            results = self.drive_service.files().list(
                q=f"'{self.server_folder_id}' in parents and name='{filename}' and trashed = false",
                fields="files(id)"
            ).execute()
            files = results.get('files', [])
            if files:
                # Update existing file
                response = self.drive_service.files().update(
                    fileId=files[0]['id'],
                    media_body=media,
                    fields='id,md5Checksum,headRevisionId'
                ).execute()
            else:
                # Create new file
                file_metadata = {
                    'name': filename,
                    'parents': [self.server_folder_id]
                }
                response = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,md5Checksum,headRevisionId'
                ).execute()
            return response
        except Exception as e:
            self.log(f"Upload error: {e}")
            return None

    # ------------------------------------------------------------------------
    #   Session cache (with remember-me logic)
    # ------------------------------------------------------------------------
    def save_session(self, username, email, server_folder_id, remember_me=True):
        """Only save session if remember_me is True."""
        if not self.fernet_key or not remember_me:
            return
        session_data = {
            'username': username,
            'email': email,
            'server_folder_id': server_folder_id,
            'created': time.time()
        }
        encrypted = self.fernet_key.encrypt(json.dumps(session_data).encode('utf-8'))
        with open(SESSION_FILE, 'wb') as f:
            f.write(encrypted)

    def load_session(self):
        if not os.path.exists(SESSION_FILE) or not self.fernet_key:
            return None
        try:
            with open(SESSION_FILE, 'rb') as f:
                encrypted = f.read()
            data = json.loads(self.fernet_key.decrypt(encrypted).decode('utf-8'))
            return data
        except:
            return None

    def delete_session(self):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    # ------------------------------------------------------------------------
    #   Authentication UI (with Remember Me and pre-filled credentials)
    # ------------------------------------------------------------------------
    def show_auth_ui(self):
        for widget in self.dynamic_display_frame.winfo_children():
            widget.destroy()
        self.current_state = "LOCKED"
        self.status_badge.configure(text=" LOCKED ", fg_color="#7A1C1C", text_color="#FFFFFF")

        self.auth_tabview = ctk.CTkTabview(self.dynamic_display_frame, fg_color="#141416",
                                           border_width=1, border_color="#2D2D34")
        self.auth_tabview.pack(fill="both", expand=True)

        tab_login = self.auth_tabview.add("🔐 Sign In")
        tab_register = self.auth_tabview.add("🎟️ Register")

        # --- Login ---
        ctk.CTkLabel(tab_login, text="Username or Email:", font=("Segoe UI", 12)).pack(anchor="w", padx=30, pady=(25, 2))
        self.login_user = ctk.CTkEntry(tab_login, placeholder_text="Enter your username or email...",
                                       fg_color="#1E1E24", height=35)
        self.login_user.pack(fill="x", padx=30, pady=(0, 15))
        ctk.CTkLabel(tab_login, text="Password:", font=("Segoe UI", 12)).pack(anchor="w", padx=30, pady=(0, 2))
        self.login_pass = ctk.CTkEntry(tab_login, placeholder_text="Enter your password...",
                                       fg_color="#1E1E24", show="*", height=35)
        self.login_pass.pack(fill="x", padx=30, pady=(0, 10))
        # Remember Me checkbox
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_cb = ctk.CTkCheckBox(tab_login, text="Remember Me", variable=self.remember_var,
                                           fg_color="#2EA44F")
        self.remember_cb.pack(anchor="w", padx=30, pady=(0, 15))
        self.login_btn = ctk.CTkButton(tab_login, text="🔐 SIGN IN", font=("Segoe UI", 13, "bold"),
                                       height=40, command=self.execute_login)
        self.login_btn.pack(fill="x", padx=30)

        # --- Register ---
        ctk.CTkLabel(tab_register, text="Invitation Token:", font=("Segoe UI", 12)).pack(anchor="w", padx=30, pady=(20, 2))
        self.reg_token = ctk.CTkEntry(tab_register, placeholder_text="Paste token (MC-XXXXXXXX)...",
                                      fg_color="#1E1E24", height=35)
        self.reg_token.pack(fill="x", padx=30, pady=(0, 12))
        ctk.CTkLabel(tab_register, text="Choose Username:", font=("Segoe UI", 12)).pack(anchor="w", padx=30, pady=(0, 2))
        self.reg_user = ctk.CTkEntry(tab_register, placeholder_text="Create a username...",
                                     fg_color="#1E1E24", height=35)
        self.reg_user.pack(fill="x", padx=30, pady=(0, 12))
        ctk.CTkLabel(tab_register, text="Email Address:", font=("Segoe UI", 12)).pack(anchor="w", padx=30, pady=(0, 2))
        self.reg_email = ctk.CTkEntry(tab_register, placeholder_text="Your Gmail address (required)...",
                                      fg_color="#1E1E24", height=35)
        self.reg_email.pack(fill="x", padx=30, pady=(0, 12))
        ctk.CTkLabel(tab_register, text="Set Password:", font=("Segoe UI", 12)).pack(anchor="w", padx=30, pady=(0, 2))
        self.reg_pass = ctk.CTkEntry(tab_register, placeholder_text="Create a strong password...",
                                     fg_color="#1E1E24", show="*", height=35)
        self.reg_pass.pack(fill="x", padx=30, pady=(0, 25))
        self.register_btn = ctk.CTkButton(tab_register, text="✨ REGISTER", font=("Segoe UI", 13, "bold"),
                                          fg_color="#2EA44F", hover_color="#22863A", height=40,
                                          command=self.execute_registration)
        self.register_btn.pack(fill="x", padx=30)

        # Pre-fill remembered username/email if a session exists
        self.prefill_remembered_credentials()

    def prefill_remembered_credentials(self):
        """If a saved session exists, fill the login username field and check Remember Me."""
        if not self.fernet_key:
            # Try to decrypt the key first
            self.decrypt_client_key()
        if not self.fernet_key:
            return
        session = self.load_session()
        if session:
            username = session.get('username', '')
            email = session.get('email', '')
            # Prefer username, fallback to email
            self.login_user.delete(0, 'end')
            self.login_user.insert(0, username if username else email)
            self.remember_var.set(True)

    # ------------------------------------------------------------------------
    #   Two‑step login: existence check then password verification
    # ------------------------------------------------------------------------
    def execute_login(self):
        if not self.decrypt_client_key():
            messagebox.showerror("Error", "Please select a valid client_access.key file first.")
            return
        username_or_email = self.login_user.get().strip()
        password = self.login_pass.get().strip()
        if not username_or_email or not password:
            messagebox.showwarning("Missing Fields", "Enter both username/email and password.")
            return
        self.login_btn.configure(text="⏳ Signing in...", state="disabled")
        threading.Thread(target=self._bg_login, args=(username_or_email, password), daemon=True).start()

    def _bg_login(self, username_or_email, password):
        try:
            if not self.authenticate_gdrive():
                self.after(0, lambda: messagebox.showerror("Auth Error",
                                                           "Google authentication failed. Check your internet connection and try again."))
                self.after(0, lambda: self.login_btn.configure(text="🔐 SIGN IN", state="normal"))
                return

            accounts = self.pull_encrypted_file(ACCOUNTS_NAME, {"users": {}, "server_folder_id": ""})
            users = accounts.get('users', {})
            # 1) Check existence
            matched_user = None
            for uname, info in users.items():
                if uname == username_or_email or info.get('email') == username_or_email:
                    matched_user = uname
                    break
            if not matched_user:
                self.after(0, lambda: messagebox.showerror("User Not Found",
                                                           "No account matches that username or email."))
                self.after(0, lambda: self.login_btn.configure(text="🔐 SIGN IN", state="normal"))
                return

            user_info = users[matched_user]
            # 2) Check approval status
            if user_info.get('status') != 'approved':
                self.after(0, lambda: messagebox.showinfo("Pending Approval",
                                                          "Your account is still awaiting admin approval."))
                self.after(0, lambda: self.login_btn.configure(text="🔐 SIGN IN", state="normal"))
                return

            # 3) Now verify password
            hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if user_info.get('password') != hashed:
                self.after(0, lambda: messagebox.showerror("Wrong Password",
                                                           "The password you entered is incorrect."))
                self.after(0, lambda: self.login_btn.configure(text="🔐 SIGN IN", state="normal"))
                return

            self.server_folder_id = accounts.get('server_folder_id')
            if not self.server_folder_id:
                self.after(0, lambda: messagebox.showerror("Config Error", "Server folder ID missing in backend."))
                self.after(0, lambda: self.login_btn.configure(text="🔐 SIGN IN", state="normal"))
                return

            self.authenticated_user = matched_user
            self.user_email = user_info.get('email', '')

            # --- FIX: Remember Me logic ---
            remember = self.remember_var.get()
            if not remember:
                # If user unchecked "Remember Me", clear any previously saved session
                self.delete_session()
            else:
                # Save session only if checkbox was checked
                self.save_session(matched_user, self.user_email, self.server_folder_id, remember_me=True)

            self.after(0, lambda: self.unlock_operational_dashboard())
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Login Error", f"Could not connect to server: {e}"))
            self.after(0, lambda: self.login_btn.configure(text="🔐 SIGN IN", state="normal"))

    # ------------------------------------------------------------------------
    #   Registration logic (unchanged except for auto-login remember flag)
    # ------------------------------------------------------------------------
    def execute_registration(self):
        if not self.decrypt_client_key():
            messagebox.showerror("Error", "Please select a valid client_access.key file first.")
            return
        token = self.reg_token.get().strip()
        username = self.reg_user.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_pass.get().strip()

        if not token or not username or not email or not password:
            messagebox.showwarning("Missing Fields", "All fields are required.")
            return
        if "@" not in email or "." not in email:
            messagebox.showwarning("Invalid Email", "Provide a valid email address.")
            return

        self.register_btn.configure(text="⏳ Registering...", state="disabled")
        threading.Thread(target=self._bg_register, args=(token, username, email, password), daemon=True).start()

    def _bg_register(self, token, username, email, password):
        try:
            if not self.authenticate_gdrive():
                self.after(0, lambda: messagebox.showerror("Auth Error", "Google authentication failed."))
                self.after(0, lambda: self.register_btn.configure(text="✨ REGISTER", state="normal"))
                return

            folder_settings = self.pull_encrypted_file(FOLDER_SETTINGS_NAME, {"mode": "public"})
            mode = folder_settings.get("mode", "public")
            status = "approved" if mode == "public" else "pending"

            tokens = self.pull_encrypted_file(TOKENS_NAME, {"tokens": [], "used_tokens": []})
            if token not in tokens.get('tokens', []):
                self.after(0, lambda: messagebox.showerror("Invalid Token", "The token is invalid or already used."))
                self.after(0, lambda: self.register_btn.configure(text="✨ REGISTER", state="normal"))
                return

            accounts = self.pull_encrypted_file(ACCOUNTS_NAME, {"users": {}, "server_folder_id": ""})
            if username in accounts.get('users', {}):
                self.after(0, lambda: messagebox.showerror("Username Taken", "That username already exists."))
                self.after(0, lambda: self.register_btn.configure(text="✨ REGISTER", state="normal"))
                return

            tokens['tokens'].remove(token)
            tokens.setdefault('used_tokens', []).append(token)
            accounts['users'][username] = {
                "password": hashlib.sha256(password.encode('utf-8')).hexdigest(),
                "email": email,
                "status": status,
                "registered_at": time.time()
            }

            self.push_encrypted_file(TOKENS_NAME, tokens)
            self.push_encrypted_file(ACCOUNTS_NAME, accounts)

            if status == "approved":
                self.server_folder_id = accounts.get('server_folder_id')
                self.authenticated_user = username
                self.user_email = email
                # Registration always saves a session (assumed remember me)
                self.save_session(username, email, self.server_folder_id, remember_me=True)
                self.after(0, lambda: messagebox.showinfo("Registration Successful",
                                                          "Account created and approved! You are now logged in."))
                self.after(0, lambda: self.unlock_operational_dashboard())
            else:
                self.after(0, lambda: messagebox.showinfo("Registration Successful",
                                                          "Your account has been created and is awaiting admin approval."))
                self.after(0, lambda: self.register_btn.configure(text="✨ REGISTER", state="normal"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Registration Error", f"Could not complete registration: {e}"))
            self.after(0, lambda: self.register_btn.configure(text="✨ REGISTER", state="normal"))

    # ------------------------------------------------------------------------
    #   Operational dashboard (with Logout button)
    # ------------------------------------------------------------------------
    def unlock_operational_dashboard(self):
        for widget in self.dynamic_display_frame.winfo_children():
            widget.destroy()
        self.allow_sync = False
        self.set_app_state("IDLE")

        # Log display
        self.log_card = ctk.CTkFrame(self.dynamic_display_frame, fg_color="#141416", corner_radius=12,
                                     border_width=1, border_color="#2D2D34")
        self.log_card.pack(fill="both", expand=True, pady=(0, 15))
        self.log_textbox = ctk.CTkTextbox(self.log_card, font=("Consolas", 12), fg_color="transparent",
                                          text_color="#CCCCCC", border_width=0)
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=15)
        self.log_textbox.configure(state="disabled")

        self.progress_bar = ctk.CTkProgressBar(self.log_card, height=4, progress_color="#4CAF50", fg_color="#1E1E24")
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 15))
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()

        # Console input
        self.console_frame = ctk.CTkFrame(self.dynamic_display_frame, fg_color="transparent")
        self.console_frame.pack(fill="x", pady=(10, 10), padx=2)
        self.console_entry = ctk.CTkEntry(self.console_frame, placeholder_text="Type server command...",
                                          fg_color="#141416", height=32)
        self.console_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.console_entry.bind("<Return>", lambda e: self.send_console_input())
        self.console_send_btn = ctk.CTkButton(self.console_frame, text="Send", width=80, height=32,
                                              command=self.send_console_input)
        self.console_send_btn.pack(side="right")
        self.console_entry.configure(state="disabled")
        self.console_send_btn.configure(state="disabled")

        # Action bar (Start/Sync)
        self.action_bar = ctk.CTkFrame(self.dynamic_display_frame, fg_color="transparent")
        self.action_bar.pack(fill="x", pady=(0, 0))
        self.toggle_server_btn = ctk.CTkButton(self.action_bar, text="▶ START SERVER", font=("Segoe UI", 14, "bold"),
                                               height=50, command=self.toggle_server_action, fg_color="#2EA44F",
                                               hover_color="#22863A")
        self.toggle_server_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.sync_btn = ctk.CTkButton(self.action_bar, text="🔄 SYNC SERVER", font=("Segoe UI", 14, "bold"),
                                      height=50, command=self.sync_to_cloud, fg_color="#3A3A42",
                                      hover_color="#4F4F59", state="disabled")
        self.sync_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Logout button in header area
        self.logout_btn = ctk.CTkButton(self.header_frame, text="🚪 Logout", font=("Segoe UI", 11),
                                        fg_color="#D32F2F", hover_color="#B71C1C", width=80,
                                        command=self.perform_logout)
        self.logout_btn.pack(side="right", padx=(10, 0), pady=10)
        # Repack status badge to maintain order
        self.status_badge.pack_forget()
        self.status_badge.pack(side="right", pady=10)

        self.log(f"Welcome, {self.authenticated_user}. System ready.")

    def perform_logout(self):
        """Logout is only allowed when the app is completely idle (no server running, no sync in progress)."""
        if self.current_state != "IDLE":
            if self.current_state == "RUNNING":
                msg = "Cannot log out while the server is running.\nPlease stop the server first."
            else:
                msg = "Cannot log out while an operation is in progress.\nPlease wait until it finishes."
            messagebox.showwarning("Action Blocked", msg)
            return

        # --- FIX: Do not delete the session file on logout ---
        # Previously, this line removed the saved username, breaking "Remember Me".
        # We now preserve it so the username is still pre-filled on next launch.
        # self.delete_session()  # <-- REMOVED

        self.authenticated_user = None
        self.user_email = None
        self.allow_sync = False
        # Remove logout button from header
        if hasattr(self, 'logout_btn'):
            self.logout_btn.pack_forget()
            self.logout_btn.destroy()
        self.show_auth_ui()

    # --- Thread-safe UI state updates ---
    def set_app_state(self, state):
        self.after(0, lambda: self._unsafe_set_app_state(state))

    def _unsafe_set_app_state(self, state):
        self.current_state = state   # track state for logout guard
        if state == "SYNCING":
            self.status_badge.configure(text=" SYNCING CLOUD ", fg_color="#FF9800", text_color="#000000")
            self.progress_bar.pack(fill="x", padx=15, pady=(0, 15))
            self.progress_bar.start()
            self.toggle_server_btn.configure(state="disabled")
            self.sync_btn.configure(state="disabled")
        elif state == "RUNNING":
            self.status_badge.configure(text=" SERVER ONLINE ", fg_color="#4CAF50", text_color="#FFFFFF")
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.toggle_server_btn.configure(text="■ STOP SERVER", fg_color="#D32F2F", hover_color="#B71C1C",
                                             state="normal")
            self.sync_btn.configure(state="disabled")
            try:
                self.console_entry.configure(state="normal")
                self.console_send_btn.configure(state="normal")
                self.console_entry.focus_set()
            except:
                pass
        elif state == "IDLE":
            self.status_badge.configure(text=f" ACTIVE: {self.authenticated_user} ", fg_color="#1F538D",
                                        text_color="#FFFFFF")
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.toggle_server_btn.configure(text="▶ START SERVER", fg_color="#2EA44F", hover_color="#22863A",
                                             state="normal")
            try:
                self.console_entry.delete(0, 'end')
                self.console_entry.configure(state="disabled")
                self.console_send_btn.configure(state="disabled")
            except:
                pass
            if self.allow_sync:
                self.sync_btn.configure(state="normal")
            else:
                self.sync_btn.configure(state="disabled")

    def log(self, message, is_server=False):
        self.after(0, lambda: self._unsafe_log(message, is_server))

    def _unsafe_log(self, message, is_server=False):
        prefix = "[SERVER] " if is_server else "[SYSTEM] "
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{prefix}{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    # ------------------------------------------------------------------------
    #   Sync utilities
    # ------------------------------------------------------------------------
    def safe_delete_zip(self, filepath):
        gc.collect()
        for _ in range(10):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return True
            except PermissionError:
                time.sleep(0.5)
        return False

    def get_local_sync_signature(self, server_dir):
        hasher = hashlib.sha256()
        for root, dirs, files in os.walk(server_dir):
            dirs[:] = sorted(d for d in dirs if d != 'logs')
            files = sorted(f for f in files if f not in [BACKUP_NAME, VERSION_FILE, 'session.lock'])
            for file_name in files:
                file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(file_path, server_dir).replace(os.sep, '/')
                hasher.update(rel_path.encode('utf-8'))
                try:
                    with open(file_path, 'rb') as handle:
                        while True:
                            chunk = handle.read(1024 * 1024)
                            if not chunk:
                                break
                            hasher.update(chunk)
                except OSError:
                    hasher.update(b'<unreadable>')
        return hasher.hexdigest()

    def read_sync_state(self, version_path):
        if not os.path.exists(version_path):
            return {'remote_md5': '', 'local_state': ''}
        try:
            with open(version_path, 'r', encoding='utf-8') as handle:
                raw = handle.read().strip()
            if not raw:
                return {'remote_md5': '', 'local_state': ''}
            if raw.startswith('{'):
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return {'remote_md5': parsed.get('remote_md5', ''), 'local_state': parsed.get('local_state', '')}
            return {'remote_md5': raw, 'local_state': ''}
        except Exception:
            return {'remote_md5': '', 'local_state': ''}

    def write_sync_state(self, version_path, remote_md5, local_state):
        with open(version_path, 'w', encoding='utf-8') as handle:
            json.dump({'remote_md5': remote_md5, 'local_state': local_state}, handle)

    def download_from_drive(self):
        if not self.server_folder_id:
            self.log("Server folder not configured.")
            return
        server_dir = self.dir_entry.get().strip()
        self.log("Checking cloud for latest world backup...")
        results = self.drive_service.files().list(
            q=f"'{self.server_folder_id}' in parents and name='{BACKUP_NAME}' and trashed = false",
            fields="files(id, name, md5Checksum)",
            orderBy="modifiedTime desc"
        ).execute()
        files = results.get('files', [])
        if not files:
            self.log("No remote backup found.")
            return

        remote_file = files[0]
        remote_id = remote_file['id']
        remote_md5 = remote_file.get('md5Checksum', 'UNKNOWN_REMOTE')

        local_version_path = os.path.join(server_dir, VERSION_FILE)
        current_local_state = self.get_local_sync_signature(server_dir)
        sync_state = self.read_sync_state(local_version_path)
        stored_remote_md5 = sync_state.get('remote_md5', '')
        stored_local_state = sync_state.get('local_state', '')

        if remote_md5 != 'UNKNOWN_REMOTE' and stored_remote_md5 == remote_md5 and stored_local_state == current_local_state:
            self.log(f"⚡ Smart Sync Match: Local files match cloud ({remote_md5[:8]}). Skipping download.")
            return

        self.log("Downloading cloud backup...")
        local_zip = os.path.join(server_dir, BACKUP_NAME)
        request = self.drive_service.files().get_media(fileId=remote_id)
        with open(local_zip, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        self.log("Extracting backup...")
        with zipfile.ZipFile(local_zip, 'r') as zip_ref:
            zip_ref.extractall(server_dir)

        self.safe_delete_zip(local_zip)
        post_download_state = self.get_local_sync_signature(server_dir)
        self.write_sync_state(local_version_path, remote_md5, post_download_state)
        self.log("Sync complete.")

    def upload_to_drive(self):
        server_dir = self.dir_entry.get().strip()
        if not server_dir or not self.server_folder_id:
            return
        local_version_path = os.path.join(server_dir, VERSION_FILE)
        self.log("Creating backup archive...")
        local_zip = os.path.join(server_dir, BACKUP_NAME)

        with zipfile.ZipFile(local_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(server_dir):
                for file in files:
                    if file in [BACKUP_NAME, VERSION_FILE, 'session.lock'] or 'logs' in root:
                        continue
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), server_dir))

        try:
            with open(local_zip, 'rb') as fh:
                zip_bytes = fh.read()
        except Exception as e:
            self.log(f"Failed to read backup: {e}")
            return

        self.log("Uploading to cloud...")
        uploaded = self.push_file_to_server_folder(BACKUP_NAME, zip_bytes)
        if uploaded:
            new_md5 = uploaded.get('md5Checksum', '')
            new_rev = uploaded.get('headRevisionId')
            current_local_state = self.get_local_sync_signature(server_dir)
            self.write_sync_state(local_version_path, new_md5, current_local_state)
            self._append_audit(f"Uploaded world backup (MD5: {new_md5[:8]})", revision_id=new_rev)
            self.log(f"✅ Upload successful (MD5: {new_md5[:8]}).")
        else:
            self.log("Upload failed.")
        self.safe_delete_zip(local_zip)

    def _append_audit(self, action, revision_id=None):
        try:
            if not self.drive_service or not self.backend_folder_id:
                return
            results = self.drive_service.files().list(
                q=f"'{self.backend_folder_id}' in parents and name='{AUDIT_LOG_NAME}' and trashed = false",
                fields="files(id)"
            ).execute()
            files = results.get('files', [])
            if files:
                file_id = files[0]['id']
                request = self.drive_service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                fh.seek(0)
                audit = json.loads(fh.read().decode('utf-8'))
            else:
                audit = []
            record = {
                "username": self.authenticated_user,
                "action": action,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + " UTC"
            }
            if revision_id:
                record["revision_id"] = revision_id
            audit.append(record)
            json_data = json.dumps(audit, indent=4).encode('utf-8')
            media = MediaIoBaseUpload(io.BytesIO(json_data), mimetype='application/json', resumable=True)
            if files:
                self.drive_service.files().update(fileId=file_id, media_body=media).execute()
            else:
                file_metadata = {'name': AUDIT_LOG_NAME, 'parents': [self.backend_folder_id]}
                self.drive_service.files().create(body=file_metadata, media_body=media).execute()
        except Exception:
            pass

    # ------------------------------------------------------------------------
    #   Server process management (unified launcher)
    # ------------------------------------------------------------------------
    def start_process_monitor(self):
        if self.monitor_id:
            self.after_cancel(self.monitor_id)
        self._monitor_process()

    def _monitor_process(self):
        if self.process and self.process.poll() is not None:
            self.process = None
            self.allow_sync = True
            self.set_app_state("IDLE")
            self.log("Server stopped. You can now sync.")
            self.monitor_id = None
            return
        self.monitor_id = self.after(500, self._monitor_process)

    def cancel_monitor(self):
        if self.monitor_id:
            self.after_cancel(self.monitor_id)
            self.monitor_id = None

    def on_server_exited(self):
        self.cancel_monitor()
        if self.process is not None:
            self.process = None
            self.allow_sync = True
            self.set_app_state("IDLE")
            self.log("Server stopped. You can now sync.")

    def stream_console_logs(self):
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if not line:
                break
            try:
                decoded = line.decode('utf-8', errors='ignore').strip()
                if decoded:
                    self.log(decoded, is_server=True)
                    lower_decoded = decoded.lower()
                    if "press any key" in lower_decoded:
                        self.log("⚡ Auto-bypassing batch pause...")
                        try:
                            self.process.stdin.write(b"\r\n")
                            self.process.stdin.flush()
                        except:
                            pass
                    if self.running_exec_is_bat and any(term in lower_decoded for term in
                                                        ("server closing", "closing server", "server closed")):
                        self.log("Server Closed")
                        self.after(0, self._bat_shutdown_detected)
            except:
                pass

    def stop_server(self):
        if self.process and self.process.poll() is None:
            self.log("Stopping server...")
            try:
                self.process.stdin.write(b"stop\r\n")
                self.process.stdin.flush()
            except Exception as e:
                self.log(f"Failed to send stop command: {e}")

    def _bat_shutdown_detected(self):
        """Called when a batch file indicates the server is closed.
        Sends a newline to bypass any 'Press any key' pause, then forces cleanup."""
        if self.process and self.process.poll() is None:
            # Send newline to let the batch exit gracefully
            try:
                self.process.stdin.write(b"\r\n")
                self.process.stdin.flush()
            except:
                pass
            # Schedule a forced cleanup in case the process still hangs
            self.after(1000, self._force_cleanup_process)
        else:
            self._force_cleanup_process()

    def _force_cleanup_process(self):
        """Kill the process if still alive, then reset state completely."""
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except:
                pass
        self.process = None
        self.allow_sync = True
        self.set_app_state("IDLE")
        self.log("Server stopped. You can now sync.")

    def toggle_server_action(self):
        if self.process and self.process.poll() is None:
            self.stop_server()
        else:
            self.start_process_monitor()
            threading.Thread(target=self.run_server_pipeline, daemon=True).start()

    def sync_to_cloud(self):
        server_dir = self.dir_entry.get().strip()
        if not server_dir:
            messagebox.showwarning("Missing Config", "Select a server directory first.")
            return
        self.sync_btn.configure(state="disabled")
        threading.Thread(target=self._bg_sync, daemon=True).start()

    def _bg_sync(self):
        self.set_app_state("SYNCING")
        try:
            self.upload_to_drive()
            self.allow_sync = False
        except Exception as e:
            self.log(f"Sync failed: {e}")
        finally:
            self.set_app_state("IDLE")

    def send_console_input(self, event=None):
        text = self.console_entry.get().strip()
        if not text:
            return
        self.log(f"> {text}")
        if self.process and self.process.poll() is None:
            try:
                payload = (text + "\r\n").encode('utf-8')
                self.process.stdin.write(payload)
                self.process.stdin.flush()
            except Exception as e:
                self.log(f"Failed to send command: {e}")
        else:
            self.log("No active server.")
        try:
            self.console_entry.delete(0, 'end')
            self.console_entry.focus_set()
        except:
            pass

    def run_server_pipeline(self):
        server_dir = self.dir_entry.get().strip()
        exec_path = self.exec_entry.get().strip()
        if not server_dir:
            self.log("Server directory not set.")
            self.cancel_monitor()
            self.set_app_state("IDLE")
            return
        self.save_current_config()
        self.set_app_state("SYNCING")
        try:
            self.download_from_drive()
            if not exec_path:
                self.log("No executable selected. Set it and restart.")
                self.cancel_monitor()
                self.set_app_state("IDLE")
                return

            self.running_exec_is_bat = exec_path.lower().endswith('.bat')
            self.set_app_state("RUNNING")
            current_env = os.environ.copy()

            # Unified launcher: always use the executable as provided
            self.process = subprocess.Popen(
                f'"{exec_path}"',
                cwd=server_dir,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=current_env
            )
            threading.Thread(target=self.stream_console_logs, daemon=True).start()
            self.process.wait()
        except Exception as e:
            self.log(f"Pipeline error: {e}")
        finally:
            self.after(0, self.on_server_exited)

    def on_closing(self):
        # Allow closing if not busy
        if self.current_state in ("LOCKED", "IDLE"):
            self.destroy()
        else:
            if self.current_state == "RUNNING":
                msg = "A server is still running.\nPlease stop the server before closing."
            else:
                msg = "An operation is in progress.\nPlease wait until it finishes before closing."
            messagebox.showwarning("Cannot Close", msg)

if __name__ == "__main__":
    app = UltimateMinecraftManager()
    app.mainloop()