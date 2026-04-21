# 🖥️ DIIP — Digital Infrastructure Intelligence Platform

O platformă web **enterprise-ready** pentru descoperirea, inventarierea și monitorizarea automată a infrastructurii IT dintr-o rețea.

> Proiect personal dezvoltat pentru a demonstra competențe în **networking**, **baze de date SQL avansate**, **backend Python** și **monitorizare sisteme**. Inspirat din Nagios — am construit o versiune mai simplă și mai intuitivă.

---

## 📸 Screenshots

### 🔐 Login — Autentificare securizată
<img width="509" height="537" alt="image" src="https://github.com/user-attachments/assets/8d14cd59-50ad-4de1-95e6-1a3f1f80cb4c" />


### Dashboard — Privire de ansamblu
<img width="1918" height="905" alt="image" src="https://github.com/user-attachments/assets/a68ec705-66ef-4a3f-8664-4926ad1274dd" />


### Inventar IT — Toate device-urile din rețea
<img width="1918" height="906" alt="image" src="https://github.com/user-attachments/assets/98d3775e-c260-4417-8cf0-d748d819d39d" />


### Scanare Rețea — Descoperire automată
<img width="1916" height="895" alt="image" src="https://github.com/user-attachments/assets/6e14be41-453c-458a-9ad1-a73bcdeba1f3" />


### Alerte — Monitorizare evenimente
<img width="1917" height="902" alt="image" src="https://github.com/user-attachments/assets/ac358c00-a6f2-4d13-b803-16f60401c295" />


### Audit Logs — Istoricul acțiunilor
<img width="1917" height="901" alt="image" src="https://github.com/user-attachments/assets/36bb2365-a158-447a-b076-f8cb3add71cc" />


### Analytics — CTE și Window Functions
<img width="1917" height="905" alt="image" src="https://github.com/user-attachments/assets/23251417-f00d-46b5-8ee6-bf6e641c256c" />


---

## ✨ Funcționalități

### 🔐 Autentificare & Securitate
- Login/logout cu sesiuni securizate (cookie httpOnly)
- Roluri: **admin** (acces complet) și **viewer** (doar vizualizare)
- Parole hash-uite cu **bcrypt** — niciodată stocate în text clar
- **Audit Logs** — fiecare acțiune înregistrată în SQL Server

### 🔍 Network Discovery
- Scanează automat un range de IP-uri cu **Nmap**
- Detectează hosturi active, sistem de operare și porturi deschise
- Identificare automată tip device (Server/Laptop/Router/Printer)

### 📦 Inventar IT
- Bază de date completă cu toate device-urile din rețea
- Câmpuri editabile: owner, departament, note
- Filtrare după status, tip, departament
- Export **Excel** (colorat) și **CSV**

### 📊 Analytics Dashboard
- Query-uri SQL avansate: **CTE**, **Window Functions**
- **RANK()**, **NTILE()**, **LAG()**, **OVER()** — funcții de analiză
- Grafice: activitate zilnică, distribuție OS, uptime ranking
- Evoluție cumulativă a infrastructurii în timp

### ⚠️ Alerting & Monitoring
- Monitor automat — verificare device-uri la fiecare 5 minute
- Alerte automate pe **email** (Gmail SMTP) când un server cade
- Dashboard cu alerte recente și device-uri offline
- Istoric uptime per device cu grafic de 24h

### 📜 Audit Logs
- Înregistrare completă: login, logout, scanări, editări, exporturi
- Filtrare după user, tip acțiune, status
- Statistici: total acțiuni, login-uri reușite/eșuate

---

## 🛠️ Tech Stack

| Componentă | Tehnologie |
|---|---|
| Backend | Python 3.11, FastAPI |
| Bază de date | Microsoft SQL Server (SSMS) |
| Network scanning | Nmap, python-nmap |
| Autentificare | bcrypt, sessions, cookies |
| Frontend | HTML, Bootstrap 5, Chart.js |
| Template engine | Jinja2 |
| Server | Uvicorn (async) |
| Email | SMTP Gmail |
| Export | openpyxl (Excel), csv |
| Versionare | Git, GitHub |

---

## 📁 Structura proiectului

