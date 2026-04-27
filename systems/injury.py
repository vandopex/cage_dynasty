# systems/injury.py
# Module 11: Injury System
# Lines: 487
#
# Handles fighter injuries, recovery times, and injury probability calculations.
# Injuries can occur during fights or training, with severity affecting recovery.

"""
Cage Dynasty - Injury System

This module manages all aspects of fighter injuries:
- Injury creation and tracking
- Recovery time calculations
- Fight injury probability based on outcome
- Training injury probability based on intensity
- Medical clearance tracking

Injury severity affects:
- Recovery time (weeks out)
- Attribute impact during recovery
- Long-term effects (career injuries)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import date
import random

from core.types import InjuryType, FightOutcome, EventType
from core.events import emit, event_bus
from core.config import get_config
from core.calendar import calendar, GameDate


# ============================================================================
# INJURY LOCATIONS
# ============================================================================

class InjuryLocation(Enum):
    """Body parts that can be injured"""
    HEAD = "Head"
    FACE = "Face"
    NECK = "Neck"
    SHOULDER = "Shoulder"
    ARM = "Arm"
    ELBOW = "Elbow"
    HAND = "Hand"
    RIBS = "Ribs"
    BACK = "Back"
    HIP = "Hip"
    KNEE = "Knee"
    LEG = "Leg"
    ANKLE = "Ankle"
    FOOT = "Foot"


# Injury descriptions by type and location
INJURY_DESCRIPTIONS: Dict[InjuryType, Dict[InjuryLocation, List[str]]] = {
    InjuryType.MINOR: {
        InjuryLocation.HEAD: ["Minor concussion symptoms", "Head contusion"],
        InjuryLocation.FACE: ["Facial laceration", "Swollen eye", "Cut above eye"],
        InjuryLocation.HAND: ["Bruised knuckles", "Jammed finger"],
        InjuryLocation.RIBS: ["Bruised ribs", "Rib contusion"],
        InjuryLocation.LEG: ["Leg contusion", "Calf bruise"],
        InjuryLocation.FOOT: ["Bruised foot", "Toe sprain"],
    },
    InjuryType.MODERATE: {
        InjuryLocation.HEAD: ["Concussion", "Post-concussion syndrome"],
        InjuryLocation.SHOULDER: ["Shoulder strain", "Rotator cuff strain"],
        InjuryLocation.ARM: ["Bicep strain", "Tricep strain"],
        InjuryLocation.ELBOW: ["Hyperextended elbow", "Elbow sprain"],
        InjuryLocation.HAND: ["Fractured metacarpal", "Broken hand"],
        InjuryLocation.RIBS: ["Cracked rib", "Intercostal strain"],
        InjuryLocation.KNEE: ["MCL sprain", "Knee hyperextension"],
        InjuryLocation.ANKLE: ["High ankle sprain", "Ankle ligament damage"],
    },
    InjuryType.SEVERE: {
        InjuryLocation.HEAD: ["Severe concussion", "Traumatic brain injury"],
        InjuryLocation.NECK: ["Neck injury", "Herniated disc (cervical)"],
        InjuryLocation.SHOULDER: ["Torn rotator cuff", "Dislocated shoulder"],
        InjuryLocation.ARM: ["Broken arm", "Fractured humerus"],
        InjuryLocation.ELBOW: ["Torn UCL", "Fractured elbow"],
        InjuryLocation.BACK: ["Herniated disc (lumbar)", "Spinal injury"],
        InjuryLocation.KNEE: ["Torn ACL", "Torn meniscus", "MCL tear"],
        InjuryLocation.LEG: ["Fractured tibia", "Broken leg"],
        InjuryLocation.ANKLE: ["Fractured ankle", "Severe ligament tear"],
    },
    InjuryType.CAREER: {
        InjuryLocation.HEAD: ["Chronic traumatic encephalopathy symptoms", "Severe TBI"],
        InjuryLocation.NECK: ["Severe spinal injury", "Fractured vertebrae"],
        InjuryLocation.BACK: ["Multiple herniated discs", "Degenerative disc disease"],
        InjuryLocation.KNEE: ["Complete knee reconstruction needed", "Multiple ligament tears"],
        InjuryLocation.SHOULDER: ["Complete shoulder reconstruction", "Chronic instability"],
    },
}


# ============================================================================
# RECOVERY TIME RANGES (in weeks)
# ============================================================================

RECOVERY_TIMES: Dict[InjuryType, Tuple[int, int]] = {
    InjuryType.MINOR: (1, 3),      # 1-3 weeks
    InjuryType.MODERATE: (4, 10),   # 4-10 weeks
    InjuryType.SEVERE: (12, 26),    # 3-6 months
    InjuryType.CAREER: (26, 52),    # 6-12 months
}


# ============================================================================
# INJURY DATA CLASS
# ============================================================================

@dataclass
class Injury:
    """
    Represents a single injury sustained by a fighter.
    
    Attributes:
        injury_id: Unique identifier
        fighter_id: Fighter who sustained the injury
        injury_type: Severity of injury
        location: Body part injured
        description: Human-readable description
        sustained_date: When the injury occurred
        recovery_weeks: Total weeks needed for recovery
        weeks_healed: Weeks of recovery completed
        source: How the injury occurred (fight, training, etc.)
        opponent_id: If from a fight, who caused it
        permanent_effects: Any lasting attribute impacts
    """
    injury_id: str
    fighter_id: str
    injury_type: InjuryType
    location: InjuryLocation
    description: str
    sustained_date: GameDate
    recovery_weeks: int
    weeks_healed: int = 0
    source: str = "fight"  # fight, training, accident
    opponent_id: Optional[str] = None
    permanent_effects: Dict[str, int] = field(default_factory=dict)
    
    @property
    def weeks_remaining(self) -> int:
        """Weeks until fully recovered"""
        return max(0, self.recovery_weeks - self.weeks_healed)
    
    @property
    def is_healed(self) -> bool:
        """Whether the injury has fully healed"""
        return self.weeks_healed >= self.recovery_weeks
    
    @property
    def recovery_progress(self) -> float:
        """Recovery progress as percentage (0-100)"""
        if self.recovery_weeks == 0:
            return 100.0
        return min(100.0, (self.weeks_healed / self.recovery_weeks) * 100)
    
    @property
    def severity_name(self) -> str:
        """Human-readable severity"""
        return self.injury_type.name.title()
    
    def heal_week(self) -> bool:
        """
        Process one week of healing.
        
        Returns:
            True if now fully healed, False otherwise
        """
        if not self.is_healed:
            self.weeks_healed += 1
        return self.is_healed
    
    def __str__(self) -> str:
        status = "Healed" if self.is_healed else f"{self.weeks_remaining} weeks"
        return f"{self.description} ({self.severity_name}) - {status}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "injury_id": self.injury_id,
            "fighter_id": self.fighter_id,
            "injury_type": self.injury_type.name,
            "location": self.location.value,
            "description": self.description,
            "sustained_date": {
                "year": self.sustained_date.year,
                "month": self.sustained_date.month,
                "day": self.sustained_date.day
            },
            "recovery_weeks": self.recovery_weeks,
            "weeks_healed": self.weeks_healed,
            "source": self.source,
            "opponent_id": self.opponent_id,
            "permanent_effects": self.permanent_effects
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Injury':
        """Deserialize from dictionary"""
        date_data = data["sustained_date"]
        return cls(
            injury_id=data["injury_id"],
            fighter_id=data["fighter_id"],
            injury_type=InjuryType[data["injury_type"]],
            location=InjuryLocation(data["location"]),
            description=data["description"],
            sustained_date=GameDate(
                date_data["year"],
                date_data["month"],
                date_data["day"]
            ),
            recovery_weeks=data["recovery_weeks"],
            weeks_healed=data.get("weeks_healed", 0),
            source=data.get("source", "fight"),
            opponent_id=data.get("opponent_id"),
            permanent_effects=data.get("permanent_effects", {})
        )


# ============================================================================
# INJURY PROBABILITY CALCULATIONS
# ============================================================================

def calculate_fight_injury_probability(
    outcome: FightOutcome,
    rounds_fought: int,
    is_loser: bool = False
) -> float:
    """
    Calculate probability of injury from a fight.
    
    Args:
        outcome: How the fight ended
        rounds_fought: Number of rounds the fight went
        is_loser: Whether this fighter lost
    
    Returns:
        Probability of injury (0.0 to 1.0)
    """
    base_prob = get_config("injury.base_fight_probability", 0.04)
    
    # Outcome modifiers
    outcome_mods = {
        FightOutcome.KO: 0.09 if is_loser else 0.025,
        FightOutcome.TKO: 0.06 if is_loser else 0.02,
        FightOutcome.SUBMISSION: 0.05 if is_loser else 0.015,
        FightOutcome.DECISION_UNANIMOUS: 0.025,
        FightOutcome.DECISION_SPLIT: 0.03,
        FightOutcome.DECISION_MAJORITY: 0.028,
        FightOutcome.DRAW: 0.025,
        FightOutcome.NO_CONTEST: 0.015,
        FightOutcome.DQ: 0.02,
    }
    
    prob = base_prob + outcome_mods.get(outcome, 0.0)
    
    # More rounds = higher chance
    prob += rounds_fought * 0.02
    
    # Losers more likely to be injured
    if is_loser:
        prob *= 1.3
    
    return min(1.0, prob)


def calculate_injury_severity_weights(
    outcome: FightOutcome,
    is_loser: bool = False
) -> Dict[InjuryType, float]:
    """
    Calculate relative weights for each injury severity.
    
    Returns weights that sum to 1.0
    """
    # Base weights favor minor injuries
    weights = {
        InjuryType.MINOR: 0.705,
        InjuryType.MODERATE: 0.27,
        InjuryType.SEVERE: 0.02,
        InjuryType.CAREER: 0.005,
    }
    
    # KO/TKO losses shift toward more severe
    if is_loser and outcome in (FightOutcome.KO, FightOutcome.TKO):
        weights[InjuryType.MINOR] = 0.52
        weights[InjuryType.MODERATE] = 0.42
        weights[InjuryType.SEVERE] = 0.05
        weights[InjuryType.CAREER] = 0.01
    
    # Submission losses can cause joint injuries
    elif is_loser and outcome == FightOutcome.SUBMISSION:
        weights[InjuryType.MINOR] = 0.57
        weights[InjuryType.MODERATE] = 0.38
        weights[InjuryType.SEVERE] = 0.04
        weights[InjuryType.CAREER] = 0.01
    
    return weights


def get_likely_locations(
    outcome: FightOutcome,
    injury_type: InjuryType
) -> List[InjuryLocation]:
    """
    Get likely injury locations based on how the fight ended.
    """
    # KO/TKO often affects head
    if outcome in (FightOutcome.KO, FightOutcome.TKO):
        if injury_type == InjuryType.MINOR:
            return [InjuryLocation.FACE, InjuryLocation.HEAD, InjuryLocation.HAND]
        elif injury_type == InjuryType.MODERATE:
            return [InjuryLocation.HEAD, InjuryLocation.HAND, InjuryLocation.RIBS]
        else:
            return [InjuryLocation.HEAD, InjuryLocation.NECK]
    
    # Submissions often affect limbs
    if outcome == FightOutcome.SUBMISSION:
        if injury_type in (InjuryType.MINOR, InjuryType.MODERATE):
            return [
                InjuryLocation.ELBOW, InjuryLocation.SHOULDER,
                InjuryLocation.KNEE, InjuryLocation.ANKLE
            ]
        else:
            return [
                InjuryLocation.KNEE, InjuryLocation.SHOULDER,
                InjuryLocation.ELBOW, InjuryLocation.NECK
            ]
    
    # Decisions - general wear and tear
    all_locations = list(INJURY_DESCRIPTIONS.get(injury_type, {}).keys())
    return all_locations if all_locations else [InjuryLocation.RIBS]


def calculate_training_injury_probability(
    intensity_value: int,
    current_fatigue: int
) -> float:
    """
    Calculate probability of injury during training.
    
    Args:
        intensity_value: Training intensity (1-4)
        current_fatigue: Current fatigue level (0-100)
    
    Returns:
        Probability of injury (0.0 to 1.0)
    """
    # Base rates by intensity
    intensity_rates = {
        1: 0.005,   # Light - 0.5%
        2: 0.01,    # Moderate - 1%
        3: 0.03,    # Intense - 3%
        4: 0.08,    # Extreme - 8%
    }
    
    base_prob = intensity_rates.get(intensity_value, 0.01)
    
    # Fatigue increases risk
    fatigue_modifier = current_fatigue / 500  # +20% at 100 fatigue
    
    return min(0.25, base_prob + fatigue_modifier)


# ============================================================================
# INJURY GENERATION
# ============================================================================

_injury_counter = 0

def generate_injury_id() -> str:
    """Generate a unique injury ID"""
    global _injury_counter
    _injury_counter += 1
    return f"inj_{_injury_counter:06d}"


def generate_injury(
    fighter_id: str,
    injury_type: InjuryType,
    location: Optional[InjuryLocation] = None,
    source: str = "fight",
    opponent_id: Optional[str] = None
) -> Injury:
    """
    Generate a new injury with appropriate details.
    
    Args:
        fighter_id: Who is injured
        injury_type: Severity
        location: Body part (random if not specified)
        source: How injury occurred
        opponent_id: Who caused it (if applicable)
    
    Returns:
        New Injury instance
    """
    # Pick location if not specified
    if location is None:
        available = list(INJURY_DESCRIPTIONS.get(injury_type, {}).keys())
        if not available:
            available = [InjuryLocation.RIBS]  # Fallback
        location = random.choice(available)
    
    # Get description
    descriptions = INJURY_DESCRIPTIONS.get(injury_type, {}).get(location, [])
    if descriptions:
        description = random.choice(descriptions)
    else:
        description = f"{injury_type.name.title()} {location.value.lower()} injury"
    
    # Calculate recovery time
    min_weeks, max_weeks = RECOVERY_TIMES[injury_type]
    recovery_weeks = random.randint(min_weeks, max_weeks)
    
    # Career injuries may have permanent effects
    permanent_effects = {}
    if injury_type == InjuryType.CAREER:
        # Random attribute penalty of 1-5 points
        if location == InjuryLocation.HEAD:
            permanent_effects["chin"] = -random.randint(2, 5)
        elif location == InjuryLocation.KNEE:
            permanent_effects["speed"] = -random.randint(1, 3)
        elif location == InjuryLocation.SHOULDER:
            permanent_effects["power"] = -random.randint(1, 3)
        elif location == InjuryLocation.BACK:
            permanent_effects["wrestling"] = -random.randint(1, 3)
    
    return Injury(
        injury_id=generate_injury_id(),
        fighter_id=fighter_id,
        injury_type=injury_type,
        location=location,
        description=description,
        sustained_date=calendar.current_date,
        recovery_weeks=recovery_weeks,
        source=source,
        opponent_id=opponent_id,
        permanent_effects=permanent_effects
    )


def generate_fight_injury(
    fighter_id: str,
    outcome: FightOutcome,
    is_loser: bool,
    opponent_id: Optional[str] = None
) -> Optional[Injury]:
    """
    Potentially generate an injury from a fight.
    
    Returns:
        Injury if one occurred, None otherwise
    """
    # Determine injury type based on weights
    weights = calculate_injury_severity_weights(outcome, is_loser)
    
    # Weighted random selection
    roll = random.random()
    cumulative = 0.0
    selected_type = InjuryType.MINOR
    
    for injury_type, weight in weights.items():
        cumulative += weight
        if roll <= cumulative:
            selected_type = injury_type
            break
    
    # Get likely location
    locations = get_likely_locations(outcome, selected_type)
    location = random.choice(locations) if locations else None
    
    return generate_injury(
        fighter_id=fighter_id,
        injury_type=selected_type,
        location=location,
        source="fight",
        opponent_id=opponent_id
    )


def generate_training_injury(fighter_id: str) -> Injury:
    """
    Generate a training injury (usually minor/moderate).
    """
    # Training injuries are usually less severe
    weights = {
        InjuryType.MINOR: 0.70,
        InjuryType.MODERATE: 0.25,
        InjuryType.SEVERE: 0.05,
        InjuryType.CAREER: 0.00,  # No career injuries from training
    }
    
    roll = random.random()
    cumulative = 0.0
    selected_type = InjuryType.MINOR
    
    for injury_type, weight in weights.items():
        cumulative += weight
        if roll <= cumulative:
            selected_type = injury_type
            break
    
    # Training injuries often affect limbs
    training_locations = [
        InjuryLocation.KNEE, InjuryLocation.ANKLE,
        InjuryLocation.SHOULDER, InjuryLocation.ELBOW,
        InjuryLocation.HAND, InjuryLocation.RIBS
    ]
    
    # Filter to valid locations for this injury type
    valid = [loc for loc in training_locations 
             if loc in INJURY_DESCRIPTIONS.get(selected_type, {})]
    location = random.choice(valid) if valid else random.choice(training_locations)
    
    return generate_injury(
        fighter_id=fighter_id,
        injury_type=selected_type,
        location=location,
        source="training"
    )


# ============================================================================
# INJURY SYSTEM CLASS
# ============================================================================

class InjurySystem:
    """
    Manages all fighter injuries across the game.
    
    Responsibilities:
    - Track active injuries
    - Process weekly healing
    - Check fight injury rolls
    - Emit injury/recovery events
    - Provide injury reports
    """
    
    def __init__(self):
        self._injuries: Dict[str, List[Injury]] = {}  # fighter_id -> injuries
        self._injury_history: Dict[str, List[Injury]] = {}  # Healed injuries
    
    def add_injury(self, injury: Injury) -> None:
        """
        Add a new injury for a fighter.
        
        Emits FIGHTER_INJURED event.
        """
        fighter_id = injury.fighter_id
        
        if fighter_id not in self._injuries:
            self._injuries[fighter_id] = []
        
        self._injuries[fighter_id].append(injury)
        
        emit(EventType.FIGHTER_INJURED, {
            "fighter_id": fighter_id,
            "injury_id": injury.injury_id,
            "injury_type": injury.injury_type.name,
            "location": injury.location.value,
            "description": injury.description,
            "recovery_weeks": injury.recovery_weeks
        })
    
    def get_injuries(self, fighter_id: str) -> List[Injury]:
        """Get all active injuries for a fighter"""
        return self._injuries.get(fighter_id, [])
    
    def get_injury_history(self, fighter_id: str) -> List[Injury]:
        """Get all past (healed) injuries for a fighter"""
        return self._injury_history.get(fighter_id, [])
    
    def has_injuries(self, fighter_id: str) -> bool:
        """Check if fighter has any active injuries"""
        return len(self.get_injuries(fighter_id)) > 0
    
    def is_cleared_to_fight(self, fighter_id: str) -> bool:
        """Check if fighter has medical clearance"""
        return not self.has_injuries(fighter_id)
    
    def get_recovery_time(self, fighter_id: str) -> int:
        """Get weeks until fighter is fully recovered"""
        injuries = self.get_injuries(fighter_id)
        if not injuries:
            return 0
        return max(inj.weeks_remaining for inj in injuries)
    
    def get_worst_injury(self, fighter_id: str) -> Optional[Injury]:
        """Get the most severe active injury"""
        injuries = self.get_injuries(fighter_id)
        if not injuries:
            return None
        
        # Sort by severity (CAREER > SEVERE > MODERATE > MINOR)
        severity_order = {
            InjuryType.CAREER: 4,
            InjuryType.SEVERE: 3,
            InjuryType.MODERATE: 2,
            InjuryType.MINOR: 1,
        }
        
        return max(injuries, key=lambda i: severity_order.get(i.injury_type, 0))
    
    def process_weekly_healing(self) -> Dict[str, List[str]]:
        """
        Process one week of healing for all injured fighters.
        
        Returns:
            Dict mapping fighter_id to list of healed injury descriptions
        """
        healed_this_week: Dict[str, List[str]] = {}
        
        for fighter_id in list(self._injuries.keys()):
            injuries = self._injuries[fighter_id]
            newly_healed = []
            still_injured = []
            
            for injury in injuries:
                was_healed = injury.is_healed
                injury.heal_week()
                
                if injury.is_healed and not was_healed:
                    newly_healed.append(injury)
                    
                    # Move to history
                    if fighter_id not in self._injury_history:
                        self._injury_history[fighter_id] = []
                    self._injury_history[fighter_id].append(injury)
                    
                    # Emit recovery event
                    emit(EventType.FIGHTER_RECOVERED, {
                        "fighter_id": fighter_id,
                        "injury_id": injury.injury_id,
                        "description": injury.description,
                        "permanent_effects": injury.permanent_effects
                    })
                elif not injury.is_healed:
                    still_injured.append(injury)
            
            # Update injuries list
            self._injuries[fighter_id] = still_injured
            
            # Clean up empty entries
            if not self._injuries[fighter_id]:
                del self._injuries[fighter_id]
            
            # Record healed injuries
            if newly_healed:
                healed_this_week[fighter_id] = [
                    inj.description for inj in newly_healed
                ]
        
        return healed_this_week
    
    def process_fight_injuries(
        self,
        fighter1_id: str,
        fighter2_id: str,
        outcome: FightOutcome,
        winner_id: str,
        rounds_fought: int
    ) -> Tuple[Optional[Injury], Optional[Injury]]:
        """
        Process potential injuries after a fight.
        
        Returns:
            Tuple of (fighter1_injury, fighter2_injury), either may be None
        """
        f1_is_loser = (fighter1_id != winner_id)
        f2_is_loser = (fighter2_id != winner_id)
        
        # Calculate injury probabilities
        f1_prob = calculate_fight_injury_probability(outcome, rounds_fought, f1_is_loser)
        f2_prob = calculate_fight_injury_probability(outcome, rounds_fought, f2_is_loser)
        
        f1_injury = None
        f2_injury = None
        
        # Roll for fighter 1
        if random.random() < f1_prob:
            f1_injury = generate_fight_injury(
                fighter1_id, outcome, f1_is_loser, fighter2_id
            )
            self.add_injury(f1_injury)
        
        # Roll for fighter 2
        if random.random() < f2_prob:
            f2_injury = generate_fight_injury(
                fighter2_id, outcome, f2_is_loser, fighter1_id
            )
            self.add_injury(f2_injury)
        
        return f1_injury, f2_injury
    
    def process_training_injury(
        self,
        fighter_id: str,
        intensity_value: int,
        current_fatigue: int
    ) -> Optional[Injury]:
        """
        Check for and potentially create a training injury.
        
        Returns:
            Injury if one occurred, None otherwise
        """
        prob = calculate_training_injury_probability(intensity_value, current_fatigue)
        
        if random.random() < prob:
            injury = generate_training_injury(fighter_id)
            self.add_injury(injury)
            return injury
        
        return None
    
    def get_injury_report(self, fighter_id: str) -> Dict[str, Any]:
        """
        Get a complete injury report for a fighter.
        """
        injuries = self.get_injuries(fighter_id)
        history = self.get_injury_history(fighter_id)
        
        return {
            "fighter_id": fighter_id,
            "is_injured": self.has_injuries(fighter_id),
            "cleared_to_fight": self.is_cleared_to_fight(fighter_id),
            "recovery_weeks": self.get_recovery_time(fighter_id),
            "active_injuries": [
                {
                    "description": inj.description,
                    "severity": inj.severity_name,
                    "weeks_remaining": inj.weeks_remaining,
                    "location": inj.location.value
                }
                for inj in injuries
            ],
            "total_injuries_career": len(history) + len(injuries),
            "severe_injuries_career": sum(
                1 for inj in history + injuries
                if inj.injury_type in (InjuryType.SEVERE, InjuryType.CAREER)
            )
        }
    
    def get_all_injured_fighters(self) -> List[str]:
        """Get list of all currently injured fighter IDs"""
        return list(self._injuries.keys())
    
    def clear_injuries(self, fighter_id: str) -> None:
        """
        Clear all injuries for a fighter (use with caution).
        Typically used for retirements or testing.
        """
        if fighter_id in self._injuries:
            # Move to history
            if fighter_id not in self._injury_history:
                self._injury_history[fighter_id] = []
            self._injury_history[fighter_id].extend(self._injuries[fighter_id])
            del self._injuries[fighter_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the injury system"""
        return {
            "injuries": {
                fighter_id: [inj.to_dict() for inj in injuries]
                for fighter_id, injuries in self._injuries.items()
            },
            "injury_history": {
                fighter_id: [inj.to_dict() for inj in injuries]
                for fighter_id, injuries in self._injury_history.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InjurySystem':
        """Deserialize the injury system"""
        system = cls()
        
        for fighter_id, injuries_data in data.get("injuries", {}).items():
            system._injuries[fighter_id] = [
                Injury.from_dict(inj) for inj in injuries_data
            ]
        
        for fighter_id, history_data in data.get("injury_history", {}).items():
            system._injury_history[fighter_id] = [
                Injury.from_dict(inj) for inj in history_data
            ]
        
        return system


# ============================================================================
# GLOBAL INJURY SYSTEM INSTANCE
# ============================================================================

injury_system = InjurySystem()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def is_fighter_injured(fighter_id: str) -> bool:
    """Check if a fighter is currently injured"""
    return injury_system.has_injuries(fighter_id)


def get_fighter_injuries(fighter_id: str) -> List[Injury]:
    """Get all active injuries for a fighter"""
    return injury_system.get_injuries(fighter_id)


def get_recovery_weeks(fighter_id: str) -> int:
    """Get weeks until fighter can fight again"""
    return injury_system.get_recovery_time(fighter_id)


def can_fight(fighter_id: str) -> bool:
    """Check if fighter is cleared to compete"""
    return injury_system.is_cleared_to_fight(fighter_id)
