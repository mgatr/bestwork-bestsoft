"""
E-Bülten Modülü Routes
Modül 6: Email listesi, şablonlar, kampanyalar
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app import models
from .admin import get_current_admin

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ============================================================================
# ABONE YÖNETİMİ
# ============================================================================

@router.get("/admin/ebulten/subscribers", response_class=HTMLResponse)
def admin_ebulten_subscribers(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    aboneler = db.query(models.EBultenAbone).order_by(models.EBultenAbone.kayit_tarihi.desc()).all()
    toplam = db.query(models.EBultenAbone).count()
    aktif = db.query(models.EBultenAbone).filter(models.EBultenAbone.aktif == True).count()

    return templates.TemplateResponse("admin_ebulten_subscribers.html", {
        "request": request,
        "aboneler": aboneler,
        "toplam": toplam,
        "aktif": aktif,
        "admin": admin_user
    })

@router.post("/admin/ebulten/subscribers/add")
def admin_ebulten_subscribers_add(
    request: Request,
    email: str = Form(...),
    ad_soyad: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Zaten var mı kontrol et
    mevcut = db.query(models.EBultenAbone).filter(models.EBultenAbone.email == email).first()
    if mevcut:
        return RedirectResponse(url="/admin/ebulten/subscribers?error=exists", status_code=303)

    abone = models.EBultenAbone(
        email=email,
        ad_soyad=ad_soyad,
        aktif=True,
        dogrulandi=True  # Admin eklediyse otomatik doğrula
    )
    db.add(abone)
    db.commit()

    return RedirectResponse(url="/admin/ebulten/subscribers?success=added", status_code=303)

@router.post("/admin/ebulten/subscribers/delete/{abone_id}")
def admin_ebulten_subscribers_delete(
    abone_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    abone = db.query(models.EBultenAbone).filter(models.EBultenAbone.id == abone_id).first()
    if abone:
        db.delete(abone)
        db.commit()

    return RedirectResponse(url="/admin/ebulten/subscribers?success=deleted", status_code=303)

# ============================================================================
# ŞABLON YÖNETİMİ
# ============================================================================

@router.get("/admin/ebulten/templates", response_class=HTMLResponse)
def admin_ebulten_templates(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    sablonlar = db.query(models.EBultenSablon).order_by(models.EBultenSablon.olusturma_tarihi.desc()).all()

    return templates.TemplateResponse("admin_ebulten_templates.html", {
        "request": request,
        "sablonlar": sablonlar,
        "admin": admin_user
    })

@router.post("/admin/ebulten/templates/add")
def admin_ebulten_templates_add(
    request: Request,
    ad: str = Form(...),
    konu: str = Form(...),
    html_icerik: str = Form(...),
    aciklama: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    sablon = models.EBultenSablon(
        ad=ad,
        konu=konu,
        html_icerik=html_icerik,
        aciklama=aciklama
    )
    db.add(sablon)
    db.commit()

    return RedirectResponse(url="/admin/ebulten/templates?success=added", status_code=303)

@router.post("/admin/ebulten/templates/delete/{sablon_id}")
def admin_ebulten_templates_delete(
    sablon_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    sablon = db.query(models.EBultenSablon).filter(models.EBultenSablon.id == sablon_id).first()
    if sablon:
        db.delete(sablon)
        db.commit()

    return RedirectResponse(url="/admin/ebulten/templates?success=deleted", status_code=303)

# ============================================================================
# KAMPANYA YÖNETİMİ
# ============================================================================

@router.get("/admin/ebulten/campaigns", response_class=HTMLResponse)
def admin_ebulten_campaigns(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    kampanyalar = db.query(models.EBultenKampanya).order_by(models.EBultenKampanya.olusturma_tarihi.desc()).all()

    return templates.TemplateResponse("admin_ebulten_campaigns.html", {
        "request": request,
        "kampanyalar": kampanyalar,
        "admin": admin_user
    })

@router.post("/admin/ebulten/campaigns/add")
def admin_ebulten_campaigns_add(
    request: Request,
    ad: str = Form(...),
    konu: str = Form(...),
    html_icerik: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Aktif abone sayısını al
    abone_sayisi = db.query(models.EBultenAbone).filter(
        models.EBultenAbone.aktif == True,
        models.EBultenAbone.dogrulandi == True
    ).count()

    kampanya = models.EBultenKampanya(
        ad=ad,
        konu=konu,
        html_icerik=html_icerik,
        gonderilecek_sayi=abone_sayisi,
        durum="taslak"
    )
    db.add(kampanya)
    db.commit()

    return RedirectResponse(url="/admin/ebulten/campaigns?success=added", status_code=303)

@router.post("/admin/ebulten/campaigns/send/{kampanya_id}")
def admin_ebulten_campaigns_send(
    kampanya_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Kampanyayı gönderime hazırla
    Not: Gerçek email gönderimi için SMTP konfigürasyonu gerekli
    """
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    kampanya = db.query(models.EBultenKampanya).filter(models.EBultenKampanya.id == kampanya_id).first()
    if kampanya and kampanya.durum == "taslak":
        kampanya.durum = "gonderiliyor"
        db.commit()

        # TODO: Asenkron email gönderimi (Celery task)
        # send_campaign_emails.delay(kampanya_id)

    return RedirectResponse(url="/admin/ebulten/campaigns?success=sending", status_code=303)
