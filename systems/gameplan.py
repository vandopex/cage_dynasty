# systems/gameplan.py
# Module: Gameplan System
# Lines: ~1,250
#
# Defines fight strategies and tactical approaches.
# Gameplans affect how fighters perform in the cage.

"""
Cage Dynasty - Gameplan System

This module handles fight strategy and tactics:
- Gameplan definitions (stance, aggression, focus areas)
- Matchup advantages/disadvantages
- Matchup analysis for fight preparation
- Round-by-round strategy adjustments
- AI gameplan generation
- CLI integration helpers for player interaction

CONCEPT:
    Before each fight, fighters can set a gameplan that affects their approach.
    A wrestler might choose to "Wrestle Heavy" to maximize takedowns.
    A striker facing a grappler might choose "Keep It Standing" for TDD bonus.
    
    Gameplans interact - some counter others, creating strategic depth.

USAGE:
    from systems.gameplan import (
        create_gameplan,
        get_gameplan_modifiers,
        get_matchup_adjustment,
        generate_ai_gameplan,
        recommend_gameplan,
        GameplanMenuHelper,
        # New matchup analysis
        get_matchup_analysis,
        get_gameplan_options,
    )
    
    # Analyze matchup
    analysis = get_matchup_analysis(my_stats, opp_stats)
    print(analysis.your_edges)
    print(analysis.their_edges)
    print(analysis.suggested_approach)
    
    # Get gameplan options with modifiers shown
    options = get_gameplan_options(my_stats, opp_stats)
    for opt in options:
        print(f"{opt.name}: {opt.description}")
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random


# ============================================================================
# ENUMS AND TYPES
# ============================================================================

class Stance(Enum):
    """Overall fighting stance/approach."""
    AGGRESSIVE = "AGGRESSIVE"      # High pressure, more offense
    BALANCED = "BALANCED"          # Default, no modifiers
    DEFENSIVE = "DEFENSIVE"        # Counter-fighting, less risk
    MEASURED = "MEASURED"          # Patient, pick shots carefully


class Focus(Enum):
    """Primary area of focus in the fight."""
    STRIKING = "STRIKING"          # Prioritize standup
    GRAPPLING = "GRAPPLING"        # Prioritize wrestling/ground
    MIXED = "MIXED"                # Balanced approach
    CLINCH = "CLINCH"              # Dirty boxing, wall work


class Priority(Enum):
    """What the fighter is trying to achieve."""
    KNOCKOUT = "KNOCKOUT"          # Hunting the finish on feet
    SUBMISSION = "SUBMISSION"      # Hunting the tap
    DECISION = "DECISION"          # Point fighting, safe
    FINISH = "FINISH"              # Any finish, ground and pound ok
    SURVIVAL = "SURVIVAL"          # Just trying to survive (injured, outclassed)


class RoundStrategy(Enum):
    """Per-round tactical adjustment."""
    FEEL_OUT = "FEEL_OUT"          # Round 1 - gather info
    PUSH_PACE = "PUSH_PACE"        # Increase output
    CONSERVE = "CONSERVE"          # Save energy
    ALL_OUT = "ALL_OUT"            # Championship rounds, go for broke
    CRUISE = "CRUISE"              # Protect a lead


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Gameplan:
    """Complete fight gameplan for a fighter."""
    stance: str = "BALANCED"
    focus: str = "MIXED"
    priority: str = "FINISH"
    
    # Round-specific strategies (optional)
    round_strategies: Dict[int, str] = field(default_factory=dict)
    
    # Specific tactical instructions
    check_leg_kicks: bool = False      # Extra defense vs leg kicks
    avoid_ground: bool = False         # Pop up immediately if taken down
    wrestle_heavy: bool = False        # Shoot often
    pressure_cage: bool = False        # Cut off the cage
    counter_fight: bool = False        # Wait for opponent to lead
    target_body: bool = False          # Attack the body
    target_legs: bool = False          # Attack the legs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stance": self.stance,
            "focus": self.focus,
            "priority": self.priority,
            "round_strategies": self.round_strategies,
            "check_leg_kicks": self.check_leg_kicks,
            "avoid_ground": self.avoid_ground,
            "wrestle_heavy": self.wrestle_heavy,
            "pressure_cage": self.pressure_cage,
            "counter_fight": self.counter_fight,
            "target_body": self.target_body,
            "target_legs": self.target_legs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Gameplan":
        """Create from dictionary."""
        if data is None:
            return cls()
        return cls(
            stance=data.get("stance", "BALANCED"),
            focus=data.get("focus", "MIXED"),
            priority=data.get("priority", "FINISH"),
            round_strategies=data.get("round_strategies", {}),
            check_leg_kicks=data.get("check_leg_kicks", False),
            avoid_ground=data.get("avoid_ground", False),
            wrestle_heavy=data.get("wrestle_heavy", False),
            pressure_cage=data.get("pressure_cage", False),
            counter_fight=data.get("counter_fight", False),
            target_body=data.get("target_body", False),
            target_legs=data.get("target_legs", False),
        )
    
    def copy(self) -> "Gameplan":
        """Create a copy of this gameplan."""
        return Gameplan(
            stance=self.stance,
            focus=self.focus,
            priority=self.priority,
            round_strategies=dict(self.round_strategies),
            check_leg_kicks=self.check_leg_kicks,
            avoid_ground=self.avoid_ground,
            wrestle_heavy=self.wrestle_heavy,
            pressure_cage=self.pressure_cage,
            counter_fight=self.counter_fight,
            target_body=self.target_body,
            target_legs=self.target_legs,
        )


@dataclass
class GameplanModifiers:
    """Stat modifiers resulting from a gameplan."""
    # Offensive modifiers
    striking_offense: int = 0
    grappling_offense: int = 0
    aggression_mod: int = 0
    
    # Defensive modifiers
    striking_defense: int = 0
    grappling_defense: int = 0
    
    # Outcome modifiers (percentages)
    ko_chance_mod: float = 0.0
    sub_chance_mod: float = 0.0
    
    # Stamina/cardio effects
    cardio_drain_mod: float = 0.0  # Positive = drains faster
    
    # Risk/reward
    damage_taken_mod: float = 0.0  # Positive = take more damage
    damage_dealt_mod: float = 0.0  # Positive = deal more damage
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for external use."""
        return {
            "striking_offense": self.striking_offense,
            "grappling_offense": self.grappling_offense,
            "aggression_mod": self.aggression_mod,
            "striking_defense": self.striking_defense,
            "grappling_defense": self.grappling_defense,
            "ko_chance_mod": self.ko_chance_mod,
            "sub_chance_mod": self.sub_chance_mod,
            "cardio_drain_mod": self.cardio_drain_mod,
            "damage_taken_mod": self.damage_taken_mod,
            "damage_dealt_mod": self.damage_dealt_mod,
        }


