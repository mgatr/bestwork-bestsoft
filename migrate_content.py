#!/usr/bin/env python3
"""
İçerik Yönetimi Modülü tablolarını ekler
Modül 5: Bannerlar, Blog, Etkinlikler, Anketler
"""
from app.database import SessionLocal, engine
from app.models import Base
from sqlalchemy import inspect

def migrate():
    print("🔧 İçerik Yönetimi modülü tabloları oluşturuluyor...")

    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)

    # Tablo kontrolü
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = ['banners', 'blog_yazilari', 'etkinlikler', 'anketler', 'anket_secenekleri', 'anket_oylari']
    created_tables = [t for t in expected_tables if t in tables]

    if len(created_tables) == len(expected_tables):
        print(f"✅ {len(created_tables)} tablo başarıyla oluşturuldu:")
        for table in created_tables:
            print(f"   - {table}")
    else:
        print(f"⚠️  {len(created_tables)}/{len(expected_tables)} tablo oluşturuldu")

    print("\n📊 İçerik Yönetimi Modülü hazır!")
    print("   - Bannerlar (Reklam görselleri)")
    print("   - Blog Yazıları (Haber ve makaleler)")
    print("   - Etkinlikler (Toplantı ve organizasyonlar)")
    print("   - Anketler (Kullanıcı geri bildirimleri)")

if __name__ == "__main__":
    migrate()
