# systems/aging.py
# Module 9: Aging & Degradation System
# Lines: 389
#
# Fighters age, peak, decline, and eventually retire.
# This creates realistic career arcs and generational turnover.

"""
Cage Dynasty - Aging & Degradation System

This module handles the biological reality of fighting careers:
- Fighters have prime years (typically 26-32)
- Physical attributes decline after prime
- Chin degrades faster (damage accumulation)
- Mental attributes decline slower (experience)
- Retirement decisions based on age, record, and decline

The system creates natural career arcs where young prospects
rise, champions reign during their prime, and legends fade
to make room for the next generation.

USAGE:
    from systems.aging import AgingSystem, calculate_decline
    
    # Create the system
    aging = AgingSystem()
    
    # Process weekly aging for all fighters
    aging.process_week(fighters)
    
    # Check individual fighter
    decline = calculate_decline(fighter)
    should_retire = aging.check_retirement(fighter)

IMPORT RULES:
- This module imports from core and entities
- Emits events for significant aging milestones
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum, auto
import random

from core.types import (
    EventType, FighterStatus,
    PHYSICAL_ATTRIBUTES, STRIKING_ATTRIBUTES,
    GRAPPLING_ATTRIBUTES, MENTAL_ATTRIBUTES,
    ALL_ATTRIBUTES
)
from core.calendar import GameDate, calendar
from core.events import emit
from core.config import get_config


# ============================================================================
# CAREER PHASE
# ============================================================================

class CareerPhase(Enum):
    """Phases of a fighter's career"""
    PROSPECT = auto()      # Young, still developing (18-25)
    PRIME = auto()         # Peak performance (26-32)
    VETERAN = auto()       # Experienced but declining (33-36)
    TWILIGHT = auto()      # Near retirement (37+)


# ============================================================================
# AGING PROFILE
# ============================================================================

@dataclass
class AgingProfile:
    """
    Snapshot of a fighter's aging status.
    
    Provides analysis of where a fighter is in their career
    and how much decline they're experiencing.
    """
    fighter_id: str
    age: int
    career_phase: CareerPhase
    years_past_prime: int
    total_decline_suffered: int
    physical_decline_rate: float
    mental_decline_rate: float
    chin_decline_rate: float
    retirement_probability: float
    
    @property
    def is_declining(self) -> bool:
        return self.years_past_prime > 0
    
    @property
    def decline_severity(self) -> str:
        """Human-readable decline description"""
        if self.years_past_prime <= 0:
            return "None"
        elif self.years_past_prime <= 2:
            return "Mild"
        elif self.years_past_prime <= 4:
            return "Moderate"
        elif self.years_past_prime <= 6:
            return "Significant"
        else:
            return "Severe"


# ============================================================================
# AGING CALCULATIONS
# ============================================================================

def get_career_phase(age: int) -> CareerPhase:
    """
    Determine career phase based on age.
    
    Args:
        age: Fighter's current age
    
    Returns:
        Current career phase
    """
    prime_start = get_config("aging.prime_start", 26)
    prime_end = get_config("aging.prime_end", 32)
    decline_start = get_config("aging.decline_start", 33)
    
    if age < prime_start:
        return CareerPhase.PROSPECT
    elif age <= prime_end:
        return CareerPhase.PRIME
    elif age <= decline_start + 3:  # 33-36
        return CareerPhase.VETERAN
    else:
        return CareerPhase.TWILIGHT


def calculate_years_past_prime(age: int) -> int:
    """
    Calculate how many years past prime a fighter is.
    
    Args:
        age: Fighter's current age
    
    Returns:
        Years past prime (0 if still in or before prime)
    """
    prime_end = get_config("aging.prime_end", 32)
    return max(0, age - prime_end)


