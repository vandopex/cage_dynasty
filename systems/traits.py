# systems/traits.py
# Module: Fighter Traits System
# Lines: ~650
#
# Handles fighter traits - special abilities that modify stats and fight behavior.
# Each trait provides unique bonuses/penalties that create diverse fighter archetypes.

"""
Cage Dynasty - Fighter Traits System

This module manages the 18 fighter traits that create unique archetypes:

PHYSICAL TRAITS:
    - Glass Cannon: High power, weak chin
    - Iron Chin: Absorbs damage, slightly slower
    - Cardio Machine: Superior stamina, less power
    - Durable: Injury resistant
    - Injury Prone: Gets hurt more often

STRIKING TRAITS:
    - Knockout Artist: Increased KO probability
    - Southpaw: Stance advantage vs orthodox fighters

GRAPPLING TRAITS:
    - Submission Ace: Increased submission probability
    - Wrestler's Base: Superior takedown defense

MENTAL TRAITS:
    - Pressure Fighter: Bonus vs counter strikers
    - Counter Striker: Bonus vs pressure fighters
    - Fast Starter: Strong early, fades late
    - Slow Starter: Weak early, strong late
    - Big Game Hunter: Thrives in title fights
    - Choke Artist: Struggles in title fights
    - Veteran Savvy: Experience advantage
    - Killer Instinct: Finishes hurt opponents

TRAINING TRAITS:
    - Gym Rat: Faster skill development

USAGE:
    from systems.traits import (
        FIGHTER_TRAITS,
        assign_traits,
        get_stat_modifiers,
        get_trait_fight_modifiers,
    )
    
    # Assign traits to a new fighter
    traits = assign_traits(fighter_attributes)
    
    # Get stat modifiers from traits
    mods = get_stat_modifiers(traits)
    
    # Get fight modifiers
    fight_mods = get_trait_fight_modifiers(traits, is_title_fight=True)
"""

from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
import random


# ============================================================================
# CONSTANTS
# ============================================================================

