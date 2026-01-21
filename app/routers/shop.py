"""
Shop Router - E-ticaret endpoint'leri.

Bu router, mağaza, ürün listeleme, sepet ve sipariş işlemlerini yönetir.
İş mantığı için CRUD yerine Service katmanını kullanır.

Mimari Notları:
- Basit CRUD işlemleri için crud.* kullanılır (sadece SELECT)
- İş mantığı gerektiren işlemler için OrderService kullanılır
- Router sadece HTTP katmanı ile ilgilenir, iş mantığını servislere delege eder
"""
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse

from app import models, crud
from app.dependencies import get_db, templates
from app.services import OrderService

router = APIRouter()


# KATEGORİ SAYFASI
@router.get("/kategori/{kategori_id}", response_class=HTMLResponse)
def kategori_sayfasi(request: Request, kategori_id: int, db: Session = Depends(get_db)):
    """Kategori sayfası - Belirli bir kategorideki ürünleri listeler."""
    # Repository katmanı: Sadece veri çekme
    kategori = crud.kategori_getir(db, kategori_id)
    if not kategori:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı!")

    urunler = crud.urunleri_listele(db, kategori_id=kategori_id)
    kategoriler = crud.kategorileri_listele(db)

    return templates.TemplateResponse("kategori.html", {
        "request": request,
        "kategori": kategori,
        "kategoriler": kategoriler,
        "urunler": urunler,
        "page_title": kategori.ad
    })


# ÜRÜN DETAY
@router.get("/urun/{urun_id}", response_class=HTMLResponse)
def urun_detay(request: Request, urun_id: int, db: Session = Depends(get_db)):
    """Ürün detay sayfası."""
    # Repository katmanı: Sadece veri çekme
    urun = crud.urun_getir(db, urun_id)
    if not urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı!")

    return templates.TemplateResponse("urun_detay.html", {
        "request": request,
        "urun": urun,
        "page_title": urun.ad
    })


# SEPET
@router.get("/sepet/{kullanici_id}", response_class=HTMLResponse)
def sepet_sayfasi(request: Request, kullanici_id: int, db: Session = Depends(get_db)):
    """Sepet sayfası - Kullanıcının sepetini gösterir."""
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=303)
    if request.state.user.id != kullanici_id:
        return RedirectResponse(url=f"/sepet/{request.state.user.id}", status_code=303)

    # Repository katmanı: Sadece veri çekme
    sepet = crud.sepet_detayi_getir(db, kullanici_id)

    return templates.TemplateResponse("sepet.html", {
        "request": request,
        "sepet": sepet,
        "kullanici_id": kullanici_id,
        "page_title": "Sepetim"
    })


# API: Sepete Ürün Ekle
@router.post("/api/sepet/{kullanici_id}/ekle")
def sepete_ekle_api(
    request: Request,
    kullanici_id: int,
    urun_id: int = Form(...),
    adet: int = Form(1),
    db: Session = Depends(get_db)
):
    """Sepete ürün ekler."""
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=303)

    # Güvenlik: Başkasının sepetine eklemeyi engelle
    if request.state.user.id != kullanici_id:
        crud.sepete_urun_ekle(db, request.state.user.id, urun_id, adet)
        return RedirectResponse(url=f"/sepet/{request.state.user.id}", status_code=303)

    # Repository katmanı: Basit INSERT/UPDATE işlemi
    crud.sepete_urun_ekle(db, kullanici_id, urun_id, adet)
    return RedirectResponse(url=f"/sepet/{kullanici_id}", status_code=303)


# API: Sepetten Ürün Çıkar
@router.get("/api/sepet/{kullanici_id}/cikar/{sepet_urun_id}")
def sepetten_cikar_api(
    request: Request,
    kullanici_id: int,
    sepet_urun_id: int,
    db: Session = Depends(get_db)
):
    """Sepetten ürün çıkarır."""
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=303)
    if request.state.user.id != kullanici_id:
        return RedirectResponse(url=f"/sepet/{request.state.user.id}", status_code=303)

    # Repository katmanı: Basit DELETE işlemi
    crud.sepetten_urun_cikar(db, kullanici_id, sepet_urun_id)
    return RedirectResponse(url=f"/sepet/{kullanici_id}", status_code=303)


# API: Sipariş Oluştur
@router.post("/api/siparis/{kullanici_id}/olustur")
def siparis_olustur_api(
    request: Request,
    kullanici_id: int,
    adres: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Sipariş oluşturur.

    SERVICE LAYER KULLANIMI:
    Bu endpoint iş mantığı içerdiği için OrderService'i kullanır.
    Service katmanı şunları yapar:
    - Sepet validasyonu
    - Sipariş oluşturma
    - PV/CV hesaplama
    - Ekonomi tetikleme (puan dağıtımı)
    """
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=303)
    if request.state.user.id != kullanici_id:
        return RedirectResponse(url=f"/sepet/{request.state.user.id}", status_code=303)

    # Service katmanı: İş mantığını yönetir
    siparis = OrderService.create_order(db, kullanici_id, adres)
    return RedirectResponse(url=f"/siparisler/{kullanici_id}", status_code=303)


# SİPARİŞLERİM
@router.get("/siparisler/{kullanici_id}", response_class=HTMLResponse)
def siparisler_sayfasi(request: Request, kullanici_id: int, db: Session = Depends(get_db)):
    """Kullanıcının siparişlerini listeler."""
    if not request.state.user:
        return RedirectResponse(url="/giris", status_code=303)
    if request.state.user.id != kullanici_id:
        return RedirectResponse(url=f"/siparisler/{request.state.user.id}", status_code=303)

    # Repository katmanı: Sadece veri çekme
    siparisler = crud.kullanici_siparislerini_getir(db, kullanici_id)

    return templates.TemplateResponse("siparisler.html", {
        "request": request,
        "siparisler": siparisler,
        "kullanici_id": kullanici_id,
        "page_title": "Siparişlerim"
    })


# MAĞAZA (TÜM ÜRÜNLER)
@router.get("/urunler", response_class=HTMLResponse)
def magaza_sayfasi(request: Request, db: Session = Depends(get_db)):
    """Ana mağaza sayfası - Tüm ürünleri listeler."""
    # Repository katmanı: Sadece veri çekme
    kategoriler = crud.kategorileri_listele(db)
    urunler = crud.urunleri_listele(db, limit=100)

    # Kategori ürün sayılarını hesapla
    for kat in kategoriler:
        kat.urun_sayisi = db.query(models.Urun).filter(
            models.Urun.kategori_id == kat.id,
            models.Urun.aktif == True
        ).count()

    return templates.TemplateResponse("magaza.html", {
        "request": request,
        "kategoriler": kategoriler,
        "urunler": urunler,
        "page_title": "Mağaza"
    })