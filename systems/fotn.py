# systems/fotn.py
# Fight of the Night System
# Lines: ~250
#
# Awards bonuses for the most exciting fights of each event.
# Based on action metrics: damage, knockdowns, submission attempts, back-and-forth action.

"""
Cage Dynasty - Fight of the Night System

This module handles FOTN selection and awards:
- Calculate excitement scores for each fight
- Select FOTN from event's fights
- Award bonuses to both fighters
- Track career FOTN awards

Scoring Formula:
    Score = (total_damage × 0.4) 
          - (damage_diff × 0.2)     # Close fights score higher
          + (knockdowns × 150)
          + (sub_attempts × 25)
          + Late finish bonus (+100 for R3+)
          + Method bonus (Split Dec +100, KO/TKO +75, Sub +50)
          + Title fight bonus (×1.2)

USAGE:
    from systems.fotn import (
        calculate_fotn_score,
        select_fotn,
        FOTN_BONUS
    )
    
    # After event fights complete
    fotn_result, fotn_score = select_fotn(fight_results)
    if fotn_result:
        # Award bonuses to both fighters
        winner.career_fotn_awards += 1
        loser.career_fotn_awards += 1
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


# ============================================================================
# CONSTANTS
# ============================================================================

FOTN_BONUS = 50000  # $50,000 bonus to each fighter
MIN_FIGHTS_FOR_FOTN = 2  # Need at least 2 fights to award FOTN


# ============================================================================
# FOTN SCORING
# ============================================================================

def calculate_fotn_score(fight_result: Dict[str, Any]) -> float:
    """
    Calculate Fight of the Night score for a single fight.
    
    Args:
        fight_result: Dict containing fight data with keys:
            - fighter1_stats: List[Dict] - round-by-round stats for fighter 1
            - fighter2_stats: List[Dict] - round-by-round stats for fighter 2
            - method: str - how the fight ended
            - finish_round: int or None - round the fight ended
            - is_title_fight: bool - whether this was a title fight
            - winner_id: str - ID of the winner
            - loser_id: str - ID of the loser
    
    Returns:
        float: Excitement score (higher = more exciting)
    """
    score = 0.0
    
    # Get stats
    f1_stats = fight_result.get("fighter1_stats", [])
    f2_stats = fight_result.get("fighter2_stats", [])
    
    if not f1_stats and not f2_stats:
        # No detailed stats available - use basic scoring
        return _calculate_basic_score(fight_result)
    
    # Calculate totals from round-by-round stats
    f1_total_damage = 0.0
    f2_total_damage = 0.0
    total_knockdowns = 0
    total_sub_attempts = 0
    
    for round_stats in f1_stats:
        f1_total_damage += round_stats.get("damage", 0) or round_stats.get("damage_dealt", 0)
        total_knockdowns += round_stats.get("knockdowns", 0)
        total_sub_attempts += round_stats.get("sub_att", 0) or round_stats.get("submission_attempts", 0)
    
    for round_stats in f2_stats:
        f2_total_damage += round_stats.get("damage", 0) or round_stats.get("damage_dealt", 0)
        total_knockdowns += round_stats.get("knockdowns", 0)
        total_sub_attempts += round_stats.get("sub_att", 0) or round_stats.get("submission_attempts", 0)
    
    total_damage = f1_total_damage + f2_total_damage
    damage_diff = abs(f1_total_damage - f2_total_damage)
    
    # Base score from action
    score += total_damage * 0.4
    score -= damage_diff * 0.2  # Close fights score higher
    score += total_knockdowns * 150
    score += total_sub_attempts * 25
    
    # Method bonus
    method = fight_result.get("method", "")
    if "Split" in method or "SPLIT" in method:
        score += 100  # Split decisions are exciting close fights
    elif "KO" in method and "TKO" not in method:
        score += 75  # Clean KOs are exciting
    elif "TKO" in method:
        score += 60  # TKOs are exciting
    elif "SUB" in method or "Submission" in method:
        score += 50  # Submissions are exciting
    
    # Late finish bonus (drama)
    finish_round = fight_result.get("finish_round")
    if finish_round and finish_round >= 3:
        score += 100  # Late finishes are dramatic
    elif not finish_round:
        # Decision - went the distance
        num_rounds = len(f1_stats) if f1_stats else 3
        if num_rounds >= 3:
            score += 30  # Full fight has more action
    
    # Title fight multiplier
    if fight_result.get("is_title_fight"):
        score *= 1.2
    
    return score


def _calculate_basic_score(fight_result: Dict[str, Any]) -> float:
    """
    Calculate basic FOTN score when detailed stats aren't available.
    Uses method and round info only.
    """
    score = 50.0  # Base score
    
    method = fight_result.get("method", "")
    finish_round = fight_result.get("finish_round")
    
    # Method scoring
    if "Split" in method or "SPLIT" in method:
        score += 80
    elif "KO" in method and "TKO" not in method:
        score += 60
    elif "TKO" in method:
        score += 50
    elif "SUB" in method or "Submission" in method:
        score += 45
    elif "Decision" in method or "DEC" in method:
        score += 20
    
    # Round bonus
    if finish_round:
        if finish_round >= 3:
            score += 50  # Late finish
        elif finish_round == 2:
            score += 25
    
    # Title fight bonus
    if fight_result.get("is_title_fight"):
        score *= 1.2
    
    return score


def select_fotn(fight_results: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Select the Fight of the Night from a list of fight results.
    
    Args:
        fight_results: List of fight result dictionaries
    
    Returns:
        Tuple of (winning fight result dict, score) or (None, 0) if no FOTN
    """
    if len(fight_results) < MIN_FIGHTS_FOR_FOTN:
        return None, 0.0
    
    scored_fights = []
    
    for fight in fight_results:
        score = calculate_fotn_score(fight)
        scored_fights.append((fight, score))
    
    if not scored_fights:
        return None, 0.0
    
    # Sort by score descending
    scored_fights.sort(key=lambda x: x[1], reverse=True)
    
    best_fight, best_score = scored_fights[0]
    
    # Minimum score threshold - fight should be somewhat exciting
    if best_score < 30:
        return None, 0.0
    
    return best_fight, best_score


