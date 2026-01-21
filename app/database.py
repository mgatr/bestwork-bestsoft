import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Engine, veritabanı ile olan fiziksel bağlantıdır
engine = create_engine(DATABASE_URL)

# SessionLocal, her bir isteğe özel veritabanı oturumudur
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base, modellerimizin miras alacağı ana sınıftır
Base = declarative_base()

# Bağlantı testi fonksiyonu
def baglantiyi_test_et():
    try:
        with engine.connect() as connection:
            print("PostgreSQL Bağlantısı Başarılı! ✅")
    except Exception as e:
        print(f"Hata: Bağlantı kurulamadı! ❌ \nDetay: {e}")