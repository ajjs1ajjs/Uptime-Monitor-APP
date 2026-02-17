#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
GITHUB_REPO="ajjs1ajjs/Uptime-Monitor-APP"
INSTALL_DIR="/opt/uptime-monitor"
CONFIG_DIR="/etc/uptime-monitor"
DATA_DIR="/var/lib/uptime-monitor"
LOG_DIR="/var/log/uptime-monitor"
SERVICE_NAME="uptime-monitor"
USER="uptime-monitor"
APP_VERSION="v1.0.0"

echo -e "${GREEN}"
echo "=========================================="
echo "   Uptime Monitor - Installation Script"
echo "=========================================="
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

# Parse arguments
PORT=8080

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --version)
            APP_VERSION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT       Set port (default: 8080)"
            echo "  --version VERSION Install specific version (e.g., v1.0.0)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
    OS_VERSION=$VERSION_ID
else
    echo -e "${RED}Error: Cannot detect OS${NC}"
    exit 1
fi

echo -e "${YELLOW}Detected OS: $OS_NAME $OS_VERSION${NC}"

# Check Python version
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}Error: Python 3.10+ is required${NC}"
    exit 1
fi

PYTHON_VER=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${YELLOW}Using Python: $PYTHON_VER${NC}"

# Install system dependencies
echo -e "${BLUE}Installing system dependencies...${NC}"
case "$OS_NAME" in
    "Ubuntu"|"Debian GNU/Linux")
        apt-get update -qq
        apt-get install -y -qq python3-pip python3-venv python3-full sqlite3 curl > /dev/null
        ;;
    "CentOS Linux"|"Red Hat Enterprise Linux"|"Fedora")
        yum install -y -q python3-pip sqlite curl > /dev/null 2>&1 || \
        dnf install -y -q python3-pip sqlite curl > /dev/null 2>&1
        ;;
    *)
        echo -e "${RED}Unsupported OS: $OS_NAME${NC}"
        echo "Supported: Ubuntu, Debian, CentOS, RHEL, Fedora"
        exit 1
        ;;
esac

# Create user
if ! id "$USER" &>/dev/null; then
    echo -e "${BLUE}Creating user: $USER${NC}"
    useradd -r -s /bin/false -d "$DATA_DIR" "$USER"
fi

# Create directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"

# Download from source archive (always use main branch for latest fixes)
echo -e "${BLUE}Downloading from GitHub main branch...${NC}"
cd /tmp
DOWNLOAD_URL="https://github.com/$GITHUB_REPO/archive/refs/heads/main.tar.gz"

if ! curl -fsSL "$DOWNLOAD_URL" -o uptime-monitor.tar.gz 2>/dev/null; then
    echo -e "${RED}Error: Failed to download from GitHub${NC}"
    exit 1
fi

echo -e "${BLUE}Extracting...${NC}"
tar -xzf uptime-monitor.tar.gz

# Find extracted directory
EXTRACT_DIR=$(find . -maxdepth 1 -type d -name "Uptime-Monitor*" | head -1)

if [ -z "$EXTRACT_DIR" ]; then
    echo -e "${RED}Error: Could not find extracted files${NC}"
    exit 1
fi

echo -e "${BLUE}Found: $EXTRACT_DIR${NC}"

# Install files from Uptime_Robot subdirectory
echo -e "${BLUE}Installing application...${NC}"
if [ -d "$EXTRACT_DIR/Uptime_Robot" ]; then
    SRC_DIR="$EXTRACT_DIR/Uptime_Robot"
else
    SRC_DIR="$EXTRACT_DIR"
fi

# Copy Python files
for f in main.py auth_module.py config.py database.py logger.py models.py notifications.py monitoring.py ssl_checker.py; do
    if [ -f "$SRC_DIR/$f" ]; then
        cp "$SRC_DIR/$f" "$INSTALL_DIR/"
    fi
done

# Copy templates and static
if [ -d "$SRC_DIR/templates" ]; then
    cp -r "$SRC_DIR/templates" "$INSTALL_DIR/"
fi

if [ -d "$SRC_DIR/static" ]; then
    cp -r "$SRC_DIR/static" "$INSTALL_DIR/"
fi

