// Dashboard.js - Ana dashboard fonksiyonları

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // Toast bildirimleri için
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        toast.innerHTML = `
            <div class="toast-header">
                <strong>${type === 'success' ? 'Başarılı' : type === 'error' ? 'Hata' : 'Bilgi'}</strong>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Otomatik kapat
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(15px)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    };
    
    // Tooltip'leri etkinleştir
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltips.length) {
        tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
    }
    
    // Sayfa belirli bir ID'ye sahipse o ID ile ilgili işlemleri başlat
    if (document.body.id === 'dashboard-page') {
        initDashboard();
    } else if (document.body.id === 'service-detail-page') {
        initServiceDetail();
    } else if (document.body.id === 'prometheus-detail-page') {
        initPrometheusDetail();
    }
});

// Dashboard sayfası için
function initDashboard() {
    // Servislerin durumunu periyodik olarak güncelle
    updateServicesStatus();
    setInterval(updateServicesStatus, 60000); // Her dakika
    
    // Özet istatistiklerini yükle
    loadSummaryStats();
}

// Servislerin durumunu API'den alıp güncelle
function updateServicesStatus() {
    fetch('/api/services')
        .then(response => response.json())
        .then(services => {
            const servicesList = document.getElementById('services-list');
            if (!servicesList) return;
            
            // Status sayaçları
            let upCount = 0;
            let downCount = 0;
            
            services.forEach(service => {
                const statusElem = document.getElementById(`service-status-${service.id}`);
                const responseTimeElem = document.getElementById(`service-response-time-${service.id}`);
                
                if (statusElem) {
                    let statusHtml = '';
                    
                    if (service.lastCheck && service.lastCheck.is_up) {
                        statusHtml = `<span class="status-badge status-badge-up"><i class="bi bi-check-circle"></i> Çalışıyor</span>`;
                        upCount++;
                    } else if (service.lastCheck) {
                        statusHtml = `<span class="status-badge status-badge-down"><i class="bi bi-x-circle"></i> Çalışmıyor</span>`;
                        downCount++;
                    } else {
                        statusHtml = `<span class="status-badge status-badge-unknown"><i class="bi bi-question-circle"></i> Bilinmiyor</span>`;
                    }
                    
                    statusElem.innerHTML = statusHtml;
                }
                
                if (responseTimeElem && service.lastCheck) {
                    const responseTime = service.lastCheck.response_time * 1000; // saniyeden milisaniyeye
                    let responseClass = 'response-fast';
                    let responseIcon = 'lightning-charge';
                    
                    if (responseTime > 1000) {
                        responseClass = 'response-slow';
                        responseIcon = 'hourglass-split';
                    } else if (responseTime > 300) {
                        responseClass = 'response-medium';
                        responseIcon = 'stopwatch';
                    }
                    
                    responseTimeElem.innerHTML = `
                        <span class="response-time ${responseClass}">
                            <i class="bi bi-${responseIcon}"></i> ${responseTime.toFixed(1)} ms
                        </span>
                    `;
                }
            });
            
            // Özet istatistiklerini güncelle
            const upCountElem = document.getElementById('up-services-count');
            const downCountElem = document.getElementById('down-services-count');
            
            if (upCountElem) upCountElem.textContent = upCount;
            if (downCountElem) downCountElem.textContent = downCount;
        })
        .catch(error => {
            console.error('Error fetching services:', error);
            showToast('Servis durumları güncellenirken bir hata oluştu.', 'error');
        });
}

// Özet istatistiklerini yükle
function loadSummaryStats() {
    fetch('/api/stats/summary')
        .then(response => response.json())
        .then(stats => {
            // Sistem sağlığı grafiği
            if (stats.uptimeHistory && document.getElementById('system-health-chart')) {
                renderUptimeChart('system-health-chart', stats.uptimeHistory);
            }
            
            // Genel istatistikler
            if (stats.servicesCount !== undefined) {
                document.getElementById('total-services-count').textContent = stats.servicesCount;
            }
            
            if (stats.averageResponseTime !== undefined) {
                document.getElementById('avg-response-time').textContent = 
                    `${(stats.averageResponseTime * 1000).toFixed(1)} ms`;
            }
            
            if (stats.uptime !== undefined) {
                document.getElementById('overall-uptime').textContent = 
                    `${stats.uptime.toFixed(2)}%`;
            }
        })
        .catch(error => {
            console.error('Error fetching summary stats:', error);
            showToast('İstatistikler yüklenirken bir hata oluştu.', 'error');
        });
}

// Uptime geçmiş grafiği oluştur
function renderUptimeChart(canvasId, historyData) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const labels = historyData.map(data => new Date(data.timestamp).toLocaleTimeString());
    const uptimeData = historyData.map(data => data.upCount / (data.upCount + data.downCount) * 100);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sistem Sağlığı (%)',
                data: uptimeData,
                borderColor: '#2ecc71',
                backgroundColor: 'rgba(46, 204, 113, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Servis detay sayfası için
function initServiceDetail() {
    const serviceId = document.getElementById('service-id')?.value;
    if (!serviceId) return;
    
    // Yanıt süresi grafiği
    loadResponseTimeChart(serviceId);
    
    // Uptime çubuğu
    loadUptimeBar(serviceId);
    
// Status güncellemeleri
    loadServiceStatus(serviceId);
    setInterval(() => loadServiceStatus(serviceId), 30000); // Her 30 saniyede bir
}

// Yanıt süresi grafiği yükle
function loadResponseTimeChart(serviceId) {
    fetch(`/api/services/${serviceId}/history?limit=100`)
        .then(response => response.json())
        .then(history => {
            const ctx = document.getElementById('response-time-chart').getContext('2d');
            
            // En son kontrolden en eskiye doğru sırala
            history.reverse();
            
            const labels = history.map(check => {
                const date = new Date(check.checked_at);
                return date.toLocaleTimeString();
            });
            
            const responseTimeData = history.map(check => check.response_time * 1000); // ms cinsinden
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Yanıt Süresi (ms)',
                        data: responseTimeData,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return value + ' ms';
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading response time chart:', error);
            showToast('Yanıt süresi grafiği yüklenirken bir hata oluştu.', 'error');
        });
}

// Uptime çubuğu oluştur
function loadUptimeBar(serviceId) {
    fetch(`/api/services/${serviceId}/history?limit=100`)
        .then(response => response.json())
        .then(history => {
            const uptimeBar = document.getElementById('uptime-bar');
            if (!uptimeBar) return;
            
            uptimeBar.innerHTML = '';
            
            // En eski kontrolden en yeniye doğru sırala
            history.reverse();
            
            history.forEach(check => {
                const slice = document.createElement('div');
                slice.className = `uptime-slice uptime-slice-${check.is_up ? 'up' : 'down'}`;
                
                // Tooltip ekle
                const date = new Date(check.checked_at);
                const tooltip = `${date.toLocaleString()}<br>Durum: ${check.is_up ? 'Çalışıyor' : 'Çalışmıyor'}<br>Yanıt Süresi: ${(check.response_time * 1000).toFixed(1)} ms`;
                
                slice.setAttribute('data-bs-toggle', 'tooltip');
                slice.setAttribute('data-bs-html', 'true');
                slice.setAttribute('title', tooltip);
                
                uptimeBar.appendChild(slice);
            });
            
            // Tooltipleri etkinleştir
            const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            if (tooltips.length) {
                tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));
            }
        })
        .catch(error => {
            console.error('Error loading uptime bar:', error);
            showToast('Uptime geçmişi yüklenirken bir hata oluştu.', 'error');
        });
}

// Servis durumunu güncelle
function loadServiceStatus(serviceId) {
    fetch(`/api/services/${serviceId}`)
        .then(response => response.json())
        .then(service => {
            const statusElem = document.getElementById('service-current-status');
            const responseTimeElem = document.getElementById('service-current-response-time');
            const lastCheckElem = document.getElementById('service-last-check');
            
            if (statusElem && service.lastCheck) {
                let statusHtml = '';
                
                if (service.lastCheck.is_up) {
                    statusHtml = `<span class="status-badge status-badge-up"><i class="bi bi-check-circle"></i> Çalışıyor</span>`;
                } else {
                    statusHtml = `<span class="status-badge status-badge-down"><i class="bi bi-x-circle"></i> Çalışmıyor</span>`;
                }
                
                statusElem.innerHTML = statusHtml;
            }
            
            if (responseTimeElem && service.lastCheck) {
                const responseTime = service.lastCheck.response_time * 1000; // saniyeden milisaniyeye
                responseTimeElem.textContent = `${responseTime.toFixed(1)} ms`;
            }
            
            if (lastCheckElem && service.lastCheck) {
                const date = new Date(service.lastCheck.checked_at);
                lastCheckElem.textContent = date.toLocaleString();
            }
        })
        .catch(error => {
            console.error('Error loading service status:', error);
            showToast('Servis durumu güncellenirken bir hata oluştu.', 'error');
        });
}

// Prometheus detay sayfası için
function initPrometheusDetail() {
    const endpointId = document.getElementById('endpoint-id')?.value;
    if (!endpointId) return;
    
    // Metrik listesini yükle
    loadMetricsList(endpointId);
    
    // Seçili metrik için grafik oluştur
    const metricSelector = document.getElementById('metric-selector');
    if (metricSelector) {
        metricSelector.addEventListener('change', function() {
            const metricName = this.value;
            if (metricName) {
                loadMetricChart(endpointId, metricName);
            }
        });
        
        // İlk metriği seç (varsa)
        if (metricSelector.options.length > 0) {
            metricSelector.dispatchEvent(new Event('change'));
        }
    }
}

// Metrik listesini yükle
function loadMetricsList(endpointId) {
    fetch(`/api/prometheus/${endpointId}/metrics`)
        .then(response => response.json())
        .then(metrics => {
            // Benzersiz metrik adlarını bul
            const uniqueMetrics = [...new Set(metrics.map(m => m.metric_name))];
            
            const metricSelector = document.getElementById('metric-selector');
            if (!metricSelector) return;
            
            // Mevcut seçenekleri temizle
            metricSelector.innerHTML = '';
            
            // Yeni seçenekleri ekle
            uniqueMetrics.forEach(metricName => {
                const option = document.createElement('option');
                option.value = metricName;
                option.textContent = metricName;
                metricSelector.appendChild(option);
            });
            
            // İlk metriği seç (varsa)
            if (metricSelector.options.length > 0) {
                metricSelector.dispatchEvent(new Event('change'));
            }
        })
        .catch(error => {
            console.error('Error loading metrics list:', error);
            showToast('Metrik listesi yüklenirken bir hata oluştu.', 'error');
        });
}

// Metrik grafiği oluştur
function loadMetricChart(endpointId, metricName) {
    fetch(`/api/prometheus/${endpointId}/metrics?metric_name=${encodeURIComponent(metricName)}`)
        .then(response => response.json())
        .then(metrics => {
            const ctx = document.getElementById('metric-chart').getContext('2d');
            
            // Grafiği temizle
            if (window.metricChart) {
                window.metricChart.destroy();
            }
            
            // En son toplamadan en eskiye doğru sırala
            metrics.reverse();
            
            const labels = metrics.map(metric => {
                const date = new Date(metric.collected_at);
                return date.toLocaleTimeString();
            });
            
            const metricData = metrics.map(metric => metric.metric_value);
            
            window.metricChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: metricName,
                        data: metricData,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error(`Error loading metric chart for ${metricName}:`, error);
            showToast('Metrik grafiği yüklenirken bir hata oluştu.', 'error');
        });
}
