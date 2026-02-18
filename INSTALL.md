# 🚀 UPTIME MONITOR - ІНСТРУКЦІЯ ВСТАНОВЛЕННЯ

## 📋 ЗМІСТ
- [Linux (CURL)](#linux-curl)
- [Linux (APT)](#linux-apt)
- [Windows](#windows)
- [Docker](#docker)
- [Після встановлення](#після-встановлення)

---

## 🐧 LINUX (CURL)

### Швидке встановлення (одна команда):

```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash
```

### З конкретним портом:

```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --port 9090
```

### Конкретна версія:

```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --version v1.0.0
```

### Керування сервісом:

```bash
# Перевірити статус
sudo systemctl status uptime-monitor

# Запустити
sudo systemctl start uptime-monitor

# Зупинити
sudo systemctl stop uptime-monitor

# Перезапустити
sudo systemctl restart uptime-monitor

# Логи
sudo journalctl -u uptime-monitor -f
```

---

## 🐧 LINUX (APT)

### ⚠️ ВАЖЛИВО: Використовуйте curl-версію замість APT

APT репозиторій зараз не працює через проблему з GPG ключем. Рекомендується використовувати curl-версію встановлення.

### Як оновити версію при встановленні через curl:

#### Оновити до останньої версії:

```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash
```

#### Встановити конкретну версію:

```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --version v1.0.0
```

#### Встановити з конкретним портом:

```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --port 9090
```

#### Перевірити поточну версію:

```bash
systemctl status uptime-monitor | grep "Version"
```

#### Оновити до останньої версії вручну:

```bash
# Зупинити сервіс
sudo systemctl stop uptime-monitor

# Оновити через curl
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash

# Запустити сервіс
sudo systemctl start uptime-monitor
sudo systemctl enable uptime-monitor
```

### Як оновити версію при встановленні через curl (підтримка версій):

1. **Перевірте доступні версії:**
   - GitHub Releases: https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases
   - Main branch: завжди містить останні зміни

2. **Встановлення конкретної версії:**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --version v1.0.0
   ```

3. **Автоматичне оновлення:**
   - Використовуйте скрипт оновлення (якщо буде створено)
   - Перевіряйте GitHub Releases для нових версій

### Керування сервісом:

```bash
# Перевірити статус
sudo systemctl status uptime-monitor

# Запустити
sudo systemctl start uptime-monitor

# Зупинити
sudo systemctl stop uptime-monitor

# Перезапустити
sudo systemctl restart uptime-monitor

# Логи
sudo journalctl -u uptime-monitor -f
```

### Видалення:

```bash
sudo systemctl stop uptime-monitor
sudo systemctl disable uptime-monitor
sudo rm -rf /opt/uptime-monitor
sudo rm -rf /etc/uptime-monitor
sudo rm -rf /var/lib/uptime-monitor
sudo rm -rf /var/log/uptime-monitor
sudo rm /etc/systemd/system/uptime-monitor.service
sudo systemctl daemon-reload
```

---

## 🪟 WINDOWS

### Варіант 1: ZIP архів (ручне встановлення)

#### 1. Завантажити:

```
https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases
```

#### 2. Розпакувати `uptime-monitor-v1.0.0-windows.zip`

#### 3. Відкрити PowerShell як Administrator

#### 4. Встановити залежності:

```powershell
cd C:\шлях\до\uptime-monitor
pip install -r requirements.txt
```

#### 5. Запустити:

```powershell
python main.py
```

#### 6. Встановити як службу (опціонально):

```powershell
install.bat
```

### Варіант 2: Windows Service

#### 1. Запустити від імені Administrator:

```powershell
install.bat
```

#### 2. Запустити службу:

```powershell
net start uptime-monitor
```

#### 3. Або через Services (services.msc)

### Керування службою:

```powershell
# Запустити
net start uptime-monitor

# Зупинити
net stop uptime-monitor

# Статус
sc query uptime-monitor
```

---

## 🐳 DOCKER

### Запуск:

```bash
docker run -d \
  --name uptime-monitor \
  -p 8080:8080 \
  -v uptime-data:/var/lib/uptime-monitor \
  ghcr.io/ajjs1ajjs/uptime-monitor:latest
```

### Конкретна версія:

```bash
docker run -d \
  --name uptime-monitor \
  -p 8080:8080 \
  -v uptime-data:/var/lib/uptime-monitor \
  ghcr.io/ajjs1ajjs/uptime-monitor:v1.0.0
```

### Docker Compose:

```yaml
version: '3'
services:
  uptime-monitor:
    image: ghcr.io/ajjs1ajjs/uptime-monitor:latest
    ports:
      - "8080:8080"
    volumes:
      - uptime-data:/var/lib/uptime-monitor
    restart: unless-stopped

volumes:
  uptime-data:
```

### Керування:

```bash
# Логи
docker logs -f uptime-monitor

# Зупинити
docker stop uptime-monitor

# Запустити
docker start uptime-monitor

# Перезапустити
docker restart uptime-monitor

# Видалити
docker rm -f uptime-monitor
```

---

## ✅ ПІСЛЯ ВСТАНОВЛЕННЯ

### 1. Відкрити браузер:

```
http://localhost:8080
```

Або (Linux):

```bash
http://$(hostname -I | awk '{print $1}'):8080
```

### 2. Вхід:

```
Username: admin
Password: admin
```

### ⚠️ 3. ЗМІНИТИ ПАРОЛЬ!

### 4. Налаштування Email (опціонально):

```bash
sudo nano /etc/uptime-monitor/config.json
```

```json
{
    "port": 8080,
    "notify_email_enabled": true,
    "notify_email_smtp_server": "smtp.gmail.com",
    "notify_email_smtp_port": 587,
    "notify_email_username": "your-email@gmail.com",
    "notify_email_password": "your-app-password",
    "notify_email_to": "alerts@company.com"
}
```

```bash
sudo systemctl restart uptime-monitor
```

---

## 📌 ПОСИЛАННЯ

| Ресурс | URL |
|--------|-----|
| **GitHub** | https://github.com/ajjs1ajjs/Uptime-Monitor-APP |
| **Releases** | https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases |
| **Issues** | https://github.com/ajjs1ajjs/Uptime-Monitor-APP/issues |
| **Install Script** | https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh |
| **APT Repo** | https://ajjs1ajjs.github.io/Uptime-Monitor-APP |
| **Docker Image** | ghcr.io/ajjs1ajjs/uptime-monitor |

---

## 🔧 КОМАНДИ ДЛЯ КОПІЮВАННЯ

### Linux (найпростіше):

```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash
```

### Windows:

1. Завантажити: https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases
2. Розпакувати
3. Запустити: `python main.py`

### Docker:

```bash
docker run -d -p 8080:8080 ghcr.io/ajjs1ajjs/uptime-monitor:latest
```

---

## 📞 ПІДТРИМКА

- **Email:** yaroslav.andreichuk@gmail.com
- **GitHub Issues:** https://github.com/ajjs1ajjs/Uptime-Monitor-APP/issues

---

## 📄 ЛІЦЕНЗІЯ

MIT License

---

**Версія:** 1.0.0  
**Автор:** Yaroslav Andreichuk
