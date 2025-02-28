"""
Konfigürasyon değişkenleri ve ayarları.
"""

import os
import secrets

class Config:
    """Temel konfigürasyon sınıfı."""
    
    # Flask ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    
    # Uygulama ayarları
    APP_NAME = 'OCP Mikro Servis Monitoring'
    
    # Veritabanı ayarları
    DATABASE_URI = os.environ.get('DATABASE_URI') or 'monitor.db'
    
    # Monitör ayarları
    DEFAULT_CHECK_INTERVAL = 60  # Saniye
    DEFAULT_TIMEOUT = 5          # Saniye
    DEFAULT_PROM_INTERVAL = 300  # Saniye
    
    # Dosya yolları
    IMPORT_CONFIG_FILE = os.environ.get('IMPORT_CONFIG_FILE') or 'config.yaml'
    
    # SSL ayarları
    VERIFY_SSL = os.environ.get('VERIFY_SSL', 'False').lower() in ('true', 'yes', '1')
    
    # Loglama ayarları
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # Arayüz ayarları
    ITEMS_PER_PAGE = 50
    
    # Prometheus ayarları
    PROM_DEFAULT_QUERY = 'up'

class DevelopmentConfig(Config):
    """Geliştirme ortamı konfigürasyonu."""
    
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Test ortamı konfigürasyonu."""
    
    DEBUG = False
    TESTING = True
    DATABASE_URI = 'monitor_test.db'

class ProductionConfig(Config):
    """Üretim ortamı konfigürasyonu."""
    
    DEBUG = False
    TESTING = False
    
    # Üretim ortamında daha güvenli ayarlar
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

# Ortama göre konfigürasyon seçimi
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Aktif konfigürasyonu belirle
active_config = config_by_name.get(os.environ.get('FLASK_ENV'), DevelopmentConfig)