# Copy requirements (prefer Linux-specific file on Linux)
if [ -f "$SRC_DIR/requirements-linux.txt" ]; then
    cp "$SRC_DIR/requirements-linux.txt" "$INSTALL_DIR/requirements.txt"
elif [ -f "$SRC_DIR/requirements.txt" ]; then
    cp "$SRC_DIR/requirements.txt" "$INSTALL_DIR/"
    # Remove Windows-specific packages on Linux
    sed -i '/pywin32/d' "$INSTALL_DIR/requirements.txt"
fi

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
cd "$INSTALL_DIR"
$PYTHON_CMD -m venv venv

 # Install Python dependencies in venv
echo -e "${BLUE}Installing Python dependencies...${NC}"
cd "$INSTALL_DIR"
$PYTHON_CMD -m venv venv

# Install Python dependencies in venv
echo -e "${BLUE}Installing Python packages...${NC}"
./venv/bin/pip install --upgrade pip > /dev/null
if [ -f "requirements-linux.txt" ]; then
    ./venv/bin/pip install -r requirements-linux.txt
elif [ -f "requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
fi

# Create configuration
echo -e "${BLUE}Creating configuration...${NC}"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cat > "$CONFIG_DIR/config.json" << EOF
{
    "port": $PORT,
    "host": "0.0.0.0",
    "data_dir": "$DATA_DIR",
    "log_dir": "$LOG_DIR",
    "check_interval": 60,
    
    "notify_email_enabled": false,
    "notify_email_smtp_server": "",
    "notify_email_smtp_port": 587,
    "notify_email_username": "",
    "notify_email_password": "",
    "notify_email_to": ""
}
EOF
fi

# Create systemd service
echo -e "${BLUE}Creating systemd service...${NC}"
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Uptime Monitor Service
Documentation=https://github.com/$GITHUB_REPO
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="CONFIG_PATH=$CONFIG_DIR/config.json"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py --port $PORT
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/uptime-monitor.log
StandardError=append:$LOG_DIR/uptime-monitor.error.log

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
echo -e "${BLUE}Setting permissions...${NC}"
chown -R "$USER:$USER" "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"
chmod 600 "$CONFIG_DIR/config.json"

# Setup firewall
echo -e "${BLUE}Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        ufw allow $PORT/tcp comment 'Uptime Monitor'
        echo -e "${GREEN}Added UFW rule for port $PORT${NC}"
    fi
elif command -v firewall-cmd &> /dev/null; then
    if firewall-cmd --state 2>/dev/null; then
        firewall-cmd --permanent --add-port=$PORT/tcp
        firewall-cmd --reload
        echo -e "${GREEN}Added firewalld rule for port $PORT${NC}"
    fi
fi

# Start service
echo -e "${BLUE}Starting service...${NC}"
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Check status
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    # Get IP
    IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "   Installation Successful!"
    echo "==========================================${NC}"
    echo ""
    echo -e "  ${GREEN}Version:${NC}     $APP_VERSION"
    echo -e "  ${GREEN}Port:${NC}        $PORT"
    echo -e "  ${GREEN}URL:${NC}         http://$IP:$PORT"
    echo ""
    echo -e "  ${YELLOW}Default Credentials:${NC}"
    echo -e "    Username: ${BLUE}admin${NC}"
    echo -e "    Password: ${BLUE}admin${NC}"
    echo ""
    echo -e "  ${YELLOW}Please change the password after first login!${NC}"
    echo ""
    echo "Management commands:"
    echo "  sudo systemctl status $SERVICE_NAME"
    echo "  sudo systemctl restart $SERVICE_NAME"
    echo "  sudo systemctl stop $SERVICE_NAME"
    echo ""
    echo "Configuration:"
    echo "  Config file: $CONFIG_DIR/config.json"
    echo "  Logs:        $LOG_DIR/"
    echo ""
else
    echo -e "${RED}=========================================="
    echo "   Installation Failed"
    echo "==========================================${NC}"
    echo ""
    echo "Service failed to start. Check logs:"
    echo "  sudo journalctl -u $SERVICE_NAME -n 50"
    echo ""
    exit 1
fi

# Cleanup
rm -rf /tmp/uptime-monitor.tar.gz "$EXTRACT_DIR"

echo -e "${GREEN}Done!${NC}"
