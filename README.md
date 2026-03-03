# Монітор безвідмовної роботи

**Сервіс моніторингу веб-сайтів** з автоматичними бекапами, SSL сертифікатами та багатоканальними сповіщеннями.

---

## 📋 Опис проекту

Uptime Monitor - це open-source рішення для моніторингу доступності веб-сайтів та сервісів. Система автоматично перевіряє стан ваших ресурсів і надсилає сповіщення при виявленні проблем.

### 🔑 Ключові особливості:
- ✅ **Моніторинг 24/7** - автоматична перевірка кожні 60 секунд
- ✅ **Система бекапів** - повне резервне копіювання з відновленням в один клік
- ✅ **SSL моніторинг** - відстеження терміну дії сертифікатів
- ✅ **Багатоканальні сповіщення** - Telegram, Email, Slack, Discord, Teams, SMS
- ✅ **Веб-інтерфейс** - зручний dashboard для управління
- ✅ **Легке налаштування** - встановлення за 5 хвилин

---

## 🚀 Швидкий старт

```bash
# Встановлення
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash

# Створення бекапу
sudo /opt/uptime-monitor/scripts/backup-system.sh --dest /backup/uptime-monitor/

# Доступ
http://$(hostname -I | awk '{print $1}'):8080
Login: admin / Password: admin
```

---

## 📚 Документація

| Документ | Опис |
|----------|------|
| **[QUICKSTART.md](docs/QUICKSTART.md)** | Швидкий старт за 5 хвилин |
| **[COMMANDS.md](docs/COMMANDS.md)** | Всі команди в одному місці |
| **[BACKUP.md](docs/BACKUP.md)** | Налаштування бекапів |
| **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Вирішення проблем |
| **[INSTALL.md](INSTALL.md)** | Повна інструкція з установки |

---

## ✨ Функціонал

### Основні можливості
- 📊 **Моніторинг сайтів** - HTTP/HTTPS перевірка
- 🔒 **SSL сертифікати** - контроль терміну дії
- 🌐 **Веб-інтерфейс** - зручне управління
- 🔌 **REST API** - програмний доступ
- 💻 **Кросплатформеність** - Linux, Windows, Docker

### Новий функціонал 🆕
- 💾 **Система бекапів** - локальні, NFS, Samba
- ⚙️ **Управління конфігурацією** - JSON, авто-IP, відкат
- 🔐 **SSL/HTTPS** - власні сертифікати, автоматичний редирект

---

## 🛠️ Технології

- **Бекенд**: Python, FastAPI
- **База даних**: SQLite
- **Інтерфейс**: HTML/JavaScript
- **Моніторинг**: aiohttp
- **Сповіщення**: SMTP, Telegram Bot API, Webhooks

---

## 📦 Встановлення

### Linux (рекомендовано)
```bash
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash
```

### Докер
```bash
docker run -d -p 8080:8080 -v uptime-data:/var/lib/uptime-monitor \
  ghcr.io/ajjs1ajjs/uptime-monitor:latest
```

### Windows
Завантажити з [Releases](https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases)

---

## 🆘 Допомога

- **Проблеми?** → [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Команді** → [COMMANDS.md](docs/COMMANDS.md)
- **Бекапі** → [BACKUP.md](docs/BACKUP.md)

---

## 📝 Ліцензія

МОЯ ліцензія

---

**⭐ Поставте зірку, якщо проект корисний!**
