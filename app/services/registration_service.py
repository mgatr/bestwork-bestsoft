"""
Registration Service - Kullanıcı kayıt işlemlerini yönetir.

Bu servis, yeni üye kaydı sürecinin tüm iş mantığını içerir:
- Validasyonlar (email, telefon, TC no benzersizliği)
- Üye numarası oluşturma
- Sponsor doğrulama
- Referans bonusu ödeme
- Hoş geldin bonusu
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

from app import models, schemas, crud
from app.services.commission_service import CommissionService

logger = logging.getLogger(__name__)


class RegistrationService:
    """Kullanıcı kayıt servisi"""

    # Varsayılan ayarlar
    DEFAULT_REFERRAL_BONUS = 50.0  # Referans bonusu (CV)
    DEFAULT_WELCOME_BONUS = 0.0    # Hoş geldin bonusu (CV)

    @staticmethod
    def register_user(db: Session, kullanici_verisi: schemas.KullaniciKayit) -> models.Kullanici:
        """
        Yeni kullanıcı kaydı oluşturur.

        Bu işlem atomic'tir ve şu adımları içerir:
        1. Validasyonlar (email, telefon, TC no benzersizliği)
        2. Sponsor doğrulama
        3. Üye numarası oluşturma
        4. Kullanıcı kaydı
        5. Referans bonusu ödeme
        6. Hoş geldin bonusu (varsa)
        7. Cüzdan hareketleri

        Args:
            db: Database session
            kullanici_verisi: Kullanıcı kayıt verisi

        Returns:
            Oluşturulan kullanıcı nesnesi

        Raises:
            HTTPException: Validasyon hatası veya kayıt başarısız ise
        """
        try:
            # 1. VALIDASYONLAR

            # Email benzersizliği
            if crud.get_user_by_email(db, kullanici_verisi.email):
                raise HTTPException(
                    status_code=400,
                    detail="Bu email adresi zaten kullanılıyor!"
                )

            # Telefon benzersizliği
            if kullanici_verisi.telefon and crud.get_user_by_phone(db, kullanici_verisi.telefon):
                raise HTTPException(
                    status_code=400,
                    detail="Bu telefon numarası zaten kullanılıyor!"
                )

            # TC No benzersizliği (varsa)
            if kullanici_verisi.tc_no and crud.get_user_by_tc_no(db, kullanici_verisi.tc_no):
                raise HTTPException(
                    status_code=400,
                    detail="Bu TC Kimlik No zaten kayıtlı!"
                )

            # 2. SPONSOR DOĞRULAMA
            sponsor = crud.get_user(db, kullanici_verisi.referans_id)
            if not sponsor:
                raise HTTPException(
                    status_code=404,
                    detail="Sponsor kullanıcı bulunamadı!"
                )

            # 3. ÜYE NUMARASI OLUŞTUR
            # Eğer kullanıcı verisi içinde üye no yoksa oluştur
            if not kullanici_verisi.uye_no:
                kullanici_verisi.uye_no = crud.generate_unique_member_number(db)

            # 4. KULLANICI KAYDI OLUŞTUR
            yeni_uye = crud.create_user(db, kullanici_verisi)

            # 5. REFERANS BONUSU ÖDE
            # Ayarlardan referans bonusu miktarını al
            referans_bonusu = RegistrationService._get_setting(
                db, "referans_bonusu", RegistrationService.DEFAULT_REFERRAL_BONUS
            )

            if referans_bonusu > 0:
                CommissionService.pay_referral_bonus(
                    db,
                    sponsor.id,
                    referans_bonusu,
                    yeni_uye.tam_ad
                )

            # 6. HOŞ GELDİN BONUSU (Yeni üyeye)
            hosgeldin_bonusu = RegistrationService._get_setting(
                db, "hosgeldin_bonusu", RegistrationService.DEFAULT_WELCOME_BONUS
            )

            if hosgeldin_bonusu > 0:
                yeni_uye.toplam_cv = (yeni_uye.toplam_cv or Decimal("0")) + Decimal(str(hosgeldin_bonusu))
                db.commit()

                # Cüzdan hareketi logla
                crud.create_wallet_transaction(
                    db,
                    models.CuzdanHareket(
                        user_id=yeni_uye.id,
                        miktar=hosgeldin_bonusu,
                        islem_tipi="HOŞGELDİN",
                        aciklama="Hoş geldin bonusu"
                    )
                )

            db.refresh(yeni_uye)

            logger.info(
                f"Yeni kullanıcı kaydedildi. "
                f"ID: {yeni_uye.id}, "
                f"Üye No: {yeni_uye.uye_no}, "
                f"Email: {yeni_uye.email}, "
                f"Sponsor ID: {sponsor.id}"
            )

            return yeni_uye

        except HTTPException:
            # HTTPException'ları olduğu gibi fırlat
            raise

        except Exception as e:
            db.rollback()
            logger.error(f"Kullanıcı kayıt hatası: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Kayıt işlemi başarısız: {str(e)}"
            )

    @staticmethod
    def validate_sponsor(db: Session, sponsor_identifier: str) -> models.Kullanici:
        """
        Sponsor kullanıcısını doğrular.

        Args:
            db: Database session
            sponsor_identifier: Üye No veya ID

        Returns:
            Sponsor kullanıcı nesnesi

        Raises:
            HTTPException: Sponsor bulunamazsa
        """
        # Önce üye numarasına göre ara
        sponsor = crud.get_user_by_uye_no(db, sponsor_identifier)

        # Bulunamazsa ve sayısal ise ID'ye göre ara
        if not sponsor and sponsor_identifier.isdigit():
            sponsor = crud.get_user(db, int(sponsor_identifier))

        if not sponsor:
            raise HTTPException(
                status_code=404,
                detail="Sponsor kullanıcı bulunamadı!"
            )

        return sponsor

    @staticmethod
    def check_email_availability(db: Session, email: str) -> bool:
        """
        Email adresinin kullanılabilir olup olmadığını kontrol eder.

        Args:
            db: Database session
            email: Kontrol edilecek email

        Returns:
            True ise kullanılabilir, False ise kullanılıyor
        """
        existing = crud.get_user_by_email(db, email)
        return existing is None

    @staticmethod
    def check_phone_availability(db: Session, phone: str) -> bool:
        """
        Telefon numarasının kullanılabilir olup olmadığını kontrol eder.

        Args:
            db: Database session
            phone: Kontrol edilecek telefon

        Returns:
            True ise kullanılabilir, False ise kullanılıyor
        """
        existing = crud.get_user_by_phone(db, phone)
        return existing is None

    @staticmethod
    def check_tc_availability(db: Session, tc_no: str) -> bool:
        """
        TC Kimlik No'nun kullanılabilir olup olmadığını kontrol eder.

        Args:
            db: Database session
            tc_no: Kontrol edilecek TC No

        Returns:
            True ise kullanılabilir, False ise kullanılıyor
        """
        if not tc_no:
            return True  # TC No zorunlu değilse

        existing = crud.get_user_by_tc_no(db, tc_no)
        return existing is None

    @staticmethod
    def _get_setting(db: Session, anahtar: str, varsayilan: float) -> float:
        """
        Ayarları getirir, yoksa oluşturur.

        Args:
            db: Database session
            anahtar: Ayar anahtarı
            varsayilan: Varsayılan değer

        Returns:
            Ayar değeri
        """
        db_ayar = crud.get_setting(db, anahtar)
        if not db_ayar:
            crud.create_or_update_setting(db, anahtar, varsayilan)
            return varsayilan
        return db_ayar.deger
