import sys
import os
import json
import sqlite3
import asyncio
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Internal modules
import config_manager
import ui_templates
import notifications
import monitoring
import models
import auth_module
from database import get_db_connection
from logger import logger

# Windows-specific imports
IS_WINDOWS = sys.platform == "win32"
if IS_WINDOWS:
    import win32service
    import win32serviceutil
    import win32con
    import win32event
    import servicemanager

# App initialization
config_manager.init_paths()
CONFIG = config_manager.load_config()
DB_PATH = config_manager.DB_PATH
APP_DIR = config_manager.APP_DIR

# Global state
NOTIFY_SETTINGS = config_manager.DEFAULT_NOTIFY_SETTINGS.copy()
DISPLAY_ADDRESS = ""
CHECK_INTERVAL = CONFIG.get("check_interval", 60)

# FastAPI app
app = FastAPI(title="Uptime Monitor")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for HTTPS redirect and HSTS
@app.middleware("http")
async def https_redirect_middleware(request: Request, call_next):
    return await config_manager.https_redirect_middleware(request, call_next, CONFIG)

# --- Dependency ---
async def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        return None
    return user

# --- Initialization ---
def initialize_app():
    global NOTIFY_SETTINGS, DISPLAY_ADDRESS
    
    # Init DB and run migrations
    models.init_database(DB_PATH)
    
    # Load settings from DB
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Notify settings
        c.execute("SELECT config FROM notify_config WHERE id = 1")
        row = c.fetchone()
        if row:
            try:
                NOTIFY_SETTINGS.update(json.loads(row["config"]))
            except:
                pass

        # App settings
        c.execute("SELECT display_address FROM app_settings WHERE id = 1")
        row = c.fetchone()
        if row:
            DISPLAY_ADDRESS = row["display_address"] or ""

    # Init Auth tables
    auth_module.init_auth_tables(DB_PATH)

initialize_app()

# --- Pydantic Models ---
class SiteCreate(BaseModel):
    name: str
    url: str
    check_interval: int = 60
    is_active: bool = True
    notify_methods: Optional[List[str]] = []
    monitor_type: str = "http"

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    notify_methods: Optional[List[str]] = None
    is_active: Optional[bool] = None

class NotifySettingsModel(BaseModel):
    telegram: Optional[dict] = None
    teams: Optional[dict] = None
    discord: Optional[dict] = None
    slack: Optional[dict] = None
    email: Optional[dict] = None
    sms: Optional[dict] = None

class AppSettingsModel(BaseModel):
    display_address: Optional[str] = ""

# --- UI Routes ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if user.get("must_change_password"):
        return RedirectResponse(url="/change-password", status_code=302)

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM sites")
        total_sites = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM sites WHERE status = 'up'")
        up_sites = c.fetchone()[0]
        down_sites = total_sites - up_sites

    notification_cards = ui_templates.get_notification_cards_html(NOTIFY_SETTINGS)
    notify_config_json = json.dumps(NOTIFY_SETTINGS)

    return HTMLResponse(content=ui_templates.get_dashboard_html(
        total_sites=total_sites,
        up_sites=up_sites,
        down_sites=down_sites,
        notify_config_json=notify_config_json,
        notification_cards=notification_cards
    ))

