import sys
import os
import json
import sqlite3
import asyncio
import threading
import ipaddress
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

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


def _is_valid_host(hostname: Optional[str]) -> bool:
    if not hostname:
        return False
    host = hostname.strip().lower().rstrip(".")
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    labels = host.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > 63:
            return False
        if label.startswith("-") or label.endswith("-"):
            return False
        if not all(ch.isalnum() or ch == "-" for ch in label):
            return False
    return True


def _normalize_and_validate_url(raw_url: str, monitor_type: str) -> str:
    url = (raw_url or "").strip()
    if not url:
        raise HTTPException(400, "URL required")

    m_type = (monitor_type or "http").lower()
    if m_type == "ssl":
        normalized = monitoring.normalize_ssl_url(url)
        if not normalized:
            raise HTTPException(400, "Invalid URL")
        url = normalized

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(400, "URL must start with http:// or https://")
    if not _is_valid_host(parsed.hostname):
        raise HTTPException(400, "Invalid host in URL")
    return url


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
        # status_history stores rows only on state changes, so use current status.
        c.execute("SELECT COUNT(*) FROM sites WHERE status = 'up'")
        up_sites = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM sites WHERE status = 'down'")
        down_sites = c.fetchone()[0]

    notification_cards = ui_templates.get_notification_cards_html(NOTIFY_SETTINGS)
    notify_config_json = json.dumps(NOTIFY_SETTINGS)

    return HTMLResponse(
        content=ui_templates.get_dashboard_html(
            total_sites=total_sites,
            up_sites=up_sites,
            down_sites=down_sites,
            notify_config_json=notify_config_json,
            notification_cards=notification_cards,
        )
    )


