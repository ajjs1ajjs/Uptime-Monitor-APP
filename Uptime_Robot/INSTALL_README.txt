UPTIME MONITOR - INSTALL, BACKUP, UPDATE, TROUBLESHOOT GUIDE
=============================================================

Quick operational guide for Linux/WSL.

Main docs:
- ../INSTALL.md
- ../docs/QUICKSTART.md
- ../docs/COMMANDS.md
- ../docs/TROUBLESHOOTING.md
- ../docs/BACKUP.md


1) Fresh install (recommended)
------------------------------

curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash

Verify:
sudo systemctl status uptime-monitor --no-pager
sudo journalctl -u uptime-monitor -n 80 --no-pager

Access:
- URL: http://<SERVER_IP>:8080
- Login: admin
- Password: admin

Important: change password after first login.


2) Clean reinstall (remove old install)
---------------------------------------

Use this when old UI/old behavior still appears.

sudo systemctl stop uptime-monitor 2>/dev/null || true
sudo systemctl disable uptime-monitor 2>/dev/null || true
sudo rm -f /etc/systemd/system/uptime-monitor.service
sudo systemctl daemon-reload
sudo rm -rf /opt/uptime-monitor /etc/uptime-monitor /var/lib/uptime-monitor /var/log/uptime-monitor

curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash


3) Backup (mandatory)
---------------------

Create first backup:
sudo /opt/uptime-monitor/scripts/backup-system.sh --dest /backup/uptime-monitor/

Schedule automatic backups:
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --install --dest /backup/uptime-monitor/

Check backup system:
sudo /opt/uptime-monitor/scripts/backup-system.sh --status
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --status

Verify backups:
sudo /opt/uptime-monitor/scripts/verify-backup.sh --all


4) Restore
----------

List backups:
sudo /opt/uptime-monitor/scripts/restore-system.sh --list

Restore latest backup:
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto

Restore specific backup:
sudo /opt/uptime-monitor/scripts/restore-system.sh --from /backup/uptime-monitor/daily/<backup-file>.tar.gz


5) Update existing installation
-------------------------------

5.1 Git installation (.git exists)

cd /opt/uptime-monitor
sudo systemctl stop uptime-monitor
sudo git fetch --all --prune
sudo git checkout main
sudo git pull --ff-only origin main
sudo systemctl start uptime-monitor

5.2 Non-git installation (no .git)

cd /opt/uptime-monitor
sudo systemctl stop uptime-monitor
sudo wget -O main.py         "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/main.py"
sudo wget -O models.py       "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/models.py"
sudo wget -O monitoring.py   "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/monitoring.py"
sudo wget -O ui_templates.py "https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/Uptime_Robot/ui_templates.py"
sudo systemctl start uptime-monitor

Verify after update:
sudo systemctl status uptime-monitor --no-pager
sudo journalctl -u uptime-monitor -n 80 --no-pager


6) Quick checks (UI + API + auth)
---------------------------------

Check new UI markers in installed code:
grep -n "Monitors Timeline (24h)" /opt/uptime-monitor/ui_templates.py
grep -n "Статус всіх моніторів" /opt/uptime-monitor/ui_templates.py
grep -n "Історія інцидентів" /opt/uptime-monitor/ui_templates.py
grep -n "Глобальні налаштування сповіщень" /opt/uptime-monitor/ui_templates.py

Basic HTTP check:
curl -sS -o /dev/null -w "GET /login -> HTTP %{http_code}\n" http://127.0.0.1:8080/login

If admin/admin does not work:
curl -X POST -d "username=admin" http://127.0.0.1:8080/forgot-password


7) Troubleshooting
------------------

Service not starting:
sudo journalctl -u uptime-monitor -n 200 --no-pager
sudo systemctl status uptime-monitor --no-pager

Wrong/old UI after update:
1. Run clean reinstall section.
2. Clear browser cache (hard reload).
3. Re-check UI markers in /opt/uptime-monitor/ui_templates.py.

Cannot login:
1. Reset admin password with forgot-password endpoint.
2. Check auth tables and DB file in /etc/uptime-monitor/sites.db.
3. Restart service.

Port busy:
sudo ss -ltnp | grep :8080 || true


8) Useful commands
------------------

Start/stop/restart/status:
sudo systemctl start uptime-monitor
sudo systemctl stop uptime-monitor
sudo systemctl restart uptime-monitor
sudo systemctl status uptime-monitor --no-pager

Logs:
sudo journalctl -u uptime-monitor -f
sudo journalctl -u uptime-monitor -n 100 --no-pager

Config:
sudo nano /etc/uptime-monitor/config.json
sudo systemctl restart uptime-monitor

