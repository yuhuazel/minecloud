# master_manager.py – Smart Sync Edition (3-Folder Progressive Security Architecture)
# Fixed: deterministic Fernet key derived from backend folder ID,
#        added cloud_pull_json, auto-reset on encryption mismatch,
#        corrected all refresh methods, guaranteed operational backup & user data.
import os
import json
import time
import random
import string
import hashlib
import base64
import io
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from cryptography.fernet import Fernet, InvalidToken

SCOPES = ['https://www.googleapis.com/auth/drive']
MASTER_CONFIG = 'master_config.json'
BACKUP_NAME = 'world_backup.zip'
TOKENS_NAME = 'tokens.json'
ACCOUNTS_NAME = 'accounts.json'
AUDIT_LOG_NAME = 'audit_log.json'
FOLDER_SETTINGS_NAME = 'folder_settings.json'
CLIENT_KEY_SEED = b"MinecraftCloudSyncPro_InternalObfuscationStandardSeed_2026"

# ------------------------------------------------------------------------
#   Deterministic key derivation – same key for same backend folder ID
# ------------------------------------------------------------------------
def derive_fernet_key(backend_folder_id: str) -> bytes:
    """Creates a reproducible Fernet key from the backend folder ID."""
    material = CLIENT_KEY_SEED + backend_folder_id.encode('utf-8')
    digest = hashlib.sha256(material).digest()
    return base64.urlsafe_b64encode(digest)

