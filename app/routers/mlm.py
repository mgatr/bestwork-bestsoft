from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, RedirectResponse, HTMLResponse
from app import models, crud
from app.dependencies import get_db, templates
from app.redis_client import cache_get, cache_set, cache_delete_pattern # Redis istemcisi

router = APIRouter()


def _build_tree_from_flat_data(nodes_data: list, root_id: int, max_depth: int = 3) -> dict:
    """
    Düz liste verisinden hiyerarşik ağaç yapısını oluşturur.
    CTE sorgusu sonucu tek seferde gelen veriyi ağaca dönüştürür.

    Args:
        nodes_data: CTE'den gelen düğüm listesi
        root_id: Kök kullanıcı ID'si
        max_depth: Maksimum ağaç derinliği

    Returns:
        Hiyerarşik ağaç yapısı (dict)
    """
    if not nodes_data:
        return None

    # ID'ye göre hızlı erişim için index oluştur
    nodes_by_id = {node["id"]: node for node in nodes_data}

    # Her node için children listesi oluştur
    children_map = {}
    for node in nodes_data:
        parent_id = node["parent_id"]
        if parent_id not in children_map:
            children_map[parent_id] = {"SOL": None, "SAG": None}
        if node["kol"]:
            children_map[parent_id][node["kol"]] = node["id"]

    def build_subtree(node_id, current_depth=0):
        if node_id not in nodes_by_id:
            return None

        node = nodes_by_id[node_id]

        # Derinlik kontrolü
        if current_depth > max_depth:
            return {
                "name": "Daha Fazla...",
                "id": node_id,
                "uye_no": "",
                "pv": "",
                "children": [],
                "expandable": True
            }

        sol_pv = node.get("sol_pv", 0) or 0
        sag_pv = node.get("sag_pv", 0) or 0

        # Çocukları bul
        children_info = children_map.get(node_id, {"SOL": None, "SAG": None})
        sol_child_id = children_info["SOL"]
        sag_child_id = children_info["SAG"]

        # Sol ve sağ çocukları oluştur
        sol_child = None
        sag_child = None

        if sol_child_id:
            sol_child = build_subtree(sol_child_id, current_depth + 1)
        if sag_child_id:
            sag_child = build_subtree(sag_child_id, current_depth + 1)

        return {
            "name": node["tam_ad"],
            "id": node["id"],
            "uye_no": node["uye_no"],
            "pv": f"Sol: {sol_pv} | Sağ: {sag_pv}",
            "children": [
                sol_child if sol_child else {"name": "Boş", "id": None, "kol": "SOL", "parent": node_id},
                sag_child if sag_child else {"name": "Boş", "id": None, "kol": "SAG", "parent": node_id}
            ]
        }

    return build_subtree(root_id)


