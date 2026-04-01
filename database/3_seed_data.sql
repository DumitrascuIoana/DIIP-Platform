-- ============================================================
-- FISIER 3: seed_data.sql
-- Ce face: Inserează date de test ca să ai ceva de văzut
--          în dashboard de la început (DEMO data)
-- Unde rulezi: SSMS > New Query > Run (F5)
--              (după fisierele 1 și 2)
-- ============================================================

USE DIIP;
GO

-- Ștergem datele vechi înainte să inserăm (evităm duplicate)
-- TRUNCATE = șterge tot din tabel, resetează IDENTITY la 1
-- Ordinea contează: întâi tabelele cu FK, apoi cele principale
DELETE FROM uptime_log;
DELETE FROM alerts;
DELETE FROM scan_history;
DELETE FROM devices;

-- Resetăm contoarele IDENTITY la 1
DBCC CHECKIDENT ('uptime_log',   RESEED, 0);
DBCC CHECKIDENT ('alerts',       RESEED, 0);
DBCC CHECKIDENT ('scan_history', RESEED, 0);
DBCC CHECKIDENT ('devices',      RESEED, 0);

PRINT '✓ Date vechi șterse. Se inserează date de test...';
GO

-- ============================================================
-- DATE DE TEST: devices
-- ============================================================
INSERT INTO devices
    (ip_address, hostname, device_type, os_name, os_family,
     mac_address, owner, department, status, open_ports, last_seen, notes)
VALUES
-- Routere / Gateway
('192.168.1.1',  'gateway-main',   'Router',  'Cisco IOS 15.2',    'Cisco',
 'A1:B2:C3:D4:E5:F6', NULL,           'IT',        'online',  '80,443,22',
 GETDATE(), 'Gateway principal al rețelei'),

-- Servere
('192.168.1.10', 'WIN-SERVER01',   'Server',  'Windows Server 2019','Windows',
 'B2:C3:D4:E5:F6:A1', 'Ion Popescu',  'IT',        'online',  '80,443,3389,8080',
 GETDATE(), 'Server web principal'),

('192.168.1.11', 'ubuntu-srv-01',  'Server',  'Ubuntu 22.04 LTS',  'Linux',
 'C3:D4:E5:F6:A1:B2', 'Maria Ionescu','IT',        'online',  '22,80,443,3306',
 GETDATE(), 'Server baza de date MySQL'),

('192.168.1.12', 'ubuntu-srv-02',  'Server',  'Ubuntu 20.04 LTS',  'Linux',
 'D4:E5:F6:A1:B2:C3', 'Maria Ionescu','IT',        'offline', '22,8080',
 DATEADD(minute, -45, GETDATE()), 'Server de backup — verificare necesară!'),

('192.168.1.13', 'WIN-SERVER02',   'Server',  'Windows Server 2022','Windows',
 'E5:F6:A1:B2:C3:D4', 'Ion Popescu',  'IT',        'online',  '80,443,3389',
 GETDATE(), 'Server Active Directory'),

-- Laptopuri / Workstations
('192.168.1.20', 'LAPTOP-HR-01',   'Laptop',  'Windows 11 Pro',    'Windows',
 'F6:A1:B2:C3:D4:E5', 'Ana Dumitrescu','HR',       'online',  '3389',
 GETDATE(), NULL),

('192.168.1.21', 'LAPTOP-HR-02',   'Laptop',  'Windows 10 Pro',    'Windows',
 'A1:B2:C3:D4:E5:F7', 'Radu Gheorghe', 'HR',       'online',  '3389',
 GETDATE(), NULL),

('192.168.1.22', 'LAPTOP-FIN-01',  'Laptop',  'Windows 11 Pro',    'Windows',
 'B2:C3:D4:E5:F7:A1', 'Elena Stan',   'Finance',   'offline', '3389',
 DATEADD(hour, -2, GETDATE()), 'Utilizatoare în concediu'),

('192.168.1.23', 'macbook-dev-01', 'Laptop',  'macOS Ventura 13',  'Other',
 'C3:D4:E5:F7:A1:B2', 'Andrei Marin',  'Development','online', '22,8080',
 GETDATE(), 'MacBook Pro Dev Team'),

('192.168.1.24', 'ubuntu-dev-01',  'Laptop',  'Ubuntu 22.04 LTS',  'Linux',
 'D4:E5:F7:A1:B2:C3', 'Cristina Popa', 'Development','online', '22,3000,8080',
 GETDATE(), NULL),

-- Imprimante
('192.168.1.50', 'printer-hr',     'Printer', NULL,                'Other',
 'E5:F7:A1:B2:C3:D4', NULL,           'HR',        'online',  '9100,515',
 GETDATE(), 'Imprimantă HP HP LaserJet HR'),

('192.168.1.51', 'printer-fin',    'Printer', NULL,                'Other',
 'F7:A1:B2:C3:D4:E5', NULL,           'Finance',   'offline', '9100',
 DATEADD(hour, -5, GETDATE()), 'Imprimantă Finance — cartus epuizat'),

-- Device necunoscut (descoperit la scanare, neidentificat)
('192.168.1.99', NULL,             'Unknown', NULL,                NULL,
 NULL,                NULL,           NULL,        'unknown', NULL,
 DATEADD(minute, -10, GETDATE()), 'Device neidentificat — verificare necesară');

