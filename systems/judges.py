# systems/judges.py
# Module: Judge & Decision System
# Lines: ~350
#
# Generates realistic judge scorecards and decision types.
# Adds narrative variety to fights that go to decision.

"""
Cage Dynasty - Judge System

This module handles all judge-related logic:
- Generate round-by-round scorecards
- Determine decision type (unanimous, split, majority)
- Detect controversial decisions ("robberies")
- Create narrative variety for decision outcomes

DECISION TYPES:
===============
- Unanimous Decision (UD): All 3 judges score for same fighter
- Split Decision (SD): 2 judges for winner, 1 for loser
- Majority Decision (MD): 2 judges for winner, 1 draw
- Draw (rare): Split or all judges score draw

CONTROVERSY SYSTEM:
==================
- Close fights have higher split decision chance
- Some decisions are flagged as "controversial"
- Creates narrative moments ("robbery", "gift decision")

USAGE:
    from systems.judges import (
        generate_decision,
        DecisionResult,
    )
    
    # After a fight goes to decision
    result = generate_decision(
        winner_dominance=0.55,  # How dominant the winner was
        total_rounds=3,
        is_title_fight=True,
    )
    
    print(result.decision_type)  # "Split Decision"
    print(result.scorecards)     # [(29, 28), (28, 29), (29, 28)]
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random


# ============================================================================
# DECISION TYPES
# ============================================================================

class DecisionType(Enum):
    """Types of judge decisions."""
    UNANIMOUS = "Unanimous Decision"
    SPLIT = "Split Decision"
    MAJORITY = "Majority Decision"
    DRAW = "Draw"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Scorecard:
    """A single judge's scorecard."""
    judge_name: str
    fighter1_score: int
    fighter2_score: int
    round_scores: List[Tuple[int, int]] = field(default_factory=list)
    
    @property
    def winner(self) -> Optional[int]:
        """Return 1 if fighter1 wins, 2 if fighter2, None if draw."""
        if self.fighter1_score > self.fighter2_score:
            return 1
        elif self.fighter2_score > self.fighter1_score:
            return 2
        return None
    
    def display(self) -> str:
        """Format scorecard for display."""
        return f"{self.judge_name}: {self.fighter1_score}-{self.fighter2_score}"


@dataclass
class DecisionResult:
    """Complete decision result with all scorecards."""
    decision_type: DecisionType
    winner: int  # 1 or 2, 0 for draw
    scorecards: List[Scorecard]
    is_controversial: bool = False
    controversy_reason: Optional[str] = None
    
    @property
    def is_split(self) -> bool:
        return self.decision_type == DecisionType.SPLIT
    
    @property
    def is_unanimous(self) -> bool:
        return self.decision_type == DecisionType.UNANIMOUS
    
    def get_scores_display(self) -> str:
        """Get formatted scores string like '29-28, 28-29, 29-28'."""
        scores = []
        for sc in self.scorecards:
            scores.append(f"{sc.fighter1_score}-{sc.fighter2_score}")
        return ", ".join(scores)
    
    def get_full_display(self) -> str:
        """Get complete decision display."""
        lines = [
            f"{self.decision_type.value}",
            f"Scores: {self.get_scores_display()}",
        ]
        if self.is_controversial:
            lines.append(f"⚠️ {self.controversy_reason}")
        return "\n".join(lines)


# ============================================================================
# JUDGE NAMES
# ============================================================================

JUDGE_NAMES = [
    "Sal D'Amato", "Chris Lee", "Derek Cleary", "Mike Bell",
    "Junichiro Kamijo", "Douglas Crosby", "Glenn Trowbridge",
    "Dave Hagen", "Tony Weeks", "Adalaide Byrd", "Cecil Peoples",
    "Patricia Morse Jarman", "Jeff Mullen", "Mark Ratner",
    "Nelson Hamilton", "Ricardo Barrera", "Marcos Rosales",
]


# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def generate_decision(
    winner_dominance: float,
    total_rounds: int = 3,
    is_title_fight: bool = False,
    fighter1_name: str = "Fighter 1",
    fighter2_name: str = "Fighter 2",
) -> DecisionResult:
    """
    Generate a complete decision with scorecards.
    
    Args:
        winner_dominance: How dominant the winner was (0.5 = dead even, 1.0 = total domination)
                         Values below 0.5 mean fighter 2 was dominant
        total_rounds: Number of rounds (3 or 5)
        is_title_fight: Title fights are scored more carefully
        fighter1_name: Name of fighter 1 (for narrative)
        fighter2_name: Name of fighter 2 (for narrative)
        
    Returns:
        DecisionResult with all scorecards and decision type
    """
    # Normalize dominance to 0-1 scale (0.5 = even)
    dominance = max(0.0, min(1.0, winner_dominance))
    
    # Determine actual winner (1 or 2)
    if dominance >= 0.5:
        actual_winner = 1
        margin = dominance - 0.5  # 0 to 0.5
    else:
        actual_winner = 2
        margin = 0.5 - dominance  # 0 to 0.5
    
    # Scale margin to 0-1 (how dominant the win was)
    margin_scaled = margin * 2  # 0 = dead even, 1 = total domination
    
    # Generate 3 judge scorecards
    judges = random.sample(JUDGE_NAMES, 3)
    scorecards = []
    
    for judge_name in judges:
        scorecard = _generate_scorecard(
            judge_name=judge_name,
            actual_winner=actual_winner,
            margin=margin_scaled,
            total_rounds=total_rounds,
            is_title_fight=is_title_fight,
        )
        scorecards.append(scorecard)
    
    # Determine decision type based on scorecards
    winners = [sc.winner for sc in scorecards]
    
    if all(w == actual_winner for w in winners):
        decision_type = DecisionType.UNANIMOUS
    elif winners.count(actual_winner) == 2:
        if None in winners:
            decision_type = DecisionType.MAJORITY
        else:
            decision_type = DecisionType.SPLIT
    elif winners.count(None) >= 2:
        decision_type = DecisionType.DRAW
        actual_winner = 0
    else:
        # Edge case: should be split
        decision_type = DecisionType.SPLIT
    
    # Check for controversy
    is_controversial, controversy_reason = _check_controversy(
        scorecards=scorecards,
        decision_type=decision_type,
        actual_winner=actual_winner,
        margin=margin_scaled,
        fighter1_name=fighter1_name,
        fighter2_name=fighter2_name,
    )
    
    return DecisionResult(
        decision_type=decision_type,
        winner=actual_winner,
        scorecards=scorecards,
        is_controversial=is_controversial,
        controversy_reason=controversy_reason,
    )


def _generate_scorecard(
    judge_name: str,
    actual_winner: int,
    margin: float,
    total_rounds: int,
    is_title_fight: bool,
) -> Scorecard:
    """Generate a single judge's scorecard."""
    round_scores = []
    
    # Base score per round is 10-9
    # Can be 10-8 for dominant rounds, 10-10 for close
    
    for round_num in range(1, total_rounds + 1):
        # Determine round winner probability based on margin
        # Higher margin = more likely winner takes round
        winner_round_prob = 0.5 + (margin * 0.35)
        
        # Add some per-round variance
        round_variance = random.gauss(0, 0.1)
        round_prob = winner_round_prob + round_variance
        
        # Determine round winner
        if random.random() < round_prob:
            round_winner = actual_winner
        else:
            round_winner = 3 - actual_winner  # Flip to other fighter
        
        # Determine round score
        score_roll = random.random()
        
        if margin > 0.7 and score_roll < 0.15:
            # Dominant round: 10-8
            if round_winner == 1:
                round_scores.append((10, 8))
            else:
                round_scores.append((8, 10))
        elif margin < 0.15 and score_roll < 0.08:
            # Very close: 10-10
            round_scores.append((10, 10))
        else:
            # Standard: 10-9
            if round_winner == 1:
                round_scores.append((10, 9))
            else:
                round_scores.append((9, 10))
    
    # Add judge bias/error
    # Some judges are known for controversial scores
    if judge_name in ["Adalaide Byrd", "Cecil Peoples"] and random.random() < 0.15:
        # These judges occasionally have "interesting" scores
        if len(round_scores) > 0:
            flip_idx = random.randint(0, len(round_scores) - 1)
            old_score = round_scores[flip_idx]
            # Flip the round
            round_scores[flip_idx] = (old_score[1], old_score[0])
    
    # Calculate totals
    f1_total = sum(r[0] for r in round_scores)
    f2_total = sum(r[1] for r in round_scores)
    
    return Scorecard(
        judge_name=judge_name,
        fighter1_score=f1_total,
        fighter2_score=f2_total,
        round_scores=round_scores,
    )


