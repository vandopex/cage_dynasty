# systems/popularity.py
# Module: Popularity System
# Lines: ~200
#
# Handles fighter popularity calculations and effects.
# Popularity affects card positioning, sponsorships, fight offers, and gates.

"""
Cage Dynasty - Popularity System

Fighter popularity (0-100) represents their drawing power and name recognition.

EFFECTS:
- Card positioning (star power affects slot)
- Sponsorship value (higher popularity = better deals)
- Fight offers (popular fighters get offered bigger fights)
- PPV/gate contribution (affects promotion revenue)

SOURCES:
- Starting tier (elite fighters start more popular)
- Wins: +2-4
- Finishes (KO/Sub): +3-5 bonus
- Title wins: +10-15
- Title defenses: +5-8
- Undefeated streak bonus: +2 per win after 3
- Losses: -1 to -3
- Losing streak penalty: -2 per loss after 2
- Inactivity decay: -2 per month after 6 months inactive
"""

from typing import Optional, Tuple
import random


# ============================================================================
# CONSTANTS
# ============================================================================

# Starting popularity by skill tier
TIER_STARTING_POPULARITY = {
    "elite": (35, 50),
    "top": (25, 40),
    "good": (15, 30),
    "average": (8, 18),
    "developing": (5, 12),
    "novice": (3, 10),
}

# Popularity changes from fight results
POPULARITY_WIN = (2, 4)
POPULARITY_FINISH_BONUS = (3, 5)
POPULARITY_TITLE_WIN = (10, 15)
POPULARITY_TITLE_DEFENSE = (5, 8)
POPULARITY_LOSS = (-3, -1)
POPULARITY_LOSS_STREAK_PENALTY = -2
POPULARITY_UNDEFEATED_BONUS = 2

# Decay
POPULARITY_DECAY_THRESHOLD_WEEKS = 26  # 6 months
POPULARITY_DECAY_RATE = 2  # Per month after threshold

# Card building weights
RANK_WEIGHT = 0.7
POPULARITY_WEIGHT = 0.3

# Main event requirements
MAIN_EVENT_MIN_COMBINED_POPULARITY = 100
MAIN_EVENT_STAR_COMBINED_POPULARITY = 120


# ============================================================================
# POPULARITY CALCULATION FUNCTIONS
# ============================================================================

def calculate_popularity_change(
    won: bool,
    method: str,
    was_title_fight: bool = False,
    was_title_defense: bool = False,
    win_streak: int = 0,
    loss_streak: int = 0,
    current_popularity: int = 10,
) -> int:
    """
    Calculate popularity change from a fight result.
    
    Args:
        won: Whether the fighter won
        method: Fight ending method (KO, TKO, SUB, DEC, etc.)
        was_title_fight: Whether this was a title fight
        was_title_defense: Whether this was a title defense (champion won)
        win_streak: Current win streak (after this fight)
        loss_streak: Current loss streak (after this fight)
        current_popularity: Fighter's current popularity
        
    Returns:
        Popularity change (positive or negative)
    """
    change = 0
    
    if won:
        # Base win bonus
        change += random.randint(*POPULARITY_WIN)
        
        # Finish bonus
        if method in ("KO", "TKO", "SUB", "Submission"):
            change += random.randint(*POPULARITY_FINISH_BONUS)
        
        # Title bonuses
        if was_title_fight:
            if was_title_defense:
                change += random.randint(*POPULARITY_TITLE_DEFENSE)
            else:
                change += random.randint(*POPULARITY_TITLE_WIN)
        
        # Undefeated bonus (after 3 wins)
        if win_streak > 3 and loss_streak == 0:
            change += POPULARITY_UNDEFEATED_BONUS
    else:
        # Base loss penalty
        change += random.randint(*POPULARITY_LOSS)
        
        # Additional penalty for losing streak
        if loss_streak > 2:
            change += POPULARITY_LOSS_STREAK_PENALTY * (loss_streak - 2)
    
    # Diminishing returns at high popularity
    if current_popularity > 80 and change > 0:
        change = change // 2
    
    return change


def apply_popularity_decay(
    current_popularity: int,
    weeks_since_last_fight: int,
) -> int:
    """
    Calculate popularity decay for inactive fighters.
    
    Fighters lose popularity if inactive for more than 6 months.
    
    Args:
        current_popularity: Fighter's current popularity
        weeks_since_last_fight: Weeks since their last fight
        
    Returns:
        New popularity value
    """
    if weeks_since_last_fight <= POPULARITY_DECAY_THRESHOLD_WEEKS:
        return current_popularity
    
    # Calculate months of inactivity beyond threshold
    extra_weeks = weeks_since_last_fight - POPULARITY_DECAY_THRESHOLD_WEEKS
    months_inactive = extra_weeks // 4
    
    # Apply decay
    decay = months_inactive * POPULARITY_DECAY_RATE
    
    return max(5, current_popularity - decay)


