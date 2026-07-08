# systems/styles.py
# Module: Fighting Styles System
# Lines: ~950
#
# The complete 11-style fighting system for Cage Dynasty.
# Defines styles, matchups, country influences, and camp specializations.

"""
Cage Dynasty - Fighting Styles System

This module defines the complete fighting style system:
- 11 distinct fighting styles (5 stand-up, 4 grappling, 2 hybrid)
- Style matchup modifiers (rock-paper-scissors dynamics)
- Country/region style influences
- Camp style specializations
- Style-based attribute bonuses
- Finish rate distributions by style

USAGE:
    from systems.styles import (
        get_style_matchup_modifier,
        generate_style_for_fighter,
        get_style_definition,
        STYLE_DEFINITIONS,
    )
    
    # Get matchup modifier
    mod = get_style_matchup_modifier(FightingStyle.WRESTLER, FightingStyle.STRIKER)
    # Returns +0.04 (Wrestler advantage vs Striker)
    
    # Generate style for fighter
    style = generate_style_for_fighter(country="Brazil", camp_styles=None)
    # Likely returns BJJ_SPECIALIST or MUAY_THAI

IMPORT RULES:
- This module imports only from core.types
- Other modules import style utilities from here
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from core.types import FightingStyle


# ============================================================================
# STYLE DEFINITION DATACLASS
# ============================================================================

@dataclass(frozen=True)
class StyleDefinition:
    """Complete definition of a fighting style"""
    name: FightingStyle
    display_name: str
    description: str
    examples: List[str]  # Real UFC fighters as examples
    
    # Attribute requirements (minimums to naturally develop this style)
    attribute_requirements: Dict[str, int]
    
    # Attribute bonuses when generating fighter with this style
    attribute_bonuses: Dict[str, int]
    
    # Finish rate distribution (must sum to 1.0)
    ko_rate: float      # KO/TKO rate
    sub_rate: float     # Submission rate
    dec_rate: float     # Decision rate
    
    # Generation weight (how common this style is globally)
    generation_weight: float
    
    # Special traits commonly associated with this style
    special_traits: List[str] = field(default_factory=list)


# ============================================================================
# STYLE DEFINITIONS - All 11 Styles
# ============================================================================

STYLE_DEFINITIONS: Dict[FightingStyle, StyleDefinition] = {
    FightingStyle.STRIKER: StyleDefinition(
        name=FightingStyle.STRIKER,
        display_name="Striker",
        description="Traditional boxing/kickboxing specialist looking for the knockout",
        examples=["Israel Adesanya", "Conor McGregor", "Alex Pereira"],
        attribute_requirements={"boxing": 70, "kicks": 60},
        attribute_bonuses={"boxing": 8, "kicks": 5, "striking_defense": 3, "wrestling": -5},
        ko_rate=0.45, sub_rate=0.05, dec_rate=0.50,
        generation_weight=1.0,
        special_traits=["Knockout Artist", "Fast Starter"]
    ),
    FightingStyle.COUNTER_STRIKER: StyleDefinition(
        name=FightingStyle.COUNTER_STRIKER,
        display_name="Counter Striker",
        description="Reactive timing master who waits and counters",
        examples=["Anderson Silva", "Lyoto Machida", "Stephen Thompson"],
        attribute_requirements={"boxing": 65, "striking_defense": 70, "composure": 70},
        attribute_bonuses={"striking_defense": 8, "composure": 5, "fight_iq": 5, "speed": 3},
        ko_rate=0.35, sub_rate=0.05, dec_rate=0.60,
        generation_weight=0.7,
        special_traits=["Counter Puncher", "Iron Chin"]
    ),
    FightingStyle.PRESSURE_FIGHTER: StyleDefinition(
        name=FightingStyle.PRESSURE_FIGHTER,
        display_name="Pressure Fighter",
        description="Relentless forward movement that breaks opponents",
        examples=["Justin Gaethje", "Max Holloway", "Tony Ferguson"],
        attribute_requirements={"cardio": 75, "chin": 70, "heart": 75},
        attribute_bonuses={"cardio": 8, "heart": 6, "chin": 4, "composure": -3},
        ko_rate=0.40, sub_rate=0.10, dec_rate=0.50,
        generation_weight=0.9,
        special_traits=["Iron Chin", "Cardio Machine"]
    ),
    FightingStyle.POINT_FIGHTER: StyleDefinition(
        name=FightingStyle.POINT_FIGHTER,
        display_name="Point Fighter",
        description="Movement and evasion specialist who wins decisions",
        examples=["Dominick Cruz", "TJ Dillashaw", "Sean O'Malley"],
        attribute_requirements={"speed": 75, "striking_defense": 70, "fight_iq": 70},
        attribute_bonuses={"speed": 8, "striking_defense": 5, "fight_iq": 5, "strength": -5},
        ko_rate=0.20, sub_rate=0.05, dec_rate=0.75,
        generation_weight=0.6,
        special_traits=["Elusive", "Fast Starter"]
    ),
    FightingStyle.MUAY_THAI: StyleDefinition(
        name=FightingStyle.MUAY_THAI,
        display_name="Muay Thai",
        description="Kicks, knees, elbows, and Thai clinch mastery",
        examples=["Jose Aldo", "Valentina Shevchenko", "Petr Yan"],
        attribute_requirements={"kicks": 70, "clinch_striking": 70},
        attribute_bonuses={"kicks": 8, "clinch_striking": 8, "boxing": 3, "wrestling": -4, "takedown_defense": 6},
        ko_rate=0.40, sub_rate=0.05, dec_rate=0.55,
        generation_weight=0.85,
        special_traits=["Knockout Artist", "Body Snatcher"]
    ),
    FightingStyle.WRESTLER: StyleDefinition(
        name=FightingStyle.WRESTLER,
        display_name="Wrestler",
        description="Control-focused fighter who grinds out decisions",
        examples=["Khabib Nurmagomedov", "Kamaru Usman", "Belal Muhammad"],
        attribute_requirements={"wrestling": 80, "takedown_defense": 70},
        attribute_bonuses={"wrestling": 10, "takedown_defense": 5, "cardio": 3, "boxing": -5},
        ko_rate=0.15, sub_rate=0.20, dec_rate=0.65,
        generation_weight=1.1,
        special_traits=["Takedown Artist", "Cardio Machine"]
    ),
    FightingStyle.GROUND_AND_POUND: StyleDefinition(
        name=FightingStyle.GROUND_AND_POUND,
        display_name="Ground & Pound",
        description="Takes opponents down and smashes them for TKO",
        examples=["Khabib Nurmagomedov", "Charles Oliveira", "Islam Makhachev"],
        attribute_requirements={"wrestling": 70, "strength": 70},
        attribute_bonuses={"wrestling": 6, "strength": 6, "bjj": 4, "kicks": -4},
        ko_rate=0.45, sub_rate=0.20, dec_rate=0.35,
        generation_weight=0.9,
        special_traits=["Knockout Artist", "Takedown Artist"]
    ),
    FightingStyle.BJJ_SPECIALIST: StyleDefinition(
        name=FightingStyle.BJJ_SPECIALIST,
        display_name="BJJ Specialist",
        description="Submission hunter who is dangerous from anywhere",
        examples=["Charles Oliveira", "Demian Maia", "Ryan Hall"],
        attribute_requirements={"bjj": 80, "wrestling": 60},
        attribute_bonuses={"bjj": 10, "wrestling": 4, "composure": 3, "boxing": -5, "kicks": -3},
        ko_rate=0.10, sub_rate=0.55, dec_rate=0.35,
        generation_weight=0.85,
        special_traits=["Choke Artist", "Submission Specialist"]
    ),
    FightingStyle.CLINCH_FIGHTER: StyleDefinition(
        name=FightingStyle.CLINCH_FIGHTER,
        display_name="Clinch Fighter",
        description="Dirty boxing, cage grinding, and smothering",
        examples=["Randy Couture", "Colby Covington", "Merab Dvalishvili"],
        attribute_requirements={"clinch_striking": 70, "wrestling": 65, "cardio": 70},
        attribute_bonuses={"clinch_striking": 8, "wrestling": 5, "cardio": 5, "kicks": -5},
        ko_rate=0.25, sub_rate=0.15, dec_rate=0.60,
        generation_weight=0.7,
        special_traits=["Cardio Machine", "Iron Chin"]
    ),
    FightingStyle.SPRAWL_AND_BRAWL: StyleDefinition(
        name=FightingStyle.SPRAWL_AND_BRAWL,
        display_name="Sprawl & Brawl",
        description="Anti-wrestler striker who refuses to go down",
        examples=["Chuck Liddell", "Mirko Cro Cop", "Jiri Prochazka"],
        attribute_requirements={"takedown_defense": 75, "boxing": 70},
        attribute_bonuses={"takedown_defense": 8, "boxing": 5, "kicks": 4, "chin": 3, "bjj": -5},
        ko_rate=0.50, sub_rate=0.05, dec_rate=0.45,
        generation_weight=0.75,
        special_traits=["Knockout Artist", "Big Game Hunter"]
    ),
    FightingStyle.BALANCED: StyleDefinition(
        name=FightingStyle.BALANCED,
        display_name="Balanced",
        description="Complete MMA fighter with no weaknesses",
        examples=["Georges St-Pierre", "Jon Jones", "Alexander Volkanovski"],
        attribute_requirements={},
        attribute_bonuses={"fight_iq": 5, "composure": 5},
        ko_rate=0.30, sub_rate=0.20, dec_rate=0.50,
        generation_weight=1.0,
        special_traits=["Big Game Hunter", "Durable"]
    ),
}


# ============================================================================
# STYLE MATCHUP MATRIX
# ============================================================================

STYLE_MATCHUPS: Dict[FightingStyle, Dict[FightingStyle, float]] = {
    FightingStyle.STRIKER: {
        FightingStyle.STRIKER: 0.0, FightingStyle.COUNTER_STRIKER: -0.03,
        FightingStyle.PRESSURE_FIGHTER: 0.02, FightingStyle.POINT_FIGHTER: -0.02,
        FightingStyle.MUAY_THAI: 0.0, FightingStyle.WRESTLER: -0.04,
        FightingStyle.GROUND_AND_POUND: -0.03, FightingStyle.BJJ_SPECIALIST: 0.03,
        FightingStyle.CLINCH_FIGHTER: -0.02, FightingStyle.SPRAWL_AND_BRAWL: 0.0,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.COUNTER_STRIKER: {
        FightingStyle.STRIKER: 0.03, FightingStyle.COUNTER_STRIKER: 0.0,
        FightingStyle.PRESSURE_FIGHTER: -0.04, FightingStyle.POINT_FIGHTER: 0.02,
        FightingStyle.MUAY_THAI: 0.01, FightingStyle.WRESTLER: -0.03,
        FightingStyle.GROUND_AND_POUND: -0.02, FightingStyle.BJJ_SPECIALIST: 0.02,
        FightingStyle.CLINCH_FIGHTER: -0.02, FightingStyle.SPRAWL_AND_BRAWL: -0.03,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.PRESSURE_FIGHTER: {
        FightingStyle.STRIKER: -0.02, FightingStyle.COUNTER_STRIKER: 0.04,
        FightingStyle.PRESSURE_FIGHTER: 0.0, FightingStyle.POINT_FIGHTER: 0.03,
        FightingStyle.MUAY_THAI: 0.0, FightingStyle.WRESTLER: -0.02,
        FightingStyle.GROUND_AND_POUND: -0.02, FightingStyle.BJJ_SPECIALIST: -0.01,
        FightingStyle.CLINCH_FIGHTER: 0.02, FightingStyle.SPRAWL_AND_BRAWL: 0.0,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.POINT_FIGHTER: {
        FightingStyle.STRIKER: 0.02, FightingStyle.COUNTER_STRIKER: -0.02,
        FightingStyle.PRESSURE_FIGHTER: -0.03, FightingStyle.POINT_FIGHTER: 0.0,
        FightingStyle.MUAY_THAI: 0.01, FightingStyle.WRESTLER: -0.04,
        FightingStyle.GROUND_AND_POUND: -0.04, FightingStyle.BJJ_SPECIALIST: 0.02,
        FightingStyle.CLINCH_FIGHTER: -0.02, FightingStyle.SPRAWL_AND_BRAWL: 0.01,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.MUAY_THAI: {
        FightingStyle.STRIKER: 0.0, FightingStyle.COUNTER_STRIKER: -0.01,
        FightingStyle.PRESSURE_FIGHTER: 0.0, FightingStyle.POINT_FIGHTER: -0.01,
        FightingStyle.MUAY_THAI: 0.0, FightingStyle.WRESTLER: -0.03,
        FightingStyle.GROUND_AND_POUND: -0.02, FightingStyle.BJJ_SPECIALIST: 0.02,
        FightingStyle.CLINCH_FIGHTER: 0.03, FightingStyle.SPRAWL_AND_BRAWL: 0.0,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.WRESTLER: {
        FightingStyle.STRIKER: 0.04, FightingStyle.COUNTER_STRIKER: 0.03,
        FightingStyle.PRESSURE_FIGHTER: 0.02, FightingStyle.POINT_FIGHTER: 0.04,
        FightingStyle.MUAY_THAI: 0.03, FightingStyle.WRESTLER: 0.0,
        FightingStyle.GROUND_AND_POUND: -0.01, FightingStyle.BJJ_SPECIALIST: -0.03,
        FightingStyle.CLINCH_FIGHTER: 0.01, FightingStyle.SPRAWL_AND_BRAWL: -0.04,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.GROUND_AND_POUND: {
        FightingStyle.STRIKER: 0.03, FightingStyle.COUNTER_STRIKER: 0.02,
        FightingStyle.PRESSURE_FIGHTER: 0.02, FightingStyle.POINT_FIGHTER: 0.04,
        FightingStyle.MUAY_THAI: 0.02, FightingStyle.WRESTLER: 0.01,
        FightingStyle.GROUND_AND_POUND: 0.0, FightingStyle.BJJ_SPECIALIST: -0.03,
        FightingStyle.CLINCH_FIGHTER: 0.01, FightingStyle.SPRAWL_AND_BRAWL: -0.05,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.BJJ_SPECIALIST: {
        FightingStyle.STRIKER: -0.03, FightingStyle.COUNTER_STRIKER: -0.02,
        FightingStyle.PRESSURE_FIGHTER: 0.01, FightingStyle.POINT_FIGHTER: -0.02,
        FightingStyle.MUAY_THAI: -0.02, FightingStyle.WRESTLER: 0.03,
        FightingStyle.GROUND_AND_POUND: 0.03, FightingStyle.BJJ_SPECIALIST: 0.0,
        FightingStyle.CLINCH_FIGHTER: 0.02, FightingStyle.SPRAWL_AND_BRAWL: -0.03,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.CLINCH_FIGHTER: {
        FightingStyle.STRIKER: 0.02, FightingStyle.COUNTER_STRIKER: 0.02,
        FightingStyle.PRESSURE_FIGHTER: -0.02, FightingStyle.POINT_FIGHTER: 0.02,
        FightingStyle.MUAY_THAI: -0.03, FightingStyle.WRESTLER: -0.01,
        FightingStyle.GROUND_AND_POUND: -0.01, FightingStyle.BJJ_SPECIALIST: -0.02,
        FightingStyle.CLINCH_FIGHTER: 0.0, FightingStyle.SPRAWL_AND_BRAWL: -0.01,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.SPRAWL_AND_BRAWL: {
        FightingStyle.STRIKER: 0.0, FightingStyle.COUNTER_STRIKER: 0.03,
        FightingStyle.PRESSURE_FIGHTER: 0.0, FightingStyle.POINT_FIGHTER: -0.01,
        FightingStyle.MUAY_THAI: 0.0, FightingStyle.WRESTLER: 0.04,
        FightingStyle.GROUND_AND_POUND: 0.05, FightingStyle.BJJ_SPECIALIST: 0.03,
        FightingStyle.CLINCH_FIGHTER: 0.01, FightingStyle.SPRAWL_AND_BRAWL: 0.0,
        FightingStyle.BALANCED: 0.0,
    },
    FightingStyle.BALANCED: {
        FightingStyle.STRIKER: 0.0, FightingStyle.COUNTER_STRIKER: 0.0,
        FightingStyle.PRESSURE_FIGHTER: 0.0, FightingStyle.POINT_FIGHTER: 0.0,
        FightingStyle.MUAY_THAI: 0.0, FightingStyle.WRESTLER: 0.0,
        FightingStyle.GROUND_AND_POUND: 0.0, FightingStyle.BJJ_SPECIALIST: 0.0,
        FightingStyle.CLINCH_FIGHTER: 0.0, FightingStyle.SPRAWL_AND_BRAWL: 0.0,
        FightingStyle.BALANCED: 0.0,
    },
}


# ============================================================================
# COUNTRY STYLE WEIGHTS
# ============================================================================

COUNTRY_STYLE_WEIGHTS: Dict[str, Dict[FightingStyle, float]] = {
    "Russia": {
        FightingStyle.WRESTLER: 35, FightingStyle.GROUND_AND_POUND: 25,
        FightingStyle.BJJ_SPECIALIST: 10, FightingStyle.STRIKER: 10,
        FightingStyle.PRESSURE_FIGHTER: 10, FightingStyle.BALANCED: 10,
    },
    "United States": {
        FightingStyle.WRESTLER: 25, FightingStyle.SPRAWL_AND_BRAWL: 15,
        FightingStyle.STRIKER: 15, FightingStyle.BALANCED: 15,
        FightingStyle.GROUND_AND_POUND: 10, FightingStyle.PRESSURE_FIGHTER: 10,
        FightingStyle.BJJ_SPECIALIST: 5, FightingStyle.POINT_FIGHTER: 5,
    },
    "Brazil": {
        FightingStyle.BJJ_SPECIALIST: 30, FightingStyle.MUAY_THAI: 20,
        FightingStyle.STRIKER: 15, FightingStyle.BALANCED: 15,
        FightingStyle.PRESSURE_FIGHTER: 10, FightingStyle.GROUND_AND_POUND: 10,
    },
    "Thailand": {
        FightingStyle.MUAY_THAI: 60, FightingStyle.CLINCH_FIGHTER: 15,
        FightingStyle.STRIKER: 10, FightingStyle.BALANCED: 10,
        FightingStyle.PRESSURE_FIGHTER: 5,
    },
    "Netherlands": {
        FightingStyle.STRIKER: 35, FightingStyle.MUAY_THAI: 25,
        FightingStyle.PRESSURE_FIGHTER: 15, FightingStyle.BALANCED: 15,
        FightingStyle.SPRAWL_AND_BRAWL: 10,
    },
    "Ireland": {
        FightingStyle.STRIKER: 35, FightingStyle.COUNTER_STRIKER: 20,
        FightingStyle.PRESSURE_FIGHTER: 15, FightingStyle.BALANCED: 15,
        FightingStyle.SPRAWL_AND_BRAWL: 15,
    },
    "Mexico": {
        FightingStyle.STRIKER: 35, FightingStyle.PRESSURE_FIGHTER: 25,
        FightingStyle.BALANCED: 15, FightingStyle.COUNTER_STRIKER: 10,
        FightingStyle.BJJ_SPECIALIST: 10, FightingStyle.SPRAWL_AND_BRAWL: 5,
    },
    "Japan": {
        FightingStyle.BJJ_SPECIALIST: 25, FightingStyle.BALANCED: 20,
        FightingStyle.STRIKER: 20, FightingStyle.WRESTLER: 15,
        FightingStyle.POINT_FIGHTER: 10, FightingStyle.COUNTER_STRIKER: 10,
    },
    "United Kingdom": {
        FightingStyle.STRIKER: 30, FightingStyle.BALANCED: 20,
        FightingStyle.PRESSURE_FIGHTER: 15, FightingStyle.WRESTLER: 15,
        FightingStyle.BJJ_SPECIALIST: 10, FightingStyle.SPRAWL_AND_BRAWL: 10,
    },
    "Canada": {
        FightingStyle.WRESTLER: 25, FightingStyle.BALANCED: 20,
        FightingStyle.STRIKER: 20, FightingStyle.BJJ_SPECIALIST: 15,
        FightingStyle.PRESSURE_FIGHTER: 10, FightingStyle.SPRAWL_AND_BRAWL: 10,
    },
    "Australia": {
        FightingStyle.STRIKER: 25, FightingStyle.BALANCED: 20,
        FightingStyle.WRESTLER: 15, FightingStyle.BJJ_SPECIALIST: 15,
        FightingStyle.SPRAWL_AND_BRAWL: 15, FightingStyle.PRESSURE_FIGHTER: 10,
    },
}

DEFAULT_STYLE_WEIGHTS: Dict[FightingStyle, float] = {
    FightingStyle.STRIKER: 15, FightingStyle.COUNTER_STRIKER: 8,
    FightingStyle.PRESSURE_FIGHTER: 12, FightingStyle.POINT_FIGHTER: 6,
    FightingStyle.MUAY_THAI: 10, FightingStyle.WRESTLER: 15,
    FightingStyle.GROUND_AND_POUND: 10, FightingStyle.BJJ_SPECIALIST: 10,
    FightingStyle.CLINCH_FIGHTER: 6, FightingStyle.SPRAWL_AND_BRAWL: 8,
    FightingStyle.BALANCED: 10,
}

CAMP_STYLE_PRESETS: Dict[str, List[FightingStyle]] = {
    "Wrestling Academy": [FightingStyle.WRESTLER, FightingStyle.GROUND_AND_POUND],
    "BJJ Gym": [FightingStyle.BJJ_SPECIALIST, FightingStyle.BALANCED],
    "Kickboxing Gym": [FightingStyle.STRIKER, FightingStyle.MUAY_THAI],
    "MMA Academy": [FightingStyle.BALANCED, FightingStyle.SPRAWL_AND_BRAWL],
    "Boxing Gym": [FightingStyle.STRIKER, FightingStyle.COUNTER_STRIKER],
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_style_definition(style: FightingStyle) -> StyleDefinition:
    """Get the complete definition for a fighting style."""
    return STYLE_DEFINITIONS.get(style, STYLE_DEFINITIONS[FightingStyle.BALANCED])


def get_style_matchup_modifier(style1: FightingStyle, style2: FightingStyle) -> float:
    """Get the matchup modifier between two styles (-0.05 to +0.05)."""
    matchups = STYLE_MATCHUPS.get(style1, {})
    return matchups.get(style2, 0.0)


def generate_style_for_fighter(
    country: Optional[str] = None,
    camp_styles: Optional[List[FightingStyle]] = None,
    weighted: bool = True
) -> FightingStyle:
    """
    Generate an appropriate fighting style for a fighter.
    
    Includes 5% "Unicorn" chance to generate counter-meta fighters:
    - Brazilian wrestler instead of BJJ
    - Dagestani kickboxer instead of wrestler
    - Thai grappler instead of Muay Thai
    
    These rare counter-meta fighters become fan favorites!
    """
    if not weighted:
        return random.choice(list(FightingStyle))
    
    # === UNICORN CHECK: 5% chance for counter-meta fighter ===
    if country and country in COUNTRY_STYLE_WEIGHTS and random.random() < 0.05:
        # Get the dominant styles for this country
        country_weights = COUNTRY_STYLE_WEIGHTS[country]
        dominant_styles = [s for s, w in country_weights.items() if w >= 20]
        
        # Find opposite styles (counter-meta)
        counter_meta_map = {
            # Grappling countries -> Striking unicorns
            FightingStyle.WRESTLER: [FightingStyle.STRIKER, FightingStyle.MUAY_THAI, FightingStyle.COUNTER_STRIKER],
            FightingStyle.BJJ_SPECIALIST: [FightingStyle.WRESTLER, FightingStyle.STRIKER, FightingStyle.PRESSURE_FIGHTER],
            FightingStyle.GROUND_AND_POUND: [FightingStyle.COUNTER_STRIKER, FightingStyle.POINT_FIGHTER],
            # Striking countries -> Grappling unicorns
            FightingStyle.MUAY_THAI: [FightingStyle.WRESTLER, FightingStyle.BJJ_SPECIALIST],
            FightingStyle.STRIKER: [FightingStyle.WRESTLER, FightingStyle.BJJ_SPECIALIST, FightingStyle.GROUND_AND_POUND],
            FightingStyle.PRESSURE_FIGHTER: [FightingStyle.BJJ_SPECIALIST, FightingStyle.COUNTER_STRIKER],
        }
        
        # Collect possible unicorn styles
        unicorn_options = []
        for dominant in dominant_styles:
            if dominant in counter_meta_map:
                unicorn_options.extend(counter_meta_map[dominant])
        
        if unicorn_options:
            # Remove duplicates and pick one
            unicorn_options = list(set(unicorn_options))
            return random.choice(unicorn_options)
    
    # === NORMAL GENERATION ===
    if country and country in COUNTRY_STYLE_WEIGHTS:
        weights = dict(COUNTRY_STYLE_WEIGHTS[country])
    else:
        weights = dict(DEFAULT_STYLE_WEIGHTS)
    
    if camp_styles:
        for style in camp_styles:
            if style in weights:
                weights[style] *= 1.2
    
    styles = list(weights.keys())
    weight_values = list(weights.values())
    return random.choices(styles, weights=weight_values, k=1)[0]


def get_style_attribute_bonuses(style: FightingStyle) -> Dict[str, int]:
    """Get the attribute bonuses for a fighting style."""
    definition = get_style_definition(style)
    return dict(definition.attribute_bonuses)


def get_style_finish_rates(style: FightingStyle) -> Dict[str, float]:
    """Get the finish rate distribution for a style."""
    definition = get_style_definition(style)
    return {"ko": definition.ko_rate, "sub": definition.sub_rate, "dec": definition.dec_rate}


def validate_style_attributes(style: FightingStyle, attributes: Dict[str, int]) -> bool:
    """Check if a fighter's attributes match a style's requirements."""
    definition = get_style_definition(style)
    for attr, min_value in definition.attribute_requirements.items():
        if attributes.get(attr, 0) < min_value:
            return False
    return True


def determine_fight_method(style: FightingStyle, is_winner: bool = True) -> str:
    """Determine how a fight ends based on fighter's style."""
    rates = get_style_finish_rates(style)
    roll = random.random()
    if roll < rates["ko"]:
        return random.choice(["KO", "TKO"])
    elif roll < rates["ko"] + rates["sub"]:
        return "Submission"
    else:
        return random.choice(["Unanimous Decision", "Split Decision", "Majority Decision"])


