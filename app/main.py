import sys
import subprocess
try:
    import asyncpg
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "asyncpg"])
    import asyncpg

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException as StarletteHTTPException
from . import models
from .database import SessionLocal, engine
from .routers import auth, mlm, shop, general, admin, admin_products, dashboard, home, content, ebulten

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Veritabanı tablolarını oluştur
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="BestWork Binary Network Marketing", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(mlm.router)
app.include_router(shop.router)
app.include_router(general.router)
app.include_router(admin.router)
app.include_router(admin_products.router)
app.include_router(dashboard.router)
app.include_router(home.router)
app.include_router(content.router)
app.include_router(ebulten.router)

def format_large_number(value):
    if value is None:
        return "0"
    try:
        num = float(value)
    except (ValueError, TypeError):
        return str(value)
        
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 100_000:
        return f"{num/1_000:.0f}K"
    else:
        if num % 1 == 0:
            return str(int(num))
        return f"{num:.2f}"

templates.env.filters["format_large_number"] = format_large_number

# --- EXCEPTION HANDLERS ---
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

from jose import JWTError
from app import utils, models, redis_client
from app.database import SessionLocal
from starlette.responses import JSONResponse

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    request.state.user = None
    request.state.cart_count = 0
    request.state.site_ayarlar = None

    if request.url.path.startswith(("/static", "/admin", "/bestsoft")):
        return await call_next(request)

    db = SessionLocal()
    try:
        # Sync query
        site_ayarlar = db.query(models.SiteAyarlari).first()
        request.state.site_ayarlar = site_ayarlar or models.SiteAyarlari()

        token_str_with_bearer = request.cookies.get("access_token")
        if not token_str_with_bearer or not token_str_with_bearer.startswith("Bearer "):
            print(f"[AUTH] No token found for {request.url.path}")
            return await call_next(request)

        _, _, token_str = token_str_with_bearer.partition(" ")

        try:
            payload = utils.decode_access_token(token_str)
            jti = payload.get("jti")

            # --- BLOCKLIST KONTROLÜ ---
            if not jti or redis_client.is_jti_blocklisted(jti):
                # Token geçersiz veya iptal edilmiş.
                # Çerezi sil ve misafir olarak devam et.
                print(f"[AUTH] Token blocked or no JTI for {request.url.path}")
                response = await call_next(request)
                response.delete_cookie("access_token")
                return response

            user_id = payload.get("sub")
            if not user_id:
                 print(f"[AUTH] No user_id in token for {request.url.path}")
                 return await call_next(request)

            # Sync user query
            user = db.query(models.Kullanici).filter(models.Kullanici.id == int(user_id)).first()
            if not user:
                # Kullanıcı veritabanından silinmiş.
                print(f"[AUTH] User {user_id} not found in DB for {request.url.path}")
                response = await call_next(request)
                response.delete_cookie("access_token")
                return response


            request.state.user = user
            print(f"[AUTH] User {user.id} authenticated for {request.url.path}")

            # Sync sepet query
            sepet = db.query(models.Sepet).filter(models.Sepet.kullanici_id == user.id).first()

            if sepet:
                cart_items = db.query(models.SepetUrun.adet).filter(models.SepetUrun.sepet_id == sepet.id).all()
                request.state.cart_count = sum(item.adet for item in cart_items)

        except Exception as e: # JWTError or other decode errors
            # Invalid token, just proceed without user
            print(f"[AUTH] Token decode error for {request.url.path}: {e}")
            pass

        return await call_next(request)

    except Exception as e:
        # General middleware error
        print(f"Middleware Error: {e}")
        return await call_next(request)
    finally:
        db.close()


# --- ADMIN GÜVENLİK DUVARI (Artık Ayrı Bir Dependency Olmalı) ---
# Örnek: Admin router'larında bu dependency kullanılabilir.
# from fastapi import Depends, HTTPException, status
#
# def get_admin_user(request: Request):
#     if not getattr(request.state, 'admin_user', None):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Admin yetkisi gereklidir",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return request.state.admin_user
#
# Bu yapı, router'a şöyle eklenir:
# @router.get("/dashboard", dependencies=[Depends(get_admin_user)])
# async def admin_dashboard(...):
#     ...


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.svg")

@app.get("/apple-touch-icon.png", include_in_schema=False)
async def apple_touch_icon():
    return FileResponse("static/favicon.svg")

@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
async def apple_touch_icon_precomposed():
    return FileResponse("static/favicon.svg")

@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def chrome_devtools():
    return {}

# Router'ları dahil et
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(mlm.router)
app.include_router(shop.router)
app.include_router(general.router)
app.include_router(admin.router)
app.include_router(home.router)
