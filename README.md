# BestWork Network Marketing Sistemi

Modern, ölçeklenebilir ve güvenli Multi-Level Marketing (MLM) platformu. FastAPI, PostgreSQL ve Redis ile geliştirilmiştir.

## 🎯 Öne Çıkan Özellikler

- 🌳 **Binary MLM Ağaç Yapısı** - Sol/sağ kol mantığıyla sınırsız derinlik
- 💰 **Dinamik Komisyon Sistemi** - Matching bonus, nesil gelirleri, referans primleri
- 🏆 **Tam Yönetilebilir Rütbe Sistemi** - Admin panelinden CRUD işlemleri
- 🛒 **E-Ticaret Entegrasyonu** - PV/CV bazlı ürün satışı
- 🎨 **Material Design 3 Arayüz** - Modern, responsive admin paneli
- 🔐 **JWT Token Auth** - Güvenli oturum yönetimi
- ⚡ **Redis Cache** - Hızlı veri erişimi ve performans

## 📦 Teknoloji Stack'i

- **Backend:** FastAPI 0.115+
- **Database:** PostgreSQL 14+
- **Cache:** Redis 7+
- **Frontend:** Jinja2 Templates, Tailwind CSS, Alpine.js
- **Auth:** JWT, Bcrypt

## Sürüm Geçmişi

### v26.1.10 (21.01.2026) - Dinamik Rütbe Sistemi ve Git Entegrasyonu

Bu sürüm, MLM sistemine tam yönetilebilirlik getiren **dinamik rütbe yönetimi** ve **version control** entegrasyonunu içerir.

#### 1. Dinamik Rütbe Yönetim Sistemi (Admin Panel)
**Önceki Durum:** Rütbeler `utils.py` dosyasında hardcoded liste olarak tanımlıydı. Değişiklik için kod düzenleme gerekiyordu.

**Yeni Yapı:**
- **Database Model:** `Rutbe` tablosu eklendi (`models.py:102-109`)
  - `ad`: Rütbe adı (örn: "Altın Distribütör")
  - `sol_pv`: Sol kol PV gereksinimi
  - `sag_pv`: Sağ kol PV gereksinimi
  - `sira`: Görüntüleme sırası
  - `renk`: Tema rengi (9 renk seçeneği)

- **Backend Routes:** CRUD işlemleri tam olarak implemente edildi
  - `GET /admin/mlm/rutbe` - Rütbeleri listele
  - `POST /admin/mlm/rutbe/ekle` - Yeni rütbe ekle
  - `POST /admin/mlm/rutbe/guncelle/{id}` - Rütbe güncelle
  - `POST /admin/mlm/rutbe/sil/{id}` - Rütbe sil

- **Frontend Özellikleri:**
  - **Inline Editing:** Rütbeleri tıklayarak düzenle
  - **Modal Ekleme:** Modern, Alpine.js destekli ekleme formu
  - **Silme Onayı:** Güvenlik için çift onay modalı
  - **Renk Seçimi:** 9 farklı tema rengi (gray, blue, green, yellow, orange, red, purple, pink, indigo)
  - **Gerçek Zamanlı Güncelleme:** Başarı mesajları ve otomatik sayfa yenileme

- **Migration:** Varsayılan 9 rütbe otomatik yükleme scripti (`migrate_rutbe.py`)

#### 2. Admin Panel - MLM Modül 4 Genişletmesi
- **Modül Yapısı:** 6 alt modül tam entegre
  1. MLM Ayarları (referans bonusu, hoşgeldin bonusu, kayıt PV/CV)
  2. Komisyon Oranları (kısa kol, referans oranı)
  3. Nesil Gelirleri (1-10. nesil oranları)
  4. Bonus Sistemleri (özet görünüm)
  5. **Rütbe Sistemi** (yeni - tam yönetilebilir)
  6. Ağaç Görünümü (binary tree visualization)

- **UI/UX Tutarlılığı:**
  - Tüm MLM sayfaları Material Design 3 standardına uygun
  - `admin_navbar.html` include ile tek navbar
  - Tailwind config ile MD3 color palette
  - Alpine.js ile reactive components

#### 3. Git Version Control Entegrasyonu
- **Repository:** https://github.com/mgatr/bestwork-bestsoft
- **Initial Commit:** 89 dosya, 16,118 satır kod
- **Güvenlik:**
  - `.gitignore` eklendi (`.env`, `.venv/`, `__pycache__/`, vb.)
  - SSH key oluşturuldu ve GitHub'a eklendi
  - Git credentials güvenli şekilde saklandı

#### 4. Dosya Yapısı İyileştirmeleri
```
app/
├── models.py              # +Rutbe model (line 102-109)
├── routers/
│   └── admin.py          # +Rütbe CRUD routes (line 867-950)
templates/
└── admin_mlm_rutbe.html  # Tamamen yeniden yazıldı (334 satır)
migrate_rutbe.py          # Yeni migration script
.gitignore                # Repository güvenliği
```

#### Upgrade Talimatları
```bash
# 1. Güncel kodu çekin
git pull origin main

# 2. Rütbe tablosunu oluşturun
source .venv/bin/activate  # veya venv/Scripts/activate (Windows)
python migrate_rutbe.py

# 3. Sunucuyu yeniden başlatın (otomatik reload yapıyorsa gerek yok)
uvicorn app.main:app --reload
```

#### Test Edildi
- ✅ Rütbe ekleme/düzenleme/silme (9 rütbe test edildi)
- ✅ Tüm MLM modülleri erişilebilir ve çalışıyor
- ✅ Admin paneli tutarlı MD3 tasarımda
- ✅ GitHub push/pull başarılı

---

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