@app.get("/status", response_class=HTMLResponse)
@app.get("/public-status", response_class=HTMLResponse)
async def public_status_page(request: Request):
    """Public status page."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, name, url, monitor_type, status FROM sites WHERE is_active = 1 ORDER BY id"
        )
        sites = c.fetchall()

    def status_of(site_row: sqlite3.Row) -> str:
        value = site_row["status"]
        return (value or "unknown").lower()

    up_count = sum(1 for s in sites if status_of(s) == "up")
    down_count = sum(1 for s in sites if status_of(s) == "down")
    total = len(sites)

    # Sort: DOWN first, then slow, then unknown/paused, then UP.
    def get_sort_order(site_row: sqlite3.Row) -> int:
        status = status_of(site_row)
        if status == "down":
            return 0
        if status == "slow":
            return 1
        if status == "unknown":
            return 2
        if status == "paused":
            return 3
        return 4

    sites.sort(key=get_sort_order)

    monitors_html = ""
    for site in sites:
        status = status_of(site)
        if status == "up":
            status_class = "up"
            status_text = "UP"
            dot_color = "#00ff88"
        elif status in ("paused", "slow"):
            status_class = "paused"
            status_text = "PAUSED" if status == "paused" else "SLOW"
            dot_color = "#f59e0b"
        elif status == "unknown":
            status_class = "unknown"
            status_text = "UNKNOWN"
            dot_color = "#94a3b8"
        else:
            status_class = "down"
            status_text = "DOWN"
            dot_color = "#ff4757"

        monitors_html += f"""
        <div class="monitor {status_class}">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 10px; height: 10px; border-radius: 50%; background: {dot_color}; box-shadow: 0 0 8px {dot_color};"></div>
                <div><div class="monitor-name">{site["name"]}</div>
                <div class="monitor-url">{site["url"]}</div></div>
            </div>
            <span class="status-badge {status_class}">{status_text}</span>
        </div>"""

    overall_status_class = "up" if down_count == 0 else "down"
    overall_status_text = (
        "All systems operational" if down_count == 0 else "Some issues detected"
    )
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return HTMLResponse(
        content=ui_templates.get_public_status_html(
            overall_status_class=overall_status_class,
            overall_status_text=overall_status_text,
            total=total,
            up_count=up_count,
            down_count=down_count,
            monitors_html=monitors_html,
            timestamp=timestamp,
        )
    )


# --- Auth Routes ---


@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, error: str = None, user: dict = Depends(get_current_user)
):
    if user:
        return RedirectResponse(url="/", status_code=302)

    error_html = f'<div class="error">{error}</div>' if error else ""
    warning_html = (
        '<div class="warning">WARNING: Change password after first login!</div>'
    )
    return HTMLResponse(
        content=auth_module.LOGIN_HTML.format(
            error_message=error_html, warning_message=warning_html
        )
    )


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, password_hash, must_change_password FROM users WHERE username = ?",
            (username,),
        )
        user = c.fetchone()

    if not user or not auth_module.verify_password(password, user["password_hash"]):
        return RedirectResponse(
            url="/login?error=Invalid username or password", status_code=302
        )

    session_id = auth_module.create_session(user["id"], DB_PATH)
    response = RedirectResponse(
        url="/change-password" if user["must_change_password"] else "/", status_code=302
    )
    response.set_cookie(
        key="session_id", value=session_id, httponly=True, max_age=604800
    )
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
async def change_password_page(
    request: Request, error: str = None, user: dict = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    error_html = f'<div class="error">{error}</div>' if error else ""
    return HTMLResponse(
        content=ui_templates.CHANGE_PASSWORD_HTML.format(error_message=error_html)
    )


@app.post("/change-password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    user: dict = Depends(get_current_user),
):
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if new_password != confirm_password:
        return RedirectResponse(
            url="/change-password?error=Passwords do not match", status_code=302
        )

    if len(new_password) < 6:
        return RedirectResponse(
            url="/change-password?error=Minimum 6 characters", status_code=302
        )

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE id = ?", (user["user_id"],))
        user_data = c.fetchone()

    if not user_data or not auth_module.verify_password(
        current_password, user_data["password_hash"]
    ):
        return RedirectResponse(
            url="/change-password?error=Invalid current password", status_code=302
        )

    if auth_module.change_password(user["user_id"], new_password, DB_PATH):
        return RedirectResponse(url="/?message=Password updated", status_code=302)
    else:
        return RedirectResponse(
            url="/change-password?error=Update failed", status_code=302
        )


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(error: str = None, success: str = None):
    error_html = f'<div class="error">{error}</div>' if error else ""
    success_html = f'<div class="success">{success}</div>' if success else ""
    return HTMLResponse(
        content=auth_module.FORGOT_PASSWORD_HTML.format(
            error_message=error_html, success_message=success_html
        )
    )


@app.post("/forgot-password")
async def forgot_password_action(username: str = Form(...)):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if not user:
            return RedirectResponse(
                url="/forgot-password?error=User not found", status_code=302
            )

        # Reset to "admin"
        auth_module.change_password(user["id"], "admin", DB_PATH)
        # Force change on next login
        c.execute(
            "UPDATE users SET must_change_password = 1 WHERE id = ?", (user["id"],)
        )
        conn.commit()

    return RedirectResponse(
        url="/forgot-password?success=Password reset to 'admin'", status_code=302
    )


# --- API Routes ---


@app.get("/api/sites")
async def get_sites(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sites ORDER BY id")
        sites = c.fetchall()
        result = []
        for site in sites:
            c.execute(
                "SELECT * FROM status_history WHERE site_id = ? ORDER BY checked_at DESC LIMIT 1",
                (site["id"],),
            )
            last_status = c.fetchone()
            c.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as up_count FROM status_history WHERE site_id = ?",
                (site["id"],),
            )
            stats = c.fetchone()
            uptime = (
                (stats["up_count"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            result.append(
                {
                    **dict(site),
                    "status": last_status["status"] if last_status else "unknown",
                    "uptime": round(uptime, 2),
                    "notify_methods": json.loads(site["notify_methods"])
                    if site["notify_methods"]
                    else [],
                }
            )
    return result


@app.get("/api/sites/{site_id}/history")
async def get_site_history(site_id: int, limit: int = 50):
    """Get status history for a site (for status bars chart)"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT status, status_code, checked_at FROM status_history WHERE site_id = ? ORDER BY checked_at DESC LIMIT ?",
            (site_id, limit),
        )
        history = c.fetchall()
    return [
        {
            "status": h["status"],
            "status_code": h["status_code"],
            "checked_at": h["checked_at"],
        }
        for h in history
    ]


