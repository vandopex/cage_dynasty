# entities/contract.py
# Module 8: Contract System
# Lines: 467
#
# Contracts bind fighters to camps and promotions.
# The legal backbone of the MMA business.

"""
Cage Dynasty - Contract System

This module handles the contractual relationships between:
- Fighters and Camps (management contracts)
- Fighters and Promotions (fight contracts)

Contracts have:
- Duration (fights remaining or time-based)
- Financial terms (purse splits, bonuses)
- Status tracking (active, expired, terminated)
- Negotiation support

USAGE:
    from entities.contract import (
        CampContract, PromotionalContract,
        create_camp_contract, create_promotional_contract
    )
    
    # Sign fighter to a camp
    camp_contract = create_camp_contract(
        fighter_id="fighter_001",
        camp_id="camp_001",
        duration_fights=6,
        camp_cut_percentage=15
    )
    
    # Sign fighter to promotion
    promo_contract = create_promotional_contract(
        fighter_id="fighter_001",
        promotion_id="dfc_001",
        fights=4,
        base_purse=50000
    )

IMPORT RULES:
- This module imports from core modules only
- Other modules may import contracts
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid

from core.types import ContractStatus, EventType, WeightClass
from core.calendar import GameDate, calendar
from core.events import emit
from core.config import get_config


# ============================================================================
# CONTRACT TYPES
# ============================================================================

class ContractType(Enum):
    """Types of contracts in the game"""
    CAMP = "Camp"           # Fighter-Camp relationship
    PROMOTIONAL = "Promotional"  # Fighter-Promotion relationship


# ============================================================================
# BASE CONTRACT
# ============================================================================

@dataclass
class ContractTerms:
    """Financial terms of a contract"""
    base_purse: int = 10000          # Base fight purse
    win_bonus: int = 5000            # Bonus for winning
    finish_bonus: int = 2500         # Bonus for finish (KO/Sub)
    ppv_points: bool = False         # Gets PPV revenue share
    ppv_percentage: float = 0.0      # PPV revenue percentage
    signing_bonus: int = 0           # One-time signing bonus
    camp_cut_percentage: float = 15.0  # Camp's cut of purse (for camp contracts)


class BaseContract:
    """
    Base class for all contracts.
    
    Provides common functionality for tracking contract status,
    duration, and financial terms.
    """
    
    def __init__(
        self,
        fighter_id: str,
        contract_type: ContractType,
        terms: ContractTerms,
        total_fights: int = 4,
        contract_id: Optional[str] = None
    ):
        """
        Create a contract.
        
        Args:
            fighter_id: ID of the fighter
            contract_type: Type of contract
            terms: Financial terms
            total_fights: Number of fights in contract
            contract_id: Unique ID (auto-generated if not provided)
        """
        self._id = contract_id or str(uuid.uuid4())[:12]
        self._fighter_id = fighter_id
        self._contract_type = contract_type
        self._terms = terms
        
        # Duration
        self._total_fights = total_fights
        self._fights_completed = 0
        
        # Status
        self._status = ContractStatus.ACTIVE
        self._signed_date = calendar.current_date
        self._expiry_date: Optional[GameDate] = None
        self._terminated_date: Optional[GameDate] = None
        
        # Tracking
        self._total_earnings = 0
        self._bonuses_earned = 0
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def fighter_id(self) -> str:
        return self._fighter_id
    
    @property
    def contract_type(self) -> ContractType:
        return self._contract_type
    
    @property
    def terms(self) -> ContractTerms:
        return self._terms
    
    @property
    def status(self) -> ContractStatus:
        return self._status
    
    @property
    def is_active(self) -> bool:
        return self._status == ContractStatus.ACTIVE
    
    @property
    def is_expired(self) -> bool:
        return self._status == ContractStatus.EXPIRED
    
    @property
    def total_fights(self) -> int:
        return self._total_fights
    
    @property
    def fights_completed(self) -> int:
        return self._fights_completed
    
    @property
    def fights_remaining(self) -> int:
        return max(0, self._total_fights - self._fights_completed)
    
    @property
    def signed_date(self) -> GameDate:
        return self._signed_date
    
    @property
    def total_earnings(self) -> int:
        return self._total_earnings
    
    # ========================================================================
    # METHODS
    # ========================================================================
    
    def record_fight(self, won: bool = False, was_finish: bool = False) -> int:
        """
        Record a completed fight under this contract.
        
        Args:
            won: Did the fighter win?
            was_finish: Was it a finish (KO/TKO/Sub)?
        
        Returns:
            Total payout for this fight
        """
        if not self.is_active:
            return 0
        
        payout = self._terms.base_purse
        
        if won:
            payout += self._terms.win_bonus
            self._bonuses_earned += self._terms.win_bonus
            
            if was_finish:
                payout += self._terms.finish_bonus
                self._bonuses_earned += self._terms.finish_bonus
        
        self._total_earnings += payout
        self._fights_completed += 1
        
        # Check if contract is now complete
        if self._fights_completed >= self._total_fights:
            self._expire()
        
        return payout
    
    def _expire(self) -> None:
        """Mark contract as expired"""
        self._status = ContractStatus.EXPIRED
        self._expiry_date = calendar.current_date
    
    def terminate(self, reason: str = "") -> None:
        """Terminate contract early"""
        self._status = ContractStatus.TERMINATED
        self._terminated_date = calendar.current_date
    
    def extend(self, additional_fights: int) -> None:
        """Extend contract by additional fights"""
        self._total_fights += additional_fights
        if self._status == ContractStatus.EXPIRED:
            self._status = ContractStatus.ACTIVE
            self._expiry_date = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Export contract data"""
        return {
            "id": self._id,
            "fighter_id": self._fighter_id,
            "contract_type": self._contract_type.value,
            "terms": {
                "base_purse": self._terms.base_purse,
                "win_bonus": self._terms.win_bonus,
                "finish_bonus": self._terms.finish_bonus,
                "ppv_points": self._terms.ppv_points,
                "ppv_percentage": self._terms.ppv_percentage,
                "signing_bonus": self._terms.signing_bonus,
                "camp_cut_percentage": self._terms.camp_cut_percentage
            },
            "total_fights": self._total_fights,
            "fights_completed": self._fights_completed,
            "status": self._status.name,
            "signed_date": {
                "year": self._signed_date.year,
                "month": self._signed_date.month,
                "day": self._signed_date.day
            },
            "total_earnings": self._total_earnings,
            "bonuses_earned": self._bonuses_earned
        }