def get_style_commentary(style: FightingStyle) -> str:
    """Get a commentary snippet for a fighting style."""
    commentary = {
        FightingStyle.STRIKER: "a dangerous knockout artist on the feet",
        FightingStyle.COUNTER_STRIKER: "a master of timing and counters",
        FightingStyle.PRESSURE_FIGHTER: "known for relentless forward pressure",
        FightingStyle.POINT_FIGHTER: "an elusive point-fighting specialist",
        FightingStyle.MUAY_THAI: "a devastating Muay Thai specialist",
        FightingStyle.WRESTLER: "an elite-level wrestler",
        FightingStyle.GROUND_AND_POUND: "a ground-and-pound specialist",
        FightingStyle.BJJ_SPECIALIST: "a dangerous submission artist",
        FightingStyle.CLINCH_FIGHTER: "a grinding clinch fighter",
        FightingStyle.SPRAWL_AND_BRAWL: "a sprawl-and-brawl fighter with excellent takedown defense",
        FightingStyle.BALANCED: "a well-rounded mixed martial artist",
    }
    return commentary.get(style, "a skilled fighter")


def get_all_styles() -> List[FightingStyle]:
    """Get list of all fighting styles."""
    return list(FightingStyle)


def get_styles_by_category() -> Dict[str, List[FightingStyle]]:
    """Get styles organized by category."""
    return {
        "stand_up": [FightingStyle.STRIKER, FightingStyle.COUNTER_STRIKER, 
                     FightingStyle.PRESSURE_FIGHTER, FightingStyle.POINT_FIGHTER, FightingStyle.MUAY_THAI],
        "grappling": [FightingStyle.WRESTLER, FightingStyle.GROUND_AND_POUND,
                      FightingStyle.BJJ_SPECIALIST, FightingStyle.CLINCH_FIGHTER],
        "hybrid": [FightingStyle.SPRAWL_AND_BRAWL, FightingStyle.BALANCED],
    }