class MasterManagerConsole(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.drive_service = None
        self.backend_folder_id = ""
        self.server_folder_id = ""
        self.client_secret_path = ""
        self.fernet_key_bytes = None
        self.fernet_cipher = None
        self.server_permission_mode = "public"
        self.revision_map = {}

        self.all_users = {}
        self.filtered_users_list = []

        self.title("MineCloud – Master Manager Console")
        self.geometry("960x800")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.tabs = ctk.CTkTabview(self, fg_color="#141416", border_width=1, border_color="#2D2D34")
        self.tabs.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_setup = self.tabs.add("⚙️ Cloud Setup")
        self.tab_tokens = self.tabs.add("🎟️ Token Keys")
        self.tab_users = self.tabs.add("👥 User Profiles")
        self.tab_settings = self.tabs.add("⚙️ Folder Settings")
        self.tab_rollback = self.tabs.add("⏪ Rollback")
        self.tab_export = self.tabs.add("🔑 Export Client Key")

        self.build_setup_tab()
        self.build_tokens_tab()
        self.build_users_tab()
        self.build_settings_tab()
        self.build_rollback_tab()
        self.build_export_tab()

        self.load_local_master_config()

    # ------------------------------------------------------------------------
    #   Cloud Setup tab
    # ------------------------------------------------------------------------
    def build_setup_tab(self):
        frame = self.tab_setup
        ctk.CTkLabel(frame, text="Infrastructure Configuration", font=("Segoe UI", 20, "bold"), text_color="#7FA8E0").pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(frame, text="Set your Backend and Server folder IDs and link your OAuth client secret.", font=("Segoe UI", 12), text_color="#888888").pack(anchor="w", padx=30, pady=(0, 20))

        ctk.CTkLabel(frame, text="Backend Folder ID (always public):", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=30, pady=(0, 2))
        self.entry_backend_folder = ctk.CTkEntry(frame, placeholder_text="Backend folder ID...", fg_color="#1E1E24", height=35)
        self.entry_backend_folder.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(frame, text="Server Folder ID (stores world backup):", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=30, pady=(0, 2))
        self.entry_server_folder = ctk.CTkEntry(frame, placeholder_text="Server folder ID...", fg_color="#1E1E24", height=35)
        self.entry_server_folder.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(frame, text="Google App Client Secret JSON File:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=30, pady=(0, 2))
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=30, pady=(0, 25))
        self.entry_secret = ctk.CTkEntry(row, placeholder_text="Select client_secret.json...", fg_color="#1E1E24", height=35)
        self.entry_secret.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(row, text="Browse", width=80, height=35, command=self.browse_client_secret, fg_color="#3A3A42", hover_color="#4F4F59").pack(side="right")

        self.btn_connect = ctk.CTkButton(frame, text="🔗 LINK INFRASTRUCTURE & INITIALIZE SYSTEM", font=("Segoe UI", 13, "bold"), height=48, command=self.connect_and_initialize)
        self.btn_connect.pack(fill="x", padx=30, pady=(0, 20))
        self.lbl_connect_status = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12), text_color="#4CAF50")
        self.lbl_connect_status.pack(pady=5)

    def browse_client_secret(self):
        p = filedialog.askopenfilename(title="Select client_secret.json", filetypes=[("Google App Credentials", "*.json")])
        if p:
            self.entry_secret.delete(0, "end")
            self.entry_secret.insert(0, os.path.normpath(p))

    def connect_and_initialize(self):
        backend_id = self.entry_backend_folder.get().strip()
        server_id = self.entry_server_folder.get().strip()
        secret_path = self.entry_secret.get().strip()
        if not backend_id or not server_id or not os.path.exists(secret_path):
            messagebox.showwarning("Missing Fields", "Fill in all folder IDs and select client_secret.json.")
            return
        self.btn_connect.configure(text="⏳ INITIALIZING...", state="disabled")
        threading.Thread(target=self._bg_connect, args=(backend_id, server_id, secret_path), daemon=True).start()

    def _bg_connect(self, backend_id, server_id, secret_path):
        try:
            with open(secret_path, 'r') as f:
                config_data = json.load(f)
            creds = None
            if os.path.exists('master_token.json'):
                creds = Credentials.from_authorized_user_file('master_token.json', SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_config(config_data, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('master_token.json', 'w') as token:
                    token.write(creds.to_json())

            self.drive_service = build('drive', 'v3', credentials=creds)
            self.backend_folder_id = backend_id
            self.server_folder_id = server_id
            self.client_secret_path = secret_path

            # Derive deterministic Fernet key
            self.fernet_key_bytes = derive_fernet_key(self.backend_folder_id)
            self.fernet_cipher = Fernet(self.fernet_key_bytes)

            # Save only folder info (no fernet key needed in config)
            local_cfg = {'backend_folder_id': backend_id,
                         'server_folder_id': server_id,
                         'secret_path': secret_path}
            self.save_local_config_dict(local_cfg)

            # Check if existing backend data is encrypted with the same key.
            # If not, offer to reinitialize.
            try:
                # Try to decrypt tokens file (or any encrypted file)
                existing = self.cloud_pull_encrypted(TOKENS_NAME, None)
                if existing is not None:
                    # successful decryption -> key matches
                    pass
            except (InvalidToken, Exception):
                # Key mismatch or corrupted data -> ask user to reset backend
                if messagebox.askyesno("Encryption Mismatch",
                                       "Existing backend data cannot be decrypted with the current key.\n\n"
                                       "Do you want to RESET the backend? This will delete all tokens, "
                                       "user accounts, and settings, but your world backup will be preserved."):
                    self.reset_backend()
                else:
                    # User refused – keep the invalid cipher, UI will show errors.
                    pass

            # Ensure critical encrypted files exist (tokens, accounts)
            self.ensure_encrypted_file(TOKENS_NAME, {"tokens": [], "used_tokens": []})
            self.ensure_encrypted_file(ACCOUNTS_NAME, {"users": {}, "server_folder_id": server_id})

            # Sync folder permission mode (non‑blocking)
            try:
                self.sync_server_folder_mode()
            except Exception as e:
                print(f"Warning: Could not sync folder mode: {e}")

            self.after(0, lambda: self.lbl_connect_status.configure(text="✅ Infrastructure linked successfully!"))
            self.after(0, lambda: self.btn_connect.configure(text="✅ LINKED", fg_color="#2EA44F", state="normal"))
            self.after(0, self.refresh_all_admin_data)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Link Failed", f"Could not link folders: {e}"))
            self.after(0, lambda: self.btn_connect.configure(text="🔗 LINK INFRASTRUCTURE & INITIALIZE SYSTEM", state="normal"))

    def reset_backend(self):
        """Delete all encrypted backend files and re‑create with defaults."""
        if not self.drive_service or not self.backend_folder_id:
            return
        # List of files to delete
        files_to_clear = [TOKENS_NAME, ACCOUNTS_NAME, FOLDER_SETTINGS_NAME]
        for fname in files_to_clear:
            try:
                results = self.drive_service.files().list(
                    q=f"'{self.backend_folder_id}' in parents and name='{fname}' and trashed = false",
                    fields="files(id)"
                ).execute()
                for f in results.get('files', []):
                    self.drive_service.files().delete(fileId=f['id']).execute()
            except:
                pass
        # Re‑create with default structures
        self.ensure_encrypted_file(TOKENS_NAME, {"tokens": [], "used_tokens": []})
        self.ensure_encrypted_file(ACCOUNTS_NAME, {"users": {}, "server_folder_id": self.server_folder_id})
        # Folder settings will be synced later

    def load_local_config_dict(self):
        if os.path.exists(MASTER_CONFIG):
            try:
                with open(MASTER_CONFIG, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_local_config_dict(self, cfg):
        with open(MASTER_CONFIG, 'w') as f:
            json.dump(cfg, f, indent=4)

    def load_local_master_config(self):
        cfg = self.load_local_config_dict()
        if 'backend_folder_id' in cfg:
            self.entry_backend_folder.insert(0, cfg['backend_folder_id'])
        if 'server_folder_id' in cfg:
            self.entry_server_folder.insert(0, cfg['server_folder_id'])
        if 'secret_path' in cfg:
            self.entry_secret.insert(0, cfg['secret_path'])
        # Fernet key is derived dynamically – ignore stored key if any

    # ------------------------------------------------------------------------
    #   Encryption helpers
    # ------------------------------------------------------------------------
    def encrypt_data(self, data: dict) -> bytes:
        if self.fernet_cipher is None:
            raise Exception("Fernet cipher not initialized.")
        return self.fernet_cipher.encrypt(json.dumps(data, indent=4).encode('utf-8'))

    def decrypt_data(self, encrypted_bytes: bytes) -> dict:
        if self.fernet_cipher is None:
            raise Exception("Fernet cipher not initialized.")
        return json.loads(self.fernet_cipher.decrypt(encrypted_bytes).decode('utf-8'))

    def ensure_encrypted_file(self, filename, default_structure):
        if self.drive_service is None or not self.backend_folder_id:
            return
        results = self.drive_service.files().list(
            q=f"'{self.backend_folder_id}' in parents and name='{filename}' and trashed = false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])
        if not files:
            encrypted = self.encrypt_data(default_structure)
            media = MediaIoBaseUpload(io.BytesIO(encrypted), mimetype='application/octet-stream', resumable=True)
            file_metadata = {'name': filename, 'parents': [self.backend_folder_id]}
            self.drive_service.files().create(body=file_metadata, media_body=media).execute()

    def cloud_pull_encrypted(self, filename, default_structure):
        """Pull and decrypt a Fernet‑encrypted JSON file. Returns default_structure on missing."""
        if self.drive_service is None:
            return default_structure
        results = self.drive_service.files().list(
            q=f"'{self.backend_folder_id}' in parents and name='{filename}' and trashed = false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])
        if not files:
            self.ensure_encrypted_file(filename, default_structure)
            return default_structure
        file_id = files[0]['id']
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return self.decrypt_data(fh.read())

    def cloud_push_encrypted(self, filename, data):
        if self.drive_service is None:
            return
        encrypted = self.encrypt_data(data)
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

    # ---- Plain JSON helpers (for audit log) ----
    def cloud_pull_json(self, filename, default=[]):
        """Pull a plain (unencrypted) JSON file. Returns default if missing."""
        if self.drive_service is None:
            return default
        results = self.drive_service.files().list(
            q=f"'{self.backend_folder_id}' in parents and name='{filename}' and trashed = false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])
        if not files:
            return default
        file_id = files[0]['id']
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return json.loads(fh.read().decode('utf-8'))

    def cloud_push_json(self, filename, data):
        """Push plain JSON data (unencrypted) to Drive."""
        if self.drive_service is None:
            return
        json_data = json.dumps(data, indent=4).encode('utf-8')
        media = MediaIoBaseUpload(io.BytesIO(json_data), mimetype='application/json', resumable=True)
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

    def append_audit_record(self, username, action_message, revision_id=None):
        try:
            audit = self.cloud_pull_json(AUDIT_LOG_NAME, [])
            record = {
                "username": username,
                "action": action_message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + " UTC"
            }
            if revision_id:
                record["revision_id"] = revision_id
            audit.append(record)
            self.cloud_push_json(AUDIT_LOG_NAME, audit)
        except:
            pass

    # ------------------------------------------------------------------------
    #   Token Keys tab
    # ------------------------------------------------------------------------
    def build_tokens_tab(self):
        frame = self.tab_tokens
        ctk.CTkLabel(frame, text="Invitation Ticket Center", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(frame, text="Generate single-use registration tokens.", font=("Segoe UI", 12), text_color="#888888").pack(anchor="w", padx=30, pady=(0, 20))

        self.btn_gen_tk = ctk.CTkButton(frame, text="✨ FORGE SINGLE-USE REGISTRATION TOKEN", font=("Segoe UI", 12, "bold"), fg_color="#1F538D", height=42, command=self.generate_invitation_token)
        self.btn_gen_tk.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(frame, text="Unused Active Vouchers:", font=("Segoe UI", 12, "bold"), text_color="#A0A0A0").pack(anchor="w", padx=30, pady=(5, 5))
        self.txt_tokens = ctk.CTkTextbox(frame, font=("Consolas", 13), fg_color="#141416", border_width=1, border_color="#2D2D34")
        self.txt_tokens.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def generate_invitation_token(self):
        if not self.drive_service or not self.fernet_cipher:
            messagebox.showwarning("Not Connected", "Please link your infrastructure first.")
            return
        new_tk = "MC-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        data = self.cloud_pull_encrypted(TOKENS_NAME, {"tokens": [], "used_tokens": []})
        data.setdefault('tokens', []).append(new_tk)
        self.cloud_push_encrypted(TOKENS_NAME, data)
        self.append_audit_record("Master Admin", f"Forged token [{new_tk}]")
        self.refresh_tokens_display()
        messagebox.showinfo("Token Built", f"Send this token to the user:\n\n{new_tk}")

    def refresh_tokens_display(self):
        if not self.drive_service or not self.fernet_cipher:
            return
        data = self.cloud_pull_encrypted(TOKENS_NAME, {"tokens": [], "used_tokens": []})
        self.txt_tokens.configure(state="normal")
        self.txt_tokens.delete("1.0", "end")
        for t in data.get('tokens', []):
            self.txt_tokens.insert("end", f" 🎫  {t}\n")
        self.txt_tokens.configure(state="disabled")

    # ------------------------------------------------------------------------
    #   User Profiles tab
    # ------------------------------------------------------------------------
    def build_users_tab(self):
        frame = self.tab_users
        ctk.CTkLabel(frame, text="Registered Client Logins", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(frame, text="Search, sort, select all, and perform bulk actions.", font=("Segoe UI", 12), text_color="#888888").pack(anchor="w", padx=30, pady=(0, 20))

        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", padx=30, pady=(0, 5))
        ctk.CTkLabel(row1, text="Search:", font=("Segoe UI", 12)).pack(side="left", padx=(0, 5))
        self.entry_search = ctk.CTkEntry(row1, placeholder_text="Username or email...", fg_color="#1E1E24", width=200)
        self.entry_search.pack(side="left", padx=(0, 5))
        self.entry_search.bind("<Return>", lambda e: self.apply_user_filters())
        self.btn_search = ctk.CTkButton(row1, text="🔍", width=30, height=30, command=self.apply_user_filters)
        self.btn_search.pack(side="left", padx=(0, 5))
        self.btn_clear_search = ctk.CTkButton(row1, text="Clear", width=60, height=30, command=self.clear_search)
        self.btn_clear_search.pack(side="left", padx=(0, 15))
        ctk.CTkLabel(row1, text="Sort by:", font=("Segoe UI", 12)).pack(side="left", padx=(0, 5))
        self.sort_var = ctk.StringVar(value="date_desc")
        self.sort_menu = ctk.CTkOptionMenu(row1, values=[
            "Date (newest first)", "Date (oldest first)", "Username (A-Z)",
            "Username (Z-A)", "Status (approved first)", "Status (pending first)"
        ], variable=self.sort_var, command=self.apply_user_filters, width=180)
        self.sort_menu.pack(side="left", padx=(0, 10))

        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=30, pady=(0, 10))
        self.select_all_var = ctk.BooleanVar(value=False)
        self.chk_select_all = ctk.CTkCheckBox(row2, text="Select All", variable=self.select_all_var, command=self.toggle_select_all)
        self.chk_select_all.pack(side="left", padx=(0, 10))
        self.btn_bulk_approve = ctk.CTkButton(row2, text="Approve Selected", width=130, height=30, fg_color="#2EA44F", hover_color="#22863A", command=self.bulk_approve)
        self.btn_bulk_approve.pack(side="left", padx=5)
        self.btn_bulk_revoke = ctk.CTkButton(row2, text="Revoke Selected", width=130, height=30, fg_color="#D32F2F", hover_color="#B71C1C", command=self.bulk_revoke)
        self.btn_bulk_revoke.pack(side="left", padx=5)

        self.users_scroll = ctk.CTkScrollableFrame(frame, fg_color="#141416", border_width=1, border_color="#2D2D34")
        self.users_scroll.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self.user_row_widgets = {}

    def clear_search(self):
        self.entry_search.delete(0, 'end')
        self.apply_user_filters()

    def apply_user_filters(self, *args):
        search_text = self.entry_search.get().strip().lower()
        sort_mode = self.sort_var.get()
        users = self.all_users

        filtered = {}
        for uname, info in users.items():
            email = info.get('email', '').lower()
            if search_text in uname.lower() or search_text in email:
                filtered[uname] = info

        items = list(filtered.items())
        if sort_mode == "Date (newest first)":
            items.sort(key=lambda x: x[1].get('registered_at', 0), reverse=True)
        elif sort_mode == "Date (oldest first)":
            items.sort(key=lambda x: x[1].get('registered_at', 0))
        elif sort_mode == "Username (A-Z)":
            items.sort(key=lambda x: x[0].lower())
        elif sort_mode == "Username (Z-A)":
            items.sort(key=lambda x: x[0].lower(), reverse=True)
        elif sort_mode == "Status (approved first)":
            items.sort(key=lambda x: (x[1].get('status', 'pending') != 'approved', x[0].lower()))
        elif sort_mode == "Status (pending first)":
            items.sort(key=lambda x: (x[1].get('status', 'pending') == 'approved', x[0].lower()))

        self.filtered_users_list = [u[0] for u in items]
        self.select_all_var.set(False)
        self._draw_user_rows(items)

    def toggle_select_all(self):
        state = self.select_all_var.get()
        for w in self.user_row_widgets.values():
            if 'checkbox' in w:
                w['checkbox'].select() if state else w['checkbox'].deselect()

    def _draw_user_rows(self, user_items):
        for w in self.users_scroll.winfo_children():
            w.destroy()
        self.user_row_widgets.clear()

        if not user_items:
            ctk.CTkLabel(self.users_scroll, text="No users match the filters.", text_color="#888888").pack(pady=20)
            return

        for uname, info in user_items:
            email = info.get('email', 'no email')
            status = info.get('status', 'pending')
            registered = info.get('registered_at', 0)
            date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(registered)) if registered else "unknown"

            row_frame = ctk.CTkFrame(self.users_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=5, padx=10)

            var = ctk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(row_frame, text="", variable=var, width=20)
            chk.pack(side="left", padx=(0, 5))

            lbl_text = f"👤 {uname}  |  {email}  [{status}]  (joined {date_str})"
            lbl = ctk.CTkLabel(row_frame, text=lbl_text, font=("Segoe UI", 11), anchor="w")
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 10))

            if status == 'pending':
                btn = ctk.CTkButton(row_frame, text="✅ Grant", width=80, height=25, fg_color="#2EA44F", hover_color="#22863A",
                                    command=lambda u=uname, e=email: self.grant_user_access(u, e))
                btn.pack(side="right", padx=5)
            else:
                btn = ctk.CTkButton(row_frame, text="🚫 Revoke", width=80, height=25, fg_color="#D32F2F", hover_color="#B71C1C",
                                    command=lambda u=uname: self.revoke_user(u))
                btn.pack(side="right", padx=5)

            self.user_row_widgets[uname] = {'checkbox': chk, 'frame': row_frame, 'info': info}

    def grant_user_access(self, username, email):
        if not self.drive_service:
            return
        try:
            self.drive_service.permissions().create(
                fileId=self.server_folder_id,
                body={'type': 'user', 'role': 'writer', 'emailAddress': email},
                sendNotificationEmail=False
            ).execute()
        except Exception as e:
            messagebox.showerror("Grant Failed", f"Could not add permission: {e}")
            return

        accounts = self.cloud_pull_encrypted(ACCOUNTS_NAME, {"users": {}, "server_folder_id": self.server_folder_id})
        if username in accounts.get('users', {}):
            accounts['users'][username]['status'] = 'approved'
            self.cloud_push_encrypted(ACCOUNTS_NAME, accounts)
            self.append_audit_record("Master Admin", f"Granted Server access to {username} ({email})")
            self.refresh_users_display()

    def revoke_user(self, username):
        if not messagebox.askyesno("Confirm Revoke", f"Remove user '{username}' and revoke all folder access?"):
            return
        accounts = self.cloud_pull_encrypted(ACCOUNTS_NAME, {"users": {}, "server_folder_id": self.server_folder_id})
        user_info = accounts.get('users', {}).get(username)
        if not user_info:
            return
        email = user_info.get('email', '')
        del accounts['users'][username]
        self.cloud_push_encrypted(ACCOUNTS_NAME, accounts)

        for folder_id in [self.server_folder_id, self.backend_folder_id]:
            if email and folder_id:
                try:
                    perms = self.drive_service.permissions().list(fileId=folder_id, fields="permissions(id,emailAddress)").execute()
                    for p in perms.get('permissions', []):
                        if p.get('emailAddress', '').lower() == email.lower():
                            self.drive_service.permissions().delete(fileId=folder_id, permissionId=p['id']).execute()
                            break
                except:
                    pass
        self.append_audit_record("Master Admin", f"Revoked user: {username} ({email})")
        self.refresh_users_display()

    def bulk_approve(self):
        selected = self._get_selected_usernames()
        if not selected:
            messagebox.showinfo("No Selection", "No users selected.")
            return
        for uname in selected:
            info = self.all_users.get(uname)
            if info and info.get('status') == 'pending':
                self.grant_user_access(uname, info.get('email', ''))

    def bulk_revoke(self):
        selected = self._get_selected_usernames()
        if not selected:
            messagebox.showinfo("No Selection", "No users selected.")
            return
        if not messagebox.askyesno("Confirm Bulk Revoke", f"Revoke {len(selected)} user(s)?"):
            return
        for uname in selected:
            self.revoke_user(uname)

    def _get_selected_usernames(self):
        return [uname for uname, w in self.user_row_widgets.items() if 'checkbox' in w and w['checkbox'].get()]

    def refresh_users_display(self):
        if not self.drive_service or not self.fernet_cipher:
            return
        accounts = self.cloud_pull_encrypted(ACCOUNTS_NAME, {"users": {}, "server_folder_id": self.server_folder_id})
        self.all_users = accounts.get('users', {})
        self.apply_user_filters()

    # ------------------------------------------------------------------------
    #   Folder Settings tab
    # ------------------------------------------------------------------------
    def build_settings_tab(self):
        frame = self.tab_settings
        ctk.CTkLabel(frame, text="Server Folder Access Control", font=("Segoe UI", 20, "bold"), text_color="#FF9800").pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(frame, text="Toggle the Server folder between public and restricted. When switching to restricted,\nall currently approved users will be automatically added as individual writers.", font=("Segoe UI", 12), text_color="#888888").pack(anchor="w", padx=30, pady=(0, 20))

        self.radio_var = ctk.StringVar(value="public")
        radio_frame = ctk.CTkFrame(frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=30, pady=10)

        self.radio_public = ctk.CTkRadioButton(radio_frame, text="🌍 Public (anyone with the link can edit)", variable=self.radio_var, value="public", font=("Segoe UI", 13))
        self.radio_public.pack(anchor="w", pady=5)
        self.radio_restricted = ctk.CTkRadioButton(radio_frame, text="🔒 Restricted (only manually added emails can access)", variable=self.radio_var, value="restricted", font=("Segoe UI", 13))
        self.radio_restricted.pack(anchor="w", pady=5)

        self.btn_apply_mode = ctk.CTkButton(frame, text="APPLY PERMISSION MODE", font=("Segoe UI", 13, "bold"), fg_color="#1F538D", height=40, command=self.apply_permission_mode)
        self.btn_apply_mode.pack(pady=(20, 10), padx=30, fill="x")

        self.lbl_mode_status = ctk.CTkLabel(frame, text="Current mode: public", font=("Segoe UI", 12), text_color="#4CAF50")
        self.lbl_mode_status.pack(pady=5)

    def sync_server_folder_mode(self):
        """Query the Server folder's actual permissions and update the stored/UI mode."""
        if not self.drive_service or not self.server_folder_id:
            return
        perms = self.drive_service.permissions().list(fileId=self.server_folder_id, fields="permissions(id,type,role)").execute()
        is_public = any(p.get('type') == 'anyone' and p.get('role') == 'writer' for p in perms.get('permissions', []))
        actual_mode = "public" if is_public else "restricted"
        if actual_mode != self.server_permission_mode:
            self.cloud_push_encrypted(FOLDER_SETTINGS_NAME, {"mode": actual_mode})
            self.server_permission_mode = actual_mode
            self.append_audit_record("Master Admin", f"Folder mode synced from Drive: {actual_mode}")
        self.update_settings_ui()

    def load_server_permission_mode(self):
        try:
            settings = self.cloud_pull_encrypted(FOLDER_SETTINGS_NAME, {"mode": "public"})
            self.server_permission_mode = settings.get("mode", "public")
            self.sync_server_folder_mode()  # force update from actual Drive state
        except:
            self.server_permission_mode = "public"

    def save_server_permission_mode(self, mode):
        self.cloud_push_encrypted(FOLDER_SETTINGS_NAME, {"mode": mode})
        old_mode = self.server_permission_mode
        self.server_permission_mode = mode
        self.append_audit_record("Master Admin", f"Server folder permission mode changed to: {mode}")

        if not self.drive_service or not self.server_folder_id:
            return

        try:
            if mode == "public":
                try:
                    self.drive_service.permissions().create(
                        fileId=self.server_folder_id,
                        body={'type': 'anyone', 'role': 'writer'},
                        fields='id'
                    ).execute()
                except Exception:
                    pass
            else:
                perms = self.drive_service.permissions().list(fileId=self.server_folder_id, fields="permissions(id,type)").execute()
                for p in perms.get('permissions', []):
                    if p.get('type') == 'anyone':
                        self.drive_service.permissions().delete(fileId=self.server_folder_id, permissionId=p['id']).execute()

                accounts = self.cloud_pull_encrypted(ACCOUNTS_NAME, {"users": {}, "server_folder_id": self.server_folder_id})
                users = accounts.get('users', {})
                count = 0
                for uname, info in users.items():
                    if info.get('status') == 'approved' and info.get('email'):
                        try:
                            self.drive_service.permissions().create(
                                fileId=self.server_folder_id,
                                body={'type': 'user', 'role': 'writer', 'emailAddress': info['email']},
                                sendNotificationEmail=False
                            ).execute()
                            count += 1
                        except Exception:
                            pass
                if old_mode == 'public':
                    self.after(0, lambda: messagebox.showinfo("Migration Complete", f"{count} approved user(s) added as editors."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Permission Error", f"Could not update folder permissions: {e}"))
            return

        self.update_settings_ui()

    def update_settings_ui(self):
        self.radio_var.set(self.server_permission_mode)
        self.lbl_mode_status.configure(text=f"Current mode: {self.server_permission_mode}")

    def apply_permission_mode(self):
        new_mode = self.radio_var.get()
        if new_mode == self.server_permission_mode:
            return
        self.save_server_permission_mode(new_mode)

    # ------------------------------------------------------------------------
    #   Rollback tab
    # ------------------------------------------------------------------------
    def build_rollback_tab(self):
        frame = self.tab_rollback
        ctk.CTkLabel(frame, text="Cloud Backup Rollback Ledger", font=("Segoe UI", 20, "bold"), text_color="#FF9800").pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(frame, text="Google automatically seals immutable backup instances. Choose a checkpoint below to rewind data.", font=("Segoe UI", 12), text_color="#888888").pack(anchor="w", padx=30, pady=(0, 15))

        self.live_status_card = ctk.CTkFrame(frame, fg_color="#1E1E24", corner_radius=10, border_width=1, border_color="#333338")
        self.live_status_card.pack(fill="x", padx=30, pady=(0, 15))
        self.lbl_live_ver = ctk.CTkLabel(self.live_status_card, text="ACTIVE CLOUD BACKUP STATE: Loading details...", font=("Segoe UI", 12, "bold"), text_color="#4CAF50")
        self.lbl_live_ver.pack(anchor="w", padx=20, pady=12)

        control_card = ctk.CTkFrame(frame, fg_color="transparent")
        control_card.pack(fill="x", padx=30, pady=(5, 15))

        ctk.CTkLabel(control_card, text="Select Target Backup Checkpoint:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.dropdown_versions = ctk.CTkOptionMenu(control_card, values=["No connected repositories"], width=400, height=40, dynamic_resizing=False)
        self.dropdown_versions.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_rollback = ctk.CTkButton(control_card, text="⏪ RESTORE SELECTED BACKUP", font=("Segoe UI", 12, "bold"), fg_color="#E65100", hover_color="#F57C00", height=40, width=240, command=self.execute_friendly_rollback)
        self.btn_rollback.pack(side="right", padx=(10, 0))

        ctk.CTkLabel(frame, text="Detailed Infrastructure Upload Audit Logs:", font=("Segoe UI", 12, "bold"), text_color="#A0A0A0").pack(anchor="w", padx=30, pady=(10, 5))
        self.rev_timeline_box = ctk.CTkTextbox(frame, font=("Consolas", 11), fg_color="#141416", border_width=1, border_color="#2D2D34")
        self.rev_timeline_box.pack(fill="both", expand=True, padx=30, pady=(0, 25))

    def refresh_rollback_history(self):
        if not self.drive_service or not self.server_folder_id:
            return

        results = self.drive_service.files().list(
            q=f"'{self.server_folder_id}' in parents and name='{BACKUP_NAME}' and trashed = false",
            fields="files(id)"
        ).execute()
        files = results.get('files', [])
        if not files:
            self.lbl_live_ver.configure(text="ACTIVE CLOUD BACKUP STATE: No world_backup.zip found.")
            self.dropdown_versions.configure(values=["No file checkpoints detected"])
            self.dropdown_versions.set("No file checkpoints detected")
            return

        file_id = files[0]['id']
        revisions_meta = self.drive_service.revisions().list(fileId=file_id, fields="revisions(id, modifiedTime)").execute()
        revisions = revisions_meta.get('revisions', [])

        audit_trail = self.cloud_pull_json(AUDIT_LOG_NAME, [])
        revision_uploader = {}
        for entry in audit_trail:
            if "revision_id" in entry:
                revision_uploader[entry["revision_id"]] = entry.get("username", "System")

        friendly_options_list = []
        self.revision_map.clear()

        self.rev_timeline_box.configure(state="normal")
        self.rev_timeline_box.delete("1.0", "end")
        self.rev_timeline_box.insert("end", f"{'BACKUP CHECKPOINT TIMELINE':<50}{'REVISION ID':<15}\n" + "—"*75 + "\n")

        for idx, rev in enumerate(reversed(revisions)):
            r_id = rev.get('id', '')
            r_time = rev.get('modifiedTime', '').replace('T', ' ').replace('Z', '')[:16]

            uploader = revision_uploader.get(r_id)
            if not uploader:
                for entry in audit_trail:
                    if "upload" in entry.get("action", "").lower() and entry.get("timestamp", "")[:16] in r_time:
                        uploader = entry.get("username", "System")
                        break
                if not uploader:
                    uploader = "Unknown Operator"

            friendly_string = f"Backup ({r_time}) — by {uploader}"
            friendly_options_list.append(friendly_string)
            self.revision_map[friendly_string] = r_id

            if idx == 0:
                self.lbl_live_ver.configure(text=f"ACTIVE: Rev #{r_id} at {r_time} by {uploader}")

            self.rev_timeline_box.insert("end", f" 💾  {friendly_string:<48}  [ID: {r_id}]\n")

        self.rev_timeline_box.configure(state="disabled")

        if friendly_options_list:
            self.dropdown_versions.configure(values=friendly_options_list)
            self.dropdown_versions.set(friendly_options_list[0])
        else:
            self.dropdown_versions.configure(values=["No file checkpoints available"])
            self.dropdown_versions.set("No file checkpoints available")

    def execute_friendly_rollback(self):
        selected_text = self.dropdown_versions.get()
        if selected_text in ["No connected repositories", "No file checkpoints detected", "No file checkpoints available"]:
            messagebox.showwarning("Selection Invalid", "No valid rollback target selected.")
            return

        target_revision_id = self.revision_map.get(selected_text)
        if not target_revision_id:
            return

        if not messagebox.askyesno("Confirm Rollback", f"Revert world_backup.zip to:\n\n{selected_text}\n\nAll subsequent changes will be lost."):
            return

        self.btn_rollback.configure(text="⏳ RESTORING...", state="disabled")
        threading.Thread(target=self._bg_rollback, args=(target_revision_id,), daemon=True).start()

    def _bg_rollback(self, revision_id):
        try:
            results = self.drive_service.files().list(
                q=f"'{self.server_folder_id}' in parents and name='{BACKUP_NAME}' and trashed = false",
                fields="files(id)"
            ).execute()
            file_id = results['files'][0]['id']

            request = self.drive_service.revisions().get_media(fileId=file_id, revisionId=revision_id)
            memory_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(memory_stream, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            memory_stream.seek(0)
            media = MediaIoBaseUpload(memory_stream, mimetype='application/zip', resumable=True)
            self.drive_service.files().update(fileId=file_id, media_body=media).execute()

            updated_file = self.drive_service.files().get(fileId=file_id, fields="headRevisionId").execute()
            new_revision = updated_file.get('headRevisionId')
            self.append_audit_record("Master Admin", f"Rolled back world to revision {revision_id}", revision_id=new_revision)

            self.after(0, lambda: messagebox.showinfo("Rollback Complete", "The world backup has been restored to the selected checkpoint."))
            self.after(0, self.refresh_rollback_history)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Rollback Failed", f"Error: {e}"))
        finally:
            self.after(0, lambda: self.btn_rollback.configure(text="⏪ RESTORE SELECTED BACKUP", state="normal"))

    # ------------------------------------------------------------------------
    #   Export Client Key
    # ------------------------------------------------------------------------
    def build_export_tab(self):
        frame = self.tab_export
        ctk.CTkLabel(frame, text="Export Client Access Key", font=("Segoe UI", 20, "bold"), text_color="#FF9800").pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(frame, text="Generates an encrypted file containing the backend folder ID, Fernet key, and OAuth client secret.\nDistribute this file to your users so they can connect without manual folder configuration.", font=("Segoe UI", 12), text_color="#888888").pack(anchor="w", padx=30, pady=(0, 20))

        self.btn_export = ctk.CTkButton(frame, text="📦 COMPILE & EXPORT client_access.key", font=("Segoe UI", 13, "bold"), fg_color="#2EA44F", hover_color="#22863A", height=45, command=self.export_client_key)
        self.btn_export.pack(fill="x", padx=30, pady=20)

        self.lbl_export_status = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12), text_color="#AAAAAA")
        self.lbl_export_status.pack(pady=10)

    def export_client_key(self):
        if not self.drive_service or not self.fernet_cipher or not self.backend_folder_id or not self.client_secret_path:
            messagebox.showwarning("Missing Configuration", "Please complete the Cloud Setup first.")
            return
        try:
            with open(self.client_secret_path, 'r') as f:
                secret_json = json.load(f)

            payload = {
                "client_config": secret_json,
                "backend_folder_id": self.backend_folder_id,
                "fernet_key": self.fernet_key_bytes.decode('utf-8')
            }
            serialized = json.dumps(payload).encode('utf-8')
            hasher = hashlib.sha256(CLIENT_KEY_SEED)
            cipher = Fernet(base64.urlsafe_b64encode(hasher.digest()))
            encrypted_data = cipher.encrypt(serialized)

            save_path = filedialog.asksaveasfilename(defaultextension=".key", filetypes=[("Client Key", "*.key")], initialfile="client_access.key")
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(encrypted_data)
                self.lbl_export_status.configure(text="✅ Client key exported successfully!")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not create client key: {e}")

    def refresh_all_admin_data(self):
        if self.drive_service and self.fernet_cipher:
            self.refresh_tokens_display()
            self.refresh_users_display()
            self.refresh_rollback_history()

if __name__ == "__main__":
    app = MasterManagerConsole()
    app.mainloop()
