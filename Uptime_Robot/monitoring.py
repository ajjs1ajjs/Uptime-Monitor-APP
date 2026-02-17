"""Модуль для моніторингу сайтів"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional
from logger import logger
from models import add_status_history, update_site, get_site_stats
from ssl_checker import check_ssl_certificate, should_notify_certificate, format_certificate_alert


class SiteMonitor:
    """Моніторинг сайтів"""
    
    def __init__(self, db_path: str, notification_service):
        self.db_path = db_path
        self.notification_service = notification_service
        self.last_status: Dict[int, str] = {}
    
    async def check_site(self, site: Dict[str, Any]) -> Dict[str, Any]:
        """Перевіряє статус сайту"""
        url = site['url']
        site_id = site['id']
        start_time = datetime.now()
        
        status = "down"
        status_code = None
        response_time = None
        error_message = None
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    timeout=aiohttp.ClientTimeout(total=15), 
                    headers=headers, 
                    allow_redirects=True
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
        
        # Зберігаємо історію
        add_status_history(
            self.db_path,
            site_id,
            status,
            status_code,
            response_time,
            error_message
        )
        
        result = {
            'site_id': site_id,
            'status': status,
            'status_code': status_code,
            'response_time': response_time,
            'error_message': error_message
        }
        
        # Перевіряємо чи потрібно відправляти сповіщення
        await self._handle_status_change(site, result)
        
        return result
    
    async def _handle_status_change(self, site: Dict[str, Any], result: Dict[str, Any]):
        """Обробляє зміну статусу та відправляє сповіщення"""
        site_id = site['id']
        current_status = result['status']
        previous_status = self.last_status.get(site_id)
        
        # Оновлюємо last_status
        self.last_status[site_id] = current_status
        
        # Відправляємо сповіщення тільки якщо статус змінився на down
        if current_status == "down" and previous_status == "up":
            await self._send_down_notification(site, result)
        
        # Відправляємо сповіщення про відновлення
        if current_status == "up" and previous_status == "down":
            await self._send_recovery_notification(site, result)
    
    async def _send_down_notification(self, site: Dict[str, Any], result: Dict[str, Any]):
        """Відправляє сповіщення про падіння сайту"""
        notify_methods = self._parse_notify_methods(site.get('notify_methods', '[]'))
        
        if not notify_methods:
            return
        
        # Перевіряємо cooldown
        last_notification = site.get('last_notification')
        if last_notification:
            last_notif_time = datetime.fromisoformat(last_notification)
            if (datetime.now() - last_notif_time).total_seconds() < 300:  # 5 хвилин
                return
        
        message = (
            f"🔴 {site['name']}\n"
            f"🌐 {site['url']}\n"
            f"Status: {result.get('status_code') or 'N/A'}\n"
            f"Error: {result.get('error_message') or 'None'}\n"
            f"Time: {datetime.now().isoformat()}"
        )
        
        await self.notification_service.send_notification(message, notify_methods)
        
        # Оновлюємо час останнього сповіщення
        update_site(self.db_path, site['id'], last_notification=datetime.now().isoformat())
    
    async def _send_recovery_notification(self, site: Dict[str, Any], result: Dict[str, Any]):
        """Відправляє сповіщення про відновлення сайту"""
        notify_methods = self._parse_notify_methods(site.get('notify_methods', '[]'))
        
        if not notify_methods:
            return
        
        message = (
            f"🟢 {site['name']} - RECOVERED\n"
            f"🌐 {site['url']}\n"
            f"Status: {result.get('status_code')}\n"
            f"Response Time: {result.get('response_time', 0):.0f}ms\n"
            f"Time: {datetime.now().isoformat()}"
        )
        
        await self.notification_service.send_notification(message, notify_methods)
    
    def _parse_notify_methods(self, methods_str: str) -> list:
        """Парсить методи сповіщень з JSON"""
        try:
            import json
            return json.loads(methods_str) if methods_str else []
        except:
            return []
    
    async def check_all_sites(self, sites: list):
        """Перевіряє всі сайти"""
        if not sites:
            return
        
        tasks = [self.check_site(site) for site in sites]
        await asyncio.gather(*tasks, return_exceptions=True)


class SSLMonitor:
    """Моніторинг SSL сертифікатів"""
    
    def __init__(self, db_path: str, notification_service):
        self.db_path = db_path
        self.notification_service = notification_service
    
    async def check_certificate(self, site: Dict[str, Any]):
        """Перевіряє SSL сертифікат сайту"""
        url = site['url']
        site_id = site['id']
        
        # Перевіряємо тільки HTTPS
        if not url.startswith('https://'):
            return
        
        try:
            cert_info = check_ssl_certificate(url)
            
            if cert_info:
                # Зберігаємо інформацію про сертифікат
                from models import save_ssl_certificate
                save_ssl_certificate(self.db_path, site_id, cert_info)
                
                # Перевіряємо чи потрібно відправити сповіщення
                if should_notify_certificate(cert_info):
                    await self._send_cert_notification(site, cert_info)
        except Exception as e:
            logger.error(f"SSL check error for {url}: {e}")
    
    async def _send_cert_notification(self, site: Dict[str, Any], cert_info: Dict[str, Any]):
        """Відправляє сповіщення про SSL сертифікат"""
        notify_methods = self._parse_notify_methods(site.get('notify_methods', '[]'))
        
        if not notify_methods:
            return
        
        message = format_certificate_alert(site['name'], site['url'], cert_info)
        await self.notification_service.send_notification(message, notify_methods)
    
    def _parse_notify_methods(self, methods_str: str) -> list:
        """Парсить методи сповіщень з JSON"""
        try:
            import json
            return json.loads(methods_str) if methods_str else []
        except:
            return []
    
    async def check_all_certificates(self, sites: list):
        """Перевіряє SSL сертифікати всіх сайтів"""
        https_sites = [site for site in sites if site['url'].startswith('https://')]
        
        if not https_sites:
            return
        
        tasks = [self.check_certificate(site) for site in https_sites]
        await asyncio.gather(*tasks, return_exceptions=True)