# ============================================================================
# CAMP CONTRACT
# ============================================================================

class CampContract(BaseContract):
    """
    Contract between a fighter and a training camp.
    
    The camp provides training and management in exchange
    for a percentage of the fighter's earnings.
    """
    
    def __init__(
        self,
        fighter_id: str,
        camp_id: str,
        terms: ContractTerms,
        total_fights: int = 6,
        contract_id: Optional[str] = None
    ):
        """
        Create a camp contract.
        
        Args:
            fighter_id: ID of the fighter
            camp_id: ID of the camp
            terms: Financial terms
            total_fights: Contract duration in fights
            contract_id: Unique ID
        """
        super().__init__(
            fighter_id=fighter_id,
            contract_type=ContractType.CAMP,
            terms=terms,
            total_fights=total_fights,
            contract_id=contract_id
        )
        self._camp_id = camp_id
        self._camp_earnings = 0
    
    @property
    def camp_id(self) -> str:
        return self._camp_id
    
    @property
    def camp_cut_percentage(self) -> float:
        return self._terms.camp_cut_percentage
    
    @property
    def camp_earnings(self) -> int:
        """Total earnings the camp has received"""
        return self._camp_earnings
    
    def calculate_camp_cut(self, fighter_earnings: int) -> int:
        """
        Calculate camp's cut of fighter earnings.
        
        Args:
            fighter_earnings: Fighter's total earnings from a fight
        
        Returns:
            Amount that goes to the camp
        """
        return int(fighter_earnings * (self._terms.camp_cut_percentage / 100))
    
    def record_fight(self, won: bool = False, was_finish: bool = False) -> int:
        """Record fight and track camp earnings"""
        payout = super().record_fight(won, was_finish)
        camp_cut = self.calculate_camp_cut(payout)
        self._camp_earnings += camp_cut
        return payout
    
    def to_dict(self) -> Dict[str, Any]:
        """Export camp contract data"""
        data = super().to_dict()
        data["camp_id"] = self._camp_id
        data["camp_earnings"] = self._camp_earnings
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampContract':
        """Create camp contract from saved data"""
        terms_data = data["terms"]
        terms = ContractTerms(
            base_purse=terms_data["base_purse"],
            win_bonus=terms_data["win_bonus"],
            finish_bonus=terms_data["finish_bonus"],
            ppv_points=terms_data.get("ppv_points", False),
            ppv_percentage=terms_data.get("ppv_percentage", 0.0),
            signing_bonus=terms_data.get("signing_bonus", 0),
            camp_cut_percentage=terms_data.get("camp_cut_percentage", 15.0)
        )
        
        contract = cls(
            fighter_id=data["fighter_id"],
            camp_id=data["camp_id"],
            terms=terms,
            total_fights=data["total_fights"],
            contract_id=data["id"]
        )
        
        contract._fights_completed = data["fights_completed"]
        contract._status = ContractStatus[data["status"]]
        
        sd = data["signed_date"]
        contract._signed_date = GameDate(sd["year"], sd["month"], sd["day"])
        
        contract._total_earnings = data.get("total_earnings", 0)
        contract._bonuses_earned = data.get("bonuses_earned", 0)
        contract._camp_earnings = data.get("camp_earnings", 0)
        
        return contract
    
    def __repr__(self) -> str:
        return f"CampContract(fighter={self._fighter_id}, camp={self._camp_id}, {self.fights_remaining}/{self._total_fights} fights)"


