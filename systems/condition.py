# systems/condition.py
# Module: Fighter Condition & Readiness System
# Lines: ~180
#
# Tracks fighter fatigue and its effects on fight performance.
# Provides readiness display and stamina penalties.

"""
Cage Dynasty - Fighter Condition System

This module handles the connection between training fatigue and fight performance:
- Fatigue accumulated during training camps
- Starting stamina penalty based on fatigue level
- Fight readiness ratings for player feedback
- Display helpers for condition status

FATIGUE EFFECTS:
================
Fatigue (0-100) reduces starting stamina in fights:
- 0-20:  Fresh - No penalty (★★★★★)
- 21-40: Rested - Minor penalty (★★★★☆)  
- 41-60: Ready - Moderate penalty (★★★☆☆)
- 61-80: Tired - Significant penalty (★★☆☆☆)
- 81-100: Exhausted - Severe penalty (★☆☆☆☆)

This creates meaningful decisions:
- Train hard = better skills, but start fights gassed
- Rest before fights = peak performance
- Manage intensity throughout camp

USAGE:
    from systems.condition import (
        get_starting_stamina,
        get_fight_readiness,
        format_readiness_display,
    )
    
    # Before a fight
    stamina = get_starting_stamina(fighter.fatigue)  # e.g., 85.0
    
    # Display to player
    print(format_readiness_display(fighter.fatigue))
    # "★★★★☆ Well Rested (Fatigue: 25)"
"""

from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# CONSTANTS
# ============================================================================

# Fatigue thresholds and their effects
FATIGUE_THRESHOLDS = {
    "FRESH": (0, 20),       # No penalty
    "RESTED": (21, 40),     # Minor penalty
    "READY": (41, 60),      # Moderate penalty
    "TIRED": (61, 80),      # Significant penalty
    "EXHAUSTED": (81, 100), # Severe penalty
}

# Starting stamina penalty by fatigue level
# These are subtracted from 100 starting stamina
STAMINA_PENALTIES = {
    "FRESH": 0,       # Start at 100
    "RESTED": 5,      # Start at 95
    "READY": 12,      # Start at 88
    "TIRED": 22,      # Start at 78
    "EXHAUSTED": 35,  # Start at 65
}

# Readiness ratings
READINESS_RATINGS = {
    "FRESH": ("Peak Condition", 5),
    "RESTED": ("Well Rested", 4),
    "READY": ("Fight Ready", 3),
    "TIRED": ("Fatigued", 2),
    "EXHAUSTED": ("Exhausted", 1),
}

# Additional cardio penalty per round (recovery is slower when exhausted)
CARDIO_RECOVERY_PENALTY = {
    "FRESH": 0,
    "RESTED": 0,
    "READY": 1,
    "TIRED": 2,
    "EXHAUSTED": 4,
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FighterCondition:
    """Complete condition status for a fighter."""
    fatigue: int
    fatigue_category: str
    readiness_text: str
    readiness_stars: int
    starting_stamina: float
    stamina_penalty: int
    cardio_recovery_penalty: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fatigue": self.fatigue,
            "fatigue_category": self.fatigue_category,
            "readiness_text": self.readiness_text,
            "readiness_stars": self.readiness_stars,
            "starting_stamina": self.starting_stamina,
            "stamina_penalty": self.stamina_penalty,
            "cardio_recovery_penalty": self.cardio_recovery_penalty,
        }


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_fatigue_category(fatigue: int) -> str:
    """
    Get the fatigue category for a fatigue level.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        Category string: FRESH, RESTED, READY, TIRED, or EXHAUSTED
    """
    fatigue = max(0, min(100, fatigue))
    
    for category, (low, high) in FATIGUE_THRESHOLDS.items():
        if low <= fatigue <= high:
            return category
    
    return "EXHAUSTED"


def get_starting_stamina(fatigue: int) -> float:
    """
    Calculate starting stamina for a fight based on fatigue.
    
    A fresh fighter starts at 100 stamina.
    A fatigued fighter starts lower, simulating entering the fight
    already somewhat gassed from hard training.
    
    Args:
        fatigue: Fighter's current fatigue (0-100)
        
    Returns:
        Starting stamina value (65-100)
    """
    category = get_fatigue_category(fatigue)
    penalty = STAMINA_PENALTIES.get(category, 0)
    return 100.0 - penalty


