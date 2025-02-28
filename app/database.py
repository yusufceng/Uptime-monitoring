"""
Veritabanı işlemleri ve bağlantı yönetimi.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("microservice-monitor.database")

class Database:
    """Veritabanı işlemlerini yönetir."""
    
    def __init__(self, db_path):
        """Veritabanını başlatır."""
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Veritabanı bağlantısı döndürür."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Sonuçları dict olarak almak için
        return conn
    
    def init_db(self):
        """Veritabanı şemasını oluşturur."""
        # Veritabanı dosyasının bulunduğu dizini kontrol et
        db_dir = Path(self.db_path).parent
        if db_dir != Path('.') and not db_dir.exists():
            db_dir.mkdir(parents=True)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Servisler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            check_interval INTEGER DEFAULT 60,
            timeout INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # Uptime kontrol sonuçları tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS uptime_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER,
            status_code INTEGER,
            response_time REAL,
            is_up BOOLEAN,
            error TEXT,
            response_headers TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services (id)
        )
        ''')
        
        # Prometheus endpoint'leri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prometheus_endpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            query TEXT,
            description TEXT,
            check_interval INTEGER DEFAULT 300,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # Prometheus metrikleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prometheus_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint_id INTEGER,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            labels TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (endpoint_id) REFERENCES prometheus_endpoints (id)
        )
        ''')
        
        # Alertler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            alert_type TEXT NOT NULL,
            target_id INTEGER,
            condition TEXT NOT NULL,
            threshold REAL,
            duration INTEGER DEFAULT 0,
            notify_channels TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Alert geçmişi tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER,
            status TEXT NOT NULL,
            value REAL,
            message TEXT,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (alert_id) REFERENCES alerts (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Veritabanı şeması oluşturuldu: {self.db_path}")
# Servis işlemleri
    def add_service(self, name, url, description="", check_interval=60, timeout=5):
        """Yeni bir servis ekler ve ID'sini döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO services (name, url, description, check_interval, timeout)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, url, description, check_interval, timeout))
        
        service_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Yeni servis eklendi: {name} (ID: {service_id})")
        return service_id
    
    def update_service(self, service_id, name=None, url=None, description=None, check_interval=None, timeout=None, is_active=None):
        """Servisi günceller."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Mevcut servis bilgilerini al
        cursor.execute('SELECT * FROM services WHERE id = ?', (service_id,))
        service = cursor.fetchone()
        
        if not service:
            conn.close()
            return False
        
        # Güncellenecek alanları belirle
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        
        if url is not None:
            updates.append('url = ?')
            params.append(url)
        
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if check_interval is not None:
            updates.append('check_interval = ?')
            params.append(check_interval)
        
        if timeout is not None:
            updates.append('timeout = ?')
            params.append(timeout)
        
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(is_active)
        
        if not updates:
            conn.close()
            return False
        
        # UPDATE sorgusu oluştur
        query = f'UPDATE services SET {", ".join(updates)} WHERE id = ?'
        params.append(service_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        logger.info(f"Servis güncellendi: ID {service_id}")
        return True
    
    def delete_service(self, service_id):
        """Servisi ve ilgili kontrol geçmişini siler."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Önce kontrol geçmişini sil
        cursor.execute('DELETE FROM uptime_checks WHERE service_id = ?', (service_id,))
        
        # Sonra servisi sil
        cursor.execute('DELETE FROM services WHERE id = ?', (service_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Servis silindi: ID {service_id}")
        return True
    
    def get_service(self, service_id):
        """Servis detaylarını döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM services WHERE id = ?', (service_id,))
        service = cursor.fetchone()
        
        conn.close()
        
        if service:
            return dict(service)
        return None
    
    def get_all_services(self, include_inactive=False):
        """Tüm servisleri döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if include_inactive:
            cursor.execute('SELECT * FROM services ORDER BY name')
        else:
            cursor.execute('SELECT * FROM services WHERE is_active = 1 ORDER BY name')
        
        services = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return services
    
    # Uptime kontrol işlemleri
    def add_uptime_check(self, service_id, status_code, response_time, is_up, error=None, response_headers=None):
        """Uptime kontrol sonucunu kaydeder."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        response_headers_json = None
        if response_headers:
            response_headers_json = json.dumps(dict(response_headers))
        
        cursor.execute('''
        INSERT INTO uptime_checks (service_id, status_code, response_time, is_up, error, response_headers)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (service_id, status_code, response_time, is_up, error, response_headers_json))
        
        check_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return check_id
    
    def get_uptime_check(self, check_id):
        """Belirli bir kontrol detayını döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM uptime_checks WHERE id = ?', (check_id,))
        check = cursor.fetchone()
        
        conn.close()
        
        if check:
            check_dict = dict(check)
            if check_dict.get('response_headers'):
                check_dict['response_headers'] = json.loads(check_dict['response_headers'])
            return check_dict
        return None
    
    def get_uptime_history(self, service_id, limit=100, offset=0):
        """Servis için uptime geçmişini döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM uptime_checks 
        WHERE service_id = ? 
        ORDER BY checked_at DESC 
        LIMIT ? OFFSET ?
        ''', (service_id, limit, offset))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # JSON formatındaki alanları ayrıştır
        for check in history:
            if check.get('response_headers'):
                check['response_headers'] = json.loads(check['response_headers'])
        
        return history
    
    def get_service_stats(self, service_id, days=30):
        """Servis için istatistikleri hesaplar."""
        # Debug print ekleyin
        print(f"DEBUG: get_service_stats() çağrıldı - Service ID: {service_id}, Days: {days}")
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Son X gündeki kontrolleri getir
            print(f"DEBUG: Kontroller çekiliyor - Service ID: {service_id}, Son {days} gün")

            cursor.execute('''
            SELECT is_up, response_time, checked_at
            FROM uptime_checks 
            WHERE service_id = ? 
            AND checked_at >= datetime('now', ?)
            ''', (service_id, f'-{days} days'))
            
            checks = cursor.fetchall()

            print(f"DEBUG: Çekilen kontrol sayısı: {len(checks)}")
            
            if not checks:
                print("DEBUG: Hiç kontrol bulunamadı")
                return {
                    'uptime_percentage': 0,
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0,
                    'total_checks': 0,
                    'up_checks': 0,
                    'down_checks': 0
                }
            
            # İstatistikleri hesapla
            total_checks = len(checks)
            up_checks = sum(1 for check in checks if check['is_up'])
            down_checks = total_checks - up_checks
            
            uptime_percentage = (up_checks / total_checks * 100) if total_checks > 0 else 0
            
            response_times = [check['response_time'] for check in checks if check['response_time'] is not None]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            
            # Hesaplanan istatistikleri debug et
            print(f"DEBUG: İstatistikler - Uptime: {uptime_percentage}%, " 
                f"Ortalama Yanıt Süresi: {avg_response_time}, "
                f"Toplam Kontrol: {total_checks}, "
                f"UP Kontrol: {up_checks}, "
                f"DOWN Kontrol: {down_checks}")
            
            return {
                'uptime_percentage': uptime_percentage,
                'avg_response_time': avg_response_time,
                'min_response_time': min_response_time,
                'max_response_time': max_response_time,
                'total_checks': total_checks,
                'up_checks': up_checks,
                'down_checks': down_checks
            }
        
        except Exception as e:
            # Hata durumunda detaylı bilgi yazdır
            print(f"DEBUG: get_service_stats() hatası - {str(e)}")
            
            # Hata durumunda varsayılan değerler
            return {
                'uptime_percentage': 0,
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'total_checks': 0,
                'up_checks': 0,
                'down_checks': 0
            }
        
        finally:
            # Bağlantıyı her durumda kapat
            if conn:
                conn.close()
    
    # Prometheus endpoint işlemleri
    def add_prometheus_endpoint(self, name, url, query="", description="", check_interval=300):
        """Yeni bir Prometheus endpoint'i ekler."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO prometheus_endpoints (name, url, query, description, check_interval)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, url, query, description, check_interval))
        
        endpoint_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Yeni Prometheus endpoint'i eklendi: {name} (ID: {endpoint_id})")
        return endpoint_id
    
    def update_prometheus_endpoint(self, endpoint_id, name=None, url=None, query=None, description=None, check_interval=None, is_active=None):
        """Prometheus endpoint'ini günceller."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Mevcut endpoint bilgilerini al
        cursor.execute('SELECT * FROM prometheus_endpoints WHERE id = ?', (endpoint_id,))
        endpoint = cursor.fetchone()
        
        if not endpoint:
            conn.close()
            return False
        
        # Güncellenecek alanları belirle
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        
        if url is not None:
            updates.append('url = ?')
            params.append(url)
        
        if query is not None:
            updates.append('query = ?')
            params.append(query)
        
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if check_interval is not None:
            updates.append('check_interval = ?')
            params.append(check_interval)
        
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(is_active)
        
        if not updates:
            conn.close()
            return False
        
        # UPDATE sorgusu oluştur
        query = f'UPDATE prometheus_endpoints SET {", ".join(updates)} WHERE id = ?'
        params.append(endpoint_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        logger.info(f"Prometheus endpoint'i güncellendi: ID {endpoint_id}")
        return True
    
    def delete_prometheus_endpoint(self, endpoint_id):
        """Prometheus endpoint'ini ve ilgili metrikleri siler."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Önce metrikleri sil
        cursor.execute('DELETE FROM prometheus_metrics WHERE endpoint_id = ?', (endpoint_id,))
        
        # Sonra endpoint'i sil
        cursor.execute('DELETE FROM prometheus_endpoints WHERE id = ?', (endpoint_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Prometheus endpoint'i silindi: ID {endpoint_id}")
        return True
    
    def get_prometheus_endpoint(self, endpoint_id):
        """Prometheus endpoint detaylarını döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prometheus_endpoints WHERE id = ?', (endpoint_id,))
        endpoint = cursor.fetchone()
        
        conn.close()
        
        if endpoint:
            return dict(endpoint)
        return None
    
    def get_all_prometheus_endpoints(self, include_inactive=False):
        """Tüm Prometheus endpoint'lerini döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if include_inactive:
            cursor.execute('SELECT * FROM prometheus_endpoints ORDER BY name')
        else:
            cursor.execute('SELECT * FROM prometheus_endpoints WHERE is_active = 1 ORDER BY name')
        
        endpoints = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return endpoints
    
    # Prometheus metrik işlemleri
    def add_prometheus_metric(self, endpoint_id, metric_name, metric_value, labels=None):
        """Prometheus metriğini kaydeder."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        labels_json = json.dumps(labels) if labels else None
        
        cursor.execute('''
        INSERT INTO prometheus_metrics (endpoint_id, metric_name, metric_value, labels)
        VALUES (?, ?, ?, ?)
        ''', (endpoint_id, metric_name, metric_value, labels_json))
        
        metric_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return metric_id
    
    def get_prometheus_metrics(self, endpoint_id, metric_name=None, limit=100, offset=0):
        """Endpoint için Prometheus metriklerini döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
        SELECT * FROM prometheus_metrics 
        WHERE endpoint_id = ?
        '''
        params = [endpoint_id]
        
        if metric_name:
            query += ' AND metric_name = ?'
            params.append(metric_name)
        
        query += ' ORDER BY collected_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        metrics = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # JSON formatındaki alanları ayrıştır
        for metric in metrics:
            if metric.get('labels'):
                metric['labels'] = json.loads(metric['labels'])
        
        return metrics
    
    def get_unique_metric_names(self, endpoint_id):
        """Endpoint için benzersiz metrik adlarını döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT DISTINCT metric_name FROM prometheus_metrics 
        WHERE endpoint_id = ?
        ''', (endpoint_id,))
        
        metric_names = [row['metric_name'] for row in cursor.fetchall()]
        conn.close()
        
        return metric_names
    
    # Alert işlemleri
    def add_alert(self, name, alert_type, target_id, condition, threshold, description="", duration=0, notify_channels=None):
        """Yeni bir alert ekler."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        notify_channels_json = json.dumps(notify_channels) if notify_channels else None
        
        cursor.execute('''
        INSERT INTO alerts (name, alert_type, target_id, condition, threshold, description, duration, notify_channels)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, alert_type, target_id, condition, threshold, description, duration, notify_channels_json))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Yeni alert eklendi: {name} (ID: {alert_id})")
        return alert_id
    
    def update_alert(self, alert_id, name=None, description=None, condition=None, threshold=None, duration=None, notify_channels=None, is_active=None):
        """Alert'i günceller."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Mevcut alert bilgilerini al
        cursor.execute('SELECT * FROM alerts WHERE id = ?', (alert_id,))
        alert = cursor.fetchone()
        
        if not alert:
            conn.close()
            return False
        
        # Güncellenecek alanları belirle
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if condition is not None:
            updates.append('condition = ?')
            params.append(condition)
        
        if threshold is not None:
            updates.append('threshold = ?')
            params.append(threshold)
        
        if duration is not None:
            updates.append('duration = ?')
            params.append(duration)
        
        if notify_channels is not None:
            updates.append('notify_channels = ?')
            params.append(json.dumps(notify_channels))
        
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(is_active)
        
        if not updates:
            conn.close()
            return False
        
        # UPDATE sorgusu oluştur
        query = f'UPDATE alerts SET {", ".join(updates)} WHERE id = ?'
        params.append(alert_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        logger.info(f"Alert güncellendi: ID {alert_id}")
        return True
    
    def delete_alert(self, alert_id):
        """Alert'i ve ilgili geçmişi siler."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Önce alert geçmişini sil
        cursor.execute('DELETE FROM alert_history WHERE alert_id = ?', (alert_id,))
        
        # Sonra alert'i sil
        cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Alert silindi: ID {alert_id}")
        return True
    
    def get_alert(self, alert_id):
        """Alert detaylarını döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM alerts WHERE id = ?', (alert_id,))
        alert = cursor.fetchone()
        
        conn.close()
        
        if alert:
            alert_dict = dict(alert)
            if alert_dict.get('notify_channels'):
                alert_dict['notify_channels'] = json.loads(alert_dict['notify_channels'])
            return alert_dict
        return None
    
    def get_all_alerts(self, include_inactive=False):
        """Tüm alert'leri döndürür."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if include_inactive:
            cursor.execute('SELECT * FROM alerts ORDER BY name')
        else:
            cursor.execute('SELECT * FROM alerts WHERE is_active = 1 ORDER BY name')
        
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # JSON formatındaki alanları ayrıştır
        for alert in alerts:
            if alert.get('notify_channels'):
                alert['notify_channels'] = json.loads(alert['notify_channels'])
        
        return alerts
    
    def add_alert_history(self, alert_id, status, value, message):
        """Alert geçmişine yeni bir kayıt ekler."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO alert_history (alert_id, status, value, message)
        VALUES (?, ?, ?, ?)
        ''', (alert_id, status, value, message))
        
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return history_id
    
    def update_alert_history(self, history_id, status=None, resolved_at=None):
        """Alert geçmiş kaydını günceller."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if status is not None:
            updates.append('status = ?')
            params.append(status)
        
        if resolved_at is not None:
            updates.append('resolved_at = ?')
            params.append(resolved_at)
        
        if not updates:
            conn.close()
            return False
        
        query = f'UPDATE alert_history SET {", ".join(updates)} WHERE id = ?'
        params.append(history_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return True
    def get_alert_history(self, alert_id=None, limit=100, offset=0):
         """Alert geçmişini döndürür."""
         conn = self.get_connection()
         cursor = conn.cursor()
         
         if alert_id:
             cursor.execute('''
             SELECT * FROM alert_history 
             WHERE alert_id = ? 
             ORDER BY triggered_at DESC 
             LIMIT ? OFFSET ?
             ''', (alert_id, limit, offset))
         else:
             cursor.execute('''
             SELECT * FROM alert_history 
             ORDER BY triggered_at DESC 
             LIMIT ? OFFSET ?
             ''', (limit, offset))
        
         history = [dict(row) for row in cursor.fetchall()]
         conn.close()
        
         return history
    
    # Özet istatistikler
    def get_summary_stats(self):
        """Özet istatistikleri hesaplar."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Aktif servis sayısı
        cursor.execute('SELECT COUNT(*) as count FROM services WHERE is_active = 1')
        services_count = cursor.fetchone()['count']
        
        # Tüm servislerin son durumları
        cursor.execute('''
        SELECT s.id, s.name, 
               (SELECT is_up FROM uptime_checks WHERE service_id = s.id ORDER BY checked_at DESC LIMIT 1) as is_up
        FROM services s
        WHERE s.is_active = 1
        ''')
        services_status = cursor.fetchall()
        
        # Çalışan ve çalışmayan servis sayıları
        up_services = [s for s in services_status if s['is_up'] == 1]
        down_services = [s for s in services_status if s['is_up'] == 0 or s['is_up'] is None]
        
        # Son 24 saatteki ortalama yanıt süresi
        cursor.execute('''
        SELECT AVG(response_time) as avg_time
        FROM uptime_checks
        WHERE checked_at >= datetime('now', '-1 day')
        ''')
        avg_response_time = cursor.fetchone()['avg_time'] or 0
        
        # Son 24 saatteki uptime yüzdesi
        cursor.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN is_up = 1 THEN 1 ELSE 0 END) as up_count
        FROM uptime_checks
        WHERE checked_at >= datetime('now', '-1 day')
        ''')
        uptime_stats = cursor.fetchone()
        
        uptime_percentage = 0
        if uptime_stats['total'] > 0:
            uptime_percentage = (uptime_stats['up_count'] / uptime_stats['total']) * 100
        
        conn.close()
        
        return {
            'services_count': services_count,
            'up_services_count': len(up_services),
            'down_services_count': len(down_services),
            'average_response_time': avg_response_time,
            'uptime_percentage': uptime_percentage
        } 