# ============================================================================
# PROMOTIONAL CONTRACT
# ============================================================================

class PromotionalContract(BaseContract):
    """
    Contract between a fighter and a promotion (DFC).
    
    Determines the fighter's purse, bonuses, and fight
    obligations to the promotion.
    """
    
    def __init__(
        self,
        fighter_id: str,
        promotion_id: str,
        terms: ContractTerms,
        total_fights: int = 4,
        weight_class: Optional[WeightClass] = None,
        is_exclusive: bool = True,
        contract_id: Optional[str] = None
    ):
        """
        Create a promotional contract.
        
        Args:
            fighter_id: ID of the fighter
            promotion_id: ID of the promotion
            terms: Financial terms
            total_fights: Contract duration in fights
            weight_class: Fighter's contracted weight class
            is_exclusive: Can fighter fight elsewhere?
            contract_id: Unique ID
        """
        super().__init__(
            fighter_id=fighter_id,
            contract_type=ContractType.PROMOTIONAL,
            terms=terms,
            total_fights=total_fights,
            contract_id=contract_id
        )
        self._promotion_id = promotion_id
        self._weight_class = weight_class
        self._is_exclusive = is_exclusive
        self._title_fights = 0
        self._main_events = 0
    
    @property
    def promotion_id(self) -> str:
        return self._promotion_id
    
    @property
    def weight_class(self) -> Optional[WeightClass]:
        return self._weight_class
    
    @weight_class.setter
    def weight_class(self, value: WeightClass) -> None:
        self._weight_class = value
    
    @property
    def is_exclusive(self) -> bool:
        return self._is_exclusive
    
    @property
    def base_purse(self) -> int:
        return self._terms.base_purse
    
    @property
    def win_bonus(self) -> int:
        return self._terms.win_bonus
    
    @property
    def has_ppv_points(self) -> bool:
        return self._terms.ppv_points
    
    @property
    def title_fights(self) -> int:
        return self._title_fights
    
    @property
    def main_events(self) -> int:
        return self._main_events
    
    def record_fight(
        self, 
        won: bool = False, 
        was_finish: bool = False,
        was_title_fight: bool = False,
        was_main_event: bool = False
    ) -> int:
        """
        Record a completed fight.
        
        Args:
            won: Did the fighter win?
            was_finish: Was it a finish?
            was_title_fight: Was it a title fight?
            was_main_event: Was it the main event?
        
        Returns:
            Total payout
        """
        payout = super().record_fight(won, was_finish)
        
        if was_title_fight:
            self._title_fights += 1
        if was_main_event:
            self._main_events += 1
        
        return payout
    
    def calculate_fight_purse(
        self,
        is_title_fight: bool = False,
        is_main_event: bool = False
    ) -> int:
        """
        Calculate purse for an upcoming fight.
        
        Args:
            is_title_fight: Is this a title fight?
            is_main_event: Is this the main event?
        
        Returns:
            Base purse for this fight
        """
        purse = self._terms.base_purse
        
        if is_title_fight:
            multiplier = get_config("economy.title_fight_multiplier", 2.0)
            purse = int(purse * multiplier)
        elif is_main_event:
            multiplier = get_config("economy.main_event_multiplier", 1.5)
            purse = int(purse * multiplier)
        
        return purse
    
    def to_dict(self) -> Dict[str, Any]:
        """Export promotional contract data"""
        data = super().to_dict()
        data["promotion_id"] = self._promotion_id
        data["weight_class"] = self._weight_class.value if self._weight_class else None
        data["is_exclusive"] = self._is_exclusive
        data["title_fights"] = self._title_fights
        data["main_events"] = self._main_events
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromotionalContract':
        """Create promotional contract from saved data"""
        terms_data = data["terms"]
        terms = ContractTerms(
            base_purse=terms_data["base_purse"],
            win_bonus=terms_data["win_bonus"],
            finish_bonus=terms_data["finish_bonus"],
            ppv_points=terms_data.get("ppv_points", False),
            ppv_percentage=terms_data.get("ppv_percentage", 0.0),
            signing_bonus=terms_data.get("signing_bonus", 0),
            camp_cut_percentage=terms_data.get("camp_cut_percentage", 15.0)
        )
        
        weight_class = None
        if data.get("weight_class"):
            weight_class = WeightClass(data["weight_class"])
        
        contract = cls(
            fighter_id=data["fighter_id"],
            promotion_id=data["promotion_id"],
            terms=terms,
            total_fights=data["total_fights"],
            weight_class=weight_class,
            is_exclusive=data.get("is_exclusive", True),
            contract_id=data["id"]
        )
        
        contract._fights_completed = data["fights_completed"]
        contract._status = ContractStatus[data["status"]]
        
        sd = data["signed_date"]
        contract._signed_date = GameDate(sd["year"], sd["month"], sd["day"])
        
        contract._total_earnings = data.get("total_earnings", 0)
        contract._bonuses_earned = data.get("bonuses_earned", 0)
        contract._title_fights = data.get("title_fights", 0)
        contract._main_events = data.get("main_events", 0)
        
        return contract
    
    def __repr__(self) -> str:
        return f"PromotionalContract(fighter={self._fighter_id}, {self.fights_remaining}/{self._total_fights} fights, ${self._terms.base_purse})"


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_camp_contract(
    fighter_id: str,
    camp_id: str,
    duration_fights: int = 6,
    camp_cut_percentage: float = 15.0,
    base_purse: int = 10000,
    win_bonus: int = 5000
) -> CampContract:
    """
    Create a camp contract with standard terms.
    
    Args:
        fighter_id: Fighter's ID
        camp_id: Camp's ID
        duration_fights: Number of fights
        camp_cut_percentage: Camp's percentage cut
        base_purse: Base fight purse
        win_bonus: Win bonus amount
    
    Returns:
        New CampContract
    """
    terms = ContractTerms(
        base_purse=base_purse,
        win_bonus=win_bonus,
        finish_bonus=2500,
        camp_cut_percentage=camp_cut_percentage
    )
    
    return CampContract(
        fighter_id=fighter_id,
        camp_id=camp_id,
        terms=terms,
        total_fights=duration_fights
    )