@app.post("/api/sites")
async def add_site(site: SiteCreate, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    m_type = site.monitor_type.lower()
    url = _normalize_and_validate_url(site.url, m_type)

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO sites (name, url, check_interval, is_active, notify_methods, monitor_type) VALUES (?, ?, ?, ?, ?, ?)",
            (
                site.name,
                url,
                site.check_interval,
                site.is_active,
                json.dumps(site.notify_methods),
                m_type,
            ),
        )
        site_id = c.lastrowid
        conn.commit()

    # Run initial check
    asyncio.create_task(
        monitoring.check_site_status(site_id, url, site.notify_methods, NOTIFY_SETTINGS)
    )
    if m_type == "ssl" or url.lower().startswith("https://"):
        asyncio.create_task(
            monitoring.check_site_certificate(
                site_id, url, site.notify_methods, NOTIFY_SETTINGS
            )
        )

    return {"id": site_id, "message": "Site added"}


@app.put("/api/sites/{site_id}")
async def update_site(
    site_id: int, site: SiteUpdate, user: dict = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT name, url, check_interval, is_active, notify_methods, monitor_type FROM sites WHERE id = ?",
            (site_id,),
        )
        existing = c.fetchone()
        if not existing:
            raise HTTPException(404, "Site not found")

        # Use existing values if not provided
        name = site.name if site.name is not None else existing["name"]
        current_monitor_type = existing["monitor_type"] or "http"
        url = (
            _normalize_and_validate_url(site.url, current_monitor_type)
            if site.url is not None
            else existing["url"]
        )
        is_active = (
            site.is_active if site.is_active is not None else existing["is_active"]
        )
        notify_methods = (
            json.dumps(site.notify_methods)
            if site.notify_methods is not None
            else existing["notify_methods"]
        )

        c.execute(
            "UPDATE sites SET name = ?, url = ?, is_active = ?, notify_methods = ? WHERE id = ?",
            (name, url, is_active, notify_methods, site_id),
        )
        conn.commit()
    return {"message": "Updated"}


@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: int, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    models.delete_site(DB_PATH, site_id)
    return {"message": "Deleted"}


