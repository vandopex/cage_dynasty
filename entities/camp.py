# entities/camp.py
# Module 6: Camp Entity
# Lines: ~770
#
# Training camps - where fighters train and careers are built.
# The player controls one camp; AI controls the rest.

"""
Cage Dynasty - Camp Entity

This module defines the Camp class, representing a training facility
that signs and develops fighters. Camps have:
- Tier levels (Garage -> Elite) affecting facilities and capacity
- Style specialties (what fighting styles the camp excels at)
- Roster of signed fighters
- Coaching staff
- Financial management
- Culture/philosophy that affects training

The player controls one camp, while AI manages competing camps.
All camps follow the same rules - no special advantages for player or AI.

USAGE:
    from entities.camp import Camp, create_camp
    
    # Create a camp
    camp = create_camp(
        name="Iron Warriors",
        tier=CampTier.GARAGE,
        is_player_controlled=True
    )
    
    # Sign a fighter
    camp.sign_fighter(fighter)
    
    # Check finances
    print(camp.balance)
    print(camp.monthly_costs)
    
    # Style specialties
    print(camp.style_specialties)  # [FightingStyle.WRESTLER, FightingStyle.GROUND_AND_POUND]

IMPORT RULES:
- This module imports from core modules and entities.fighter
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import uuid

from core.types import (
    CampTier, CampCulture, WeightClass, EventType, FightingStyle,
    FighterID, CampID
)
from core.calendar import GameDate, calendar
from core.events import emit
from core.config import get_config


# ============================================================================
# COACH CLASS
# ============================================================================

class CoachSpecialty(Enum):
    """Areas a coach can specialize in"""
    STRIKING = "Striking"
    GRAPPLING = "Grappling"
    WRESTLING = "Wrestling"
    CONDITIONING = "Conditioning"
    GAME_PLANNING = "Game Planning"
    CORNERING = "Cornering"


@dataclass
class Coach:
    """
    A coach on staff at a camp.
    
    Coaches provide training bonuses in their specialty areas
    and can improve fighter development.
    """
    name: str
    specialty: CoachSpecialty
    quality: int  # 1-5 stars
    salary: int  # Weekly salary
    coach_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    @property
    def quality_multiplier(self) -> float:
        """Training effectiveness multiplier based on quality"""
        multipliers = get_config("training.coach_quality_multiplier", {
            1: 0.6, 2: 0.8, 3: 1.0, 4: 1.2, 5: 1.5
        })
        return multipliers.get(self.quality, 1.0)
    
    def __str__(self) -> str:
        stars = "â˜…" * self.quality + "â˜†" * (5 - self.quality)
        return f"{self.name} ({self.specialty.value}) {stars}"


# ============================================================================
# UPGRADE COSTS - Hardcoded to avoid config issues
# ============================================================================

# Define upgrade costs directly to avoid config lookup issues
UPGRADE_COSTS = {
    CampTier.GARAGE: 50000,    # GARAGE -> LOCAL
    CampTier.LOCAL: 150000,    # LOCAL -> REGIONAL
    CampTier.REGIONAL: 500000, # REGIONAL -> NATIONAL
    CampTier.NATIONAL: 2000000 # NATIONAL -> ELITE
}


# ============================================================================
# CAMP CLASS
# ============================================================================

class Camp:
    """
    Represents a training camp/gym in the game.
    
    Camps sign fighters, provide training, and compete for
    championships and prestige. The player manages one camp
    while AI manages all others.
    """
    
    def __init__(
        self,
        name: str,
        tier: CampTier = CampTier.GARAGE,
        culture: CampCulture = CampCulture.FAMILY,
        is_player_controlled: bool = False,
        camp_id: Optional[str] = None,
        location: str = "Las Vegas",
        style_specialties: Optional[List[FightingStyle]] = None
    ):
        """
        Create a new camp.
        
        Args:
            name: Camp name
            tier: Facility tier (affects capacity and training)
            culture: Camp philosophy
            is_player_controlled: True if this is the player's camp
            camp_id: Unique ID (auto-generated if not provided)
            location: City/region where camp is based
            style_specialties: Fighting styles this camp excels at (max 2)
        """
        # Identity
        self._id = camp_id or str(uuid.uuid4())[:12]
        self._name = name
        self._location = location
        self._is_player_controlled = is_player_controlled
        
        # Facility
        self._tier = tier
        self._culture = culture
        
        # Style Specialties (what this camp is known for)
        if style_specialties:
            self._style_specialties = style_specialties[:2]  # Max 2 specialties
        else:
            self._style_specialties: List[FightingStyle] = []
        
        # Roster
        self._fighter_ids: Set[str] = set()
        
        # Staff
        self._coaches: List[Coach] = []
        self._head_coach_id: Optional[str] = None  # coach_id of head coach
        
        # Finances
        starting_funds = get_config("camp.starting_funds", 50000)
        self._balance = starting_funds if is_player_controlled else starting_funds * 2
        self._total_earnings = 0
        self._total_expenses = 0
        
        # Reputation & Stats
        self._reputation = 50  # 0-100
        self._total_wins = 0
        self._total_losses = 0
        self._championships_won = 0
        
        # Metadata
        self._created_date = calendar.current_date
        self._is_active = True
    
    # ========================================================================
    # IDENTITY PROPERTIES
    # ========================================================================
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value
    
    @property
    def location(self) -> str:
        return self._location
    
    @property
    def is_player_controlled(self) -> bool:
        return self._is_player_controlled
    
    @property
    def is_ai_controlled(self) -> bool:
        return not self._is_player_controlled
    
    # ========================================================================
    # FACILITY PROPERTIES
    # ========================================================================
    
    @property
    def tier(self) -> CampTier:
        return self._tier
    
    @property
    def tier_name(self) -> str:
        """Human-readable tier name"""
        names = {
            CampTier.GARAGE: "Garage Gym",
            CampTier.LOCAL: "Local Gym",
            CampTier.REGIONAL: "Regional Camp",
            CampTier.NATIONAL: "National Camp",
            CampTier.ELITE: "Elite Camp"
        }
        return names.get(self._tier, "Unknown")
    
    @property
    def culture(self) -> CampCulture:
        return self._culture
    
    @culture.setter
    def culture(self, value: CampCulture) -> None:
        self._culture = value
    
    @property
    def max_fighters(self) -> int:
        """Maximum roster size based on tier"""
        limits = get_config("camp.max_fighters_by_tier", {
            1: 3, 2: 5, 3: 8, 4: 10, 5: 12
        })
        return limits.get(self._tier.value, 3)
    
    @property
    def training_bonus(self) -> float:
        """Training effectiveness multiplier based on tier"""
        # Higher tier = better facilities = better training
        base = 0.8 + (self._tier.value * 0.1)  # 0.9 to 1.3
        return base
    
    # ========================================================================
    # STYLE SPECIALTIES
    # ========================================================================
    
    @property
    def style_specialties(self) -> List[FightingStyle]:
        """Fighting styles this camp specializes in (copy to prevent modification)"""
        return self._style_specialties.copy()
    
    @property
    def style_specialties_display(self) -> str:
        """Display-friendly string of style specialties"""
        if not self._style_specialties:
            return "General MMA"
        return ", ".join(s.value for s in self._style_specialties)
    
    def has_style_specialty(self, style: FightingStyle) -> bool:
        """Check if camp specializes in a particular style"""
        return style in self._style_specialties
    
    def add_style_specialty(self, style: FightingStyle) -> bool:
        """
        Add a style specialty to the camp.
        
        Args:
            style: Fighting style to add as specialty
            
        Returns:
            True if added, False if already at max (2) or already has it
        """
        if len(self._style_specialties) >= 2:
            return False
        if style in self._style_specialties:
            return False
        self._style_specialties.append(style)
        return True
    
    def remove_style_specialty(self, style: FightingStyle) -> bool:
        """
        Remove a style specialty from the camp.
        
        Args:
            style: Fighting style to remove
            
        Returns:
            True if removed, False if not present
        """
        if style not in self._style_specialties:
            return False
        self._style_specialties.remove(style)
        return True
    
    def get_style_training_bonus(self, style: FightingStyle) -> float:
        """
        Get training bonus for a specific fighting style.
        
        Camps with specialties train those styles more effectively.
        
        Returns:
            Multiplier (1.0 = normal, 1.2 = specialty bonus)
        """
        if style in self._style_specialties:
            return 1.2  # 20% bonus for specialty styles
        return 1.0
    
    # ========================================================================
    # ROSTER MANAGEMENT
    # ========================================================================
    
    @property
    def fighter_ids(self) -> List[str]:
        """List of fighter IDs on roster"""
        return list(self._fighter_ids)
    
    @property
    def roster_size(self) -> int:
        """Current number of fighters"""
        return len(self._fighter_ids)
    
    @property
    def roster_spots_available(self) -> int:
        """Open spots on roster"""
        return max(0, self.max_fighters - self.roster_size)
    
    @property
    def is_roster_full(self) -> bool:
        """Check if roster is at capacity"""
        return self.roster_size >= self.max_fighters
    
    def has_fighter(self, fighter_id: str) -> bool:
        """Check if a fighter is on the roster"""
        return fighter_id in self._fighter_ids
    
    def sign_fighter(self, fighter_id: str) -> bool:
        """
        Add a fighter to the roster.
        
        Args:
            fighter_id: ID of fighter to sign
        
        Returns:
            True if signed successfully, False if roster full
        """
        if self.is_roster_full:
            return False
        
        if fighter_id in self._fighter_ids:
            return False  # Already signed
        
        self._fighter_ids.add(fighter_id)
        
        emit(EventType.FIGHTER_SIGNED, {
            "fighter_id": fighter_id,
            "camp_id": self._id,
            "camp_name": self._name
        })
        
        return True
    
    def release_fighter(self, fighter_id: str) -> bool:
        """
        Remove a fighter from the roster.
        
        Args:
            fighter_id: ID of fighter to release
        
        Returns:
            True if released, False if not on roster
        """
        if fighter_id not in self._fighter_ids:
            return False
        
        self._fighter_ids.remove(fighter_id)
        
        emit(EventType.FIGHTER_RELEASED, {
            "fighter_id": fighter_id,
            "camp_id": self._id,
            "camp_name": self._name
        })
        
        return True
    
    # ========================================================================
    # COACHING STAFF
    # ========================================================================
    
    @property
    def coaches(self) -> List[Coach]:
        """List of coaches on staff"""
        return self._coaches.copy()
    
    @property
    def coach_count(self) -> int:
        """Number of coaches"""
        return len(self._coaches)
    
    @property
    def head_coach(self) -> Optional[str]:
        """ID of the head coach, or None if no coaches"""
        return self._head_coach_id
    
    def hire_coach(self, coach: Coach) -> bool:
        """
        Add a coach to the staff.
        
        Args:
            coach: Coach to hire
        
        Returns:
            True if hired successfully
        """
        # Check if we can afford them (simplified)
        self._coaches.append(coach)
        
        # First coach becomes head coach
        if self._head_coach_id is None:
            self._head_coach_id = coach.coach_id
        
        return True
    
    def fire_coach(self, coach_id: str) -> bool:
        """
        Remove a coach from staff.
        
        Args:
            coach_id: ID of coach to fire
        
        Returns:
            True if fired, False if not found
        """
        for coach in self._coaches:
            if coach.coach_id == coach_id:
                self._coaches.remove(coach)
                if self._head_coach_id == coach_id:
                    # Assign new head coach if available
                    self._head_coach_id = self._coaches[0].coach_id if self._coaches else None
                return True
        return False
    
    def get_coach_by_specialty(self, specialty: CoachSpecialty) -> Optional[Coach]:
        """Find the best coach for a specialty"""
        matching = [c for c in self._coaches if c.specialty == specialty]
        if not matching:
            return None
        return max(matching, key=lambda c: c.quality)
    
    @property
    def total_coach_salary(self) -> int:
        """Total weekly salary for all coaches"""
        return sum(c.salary for c in self._coaches)
    
    # ========================================================================
    # FINANCES
    # ========================================================================
    
    @property
    def balance(self) -> int:
        """Current cash balance"""
        return self._balance
    
    @property
    def monthly_costs(self) -> int:
        """Monthly operating costs"""
        tier_costs = get_config("camp.tier_costs", {
            1: 5000, 2: 15000, 3: 40000, 4: 100000, 5: 250000
        })
        base_cost = tier_costs.get(self._tier.value, 5000)
        coach_cost = self.total_coach_salary * 4  # Monthly
        return base_cost + coach_cost
    
    @property
    def weekly_costs(self) -> int:
        """Weekly operating costs"""
        return self.monthly_costs // 4
    
    @property
    def total_earnings(self) -> int:
        """Total lifetime earnings"""
        return self._total_earnings
    
    @property
    def total_expenses(self) -> int:
        """Total lifetime expenses"""
        return self._total_expenses
    
    def add_funds(self, amount: int, source: str = "") -> None:
        """Add money to the camp"""
        self._balance += amount
        self._total_earnings += amount
    
    def deduct_funds(self, amount: int, reason: str = "") -> bool:
        """
        Deduct money from the camp.
        
        Returns:
            True if successful, False if insufficient funds
        """
        if amount > self._balance:
            return False
        
        self._balance -= amount
        self._total_expenses += amount
        return True
    
    def process_weekly_expenses(self) -> bool:
        """Process weekly operating costs"""
        return self.deduct_funds(self.weekly_costs, "Weekly operating costs")
    
    # Alias for backwards compatibility
    def process_weekly_costs(self) -> bool:
        """Alias for process_weekly_expenses"""
        return self.process_weekly_expenses()
    
    @property
    def is_bankrupt(self) -> bool:
        """Check if camp is out of money"""
        return self._balance < 0
    
    # ========================================================================
    # REPUTATION & RECORDS
    # ========================================================================
    
    @property
    def reputation(self) -> int:
        """Camp reputation (0-100)"""
        return self._reputation
    
    @reputation.setter
    def reputation(self, value: int) -> None:
        self._reputation = max(0, min(100, value))
    
    @property
    def total_wins(self) -> int:
        return self._total_wins
    
    @property
    def total_losses(self) -> int:
        return self._total_losses
    
    @property
    def win_percentage(self) -> float:
        """Camp's overall win percentage"""
        total = self._total_wins + self._total_losses
        if total == 0:
            return 0.0
        return (self._total_wins / total) * 100
    
    @property
    def win_rate(self) -> float:
        """Alias for win_percentage"""
        return self.win_percentage
    
    @property
    def championships_won(self) -> int:
        return self._championships_won
    
    def record_win(self) -> None:
        """Record a fighter win"""
        self._total_wins += 1
        self.reputation = min(100, self._reputation + 1)
    
    def record_loss(self) -> None:
        """Record a fighter loss"""
        self._total_losses += 1
        self.reputation = max(0, self._reputation - 1)
    
    def record_championship(self) -> None:
        """Record a championship win"""
        self._championships_won += 1
        self.reputation = min(100, self._reputation + 5)
    
    # ========================================================================
    # UPGRADE SYSTEM
    # ========================================================================
    
    def can_upgrade(self) -> bool:
        """Check if camp can upgrade to next tier"""
        if self._tier == CampTier.ELITE:
            return False  # Already max
        
        cost = self.get_upgrade_cost()
        return self._balance >= cost
    
    def get_upgrade_cost(self) -> int:
        """Get cost to upgrade to next tier"""
        # Use hardcoded costs to avoid config lookup issues
        return UPGRADE_COSTS.get(self._tier, 0)
    
    @property
    def upgrade_cost(self) -> int:
        """Property alias for get_upgrade_cost()"""
        return self.get_upgrade_cost()
    
    def upgrade(self) -> bool:
        """
        Upgrade camp to next tier.
        
        Returns:
            True if upgraded, False if can't upgrade
        """
        if not self.can_upgrade():
            return False
        
        cost = self.get_upgrade_cost()
        if not self.deduct_funds(cost, "Camp upgrade"):
            return False
        
        # Move to next tier
        tier_order = [CampTier.GARAGE, CampTier.LOCAL, CampTier.REGIONAL,
                     CampTier.NATIONAL, CampTier.ELITE]
        current_idx = tier_order.index(self._tier)
        self._tier = tier_order[current_idx + 1]
        
        emit(EventType.CAMP_UPGRADED, {
            "camp_id": self._id,
            "camp_name": self._name,
            "new_tier": self._tier.value
        })
        
        return True
    
    def upgrade_tier(self) -> bool:
        """Alias for upgrade()"""
        return self.upgrade()
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Export camp data for saving"""
        return {
            "id": self._id,
            "name": self._name,
            "location": self._location,
            "is_player_controlled": self._is_player_controlled,
            "tier": self._tier.value,
            "culture": self._culture.value,
            "style_specialties": [s.value for s in self._style_specialties],
            "fighter_ids": list(self._fighter_ids),
            "coaches": [
                {
                    "name": c.name,
                    "specialty": c.specialty.value,
                    "quality": c.quality,
                    "salary": c.salary,
                    "coach_id": c.coach_id
                }
                for c in self._coaches
            ],
            "head_coach": self._head_coach_id,
            "balance": self._balance,
            "total_earnings": self._total_earnings,
            "total_expenses": self._total_expenses,
            "reputation": self._reputation,
            "total_wins": self._total_wins,
            "total_losses": self._total_losses,
            "championships_won": self._championships_won,
            "is_active": self._is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Camp':
        """Create camp from saved data"""
        # Parse style specialties (with fallback for old saves)
        style_specialties = []
        for style_str in data.get("style_specialties", []):
            try:
                style_specialties.append(FightingStyle(style_str))
            except ValueError:
                pass  # Skip invalid styles
        
        camp = cls(
            name=data["name"],
            tier=CampTier(data["tier"]),
            culture=CampCulture(data["culture"]),
            is_player_controlled=data["is_player_controlled"],
            camp_id=data["id"],
            location=data.get("location", "Las Vegas"),
            style_specialties=style_specialties
        )
        
        camp._fighter_ids = set(data.get("fighter_ids", []))
        
        # Restore coaches
        for coach_data in data.get("coaches", []):
            coach = Coach(
                name=coach_data["name"],
                specialty=CoachSpecialty(coach_data["specialty"]),
                quality=coach_data["quality"],
                salary=coach_data["salary"],
                coach_id=coach_data.get("coach_id", str(uuid.uuid4())[:8])
            )
            camp._coaches.append(coach)
        
        camp._head_coach_id = data.get("head_coach")
        camp._balance = data.get("balance", 50000)
        camp._total_earnings = data.get("total_earnings", 0)
        camp._total_expenses = data.get("total_expenses", 0)
        camp._reputation = data.get("reputation", 50)
        camp._total_wins = data.get("total_wins", 0)
        camp._total_losses = data.get("total_losses", 0)
        camp._championships_won = data.get("championships_won", 0)
        camp._is_active = data.get("is_active", True)
        
        return camp
    
    def __repr__(self) -> str:
        return f"Camp({self._name}, {self.tier_name}, {self.roster_size}/{self.max_fighters} fighters)"
    
    def __str__(self) -> str:
        return f"{self._name} ({self.tier_name})"


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_camp(
    name: str,
    tier: CampTier = CampTier.GARAGE,
    culture: CampCulture = CampCulture.FAMILY,
    is_player_controlled: bool = False,
    location: str = "Las Vegas",
    style_specialties: Optional[List[FightingStyle]] = None
) -> Camp:
    """
    Factory function to create a new camp.
    
    Args:
        name: Camp name
        tier: Starting tier level
        culture: Camp philosophy
        is_player_controlled: True if player's camp
        location: City/region
        style_specialties: Fighting styles this camp excels at (max 2)
    
    Returns:
        New Camp instance
    """
    return Camp(
        name=name,
        tier=tier,
        culture=culture,
        is_player_controlled=is_player_controlled,
        location=location,
        style_specialties=style_specialties
    )
