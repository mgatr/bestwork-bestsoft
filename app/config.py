from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Uygulama konfigürasyonunu .env dosyasından veya ortam değişkenlerinden yönetir.
    pydantic-settings kütüphanesini kullanır.
    """
    # JWT Ayarları
    SECRET_KEY: str  # Varsayılan değer yok, bulunamazsa uygulama başlamaz.
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 saat

    # İş Mantığı Ayarları (Varsayılan değerler)
    KAYIT_PV: int = 100
    KAYIT_CV: float = 50.0
    REFERANS_BONUS_ORANI: float = 0.40  # %40
    ESLESME_BONUS_MIKTARI: float = 10.0
    KARIYER_BRONZ_PUAN: int = 500

    class Config:
        # .env dosyasını okumak için
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

@lru_cache()
def get_settings():
    """
    Ayarları sadece bir kez yükler ve cache'ler.
    Uygulama genelinde bu fonksiyon aracılığıyla ayarlara erişilir.
    """
    try:
        return Settings()
    except Exception as e:
        # Genellikle pydantic.error_wrappers.ValidationError fırlatır
        print(f"KRİTİK HATA: Konfigürasyon yüklenemedi. .env dosyasını ve gerekli alanları (örn: SECRET_KEY) kontrol edin.")
        raise RuntimeError(f"Konfigürasyon yüklenemedi: {e}")

# Projenin diğer kısımlarında bu `settings` nesnesi import edilecek.
settings = get_settings()