from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse
from app import models, crud, schemas
from app.dependencies import get_db, templates
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter()

# SERTİFİKALAR
@router.get("/sertifikalar", response_class=HTMLResponse)
def sertifikalar_sayfasi(request: Request, db: Session = Depends(get_db)):
    sertifikalar = db.query(models.Sertifika).filter(models.Sertifika.aktif == True).order_by(models.Sertifika.sira.asc()).all()
    return templates.TemplateResponse("sertifikalar.html", {
        "request": request,
        "page_title": "Sertifikalar",
        "sertifikalar": sertifikalar
    })

# KURUMSAL
@router.get("/kurumsal", response_class=HTMLResponse)
def kurumsal_sayfasi(request: Request):
    return templates.TemplateResponse("kurumsal.html", {
        "request": request,
        "page_title": "Kurumsal"
    })

# --- İLETİŞİM SAYFASI (home.py'ye taşındı) ---
# @router.get("/iletisim", response_class=HTMLResponse)
# async def iletisim_sayfasi(request: Request, db: Session = Depends(get_db)):
#     ayarlar = db.query(models.SiteAyarlari).first()
#     return templates.TemplateResponse("iletisim.html", {"request": request, "ayarlar": ayarlar, "page_title": "İletişim"})

# @router.post("/iletisim", response_class=HTMLResponse)
# async def iletisim_formu_gonder(
#     request: Request,
#     ad_soyad: str = Form(...),
#     email: str = Form(...),
#     konu: str = Form(...),
#     mesaj: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     yeni_mesaj = schemas.IletisimCreate(
#         ad_soyad=ad_soyad,
#         email=email,
#         konu=konu,
#         mesaj=mesaj
#     )
#     kayit = crud.create_iletisim_mesaji(db, yeni_mesaj)
#     ayarlar = db.query(models.SiteAyarlari).first()
#     return templates.TemplateResponse("iletisim.html", {
#         "request": request,
#         "basari_mesaji": f"Mesajınız başarıyla alındı. Takip Numaranız: {kayit.takip_no}",
#         "ayarlar": ayarlar,
#         "page_title": "İletişim"
#     })

