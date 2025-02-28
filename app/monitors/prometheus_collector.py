"""
Prometheus metriklerini toplayan modül.
"""

import time
import logging
import threading
import json
import requests
from prometheus_client.parser import text_string_to_metric_families
from urllib3.exceptions import InsecureRequestWarning

# SSL uyarılarını kapat
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

logger = logging.getLogger("microservice-monitor.prometheus")

class PrometheusCollector:
    """Prometheus'tan metrik toplayan sınıf."""
    
    def __init__(self, db):
        """Prometheus toplayıcısını başlatır."""
        self.db = db
        self.stopping = False
        self.collector_thread = None
    
    def query_prometheus(self, endpoint):
        """Prometheus'a sorgu yapar ve metrikleri toplar."""
        try:
            if endpoint['query']:
                # PromQL sorgusu kullan
                url = f"{endpoint['url']}/api/v1/query"
                response = requests.get(
                    url,
                    params={'query': endpoint['query']},
                    timeout=10,
                    verify=False  # SSL sertifikası doğrulamasını devre dışı bırakır
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'success':
                        # Sonuçları işle ve veritabanına kaydet
                        for result in data['data']['result']:
                            metric_name = result['metric'].get('__name__', endpoint['query'])
                            labels = {k: v for k, v in result['metric'].items() if k != '__name__'}
                            
                            # Scalar, vector veya matrix sonuçları işle
                            if isinstance(result['value'], list) and len(result['value']) > 1:
                                # [timestamp, value] formatında
                                try:
                                    metric_value = float(result['value'][1])
                                    self.db.add_prometheus_metric(
                                        endpoint['id'],
                                        metric_name,
                                        metric_value,
                                        labels
                                    )
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Metrik değeri dönüştürme hatası: {str(e)}")
                
                logger.info(f"PromQL sorgusu çalıştırıldı: {endpoint['name']} - {endpoint['query']}")
                return True
                
            else:
                # metrics endpoint'inden tüm metrikleri al
                url = endpoint['url']
                if not url.endswith('/metrics'):
                    url = f"{url}/metrics"
                
                response = requests.get(
                    url,
                    timeout=10,
                    verify=False
                )
                
                if response.status_code == 200:
                    # Metrikleri ayrıştır
                    for family in text_string_to_metric_families(response.text):
                        for sample in family.samples:
                            try:
                                self.db.add_prometheus_metric(
                                    endpoint['id'],
                                    sample.name,
                                    sample.value,
                                    sample.labels
                                )
                            except Exception as e:
                                logger.warning(f"Metrik kaydetme hatası: {str(e)}")
                    
                    logger.info(f"Metrikler toplandı: {endpoint['name']} - {url}")
                    return True
                else:
                    logger.warning(f"Metrik toplama hatası: {endpoint['name']} - HTTP {response.status_code}")
                    return False
                    
        except requests.exceptions.Timeout:
            logger.warning(f"Prometheus sorgu timeout: {endpoint['name']}")
            return False
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Prometheus bağlantı hatası: {endpoint['name']} - {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Prometheus metrik toplama hatası: {endpoint['name']} - {str(e)}")
            return False
    
    def collect_metrics(self):
        """Tüm Prometheus endpoint'lerinden metrik toplar."""
        logger.info("Prometheus metrik toplama başladı")
        
        while not self.stopping:
            try:
                # Aktif endpoint'leri al
                endpoints = self.db.get_all_prometheus_endpoints()
                
                for endpoint in endpoints:
                    # Thread'i durdurmak istersek döngüden çık
                    if self.stopping:
                        break
                    
                    try:
                        # Her endpoint için metrik topla
                        self.query_prometheus(endpoint)
                    except Exception as e:
                        logger.error(f"Metrik toplama hatası ({endpoint['name']}): {str(e)}")
                    
                    # Diğer endpoint'lere geçmeden önce kısa bir bekle
                    time.sleep(1)
                
                # Bir sonraki toplama turuna geçmeden önce bekle
                time.sleep(60)  # Her dakika
                
            except Exception as e:
                logger.error(f"Metrik toplama döngüsü hatası: {str(e)}")
                time.sleep(30)  # Hata durumunda daha uzun bekle
    
    def start(self):
        """Metrik toplamayı başlatır."""
        if self.collector_thread is None or not self.collector_thread.is_alive():
            self.stopping = False
            self.collector_thread = threading.Thread(target=self.collect_metrics)
            self.collector_thread.daemon = True
            self.collector_thread.start()
            logger.info("Prometheus metrik toplama servisi başlatıldı")
    
    def stop(self):
        """Metrik toplamayı durdurur."""
        self.stopping = True
        if self.collector_thread:
            self.collector_thread.join(timeout=10)
            logger.info("Prometheus metrik toplama servisi durduruldu")
