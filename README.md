# 🖥️ DIIP — Digital Infrastructure Intelligence Platform

O platformă web enterprise-ready pentru descoperirea, inventarierea și monitorizarea automată a infrastructurii IT dintr-o rețea.

Proiect personal dezvoltat pentru a demonstra competențe în networking, baze de date SQL avansate, backend Python și monitorizare sisteme. Inspirat din Nagios — am construit o versiune mai simplă și mai intuitivă.
---

## 📸 Screenshots

### Dashboard — Privire de ansamblu
<img width="1918" height="907" alt="image" src="https://github.com/user-attachments/assets/59931b16-0897-4c4d-9301-0610a2f80846" />


### Inventar IT — Toate device-urile din rețea
<img width="1919" height="900" alt="image" src="https://github.com/user-attachments/assets/8bee0ae4-c487-4ffb-8d97-d218f190190f" />


### Scanare Rețea — Descoperire automată
<img width="1915" height="897" alt="image" src="https://github.com/user-attachments/assets/b052d778-ed36-4566-8d7f-2a6293a17071" />


### Alerte — Monitorizare evenimente
<img width="1918" height="907" alt="image" src="https://github.com/user-attachments/assets/1162c765-b723-463c-80a7-b3f4ab88604a" />


### Audit Logs  — Istoricul acțiunilor
<img width="1915" height="904" alt="image" src="https://github.com/user-attachments/assets/e38dd8fc-e594-4228-bf83-64865dd1966c" />



### Analitycs  — CTE și Window Functions
<img width="1918" height="900" alt="image" src="https://github.com/user-attachments/assets/cfe75955-4d16-4c5d-bc5e-aa1ee382e3ed" />

----

## ✨ Funcționalități

**Autentificare & Securitate**

Login/logout cu sesiuni securizate (cookie httpOnly)
Roluri: admin (acces complet) și viewer (doar vizualizare)
Parole hash-uite cu bcrypt — niciodată stocate în text clar
Audit Logs — fiecare acțiune înregistrată în SQL Server

**🔍 Network Discovery**

Scanează automat un range de IP-uri cu Nmap
Detectează hosturi active, sistem de operare și porturi deschise
Identificare automată tip device (Server/Laptop/Router/Printer)

**📦 Inventar IT**

Bază de date completă cu toate device-urile din rețea
Câmpuri editabile: owner, departament, note
Filtrare după status, tip, departament
Export Excel (colorat) și CSV

**📊 Analytics Dashboard**

Query-uri SQL avansate: CTE, Window Functions
RANK(), NTILE(), LAG(), OVER() — funcții de analiză
Grafice: activitate zilnică, distribuție OS, uptime ranking
Evoluție cumulativă a infrastructurii în timp

**⚠️ Alerting & Monitoring**

Monitor automat — verificare device-uri la fiecare 5 minute
Alerte automate pe email (Gmail SMTP) când un server cade
Dashboard cu alerte recente și device-uri offline
Istoric uptime per device cu grafic de 24h

**📜 Audit Logs**

Înregistrare completă: login, logout, scanări, editări, exporturi
Filtrare după user, tip acțiune, status
Statistici: total acțiuni, login-uri reușite/eșuate
---

## 🛠️ Tech Stack

| Componentă | Tehnologie |
|---|---|
| Backend | Python, FastAPI |
| Bază de date | Microsoft SQL Server (SSMS) |
| Network scanning | Nmap, python-nmap |
| Frontend | HTML, Bootstrap 5, Chart.js |
| Template engine | Jinja2 |
| Server | Uvicorn |
| Versionare | Git, GitHub |

---

## 📁 Structura proiectului

```
DIIP-Platform/
├── database/
│   ├── 1_create_tables.sql    # Schema bazei de date
│   ├── 2_create_indexes.sql   # Indexuri pentru performanță
│   └── 3_seed_data.sql        # Date de test
├── templates/
│   ├── base.html              # Template de bază (sidebar, header)
│   ├── dashboard.html         # Pagina principală cu grafice
│   ├── inventory.html         # Inventar device-uri
│   ├── scan.html              # Scanare rețea
│   └── alerts.html            # Alerte și notificări
├── static/
│   └── style.css              # Stiluri CSS (tema dark)
├── screenshots/               # Screenshot-uri aplicație
├── main.py                    # Aplicația FastAPI + toate rutele
├── database.py                # Conexiunea și operațiile SQL Server
├── scanner.py                 # Network scanner cu Nmap
├── monitor.py                 # Monitor automat de alerte
├── requirements.txt           # Dependențe Python
└── .env.example               # Template configurare
```

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

### Pasul 2: Instalează dependențele Python

```bash
pip install -r requirements.txt
```

### Pasul 3: Configurează baza de date

Deschide **SSMS** și rulează fișierele SQL în ordine:
```
1. database/1_create_tables.sql   ← creează tabelele
2. database/2_create_indexes.sql  ← adaugă indexurile
3. database/3_seed_data.sql       ← inserează date demo
```

### Pasul 4: Configurează conexiunea

Creează fișierul `.env` în folderul proiectului:
```env
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=DIIP
DB_TRUSTED_CONNECTION=Yes
DB_DRIVER=ODBC Driver 17 for SQL Server
```

### Pasul 5: Pornește aplicația

```bash
python -m uvicorn main:app --reload --port 8080
```

Deschide browserul la: **http://127.0.0.1:8080** 🎉

---

## 📊 Schema bazei de date

```
devices       → toate device-urile descoperite în rețea
scan_history  → istoricul scanărilor efectuate
alerts        → alertele generate de monitor
uptime_log    → istoricul de disponibilitate per device
```

---

## 🔌 API Endpoints

| Method | Endpoint | Descriere |
|--------|----------|-----------|
| GET | `/api/dashboard/stats` | Statistici pentru dashboard |
| GET | `/api/devices` | Lista tuturor device-urilor |
| PUT | `/api/devices/{id}` | Actualizează info device |
| POST | `/api/scan` | Pornește o scanare nouă |
| GET | `/api/scan/history` | Istoricul scanărilor |
| GET | `/api/alerts` | Lista alertelor |
| PUT | `/api/alerts/{id}/read` | Marchează alertă citită |
| GET | `/api/health` | Status aplicație |

---

## 👩‍💻 Autor

**Ioana Dumitrascu**
- GitHub: [@DumitrascuIoana](https://github.com/DumitrascuIoana)

---

## 📝 Licență

Proiect open-source — liber de folosit și modificat.
