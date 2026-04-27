# entities/__init__.py
"""Game entities for Cage Dynasty"""

from .fighter import (
    Fighter, create_fighter,
    FightHistoryEntry, InjuryRecord
)
from .camp import (
    Camp, create_camp,
    Coach, CoachSpecialty
)
from .promotion import (
    Promotion, create_promotion, create_dfc,
    Division, ScheduledEvent
)
from .contract import (
    CampContract, PromotionalContract,
    create_camp_contract, create_promotional_contract,
    ContractTerms, ContractType, ContractManager
)
