"""
Order Service - Sipariş oluşturma ve işleme mantığı.

Bu servis, e-ticaret siparişlerinin oluşturulması ve işlenmesinden sorumludur.
Sepet doğrulaması, sipariş oluşturma, stok kontrolü ve ekonomi tetikleme gibi
iş mantıklarını içerir.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from app import models, crud
from app.services.economy_service import EconomyService

logger = logging.getLogger(__name__)


class OrderService:
    """Sipariş yönetim servisi"""

    @staticmethod
    def create_order(db: Session, kullanici_id: int, adres: str) -> models.Siparis:
        """
        Kullanıcının sepetinden sipariş oluşturur.

        Bu işlem atomic'tir:
        1. Sepeti kontrol eder
        2. Sipariş kaydı oluşturur
        3. Sipariş ürünlerini kaydeder
        4. Sepeti temizler
        5. Ekonomi sistemini tetikler (PV dağıtımı)

        Args:
            db: Database session
            kullanici_id: Kullanıcı ID
            adres: Teslimat adresi

        Returns:
            Oluşturulan sipariş nesnesi

        Raises:
            HTTPException: Sepet boş veya işlem başarısız ise
        """
        try:
            # 1. Sepeti getir ve kontrol et
            sepet_detay = crud.get_cart_details(db, kullanici_id)

            if not sepet_detay or not sepet_detay.get("urunler"):
                raise HTTPException(
                    status_code=400,
                    detail="Sepetiniz boş! Sipariş oluşturamazsınız."
                )

            # 2. Sipariş toplam değerlerini hesapla
            toplam_fiyat = sepet_detay["toplam_fiyat"]
            toplam_pv = 0
            toplam_cv = 0.0

            # Her ürün için PV ve CV hesapla
            for urun_detay in sepet_detay["urunler"]:
                urun = urun_detay["urun"]
                adet = urun_detay["adet"]

                # PV ve CV değerlerini topla
                urun_pv = (urun.pv or 0) * adet
                urun_cv = (urun.cv or 0.0) * adet

                toplam_pv += urun_pv
                toplam_cv += float(urun_cv)

            # 3. Sipariş kaydı oluştur
            yeni_siparis = models.Siparis(
                kullanici_id=kullanici_id,
                toplam_fiyat=toplam_fiyat,
                toplam_pv=toplam_pv,
                toplam_cv=toplam_cv,
                adres=adres,
                durum="BEKLEMEDE",
                olusturma_tarihi=datetime.now(ZoneInfo("Europe/Istanbul"))
            )

            db.add(yeni_siparis)
            db.flush()  # ID'yi almak için

            # 4. Sipariş ürünlerini kaydet
            for urun_detay in sepet_detay["urunler"]:
                urun = urun_detay["urun"]
                adet = urun_detay["adet"]
                fiyat = urun.indirimli_fiyat if urun.indirimli_fiyat else urun.fiyat

                siparis_urun = models.SiparisUrun(
                    siparis_id=yeni_siparis.id,
                    urun_id=urun.id,
                    adet=adet,
                    birim_fiyat=fiyat,
                    toplam_fiyat=fiyat * adet
                )
                db.add(siparis_urun)

            # 5. Sepeti temizle
            crud.clear_cart(db, kullanici_id)

            # 6. Veritabanına kaydet
            db.commit()
            db.refresh(yeni_siparis)

            # 7. Ekonomi sistemini tetikle (PV dağıtımı)
            # Kullanıcının kendisinden başlayarak yukarı doğru PV dağıt
            if toplam_pv > 0:
                try:
                    EconomyService.run_payout_workflow(
                        db, kullanici_id, toplam_pv, toplam_cv
                    )
                except Exception as e:
                    logger.error(f"Ekonomi tetikleme hatası (Sipariş ID: {yeni_siparis.id}): {e}")
                    # Sipariş oluşturuldu ama ekonomi tetiklenemedi
                    # Bu durum loglanır ancak sipariş iptal edilmez

            logger.info(
                f"Sipariş oluşturuldu. "
                f"Sipariş ID: {yeni_siparis.id}, "
                f"Kullanıcı ID: {kullanici_id}, "
                f"Toplam: {toplam_fiyat}, "
                f"PV: {toplam_pv}"
            )

            return yeni_siparis

        except HTTPException:
            # HTTPException'ları olduğu gibi fırlat
            raise

        except Exception as e:
            db.rollback()
            logger.error(f"Sipariş oluşturma hatası: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Sipariş oluşturulamadı: {str(e)}"
            )

    @staticmethod
    def update_order_status(
        db: Session,
        siparis_id: int,
        yeni_durum: str
    ) -> models.Siparis:
        """
        Sipariş durumunu günceller.

        Args:
            db: Database session
            siparis_id: Sipariş ID
            yeni_durum: Yeni durum (BEKLEMEDE, HAZIRLANIYOR, KARGODA, TESLIM_EDILDI, IPTAL)

        Returns:
            Güncellenmiş sipariş

        Raises:
            HTTPException: Sipariş bulunamazsa
        """
        VALID_STATUSES = ["BEKLEMEDE", "HAZIRLANIYOR", "KARGODA", "TESLIM_EDILDI", "IPTAL"]

        if yeni_durum not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Geçersiz durum. Geçerli durumlar: {', '.join(VALID_STATUSES)}"
            )

        siparis = crud.get_order(db, siparis_id)

        if not siparis:
            raise HTTPException(
                status_code=404,
                detail="Sipariş bulunamadı."
            )

        try:
            siparis.durum = yeni_durum

            # İptal durumunda iptal tarihi ekle
            if yeni_durum == "IPTAL" and not siparis.iptal_tarihi:
                siparis.iptal_tarihi = datetime.now(ZoneInfo("Europe/Istanbul"))

            db.commit()
            db.refresh(siparis)

            logger.info(f"Sipariş durumu güncellendi. Sipariş ID: {siparis_id}, Yeni Durum: {yeni_durum}")

            return siparis

        except Exception as e:
            db.rollback()
            logger.error(f"Sipariş durumu güncelleme hatası: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Sipariş durumu güncellenemedi: {str(e)}"
            )

    @staticmethod
    def get_order_details(db: Session, siparis_id: int) -> dict:
        """
        Sipariş detaylarını (ürünler dahil) getirir.

        Args:
            db: Database session
            siparis_id: Sipariş ID

        Returns:
            Sipariş detayları dictionary

        Raises:
            HTTPException: Sipariş bulunamazsa
        """
        siparis = crud.get_order(db, siparis_id)

        if not siparis:
            raise HTTPException(
                status_code=404,
                detail="Sipariş bulunamadı."
            )

        # Sipariş ürünlerini getir
        siparis_urunler = db.query(models.SiparisUrun).filter(
            models.SiparisUrun.siparis_id == siparis_id
        ).all()

        urunler = []
        for su in siparis_urunler:
            urun = crud.get_product(db, su.urun_id)
            if urun:
                urunler.append({
                    "urun": urun,
                    "adet": su.adet,
                    "birim_fiyat": su.birim_fiyat,
                    "toplam_fiyat": su.toplam_fiyat
                })

        return {
            "siparis": siparis,
            "urunler": urunler
        }
