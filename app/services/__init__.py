"""
Services Package - İş mantığı katmanı.

Bu paket, uygulamanın tüm iş mantığını (business logic) içerir.
Her servis, belirli bir domain sorumluluğunu yönetir:

- EconomyService: Puan dağıtımı ve genel ekonomi akışı
- CommissionService: Komisyon ve nesil geliri hesaplamaları
- RankService: Rütbe ve kariyer güncellemeleri
- BinaryTreeService: Binary ağaç yerleşimi ve hiyerarşi yönetimi
- OrderService: Sipariş oluşturma ve işleme
- RegistrationService: Kullanıcı kayıt işlemleri

Tüm servisler static metodlar kullanır ve state-less'tir (durum tutmazlar).
Bu yaklaşım test edilebilirliği ve bakımı kolaylaştırır.
"""

from .economy_service import EconomyService
from .commission_service import CommissionService
from .rank_service import RankService
from .binary_service import BinaryTreeService
from .order_service import OrderService
from .registration_service import RegistrationService

__all__ = [
    "EconomyService",
    "CommissionService",
    "RankService",
    "BinaryTreeService",
    "OrderService",
    "RegistrationService"
]