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
VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
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
    OS=$NAME
    VER=$VERSION_ID
else
    echo -e "${RED}Error: Cannot detect OS${NC}"
    exit 1
fi

echo -e "${YELLOW}Detected OS: $OS $VER${NC}"

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

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${YELLOW}Using Python: $PYTHON_VERSION${NC}"

# Install system dependencies
echo -e "${BLUE}Installing system dependencies...${NC}"
case "$OS" in
    "Ubuntu"|"Debian GNU/Linux")
        apt-get update -qq
        apt-get install -y -qq python3-pip python3-venv sqlite3 curl > /dev/null
        ;;
    "CentOS Linux"|"Red Hat Enterprise Linux"|"Fedora")
        yum install -y -q python3-pip sqlite curl > /dev/null 2>&1 || \
        dnf install -y -q python3-pip sqlite curl > /dev/null 2>&1
        ;;
    *)
        echo -e "${RED}Unsupported OS: $OS${NC}"
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

# Detect latest version
if [ -z "$VERSION" ]; then
    echo -e "${BLUE}Detecting latest version...${NC}"
    VERSION=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" | \
              grep '"tag_name":' | \
              sed -E 's/.*"([^"]+)".*/\1/')
    
    if [ -z "$VERSION" ]; then
        VERSION="v1.0.0"
        echo -e "${YELLOW}Could not detect version, using: $VERSION${NC}"
    else
        echo -e "${GREEN}Latest version: $VERSION${NC}"
    fi
fi

# Download and extract
echo -e "${BLUE}Downloading $VERSION...${NC}"
cd /tmp
DOWNLOAD_URL="https://github.com/$GITHUB_REPO/releases/download/$VERSION/uptime-monitor-$VERSION-linux.tar.gz"

if ! curl -fsSL "$DOWNLOAD_URL" -o uptime-monitor.tar.gz; then
    echo -e "${YELLOW}Package not found, downloading from source...${NC}"
    DOWNLOAD_URL="https://github.com/$GITHUB_REPO/archive/refs/tags/$VERSION.tar.gz"
    curl -fsSL "$DOWNLOAD_URL" -o uptime-monitor.tar.gz
fi

echo -e "${BLUE}Extracting...${NC}"
tar -xzf uptime-monitor.tar.gz

# Find extracted directory
EXTRACT_DIR=$(find . -maxdepth 1 -type d -name "uptime-monitor*" -o -name "Uptime-Monitor*" | head -1)

if [ -z "$EXTRACT_DIR" ]; then
    echo -e "${RED}Error: Could not find extracted files${NC}"
    exit 1
fi

# Install files
echo -e "${BLUE}Installing application...${NC}"
if [ -d "$EXTRACT_DIR/src" ]; then
    cp -r "$EXTRACT_DIR/src/"* "$INSTALL_DIR/"
else
    cp -r "$EXTRACT_DIR/"* "$INSTALL_DIR/"
fi

if [ -d "$EXTRACT_DIR/templates" ]; then
    cp -r "$EXTRACT_DIR/templates" "$INSTALL_DIR/"
fi

if [ -d "$EXTRACT_DIR/static" ]; then
    cp -r "$EXTRACT_DIR/static" "$INSTALL_DIR/"
fi

if [ -f "$EXTRACT_DIR/requirements.txt" ]; then
    cp "$EXTRACT_DIR/requirements.txt" "$INSTALL_DIR/"
fi

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
cd "$INSTALL_DIR"
$PYTHON_CMD -m pip install -r requirements.txt --break-system-packages 2>/dev/null || \
$PYTHON_CMD -m pip install -r requirements.txt

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
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="CONFIG_PATH=$CONFIG_DIR/config.json"
ExecStart=/usr/bin/$PYTHON_CMD $INSTALL_DIR/main.py --port $PORT
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
    if command -v hostname &> /dev/null; then
        IP=$(hostname -I | awk '{print $1}')
    else
        IP="localhost"
    fi
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "   Installation Successful!"
    echo "==========================================${NC}"
    echo ""
    echo -e "  ${GREEN}Version:${NC}     $VERSION"
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