def get_style_for_attributes(attributes: Dict[str, int]) -> FightingStyle:
    """
    Determine the most appropriate style based on fighter attributes.
    
    Uses SOFT PENALTIES instead of hard gates to prevent specialists
    from being misclassified as "Balanced" due to one weak stat.
    
    Example: 95 kicks + 54 boxing should still be Kickboxer/Muay Thai,
    not "Balanced" just because boxing is 1 point below threshold.
    """
    scores = {}
    
    for style, definition in STYLE_DEFINITIONS.items():
        score = 0.0
        
        # 1. Calculate base score from attribute bonuses
        # Higher relevant stats = higher score for this style
        for attr, bonus in definition.attribute_bonuses.items():
            if bonus > 0:
                attr_value = attributes.get(attr, 50)
                score += attr_value * (bonus / 10)
        
        # 2. Apply SOFT PENALTIES for unmet requirements (instead of hard rejection)
        # Missing requirements reduce score but don't disqualify
        penalty = 0.0
        primary_stat_elite = False
        
        for attr, min_val in definition.attribute_requirements.items():
            attr_value = attributes.get(attr, 0)
            
            if attr_value < min_val:
                # Penalty scales with how far below requirement
                # 5 points per point below threshold
                penalty += (min_val - attr_value) * 5
            
            # Check if this is an ELITE primary stat (85+)
            # Elite primary stats can override secondary deficiencies
            if attr_value >= 85:
                primary_stat_elite = True
        
        # 3. Elite override: reduce penalty if fighter has elite primary stat
        # This lets the 95 kicks / 54 boxing fighter still be a Kickboxer
        if primary_stat_elite:
            penalty *= 0.5  # Halve the penalty
        
        # 4. Calculate final score
        final_score = score - penalty
        
        # Only consider positive scores
        scores[style] = max(0, final_score)
    
    # If no style has positive score, default to Balanced
    if max(scores.values()) == 0:
        return FightingStyle.BALANCED
    
    return max(scores, key=scores.get)


