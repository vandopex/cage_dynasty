# systems/matchmaking.py
# Module 12: Matchmaking Engine
# Lines: ~950
#
# Intelligent matchmaking system that finds and scores potential fights.
# Considers rankings, streaks, rivalries, recency, cooldowns, and entertainment value.

"""
Cage Dynasty - Matchmaking Engine

This module handles all aspects of fight matchmaking:
- Finding eligible opponents for a fighter
- Scoring potential matchups by multiple criteria
- Title fight logic and mandatory challengers
- Avoiding recent rematches
- Balancing competitive and entertaining fights
- Fighter cooldown system (winners fight sooner, losers wait longer)
- Ranked vs Ranked preference for realistic matchmaking

The matchmaker aims to create fights that are:
1. Competitively fair (similar skill/ranking)
2. Narratively interesting (rivalries, streaks)
3. Logistically possible (both available, not on cooldown)
4. Fresh (not immediate rematches)
5. Realistic (ranked fight ranked, unranked fight unranked)

COOLDOWN SYSTEM:
================
Winners: 4 weeks minimum
Losers: 6 weeks + 2 per loss in streak (max 12)
Champions: 8 weeks minimum (title fights are special)
"""

from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import date
import random

# Try multiple import paths for flexibility
try:
    from core.types import WeightClass, EventType, FighterStatus
    from core.events import emit
    from core.config import get_config
    from core.calendar import calendar, GameDate
except ImportError:
    try:
        from types import WeightClass, EventType, FighterStatus
        from events import emit
        from config import get_config
        from calendar import calendar, GameDate
    except ImportError:
        # Minimal fallback for standalone testing
        from enum import Enum
        
        class WeightClass(Enum):
            STRAWWEIGHT = "Strawweight"
            FLYWEIGHT = "Flyweight"
            BANTAMWEIGHT = "Bantamweight"
            FEATHERWEIGHT = "Featherweight"
            LIGHTWEIGHT = "Lightweight"
            WELTERWEIGHT = "Welterweight"
            MIDDLEWEIGHT = "Middleweight"
            LIGHT_HEAVYWEIGHT = "Light Heavyweight"
            HEAVYWEIGHT = "Heavyweight"
        
        class FighterStatus(Enum):
            ACTIVE = "Active"
            INJURED = "Injured"
            RETIRED = "Retired"
            FREE_AGENT = "Free Agent"
        
        class EventType(Enum):
            MATCHUP_CREATED = "matchup_created"
        
        def emit(event_type, data):
            pass
        
        def get_config(key, default):
            return default
        
        @dataclass
        class GameDate:
            year: int
            month: int
            day: int
            
            def weeks_until(self, other: 'GameDate') -> int:
                return abs((other.year - self.year) * 52 + (other.month - self.month) * 4)
        
        class MockCalendar:
            current_date = GameDate(1, 1, 1)
            current_week = 1
        
        calendar = MockCalendar()


# ============================================================================
# COOLDOWN CONSTANTS
# ============================================================================

# Base cooldown in weeks
COOLDOWN_WINNER = 4          # Winners can fight again after 4 weeks
COOLDOWN_LOSER_BASE = 6      # Losers wait at least 6 weeks
COOLDOWN_LOSER_PER_LOSS = 2  # Additional weeks per loss in losing streak
COOLDOWN_LOSER_MAX = 12      # Maximum loser cooldown
COOLDOWN_CHAMPION = 8        # Champions wait longer between title defenses

# Ranked vs ranked probability
RANKED_VS_RANKED_PROBABILITY = 0.70  # 70% chance to match ranked fighters
RANKED_VS_UNRANKED_PROBABILITY = 0.40  # 40% chance for gatekeeper fights

# ============================================================================
# TITLE ELIGIBILITY CONSTANTS
# ============================================================================

# Title shot requirements - must meet ONE of these criteria
TITLE_MIN_RANK = 5           # Must be ranked #1-5 (top contender)
TITLE_MIN_FIGHTS_RECORD = 6  # OR: minimum fights with good record
TITLE_MIN_WIN_PCT = 0.70     # OR: minimum win percentage (with min fights)
TITLE_MIN_WINS = 8           # OR: minimum total wins (regardless of losses)
TITLE_MIN_PRO_FIGHTS = 3     # Minimum pro fights for ANY title shot


# ============================================================================
# MATCHUP TYPES
# ============================================================================

class MatchupType(Enum):
    """Categories of matchups"""
    TITLE_FIGHT = "Title Fight"
    TITLE_ELIMINATOR = "Title Eliminator"
    MAIN_EVENT = "Main Event"
    CO_MAIN = "Co-Main Event"
    MAIN_CARD = "Main Card"
    PRELIM = "Preliminary"
    DEBUT = "Debut Fight"


class MatchupReason(Enum):
    """Why a matchup was suggested"""
    RANKINGS_PROXIMITY = "Close in rankings"
    RIVALRY = "Ongoing rivalry"
    WIN_STREAK_CLASH = "Battle of win streaks"
    GATEKEEPER_TEST = "Veteran test for prospect"
    TITLE_SHOT = "Earned title opportunity"
    REMATCH = "Rubber match"
    STYLISTIC = "Exciting style matchup"
    RANDOM = "Available opponents"


# ============================================================================
# MATCHUP SCORE WEIGHTS
# ============================================================================

# Default weights for scoring matchups (can be configured)
DEFAULT_WEIGHTS = {
    "ranking_proximity": 30,      # Fighters close in rankings
    "skill_balance": 20,          # Similar overall ratings
    "streak_interest": 15,        # Win streaks make fights interesting
    "rivalry_bonus": 25,          # Rivalries are compelling
    "freshness": 10,              # Haven't fought recently
    "title_implications": 20,     # Stakes matter
    "entertainment": 10,          # Style matchups
}


# ============================================================================
# MATCHUP RESULT
# ============================================================================

@dataclass
class MatchupScore:
    """
    Detailed scoring breakdown for a potential matchup.
    """
    fighter1_id: str
    fighter2_id: str
    weight_class: WeightClass
    total_score: float
    
    # Component scores
    ranking_score: float = 0.0
    skill_score: float = 0.0
    streak_score: float = 0.0
    rivalry_score: float = 0.0
    freshness_score: float = 0.0
    title_score: float = 0.0
    entertainment_score: float = 0.0
    
    # Metadata
    matchup_type: MatchupType = MatchupType.MAIN_CARD
    reasons: List[MatchupReason] = field(default_factory=list)
    is_title_fight: bool = False
    is_rematch: bool = False
    
    # Fighter names for display
    fighter1_name: str = ""
    fighter2_name: str = ""
    
    def __str__(self) -> str:
        return f"{self.fighter1_id} vs {self.fighter2_id}: {self.total_score:.1f} pts"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter1_id": self.fighter1_id,
            "fighter2_id": self.fighter2_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_name": self.fighter2_name,
            "weight_class": self.weight_class.value,
            "total_score": self.total_score,
            "ranking_score": self.ranking_score,
            "skill_score": self.skill_score,
            "streak_score": self.streak_score,
            "rivalry_score": self.rivalry_score,
            "freshness_score": self.freshness_score,
            "title_score": self.title_score,
            "entertainment_score": self.entertainment_score,
            "matchup_type": self.matchup_type.value,
            "reasons": [r.value for r in self.reasons],
            "is_title_fight": self.is_title_fight,
            "is_rematch": self.is_rematch
        }


