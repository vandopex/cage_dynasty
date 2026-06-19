# simulation/world_init.py
# World Initialization System
# Lines: ~1,800
#
# Generates the initial game world with:
# - AI camps at various tiers
# - Coaches for all camps (based on tier)
# - Fighters for all weight classes (~30 per division)
# - 2-3 years of simulated fight history with REAL EVENTS (DFC 1, DFC 2, etc.)
# - Established champions and rankings
# - Popularity system integrated from start

"""
Cage Dynasty - World Initialization

This module creates a living, breathing MMA world with history:
- Generates 20-30 AI training camps
- Creates ~270 fighters across all weight classes (~30 per division)
- Simulates 2-3 years of fight history as ACTUAL EVENTS (DFC 1 through DFC ~105)
- Establishes champions, rankings, and records
- Tracks popularity that carries into gameplay

Fighter count supports the cooldown system where 40-50% of
fighters are unavailable at any given time.

POPULARITY SYSTEM:
==================
Popularity (0-100) affects:
- Card positioning (star power)
- Sponsorship value
- Fight offers
- PPV/gate contribution

Popularity Sources:
- Skill tier at generation (elite starts higher)
- Wins: +2-3
- Finishes (KO/Sub): +5-7
- Title wins: +10-15
- Title defenses: +5-8
- Undefeated streak bonus
- Losses: -2-3
- Inactivity decay (after 6 months)

USAGE:
    from simulation.world_init import WorldInitializer
    
    initializer = WorldInitializer(game_state)
    initializer.initialize_world()
    
    # Get the starting event number for the player's game
    next_event_num = initializer.get_next_event_number()  # e.g., 106
"""

import random
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Ship K4: canonical style generator (respects generation_weight + country bias)
try:
    from styles import generate_style_for_fighter
except ImportError:
    generate_style_for_fighter = None


# ============================================================================
# FULL FIGHT ENGINE SUPPORT (Optional - for realistic history)
# ============================================================================

FULL_ENGINE_AVAILABLE = False
try:
    from simulation.fight_engine import (
        simulate_fight as engine_simulate_fight,
        FighterAttributes,
        FightConfig,
    )
    FULL_ENGINE_AVAILABLE = True
except ImportError:
    pass

# Popularity System (shared module)
POPULARITY_MODULE_AVAILABLE = False
try:
    from popularity import (
        calculate_popularity_change as shared_calculate_popularity_change,
        calculate_star_power as shared_calculate_star_power,
        is_main_event_worthy as shared_is_main_event_worthy,
    )
    POPULARITY_MODULE_AVAILABLE = True
except ImportError:
    pass

# Coach System (v2 - skill-based)
COACHES_AVAILABLE = False
CoachSystem = None
generate_coach = None
try:
    from systems.coaches import (
        CoachSystem,
        Coach,
        generate_coach,
        generate_starting_coach_options,
    )
    COACHES_AVAILABLE = True
except ImportError:
    pass

# Amateur System
AMATEUR_AVAILABLE = False
AmateurSystem = None
try:
    from systems.amateur import (
        AmateurSystem,
        create_amateur_system,
    )
    AMATEUR_AVAILABLE = True
except ImportError:
    pass

# Aging System (for during-sim aging, decline, retirement)
AGING_AVAILABLE = False
try:
    from aging import AgingSystem, calculate_retirement_probability
    AGING_AVAILABLE = True
except ImportError:
    pass

# Rivalry System (for during-sim rivalry seeding from repeat matchups)
RIVALRY_AVAILABLE = False
try:
    from rivalry import get_rivalry_system, FightContext
    RIVALRY_AVAILABLE = True
except ImportError:
    try:
        from narrative.rivalry import get_rivalry_system, FightContext
        RIVALRY_AVAILABLE = True
    except ImportError:
        pass

# Traits System (for AI fighter trait assignment at world gen)
TRAITS_AVAILABLE = False
try:
    from systems.traits import assign_traits as _assign_traits
    TRAITS_AVAILABLE = True
except ImportError:
    try:
        from traits import assign_traits as _assign_traits
        TRAITS_AVAILABLE = True
    except ImportError:
        pass


# ============================================================================
# NAME DATABASE (Comprehensive)
# ============================================================================

# Name generation — single source of truth
# Imported from name_database.py (28 countries, large pools)
try:
    from name_database import COUNTRY_NAMES, generate_unique_name as _gen_unique
