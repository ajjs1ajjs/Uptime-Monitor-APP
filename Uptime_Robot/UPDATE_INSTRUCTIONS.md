# Оновлення Uptime Monitor на продакшені

## Варіант 1: Git (якщо є .git)

```bash
# 1. Зупинити службу
sudo systemctl stop uptime-monitor

# 2. Бекап бази
sudo cp /etc/uptime-monitor/sites.db /backup/sites_$(date +%Y%m%d).db

# 3. Оновити
cd /opt/uptime-monitor
sudo git pull

# 4. Запустити
sudo systemctl start uptime-monitor

# 5. Перевірити
sudo systemctl status uptime-monitor
```

## Варіант 2: wget (якщо немає git)

```bash
# 1. Зупинити
sudo systemctl stop uptime-monitor

# 2. Бекап
sudo cp /etc/uptime-monitor/sites.db /backup/sites_$(date +%Y%m%d).db

# 3. Скачати нові файли
cd /opt/uptime-monitor

# Видалити старі дублікати якщо є
sudo rm -f *.py.1 *.py.2

# Скачати нові
sudo wget -q https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/config_manager.py
sudo wget -q https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/ui_templates.py
sudo wget -q https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/notifications.py
sudo wget -q https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/monitoring.py
sudo wget -q https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/main.py

# 4. Перевірити розмір файлів (має бути > 10000 bytes)
ls -la *.py

# 5. Запустити
sudo systemctl start uptime-monitor

# 6. Перевірити
sudo systemctl status uptime-monitor
```

## Перевірка оновлення

Після оновлення в браузері:
- Очистити кеш: Ctrl+Shift+R
- Або відкрити в інкогніто

## Розміри файлів (актуальні):

| Файл | Розмір |
|------|---------|
| main.py | ~25500 |
| ui_templates.py | ~84300 |
| notifications.py | ~20000 |
| monitoring.py | ~10900 |
| config_manager.py | ~9400 |

## Якщо щось пішло не так

```bash
# Відкатити до бекапу
sudo systemctl stop uptime-monitor
sudo cp /backup/sites_YYYYMMDD.db /etc/uptime-monitor/sites.db
sudo systemctl start uptime-monitor
```
