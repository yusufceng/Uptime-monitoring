"""
Uygulamayı başlatan ana script.
"""

import os
import sys
import argparse
import logging
from app import create_app

def parse_args():
    """Komut satırı argümanlarını ayrıştırır."""
    parser = argparse.ArgumentParser(description='OCP Mikro Servis Monitoring')
    
    parser.add_argument('-c', '--config', default=None,
                        help='Konfigürasyon dosyası (YAML)')
    
    parser.add_argument('-H', '--host', default='0.0.0.0',
                        help='Bağlanılacak host (default: 0.0.0.0)')
    
    parser.add_argument('-p', '--port', type=int, default=5000,
                        help='Dinlenecek port (default: 5000)')
    
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debug modunu etkinleştir')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Ayrıntılı loglama etkinleştir')
    
    return parser.parse_args()

def main():
    """Ana uygulama girişi."""
    args = parse_args()
    
    # Loglama seviyesini ayarla
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Ortam değişkenlerini ayarla
    if args.debug:
        os.environ['FLASK_ENV'] = 'development'
    else:
        os.environ['FLASK_ENV'] = 'production'
    
    # Konfigürasyon dosyasını ayarla
    if args.config:
        os.environ['IMPORT_CONFIG_FILE'] = args.config
    
    # Uygulamayı oluştur
    app = create_app()
    
    # Uygulamayı başlat
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
