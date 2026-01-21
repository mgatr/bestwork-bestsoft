"""
Katalog Modülü Routes
Modül 9: Dijital Kataloglar ve Sayfalar
"""
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
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
# KATALOG YÖNETİMİ
# ============================================================================

@router.get("/admin/catalogs/list", response_class=HTMLResponse)
def admin_catalogs_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    kataloglar = db.query(models.Katalog).order_by(models.Katalog.olusturma_tarihi.desc()).all()

    return templates.TemplateResponse("admin_catalogs.html", {
        "request": request,
        "kataloglar": kataloglar,
        "admin": admin_user
    })

@router.post("/admin/catalogs/add")
def admin_catalogs_add(
    request: Request,
    baslik: str = Form(...),
    aciklama: Optional[str] = Form(None),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    katalog = models.Katalog(
        baslik=baslik,
        aciklama=aciklama,
        aktif=aktif
    )
    db.add(katalog)
    db.commit()

    return RedirectResponse(url="/admin/catalogs/list?success=added", status_code=303)

@router.post("/admin/catalogs/delete/{katalog_id}")
def admin_catalogs_delete(
    katalog_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    katalog = db.query(models.Katalog).filter(models.Katalog.id == katalog_id).first()
    if katalog:
        db.delete(katalog)
        db.commit()

    return RedirectResponse(url="/admin/catalogs/list?success=deleted", status_code=303)

# ============================================================================
# KATALOG SAYFALARI YÖNETİMİ
# ============================================================================

@router.get("/admin/catalogs/{katalog_id}/pages", response_class=HTMLResponse)
def admin_catalog_pages(
    katalog_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    katalog = db.query(models.Katalog).filter(models.Katalog.id == katalog_id).first()
    if not katalog:
        return RedirectResponse(url="/admin/catalogs/list?error=notfound", status_code=303)

    sayfalar = db.query(models.KatalogSayfa).filter(
        models.KatalogSayfa.katalog_id == katalog_id
    ).order_by(models.KatalogSayfa.sayfa_no).all()

    return templates.TemplateResponse("admin_catalog_pages.html", {
        "request": request,
        "katalog": katalog,
        "sayfalar": sayfalar,
        "admin": admin_user
    })

@router.post("/admin/catalogs/{katalog_id}/pages/add")
def admin_catalog_pages_add(
    katalog_id: int,
    request: Request,
    sayfa_no: int = Form(...),
    baslik: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    # Resim upload işlemi sonra eklenecek
    sayfa = models.KatalogSayfa(
        katalog_id=katalog_id,
        sayfa_no=sayfa_no,
        baslik=baslik,
        resim_yolu="/static/catalogs/placeholder.jpg"
    )
    db.add(sayfa)
    db.commit()

    return RedirectResponse(url=f"/admin/catalogs/{katalog_id}/pages?success=added", status_code=303)

@router.post("/admin/catalogs/{katalog_id}/pages/delete/{sayfa_id}")
def admin_catalog_pages_delete(
    katalog_id: int,
    sayfa_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    sayfa = db.query(models.KatalogSayfa).filter(models.KatalogSayfa.id == sayfa_id).first()
    if sayfa:
        db.delete(sayfa)
        db.commit()

    return RedirectResponse(url=f"/admin/catalogs/{katalog_id}/pages?success=deleted", status_code=303)
