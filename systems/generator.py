# simulation/generator.py
# Module 17: Fighter Generator  
# Lines: ~985
#
# Generates realistic fighters with culturally-appropriate names,
# regional fighting styles, and layered attribute generation.
# Updated with FightingStyle integration.
# Added: Generational Talent system (0.3% chance)

"""
Cage Dynasty - Fighter Generator

Comprehensive fighter generation with:
- Regional style tendencies (BJJ from Brazil, Wrestling from US, etc.)
- Physical build types affecting attributes
- Personality archetypes influencing behavior
- Age-appropriate stat potential
- Integration with existing fight engine
- FightingStyle enum mapping for entity creation

Usage:
    from simulation.generator import generate_fighter, generate_roster
    from simulation.generator import generate_fighting_style, get_fighting_style_for_martial_art
    
    # Generate single fighter
    fighter = generate_fighter()
    
    # Get fighting style for a fighter
    style = generate_fighting_style(country="Brazil", attributes={"bjj": 85, "wrestling": 60})
    # Returns FightingStyle.BJJ_SPECIALIST
    
    # Map martial art to fighting style
    fighting_style = get_fighting_style_for_martial_art("BJJ")
    # Returns FightingStyle.BJJ_SPECIALIST
"""

import random
import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# Import from our existing modules
from simulation.fight_engine import FighterAttributes
from data.name_database import get_full_name, get_random_country, generate_unique_name
from core.types import FightingStyle


# ============================================================================
# WEIGHT CLASS DEFINITIONS
# ============================================================================

WEIGHT_CLASSES: Dict[str, Tuple[int, int]] = {
    "Strawweight": (106, 115),
    "Flyweight": (116, 125),
    "Bantamweight": (126, 135),
    "Featherweight": (136, 145),
    "Lightweight": (146, 155),
    "Welterweight": (156, 170),
    "Middleweight": (171, 185),
    "Light Heavyweight": (186, 205),
    "Heavyweight": (206, 265),
}

# Height ranges by weight class (in cm)
HEIGHT_RANGES: Dict[str, Tuple[int, int]] = {
    "Strawweight": (155, 168),
    "Flyweight": (160, 173),
    "Bantamweight": (165, 178),
    "Featherweight": (170, 183),
    "Lightweight": (173, 188),
    "Welterweight": (178, 191),
    "Middleweight": (180, 194),
    "Light Heavyweight": (185, 198),
    "Heavyweight": (188, 203),
}


# ============================================================================
# COUNTRY LISTS AND MAPPINGS
# ============================================================================

COUNTRIES = [
    "United States", "Brazil", "Canada", "United Kingdom", "Ireland", "Russia",
    "Mexico", "Australia", "Netherlands", "Sweden", "Poland", "Germany",
    "France", "Italy", "Spain", "Japan", "China", "South Korea", "Thailand",
    "New Zealand", "South Africa", "Nigeria", "Ukraine", "Argentina",
    "Uzbekistan", "Kazakhstan"
]

COUNTRY_TO_REGION_MAP: Dict[str, str] = {
    "Nigeria": "West Africa",
    "South Africa": "West Africa",
    "Sweden": "Northern Europe",
    "Netherlands": "Northern Europe",
    "Germany": "Northern Europe",
    "Thailand": "Southeast Asia",
    "China": "Southeast Asia",
    "Japan": "East Asia",
    "South Korea": "East Asia",
    "Brazil": "South America",
    "Argentina": "South America",
    "Russia": "Eastern Europe",
    "Ukraine": "Eastern Europe",
    "Poland": "Eastern Europe",
    "Uzbekistan": "Central Asia",
    "Kazakhstan": "Central Asia",
    "United States": "North America",
    "Canada": "North America",
    "Mexico": "Latin America",
    "United Kingdom": "Western Europe",
    "Ireland": "Western Europe",
    "France": "Western Europe",
    "Italy": "Western Europe",
    "Spain": "Western Europe",
    "Australia": "Oceania",
    "New Zealand": "Oceania",
}

REGIONAL_TRAITS: Dict[str, Dict] = {
    "West Africa": {
        "attr_mod": {"speed": 3, "strength": 2},
        "style_tendency": "athletic_striker"
    },
    "Northern Europe": {
        "attr_mod": {"speed": -1, "strength": 3, "chin": 2},
        "style_tendency": "kickboxer"
    },
    "Southeast Asia": {
        "attr_mod": {"speed": 2, "kicks": 4, "chin": -1},
        "style_tendency": "muay_thai"
    },
    "East Asia": {
        "attr_mod": {"speed": 2, "fight_iq": 2},
        "style_tendency": "technical"
    },
    "South America": {
        "attr_mod": {"bjj": 4, "composure": 2},
        "style_tendency": "bjj_specialist"
    },
    "Eastern Europe": {
        "attr_mod": {"wrestling": 3, "strength": 2, "chin": 2},
        "style_tendency": "sambo"
    },
    "Central Asia": {
        "attr_mod": {"wrestling": 5, "cardio": 2, "heart": 2},
        "style_tendency": "wrestler"
    },
    "North America": {
        "attr_mod": {"wrestling": 2, "boxing": 2},
        "style_tendency": "mma_hybrid"
    },
    "Latin America": {
        "attr_mod": {"boxing": 3, "heart": 2},
        "style_tendency": "boxer"
    },
    "Western Europe": {
        "attr_mod": {"boxing": 2, "composure": 2},
        "style_tendency": "technical_striker"
    },
    "Oceania": {
        "attr_mod": {"cardio": 2, "heart": 2},
        "style_tendency": "well_rounded"
    },
}


