# ============================================================
# monitor.py
# Ce face: Monitorizează automat device-urile din baza de date
#
# Cum funcționează:
#   1. La fiecare X minute, ia toate device-urile din DB
#   2. Face ping la fiecare IP
#   3. Dacă un device nu răspunde → creează alertă "offline"
#   4. Dacă un device revenea online → creează alertă "back_online"
#   5. Salvează istoricul în uptime_log
#
# Rulează în fundal (background task) odată cu aplicația.
# ============================================================

import asyncio
import time
from datetime import datetime
from database import db
from scanner import NetworkScanner


# ============================================================
# CLASA AlertMonitor
# ============================================================
class AlertMonitor:

    def __init__(self, check_interval_seconds: int = 300):
        """
        check_interval_seconds = cât de des verifică device-urile
        Default: 300 secunde = 5 minute
        La interviu poți spune că e configurabil.
        """
        self.interval = check_interval_seconds
        self.scanner = NetworkScanner()

        # Dicționar care ține minte statusul anterior al fiecărui device
        # { "192.168.1.10": "online", "192.168.1.11": "offline", ... }
        # Folosit să detectăm SCHIMBĂRILE de status
        self.previous_status = {}

        print(f"[MONITOR] Inițializat. Verificare la fiecare {self.interval}s.")

    # ==========================================================
    # METODA PRINCIPALĂ: run
    # Rulează la nesfârșit în background
    # ==========================================================
    async def run(self):
        """
        Loop infinit care verifică device-urile periodic.
        Este un coroutine async — rulează în background
        fără să blocheze restul aplicației.
        """
        print("[MONITOR] Pornit. Aștept prima verificare...")

        while True:
            try:
                await self.check_all_devices()
            except Exception as e:
                print(f"[MONITOR ERROR] Eroare la verificare: {e}")

            # Așteptăm intervalul configurat înainte de următoarea verificare
            # asyncio.sleep = pauză async (nu blochează aplicația)
            print(f"[MONITOR] Următoarea verificare în {self.interval}s...")
            await asyncio.sleep(self.interval)

    # ==========================================================
    # METODA: check_all_devices
    # Verifică toate device-urile o dată
    # ==========================================================
    async def check_all_devices(self):
        """
        Ia toate device-urile din DB și verifică fiecare prin ping.
        Detectează schimbările de status și creează alerte.
        """
        print(f"[MONITOR] [{datetime.now().strftime('%H:%M:%S')}] Verificare device-uri...")

        # Luăm toate device-urile din baza de date
        devices = db.get_all_devices()

        if not devices:
            print("[MONITOR] Nu există device-uri în DB.")
            return

        online_count = 0
        offline_count = 0

        for device in devices:
            ip = device["ip_address"]
            device_id = device["id"]

            # Facem ping la device
            # run_in_executor = rulăm funcția sincronă (ping)
            # într-un thread separat ca să nu blocheze async loop-ul
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.scanner.ping_host,
                ip
            )

            is_online = result["online"]
            response_ms = result["response_ms"]

            # Salvăm verificarea în uptime_log
            db.log_uptime(device_id, is_online, response_ms)

            if is_online:
                online_count += 1
                new_status = "online"
            else:
                offline_count += 1
                new_status = "offline"

            # Actualizăm statusul în baza de date
            db.update_device_status(ip, new_status)

            # ──────────────────────────────────────────────────
            # DETECTĂM SCHIMBĂRILE DE STATUS
            # Creăm alertă DOAR când statusul se SCHIMBĂ
            # (nu la fiecare verificare — am avea prea multe alerte)
            # ──────────────────────────────────────────────────
            previous = self.previous_status.get(ip)

            if previous is None:
                # Prima verificare — doar reținem statusul, fără alertă
                self.previous_status[ip] = new_status

            elif previous == "online" and new_status == "offline":
                # Device era online → a ieșit offline → ALERTĂ!
                self._create_offline_alert(device, device_id)
                self.previous_status[ip] = new_status
                print(f"[MONITOR] ⚠ OFFLINE: {ip} ({device.get('hostname', 'unknown')})")

            elif previous == "offline" and new_status == "online":
                # Device era offline → a revenit online → notificare
                self._create_back_online_alert(device, device_id)
                self.previous_status[ip] = new_status
                print(f"[MONITOR] ✓ BACK ONLINE: {ip} ({device.get('hostname', 'unknown')})")

            else:
                # Statusul nu s-a schimbat — actualizăm doar dicționarul
                self.previous_status[ip] = new_status

        print(f"[MONITOR] Verificare completă: {online_count} online, {offline_count} offline.")

    # ==========================================================
    # METODE HELPER pentru crearea alertelor
    # ==========================================================

    def _create_offline_alert(self, device: dict, device_id: int):
        """
        Creează o alertă când un device iese offline.
        Severitatea depinde de tipul device-ului:
          - Server offline → CRITICAL (roșu)
          - Altceva offline → WARNING (galben)
        """
        ip = device["ip_address"]
        hostname = device.get("hostname") or ip
        dtype = device.get("device_type", "Device")

        # Serverele sunt mai critice decât laptopurile
        if dtype == "Server":
            severity = "critical"
            message = f"CRITIC: Serverul {hostname} ({ip}) nu răspunde!"
        else:
            severity = "warning"
            message = f"{dtype} {hostname} ({ip}) este offline."

        db.create_alert(
            device_id=device_id,
            alert_type="offline",
            message=message,
            severity=severity
        )

    def _create_back_online_alert(self, device: dict, device_id: int):
        """
        Creează o notificare când un device revine online.
        Severitatea e întotdeauna 'info' (albastru — veste bună).
        """
        ip = device["ip_address"]
        hostname = device.get("hostname") or ip
        dtype = device.get("device_type", "Device")

        message = f"{dtype} {hostname} ({ip}) a revenit online."

        db.create_alert(
            device_id=device_id,
            alert_type="back_online",
            message=message,
            severity="info"
        )

    # ==========================================================
    # METODĂ UTILĂ: check_single_device
    # Verifică un singur device (apelat din API la cerere)
    # ==========================================================
    def check_single_device(self, ip: str) -> dict:
        """
        Verifică imediat un singur device și returnează statusul.
        Apelat din API când userul cere refresh manual.
        """
        result = self.scanner.ping_host(ip)
        is_online = result["online"]

        db.update_device_status(ip, "online" if is_online else "offline")

        return {
            "ip": ip,
            "online": is_online,
            "response_ms": result["response_ms"],
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# ============================================================
# TEST RAPID — rulezi direct fișierul:
#   python monitor.py
# Verifică localhost și primul device din DB (dacă există)
# ============================================================
if __name__ == "__main__":
    import asyncio

    monitor = AlertMonitor(check_interval_seconds=30)

    # Test simplu: verifică un singur IP
    print("\n--- Test check_single_device ---")
    result = monitor.check_single_device("127.0.0.1")
    print(f"Rezultat: {result}")

    # Decomentează pentru a porni monitorul complet (loop infinit):
    # print("\n--- Pornesc monitorul complet ---")
    # asyncio.run(monitor.run())