# ============================================================================
# FIGHTER INFO PROTOCOL
# ============================================================================

def _match_strength(fighter) -> float:
    """Derive a match-strength proxy from per-attribute stats.
    Used INSTEAD of overall_rating so OVR stays player-facing only
    (see memory/principle_OVR_player_facing_only.md). Weights
    striking, grappling, and physical roughly equally."""
    striking  = (getattr(fighter, 'boxing', 50) +
                 getattr(fighter, 'kicks', 50) +
                 getattr(fighter, 'clinch_striking', 50)) / 3
    grappling = (getattr(fighter, 'takedowns', 50) +
                 getattr(fighter, 'top_control', 50) +
                 getattr(fighter, 'submissions', 50)) / 3
    physical  = (getattr(fighter, 'strength', 50) +
                 getattr(fighter, 'cardio', 50) +
                 getattr(fighter, 'chin', 50)) / 3
    return (striking + grappling + physical) / 3


@dataclass
class FighterMatchInfo:
    """
    Information about a fighter needed for matchmaking.
    This is passed in rather than importing Fighter to avoid circular deps.
    """
    fighter_id: str
    name: str
    weight_class: WeightClass
    rank: Optional[int]  # None = unranked, 0 = champion
    overall_rating: int
    win_streak: int
    lose_streak: int
    wins: int
    losses: int
    is_champion: bool
    status: FighterStatus
    recent_opponents: List[str]  # Last 3-5 opponent IDs
    rivalry_ids: List[str]  # Fighter IDs they have rivalries with
    style_tags: List[str] = field(default_factory=list)  # "striker", "grappler", etc.

    # New fields for cooldown system
    last_fight_week: int = 0  # Week number of last fight
    camp_id: Optional[str] = None  # Camp ID to avoid same-camp fights
    # Derived match-strength — populated by factory from per-attribute
    # stats. Used by matchmaking decisions instead of overall_rating
    # so OVR remains player-facing only.
    match_strength: float = 50.0
    
    @property
    def is_available(self) -> bool:
        """Check if fighter can be booked (status only, not cooldown)"""
        return self.status == FighterStatus.ACTIVE
    
    @property
    def is_ranked(self) -> bool:
        """Check if fighter is ranked"""
        return self.rank is not None
    
    @property
    def is_contender(self) -> bool:
        """Top 5 ranked fighter"""
        return self.rank is not None and 1 <= self.rank <= 5
    
    @property
    def is_title_eligible(self) -> bool:
        """
        Check if fighter qualifies for a title shot.
        
        Champions are always eligible (they're defending).
        Challengers must have 3+ pro fights AND meet ONE of:
        - Ranked #1-5 (top contender)
        - 6+ fights with 70%+ win rate
        - 8+ wins total
        """
        if self.is_champion:
            return True
        
        # MUST have minimum pro fights
        total_fights = self.wins + self.losses
        if total_fights < TITLE_MIN_PRO_FIGHTS:
            return False
        
        # Check ranking eligibility
        if self.rank is not None and 1 <= self.rank <= TITLE_MIN_RANK:
            return True
        
        # Check record-based eligibility
        if total_fights >= TITLE_MIN_FIGHTS_RECORD:
            win_pct = self.wins / total_fights
            if win_pct >= TITLE_MIN_WIN_PCT:
                return True
        
        # Check total wins
        if self.wins >= TITLE_MIN_WINS:
            return True
        
        return False
    
    def get_cooldown_weeks(self) -> int:
        """
        Calculate required cooldown in weeks.
        
        Returns the minimum weeks a fighter must wait between fights.
        """
        if self.is_champion:
            return COOLDOWN_CHAMPION
        elif self.lose_streak > 0:
            # Losers wait longer, especially on losing streaks
            cooldown = COOLDOWN_LOSER_BASE + (self.lose_streak * COOLDOWN_LOSER_PER_LOSS)
            return min(cooldown, COOLDOWN_LOSER_MAX)
        else:
            return COOLDOWN_WINNER
    
    def is_on_cooldown(self, current_week: int) -> bool:
        """
        Check if fighter is still on cooldown from last fight.
        
        Args:
            current_week: Current game week number
            
        Returns:
            True if fighter cannot be booked yet
        """
        if self.last_fight_week == 0:
            return False  # Never fought, no cooldown
        
        weeks_since_fight = current_week - self.last_fight_week
        required_cooldown = self.get_cooldown_weeks()
        
        return weeks_since_fight < required_cooldown


# ============================================================================
# COOLDOWN HELPER FUNCTIONS
# ============================================================================

def calculate_cooldown(
    is_champion: bool,
    lose_streak: int,
    won_last_fight: bool = True
) -> int:
    """
    Calculate cooldown weeks for a fighter.
    
    Args:
        is_champion: Is this fighter a champion?
        lose_streak: Current losing streak (0 if won last)
        won_last_fight: Did they win their last fight?
        
    Returns:
        Number of weeks they must wait
    """
    if is_champion:
        return COOLDOWN_CHAMPION
    elif not won_last_fight or lose_streak > 0:
        cooldown = COOLDOWN_LOSER_BASE + (lose_streak * COOLDOWN_LOSER_PER_LOSS)
        return min(cooldown, COOLDOWN_LOSER_MAX)
    else:
        return COOLDOWN_WINNER


def weeks_until_available(
    last_fight_week: int,
    current_week: int,
    cooldown_weeks: int
) -> int:
    """
    Calculate weeks until fighter is available.
    
    Returns 0 if already available.
    """
    weeks_since = current_week - last_fight_week
    remaining = cooldown_weeks - weeks_since
    return max(0, remaining)


# ============================================================================
# TITLE ELIGIBILITY HELPER FUNCTIONS
# ============================================================================

