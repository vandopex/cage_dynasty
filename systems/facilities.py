# systems/facilities.py
# Module: Facility Caps System
# Lines: ~650
#
# Defines training stat caps based on camp facility tier.
# Higher tier facilities allow training fighters to higher stat levels.

"""
Cage Dynasty - Facility Caps System

This module handles facility-based training limitations:
- Stat caps per facility tier
- Training cap enforcement
- Upgrade requirements and costs
- Roster limits per tier
- Monthly costs and efficiency bonuses

CONCEPT:
    A GARAGE gym can only train fighters to ~65 in any stat.
    To develop elite (90+) fighters, you need NATIONAL or ELITE facilities.
    This creates meaningful progression and strategic camp upgrades.

USAGE:
    from systems.facilities import (
        get_stat_cap,
        apply_facility_cap,
        can_sign_fighter,
        get_upgrade_cost,
        can_upgrade,
    )
    
    # Check stat cap for a tier
    cap = get_stat_cap("REGIONAL")  # Returns 80
    
    # Apply cap during training
    new_val, actual_gain, was_capped = apply_facility_cap(
        current_value=78, raw_gain=5, camp_tier="REGIONAL"
    )  # Returns (80, 2, True)
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CampStats:
    """Statistics about a camp used for upgrade requirements."""
    money: int = 0
    wins: int = 0
    title_wins: int = 0
    fighters_trained: int = 0
    reputation: int = 0
    weeks_at_tier: int = 0


# ============================================================================
# FACILITY TIER DEFINITIONS
# ============================================================================

class FacilityTier(Enum):
    """Camp facility tiers from lowest to highest."""
    GARAGE = "GARAGE"
    LOCAL = "LOCAL"
    REGIONAL = "REGIONAL"
    NATIONAL = "NATIONAL"
    ELITE = "ELITE"


# All valid tier strings
FACILITY_TIERS: List[str] = ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]


# Stat caps by facility tier
# These represent the maximum stat value achievable through training
FACILITY_STAT_CAPS: Dict[str, int] = {
    "GARAGE": 65,      # Basement/garage gym - can develop decent fighters
    "LOCAL": 72,       # Local gym - solid regional talent
    "REGIONAL": 80,    # Regional facility - competitive fighters
    "NATIONAL": 90,    # National-level gym - elite development
    "ELITE": 100,      # World-class facility - no limits
}


# Tier order for comparisons and upgrades
TIER_ORDER: List[str] = ["GARAGE", "LOCAL", "REGIONAL", "NATIONAL", "ELITE"]


# Maximum fighters per tier
MAX_FIGHTERS: Dict[str, int] = {
    "GARAGE": 3,       # Small operation
    "LOCAL": 5,        # Growing gym
    "REGIONAL": 8,     # Established camp
    "NATIONAL": 10,    # Major camp
    "ELITE": 12,       # Super camp (max 12)
}


# Upgrade costs (money required to upgrade TO this tier)
UPGRADE_COSTS: Dict[str, int] = {
    "GARAGE": 0,           # Starting tier
    "LOCAL": 25_000,       # $25k to upgrade from GARAGE
    "REGIONAL": 100_000,   # $100k to upgrade from LOCAL
    "NATIONAL": 500_000,   # $500k to upgrade from REGIONAL
    "ELITE": 2_000_000,    # $2M to upgrade from NATIONAL
}


# Monthly maintenance costs by tier (convert to weekly by dividing by 4)
MONTHLY_COSTS: Dict[str, int] = {
    "GARAGE": 2_000,       # $2k/month
    "LOCAL": 6_000,        # $6k/month
    "REGIONAL": 20_000,    # $20k/month
    "NATIONAL": 60_000,    # $60k/month
    "ELITE": 200_000,      # $200k/month
}


# Weekly maintenance costs by tier
MAINTENANCE_COSTS: Dict[str, int] = {
    "GARAGE": 500,         # $500/week
    "LOCAL": 1_500,        # $1,500/week
    "REGIONAL": 5_000,     # $5,000/week
    "NATIONAL": 15_000,    # $15,000/week
    "ELITE": 50_000,       # $50,000/week
}


# Training efficiency bonuses (multiplier on training gains)
TRAINING_EFFICIENCY: Dict[str, float] = {
    "GARAGE": 1.0,         # Baseline
    "LOCAL": 1.05,         # 5% bonus
    "REGIONAL": 1.10,      # 10% bonus
    "NATIONAL": 1.15,      # 15% bonus
    "ELITE": 1.25,         # 25% bonus
}


# Upgrade requirements beyond just money
UPGRADE_REQUIREMENTS: Dict[str, Dict[str, int]] = {
    "LOCAL": {
        "money": 25_000,
        "wins": 3,
    },
    "REGIONAL": {
        "money": 100_000,
        "wins": 10,
    },
    "NATIONAL": {
        "money": 500_000,
        "wins": 25,
        "title_wins": 1,
    },
    "ELITE": {
        "money": 2_000_000,
        "wins": 50,
        "title_wins": 3,
    },
}


# Stats affected by facility caps (all trainable stats)
CAPPED_STATS: List[str] = [
    # Physical
    "strength",
    "speed",
    "cardio",
    # Striking
    "boxing",
    "kicks",
    "clinch",
    "power",
    "accuracy",
    # Grappling
    "wrestling",
    "bjj",
    "takedown_defense",
    "top_control",
    "submissions",
    # Defense
    "striking_defense",
    "grappling_defense",
]

# Stats NOT affected by facility caps (innate attributes)
UNCAPPED_STATS: List[str] = [
    "chin",          # Natural toughness
    "recovery",      # Natural healing
    "heart",         # Natural determination
    "fight_iq",      # Can improve but not capped by facilities
    "composure",     # Mental attribute
]


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_stat_cap(camp_tier: str) -> int:
    """
    Get the maximum trainable stat value for a facility tier.
    
    Args:
        camp_tier: The facility tier (GARAGE, LOCAL, REGIONAL, NATIONAL, ELITE)
        
    Returns:
        Maximum stat value achievable through training
    """
    return FACILITY_STAT_CAPS.get(camp_tier.upper(), 65)


def get_tier_index(camp_tier: str) -> int:
    """Get the numeric index of a tier (0-4)."""
    try:
        return TIER_ORDER.index(camp_tier.upper())
    except ValueError:
        return 0


def get_next_tier(camp_tier: str) -> Optional[str]:
    """Get the next tier up from current tier, or None if already ELITE."""
    idx = get_tier_index(camp_tier)
    if idx < len(TIER_ORDER) - 1:
        return TIER_ORDER[idx + 1]
    return None


def is_stat_capped(stat_name: str) -> bool:
    """Check if a stat is subject to facility caps."""
    return stat_name.lower() in [s.lower() for s in CAPPED_STATS]


def can_improve_stat(
    stat_name: str,
    current_value: int,
    camp_tier: str,
) -> bool:
    """
    Check if a stat can be improved further at this facility tier.
    
    Args:
        stat_name: Name of the stat
        current_value: Current stat value
        camp_tier: Camp's facility tier
        
    Returns:
        True if stat can still be improved, False if at cap
    """
    # Uncapped stats can always improve (up to 100)
    if not is_stat_capped(stat_name):
        return current_value < 100
    
    cap = get_stat_cap(camp_tier)
    return current_value < cap


def get_effective_training_gain(
    current_value: int,
    raw_gain: int,
    camp_tier: str,
    stat_name: str = "",
) -> int:
    """
    Calculate effective training gain after applying facility cap.
    
    Args:
        current_value: Current stat value
        raw_gain: Raw training gain before cap
        camp_tier: Camp's facility tier
        stat_name: Name of the stat (optional, for cap checking)
        
    Returns:
        Effective gain after applying cap (may be 0 if at cap)
    """
    if raw_gain <= 0:
        return 0
    
    # Get the cap for this tier
    cap = get_stat_cap(camp_tier)
    
    # If stat is uncapped, use 100 as the ceiling
    if stat_name and not is_stat_capped(stat_name):
        cap = 100
    
    # Calculate maximum possible value
    max_value = min(cap, 100)
    
    # If already at or above cap, no gain
    if current_value >= max_value:
        return 0
    
    # Calculate effective gain (don't exceed cap)
    new_value = current_value + raw_gain
    if new_value > max_value:
        return max_value - current_value
    
    return raw_gain


def apply_facility_cap(
    current_value: int,
    raw_gain: int,
    camp_tier: str,
    stat_name: str = "",
) -> Tuple[int, int, bool]:
    """
    Apply facility cap to training gain, returning new value and details.
    
    Args:
        current_value: Current stat value
        raw_gain: Raw training gain before cap
        camp_tier: Camp's facility tier
        stat_name: Name of the stat (optional)
        
    Returns:
        Tuple of (new_value, actual_gain, was_capped)
    """
    effective_gain = get_effective_training_gain(
        current_value, raw_gain, camp_tier, stat_name
    )
    new_value = current_value + effective_gain
    was_capped = effective_gain < raw_gain
    
    return new_value, effective_gain, was_capped


def calculate_training_gain(
    base_gain: int,
    camp_tier: str,
    current_value: int = 50,
    stat_name: str = "",
) -> Tuple[int, int, bool]:
    """
    Calculate training gain with efficiency bonus and cap.
    
    Args:
        base_gain: Base training gain
        camp_tier: Camp's facility tier
        current_value: Current stat value
        stat_name: Name of the stat
        
    Returns:
        Tuple of (new_value, actual_gain, was_capped)
    """
    # Apply efficiency bonus
    efficiency = get_training_efficiency(camp_tier)
    raw_gain = int(base_gain * efficiency)
    
    return apply_facility_cap(current_value, raw_gain, camp_tier, stat_name)


def apply_training_with_caps(
    stats: Dict[str, int],
    gains: Dict[str, int],
    camp_tier: str,
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Apply training gains to stats, respecting facility caps.
    
    Args:
        stats: Current stat values
        gains: Raw training gains
        camp_tier: Camp's facility tier
        
    Returns:
        Tuple of (new_stats, actual_gains) where actual_gains shows
        what was actually applied after caps
    """
    new_stats = dict(stats)
    actual_gains = {}
    
    for stat_name, raw_gain in gains.items():
        current = stats.get(stat_name, 50)
        effective = get_effective_training_gain(
            current_value=current,
            raw_gain=raw_gain,
            camp_tier=camp_tier,
            stat_name=stat_name,
        )
        
        new_stats[stat_name] = current + effective
        actual_gains[stat_name] = effective
    
    return new_stats, actual_gains