@dataclass
class MatchupAnalysis:
    """Analysis of a fighter matchup."""
    your_edges: List[str] = field(default_factory=list)
    their_edges: List[str] = field(default_factory=list)
    suggested_approach: str = ""
    danger_warnings: List[str] = field(default_factory=list)
    recommended_gameplan_idx: str = "2"  # Default to striker
    recommendation_reason: str = ""
    
    # Detailed stat comparisons
    striking_advantage: int = 0  # Positive = you're better
    grappling_advantage: int = 0
    physical_advantage: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "your_edges": self.your_edges,
            "their_edges": self.their_edges,
            "suggested_approach": self.suggested_approach,
            "danger_warnings": self.danger_warnings,
            "recommended_gameplan_idx": self.recommended_gameplan_idx,
            "recommendation_reason": self.recommendation_reason,
            "striking_advantage": self.striking_advantage,
            "grappling_advantage": self.grappling_advantage,
            "physical_advantage": self.physical_advantage,
        }


@dataclass
class GameplanOption:
    """A gameplan option for the menu."""
    key: str
    name: str
    description: str
    modifiers_text: str
    gameplan: Gameplan
    is_recommended: bool = False
    warning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "modifiers_text": self.modifiers_text,
            "is_recommended": self.is_recommended,
            "warning": self.warning,
        }


# ============================================================================
# GAMEPLAN DEFINITIONS
# ============================================================================

# Stance modifiers
STANCE_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "AGGRESSIVE": {
        "striking_offense": 8,
        "grappling_offense": 5,
        "aggression_mod": 15,
        "striking_defense": -5,
        "grappling_defense": -3,
        "ko_chance_mod": 0.10,
        "cardio_drain_mod": 0.15,
        "damage_taken_mod": 0.10,
        "damage_dealt_mod": 0.10,
    },
    "BALANCED": {
        # No modifiers - baseline
    },
    "DEFENSIVE": {
        "striking_offense": -5,
        "grappling_offense": -3,
        "aggression_mod": -10,
        "striking_defense": 8,
        "grappling_defense": 5,
        "ko_chance_mod": -0.10,
        "cardio_drain_mod": -0.10,
        "damage_taken_mod": -0.15,
        "damage_dealt_mod": -0.05,
    },
    "MEASURED": {
        "striking_offense": -2,
        "aggression_mod": -5,
        "striking_defense": 3,
        "grappling_defense": 3,
        "cardio_drain_mod": -0.05,
        "damage_taken_mod": -0.05,
    },
}

# Focus modifiers
FOCUS_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "STRIKING": {
        "striking_offense": 5,
        "striking_defense": 3,
        "grappling_offense": -3,
        "grappling_defense": -2,
    },
    "GRAPPLING": {
        "grappling_offense": 5,
        "grappling_defense": 3,
        "striking_offense": -3,
        "striking_defense": -2,
    },
    "MIXED": {
        # Balanced - small bonuses everywhere
        "striking_offense": 1,
        "grappling_offense": 1,
        "striking_defense": 1,
        "grappling_defense": 1,
    },
    "CLINCH": {
        "grappling_offense": 3,
        "striking_offense": 2,
        "cardio_drain_mod": 0.05,
    },
}

# Priority modifiers
PRIORITY_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "KNOCKOUT": {
        "striking_offense": 5,
        "ko_chance_mod": 0.15,
        "damage_dealt_mod": 0.10,
        "damage_taken_mod": 0.05,
    },
    "SUBMISSION": {
        "grappling_offense": 5,
        "sub_chance_mod": 0.15,
    },
    "DECISION": {
        "striking_defense": 5,
        "grappling_defense": 5,
        "ko_chance_mod": -0.10,
        "sub_chance_mod": -0.05,
        "cardio_drain_mod": -0.10,
        "damage_taken_mod": -0.10,
    },
    "FINISH": {
        "ko_chance_mod": 0.05,
        "sub_chance_mod": 0.05,
        "damage_dealt_mod": 0.05,
    },
    "SURVIVAL": {
        "striking_offense": -10,
        "grappling_offense": -10,
        "striking_defense": 10,
        "grappling_defense": 10,
        "damage_taken_mod": -0.20,
    },
}

