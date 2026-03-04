# Оновлення Uptime Monitor на продакшені

Нижче два коректні сценарії: для git clone і для встановлення без `.git`.

## Крок 0: Перевірити тип інсталяції

```bash
cd /opt/uptime-monitor
if [ -d .git ]; then
  echo "git installation"
else
  echo "non-git installation"
fi
```

## Варіант 1: Git (якщо є `.git`)

```bash
# 1) Stop service
sudo systemctl stop uptime-monitor

# 2) Backup database
DB_PATH=$(python3 - <<'PY'
import json, os
config='/etc/uptime-monitor/config.json'
if os.path.exists(config):
    try:
        with open(config,'r',encoding='utf-8') as f:
            data=json.load(f)
        print(os.path.join(os.path.dirname(config), 'sites.db'))
    except Exception:
        print('/etc/uptime-monitor/sites.db')
else:
    print('/etc/uptime-monitor/sites.db')
PY
)
sudo cp "$DB_PATH" "/backup/sites_$(date +%Y%m%d-%H%M%S).db"

# 3) Update code
cd /opt/uptime-monitor
sudo git fetch --all --prune
sudo git checkout main
sudo git pull --ff-only origin main

# 4) Start service
sudo systemctl start uptime-monitor

# 5) Verify
sudo systemctl status uptime-monitor --no-pager
sudo journalctl -u uptime-monitor -n 80 --no-pager
```

## Варіант 2: wget (якщо немає `.git`)

```bash
# 1) Stop service
sudo systemctl stop uptime-monitor

# 2) Backup database
DB_PATH=$(python3 - <<'PY'
import json, os
config='/etc/uptime-monitor/config.json'
if os.path.exists(config):
    try:
        with open(config,'r',encoding='utf-8') as f:
            data=json.load(f)
        print(os.path.join(os.path.dirname(config), 'sites.db'))
    except Exception:
        print('/etc/uptime-monitor/sites.db')
else:
    print('/etc/uptime-monitor/sites.db')
PY
)
sudo cp "$DB_PATH" "/backup/sites_$(date +%Y%m%d-%H%M%S).db"

# 3) Download updated files from main
cd /opt/uptime-monitor
sudo wget -O main.py         "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/main.py"
sudo wget -O models.py       "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/models.py"
sudo wget -O monitoring.py   "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/monitoring.py"
sudo wget -O ui_templates.py "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/ui_templates.py"
sudo wget -O page.html       "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/page.html"

# 4) Start service
sudo systemctl start uptime-monitor

# 5) Verify
sudo systemctl status uptime-monitor --no-pager
sudo journalctl -u uptime-monitor -n 80 --no-pager
```

## Точна перевірка, що оновлення застосувалось

```bash
cd /opt/uptime-monitor
grep -n "_normalize_and_validate_url" main.py
grep -n "idx_ssl_certificates_site_id_unique" models.py
grep -n "UPDATE ssl_certificates SET" monitoring.py
grep -n "WHERE s.is_active = 1" models.py
```

## Якщо щось пішло не так

```bash
sudo systemctl stop uptime-monitor
# вибери потрібний backup файл у /backup/
sudo cp /backup/sites_YYYYMMDD-HHMMSS.db /etc/uptime-monitor/sites.db
sudo systemctl start uptime-monitor
```

## Windows (окремий сценарій)

```powershell
# 1) Backup data
Copy-Item "$env:USERPROFILE\UptimeMonitor\sites.db" "$env:USERPROFILE\UptimeMonitor\sites.db.backup.$(Get-Date -Format yyyyMMdd-HHmmss)"
Copy-Item "$env:USERPROFILE\UptimeMonitor\config.json" "$env:USERPROFILE\UptimeMonitor\config.json.backup.$(Get-Date -Format yyyyMMdd-HHmmss)"

# 2) Update files
# If git clone:
cd D:\path\to\Uptime-Monitor-APP
git pull --ff-only origin main

# If release ZIP:
# Download and extract latest Windows ZIP from:
# https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases

# 3) Reinstall service from updated folder
cd D:\path\to\Uptime-Monitor-APP\Uptime_Robot
python main_service.py stop
python main_service.py remove
.\install.bat

# 4) Verify service and port
sc.exe queryex UptimeMonitor
netstat -ano | findstr :8080
```
