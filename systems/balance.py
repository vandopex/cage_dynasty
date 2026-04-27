# systems/balance.py
# Module: Fight Balance System
# Lines: ~450
# Updated: Balance Pass v2
#
# Centralizes all fight balance modifiers:
# - Mentality effects on combat
# - Champion's advantage
# - Title fight modifiers
# - Combined trait + mentality calculations

"""
Cage Dynasty - Fight Balance System

This module provides the unified balance calculations for fights.
All combat probability modifiers flow through here.

BALANCE VALUES v2:
==================
MENTALITY MODIFIERS:
- WARRIOR: +2.0% win bonus (lives to fight)
- KILLER: +1.5% win bonus (aggressive advantage)
- GLORY_SEEKER: +0.5% win bonus (motivated by big stage)
- TECHNICIAN: +0.0% win bonus (methodical, no bonus)
- JOURNEYMAN: +0.0% win bonus (neutral)
- BUSINESSMAN: -2.5% win PENALTY (plays it safe)

TITLE FIGHT MODIFIERS:
- Champion's Advantage: +5% for defending champion
- Big Fight Bonus: Applied from Big Game Hunter trait
- Big Fight Penalty: Applied from Choke Artist trait

USAGE:
    from systems.balance import (
        get_mentality_modifier,
        get_champion_advantage,
        calculate_fight_probability,
    )
    
    # Get mentality combat modifier
    mod = get_mentality_modifier(FighterMentality.WARRIOR)
    
    # Calculate full fight probability
    prob = calculate_fight_probability(fighter1, fighter2, context)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import random

# Import from sibling modules
try:
    from simulation.ai_behavior import FighterMentality, FinishingInstinct
except ImportError:
    # Fallback for standalone testing
    class FighterMentality(Enum):
        WARRIOR = "warrior"
        BUSINESSMAN = "businessman"
        GLORY_SEEKER = "glory_seeker"
        JOURNEYMAN = "journeyman"
        KILLER = "killer"
        TECHNICIAN = "technician"
    
    class FinishingInstinct(Enum):
        KILLER_INSTINCT = "killer"
        MEASURED = "measured"
        CONSERVATIVE = "conservative"
        POINT_FIGHTER = "point_fighter"


# ============================================================================
# MENTALITY BALANCE VALUES
# ============================================================================

# Combat win probability modifiers by mentality
# Positive = more likely to win, Negative = less likely
MENTALITY_COMBAT_MODIFIERS: Dict[FighterMentality, float] = {
    FighterMentality.WARRIOR: 0.020,        # +2.0% - Lives to fight
    FighterMentality.KILLER: 0.015,         # +1.5% - Aggressive advantage
    FighterMentality.GLORY_SEEKER: 0.005,   # +0.5% - Motivated by big stage
    FighterMentality.TECHNICIAN: 0.000,     # +0.0% - Methodical, neutral
    FighterMentality.JOURNEYMAN: 0.000,     # +0.0% - Steady, neutral
    FighterMentality.BUSINESSMAN: -0.025,   # -2.5% - Plays it safe (PENALTY)
}

# Finish rate modifiers by mentality (when winning)
MENTALITY_FINISH_MODIFIERS: Dict[FighterMentality, float] = {
    FighterMentality.WARRIOR: 0.00,         # Warriors don't stop, but also take damage
    FighterMentality.KILLER: 0.08,          # +8% finish rate - goes for the kill
    FighterMentality.GLORY_SEEKER: 0.03,    # +3% - wants highlight reel
    FighterMentality.TECHNICIAN: -0.05,     # -5% - happy to outpoint
    FighterMentality.JOURNEYMAN: -0.03,     # -3% - content with decisions
    FighterMentality.BUSINESSMAN: -0.05,    # -5% - takes no risks
}

# Finishing instinct modifiers
FINISHING_INSTINCT_MODIFIERS: Dict[FinishingInstinct, float] = {
    FinishingInstinct.KILLER_INSTINCT: 0.10,  # +10% finish rate
    FinishingInstinct.MEASURED: 0.02,          # +2% - tests then finishes
    FinishingInstinct.CONSERVATIVE: -0.05,     # -5% - takes no risks
    FinishingInstinct.POINT_FIGHTER: -0.08,    # -8% - happy with decisions
}


# ============================================================================
# TITLE FIGHT BALANCE
# ============================================================================

# Champion's advantage in title fights
CHAMPION_ADVANTAGE = 0.025  # +2.5% win probability for defending champion

# Title fight intensity modifier (more careful fighting)
TITLE_FIGHT_VARIANCE_REDUCTION = 0.02  # Reduces variance slightly


# ============================================================================
# BALANCE FUNCTIONS
# ============================================================================

def get_mentality_modifier(mentality: FighterMentality) -> float:
    """
    Get combat win probability modifier for a mentality.
    
    Args:
        mentality: Fighter's core mentality
        
    Returns:
        Win probability modifier (e.g., 0.02 = +2%)
    """
    return MENTALITY_COMBAT_MODIFIERS.get(mentality, 0.0)


def get_mentality_finish_modifier(mentality: FighterMentality) -> float:
    """
    Get finish rate modifier for a mentality.
    
    Args:
        mentality: Fighter's core mentality
        
    Returns:
        Finish rate modifier (e.g., 0.08 = +8%)
    """
    return MENTALITY_FINISH_MODIFIERS.get(mentality, 0.0)


def get_finishing_instinct_modifier(instinct: FinishingInstinct) -> float:
    """
    Get finish rate modifier for finishing instinct.
    
    Args:
        instinct: Fighter's finishing instinct
        
    Returns:
        Finish rate modifier
    """
    return FINISHING_INSTINCT_MODIFIERS.get(instinct, 0.0)


def get_champion_advantage(
    is_title_fight: bool,
    fighter_is_champion: bool,
) -> float:
    """
    Get champion's home advantage modifier.
    
    Args:
        is_title_fight: Whether this is a title fight
        fighter_is_champion: Whether this fighter is defending
        
    Returns:
        Win probability bonus (0.05 = +5% for defending champ)
    """
    if is_title_fight and fighter_is_champion:
        return CHAMPION_ADVANTAGE
    return 0.0


# ============================================================================
# FIGHT CONTEXT
# ============================================================================

@dataclass
class FightContext:
    """Context for a fight that affects balance calculations."""
    is_title_fight: bool = False
    is_main_event: bool = False
    total_rounds: int = 3
    champion_id: Optional[str] = None  # ID of defending champion
    
    # Round-specific (for per-round calculations)
    current_round: int = 1
    is_championship_rounds: bool = False  # R4-5 of title fight
    
    @property
    def is_big_fight(self) -> bool:
        return self.is_title_fight or self.is_main_event


@dataclass
class FighterCombatProfile:
    """Fighter data needed for balance calculations."""
    fighter_id: str
    overall_rating: int
    mentality: FighterMentality
    finishing: FinishingInstinct
    traits: List[str]
    
    # Optional detailed stats
    striking_rating: int = 50
    grappling_rating: int = 50
    
    # State
    is_injured: bool = False
    had_full_camp: bool = True


@dataclass
class BalanceResult:
    """Result of balance calculations."""
    base_win_probability: float
    final_win_probability: float
    finish_chance_modifier: float
    
    # Breakdown for debugging/display
    rating_difference_mod: float = 0.0
    mentality_mod: float = 0.0
    trait_mod: float = 0.0
    champion_mod: float = 0.0
    style_matchup_mod: float = 0.0


# ============================================================================
# MAIN CALCULATION
# ============================================================================

def calculate_fight_probability(
    fighter: FighterCombatProfile,
    opponent: FighterCombatProfile,
    context: FightContext,
) -> BalanceResult:
    """
    Calculate comprehensive fight win probability.
    
    This is the main entry point for all balance calculations.
    Combines rating difference, mentality, traits, and context.
    
    Args:
        fighter: The fighter we're calculating probability for
        opponent: The opposing fighter
        context: Fight context (title fight, rounds, etc.)
        
    Returns:
        BalanceResult with probabilities and breakdown
    """
    # Import trait functions (avoid circular import)
    from systems.traits import (
        get_trait_win_bonus,
        get_pressure_counter_interaction,
        get_trait_fight_modifiers,
        get_camp_bonus,
    )
    
    # 1. Base probability from rating difference
    rating_diff = fighter.overall_rating - opponent.overall_rating
    # Rating diff of 10 points = ~3% advantage
    rating_mod = (rating_diff / 100) * 0.3
    base_prob = 0.5 + rating_mod
    
    # 2. Mentality modifiers
    fighter_mentality_mod = get_mentality_modifier(fighter.mentality)
    opponent_mentality_mod = get_mentality_modifier(opponent.mentality)
    mentality_mod = fighter_mentality_mod - opponent_mentality_mod
    
    # 3. Trait modifiers
    fighter_trait_mod = get_trait_win_bonus(fighter.traits)
    opponent_trait_mod = get_trait_win_bonus(opponent.traits)
    trait_mod = fighter_trait_mod - opponent_trait_mod
    
    # 4. Style matchup (pressure vs counter)
    fighter_style_mod, opponent_style_mod = get_pressure_counter_interaction(
        fighter.traits, opponent.traits
    )
    style_mod = fighter_style_mod - opponent_style_mod
    
    # 5. Champion advantage
    champion_mod = 0.0
    if context.is_title_fight:
        if fighter.fighter_id == context.champion_id:
            champion_mod = CHAMPION_ADVANTAGE
        elif opponent.fighter_id == context.champion_id:
            champion_mod = -CHAMPION_ADVANTAGE
    
    # 6. Big fight modifiers (from traits like Big Game Hunter)
    if context.is_big_fight:
        fighter_mods = get_trait_fight_modifiers(
            fighter.traits,
            is_title_fight=context.is_title_fight,
            is_main_event=context.is_main_event,
            total_rounds=context.total_rounds,
        )
        opponent_mods = get_trait_fight_modifiers(
            opponent.traits,
            is_title_fight=context.is_title_fight,
            is_main_event=context.is_main_event,
            total_rounds=context.total_rounds,
        )
        # Big fight bonuses already included in trait win_bonus via big_fight_bonus
        trait_mod += (fighter_mods.win_bonus - opponent_mods.win_bonus)
    
    # 7. Camp bonus (Gym Rat in full camp)
    if fighter.had_full_camp:
        camp_bonus = get_camp_bonus(fighter.traits)
        trait_mod += camp_bonus
    if opponent.had_full_camp:
        camp_bonus = get_camp_bonus(opponent.traits)
        trait_mod -= camp_bonus
    
    # Calculate final probability
    final_prob = base_prob + mentality_mod + trait_mod + style_mod + champion_mod
    
    # Clamp to reasonable range (never <8% or >92%)
    final_prob = max(0.08, min(0.92, final_prob))
    
    # Calculate finish chance modifier
    finish_mod = 0.0
    finish_mod += get_mentality_finish_modifier(fighter.mentality)
    finish_mod += get_finishing_instinct_modifier(fighter.finishing)
    
    # Add Injury Prone explosive bonus
    fighter_mods = get_trait_fight_modifiers(fighter.traits)
    finish_mod += fighter_mods.finish_bonus
    
    return BalanceResult(
        base_win_probability=base_prob,
        final_win_probability=final_prob,
        finish_chance_modifier=finish_mod,
        rating_difference_mod=rating_mod,
        mentality_mod=mentality_mod,
        trait_mod=trait_mod,
        champion_mod=champion_mod,
        style_matchup_mod=style_mod,
    )


def simulate_fight_outcome(
    fighter: FighterCombatProfile,
    opponent: FighterCombatProfile,
    context: FightContext,
    variance: float = 0.12,
) -> Tuple[str, str, int]:
    """
    Simulate a fight outcome using balance calculations.
    
    Args:
        fighter: Fighter 1
        opponent: Fighter 2
        context: Fight context
        variance: Standard deviation for randomness
        
    Returns:
        Tuple of (winner_id, method, round)
    """
    from systems.traits import get_trait_fight_modifiers
    
    # Get balance calculations
    result = calculate_fight_probability(fighter, opponent, context)
    
    # Apply variance
    final_prob = result.final_win_probability + random.gauss(0, variance)
    final_prob = max(0.08, min(0.92, final_prob))
    
    # Determine winner
    if random.random() < final_prob:
        winner, loser = fighter, opponent
    else:
        winner, loser = opponent, fighter
    
    # Determine method
    # Base finish chance
    base_finish = 0.35 + (winner.overall_rating - 50) / 200
    
    # Add winner's finish modifiers
    finish_chance = base_finish
    finish_chance += get_mentality_finish_modifier(winner.mentality)
    finish_chance += get_finishing_instinct_modifier(winner.finishing)
    
    # Trait modifiers
    winner_mods = get_trait_fight_modifiers(winner.traits)
    finish_chance += winner_mods.finish_bonus
    finish_chance += winner_mods.ko_chance_mod / 2  # KO artists finish more
    finish_chance += winner_mods.sub_chance_mod / 2  # Sub aces finish more
    
    # Loser durability
    loser_mods = get_trait_fight_modifiers(loser.traits)
    finish_chance += loser_mods.get_kod_mod  # Negative = harder to finish
    finish_chance += loser_mods.get_finished_mod
    
    # Cap finish chance
    finish_chance = max(0.15, min(0.70, finish_chance))
    
    if random.random() < finish_chance:
        # Determine KO vs SUB
        ko_lean = 0.65
        ko_lean += winner_mods.ko_chance_mod
        ko_lean -= winner_mods.sub_chance_mod
        
        if winner.striking_rating > winner.grappling_rating:
            ko_lean += 0.10
        else:
            ko_lean -= 0.10
        
        ko_lean = max(0.20, min(0.85, ko_lean))
        
        if random.random() < ko_lean:
            method = random.choice(["KO", "TKO"])
        else:
            method = "SUB"
        
        fight_round = random.randint(1, context.total_rounds)
    else:
        method = "DEC"
        fight_round = context.total_rounds
    
    return winner.fighter_id, method, fight_round


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_modifiers_display(
    fighter: FighterCombatProfile,
    opponent: FighterCombatProfile,
    context: FightContext,
) -> str:
    """
    Get a formatted string showing all balance modifiers for display.
    Useful for debugging or showing fight preview.
    """
    result = calculate_fight_probability(fighter, opponent, context)
    
    lines = [
        f"Fight Balance Breakdown:",
        f"  Base (ratings): {result.base_win_probability:.1%}",
        f"  Rating diff:    {result.rating_difference_mod:+.1%}",
        f"  Mentality:      {result.mentality_mod:+.1%}",
        f"  Traits:         {result.trait_mod:+.1%}",
        f"  Style matchup:  {result.style_matchup_mod:+.1%}",
        f"  Champion bonus: {result.champion_mod:+.1%}",
        f"  ─────────────────────",
        f"  FINAL:          {result.final_win_probability:.1%}",
        f"  Finish modifier:{result.finish_chance_modifier:+.1%}",
    ]
    
    return "\n".join(lines)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Constants
    "MENTALITY_COMBAT_MODIFIERS",
    "MENTALITY_FINISH_MODIFIERS",
    "FINISHING_INSTINCT_MODIFIERS",
    "CHAMPION_ADVANTAGE",
    
    # Individual modifiers
    "get_mentality_modifier",
    "get_mentality_finish_modifier",
    "get_finishing_instinct_modifier",
    "get_champion_advantage",
    
    # Data classes
    "FightContext",
    "FighterCombatProfile",
    "BalanceResult",
    
    # Main functions
    "calculate_fight_probability",
    "simulate_fight_outcome",
    "get_all_modifiers_display",
]