def get_capped_stats(
    stats: Dict[str, int],
    camp_tier: str,
) -> List[str]:
    """
    Get list of stats that are currently at their facility cap.
    
    Args:
        stats: Current stat values
        camp_tier: Camp's facility tier
        
    Returns:
        List of stat names that are at or above their cap
    """
    cap = get_stat_cap(camp_tier)
    capped = []
    
    for stat_name in CAPPED_STATS:
        if stat_name in stats and stats[stat_name] >= cap:
            capped.append(stat_name)
    
    return capped


def get_stats_near_cap(
    stats: Dict[str, int],
    camp_tier: str,
    threshold: int = 3,
) -> List[Tuple[str, int, int]]:
    """
    Get stats that are approaching their facility cap.
    
    Args:
        stats: Current stat values
        camp_tier: Camp's facility tier
        threshold: How close to cap to be considered "near"
        
    Returns:
        List of (stat_name, current_value, cap) tuples
    """
    cap = get_stat_cap(camp_tier)
    near_cap = []
    
    for stat_name in CAPPED_STATS:
        if stat_name in stats:
            current = stats[stat_name]
            if current >= cap - threshold and current < cap:
                near_cap.append((stat_name, current, cap))
    
    return near_cap


# ============================================================================
# ROSTER FUNCTIONS
# ============================================================================

