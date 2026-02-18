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

## Backup System

Uptime Monitor includes a comprehensive backup system that supports local storage, NFS, and Samba shares.

### Quick Start

**Create your first backup:**
```bash
sudo /opt/uptime-monitor/scripts/backup-system.sh --dest /backup/uptime-monitor/ --type daily
```

**Check backup status:**
```bash
sudo /opt/uptime-monitor/scripts/backup-system.sh --status
```

**List available backups:**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh --list
```

**Restore from latest backup:**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto
```

### What Gets Backed Up

- **Database**: SQLite database with all sites and monitoring data
- **Configuration**: config.json and configuration history
- **SSL Certificates**: Your SSL certificates and keys
- **Logs**: Recent log files (last 7 days)
- **Systemd Service**: Service configuration file

### Backup Types

| Type | When | Retention |
|------|------|-----------|
| on-change | After config changes | 10 backups |
| daily | Every day at 2:00 AM | 7 days |
| weekly | Every Sunday at 3:00 AM | All (kept until monthly) |
| monthly | 1st of month at 4:00 AM | All (kept until yearly) |
| yearly | January 1st at 5:00 AM | Forever |

### Manual Backup

**Create immediate backup:**
```bash
sudo /opt/uptime-monitor/scripts/backup-system.sh --dest /backup/uptime-monitor/
```

**Create backup with comment:**
```bash
sudo /opt/uptime-monitor/scripts/backup-system.sh \
    --dest /backup/uptime-monitor/ \
    --type on-change \
    --comment "Before major config change"
```

**Verify backup integrity:**
```bash
sudo /opt/uptime-monitor/scripts/backup-system.sh --verify --dest /backup/uptime-monitor/
```

### Scheduled Backups (Automatic)

**Install daily backups:**
```bash
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --install \
    --daily "0 2 * * *" \
    --dest /backup/uptime-monitor/
```

**Install with full schedule:**
```bash
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --install \
    --daily "0 2 * * *" \
    --weekly "0 3 * * 0" \
    --monthly "0 4 1 * *" \
    --dest /backup/uptime-monitor/
```

**Check schedule status:**
```bash
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --status
```

**Remove all schedules:**
```bash
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --remove
```

**Test backup system:**
```bash
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --test
```

### NFS Backup Setup

**1. Install NFS client:**
```bash
sudo apt-get update
sudo apt-get install -y nfs-common
```

**2. Mount NFS share:**
```bash
sudo /opt/uptime-monitor/scripts/mount-backup.sh \
    --type nfs \
    --server 192.168.1.10 \
    --path /exports/backups \
    --mount-point /mnt/nfs-backup \
    --persist
```

**3. Create backup to NFS:**
```bash
sudo /opt/uptime-monitor/scripts/backup-system.sh \
    --dest /mnt/nfs-backup/uptime-monitor/ \
    --type daily
```

**4. Schedule automatic NFS backups:**
```bash
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --install \
    --daily "0 2 * * *" \
    --dest /mnt/nfs-backup/uptime-monitor/
```

**Manual NFS mount (alternative):**
```bash
# Create mount point
sudo mkdir -p /mnt/nfs-backup

# Mount
sudo mount -t nfs 192.168.1.10:/exports/backups /mnt/nfs-backup

# Add to /etc/fstab for persistence
echo "192.168.1.10:/exports/backups /mnt/nfs-backup nfs defaults 0 0" | sudo tee -a /etc/fstab
```

### Samba (SMB) Backup Setup

**1. Install Samba client:**
```bash
sudo apt-get update
sudo apt-get install -y cifs-utils
```

**2. Create credentials file:**
```bash
sudo mkdir -p /root/.backup-creds
sudo tee /root/.backup-creds/smb-credentials << EOF
username=backupuser
password=yourpassword
domain=WORKGROUP
EOF
sudo chmod 600 /root/.backup-creds/smb-credentials
```

**3. Mount Samba share:**
```bash
sudo /opt/uptime-monitor/scripts/mount-backup.sh \
    --type smb \
    --server 192.168.1.11 \
    --share backups \
    --mount-point /mnt/smb-backup \
    --credentials /root/.backup-creds/smb-credentials \
    --persist
```

**4. Create backup to Samba:**
```bash
sudo /opt/uptime-monitor/scripts/backup-system.sh \
    --dest /mnt/smb-backup/uptime-monitor/ \
    --type daily
```

**Manual Samba mount (alternative):**
```bash
# Create mount point
sudo mkdir -p /mnt/smb-backup

# Mount
sudo mount -t cifs //192.168.1.11/backups /mnt/smb-backup \
    -o credentials=/root/.backup-creds/smb-credentials

# Add to /etc/fstab
echo "//192.168.1.11/backups /mnt/smb-backup cifs credentials=/root/.backup-creds/smb-credentials,_netdev 0 0" | sudo tee -a /etc/fstab
```

### Using Both NFS and Samba

You can use multiple backup destinations simultaneously:

```bash
# Install schedule for both
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --install \
    --daily "0 2 * * *" \
    --dest /backup/uptime-monitor/ \
    --enable-nfs

# This will backup to:
# 1. /backup/uptime-monitor/ (local)
# 2. /mnt/nfs-backup/uptime-monitor/ (NFS)
```

### Restore from Backup

**List available backups:**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh --list
```

**Restore from latest backup:**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto
```

**Restore from specific backup:**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh \
    --from /backup/uptime-monitor/daily/backup-20260218-020000.tar.gz
```

**Restore only database:**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto --only database
```

**Restore only configuration:**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto --only config
```

**Dry run (see what would be restored):**
```bash
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto --dry-run
```

### Backup Rotation

Automatic rotation runs after each backup. To run manually:

```bash
# Check what would be deleted (dry run)
sudo /opt/uptime-monitor/scripts/backup-rotation.sh --dry-run

# Run rotation
sudo /opt/uptime-monitor/scripts/backup-rotation.sh

# Keep only last 5 backups of each type
sudo /opt/uptime-monitor/scripts/backup-rotation.sh --keep 5
```

### Verify Backups

**Verify specific backup:**
```bash
sudo /opt/uptime-monitor/scripts/verify-backup.sh \
    /backup/uptime-monitor/daily/backup-20260218-020000.tar.gz
```

**Verify all backups:**
```bash
sudo /opt/uptime-monitor/scripts/verify-backup.sh --all
```

**Show backup statistics:**
```bash
sudo /opt/uptime-monitor/scripts/verify-backup.sh --list
```

### Backup Configuration

Edit `/etc/uptime-monitor/config.json`:

```json
{
    "backup": {
        "enabled": true,
        "on_change_backup": true,
        "retention": {
            "on_change": 10,
            "daily": 7,
            "weekly": "all",
            "monthly": "all",
            "yearly": "all"
        }
    }
}
```

### Unmount Backup Storage

**Unmount NFS:**
```bash
sudo /opt/uptime-monitor/scripts/mount-backup.sh \
    --unmount \
    --mount-point /mnt/nfs-backup
```

**Unmount Samba:**
```bash
sudo /opt/uptime-monitor/scripts/mount-backup.sh \
    --unmount \
    --mount-point /mnt/smb-backup
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