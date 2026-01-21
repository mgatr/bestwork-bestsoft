from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, Annotated
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

# Decimal için yardımcı fonksiyon
def quantize_money(value: Decimal) -> Decimal:
    """Para değerlerini 4 ondalık basamağa yuvarla"""
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

# Kol seçimi sadece bu iki seçenekten biri olabilir
class KolSecimi(str, Enum):
    SAG = "SAG"
    SOL = "SOL"

# Yeni üye kayıt olurken gönderilecek veriler
class KullaniciKayit(BaseModel):
    tam_ad: str
    email: EmailStr
    telefon: str
    sifre: str
    referans_id: int  # Davet eden kişi ID
    
    # Opsiyonel hale getiriyoruz, formda yoksa otomatik atanacak
    uye_no: Optional[str] = None  # Otomatik oluşturulacak
    parent_id: Optional[int] = None
    kol: Optional[KolSecimi] = None

    # Yeni Alanlar
    tc_no: Optional[str] = None
    dogum_tarihi: Optional[str] = None # String olarak alıp backend'de çevirebiliriz
    cinsiyet: Optional[str] = "KADIN"
    uyelik_turu: Optional[str] = "Bireysel"
    ulke: Optional[str] = "Türkiye"
    il: Optional[str] = None
    ilce: Optional[str] = None
    mahalle: Optional[str] = None
    adres: Optional[str] = None
    posta_kodu: Optional[str] = None
    vergi_dairesi: Optional[str] = None
    vergi_no: Optional[str] = None

# API'den geri dönecek (Cevap) verisi
class KullaniciCevap(BaseModel):
    id: int
    tam_ad: str
    email: str
    parent_id: Optional[int]
    kol: Optional[str]
    sol_pv: int
    sag_pv: int

    class Config:
        from_attributes = True

class AgacYapisi(BaseModel):
    id: int
    tam_ad: str
    kol: Optional[str]
    sol_pv: int
    sag_pv: int
    alt_ekip: list["AgacYapisi"] = [] # Kendini tekrar eden yapı

    class Config:
        from_attributes = True

class DashboardOzet(BaseModel):
    id: int
    tam_ad: str
    toplam_cv: Decimal  # Kazanılan toplam para - Decimal hassasiyetinde
    mevcut_sol_pv: int
    mevcut_sag_pv: int
    toplam_sol_ekip: int
    toplam_sag_ekip: int

    model_config = ConfigDict(from_attributes=True)

class IletisimCreate(BaseModel):
    ad_soyad: str
    email: EmailStr
    konu: str
    mesaj: str

    class Config:
        from_attributes = True

class AyarGuncelle(BaseModel):
    anahtar: str
    deger: Decimal  # Ayar değeri - Decimal hassasiyetinde

    model_config = ConfigDict(from_attributes=True)

class AyarCevap(AyarGuncelle):
    pass

from datetime import datetime

class CuzdanHareketCevap(BaseModel):
    id: int
    miktar: Decimal  # Para miktarı - Decimal hassasiyetinde
    islem_tipi: str
    aciklama: str
    tarih: datetime

    model_config = ConfigDict(from_attributes=True)

class VarisBase(BaseModel):
    ad_soyad: str
    tc: str
    telefon: Optional[str] = None
    email: Optional[EmailStr] = None
    yakinlik: Optional[str] = None
    adres: Optional[str] = None

class VarisCreate(VarisBase):
    pass

class VarisUpdate(BaseModel):
    ad_soyad: Optional[str] = None
    tc: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[EmailStr] = None
    yakinlik: Optional[str] = None
    adres: Optional[str] = None

class VarisCevap(VarisBase):
    id: int
    kullanici_id: int
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True

# E-TİCARET SCHEMAS

class KategoriBase(BaseModel):
    ad: str
    aciklama: Optional[str] = None
    resim_url: Optional[str] = None
    aktif: bool = True

class KategoriOlustur(KategoriBase):
    pass

class KategoriCevap(KategoriBase):
    id: int
    olusturma_tarihi: datetime
    
    class Config:
        from_attributes = True

class UrunBase(BaseModel):
    ad: str
    aciklama: Optional[str] = None
    fiyat: Decimal  # Fiyat - Decimal hassasiyetinde
    indirimli_fiyat: Optional[Decimal] = None  # İndirimli fiyat - Decimal
    stok: int = 0
    kategori_id: Optional[int] = None
    resim_url: Optional[str] = None
    pv_degeri: int = 0
    aktif: bool = True

class UrunOlustur(UrunBase):
    pass

class UrunGuncelle(BaseModel):
    ad: Optional[str] = None
    aciklama: Optional[str] = None
    fiyat: Optional[Decimal] = None  # Fiyat - Decimal hassasiyetinde
    indirimli_fiyat: Optional[Decimal] = None  # İndirimli fiyat - Decimal
    stok: Optional[int] = None
    kategori_id: Optional[int] = None
    resim_url: Optional[str] = None
    pv_degeri: Optional[int] = None
    aktif: Optional[bool] = None

class UrunCevap(UrunBase):
    id: int
    olusturma_tarihi: datetime

    model_config = ConfigDict(from_attributes=True)

class SepetUrunu(BaseModel):
    urun_id: int
    adet: int = 1

class SepetCevap(BaseModel):
    id: int
    urunler: list = []
    toplam_fiyat: Decimal = Decimal("0.0000")  # Toplam fiyat - Decimal hassasiyetinde
    toplam_adet: int = 0

    model_config = ConfigDict(from_attributes=True)

class SiparisOlustur(BaseModel):
    adres: str

class SiparisCevap(BaseModel):
    id: int
    kullanici_id: int
    toplam_tutar: Decimal  # Sipariş tutarı - Decimal hassasiyetinde
    toplam_pv: int
    durum: str
    adres: str
    olusturma_tarihi: datetime

    model_config = ConfigDict(from_attributes=True)