@app.post("/api/sites/{site_id}/check")
async def manual_check(site_id: int, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT url, notify_methods FROM sites WHERE id = ?", (site_id,))
        site = c.fetchone()
    if not site:
        raise HTTPException(404)
    methods = json.loads(site["notify_methods"]) if site["notify_methods"] else []
    await monitoring.check_site_status(site_id, site["url"], methods, NOTIFY_SETTINGS)
    return {"message": "Check triggered"}


@app.get("/api/ssl-certificates")
async def get_ssl_certs(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    return models.get_ssl_certificates(DB_PATH)


@app.post("/api/ssl-certificates/check")
async def manual_ssl_check(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    await monitoring.check_all_certificates(NOTIFY_SETTINGS)
    return {"message": "SSL check triggered"}


@app.get("/api/stats/response-time")
async def get_response_time_stats(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT site_id, s.name as site_name, AVG(sh.response_time) as avg_time, MIN(sh.response_time) as min_time, MAX(sh.response_time) as max_time, COUNT(*) as checks
            FROM status_history sh
            JOIN sites s ON sh.site_id = s.id
            WHERE sh.checked_at >= datetime('now', '-24 hours') AND sh.response_time IS NOT NULL
            GROUP BY site_id
            ORDER BY avg_time ASC
        """)
        results = c.fetchall()
        return [
            {
                "site_id": r["site_id"],
                "site_name": r["site_name"],
                "avg_time": round(r["avg_time"], 1) if r["avg_time"] else 0,
                "min_time": round(r["min_time"], 1) if r["min_time"] else 0,
                "max_time": round(r["max_time"], 1) if r["max_time"] else 0,
                "checks": r["checks"],
            }
            for r in results
        ]


@app.get("/api/incidents")
async def get_incidents(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    with get_db_connection() as conn:
        c = conn.cursor()
        # Get incidents (status changes to down/slow in last 7 days)
        c.execute("""
            SELECT 
                sh.id, 
                sh.site_id, 
                s.name as site_name, 
                s.url as site_url,
                sh.status, 
                sh.status_code, 
                sh.response_time, 
                sh.error_message, 
                sh.checked_at
            FROM status_history sh
            JOIN sites s ON sh.site_id = s.id
            WHERE sh.status IN ('down', 'slow')
            AND sh.checked_at >= datetime('now', '-7 days')
            ORDER BY sh.checked_at DESC
            LIMIT 50
        """)
        results = c.fetchall()

        # Get first and last occurrence for each status
        c.execute("""
            SELECT 
                sh.site_id,
                sh.status,
                MIN(sh.checked_at) as started_at,
                MAX(sh.checked_at) as ended_at
            FROM status_history sh
            WHERE sh.checked_at >= datetime('now', '-7 days')
            GROUP BY sh.site_id, sh.status
            HAVING sh.status IN ('down', 'slow')
        """)
        down_times = {f"{r['site_id']}_{r['status']}": dict(r) for r in c.fetchall()}

        incidents = []
        for r in results:
            inc = {
                "id": r["id"],
                "site_id": r["site_id"],
                "site_name": r["site_name"],
                "site_url": r["site_url"],
                "status": r["status"],
                "status_code": r["status_code"],
                "response_time": r["response_time"],
                "error_message": r["error_message"],
                "checked_at": r["checked_at"],
                "prev_status": None,
            }

            # Add duration
            key = f"{inc['site_id']}_{inc['status']}"
            if key in down_times:
                dt = down_times[key]
                started = dt["started_at"]
                ended = dt["ended_at"] if dt["ended_at"] else None
                if started and ended:
                    try:
                        from datetime import datetime

                        start = datetime.fromisoformat(started.replace("Z", "+00:00"))
                        end = datetime.fromisoformat(ended.replace("Z", "+00:00"))
                        duration = end - start
                        hours = duration.total_seconds() // 3600
                        mins = (duration.total_seconds() % 3600) // 60
                        inc["duration"] = (
                            f"{int(hours)}год {int(mins)}хв"
                            if hours > 0
                            else f"{int(mins)}хв"
                        )
                    except:
                        inc["duration"] = None
                else:
                    inc["duration"] = "в процесі"
            else:
                inc["duration"] = None

            incidents.append(inc)

        return incidents


@app.post("/api/notify-settings")
async def save_notify(
    settings: NotifySettingsModel, user: dict = Depends(get_current_user)
):
    if not user:
        raise HTTPException(401)
    global NOTIFY_SETTINGS
    new_data = settings.dict(exclude_unset=True)
    for k, v in new_data.items():
        if v is not None:
            NOTIFY_SETTINGS[k] = v
    models.save_notify_settings(DB_PATH, NOTIFY_SETTINGS)
    return {"message": "Saved"}


@app.post("/api/app-settings")
async def save_app(settings: AppSettingsModel, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    global DISPLAY_ADDRESS
    DISPLAY_ADDRESS = settings.display_address
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO app_settings (id, display_address) VALUES (1, ?)",
            (DISPLAY_ADDRESS,),
        )
        conn.commit()
    return {"message": "Saved"}


@app.get("/api/app-settings")
async def get_app(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    return {"display_address": DISPLAY_ADDRESS}


@app.get("/api/user")
async def get_user_info(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(401)
    return {"username": user["username"], "is_admin": user.get("is_admin", False)}


# --- Background Task & Service ---

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Uptime Monitor")
    parser.add_argument(
        "--host",
        type=str,
        default=CONFIG["server"].get("host", "0.0.0.0"),
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=CONFIG["server"].get("port", 8080),
        help="Port to bind to",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["install", "remove", "start", "stop", "restart"],
        help="Service command",
    )

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
        target=lambda: asyncio.run(
            monitoring.monitor_loop(NOTIFY_SETTINGS, CHECK_INTERVAL)
        ),
        daemon=True,
    )
    monitor_thread.start()

    ssl_context = config_manager.setup_ssl(CONFIG)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        ssl_keyfile=CONFIG["ssl"].get("key_path") if ssl_context else None,
        ssl_certfile=CONFIG["ssl"].get("cert_path") if ssl_context else None,
        log_level="info",
    )