# Complete trait definitions
FIGHTER_TRAITS: Dict[str, Dict[str, Any]] = {
    # === PHYSICAL TRAITS ===
    "Glass Cannon": {
        "category": "Physical",
        "description": "Devastating power but vulnerable to damage",
        "flavor": "Hits like a truck, but can't take a punch",
        "stat_mods": {"strength": 15, "chin": -15},
        "win_bonus": 0.02,
        "ko_mod": 0.15,
        "get_kod_mod": 0.15,
        "conflicts": ["Iron Chin", "Durable"],
    },
    "Iron Chin": {
        "category": "Physical",
        "description": "Absorbs punishment that would drop others",
        "flavor": "Can walk through fire",
        "stat_mods": {"chin": 15, "speed": -5},
        "win_bonus": 0.01,
        "ko_mod": 0.0,
        "get_kod_mod": -0.20,
        "conflicts": ["Glass Cannon"],
    },
    "Cardio Machine": {
        "category": "Physical",
        "description": "Endless gas tank, maintains pace throughout",
        "flavor": "Could go five rounds at championship pace",
        "stat_mods": {"cardio": 15, "strength": -5},
        "win_bonus": 0.01,
        "late_round_bonus": 0.10,
        "conflicts": [],
    },
    "Durable": {
        "category": "Physical",
        "description": "Rarely gets injured, iron body",
        "flavor": "Built to last",
        "stat_mods": {},
        "win_bonus": 0.0,
        "injury_mod": -0.30,
        "conflicts": ["Injury Prone", "Glass Cannon"],
    },
    "Injury Prone": {
        "category": "Physical",
        "description": "Body breaks down frequently",
        "flavor": "Made of glass",
        "stat_mods": {},
        "win_bonus": -0.01,
        "injury_mod": 0.50,
        "conflicts": ["Durable"],
    },
    
    # === STRIKING TRAITS ===
    "Knockout Artist": {
        "category": "Striking",
        "description": "Terrifying one-punch knockout power",
        "flavor": "Touch of death in both hands",
        "stat_mods": {},
        "win_bonus": 0.02,
        "ko_mod": 0.10,
        "conflicts": [],
    },
    "Southpaw": {
        "category": "Striking",
        "description": "Unorthodox stance creates angles and confusion",
        "flavor": "The angles are all wrong for orthodox fighters",
        "stat_mods": {"boxing": 3, "striking_defense": 2},
        "win_bonus": 0.01,
        "vs_orthodox_bonus": 0.05,
        "vs_southpaw_penalty": -0.03,
        "conflicts": [],
    },
    
    # === GRAPPLING TRAITS ===
    "Submission Ace": {
        "category": "Grappling",
        "description": "Dangerous submission threat from any position",
        "flavor": "Arms and necks aren't safe",
        "stat_mods": {"bjj": 5},
        "win_bonus": 0.02,
        "sub_mod": 0.10,
        "conflicts": [],
    },
    "Wrestler's Base": {
        "category": "Grappling",
        "description": "Nearly impossible to take down",
        "flavor": "Roots planted like an oak tree",
        "stat_mods": {"takedown_defense": 10},
        "win_bonus": 0.01,
        "conflicts": [],
    },
    
    # === MENTAL TRAITS ===
    "Pressure Fighter": {
        "category": "Mental",
        "description": "Relentless forward pressure, smothers opponents",
        "flavor": "Constantly in your face",
        "stat_mods": {},
        "win_bonus": 0.01,
        "vs_counter_bonus": 0.05,
        "vs_pressure_penalty": -0.02,
        "conflicts": ["Counter Striker"],
    },
    "Counter Striker": {
        "category": "Mental",
        "description": "Times opponents perfectly, makes them pay",
        "flavor": "You swing, you pay",
        "stat_mods": {},
        "win_bonus": 0.01,
        "vs_pressure_bonus": 0.05,
        "vs_counter_penalty": -0.02,
        "conflicts": ["Pressure Fighter"],
    },
    "Fast Starter": {
        "category": "Mental",
        "description": "Explodes out of the gate, dangerous early",
        "flavor": "Comes out guns blazing",
        "stat_mods": {},
        "win_bonus": 0.01,
        "round1_bonus": 0.10,
        "late_round_penalty": -0.05,
        "conflicts": ["Slow Starter"],
    },
    "Slow Starter": {
        "category": "Mental",
        "description": "Takes time to find rhythm, dangerous late",
        "flavor": "Championship rounds are where they shine",
        "stat_mods": {},
        "win_bonus": 0.01,
        "round1_penalty": -0.05,
        "late_round_bonus": 0.10,
        "conflicts": ["Fast Starter"],
    },
    "Big Game Hunter": {
        "category": "Mental",
        "description": "Rises to the occasion in big fights",
        "flavor": "Lives for the bright lights",
        "stat_mods": {},
        "win_bonus": 0.0,
        "title_fight_bonus": 0.10,
        "conflicts": ["Choke Artist"],
    },
    "Choke Artist": {
        "category": "Mental",
        "description": "Struggles under championship pressure",
        "flavor": "Can't handle the moment",
        "stat_mods": {},
        "win_bonus": 0.0,
        "title_fight_penalty": -0.15,
        "conflicts": ["Big Game Hunter"],
    },
    "Veteran Savvy": {
        "category": "Mental",
        "description": "Experience provides edge in close fights",
        "flavor": "Seen it all before",
        "stat_mods": {"fight_iq": 5, "composure": 5},
        "win_bonus": 0.01,
        "decision_bonus": 0.05,
        "conflicts": [],
    },
    "Killer Instinct": {
        "category": "Mental",
        "description": "Smells blood and finishes hurt opponents",
        "flavor": "When they're hurt, they're done",
        "stat_mods": {},
        "win_bonus": 0.02,
        "finish_rate_mod": 0.25,  # +25% chance to finish when opponent is rocked
        "vs_rocked_accuracy": 0.15,  # Bonus accuracy when opponent is compromised
        "conflicts": [],
    },
    
    # === TRAINING TRAITS ===
    "Gym Rat": {
        "category": "Training",
        "description": "First in, last out - absorbs training like a sponge",
        "flavor": "Lives in the gym",
        "stat_mods": {},
        "win_bonus": 0.0,
        "training_mod": 0.20,
        "conflicts": [],
    },
}

