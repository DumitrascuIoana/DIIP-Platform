-- ============================================================
-- analytics_queries.sql
-- Ce face: Query-uri SQL avansate pentru Analytics Dashboard
--
-- Tehnologii folosite:
--   CTE (WITH) = subquery-uri reutilizabile
--   WINDOW FUNCTIONS = calcule pe grupuri de date
--   ROW_NUMBER, RANK, LAG = functii de analiza
--
-- Ruleaza in SSMS sa vezi rezultatele direct
-- ============================================================

USE DIIP;
GO

-- ============================================================
-- QUERY 1: Distributia device-urilor pe departament
-- Foloseste: GROUP BY + COUNT + ROUND pentru procente
-- ============================================================
SELECT
    ISNULL(department, 'Neatribuit')    AS departament,
    COUNT(*)                             AS total_devices,
    SUM(CASE WHEN status = 'online'  THEN 1 ELSE 0 END) AS online,
    SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) AS offline,
    -- Calculam procentul din total
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(),
        1
    )                                    AS procent
    -- OVER() = aplica SUM pe TOATE randurile (window function)
    -- Fara OVER(), am fi nevoiti sa facem un subquery separat
FROM devices
GROUP BY department
ORDER BY total_devices DESC;
GO

-- ============================================================
-- QUERY 2: Top device-uri dupa uptime (Window Function: RANK)
-- Foloseste: CTE + RANK() OVER
-- ============================================================
WITH uptime_stats AS (
    -- CTE = definim un "tabel temporar" cu statistici uptime
    -- Il putem folosi ca pe un tabel normal mai jos
    SELECT
        d.id,
        d.ip_address,
        d.hostname,
        d.device_type,
        d.department,
        COUNT(ul.id)                          AS total_checks,
        SUM(CASE WHEN ul.is_online = 1 THEN 1 ELSE 0 END) AS online_checks,
        -- Calculam procentul uptime
        ROUND(
            SUM(CASE WHEN ul.is_online = 1 THEN 1.0 ELSE 0 END)
            / NULLIF(COUNT(ul.id), 0) * 100,
            1
        )                                     AS uptime_pct,
        AVG(CASE WHEN ul.response_ms IS NOT NULL
            THEN CAST(ul.response_ms AS FLOAT) END) AS avg_response_ms
    FROM devices d
    LEFT JOIN uptime_log ul ON d.id = ul.device_id
    GROUP BY d.id, d.ip_address, d.hostname, d.device_type, d.department
)
SELECT
    ip_address,
    ISNULL(hostname, 'Unknown')          AS hostname,
    device_type,
    ISNULL(department, 'Neatribuit')     AS department,
    total_checks,
    uptime_pct,
    ROUND(avg_response_ms, 0)            AS avg_ms,
    -- RANK() = clasamentul in functie de uptime
    -- OVER (ORDER BY ...) = definim cum se calculeaza rangul
    RANK() OVER (ORDER BY uptime_pct DESC)   AS rank_uptime,
    -- NTILE(4) = imparte in 4 grupuri egale (quartile)
    -- 1 = top 25%, 4 = bottom 25%
    NTILE(4) OVER (ORDER BY uptime_pct DESC) AS quartile
FROM uptime_stats
WHERE total_checks > 0
ORDER BY rank_uptime;
GO

-- ============================================================
-- QUERY 3: Activitate zilnica (scanari + alerte pe zi)
-- Foloseste: CTE + CAST pentru grupare pe data
-- ============================================================
WITH activity AS (
    SELECT
        CAST(started_at AS DATE)  AS zi,
        'scanare'                  AS tip,
        COUNT(*)                   AS numar
    FROM scan_history
    WHERE started_at >= DATEADD(day, -30, GETDATE())
    GROUP BY CAST(started_at AS DATE)

    UNION ALL

    SELECT
        CAST(created_at AS DATE)  AS zi,
        'alerta'                   AS tip,
        COUNT(*)                   AS numar
    FROM alerts
    WHERE created_at >= DATEADD(day, -30, GETDATE())
    GROUP BY CAST(created_at AS DATE)
)
SELECT
    zi,
    SUM(CASE WHEN tip = 'scanare' THEN numar ELSE 0 END) AS scanari,
    SUM(CASE WHEN tip = 'alerta'  THEN numar ELSE 0 END) AS alerte,
    -- LAG() = valoarea din randul ANTERIOR
    -- Folosim pentru a compara cu ziua precedenta
    LAG(SUM(CASE WHEN tip = 'alerta' THEN numar ELSE 0 END))
        OVER (ORDER BY zi)                               AS alerte_zi_anterioara
FROM activity
GROUP BY zi
ORDER BY zi DESC;
GO

-- ============================================================
-- QUERY 4: Analiza alertelor pe tip si severitate
-- Foloseste: PIVOT logic cu CASE + GROUP BY
-- ============================================================
SELECT
    alert_type                                AS tip_alerta,
    COUNT(*)                                   AS total,
    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critice,
    SUM(CASE WHEN severity = 'warning'  THEN 1 ELSE 0 END) AS avertismente,
    SUM(CASE WHEN severity = 'info'     THEN 1 ELSE 0 END) AS informatii,
    SUM(CASE WHEN is_read = 0           THEN 1 ELSE 0 END) AS necitite,
    -- Prima si ultima alerta de acest tip
    MIN(created_at)                            AS prima_alerta,
    MAX(created_at)                            AS ultima_alerta
FROM alerts
GROUP BY alert_type
ORDER BY total DESC;
GO

-- ============================================================
-- QUERY 5: Evolutia device-urilor descoperite in timp
-- Foloseste: CTE + ROW_NUMBER + running total
-- ============================================================
WITH device_timeline AS (
    SELECT
        CAST(first_seen AS DATE)  AS data_descoperire,
        COUNT(*)                   AS device_noi,
        -- Running total = suma cumulativa
        SUM(COUNT(*)) OVER (
            ORDER BY CAST(first_seen AS DATE)
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                          AS total_cumulativ
    FROM devices
    WHERE first_seen IS NOT NULL
    GROUP BY CAST(first_seen AS DATE)
)
SELECT
    data_descoperire,
    device_noi,
    total_cumulativ,
    -- Crestere procentuala fata de ziua anterioara
    ROUND(
        (device_noi * 100.0) /
        NULLIF(
            LAG(total_cumulativ) OVER (ORDER BY data_descoperire),
            0
        ),
        1
    )                              AS crestere_pct
FROM device_timeline
ORDER BY data_descoperire DESC;
GO

-- ============================================================
-- QUERY 6: Audit log - activitate utilizatori
-- Foloseste: CTE + COUNT + GROUP BY + ORDER BY
-- ============================================================
WITH user_activity AS (
    SELECT
        ISNULL(username, 'anonim')  AS username,
        action,
        COUNT(*)                     AS numar_actiuni,
        MIN(created_at)              AS prima_actiune,
        MAX(created_at)              AS ultima_actiune,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS actiuni_esuate
    FROM audit_logs
    GROUP BY username, action
)
SELECT
    username,
    action,
    numar_actiuni,
    actiuni_esuate,
    ultima_actiune,
    -- Rangul userului dupa numarul de actiuni
    RANK() OVER (
        PARTITION BY action          -- separat pentru fiecare tip de actiune
        ORDER BY numar_actiuni DESC
    )                                AS rank_per_actiune
FROM user_activity
ORDER BY username, numar_actiuni DESC;
GO

PRINT 'Toate query-urile analytics executate cu succes!';
