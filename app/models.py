from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Text, Boolean, Numeric
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
import enum
from .database import Base

# Finansal hassasiyet için sabitler
# Numeric(18, 4) = 18 toplam basamak, 4 ondalık basamak
# Maksimum: 99,999,999,999,999.9999
PARA_PRECISION = 18
PARA_SCALE = 4
ORAN_SCALE = 6  # Oranlar için daha fazla hassasiyet (örn: 0.130000)

def get_turkey_time():
    return datetime.now(ZoneInfo("Europe/Istanbul"))

class KolPozisyon(str, enum.Enum):
    SAG = "SAG"
    SOL = "SOL"

class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id = Column(Integer, primary_key=True, index=True)
    uye_no = Column(String(20), unique=True, index=True) # 90 ile başlayan özel ID
    tam_ad = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    telefon = Column(String(20))
    sifre = Column(String(255))
    rutbe = Column(String, default="Distribütör")
    profil_resmi = Column(String, nullable=True)

    # Kişisel Bilgiler
    tc_no = Column(String(11), nullable=True)
    dogum_tarihi = Column(DateTime(timezone=True), nullable=True)
    cinsiyet = Column(String(10), nullable=True) # KADIN / ERKEK
    uyelik_turu = Column(String(20), default="Bireysel") # Bireysel / Kurumsal
    
    # Adres Bilgileri
    ulke = Column(String(50), default="Türkiye")
    il = Column(String(50), nullable=True)
    ilce = Column(String(50), nullable=True)
    mahalle = Column(String(100), nullable=True)
    adres = Column(Text, nullable=True)
    posta_kodu = Column(String(10), nullable=True)

    # Vergi Bilgileri (Kurumsal için)
    vergi_dairesi = Column(String(100), nullable=True)
    vergi_no = Column(String(20), nullable=True)
    
    # Bağlantılar
    referans_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    kol = Column(Enum(KolPozisyon), nullable=True)

    # PV - CV Sistemi
    sol_pv = Column(Integer, default=0)
    sag_pv = Column(Integer, default=0)
    toplam_cv = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000"))
    toplam_sol_pv = Column(Integer, default=0)
    toplam_sag_pv = Column(Integer, default=0)

    kayit_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)
    yerlestirme_tarihi = Column(DateTime(timezone=True), nullable=True)

class Ayarlar(Base):
    __tablename__ = "ayarlar"

    id = Column(Integer, primary_key=True, index=True)
    anahtar = Column(String, unique=True, index=True) # Örn: 'referans_orani'
    deger = Column(Numeric(PARA_PRECISION, ORAN_SCALE)) # Örn: 0.400000 - oranlar için daha hassas

class CuzdanHareket(Base):
    __tablename__ = "cuzdan_hareketleri"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    miktar = Column(Numeric(PARA_PRECISION, PARA_SCALE))  # Para miktarı - hassas
    islem_tipi = Column(String) # "REFERANS", "ESLESME", "LIDERLIK"
    aciklama = Column(String)
    tarih = Column(DateTime(timezone=True), default=get_turkey_time)

class IletisimMesaji(Base):
    __tablename__ = "iletisim_mesajlari"

    id = Column(Integer, primary_key=True, index=True)
    ad_soyad = Column(String)
    email = Column(String)
    konu = Column(String)
    mesaj = Column(Text)
    takip_no = Column(String, unique=True, index=True)
    tarih = Column(DateTime(timezone=True), default=get_turkey_time)
    durum = Column(String, default="Beklemede") # Beklemede, Okundu, Cevaplandı

class NesilAyari(Base):
    __tablename__ = "nesil_ayarlari"
    id = Column(Integer, primary_key=True, index=True)
    nesil_no = Column(Integer)  # 1, 2, 3...
    oran = Column(Numeric(PARA_PRECISION, ORAN_SCALE))  # 0.100000, 0.050000... - oran hassasiyeti

class Rutbe(Base):
    __tablename__ = "rutbeler"
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), nullable=False, unique=True)  # Rütbe adı
    sol_pv = Column(Integer, default=0)  # Sol kol PV gereksinimi
    sag_pv = Column(Integer, default=0)  # Sağ kol PV gereksinimi
    sira = Column(Integer, default=0)  # Görüntüleme sırası
    renk = Column(String(20), default="gray")  # Tema rengi (gray, blue, green, yellow, orange, red, purple, pink, indigo)

