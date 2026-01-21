"""
Rank Service - Kullanıcı rütbe ve kariyer güncellemelerini yönetir.
"""
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app import models
from app.utils import RUTBE_GEREKSINIMLERI

logger = logging.getLogger(__name__)


class RankService:
    """Rütbe ve kariyer yönetim servisi"""
    
    @staticmethod
    def check_and_update(db: Session, kullanici: models.Kullanici) -> None:
        """
        Kullanıcının toplam cirosuna (toplam_sol_pv, toplam_sag_pv) bakarak 
        hak ettiği en yüksek rütbeyi atar.
        """
        if not kullanici:
            return

        current_sol = kullanici.toplam_sol_pv or 0
        current_sag = kullanici.toplam_sag_pv or 0

        yeni_rutbe = "Distribütör"  # Default

        # RUTBE_GEREKSINIMLERI küçükten büyüğe sıralı olduğu için
        # her sağlayan rütbeyi atayabiliriz, döngü sonunda en yüksek olanda kalır.
        for r in RUTBE_GEREKSINIMLERI:
            gerekli_sol = r["sol_pv"]
            gerekli_sag = r["sag_pv"]
            rutbe_adi = r["ad"]

            if current_sol >= gerekli_sol and current_sag >= gerekli_sag:
                yeni_rutbe = rutbe_adi

        # Eğer rütbe değiştiyse güncelle
        if kullanici.rutbe != yeni_rutbe:
            kullanici.rutbe = yeni_rutbe
            logger.info(f"Rütbe güncellendi. Kullanıcı ID: {kullanici.id}, Yeni Rütbe: {yeni_rutbe}")

    @staticmethod
    def update_career(db: Session, kullanici_id: int) -> None:
        """
        Kariyer güncelleme - Kısa kol ciro (PV) baremlerine göre rütbe atar.
        """
        kullanici = db.query(models.Kullanici).filter(models.Kullanici.id == kullanici_id).first()
        if not kullanici:
            return

        # Senin belirlediğin kısa kol ciro (PV) baremleri
        ciro = min(kullanici.sol_pv, kullanici.sag_pv)

        eski_rutbe = kullanici.rutbe
        yeni_rutbe = "Distributor"

        # Kariyer Basamakları (Tam Liste)
        if ciro >= 25000000:
            yeni_rutbe = "Triple President"
        elif ciro >= 10000000:
            yeni_rutbe = "Double President"
        elif ciro >= 5000000:
            yeni_rutbe = "President"
        elif ciro >= 2500000:
            yeni_rutbe = "Triple Diamond"
        elif ciro >= 1000000:
            yeni_rutbe = "Double Diamond"
        elif ciro >= 500000:
            yeni_rutbe = "Diamond"
        elif ciro >= 250000:
            yeni_rutbe = "Emerald"
        elif ciro >= 100000:
            yeni_rutbe = "Ruby"
        elif ciro >= 50000:
            yeni_rutbe = "Sapphire"
        elif ciro >= 15000:
            yeni_rutbe = "Pearl"
        elif ciro >= 5000:
            yeni_rutbe = "Platinum"
        else:
            yeni_rutbe = "Distribütör"

        if eski_rutbe != yeni_rutbe:
            kullanici.rutbe = yeni_rutbe
            db.commit()
            
            # Cüzdan hareketi logla (miktar 0)
            from app.services.economy_service import EconomyService
            EconomyService.log_wallet_transaction(
                db, kullanici.id, 0, "RANK_UP",
                f"Yeni Kariyer: {yeni_rutbe}"
            )
            logger.info(f"Kariyer güncellendi. Kullanıcı ID: {kullanici.id}, Yeni Rütbe: {yeni_rutbe}")

    @staticmethod
    def find_lowest_empty_spot(db: Session, parent_id: int, tercih_kol: str) -> int:
        """
        Kullanıcı sadece seçtiği kolun (SOL veya SAĞ) en dış hattına kayıt yapabilir.
        İç kollara (inner leg) kayıt yapılmasına izin vermez.
        Recursive yapıdan While döngüsüne dönüştürülerek Stack Overflow riski sıfırlandı.
        """
        current_parent_id = parent_id

        while True:
            # Mevcut parent'ın altında, seçilen kolda (SOL veya SAĞ) biri var mı?
            mevcut_uye = db.query(models.Kullanici).filter(
                models.Kullanici.parent_id == current_parent_id,
                models.Kullanici.kol == tercih_kol
            ).first()

            if not mevcut_uye:
                # Eğer o kol boşsa, burası kayıt için doğru yerdir.
                return current_parent_id

            # EĞER DOLUYSA:
            # Bir alt basamağa geç ve döngüye devam et
            current_parent_id = mevcut_uye.id