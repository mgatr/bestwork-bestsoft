from app.database import engine
from app import models

def update_database():
    print("Veritabanı tabloları kontrol ediliyor ve güncelleniyor...")
    # Yeni eklenen tabloları oluşturur (Mevcut tablolara dokunmaz)
    models.Base.metadata.create_all(bind=engine)
    print("Veritabanı başarıyla senkronize edildi.")

if __name__ == "__main__":
    update_database()