def calculate_star_power(
    fighter1_rank: Optional[int],
    fighter2_rank: Optional[int],
    fighter1_popularity: int,
    fighter2_popularity: int,
    is_title_fight: bool = False,
) -> float:
    """
    Calculate combined star power for card positioning.
    
    Higher star power = higher card position.
    
    Args:
        fighter1_rank: Rank of fighter 1 (None = unranked, 0 = champion)
        fighter2_rank: Rank of fighter 2
        fighter1_popularity: Popularity of fighter 1 (0-100)
        fighter2_popularity: Popularity of fighter 2 (0-100)
        is_title_fight: Whether this is a title fight
        
    Returns:
        Star power score (0-300+)
    """
    # Title fights always get max priority
    if is_title_fight:
        return 300
    
    # Calculate rank score (lower rank = higher score)
    def rank_to_score(rank: Optional[int]) -> float:
        if rank is None or rank < 0:
            return 5  # Unranked
        if rank == 0:
            return 100  # Champion
        if rank <= 3:
            return 80 - (rank * 5)  # Top 3: 75, 70, 65
        if rank <= 5:
            return 60 - (rank * 3)  # 4-5: 48, 45
        if rank <= 10:
            return 35 - (rank * 2)  # 6-10: 23-15
        return max(5, 20 - rank)  # 11-15
    
    r1_score = rank_to_score(fighter1_rank)
    r2_score = rank_to_score(fighter2_rank)
    
    # Combined rank score (weighted 70%)
    rank_score = (r1_score + r2_score) * RANK_WEIGHT
    
    # Combined popularity score (weighted 30%)
    pop_score = (fighter1_popularity + fighter2_popularity) * POPULARITY_WEIGHT
    
    return rank_score + pop_score


def is_main_event_worthy(
    fighter1_rank: Optional[int],
    fighter2_rank: Optional[int],
    fighter1_popularity: int,
    fighter2_popularity: int,
    is_title_fight: bool = False,
) -> bool:
    """
    Determine if a fight qualifies for main event.
    
    Requirements (must meet at least one):
    1. Title fight
    2. Both fighters top 3 ranked
    3. Combined popularity >= 120
    4. One fighter is champion-level (rank 0 or popularity 70+)
    
    AND minimum requirement:
    - At least one fighter top 5 OR combined popularity >= 100
    """
    # Title fights always qualify
    if is_title_fight:
        return True
    
    combined_pop = fighter1_popularity + fighter2_popularity
    
    # Check if it's even close to main event material
    r1_top5 = fighter1_rank is not None and 0 <= fighter1_rank <= 5
    r2_top5 = fighter2_rank is not None and 0 <= fighter2_rank <= 5
    
    # Minimum requirement
    if not (r1_top5 or r2_top5 or combined_pop >= MAIN_EVENT_MIN_COMBINED_POPULARITY):
        return False
    
    # Check qualifying criteria
    
    # Top 3 clash
    r1_top3 = fighter1_rank is not None and 0 <= fighter1_rank <= 3
    r2_top3 = fighter2_rank is not None and 0 <= fighter2_rank <= 3
    if r1_top3 and r2_top3:
        return True
    
    # Star power combined
    if combined_pop >= MAIN_EVENT_STAR_COMBINED_POPULARITY:
        return True
    
    # Champion-level fighter involved
    is_star1 = fighter1_rank == 0 or fighter1_popularity >= 70
    is_star2 = fighter2_rank == 0 or fighter2_popularity >= 70
    if is_star1 or is_star2:
        return True
    
    return False


def get_card_slot_recommendation(
    fighter1_rank: Optional[int],
    fighter2_rank: Optional[int],
    fighter1_popularity: int,
    fighter2_popularity: int,
    is_title_fight: bool = False,
) -> str:
    """
    Get recommended card slot based on ranks and popularity.
    
    Returns: "main_event", "co_main", "main_card", "prelim", or "early_prelim"
    """
    if is_title_fight:
        return "main_event"
    
    star_power = calculate_star_power(
        fighter1_rank, fighter2_rank,
        fighter1_popularity, fighter2_popularity,
        is_title_fight
    )
    
    # Check main event eligibility
    if is_main_event_worthy(
        fighter1_rank, fighter2_rank,
        fighter1_popularity, fighter2_popularity,
        is_title_fight
    ):
        return "main_event"
    
    # Co-main: High star power but not main event level
    if star_power >= 80:
        return "co_main"
    
    # Main card: Decent ranked fighters or good popularity
    if star_power >= 50:
        return "main_card"
    
    # Prelim: Lower ranked fighters
    if star_power >= 25:
        return "prelim"
    
    # Early prelim: Unranked
    return "early_prelim"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Functions
    "calculate_popularity_change",
    "apply_popularity_decay",
    "calculate_star_power",
    "is_main_event_worthy",
    "get_card_slot_recommendation",
    
    # Constants
    "TIER_STARTING_POPULARITY",
    "POPULARITY_WIN",
    "POPULARITY_FINISH_BONUS",
    "POPULARITY_TITLE_WIN",
    "POPULARITY_TITLE_DEFENSE",
    "POPULARITY_LOSS",
    "POPULARITY_DECAY_THRESHOLD_WEEKS",
    "RANK_WEIGHT",
    "POPULARITY_WEIGHT",
]