# Round strategy modifiers
ROUND_STRATEGY_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "FEEL_OUT": {
        "striking_offense": -3,
        "grappling_offense": -3,
        "striking_defense": 5,
        "cardio_drain_mod": -0.15,
    },
    "PUSH_PACE": {
        "striking_offense": 5,
        "grappling_offense": 5,
        "aggression_mod": 10,
        "cardio_drain_mod": 0.10,
    },
    "CONSERVE": {
        "striking_offense": -5,
        "cardio_drain_mod": -0.20,
    },
    "ALL_OUT": {
        "striking_offense": 10,
        "grappling_offense": 10,
        "aggression_mod": 20,
        "ko_chance_mod": 0.10,
        "sub_chance_mod": 0.10,
        "cardio_drain_mod": 0.25,
        "damage_taken_mod": 0.10,
    },
    "CRUISE": {
        "striking_offense": -5,
        "grappling_offense": -5,
        "striking_defense": 8,
        "grappling_defense": 8,
        "cardio_drain_mod": -0.15,
    },
}

# Tactical instruction modifiers
TACTICAL_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "check_leg_kicks": {
        "striking_defense": 3,
        # Reduces leg kick damage taken
    },
    "avoid_ground": {
        "grappling_defense": 8,
        "grappling_offense": -5,
    },
    "wrestle_heavy": {
        "grappling_offense": 10,
        "striking_offense": -5,
        "cardio_drain_mod": 0.10,
    },
    "pressure_cage": {
        "aggression_mod": 10,
        "striking_offense": 3,
        "cardio_drain_mod": 0.05,
    },
    "counter_fight": {
        "striking_defense": 5,
        "ko_chance_mod": 0.10,  # Counter shots are damaging
        "aggression_mod": -10,
        "cardio_drain_mod": -0.10,
    },
    "target_body": {
        "cardio_drain_mod": -0.05,  # Body shots drain opponent cardio
    },
    "target_legs": {
        # Reduces opponent mobility over time
    },
}


# ============================================================================
# CORE GAMEPLAN FUNCTIONS
# ============================================================================

def create_gameplan(
    stance: str = "BALANCED",
    focus: str = "MIXED",
    priority: str = "FINISH",
    **kwargs,
) -> Gameplan:
    """
    Create a gameplan with specified parameters.
    
    Args:
        stance: Overall approach (AGGRESSIVE, BALANCED, DEFENSIVE, MEASURED)
        focus: Primary focus (STRIKING, GRAPPLING, MIXED, CLINCH)
        priority: Goal (KNOCKOUT, SUBMISSION, DECISION, FINISH, SURVIVAL)
        **kwargs: Tactical instructions (check_leg_kicks, wrestle_heavy, etc.)
        
    Returns:
        Gameplan object
    """
    return Gameplan(
        stance=stance.upper(),
        focus=focus.upper(),
        priority=priority.upper(),
        check_leg_kicks=kwargs.get("check_leg_kicks", False),
        avoid_ground=kwargs.get("avoid_ground", False),
        wrestle_heavy=kwargs.get("wrestle_heavy", False),
        pressure_cage=kwargs.get("pressure_cage", False),
        counter_fight=kwargs.get("counter_fight", False),
        target_body=kwargs.get("target_body", False),
        target_legs=kwargs.get("target_legs", False),
        round_strategies=kwargs.get("round_strategies", {}),
    )


def get_default_gameplan() -> Gameplan:
    """Get a default balanced gameplan."""
    return create_gameplan("BALANCED", "MIXED", "FINISH")


def get_gameplan_modifiers(
    gameplan: Gameplan,
    current_round: int = 1,
) -> GameplanModifiers:
    """
    Calculate all stat modifiers from a gameplan.
    
    Args:
        gameplan: The gameplan to evaluate
        current_round: Current round (for round-specific strategies)
        
    Returns:
        GameplanModifiers with all accumulated modifiers
    """
    mods = GameplanModifiers()
    
    # Apply stance modifiers
    stance_mods = STANCE_MODIFIERS.get(gameplan.stance, {})
    _apply_modifiers(mods, stance_mods)
    
    # Apply focus modifiers
    focus_mods = FOCUS_MODIFIERS.get(gameplan.focus, {})
    _apply_modifiers(mods, focus_mods)
    
    # Apply priority modifiers
    priority_mods = PRIORITY_MODIFIERS.get(gameplan.priority, {})
    _apply_modifiers(mods, priority_mods)
    
    # Apply round strategy if set
    round_strat = gameplan.round_strategies.get(current_round)
    if round_strat:
        round_mods = ROUND_STRATEGY_MODIFIERS.get(round_strat, {})
        _apply_modifiers(mods, round_mods)
    
    # Apply tactical instructions
    if gameplan.check_leg_kicks:
        _apply_modifiers(mods, TACTICAL_MODIFIERS["check_leg_kicks"])
    if gameplan.avoid_ground:
        _apply_modifiers(mods, TACTICAL_MODIFIERS["avoid_ground"])
    if gameplan.wrestle_heavy:
        _apply_modifiers(mods, TACTICAL_MODIFIERS["wrestle_heavy"])
    if gameplan.pressure_cage:
        _apply_modifiers(mods, TACTICAL_MODIFIERS["pressure_cage"])
    if gameplan.counter_fight:
        _apply_modifiers(mods, TACTICAL_MODIFIERS["counter_fight"])
    if gameplan.target_body:
        _apply_modifiers(mods, TACTICAL_MODIFIERS["target_body"])
    if gameplan.target_legs:
        _apply_modifiers(mods, TACTICAL_MODIFIERS["target_legs"])
    
    return mods


