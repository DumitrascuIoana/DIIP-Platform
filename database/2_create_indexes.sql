-- ============================================================
-- FISIER 2: create_indexes.sql
-- Ce face: Creează indexuri pentru interogări rapide
-- De ce contează: Fără indexuri, SQL Server scanează TOT tabelul
--                 la fiecare SELECT. Cu indexuri, găsește rapid.
-- Unde rulezi: SSMS > New Query > Run (F5)
--              (după ce ai rulat fisierul 1)
-- ============================================================

USE DIIP;
GO

-- ============================================================
-- INDEX pe ip_address
-- De ce: Aplicația caută des un device după IP
--        ex: SELECT * FROM devices WHERE ip_address = '192.168.1.10'
-- ============================================================
IF NOT EXISTS (
    SELECT * FROM sys.indexes
    WHERE name = 'IX_devices_ip_address'
)
BEGIN
    CREATE INDEX IX_devices_ip_address
        ON devices(ip_address);
    PRINT '✓ Index IX_devices_ip_address creat.';
END
ELSE
    PRINT '! Index IX_devices_ip_address există deja.';
GO

-- ============================================================
-- INDEX pe status
-- De ce: Dashboard-ul filtrează des după status
--        ex: SELECT COUNT(*) FROM devices WHERE status = 'online'
-- ============================================================
IF NOT EXISTS (
    SELECT * FROM sys.indexes
    WHERE name = 'IX_devices_status'
)
BEGIN
    CREATE INDEX IX_devices_status
        ON devices(status);
    PRINT '✓ Index IX_devices_status creat.';
END
ELSE
    PRINT '! Index IX_devices_status există deja.';
GO

-- ============================================================
-- INDEX pe os_family
-- De ce: Graficul "Linux vs Windows" filtrează după os_family
--        ex: SELECT os_family, COUNT(*) FROM devices GROUP BY os_family
-- ============================================================
IF NOT EXISTS (
    SELECT * FROM sys.indexes
    WHERE name = 'IX_devices_os_family'
)
BEGIN
    CREATE INDEX IX_devices_os_family
        ON devices(os_family);
    PRINT '✓ Index IX_devices_os_family creat.';
END
ELSE
    PRINT '! Index IX_devices_os_family există deja.';
GO

-- ============================================================
-- INDEX pe alerts.is_read
-- De ce: Notificările din header cer alertele necitite constant
--        ex: SELECT * FROM alerts WHERE is_read = 0
-- ============================================================
IF NOT EXISTS (
    SELECT * FROM sys.indexes
    WHERE name = 'IX_alerts_is_read'
)
BEGIN
    CREATE INDEX IX_alerts_is_read
        ON alerts(is_read);
    PRINT '✓ Index IX_alerts_is_read creat.';
END
ELSE
    PRINT '! Index IX_alerts_is_read există deja.';
GO

-- ============================================================
-- INDEX COMPUS pe uptime_log(device_id, checked_at)
-- De ce: Graficul de uptime cere istoricul unui device pe o perioadă
--        ex: SELECT * FROM uptime_log
--            WHERE device_id = 5 AND checked_at >= DATEADD(day, -7, GETDATE())
-- INDEX COMPUS = index pe două coloane împreună (mai eficient)
-- ============================================================
IF NOT EXISTS (
    SELECT * FROM sys.indexes
    WHERE name = 'IX_uptime_device_date'
)
BEGIN
    CREATE INDEX IX_uptime_device_date
        ON uptime_log(device_id, checked_at);
    PRINT '✓ Index IX_uptime_device_date creat.';
END
ELSE
    PRINT '! Index IX_uptime_device_date există deja.';
GO

PRINT '';
PRINT '============================================';
PRINT ' Toate indexurile au fost create!';
PRINT ' Mergi la fisierul 3: seed_data.sql';
PRINT '============================================';
