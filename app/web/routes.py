"""
Web arayüzü için Flask rotaları.
"""

import os
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from .. import db
import logging

web_bp = Blueprint('web', __name__)

@web_bp.context_processor
def inject_now():
    """Şablonlara tarih değişkenini ekler."""
    return {'now': datetime.datetime.now()}

@web_bp.route('/')
def index():
    """Ana sayfa - Dashboard."""
    # Servisleri al
    services = db.get_all_services()
    
    # Her servis için son durum bilgisini ekle
    for service in services:
        history = db.get_uptime_history(service['id'], limit=1)
        service['last_check'] = history[0] if history else None
    
    # Çalışan ve çalışmayan servisleri ayır
    up_services = [s for s in services if s.get('last_check') and s['last_check']['is_up']]
    down_services = [s for s in services if s.get('last_check') and not s['last_check']['is_up']]
    
    # Prometheus endpoint'lerini al
    prometheus_endpoints = db.get_all_prometheus_endpoints()
    
    # Özet istatistikler
    stats = db.get_summary_stats()
    
    return render_template('index.html',
                          services=services,
                          up_services=up_services,
                          down_services=down_services,
                          prometheus_endpoints=prometheus_endpoints,
                          average_response_time=stats.get('average_response_time', 0))

@web_bp.route('/services')
def services_list():
    """Tüm servislerin listesi."""
    services = db.get_all_services(include_inactive=True)
    
    # Her servis için son durum bilgisini ekle
    for service in services:
        history = db.get_uptime_history(service['id'], limit=1)
        service['last_check'] = history[0] if history else None
    
    return render_template('services_list.html', services=services)

@web_bp.route('/services/<int:service_id>')
def service_detail(service_id):
    logging.info(f"Servis detayı isteği - Service ID: {service_id}")
    print(f"Servis detayı isteği - Service ID: {service_id}")
    
    service = db.get_service(service_id)
    print(f"Bulunan Servis: {service}")
    
    
    if not service:
        print("Servis bulunamadı")
        flash('Servis bulunamadı', 'danger')
        return redirect(url_for('web.services_list'))
    
    # Diğer print() logları ekleyebilirsiniz
    print(f"Uptime geçmişi çekiliyor: {service_id}")
    history = db.get_uptime_history(service_id, limit=1000)
    print(f"Uptime geçmişi: {history}")
    
    print("İstatistikler çekiliyor")
    stats = db.get_service_stats(service_id)
    print(f"Servis İstatistikleri: {stats}")
    
    # Uptime geçmişini al
    history = db.get_uptime_history(service_id, limit=1000)
    
    # İstatistikleri hesapla
    stats = db.get_service_stats(service_id)
    
    # Son 24 saat ve 7 gün için uptime yüzdeleri
    uptime_24h = 100
    uptime_7d = 100
    uptime_30d = 100
    
    # Son 24 saat ve 7 gün için ortalama yanıt süreleri
    avg_response_time_24h = 0
    avg_response_time_7d = 0
    
    # Geçmiş başlangıç zamanı
    history_start_time = datetime.datetime.now() - datetime.timedelta(hours=24)
    if history:
        history_start_time = datetime.datetime.fromisoformat(history[-1]['checked_at'].replace('Z', '+00:00'))
    
    return render_template('service_detail.html',
                          service=service,
                          history=history,
                          history_start_time=history_start_time,
                          uptime_percentage=stats['uptime_percentage'],
                          uptime_24h=uptime_24h,
                          uptime_7d=uptime_7d,
                          uptime_30d=uptime_30d,
                          avg_response_time=stats['avg_response_time'],
                          avg_response_time_24h=avg_response_time_24h,
                          avg_response_time_7d=avg_response_time_7d,
                          min_response_time=stats['min_response_time'],
                          max_response_time=stats['max_response_time'],
                          total_checks=stats['total_checks'])

