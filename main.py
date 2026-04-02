# ============================================================
# main.py
# Ce face: Punctul de intrare al aplicației FastAPI
#
# Acest fișier:
#   1. Creează aplicația FastAPI
#   2. Pornește monitorul în background
#   3. Definește toate rutele (paginile web + API)
#   4. Servește fișierele HTML din folderul templates/
#
# Cum pornești aplicația:
#   uvicorn main:app --reload
#
# Apoi deschizi browser la: http://127.0.0.1:8000
# ============================================================

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio

from fastapi.responses import StreamingResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from io import BytesIO
import csv

from database import db
from scanner import NetworkScanner
from monitor import AlertMonitor
from email_service import email_service

# ============================================================
# LIFESPAN — rulează la pornirea și oprirea aplicației
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Cod care rulează la PORNIRE (înainte de yield)
    și la OPRIRE (după yield).

    La pornire: verificăm conexiunea DB și pornim monitorul.
    La oprire: oprim monitorul elegant.
    """
    # ── PORNIRE ───────────────────────────────────────────────
    print("\n" + "="*50)
    print(" Digital Infrastructure Intelligence Platform")
    print("="*50)

    # Verificăm conexiunea la SQL Server
    test = db.test_connection()
    if test["status"] == "ok":
        print(f"✓ DB conectat: {test['server_name']}")
    else:
        print(f"✗ DB eroare: {test['message']}")

    # Pornim monitorul de alerte în background
    monitor = AlertMonitor(check_interval_seconds=300)
    task    = asyncio.create_task(monitor.run())
    print("✓ Monitor pornit (verificare la fiecare 5 minute)")
    print("✓ Aplicatie disponibila la: http://127.0.0.1:8000")
    print("="*50 + "\n")

    yield   # aplicația rulează între cele două blocuri

    # ── OPRIRE ────────────────────────────────────────────────
    task.cancel()
    print("\n[APP] Aplicatie oprita.")


# ============================================================
# CREĂM APLICAȚIA FASTAPI
# ============================================================
app = FastAPI(
    title       = "Digital Infrastructure Intelligence Platform",
    description = "Network discovery, inventory and monitoring",
    version     = "1.0.0",
    lifespan    = lifespan
)

# Fișiere statice (CSS, JS, imagini)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Template-uri HTML
templates = Jinja2Templates(directory="templates")

# Instanță scanner
scanner = NetworkScanner()


# ============================================================
# RUTE DE PAGINI (returnează HTML)
# ============================================================

@app.get("/")
async def page_dashboard(request: Request):
    """Pagina principală — Dashboard cu statistici și grafice."""
    return templates.TemplateResponse(request=request, name="dashboard.html")


@app.get("/inventory")
async def page_inventory(request: Request):
    """Pagina Inventar — lista tuturor device-urilor."""
    return templates.TemplateResponse(request=request, name="inventory.html")


@app.get("/scan")
async def page_scan(request: Request):
    """Pagina Scanare — formular pentru scanare rețea."""
    return templates.TemplateResponse(request=request, name="scan.html")


@app.get("/alerts")
async def page_alerts(request: Request):
    """Pagina Alerte — lista tuturor alertelor."""
    return templates.TemplateResponse(request=request, name="alerts.html")


@app.get("/device/{ip_address}")
async def page_device_detail(request: Request, ip_address: str):
    """Pagina de detalii pentru un device specific."""
    return templates.TemplateResponse(
        request=request,
        name="device_detail.html",
        context={"ip_address": ip_address.replace("-", ".")}
    )


# ============================================================
# RUTE API (returnează JSON — apelate din JavaScript)
# ============================================================

# ── Dashboard ─────────────────────────────────────────────────

@app.get("/api/dashboard/stats")
async def api_dashboard_stats():
    """Statistici pentru dashboard: total, online, offline, by_type, by_os."""
    try:
        stats = db.get_dashboard_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ── Devices ───────────────────────────────────────────────────

@app.get("/api/devices")
async def api_get_devices():
    """Returnează toate device-urile din inventar."""
    try:
        devices = db.get_all_devices()
        return JSONResponse(content={"devices": devices})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/devices/{ip_address}")
async def api_get_device(ip_address: str):
    """
    Returnează un device specific după IP.
    IP-ul vine cu - în loc de . în URL:
    Ex: /api/devices/192-168-1-10 → caută 192.168.1.10
    """
    try:
        ip     = ip_address.replace("-", ".")
        device = db.get_device_by_ip(ip)
        if not device:
            return JSONResponse(content={"error": "Device negasit"}, status_code=404)
        return JSONResponse(content=device)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.put("/api/devices/{device_id}")
async def api_update_device(device_id: int, request: Request):
    """
    Actualizează owner, department, notes ale unui device.
    Apelat din pagina Inventar când userul editează.
    """
    try:
        data = await request.json()
        db.update_device_info(device_id, data)
        return JSONResponse(content={"message": "Device actualizat cu succes!"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ── Scan ──────────────────────────────────────────────────────

@app.post("/api/scan")
async def api_start_scan(request: Request, background_tasks: BackgroundTasks):
    """
    Pornește o scanare de rețea în background.
    Userul primește răspuns imediat, scanarea rulează în spate.

    Body JSON:
    {
        "ip_range": "192.168.1.1-254",
        "detailed": false
    }
    """
    try:
        data     = await request.json()
        ip_range = data.get("ip_range", "").strip()
        detailed = data.get("detailed", False)

        if not ip_range:
            return JSONResponse(
                content={"error": "ip_range este obligatoriu"},
                status_code=400
            )

        if detailed:
            background_tasks.add_task(scanner.scan_with_details, ip_range)
        else:
            background_tasks.add_task(scanner.scan_network, ip_range)

        return JSONResponse(content={
            "message":  f"Scanare pornita pentru {ip_range}",
            "ip_range": ip_range,
            "detailed": detailed
        })

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/scan/history")
async def api_scan_history():
    """Returnează istoricul ultimelor 20 de scanări."""
    try:
        history = db.get_scan_history()
        return JSONResponse(content={"history": history})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ── Alerts ────────────────────────────────────────────────────

@app.get("/api/alerts")
async def api_get_alerts(unread_only: bool = False):
    """
    Returnează alertele.
    ?unread_only=true → doar necitite (pentru iconița din header)
    """
    try:
        alerts = db.get_alerts(unread_only=unread_only)
        return JSONResponse(content={"alerts": alerts})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.put("/api/alerts/{alert_id}/read")
async def api_mark_alert_read(alert_id: int):
    """Marchează o alertă ca citită."""
    try:
        db.mark_alert_read(alert_id)
        return JSONResponse(content={"message": "Alerta marcata ca citita."})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ── Uptime per device ─────────────────────────────────────────

@app.get("/api/devices/{ip_address}/uptime")
async def api_device_uptime(ip_address: str):
    """Returnează istoricul uptime pentru un device — ultimele 24 verificări."""
    try:
        ip   = ip_address.replace("-", ".")
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 24
                ul.checked_at, ul.is_online, ul.response_ms
            FROM uptime_log ul
            JOIN devices d ON ul.device_id = d.id
            WHERE d.ip_address = ?
            ORDER BY ul.checked_at DESC
        """, (ip,))
        columns = [col[0] for col in cursor.description]
        rows = []
        for row in cursor.fetchall():
            item = dict(zip(columns, row))
            if item["checked_at"]:
                item["checked_at"] = item["checked_at"].strftime("%H:%M")
            item["is_online"] = bool(item["is_online"])
            rows.append(item)
        conn.close()
        return JSONResponse(content={"uptime": rows})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ── Health check ──────────────────────────────────────────────