class SiteAyarlari(Base):
    __tablename__ = "site_ayarlari"

    id = Column(Integer, primary_key=True, index=True)
    site_basligi = Column(String(255), default="BestWork")
    min_cekime_limiti = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("500.0000"))
    
    # SEO Ayarları
    seo_aciklama = Column(Text, default="BestWork E-Ticaret ve Network Marketing Sistemi")
    seo_anahtar_kelimeler = Column(Text, default="e-ticaret, network marketing, kazanç sistemi")
    seo_yazar = Column(String(100), default="BestSoft")

    # Google Analytics
    google_analytics_kodu = Column(Text, nullable=True)

    # Footer Ayarları
    footer_baslik = Column(String, default="BestWork")
    footer_aciklama = Column(Text, default="Premium alışveriş deneyimini yeniden tanımlıyoruz. Kalite, güven ve estetik bir arada.")
    footer_copyright = Column(String, default="© 2025 BestWork. Tüm hakları saklıdır.")
    
    # İletişim vs
    iletisim_adres = Column(Text, nullable=True)
    iletisim_email = Column(String, nullable=True)
    iletisim_telefon = Column(String, nullable=True)
    iletisim_harita = Column(Text, nullable=True)

    # Sosyal Medya
    sosyal_facebook = Column(String, nullable=True)
    sosyal_twitter = Column(String, nullable=True)
    sosyal_instagram = Column(String, nullable=True)
    sosyal_linkedin = Column(String, nullable=True)
    sosyal_youtube = Column(String, nullable=True)

class Slider(Base):
    __tablename__ = "sliders"
    
    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(200), nullable=True)
    aciklama = Column(Text, nullable=True)
    resim_yolu = Column(String(500), nullable=False) # WebP path
    link = Column(String(500), nullable=True)
    sira = Column(Integer, default=0)
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)

class Sertifika(Base):
    __tablename__ = "sertifikalar_tablosu"
    
    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(200), nullable=True)
    aciklama = Column(String(500), nullable=True)
    resim_yolu = Column(String(500), nullable=False)
    sira = Column(Integer, default=0)
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)


class Varis(Base):
    __tablename__ = "varisler"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"))
    ad_soyad = Column(String(100), nullable=False)
    tc = Column(String(11), nullable=False)
    telefon = Column(String(20))
    email = Column(String(100))
    yakinlik = Column(String(50))
    adres = Column(Text)
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)

# E-TİCARET VE ÜRÜN YÖNETİMİ MODÜLÜ (MODÜL 3)

class Marka(Base):
    __tablename__ = "markalar"
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), nullable=False)
    aciklama = Column(Text)
    resim_url = Column(String(500))
    aktif = Column(Boolean, default=True)

class UrunGrup(Base):
    __tablename__ = "urun_gruplari"
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), nullable=False)
    aktif = Column(Boolean, default=True)

class Depo(Base):
    __tablename__ = "depolar"
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), nullable=False)
    adres = Column(Text)
    yetkili = Column(String(100))
    aktif = Column(Boolean, default=True)

class DepoRaf(Base):
    __tablename__ = "depo_raflari"
    id = Column(Integer, primary_key=True, index=True)
    depo_id = Column(Integer, ForeignKey("depolar.id"))
    kod = Column(String(50), nullable=False) # A1-01 gibi
    aciklama = Column(String(200))

class Kategori(Base):
    __tablename__ = "kategoriler"
    
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), nullable=False)
    ust_kategori_id = Column(Integer, ForeignKey("kategoriler.id"), nullable=True) # Alt kategori desteği
    aciklama = Column(Text)
    resim_url = Column(String(500))
    seo_baslik = Column(String(200)) # SEO
    seo_aciklama = Column(Text)      # SEO
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)

class Urun(Base):
    __tablename__ = "urunler"
    
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(200), nullable=False, index=True)
    sku = Column(String(50), unique=True, index=True) # Stok Kodu
    barkod = Column(String(50), unique=True, index=True)
    
    # İlişkiler
    kategori_id = Column(Integer, ForeignKey("kategoriler.id"))
    marka_id = Column(Integer, ForeignKey("markalar.id"), nullable=True)
    grup_id = Column(Integer, ForeignKey("urun_gruplari.id"), nullable=True)
    
    # Fiyatlandırma - Decimal hassasiyetinde
    maliyet = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000"))
    katalog_fiyati = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000")) # Liste Fiyatı
    fiyat = Column(Numeric(PARA_PRECISION, PARA_SCALE), nullable=False) # Satış Fiyatı
    indirimli_fiyat = Column(Numeric(PARA_PRECISION, PARA_SCALE), nullable=True)
    uye_alis_fiyati = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000")) # Üyelere özel fiyat
    kdv_orani = Column(Integer, default=20) # %1, %10, %20

    # Stok Kargo
    stok = Column(Integer, default=0)
    kritik_stok = Column(Integer, default=5)
    desi = Column(Numeric(10, 3), default=Decimal("0.000"))  # Kargo için desi
    agirlik = Column(Numeric(10, 3), default=Decimal("0.000"))  # Ağırlık
    agirlik_birimi = Column(String(10), default="kg")
    
    # Açıklamalar
    kisa_aciklama = Column(Text)
    aciklama = Column(Text)
    
    # Network Marketing
    pv_degeri = Column(Integer, default=0)
    cv_degeri = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000")) # Commission Volume
    referans_primi_orani = Column(Numeric(PARA_PRECISION, ORAN_SCALE), default=Decimal("0.000000")) # Bu ürüne özel referans primi
    
    # Görseller
    resim_url = Column(String(500))
    # Ek resimler için ayrı tablo gerekebilir ama şimdilik JSON veya string tutabiliriz
    galeri = Column(Text, nullable=True) # JSON array string
    
    # SEO
    seo_baslik = Column(String(200))
    seo_aciklama = Column(Text)
    seo_etiketler = Column(String(200))
    
    aktif = Column(Boolean, default=True)
    vitrin = Column(Boolean, default=False) # Vitrinde göster
    yeni = Column(Boolean, default=True)    # Yeni ürün etiketi
    
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)
    guncelleme_tarihi = Column(DateTime(timezone=True), default=get_turkey_time, onupdate=get_turkey_time)