# ============================================================================
# GAMEPLAN-AI-SELECT1 — AI style → gameplan map
# ============================================================================
# Deterministic, complete, no fall-through. Covers all 11 canonical
# fighting_style display_name strings from STYLE_DEFINITIONS above.
# BALANCED is legitimate only for the "Balanced" style — never a fallthrough.
# Judgment calls (documented for future revisit):
#   Striker         → AGGRESSIVE (was MEASURED; flipped on GAMEPLAN-AI-SELECT1
#                                 probe evidence — MEASURED's +4
#                                 striking_defense / -2 initiative pre-fight
#                                 mutation produced a broken "striker" identity:
#                                 Str-mir cell showed +9pp KO surge from
#                                 defensively-buffed strikers spending more
#                                 exchanges attriting chins, and BJJ-Str cell
#                                 lost -3.2pp SUB rate because MEASURED
#                                 strikers stopped committing to strikes the
#                                 BJJ hunter could counter into grapple.
#                                 AGGRESSIVE = +4 boxing/kicks, +2 initiative,
#                                 forward intent — matches "plain striker
#                                 pushes the pace" identity.)
#   Point Fighter   → MEASURED   (alt: DEFENSIVE for out-point safety.
#                                 MEASURED works here because Point Fighter's
#                                 IDENTITY is patient point accumulation —
#                                 the +4 striking_defense buff matches intent.)
#   Muay Thai       → CLINCH     (alt: AGGRESSIVE for stand-and-bang)
#   Sprawl & Brawl  → AGGRESSIVE (alt: DEFENSIVE if anti-wrestling reads
#                                 more than the brawl)
_AI_STYLE_TO_GAMEPLAN: Dict[str, str] = {
    "Striker":          "AGGRESSIVE",
    "Counter Striker":  "DEFENSIVE",
    "Pressure Fighter": "AGGRESSIVE",
    "Point Fighter":    "MEASURED",
    "Muay Thai":        "CLINCH",
    "Wrestler":         "TAKEDOWN",
    "Ground & Pound":   "GNP",
    "BJJ Specialist":   "SUBMISSION",
    "Clinch Fighter":   "CLINCH",
    "Sprawl & Brawl":   "AGGRESSIVE",
    "Balanced":         "BALANCED",
}


