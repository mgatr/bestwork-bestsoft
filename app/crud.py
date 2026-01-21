"""
CRUD (Repository) Layer - Sadece veritabanı işlemleri yapar.
İş mantığı servis katmanına taşınmıştır.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models, schemas
import uuid
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException


# === SAF CRUD OPERASYONLARI ===

# ---- Kullanıcı İşlemleri ----
def get_user(db: Session, user_id: int):
    return db.query(models.Kullanici).filter(models.Kullanici.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.Kullanici).filter(models.Kullanici.email == email).first()

def get_user_by_phone(db: Session, phone: str):
    return db.query(models.Kullanici).filter(models.Kullanici.telefon == phone).first()

def get_user_by_tc_no(db: Session, tc_no: str):
    return db.query(models.Kullanici).filter(models.Kullanici.tc_no == tc_no).first()

def get_user_by_uye_no(db: Session, uye_no: str):
    return db.query(models.Kullanici).filter(models.Kullanici.uye_no == uye_no).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Kullanici).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.KullaniciKayit):
    """Sadece kullanıcı oluşturur, iş mantığı içermez."""
    yeni_uye = models.Kullanici(
        tam_ad=user.tam_ad,
        email=user.email,
        telefon=user.telefon,
        sifre=user.sifre,
        referans_id=user.referans_id,
        parent_id=None,
        kol=None,
        uye_no=user.uye_no if hasattr(user, 'uye_no') else None,
        tc_no=user.tc_no,
        dogum_tarihi=user.dogum_tarihi,
        cinsiyet=user.cinsiyet,
        uyelik_turu=user.uyelik_turu,
        ulke=user.ulke,
        il=user.il,
        ilce=user.ilce,
        mahalle=user.mahalle,
        adres=user.adres,
        posta_kodu=user.posta_kodu,
        vergi_dairesi=user.vergi_dairesi,
        vergi_no=user.vergi_no
    )
    db.add(yeni_uye)
    db.commit()
    db.refresh(yeni_uye)
    return yeni_uye

def update_user(db: Session, user_id: int, update_data: dict):
    user = db.query(models.Kullanici).filter(models.Kullanici.id == user_id).first()
    if user:
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.Kullanici).filter(models.Kullanici.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def generate_unique_member_number(db: Session):
    """Benzersiz üye numarası oluşturur."""
    while True:
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(7)])
        aday_no = "90" + suffix
        
        mevcut = db.query(models.Kullanici).filter(models.Kullanici.uye_no == aday_no).first()
        if not mevcut:
            return aday_no

# ---- Kategori İşlemleri ----
def create_category(db: Session, kategori: schemas.KategoriOlustur):
    db_kategori = models.Kategori(**kategori.dict())
    db.add(db_kategori)
    db.commit()
    db.refresh(db_kategori)
    return db_kategori

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Kategori).filter(models.Kategori.aktif == True).offset(skip).limit(limit).all()

def get_category(db: Session, kategori_id: int):
    return db.query(models.Kategori).filter(models.Kategori.id == kategori_id).first()

def update_category(db: Session, kategori_id: int, update_data: dict):
    kategori = db.query(models.Kategori).filter(models.Kategori.id == kategori_id).first()
    if kategori:
        for key, value in update_data.items():
            setattr(kategori, key, value)
        db.commit()
        db.refresh(kategori)
    return kategori

def delete_category(db: Session, kategori_id: int):
    kategori = db.query(models.Kategori).filter(models.Kategori.id == kategori_id).first()
    if kategori:
        db.delete(kategori)
        db.commit()
        return True
    return False

# ---- Ürün İşlemleri ----
def create_product(db: Session, urun: schemas.UrunOlustur):
    db_urun = models.Urun(**urun.dict())
    db.add(db_urun)
    db.commit()
    db.refresh(db_urun)
    return db_urun

def get_products(db: Session, kategori_id: int = None, skip: int = 0, limit: int = 100):
    sorgu = db.query(models.Urun).filter(models.Urun.aktif == True)
    if kategori_id:
        sorgu = sorgu.filter(models.Urun.kategori_id == kategori_id)
    return sorgu.offset(skip).limit(limit).all()

def get_product(db: Session, urun_id: int):
    return db.query(models.Urun).filter(models.Urun.id == urun_id).first()

def update_product(db: Session, urun_id: int, update_data: dict):
    urun = db.query(models.Urun).filter(models.Urun.id == urun_id).first()
    if urun:
        for key, value in update_data.items():
            setattr(urun, key, value)
        db.commit()
        db.refresh(urun)
    return urun

def delete_product(db: Session, urun_id: int):
    urun = db.query(models.Urun).filter(models.Urun.id == urun_id).first()
    if urun:
        db.delete(urun)
        db.commit()
        return True
    return False

# ---- Sepet İşlemleri ----
def get_or_create_cart(db: Session, kullanici_id: int):
    sepet = db.query(models.Sepet).filter(models.Sepet.kullanici_id == kullanici_id).first()
    if not sepet:
        sepet = models.Sepet(kullanici_id=kullanici_id)
        db.add(sepet)
        db.commit()
        db.refresh(sepet)
    return sepet

def add_to_cart(db: Session, kullanici_id: int, urun_id: int, adet: int = 1):
    sepet = get_or_create_cart(db, kullanici_id)
    
    mevcut = db.query(models.SepetUrun).filter(
        models.SepetUrun.sepet_id == sepet.id,
        models.SepetUrun.urun_id == urun_id
    ).first()
    
    if mevcut:
        mevcut.adet += adet
    else:
        yeni_sepet_urun = models.SepetUrun(sepet_id=sepet.id, urun_id=urun_id, adet=adet)
        db.add(yeni_sepet_urun)
    
    db.commit()
    return sepet

def get_cart_details(db: Session, kullanici_id: int):
    sepet = get_or_create_cart(db, kullanici_id)
    
    sepet_urunler = db.query(models.SepetUrun).filter(models.SepetUrun.sepet_id == sepet.id).all()
    
    urunler = []
    toplam_fiyat = 0
    toplam_adet = 0
    
    for sepet_urun in sepet_urunler:
        urun = db.query(models.Urun).filter(models.Urun.id == sepet_urun.urun_id).first()
        if urun:
            fiyat = urun.indirimli_fiyat if urun.indirimli_fiyat else urun.fiyat
            urunler.append({
                "id": sepet_urun.id,
                "urun": urun,
                "adet": sepet_urun.adet,
                "toplam": fiyat * sepet_urun.adet
            })
            toplam_fiyat += fiyat * sepet_urun.adet
            toplam_adet += sepet_urun.adet
    
    return {
        "id": sepet.id,
        "urunler": urunler,
        "toplam_fiyat": toplam_fiyat,
        "toplam_adet": toplam_adet
    }

def remove_from_cart(db: Session, kullanici_id: int, sepet_urun_id: int):
    sepet = get_or_create_cart(db, kullanici_id)
    
    sepet_urun = db.query(models.SepetUrun).filter(
        models.SepetUrun.id == sepet_urun_id,
        models.SepetUrun.sepet_id == sepet.id
    ).first()
    
    if sepet_urun:
        db.delete(sepet_urun)
        db.commit()
    
    return True

def clear_cart(db: Session, kullanici_id: int):
    sepet = get_or_create_cart(db, kullanici_id)
    db.query(models.SepetUrun).filter(models.SepetUrun.sepet_id == sepet.id).delete()
    db.commit()
    return True

# ---- Sipariş İşlemleri ----
def create_order(db: Session, siparis: models.Siparis):
    db.add(siparis)
    db.commit()
    db.refresh(siparis)
    return siparis

def get_user_orders(db: Session, kullanici_id: int):
    return db.query(models.Siparis).filter(
        models.Siparis.kullanici_id == kullanici_id
    ).order_by(models.Siparis.olusturma_tarihi.desc()).all()

def get_order(db: Session, siparis_id: int):
    return db.query(models.Siparis).filter(models.Siparis.id == siparis_id).first()

def create_order_item(db: Session, siparis_urun: models.SiparisUrun):
    db.add(siparis_urun)
    db.commit()
    db.refresh(siparis_urun)
    return siparis_urun

# ---- Cüzdan Hareketleri ----
def create_wallet_transaction(db: Session, transaction: models.CuzdanHareket):
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def get_user_wallet_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.CuzdanHareket).filter(
        models.CuzdanHareket.user_id == user_id
    ).order_by(models.CuzdanHareket.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

# ---- İletişim Mesajları ----
def create_contact_message(db: Session, mesaj: schemas.IletisimCreate):
    takip_no = str(uuid.uuid4().hex[:8]).upper()
    db_mesaj = models.IletisimMesaji(
        ad_soyad=mesaj.ad_soyad,
        email=mesaj.email,
        konu=mesaj.konu,
        mesaj=mesaj.mesaj,
        takip_no=takip_no
    )
    db.add(db_mesaj)
    db.commit()
    db.refresh(db_mesaj)
    return db_mesaj

def get_contact_messages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.IletisimMesaji).offset(skip).limit(limit).all()

# ---- Varis İşlemleri ----
def create_heir(db: Session, varis: schemas.VarisCreate, kullanici_id: int):
    db_varis = models.Varis(**varis.dict(), kullanici_id=kullanici_id)
    db.add(db_varis)
    db.commit()
    db.refresh(db_varis)
    return db_varis

def get_heirs(db: Session, kullanici_id: int):
    return db.query(models.Varis).filter(models.Varis.kullanici_id == kullanici_id).all()

def update_heir(db: Session, varis_id: int, update_data: dict, kullanici_id: int):
    db_varis = db.query(models.Varis).filter(
        models.Varis.id == varis_id, 
        models.Varis.kullanici_id == kullanici_id
    ).first()
    if db_varis:
        for key, value in update_data.items():
            setattr(db_varis, key, value)
        db.commit()
        db.refresh(db_varis)
    return db_varis

def delete_heir(db: Session, varis_id: int, kullanici_id: int):
    db_varis = db.query(models.Varis).filter(
        models.Varis.id == varis_id, 
        models.Varis.kullanici_id == kullanici_id
    ).first()
    if db_varis:
        db.delete(db_varis)
        db.commit()
        return True
    return False

# ---- Ayarlar ----
def get_setting(db: Session, anahtar: str):
    return db.query(models.Ayarlar).filter(models.Ayarlar.anahtar == anahtar).first()

def create_or_update_setting(db: Session, anahtar: str, deger: float):
    ayar = get_setting(db, anahtar)
    if ayar:
        ayar.deger = deger
    else:
        ayar = models.Ayarlar(anahtar=anahtar, deger=deger)
        db.add(ayar)
    db.commit()
    return ayar

# ---- Dashboard Verisi (Recursive CTE) ----
def get_dashboard_data(user_id: int, db: Session):
    """
    Dashboard verilerini getirir. Recursive CTE kullanır.
    NOT: Bu fonksiyon iş mantığı içeriyor olabilir, ileride servis katmanına taşınabilir.
    """
    kullanici = db.query(models.Kullanici).filter(models.Kullanici.id == user_id).first()
    if not kullanici:
        return None

    # Recursive CTE sorgusu
    cte_query = text("""
        WITH RECURSIVE alt_uyeler (id, parent_id, kol) AS (
            -- Başlangıç (Anchor): Ana kullanıcının doğrudan alt üyeleri
            SELECT id, parent_id, kol
            FROM kullanicilar
            WHERE parent_id = :user_id
            
            UNION ALL
            
            -- Tekrarlanan (Recursive) Kısım: Bir önceki adımda bulunan üyelerin alt üyeleri
            SELECT u.id, u.parent_id, u.kol
            FROM kullanicilar u
            INNER JOIN alt_uyeler au ON u.parent_id = au.id
        )
        -- Sonuç: Kol (SOL/SAĞ) bazında gruplayarak üye sayısını al
        SELECT kol, COUNT(id) as uye_sayisi
        FROM alt_uyeler
        GROUP BY kol;
    """)
    
    sol_ekip = 0
    sag_ekip = 0
    
    try:
        result = db.execute(cte_query, {"user_id": user_id}).fetchall()
        for row in result:
            if row[0] == 'SOL':
                sol_ekip = row[1]
            elif row[0] == 'SAG':
                sag_ekip = row[1]
    except Exception as e:
        print(f"CTE sorgusu hatası: {e}")

    referanslar = db.query(models.Kullanici).filter(models.Kullanici.referans_id == user_id).count()
    bekleyenler = db.query(models.Kullanici).filter(
        models.Kullanici.referans_id == user_id,
        models.Kullanici.parent_id == None
    ).count()

    # Rütbe Mantığı
    rutbeler = [
        "Distribütör", 
        "Platinum", 
        "Pearl", 
        "Sapphire", 
        "Ruby", 
        "Emerald", 
        "Diamond", 
        "Double Diamond", 
        "Triple Diamond", 
        "President", 
        "Double President", 
        "Triple President"
    ]
    mevcut_rutbe = getattr(kullanici, 'rutbe', 'Distribütör')
    
    try:
        mevcut_index = rutbeler.index(mevcut_rutbe)
        sonraki_rutbe = rutbeler[mevcut_index + 1] if mevcut_index + 1 < len(rutbeler) else None
    except ValueError:
        sonraki_rutbe = "Platinum" # Bilinmeyen rütbe ise varsayılan

    return {
        "id": kullanici.id,
        "uye_no": kullanici.uye_no,
        "tam_ad": kullanici.tam_ad,
        "email": kullanici.email,
        "rutbe": mevcut_rutbe,
        "sonraki_rutbe": sonraki_rutbe,
        "toplam_cv": kullanici.toplam_cv,
        "mevcut_sol_pv": kullanici.sol_pv,
        "mevcut_sag_pv": kullanici.sag_pv,
        "toplam_sol_ekip": sol_ekip,
        "toplam_sag_ekip": sag_ekip,
        "referans_sayisi": referanslar,
        "bekleyen_sayisi": bekleyenler,
        "profil_resmi": getattr(kullanici, 'profil_resmi', None)
    }

# ---- Yardımcı Fonksiyonlar ----
def get_direct_downlines(db: Session, user_id: int):
    """Kullanıcının direkt alt üyelerini getirir."""
    return db.query(models.Kullanici).filter(models.Kullanici.parent_id == user_id).all()

def get_downlines_by_leg(db: Session, user_id: int, kol: str):
    """Belirli koldaki alt üyeleri getirir."""
    return db.query(models.Kullanici).filter(
        models.Kullanici.parent_id == user_id,
        models.Kullanici.kol == kol
    ).all()

def get_referrals(db: Session, referans_id: int):
    """Referans ettiği kişileri getirir."""
    return db.query(models.Kullanici).filter(models.Kullanici.referans_id == referans_id).all()

def update_password(db: Session, user_id: int, new_password: str):
    """Kullanıcı şifresini günceller (hashlenmiş şifre beklenir)."""
    user = db.query(models.Kullanici).filter(models.Kullanici.id == user_id).first()
    if user:
        user.sifre = new_password
        db.commit()
        db.refresh(user)
    return user

# ---- Ürün ve Kategori İşlemleri (Türkçe İsimler) ----
def kategori_getir(db: Session, kategori_id: int):
    """Kategori ID'sine göre kategori getirir."""
    return db.query(models.Kategori).filter(models.Kategori.id == kategori_id).first()