PRINT '✓ Date devices inserate (13 dispozitive).';
GO

-- ============================================================
-- DATE DE TEST: scan_history
-- ============================================================
INSERT INTO scan_history (ip_range, started_at, finished_at, devices_found, status, triggered_by)
VALUES
('192.168.1.1-192.168.1.255',
 DATEADD(day, -1, GETDATE()), DATEADD(day, -1, DATEADD(minute, 3, GETDATE())),
 11, 'completed', 'manual'),

('192.168.1.1-192.168.1.255',
 DATEADD(hour, -12, GETDATE()), DATEADD(hour, -12, DATEADD(minute, 4, GETDATE())),
 12, 'completed', 'scheduled'),

('192.168.1.1-192.168.1.255',
 DATEADD(hour, -1, GETDATE()), DATEADD(minute, -57, GETDATE()),
 13, 'completed', 'manual');

PRINT '✓ Date scan_history inserate (3 scanări).';
GO

-- ============================================================
-- DATE DE TEST: alerts
-- ============================================================
-- Luăm ID-urile device-urilor offline ca să le referențiem corect
DECLARE @id_ubuntu_srv_02 INT = (SELECT id FROM devices WHERE ip_address = '192.168.1.12');
DECLARE @id_laptop_fin    INT = (SELECT id FROM devices WHERE ip_address = '192.168.1.22');
DECLARE @id_printer_fin   INT = (SELECT id FROM devices WHERE ip_address = '192.168.1.51');
DECLARE @id_unknown       INT = (SELECT id FROM devices WHERE ip_address = '192.168.1.99');

INSERT INTO alerts (device_id, alert_type, message, severity, is_read, created_at)
VALUES
-- Alertă critică: server offline
(@id_ubuntu_srv_02, 'offline',
 'CRITIC: Server ubuntu-srv-02 (192.168.1.12) nu răspunde de 45 minute!',
 'critical', 0, DATEADD(minute, -45, GETDATE())),

-- Alertă warning: laptop offline
(@id_laptop_fin, 'offline',
 'Laptop LAPTOP-FIN-01 (192.168.1.22) este offline de 2 ore.',
 'warning', 0, DATEADD(hour, -2, GETDATE())),

-- Alertă info: imprimantă offline (mai puțin urgentă)
(@id_printer_fin, 'offline',
 'Imprimanta printer-fin (192.168.1.51) nu răspunde.',
 'warning', 1, DATEADD(hour, -5, GETDATE())),

-- Alertă info: device nou descoperit
(@id_unknown, 'new_device',
 'Device necunoscut descoperit în rețea: 192.168.1.99. Verificați imediat!',
 'info', 0, DATEADD(minute, -10, GETDATE()));

PRINT '✓ Date alerts inserate (4 alerte).';
GO

-- ============================================================
-- DATE DE TEST: uptime_log (ultimele 24 ore pentru 3 servere)
-- ============================================================
-- Generăm câte 24 de înregistrări (o verificare pe oră) pentru
-- fiecare din cele 3 servere principale

DECLARE @srv1 INT = (SELECT id FROM devices WHERE ip_address = '192.168.1.10');
DECLARE @srv2 INT = (SELECT id FROM devices WHERE ip_address = '192.168.1.11');
DECLARE @srv3 INT = (SELECT id FROM devices WHERE ip_address = '192.168.1.12');
DECLARE @i    INT = 0;

WHILE @i < 24
BEGIN
    -- Server 1 (Windows): mereu online
    INSERT INTO uptime_log (device_id, checked_at, is_online, response_ms)
    VALUES (@srv1, DATEADD(hour, -@i, GETDATE()), 1, 5 + (ABS(CHECKSUM(NEWID())) % 20));

    -- Server 2 (Ubuntu): mereu online
    INSERT INTO uptime_log (device_id, checked_at, is_online, response_ms)
    VALUES (@srv2, DATEADD(hour, -@i, GETDATE()), 1, 3 + (ABS(CHECKSUM(NEWID())) % 15));

    -- Server 3 (backup): offline în ultimele 45 minute (i = 0)
    INSERT INTO uptime_log (device_id, checked_at, is_online, response_ms)
    VALUES (
        @srv3,
        DATEADD(hour, -@i, GETDATE()),
        CASE WHEN @i = 0 THEN 0 ELSE 1 END,  -- offline doar acum
        CASE WHEN @i = 0 THEN NULL ELSE 8 + (ABS(CHECKSUM(NEWID())) % 25) END
    );

    SET @i = @i + 1;
END

PRINT '✓ Date uptime_log inserate (72 înregistrări).';
GO

-- ============================================================
-- VERIFICARE FINALĂ: afișează ce s-a inserat
-- ============================================================
PRINT '';
PRINT '=== REZUMAT DATE INSERATE ===';

SELECT 'devices'      AS Tabel, COUNT(*) AS Randuri FROM devices
UNION ALL
SELECT 'scan_history',           COUNT(*)            FROM scan_history
UNION ALL
SELECT 'alerts',                 COUNT(*)            FROM alerts
UNION ALL
SELECT 'uptime_log',             COUNT(*)            FROM uptime_log;

PRINT '';
PRINT '============================================';
PRINT ' Seed data completă! Baza de date e gata.';
PRINT ' Acum treci la configurarea Python.';
PRINT '============================================';
