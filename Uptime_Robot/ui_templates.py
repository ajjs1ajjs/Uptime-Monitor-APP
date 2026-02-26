"""
Module for UI Templates (HTML, CSS, JS)
# Refactoring in progress
"""

# Public Status Page Template
PUBLIC_STATUS_HTML = """<!DOCTYPE html>
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
        <div class="overall-status {overall_status_class}">
            {overall_status_text}
        </div>
        <div class="stats">
            <div class="stat"><div class="stat-value" style="color: #00d9ff;">{total}</div><div class="stat-label">Моніторів</div></div>
            <div class="stat"><div class="stat-value" style="color: #00ff88;">{up_count}</div><div class="stat-label">Онлайн</div></div>
            <div class="stat"><div class="stat-value" style="color: #ff4757;">{down_count}</div><div class="stat-label">Офлайн</div></div>
        </div>
    </div>
    <div class="container">{monitors_html}
    </div>
    <div class="footer"><p>Оновлено: {timestamp}</p></div>
</body>
</html>"""

# Dashboard HTML Template
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uptime Monitor - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16162a;
            --bg-card: #0f0f1a;
            --accent: #00d9ff;
            --accent-hover: #00a8cc;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text-primary: #ffffff;
            --text-secondary: #94a3b8;
            --border: #334155;
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg-gradient); color: var(--text-primary); min-height: 100vh; }}
        
        .header {{ background: rgba(15, 23, 42, 0.95); padding: 16px 32px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 100; }}
        .logo {{ font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 12px; }}
        .logo-icon {{ width: 40px; height: 40px; background: linear-gradient(135deg, var(--accent), #06b6d4); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; box-shadow: 0 4px 15px rgba(0, 217, 255, 0.3); }}
        
        .hero-stats {{ display: flex; gap: 24px; margin: 32px; background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)); padding: 28px 36px; border-radius: 20px; border: 1px solid rgba(148, 163, 184, 0.1); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }}
        .hero-stat {{ text-align: center; flex: 1; position: relative; padding: 0 20px; }}
        .hero-stat:not(:last-child)::after {{ content: ''; position: absolute; right: 0; top: 50%; transform: translateY(-50%); height: 50%; width: 1px; background: var(--border); }}
        .hero-stat-value {{ font-size: 42px; font-weight: 700; color: var(--accent); text-shadow: 0 0 30px rgba(0, 217, 255, 0.3); }}
        .hero-stat-label {{ color: var(--text-secondary); font-size: 13px; margin-top: 8px; text-transform: uppercase; letter-spacing: 1px; }}
        
        .monitoring-types {{ display: flex; gap: 12px; margin: 0 32px 24px; flex-wrap: wrap; }}
        .monitor-type-btn {{ padding: 10px 20px; background: rgba(30, 41, 59, 0.6); border: 1px solid var(--border); border-radius: 10px; cursor: pointer; font-weight: 500; color: var(--text-secondary); transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; font-size: 13px; }}
        .monitor-type-btn:hover {{ border-color: var(--accent); color: var(--text-primary); background: rgba(0, 217, 255, 0.1); }}
        .monitor-type-btn.active {{ background: linear-gradient(135deg, var(--accent), #06b6d4); color: #000; border-color: var(--accent); font-weight: 600; }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 0 32px 32px; }}
        #tab-dashboard .container {{
            max-width: none !important;
            margin: 0 !important;
            width: 100% !important;
            padding: 0 12px 32px !important;
        }}
        
        .panel {{ background: linear-gradient(180deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); padding: 24px; border-radius: 16px; margin-bottom: 24px; border: 1px solid rgba(148, 163, 184, 0.1); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); transition: all 0.3s ease; }}
        .panel:hover {{ border-color: rgba(0, 217, 255, 0.3); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4); }}
        .panel-title {{ font-size: 16px; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; color: var(--text-primary); }}
        
        .chart-container {{ position: relative; height: 280px; margin: 16px 0; }}
        
        .monitor-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }}
        .monitor-card {{ background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%); padding: 20px; border-radius: 16px; border: 1px solid rgba(148, 163, 184, 0.1); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); position: relative; overflow: hidden; }}
        .monitor-card:hover {{ transform: translateY(-5px) scale(1.02); box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 30px rgba(0,217,255,0.1); }}
        .monitor-card.up {{ border-left: 4px solid var(--success); }}
        .monitor-card.down {{ border-left: 4px solid var(--danger); }}
        .monitor-card.paused {{ border-left: 4px solid var(--warning); opacity: 0.7; }}
        
        .monitor-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
        .monitor-name {{ font-size: 18px; font-weight: 600; }}
        .monitor-url {{ color: var(--text-secondary); font-size: 13px; word-break: break-all; margin-top: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 280px; }}
        .monitor-type-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; background: rgba(0,255,136,0.15); color: var(--accent); }}
        
        .monitor-stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; padding: 12px 0; border-top: 1px solid rgba(148, 163, 184, 0.1); border-bottom: 1px solid rgba(148, 163, 184, 0.1); }}
        .monitor-stat {{ text-align: center; }}
        .monitor-stat-value {{ font-size: 16px; font-weight: 600; }}
        .monitor-stat-label {{ font-size: 11px; color: var(--text-secondary); margin-top: 4px; }}
        
        .monitor-actions {{ display: flex; gap: 8px; margin-top: 16px; }}
        .btn {{ flex: 1; padding: 10px; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; font-size: 12px; transition: all 0.2s ease; }}
        .btn-check {{ background: linear-gradient(135deg, var(--accent), #06b6d4); color: #000; }}
        .btn-edit {{ background: rgba(245, 158, 11, 0.15); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }}
        .btn-delete {{ background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.3); }}
        
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); z-index: 1000; align-items: center; justify-content: center; backdrop-filter: blur(4px); }}
        .modal.active {{ display: flex; }}
        .modal-content {{ background: linear-gradient(180deg, #1e293b, #0f172a); padding: 28px; border-radius: 16px; max-width: 480px; width: 90%; border: 1px solid var(--border); box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }}
        
        .tabs {{ display: flex; gap: 8px; margin: 0 32px; padding: 4px; background: rgba(15, 23, 42, 0.6); border-radius: 12px; border: 1px solid rgba(148, 163, 184, 0.1); width: fit-content; }}
        .tab-btn {{ padding: 10px 24px; background: transparent; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; color: var(--text-secondary); transition: all 0.2s ease; font-size: 14px; }}
        .tab-btn.active {{ background: linear-gradient(135deg, var(--accent), #06b6d4); color: #000; font-weight: 600; }}
        
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; animation: fadeSlideIn 0.4s ease; }}
        
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes fadeSlideIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        
        .notify-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }}
        .notify-card {{ background: linear-gradient(180deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); padding: 20px; border-radius: 14px; border: 1px solid rgba(148, 163, 184, 0.1); transition: all 0.2s ease; }}
        .notify-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }}
        
        .toggle {{ position: relative; display: inline-block; width: 44px; height: 24px; }}
        .toggle input {{ opacity: 0; width: 0; height: 0; }}
        .toggle-slider {{ position: absolute; cursor: pointer; inset: 0; background: rgba(30, 41, 59, 0.8); border-radius: 24px; transition: 0.2s; border: 1px solid var(--border); }}
        .toggle-slider::before {{ content: ''; position: absolute; height: 18px; width: 18px; left: 2px; bottom: 2px; background: var(--text-secondary); border-radius: 50%; transition: 0.2s; }}
        .toggle input:checked + .toggle-slider {{ background: var(--accent); border-color: var(--accent); }}
        .toggle input:checked + .toggle-slider::before {{ transform: translateX(20px); background: #000; }}
        
        .notify-fields {{ display: flex; flex-direction: column; gap: 10px; }}
        .notify-fields input {{ width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border); background: rgba(15, 23, 42, 0.8); color: var(--text-primary); font-size: 13px; }}
        
        .form-row {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
        .form-row input, .form-row select {{ flex: 1; min-width: 180px; padding: 12px; border-radius: 10px; background: rgba(15, 23, 42, 0.8); color: var(--text-primary); border: 1px solid var(--border); font-size: 14px; }}
        
        .ssl-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
        
        .header-btn {{ padding: 8px 16px; background: rgba(0, 217, 255, 0.15); color: var(--accent); text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: 500; transition: all 0.2s; border: 1px solid transparent; }}
        .header-btn.danger {{ background: rgba(239, 68, 68, 0.15); color: var(--danger); }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo"><div class="logo-icon">⚡</div><span>Uptime Monitor</span></div>
        <div style="display: flex; align-items: center; gap: 16px;">
            <div id="lastUpdate" style="color: var(--text-secondary); font-size: 13px;"></div>
            <a href="/status" target="_blank" class="header-btn">📄 Status</a>
            <a href="/logout" class="header-btn danger">🚪 Вийти</a>
        </div>
    </div>
    
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('dashboard')">Dashboard</button>
        <button class="tab-btn" onclick="switchTab('ssl')">SSL</button>
        <button class="tab-btn" onclick="switchTab('incidents')">Incidents</button>
        <button class="tab-btn" onclick="switchTab('settings')">Settings</button>
    </div>
    
    <div id="tab-dashboard" class="tab-content active">
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-value">{total_sites}</div>
                <div class="hero-stat-label">Моніторів</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value" style="color: var(--success);">{up_sites}</div>
                <div class="hero-stat-label">Онлайн</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value" style="color: var(--danger);">{down_sites}</div>
                <div class="hero-stat-label">Офлайн</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value" style="color: var(--warning);">0</div>
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
                    <button class="btn btn-check" style="background: linear-gradient(135deg, #00ff88, #00cc6a);" onclick="checkAllMonitors()">🔄 Перевірити всі</button>
                    <button class="btn btn-check" onclick="loadDashboard()">📊 Оновити дані</button>
                    <button class="btn btn-edit" onclick="switchTab('incidents')">⚠️ Інциденти</button>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">📊 Статус всіх моніторів</div>
                <div class="monitor-grid" id="dashboardMonitors"></div>
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
                <div class="panel-title">➕ Додати новий монітор</div>
                <div class="form-row">
                    <input type="text" id="siteName" placeholder="Назва">
                    <input type="url" id="siteUrl" placeholder="URL">
                </div>
                <div class="form-row" style="margin-top: 15px;">
                    <select id="monitorType">
                        <option value="http">🌐 HTTP(S)</option>
                        <option value="port">🔌 Порт</option>
                        <option value="ping">📡 Пінг</option>
                        <option value="ssl">🔒 SSL</option>
                    </select>
                    <select id="siteNotify" multiple>
                        <option value="telegram">📱 Telegram</option>
                        <option value="teams">🏢 Teams</option>
                        <option value="discord">🎮 Discord</option>
                        <option value="email">📧 Email</option>
                    </select>
                </div>
                <button class="btn btn-check" style="margin-top: 15px; width: 100%;" onclick="addSite()">➕ Додати монітор</button>
            </div>
            
            <div class="panel">
                <div class="panel-title">🔗 Налаштування адреси</div>
                <div class="address-config">
                    <div class="form-row">
                        <input type="text" id="displayAddress" placeholder="Адреса доступу">
                        <button onclick="saveDisplayAddress()">💾 Зберегти</button>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">🔧 Налаштування сповіщень</div>
                <div class="notify-grid">
                    <!-- Notification Cards here -->
                    {notification_cards}
                </div>
                <button class="btn btn-check" style="margin-top: 20px; width: 100%;" onclick="saveNotifySettings()">💾 Зберегти налаштування</button>
            </div>
        </div>
    </div>

    <div id="tab-ssl" class="tab-content">
        <div class="panel">
            <div class="panel-title" style="display:flex; justify-content:space-between;">
                <span>🔒 SSL Сертифікати</span>
                <button class="btn btn-check" onclick="checkSSLCertificates()" style="padding:8px 20px;">🔄 Перевірити зараз</button>
            </div>
            <div class="ssl-grid" id="sslGrid"></div>
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
        var notifyConfig = {notify_config_json};

        {js_functions}

        initNotifyUI();
        loadAppSettings();
        loadSites();
        loadSSLCertificates();
        setInterval(loadSites, 30000);
    </script>
</body>
</html>"""

# Auth Templates
LOGIN_HTML = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uptime Monitor - Login</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .login-container {{
            background: #16213e;
            padding: 40px;
            border-radius: 15px;
            border: 1px solid #2a2a4a;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
        }}
        .logo {{ text-align: center; margin-bottom: 30px; }}
        .logo-icon {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #00d9ff 0%, #00a8cc 100%);
            border-radius: 15px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            margin-bottom: 15px;
        }}
        h1 {{ color: #fff; font-size: 24px; text-align: center; }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 8px; color: #a0a0b0; font-weight: 500; }}
        input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #2a2a4a;
            background: #0f0f23;
            color: #fff;
            border-radius: 8px;
            font-size: 14px;
        }}
        button {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00d9ff 0%, #00a8cc 100%);
            color: #000;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }}
        .error {{ background: rgba(255, 71, 87, 0.15); color: #ff4757; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; border: 1px solid rgba(255, 71, 87, 0.3); }}
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
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>"""

CHANGE_PASSWORD_HTML = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uptime Monitor - Change Password</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .container {{
            background: #16213e;
            padding: 40px;
            border-radius: 15px;
            border: 1px solid #2a2a4a;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
        }}
        .warning-box {{
            background: rgba(255, 71, 87, 0.15);
            border: 1px solid rgba(255, 71, 87, 0.3);
            color: #ff4757;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 25px;
            text-align: center;
        }}
        input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #2a2a4a;
            background: #0f0f23;
            color: #fff;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        button {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00d9ff 0%, #00a8cc 100%);
            color: #000;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Change Password</h1>
        <div class="warning-box">Please change your default password for security.</div>
        {error_message}
        <form method="POST" action="/change-password">
            <input type="password" name="current_password" placeholder="Current Password" required>
            <input type="password" name="new_password" placeholder="New Password" required minlength="6">
            <input type="password" name="confirm_password" placeholder="Confirm New Password" required>
            <button type="submit">Change Password</button>
        </form>
    </div>
</body>
</html>"""

DASHBOARD_JS = """
        let currentFilter = 'all';
        let sitesData = [];
        let sslCertificatesData = [];
        let responseChart = null;

        async function loadSites() {
            try {
                const response = await fetch('/api/sites');
                sitesData = await response.json();
                renderMonitors();
                updateStats();
            } catch(e) { console.error(e); }
        }

        function updateStats() {
            const up = sitesData.filter(s => s.status === 'up').length;
            const down = sitesData.filter(s => s.status === 'down').length;
            const total = sitesData.length;
            
            // Update hero stats if they exist
            const vTotal = document.querySelector('.hero-stat-value:nth-child(1)');
            const vUp = document.querySelector('.hero-stat-value:nth-child(2)');
            const vDown = document.querySelector('.hero-stat-value:nth-child(3)');
            
            document.getElementById('lastUpdate').innerText = 'Останнє оновлення: ' + new Date().toLocaleTimeString();
        }

        function renderMonitors() {
            const grid = document.getElementById('dashboardMonitors');
            if (!grid) return;
            
            const filtered = currentFilter === 'all' ? sitesData : sitesData.filter(s => s.monitor_type === currentFilter);
            
            if (filtered.length === 0) {
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-secondary);">Моніторів не знайдено.</div>';
                return;
            }
            
            let html = '';
            filtered.forEach(site => {
                const statusClass = site.status === 'up' ? 'up' : (site.status === 'paused' ? 'paused' : 'down');
                const statusText = site.status === 'up' ? 'UP' : (site.status === 'paused' ? 'PAUSED' : 'DOWN');
                const statusColor = site.status === 'up' ? 'var(--success)' : 'var(--danger)';
                
                html += `
                <div class="monitor-card ${statusClass}">
                    <div class="monitor-header">
                        <div style="min-width: 0; flex: 1;">
                            <div class="monitor-name" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${site.name}">${site.name}</div>
                            <div class="monitor-url" title="${site.url}">${site.url}</div>
                        </div>
                        <span class="monitor-type-badge">${site.monitor_type}</span>
                    </div>
                    <div class="monitor-stats">
                        <div class="monitor-stat"><div class="monitor-stat-value" style="color:${statusColor}">${statusText}</div><div class="monitor-stat-label">Status</div></div>
                        <div class="monitor-stat"><div class="monitor-stat-value">${site.response_time || '—'}ms</div><div class="monitor-stat-label">Time</div></div>
                        <div class="monitor-stat"><div class="monitor-stat-value">${site.uptime || 100}%</div><div class="monitor-stat-label">Uptime</div></div>
                        <div class="monitor-stat"><div class="monitor-stat-value">${site.status_code || '—'}</div><div class="monitor-stat-label">HTTP</div></div>
                    </div>
                    <div class="monitor-actions">
                        <button class="btn btn-check" onclick="checkSite(${site.id})">Check</button>
                        <button class="btn btn-edit" onclick="openEditModal(${site.id}, '${encodeURIComponent(site.name)}', '${encodeURIComponent(site.url)}', ${JSON.stringify(site.notify_methods || [])})">Edit</button>
                        <button class="btn btn-delete" onclick="deleteSite(${site.id})">Delete</button>
                    </div>
                </div>`;
            });
            grid.innerHTML = html;
        }

        async function checkSite(id) {
            try {
                await fetch(`/api/sites/${id}/check`, { method: 'POST' });
                loadSites();
            } catch(e) { console.error(e); }
        }

        async function deleteSite(id) {
            if (!confirm('Ви впевнені, що хочете видалити цей монітор?')) return;
            try {
                await fetch(`/api/sites/${id}`, { method: 'DELETE' });
                loadSites();
            } catch(e) { console.error(e); }
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            document.querySelector(`.tab-btn[onclick="switchTab('${tabId}')"]`).classList.add('active');
            
            if (tabId === 'dashboard') loadSites();
            if (tabId === 'ssl') loadSSLCertificates();
        }

        async function addSite() {
            const name = document.getElementById('siteName').value;
            const url = document.getElementById('siteUrl').value;
            const monitor_type = document.getElementById('monitorType').value;
            const notify_select = document.getElementById('siteNotify');
            const notify_methods = Array.from(notify_select.selectedOptions).map(o => o.value);

            if (!name || !url) return alert('Заповніть назву та URL');

            try {
                const response = await fetch('/api/sites', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name, url, monitor_type, notify_methods})
                });
                if (response.ok) {
                    document.getElementById('siteName').value = '';
                    document.getElementById('siteUrl').value = '';
                    loadSites();
                    alert('Монітор додано!');
                }
            } catch(e) { console.error(e); }
        }

        async function loadSSLCertificates() {
            try {
                const response = await fetch('/api/ssl-certificates');
                sslCertificatesData = await response.json();
                renderSSLCertificates();
            } catch(e) { console.error(e); }
        }

        function renderSSLCertificates() {
            const grid = document.getElementById('sslGrid');
            if (!grid) return;
            if (sslCertificatesData.length === 0) {
                grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px;">Немає SSL даних.</div>';
                return;
            }
            let html = '';
            sslCertificatesData.forEach(cert => {
                const days = cert.days_until_expire;
                const statusColor = days <= 0 ? 'var(--danger)' : days <= 7 ? 'var(--warning)' : 'var(--success)';
                html += `
                <div class="ssl-card" style="padding: 12px; background: rgba(30, 41, 59, 0.4); border-radius: 10px; border-left: 4px solid ${statusColor}; border: 1px solid rgba(148, 163, 184, 0.1); margin-bottom: 10px; overflow: hidden;">
                    <div style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${cert.site_name}">${cert.site_name}</div>
                    <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${cert.hostname}">${cert.hostname}</div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px;">
                        <span>Term: ${days} days</span>
                        <span style="color: ${statusColor}">${days <= 0 ? '❌ Overdue' : '✅ Valid'}</span>
                    </div>
                </div>`;
            });
            grid.innerHTML = html;
        }

        let responseTimeData = [];
        let incidentsData = [];

        async function loadDashboard() {
            loadSites();
            loadSSLCertificates();
            await loadResponseTimeStats();
            await loadIncidents();
        }

        async function loadResponseTimeStats() {
            try {
                const response = await fetch('/api/stats/response-time');
                responseTimeData = await response.json();
                renderResponseTimeChart();
            } catch(e) { console.error(e); }
        }

        function renderResponseTimeChart() {
            const canvas = document.getElementById('responseTimeChart');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            const data = responseTimeData;
            
            if (data.length === 0) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#6b7280';
                ctx.font = '14px Inter';
                ctx.textAlign = 'center';
                ctx.fillText('Немає даних про час відповіді', canvas.width / 2, canvas.height / 2);
                return;
            }
            
            canvas.width = canvas.parentElement?.clientWidth || 600;
            canvas.height = 250;
            
            const maxTime = Math.max(...data.map(d => d.max_time), 100);
            const barWidth = (canvas.width - 60) / data.length - 10;
            const scale = (canvas.height - 60) / maxTime;
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            data.forEach((item, i) => {
                const x = 40 + i * (barWidth + 10);
                const avgHeight = item.avg_time * scale;
                const maxHeight = item.max_time * scale;
                
                ctx.fillStyle = 'rgba(0, 217, 255, 0.3)';
                ctx.fillRect(x, canvas.height - 40 - maxHeight, barWidth, maxHeight);
                
                ctx.fillStyle = '#00d9ff';
                ctx.fillRect(x, canvas.height - 40 - avgHeight, barWidth, avgHeight);
                
                ctx.fillStyle = '#9ca3af';
                ctx.font = '10px Inter';
                ctx.textAlign = 'center';
                const name = item.site_name.length > 10 ? item.site_name.substring(0, 10) + '...' : item.site_name;
                ctx.fillText(name, x + barWidth / 2, canvas.height - 10);
                
                ctx.fillStyle = '#00d9ff';
                ctx.font = '11px Inter';
                ctx.fillText(Math.round(item.avg_time) + 'ms', x + barWidth / 2, canvas.height - 45 - avgHeight);
            });
        }

        async function loadIncidents() {
            try {
                const response = await fetch('/api/incidents');
                incidentsData = await response.json();
                renderIncidents();
                updateIncidentsCount();
            } catch(e) { console.error(e); }
        }

        function updateIncidentsCount() {
            const el = document.querySelector('#tab-dashboard .hero-stat-value[style*="var(--warning)"]');
            if (el) {
                el.textContent = incidentsData.length;
            }
        }

        function renderIncidents() {
            const list = document.getElementById('incidentsList');
            if (!list) return;
            
            if (incidentsData.length === 0) {
                list.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-secondary);">Немає інцидентів - всі монітори працюють!</div>';
                return;
            }
            
            let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
            incidentsData.forEach(inc => {
                const date = new Date(inc.checked_at).toLocaleString('uk-UA');
                html += `
                <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid var(--danger); padding: 12px 16px; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: var(--danger);">${inc.site_name}</span>
                        <span style="font-size: 12px; color: var(--text-secondary);">${date}</span>
                    </div>
                    <div style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">
                        Код: ${inc.status_code} | Час: ${inc.response_time ? Math.round(inc.response_time) + 'ms' : '—'}
                    </div>
                    ${inc.error_message ? `<div style="font-size: 12px; color: var(--warning); margin-top: 4px;">${inc.error_message}</div>` : ''}
                </div>`;
            });
            html += '</div>';
            list.innerHTML = html;
        }

        async function checkAllMonitors() {
            try {
                for (const site of sitesData) {
                    await fetch(`/api/sites/${site.id}/check`, { method: 'POST' });
                }
                loadSites();
            } catch(e) { console.error(e); }
        }

        function initNotifyUI() {
            ['telegram', 'teams', 'discord', 'slack', 'email', 'sms'].forEach(method => {
                const config = notifyConfig[method] || {};
                const card = document.getElementById('card-' + method);
                const toggle = document.getElementById('toggle-' + method);
                if (!card || !toggle) return;
                if (config.enabled) {
                    card.classList.add('enabled');
                    toggle.checked = true;
                }
                const fields = card.querySelectorAll('input[type="text"], input[type="password"]');
                fields.forEach(input => {
                    const fieldName = input.id.replace(method + '-', '').replace(/-/g, '_');
                    if (config[fieldName] !== undefined) input.value = config[fieldName];
                });
            });
        }

        function toggleNotify(method) {
            const card = document.getElementById('card-' + method);
            const toggle = document.getElementById('toggle-' + method);
            if (!card || !toggle) return;
            if (toggle.checked) card.classList.add('enabled');
            else card.classList.remove('enabled');
        }

        async function saveNotifySettings() {
            const settings = {
                telegram: { enabled: document.getElementById('toggle-telegram')?.checked, token: document.getElementById('telegram-token')?.value, chat_id: document.getElementById('telegram-chat_id')?.value },
                teams: { enabled: document.getElementById('toggle-teams')?.checked, webhook_url: document.getElementById('teams-webhook_url')?.value },
                discord: { enabled: document.getElementById('toggle-discord')?.checked, webhook_url: document.getElementById('discord-webhook_url')?.value },
                slack: { enabled: document.getElementById('toggle-slack')?.checked, webhook_url: document.getElementById('slack-webhook_url')?.value },
                email: { enabled: document.getElementById('toggle-email')?.checked, smtp_server: document.getElementById('email-smtp_server')?.value, smtp_port: parseInt(document.getElementById('email-smtp_port')?.value) || 587, username: document.getElementById('email-username')?.value, password: document.getElementById('email-password')?.value, to_email: document.getElementById('email-to_email')?.value },
            };
            try {
                await fetch('/api/notify-settings', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(settings) });
                alert('✅ Налаштування збережено!');
            } catch(e) { console.error(e); }
        }

        async function loadAppSettings() {
            try {
                const response = await fetch('/api/app-settings');
                const data = await response.json();
                const el = document.getElementById('displayAddress');
                if (el) el.value = data.display_address || '';
            } catch(e) { /* ignore */ }
        }

        async function saveAddress() {
            const addr = document.getElementById('displayAddress')?.value || '';
            try {
                await fetch('/api/app-settings', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({display_address: addr}) });
                alert('✅ Адресу збережено!');
            } catch(e) { console.error(e); }
        }

        function openEditModal(id, name, url, notifyMethods) {
            document.getElementById('editSiteId').value = id;
            document.getElementById('editSiteName').value = decodeURIComponent(name);
            document.getElementById('editSiteUrl').value = decodeURIComponent(url);
            const select = document.getElementById('editSiteNotify');
            if (select) Array.from(select.options).forEach(opt => { opt.selected = notifyMethods.includes(opt.value); });
            document.getElementById('editModal').classList.add('active');
        }

        function closeEditModal() {
            document.getElementById('editModal').classList.remove('active');
        }

        async function saveEdit() {
            const id = document.getElementById('editSiteId').value;
            const name = document.getElementById('editSiteName').value.trim();
            const url = document.getElementById('editSiteUrl').value.trim();
            const select = document.getElementById('editSiteNotify');
            const notify_methods = select ? Array.from(select.selectedOptions).map(o => o.value) : [];
            if (!name || !url) return alert('Заповніть всі поля!');
            try {
                await fetch(`/api/sites/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, url, notify_methods}) });
                closeEditModal();
                loadSites();
            } catch(e) { console.error(e); }
        }

        async function checkSSLCertificates() {
            try {
                await fetch('/api/ssl-certificates/check', { method: 'POST' });
                loadSSLCertificates();
            } catch(e) { console.error(e); }
        }
"""


def get_notification_cards_html(config):
    methods = [
        ("telegram", "📱", "Telegram", "Миттєві сповіщення", ["token", "chat_id"]),
        ("teams", "🏢", "MS Teams", "Робочі групи", ["webhook_url"]),
        ("discord", "🎮", "Discord", "Геймерські спільноти", ["webhook_url"]),
        ("slack", "💬", "Slack", "Корпоративний чат", ["webhook_url"]),
        (
            "email",
            "📧",
            "Email",
            "Електронна пошта",
            ["smtp_server", "smtp_port", "username", "password", "to_email"],
        ),
    ]

    html = ""
    for key, icon, name, desc, fields in methods:
        enabled = config.get(key, {}).get("enabled", False)
        enabled_class = "enabled" if enabled else ""
        checked = "checked" if enabled else ""

        card = f"""
        <div class="notify-card {enabled_class}" id="card-{key}">
            <div class="notify-header">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:24px;">{icon}</span>
                    <div><div style="font-weight:600;">{name}</div><div style="font-size:12px; color:var(--text-secondary);">{desc}</div></div>
                </div>
                <label class="toggle">
                    <input type="checkbox" id="toggle-{key}" onchange="toggleNotify('{key}')" {checked}>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            <div class="notify-fields">"""

        for field in fields:
            val = config.get(key, {}).get(field, "")
            card += f'<input type="text" id="{key}-{field}" placeholder="{field}" value="{val}">'

        card += "</div></div>"
        html += card
    return html


def get_dashboard_html(
    total_sites, up_sites, down_sites, notify_config_json, notification_cards
):
    return DASHBOARD_HTML.format(
        total_sites=total_sites,
        up_sites=up_sites,
        down_sites=down_sites,
        notify_config_json=notify_config_json,
        notification_cards=notification_cards,
        js_functions=DASHBOARD_JS,
    )


def get_public_status_html(
    overall_status_class,
    overall_status_text,
    total,
    up_count,
    down_count,
    monitors_html,
    timestamp,
):
    return PUBLIC_STATUS_HTML.format(
        overall_status_class=overall_status_class,
        overall_status_text=overall_status_text,
        total=total,
        up_count=up_count,
        down_count=down_count,
        monitors_html=monitors_html,
        timestamp=timestamp,
    )