def _check_controversy(
    scorecards: List[Scorecard],
    decision_type: DecisionType,
    actual_winner: int,
    margin: float,
    fighter1_name: str,
    fighter2_name: str,
) -> Tuple[bool, Optional[str]]:
    """Check if decision is controversial."""
    
    # Get winner/loser names
    winner_name = fighter1_name if actual_winner == 1 else fighter2_name
    loser_name = fighter2_name if actual_winner == 1 else fighter1_name
    
    # Check for wide disparity in scores
    total_diffs = []
    for sc in scorecards:
        diff = abs(sc.fighter1_score - sc.fighter2_score)
        total_diffs.append(diff)
    
    # If one judge has much different score than others
    if max(total_diffs) - min(total_diffs) >= 3:
        outlier_judge = scorecards[total_diffs.index(max(total_diffs))]
        return True, f"Wide scoring disparity from {outlier_judge.judge_name}"
    
    # Split decision in dominant fight is controversial
    if decision_type == DecisionType.SPLIT and margin > 0.6:
        return True, f"Questionable split decision - {winner_name} appeared dominant"
    
    # Very close fight unanimous is suspicious
    if decision_type == DecisionType.UNANIMOUS and margin < 0.15:
        return True, f"Surprisingly unanimous in a razor-close fight"
    
    # Rare: Check for "robbery" - loser had 2 judges
    loser_winner = 3 - actual_winner
    loser_cards = sum(1 for sc in scorecards if sc.winner == loser_winner)
    if loser_cards >= 2 and margin > 0.4:
        # This shouldn't happen often but creates stories
        return True, f"Controversial! Many felt {loser_name} won"
    
    return False, None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_decision_type_from_dominance(dominance: float) -> DecisionType:
    """
    Quick decision type based on dominance without full scorecard generation.
    
    For use when you just need decision type, not full scorecards.
    """
    margin = abs(dominance - 0.5) * 2
    
    roll = random.random()
    
    if margin > 0.6:
        # Dominant fight - almost always unanimous
        if roll < 0.90:
            return DecisionType.UNANIMOUS
        else:
            return DecisionType.SPLIT
    elif margin > 0.3:
        # Clear winner but competitive
        if roll < 0.70:
            return DecisionType.UNANIMOUS
        elif roll < 0.95:
            return DecisionType.SPLIT
        else:
            return DecisionType.MAJORITY
    else:
        # Very close fight
        if roll < 0.40:
            return DecisionType.UNANIMOUS
        elif roll < 0.85:
            return DecisionType.SPLIT
        elif roll < 0.98:
            return DecisionType.MAJORITY
        else:
            return DecisionType.DRAW


def format_decision_for_commentary(
    result: DecisionResult,
    winner_name: str,
    loser_name: str,
) -> str:
    """Format decision result for fight commentary."""
    
    if result.decision_type == DecisionType.DRAW:
        return f"This fight is declared a DRAW! Scores: {result.get_scores_display()}"
    
    lines = []
    
    if result.is_split:
        lines.append(f"After {len(result.scorecards[0].round_scores)} rounds, we go to the judges' scorecards...")
        lines.append(f"And we have a SPLIT DECISION!")
    elif result.decision_type == DecisionType.MAJORITY:
        lines.append(f"We have a MAJORITY DECISION!")
    else:
        lines.append(f"We have a UNANIMOUS DECISION!")
    
    # Add individual scores
    for sc in result.scorecards:
        if sc.winner == result.winner:
            lines.append(f"  {sc.judge_name} scores it {sc.fighter1_score}-{sc.fighter2_score}")
        else:
            lines.append(f"  {sc.judge_name} scores it {sc.fighter2_score}-{sc.fighter1_score} for {loser_name}")
    
    lines.append(f"Your winner by {result.decision_type.value}... {winner_name}!")
    
    if result.is_controversial:
        lines.append(f"")
        lines.append(f"⚠️ {result.controversy_reason}")
    
    return "\n".join(lines)


def calculate_dominance_from_fight(
    winner_rating: int,
    loser_rating: int,
    winner_strikes_landed: int = 0,
    loser_strikes_landed: int = 0,
    winner_control_time: int = 0,
    loser_control_time: int = 0,
) -> float:
    """
    Calculate dominance score from fight stats.
    
    Returns 0.5-1.0 (higher = more dominant for winner)
    """
    # Base dominance from rating difference
    rating_diff = winner_rating - loser_rating
    # 20 point diff = ~10% dominance boost
    base_dominance = 0.5 + (rating_diff / 100) * 0.5
    
    # Add strike differential if available
    if winner_strikes_landed + loser_strikes_landed > 0:
        strike_ratio = winner_strikes_landed / max(1, winner_strikes_landed + loser_strikes_landed)
        base_dominance += (strike_ratio - 0.5) * 0.3
    
    # Add control time differential if available
    if winner_control_time + loser_control_time > 0:
        control_ratio = winner_control_time / max(1, winner_control_time + loser_control_time)
        base_dominance += (control_ratio - 0.5) * 0.15
    
    # Add small randomness
    base_dominance += random.gauss(0, 0.03)
    
    return max(0.5, min(1.0, base_dominance))


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "DecisionType",
    
    # Data classes
    "Scorecard",
    "DecisionResult",
    
    # Main functions
    "generate_decision",
    "get_decision_type_from_dominance",
    "format_decision_for_commentary",
    "calculate_dominance_from_fight",
    
    # Constants
    "JUDGE_NAMES",
]
