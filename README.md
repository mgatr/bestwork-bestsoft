# BestWork Network Marketing Sistemi

## Sürüm Geçmişi

### v26.1.9 (17.01.2026) - Kritik Güvenlik Yaması ve Veritabanı Düzeltmesi

Bu sürüm, sistemdeki kritik güvenlik açıklarını kapatmış ve veritabanı sorgu hatalarını gidermiştir. **Tüm production ortamlarının derhal güncellenmesi önerilir.**

#### 1. Veritabanı Sorgu Düzeltmesi (Kritik Bug Fix)
*   **Tablo İsmi Uyumsuzluğu:** `crud.py` dosyasındaki 16 adet raw SQL sorgusunda tablo ismi `kullanici` (tekil) olarak yazılmıştı, ancak SQLAlchemy modelinde `__tablename__ = "kullanicilar"` (çoğul) tanımlıydı.
*   **Etkilenen Fonksiyonlar:** `ekip_sayisini_bul_cte()`, `ust_sponsor_zincirini_getir_cte()` ve ekonomi tetikleme fonksiyonları.
*   **Sonuç:** Dashboard sayfası (`/panel/{id}`) ve MLM ağaç hesaplamaları artık sorunsuz çalışıyor.

#### 2. Güvenlik: Backdoor Temizliği (`app/utils.py`)
*   **Kaldırılan Kod:** `verify_password()` fonksiyonundaki düz metin şifre karşılaştırması (`if plain_password == hashed_password`) tamamen kaldırıldı.
*   **Yeni Davranış:** Artık sadece **bcrypt hash doğrulaması** yapılıyor. Düz metin şifreler kabul edilmiyor.
*   **Güvenlik Etkisi:** Potansiyel kimlik doğrulama bypass açığı kapatıldı.

#### 3. Güvenlik: Şifre Hashleme Garantisi (`app/crud.py`)
*   **`sifre_guncelle()` Fonksiyonu:** Parametre olarak düz metin şifre alıp, fonksiyon içinde `bcrypt` ile hashleyerek kaydediyor.
*   **Defense in Depth:** Şifre asla düz metin olarak veritabanına yazılamaz - fonksiyon seviyesinde garanti altına alındı.

#### 4. Güvenlik: SECRET_KEY Zorunluluğu (`app/config.py`)
*   **Varsayılan Değer Kaldırıldı:** Hardcoded `SECRET_KEY` tamamen silindi.
*   **Yeni Davranış:** `.env` dosyasında `SECRET_KEY` tanımlı değilse uygulama `RuntimeError` fırlatarak başlamayı reddediyor.
*   **Kullanıcı Talimatı:** Güvenli anahtar oluşturmak için `openssl rand -hex 32` komutu önerildi.

#### 5. Güvenlik: JWT Hata Yönetimi İyileştirmesi
*   **Logging Altyapısı:** `bestwork.security` logger'ı eklendi.
*   **Middleware (`app/main.py`):**
    *   `except: pass` → `except Exception as e: logger.error(...)` olarak değiştirildi.
    *   Debug amaçlı `print()` çağrıları kaldırıldı.
    *   Geçersiz kullanıcı ID'leri ve bulunamayan kullanıcılar loglanıyor.
*   **Token Decode (`app/utils.py`):**
    *   Süresi dolmuş token: `logger.info("JWT token süresi dolmuş")`
    *   Geçersiz token: `logger.warning("JWT decode hatası: ...")`

#### Güncelleme Talimatları
```bash
# 1. Kodu güncelleyin
git pull origin main

# 2. .env dosyasında SECRET_KEY olduğundan emin olun
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env

# 3. Uygulamayı yeniden başlatın
uvicorn app.main:app --reload
```

---

### v26.1.8 (16.01.2026) - Material Design 3 (Android S) Revizyonu ve Kategori Görsel Optimizasyonu

Bu sürüm, yönetim panelini modern **Google Material Design 3 (MD3)** standartlarına taşımış ve "Ürünler & Kategoriler" modülünde görsel deneyimi en üst seviyeye çıkarmıştır.

