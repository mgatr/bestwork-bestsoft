from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, templates
from app import crud, models
import uuid

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def anasayfa(request: Request, db: Session = Depends(get_db)):
    kategoriler = crud.kategorileri_listele(db)
    urunler = crud.urunleri_listele(db, limit=12)
    sliders = db.query(models.Slider).filter(models.Slider.aktif == True).order_by(models.Slider.sira.asc()).all()
    return templates.TemplateResponse("anasayfa.html", {
        "request": request,
        "kategoriler": kategoriler,
        "urunler": urunler,
        "sliders": sliders,
        "page_title": "Anasayfa"
    })

@router.get("/iletisim", response_class=HTMLResponse)
def iletisim_sayfasi(request: Request, db: Session = Depends(get_db)):
    ayarlar = db.query(models.SiteAyarlari).first()
    return templates.TemplateResponse("iletisim.html", {
        "request": request,
        "page_title": "İletişim",
        "ayarlar": ayarlar
    })

@router.post("/iletisim", response_class=HTMLResponse)
def iletisim_formu_gonder(
    request: Request,
    ad_soyad: str = Form(...),
    email: str = Form(...),
    konu: str = Form(...),
    mesaj: str = Form(...),
    db: Session = Depends(get_db)
):
    # Takip numarası oluştur
    takip_no = str(uuid.uuid4())[:8].upper()
    
    yeni_mesaj = models.IletisimMesaji(
        ad_soyad=ad_soyad,
        email=email,
        konu=konu,
        mesaj=mesaj,
        takip_no=takip_no
    )
    db.add(yeni_mesaj)
    db.commit()
    db.refresh(yeni_mesaj)
    
    ayarlar = db.query(models.SiteAyarlari).first()
    
    return templates.TemplateResponse("iletisim.html", {
        "request": request,
        "page_title": "İletişim",
        "basari_mesaji": f"Mesajınız başarıyla alındı. Takip numaranız: {takip_no}",
        "ayarlar": ayarlar
    })
