"""Модуль для моніторингу сайтів"""

import asyncio
import aiohttp
import json
import socket
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from logger import logger
from database import get_db_connection
from ssl_checker import check_ssl_certificate, format_certificate_alert

# Глобальні змінні для відстеження стану
LAST_STATUS = {}  # site_id -> status
LAST_DOWN_ALERT = {}  # site_id -> datetime


def normalize_ssl_url(url: str) -> Optional[str]:
    """Нормалізує URL для перевірки SSL (додає https:// якщо потрібно)"""
    if not url:
        return None
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        return f"https://{url}"
    return url


async def check_site_status(
    site_id: int, url: str, notify_methods: List[str], notify_settings: Dict[str, Any]
):
    """Перевіряє статус сайту та відправляє сповіщення"""
    global LAST_STATUS, LAST_DOWN_ALERT
    from notifications import send_notification

    start_time = datetime.now()
    status = "down"
    status_code = None
    response_time = None
    error_message = None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        # У майбутньому тут можна додати логіку для різних типів моніторів (port, ping)
        # Наразі реалізовано HTTP/HTTPS
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15),
                headers=headers,
                ssl=False,
                allow_redirects=True,
            ) as response:
                status_code = response.status
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                status = "up" if status_code < 500 else "down"
    except aiohttp.ClientConnectorError:
        error_message = "Connection failed"
    except asyncio.TimeoutError:
        error_message = "Timeout"
    except Exception as e:
        error_message = str(e)[:100]

    checked_at = datetime.now()
    checked_at_iso = checked_at.isoformat()

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name, status FROM sites WHERE id = ?", (site_id,))
        row = c.fetchone()
        site_name = row["name"] if row else url
        prev_status = row["status"] if row else None

        # Only save to history when status CHANGES
        if prev_status != status:
            c.execute(
                """INSERT INTO status_history (site_id, status, status_code, response_time, error_message, checked_at)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    site_id,
                    status,
                    status_code,
                    round(response_time, 2) if response_time else None,
                    error_message,
                    checked_at_iso,
                ),
            )

        c.execute(
            "UPDATE sites SET status = ?, status_code = ?, response_time = ? WHERE id = ?",
            (
                status,
                status_code,
                round(response_time, 2) if response_time else None,
                site_id,
            ),
        )
        conn.commit()

    in_memory_prev_status = LAST_STATUS.get(site_id)

    # Логіка сповіщень - використовуємо статус з БД для уникнення дублювання
    notification_status = prev_status if prev_status else in_memory_prev_status

    if status == "down" and notify_methods:
        should_alert = False
        alert_type = ""

        if notification_status == "up" or notification_status is None:
            should_alert = True
            alert_type = "NEW"
        else:
            last_alert = LAST_DOWN_ALERT.get(site_id)
            # Повторне сповіщення раз на 30 хвилин (як у main.py)
            if last_alert is None or (checked_at - last_alert).total_seconds() >= 1800:
                should_alert = True
                alert_type = "REPEAT"

        if should_alert:
            if alert_type == "NEW":
                msg = {
                    "alert_type": "down",
                    "site_name": site_name,
                    "url": url,
                    "status_code": status_code or "N/A",
                    "error": error_message or "None",
                    "checked_at": checked_at_iso,
                }
            else:
                msg = {
                    "alert_type": "still_down",
                    "site_name": site_name,
                    "url": url,
                    "status_code": status_code or "N/A",
                    "error": error_message or "None",
                    "checked_at": checked_at_iso,
                }

            await send_notification(msg, notify_methods, notify_settings)
            LAST_DOWN_ALERT[site_id] = checked_at

    # Сповіщення про відновлення
    if status == "up" and notification_status == "down" and notify_methods:
        msg = {
            "alert_type": "up",
            "site_name": site_name,
            "url": url,
            "status_code": status_code,
            "response_time": response_time,
            "checked_at": checked_at_iso,
        }
        await send_notification(msg, notify_methods, notify_settings)
        if site_id in LAST_DOWN_ALERT:
            del LAST_DOWN_ALERT[site_id]

    LAST_STATUS[site_id] = status
    return status, status_code, response_time, error_message


async def check_site_certificate(
    site_id: int, url: str, notify_methods: List[str], notify_settings: Dict[str, Any]
):
    """Перевіряє SSL сертифікат сайту"""
    from notifications import send_notification

    # Тільки для HTTPS
    if not url.lower().startswith("https://"):
        # Спробуємо нормалізувати
        if "." in url and "://" not in url:
            url = "https://" + url
        else:
            return

    cert_info = await check_ssl_certificate(url)
    if not cert_info:
        return

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sites WHERE id = ?", (site_id,))
        row = c.fetchone()
        site_name = row["name"] if row else url

        c.execute(
            """UPDATE ssl_certificates SET
               hostname = ?, issuer = ?, subject = ?, start_date = ?, expire_date = ?,
               days_until_expire = ?, is_valid = ?, last_checked = ?
               WHERE site_id = ?""",
            (
                cert_info["hostname"],
                cert_info["issuer"],
                cert_info["subject"],
                cert_info["start_date"],
                cert_info["expire_date"],
                cert_info["days_until_expire"],
                cert_info["is_valid"],
                cert_info["checked_at"],
                site_id,
            ),
        )
        if c.rowcount == 0:
            c.execute(
                """INSERT INTO ssl_certificates
                (site_id, hostname, issuer, subject, start_date, expire_date, days_until_expire, is_valid, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    site_id,
                    cert_info["hostname"],
                    cert_info["issuer"],
                    cert_info["subject"],
                    cert_info["start_date"],
                    cert_info["expire_date"],
                    cert_info["days_until_expire"],
                    cert_info["is_valid"],
                    cert_info["checked_at"],
                ),
            )
        conn.commit()

    # Сповіщення про закінчення терміну дії (за 14 днів)
    days = cert_info["days_until_expire"]
    if days <= 14 and notify_methods:
        c.execute(
            "SELECT last_notified FROM ssl_certificates WHERE site_id = ?", (site_id,)
        )
        row = c.fetchone()

        should_notify = True
        if row and row["last_notified"]:
            last_notif = datetime.fromisoformat(row["last_notified"])
            if (datetime.now() - last_notif).total_seconds() < 86400:  # Раз на добу
                should_notify = False

        if should_notify:
            expire_date = datetime.fromisoformat(cert_info["expire_date"]).strftime(
                "%Y-%m-%d %H:%M"
            )
            days = cert_info["days_until_expire"]

            if days <= 0:
                urgency = "КРИТИЧНО"
            elif days <= 3:
                urgency = "КРИТИЧНО"
            elif days <= 7:
                urgency = "ВАЖЛИВО"
            else:
                urgency = "УВАГА"

            msg = {
                "alert_type": "ssl",
                "site_name": site_name,
                "url": url,
                "days_left": days,
                "expire_date": expire_date,
                "urgency": urgency,
            }
            await send_notification(msg, notify_methods, notify_settings)

            c.execute(
                "UPDATE ssl_certificates SET last_notified = ? WHERE site_id = ?",
                (datetime.now().isoformat(), site_id),
            )
            conn.commit()


