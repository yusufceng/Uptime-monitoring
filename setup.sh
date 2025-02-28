#!/bin/bash

# Ana dizinleri oluştur
mkdir -p app/api
mkdir -p app/monitors
mkdir -p app/web/templates
mkdir -p static/css
mkdir -p static/js
mkdir -p data
mkdir -p prometheus

# Boş __init__.py dosyalarını oluştur
touch app/__init__.py
touch app/api/__init__.py
touch app/monitors/__init__.py
touch app/web/__init__.py

# Python dosyalarını oluştur (içerikleri elle dolduracaksınız)
touch app/config.py
touch app/database.py
touch app/api/routes.py
touch app/monitors/uptime_monitor.py
touch app/monitors/prometheus_collector.py
touch app/web/routes.py

# HTML şablonlarını oluştur
touch app/web/templates/layout.html
touch app/web/templates/index.html
touch app/web/templates/service_detail.html
touch app/web/templates/prometheus_detail.html

# Static dosyalarını oluştur
touch static/css/style.css
touch static/js/dashboard.js

# Ana dizindeki dosyaları oluştur
touch run.py
touch requirements.txt
touch config.yaml
touch README.md
touch Dockerfile
touch docker-compose.yml
touch docker-compose-full.yml
touch docker-config.yaml
touch .gitignore
touch Makefile

# Prometheus yapılandırmasını oluştur
touch prometheus/prometheus.yml

echo "Proje yapısı oluşturuldu!"

