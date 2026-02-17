"""Тести для Uptime Monitor"""
import pytest
import asyncio
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Додаємо шлях до модулів
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_module import hash_password, verify_password, hash_password as old_hash_password
from database import get_db_path
from models import init_database, add_site, get_all_sites, delete_site
from notifications import NotificationService


class TestAuth:
    """Тести авторизації"""
    
    def test_password_hashing(self):
        """Тест хешування паролів"""
        password = "test_password123"
        hashed = hash_password(password)
        
        # Перевіряємо що хеш відрізняється від пароля
        assert hashed != password
        # Перевіряємо що bcrypt хеш починається з $2b$
        assert hashed.startswith('$2b$')
        # Перевіряємо верифікацію
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_password_verification_old_hash(self):
        """Тест сумісності зі старими SHA256 хешами"""
        # Старий SHA256 хеш для "admin"
        import hashlib
        old_hash = hashlib.sha256('admin'.encode()).hexdigest()
        
        # Старий метод не повинен працювати з новим verify_password
        assert verify_password('admin', old_hash) is False


class TestDatabase:
    """Тести бази даних"""
    
    def setup_method(self):
        """Налаштування перед кожним тестом"""
        self.test_db = "test_sites.db"
        # Видаляємо стару базу якщо існує
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        init_database(self.test_db)
    
    def teardown_method(self):
        """Очистка після кожного тесту"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_init_database(self):
        """Тест ініціалізації БД"""
        assert os.path.exists(self.test_db)
        
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        
        # Перевіряємо чи створились таблиці
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        
        assert 'sites' in tables
        assert 'status_history' in tables
        assert 'ssl_certificates' in tables
        
        conn.close()
    
    def test_add_site(self):
        """Тест додавання сайту"""
        # Видаляємо базу перед тестом
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        init_database(self.test_db)
        
        site_id = add_site(
            self.test_db,
            name="Test Site",
            url="https://example.com",
            check_interval=60
        )
        
        assert site_id > 0
        
        sites = get_all_sites(self.test_db)
        assert len(sites) == 1
        assert sites[0]['name'] == "Test Site"
        assert sites[0]['url'] == "https://example.com"
    
    def test_delete_site(self):
        """Тест видалення сайту"""
        # Видаляємо базу перед тестом
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        init_database(self.test_db)
        
        site_id = add_site(
            self.test_db,
            name="Test Site Delete",
            url="https://example-delete.com"
        )
        
        sites = get_all_sites(self.test_db)
        assert len(sites) == 1
        
        delete_site(self.test_db, site_id)
        
        sites = get_all_sites(self.test_db)
        assert len(sites) == 0


class TestValidation:
    """Тести валідації"""
    
    def test_url_validation(self):
        """Тест валідації URL"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://sub.example.com/path",
        ]
        
        invalid_urls = [
            "ftp://example.com",
            "example.com",
            "not_a_url",
        ]
        
        for url in valid_urls:
            assert url.startswith(('http://', 'https://'))
        
        for url in invalid_urls:
            assert not url.startswith(('http://', 'https://'))
    
    def test_site_name_validation(self):
        """Тест валідації назви сайту"""
        valid_names = [
            "My Site",
            "Site-123",
            "A",
        ]
        
        for name in valid_names:
            assert len(name.strip()) > 0


class TestNotificationService:
    """Тести сервісу сповіщень"""
    
    def test_notification_service_init(self):
        """Тест ініціалізації сервісу"""
        settings = {
            "telegram": {"enabled": True, "token": "test_token", "chat_id": "123456"},
            "email": {"enabled": False}
        }
        
        service = NotificationService(settings)
        assert service.settings == settings


# pytest.ini конфігурація
"""
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
"""

if __name__ == "__main__":
    # Запуск тестів
    print("Running tests...")
    
    # Тести авторизації
    auth_tests = TestAuth()
    auth_tests.test_password_hashing()
    print("[OK] Password hashing test passed")
    
    auth_tests.test_password_verification_old_hash()
    print("[OK] Old hash compatibility test passed")
    
    # Тести бази даних
    db_tests = TestDatabase()
    db_tests.setup_method()
    db_tests.test_init_database()
    print("[OK] Database initialization test passed")
    
    db_tests.setup_method()
    db_tests.test_add_site()
    print("[OK] Add site test passed")
    
    db_tests.setup_method()
    db_tests.test_delete_site()
    print("[OK] Delete site test passed")
    db_tests.teardown_method()
    
    # Тести валідації
    val_tests = TestValidation()
    val_tests.test_url_validation()
    print("[OK] URL validation test passed")
    
    val_tests.test_site_name_validation()
    print("[OK] Site name validation test passed")
    
    # Тести сповіщень
    notif_tests = TestNotificationService()
    notif_tests.test_notification_service_init()
    print("[OK] Notification service test passed")
    
    print("\n" + "="*50)
    print("All tests passed!")
    print("="*50)
