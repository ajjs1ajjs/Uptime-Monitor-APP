import sys
import os
import json
import sqlite3
import asyncio
import aiohttp
import smtplib
import socket
import servicemanager
import win32serviceutil
import win32service
import win32event
from datetime import datetime
from email.mime.text import MIMEText
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from ssl_checker import check_ssl_certificate, format_certificate_alert

# Configuration
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "sites.db")
CHECK_INTERVAL = 60
DEFAULT_PORT = 8080

NOTIFY_SETTINGS = {
    "telegram": {"enabled": False, "token": "", "chat_id": ""},
    "teams": {"enabled": False, "webhook_url": ""},
    "discord": {"enabled": False, "webhook_url": ""},
    "slack": {"enabled": False, "webhook_url": ""},
    "email": {
        "enabled": False,
        "smtp_server": "",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "to_email": "",
    },
    "sms": {
        "enabled": False,
        "account_sid": "",
        "auth_token": "",
        "from_number": "",
        "to_number": "",
    },
}

app = FastAPI(title="Uptime Monitor Service")


# Database functions
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        check_interval INTEGER DEFAULT 60,
        is_active BOOLEAN DEFAULT 1,
        last_notification TEXT,
        notify_methods TEXT DEFAULT '[]'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        status TEXT,
        status_code INTEGER,
        response_time REAL,
        error_message TEXT,
        checked_at TEXT,
        FOREIGN KEY (site_id) REFERENCES sites(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notify_config (
        id INTEGER PRIMARY KEY,
        config TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ssl_certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        hostname TEXT,
        issuer TEXT,
        subject TEXT,
        start_date TEXT,
        expire_date TEXT,
        days_until_expire INTEGER,
        is_valid BOOLEAN,
        last_notified TEXT,
        last_checked TEXT,
        FOREIGN KEY (site_id) REFERENCES sites(id)
    )""")
    conn.commit()
    conn.close()


init_db()


# Pydantic models
class Site(BaseModel):
    id: Optional[int] = None
    name: str
    url: str
    check_interval: int = 60
    is_active: bool = True


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


# Load notification settings
def load_notify_settings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT config FROM notify_config WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if row:
        global NOTIFY_SETTINGS
        NOTIFY_SETTINGS = json.loads(row["config"])


load_notify_settings()


# Notification functions
async def send_notification(message: str, methods: List[str]):
    tasks = []
    for method in methods:
        if method == "telegram" and NOTIFY_SETTINGS["telegram"]["enabled"]:
            tasks.append(send_telegram(message))
        elif method == "teams" and NOTIFY_SETTINGS["teams"]["enabled"]:
            tasks.append(send_teams(message))
        elif method == "discord" and NOTIFY_SETTINGS["discord"]["enabled"]:
            tasks.append(send_discord(message))
        elif method == "slack" and NOTIFY_SETTINGS["slack"]["enabled"]:
            tasks.append(send_slack(message))
        elif method == "email" and NOTIFY_SETTINGS["email"]["enabled"]:
            tasks.append(send_email(message))
        elif method == "sms" and NOTIFY_SETTINGS["sms"]["enabled"]:
            tasks.append(send_sms(message))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_telegram(message: str):
    settings = NOTIFY_SETTINGS["telegram"]
    if not settings.get("token") or not settings.get("chat_id"):
        return
    try:
        url = f"https://api.telegram.org/bot{settings['token']}/sendMessage"
        async with aiohttp.ClientSession() as session:
            await session.post(
                url,
                json={
                    "chat_id": settings["chat_id"],
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
    except Exception as e:
        print(f"Telegram error: {e}")


async def send_teams(message: str):
    settings = NOTIFY_SETTINGS["teams"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings["webhook_url"], json=payload)
    except Exception as e:
        print(f"Teams error: {e}")


async def send_discord(message: str):
    settings = NOTIFY_SETTINGS["discord"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"content": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings["webhook_url"], json=payload)
    except Exception as e:
        print(f"Discord error: {e}")


async def send_slack(message: str):
    settings = NOTIFY_SETTINGS["slack"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings["webhook_url"], json=payload)
    except Exception as e:
        print(f"Slack error: {e}")


async def send_email(message: str):
    settings = NOTIFY_SETTINGS["email"]
    if not all(
        [
            settings.get("smtp_server"),
            settings.get("username"),
            settings.get("password"),
            settings.get("to_email"),
        ]
    ):
        return
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "Uptime Alert"
        msg["From"] = settings["username"]
        msg["To"] = settings["to_email"]

        with smtplib.SMTP(
            settings["smtp_server"], settings.get("smtp_port", 587)
        ) as server:
            server.starttls()
            server.login(settings["username"], settings["password"])
            server.send_message(msg)
    except Exception as e:
        print(f"Email error: {e}")


async def send_sms(message: str):
    settings = NOTIFY_SETTINGS["sms"]
    if not all(
        [
            settings.get("account_sid"),
            settings.get("auth_token"),
            settings.get("from_number"),
            settings.get("to_number"),
        ]
    ):
        return
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings['account_sid']}/Messages.json"
        auth = aiohttp.BasicAuth(settings["account_sid"], settings["auth_token"])
        payload = {
            "From": settings["from_number"],
            "To": settings["to_number"],
            "Body": message[:1600],
        }
        async with aiohttp.ClientSession() as session:
            await session.post(url, data=payload, auth=auth)
    except Exception as e:
        print(f"SMS error: {e}")


# Site checking functions
async def check_site_status(site_id: int, url: str, notify_methods: List[str]):
    start_time = datetime.now()
    status = "down"
    status_code = None
    response_time = None
    error_message = None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15),
                headers=headers,
                allow_redirects=True,
            ) as response:
                status_code = response.status
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                status = "up" if status_code < 500 else "down"
    except aiohttp.ClientConnectorError:
        error_message = "Connection failed"
    except asyncio.TimeoutError:
        error_message = "Timeout"
    except Exception as e:
        error_message = str(e)[:100]

    checked_at = datetime.now().isoformat()

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name, last_notification FROM sites WHERE id = ?", (site_id,))
    site = c.fetchone()

    c.execute(
        """INSERT INTO status_history (site_id, status, status_code, response_time, error_message, checked_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
        (
            site_id,
            status,
            status_code,
            round(response_time, 2) if response_time else None,
            error_message,
            checked_at,
        ),
    )

    # Очищення старих записів (старші за 30 днів)
    c.execute(
        "DELETE FROM status_history WHERE checked_at < datetime('now', '-30 days')"
    )

    conn.commit()

    if status == "down" and site and notify_methods:
        now = datetime.now()
        should_notify = True
        if site["last_notification"]:
            last_notif = datetime.fromisoformat(site["last_notification"])
            if (now - last_notif).total_seconds() < 300:
                should_notify = False

        if should_notify:
            msg = f"🔴 {site['name']}\n🌐 {url}\nStatus: {status_code or 'N/A'}\nError: {error_message or 'None'}\nTime: {checked_at}"
            await send_notification(msg, notify_methods)

            c.execute(
                "UPDATE sites SET last_notification = ? WHERE id = ?",
                (checked_at, site_id),
            )
            conn.commit()

    conn.close()
    return status, status_code, response_time, error_message


async def check_site_certificate(site_id: int, url: str, notify_methods: List[str]):
    if not url.startswith("https://"):
        return

    cert_info = await check_ssl_certificate(url)
    if not cert_info:
        return

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT name FROM sites WHERE id = ?", (site_id,))
    site = c.fetchone()
    site_name = site["name"] if site else url

    c.execute(
        """
        INSERT OR REPLACE INTO ssl_certificates 
        (site_id, hostname, issuer, subject, start_date, expire_date, days_until_expire, is_valid, last_checked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            site_id,
            cert_info["hostname"],
            cert_info["issuer"],
            cert_info["subject"],
            cert_info["start_date"],
            cert_info["expire_date"],
            cert_info["days_until_expire"],
            cert_info["is_valid"],
            cert_info["checked_at"],
        ),
    )
    conn.commit()

    days = cert_info["days_until_expire"]

    if days <= 14:
        c.execute(
            "SELECT last_notified FROM ssl_certificates WHERE site_id = ?", (site_id,)
        )
        row = c.fetchone()

        should_notify = True
        if row and row["last_notified"]:
            last_notif = datetime.fromisoformat(row["last_notified"])
            if (datetime.now() - last_notif).total_seconds() < 86400:
                should_notify = False

        if should_notify and notify_methods:
            msg = format_certificate_alert(cert_info, site_name, url)
            await send_notification(msg, notify_methods)

            c.execute(
                "UPDATE ssl_certificates SET last_notified = ? WHERE site_id = ?",
                (datetime.now().isoformat(), site_id),
            )
            conn.commit()

    conn.close()


# Background monitoring task
async def monitor_loop():
    while True:
        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id, url, notify_methods FROM sites WHERE is_active = 1")
            sites = c.fetchall()
            conn.close()

            for site in sites:
                notify_methods = (
                    json.loads(site["notify_methods"]) if site["notify_methods"] else []
                )
                await check_site_status(site["id"], site["url"], notify_methods)
                if site["url"].startswith("https://"):
                    await check_site_certificate(
                        site["id"], site["url"], notify_methods
                    )
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Monitor error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sites ORDER BY id")
    sites = c.fetchall()

    site_data = []
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
        uptime = (stats["up_count"] / stats["total"] * 100) if stats["total"] > 0 else 0

        notify_methods = (
            json.loads(site["notify_methods"]) if site["notify_methods"] else []
        )

        site_data.append(
            {
                "id": site["id"],
                "name": site["name"],
                "url": site["url"],
                "is_active": site["is_active"],
                "status": last_status["status"] if last_status else "unknown",
                "status_code": last_status["status_code"] if last_status else None,
                "response_time": last_status["response_time"] if last_status else None,
                "error_message": last_status["error_message"] if last_status else None,
                "last_checked": last_status["checked_at"] if last_status else None,
                "uptime": round(uptime, 2),
                "notify_methods": notify_methods,
            }
        )
    conn.close()

    total_sites = len(site_data)
    up_sites = sum(1 for s in site_data if s["status"] == "up")
    down_sites = sum(1 for s in site_data if s["status"] == "down")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"

    notify_config_json = json.dumps(NOTIFY_SETTINGS)

    html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uptime Monitor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f0f23;
            --bg-secondary: #1a1a2e;
            --bg-card: #16213e;
            --accent: #00d9ff;
            --accent-hover: #00a8cc;
            --success: #00ff88;
            --danger: #ff4757;
            --warning: #ffd93d;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --border: #2a2a4a;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; }}
        
        .header {{ background: linear-gradient(135deg, var(--bg-secondary) 0%, #1f1f3a 100%); padding: 20px 40px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px; }}
        .logo-icon {{ width: 40px; height: 40px; background: var(--accent); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }}
        
        .stats-bar {{ display: flex; gap: 20px; margin: 30px 40px; }}
        .stat-card {{ background: var(--bg-card); padding: 20px 30px; border-radius: 15px; flex: 1; border: 1px solid var(--border); }}
        .stat-value {{ font-size: 32px; font-weight: 700; }}
        .stat-label {{ color: var(--text-secondary); font-size: 14px; margin-top: 5px; }}
        .stat-card.total .stat-value {{ color: var(--accent); }}
        .stat-card.up .stat-value {{ color: var(--success); }}
        .stat-card.down .stat-value {{ color: var(--danger); }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 0 40px 40px; }}
        
        .panel {{ background: var(--bg-card); padding: 25px; border-radius: 15px; margin-bottom: 30px; border: 1px solid var(--border); }}
        .panel-title {{ font-size: 18px; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
        
        .server-info {{ background: var(--bg-card); padding: 20px; border-radius: 15px; margin-bottom: 30px; border: 1px solid var(--accent); text-align: center; }}
        .server-info .label {{ color: var(--text-secondary); font-size: 14px; }}
        .server-info .value {{ color: var(--accent); font-size: 24px; font-weight: 700; margin-top: 5px; }}
        
        .notify-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; }}
        .notify-card {{ background: var(--bg-secondary); padding: 20px; border-radius: 12px; border: 1px solid var(--border); }}
        .notify-card.enabled {{ border-color: var(--success); }}
        .notify-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .notify-name {{ font-weight: 600; display: flex; align-items: center; gap: 8px; }}
        .toggle {{ position: relative; width: 50px; height: 26px; }}
        .toggle input {{ opacity: 0; width: 0; height: 0; }}
        .toggle-slider {{ position: absolute; cursor: pointer; inset: 0; background: var(--border); border-radius: 26px; transition: 0.3s; }}
        .toggle-slider:before {{ content: ''; position: absolute; height: 20px; width: 20px; left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: 0.3s; }}
        .toggle input:checked + .toggle-slider {{ background: var(--success); }}
        .toggle input:checked + .toggle-slider:before {{ transform: translateX(24px); }}
        
        .notify-fields {{ display: none; }}
        .notify-card.enabled .notify-fields {{ display: block; }}
        .notify-fields input {{ width: 100%; padding: 10px; margin-bottom: 10px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-size: 13px; }}
        .notify-fields input:focus {{ outline: none; border-color: var(--accent); }}
        
        .form-row {{ display: flex; gap: 15px; flex-wrap: wrap; }}
        .form-row input {{ flex: 1; min-width: 200px; padding: 12px 15px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg-secondary); color: var(--text-primary); font-size: 14px; }}
        .form-row input:focus {{ outline: none; border-color: var(--accent); }}
        .form-row button {{ padding: 12px 30px; background: var(--accent); border: none; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 14px; transition: all 0.3s; }}
        .form-row button:hover {{ background: var(--accent-hover); transform: translateY(-2px); }}
        
        .sites-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }}
        .site-card {{ background: var(--bg-card); padding: 25px; border-radius: 15px; border: 1px solid var(--border); transition: all 0.3s; }}
        .site-card:hover {{ transform: translateY(-3px); border-color: var(--accent); box-shadow: 0 10px 30px rgba(0,217,255,0.1); }}
        .site-card.up {{ border-left: 4px solid var(--success); }}
        .site-card.down {{ border-left: 4px solid var(--danger); }}
        
        .site-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
        .site-name {{ font-size: 18px; font-weight: 600; }}
        .site-url {{ color: var(--text-secondary); font-size: 13px; word-break: break-all; margin-top: 5px; }}
        
        .status-badge {{ padding: 6px 15px; border-radius: 20px; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        .status-badge.up {{ background: rgba(0,255,136,0.15); color: var(--success); }}
        .status-badge.down {{ background: rgba(255,71,87,0.15); color: var(--danger); }}
        
        .site-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; padding: 15px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
        .site-stat {{ text-align: center; }}
        .site-stat-value {{ font-size: 20px; font-weight: 700; }}
        .site-stat-label {{ font-size: 12px; color: var(--text-secondary); margin-top: 3px; }}
        
        .notify-badges {{ display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 15px; }}
        .notify-badge {{ padding: 4px 10px; background: var(--bg-secondary); border-radius: 5px; font-size: 11px; color: var(--text-secondary); }}
        
        .site-actions {{ display: flex; gap: 10px; }}
        .btn {{ flex: 1; padding: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; font-size: 13px; transition: all 0.2s; }}
        .btn-check {{ background: var(--accent); color: #000; }}
        .btn-check:hover {{ background: var(--accent-hover); }}
        .btn-edit {{ background: rgba(255,217,61,0.2); color: var(--warning); }}
        .btn-edit:hover {{ background: var(--warning); color: #000; }}
        .btn-delete {{ background: rgba(255,71,87,0.2); color: var(--danger); }}
        .btn-delete:hover {{ background: var(--danger); color: #fff; }}
        
        .refresh-info {{ text-align: center; margin-top: 30px; color: var(--text-secondary); }}
        
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; }}
        .modal.active {{ display: flex; }}
        .modal-content {{ background: var(--bg-card); padding: 30px; border-radius: 15px; max-width: 500px; width: 90%; border: 1px solid var(--border); }}
        .modal-title {{ font-size: 20px; font-weight: 600; margin-bottom: 20px; }}
        .modal-field {{ margin-bottom: 15px; }}
        .modal-field label {{ display: block; margin-bottom: 5px; color: var(--text-secondary); font-size: 13px; }}
        .modal-field input, .modal-field select {{ width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-secondary); color: var(--text-primary); }}
        .modal-actions {{ display: flex; gap: 10px; margin-top: 20px; }}
        .modal-actions button {{ flex: 1; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo"><div class="logo-icon">⚡</div><span>Uptime Monitor</span></div>
        <div id="lastUpdate" style="color: var(--text-secondary); font-size: 14px;"></div>
    </div>
    
    <div class="container">
        <div class="server-info">
            <div class="label">Доступ за адресою:</div>
            <div class="value">http://{local_ip}:8000</div>
        </div>
        
        <div class="panel">
            <div class="panel-title">🔧 Налаштування сповіщень</div>
            <div class="notify-grid">
                <div class="notify-card" id="card-telegram">
                    <div class="notify-header">
                        <div class="notify-name">📱 Telegram</div>
                        <label class="toggle"><input type="checkbox" id="toggle-telegram" onchange="toggleNotify('telegram')"><span class="toggle-slider"></span></label>
                    </div>
                    <div class="notify-fields">
                        <input type="text" id="telegram-token" placeholder="Bot Token">
                        <input type="text" id="telegram-chatid" placeholder="Chat ID">
                    </div>
                </div>
                
                <div class="notify-card" id="card-teams">
                    <div class="notify-header">
                        <div class="notify-name">🏢 MS Teams</div>
                        <label class="toggle"><input type="checkbox" id="toggle-teams" onchange="toggleNotify('teams')"><span class="toggle-slider"></span></label>
                    </div>
                    <div class="notify-fields">
                        <input type="text" id="teams-webhook" placeholder="Webhook URL">
                    </div>
                </div>
                
                <div class="notify-card" id="card-discord">
                    <div class="notify-header">
                        <div class="notify-name">🎮 Discord</div>
                        <label class="toggle"><input type="checkbox" id="toggle-discord" onchange="toggleNotify('discord')"><span class="toggle-slider"></span></label>
                    </div>
                    <div class="notify-fields">
                        <input type="text" id="discord-webhook" placeholder="Webhook URL">
                    </div>
                </div>
                
                <div class="notify-card" id="card-slack">
                    <div class="notify-header">
                        <div class="notify-name">💬 Slack</div>
                        <label class="toggle"><input type="checkbox" id="toggle-slack" onchange="toggleNotify('slack')"><span class="toggle-slider"></span></label>
                    </div>
                    <div class="notify-fields">
                        <input type="text" id="slack-webhook" placeholder="Webhook URL">
                    </div>
                </div>
                
                <div class="notify-card" id="card-email">
                    <div class="notify-header">
                        <div class="notify-name">📧 Email (SMTP)</div>
                        <label class="toggle"><input type="checkbox" id="toggle-email" onchange="toggleNotify('email')"><span class="toggle-slider"></span></label>
                    </div>
                    <div class="notify-fields">
                        <input type="text" id="email-smtp" placeholder="SMTP Server (smtp.gmail.com)">
                        <input type="text" id="email-port" placeholder="Port (587)">
                        <input type="text" id="email-user" placeholder="Username / Email">
                        <input type="password" id="email-pass" placeholder="Password / App Password">
                        <input type="text" id="email-to" placeholder="To Email">
                    </div>
                </div>
                
                <div class="notify-card" id="card-sms">
                    <div class="notify-header">
                        <div class="notify-name">📱 SMS (Twilio)</div>
                        <label class="toggle"><input type="checkbox" id="toggle-sms" onchange="toggleNotify('sms')"><span class="toggle-slider"></span></label>
                    </div>
                    <div class="notify-fields">
                        <input type="text" id="sms-sid" placeholder="Account SID">
                        <input type="password" id="sms-token" placeholder="Auth Token">
                        <input type="text" id="sms-from" placeholder="From Number">
                        <input type="text" id="sms-to" placeholder="To Number">
                    </div>
                </div>
            </div>
            <button class="btn btn-check" style="margin-top: 20px; width: 100%;" onclick="saveNotifySettings()">💾 Зберегти налаштування</button>
        </div>
        
        <div class="stats-bar">
            <div class="stat-card total"><div class="stat-value">{total_sites}</div><div class="stat-label">Всього сайтів</div></div>
            <div class="stat-card up"><div class="stat-value">{up_sites}</div><div class="stat-label">Працюють</div></div>
            <div class="stat-card down"><div class="stat-value">{down_sites}</div><div class="stat-label">Недоступні</div></div>
        </div>
        
        <div class="panel">
            <div class="panel-title">➕ Додати новий сайт</div>
            <div class="form-row">
                <input type="text" id="siteName" placeholder="Назва сайту">
                <input type="url" id="siteUrl" placeholder="URL (https://example.com)">
                <select id="siteNotify" multiple style="flex:1; min-width:200px; padding:12px; border-radius:10px; background:var(--bg-secondary); color:var(--text-primary); border:1px solid var(--border);">
                    <option value="telegram">📱 Telegram</option>
                    <option value="teams">🏢 MS Teams</option>
                    <option value="discord">🎮 Discord</option>
                    <option value="slack">💬 Slack</option>
                    <option value="email">📧 Email</option>
                    <option value="sms">📱 SMS</option>
                </select>
                <button onclick="addSite()">Додати сайт</button>
            </div>
            <div style="margin-top: 10px; color: var(--text-secondary); font-size: 12px;">Виберіть способи сповіщень (Ctrl+Click для вибору кількох)</div>
        </div>
        
        <div class="panel">
            <div class="panel-title">📊 Моніторинг сайтів</div>
            <div class="sites-grid" id="sitesGrid"></div>
        </div>
        
        <p class="refresh-info">Сторінка автоматично оновлюється кожні 30 секунд</p>
    </div>
    
    <div class="modal" id="editModal">
        <div class="modal-content">
            <div class="modal-title">✏️ Редагування сайту</div>
            <input type="hidden" id="editSiteId">
            <div class="modal-field">
                <label>Назва</label>
                <input type="text" id="editSiteName">
            </div>
            <div class="modal-field">
                <label>URL</label>
                <input type="url" id="editSiteUrl">
            </div>
            <div class="modal-field">
                <label>Способи сповіщень</label>
                <select id="editSiteNotify" multiple style="height: 120px;">
                    <option value="telegram">📱 Telegram</option>
                    <option value="teams">🏢 MS Teams</option>
                    <option value="discord">🎮 Discord</option>
                    <option value="slack">💬 Slack</option>
                    <option value="email">📧 Email</option>
                    <option value="sms">📱 SMS</option>
                </select>
            </div>
            <div class="modal-actions">
                <button onclick="closeEditModal()" style="background: var(--border); color: var(--text-primary);">Скасувати</button>
                <button onclick="saveEdit()" style="background: var(--accent); color: #000;">💾 Зберегти</button>
            </div>
        </div>
    </div>
    
    <script>
        // const notifyConfig removed - using empty object
        var notifyConfig = {};
        
        function initNotifyUI() {{
            ['telegram', 'teams', 'discord', 'slack', 'email', 'sms'].forEach(method => {{
                const config = notifyConfig[method];
                const card = document.getElementById('card-' + method);
                const toggle = document.getElementById('toggle-' + method);
                if (config && config.enabled) {{
                    card.classList.add('enabled');
                    toggle.checked = true;
                }}
                if (method === 'telegram') {{
                    document.getElementById('telegram-token').value = config?.token || '';
                    document.getElementById('telegram-chatid').value = config?.chat_id || '';
                }} else if (method === 'teams') {{
                    document.getElementById('teams-webhook').value = config?.webhook_url || '';
                }} else if (method === 'discord') {{
                    document.getElementById('discord-webhook').value = config?.webhook_url || '';
                }} else if (method === 'slack') {{
                    document.getElementById('slack-webhook').value = config?.webhook_url || '';
                }} else if (method === 'email') {{
                    document.getElementById('email-smtp').value = config?.smtp_server || '';
                    document.getElementById('email-port').value = config?.smtp_port || '587';
                    document.getElementById('email-user').value = config?.username || '';
                    document.getElementById('email-pass').value = config?.password || '';
                    document.getElementById('email-to').value = config?.to_email || '';
                }} else if (method === 'sms') {{
                    document.getElementById('sms-sid').value = config?.account_sid || '';
                    document.getElementById('sms-token').value = config?.auth_token || '';
                    document.getElementById('sms-from').value = config?.from_number || '';
                    document.getElementById('sms-to').value = config?.to_number || '';
                }}
            }});
        }}
        
        function toggleNotify(method) {{
            const card = document.getElementById('card-' + method);
            const toggle = document.getElementById('toggle-' + method);
            if (toggle.checked) card.classList.add('enabled');
            else card.classList.remove('enabled');
        }}
        
        async function saveNotifySettings() {{
            const settings = {{
                telegram: {{ enabled: document.getElementById('toggle-telegram').checked, token: document.getElementById('telegram-token').value, chat_id: document.getElementById('telegram-chatid').value }},
                teams: {{ enabled: document.getElementById('toggle-teams').checked, webhook_url: document.getElementById('teams-webhook').value }},
                discord: {{ enabled: document.getElementById('toggle-discord').checked, webhook_url: document.getElementById('discord-webhook').value }},
                slack: {{ enabled: document.getElementById('toggle-slack').checked, webhook_url: document.getElementById('slack-webhook').value }},
                email: {{ enabled: document.getElementById('toggle-email').checked, smtp_server: document.getElementById('email-smtp').value, smtp_port: parseInt(document.getElementById('email-port').value) || 587, username: document.getElementById('email-user').value, password: document.getElementById('email-pass').value, to_email: document.getElementById('email-to').value }},
                sms: {{ enabled: document.getElementById('toggle-sms').checked, account_sid: document.getElementById('sms-sid').value, auth_token: document.getElementById('sms-token').value, from_number: document.getElementById('sms-from').value, to_number: document.getElementById('sms-to').value }}
            }};
            await fetch('/api/notify-settings', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(settings) }});
            alert('✅ Налаштування збережено!');
        }}
        
        let sitesData = [];
        
        async function loadSites() {{
            try {{
                const response = await fetch('/api/sites');
                sitesData = await response.json();
                renderSites();
                document.getElementById('lastUpdate').textContent = 'Оновлено: ' + new Date().toLocaleTimeString('uk-UA');
            }} catch(e) {{ console.error(e); }}
        }}
        
        function renderSites() {{
            const grid = document.getElementById('sitesGrid');
            if (sitesData.length === 0) {{
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Немає сайтів для моніторингу. Додайте перший сайт!</div>';
                return;
            }}
            grid.innerHTML = sitesData.map(site => {{
                const notifyBadges = (site.notify_methods || []).map(m => {{ const names = {{telegram:'📱 Telegram', teams:'🏢 Teams', discord:'🎮 Discord', slack:'💬 Slack', email:'📧 Email', sms:'📱 SMS'}}; return '<span class="notify-badge">' + (names[m] || m) + '</span>' }}).join('');
                return `
                <div class="site-card ${{site.status}}">
                    <div class="site-header">
                        <div><div class="site-name">${{site.name}}</div><div class="site-url">${{site.url}}</div></div>
                        <span class="status-badge ${{site.status}}">${{site.status === 'up' ? '✓ ONLINE' : '✗ OFFLINE'}}</span>
                    </div>
                    <div class="notify-badges">${{notifyBadges}}</div>
                    <div class="site-stats">
                        <div class="site-stat"><div class="site-stat-value" style="color: ${{site.response_time < 500 ? 'var(--success)' : site.response_time < 1000 ? 'var(--warning)' : 'var(--danger)'}}">${{site.response_time ? site.response_time + 'ms' : 'N/A'}}</div><div class="site-stat-label">Час відповіді</div></div>
                        <div class="site-stat"><div class="site-stat-value" style="color: ${{site.uptime >= 99 ? 'var(--success)' : site.uptime >= 95 ? 'var(--warning)' : 'var(--danger)'}}">${{site.uptime}}%</div><div class="site-stat-label">Uptime</div></div>
                        <div class="site-stat"><div class="site-stat-value">${{site.status_code || '—'}}</div><div class="site-stat-label">HTTP код</div></div>
                    </div>
                    ${{site.error_message ? `<div style="color: var(--danger); font-size: 12px; margin-bottom: 10px;">⚠️ ${{site.error_message}}</div>` : ''}}
                    <div class="site-actions">
                        <button class="btn btn-check" onclick="checkSite(${{site.id}})">🔄 Перевірити</button>
                        <button class="btn btn-edit" onclick="openEditModal(${{site.id}}, '${{site.name}}', '${{site.url}}', '${{JSON.stringify(site.notify_methods).replace(/'/g, "\\'")}}')">✏️ Редагувати</button>
                        <button class="btn btn-delete" onclick="deleteSite(${{site.id}})">🗑️ Видалити</button>
                    </div>
                </div>`;
            }}).join('');
        }}
        
        async function addSite() {{
            const name = document.getElementById('siteName').value.trim();
            const url = document.getElementById('siteUrl').value.trim();
            const notifySelect = document.getElementById('siteNotify');
            const notifyMethods = Array.from(notifySelect.selectedOptions).map(o => o.value);
            if (!name || !url) return alert('Заповніть всі поля!');
            
            await fetch('/api/sites', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{name, url, notify_methods: notifyMethods}})
            }});
            document.getElementById('siteName').value = '';
            document.getElementById('siteUrl').value = '';
            loadSites();
        }}
        
        async function deleteSite(id) {{
            if (!confirm('Видалити сайт з моніторингу?')) return;
            await fetch(`/api/sites/${{id}}`, {{method: 'DELETE'}});
            loadSites();
        }}
        
        async function checkSite(id) {{
            await fetch(`/api/sites/${{id}}/check`, {{method: 'POST'}});
            loadSites();
        }}
        
        function openEditModal(id, name, url, notifyMethods) {{
            document.getElementById('editSiteId').value = id;
            document.getElementById('editSiteName').value = name;
            document.getElementById('editSiteUrl').value = url;
            
            const select = document.getElementById('editSiteNotify');
            Array.from(select.options).forEach(opt => {{
                opt.selected = notifyMethods.includes(opt.value);
            }});
            
            document.getElementById('editModal').classList.add('active');
        }}
        
        function closeEditModal() {{
            document.getElementById('editModal').classList.remove('active');
        }}
        
        async function saveEdit() {{
            const id = document.getElementById('editSiteId').value;
            const name = document.getElementById('editSiteName').value.trim();
            const url = document.getElementById('editSiteUrl').value.trim();
            const notifySelect = document.getElementById('editSiteNotify');
            const notifyMethods = Array.from(notifySelect.selectedOptions).map(o => o.value);
            
            if (!name || !url) return alert('Заповніть всі поля!');
            
            await fetch(`/api/sites/${{id}}`, {{
                method: 'PUT',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{name, url, notify_methods: notifyMethods}})
            }});
            
            closeEditModal();
            loadSites();
        }}
        
        initNotifyUI();
        loadSites();
        setInterval(loadSites, 30000);
    </script>
</body>
</html>"""
    return html


@app.get("/api/sites")
async def get_sites():
    conn = get_db_connection()
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
        uptime = (stats["up_count"] / stats["total"] * 100) if stats["total"] > 0 else 0

        notify_methods = (
            json.loads(site["notify_methods"]) if site["notify_methods"] else []
        )

        result.append(
            {
                "id": site["id"],
                "name": site["name"],
                "url": site["url"],
                "is_active": site["is_active"],
                "status": last_status["status"] if last_status else "unknown",
                "status_code": last_status["status_code"] if last_status else None,
                "response_time": last_status["response_time"] if last_status else None,
                "error_message": last_status["error_message"] if last_status else None,
                "last_checked": last_status["checked_at"] if last_status else None,
                "uptime": round(uptime, 2),
                "notify_methods": notify_methods,
            }
        )
    conn.close()
    return result


@app.post("/api/sites")
async def add_site(site: SiteCreate):
    conn = get_db_connection()
    c = conn.cursor()
    notify_methods = site.notify_methods or []
    notify_json = json.dumps(notify_methods)
    try:
        c.execute(
            "INSERT INTO sites (name, url, check_interval, is_active, notify_methods) VALUES (?, ?, ?, ?, ?)",
            (site.name, site.url, site.check_interval, site.is_active, notify_json),
        )
        site_id = c.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Site already exists")
    conn.close()
    if site_id is None:
        raise HTTPException(status_code=500, detail="Failed to create site")
    await check_site_status(site_id, site.url, notify_methods)
    return {"id": site_id, "message": "Site added"}


@app.put("/api/sites/{site_id}")
async def update_site(site_id: int, site_update: SiteUpdate):
    conn = get_db_connection()
    c = conn.cursor()

    # Список дозволених колонок для оновлення
    allowed_columns = {"name", "url", "notify_methods", "is_active"}

    updates = []
    params = []
    if site_update.name is not None:
        updates.append("name = ?")
        params.append(site_update.name)
    if site_update.url is not None:
        updates.append("url = ?")
        params.append(site_update.url)
    if site_update.notify_methods is not None:
        updates.append("notify_methods = ?")
        params.append(json.dumps(site_update.notify_methods))
    if site_update.is_active is not None:
        updates.append("is_active = ?")
        params.append(site_update.is_active)

    if updates:
        # Перевіряємо що всі колонки дозволені (захист від SQL Injection)
        for update in updates:
            col_name = update.split("=")[0].strip()
            if col_name not in allowed_columns:
                conn.close()
                raise HTTPException(
                    status_code=400, detail=f"Invalid column: {col_name}"
                )

        params.append(site_id)
        c.execute(f"UPDATE sites SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()
    return {"message": "Site updated"}


@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM status_history WHERE site_id = ?", (site_id,))
    c.execute("DELETE FROM ssl_certificates WHERE site_id = ?", (site_id,))
    c.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()
    return {"message": "Site deleted"}


@app.post("/api/sites/{site_id}/check")
async def check_site_endpoint(site_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT url, notify_methods FROM sites WHERE id = ?", (site_id,))
    site = c.fetchone()
    conn.close()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    notify_methods = (
        json.loads(site["notify_methods"]) if site["notify_methods"] else []
    )
    await check_site_status(site_id, site["url"], notify_methods)
    return {"message": "Check completed"}


@app.post("/api/notify-settings")
async def save_notify_settings(settings: NotifySettings):
    global NOTIFY_SETTINGS
    if settings.telegram:
        NOTIFY_SETTINGS["telegram"] = settings.telegram
    if settings.teams:
        NOTIFY_SETTINGS["teams"] = settings.teams
    if settings.discord:
        NOTIFY_SETTINGS["discord"] = settings.discord
    if settings.slack:
        NOTIFY_SETTINGS["slack"] = settings.slack
    if settings.email:
        NOTIFY_SETTINGS["email"] = settings.email
    if settings.sms:
        NOTIFY_SETTINGS["sms"] = settings.sms

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO notify_config (id, config) VALUES (1, ?)",
        (json.dumps(NOTIFY_SETTINGS),),
    )
    conn.commit()
    conn.close()
    return {"message": "Settings saved"}


# Windows Service Class
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
        import threading
        import time

        def run_async_server():
            """Run the async server in a separate thread"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Start background monitoring
                asyncio.ensure_future(monitor_loop())

                # Configure and start uvicorn
                config = uvicorn.Config(
                    app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info"
                )
                server = uvicorn.Server(config)

                loop.run_until_complete(server.serve())
            except Exception as e:
                servicemanager.LogErrorMsg(f"Server error: {str(e)}")

        try:
            # Report that service is starting (give 30 seconds to start)
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING, waitHint=30000)

            # Start server in background thread
            server_thread = threading.Thread(target=run_async_server)
            server_thread.daemon = True
            server_thread.start()

            # Give the server time to start
            time.sleep(3)

            # Report that service is running
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)

            # Wait for stop event (check every second)
            while True:
                rc = win32event.WaitForSingleObject(self.stop_event, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    break

        except Exception as e:
            servicemanager.LogErrorMsg(f"UptimeMonitor error: {str(e)}")
            import traceback

            servicemanager.LogErrorMsg(traceback.format_exc())


def install_service():
    """Install the service"""
    try:
        # Install service - pass the executable path and service class name as string
        # When running as compiled EXE, we need to handle this differently
        exe_path = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]

        # For pyinstaller EXE, use the HandleCommandLine method
        # which properly registers the service
        win32serviceutil.HandleCommandLine(
            UptimeMonitorService, argv=[exe_path, "install"]
        )

        # Set service to auto-start
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SYSTEM\CurrentControlSet\Services\{UptimeMonitorService._svc_name_}",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 2)  # 2 = Auto
            winreg.CloseKey(key)
        except:
            pass

        print(
            f"✅ Service '{UptimeMonitorService._svc_display_name_}' installed successfully!"
        )
        print(f"   Name: {UptimeMonitorService._svc_name_}")
        print(f"   Auto-start: Enabled")
        print(
            f"\nTo start the service, run: net start {UptimeMonitorService._svc_name_}"
        )
        return True
    except Exception as e:
        print(f"❌ Error installing service: {e}")
        import traceback

        traceback.print_exc()
        return False


def remove_service():
    """Remove the service"""
    try:
        exe_path = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
        win32serviceutil.HandleCommandLine(
            UptimeMonitorService, argv=[exe_path, "remove"]
        )
        print(
            f"✅ Service '{UptimeMonitorService._svc_display_name_}' removed successfully!"
        )
        return True
    except Exception as e:
        print(f"❌ Error removing service: {e}")
        return False


def start_service():
    """Start the service"""
    try:
        win32serviceutil.StartService(UptimeMonitorService._svc_name_)
        print(f"✅ Service '{UptimeMonitorService._svc_display_name_}' started!")
        print(f"   Access: http://localhost:{DEFAULT_PORT}")
        return True
    except Exception as e:
        print(f"❌ Error starting service: {e}")
        return False


def stop_service():
    """Stop the service"""
    try:
        win32serviceutil.StopService(UptimeMonitorService._svc_name_)
        print(f"✅ Service '{UptimeMonitorService._svc_display_name_}' stopped!")
        return True
    except Exception as e:
        print(f"❌ Error stopping service: {e}")
        return False


def run_console():
    """Run in console mode (not as service)"""
    print("=" * 50)
    print("Uptime Monitor - Console Mode")
    print("=" * 50)
    print(f"Starting server on port {DEFAULT_PORT}...")
    print(f"Access: http://localhost:{DEFAULT_PORT}")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    async def main():
        # Start background monitoring
        asyncio.create_task(monitor_loop())

        config = uvicorn.Config(
            app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - run as console application
        run_console()
    else:
        # Handle service commands
        cmd = sys.argv[1].lower()
        if cmd == "install":
            install_service()
        elif cmd == "remove":
            remove_service()
        elif cmd == "start":
            start_service()
        elif cmd == "stop":
            stop_service()
        elif cmd == "restart":
            stop_service()
            start_service()
        elif cmd == "console":
            run_console()
        else:
            # Let pywin32 handle service commands
            win32serviceutil.HandleCommandLine(UptimeMonitorService)
