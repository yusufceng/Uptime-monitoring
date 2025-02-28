.PHONY: setup run docker-build docker-run docker-compose docker-compose-full clean help

setup:
	@echo "Kurulum başlatılıyor..."
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	mkdir -p data
	mkdir -p prometheus
	cp prometheus/prometheus.yml prometheus/ || true
	@echo "Kurulum tamamlandı. 'make run' ile uygulamayı başlatabilirsiniz."

run:
	@echo "Uygulama başlatılıyor..."
	. venv/bin/activate && python run.py

docker-build:
	@echo "Docker image oluşturuluyor..."
	docker build -t microservice-monitor .
	@echo "Docker image oluşturuldu: microservice-monitor"

docker-run: docker-build
	@echo "Docker container başlatılıyor..."
	mkdir -p data
	docker run -d --name microservice-monitor -p 5000:5000 -v $(PWD)/data:/data -v $(PWD)/config.yaml:/app/config.yaml microservice-monitor
	@echo "Container başlatıldı. http://localhost:5000 adresinden erişebilirsiniz."

docker-compose:
	@echo "Docker Compose ile servisler başlatılıyor..."
	mkdir -p data
	mkdir -p prometheus
	cp prometheus/prometheus.yml prometheus/ || true
	cp docker-config.yaml config.yaml || true
	docker-compose up -d
	@echo "Servisler başlatıldı. http://localhost:5000 adresinden erişebilirsiniz."

docker-compose-full:
	@echo "Docker Compose ile tüm servisler başlatılıyor (demo dahil)..."
	mkdir -p data
	mkdir -p prometheus
	cp prometheus/prometheus.yml prometheus/ || true
	cp docker-config.yaml config.yaml || true
	docker-compose -f docker-compose-full.yml up -d
	@echo "Servisler başlatıldı:"
	@echo "- Monitoring: http://localhost:5000"
	@echo "- Prometheus: http://localhost:9090"
	@echo "- Demo Servis 1: http://localhost:8081"
	@echo "- Demo Servis 2: http://localhost:8082"

clean:
	@echo "Temizleme işlemi başlatılıyor..."
	docker-compose down -v || true
	docker-compose -f docker-compose-full.yml down -v || true
	docker rm -f microservice-monitor prometheus node-exporter demo-service1 demo-service2 || true
	docker rmi microservice-monitor || true
	rm -rf data/*.db
	@echo "Temizleme işlemi tamamlandı."

help:
	@echo "Kullanılabilir komutlar:"
	@echo "  make setup               - Geliştirme ortamını hazırlar"
	@echo "  make run                 - Uygulamayı yerel olarak çalıştırır"
	@echo "  make docker-build        - Docker image oluşturur"
	@echo "  make docker-run          - Docker containerda çalıştırır"
	@echo "  make docker-compose      - Docker Compose ile çalıştırır (monitoring ve prometheus)"
	@echo "  make docker-compose-full - Docker Compose ile tüm servisleri çalıştırır (demo dahil)"
	@echo "  make clean               - Tüm containerları ve volumeleri temizler"
