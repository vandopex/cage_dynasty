# systems/rankings.py
# Module: Enhanced Rankings System
# Lines: ~1,450
#
# Manages fighter rankings with smart movement algorithms.
# Includes P4P rankings, win streak bonuses, and finish rewards.

"""
Cage Dynasty - Enhanced Rankings System

Smart ranking system that reflects real MMA dynamics:
- Finish bonus: KO/TKO/Sub wins = +1 extra spot
- Win streak bonus: 3+ streak = +1, 5+ streak = +2
- Upset magnitude: Bigger upsets = bigger jumps
- P4P algorithm: Cross-division pound-for-pound rankings
- Bubble volatility: Ranks 11-15 more volatile
- Former champ protection: Legends don't crater immediately

RANKING MOVEMENT FORMULA:
========================
Base movement from fight result
+ Finish bonus (0-1)
+ Win streak bonus (0-2)
+ Upset scaling (0-2)
- Bubble penalty if applicable
= Final movement (capped)

P4P SCORING:
===========
Champion bonus: +100
Divisional rank: (16 - rank) * 5
Win streak: streak * 8 (max 40)
Quality wins: ranked_wins * 10
Title defenses: defenses * 15
Recent activity: +10 if fought in 12 weeks
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import date
import random

# Try multiple import paths for flexibility
try:
    from core.types import WeightClass, FightOutcome, EventType
    from core.events import emit
    from core.config import get_config
    from core.calendar import calendar, GameDate
except ImportError:
    try:
        from types import WeightClass, FightOutcome, EventType
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
        
        class FightOutcome(Enum):
            KO = "KO"
            TKO = "TKO"
            SUBMISSION = "Submission"
            DECISION_UNANIMOUS = "Unanimous Decision"
            DECISION_SPLIT = "Split Decision"
            DECISION_MAJORITY = "Majority Decision"
            DRAW = "Draw"
            NO_CONTEST = "No Contest"
            DQ = "Disqualification"
        
        class EventType(Enum):
            FIGHTER_RANKED = "fighter_ranked"
            P4P_UPDATED = "p4p_updated"
        
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
# CONSTANTS
# ============================================================================

MAX_RANKED_FIGHTERS = 15  # Standard top 15 rankings
CHAMPION_RANK = 0  # Champion is rank 0
UNRANKED = None  # Represents unranked status

# Movement limits
MAX_RANK_JUMP = 7  # Increased from 5 to allow big upsets
MAX_RANK_DROP = 4  # Increased slightly

# Win streak thresholds
WIN_STREAK_BONUS_3 = 3   # +1 bonus at 3+ streak
WIN_STREAK_BONUS_5 = 5   # +2 bonus at 5+ streak

# Inactivity
INACTIVITY_WEEKS = 26  # 6 months

# P4P
P4P_TOP_COUNT = 10  # Top 10 P4P


# ============================================================================
# ENUMS
# ============================================================================

class RankingChangeReason(Enum):
    """Why a ranking changed"""
    FIGHT_WIN = "Won fight"
    FIGHT_WIN_FINISH = "Won by finish"
    FIGHT_WIN_UPSET = "Upset victory"
    FIGHT_LOSS = "Lost fight"
    TITLE_WIN = "Won championship"
    TITLE_LOSS = "Lost championship"
    TITLE_DEFENSE = "Defended championship"
    INACTIVITY = "Inactivity"
    SIGNED = "Signed to promotion"
    RELEASED = "Released from promotion"
    RETIRED = "Retired"
    INJURY = "Long-term injury"
    OTHER_MOVEMENT = "Other fighters moved"
    INITIAL_RANKING = "Initial ranking"
    MANUAL_ADJUSTMENT = "Manual adjustment"
    ENTERED_RANKINGS = "Entered rankings"
    DROPPED_OUT = "Dropped from rankings"


class FinishType(Enum):
    """Type of fight finish for bonus calculation"""
    KO = "KO"
    TKO = "TKO"
    SUBMISSION = "Submission"
    DECISION = "Decision"
    OTHER = "Other"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RankingEntry:
    """A single ranking entry for a fighter."""
    fighter_id: str
    rank: int  # 0 = champion, 1-15 = ranked
    weight_class: WeightClass
    ranking_points: float = 1000.0
    weeks_at_rank: int = 0
    last_fight_week: int = 0
    last_fight_year: int = 0
    wins_while_ranked: int = 0
    losses_while_ranked: int = 0
    current_win_streak: int = 0
    is_former_champion: bool = False
    former_champ_protection_fights: int = 0  # Fights remaining with protection
    title_defenses: int = 0
    ranked_wins: int = 0  # Wins over ranked opponents
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "rank": self.rank,
            "weight_class": self.weight_class.value,
            "ranking_points": self.ranking_points,
            "weeks_at_rank": self.weeks_at_rank,
            "last_fight_week": self.last_fight_week,
            "last_fight_year": self.last_fight_year,
            "wins_while_ranked": self.wins_while_ranked,
            "losses_while_ranked": self.losses_while_ranked,
            "current_win_streak": self.current_win_streak,
            "is_former_champion": self.is_former_champion,
            "former_champ_protection_fights": self.former_champ_protection_fights,
            "title_defenses": self.title_defenses,
            "ranked_wins": self.ranked_wins,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RankingEntry':
        return cls(
            fighter_id=data["fighter_id"],
            rank=data["rank"],
            weight_class=WeightClass(data["weight_class"]),
            ranking_points=data.get("ranking_points", 1000.0),
            weeks_at_rank=data.get("weeks_at_rank", 0),
            last_fight_week=data.get("last_fight_week", 0),
            last_fight_year=data.get("last_fight_year", 0),
            wins_while_ranked=data.get("wins_while_ranked", 0),
            losses_while_ranked=data.get("losses_while_ranked", 0),
            current_win_streak=data.get("current_win_streak", 0),
            is_former_champion=data.get("is_former_champion", False),
            former_champ_protection_fights=data.get("former_champ_protection_fights", 0),
            title_defenses=data.get("title_defenses", 0),
            ranked_wins=data.get("ranked_wins", 0),
        )


@dataclass
class RankingChange:
    """Record of a ranking change for history tracking."""
    fighter_id: str
    fighter_name: str
    weight_class: WeightClass
    old_rank: Optional[int]
    new_rank: Optional[int]
    reason: RankingChangeReason
    week: int
    year: int
    details: str = ""
    
    @property
    def is_promotion(self) -> bool:
        """Did rank improve (lower number)?"""
        if self.old_rank is None:
            return self.new_rank is not None
        if self.new_rank is None:
            return False
        return self.new_rank < self.old_rank
    
    @property
    def is_demotion(self) -> bool:
        """Did rank get worse (higher number)?"""
        if self.new_rank is None:
            return self.old_rank is not None
        if self.old_rank is None:
            return False
        return self.new_rank > self.old_rank
    
    @property
    def positions_moved(self) -> int:
        """How many positions changed (positive = up, negative = down)"""
        if self.old_rank is None or self.new_rank is None:
            return 0
        return self.old_rank - self.new_rank
    
    @property
    def is_big_mover(self) -> bool:
        """Is this a significant ranking change?"""
        moved = abs(self.positions_moved)
        # Big move = 3+ spots, or entering/leaving top 5
        if moved >= 3:
            return True
        if self.new_rank is not None and self.new_rank <= 5:
            if self.old_rank is None or self.old_rank > 5:
                return True
        return False
    
    def __str__(self) -> str:
        old = f"#{self.old_rank}" if self.old_rank is not None else "Unranked"
        new = f"#{self.new_rank}" if self.new_rank is not None else "Unranked"
        if self.new_rank == CHAMPION_RANK:
            new = "Champion"
        if self.old_rank == CHAMPION_RANK:
            old = "Champion"
        return f"{old} Ã¢â€ â€™ {new} ({self.reason.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "weight_class": self.weight_class.value,
            "old_rank": self.old_rank,
            "new_rank": self.new_rank,
            "reason": self.reason.value,
            "week": self.week,
            "year": self.year,
            "details": self.details,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RankingChange':
        return cls(
            fighter_id=data["fighter_id"],
            fighter_name=data.get("fighter_name", "Unknown"),
            weight_class=WeightClass(data["weight_class"]),
            old_rank=data["old_rank"],
            new_rank=data["new_rank"],
            reason=RankingChangeReason(data["reason"]),
            week=data.get("week", 1),
            year=data.get("year", 1),
            details=data.get("details", ""),
        )


@dataclass
class P4PEntry:
    """Pound-for-pound ranking entry."""
    fighter_id: str
    fighter_name: str
    weight_class: WeightClass
    rank: int
    score: float
    is_champion: bool
    divisional_rank: Optional[int]
    win_streak: int
    title_defenses: int
    ranked_wins: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "weight_class": self.weight_class.value,
            "rank": self.rank,
            "score": self.score,
            "is_champion": self.is_champion,
            "divisional_rank": self.divisional_rank,
            "win_streak": self.win_streak,
            "title_defenses": self.title_defenses,
            "ranked_wins": self.ranked_wins,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'P4PEntry':
        return cls(
            fighter_id=data["fighter_id"],
            fighter_name=data.get("fighter_name", "Unknown"),
            weight_class=WeightClass(data["weight_class"]),
            rank=data["rank"],
            score=data.get("score", 0),
            is_champion=data.get("is_champion", False),
            divisional_rank=data.get("divisional_rank"),
            win_streak=data.get("win_streak", 0),
            title_defenses=data.get("title_defenses", 0),
            ranked_wins=data.get("ranked_wins", 0),
        )


# ============================================================================
# MOVEMENT CALCULATIONS
# ============================================================================

def calculate_finish_bonus(outcome: FightOutcome) -> int:
    """
    Calculate bonus spots for finishing a fight.
    
    KO/TKO/Submission = +1 spot
    Decision = +0
    """
    # Handle string outcomes
    if isinstance(outcome, str):
        outcome_upper = outcome.upper()
        if outcome_upper in ["KO", "TKO", "SUBMISSION"]:
            return 1
        return 0
    
    # Handle enum outcomes
    finish_outcomes = {
        FightOutcome.KO, FightOutcome.TKO, FightOutcome.SUBMISSION,
    }
    
    if outcome in finish_outcomes:
        return 1
    return 0


def calculate_win_streak_bonus(win_streak: int) -> int:
    """
    Calculate bonus spots for win streak.
    
    3-4 wins = +1 spot
    5+ wins = +2 spots
    """
    if win_streak >= WIN_STREAK_BONUS_5:
        return 2
    elif win_streak >= WIN_STREAK_BONUS_3:
        return 1
    return 0


def calculate_upset_scaling(winner_rank: Optional[int], loser_rank: Optional[int]) -> int:
    """
    Calculate bonus spots based on upset magnitude.
    
    Bigger upsets (rank difference) = bigger jumps
    
    Rank difference 1-3: +0 (not really an upset)
    Rank difference 4-6: +1
    Rank difference 7-10: +2
    Rank difference 11+: +3 (massive upset)
    """
    if winner_rank is None or loser_rank is None:
        return 0
    
    # Only applies when winner was lower ranked (higher number)
    if winner_rank <= loser_rank:
        return 0
    
    diff = winner_rank - loser_rank
    
    if diff >= 11:
        return 3
    elif diff >= 7:
        return 2
    elif diff >= 4:
        return 1
    return 0


def calculate_bubble_modifier(current_rank: Optional[int], is_loss: bool) -> int:
    """
    Calculate additional movement for bubble fighters (11-15).
    
    Ranks 11-15 are more volatile:
    - Losses drop you 1 extra spot
    - Easier to fall out of rankings
    """
    if current_rank is None:
        return 0
    
    if 11 <= current_rank <= 15 and is_loss:
        return 1  # Extra drop
    
    return 0


def calculate_former_champ_protection(
    is_former_champ: bool,
    protection_fights_remaining: int,
    current_rank: Optional[int],
) -> int:
    """
    Calculate protection modifier for former champions.
    
    Former champs in top 5 with protection remaining:
    - Take 1 less spot drop on losses
    """
    if not is_former_champ:
        return 0
    
    if protection_fights_remaining <= 0:
        return 0
    
    if current_rank is not None and current_rank <= 5:
        return -1  # Reduces drop by 1
    
    return 0


def calculate_total_movement(
    base_movement: int,
    outcome: FightOutcome,
    winner_streak: int,
    winner_rank: Optional[int],
    loser_rank: Optional[int],
    is_loss: bool = False,
    is_former_champ: bool = False,
    protection_fights: int = 0,
) -> int:
    """
    Calculate total ranking movement with all modifiers.
    """
    if is_loss:
        # Loss calculation
        drop = abs(base_movement)
        
        # Bubble penalty
        drop += calculate_bubble_modifier(winner_rank, is_loss=True)
        
        # Former champ protection (reduces drop)
        drop += calculate_former_champ_protection(
            is_former_champ, protection_fights, winner_rank
        )
        
        # Cap the drop
        return -min(drop, MAX_RANK_DROP)
    
    else:
        # Win calculation
        jump = base_movement
        
        # Finish bonus
        jump += calculate_finish_bonus(outcome)
        
        # Win streak bonus
        jump += calculate_win_streak_bonus(winner_streak)
        
        # Upset scaling
        jump += calculate_upset_scaling(winner_rank, loser_rank)
        
        # Cap the jump
        return min(jump, MAX_RANK_JUMP)


# ============================================================================
# P4P CALCULATIONS
# ============================================================================

def calculate_p4p_score(
    is_champion: bool,
    divisional_rank: Optional[int],
    win_streak: int,
    ranked_wins: int,
    title_defenses: int,
    last_fight_week: int,
    last_fight_year: int,
    current_week: int,
    current_year: int,
) -> float:
    """
    Calculate pound-for-pound score.
    
    Components:
    - Champion bonus: +100
    - Divisional rank: (16 - rank) * 5 (max 75 for #1)
    - Win streak: streak * 8 (max 40 for 5+)
    - Quality wins: ranked_wins * 10
    - Title defenses: defenses * 15
    - Recent activity: +10 if fought in 12 weeks
    """
    score = 0.0
    
    # Champion bonus
    if is_champion:
        score += 100
    
    # Divisional rank (inverted - lower rank = higher score)
    if divisional_rank is not None and divisional_rank != CHAMPION_RANK:
        score += max(0, (16 - divisional_rank) * 5)
    elif is_champion:
        score += 75  # Champions get full rank points
    
    # Win streak (capped at 5 for scoring)
    streak_score = min(win_streak, 5) * 8
    score += streak_score
    
    # Quality wins (ranked opponents beaten)
    score += ranked_wins * 10
    
    # Title defenses
    score += title_defenses * 15
    
    # Recent activity bonus
    weeks_since_fight = (current_year - last_fight_year) * 52 + (current_week - last_fight_week)
    if weeks_since_fight <= 12:
        score += 10
    
    return score


# ============================================================================
# DIVISION RANKINGS
# ============================================================================

class DivisionRankings:
    """Manages rankings for a single weight class."""
    
    def __init__(self, weight_class: WeightClass):
        self.weight_class = weight_class
        self._champion_id: Optional[str] = None
        self._champion_entry: Optional[RankingEntry] = None
        self._rankings: List[RankingEntry] = []  # Ordered by rank (1-15)
        self._fighter_names: Dict[str, str] = {}  # fighter_id -> name
    
    @property
    def champion(self) -> Optional[str]:
        return self._champion_id
    
    @property
    def has_champion(self) -> bool:
        return self._champion_id is not None
    
    def set_fighter_name(self, fighter_id: str, name: str) -> None:
        """Store fighter name for display."""
        self._fighter_names[fighter_id] = name
    
    def get_fighter_name(self, fighter_id: str) -> str:
        """Get stored fighter name."""
        return self._fighter_names.get(fighter_id, "Unknown")
    
    def get_ranked_fighters(self) -> List[str]:
        """Get list of ranked fighter IDs in order."""
        return [entry.fighter_id for entry in self._rankings]
    
    def get_rank(self, fighter_id: str) -> Optional[int]:
        """Get a fighter's current rank (None if unranked)."""
        if fighter_id == self._champion_id:
            return CHAMPION_RANK
        
        for i, entry in enumerate(self._rankings):
            if entry.fighter_id == fighter_id:
                return i + 1
        return None
    
    def get_entry(self, fighter_id: str) -> Optional[RankingEntry]:
        """Get full ranking entry for a fighter."""
        if fighter_id == self._champion_id and self._champion_entry:
            return self._champion_entry
        
        for entry in self._rankings:
            if entry.fighter_id == fighter_id:
                return entry
        return None
    
    def get_fighter_at_rank(self, rank: int) -> Optional[str]:
        """Get fighter ID at a specific rank."""
        if rank == CHAMPION_RANK:
            return self._champion_id
        if 1 <= rank <= len(self._rankings):
            return self._rankings[rank - 1].fighter_id
        return None
    
    def set_champion(
        self,
        fighter_id: str,
        fighter_name: str = "",
        title_defenses: int = 0,
    ) -> Optional[str]:
        """Set the division champion."""
        previous = self._champion_id
        
        # Remove from rankings if ranked
        self._remove_from_rankings(fighter_id)
        
        # Get existing entry data if available
        old_entry = self.get_entry(fighter_id)
        win_streak = old_entry.current_win_streak if old_entry else 0
        ranked_wins = old_entry.ranked_wins if old_entry else 0
        
        self._champion_id = fighter_id
        self._champion_entry = RankingEntry(
            fighter_id=fighter_id,
            rank=CHAMPION_RANK,
            weight_class=self.weight_class,
            ranking_points=2000.0,
            current_win_streak=win_streak + 1,  # Title win adds to streak
            title_defenses=title_defenses,
            ranked_wins=ranked_wins,
        )
        
        if fighter_name:
            self._fighter_names[fighter_id] = fighter_name
        
        return previous
    
    def vacate_title(self) -> Optional[str]:
        """Vacate the championship."""
        previous = self._champion_id
        self._champion_id = None
        self._champion_entry = None
        return previous
    
    def add_ranked_fighter(
        self,
        fighter_id: str,
        fighter_name: str = "",
        initial_points: float = 1000.0,
        target_rank: Optional[int] = None,
        win_streak: int = 0,
    ) -> int:
        """Add a fighter to the rankings."""
        # Don't add if already ranked or is champion
        existing_rank = self.get_rank(fighter_id)
        if existing_rank is not None:
            return existing_rank
        
        entry = RankingEntry(
            fighter_id=fighter_id,
            rank=0,
            weight_class=self.weight_class,
            ranking_points=initial_points,
            current_win_streak=win_streak,
        )
        
        if target_rank and 1 <= target_rank <= MAX_RANKED_FIGHTERS:
            insert_pos = min(target_rank - 1, len(self._rankings))
            self._rankings.insert(insert_pos, entry)
        else:
            self._rankings.append(entry)
        
        # Trim to max size
        if len(self._rankings) > MAX_RANKED_FIGHTERS:
            removed = self._rankings.pop()
        
        self._update_rank_numbers()
        
        if fighter_name:
            self._fighter_names[fighter_id] = fighter_name
        
        return self.get_rank(fighter_id)
    
    def remove_fighter(self, fighter_id: str) -> Optional[int]:
        """Remove a fighter from rankings entirely."""
        old_rank = self.get_rank(fighter_id)
        
        if fighter_id == self._champion_id:
            self._champion_id = None
            self._champion_entry = None
        
        self._remove_from_rankings(fighter_id)
        
        return old_rank
    
    def _remove_from_rankings(self, fighter_id: str) -> None:
        """Remove fighter from ranked list (not champion)."""
        self._rankings = [e for e in self._rankings if e.fighter_id != fighter_id]
        self._update_rank_numbers()
    
    def _update_rank_numbers(self) -> None:
        """Update rank numbers after changes."""
        for i, entry in enumerate(self._rankings):
            entry.rank = i + 1
    
    def rerank_by_prestige(self, unranked_fighters: Optional[List[Tuple[str, str, float]]] = None) -> List['RankingChange']:
        """
        Re-sort the entire division based on prestige points.
        
        This is the core of the "Earn It" system. Rankings are determined
        purely by accumulated prestige points, not arbitrary slot assignments.
        
        Args:
            unranked_fighters: Optional list of (fighter_id, name, prestige_points)
                              for unranked fighters who might break into rankings
        
        Returns:
            List of ranking changes that occurred
        """
        changes = []
        
        # Combine ranked fighters with potential unranked entrants
        all_candidates = []
        
        # Add current ranked fighters
        for entry in self._rankings:
            all_candidates.append({
                "fighter_id": entry.fighter_id,
                "name": self._fighter_names.get(entry.fighter_id, "Unknown"),
                "points": entry.ranking_points,
                "entry": entry,
                "old_rank": entry.rank,
            })
        
        # Add unranked fighters who might qualify
        if unranked_fighters:
            for fighter_id, name, points in unranked_fighters:
                # Only consider if they have enough points to potentially rank
                min_ranked_points = min(e.ranking_points for e in self._rankings) if self._rankings else 0
                if points >= min_ranked_points * 0.8 or points >= 300:  # 80% of lowest or 300 min
                    all_candidates.append({
                        "fighter_id": fighter_id,
                        "name": name,
                        "points": points,
                        "entry": None,
                        "old_rank": None,
                    })
        
        # Sort by prestige points (highest first)
        all_candidates.sort(key=lambda x: x["points"], reverse=True)
        
        # Take top 15 for rankings
        new_rankings = []
        for i, candidate in enumerate(all_candidates[:MAX_RANKED_FIGHTERS]):
            new_rank = i + 1
            old_rank = candidate["old_rank"]
            
            if candidate["entry"]:
                # Existing ranked fighter
                entry = candidate["entry"]
                entry.rank = new_rank
                new_rankings.append(entry)
            else:
                # New entrant to rankings
                entry = RankingEntry(
                    fighter_id=candidate["fighter_id"],
                    rank=new_rank,
                    weight_class=self.weight_class,
                    ranking_points=candidate["points"],
                )
                new_rankings.append(entry)
                self._fighter_names[candidate["fighter_id"]] = candidate["name"]
            
            # Track changes
            if old_rank != new_rank:
                if old_rank is None:
                    reason = RankingChangeReason.ENTERED_RANKINGS
                elif new_rank < old_rank:
                    reason = RankingChangeReason.FIGHT_WIN
                else:
                    reason = RankingChangeReason.FIGHT_LOSS
                
                changes.append(RankingChange(
                    fighter_id=candidate["fighter_id"],
                    fighter_name=candidate["name"],
                    weight_class=self.weight_class,
                    old_rank=old_rank,
                    new_rank=new_rank,
                    reason=reason,
                    week=0,  # Will be filled in by caller
                    year=0,
                ))
        
        # Check for fighters who dropped out
        old_ids = {e.fighter_id for e in self._rankings}
        new_ids = {e.fighter_id for e in new_rankings}
        dropped = old_ids - new_ids
        
        for fighter_id in dropped:
            old_entry = next((e for e in self._rankings if e.fighter_id == fighter_id), None)
            if old_entry:
                changes.append(RankingChange(
                    fighter_id=fighter_id,
                    fighter_name=self._fighter_names.get(fighter_id, "Unknown"),
                    weight_class=self.weight_class,
                    old_rank=old_entry.rank,
                    new_rank=None,
                    reason=RankingChangeReason.DROPPED_OUT,
                    week=0,
                    year=0,
                ))
        
        self._rankings = new_rankings
        return changes
    
    def update_prestige_points(
        self,
        fighter_id: str,
        points_change: float,
    ) -> None:
        """
        Update a fighter's prestige points.
        
        Args:
            fighter_id: Fighter ID
            points_change: Points to add (positive) or subtract (negative)
        """
        entry = self.get_entry(fighter_id)
        if entry:
            entry.ranking_points = max(0, entry.ranking_points + points_change)
        
        # Also update champion if applicable
        if fighter_id == self._champion_id and self._champion_entry:
            self._champion_entry.ranking_points = max(0, self._champion_entry.ranking_points + points_change)
    
    def move_fighter(self, fighter_id: str, new_rank: int) -> Optional[int]:
        """Move a fighter to a specific rank."""
        old_rank = self.get_rank(fighter_id)
        
        if old_rank is None or old_rank == CHAMPION_RANK:
            return old_rank
        
        # Find and remove from current position
        entry = None
        for e in self._rankings:
            if e.fighter_id == fighter_id:
                entry = e
                break
        
        if not entry:
            return None
        
        self._rankings.remove(entry)
        
        # Insert at new position
        new_pos = max(0, min(new_rank - 1, len(self._rankings)))
        self._rankings.insert(new_pos, entry)
        
        self._update_rank_numbers()
        
        return old_rank
    
    def process_fight_result(
        self,
        winner_id: str,
        winner_name: str,
        loser_id: str,
        loser_name: str,
        outcome: FightOutcome,
        was_title_fight: bool,
        week: int,
        year: int,
    ) -> List[RankingChange]:
        """Process ranking changes from a fight result."""
        changes: List[RankingChange] = []
        
        winner_rank = self.get_rank(winner_id)
        loser_rank = self.get_rank(loser_id)
        winner_entry = self.get_entry(winner_id)
        loser_entry = self.get_entry(loser_id)
        
        # Store names
        self._fighter_names[winner_id] = winner_name
        self._fighter_names[loser_id] = loser_name
        
        # Get current win streak (will be incremented)
        winner_streak = (winner_entry.current_win_streak if winner_entry else 0) + 1
        
        # ===== TITLE FIGHT =====
        if was_title_fight and loser_id == self._champion_id:
            # Title changed hands!
            
            # Former champ becomes #1 with protection
            changes.append(RankingChange(
                fighter_id=loser_id,
                fighter_name=loser_name,
                weight_class=self.weight_class,
                old_rank=CHAMPION_RANK,
                new_rank=1,
                reason=RankingChangeReason.TITLE_LOSS,
                week=week,
                year=year,
            ))
            
            # New champion
            changes.append(RankingChange(
                fighter_id=winner_id,
                fighter_name=winner_name,
                weight_class=self.weight_class,
                old_rank=winner_rank,
                new_rank=CHAMPION_RANK,
                reason=RankingChangeReason.TITLE_WIN,
                week=week,
                year=year,
            ))
            
            # Execute changes
            old_champ = self._champion_id
            old_champ_entry = self._champion_entry
            
            # Remove winner from rankings
            self._remove_from_rankings(winner_id)
            
            # Set new champion
            self._champion_id = winner_id
            ranked_wins = (winner_entry.ranked_wins if winner_entry else 0) + 1
            self._champion_entry = RankingEntry(
                fighter_id=winner_id,
                rank=CHAMPION_RANK,
                weight_class=self.weight_class,
                ranking_points=2000.0,
                current_win_streak=winner_streak,
                last_fight_week=week,
                last_fight_year=year,
                ranked_wins=ranked_wins,
            )
            
            # Former champ becomes #1 with protection
            if old_champ:
                title_defenses = old_champ_entry.title_defenses if old_champ_entry else 0
                entry = RankingEntry(
                    fighter_id=old_champ,
                    rank=1,
                    weight_class=self.weight_class,
                    ranking_points=1800.0,
                    is_former_champion=True,
                    former_champ_protection_fights=3,  # 3 fights of protection
                    title_defenses=title_defenses,
                    current_win_streak=0,  # Streak reset
                    last_fight_week=week,
                    last_fight_year=year,
                )
                self._rankings.insert(0, entry)
                if len(self._rankings) > MAX_RANKED_FIGHTERS:
                    self._rankings.pop()
                self._update_rank_numbers()
            
            return changes
        
        # ===== TITLE DEFENSE =====
        if was_title_fight and winner_id == self._champion_id:
            # Successful title defense
            if self._champion_entry:
                self._champion_entry.title_defenses += 1
                self._champion_entry.current_win_streak = winner_streak
                self._champion_entry.last_fight_week = week
                self._champion_entry.last_fight_year = year
                if loser_rank is not None:
                    self._champion_entry.ranked_wins += 1
            
            changes.append(RankingChange(
                fighter_id=winner_id,
                fighter_name=winner_name,
                weight_class=self.weight_class,
                old_rank=CHAMPION_RANK,
                new_rank=CHAMPION_RANK,
                reason=RankingChangeReason.TITLE_DEFENSE,
                week=week,
                year=year,
                details=f"Defense #{self._champion_entry.title_defenses if self._champion_entry else 1}",
            ))
            
            # Loser drops
            if loser_entry and loser_rank is not None:
                self._process_loser_drop(
                    loser_entry, loser_rank, winner_rank, changes, week, year
                )
            
            return changes
        
        # ===== NON-TITLE FIGHTS =====
        
        # Winner movement
        if winner_rank is not None and winner_rank != CHAMPION_RANK:
            # Calculate base movement
            if loser_rank is not None and loser_rank < winner_rank:
                # Beat someone higher ranked
                base_jump = min(3, winner_rank - loser_rank)
            else:
                base_jump = 1
            
            # Apply all modifiers
            total_jump = calculate_total_movement(
                base_movement=base_jump,
                outcome=outcome,
                winner_streak=winner_streak,
                winner_rank=winner_rank,
                loser_rank=loser_rank,
            )
            
            new_rank = max(1, winner_rank - total_jump)
            
            if new_rank != winner_rank:
                reason = RankingChangeReason.FIGHT_WIN
                if calculate_finish_bonus(outcome) > 0:
                    reason = RankingChangeReason.FIGHT_WIN_FINISH
                if loser_rank is not None and loser_rank < winner_rank:
                    reason = RankingChangeReason.FIGHT_WIN_UPSET
                
                changes.append(RankingChange(
                    fighter_id=winner_id,
                    fighter_name=winner_name,
                    weight_class=self.weight_class,
                    old_rank=winner_rank,
                    new_rank=new_rank,
                    reason=reason,
                    week=week,
                    year=year,
                ))
                self.move_fighter(winner_id, new_rank)
            
            # Update winner entry
            if winner_entry:
                winner_entry.current_win_streak = winner_streak
                winner_entry.last_fight_week = week
                winner_entry.last_fight_year = year
                winner_entry.wins_while_ranked += 1
                if loser_rank is not None:
                    winner_entry.ranked_wins += 1
        
        elif winner_rank is None:
            # Unranked winner might enter rankings
            if loser_rank is not None and loser_rank <= 10:
                # Beat a top 10 - enter rankings!
                new_rank = min(MAX_RANKED_FIGHTERS, loser_rank + 2)
                actual_rank = self.add_ranked_fighter(
                    winner_id, winner_name, target_rank=new_rank, win_streak=winner_streak
                )
                
                changes.append(RankingChange(
                    fighter_id=winner_id,
                    fighter_name=winner_name,
                    weight_class=self.weight_class,
                    old_rank=None,
                    new_rank=actual_rank,
                    reason=RankingChangeReason.ENTERED_RANKINGS,
                    week=week,
                    year=year,
                    details="Entered rankings with win over ranked opponent",
                ))
        
        # Loser drops
        if loser_entry and loser_rank is not None and loser_rank != CHAMPION_RANK:
            self._process_loser_drop(
                loser_entry, loser_rank, winner_rank, changes, week, year
            )
        
        # ===== PRESTIGE POINTS UPDATE =====
        # This is the "Earn It" system - accumulate points based on fight results
        
        # Calculate points gained by winner
        outcome_str = "DEC"
        if outcome in [FightOutcome.KO]:
            outcome_str = "KO"
        elif outcome in [FightOutcome.TKO]:
            outcome_str = "TKO"
        elif outcome in [FightOutcome.SUBMISSION]:
            outcome_str = "SUB"
        
        loser_prestige = loser_entry.ranking_points if loser_entry else 100.0
        
        # Winner gains points
        points_gained = self._calculate_prestige_gain(
            winner_rank=winner_rank,
            loser_rank=loser_rank,
            loser_prestige=loser_prestige,
            outcome=outcome_str,
        )
        
        # Apply to winner
        if winner_entry:
            winner_entry.ranking_points += points_gained
        elif winner_rank is None:
            # Track unranked fighter points for potential future ranking entry
            # Store in a separate dict (would need to add self._unranked_prestige)
            pass
        
        # Loser loses points (less severe than gain)
        if loser_entry:
            points_lost = self._calculate_prestige_loss(
                loser_rank=loser_rank,
                loser_prestige=loser_prestige,
                winner_rank=winner_rank,
                outcome=outcome_str,
            )
            loser_entry.ranking_points = max(100.0, loser_entry.ranking_points - points_lost)
        
        return changes
    
    def _calculate_prestige_gain(
        self,
        winner_rank: Optional[int],
        loser_rank: Optional[int],
        loser_prestige: float,
        outcome: str,
    ) -> float:
        """Calculate prestige points gained from a win."""
        base_gain = 50.0
        
        # Quality of opponent
        if loser_rank is not None:
            if loser_rank == 0:  # Beat champion
                base_gain += 500
            elif loser_rank <= 5:
                base_gain += (6 - loser_rank) * 50 + 100
            elif loser_rank <= 10:
                base_gain += (11 - loser_rank) * 30
            elif loser_rank <= 15:
                base_gain += (16 - loser_rank) * 20
        else:
            # Unranked opponent
            if loser_prestige > 500:
                base_gain += 75
            elif loser_prestige > 300:
                base_gain += 50
            elif loser_prestige > 100:
                base_gain += 25
        
        # Finish bonus
        if outcome in ["KO", "TKO"]:
            base_gain *= 1.30
        elif outcome == "SUB":
            base_gain *= 1.20
        
        return base_gain
    
    def _calculate_prestige_loss(
        self,
        loser_rank: Optional[int],
        loser_prestige: float,
        winner_rank: Optional[int],
        outcome: str,
    ) -> float:
        """Calculate prestige points lost from a defeat."""
        base_loss = loser_prestige * 0.10
        base_loss = max(base_loss, 25.0)
        base_loss = min(base_loss, 200.0)
        
        # Losing to lower-ranked hurts more
        if loser_rank is not None and winner_rank is not None:
            if winner_rank > loser_rank + 5:
                base_loss *= 1.5
        
        if loser_rank is not None and loser_rank <= 15 and winner_rank is None:
            base_loss *= 1.3
        
        if outcome in ["KO", "TKO"]:
            base_loss *= 1.2
        elif outcome == "SUB":
            base_loss *= 1.1
        
        return base_loss
    
    def _process_loser_drop(
        self,
        loser_entry: RankingEntry,
        loser_rank: int,
        winner_rank: Optional[int],
        changes: List[RankingChange],
        week: int,
        year: int,
    ) -> None:
        """Process ranking drop for fight loser."""
        # Base drop
        if winner_rank is not None and winner_rank > loser_rank:
            # Lost to lower ranked - bigger drop
            base_drop = 2
        else:
            base_drop = 1
        
        # Apply modifiers
        total_drop = calculate_total_movement(
            base_movement=base_drop,
            outcome="DECISION",  # Placeholder - doesn't matter for losses
            winner_streak=0,
            winner_rank=loser_rank,  # loser's rank for bubble calc
            loser_rank=winner_rank,
            is_loss=True,
            is_former_champ=loser_entry.is_former_champion,
            protection_fights=loser_entry.former_champ_protection_fights,
        )
        
        new_rank = min(MAX_RANKED_FIGHTERS + 1, loser_rank + abs(total_drop))
        
        # Use protection
        if loser_entry.is_former_champion and loser_entry.former_champ_protection_fights > 0:
            loser_entry.former_champ_protection_fights -= 1
        
        # Check if dropped out
        if new_rank > MAX_RANKED_FIGHTERS:
            changes.append(RankingChange(
                fighter_id=loser_entry.fighter_id,
                fighter_name=self.get_fighter_name(loser_entry.fighter_id),
                weight_class=self.weight_class,
                old_rank=loser_rank,
                new_rank=None,
                reason=RankingChangeReason.DROPPED_OUT,
                week=week,
                year=year,
            ))
            self.remove_fighter(loser_entry.fighter_id)
        elif new_rank != loser_rank:
            changes.append(RankingChange(
                fighter_id=loser_entry.fighter_id,
                fighter_name=self.get_fighter_name(loser_entry.fighter_id),
                weight_class=self.weight_class,
                old_rank=loser_rank,
                new_rank=new_rank,
                reason=RankingChangeReason.FIGHT_LOSS,
                week=week,
                year=year,
            ))
            self.move_fighter(loser_entry.fighter_id, new_rank)
        
        # Update loser entry
        loser_entry.current_win_streak = 0  # Reset streak
        loser_entry.losses_while_ranked += 1
        loser_entry.last_fight_week = week
        loser_entry.last_fight_year = year
    
    def get_top_contenders(self, n: int = 5) -> List[str]:
        """Get top N contenders (not including champion)."""
        return [e.fighter_id for e in self._rankings[:n]]
    
    def process_weekly_update(self, current_week: int, current_year: int) -> List[RankingChange]:
        """Process weekly maintenance (inactivity checks)."""
        changes = []
        
        for entry in self._rankings:
            entry.weeks_at_rank += 1
            
            # Check inactivity
            if entry.last_fight_week > 0:
                weeks_inactive = (current_year - entry.last_fight_year) * 52 + \
                                (current_week - entry.last_fight_week)
                
                if weeks_inactive > INACTIVITY_WEEKS and entry.rank <= 10:
                    old_rank = entry.rank
                    new_rank = min(MAX_RANKED_FIGHTERS, old_rank + 2)
                    
                    self.move_fighter(entry.fighter_id, new_rank)
                    
                    changes.append(RankingChange(
                        fighter_id=entry.fighter_id,
                        fighter_name=self.get_fighter_name(entry.fighter_id),
                        weight_class=self.weight_class,
                        old_rank=old_rank,
                        new_rank=new_rank,
                        reason=RankingChangeReason.INACTIVITY,
                        week=current_week,
                        year=current_year,
                    ))
        
        return changes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "weight_class": self.weight_class.value,
            "champion_id": self._champion_id,
            "champion_entry": self._champion_entry.to_dict() if self._champion_entry else None,
            "rankings": [e.to_dict() for e in self._rankings],
            "fighter_names": self._fighter_names.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DivisionRankings':
        division = cls(WeightClass(data["weight_class"]))
        division._champion_id = data.get("champion_id")
        if data.get("champion_entry"):
            division._champion_entry = RankingEntry.from_dict(data["champion_entry"])
        division._rankings = [
            RankingEntry.from_dict(e) for e in data.get("rankings", [])
        ]
        division._fighter_names = data.get("fighter_names", {})
        return division


# ============================================================================
# RANKINGS SYSTEM
# ============================================================================

class RankingsSystem:
    """Central rankings manager for all divisions."""
    
    def __init__(self):
        self._divisions: Dict[WeightClass, DivisionRankings] = {
            wc: DivisionRankings(wc) for wc in WeightClass
        }
        self._history: List[RankingChange] = []
        self._p4p_rankings: List[P4PEntry] = []
        self._p4p_history: List[Dict[str, Any]] = []  # Track P4P changes
    
    def get_division(self, weight_class: WeightClass) -> DivisionRankings:
        """Get division rankings object."""
        return self._divisions[weight_class]
    
    def get_rank(self, fighter_id: str, weight_class: WeightClass) -> Optional[int]:
        """Get a fighter's rank in their division."""
        return self._divisions[weight_class].get_rank(fighter_id)
    
    def get_champion(self, weight_class: WeightClass) -> Optional[str]:
        """Get division champion."""
        return self._divisions[weight_class].champion
    
    def is_champion(self, fighter_id: str, weight_class: WeightClass) -> bool:
        """Check if fighter is champion."""
        return self.get_rank(fighter_id, weight_class) == CHAMPION_RANK
    
    def set_champion(
        self,
        fighter_id: str,
        fighter_name: str,
        weight_class: WeightClass,
        week: int = 1,
        year: int = 1,
    ) -> Optional[str]:
        """Set division champion."""
        division = self._divisions[weight_class]
        old_rank = division.get_rank(fighter_id)
        previous = division.set_champion(fighter_id, fighter_name)
        
        change = RankingChange(
            fighter_id=fighter_id,
            fighter_name=fighter_name,
            weight_class=weight_class,
            old_rank=old_rank,
            new_rank=CHAMPION_RANK,
            reason=RankingChangeReason.TITLE_WIN,
            week=week,
            year=year,
        )
        self._history.append(change)
        
        return previous
    
    def add_to_rankings(
        self,
        fighter_id: str,
        fighter_name: str,
        weight_class: WeightClass,
        target_rank: Optional[int] = None,
        week: int = 1,
        year: int = 1,
    ) -> Optional[int]:
        """Add fighter to division rankings."""
        division = self._divisions[weight_class]
        old_rank = division.get_rank(fighter_id)
        
        if old_rank is not None:
            return old_rank
        
        actual_rank = division.add_ranked_fighter(
            fighter_id, fighter_name, target_rank=target_rank
        )
        
        if actual_rank:
            change = RankingChange(
                fighter_id=fighter_id,
                fighter_name=fighter_name,
                weight_class=weight_class,
                old_rank=None,
                new_rank=actual_rank,
                reason=RankingChangeReason.INITIAL_RANKING,
                week=week,
                year=year,
            )
            self._history.append(change)
        
        return actual_rank
    
    def remove_from_rankings(
        self,
        fighter_id: str,
        weight_class: WeightClass,
        reason: RankingChangeReason = RankingChangeReason.RELEASED,
        week: int = 1,
        year: int = 1,
    ) -> Optional[int]:
        """Remove fighter from rankings."""
        division = self._divisions[weight_class]
        old_rank = division.remove_fighter(fighter_id)
        
        if old_rank is not None:
            change = RankingChange(
                fighter_id=fighter_id,
                fighter_name=division.get_fighter_name(fighter_id),
                weight_class=weight_class,
                old_rank=old_rank,
                new_rank=None,
                reason=reason,
                week=week,
                year=year,
            )
            self._history.append(change)
        
        return old_rank
    
    def process_fight_result(
        self,
        winner_id: str,
        winner_name: str,
        loser_id: str,
        loser_name: str,
        weight_class: WeightClass,
        outcome: FightOutcome,
        was_title_fight: bool = False,
        week: int = 1,
        year: int = 1,
    ) -> List[RankingChange]:
        """Process fight result and update rankings."""
        division = self._divisions[weight_class]
        
        changes = division.process_fight_result(
            winner_id=winner_id,
            winner_name=winner_name,
            loser_id=loser_id,
            loser_name=loser_name,
            outcome=outcome,
            was_title_fight=was_title_fight,
            week=week,
            year=year,
        )
        
        self._history.extend(changes)
        
        # Emit events for significant changes
        for change in changes:
            emit(EventType.FIGHTER_RANKED, {
                "fighter_id": change.fighter_id,
                "fighter_name": change.fighter_name,
                "weight_class": weight_class.value,
                "old_rank": change.old_rank,
                "new_rank": change.new_rank,
                "reason": change.reason.value,
                "is_big_mover": change.is_big_mover,
            })
        
        return changes
    
    def get_rankings(self, weight_class: WeightClass) -> List[Tuple[int, str, str]]:
        """Get full rankings for a division: (rank, fighter_id, fighter_name)."""
        division = self._divisions[weight_class]
        rankings = []
        
        if division.champion:
            rankings.append((
                CHAMPION_RANK,
                division.champion,
                division.get_fighter_name(division.champion),
            ))
        
        # Use position (i+1) for consistency with get_rank() method
        for i, entry in enumerate(division._rankings):
            rankings.append((
                i + 1,  # Position-based rank, not entry.rank
                entry.fighter_id,
                division.get_fighter_name(entry.fighter_id),
            ))
        
        return rankings
    
    def get_ranking_history(
        self,
        fighter_id: Optional[str] = None,
        weight_class: Optional[WeightClass] = None,
        limit: int = 50,
    ) -> List[RankingChange]:
        """Get ranking change history with optional filters."""
        history = self._history
        
        if fighter_id:
            history = [h for h in history if h.fighter_id == fighter_id]
        
        if weight_class:
            history = [h for h in history if h.weight_class == weight_class]
        
        return history[-limit:]
    
    def get_big_movers(self, week: int, year: int) -> List[RankingChange]:
        """Get all big ranking moves from a specific week."""
        return [
            h for h in self._history
            if h.week == week and h.year == year and h.is_big_mover
        ]
    
    # =========================================================================
    # P4P RANKINGS
    # =========================================================================
    
    def calculate_p4p_rankings(
        self,
        current_week: int,
        current_year: int,
    ) -> List[P4PEntry]:
        """Calculate and update P4P rankings."""
        old_p4p = {e.fighter_id: e.rank for e in self._p4p_rankings}
        
        candidates = []
        
        for wc, division in self._divisions.items():
            # Add champion
            if division.champion and division._champion_entry:
                entry = division._champion_entry
                score = calculate_p4p_score(
                    is_champion=True,
                    divisional_rank=CHAMPION_RANK,
                    win_streak=entry.current_win_streak,
                    ranked_wins=entry.ranked_wins,
                    title_defenses=entry.title_defenses,
                    last_fight_week=entry.last_fight_week,
                    last_fight_year=entry.last_fight_year,
                    current_week=current_week,
                    current_year=current_year,
                )
                candidates.append(P4PEntry(
                    fighter_id=division.champion,
                    fighter_name=division.get_fighter_name(division.champion),
                    weight_class=wc,
                    rank=0,  # Will be set
                    score=score,
                    is_champion=True,
                    divisional_rank=CHAMPION_RANK,
                    win_streak=entry.current_win_streak,
                    title_defenses=entry.title_defenses,
                    ranked_wins=entry.ranked_wins,
                ))
            
            # Add top contenders
            for entry in division._rankings[:5]:  # Top 5 per division
                score = calculate_p4p_score(
                    is_champion=False,
                    divisional_rank=entry.rank,
                    win_streak=entry.current_win_streak,
                    ranked_wins=entry.ranked_wins,
                    title_defenses=entry.title_defenses,
                    last_fight_week=entry.last_fight_week,
                    last_fight_year=entry.last_fight_year,
                    current_week=current_week,
                    current_year=current_year,
                )
                candidates.append(P4PEntry(
                    fighter_id=entry.fighter_id,
                    fighter_name=division.get_fighter_name(entry.fighter_id),
                    weight_class=wc,
                    rank=0,
                    score=score,
                    is_champion=False,
                    divisional_rank=entry.rank,
                    win_streak=entry.current_win_streak,
                    title_defenses=entry.title_defenses,
                    ranked_wins=entry.ranked_wins,
                ))
        
        # Sort by score and take top 10
        candidates.sort(key=lambda x: -x.score)
        self._p4p_rankings = candidates[:P4P_TOP_COUNT]
        
        # Assign ranks
        for i, entry in enumerate(self._p4p_rankings):
            entry.rank = i + 1
        
        # Track changes
        new_p4p = {e.fighter_id: e.rank for e in self._p4p_rankings}
        p4p_changes = []
        
        for entry in self._p4p_rankings:
            old_rank = old_p4p.get(entry.fighter_id)
            new_rank = entry.rank
            
            if old_rank != new_rank:
                movement = (old_rank - new_rank) if old_rank else new_rank
                p4p_changes.append({
                    "fighter_id": entry.fighter_id,
                    "fighter_name": entry.fighter_name,
                    "weight_class": entry.weight_class.value,
                    "old_rank": old_rank,
                    "new_rank": new_rank,
                    "movement": movement,
                    "is_new_entry": old_rank is None,
                    "week": current_week,
                    "year": current_year,
                })
        
        if p4p_changes:
            self._p4p_history.append({
                "week": current_week,
                "year": current_year,
                "changes": p4p_changes,
            })
        
        return self._p4p_rankings
    
    def get_p4p_rankings(self) -> List[P4PEntry]:
        """Get current P4P rankings."""
        return self._p4p_rankings.copy()
    
    def get_p4p_big_movers(self, week: int, year: int) -> List[Dict[str, Any]]:
        """Get big P4P movers from a week (3+ spots or new entry)."""
        for record in self._p4p_history:
            if record["week"] == week and record["year"] == year:
                return [
                    c for c in record["changes"]
                    if c["is_new_entry"] or abs(c.get("movement", 0)) >= 3
                ]
        return []
    
    # =========================================================================
    # WEEKLY UPDATES
    # =========================================================================
    
    def process_weekly_update(
        self,
        current_week: int,
        current_year: int,
    ) -> Tuple[List[RankingChange], List[Dict[str, Any]]]:
        """
        Process weekly maintenance.
        
        Returns:
            Tuple of (ranking_changes, p4p_changes)
        """
        ranking_changes = []
        
        # Process each division
        for division in self._divisions.values():
            changes = division.process_weekly_update(current_week, current_year)
            ranking_changes.extend(changes)
            self._history.extend(changes)
        
        # Update P4P
        self.calculate_p4p_rankings(current_week, current_year)
        p4p_changes = self.get_p4p_big_movers(current_week, current_year)
        
        return ranking_changes, p4p_changes
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "divisions": {
                wc.value: div.to_dict()
                for wc, div in self._divisions.items()
            },
            "history": [h.to_dict() for h in self._history[-500:]],
            "p4p_rankings": [e.to_dict() for e in self._p4p_rankings],
            "p4p_history": self._p4p_history[-50:],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RankingsSystem':
        system = cls()
        
        for wc_value, div_data in data.get("divisions", {}).items():
            wc = WeightClass(wc_value)
            system._divisions[wc] = DivisionRankings.from_dict(div_data)
        
        system._history = [
            RankingChange.from_dict(h) for h in data.get("history", [])
        ]
        system._p4p_rankings = [
            P4PEntry.from_dict(e) for e in data.get("p4p_rankings", [])
        ]
        system._p4p_history = data.get("p4p_history", [])
        
        return system


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_fighter_rank(fighter_id: str, weight_class: WeightClass) -> Optional[int]:
    """Get a fighter's rank (convenience function)."""
    return rankings_system.get_rank(fighter_id, weight_class)


def is_ranked(fighter_id: str, weight_class: WeightClass) -> bool:
    """Check if a fighter is ranked."""
    return rankings_system.get_rank(fighter_id, weight_class) is not None


def is_champion(fighter_id: str, weight_class: WeightClass) -> bool:
    """Check if a fighter is champion."""
    return rankings_system.get_rank(fighter_id, weight_class) == CHAMPION_RANK


def get_division_champion(weight_class: WeightClass) -> Optional[str]:
    """Get the champion of a division."""
    return rankings_system.get_champion(weight_class)


def get_top_contender(weight_class: WeightClass) -> Optional[str]:
    """Get the #1 contender."""
    division = rankings_system.get_division(weight_class)
    contenders = division.get_top_contenders(1)
    return contenders[0] if contenders else None


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

rankings_system = RankingsSystem()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "RankingChangeReason", "FinishType",
    
    # Data classes
    "RankingEntry", "RankingChange", "P4PEntry",
    
    # Classes
    "DivisionRankings", "RankingsSystem",
    
    # Global instance
    "rankings_system",
    
    # Convenience functions
    "get_fighter_rank", "is_ranked", "is_champion",
    "get_division_champion", "get_top_contender",
    
    # Calculation functions
    "calculate_finish_bonus", "calculate_win_streak_bonus",
    "calculate_upset_scaling", "calculate_p4p_score",
    
    # Constants
    "MAX_RANKED_FIGHTERS", "CHAMPION_RANK", "P4P_TOP_COUNT",
]