```
DIIP-Platform/
├── database/
│   ├── 1_create_tables.sql      # Schema principală
│   ├── 2_create_indexes.sql     # Indexuri pentru performanță
│   ├── 3_seed_data.sql          # Date demo
│   ├── 4_auth_schema.sql        # Tabele autentificare
│   └── 5_analytics_queries.sql  # Query-uri CTE + Window Functions
├── templates/
│   ├── base.html                # Template de bază (sidebar, header)
│   ├── login.html               # Pagina de autentificare
│   ├── dashboard.html           # Dashboard principal
│   ├── inventory.html           # Inventar device-uri
│   ├── scan.html                # Scanare rețea
│   ├── alerts.html              # Alerte și notificări
│   ├── audit.html               # Audit logs
│   ├── analytics.html           # Analytics avansat
│   └── device_detail.html       # Detalii device + uptime
├── static/
│   └── style.css                # Dark/Light mode theme
├── screenshots/                 # Screenshots aplicație
├── main.py                      # FastAPI app + toate rutele
├── database.py                  # Conexiunea SQL Server
├── auth.py                      # Autentificare + audit logging
├── scanner.py                   # Network scanner Nmap
├── monitor.py                   # Monitor automat alerte
├── email_service.py             # Email alerts SMTP
├── requirements.txt             # Dependențe Python
└── .env.example                 # Template configurare
```

---

## 🗃️ Schema bazei de date

```
devices       → device-uri descoperite (IP, OS, owner, status)
scan_history  → istoricul scanărilor efectuate
alerts        → alerte generate de monitor
uptime_log    → disponibilitate per device (grafic 24h)
users         → utilizatori platformă (bcrypt passwords)
sessions      → sesiuni active (token-uri)
audit_logs    → jurnal complet al acțiunilor
```

**Query-uri avansate folosite:**
- `CTE (WITH)` — subquery-uri reutilizabile pentru analytics
- `RANK() OVER` — clasament device-uri după uptime
- `NTILE(4) OVER` — împărțire în quartile
- `LAG() OVER` — comparație cu ziua anterioară
- `SUM() OVER()` — running total cumulativ
- `WINDOW FUNCTIONS` cu `PARTITION BY`

---

## 🚀 Instalare și rulare

### Cerințe prealabile

- Python 3.10+
- Microsoft SQL Server + SSMS
- [Nmap](https://nmap.org/download.html) instalat pe sistem
- ODBC Driver 17 for SQL Server

### Pasul 1: Clonează repository-ul

```bash
git clone https://github.com/DumitrascuIoana/DIIP-Platform.git
cd DIIP-Platform
```

### Pasul 2: Instalează dependențele

```bash
pip install -r requirements.txt
```

### Pasul 3: Configurează baza de date

Deschide **SSMS** și rulează în ordine:
```
1. database/1_create_tables.sql
2. database/2_create_indexes.sql
3. database/3_seed_data.sql
4. database/4_auth_schema.sql
```

### Pasul 4: Configurează `.env`

```env
DB_SERVER=localhost
DB_NAME=DIIP
DB_TRUSTED_CONNECTION=Yes
DB_DRIVER=ODBC Driver 17 for SQL Server
EMAIL_SENDER=emailul_tau@gmail.com
EMAIL_PASSWORD=app_password_gmail
EMAIL_RECEIVER=emailul_tau@gmail.com
EMAIL_ENABLED=True
```

### Pasul 5: Pornește aplicația

```bash
python -m uvicorn main:app --reload --port 8080
```

Deschide: **http://127.0.0.1:8080**

### Conturi demo

| Username | Parolă | Rol |
|----------|--------|-----|
| admin | Admin1234! | Administrator |
| viewer | Admin1234! | Viewer |

---

## 🔌 API Endpoints

| Method | Endpoint | Descriere |
|--------|----------|-----------|
| POST | `/api/auth/login` | Autentificare |
| POST | `/api/auth/logout` | Deconectare |
| GET | `/api/dashboard/stats` | Statistici dashboard |
| GET | `/api/devices` | Lista device-uri |
| PUT | `/api/devices/{id}` | Actualizează device |
| POST | `/api/scan` | Pornește scanare |
| GET | `/api/alerts` | Lista alerte |
| GET | `/api/audit/logs` | Audit logs |
| GET | `/api/analytics/kpi` | KPI-uri analytics |
| GET | `/api/export/excel` | Export Excel |
| GET | `/api/export/csv` | Export CSV |

---

## 👩‍💻 Autor

**Ioana Dumitrascu**
- GitHub: [@DumitrascuIoana](https://github.com/DumitrascuIoana)

---

## 📝 Licență

Proiect open-source — liber de folosit și modificat.
