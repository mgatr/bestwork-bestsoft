"""
Banka ve Ödeme Modülü Routes
Modül 8: Bankalar, Hesaplar, Dövizler
"""
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal

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
# BANKA YÖNETİMİ
# ============================================================================

@router.get("/admin/banks/list", response_class=HTMLResponse)
def admin_banks_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    bankalar = db.query(models.Banka).order_by(models.Banka.ad).all()

    return templates.TemplateResponse("admin_banks.html", {
        "request": request,
        "bankalar": bankalar,
        "admin": admin_user
    })

@router.post("/admin/banks/add")
def admin_banks_add(
    request: Request,
    ad: str = Form(...),
    kod: Optional[str] = Form(None),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    banka = models.Banka(
        ad=ad,
        kod=kod,
        aktif=aktif
    )
    db.add(banka)
    db.commit()

    return RedirectResponse(url="/admin/banks/list?success=added", status_code=303)

@router.post("/admin/banks/delete/{banka_id}")
def admin_banks_delete(
    banka_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    banka = db.query(models.Banka).filter(models.Banka.id == banka_id).first()
    if banka:
        db.delete(banka)
        db.commit()

    return RedirectResponse(url="/admin/banks/list?success=deleted", status_code=303)

# ============================================================================
# BANKA HESAPLARI YÖNETİMİ
# ============================================================================

@router.get("/admin/banks/accounts", response_class=HTMLResponse)
def admin_bank_accounts_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    hesaplar = db.query(models.BankaHesap).all()
    bankalar = db.query(models.Banka).filter(models.Banka.aktif == True).all()
    dovizler = db.query(models.Doviz).all()

    return templates.TemplateResponse("admin_bank_accounts.html", {
        "request": request,
        "hesaplar": hesaplar,
        "bankalar": bankalar,
        "dovizler": dovizler,
        "admin": admin_user
    })

@router.post("/admin/banks/accounts/add")
def admin_bank_accounts_add(
    request: Request,
    banka_id: int = Form(...),
    hesap_adi: str = Form(...),
    iban: str = Form(...),
    doviz_id: int = Form(...),
    aktif: bool = Form(True),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    hesap = models.BankaHesap(
        banka_id=banka_id,
        hesap_adi=hesap_adi,
        iban=iban,
        doviz_id=doviz_id,
        bakiye=Decimal("0.00"),
        aktif=aktif
    )
    db.add(hesap)
    db.commit()

    return RedirectResponse(url="/admin/banks/accounts?success=added", status_code=303)

@router.post("/admin/banks/accounts/delete/{hesap_id}")
def admin_bank_accounts_delete(
    hesap_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    hesap = db.query(models.BankaHesap).filter(models.BankaHesap.id == hesap_id).first()
    if hesap:
        db.delete(hesap)
        db.commit()

    return RedirectResponse(url="/admin/banks/accounts?success=deleted", status_code=303)

# ============================================================================
# DÖVİZ YÖNETİMİ
# ============================================================================

@router.get("/admin/banks/currency", response_class=HTMLResponse)
def admin_currency_page(request: Request, db: Session = Depends(get_db)):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    dovizler = db.query(models.Doviz).order_by(models.Doviz.kod).all()

    return templates.TemplateResponse("admin_currency.html", {
        "request": request,
        "dovizler": dovizler,
        "admin": admin_user
    })

@router.post("/admin/banks/currency/add")
def admin_currency_add(
    request: Request,
    kod: str = Form(...),
    ad: str = Form(...),
    sembol: str = Form(...),
    alis: str = Form(...),
    satis: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    doviz = models.Doviz(
        kod=kod.upper(),
        ad=ad,
        sembol=sembol,
        alis=Decimal(alis),
        satis=Decimal(satis)
    )
    db.add(doviz)
    db.commit()

    return RedirectResponse(url="/admin/banks/currency?success=added", status_code=303)

@router.post("/admin/banks/currency/update/{doviz_id}")
def admin_currency_update(
    doviz_id: int,
    request: Request,
    alis: str = Form(...),
    satis: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    doviz = db.query(models.Doviz).filter(models.Doviz.id == doviz_id).first()
    if doviz:
        doviz.alis = Decimal(alis)
        doviz.satis = Decimal(satis)
        db.commit()

    return RedirectResponse(url="/admin/banks/currency?success=updated", status_code=303)

@router.post("/admin/banks/currency/delete/{doviz_id}")
def admin_currency_delete(
    doviz_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    admin_user = get_current_admin(request)
    if not admin_user:
        return RedirectResponse(url="/bestsoft", status_code=303)

    doviz = db.query(models.Doviz).filter(models.Doviz.id == doviz_id).first()
    if doviz:
        db.delete(doviz)
        db.commit()

    return RedirectResponse(url="/admin/banks/currency?success=deleted", status_code=303)
