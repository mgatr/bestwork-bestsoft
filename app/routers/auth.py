from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import timedelta
from .. import models, schemas, crud, utils
from ..dependencies import get_db, templates
from ..config import settings

router = APIRouter()

@router.get("/giris", response_class=HTMLResponse)
def giris_sayfasi(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "page_title": "Giriş Yap"})

@router.post("/giris", response_class=HTMLResponse)
def giris_yap(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Email veya Üye No ile giriş kontrolü
    user = db.query(models.Kullanici).filter(
        or_(models.Kullanici.email == email, models.Kullanici.uye_no == email)
    ).first()
    
    # Güvenli şifre kontrolü (Hash + Legacy)
    if not user or not utils.verify_password(password, user.sifre):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "hata": "Hatalı kullanıcı adı veya şifre!",
            "page_title": "Giriş Yap"
        })
    
    # Başarılı giriş - JWT Oluştur
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url=f"/panel/{user.id}", status_code=303)
    
    # Secure Cookie
    # NOT: 127.0.0.1 üzerinde secure=True çalışmayabilir. Şimdilik False.
    # Ayrıca samesite="Lax" önemlidir.
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,   
        samesite="lax",  
        secure=False # Localhost'ta HTTPS yoksa False olmalı
    )
    # Eski cookie'yi temizle
    response.delete_cookie("user_id")

    # Debug için
    print(f"Giriş Başarılı: User {user.id}, Token oluşturuldu.")
    
    return response

@router.get("/cikis")
def cikis_yap():
    response = RedirectResponse(url="/giris", status_code=303)
    response.delete_cookie("access_token")
    response.delete_cookie("user_id") # Eski cookie varsa sil
    return response

@router.get("/sifre-degistir", response_class=HTMLResponse)
def sifre_degistir_sayfasi(request: Request):
    if not hasattr(request.state, "user") or not request.state.user:
        return RedirectResponse(url="/giris", status_code=303)
    return templates.TemplateResponse("sifre_degistir.html", {"request": request, "page_title": "Şifre Değiştir"})

@router.post("/sifre-degistir", response_class=HTMLResponse)
def sifre_degistir_islem(
    request: Request,
    mevcut_sifre: str = Form(...),
    yeni_sifre: str = Form(...),
    yeni_sifre_tekrar: str = Form(...),
    db: Session = Depends(get_db)
):
    if not hasattr(request.state, "user") or not request.state.user:
        return RedirectResponse(url="/giris", status_code=303)
    
    user = request.state.user
    
    if not user or not utils.verify_password(mevcut_sifre, user.sifre):
        return templates.TemplateResponse("sifre_degistir.html", {
            "request": request,
            "hata": "Mevcut şifreniz hatalı!",
            "page_title": "Şifre Değiştir"
        })
    
    if yeni_sifre != yeni_sifre_tekrar:
        return templates.TemplateResponse("sifre_degistir.html", {
            "request": request,
            "hata": "Yeni şifreler uyuşmuyor!",
            "page_title": "Şifre Değiştir"
        })
        
    if len(yeni_sifre) < 6:
        return templates.TemplateResponse("sifre_degistir.html", {
            "request": request,
            "hata": "Yeni şifre en az 6 karakter olmalı!",
            "page_title": "Şifre Değiştir"
        })

    # Şifreyi güncelle (hashleme crud.sifre_guncelle içinde yapılır)
    crud.sifre_guncelle(db, user.id, yeni_sifre)
    
    return templates.TemplateResponse("sifre_degistir.html", {
        "request": request,
        "basari": "Şifreniz başarıyla güncellendi.",
        "page_title": "Şifre Değiştir"
    })

# --- KAYIT İŞLEMLERİ ---

@router.get("/kayit", response_class=HTMLResponse)
def kayit_sponsor_kontrol(request: Request, ref: str = None):
    if ref:
        return RedirectResponse(url=f"/kayit-form?ref={ref}", status_code=303)
    return templates.TemplateResponse("sponsor_kontrol.html", {"request": request, "page_title": "Sponsor Kontrol"})