except ImportError:
    # Fallback minimal pool if name_database not found
    COUNTRY_NAMES = {"United States": {"first": ["James","John","Michael","David","Chris","Ryan","Daniel","Marcus","Kevin","Brandon"], "last": ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez"]}}
    def _gen_unique(country, used): return 'Fighter ' + str(len(used)+1)

# Camp name components
CAMP_PREFIXES = [
    "Iron", "Steel", "Dragon", "Tiger", "Lion", "Wolf", "Apex", "Elite", "Prime", "Alpha",
    "Thunder", "Lightning", "Storm", "Phoenix", "Warrior", "Champion", "Victory", "Power", "Force", "Strike",
    "Combat", "Battle", "Fight", "War", "Gladiator", "Spartan", "Viking", "Samurai", "Ronin", "Shogun",
    "Cobra", "Viper", "Hawk", "Eagle", "Raven", "Bear", "Bull", "Ram", "Jaguar", "Panther",
    "Black", "Red", "Gold", "Silver", "Platinum", "Diamond", "Royal", "Imperial", "Supreme", "Ultimate"
]

CAMP_SUFFIXES = [
    "MMA", "Fight Team", "Combat", "Athletics", "Academy", "Gym", "Training Center", "Martial Arts",
    "Fighting", "Kombat", "Warriors", "Fighters", "Champions", "Elite", "Pro", "Sports",
    "Alliance", "Coalition", "Brotherhood", "Legion", "Squad", "Crew", "Unit", "Force",
    "Foundation", "Institute", "Performance", "Conditioning", "Systems", "Methods"
]

# Weight class definitions
WEIGHT_CLASSES = [
    "Strawweight", "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
    "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
]

WEIGHT_CLASS_RANGES = {
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

# Fighters per division (min, max)
FIGHTERS_PER_DIVISION = {
    "Strawweight": (25, 32),
    "Flyweight": (28, 35),
    "Bantamweight": (30, 38),
    "Featherweight": (30, 38),
    "Lightweight": (32, 42),
    "Welterweight": (32, 40),
    "Middleweight": (28, 36),
    "Light Heavyweight": (25, 32),
    "Heavyweight": (22, 28),
}


# ============================================================================
# POPULARITY CONSTANTS
# ============================================================================

# Starting popularity by skill tier
TIER_STARTING_POPULARITY = {
    "elite": (35, 50),      # Well-known coming in
    "top": (25, 40),        # Some recognition
    "good": (15, 30),       # Fringe known
    "average": (8, 18),     # Unknown
    "developing": (5, 12),  # Complete unknown
    "novice": (3, 10),      # Debut level
}

# Popularity changes from fight results
POPULARITY_WIN = (2, 4)              # Base win
POPULARITY_FINISH_BONUS = (3, 5)     # KO/TKO/SUB bonus (added to win)
POPULARITY_TITLE_WIN = (10, 15)      # Winning a title
POPULARITY_TITLE_DEFENSE = (5, 8)    # Defending title
POPULARITY_LOSS = (-3, -1)           # Base loss
POPULARITY_LOSS_STREAK_PENALTY = -2  # Per loss in streak (after 2)
POPULARITY_UNDEFEATED_BONUS = 2      # Per win while undefeated (after 3 wins)

# Popularity decay
POPULARITY_DECAY_THRESHOLD_WEEKS = 26  # 6 months
POPULARITY_DECAY_RATE = 2              # Per month inactive after threshold


# ============================================================================
# CARD BUILDING CONSTANTS
# ============================================================================

# Card slot scoring - blend of rank and popularity
RANK_WEIGHT = 0.7       # 70% rank importance
POPULARITY_WEIGHT = 0.3  # 30% popularity importance

# Main event requirements (must meet at least one)
MAIN_EVENT_REQUIREMENTS = {
    "title_fight": True,                    # Any title fight
    "combined_popularity": 120,             # Both fighters combined
    "top_3_clash": True,                    # Both fighters top 3 ranked
    "champion_involved": True,              # Either fighter is/was champion
}

# Minimum requirements for main event (non-title)
MAIN_EVENT_MIN_RANK = 5  # At least one fighter must be top 5


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class GeneratedFighter:
    """Represents a generated fighter before adding to game state"""
    fighter_id: str
    name: str
    country: str
    weight_class: str
    age: int
    
    # Physical attributes
    height: int  # cm
    reach: int   # cm
    weight: float  # lbs
    
    # Core stats (1-100)
    attributes: Dict[str, int] = field(default_factory=dict)
    
    # Fighting style
    style: str = "Balanced"
    stance: str = "Orthodox"
    
    # Record (built during history simulation)
    wins: int = 0
    losses: int = 0
    draws: int = 0
    ko_wins: int = 0       # Track finish types for excitement factor
    sub_wins: int = 0
    
    # Career info
    camp_id: Optional[str] = None
    ranking: Optional[int] = None
    is_champion: bool = False
    
    # Skill tier for simulation
    skill_rating: int = 50  # Overall rating for matchmaking
    skill_tier: str = "average"  # Track original tier

    # Potential ceiling — bounds how high attributes can grow over career.
    # Bridge reads this into _fighter_data["potential"] and the training
    # loop consults it in _diminishing_gain. Default 75 = Average grade
    # mid-band; overwritten by generate_fighter with grade-band logic.
    potential_ceiling: int = 75

    # POPULARITY SYSTEM
    popularity: int = 10  # 0-100, affects card position, sponsorships, etc.
    
    # Fight history - list of fight records with event names
    fight_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Streak tracking
    current_win_streak: int = 0
    current_loss_streak: int = 0

    # Activity tracking (for decay)
    last_fight_week: int = 0

    # Lifecycle (aging-during-sim)
    is_active: bool = True
    retirement_age: Optional[int] = None
    retirement_week: Optional[int] = None

    # Body frame relative to weight class. Drives cut severity and
    # division-move alerts. Assigned in generate_fighters() after construction.
    body_frame: int = 5
    natural_weight_class: str = ""

    # Personality — drives challenge acceptance and offer frequency.
    # Assigned in generate_fighters() after construction.
    personality: str = ""


@dataclass
class GeneratedCamp:
    """Represents a generated AI camp"""
    camp_id: str
    name: str
    location: str
    tier: str  # GARAGE, LOCAL, REGIONAL, NATIONAL, ELITE
    reputation: int
    balance: int
    fighter_ids: List[str] = field(default_factory=list)
    coach_ids: List[str] = field(default_factory=list)


@dataclass 
class SimulatedFight:
    """Record of a simulated historical fight"""
    winner_id: str
    loser_id: str
    method: str  # KO, TKO, SUB, DEC
    round_ended: int
    was_title_fight: bool = False
    event_name: str = ""           # e.g., "DFC 47"
    event_number: int = 0          # e.g., 47
    card_slot: str = "prelim"      # main_event, co_main, main_card, prelim, early_prelim
    weight_class: str = ""
    winner_name: str = ""
    loser_name: str = ""


@dataclass
class SimulatedEvent:
    """
    Represents a complete fight card event.
    
    UFC-style structure:
    - Main Event (1): Title fight or star power match
    - Co-Main (1): High-profile bout
    - Main Card (3): Ranked fights
    - Prelims (4): Lower ranked
    - Early Prelims (3): Unranked prospects
    """
    event_number: int              # DFC event number (1, 2, 3, ...)
    event_name: str                # "DFC 1", "DFC 2", etc.
    week_number: int               # Week in simulation when this occurred
    
    # Fights organized by card position
    main_event: Optional[SimulatedFight] = None
    co_main: Optional[SimulatedFight] = None
    main_card: List[SimulatedFight] = field(default_factory=list)
    prelims: List[SimulatedFight] = field(default_factory=list)
    early_prelims: List[SimulatedFight] = field(default_factory=list)
    
    @property
    def all_fights(self) -> List[SimulatedFight]:
        """Get all fights in card order"""
        fights = []
        if self.main_event:
            fights.append(self.main_event)
        if self.co_main:
            fights.append(self.co_main)
        fights.extend(self.main_card)
        fights.extend(self.prelims)
        fights.extend(self.early_prelims)
        return fights
    
    @property
    def total_fights(self) -> int:
        count = 0
        if self.main_event:
            count += 1
        if self.co_main:
            count += 1
        count += len(self.main_card)
        count += len(self.prelims)
        count += len(self.early_prelims)
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event for saving"""
        return {
            "event_number": self.event_number,
            "event_name": self.event_name,
            "week_number": self.week_number,
            "main_event": self._fight_to_dict(self.main_event),
            "co_main": self._fight_to_dict(self.co_main),
            "main_card": [self._fight_to_dict(f) for f in self.main_card],
            "prelims": [self._fight_to_dict(f) for f in self.prelims],
            "early_prelims": [self._fight_to_dict(f) for f in self.early_prelims],
        }
    
    def _fight_to_dict(self, fight: Optional[SimulatedFight]) -> Optional[Dict]:
        if not fight:
            return None
        return {
            "winner_id": fight.winner_id,
            "loser_id": fight.loser_id,
            "winner_name": fight.winner_name,
            "loser_name": fight.loser_name,
            "method": fight.method,
            "round_ended": fight.round_ended,
            "was_title_fight": fight.was_title_fight,
            "card_slot": fight.card_slot,
            "weight_class": fight.weight_class,
        }


@dataclass
class BeltReign:
    """Record of a single championship reign"""
    champion_id: str
    champion_name: str
    weight_class: str
    
    # Reign timeline
    won_week: int                    # Week number belt was won
    won_event: str                   # Event name (e.g., "DFC 15")
    won_from: Optional[str] = None   # Fighter ID of previous champion (None = inaugural)
    won_from_name: Optional[str] = None
    won_method: str = ""             # How they won the belt
    
    # Reign stats
    successful_defenses: int = 0
    
    # Reign end (filled when they lose)
    lost_week: Optional[int] = None
    lost_event: Optional[str] = None
    lost_to: Optional[str] = None
    lost_to_name: Optional[str] = None
    lost_method: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """True if this reign is still active"""
        return self.lost_week is None
    
    @property
    def reign_length_weeks(self) -> int:
        """Length of reign in weeks (ongoing or completed)"""
        if self.lost_week:
            return self.lost_week - self.won_week
        return 0  # Will be calculated live during game
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "champion_id": self.champion_id,
            "champion_name": self.champion_name,
            "weight_class": self.weight_class,
            "won_week": self.won_week,
            "won_event": self.won_event,
            "won_from": self.won_from,
            "won_from_name": self.won_from_name,
            "won_method": self.won_method,
            "successful_defenses": self.successful_defenses,
            "lost_week": self.lost_week,
            "lost_event": self.lost_event,
            "lost_to": self.lost_to,
            "lost_to_name": self.lost_to_name,
            "lost_method": self.lost_method,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeltReign":
        return cls(**data)


class BeltHistory:
    """
    Tracks the complete history of a championship belt.
    
    For each weight class, maintains:
    - List of all reigns in chronological order
    - Current champion reference
    - Stats like longest reign, most defenses, etc.
    """
    
    def __init__(self):
        # All reigns by weight class (chronological order)
        self.reigns: Dict[str, List[BeltReign]] = {wc: [] for wc in WEIGHT_CLASSES}
        
        # Current champions (quick reference)
        self.current_champions: Dict[str, str] = {}  # weight_class -> fighter_id
    
    def crown_initial_champion(
        self,
        fighter_id: str,
        fighter_name: str,
        weight_class: str,
        week: int,
        event_name: str,
        won_method: str = "Inaugural Champion",
    ) -> BeltReign:
        """Crown the inaugural champion of a division (or a vacant-title winner via won_method override)"""
        reign = BeltReign(
            champion_id=fighter_id,
            champion_name=fighter_name,
            weight_class=weight_class,
            won_week=week,
            won_event=event_name,
            won_from=None,  # Inaugural / vacated belt — no predecessor
            won_from_name=None,
            won_method=won_method,
        )
        self.reigns[weight_class].append(reign)
        self.current_champions[weight_class] = fighter_id
        return reign
    
    def title_changes_hands(
        self,
        new_champion_id: str,
        new_champion_name: str,
        old_champion_id: str,
        old_champion_name: str,
        weight_class: str,
        week: int,
        event_name: str,
        method: str,
    ) -> BeltReign:
        """Record a title change"""
        # End the previous reign
        if self.reigns[weight_class]:
            old_reign = self.reigns[weight_class][-1]
            if old_reign.is_active:
                old_reign.lost_week = week
                old_reign.lost_event = event_name
                old_reign.lost_to = new_champion_id
                old_reign.lost_to_name = new_champion_name
                old_reign.lost_method = method
        
        # Start new reign
        reign = BeltReign(
            champion_id=new_champion_id,
            champion_name=new_champion_name,
            weight_class=weight_class,
            won_week=week,
            won_event=event_name,
            won_from=old_champion_id,
            won_from_name=old_champion_name,
            won_method=method,
        )
        self.reigns[weight_class].append(reign)
        self.current_champions[weight_class] = new_champion_id
        return reign
    
    def record_title_defense(self, weight_class: str) -> None:
        """Record a successful title defense"""
        if self.reigns[weight_class]:
            current_reign = self.reigns[weight_class][-1]
            if current_reign.is_active:
                current_reign.successful_defenses += 1

    def vacate_belt(self, weight_class: str, week: int, event_name: str, reason: str = "Retired") -> None:
        """End the current reign without crowning a new champion. Belt sits vacant until next title fight."""
        if self.reigns[weight_class]:
            current_reign = self.reigns[weight_class][-1]
            if current_reign.is_active:
                current_reign.lost_week = week
                current_reign.lost_event = event_name
                current_reign.lost_to = None
                current_reign.lost_to_name = None
                current_reign.lost_method = reason
        self.current_champions.pop(weight_class, None)
    
    def get_current_champion(self, weight_class: str) -> Optional[str]:
        """Get current champion ID for a weight class"""
        return self.current_champions.get(weight_class)
    
    def get_current_reign(self, weight_class: str) -> Optional[BeltReign]:
        """Get current reign for a weight class"""
        if self.reigns[weight_class]:
            reign = self.reigns[weight_class][-1]
            if reign.is_active:
                return reign
        return None
    
    def get_all_reigns(self, weight_class: str) -> List[BeltReign]:
        """Get all reigns for a weight class"""
        return self.reigns[weight_class]
    
    def get_fighter_reigns(self, fighter_id: str) -> List[BeltReign]:
        """Get all reigns by a specific fighter across all divisions"""
        reigns = []
        for wc_reigns in self.reigns.values():
            for reign in wc_reigns:
                if reign.champion_id == fighter_id:
                    reigns.append(reign)
        return reigns
    
    def get_longest_reign(self, weight_class: str) -> Optional[BeltReign]:
        """Get the longest reign in a division"""
        completed = [r for r in self.reigns[weight_class] if not r.is_active]
        if not completed:
            return None
        return max(completed, key=lambda r: r.reign_length_weeks)
    
    def get_most_defenses(self, weight_class: str) -> Optional[BeltReign]:
        """Get the reign with most defenses in a division"""
        if not self.reigns[weight_class]:
            return None
        return max(self.reigns[weight_class], key=lambda r: r.successful_defenses)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize belt history for saving"""
        return {
            "reigns": {
                wc: [reign.to_dict() for reign in reigns]
                for wc, reigns in self.reigns.items()
            },
            "current_champions": self.current_champions.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeltHistory":
        """Deserialize from save data"""
        history = cls()
        for wc, reign_dicts in data.get("reigns", {}).items():
            if wc in history.reigns:
                history.reigns[wc] = [BeltReign.from_dict(r) for r in reign_dicts]
        history.current_champions = data.get("current_champions", {}).copy()
        return history


# ============================================================================
# POPULARITY HELPER FUNCTIONS
# ============================================================================

def calculate_starting_popularity(skill_tier: str, amateur_bonus: int = 0) -> int:
    """
    Calculate starting popularity based on skill tier and amateur success.
    
    Args:
        skill_tier: Fighter's skill tier (elite, top, good, average, developing, novice)
        amateur_bonus: Bonus from amateur career (tournament wins, etc.)
        
    Returns:
        Starting popularity (0-100)
    """
    pop_range = TIER_STARTING_POPULARITY.get(skill_tier, (8, 18))
    base_pop = random.randint(pop_range[0], pop_range[1])
    
    # Add amateur bonus (capped)
    total = base_pop + min(amateur_bonus, 15)
    
    return max(0, min(100, total))


def calculate_popularity_change(
    won: bool,
    method: str,
    was_title_fight: bool,
    was_title_defense: bool,
    win_streak: int,
    loss_streak: int,
    current_popularity: int,
) -> int:
    """
    Calculate popularity change from a fight result.
    Uses shared popularity module when available, otherwise local calculation.
    """
    # Use shared module if available
    if POPULARITY_MODULE_AVAILABLE:
        return shared_calculate_popularity_change(
            won=won,
            method=method,
            was_title_fight=was_title_fight,
            was_title_defense=was_title_defense,
            win_streak=win_streak,
            loss_streak=loss_streak,
            current_popularity=current_popularity,
        )
    
    # Fallback: local calculation
    change = 0
    
    if won:
        # Base win bonus
        change += random.randint(*POPULARITY_WIN)
        
        # Finish bonus
        if method in ("KO", "TKO", "SUB"):
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
    
    # Apply diminishing returns at high popularity
    if current_popularity > 80 and change > 0:
        change = change // 2
    
    return change


def calculate_star_power(
    fighter1_rank: Optional[int],
    fighter2_rank: Optional[int],
    fighter1_popularity: int,
    fighter2_popularity: int,
    is_title_fight: bool,
) -> float:
    """
    Calculate combined star power for card positioning.
    
    Higher star power = higher card position.
    
    Args:
        fighter1_rank: Rank of fighter 1 (None = unranked, 0 = champion)
        fighter2_rank: Rank of fighter 2
        fighter1_popularity: Popularity of fighter 1
        fighter2_popularity: Popularity of fighter 2
        is_title_fight: Whether this is a title fight
        
    Returns:
        Star power score (0-200+)
    """
    # Title fights always get priority
    if is_title_fight:
        return 300  # Guaranteed main event consideration
    
    # Calculate rank score (lower rank = higher score)
    def rank_to_score(rank: Optional[int]) -> float:
        if rank is None or rank < 0:
            return 5  # Unranked
        if rank == 0:
            return 100  # Champion
        if rank <= 3:
            return 80 - (rank * 5)  # Top 3: 75, 70, 65
        if rank <= 5:
            return 60 - (rank * 3)  # Top 5: 48, 45
        if rank <= 10:
            return 35 - (rank * 2)  # Top 10: 23-15
        return max(5, 20 - rank)  # Lower ranked
    
    r1_score = rank_to_score(fighter1_rank)
    r2_score = rank_to_score(fighter2_rank)
    
    # Combined rank score (weighted)
    rank_score = (r1_score + r2_score) * RANK_WEIGHT
    
    # Combined popularity score
    pop_score = (fighter1_popularity + fighter2_popularity) * POPULARITY_WEIGHT
    
    return rank_score + pop_score


def is_main_event_worthy(
    fighter1_rank: Optional[int],
    fighter2_rank: Optional[int],
    fighter1_popularity: int,
    fighter2_popularity: int,
    is_title_fight: bool,
) -> bool:
    """
    Determine if a fight is worthy of main event.
    
    Requirements (must meet at least one):
    1. Title fight
    2. Combined popularity >= 120
    3. Both fighters top 3 ranked
    4. One fighter is/was champion (rank 0 or very high popularity)
    
    And must meet minimum:
    - At least one fighter top 5 ranked OR
    - Combined popularity >= 100
    """
    # Title fights always qualify
    if is_title_fight:
        return True
    
    # Check minimum requirements first
    r1_top5 = fighter1_rank is not None and 0 <= fighter1_rank <= 5
    r2_top5 = fighter2_rank is not None and 0 <= fighter2_rank <= 5
    combined_pop = fighter1_popularity + fighter2_popularity
    
    if not (r1_top5 or r2_top5 or combined_pop >= 100):
        return False  # Doesn't meet minimum
    
    # Check qualifying criteria
    # Combined popularity
    if combined_pop >= MAIN_EVENT_REQUIREMENTS["combined_popularity"]:
        return True
    
    # Top 3 clash
    r1_top3 = fighter1_rank is not None and 0 <= fighter1_rank <= 3
    r2_top3 = fighter2_rank is not None and 0 <= fighter2_rank <= 3
    if r1_top3 and r2_top3:
        return True
    
    # Champion involved (rank 0 or popularity 70+)
    is_champ1 = fighter1_rank == 0 or fighter1_popularity >= 70
    is_champ2 = fighter2_rank == 0 or fighter2_popularity >= 70
    if is_champ1 or is_champ2:
        return True
    
    return False


# ============================================================================
# FIGHTER GENERATOR
# ============================================================================

class FighterGenerator:
    """Generates realistic fighters with varied attributes"""
    
    # Ship K4: legacy flat list — superseded by generate_style_for_fighter
    # which uses generation_weight + country bias from styles.py. Kept as
    # reference only; the active generation path no longer reads this list.
    # NOTE: "Brawler" and "Grappler" entries here are not in the canonical
    # 11-style set (core/types.py:FightingStyle) — never re-use this list
    # without remapping those.
    STYLES = ["Striker", "Grappler", "Wrestler", "BJJ Specialist", "Balanced", "Brawler", "Counter Striker", "Pressure Fighter"]
    STANCES = ["Orthodox", "Southpaw", "Switch"]
    
    # Country weights for distribution
    COUNTRY_WEIGHTS = {
        "United States": 25,
        "Brazil": 20,
        "Russia": 12,
        "United Kingdom": 8,
        "Canada": 6,
        "Mexico": 5,
        "Japan": 4,
        "South Korea": 3,
        "Australia": 4,
        "Netherlands": 3,
        "Poland": 3,
        "Nigeria": 3,
        "Thailand": 2,
        "China": 2,
        "Sweden": 2,
        "France": 2,
        "Ireland": 2,
        "New Zealand": 1,
        "Georgia": 2,
        "Argentina": 1,
    }
    
    def __init__(self, starting_year: int = 2025):
        self.starting_year = starting_year
        self.used_names: set = set()
    
    def generate_country(self) -> str:
        """Select a country based on weighted distribution"""
        countries = list(self.COUNTRY_WEIGHTS.keys())
        weights = list(self.COUNTRY_WEIGHTS.values())
        return random.choices(countries, weights=weights, k=1)[0]
    
    def generate_name(self, country: str) -> str:
        """Generate a unique name based on country"""
        
        names_data = COUNTRY_NAMES.get(country, COUNTRY_NAMES["United States"])
        
        for _ in range(100):
            first = random.choice(names_data["first"])
            last = random.choice(names_data["last"])
            full_name = f"{first} {last}"
            
            if full_name not in self.used_names:
                self.used_names.add(full_name)
                return full_name
        
        # Fallback with unique suffix
        first = random.choice(names_data["first"])
        last = random.choice(names_data["last"])
        suffix = str(random.randint(1, 99))
        return f"{first} {last} {suffix}"
    
    def generate_attributes(self, skill_tier: str) -> Dict[str, int]:
        """Generate fighter attributes based on skill tier"""
        
        tier_ranges = {
            "elite": (70, 95),
            "top": (60, 85),
            "good": (50, 75),
            "average": (40, 65),
            "developing": (30, 55),
            "novice": (20, 45),
        }
        
        low, high = tier_ranges.get(skill_tier, (40, 65))
        
        attributes = {
            # Physical
            "strength": random.randint(low, high),
            "speed": random.randint(low, high),
            "cardio": random.randint(low, high),
            "chin": random.randint(low, high),
            "recovery": random.randint(low, high),
            
            # Striking
            "boxing": random.randint(low, high),
            "kicks": random.randint(low, high),
            "clinch": random.randint(low, high),
            "power": random.randint(low, high),
            "accuracy": random.randint(low, high),
            
            # Grappling
            "wrestling": random.randint(low, high),
            "bjj": random.randint(low, high),
            "takedown_defense": random.randint(low, high),
            "top_control": random.randint(low, high),
            "submissions": random.randint(low, high),
            
            # Mental
            "heart": random.randint(low, high),
            "iq": random.randint(low, high),
            "composure": random.randint(low, high),
        }
        
        return attributes
    
    def generate_fighter(
        self,
        weight_class: str,
        skill_tier: str = "average",
        age_range: Tuple[int, int] = (22, 35),
        amateur_bonus: int = 0,
    ) -> GeneratedFighter:
        """Generate a complete fighter with popularity"""
        
        country = self.generate_country()
        name = self.generate_name(country)
        age = random.randint(*age_range)
        
        # Physical stats based on weight class
        weight_range = WEIGHT_CLASS_RANGES[weight_class]
        weight = random.uniform(weight_range[0], weight_range[1])
        
        # Height correlates with weight class
        height_base = {
            "Strawweight": 160, "Flyweight": 165, "Bantamweight": 170,
            "Featherweight": 175, "Lightweight": 178, "Welterweight": 183,
            "Middleweight": 188, "Light Heavyweight": 191, "Heavyweight": 193
        }
        height = height_base[weight_class] + random.randint(-5, 8)
        reach = height + random.randint(-3, 10)
        
        attributes = self.generate_attributes(skill_tier)
        
        # Calculate overall skill rating
        skill_rating = sum(attributes.values()) // len(attributes)
        
        # Use canonical style generator — respects generation weights
        # (Wrestler 1.10 → Point Fighter 0.60) and country bias
        # (Brazil→BJJ, Thailand→Muay Thai, Russia→Wrestler, etc.).
        # 5% "unicorn" chance for counter-meta archetypes baked into
        # generate_style_for_fighter itself.
        try:
            if generate_style_for_fighter is not None:
                _style_result = generate_style_for_fighter(
                    country=country or '',
                    camp_styles=None,
                )
                style = (_style_result.value
                         if hasattr(_style_result, 'value')
                         else str(_style_result))
            else:
                raise ImportError("generate_style_for_fighter unavailable")
        except Exception:
            # Fallback — full canonical 11-style list, flat random
            style = random.choice([
                "Wrestler", "Striker", "Balanced",
                "Pressure Fighter", "Ground & Pound",
                "Muay Thai", "BJJ Specialist",
                "Sprawl & Brawl", "Counter Striker",
                "Clinch Fighter", "Point Fighter"
            ])
        stance = random.choices(self.STANCES, weights=[70, 25, 5], k=1)[0]
        
        # Calculate starting popularity based on tier
        popularity = calculate_starting_popularity(skill_tier, amateur_bonus)

        # Potential ceiling — age-weighted grade pick (Elite/High/Average/
        # Limited per game_start.POTENTIAL_GRADES), then random within band.
        # Floored at skill_rating + 3 so the ceiling never lands below
        # current OVR for already-skilled fighters (avoids "you're past
        # your potential" incoherence for elite-tier world-init fighters).
        if age <= 24:
            grade_weights = [10, 20, 40, 30]   # Elite, High, Average, Limited
        elif age <= 27:
            grade_weights = [5, 20, 45, 30]
        else:
            grade_weights = [0, 10, 50, 40]    # No Elite for older
        grade_bands = [(90, 97), (79, 87), (68, 77), (55, 66)]
        ceil_min, ceil_max = random.choices(grade_bands, weights=grade_weights, k=1)[0]
        potential_ceiling = max(random.randint(ceil_min, ceil_max),
                                 skill_rating + 3)
        potential_ceiling = min(99, potential_ceiling)

        return GeneratedFighter(
            fighter_id=str(uuid.uuid4())[:8],
            name=name,
            country=country,
            weight_class=weight_class,
            age=age,
            height=height,
            reach=reach,
            weight=round(weight, 1),
            attributes=attributes,
            style=style,
            stance=stance,
            skill_rating=skill_rating,
            skill_tier=skill_tier,
            potential_ceiling=potential_ceiling,
            popularity=popularity,
        )


# ============================================================================
# CAMP GENERATOR
# ============================================================================

class CampGenerator:
    """Generates AI training camps"""
    
    TIER_DISTRIBUTION = {
        "GARAGE": 20,
        "LOCAL": 35,
        "REGIONAL": 25,
        "NATIONAL": 15,
        "ELITE": 5,
    }
    
    TIER_STATS = {
        "GARAGE": {"reputation": (10, 30), "balance": (5000, 20000), "fighters": (1, 3)},
        "LOCAL": {"reputation": (20, 45), "balance": (15000, 50000), "fighters": (2, 5)},
        "REGIONAL": {"reputation": (40, 65), "balance": (40000, 150000), "fighters": (4, 7)},
        "NATIONAL": {"reputation": (60, 85), "balance": (100000, 500000), "fighters": (6, 10)},
        "ELITE": {"reputation": (80, 100), "balance": (300000, 2000000), "fighters": (10, 15)},
    }
    
    # Locations by tier
    LOCATIONS = {
        "ELITE": ["Las Vegas, NV", "Miami, FL", "Los Angeles, CA", "New York, NY", "Albuquerque, NM"],
        "NATIONAL": ["Denver, CO", "San Diego, CA", "Dallas, TX", "Chicago, IL", "Phoenix, AZ", "Sacramento, CA"],
        "REGIONAL": ["Portland, OR", "Seattle, WA", "Austin, TX", "Atlanta, GA", "Boston, MA", "Philadelphia, PA"],
        "LOCAL": ["Fresno, CA", "Tulsa, OK", "Milwaukee, WI", "Omaha, NE", "Boise, ID", "Salt Lake City, UT"],
        "GARAGE": ["Bakersfield, CA", "Stockton, CA", "Lubbock, TX", "Fargo, ND", "Reno, NV", "Tucson, AZ"],
    }
    
    def __init__(self):
        self.used_names: set = set()
    
    def generate_name(self) -> str:
        """Generate a unique camp name"""
        for _ in range(100):
            prefix = random.choice(CAMP_PREFIXES)
            suffix = random.choice(CAMP_SUFFIXES)
            name = f"{prefix} {suffix}"
            
            if name not in self.used_names:
                self.used_names.add(name)
                return name
        
        # Fallback
        return f"Fight Team {random.randint(100, 999)}"
    
    def generate_camp(self, tier: Optional[str] = None) -> GeneratedCamp:
        """Generate a training camp"""
        
        if not tier:
            tiers = list(self.TIER_DISTRIBUTION.keys())
            weights = list(self.TIER_DISTRIBUTION.values())
            tier = random.choices(tiers, weights=weights, k=1)[0]
        
        stats = self.TIER_STATS[tier]
        
        return GeneratedCamp(
            camp_id=str(uuid.uuid4())[:8],
            name=self.generate_name(),
            location=random.choice(self.LOCATIONS[tier]),
            tier=tier,
            reputation=random.randint(*stats["reputation"]),
            balance=random.randint(*stats["balance"]),
        )


# ============================================================================
# HISTORY SIMULATOR (Event-Based)
# ============================================================================

class HistorySimulator:
    """
    Simulates years of fight history with ACTUAL EVENTS.
    
    Creates DFC 1, DFC 2, etc. with proper card structure.
    Each event has Main Event, Co-Main, Main Card, Prelims, Early Prelims.
    
    Fight history is saved to each fighter for viewing in their profile.
    """
    
    # Fallback finish rates if simple simulation is used
    FINISH_METHODS = {
        "KO": 18,
        "TKO": 22,
        "SUB": 20,
        "DEC": 35,
        "SPLIT": 5,
    }
    
    # Events per week (UFC averages about 1 per week)
    EVENTS_PER_WEEK = 1
    FIGHTS_PER_EVENT = (10, 14)  # Min, max fights per card
    
    def __init__(
        self,
        fighters: Dict[str, GeneratedFighter],
        use_full_engine: bool = True,
        camps: Optional[Dict[str, "GeneratedCamp"]] = None,
        fighter_gen: Optional["FighterGenerator"] = None,
    ):
        """
        Initialize history simulator.

        Args:
            fighters: Dictionary of generated fighters
            use_full_engine: If True, use full fight engine for realistic results
            camps: Optional camps dict (enables prospect camp placement during sim)
            fighter_gen: Optional FighterGenerator (enables prospect spawning during sim)
        """
        self.fighters = fighters
        self.camps = camps or {}
        self.fighter_gen = fighter_gen
        self.fight_history: List[SimulatedFight] = []
        self.events: List[SimulatedEvent] = []
        self.title_holders: Dict[str, str] = {}  # weight_class -> fighter_id
        self.use_full_engine = use_full_engine and FULL_ENGINE_AVAILABLE

        # Belt history tracking
        self.belt_history = BeltHistory()

        # Track event numbering
        self.next_event_number = 1

        # Track fighter cooldowns (weeks since last fight)
        self.fighter_last_fight: Dict[str, int] = {}  # fighter_id -> week_number

        # Rankings cache
        self.division_rankings: Dict[str, List[Tuple[str, int]]] = {}  # wc -> [(fighter_id, rank)]

        # Aging-during-sim
        self.aging_system: Optional[AgingSystem] = AgingSystem() if AGING_AVAILABLE else None
        self.vacant_divisions: Set[str] = set()
        self.retirement_count: int = 0
        self.replacement_count: int = 0
        self.champion_retirement_count: int = 0

        # Rivalry-during-sim (Ship #25)
        self.rivalry_seeded_count: int = 0
        self.rivalry_failed_count: int = 0
    
    def crown_initial_champions(self) -> None:
        """
        Crown inaugural champions for each division.
        
        Selects the highest-rated fighter in each division as the starting champion.
        This should be called before simulating fight history.
        """
        for weight_class in WEIGHT_CLASSES:
            # Get all fighters in this division
            division_fighters = [
                f for f in self.fighters.values() 
                if f.weight_class == weight_class
            ]
            
            if not division_fighters:
                continue
            
            # Sort by skill rating (highest first)
            division_fighters.sort(key=lambda f: (f.skill_rating, f.popularity), reverse=True)
            
            # Crown the best fighter as inaugural champion
            champion = division_fighters[0]
            champion.is_champion = True
            champion.ranking = 0
            
            # Track in title_holders
            self.title_holders[weight_class] = champion.fighter_id
            
            # Record in belt history. Event name slots into DFC
            # universe; won_method keeps "Inaugural" substring so
            # champions.html:96 branch detects inaugural reigns.
            _founding_event = f"DFC Founding — {weight_class} Championship"
            self.belt_history.crown_initial_champion(
                fighter_id=champion.fighter_id,
                fighter_name=champion.name,
                weight_class=weight_class,
                week=0,
                event_name=_founding_event,
                won_method="Inaugural Crown",
            )

            # Synthetic fight_history entry — the inaugural crowning
            # was previously metadata-only on the BeltReign and never
            # appeared on the champion's personal timeline. Adds a
            # tombstone-style record so the profile shows the moment.
            champion.fight_history.append({
                "event_name":     _founding_event,
                "event_number":   0,
                "opponent_id":    None,
                "opponent_name":  "—",
                "result":         "W",
                "method":         "Inaugural Crown",
                "round":          None,
                "was_title_fight": True,
                "weight_class":   weight_class,
                "week":           0,
            })

            # Give champion a popularity boost
            champion.popularity = min(100, champion.popularity + random.randint(15, 25))
    
    def _fighter_to_attributes(self, fighter: GeneratedFighter) -> Optional[Any]:
        """Convert GeneratedFighter to FighterAttributes for full engine"""
        if not FULL_ENGINE_AVAILABLE:
            return None
        
        try:
            # Create FighterAttributes from generated fighter stats
            attrs = FighterAttributes(
                fighter_id=fighter.fighter_id,
                name=fighter.name,
                # Use skill_rating to derive attributes
                boxing=fighter.attributes.get("boxing", fighter.skill_rating),
                kicks=fighter.attributes.get("kicks", fighter.skill_rating - 5),
                wrestling=fighter.attributes.get("wrestling", fighter.skill_rating),
                bjj=fighter.attributes.get("bjj", fighter.skill_rating - 5),
                clinch=fighter.attributes.get("clinch", fighter.skill_rating - 5),
                cardio=fighter.attributes.get("cardio", 70),
                strength=fighter.attributes.get("strength", 65),
                speed=fighter.attributes.get("speed", 65),
                chin=fighter.attributes.get("chin", 70),
                recovery=fighter.attributes.get("recovery", 65),
                striking_defense=fighter.attributes.get("striking_defense", fighter.skill_rating - 5),
                takedown_defense=fighter.attributes.get("takedown_defense", fighter.skill_rating - 5),
                submission_defense=fighter.attributes.get("submission_defense", fighter.skill_rating - 10),
                fight_iq=fighter.attributes.get("fight_iq", 60),
                composure=fighter.attributes.get("composure", 60),
            )
            return attrs
        except Exception:
            return None
    
    def simulate_fight_full_engine(
        self, 
        fighter1_id: str, 
        fighter2_id: str, 
        is_title_fight: bool = False
    ) -> Tuple[Optional[str], Optional[str], str, int]:
        """
        Simulate fight using full engine (no commentary generation).
        
        Returns: (winner_id, loser_id, method, round_ended) or (None, None, "", 0) on error
        """
        if not FULL_ENGINE_AVAILABLE:
            return None, None, "", 0
        
        f1 = self.fighters[fighter1_id]
        f2 = self.fighters[fighter2_id]
        
        f1_attrs = self._fighter_to_attributes(f1)
        f2_attrs = self._fighter_to_attributes(f2)
        
        if not f1_attrs or not f2_attrs:
            return None, None, "", 0
        
        try:
            # Configure fight (no commentary needed for history)
            config = FightConfig.championship_fight() if is_title_fight else FightConfig.standard_fight()
            
            # Run simulation
            result = engine_simulate_fight(f1_attrs, f2_attrs, config)
            
            # Extract method
            method = result.method
            if "KO" in method and "TKO" not in method:
                method = "KO"
            elif "TKO" in method:
                method = "TKO"
            elif "Submission" in method:
                method = "SUB"
            elif "Decision" in method:
                if "Split" in method:
                    method = "SPLIT"
                else:
                    method = "DEC"
            elif method == "Draw":
                method = "DRAW"
            else:
                method = "DEC"
            
            # Determine winner/loser
            if result.winner_id == fighter1_id:
                winner_id, loser_id = fighter1_id, fighter2_id
            else:
                winner_id, loser_id = fighter2_id, fighter1_id
            
            round_ended = result.finish_round if result.finish_round else 3
            
            return winner_id, loser_id, method, round_ended
            
        except Exception:
            return None, None, "", 0
    
    def simulate_fight_simple(
        self, 
        fighter1_id: str, 
        fighter2_id: str
    ) -> Tuple[str, str, str, int]:
        """Simple probability-based fight simulation (fast fallback)"""
        
        f1 = self.fighters[fighter1_id]
        f2 = self.fighters[fighter2_id]
        
        # Calculate win probability based on skill ratings
        skill_diff = f1.skill_rating - f2.skill_rating
        f1_win_prob = 0.5 + (skill_diff / 100)
        f1_win_prob = max(0.2, min(0.8, f1_win_prob))
        
        # Add some randomness for upsets
        if random.random() < 0.1:
            f1_win_prob = 1 - f1_win_prob
        
        # Determine winner
        if random.random() < f1_win_prob:
            winner_id, loser_id = fighter1_id, fighter2_id
        else:
            winner_id, loser_id = fighter2_id, fighter1_id
        
        # Determine method
        methods = list(self.FINISH_METHODS.keys())
        weights = list(self.FINISH_METHODS.values())
        method = random.choices(methods, weights=weights, k=1)[0]
        
        # Round ended
        if method in ("KO", "TKO", "SUB"):
            round_ended = random.choices([1, 2, 3], weights=[30, 40, 30], k=1)[0]
        else:
            round_ended = 3
        
        return winner_id, loser_id, method, round_ended
    
    def _simulate_single_fight(
        self, 
        fighter1_id: str, 
        fighter2_id: str, 
        is_title_fight: bool,
        event_name: str,
        event_number: int,
        card_slot: str,
        current_week: int,
    ) -> SimulatedFight:
        """
        Simulate a single fight and update all records.
        
        Returns the SimulatedFight record.
        """
        f1 = self.fighters[fighter1_id]
        f2 = self.fighters[fighter2_id]
        
        # Try full engine first
        winner_id, loser_id, method, round_ended = None, None, "", 0
        if self.use_full_engine:
            winner_id, loser_id, method, round_ended = self.simulate_fight_full_engine(
                fighter1_id, fighter2_id, is_title_fight
            )
        
        # Fall back to simple if needed
        if not winner_id:
            winner_id, loser_id, method, round_ended = self.simulate_fight_simple(
                fighter1_id, fighter2_id
            )
        
        winner = self.fighters[winner_id]
        loser = self.fighters[loser_id]
        
        # Update records
        winner.wins += 1
        loser.losses += 1
        
        # Track finish types
        if method in ("KO", "TKO"):
            winner.ko_wins += 1
        elif method == "SUB":
            winner.sub_wins += 1
        
        # Update streaks
        winner.current_win_streak += 1
        winner.current_loss_streak = 0
        loser.current_win_streak = 0
        loser.current_loss_streak += 1

        # Post-fight retirement check (lose-streak ≥3 triggers a roll)
        self._maybe_retire_post_fight(loser, current_week, event_name)

        # Handle title
        was_title_defense = False
        if is_title_fight:
            weight_class = winner.weight_class
            old_champion_id = self.title_holders.get(weight_class)
            
            if old_champion_id == loser.fighter_id:
                # Title changes hands!
                loser.is_champion = False
                winner.is_champion = True
                self.title_holders[weight_class] = winner.fighter_id
                
                # Record in belt history
                self.belt_history.title_changes_hands(
                    new_champion_id=winner.fighter_id,
                    new_champion_name=winner.name,
                    old_champion_id=loser.fighter_id,
                    old_champion_name=loser.name,
                    weight_class=weight_class,
                    week=current_week,
                    event_name=event_name,
                    method=method,
                )
            elif old_champion_id == winner.fighter_id:
                # Successful title defense
                was_title_defense = True
                self.belt_history.record_title_defense(weight_class)
            else:
                # Vacant-title fight (no current champion): winner claims the vacated belt.
                # Records into belt_history with a distinguishing won_method.
                winner.is_champion = True
                self.title_holders[weight_class] = winner.fighter_id
                self.belt_history.crown_initial_champion(
                    fighter_id=winner.fighter_id,
                    fighter_name=winner.name,
                    weight_class=weight_class,
                    week=current_week,
                    event_name=event_name,
                    won_method=f"Won Vacant Title ({method})",
                )
        
        # Update popularity
        winner_pop_change = calculate_popularity_change(
            won=True,
            method=method,
            was_title_fight=is_title_fight,
            was_title_defense=was_title_defense,
            win_streak=winner.current_win_streak,
            loss_streak=0,
            current_popularity=winner.popularity,
        )
        loser_pop_change = calculate_popularity_change(
            won=False,
            method=method,
            was_title_fight=is_title_fight,
            was_title_defense=False,
            win_streak=0,
            loss_streak=loser.current_loss_streak,
            current_popularity=loser.popularity,
        )
        
        winner.popularity = max(0, min(100, winner.popularity + winner_pop_change))
        loser.popularity = max(0, min(100, loser.popularity + loser_pop_change))
        
        # Update last fight week
        winner.last_fight_week = current_week
        loser.last_fight_week = current_week
        self.fighter_last_fight[winner_id] = current_week
        self.fighter_last_fight[loser_id] = current_week

        # Sim-seed rivalry: feed every sim fight through the rivalry system
        # so repeat matchups build heat retroactively. Persistence wired in
        # Ship #24; sim-built rivalries survive into player runtime via the
        # bridge save/load path. Per-fight try/except so a rivalry bookkeeping
        # issue can't crash world-gen.
        if RIVALRY_AVAILABLE:
            try:
                _is_main_event = (card_slot == "main_event")
                _total_rounds = 5 if (is_title_fight or _is_main_event) else 3
                ctx = FightContext(
                    fight_id=f"sim_{event_name}_{winner_id}",
                    fighter1_id=winner.fighter_id,
                    fighter2_id=loser.fighter_id,
                    fighter1_name=winner.name,
                    fighter2_name=loser.name,
                    winner_id=winner.fighter_id,
                    method=method,
                    is_title_fight=is_title_fight,
                    is_main_event=_is_main_event,
                    round_ended=round_ended,
                    total_rounds=_total_rounds,
                    was_close=(method == "SPLIT"),
                    was_controversial=False,
                )
                get_rivalry_system().process_fight(ctx)
                self.rivalry_seeded_count += 1
            except Exception:
                self.rivalry_failed_count += 1

        # Create fight record
        fight = SimulatedFight(
            winner_id=winner_id,
            loser_id=loser_id,
            winner_name=winner.name,
            loser_name=loser.name,
            method=method,
            round_ended=round_ended,
            was_title_fight=is_title_fight,
            event_name=event_name,
            event_number=event_number,
            card_slot=card_slot,
            weight_class=winner.weight_class,
        )
        
        # Add to fight history
        self.fight_history.append(fight)
        
        # Add to fighter's personal history
        fight_record_winner = {
            "event_name": event_name,
            "event_number": event_number,
            "opponent_id": loser_id,
            "opponent_name": loser.name,
            "result": "W",
            "method": method,
            "round": round_ended,
            "was_title_fight": is_title_fight,
            "weight_class": winner.weight_class,
            "week": current_week,
        }
        fight_record_loser = {
            "event_name": event_name,
            "event_number": event_number,
            "opponent_id": winner_id,
            "opponent_name": winner.name,
            "result": "L",
            "method": method,
            "round": round_ended,
            "was_title_fight": is_title_fight,
            "weight_class": loser.weight_class,
            "week": current_week,
        }
        
        winner.fight_history.append(fight_record_winner)
        loser.fight_history.append(fight_record_loser)
        
        return fight
    
    def _get_fighter_rank(self, fighter_id: str, weight_class: str) -> Optional[int]:
        """Get fighter's current rank in their division"""
        ranked_list = self.division_rankings.get(weight_class, [])
        for fid, rank in ranked_list:
            if fid == fighter_id:
                return rank
        return None
    
    def _is_fighter_available(self, fighter_id: str, current_week: int, booked_this_week: Set[str]) -> bool:
        """Check if fighter is available for booking"""
        fighter = self.fighters.get(fighter_id)
        if fighter is None or not fighter.is_active:
            return False

        if fighter_id in booked_this_week:
            return False

        # Cooldown check (minimum 4 weeks between fights)
        last_fight = self.fighter_last_fight.get(fighter_id, -10)
        if current_week - last_fight < 4:
            return False

        return True
    
    def update_rankings(self):
        """Recalculate rankings based on current records."""
        for weight_class in WEIGHT_CLASSES:
            division_fighters = [
                f for f in self.fighters.values()
                if f.weight_class == weight_class and f.is_active
            ]
            
            # Sort by: champion first, then win percentage, then total wins, then popularity
            def rank_key(f: GeneratedFighter):
                total_fights = f.wins + f.losses
                win_pct = f.wins / total_fights if total_fights > 0 else 0
                return (f.is_champion, win_pct, f.wins, f.popularity, f.skill_rating)
            
            sorted_fighters = sorted(division_fighters, key=rank_key, reverse=True)
            
            # Build ranked list (excluding champion)
            ranked = []
            rank = 0
            for fighter in sorted_fighters:
                if fighter.is_champion:
                    fighter.ranking = 0
                    continue
                rank += 1
                fighter.ranking = rank
                if rank <= 15:
                    ranked.append((fighter.fighter_id, rank))
            
            self.division_rankings[weight_class] = ranked
    
    def _get_opponent_rank_range(self, rank: int) -> Tuple[int, int, float]:
        """Get realistic opponent rank range based on UFC patterns.
        
        Returns: (min_rank, max_rank, unranked_chance)
        """
        if rank <= 0:
            return (11, 15, 0.70)  # Unranked
        elif rank <= 3:
            return (1, 6, 0.05)    # Top 3 fight other top 5
        elif rank <= 5:
            return (2, 8, 0.05)    # #4-5 fight top 8
        elif rank <= 7:
            return (4, 10, 0.10)   # #6-7 fight #4-10
        elif rank <= 10:
            return (5, 13, 0.15)   # #8-10 fight #5-13
        elif rank <= 12:
            return (8, 15, 0.30)   # #11-12 fight #8-15
        else:
            return (10, 15, 0.40)  # #13-15 frequently fight unranked
    
    def _find_opponent(
        self, 
        fighter: GeneratedFighter, 
        available_fighters: List[GeneratedFighter],
        booked_this_week: Set[str],
        current_week: int,
    ) -> Optional[GeneratedFighter]:
        """Find appropriate opponent using UFC-style matchmaking with popularity consideration"""
        
        fighter_rank = self._get_fighter_rank(fighter.fighter_id, fighter.weight_class) or 0
        ranked_list = self.division_rankings.get(fighter.weight_class, [])
        ranked_ids = {fid for fid, _ in ranked_list}
        
        # Champion logic
        if fighter.is_champion:
            # Champions fight top 5 contenders
            candidates = []
            for fid, rank in ranked_list[:5]:
                opp = self.fighters.get(fid)
                if opp and self._is_fighter_available(fid, current_week, booked_this_week):
                    candidates.append(opp)
            if candidates:
                # Prefer higher ranked opponents
                return random.choice(candidates[:3]) if len(candidates) >= 3 else random.choice(candidates)
        
        min_rank, max_rank, unranked_chance = self._get_opponent_rank_range(fighter_rank)
        
        # Build candidate pools
        ranked_candidates = []
        unranked_candidates = []
        
        for opp in available_fighters:
            if opp.fighter_id == fighter.fighter_id:
                continue
            if opp.is_champion:
                continue
            if not self._is_fighter_available(opp.fighter_id, current_week, booked_this_week):
                continue
            if opp.camp_id and fighter.camp_id and opp.camp_id == fighter.camp_id:
                continue  # Same camp
            
            opp_rank = self._get_fighter_rank(opp.fighter_id, opp.weight_class) or 0
            
            if opp_rank > 0:
                if min_rank <= opp_rank <= max_rank:
                    # Weight by rank proximity and popularity
                    rank_diff = abs(fighter_rank - opp_rank) if fighter_rank > 0 else opp_rank
                    weight = max(1, 10 - rank_diff) + (opp.popularity // 20)
                    ranked_candidates.append((opp, weight))
            else:
                unranked_candidates.append(opp)
        
        # Decide: fight unranked or ranked?
        if fighter_rank == 0 or fighter_rank > 15:
            # Unranked fighter - mostly fight unranked
            if unranked_candidates and random.random() < 0.70:
                # Prefer opponents with similar skill/popularity
                unranked_candidates.sort(key=lambda x: abs(x.skill_rating - fighter.skill_rating))
                return random.choice(unranked_candidates[:5]) if len(unranked_candidates) >= 5 else random.choice(unranked_candidates)
            elif ranked_candidates:
                lower_ranked = [(o, w) for o, w in ranked_candidates if (self._get_fighter_rank(o.fighter_id, o.weight_class) or 99) >= 11]
                if lower_ranked:
                    opps, weights = zip(*lower_ranked)
                    return random.choices(opps, weights=weights)[0]
        else:
            # Ranked fighter
            if random.random() < unranked_chance and unranked_candidates:
                return random.choice(unranked_candidates)
            elif ranked_candidates:
                opps, weights = zip(*ranked_candidates)
                return random.choices(opps, weights=weights)[0]
        
        # Fallback
        if unranked_candidates:
            return random.choice(unranked_candidates)
        if ranked_candidates:
            return ranked_candidates[0][0]
        
        return None
    
    def _build_event_card(self, week: int, booked_fighters: Set[str]) -> SimulatedEvent:
        """
        Build a complete event card for a given week.
        
        UFC-style structure:
        - Main Event (1): Title fight or high star power
        - Co-Main (1): Top ranked bout
        - Main Card (3-4): Ranked fights
        - Prelims (4-5): Mix of ranked/unranked
        - Early Prelims (3-4): Unranked prospects
        """
        event_number = self.next_event_number
        self.next_event_number += 1
        event_name = f"DFC {event_number}"
        
        event = SimulatedEvent(
            event_number=event_number,
            event_name=event_name,
            week_number=week,
        )
        
        fights_this_card: List[SimulatedFight] = []
        booked_this_card: Set[str] = set()
        
        def book_fighter(fid: str):
            booked_this_card.add(fid)
            booked_fighters.add(fid)
        
        def all_booked() -> Set[str]:
            return booked_fighters | booked_this_card
        
        def is_available(fid: str) -> bool:
            return self._is_fighter_available(fid, week, all_booked())
        
        def get_available_in_division(wc: str) -> List[GeneratedFighter]:
            """Get all available fighters in a weight class"""
            return [
                f for f in self.fighters.values()
                if f.weight_class == wc and is_available(f.fighter_id)
            ]
        
        def make_fight(f1_id: str, f2_id: str, is_title: bool, card_slot: str) -> Optional[SimulatedFight]:
            """Helper to create a fight with correct signature"""
            if not is_available(f1_id) or not is_available(f2_id):
                return None
            if f1_id == f2_id:
                return None
            try:
                fight = self._simulate_single_fight(
                    fighter1_id=f1_id,
                    fighter2_id=f2_id,
                    is_title_fight=is_title,
                    event_name=event_name,
                    event_number=event_number,
                    card_slot=card_slot,
                    current_week=week,
                )
                return fight
            except Exception:
                return None
        
        def find_opponent_for(fighter: GeneratedFighter) -> Optional[GeneratedFighter]:
            """Find opponent using the correct signature"""
            available = get_available_in_division(fighter.weight_class)
            return self._find_opponent(fighter, available, all_booked(), week)
        
        # Shuffle weight classes for variety
        divisions = list(WEIGHT_CLASSES)
        random.shuffle(divisions)
        
        # === MAIN EVENT ===
        main_event_fight = None

        # First priority: Vacant-title fight (champion retired or otherwise vacated)
        for wc in list(self.vacant_divisions):
            if main_event_fight:
                break
            rankings = self.division_rankings.get(wc, [])
            top_contenders = [fid for fid, _ in rankings[:5] if is_available(fid)]
            if len(top_contenders) >= 2:
                f1_id, f2_id = top_contenders[0], top_contenders[1]
                fight = make_fight(f1_id, f2_id, True, "main_event")
                if fight:
                    main_event_fight = fight
                    book_fighter(f1_id)
                    book_fighter(f2_id)
                    # Vacant belt is now claimed; clear from set
                    self.vacant_divisions.discard(wc)

        # Second try: Title fight
        for wc in divisions:
            if main_event_fight:
                break
            champion_id = self.title_holders.get(wc)
            if not champion_id or not is_available(champion_id):
                continue
            # Find top contender
            rankings = self.division_rankings.get(wc, [])
            for contender_id, _ in rankings[:5]:
                if contender_id != champion_id and is_available(contender_id):
                    fight = make_fight(champion_id, contender_id, True, "main_event")
                    if fight:
                        main_event_fight = fight
                        book_fighter(champion_id)
                        book_fighter(contender_id)
                        break
        
        # Second try: Top ranked matchup
        if not main_event_fight:
            for wc in divisions:
                if main_event_fight:
                    break
                rankings = self.division_rankings.get(wc, [])
                for i, (f1_id, _) in enumerate(rankings[:3]):
                    if main_event_fight:
                        break
                    if not is_available(f1_id):
                        continue
                    for f2_id, _ in rankings[i+1:6]:
                        if is_available(f2_id):
                            fight = make_fight(f1_id, f2_id, False, "main_event")
                            if fight:
                                main_event_fight = fight
                                book_fighter(f1_id)
                                book_fighter(f2_id)
                                break
        
        if main_event_fight:
            event.main_event = main_event_fight
            fights_this_card.append(main_event_fight)
        
        # === CO-MAIN ===
        co_main_fight = None
        for wc in divisions:
            if co_main_fight:
                break
            rankings = self.division_rankings.get(wc, [])
            for f1_id, _ in rankings[:8]:
                if co_main_fight:
                    break
                if not is_available(f1_id):
                    continue
                f1 = self.fighters.get(f1_id)
                if not f1:
                    continue
                opponent = find_opponent_for(f1)
                if opponent and is_available(opponent.fighter_id):
                    fight = make_fight(f1_id, opponent.fighter_id, False, "co_main")
                    if fight:
                        co_main_fight = fight
                        book_fighter(f1_id)
                        book_fighter(opponent.fighter_id)
        
        if co_main_fight:
            event.co_main = co_main_fight
            fights_this_card.append(co_main_fight)
        
        # === MAIN CARD (3-4 fights) ===
        main_card_target = random.randint(3, 4)
        for wc in divisions:
            if len(event.main_card) >= main_card_target:
                break
            rankings = self.division_rankings.get(wc, [])
            for f1_id, _ in rankings[5:15]:
                if len(event.main_card) >= main_card_target:
                    break
                if not is_available(f1_id):
                    continue
                f1 = self.fighters.get(f1_id)
                if not f1:
                    continue
                opponent = find_opponent_for(f1)
                if opponent and is_available(opponent.fighter_id):
                    fight = make_fight(f1_id, opponent.fighter_id, False, "main_card")
                    if fight:
                        event.main_card.append(fight)
                        fights_this_card.append(fight)
                        book_fighter(f1_id)
                        book_fighter(opponent.fighter_id)
        
        # === PRELIMS (4-5 fights) ===
        prelims_target = random.randint(4, 5)
        for wc in divisions:
            if len(event.prelims) >= prelims_target:
                break
            candidates = get_available_in_division(wc)
            random.shuffle(candidates)
            for f1 in candidates[:10]:
                if len(event.prelims) >= prelims_target:
                    break
                if not is_available(f1.fighter_id):
                    continue
                opponent = find_opponent_for(f1)
                if opponent and is_available(opponent.fighter_id):
                    fight = make_fight(f1.fighter_id, opponent.fighter_id, False, "prelims")
                    if fight:
                        event.prelims.append(fight)
                        fights_this_card.append(fight)
                        book_fighter(f1.fighter_id)
                        book_fighter(opponent.fighter_id)
        
        # === EARLY PRELIMS (3-4 fights) ===
        early_target = random.randint(3, 4)
        for wc in divisions:
            if len(event.early_prelims) >= early_target:
                break
            # Prefer unranked
            unranked = [
                f for f in self.fighters.values()
                if f.weight_class == wc 
                and is_available(f.fighter_id)
                and self._get_fighter_rank(f.fighter_id, wc) is None
            ]
            random.shuffle(unranked)
            for f1 in unranked[:8]:
                if len(event.early_prelims) >= early_target:
                    break
                if not is_available(f1.fighter_id):
                    continue
                opponent = find_opponent_for(f1)
                if opponent and is_available(opponent.fighter_id):
                    fight = make_fight(f1.fighter_id, opponent.fighter_id, False, "early_prelims")
                    if fight:
                        event.early_prelims.append(fight)
                        fights_this_card.append(fight)
                        book_fighter(f1.fighter_id)
                        book_fighter(opponent.fighter_id)
        
        # Add all fights to history
        self.fight_history.extend(fights_this_card)
        
        return event
    
    def simulate_history(self, weeks: int = 120):
        """
        Simulate several years of fight history with real events.
        
        Creates DFC 1 through DFC ~105 (about 1 event per week).
        
        Args:
            weeks: Number of weeks to simulate (120 = ~2.3 years)
        """
        print(f"  Simulating {weeks} weeks of history with real events...")
        
        # Crown initial champions before starting
        self.crown_initial_champions()
        print(f"    Crowned {len(self.title_holders)} inaugural champions")
        
        # Initialize rankings
        self.update_rankings()
        
        # Track fighters who fought recently (for cooldown)
        booked_this_period: Set[str] = set()
        
        for week in range(1, weeks + 1):
            # Annual aging tick (every 52 weeks): age all active fighters,
            # apply attribute decline, roll annual retirement, spawn replacements.
            if week % 52 == 0:
                self._process_annual_aging(year=week // 52, current_week=week)

            # Update rankings periodically (every 4 weeks)
            if week % 4 == 0:
                self.update_rankings()

            # Clear period cooldowns periodically
            if week % 2 == 0:
                booked_this_period.clear()

            # Build event card for this week
            event = self._build_event_card(week, booked_this_period)
            self.events.append(event)

            # Progress indicator
            if week % 20 == 0:
                title_fights = sum(1 for e in self.events if e.main_event and e.main_event.was_title_fight)
                print(f"    Week {week}/{weeks} - DFC {event.event_number} ({event.total_fights} fights, {title_fights} title fights so far)")

        # Final ranking update
        self.update_rankings()

        # Summary
        title_fights = sum(1 for f in self.fight_history if f.was_title_fight)
        title_changes = sum(
            len([r for r in reigns if r.won_from is not None])
            for reigns in self.belt_history.reigns.values()
        )
        print(f"  Created {len(self.events)} events (DFC 1 - DFC {self.next_event_number - 1})")
        print(f"  Total fights: {len(self.fight_history)} | Title fights: {title_fights} | Title changes: {title_changes}")
        print(f"  Aging: {self.retirement_count} retirements ({self.champion_retirement_count} champions) | {self.replacement_count} replacement prospects")
        print(f"  Rivalries seeded: {self.rivalry_seeded_count}" +
              (f" ({self.rivalry_failed_count} failed)" if self.rivalry_failed_count else ""))
    
    # ========================================================================
    # AGING-DURING-SIM
    # ========================================================================

    def _process_annual_aging(self, year: int, current_week: int) -> None:
        """
        Annual tick: age every active fighter by 1 year, apply attribute
        decline, roll annual retirement probability. After retirements,
        spawn replacement prospects 1:1 same-division (Lock 3).
        """
        if not self.aging_system:
            return

        retired_by_division: Dict[str, int] = {}

        for fighter in list(self.fighters.values()):
            if not fighter.is_active:
                continue

            # Age the fighter
            fighter.age += 1

            # Apply attribute decline (returns dict of negative deltas)
            ko_losses = sum(
                1 for fr in fighter.fight_history
                if fr.get("result") == "L" and fr.get("method") in ("KO", "TKO")
            )
            try:
                changes = self.aging_system.apply_annual_decline(
                    fighter_id=fighter.fighter_id,
                    age=fighter.age,
                    current_attributes=fighter.attributes,
                    ko_losses=ko_losses,
                )
            except Exception as e:
                print(f"  [AGING] apply_annual_decline failed for {fighter.name} age {fighter.age}: {e}")
                changes = {}
            for attr, delta in changes.items():
                if attr in fighter.attributes:
                    fighter.attributes[attr] = max(1, fighter.attributes[attr] + delta)
            # Recompute skill_rating from updated attributes
            if fighter.attributes:
                fighter.skill_rating = sum(fighter.attributes.values()) // len(fighter.attributes)

            # Annual retirement roll
            prob = calculate_retirement_probability(
                age=fighter.age,
                current_lose_streak=fighter.current_loss_streak,
                is_champion=fighter.is_champion,
                total_fights=fighter.wins + fighter.losses + fighter.draws,
                morale=50,
            )

            if prob > 0 and random.random() < prob:
                self._retire_fighter(fighter, current_week, reason="Annual age check")
                retired_by_division[fighter.weight_class] = retired_by_division.get(fighter.weight_class, 0) + 1

        # Spawn replacement prospects 1:1 same-division (Lock 3)
        for wc, count in retired_by_division.items():
            for _ in range(count):
                self._spawn_replacement_prospect(wc)

        # Refresh rankings after aging tick (retired fighters drop out)
        self.update_rankings()

    def _maybe_retire_post_fight(self, loser: GeneratedFighter, current_week: int, event_name: str) -> None:
        """Post-fight retirement check: only fires when lose-streak ≥3 (Lock 1)."""
        if not self.aging_system:
            return
        if loser.current_loss_streak < 3:
            return
        if not loser.is_active:
            return

        prob = calculate_retirement_probability(
            age=loser.age,
            current_lose_streak=loser.current_loss_streak,
            is_champion=loser.is_champion,
            total_fights=loser.wins + loser.losses + loser.draws,
            morale=50,
        )

        if prob > 0 and random.random() < prob:
            self._retire_fighter(loser, current_week, reason=f"Post-fight ({event_name})")
            # Spawn 1:1 replacement immediately
            self._spawn_replacement_prospect(loser.weight_class)

    def _retire_fighter(self, fighter: GeneratedFighter, current_week: int, reason: str) -> None:
        """Mark a fighter retired. If champion, vacate the belt and queue a vacant-title fight."""
        fighter.is_active = False
        fighter.retirement_age = fighter.age
        fighter.retirement_week = current_week
        self.retirement_count += 1

        if fighter.is_champion:
            self.champion_retirement_count += 1
            wc = fighter.weight_class
            fighter.is_champion = False
            self.title_holders.pop(wc, None)
            # Belt vacates; next event card prioritizes top-2 vacant-title fight.
            self.belt_history.vacate_belt(
                weight_class=wc,
                week=current_week,
                event_name=reason,
                reason="Retired",
            )
            self.vacant_divisions.add(wc)

    def _spawn_replacement_prospect(self, weight_class: str) -> None:
        """Spawn a developing prospect into the same division and place into a camp if possible."""
        if not self.fighter_gen:
            return
        try:
            prospect = self.fighter_gen.generate_fighter(
                weight_class=weight_class,
                skill_tier="developing",
                age_range=(21, 25),
            )
        except Exception:
            return

        self.fighters[prospect.fighter_id] = prospect
        self._place_prospect_in_camp(prospect)
        self.replacement_count += 1

    def _place_prospect_in_camp(self, prospect: GeneratedFighter) -> None:
        """
        Lock 4: walk same-division camps with ≥1 fighter in the prospect's
        weight class, filter to those under MAX_PER_DIVISION, pick the
        lowest-count camp. Fall back to camp_id=None (free agent) if all saturated.
        """
        if not self.camps:
            return  # No camp registry available; remains free agent

        MAX_PER_DIVISION = 2
        wc = prospect.weight_class

        # Compute per-camp count of fighters in this division (active only)
        camp_div_counts: Dict[str, int] = {}
        for f in self.fighters.values():
            if f.is_active and f.camp_id and f.weight_class == wc:
                camp_div_counts[f.camp_id] = camp_div_counts.get(f.camp_id, 0) + 1

        # Qualifying = camps that already have ≥1 in this division and are under cap
        qualifying = [
            (cid, count) for cid, count in camp_div_counts.items()
            if count < MAX_PER_DIVISION and cid in self.camps
        ]
        if not qualifying:
            return  # Saturated; remains free agent

        qualifying.sort(key=lambda pair: pair[1])  # Lowest-count first
        chosen_cid = qualifying[0][0]
        prospect.camp_id = chosen_cid
        camp = self.camps.get(chosen_cid)
        if camp is not None:
            camp.fighter_ids.append(prospect.fighter_id)

    def calculate_rankings(self) -> Dict[str, List[str]]:
        """Calculate and return final rankings"""
        self.update_rankings()
        
        rankings: Dict[str, List[str]] = {}
        for wc in WEIGHT_CLASSES:
            ranked_list = self.division_rankings.get(wc, [])
            rankings[wc] = [fid for fid, _ in ranked_list[:15]]
        
        return rankings
    
    def get_next_event_number(self) -> int:
        """Return the next event number for the player's game"""
        return self.next_event_number


# ============================================================================
# WORLD INITIALIZER (Main Class)
# ============================================================================

class WorldInitializer:
    """
    Initializes the game world with fighters, camps, and history.
    
    This is the main entry point for world generation.
    """
    
    def __init__(self, game_state, starting_year: int = 2025, history_weeks: int = 120, bridge=None):
        """
        Initialize the world initializer.

        Args:
            game_state: The GameState object to populate
            starting_year: Year the game starts
            history_weeks: Weeks of history to simulate (120 = ~2.3 years)
            bridge: Optional GameBridge handle (for surfacing sim-time
                state like AI camp equipment back to the bridge).
        """
        self.game_state = game_state
        self._bridge = bridge
        self.starting_year = starting_year
        self.history_weeks = history_weeks
        
        self.fighter_gen = FighterGenerator(starting_year)
        self.camp_gen = CampGenerator()
        
        self.fighters: Dict[str, GeneratedFighter] = {}
        self.camps: Dict[str, GeneratedCamp] = {}
        
        # Store history simulator for event number
        self._history_sim: Optional[HistorySimulator] = None
    
    def generate_fighters(self) -> None:
        """Generate all fighters for the promotion"""
        
        print("Generating fighters...")
        
        for weight_class in WEIGHT_CLASSES:
            min_fighters, max_fighters = FIGHTERS_PER_DIVISION[weight_class]
            num_fighters = random.randint(min_fighters, max_fighters)
            
            for i in range(num_fighters):
                # Vary skill tiers across division
                if i < 3:
                    tier = "elite"
                elif i < 8:
                    tier = "top"
                elif i < 15:
                    tier = "good"
                else:
                    tier = random.choice(["average", "developing"])
                
                # Vary age based on tier
                if tier in ("elite", "top"):
                    age_range = (26, 34)
                elif tier == "good":
                    age_range = (24, 32)
                else:
                    age_range = (21, 30)
                
                fighter = self.fighter_gen.generate_fighter(
                    weight_class=weight_class,
                    skill_tier=tier,
                    age_range=age_range,
                )

                # Body frame — gaussian-distributed size relative to class
                # (1=very small, 10=very large). Drives cut severity and
                # division-move signals.
                _bf = int(random.gauss(5, 1.8))
                _bf = max(1, min(10, _bf))
                fighter.body_frame = _bf

                # Natural weight class: where the fighter belongs without
                # cutting. Frames 1-3: could drop a class. 4-7: native.
                # 8-10: could move up.
                _idx = WEIGHT_CLASSES.index(fighter.weight_class) \
                    if fighter.weight_class in WEIGHT_CLASSES else 4
                if _bf >= 8 and _idx < len(WEIGHT_CLASSES) - 1:
                    fighter.natural_weight_class = WEIGHT_CLASSES[_idx + 1]
                elif _bf <= 3 and _idx > 0:
                    fighter.natural_weight_class = WEIGHT_CLASSES[_idx - 1]
                else:
                    fighter.natural_weight_class = fighter.weight_class

                # Personality — drives challenge acceptance and offer
                # frequency. Distribution: Competitor 35%, Calculated 20%,
                # Hungry 20%, Warrior 15%, Political 10%.
                _personalities = ["Competitor"] * 35 + \
                                 ["Calculated"] * 20 + \
                                 ["Hungry"] * 20 + \
                                 ["Warrior"] * 15 + \
                                 ["Political"] * 10
                fighter.personality = random.choice(_personalities)

                self.fighters[fighter.fighter_id] = fighter
        
        print(f"Generated {len(self.fighters)} fighters")
    
    def generate_camps(self, num_camps: int = 40) -> None:
        """Generate AI training camps with realistic distribution"""
        
        print("Generating camps...")
        
        # More camps, better distribution
        # Target: ~40 camps for ~280 fighters = avg 7 fighters/camp
        tier_counts = {
            "ELITE": 3,      # 3 super-gyms (10-15 fighters each)
            "NATIONAL": 6,   # 6 national gyms (6-10 fighters each)
            "REGIONAL": 10,  # 10 regional gyms (4-7 fighters each)
            "LOCAL": 14,     # 14 local gyms (2-5 fighters each)
            "GARAGE": 7,     # 7 garage gyms (1-3 fighters each)
        }
        
        for tier, count in tier_counts.items():
            for _ in range(count):
                camp = self.camp_gen.generate_camp(tier=tier)
                self.camps[camp.camp_id] = camp
        
        print(f"Generated {len(self.camps)} camps")
    
    def assign_fighters_to_camps(self) -> None:
        """
        Distribute fighters among camps with smart division balancing.
        
        Goals:
        - Each camp gets fighters across multiple divisions (realistic gym)
        - Max 2 fighters per division per camp (allows teammate scenarios)
        - Higher tier camps get higher rated fighters
        - Avoids clustering (e.g., 5 Lightweights in one camp)
        """
        
        print("Assigning fighters to camps...")
        
        # Convert to lists for easier manipulation
        fighters_list = list(self.fighters.values())
        camps_list = list(self.camps.values())
        
        # Sort fighters by skill rating (best first - they go to better camps)
        fighters_list.sort(key=lambda f: f.skill_rating, reverse=True)
        
        # Sort camps by tier (better camps first)
        tier_order = {"ELITE": 0, "NATIONAL": 1, "REGIONAL": 2, "LOCAL": 3, "GARAGE": 4}
        camps_list.sort(key=lambda c: (tier_order[c.tier], -c.reputation))
        
        camp_stats = CampGenerator.TIER_STATS
        
        # Track division counts per camp: {camp_id: {weight_class: count}}
        camp_division_counts: Dict[str, Dict[str, int]] = {
            c.camp_id: {} for c in camps_list
        }
        
        # Max fighters per division per camp
        MAX_PER_DIVISION = 2
        
        def get_division_count(camp_id: str, weight_class: str) -> int:
            return camp_division_counts[camp_id].get(weight_class, 0)
        
        def add_fighter_to_camp(fighter: GeneratedFighter, camp: GeneratedCamp) -> None:
            fighter.camp_id = camp.camp_id
            camp.fighter_ids.append(fighter.fighter_id)
            wc = fighter.weight_class
            camp_division_counts[camp.camp_id][wc] = get_division_count(camp.camp_id, wc) + 1
        
        def can_accept_fighter(camp: GeneratedCamp, fighter: GeneratedFighter) -> bool:
            """Check if camp can accept this fighter (capacity + division limit)"""
            max_fighters = camp_stats[camp.tier]["fighters"][1]
            if len(camp.fighter_ids) >= max_fighters:
                return False
            # Check division limit
            if get_division_count(camp.camp_id, fighter.weight_class) >= MAX_PER_DIVISION:
                return False
            return True
        
        def find_best_camp(fighter: GeneratedFighter, prefer_empty_division: bool = True) -> Optional[GeneratedCamp]:
            """Find best camp for a fighter, preferring camps without someone in their division"""
            available = [c for c in camps_list if can_accept_fighter(c, fighter)]
            
            if not available:
                return None
            
            if prefer_empty_division:
                # Prefer camps with 0 fighters in this division
                empty_div_camps = [
                    c for c in available 
                    if get_division_count(c.camp_id, fighter.weight_class) == 0
                ]
                if empty_div_camps:
                    # Among empty-division camps, prefer higher tier
                    return empty_div_camps[0]
                
                # Next prefer camps with only 1 fighter in division
                one_fighter_camps = [
                    c for c in available
                    if get_division_count(c.camp_id, fighter.weight_class) == 1
                ]
                if one_fighter_camps:
                    return one_fighter_camps[0]
            
            # Fallback: any available camp (prefer higher tier)
            return available[0]
        
        # Assign all fighters with smart distribution
        assigned = 0
        for fighter in fighters_list:
            camp = find_best_camp(fighter, prefer_empty_division=True)
            
            if camp:
                add_fighter_to_camp(fighter, camp)
                assigned += 1
            else:
                # All camps at capacity - force assign to least full camp
                camps_by_space = sorted(
                    camps_list,
                    key=lambda c: len(c.fighter_ids)
                )
                if camps_by_space:
                    add_fighter_to_camp(fighter, camps_by_space[0])
                    assigned += 1
        
        # Ensure minimum fighters per camp (redistribute if needed)
        for camp in camps_list:
            min_fighters = camp_stats[camp.tier]["fighters"][0]
            while len(camp.fighter_ids) < min_fighters:
                # Find a camp with excess fighters to steal from
                donor_camp = None
                for other in camps_list:
                    if other.camp_id == camp.camp_id:
                        continue
                    other_min = camp_stats[other.tier]["fighters"][0]
                    if len(other.fighter_ids) > other_min + 1:
                        donor_camp = other
                        break
                
                if not donor_camp:
                    break  # Can't redistribute more
                
                # Move last fighter from donor to this camp
                fighter_id = donor_camp.fighter_ids.pop()
                fighter = self.fighters.get(fighter_id)
                if fighter:
                    # Update tracking
                    wc = fighter.weight_class
                    camp_division_counts[donor_camp.camp_id][wc] -= 1
                    add_fighter_to_camp(fighter, camp)
        
        # Report distribution stats
        division_clusters = 0
        for camp in camps_list:
            for wc, count in camp_division_counts[camp.camp_id].items():
                if count > 2:
                    division_clusters += 1
        
        if division_clusters == 0:
            print(f"  Smart distribution: No division clusters (max 2 per division per camp)")
    
    def generate_coaches(self) -> None:
        """Generate coaches for all camps based on tier."""
        
        if not COACHES_AVAILABLE or not CoachSystem:
            print("Coach system not available, skipping coach generation.")
            return
        
        print("Generating coaches...")
        
        # Coach count by tier
        COACH_CONFIG = {
            "ELITE": {"count": 5, "head_min": 75, "head_max": 95, "assist_min": 60, "assist_max": 85},
            "NATIONAL": {"count": 4, "head_min": 65, "head_max": 85, "assist_min": 50, "assist_max": 75},
            "REGIONAL": {"count": 3, "head_min": 55, "head_max": 75, "assist_min": 40, "assist_max": 65},
            "LOCAL": {"count": 2, "head_min": 40, "head_max": 65, "assist_min": 30, "assist_max": 55},
            "GARAGE": {"count": 1, "head_min": 25, "head_max": 55, "assist_min": 20, "assist_max": 45},
        }
        
        self._coach_system = CoachSystem()
        total_coaches = 0
        
        for camp in self.camps.values():
            config = COACH_CONFIG[camp.tier]
            camp_id = camp.camp_id
            
            nationality_hint = None
            if camp.fighter_ids:
                first_fighter = self.fighters.get(camp.fighter_ids[0])
                if first_fighter:
                    nationality_hint = first_fighter.country
            
            if camp_id not in self._coach_system._camp_coaches:
                self._coach_system._camp_coaches[camp_id] = []
            
            head_coach = generate_coach(
                nationality=nationality_hint if random.random() < 0.7 else None,
                min_overall=config["head_min"],
                max_overall=config["head_max"],
            )
            head_coach.camp_id = camp_id
            head_coach.is_head_coach = True
            self._coach_system._coaches[head_coach.coach_id] = head_coach
            camp.coach_ids.append(head_coach.coach_id)
            self._coach_system._camp_coaches[camp_id].append(head_coach.coach_id)
            total_coaches += 1
            
            for i in range(config["count"] - 1):
                assistant = generate_coach(
                    nationality=nationality_hint if random.random() < 0.5 else None,
                    min_overall=config["assist_min"],
                    max_overall=config["assist_max"],
                )
                assistant.camp_id = camp_id
                assistant.is_head_coach = False
                self._coach_system._coaches[assistant.coach_id] = assistant
                camp.coach_ids.append(assistant.coach_id)
                self._coach_system._camp_coaches[camp_id].append(assistant.coach_id)
                total_coaches += 1
        
        print(f"Generated {total_coaches} coaches for {len(self.camps)} camps")
    
    def get_coach_system(self):
        """Return the coach system for use by CLI."""
        return getattr(self, '_coach_system', None)

    def simulate_history(self) -> None:
        """Simulate years of fight history with real events"""
        
        print(f"Simulating {self.history_weeks} weeks of fight history...")
        
        self._history_sim = HistorySimulator(
            self.fighters,
            camps=self.camps,
            fighter_gen=self.fighter_gen,
        )
        self._history_sim.simulate_history(self.history_weeks)
        
        # Get final rankings
        rankings = self._history_sim.calculate_rankings()
        
        # Store rankings for later use
        self._rankings = rankings
        self._title_holders = self._history_sim.title_holders
        self._events = self._history_sim.events
        self._belt_history = self._history_sim.belt_history
        
        print(f"Simulated {len(self._history_sim.fight_history)} fights across {len(self._events)} events")
    
    def get_next_event_number(self) -> int:
        """Return the next event number for player's game (continues from sim)"""
        if self._history_sim:
            return self._history_sim.get_next_event_number()
        return 1
    
    def get_simulated_events(self) -> List[SimulatedEvent]:
        """Return all simulated events for archives"""
        return getattr(self, '_events', [])
    
    def get_belt_history(self) -> Optional[BeltHistory]:
        """Return belt history for archives/tracking"""
        return getattr(self, '_belt_history', None)
    
    def populate_game_state(self) -> None:
        """Add all generated content to the game state"""
        
        print("Populating game state...")
        
        # Add camps
        for camp in self.camps.values():
            self._add_camp_to_state(camp)
        
        # Add fighters (with fight history and popularity)
        for fighter in self.fighters.values():
            self._add_fighter_to_state(fighter)
        
        # Update division state
        for weight_class in WEIGHT_CLASSES:
            self._update_division_state(weight_class)
        
        # Store next event number in game state
        if hasattr(self.game_state, 'next_event_number'):
            self.game_state.next_event_number = self.get_next_event_number()
        
        print("World initialization complete!")
    
    def _add_camp_to_state(self, camp: GeneratedCamp) -> None:
        """Add a generated camp to game state"""
        
        if hasattr(self.game_state, 'add_camp'):
            self.game_state.add_camp(
                camp_id=camp.camp_id,
                name=camp.name,
                tier=camp.tier,
                balance=camp.balance,
                reputation=camp.reputation,
                is_player=False,
                location=camp.location,
            )
        elif hasattr(self.game_state, 'camps'):
            from core.game_state import CampRecord
            self.game_state.camps[camp.camp_id] = CampRecord(
                camp_id=camp.camp_id,
                name=camp.name,
                tier=camp.tier,
                balance=camp.balance,
                reputation=camp.reputation,
                is_player=False,
                fighter_count=len(camp.fighter_ids),
                location=camp.location,
            )

        # Generate equipment for AI camp based on tier
        try:
            import random as _rng_eq
            camp_tier = str(getattr(camp, 'tier', 'GARAGE')).upper()
            _eq_slots = {"GARAGE":2,"LOCAL":4,"REGIONAL":6,"NATIONAL":8,"ELITE":99}
            _eq_types = ["heavy_bags","wrestling_mats","submission_mats",
                         "weight_room","recovery_tank","cage"]
            _allowed_tiers = {
                "GARAGE":   ["BASIC"],
                "LOCAL":    ["BASIC","PRO"],
                "REGIONAL": ["BASIC","PRO","ELITE"],
                "NATIONAL": ["BASIC","PRO","ELITE"],
                "ELITE":    ["BASIC","PRO","ELITE"],
            }
            slots = _eq_slots.get(camp_tier, 2)
            allowed = _allowed_tiers.get(camp_tier, ["BASIC"])
            chosen_types = _rng_eq.sample(_eq_types, min(slots, len(_eq_types)))
            camp_eq = {}
            for et in chosen_types:
                if "ELITE" in allowed and _rng_eq.random() < 0.4:
                    camp_eq[et] = "ELITE"
                elif "PRO" in allowed and _rng_eq.random() < 0.6:
                    camp_eq[et] = "PRO"
                else:
                    camp_eq[et] = "BASIC"
            if hasattr(self, '_bridge') and self._bridge:
                _cid = camp.camp_id
                if not hasattr(self._bridge, '_camp_equipment'):
                    self._bridge._camp_equipment = {}
                self._bridge._camp_equipment[_cid] = camp_eq
        except Exception:
            pass

    def _add_fighter_to_state(self, fighter: GeneratedFighter) -> None:
        """Add a generated fighter to game state with popularity and history"""

        if hasattr(self.game_state, 'add_fighter'):
            self.game_state.add_fighter(
                fighter_id=fighter.fighter_id,
                name=fighter.name,
                weight_class=fighter.weight_class,
                camp_id=fighter.camp_id,
                wins=fighter.wins,
                losses=fighter.losses,
                draws=fighter.draws,
                is_champion=fighter.is_champion,
                popularity=fighter.popularity,
                ko_wins=fighter.ko_wins,
                sub_wins=fighter.sub_wins,
                fight_history=fighter.fight_history,
            )
        elif hasattr(self.game_state, 'fighters'):
            from core.game_state import FighterRecord
            record = FighterRecord(
                fighter_id=fighter.fighter_id,
                name=fighter.name,
                weight_class=fighter.weight_class,
                camp_id=fighter.camp_id,
                wins=fighter.wins,
                losses=fighter.losses,
                draws=fighter.draws,
                is_champion=fighter.is_champion,
                overall_rating=fighter.skill_rating,
                is_active=fighter.is_active,
            )
            # Add popularity if the record supports it
            if hasattr(record, 'popularity'):
                record.popularity = fighter.popularity
            # Add fight history if the record supports it
            if hasattr(record, 'fight_history'):
                record.fight_history = fighter.fight_history.copy() if fighter.fight_history else []
            # Ship K2: body frame + natural weight class for cut mechanics
            if hasattr(record, 'body_frame'):
                record.body_frame = getattr(fighter, 'body_frame', 5)
            if hasattr(record, 'natural_weight_class'):
                record.natural_weight_class = getattr(
                    fighter, 'natural_weight_class', fighter.weight_class)
            # Ship K5: persistent personality for challenge/offer mechanics
            if hasattr(record, 'personality'):
                record.personality = getattr(
                    fighter, 'personality', 'Competitor')
            self.game_state.fighters[fighter.fighter_id] = record

        # Ship #32: persist world-gen's actual attribute values into
        # _fighter_data so the bridge's _convert_real_fighter._attr() reads
        # them on demand instead of falling through to the random fallback.
        # Save/load rides the existing dict-key-agnostic serialization at
        # game_state.py:1239 (to_dict) and 1306 (from_dict). Fixes Finding
        # #32 (fighter attributes mutating across Flask reload). Style is
        # populated downstream by game_bridge.py:894-914's enrichment block;
        # don't write it here to avoid duplicate-write churn.
        if hasattr(self.game_state, '_fighter_data') and fighter.attributes:
            _fdata = self.game_state._fighter_data.get(fighter.fighter_id, {})
            for _key, _val in fighter.attributes.items():
                _fdata[_key] = int(_val)
            _fdata['age'] = int(fighter.age)
            _fdata['country'] = str(fighter.country)
            # Per-fighter potential ceiling — read by the training loop
            # (_diminishing_gain) and the AI dev loop (_advance_ai_fighter_
            # training). Fall back to skill_rating+8 for any fighter that
            # somehow predates the potential_ceiling field on GeneratedFighter.
            _fdata['potential'] = int(getattr(fighter, 'potential_ceiling',
                                              int(fighter.skill_rating) + 8))
            # Ship K2: persist body_frame + natural_weight_class
            _fdata['body_frame'] = int(getattr(fighter, 'body_frame', 5))
            _fdata['natural_weight_class'] = str(getattr(
                fighter, 'natural_weight_class', fighter.weight_class))
            # Ship K5: persist personality
            _fdata['personality'] = str(getattr(
                fighter, 'personality', 'Competitor'))

            # Ship: AI fighter trait assignment at world gen.
            # Uses the traits module's assign_traits() which handles
            # attribute-triggered + weighted random + conflict avoidance.
            # OVR-gated trait count:
            #   skill_rating >= 80 (elite): 1 or 2 traits
            #   skill_rating >= 65 (mid):   0 / 1 / 2 (mostly 1)
            #   skill_rating <  65 (raw):   0 or 1 (mostly 0)
            if TRAITS_AVAILABLE and not _fdata.get('traits'):
                try:
                    _ovr = int(getattr(fighter, 'skill_rating', 50))
                    if _ovr >= 80:
                        _n = random.choices([1, 2], weights=[0.45, 0.55])[0]
                    elif _ovr >= 65:
                        _n = random.choices([0, 1, 2],
                                             weights=[0.20, 0.65, 0.15])[0]
                    else:
                        _n = random.choices([0, 1],
                                             weights=[0.55, 0.45])[0]

                    # Remap world-gen attribute keys to the trigger
                    # keys the traits module expects (iq -> fight_iq).
                    _attr_for_traits = dict(fighter.attributes)
                    if 'iq' in _attr_for_traits and 'fight_iq' not in _attr_for_traits:
                        _attr_for_traits['fight_iq'] = _attr_for_traits['iq']

                    _traits = _assign_traits(_attr_for_traits, num_traits=_n)
                    _fdata['traits'] = list(_traits) if _traits else []
                except Exception as _te:
                    print(f"  ⚠️ trait assignment failed for {fighter.fighter_id}: {_te}")
                    _fdata['traits'] = []

            self.game_state._fighter_data[fighter.fighter_id] = _fdata
    
    def _update_division_state(self, weight_class: str) -> None:
        """Update division state with champion and rankings"""
        
        if hasattr(self.game_state, 'divisions') and weight_class in self.game_state.divisions:
            division = self.game_state.divisions[weight_class]
            
            # Set champion
            champion_id = self._title_holders.get(weight_class)
            if champion_id:
                division.champion_id = champion_id
            
            # Set rankings
            if hasattr(division, 'rankings') and weight_class in self._rankings:
                division.rankings = self._rankings[weight_class][:15]
    
    def initialize_world(self) -> None:
        """
        Main entry point - initialize the entire world.
        
        Call this method to populate the game state with:
        - AI training camps
        - Fighters for all divisions
        - 2-3 years of simulated fight history AS REAL EVENTS
        - Champions and rankings
        - Amateur circuit with tournament history
        - Popularity values for all fighters
        """
        
        print("=" * 50)
        print("INITIALIZING WORLD")
        print("=" * 50)
        
        self.generate_fighters()
        self.generate_camps()
        self.assign_fighters_to_camps()
        self.generate_coaches()
        self.simulate_history()
        
        # Initialize amateur system with history
        self.simulate_amateur_history()
        
        self.populate_game_state()
        
        # Count coaches
        coach_count = sum(len(c.coach_ids) for c in self.camps.values())
        
        print("=" * 50)
        print("WORLD READY")
        print(f"  Fighters: {len(self.fighters)}")
        print(f"  Camps: {len(self.camps)}")
        print(f"  Coaches: {coach_count}")
        print(f"  Champions: {len(self._title_holders)}")
        print(f"  Events Created: {len(self._events)} (DFC 1 - DFC {self.get_next_event_number() - 1})")
        print(f"  Next Event: DFC {self.get_next_event_number()}")
        if hasattr(self, '_amateur_system') and self._amateur_system:
            amateur_count = len(self._amateur_system.amateurs)
            print(f"  Amateur Fighters: {amateur_count}")
        print("=" * 50)
    
    def simulate_amateur_history(self) -> None:
        """Initialize amateur system and simulate tournament history."""
        
        if not AMATEUR_AVAILABLE:
            print("Amateur system not available, skipping...")
            return
        
        print("Initializing amateur circuit...")
        
        try:
            self._amateur_system = create_amateur_system()
            
            # Calculate months of history based on total history weeks
            if self.history_weeks >= 156:  # 3 years
                amateur_months = 12
            elif self.history_weeks >= 104:  # 2 years
                amateur_months = 9
            else:
                amateur_months = 6
            
            # Simulate amateur history
            history_summary = self._amateur_system.simulate_history(
                num_months=amateur_months,
                start_week=max(1, self.history_weeks - (amateur_months * 4)),
                verbose=True,
            )
            
            print(f"  Amateur tournaments: {history_summary['tournaments_run']}")
            print(f"  Amateur fights: {history_summary['fights_simulated']}")
            print(f"  Pro graduates: {len(history_summary['pro_graduates'])}")
            
            self._pro_graduates = history_summary['pro_graduates']
            
        except Exception as e:
            print(f"  Amateur system error: {e}")
            self._amateur_system = None
    
    def get_amateur_system(self):
        """Return the amateur system for use by CLI."""
        return getattr(self, '_amateur_system', None)
    
    def get_pro_graduates(self) -> List[Dict[str, Any]]:
        """Get list of amateurs who recently turned pro."""
        return getattr(self, '_pro_graduates', [])


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def initialize_world(game_state, history_years: float = 2.5, bridge=None) -> WorldInitializer:
    """
    Convenience function to initialize the game world.

    Args:
        game_state: The GameState to populate
        history_years: Years of history to simulate (default 2.5)
        bridge: Optional GameBridge handle (threaded into WorldInitializer
            so sim-time state like AI camp equipment can be surfaced back).

    Returns:
        The WorldInitializer instance (for inspection if needed)
    """
    history_weeks = int(history_years * 52)

    initializer = WorldInitializer(
        game_state=game_state,
        history_weeks=history_weeks,
        bridge=bridge,
    )
    
    initializer.initialize_world()
    
    return initializer


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Classes
    "WorldInitializer",
    "FighterGenerator", 
    "CampGenerator",
    "HistorySimulator",
    
    # Data structures
    "GeneratedFighter",
    "GeneratedCamp",
    "SimulatedFight",
    "SimulatedEvent",
    
    # Functions
    "initialize_world",
    "calculate_starting_popularity",
    "calculate_popularity_change",
    "calculate_star_power",
    "is_main_event_worthy",
    
    # Constants
    "WEIGHT_CLASSES",
    "COUNTRY_NAMES",
    "TIER_STARTING_POPULARITY",
    "POPULARITY_WIN",
    "POPULARITY_FINISH_BONUS",
    "POPULARITY_TITLE_WIN",
]