def is_title_eligible(
    wins: int,
    losses: int,
    rank: Optional[int] = None,
    is_champion: bool = False
) -> bool:
    """
    Check if a fighter qualifies for a title shot.
    
    Champions are always eligible (defending).
    Challengers must have at least 3 pro fights AND meet ONE of:
    - Ranked #1-5 (top contender)
    - 6+ fights with 70%+ win rate  
    - 8+ wins total
    
    Args:
        wins: Total career wins
        losses: Total career losses
        rank: Current ranking (None if unranked)
        is_champion: Whether fighter is current champion
        
    Returns:
        True if fighter can receive/defend title shot
    """
    if is_champion:
        return True
    
    # MUST have minimum pro fights to challenge for title
    total_fights = wins + losses
    if total_fights < TITLE_MIN_PRO_FIGHTS:
        return False
    
    # Top contender (with minimum fights)
    if rank is not None and 1 <= rank <= TITLE_MIN_RANK:
        return True
    
    # Good record
    if total_fights >= TITLE_MIN_FIGHTS_RECORD:
        win_pct = wins / total_fights
        if win_pct >= TITLE_MIN_WIN_PCT:
            return True
    
    # Many wins
    if wins >= TITLE_MIN_WINS:
        return True
    
    return False


def can_be_title_fight(
    fighter1_wins: int,
    fighter1_losses: int,
    fighter1_rank: Optional[int],
    fighter1_is_champion: bool,
    fighter2_wins: int,
    fighter2_losses: int,
    fighter2_rank: Optional[int],
    fighter2_is_champion: bool
) -> bool:
    """
    Check if a matchup can be a title fight.
    
    Requires:
    - Exactly one fighter is champion
    - The non-champion is title eligible
    
    Args:
        fighter1/2 stats: Wins, losses, rank, and champion status
        
    Returns:
        True if this can be a title fight
    """
    # Need exactly one champion
    if fighter1_is_champion == fighter2_is_champion:
        return False  # Both or neither are champions
    
    # Check challenger eligibility
    if fighter1_is_champion:
        challenger_eligible = is_title_eligible(
            fighter2_wins, fighter2_losses, fighter2_rank, False
        )
    else:
        challenger_eligible = is_title_eligible(
            fighter1_wins, fighter1_losses, fighter1_rank, False
        )
    
    return challenger_eligible


def get_title_eligibility_reason(
    wins: int,
    losses: int,
    rank: Optional[int] = None
) -> Optional[str]:
    """
    Get the reason why a fighter IS or ISN'T title eligible.
    
    Returns:
        String explaining eligibility status, or None if not eligible
    """
    if rank is not None and 1 <= rank <= TITLE_MIN_RANK:
        return f"Top contender (#{rank})"
    
    total_fights = wins + losses
    if total_fights >= TITLE_MIN_FIGHTS_RECORD:
        win_pct = wins / total_fights
        if win_pct >= TITLE_MIN_WIN_PCT:
            return f"Strong record ({wins}-{losses}, {int(win_pct*100)}%)"
    
    if wins >= TITLE_MIN_WINS:
        return f"Veteran ({wins} career wins)"
    
    return None


# ============================================================================
# MATCHMAKING CALCULATOR FUNCTIONS
# ============================================================================

def calculate_ranking_score(
    fighter1: FighterMatchInfo,
    fighter2: FighterMatchInfo,
    max_score: float = 30.0
) -> float:
    """
    Score based on how close fighters are in rankings.
    
    Champion vs #1 = perfect score
    #1 vs #2 = near perfect
    #15 vs unranked = low score
    """
    rank1 = fighter1.rank if fighter1.rank is not None else 20
    rank2 = fighter2.rank if fighter2.rank is not None else 20
    
    # Champion is effectively rank 0
    if fighter1.is_champion:
        rank1 = 0
    if fighter2.is_champion:
        rank2 = 0
    
    rank_diff = abs(rank1 - rank2)
    
    # Perfect match = 0 difference, score decreases with gap
    if rank_diff == 0:
        return max_score
    elif rank_diff == 1:
        return max_score * 0.9
    elif rank_diff <= 3:
        return max_score * 0.7
    elif rank_diff <= 5:
        return max_score * 0.5
    elif rank_diff <= 10:
        return max_score * 0.3
    else:
        return max_score * 0.1


def calculate_skill_score(
    fighter1: FighterMatchInfo,
    fighter2: FighterMatchInfo,
    max_score: float = 20.0
) -> float:
    """
    Score based on overall rating similarity.
    
    Competitive fights are more interesting.
    """
    rating_diff = abs(fighter1.match_strength - fighter2.match_strength)

    if rating_diff <= 5:
        return max_score  # Very evenly matched
    elif rating_diff <= 10:
        return max_score * 0.8
    elif rating_diff <= 15:
        return max_score * 0.6
    elif rating_diff <= 20:
        return max_score * 0.4
    else:
        return max_score * 0.2


def calculate_streak_score(
    fighter1: FighterMatchInfo,
    fighter2: FighterMatchInfo,
    max_score: float = 15.0
) -> float:
    """
    Score based on win streaks.
    
    Two fighters on win streaks = exciting matchup.
    """
    streak1 = fighter1.win_streak
    streak2 = fighter2.win_streak
    
    # Both on win streaks is most interesting
    if streak1 >= 2 and streak2 >= 2:
        combined = min(streak1 + streak2, 10)  # Cap at 10
        return max_score * (combined / 10)
    
    # One on a streak
    max_streak = max(streak1, streak2)
    if max_streak >= 3:
        return max_score * 0.5
    elif max_streak >= 2:
        return max_score * 0.3
    
    return 0.0


def calculate_rivalry_score(
    fighter1: FighterMatchInfo,
    fighter2: FighterMatchInfo,
    max_score: float = 25.0
) -> float:
    """
    Score based on existing rivalry.
    
    Rivalry fights are always compelling.
    """
    if fighter2.fighter_id in fighter1.rivalry_ids:
        return max_score
    if fighter1.fighter_id in fighter2.rivalry_ids:
        return max_score
    return 0.0


def calculate_freshness_score(
    fighter1: FighterMatchInfo,
    fighter2: FighterMatchInfo,
    max_score: float = 10.0
) -> float:
    """
    Score based on not being a recent rematch.
    
    Fresh matchups are preferred over immediate rematches.
    """
    # Check if they've fought recently
    if fighter2.fighter_id in fighter1.recent_opponents:
        return 0.0  # Immediate rematch = no freshness
    if fighter1.fighter_id in fighter2.recent_opponents:
        return 0.0
    
    return max_score


