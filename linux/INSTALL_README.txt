UPTIME MONITOR - INSTALLATION GUIDE
====================================

Choose your installation method:


OPTION 1: WINDOWS SERVICE (Recommended - Like Windows Exporter)
===============================================================
Best for: Production servers, runs 24/7, auto-restart on crash

1. Install as Service (needs Python + Admin rights):
   Run: INSTALL_SERVICE_NSSM.bat
   - Auto-downloads NSSM (service wrapper)
   - Creates Windows Service
   - Auto-starts on Windows boot
   - Auto-restarts on crash

2. Manage service:
   nssm start UptimeMonitor
   nssm stop UptimeMonitor
   nssm restart UptimeMonitor
   nssm remove UptimeMonitor

3. Access: http://localhost:8000


OPTION 2: STANDALONE EXE (No Python needed on target)
====================================================
Best for: Copy to any PC, no dependencies

1. Build EXE first:
   Run: build_windows_service.bat
   (Creates UptimeMonitor_Service\ folder)

2. Copy folder to target PC

3. On target PC run as Admin:
   INSTALL.bat

4. Service auto-runs forever!


OPTION 3: MANUAL START (Development/Testing)
=============================================
Best for: Testing, development

1. Run: START.bat
2. Enter port
3. Press Ctrl+C to stop

No service, no auto-start.


OPTION 4: AUTO-START (No service, runs on login)
================================================
Best for: Personal use, starts with Windows

1. Run: SETUP_AUTO.bat
2. Enters startup registry
3. To disable: Task Manager - Startup tab


FEATURES AVAILABLE IN ALL VERSIONS:
===================================
✅ Website uptime monitoring
✅ Response time tracking
✅ SSL certificate expiration alerts
   - 14 days before expiry: daily alerts
   - 7 days: urgent alerts
   - 3 days: critical alerts
   - Expired: immediate alerts
✅ Multi-channel notifications:
   - Telegram
   - Email (SMTP)
   - More in web interface
✅ Auto-restart on crash (service mode)
✅ Auto-start on Windows boot


WEB INTERFACE:
==============
After installation, open browser:
http://localhost:8000 (or your port)

Functionality:
- Add/remove websites to monitor
- Configure notifications (Telegram, Email)
- View uptime statistics
- View SSL certificate status
- Manual check trigger
- Real-time updates


NOTIFICATION SETUP:
==================
1. Open web interface
2. Go to "Notification Settings"
3. Enable desired channels:
   
   Telegram:
   - Get Bot Token from @BotFather
   - Get Chat ID (message @userinfobot)
   
   Email:
   - SMTP server (e.g., smtp.gmail.com)
   - Port (usually 587)
   - Username/Password
   - Recipient email

4. Click "Save"

5. Add website and select notification methods


SSL CERTIFICATE MONITORING:
==========================
Automatic for all HTTPS sites:
- Checks once per day
- Alerts start 14 days before expiry
- Daily reminders until renewed
- Severity levels:
  🟡 8-14 days: Warning
  🟠 4-7 days: Important
  🔴 0-3 days: Critical
  🔴 Expired: Immediate


TROUBLESHOOTING:
===============
Port already in use:
  - Choose different port (8080, 3000, etc.)
  - Or stop other application

Service won't start:
  - Check service.log file
  - Ensure Python is in PATH
  - Run as Administrator

Can't access from network:
  - Check Windows Firewall
  - Verify port is open
  - Use IP address, not localhost

Python not found:
  - Install from python.org
  - Check "Add to PATH" during install


FILES IN THIS PACKAGE:
=====================
main_service.py           - Main application with service support
main.py                   - Original version
ssl_checker.py            - SSL certificate checking
INSTALL_SERVICE_NSSM.bat  - Install as Windows Service (Option 1)
build_windows_service.bat - Build standalone EXE (Option 2)
START.bat                 - Manual start (Option 3)
SETUP_AUTO.bat            - Auto-start on login (Option 4)
README.txt                - This file


PORTABLE VERSION:
================
To create for distribution:
1. Run: build_windows_service.bat
2. Copy UptimeMonitor_Service\ folder
3. Distribute to any PC
4. On target PC run INSTALL.bat as Admin

No Python required on target PC!


SUPPORT:
========
- Check service.log for errors
- Ensure all dependencies installed
- Run as Administrator for service install
- Open firewall ports if needed


---
Uptime Monitor - Keep your sites online!
