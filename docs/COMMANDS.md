# 📋 Commands Reference

Повний список команд Uptime Monitor

---

## 🔧 Service Management (Управління службою)

```bash
# Запустити службу
sudo systemctl start uptime-monitor

# Зупинити службу
sudo systemctl stop uptime-monitor

# Перезапустити службу
sudo systemctl restart uptime-monitor

# Перевірити статус
sudo systemctl status uptime-monitor

# Увімкнути автозапуск
sudo systemctl enable uptime-monitor

# Вимкнути автозапуск
sudo systemctl disable uptime-monitor
```

---

## 📊 Logs (Логи)

```bash
# Дивитись логи в реальному часі
sudo journalctl -u uptime-monitor -f

# Показати останні 50 рядків
sudo journalctl -u uptime-monitor -n 50

# Показати логи за сьогодні
sudo journalctl -u uptime-monitor --since today

# Показати логи помилок
sudo tail -f /var/log/uptime-monitor/uptime-monitor.error.log
```

---

## ⚙️ Configuration (Конфігурація)

```bash
# Редагувати конфігурацію
sudo nano /etc/uptime-monitor/config.json

# Перевірити синтаксис JSON
python3 -m json.tool /etc/uptime-monitor/config.json

# Перезапустити після змін
sudo systemctl restart uptime-monitor
```

---

## 🔄 Configuration Rollback (Відкат конфігурації)

```bash
# Список доступних версій
sudo /opt/uptime-monitor/scripts/config-rollback.sh --list

# Відкат до попередньої версії
sudo /opt/uptime-monitor/scripts/config-rollback.sh --previous

# Відкат до конкретної версії
sudo /opt/uptime-monitor/scripts/config-rollback.sh --to config.20260218-120000.json

# Показати відмінності
sudo /opt/uptime-monitor/scripts/config-rollback.sh --diff config.latest.json
```

---

## 💾 Backup (Створення бекапів)

```bash
# Створити бекап зараз
sudo /opt/uptime-monitor/scripts/backup-system.sh --dest /backup/uptime-monitor/

# Створити бекап з коментарем
sudo /opt/uptime-monitor/scripts/backup-system.sh --dest /backup/uptime-monitor/ --type on-change --comment "Before SSL setup"

# Перевірити статус бекапів
sudo /opt/uptime-monitor/scripts/backup-system.sh --status

# Перевірити цілісність бекапу
sudo /opt/uptime-monitor/scripts/verify-backup.sh /backup/uptime-monitor/daily/backup-20260218-020000.tar.gz

# Перевірити всі бекапи
sudo /opt/uptime-monitor/scripts/verify-backup.sh --all
```

---

## 📅 Scheduled Backups (Заплановані бекапи)

```bash
# Встановити щоденні бекапи
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --install --daily "0 2 * * *" --dest /backup/uptime-monitor/

# Встановити повний розклад
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --install \
    --daily "0 2 * * *" \
    --weekly "0 3 * * 0" \
    --monthly "0 4 1 * *" \
    --dest /backup/uptime-monitor/

# Перевірити статус розкладу
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --status

# Видалити всі розклади
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --remove

# Тестувати систему бекапів
sudo /opt/uptime-monitor/scripts/schedule-backup.sh --test
```

---

## 🗄️ Restore (Відновлення)

```bash
# Список доступних бекапів
sudo /opt/uptime-monitor/scripts/restore-system.sh --list

# Відновити з останнього бекапу
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto

# Відновити з конкретного бекапу
sudo /opt/uptime-monitor/scripts/restore-system.sh --from /backup/uptime-monitor/daily/backup-20260218-020000.tar.gz

# Відновити тільки базу даних
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto --only database

# Відновити тільки конфігурацію
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto --only config

# Тестовий запуск (без змін)
sudo /opt/uptime-monitor/scripts/restore-system.sh --auto --dry-run
```

---

## 🔄 Backup Rotation (Ротація бекапів)