async def check_all_certificates(notify_settings: Dict[str, Any]):
    """Перевіряє всі SSL сертифікати"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, url, notify_methods FROM sites WHERE is_active = 1 AND (url LIKE 'https://%' OR monitor_type = 'ssl')"
        )
        sites = c.fetchall()

    for site in sites:
        notify_methods = (
            json.loads(site["notify_methods"]) if site["notify_methods"] else []
        )
        await check_site_certificate(
            site["id"], site["url"], notify_methods, notify_settings
        )
        await asyncio.sleep(1)


async def monitor_loop(notify_settings: Dict[str, Any], check_interval: int = 60):
    """Основний цикл моніторингу"""
    last_cert_check = datetime.now() - timedelta(hours=25)

    while True:
        try:
            # Перевірка доступності сайтів
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT id, url, notify_methods FROM sites WHERE is_active = 1"
                )
                sites = c.fetchall()

            for site in sites:
                notify_methods = (
                    json.loads(site["notify_methods"]) if site["notify_methods"] else []
                )
                # Передаємо notify_settings у check_site_status
                await check_site_status(
                    site["id"], site["url"], notify_methods, notify_settings
                )

            # Перевірка SSL сертифікатів раз на добу
            if (datetime.now() - last_cert_check).total_seconds() >= 86400:
                logger.info("Checking SSL certificates in background...")
                await check_all_certificates(notify_settings)
                last_cert_check = datetime.now()
        except Exception as e:
            logger.error(f"Error in monitor_loop: {e}")

        await asyncio.sleep(check_interval)