def create_promotional_contract(
    fighter_id: str,
    promotion_id: str,
    fights: int = 4,
    base_purse: int = 15000,
    win_bonus: int = 7500,
    weight_class: Optional[WeightClass] = None,
    ppv_points: bool = False
) -> PromotionalContract:
    """
    Create a promotional contract with standard terms.
    
    Args:
        fighter_id: Fighter's ID
        promotion_id: Promotion's ID
        fights: Number of fights
        base_purse: Base fight purse
        win_bonus: Win bonus amount
        weight_class: Contracted weight class
        ppv_points: Include PPV points?
    
    Returns:
        New PromotionalContract
    """
    terms = ContractTerms(
        base_purse=base_purse,
        win_bonus=win_bonus,
        finish_bonus=5000,
        ppv_points=ppv_points,
        ppv_percentage=0.5 if ppv_points else 0.0
    )
    
    return PromotionalContract(
        fighter_id=fighter_id,
        promotion_id=promotion_id,
        terms=terms,
        total_fights=fights,
        weight_class=weight_class
    )


# ============================================================================
# CONTRACT MANAGER
# ============================================================================

class ContractManager:
    """
    Manages all contracts in the game.
    
    Provides lookup and management functionality for
    camp and promotional contracts.
    """
    
    def __init__(self):
        self._camp_contracts: Dict[str, CampContract] = {}
        self._promo_contracts: Dict[str, PromotionalContract] = {}
        # Index by fighter for quick lookup
        self._fighter_camp_contracts: Dict[str, str] = {}  # fighter_id -> contract_id
        self._fighter_promo_contracts: Dict[str, str] = {}  # fighter_id -> contract_id
    
    def add_camp_contract(self, contract: CampContract) -> None:
        """Add a camp contract"""
        self._camp_contracts[contract.id] = contract
        self._fighter_camp_contracts[contract.fighter_id] = contract.id
    
    def add_promo_contract(self, contract: PromotionalContract) -> None:
        """Add a promotional contract"""
        self._promo_contracts[contract.id] = contract
        self._fighter_promo_contracts[contract.fighter_id] = contract.id
    
    def get_camp_contract(self, contract_id: str) -> Optional[CampContract]:
        """Get a camp contract by ID"""
        return self._camp_contracts.get(contract_id)
    
    def get_promo_contract(self, contract_id: str) -> Optional[PromotionalContract]:
        """Get a promotional contract by ID"""
        return self._promo_contracts.get(contract_id)
    
    def get_fighter_camp_contract(self, fighter_id: str) -> Optional[CampContract]:
        """Get a fighter's active camp contract"""
        contract_id = self._fighter_camp_contracts.get(fighter_id)
        if contract_id:
            contract = self._camp_contracts.get(contract_id)
            if contract and contract.is_active:
                return contract
        return None
    
    def get_fighter_promo_contract(self, fighter_id: str) -> Optional[PromotionalContract]:
        """Get a fighter's active promotional contract"""
        contract_id = self._fighter_promo_contracts.get(fighter_id)
        if contract_id:
            contract = self._promo_contracts.get(contract_id)
            if contract and contract.is_active:
                return contract
        return None
    
    def get_camp_contracts(self, camp_id: str) -> List[CampContract]:
        """Get all contracts for a camp"""
        return [c for c in self._camp_contracts.values() if c.camp_id == camp_id]
    
    def get_active_camp_contracts(self, camp_id: str) -> List[CampContract]:
        """Get active contracts for a camp"""
        return [c for c in self._camp_contracts.values() 
                if c.camp_id == camp_id and c.is_active]
    
    def remove_contract(self, contract_id: str) -> bool:
        """Remove a contract"""
        if contract_id in self._camp_contracts:
            contract = self._camp_contracts.pop(contract_id)
            if contract.fighter_id in self._fighter_camp_contracts:
                del self._fighter_camp_contracts[contract.fighter_id]
            return True
        
        if contract_id in self._promo_contracts:
            contract = self._promo_contracts.pop(contract_id)
            if contract.fighter_id in self._fighter_promo_contracts:
                del self._fighter_promo_contracts[contract.fighter_id]
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all contracts"""
        return {
            "camp_contracts": [c.to_dict() for c in self._camp_contracts.values()],
            "promo_contracts": [c.to_dict() for c in self._promo_contracts.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContractManager':
        """Create manager from saved data"""
        manager = cls()
        
        for contract_data in data.get("camp_contracts", []):
            contract = CampContract.from_dict(contract_data)
            manager.add_camp_contract(contract)
        
        for contract_data in data.get("promo_contracts", []):
            contract = PromotionalContract.from_dict(contract_data)
            manager.add_promo_contract(contract)
        
        return manager
