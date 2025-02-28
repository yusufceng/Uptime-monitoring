"""
API rotalarını tanımlayan modül.
"""

import datetime
from flask import Blueprint, jsonify, request
from .. import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/services')
def get_services():
    """Tüm servislerin listesini döndürür."""
    services = db.get_all_services()
    
    # Her servis için son durumu ve istatistikleri ekle
    for service in services:
        history = db.get_uptime_history(service['id'], limit=1)
        service['lastCheck'] = history[0] if history else None
        
        stats = db.get_service_stats(service['id'])
        service['stats'] = stats
    
    return jsonify(services)

@api_bp.route('/services/<int:service_id>')
def get_service(service_id):
    """Belirli bir servisin detaylarını döndürür."""
    service = db.get_service(service_id)
    
    if not service:
        return jsonify({'error': 'Servis bulunamadı'}), 404
    
    # Son kontrolü ekle
    history = db.get_uptime_history(service_id, limit=1)
    service['lastCheck'] = history[0] if history else None
    
    # İstatistikleri ekle
    stats = db.get_service_stats(service_id)
    service['stats'] = stats
    
    return jsonify(service)

@api_bp.route('/services/<int:service_id>/history')
def get_service_history(service_id):
    """Servis için uptime geçmişini döndürür."""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    history = db.get_uptime_history(service_id, limit, offset)
    
    if not history and db.get_service(service_id) is None:
        return jsonify({'error': 'Servis bulunamadı'}), 404
    
    return jsonify(history)

@api_bp.route('/checks/<int:check_id>')
def get_check(check_id):
    """Belirli bir kontrol detayını döndürür."""
    check = db.get_uptime_check(check_id)
    
    if not check:
        return jsonify({'error': 'Kontrol bulunamadı'}), 404
    
    return jsonify(check)

@api_bp.route('/prometheus')
def get_prometheus_endpoints():
    """Tüm Prometheus endpoint'lerini döndürür."""
    endpoints = db.get_all_prometheus_endpoints()
    return jsonify(endpoints)

@api_bp.route('/prometheus/<int:endpoint_id>')
def get_prometheus_endpoint(endpoint_id):
    """Belirli bir Prometheus endpoint detayını döndürür."""
    endpoint = db.get_prometheus_endpoint(endpoint_id)
    
    if not endpoint:
        return jsonify({'error': 'Prometheus endpoint bulunamadı'}), 404
    
    return jsonify(endpoint)

@api_bp.route('/prometheus/<int:endpoint_id>/metrics')
def get_prometheus_metrics(endpoint_id):
    """Endpoint için metrik verilerini döndürür."""
    metric_name = request.args.get('metric_name')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    time_range = request.args.get('time_range', '24h')
    
    # Zaman aralığını kontrol et (şimdilik limit/offset kullanıyoruz)
    metrics = db.get_prometheus_metrics(endpoint_id, metric_name, limit, offset)
    
    if not metrics and db.get_prometheus_endpoint(endpoint_id) is None:
        return jsonify({'error': 'Prometheus endpoint bulunamadı'}), 404
    
    return jsonify(metrics)

@api_bp.route('/prometheus/<int:endpoint_id>/metric_names')
def get_metric_names(endpoint_id):
    """Endpoint için benzersiz metrik adlarını döndürür."""
    metric_names = db.get_unique_metric_names(endpoint_id)
    
    if metric_names is None:
        return jsonify({'error': 'Prometheus endpoint bulunamadı'}), 404
    
    return jsonify(metric_names)
@api_bp.route('/stats/summary')
def get_summary_stats():
    """Özet istatistikleri döndürür."""
    stats = db.get_summary_stats()
    
    # Uptime geçmişi grafiği için veriler
    uptime_history = []
    # Bu kısım normalde veritabanından gelen gerçek verilerle doldurulur
    # Şimdilik örnek veri oluşturuyoruz
    
    stats['uptimeHistory'] = uptime_history
    
    return jsonify(stats)

@api_bp.route('/alerts')
def get_alerts():
    """Tüm alert'leri döndürür."""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    alerts = db.get_all_alerts(include_inactive)
    return jsonify(alerts)

@api_bp.route('/alerts/<int:alert_id>')
def get_alert(alert_id):
    """Belirli bir alert detayını döndürür."""
    alert = db.get_alert(alert_id)
    
    if not alert:
        return jsonify({'error': 'Alert bulunamadı'}), 404
    
    return jsonify(alert)

@api_bp.route('/alerts/<int:alert_id>/history')
def get_alert_history(alert_id):
    """Alert için geçmiş kayıtları döndürür."""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    history = db.get_alert_history(alert_id, limit, offset)
    
    if not history and db.get_alert(alert_id) is None:
        return jsonify({'error': 'Alert bulunamadı'}), 404
    
    return jsonify(history)

@api_bp.route('/health')
def health_check():
    """API sağlık kontrolü."""
    return jsonify({
        'status': 'ok',
        'timestamp': str(datetime.datetime.now())
    })