# Trait categories for organization
TRAIT_CATEGORIES = {
    "Physical": ["Glass Cannon", "Iron Chin", "Cardio Machine", "Durable", "Injury Prone"],
    "Striking": ["Knockout Artist", "Southpaw"],
    "Grappling": ["Submission Ace", "Wrestler's Base"],
    "Mental": ["Pressure Fighter", "Counter Striker", "Fast Starter", "Slow Starter", 
               "Big Game Hunter", "Choke Artist", "Veteran Savvy", "Killer Instinct"],
    "Training": ["Gym Rat"],
}

# Conflicting traits that can't coexist
CONFLICTING_TRAITS: List[Tuple[str, str]] = [
    ("Glass Cannon", "Iron Chin"),
    ("Glass Cannon", "Durable"),
    ("Durable", "Injury Prone"),
    ("Pressure Fighter", "Counter Striker"),
    ("Fast Starter", "Slow Starter"),
    ("Big Game Hunter", "Choke Artist"),
]

# Attribute thresholds for trait assignment
TRAIT_ATTRIBUTE_TRIGGERS = {
    "Iron Chin": {"chin": 80},
    "Glass Cannon": {"strength": 80, "chin_max": 55},
    "Cardio Machine": {"cardio": 80},
    "Knockout Artist": {"strength": 75, "boxing": 70},
    "Submission Ace": {"bjj": 80},
    "Wrestler's Base": {"wrestling": 75, "takedown_defense": 75},
    "Veteran Savvy": {"fight_iq": 80, "composure": 75},
}

# Weights for random trait assignment
TRAIT_RARITY = {
    # Common traits (higher weight)
    "Iron Chin": 15,
    "Cardio Machine": 15,
    "Fast Starter": 12,
    "Slow Starter": 12,
    "Pressure Fighter": 12,
    "Counter Striker": 12,
    "Durable": 10,
    
    # Uncommon traits
    "Knockout Artist": 8,
    "Submission Ace": 8,
    "Wrestler's Base": 8,
    "Veteran Savvy": 8,
    "Gym Rat": 8,
    "Southpaw": 8,  # ~10% of population is left-handed
    
    # Rare traits
    "Glass Cannon": 6,
    "Big Game Hunter": 6,
    "Killer Instinct": 5,
    
    # Negative traits (less common)
    "Injury Prone": 5,
    "Choke Artist": 4,
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TraitModifiers:
    """Collection of all modifiers from a fighter's traits."""
    # Core rating adjustment (sum of applicable bonuses as a rating modifier)
    rating_adjustment: float = 0.0
    
    # Win/loss modifiers
    win_bonus: float = 0.0
    
    # Finish chance modifiers (for determining fight outcome method)
    ko_mod: float = 0.0              # Internal tracking
    ko_chance_mod: float = 0.0       # Used by CLI for KO probability
    sub_mod: float = 0.0             # Internal tracking
    sub_chance_mod: float = 0.0      # Used by CLI for SUB probability
    dec_chance_mod: float = 0.0      # Decision probability modifier
    
    # Getting finished modifiers
    get_kod_mod: float = 0.0
    get_subbed_mod: float = 0.0
    get_finished_mod: float = 0.0    # General "gets finished" modifier
    
    # Round-specific modifiers
    round1_bonus: float = 0.0
    late_round_bonus: float = 0.0
    early_finish_bonus: float = 0.0  # Bonus for finishing early (Fast Starter)
    late_finish_bonus: float = 0.0   # Bonus for finishing late (Slow Starter)
    
    # Fight type modifiers
    title_fight_bonus: float = 0.0
    decision_bonus: float = 0.0
    
    # Other modifiers
    injury_mod: float = 0.0
    training_mod: float = 0.0
    finish_rate_mod: float = 0.0
    vs_rocked_accuracy: float = 0.0
    
    # Stance modifiers
    vs_orthodox_bonus: float = 0.0
    vs_southpaw_penalty: float = 0.0
    
    # Style interaction modifiers
    vs_counter_bonus: float = 0.0
    vs_pressure_bonus: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "rating_adjustment": self.rating_adjustment,
            "win_bonus": self.win_bonus,
            "ko_chance_mod": self.ko_chance_mod,
            "sub_chance_mod": self.sub_chance_mod,
            "dec_chance_mod": self.dec_chance_mod,
            "get_kod_mod": self.get_kod_mod,
            "get_finished_mod": self.get_finished_mod,
            "round1_bonus": self.round1_bonus,
            "late_round_bonus": self.late_round_bonus,
            "early_finish_bonus": self.early_finish_bonus,
            "late_finish_bonus": self.late_finish_bonus,
            "title_fight_bonus": self.title_fight_bonus,
            "decision_bonus": self.decision_bonus,
            "injury_mod": self.injury_mod,
            "training_mod": self.training_mod,
            "finish_rate_mod": self.finish_rate_mod,
            "vs_rocked_accuracy": self.vs_rocked_accuracy,
        }


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def has_trait(traits: List[str], trait_name: str) -> bool:
    """Check if fighter has a specific trait."""
    if not traits:
        return False
    return trait_name in traits


