-- ============================================================
-- FISIER 1: create_tables.sql
-- Ce face: Creează toate tabelele bazei de date
-- Unde rulezi: SSMS > New Query > Run (F5)
-- ============================================================

-- Pasul 1: Creează baza de date dacă nu există deja
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DIIP')
BEGIN
    CREATE DATABASE DIIP;
    PRINT '✓ Baza de date DIIP a fost creată.';
END
ELSE
    PRINT '! Baza de date DIIP există deja.';
GO

-- Spune SQL Server să lucreze în DIIP de acum încolo
USE DIIP;
GO

-- ============================================================
-- TABEL 1: devices
-- Scopul: Stochează fiecare dispozitiv descoperit în rețea
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'devices')
BEGIN
    CREATE TABLE devices (

        -- Identificare
        id            INT IDENTITY(1,1) PRIMARY KEY,
        -- IDENTITY = auto-increment (1, 2, 3...) — nu trebuie să îl completezi manual

        ip_address    VARCHAR(15)  NOT NULL UNIQUE,
        -- VARCHAR(15) = maxim 15 caractere (ex: "192.168.100.100")
        -- NOT NULL    = câmpul este obligatoriu
        -- UNIQUE      = nu pot exista 2 device-uri cu același IP

        hostname      VARCHAR(255) NULL,
        -- Numele calculatorului în rețea (ex: DESKTOP-ABC123)
        -- NULL = câmpul este opțional (poate lipsi)

        -- Tipul și sistemul de operare
        device_type   VARCHAR(50)  NULL,
        -- Valorile posibile: Server / Laptop / Router / Printer / Unknown

        os_name       VARCHAR(100) NULL,
        -- Numele complet al OS-ului (ex: Windows 10 Pro, Ubuntu 22.04)

        os_family     VARCHAR(20)  NULL,
        -- Familia OS: Windows / Linux / Cisco / Other
        -- Folosit pentru graficul "Linux vs Windows" din dashboard

        mac_address   VARCHAR(17)  NULL,
        -- Adresa MAC în format AA:BB:CC:DD:EE:FF (17 caractere)

        -- Informații organizaționale (completate manual)
        owner         VARCHAR(100) NULL,
        -- Persoana responsabilă de device (ex: Ion Popescu)

        department    VARCHAR(100) NULL,
        -- Departamentul (ex: IT, HR, Finance, Marketing)

        -- Starea curentă
        status        VARCHAR(20)  NOT NULL DEFAULT 'unknown',
        -- DEFAULT = valoarea pusă automat dacă nu specifici altceva
        -- Valorile posibile: online / offline / unknown

        open_ports    VARCHAR(500) NULL,
        -- Porturile deschise găsite la scanare (ex: "22,80,443,3389")
        -- Stocăm ca text simplu, separate prin virgulă

        -- Timestamps
        last_seen     DATETIME     NULL,
        -- Ultima dată când device-ul a răspuns la ping

        first_seen    DATETIME     NOT NULL DEFAULT GETDATE(),
        -- GETDATE() = data și ora curentă, pusă automat la inserare

        notes         VARCHAR(500) NULL
        -- Observații manuale (ex: "Laptop de rezervă", "Se repară")
    );

    PRINT '✓ Tabel [devices] creat.';
END
ELSE
    PRINT '! Tabel [devices] există deja.';
GO

-- ============================================================
-- TABEL 2: scan_history
-- Scopul: Înregistrează fiecare scanare de rețea efectuată
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'scan_history')
BEGIN
    CREATE TABLE scan_history (
        id              INT IDENTITY(1,1) PRIMARY KEY,

        ip_range        VARCHAR(50)  NOT NULL,
        -- Range-ul scanat (ex: "192.168.1.1-192.168.1.255")

        started_at      DATETIME     NOT NULL DEFAULT GETDATE(),
        -- Când a început scanarea

        finished_at     DATETIME     NULL,
        -- Când s-a terminat (NULL dacă încă rulează)

        devices_found   INT          NOT NULL DEFAULT 0,
        -- Câte hosturi active a găsit scanarea

        status          VARCHAR(20)  NOT NULL DEFAULT 'running',
        -- running = în curs / completed = terminată / failed = eroare

        triggered_by    VARCHAR(100) NULL DEFAULT 'manual'
        -- Cine a declanșat scanarea: manual / scheduled (automat)
    );

    PRINT '✓ Tabel [scan_history] creat.';
END
ELSE
    PRINT '! Tabel [scan_history] există deja.';
GO

-- ============================================================
-- TABEL 3: alerts
-- Scopul: Stochează alertele generate de monitor
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'alerts')
BEGIN
    CREATE TABLE alerts (
        id              INT IDENTITY(1,1) PRIMARY KEY,

        device_id       INT          NOT NULL,
        -- ID-ul device-ului care a generat alerta
        -- Legat prin FOREIGN KEY de tabelul devices

        alert_type      VARCHAR(50)  NOT NULL,
        -- Tipul alertei: offline / back_online / new_device

        message         VARCHAR(500) NOT NULL,
        -- Mesajul alertei (ex: "Server 192.168.1.10 nu răspunde!")

        severity        VARCHAR(20)  NOT NULL DEFAULT 'warning',
        -- Gravitatea: info (albastru) / warning (galben) / critical (roșu)

        is_read         BIT          NOT NULL DEFAULT 0,
        -- BIT = doar 0 sau 1 (ca un boolean)
        -- 0 = alertă necitită (apare în notificări)
        -- 1 = alertă citită

        created_at      DATETIME     NOT NULL DEFAULT GETDATE(),

        -- FOREIGN KEY = legătură între cele două tabele
        -- Dacă ștergi un device, se șterg automat și alertele lui (CASCADE)
        CONSTRAINT FK_alerts_devices
            FOREIGN KEY (device_id)
            REFERENCES devices(id)
            ON DELETE CASCADE
    );

    PRINT '✓ Tabel [alerts] creat.';
END
ELSE
    PRINT '! Tabel [alerts] există deja.';
GO

-- ============================================================
-- TABEL 4: uptime_log
-- Scopul: Ține istoricul de disponibilitate al fiecărui device
--         (folosit pentru graficul de uptime din dashboard)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'uptime_log')
BEGIN
    CREATE TABLE uptime_log (
        id          INT IDENTITY(1,1) PRIMARY KEY,

        device_id   INT         NOT NULL,

        checked_at  DATETIME    NOT NULL DEFAULT GETDATE(),
        -- Momentul exact al verificării

        is_online   BIT         NOT NULL,
        -- 1 = device-ul a răspuns la ping
        -- 0 = device-ul nu a răspuns

        response_ms INT         NULL,
        -- Timpul de răspuns în milisecunde (ex: 12ms)
        -- NULL dacă device-ul e offline

        CONSTRAINT FK_uptime_devices
            FOREIGN KEY (device_id)
            REFERENCES devices(id)
            ON DELETE CASCADE
    );

    PRINT '✓ Tabel [uptime_log] creat.';
END
ELSE
    PRINT '! Tabel [uptime_log] există deja.';
GO

PRINT '';
PRINT '============================================';
PRINT ' Toate tabelele au fost create cu succes!';
PRINT ' Mergi la fisierul 2: create_indexes.sql';
PRINT '============================================';
