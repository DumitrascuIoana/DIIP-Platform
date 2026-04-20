# ============================================================
# auth.py
# Ce face: Gestioneaza autentificarea utilizatorilor
#
# Contine:
#   1. Verificarea parolei (bcrypt)
#   2. Crearea si validarea sesiunilor (token-uri)
#   3. Logging-ul actiunilor in audit_logs
#   4. Decoratori pentru protejarea rutelor
# ============================================================

import bcrypt
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException
from database import db


# ============================================================
# CLASA AuthManager
# Gestioneaza toate operatiile de autentificare
# ============================================================
class AuthManager:

    def __init__(self):
        # Durata sesiunii: 8 ore
        # Dupa 8 ore, userul trebuie sa se relogheze
        self.session_duration_hours = 8

    # ==========================================================
    # OPERATII CU PAROLE
    # ==========================================================

    def hash_password(self, password: str) -> str:
        """
        Transforma o parola in hash bcrypt.
        Hash-ul e ireversibil — nu poti recupera parola din hash.

        Ex: "Admin1234!" -> "$2b$12$abc...xyz"

        bcrypt adauga automat un "salt" (date random)
        ca doua parole identice sa aiba hash-uri diferite.
        """
        # encode() = convertim string in bytes (bcrypt lucreaza cu bytes)
        password_bytes = password.encode('utf-8')
        # rounds=12 = cat de "greu" e hash-ul (mai mare = mai sigur dar mai lent)
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
        return hashed.decode('utf-8')  # convertim inapoi la string

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica daca o parola in text clar corespunde hash-ului din DB.
        Returneaza True daca parola e corecta, False altfel.

        bcrypt.checkpw() face hash-ul din nou si compara.
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    # ==========================================================
    # OPERATII CU USERI
    # ==========================================================

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Cauta un user dupa username. Returneaza dict sau None."""
        conn   = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, email, password_hash, role, is_active, last_login FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        columns = [col[0] for col in cursor.description]
        user    = dict(zip(columns, row))
        if user.get("last_login"):
            user["last_login"] = user["last_login"].strftime("%Y-%m-%d %H:%M:%S")
        return user

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Cauta un user dupa ID."""
        conn   = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, email, role, is_active FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

    def get_all_users(self) -> list:
        """Returneaza toti userii (fara parole!)."""
        conn   = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, email, role, is_active, last_login, created_at
            FROM users
            ORDER BY created_at DESC
        """)

        columns = [col[0] for col in cursor.description]
        users   = []
        for row in cursor.fetchall():
            user = dict(zip(columns, row))
            for key in ["last_login", "created_at"]:
                if user.get(key):
                    user[key] = user[key].strftime("%Y-%m-%d %H:%M:%S")
            users.append(user)

        conn.close()
        return users

    def create_user(self, username: str, email: str,
                    password: str, role: str = "user") -> int:
        """
        Creeaza un user nou.
        Parola e hash-uita automat — niciodata salvata in text clar!
        """
        conn   = db.get_connection()
        cursor = conn.cursor()

        password_hash = self.hash_password(password)

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (username, email, password_hash, role))

        cursor.execute("SELECT @@IDENTITY")
        user_id = int(cursor.fetchone()[0])

        conn.commit()
        conn.close()
        return user_id

    def update_last_login(self, user_id: int):
        """Actualizeaza data ultimului login."""
        conn   = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = GETDATE() WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        conn.close()

    # ==========================================================
    # OPERATII CU SESIUNI
    # ==========================================================

    def create_session(self, user_id: int, ip_address: str = None) -> str:
        """
        Creeaza o sesiune noua pentru un user logat.

        secrets.token_urlsafe(32) genereaza un token random de 32 bytes
        Ex: "abc123xyz..." — imposibil de ghicit

        Returneaza token-ul — il salvam in cookie-ul browserului.
        """
        # Generam token unic si sigur
        token      = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)

        conn   = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (user_id, session_token, expires_at, ip_address)
            VALUES (?, ?, ?, ?)
        """, (user_id, token, expires_at, ip_address))

        conn.commit()
        conn.close()
        return token

    def validate_session(self, token: str) -> Optional[dict]:
        """
        Verifica daca un token de sesiune e valid.

        Verificari:
        1. Token-ul exista in DB
        2. Sesiunea nu a expirat
        3. Sesiunea e activa (nu s-a facut logout)
        4. Userul e activ

        Returneaza datele user-ului sau None daca sesiunea e invalida.
        """
        if not token:
            return None

        conn   = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.user_id, s.expires_at, s.is_active,
                u.username, u.email, u.role, u.is_active as user_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ?
        """, (token,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None  # Token inexistent

        user_id, expires_at, session_active, username, email, role, user_active = row

        # Verificam daca sesiunea a expirat
        if datetime.now() > expires_at:
            return None

        # Verificam daca sesiunea e activa si userul e activ
        if not session_active or not user_active:
            return None

        return {
            "user_id":  user_id,
            "username": username,
            "email":    email,
            "role":     role
        }

    def invalidate_session(self, token: str):
        """
        Invalideaza sesiunea (logout).
        Nu stergem din DB — pastram istoricul.
        """
        conn   = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
            (token,)
        )

        conn.commit()
        conn.close()

    def invalidate_all_sessions(self, user_id: int):
        """Invalideaza TOATE sesiunile unui user (logout de peste tot)."""
        conn   = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE sessions SET is_active = 0 WHERE user_id = ?",
            (user_id,)
        )

        conn.commit()
        conn.close()

    # ==========================================================
    # AUDIT LOGS
    # ==========================================================

    def log_action(self, action: str, user_id: int = None,
                   username: str = None, entity_type: str = None,
                   entity_id: int = None, details: str = None,
                   ip_address: str = None, status: str = "success"):
        """
        Salveaza o actiune in audit_logs.

        Apelata dupa fiecare actiune importanta:
        - login reusit / esuat
        - logout
        - scanare pornita
        - device editat
        - export Excel/CSV
        """
        try:
            conn   = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO audit_logs
                    (user_id, username, action, entity_type, entity_id,
                     details, ip_address, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, action, entity_type, entity_id,
                  details, ip_address, status))

            conn.commit()
            conn.close()
        except Exception as e:
            # Nu vrem ca un log esuat sa opreasca aplicatia
            print(f"[AUDIT] Eroare la logare: {e}")

    def get_audit_logs(self, limit: int = 100,
                       username_filter: str = None,
                       action_filter: str = None) -> list:
        """
        Returneaza audit logs cu filtre optionale.
        Folosit in pagina de Audit din dashboard.
        """
        conn   = db.get_connection()
        cursor = conn.cursor()

        query  = """
            SELECT TOP (?)
                id, username, action, entity_type, entity_id,
                details, ip_address, status, created_at
            FROM audit_logs
            WHERE 1=1
        """
        params = [limit]

        if username_filter:
            query += " AND username LIKE ?"
            params.append(f"%{username_filter}%")

        if action_filter:
            query += " AND action = ?"
            params.append(action_filter)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        logs    = []

        for row in cursor.fetchall():
            item = dict(zip(columns, row))
            if item.get("created_at"):
                item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            logs.append(item)

        conn.close()
        return logs

    # ==========================================================
    # HELPER: extrage token din request
    # ==========================================================

    def get_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extrage token-ul de sesiune din cookie-ul browserului.
        Cookie-ul se numeste 'session_token'.
        """
        return request.cookies.get("session_token")

    def get_current_user(self, request: Request) -> Optional[dict]:
        """
        Returneaza userul logat din request.
        Folosit in fiecare ruta protejata.
        """
        token = self.get_token_from_request(request)
        if not token:
            return None
        return self.validate_session(token)

    def require_auth(self, request: Request) -> dict:
        """
        Verifica autentificarea. Arunca eroare 401 daca nu e logat.
        Folosit ca dependency in rutele FastAPI.
        """
        user = self.get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Neautentificat")
        return user

    def require_admin(self, request: Request) -> dict:
        """
        Verifica ca userul e admin. Arunca eroare 403 daca nu e.
        """
        user = self.require_auth(request)
        if user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Acces interzis — necesita rol de admin"
            )
        return user

    # ==========================================================
    # LOGIN FLOW COMPLET
    # ==========================================================

    def login(self, username: str, password: str,
              ip_address: str = None) -> dict:
        """
        Flow complet de login:
        1. Cauta userul in DB
        2. Verifica parola
        3. Creeaza sesiune
        4. Logheaza actiunea in audit_logs
        5. Returneaza token-ul

        Returneaza:
            {'success': True, 'token': '...', 'user': {...}}
            sau
            {'success': False, 'message': '...'}
        """
        # Pasul 1: Cauta userul
        user = self.get_user_by_username(username)

        if not user:
            # Userul nu exista — logam tentativa esuata
            self.log_action(
                action     = "LOGIN_FAILED",
                username   = username,
                details    = "Username inexistent",
                ip_address = ip_address,
                status     = "failed"
            )
            return {"success": False, "message": "Username sau parola incorecta"}

        # Pasul 2: Verifica daca contul e activ
        if not user["is_active"]:
            self.log_action(
                action     = "LOGIN_FAILED",
                user_id    = user["id"],
                username   = username,
                details    = "Cont dezactivat",
                ip_address = ip_address,
                status     = "failed"
            )
            return {"success": False, "message": "Contul este dezactivat"}

        # Pasul 3: Verifica parola
        if not self.verify_password(password, user["password_hash"]):
            self.log_action(
                action     = "LOGIN_FAILED",
                user_id    = user["id"],
                username   = username,
                details    = "Parola incorecta",
                ip_address = ip_address,
                status     = "failed"
            )
            return {"success": False, "message": "Username sau parola incorecta"}

        # Pasul 4: Creeaza sesiune
        token = self.create_session(user["id"], ip_address)

        # Pasul 5: Actualizeaza last_login
        self.update_last_login(user["id"])

        # Pasul 6: Logam login-ul reusit
        self.log_action(
            action     = "LOGIN",
            user_id    = user["id"],
            username   = username,
            details    = f"Login reusit — rol: {user['role']}",
            ip_address = ip_address,
            status     = "success"
        )

        return {
            "success": True,
            "token":   token,
            "user": {
                "id":       user["id"],
                "username": user["username"],
                "email":    user["email"],
                "role":     user["role"]
            }
        }

    def logout(self, request: Request) -> bool:
        """
        Flow complet de logout:
        1. Extrage token din cookie
        2. Invalideaza sesiunea
        3. Logheaza actiunea
        """
        token = self.get_token_from_request(request)
        user  = self.get_current_user(request)

        if token:
            self.invalidate_session(token)

        if user:
            self.log_action(
                action   = "LOGOUT",
                user_id  = user["id"],
                username = user["username"],
                details  = "Logout manual",
                status   = "success"
            )

        return True


# ============================================================
# INSTANTA GLOBALA
# Importa aceasta in main.py si in alte fisiere:
#   from auth import auth_manager
# ============================================================
auth_manager = AuthManager()