def get_trait_description(trait_name: str) -> str:
    """Get the description of a trait."""
    trait = FIGHTER_TRAITS.get(trait_name, {})
    return trait.get("description", "Unknown trait")


def get_trait_flavor(trait_name: str) -> str:
    """Get the flavor text of a trait."""
    trait = FIGHTER_TRAITS.get(trait_name, {})
    return trait.get("flavor", "")


def get_trait_category(trait_name: str) -> str:
    """Get the category of a trait."""
    trait = FIGHTER_TRAITS.get(trait_name, {})
    return trait.get("category", "Unknown")


def get_stat_modifiers(traits: List[str]) -> Dict[str, int]:
    """
    Get combined stat modifiers from all traits.
    
    Args:
        traits: List of trait names
        
    Returns:
        Dictionary of stat modifications
    """
    combined = {}
    
    if not traits:
        return combined
    
    for trait_name in traits:
        trait = FIGHTER_TRAITS.get(trait_name, {})
        stat_mods = trait.get("stat_mods", {})
        
        for stat, mod in stat_mods.items():
            combined[stat] = combined.get(stat, 0) + mod
    
    return combined


def apply_stat_modifiers(
    base_stats: Dict[str, int],
    traits: List[str]
) -> Dict[str, int]:
    """
    Apply trait modifiers to base stats.
    
    Args:
        base_stats: Original fighter stats
        traits: List of trait names
        
    Returns:
        Modified stats dictionary
    """
    modified = base_stats.copy()
    modifiers = get_stat_modifiers(traits)
    
    for stat, mod in modifiers.items():
        if stat in modified:
            modified[stat] = max(1, min(99, modified[stat] + mod))
    
    return modified