def _apply_modifiers(target: GameplanModifiers, source: Dict[str, Any]) -> None:
    """Apply modifier dictionary to GameplanModifiers object."""
    for key, value in source.items():
        if hasattr(target, key):
            current = getattr(target, key)
            setattr(target, key, current + value)


# ============================================================================
# MATCHUP ANALYSIS FUNCTIONS
# ============================================================================

def get_matchup_analysis(
    fighter_stats: Dict[str, int],
    opponent_stats: Dict[str, int],
) -> MatchupAnalysis:
    """
    Analyze a matchup between two fighters.
    
    Args:
        fighter_stats: Dict with your fighter's attributes
        opponent_stats: Dict with opponent's attributes
        
    Returns:
        MatchupAnalysis with edges, suggestions, and warnings
    """
    analysis = MatchupAnalysis()
    
    # Define stat comparisons
    stat_comparisons = [
        ("Boxing", fighter_stats.get("boxing", 50), opponent_stats.get("boxing", 50), "striking"),
        ("Kicks", fighter_stats.get("kicks", 50), opponent_stats.get("kicks", 50), "striking"),
        ("Wrestling", fighter_stats.get("wrestling", 50), opponent_stats.get("wrestling", 50), "grappling"),
        ("BJJ", fighter_stats.get("bjj", 50), opponent_stats.get("bjj", 50), "grappling"),
        ("Cardio", fighter_stats.get("cardio", 50), opponent_stats.get("cardio", 50), "physical"),
        ("Chin", fighter_stats.get("chin", 50), opponent_stats.get("chin", 50), "physical"),
        ("Strength", fighter_stats.get("strength", 50), opponent_stats.get("strength", 50), "physical"),
        ("Speed", fighter_stats.get("speed", 50), opponent_stats.get("speed", 50), "physical"),
    ]
    
    # Calculate edges
    for name, yours, theirs, category in stat_comparisons:
        diff = yours - theirs
        if diff >= 10:
            analysis.your_edges.append(f"{name}: {yours}")
        elif diff <= -10:
            analysis.their_edges.append(f"{name}: {theirs}")
    
    # Calculate category advantages
    your_striking = (fighter_stats.get("boxing", 50) + fighter_stats.get("kicks", 50)) / 2
    their_striking = (opponent_stats.get("boxing", 50) + opponent_stats.get("kicks", 50)) / 2
    your_grappling = (fighter_stats.get("wrestling", 50) + fighter_stats.get("bjj", 50)) / 2
    their_grappling = (opponent_stats.get("wrestling", 50) + opponent_stats.get("bjj", 50)) / 2
    
    analysis.striking_advantage = int(your_striking - their_striking)
    analysis.grappling_advantage = int(your_grappling - their_grappling)
    
    # Determine suggested approach
    if analysis.grappling_advantage > 10:
        analysis.suggested_approach = "Take the fight to the ground, control and finish"
        analysis.recommended_gameplan_idx = "3"  # Wrestler
        analysis.recommendation_reason = "Your grappling is superior"
    elif analysis.striking_advantage > 10:
        analysis.suggested_approach = "Keep it standing, pick your shots"
        analysis.recommended_gameplan_idx = "2"  # Striker
        analysis.recommendation_reason = "Your striking is superior"
    elif analysis.grappling_advantage < -10:
        analysis.suggested_approach = "Stuff takedowns, make them strike with you"
        analysis.recommended_gameplan_idx = "2"  # Striker - avoid ground
        analysis.recommendation_reason = "Avoid their grappling"
    elif analysis.striking_advantage < -10:
        analysis.suggested_approach = "Close distance, clinch or take down"
        analysis.recommended_gameplan_idx = "3"  # Wrestler
        analysis.recommendation_reason = "Neutralize their striking"
    else:
        analysis.suggested_approach = "Well-matched, execute your gameplan"
        analysis.recommended_gameplan_idx = "4"  # Point fighter - safe
        analysis.recommendation_reason = "Even matchup, fight smart"
    
    # Check for specific dangers
    opp_bjj = opponent_stats.get("bjj", 50)
    opp_power = opponent_stats.get("power", 50)
    your_wrestling = fighter_stats.get("wrestling", 50)
    your_chin = fighter_stats.get("chin", 50)
    
    if opp_bjj >= 80 and your_wrestling < 70:
        analysis.danger_warnings.append("HIGH submission threat - avoid the ground")
    if opp_power >= 80 and your_chin < 65:
        analysis.danger_warnings.append("HIGH knockout threat - don't trade")
    if opponent_stats.get("wrestling", 50) >= 80 and fighter_stats.get("bjj", 50) < 65:
        analysis.danger_warnings.append("If taken down, difficult to escape")
    if opponent_stats.get("cardio", 50) >= 80 and fighter_stats.get("cardio", 50) < 60:
        analysis.danger_warnings.append("May get outworked in later rounds")
    
    return analysis