def calculate_title_score(
    fighter1: FighterMatchInfo,
    fighter2: FighterMatchInfo,
    max_score: float = 20.0
) -> float:
    """
    Score based on title implications.
    
    Title fights and eliminators are high stakes.
    """
    # Title fight
    if fighter1.is_champion or fighter2.is_champion:
        return max_score
    
    # Title eliminator (both top 5)
    if fighter1.is_contender and fighter2.is_contender:
        return max_score * 0.8
    
    # One contender
    if fighter1.is_contender or fighter2.is_contender:
        return max_score * 0.4
    
    # Both ranked
    if fighter1.is_ranked and fighter2.is_ranked:
        return max_score * 0.2
    
    return 0.0


def calculate_entertainment_score(
    fighter1: FighterMatchInfo,
    fighter2: FighterMatchInfo,
    max_score: float = 10.0
) -> float:
    """
    Score based on stylistic matchup.
    
    Striker vs grappler = fireworks.
    """
    tags1 = set(fighter1.style_tags)
    tags2 = set(fighter2.style_tags)
    
    # Striker vs grappler is exciting
    if ("striker" in tags1 and "grappler" in tags2) or \
       ("grappler" in tags1 and "striker" in tags2):
        return max_score
    
    # Both finishers
    if "finisher" in tags1 and "finisher" in tags2:
        return max_score * 0.8
    
    # Some overlap = decent matchup
    if tags1 & tags2:
        return max_score * 0.3
    
    return max_score * 0.5  # Unknown styles = average


# ============================================================================
# MATCHMAKING ENGINE
# ============================================================================