def get_trait_fight_modifiers(
    traits: List[str],
    is_title_fight: bool = False,
    is_main_event: bool = False,
    current_round: int = 1,
    total_rounds: int = 3,
    opponent_rocked: bool = False,
    opponent_southpaw: bool = False,
) -> TraitModifiers:
    """
    Get all fight-relevant modifiers from traits.
    
    Args:
        traits: List of trait names
        is_title_fight: Whether this is a title fight
        is_main_event: Whether this is a main event
        current_round: Current round number
        total_rounds: Total scheduled rounds
        opponent_rocked: Whether opponent is in rocked state
        opponent_southpaw: Whether opponent is a southpaw
        
    Returns:
        TraitModifiers with all applicable bonuses
    """
    mods = TraitModifiers()
    
    if not traits:
        return mods
    
    for trait_name in traits:
        trait = FIGHTER_TRAITS.get(trait_name, {})
        
        # Base win bonus
        mods.win_bonus += trait.get("win_bonus", 0.0)
        
        # KO/Sub modifiers - populate both internal and CLI-facing attributes
        ko_bonus = trait.get("ko_mod", 0.0)
        mods.ko_mod += ko_bonus
        mods.ko_chance_mod += ko_bonus
        
        sub_bonus = trait.get("sub_mod", 0.0)
        mods.sub_mod += sub_bonus
        mods.sub_chance_mod += sub_bonus
        
        # Getting finished modifiers
        mods.get_kod_mod += trait.get("get_kod_mod", 0.0)
        mods.get_subbed_mod += trait.get("get_subbed_mod", 0.0)
        mods.get_finished_mod += trait.get("get_finished_mod", 0.0)
        
        # Injury modifier
        mods.injury_mod += trait.get("injury_mod", 0.0)
        
        # Training modifier
        mods.training_mod += trait.get("training_mod", 0.0)
        
        # Round-specific modifiers
        if current_round == 1:
            round1_bonus = trait.get("round1_bonus", 0.0) + trait.get("round1_penalty", 0.0)
            mods.round1_bonus += round1_bonus
            # Fast Starter gets early finish bonus
            if trait_name == "Fast Starter":
                mods.early_finish_bonus += 0.10
        
        if current_round >= total_rounds - 1:  # Late rounds
            late_bonus = trait.get("late_round_bonus", 0.0) + trait.get("late_round_penalty", 0.0)
            mods.late_round_bonus += late_bonus
            # Slow Starter gets late finish bonus
            if trait_name == "Slow Starter":
                mods.late_finish_bonus += 0.10
        
        # Title fight modifiers
        if is_title_fight:
            mods.title_fight_bonus += trait.get("title_fight_bonus", 0.0)
            mods.title_fight_bonus += trait.get("title_fight_penalty", 0.0)
        
        # Decision bonus
        dec_bonus = trait.get("decision_bonus", 0.0)
        mods.decision_bonus += dec_bonus
        mods.dec_chance_mod += dec_bonus
        
        # Killer Instinct - bonus when opponent is hurt
        if opponent_rocked:
            mods.finish_rate_mod += trait.get("finish_rate_mod", 0.0)
            mods.vs_rocked_accuracy += trait.get("vs_rocked_accuracy", 0.0)
        
        # Southpaw interactions
        if trait_name == "Southpaw":
            if opponent_southpaw:
                mods.win_bonus += trait.get("vs_southpaw_penalty", 0.0)
            else:
                mods.win_bonus += trait.get("vs_orthodox_bonus", 0.0)
    
    # Calculate rating_adjustment from applicable bonuses
    # Convert percentage bonuses to rating points (e.g., 5% = 5 rating points)
    # This provides a unified adjustment for simple fight simulations
    mods.rating_adjustment = (
        (mods.win_bonus * 100) +           # win_bonus is 0.01-0.05, convert to 1-5 points
        (mods.round1_bonus * 50) +         # round bonus is 0.05-0.15, convert to 2.5-7.5 points
        (mods.late_round_bonus * 50) +     # late round bonus
        (mods.title_fight_bonus * 50) +    # title fight bonus
        (mods.ko_mod * 30) +               # KO mod contributes to rating
        (mods.sub_mod * 30)                # Sub mod contributes to rating
    )
    
    return mods


def get_pressure_counter_interaction(
    traits1: List[str],
    traits2: List[str]
) -> Tuple[float, float]:
    """
    Calculate Pressure Fighter vs Counter Striker interaction.
    
    Args:
        traits1: Fighter 1's traits
        traits2: Fighter 2's traits
        
    Returns:
        Tuple of (fighter1_mod, fighter2_mod)
    """
    f1_mod = 0.0
    f2_mod = 0.0
    
    f1_pressure = has_trait(traits1, "Pressure Fighter")
    f1_counter = has_trait(traits1, "Counter Striker")
    f2_pressure = has_trait(traits2, "Pressure Fighter")
    f2_counter = has_trait(traits2, "Counter Striker")
    
    # Pressure vs Counter interactions
    if f1_pressure and f2_counter:
        # Counter striker has advantage vs pressure
        f2_mod += 0.05
    elif f1_counter and f2_pressure:
        # Counter striker has advantage vs pressure
        f1_mod += 0.05
    
    # Same style matchups are neutral/slight negative
    if f1_pressure and f2_pressure:
        # Both pressure = coin flip, slight penalty
        f1_mod -= 0.02
        f2_mod -= 0.02
    elif f1_counter and f2_counter:
        # Both counter = waiting game, slight penalty
        f1_mod -= 0.02
        f2_mod -= 0.02
    
    return f1_mod, f2_mod