def ai_gameplan_for_style(style: str) -> str:
    """Return the AI's deterministic gameplan for a fighting style.

    Style-identity only — no opponent scouting, no variance. Same style
    → same plan, every fight. Style input is the display_name string
    from STYLE_DEFINITIONS (e.g. "Wrestler", "BJJ Specialist"). Unknown
    inputs return "BALANCED" as a safe fallback, but every real style
    in the codebase has an explicit entry so BALANCED is never reached
    by a legitimate call.
    """
    return _AI_STYLE_TO_GAMEPLAN.get(style or "", "BALANCED")


__all__ = [
    "StyleDefinition", "STYLE_DEFINITIONS", "STYLE_MATCHUPS",
    "COUNTRY_STYLE_WEIGHTS", "DEFAULT_STYLE_WEIGHTS", "CAMP_STYLE_PRESETS",
    "get_style_definition", "get_style_matchup_modifier", "generate_style_for_fighter",
    "get_style_attribute_bonuses", "get_style_finish_rates", "validate_style_attributes",
    "determine_fight_method", "get_style_commentary", "get_all_styles",
    "get_styles_by_category", "get_style_for_attributes",
    "calculate_style_score", "check_secondary_style", "get_style_display_name",
    "ai_gameplan_for_style",
]


# ============================================================================
# DUAL STYLE SYSTEM
# ============================================================================

