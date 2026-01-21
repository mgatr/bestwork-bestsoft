#!/usr/bin/env python3
"""
Tüm kalan modülleri migrate eder
Modül 7-15: SMS, Banka, Katalog, Yetki, Form
"""
from app.database import SessionLocal, engine
from app.models import Base, Banka, Doviz
from sqlalchemy import inspect
from decimal import Decimal

def migrate():
    print("🔧 Tüm modül tabloları oluşturuluyor...")
    
    # Tabloları oluştur
    Base.metadata.create_all(bind=engine)
    
    # Tablo kontrolü
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    yeni_tablolar = [
        'sms_kampanyalar', 'sms_log',
        'bankalar', 'banka_hesaplari', 'dovizler',
        'kataloglar', 'katalog_sayfalar',
        'roller', 'yetkiler',
        'formlar', 'form_cevaplar'
    ]
    
    olusan = [t for t in yeni_tablolar if t in tables]
    print(f"✅ {len(olusan)}/{len(yeni_tablolar)} tablo oluşturuldu")
    
    # Varsayılan veriler
    db = SessionLocal()
    try:
        # Bankalar
        if db.query(Banka).count() == 0:
            print("\n📦 Varsayılan bankalar ekleniyor...")
            bankalar = [
                Banka(ad="Türkiye İş Bankası", kod="0064"),
                Banka(ad="Garanti BBVA", kod="0062"),
                Banka(ad="Yapı Kredi", kod="0067"),
                Banka(ad="Akbank", kod="0046"),
                Banka(ad="Ziraat Bankası", kod="0010")
            ]
            for banka in bankalar:
                db.add(banka)
            db.commit()
            print("   ✅ 5 banka eklendi")
        
        # Dövizler
        if db.query(Doviz).count() == 0:
            print("\n💱 Varsayılan dövizler ekleniyor...")
            dovizler = [
                Doviz(kod="TRY", ad="Türk Lirası", sembol="₺", alis=Decimal("1.0000"), satis=Decimal("1.0000")),
                Doviz(kod="USD", ad="Amerikan Doları", sembol="$", alis=Decimal("34.5000"), satis=Decimal("34.8000")),
                Doviz(kod="EUR", ad="Euro", sembol="€", alis=Decimal("37.5000"), satis=Decimal("37.8000"))
            ]
            for doviz in dovizler:
                db.add(doviz)
            db.commit()
            print("   ✅ 3 döviz eklendi")
            
    except Exception as e:
        print(f"⚠️  Varsayılan veri hatası: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n🎉 Tüm modüller hazır!")
    print("   Modül 7: SMS Sistemi")
    print("   Modül 8: Bankalar ve Ödeme")
    print("   Modül 9: Kataloglar")
    print("   Modül 10: Yetki Yönetimi")
    print("   Modül 14: Form Builder")

if __name__ == "__main__":
    migrate()
