# systems/scouting.py
# Module: Scouting System
# Lines: ~650
#
# Handles fighter evaluation, comparison, and potential assessment.
# Used for signing decisions, fight preparation, and AI camp decisions.

"""
Cage Dynasty - Scouting System

This module handles fighter evaluation and analysis:
- Fighter strengths/weaknesses identification
- Fighter comparison and matchup analysis
- Potential assessment for prospects
- Scouting reports generation
- Style matchup advantages

DESIGN PHILOSOPHY:
    Free Agents vs Prospects create meaningful trade-offs:
    
    FREE AGENTS:
    - Known quantities with established records
    - Higher current ratings (55-85)
    - Older (26-34), closer to decline
    - Lower potential ceiling
    - Can compete immediately
    
    PROSPECTS:
    - Young and unproven (18-23)
    - Lower current ratings (40-65)
    - Higher potential ceiling (hidden)
    - Need development time
    - Cheaper, more loyal
    - Risk/reward proposition

USAGE:
    from systems.scouting import (
        scout_fighter,
        compare_fighters,
        get_matchup_analysis,
        assess_potential,
        ScoutingReport,
    )
    
    # Get full scouting report
    report = scout_fighter(fighter_data)
    
    # Compare two fighters
    comparison = compare_fighters(fighter1, fighter2)
    
    # Assess prospect potential
    potential = assess_potential(prospect_data)
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random


# ============================================================================
# CONSTANTS
# ============================================================================

# Potential grades and their stat ceiling multipliers
POTENTIAL_GRADES = {
    "Elite": {"min_ceiling": 88, "max_ceiling": 99, "description": "Future champion material"},
    "High": {"min_ceiling": 78, "max_ceiling": 87, "description": "Could be a contender"},
    "Average": {"min_ceiling": 65, "max_ceiling": 77, "description": "Solid roster filler"},
    "Limited": {"min_ceiling": 55, "max_ceiling": 64, "description": "Journeyman at best"},
    "Low": {"min_ceiling": 45, "max_ceiling": 54, "description": "Unlikely to develop much"},
}

# Age ranges for fighter types
PROSPECT_AGE_RANGE = (18, 23)
FREE_AGENT_AGE_RANGE = (24, 35)

# Development speed by age (younger = faster development)
DEVELOPMENT_MULTIPLIERS = {
    18: 1.5,
    19: 1.4,
    20: 1.3,
    21: 1.25,
    22: 1.2,
    23: 1.15,
    24: 1.1,
    25: 1.05,
    26: 1.0,  # Prime start - baseline
    27: 1.0,
    28: 0.95,
    29: 0.9,
    30: 0.85,
    31: 0.8,
    32: 0.75,
    33: 0.6,  # Decline
    34: 0.5,
    35: 0.4,
}

# Style matchup advantages (attacker_style -> defender_style -> advantage)
STYLE_MATCHUPS = {
    "Boxer": {
        "Wrestler": -10,  # Boxers struggle vs wrestlers
        "BJJ Specialist": -5,
        "Muay Thai": 5,
        "Brawler": 10,  # Technical beats wild
        "Counter Striker": -5,
    },
    "Wrestler": {
        "Boxer": 10,
        "Muay Thai": 5,
        "BJJ Specialist": -10,  # BJJ off their back
        "Sprawl and Brawl": -15,
        "Counter Striker": 5,
    },
    "BJJ Specialist": {
        "Wrestler": 10,  # Can work off back
        "Boxer": 5,
        "Muay Thai": 0,
        "Sprawl and Brawl": -10,
        "Sambo": -5,
    },
    "Muay Thai": {
        "Boxer": -5,  # Range issues
        "Wrestler": -5,
        "Brawler": 10,
        "Counter Striker": -10,  # Countered on kicks
        "Karate": 5,
    },
    "Brawler": {
        "Boxer": -10,
        "Counter Striker": -15,  # Gets timed
        "Wrestler": -5,
        "Pressure Fighter": 5,
        "Muay Thai": -10,
    },
    "Counter Striker": {
        "Brawler": 15,
        "Pressure Fighter": -10,  # Pressured out
        "Muay Thai": 10,
        "Boxer": 5,
        "Wrestler": -5,
    },
    "Pressure Fighter": {
        "Counter Striker": 10,
        "Boxer": 0,
        "Wrestler": -5,
        "BJJ Specialist": -5,
        "Brawler": 5,
    },
    "Sprawl and Brawl": {
        "Wrestler": 15,  # Built to stop wrestlers
        "BJJ Specialist": 10,
        "Boxer": -5,
        "Muay Thai": -5,
        "Counter Striker": -10,
    },
    "Sambo": {
        "BJJ Specialist": 5,
        "Wrestler": 5,
        "Boxer": 5,
        "Muay Thai": 0,
        "Brawler": 5,
    },
    "Karate": {
        "Brawler": 10,
        "Pressure Fighter": -10,
        "Wrestler": -10,
        "Muay Thai": -5,
        "Counter Striker": 5,
    },
}

# Attribute categories for analysis
PHYSICAL_ATTRS = ["strength", "speed", "cardio", "chin"]
STRIKING_ATTRS = ["boxing", "kicks", "clinch_striking"]
GRAPPLING_ATTRS = ["wrestling", "bjj", "takedown_defense"]
MENTAL_ATTRS = ["heart", "fight_iq", "composure"]

# ============================================================================
# TRAIT CLASHES - Narrative tension when specific traits interact
# ============================================================================

TRAIT_CLASHES = {
    # Power vs Durability
    ("Knockout Artist", "Iron Chin"): ("💥", "UNSTOPPABLE FORCE vs IMMOVABLE OBJECT"),
    ("Glass Cannon", "Iron Chin"): ("🎯", "POWER vs DURABILITY"),
    ("Killer Instinct", "Iron Chin"): ("🦈", "FINISHER vs SURVIVOR"),
    
    # Timing clashes
    ("Fast Starter", "Slow Starter"): ("⚠️", "DANGEROUS FIRST ROUND"),
    ("Fast Starter", "Cardio Machine"): ("⏱️", "SPRINT vs MARATHON"),
    ("Killer Instinct", "Cardio Machine"): ("🎭", "FINISH EARLY vs GRIND LATE"),
    
    # Stylistic clashes
    ("Pressure Fighter", "Counter Striker"): ("🎯", "BULL vs MATADOR"),
    ("Submission Ace", "Wrestler's Base"): ("♟️", "CHESS MATCH ON THE GROUND"),
    ("Southpaw", "Knockout Artist"): ("🔄", "ANGLES vs POWER"),
    
    # Mental clashes
    ("Big Game Hunter", "Choke Artist"): ("🧠", "MENTALITY MISMATCH"),
    ("Veteran Savvy", "Fast Starter"): ("📚", "EXPERIENCE vs EXPLOSIVENESS"),
    ("Killer Instinct", "Durable"): ("⚔️", "FINISHER vs SURVIVOR"),
    
    # Physical clashes
    ("Cardio Machine", "Knockout Artist"): ("🌊", "DEEP WATERS DANGER"),
    ("Durable", "Glass Cannon"): ("🛡️", "TANK vs GLASS CANNON"),
    
    # Southpaw specific
    ("Southpaw", "Southpaw"): ("🔀", "SOUTHPAW SHOWDOWN"),
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PotentialAssessment:
    """Assessment of a fighter's potential ceiling."""
    current_overall: int
    potential_ceiling: int
    potential_grade: str  # Elite, High, Average, Limited, Low
    years_to_peak: int
    development_speed: float  # Multiplier for training gains
    confidence: str  # How sure we are: "High", "Medium", "Low"
    notes: List[str] = field(default_factory=list)
    
    @property
    def upside(self) -> int:
        """How much room for growth."""
        return max(0, self.potential_ceiling - self.current_overall)
    
    @property
    def is_worth_developing(self) -> bool:
        """Whether this fighter is worth the investment."""
        return self.upside >= 15 and self.potential_grade in ("Elite", "High")