def calculate_physical_decline(age: int, base_rate: Optional[float] = None) -> float:
    """
    Calculate annual physical attribute decline rate.
    
    Physical attributes (strength, speed, cardio, chin, recovery)
    decline faster than other attributes.
    
    Args:
        age: Fighter's current age
        base_rate: Override base decline rate
    
    Returns:
        Points of decline per year for physical attributes
    """
    if base_rate is None:
        base_rate = get_config("aging.decline_rate_physical", 2.0)
    
    years_past = calculate_years_past_prime(age)
    
    if years_past <= 0:
        return 0.0
    
    # Accelerating decline - worse each year
    # Year 1: base_rate, Year 2: base_rate * 1.1, etc.
    acceleration = 1.0 + (years_past - 1) * 0.1
    
    return base_rate * acceleration


def calculate_mental_decline(age: int, base_rate: Optional[float] = None) -> float:
    """
    Calculate annual mental attribute decline rate.
    
    Mental attributes (heart, IQ, composure, aggression) decline
    slower - experience somewhat compensates for physical decline.
    
    Args:
        age: Fighter's current age
        base_rate: Override base decline rate
    
    Returns:
        Points of decline per year for mental attributes
    """
    if base_rate is None:
        base_rate = get_config("aging.decline_rate_mental", 0.5)
    
    years_past = calculate_years_past_prime(age)
    
    if years_past <= 0:
        return 0.0
    
    # Mental decline starts later and is more gradual
    # No decline until 2 years past prime
    if years_past <= 2:
        return 0.0
    
    return base_rate * (1.0 + (years_past - 2) * 0.05)


def calculate_chin_decline(age: int, ko_losses: int = 0) -> float:
    """
    Calculate chin degradation rate.
    
    Chin degrades faster than other physical attributes due to
    accumulated damage. KO losses accelerate this.
    
    Args:
        age: Fighter's current age
        ko_losses: Number of KO/TKO losses suffered
    
    Returns:
        Points of decline per year for chin
    """
    base_rate = get_config("aging.decline_rate_physical", 2.0)
    chin_multiplier = get_config("aging.chin_decline_multiplier", 1.5)
    
    years_past = calculate_years_past_prime(age)
    
    if years_past <= 0:
        return 0.0
    
    # Base chin decline
    decline = base_rate * chin_multiplier
    
    # KO losses add extra decline
    ko_penalty = ko_losses * 0.5
    
    # Accelerating with age
    acceleration = 1.0 + (years_past - 1) * 0.15
    
    return (decline + ko_penalty) * acceleration


def calculate_retirement_probability(
    age: int,
    current_lose_streak: int = 0,
    is_champion: bool = False,
    total_fights: int = 0,
    morale: int = 50
) -> float:
    """
    Calculate probability a fighter will retire.
    
    Factors:
    - Age (primary factor)
    - Losing streak (fighters often retire after consecutive losses)
    - Championship status (champions hang on longer)
    - Career length (long careers = higher retirement chance)
    - Morale (low morale = more likely to retire)
    
    Args:
        age: Fighter's current age
        current_lose_streak: Consecutive losses
        is_champion: Currently holds a title
        total_fights: Career fight count
        morale: Current morale (0-100)
    
    Returns:
        Probability of retirement (0.0 to 1.0)
    """
    retirement_avg = get_config("aging.retirement_avg", 38)
    retirement_min = get_config("aging.retirement_min", 34)
    retirement_max = get_config("aging.retirement_max", 45)
    
    # No retirement before minimum age
    if age < retirement_min:
        return 0.0
    
    # Base probability increases with age
    if age >= retirement_max:
        base_prob = 0.8
    else:
        # Linear increase from min to avg, steeper from avg to max
        if age <= retirement_avg:
            base_prob = 0.05 + (age - retirement_min) * 0.05
        else:
            base_prob = 0.25 + (age - retirement_avg) * 0.1
    
    # Losing streak increases retirement chance
    streak_modifier = current_lose_streak * 0.1
    
    # Champions are less likely to retire
    champion_modifier = -0.15 if is_champion else 0.0
    
    # Long careers increase retirement chance
    career_modifier = 0.0
    if total_fights > 30:
        career_modifier = (total_fights - 30) * 0.01
    
    # Low morale increases retirement chance
    morale_modifier = (50 - morale) * 0.005 if morale < 50 else 0.0
    
    probability = base_prob + streak_modifier + champion_modifier + career_modifier + morale_modifier
    
    return max(0.0, min(1.0, probability))


