"""
OCP Mikro Servis Monitoring aplikasyonu ana başlatma modülü.
"""

import os
import logging
from flask import Flask
from .config import Config
from .database import Database
from .monitors.uptime_monitor import UptimeMonitor
from .monitors.prometheus_collector import PrometheusCollector

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("microservice_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("microservice-monitor")

# Global değişkenler
db = None
uptime_monitor = None
prometheus_collector = None

def create_app(config_object=Config):
    """Flask uygulamasını oluşturur ve yapılandırır."""
    global db, uptime_monitor, prometheus_collector
    
    # Flask uygulamasını oluştur
    app = Flask(__name__, 
                static_folder='../static', 
                template_folder='web/templates')
                
    # Konfigürasyonu yükle
    app.config.from_object(config_object)
    
    # Veritabanını başlat
    db = Database(app.config['DATABASE_URI'])
    
    # Monitör nesnelerini oluştur
    uptime_monitor = UptimeMonitor(db)
    prometheus_collector = PrometheusCollector(db)
    
    # Blueprint'leri kaydet
    register_blueprints(app)
    
    # Uygulama başlatma işlemleri
    @app.before_first_request
    def initialize():
        """İlk istek geldiğinde çalışacak başlatma fonksiyonu."""
        # Kontrol servislerini başlat
        uptime_monitor.start()
        prometheus_collector.start()
        
        # Konfigürasyon dosyasından içe aktar (eğer varsa)
        if app.config.get('IMPORT_CONFIG_FILE'):
            from .utils import import_config
            config_file = app.config['IMPORT_CONFIG_FILE']
            if os.path.exists(config_file):
                import_config(db, config_file)
    
    # Uygulama kapanış işlemleri
    @app.teardown_appcontext
    def shutdown(exception=None):
        """Uygulama kapanırken çalışacak fonksiyon."""
        if uptime_monitor:
            uptime_monitor.stop()
        if prometheus_collector:
            prometheus_collector.stop()
    
    return app

def register_blueprints(app):
    """Blueprint'leri Flask uygulamasına kaydeder."""
    from .web.routes import web_bp
    from .api.routes import api_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