@dataclass
class StrengthWeakness:
    """A fighter's strength or weakness."""
    attribute: str
    value: int
    category: str  # Physical, Striking, Grappling, Mental
    description: str


@dataclass
class MatchupAnalysis:
    """Analysis of how two fighters match up."""
    fighter1_advantages: List[str]
    fighter2_advantages: List[str]
    style_advantage: int  # Positive = fighter1, negative = fighter2
    prediction: str  # "Fighter 1 favored", "Fighter 2 favored", "Even"
    key_factors: List[str]
    danger_zones: Dict[str, str]  # What each fighter should avoid
    
    # New: Trait clashes and keys to victory
    trait_clashes: List[str] = field(default_factory=list)  # Narrative X-Factors
    keys_to_victory_f1: List[str] = field(default_factory=list)  # How Fighter 1 wins
    keys_to_victory_f2: List[str] = field(default_factory=list)  # How Fighter 2 wins


@dataclass
class ScoutingReport:
    """Complete scouting report for a fighter."""
    fighter_id: str
    fighter_name: str
    
    # Basic info
    age: int
    weight_class: str
    record: Tuple[int, int, int]  # W-L-D
    overall_rating: int
    fighting_style: str
    
    # Analysis
    strengths: List[StrengthWeakness]
    weaknesses: List[StrengthWeakness]
    traits: List[str]
    trait_analysis: List[str]
    
    # Potential (for prospects)
    potential: Optional[PotentialAssessment] = None
    
    # Aggregate scores
    striking_score: int = 0
    grappling_score: int = 0
    physical_score: int = 0
    mental_score: int = 0
    
    # Recommendations
    ideal_matchups: List[str] = field(default_factory=list)
    bad_matchups: List[str] = field(default_factory=list)
    development_focus: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "age": self.age,
            "overall_rating": self.overall_rating,
            "fighting_style": self.fighting_style,
            "strengths": [(s.attribute, s.value) for s in self.strengths],
            "weaknesses": [(w.attribute, w.value) for w in self.weaknesses],
            "striking_score": self.striking_score,
            "grappling_score": self.grappling_score,
            "potential_grade": self.potential.potential_grade if self.potential else None,
        }


@dataclass 
class FighterComparison:
    """Side-by-side comparison of two fighters."""
    fighter1_name: str
    fighter2_name: str
    
    # Overall
    overall_edge: str  # "fighter1", "fighter2", "even"
    overall_diff: int
    
    # Category comparisons (positive = fighter1 advantage)
    striking_diff: int
    grappling_diff: int
    physical_diff: int
    mental_diff: int
    
    # Specific advantages
    fighter1_advantages: List[Tuple[str, int]]  # (attribute, margin)
    fighter2_advantages: List[Tuple[str, int]]
    
    # Style analysis
    style_advantage: int  # Positive = fighter1
    style_notes: List[str]
    
    # Prediction
    predicted_winner: str
    confidence: str  # "High", "Medium", "Low"
    method_prediction: str  # "KO", "SUB", "DEC"


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def get_attribute_value(fighter_data: Any, attr: str) -> int:
    """Safely get an attribute value from fighter data."""
    if hasattr(fighter_data, attr):
        return getattr(fighter_data, attr, 50)
    elif isinstance(fighter_data, dict):
        return fighter_data.get(attr, 50)
    return 50


