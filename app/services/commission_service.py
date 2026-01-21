"""
Commission Service - Komisyon, nesil geliri ve eşleme ödemelerini yönetir.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
from typing import Optional
from decimal import Decimal

from app import models
from app.crud import create_wallet_transaction

logger = logging.getLogger(__name__)


class CommissionService:
    """Komisyon ve ödeme dağıtım servisi"""
    
    @staticmethod
    def check_matching(db: Session, kullanici_id: int) -> None:
        """
        Kullanıcının kısa kol cirosuna göre eşleşme ödemesi yapar.
        %13 kısa kol mantığı uygulanır.
        """
        try:
            # Transaction ve Kilitleme Başlat
            try:
                kullanici = db.query(models.Kullanici).filter(
                    models.Kullanici.id == kullanici_id
                ).with_for_update().first()
            except:
                kullanici = db.query(models.Kullanici).filter(
                    models.Kullanici.id == kullanici_id
                ).first()

            if not kullanici:
                return

            # PV değerleri None ise 0 olarak başlat
            if kullanici.sol_pv is None:
                kullanici.sol_pv = 0
            if kullanici.sag_pv is None:
                kullanici.sag_pv = 0

            # Her iki kolda da puan birikmiş mi?
            if kullanici.sol_pv > 0 and kullanici.sag_pv > 0:
                # Kısa kolu (ödenecek puanı) belirle
                odenecek_puan = min(kullanici.sol_pv, kullanici.sag_pv)

                if odenecek_puan <= 0:
                    return

                # Ayarlardan %13 oranını çek (admin panelinden güncellenebilir)
                odeme_orani = CommissionService._get_setting(db, "kisa_kol_oran", 0.13)

                # Kazanç = Kısa Kol Cirosu * Oran
                kazanc = odenecek_puan * odeme_orani

                # Bakiyeyi güncelle ve puanları kollardan düş (Dengeleme)
                if kullanici.toplam_cv is None:
                    kullanici.toplam_cv = Decimal("0")
                kullanici.toplam_cv += Decimal(str(kazanc))
                kullanici.sol_pv -= odenecek_puan
                kullanici.sag_pv -= odenecek_puan

                db.commit()

                # Cüzdan hareketi logla
                create_wallet_transaction(
                    db,
                    models.CuzdanHareket(
                        user_id=kullanici_id,
                        miktar=kazanc,
                        islem_tipi="ESLESME",
                        aciklama=f"Kısa kol cirosu ({odenecek_puan} PV) üzerinden %{int(odeme_orani*100)} kazanç."
                    )
                )

                # Nesil Geliri (Matching) Dağıtımı
                CommissionService.distribute(db, kullanici.id, kazanc)

        except Exception as e:
            logger.error(f"Eşleme kontrolü sırasında hata: {e}")
            db.rollback()
            raise

    @staticmethod
    def distribute(db: Session, alt_uye_id: int, kazanilan_miktar: float) -> None:
        """
        Sponsor hattı boyunca yukarı çıkar ve her nesle tanımlı oranını öder.
        Recursive yerine while döngüsü kullanır.
        """
        # Max derinlik
        MAX_NESIL = 10

        current_alt_uye_id = alt_uye_id

        for nesil in range(1, MAX_NESIL + 1):
            # 1. Bu nesil için bir ayar var mı?
            ayar = db.query(models.NesilAyari).filter(
                models.NesilAyari.nesil_no == nesil
            ).first()
            if not ayar:
                break  # Ayar yoksa veya bittiyse dur.

            # 2. Alt üyenin sponsorunu (liderini) bul
            alt_uye = db.query(models.Kullanici).filter(
                models.Kullanici.id == current_alt_uye_id
            ).first()
            if not alt_uye or not alt_uye.referans_id:
                break  # Sponsor zinciri koptu.

            lider = db.query(models.Kullanici).filter(
                models.Kullanici.id == alt_uye.referans_id
            ).first()
            if not lider:
                break

            # Bonusu öde
            bonus = kazanilan_miktar * ayar.oran
            lider.toplam_cv = (lider.toplam_cv or Decimal("0")) + Decimal(str(bonus))
            db.commit()

            # Cüzdan hareketi logla
            create_wallet_transaction(
                db,
                models.CuzdanHareket(
                    user_id=lider.id,
                    miktar=bonus,
                    islem_tipi="LIDERLIK",
                    aciklama=f"{nesil}. Nesil Primi ({alt_uye.tam_ad} kazancından)"
                )
            )

            # Bir sonraki tur için yukarı çık
            current_alt_uye_id = lider.id

        logger.info(f"Nesil geliri dağıtımı tamamlandı. Alt Üye ID: {alt_uye_id}, Kazanç: {kazanilan_miktar}")

    @staticmethod
    def pay_referral_bonus(db: Session, sponsor_id: int, prim_miktari: float, yeni_uye_adi: str) -> None:
        """Referans bonusu öder."""
        sponsor = db.query(models.Kullanici).filter(models.Kullanici.id == sponsor_id).first()
        if sponsor:
            sponsor.toplam_cv += Decimal(str(prim_miktari))
            db.commit()
            
            create_wallet_transaction(
                db,
                models.CuzdanHareket(
                    user_id=sponsor_id,
                    miktar=prim_miktari,
                    islem_tipi="REFERANS",
                    aciklama=f"Yeni kayıt: {yeni_uye_adi}"
                )
            )
            logger.info(f"Referans bonusu ödendi. Sponsor ID: {sponsor_id}, Miktar: {prim_miktari}")

    @staticmethod
    def _get_setting(db: Session, anahtar: str, varsayilan: float) -> float:
        """Ayarları getirir, yoksa oluşturur."""
        db_ayar = db.query(models.Ayarlar).filter(models.Ayarlar.anahtar == anahtar).first()
        if not db_ayar:
            yeni_ayar = models.Ayarlar(anahtar=anahtar, deger=varsayilan)
            db.add(yeni_ayar)
            db.commit()
            return varsayilan
        return db_ayar.deger