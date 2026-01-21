#!/usr/bin/env python3
"""
Rütbe tablosunu ekler ve varsayılan rütbeleri yükler
"""
from app.database import SessionLocal, engine
from app.models import Base, Rutbe
from sqlalchemy import inspect

# Varsayılan rütbeler (utils.py'deki RUTBE_GEREKSINIMLERI'nden)
VARSAYILAN_RUTBELER = [
    {"ad": "Distribütör", "sol_pv": 0, "sag_pv": 0, "sira": 1, "renk": "gray"},
    {"ad": "Gümüş Distribütör", "sol_pv": 500, "sag_pv": 500, "sira": 2, "renk": "gray"},
    {"ad": "Altın Distribütör", "sol_pv": 2000, "sag_pv": 2000, "sira": 3, "renk": "blue"},
    {"ad": "Platin Distribütör", "sol_pv": 5000, "sag_pv": 5000, "sira": 4, "renk": "blue"},
    {"ad": "Elmas Distribütör", "sol_pv": 10000, "sag_pv": 10000, "sira": 5, "renk": "green"},
    {"ad": "Kraliyet Elmas", "sol_pv": 25000, "sag_pv": 25000, "sira": 6, "renk": "green"},
    {"ad": "Başkan Elmas", "sol_pv": 50000, "sag_pv": 50000, "sira": 7, "renk": "yellow"},
    {"ad": "Kraliyet Başkan", "sol_pv": 100000, "sag_pv": 100000, "sira": 8, "renk": "orange"},
    {"ad": "İmparatorluk Başkan", "sol_pv": 250000, "sag_pv": 250000, "sira": 9, "renk": "purple"},
]

def migrate():
    print("🔧 Rütbe tablosu oluşturuluyor...")

    # Tabloyu oluştur
    Base.metadata.create_all(bind=engine)

    # Tablo var mı kontrol et
    inspector = inspect(engine)
    if 'rutbeler' not in inspector.get_table_names():
        print("❌ Tablo oluşturulamadı!")
        return

    print("✅ Tablo başarıyla oluşturuldu")

    # Varsayılan verileri yükle
    db = SessionLocal()
    try:
        # Mevcut kayıt var mı kontrol et
        mevcut = db.query(Rutbe).count()
        if mevcut > 0:
            print(f"⚠️  Tabloda zaten {mevcut} kayıt var. Varsayılan veriler yüklenmedi.")
            return

        print(f"📝 {len(VARSAYILAN_RUTBELER)} varsayılan rütbe ekleniyor...")
        for rutbe_data in VARSAYILAN_RUTBELER:
            rutbe = Rutbe(**rutbe_data)
            db.add(rutbe)

        db.commit()
        print("✅ Varsayılan rütbeler başarıyla eklendi!")

        # Kontrol
        toplam = db.query(Rutbe).count()
        print(f"📊 Toplam rütbe sayısı: {toplam}")

    except Exception as e:
        print(f"❌ Hata: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
