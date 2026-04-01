# ============================================================
# database.py
# Ce face: Gestionează TOATĂ comunicarea cu SQL Server
#
# Acest fișier are 2 roluri:
#   1. Conexiunea la baza de date (citește .env)
#   2. Toate operațiile SQL (get, insert, update)
#
# Restul aplicației nu scrie SQL direct —
# importă funcțiile definite AICI.
# ============================================================

import pyodbc
from dotenv import load_dotenv
import os
from typing import Optional

# Încarcă variabilele din fișierul .env
# Fără această linie, os.getenv() returnează None
load_dotenv()


# ============================================================
# CLASA DatabaseManager
# Gândește-te la ea ca la un "asistent" dedicat bazei de date.
# Creezi o singură instanță (jos, la finalul fișierului)
# și o folosești peste tot în aplicație.
# ============================================================
class DatabaseManager:

    def __init__(self):
        # Se rulează automat când faci: db = DatabaseManager()
        # Construiește string-ul de conectare din .env
        self.connection_string = self._build_connection_string()

    def _build_connection_string(self) -> str:
        """
        Construiește șirul de conectare pentru pyodbc.
        Prefixul _ = metodă internă, nu o apelezi din exterior.
        """
        server = os.getenv("DB_SERVER", "localhost")
        database = os.getenv("DB_NAME", "DIIP")
        driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        trusted = os.getenv("DB_TRUSTED_CONNECTION", "Yes")

        if trusted.lower() == "yes":
            # Autentificare Windows — fără user/parolă
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
            )
        else:
            # Autentificare SQL Server — cu user și parolă din .env
            username = os.getenv("DB_USERNAME", "")
            password = os.getenv("DB_PASSWORD", "")
            return (
                f"DRIVER={{{driver}}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
            )

    def get_connection(self):
        """
        Deschide o conexiune nouă la SQL Server și o returnează.
        Fiecare operație deschide și închide propria conexiune.
        Dacă eșuează, aruncă o eroare cu mesaj clar.
        """
        try:
            return pyodbc.connect(self.connection_string)
        except pyodbc.Error as e:
            print(f"[DB ERROR] Conexiune eșuată: {e}")
            raise

    def test_connection(self) -> dict:
        """
        Verifică dacă conexiunea la SQL Server funcționează.
        Returnează un dict cu status și detalii.
        Util să rulezi la pornirea aplicației.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT GETDATE() AS server_time, @@SERVERNAME AS server_name")
            row = cursor.fetchone()
            conn.close()
            return {
                "status": "ok",
                "message": "Conexiune reușită!",
                "server_time": str(row.server_time),
                "server_name": row.server_name
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    # ----------------------------------------------------------
    # Metodă ajutătoare internă
    # Transformă un rând pyodbc într-un dict Python
    # ----------------------------------------------------------
    def _row_to_dict(self, cursor, row) -> dict:
        """
        pyodbc returnează rânduri ca tuple-uri.
        Această funcție le convertește în dictionare:
        Ex: (1, '192.168.1.1', 'online') →
            {'id': 1, 'ip_address': '192.168.1.1', 'status': 'online'}
        """
        columns = [col[0] for col in cursor.description]
        item = dict(zip(columns, row))
        # Convertim obiectele datetime în string (pentru JSON)
        for key, value in item.items():
            if hasattr(value, 'strftime'):
                item[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        return item

    # ==========================================================
    # DEVICES — operații CRUD
    # ==========================================================

    def get_all_devices(self) -> list:
        """
        Returnează TOATE device-urile din baza de date.
        Sortate: online primul, offline al doilea, unknown ultimul.
        Folosit de: pagina Inventar
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, ip_address, hostname, device_type,
                os_name, os_family, mac_address,
                owner, department, status,
                open_ports, last_seen, first_seen, notes
            FROM devices
            ORDER BY
                CASE status
                    WHEN 'online'  THEN 1
                    WHEN 'offline' THEN 2
                    ELSE 3
                END,
                ip_address
        """)

        devices = [self._row_to_dict(cursor, row) for row in cursor.fetchall()]
        conn.close()
        return devices

    def get_device_by_ip(self, ip_address: str) -> Optional[dict]:
        """
        Caută un device după adresa IP.
        Returnează dict sau None dacă nu există.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # ? = parametru — PROTEJEAZĂ împotriva SQL Injection
        # Nu folosi NICIODATĂ f-string cu date de la user în SQL!
        cursor.execute(
            "SELECT * FROM devices WHERE ip_address = ?",
            (ip_address,)
        )

        row = cursor.fetchone()
        result = self._row_to_dict(cursor, row) if row else None
        conn.close()
        return result

    def upsert_device(self, device_data: dict) -> int:
        """
        UPSERT = UPDATE dacă există + INSERT dacă nu există.
        Apelat după scanare pentru fiecare IP activ găsit.
        Returnează ID-ul device-ului din baza de date.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Verificăm dacă IP-ul există deja
        cursor.execute(
            "SELECT id FROM devices WHERE ip_address = ?",
            (device_data["ip_address"],)
        )
        existing = cursor.fetchone()

        if existing:
            # Există → actualizăm informațiile
            cursor.execute("""
                UPDATE devices SET
                    hostname    = ?,
                    device_type = ?,
                    os_name     = ?,
                    os_family   = ?,
                    mac_address = ?,
                    status      = ?,
                    open_ports  = ?,
                    last_seen   = GETDATE()
                WHERE ip_address = ?
            """, (
                device_data.get("hostname"),
                device_data.get("device_type", "Unknown"),
                device_data.get("os_name"),
                device_data.get("os_family"),
                device_data.get("mac_address"),
                device_data.get("status", "online"),
                device_data.get("open_ports"),
                device_data["ip_address"]
            ))
            device_id = existing[0]

        else:
            # Nu există → inserăm device nou
            cursor.execute("""
                INSERT INTO devices
                    (ip_address, hostname, device_type, os_name,
                     os_family, mac_address, status, open_ports, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                device_data["ip_address"],
                device_data.get("hostname"),
                device_data.get("device_type", "Unknown"),
                device_data.get("os_name"),
                device_data.get("os_family"),
                device_data.get("mac_address"),
                device_data.get("status", "online"),
                device_data.get("open_ports")
            ))
            # @@IDENTITY = ID-ul generat automat de IDENTITY(1,1)
            cursor.execute("SELECT @@IDENTITY")
            device_id = int(cursor.fetchone()[0])

        conn.commit()  # <-- IMPORTANT: salvează modificările!
        conn.close()
        return device_id

    def update_device_status(self, ip_address: str, status: str):
        """
        Actualizează DOAR statusul unui device (online/offline).
        Apelat de monitorul de alerte la fiecare verificare.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE devices
            SET
                status    = ?,
                last_seen = CASE WHEN ? = 'online' THEN GETDATE() ELSE last_seen END
            WHERE ip_address = ?
        """, (status, status, ip_address))

        conn.commit()
        conn.close()

    def update_device_info(self, device_id: int, data: dict):
        """
        Actualizează câmpurile completate manual de user:
        owner, department, notes.
        Apelat din pagina Inventar când userul editează un device.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE devices
            SET owner      = ?,
                department = ?,
                notes      = ?
            WHERE id = ?
        """, (
            data.get("owner"),
            data.get("department"),
            data.get("notes"),
            device_id
        ))

        conn.commit()
        conn.close()

    # ==========================================================
    # DASHBOARD — statistici
    # ==========================================================

    def get_dashboard_stats(self) -> dict:
        """
        Returnează toate datele necesare pentru dashboard:
        - total/online/offline/unknown
        - distribuție pe tip device (grafic Pie)
        - distribuție pe OS (grafic Bar)
        - număr alerte necitite
        Calculele se fac în SQL Server — mai rapid decât în Python.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Statistici generale
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'online'  THEN 1 ELSE 0 END) AS online,
                SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) AS offline,
                SUM(CASE WHEN status = 'unknown' THEN 1 ELSE 0 END) AS unknown
            FROM devices
        """)
        row = cursor.fetchone()
        stats = {
            "total": row[0] or 0,
            "online": row[1] or 0,
            "offline": row[2] or 0,
            "unknown": row[3] or 0
        }

        # Distribuție după tipul device-ului (Pie chart)
        cursor.execute("""
            SELECT device_type, COUNT(*) AS count
            FROM devices
            WHERE device_type IS NOT NULL
            GROUP BY device_type
            ORDER BY count DESC
        """)
        stats["by_type"] = [
            {"type": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]

        # Distribuție după familia OS (Bar chart "Linux vs Windows")
        cursor.execute("""
            SELECT os_family, COUNT(*) AS count
            FROM devices
            WHERE os_family IS NOT NULL
            GROUP BY os_family
            ORDER BY count DESC
        """)
        stats["by_os"] = [
            {"os": row[0], "count": row[1]}
            for row in cursor.fetchall()
        ]

        # Alerte necitite (iconița din header)
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_read = 0")
        stats["unread_alerts"] = cursor.fetchone()[0]

        conn.close()
        return stats

    # ==========================================================
    # SCAN HISTORY
    # ==========================================================

    def create_scan(self, ip_range: str) -> int:
        """
        Înregistrează începerea unei scanări noi.
        Returnează scan_id — folosit să actualizăm după terminare.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scan_history (ip_range, status, triggered_by)
            VALUES (?, 'running', 'manual')
        """, (ip_range,))

        cursor.execute("SELECT @@IDENTITY")
        scan_id = int(cursor.fetchone()[0])

        conn.commit()
        conn.close()
        return scan_id

    def finish_scan(self, scan_id: int, devices_found: int, status: str = "completed"):
        """
        Marchează scanarea ca terminată.
        Salvează câte device-uri active a găsit.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE scan_history
            SET finished_at   = GETDATE(),
                devices_found = ?,
                status        = ?
            WHERE id = ?
        """, (devices_found, status, scan_id))

        conn.commit()
        conn.close()

    def get_scan_history(self) -> list:
        """Returnează ultimele 20 de scanări, cele mai recente primele."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 20
                id, ip_range, started_at, finished_at,
                devices_found, status, triggered_by
            FROM scan_history
            ORDER BY started_at DESC
        """)

        history = [self._row_to_dict(cursor, row) for row in cursor.fetchall()]
        conn.close()
        return history

    # ==========================================================
    # ALERTS
    # ==========================================================

    def create_alert(self, device_id: int, alert_type: str,
                     message: str, severity: str = "warning"):
        """Creează o alertă nouă."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alerts (device_id, alert_type, message, severity)
            VALUES (?, ?, ?, ?)
        """, (device_id, alert_type, message, severity))

        conn.commit()
        conn.close()

    def get_alerts(self, unread_only: bool = False) -> list:
        """
        Returnează alertele cu detalii despre device.
        unread_only=True  → doar necitite (header notificări)
        unread_only=False → toate (pagina Alerts)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                a.id, a.alert_type, a.message, a.severity,
                a.is_read, a.created_at,
                d.ip_address, d.hostname
            FROM alerts a
            JOIN devices d ON a.device_id = d.id
        """
        if unread_only:
            query += " WHERE a.is_read = 0"
        query += " ORDER BY a.created_at DESC"

        cursor.execute(query)
        alerts = [self._row_to_dict(cursor, row) for row in cursor.fetchall()]
        conn.close()
        return alerts

    def mark_alert_read(self, alert_id: int):
        """Marchează o alertă ca citită (is_read = 1)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET is_read = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()

    # ==========================================================
    # UPTIME LOG
    # ==========================================================

    def log_uptime(self, device_id: int, is_online: bool,
                   response_ms: Optional[int] = None):
        """
        Salvează o verificare de disponibilitate în uptime_log.
        Apelat de monitorul de alerte la fiecare verificare.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO uptime_log (device_id, is_online, response_ms)
            VALUES (?, ?, ?)
        """, (device_id, 1 if is_online else 0, response_ms))

        conn.commit()
        conn.close()


# ============================================================
# INSTANȚĂ GLOBALĂ — importă ACEASTA în restul aplicației
#
# Exemplu de utilizare în alt fișier:
#   from database import db
#   toate_device_urile = db.get_all_devices()
#   db.update_device_status("192.168.1.10", "offline")
# ============================================================
db = DatabaseManager()