# ============================================================================
# BUILD TYPES
# ============================================================================

BUILD_TYPES: List[Dict[str, Any]] = [
    {
        "name": "Power",
        "modifiers": {"strength": 6, "speed": -2, "chin": 2, "reach_ratio": 1.0},
        "weight_modifier": 1.03,
        "description": "Thick, powerful build"
    },
    {
        "name": "Athletic",
        "modifiers": {"strength": 2, "speed": 3, "cardio": 2, "reach_ratio": 1.02},
        "weight_modifier": 1.00,
        "description": "Well-balanced athletic build"
    },
    {
        "name": "Slim",
        "modifiers": {"speed": 4, "cardio": 3, "strength": -3, "reach_ratio": 1.04},
        "weight_modifier": 0.97,
        "description": "Lean with reach advantage"
    },
    {
        "name": "Stocky",
        "modifiers": {"strength": 4, "chin": 3, "speed": -3, "reach_ratio": 0.96},
        "weight_modifier": 1.02,
        "description": "Compact and durable"
    },
    {
        "name": "Average",
        "modifiers": {"reach_ratio": 1.0},
        "weight_modifier": 1.00,
        "description": "Standard build"
    },
]

# Alias for backward compatibility
BUILDS = BUILD_TYPES


# ============================================================================
# FIGHTING STYLES (Martial Art Backgrounds)
# ============================================================================

STYLES: List[Dict[str, Any]] = [
    {
        "name": "Wrestling",
        "modifiers": {"wrestling": 6, "takedown_defense": 4, "bjj": 2, "boxing": -2},
        "behavior_tendency": {"strike": 0.20, "takedown": 0.55, "clinch": 0.25},
        "description": "Control-based wrestling foundation"
    },
    {
        "name": "BJJ",
        "modifiers": {"bjj": 8, "wrestling": 2, "striking_defense": -2},
        "behavior_tendency": {"strike": 0.15, "takedown": 0.40, "clinch": 0.45},
        "description": "Submission specialist"
    },
    {
        "name": "Boxing",
        "modifiers": {"boxing": 6, "striking_defense": 3, "wrestling": -3, "bjj": -2},
        "behavior_tendency": {"strike": 0.70, "takedown": 0.05, "clinch": 0.25},
        "description": "Classic boxing foundation"
    },
    {
        "name": "Muay Thai",
        "modifiers": {"kicks": 5, "clinch_striking": 5, "boxing": 2, "wrestling": -3},
        "behavior_tendency": {"strike": 0.60, "takedown": 0.10, "clinch": 0.30},
        "description": "Traditional Thai boxing"
    },
    {
        "name": "Kickboxing",
        "modifiers": {"kicks": 4, "boxing": 4, "speed": 2, "wrestling": -4},
        "behavior_tendency": {"strike": 0.75, "takedown": 0.05, "clinch": 0.20},
        "description": "Dutch kickboxing style"
    },
    {
        "name": "Sambo",
        "modifiers": {"wrestling": 5, "bjj": 5, "boxing": -2, "kicks": -2},
        "behavior_tendency": {"strike": 0.15, "takedown": 0.55, "clinch": 0.30},
        "description": "Russian grappling, leg lock specialist"
    },
    {
        "name": "Judo",
        "modifiers": {"wrestling": 4, "bjj": 4, "clinch_striking": 2, "kicks": -3},
        "behavior_tendency": {"strike": 0.10, "takedown": 0.50, "clinch": 0.40},
        "description": "Throws and trips expert"
    },
    {
        "name": "Karate",
        "modifiers": {"kicks": 5, "speed": 3, "boxing": 2, "wrestling": -4},
        "behavior_tendency": {"strike": 0.70, "takedown": 0.05, "clinch": 0.25},
        "description": "Point fighting, distance management"
    },
    {
        "name": "MMA Hybrid",
        "modifiers": {"boxing": 2, "kicks": 2, "wrestling": 2, "bjj": 2},
        "behavior_tendency": {"strike": 0.40, "takedown": 0.30, "clinch": 0.30},
        "description": "Well-rounded mixed martial artist"
    },
]