@router.get("/api/sponsor-kontrol/{sponsor_no}")
def sponsor_kontrol_api(sponsor_no: str, db: Session = Depends(get_db)):
    sponsor = db.query(models.Kullanici).filter(
        or_(models.Kullanici.uye_no == sponsor_no, models.Kullanici.id == (int(sponsor_no) if sponsor_no.isdigit() else -1))
    ).first()
    
    if sponsor:
        return {"valid": True, "ad_soyad": sponsor.tam_ad, "id": sponsor.id}
    else:
        return {"valid": False}

@router.get("/kayit-form", response_class=HTMLResponse)
def kayit_formu_sayfasi(request: Request, ref: str = None, db: Session = Depends(get_db)):
    sponsor = None
    
    if ref:
        sponsor = db.query(models.Kullanici).filter(
            or_(models.Kullanici.uye_no == ref, models.Kullanici.id == (int(ref) if ref.isdigit() else -1))
        ).first()
    
    if not sponsor:
        sponsor = db.query(models.Kullanici).order_by(models.Kullanici.id.asc()).first()
        
    if not sponsor:
        return HTMLResponse("Sistemde hiç üye yok, lütfen önce kurulum yapın.", status_code=500)

    return templates.TemplateResponse("kayit_form.html", {
        "request": request,
        "sponsor": sponsor,
        "page_title": "Üyelik Kaydı"
    })

@router.post("/kayit-tamamla", response_class=HTMLResponse)
def kayit_tamamla_form(
    request: Request,
    referans_id: int = Form(...),
    ad: str = Form(...),
    soyad: str = Form(...),
    email: str = Form(...),
    telefon: str = Form(...),
    sifre: str = Form(...),
    sifre_tekrar: str = Form(...),
    uyelik_turu: str = Form("Bireysel"),
    ulke: str = Form("Türkiye"),
    dogum_tarihi: str = Form(None),
    cinsiyet: str = Form("KADIN"),
    il: str = Form(None),
    ilce: str = Form(None),
    mahalle: str = Form(None),
    tc_no: str = Form(None),
    vergi_dairesi: str = Form(None),
    vergi_no: str = Form(None),
    posta_kodu: str = Form(None),
    adres: str = Form(None),
    db: Session = Depends(get_db)
):
    if sifre != sifre_tekrar:
        return HTMLResponse("Şifreler uyuşmuyor! <a href='javascript:history.back()'>Geri Dön</a>", status_code=400)
    
    # Şifreyi hashle
    hashed_password = utils.get_password_hash(sifre)
    
    yeni_uye_data = schemas.KullaniciKayit(
        tam_ad=f"{ad} {soyad}",
        email=email,
        telefon=telefon,
        sifre=hashed_password, # Hashlenmiş şifre
        referans_id=referans_id,
        tc_no=tc_no,
        dogum_tarihi=dogum_tarihi,
        cinsiyet=cinsiyet,
        uyelik_turu=uyelik_turu,
        ulke=ulke,
        il=il,
        ilce=ilce,
        mahalle=mahalle,
        adres=adres,
        posta_kodu=posta_kodu,
        vergi_dairesi=vergi_dairesi,
        vergi_no=vergi_no
    )
    
    try:
        yeni_uye = crud.yeni_uye_kaydet(db, yeni_uye_data)
        return templates.TemplateResponse("login.html", {
            "request": request,
            "basari": "Kaydınız başarıyla oluşturuldu! Giriş yapabilirsiniz.",
            "page_title": "Giriş Yap"
        })
    except Exception as e:
        return HTMLResponse(f"Kayıt hatası: {str(e)} <a href='javascript:history.back()'>Geri Dön</a>", status_code=500)

@router.post("/kayit/", response_model=schemas.KullaniciCevap)
def uye_kaydet_api(kullanici: schemas.KullaniciKayit, db: Session = Depends(get_db)):
    # API üzerinden gelen kayıtlarda da hashleme yapılmalı
    kullanici.sifre = utils.get_password_hash(kullanici.sifre)
    return crud.yeni_uye_kaydet(db=db, kullanici_verisi=kullanici)