def kategorileri_listele(db: Session, skip: int = 0, limit: int = 100):
    """Aktif kategorileri listeler."""
    return db.query(models.Kategori).filter(models.Kategori.aktif == True).offset(skip).limit(limit).all()

def kategori_olustur(db: Session, kategori_data: schemas.KategoriOlustur):
    """Yeni kategori oluşturur."""
    db_kategori = models.Kategori(**kategori_data.dict())
    db.add(db_kategori)
    db.commit()
    db.refresh(db_kategori)
    return db_kategori

def urun_getir(db: Session, urun_id: int):
    """Ürün ID'sine göre ürün getirir."""
    return db.query(models.Urun).filter(models.Urun.id == urun_id).first()

def urunleri_listele(db: Session, kategori_id: int = None, skip: int = 0, limit: int = 100):
    """Aktif ürünleri listeler."""
    sorgu = db.query(models.Urun).filter(models.Urun.aktif == True)
    if kategori_id:
        sorgu = sorgu.filter(models.Urun.kategori_id == kategori_id)
    return sorgu.offset(skip).limit(limit).all()

def urun_olustur(db: Session, urun_data: schemas.UrunOlustur):
    """Yeni ürün oluşturur."""
    db_urun = models.Urun(**urun_data.dict())
    db.add(db_urun)
    db.commit()
    db.refresh(db_urun)
    return db_urun

