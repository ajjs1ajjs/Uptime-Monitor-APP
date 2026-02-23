import sys
import os
import json
import socket
import ssl as ssl_module
from datetime import datetime

# Windows-specific imports (only on Windows)
IS_WINDOWS = sys.platform == 'win32'
if IS_WINDOWS:
    import win32service
    import win32serviceutil
    import win32con
    import win32event
    import servicemanager

# Get the application directory (works for both script and compiled EXE)
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    APP_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration paths
CONFIG_PATH = os.environ.get('CONFIG_PATH', '/etc/uptime-monitor/config.json')
if not os.path.exists(CONFIG_PATH) and IS_WINDOWS:
    CONFIG_PATH = os.path.join(os.environ.get('USERPROFILE', APP_DIR), 'UptimeMonitor', 'config.json')

# Default configuration
DEFAULT_CONFIG = {
    "server": {
        "port": 8080,
        "host": "0.0.0.0",
        "domain": "auto"
    },
    "ssl": {
        "enabled": False,
        "type": "custom",
        "cert_path": "/etc/uptime-monitor/ssl/cert.pem",
        "key_path": "/etc/uptime-monitor/ssl/key.pem",
        "redirect_http": True,
        "hsts": True,
        "hsts_max_age": 31536000
    },
    "data_dir": "/var/lib/uptime-monitor" if not IS_WINDOWS else os.path.join(os.environ.get('USERPROFILE', ''), 'UptimeMonitor', 'data'),
    "log_dir": "/var/log/uptime-monitor" if not IS_WINDOWS else os.path.join(os.environ.get('USERPROFILE', ''), 'UptimeMonitor', 'logs'),
    "check_interval": 60,
    "notifications": {
        "email_enabled": False,
        "email_smtp_server": "",
        "email_smtp_port": 587,
        "email_username": "",
        "email_password": "",
        "email_to": ""
    },
    "backup": {
        "enabled": True,
        "max_backups": 10,
        "backup_dir": "/etc/uptime-monitor/config.backups" if not IS_WINDOWS else os.path.join(os.environ.get('USERPROFILE', ''), 'UptimeMonitor', 'config.backups')
    }
}

def get_server_ip():
    """Get the server IP address"""
    try:
        # Get all network interfaces
        hostname = socket.gethostname()
        # Get IP from hostname
        ip = socket.gethostbyname(hostname)
        # If it's localhost, try to get external IP
        if ip.startswith('127.'):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
            except:
                pass
            finally:
                s.close()
        return ip
    except:
        return '0.0.0.0'

def load_config():
    """Load configuration from file or create default"""
    global CONFIG
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                CONFIG = json.load(f)
            # Merge with defaults to ensure all keys exist
            for key, value in DEFAULT_CONFIG.items():
                if key not in CONFIG:
                    CONFIG[key] = value
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_key not in CONFIG[key]:
                            CONFIG[key][sub_key] = sub_value
        except Exception as e:
            print(f"Error loading config: {e}")
            CONFIG = DEFAULT_CONFIG.copy()
    else:
        CONFIG = DEFAULT_CONFIG.copy()
        # Create default config file
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(CONFIG, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    # Handle auto domain
    if CONFIG['server'].get('domain') == 'auto':
        CONFIG['server']['domain'] = get_server_ip()
    
    return CONFIG

def log_config_change(old_config, new_config, user='system'):
    """Log configuration changes"""
    try:
        log_dir = CONFIG.get('log_dir', '/var/log/uptime-monitor')
        log_file = os.path.join(log_dir, 'config-changes.log')
        os.makedirs(log_dir, exist_ok=True)
        
        change_entry = {
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'action': 'config_changed',
            'changes': {
                'old': old_config,
                'new': new_config
            }
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(change_entry, ensure_ascii=False) + '\n')
    except:
        pass

def backup_config():
    """Create backup of current configuration"""
    try:
        backup_dir = CONFIG.get('backup', {}).get('backup_dir', '/etc/uptime-monitor/config.backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_file = os.path.join(backup_dir, f'config.{timestamp}.json')
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(CONFIG, f, indent=4, ensure_ascii=False)
        
        # Create symlinks
        latest_link = os.path.join(backup_dir, 'config.latest.json')
        prev_link = os.path.join(backup_dir, 'config.previous.json')
        
        if os.path.exists(latest_link):
            if os.path.exists(prev_link):
                os.remove(prev_link)
            os.rename(latest_link, prev_link)
        
        if os.path.exists(latest_link):
            os.remove(latest_link)
        os.symlink(backup_file, latest_link)
        
        # Clean old backups
        max_backups = CONFIG.get('backup', {}).get('max_backups', 10)
        backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('config.') and f.endswith('.json') and not f.endswith('.latest.json')])
        if len(backups) > max_backups:
            for old_backup in backups[:-max_backups]:
                os.remove(os.path.join(backup_dir, old_backup))
                
    except:
        pass

def setup_ssl():
    """Setup SSL context"""
    if not CONFIG.get('ssl', {}).get('enabled', False):
        return None
    
    try:
        cert_path = CONFIG['ssl'].get('cert_path', '')
        key_path = CONFIG['ssl'].get('key_path', '')
        
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            print(f"SSL certificates not found: {cert_path}, {key_path}")
            return None
        
        ssl_context = ssl_module.create_default_context(ssl_module.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cert_path, key_path)
        return ssl_context
    except Exception as e:
        print(f"SSL setup error: {e}")
        return None

# Load configuration
CONFIG = load_config()
port = CONFIG['server'].get('port', 8080)
host = CONFIG['server'].get('host', '0.0.0.0')
domain = CONFIG['server'].get('domain', get_server_ip())

# Allow command line override
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except:
        pass

import asyncio
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText

# Імпортуємо SSL чекер
from ssl_checker import check_ssl_certificate, should_notify_certificate, format_certificate_alert

# Імпортуємо модуль авторизації
import auth_module

app = FastAPI(title="Uptime Monitor")

# Middleware for HTTPS redirect and HSTS
@app.middleware("http")
async def https_redirect_middleware(request: Request, call_next):
    """Redirect HTTP to HTTPS if SSL is enabled"""
    response = await call_next(request)
    
    # Add HSTS header if enabled
    if CONFIG.get('ssl', {}).get('enabled', False) and CONFIG.get('ssl', {}).get('hsts', True):
        max_age = CONFIG['ssl'].get('hsts_max_age', 31536000)
        response.headers['Strict-Transport-Security'] = f'max-age={max_age}; includeSubDomains'
    
    return response

DB_PATH = os.path.join(APP_DIR, "sites.db")

# Ініціалізація авторизації
auth_module.init_auth_tables(DB_PATH)
CHECK_INTERVAL = 60

NOTIFY_SETTINGS = {
    "telegram": {"enabled": False, "token": "", "chat_id": ""},
    "teams": {"enabled": False, "webhook_url": ""},
    "discord": {"enabled": False, "webhook_url": ""},
    "slack": {"enabled": False, "webhook_url": ""},
    "email": {"enabled": False, "smtp_server": "", "smtp_port": 587, "username": "", "password": "", "to_email": ""},
    "sms": {"enabled": False, "account_sid": "", "auth_token": "", "from_number": "", "to_number": ""},
}

DISPLAY_ADDRESS = ""
LAST_STATUS = {}

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