def calculate_category_score(fighter_data: Any, attributes: List[str]) -> int:
    """Calculate average score for a category of attributes."""
    values = [get_attribute_value(fighter_data, attr) for attr in attributes]
    return sum(values) // len(values) if values else 50


def get_fighter_strengths(fighter_data: Any, top_n: int = 3) -> List[StrengthWeakness]:
    """Identify a fighter's top strengths."""
    all_attrs = []
    
    # Physical
    for attr in PHYSICAL_ATTRS:
        val = get_attribute_value(fighter_data, attr)
        all_attrs.append(StrengthWeakness(
            attribute=attr.replace("_", " ").title(),
            value=val,
            category="Physical",
            description=_get_strength_description(attr, val)
        ))
    
    # Striking
    for attr in STRIKING_ATTRS:
        val = get_attribute_value(fighter_data, attr)
        all_attrs.append(StrengthWeakness(
            attribute=attr.replace("_", " ").title(),
            value=val,
            category="Striking",
            description=_get_strength_description(attr, val)
        ))
    
    # Grappling
    for attr in GRAPPLING_ATTRS:
        val = get_attribute_value(fighter_data, attr)
        all_attrs.append(StrengthWeakness(
            attribute=attr.replace("_", " ").title(),
            value=val,
            category="Grappling",
            description=_get_strength_description(attr, val)
        ))
    
    # Mental
    for attr in MENTAL_ATTRS:
        val = get_attribute_value(fighter_data, attr)
        all_attrs.append(StrengthWeakness(
            attribute=attr.replace("_", " ").title(),
            value=val,
            category="Mental",
            description=_get_strength_description(attr, val)
        ))
    
    # Sort by value descending, take top N
    all_attrs.sort(key=lambda x: x.value, reverse=True)
    return all_attrs[:top_n]


def get_fighter_weaknesses(fighter_data: Any, top_n: int = 3) -> List[StrengthWeakness]:
    """Identify a fighter's biggest weaknesses."""
    all_attrs = []
    
    for attr in PHYSICAL_ATTRS + STRIKING_ATTRS + GRAPPLING_ATTRS + MENTAL_ATTRS:
        val = get_attribute_value(fighter_data, attr)
        all_attrs.append(StrengthWeakness(
            attribute=attr.replace("_", " ").title(),
            value=val,
            category=_get_attr_category(attr),
            description=_get_weakness_description(attr, val)
        ))
    
    # Sort by value ascending, take bottom N
    all_attrs.sort(key=lambda x: x.value)
    return all_attrs[:top_n]


def _get_attr_category(attr: str) -> str:
    """Get category for an attribute."""
    if attr in PHYSICAL_ATTRS:
        return "Physical"
    elif attr in STRIKING_ATTRS:
        return "Striking"
    elif attr in GRAPPLING_ATTRS:
        return "Grappling"
    else:
        return "Mental"


def _get_strength_description(attr: str, value: int) -> str:
    """Get description for a strength."""
    descriptions = {
        "strength": "Powerful striker with knockout potential",
        "speed": "Quick hands and feet, hard to time",
        "cardio": "Can maintain pace deep into fights",
        "chin": "Can absorb punishment and keep coming",
        "boxing": "Crisp hands, excellent combinations",
        "kicks": "Dangerous leg and body kicks",
        "clinch_striking": "Devastating in the clinch",
        "wrestling": "Elite takedowns and control",
        "bjj": "Dangerous submission threat",
        "takedown_defense": "Very hard to take down",
        "heart": "Never gives up, digs deep when hurt",
        "fight_iq": "Reads opponents well, adapts quickly",
        "composure": "Stays calm under pressure",
    }
    base = descriptions.get(attr, "Notable attribute")
    if value >= 85:
        return f"Elite: {base}"
    elif value >= 75:
        return base
    else:
        return f"Solid: {base}"


def _get_weakness_description(attr: str, value: int) -> str:
    """Get description for a weakness."""
    descriptions = {
        "strength": "Lacks power, struggles to hurt opponents",
        "speed": "Slow reactions, gets timed easily",
        "cardio": "Fades in later rounds",
        "chin": "Vulnerable to being hurt/finished",
        "boxing": "Limited hands, predictable striking",
        "kicks": "Doesn't use kicks effectively",
        "clinch_striking": "Uncomfortable in clinch exchanges",
        "wrestling": "Poor takedown offense",
        "bjj": "Limited ground game, avoid the mat",
        "takedown_defense": "Gets taken down easily",
        "heart": "May quit when things get tough",
        "fight_iq": "Makes poor decisions in the cage",
        "composure": "Panics when pressured or hurt",
    }
    base = descriptions.get(attr, "Area of concern")
    if value <= 40:
        return f"Major liability: {base}"
    elif value <= 50:
        return f"Weakness: {base}"
    else:
        return f"Below average: {base}"