def get_trait_win_bonus(traits: List[str]) -> float:
    """Get total win probability bonus from traits."""
    if not traits:
        return 0.0
    
    total = 0.0
    for trait_name in traits:
        trait = FIGHTER_TRAITS.get(trait_name, {})
        total += trait.get("win_bonus", 0.0)
    
    return total


def get_training_multiplier(traits: List[str]) -> float:
    """Get training gains multiplier from traits."""
    if not traits:
        return 1.0
    
    multiplier = 1.0
    for trait_name in traits:
        trait = FIGHTER_TRAITS.get(trait_name, {})
        multiplier += trait.get("training_mod", 0.0)
    
    return multiplier


def get_injury_multiplier(traits: List[str]) -> float:
    """Get injury chance multiplier from traits."""
    if not traits:
        return 1.0
    
    multiplier = 1.0
    for trait_name in traits:
        trait = FIGHTER_TRAITS.get(trait_name, {})
        multiplier += trait.get("injury_mod", 0.0)
    
    return max(0.1, multiplier)  # Minimum 10% of base injury chance


def get_camp_bonus(traits: List[str]) -> float:
    """Get training camp bonus from traits (for Gym Rat etc)."""
    return get_training_multiplier(traits) - 1.0


# ============================================================================
# TRAIT ASSIGNMENT
# ============================================================================

def _check_conflicts(existing: List[str], new_trait: str) -> bool:
    """Check if new trait conflicts with existing traits."""
    new_conflicts = FIGHTER_TRAITS.get(new_trait, {}).get("conflicts", [])
    
    for existing_trait in existing:
        # Check if new trait conflicts with existing
        if existing_trait in new_conflicts:
            return True
        
        # Check if existing trait conflicts with new
        existing_conflicts = FIGHTER_TRAITS.get(existing_trait, {}).get("conflicts", [])
        if new_trait in existing_conflicts:
            return True
    
    return False


def assign_traits(
    attributes: Dict[str, Any],
    num_traits: Optional[int] = None,
    forced_traits: Optional[List[str]] = None,
) -> List[str]:
    """
    Assign appropriate traits based on fighter attributes.
    
    Args:
        attributes: Fighter's attributes dictionary
        num_traits: Force specific number of traits (random 0-3 if None)
        forced_traits: Traits to include regardless of other logic
        
    Returns:
        List of assigned trait names
    """
    selected: List[str] = []
    
    # Add forced traits first
    if forced_traits:
        for trait in forced_traits:
            if trait in FIGHTER_TRAITS and trait not in selected:
                selected.append(trait)
    
    # Determine number of traits
    if num_traits is None:
        num_traits = random.choices([0, 1, 2, 3], weights=[0.15, 0.40, 0.35, 0.10], k=1)[0]
    
    remaining = num_traits - len(selected)
    if remaining <= 0:
        return selected[:num_traits]
    
    # Check for attribute-triggered traits first
    for trait_name, triggers in TRAIT_ATTRIBUTE_TRIGGERS.items():
        if trait_name in selected:
            continue
        if _check_conflicts(selected, trait_name):
            continue
        
        matches = True
        for attr, threshold in triggers.items():
            if attr.endswith("_max"):
                # Maximum threshold (must be below)
                real_attr = attr[:-4]
                if attributes.get(real_attr, 50) > threshold:
                    matches = False
                    break
            else:
                # Minimum threshold
                if attributes.get(attr, 50) < threshold:
                    matches = False
                    break
        
        if matches and random.random() < 0.4:  # 40% chance to get triggered trait
            selected.append(trait_name)
            remaining -= 1
            if remaining <= 0:
                return selected
    
    # Fill remaining with weighted random selection
    available = [t for t in FIGHTER_TRAITS.keys() 
                 if t not in selected and not _check_conflicts(selected, t)]
    
    if available and remaining > 0:
        weights = [TRAIT_RARITY.get(t, 5) for t in available]
        
        for _ in range(remaining):
            if not available:
                break
            
            chosen = random.choices(available, weights=weights, k=1)[0]
            selected.append(chosen)
            
            # Remove chosen and conflicting traits from pool
            idx = available.index(chosen)
            available.pop(idx)
            weights.pop(idx)
            
            # Also remove any traits that now conflict
            conflicts = FIGHTER_TRAITS.get(chosen, {}).get("conflicts", [])
            for conflict in conflicts:
                if conflict in available:
                    c_idx = available.index(conflict)
                    available.pop(c_idx)
                    weights.pop(c_idx)
    
    return selected