@app.get("/status", response_class=HTMLResponse)
@app.get("/public-status", response_class=HTMLResponse)
async def public_status_page(request: Request):
    """Публічна сторінка статусу"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, url, monitor_type FROM sites WHERE is_active = 1 ORDER BY id")
        sites = c.fetchall()
        
        # Get last status for each site from history
        c.execute("""
            SELECT site_id, status FROM status_history 
            WHERE checked_at > datetime('now', '-24 hours') 
            ORDER BY checked_at DESC
        """)
        history = c.fetchall()
        
    site_status = {}
    for h in history:
        if h["site_id"] not in site_status:
            site_status[h["site_id"]] = h["status"]
            
    up_count = sum(1 for s in site_status.values() if s == "up")
    down_count = sum(1 for s in site_status.values() if s == "down")
    total = len(sites)
    
    monitors_html = ""
    for site in sites:
        status = site_status.get(site["id"], "unknown")
        status_class = "up" if status == "up" else ("paused" if status == "paused" else "down")
        status_text = "✓ Онлайн" if status == "up" else ("⏸ Пауза" if status == "paused" else "✗ Офлайн")
        monitors_html += f"""
        <div class="monitor {status_class}">
            <div><div class="monitor-name">{site["name"]}</div>
            <div class="monitor-url">{site["url"]}</div></div>
            <span class="status-badge {status_class}">{status_text}</span>
        </div>"""
        
    overall_status_class = "up" if down_count == 0 else "down"
    overall_status_text = "✅ Всі системи працюють" if down_count == 0 else "⚠️ Деякі проблеми"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return HTMLResponse(content=ui_templates.get_public_status_html(
        overall_status_class=overall_status_class,
        overall_status_text=overall_status_text,
        total=total,
        up_count=up_count,
        down_count=down_count,
        monitors_html=monitors_html,
        timestamp=timestamp
    ))

# --- Auth Routes ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None, user: dict = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    error_html = f'<div class="error">{error}</div>' if error else ""
    warning_html = '<div class="warning">WARNING: Change password after first login!</div>'
    return HTMLResponse(content=auth_module.LOGIN_HTML.format(
        error_message=error_html, warning_message=warning_html
    ))

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, password_hash, must_change_password FROM users WHERE username = ?", (username,))
        user = c.fetchone()

    if not user or not auth_module.verify_password(password, user["password_hash"]):
        return RedirectResponse(url="/login?error=Invalid username or password", status_code=302)

    session_id = auth_module.create_session(user["id"], DB_PATH)
    response = RedirectResponse(url="/change-password" if user["must_change_password"] else "/", status_code=302)
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=604800)
    return response

@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_module.delete_session(session_id, DB_PATH)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_id")
    return response

@app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request, error: str = None, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    error_html = f'<div class="error">{error}</div>' if error else ""
    return HTMLResponse(content=ui_templates.CHANGE_PASSWORD_HTML.format(error_message=error_html))

@app.post("/change-password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: dict = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if new_password != confirm_password:
        return RedirectResponse(url="/change-password?error=Passwords do not match", status_code=302)
    
    if len(new_password) < 6:
        return RedirectResponse(url="/change-password?error=Minimum 6 characters", status_code=302)

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE id = ?", (user["user_id"],))
        user_data = c.fetchone()

    if not user_data or not auth_module.verify_password(current_password, user_data["password_hash"]):
        return RedirectResponse(url="/change-password?error=Invalid current password", status_code=302)

    if auth_module.change_password(user["user_id"], new_password, DB_PATH):
        return RedirectResponse(url="/?message=Password updated", status_code=302)
    else:
        return RedirectResponse(url="/change-password?error=Update failed", status_code=302)

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(error: str = None, success: str = None):
    error_html = f'<div class="error">{error}</div>' if error else ""
    success_html = f'<div class="success">{success}</div>' if success else ""
    return HTMLResponse(content=auth_module.FORGOT_PASSWORD_HTML.format(
        error_message=error_html, success_message=success_html
    ))

@app.post("/forgot-password")
async def forgot_password_action(username: str = Form(...)):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if not user:
            return RedirectResponse(url="/forgot-password?error=User not found", status_code=302)
        
        # Reset to "admin"
        auth_module.change_password(user["id"], "admin", DB_PATH)
        # Force change on next login
        c.execute("UPDATE users SET must_change_password = 1 WHERE id = ?", (user["id"],))
        conn.commit()

    return RedirectResponse(url="/forgot-password?success=Password reset to 'admin'", status_code=302)

# --- API Routes ---

@app.get("/api/sites")
async def get_sites(user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(status_code=401)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sites ORDER BY id")
        sites = c.fetchall()
        result = []
        for site in sites:
            c.execute("SELECT * FROM status_history WHERE site_id = ? ORDER BY checked_at DESC LIMIT 1", (site["id"],))
            last_status = c.fetchone()
            c.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as up_count FROM status_history WHERE site_id = ?", (site["id"],))
            stats = c.fetchone()
            uptime = (stats["up_count"] / stats["total"] * 100) if stats["total"] > 0 else 0
            result.append({
                **dict(site),
                "status": last_status["status"] if last_status else "unknown",
                "uptime": round(uptime, 2),
                "notify_methods": json.loads(site["notify_methods"]) if site["notify_methods"] else []
            })
    return result

@app.post("/api/sites")
async def add_site(site: SiteCreate, user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(status_code=401)
    url = site.url.strip()
    if not url: raise HTTPException(400, "URL required")
    
    m_type = site.monitor_type.lower()
    if m_type == "ssl":
        url = monitoring.normalize_ssl_url(url)
    
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO sites (name, url, check_interval, is_active, notify_methods, monitor_type) VALUES (?, ?, ?, ?, ?, ?)",
                  (site.name, url, site.check_interval, site.is_active, json.dumps(site.notify_methods), m_type))
        site_id = c.lastrowid
        conn.commit()
    
    # Run initial check
    asyncio.create_task(monitoring.check_site_status(site_id, url, site.notify_methods, NOTIFY_SETTINGS))
    if m_type == "ssl" or url.lower().startswith("https://"):
        asyncio.create_task(monitoring.check_site_certificate(site_id, url, site.notify_methods, NOTIFY_SETTINGS))
    
    return {"id": site_id, "message": "Site added"}

@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: int, user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(status_code=401)
    models.delete_site(DB_PATH, site_id)
    return {"message": "Deleted"}

@app.post("/api/sites/{site_id}/check")
async def manual_check(site_id: int, user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(401)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT url, notify_methods FROM sites WHERE id = ?", (site_id,))
        site = c.fetchone()
    if not site: raise HTTPException(404)
    methods = json.loads(site["notify_methods"]) if site["notify_methods"] else []
    await monitoring.check_site_status(site_id, site["url"], methods, NOTIFY_SETTINGS)
    return {"message": "Check triggered"}

@app.get("/api/ssl-certificates")
async def get_ssl_certs(user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(401)
    return models.get_ssl_certificates(DB_PATH)

@app.post("/api/ssl-certificates/check")
async def manual_ssl_check(user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(401)
    await monitoring.check_all_certificates(NOTIFY_SETTINGS)
    return {"message": "SSL check triggered"}

@app.post("/api/notify-settings")
async def save_notify(settings: NotifySettingsModel, user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(401)
    global NOTIFY_SETTINGS
    new_data = settings.dict(exclude_unset=True)
    for k, v in new_data.items():
        if v is not None: NOTIFY_SETTINGS[k] = v
    models.save_notify_settings(DB_PATH, NOTIFY_SETTINGS)
    return {"message": "Saved"}

@app.post("/api/app-settings")
async def save_app(settings: AppSettingsModel, user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(401)
    global DISPLAY_ADDRESS
    DISPLAY_ADDRESS = settings.display_address
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO app_settings (id, display_address) VALUES (1, ?)", (DISPLAY_ADDRESS,))
        conn.commit()
    return {"message": "Saved"}

@app.get("/api/app-settings")
async def get_app(user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(401)
    return {"display_address": DISPLAY_ADDRESS}

@app.get("/api/user")
async def get_user_info(user: dict = Depends(get_current_user)):
    if not user: raise HTTPException(401)
    return {"username": user["username"], "is_admin": user.get("is_admin", False)}

# --- Background Task & Service ---

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Uptime Monitor")
    parser.add_argument("--host", type=str, default=CONFIG["server"].get("host", "0.0.0.0"), help="Host to bind to")
    parser.add_argument("--port", type=int, default=CONFIG["server"].get("port", 8080), help="Port to bind to")
    parser.add_argument("command", nargs="?", choices=["install", "remove", "start", "stop", "restart"], help="Service command")
    
    args, unknown = parser.parse_known_args()

    # Command line args for service management
    if args.command:
        if IS_WINDOWS:
            # Note: For Windows services, you usually need a specialized setup.
            # This is a placeholder for standard win32serviceutil usage.
            # win32serviceutil.HandleCommandLine(UptimeMonitorService)
            print(f"Executing service command: {args.command}")
            # In a real scenario, we'd call win32serviceutil.HandleCommandLine here
            sys.exit(0)

    # Normal application start
    print(f"Uptime Monitor starting on {args.host}:{args.port}...")
    
    # Start monitoring loop in a thread
    monitor_thread = threading.Thread(
        target=lambda: asyncio.run(monitoring.monitor_loop(NOTIFY_SETTINGS, CHECK_INTERVAL)), 
        daemon=True
    )
    monitor_thread.start()

    ssl_context = config_manager.setup_ssl(CONFIG)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        ssl_keyfile=CONFIG["ssl"].get("key_path") if ssl_context else None,
        ssl_certfile=CONFIG["ssl"].get("cert_path") if ssl_context else None,
        log_level="info"
    )
