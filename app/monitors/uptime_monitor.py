"""
Servis uptime durumunu izleyen modül.
"""

import time
import logging
import threading
import requests
from urllib3.exceptions import InsecureRequestWarning

# SSL uyarılarını kapat
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

logger = logging.getLogger("microservice-monitor.uptime")

class UptimeMonitor:
    """Servislerin uptime durumunu kontrol eden sınıf."""
    
    def __init__(self, db):
        """Uptime izleyicisini başlatır."""
        self.db = db
        self.stopping = False
        self.monitor_thread = None
    
    def check_service(self, service):
        """Bir servisin durumunu kontrol eder ve sonucu veritabanına kaydeder."""
        start_time = time.time()
        is_up = False
        status_code = None
        error = None
        response_headers = None
        
        try:
            response = requests.get(
                service['url'],
                timeout=service['timeout'],
                verify=False  # SSL sertifikası doğrulamasını devre dışı bırakır
            )
            status_code = response.status_code
            is_up = 200 <= response.status_code < 400
            response_headers = dict(response.headers)
            
        except requests.exceptions.Timeout as e:
            error = f"Timeout: {str(e)}"
            status_code = 0
            is_up = False
            
        except requests.exceptions.ConnectionError as e:
            error = f"Connection Error: {str(e)}"
            status_code = 0
            is_up = False
            
        except requests.exceptions.RequestException as e:
            error = f"Request Error: {str(e)}"
            status_code = 0
            is_up = False
        
        response_time = time.time() - start_time
        
        # Sonucu veritabanına kaydet
        check_id = self.db.add_uptime_check(
            service['id'],
            status_code,
            response_time,
            is_up,
            error,
            response_headers
        )
        
        logger.info(f"Servis kontrolü: {service['name']} - Durum: {'UP' if is_up else 'DOWN'}, Yanıt Süresi: {response_time:.3f}s")
        
        # Alert'leri kontrol et
        self._check_alerts(service, is_up, response_time, status_code)
        
        return {
            'id': check_id,
            'is_up': is_up,
            'response_time': response_time,
            'status_code': status_code,
            'error': error
        }
    
    def _check_alerts(self, service, is_up, response_time, status_code):
        """Servisle ilgili alert'leri kontrol eder."""
        # Burada alert kontrolü yapılacak
        # Şimdilik sadece log kaydı oluşturuyoruz
        if not is_up:
            logger.warning(f"ALERT: {service['name']} servis çalışmıyor! Status code: {status_code}")
    
    def monitor_services(self):
        """Tüm servisleri düzenli olarak kontrol eder."""
        logger.info("Servis izleme başladı")
        
    def monitor_services(self):
        """Tüm servisleri düzenli olarak kontrol eder."""
        logger.info("Servis izleme başladı")
        
        while not self.stopping:
            try:
                # Aktif servisleri al
                services = self.db.get_all_services()
                logger.info(f"Kontrol edilecek {len(services)} servis bulundu")
                
                for service in services:
                    logger.info(f"Kontrol ediliyor: {service['name']} - URL: {service['url']}")
                    # Her servis için bir kontrol yap
                    try:
                        result = self.check_service(service)
                        logger.info(f"Kontrol sonucu: {service['name']} - Durum: {'UP' if result['is_up'] else 'DOWN'}")
                    except Exception as e:
                        logger.error(f"Servis kontrol hatası ({service['name']}): {str(e)}")
                    
                    # Diğer servislere geçmeden kısa bir bekle 
                    time.sleep(0.5)
                
                # Bir sonraki kontrol turuna geçmeden önce bekle
                logger.info("Tüm servisler kontrol edildi, bekleniyor...")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Servis izleme hatası: {str(e)}")
                time.sleep(10)  # Hata durumunda daha uzun bekle
    
    def start(self):
        """Servis izlemeyi başlatır."""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.stopping = False
            self.monitor_thread = threading.Thread(target=self.monitor_services)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("Uptime izleme servisi başlatıldı")
    
    def stop(self):
        """Servis izlemeyi durdurur."""
        self.stopping = True
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
            logger.info("Uptime izleme servisi durduruldu")
