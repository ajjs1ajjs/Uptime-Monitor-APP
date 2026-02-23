# 📚 Uptime Monitor Documentation

Документація та інструкції для Uptime Monitor

---

## 📖 Швидка навігація

| Документ | Опис | Для чого |
|----------|------|----------|
| **[QUICKSTART.md](QUICKSTART.md)** | Швидкий старт | Швидко запустити систему |
| **[COMMANDS.md](COMMANDS.md)** | Команди | Знайти потрібну команду |
| **[BACKUP.md](BACKUP.md)** | Бекапи | Налаштувати бекапи |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Проблеми | Вирішити проблему |

---

## 🚀 Початок роботи

**Новий користувач?** Почніть з [QUICKSTART.md](QUICKSTART.md)

```bash
# 1. Встановити
curl -fsSL https://raw.githubusercontent.com/ajjs1ajjs/Uptime-Monitor-APP/main/install.sh | sudo bash

# 2. Створити бекап
sudo /opt/uptime-monitor/Uptime_Robot/scripts/backup-system.sh --dest /backup/uptime-monitor/

# 3. Відкрити в браузері
# http://$(hostname -I | awk '{print $1}'):8080
```

---

## 💡 Коли що використовувати

### 🔧 Потрібна команда?
→ [COMMANDS.md](COMMANDS.md) - всі команди в одному місці

### 💾 Проблеми з бекапом?
→ [BACKUP.md](BACKUP.md) - повна інструкція з бекапу

### 🛠️ Щось не працює?
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - вирішення проблем

### ⏱️ Швидкий старт?
→ [QUICKSTART.md](QUICKSTART.md) - 5 хвилин і все готово

---

## 📋 Основні команди

```bash
# Керування службою
sudo systemctl start|stop|restart|status uptime-monitor

# Бекап
sudo /opt/uptime-monitor/Uptime_Robot/scripts/backup-system.sh --dest /backup/uptime-monitor/

# Відновлення
sudo /opt/uptime-monitor/Uptime_Robot/scripts/restore-system.sh --auto

# Перегляд логів
sudo journalctl -u uptime-monitor -f
```

---

## 🔗 Корисні посилання

- **Веб-інтерфейс**: `http://$(hostname -I | awk '{print $1}'):8080`
- **Основна документація**: [../INSTALL.md](../INSTALL.md)
- **GitHub**: https://github.com/ajjs1ajjs/Uptime-Monitor-APP

---

## 🆘 Екстрена допомога

Якщо все пішло не так:

1. **Перевірте логи:**
   ```bash
   sudo journalctl -u uptime-monitor -n 50
   ```

2. **Відновіть з бекапу:**
   ```bash
   sudo /opt/uptime-monitor/Uptime_Robot/scripts/restore-system.sh --auto
   ```

3. **Перевірте [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

4. **Створіть issue на GitHub**

---

## 📝 License

MIT License - дивіться основний проект