# ============================================================================
# AGING SYSTEM
# ============================================================================

class AgingSystem:
    """
    Manages aging and degradation for all fighters.
    
    Should be called each week to process aging effects.
    Handles:
    - Annual attribute decline
    - Career phase transitions
    - Retirement decisions
    """
    
    def __init__(self):
        self._last_processed_year: Dict[str, int] = {}  # fighter_id -> year
        self._retirement_checks: Dict[str, GameDate] = {}  # fighter_id -> last check date
    
    def get_aging_profile(
        self,
        fighter_id: str,
        age: int,
        ko_losses: int = 0,
        lose_streak: int = 0,
        is_champion: bool = False,
        total_fights: int = 0,
        morale: int = 50
    ) -> AgingProfile:
        """
        Generate aging profile for a fighter.
        
        Args:
            fighter_id: Fighter's ID
            age: Current age
            ko_losses: Career KO/TKO losses
            lose_streak: Current consecutive losses
            is_champion: Holds a title
            total_fights: Career fight count
            morale: Current morale
        
        Returns:
            Complete AgingProfile
        """
        phase = get_career_phase(age)
        years_past = calculate_years_past_prime(age)
        
        physical_rate = calculate_physical_decline(age)
        mental_rate = calculate_mental_decline(age)
        chin_rate = calculate_chin_decline(age, ko_losses)
        
        # Estimate total decline suffered
        total_decline = 0
        for y in range(max(0, years_past)):
            check_age = get_config("aging.prime_end", 32) + y + 1
            total_decline += int(calculate_physical_decline(check_age))
        
        retirement_prob = calculate_retirement_probability(
            age, lose_streak, is_champion, total_fights, morale
        )
        
        return AgingProfile(
            fighter_id=fighter_id,
            age=age,
            career_phase=phase,
            years_past_prime=years_past,
            total_decline_suffered=total_decline,
            physical_decline_rate=physical_rate,
            mental_decline_rate=mental_rate,
            chin_decline_rate=chin_rate,
            retirement_probability=retirement_prob
        )
    
    def apply_annual_decline(
        self,
        fighter_id: str,
        age: int,
        current_attributes: Dict[str, int],
        ko_losses: int = 0
    ) -> Dict[str, int]:
        """
        Apply one year of aging decline to attributes.
        
        Args:
            fighter_id: Fighter's ID
            age: Current age
            current_attributes: Current attribute values
            ko_losses: Career KO/TKO losses
        
        Returns:
            Dictionary of attribute changes (negative values)
        """
        changes: Dict[str, int] = {}
        
        physical_decline = calculate_physical_decline(age)
        mental_decline = calculate_mental_decline(age)
        chin_decline = calculate_chin_decline(age, ko_losses)
        
        if physical_decline <= 0 and mental_decline <= 0:
            return changes  # No decline yet
        
        # Apply physical decline
        for attr in PHYSICAL_ATTRIBUTES:
            if attr == "chin":
                decline = int(chin_decline)
            else:
                decline = int(physical_decline)
            
            if decline > 0:
                # Add some randomness (+/- 1)
                actual_decline = decline + random.randint(-1, 1)
                actual_decline = max(0, actual_decline)
                if actual_decline > 0:
                    changes[attr] = -actual_decline
        
        # Striking and grappling decline at moderate rate
        technique_decline = int((physical_decline + mental_decline) / 2)
        if technique_decline > 0:
            for attr in list(STRIKING_ATTRIBUTES) + list(GRAPPLING_ATTRIBUTES):
                if attr not in ["power"]:  # Power tied to physical
                    actual = technique_decline + random.randint(-1, 0)
                    if actual > 0:
                        changes[attr] = -actual
            
            # Power declines with physical
            if physical_decline > 0:
                changes["power"] = -int(physical_decline)
        
        # Mental decline (slower)
        if mental_decline > 0:
            for attr in MENTAL_ATTRIBUTES:
                # IQ often improves or stays stable with experience
                if attr == "iq":
                    continue
                actual = int(mental_decline) + random.randint(-1, 0)
                if actual > 0:
                    changes[attr] = -actual
        
        return changes
    
    def should_process_annual_aging(self, fighter_id: str, current_year: int) -> bool:
        """Check if annual aging should be processed for this fighter"""
        last_year = self._last_processed_year.get(fighter_id, 0)
        return current_year > last_year
    
    def mark_annual_aging_processed(self, fighter_id: str, year: int) -> None:
        """Mark that annual aging was processed"""
        self._last_processed_year[fighter_id] = year
    
    def check_retirement(
        self,
        fighter_id: str,
        age: int,
        lose_streak: int = 0,
        is_champion: bool = False,
        total_fights: int = 0,
        morale: int = 50
    ) -> bool:
        """
        Check if a fighter should retire.
        
        Args:
            fighter_id: Fighter's ID
            age: Current age
            lose_streak: Current consecutive losses
            is_champion: Holds a title
            total_fights: Career fight count
            morale: Current morale
        
        Returns:
            True if fighter should retire
        """
        probability = calculate_retirement_probability(
            age, lose_streak, is_champion, total_fights, morale
        )
        
        return random.random() < probability
    
    def process_birthday(
        self,
        fighter_id: str,
        new_age: int,
        ko_losses: int = 0
    ) -> Tuple[CareerPhase, Dict[str, int]]:
        """
        Process a fighter's birthday (annual aging).
        
        Args:
            fighter_id: Fighter's ID
            new_age: Age after birthday
            ko_losses: Career KO/TKO losses
        
        Returns:
            Tuple of (new career phase, attribute changes)
        """
        phase = get_career_phase(new_age)
        
        # Get decline
        changes = self.apply_annual_decline(
            fighter_id, new_age, {}, ko_losses
        )
        
        # Emit phase transition events
        old_phase = get_career_phase(new_age - 1)
        if phase != old_phase:
            emit(EventType.FIGHTER_RANKED, {  # Reusing event for phase change
                "fighter_id": fighter_id,
                "event": "career_phase_change",
                "old_phase": old_phase.name,
                "new_phase": phase.name,
                "age": new_age
            })
        
        return phase, changes
    
    def to_dict(self) -> Dict[str, Any]:
        """Export system state"""
        return {
            "last_processed_year": self._last_processed_year.copy(),
            "retirement_checks": {
                fid: {"year": d.year, "month": d.month, "day": d.day}
                for fid, d in self._retirement_checks.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgingSystem':
        """Create system from saved data"""
        system = cls()
        system._last_processed_year = data.get("last_processed_year", {})
        
        for fid, date_data in data.get("retirement_checks", {}).items():
            system._retirement_checks[fid] = GameDate(
                date_data["year"], date_data["month"], date_data["day"]
            )
        
        return system


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_prime_years() -> Tuple[int, int]:
    """Get the prime age range"""
    return (
        get_config("aging.prime_start", 26),
        get_config("aging.prime_end", 32)
    )


def is_in_prime(age: int) -> bool:
    """Check if age is within prime years"""
    start, end = get_prime_years()
    return start <= age <= end


def years_until_decline(age: int) -> int:
    """Calculate years until decline begins"""
    prime_end = get_config("aging.prime_end", 32)
    return max(0, prime_end - age)
