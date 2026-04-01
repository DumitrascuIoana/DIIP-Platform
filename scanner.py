# ============================================================
# scanner.py
# Ce face: Scanează rețeaua și salvează device-urile în DB
#
# Pași:
#   1. Primește un IP range (ex: 192.168.1.1-192.168.1.255)
#   2. Rulează Nmap să găsească hosturi active
#   3. Detectează OS, hostname, porturi deschise
#   4. Salvează/actualizează în baza de date
#   5. Returnează rezultatele scanării
# ============================================================

import nmap
import socket
import time
from database import db


# ============================================================
# CLASA NetworkScanner
# ============================================================
class NetworkScanner:

    def __init__(self):
        # Creăm instanța Nmap — aceasta comunică cu programul
        # Nmap instalat pe calculatorul tău
        try:
            self.scanner = nmap.PortScanner()
            print("[SCANNER] Nmap inițializat cu succes.")
        except nmap.PortScannerError as e:
            print(f"[SCANNER ERROR] Nmap nu a fost găsit: {e}")
            raise

    # ==========================================================
    # METODA PRINCIPALĂ: scan_network
    # Aceasta e funcția pe care o apelezi pentru o scanare completă
    # ==========================================================
    def scan_network(self, ip_range: str) -> dict:
        """
        Scanează un range de IP-uri și salvează rezultatele în DB.

        Parametru:
            ip_range: ex: "192.168.1.1-254" sau "192.168.1.0/24"

        Returnează:
            dict cu: devices găsite, durată, scan_id
        """

        print(f"[SCANNER] Încep scanarea: {ip_range}")
        start_time = time.time()

        # Înregistrăm scanarea în baza de date (status: running)
        scan_id = db.create_scan(ip_range)

        devices_found = []

        try:
            # ──────────────────────────────────────────────────
            # ARGUMENTELE NMAP explicate:
            # -sn  = Ping Scan (verifică doar dacă hostul e activ,
            #        fără să scaneze porturi — mai rapid)
            # -O   = detectare sistem de operare
            # -sV  = detectare versiuni servicii
            # --open = afișează doar porturile deschise
            # -T4  = viteză scanare (T1=lent ... T5=agresiv)
            #        T4 = rapid dar fără să suprasolicite rețeaua
            # ──────────────────────────────────────────────────
            self.scanner.scan(
                hosts=ip_range,
                arguments="-sn -T4"
                # Începem cu ping scan (simplu și rapid)
                # După ce confirmăm că merge, putem adăuga -O -sV
            )

            # Iterăm prin fiecare host găsit de Nmap
            for host in self.scanner.all_hosts():

                # Verificăm că hostul e activ (up)
                if self.scanner[host].state() == "up":

                    # Extragem informațiile despre device
                    device_info = self._extract_device_info(host)

                    # Salvăm în baza de date (upsert)
                    device_id = db.upsert_device(device_info)
                    device_info["id"] = device_id

                    devices_found.append(device_info)
                    print(f"[SCANNER] Găsit: {host} ({device_info.get('hostname', 'unknown')})")

            # Marcăm scanarea ca terminată în DB
            db.finish_scan(scan_id, len(devices_found), "completed")

        except Exception as e:
            print(f"[SCANNER ERROR] Eroare la scanare: {e}")
            db.finish_scan(scan_id, 0, "failed")
            raise

        duration = round(time.time() - start_time, 2)
        print(f"[SCANNER] Scanare completă: {len(devices_found)} device-uri în {duration}s")

        return {
            "scan_id":       scan_id,
            "ip_range":      ip_range,
            "devices_found": len(devices_found),
            "duration_sec":  duration,
            "devices":       devices_found
        }

    # ==========================================================
    # METODA: scan_with_details
    # Scanare completă cu detectare OS și porturi
    # Durează mai mult dar oferă mai multe informații
    # ==========================================================
    def scan_with_details(self, ip_range: str) -> dict:
        """
        Scanare avansată cu detectare OS și porturi deschise.
        Durează mai mult decât scan_network (2-5 minute).
        Necesită Nmap rulat ca Administrator pentru detectare OS.
        """
        print(f"[SCANNER] Scanare detaliată: {ip_range}")
        start_time = time.time()
        scan_id    = db.create_scan(ip_range)
        devices_found = []

        try:
            # -sV = detectare versiuni servicii (ce rulează pe porturi)
            # -O  = detectare OS (necesită privilegii admin)
            # --top-ports 20 = scanează cele mai comune 20 porturi
            self.scanner.scan(
                hosts=ip_range,
                arguments="-sV -O --top-ports 20 -T4"
            )

            for host in self.scanner.all_hosts():
                if self.scanner[host].state() == "up":
                    device_info = self._extract_device_info_detailed(host)
                    device_id   = db.upsert_device(device_info)
                    device_info["id"] = device_id
                    devices_found.append(device_info)
                    print(f"[SCANNER] Detalii: {host} | OS: {device_info.get('os_name', '?')} | Porturi: {device_info.get('open_ports', '?')}")

            db.finish_scan(scan_id, len(devices_found), "completed")

        except Exception as e:
            print(f"[SCANNER ERROR] {e}")
            db.finish_scan(scan_id, 0, "failed")
            raise

        duration = round(time.time() - start_time, 2)

        return {
            "scan_id":       scan_id,
            "ip_range":      ip_range,
            "devices_found": len(devices_found),
            "duration_sec":  duration,
            "devices":       devices_found
        }

    # ==========================================================
    # METODA INTERNĂ: _extract_device_info
    # Extrage informații de bază despre un host (ping scan)
    # ==========================================================
    def _extract_device_info(self, host: str) -> dict:
        """
        Extrage informațiile de bază despre un host activ.
        Folosit după ping scan (scan_network).
        """

        # Încercăm să obținem hostname-ul prin DNS reverse lookup
        hostname = self._get_hostname(host)

        # Hostname-ul ne ajută să ghicim tipul device-ului
        device_type = self._guess_device_type(hostname, host)

        return {
            "ip_address":  host,
            "hostname":    hostname,
            "device_type": device_type,
            "os_name":     None,       # nu știm fără -O
            "os_family":   None,
            "mac_address": self._get_mac(host),
            "status":      "online",
            "open_ports":  None        # nu știm fără port scan
        }

    # ==========================================================
    # METODA INTERNĂ: _extract_device_info_detailed
    # Extrage informații complete despre un host (scanare detaliată)
    # ==========================================================
    def _extract_device_info_detailed(self, host: str) -> dict:
        """
        Extrage informații complete: OS, porturi, hostname.
        Folosit după scanarea detaliată (scan_with_details).
        """
        hostname = self._get_hostname(host)

        # ── Detectare OS ──────────────────────────────────────
        os_name   = None
        os_family = None

        if "osmatch" in self.scanner[host]:
            os_matches = self.scanner[host]["osmatch"]
            if os_matches:
                # Luăm primul rezultat (cel mai probabil)
                best_match = os_matches[0]
                os_name    = best_match.get("name")
                os_family  = self._get_os_family(os_name)

        # ── Detectare porturi deschise ────────────────────────
        open_ports = []
        for protocol in self.scanner[host].all_protocols():
            ports = self.scanner[host][protocol].keys()
            for port in ports:
                state = self.scanner[host][protocol][port]["state"]
                if state == "open":
                    open_ports.append(str(port))

        open_ports_str = ",".join(open_ports) if open_ports else None

        # ── Ghicim tipul device-ului ──────────────────────────
        device_type = self._guess_device_type_advanced(
            hostname, host, open_ports, os_name
        )

        return {
            "ip_address":  host,
            "hostname":    hostname,
            "device_type": device_type,
            "os_name":     os_name,
            "os_family":   os_family,
            "mac_address": self._get_mac(host),
            "status":      "online",
            "open_ports":  open_ports_str
        }

    # ==========================================================
    # METODE HELPER (ajutătoare)
    # ==========================================================

    def _get_hostname(self, host: str) -> str | None:
        """
        Încearcă să obțină hostname-ul unui IP prin DNS.
        Dacă DNS-ul nu știe → returnează None.
        """
        try:
            hostname = socket.gethostbyaddr(host)[0]
            return hostname
        except (socket.herror, socket.gaierror):
            return None

    def _get_mac(self, host: str) -> str | None:
        """
        Extrage adresa MAC dacă Nmap a găsit-o.
        Funcționează doar pentru device-uri în aceeași subrețea.
        """
        try:
            if "addresses" in self.scanner[host]:
                return self.scanner[host]["addresses"].get("mac")
        except Exception:
            pass
        return None

    def _get_os_family(self, os_name: str | None) -> str | None:
        """
        Din numele OS-ului detectat, extrage familia:
        Windows / Linux / Cisco / Other
        """
        if not os_name:
            return None

        os_lower = os_name.lower()

        if "windows" in os_lower:
            return "Windows"
        elif any(x in os_lower for x in ["linux", "ubuntu", "debian", "centos", "fedora", "red hat"]):
            return "Linux"
        elif any(x in os_lower for x in ["cisco", "ios"]):
            return "Cisco"
        elif any(x in os_lower for x in ["mac", "darwin", "macos"]):
            return "Other"
        else:
            return "Other"

    def _guess_device_type(self, hostname: str | None, ip: str) -> str:
        """
        Ghicește tipul device-ului din hostname și IP.
        Folosit pentru ping scan (fără informații OS/porturi).
        """
        if not hostname:
            # IP-urile .1 sunt de obicei gateway/router
            if ip.endswith(".1") or ip.endswith(".254"):
                return "Router"
            return "Unknown"

        h = hostname.lower()

        if any(x in h for x in ["router", "gateway", "gw", "cisco", "switch"]):
            return "Router"
        elif any(x in h for x in ["srv", "server", "svr", "dc", "nas"]):
            return "Server"
        elif any(x in h for x in ["printer", "print", "hp", "canon", "epson"]):
            return "Printer"
        elif any(x in h for x in ["laptop", "notebook", "pc", "desktop", "win", "mac"]):
            return "Laptop"
        else:
            return "Unknown"

    def _guess_device_type_advanced(self, hostname: str | None,
                                     ip: str,
                                     open_ports: list,
                                     os_name: str | None) -> str:
        """
        Ghicește tipul device-ului folosind mai multe surse:
        hostname + porturi deschise + OS detectat.
        Mai precis decât _guess_device_type.
        """
        ports_set = set(int(p) for p in open_ports if p.isdigit())

        # Porturi tipice pentru routere/switch-uri
        if {80, 443, 22} <= ports_set and (not os_name or "cisco" in (os_name or "").lower()):
            return "Router"

        # Porturi tipice pentru imprimante
        if any(p in ports_set for p in [9100, 515, 631]):
            return "Printer"

        # Server: are porturi de servicii web/BD/SSH
        if any(p in ports_set for p in [80, 443, 3306, 5432, 1433, 8080]):
            return "Server"

        # Remote Desktop = Laptop/Workstation Windows
        if 3389 in ports_set:
            return "Laptop"

        # Fallback la hostname
        return self._guess_device_type(hostname, ip)

    # ==========================================================
    # METODĂ UTILĂ: ping_host
    # Verifică rapid dacă un singur host răspunde
    # Folosită de monitorul de alerte
    # ==========================================================
    def ping_host(self, ip: str) -> dict:
        """
        Verifică dacă un singur IP răspunde la ping.
        Returnează: {'online': True/False, 'response_ms': 12}
        Folosit de monitor.py pentru verificări periodice.
        """
        try:
            self.scanner.scan(hosts=ip, arguments="-sn -T4")
            is_online = (
                ip in self.scanner.all_hosts() and
                self.scanner[ip].state() == "up"
            )

            # Extragem timpul de răspuns dacă există
            response_ms = None
            try:
                latency = self.scanner[ip]["status"].get("reason_ttl")
                if latency:
                    response_ms = int(latency)
            except Exception:
                pass

            return {"online": is_online, "response_ms": response_ms}

        except Exception as e:
            print(f"[SCANNER] Ping eșuat pentru {ip}: {e}")
            return {"online": False, "response_ms": None}


# ============================================================
# TEST RAPID — rulezi direct fișierul să verifici că merge:
#   python scanner.py
# ============================================================
if __name__ == "__main__":
    scanner = NetworkScanner()

    # Testăm ping pe localhost (ar trebui să fie întotdeauna online)
    print("\n--- Test ping localhost ---")
    result = scanner.ping_host("127.0.0.1")
    print(f"Localhost online: {result['online']}")

    # Decomentează linia de mai jos pentru a testa o scanare reală
    # Înlocuiește cu range-ul rețelei tale (găsești cu ipconfig)
    # result = scanner.scan_network("192.168.1.1-10")
    # print(f"Găsite: {result['devices_found']} device-uri")
