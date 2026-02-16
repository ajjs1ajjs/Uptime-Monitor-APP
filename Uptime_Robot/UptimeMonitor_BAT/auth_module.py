import hashlib
import secrets
import functools
from fastapi import Request, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
import sqlite3
import json
from datetime import datetime, timedelta

# Ініціалізація таблиці користувачів
def init_auth_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблиця користувачів
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT 0,
        created_at TEXT,
        last_login TEXT
    )''')
    
    # Таблиця сесій
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id INTEGER,
        created_at TEXT,
        expires_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Створюємо дефолтного адміна якщо немає
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    if not c.fetchone():
        # Пароль: admin123
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, 1, ?)",
                 ('admin', password_hash, datetime.now().isoformat()))
        print("Default user created: admin / admin123")
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Хешує пароль"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id: int) -> str:
    """Створює сесію і повертає session_id"""
    session_id = secrets.token_urlsafe(32)
    now = datetime.now()
    expires = now + timedelta(days=7)  # Сесія на 7 днів
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (session_id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
             (session_id, user_id, now.isoformat(), expires.isoformat()))
    
    # Оновлюємо last_login
    c.execute("UPDATE users SET last_login = ? WHERE id = ?", (now.isoformat(), user_id))
    conn.commit()
    conn.close()
    
    return session_id

def validate_session(session_id: str) -> dict:
    """Перевіряє сесію і повертає дані користувача"""
    if not session_id:
        return None
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Перевіряємо чи сесія існує і не протермінована
    c.execute("""
        SELECT s.user_id, u.username, u.is_admin, s.expires_at 
        FROM sessions s 
        JOIN users u ON s.user_id = u.id 
        WHERE s.session_id = ?
    """, (session_id,))
    
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
    
    # Перевіряємо термін дії
    expires = datetime.fromisoformat(row['expires_at'])
    if datetime.now() > expires:
        return None
    
    return {
        'user_id': row['user_id'],
        'username': row['username'],
        'is_admin': row['is_admin']
    }

def delete_session(session_id: str):
    """Видаляє сесію (logout)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

# Middleware для перевірки сесії
async def get_current_user(request: Request):
    session_id = request.cookies.get('session_id')
    user = validate_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# Декоратор для захисту роутів
def require_auth(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Отримуємо request з args або kwargs
        request = kwargs.get('request') or (args[0] if args else None)
        if not request:
            raise HTTPException(status_code=401, detail="Request required")
        
        session_id = request.cookies.get('session_id')
        user = validate_session(session_id)
        if not user:
            return RedirectResponse(url='/login', status_code=302)
        
        return await func(*args, **kwargs)
    return wrapper

# Login page HTML
LOGIN_HTML = '''<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uptime Monitor - Login</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            margin-bottom: 15px;
        }
        h1 {
            color: #333;
            font-size: 24px;
            text-align: center;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input[type="text"],
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e1e1;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus,
        input[type="password"]:focus {
            border-color: #667eea;
            outline: none;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .info {
            background: #e8f4f8;
            color: #0066cc;
            padding: 12px;
            border-radius: 6px;
            margin-top: 20px;
            font-size: 13px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <div class="logo-icon">⚡</div>
            <h1>Uptime Monitor</h1>
        </div>
        {error_message}
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Sign In</button>
        </form>
        <div class="info">
            Default: admin / admin123<br>
            Change after first login!
        </div>
    </div>
</body>
</html>'''

# Додаємо роути для авторизації
def add_auth_routes(app):
    
    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request, error: str = None):
        """Сторінка логіну"""
        # Перевіряємо чи вже залогінений
        session_id = request.cookies.get('session_id')
        if validate_session(session_id):
            return RedirectResponse(url='/', status_code=302)
        
        error_html = f'<div class="error">{error}</div>' if error else ''
        return LOGIN_HTML.format(error_message=error_html)
    
    @app.post("/login")
    async def login(request: Request, username: str = Form(...), password: str = Form(...)):
        """Обробка логіну"""
        password_hash = hash_password(password)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, is_admin FROM users WHERE username = ? AND password_hash = ?",
                 (username, password_hash))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return RedirectResponse(url='/login?error=Invalid username or password', status_code=302)
        
        # Створюємо сесію
        session_id = create_session(user['id'])
        
        response = RedirectResponse(url='/', status_code=302)
        response.set_cookie(key='session_id', value=session_id, httponly=True, max_age=604800)
        return response
    
    @app.get("/logout")
    async def logout(request: Request):
        """Вихід"""
        session_id = request.cookies.get('session_id')
        if session_id:
            delete_session(session_id)
        
        response = RedirectResponse(url='/login', status_code=302)
        response.delete_cookie('session_id')
        return response
    
    @app.get("/api/user")
    async def get_user(request: Request):
        """Отримати поточного користувача"""
        session_id = request.cookies.get('session_id')
        user = validate_session(session_id)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return user

# Ініціалізація при старті
init_auth_tables()

print("✅ Auth module loaded")
print("   Default login: admin / admin123")
print("   Change password in web interface after first login!")
