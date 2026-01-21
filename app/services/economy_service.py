"""
Economy Service - MLM puan dağıtım işlemlerini yönetir.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
from typing import Optional

from app import models
from app.services.commission_service import CommissionService
from app.services.rank_service import RankService
from app.crud import create_wallet_transaction

logger = logging.getLogger(__name__)


class EconomyService:
    """MLM ekonomisi tetikleme ve puan dağıtım servisi"""
    
    @staticmethod
    def run_payout_workflow(db: Session, baslangic_id: int, satis_pv: int, satis_cv: float) -> None:
        """
        Bir satıştan gelen PV puanını, ağaç yapısında yukarı doğru 7 seviyeye kadar dağıtır.
        Bu işlem artık tamamen atomiktir. Ya herkes puanını alır ya da bir hata durumunda
        hiç kimse almaz ve tüm değişiklikler geri alınır.
        """
        try:
            current_id = baslangic_id
            limit = 500  # Sonsuz döngü koruması

            while current_id and limit > 0:
                limit -= 1

                mevcut_uye = db.query(models.Kullanici).filter(models.Kullanici.id == current_id).first()
                if not mevcut_uye or not mevcut_uye.parent_id:
                    break  # Zincir bitti

                ust_uye_id = mevcut_uye.parent_id
                kol_pozisyonu = mevcut_uye.kol

                # Üst üyeyi satır seviyesinde kilitleyerek getir (Race Condition Önlemi)
                try:
                    # PostgreSQL gibi bunu destekleyen DB'ler için ideal
                    ust_uye = db.query(models.Kullanici).filter(
                        models.Kullanici.id == ust_uye_id
                    ).with_for_update().first()
                except Exception:
                    # SQLite gibi desteklemeyen platformlar için fallback
                    ust_uye = db.query(models.Kullanici).filter(
                        models.Kullanici.id == ust_uye_id
                    ).first()

                if not ust_uye:
                    break

                # Puanları bellekte güncelle (henüz commit yok)
                if kol_pozisyonu == 'SOL':
                    ust_uye.sol_pv = (ust_uye.sol_pv or 0) + satis_pv
                    ust_uye.toplam_sol_pv = (ust_uye.toplam_sol_pv or 0) + satis_pv
                else:  # SAĞ
                    ust_uye.sag_pv = (ust_uye.sag_pv or 0) + satis_pv
                    ust_uye.toplam_sag_pv = (ust_uye.toplam_sag_pv or 0) + satis_pv

                # Rütbe kontrolünü yap
                RankService.check_and_update(db, ust_uye)

                # Eşleşme kontrolünü tetikle
                CommissionService.check_matching(db, ust_uye.id)

                # Bir sonraki seviyeye geç
                current_id = ust_uye.id

            # Döngü başarıyla bittiyse, tüm değişiklikleri tek seferde veritabanına işle
            db.commit()
            logger.info(f"Puan dağıtımı başarıyla tamamlandı. Başlangıç ID: {baslangic_id}, PV: {satis_pv}")

        except Exception as e:
            # Herhangi bir hata oluşursa, bu transaction içindeki tüm değişiklikleri geri al
            db.rollback()
            logger.error(f"Ekonomi tetiklenirken hata oluştu: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Puan dağıtımı sırasında kritik bir hata oluştu: {e}"
            )