def get_gameplan_options(
    fighter_stats: Dict[str, int],
    opponent_stats: Optional[Dict[str, int]] = None,
) -> List[GameplanOption]:
    """
    Get all gameplan options with modifiers and recommendations.
    
    Args:
        fighter_stats: Dict with fighter's attributes
        opponent_stats: Optional dict with opponent's attributes
        
    Returns:
        List of GameplanOption objects
    """
    options = []
    
    # Get recommendation from analysis
    recommended_idx = "2"  # Default
    if opponent_stats:
        analysis = get_matchup_analysis(fighter_stats, opponent_stats)
        recommended_idx = analysis.recommended_gameplan_idx
    
    # Define base options
    boxing = fighter_stats.get("boxing", 50)
    kicks = fighter_stats.get("kicks", 50)
    wrestling = fighter_stats.get("wrestling", 50)
    bjj = fighter_stats.get("bjj", 50)
    
    # 2. Striker
    striker_plan = create_gameplan("AGGRESSIVE", "STRIKING", "KNOCKOUT")
    striker_warn = ""
    if (boxing + kicks) / 2 < 65:
        striker_warn = "(your striking is weak)"
    options.append(GameplanOption(
        key="2",
        name="Striker",
        description="Aggressive standup, hunt KO",
        modifiers_text="+8 striking, +10% KO chance, -5 defense",
        gameplan=striker_plan,
        is_recommended=(recommended_idx == "2"),
        warning=striker_warn,
    ))
    
    # 3. Wrestler
    wrestler_plan = create_gameplan("BALANCED", "GRAPPLING", "FINISH", wrestle_heavy=True)
    wrestler_warn = ""
    if wrestling < 65:
        wrestler_warn = "(your wrestling is weak)"
    options.append(GameplanOption(
        key="3",
        name="Wrestler",
        description="Control and ground-and-pound",
        modifiers_text="+8 grappling, wrestle heavy, ground & pound",
        gameplan=wrestler_plan,
        is_recommended=(recommended_idx == "3"),
        warning=wrestler_warn,
    ))
    
    # 4. Point Fighter
    point_plan = create_gameplan("MEASURED", "MIXED", "DECISION")
    options.append(GameplanOption(
        key="4",
        name="Point Fighter",
        description="Safe, outwork opponent",
        modifiers_text="Safe approach, -10% damage taken, lower finish rate",
        gameplan=point_plan,
        is_recommended=(recommended_idx == "4"),
        warning="",
    ))
    
    # 5. Counter Striker
    counter_plan = create_gameplan("DEFENSIVE", "STRIKING", "KNOCKOUT", counter_fight=True)
    options.append(GameplanOption(
        key="5",
        name="Counter Striker",
        description="Let them come to you",
        modifiers_text="+10% KO on counters, -10% cardio drain, patient",
        gameplan=counter_plan,
        is_recommended=(recommended_idx == "5"),
        warning="",
    ))
    
    # 6. Submission Hunter
    sub_plan = create_gameplan("MEASURED", "GRAPPLING", "SUBMISSION")
    sub_warn = ""
    if bjj < 70:
        sub_warn = "(your BJJ is weak)"
    options.append(GameplanOption(
        key="6",
        name="Submission Hunter",
        description="Take down and hunt the tap",
        modifiers_text="+10% submission chance, patient ground game",
        gameplan=sub_plan,
        is_recommended=(recommended_idx == "6"),
        warning=sub_warn,
    ))
    
    return options


# ============================================================================
# MATCHUP FUNCTIONS
# ============================================================================

def get_matchup_adjustment(
    gameplan1: Gameplan,
    gameplan2: Gameplan,
) -> Tuple[int, int]:
    """
    Calculate matchup adjustments based on clashing gameplans.
    
    Some strategies counter others:
    - Counter-fighting beats aggressive pressure
    - Wrestle heavy beats pure strikers
    - Pressure cage beats counter-fighters
    
    Args:
        gameplan1: Fighter 1's gameplan
        gameplan2: Fighter 2's gameplan
        
    Returns:
        Tuple of (fighter1_adjustment, fighter2_adjustment)
    """
    adj1, adj2 = 0, 0
    
    # Aggressive vs Defensive/Counter
    if gameplan1.stance == "AGGRESSIVE" and gameplan2.counter_fight:
        adj1 -= 5
        adj2 += 5
    if gameplan2.stance == "AGGRESSIVE" and gameplan1.counter_fight:
        adj2 -= 5
        adj1 += 5
    
    # Pressure beats counter (if not also countering)
    if gameplan1.pressure_cage and gameplan2.counter_fight and not gameplan1.counter_fight:
        adj1 += 3
        adj2 -= 3
    if gameplan2.pressure_cage and gameplan1.counter_fight and not gameplan2.counter_fight:
        adj2 += 3
        adj1 -= 3
    
    # Wrestle heavy vs Striking focus
    if gameplan1.wrestle_heavy and gameplan2.focus == "STRIKING":
        adj1 += 5
    if gameplan2.wrestle_heavy and gameplan1.focus == "STRIKING":
        adj2 += 5
    
    # Avoid ground vs Wrestle heavy (mutual negation)
    if gameplan1.avoid_ground and gameplan2.wrestle_heavy:
        adj1 += 3  # TDD focus helps
    if gameplan2.avoid_ground and gameplan1.wrestle_heavy:
        adj2 += 3
    
    # Decision fighter vs Aggressive (aggressor can walk into counters)
    if gameplan1.priority == "DECISION" and gameplan2.stance == "AGGRESSIVE":
        adj1 += 3
    if gameplan2.priority == "DECISION" and gameplan1.stance == "AGGRESSIVE":
        adj2 += 3
    
    return adj1, adj2


