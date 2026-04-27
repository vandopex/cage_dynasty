# systems/fight_offers.py
# Module: Smart Fight Offers System (Enhanced)
# Lines: ~1,350
#
# Bidirectional fight offer system with ranking-based logic,
# smart matchmaking integration, and anti-cheese mechanics.

"""
Cage Dynasty - Smart Fight Offers System

UFC-style matchmaking and fight booking system:
- Bidirectional offers (player <-> AI)
- Ranking-based matchmaking logic
- Integration with MatchmakingEngine for scoring
- Advantages for fighting UP in rankings
- Penalties/cooldowns for fighting DOWN
- Earned title paths (with hype exception for young KO artists)
- Anti-cheese mechanics to prevent exploitation

RULES:
    1. Fighting UP: Bonus ranking points, prestige, bigger potential purse
    2. Fighting DOWN: Cooldown period, reduced gains, reputation hit
    3. Title Shots: Must be top 5, OR young (<26) with 3+ KO streak & high hype
    4. Cheese Stoppers: Cooldowns, AI rejection, promotion pressure
"""

from typing import Dict, List, Optional, Any, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random

# Conditional import for type checking only
if TYPE_CHECKING:
    from systems.matchmaking import MatchmakingEngine, MatchupScore


# ============================================================================
# ENUMS
# ============================================================================

