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

**Note:** After installation, the server will be accessible at `http://{SERVER_IP}:8080` where `{SERVER_IP}` is automatically detected.

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
    "server": {
        "port": 8080,
        "host": "0.0.0.0",
        "domain": "auto"
    },
    "ssl": {
        "enabled": false,
        "type": "custom",
        "cert_path": "/etc/uptime-monitor/ssl/cert.pem",
        "key_path": "/etc/uptime-monitor/ssl/key.pem",
        "redirect_http": true,
        "hsts": true,
        "hsts_max_age": 31536000
    },
    "data_dir": "/var/lib/uptime-monitor",
    "log_dir": "/var/log/uptime-monitor",
    "check_interval": 60,
    "notifications": {
        "email_enabled": false,
        "email_smtp_server": "",
        "email_smtp_port": 587,
        "email_username": "",
        "email_password": "",
        "email_to": ""
    },
    "backup": {
        "enabled": true,
        "max_backups": 10,
        "backup_dir": "/etc/uptime-monitor/config.backups"
    }
}
```

**Configuration Parameters:**

- `server.port` - Port number (default: 8080)
- `server.host` - Bind address (default: 0.0.0.0 - all interfaces)
- `server.domain` - Server domain or IP (default: "auto" - auto-detect IP)
- `ssl.enabled` - Enable HTTPS (default: false)
- `ssl.type` - Certificate type: "custom", "selfsigned", "letsencrypt"
- `ssl.cert_path` - Path to SSL certificate
- `ssl.key_path` - Path to SSL private key
- `backup.enabled` - Enable automatic backups (default: true)
- `backup.max_backups` - Number of backups to keep (default: 10)

### Windows Configuration File

Location: `%USERPROFILE%\UptimeMonitor\config.json`

## Configuration Management

### Editing Configuration

**Linux:**
```bash
# Edit configuration
sudo nano /etc/uptime-monitor/config.json

# Restart service to apply changes
sudo systemctl restart uptime-monitor

# Check status
sudo systemctl status uptime-monitor
```

### Configuration Rollback

Automatic backups are created before each configuration change.

**List available backups:**
```bash
sudo /opt/uptime-monitor/scripts/config-rollback.sh --list
```

**Rollback to previous configuration:**
```bash
sudo /opt/uptime-monitor/scripts/config-rollback.sh --previous
```

**Rollback to specific backup:**
```bash
sudo /opt/uptime-monitor/scripts/config-rollback.sh --to config.20260218-120000.json
```

**View differences:**
```bash
sudo /opt/uptime-monitor/scripts/config-rollback.sh --diff config.latest.json
```

## SSL/HTTPS Setup

### Option 1: Using Your Own Certificates (Recommended)

**Step 1:** Copy your certificates to the SSL directory:
```bash
sudo mkdir -p /etc/uptime-monitor/ssl
sudo cp /path/to/your/certificate.pem /etc/uptime-monitor/ssl/cert.pem
sudo cp /path/to/your/private.key /etc/uptime-monitor/ssl/key.pem
sudo chmod 600 /etc/uptime-monitor/ssl/*.pem
```

**Step 2:** Update configuration:
```bash
sudo nano /etc/uptime-monitor/config.json
```

Change the following settings:
```json
{
    "server": {
        "port": 443,
        "domain": "your-domain.com"
    },
    "ssl": {
        "enabled": true,
        "type": "custom",
        "cert_path": "/etc/uptime-monitor/ssl/cert.pem",
        "key_path": "/etc/uptime-monitor/ssl/key.pem"
    }
}
```

**Step 3:** Restart service:
```bash
sudo systemctl restart uptime-monitor
```

### Option 2: Self-Signed Certificate (Testing Only)

```bash
# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/uptime-monitor/ssl/key.pem \
  -out /etc/uptime-monitor/ssl/cert.pem \
  -subj "/CN=localhost"

# Update config and restart
sudo nano /etc/uptime-monitor/config.json
sudo systemctl restart uptime-monitor
```

**Warning:** Browsers will show security warnings with self-signed certificates.

## Domain and IP Configuration

### Automatic IP Detection

By default, the server auto-detects the server's IP address:
```json
{
    "server": {
        "domain": "auto"
    }
}
```

### Using Specific IP

```bash
# Get your server IP
hostname -I

# Edit config
sudo nano /etc/uptime-monitor/config.json
```

Set domain to your IP:
```json
{
    "server": {
        "domain": "192.168.1.100"
    }
}
```

### Using Domain Name

**Step 1:** Configure DNS A-record pointing to your server IP

**Step 2:** Update configuration:
```json
{
    "server": {
        "domain": "monitor.yourdomain.com"
    }
}
```

**Step 3:** Restart service:
```bash
sudo systemctl restart uptime-monitor
```

## API Endpoints

- `GET /` - Web interface
- `GET /api/sites` - List all sites
- `POST /api/sites` - Add site
- `PUT /api/sites/{id}` - Update site
- `DELETE /api/sites/{id}` - Delete site
- `POST /api/sites/{id}/check` - Check site manually
- `POST /api/notify-settings` - Save notification settings

## Accessing the Web Interface

**Initial Setup (after installation):**
- **Linux:** `http://<server-ip>:8080` (IP auto-detected during installation)
- **Windows:** `http://localhost:8000` or `http://<your-ip>:8000`

**After SSL configuration:**
- **HTTPS:** `https://your-domain.com` (port 443)

**To check your server IP:**
```bash
hostname -I
```

## Technical Details

- **Framework:** FastAPI
- **Database:** SQLite
- **HTTP Client:** aiohttp
- **Windows Service:** pywin32
- **Linux Service:** systemd
- **Default Port:** 8080 (Linux) / 8000 (Windows)
- **SSL Support:** Yes (custom certificates, self-signed, Let's Encrypt ready)
- **Configuration:** JSON-based with automatic backup/rollback
- **Check Interval:** 60 seconds
- **Configuration File:** `/etc/uptime-monitor/config.json` (Linux)
- **Backup Directory:** `/etc/uptime-monitor/config.backups` (Linux)

## Support

For issues and questions, please open an issue on GitHub:
https://github.com/ajjs1ajjs/Uptime-Monitor-APP/issues