def gameplans_clash(gameplan1: Gameplan, gameplan2: Gameplan) -> str:
    """
    Describe how two gameplans interact for commentary.
    
    Returns a string describing the tactical clash.
    """
    clashes = []
    
    if gameplan1.wrestle_heavy and gameplan2.avoid_ground:
        clashes.append("wrestling vs anti-grappling")
    elif gameplan2.wrestle_heavy and gameplan1.avoid_ground:
        clashes.append("wrestling vs anti-grappling")
    
    if gameplan1.counter_fight and gameplan2.pressure_cage:
        clashes.append("counter-punching vs pressure")
    elif gameplan2.counter_fight and gameplan1.pressure_cage:
        clashes.append("counter-punching vs pressure")
    
    if gameplan1.focus == "STRIKING" and gameplan2.focus == "GRAPPLING":
        clashes.append("striker vs grappler")
    elif gameplan2.focus == "STRIKING" and gameplan1.focus == "GRAPPLING":
        clashes.append("striker vs grappler")
    
    if gameplan1.stance == "AGGRESSIVE" and gameplan2.stance == "DEFENSIVE":
        clashes.append("aggressor vs counter-fighter")
    elif gameplan2.stance == "AGGRESSIVE" and gameplan1.stance == "DEFENSIVE":
        clashes.append("aggressor vs counter-fighter")
    
    if not clashes:
        return "evenly matched strategies"
    
    return " and ".join(clashes)


# ============================================================================
# AI GAMEPLAN GENERATION
# ============================================================================

def generate_ai_gameplan(
    fighter_stats: Dict[str, int],
    opponent_stats: Optional[Dict[str, int]] = None,
    is_title_fight: bool = False,
    rounds_in_fight: int = 3,
) -> Gameplan:
    """
    Generate an intelligent gameplan based on fighter attributes.
    
    Args:
        fighter_stats: Dict with fighter's attributes
        opponent_stats: Optional dict with opponent's attributes
        is_title_fight: Whether this is a title fight
        rounds_in_fight: Number of rounds
        
    Returns:
        Gameplan tailored to fighter's strengths
    """
    # Get base stats
    boxing = fighter_stats.get("boxing", 50)
    kicks = fighter_stats.get("kicks", 50)
    wrestling = fighter_stats.get("wrestling", 50)
    bjj = fighter_stats.get("bjj", 50)
    power = fighter_stats.get("power", 50)
    cardio = fighter_stats.get("cardio", 50)
    aggression = fighter_stats.get("aggression", 50)
    composure = fighter_stats.get("composure", 50)
    submissions = fighter_stats.get("submissions", 50)
    
    # Calculate averages
    striking = (boxing + kicks) / 2
    grappling = (wrestling + bjj) / 2
    
    # Determine stance based on personality
    if aggression >= 70:
        stance = "AGGRESSIVE"
    elif composure >= 70 and aggression < 50:
        stance = "MEASURED"
    elif aggression < 40:
        stance = "DEFENSIVE"
    else:
        stance = "BALANCED"
    
    # Determine focus based on skills
    if striking > grappling + 15:
        focus = "STRIKING"
    elif grappling > striking + 15:
        focus = "GRAPPLING"
    else:
        focus = "MIXED"
    
    # Determine priority based on finishing ability
    if power >= 75 and focus in ["STRIKING", "MIXED"]:
        priority = "KNOCKOUT"
    elif submissions >= 75 and focus in ["GRAPPLING", "MIXED"]:
        priority = "SUBMISSION"
    elif cardio >= 70 and power < 60:
        priority = "DECISION"
    else:
        priority = "FINISH"
    
    # Build tactical options
    tactics = {}
    
    # Wrestling-heavy if good wrestler facing striker
    if opponent_stats:
        opp_striking = (opponent_stats.get("boxing", 50) + opponent_stats.get("kicks", 50)) / 2
        opp_grappling = (opponent_stats.get("wrestling", 50) + opponent_stats.get("bjj", 50)) / 2
        
        if wrestling >= 70 and opp_striking > opp_grappling:
            tactics["wrestle_heavy"] = True
        
        if striking >= 65 and opp_grappling > opp_striking + 10:
            tactics["avoid_ground"] = True
        
        if composure >= 65 and opponent_stats.get("aggression", 50) >= 70:
            tactics["counter_fight"] = True
        
        if aggression >= 70:
            tactics["pressure_cage"] = True
    
    return create_gameplan(stance, focus, priority, **tactics)


def adjust_gameplan_for_situation(
    gameplan: Gameplan,
    current_round: int,
    total_rounds: int,
    is_winning: bool,
    health_percent: float,
    stamina_percent: float,
) -> Gameplan:
    """
    Adjust gameplan based on fight situation.
    
    Args:
        gameplan: Current gameplan
        current_round: Current round number
        total_rounds: Total rounds in fight
        is_winning: Whether fighter is ahead on scorecards
        health_percent: Fighter's health (0-1)
        stamina_percent: Fighter's stamina (0-1)
        
    Returns:
        Adjusted gameplan (new instance)
    """
    # Create a copy
    new_plan = gameplan.copy()
    
    # Emergency adjustments
    if health_percent < 0.3:
        new_plan.priority = "SURVIVAL"
        new_plan.stance = "DEFENSIVE"
    elif stamina_percent < 0.25:
        new_plan.round_strategies[current_round] = "CONSERVE"
    
    # Championship rounds adjustments
    if current_round >= total_rounds - 1:
        if is_winning:
            new_plan.round_strategies[current_round] = "CRUISE"
        else:
            new_plan.round_strategies[current_round] = "ALL_OUT"
    
    return new_plan


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

