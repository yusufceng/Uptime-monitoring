"""
Yardımcı fonksiyonlar ve işlevler.
"""

import os
import yaml
import logging

logger = logging.getLogger("microservice-monitor.utils")

def import_config(db, config_file):
    """YAML konfigürasyon dosyasından servisleri ve Prometheus endpoint'lerini içe aktarır."""
    try:
        if not os.path.exists(config_file):
            logger.warning(f"Konfigürasyon dosyası bulunamadı: {config_file}")
            return False

        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        
        # Servisleri ekle
        if 'services' in config:
            for service_config in config['services']:
                db.add_service(
                    service_config['name'],
                    service_config['url'],
                    service_config.get('description', ''),
                    service_config.get('check_interval', 60),
                    service_config.get('timeout', 5)
                )
        
        # Prometheus endpoint'lerini ekle
        if 'prometheus_endpoints' in config:
            for endpoint_config in config['prometheus_endpoints']:
                db.add_prometheus_endpoint(
                    endpoint_config['name'],
                    endpoint_config['url'],
                    endpoint_config.get('query', ''),
                    endpoint_config.get('description', ''),
                    endpoint_config.get('check_interval', 300)
                )
                
        logger.info(f"Konfigürasyon içe aktarıldı: {config_file}")
        return True
    except Exception as e:
        logger.error(f"Konfigürasyon içe aktarma hatası: {str(e)}")
        return False
