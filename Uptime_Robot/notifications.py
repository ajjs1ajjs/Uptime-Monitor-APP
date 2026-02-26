"""Модуль для відправки сповіщень"""

import asyncio
import aiohttp
import smtplib
import json
import os
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from datetime import datetime
from logger import logger


class NotificationService:
    """Сервіс для відправки сповіщень"""

    def __init__(self, settings: Dict[str, Any]):
        """Ініціалізація сервісу сповіщень"""
        self.settings = settings

    async def send(self, message: str, methods: List[str]):
        """Відправляє сповіщення через вказані методи"""
        tasks = []
        for method in methods:
            if method == "telegram" and self.settings.get("telegram", {}).get(
                "enabled"
            ):
                tasks.append(send_telegram(message, self.settings["telegram"]))
            elif method == "teams" and self.settings.get("teams", {}).get("enabled"):
                tasks.append(send_teams(message, self.settings["teams"]))
            elif method == "discord" and self.settings.get("discord", {}).get(
                "enabled"
            ):
                tasks.append(send_discord(message, self.settings["discord"]))
            elif method == "slack" and self.settings.get("slack", {}).get("enabled"):
                tasks.append(send_slack(message, self.settings["slack"]))
            elif method == "email" and self.settings.get("email", {}).get("enabled"):
                tasks.append(send_email(message, self.settings["email"]))
            elif method == "sms" and self.settings.get("sms", {}).get("enabled"):
                tasks.append(send_sms(message, self.settings["sms"]))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


async def send_notification(
    message: str, methods: List[str], notify_settings: Dict[str, Any]
):
    """Відправляє сповіщення через вказані методи"""
    tasks = []
    for method in methods:
        if method == "telegram" and notify_settings.get("telegram", {}).get("enabled"):
            tasks.append(send_telegram(message, notify_settings["telegram"]))
        elif method == "teams" and notify_settings.get("teams", {}).get("enabled"):
            tasks.append(send_teams(message, notify_settings["teams"]))
        elif method == "discord" and notify_settings.get("discord", {}).get("enabled"):
            tasks.append(send_discord(message, notify_settings["discord"]))
        elif method == "slack" and notify_settings.get("slack", {}).get("enabled"):
            tasks.append(send_slack(message, notify_settings["slack"]))
        elif method == "email" and notify_settings.get("email", {}).get("enabled"):
            tasks.append(send_email(message, notify_settings["email"]))
        elif method == "sms" and notify_settings.get("sms", {}).get("enabled"):
            tasks.append(send_sms(message, notify_settings["sms"]))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_telegram(message: str, settings: Dict[str, Any]):
    """Відправляє повідомлення в Telegram"""
    token = settings.get("token")
    chat_id = settings.get("chat_id")

    if not token or not chat_id:
        return

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Telegram API error: {response.status} - {error_text}"
                    )
    except Exception as e:
        logger.error(f"Telegram error: {e}")


async def send_teams(message: str, settings: Dict[str, Any]):
    """Відправляє повідомлення в Microsoft Teams"""
    webhook_url = settings.get("webhook_url")
    if not webhook_url:
        return

    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in [200, 204]:
                    logger.error(f"Teams API error: {response.status}")
    except Exception as e:
        logger.error(f"Teams error: {e}")


async def send_discord(message: str, settings: Dict[str, Any]):
    """Відправляє повідомлення в Discord"""
    webhook_url = settings.get("webhook_url")
    if not webhook_url:
        return

    try:
        payload = {"content": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in [200, 204]:
                    logger.error(f"Discord API error: {response.status}")
    except Exception as e:
        logger.error(f"Discord error: {e}")


async def send_slack(message: str, settings: Dict[str, Any]):
    """Відправляє повідомлення в Slack"""
    webhook_url = settings.get("webhook_url")
    if not webhook_url:
        return

    try:
        payload = {"text": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in [200, 204]:
                    logger.error(f"Slack API error: {response.status}")
    except Exception as e:
        logger.error(f"Slack error: {e}")


async def send_email(message: str, settings: Dict[str, Any]):
    """Відправляє email"""
    smtp_server = settings.get("smtp_server")
    smtp_port = settings.get("smtp_port", 587)
    username = settings.get("username")
    password = settings.get("password")
    to_email = settings.get("to_email")

    if not all([smtp_server, username, password, to_email]):
        return

    try:
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = "Uptime Monitor Alert"
        msg["From"] = username
        msg["To"] = to_email

        def _send():
            with smtplib.SMTP(str(smtp_server), int(smtp_port)) as server:
                server.starttls()
                server.login(str(username), str(password))
                server.send_message(msg)

        await asyncio.to_thread(_send)
    except Exception as e:
        logger.error(f"Email error: {e}")


async def send_sms(message: str, settings: Dict[str, Any]):
    """Відправляє SMS через Twilio"""
    account_sid = settings.get("account_sid")
    auth_token = settings.get("auth_token")
    from_number = settings.get("from_number")
    to_number = settings.get("to_number")

    if not all([account_sid, auth_token, from_number, to_number]):
        return

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        auth = aiohttp.BasicAuth(str(account_sid), str(auth_token))
        payload = {
            "From": str(from_number),
            "To": str(to_number),
            "Body": message[:1600],
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, auth=auth) as response:
                if response.status not in [200, 201]:
                    logger.error(f"SMS API error: {response.status}")
    except Exception as e:
        logger.error(f"SMS error: {e}")