# ---- Sepet İşlemleri (Türkçe İsimler) ----
def sepet_detayi_getir(db: Session, kullanici_id: int):
    """Kullanıcının sepet detaylarını getirir."""
    return get_cart_details(db, kullanici_id)

def sepete_urun_ekle(db: Session, kullanici_id: int, urun_id: int, adet: int = 1):
    """Sepete ürün ekler."""
    return add_to_cart(db, kullanici_id, urun_id, adet)

def sepetten_urun_cikar(db: Session, kullanici_id: int, sepet_urun_id: int):
    """Sepetten ürün çıkarır."""
    return remove_from_cart(db, kullanici_id, sepet_urun_id)

# ---- Sipariş İşlemleri (Türkçe İsimler) ----
def kullanici_siparislerini_getir(db: Session, kullanici_id: int):
    """Kullanıcının siparişlerini getirir."""
    return get_user_orders(db, kullanici_id)

# ---- Varis İşlemleri (Türkçe İsimler) ----
def varisleri_getir(db: Session, kullanici_id: int):
    """Kullanıcının varislerini getirir."""
    return get_heirs(db, kullanici_id)

def varis_olustur(db: Session, varis: schemas.VarisCreate, kullanici_id: int):
    """Yeni varis oluşturur."""
    return create_heir(db, varis, kullanici_id)