def get_stamina_penalty(fatigue: int) -> int:
    """
    Get the raw stamina penalty for a fatigue level.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        Stamina penalty points (0-35)
    """
    category = get_fatigue_category(fatigue)
    return STAMINA_PENALTIES.get(category, 0)


def get_cardio_recovery_penalty(fatigue: int) -> int:
    """
    Get the between-round cardio recovery penalty.
    
    Fatigued fighters recover less stamina between rounds.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        Recovery penalty per round (0-4)
    """
    category = get_fatigue_category(fatigue)
    return CARDIO_RECOVERY_PENALTY.get(category, 0)


def get_fight_readiness(fatigue: int) -> Tuple[str, int]:
    """
    Get readiness rating text and stars.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        Tuple of (readiness_text, stars_out_of_5)
    """
    category = get_fatigue_category(fatigue)
    return READINESS_RATINGS.get(category, ("Unknown", 0))


def get_fighter_condition(fatigue: int) -> FighterCondition:
    """
    Get complete condition status for a fighter.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        FighterCondition with all status info
    """
    category = get_fatigue_category(fatigue)
    text, stars = get_fight_readiness(fatigue)
    
    return FighterCondition(
        fatigue=fatigue,
        fatigue_category=category,
        readiness_text=text,
        readiness_stars=stars,
        starting_stamina=get_starting_stamina(fatigue),
        stamina_penalty=get_stamina_penalty(fatigue),
        cardio_recovery_penalty=get_cardio_recovery_penalty(fatigue),
    )


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_readiness_display(fatigue: int, show_fatigue: bool = True) -> str:
    """
    Format readiness for display to player.
    
    Args:
        fatigue: Fatigue level (0-100)
        show_fatigue: Whether to include raw fatigue number
        
    Returns:
        Formatted string like "★★★★☆ Well Rested (Fatigue: 25)"
    """
    text, stars = get_fight_readiness(fatigue)
    star_display = "★" * stars + "☆" * (5 - stars)
    
    if show_fatigue:
        return f"{star_display} {text} (Fatigue: {fatigue})"
    return f"{star_display} {text}"


def format_readiness_short(fatigue: int) -> str:
    """
    Short format for tight displays.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        Short string like "★★★★☆"
    """
    _, stars = get_fight_readiness(fatigue)
    return "★" * stars + "☆" * (5 - stars)


def format_condition_details(fatigue: int) -> str:
    """
    Detailed condition breakdown for player info.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        Multi-line detailed condition report
    """
    condition = get_fighter_condition(fatigue)
    
    lines = [
        f"Condition: {condition.readiness_text}",
        f"Readiness: {format_readiness_short(fatigue)}",
        f"Fatigue: {fatigue}/100",
    ]
    
    if condition.stamina_penalty > 0:
        lines.append(f"Starting Stamina: {condition.starting_stamina:.0f}% (-{condition.stamina_penalty})")
    else:
        lines.append(f"Starting Stamina: 100% (No penalty)")
    
    if condition.cardio_recovery_penalty > 0:
        lines.append(f"Recovery Penalty: -{condition.cardio_recovery_penalty} per round")
    
    return "\n".join(lines)


def get_condition_warning(fatigue: int) -> Optional[str]:
    """
    Get a warning message if fighter is in poor condition.
    
    Args:
        fatigue: Fatigue level (0-100)
        
    Returns:
        Warning string or None if condition is acceptable
    """
    category = get_fatigue_category(fatigue)
    
    if category == "TIRED":
        return "⚠️ Fighter is fatigued - consider rest before fight"
    elif category == "EXHAUSTED":
        return "🚨 Fighter is exhausted - will start fight severely gassed!"
    
    return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "FighterCondition",
    
    # Core functions
    "get_fatigue_category",
    "get_starting_stamina",
    "get_stamina_penalty",
    "get_cardio_recovery_penalty",
    "get_fight_readiness",
    "get_fighter_condition",
    
    # Display helpers
    "format_readiness_display",
    "format_readiness_short",
    "format_condition_details",
    "get_condition_warning",
    
    # Constants
    "FATIGUE_THRESHOLDS",
    "STAMINA_PENALTIES",
    "READINESS_RATINGS",
    "CARDIO_RECOVERY_PENALTY",
]
