# OCP Mikro Servis Monitoring

OpenShift (OCP) üzerinde çalışan mikro servisleri izlemek için geliştirilen modern ve kullanıcı dostu bir monitoring aracı. Bu araç, servislerin uptime durumlarını kontrol eder ve Prometheus'tan metrik verilerini toplar.

## Özellikler

- **Servis Uptime İzleme**: Mikro servisleri düzenli olarak kontrol eder ve uptime durumlarını kaydeder
- **Prometheus Entegrasyonu**: Prometheus endpoint'lerinden metrik toplar ve görselleştirir
- **Modern Dashboard**: Tüm servisler ve metrikler için kullanımı kolay, modern bir arayüz
- **Kapsamlı Grafikler**: Yanıt süreleri, uptime yüzdeleri ve Prometheus metrikleri için grafikler
- **Alarm Sistemi**: Servis kesintileri ve anormal metrik değerleri için bildirimler
- **Raporlama**: Servis durumu ve metrikler için özelleştirilebilir raporlar

## Kurulum

### Gereksinimler

- Python 3.8+
- Flask
- SQLite (veya başka bir veritabanı)
- Prometheus (metrik toplama için)

### Kurulum Adımları

1. Depoyu klonlayın:
