from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse
from PIL import Image
import shutil
import uuid
import subprocess
import os
import json
import time
import sys
from decimal import Decimal
from app import models, crud, schemas
from app.dependencies import get_db, templates

router = APIRouter()

# --- BESTSOFT ADMIN GİRİŞ ---
@router.get("/bestsoft", response_class=HTMLResponse)
async def bestsoft_login_page(request: Request):
    return templates.TemplateResponse("bestsoft_login.html", {"request": request})

@router.post("/bestsoft/login")
async def bestsoft_login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Admin modelinde ara
    admin = db.query(models.Admin).filter(models.Admin.kullanici_adi == username).first()
    if not admin or admin.sifre != password:
        return templates.TemplateResponse("bestsoft_login.html", {"request": request, "hata": "Geçersiz Kullanıcı Adı veya Şifre"})
    
    # Admin JWT Token
    from app import utils
    access_token = utils.create_access_token(
        data={"sub": f"admin:{username}"}
    )

    response = RedirectResponse(url="/bestsoft/dashboard", status_code=303)
    response.set_cookie(
        key="admin_token", 
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400  # 24 Saat (saniye cinsinden)
    )
    return response

@router.get("/admin/logout")
def admin_logout():
    response = RedirectResponse(url="/bestsoft", status_code=303)
    response.delete_cookie("admin_token")
    return response

# Dependency veya Yardımcı Fonksiyon
def get_current_admin(request: Request):
    token = request.cookies.get("admin_token")
    if token and token.startswith("Bearer "):
        from app import utils
        _, _, param = token.partition(" ")
        payload = utils.decode_access_token(param)
        if payload:
            sub = payload.get("sub")
            if sub and sub.startswith("admin:"):
                return sub.split(":")[1]
    return None

