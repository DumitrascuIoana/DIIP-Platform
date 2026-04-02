# 🖥️ DIIP — Digital Infrastructure Intelligence Platform

O platformă web pentru descoperirea, inventarierea și monitorizarea automată a infrastructurii IT dintr-o rețea.

> Proiect personal dezvoltat pentru a demonstra competențe în **networking**, **baze de date**, **backend Python** și **monitorizare sisteme**.

---

## 📸 Screenshots

### Dashboard — Privire de ansamblu
<img width="1916" height="984" alt="image" src="https://github.com/user-attachments/assets/aeb35c62-eb9a-4a6d-af50-16c46a6f1f20" />


### Inventar IT — Toate device-urile din rețea
<img width="1917" height="973" alt="image" src="https://github.com/user-attachments/assets/532537c3-e9cd-4199-9f79-c082cd542d3e" />



### Scanare Rețea — Descoperire automată
<img width="1912" height="977" alt="image" src="https://github.com/user-attachments/assets/284941e7-3323-4622-997a-487acdd51fc6" />



### Alerte — Monitorizare evenimente
<img width="1915" height="975" alt="image" src="https://github.com/user-attachments/assets/df79b6f2-fce9-4e08-9159-d11918481242" />



---

## ✨ Funcționalități

- 🔍 **Network Scanner** — scanează automat un range de IP-uri și detectează hosturi active
- 🖥️ **Identificare device-uri** — detectează tipul (Server/Laptop/Router), OS și porturi deschise
- 📦 **Inventar IT** — bază de date completă cu toate device-urile din rețea
- 📊 **Dashboard** — grafice în timp real (tip device, OS distribution, status rețea)
- ⚠️ **Alerting automat** — notificări când un server iese offline
- 🔄 **Monitorizare continuă** — verificare automată la fiecare 5 minute

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

**Ionut Dumitrascu**
- GitHub: [@DumitrascuIoana](https://github.com/DumitrascuIoana)

---

## 📝 Licență

Proiect open-source — liber de folosit și modificat.
