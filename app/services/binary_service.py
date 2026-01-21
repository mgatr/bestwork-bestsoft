"""
Binary Tree Service - Binary ağaç yerleşimi ve hiyerarşi yönetimi.

Bu servis, MLM sistemindeki binary (ikili) ağaç yapısının yönetiminden sorumludur.
Üyelerin ağaca yerleştirilmesi, ağaç verisinin çekilmesi gibi işlemleri yönetir.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
import logging
from typing import List, Dict, Optional

from app import models

logger = logging.getLogger(__name__)


class BinaryTreeService:
    """Binary ağaç yönetim servisi"""

    @staticmethod
    def get_tree_data_cte(db: Session, root_user_id: int, max_depth: int = 3) -> List[Dict]:
        """
        CTE (Common Table Expression) kullanarak binary ağacın tüm verilerini
        tek sorguda getirir. N+1 sorgu problemini önler.

        Args:
            db: Database session
            root_user_id: Kök kullanıcı ID'si
            max_depth: Maksimum derinlik

        Returns:
            Ağaç düğümleri listesi (düz liste halinde)
        """
        # Recursive CTE sorgusu - Tek sorguda tüm ağacı getirir
        cte_query = text("""
            WITH RECURSIVE binary_tree (id, tam_ad, uye_no, parent_id, kol, sol_pv, sag_pv, depth) AS (
                -- Anchor: Kök kullanıcı
                SELECT
                    id,
                    tam_ad,
                    uye_no,
                    parent_id,
                    kol,
                    sol_pv,
                    sag_pv,
                    0 as depth
                FROM kullanicilar
                WHERE id = :root_user_id

                UNION ALL

                -- Recursive: Alt üyeleri bul
                SELECT
                    k.id,
                    k.tam_ad,
                    k.uye_no,
                    k.parent_id,
                    k.kol,
                    k.sol_pv,
                    k.sag_pv,
                    bt.depth + 1
                FROM kullanicilar k
                INNER JOIN binary_tree bt ON k.parent_id = bt.id
                WHERE bt.depth < :max_depth
            )
            SELECT * FROM binary_tree;
        """)

        try:
            result = db.execute(cte_query, {
                "root_user_id": root_user_id,
                "max_depth": max_depth
            }).fetchall()

            # Sonuçları dict listesine dönüştür
            tree_nodes = []
            for row in result:
                tree_nodes.append({
                    "id": row.id,
                    "tam_ad": row.tam_ad,
                    "uye_no": row.uye_no,
                    "parent_id": row.parent_id,
                    "kol": row.kol,
                    "sol_pv": row.sol_pv or 0,
                    "sag_pv": row.sag_pv or 0,
                    "depth": row.depth
                })

            return tree_nodes

        except Exception as e:
            logger.error(f"Ağaç verisi çekilirken hata: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Ağaç verisi alınamadı: {str(e)}"
            )

    @staticmethod
    def place_user_in_tree(
        db: Session,
        user_id: int,
        parent_id: int,
        kol: str
    ) -> None:
        """
        Kullanıcıyı binary ağaca yerleştirir.

        Bu işlem atomic'tir - ya tamamen başarılı olur ya da hiç olmaz.

        Args:
            db: Database session
            user_id: Yerleştirilecek kullanıcı ID
            parent_id: Üst kullanıcı (parent) ID
            kol: Hangi kola yerleşecek ("SOL" veya "SAG")

        Raises:
            HTTPException: Yerleştirme başarısız olursa
        """
        # Validasyonlar
        if kol not in ["SOL", "SAG"]:
            raise HTTPException(
                status_code=400,
                detail="Kol sadece 'SOL' veya 'SAG' olabilir."
            )

        # Kullanıcıyı getir
        user = db.query(models.Kullanici).filter(
            models.Kullanici.id == user_id
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Kullanıcı bulunamadı."
            )

        # Zaten yerleştirilmiş mi?
        if user.parent_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Bu kullanıcı zaten ağaca yerleştirilmiş."
            )

        # Parent kullanıcısını kontrol et
        parent = db.query(models.Kullanici).filter(
            models.Kullanici.id == parent_id
        ).first()

        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Üst kullanıcı (parent) bulunamadı."
            )

        # Seçilen kol dolu mu?
        existing_in_leg = db.query(models.Kullanici).filter(
            models.Kullanici.parent_id == parent_id,
            models.Kullanici.kol == kol
        ).first()

        if existing_in_leg:
            raise HTTPException(
                status_code=400,
                detail=f"{parent.tam_ad} kullanıcısının {kol} kolu zaten dolu!"
            )

        try:
            # Kullanıcıyı yerleştir
            user.parent_id = parent_id
            user.kol = kol

            db.commit()
            db.refresh(user)

            logger.info(
                f"Kullanıcı ağaca yerleştirildi. "
                f"User ID: {user_id}, Parent ID: {parent_id}, Kol: {kol}"
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Ağaca yerleştirme sırasında hata: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Yerleştirme işlemi başarısız: {str(e)}"
            )

    @staticmethod
    def find_empty_spot(
        db: Session,
        parent_id: int,
        preferred_leg: str
    ) -> int:
        """
        Belirli bir kolda boş yer bulur. Eğer kol doluysa, o koldaki
        en dıştaki (leaf) pozisyona kadar iner.

        Bu recursive işlemi while döngüsü ile yapar (stack overflow önlemi).

        Args:
            db: Database session
            parent_id: Başlangıç parent ID
            preferred_leg: Tercih edilen kol ("SOL" veya "SAG")

        Returns:
            Boş pozisyonun parent ID'si
        """
        current_parent_id = parent_id
        iteration_limit = 1000  # Sonsuz döngü koruması

        while iteration_limit > 0:
            iteration_limit -= 1

            # Bu parent'ın seçilen kolunda biri var mı?
            child_in_leg = db.query(models.Kullanici).filter(
                models.Kullanici.parent_id == current_parent_id,
                models.Kullanici.kol == preferred_leg
            ).first()

            if not child_in_leg:
                # Kol boş - burası yerleştirme için uygun
                return current_parent_id

            # Kol dolu - bir seviye aşağı in
            current_parent_id = child_in_leg.id

        # Güvenlik önlemi - çok derin bir ağaç
        logger.warning(
            f"Boş yer bulma işlemi iterasyon limitine ulaştı. "
            f"Parent ID: {parent_id}, Kol: {preferred_leg}"
        )
        return current_parent_id

    @staticmethod
    def get_team_count(db: Session, user_id: int, kol: Optional[str] = None) -> int:
        """
        Kullanıcının altındaki toplam ekip sayısını hesaplar.

        Recursive CTE kullanarak tüm alt ağacı sayar.

        Args:
            db: Database session
            user_id: Kullanıcı ID
            kol: Belirli bir kolu saymak için (None ise tüm ağaç)

        Returns:
            Ekip üyesi sayısı
        """
        if kol:
            # Belirli bir kol için
            cte_query = text("""
                WITH RECURSIVE team_count (id) AS (
                    -- Anchor: Seçilen koldaki direkt alt üye
                    SELECT id
                    FROM kullanicilar
                    WHERE parent_id = :user_id AND kol = :kol

                    UNION ALL

                    -- Recursive: Tüm alt üyeleri bul
                    SELECT k.id
                    FROM kullanicilar k
                    INNER JOIN team_count tc ON k.parent_id = tc.id
                )
                SELECT COUNT(id) as toplam FROM team_count;
            """)

            result = db.execute(cte_query, {
                "user_id": user_id,
                "kol": kol
            }).fetchone()

        else:
            # Tüm ağaç
            cte_query = text("""
                WITH RECURSIVE team_count (id) AS (
                    -- Anchor: Direkt alt üyeler
                    SELECT id
                    FROM kullanicilar
                    WHERE parent_id = :user_id

                    UNION ALL

                    -- Recursive: Tüm alt üyeleri bul
                    SELECT k.id
                    FROM kullanicilar k
                    INNER JOIN team_count tc ON k.parent_id = tc.id
                )
                SELECT COUNT(id) as toplam FROM team_count;
            """)

            result = db.execute(cte_query, {"user_id": user_id}).fetchone()

        return result.toplam if result else 0

    @staticmethod
    def get_pending_placements(db: Session, sponsor_id: int) -> List[models.Kullanici]:
        """
        Sponsorun ağaca yerleştirmediği (parent_id=None) üyeleri getirir.

        Args:
            db: Database session
            sponsor_id: Sponsor kullanıcı ID

        Returns:
            Bekleyen kullanıcılar listesi
        """
        return db.query(models.Kullanici).filter(
            models.Kullanici.referans_id == sponsor_id,
            models.Kullanici.parent_id == None
        ).all()
