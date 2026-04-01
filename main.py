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

from database import db
from scanner import NetworkScanner
from monitor import AlertMonitor


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
    print("\n" + "=" * 50)
    print(" Digital Infrastructure Intelligence Platform")
    print("=" * 50)

    # Verificăm conexiunea la SQL Server
    test = db.test_connection()
    if test["status"] == "ok":
        print(f"✓ DB conectat: {test['server_name']}")
    else:
        print(f"✗ DB eroare: {test['message']}")

    # Pornim monitorul de alerte în background
    monitor = AlertMonitor(check_interval_seconds=300)
    task = asyncio.create_task(monitor.run())
    print("✓ Monitor pornit (verificare la fiecare 5 minute)")
    print("✓ Aplicatie disponibila la: http://127.0.0.1:8000")
    print("=" * 50 + "\n")

    yield  # aplicația rulează între cele două blocuri

    # ── OPRIRE ────────────────────────────────────────────────
    task.cancel()
    print("\n[APP] Aplicatie oprita.")


# ============================================================
# CREĂM APLICAȚIA FASTAPI
# ============================================================
app = FastAPI(
    title="Digital Infrastructure Intelligence Platform",
    description="Network discovery, inventory and monitoring",
    version="1.0.0",
    lifespan=lifespan
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
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get("/inventory")
async def page_inventory(request: Request):
    return templates.TemplateResponse(request=request, name="inventory.html")

@app.get("/scan")
async def page_scan(request: Request):
    return templates.TemplateResponse(request=request, name="scan.html")

@app.get("/alerts")
async def page_alerts(request: Request):
    return templates.TemplateResponse(request=request, name="alerts.html")


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
        ip = ip_address.replace("-", ".")
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
        data = await request.json()
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
            "message": f"Scanare pornita pentru {ip_range}",
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


# ── Health check ──────────────────────────────────────────────

@app.get("/api/health")
async def api_health():
    """Verifică starea aplicației și conexiunea DB. Util pentru debugging."""
    db_status = db.test_connection()
    return JSONResponse(content={
        "app": "running",
        "database": db_status["status"],
        "message": db_status.get("message")
    })


# ============================================================
# PORNIRE DIRECTĂ
# Recomandat: uvicorn main:app --reload
# Alternativ:  python main.py
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)