def assess_potential(
    fighter_data: Any,
    scouting_accuracy: float = 0.8
) -> PotentialAssessment:
    """
    Assess a prospect's potential ceiling.
    
    Args:
        fighter_data: Fighter to assess
        scouting_accuracy: How accurate the assessment is (0.0-1.0)
            Higher accuracy reveals true potential better
    
    Returns:
        PotentialAssessment with ceiling estimate
    """
    age = get_attribute_value(fighter_data, "age")
    current = get_attribute_value(fighter_data, "overall_rating")
    
    # Base potential from current + growth room
    # Younger fighters have more unknown potential
    age_factor = max(0, 26 - age) * 2  # Up to 16 points for youngest
    
    # Check for traits that indicate potential
    traits = getattr(fighter_data, "traits", []) or []
    trait_bonus = 0
    trait_notes = []
    
    if "Gym Rat" in traits:
        trait_bonus += 8
        trait_notes.append("Gym Rat trait suggests high development potential")
    if "Fast Learner" in traits:
        trait_bonus += 10
        trait_notes.append("Fast Learner - could develop very quickly")
    if "Injury Prone" in traits:
        trait_bonus -= 5
        trait_notes.append("Injury Prone - development may be interrupted")
    if "Veteran Savvy" in traits:
        trait_notes.append("Already shows veteran instincts despite age")
    
    # Calculate true potential ceiling
    true_ceiling = min(99, current + age_factor + trait_bonus + random.randint(5, 20))
    
    # Apply scouting accuracy - add noise for less accurate scouting
    noise_range = int((1.0 - scouting_accuracy) * 15)
    scouted_ceiling = true_ceiling + random.randint(-noise_range, noise_range)
    scouted_ceiling = max(current, min(99, scouted_ceiling))
    
    # Determine potential grade
    if scouted_ceiling >= 88:
        grade = "Elite"
    elif scouted_ceiling >= 78:
        grade = "High"
    elif scouted_ceiling >= 65:
        grade = "Average"
    elif scouted_ceiling >= 55:
        grade = "Limited"
    else:
        grade = "Low"
    
    # Development speed based on age
    dev_speed = DEVELOPMENT_MULTIPLIERS.get(age, 1.0)
    
    # Years to reach potential
    gap = scouted_ceiling - current
    years_to_peak = max(1, gap // 8) if gap > 0 else 0
    
    # Confidence based on scouting accuracy and age
    if scouting_accuracy >= 0.9:
        confidence = "High"
    elif scouting_accuracy >= 0.7:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    # Additional notes
    notes = trait_notes.copy()
    if age <= 20:
        notes.append(f"Very young ({age}) - high upside but needs time")
    if current >= 65:
        notes.append("Already polished for a prospect")
    if gap >= 25:
        notes.append("Huge development ceiling if potential is reached")
    if dev_speed >= 1.3:
        notes.append(f"Should develop {int((dev_speed-1)*100)}% faster than average")
    
    return PotentialAssessment(
        current_overall=current,
        potential_ceiling=scouted_ceiling,
        potential_grade=grade,
        years_to_peak=years_to_peak,
        development_speed=dev_speed,
        confidence=confidence,
        notes=notes,
    )


def compare_fighters(fighter1: Any, fighter2: Any) -> FighterComparison:
    """
    Create detailed comparison between two fighters.
    
    Returns FighterComparison with analysis of how they match up.
    """
    f1_name = getattr(fighter1, "name", "Fighter 1")
    f2_name = getattr(fighter2, "name", "Fighter 2")
    
    # Overall ratings
    f1_overall = get_attribute_value(fighter1, "overall_rating")
    f2_overall = get_attribute_value(fighter2, "overall_rating")
    overall_diff = f1_overall - f2_overall
    
    if overall_diff > 5:
        overall_edge = "fighter1"
    elif overall_diff < -5:
        overall_edge = "fighter2"
    else:
        overall_edge = "even"
    
    # Category scores
    f1_striking = calculate_category_score(fighter1, ["boxing", "kicks"])
    f2_striking = calculate_category_score(fighter2, ["boxing", "kicks"])
    striking_diff = f1_striking - f2_striking
    
    f1_grappling = calculate_category_score(fighter1, ["wrestling", "bjj", "takedown_defense"])
    f2_grappling = calculate_category_score(fighter2, ["wrestling", "bjj", "takedown_defense"])
    grappling_diff = f1_grappling - f2_grappling
    
    f1_physical = calculate_category_score(fighter1, PHYSICAL_ATTRS)
    f2_physical = calculate_category_score(fighter2, PHYSICAL_ATTRS)
    physical_diff = f1_physical - f2_physical
    
    f1_mental = calculate_category_score(fighter1, MENTAL_ATTRS)
    f2_mental = calculate_category_score(fighter2, MENTAL_ATTRS)
    mental_diff = f1_mental - f2_mental
    
    # Specific attribute advantages
    f1_advantages = []
    f2_advantages = []
    
    all_attrs = PHYSICAL_ATTRS + STRIKING_ATTRS + GRAPPLING_ATTRS + MENTAL_ATTRS
    for attr in all_attrs:
        f1_val = get_attribute_value(fighter1, attr)
        f2_val = get_attribute_value(fighter2, attr)
        diff = f1_val - f2_val
        
        if diff >= 10:
            f1_advantages.append((attr.replace("_", " ").title(), diff))
        elif diff <= -10:
            f2_advantages.append((attr.replace("_", " ").title(), -diff))
    
    # Style matchup
    f1_style = getattr(fighter1, "fighting_style", "")
    f2_style = getattr(fighter2, "fighting_style", "")
    style_advantage = get_style_advantage(f1_style, f2_style)
    
    style_notes = []
    if style_advantage > 5:
        style_notes.append(f"{f1_name}'s {f1_style} style matches up well vs {f2_style}")
    elif style_advantage < -5:
        style_notes.append(f"{f2_name}'s {f2_style} style matches up well vs {f1_style}")
    else:
        style_notes.append("Styles are relatively neutral matchup")
    
    # Prediction
    total_advantage = (overall_diff * 2) + striking_diff + grappling_diff + style_advantage
    
    if total_advantage > 15:
        predicted_winner = f1_name
        confidence = "High"
    elif total_advantage > 5:
        predicted_winner = f1_name
        confidence = "Medium"
    elif total_advantage < -15:
        predicted_winner = f2_name
        confidence = "High"
    elif total_advantage < -5:
        predicted_winner = f2_name
        confidence = "Medium"
    else:
        predicted_winner = "Toss-up"
        confidence = "Low"
    
    # Method prediction
    if striking_diff > 10 or style_advantage > 10:
        method = "KO/TKO"
    elif grappling_diff > 10:
        method = "SUB/DEC"
    elif grappling_diff < -10:
        method = "SUB/DEC"
    else:
        method = "Decision"
    
    return FighterComparison(
        fighter1_name=f1_name,
        fighter2_name=f2_name,
        overall_edge=overall_edge,
        overall_diff=overall_diff,
        striking_diff=striking_diff,
        grappling_diff=grappling_diff,
        physical_diff=physical_diff,
        mental_diff=mental_diff,
        fighter1_advantages=f1_advantages,
        fighter2_advantages=f2_advantages,
        style_advantage=style_advantage,
        style_notes=style_notes,
        predicted_winner=predicted_winner,
        confidence=confidence,
        method_prediction=method,
    )


def get_style_advantage(style1: str, style2: str) -> int:
    """
    Get style matchup advantage.
    
    Returns positive if style1 has advantage, negative if style2.
    """
    if not style1 or not style2:
        return 0
    
    # Normalize style names
    style1 = style1.strip()
    style2 = style2.strip()
    
    # Check direct matchup
    if style1 in STYLE_MATCHUPS:
        if style2 in STYLE_MATCHUPS[style1]:
            return STYLE_MATCHUPS[style1][style2]
    
    return 0


# ============================================================================
# TRAIT CLASHES & KEYS TO VICTORY
# ============================================================================

def detect_trait_clashes(traits1: List[str], traits2: List[str]) -> List[str]:
    """
    Detect narrative clashes between fighter traits.
    
    These create compelling storylines and X-factors in matchups.
    
    Args:
        traits1: List of Fighter 1's traits
        traits2: List of Fighter 2's traits
        
    Returns:
        List of narrative clash descriptions
    """
    clashes = []
    t1_set = set(traits1) if traits1 else set()
    t2_set = set(traits2) if traits2 else set()
    
    for (trait_a, trait_b), (emoji, narrative) in TRAIT_CLASHES.items():
        # Check Direction 1 (Fighter 1 has trait_a, Fighter 2 has trait_b)
        if trait_a in t1_set and trait_b in t2_set:
            clashes.append(f"{emoji} {narrative}")
        # Check Direction 2 (Fighter 1 has trait_b, Fighter 2 has trait_a)
        elif trait_b in t1_set and trait_a in t2_set:
            clashes.append(f"{emoji} {narrative}")
    
    return clashes


def generate_keys_to_victory(
    my_name: str,
    my_stats: Dict[str, int],
    opp_name: str,
    opp_stats: Dict[str, int],
    my_traits: Optional[List[str]] = None,
    opp_traits: Optional[List[str]] = None,
) -> List[str]:
    """
    Generate actionable "Keys to Victory" based on stat comparisons and traits.
    
    These give the player strategic guidance, not just "you're better."
    
    Args:
        my_name: Fighter's first name
        my_stats: Dictionary of fighter's attributes
        opp_name: Opponent's first name
        opp_stats: Dictionary of opponent's attributes
        my_traits: Optional list of fighter's traits
        opp_traits: Optional list of opponent's traits
        
    Returns:
        List of strategic keys to victory
    """
    keys = []
    my_traits = my_traits or []
    opp_traits = opp_traits or []
    
    # Get stats with defaults
    my_cardio = my_stats.get("cardio", 50)
    opp_cardio = opp_stats.get("cardio", 50)
    my_chin = my_stats.get("chin", 50)
    opp_chin = opp_stats.get("chin", 50)
    my_boxing = my_stats.get("boxing", 50)
    opp_boxing = opp_stats.get("boxing", 50)
    my_kicks = my_stats.get("kicks", 50)
    opp_kicks = opp_stats.get("kicks", 50)
    my_wrestling = my_stats.get("wrestling", 50)
    opp_wrestling = opp_stats.get("wrestling", 50)
    my_bjj = my_stats.get("bjj", 50)
    opp_bjj = opp_stats.get("bjj", 50)
    my_tdd = my_stats.get("takedown_defense", 50)
    opp_tdd = opp_stats.get("takedown_defense", 50)
    my_speed = my_stats.get("speed", 50)
    opp_speed = opp_stats.get("speed", 50)
    my_strength = my_stats.get("strength", 50)
    opp_strength = opp_stats.get("strength", 50)
    
    # === TRAIT-BASED KEYS ===
    
    # Killer Instinct advantage
    if "Killer Instinct" in my_traits:
        keys.append(f"🦈 FINISH HIM: Your killer instinct activates when {opp_name} is hurt")
    
    # Southpaw advantage (if opponent isn't also southpaw)
    if "Southpaw" in my_traits and "Southpaw" not in opp_traits:
        keys.append(f"🔄 SOUTHPAW ANGLES: Use stance to create openings")
    elif "Southpaw" not in my_traits and "Southpaw" in opp_traits:
        keys.append(f"⚠️ SOUTHPAW ALERT: Circle away from {opp_name}'s power hand")
    
    # Opponent has Glass Cannon + I have power
    if "Glass Cannon" in opp_traits and my_strength > 65:
        keys.append(f"💥 TARGET THE CHIN: {opp_name} can't take a shot")
    
    # I'm a Fast Starter, they're a Slow Starter
    if "Fast Starter" in my_traits or "Slow Starter" in opp_traits:
        keys.append(f"⚡ BLITZ EARLY: Win this fight in Round 1")
    
    # They have Killer Instinct - don't get hurt
    if "Killer Instinct" in opp_traits:
        keys.append(f"🛡️ STAY SAFE: {opp_name} is lethal when you're hurt")
    
    # === STAT-BASED KEYS ===
    
    # 1. Cardio Advantage - Pace strategy
    if my_cardio > opp_cardio + 15:
        keys.append(f"🌊 PACE STRATEGY: Drag {opp_name} into deep waters (Rounds 2-3)")
    elif my_cardio < opp_cardio - 15:
        keys.append(f"⚡ EARLY PRESSURE: Don't let this go to later rounds")
    
    # 2. Chin Vulnerability - Headhunting opportunity
    if opp_chin < 55 and my_boxing > 65:
        keys.append(f"🎯 HEADHUNTING: {opp_name}'s chin is suspect ({opp_chin})")
    
    # 3. Leg Kick Vulnerability
    if my_kicks > 70 and opp_kicks < 60:
        keys.append(f"🦵 CHOP THE TREE: Heavy focus on leg kicks")
    
    # 4. Wrestling/Takedown Gap
    if my_wrestling > opp_tdd + 10:
        diff = my_wrestling - opp_tdd
        keys.append(f"⬇️ GROUND CONTROL: Take {opp_name} down early (+{diff} advantage)")
    elif opp_wrestling > my_tdd + 10:
        keys.append(f"🧱 STAY STANDING: Sprawl and punish failed takedowns")
    
    # 5. Speed Advantage
    if my_speed > opp_speed + 12:
        keys.append(f"💨 HIT & MOVE: Use speed advantage, don't brawl")
    
    # 6. Power/Strength Advantage
    if my_strength > opp_strength + 12:
        keys.append(f"💪 IMPOSE PHYSICALITY: Use strength in clinch and grappling")
    
    # 7. BJJ Trap
    if my_bjj > opp_bjj + 15 and opp_wrestling > 70:
        keys.append(f"🐍 BJJ TRAP: Let {opp_name} take you down, then submit")
    
    # 8. Counter Opportunity (if opponent is aggressive and you have better defense)
    my_def = my_stats.get("striking_defense", 50)
    if my_def > 75 and opp_boxing > 70:
        keys.append(f"🎯 COUNTER OPPORTUNITY: Let {opp_name} lead, time the counter")
    
    # Limit to top 4 keys
    return keys[:4]


def get_matchup_analysis(fighter1: Any, fighter2: Any) -> MatchupAnalysis:
    """
    Get detailed matchup analysis for fight preparation.
    
    Now includes X-Factors (trait clashes) and Keys to Victory.
    """
    f1_name = getattr(fighter1, "name", "Fighter 1").split()[0]
    f2_name = getattr(fighter2, "name", "Fighter 2").split()[0]
    
    comparison = compare_fighters(fighter1, fighter2)
    
    f1_advantages = []
    f2_advantages = []
    key_factors = []
    danger_zones = {}
    
    # Analyze striking
    if comparison.striking_diff > 10:
        f1_advantages.append(f"{f1_name} has clear striking advantage (+{comparison.striking_diff})")
        key_factors.append(f"{f2_name} should avoid extended striking exchanges")
    elif comparison.striking_diff < -10:
        f2_advantages.append(f"{f2_name} has clear striking advantage (+{-comparison.striking_diff})")
        key_factors.append(f"{f1_name} should avoid extended striking exchanges")
    
    # Analyze grappling
    if comparison.grappling_diff > 10:
        f1_advantages.append(f"{f1_name} has clear grappling advantage (+{comparison.grappling_diff})")
        key_factors.append(f"{f1_name} should look to take the fight to the ground")
        danger_zones[f2_name] = "Ground fighting"
    elif comparison.grappling_diff < -10:
        f2_advantages.append(f"{f2_name} has clear grappling advantage (+{-comparison.grappling_diff})")
        key_factors.append(f"{f2_name} should look to take the fight to the ground")
        danger_zones[f1_name] = "Ground fighting"
    
    # Cardio analysis
    f1_cardio = get_attribute_value(fighter1, "cardio")
    f2_cardio = get_attribute_value(fighter2, "cardio")
    if f1_cardio > f2_cardio + 10:
        f1_advantages.append(f"{f1_name} should have better gas tank")
        key_factors.append("Fight may favor later rounds for " + f1_name)
    elif f2_cardio > f1_cardio + 10:
        f2_advantages.append(f"{f2_name} should have better gas tank")
        key_factors.append("Fight may favor later rounds for " + f2_name)
    
    # Chin analysis
    f1_chin = get_attribute_value(fighter1, "chin")
    f2_chin = get_attribute_value(fighter2, "chin")
    if f1_chin < 50:
        f2_advantages.append(f"{f1_name} has a suspect chin")
        danger_zones[f1_name] = "Power shots"
    if f2_chin < 50:
        f1_advantages.append(f"{f2_name} has a suspect chin")
        danger_zones[f2_name] = "Power shots"
    
    # Style advantage
    style_adv = comparison.style_advantage
    if style_adv > 5:
        f1_advantages.append("Stylistic advantage in this matchup")
    elif style_adv < -5:
        f2_advantages.append("Stylistic advantage in this matchup")
    
    # Prediction
    if comparison.predicted_winner == f1_name or comparison.overall_edge == "fighter1":
        prediction = f"{f1_name} favored"
    elif comparison.predicted_winner == f2_name or comparison.overall_edge == "fighter2":
        prediction = f"{f2_name} favored"
    else:
        prediction = "Even matchup"
    
    # === NEW: Trait Clashes (X-Factors) ===
    f1_traits = getattr(fighter1, "traits", []) or []
    f2_traits = getattr(fighter2, "traits", []) or []
    trait_clashes = detect_trait_clashes(f1_traits, f2_traits)
    
    # === NEW: Keys to Victory ===
    # Build stat dictionaries for each fighter
    f1_stats = {
        "cardio": get_attribute_value(fighter1, "cardio"),
        "chin": get_attribute_value(fighter1, "chin"),
        "boxing": get_attribute_value(fighter1, "boxing"),
        "kicks": get_attribute_value(fighter1, "kicks"),
        "wrestling": get_attribute_value(fighter1, "wrestling"),
        "bjj": get_attribute_value(fighter1, "bjj"),
        "takedown_defense": get_attribute_value(fighter1, "takedown_defense"),
        "speed": get_attribute_value(fighter1, "speed"),
        "strength": get_attribute_value(fighter1, "strength"),
        "striking_defense": get_attribute_value(fighter1, "striking_defense"),
    }
    f2_stats = {
        "cardio": get_attribute_value(fighter2, "cardio"),
        "chin": get_attribute_value(fighter2, "chin"),
        "boxing": get_attribute_value(fighter2, "boxing"),
        "kicks": get_attribute_value(fighter2, "kicks"),
        "wrestling": get_attribute_value(fighter2, "wrestling"),
        "bjj": get_attribute_value(fighter2, "bjj"),
        "takedown_defense": get_attribute_value(fighter2, "takedown_defense"),
        "speed": get_attribute_value(fighter2, "speed"),
        "strength": get_attribute_value(fighter2, "strength"),
        "striking_defense": get_attribute_value(fighter2, "striking_defense"),
    }
    
    keys_f1 = generate_keys_to_victory(f1_name, f1_stats, f2_name, f2_stats, f1_traits, f2_traits)
    keys_f2 = generate_keys_to_victory(f2_name, f2_stats, f1_name, f1_stats, f2_traits, f1_traits)
    
    return MatchupAnalysis(
        fighter1_advantages=f1_advantages,
        fighter2_advantages=f2_advantages,
        style_advantage=style_adv,
        prediction=prediction,
        key_factors=key_factors,
        danger_zones=danger_zones,
        trait_clashes=trait_clashes,
        keys_to_victory_f1=keys_f1,
        keys_to_victory_f2=keys_f2,
    )


def scout_fighter(fighter_data: Any, is_prospect: bool = False) -> ScoutingReport:
    """
    Generate complete scouting report for a fighter.
    
    Args:
        fighter_data: Fighter to scout
        is_prospect: Whether to include potential assessment
        
    Returns:
        Complete ScoutingReport
    """
    fighter_id = getattr(fighter_data, "fighter_id", "unknown")
    name = getattr(fighter_data, "name", "Unknown")
    age = get_attribute_value(fighter_data, "age")
    weight_class = getattr(fighter_data, "weight_class", "Unknown")
    wins = get_attribute_value(fighter_data, "wins")
    losses = get_attribute_value(fighter_data, "losses")
    draws = get_attribute_value(fighter_data, "draws")
    overall = get_attribute_value(fighter_data, "overall_rating")
    style = getattr(fighter_data, "fighting_style", "Unknown")
    traits = getattr(fighter_data, "traits", []) or []
    
    # Get strengths and weaknesses
    strengths = get_fighter_strengths(fighter_data)
    weaknesses = get_fighter_weaknesses(fighter_data)
    
    # Calculate category scores
    striking_score = calculate_category_score(fighter_data, ["boxing", "kicks"])
    grappling_score = calculate_category_score(fighter_data, ["wrestling", "bjj", "takedown_defense"])
    physical_score = calculate_category_score(fighter_data, PHYSICAL_ATTRS)
    mental_score = calculate_category_score(fighter_data, MENTAL_ATTRS)
    
    # Analyze traits
    trait_analysis = []
    for trait in traits:
        analysis = _analyze_trait(trait)
        if analysis:
            trait_analysis.append(analysis)
    
    # Potential assessment if prospect
    potential = None
    if is_prospect or age <= 24:
        potential = assess_potential(fighter_data)
    
    # Recommendations
    ideal_matchups = []
    bad_matchups = []
    development_focus = []
    
    # Determine ideal/bad matchups based on style
    if striking_score > grappling_score + 10:
        ideal_matchups.append("Other strikers")
        ideal_matchups.append("Fighters with poor TDD")
        bad_matchups.append("Elite wrestlers")
        bad_matchups.append("Grapplers with good takedowns")
    elif grappling_score > striking_score + 10:
        ideal_matchups.append("One-dimensional strikers")
        ideal_matchups.append("Fighters with poor cardio")
        bad_matchups.append("Sprawl and brawl fighters")
        bad_matchups.append("Fighters with elite TDD")
    
    # Development focus based on weaknesses
    for weakness in weaknesses[:2]:
        if weakness.value < 60:
            development_focus.append(f"Improve {weakness.attribute}")
    
    return ScoutingReport(
        fighter_id=fighter_id,
        fighter_name=name,
        age=age,
        weight_class=weight_class,
        record=(wins, losses, draws),
        overall_rating=overall,
        fighting_style=style,
        strengths=strengths,
        weaknesses=weaknesses,
        traits=traits,
        trait_analysis=trait_analysis,
        potential=potential,
        striking_score=striking_score,
        grappling_score=grappling_score,
        physical_score=physical_score,
        mental_score=mental_score,
        ideal_matchups=ideal_matchups,
        bad_matchups=bad_matchups,
        development_focus=development_focus,
    )


def _analyze_trait(trait: str) -> Optional[str]:
    """Get analysis/implication of a trait."""
    analyses = {
        "Glass Cannon": "High risk/reward - can finish but can be finished",
        "Iron Chin": "Can absorb punishment and survive bad moments",
        "Cardio Machine": "Will stay fresh in later rounds",
        "Knockout Artist": "Always dangerous, can end it with one shot",
        "Submission Ace": "Must avoid ground fighting or risk getting tapped",
        "Wrestler's Base": "Very hard to take down",
        "Pressure Fighter": "Will push forward relentlessly",
        "Counter Striker": "Dangerous to lead against, waits for mistakes",
        "Fast Starter": "Dangerous early, may fade",
        "Slow Starter": "Survives early, gets better as fight progresses",
        "Big Game Hunter": "Rises to the occasion in big fights",
        "Choke Artist": "May crumble under pressure in big moments",
        "Gym Rat": "Dedicated trainer, will keep improving",
        "Injury Prone": "Risk of setbacks due to injuries",
        "Durable": "Rarely gets hurt, consistent performer",
        "Veteran Savvy": "Smart fighter, won't make rookie mistakes",
        "Killer Instinct": "Lethal when opponent is hurt - finishes fights",
        "Southpaw": "Unorthodox stance creates tricky angles",
    }
    return analyses.get(trait)


# ============================================================================
# PROSPECT VS FREE AGENT HELPERS
# ============================================================================

def is_prospect(fighter_data: Any) -> bool:
    """Determine if fighter should be classified as a prospect."""
    age = get_attribute_value(fighter_data, "age")
    wins = get_attribute_value(fighter_data, "wins")
    losses = get_attribute_value(fighter_data, "losses")
    
    # Prospect if young with limited experience
    return age <= 23 and (wins + losses) <= 5


def get_signing_recommendation(fighter_data: Any) -> Dict[str, Any]:
    """
    Get recommendation for signing a fighter.
    
    Returns dict with:
    - recommendation: "Sign", "Pass", "Consider"
    - reasons: List of reasons
    - risk_level: "Low", "Medium", "High"
    - value_type: "Immediate", "Development", "Neither"
    """
    age = get_attribute_value(fighter_data, "age")
    overall = get_attribute_value(fighter_data, "overall_rating")
    
    reasons = []
    
    # Determine value type
    if age <= 23 and overall < 65:
        value_type = "Development"
        potential = assess_potential(fighter_data)
        
        if potential.potential_grade in ("Elite", "High"):
            recommendation = "Sign"
            reasons.append(f"{potential.potential_grade} potential ceiling ({potential.potential_ceiling})")
            reasons.append(f"Young ({age}) with room to grow")
            risk_level = "Medium"
        elif potential.potential_grade == "Average":
            recommendation = "Consider"
            reasons.append("Average ceiling but could be useful depth")
            risk_level = "Medium"
        else:
            recommendation = "Pass"
            reasons.append("Limited upside doesn't justify development time")
            risk_level = "Low"
    
    elif overall >= 70:
        value_type = "Immediate"
        recommendation = "Sign"
        reasons.append(f"High current rating ({overall}) - can compete now")
        
        if age >= 32:
            reasons.append(f"Warning: Age {age} means limited prime years left")
            risk_level = "Medium"
        else:
            risk_level = "Low"
    
    elif overall >= 60:
        value_type = "Immediate"
        recommendation = "Consider"
        reasons.append(f"Solid rating ({overall}) for roster depth")
        
        if age <= 28:
            reasons.append("Still has some development potential")
            risk_level = "Low"
        else:
            reasons.append(f"Age {age} - what you see is what you get")
            risk_level = "Low"
    
    else:
        value_type = "Neither"
        recommendation = "Pass"
        reasons.append(f"Low rating ({overall}) with limited upside")
        risk_level = "Low"
    
    return {
        "recommendation": recommendation,
        "reasons": reasons,
        "risk_level": risk_level,
        "value_type": value_type,
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "PotentialAssessment",
    "StrengthWeakness",
    "MatchupAnalysis",
    "ScoutingReport",
    "FighterComparison",
    
    # Core functions
    "scout_fighter",
    "compare_fighters",
    "get_matchup_analysis",
    "assess_potential",
    
    # Helper functions
    "get_fighter_strengths",
    "get_fighter_weaknesses",
    "get_style_advantage",
    "calculate_category_score",
    "is_prospect",
    "get_signing_recommendation",
    
    # Constants
    "POTENTIAL_GRADES",
    "STYLE_MATCHUPS",
    "DEVELOPMENT_MULTIPLIERS",
]