def varis_guncelle(db: Session, varis_id: int, update_data: dict, kullanici_id: int):
    """Varis bilgilerini günceller."""
    return update_heir(db, varis_id, update_data, kullanici_id)

def varis_sil(db: Session, varis_id: int, kullanici_id: int):
    """Varis kaydını siler."""
    return delete_heir(db, varis_id, kullanici_id)

# ---- İletişim İşlemleri (Türkçe İsimler) ----
def create_iletisim_mesaji(db: Session, mesaj: schemas.IletisimCreate):
    """İletişim mesajı oluşturur."""
    return create_contact_message(db, mesaj)

# ---- Binary Tree İşlemleri (Service katmanına taşınacak) ----
def agac_verisi_getir_cte(db: Session, user_id: int, max_depth: int = 3):
    """
    DEPRECATION WARNING: Bu fonksiyon BinaryTreeService.get_tree_data_cte() ile değiştirilmelidir.
    Geçici olarak servisi çağırıyor.
    """
    from app.services.binary_service import BinaryTreeService
    return BinaryTreeService.get_tree_data_cte(db, user_id, max_depth)

def uyeyi_agaca_yerlestir(db: Session, user_id: int, parent_id: int, kol: str):
    """
    DEPRECATION WARNING: Bu fonksiyon BinaryTreeService.place_user_in_tree() ile değiştirilmelidir.
    Geçici olarak servisi çağırıyor.
    """
    from app.services.binary_service import BinaryTreeService
    return BinaryTreeService.place_user_in_tree(db, user_id, parent_id, kol)

# ---- Şifre Güncelleme (Alias) ----
def sifre_guncelle(db: Session, user_id: int, new_password: str):
    """Şifre güncelleme - update_password fonksiyonunu çağırır."""
    return update_password(db, user_id, new_password)

# ---- Sipariş Oluşturma (Service katmanına taşınacak) ----
def siparis_olustur(db: Session, kullanici_id: int, adres: str):
    """
    DEPRECATION WARNING: Bu fonksiyon OrderService.create_order() ile değiştirilmelidir.
    Geçici olarak servisi çağırıyor.
    """
    from app.services.order_service import OrderService
    return OrderService.create_order(db, kullanici_id, adres)

# ---- Kullanıcı Kaydı (Service katmanına taşınacak) ----
def yeni_uye_kaydet(db: Session, kullanici_verisi: schemas.KullaniciKayit):
    """
    DEPRECATION WARNING: Bu fonksiyon RegistrationService.register_user() ile değiştirilmelidir.
    Geçici olarak servisi çağırıyor.
    """
    from app.services.registration_service import RegistrationService
    return RegistrationService.register_user(db, kullanici_verisi)