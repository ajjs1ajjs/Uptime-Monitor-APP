# Uptime Monitor

[![GitHub release](https://img.shields.io/github/release/ajjs1ajjs/Uptime-Monitor-APP.svg)](https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases)
[![Codecov](https://codecov.io/gh/ajjs1ajjs/Uptime-Monitor-APP/branch/main/graph/badge.svg)](https://codecov.io/gh/ajjs1ajjs/Uptime-Monitor-APP)
[![Docker](https://img.shields.io/badge/ghcr.io-ajjs1ajjs%2Fuptime--monitor-blue)](https://github.com/ajjs1ajjs/Uptime-Monitor-APP/pkgs/container/uptime-monitor-app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Website uptime monitoring service with multi-channel notifications and SSL certificate tracking.

**Features:**
- Monitor multiple websites and endpoints
- SSL certificate expiration tracking
- Multi-channel notifications (Telegram, Email, Slack, Discord, Teams, SMS)
- Web-based dashboard
- REST API
- Cross-platform (Linux, Windows, Docker)

## Quick Start

### Linux (CURL) - Recommended

```bash
# Install latest version
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash

# Install with custom port
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --port 9090

# Install specific version
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash -s -- --version v1.0.0
```

### Linux (APT)

```bash
# Add repository
curl -fsSL https://ajjs1ajjs.github.io/Uptime-Monitor-APP/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/uptime-monitor.gpg
echo "deb [signed-by=/usr/share/keyrings/uptime-monitor.gpg] https://ajjs1ajjs.github.io/Uptime-Monitor-APP stable main" | sudo tee /etc/apt/sources.list.d/uptime-monitor.list

# Install
sudo apt update && sudo apt install uptime-monitor

# Start
sudo systemctl start uptime-monitor
```

### Docker

```bash
# Pull and run
docker run -d -p 8080:8080 -v uptime-data:/var/lib/uptime-monitor ghcr.io/ajjs1ajjs/uptime-monitor:latest
```

### Windows

1. Download `uptime-monitor-vX.X.X-windows.zip` from [Releases](https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases)
2. Extract to desired location
3. Run `install.bat` as Administrator

## Default Credentials

- **Username:** `admin`
- **Password:** `admin`

**Change password after first login!**

## Структура проекту

```
Uptime_Robot/
├── main.py                 # Головна програма
├── requirements.txt        # Залежності Python
├── icon.ico               # Іконка програми
├── install.bat            # Встановлення як служба
├── build.bat              # Збірка інсталятора
├── build_installer.py     # Скрипт створення інсталятора
├── create_icon.py         # Генератор іконки
├── uptime_monitor.spec    # Конфігурація PyInstaller
├── README.md              # Цей файл
└── sites.db               # База даних (створюється автоматично)
```

## Швидкий старт (Python)

### 1. Встановлення залежностей
```bash
pip install -r requirements.txt
```

### 2. Запуск вручну
```bash
python main.py [port]
```

За замовчуванням порт 8000. Приклад:
```bash
python main.py 8080
```

### 3. Вхід в систему
Відкрийте браузер: http://localhost:8000 (або ваш порт)

**Обов'язкова авторизація:**
- **Логін:** `admin`
- **Пароль:** `admin`
- ⚠️ **Обов'язково змініть пароль після першого входу!**

Після входу система перенаправить на сторінку зміни пароля.

## Встановлення як Windows служба

### Спосіб 1: Простий (install.bat)
1. Запустіть `install.bat` від імені Адміністратора
2. Введіть порт
3. Служба буде встановлена та запущена

```bash
install.bat
```

### Спосіб 2: Створення EXE + інсталятора

1. **Запустіть збірку:**
```bash
build.bat
```
Це створить:
- `UptimeMonitor.exe` - головний виконуваний файл
- Інсталятор з GUI для вибору порту
- Програма реєструється в "Programs and Features" для видалення

2. **Встановіть:**
- Запустіть згенерований інсталятор
- Введіть бажаний порт
- Програма встановиться в `C:\Program Files\UptimeMonitor`
- Служба автоматично запуститься

3. **Доступ:**
- Веб-інтерфейс: http://localhost:[port]
- Автоматичний визначення IP показується на головній сторінці

### Управління службою

```cmd
# Зупинити
net stop UptimeMonitor

# Запустити
net start UptimeMonitor

# Перезапустити
net stop UptimeMonitor && net start UptimeMonitor

# Видалити службу
sc delete UptimeMonitor
```

## Видалення програми

### Якщо встановлено через інсталятор:
1. Відкрийте "Settings" -> "Apps" -> "Installed apps"
2. Знайдіть "Uptime Monitor"
3. Натисніть "Uninstall"

### Ручне видалення:
```cmd
net stop UptimeMonitor
sc delete UptimeMonitor
rd /s /q "C:\Program Files\UptimeMonitor"
```

## Налаштування сповіщень

### Доступні канали:
- 📱 **Telegram** - Bot Token + Chat ID
- 🏢 **MS Teams** - Incoming Webhook URL
- 🎮 **Discord** - Webhook URL
- 💬 **Slack** - Incoming Webhook URL
- 📧 **Email** - SMTP (Gmail, Outlook, тощо)
- 📱 **SMS** - Twilio API

### Налаштування в веб-інтерфейсі:
1. Увімкніть потрібні канали (toggle switches)
2. Заповніть дані для кожного каналу
3. Натисніть "Зберегти налаштування"

## Функціонал

### Моніторинг сайтів:
- ➕ Додавання сайтів з вибором каналів сповіщень
- ✏️ Редагування доданих сайтів
- 🗑️ Видалення сайтів
- 🔄 Ручна перевірка

### Статистика:
- Загальна кількість сайтів
- Кількість доступних/недоступних
- Uptime (відсоток доступності)
- Час відповіді
- HTTP статус код

### Автоматичні перевірки:
- Кожні 60 секунд
- Автоматичні сповіщення при падінні
- Антиспам: сповіщення не частіше ніж раз в 5 хвилин

## API Endpoints

- `GET /` - Веб-інтерфейс
- `GET /api/sites` - Список всіх сайтів
- `POST /api/sites` - Додати сайт
- `PUT /api/sites/{id}` - Оновити сайт
- `DELETE /api/sites/{id}` - Видалити сайт
- `POST /api/sites/{id}/check` - Перевірити сайт вручну
- `POST /api/notify-settings` - Зберегти налаштування сповіщень

## Порт

За замовчуванням: **8000**

Можна змінити:
- При запуску: `python main.py 8080`
- При встановленні через інсталятор
- В файлі `port.txt` в папці програми

## Технічні деталі

- **Фреймворк:** FastAPI
- **База даних:** SQLite
- **HTTP клієнт:** aiohttp
- **Windows служба:** pywin32
- **Порт:** Конфігурований (за замовч. 8000)
- **IP:** Автоматично визначається локальна IP адреса

## Проблеми та рішення

### Порт зайнятий
Змініть порт в файлі `port.txt` або запустіть з іншим портом.

### Служба не запускається
Перевірте чи є права адміністратора:
```cmd
sc query UptimeMonitor
```

### Не надходять сповіщення
Перевірте налаштування в веб-інтерфейсі та правильність API ключів.

## Ліцензія

MIT License