def recommend_gameplan(
    fighter_stats: Dict[str, int],
    opponent_stats: Optional[Dict[str, int]] = None,
    is_title_fight: bool = False,
    rounds_in_fight: int = 3,
) -> Tuple[Gameplan, str]:
    """
    Generate a recommended gameplan with explanation.
    
    Args:
        fighter_stats: Dict with fighter's attributes
        opponent_stats: Optional dict with opponent's attributes
        is_title_fight: Whether this is a title fight
        rounds_in_fight: Number of rounds
        
    Returns:
        Tuple of (recommended Gameplan, reason string)
    """
    gameplan = generate_ai_gameplan(fighter_stats, opponent_stats, is_title_fight, rounds_in_fight)
    
    # Build reason
    reasons = []
    
    boxing = fighter_stats.get("boxing", 50)
    kicks = fighter_stats.get("kicks", 50)
    wrestling = fighter_stats.get("wrestling", 50)
    bjj = fighter_stats.get("bjj", 50)
    striking = (boxing + kicks) / 2
    grappling = (wrestling + bjj) / 2
    
    if gameplan.focus == "STRIKING":
        reasons.append(f"Striking ({striking:.0f})")
    elif gameplan.focus == "GRAPPLING":
        reasons.append(f"Grappling ({grappling:.0f})")
    
    if gameplan.priority == "KNOCKOUT":
        reasons.append("KO power")
    elif gameplan.priority == "SUBMISSION":
        reasons.append("Sub threat")
    elif gameplan.priority == "DECISION":
        reasons.append("Point fight")
    
    reason = "Based on: " + ", ".join(reasons) if reasons else "Balanced approach"
    
    return gameplan, reason


def get_gameplan_warnings(
    gameplan: Gameplan,
    fighter_stats: Dict[str, int],
) -> List[str]:
    """
    Get warnings about potential gameplan issues.
    
    Args:
        gameplan: The gameplan to evaluate
        fighter_stats: Fighter's attributes
        
    Returns:
        List of warning strings
    """
    warnings = []
    
    cardio = fighter_stats.get("cardio", 50)
    chin = fighter_stats.get("chin", 50)
    power = fighter_stats.get("power", 50)
    wrestling = fighter_stats.get("wrestling", 50)
    bjj = fighter_stats.get("bjj", 50)
    composure = fighter_stats.get("composure", 50)
    
    # Cardio warnings
    if gameplan.stance == "AGGRESSIVE" and cardio < 60:
        warnings.append(f"Aggressive stance with low cardio ({cardio}) risks gassing")
    
    if gameplan.priority == "KNOCKOUT" and power < 60:
        warnings.append(f"KO hunting with low power ({power}) may be ineffective")
    
    if gameplan.priority == "SUBMISSION" and bjj < 65:
        warnings.append(f"Sub hunting with low BJJ ({bjj}) is risky")
    
    if gameplan.wrestle_heavy and wrestling < 65:
        warnings.append(f"Wrestle heavy with low wrestling ({wrestling}) may backfire")
    
    if gameplan.counter_fight and composure < 60:
        warnings.append(f"Counter fighting with low composure ({composure}) is difficult")
    
    if gameplan.stance == "AGGRESSIVE" and chin < 60:
        warnings.append(f"Aggressive with weak chin ({chin}) invites disaster")
    
    return warnings


# ============================================================================
# CLI MENU HELPER
# ============================================================================

class GameplanMenuHelper:
    """Helper class for CLI gameplan selection menus."""
    
    STANCE_OPTIONS = [
        ("1", "AGGRESSIVE", "High pressure, more offense (+offense, -defense)"),
        ("2", "BALANCED", "No modifiers, baseline approach"),
        ("3", "DEFENSIVE", "Counter-fighting, less risk (+defense, -offense)"),
        ("4", "MEASURED", "Patient, pick shots carefully"),
    ]
    
    FOCUS_OPTIONS = [
        ("1", "STRIKING", "Prioritize standup fighting"),
        ("2", "GRAPPLING", "Prioritize wrestling and ground"),
        ("3", "MIXED", "Balanced, use all tools"),
        ("4", "CLINCH", "Dirty boxing, wall work"),
    ]
    
    PRIORITY_OPTIONS = [
        ("1", "KNOCKOUT", "Hunting the knockout"),
        ("2", "SUBMISSION", "Hunting the tap"),
        ("3", "DECISION", "Point fighting, safe"),
        ("4", "FINISH", "Any finish is good"),
    ]
    
    TACTICS_OPTIONS = [
        ("1", "wrestle_heavy", "Wrestle Heavy", "Shoot often, control on ground"),
        ("2", "avoid_ground", "Avoid Ground", "Stay standing, pop up if down"),
        ("3", "pressure_cage", "Cage Pressure", "Cut off the cage"),
        ("4", "counter_fight", "Counter Fight", "Let them lead, counter"),
        ("5", "target_body", "Target Body", "Attack the body"),
        ("6", "target_legs", "Target Legs", "Leg kicks to slow them"),
        ("7", "check_leg_kicks", "Check Kicks", "Defend leg kicks"),
    ]
    
    def get_stance_menu(self) -> List[Tuple[str, str]]:
        """Get stance options for display."""
        return [(key, f"{name} - {desc}") for key, name, desc in self.STANCE_OPTIONS]
    
    def get_focus_menu(self) -> List[Tuple[str, str]]:
        """Get focus options for display."""
        return [(key, f"{name} - {desc}") for key, name, desc in self.FOCUS_OPTIONS]
    
    def get_priority_menu(self) -> List[Tuple[str, str]]:
        """Get priority options for display."""
        return [(key, f"{name} - {desc}") for key, name, desc in self.PRIORITY_OPTIONS]
    
    def get_tactics_menu(self) -> List[Tuple[str, str]]:
        """Get tactics options for display."""
        return [(key, f"{name} - {desc}") for key, _, name, desc in self.TACTICS_OPTIONS]
    
    def stance_from_choice(self, choice: str) -> str:
        """Convert menu choice to stance value."""
        for key, value, _ in self.STANCE_OPTIONS:
            if key == choice:
                return value
        return "BALANCED"
    
    def focus_from_choice(self, choice: str) -> str:
        """Convert menu choice to focus value."""
        for key, value, _ in self.FOCUS_OPTIONS:
            if key == choice:
                return value
        return "MIXED"
    
    def priority_from_choice(self, choice: str) -> str:
        """Convert menu choice to priority value."""
        for key, value, _ in self.PRIORITY_OPTIONS:
            if key == choice:
                return value
        return "FINISH"
    
    def tactic_from_choice(self, choice: str) -> Optional[str]:
        """Convert menu choice to tactic key."""
        for key, attr, _, _ in self.TACTICS_OPTIONS:
            if key == choice:
                return attr
        return None
    
    def build_gameplan_from_choices(
        self,
        stance_choice: str,
        focus_choice: str,
        priority_choice: str,
        tactic_choices: List[str],
    ) -> Gameplan:
        """Build a gameplan from menu choices."""
        tactics = {}
        for choice in tactic_choices:
            tactic = self.tactic_from_choice(choice)
            if tactic:
                tactics[tactic] = True
        
        return create_gameplan(
            stance=self.stance_from_choice(stance_choice),
            focus=self.focus_from_choice(focus_choice),
            priority=self.priority_from_choice(priority_choice),
            **tactics
        )


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def get_stance_description(stance: str) -> str:
    """Get human-readable stance description."""
    descriptions = {
        "AGGRESSIVE": "High pressure, looking to finish",
        "BALANCED": "Measured approach, looking for openings",
        "DEFENSIVE": "Counter-fighting, making opponent lead",
        "MEASURED": "Patient, picking shots carefully",
    }
    return descriptions.get(stance, stance)


