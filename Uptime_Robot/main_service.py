import sys
import os
import json
import sqlite3
import asyncio
import threading
import socket
import servicemanager
import win32serviceutil
import win32service
import win32event
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Internal modules
import config_manager
import ui_templates
import notifications
import monitoring
import models
from database import get_db_connection
from logger import logger

# Configuration
config_manager.init_paths()
CONFIG = config_manager.load_config()
DB_PATH = config_manager.DB_PATH
APP_DIR = config_manager.APP_DIR
DEFAULT_PORT = CONFIG.get("server", {}).get("port", 8080)
CHECK_INTERVAL = CONFIG.get("check_interval", 60)

# Global settings
NOTIFY_SETTINGS = config_manager.DEFAULT_NOTIFY_SETTINGS.copy()

app = FastAPI(title="Uptime Monitor Service")

# --- Initialization ---
def initialize_app():
    global NOTIFY_SETTINGS
    models.init_database(DB_PATH)
    # Load notify settings from DB
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT config FROM notify_config WHERE id = 1")
        row = c.fetchone()
        if row:
            try:
                NOTIFY_SETTINGS.update(json.loads(row["config"]))
            except:
                pass

initialize_app()

# --- Pydantic Models (Simplified for Service) ---
class SiteCreate(BaseModel):
    name: str
    url: str
    check_interval: int = 60
    is_active: bool = True
    notify_methods: Optional[List[str]] = []

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    notify_methods: Optional[List[str]] = None
    is_active: Optional[bool] = None

class NotifySettings(BaseModel):
    telegram: Optional[dict] = None
    teams: Optional[dict] = None
    discord: Optional[dict] = None
    slack: Optional[dict] = None
    email: Optional[dict] = None
    sms: Optional[dict] = None

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sites")
        total_sites = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM sites WHERE status = 'up'")
        up_sites = c.fetchone()[0]
        down_sites = total_sites - up_sites

    notification_cards = ui_templates.get_notification_cards_html(NOTIFY_SETTINGS)
    notify_config_json = json.dumps(NOTIFY_SETTINGS)

    # Note: Service dashboard uses a single-page approach without login
    return HTMLResponse(content=ui_templates.get_dashboard_html(
        total_sites=total_sites,
        up_sites=up_sites,
        down_sites=down_sites,
        notify_config_json=notify_config_json,
        notification_cards=notification_cards
    ))

@app.get("/api/sites")
async def get_sites():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sites ORDER BY id")
        sites = [dict(row) for row in c.fetchall()]
        
        for site in sites:
            c.execute("SELECT * FROM status_history WHERE site_id = ? ORDER BY checked_at DESC LIMIT 1", (site["id"],))
            last = c.fetchone()
            site["status"] = last["status"] if last else "unknown"
            site["notify_methods"] = json.loads(site["notify_methods"]) if site["notify_methods"] else []
    return sites

@app.post("/api/sites")
async def add_site(site: SiteCreate):
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO sites (name, url, check_interval, is_active, notify_methods) VALUES (?, ?, ?, ?, ?)",
                      (site.name, site.url, site.check_interval, site.is_active, json.dumps(site.notify_methods)))
            site_id = c.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(400, "Already exists")
    
    await monitoring.check_site_status(site_id, site.url, site.notify_methods, NOTIFY_SETTINGS)
    return {"id": site_id}

@app.put("/api/sites/{site_id}")
async def update_site(site_id: int, site_update: SiteUpdate):
    models.update_site(DB_PATH, site_id, **site_update.dict(exclude_unset=True))
    return {"message": "Updated"}

@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: int):
    models.delete_site(DB_PATH, site_id)
    return {"message": "Deleted"}

@app.post("/api/sites/{site_id}/check")
async def manual_check(site_id: int):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT url, notify_methods FROM sites WHERE id = ?", (site_id,))
        site = c.fetchone()
    if not site: raise HTTPException(404)
    methods = json.loads(site["notify_methods"]) if site["notify_methods"] else []
    await monitoring.check_site_status(site_id, site["url"], methods, NOTIFY_SETTINGS)
    return {"message": "Check done"}

@app.post("/api/notify-settings")
async def save_notify(settings: NotifySettings):
    global NOTIFY_SETTINGS
    data = settings.dict(exclude_unset=True)
    for k, v in data.items():
        if v: NOTIFY_SETTINGS[k] = v
    models.save_notify_settings(DB_PATH, NOTIFY_SETTINGS)
    return {"message": "Saved"}

# --- Windows Service Logic ---

class UptimeMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "UptimeMonitor"
    _svc_display_name_ = "Uptime Monitor Service"
    _svc_description_ = "Website uptime monitoring service with web interface"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = False

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        self.running = True
        self.main()

    def main(self):
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            asyncio.ensure_future(monitoring.monitor_loop(NOTIFY_SETTINGS, CHECK_INTERVAL))
            config = uvicorn.Config(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="error")
            server = uvicorn.Server(config)
            loop.run_until_complete(server.serve())

        self.ReportServiceStatus(win32service.SERVICE_START_PENDING, waitHint=30000)
        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

def install_service():
    try:
        exe_path = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
        win32serviceutil.HandleCommandLine(UptimeMonitorService, argv=[exe_path, "install"])
        # Set to auto-start
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"SYSTEM\\CurrentControlSet\\Services\\{UptimeMonitorService._svc_name_}", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 2)
        winreg.CloseKey(key)
        print("✅ Service installed and set to Auto-start.")
    except Exception as e: print(f"❌ Installation error: {e}")

def run_console():
    print(f"Uptime Monitor (Console Mode) on port {DEFAULT_PORT}")
    async def run():
        asyncio.create_task(monitoring.monitor_loop(NOTIFY_SETTINGS, CHECK_INTERVAL))
        config = uvicorn.Config(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
        await uvicorn.Server(config).serve()
    try: asyncio.run(run())
    except KeyboardInterrupt: pass

if __name__ == "__main__":
    if len(sys.argv) == 1: run_console()
    else:
        cmd = sys.argv[1].lower()
        if cmd == "install": install_service()
        elif cmd in ("remove", "start", "stop", "restart"):
            win32serviceutil.HandleCommandLine(UptimeMonitorService)
        elif cmd == "console": run_console()
        else: win32serviceutil.HandleCommandLine(UptimeMonitorService)