@app.get("/api/health")
async def api_health():
    """Verifică starea aplicației și conexiunea DB. Util pentru debugging."""
    db_status = db.test_connection()
    return JSONResponse(content={
        "app":      "running",
        "database": db_status["status"],
        "message":  db_status.get("message")
    })


# ============================================================
# PORNIRE DIRECTĂ
# Recomandat: uvicorn main:app --reload
# Alternativ:  python main.py
# ============================================================

# ── Export Excel ──────────────────────────────────────────────

@app.get("/api/export/excel")
async def export_excel():
    """
    Exportă inventarul complet în format Excel (.xlsx).
    Returneaza un fisier descarcabil direct din browser.
    """
    try:
        devices = db.get_all_devices()

        # Creăm workbook-ul Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventar IT"

        # ── Stiluri ──────────────────────────────────────────
        # Header: fundal albastru, text alb, bold
        header_fill = PatternFill("solid", fgColor="1e3a5f")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_align = Alignment(horizontal="center", vertical="center")

        # Online: verde deschis
        online_fill = PatternFill("solid", fgColor="d1fae5")
        # Offline: roșu deschis
        offline_fill = PatternFill("solid", fgColor="fee2e2")

        # ── Header row ────────────────────────────────────────
        headers = [
            "ID", "IP Address", "Hostname", "Tip Device",
            "Sistem de Operare", "OS Family", "MAC Address",
            "Owner", "Departament", "Status",
            "Porturi Deschise", "Prima Descoperire",
            "Ultima Activitate", "Note"
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align

        # ── Date ──────────────────────────────────────────────
        for row_num, device in enumerate(devices, 2):
            row_data = [
                device.get("id"),
                device.get("ip_address"),
                device.get("hostname"),
                device.get("device_type"),
                device.get("os_name"),
                device.get("os_family"),
                device.get("mac_address"),
                device.get("owner"),
                device.get("department"),
                device.get("status"),
                device.get("open_ports"),
                device.get("first_seen"),
                device.get("last_seen"),
                device.get("notes"),
            ]

            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num, value=value)
                cell.alignment = Alignment(vertical="center")

            # Colorăm rândul după status
            status = device.get("status", "")
            if status == "online":
                for col in range(1, len(headers) + 1):
                    ws.cell(row=row_num, column=col).fill = online_fill
            elif status == "offline":
                for col in range(1, len(headers) + 1):
                    ws.cell(row=row_num, column=col).fill = offline_fill

        # ── Lățime coloane automată ───────────────────────────
        col_widths = [6, 16, 20, 14, 22, 12, 18, 18, 14, 10, 18, 20, 20, 30]
        for col_num, width in enumerate(col_widths, 1):
            ws.column_dimensions[
                openpyxl.utils.get_column_letter(col_num)
            ].width = width

        # Înghețăm primul rând (header rămâne vizibil la scroll)
        ws.freeze_panes = "A2"

        # ── Salvăm în memorie și trimitem ─────────────────────
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=inventar_DIIP.xlsx"}
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ── Export CSV ────────────────────────────────────────────────

@app.get("/api/export/csv")
async def export_csv():
    """
    Exportă inventarul complet în format CSV.
    CSV = text simplu, poate fi deschis în Excel, Google Sheets etc.
    """
    try:
        devices = db.get_all_devices()

        # Creăm CSV în memorie
        buffer = BytesIO()
        # CSV-ul trebuie să fie text, îl encodăm UTF-8
        import io
        text_buffer = io.StringIO()

        headers = [
            "id", "ip_address", "hostname", "device_type",
            "os_name", "os_family", "mac_address",
            "owner", "department", "status",
            "open_ports", "first_seen", "last_seen", "notes"
        ]

        writer = csv.DictWriter(text_buffer, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(devices)

        # Convertim în bytes
        buffer = BytesIO(text_buffer.getvalue().encode("utf-8-sig"))
        # utf-8-sig = adaugă BOM la început → Excel îl deschide corect cu diacritice

        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventar_DIIP.csv"}
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/email/test")
async def api_test_email():
    """Trimite un email de test — verifică configurația."""
    result = email_service.test_email()
    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