# Country style weightings
COUNTRY_STYLE_MAP: Dict[str, Dict[str, float]] = {
    "Brazil": {"BJJ": 0.50, "MMA Hybrid": 0.30, "Muay Thai": 0.15, "Boxing": 0.05},
    "Russia": {"Sambo": 0.40, "Wrestling": 0.35, "MMA Hybrid": 0.20, "Boxing": 0.05},
    "United States": {"Wrestling": 0.40, "MMA Hybrid": 0.30, "Boxing": 0.20, "BJJ": 0.10},
    "Netherlands": {"Kickboxing": 0.45, "Muay Thai": 0.25, "MMA Hybrid": 0.20, "Boxing": 0.10},
    "Thailand": {"Muay Thai": 0.70, "MMA Hybrid": 0.20, "Kickboxing": 0.10},
    "Japan": {"Judo": 0.35, "Karate": 0.25, "MMA Hybrid": 0.25, "BJJ": 0.15},
    "Canada": {"Wrestling": 0.35, "MMA Hybrid": 0.35, "BJJ": 0.20, "Kickboxing": 0.10},
    "Mexico": {"Boxing": 0.55, "Wrestling": 0.25, "MMA Hybrid": 0.20},
    "United Kingdom": {"Boxing": 0.40, "MMA Hybrid": 0.35, "BJJ": 0.15, "Wrestling": 0.10},
    "Ireland": {"Boxing": 0.50, "Karate": 0.20, "MMA Hybrid": 0.30},
    "Sweden": {"MMA Hybrid": 0.40, "Wrestling": 0.25, "Kickboxing": 0.20, "Boxing": 0.15},
    "Germany": {"Kickboxing": 0.40, "MMA Hybrid": 0.35, "Wrestling": 0.15, "Boxing": 0.10},
    "France": {"Judo": 0.30, "Kickboxing": 0.25, "MMA Hybrid": 0.30, "Boxing": 0.15},
    "Italy": {"MMA Hybrid": 0.40, "BJJ": 0.25, "Kickboxing": 0.20, "Boxing": 0.15},
    "Spain": {"MMA Hybrid": 0.40, "Boxing": 0.30, "Kickboxing": 0.20, "BJJ": 0.10},
    "Poland": {"MMA Hybrid": 0.35, "Wrestling": 0.30, "Kickboxing": 0.25, "Boxing": 0.10},
    "Ukraine": {"Boxing": 0.40, "Sambo": 0.25, "Wrestling": 0.25, "MMA Hybrid": 0.10},
    "South Korea": {"Judo": 0.35, "Karate": 0.25, "MMA Hybrid": 0.30, "BJJ": 0.10},
    "China": {"MMA Hybrid": 0.35, "Wrestling": 0.30, "Kickboxing": 0.25, "Judo": 0.10},
    "Australia": {"MMA Hybrid": 0.35, "Muay Thai": 0.30, "BJJ": 0.20, "Boxing": 0.15},
    "New Zealand": {"MMA Hybrid": 0.35, "Muay Thai": 0.30, "Wrestling": 0.20, "BJJ": 0.15},
    "Argentina": {"BJJ": 0.30, "Boxing": 0.30, "MMA Hybrid": 0.30, "Wrestling": 0.10},
    "Nigeria": {"Boxing": 0.40, "Wrestling": 0.25, "MMA Hybrid": 0.25, "Kickboxing": 0.10},
    "South Africa": {"MMA Hybrid": 0.40, "Wrestling": 0.25, "Kickboxing": 0.20, "Boxing": 0.15},
    "Uzbekistan": {"Wrestling": 0.45, "Boxing": 0.30, "Sambo": 0.15, "MMA Hybrid": 0.10},
    "Kazakhstan": {"Wrestling": 0.50, "Boxing": 0.25, "MMA Hybrid": 0.15, "Sambo": 0.10},
}


# ============================================================================
# MARTIAL ART TO FIGHTING STYLE MAPPING
# ============================================================================

# Maps generator's martial art styles to FightingStyle enum
MARTIAL_ART_TO_FIGHTING_STYLE: Dict[str, FightingStyle] = {
    "Wrestling": FightingStyle.WRESTLER,
    "BJJ": FightingStyle.BJJ_SPECIALIST,
    "Boxing": FightingStyle.STRIKER,
    "Muay Thai": FightingStyle.MUAY_THAI,
    "Kickboxing": FightingStyle.STRIKER,
    "Sambo": FightingStyle.GROUND_AND_POUND,
    "Judo": FightingStyle.CLINCH_FIGHTER,
    "Karate": FightingStyle.POINT_FIGHTER,
    "MMA Hybrid": FightingStyle.BALANCED,
}


# ============================================================================
# PERSONALITY ARCHETYPES
# ============================================================================