# --- VARİS İŞLEMLERİ ---
@router.get("/varis-islemleri", response_class=HTMLResponse)
async def varis_islemleri_sayfasi(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    varisler = crud.varisleri_getir(db, request.state.user.id)
    return templates.TemplateResponse("varis_islemleri.html", {"request": request, "varis_members": varisler, "user": request.state.user, "page_title": "Varis İşlemleri"})

@router.post("/varis-kaydet")
async def save_varis(
    request: Request,
    entry_id: str = Form(None),
    name: str = Form(...),
    tc: str = Form(...),
    phone: str = Form(None),
    email: str = Form(None),
    relation: str = Form(None),
    address: str = Form(None),
    db: Session = Depends(get_db)
):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    # Boş stringleri None'a çevir
    phone = phone if phone and phone.strip() else None
    email = email if email and email.strip() else None
    relation = relation if relation and relation.strip() else None
    address = address if address and address.strip() else None
    
    if entry_id and entry_id.strip():
        varis_update = schemas.VarisUpdate(
            ad_soyad=name,
            tc=tc,
            telefon=phone,
            email=email,
            yakinlik=relation,
            adres=address
        )
        crud.varis_guncelle(db, int(entry_id), varis_update, request.state.user.id)
    else:
        varis_create = schemas.VarisCreate(
            ad_soyad=name,
            tc=tc,
            telefon=phone,
            email=email,
            yakinlik=relation,
            adres=address
        )
        crud.varis_olustur(db, varis_create, request.state.user.id)
        
    return RedirectResponse(url="/varis-islemleri", status_code=302)

@router.post("/varis-sil")
async def delete_varis(
    request: Request,
    entry_id: int = Form(...),
    db: Session = Depends(get_db)
):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
        
    crud.varis_sil(db, entry_id, request.state.user.id)
    return RedirectResponse(url="/varis-islemleri", status_code=302)

# --- BANKA BİLGİLERİ ---
@router.get("/banka-bilgileri", response_class=HTMLResponse)
async def banka_bilgileri_sayfasi(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    # Sadece tek bir banka hesabı getir
    banka = db.query(models.BankaBilgisi).filter(models.BankaBilgisi.user_id == request.state.user.id).first()
    return templates.TemplateResponse("banka_bilgileri.html", {"request": request, "banka": banka, "page_title": "Banka Bilgilerim"})

@router.post("/banka-bilgileri/kaydet")
async def banka_bilgisi_kaydet(
    request: Request,
    hesap_sahibi: str = Form(...),
    banka_adi: str = Form(...),
    iban: str = Form(...),
    swift_kodu: str = Form(None),
    db: Session = Depends(get_db)
):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    # Mevcut kaydı kontrol et
    banka = db.query(models.BankaBilgisi).filter(models.BankaBilgisi.user_id == request.state.user.id).first()
    
    if banka:
        # Güncelle
        banka.hesap_sahibi = hesap_sahibi
        banka.banka_adi = banka_adi
        banka.iban = iban
        banka.swift_kodu = swift_kodu
    else:
        # Yeni oluştur
        banka = models.BankaBilgisi(
            user_id=request.state.user.id,
            hesap_sahibi=hesap_sahibi,
            banka_adi=banka_adi,
            iban=iban,
            swift_kodu=swift_kodu
        )
        db.add(banka)
    
    db.commit()
    
    return RedirectResponse(url="/banka-bilgileri", status_code=302)

# --- ÜYELİK BİLGİLERİ ---
@router.get("/uyelik-bilgileri", response_class=HTMLResponse)
async def uyelik_bilgileri_sayfasi(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    user = request.state.user
    
    # Sponsor bilgisini getir
    sponsor = None
    if user.referans_id:
        sponsor = db.query(models.Kullanici).filter(models.Kullanici.id == user.referans_id).first()
    
    # Kayıt gün farkını hesapla
    gun_farki = 0
    if user.kayit_tarihi:
        simdi = datetime.now(ZoneInfo("Europe/Istanbul"))
        fark = simdi - user.kayit_tarihi
        gun_farki = fark.days
        
    return templates.TemplateResponse("uyelik_bilgileri.html", {
        "request": request,
        "user": user,
        "sponsor": sponsor,
        "gun_farki": gun_farki,
        "page_title": "Üyelik Bilgilerim"
    })

# --- PRİM BİLGİLERİ ---
@router.get("/prim-bilgileri", response_class=HTMLResponse)
async def prim_bilgileri_sayfasi(request: Request, month: int = None, year: int = None, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
        
    return templates.TemplateResponse("priminfo.html", {
        "request": request,
        "current_month": int(month),
        "current_year": int(year),
        "page_title": "Prim Bilgileri"
    })

# --- HIZLI BAŞLANGIÇ BONUSU ---
@router.get("/hizli-baslangic", response_class=HTMLResponse)
async def hizli_baslangic_sayfasi(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    # Şimdilik boş veri gönderiyoruz, ileride gerçek verilerle doldurulacak
    # Örnek veri yapısı:
    # kayitlar = [
    #     {
    #         "uye_no": "TR87550847",
    #         "ad_soyad": "EBUBEKİR ARSLAN",
    #         "paket_adi": "STARTER",
    #         "bonus": 60.00,
    #         "tarih": datetime(2022, 1, 26),
    #         "kazanc": 0.00
    #     },
    #     {
    #         "uye_no": "TR76497419",
    #         "ad_soyad": "Fahriye Burcu Arslan",
    #         "paket_adi": "STARTER",
    #         "bonus": 60.00,
    #         "tarih": datetime(2022, 1, 27),
    #         "kazanc": 60.00
    #     }
    # ]
    
    kayitlar = []
    toplam_kazanc = sum(k["kazanc"] for k in kayitlar) if kayitlar else 0.0
    
    return templates.TemplateResponse("hizli_baslangic.html", {
        "request": request,
        "kayitlar": kayitlar,
        "toplam_kazanc": toplam_kazanc,
        "page_title": "Hızlı Başlangıç Bonusu"
    })

# --- REFERANS BONUSU ---
@router.get("/referans-bonusu", response_class=HTMLResponse)
async def referans_bonusu_sayfasi(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    # Şimdilik boş veri gönderiyoruz
    kayitlar = []
    toplam_kazanc = sum(k["kazanc"] for k in kayitlar) if kayitlar else 0.0
    
    # Tarih filtreleri için varsayılan değerler
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    return templates.TemplateResponse("referans_bonusu.html", {
        "request": request,
        "kayitlar": kayitlar,
        "toplam_kazanc": toplam_kazanc,
        "current_month": current_month,
        "current_year": current_year,
        "page_title": "Referans Bonusu"
    })

# --- ANLIK EŞLEŞME SAYFASI ---
@router.get("/anlik-eslesme", response_class=HTMLResponse)
async def anlik_eslesme_sayfasi(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=302)
    
    user = request.state.user
    
    # PV değerlerini güvenli al
    sol_pv = user.sol_pv if user.sol_pv else 0
    sag_pv = user.sag_pv if user.sag_pv else 0
    
    # Anlık hesaplanan olası kazanç
    eslesecek_puan = min(sol_pv, sag_pv)
    olasi_kazanc = eslesecek_puan * 0.13
    
    # Geçmiş Eşleşme Hareketleri (Şimdilik boş list veya mock data)
    # Burada Cüzdan Hareketleri tablosundan "ESLESME" tipindeki kayıtları çekmek gerekir.
    # eslesmeler = db.query(models.CuzdanHareket).filter(...)
    
    # Tarih filtreleri için varsayılan değerler
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    eslesmeler = [] # Boş liste şimdilik
    toplam_kazanc = sum(e.get("kazanc", 0) for e in eslesmeler)
    
    return templates.TemplateResponse("anlik_eslesme.html", {
        "request": request,
        "user": user,
        "sol_pv": sol_pv,
        "sag_pv": sag_pv,
        "eslesecek_puan": eslesecek_puan,
        "olasi_kazanc": olasi_kazanc,
        "eslesmeler": eslesmeler,
        "toplam_kazanc": toplam_kazanc,
        "current_month": current_month,
        "current_year": current_year,
        "page_title": "Anlık Eşleşme"
    })