def calculate_style_score(style: FightingStyle, attributes: Dict[str, int]) -> float:
    """
    Calculate how well a fighter's attributes match a given style.
    
    Returns a score where higher = better fit.
    Used for determining primary/secondary styles.
    """
    definition = STYLE_DEFINITIONS.get(style)
    if not definition:
        return 0.0
    
    score = 0.0
    
    # Base score from attribute bonuses
    for attr, bonus in definition.attribute_bonuses.items():
        if bonus > 0:
            attr_value = attributes.get(attr, 50)
            score += attr_value * (bonus / 10)
    
    # Penalty for unmet requirements
    penalty = 0.0
    primary_stat_elite = False
    
    for attr, min_val in definition.attribute_requirements.items():
        attr_value = attributes.get(attr, 0)
        
        if attr_value < min_val:
            penalty += (min_val - attr_value) * 5
        
        if attr_value >= 85:
            primary_stat_elite = True
    
    if primary_stat_elite:
        penalty *= 0.5
    
    return max(0, score - penalty)


def check_secondary_style(
    primary_style: FightingStyle,
    attributes: Dict[str, int],
    current_secondary: Optional[FightingStyle] = None,
) -> Optional[FightingStyle]:
    """
    Check if fighter qualifies for a secondary style.
    
    Requirements to EARN a secondary style:
    1. Must score at least 75% of primary style score
    2. Must be a DIFFERENT style than primary
    3. Must not be "Balanced" (too generic)
    
    Requirements to KEEP existing secondary:
    1. Must still score at least 60% of primary (more lenient)
    
    Args:
        primary_style: Fighter's current primary style
        attributes: Fighter's current attributes
        current_secondary: Existing secondary style (if any)
        
    Returns:
        New/retained secondary style, or None if not qualified
    """
    primary_score = calculate_style_score(primary_style, attributes)
    
    if primary_score <= 0:
        return None
    
    # Calculate scores for all styles
    style_scores = {}
    for style in STYLE_DEFINITIONS.keys():
        if style == primary_style:
            continue
        if style == FightingStyle.BALANCED:
            continue  # Balanced doesn't count as secondary
        
        score = calculate_style_score(style, attributes)
        if score > 0:
            style_scores[style] = score
    
    if not style_scores:
        return None
    
    # Find best non-primary style
    best_secondary = max(style_scores, key=style_scores.get)
    best_score = style_scores[best_secondary]
    
    # Check if they qualify
    threshold = 0.60 if current_secondary else 0.75
    
    if best_score >= primary_score * threshold:
        return best_secondary
    
    # Check if they can keep existing secondary (lower threshold)
    if current_secondary and current_secondary in style_scores:
        if style_scores[current_secondary] >= primary_score * 0.60:
            return current_secondary
    
    return None