# BESTSOFT ADMIN DASHBOARD (YENİ ANASAYFA)
@router.get("/bestsoft/dashboard", response_class=HTMLResponse)
def bestsoft_dashboard(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    # İstatistikler
    bekleyen_mesaj_sayisi = db.query(models.IletisimMesaji).filter(models.IletisimMesaji.durum == "Beklemede").count()
    toplam_mesaj_sayisi = db.query(models.IletisimMesaji).count()
    toplam_urun_sayisi = db.query(models.Urun).count()
    toplam_kategori_sayisi = db.query(models.Kategori).count()
    
    return templates.TemplateResponse("bestsoft_dashboard.html", {
        "request": request,
        "bekleyen_mesaj_sayisi": bekleyen_mesaj_sayisi,
        "toplam_mesaj_sayisi": toplam_mesaj_sayisi,
        "toplam_urun_sayisi": toplam_urun_sayisi,
        "toplam_kategori_sayisi": toplam_kategori_sayisi,
        "active_menu": "dashboard"
    })

# Yardımcı Fonksiyon: Güncelleme Kontrolü
def check_for_updates():
    try:
        should_fetch = True
        info_file = "update_check_info.json"
        
        # 8 Saatlik Kontrol (28800 saniye)
        if os.path.exists(info_file):
            try:
                with open(info_file, "r") as f:
                    data = json.load(f)
                    last_check = data.get("last_check", 0)
                    if time.time() - last_check < 28800:
                        should_fetch = False
            except:
                pass
        
        if should_fetch:
            # Git fetch işlemi (timeout ile)
            subprocess.run(["git", "fetch"], check=True, timeout=10, capture_output=True)
            # Zaman damgasını kaydet
            try:
                with open(info_file, "w") as f:
                    json.dump({"last_check": time.time()}, f)
            except:
                pass

        # Status kontrolü
        result = subprocess.run(["git", "status", "-uno"], check=True, capture_output=True, text=True)
        if "Your branch is behind" in result.stdout:
            return True
    except:
        pass
    return False

def get_system_version():
    try:
        readme_path = os.path.join(os.getcwd(), "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                import re
                content = f.read()
                match = re.search(r"### (v\d+(\.\d+)+)", content)
                if match:
                    return match.group(1)
    except:
        pass
    return "v?.?.?"

def get_remote_system_version():
    try:
        # Fetch remote details first if we haven't recently (relies on check_for_updates having run usually, but safe to run)
        # Assuming origin/main is the target. Better to use @{u} if configured.
        result = subprocess.run(["git", "show", "@{u}:README.md"], capture_output=True, text=True)
        if result.returncode == 0:
            import re
            content = result.stdout
            match = re.search(r"### (v\d+(\.\d+)+)", content)
            if match:
                return match.group(1)
    except:
        pass
    return None

# ADMIN AYARLAR SAYFASI
@router.get("/admin/ayarlar")
def admin_ayarlar_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    update_available = check_for_updates()
    current_version = get_system_version()
    remote_version = None

    return templates.TemplateResponse("admin_ayarlar.html", {
        "request": request, 
        "update_available": update_available,
        "current_version": current_version,
        "remote_version": remote_version,
        "active_menu": "ayarlar"
    })

# --- SLIDER YÖNETİMİ ---
@router.get("/admin/ayarlar/slider", response_class=HTMLResponse)
def admin_slider_list(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    sliders = db.query(models.Slider).order_by(models.Slider.sira.asc()).all()
    return templates.TemplateResponse("admin_slider.html", {
        "request": request, "sliders": sliders, "active_menu": "ayarlar"
    })

@router.post("/admin/ayarlar/slider/ekle")
async def admin_slider_add(
    request: Request,
    baslik: str = Form(None),
    link: str = Form(None),
    sira: int = Form(0),
    resim: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    UPLOAD_DIR = "static/uploads/sliders"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    unique_filename = f"slide_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    webp_filename = f"{unique_filename}.webp"
    file_path = os.path.join(UPLOAD_DIR, webp_filename)
    
    try:
        image = Image.open(resim.file)
        image.save(file_path, "WEBP", quality=85)
    except Exception as e:
        print(f"Slider upload error: {e}")
    
    new_slider = models.Slider(
        baslik=baslik,
        link=link,
        sira=sira,
        resim_yolu=f"/static/uploads/sliders/{webp_filename}",
        aktif=True
    )
    db.add(new_slider)
    db.commit()
    
    return RedirectResponse(url="/admin/ayarlar/slider", status_code=303)

@router.get("/admin/ayarlar/slider/sil/{id}")
def admin_slider_delete(id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    slider = db.query(models.Slider).filter(models.Slider.id == id).first()
    if slider:
        try:
            relative_path = slider.resim_yolu.lstrip('/')
            if os.path.exists(relative_path):
                os.remove(relative_path)
        except:
            pass
        db.delete(slider)
        db.commit()
    return RedirectResponse(url="/admin/ayarlar/slider", status_code=303)

# --- SERTİFİKA YÖNETİMİ ---
@router.get("/admin/ayarlar/sertifika", response_class=HTMLResponse)
def admin_sertifika_list(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    sertifikalar = db.query(models.Sertifika).order_by(models.Sertifika.sira.asc()).all()
    return templates.TemplateResponse("admin_sertifika.html", {
        "request": request, "sertifikalar": sertifikalar, "active_menu": "ayarlar"
    })

@router.post("/admin/ayarlar/sertifika/ekle")
async def admin_sertifika_add(
    request: Request,
    baslik: str = Form(None),
    aciklama: str = Form(None),
    sira: int = Form(0),
    resim: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    UPLOAD_DIR = "static/uploads/sertifikalar"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    unique_filename = f"cert_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    webp_filename = f"{unique_filename}.webp"
    file_path = os.path.join(UPLOAD_DIR, webp_filename)
    
    try:
        image = Image.open(resim.file)
        image.save(file_path, "WEBP", quality=85)
    except Exception as e:
        print(f"Certificate upload error: {e}")
    
    new_sertifika = models.Sertifika(
        baslik=baslik,
        aciklama=aciklama,
        sira=sira,
        resim_yolu=f"/static/uploads/sertifikalar/{webp_filename}",
        aktif=True
    )
    db.add(new_sertifika)
    db.commit()
    
    return RedirectResponse(url="/admin/ayarlar/sertifika", status_code=303)

@router.get("/admin/ayarlar/sertifika/sil/{id}")
def admin_sertifika_delete(id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    sertifika = db.query(models.Sertifika).filter(models.Sertifika.id == id).first()
    if sertifika:
        try:
            relative_path = sertifika.resim_yolu.lstrip('/')
            if os.path.exists(relative_path):
                os.remove(relative_path)
        except:
            pass
        db.delete(sertifika)
        db.commit()
    return RedirectResponse(url="/admin/ayarlar/sertifika", status_code=303)

# ADMIN KONTROL SAYFASI (Eski Rota - Yönlendirme)
@router.get("/admin/kontrol")
def admin_ayar_redirect():
    return RedirectResponse(url="/admin/ayarlar", status_code=303)

# ... Diğer rotalar (Ürünler, Kategoriler vb.) buraya eklenebilir ...

# ADMİN: Ürün Ekleme
@router.get("/admin/urun/ekle", response_class=HTMLResponse)
def admin_urun_ekle_form(request: Request, db: Session = Depends(get_db)):
    kategoriler = crud.kategorileri_listele(db)
    return templates.TemplateResponse("admin_urun_ekle.html", {
        "request": request,
        "kategoriler": kategoriler,
        "active_menu": "urunler"
    })

@router.post("/admin/urun/ekle")
def admin_urun_ekle(
    ad: str = Form(...),
    aciklama: str = Form(""),
    fiyat: Decimal = Form(...),
    indirimli_fiyat: Decimal = Form(None),
    stok: int = Form(0),
    kategori_id: int = Form(None),
    resim_url: str = Form(""),
    pv_degeri: int = Form(0),
    db: Session = Depends(get_db)
):
    urun_data = schemas.UrunOlustur(
        ad=ad,
        aciklama=aciklama,
        fiyat=fiyat,
        indirimli_fiyat=indirimli_fiyat if indirimli_fiyat else None,
        stok=stok,
        kategori_id=kategori_id if kategori_id else None,
        resim_url=resim_url,
        pv_degeri=pv_degeri
    )
    crud.urun_olustur(db, urun_data)
    return RedirectResponse(url="/admin/urunler", status_code=303)

# ADMİN: Ürün Listesi
@router.get("/admin/urunler", response_class=HTMLResponse)
def admin_urunler(request: Request, db: Session = Depends(get_db)):
    urunler = crud.urunleri_listele(db, limit=1000)
    return templates.TemplateResponse("admin_urunler.html", {
        "request": request,
        "urunler": urunler,
        "active_menu": "urunler"
    })

# ADMİN: Kategoriler
@router.get("/admin/kategoriler", response_class=HTMLResponse)
def admin_kategoriler(request: Request, db: Session = Depends(get_db)):
    kategoriler = crud.kategorileri_listele(db)
    return templates.TemplateResponse("admin_kategoriler.html", {
        "request": request,
        "kategoriler": kategoriler,
        "active_menu": "kategoriler"
    })

@router.post("/admin/kategoriler")
def admin_kategori_ekle(
    ad: str = Form(...),
    aciklama: str = Form(""),
    db: Session = Depends(get_db)
):
    kategori_data = schemas.KategoriOlustur(
        ad=ad,
        aciklama=aciklama
    )
    crud.kategori_olustur(db, kategori_data)
    return RedirectResponse(url="/admin/kategoriler", status_code=303)

# --- İLETİŞİM MESAJLARI ---
@router.get("/admin/iletisim", response_class=HTMLResponse)
def admin_iletisim_listele(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    mesajlar = db.query(models.IletisimMesaji).order_by(models.IletisimMesaji.tarih.desc()).all()
    
    return templates.TemplateResponse("admin_iletisim.html", {
        "request": request,
        "mesajlar": mesajlar,
        "active_menu": "iletisim"
    })

@router.post("/admin/iletisim/durum")
def admin_iletisim_durum_guncelle(
    request: Request,
    mesaj_id: int = Form(...),
    durum: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    mesaj = db.query(models.IletisimMesaji).filter(models.IletisimMesaji.id == mesaj_id).first()
    if mesaj:
        mesaj.durum = durum
        db.commit()
    
    return RedirectResponse(url="/admin/iletisim", status_code=303)

@router.post("/admin/iletisim/sil")
def admin_iletisim_sil(
    request: Request,
    mesaj_id: int = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    mesaj = db.query(models.IletisimMesaji).filter(models.IletisimMesaji.id == mesaj_id).first()
    if mesaj:
        db.delete(mesaj)
        db.commit()
    
    return RedirectResponse(url="/admin/iletisim", status_code=303)

# --- SEO AYARLARI ---

@router.get("/admin/ayarlar/seo", response_class=HTMLResponse)
def admin_seo_page(request: Request, db: Session = Depends(get_db)):
    # Check admin auth
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    ayarlar = db.query(models.SiteAyarlari).first()
    if not ayarlar:
        ayarlar = models.SiteAyarlari()
        db.add(ayarlar)
        db.commit()
        db.refresh(ayarlar)
        
    return templates.TemplateResponse("admin_seo.html", {
        "request": request,
        "ayarlar": ayarlar,
        "active_menu": "ayarlar"
    })

@router.post("/admin/ayarlar/seo")
def admin_seo_update(
    request: Request,
    site_basligi: str = Form(...),
    seo_aciklama: str = Form(""),
    seo_anahtar_kelimeler: str = Form(""),
    seo_yazar: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    ayarlar = db.query(models.SiteAyarlari).first()
    if not ayarlar:
        ayarlar = models.SiteAyarlari()
        db.add(ayarlar)
    
    ayarlar.site_basligi = site_basligi
    ayarlar.seo_aciklama = seo_aciklama
    ayarlar.seo_anahtar_kelimeler = seo_anahtar_kelimeler
    ayarlar.seo_yazar = seo_yazar
    
    db.commit()
    
    # Redirect back with success message
    return RedirectResponse(url="/admin/ayarlar/seo?success=true", status_code=303)

# --- GOOGLE ANALYTICS AYARLARI ---

@router.get("/admin/ayarlar/analytics", response_class=HTMLResponse)
def admin_analytics_page(request: Request, db: Session = Depends(get_db)):
    # Check admin auth
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    ayarlar = db.query(models.SiteAyarlari).first()
    if not ayarlar:
        ayarlar = models.SiteAyarlari()
        db.add(ayarlar)
        db.commit()
        db.refresh(ayarlar)
        
    return templates.TemplateResponse("admin_analytics.html", {
        "request": request,
        "ayarlar": ayarlar,
        "active_menu": "ayarlar"
    })

@router.post("/admin/ayarlar/analytics")
def admin_analytics_update(
    request: Request,
    google_analytics_kodu: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    ayarlar = db.query(models.SiteAyarlari).first()
    if not ayarlar:
        ayarlar = models.SiteAyarlari()
        db.add(ayarlar)
    
    ayarlar.google_analytics_kodu = google_analytics_kodu
    
    db.commit()
    
    return RedirectResponse(url="/admin/ayarlar/analytics?success=true", status_code=303)

# --- FİRMA BİLGİLERİ AYARLARI ---

@router.get("/admin/ayarlar/firma", response_class=HTMLResponse)
def admin_firma_page(request: Request, db: Session = Depends(get_db)):
    # Check admin auth
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    ayarlar = db.query(models.SiteAyarlari).first()
    if not ayarlar:
        ayarlar = models.SiteAyarlari()
        db.add(ayarlar)
        db.commit()
        db.refresh(ayarlar)
        
    return templates.TemplateResponse("admin_firma.html", {
        "request": request,
        "ayarlar": ayarlar,
        "active_menu": "ayarlar"
    })

@router.post("/admin/ayarlar/firma")
def admin_firma_update(
    request: Request,
    footer_baslik: str = Form(""),
    footer_aciklama: str = Form(""),
    footer_copyright: str = Form(""),
    iletisim_adres: str = Form(""),
    iletisim_email: str = Form(""),
    iletisim_telefon: str = Form(""),
    iletisim_harita: str = Form(""),
    sosyal_facebook: str = Form(""),
    sosyal_twitter: str = Form(""),
    sosyal_instagram: str = Form(""),
    sosyal_linkedin: str = Form(""),
    sosyal_youtube: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
        
    ayarlar = db.query(models.SiteAyarlari).first()
    if not ayarlar:
        ayarlar = models.SiteAyarlari()
        db.add(ayarlar)
    
    ayarlar.footer_baslik = footer_baslik
    ayarlar.footer_aciklama = footer_aciklama
    ayarlar.footer_copyright = footer_copyright
    ayarlar.iletisim_adres = iletisim_adres
    ayarlar.iletisim_email = iletisim_email
    ayarlar.iletisim_telefon = iletisim_telefon
    ayarlar.iletisim_harita = iletisim_harita
    ayarlar.sosyal_facebook = sosyal_facebook
    ayarlar.sosyal_twitter = sosyal_twitter
    ayarlar.sosyal_instagram = sosyal_instagram
    ayarlar.sosyal_linkedin = sosyal_linkedin
    ayarlar.sosyal_youtube = sosyal_youtube
    

    db.commit()
    
    # Redirect back with success message
    return RedirectResponse(url="/admin/ayarlar/firma?success=true", status_code=303)

# --- SİSTEM GÜNCELLEME ---
@router.get("/admin/ayarlar/guncelleme", response_class=HTMLResponse)
def admin_ayarlar_guncelleme(request: Request):
    # Read the README.md content
    readme_content = ""
    try:
        # Assuming README.md is in the root directory
        readme_path = os.path.join(os.getcwd(), "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
        else:
            readme_content = "README.md dosyası bulunamadı."
    except Exception as e:
        readme_content = f"README dosyası okunamadı: {str(e)}"
    
    result_message = request.query_params.get("message")
    update_available = check_for_updates()

    return templates.TemplateResponse("admin_ayarlar_guncelleme.html", {
        "request": request,
        "readme_content": readme_content,
        "result_message": result_message,
        "update_available": update_available,
        "active_menu": "ayarlar"
    })

@router.post("/admin/ayarlar/guncelleme/check")
def admin_ayarlar_guncelleme_check(request: Request):
    try:
        # Run git fetch
        subprocess.run(["git", "fetch"], check=True, capture_output=True)
        
        # Manuel kontrol yapıldığı için zamanlayıcıyı güncelle
        try:
            info_file = "update_check_info.json"
            with open(info_file, "w") as f:
                json.dump({"last_check": time.time()}, f)
        except:
            pass

        # Check status
        result = subprocess.run(["git", "status", "-uno"], check=True, capture_output=True, text=True)
        raw_output = result.stdout
        
        # Output Parsing & Formatting
        message = ""
        lines = raw_output.splitlines()
        
        # Check Main Status
        if "Your branch is up to date" in raw_output:
            message += "✅ SİSTEM GÜNCEL\n\n"
            message += "Sisteminiz şu anda sunucudaki en son versiyonla senkronizedir.\n"
        elif "Your branch is behind" in raw_output:
            message += "⚠️ GÜNCELLEME MEVCUT\n\n"
            message += "Sunucuda yeni bir sürüm bulundu. Lütfen güncelleme butonunu kullanarak sistemi yükseltin.\n"
        else:
            message += "ℹ️ DURUM BİLGİSİ\n\n"
            message += "Git durumu aşağıdadır:\n"

        # Check Local Changes (Dirty State)
        if "Changes not staged for commit" in raw_output or "Changes to be committed" in raw_output:
             message += "\n----------------------------------------\n"
             message += "⚠️ YEREL DEĞİŞİKLİKLER UYARISI:\n"
             message += "Sistemde yerel olarak değiştirilmiş dosyalar var.\n"
             
             # Filter out massive lists of files (like .venv clutter)
             change_lines = [line for line in lines if "modified:" in line or "deleted:" in line or "renamed:" in line]
             if len(change_lines) > 10:
                 message += f"{len(change_lines)} adet dosya farklı görünüyor. (Detaylar gizlendi)\n"
             else:
                 message += "Etkilenen Dosyalar:\n"
                 for line in change_lines:
                     message += f"{line.strip()}\n"

    except Exception as e:
        message = f"Hata oluştu: {str(e)}"
    
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    
    return RedirectResponse(url=f"/admin/ayarlar/guncelleme?message={encoded_message}", status_code=303)

@router.post("/admin/ayarlar/guncelleme/pull")
def admin_ayarlar_guncelleme_pull(request: Request):
    try:
        # Run git pull
        result = subprocess.run(["git", "pull"], check=True, capture_output=True, text=True)
        message = f"Güncelleme Çıktısı:\n{result.stdout}"

        # Veritabanı Güncelleme Scriptini Çalıştır
        # Yeni bir process olarak çalıştırıyoruz böylece yeni inen kodu okur
        try:
            db_result = subprocess.run([sys.executable, "update_db.py"], capture_output=True, text=True)
            if db_result.returncode == 0:
                message += "\n\n✅ Veritabanı Senkronizasyonu Başarılı.\n"
            else:
                message += f"\n\n⚠️ Veritabanı Güncelleme Hatası:\n{db_result.stderr}"
        except Exception as db_e:
             message += f"\n\n⚠️ DB Script Çalıştırılamadı: {str(db_e)}"

    except subprocess.CalledProcessError as e:
        # Decode bytes if necessary
        err_msg = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
        message = f"Güncelleme Hatası (Git):\n{err_msg}"
    except Exception as e:
        message = f"Hata: {str(e)}"
    
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    
    return RedirectResponse(url=f"/admin/ayarlar/guncelleme?message={encoded_message}", status_code=303)


# ========================================
# MODÜL 4 - NETWORK MARKETING YÖNETİMİ
# ========================================

# --- MLM GENEL AYARLAR ---
@router.get("/admin/mlm/ayarlar", response_class=HTMLResponse)
def admin_mlm_ayarlar_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    # Ayarları getir
    ayarlar = {
        "referans_bonusu": crud.get_setting(db, "referans_bonusu") or models.Ayarlar(anahtar="referans_bonusu", deger=50.0),
        "hosgeldin_bonusu": crud.get_setting(db, "hosgeldin_bonusu") or models.Ayarlar(anahtar="hosgeldin_bonusu", deger=0.0),
        "kayit_pv": crud.get_setting(db, "kayit_pv") or models.Ayarlar(anahtar="kayit_pv", deger=100.0),
        "kayit_cv": crud.get_setting(db, "kayit_cv") or models.Ayarlar(anahtar="kayit_cv", deger=50.0),
    }
    
    return templates.TemplateResponse("admin_mlm_ayarlar.html", {
        "request": request,
        "ayarlar": ayarlar,
        "admin": admin_user
    })

@router.post("/admin/mlm/ayarlar/guncelle")
def admin_mlm_ayarlar_guncelle(
    request: Request,
    referans_bonusu: float = Form(...),
    hosgeldin_bonusu: float = Form(...),
    kayit_pv: float = Form(...),
    kayit_cv: float = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    # Ayarları güncelle
    crud.create_or_update_setting(db, "referans_bonusu", referans_bonusu)
    crud.create_or_update_setting(db, "hosgeldin_bonusu", hosgeldin_bonusu)
    crud.create_or_update_setting(db, "kayit_pv", kayit_pv)
    crud.create_or_update_setting(db, "kayit_cv", kayit_cv)
    
    return RedirectResponse(url="/admin/mlm/ayarlar?basari=1", status_code=303)

# --- KOMİSYON ORANLARI ---
@router.get("/admin/mlm/komisyon", response_class=HTMLResponse)
def admin_mlm_komisyon_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    # Komisyon ayarları
    kisa_kol_oran = crud.get_setting(db, "kisa_kol_oran") or models.Ayarlar(anahtar="kisa_kol_oran", deger=0.13)
    referans_orani = crud.get_setting(db, "referans_orani") or models.Ayarlar(anahtar="referans_orani", deger=0.40)
    
    return templates.TemplateResponse("admin_mlm_komisyon.html", {
        "request": request,
        "kisa_kol_oran": kisa_kol_oran,
        "referans_orani": referans_orani,
        "admin": admin_user
    })

@router.post("/admin/mlm/komisyon/guncelle")
def admin_mlm_komisyon_guncelle(
    request: Request,
    kisa_kol_oran: float = Form(...),
    referans_orani: float = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    crud.create_or_update_setting(db, "kisa_kol_oran", kisa_kol_oran)
    crud.create_or_update_setting(db, "referans_orani", referans_orani)
    
    return RedirectResponse(url="/admin/mlm/komisyon?basari=1", status_code=303)

# --- NESİL GELİRLERİ ---
@router.get("/admin/mlm/nesil", response_class=HTMLResponse)
def admin_mlm_nesil_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    # Nesil ayarlarını getir (1-10)
    nesil_ayarlari = db.query(models.NesilAyari).order_by(models.NesilAyari.nesil_no).all()
    
    return templates.TemplateResponse("admin_mlm_nesil.html", {
        "request": request,
        "nesil_ayarlari": nesil_ayarlari,
        "admin": admin_user
    })

@router.post("/admin/mlm/nesil/guncelle")
def admin_mlm_nesil_guncelle(
    request: Request,
    nesil_1: float = Form(0.0),
    nesil_2: float = Form(0.0),
    nesil_3: float = Form(0.0),
    nesil_4: float = Form(0.0),
    nesil_5: float = Form(0.0),
    nesil_6: float = Form(0.0),
    nesil_7: float = Form(0.0),
    nesil_8: float = Form(0.0),
    nesil_9: float = Form(0.0),
    nesil_10: float = Form(0.0),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Nesil oranlarını liste olarak topla
    oranlar = [nesil_1, nesil_2, nesil_3, nesil_4, nesil_5,
               nesil_6, nesil_7, nesil_8, nesil_9, nesil_10]

    # Her nesil için güncelle
    for i, oran in enumerate(oranlar, start=1):
        # Nesil ayarı var mı kontrol et
        nesil_ayar = db.query(models.NesilAyari).filter(
            models.NesilAyari.nesil_no == i
        ).first()

        if nesil_ayar:
            nesil_ayar.oran = oran
        else:
            nesil_ayar = models.NesilAyari(nesil_no=i, oran=oran)
            db.add(nesil_ayar)

    db.commit()

    return RedirectResponse(url="/admin/mlm/nesil?basari=1", status_code=303)

# --- BONUS SİSTEMLERİ ---
@router.get("/admin/mlm/bonus", response_class=HTMLResponse)
def admin_mlm_bonus_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    # Bonus ayarları (MLM Ayarlar ile aynı ama farklı görünüm)
    ayarlar = {
        "referans_bonusu": crud.get_setting(db, "referans_bonusu") or models.Ayarlar(anahtar="referans_bonusu", deger=50.0),
        "hosgeldin_bonusu": crud.get_setting(db, "hosgeldin_bonusu") or models.Ayarlar(anahtar="hosgeldin_bonusu", deger=0.0),
    }
    
    return templates.TemplateResponse("admin_mlm_bonus.html", {
        "request": request,
        "ayarlar": ayarlar,
        "admin": admin_user
    })

# --- RÜTBE SİSTEMİ ---
@router.get("/admin/mlm/rutbe", response_class=HTMLResponse)
def admin_mlm_rutbe_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Veritabanından rütbeleri getir (sıraya göre)
    rutbeler = db.query(models.Rutbe).order_by(models.Rutbe.sira).all()

    return templates.TemplateResponse("admin_mlm_rutbe.html", {
        "request": request,
        "rutbeler": rutbeler,
        "admin": admin_user
    })

@router.post("/admin/mlm/rutbe/ekle")
def admin_mlm_rutbe_ekle(
    request: Request,
    ad: str = Form(...),
    sol_pv: int = Form(...),
    sag_pv: int = Form(...),
    renk: str = Form("gray"),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Mevcut maksimum sıra numarasını bul
    max_sira = db.query(models.Rutbe).count()

    # Yeni rütbe ekle
    yeni_rutbe = models.Rutbe(
        ad=ad,
        sol_pv=sol_pv,
        sag_pv=sag_pv,
        renk=renk,
        sira=max_sira + 1
    )
    db.add(yeni_rutbe)
    db.commit()

    return RedirectResponse(url="/admin/mlm/rutbe?basari=eklendi", status_code=303)

@router.post("/admin/mlm/rutbe/guncelle/{rutbe_id}")
def admin_mlm_rutbe_guncelle(
    rutbe_id: int,
    request: Request,
    ad: str = Form(...),
    sol_pv: int = Form(...),
    sag_pv: int = Form(...),
    renk: str = Form("gray"),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    rutbe = db.query(models.Rutbe).filter(models.Rutbe.id == rutbe_id).first()
    if rutbe:
        rutbe.ad = ad
        rutbe.sol_pv = sol_pv
        rutbe.sag_pv = sag_pv
        rutbe.renk = renk
        db.commit()

    return RedirectResponse(url="/admin/mlm/rutbe?basari=guncellendi", status_code=303)

@router.post("/admin/mlm/rutbe/sil/{rutbe_id}")
def admin_mlm_rutbe_sil(
    rutbe_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    rutbe = db.query(models.Rutbe).filter(models.Rutbe.id == rutbe_id).first()
    if rutbe:
        db.delete(rutbe)
        db.commit()

    return RedirectResponse(url="/admin/mlm/rutbe?basari=silindi", status_code=303)

# --- AĞAÇ GÖRÜNÜMÜ ---
@router.get("/admin/mlm/agac", response_class=HTMLResponse)
def admin_mlm_agac_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)
    
    # Root kullanıcıları getir (parent_id = None)
    root_users = db.query(models.Kullanici).filter(
        models.Kullanici.parent_id == None
    ).all()
    
    # Toplam istatistikler
    toplam_uye = db.query(models.Kullanici).count()
    
    return templates.TemplateResponse("admin_mlm_agac.html", {
        "request": request,
        "root_users": root_users,
        "toplam_uye": toplam_uye,
        "admin": admin_user
    })
