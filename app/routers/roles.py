"""
Yetki Yönetimi Modülü Routes
Modül 10: Roller ve Yetkiler
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_current_admin(request: Request):
    """Admin oturum kontrolü"""
    admin_id = request.cookies.get("admin_session")
    if not admin_id:
        return None
    return {"id": admin_id}

# ============================================================================
# ROL YÖNETİMİ
# ============================================================================

@router.get("/admin/roles/list", response_class=HTMLResponse)
def admin_roles_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    roller = db.query(models.Rol).order_by(models.Rol.ad).all()

    return templates.TemplateResponse("admin_roles.html", {
        "request": request,
        "roller": roller,
        "admin": admin_user
    })

@router.post("/admin/roles/add")
def admin_roles_add(
    request: Request,
    ad: str = Form(...),
    aciklama: Optional[str] = Form(None),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    rol = models.Rol(
        ad=ad,
        aciklama=aciklama,
        aktif=aktif
    )
    db.add(rol)
    db.commit()

    return RedirectResponse(url="/admin/roles/list?success=added", status_code=303)

@router.post("/admin/roles/delete/{rol_id}")
def admin_roles_delete(
    rol_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    rol = db.query(models.Rol).filter(models.Rol.id == rol_id).first()
    if rol:
        db.delete(rol)
        db.commit()

    return RedirectResponse(url="/admin/roles/list?success=deleted", status_code=303)

# ============================================================================
# YETKİ YÖNETİMİ
# ============================================================================

@router.get("/admin/roles/{rol_id}/permissions", response_class=HTMLResponse)
def admin_permissions_page(
    rol_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    rol = db.query(models.Rol).filter(models.Rol.id == rol_id).first()
    if not rol:
        return RedirectResponse(url="/admin/roles/list?error=notfound", status_code=303)

    yetkiler = db.query(models.Yetki).filter(models.Yetki.rol_id == rol_id).all()

    # Mevcut modüller
    moduller = [
        "site_yonetimi", "firma_bilgileri", "urunler", "mlm_sistemi",
        "icerik_yonetimi", "ebulten", "sms", "bankalar", "kataloglar",
        "siparisler", "uyeler", "tanimlar", "formlar", "raporlar"
    ]

    return templates.TemplateResponse("admin_permissions.html", {
        "request": request,
        "rol": rol,
        "yetkiler": yetkiler,
        "moduller": moduller,
        "admin": admin_user
    })

@router.post("/admin/roles/{rol_id}/permissions/update")
def admin_permissions_update(
    rol_id: int,
    request: Request,
    modul: str = Form(...),
    okuma: bool = Form(False),
    yazma: bool = Form(False),
    silme: bool = Form(False),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Mevcut yetkiyi bul veya oluştur
    yetki = db.query(models.Yetki).filter(
        models.Yetki.rol_id == rol_id,
        models.Yetki.modul == modul
    ).first()

    if yetki:
        yetki.okuma = okuma
        yetki.yazma = yazma
        yetki.silme = silme
    else:
        yetki = models.Yetki(
            rol_id=rol_id,
            modul=modul,
            okuma=okuma,
            yazma=yazma,
            silme=silme
        )
        db.add(yetki)

    db.commit()

    return RedirectResponse(url=f"/admin/roles/{rol_id}/permissions?success=updated", status_code=303)
