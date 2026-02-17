"""Модуль для відправки сповіщень"""
import asyncio
import aiohttp
import smtplib
import json
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional
from logger import logger


class NotificationService:
    """Сервіс для відправки сповіщень через різні канали"""
    
    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
    
    async def send_notification(self, message: str, methods: Optional[List[str]] = None):
        """Відправляє сповіщення через вказані методи"""
        if not methods:
            return
        
        tasks = []
        for method in methods:
            if method == "telegram" and self.settings.get("telegram", {}).get("enabled"):
                tasks.append(self._send_telegram(message))
            elif method == "teams" and self.settings.get("teams", {}).get("enabled"):
                tasks.append(self._send_teams(message))
            elif method == "discord" and self.settings.get("discord", {}).get("enabled"):
                tasks.append(self._send_discord(message))
            elif method == "slack" and self.settings.get("slack", {}).get("enabled"):
                tasks.append(self._send_slack(message))
            elif method == "email" and self.settings.get("email", {}).get("enabled"):
                tasks.append(self._send_email(message))
            elif method == "sms" and self.settings.get("sms", {}).get("enabled"):
                tasks.append(self._send_sms(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_telegram(self, message: str):
        """Відправляє повідомлення в Telegram"""
        try:
            settings = self.settings.get("telegram", {})
            token = settings.get("token")
            chat_id = settings.get("chat_id")
            
            if not token or not chat_id:
                return
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Telegram API error: {response.status}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")
    
    async def _send_teams(self, message: str):
        """Відправляє повідомлення в Microsoft Teams"""
        try:
            settings = self.settings.get("teams", {})
            webhook_url = settings.get("webhook_url")
            
            if not webhook_url:
                return
            
            payload = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "themeColor": "FF0000",
                "summary": "Uptime Monitor Alert",
                "sections": [{
                    "activityTitle": "⚠️ Site Down Alert",
                    "activitySubtitle": message,
                    "markdown": True
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Teams API error: {response.status}")
        except Exception as e:
            logger.error(f"Teams error: {e}")
    
    async def _send_discord(self, message: str):
        """Відправляє повідомлення в Discord"""
        try:
            settings = self.settings.get("discord", {})
            webhook_url = settings.get("webhook_url")
            
            if not webhook_url:
                return
            
            payload = {
                "content": message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 204:
                        logger.error(f"Discord API error: {response.status}")
        except Exception as e:
            logger.error(f"Discord error: {e}")
    
    async def _send_slack(self, message: str):
        """Відправляє повідомлення в Slack"""
        try:
            settings = self.settings.get("slack", {})
            webhook_url = settings.get("webhook_url")
            
            if not webhook_url:
                return
            
            payload = {
                "text": message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Slack API error: {response.status}")
        except Exception as e:
            logger.error(f"Slack error: {e}")
    
    async def _send_email(self, message: str):
        """Відправляє email"""
        try:
            settings = self.settings.get("email", {})
            smtp_server = settings.get("smtp_server")
            smtp_port = settings.get("smtp_port", 587)
            username = settings.get("username")
            password = settings.get("password")
            to_email = settings.get("to_email")
            
            if not all([smtp_server, username, password, to_email]):
                return
            
            msg = MIMEText(message)
            msg['Subject'] = 'Uptime Monitor Alert'
            msg['From'] = username
            msg['To'] = to_email
            
            await asyncio.to_thread(self._send_email_sync, smtp_server, smtp_port, 
                                   username, password, msg)
        except Exception as e:
            logger.error(f"Email error: {e}")
    
    def _send_email_sync(self, smtp_server: str, smtp_port: int, username: str, 
                        password: str, msg: MIMEText):
        """Синхронна відправка email"""
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
    
    async def _send_sms(self, message: str):
        """Відправляє SMS (placeholder для Twilio)"""
        try:
            settings = self.settings.get("sms", {})
            account_sid = settings.get("account_sid")
            auth_token = settings.get("auth_token")
            from_number = settings.get("from_number")
            to_number = settings.get("to_number")
            
            if not all([account_sid, auth_token, from_number, to_number]):
                return
            
            # Тут має бути інтеграція з Twilio
            logger.info(f"SMS would be sent: {message}")
        except Exception as e:
            logger.error(f"SMS error: {e}")
