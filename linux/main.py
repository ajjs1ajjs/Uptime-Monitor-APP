import sys
import os
import json

# Get the application directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Get port from file if exists, otherwise use default
port = 8080
port_file = os.path.join(APP_DIR, "port.txt")
if os.path.exists(port_file):
    try:
        with open(port_file, "r") as f:
            port = int(f.read().strip())
    except:
        pass

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

# Імпортуємо логер та БД
from logger import logger
from database import get_db_connection, init_db_pool, get_db_path

app = FastAPI(title="Uptime Monitor")

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
    
    with get_db_connection(DB_PATH) as conn:
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

init_db()

def load_notify_settings():
    with get_db_connection(DB_PATH) as conn:
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

def save_notify_settings_to_db():
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO notify_config (id, config) VALUES (1, ?)", (json.dumps(NOTIFY_SETTINGS),))
        conn.commit()

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
        logger.error(f"Telegram error: {e}")

async def send_teams(message: str):
    settings = NOTIFY_SETTINGS["teams"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings['webhook_url'], json=payload)
    except Exception as e:
        logger.error(f"Teams error: {e}")

async def send_discord(message: str):
    settings = NOTIFY_SETTINGS["discord"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"content": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings['webhook_url'], json=payload)
    except Exception as e:
        logger.error(f"Discord error: {e}")

async def send_slack(message: str):
    settings = NOTIFY_SETTINGS["slack"]
    if not settings.get("webhook_url"):
        return
    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            await session.post(settings['webhook_url'], json=payload)
    except Exception as e:
        logger.error(f"Slack error: {e}")

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
        logger.error(f"Email error: {e}")

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
        logger.error(f"SMS error: {e}")

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
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers=headers, allow_redirects=True) as response:
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
    
    with get_db_connection(DB_PATH) as conn:
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
            if last_alert is None or (checked_at - last_alert).total_seconds() >= 60:
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
    
    return status, status_code, response_time, error_message

async def check_site_certificate(site_id: int, url: str, notify_methods: List[str]):
    """Перевіряє SSL сертифікат сайту та зберігає результати"""
    # Перевіряємо тільки HTTPS сайти
    if not url.startswith('https://'):
        return
    
    cert_info = await check_ssl_certificate(url)
    
    if not cert_info:
        return
    
    with get_db_connection(DB_PATH) as conn:
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

async def check_all_certificates():
    """Перевіряє SSL сертифікати всіх активних сайтів"""
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, url, notify_methods FROM sites WHERE is_active = 1 AND url LIKE 'https://%'")
        sites = c.fetchall()
    
    for site in sites:
        notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
        await check_site_certificate(site['id'], site['url'], notify_methods)
        await asyncio.sleep(1)  # Пауза між перевірками

async def monitor_loop():
    """Головний цикл моніторингу"""
    last_cert_check = datetime.now() - timedelta(hours=23)  # Перевірити сертифікати невдовзі після старту
    
    while True:
        try:
            with get_db_connection(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM sites WHERE is_active = 1")
                sites = c.fetchall()
            
            # Check sites in parallel
            tasks = []
            for site in sites:
                notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
                tasks.append(check_site_status(site['id'], site['url'], notify_methods))
            
            if tasks:
                await asyncio.gather(*tasks)
            
            # Check SSL certificates once a day
            if (datetime.now() - last_cert_check).total_seconds() >= 86400:
                logger.info("Checking SSL certificates...")
                await check_all_certificates()
                last_cert_check = datetime.now()
        
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
            
        await asyncio.sleep(CHECK_INTERVAL)

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
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT sc.*, s.name as site_name, s.url as site_url 
            FROM ssl_certificates sc
            JOIN sites s ON sc.site_id = s.id
            ORDER BY sc.days_until_expire ASC
        """)
        certs = c.fetchall()
    
    return certs

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
    
    with get_db_connection(DB_PATH) as conn:
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
    
    total_sites = len(site_data)
    up_sites = sum(1 for s in site_data if s['status'] == 'up')
    down_sites = sum(1 for s in site_data if s['status'] == 'down')
    
    notify_config_json = json.dumps(NOTIFY_SETTINGS)
    display_address = DISPLAY_ADDRESS if DISPLAY_ADDRESS else f"http://{LOCAL_IP}:{port}"
    
    certs_data = await get_ssl_certificates_data()
    
    # Render dashboard using Jinja2 if available, or fallback to simple HTML
    try:
        return auth_module.render_template('dashboard.html', 
            sites=site_data, 
            total_sites=total_sites, 
            up_sites=up_sites, 
            down_sites=down_sites,
            display_address=display_address,
            notify_config_json=notify_config_json,
            certs=certs_data,
            local_ip=LOCAL_IP,
            port=port
        )
    except:
        return HTMLResponse(content="<h1>Dashboard</h1><p>Please check template configuration.</p>")

# ============ AUTH ROUTES ============

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    """Сторінка логіну"""
    try:
        session_id = request.cookies.get('session_id') or ""
        if session_id and auth_module.validate_session(session_id, DB_PATH):
            return RedirectResponse(url='/', status_code=302)
        
        return auth_module.render_template('login.html', error_message=error)
    except Exception as e:
        logger.error(f"Login page error: {e}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Обробка логіну"""
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, password_hash, must_change_password FROM users WHERE username = ?",
                 (username,))
        user = c.fetchone()
    
    # Перевіряємо чи користувач існує і пароль правильний
    if not user or not auth_module.verify_password(password, user['password_hash']):
        return RedirectResponse(url='/login?error=Невірне ім\'я користувача або пароль', status_code=302)
    
    # Створюємо сесію
    session_id = auth_module.create_session(user['id'], DB_PATH)
    
    # Перевіряємо чи потрібно змінити пароль
    if user['must_change_password']:
        response = RedirectResponse(url='/change-password', status_code=302)
    else:
        response = RedirectResponse(url='/', status_code=302)
    
    response.set_cookie(
        key='session_id',
        value=session_id,
        httponly=True,
        secure=False,  # Встановіть True для HTTPS
        samesite='lax',
        max_age=604800
    )
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
    
    return auth_module.render_template('change_password.html', error_message=error)

