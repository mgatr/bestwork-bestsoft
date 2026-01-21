from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, HTMLResponse
import os
import time
import uuid
from PIL import Image
from app import models, crud, schemas
from app.dependencies import get_db, templates, get_current_admin_user

router = APIRouter(
    prefix="/admin/products",
    tags=["Admin Products"],
    dependencies=[Depends(get_current_admin_user)]
)

# --- PANEL GİRİŞ ---
# Bu router altındaki tüm endpoint'ler artık otomatik olarak korunuyor.
# Manuel yetki kontrolüne gerek yok.

@router.get("/", response_class=HTMLResponse)
def products_dashboard(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Urun).count()
    categories = db.query(models.Kategori).count()
    brands = db.query(models.Marka).count()
    low_stock = db.query(models.Urun).filter(models.Urun.stok < 10).count()
    
    return templates.TemplateResponse("admin_products_dashboard.html", {
        "request": request,
        "active_menu": "urunler_modulu",
        "stats": {
            "products": products,
            "categories": categories,
            "brands": brands,
            "low_stock": low_stock
        }
    })

# --- ÜRÜN LİSTESİ ---
@router.get("/list", response_class=HTMLResponse)
def product_list(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Urun).all()
    return templates.TemplateResponse("admin_urun_liste.html", {
        "request": request,
        "products": products,
        "active_menu": "urunler_modulu"
    })

# --- YENİ ÜRÜN EKLEME SAYFASI ---
@router.get("/add", response_class=HTMLResponse)
def product_add_page(request: Request, db: Session = Depends(get_db)):
    categories = db.query(models.Kategori).all()
    brands = db.query(models.Marka).all()
    groups = db.query(models.UrunGrup).all()
    warehouses = db.query(models.Depo).all()
    
    return templates.TemplateResponse("admin_urun_ekle_v2.html", {
        "request": request,
        "categories": categories,
        "brands": brands,
        "groups": groups,
        "warehouses": warehouses,
        "active_menu": "urunler_modulu"
    })

# --- YENİ ÜRÜN KAYDETME ---
@router.post("/add")
async def product_add_action(
    ad: str = Form(...),
    sku: str = Form(None),
    barkod: str = Form(None),
    kategori_id: int = Form(...),
    marka_id: int = Form(None),
    grup_id: int = Form(None),
    fiyat: float = Form(...),
    maliyet: float = Form(0.0),
    katalog_fiyati: float = Form(0.0),
    uye_alis_fiyati: float = Form(0.0),
    kdv_orani: int = Form(20),
    stok: int = Form(0),
    kritik_stok: int = Form(5),
    desi: float = Form(0.0),
    agirlik: float = Form(0.0),
    pv_degeri: int = Form(0),
    cv_degeri: float = Form(0.0),
    seo_baslik: str = Form(None),
    seo_aciklama: str = Form(None),
    kisa_aciklama: str = Form(None),
    aciklama: str = Form(None),
    resim: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    resim_url = ""
    if resim and resim.filename:
        UPLOAD_DIR = "static/uploads/products"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        unique_filename = f"prod_{int(time.time())}_{uuid.uuid4().hex[:8]}.webp"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        try:
            Image.open(resim.file).save(file_path, "WEBP", quality=85)
            resim_url = f"/static/uploads/products/{unique_filename}"
        except Exception as e:
            print(f"Image upload failed: {e}")

    new_product = models.Urun(
        ad=ad, sku=sku, barkod=barkod, kategori_id=kategori_id, marka_id=marka_id,
        grup_id=grup_id, fiyat=fiyat, maliyet=maliyet, katalog_fiyati=katalog_fiyati,
        uye_alis_fiyati=uye_alis_fiyati, kdv_orani=kdv_orani, stok=stok,
        kritik_stok=kritik_stok, desi=desi, agirlik=agirlik, cv_degeri=cv_degeri,
        pv_degeri=pv_degeri, seo_baslik=seo_baslik, seo_aciklama=seo_aciklama,
        kisa_aciklama=kisa_aciklama, aciklama=aciklama, resim_url=resim_url
    )
    
    db.add(new_product)
    db.commit()
    
    return RedirectResponse(url="/admin/products/list", status_code=303)

# --- KATEGORİ YÖNETİMİ ---
@router.get("/categories", response_class=HTMLResponse)
def category_list(request: Request, db: Session = Depends(get_db)):
    categories = db.query(models.Kategori).all()
    return templates.TemplateResponse("admin_kategoriler_v2.html", {
        "request": request,
        "categories": categories,
        "active_menu": "urunler_modulu"
    })

@router.post("/categories/add")
async def category_add(
    ad: str = Form(...),
    ust_kategori_id: int = Form(None),
    aciklama: str = Form(None),
    seo_baslik: str = Form(None),
    resim: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    resim_url = ""
    if resim and resim.filename:
        upload_dir = "static/uploads/categories"
        os.makedirs(upload_dir, exist_ok=True)
        unique_filename = f"{uuid.uuid4()}.webp"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with Image.open(resim.file) as img:
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            img.save(file_path, 'WEBP', quality=85)
        resim_url = f"/{file_path}"
        
    new_cat = models.Kategori(
        ad=ad, ust_kategori_id=ust_kategori_id, aciklama=aciklama, 
        seo_baslik=seo_baslik, resim_url=resim_url
    )
    db.add(new_cat)
    db.commit()
    return RedirectResponse(url="/admin/products/categories", status_code=303)

@router.post("/categories/update")
async def category_update(
    kategori_id: int = Form(...),
    ad: str = Form(...),
    ust_kategori_id: int = Form(None),
    aciklama: str = Form(None),
    seo_baslik: str = Form(None),
    resim: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    category = db.get(models.Kategori, kategori_id)
    if not category:
        return RedirectResponse(url="/admin/products/categories", status_code=303)
        
    category.ad = ad
    category.ust_kategori_id = ust_kategori_id
    category.aciklama = aciklama
    category.seo_baslik = seo_baslik
    
    if resim and resim.filename:
        upload_dir = "static/uploads/categories"
        os.makedirs(upload_dir, exist_ok=True)
        unique_filename = f"{uuid.uuid4()}.webp"
        file_path = os.path.join(upload_dir, unique_filename)
        with Image.open(resim.file) as img:
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            img.save(file_path, 'WEBP', quality=85)
        category.resim_url = f"/{file_path}"

    db.commit()
    return RedirectResponse(url="/admin/products/categories", status_code=303)

@router.post("/categories/delete")
async def category_delete(kategori_id: int = Form(...), db: Session = Depends(get_db)):
    category = db.get(models.Kategori, kategori_id)
    if category:
        # Opsiyonel: Kategoriye bağlı ürünlerin resimlerini de sil
        if category.resim_url and os.path.exists(category.resim_url.lstrip('/')):
            os.remove(category.resim_url.lstrip('/'))
        db.delete(category)
        db.commit()
    
    return RedirectResponse(url="/admin/products/categories", status_code=303)

# --- MARKA YÖNETİMİ ---
@router.get("/brands", response_class=HTMLResponse)
def brand_list(request: Request, db: Session = Depends(get_db)):
    brands = db.query(models.Marka).all()
    return templates.TemplateResponse("admin_markalar.html", {
        "request": request,
        "brands": brands,
        "active_menu": "urunler_modulu"
    })

@router.post("/brands/add")
async def brand_add(ad: str = Form(...), db: Session = Depends(get_db)):
    new_brand = models.Marka(ad=ad)
    db.add(new_brand)
    db.commit()
    return RedirectResponse(url="/admin/products/brands", status_code=303)