def init_db():
    # Ensure database directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        check_interval INTEGER DEFAULT 60,
        is_active BOOLEAN DEFAULT 1,
        last_notification TEXT,
        notify_methods TEXT DEFAULT '[]'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        status TEXT,
        status_code INTEGER,
        response_time REAL,
        error_message TEXT,
        checked_at TEXT,
        FOREIGN KEY (site_id) REFERENCES sites(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS notify_config (
        id INTEGER PRIMARY KEY,
        config TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS app_settings (
        id INTEGER PRIMARY KEY,
        display_address TEXT DEFAULT ''
    )''')
    # Таблиця для SSL сертифікатів
    c.execute('''CREATE TABLE IF NOT EXISTS ssl_certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER UNIQUE,
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
    )''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_notify_settings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT config FROM notify_config WHERE id = 1")
    row = c.fetchone()
    if row:
        global NOTIFY_SETTINGS
        NOTIFY_SETTINGS = json.loads(row['config'])
    
    c.execute("SELECT display_address FROM app_settings WHERE id = 1")
    row = c.fetchone()
    if row:
        global DISPLAY_ADDRESS
        DISPLAY_ADDRESS = row['display_address'] or ""
    conn.close()

def save_notify_settings_to_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO notify_config (id, config) VALUES (1, ?)", (json.dumps(NOTIFY_SETTINGS),))
    conn.commit()
    conn.close()

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
            await session.post(url, json={"chat_id": settings['chat_id'], "text": message, "parse_mode": "HTML"})
    except Exception as e:
        print(f"Telegram error: {e}")

async def send_teams(message: str):
    settings = NOTIFY_SETTINGS["teams"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings['webhook_url'], json=payload)
    except Exception as e:
        print(f"Teams error: {e}")

async def send_discord(message: str):
    settings = NOTIFY_SETTINGS["discord"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"content": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings['webhook_url'], json=payload)
    except Exception as e:
        print(f"Discord error: {e}")

async def send_slack(message: str):
    settings = NOTIFY_SETTINGS["slack"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings['webhook_url'], json=payload)
    except Exception as e:
        print(f"Slack error: {e}")

async def send_email(message: str):
    settings = NOTIFY_SETTINGS["email"]
    if not all([settings.get("smtp_server"), settings.get("username"), settings.get("password"), settings.get("to_email")]):
        return
    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "Uptime Alert"
        msg["From"] = settings["username"]
        msg["To"] = settings["to_email"]
        
        with smtplib.SMTP(settings["smtp_server"], settings.get("smtp_port", 587)) as server:
            server.starttls()
            server.login(settings["username"], settings["password"])
            server.send_message(msg)
    except Exception as e:
        print(f"Email error: {e}")

async def send_sms(message: str):
    settings = NOTIFY_SETTINGS["sms"]
    if not all([settings.get("account_sid"), settings.get("auth_token"), settings.get("from_number"), settings.get("to_number")]):
        return
    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings['account_sid']}/Messages.json"
        auth = aiohttp.BasicAuth(settings["account_sid"], settings["auth_token"])
        payload = {
            "From": settings["from_number"],
            "To": settings["to_number"],
            "Body": message[:1600]
        }
        async with aiohttp.ClientSession() as session:
            await session.post(url, data=payload, auth=auth)
    except Exception as e:
        print(f"SMS error: {e}")

# Track last notification time for DOWN sites (for 1-minute repeat alerts)
LAST_DOWN_ALERT = {}  # site_id -> datetime of last alert

async def check_site_status(site_id: int, url: str, notify_methods: List[str]):
    global LAST_STATUS, LAST_DOWN_ALERT
    start_time = datetime.now()
    status = "down"
    status_code = None
    response_time = None
    error_message = None
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers=headers, ssl=False, allow_redirects=True) as response:
                status_code = response.status
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                status = "up" if status_code < 500 else "down"
    except aiohttp.ClientConnectorError:
        error_message = "Connection failed"
    except asyncio.TimeoutError:
        error_message = "Timeout"
    except Exception as e:
        error_message = str(e)[:100]
    
    checked_at = datetime.now()
    checked_at_iso = checked_at.isoformat()
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sites WHERE id = ?", (site_id,))
    site = c.fetchone()
    
    c.execute("""INSERT INTO status_history (site_id, status, status_code, response_time, error_message, checked_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (site_id, status, status_code, round(response_time, 2) if response_time else None, error_message, checked_at_iso))
    conn.commit()
    
    prev_status = LAST_STATUS.get(site_id)
    
    # Production alerting: immediate notifications, no delays
    if status == "down" and site and notify_methods:
        should_alert = False
        alert_type = ""
        
        if prev_status == "up" or prev_status is None:
            # Site just went down - immediate alert
            should_alert = True
            alert_type = "NEW"
        else:
            # Site is still down - check if 1 minute passed since last alert
            last_alert = LAST_DOWN_ALERT.get(site_id)
            if last_alert is None or (checked_at - last_alert).total_seconds() >= 1800:
                should_alert = True
                alert_type = "REPEAT"
        
        if should_alert:
            if alert_type == "NEW":
                msg = f"🔴 {site['name']}\n🌐 {url}\nStatus: {status_code or 'N/A'}\nError: {error_message or 'None'}\nTime: {checked_at_iso}"
            else:
                msg = f"🔴 {site['name']} - STILL DOWN\n🌐 {url}\nStatus: {status_code or 'N/A'}\nError: {error_message or 'None'}\nTime: {checked_at_iso}\n⏱️ Still down after 1 minute"
            
            await send_notification(msg, notify_methods)
            LAST_DOWN_ALERT[site_id] = checked_at
    
    # Site is back up - immediate recovery alert
    if status == "up" and prev_status == "down" and site and notify_methods:
        msg = f"🟢 {site['name']} - RECOVERED\n🌐 {url}\nStatus: {status_code}\nResponse Time: {round(response_time, 2) if response_time else 0}ms\nTime: {checked_at_iso}"
        await send_notification(msg, notify_methods)
        # Clear last down alert time
        if site_id in LAST_DOWN_ALERT:
            del LAST_DOWN_ALERT[site_id]
    
    LAST_STATUS[site_id] = status
    
    conn.close()
    return status, status_code, response_time, error_message

async def check_site_certificate(site_id: int, url: str, notify_methods: List[str]):
    """Перевіряє SSL сертифікат сайту та зберігає результати"""
    # Перевіряємо тільки HTTPS сайти
    if not url.startswith('https://'):
        return
    
    cert_info = await check_ssl_certificate(url)
    
    if not cert_info:
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Отримуємо назву сайту
    c.execute("SELECT name FROM sites WHERE id = ?", (site_id,))
    site = c.fetchone()
    site_name = site['name'] if site else url
    
    # Зберігаємо або оновлюємо інформацію про сертифікат
    c.execute("""
        INSERT OR REPLACE INTO ssl_certificates 
        (site_id, hostname, issuer, subject, start_date, expire_date, days_until_expire, is_valid, last_checked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        site_id,
        cert_info['hostname'],
        cert_info['issuer'],
        cert_info['subject'],
        cert_info['start_date'],
        cert_info['expire_date'],
        cert_info['days_until_expire'],
        cert_info['is_valid'],
        cert_info['checked_at']
    ))
    conn.commit()
    
    # Перевіряємо чи треба сповіщати
    days = cert_info['days_until_expire']
    
    # Сповіщати за 14 днів до закінчення і кожен день після
    if days <= 14:
        # Перевіряємо коли останній раз сповіщали
        c.execute("SELECT last_notified FROM ssl_certificates WHERE site_id = ?", (site_id,))
        row = c.fetchone()
        
        should_notify = True
        if row and row['last_notified']:
            last_notif = datetime.fromisoformat(row['last_notified'])
            # Сповіщати раз на день
            if (datetime.now() - last_notif).total_seconds() < 86400:  # 24 години
                should_notify = False
        
        if should_notify and notify_methods:
            msg = format_certificate_alert(cert_info, site_name, url)
            await send_notification(msg, notify_methods)
            
            # Оновлюємо час останнього сповіщення
            c.execute("UPDATE ssl_certificates SET last_notified = ? WHERE site_id = ?", 
                     (datetime.now().isoformat(), site_id))
            conn.commit()
    
    conn.close()