@router.get("/api/tree/{user_id}")
def get_tree_data(user_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Binary ağaç verisini getirir - CTE ile optimize edildi.

    N+1 Problemi Çözümü:
    - Eski: Her node için 3 SELECT sorgusu (user, sol_uye, sag_uye) - recursive
    - Yeni: 1 CTE sorgusu ile tüm ağaç tek seferde gelir

    Performans:
    - 3 seviye derinlikte eski yöntem: ~21 sorgu (7 node × 3 sorgu)
    - Yeni yöntem: 1 sorgu
    """
    if not request.state.user:
        raise HTTPException(status_code=401, detail="Giriş yapmalısınız")

    # 1. ÖNCE REDIS CACHE KONTROL EDİLİR
    cache_key = f"tree_data:{user_id}"
    cached_data = cache_get(cache_key)
    if cached_data:
        # Cache Hit - Log (İsteğe bağlı)
        print(f"⚡️ Redis Cache'den Çekildi: {user_id}")
        return cached_data

    # Kendi ağacını veya admin ise herkesi
    if request.state.user.id != user_id:
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")

    # Derinlik Limiti (Performans için)
    MAX_DEPTH = 3

    # === CTE İLE TÜM AĞACI TEK SEFERDE GETİR ===
    # Bu sorgu N+1 problemini tamamen ortadan kaldırır
    tree_nodes = crud.agac_verisi_getir_cte(db, user_id, MAX_DEPTH)

    if not tree_nodes:
        # Kullanıcı bulunamadı
        return None

    # Düz veriyi hiyerarşik ağaca dönüştür
    tree_data = _build_tree_from_flat_data(tree_nodes, user_id, MAX_DEPTH)

    # 2. REDIS'E KAYDET (5 Dakika = 300 saniye Ömrü)
    if tree_data:
        cache_set(cache_key, tree_data, expire=300)

    return tree_data

@router.get("/api/bekleyen-uyeler/{user_id}")
def get_bekleyen_uyeler(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.state.user or request.state.user.id != user_id:
        raise HTTPException(status_code=401, detail="Yetkisiz işlem")

    # Kullanıcının referans olduğu ve henüz ağaca yerleşmemiş (parent_id=None) üyeleri getir
    bekleyenler = db.query(models.Kullanici).filter(
        models.Kullanici.referans_id == user_id,
        models.Kullanici.parent_id == None
    ).all()
    
    return [
        {
            "id": u.id, 
            "uye_no": u.uye_no, 
            "tam_ad": u.tam_ad, 
            "email": u.email,
            "telefon": u.telefon,
            "rutbe": u.rutbe,
            "kayit_tarihi": u.kayit_tarihi.strftime("%d.%m.%Y %H:%M") if u.kayit_tarihi else "-"
        } 
        for u in bekleyenler
    ]

@router.post("/api/yerlestir")
def yerlestir_api(
    request: Request,
    uye_id: int = Form(...),
    parent_id: int = Form(...),
    kol: str = Form(...),
    db: Session = Depends(get_db)
):
    if not request.state.user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Giriş yapmalısınız"})

    # Güvenlik: Sadece sponsoru olduğu üyeyi yerleştirebilir
    uye = db.query(models.Kullanici).filter(models.Kullanici.id == uye_id).first()
    if not uye:
        return JSONResponse(status_code=404, content={"success": False, "message": "Üye bulunamadı"})
    
    if uye.referans_id != request.state.user.id:
        return JSONResponse(status_code=403, content={"success": False, "message": "Bu üyeyi yerleştirme yetkiniz yok!"})

    try:
        crud.uyeyi_agaca_yerlestir(db, uye_id, parent_id, kol)
        
        # 3. CACHE INVALIDATION (Önbellek Temizliği)
        # Ağaç yapısı değiştiği için bu kullanıcının ve üst sponsorların cache'i silinmeli
        # Basit yaklaşım: O anki kullanıcının cache'ini sil.
        # Daha iyi yaklaşım: Tüm ağaç cache'lerini sil (Wildcard ile) çünkü binary ağacı herkesi etkiler.
        cache_delete_pattern("tree_data:*")
        
        return {"success": True, "message": "Üye başarıyla yerleştirildi."}
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"success": False, "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

@router.get("/panel/agac/{user_id}", response_class=HTMLResponse)
def tree_page(request: Request, user_id: int, db: Session = Depends(get_db)):
    # GÜVENLİK KONTROLÜ
    current_user = request.state.user
    if not current_user:
        return RedirectResponse(url="/giris", status_code=303)
    
    # Başkasının ağacını görüntülemeyi engelle (Şimdilik sadece kendi ağacı)
    if current_user.id != user_id:
        return RedirectResponse(url=f"/panel/agac/{current_user.id}", status_code=303)

    # Temel template verileri
    return templates.TemplateResponse("tree.html", {
        "request": request,
        "user_id": user_id,
        "site_branding": {"site_name": "BestWork", "primary_color": "#7C3AED"},
        "t": lambda x: x,
        "page_title": "Binary Ağacı"
    })
