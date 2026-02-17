# APT Repository for Uptime Monitor

This branch contains the APT repository for Uptime Monitor.

## Usage

```bash
# Add repository
curl -fsSL https://ajjs1ajjs.github.io/Uptime-Monitor-APP/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/uptime-monitor.gpg
echo "deb [signed-by=/usr/share/keyrings/uptime-monitor.gpg] https://ajjs1ajjs.github.io/Uptime-Monitor-APP stable main" | sudo tee /etc/apt/sources.list.d/uptime-monitor.list

# Install
sudo apt update
sudo apt install uptime-monitor
```

## Directory Structure

```
apt-repo/
├── dists/
│   └── stable/
│       └── main/
│           └── binary-amd64/
│               ├── Packages
│               └── Packages.gz
├── pool/
│   └── main/
│       └── u/
│           └── uptime-monitor/
│               └── uptime-monitor_*.deb
└── README.md
```

## Updates

This repository is automatically updated by GitHub Actions when a new release is created.