def get_focus_description(focus: str) -> str:
    """Get human-readable focus description."""
    descriptions = {
        "STRIKING": "Keeping it standing, looking for the knockout",
        "GRAPPLING": "Taking the fight to the ground",
        "MIXED": "Using all weapons, well-rounded attack",
        "CLINCH": "Working in the clinch, dirty boxing",
    }
    return descriptions.get(focus, focus)


def get_priority_description(priority: str) -> str:
    """Get human-readable priority description."""
    descriptions = {
        "KNOCKOUT": "Hunting the knockout",
        "SUBMISSION": "Looking for the submission",
        "DECISION": "Point fighting, outworking opponent",
        "FINISH": "Looking for any finish",
        "SURVIVAL": "Just trying to survive",
    }
    return descriptions.get(priority, priority)


def format_gameplan(gameplan: Gameplan) -> str:
    """Format gameplan for display."""
    lines = [
        f"Stance: {gameplan.stance} - {get_stance_description(gameplan.stance)}",
        f"Focus: {gameplan.focus} - {get_focus_description(gameplan.focus)}",
        f"Priority: {gameplan.priority} - {get_priority_description(gameplan.priority)}",
    ]
    
    tactics = []
    if gameplan.wrestle_heavy:
        tactics.append("Wrestle Heavy")
    if gameplan.avoid_ground:
        tactics.append("Keep It Standing")
    if gameplan.pressure_cage:
        tactics.append("Pressure Fighter")
    if gameplan.counter_fight:
        tactics.append("Counter Puncher")
    if gameplan.target_body:
        tactics.append("Body Work")
    if gameplan.target_legs:
        tactics.append("Leg Kicks")
    if gameplan.check_leg_kicks:
        tactics.append("Check Kicks")
    
    if tactics:
        lines.append(f"Tactics: {', '.join(tactics)}")
    
    if gameplan.round_strategies:
        strats = [f"R{r}: {s}" for r, s in sorted(gameplan.round_strategies.items())]
        lines.append(f"Round Plans: {', '.join(strats)}")
    
    return "\n".join(lines)


def format_gameplan_compact(gameplan: Gameplan) -> str:
    """Format gameplan in a compact single-line format."""
    parts = [gameplan.stance, gameplan.focus]
    
    if gameplan.wrestle_heavy:
        parts.append("Wrestle")
    if gameplan.avoid_ground:
        parts.append("TDD")
    if gameplan.counter_fight:
        parts.append("Counter")
    if gameplan.pressure_cage:
        parts.append("Pressure")
    
    if gameplan.priority not in ["FINISH"]:
        parts.append(gameplan.priority)
    
    return " / ".join(parts)


def get_gameplan_summary(gameplan: Gameplan) -> str:
    """Get short one-line summary of gameplan."""
    return format_gameplan_compact(gameplan)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "Gameplan",
    "GameplanModifiers",
    "MatchupAnalysis",
    "GameplanOption",
    
    # Enums
    "Stance",
    "Focus", 
    "Priority",
    "RoundStrategy",
    
    # Constants
    "STANCE_MODIFIERS",
    "FOCUS_MODIFIERS",
    "PRIORITY_MODIFIERS",
    "ROUND_STRATEGY_MODIFIERS",
    "TACTICAL_MODIFIERS",
    
    # Core functions
    "create_gameplan",
    "get_default_gameplan",
    "get_gameplan_modifiers",
    
    # Matchup analysis (NEW)
    "get_matchup_analysis",
    "get_gameplan_options",
    
    # Matchup functions
    "get_matchup_adjustment",
    "gameplans_clash",
    
    # AI functions
    "generate_ai_gameplan",
    "adjust_gameplan_for_situation",
    
    # Recommendation functions
    "recommend_gameplan",
    "get_gameplan_warnings",
    
    # CLI helpers
    "GameplanMenuHelper",
    
    # Display helpers
    "get_stance_description",
    "get_focus_description",
    "get_priority_description",
    "format_gameplan",
    "format_gameplan_compact",
    "get_gameplan_summary",
]