async def check_all_certificates():
    """Перевіряє SSL сертифікати всіх активних сайтів"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, url, notify_methods FROM sites WHERE is_active = 1 AND url LIKE 'https://%'")
    sites = c.fetchall()
    conn.close()
    
    for site in sites:
        notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
        await check_site_certificate(site['id'], site['url'], notify_methods)
        await asyncio.sleep(1)  # Пауза між перевірками

load_notify_settings()

def get_local_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

async def get_ssl_certificates_data():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT sc.*, s.name as site_name, s.url as site_url 
        FROM ssl_certificates sc
        JOIN sites s ON sc.site_id = s.id
        ORDER BY sc.days_until_expire ASC
    """)
    certs = c.fetchall()
    conn.close()
    
    return certs

@app.get("/status", response_class=HTMLResponse)
async def public_status_page(request: Request):
    """Публічна сторінка статусу"""
    from datetime import datetime as dt
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, url FROM sites ORDER BY id")
    sites = c.fetchall()
    
    c.execute("SELECT site_id, status FROM status_history WHERE checked_at > datetime('now', '-24 hours') ORDER BY checked_at DESC")
    history = c.fetchall()
    
    site_status = {}
    for h in history:
        if h['site_id'] not in site_status:
            site_status[h['site_id']] = h['status']
    
    conn.close()
    
    up_count = sum(1 for s in site_status.values() if s == 'up')
    down_count = sum(1 for s in site_status.values() if s == 'down')
    total = len(sites)
    
    monitors_html = ''
    for site in sites:
        status = site_status.get(site['id'], 'unknown')
        status_class = 'up' if status == 'up' else 'down'
        status_text = '✓ Онлайн' if status == 'up' else '✗ Офлайн'
        monitors_html += f'''
        <div class="monitor {status_class}">
            <div><div class="monitor-name">{site['name']}</div>
            <div class="monitor-url">{site['url']}</div></div>
            <span class="status-badge {status_class}">{status_text}</span>
        </div>'''
    
    status_html = f'''<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Status - Uptime Monitor</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', sans-serif; background: #0f0f23; color: #fff; min-height: 100vh; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e, #0f0f23); padding: 40px; text-align: center; border-bottom: 1px solid #2a2a4a; }}
        .logo {{ font-size: 32px; font-weight: 700; margin-bottom: 20px; }}
        .logo-icon {{ display: inline-block; width: 50px; height: 50px; background: linear-gradient(135deg, #00d9ff, #00ff88); border-radius: 12px; line-height: 50px; font-size: 24px; margin-right: 10px; }}
        .overall-status {{ font-size: 48px; font-weight: 700; margin: 30px 0; }}
        .overall-status.up {{ color: #00ff88; }}
        .overall-status.down {{ color: #ff4757; }}
        .stats {{ display: flex; justify-content: center; gap: 40px; margin: 20px 0; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 36px; font-weight: 700; }}
        .stat-label {{ color: #a0a0b0; font-size: 14px; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 40px; }}
        .monitor {{ background: linear-gradient(145deg, #1a1a2e, #16213e); padding: 20px; margin-bottom: 15px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #2a2a4a; }}
        .monitor.up {{ border-left: 4px solid #00ff88; }}
        .monitor.down {{ border-left: 4px solid #ff4757; }}
        .monitor-name {{ font-size: 18px; font-weight: 600; }}
        .monitor-url {{ color: #a0a0b0; font-size: 13px; margin-top: 5px; }}
        .status-badge {{ padding: 8px 20px; border-radius: 20px; font-weight: 600; font-size: 14px; }}
        .status-badge.up {{ background: rgba(0,255,136,0.15); color: #00ff88; }}
        .status-badge.down {{ background: rgba(255,71,87,0.15); color: #ff4757; }}
        .footer {{ text-align: center; padding: 40px; color: #a0a0b0; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo"><span class="logo-icon">⚡</span>Uptime Monitor</div>
        <div class="overall-status {'up' if down_count == 0 else 'down'}">
            {'✅ Всі системи працюють' if down_count == 0 else '⚠️ Деякі проблеми'}
        </div>
        <div class="stats">
            <div class="stat"><div class="stat-value" style="color: #00d9ff;">{total}</div><div class="stat-label">Моніторів</div></div>
            <div class="stat"><div class="stat-value" style="color: #00ff88;">{up_count}</div><div class="stat-label">Онлайн</div></div>
            <div class="stat"><div class="stat-value" style="color: #ff4757;">{down_count}</div><div class="stat-label">Офлайн</div></div>
        </div>
    </div>
    <div class="container">{monitors_html}
    </div>
    <div class="footer"><p>Оновлено: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div>
</body>
</html>'''
    
    return HTMLResponse(content=status_html)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Перевірка авторизації
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    
    if not user:
        return RedirectResponse(url='/login', status_code=302)
    
    # Перевірка чи потрібно змінити пароль
    if user.get('must_change_password'):
        return RedirectResponse(url='/change-password', status_code=302)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sites ORDER BY id")
    sites = c.fetchall()
    
    site_data = []
    for site in sites:
        c.execute("SELECT * FROM status_history WHERE site_id = ? ORDER BY checked_at DESC LIMIT 1", (site['id'],))
        last_status = c.fetchone()
        
        c.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as up_count FROM status_history WHERE site_id = ?", (site['id'],))
        stats = c.fetchone()
        uptime = (stats['up_count'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
        
        site_data.append({
            'id': site['id'],
            'name': site['name'],
            'url': site['url'],
            'is_active': site['is_active'],
            'status': last_status['status'] if last_status else 'unknown',
            'status_code': last_status['status_code'] if last_status else None,
            'response_time': last_status['response_time'] if last_status else None,
            'error_message': last_status['error_message'] if last_status else None,
            'last_checked': last_status['checked_at'] if last_status else None,
            'uptime': round(uptime, 2),
            'notify_methods': notify_methods
        })
    conn.close()
    
    total_sites = len(site_data)
    up_sites = sum(1 for s in site_data if s['status'] == 'up')
    down_sites = sum(1 for s in site_data if s['status'] == 'down')
    
    notify_config_json = json.dumps(NOTIFY_SETTINGS)
    display_address = DISPLAY_ADDRESS if DISPLAY_ADDRESS else f"http://{LOCAL_IP}:{port}"
    
    certs_data = await get_ssl_certificates_data()
    
    html = f'''<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uptime Monitor - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            --bg-gradient: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg-gradient); color: var(--text-primary); min-height: 100vh; }}
        
        .header {{ background: linear-gradient(180deg, rgba(26,26,46,0.95) 0%, rgba(15,15,35,0.95) 100%); padding: 20px 40px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; backdrop-filter: blur(10px); }}
        .logo {{ font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 12px; }}
        .logo-icon {{ width: 44px; height: 44px; background: linear-gradient(135deg, var(--accent), #00ff88); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 4px 20px rgba(0,217,255,0.4), 0 0 30px rgba(0,255,136,0.2); }}
        
        .hero-stats {{ display: flex; gap: 30px; margin: 40px; background: linear-gradient(145deg, rgba(30,42,74,0.6), rgba(22,33,62,0.8)); padding: 30px 40px; border-radius: 24px; border: 1px solid rgba(0,217,255,0.1); box-shadow: 0 20px 60px rgba(0,0,0,0.4); }}
        .hero-stat {{ text-align: center; flex: 1; position: relative; }}
        .hero-stat:not(:last-child)::after {{ content: ''; position: absolute; right: 0; top: 50%; transform: translateY(-50%); height: 60%; width: 1px; background: linear-gradient(180deg, transparent, var(--border), transparent); }}
        .hero-stat-value {{ font-size: 48px; font-weight: 700; background: linear-gradient(135deg, var(--accent), #00ff88); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .hero-stat-label {{ color: var(--text-secondary); font-size: 14px; margin-top: 8px; text-transform: uppercase; letter-spacing: 1px; }}
        
        .monitoring-types {{ display: flex; gap: 15px; margin: 0 40px 30px; flex-wrap: wrap; }}
        .monitor-type-btn {{ padding: 12px 24px; background: linear-gradient(145deg, rgba(26,26,46,0.8), rgba(22,33,62,0.9)); border: 1px solid var(--border); border-radius: 12px; cursor: pointer; font-weight: 600; color: var(--text-secondary); transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; }}
        .monitor-type-btn:hover {{ border-color: var(--accent); color: var(--text-primary); transform: translateY(-2px); }}
        .monitor-type-btn.active {{ background: linear-gradient(135deg, var(--accent), var(--accent-hover)); color: #000; border-color: var(--accent); box-shadow: 0 4px 20px rgba(0,217,255,0.3); }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 0 40px 40px; }}
        
        .panel {{ background: linear-gradient(145deg, rgba(30,42,74,0.5), rgba(22,33,62,0.7)); padding: 25px; border-radius: 20px; margin-bottom: 30px; border: 1px solid var(--border); box-shadow: 0 10px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05); backdrop-filter: blur(10px); }}
        .panel:hover {{ transform: translateY(-2px); box-shadow: 0 20px 60px rgba(0,0,0,0.4); }}
        .panel-title {{ font-size: 18px; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
        
        .chart-container {{ position: relative; height: 300px; margin: 20px 0; }}
        
        .monitor-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }}
        .monitor-card {{ background: linear-gradient(145deg, rgba(30,42,74,0.6), rgba(22,33,62,0.8)); padding: 24px; border-radius: 20px; border: 1px solid var(--border); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); box-shadow: 0 10px 40px rgba(0,0,0,0.3); position: relative; overflow: hidden; }}
        .monitor-card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--accent), #00ff88); opacity: 0; transition: opacity 0.3s; }}
        .monitor-card:hover {{ transform: translateY(-5px) scale(1.02); box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 30px rgba(0,217,255,0.1); }}
        .monitor-card:hover::before {{ opacity: 1; }}
        .monitor-card.up {{ border-left: 4px solid var(--success); }}
        .monitor-card.down {{ border-left: 4px solid var(--danger); }}
        .monitor-card.paused {{ border-left: 4px solid var(--warning); opacity: 0.7; }}
        
        .monitor-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
        .monitor-name {{ font-size: 18px; font-weight: 600; }}
        .monitor-url {{ color: var(--text-secondary); font-size: 13px; word-break: break-all; margin-top: 5px; }}
        .monitor-type-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; background: rgba(0,217,255,0.15); color: var(--accent); }}
        
        .monitor-stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; padding: 15px 0; border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
        .monitor-stat {{ text-align: center; }}
        .monitor-stat-value {{ font-size: 18px; font-weight: 700; }}
        .monitor-stat-label {{ font-size: 11px; color: var(--text-secondary); margin-top: 3px; }}
        
        .monitor-actions {{ display: flex; gap: 10px; }}
        .btn {{ flex: 1; padding: 10px; border: none; border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 13px; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
        .btn-check {{ background: linear-gradient(135deg, var(--accent), var(--accent-hover)); color: #000; box-shadow: 0 4px 15px rgba(0,217,255,0.3); }}
        .btn-check:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,217,255,0.5); }}
        .btn-edit {{ background: linear-gradient(135deg, rgba(255,217,61,0.2), rgba(255,217,61,0.1)); color: var(--warning); }}
        .btn-edit:hover {{ background: linear-gradient(135deg, var(--warning), #e6c200); color: #000; }}
        .btn-delete {{ background: linear-gradient(135deg, rgba(255,71,87,0.2), rgba(255,71,87,0.1)); color: var(--danger); }}
        .btn-delete:hover {{ background: linear-gradient(135deg, var(--danger), #cc3a47); color: #fff; }}
        
        .site-actions {{ display: flex; gap: 10px; }}
        .btn {{ flex: 1; padding: 10px; border: none; border-radius: 10px; cursor: pointer; font-weight: 500; font-size: 13px; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
        .btn-check {{ background: linear-gradient(135deg, var(--accent), var(--accent-hover)); color: #000; box-shadow: 0 4px 15px rgba(0,217,255,0.3); }}
        .btn-check:hover {{ background: linear-gradient(135deg, var(--accent-hover), var(--accent)); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,217,255,0.5); }}
        .btn-edit {{ background: linear-gradient(135deg, rgba(255,217,61,0.2), rgba(255,217,61,0.1)); color: var(--warning); box-shadow: 0 4px 15px rgba(255,217,61,0.2); }}
        .btn-edit:hover {{ background: linear-gradient(135deg, var(--warning), #e6c200); color: #000; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,217,61,0.5); }}
        .btn-delete {{ background: linear-gradient(135deg, rgba(255,71,87,0.2), rgba(255,71,87,0.1)); color: var(--danger); box-shadow: 0 4px 15px rgba(255,71,87,0.2); }}
        .btn-delete:hover {{ background: linear-gradient(135deg, var(--danger), #cc3a47); color: #fff; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,71,87,0.5); }}
        
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
        
        .tabs {{ display: flex; gap: 10px; margin: 0 40px; }}
        .tab-btn {{ padding: 12px 30px; background: linear-gradient(145deg, #1a1a2e, #0f0f23); border: 1px solid var(--border); border-radius: 12px; cursor: pointer; font-weight: 600; color: var(--text-secondary); transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); box-shadow: 0 4px 15px rgba(0,0,0,0.2); position: relative; overflow: hidden; }}
        .tab-btn::before {{ content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); transition: 0.5s; }}
        .tab-btn:hover::before {{ left: 100%; }}
        .tab-btn:hover {{ border-color: var(--accent); color: var(--text-primary); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,217,255,0.2); }}
        .tab-btn.active {{ background: linear-gradient(135deg, var(--accent), var(--accent-hover)); color: #000; border-color: var(--accent); box-shadow: 0 4px 20px rgba(0,217,255,0.4), inset 0 1px 0 rgba(255,255,255,0.2); transform: translateY(-2px); }}
        
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        .address-config {{ background: linear-gradient(145deg, #1a1a2e, #0f0f23); padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.2); }}
        .address-config input {{ flex: 1; padding: 10px; border-radius: 10px; border: 1px solid var(--border); background: linear-gradient(145deg, #0f0f23, #1a1a2e); color: var(--text-primary); font-size: 14px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.2); transition: all 0.3s ease; }}
        .address-config input:focus {{ outline: none; border-color: var(--accent); box-shadow: inset 0 2px 5px rgba(0,0,0,0.2), 0 0 15px rgba(0,217,255,0.3); }}
        
        .tab-content {{ display: none; animation: fadeSlideIn 0.4s ease; }}
        .tab-content.active {{ display: block; animation: fadeSlideIn 0.4s ease; }}
        
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 1000; align-items: center; justify-content: center; backdrop-filter: blur(5px); }}
        .modal.active {{ display: flex; animation: fadeIn 0.3s ease; }}
        .modal-content {{ background: linear-gradient(145deg, #1e2a4a, #16213e); padding: 30px; border-radius: 20px; max-width: 500px; width: 90%; border: 1px solid var(--border); box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 50px rgba(0,0,0,0.5); animation: scaleIn 0.3s ease; }}
        
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes fadeSlideIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes scaleIn {{ from {{ opacity: 0; transform: scale(0.9); }} to {{ opacity: 1; transform: scale(1); }} }}
        @keyframes slideDown {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo"><div class="logo-icon">⚡</div><span>Uptime Monitor</span></div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <div id="lastUpdate" style="color: var(--text-secondary); font-size: 14px;"></div>
            <a href="/status" target="_blank" style="padding: 8px 16px; background: rgba(0,217,255,0.2); color: var(--accent); text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: 500;">📄 Status Page</a>
            <a href="/logout" style="padding: 8px 16px; background: rgba(255,71,87,0.2); color: var(--danger); text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: 500;">🚪 Вийти</a>
        </div>
    </div>
    
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('dashboard')">📊 Dashboard</button>
        <button class="tab-btn" onclick="switchTab('monitors')">🖥️ Монітори</button>
        <button class="tab-btn" onclick="switchTab('incidents')">⚠️ Інциденти</button>
        <button class="tab-btn" onclick="switchTab('settings')">⚙️ Налаштування</button>
    </div>
    
    <div id="tab-dashboard" class="tab-content active">
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-value">{total_sites}</div>
                <div class="hero-stat-label">Моніторів</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value" style="background: linear-gradient(135deg, #00ff88, #00cc6a); -webkit-background-clip: text;">{up_sites}</div>
                <div class="hero-stat-label">Онлайн</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value" style="background: linear-gradient(135deg, #ff4757, #ff6b7a); -webkit-background-clip: text;">{down_sites}</div>
                <div class="hero-stat-label">Офлайн</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value" style="background: linear-gradient(135deg, #ffd93d, #ffb300); -webkit-background-clip: text;">0</div>
                <div class="hero-stat-label">Інцидентів</div>
            </div>
        </div>
        
        <div class="container">
            <div class="panel">
                <div class="panel-title">📈 Час відповіді (24 години)</div>
                <div class="chart-container">
                    <canvas id="responseTimeChart"></canvas>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">🎯 Швидкі дії</div>
                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                    <button class="btn btn-check" onclick="switchTab('monitors'); setTimeout(() => addMonitorModal.show(), 300)">➕ Додати монітор</button>
                    <button class="btn btn-check" style="background: linear-gradient(135deg, #00ff88, #00cc6a);" onclick="checkAllMonitors()">🔄 Перевірити всі</button>
                    <button class="btn btn-edit" onclick="switchTab('incidents')">📋 Історія інцидентів</button>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">📊 Статус всіх моніторів</div>
                <div class="monitor-grid" id="dashboardMonitors"></div>
            </div>
        </div>
    </div>
    
    <div id="tab-monitors" class="tab-content">
        <div class="monitoring-types">
            <button class="monitor-type-btn active" onclick="filterMonitors('all')">🌐 Всі</button>
            <button class="monitor-type-btn" onclick="filterMonitors('http')">🌐 HTTP(S)</button>
            <button class="monitor-type-btn" onclick="filterMonitors('port')">🔌 Порт</button>
            <button class="monitor-type-btn" onclick="filterMonitors('ping')">📡 Пінг</button>
            <button class="monitor-type-btn" onclick="filterMonitors('ssl')">🔒 SSL</button>
        </div>
        
        <div class="container">
            <div class="panel">
                <div class="panel-title" style="display:flex; justify-content:space-between; align-items:center;">
                    <span>🖥️ Мої монітори</span>
                    <button class="btn btn-check" onclick="document.getElementById('addMonitorModal').classList.add('active')">➕ Додати</button>
                </div>
                <div class="monitor-grid" id="monitorsGrid"></div>
            </div>
        </div>
    </div>
    
    <div id="tab-incidents" class="tab-content">
        <div class="container">
            <div class="panel">
                <div class="panel-title">⚠️ Історія інцидентів</div>
                <div id="incidentsList" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    Немає інцидентів - всі монітори працюють!
                </div>
            </div>
        </div>
    </div>
    
    <div id="tab-settings" class="tab-content">
        <div class="container">
        
        <div class="panel">
            <div class="panel-title">🔗 Налаштування адреси</div>
            <div class="address-config">
                <div class="form-row">
                    <input type="text" id="displayAddress" placeholder="Адреса для доступу (наприклад: http://192.168.1.100:8000)">
                    <button onclick="saveDisplayAddress()">💾 Зберегти</button>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-title">🔒 SSL Сертифікати</div>
            <div class="ssl-grid" id="sslGridSettings"></div>
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
        </div>
        
        <div id="tab-ssl" class="tab-content">
            <div class="panel">
                <div class="panel-title" style="display:flex; justify-content:space-between; align-items:center;">
                    <span>🔒 SSL Сертифікати</span>
                    <button class="btn btn-check" onclick="checkSSLCertificates()" style="padding:8px 20px;">🔄 Перевірити зараз</button>
                </div>
                <div class="ssl-grid" id="sslGrid"></div>
            </div>
        </div>
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
        const notifyConfig = {notify_config_json};
        let currentFilter = 'all';
        let responseChart = null;
        
        function switchTab(tabName) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.querySelector('.tab-btn[onclick="switchTab(\\'' + tabName + '\\')"]').classList.add('active');
            document.getElementById('tab-' + tabName).classList.add('active');
            
            if (tabName === 'dashboard') {{
                loadDashboard();
            }} else if (tabName === 'monitors') {{
                loadMonitors();
            }}
        }}
        
        function filterMonitors(type) {{
            currentFilter = type;
            document.querySelectorAll('.monitor-type-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            loadMonitors();
        }}
        
        async function loadDashboard() {{
            try {{
                const response = await fetch('/api/sites');
                sitesData = await response.json();
                renderDashboardMonitors();
                initResponseChart();
            }} catch(e) {{ console.error(e); }}
        }}
        
        function renderDashboardMonitors() {{
            const grid = document.getElementById('dashboardMonitors');
            if (!grid) return;
            
            const filtered = currentFilter === 'all' ? sitesData : sitesData.filter(s => s.monitor_type === currentFilter);
            
            if (filtered.length === 0) {{
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Немає моніторів. Додайте перший!</div>';
                return;
            }}
            
            let html = '';
            filtered.slice(0, 6).forEach(site => {{
                const statusClass = site.status === 'up' ? 'up' : (site.status === 'paused' ? 'paused' : 'down');
                const typeBadge = site.monitor_type === 'http' ? '🌐 HTTP' : site.monitor_type === 'port' ? '🔌 Порт' : site.monitor_type === 'ping' ? '📡 Пінг' : '🔒 SSL';
                const statusColor = site.status === 'up' ? 'var(--success)' : 'var(--danger)';
                const statusIcon = site.status === 'up' ? '✓' : '✗';
                const respTime = site.response_time || '—';
                const uptime = site.uptime || 100;
                const httpCode = site.status_code || '—';
                
                html += '<div class="monitor-card ' + statusClass + '">';
                html += '<div class="monitor-header"><div>';
                html += '<div class="monitor-name">' + site.name + '</div>';
                html += '<div class="monitor-url">' + site.url + '</div>';
                html += '</div><span class="monitor-type-badge">' + typeBadge + '</span></div>';
                html += '<div class="monitor-stats">';
                html += '<div class="monitor-stat"><div class="monitor-stat-value" style="color:' + statusColor + '">' + statusIcon + '</div><div class="monitor-stat-label">Статус</div></div>';
                html += '<div class="monitor-stat"><div class="monitor-stat-value">' + respTime + '</div><div class="monitor-stat-label">ms</div></div>';
                html += '<div class="monitor-stat"><div class="monitor-stat-value">' + uptime + '%</div><div class="monitor-stat-label">Uptime</div></div>';
                html += '<div class="monitor-stat"><div class="monitor-stat-value">' + httpCode + '</div><div class="monitor-stat-label">HTTP</div></div>';
                html += '</div></div>';
            }});
            grid.innerHTML = html;
        }}
        
        async function loadMonitors() {{
            try {{
                const response = await fetch('/api/sites');
                sitesData = await response.json();
                renderMonitors();
            }} catch(e) {{ console.error(e); }}
        }}
        
        function renderMonitors() {{
            const grid = document.getElementById('monitorsGrid');
            if (!grid) return;
            
            const filtered = currentFilter === 'all' ? sitesData : sitesData.filter(s => s.monitor_type === currentFilter);
            
            if (filtered.length === 0) {{
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Немає моніторів. Додайте перший!</div>';
                return;
            }}
            
            let html = '';
            filtered.forEach(site => {{
                const statusClass = site.status === 'up' ? 'up' : (site.status === 'paused' ? 'paused' : 'down');
                const statusText = site.status === 'up' ? '✓ Онлайн' : (site.status === 'paused' ? '⏸ Пауза' : '✗ Офлайн');
                const typeBadge = site.monitor_type === 'http' ? '🌐 HTTP' : site.monitor_type === 'port' ? '🔌 Порт' : site.monitor_type === 'ping' ? '📡 Пінг' : '🔒 SSL';
                const statusColor = site.status === 'up' ? 'var(--success)' : 'var(--danger)';
                const respTime = site.response_time || '—';
                const uptime = site.uptime || 100;
                const httpCode = site.status_code || '—';
                
                html += '<div class="monitor-card ' + statusClass + '">';
                html += '<div class="monitor-header"><div>';
                html += '<div class="monitor-name">' + site.name + '</div>';
                html += '<div class="monitor-url">' + site.url + '</div>';
                html += '</div><span class="monitor-type-badge">' + typeBadge + '</span></div>';
                html += '<div class="monitor-stats">';
                html += '<div class="monitor-stat"><div class="monitor-stat-value" style="color:' + statusColor + '">' + statusText + '</div><div class="monitor-stat-label">Статус</div></div>';
                html += '<div class="monitor-stat"><div class="monitor-stat-value">' + respTime + 'ms</div><div class="monitor-stat-label">Час</div></div>';
                html += '<div class="monitor-stat"><div class="monitor-stat-value">' + uptime + '%</div><div class="monitor-stat-label">Uptime</div></div>';
                html += '<div class="monitor-stat"><div class="monitor-stat-value">' + httpCode + '</div><div class="monitor-stat-label">HTTP</div></div>';
                html += '</div>';
                html += '<div class="monitor-actions">';
                html += '<button class="btn btn-check" onclick="checkSite(' + site.id + ')">🔄</button>';
                html += '<button class="btn btn-edit" onclick="openEditModal(' + site.id + ', \\'' + site.name + '\\', \\'' + site.url + '\\', \\'' + site.monitor_type + '\\')">✏️</button>';
                html += '<button class="btn btn-delete" onclick="deleteSite(' + site.id + ')">🗑️</button>';
                html += '</div></div>';
            }});
            grid.innerHTML = html;
        }}
        
        function initResponseChart() {{
            const ctx = document.getElementById('responseTimeChart');
            if (!ctx) return;
            
            if (responseChart) responseChart.destroy();
            
            const labels = [];
            const data = [];
            for (let i = 23; i >= 0; i--) {{
                labels.push(i + 'h');
                data.push(Math.floor(Math.random() * 200) + 50);
            }}
            
            responseChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Час відповіді (ms)',
                        data: data,
                        borderColor: '#00d9ff',
                        backgroundColor: 'rgba(0, 217, 255, 0.1)',
                        fill: true,
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            grid: {{ color: 'rgba(255,255,255,0.1)' }},
                            ticks: {{ color: '#a0a0b0' }}
                        }},
                        x: {{
                            grid: {{ color: 'rgba(255,255,255,0.05)' }},
                            ticks: {{ color: '#a0a0b0' }}
                        }}
                    }}
                }}
            }});
        }}
        
        async function checkAllMonitors() {{
            for (const site of sitesData) {{
                await checkSite(site.id);
            }}
            loadDashboard();
            alert('✅ Перевірку всіх моніторів запущено!');
        }}
        
        async function loadAppSettings() {{
            try {{
                const response = await fetch('/api/app-settings');
                const data = await response.json();
                document.getElementById('displayAddress').value = data.display_address || '';
            }} catch(e) {{ console.error(e); }}
        }}
        
        async function saveDisplayAddress() {{
            const address = document.getElementById('displayAddress').value.trim();
            await fetch('/api/app-settings', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{display_address: address}})
            }});
            alert('✅ Адресу збережено! Перезавантажте сторінку.');
        }}
        
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
                const safeName = site.name.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                const safeUrl = site.url.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                const notifyMethodsJson = JSON.stringify(site.notify_methods || []).replace(/"/g, '&quot;');
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
                        <button class="btn btn-edit" onclick="openEditModal(${{site.id}}, '${{safeName}}', '${{safeUrl}}', ${{notifyMethodsJson}})">✏️ Редагувати</button>
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
        
        let sslCertificatesData = [];
        
        async function loadSSLCertificates() {{
            try {{
                const response = await fetch('/api/ssl-certificates');
                sslCertificatesData = await response.json();
                renderSSLCertificates();
            }} catch(e) {{ console.error(e); }}
        }}
        
        async function checkSSLCertificates() {{
            try {{
                await fetch('/api/ssl-certificates/check', {{ method: 'POST' }});
                loadSSLCertificates();
                alert('✅ Перевірку SSL сертифікатів запущено!');
            }} catch(e) {{ console.error(e); }}
        }}
        
        function renderSSLCertificates() {{
            const grid = document.getElementById('sslGrid');
            const gridSettings = document.getElementById('sslGridSettings');
            
            const renderContent = () => {{
                if (sslCertificatesData.length === 0) {{
                    return '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Немає SSL сертифікатів для перегляду. Додайте HTTPS сайт!</div>';
                }}
                
                let html = '';
                sslCertificatesData.forEach(cert => {{
                    const days = cert.days_until_expire;
                    let statusColor, statusText, icon;
                    
                    if (days <= 0) {{
                        statusColor = 'var(--danger)';
                        statusText = 'ПРОСТРОЧЕНИЙ';
                        icon = '🔴';
                    }} else if (days <= 7) {{
                        statusColor = 'var(--warning)';
                        statusText = 'Закінчується через ' + days + ' днів';
                        icon = '🟠';
                    }} else {{
                        statusColor = 'var(--success)';
                        statusText = 'Дійсний';
                        icon = '🟢';
                    }}
                    
                    let hostnameHtml = cert.hostname ? '<div style="color: var(--text-secondary); font-size: 12px; margin-bottom: 10px;">🌐 ' + cert.hostname + '</div>' : '';
                    
                    let expireDateDisplay = '—';
                    if (cert.expire_date) {{
                        try {{
                            expireDateDisplay = new Date(cert.expire_date).toLocaleDateString('uk-UA');
                        }} catch(e) {{
                            expireDateDisplay = '—';
                        }}
                    }}
                    
                    html += '<div class="ssl-card" style="border-left: 3px solid ' + statusColor + '">';
                    html += '<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">';
                    html += '<div style="font-size:14px; font-weight:600;">' + cert.site_name + '</div>';
                    html += '<span style="padding:3px 8px; border-radius:10px; font-size:10px; font-weight:600; background: rgba(' + (statusColor === 'var(--success)' ? '0,255,136' : statusColor === 'var(--warning)' ? '255,217,61' : '255,71,87') + ',0.15); color: ' + statusColor + '">' + icon + ' ' + days + 'д</span>';
                    html += '</div>';
                    html += '<div style="color:var(--text-secondary); font-size:11px; margin-bottom:8px; word-break:break-all;">' + cert.site_url + '</div>';
                    html += '<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:11px;">';
                    html += '<div><span style="color:var(--text-secondary)">Видавець:</span> ' + (cert.issuer ? cert.issuer.split(',')[0] : '—') + '</div>';
                    html += '<div><span style="color:var(--text-secondary)">До:</span> ' + expireDateDisplay + '</div>';
                    html += '</div>';
                    html += '</div>';
                }});
                return html;
            }};
            
            if (grid) grid.innerHTML = renderContent();
            if (gridSettings) gridSettings.innerHTML = renderContent();
        }}
        
        initNotifyUI();
        loadAppSettings();
        loadSites();
        loadSSLCertificates();
        setInterval(loadSites, 30000);
        setInterval(loadSSLCertificates, 86400000);
    </script>
</body>
</html>'''
    return html

@app.get("/api/sites", response_model=List[dict])
async def get_sites():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sites ORDER BY id")
    sites = c.fetchall()
    
    result = []
    for site in sites:
        c.execute("SELECT * FROM status_history WHERE site_id = ? ORDER BY checked_at DESC LIMIT 1", (site['id'],))
        last_status = c.fetchone()
        
        c.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as up_count FROM status_history WHERE site_id = ?", (site['id'],))
        stats = c.fetchone()
        uptime = (stats['up_count'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
        
        result.append({
            'id': site['id'],
            'name': site['name'],
            'url': site['url'],
            'is_active': site['is_active'],
            'status': last_status['status'] if last_status else 'unknown',
            'status_code': last_status['status_code'] if last_status else None,
            'response_time': last_status['response_time'] if last_status else None,
            'error_message': last_status['error_message'] if last_status else None,
            'last_checked': last_status['checked_at'] if last_status else None,
            'uptime': round(uptime, 2),
            'notify_methods': notify_methods
        })
    conn.close()
    return result

@app.get("/test123")
async def test123():
    return {"test": "123"}

@app.get("/public-status")
async def public_status_page(request: Request):
    """Публічна сторінка статусу - без авторизації"""
    from datetime import datetime as dt
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, url FROM sites ORDER BY id")
    sites = c.fetchall()
    
    c.execute("SELECT site_id, status FROM status_history WHERE checked_at > datetime('now', '-24 hours') ORDER BY checked_at DESC")
    history = c.fetchall()
    
    site_status = {}
    for h in history:
        if h['site_id'] not in site_status:
            site_status[h['site_id']] = h['status']
    
    conn.close()
    
    up_count = sum(1 for s in site_status.values() if s == 'up')
    down_count = sum(1 for s in site_status.values() if s == 'down')
    total = len(sites)
    
    monitors_html = ''
    for site in sites:
        status = site_status.get(site['id'], 'unknown')
        status_class = 'up' if status == 'up' else 'down'
        status_text = '✓ Онлайн' if status == 'up' else '✗ Офлайн'
        monitors_html += f'''
        <div class="monitor {status_class}">
            <div><div class="monitor-name">{site['name']}</div>
            <div class="monitor-url">{site['url']}</div></div>
            <span class="status-badge {status_class}">{status_text}</span>
        </div>'''
    
    status_html = f'''<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Status - Uptime Monitor</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', sans-serif; background: #0f0f23; color: #fff; min-height: 100vh; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e, #0f0f23); padding: 40px; text-align: center; border-bottom: 1px solid #2a2a4a; }}
        .logo {{ font-size: 32px; font-weight: 700; margin-bottom: 20px; }}
        .logo-icon {{ display: inline-block; width: 50px; height: 50px; background: linear-gradient(135deg, #00d9ff, #00ff88); border-radius: 12px; line-height: 50px; font-size: 24px; margin-right: 10px; }}
        .overall-status {{ font-size: 48px; font-weight: 700; margin: 30px 0; }}
        .overall-status.up {{ color: #00ff88; }}
        .overall-status.down {{ color: #ff4757; }}
        .stats {{ display: flex; justify-content: center; gap: 40px; margin: 20px 0; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 36px; font-weight: 700; }}
        .stat-label {{ color: #a0a0b0; font-size: 14px; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 40px; }}
        .monitor {{ background: linear-gradient(145deg, #1a1a2e, #16213e); padding: 20px; margin-bottom: 15px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #2a2a4a; }}
        .monitor.up {{ border-left: 4px solid #00ff88; }}
        .monitor.down {{ border-left: 4px solid #ff4757; }}
        .monitor-name {{ font-size: 18px; font-weight: 600; }}
        .monitor-url {{ color: #a0a0b0; font-size: 13px; margin-top: 5px; }}
        .status-badge {{ padding: 8px 20px; border-radius: 20px; font-weight: 600; font-size: 14px; }}
        .status-badge.up {{ background: rgba(0,255,136,0.15); color: #00ff88; }}
        .status-badge.down {{ background: rgba(255,71,87,0.15); color: #ff4757; }}
        .footer {{ text-align: center; padding: 40px; color: #a0a0b0; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo"><span class="logo-icon">⚡</span>Uptime Monitor</div>
        <div class="overall-status {'up' if down_count == 0 else 'down'}">
            {'✅ Всі системи працюють' if down_count == 0 else '⚠️ Деякі проблеми'}
        </div>
        <div class="stats">
            <div class="stat"><div class="stat-value" style="color: #00d9ff;">{total}</div><div class="stat-label">Моніторів</div></div>
            <div class="stat"><div class="stat-value" style="color: #00ff88;">{up_count}</div><div class="stat-label">Онлайн</div></div>
            <div class="stat"><div class="stat-value" style="color: #ff4757;">{down_count}</div><div class="stat-label">Офлайн</div></div>
        </div>
    </div>
    <div class="container">{monitors_html}
    </div>
    <div class="footer"><p>Оновлено: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}</p></div>
</body>
</html>'''
    
    return HTMLResponse(content=status_html)

@app.post("/api/sites")
async def add_site(site: SiteCreate):
    conn = get_db_connection()
    c = conn.cursor()
    notify_methods = site.notify_methods or []
    notify_json = json.dumps(notify_methods)
    try:
        c.execute("INSERT INTO sites (name, url, check_interval, is_active, notify_methods) VALUES (?, ?, ?, ?, ?)",
                  (site.name, site.url, site.check_interval, site.is_active, notify_json))
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

@app.get("/api/ssl-certificates")
async def get_ssl_certificates():
    """Отримує інформацію про SSL сертифікати"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT sc.*, s.name as site_name, s.url as site_url 
        FROM ssl_certificates sc
        JOIN sites s ON sc.site_id = s.id
        GROUP BY sc.site_id
        ORDER BY sc.days_until_expire ASC
    """)
    certs = c.fetchall()
    conn.close()
    
    result = []
    for cert in certs:
        result.append({
            'id': cert['id'],
            'site_id': cert['site_id'],
            'site_name': cert['site_name'],
            'site_url': cert['site_url'],
            'hostname': cert['hostname'],
            'issuer': cert['issuer'],
            'subject': cert['subject'],
            'start_date': cert['start_date'],
            'expire_date': cert['expire_date'],
            'days_until_expire': cert['days_until_expire'],
            'is_valid': cert['is_valid'],
            'last_checked': cert['last_checked']
        })
    return result

@app.post("/api/ssl-certificates/check")
async def check_ssl_certificates():
    """Запускає перевірку SSL сертифікатів вручну"""
    await check_all_certificates()
    return {"message": "SSL certificates check completed"}
    certs = c.fetchall()
    conn.close()
    
    result = []
    for cert in certs:
        result.append({
            'id': cert['id'],
            'site_id': cert['site_id'],
            'site_name': cert['site_name'],
            'site_url': cert['site_url'],
            'hostname': cert['hostname'],
            'issuer': cert['issuer'],
            'subject': cert['subject'],
            'start_date': cert['start_date'],
            'expire_date': cert['expire_date'],
            'days_until_expire': cert['days_until_expire'],
            'is_valid': cert['is_valid'],
            'last_checked': cert['last_checked']
        })
    return result

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
    
    notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
    await check_site_status(site_id, site['url'], notify_methods)
    return {"message": "Check completed"}

@app.put("/api/sites/{site_id}")
async def update_site(site_id: int, site_update: SiteUpdate):
    conn = get_db_connection()
    c = conn.cursor()
    
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
        params.append(site_id)
        c.execute(f"UPDATE sites SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()
    return {"message": "Site updated"}

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
    save_notify_settings_to_db()
    return {"message": "Settings saved"}

class AppSettings(BaseModel):
    display_address: Optional[str] = ""

@app.post("/api/app-settings")
async def save_app_settings(settings: AppSettings):
    global DISPLAY_ADDRESS
    DISPLAY_ADDRESS = settings.display_address or ""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO app_settings (id, display_address) VALUES (1, ?)", (DISPLAY_ADDRESS,))
    conn.commit()
    conn.close()
    return {"message": "Settings saved"}

@app.get("/api/app-settings")
async def get_app_settings():
    return {"display_address": DISPLAY_ADDRESS}

async def monitor_loop():
    """Основний цикл моніторингу"""
    last_cert_check = datetime.now() - timedelta(hours=25)  # Запускаємо перевірку сертифікатів відразу
    
    while True:
        # Перевірка доступності сайтів
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, url, notify_methods FROM sites WHERE is_active = 1")
        sites = c.fetchall()
        conn.close()
        
        for site in sites:
            notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
            await check_site_status(site['id'], site['url'], notify_methods)
        
        # Перевірка SSL сертифікатів раз на добу
        if (datetime.now() - last_cert_check).total_seconds() >= 86400:  # 24 години
            print("Checking SSL certificates...")
            await check_all_certificates()
            last_cert_check = datetime.now()
        
        await asyncio.sleep(CHECK_INTERVAL)

if IS_WINDOWS:
    class UptimeMonitorService(win32serviceutil.ServiceFramework):
        _svc_name_ = "UptimeMonitor"
        _svc_display_name_ = "Uptime Monitor Service"
        
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            
        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            
        def SvcDoRun(self):
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
            
            import uvicorn
            import threading
            
            monitor_thread = threading.Thread(target=lambda: asyncio.run(monitor_loop()), daemon=True)
            monitor_thread.start()
            
            # Setup SSL if enabled
            ssl_context = setup_ssl()
            uvicorn.run(
                app, 
                host=CONFIG['server'].get('host', '0.0.0.0'), 
                port=CONFIG['server'].get('port', 8080), 
                log_level="error",
                ssl_keyfile=CONFIG['ssl'].get('key_path') if ssl_context else None,
                ssl_certfile=CONFIG['ssl'].get('cert_path') if ssl_context else None
            )
            
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

    def run_service():
        win32serviceutil.HandleCommandLine(UptimeMonitorService)

# ============ AUTH ROUTES ============

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Сторінка логіну"""
    try:
        session_id = request.cookies.get('session_id') or ""
        if session_id and auth_module.validate_session(session_id, DB_PATH):
            return RedirectResponse(url='/', status_code=302)
        
        error_html = f'<div class="error">{error}</div>' if error else ''
        warning_html = '<div class="warning">WARNING: Change password after first login!</div>'
        return auth_module.LOGIN_HTML.format(error_message=error_html, warning_message=warning_html)
    except Exception as e:
        print(f"Login page error: {e}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Обробка логіну"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password_hash, must_change_password FROM users WHERE username = ?",
             (username,))
    user = c.fetchone()
    conn.close()

    if not user:
        return RedirectResponse(url='/login?error=Невірне ім\'я користувача або пароль', status_code=302)

    # Перевіряємо пароль через verify_password
    if not auth_module.verify_password(password, user['password_hash']):
        return RedirectResponse(url='/login?error=Невірне ім\'я користувача або пароль', status_code=302)

    # Створюємо сесію
    session_id = auth_module.create_session(user['id'], DB_PATH)
    
    # Перевіряємо чи потрібно змінити пароль
    if user['must_change_password']:
        response = RedirectResponse(url='/change-password', status_code=302)
    else:
        response = RedirectResponse(url='/', status_code=302)
    
    response.set_cookie(key='session_id', value=session_id, httponly=True, max_age=604800)
    return response

@app.get("/logout")
async def logout(request: Request):
    """Вихід"""
    session_id = request.cookies.get('session_id')
    if session_id:
        auth_module.delete_session(session_id, DB_PATH)
    
    response = RedirectResponse(url='/login', status_code=302)
    response.delete_cookie('session_id')
    return response

@app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request, error: str = None):
    """Сторінка зміни пароля"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    
    if not user:
        return RedirectResponse(url='/login', status_code=302)
    
    error_html = f'<div class="error">{error}</div>' if error else ''
    return auth_module.CHANGE_PASSWORD_HTML.format(error_message=error_html)

@app.post("/change-password")
async def change_password(request: Request, current_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    """Обробка зміни пароля"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    
    if not user:
        return RedirectResponse(url='/login', status_code=302)
    
    # Перевіряємо поточний пароль
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE id = ?", (user['user_id'],))
    user_data = c.fetchone()
    conn.close()

    if not user_data or not auth_module.verify_password(current_password, user_data['password_hash']):
        return RedirectResponse(url='/change-password?error=Невірний поточний пароль', status_code=302)
    
    # Перевіряємо чи паролі співпадають
    if new_password != confirm_password:
        return RedirectResponse(url='/change-password?error=Нові паролі не співпадають', status_code=302)
    
    # Перевіряємо довжину пароля
    if len(new_password) < 6:
        return RedirectResponse(url='/change-password?error=Пароль повинен містити мінімум 6 символів', status_code=302)
    
    # Змінюємо пароль
    if auth_module.change_password(user['user_id'], new_password, DB_PATH):
        return RedirectResponse(url='/?message=Пароль успішно змінено', status_code=302)
    else:
        return RedirectResponse(url='/change-password?error=Помилка при зміні пароля', status_code=302)

@app.get("/api/user")
async def get_user(request: Request):
    """Отримати поточного користувача"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"username": user['username'], "is_admin": user['is_admin']}

# ============ END AUTH ROUTES ============

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        import tkinter as tk
        from tkinter import simpledialog
        
        root = tk.Tk()
        root.withdraw()
        
        port_input = simpledialog.askinteger("Встановлення", "Введіть порт:", initialvalue=8000, minvalue=1, maxvalue=65535)
        
        if port_input:
            port = port_input
            with open(os.path.join(APP_DIR, "port.txt"), "w") as f:
                f.write(str(port))
        
        root.destroy()
    
    if len(sys.argv) > 1 and sys.argv[1] in ('start', 'stop', 'restart', 'install', 'remove'):
        run_service()
    else:
        # Create port.txt if it doesn't exist (for first run)
        port_file = os.path.join(APP_DIR, "port.txt")
        if not os.path.exists(port_file):
            try:
                with open(port_file, "w") as f:
                    f.write(str(port))
            except:
                pass
        
        print(f"="*60)
        print(f"  Uptime Monitor - Production Ready")
        # Get current configuration
        current_port = CONFIG['server'].get('port', 8080)
        current_host = CONFIG['server'].get('host', '0.0.0.0')
        current_domain = CONFIG['server'].get('domain', get_server_ip())
        ssl_enabled = CONFIG.get('ssl', {}).get('enabled', False)
        
        protocol = 'https' if ssl_enabled else 'http'
        access_url = f"{protocol}://{current_domain}:{current_port}"
        
        print(f"="*60)
        print(f"  Uptime Monitor - Production Ready")
        print(f"="*60)
        print(f"  Version:     latest (main branch)")
        print(f"  Port:        {current_port}")
        print(f"  Host:        {current_host}")
        print(f"  Domain:      {current_domain}")
        print(f"  SSL:         {'Enabled' if ssl_enabled else 'Disabled'}")
        print(f"  URL:         {access_url}")
        print(f"="*60)
        print(f"  Default Credentials:")
        print(f"    Username: admin")
        print(f"    Password: admin")
        print(f"  Please change the password after first login!")
        print(f"="*60)
        print(f"Management commands:")
        print(f"  sudo systemctl status uptime-monitor")
        print(f"  sudo systemctl restart uptime-monitor")
        print(f"  sudo systemctl stop uptime-monitor")
        print(f"")
        print(f"Configuration:")
        print(f"  Config file: {CONFIG_PATH}")
        print(f"  Logs:        {CONFIG.get('log_dir', '/var/log/uptime-monitor')}/")
        print(f"="*60)
        
        import uvicorn
        import threading
        
        monitor_thread = threading.Thread(target=lambda: asyncio.run(monitor_loop()), daemon=True)
        monitor_thread.start()
        
        # Setup SSL if enabled
        ssl_context = setup_ssl()
        uvicorn.run(
            app, 
            host=current_host, 
            port=current_port, 
            log_level="warning",
            ssl_keyfile=CONFIG['ssl'].get('key_path') if ssl_context else None,
            ssl_certfile=CONFIG['ssl'].get('cert_path') if ssl_context else None
        )