#### 1. Admin Arayüzü: Tam Kapsamlı MD3 Dönüşümü
Tüm Ürün Yönetimi modülü, "Admin SEO" sayfasındaki referans tasarım (Lavender/Mor tema) baz alınarak yeniden kodlandı:
*   **Tasarım Dili:** HTML yapısı `{% extends %}` kalıbından çıkarılarak, her sayfa için özel Tailwind konfigürasyonu içeren bağımsız yapılara dönüştürüldü.
*   **Renk Paleti:** Özel tanımlanmış MD3 renkleri (`#F3EDF7` arka plan, `#6750A4` primary, `#FEF7FF` surface) ile tam uyum sağlandı.
*   **Sayfa Revizyonları:**
    *   **Ürün Listesi:** Tablolar gölgeli kart yapısına (Elevation-1) taşındı, "PV/CV" değerleri renkli rozetlerle (Badge) belirginleştirildi.
    *   **Ürün Ekleme:** Formlar, kavisli köşelere (`rounded-[24px]`) ve MD3 input stillerine (altı çizgili, animasyonlu label) kavuştu.
    *   **Kategoriler & Markalar:** Sayfalar "Split View" (Bölünmüş Görünüm) yapısına geçirilerek, sol tarafta Ekleme Formu, sağ tarafta Liste/Ağaç yapısı sunuldu.

#### 2. Kategori Görsel Yönetimi ve WebP Dönüşümü
*   **WebP Standardı:** Yüklenen tüm kategori görselleri, formatı ne olursa olsun (JPG/PNG), performans için otomatik olarak **WebP** formatına dönüştürülüyor.
*   **Düzenleme Yeteneği:** Kategoriler için "Resim Güncelleme" yeteneği eklendi. Admin panelindeki listeden "Düzenle" (Kalem ikonu) butonuna basılarak görsel değiştirilebilir hale geldi.
*   **Sunucu Tarafı:** `admin_products.py` üzerindeki boş placeholder fonksiyonlar, gerçek resim işleme (Pillow/PIL), boyutlandırma (800x800px) ve kaydetme mantıklarıyla dolduruldu.

#### 3. Frontend (Anasayfa) İyileştirmeleri
*   **Dinamik Kategori İkonları:** Anasayfadaki "Kategorilere Göz At" bölümü, statik emojiler yerine veritabanından gelen gerçek kategori görsellerini göstermeye başladı.
*   **UI Hassas Ayarları:**
    *   Kategori ikonları **40x40px** boyutunda sabitlendi.
    *   Görseller kapsayıcı içine dolgu (padding) ile ortalanarak daha kibar bir görünüm elde edildi.
    *   Tüm kategori listesi sayfa ortasına (`justify-center`) hizalandı.

### v26.1.7 (12.01.2026) - Python 3.12 Uyumluluğu ve Gelişmiş Kurulum Yöneticisi

Bu sürüm, altyapıyı modernize ederek en güncel Python sürümleriyle tam uyumluluk sağlar ve kurulum süreçlerini kolaylaştırır.

#### 1. Altyapı Modernizasyonu (Python 3.12+)
*   **Bağımlılık Güncellemesi:** Eski `passlib` kütüphanesi kaldırılarak, modern Python sürümleriyle uyumlu saf `bcrypt` implementasyonuna geçildi.
*   **Şifreleme:** Kullanıcı şifreleme algoritmaları güncel güvenlik standartlarına yükseltildi.

#### 2. Yeni Kurulum Yöneticisi (Setup CLI)
*   **Gelişmiş Arayüz:** Kurulum paneli renkli, adım adım ilerleyen ve kullanıcı dostu bir terminal arayüzüne kavuştu.
*   **Akıllı Algılama:** Sistem otomatik olarak sanal ortamı, Python sürümünü ve eksik paketleri algılar.
*   **Hata Yönetimi:** Kurulum sırasındaki hatalar (internet kesintisi vb.) yakalanarak kullanıcıya çözüm önerileri sunulur.

#### 3. UX İyileştirmeleri
*   **Otomatik Başlangıç:** Sunucu başlatıldığında tarayıcı artık doğrudan anasayfaya (`/`) yönleniyor.
*   **Hızlı Kurulum:** "Hızlı Kurulum" ve "Onarım" modları ayrıştırıldı.

---

## 🚀 Gelecek Planlaması (Roadmap)
Bu maddeler sistemin büyüme stratejisine göre sıraya alınmıştır:

- [ ] **Asenkron Puan Dağıtımı (Celery + Redis):** Anlık 10.000+ işlem hacmine ulaşıldığında, puan hesaplamalarının arka plana (Background Worker) taşınması.
- [ ] **Mobil Uygulama API:** React Native veya Flutter entegrasyonu için REST API endpoint'lerinin genişletilmesi.
- [ ] **Çoklu Dil Desteği (i18n):** İngilizce, Almanca ve Arapça dil seçeneklerinin eklenmesi.
