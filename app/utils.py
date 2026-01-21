import bcrypt
from PIL import Image
import io
from pathlib import Path
from fastapi import UploadFile
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional
import uuid
from .config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verilen düz metin şifreyi, veritabanından gelen hashlenmiş şifre ile güvenli bir şekilde karşılaştırır.
    Sadece bcrypt kullanır.
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False

def get_password_hash(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(), # Issued At Time
        "jti": str(uuid.uuid4()) # JWT ID - Blocklist için benzersiz kimlik
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Token'ı çözer ve payload'ı döndürür. Hata durumunda JWTError fırlatır.
    """
    # try/except bloğu kaldırıldı. Hata yönetimi artık çağıran katmanın sorumluluğunda.
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload

# Rütbe Gereksinimleri
RUTBE_GEREKSINIMLERI = [
    # ... (içerik aynı)
]

def process_image_to_webp(file_content: bytes, destination_dir: Path, filename_prefix: str) -> str:
    """
    Yüklenen herhangi bir resmi WebP formatına çevirir ve kaydeder.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(io.BytesIO(file_content))
    new_filename = f"{filename_prefix}.webp"
    file_path = destination_dir / new_filename
    image.save(file_path, "WEBP", quality=80, method=6)
    return new_filename

