"""
SMS Sistemi Modülü Routes
Modül 7: SMS Kampanyaları ve Gönderim
"""
from fastapi import APIRouter, Depends, Request, Form
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
# SMS KAMPANYA YÖNETİMİ
# ============================================================================

@router.get("/admin/sms/campaigns", response_class=HTMLResponse)
def admin_sms_campaigns_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    kampanyalar = db.query(models.SMSKampanya).order_by(models.SMSKampanya.olusturma_tarihi.desc()).all()

    return templates.TemplateResponse("admin_sms_campaigns.html", {
        "request": request,
        "kampanyalar": kampanyalar,
        "admin": admin_user
    })

@router.post("/admin/sms/campaigns/add")
def admin_sms_campaigns_add(
    request: Request,
    baslik: str = Form(...),
    mesaj: str = Form(...),
    hedef: str = Form("tum_uyeler"),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    kampanya = models.SMSKampanya(
        baslik=baslik,
        mesaj=mesaj,
        hedef=hedef,
        aktif=aktif
    )
    db.add(kampanya)
    db.commit()

    return RedirectResponse(url="/admin/sms/campaigns?success=added", status_code=303)

@router.post("/admin/sms/campaigns/delete/{kampanya_id}")
def admin_sms_campaigns_delete(
    kampanya_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    kampanya = db.query(models.SMSKampanya).filter(models.SMSKampanya.id == kampanya_id).first()
    if kampanya:
        db.delete(kampanya)
        db.commit()

    return RedirectResponse(url="/admin/sms/campaigns?success=deleted", status_code=303)

@router.post("/admin/sms/campaigns/send/{kampanya_id}")
def admin_sms_campaigns_send(
    kampanya_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    kampanya = db.query(models.SMSKampanya).filter(models.SMSKampanya.id == kampanya_id).first()
    if not kampanya:
        return RedirectResponse(url="/admin/sms/campaigns?error=notfound", status_code=303)

    # Hedef kitleyı belirle
    if kampanya.hedef == "tum_uyeler":
        uyeler = db.query(models.Uye).filter(models.Uye.aktif == True).all()
    elif kampanya.hedef == "aktif_uyeler":
        uyeler = db.query(models.Uye).filter(models.Uye.aktif == True, models.Uye.onay_durumu == "onaylandi").all()
    else:
        uyeler = []

    # SMS gönderimi simülasyonu (gerçek SMS servisi entegrasyonu gerekir)
    gonderilen = 0
    for uye in uyeler:
        if uye.telefon:
            # SMS log kaydet
            sms_log = models.SMSLog(
                kampanya_id=kampanya_id,
                uye_id=uye.id,
                telefon=uye.telefon,
                mesaj=kampanya.mesaj,
                durum="gonderildi"
            )
            db.add(sms_log)
            gonderilen += 1

    kampanya.gonderilen_sayi = gonderilen
    kampanya.gonderim_tarihi = datetime.utcnow()
    db.commit()

    return RedirectResponse(url=f"/admin/sms/campaigns?success=sent&count={gonderilen}", status_code=303)

# ============================================================================
# SMS LOG GÖRÜNTÜLEMİ
# ============================================================================

@router.get("/admin/sms/logs", response_class=HTMLResponse)
def admin_sms_logs_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    logs = db.query(models.SMSLog).order_by(models.SMSLog.gonderim_tarihi.desc()).limit(100).all()

    return templates.TemplateResponse("admin_sms_logs.html", {
        "request": request,
        "logs": logs,
        "admin": admin_user
    })