def get_max_fighters(camp_tier: str) -> int:
    """Get maximum fighters allowed for a facility tier."""
    return MAX_FIGHTERS.get(camp_tier.upper(), 3)


def can_sign_fighter(camp_tier: str, current_count: int) -> Tuple[bool, str]:
    """
    Check if camp can sign another fighter.
    
    Args:
        camp_tier: Camp's facility tier
        current_count: Current number of fighters
        
    Returns:
        Tuple of (can_sign, reason_if_not)
    """
    max_f = get_max_fighters(camp_tier)
    if current_count >= max_f:
        return False, f"Roster full ({current_count}/{max_f}). Upgrade facilities to sign more."
    return True, ""


def get_roster_status(camp_tier: str, current_count: int) -> str:
    """Get formatted roster status string."""
    max_f = get_max_fighters(camp_tier)
    return f"{current_count}/{max_f}"


# ============================================================================
# UPGRADE FUNCTIONS
# ============================================================================

def get_upgrade_cost(current_tier: str) -> Optional[int]:
    """
    Get cost to upgrade from current tier to next tier.
    
    Args:
        current_tier: Current facility tier
        
    Returns:
        Cost in dollars, or None if already at ELITE
    """
    next_tier = get_next_tier(current_tier)
    if next_tier is None:
        return None
    return UPGRADE_COSTS.get(next_tier, 0)