class UrunVaryasyon(Base):
    __tablename__ = "urun_varyasyonlari"
    id = Column(Integer, primary_key=True, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"))
    ad = Column(String(100)) # Örn: Kırmızı - XL
    sku = Column(String(50))
    stok = Column(Integer, default=0)
    fiyat_farki = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000"))

class UrunYorum(Base):
    __tablename__ = "urun_yorumlari"
    id = Column(Integer, primary_key=True, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"))
    user_id = Column(Integer, ForeignKey("kullanicilar.id"))
    puan = Column(Integer) # 1-5
    yorum = Column(Text)
    onayli = Column(Boolean, default=False)
    tarih = Column(DateTime(timezone=True), default=get_turkey_time)

class AlisFaturasi(Base):
    __tablename__ = "alis_faturalari"
    id = Column(Integer, primary_key=True, index=True)
    tedarikci_adi = Column(String(100))
    fatura_no = Column(String(50))
    fatura_tarihi = Column(DateTime)
    vade_tarihi = Column(DateTime, nullable=True)
    toplam_tutar = Column(Numeric(PARA_PRECISION, PARA_SCALE))  # Fatura tutarı - hassas
    aciklama = Column(Text)
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)

class AlisFaturasiKalem(Base):
    __tablename__ = "alis_faturasi_kalemleri"
    id = Column(Integer, primary_key=True, index=True)
    fatura_id = Column(Integer, ForeignKey("alis_faturalari.id"))
    urun_id = Column(Integer, ForeignKey("urunler.id"))
    adet = Column(Integer)
    birim_fiyat = Column(Numeric(PARA_PRECISION, PARA_SCALE))  # Birim fiyat - hassas
    toplam_fiyat = Column(Numeric(PARA_PRECISION, PARA_SCALE)) # adet * birim_fiyat - hassas

class Sepet(Base):
    __tablename__ = "sepetler"
    
    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"))
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)
    guncelleme_tarihi = Column(DateTime(timezone=True), default=get_turkey_time, onupdate=get_turkey_time)

class SepetUrun(Base):
    __tablename__ = "sepet_urunler"
    
    id = Column(Integer, primary_key=True, index=True)
    sepet_id = Column(Integer, ForeignKey("sepetler.id"))
    urun_id = Column(Integer, ForeignKey("urunler.id"))
    adet = Column(Integer, default=1)
    ekleme_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)

class Siparis(Base):
    __tablename__ = "siparisler"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"))
    toplam_tutar = Column(Numeric(PARA_PRECISION, PARA_SCALE), nullable=False)  # Sipariş tutarı - hassas
    toplam_cv = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000"))  # CV - hassas
    toplam_pv = Column(Integer, default=0)
    durum = Column(String(50), default="BEKLEMEDE")  # BEKLEMEDE, ONAYLANDI, KARGODA, TESLIM_EDILDI
    adres = Column(Text)
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)

class SiparisUrun(Base):
    __tablename__ = "siparis_urunler"

    id = Column(Integer, primary_key=True, index=True)
    siparis_id = Column(Integer, ForeignKey("siparisler.id"))
    urun_id = Column(Integer, ForeignKey("urunler.id"))
    urun_adi = Column(String(200))
    adet = Column(Integer)
    birim_fiyat = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000"))  # Birim fiyat - hassas
    cv_degeri = Column(Numeric(PARA_PRECISION, PARA_SCALE), default=Decimal("0.0000"))  # CV - hassas
    pv_degeri = Column(Integer)
class BankaBilgisi(Base):
    __tablename__ = "banka_bilgileri"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("kullanicilar.id"))
    hesap_sahibi = Column(String(100))
    banka_adi = Column(String(100))
    iban = Column(String(34))
    swift_kodu = Column(String(20), nullable=True)
    guncelleme_tarihi = Column(DateTime(timezone=True), default=get_turkey_time, onupdate=get_turkey_time)

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_adi = Column(String, unique=True, index=True)
    sifre = Column(String)
    olusturma_tarihi = Column(DateTime(timezone=True), default=get_turkey_time)