class OfferStatus(Enum):
    """Status of a fight offer."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    COUNTERED = "COUNTERED"


class OfferDirection(Enum):
    """Who initiated the offer."""
    PLAYER_TO_AI = "PLAYER_TO_AI"
    AI_TO_PLAYER = "AI_TO_PLAYER"
    PROMOTION = "PROMOTION"  # Mandatory/ordered by promotion


class DeclineReason(Enum):
    """Why an offer was declined."""
    NOT_INTERESTED = "Not interested in this matchup"
    RANK_TOO_LOW = "Opponent ranked too low"
    RANK_TOO_HIGH = "Opponent ranked too high"
    RECENT_FIGHT = "Fought too recently"
    CAMP_RIVAL = "Will not fight camp mate"
    INJURED = "Currently injured"
    ALREADY_BOOKED = "Already has a fight scheduled"
    BAD_TIMING = "Bad timing"
    LOW_PURSE = "Purse too low"
    DISRESPECTFUL = "Offer considered disrespectful"
    WANTS_TITLE = "Holding out for title shot"
    COOLING_OFF = "On cooldown from fighting down"


class OfferType(Enum):
    """Type of fight being offered."""
    STANDARD = "STANDARD"
    TITLE_FIGHT = "TITLE_FIGHT"
    TITLE_ELIMINATOR = "TITLE_ELIMINATOR"
    MAIN_EVENT = "MAIN_EVENT"
    CO_MAIN = "CO_MAIN"


class FightDirection(Enum):
    """Direction of fight relative to ranking."""
    FIGHTING_UP = "FIGHTING_UP"        # Opponent ranked higher
    FIGHTING_LATERAL = "FIGHTING_LATERAL"  # Similar ranking
    FIGHTING_DOWN = "FIGHTING_DOWN"    # Opponent ranked lower


class MatchupQuality(Enum):
    """Quality rating for a matchup."""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    MISMATCH = "Mismatch"


# ============================================================================
# CONSTANTS
# ============================================================================

# Offer expiration (in weeks)
DEFAULT_OFFER_EXPIRATION = 2

# Cooldown after fighting down (weeks)
FIGHT_DOWN_COOLDOWN_WEEKS = 6

# Minimum weeks between fights
MIN_WEEKS_BETWEEN_FIGHTS = 4

# Ranking thresholds
TITLE_SHOT_RANK_THRESHOLD = 5  # Must be top 5 normally
HYPE_TITLE_SHOT_MIN_STREAK = 3  # KO streak for hype exception
HYPE_TITLE_SHOT_MAX_AGE = 26   # Max age for hype exception

# Lateral fight range (considered "same level")
LATERAL_RANK_RANGE = 3

# Fight up/down bonuses and penalties
FIGHT_UP_RANKING_BONUS = 1.5      # 50% more ranking points
FIGHT_UP_PURSE_BONUS = 1.25       # 25% more purse potential
FIGHT_DOWN_RANKING_PENALTY = 0.5  # 50% less ranking points
FIGHT_DOWN_REPUTATION_HIT = -5    # Rep penalty

# AI acceptance thresholds
AI_MIN_RANK_DIFF_TO_ACCEPT = -10  # Won't accept if they're 10+ ranks higher
AI_PRESTIGE_FIGHT_CHANCE = 0.3   # Chance to accept fighting down for prestige

# Matchup quality thresholds (based on 0-130 score)
QUALITY_THRESHOLDS = {
    MatchupQuality.EXCELLENT: 90,
    MatchupQuality.GOOD: 70,
    MatchupQuality.FAIR: 50,
    MatchupQuality.POOR: 30,
    MatchupQuality.MISMATCH: 0,
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FighterOfferInfo:
    """Fighter info needed for offer logic."""
    fighter_id: str
    name: str
    camp_id: str
    weight_class: str
    rank: Optional[int]  # None = unranked, 0 = champion
    overall_rating: int
    age: int
    wins: int
    losses: int
    win_streak: int
    ko_streak: int  # Consecutive KO/TKO wins
    is_champion: bool
    is_player_fighter: bool
    status: str  # "ACTIVE", "INJURED", etc.
    last_fight_date: Optional[str] = None  # ISO format
    scheduled_fight_date: Optional[str] = None
    recent_opponents: List[str] = field(default_factory=list)
    hype_rating: int = 50  # 1-100 hype/popularity
    style_tags: List[str] = field(default_factory=list)
    
    # Cooldown tracking
    last_fought_down_date: Optional[str] = None
    fights_down_count: int = 0  # How many times fought down recently
    
    @property
    def is_available(self) -> bool:
        return self.status == "ACTIVE" and self.scheduled_fight_date is None
    
    @property
    def is_ranked(self) -> bool:
        return self.rank is not None
    
    @property
    def effective_rank(self) -> int:
        """Rank for comparison (unranked = 20)."""
        if self.is_champion:
            return 0
        return self.rank if self.rank is not None else 20
    
    @property
    def is_title_eligible(self) -> bool:
        """Check if eligible for title shot through normal path."""
        if self.is_champion:
            return True
        if self.rank is not None and self.rank <= TITLE_SHOT_RANK_THRESHOLD:
            return True
        return False
    
    @property
    def is_hype_title_eligible(self) -> bool:
        """Check if eligible through hype exception."""
        if self.age > HYPE_TITLE_SHOT_MAX_AGE:
            return False
        if self.ko_streak < HYPE_TITLE_SHOT_MIN_STREAK:
            return False
        if self.hype_rating < 70:
            return False
        return True
    
    @property
    def rank_display(self) -> str:
        """Format rank for display."""
        if self.is_champion:
            return "C"
        elif self.rank is not None:
            return f"#{self.rank}"
        return "NR"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "camp_id": self.camp_id,
            "weight_class": self.weight_class,
            "rank": self.rank,
            "overall_rating": self.overall_rating,
            "age": self.age,
            "wins": self.wins,
            "losses": self.losses,
            "win_streak": self.win_streak,
            "ko_streak": self.ko_streak,
            "is_champion": self.is_champion,
            "is_player_fighter": self.is_player_fighter,
            "status": self.status,
            "last_fight_date": self.last_fight_date,
            "scheduled_fight_date": self.scheduled_fight_date,
            "recent_opponents": self.recent_opponents,
            "hype_rating": self.hype_rating,
            "style_tags": self.style_tags,
            "last_fought_down_date": self.last_fought_down_date,
            "fights_down_count": self.fights_down_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FighterOfferInfo":
        return cls(**data)


@dataclass
class FightOffer:
    """A fight offer between two fighters."""
    offer_id: str
    
    # Fighters
    offering_fighter_id: str
    offering_fighter_name: str
    target_fighter_id: str
    target_fighter_name: str
    
    # Ranks (for display)
    offering_fighter_rank: Optional[int] = None  # None=unranked, 0=champ
    target_fighter_rank: Optional[int] = None
    
    # Direction and type
    direction: OfferDirection = OfferDirection.AI_TO_PLAYER
    offer_type: OfferType = OfferType.STANDARD
    fight_direction: FightDirection = FightDirection.FIGHTING_LATERAL
    
    # Scheduling
    weight_class: str = ""
    proposed_date: str = ""  # ISO format
    proposed_weeks_out: int = 8
    
    # Terms
    purse_offered: int = 0  # In dollars
    is_main_event: bool = False
    
    # Status
    status: OfferStatus = OfferStatus.PENDING
    created_date: str = ""
    expiration_date: str = ""
    response_date: Optional[str] = None
    decline_reason: Optional[DeclineReason] = None
    
    # Matchup Analysis
    ranking_advantage: int = 0  # Positive = fighting up, negative = fighting down
    matchup_score: float = 0.0  # Raw score (0-130)
    matchup_quality: str = "Good"  # Excellent/Good/Fair/Poor/Mismatch
    matchup_reasons: List[str] = field(default_factory=list)
    
    # Metadata
    notes: str = ""
    
    @property
    def is_step_up(self) -> bool:
        """Check if this is a step-up fight (fighting higher ranked)."""
        return self.fight_direction == FightDirection.FIGHTING_UP
    
    @property
    def is_title_fight(self) -> bool:
        """Check if this is a title fight."""
        return self.offer_type == OfferType.TITLE_FIGHT
    
    @property
    def offering_rank_display(self) -> str:
        """Format offering fighter rank for display."""
        if self.offering_fighter_rank == 0:
            return "C"
        elif self.offering_fighter_rank is not None:
            return f"#{self.offering_fighter_rank}"
        return "NR"
    
    @property
    def target_rank_display(self) -> str:
        """Format target fighter rank for display."""
        if self.target_fighter_rank == 0:
            return "C"
        elif self.target_fighter_rank is not None:
            return f"#{self.target_fighter_rank}"
        return "NR"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "offering_fighter_id": self.offering_fighter_id,
            "offering_fighter_name": self.offering_fighter_name,
            "target_fighter_id": self.target_fighter_id,
            "target_fighter_name": self.target_fighter_name,
            "offering_fighter_rank": self.offering_fighter_rank,
            "target_fighter_rank": self.target_fighter_rank,
            "direction": self.direction.value,
            "offer_type": self.offer_type.value,
            "fight_direction": self.fight_direction.value,
            "weight_class": self.weight_class,
            "proposed_date": self.proposed_date,
            "proposed_weeks_out": self.proposed_weeks_out,
            "purse_offered": self.purse_offered,
            "is_main_event": self.is_main_event,
            "status": self.status.value,
            "created_date": self.created_date,
            "expiration_date": self.expiration_date,
            "response_date": self.response_date,
            "decline_reason": self.decline_reason.value if self.decline_reason else None,
            "ranking_advantage": self.ranking_advantage,
            "matchup_score": self.matchup_score,
            "matchup_quality": self.matchup_quality,
            "matchup_reasons": self.matchup_reasons,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FightOffer":
        return cls(
            offer_id=data["offer_id"],
            offering_fighter_id=data["offering_fighter_id"],
            offering_fighter_name=data["offering_fighter_name"],
            target_fighter_id=data["target_fighter_id"],
            target_fighter_name=data["target_fighter_name"],
            offering_fighter_rank=data.get("offering_fighter_rank"),
            target_fighter_rank=data.get("target_fighter_rank"),
            direction=OfferDirection(data["direction"]),
            offer_type=OfferType(data["offer_type"]),
            fight_direction=FightDirection(data["fight_direction"]),
            weight_class=data["weight_class"],
            proposed_date=data["proposed_date"],
            proposed_weeks_out=data["proposed_weeks_out"],
            purse_offered=data.get("purse_offered", 0),
            is_main_event=data.get("is_main_event", False),
            status=OfferStatus(data["status"]),
            created_date=data["created_date"],
            expiration_date=data["expiration_date"],
            response_date=data.get("response_date"),
            decline_reason=DeclineReason(data["decline_reason"]) if data.get("decline_reason") else None,
            ranking_advantage=data.get("ranking_advantage", 0),
            matchup_score=data.get("matchup_score", 0.0),
            matchup_quality=data.get("matchup_quality", "Good"),
            matchup_reasons=data.get("matchup_reasons", []),
            notes=data.get("notes", ""),
        )


@dataclass
class CooldownEntry:
    """Tracks cooldown for a fighter."""
    fighter_id: str
    cooldown_type: str  # "FIGHT_DOWN", "RECENT_FIGHT", etc.
    start_date: str
    end_date: str
    reason: str = ""


@dataclass
class ScheduledFight:
    """A confirmed scheduled fight."""
    fight_id: str
    fighter1_id: str
    fighter1_name: str
    fighter2_id: str
    fighter2_name: str
    weight_class: str
    scheduled_date: str
    is_title_fight: bool = False
    is_main_event: bool = False
    offer_id: str = ""  # Link to original offer
    purse: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fight_id": self.fight_id,
            "fighter1_id": self.fighter1_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_id": self.fighter2_id,
            "fighter2_name": self.fighter2_name,
            "weight_class": self.weight_class,
            "scheduled_date": self.scheduled_date,
            "is_title_fight": self.is_title_fight,
            "is_main_event": self.is_main_event,
            "offer_id": self.offer_id,
            "purse": self.purse,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledFight":
        return cls(**data)


# ============================================================================
# FIGHT DIRECTION CALCULATION
# ============================================================================

def calculate_fight_direction(
    offering_rank: int,
    target_rank: int,
    lateral_range: int = LATERAL_RANK_RANGE
) -> Tuple[FightDirection, int]:
    """
    Calculate fight direction for the offering fighter.
    
    Returns:
        Tuple of (FightDirection, rank_difference)
        Positive difference = fighting up
    """
    diff = offering_rank - target_rank  # Positive if they're lower ranked
    
    if abs(diff) <= lateral_range:
        return FightDirection.FIGHTING_LATERAL, diff
    elif diff > 0:
        return FightDirection.FIGHTING_UP, diff
    else:
        return FightDirection.FIGHTING_DOWN, diff


def score_to_quality(score: float) -> str:
    """Convert matchup score (0-130) to quality string."""
    if score >= QUALITY_THRESHOLDS[MatchupQuality.EXCELLENT]:
        return MatchupQuality.EXCELLENT.value
    elif score >= QUALITY_THRESHOLDS[MatchupQuality.GOOD]:
        return MatchupQuality.GOOD.value
    elif score >= QUALITY_THRESHOLDS[MatchupQuality.FAIR]:
        return MatchupQuality.FAIR.value
    elif score >= QUALITY_THRESHOLDS[MatchupQuality.POOR]:
        return MatchupQuality.POOR.value
    else:
        return MatchupQuality.MISMATCH.value


# ============================================================================
# OFFER VALIDATION
# ============================================================================

def validate_offer(
    offerer: FighterOfferInfo,
    target: FighterOfferInfo,
    current_date: str,
    weeks_out: int = 8,
) -> Tuple[bool, Optional[DeclineReason], str]:
    """
    Validate if an offer can be made.
    
    Returns:
        Tuple of (is_valid, decline_reason if invalid, message)
    """
    # Check availability
    if not offerer.is_available:
        return False, DeclineReason.ALREADY_BOOKED, f"{offerer.name} is not available"
    
    if not target.is_available:
        return False, DeclineReason.ALREADY_BOOKED, f"{target.name} is not available"
    
    # Check status
    if offerer.status == "INJURED":
        return False, DeclineReason.INJURED, f"{offerer.name} is injured"
    if target.status == "INJURED":
        return False, DeclineReason.INJURED, f"{target.name} is injured"
    
    # Check weight class
    if offerer.weight_class != target.weight_class:
        return False, DeclineReason.NOT_INTERESTED, "Different weight classes"
    
    # Check recent fight
    if target.fighter_id in offerer.recent_opponents:
        return False, DeclineReason.RECENT_FIGHT, "Fought too recently for rematch"
    
    # Check same camp
    if offerer.camp_id == target.camp_id:
        return False, DeclineReason.CAMP_RIVAL, "Cannot fight camp mate"
    
    return True, None, "Offer is valid"


def check_cooldown(
    fighter: FighterOfferInfo,
    target: FighterOfferInfo,
    current_date: str,
) -> Tuple[bool, Optional[str]]:
    """
    Check if fighter is on cooldown for fighting down.
    
    Returns:
        Tuple of (is_on_cooldown, end_date if on cooldown)
    """
    if fighter.last_fought_down_date is None:
        return False, None
    
    # Check if they've fought down too much
    if fighter.fights_down_count >= 2:
        return True, "Must fight at or above rank before fighting down again"
    
    return False, None


# ============================================================================
# AI DECISION LOGIC
# ============================================================================

def ai_evaluate_offer(
    offer: FightOffer,
    ai_fighter: FighterOfferInfo,
    opponent: FighterOfferInfo,
) -> Tuple[bool, Optional[DeclineReason], float]:
    """
    AI evaluates whether to accept a fight offer.
    
    Returns:
        Tuple of (accept, decline_reason if not, acceptance_score)
    """
    score = 50.0  # Base score
    
    # Ranking considerations
    rank_diff = ai_fighter.effective_rank - opponent.effective_rank
    
    # Fighting down - generally reluctant
    if rank_diff < 0:
        # They're higher ranked, being asked to fight down
        if rank_diff < -10:
            return False, DeclineReason.RANK_TOO_LOW, 0.0
        
        # Might accept for prestige/money
        score -= abs(rank_diff) * 3
        
        # Champions are very reluctant to fight unranked
        if ai_fighter.is_champion and opponent.rank is None:
            return False, DeclineReason.DISRESPECTFUL, 0.0
        
        # Top 5 rarely fight outside top 10
        if ai_fighter.rank is not None and ai_fighter.rank <= 5:
            if opponent.rank is None or opponent.rank > 10:
                if random.random() > AI_PRESTIGE_FIGHT_CHANCE:
                    return False, DeclineReason.RANK_TOO_LOW, score
    
    # Fighting up - generally eager
    elif rank_diff > 0:
        score += rank_diff * 2
        
        # Very eager to fight champions
        if opponent.is_champion:
            score += 30
    
    # Title shot considerations
    if ai_fighter.is_title_eligible and not opponent.is_champion:
        # They want a title shot, not a regular fight
        if ai_fighter.rank is not None and ai_fighter.rank <= 3:
            if random.random() > 0.4:
                return False, DeclineReason.WANTS_TITLE, score
    
    # Win streak makes them confident
    if ai_fighter.win_streak >= 3:
        score += 10
    
    # Losing streak makes them cautious about tough fights
    if ai_fighter.win_streak < 0:  # Negative = lose streak
        if rank_diff > 5:
            score -= 15
    
    # Hype fighters are more willing to take big fights
    if ai_fighter.hype_rating > 70:
        score += 10
    
    # Recent opponents - no immediate rematches
    if opponent.fighter_id in ai_fighter.recent_opponents:
        return False, DeclineReason.RECENT_FIGHT, 0.0
    
    # Final decision
    accept_threshold = 40.0
    
    if score >= accept_threshold:
        return True, None, score
    else:
        # Pick most appropriate decline reason
        if rank_diff < -5:
            return False, DeclineReason.RANK_TOO_LOW, score
        elif rank_diff > 10:
            return False, DeclineReason.RANK_TOO_HIGH, score
        else:
            return False, DeclineReason.NOT_INTERESTED, score


# ============================================================================
# TITLE SHOT ELIGIBILITY
# ============================================================================

def check_title_eligibility(
    fighter: FighterOfferInfo,
    champion: Optional[FighterOfferInfo] = None,
) -> Tuple[bool, str]:
    """
    Check if fighter is eligible for a title shot.
    
    Returns:
        Tuple of (is_eligible, reason)
    """
    if fighter.is_champion:
        return False, "Already champion"
    
    # Standard path: Top 5 ranking
    if fighter.is_title_eligible:
        return True, f"Ranked #{fighter.rank} - earned title shot"
    
    # Hype exception: Young KO artist
    if fighter.is_hype_title_eligible:
        return True, f"Hype exception: {fighter.ko_streak} KO streak, age {fighter.age}, {fighter.hype_rating} hype"
    
    # Not eligible
    if fighter.rank is None:
        return False, "Must be ranked to challenge for title"
    else:
        return False, f"Ranked #{fighter.rank} - need top {TITLE_SHOT_RANK_THRESHOLD} or hype exception"


# ============================================================================
# PURSE CALCULATION
# ============================================================================

def calculate_smart_purse(
    fighter: FighterOfferInfo,
    opponent: FighterOfferInfo,
    matchup_score: float = 50.0,
    is_title: bool = False,
    is_main_event: bool = False,
) -> int:
    """
    Calculate purse based on rankings, matchup quality, and fight importance.
    """
    # Base purse from ratings
    base = 5000 + (fighter.overall_rating + opponent.overall_rating) * 50
    
    # Rank bonus
    rank_bonus = 0
    if fighter.rank is not None and fighter.rank <= 5:
        rank_bonus += 5000
    if opponent.rank is not None and opponent.rank <= 5:
        rank_bonus += 5000
    if fighter.is_champion or opponent.is_champion:
        rank_bonus += 10000
    
    # Quality bonus
    quality_bonus = int(matchup_score * 100)
    
    # Win streak bonus
    streak_bonus = 0
    if fighter.win_streak >= 3:
        streak_bonus += fighter.win_streak * 500
    if opponent.win_streak >= 3:
        streak_bonus += opponent.win_streak * 500
    
    total = base + rank_bonus + quality_bonus + streak_bonus
    
    # Multipliers
    if is_title:
        total = int(total * 3.0)
    elif is_main_event:
        total = int(total * 1.5)
    
    # Step-up bonus (fighter gets more for taking risk)
    if opponent.effective_rank < fighter.effective_rank:
        total = int(total * FIGHT_UP_PURSE_BONUS)
    
    return total


# ============================================================================
# MATCHUP REASON INFERENCE
# ============================================================================

def infer_matchup_reasons(
    fighter: FighterOfferInfo,
    opponent: FighterOfferInfo,
    matchup_score: Optional[Any] = None,  # MatchupScore from matchmaking engine
) -> List[str]:
    """
    Generate human-readable reasons for this matchup.
    """
    reasons = []
    
    # Use matchmaking engine scores if available
    if matchup_score is not None and hasattr(matchup_score, 'ranking_score'):
        if matchup_score.ranking_score >= 25:
            reasons.append("Close in rankings")
        if hasattr(matchup_score, 'skill_score') and matchup_score.skill_score >= 16:
            reasons.append("Evenly matched")
        if hasattr(matchup_score, 'streak_score') and matchup_score.streak_score >= 10:
            reasons.append("Battle of win streaks")
        if hasattr(matchup_score, 'title_score') and matchup_score.title_score >= 15:
            if fighter.is_champion or opponent.is_champion:
                reasons.append("Title fight")
            else:
                reasons.append("Title implications")
        if hasattr(matchup_score, 'rivalry_score') and matchup_score.rivalry_score > 0:
            reasons.append("Rivalry match")
        if hasattr(matchup_score, 'entertainment_score') and matchup_score.entertainment_score >= 7:
            reasons.append("Exciting style matchup")
    
    # Fallback inference from fighter data
    if not reasons:
        rank_diff = abs(fighter.effective_rank - opponent.effective_rank)
        
        if rank_diff <= 2:
            reasons.append("Close in rankings")
        
        rating_diff = abs(fighter.overall_rating - opponent.overall_rating)
        if rating_diff <= 5:
            reasons.append("Evenly matched")
        
        if fighter.win_streak >= 3 and opponent.win_streak >= 3:
            reasons.append("Battle of win streaks")
        elif fighter.win_streak >= 3 or opponent.win_streak >= 3:
            reasons.append("Win streak on the line")
        
        if fighter.is_champion or opponent.is_champion:
            reasons.append("Title fight")
        elif (fighter.rank is not None and fighter.rank <= 5 and 
              opponent.rank is not None and opponent.rank <= 5):
            reasons.append("Title eliminator")
    
    # Add direction-based reason if nothing else
    if not reasons:
        if fighter.effective_rank > opponent.effective_rank:
            reasons.append("Step up in competition")
        else:
            reasons.append("Favorable matchup")
    
    return reasons[:3]  # Limit to 3 reasons


# ============================================================================
# FIGHT OFFERS MANAGER
# ============================================================================

class FightOffersManager:
    """
    Manages all fight offers and scheduling.
    Integrates with MatchmakingEngine for smart matchmaking.
    """
    
    def __init__(self):
        self._offers: Dict[str, FightOffer] = {}
        self._scheduled_fights: Dict[str, ScheduledFight] = {}
        self._cooldowns: Dict[str, List[CooldownEntry]] = {}  # fighter_id -> cooldowns
        self._fighters: Dict[str, FighterOfferInfo] = {}
        self._offer_counter = 0
        self._fight_counter = 0
    
    # -------------------------------------------------------------------------
    # Fighter Registration
    # -------------------------------------------------------------------------
    
    def register_fighter(self, fighter: FighterOfferInfo) -> None:
        """Register or update a fighter."""
        self._fighters[fighter.fighter_id] = fighter
    
    def unregister_fighter(self, fighter_id: str) -> None:
        """Remove a fighter."""
        self._fighters.pop(fighter_id, None)
    
    def get_fighter(self, fighter_id: str) -> Optional[FighterOfferInfo]:
        """Get fighter info."""
        return self._fighters.get(fighter_id)
    
    def update_fighter_rank(self, fighter_id: str, rank: Optional[int]) -> None:
        """Update a fighter's rank."""
        if fighter_id in self._fighters:
            self._fighters[fighter_id].rank = rank
    
    def clear_fighters(self) -> None:
        """Clear all fighters (for refresh)."""
        self._fighters.clear()
    
    # -------------------------------------------------------------------------
    # Smart Offer Generation (The Main Method)
    # -------------------------------------------------------------------------
    
    def generate_smart_offers_for_fighter(
        self,
        fighter_id: str,
        matchmaking_engine: Optional[Any] = None,  # MatchmakingEngine
        current_date: str = "",
        min_weeks: int = 4,
        max_weeks: int = 8,
        max_step_up: int = 3,
        max_step_down: int = 3,
    ) -> List[FightOffer]:
        """
        Generate smart fight offers for a fighter.
        
        Uses MatchmakingEngine if available, otherwise falls back to basic logic.
        
        Args:
            fighter_id: The fighter to generate offers for
            matchmaking_engine: Optional MatchmakingEngine for advanced scoring
            current_date: Current date string
            min_weeks: Minimum weeks until fight
            max_weeks: Maximum weeks until fight
            max_step_up: Maximum step-up offers
            max_step_down: Maximum favorable offers
            
        Returns:
            List of FightOffer objects ready for display
        """
        fighter = self._fighters.get(fighter_id)
        if not fighter or not fighter.is_available:
            return []
        
        offers = []
        
        if matchmaking_engine is not None:
            offers = self._generate_smart_offers_with_engine(
                fighter, matchmaking_engine, current_date,
                min_weeks, max_weeks, max_step_up, max_step_down
            )
        
        # Fallback if engine not available or returned no offers
        if not offers:
            offers = self._generate_basic_offers(
                fighter, current_date,
                min_weeks, max_weeks, max_step_up, max_step_down
            )
        
        return offers
    
    def _generate_smart_offers_with_engine(
        self,
        fighter: FighterOfferInfo,
        matchmaking_engine: Any,
        current_date: str,
        min_weeks: int,
        max_weeks: int,
        max_step_up: int,
        max_step_down: int,
    ) -> List[FightOffer]:
        """Generate offers using the matchmaking engine."""
        offers = []
        
        try:
            # Get matchups from engine
            matchups = matchmaking_engine.find_opponents(
                fighter.fighter_id,
                limit=20,
                same_weight_class=True
            )
        except Exception:
            return []
        
        if not matchups:
            return []
        
        # Filter and categorize matchups
        step_up_matchups = []
        step_down_matchups = []
        
        for matchup in matchups:
            opponent = self._fighters.get(matchup.fighter2_id)
            if not opponent:
                continue
            if not opponent.is_available:
                continue
            if opponent.camp_id == fighter.camp_id:
                continue
            if opponent.fighter_id in fighter.recent_opponents:
                continue
            
            # Calculate direction
            fight_dir, rank_diff = calculate_fight_direction(
                fighter.effective_rank,
                opponent.effective_rank
            )
            
            if fight_dir == FightDirection.FIGHTING_UP:
                step_up_matchups.append((matchup, opponent, fight_dir, rank_diff))
            else:
                step_down_matchups.append((matchup, opponent, fight_dir, rank_diff))
        
        # Sort by matchup score
        step_up_matchups.sort(key=lambda x: x[0].total_score, reverse=True)
        step_down_matchups.sort(key=lambda x: x[0].total_score, reverse=True)
        
        # Take top from each category
        selected = []
        selected.extend(step_up_matchups[:max_step_up])
        selected.extend(step_down_matchups[:max_step_down])
        
        # Create offers
        for matchup, opponent, fight_dir, rank_diff in selected:
            offer = self._create_offer_from_matchup(
                fighter, opponent, matchup,
                fight_dir, rank_diff,
                current_date, min_weeks, max_weeks
            )
            offers.append(offer)
        
        return offers
    
    def _generate_basic_offers(
        self,
        fighter: FighterOfferInfo,
        current_date: str,
        min_weeks: int,
        max_weeks: int,
        max_step_up: int,
        max_step_down: int,
    ) -> List[FightOffer]:
        """Fallback basic offer generation without matchmaking engine."""
        offers = []
        
        # Get all valid opponents
        all_opponents = []
        for opp in self._fighters.values():
            if opp.fighter_id == fighter.fighter_id:
                continue
            if opp.weight_class != fighter.weight_class:
                continue
            if not opp.is_available:
                continue
            if opp.camp_id == fighter.camp_id:
                continue
            if opp.fighter_id in fighter.recent_opponents:
                continue
            
            fight_dir, rank_diff = calculate_fight_direction(
                fighter.effective_rank,
                opp.effective_rank
            )
            
            all_opponents.append((opp, fight_dir, rank_diff))
        
        # Separate by direction
        step_up = [(o, d, r) for o, d, r in all_opponents if d == FightDirection.FIGHTING_UP]
        step_down = [(o, d, r) for o, d, r in all_opponents if d != FightDirection.FIGHTING_UP]
        
        # Sort by rank proximity
        step_up.sort(key=lambda x: x[0].effective_rank)  # Lowest rank first
        step_down.sort(key=lambda x: abs(x[0].overall_rating - fighter.overall_rating))
        
        # Select and create offers
        for opp, fight_dir, rank_diff in step_up[:max_step_up]:
            offer = self._create_basic_offer(
                fighter, opp, fight_dir, rank_diff,
                current_date, min_weeks, max_weeks
            )
            offers.append(offer)
        
        for opp, fight_dir, rank_diff in step_down[:max_step_down]:
            offer = self._create_basic_offer(
                fighter, opp, fight_dir, rank_diff,
                current_date, min_weeks, max_weeks
            )
            offers.append(offer)
        
        return offers
    
    def _create_offer_from_matchup(
        self,
        fighter: FighterOfferInfo,
        opponent: FighterOfferInfo,
        matchup: Any,  # MatchupScore
        fight_dir: FightDirection,
        rank_diff: int,
        current_date: str,
        min_weeks: int,
        max_weeks: int,
    ) -> FightOffer:
        """Create a FightOffer from a matchmaking engine matchup."""
        # Determine offer type
        is_title = fighter.is_champion or opponent.is_champion
        is_eliminator = (
            not is_title and
            fighter.rank is not None and fighter.rank <= 5 and
            opponent.rank is not None and opponent.rank <= 5
        )
        
        if is_title:
            offer_type = OfferType.TITLE_FIGHT
        elif is_eliminator:
            offer_type = OfferType.TITLE_ELIMINATOR
        elif fighter.overall_rating >= 75 or opponent.overall_rating >= 75:
            offer_type = OfferType.MAIN_EVENT
        else:
            offer_type = OfferType.STANDARD
        
        # Calculate weeks
        weeks_out = random.randint(min_weeks, max_weeks)
        if is_title:
            weeks_out = max(weeks_out, 8)
        
        # Get matchup score and quality
        score = matchup.total_score if hasattr(matchup, 'total_score') else 50.0
        quality = score_to_quality(score)
        
        # Get reasons
        reasons = infer_matchup_reasons(fighter, opponent, matchup)
        
        # Calculate purse
        purse = calculate_smart_purse(
            fighter, opponent, score,
            is_title, offer_type == OfferType.MAIN_EVENT
        )
        
        # Create offer
        self._offer_counter += 1
        offer_id = f"offer_{self._offer_counter}"
        
        return FightOffer(
            offer_id=offer_id,
            offering_fighter_id=opponent.fighter_id,  # AI offering to player
            offering_fighter_name=opponent.name,
            target_fighter_id=fighter.fighter_id,
            target_fighter_name=fighter.name,
            offering_fighter_rank=opponent.rank,
            target_fighter_rank=fighter.rank,
            direction=OfferDirection.AI_TO_PLAYER,
            offer_type=offer_type,
            fight_direction=fight_dir,
            weight_class=fighter.weight_class,
            proposed_date=current_date,
            proposed_weeks_out=weeks_out,
            purse_offered=purse,
            is_main_event=(offer_type in [OfferType.MAIN_EVENT, OfferType.TITLE_FIGHT]),
            status=OfferStatus.PENDING,
            created_date=current_date,
            expiration_date=current_date,
            ranking_advantage=rank_diff,
            matchup_score=score,
            matchup_quality=quality,
            matchup_reasons=reasons,
        )
    
    def _create_basic_offer(
        self,
        fighter: FighterOfferInfo,
        opponent: FighterOfferInfo,
        fight_dir: FightDirection,
        rank_diff: int,
        current_date: str,
        min_weeks: int,
        max_weeks: int,
    ) -> FightOffer:
        """Create a basic FightOffer without matchmaking engine."""
        is_title = fighter.is_champion or opponent.is_champion
        is_eliminator = (
            not is_title and
            fighter.rank is not None and fighter.rank <= 5 and
            opponent.rank is not None and opponent.rank <= 5
        )
        
        if is_title:
            offer_type = OfferType.TITLE_FIGHT
        elif is_eliminator:
            offer_type = OfferType.TITLE_ELIMINATOR
        elif fighter.overall_rating >= 75 or opponent.overall_rating >= 75:
            offer_type = OfferType.MAIN_EVENT
        else:
            offer_type = OfferType.STANDARD
        
        weeks_out = random.randint(min_weeks, max_weeks)
        if is_title:
            weeks_out = max(weeks_out, 8)
        
        # Calculate basic matchup score
        rank_score = max(0, 30 - abs(rank_diff) * 3)
        rating_diff = abs(fighter.overall_rating - opponent.overall_rating)
        skill_score = max(0, 20 - rating_diff)
        streak_score = min(15, (fighter.win_streak + opponent.win_streak) * 2)
        title_score = 20 if is_title else (10 if is_eliminator else 0)
        
        score = rank_score + skill_score + streak_score + title_score
        quality = score_to_quality(score)
        reasons = infer_matchup_reasons(fighter, opponent)
        
        purse = calculate_smart_purse(
            fighter, opponent, score,
            is_title, offer_type == OfferType.MAIN_EVENT
        )
        
        self._offer_counter += 1
        offer_id = f"offer_{self._offer_counter}"
        
        return FightOffer(
            offer_id=offer_id,
            offering_fighter_id=opponent.fighter_id,
            offering_fighter_name=opponent.name,
            target_fighter_id=fighter.fighter_id,
            target_fighter_name=fighter.name,
            offering_fighter_rank=opponent.rank,
            target_fighter_rank=fighter.rank,
            direction=OfferDirection.AI_TO_PLAYER,
            offer_type=offer_type,
            fight_direction=fight_dir,
            weight_class=fighter.weight_class,
            proposed_date=current_date,
            proposed_weeks_out=weeks_out,
            purse_offered=purse,
            is_main_event=(offer_type in [OfferType.MAIN_EVENT, OfferType.TITLE_FIGHT]),
            status=OfferStatus.PENDING,
            created_date=current_date,
            expiration_date=current_date,
            ranking_advantage=rank_diff,
            matchup_score=score,
            matchup_quality=quality,
            matchup_reasons=reasons,
        )
    
    # -------------------------------------------------------------------------
    # Generate All Offers (Batch Generation)
    # -------------------------------------------------------------------------
    
    def generate_all_player_offers(
        self,
        player_camp_id: str,
        matchmaking_engine: Optional[Any] = None,
        current_date: str = "",
        min_weeks: int = 4,
        max_weeks: int = 8,
        max_step_up: int = 3,
        max_step_down: int = 3,
    ) -> List[FightOffer]:
        """
        Generate offers for all available player fighters.
        
        Returns:
            List of all generated offers
        """
        all_offers = []
        
        player_fighters = [
            f for f in self._fighters.values()
            if f.camp_id == player_camp_id and f.is_available
        ]
        
        for fighter in player_fighters:
            offers = self.generate_smart_offers_for_fighter(
                fighter.fighter_id,
                matchmaking_engine=matchmaking_engine,
                current_date=current_date,
                min_weeks=min_weeks,
                max_weeks=max_weeks,
                max_step_up=max_step_up,
                max_step_down=max_step_down,
            )
            all_offers.extend(offers)
        
        return all_offers
    
    # -------------------------------------------------------------------------
    # Original create_offer for Manual/Player-Initiated Offers
    # -------------------------------------------------------------------------
    
    def create_offer(
        self,
        offering_fighter_id: str,
        target_fighter_id: str,
        direction: OfferDirection,
        current_date: str,
        weeks_out: int = 8,
        purse: int = 0,
        is_main_event: bool = False,
    ) -> Tuple[Optional[FightOffer], str]:
        """
        Create a new fight offer (manual/player-initiated).
        
        Returns:
            Tuple of (offer if created, message)
        """
        offerer = self._fighters.get(offering_fighter_id)
        target = self._fighters.get(target_fighter_id)
        
        if not offerer or not target:
            return None, "Fighter not found"
        
        # Validate
        valid, reason, msg = validate_offer(offerer, target, current_date, weeks_out)
        if not valid:
            return None, msg
        
        # Check cooldowns
        on_cooldown, cooldown_msg = check_cooldown(offerer, target, current_date)
        if on_cooldown:
            return None, f"On cooldown: {cooldown_msg}"
        
        # Calculate fight direction
        fight_dir, rank_diff = calculate_fight_direction(
            offerer.effective_rank,
            target.effective_rank
        )
        
        # Determine offer type
        offer_type = OfferType.STANDARD
        if target.is_champion or offerer.is_champion:
            eligible, reason_text = check_title_eligibility(
                offerer if target.is_champion else target,
                target if target.is_champion else offerer
            )
            if eligible:
                offer_type = OfferType.TITLE_FIGHT
            else:
                return None, f"Title fight not possible: {reason_text}"
        elif offerer.rank is not None and target.rank is not None:
            if offerer.rank <= 5 and target.rank <= 5:
                offer_type = OfferType.TITLE_ELIMINATOR
        
        # Calculate matchup score
        score = self._calculate_matchup_score(offerer, target)
        quality = score_to_quality(score)
        reasons = infer_matchup_reasons(offerer, target)
        
        # Create offer
        self._offer_counter += 1
        offer_id = f"offer_{self._offer_counter}"
        
        offer = FightOffer(
            offer_id=offer_id,
            offering_fighter_id=offering_fighter_id,
            offering_fighter_name=offerer.name,
            target_fighter_id=target_fighter_id,
            target_fighter_name=target.name,
            offering_fighter_rank=offerer.rank,
            target_fighter_rank=target.rank,
            direction=direction,
            offer_type=offer_type,
            fight_direction=fight_dir,
            weight_class=offerer.weight_class,
            proposed_date=current_date,
            proposed_weeks_out=weeks_out,
            purse_offered=purse,
            is_main_event=is_main_event,
            status=OfferStatus.PENDING,
            created_date=current_date,
            expiration_date=current_date,
            ranking_advantage=rank_diff,
            matchup_score=score,
            matchup_quality=quality,
            matchup_reasons=reasons,
        )
        
        self._offers[offer_id] = offer
        return offer, f"Offer created: {offerer.name} vs {target.name}"
    
    def _calculate_matchup_score(
        self,
        fighter1: FighterOfferInfo,
        fighter2: FighterOfferInfo
    ) -> float:
        """Calculate how good this matchup is (basic scoring)."""
        score = 50.0
        
        # Ranking proximity
        rank_diff = abs(fighter1.effective_rank - fighter2.effective_rank)
        if rank_diff <= 2:
            score += 30
        elif rank_diff <= 5:
            score += 20
        elif rank_diff <= 10:
            score += 10
        
        # Win streaks make it exciting
        if fighter1.win_streak >= 3 or fighter2.win_streak >= 3:
            score += 15
        
        # Title implications
        if fighter1.is_champion or fighter2.is_champion:
            score += 25
        
        # Rating balance
        rating_diff = abs(fighter1.overall_rating - fighter2.overall_rating)
        if rating_diff <= 5:
            score += 10
        elif rating_diff >= 15:
            score -= 10
        
        return min(130.0, max(0.0, score))
    
    # -------------------------------------------------------------------------
    # Offer Response
    # -------------------------------------------------------------------------
    
    def accept_offer(
        self,
        offer_id: str,
        current_date: str,
    ) -> Tuple[bool, str, Optional[ScheduledFight]]:
        """
        Accept a fight offer and schedule the fight.
        
        Returns:
            Tuple of (success, message, scheduled_fight)
        """
        offer = self._offers.get(offer_id)
        if not offer:
            return False, "Offer not found", None
        
        if offer.status != OfferStatus.PENDING:
            return False, f"Offer is {offer.status.value}", None
        
        # Create scheduled fight
        self._fight_counter += 1
        fight_id = f"fight_{self._fight_counter}"
        
        fight = ScheduledFight(
            fight_id=fight_id,
            fighter1_id=offer.offering_fighter_id,
            fighter1_name=offer.offering_fighter_name,
            fighter2_id=offer.target_fighter_id,
            fighter2_name=offer.target_fighter_name,
            weight_class=offer.weight_class,
            scheduled_date=offer.proposed_date,
            is_title_fight=offer.is_title_fight,
            is_main_event=offer.is_main_event,
            offer_id=offer_id,
            purse=offer.purse_offered,
        )
        
        # Update offer status
        offer.status = OfferStatus.ACCEPTED
        offer.response_date = current_date
        
        # Mark fighters as scheduled
        if offer.offering_fighter_id in self._fighters:
            self._fighters[offer.offering_fighter_id].scheduled_fight_date = offer.proposed_date
        if offer.target_fighter_id in self._fighters:
            self._fighters[offer.target_fighter_id].scheduled_fight_date = offer.proposed_date
        
        self._scheduled_fights[fight_id] = fight
        
        return True, f"Fight scheduled: {fight.fighter1_name} vs {fight.fighter2_name}", fight
    
    def decline_offer(
        self,
        offer_id: str,
        reason: DeclineReason,
        current_date: str,
    ) -> Tuple[bool, str]:
        """
        Decline a fight offer.
        
        Returns:
            Tuple of (success, message)
        """
        offer = self._offers.get(offer_id)
        if not offer:
            return False, "Offer not found"
        
        if offer.status != OfferStatus.PENDING:
            return False, f"Offer is {offer.status.value}"
        
        offer.status = OfferStatus.DECLINED
        offer.decline_reason = reason
        offer.response_date = current_date
        
        return True, f"Offer declined: {reason.value}"
    
    def expire_old_offers(self, current_date: str, weeks_old: int = 2) -> int:
        """
        Expire offers older than specified weeks.
        
        Returns:
            Number of offers expired
        """
        expired = 0
        for offer in self._offers.values():
            if offer.status == OfferStatus.PENDING:
                # Would do proper date math here
                offer.status = OfferStatus.EXPIRED
                expired += 1
        return expired
    
    # -------------------------------------------------------------------------
    # AI Offer Generation
    # -------------------------------------------------------------------------
    
    def generate_ai_offers_for_player(
        self,
        player_camp_id: str,
        current_date: str,
        max_offers: int = 3,
    ) -> List[FightOffer]:
        """
        Generate fight offers from AI camps to player's fighters.
        
        Returns:
            List of generated offers
        """
        offers = []
        
        # Get player fighters
        player_fighters = [
            f for f in self._fighters.values()
            if f.camp_id == player_camp_id and f.is_available
        ]
        
        # Get AI fighters
        ai_fighters = [
            f for f in self._fighters.values()
            if f.camp_id != player_camp_id and f.is_available
        ]
        
        for player_fighter in player_fighters:
            # Find suitable AI opponents
            suitable = [
                af for af in ai_fighters
                if af.weight_class == player_fighter.weight_class
                and af.fighter_id not in player_fighter.recent_opponents
            ]
            
            if not suitable:
                continue
            
            # Score potential matchups
            matchups = []
            for ai_fighter in suitable:
                score = self._calculate_matchup_score(ai_fighter, player_fighter)
                
                # AI prefers favorable matchups
                rank_diff = ai_fighter.effective_rank - player_fighter.effective_rank
                if rank_diff < 0:  # AI would be fighting up
                    score += 20
                
                matchups.append((ai_fighter, score))
            
            # Sort by score and pick top
            matchups.sort(key=lambda x: x[1], reverse=True)
            
            for ai_fighter, score in matchups[:2]:
                if len(offers) >= max_offers:
                    break
                
                # Check if AI wants to make this offer
                if score < 40:
                    continue
                
                # Random chance to actually make offer
                if random.random() > 0.6:
                    continue
                
                offer, msg = self.create_offer(
                    ai_fighter.fighter_id,
                    player_fighter.fighter_id,
                    OfferDirection.AI_TO_PLAYER,
                    current_date,
                )
                
                if offer:
                    offers.append(offer)
        
        return offers
    
    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------
    
    def get_pending_offers(
        self,
        fighter_id: Optional[str] = None,
        direction: Optional[OfferDirection] = None,
    ) -> List[FightOffer]:
        """Get pending offers, optionally filtered."""
        offers = [o for o in self._offers.values() if o.status == OfferStatus.PENDING]
        
        if fighter_id:
            offers = [
                o for o in offers
                if o.offering_fighter_id == fighter_id or o.target_fighter_id == fighter_id
            ]
        
        if direction:
            offers = [o for o in offers if o.direction == direction]
        
        return offers
    
    def get_offers_for_fighter(
        self,
        fighter_id: str,
        include_expired: bool = False,
    ) -> List[FightOffer]:
        """Get all offers involving a fighter."""
        offers = [
            o for o in self._offers.values()
            if o.offering_fighter_id == fighter_id or o.target_fighter_id == fighter_id
        ]
        
        if not include_expired:
            offers = [o for o in offers if o.status != OfferStatus.EXPIRED]
        
        return offers
    
    def get_incoming_offers(self, fighter_id: str) -> List[FightOffer]:
        """Get offers where this fighter is the target."""
        return [
            o for o in self._offers.values()
            if o.target_fighter_id == fighter_id and o.status == OfferStatus.PENDING
        ]
    
    def get_outgoing_offers(self, fighter_id: str) -> List[FightOffer]:
        """Get offers this fighter has made."""
        return [
            o for o in self._offers.values()
            if o.offering_fighter_id == fighter_id and o.status == OfferStatus.PENDING
        ]
    
    def get_scheduled_fights(
        self,
        fighter_id: Optional[str] = None,
    ) -> List[ScheduledFight]:
        """Get scheduled fights."""
        fights = list(self._scheduled_fights.values())
        
        if fighter_id:
            fights = [
                f for f in fights
                if f.fighter1_id == fighter_id or f.fighter2_id == fighter_id
            ]
        
        return fights
    
    def get_available_opponents(
        self,
        fighter_id: str,
        include_title_fights: bool = True,
    ) -> List[Tuple[FighterOfferInfo, str, FightDirection]]:
        """
        Get available opponents for a fighter.
        
        Returns:
            List of (fighter, eligibility_note, fight_direction)
        """
        fighter = self._fighters.get(fighter_id)
        if not fighter:
            return []
        
        opponents = []
        
        for opp in self._fighters.values():
            if opp.fighter_id == fighter_id:
                continue
            if opp.weight_class != fighter.weight_class:
                continue
            if not opp.is_available:
                continue
            if opp.camp_id == fighter.camp_id:
                continue
            if opp.fighter_id in fighter.recent_opponents:
                continue
            
            # Calculate direction
            fight_dir, rank_diff = calculate_fight_direction(
                fighter.effective_rank,
                opp.effective_rank
            )
            
            # Build note
            notes = []
            if opp.is_champion:
                if include_title_fights:
                    eligible, reason = check_title_eligibility(fighter, opp)
                    if eligible:
                        notes.append(f"TITLE SHOT: {reason}")
                    else:
                        notes.append(f"Not eligible: {reason}")
                        continue
                else:
                    continue
            
            if fight_dir == FightDirection.FIGHTING_UP:
                notes.append(f"+{rank_diff} ranks up")
            elif fight_dir == FightDirection.FIGHTING_DOWN:
                notes.append(f"{rank_diff} ranks down (cooldown applies)")
            
            if opp.win_streak >= 3:
                notes.append(f"{opp.win_streak}W streak")
            
            note = ", ".join(notes) if notes else "Standard matchup"
            opponents.append((opp, note, fight_dir))
        
        # Sort by ranking
        opponents.sort(key=lambda x: x[0].effective_rank)
        
        return opponents
    
    # -------------------------------------------------------------------------
    # Fight Direction Benefits/Penalties
    # -------------------------------------------------------------------------
    
    def get_fight_direction_modifiers(
        self,
        fight_direction: FightDirection,
    ) -> Dict[str, float]:
        """
        Get modifiers based on fight direction.
        
        Returns:
            Dict with ranking_multiplier, purse_multiplier, reputation_change
        """
        if fight_direction == FightDirection.FIGHTING_UP:
            return {
                "ranking_multiplier": FIGHT_UP_RANKING_BONUS,
                "purse_multiplier": FIGHT_UP_PURSE_BONUS,
                "reputation_change": 5,
                "description": "Fighting up: +50% ranking points, +25% purse, +5 rep",
            }
        elif fight_direction == FightDirection.FIGHTING_DOWN:
            return {
                "ranking_multiplier": FIGHT_DOWN_RANKING_PENALTY,
                "purse_multiplier": 1.0,
                "reputation_change": FIGHT_DOWN_REPUTATION_HIT,
                "description": f"Fighting down: -50% ranking points, {FIGHT_DOWN_REPUTATION_HIT} rep, {FIGHT_DOWN_COOLDOWN_WEEKS}wk cooldown",
            }
        else:
            return {
                "ranking_multiplier": 1.0,
                "purse_multiplier": 1.0,
                "reputation_change": 0,
                "description": "Lateral fight: Standard rewards",
            }
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "offers": {k: v.to_dict() for k, v in self._offers.items()},
            "scheduled_fights": {k: v.to_dict() for k, v in self._scheduled_fights.items()},
            "fighters": {k: v.to_dict() for k, v in self._fighters.items()},
            "offer_counter": self._offer_counter,
            "fight_counter": self._fight_counter,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FightOffersManager":
        manager = cls()
        manager._offer_counter = data.get("offer_counter", 0)
        manager._fight_counter = data.get("fight_counter", 0)
        
        for fighter_data in data.get("fighters", {}).values():
            fighter = FighterOfferInfo.from_dict(fighter_data)
            manager._fighters[fighter.fighter_id] = fighter
        
        for offer_data in data.get("offers", {}).values():
            offer = FightOffer.from_dict(offer_data)
            manager._offers[offer.offer_id] = offer
        
        for fight_data in data.get("scheduled_fights", {}).values():
            fight = ScheduledFight.from_dict(fight_data)
            manager._scheduled_fights[fight.fight_id] = fight
        
        return manager


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_fight_offers_manager() -> FightOffersManager:
    """Create a new fight offers manager."""
    return FightOffersManager()


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_offer(offer: FightOffer, perspective_fighter_id: Optional[str] = None) -> str:
    """Format offer for display."""
    direction_icon = {
        FightDirection.FIGHTING_UP: "▲",
        FightDirection.FIGHTING_LATERAL: "↔",
        FightDirection.FIGHTING_DOWN: "▼",
    }
    
    type_icon = {
        OfferType.TITLE_FIGHT: "[TITLE]",
        OfferType.TITLE_ELIMINATOR: "[ELIM]",
        OfferType.MAIN_EVENT: "[MAIN]",
        OfferType.CO_MAIN: "[CO-MAIN]",
        OfferType.STANDARD: "",
    }
    
    status_icon = {
        OfferStatus.PENDING: "⏳",
        OfferStatus.ACCEPTED: "✓",
        OfferStatus.DECLINED: "✗",
        OfferStatus.EXPIRED: "⏰",
        OfferStatus.CANCELLED: "🚫",
    }
    
    type_str = type_icon.get(offer.offer_type, "")
    status_str = status_icon.get(offer.status, "")
    dir_str = direction_icon.get(offer.fight_direction, "")
    
    line = f"{status_str} {type_str} {offer.offering_fighter_name} vs {offer.target_fighter_name}"
    line += f" [{offer.weight_class}] {dir_str}"
    
    if offer.status == OfferStatus.PENDING:
        line += f" - {offer.proposed_weeks_out} weeks out"
    
    return line.strip()