def check_style_evolution(
    current_primary: FightingStyle,
    current_secondary: Optional[FightingStyle],
    attributes: Dict[str, int],
) -> Tuple[FightingStyle, Optional[FightingStyle], bool]:
    """
    Check if fighter's styles should evolve based on current attributes.
    
    Evolution can happen in two ways:
    1. Secondary becomes strong enough to become Primary (styles swap)
    2. Fighter qualifies for a new secondary style
    
    Args:
        current_primary: Current primary fighting style
        current_secondary: Current secondary style (if any)
        attributes: Fighter's current attributes
        
    Returns:
        Tuple of (new_primary, new_secondary, did_evolve)
    """
    # Get what style their attributes suggest now
    suggested_primary = get_style_for_attributes(attributes)
    
    # Check for secondary style
    new_secondary = check_secondary_style(
        suggested_primary, attributes, current_secondary
    )
    
    # Determine if evolution happened
    did_evolve = False
    
    # Case 1: Primary style changed
    if suggested_primary != current_primary:
        # The old primary might become secondary
        old_primary_score = calculate_style_score(current_primary, attributes)
        new_primary_score = calculate_style_score(suggested_primary, attributes)
        
        # Only evolve if new style is significantly better (25%+)
        if new_primary_score > old_primary_score * 1.25:
            did_evolve = True
            # Old primary becomes secondary if it qualifies
            if old_primary_score >= new_primary_score * 0.60:
                new_secondary = current_primary
            return suggested_primary, new_secondary, True
    
    # Case 2: Secondary changed
    if new_secondary != current_secondary:
        did_evolve = True
    
    return current_primary, new_secondary, did_evolve