```bash
# Перевірити що буде видалено
sudo /opt/uptime-monitor/scripts/backup-rotation.sh --dry-run

# Виконати ротацію
sudo /opt/uptime-monitor/scripts/backup-rotation.sh

# Залишити тільки 5 останніх
sudo /opt/uptime-monitor/scripts/backup-rotation.sh --keep 5
```

---

## 🌐 NFS Mount (Монтування NFS)

```bash
# Встановити NFS клієнт
sudo apt-get install -y nfs-common

# Змонтувати NFS
sudo /opt/uptime-monitor/scripts/mount-backup.sh \
    --type nfs \
    --server 192.168.1.10 \
    --path /exports/backups \
    --mount-point /mnt/nfs-backup \
    --persist

# Розмонтувати
sudo /opt/uptime-monitor/scripts/mount-backup.sh --unmount --mount-point /mnt/nfs-backup

# Перевірити монтування
mount | grep nfs
```

---

## 🔗 Samba Mount (Монтування Samba)

```bash
# Встановити Samba клієнт
sudo apt-get install -y cifs-utils

# Змонтувати з паролем
sudo /opt/uptime-monitor/scripts/mount-backup.sh \
    --type smb \
    --server 192.168.1.11 \
    --share backups \
    --mount-point /mnt/smb-backup \
    --username backupuser \
    --password secret \
    --persist

# Змонтувати з credentials файлом
sudo /opt/uptime-monitor/scripts/mount-backup.sh \
    --type smb \
    --server nas.local \
    --share backups \
    --mount-point /mnt/smb-backup \
    --credentials /root/.smb-credentials \
    --persist

# Розмонтувати
sudo /opt/uptime-monitor/scripts/mount-backup.sh --unmount --mount-point /mnt/smb-backup
```

---

## 🔒 SSL/HTTPS Setup

```bash
# Створити директорію для сертифікатів
sudo mkdir -p /etc/uptime-monitor/ssl

# Скопіювати сертифікати
sudo cp /path/to/cert.pem /etc/uptime-monitor/ssl/
sudo cp /path/to/key.pem /etc/uptime-monitor/ssl/

# Встановити права
sudo chmod 600 /etc/uptime-monitor/ssl/*.pem

# Редагувати конфіг
sudo nano /etc/uptime-monitor/config.json
# Змінити:
#   "server.port": 443
#   "ssl.enabled": true

# Перезапустити
sudo systemctl restart uptime-monitor
```

---

## 🧹 Cleanup (Очищення)

```bash
# Перевірити розмір бекапів
sudo du -sh /backup/uptime-monitor/*

# Видалити старі бекапи
sudo /opt/uptime-monitor/scripts/backup-rotation.sh

# Видалити службу
sudo systemctl stop uptime-monitor
sudo systemctl disable uptime-monitor
sudo rm /etc/systemd/system/uptime-monitor.service
sudo systemctl daemon-reload

# Видалити програму
sudo rm -rf /opt/uptime-monitor
sudo rm -rf /etc/uptime-monitor
sudo rm -rf /var/lib/uptime-monitor
sudo userdel uptime-monitor
```

---

## 📍 Шляхи до файлів

| Файл | Шлях |
|------|------|
| Конфігурація | `/etc/uptime-monitor/config.json` |
| База даних | `/var/lib/uptime-monitor/sites.db` |
| SSL сертифікати | `/etc/uptime-monitor/ssl/` |
| Логи | `/var/log/uptime-monitor/` |
| Скрипти | `/opt/uptime-monitor/scripts/` |
| Бекапи | `/backup/uptime-monitor/` |
| Служба systemd | `/etc/systemd/system/uptime-monitor.service` |

---

## 🔍 Корисні команди

```bash
# Перевірити порт
sudo lsof -i :8080

# Перевірити диск
sudo df -h

# Перевірити процеси
ps aux | grep uptime

# Перевірити IP
hostname -I

# Перевірити версію Python
python3 --version

# Перевірити права
ls -la /opt/uptime-monitor/
ls -la /etc/uptime-monitor/
ls -la /var/lib/uptime-monitor/
```