PERSONALITIES: List[Dict[str, Any]] = [
    {
        "name": "Hot Head",
        "modifiers": {"heart": 4, "composure": -3},
        "description": "Emotional, aggressive, never backs down"
    },
    {
        "name": "Methodical",
        "modifiers": {"fight_iq": 4, "composure": 3, "heart": -2},
        "description": "Calculated, patient game plan"
    },
    {
        "name": "Showman",
        "modifiers": {"composure": 2, "heart": 2},
        "description": "Plays to the crowd, flashy style"
    },
    {
        "name": "Cautious",
        "modifiers": {"striking_defense": 2, "takedown_defense": 2, "heart": -3},
        "description": "Defense-first, point fighter"
    },
    {
        "name": "Warrior",
        "modifiers": {"heart": 6, "chin": 2, "composure": -2},
        "description": "Walks through fire, never quits"
    },
    {
        "name": "Technician",
        "modifiers": {"fight_iq": 5, "composure": 3},
        "description": "Technical mastery, precise execution"
    },
    {
        "name": "Brawler",
        "modifiers": {"strength": 3, "heart": 3, "fight_iq": -3},
        "description": "Swings for the fences"
    },
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def stat_gauss(mu: int, sigma: int) -> int:
    """Generate a stat with gaussian distribution, clamped 1-100"""
    return max(1, min(100, int(random.gauss(mu, sigma))))


def stat_uniform(low: int, high: int) -> int:
    """Generate a stat with uniform distribution, clamped 1-100"""
    return max(1, min(100, random.randint(low, high)))


def get_weight_class_for_weight(weight: int) -> str:
    """Determine weight class based on fighter weight"""
    for wc_name, (min_w, max_w) in WEIGHT_CLASSES.items():
        if min_w <= weight <= max_w:
            return wc_name
    if weight < 106:
        return "Strawweight"
    return "Heavyweight"


def get_weight_for_class(weight_class: str) -> int:
    """Generate a realistic weight for the given class"""
    if weight_class not in WEIGHT_CLASSES:
        weight_class = random.choice(list(WEIGHT_CLASSES.keys()))
    min_w, max_w = WEIGHT_CLASSES[weight_class]
    return random.randint(min_w, max_w)


def select_style_for_country(country: str) -> Dict[str, Any]:
    """Select a fighting style based on country tendencies"""
    style_weights = COUNTRY_STYLE_MAP.get(country, {"MMA Hybrid": 1.0})
    styles = list(style_weights.keys())
    weights = list(style_weights.values())
    selected_name = random.choices(styles, weights=weights, k=1)[0]
    for style in STYLES:
        if style["name"] == selected_name:
            return style
    return STYLES[-1]  # Default to MMA Hybrid


def select_build(country: str) -> Dict[str, Any]:
    """Select a build type with some regional tendencies"""
    build_weights = [1.0, 1.5, 1.0, 0.8, 1.2]  # Base weights
    region = COUNTRY_TO_REGION_MAP.get(country)
    if region in ["Central Asia", "Eastern Europe"]:
        build_weights[0] = 1.5  # More Power builds
        build_weights[3] = 1.2  # More Stocky builds
    elif region in ["Southeast Asia", "East Asia"]:
        build_weights[2] = 1.8  # More Slim builds
        build_weights[1] = 1.3  # More Athletic
    elif region == "West Africa":
        build_weights[1] = 2.0  # More Athletic builds
    return random.choices(BUILD_TYPES, weights=build_weights, k=1)[0]


def generate_birth_date(min_age: int = 18, max_age: int = 40) -> Tuple[int, int, int]:
    """Generate a random birth date resulting in given age range"""
    today = datetime.date.today()
    age = random.randint(min_age, max_age)
    birth_year = today.year - age
    birth_month = random.randint(1, 12)
    max_day = 28 if birth_month == 2 else (30 if birth_month in [4, 6, 9, 11] else 31)
    birth_day = random.randint(1, max_day)
    return birth_year, birth_month, birth_day


def calculate_age(birth_year: int, birth_month: int, birth_day: int) -> int:
    """Calculate age from birth date components"""
    today = datetime.date.today()
    age = today.year - birth_year
    if (today.month, today.day) < (birth_month, birth_day):
        age -= 1
    return age


# ============================================================================
# FIGHTING STYLE GENERATION (NEW - Uses FightingStyle Enum)
# ============================================================================

def get_fighting_style_for_martial_art(martial_art: str) -> FightingStyle:
    """
    Map a martial art background to a FightingStyle enum.
    
    Args:
        martial_art: Name from STYLES list (e.g., "Wrestling", "BJJ")
        
    Returns:
        Corresponding FightingStyle enum value
    """
    return MARTIAL_ART_TO_FIGHTING_STYLE.get(martial_art, FightingStyle.BALANCED)


def generate_fighting_style(
    country: Optional[str] = None,
    attributes: Optional[Dict[str, int]] = None,
    martial_art: Optional[str] = None
) -> FightingStyle:
    """
    Generate an appropriate FightingStyle for a fighter.
    
    Can use country tendencies, attribute profile, or specified martial art.
    
    Args:
        country: Fighter's nationality (affects style probability)
        attributes: Dict of attribute values (for attribute-based selection)
        martial_art: Specific martial art name to map
        
    Returns:
        FightingStyle enum value
    """
    # If martial art specified, map directly
    if martial_art:
        return get_fighting_style_for_martial_art(martial_art)
    
    # If attributes provided, determine from attribute profile
    if attributes:
        return _determine_style_from_attributes(attributes)
    
    # Otherwise use country tendencies
    if country:
        style_data = select_style_for_country(country)
        return get_fighting_style_for_martial_art(style_data["name"])
    
    # Default: random style with country weighting
    country = random.choice(COUNTRIES)
    style_data = select_style_for_country(country)
    return get_fighting_style_for_martial_art(style_data["name"])


def _determine_style_from_attributes(attributes: Dict[str, int]) -> FightingStyle:
    """
    Determine the most appropriate FightingStyle based on attribute profile.
    
    Args:
        attributes: Dict of attribute name -> value
        
    Returns:
        FightingStyle that best matches the attribute profile
    """
    boxing = attributes.get("boxing", 50)
    kicks = attributes.get("kicks", 50)
    wrestling = attributes.get("wrestling", 50)
    bjj = attributes.get("bjj", 50)
    takedown_defense = attributes.get("takedown_defense", 50)
    clinch_striking = attributes.get("clinch_striking", 50)
    speed = attributes.get("speed", 50)
    striking_defense = attributes.get("striking_defense", 50)
    
    # Calculate composite scores
    striking_score = (boxing + kicks) / 2
    grappling_score = (wrestling + bjj) / 2
    
    # High BJJ, moderate wrestling -> BJJ_SPECIALIST
    if bjj >= 75 and bjj > wrestling:
        return FightingStyle.BJJ_SPECIALIST
    
    # High wrestling -> WRESTLER or GROUND_AND_POUND
    if wrestling >= 75:
        if attributes.get("strength", 50) >= 70:
            return FightingStyle.GROUND_AND_POUND
        return FightingStyle.WRESTLER
    
    # High kicks and clinch -> MUAY_THAI
    if kicks >= 70 and clinch_striking >= 65:
        return FightingStyle.MUAY_THAI
    
    # High takedown defense with good striking -> SPRAWL_AND_BRAWL
    if takedown_defense >= 75 and striking_score >= 65:
        return FightingStyle.SPRAWL_AND_BRAWL
    
    # High speed and defense -> POINT_FIGHTER or COUNTER_STRIKER
    if speed >= 75 and striking_defense >= 70:
        if attributes.get("composure", 50) >= 70:
            return FightingStyle.COUNTER_STRIKER
        return FightingStyle.POINT_FIGHTER
    
    # High cardio and heart -> PRESSURE_FIGHTER
    if attributes.get("cardio", 50) >= 75 and attributes.get("heart", 50) >= 75:
        return FightingStyle.PRESSURE_FIGHTER
    
    # High clinch -> CLINCH_FIGHTER
    if clinch_striking >= 70 and wrestling >= 60:
        return FightingStyle.CLINCH_FIGHTER
    
    # High striking overall -> STRIKER
    if striking_score >= 70:
        return FightingStyle.STRIKER
    
    # Default to BALANCED
    return FightingStyle.BALANCED


def generate_traits_for_style(
    fighting_style: FightingStyle,
    attributes: Optional[Dict[str, int]] = None
) -> List[str]:
    """
    Generate appropriate traits for a fighter based on their style.
    
    Args:
        fighting_style: Fighter's FightingStyle
        attributes: Optional attribute dict for additional trait selection
        
    Returns:
        List of trait names (0-3 traits)
    """
    # Style-associated traits
    style_traits = {
        FightingStyle.STRIKER: ["Knockout Artist", "Fast Starter", "Counter Puncher", "Killer Instinct"],
        FightingStyle.COUNTER_STRIKER: ["Counter Puncher", "Iron Chin", "Elusive", "Southpaw"],
        FightingStyle.PRESSURE_FIGHTER: ["Iron Chin", "Cardio Machine", "Durable", "Killer Instinct"],
        FightingStyle.POINT_FIGHTER: ["Elusive", "Fast Starter", "Cardio Machine", "Southpaw"],
        FightingStyle.MUAY_THAI: ["Knockout Artist", "Body Snatcher", "Iron Chin", "Southpaw"],
        FightingStyle.WRESTLER: ["Takedown Artist", "Cardio Machine", "Grinding"],
        FightingStyle.GROUND_AND_POUND: ["Knockout Artist", "Takedown Artist", "Heavy Hands", "Killer Instinct"],
        FightingStyle.BJJ_SPECIALIST: ["Submission Specialist", "Choke Artist", "Rubber Guard"],
        FightingStyle.CLINCH_FIGHTER: ["Cardio Machine", "Iron Chin", "Grinding"],
        FightingStyle.SPRAWL_AND_BRAWL: ["Knockout Artist", "Takedown Defense", "Big Game Hunter", "Killer Instinct"],
        FightingStyle.BALANCED: ["Durable", "Big Game Hunter", "Gym Rat"],
    }
    
    possible_traits = style_traits.get(fighting_style, ["Durable"])
    
    # Randomly select 0-2 traits
    num_traits = random.choices([0, 1, 2], weights=[0.3, 0.5, 0.2], k=1)[0]
    
    if num_traits == 0:
        return []
    
    selected = random.sample(possible_traits, min(num_traits, len(possible_traits)))
    
    # Attribute-based bonus traits
    if attributes:
        if attributes.get("chin", 50) >= 85 and "Iron Chin" not in selected:
            if random.random() < 0.5:
                selected.append("Iron Chin")
        if attributes.get("cardio", 50) >= 85 and "Cardio Machine" not in selected:
            if random.random() < 0.5:
                selected.append("Cardio Machine")
        if attributes.get("heart", 50) >= 90 and "Never Gives Up" not in selected:
            if random.random() < 0.3:
                selected.append("Never Gives Up")
        # Killer Instinct for high finishing attributes
        if attributes.get("strength", 50) >= 80 and attributes.get("composure", 50) >= 75:
            if "Killer Instinct" not in selected and random.random() < 0.2:
                selected.append("Killer Instinct")
    
    # ~10% chance to be a Southpaw (matches real world left-handed population)
    if "Southpaw" not in selected and random.random() < 0.10:
        selected.append("Southpaw")
    
    return selected[:3]  # Max 3 traits


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_fighter(
    name: Optional[str] = None,
    country: Optional[str] = None,
    weight_class: Optional[str] = None,
    weight: Optional[int] = None,
    style: Optional[str] = None,
    overall_rating: Optional[int] = None,
    fighter_type: str = "standard",
    fighter_id: Optional[str] = None,
    existing_names: Optional[set] = None
) -> FighterAttributes:
    """
    Generate a complete fighter with realistic attributes.
    
    Args:
        name: Fighter name (auto-generated if None)
        country: Nationality (random if None)
        weight_class: Target weight class (random if None)
        weight: Specific weight (generated if None)
        style: Fighting style name (country-based if None)
        overall_rating: Target overall rating (type-based if None)
        fighter_type: "prospect", "standard", "prime", or "veteran"
        fighter_id: Unique ID (auto-generated if None)
        existing_names: Set of names to avoid duplicates
        
    Returns:
        FighterAttributes object ready for fight simulation
    """
    if existing_names is None:
        existing_names = set()
    
    # --- 1. Country and Name ---
    if country is None:
        country = get_random_country()
    
    if name is None:
        # generate_unique_name returns (name, country) tuple
        name_result = generate_unique_name(country, existing_names)
        name = name_result[0]  # Extract just the name string
    
    if fighter_id is None:
        fighter_id = f"fighter_{hash(name) % 100000:05d}"
    
    # --- 2. Age based on fighter type ---
    age_ranges = {
        "prospect": (18, 25),
        "standard": (23, 32),
        "prime": (26, 32),
        "veteran": (32, 40),
    }
    min_age, max_age = age_ranges.get(fighter_type, (23, 32))
    birth_year, birth_month, birth_day = generate_birth_date(min_age, max_age)
    age = calculate_age(birth_year, birth_month, birth_day)
    
    # --- 3. Weight Class and Weight ---
    if weight_class is None:
        weight_class = random.choice(list(WEIGHT_CLASSES.keys()))
    
    if weight is None:
        weight = get_weight_for_class(weight_class)
    
    # --- 4. Build Type ---
    build = select_build(country)
    
    # --- 5. Fighting Style ---
    if style:
        style_data = next((s for s in STYLES if s["name"] == style), None)
        if style_data is None:
            style_data = select_style_for_country(country)
    else:
        style_data = select_style_for_country(country)
    
    # --- 6. Personality ---
    personality = random.choice(PERSONALITIES)
    
    # --- 7. Generate Base Stats ---
    if overall_rating:
        base_mu = overall_rating
        sigma = 10
    else:
        if fighter_type == "prospect":
            base_mu = 50 + random.randint(0, 15)
        elif fighter_type == "veteran":
            base_mu = 60 + random.randint(0, 15)
        else:
            base_mu = 55 + random.randint(0, 15)
        sigma = 12
    
    # Physical stats
    strength = stat_gauss(base_mu, sigma)
    speed = stat_gauss(base_mu, sigma)
    cardio = stat_gauss(base_mu, sigma)
    chin = stat_gauss(base_mu, sigma)
    
    # Skill stats
    boxing = stat_gauss(base_mu, sigma)
    kicks = stat_gauss(base_mu, sigma)
    clinch_striking = stat_gauss(base_mu - 5, sigma)
    striking_defense = stat_gauss(base_mu, sigma)
    wrestling = stat_gauss(base_mu, sigma)
    bjj = stat_gauss(base_mu, sigma)
    takedown_defense = stat_gauss(base_mu, sigma)
    
    # Mental stats
    heart = stat_gauss(base_mu + 5, sigma)
    fight_iq = stat_gauss(base_mu, sigma)
    composure = stat_gauss(base_mu, sigma)
    
    # --- 8. Apply Build Modifiers ---
    for attr, mod in build["modifiers"].items():
        if attr == "reach_ratio":
            continue
        if attr == "strength":
            strength = max(1, min(100, strength + mod))
        elif attr == "speed":
            speed = max(1, min(100, speed + mod))
        elif attr == "cardio":
            cardio = max(1, min(100, cardio + mod))
        elif attr == "chin":
            chin = max(1, min(100, chin + mod))
    
    # --- 9. Apply Regional Traits ---
    region = COUNTRY_TO_REGION_MAP.get(country)
    if region and region in REGIONAL_TRAITS:
        traits = REGIONAL_TRAITS[region]["attr_mod"]
        for attr, mod in traits.items():
            if attr == "speed":
                speed = max(1, min(100, speed + mod))
            elif attr == "strength":
                strength = max(1, min(100, strength + mod))
            elif attr == "chin":
                chin = max(1, min(100, chin + mod))
            elif attr == "kicks":
                kicks = max(1, min(100, kicks + mod))
            elif attr == "wrestling":
                wrestling = max(1, min(100, wrestling + mod))
            elif attr == "bjj":
                bjj = max(1, min(100, bjj + mod))
            elif attr == "boxing":
                boxing = max(1, min(100, boxing + mod))
            elif attr == "fight_iq":
                fight_iq = max(1, min(100, fight_iq + mod))
            elif attr == "composure":
                composure = max(1, min(100, composure + mod))
            elif attr == "cardio":
                cardio = max(1, min(100, cardio + mod))
            elif attr == "heart":
                heart = max(1, min(100, heart + mod))
    
    # --- 10. Apply Style Modifiers ---
    style_mods = style_data["modifiers"]
    boxing = max(1, min(100, boxing + style_mods.get("boxing", 0)))
    kicks = max(1, min(100, kicks + style_mods.get("kicks", 0)))
    clinch_striking = max(1, min(100, clinch_striking + style_mods.get("clinch_striking", 0)))
    striking_defense = max(1, min(100, striking_defense + style_mods.get("striking_defense", 0)))
    wrestling = max(1, min(100, wrestling + style_mods.get("wrestling", 0)))
    bjj = max(1, min(100, bjj + style_mods.get("bjj", 0)))
    takedown_defense = max(1, min(100, takedown_defense + style_mods.get("takedown_defense", 0)))
    speed = max(1, min(100, speed + style_mods.get("speed", 0)))
    strength = max(1, min(100, strength + style_mods.get("strength", 0)))
    
    # --- 11. Apply Personality Modifiers ---
    pers_mods = personality["modifiers"]
    heart = max(1, min(100, heart + pers_mods.get("heart", 0)))
    fight_iq = max(1, min(100, fight_iq + pers_mods.get("fight_iq", 0)))
    composure = max(1, min(100, composure + pers_mods.get("composure", 0)))
    chin = max(1, min(100, chin + pers_mods.get("chin", 0)))
    strength = max(1, min(100, strength + pers_mods.get("strength", 0)))
    striking_defense = max(1, min(100, striking_defense + pers_mods.get("striking_defense", 0)))
    takedown_defense = max(1, min(100, takedown_defense + pers_mods.get("takedown_defense", 0)))
    
    # --- 12. Apply Weight Class Adjustments ---
    if weight_class in ["Strawweight", "Flyweight"]:
        speed = min(100, speed + 5)
        strength = max(1, strength - 5)
    elif weight_class in ["Bantamweight", "Featherweight"]:
        speed = min(100, speed + 3)
        strength = max(1, strength - 2)
    elif weight_class in ["Middleweight", "Light Heavyweight"]:
        strength = min(100, strength + 3)
        speed = max(1, speed - 2)
    elif weight_class == "Heavyweight":
        strength = min(100, strength + 6)
        speed = max(1, speed - 4)
        chin = min(100, chin + 3)
    
    # --- 13. Age-based Adjustments ---
    if age < 25:
        fight_iq = max(1, fight_iq - 3)
        composure = max(1, composure - 3)
    elif age > 35:
        fight_iq = min(100, fight_iq + 3)
        composure = min(100, composure + 2)
        speed = max(1, speed - 3)
        cardio = max(1, cardio - 2)
        chin = max(1, chin - 2)
    
    # --- 13.5. STRIKER TDD CAP (NEW) ---
    # Pure strikers don't drill takedown defense like grapplers do
    # This creates realistic vulnerability to wrestlers
    # Boxing, Kickboxing, Karate styles get reduced TDD
    striker_styles = {"Boxing", "Kickboxing", "Karate"}
    if style_data["name"] in striker_styles:
        # Apply 0.75x multiplier to TDD (slower growth)
        takedown_defense = int(takedown_defense * 0.75)
        # Hard cap at 75 - even elite strikers vulnerable to elite wrestlers
        takedown_defense = min(takedown_defense, 75)
        takedown_defense = max(1, takedown_defense)  # Ensure at least 1
    
    # --- 14. Generational Talent Check ---
    # 0.3% chance = roughly 1 per 300 fighters
    # Over a 20-year dynasty, expect 1-3 generational talents total
    is_generational = False
    if random.random() < 0.003:
        is_generational = True
        
        # Boost their top 3 skill attributes by 8-12 points
        skill_attrs = [
            ('boxing', boxing), ('kicks', kicks), ('wrestling', wrestling),
            ('bjj', bjj), ('striking_defense', striking_defense)
        ]
        skill_attrs.sort(key=lambda x: x[1], reverse=True)
        
        for attr_name, _ in skill_attrs[:3]:
            boost = random.randint(8, 12)
            if attr_name == 'boxing': boxing = min(99, boxing + boost)
            elif attr_name == 'kicks': kicks = min(99, kicks + boost)
            elif attr_name == 'wrestling': wrestling = min(99, wrestling + boost)
            elif attr_name == 'bjj': bjj = min(99, bjj + boost)
            elif attr_name == 'striking_defense': striking_defense = min(99, striking_defense + boost)
        
        # Boost intangibles - generational talents have exceptional mentals
        heart = min(99, heart + random.randint(5, 10))
        fight_iq = min(99, fight_iq + random.randint(5, 10))
        composure = min(99, composure + random.randint(3, 8))
    
    # --- 15. Create FighterAttributes ---
    # Get the FightingStyle enum from the style_data
    fighting_style = get_fighting_style_for_martial_art(style_data["name"])
    
    return FighterAttributes(
        fighter_id=fighter_id,
        name=name,
        strength=strength,
        speed=speed,
        cardio=cardio,
        chin=chin,
        boxing=boxing,
        kicks=kicks,
        clinch_striking=clinch_striking,
        striking_defense=striking_defense,
        wrestling=wrestling,
        bjj=bjj,
        takedown_defense=takedown_defense,
        heart=heart,
        fight_iq=fight_iq,
        composure=composure,
        is_generational=is_generational,
        fighting_style=fighting_style,
    )


# ============================================================================
# ROSTER GENERATION
# ============================================================================

def generate_roster(
    count: int = 50,
    weight_class: Optional[str] = None,
    country: Optional[str] = None
) -> List[FighterAttributes]:
    """Generate a roster of fighters."""
    roster = []
    existing_names = set()
    
    type_weights = {
        "prospect": 0.20,
        "standard": 0.55,
        "prime": 0.15,
        "veteran": 0.10,
    }
    
    for _ in range(count):
        fighter_type = random.choices(
            list(type_weights.keys()),
            weights=list(type_weights.values()),
            k=1
        )[0]
        
        fighter = generate_fighter(
            country=country,
            weight_class=weight_class,
            fighter_type=fighter_type,
            existing_names=existing_names
        )
        
        existing_names.add(fighter.name)
        roster.append(fighter)
    
    return roster


def generate_weight_class_roster(
    weight_class: str,
    count: int = 15
) -> List[FighterAttributes]:
    """Generate fighters for a specific weight class"""
    return generate_roster(count=count, weight_class=weight_class)


def generate_division(
    weight_class: str,
    ranked_count: int = 15,
    unranked_count: int = 10
) -> Dict[str, List[FighterAttributes]]:
    """Generate a complete division with ranked and unranked fighters"""
    existing_names = set()
    
    ranked = []
    for i in range(ranked_count):
        if i < 5:
            overall = random.randint(80, 95)
        elif i < 10:
            overall = random.randint(70, 85)
        else:
            overall = random.randint(60, 75)
        
        fighter = generate_fighter(
            weight_class=weight_class,
            overall_rating=overall,
            fighter_type="prime" if i < 5 else "standard",
            existing_names=existing_names
        )
        existing_names.add(fighter.name)
        ranked.append(fighter)
    
    unranked = []
    for _ in range(unranked_count):
        fighter_type = random.choices(
            ["prospect", "standard", "veteran"],
            weights=[0.4, 0.4, 0.2],
            k=1
        )[0]
        
        fighter = generate_fighter(
            weight_class=weight_class,
            fighter_type=fighter_type,
            existing_names=existing_names
        )
        existing_names.add(fighter.name)
        unranked.append(fighter)
    
    return {
        "ranked": ranked,
        "unranked": unranked
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_fighter_summary(fighter: FighterAttributes) -> str:
    """Get a brief summary of a fighter's attributes"""
    overall = (
        fighter.boxing + fighter.kicks + fighter.wrestling + 
        fighter.bjj + fighter.strength + fighter.speed +
        fighter.chin + fighter.heart
    ) // 8
    
    if fighter.boxing > fighter.wrestling and fighter.boxing > fighter.bjj:
        tendency = "Striker"
    elif fighter.wrestling > fighter.bjj:
        tendency = "Wrestler"
    elif fighter.bjj > fighter.wrestling:
        tendency = "Grappler"
    else:
        tendency = "Well-Rounded"
    
    return f"{fighter.name} - {tendency} (OVR: {overall})"


def calculate_overall(fighter: FighterAttributes) -> int:
    """Calculate overall rating for a fighter"""
    return (
        fighter.boxing + fighter.kicks + fighter.clinch_striking +
        fighter.striking_defense + fighter.wrestling + fighter.bjj +
        fighter.takedown_defense + fighter.strength + fighter.speed +
        fighter.cardio + fighter.chin + fighter.heart +
        fighter.fight_iq + fighter.composure
    ) // 14