def get_all_trait_names() -> List[str]:
    """Get list of all trait names."""
    return list(FIGHTER_TRAITS.keys())


def get_traits_by_category(category: str) -> List[str]:
    """Get all traits in a category."""
    return TRAIT_CATEGORIES.get(category, [])


# ============================================================================
# TRAIT DISPLAY HELPERS
# ============================================================================

def format_trait_for_display(trait_name: str) -> str:
    """Format a trait for UI display with description."""
    trait = FIGHTER_TRAITS.get(trait_name, {})
    desc = trait.get("description", "")
    return f"{trait_name}: {desc}"


def get_trait_summary(traits: List[str]) -> Dict[str, Any]:
    """
    Get a summary of trait effects for display.
    
    Returns dict with positive effects, negative effects, and net impact.
    """
    positives = []
    negatives = []
    
    stat_mods = get_stat_modifiers(traits)
    
    for stat, mod in stat_mods.items():
        if mod > 0:
            positives.append(f"+{mod} {stat.replace('_', ' ').title()}")
        elif mod < 0:
            negatives.append(f"{mod} {stat.replace('_', ' ').title()}")
    
    # Check for special bonuses
    for trait_name in traits:
        trait = FIGHTER_TRAITS.get(trait_name, {})
        
        if trait.get("ko_mod", 0) > 0:
            positives.append(f"+{int(trait['ko_mod']*100)}% KO chance")
        if trait.get("sub_mod", 0) > 0:
            positives.append(f"+{int(trait['sub_mod']*100)}% Sub chance")
        if trait.get("title_fight_bonus", 0) > 0:
            positives.append(f"+{int(trait['title_fight_bonus']*100)}% in title fights")
        if trait.get("title_fight_penalty", 0) < 0:
            negatives.append(f"{int(trait['title_fight_penalty']*100)}% in title fights")
        if trait.get("training_mod", 0) > 0:
            positives.append(f"+{int(trait['training_mod']*100)}% training gains")
        if trait.get("finish_rate_mod", 0) > 0:
            positives.append(f"+{int(trait['finish_rate_mod']*100)}% finish rate vs hurt opponents")
        if trait.get("vs_orthodox_bonus", 0) > 0:
            positives.append(f"+{int(trait['vs_orthodox_bonus']*100)}% vs orthodox fighters")
    
    return {
        "positives": positives,
        "negatives": negatives,
        "net_win_bonus": get_trait_win_bonus(traits),
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "FIGHTER_TRAITS",
    "TRAIT_CATEGORIES", 
    "CONFLICTING_TRAITS",
    "TraitModifiers",
    "has_trait",
    "get_trait_description",
    "get_trait_flavor",
    "get_trait_category",
    "get_stat_modifiers",
    "apply_stat_modifiers",
    "get_trait_fight_modifiers",
    "get_pressure_counter_interaction",
    "get_trait_win_bonus",
    "get_training_multiplier",
    "get_injury_multiplier",
    "get_camp_bonus",
    "assign_traits",
    "get_all_trait_names",
    "get_traits_by_category",
    "format_trait_for_display",
    "get_trait_summary",
]

# Alias for backward compatibility
FightModifiers = TraitModifiers

# Alias for backward compatibility
get_injury_modifier = get_injury_multiplier

# Alias for backward compatibility
def get_trait_info(trait_name: str) -> Dict[str, Any]:
    """Get full info for a trait."""
    return FIGHTER_TRAITS.get(trait_name, {})