class MatchmakingEngine:
    """
    Central engine for finding and scoring matchups.
    
    Usage:
        engine = MatchmakingEngine()
        
        # Add available fighters
        for fighter in roster:
            engine.add_fighter(fighter_info)
        
        # Set current week for cooldown calculations
        engine.set_current_week(52)
        
        # Find best opponent for a specific fighter
        matches = engine.find_opponents(fighter_id, limit=5)
        
        # Generate a full card with ranked vs ranked preference
        card = engine.generate_smart_card(weight_class, num_fights=10)
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize matchmaking engine.
        
        Args:
            weights: Custom scoring weights (uses defaults if not provided)
        """
        self._fighters: Dict[str, FighterMatchInfo] = {}
        self._weights = weights or DEFAULT_WEIGHTS.copy()
        self._booked_fighters: Set[str] = set()  # Currently booked
        self._recent_matchups: List[Tuple[str, str, GameDate]] = []  # History
        self._current_week: int = 1  # For cooldown calculations
    
    def set_current_week(self, week: int) -> None:
        """Set current week for cooldown calculations"""
        self._current_week = week
    
    def add_fighter(self, fighter: FighterMatchInfo) -> None:
        """Add a fighter to the matchmaking pool"""
        self._fighters[fighter.fighter_id] = fighter
    
    def remove_fighter(self, fighter_id: str) -> None:
        """Remove a fighter from the pool"""
        self._fighters.pop(fighter_id, None)
    
    def get_fighter(self, fighter_id: str) -> Optional[FighterMatchInfo]:
        """Get fighter info by ID"""
        return self._fighters.get(fighter_id)
    
    def set_booked(self, fighter_id: str) -> None:
        """Mark a fighter as booked (unavailable)"""
        self._booked_fighters.add(fighter_id)
    
    def clear_booked(self, fighter_id: str) -> None:
        """Mark a fighter as available again"""
        self._booked_fighters.discard(fighter_id)
    
    def clear_all_booked(self) -> None:
        """Clear all booked fighters"""
        self._booked_fighters.clear()
    
    def is_available(self, fighter_id: str, check_cooldown: bool = True) -> bool:
        """
        Check if fighter is available for booking.
        
        Args:
            fighter_id: Fighter to check
            check_cooldown: Whether to check cooldown (default True)
            
        Returns:
            True if fighter can be booked
        """
        fighter = self._fighters.get(fighter_id)
        if not fighter:
            return False
        
        # Check basic availability
        if not fighter.is_available:
            return False
        
        # Check if already booked
        if fighter_id in self._booked_fighters:
            return False
        
        # Check cooldown
        if check_cooldown and fighter.is_on_cooldown(self._current_week):
            return False
        
        return True
    
    def get_weeks_until_available(self, fighter_id: str) -> int:
        """Get weeks until fighter is available (0 if already available)"""
        fighter = self._fighters.get(fighter_id)
        if not fighter:
            return 0
        
        if fighter_id in self._booked_fighters:
            return -1  # Already booked, unknown return
        
        cooldown = fighter.get_cooldown_weeks()
        return weeks_until_available(
            fighter.last_fight_week, 
            self._current_week, 
            cooldown
        )
    
    def record_matchup(self, fighter1_id: str, fighter2_id: str) -> None:
        """Record that a matchup was made"""
        try:
            self._recent_matchups.append((fighter1_id, fighter2_id, calendar.current_date))
        except:
            pass  # Calendar may not be available
        
        # Keep only last 100 matchups
        if len(self._recent_matchups) > 100:
            self._recent_matchups = self._recent_matchups[-100:]
    
    def get_eligible_opponents(
        self,
        fighter_id: str,
        same_weight_class: bool = True,
        include_booked: bool = False,
        check_cooldown: bool = True,
        exclude_same_camp: bool = True
    ) -> List[FighterMatchInfo]:
        """
        Get all eligible opponents for a fighter.
        
        Args:
            fighter_id: Fighter looking for opponent
            same_weight_class: Only same weight class
            include_booked: Include currently booked fighters
            check_cooldown: Filter out fighters on cooldown
            exclude_same_camp: Exclude fighters from same camp
        
        Returns:
            List of eligible opponent infos
        """
        fighter = self._fighters.get(fighter_id)
        if not fighter:
            return []
        
        eligible = []
        for opp_id, opp in self._fighters.items():
            # Can't fight yourself
            if opp_id == fighter_id:
                continue
            
            # Check weight class
            if same_weight_class and opp.weight_class != fighter.weight_class:
                continue
            
            # Check availability
            if not include_booked:
                if opp_id in self._booked_fighters:
                    continue
                if not opp.is_available:
                    continue
            
            # Check cooldown
            if check_cooldown and opp.is_on_cooldown(self._current_week):
                continue
            
            # Check camp (no same-camp fights)
            if exclude_same_camp and fighter.camp_id and opp.camp_id:
                if fighter.camp_id == opp.camp_id:
                    continue
            
            eligible.append(opp)
        
        return eligible
    
    def get_ranked_fighters(
        self,
        weight_class: WeightClass,
        check_cooldown: bool = True
    ) -> List[FighterMatchInfo]:
        """
        Get all ranked fighters in a weight class.
        
        Returns fighters sorted by rank (champion first, then #1, #2, etc.)
        """
        fighters = []
        for f in self._fighters.values():
            if f.weight_class != weight_class:
                continue
            if not f.is_ranked and not f.is_champion:
                continue
            if not self.is_available(f.fighter_id, check_cooldown):
                continue
            fighters.append(f)
        
        # Sort by rank (champion = 0)
        def sort_key(f):
            if f.is_champion:
                return 0
            return f.rank if f.rank else 99
        
        fighters.sort(key=sort_key)
        return fighters
    
    def get_unranked_fighters(
        self,
        weight_class: WeightClass,
        check_cooldown: bool = True
    ) -> List[FighterMatchInfo]:
        """
        Get all unranked fighters in a weight class.
        
        Returns fighters sorted by overall rating (highest first).
        """
        fighters = []
        for f in self._fighters.values():
            if f.weight_class != weight_class:
                continue
            if f.is_ranked or f.is_champion:
                continue
            if not self.is_available(f.fighter_id, check_cooldown):
                continue
            fighters.append(f)
        
        fighters.sort(key=lambda f: -f.match_strength)
        return fighters
    
    def score_matchup(
        self,
        fighter1: FighterMatchInfo,
        fighter2: FighterMatchInfo
    ) -> MatchupScore:
        """
        Calculate comprehensive score for a potential matchup.
        """
        # Calculate component scores
        ranking = calculate_ranking_score(
            fighter1, fighter2, self._weights.get("ranking_proximity", 30)
        )
        skill = calculate_skill_score(
            fighter1, fighter2, self._weights.get("skill_balance", 20)
        )
        streak = calculate_streak_score(
            fighter1, fighter2, self._weights.get("streak_interest", 15)
        )
        rivalry = calculate_rivalry_score(
            fighter1, fighter2, self._weights.get("rivalry_bonus", 25)
        )
        freshness = calculate_freshness_score(
            fighter1, fighter2, self._weights.get("freshness", 10)
        )
        title = calculate_title_score(
            fighter1, fighter2, self._weights.get("title_implications", 20)
        )
        entertainment = calculate_entertainment_score(
            fighter1, fighter2, self._weights.get("entertainment", 10)
        )
        
        total = ranking + skill + streak + rivalry + freshness + title + entertainment
        
        # Determine matchup type
        matchup_type = self._determine_matchup_type(fighter1, fighter2)
        
        # Determine reasons
        reasons = self._determine_reasons(
            fighter1, fighter2, ranking, rivalry, streak
        )
        
        # Check if rematch
        is_rematch = (
            fighter2.fighter_id in fighter1.recent_opponents or
            fighter1.fighter_id in fighter2.recent_opponents
        )
        
        return MatchupScore(
            fighter1_id=fighter1.fighter_id,
            fighter2_id=fighter2.fighter_id,
            fighter1_name=fighter1.name,
            fighter2_name=fighter2.name,
            weight_class=fighter1.weight_class,
            total_score=total,
            ranking_score=ranking,
            skill_score=skill,
            streak_score=streak,
            rivalry_score=rivalry,
            freshness_score=freshness,
            title_score=title,
            entertainment_score=entertainment,
            matchup_type=matchup_type,
            reasons=reasons,
            is_title_fight=(fighter1.is_champion or fighter2.is_champion),
            is_rematch=is_rematch
        )
    
    def _determine_matchup_type(
        self,
        fighter1: FighterMatchInfo,
        fighter2: FighterMatchInfo
    ) -> MatchupType:
        """Determine the type of matchup"""
        if fighter1.is_champion or fighter2.is_champion:
            return MatchupType.TITLE_FIGHT
        
        if fighter1.is_contender and fighter2.is_contender:
            return MatchupType.TITLE_ELIMINATOR
        
        if fighter1.is_contender or fighter2.is_contender:
            return MatchupType.MAIN_EVENT
        
        if fighter1.is_ranked and fighter2.is_ranked:
            return MatchupType.CO_MAIN
        
        if fighter1.is_ranked or fighter2.is_ranked:
            return MatchupType.MAIN_CARD
        
        # Both unranked
        total_fights = fighter1.wins + fighter1.losses + fighter2.wins + fighter2.losses
        if total_fights < 4:
            return MatchupType.DEBUT
        
        return MatchupType.PRELIM
    
    def _determine_reasons(
        self,
        fighter1: FighterMatchInfo,
        fighter2: FighterMatchInfo,
        ranking_score: float,
        rivalry_score: float,
        streak_score: float
    ) -> List[MatchupReason]:
        """Determine why this matchup makes sense"""
        reasons = []
        
        if fighter1.is_champion or fighter2.is_champion:
            reasons.append(MatchupReason.TITLE_SHOT)
        
        if rivalry_score > 0:
            reasons.append(MatchupReason.RIVALRY)
        
        if ranking_score >= 20:
            reasons.append(MatchupReason.RANKINGS_PROXIMITY)
        
        if streak_score >= 10:
            reasons.append(MatchupReason.WIN_STREAK_CLASH)
        
        # Gatekeeper test: ranked vs unranked
        if (fighter1.is_ranked and not fighter2.is_ranked) or \
           (fighter2.is_ranked and not fighter1.is_ranked):
            reasons.append(MatchupReason.GATEKEEPER_TEST)
        
        if not reasons:
            reasons.append(MatchupReason.RANDOM)
        
        return reasons
    
    def find_opponents(
        self,
        fighter_id: str,
        limit: int = 5,
        same_weight_class: bool = True
    ) -> List[MatchupScore]:
        """
        Find best opponents for a fighter.
        
        Args:
            fighter_id: Fighter looking for opponent
            limit: Maximum number of suggestions
            same_weight_class: Only same weight class
        
        Returns:
            List of MatchupScores, sorted by total_score descending
        """
        fighter = self._fighters.get(fighter_id)
        if not fighter:
            return []
        
        eligible = self.get_eligible_opponents(fighter_id, same_weight_class)
        
        # Score all matchups
        scores = [self.score_matchup(fighter, opp) for opp in eligible]
        
        # Sort by total score descending
        scores.sort(key=lambda s: s.total_score, reverse=True)
        
        return scores[:limit]
    
    def find_ranked_matchup(
        self,
        weight_class: WeightClass,
        used_fighters: Set[str]
    ) -> Optional[MatchupScore]:
        """
        Find best ranked vs ranked matchup in a division.
        
        Prioritizes rank proximity for realistic matchmaking.
        
        Args:
            weight_class: Division to match
            used_fighters: Fighter IDs already on the card
            
        Returns:
            Best ranked matchup, or None if not enough ranked fighters
        """
        ranked = [f for f in self.get_ranked_fighters(weight_class)
                  if f.fighter_id not in used_fighters]
        
        if len(ranked) < 2:
            return None
        
        # Find best matchup by rank proximity
        best_matchup = None
        best_score = -1
        
        for i, f1 in enumerate(ranked):
            for f2 in ranked[i+1:]:
                # Same camp check
                if f1.camp_id and f2.camp_id and f1.camp_id == f2.camp_id:
                    continue
                
                matchup = self.score_matchup(f1, f2)
                if matchup.total_score > best_score:
                    best_score = matchup.total_score
                    best_matchup = matchup
        
        return best_matchup
    
    def find_unranked_matchup(
        self,
        weight_class: WeightClass,
        used_fighters: Set[str]
    ) -> Optional[MatchupScore]:
        """
        Find best unranked vs unranked matchup in a division.
        
        Prioritizes rating proximity.
        """
        unranked = [f for f in self.get_unranked_fighters(weight_class)
                    if f.fighter_id not in used_fighters]
        
        if len(unranked) < 2:
            return None
        
        best_matchup = None
        best_score = -1
        
        for i, f1 in enumerate(unranked):
            for f2 in unranked[i+1:]:
                # Same camp check
                if f1.camp_id and f2.camp_id and f1.camp_id == f2.camp_id:
                    continue
                
                # Rating proximity check (uses derived match_strength,
                # not OVR — per principle_OVR_player_facing_only)
                if abs(f1.match_strength - f2.match_strength) > 20:
                    continue
                
                matchup = self.score_matchup(f1, f2)
                if matchup.total_score > best_score:
                    best_score = matchup.total_score
                    best_matchup = matchup
        
        return best_matchup
    
    def find_gatekeeper_matchup(
        self,
        weight_class: WeightClass,
        used_fighters: Set[str]
    ) -> Optional[MatchupScore]:
        """
        Find ranked vs unranked "gatekeeper" matchup.
        
        These are less common but serve to test prospects.
        """
        ranked = [f for f in self.get_ranked_fighters(weight_class)
                  if f.fighter_id not in used_fighters]
        unranked = [f for f in self.get_unranked_fighters(weight_class)
                    if f.fighter_id not in used_fighters]
        
        if not ranked or not unranked:
            return None
        
        # Prefer lower-ranked fighters for gatekeeper duty
        ranked.sort(key=lambda f: -(f.rank or 0))  # Higher rank numbers first
        
        best_matchup = None
        best_score = -1
        
        for r_fighter in ranked[:5]:  # Only consider ranks 11-15 as gatekeepers
            for u_fighter in unranked:
                # Same camp check
                if r_fighter.camp_id and u_fighter.camp_id:
                    if r_fighter.camp_id == u_fighter.camp_id:
                        continue
                
                # Rating proximity (uses derived match_strength,
                # not OVR — per principle_OVR_player_facing_only)
                if abs(r_fighter.match_strength - u_fighter.match_strength) > 15:
                    continue
                
                matchup = self.score_matchup(r_fighter, u_fighter)
                if matchup.total_score > best_score:
                    best_score = matchup.total_score
                    best_matchup = matchup
        
        return best_matchup
    
    def find_title_challenger(
        self,
        champion_id: str
    ) -> Optional[MatchupScore]:
        """
        Find the best title challenger for a champion.
        
        Prioritizes:
        1. Mandatory challenger (#1 ranked)
        2. Rival with high ranking
        3. Highest ranked available
        """
        champion = self._fighters.get(champion_id)
        if not champion or not champion.is_champion:
            return None
        
        eligible = self.get_eligible_opponents(champion_id)
        
        if not eligible:
            return None
        
        # Find #1 contender
        contenders = [f for f in eligible if f.rank == 1]
        if contenders:
            return self.score_matchup(champion, contenders[0])
        
        # Find highest ranked rival
        rivals = [f for f in eligible if f.fighter_id in champion.rivalry_ids]
        if rivals:
            rivals.sort(key=lambda f: f.rank if f.rank else 99)
            return self.score_matchup(champion, rivals[0])
        
        # Highest ranked overall
        ranked = [f for f in eligible if f.is_ranked]
        if ranked:
            ranked.sort(key=lambda f: f.rank if f.rank else 99)
            return self.score_matchup(champion, ranked[0])
        
        # Any opponent
        return self.score_matchup(champion, eligible[0])
    
    def generate_smart_card(
        self,
        weight_class: WeightClass,
        num_fights: int = 10,
        include_title: bool = True
    ) -> List[MatchupScore]:
        """
        Generate a fight card with smart matchmaking.
        
        Prioritizes:
        1. Title fight if champion available
        2. Ranked vs Ranked (70% probability)
        3. Unranked vs Unranked (remaining)
        4. Gatekeeper fights (40% probability when mixing)
        
        Args:
            weight_class: Weight class for the card
            num_fights: Target number of fights
            include_title: Include title fight if available
        
        Returns:
            List of MatchupScores for the card
        """
        card: List[MatchupScore] = []
        used_fighters: Set[str] = set()
        
        # 1. Try to add title fight first
        if include_title:
            champions = [f for f in self._fighters.values()
                        if f.weight_class == weight_class and f.is_champion
                        and self.is_available(f.fighter_id)]
            if champions:
                champ = champions[0]
                title_match = self.find_title_challenger(champ.fighter_id)
                if title_match:
                    card.append(title_match)
                    used_fighters.add(title_match.fighter1_id)
                    used_fighters.add(title_match.fighter2_id)
        
        # 2. Fill remaining slots with smart matchmaking
        while len(card) < num_fights:
            matchup = None
            
            # Determine matchup type by probability
            roll = random.random()
            
            if roll < RANKED_VS_RANKED_PROBABILITY:
                # Try ranked vs ranked
                matchup = self.find_ranked_matchup(weight_class, used_fighters)
            
            if not matchup and roll < RANKED_VS_RANKED_PROBABILITY + RANKED_VS_UNRANKED_PROBABILITY:
                # Try gatekeeper fight
                matchup = self.find_gatekeeper_matchup(weight_class, used_fighters)
            
            if not matchup:
                # Fall back to unranked vs unranked
                matchup = self.find_unranked_matchup(weight_class, used_fighters)
            
            if not matchup:
                # Last resort: any available matchup
                available = [f for f in self._fighters.values()
                            if f.weight_class == weight_class
                            and f.fighter_id not in used_fighters
                            and self.is_available(f.fighter_id)]
                
                if len(available) >= 2:
                    # Find any valid matchup
                    for i, f1 in enumerate(available):
                        for f2 in available[i+1:]:
                            if f1.camp_id and f2.camp_id and f1.camp_id == f2.camp_id:
                                continue
                            matchup = self.score_matchup(f1, f2)
                            break
                        if matchup:
                            break
            
            if matchup:
                card.append(matchup)
                used_fighters.add(matchup.fighter1_id)
                used_fighters.add(matchup.fighter2_id)
            else:
                break  # No more matchups possible
        
        # Sort card by matchup type importance
        type_order = {
            MatchupType.TITLE_FIGHT: 0,
            MatchupType.TITLE_ELIMINATOR: 1,
            MatchupType.MAIN_EVENT: 2,
            MatchupType.CO_MAIN: 3,
            MatchupType.MAIN_CARD: 4,
            MatchupType.PRELIM: 5,
            MatchupType.DEBUT: 6,
        }
        card.sort(key=lambda m: type_order.get(m.matchup_type, 99))
        
        return card
    
    def generate_card(
        self,
        weight_class: WeightClass,
        num_fights: int = 5,
        include_title: bool = True
    ) -> List[MatchupScore]:
        """
        Generate a fight card for a weight class (legacy method).
        
        For full smart matchmaking, use generate_smart_card().
        """
        return self.generate_smart_card(weight_class, num_fights, include_title)
    
    def generate_multi_division_card(
        self,
        num_fights: int = 12
    ) -> List[MatchupScore]:
        """
        Generate a card across all weight classes.
        
        Distributes fights across divisions evenly.
        """
        card: List[MatchupScore] = []
        used_fighters: Set[str] = set()
        
        # Get all weight classes with available fighters
        weight_classes = set(f.weight_class for f in self._fighters.values()
                            if self.is_available(f.fighter_id))
        
        if not weight_classes:
            return card
        
        # Cycle through weight classes
        wc_list = list(weight_classes)
        wc_index = 0
        
        while len(card) < num_fights:
            wc = wc_list[wc_index % len(wc_list)]
            wc_index += 1
            
            # Try to find a matchup in this weight class
            matchup = None
            
            # First try ranked vs ranked
            if random.random() < RANKED_VS_RANKED_PROBABILITY:
                matchup = self.find_ranked_matchup(wc, used_fighters)
            
            # Then try unranked
            if not matchup:
                matchup = self.find_unranked_matchup(wc, used_fighters)
            
            # Any matchup
            if not matchup:
                available = [f for f in self._fighters.values()
                            if f.weight_class == wc
                            and f.fighter_id not in used_fighters
                            and self.is_available(f.fighter_id)]
                if len(available) >= 2:
                    matchup = self.score_matchup(available[0], available[1])
            
            if matchup:
                card.append(matchup)
                used_fighters.add(matchup.fighter1_id)
                used_fighters.add(matchup.fighter2_id)
            
            # Safety: don't infinite loop
            if wc_index > num_fights * 3:
                break
        
        # Sort by matchup type
        type_order = {
            MatchupType.TITLE_FIGHT: 0,
            MatchupType.TITLE_ELIMINATOR: 1,
            MatchupType.MAIN_EVENT: 2,
            MatchupType.CO_MAIN: 3,
            MatchupType.MAIN_CARD: 4,
            MatchupType.PRELIM: 5,
            MatchupType.DEBUT: 6,
        }
        card.sort(key=lambda m: type_order.get(m.matchup_type, 99))
        
        return card
    
    def get_division_state(
        self,
        weight_class: WeightClass
    ) -> Dict[str, Any]:
        """
        Get overview of a division's matchmaking state.
        """
        fighters = [
            f for f in self._fighters.values()
            if f.weight_class == weight_class
        ]
        
        champion = next((f for f in fighters if f.is_champion), None)
        ranked = [f for f in fighters if f.is_ranked and not f.is_champion]
        ranked.sort(key=lambda f: f.rank or 99)
        unranked = [f for f in fighters if not f.is_ranked]
        
        available_count = sum(1 for f in fighters if self.is_available(f.fighter_id))
        on_cooldown = sum(1 for f in fighters if f.is_on_cooldown(self._current_week))
        
        return {
            "weight_class": weight_class.value,
            "total_fighters": len(fighters),
            "champion": champion.fighter_id if champion else None,
            "champion_name": champion.name if champion else None,
            "ranked_count": len(ranked),
            "unranked_count": len(unranked),
            "available_count": available_count,
            "on_cooldown_count": on_cooldown,
            "top_5": [f.fighter_id for f in ranked[:5]]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize engine state"""
        return {
            "weights": self._weights,
            "booked_fighters": list(self._booked_fighters),
            "current_week": self._current_week,
            "recent_matchups": [
                {"f1": f1, "f2": f2, "date": {"y": d.year, "m": d.month, "d": d.day}}
                for f1, f2, d in self._recent_matchups
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchmakingEngine':
        """Deserialize engine state (fighters must be re-added)"""
        engine = cls(weights=data.get("weights"))
        engine._booked_fighters = set(data.get("booked_fighters", []))
        engine._current_week = data.get("current_week", 1)
        
        for m in data.get("recent_matchups", []):
            d = m.get("date", {})
            if d:
                try:
                    engine._recent_matchups.append((
                        m["f1"], m["f2"], GameDate(d["y"], d["m"], d["d"])
                    ))
                except:
                    pass
        
        return engine


# ============================================================================
# GLOBAL ENGINE INSTANCE
# ============================================================================

matchmaking_engine = MatchmakingEngine()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def find_best_opponent(fighter_id: str) -> Optional[MatchupScore]:
    """Find the single best opponent for a fighter"""
    matches = matchmaking_engine.find_opponents(fighter_id, limit=1)
    return matches[0] if matches else None


def is_good_matchup(fighter1_id: str, fighter2_id: str, threshold: float = 60.0) -> bool:
    """Check if two fighters make a good matchup"""
    f1 = matchmaking_engine.get_fighter(fighter1_id)
    f2 = matchmaking_engine.get_fighter(fighter2_id)
    if not f1 or not f2:
        return False
    
    score = matchmaking_engine.score_matchup(f1, f2)
    return score.total_score >= threshold


def get_matchup_quality(fighter1_id: str, fighter2_id: str) -> str:
    """Get human-readable matchup quality"""
    f1 = matchmaking_engine.get_fighter(fighter1_id)
    f2 = matchmaking_engine.get_fighter(fighter2_id)
    if not f1 or not f2:
        return "Unknown"
    
    score = matchmaking_engine.score_matchup(f1, f2)
    
    if score.total_score >= 90:
        return "Excellent"
    elif score.total_score >= 70:
        return "Good"
    elif score.total_score >= 50:
        return "Fair"
    elif score.total_score >= 30:
        return "Poor"
    else:
        return "Mismatch"


def get_fighter_cooldown(
    is_champion: bool,
    lose_streak: int,
    won_last: bool = True
) -> int:
    """Get cooldown weeks for a fighter"""
    return calculate_cooldown(is_champion, lose_streak, won_last)


def create_fighter_match_info(
    fighter: Any,
    rank: Optional[int] = None,
    recent_opponents: Optional[List[str]] = None,
    rivalry_ids: Optional[List[str]] = None,
    last_fight_week: int = 0,
    current_week: int = 0,
) -> FighterMatchInfo:
    """
    Factory function to create FighterMatchInfo from a game fighter object.
    
    This bridges the gap between game state fighters and matchmaking system.
    
    Args:
        fighter: A fighter object with standard attributes
        rank: Optional explicit rank (None=unranked, 0=champion, 1-15=ranked)
        recent_opponents: List of recent opponent IDs
        rivalry_ids: List of rivalry fighter IDs
        last_fight_week: Week of last fight for cooldown
        current_week: Current game week
        
    Returns:
        FighterMatchInfo ready for matchmaking
    """
    # Extract weight class
    wc = getattr(fighter, 'weight_class', 'Lightweight')
    if isinstance(wc, str):
        try:
            wc = WeightClass(wc)
        except ValueError:
            wc = WeightClass.LIGHTWEIGHT
    
    # Determine rank if not provided
    if rank is None:
        if getattr(fighter, 'is_champion', False):
            rank = 0
        # Otherwise stays None (unranked)
    
    # Get status
    is_active = getattr(fighter, 'is_active', True)
    status = FighterStatus.ACTIVE if is_active else FighterStatus.INJURED
    
    return FighterMatchInfo(
        fighter_id=getattr(fighter, 'fighter_id', str(id(fighter))),
        name=getattr(fighter, 'name', 'Unknown'),
        weight_class=wc,
        rank=rank,
        overall_rating=getattr(fighter, 'overall_rating', 50),
        win_streak=getattr(fighter, 'win_streak', 0),
        lose_streak=getattr(fighter, 'lose_streak', 0),
        wins=getattr(fighter, 'wins', 0),
        losses=getattr(fighter, 'losses', 0),
        is_champion=getattr(fighter, 'is_champion', False),
        status=status,
        recent_opponents=recent_opponents or [],
        rivalry_ids=rivalry_ids or [],
        camp_id=getattr(fighter, 'camp_id', None),
        last_fight_week=last_fight_week,
        match_strength=_match_strength(fighter),
    )


def find_best_matchup_for_fighter(
    fighter: Any,
    potential_opponents: List[Any],
    fighter_rank: Optional[int] = None,
    get_opponent_rank: Optional[callable] = None,
    get_recent_opponents: Optional[callable] = None,
    get_rivalry_ids: Optional[callable] = None,
    current_week: int = 0,
) -> Optional[Tuple[Any, MatchupScore]]:
    """
    Find the best opponent for a fighter from a list of potential opponents.
    
    This is a convenience function that handles conversion to FighterMatchInfo
    internally, making it easy for CLI to use smart matchmaking.
    
    Args:
        fighter: The fighter looking for opponent
        potential_opponents: List of potential opponent fighter objects
        fighter_rank: Rank of the fighter (None=unranked, 0=champ)
        get_opponent_rank: Function(fighter) -> rank, or None
        get_recent_opponents: Function(fighter_id) -> List[opponent_ids]
        get_rivalry_ids: Function(fighter_id) -> List[rivalry_ids]
        current_week: Current game week for cooldown
        
    Returns:
        Tuple of (best_opponent, MatchupScore) or None if no valid matchup
    """
    if not potential_opponents:
        return None
    
    # Convert fighter to match info
    f1_rivals = []
    if get_rivalry_ids:
        f1_rivals = get_rivalry_ids(fighter.fighter_id) or []
    
    f1_recent = []
    if get_recent_opponents:
        f1_recent = get_recent_opponents(fighter.fighter_id) or []
    
    f1 = create_fighter_match_info(
        fighter,
        rank=fighter_rank,
        recent_opponents=f1_recent,
        rivalry_ids=f1_rivals,
        current_week=current_week,
    )
    
    # Create a temporary matchmaking engine
    engine = MatchmakingEngine()
    engine.set_current_week(current_week)
    engine.register_fighter(f1)
    
    best_opponent = None
    best_score = None
    best_total = -1
    
    for opp in potential_opponents:
        # Skip same-camp fights
        if hasattr(fighter, 'camp_id') and hasattr(opp, 'camp_id'):
            if fighter.camp_id and opp.camp_id and fighter.camp_id == opp.camp_id:
                continue
        
        # Get opponent rank
        opp_rank = None
        if get_opponent_rank:
            opp_rank = get_opponent_rank(opp)
        elif getattr(opp, 'is_champion', False):
            opp_rank = 0
        
        # Get opponent rivalries and recent
        opp_rivals = []
        if get_rivalry_ids:
            opp_rivals = get_rivalry_ids(opp.fighter_id) or []
        
        opp_recent = []
        if get_recent_opponents:
            opp_recent = get_recent_opponents(opp.fighter_id) or []
        
        f2 = create_fighter_match_info(
            opp,
            rank=opp_rank,
            recent_opponents=opp_recent,
            rivalry_ids=opp_rivals,
            current_week=current_week,
        )
        
        engine.register_fighter(f2)
        
        # Score this matchup
        score = engine.score_matchup(f1, f2)
        
        if score.total_score > best_total:
            best_total = score.total_score
            best_opponent = opp
            best_score = score
    
    if best_opponent and best_score:
        return (best_opponent, best_score)
    return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "MatchupType", "MatchupReason",
    
    # Data classes
    "MatchupScore", "FighterMatchInfo",
    
    # Engine
    "MatchmakingEngine", "matchmaking_engine",
    
    # Functions
    "find_best_opponent", "is_good_matchup", "get_matchup_quality",
    "calculate_cooldown", "weeks_until_available", "get_fighter_cooldown",
    "create_fighter_match_info", "find_best_matchup_for_fighter",
    
    # Score functions
    "calculate_ranking_score", "calculate_skill_score", "calculate_streak_score",
    "calculate_rivalry_score", "calculate_freshness_score", "calculate_title_score",
    "calculate_entertainment_score",
    
    # Title eligibility functions
    "is_title_eligible", "can_be_title_fight", "get_title_eligibility_reason",
    
    # Constants
    "COOLDOWN_WINNER", "COOLDOWN_LOSER_BASE", "COOLDOWN_LOSER_MAX",
    "COOLDOWN_CHAMPION", "RANKED_VS_RANKED_PROBABILITY",
    "TITLE_MIN_RANK", "TITLE_MIN_FIGHTS_RECORD", "TITLE_MIN_WIN_PCT", "TITLE_MIN_WINS",
]
