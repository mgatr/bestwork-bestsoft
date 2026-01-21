"""
Form Builder Modülü Routes
Modül 14: Dinamik Formlar ve Cevaplar
"""
from fastapi import APIRouter, Depends, Request, Form as FormField
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import json

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
# FORM YÖNETİMİ
# ============================================================================

@router.get("/admin/forms/list", response_class=HTMLResponse)
def admin_forms_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    formlar = db.query(models.Form).order_by(models.Form.olusturma_tarihi.desc()).all()

    return templates.TemplateResponse("admin_forms.html", {
        "request": request,
        "formlar": formlar,
        "admin": admin_user
    })

@router.post("/admin/forms/add")
def admin_forms_add(
    request: Request,
    baslik: str = FormField(...),
    aciklama: Optional[str] = FormField(None),
    alan_tanimlari: str = FormField(...),
    aktif: bool = FormField(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    form = models.Form(
        baslik=baslik,
        aciklama=aciklama,
        alan_tanimlari=alan_tanimlari,
        aktif=aktif
    )
    db.add(form)
    db.commit()

    return RedirectResponse(url="/admin/forms/list?success=added", status_code=303)

@router.post("/admin/forms/delete/{form_id}")
def admin_forms_delete(
    form_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    form = db.query(models.Form).filter(models.Form.id == form_id).first()
    if form:
        db.delete(form)
        db.commit()

    return RedirectResponse(url="/admin/forms/list?success=deleted", status_code=303)

# ============================================================================
# FORM CEVAPLARI
# ============================================================================

@router.get("/admin/forms/{form_id}/responses", response_class=HTMLResponse)
def admin_form_responses(
    form_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    form = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not form:
        return RedirectResponse(url="/admin/forms/list?error=notfound", status_code=303)

    cevaplar = db.query(models.FormCevap).filter(
        models.FormCevap.form_id == form_id
    ).order_by(models.FormCevap.gonderim_tarihi.desc()).all()

    return templates.TemplateResponse("admin_form_responses.html", {
        "request": request,
        "form": form,
        "cevaplar": cevaplar,
        "admin": admin_user
    })

@router.post("/admin/forms/{form_id}/responses/delete/{cevap_id}")
def admin_form_responses_delete(
    form_id: int,
    cevap_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    cevap = db.query(models.FormCevap).filter(models.FormCevap.id == cevap_id).first()
    if cevap:
        db.delete(cevap)
        db.commit()

    return RedirectResponse(url=f"/admin/forms/{form_id}/responses?success=deleted", status_code=303)

# ============================================================================
# GENEL KULLANICI FORM GÖRÜNTÜLEMİ (Frontend)
# ============================================================================

@router.get("/forms/{form_id}", response_class=HTMLResponse)
def public_form_view(
    form_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    form = db.query(models.Form).filter(
        models.Form.id == form_id,
        models.Form.aktif == True
    ).first()

    if not form:
        return RedirectResponse(url="/?error=form_not_found", status_code=303)

    return templates.TemplateResponse("public_form.html", {
        "request": request,
        "form": form
    })

@router.post("/forms/{form_id}/submit")
async def public_form_submit(
    form_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    form = db.query(models.Form).filter(models.Form.id == form_id).first()
    if not form:
        return RedirectResponse(url="/?error=form_not_found", status_code=303)

    # Form verilerini al
    form_data = await request.form()
    cevaplar_dict = dict(form_data)

    # Üye ID'sini cookie'den al (varsa)
    uye_id = request.cookies.get("user_session")

    cevap = models.FormCevap(
        form_id=form_id,
        uye_id=int(uye_id) if uye_id else None,
        cevaplar=json.dumps(cevaplar_dict, ensure_ascii=False)
    )
    db.add(cevap)
    db.commit()

    return RedirectResponse(url=f"/forms/{form_id}?success=submitted", status_code=303)