@app.post("/change-password")
async def change_password(request: Request, current_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    """Обробка зміни пароля"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    
    if not user:
        return RedirectResponse(url='/login', status_code=302)
    
    # Перевіряємо поточний пароль
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE id = ?", (user['user_id'],))
        result = c.fetchone()
    
    if not result or not auth_module.verify_password(current_password, result['password_hash']):
        return RedirectResponse(url='/change-password?error=Невірний поточний пароль', status_code=302)
    
    # Перевіряємо чи паролі співпадають
    if new_password != confirm_password:
        return RedirectResponse(url='/change-password?error=Паролі не співпадають', status_code=302)
    
    # Перевіряємо довжину пароля
    if len(new_password) < 6:
        return RedirectResponse(url='/change-password?error=Пароль має бути не менше 6 символів', status_code=302)
    
    # Змінюємо пароль
    if auth_module.change_password(user['user_id'], new_password, DB_PATH):
        return RedirectResponse(url='/?message=Пароль змінено успішно', status_code=302)
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

@app.get("/api/sites")
async def get_sites(request: Request):
    """Отримати всі сайти"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sites ORDER BY id DESC")
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
    return result

@app.post("/api/sites")
async def add_site(site: SiteCreate, request: Request):
    """Додати новий сайт"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        with get_db_connection(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO sites (name, url, check_interval, notify_methods) VALUES (?, ?, ?, ?)",
                     (site.name, site.url, site.check_interval, json.dumps(site.notify_methods or [])))
            conn.commit()
            site_id = c.lastrowid
        return {"id": site_id, "message": "Site added"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Site with this URL already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/sites/{site_id}")
async def update_site_endpoint(site_id: int, site_update: SiteUpdate, request: Request):
    """Оновити налаштування сайту"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Список дозволених колонок для оновлення
    allowed_columns = {'name', 'url', 'notify_methods', 'is_active'}
    
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
            col_name = update.split('=')[0].strip()
            if col_name not in allowed_columns:
                raise HTTPException(status_code=400, detail=f"Invalid column: {col_name}")
        
        params.append(site_id)
        
        with get_db_connection(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"UPDATE sites SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
            
    return {"message": "Site updated"}

@app.delete("/api/sites/{site_id}")
async def delete_site(site_id: int, request: Request):
    """Видалити сайт"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM status_history WHERE site_id = ?", (site_id,))
        c.execute("DELETE FROM ssl_certificates WHERE site_id = ?", (site_id,))
        c.execute("DELETE FROM sites WHERE id = ?", (site_id,))
        conn.commit()
    return {"message": "Site deleted"}

@app.post("/api/sites/{site_id}/check")
async def manual_check(site_id: int, request: Request):
    """Ручна перевірка сайту"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
        site = c.fetchone()
    
    if site:
        notify_methods = json.loads(site['notify_methods']) if site['notify_methods'] else []
        status, code, time, error = await check_site_status(site['id'], site['url'], notify_methods)
        return {"status": status, "code": code, "time": time, "error": error}
    else:
        raise HTTPException(status_code=404, detail="Site not found")

@app.get("/api/notify-settings")
async def get_notify_settings(request: Request):
    """Отримати налаштування сповіщень"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return NOTIFY_SETTINGS

@app.post("/api/notify-settings")
async def update_notify_settings(settings: dict, request: Request):
    """Оновити налаштування сповіщень"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    global NOTIFY_SETTINGS
    NOTIFY_SETTINGS.update(settings)
    save_notify_settings_to_db()
    return {"message": "Settings updated"}

@app.get("/api/app-settings")
async def get_app_settings(request: Request):
    """Отримати загальні налаштування"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"display_address": DISPLAY_ADDRESS}

@app.post("/api/app-settings")
async def update_app_settings(settings: dict, request: Request):
    """Оновити загальні налаштування"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    global DISPLAY_ADDRESS
    DISPLAY_ADDRESS = settings.get('display_address', '')
    
    with get_db_connection(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO app_settings (id, display_address) VALUES (1, ?)", (DISPLAY_ADDRESS,))
        conn.commit()
    return {"message": "App settings updated"}

@app.get("/api/ssl-certificates")
async def api_get_ssl_certs(request: Request):
    """Отримати SSL сертифікати через API"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    certs = await get_ssl_certificates_data()
    return [dict(c) for c in certs]

@app.post("/api/ssl-certificates/check")
async def api_check_ssl_certs(request: Request):
    """Запустити перевірку SSL сертифікатів вручну"""
    session_id = request.cookies.get('session_id')
    user = auth_module.validate_session(session_id, DB_PATH)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    await check_all_certificates()
    return {"message": "SSL certificates check initiated"}

@app.get("/health")
async def health_check():
    """Перевірка працездатності додатку"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============ STARTUP ============

if __name__ == "__main__":
    logger.info(f"="*60)
    logger.info(f"  Uptime Monitor - Starting")
    logger.info(f"="*60)
    logger.info(f"  Port: {port}")
    logger.info(f"  Database: {DB_PATH}")
    logger.info(f"  Access URL: http://{LOCAL_IP}:{port}")
    logger.info(f"="*60)
    
    import uvicorn
    import threading
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(target=lambda: asyncio.run(monitor_loop()), daemon=True)
    monitor_thread.start()
    
    # Start web server
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