def get_upgrade_requirements(current_tier: str) -> Optional[Dict[str, int]]:
    """
    Get all requirements to upgrade from current tier.
    
    Args:
        current_tier: Current facility tier
        
    Returns:
        Dict of requirement_name -> value, or None if at ELITE
    """
    next_tier = get_next_tier(current_tier)
    if next_tier is None:
        return None
    return UPGRADE_REQUIREMENTS.get(next_tier, {})


def can_upgrade(current_tier: str, camp_stats: CampStats) -> Tuple[bool, List[str]]:
    """
    Check if camp meets all upgrade requirements.
    
    Args:
        current_tier: Current facility tier
        camp_stats: Current camp statistics
        
    Returns:
        Tuple of (can_upgrade, list_of_missing_requirements)
    """
    requirements = get_upgrade_requirements(current_tier)
    if requirements is None:
        return False, ["Already at maximum tier"]
    
    missing = []
    
    if camp_stats.money < requirements.get("money", 0):
        missing.append(f"Need ${requirements['money']:,} (have ${camp_stats.money:,})")
    
    if camp_stats.wins < requirements.get("wins", 0):
        missing.append(f"Need {requirements['wins']} wins (have {camp_stats.wins})")
    
    if camp_stats.title_wins < requirements.get("title_wins", 0):
        missing.append(f"Need {requirements['title_wins']} title wins (have {camp_stats.title_wins})")
    
    return len(missing) == 0, missing


def perform_upgrade(current_tier: str, camp_stats: CampStats) -> Tuple[bool, str, int]:
    """
    Attempt to perform facility upgrade.
    
    Args:
        current_tier: Current facility tier
        camp_stats: Current camp statistics
        
    Returns:
        Tuple of (success, result_message, cost_deducted)
    """
    can_up, missing = can_upgrade(current_tier, camp_stats)
    
    if not can_up:
        return False, f"Cannot upgrade: {', '.join(missing)}", 0
    
    next_tier = get_next_tier(current_tier)
    cost = get_upgrade_cost(current_tier)
    
    return True, f"Upgraded to {get_tier_display_name(next_tier)}!", cost


def can_afford_upgrade(current_tier: str, available_funds: int) -> bool:
    """Check if upgrade to next tier is affordable."""
    cost = get_upgrade_cost(current_tier)
    if cost is None:
        return False
    return available_funds >= cost