@web_bp.route('/services/<int:service_id>/edit', methods=['GET', 'POST'])
def service_edit(service_id):
    """Servis düzenleme sayfası."""
    service = db.get_service(service_id)
    
    if not service:
        flash('Servis bulunamadı', 'danger')
        return redirect(url_for('web.services_list'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        description = request.form.get('description', '')
        check_interval = int(request.form.get('check_interval', 60))
        timeout = int(request.form.get('timeout', 5))
        is_active = bool(request.form.get('is_active', False))
        
        if db.update_service(service_id, name, url, description, check_interval, timeout, is_active):
            flash('Servis güncellendi', 'success')
            return redirect(url_for('web.service_detail', service_id=service_id))
        else:
            flash('Servis güncellenirken bir hata oluştu', 'danger')
    
    return render_template('service_edit.html', service=service)

@web_bp.route('/services/<int:service_id>/delete', methods=['POST'])
def service_delete(service_id):
    """Servis silme işlemi."""
    service = db.get_service(service_id)
    
    if not service:
        flash('Servis bulunamadı', 'danger')
        return redirect(url_for('web.services_list'))
    
    if db.delete_service(service_id):
        flash('Servis silindi', 'success')
    else:
        flash('Servis silinirken bir hata oluştu', 'danger')
    
    return redirect(url_for('web.services_list'))

@web_bp.route('/add/service', methods=['GET', 'POST'])
def add_service():
    """Yeni servis ekleme sayfası."""
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        description = request.form.get('description', '')
        check_interval = int(request.form.get('check_interval', 60))
        timeout = int(request.form.get('timeout', 5))
        
        if name and url:
            service_id = db.add_service(name, url, description, check_interval, timeout)
            flash('Servis eklendi', 'success')
            return redirect(url_for('web.service_detail', service_id=service_id))
        else:
            flash('Ad ve URL alanları gereklidir', 'danger')
    
    return render_template('service_add.html')

@web_bp.route('/prometheus')
def prometheus_list():
    """Tüm Prometheus endpoint'lerinin listesi."""
    endpoints = db.get_all_prometheus_endpoints(include_inactive=True)
    return render_template('prometheus_list.html', endpoints=endpoints)

@web_bp.route('/prometheus/<int:endpoint_id>')
def prometheus_detail(endpoint_id):
    """Prometheus endpoint detay sayfası."""
    endpoint = db.get_prometheus_endpoint(endpoint_id)
    
    if not endpoint:
        flash('Prometheus endpoint bulunamadı', 'danger')
        return redirect(url_for('web.prometheus_list'))
    
    # Metrik adlarını al
    metric_names = db.get_unique_metric_names(endpoint_id)
    
    # Son toplanan metrikleri al
    recent_metrics = db.get_prometheus_metrics(endpoint_id, limit=50)
    
    # Metrik sayısı
    metrics_count = len(db.get_prometheus_metrics(endpoint_id, limit=1))
    
    # Son kontrol zamanı
    last_check_time = "Henüz veri yok"
    if recent_metrics:
        last_check_time = recent_metrics[0]['collected_at']
    
    return render_template('prometheus_detail.html',
                          endpoint=endpoint,
                          metric_names=metric_names,
                          recent_metrics=recent_metrics,
                          metrics_count=metrics_count,
                          last_check_time=last_check_time)

@web_bp.route('/prometheus/<int:endpoint_id>/edit', methods=['GET', 'POST'])
def prometheus_edit(endpoint_id):
    """Prometheus endpoint düzenleme sayfası."""
    endpoint = db.get_prometheus_endpoint(endpoint_id)
    
    if not endpoint:
        flash('Prometheus endpoint bulunamadı', 'danger')
        return redirect(url_for('web.prometheus_list'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        query = request.form.get('query', '')
        description = request.form.get('description', '')
        check_interval = int(request.form.get('check_interval', 300))
        is_active = bool(request.form.get('is_active', False))
        
        if db.update_prometheus_endpoint(endpoint_id, name, url, query, description, check_interval, is_active):
            flash('Prometheus endpoint güncellendi', 'success')
            return redirect(url_for('web.prometheus_detail', endpoint_id=endpoint_id))
        else:
            flash('Prometheus endpoint güncellenirken bir hata oluştu', 'danger')
    
    return render_template('prometheus_edit.html', endpoint=endpoint)

@web_bp.route('/prometheus/<int:endpoint_id>/delete', methods=['POST'])
def prometheus_delete(endpoint_id):
    """Prometheus endpoint silme işlemi."""
    endpoint = db.get_prometheus_endpoint(endpoint_id)
    
    if not endpoint:
        flash('Prometheus endpoint bulunamadı', 'danger')
        return redirect(url_for('web.prometheus_list'))
    
    if db.delete_prometheus_endpoint(endpoint_id):
        flash('Prometheus endpoint silindi', 'success')
    else:
        flash('Prometheus endpoint silinirken bir hata oluştu', 'danger')
    
    return redirect(url_for('web.prometheus_list'))

@web_bp.route('/add/prometheus', methods=['GET', 'POST'])
def add_prometheus():
    """Yeni Prometheus endpoint ekleme sayfası."""
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        query = request.form.get('query', '')
        description = request.form.get('description', '')
        check_interval = int(request.form.get('check_interval', 300))
        
        if name and url:
            endpoint_id = db.add_prometheus_endpoint(name, url, query, description, check_interval)
            flash('Prometheus endpoint eklendi', 'success')
            return redirect(url_for('web.prometheus_detail', endpoint_id=endpoint_id))
        else:
            flash('Ad ve URL alanları gereklidir', 'danger')
    
    return render_template('prometheus_add.html')

@web_bp.route('/alerts')
def alerts_list():
    """Tüm alert'lerin listesi."""
    alerts = db.get_all_alerts(include_inactive=True)
    return render_template('alerts_list.html', alerts=alerts)

@web_bp.route('/reports')
def reports():
    """Raporlar sayfası."""
    return render_template('reports.html')

@web_bp.route('/settings')
def settings():
    """Ayarlar sayfası."""
    return render_template('settings.html')

@web_bp.route('/about')
def about():
    """Hakkında sayfası."""
    return render_template('about.html')

@web_bp.route('/import-export')
def import_export():
    """İçe/Dışa aktarma sayfası."""
    return render_template('import_export.html')
