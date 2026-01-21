#!/usr/bin/env python3
"""
E-Bülten Modülü tablolarını ekler
Modül 6: Email listesi, şablonlar, kampanyalar
"""
from app.database import SessionLocal, engine
from app.models import Base, EBultenSablon
from sqlalchemy import inspect

def migrate():
    print("🔧 E-Bülten modülü tabloları oluşturuluyor...")

    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)

    # Tablo kontrolü
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = ['ebulten_aboneler', 'ebulten_sablonlar', 'ebulten_kampanyalar', 'ebulten_gonderimler']
    created_tables = [t for t in expected_tables if t in tables]

    if len(created_tables) == len(expected_tables):
        print(f"✅ {len(created_tables)} tablo başarıyla oluşturuldu:")
        for table in created_tables:
            print(f"   - {table}")
    else:
        print(f"⚠️  {len(created_tables)}/{len(expected_tables)} tablo oluşturuldu")

    # Örnek şablon ekle
    db = SessionLocal()
    try:
        mevcut = db.query(EBultenSablon).count()
        if mevcut == 0:
            print("\n📝 Örnek e-bülten şablonu ekleniyor...")
            sablon = EBultenSablon(
                ad="Hoşgeldin Şablonu",
                konu="BestWork'e Hoş Geldiniz!",
                html_icerik="""
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                        <h1 style="color: #6750A4;">Merhaba {{ad_soyad}}!</h1>
                        <p>BestWork e-bülten listemize abone olduğunuz için teşekkür ederiz.</p>
                        <p>Size özel fırsatlar ve haberlerden ilk siz haberdar olacaksınız.</p>
                        <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                        <p style="font-size: 12px; color: #666;">
                            E-bültenden çıkmak için <a href="{{unsubscribe_link}}">tıklayın</a>
                        </p>
                    </div>
                </body>
                </html>
                """,
                aciklama="Yeni abonelere gönderilen hoşgeldin mesajı"
            )
            db.add(sablon)
            db.commit()
            print("   ✅ Örnek şablon eklendi")
    except Exception as e:
        print(f"   ⚠️  Şablon eklenemedi: {e}")
        db.rollback()
    finally:
        db.close()

    print("\n📧 E-Bülten Modülü hazır!")
    print("   - Abone yönetimi")
    print("   - Email şablonları")
    print("   - Kampanya oluşturma")
    print("   - Toplu gönderim sistemi")

if __name__ == "__main__":
    migrate()