def format_fight_direction_info(direction: FightDirection, rank_diff: int) -> str:
    """Format fight direction for display."""
    if direction == FightDirection.FIGHTING_UP:
        return f"▲ Fighting UP (+{abs(rank_diff)} ranks) - Bonus ranking points & purse!"
    elif direction == FightDirection.FIGHTING_DOWN:
        return f"▼ Fighting DOWN ({abs(rank_diff)} ranks) - Reduced rewards, cooldown applies"
    else:
        return f"↔ Lateral matchup - Standard rewards"


def format_title_eligibility(fighter: FighterOfferInfo) -> str:
    """Format title eligibility for display."""
    eligible, reason = check_title_eligibility(fighter)
    if eligible:
        return f"✓ TITLE ELIGIBLE: {reason}"
    else:
        return f"✗ Not eligible: {reason}"


def format_matchup_quality(quality: str) -> Tuple[str, str]:
    """
    Get quality string and suggested color.
    
    Returns:
        Tuple of (quality_string, color_name)
    """
    colors = {
        "Excellent": "green",
        "Good": "cyan",
        "Fair": "yellow",
        "Poor": "orange",
        "Mismatch": "red",
    }
    return quality, colors.get(quality, "white")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "OfferStatus", "OfferDirection", "DeclineReason", "OfferType", 
    "FightDirection", "MatchupQuality",
    
    # Data classes
    "FighterOfferInfo", "FightOffer", "CooldownEntry", "ScheduledFight",
    
    # Manager
    "FightOffersManager", "create_fight_offers_manager",
    
    # Functions
    "calculate_fight_direction", "validate_offer", "check_cooldown",
    "ai_evaluate_offer", "check_title_eligibility", "calculate_smart_purse",
    "score_to_quality", "infer_matchup_reasons",
    
    # Display
    "format_offer", "format_fight_direction_info", "format_title_eligibility",
    "format_matchup_quality",
    
    # Constants
    "TITLE_SHOT_RANK_THRESHOLD", "HYPE_TITLE_SHOT_MIN_STREAK",
    "HYPE_TITLE_SHOT_MAX_AGE", "FIGHT_DOWN_COOLDOWN_WEEKS",
    "FIGHT_UP_RANKING_BONUS", "FIGHT_DOWN_RANKING_PENALTY",
    "QUALITY_THRESHOLDS",
]
