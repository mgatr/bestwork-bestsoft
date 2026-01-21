import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Varsayılan olarak localhost
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Ping testi
    redis_client.ping()
    print("Redis bağlantısı başarılı.")
    REDIS_AVAILABLE = True
except Exception as e:
    print(f"Redis bağlantı hatası: {e}")
    print("Sistem Redis olmadan veritabanı modunda çalışacak.")
    REDIS_AVAILABLE = False
    redis_client = None

def cache_get(key: str):
    if not REDIS_AVAILABLE or not redis_client:
        return None
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except:
        return None
    return None

def cache_set(key: str, value: dict, expire: int = 300):
    if not REDIS_AVAILABLE or not redis_client:
        return
    try:
        redis_client.setex(key, expire, json.dumps(value))
    except:
        pass

def cache_delete_pattern(pattern: str):
    """
    Belirli bir pattern'e uyan (örn: 'tree:*') tüm keyleri siler.
    """
    if not REDIS_AVAILABLE or not redis_client:
        return
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except:
        pass

def is_jti_blocklisted(jti: str) -> bool:
    """
    JTI'nin blocklist'te olup olmadığını kontrol eder.
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False
    try:
        return redis_client.exists(f"blocklist:{jti}") > 0
    except:
        return False

def add_jti_to_blocklist(jti: str, expire: int = 86400):
    """
    JTI'yi blocklist'e ekler (varsayılan 24 saat).
    """
    if not REDIS_AVAILABLE or not redis_client:
        return
    try:
        redis_client.setex(f"blocklist:{jti}", expire, "1")
    except:
        pass