def get_monthly_cost(camp_tier: str) -> int:
    """Get monthly maintenance cost for a facility tier."""
    return MONTHLY_COSTS.get(camp_tier.upper(), 2000)


def get_maintenance_cost(camp_tier: str) -> int:
    """Get weekly maintenance cost for a facility tier."""
    return MAINTENANCE_COSTS.get(camp_tier.upper(), 500)


def get_training_efficiency(camp_tier: str) -> float:
    """Get training efficiency multiplier for a facility tier."""
    return TRAINING_EFFICIENCY.get(camp_tier.upper(), 1.0)


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def get_tier_display_name(camp_tier: str) -> str:
    """Get display-friendly tier name."""
    names = {
        "GARAGE": "Garage Gym",
        "LOCAL": "Local Gym",
        "REGIONAL": "Regional Facility",
        "NATIONAL": "National Center",
        "ELITE": "Elite Complex",
    }
    return names.get(camp_tier.upper(), camp_tier)


def get_tier_description(camp_tier: str) -> str:
    """Get description of what a facility tier offers."""
    descriptions = {
        "GARAGE": "Basic equipment, limited space. Good for starting out.",
        "LOCAL": "Decent equipment, proper mats. Trains solid local talent.",
        "REGIONAL": "Full equipment, dedicated training areas. Competitive fighters.",
        "NATIONAL": "Top-tier equipment, sports science. Elite development.",
        "ELITE": "World-class everything. No limits on potential.",
    }
    return descriptions.get(camp_tier.upper(), "")


def get_facility_description(camp_tier: str) -> str:
    """Alias for get_tier_description."""
    return get_tier_description(camp_tier)


def format_cap_warning(stat_name: str, current: int, cap: int) -> str:
    """Format a warning message about approaching cap."""
    if current >= cap:
        return f"{stat_name} is MAXED at {cap} (facility limit)"
    else:
        remaining = cap - current
        return f"{stat_name} is {remaining} points from facility cap ({cap})"


def format_upgrade_requirements(current_tier: str) -> str:
    """Format upgrade requirements as a readable string."""
    reqs = get_upgrade_requirements(current_tier)
    if reqs is None:
        return "Maximum tier reached"
    
    parts = []
    if "money" in reqs:
        parts.append(f"${reqs['money']:,}")
    if "wins" in reqs:
        parts.append(f"{reqs['wins']} wins")
    if "title_wins" in reqs:
        parts.append(f"{reqs['title_wins']} title wins")
    
    return ", ".join(parts)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "CampStats",
    
    # Constants
    "FACILITY_TIERS",
    "FACILITY_STAT_CAPS",
    "TIER_ORDER",
    "MAX_FIGHTERS",
    "UPGRADE_COSTS",
    "MONTHLY_COSTS",
    "MAINTENANCE_COSTS",
    "TRAINING_EFFICIENCY",
    "UPGRADE_REQUIREMENTS",
    "CAPPED_STATS",
    "UNCAPPED_STATS",
    
    # Core functions
    "get_stat_cap",
    "get_tier_index",
    "get_next_tier",
    "is_stat_capped",
    "can_improve_stat",
    "get_effective_training_gain",
    "apply_facility_cap",
    "calculate_training_gain",
    "apply_training_with_caps",
    "get_capped_stats",
    "get_stats_near_cap",
    
    # Roster functions
    "get_max_fighters",
    "can_sign_fighter",
    "get_roster_status",
    
    # Upgrade functions
    "get_upgrade_cost",
    "get_upgrade_requirements",
    "can_upgrade",
    "perform_upgrade",
    "can_afford_upgrade",
    "get_monthly_cost",
    "get_maintenance_cost",
    "get_training_efficiency",
    
    # Display helpers
    "get_tier_display_name",
    "get_tier_description",
    "get_facility_description",
    "format_cap_warning",
    "format_upgrade_requirements",
]
