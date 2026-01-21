"""
İçerik Yönetimi Modülü Routes
Modül 5: Bannerlar, Blog, Etkinlikler, Anketler
"""
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.dependencies import get_db
from app import models
from .admin import get_current_admin

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ============================================================================
# BANNER YÖNETİMİ
# ============================================================================

@router.get("/admin/content/banners", response_class=HTMLResponse)
def admin_banners_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    banners = db.query(models.Banner).order_by(models.Banner.sira).all()

    return templates.TemplateResponse("admin_content_banners.html", {
        "request": request,
        "banners": banners,
        "admin": admin_user
    })

@router.post("/admin/content/banners/add")
async def admin_banners_add(
    request: Request,
    baslik: str = Form(...),
    aciklama: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    konum: str = Form("anasayfa"),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Yeni banner ekle (resim upload işlemi sonra eklenecek)
    banner = models.Banner(
        baslik=baslik,
        aciklama=aciklama,
        resim_yolu="/static/banners/default.jpg",  # Placeholder
        link=link,
        konum=konum,
        aktif=aktif
    )
    db.add(banner)
    db.commit()

    return RedirectResponse(url="/admin/content/banners?success=added", status_code=303)

@router.post("/admin/content/banners/delete/{banner_id}")
def admin_banners_delete(
    banner_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    banner = db.query(models.Banner).filter(models.Banner.id == banner_id).first()
    if banner:
        db.delete(banner)
        db.commit()

    return RedirectResponse(url="/admin/content/banners?success=deleted", status_code=303)

# ============================================================================
# BLOG YÖNETİMİ
# ============================================================================

@router.get("/admin/content/blog", response_class=HTMLResponse)
def admin_blog_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    yazilar = db.query(models.BlogYazi).order_by(models.BlogYazi.yayinlanma_tarihi.desc()).all()

    return templates.TemplateResponse("admin_content_blog.html", {
        "request": request,
        "yazilar": yazilar,
        "admin": admin_user
    })

@router.post("/admin/content/blog/add")
def admin_blog_add(
    request: Request,
    baslik: str = Form(...),
    ozet: Optional[str] = Form(None),
    icerik: str = Form(...),
    kategori: Optional[str] = Form(None),
    etiketler: Optional[str] = Form(None),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Slug oluştur
    import re
    slug = re.sub(r'[^\w\s-]', '', baslik.lower())
    slug = re.sub(r'[-\s]+', '-', slug)

    yazi = models.BlogYazi(
        baslik=baslik,
        slug=slug,
        ozet=ozet,
        icerik=icerik,
        kategori=kategori,
        etiketler=etiketler,
        aktif=aktif
    )
    db.add(yazi)
    db.commit()

    return RedirectResponse(url="/admin/content/blog?success=added", status_code=303)

@router.post("/admin/content/blog/delete/{yazi_id}")
def admin_blog_delete(
    yazi_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    yazi = db.query(models.BlogYazi).filter(models.BlogYazi.id == yazi_id).first()
    if yazi:
        db.delete(yazi)
        db.commit()

    return RedirectResponse(url="/admin/content/blog?success=deleted", status_code=303)

# ============================================================================
# ETKİNLİK YÖNETİMİ
# ============================================================================

@router.get("/admin/content/events", response_class=HTMLResponse)
def admin_events_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    etkinlikler = db.query(models.Etkinlik).order_by(models.Etkinlik.etkinlik_tarihi.desc()).all()

    return templates.TemplateResponse("admin_content_events.html", {
        "request": request,
        "etkinlikler": etkinlikler,
        "admin": admin_user
    })

@router.post("/admin/content/events/add")
def admin_events_add(
    request: Request,
    baslik: str = Form(...),
    aciklama: Optional[str] = Form(None),
    etkinlik_tarihi: str = Form(...),
    konum: Optional[str] = Form(None),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Tarih parse et
    from datetime import datetime
    tarih = datetime.fromisoformat(etkinlik_tarihi)

    etkinlik = models.Etkinlik(
        baslik=baslik,
        aciklama=aciklama,
        etkinlik_tarihi=tarih,
        konum=konum,
        aktif=aktif
    )
    db.add(etkinlik)
    db.commit()

    return RedirectResponse(url="/admin/content/events?success=added", status_code=303)

@router.post("/admin/content/events/delete/{etkinlik_id}")
def admin_events_delete(
    etkinlik_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    etkinlik = db.query(models.Etkinlik).filter(models.Etkinlik.id == etkinlik_id).first()
    if etkinlik:
        db.delete(etkinlik)
        db.commit()

    return RedirectResponse(url="/admin/content/events?success=deleted", status_code=303)

# ============================================================================
# ANKET YÖNETİMİ
# ============================================================================

@router.get("/admin/content/polls", response_class=HTMLResponse)
def admin_polls_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    anketler = db.query(models.Anket).order_by(models.Anket.olusturma_tarihi.desc()).all()

    return templates.TemplateResponse("admin_content_polls.html", {
        "request": request,
        "anketler": anketler,
        "admin": admin_user
    })

@router.post("/admin/content/polls/add")
def admin_polls_add(
    request: Request,
    baslik: str = Form(...),
    aciklama: Optional[str] = Form(None),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    anket = models.Anket(
        baslik=baslik,
        aciklama=aciklama,
        aktif=aktif
    )
    db.add(anket)
    db.commit()

    return RedirectResponse(url="/admin/content/polls?success=added", status_code=303)

@router.post("/admin/content/polls/delete/{anket_id}")
def admin_polls_delete(
    anket_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    anket = db.query(models.Anket).filter(models.Anket.id == anket_id).first()
    if anket:
        db.delete(anket)
        db.commit()

    return RedirectResponse(url="/admin/content/polls?success=deleted", status_code=303)