def get_style_display_name(
    primary: FightingStyle,
    secondary: Optional[FightingStyle] = None
) -> str:
    """
    Get display string for fighter's style(s).
    
    Examples:
        "Wrestler"
        "Sprawl and Brawl / Wrestler"
    """
    primary_def = get_style_definition(primary)
    primary_name = primary_def.display_name
    
    if secondary:
        secondary_def = get_style_definition(secondary)
        secondary_name = secondary_def.display_name
        return f"{primary_name} / {secondary_name}"
    
    return primary_name


def get_active_style_matchup(
    fighter_primary: FightingStyle,
    fighter_secondary: Optional[FightingStyle],
    fighter_using_secondary: bool,
    opponent_primary: FightingStyle,
    opponent_secondary: Optional[FightingStyle],
    opponent_using_secondary: bool,
) -> float:
    """
    Get matchup modifier when fighters can choose which style to use.
    
    Args:
        fighter_*: Fighter's styles and choice
        opponent_*: Opponent's styles and choice
        
    Returns:
        Matchup modifier (-0.08 to +0.08)
    """
    fighter_style = fighter_secondary if (fighter_using_secondary and fighter_secondary) else fighter_primary
    opponent_style = opponent_secondary if (opponent_using_secondary and opponent_secondary) else opponent_primary
    
    return get_style_matchup_modifier(fighter_style, opponent_style)