def format_fotn_announcement(
    fight_result: Dict[str, Any],
    score: float,
    fighter1_name: str,
    fighter2_name: str
) -> str:
    """
    Format the FOTN announcement string.
    
    Args:
        fight_result: The winning fight
        score: The FOTN score
        fighter1_name: Name of fighter 1
        fighter2_name: Name of fighter 2
    
    Returns:
        Formatted announcement string
    """
    bonus_str = f"${FOTN_BONUS:,}"
    return f"🔥 FIGHT OF THE NIGHT: {fighter1_name} vs {fighter2_name} ({bonus_str} bonus each)"


# ============================================================================
# FOTN RESULT DATA CLASS
# ============================================================================

@dataclass
class FOTNResult:
    """Result of FOTN selection for an event"""
    fighter1_id: str
    fighter1_name: str
    fighter2_id: str
    fighter2_name: str
    score: float
    bonus_amount: int = FOTN_BONUS
    method: str = ""
    was_title_fight: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter1_id": self.fighter1_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_id": self.fighter2_id,
            "fighter2_name": self.fighter2_name,
            "score": self.score,
            "bonus_amount": self.bonus_amount,
            "method": self.method,
            "was_title_fight": self.was_title_fight,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FOTNResult":
        return cls(**data)


def create_fotn_result(
    fight_result: Dict[str, Any],
    score: float,
    fighter1_name: str,
    fighter2_name: str
) -> FOTNResult:
    """
    Create a FOTNResult from fight data.
    
    Args:
        fight_result: The fight result dict
        score: The calculated score
        fighter1_name: Name of fighter 1
        fighter2_name: Name of fighter 2
    
    Returns:
        FOTNResult object
    """
    return FOTNResult(
        fighter1_id=fight_result.get("fighter1_id", fight_result.get("winner_id", "")),
        fighter1_name=fighter1_name,
        fighter2_id=fight_result.get("fighter2_id", fight_result.get("loser_id", "")),
        fighter2_name=fighter2_name,
        score=score,
        method=fight_result.get("method", ""),
        was_title_fight=fight_result.get("is_title_fight", False),
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_fight_exciting(fight_result: Dict[str, Any], threshold: float = 100.0) -> bool:
    """
    Check if a fight meets the excitement threshold.
    
    Args:
        fight_result: Fight result dict
        threshold: Minimum score to be considered exciting
    
    Returns:
        True if fight is exciting
    """
    score = calculate_fotn_score(fight_result)
    return score >= threshold


def get_excitement_tier(score: float) -> str:
    """
    Get a descriptive tier for the excitement score.
    
    Args:
        score: FOTN score
    
    Returns:
        Tier description
    """
    if score >= 300:
        return "INSTANT CLASSIC"
    elif score >= 200:
        return "Fight of the Year Candidate"
    elif score >= 150:
        return "Excellent"
    elif score >= 100:
        return "Great"
    elif score >= 50:
        return "Good"
    else:
        return "Standard"


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    # Quick test
    test_fight = {
        "fighter1_stats": [
            {"damage_dealt": 50, "knockdowns": 1, "sub_att": 0},
            {"damage_dealt": 40, "knockdowns": 0, "sub_att": 1},
            {"damage_dealt": 60, "knockdowns": 1, "sub_att": 0},
        ],
        "fighter2_stats": [
            {"damage_dealt": 45, "knockdowns": 0, "sub_att": 0},
            {"damage_dealt": 55, "knockdowns": 1, "sub_att": 0},
            {"damage_dealt": 35, "knockdowns": 0, "sub_att": 2},
        ],
        "method": "KO",
        "finish_round": 3,
        "is_title_fight": True,
        "winner_id": "f1",
        "loser_id": "f2",
    }
    
    score = calculate_fotn_score(test_fight)
    print(f"Test fight score: {score:.1f}")
    print(f"Excitement tier: {get_excitement_tier(score)}")
    
    # Test with no stats
    basic_fight = {
        "method": "Split Decision",
        "finish_round": None,
        "is_title_fight": False,
    }
    basic_score = calculate_fotn_score(basic_fight)
    print(f"Basic fight score: {basic_score:.1f}")
    
    print("\nFOTN module loaded successfully!")
