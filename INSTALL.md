# Uptime Monitor - Installation Guide

## Linux Installation via CURL

### Install Latest Version
```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash
```

### Install with Custom Port
```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --port 9090
```

### Install Specific Version
```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --version v1.0.0
```

## Linux Installation via APT

### Add Repository
```bash
curl -fsSL https://ajjs1ajjs.github.io/Uptime-Monitor-APP/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/uptime-monitor.gpg
echo "deb [signed-by=/usr/share/keyrings/uptime-monitor.gpg] https://ajjs1ajjs.github.io/Uptime-Monitor-APP stable main" | sudo tee /etc/apt/sources.list.d/uptime-monitor.list
```

### Install
```bash
sudo apt update && sudo apt install uptime-monitor
```

### Start Service
```bash
sudo systemctl start uptime-monitor
```

## Windows Installation

### Method 1: Simple Installation
1. Download `uptime-monitor-vX.X.X-windows.zip` from [Releases](https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases)
2. Extract to desired location
3. Run `install.bat` as Administrator

### Method 2: Manual Installation
```cmd
cd C:\path\to\Uptime-Monitor-APP
pip install -r requirements.txt
python main.py --port 8080
```

## Docker Installation

```bash
docker run -d -p 8080:8080 -v uptime-data:/var/lib/uptime-monitor ghcr.io/ajjs1ajjs/uptime-monitor:latest
```

## Default Credentials

- **Username:** `admin`
- **Password:** `admin`

**Change password after first login!**

## Management Commands

### Linux (systemd)

```bash
# Check status
sudo systemctl status uptime-monitor

# Start service
sudo systemctl start uptime-monitor

# Stop service
sudo systemctl stop uptime-monitor

# Restart service
sudo systemctl restart uptime-monitor

# Enable on boot
sudo systemctl enable uptime-monitor

# Disable on boot
sudo systemctl disable uptime-monitor

# View logs
sudo journalctl -u uptime-monitor -f

# View last 50 lines
sudo journalctl -u uptime-monitor -n 50
```

### Windows (Service)

```cmd
# Check status
sc query UptimeMonitor

# Start service
net start UptimeMonitor

# Stop service
net stop UptimeMonitor

# Restart service
net stop UptimeMonitor && net start UptimeMonitor

# Disable on boot
sc config UptimeMonitor start= disabled

# Enable on boot
sc config UptimeMonitor start= auto
```

## Uninstallation

### Linux (via install.sh)

```bash
# Stop service
sudo systemctl stop uptime-monitor

# Disable service
sudo systemctl disable uptime-monitor

# Remove systemd service file
sudo rm /etc/systemd/system/uptime-monitor.service

# Reload systemd
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/uptime-monitor

# Remove user (optional)
sudo userdel uptime-monitor
```

### Linux (via APT)

```bash
# Stop service
sudo systemctl stop uptime-monitor

# Disable service
sudo systemctl disable uptime-monitor

# Uninstall package
sudo apt remove --purge uptime-monitor

# Remove repository
sudo rm /etc/apt/sources.list.d/uptime-monitor.list
sudo rm /usr/share/keyrings/uptime-monitor.gpg

# Update package list
sudo apt update
```

### Windows (via installer)

1. Open "Settings" -> "Apps" -> "Installed apps"
2. Find "Uptime Monitor"
3. Click "Uninstall"

### Windows (manual)

```cmd
# Stop service
net stop UptimeMonitor

# Delete service
sc delete UptimeMonitor

# Remove application files
rd /s /q "C:\Program Files\UptimeMonitor"
rd /s /q "%USERPROFILE%\UptimeMonitor"
```

## Troubleshooting

### Port Already in Use

**Linux:**
```bash
# Find process using port
sudo lsof -i :8080

# Kill process
sudo kill -9 <PID>
```

**Windows:**
```cmd
# Find process using port
netstat -ano | findstr :8080

# Kill process
taskkill /PID <PID> /F
```

### Service Won't Start

**Linux:**
```bash
# Check logs
sudo journalctl -u uptime-monitor -n 50

# Check permissions
ls -la /opt/uptime-monitor

# Check Python version
python3 --version
```

**Windows:**
```cmd
# Check logs
type "%USERPROFILE%\UptimeMonitor\uptime_monitor.log"

# Check if running as admin
whoami /priv
```

### Notifications Not Working

1. Check if notifications are enabled in web interface
2. Verify API keys are correct
3. Check logs for errors:
   ```bash
   sudo journalctl -u uptime-monitor -f
   ```
   ```cmd
   type "%USERPROFILE%\UptimeMonitor\uptime_monitor.log"
   ```

## Configuration

### Linux Configuration File

Location: `/etc/uptime-monitor/config.json`

```json
{
    "port": 8080,
    "host": "0.0.0.0",
    "data_dir": "/var/lib/uptime-monitor",
    "log_dir": "/var/log/uptime-monitor",
    "check_interval": 60,

    "notify_email_enabled": false,
    "notify_email_smtp_server": "",
    "notify_email_smtp_port": 587,
    "notify_email_username": "",
    "notify_email_password": "",
    "notify_email_to": ""
}
```

### Windows Configuration File

Location: `%USERPROFILE%\UptimeMonitor\config.json`

## API Endpoints

- `GET /` - Web interface
- `GET /api/sites` - List all sites
- `POST /api/sites` - Add site
- `PUT /api/sites/{id}` - Update site
- `DELETE /api/sites/{id}` - Delete site
- `POST /api/sites/{id}/check` - Check site manually
- `POST /api/notify-settings` - Save notification settings

## Accessing the Web Interface

- **Linux:** `http://localhost:8080` or `http://<your-ip>:8080`
- **Windows:** `http://localhost:8000` or `http://<your-ip>:8000`

## Technical Details

- **Framework:** FastAPI
- **Database:** SQLite
- **HTTP Client:** aiohttp
- **Windows Service:** pywin32
- **Linux Service:** systemd
- **Default Port:** 8000 (Windows) / 8080 (Linux)
- **Check Interval:** 60 seconds

## Support

For issues and questions, please open an issue on GitHub:
https://github.com/ajjs1ajjs/Uptime-Monitor-APP/issues