# interface/cli.py
# Module 35: CLI Interface (Full Integration)
# Lines: ~8,800
#
# Comprehensive CLI with all systems integrated:
# - Smart matchmaking with personality variance
# - Full MMA-style rankings with P4P
# - AI behavior & fight acceptance decisions
# - Scouting, Tale of Tape, Gameplans
# - Coach management for all camps (AI + Player)
# - Training camps with coach bonuses
# - Fight commentary/summaries
# - Week advancement with ranking changes
# - Judges system with named scorecards & controversy
# - Starting coach selection at game start
# - Fictional sponsorship brands (APEX, Titan, SURGE, etc.)
# - Fighter and camp sponsorship system
# - Tier-based fighter overhead costs
# - Financial pressure system (warnings, emergency loans, forced cuts, bankruptcy)

"""
Cage Dynasty - Command Line Interface (Integrated v2)

Complete text-based interface with all game systems connected.
"""

from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
import os
import sys
import random

# Core imports
from core.game_state import GameState, GamePhase, GameMode, FighterRecord
from core.persistence import (
    save_game, load_game, quicksave, quickload, autosave,
    list_saves, save_exists, get_available_slots, SaveMetadata,
)
from core.events import emit, subscribe
from core.config import get_config

# Traits system
from systems.traits import (
    FIGHTER_TRAITS,
    assign_traits,
    get_stat_modifiers,
    apply_stat_modifiers,
    get_trait_fight_modifiers,
    get_pressure_counter_interaction,
    get_training_multiplier,
    get_trait_description,
    get_trait_category,
    has_trait,
)

# FOTN (Fight of the Night) System
FOTN_AVAILABLE = False
try:
    from systems.fotn import (
        calculate_fotn_score,
        select_fotn,
        format_fotn_announcement,
        create_fotn_result,
        FOTN_BONUS,
    )
    FOTN_AVAILABLE = True
except ImportError:
    FOTN_AVAILABLE = False

# AI Behavior System (Personality & Decision Variance)
AI_BEHAVIOR_AVAILABLE = False
AIDecisionEngine = None
FighterPersonality = None
FighterMentality = None
RiskProfile = None
generate_fighter_personality = None
try:
    from simulation.ai_behavior import (
        AIDecisionEngine,
        FighterPersonality,
        FighterMentality,
        RiskProfile,
        ActivityPreference,
        FinishingInstinct,
        TrainingDedication,
        generate_fighter_personality,
        DecisionBreakdown,
    )
    AI_BEHAVIOR_AVAILABLE = True
except ImportError:
    pass

# Rankings System (Full MMA-style rankings)
RANKINGS_AVAILABLE = False
RankingsSystem = None
RankingChange = None
RankingChangeReason = None
P4PEntry = None
FightOutcome = None
CHAMPION_RANK = 0
try:
    from systems.rankings import (
        RankingsSystem,
        RankingChange,
        RankingChangeReason,
        RankingEntry,
        P4PEntry,
        DivisionRankings,
        CHAMPION_RANK,
        calculate_finish_bonus,
        calculate_win_streak_bonus,
    )
    from core.types import FightOutcome
    RANKINGS_AVAILABLE = True
except ImportError:
    try:
        # Try alternate path
        from rankings import RankingsSystem, RankingChange, RankingChangeReason, P4PEntry, CHAMPION_RANK
        RANKINGS_AVAILABLE = True
    except ImportError:
        pass

# Aging System
AGING_AVAILABLE = False
AgingSystem = None
CareerPhase = None
try:
    from systems.aging import (
        AgingSystem,
        CareerPhase,
        get_career_phase,
        calculate_retirement_probability,
        is_in_prime,
        years_until_decline,
    )
    AGING_AVAILABLE = True
except ImportError:
    pass

# Injury System
INJURY_AVAILABLE = False
InjurySystem = None
InjuryType = None
try:
    from systems.injury import (
        InjurySystem,
        Injury,
        InjuryLocation,
        generate_fight_injury,
        calculate_fight_injury_probability,
    )
    from core.types import InjuryType, FightOutcome
    INJURY_AVAILABLE = True
except ImportError:
    pass

# Rivalry System
RIVALRY_AVAILABLE = False
RivalrySystem = None
try:
    from narrative.rivalry import (
        RivalrySystem,
        RivalryType,
        RivalryIntensity,
        Rivalry,
        FightContext,
        detect_rivalry_from_fight,
        get_rivalry_intensity_description,
        get_rivalry_type_description,
        format_rivalry_display,
    )
    RIVALRY_AVAILABLE = True
except ImportError:
    pass

# Facilities System
FACILITIES_AVAILABLE = False
try:
    from systems.facilities import (
        get_stat_cap,
        apply_facility_cap,
        can_sign_fighter,
        get_max_fighters,
        get_upgrade_cost,
        get_upgrade_requirements,
        can_upgrade,
        perform_upgrade,
        get_roster_status,
        get_stats_near_cap,
        FACILITY_STAT_CAPS,
        TIER_ORDER,
        CampStats,
    )
    FACILITIES_AVAILABLE = True
except ImportError:
    pass

# Watchlist System
WATCHLIST_AVAILABLE = False
Watchlist = None
try:
    from systems.watchlist import (
        Watchlist,
        WatchCategory,
        WatchPriority,
        WatchEntry,
        WatchAlert,
        AlertType,
        create_watchlist,
        format_watch_entry,
        format_watchlist_summary,
        get_category_options,
        get_priority_options,
        PRIORITY_SYMBOLS,
    )
    WATCHLIST_AVAILABLE = True
except ImportError:
    pass

# Economy System
ECONOMY_AVAILABLE = False
try:
    from systems.economy import (
        EconomyManager,
        create_economy_manager,
        initialize_camp_finances,
        format_money as economy_format_money,
        TransactionType,
        FightEarnings,
        WeeklyFinanceSummary,
        Sponsorship,
        CampSponsorship,
        SponsorTier,
        FinancialPressureStage,
        FinancialPressureResult,
        CAMP_MONTHLY_COSTS,
        UPGRADE_REQUIREMENTS,
        LOAN_CONFIG,
        BASE_PURSE_BY_TIER,
        FIGHTER_OVERHEAD_BY_TIER,
        SPONSORSHIP_COMPANIES,
        CAMP_SPONSORS,
        generate_sponsorship_offer,
        generate_camp_sponsorship_offer,
        EMERGENCY_LOAN_INTEREST,
    )
    ECONOMY_AVAILABLE = True
except ImportError:
    EconomyManager = None
    ECONOMY_AVAILABLE = False

# Full Fight Engine
FIGHT_ENGINE_AVAILABLE = False
FightEngineAttributes = None
FightConfig = None
NarratedFightSimulator = None
NarratedFightResult = None
FightingStyleEnum = None  # For mapping style strings to enums

try:
    # Try nested module structure first (simulation/fight_engine.py)
    from simulation.fight_engine import FighterAttributes as FightEngineAttributes, FightConfig
    from simulation.fight_integration import NarratedFightSimulator, NarratedFightResult, simulate_narrated_fight
    from core.types import FightingStyle as FightingStyleEnum
    FIGHT_ENGINE_AVAILABLE = True
except ImportError:
    try:
        # Try flat module structure (fight_engine.py in same directory)
        from fight_engine import FighterAttributes as FightEngineAttributes, FightConfig
        from fight_integration import NarratedFightSimulator, NarratedFightResult, simulate_narrated_fight
        from core.types import FightingStyle as FightingStyleEnum
        FIGHT_ENGINE_AVAILABLE = True
    except ImportError:
        pass





# Pagination and Search Helpers
try:
    from interface.cli_constants import (
        Paginator,
        search_by_name,
        DEFAULT_PAGE_SIZE,
    )
    PAGINATION_AVAILABLE = True
except ImportError:
    PAGINATION_AVAILABLE = False
    DEFAULT_PAGE_SIZE = 15
    
    def search_by_name(items, query, name_attr="name"):
        """Fallback search if cli_constants not available."""
        if not query or not query.strip():
            return items
        query = query.lower().strip()
        return [item for item in items 
                if query in str(getattr(item, name_attr, "")).lower()]

# Scouting System
SCOUTING_AVAILABLE = False
try:
    from systems.scouting import (
        scout_fighter,
        compare_fighters,
        get_matchup_analysis,
        assess_potential,
        ScoutingReport,
        FighterComparison,
        MatchupAnalysis,
    )
    SCOUTING_AVAILABLE = True
except ImportError:
    pass

# Tale of Tape System
TALE_OF_TAPE_AVAILABLE = False
try:
    from systems.tale_of_tape import (
        generate_tale_of_tape,
        format_tale_of_tape,
        print_tale_of_tape,
        format_tale_of_tape_compact,
        TaleOfTape,
    )
    TALE_OF_TAPE_AVAILABLE = True
except ImportError:
    pass

# Gameplan System
GAMEPLAN_AVAILABLE = False
try:
    from systems.gameplan import (
        create_gameplan,
        get_gameplan_modifiers,
        recommend_gameplan,
        generate_ai_gameplan,
        format_gameplan,
        format_gameplan_compact,
        GameplanMenuHelper,
        Gameplan,
        # New matchup analysis
        get_matchup_analysis,
        get_gameplan_options,
        MatchupAnalysis,
        GameplanOption,
    )
    GAMEPLAN_AVAILABLE = True
except ImportError:
    pass

# Coach System
COACHES_AVAILABLE = False
CoachSystem = None
try:
    from systems.coaches import (
        CoachSystem,
        Coach,
        CoachSpecialty,
        CoachTrait,
        generate_coach,
        generate_starting_coach_options,
        calculate_chemistry,
        format_coach_display,
        format_coach_stars,
    )
    COACHES_AVAILABLE = True
except ImportError:
    pass

# ============================================================================
# CONSTANTS
# ============================================================================

TERMINAL_WIDTH = 70

# Box drawing
BOX_H, BOX_V = "-", "|"
BOX_TL, BOX_TR, BOX_BL, BOX_BR = "+", "+", "+", "+"


class Colors:
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GOLD = "\033[93m"
    WIN = "\033[92m"
    LOSS = "\033[91m"
    NEUTRAL = "\033[96m"
    HIGHLIGHT = "\033[1;97m"
    ORANGE = "\033[38;5;208m"
    
    @classmethod
    def disable(cls):
        for attr in ['RESET', 'BOLD', 'DIM', 'RED', 'GREEN', 'YELLOW', 
                     'BLUE', 'MAGENTA', 'CYAN', 'WHITE', 'GOLD', 'WIN',
                     'LOSS', 'NEUTRAL', 'HIGHLIGHT', 'ORANGE']:
            setattr(cls, attr, "")


def colored(text: str, color: str) -> str:
    return f"{color}{text}{Colors.RESET}"


def format_record_colored(wins: int, losses: int, draws: int = 0) -> str:
    w = colored(str(wins), Colors.WIN)
    l = colored(str(losses), Colors.LOSS)
    if draws > 0:
        d = colored(str(draws), Colors.NEUTRAL)
        return f"{w}-{l}-{d}"
    return f"{w}-{l}"


TITLE_ART = r"""
   ____    _    ____ _____   ______   ___   _    _    ____ _______   __
  / ___|  / \  / ___| ____| |  _ \ \ / / \ | |  / \  / ___|_   _\ \ / /
 | |     / _ \| |  _|  _|   | | | \ V /|  \| | / _ \ \___ \ | |  \ V / 
 | |___ / ___ \ |_| | |___  | |_| || | | |\  |/ ___ \ ___) || |   | |  
  \____/_/   \_\____|_____| |____/ |_| |_| \_/_/   \_\____/ |_|   |_|  
"""

VERSION = "0.3.0"


# ============================================================================
# DISPLAY UTILITIES
# ============================================================================

def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str) -> None:
    print()
    print(BOX_TL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_TR)
    print(BOX_V + title.center(TERMINAL_WIDTH - 2) + BOX_V)
    print(BOX_BL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_BR)
    print()


def print_divider() -> None:
    print(BOX_H * TERMINAL_WIDTH)


def print_box(lines: List[str], title: Optional[str] = None) -> None:
    print(BOX_TL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_TR)
    if title:
        print(BOX_V + title.center(TERMINAL_WIDTH - 2) + BOX_V)
        print(BOX_V + BOX_H * (TERMINAL_WIDTH - 2) + BOX_V)
    for line in lines:
        display_line = line[:TERMINAL_WIDTH - 4]
        padding = TERMINAL_WIDTH - 4 - len(display_line)
        print(BOX_V + " " + display_line + " " * padding + " " + BOX_V)
    print(BOX_BL + BOX_H * (TERMINAL_WIDTH - 2) + BOX_BR)


def print_menu(options: List[Tuple[str, str]], prompt: str = "Choose") -> None:
    print()
    for key, description in options:
        print(f"  [{key}] {description}")
    print()


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def get_choice(options: List[str], prompt: str = "Choose") -> Optional[str]:
    choice = get_input(f"{prompt}: ").lower()
    if choice in [o.lower() for o in options]:
        return choice
    return None


def confirm(message: str) -> bool:
    response = get_input(f"{message} (y/n): ").lower()
    return response in ("y", "yes")


def pause(message: str = "Press Enter to continue...") -> None:
    get_input(message)


def format_record(wins: int, losses: int, draws: int = 0) -> str:
    if draws:
        return f"{wins}-{losses}-{draws}"
    return f"{wins}-{losses}"


def format_money(amount: int) -> str:
    return f"${amount:,}"


def stat_bar(value: int, width: int = 20) -> str:
    """Create a visual stat bar"""
    filled = int((value / 100) * width)
    empty = width - filled
    
    if value >= 80:
        color = Colors.GREEN
    elif value >= 60:
        color = Colors.YELLOW
    elif value >= 40:
        color = Colors.ORANGE
    else:
        color = Colors.RED
    
    bar = "#" * filled + "." * empty
    return f"{color}{bar}{Colors.RESET} {value}"


def stat_letter_grade(value: int) -> str:
    """Convert stat to letter grade with color"""
    if value >= 90:
        return colored("A+", Colors.GREEN)
    elif value >= 85:
        return colored("A", Colors.GREEN)
    elif value >= 80:
        return colored("A-", Colors.GREEN)
    elif value >= 75:
        return colored("B+", Colors.CYAN)
    elif value >= 70:
        return colored("B", Colors.CYAN)
    elif value >= 65:
        return colored("B-", Colors.CYAN)
    elif value >= 60:
        return colored("C+", Colors.YELLOW)
    elif value >= 55:
        return colored("C", Colors.YELLOW)
    elif value >= 50:
        return colored("C-", Colors.YELLOW)
    elif value >= 45:
        return colored("D+", Colors.ORANGE)
    elif value >= 40:
        return colored("D", Colors.ORANGE)
    else:
        return colored("F", Colors.RED)


# ============================================================================
# EXPANDED DATA CLASSES
# ============================================================================

@dataclass
class FighterFullData:
    """Complete fighter data with all attributes"""
    # Identity
    fighter_id: str
    name: str
    nickname: Optional[str] = None
    
    # Bio
    country: str = "United States"
    age: int = 25
    height_cm: int = 178
    weight_lbs: float = 155.0
    reach_cm: int = 180
    
    # Classification
    weight_class: str = "Lightweight"
    camp_id: Optional[str] = None
    contract_id: Optional[str] = None
    is_champion: bool = False
    is_active: bool = True
    is_generational: bool = False  # Once-in-a-generation talent
    
    # Style
    fighting_style: str = "MMA Hybrid"
    build_type: str = "Athletic"
    personality: str = "Methodical"
    
    # Physical Attributes (1-100)
    strength: int = 50
    speed: int = 50
    cardio: int = 50
    chin: int = 50
    
    # Striking Attributes
    boxing: int = 50
    kicks: int = 50
    clinch_striking: int = 50
    striking_defense: int = 50
    
    # Grappling Attributes
    wrestling: int = 50
    bjj: int = 50
    takedown_defense: int = 50
    
    # Mental Attributes
    heart: int = 50
    fight_iq: int = 50
    composure: int = 50
    
    # Record
    wins: int = 0
    losses: int = 0
    draws: int = 0
    ko_wins: int = 0
    sub_wins: int = 0
    dec_wins: int = 0
    ko_losses: int = 0
    sub_losses: int = 0
    
    # Career stats
    title_defenses: int = 0
    fights_total: int = 0
    win_streak: int = 0
    lose_streak: int = 0
    fotn_awards: int = 0  # Fight of the Night bonuses
    
    # Traits (special abilities/characteristics)
    traits: List[str] = field(default_factory=list)
    
    @property
    def overall_rating(self) -> int:
        """Calculate overall rating from attributes"""
        striking = (self.boxing * 2 + self.kicks + self.clinch_striking) // 4
        grappling = (self.wrestling + self.bjj * 2 + self.takedown_defense) // 4
        return (striking + grappling + self.chin + self.cardio + self.heart) // 5
    
    @property
    def record(self) -> str:
        if self.draws:
            return f"{self.wins}-{self.losses}-{self.draws}"
        return f"{self.wins}-{self.losses}"
    
    @property
    def height_display(self) -> str:
        """Convert cm to feet/inches"""
        total_inches = self.height_cm / 2.54
        feet = int(total_inches // 12)
        inches = int(total_inches % 12)
        return f"{feet}'{inches}\""
    
    @property
    def reach_display(self) -> str:
        """Convert cm to inches"""
        return f"{int(self.reach_cm / 2.54)}\""
    
    def to_dict(self) -> Dict[str, Any]:
        # Ensure fighting_style is a string (not enum)
        style_str = self.fighting_style
        if hasattr(self.fighting_style, 'value'):
            style_str = str(self.fighting_style.value)
        elif hasattr(self.fighting_style, 'name'):
            style_str = str(self.fighting_style.name).replace('_', ' ').title()
        
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "nickname": self.nickname,
            "country": self.country,
            "age": self.age,
            "height_cm": self.height_cm,
            "weight_lbs": self.weight_lbs,
            "reach_cm": self.reach_cm,
            "weight_class": self.weight_class,
            "camp_id": self.camp_id,
            "contract_id": self.contract_id,
            "is_champion": self.is_champion,
            "is_active": self.is_active,
            "fighting_style": style_str,
            "build_type": self.build_type,
            "personality": self.personality,
            "strength": self.strength,
            "speed": self.speed,
            "cardio": self.cardio,
            "chin": self.chin,
            "boxing": self.boxing,
            "kicks": self.kicks,
            "clinch_striking": self.clinch_striking,
            "striking_defense": self.striking_defense,
            "wrestling": self.wrestling,
            "bjj": self.bjj,
            "takedown_defense": self.takedown_defense,
            "heart": self.heart,
            "fight_iq": self.fight_iq,
            "composure": self.composure,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "ko_wins": self.ko_wins,
            "sub_wins": self.sub_wins,
            "dec_wins": self.dec_wins,
            "ko_losses": self.ko_losses,
            "sub_losses": self.sub_losses,
            "title_defenses": self.title_defenses,
            "fights_total": self.fights_total,
            "win_streak": self.win_streak,
            "lose_streak": self.lose_streak,
            "fotn_awards": self.fotn_awards,
            "traits": self.traits,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FighterFullData":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_fight_attributes(self) -> Optional[Any]:
        """Convert to FighterAttributes for fight engine.
        
        Returns None if fight engine not available.
        """
        if not FIGHT_ENGINE_AVAILABLE or FightEngineAttributes is None:
            return None
        
        # Convert string fighting_style to FightingStyle enum
        style_enum = FightingStyleEnum.BALANCED  # Default
        if FightingStyleEnum is not None:
            # Map common style strings to enum values
            style_mapping = {
                "MMA Hybrid": FightingStyleEnum.BALANCED,
                "Balanced": FightingStyleEnum.BALANCED,
                "Striker": FightingStyleEnum.STRIKER,
                "Kickboxer": FightingStyleEnum.STRIKER,
                "Boxing": FightingStyleEnum.STRIKER,
                "Counter Striker": FightingStyleEnum.COUNTER_STRIKER,
                "Counter-Striker": FightingStyleEnum.COUNTER_STRIKER,
                "Pressure Fighter": FightingStyleEnum.PRESSURE_FIGHTER,
                "Point Fighter": FightingStyleEnum.POINT_FIGHTER,
                "Muay Thai": FightingStyleEnum.MUAY_THAI,
                "Wrestler": FightingStyleEnum.WRESTLER,
                "Wrestling": FightingStyleEnum.WRESTLER,
                "Ground and Pound": FightingStyleEnum.GROUND_AND_POUND,
                "Ground & Pound": FightingStyleEnum.GROUND_AND_POUND,
                "GnP": FightingStyleEnum.GROUND_AND_POUND,
                "BJJ Specialist": FightingStyleEnum.BJJ_SPECIALIST,
                "BJJ": FightingStyleEnum.BJJ_SPECIALIST,
                "Jiu-Jitsu": FightingStyleEnum.BJJ_SPECIALIST,
                "Submission Grappler": FightingStyleEnum.BJJ_SPECIALIST,
                "Clinch Fighter": FightingStyleEnum.CLINCH_FIGHTER,
                "Sprawl and Brawl": FightingStyleEnum.SPRAWL_AND_BRAWL,
                "Sprawl & Brawl": FightingStyleEnum.SPRAWL_AND_BRAWL,
            }
            style_enum = style_mapping.get(self.fighting_style, FightingStyleEnum.BALANCED)
        
        return FightEngineAttributes(
            fighter_id=self.fighter_id,
            name=self.name,
            strength=self.strength,
            speed=self.speed,
            cardio=self.cardio,
            chin=self.chin,
            boxing=self.boxing,
            kicks=self.kicks,
            clinch_striking=self.clinch_striking,
            striking_defense=self.striking_defense,
            wrestling=self.wrestling,
            bjj=self.bjj,
            takedown_defense=self.takedown_defense,
            heart=self.heart,
            fight_iq=self.fight_iq,
            composure=self.composure,
            fighting_style=style_enum,
        )


@dataclass
class FightResult:
    """Result of a completed fight"""
    fight_id: str
    event_id: str
    event_name: str
    week: int
    
    # Fighters
    fighter1_id: str
    fighter1_name: str
    fighter2_id: str
    fighter2_name: str
    
    # Result
    winner_id: str
    winner_name: str
    loser_id: str
    loser_name: str
    method: str  # KO, TKO, SUB, DEC, DRAW
    round_finished: int
    time_finished: str = "5:00"
    
    # Fight details
    weight_class: str = ""
    is_title_fight: bool = False
    is_main_event: bool = False
    rounds_scheduled: int = 3
    
    # Stats summary
    fighter1_strikes: int = 0
    fighter2_strikes: int = 0
    fighter1_takedowns: int = 0
    fighter2_takedowns: int = 0
    fighter1_sub_attempts: int = 0
    fighter2_sub_attempts: int = 0
    
    # Commentary summary
    fight_summary: str = ""
    key_moments: List[str] = field(default_factory=list)
    
    # Enhanced commentary from full fight engine
    full_commentary: str = ""
    fight_narrative: str = ""
    round_summaries: List[Dict[str, Any]] = field(default_factory=list)
    
    # Round-by-round stats
    fighter1_round_stats: List[Dict[str, Any]] = field(default_factory=list)
    fighter2_round_stats: List[Dict[str, Any]] = field(default_factory=list)
    
    # Judges scores (for decisions)
    judge_scores: List[Tuple[int, int]] = field(default_factory=list)
    decision_type: str = ""  # Unanimous, Split, Majority
    
    # Judge details (from judges.py integration)
    judge_names: List[str] = field(default_factory=list)
    judge_scorecards: List[Dict[str, Any]] = field(default_factory=list)
    is_controversial: bool = False
    controversy_reason: str = ""
    decision_commentary: str = ""
    
    # Bonuses
    fight_of_night: bool = False
    performance_bonus: bool = False
    
    # Final health (for injury calculation)
    fighter1_final_health: float = 100.0
    fighter2_final_health: float = 100.0
    
    def get_summary_line(self) -> str:
        """One-line summary of the fight"""
        if self.method == "DEC":
            return f"{self.winner_name} def. {self.loser_name} by Decision"
        elif self.method == "DRAW":
            return f"{self.fighter1_name} vs {self.fighter2_name} - Draw"
        else:
            return f"{self.winner_name} def. {self.loser_name} by {self.method} (R{self.round_finished})"
    
    @property
    def has_full_commentary(self) -> bool:
        """Check if this result has full fight engine commentary"""
        return bool(self.full_commentary or self.fight_narrative)


@dataclass
class CompletedEvent:
    """A completed DFC event with all fight results"""
    event_id: str
    event_name: str
    week: int
    location: str = "Las Vegas, NV"
    
    # Fights (ordered main event to opener)
    fights: List[FightResult] = field(default_factory=list)
    
    # Stats
    total_fights: int = 0
    finishes: int = 0
    knockouts: int = 0
    submissions: int = 0
    decisions: int = 0
    
    def add_fight(self, result: FightResult) -> None:
        self.fights.append(result)
        self.total_fights += 1
        if result.method in ["KO", "TKO"]:
            self.finishes += 1
            self.knockouts += 1
        elif result.method == "SUB":
            self.finishes += 1
            self.submissions += 1
        elif result.method == "DEC":
            self.decisions += 1


@dataclass
class NewsItem:
    """A news item for the feed"""
    headline: str
    details: str = ""
    category: str = "general"
    week: int = 0
    
    def __str__(self) -> str:
        return self.headline


@dataclass
class FightOffer:
    """A fight offer for the player"""
    offer_id: str
    fighter_id: str
    fighter_name: str
    opponent_id: str
    opponent_name: str
    opponent_record: str
    opponent_rating: int
    weight_class: str
    event_name: str
    event_date: str
    weeks_away: int
    purse: int
    is_title_fight: bool = False
    is_main_event: bool = False
    matchup_quality: str = "Good"
    
    def __str__(self) -> str:
        title_str = " [TITLE FIGHT]" if self.is_title_fight else ""
        return f"{self.fighter_name} vs {self.opponent_name}{title_str}"


# ============================================================================
# SCHEDULING CONFIGURATION
# ============================================================================

# Minimum weeks before fight by camp tier
MIN_WEEKS_BY_TIER = {
    "GARAGE": 4,
    "LOCAL": 5,
    "REGIONAL": 6,
    "NATIONAL": 8,
    "ELITE": 8,
}

# Maximum weeks for offer generation
MAX_WEEKS_BY_TIER = {
    "GARAGE": 6,
    "LOCAL": 7,
    "REGIONAL": 8,
    "NATIONAL": 10,
    "ELITE": 12,
}

# FIGHTER_TRAITS, TRAIT_CATEGORIES, CONFLICTING_TRAITS are now imported from systems.traits


# ============================================================================
# EXTENDED SAVE/LOAD HELPERS
# ============================================================================

def get_extended_save_path(slot_name: str) -> str:
    """Get path for extended save data"""
    from pathlib import Path
    save_dir = Path("saves")
    save_dir.mkdir(exist_ok=True)
    return str(save_dir / f"{slot_name}_extended.json")


def save_extended_data(slot_name: str, data: Dict[str, Any]) -> bool:
    """Save extended CLI data to companion file"""
    import json
    try:
        path = get_extended_save_path(slot_name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Warning: Could not save extended data: {e}")
        return False


def load_extended_data(slot_name: str) -> Optional[Dict[str, Any]]:
    """Load extended CLI data from companion file"""
    import json
    try:
        path = get_extended_save_path(slot_name)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load extended data: {e}")
        return None


# ============================================================================
# CLI CLASS
# ============================================================================

class CLI:
    """Main command line interface for Cage Dynasty."""
    
    def __init__(self):
        self.game_state: Optional[GameState] = None
        self.running = True
        self.in_game = False
        
        # Extended fighter data (full attributes)
        self.fighter_data: Dict[str, FighterFullData] = {}
        
        # System references
        self._training_system = None
        self._matchmaking_engine = None
        self._world_simulation = None
        self._fight_simulator_available = False
        
        # New systems (initialized in _initialize_systems)
        self._aging_system = None
        self._injury_system = None
        self._rivalry_system = None
        self._watchlist = None
        self._coach_system = None

        # Initialize economy system
        if ECONOMY_AVAILABLE:
            try:
                self._economy_manager = create_economy_manager()
                self._initialize_camp_finances()
            except Exception as e:
                self._economy_manager = None
        
        # Fight offers and scheduling
        self.fight_offers: List[FightOffer] = []
        self.player_scheduled_fights: List[Dict[str, Any]] = []
        
        # Fighter cooldowns (fighter_id -> weeks remaining)
        self._fighter_cooldowns: Dict[str, int] = {}
        
        # Event history
        self.completed_events: List[CompletedEvent] = []
        self.all_fight_results: Dict[str, FightResult] = {}  # fight_id -> result
        
        # AI Fight System
        self.ai_scheduled_fights: List[Dict[str, Any]] = []  # Upcoming AI fights
        self.next_event_number: int = 1
        
        # News
        self.news_feed: List[NewsItem] = []
        self.max_news_items = 100
        
        # Fight history for matchmaking
        self.fight_history: List[Any] = []
        
        # AI Behavior - Personality storage
        self._fighter_personalities: Dict[str, Any] = {}
        self._ai_decision_engine = None
        if AI_BEHAVIOR_AVAILABLE:
            try:
                self._ai_decision_engine = AIDecisionEngine()
            except:
                pass
        
        # Rankings system
        self._rankings_system = None
        if RANKINGS_AVAILABLE:
            try:
                self._rankings_system = RankingsSystem()
            except:
                pass
        
        # Economy system
        self._economy_manager = None  # EconomyManager instance
    
    # -------------------------------------------------------------------------
    # System Initialization
    # -------------------------------------------------------------------------
    
    def _initialize_systems(self) -> None:
        """Initialize all game systems"""
        try:
            from systems.training import TrainingSystem
            self._training_system = TrainingSystem()
        except ImportError:
            self._training_system = None
        
        try:
            from systems.matchmaking import MatchmakingEngine
            self._matchmaking_engine = MatchmakingEngine()
            self._populate_matchmaking_engine()
        except ImportError:
            self._matchmaking_engine = None
        
        # Initialize rankings system
        if RANKINGS_AVAILABLE and self._rankings_system:
            self._populate_rankings_system()
        
        # Initialize coaches for all camps
        if COACHES_AVAILABLE and self._coach_system:
            self._initialize_coaches()
        
        try:
            from simulation.world import WorldSimulation
            self._world_simulation = WorldSimulation(self.game_state.calendar)
            self._setup_world_simulation()
        except ImportError:
            self._world_simulation = None
        
        try:
            from simulation.fight_integration import NarratedFightSimulator
            self._fight_simulator_available = True
        except ImportError:
            self._fight_simulator_available = False
        
        # Initialize economy system
        if ECONOMY_AVAILABLE:
            try:
                self._economy_manager = create_economy_manager()
                self._initialize_camp_finances()
            except Exception as e:
                self._economy_manager = None
        
        # Initialize aging system
        if AGING_AVAILABLE and AgingSystem:
            try:
                self._aging_system = AgingSystem()
            except Exception:
                self._aging_system = None
        
        # Initialize injury system
        if INJURY_AVAILABLE and InjurySystem:
            try:
                self._injury_system = InjurySystem()
            except Exception:
                self._injury_system = None
        
        # Initialize rivalry system
        if RIVALRY_AVAILABLE and RivalrySystem:
            try:
                self._rivalry_system = RivalrySystem()
            except Exception:
                self._rivalry_system = None
        
        
        # Initialize coach system
        if COACHES_AVAILABLE and CoachSystem:
            try:
                self._coach_system = CoachSystem()
            except Exception:
                self._coach_system = None

        # Initialize watchlist
        if WATCHLIST_AVAILABLE and Watchlist:
            try:
                self._watchlist = create_watchlist(max_entries=100)
            except Exception:
                self._watchlist = None
    
    def _populate_matchmaking_engine(self) -> None:
        """Populate matchmaking engine with fighter data"""
        if not self._matchmaking_engine or not self.game_state:
            return
        # Implementation remains similar to before
        pass
    
    def _initialize_camp_finances(self) -> None:
        """Initialize economy manager with camp data."""
        if not self._economy_manager or not self.game_state:
            return
        
        player_camp = self.game_state.get_player_camp()
        if player_camp:
            # Initialize player camp finances
            state = initialize_camp_finances(
                camp_id=player_camp.camp_id,
                tier=self._get_camp_tier(),
                is_player=True,
                manager=self._economy_manager,
            )
            # Sync with existing balance if different
            if player_camp.balance != state.balance:
                self._economy_manager.set_camp_balance(
                    player_camp.camp_id, 
                    player_camp.balance
                )
        
        # Initialize AI camp finances  
        for camp_id, camp in self.game_state.camps.items():
            if camp_id == getattr(player_camp, 'camp_id', None):
                continue
            initialize_camp_finances(
                camp_id=camp_id,
                tier="LOCAL",
                is_player=False,
                manager=self._economy_manager,
            )
    
    def _initialize_coaches(self) -> None:
        """Initialize coaches for camps that don't have them yet."""
        if not COACHES_AVAILABLE:
            return
        
        if not self.game_state:
            return
        
        # If coach system doesn't exist, create it
        if not self._coach_system:
            try:
                self._coach_system = CoachSystem()
            except:
                return
        
        try:
            # Check if coaches already exist (from world_init)
            existing_coaches = len(self._coach_system._coaches) if hasattr(self._coach_system, '_coaches') else 0
            
            if existing_coaches > 0:
                # Coaches already generated by world_init, don't regenerate
                return
            
            # Generate free agent pool
            self._coach_system.generate_initial_pool(count=30)
            
            player_camp = self.game_state.get_player_camp()
            player_camp_id = player_camp.camp_id if player_camp else None
            
            # Generate coaches for ALL camps (only if not already done)
            for camp_id, camp in self.game_state.camps.items():
                # Skip if camp already has coaches
                existing = self._coach_system.get_camp_coaches(camp_id) if hasattr(self._coach_system, 'get_camp_coaches') else []
                if existing:
                    continue
                
                # Get camp tier
                tier = getattr(camp, 'tier', 'GARAGE')
                if isinstance(tier, str):
                    tier = tier.upper()
                else:
                    tier = tier.value if hasattr(tier, 'value') else 'GARAGE'
                
                # Generate coaches for this camp
                self._coach_system.generate_ai_starting_coaches(camp_id, tier)
            
        except Exception as e:
            pass
    
    def _get_camp_coach_bonus(self, camp_id: str) -> float:
        """Get training bonus multiplier from camp's coaching staff."""
        if not COACHES_AVAILABLE or not self._coach_system:
            return 1.0
        
        try:
            return self._coach_system.get_camp_training_bonus(camp_id)
        except:
            return 1.0
    
    def _get_camp_coaches_display(self, camp_id: str) -> List[Dict[str, Any]]:
        """Get coaches for display."""
        if not COACHES_AVAILABLE or not self._coach_system:
            return []
        
        try:
            coaches = self._coach_system.get_camp_coaches(camp_id)
            result = []
            for coach in coaches:
                result.append({
                    "name": coach.name,
                    "specialty": coach.specialty.value if hasattr(coach.specialty, 'value') else str(coach.specialty),
                    "quality": coach.quality,
                    "stars": coach.quality,
                    "is_head": getattr(coach, 'is_head_coach', False),
                    "salary": getattr(coach, 'weekly_salary', 0),
                })
            return result
        except:
            return []

    def _setup_world_simulation(self) -> None:
        """Set up world simulation"""
        if not self._world_simulation or not self.game_state:
            return
        
        for fighter_id in self.game_state.fighters:
            camp_id = self.game_state.fighters[fighter_id].camp_id
            self._world_simulation.register_fighter(fighter_id, camp_id)
        
        for camp_id in self.game_state.camps:
            self._world_simulation.register_camp(camp_id)
        
        self._world_simulation.set_fight_simulator(self._simulate_fight_callback)
    
    def _simulate_fight_callback(self, scheduled_fight) -> Dict[str, Any]:
        """Callback for fight simulation"""
        f1 = self.game_state.fighters.get(scheduled_fight.fighter1_id)
        f2 = self.game_state.fighters.get(scheduled_fight.fighter2_id)
        
        if not f1 or not f2:
            winner_id = random.choice([scheduled_fight.fighter1_id, scheduled_fight.fighter2_id])
            loser_id = scheduled_fight.fighter2_id if winner_id == scheduled_fight.fighter1_id else scheduled_fight.fighter1_id
            return {
                "winner_id": winner_id,
                "loser_id": loser_id,
                "method": random.choice(["KO", "TKO", "SUB", "DEC"]),
                "round": random.randint(1, scheduled_fight.rounds),
            }
        
        f1_rating = f1.overall_rating
        f2_rating = f2.overall_rating
        
        # Get fight type flags
        is_title = getattr(scheduled_fight, 'is_title_fight', False)
        is_main = getattr(scheduled_fight, 'is_main_event', False)
        
        return self._simple_fight_simulation(
            scheduled_fight.fighter1_id, scheduled_fight.fighter2_id,
            f1.name, f2.name, f1_rating, f2_rating,
            scheduled_fight.rounds,
            is_title_fight=is_title,
            is_main_event=is_main
        )
    
    def _simple_fight_simulation(
        self, f1_id: str, f2_id: str, f1_name: str, f2_name: str,
        f1_rating: int, f2_rating: int, rounds: int,
        is_title_fight: bool = False, is_main_event: bool = False,
        f1_gameplan: Optional[Dict] = None, f2_gameplan: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Simple rating-based fight simulation with trait and gameplan effects.
        
        Uses systems.traits module for modifier calculations.
        Gameplans affect fighting style bonuses.
        """
        # Get full fighter data if available for better simulation
        f1_data = self.fighter_data.get(f1_id)
        f2_data = self.fighter_data.get(f2_id)
        
        # Get traits
        f1_traits = f1_data.traits if f1_data else []
        f2_traits = f2_data.traits if f2_data else []
        
        # Get trait modifiers using the traits module
        f1_mods = get_trait_fight_modifiers(
            f1_traits, is_title_fight=is_title_fight, is_main_event=is_main_event
        )
        f2_mods = get_trait_fight_modifiers(
            f2_traits, is_title_fight=is_title_fight, is_main_event=is_main_event
        )
        
        # Get pressure/counter interaction
        f1_interact, f2_interact = get_pressure_counter_interaction(f1_traits, f2_traits)
        
        # Apply gameplan modifiers if available
        f1_gameplan_bonus = 0
        f2_gameplan_bonus = 0
        f1_ko_bonus = 0.0
        f2_ko_bonus = 0.0
        f1_sub_bonus = 0.0
        f2_sub_bonus = 0.0
        
        if GAMEPLAN_AVAILABLE and f1_gameplan:
            try:
                gp = Gameplan.from_dict(f1_gameplan) if isinstance(f1_gameplan, dict) else f1_gameplan
                gp_mods = get_gameplan_modifiers(gp)
                f1_gameplan_bonus = gp_mods.striking_offense + gp_mods.grappling_offense
                f1_ko_bonus = gp_mods.ko_chance_mod
                f1_sub_bonus = gp_mods.sub_chance_mod
            except:
                pass
        
        if GAMEPLAN_AVAILABLE and f2_gameplan:
            try:
                gp = Gameplan.from_dict(f2_gameplan) if isinstance(f2_gameplan, dict) else f2_gameplan
                gp_mods = get_gameplan_modifiers(gp)
                f2_gameplan_bonus = gp_mods.striking_offense + gp_mods.grappling_offense
                f2_ko_bonus = gp_mods.ko_chance_mod
                f2_sub_bonus = gp_mods.sub_chance_mod
            except:
                pass
        
        # Apply all rating adjustments
        f1_adjusted = f1_rating + f1_mods.rating_adjustment + f1_interact + f1_gameplan_bonus
        f2_adjusted = f2_rating + f2_mods.rating_adjustment + f2_interact + f2_gameplan_bonus
        
        # Calculate win probability with adjusted ratings
        total = f1_adjusted + f2_adjusted
        if total <= 0:
            total = 100
        f1_chance = max(0.1, min(0.9, f1_adjusted / total))  # Cap between 10-90%
        
        # Determine winner
        if random.random() < f1_chance:
            winner_id, loser_id = f1_id, f2_id
            winner_name, loser_name = f1_name, f2_name
            winner_data, loser_data = f1_data, f2_data
            winner_traits, loser_traits = f1_traits, f2_traits
            winner_mods, loser_mods = f1_mods, f2_mods
            winner_ko_bonus, winner_sub_bonus = f1_ko_bonus, f1_sub_bonus
        else:
            winner_id, loser_id = f2_id, f1_id
            winner_name, loser_name = f2_name, f1_name
            winner_data, loser_data = f2_data, f1_data
            winner_traits, loser_traits = f2_traits, f1_traits
            winner_mods, loser_mods = f2_mods, f1_mods
            winner_ko_bonus, winner_sub_bonus = f2_ko_bonus, f2_sub_bonus
        
        # Determine method based on fighter styles and traits
        method_weights = {"KO": 0.20, "TKO": 0.15, "SUB": 0.15, "DEC": 0.50}
        
        if winner_data:
            # Adjust based on winner's strengths
            if winner_data.boxing >= 70 or winner_data.kicks >= 70:
                method_weights["KO"] += 0.10
                method_weights["TKO"] += 0.05
            if winner_data.bjj >= 70:
                method_weights["SUB"] += 0.15
            if winner_data.wrestling >= 70 and winner_data.bjj < 60:
                method_weights["DEC"] += 0.10
        
        # Apply winner's trait effects on method (from module modifiers)
        method_weights["KO"] += winner_mods.ko_chance_mod
        method_weights["SUB"] += winner_mods.sub_chance_mod
        method_weights["DEC"] += winner_mods.dec_chance_mod
        
        # Apply winner's gameplan bonuses
        method_weights["KO"] += winner_ko_bonus
        method_weights["SUB"] += winner_sub_bonus
        
        # Apply loser's defensive trait effects
        method_weights["KO"] += loser_mods.get_kod_mod
        method_weights["KO"] += loser_mods.get_finished_mod * 0.5
        method_weights["SUB"] += loser_mods.get_finished_mod * 0.5
        
        # Ensure no negative weights
        method_weights = {k: max(0.01, v) for k, v in method_weights.items()}
        
        # Normalize weights
        total_weight = sum(method_weights.values())
        method_weights = {k: v/total_weight for k, v in method_weights.items()}
        
        # Select method
        rand = random.random()
        cumulative = 0
        method = "DEC"
        for m, w in method_weights.items():
            cumulative += w
            if rand < cumulative:
                method = m
                break
        
        # Determine round
        if method == "DEC":
            finish_round = rounds
        else:
            # Earlier finishes more likely with bigger skill gap
            skill_gap = abs(f1_rating - f2_rating)
            
            # Fast Starter / Slow Starter affects finish round (use module flags)
            if winner_mods.early_finish_bonus:
                # More likely to finish early
                finish_round = random.randint(1, max(1, (rounds + 1) // 2))
            elif winner_mods.late_finish_bonus:
                # More likely to finish late
                finish_round = random.randint(max(1, rounds // 2), rounds)
            elif skill_gap > 15:
                finish_round = random.randint(1, max(1, rounds - 1))
            else:
                finish_round = random.randint(1, rounds)
        
        # Generate basic stats
        base_strikes = 30 + random.randint(-10, 20)
        
        # Cardio Machine wins more in late rounds (if method is DEC)
        # This is narrative, stats are similar
        
        return {
            "winner_id": winner_id,
            "loser_id": loser_id,
            "winner_name": winner_name,
            "loser_name": loser_name,
            "method": method,
            "round": finish_round,
            "fighter1_strikes": base_strikes + random.randint(-10, 10),
            "fighter2_strikes": base_strikes + random.randint(-10, 10),
            "fighter1_takedowns": random.randint(0, 3),
            "fighter2_takedowns": random.randint(0, 3),
            "winner_traits": winner_traits,
            "loser_traits": loser_traits,
        }
    
    def _narrated_fight_simulation(
        self, f1_id: str, f2_id: str, rounds: int,
        is_title_fight: bool = False, is_main_event: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Full fight simulation with round-by-round commentary.
        
        Uses the sophisticated fight engine for detailed simulation.
        Returns None if fight engine not available or fighters not found.
        """
        if not FIGHT_ENGINE_AVAILABLE:
            return None
        
        # Get fighter data
        f1_data = self.fighter_data.get(f1_id)
        f2_data = self.fighter_data.get(f2_id)
        
        if not f1_data or not f2_data:
            return None
        
        # Convert to fight engine attributes
        f1_attrs = f1_data.to_fight_attributes()
        f2_attrs = f2_data.to_fight_attributes()
        
        if not f1_attrs or not f2_attrs:
            return None
        
        # Create fight config
        if is_title_fight:
            config = FightConfig.championship_fight()
        elif is_main_event:
            config = FightConfig.main_event()
        else:
            config = FightConfig.standard_fight()
        
        if rounds == 5:
            config.scheduled_rounds = 5
        
        # Run the simulation
        try:
            simulator = NarratedFightSimulator(f1_attrs, f2_attrs, config, verbose=False)
            result = simulator.simulate()
        except Exception as e:
            # Fall back to simple simulation on error
            return None
        
        # Convert NarratedFightResult to dict format
        # Map method names
        method_map = {
            "KO (Punches)": "KO",
            "KO (Head Kick)": "KO", 
            "KO (Knee)": "KO",
            "TKO (Punches)": "TKO",
            "TKO (Ground and Pound)": "TKO",
            "TKO (Elbows)": "TKO",
            "TKO (Kicks)": "TKO",
            "TKO (Doctor Stoppage)": "TKO",
            "TKO (Corner Stoppage)": "TKO",
            "Unanimous Decision": "DEC",
            "Split Decision": "DEC",
            "Majority Decision": "DEC",
            "Draw": "DRAW",
        }
        
        method = result.method
        # Extract base method
        if "KO" in method and "TKO" not in method:
            method = "KO"
        elif "TKO" in method:
            method = "TKO"
        elif "Submission" in method or "SUB" in method.upper():
            method = "SUB"
        elif "Decision" in method:
            method = "DEC"
        elif method in method_map:
            method = method_map[method]
        
        # Calculate total stats
        f1_strikes = sum(s.get("sig_strikes_landed", 0) for s in result.fighter1_stats)
        f2_strikes = sum(s.get("sig_strikes_landed", 0) for s in result.fighter2_stats)
        f1_takedowns = sum(s.get("td_landed", 0) for s in result.fighter1_stats)
        f2_takedowns = sum(s.get("td_landed", 0) for s in result.fighter2_stats)
        f1_sub_attempts = sum(s.get("sub_att", 0) for s in result.fighter1_stats)
        f2_sub_attempts = sum(s.get("sub_att", 0) for s in result.fighter2_stats)
        
        return {
            "winner_id": result.winner_id,
            "loser_id": result.loser_id,
            "winner_name": result.winner_name,
            "loser_name": result.loser_name,
            "method": method,
            "round": result.finish_round if result.finish_round else rounds,
            "time": result.finish_time if result.finish_time else "5:00",
            "fighter1_strikes": f1_strikes,
            "fighter2_strikes": f2_strikes,
            "fighter1_takedowns": f1_takedowns,
            "fighter2_takedowns": f2_takedowns,
            "fighter1_sub_attempts": f1_sub_attempts,
            "fighter2_sub_attempts": f2_sub_attempts,
            "winner_traits": f1_data.traits if result.winner_id == f1_id else f2_data.traits,
            "loser_traits": f2_data.traits if result.winner_id == f1_id else f1_data.traits,
            # Full commentary data
            "full_commentary": result.full_commentary,
            "fight_narrative": result.fight_narrative,
            "round_summaries": result.round_summaries,
            "key_moments": [m.get("description", str(m)) for m in result.key_moments],
            "fighter1_round_stats": result.fighter1_stats,
            "fighter2_round_stats": result.fighter2_stats,
            "judge_scores": result.judge_scores,
            "decision_type": result.decision_type or "",
            "fight_of_night": result.fight_of_night,
            "performance_bonus": result.performance_bonus,
            "fighter1_final_health": result.fighter1_final_health,
            "fighter2_final_health": result.fighter2_final_health,
        }
    
    # -------------------------------------------------------------------------
    # Fighter Data Management
    # -------------------------------------------------------------------------
    
    def _create_full_fighter_data(self, fighter_id: str) -> Optional[FighterFullData]:
        """Create or retrieve full fighter data"""
        if fighter_id in self.fighter_data:
            return self.fighter_data[fighter_id]
        
        # Get basic record from game state
        if fighter_id not in self.game_state.fighters:
            return None
        
        basic = self.game_state.fighters[fighter_id]
        
        # Try to get generated attributes
        try:
            from simulation.generator import generate_fighter, COUNTRIES
            # For existing fighters, generate attributes around their overall rating
            country = random.choice(COUNTRIES)
            gen = generate_fighter(
                name=basic.name,
                country=country,
                weight_class=basic.weight_class,
                overall_rating=basic.overall_rating,
            )
            
            full_data = FighterFullData(
                fighter_id=fighter_id,
                name=basic.name,
                nickname=basic.nickname,
                weight_class=basic.weight_class,
                camp_id=basic.camp_id,
                contract_id=basic.contract_id,
                is_champion=basic.is_champion,
                is_active=basic.is_active,
                is_generational=getattr(gen, 'is_generational', False),
                country=country,
                age=random.randint(22, 35),
                strength=gen.strength,
                speed=gen.speed,
                cardio=gen.cardio,
                chin=gen.chin,
                boxing=gen.boxing,
                kicks=gen.kicks,
                clinch_striking=gen.clinch_striking,
                striking_defense=gen.striking_defense,
                wrestling=gen.wrestling,
                bjj=gen.bjj,
                takedown_defense=gen.takedown_defense,
                heart=gen.heart,
                fight_iq=gen.fight_iq,
                composure=gen.composure,
                wins=basic.wins,
                losses=basic.losses,
                draws=basic.draws,
                ko_wins=basic.ko_wins,
                sub_wins=basic.sub_wins,
            )
            # Infer style from generated attributes
            full_data.fighting_style = self._infer_fighting_style(full_data)
            # Assign random traits
            self._assign_traits(full_data)
            
        except ImportError:
            # Fallback: generate random attributes around the overall
            base = basic.overall_rating
            variance = 10
            countries = ["United States", "Brazil", "Russia", "Japan", "Mexico", 
                        "United Kingdom", "Canada", "Netherlands", "Thailand", "Ireland"]
            
            full_data = FighterFullData(
                fighter_id=fighter_id,
                name=basic.name,
                nickname=basic.nickname,
                weight_class=basic.weight_class,
                camp_id=basic.camp_id,
                contract_id=basic.contract_id,
                is_champion=basic.is_champion,
                is_active=basic.is_active,
                country=random.choice(countries),
                age=random.randint(22, 35),
                strength=max(1, min(100, base + random.randint(-variance, variance))),
                speed=max(1, min(100, base + random.randint(-variance, variance))),
                cardio=max(1, min(100, base + random.randint(-variance, variance))),
                chin=max(1, min(100, base + random.randint(-variance, variance))),
                boxing=max(1, min(100, base + random.randint(-variance, variance))),
                kicks=max(1, min(100, base + random.randint(-variance, variance))),
                clinch_striking=max(1, min(100, base + random.randint(-variance, variance) - 5)),
                striking_defense=max(1, min(100, base + random.randint(-variance, variance))),
                wrestling=max(1, min(100, base + random.randint(-variance, variance))),
                bjj=max(1, min(100, base + random.randint(-variance, variance))),
                takedown_defense=max(1, min(100, base + random.randint(-variance, variance))),
                heart=max(1, min(100, base + random.randint(-variance, variance))),
                fight_iq=max(1, min(100, base + random.randint(-variance, variance))),
                composure=max(1, min(100, base + random.randint(-variance, variance))),
                wins=basic.wins,
                losses=basic.losses,
                draws=basic.draws,
                ko_wins=basic.ko_wins,
                sub_wins=basic.sub_wins,
            )
            # Infer style from generated attributes
            full_data.fighting_style = self._infer_fighting_style(full_data)
            # Assign random traits
            self._assign_traits(full_data)
        
        self.fighter_data[fighter_id] = full_data
        return full_data
    
    def _sync_fighter_record(self, fighter_id: str) -> None:
        """Sync full data back to game state"""
        if fighter_id not in self.fighter_data:
            return
        if fighter_id not in self.game_state.fighters:
            return
        
        full = self.fighter_data[fighter_id]
        basic = self.game_state.fighters[fighter_id]
        
        # Sync record
        basic.wins = full.wins
        basic.losses = full.losses
        basic.draws = full.draws
        basic.ko_wins = full.ko_wins
        basic.sub_wins = full.sub_wins
        basic.is_champion = full.is_champion
        basic.overall_rating = full.overall_rating
    
    def _get_style_string(self, style) -> str:
        """Convert FightingStyle enum or string to string."""
        if style is None:
            return "Balanced"
        if hasattr(style, 'value'):
            # It's an enum, get its value
            return str(style.value)
        if hasattr(style, 'name'):
            # It might be an enum, try name
            return str(style.name).replace('_', ' ').title()
        return str(style)
    
    def _infer_fighting_style(self, fighter_data: FighterFullData) -> str:
        """Infer fighting style from attributes"""
        boxing = fighter_data.boxing
        kicks = fighter_data.kicks
        wrestling = fighter_data.wrestling
        bjj = fighter_data.bjj
        clinch = fighter_data.clinch_striking
        
        # Check for dominant style
        striking_avg = (boxing + kicks) / 2
        grappling_avg = (wrestling + bjj) / 2
        
        # Strong BJJ focus
        if bjj >= 70 and bjj > wrestling + 10:
            return "Brazilian Jiu-Jitsu"
        
        # Strong wrestling focus
        if wrestling >= 70 and wrestling > bjj + 10:
            return "Wrestling"
        
        # Sambo style (good at both)
        if wrestling >= 65 and bjj >= 65:
            return "Sambo"
        
        # Muay Thai (kicks + clinch)
        if kicks >= 70 and clinch >= 60:
            return "Muay Thai"
        
        # Kickboxing (balanced striking)
        if kicks >= 65 and boxing >= 65:
            return "Kickboxing"
        
        # Pure boxer
        if boxing >= 70 and boxing > kicks + 15:
            return "Boxing"
        
        # Karate (kicks dominant)
        if kicks >= 70 and kicks > boxing + 10:
            return "Karate"
        
        # Judo (wrestling + bjj but more throws)
        if wrestling >= 60 and bjj >= 60 and clinch >= 55:
            return "Judo"
        
        # Default
        return "MMA Hybrid"
    
    def _assign_traits(self, fighter_data: FighterFullData) -> None:
        """Assign random traits to a fighter based on their attributes.
        
        Uses the traits module for assignment logic and stat modifiers.
        """
        # Build attributes dict for the traits module
        fighter_attrs = {
            "boxing": fighter_data.boxing,
            "kicks": fighter_data.kicks,
            "wrestling": fighter_data.wrestling,
            "bjj": fighter_data.bjj,
            "chin": fighter_data.chin,
            "cardio": fighter_data.cardio,
            "speed": fighter_data.speed,
            "striking_defense": fighter_data.striking_defense,
            "age": fighter_data.age,
        }
        
        # Use module function for weighted trait assignment
        selected_traits = assign_traits(fighter_attrs)
        fighter_data.traits = selected_traits
        
        # Apply stat modifiers from traits
        modifiers = get_stat_modifiers(selected_traits)
        for stat, mod in modifiers.items():
            if hasattr(fighter_data, stat):
                old_val = getattr(fighter_data, stat)
                new_val = max(1, min(100, old_val + mod))
                setattr(fighter_data, stat, new_val)
    
    # -------------------------------------------------------------------------
    # AI Fight System
    # -------------------------------------------------------------------------
    
    def _get_available_ai_fighters(self, weight_class: str) -> List[str]:
        """Get AI fighters available to fight (not scheduled, not injured, not on cooldown)"""
        player_camp = self.game_state.get_player_camp()
        player_camp_id = player_camp.camp_id if player_camp else None
        
        # Get all scheduled fighter IDs
        scheduled_ids = set()
        for fight in self.player_scheduled_fights:
            scheduled_ids.add(fight.get("fighter1_id"))
            scheduled_ids.add(fight.get("fighter2_id"))
        for fight in self.ai_scheduled_fights:
            scheduled_ids.add(fight.get("fighter1_id"))
            scheduled_ids.add(fight.get("fighter2_id"))
        
        available = []
        for f in self.game_state.fighters.values():
            if f.weight_class != weight_class:
                continue
            if not f.is_active:
                continue
            if f.camp_id == player_camp_id:
                continue  # Player fighters handled separately
            if f.fighter_id in scheduled_ids:
                continue
            # Check cooldown
            if f.fighter_id in self._fighter_cooldowns and self._fighter_cooldowns[f.fighter_id] > 0:
                continue
            available.append(f.fighter_id)
        
        return available
    
    def _schedule_ai_event(self, weeks_away: int, event_name: str) -> None:
        """Schedule a full AI fight card"""
        weight_classes = list(self.game_state.divisions.keys())
        fights_to_schedule = random.randint(8, 12)  # 8-12 fights per card
        
        scheduled_this_event = set()
        
        for _ in range(fights_to_schedule):
            # Pick a random weight class
            wc = random.choice(weight_classes)
            available = self._get_available_ai_fighters(wc)
            
            # Remove fighters already on this card
            available = [f for f in available if f not in scheduled_this_event]
            
            if len(available) < 2:
                continue
            
            # Pick two fighters with similar ratings
            random.shuffle(available)
            f1_id = available[0]
            f1 = self.game_state.fighters.get(f1_id)
            if not f1:
                continue
            
            # Find opponent with similar rating
            best_opponent = None
            best_diff = 100
            for opp_id in available[1:]:
                opp = self.game_state.fighters.get(opp_id)
                if opp and opp.camp_id != f1.camp_id:  # Different camps
                    diff = abs(f1.overall_rating - opp.overall_rating)
                    if diff < best_diff and diff <= 20:  # Within 20 rating
                        best_diff = diff
                        best_opponent = opp_id
            
            if not best_opponent:
                continue
            
            f2 = self.game_state.fighters.get(best_opponent)
            if not f2:
                continue
            
            # Check for title fight
            is_title = f1.is_champion or f2.is_champion
            rounds = 5 if is_title else 3
            
            # Generate AI gameplans using module functions
            f1_gameplan = None
            f2_gameplan = None
            if GAMEPLAN_AVAILABLE:
                f1_data = self.fighter_data.get(f1_id) or self._create_full_fighter_data(f1_id)
                f2_data = self.fighter_data.get(best_opponent) or self._create_full_fighter_data(best_opponent)
                
                if f1_data and f2_data:
                    f1_stats = {
                        "boxing": f1_data.boxing, "kicks": f1_data.kicks,
                        "wrestling": f1_data.wrestling, "bjj": f1_data.bjj,
                        "power": getattr(f1_data, 'power', 50), "cardio": f1_data.cardio,
                    }
                    f2_stats = {
                        "boxing": f2_data.boxing, "kicks": f2_data.kicks,
                        "wrestling": f2_data.wrestling, "bjj": f2_data.bjj,
                        "power": getattr(f2_data, 'power', 50), "cardio": f2_data.cardio,
                    }
                    f1_gameplan = generate_ai_gameplan(f1_stats, f2_stats, is_title, rounds)
                    f2_gameplan = generate_ai_gameplan(f2_stats, f1_stats, is_title, rounds)
            
            fight = {
                "fighter1_id": f1_id,
                "fighter2_id": best_opponent,
                "fighter1_name": f1.name,
                "fighter2_name": f2.name,
                "weight_class": wc,
                "is_title_fight": is_title,
                "is_main_event": is_title,
                "rounds": rounds,
                "weeks_until": weeks_away,
                "event_name": event_name,
            }
            
            # Store AI gameplans
            if f1_gameplan:
                fight["fighter1_gameplan"] = f1_gameplan.to_dict() if hasattr(f1_gameplan, 'to_dict') else None
            if f2_gameplan:
                fight["fighter2_gameplan"] = f2_gameplan.to_dict() if hasattr(f2_gameplan, 'to_dict') else None
            
            self.ai_scheduled_fights.append(fight)
            scheduled_this_event.add(f1_id)
            scheduled_this_event.add(best_opponent)
            
            # Announce bigger fights
            if is_title or (f1.overall_rating >= 75 and f2.overall_rating >= 75):
                tag = " for the title!" if is_title else ""
                self.news_feed.insert(0, NewsItem(
                    headline=f"SIGNED: {f1.name} vs {f2.name}{tag}",
                    category="fight",
                    week=self.game_state.week_number,
                ))
    
    def _process_ai_fights(self) -> List[str]:
        """Process AI fights happening this week"""
        events = []
        completed = []
        
        # Group fights by event
        events_this_week: Dict[str, List[Dict]] = {}
        
        for i, fight in enumerate(self.ai_scheduled_fights):
            if fight.get("weeks_until", 0) <= 1:
                event_name = fight.get("event_name", "DFC Fight Night")
                if event_name not in events_this_week:
                    events_this_week[event_name] = []
                events_this_week[event_name].append((i, fight))
        
        # Process each event
        for event_name, fights in events_this_week.items():
            if not fights:
                continue
            
            # Create event
            event_id = f"event_{self.game_state.week_number}_{event_name.replace(' ', '_')}"
            event = CompletedEvent(
                event_id=event_id,
                event_name=event_name,
                week=self.game_state.week_number,
            )
            
            event_results = []
            
            for idx, fight in fights:
                result = self._execute_ai_fight(fight, event_id, event_name)
                if result:
                    event.add_fight(result["fight_result"])
                    event_results.append(result)
                    completed.append(idx)
            
            if event.fights:
                self.completed_events.append(event)
                
                # Summary for week
                finishes = event.knockouts + event.submissions
                events.append(f"   {event_name}: {event.total_fights} fights ({finishes} finishes)")
                
                # Highlight main event
                if event_results:
                    main = event_results[-1]  # Last fight is usually main
                    headline = main.get("headline", "")
                    if main.get("is_title", False):
                        events.append(f"      {headline}")
                    elif main.get("is_finish", False):
                        events.append(f"     * {headline}")
        
        # Remove completed fights (reverse order to preserve indices)
        for i in sorted(completed, reverse=True):
            self.ai_scheduled_fights.pop(i)
        
        # Decrement weeks for remaining AI fights
        for fight in self.ai_scheduled_fights:
            if "weeks_until" in fight:
                fight["weeks_until"] = max(0, fight["weeks_until"] - 1)
        
        return events
    
    def _execute_ai_fight(self, fight: Dict[str, Any], event_id: str, event_name: str) -> Optional[Dict[str, Any]]:
        """Execute a single AI fight.
        
        Note: AI fights use simple simulation for performance (many fights per week).
        Player fights use the full narrated engine for immersive experience.
        """
        import uuid
        
        f1_id = fight.get("fighter1_id")
        f2_id = fight.get("fighter2_id")
        f1_name = fight.get("fighter1_name", "Fighter 1")
        f2_name = fight.get("fighter2_name", "Fighter 2")
        is_title = fight.get("is_title_fight", False)
        rounds = fight.get("rounds", 3)
        weight_class = fight.get("weight_class", "")
        
        # Get or create fighter data
        f1_data = self._create_full_fighter_data(f1_id)
        f2_data = self._create_full_fighter_data(f2_id)
        
        f1_rating = f1_data.overall_rating if f1_data else 50
        f2_rating = f2_data.overall_rating if f2_data else 50
        
        is_main = fight.get("is_main_event", False)
        
        # Get AI gameplans if stored
        f1_gameplan = fight.get("fighter1_gameplan")
        f2_gameplan = fight.get("fighter2_gameplan")
        
        # Simulate with gameplans
        sim_result = self._simple_fight_simulation(
            f1_id, f2_id, f1_name, f2_name, f1_rating, f2_rating, rounds,
            is_title_fight=is_title,
            is_main_event=is_main,
            f1_gameplan=f1_gameplan,
            f2_gameplan=f2_gameplan
        )
        
        winner_id = sim_result["winner_id"]
        loser_id = sim_result["loser_id"]
        method = sim_result["method"]
        finish_round = sim_result["round"]
        winner_name = sim_result["winner_name"]
        loser_name = sim_result["loser_name"]
        
        # Create fight result
        fight_id = f"fight_{uuid.uuid4().hex[:8]}"
        result = FightResult(
            fight_id=fight_id,
            event_id=event_id,
            event_name=event_name,
            week=self.game_state.week_number,
            fighter1_id=f1_id,
            fighter1_name=f1_name,
            fighter2_id=f2_id,
            fighter2_name=f2_name,
            winner_id=winner_id,
            winner_name=winner_name,
            loser_id=loser_id,
            loser_name=loser_name,
            method=method,
            round_finished=finish_round,
            weight_class=weight_class,
            is_title_fight=is_title,
            is_main_event=fight.get("is_main_event", False),
            rounds_scheduled=rounds,
            fighter1_strikes=sim_result.get("fighter1_strikes", 0),
            fighter2_strikes=sim_result.get("fighter2_strikes", 0),
            fighter1_takedowns=sim_result.get("fighter1_takedowns", 0),
            fighter2_takedowns=sim_result.get("fighter2_takedowns", 0),
        )
        
        # Generate fight summary
        if method == "KO":
            result.fight_summary = f"{winner_name} knocked out {loser_name} with a devastating strike in round {finish_round}."
            result.key_moments = [f"Round {finish_round}: {winner_name} lands the knockout blow"]
        elif method == "TKO":
            result.fight_summary = f"{winner_name} stopped {loser_name} by TKO in round {finish_round}."
            result.key_moments = [f"Round {finish_round}: Referee stoppage"]
        elif method == "SUB":
            subs = ["rear naked choke", "guillotine", "armbar", "triangle", "kimura"]
            sub_type = random.choice(subs)
            result.fight_summary = f"{winner_name} submitted {loser_name} with a {sub_type} in round {finish_round}."
            result.key_moments = [f"Round {finish_round}: {winner_name} locks in the {sub_type}"]
        else:
            result.fight_summary = f"{winner_name} outpointed {loser_name} over {rounds} rounds."
            result.key_moments = ["Fight goes to the scorecards"]
        
        # Store result
        self.all_fight_results[fight_id] = result
        
        # Add to week fight results for display in recap
        if hasattr(self, '_week_fight_results'):
            self._week_fight_results.append({
                "winner_name": winner_name,
                "loser_name": loser_name,
                "winner_id": winner_id,
                "loser_id": loser_id,
                "method": method,
                "round": finish_round,
                "is_title_fight": is_title,
                "is_main_event": fight.get("is_main_event", False),
                "is_co_main": fight.get("is_co_main", False),
                "weight_class": weight_class,
                "event_name": event_name,
                "card_position": fight.get("card_position", 0),
            })
        
        # Update fighter records in fighter_data
        if winner_id in self.fighter_data:
            self.fighter_data[winner_id].wins += 1
            self.fighter_data[winner_id].win_streak += 1
            self.fighter_data[winner_id].lose_streak = 0
            if method in ["KO", "TKO"]:
                self.fighter_data[winner_id].ko_wins += 1
            elif method == "SUB":
                self.fighter_data[winner_id].sub_wins += 1
            self._sync_fighter_record(winner_id)
        
        # Clear cooldown on win (for any fighter)
        if winner_id in self._fighter_cooldowns:
            del self._fighter_cooldowns[winner_id]
        
        if loser_id in self.fighter_data:
            self.fighter_data[loser_id].losses += 1
            self.fighter_data[loser_id].lose_streak += 1
            self.fighter_data[loser_id].win_streak = 0
            if method in ["KO", "TKO"]:
                self.fighter_data[loser_id].ko_losses += 1
            elif method == "SUB":
                self.fighter_data[loser_id].sub_losses += 1
            self._sync_fighter_record(loser_id)
            # Apply cooldown: 4 weeks + 2 per additional loss in streak
            lose_streak = self.fighter_data[loser_id].lose_streak
            cooldown_weeks = 4 + (lose_streak - 1) * 2
            self._fighter_cooldowns[loser_id] = cooldown_weeks
        else:
            # AI fighter not in fighter_data - apply base cooldown
            # Check existing cooldown to estimate streak
            existing_cooldown = self._fighter_cooldowns.get(loser_id, 0)
            if existing_cooldown > 0:
                # Was already on cooldown, they lost again - extend it
                cooldown_weeks = existing_cooldown + 2
            else:
                # First loss or fresh fighter
                cooldown_weeks = 4
            self._fighter_cooldowns[loser_id] = cooldown_weeks
        
        # --- PAY FIGHT PURSES ---
        if hasattr(self, '_economy_manager') and self._economy_manager and ECONOMY_AVAILABLE:
            player_camp = self.game_state.get_player_camp()
            if player_camp:
                is_finish = method in ["KO", "TKO", "SUB"]
                
                # Pay winner if player's fighter
                if winner_id in self.fighter_data:
                    winner_data = self.fighter_data[winner_id]
                    if winner_data.camp_id == player_camp.camp_id:
                        winner_rank = None
                        if winner_id in self.game_state.fighters:
                            winner_rank = getattr(self.game_state.fighters[winner_id], 'rank', None)
                        
                        earnings = self._economy_manager.pay_fight_purse(
                            camp_id=player_camp.camp_id,
                            fighter_id=winner_id,
                            fighter_name=winner_name,
                            won=True,
                            rank=winner_rank,
                            is_champion=getattr(winner_data, 'is_champion', False),
                            total_fights=winner_data.wins + winner_data.losses,
                            is_title_fight=is_title,
                            is_main_event=is_main,
                            is_finish=is_finish,
                            method=method,
                        )
                        player_camp._balance = self._economy_manager.get_balance(player_camp.camp_id)
                        
                        # Offer sponsorship after win
                        self._offer_sponsorship_after_win(winner_id, winner_name, is_title)
                
                # Pay loser if player's fighter  
                if loser_id in self.fighter_data:
                    loser_data = self.fighter_data[loser_id]
                    if loser_data.camp_id == player_camp.camp_id:
                        loser_rank = None
                        if loser_id in self.game_state.fighters:
                            loser_rank = getattr(self.game_state.fighters[loser_id], 'rank', None)
                        
                        earnings = self._economy_manager.pay_fight_purse(
                            camp_id=player_camp.camp_id,
                            fighter_id=loser_id,
                            fighter_name=loser_name,
                            won=False,
                            rank=loser_rank,
                            is_champion=getattr(loser_data, 'is_champion', False),
                            total_fights=loser_data.wins + loser_data.losses,
                            is_title_fight=is_title,
                            is_main_event=is_main,
                        )
                        player_camp._balance = self._economy_manager.get_balance(player_camp.camp_id)

        
        # Handle title changes
        if is_title:
            # Check if champion lost
            f1_rec = self.game_state.fighters.get(f1_id)
            f2_rec = self.game_state.fighters.get(f2_id)
            
            if f1_rec and f1_rec.is_champion and loser_id == f1_id:
                f1_rec.is_champion = False
                if f2_rec:
                    f2_rec.is_champion = True
                if f1_id in self.fighter_data:
                    self.fighter_data[f1_id].is_champion = False
                if f2_id in self.fighter_data:
                    self.fighter_data[f2_id].is_champion = True
                # Update division
                if weight_class in self.game_state.divisions:
                    self.game_state.divisions[weight_class].champion_id = winner_id
            elif f2_rec and f2_rec.is_champion and loser_id == f2_id:
                f2_rec.is_champion = False
                if f1_rec:
                    f1_rec.is_champion = True
                if f2_id in self.fighter_data:
                    self.fighter_data[f2_id].is_champion = False
                if f1_id in self.fighter_data:
                    self.fighter_data[f1_id].is_champion = True
                if weight_class in self.game_state.divisions:
                    self.game_state.divisions[weight_class].champion_id = winner_id
        
        # Generate headline
        if method == "DEC":
            headline = f"{winner_name} def. {loser_name} by decision"
        else:
            headline = f"{winner_name} finishes {loser_name} ({method} R{finish_round})"
        
        # Add to news
        category = "title" if is_title else "fight"
        self.news_feed.insert(0, NewsItem(
            headline=headline,
            category=category,
            week=self.game_state.week_number,
        ))
        
        return {
            "fight_result": result,
            "headline": headline,
            "is_title": is_title,
            "is_finish": method != "DEC",
        }
    
    def _ensure_ai_events_scheduled(self) -> None:
        """Ensure there are always AI events scheduled"""
        # Count events in next 8 weeks
        upcoming_weeks = set()
        for fight in self.ai_scheduled_fights:
            weeks = fight.get("weeks_until", 0)
            if weeks > 0:
                upcoming_weeks.add(weeks)
        
        # Schedule events to fill gaps
        for week in [2, 4, 6, 8]:
            if week not in upcoming_weeks:
                # Check if player has fight this week
                player_fight_week = any(
                    f.get("weeks_until") == week for f in self.player_scheduled_fights
                )
                
                event_name = f"DFC Fight Night {self.next_event_number}"
                self.next_event_number += 1
                self._schedule_ai_event(week, event_name)
    
    # -------------------------------------------------------------------------
    # Extended Save/Load
    # -------------------------------------------------------------------------
    
    def _save_extended_data(self, slot_name: str) -> bool:
        """Save all extended CLI data"""
        data = {
            "version": 2,  # Updated version for AI fights
            "fighter_data": {
                fid: fd.to_dict() for fid, fd in self.fighter_data.items()
            },
            "completed_events": [
                {
                    "event_id": e.event_id,
                    "event_name": e.event_name,
                    "week": e.week,
                    "location": e.location,
                    "total_fights": e.total_fights,
                    "finishes": e.finishes,
                    "knockouts": e.knockouts,
                    "submissions": e.submissions,
                    "decisions": e.decisions,
                    "fights": [
                        {
                            "fight_id": f.fight_id,
                            "event_id": f.event_id,
                            "event_name": f.event_name,
                            "week": f.week,
                            "fighter1_id": f.fighter1_id,
                            "fighter1_name": f.fighter1_name,
                            "fighter2_id": f.fighter2_id,
                            "fighter2_name": f.fighter2_name,
                            "winner_id": f.winner_id,
                            "winner_name": f.winner_name,
                            "loser_id": f.loser_id,
                            "loser_name": f.loser_name,
                            "method": f.method,
                            "round_finished": f.round_finished,
                            "time_finished": f.time_finished,
                            "weight_class": f.weight_class,
                            "is_title_fight": f.is_title_fight,
                            "is_main_event": f.is_main_event,
                            "rounds_scheduled": f.rounds_scheduled,
                            "fighter1_strikes": f.fighter1_strikes,
                            "fighter2_strikes": f.fighter2_strikes,
                            "fighter1_takedowns": f.fighter1_takedowns,
                            "fighter2_takedowns": f.fighter2_takedowns,
                            "fighter1_sub_attempts": f.fighter1_sub_attempts,
                            "fighter2_sub_attempts": f.fighter2_sub_attempts,
                            "fight_summary": f.fight_summary,
                            "key_moments": f.key_moments,
                        }
                        for f in e.fights
                    ]
                }
                for e in self.completed_events
            ],
            "fight_offers": [
                {
                    "offer_id": o.offer_id,
                    "fighter_id": o.fighter_id,
                    "fighter_name": o.fighter_name,
                    "opponent_id": o.opponent_id,
                    "opponent_name": o.opponent_name,
                    "opponent_record": o.opponent_record,
                    "opponent_rating": o.opponent_rating,
                    "weight_class": o.weight_class,
                    "event_name": o.event_name,
                    "event_date": o.event_date,
                    "weeks_away": o.weeks_away,
                    "purse": o.purse,
                    "is_title_fight": o.is_title_fight,
                    "is_main_event": o.is_main_event,
                    "matchup_quality": o.matchup_quality,
                }
                for o in self.fight_offers
            ],
            "player_scheduled_fights": self.player_scheduled_fights,
            "ai_scheduled_fights": self.ai_scheduled_fights,
            "fighter_cooldowns": self._fighter_cooldowns,
            "next_event_number": self.next_event_number,
            "news_feed": [
                {
                    "headline": n.headline,
                    "details": n.details,
                    "category": n.category,
                    "week": n.week,
                }
                for n in self.news_feed
            ],
            "economy_data": self._economy_manager.to_dict() if self._economy_manager else {},
            # New systems data
            "watchlist_data": self._watchlist.to_dict() if self._watchlist else {},
            "injury_data": self._injury_system.to_dict() if self._injury_system else {},
            "rivalry_data": self._rivalry_system.to_dict() if self._rivalry_system else {},
            "aging_data": self._aging_system.to_dict() if self._aging_system else {},
        }
        
        return save_extended_data(slot_name, data)
    
    def _load_extended_data(self, slot_name: str) -> bool:
        """Load all extended CLI data"""
        data = load_extended_data(slot_name)
        if not data:
            return False
        
        try:
            # Load fighter data
            self.fighter_data = {}
            for fid, fd_dict in data.get("fighter_data", {}).items():
                self.fighter_data[fid] = FighterFullData.from_dict(fd_dict)
            
            # Load completed events
            self.completed_events = []
            for e_dict in data.get("completed_events", []):
                event = CompletedEvent(
                    event_id=e_dict.get("event_id", ""),
                    event_name=e_dict.get("event_name", ""),
                    week=e_dict.get("week", 0),
                    location=e_dict.get("location", ""),
                )
                event.total_fights = e_dict.get("total_fights", 0)
                event.finishes = e_dict.get("finishes", 0)
                event.knockouts = e_dict.get("knockouts", 0)
                event.submissions = e_dict.get("submissions", 0)
                event.decisions = e_dict.get("decisions", 0)
                
                for f_dict in e_dict.get("fights", []):
                    fight = FightResult(
                        fight_id=f_dict.get("fight_id", ""),
                        event_id=f_dict.get("event_id", ""),
                        event_name=f_dict.get("event_name", ""),
                        week=f_dict.get("week", 0),
                        fighter1_id=f_dict.get("fighter1_id", ""),
                        fighter1_name=f_dict.get("fighter1_name", ""),
                        fighter2_id=f_dict.get("fighter2_id", ""),
                        fighter2_name=f_dict.get("fighter2_name", ""),
                        winner_id=f_dict.get("winner_id", ""),
                        winner_name=f_dict.get("winner_name", ""),
                        loser_id=f_dict.get("loser_id", ""),
                        loser_name=f_dict.get("loser_name", ""),
                        method=f_dict.get("method", ""),
                        round_finished=f_dict.get("round_finished", 1),
                        time_finished=f_dict.get("time_finished", "5:00"),
                        weight_class=f_dict.get("weight_class", ""),
                        is_title_fight=f_dict.get("is_title_fight", False),
                        is_main_event=f_dict.get("is_main_event", False),
                        rounds_scheduled=f_dict.get("rounds_scheduled", 3),
                        fighter1_strikes=f_dict.get("fighter1_strikes", 0),
                        fighter2_strikes=f_dict.get("fighter2_strikes", 0),
                        fighter1_takedowns=f_dict.get("fighter1_takedowns", 0),
                        fighter2_takedowns=f_dict.get("fighter2_takedowns", 0),
                        fighter1_sub_attempts=f_dict.get("fighter1_sub_attempts", 0),
                        fighter2_sub_attempts=f_dict.get("fighter2_sub_attempts", 0),
                        fight_summary=f_dict.get("fight_summary", ""),
                        key_moments=f_dict.get("key_moments", []),
                    )
                    event.fights.append(fight)
                    self.all_fight_results[fight.fight_id] = fight
                
                self.completed_events.append(event)
            
            # Load fight offers
            self.fight_offers = []
            for o_dict in data.get("fight_offers", []):
                self.fight_offers.append(FightOffer(
                    offer_id=o_dict.get("offer_id", ""),
                    fighter_id=o_dict.get("fighter_id", ""),
                    fighter_name=o_dict.get("fighter_name", ""),
                    opponent_id=o_dict.get("opponent_id", ""),
                    opponent_name=o_dict.get("opponent_name", ""),
                    opponent_record=o_dict.get("opponent_record", ""),
                    opponent_rating=o_dict.get("opponent_rating", 50),
                    weight_class=o_dict.get("weight_class", ""),
                    event_name=o_dict.get("event_name", ""),
                    event_date=o_dict.get("event_date", ""),
                    weeks_away=o_dict.get("weeks_away", 4),
                    purse=o_dict.get("purse", 5000),
                    is_title_fight=o_dict.get("is_title_fight", False),
                    is_main_event=o_dict.get("is_main_event", False),
                    matchup_quality=o_dict.get("matchup_quality", "Good"),
                ))
            
            # Load scheduled fights
            self.player_scheduled_fights = data.get("player_scheduled_fights", [])
            
            # Load AI scheduled fights
            self.ai_scheduled_fights = data.get("ai_scheduled_fights", [])
            self.next_event_number = data.get("next_event_number", 1)
            
            # Load fighter cooldowns
            self._fighter_cooldowns = data.get("fighter_cooldowns", {})
            
            # Load news
            self.news_feed = []
            for n_dict in data.get("news_feed", []):
                self.news_feed.append(NewsItem(
                    headline=n_dict.get("headline", ""),
                    details=n_dict.get("details", ""),
                    category=n_dict.get("category", "general"),
                    week=n_dict.get("week", 0),
                ))
            
            # Load economy data
            if ECONOMY_AVAILABLE and "economy_data" in data and data["economy_data"]:
                try:
                    self._economy_manager = EconomyManager.from_dict(data["economy_data"])
                except:
                    self._economy_manager = create_economy_manager()
                    self._initialize_camp_finances()
            elif ECONOMY_AVAILABLE:
                self._economy_manager = create_economy_manager()
                self._initialize_camp_finances()
            
            # Load watchlist data
            if WATCHLIST_AVAILABLE and "watchlist_data" in data and data["watchlist_data"]:
                try:
                    self._watchlist = Watchlist.from_dict(data["watchlist_data"])
                except:
                    self._watchlist = create_watchlist(max_entries=100)
            
            # Load injury data
            if INJURY_AVAILABLE and "injury_data" in data and data["injury_data"]:
                try:
                    self._injury_system = InjurySystem.from_dict(data["injury_data"])
                except:
                    self._injury_system = InjurySystem()
            
            # Load rivalry data
            if RIVALRY_AVAILABLE and "rivalry_data" in data and data["rivalry_data"]:
                try:
                    self._rivalry_system = RivalrySystem.from_dict(data["rivalry_data"])
                except:
                    self._rivalry_system = RivalrySystem()
            
            # Load aging data
            if AGING_AVAILABLE and "aging_data" in data and data["aging_data"]:
                try:
                    self._aging_system = AgingSystem.from_dict(data["aging_data"])
                except:
                    self._aging_system = AgingSystem()
            
            return True
        except Exception as e:
            print(f"Warning: Error restoring extended data: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # Main Entry Point
    # -------------------------------------------------------------------------
    
    def run(self) -> None:
        """Main entry point"""
        self.running = True
        
        while self.running:
            if self.in_game and self.game_state:
                self.game_loop()
            else:
                self.main_menu()
    
    # -------------------------------------------------------------------------
    # Main Menu
    # -------------------------------------------------------------------------
    
    def main_menu(self) -> None:
        """Display main menu"""
        clear_screen()
        print(TITLE_ART)
        print(f"Version {VERSION}".center(TERMINAL_WIDTH))
        print()
        print_divider()
        
        options = [
            ("1", "New Game"),
            ("2", "Load Game"),
            ("3", "Settings"),
            ("Q", "Quit"),
        ]
        
        print_menu(options)
        
        choice = get_choice(["1", "2", "3", "q"])
        
        if choice == "1":
            self.new_game_menu()
        elif choice == "2":
            self.load_game_menu()
        elif choice == "3":
            self.settings_menu()
        elif choice == "q":
            if confirm("Are you sure you want to quit?"):
                self.running = False
    
    def new_game_menu(self) -> None:
        """Handle new game creation with coach selection."""
        clear_screen()
        print_header("NEW GAME")
        
        print("Enter your name:")
        player_name = get_input("> ")
        if not player_name:
            player_name = "Coach"
        
        print()
        print("Enter your camp name:")
        camp_name = get_input("> ")
        if not camp_name:
            camp_name = f"{player_name}'s Gym"
        
        print()
        
        # Coach selection
        selected_coach = self._select_starting_coach()
        
        if selected_coach is None:
            print("Coach selection cancelled.")
            pause()
            return
        
        print()
        
        coach_name = selected_coach.name if selected_coach else "None"
        coach_specialty = selected_coach.specialty.value if selected_coach and hasattr(selected_coach.specialty, 'value') else "None"
        
        print_box([
            f"Player: {player_name}",
            f"Camp: {camp_name}",
            f"Head Coach: {coach_name}",
            f"Specialty: {coach_specialty}",
            "",
            "Ready to begin your journey in MMA?",
        ], title="CONFIRM NEW GAME")
        
        if confirm("Start game?"):
            self.start_new_game(player_name, camp_name, selected_coach)
    
    def _select_starting_coach(self):
        """Let player select their starting head coach."""
        clear_screen()
        print_header("SELECT YOUR HEAD COACH")
        
        print()
        print("  Every camp needs a leader. Choose your head coach wisely.")
        print("  They'll guide your fighters' development and corner them in fights.")
        print()
        
        # Generate coach options
        coach_options = []
        
        if COACHES_AVAILABLE:
            try:
                from systems.coaches import generate_starting_coach_options, generate_coach, CoachSpecialty
                
                # Generate 5 diverse options (2-3 star quality for balance)
                specialties = [
                    CoachSpecialty.STRIKING,
                    CoachSpecialty.WRESTLING,
                    CoachSpecialty.JIU_JITSU,
                    CoachSpecialty.CONDITIONING,
                    CoachSpecialty.CORNERING,
                ]
                
                for i, specialty in enumerate(specialties):
                    # Mix of 2-star and 3-star coaches
                    quality = 2 if i < 3 else 3
                    coach = generate_coach(quality=quality, specialty=specialty)
                    coach_options.append(coach)
                    
            except Exception as e:
                print(f"  {colored('Coach generation unavailable', Colors.RED)}")
                pause()
                return None
        else:
            print(f"  {colored('Coach system not available', Colors.RED)}")
            pause()
            return None
        
        if not coach_options:
            print("  No coaches available.")
            pause()
            return None
        
        print_divider()
        print()
        
        for i, coach in enumerate(coach_options, 1):
            stars = "*" * coach.quality + "-" * (5 - coach.quality)
            specialty = coach.specialty.value if hasattr(coach.specialty, 'value') else str(coach.specialty)
            salary = getattr(coach, 'weekly_salary', coach.quality * 500)
            
            # Get traits display
            traits_str = ""
            if coach.traits:
                trait_names = [t.value if hasattr(t, 'value') else str(t) for t in coach.traits[:2]]
                traits_str = f" | {', '.join(trait_names)}"
            
            # Color based on specialty
            specialty_colors = {
                "Striking": Colors.RED,
                "Wrestling": Colors.BLUE,
                "Jiu-Jitsu": Colors.MAGENTA,
                "Conditioning": Colors.GREEN,
                "Strength": Colors.ORANGE,
                "Cornering": Colors.CYAN,
            }
            spec_color = specialty_colors.get(specialty, Colors.NEUTRAL)
            
            print(f"  [{i}] {colored(coach.name, Colors.HIGHLIGHT)}")
            print(f"      {colored(specialty, spec_color)} | [{stars}] | ${salary:,}/week{traits_str}")
            
            # Show specialty bonus
            bonus_pct = int((coach.quality_multiplier - 1) * 100)
            if bonus_pct > 0:
                print(f"      Training Bonus: {colored(f'+{bonus_pct}%', Colors.GREEN)}")
            print()
        
        print(f"  [0] Cancel")
        print()
        
        choice = get_input("Select your head coach: ")
        
        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(coach_options):
                selected = coach_options[idx - 1]
                print()
                print(f"  {colored('[OK]', Colors.GREEN)} {selected.name} is ready to lead {colored('your camp', Colors.HIGHLIGHT)}!")
                pause()
                return selected
        except ValueError:
            pass
        
        return None
    
    def start_new_game(self, player_name: str, camp_name: str, starting_coach=None) -> None:
        """Initialize and start a new game with selected coach."""
        print()
        print("Creating your dynasty...")
        print()
        
        self.game_state = GameState()
        self.game_state.new_game(
            player_camp_name=camp_name,
            player_name=player_name,
        )
        
        self._initialize_systems()
        
        print("Generating the MMA world...")
        print()
        
        try:
            from simulation.world_init import WorldInitializer
            
            initializer = WorldInitializer(
                self.game_state,
                history_weeks=120
            )
            initializer.initialize_world()
            
            print()
            print(f"[OK] Created {len(initializer.fighters)} fighters")
            print(f"[OK] Created {len(initializer.camps)} AI camps")
            print(f"[OK] Simulated 2+ years of fight history")
            print(f"[OK] Crowned 9 division champions")
            
            # Get coach system from world initializer if available
            world_coach_system = initializer.get_coach_system()
            if world_coach_system and COACHES_AVAILABLE:
                self._coach_system = world_coach_system
                
                # Count coaches generated
                coach_count = sum(len(c.coach_ids) for c in initializer.camps.values())
                print(f"[OK] Generated {coach_count} coaches for AI camps")
            
            # Assign starting coach to player camp
            if starting_coach and COACHES_AVAILABLE and self._coach_system:
                player_camp = self.game_state.get_player_camp()
                if player_camp:
                    # Add coach to system
                    starting_coach.camp_id = player_camp.camp_id
                    starting_coach.is_head_coach = True
                    self._coach_system._coaches[starting_coach.coach_id] = starting_coach
                    
                    # Track in camp_coaches
                    if player_camp.camp_id not in self._coach_system._camp_coaches:
                        self._coach_system._camp_coaches[player_camp.camp_id] = []
                    self._coach_system._camp_coaches[player_camp.camp_id].append(starting_coach.coach_id)
                    
                    print(f"[OK] {starting_coach.name} joins as your Head Coach")
            
            # Generate full data for all fighters
            for fighter_id in self.game_state.fighters:
                self._create_full_fighter_data(fighter_id)
            
        except ImportError:
            print("(Using simplified world generation)")
            counts = self.game_state.initialize_world(
                num_ai_camps=20,
                fighters_per_division=15,
                generate_history=True,
            )
            print(f"[OK] Created {counts['fighters']} fighters")
            print(f"[OK] Created {counts['camps']} AI camps")
        
        print()
        pause()
        
        self._schedule_initial_events()
        
        self.in_game = True
        self.pick_starting_fighter()
        
        self._generate_fight_offers()
        
        self.news_feed.append(NewsItem(
            headline=f"Welcome to the DFC! {camp_name} joins the fight game.",
            category="general",
            week=self.game_state.week_number,
        ))
        
        print()
        print("Your dynasty awaits!")
        pause()
    
    def _schedule_initial_events(self) -> None:
        """Schedule first AI events"""
        # Schedule events at weeks 2, 4, 6, 8
        for weeks in [2, 4, 6, 8]:
            event_name = f"DFC Fight Night {self.next_event_number}"
            self.next_event_number += 1
            self._schedule_ai_event(weeks, event_name)
    
    def pick_starting_fighter(self) -> None:
        """Let player pick starting fighter"""
        clear_screen()
        print_header("CHOOSE YOUR FIRST FIGHTER")
        
        print("Every dynasty starts with one fighter.")
        print()
        
        options = [
            ("1", "Scout a Free Agent"),
            ("2", "Sign a Prospect"),
            ("3", "Start Empty"),
        ]
        print_menu(options)
        
        choice = get_choice(["1", "2", "3"])
        
        if choice == "1":
            self.scout_free_agent()
        elif choice == "2":
            self.generate_prospect()
    
    def scout_free_agent(self) -> None:
        """Browse free agents"""
        clear_screen()
        print_header("SCOUT FREE AGENTS")
        
        weight_classes = list(self.game_state.divisions.keys())
        for i, wc in enumerate(weight_classes, 1):
            print(f"  [{i}] {wc}")
        print()
        print(f"  [0] Back")
        print()
        
        choice = get_input("Select weight class: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(weight_classes):
                self.show_free_agents(weight_classes[index - 1])
        except (ValueError, IndexError):
            pass
    
    def show_free_agents(self, weight_class: str) -> None:
        """Show free agents in a weight class with pagination and search."""
        game = self.game_state
        player_camp = game.get_player_camp()
        player_camp_id = player_camp.camp_id if player_camp else None
        
        all_available = []
        for fighter_rec in game.fighters.values():
            if getattr(fighter_rec, 'weight_class', '') != weight_class:
                continue
            if getattr(fighter_rec, 'camp_id', None) == player_camp_id:
                continue
            
            fighter_camp_id = getattr(fighter_rec, 'camp_id', None)
            if fighter_camp_id is None or fighter_rec.fighter_id in game.free_agents:
                all_available.append(fighter_rec)
            elif fighter_camp_id and fighter_camp_id in game.camps:
                camp = game.camps[fighter_camp_id]
                tier = getattr(camp, 'tier', 'LOCAL')
                if tier in ("GARAGE", "LOCAL"):
                    all_available.append(fighter_rec)
        
        if not all_available:
            clear_screen()
            print_header(f"FREE AGENTS - {weight_class.upper()}")
            print("No free agents available.")
            pause()
            return
        
        all_available.sort(key=lambda f: getattr(f, 'overall_rating', 0), reverse=True)
        
        current_available = all_available
        search_query = ""
        page = 0
        page_size = 10
        
        while True:
            clear_screen()
            
            total_pages = max(1, (len(current_available) + page_size - 1) // page_size)
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(current_available))
            display_fighters = current_available[start_idx:end_idx]
            
            header_title = f"FREE AGENTS - {weight_class.upper()}"
            if search_query:
                header_title += f" (Search: '{search_query}')"
            if total_pages > 1:
                header_title += f" (Page {page + 1}/{total_pages})"
            print_header(header_title)
            
            if not display_fighters:
                if search_query:
                    print(f"  No free agents match '{search_query}'")
                else:
                    print("  No free agents available")
            else:
                for i, fighter in enumerate(display_fighters, 1):
                    # Show scouting info if available
                    scouting_info = ""
                    if SCOUTING_AVAILABLE:
                        try:
                            fdata = self._create_full_fighter_data(fighter.fighter_id)
                            if fdata:
                                report = scout_fighter(fdata)
                                if report.strengths:
                                    top_strength = report.strengths[0].attribute
                                    scouting_info = colored(f" [{top_strength}]", Colors.CYAN)
                        except:
                            pass
                    
                    print(f"  [{i}] {fighter.name}{scouting_info}")
                    print(f"      Record: {format_record_colored(fighter.wins, fighter.losses)}")
                    print(f"      Rating: {fighter.overall_rating}")
                    print()
            
            print()
            nav_opts = []
            if page > 0:
                nav_opts.append("[P]rev")
            if page < total_pages - 1:
                nav_opts.append("[N]ext")
            nav_opts.append("[S]earch")
            if search_query:
                nav_opts.append("[C]lear")
            nav_opts.append("[0] Back")
            print(f"  [#] Sign | {' | '.join(nav_opts)}")
            print()
            
            choice = get_input("Sign fighter: ").lower().strip()
            
            if choice == "0":
                return
            elif choice == "s":
                query = get_input("Search name: ").strip()
                if query:
                    search_query = query
                    current_available = search_by_name(all_available, query)
                    page = 0
            elif choice == "c" and search_query:
                search_query = ""
                current_available = all_available
                page = 0
            elif choice == "n" and page < total_pages - 1:
                page += 1
            elif choice == "p" and page > 0:
                page -= 1
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(display_fighters):
                        fighter_to_sign = display_fighters[index]
                        self.sign_fighter(fighter_to_sign)
                        all_available = [f for f in all_available 
                                        if f.fighter_id != fighter_to_sign.fighter_id]
                        if search_query:
                            current_available = search_by_name(all_available, search_query)
                        else:
                            current_available = all_available
                        total_pages = max(1, (len(current_available) + page_size - 1) // page_size)
                        if page >= total_pages:
                            page = max(0, total_pages - 1)
                except (ValueError, IndexError):
                    pass


    def sign_fighter(self, fighter) -> None:
        """Sign a fighter"""
        fighter_id = fighter.fighter_id
        name = fighter.name
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        if fighter_id in self.game_state.fighters:
            self.game_state.fighters[fighter_id].camp_id = player_camp.camp_id
            self.game_state.free_agents.discard(fighter_id)
        
        # Create full data
        self._create_full_fighter_data(fighter_id)
        if fighter_id in self.fighter_data:
            self.fighter_data[fighter_id].camp_id = player_camp.camp_id
        
        self.news_feed.insert(0, NewsItem(
            headline=f"{name} signs with {player_camp.name}!",
            category="signing",
            week=self.game_state.week_number,
        ))
        
        print()
        print(f"[OK] Signed {colored(name, Colors.WIN)}!")
        pause()
    
    def generate_prospect(self) -> None:
        """Generate prospects to scout and potentially sign."""
        clear_screen()
        print_header("SCOUT PROSPECTS")
        
        print("  Select a weight class to scout young talent.")
        print("  Prospects are unproven but have high development potential.")
        print()
        
        weight_classes = list(self.game_state.divisions.keys())
        for i, wc in enumerate(weight_classes, 1):
            print(f"  [{i}] {wc}")
        print()
        print(f"  [0] Back")
        print()
        
        choice = get_input("Select weight class: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(weight_classes):
                self.show_prospect_pool(weight_classes[index - 1])
        except (ValueError, IndexError):
            pass
    
    def show_prospect_pool(self, weight_class: str) -> None:
        """Show a pool of generated prospects with full scouting."""
        import uuid
        
        clear_screen()
        print_header(f"PROSPECT POOL - {weight_class.upper()}")
        
        print("  Generating prospects for evaluation...")
        print()
        
        # Generate 3-5 prospects to choose from
        prospects = []
        num_prospects = random.randint(3, 5)
        
        try:
            from simulation.generator import generate_fighter
            
            for _ in range(num_prospects):
                gen = generate_fighter(
                    weight_class=weight_class,
                    fighter_type="prospect",
                )
                
                # Create temporary full data for scouting
                age = random.randint(18, 23)
                full_data = FighterFullData(
                    fighter_id=gen.fighter_id,
                    name=gen.name,
                    weight_class=weight_class,
                    camp_id=None,
                    age=age,
                    personality=getattr(gen, "personality", "Methodical"),
                    fighting_style=self._get_style_string(getattr(gen, 'fighting_style', 'Balanced')),
                    strength=gen.strength,
                    speed=gen.speed,
                    cardio=gen.cardio,
                    chin=gen.chin,
                    boxing=gen.boxing,
                    kicks=gen.kicks,
                    clinch_striking=gen.clinch_striking,
                    striking_defense=gen.striking_defense,
                    wrestling=gen.wrestling,
                    bjj=gen.bjj,
                    takedown_defense=gen.takedown_defense,
                    heart=gen.heart,
                    fight_iq=gen.fight_iq,
                    composure=gen.composure,
                    traits=getattr(gen, 'traits', []),
                )
                prospects.append(full_data)
                
        except ImportError:
            # Fallback generation
            first_names = ["Alex", "Mike", "John", "Chris", "Jake", "Marcus", "Tyler", "Ryan"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez"]
            
            for _ in range(num_prospects):
                fighter_id = f"prospect_{uuid.uuid4().hex[:8]}"
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                age = random.randint(18, 23)
                base_rating = random.randint(45, 62)
                
                full_data = FighterFullData(
                    fighter_id=fighter_id,
                    name=name,
                    weight_class=weight_class,
                    age=age,
                    overall_rating=base_rating,
                    boxing=base_rating + random.randint(-10, 10),
                    kicks=base_rating + random.randint(-10, 10),
                    wrestling=base_rating + random.randint(-10, 10),
                    bjj=base_rating + random.randint(-10, 10),
                )
                prospects.append(full_data)
        
        # Display prospects with scouting info
        self._display_prospect_pool(prospects, weight_class)
    
    def _display_prospect_pool(self, prospects: list, weight_class: str) -> None:
        """Display prospect pool with scouting reports."""
        page = 0
        
        while True:
            clear_screen()
            print_header(f"PROSPECT POOL - {weight_class.upper()}")
            
            print(colored("  AVAILABLE PROSPECTS", Colors.CYAN))
            print()
            
            for i, prospect in enumerate(prospects, 1):
                # Get potential assessment if scouting available
                potential_info = ""
                grade_color = Colors.WHITE
                
                if SCOUTING_AVAILABLE:
                    try:
                        assessment = assess_potential(prospect)
                        grade = assessment.potential_grade
                        
                        # Color code the grade
                        if grade == "Elite":
                            grade_color = Colors.GOLD
                        elif grade == "High":
                            grade_color = Colors.GREEN
                        elif grade == "Average":
                            grade_color = Colors.YELLOW
                        else:
                            grade_color = Colors.RED
                        
                        potential_info = f" | Potential: {colored(grade, grade_color)}"
                        
                        # Get top strength
                        report = scout_fighter(prospect, is_prospect=True)
                        if report.strengths:
                            top = report.strengths[0].attribute
                            potential_info += f" | {colored(top, Colors.CYAN)}"
                    except:
                        pass
                
                age_str = f"Age {prospect.age}" if prospect.age else "Young"
                rating = prospect.overall_rating
                
                print(f"  [{i}] {prospect.name}")
                print(f"      {age_str} | OVR: {rating}{potential_info}")
                print()
            
            print_divider()
            print()
            print(f"  [#] View Full Report & Sign")
            print(f"  [0] Back (no signing)")
            print()
            
            choice = get_input("Select prospect: ")
            
            if choice == "0":
                return
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(prospects):
                    if self._view_prospect_report(prospects[index]):
                        return  # Signed, exit
            except (ValueError, IndexError):
                pass
    
    def _view_prospect_report(self, prospect: FighterFullData) -> bool:
        """View detailed prospect report and option to sign. Returns True if signed."""
        clear_screen()
        print_header(f"PROSPECT REPORT: {prospect.name}")
        
        # Basic info
        print(f"  Name: {colored(prospect.name, Colors.CYAN)}")
        print(f"  Age: {prospect.age}")
        print(f"  Weight Class: {prospect.weight_class}")
        print(f"  Current Overall: {prospect.overall_rating}")
        print()
        
        # Potential Assessment
        if SCOUTING_AVAILABLE:
            try:
                assessment = assess_potential(prospect)
                
                print_divider()
                print(colored("  POTENTIAL ASSESSMENT", Colors.GOLD))
                print()
                
                # Grade with color
                grade = assessment.potential_grade
                if grade == "Elite":
                    grade_display = colored(f"***** {grade}", Colors.GOLD)
                elif grade == "High":
                    grade_display = colored(f"****- {grade}", Colors.GREEN)
                elif grade == "Average":
                    grade_display = colored(f"***-- {grade}", Colors.YELLOW)
                elif grade == "Limited":
                    grade_display = colored(f"**--- {grade}", Colors.ORANGE)
                else:
                    grade_display = colored(f"*---- {grade}", Colors.RED)
                
                print(f"  Grade: {grade_display}")
                print(f"  Ceiling: {assessment.potential_ceiling}")
                print(f"  Upside: +{assessment.upside} points of growth")
                print(f"  Years to Peak: ~{assessment.years_to_peak}")
                print(f"  Development Speed: {assessment.development_speed:.1f}x")
                print(f"  Confidence: {assessment.confidence}")
                print()
                
                # Visual potential bar
                current = prospect.overall_rating
                ceiling = assessment.potential_ceiling
                current_bars = current // 5
                growth_bars = (ceiling - current) // 5
                empty_bars = 20 - current_bars - growth_bars
                
                bar = colored("#" * current_bars, Colors.CYAN)
                bar += colored("+" * growth_bars, Colors.GREEN)
                bar += "." * empty_bars
                print(f"  [{bar}]")
                print(f"   Current: {current}  ->  Ceiling: {ceiling}")
                print()
                
                # Scout notes
                if assessment.notes:
                    print(colored("  SCOUT NOTES", Colors.MAGENTA))
                    for note in assessment.notes:
                        print(f"    * {note}")
                    print()
                
                # Worth developing indicator
                if assessment.is_worth_developing:
                    print(f"  {colored('[OK] RECOMMENDED SIGNING', Colors.GREEN)}")
                else:
                    print(f"  {colored('[!] LIMITED UPSIDE', Colors.YELLOW)}")
                print()
                
            except Exception as e:
                print(f"  Could not assess potential: {e}")
                print()
        
        # Strengths & Weaknesses
        if SCOUTING_AVAILABLE:
            try:
                report = scout_fighter(prospect, is_prospect=True)
                
                print_divider()
                print(colored("  STRENGTHS", Colors.GREEN))
                for s in report.strengths[:3]:
                    print(f"    + {s.attribute}: {s.value}")
                print()
                
                print(colored("  WEAKNESSES", Colors.RED))
                for w in report.weaknesses[:3]:
                    print(f"    - {w.attribute}: {w.value}")
                print()
                
                # Traits
                if prospect.traits:
                    print_divider()
                    print("  TRAITS")
                    for trait in prospect.traits:
                        desc = get_trait_description(trait) if 'get_trait_description' in dir() else ""
                        print(f"    * {trait}")
                        if desc:
                            print(f"      {desc}")
                    print()
                    
            except:
                pass
        
        # Key Stats
        print_divider()
        print("  KEY ATTRIBUTES")
        print(f"    Boxing:    {self._attr_bar(prospect.boxing)}")
        print(f"    Kicks:     {self._attr_bar(prospect.kicks)}")
        print(f"    Wrestling: {self._attr_bar(prospect.wrestling)}")
        print(f"    BJJ:       {self._attr_bar(prospect.bjj)}")
        print(f"    Cardio:    {self._attr_bar(prospect.cardio)}")
        print()
        
        # Options
        print_divider()
        options = [
            ("1", colored("Sign Prospect", Colors.WIN)),
            ("0", "Back to Pool"),
        ]
        print_menu(options)
        
        choice = get_input("> ")
        
        if choice == "1":
            self._sign_prospect(prospect)
            return True
        
        return False
    
    def _attr_bar(self, value: int) -> str:
        """Create attribute bar display."""
        bars = value // 5
        empty = 20 - bars
        
        if value >= 75:
            color = Colors.GREEN
        elif value >= 60:
            color = Colors.YELLOW
        elif value >= 45:
            color = Colors.ORANGE
        else:
            color = Colors.RED
        
        bar = colored("#" * bars, color) + "." * empty
        return f"{bar} {value}"
    
    def _sign_prospect(self, prospect: FighterFullData) -> None:
        """Sign a prospect to the player's camp."""
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            print("No camp found!")
            pause()
            return
        
        fighter_id = prospect.fighter_id
        
        # Add to game state
        self.game_state.fighters[fighter_id] = FighterRecord(
            fighter_id=fighter_id,
            name=prospect.name,
            weight_class=prospect.weight_class,
            camp_id=player_camp.camp_id,
            wins=0,
            losses=0,
            overall_rating=prospect.overall_rating,
        )
        
        # Store full data with camp assignment
        prospect.camp_id = player_camp.camp_id
        self.fighter_data[fighter_id] = prospect
        
        # News
        self.news_feed.insert(0, NewsItem(
            headline=f"{prospect.name} signs with {player_camp.name}!",
            category="signing",
            week=self.game_state.week_number,
        ))
        
        print()
        print(f"  {colored('[OK] SIGNED!', Colors.WIN)} {prospect.name} joins your camp!")
        print()
        
        # Show development recommendation
        if SCOUTING_AVAILABLE:
            try:
                report = scout_fighter(prospect, is_prospect=True)
                if report.development_focus:
                    print(colored("  DEVELOPMENT RECOMMENDATION:", Colors.CYAN))
                    for focus in report.development_focus[:2]:
                        print(f"    -> {focus}")
                    print()
            except:
                pass
        
        pause()



    def load_game_menu(self) -> None:
        """Load game menu"""
        clear_screen()
        print_header("LOAD GAME")
        
        saves = list_saves()
        
        if not saves:
            print("No saved games found.")
            pause()
            return
        
        for i, save in enumerate(saves, 1):
            print(f"  [{i}] {save.game_name} - Week {save.week_number}")
        
        print()
        print(f"  [Q] Quick Load")
        print(f"  [0] Back")
        print()
        
        choice = get_input("Select save: ").lower()
        
        if choice == "0":
            return
        elif choice == "q":
            result = quickload()
            if result:
                self.game_state = result
                self._initialize_systems()
                self.in_game = True
                # Try to load extended data
                if not self._load_extended_data("quicksave"):
                    # Generate fighter data if no extended save
                    for fid in self.game_state.fighters:
                        self._create_full_fighter_data(fid)
                print("Quick loaded!")
            else:
                print("No quick save found.")
            pause()
            return
        
        try:
            index = int(choice)
            if 1 <= index <= len(saves):
                save = saves[index - 1]
                result = load_game(save.slot_name)
                if result:
                    self.game_state = result
                    self._initialize_systems()
                    self.in_game = True
                    # Try to load extended data
                    if not self._load_extended_data(save.slot_name):
                        # Generate fighter data if no extended save
                        for fid in self.game_state.fighters:
                            self._create_full_fighter_data(fid)
                        print(f"Loaded: {save.game_name} (no extended data found)")
                    else:
                        print(f"Loaded: {save.game_name}")
                pause()
        except ValueError:
            pass
    
    def settings_menu(self) -> None:
        """Settings menu"""
        clear_screen()
        print_header("SETTINGS")
        print("Settings coming soon!")
        pause()
    
    # -------------------------------------------------------------------------
    # Game Loop
    # -------------------------------------------------------------------------
    
    def game_loop(self) -> None:
        """Main game loop"""
        if not self.game_state:
            self.in_game = False
            return
        self.show_hub()
    
    def show_hub(self) -> None:
        """Display the main hub with comprehensive dashboard."""
        clear_screen()
        
        game = self.game_state
        player_camp = game.get_player_camp()
        
        try:
            date_str = game.calendar.current_date.format("long")
        except:
            date_str = f"Week {game.week_number}"
        
        camp_name = player_camp.name if player_camp else "Unknown Camp"
        
        # =====================================================================
        # CAMP OVERVIEW BOX
        # =====================================================================
        tier = self._get_camp_tier()
        balance = player_camp.balance if player_camp else 0
        
        # Get roster info
        camp_fighters = [f for f in game.fighters.values() 
                        if getattr(f, 'camp_id', None) == player_camp.camp_id] if player_camp else []
        max_fighters = {"GARAGE": 5, "LOCAL": 10, "REGIONAL": 20, "NATIONAL": 35, "ELITE": 50}.get(tier, 5)
        
        # Camp record
        total_wins = sum(f.wins for f in camp_fighters)
        total_losses = sum(f.losses for f in camp_fighters)
        win_pct = int(total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        
        # Championships
        champ_count = sum(1 for f in camp_fighters if f.is_champion)
        
        print(f"  {colored('=' * 68, Colors.CYAN)}")
        print(f"  {colored('|', Colors.CYAN)}  {colored(camp_name.upper(), Colors.HIGHLIGHT):<40} {colored(tier + ' GYM', Colors.YELLOW):>22}  {colored('|', Colors.CYAN)}")
        print(f"  {colored('+' + '=' * 66 + '+', Colors.CYAN)}")
        print(f"  {colored('|', Colors.CYAN)}  {date_str:<32} Week {game.week_number:<20}  {colored('|', Colors.CYAN)}")
        print(f"  {colored('|', Colors.CYAN)}  Balance: {colored(format_money(balance), Colors.WIN):<22} Roster: {len(camp_fighters)}/{max_fighters} fighters      {colored('|', Colors.CYAN)}")
        
        champ_str = f"[C] {champ_count}" if champ_count > 0 else "0"
        record_str = f"{total_wins}-{total_losses} ({win_pct}%)"
        print(f"  {colored('|', Colors.CYAN)}  Championships: {champ_str:<16} Camp Record: {record_str:<14}  {colored('|', Colors.CYAN)}")
        print(f"  {colored('=' * 68, Colors.CYAN)}")
        print()
        
        # =====================================================================
        # FIGHTER ROSTER SUMMARY
        # =====================================================================
        if camp_fighters:
            print(f"  {colored('YOUR FIGHTERS', Colors.CYAN)}")
            print(f"  {'-' * 66}")
            
            # Sort by: champions first, then by rating
            camp_fighters.sort(key=lambda f: (-int(f.is_champion), -f.overall_rating))
            
            for fighter in camp_fighters[:5]:  # Show top 5
                # Get ranking
                rank_str = self._get_fighter_rank_str(fighter)
                
                # Get division abbreviation
                div_abbrev = self._get_division_abbrev(fighter.weight_class)
                
                # Status indicators
                status = self._get_fighter_status_str(fighter)
                
                # Win streak
                streak_str = ""
                full_data = self.fighter_data.get(fighter.fighter_id)
                if full_data and full_data.win_streak >= 3:
                    streak_str = colored(f" [!]{full_data.win_streak}", Colors.ORANGE)
                
                # Format line
                champ_icon = "[C] " if fighter.is_champion else "   "
                name_colored = colored(fighter.name, Colors.HIGHLIGHT) if fighter.is_champion else fighter.name
                record = f"{fighter.wins}-{fighter.losses}"
                
                line = f"  {champ_icon}{name_colored:<18} {div_abbrev:>3}  {fighter.overall_rating:>2} OVR  {record:<6} {rank_str:<14}{streak_str}"
                print(line)
                
                # Status on second line if any
                if status:
                    print(f"      {status}")
            
            if len(camp_fighters) > 5:
                print(f"      {colored(f'... and {len(camp_fighters) - 5} more', Colors.DIM)}")
            
            print(f"  {'-' * 66}")
            print()
        
        # =====================================================================
        # ALERTS
        # =====================================================================
        offer_count = len(self.fight_offers)
        scheduled_count = len(self.player_scheduled_fights)
        
        if offer_count > 0 or scheduled_count > 0:
            alert_parts = []
            if offer_count > 0:
                alert_parts.append(colored(f"[!] {offer_count} offer(s)", Colors.YELLOW))
            if scheduled_count > 0:
                alert_parts.append(colored(f"[*] {scheduled_count} fight(s) booked", Colors.CYAN))
            print(f"  {' | '.join(alert_parts)}")
            print()
        
        # =====================================================================
        # NEWS SECTIONS
        # =====================================================================
        self._display_dashboard_news(camp_fighters)
        
        # =====================================================================
        # MENU
        # =====================================================================
        unique_weeks = len(set(f.get("weeks_until") for f in self.ai_scheduled_fights if f.get("weeks_until", 0) > 0))
        
        options = [
            ("1", "Advance Week"),
            ("2", "My Camp"),
            ("3", "My Fighters"),
            ("4", f"Fight Offers ({offer_count})"),
            ("5", f"Upcoming Events ({unique_weeks})"),
            ("6", "Rankings"),
            ("7", "Browse Fighters"),
            ("8", "Browse Camps"),
            ("9", "News Feed"),
            ("0", "History & Records"),
            ("W", "Watchlist"),
            ("S", "Save Game"),
            ("Q", "Quit to Menu"),
        ]
        
        print_menu(options)
        
        choice = get_choice(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "w", "s", "q"])
        
        if choice == "1":
            self.advance_week()
        elif choice == "2":
            self.show_camp()
        elif choice == "3":
            self.show_fighters()
        elif choice == "4":
            self.show_fight_offers()
        elif choice == "5":
            self.show_upcoming_events()
        elif choice == "6":
            self.show_rankings()
        elif choice == "7":
            self.browse_all_fighters()
        elif choice == "8":
            self.browse_camps()
        elif choice == "9":
            self.show_news_feed()
        elif choice == "0":
            self.show_history_menu()
        elif choice == "w":
            self.show_watchlist()
        elif choice == "s":
            self.save_game_menu()
        elif choice == "q":
            self.quit_to_menu()
    
    def _get_fighter_rank_str(self, fighter) -> str:
        """Get ranking string for a fighter (e.g., '#1 Contender', 'Unranked')."""
        if fighter.is_champion:
            return colored("CHAMPION", Colors.GOLD)
        
        # Get division fighters sorted by rating
        div_fighters = [f for f in self.game_state.fighters.values()
                       if f.weight_class == fighter.weight_class 
                       and f.is_active and not f.is_champion]
        div_fighters.sort(key=lambda f: f.overall_rating, reverse=True)
        
        # Find rank
        for i, f in enumerate(div_fighters[:15], 1):
            if f.fighter_id == fighter.fighter_id:
                if i == 1:
                    return colored("#1 Contender", Colors.GREEN)
                elif i <= 5:
                    return colored(f"#{i} Ranked", Colors.CYAN)
                elif i <= 10:
                    return f"#{i} Ranked"
                else:
                    return colored(f"#{i} Ranked", Colors.DIM)
        
        return colored("Unranked", Colors.DIM)
    
    def _get_division_abbrev(self, weight_class: str) -> str:
        """Get short abbreviation for weight class."""
        abbrevs = {
            "Strawweight": "STW",
            "Flyweight": "FLW", 
            "Bantamweight": "BW",
            "Featherweight": "FW",
            "Lightweight": "LW",
            "Welterweight": "WW",
            "Middleweight": "MW",
            "Light Heavyweight": "LHW",
            "Heavyweight": "HW",
        }
        return abbrevs.get(weight_class, weight_class[:3].upper())
    
    def _get_fighter_status_str(self, fighter) -> str:
        """Get status string (training, injured, scheduled fight, cooldown)."""
        statuses = []
        
        # Check training
        if self._training_system:
            camp = self._training_system.get_camp(fighter.fighter_id)
            if camp and not camp.is_complete:
                weeks_left = camp.weeks_remaining if hasattr(camp, 'weeks_remaining') else '?'
                focus = camp.focus.value if hasattr(camp, 'focus') else 'Training'
                statuses.append(colored(f"[T] {focus} (Week {camp.weeks_completed}/{camp.total_weeks})", Colors.CYAN))
        
        # Check injury
        if self._is_fighter_injured(fighter.fighter_id):
            weeks = self._get_fighter_recovery_weeks(fighter.fighter_id)
            statuses.append(colored(f"[X] Injured ({weeks} wks)", Colors.RED))
        
        # Check scheduled fight
        for fight in self.player_scheduled_fights:
            if fight.get("fighter1_id") == fighter.fighter_id:
                weeks = fight.get("weeks_until", "?")
                opp_name = fight.get("fighter2_name", "TBD")
                is_title = fight.get("is_title_fight", False)
                title_tag = " [C]" if is_title else ""
                statuses.append(colored(f"[*] vs {opp_name} in {weeks}wks{title_tag}", Colors.YELLOW))
                break
        
        # Check cooldown (recovering from loss)
        if fighter.fighter_id in self._fighter_cooldowns and self._fighter_cooldowns[fighter.fighter_id] > 0:
            weeks = self._fighter_cooldowns[fighter.fighter_id]
            fighter_data = self.fighter_data.get(fighter.fighter_id)
            streak = fighter_data.lose_streak if fighter_data else 0
            streak_str = f" ({streak}L streak)" if streak > 1 else ""
            statuses.append(colored(f"[!] Recovering ({weeks} wks){streak_str}", Colors.ORANGE))
        
        if not statuses:
            statuses.append(colored("[OK] Ready to book", Colors.GREEN))
        
        return " | ".join(statuses)
    
    def _display_dashboard_news(self, camp_fighters: list) -> None:
        """Display news sections for dashboard."""
        if not self.news_feed:
            return
        
        camp_fighter_ids = {f.fighter_id for f in camp_fighters}
        camp_fighter_names = {f.name.lower() for f in camp_fighters}
        
        # Get player's divisions for priority
        player_divisions = {f.weight_class for f in camp_fighters}
        
        # Separate news
        camp_news = []
        dfc_news = []
        
        for news in self.news_feed[:30]:  # Check last 30 items
            headline = news.headline
            
            # Check if it's about our camp
            is_camp_news = False
            for name in camp_fighter_names:
                if name in headline.lower():
                    is_camp_news = True
                    break
            
            # Enhance headline with ranks/titles
            enhanced = self._enhance_news_headline(headline)
            
            if is_camp_news:
                if len(camp_news) < 5:
                    camp_news.append(enhanced)
            else:
                # Prioritize: title fights, top fighters, player's divisions, upsets
                priority = self._get_news_priority(news, player_divisions)
                if priority > 0 and len(dfc_news) < 7:
                    dfc_news.append((priority, enhanced))
        
        # Sort DFC news by priority
        dfc_news.sort(key=lambda x: -x[0])
        dfc_headlines = [h for _, h in dfc_news[:7]]
        
        # Display YOUR CAMP news
        if camp_news:
            print(f"  {colored('[>] YOUR CAMP', Colors.CYAN)}")
            for headline in camp_news[:5]:
                print(f"     * {headline}")
            print()
        
        # Display AROUND DFC news
        if dfc_headlines:
            print(f"  {colored('[>] AROUND DFC', Colors.MAGENTA)}")
            for headline in dfc_headlines[:7]:
                print(f"     * {headline}")
            print()
    
    def _enhance_news_headline(self, headline: str) -> str:
        """Add rank/title info to fighter names in headlines."""
        # Find fighter names mentioned and add their rank
        enhanced = headline
        
        for fighter in self.game_state.fighters.values():
            if fighter.name in headline:
                # Get rank info
                div_abbrev = self._get_division_abbrev(fighter.weight_class)
                
                if fighter.is_champion:
                    enhanced_name = colored(f"[C] {div_abbrev} {fighter.name}", Colors.GOLD)
                else:
                    # Get ranking
                    div_fighters = [f for f in self.game_state.fighters.values()
                                   if f.weight_class == fighter.weight_class 
                                   and f.is_active and not f.is_champion]
                    div_fighters.sort(key=lambda f: f.overall_rating, reverse=True)
                    
                    rank = None
                    for i, f in enumerate(div_fighters[:15], 1):
                        if f.fighter_id == fighter.fighter_id:
                            rank = i
                            break
                    
                    if rank:
                        enhanced_name = colored(f"#{rank} {div_abbrev}", Colors.CYAN) + f" {fighter.name}"
                    else:
                        enhanced_name = fighter.name
                
                enhanced = enhanced.replace(fighter.name, enhanced_name, 1)
                break  # Only enhance first found fighter to avoid cluttering
        
        return enhanced
    
    def _get_news_priority(self, news, player_divisions: set) -> int:
        """Calculate priority score for news item."""
        headline = news.headline.lower()
        category = news.category if hasattr(news, 'category') else ""
        priority = 0
        
        # Title changes are highest priority
        if "title" in headline or "champion" in headline:
            priority += 100
        
        # Knockouts and finishes
        if "ko" in headline or "tko" in headline or "submission" in headline:
            priority += 30
        
        # Check if involves top fighters
        for fighter in self.game_state.fighters.values():
            if fighter.name.lower() in headline:
                if fighter.is_champion:
                    priority += 80
                elif fighter.overall_rating >= 85:
                    priority += 50
                elif fighter.overall_rating >= 75:
                    priority += 20
                
                # Bonus for player's divisions
                if fighter.weight_class in player_divisions:
                    priority += 40
                
                break
        
        # Upsets (might contain "upset" in generated news)
        if "upset" in headline:
            priority += 60
        
        # Injuries of top fighters
        if "injur" in headline:
            priority += 25
        
        return priority


    def show_fighters(self) -> None:
        """Display fighter roster with search capability."""
        game = self.game_state
        player_camp = game.get_player_camp()
        
        if not player_camp:
            clear_screen()
            print("No camp found!")
            pause()
            return
        
        camp_id = player_camp.camp_id
        all_fighters = [f for f in game.fighters.values() 
                        if getattr(f, 'camp_id', None) == camp_id]
        all_fighters.sort(key=lambda f: getattr(f, 'overall_rating', 0), reverse=True)
        
        if not all_fighters:
            clear_screen()
            print_header("MY FIGHTERS")
            print("No fighters in your camp yet.")
            print()
            print("Scout free agents to build your roster!")
            pause()
            return
        
        current_fighters = all_fighters
        search_query = ""
        
        while True:
            clear_screen()
            
            header_title = "MY FIGHTERS"
            if search_query:
                header_title += f" (Search: '{search_query}')"
            print_header(header_title)
            
            if not current_fighters:
                print(f"  No fighters match '{search_query}'")
            else:
                for i, fighter in enumerate(current_fighters, 1):
                    name = fighter.name
                    record = format_record_colored(fighter.wins, fighter.losses)
                    weight = fighter.weight_class
                    rating = fighter.overall_rating
                    is_champ = fighter.is_champion
                    
                    champ_marker = "[C] " if is_champ else "   "
                    
                    training_status = ""
                    if self._training_system:
                        camp = self._training_system.get_camp(fighter.fighter_id)
                        if camp and not camp.is_complete:
                            training_status = colored(" [TRAINING]", Colors.CYAN)
                    
                    scheduled = ""
                    for fight in self.player_scheduled_fights:
                        if fight.get("fighter1_id") == fighter.fighter_id:
                            weeks = fight.get("weeks_until", "?")
                            scheduled = colored(f" [FIGHT in {weeks}wks]", Colors.ORANGE)
                            break
                    
                    print(f"  [{i}] {champ_marker}{name}{training_status}{scheduled}")
                    print(f"       {weight} | {record} | OVR: {rating}")
                    print()
            
            print()
            nav_opts = ["[#] View", "[S]earch"]
            if search_query:
                nav_opts.append("[C]lear")
            nav_opts.append("[0] Back")
            print(f"  {' | '.join(nav_opts)}")
            print()
            
            choice = get_input("Select fighter: ").lower().strip()
            
            if choice == "0":
                return
            elif choice == "s":
                query = get_input("Search fighter name: ").strip()
                if query:
                    search_query = query
                    current_fighters = search_by_name(all_fighters, query)
            elif choice == "c" and search_query:
                search_query = ""
                current_fighters = all_fighters
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(current_fighters):
                        self.show_fighter_details(current_fighters[index])
                except (ValueError, IndexError):
                    pass


    def show_fighter_details(self, fighter_rec) -> None:
        """Display detailed fighter info with all stats"""
        fighter_id = fighter_rec.fighter_id
        
        # Get or create full data
        full_data = self._create_full_fighter_data(fighter_id)
        if not full_data:
            print("Fighter data not found.")
            pause()
            return
        
        while True:
            clear_screen()
            
            # Header
            if full_data.nickname:
                print_header(f'{full_data.name} "{full_data.nickname}"')
            else:
                print_header(f"FIGHTER: {full_data.name}")
            
            game = self.game_state
            player_camp = game.get_player_camp()
            is_player_fighter = (player_camp and full_data.camp_id == player_camp.camp_id)
            
            # === BIO INFO ===
            bio_lines = []
            if full_data.is_champion:
                bio_lines.append(colored(" DIVISION CHAMPION", Colors.GOLD))
            if getattr(full_data, 'is_generational', False):
                bio_lines.append(colored("   GENERATIONAL TALENT", Colors.GOLD))
            bio_lines.append(f"Weight Class: {full_data.weight_class}")
            bio_lines.append(f"Country: {full_data.country}")
            bio_lines.append(f"Age: {full_data.age}")
            bio_lines.append(f"Height: {full_data.height_display} | Reach: {full_data.reach_display}")
            bio_lines.append(f"Style: {full_data.fighting_style}")
            print_box(bio_lines, title="BIO")
            
            # === STATUS (Injury, Career Phase, Rivalries) ===
            status_lines = []
            
            # Career phase
            career_phase = self._get_fighter_career_phase(fighter_id)
            if career_phase:
                phase_color = Colors.GREEN if career_phase in ["Prospect", "Prime"] else Colors.YELLOW
                if career_phase == "Twilight":
                    phase_color = Colors.ORANGE
                status_lines.append(f"Career Phase: {colored(career_phase, phase_color)}")
            
            # Injury status
            if self._is_fighter_injured(fighter_id):
                weeks = self._get_fighter_recovery_weeks(fighter_id)
                status_lines.append(colored(f"INJURED - {weeks} weeks until cleared", Colors.RED))
            
            # Rivalries
            rivalries = self._get_fighter_rivalries(fighter_id)
            if rivalries:
                rival_str = ", ".join([
                    f"{r.fighter1_name if r.fighter2_id == fighter_id else r.fighter2_name}"
                    for r in rivalries[:3]  # Show top 3
                ])
                status_lines.append(f"Rivalries: {colored(rival_str, Colors.MAGENTA)}")
            
            if status_lines:
                print_box(status_lines, title="STATUS")
            
            # === RECORD ===
            record_lines = [
                f"Record: {format_record_colored(full_data.wins, full_data.losses, full_data.draws)}",
            ]
            if full_data.wins > 0:
                dec_wins = full_data.wins - full_data.ko_wins - full_data.sub_wins
                record_lines.append(f"Wins: {full_data.ko_wins} KO | {full_data.sub_wins} SUB | {dec_wins} DEC")
            if full_data.title_defenses > 0:
                record_lines.append(f"Title Defenses: {full_data.title_defenses}")
            if full_data.fotn_awards > 0:
                record_lines.append(colored(f"Fight of the Night: {full_data.fotn_awards}x", Colors.GOLD))
            if full_data.win_streak > 0:
                record_lines.append(colored(f"Win Streak: {full_data.win_streak}", Colors.WIN))
            elif full_data.lose_streak > 0:
                record_lines.append(colored(f"Losing Streak: {full_data.lose_streak}", Colors.LOSS))
            print_box(record_lines, title="RECORD")
            
            # === ATTRIBUTES ===
            print()
            print(f"  {colored('ATTRIBUTES', Colors.BOLD)}  (Overall: {colored(str(full_data.overall_rating), Colors.HIGHLIGHT)})")
            print()
            
            # Physical
            print(f"  {colored('Physical:', Colors.CYAN)}")
            print(f"    Strength:  {stat_letter_grade(full_data.strength):>6}  ({full_data.strength})")
            print(f"    Speed:     {stat_letter_grade(full_data.speed):>6}  ({full_data.speed})")
            print(f"    Cardio:    {stat_letter_grade(full_data.cardio):>6}  ({full_data.cardio})")
            print(f"    Chin:      {stat_letter_grade(full_data.chin):>6}  ({full_data.chin})")
            print()
            
            # Striking
            print(f"  {colored('Striking:', Colors.ORANGE)}")
            print(f"    Boxing:    {stat_letter_grade(full_data.boxing):>6}  ({full_data.boxing})")
            print(f"    Kicks:     {stat_letter_grade(full_data.kicks):>6}  ({full_data.kicks})")
            print(f"    Clinch:    {stat_letter_grade(full_data.clinch_striking):>6}  ({full_data.clinch_striking})")
            print(f"    Defense:   {stat_letter_grade(full_data.striking_defense):>6}  ({full_data.striking_defense})")
            print()
            
            # Grappling
            print(f"  {colored('Grappling:', Colors.MAGENTA)}")
            print(f"    Wrestling: {stat_letter_grade(full_data.wrestling):>6}  ({full_data.wrestling})")
            print(f"    BJJ:       {stat_letter_grade(full_data.bjj):>6}  ({full_data.bjj})")
            print(f"    TD Def:    {stat_letter_grade(full_data.takedown_defense):>6}  ({full_data.takedown_defense})")
            print()
            
            # Mental
            print(f"  {colored('Mental:', Colors.YELLOW)}")
            print(f"    Heart:     {stat_letter_grade(full_data.heart):>6}  ({full_data.heart})")
            print(f"    Fight IQ:  {stat_letter_grade(full_data.fight_iq):>6}  ({full_data.fight_iq})")
            print(f"    Composure: {stat_letter_grade(full_data.composure):>6}  ({full_data.composure})")
            print()
            
            # === TRAITS ===
            if full_data.traits:
                print(f"  {colored('TRAITS', Colors.BOLD)}")
                print()
                for trait_name in full_data.traits:
                    description = get_trait_description(trait_name)
                    category = get_trait_category(trait_name)
                    
                    # Color based on category
                    category_colors = {
                        "offensive": Colors.RED,
                        "defensive": Colors.CYAN,
                        "cardio": Colors.GREEN,
                        "mental": Colors.YELLOW,
                        "training": Colors.MAGENTA,
                    }
                    trait_color = category_colors.get(category, Colors.WHITE)
                    
                    print(f"    {colored(trait_name, trait_color)}")
                    print(f"      {description}")
                print()
            
            # Menu
            if is_player_fighter:
                options = [
                    ("1", "Training Camp"),
                    ("2", "Find Opponents"),
                    ("3", "Fight History"),
                    ("4", "Release Fighter"),
                    ("0", "Back"),
                ]
            else:
                options = [
                    ("1", "Fight History"),
                    ("0", "Back"),
                ]
            
            print_menu(options)
            
            if is_player_fighter:
                choice = get_choice(["1", "2", "3", "4", "0"])
                if choice == "0":
                    return
                elif choice == "1":
                    self.show_training_menu(full_data)
                elif choice == "2":
                    self.find_opponents_for_fighter(full_data)
                elif choice == "3":
                    self.show_fighter_fight_history(fighter_id)
                elif choice == "4":
                    if confirm(f"Release {full_data.name}?"):
                        self.release_fighter(fighter_id)
                        return
            else:
                choice = get_choice(["1", "0"])
                if choice == "0":
                    return
                elif choice == "1":
                    self.show_fighter_fight_history(fighter_id)
    
    def show_fighter_fight_history(self, fighter_id: str) -> None:
        """Show a fighter's fight history"""
        full_data = self.fighter_data.get(fighter_id)
        name = full_data.name if full_data else "Fighter"
        
        # Find fights involving this fighter
        fighter_fights = [
            r for r in self.all_fight_results.values()
            if r.fighter1_id == fighter_id or r.fighter2_id == fighter_id
        ]
        
        if not fighter_fights:
            clear_screen()
            print_header(f"FIGHT HISTORY: {name}")
            print("No recorded fights yet.")
            print()
            if full_data:
                print(f"Career Record: {format_record_colored(full_data.wins, full_data.losses)}")
            pause()
            return
        
        fighter_fights.sort(key=lambda r: r.week, reverse=True)
        
        while True:
            clear_screen()
            print_header(f"FIGHT HISTORY: {name}")
            
            if full_data:
                print(f"  Record: {format_record_colored(full_data.wins, full_data.losses)}")
                print()
            
            for i, fight in enumerate(fighter_fights[:15], 1):
                # Determine if this fighter won or lost
                if fight.winner_id == fighter_id:
                    result = colored("W", Colors.WIN)
                    opponent = fight.loser_name
                elif fight.loser_id == fighter_id:
                    result = colored("L", Colors.LOSS)
                    opponent = fight.winner_name
                else:
                    result = colored("D", Colors.NEUTRAL)
                    opponent = fight.fighter1_name if fight.fighter2_id == fighter_id else fight.fighter2_name
                
                method_str = fight.method
                if fight.method != "DEC" and fight.method != "DRAW":
                    method_str = f"{fight.method} R{fight.round_finished}"
                
                print(f"  [{i:2}] {result} vs {opponent}")
                print(f"       {method_str} | {fight.event_name} (Week {fight.week})")
                print()
            
            print(f"  [0] Back")
            print()
            print("  Select a fight to view details")
            
            choice = get_input("> ")
            
            if choice == "0":
                return
            
            try:
                index = int(choice)
                if 1 <= index <= len(fighter_fights):
                    self.show_fight_details(fighter_fights[index - 1])
            except ValueError:
                pass
    
    def release_fighter(self, fighter_id: str) -> None:
        """Release a fighter"""
        if fighter_id in self.game_state.fighters:
            self.game_state.fighters[fighter_id].camp_id = None
            self.game_state.free_agents.add(fighter_id)
        
        if fighter_id in self.fighter_data:
            name = self.fighter_data[fighter_id].name
            self.fighter_data[fighter_id].camp_id = None
        else:
            name = "Fighter"
        
        # Cancel fights
        self.player_scheduled_fights = [
            f for f in self.player_scheduled_fights if f.get("fighter1_id") != fighter_id
        ]
        
        # Remove offers
        self.fight_offers = [o for o in self.fight_offers if o.fighter_id != fighter_id]
        
        self.news_feed.insert(0, NewsItem(
            headline=f"{name} has been released",
            category="signing",
            week=self.game_state.week_number,
        ))
        
        print(f"{name} released.")
        pause()
    
    # -------------------------------------------------------------------------
    # Training System
    # -------------------------------------------------------------------------
    
    def show_training_menu(self, fighter: FighterFullData) -> None:
        """Training options for a fighter"""
        clear_screen()
        print_header(f"TRAINING: {fighter.name}")
        
        active_camp = None
        if self._training_system:
            active_camp = self._training_system.get_camp(fighter.fighter_id)
        
        if active_camp and not active_camp.is_complete:
            print(f"  ACTIVE TRAINING CAMP")
            print()
            print(f"  Focus: {active_camp.focus.value}")
            print(f"  Progress: {active_camp.weeks_completed}/{active_camp.total_weeks} weeks")
            print(f"  Gains: +{active_camp.total_gains} points")
            print()
            
            options = [
                ("1", "Continue Training"),
                ("2", "End Camp Early"),
                ("0", "Back"),
            ]
        else:
            print("  No active training camp.")
            print()
            
            options = [
                ("1", "Start New Camp"),
                ("0", "Back"),
            ]
        
        print_menu(options)
        
        choice = get_choice(["1", "2", "0"] if active_camp else ["1", "0"])
        
        if choice == "1":
            if active_camp and not active_camp.is_complete:
                print("Training continues...")
            else:
                self.start_training_camp(fighter)
        elif choice == "2" and active_camp:
            if self._training_system:
                self._training_system.end_camp(fighter.fighter_id)
            print("Camp ended.")
        
        pause()
    
    def start_training_camp(self, fighter: FighterFullData) -> None:
        """Start a training camp"""
        if not self._training_system:
            print("Training system not available.")
            return
        
        print()
        print("Select training focus:")
        print()
        
        focuses = [
            ("1", "Striking - Improve boxing, kicks, power"),
            ("2", "Jiu-Jitsu - Improve BJJ, submissions"),
            ("3", "Wrestling - Improve takedowns, defense"),
            ("4", "Conditioning - Improve cardio, strength"),
            ("5", "Balanced - All-around"),
        ]
        print_menu(focuses)
        
        choice = get_choice(["1", "2", "3", "4", "5"])
        if not choice:
            return
        
        print()
        print("Select duration:")
        print("  [1] 4 weeks")
        print("  [2] 6 weeks")
        print("  [3] 8 weeks")
        print()
        
        dur_choice = get_choice(["1", "2", "3"])
        duration_map = {"1": 4, "2": 6, "3": 8}
        weeks = duration_map.get(dur_choice, 6)
        
        try:
            from systems.training import TrainingFocus, TrainingIntensity
            
            focus_map = {
                "1": TrainingFocus.STRIKING,
                "2": TrainingFocus.JIUJITSU,
                "3": TrainingFocus.WRESTLING,
                "4": TrainingFocus.CONDITIONING,
                "5": TrainingFocus.BALANCED,
            }
            
            focus = focus_map.get(choice, TrainingFocus.BALANCED)
            player_camp = self.game_state.get_player_camp()
            camp_id = player_camp.camp_id if player_camp else "player_camp"
            
            self._training_system.start_camp(
                fighter_id=fighter.fighter_id,
                camp_id=camp_id,
                focus=focus,
                intensity=TrainingIntensity.MODERATE,
                weeks=weeks,
            )
            
            print()
            print(f"[OK] Training camp started!")
            print(f"  Focus: {focus.value}")
            print(f"  Duration: {weeks} weeks")
        except ImportError:
            print("Training camp started (simplified).")
    
    # -------------------------------------------------------------------------
    # Fight Offers with Tier-Based Scheduling
    # -------------------------------------------------------------------------
    
    def _get_camp_tier(self) -> str:
        """Get player's camp tier"""
        player_camp = self.game_state.get_player_camp()
        if player_camp and hasattr(player_camp, 'tier'):
            tier = player_camp.tier
            return tier.name if hasattr(tier, 'name') else str(tier)
        return "GARAGE"
    
    def _generate_fight_offers(self) -> None:
        """Generate fight offers using smart matchmaking."""
        game = self.game_state
        player_camp = game.get_player_camp()
        
        if not player_camp:
            return
        
        self.fight_offers = []
        
        tier = self._get_camp_tier()
        min_weeks = MIN_WEEKS_BY_TIER.get(tier, 4)
        max_weeks = MAX_WEEKS_BY_TIER.get(tier, 8)
        
        player_fighters = [
            f for f in game.fighters.values()
            if getattr(f, 'camp_id', None) == player_camp.camp_id and f.is_active
        ]
        
        if not player_fighters:
            return
        
        for fighter in player_fighters:
            if any(f.get("fighter1_id") == fighter.fighter_id for f in self.player_scheduled_fights):
                continue
            
            # Skip fighters on cooldown (recovering from loss)
            if fighter.fighter_id in self._fighter_cooldowns and self._fighter_cooldowns[fighter.fighter_id] > 0:
                continue
            
            # Get smart matchup scores
            scored_opponents = self._score_all_opponents(fighter)
            
            # Take top 5-6 quality matches
            num_offers = min(len(scored_opponents), 6)
            
            for matchup in scored_opponents[:num_offers]:
                opp = matchup["opponent"]
                score_data = matchup["score_data"]
                
                weeks_away = random.randint(min_weeks, max_weeks)
                
                # Calculate purse based on matchup quality and ratings
                base_purse = 5000
                rating_bonus = (fighter.overall_rating + opp.overall_rating) * 50
                quality_bonus = int(score_data["total_score"] * 20)
                purse = base_purse + rating_bonus + quality_bonus
                
                is_title = fighter.is_champion or opp.is_champion
                if is_title:
                    purse *= 3
                    weeks_away = max(weeks_away, 8)
                
                # Create enhanced offer with matchup data
                offer = FightOffer(
                    offer_id=f"offer_{len(self.fight_offers)}",
                    fighter_id=fighter.fighter_id,
                    fighter_name=fighter.name,
                    opponent_id=opp.fighter_id,
                    opponent_name=opp.name,
                    opponent_record=format_record(opp.wins, opp.losses),
                    opponent_rating=opp.overall_rating,
                    weight_class=fighter.weight_class,
                    event_name="DFC Fight Night",
                    event_date="TBD",
                    weeks_away=weeks_away,
                    purse=purse,
                    is_title_fight=is_title,
                    is_main_event=is_title or fighter.overall_rating >= 75,
                    matchup_quality=score_data["quality"],
                )
                
                # Store extra matchup data for display
                offer.matchup_data = score_data
                
                self.fight_offers.append(offer)
    
    def _score_all_opponents(self, fighter) -> list:
        """Score all potential opponents using smart matchmaking."""
        game = self.game_state
        player_camp = game.get_player_camp()
        
        # Get fighter's rank
        fighter_rank = self._get_fighter_division_rank(fighter)
        fighter_data = self.fighter_data.get(fighter.fighter_id)
        fighter_streak = fighter_data.win_streak if fighter_data else 0
        
        scored = []
        
        for opp in game.fighters.values():
            # Basic filters
            if opp.weight_class != fighter.weight_class:
                continue
            if opp.fighter_id == fighter.fighter_id:
                continue
            if player_camp and opp.camp_id == player_camp.camp_id:
                continue
            if not opp.is_active:
                continue
            
            # Get opponent data
            opp_rank = self._get_fighter_division_rank(opp)
            opp_data = self.fighter_data.get(opp.fighter_id)
            if not opp_data:
                opp_data = self._create_full_fighter_data(opp.fighter_id)
            opp_streak = opp_data.win_streak if opp_data else 0
            
            # Calculate matchup scores
            score_data = self._calculate_matchup_score(
                fighter, opp, fighter_rank, opp_rank, 
                fighter_streak, opp_streak, fighter_data, opp_data
            )
            
            # Only include reasonable matchups (score > 30)
            if score_data["total_score"] >= 30:
                # Check if AI would accept this fight
                will_accept, decline_reason, accept_prob = self._ai_will_accept_fight(
                    ai_fighter=opp,
                    player_fighter=fighter,
                    is_title_fight=fighter.is_champion or opp.is_champion,
                    is_main_event=fighter.overall_rating >= 75,
                    weeks_out=8,
                    purse=5000 + (fighter.overall_rating + opp.overall_rating) * 50,
                )
                
                # Add acceptance info to score data
                score_data["ai_will_accept"] = will_accept
                score_data["ai_decline_reason"] = decline_reason
                score_data["ai_accept_probability"] = accept_prob
                
                # Only show offers where AI is likely to accept (>30% chance)
                # But always show if they WILL accept (rolled yes)
                if will_accept or accept_prob >= 0.30:
                    scored.append({
                        "opponent": opp,
                        "score_data": score_data,
                    })
        
        # Sort by score descending
        scored.sort(key=lambda x: -x["score_data"]["total_score"])
        
        return scored
    
    def _calculate_matchup_score(self, fighter, opp, f_rank, o_rank, f_streak, o_streak, f_data, o_data) -> dict:
        """Calculate comprehensive matchup score."""
        scores = {
            "ranking": 0,
            "skill": 0,
            "streak": 0,
            "style": 0,
            "freshness": 0,
            "narrative": 0,
        }
        tags = []
        
        # === RANKING SCORE (0-30) ===
        rank_diff = abs((f_rank or 20) - (o_rank or 20))
        if rank_diff <= 2:
            scores["ranking"] = 30
        elif rank_diff <= 5:
            scores["ranking"] = 22
        elif rank_diff <= 8:
            scores["ranking"] = 15
        elif rank_diff <= 12:
            scores["ranking"] = 8
        else:
            scores["ranking"] = 3
        
        # Determine direction
        direction = "LATERAL"
        if f_rank and o_rank:
            if o_rank < f_rank - 2:
                direction = "STEP_UP"
                tags.append("STEP UP")
            elif o_rank > f_rank + 2:
                direction = "STEP_DOWN"
                tags.append("STEP DOWN")
        elif o_rank and not f_rank:
            direction = "STEP_UP"
            tags.append("STEP UP")
        
        # === SKILL SCORE (0-20) ===
        rating_diff = abs(fighter.overall_rating - opp.overall_rating)
        if rating_diff <= 5:
            scores["skill"] = 20
        elif rating_diff <= 10:
            scores["skill"] = 15
        elif rating_diff <= 15:
            scores["skill"] = 10
        elif rating_diff <= 20:
            scores["skill"] = 5
        else:
            scores["skill"] = 0
        
        # === STREAK SCORE (0-15) ===
        if f_streak >= 3 and o_streak >= 3:
            scores["streak"] = 15
            tags.append("STREAK CLASH")
        elif f_streak >= 3 or o_streak >= 3:
            scores["streak"] = 10
        elif f_streak >= 2 or o_streak >= 2:
            scores["streak"] = 5
        
        # === STYLE SCORE (0-15) ===
        style_edge = None
        if f_data and o_data and SCOUTING_AVAILABLE:
            try:
                analysis = get_matchup_analysis(f_data, o_data)
                f_advs = len(analysis.fighter1_advantages)
                o_advs = len(analysis.fighter2_advantages)
                
                if f_advs > o_advs + 1:
                    scores["style"] = 12
                    style_edge = "YOU"
                    tags.append("STYLE EDGE")
                elif o_advs > f_advs + 1:
                    scores["style"] = 8
                    style_edge = "THEM"
                    tags.append("STYLE CLASH")
                else:
                    scores["style"] = 10
                    style_edge = "EVEN"
            except:
                scores["style"] = 8
        else:
            scores["style"] = 8
        
        # === FRESHNESS SCORE (0-10) ===
        # Check if they fought recently
        recent = self._check_recent_matchup(fighter.fighter_id, opp.fighter_id)
        if recent:
            scores["freshness"] = 2
            if recent.get("result") == "loss":
                tags.append("REVENGE")
            else:
                tags.append("REMATCH")
        else:
            scores["freshness"] = 10
        
        # === NARRATIVE SCORE (0-10) ===
        # Title implications
        if fighter.is_champion or opp.is_champion:
            scores["narrative"] = 10
            tags.append("TITLE FIGHT")
        elif (f_rank and f_rank <= 5) or (o_rank and o_rank <= 5):
            scores["narrative"] = 8
            if f_rank and f_rank <= 3 and not opp.is_champion:
                tags.append("TITLE PATH")
        elif f_streak >= 3:
            scores["narrative"] = 6
        
        # Calculate total
        total = sum(scores.values())
        
        # Determine quality label
        if total >= 85:
            quality = "Excellent"
        elif total >= 65:
            quality = "Good"
        elif total >= 45:
            quality = "Fair"
        else:
            quality = "Poor"
        
        # Calculate risk/reward
        if direction == "STEP_UP":
            risk = 4
            reward = 5
        elif direction == "STEP_DOWN":
            risk = 2
            reward = 2
        else:
            risk = 3
            reward = 3
        
        # Adjust based on rating diff
        if opp.overall_rating > fighter.overall_rating + 5:
            risk = min(5, risk + 1)
        elif opp.overall_rating < fighter.overall_rating - 5:
            risk = max(1, risk - 1)
        
        return {
            "total_score": total,
            "scores": scores,
            "quality": quality,
            "tags": tags,
            "direction": direction,
            "style_edge": style_edge,
            "risk": risk,
            "reward": reward,
            "opponent_rank": o_rank,
            "opponent_streak": o_streak,
        }
    

    def _get_fighter_personality(self, fighter_id: str) -> Any:
        """Get or generate personality for a fighter."""
        if not AI_BEHAVIOR_AVAILABLE:
            return None
        
        if fighter_id in self._fighter_personalities:
            return self._fighter_personalities[fighter_id]
        
        # Generate new personality
        fighter = self.game_state.fighters.get(fighter_id)
        if not fighter:
            return None
        
        personality = generate_fighter_personality(
            fighter_id=fighter_id,
            age=getattr(fighter, 'age', 25),
            wins=fighter.wins,
            losses=fighter.losses,
            is_champion=fighter.is_champion,
        )
        
        self._fighter_personalities[fighter_id] = personality
        return personality
    
    def _ai_will_accept_fight(
        self,
        ai_fighter,
        player_fighter,
        is_title_fight: bool = False,
        is_main_event: bool = False,
        weeks_out: int = 8,
        purse: int = 10000,
    ) -> Tuple[bool, Optional[str], float]:
        """
        Check if AI fighter will accept fight offer.
        
        Returns: (will_accept, decline_reason, acceptance_probability)
        """
        if not AI_BEHAVIOR_AVAILABLE or not self._ai_decision_engine:
            # Fallback: basic acceptance based on rating diff
            rating_diff = ai_fighter.overall_rating - player_fighter.overall_rating
            if rating_diff > 15:  # They're much better
                return random.random() < 0.4, "Opponent ranked too low", 0.4
            elif rating_diff < -15:  # They're much worse
                return random.random() < 0.7, None, 0.7
            return True, None, 0.6
        
        # Get personalities
        ai_personality = self._get_fighter_personality(ai_fighter.fighter_id)
        if not ai_personality:
            return True, None, 0.5
        
        # Get fighter data
        ai_data = self.fighter_data.get(ai_fighter.fighter_id)
        player_data = self.fighter_data.get(player_fighter.fighter_id)
        
        ai_rank = self._get_fighter_division_rank(ai_fighter)
        player_rank = self._get_fighter_division_rank(player_fighter)
        
        # Check fight history
        fought_before = False
        lost_to_opponent = False
        if hasattr(self, 'fight_history'):
            for result in self.fight_history:
                if hasattr(result, 'fighter1_id'):
                    if (result.fighter1_id == ai_fighter.fighter_id and 
                        result.fighter2_id == player_fighter.fighter_id):
                        fought_before = True
                        if result.winner_id == player_fighter.fighter_id:
                            lost_to_opponent = True
                    elif (result.fighter2_id == ai_fighter.fighter_id and 
                          result.fighter1_id == player_fighter.fighter_id):
                        fought_before = True
                        if result.winner_id == player_fighter.fighter_id:
                            lost_to_opponent = True
        
        # Use AI decision engine
        will_accept, breakdown = self._ai_decision_engine.evaluate_fight_offer(
            personality=ai_personality,
            fighter_rating=ai_fighter.overall_rating,
            fighter_rank=ai_rank,
            is_champion=ai_fighter.is_champion,
            wins=ai_fighter.wins,
            losses=ai_fighter.losses,
            win_streak=ai_data.win_streak if ai_data else 0,
            lose_streak=ai_data.lose_streak if ai_data else 0,
            weeks_since_fight=12,  # Approximate
            opponent_rating=player_fighter.overall_rating,
            opponent_rank=player_rank,
            opponent_id=player_fighter.fighter_id,
            is_title_fight=is_title_fight,
            is_main_event=is_main_event,
            weeks_out=weeks_out,
            purse=purse,
            fought_before=fought_before,
            lost_to_opponent=lost_to_opponent,
        )
        
        decline_reason = None if will_accept else breakdown.result_reason
        
        return will_accept, decline_reason, breakdown.final_probability
    
    def _get_personality_display(self, fighter_id: str) -> Dict[str, str]:
        """Get displayable personality info for a fighter."""
        if not AI_BEHAVIOR_AVAILABLE:
            return {}
        
        personality = self._get_fighter_personality(fighter_id)
        if not personality:
            return {}
        
        # Build display info
        info = {}
        
        # Mentality
        mentality_display = {
            "warrior": ("Warrior", "Lives to fight, takes any challenge"),
            "businessman": ("Businessman", "Smart career choices, calculated"),
            "glory_seeker": ("Glory Seeker", "Wants titles and big stages"),
            "journeyman": ("Journeyman", "Steady worker, always active"),
            "killer": ("Killer", "Aggressive, wants to hurt people"),
            "technician": ("Technician", "Selective perfectionist"),
        }
        m_key = personality.mentality.value
        if m_key in mentality_display:
            info["mentality"] = mentality_display[m_key][0]
            info["mentality_desc"] = mentality_display[m_key][1]
        
        # Risk profile
        risk_display = {
            "reckless": ("Reckless", "Takes any fight"),
            "aggressive": ("Aggressive", "Welcomes challenges"),
            "balanced": ("Balanced", "Weighs risk vs reward"),
            "cautious": ("Cautious", "Protects record"),
            "cowardly": ("Gun-shy", "Avoids tough fights"),
        }
        r_key = personality.risk_profile.value
        if r_key in risk_display:
            info["risk"] = risk_display[r_key][0]
            info["risk_desc"] = risk_display[r_key][1]
        
        # Activity
        activity_display = {
            "very_active": "Fights frequently",
            "active": "Stays busy",
            "normal": "Standard activity",
            "selective": "Picks fights carefully",
            "inactive": "Rarely fights",
        }
        a_key = personality.activity.value
        if a_key in activity_display:
            info["activity"] = activity_display[a_key]
        
        # Confidence indicator
        if personality.confidence > 70:
            info["confidence"] = "High confidence"
        elif personality.confidence < 30:
            info["confidence"] = "Low confidence"
        
        # Ego indicator
        if personality.ego > 70:
            info["ego"] = "Big ego"
        
        return info


    def _get_fighter_division_rank(self, fighter) -> int:
        """Get fighter's rank in their division (None if unranked)."""
        if fighter.is_champion:
            return 0
        
        # Use real rankings system if available
        if RANKINGS_AVAILABLE and self._rankings_system:
            try:
                from core.types import WeightClass
                wc = WeightClass(fighter.weight_class) if isinstance(fighter.weight_class, str) else fighter.weight_class
                rank = self._rankings_system.get_rank(fighter.fighter_id, wc)
                if rank is not None:
                    return rank
            except:
                pass
        
        # Fallback: Sort by overall_rating
        div_fighters = [f for f in self.game_state.fighters.values()
                       if f.weight_class == fighter.weight_class 
                       and f.is_active and not f.is_champion]
        div_fighters.sort(key=lambda f: f.overall_rating, reverse=True)
        
        for i, f in enumerate(div_fighters[:15], 1):
            if f.fighter_id == fighter.fighter_id:
                return i
        
        return None
    
    def _populate_rankings_system(self) -> None:
        """Populate rankings system from current fighters."""
        if not RANKINGS_AVAILABLE or not self._rankings_system:
            return
        
        try:
            from core.types import WeightClass
            
            # Group fighters by weight class
            by_division = {}
            for f in self.game_state.fighters.values():
                if not f.is_active:
                    continue
                wc = WeightClass(f.weight_class) if isinstance(f.weight_class, str) else f.weight_class
                if wc not in by_division:
                    by_division[wc] = []
                by_division[wc].append(f)
            
            # For each division, set champion and rank top 15
            for wc, fighters in by_division.items():
                # Sort by rating
                fighters.sort(key=lambda f: f.overall_rating, reverse=True)
                
                # Find champion (or highest rated becomes champ)
                champion = None
                for f in fighters:
                    if f.is_champion:
                        champion = f
                        break
                
                if champion:
                    self._rankings_system.set_champion(
                        champion.fighter_id,
                        champion.name,
                        wc,
                        week=self.game_state.current_week,
                        year=self.game_state.current_year,
                    )
                
                # Add top 15 to rankings
                rank_count = 0
                for f in fighters:
                    if f.is_champion:
                        continue
                    if rank_count >= 15:
                        break
                    
                    self._rankings_system.add_to_rankings(
                        f.fighter_id,
                        f.name,
                        wc,
                        target_rank=rank_count + 1,
                        week=self.game_state.current_week,
                        year=self.game_state.current_year,
                    )
                    rank_count += 1
            
        except Exception as e:
            pass
    
    def _process_ranking_changes(
        self,
        winner_id: str,
        winner_name: str,
        loser_id: str,
        loser_name: str,
        weight_class: str,
        method: str,
        was_title_fight: bool = False,
    ) -> List[Dict[str, Any]]:
        """Process ranking changes after a fight."""
        changes = []
        
        if not RANKINGS_AVAILABLE or not self._rankings_system:
            return changes
        
        try:
            from core.types import WeightClass, FightOutcome
            
            wc = WeightClass(weight_class) if isinstance(weight_class, str) else weight_class
            
            # Map method to FightOutcome
            method_upper = method.upper()
            if method_upper == "KO":
                outcome = FightOutcome.KO
            elif method_upper == "TKO":
                outcome = FightOutcome.TKO
            elif method_upper in ["SUB", "SUBMISSION"]:
                outcome = FightOutcome.SUBMISSION
            elif "SPLIT" in method_upper:
                outcome = FightOutcome.DECISION_SPLIT
            elif "MAJORITY" in method_upper:
                outcome = FightOutcome.DECISION_MAJORITY
            else:
                outcome = FightOutcome.DECISION_UNANIMOUS
            
            # Process the fight
            ranking_changes = self._rankings_system.process_fight_result(
                winner_id=winner_id,
                winner_name=winner_name,
                loser_id=loser_id,
                loser_name=loser_name,
                weight_class=wc,
                outcome=outcome,
                was_title_fight=was_title_fight,
                week=self.game_state.current_week,
                year=self.game_state.current_year,
            )
            
            # Convert to dict for display
            for change in ranking_changes:
                changes.append({
                    "fighter_id": change.fighter_id,
                    "fighter_name": change.fighter_name,
                    "old_rank": change.old_rank,
                    "new_rank": change.new_rank,
                    "reason": change.reason.value if hasattr(change.reason, 'value') else str(change.reason),
                    "is_promotion": change.is_promotion,
                    "positions_moved": change.positions_moved,
                    "is_big_mover": change.is_big_mover,
                })
            
        except Exception as e:
            pass
        
        return changes
    
    def _get_p4p_rankings(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Get pound-for-pound rankings."""
        if not RANKINGS_AVAILABLE or not self._rankings_system:
            return []
        
        try:
            p4p = self._rankings_system.calculate_p4p_rankings(
                current_week=self.game_state.current_week,
                current_year=self.game_state.current_year,
            )
            
            results = []
            for entry in p4p[:limit]:
                results.append({
                    "rank": entry.rank,
                    "fighter_id": entry.fighter_id,
                    "fighter_name": entry.fighter_name,
                    "weight_class": entry.weight_class.value if hasattr(entry.weight_class, 'value') else str(entry.weight_class),
                    "score": entry.score,
                    "is_champion": entry.is_champion,
                    "win_streak": entry.win_streak,
                    "title_defenses": entry.title_defenses,
                })
            
            return results
        except:
            return []
    
    def _check_recent_matchup(self, fighter1_id: str, fighter2_id: str) -> dict:
        """Check if these fighters have fought recently."""
        # Check fight history if available
        if not hasattr(self, 'fight_history') or not self.fight_history:
            return None
        
        try:
            for result in self.fight_history[-20:]:
                if hasattr(result, 'fighter1_id'):
                    if (result.fighter1_id == fighter1_id and result.fighter2_id == fighter2_id):
                        return {"fought": True, "result": "win" if result.winner_id == fighter1_id else "loss"}
                    if (result.fighter2_id == fighter1_id and result.fighter1_id == fighter2_id):
                        return {"fought": True, "result": "win" if result.winner_id == fighter1_id else "loss"}
        except:
            pass
        return None


    def _find_opponents_for_fighter_basic(self, fighter) -> List:
        """Find suitable opponents"""
        game = self.game_state
        player_camp = game.get_player_camp()
        
        opponents = []
        for opp in game.fighters.values():
            if opp.weight_class != fighter.weight_class:
                continue
            if opp.fighter_id == fighter.fighter_id:
                continue
            if player_camp and opp.camp_id == player_camp.camp_id:
                continue
            if not opp.is_active:
                continue
            if abs(opp.overall_rating - fighter.overall_rating) > 25:
                continue
            opponents.append(opp)
        
        opponents.sort(key=lambda o: abs(o.overall_rating - fighter.overall_rating))
        return opponents[:5]
    
    def _get_matchup_quality(self, rating1: int, rating2: int) -> str:
        """Get matchup quality string"""
        diff = abs(rating1 - rating2)
        if diff <= 5:
            return "Excellent"
        elif diff <= 10:
            return "Good"
        elif diff <= 15:
            return "Fair"
        else:
            return "Mismatch"
    
    def show_fight_offers(self) -> None:
        """Display fight offers with smart matchmaking insights."""
        clear_screen()
        print_header("FIGHT OFFERS")
        
        tier = self._get_camp_tier()
        min_weeks = MIN_WEEKS_BY_TIER.get(tier, 4)
        max_weeks = MAX_WEEKS_BY_TIER.get(tier, 8)
        
        print(f"  {colored('Camp:', Colors.CYAN)} {tier} | Schedule window: {min_weeks}-{max_weeks} weeks")
        print()
        
        # Check for fighters on cooldown
        player_camp = self.game_state.get_player_camp()
        cooldown_fighters = []
        if player_camp:
            for fighter in self.game_state.fighters.values():
                if getattr(fighter, 'camp_id', None) == player_camp.camp_id and fighter.is_active:
                    if fighter.fighter_id in self._fighter_cooldowns and self._fighter_cooldowns[fighter.fighter_id] > 0:
                        weeks = self._fighter_cooldowns[fighter.fighter_id]
                        fighter_data = self.fighter_data.get(fighter.fighter_id)
                        streak = fighter_data.lose_streak if fighter_data else 0
                        cooldown_fighters.append((fighter.name, weeks, streak))
        
        if not self.fight_offers:
            print("  No fight offers at this time.")
            print()
            
            # Show cooldown info
            if cooldown_fighters:
                print(f"  {colored('FIGHTERS RECOVERING:', Colors.ORANGE)}")
                for name, weeks, streak in cooldown_fighters:
                    streak_str = f" ({streak}L streak)" if streak > 1 else ""
                    print(f"    {name}: {weeks} weeks until available{streak_str}")
                print()
            
            print(f"  {colored('TIP:', Colors.YELLOW)} Offers generate every 2 weeks.")
            print(f"       Fighters need recovery time after losses.")
            pause()
            return
        
        # Show cooldown info if any fighters recovering
        if cooldown_fighters:
            print(f"  {colored('RECOVERING:', Colors.ORANGE)} ", end="")
            recovery_strs = [f"{name} ({weeks}wks)" for name, weeks, _ in cooldown_fighters]
            print(", ".join(recovery_strs))
            print()
        
        # Group offers by fighter
        offers_by_fighter = {}
        for offer in self.fight_offers:
            if offer.fighter_id not in offers_by_fighter:
                offers_by_fighter[offer.fighter_id] = []
            offers_by_fighter[offer.fighter_id].append(offer)
        
        print(f"  {colored(f'{len(self.fight_offers)} Available Offers', Colors.WIN)}")
        print()
        
        offer_index = 0
        for fighter_id, offers in offers_by_fighter.items():
            fighter = self.game_state.fighters.get(fighter_id)
            fighter_data = self.fighter_data.get(fighter_id)
            
            if fighter:
                f_rank = self._get_fighter_division_rank(fighter)
                rank_str = f"#{f_rank}" if f_rank else "Unranked"
                div_abbrev = self._get_division_abbrev(fighter.weight_class)
                streak_str = f" W{fighter_data.win_streak}" if fighter_data and fighter_data.win_streak >= 2 else ""
                
                print(f"  {colored(fighter.name, Colors.HIGHLIGHT)} ({rank_str} {div_abbrev} | {fighter.overall_rating} OVR{streak_str})")
                print(f"  {'-' * 60}")
            
            for offer in offers:
                offer_index += 1
                self._display_offer_line(offer_index, offer, fighter_data)
            
            print()
        
        print_divider()
        print()
        print(f"  {colored('[#]', Colors.CYAN)} View full breakdown & accept")
        print(f"  {colored('[0]', Colors.CYAN)} Back")
        print()
        
        choice = get_input("Select offer: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(self.fight_offers):
                self.view_fight_offer(self.fight_offers[index - 1])
        except ValueError:
            pass
    
    def _display_offer_line(self, index: int, offer: FightOffer, your_data) -> None:
        """Display a single offer line with matchmaking insights."""
        # Get matchup data if available
        matchup = getattr(offer, 'matchup_data', None)
        
        opp_data = self.fighter_data.get(offer.opponent_id)
        if not opp_data:
            opp_data = self._create_full_fighter_data(offer.opponent_id)
        
        # Build tags
        tags = []
        if offer.is_title_fight:
            tags.append(colored("TITLE", Colors.GOLD))
        
        if matchup:
            for tag in matchup.get("tags", []):
                if tag == "STEP UP":
                    tags.append(colored("^ UP", Colors.GREEN))
                elif tag == "STEP DOWN":
                    tags.append(colored("v DOWN", Colors.YELLOW))
                elif tag == "STYLE EDGE":
                    tags.append(colored("+ EDGE", Colors.CYAN))
                elif tag == "STYLE CLASH":
                    tags.append(colored("! CLASH", Colors.RED))
                elif tag == "STREAK CLASH":
                    tags.append(colored("* STREAKS", Colors.ORANGE))
                elif tag == "REVENGE":
                    tags.append(colored("REVENGE", Colors.MAGENTA))
                elif tag == "TITLE PATH":
                    tags.append(colored("-> TITLE", Colors.GOLD))
        
        tag_str = " ".join(tags) if tags else ""
        
        # Opponent info line
        opp_rank = matchup.get("opponent_rank") if matchup else None
        opp_streak = matchup.get("opponent_streak", 0) if matchup else 0
        
        rank_str = f"#{opp_rank}" if opp_rank else "UR"
        streak_str = f" W{opp_streak}" if opp_streak >= 2 else ""
        
        # Style from scouting
        style_str = ""
        if SCOUTING_AVAILABLE and opp_data:
            try:
                report = scout_fighter(opp_data)
                style_str = f" | {report.fighting_style}"
            except:
                pass
        
        # Risk/Reward stars
        risk = matchup.get("risk", 3) if matchup else 3
        reward = matchup.get("reward", 3) if matchup else 3
        risk_str = colored("*" * risk + "-" * (5-risk), Colors.RED if risk >= 4 else Colors.YELLOW if risk >= 3 else Colors.GREEN)
        reward_str = colored("*" * reward + "-" * (5-reward), Colors.GREEN if reward >= 4 else Colors.CYAN)
        
        # Print
        print()
        print(f"    [{colored(str(index), Colors.CYAN)}] vs {colored(offer.opponent_name, Colors.HIGHLIGHT)}")
        print(f"        {rank_str} | {offer.opponent_record} | {offer.opponent_rating} OVR{streak_str}{style_str}")
        print(f"        Risk: {risk_str}  Reward: {reward_str}  {tag_str}")
        # Show acceptance likelihood
        if matchup:
            accept_prob = matchup.get("ai_accept_probability", 0.5)
            will_accept = matchup.get("ai_will_accept", True)
            decline_reason = matchup.get("ai_decline_reason")
            
            if not will_accept and decline_reason:
                accept_str = colored(f"[DECLINED: {decline_reason}]", Colors.RED)
            elif accept_prob >= 0.7:
                accept_str = colored("[EAGER]", Colors.GREEN)
            elif accept_prob >= 0.5:
                accept_str = colored("[INTERESTED]", Colors.CYAN)
            elif accept_prob >= 0.3:
                accept_str = colored("[HESITANT]", Colors.YELLOW)
            else:
                accept_str = colored("[RELUCTANT]", Colors.RED)
        else:
            accept_str = ""
        
        print(f"        {offer.weeks_away}wks | {colored(format_money(offer.purse), Colors.WIN)} {accept_str}")


    def view_fight_offer(self, offer: FightOffer) -> None:
        """View fight offer with full matchmaking breakdown."""
        clear_screen()
        
        title = "TITLE FIGHT OFFER" if offer.is_title_fight else "FIGHT OFFER"
        print_header(title)
        
        your_data = self.fighter_data.get(offer.fighter_id)
        opp_data = self.fighter_data.get(offer.opponent_id)
        if not opp_data:
            opp_data = self._create_full_fighter_data(offer.opponent_id)
        
        your_fighter = self.game_state.fighters.get(offer.fighter_id)
        opp_fighter = self.game_state.fighters.get(offer.opponent_id)
        
        # === TALE OF TAPE ===
        if TALE_OF_TAPE_AVAILABLE and your_data and opp_data:
            try:
                tape = generate_tale_of_tape(your_data, opp_data)
                tape_lines = format_tale_of_tape_compact(tape)
                for line in tape_lines:
                    print(line)
                print()
            except:
                self._show_basic_offer_display(your_data, opp_data, offer)
        else:
            self._show_basic_offer_display(your_data, opp_data, offer)
        
        # === MATCHUP ANALYSIS ===
        matchup = getattr(offer, 'matchup_data', None)
        
        print_divider()
        print(f"  {colored('MATCHUP ANALYSIS', Colors.CYAN)}")
        print()
        
        # Opponent personality hints
        if opp_data:
            personality_info = self._get_personality_display(opp_data.fighter_id)
            if personality_info:
                mentality = personality_info.get('mentality', 'Unknown')
                risk = personality_info.get('risk', 'Unknown')
                print(f"    Opponent Profile: {colored(mentality, Colors.HIGHLIGHT)} | {risk}")
                
                # Acceptance status
                if matchup:
                    accept_prob = matchup.get("ai_accept_probability", 0.5)
                    will_accept = matchup.get("ai_will_accept", True)
                    decline_reason = matchup.get("ai_decline_reason")
                    
                    if not will_accept:
                        print(f"    Status: {colored('DECLINED', Colors.RED)} - {decline_reason}")
                    elif accept_prob >= 0.7:
                        print(f"    Status: {colored('EAGER TO FIGHT', Colors.GREEN)} ({int(accept_prob*100)}% acceptance)")
                    elif accept_prob >= 0.5:
                        print(f"    Status: {colored('INTERESTED', Colors.CYAN)} ({int(accept_prob*100)}% acceptance)")
                    else:
                        print(f"    Status: {colored('HESITANT', Colors.YELLOW)} ({int(accept_prob*100)}% acceptance)")
                print()
        
        # Tags
        if matchup and matchup.get("tags"):
            tag_display = []
            for tag in matchup["tags"]:
                if tag in ["STEP UP", "TITLE PATH"]:
                    tag_display.append(colored(f"[{tag}]", Colors.GREEN))
                elif tag in ["STEP DOWN"]:
                    tag_display.append(colored(f"[{tag}]", Colors.YELLOW))
                elif tag in ["STYLE EDGE"]:
                    tag_display.append(colored(f"[{tag}]", Colors.CYAN))
                elif tag in ["REVENGE", "STREAK CLASH"]:
                    tag_display.append(colored(f"[{tag}]", Colors.ORANGE))
                else:
                    tag_display.append(f"[{tag}]")
            print(f"    {' '.join(tag_display)}")
            print()
        
        # Risk/Reward
        if matchup:
            risk = matchup.get("risk", 3)
            reward = matchup.get("reward", 3)
            
            risk_bar = colored("*" * risk, Colors.RED) + colored("-" * (5-risk), Colors.DIM)
            reward_bar = colored("*" * reward, Colors.GREEN) + colored("-" * (5-reward), Colors.DIM)
            
            print(f"    Difficulty: [{risk_bar}] ", end="")
            if risk >= 4:
                print(colored("Hard", Colors.RED))
            elif risk >= 3:
                print(colored("Moderate", Colors.YELLOW))
            else:
                print(colored("Easier", Colors.GREEN))
            
            print(f"    Reward:     [{reward_bar}] ", end="")
            if reward >= 4:
                print(colored("High Stakes", Colors.GREEN))
            elif reward >= 3:
                print(colored("Standard", Colors.CYAN))
            else:
                print(colored("Low Stakes", Colors.YELLOW))
            print()
        
        # Style Analysis
        if SCOUTING_AVAILABLE and your_data and opp_data:
            try:
                analysis = get_matchup_analysis(your_data, opp_data)
                
                if analysis.fighter1_advantages:
                    print(f"    {colored('Your Advantages:', Colors.GREEN)}")
                    for adv in analysis.fighter1_advantages[:3]:
                        print(f"      + {adv}")
                
                if analysis.fighter2_advantages:
                    print(f"    {colored('Their Advantages:', Colors.RED)}")
                    for adv in analysis.fighter2_advantages[:3]:
                        print(f"      - {adv}")
                
                print()
            except:
                pass
        
        # === IF YOU WIN / IF YOU LOSE ===
        print_divider()
        print(f"  {colored('STAKES', Colors.GOLD)}")
        print()
        
        your_rank = self._get_fighter_division_rank(your_fighter) if your_fighter else None
        opp_rank = matchup.get("opponent_rank") if matchup else self._get_fighter_division_rank(opp_fighter) if opp_fighter else None
        
        # Predict win outcome
        if your_rank and opp_rank:
            if opp_rank < your_rank:  # Fighting up
                new_rank = max(1, opp_rank + 1)
                print(f"    {colored('IF YOU WIN:', Colors.GREEN)}")
                print(f"      -> Move from #{your_rank} to ~#{new_rank}")
                if opp_fighter and opp_fighter.is_champion:
                    print(f"      -> {colored('BECOME CHAMPION!', Colors.GOLD)}")
                elif new_rank <= 3:
                    print(f"      -> {colored('Title shot territory!', Colors.GOLD)}")
                elif new_rank <= 5:
                    print(f"      -> Enter top 5 contenders")
            elif opp_rank > your_rank:  # Fighting down
                print(f"    {colored('IF YOU WIN:', Colors.GREEN)}")
                print(f"      -> Stay at #{your_rank}")
                print(f"      -> Smaller ranking gain (fighting down)")
            else:
                print(f"    {colored('IF YOU WIN:', Colors.GREEN)}")
                print(f"      -> Move up 1-2 spots")
        elif opp_rank and not your_rank:  # You're unranked
            print(f"    {colored('IF YOU WIN:', Colors.GREEN)}")
            print(f"      -> Enter rankings around #{min(15, opp_rank + 3)}")
            print(f"      -> Major boost to reputation")
        else:
            print(f"    {colored('IF YOU WIN:', Colors.GREEN)}")
            print(f"      -> Build momentum")
        
        # Add win streak info
        if your_data and your_data.win_streak >= 2:
            print(f"      -> Extend win streak to {your_data.win_streak + 1}!")
        
        print()
        
        # Predict loss outcome
        if your_rank:
            if opp_rank and opp_rank > your_rank:  # Losing to lower ranked
                drop = min(5, opp_rank - your_rank + 1)
                print(f"    {colored('IF YOU LOSE:', Colors.RED)}")
                print(f"      -> Drop from #{your_rank} to ~#{your_rank + drop}")
                print(f"      -> Major setback (lost to lower ranked)")
            elif opp_rank and opp_rank < your_rank:  # Losing to higher ranked
                print(f"    {colored('IF YOU LOSE:', Colors.RED)}")
                print(f"      -> Stay around #{your_rank}")
                print(f"      -> No shame losing to higher ranked")
            else:
                print(f"    {colored('IF YOU LOSE:', Colors.RED)}")
                print(f"      -> Drop 1-2 spots")
        else:
            print(f"    {colored('IF YOU LOSE:', Colors.RED)}")
            print(f"      -> Stay unranked")
            print(f"      -> Need more wins to break through")
        
        # Win streak broken
        if your_data and your_data.win_streak >= 3:
            print(f"      -> {colored(f'{your_data.win_streak}-fight win streak broken!', Colors.ORANGE)}")
        
        print()
        
        # === FIGHT DETAILS ===
        print_divider()
        print(f"  {colored('FIGHT DETAILS', Colors.CYAN)}")
        print()
        print(f"    Event: {offer.event_name}")
        print(f"    When: {offer.weeks_away} weeks away")
        print(f"    Purse: {colored(format_money(offer.purse), Colors.WIN)}")
        if offer.is_title_fight:
            print(f"    Rounds: 5 (championship)")
        elif offer.is_main_event:
            print(f"    Rounds: 5 (main event)")
        else:
            print(f"    Rounds: 3")
        print()
        
        # === OPTIONS ===
        print_divider()
        options = [
            ("1", colored("Accept Fight", Colors.WIN)),
            ("2", "View Full Scouting Report"),
            ("0", "Back to Offers"),
        ]
        print_menu(options)
        
        choice = get_choice(["1", "2", "0"])
        
        if choice == "1":
            self.accept_fight_offer(offer)
        elif choice == "2":
            if opp_data:
                self._show_full_scouting_report(opp_data)
            self.view_fight_offer(offer)  # Return to this screen


    def _show_basic_offer_display(self, your_data, opp_data, offer) -> None:
        """Basic offer display when tale of tape not available."""
        if your_data:
            print(f"  YOUR FIGHTER:")
            print(f"  {colored(your_data.name, Colors.CYAN)}")
            print(f"  Record: {format_record_colored(your_data.wins, your_data.losses)}")
            print(f"  Rating: {your_data.overall_rating}")
            print()
        
        print(f"  VS")
        print()
        
        if opp_data:
            champ_tag = colored(" CHAMPION", Colors.GOLD) if opp_data.is_champion else ""
            print(f"  OPPONENT:{champ_tag}")
            print(f"  {colored(opp_data.name, Colors.RED)}")
            print(f"  Record: {format_record_colored(opp_data.wins, opp_data.losses)}")
            print(f"  Rating: {opp_data.overall_rating}")
            print(f"  Style: {opp_data.fighting_style}")
        print()
    
    def _show_full_scouting_report(self, fighter_data) -> None:
        """Display full scouting report for a fighter with personality and camp info."""
        if not SCOUTING_AVAILABLE or not fighter_data:
            print("Scouting not available.")
            pause()
            return
        
        clear_screen()
        print_header(f"SCOUTING REPORT: {fighter_data.name}")
        
        # Show camp and coaching info
        if fighter_data.camp_id:
            camp = self.game_state.camps.get(fighter_data.camp_id)
            if camp:
                print()
                print(f"  {colored('CAMP', Colors.CYAN)}: {camp.name}")
                
                # Show coaches
                coaches = self._get_camp_coaches_display(fighter_data.camp_id)
                if coaches:
                    head_coach = next((c for c in coaches if c.get("is_head")), coaches[0] if coaches else None)
                    if head_coach:
                        stars = "*" * head_coach["stars"] + "-" * (5 - head_coach["stars"])
                        print(f"  Head Coach: {head_coach['name']} [{stars}] ({head_coach['specialty']})")
                    
                    coach_bonus = self._get_camp_coach_bonus(fighter_data.camp_id)
                    bonus_pct = int((coach_bonus - 1) * 100)
                    if bonus_pct != 0:
                        color = Colors.GREEN if bonus_pct > 0 else Colors.RED
                        print(f"  Training Bonus: {colored(f'{bonus_pct:+d}%', color)}")
                print()
        
        # Show personality section if available
        personality_info = self._get_personality_display(fighter_data.fighter_id)
        if personality_info:
            print()
            print(f"  {colored('FIGHTER PROFILE', Colors.GOLD)}")
            print()
            if "mentality" in personality_info:
                print(f"    Mentality: {colored(personality_info['mentality'], Colors.HIGHLIGHT)}")
                print(f"               {colored(personality_info.get('mentality_desc', ''), Colors.DIM)}")
            if "risk" in personality_info:
                risk = personality_info['risk']
                risk_color = Colors.GREEN if risk in ['Aggressive', 'Reckless'] else Colors.YELLOW if risk == 'Balanced' else Colors.RED
                print(f"    Risk Profile: {colored(risk, risk_color)} - {personality_info.get('risk_desc', '')}")
            if "activity" in personality_info:
                print(f"    Activity: {personality_info['activity']}")
            extras = []
            if "confidence" in personality_info:
                extras.append(personality_info['confidence'])
            if "ego" in personality_info:
                extras.append(personality_info['ego'])
            if extras:
                print(f"    Traits: {', '.join(extras)}")
            print()
            
            # Fight acceptance hints
            print(f"  {colored('FIGHT TENDENCIES', Colors.CYAN)}")
            mentality = personality_info.get('mentality', '')
            if mentality == 'Warrior':
                print(f"    {colored('+', Colors.GREEN)} Takes any fight, anytime")
                print(f"    {colored('+', Colors.GREEN)} Never ducks opponents")
            elif mentality == 'Glory Seeker':
                print(f"    {colored('+', Colors.GREEN)} Eager for title fights & main events")
                print(f"    {colored('-', Colors.RED)} May decline undercard spots")
            elif mentality == 'Journeyman':
                print(f"    {colored('+', Colors.GREEN)} Stays active, consistent")
                print(f"    {colored('+', Colors.GREEN)} Reliable opponent")
            elif mentality == 'Killer':
                print(f"    {colored('+', Colors.GREEN)} Aggressive, seeks finishes")
                print(f"    {colored('+', Colors.GREEN)} Won't back down")
            elif mentality == 'Technician':
                print(f"    {colored('-', Colors.RED)} Very selective about opponents")
                print(f"    {colored('+', Colors.GREEN)} Takes favorable matchups")
            elif mentality == 'Businessman':
                print(f"    {colored('~', Colors.YELLOW)} Calculates risk vs reward")
                print(f"    {colored('-', Colors.RED)} May avoid high-risk fights")
            
            risk = personality_info.get('risk', '')
            if risk in ['Reckless', 'Aggressive']:
                print(f"    {colored('+', Colors.GREEN)} Will fight up in rankings")
            elif risk in ['Cautious', 'Gun-shy']:
                print(f"    {colored('-', Colors.RED)} Prefers safer matchups")
            
            print()
            print_divider()
        
        try:
            report = scout_fighter(fighter_data, is_prospect=(fighter_data.age <= 24))
            
            print(f"  Age: {report.age} | Style: {report.fighting_style}")
            print(f"  Record: {report.record[0]}-{report.record[1]}-{report.record[2]}")
            print(f"  Overall: {report.overall_rating}")
            print()
            
            print_divider()
            print("  CATEGORY SCORES")
            print(f"    Striking:  {self._score_bar(report.striking_score)}")
            print(f"    Grappling: {self._score_bar(report.grappling_score)}")
            print(f"    Physical:  {self._score_bar(report.physical_score)}")
            print(f"    Mental:    {self._score_bar(report.mental_score)}")
            print()
            
            print_divider()
            print(colored("  STRENGTHS", Colors.GREEN))
            for s in report.strengths:
                print(f"    + {s.attribute}: {s.value} - {s.description}")
            print()
            
            print(colored("  WEAKNESSES", Colors.RED))
            for w in report.weaknesses:
                print(f"    - {w.attribute}: {w.value} - {w.description}")
            print()
            
            if report.traits:
                print_divider()
                print("  TRAITS")
                for trait in report.traits:
                    print(f"    * {trait}")
                if report.trait_analysis:
                    print()
                    for analysis in report.trait_analysis[:3]:
                        print(f"      -> {analysis}")
            print()
            
            if report.potential:
                print_divider()
                print(colored("  POTENTIAL ASSESSMENT", Colors.CYAN))
                print(f"    Grade: {report.potential.grade}")
                print(f"    Current: {report.potential.current_overall}")
                print(f"    Ceiling: {report.potential.ceiling}")
                print(f"    Upside: +{report.potential.upside} points")
                print()
            
            if report.ideal_matchups or report.bad_matchups:
                print_divider()
                print("  MATCHUP RECOMMENDATIONS")
                if report.ideal_matchups:
                    print(f"    Good vs: {', '.join(report.ideal_matchups)}")
                if report.bad_matchups:
                    print(f"    Avoid: {', '.join(report.bad_matchups)}")
            print()
            
        except Exception as e:
            print(f"  Error generating report: {e}")
        
        pause()
    
    def _score_bar(self, score: int) -> str:
        """Create a visual score bar."""
        filled = score // 5
        empty = 20 - filled
        bar = "#" * filled + "." * empty
        if score >= 80:
            color = Colors.GREEN
        elif score >= 60:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        return f"{colored(bar, color)} {score}"


    def accept_fight_offer(self, offer: FightOffer) -> None:
        """Accept a fight offer with full fight preparation flow."""
        
        # Get fighter data
        your_data = self.fighter_data.get(offer.fighter_id)
        opp_data = self.fighter_data.get(offer.opponent_id)
        if not opp_data:
            opp_data = self._create_full_fighter_data(offer.opponent_id)
        
        # === FIGHT PREPARATION SCREEN ===
        clear_screen()
        print_header("FIGHT PREPARATION")
        
        # Fighter comparison header
        your_name = offer.fighter_name
        opp_name = offer.opponent_name
        your_rating = your_data.overall_rating if your_data else 50
        opp_rating = opp_data.overall_rating if opp_data else 50
        opp_style = getattr(opp_data, 'fighting_style', 'Unknown') if opp_data else 'Unknown'
        
        print(f"  {colored('YOUR FIGHTER:', Colors.CYAN)} {your_name} ({your_rating} OVR)")
        print(f"  {colored('OPPONENT:', Colors.RED)} {opp_name} ({opp_rating} OVR) - {opp_style}")
        print()
        print_divider()
        
        # Build stats dicts for module functions
        fighter_stats = {}
        opp_stats = {}
        
        if your_data:
            fighter_stats = {
                "boxing": your_data.boxing,
                "kicks": your_data.kicks,
                "wrestling": your_data.wrestling,
                "bjj": your_data.bjj,
                "power": getattr(your_data, 'power', 50),
                "cardio": your_data.cardio,
                "chin": your_data.chin,
                "strength": getattr(your_data, 'strength', 50),
                "speed": getattr(your_data, 'speed', 50),
            }
        
        if opp_data:
            opp_stats = {
                "boxing": opp_data.boxing,
                "kicks": opp_data.kicks,
                "wrestling": opp_data.wrestling,
                "bjj": opp_data.bjj,
                "power": getattr(opp_data, 'power', 50),
                "cardio": opp_data.cardio,
                "chin": opp_data.chin,
                "strength": getattr(opp_data, 'strength', 50),
                "speed": getattr(opp_data, 'speed', 50),
            }
        
        # === MATCHUP ANALYSIS (from module) ===
        if GAMEPLAN_AVAILABLE and fighter_stats and opp_stats:
            analysis = get_matchup_analysis(fighter_stats, opp_stats)
            
            print()
            print(f"  {colored('MATCHUP ANALYSIS', Colors.YELLOW)}")
            print()
            
            # Two column comparison
            print(f"  {colored('YOUR EDGES', Colors.GREEN):30} {colored('THEIR EDGES', Colors.RED)}")
            max_edges = max(len(analysis.your_edges), len(analysis.their_edges))
            for i in range(max(max_edges, 1)):
                your_edge = analysis.your_edges[i] if i < len(analysis.your_edges) else ""
                their_edge = analysis.their_edges[i] if i < len(analysis.their_edges) else ""
                your_prefix = "+ " if your_edge else "  "
                their_prefix = "+ " if their_edge else "  "
                print(f"  {your_prefix}{your_edge:28} {their_prefix}{their_edge}")
            
            if not analysis.your_edges and not analysis.their_edges:
                print(f"  {'Evenly matched across the board':30}")
            
            print()
            print(f"  {colored('SUGGESTED:', Colors.CYAN)} {analysis.suggested_approach}")
            for warning in analysis.danger_warnings:
                print(f"  {colored('DANGER:', Colors.RED)} {warning}")
        
        print()
        print_divider()
        
        # === GAMEPLAN SELECTION (from module) ===
        print()
        print(f"  {colored('SELECT GAMEPLAN', Colors.CYAN)}")
        print()
        
        gameplan = None
        if GAMEPLAN_AVAILABLE and fighter_stats:
            # Get options from module
            gameplan_options = get_gameplan_options(fighter_stats, opp_stats if opp_stats else None)
            
            # Display options
            for opt in gameplan_options:
                rec_tag = colored(" [RECOMMENDED]", Colors.GREEN) if opt.is_recommended else ""
                warn_tag = colored(f" ({opt.warning})", Colors.YELLOW) if opt.warning else ""
                print(f"  [{opt.key}] {opt.name} - {opt.description}{rec_tag}{warn_tag}")
                print(f"      {colored(opt.modifiers_text, Colors.DIM)}")
            
            print()
            print(f"  [C] Custom - Build your own gameplan")
            print(f"  [0] Cancel - Don't accept fight")
            print()
            
            choice = get_input("Select gameplan: ").upper().strip()
            
            if choice == "0":
                return
            elif choice == "C":
                helper = GameplanMenuHelper()
                gameplan = self._custom_gameplan_selection(helper)
            else:
                for opt in gameplan_options:
                    if opt.key == choice:
                        gameplan = opt.gameplan
                        break
                if not gameplan and gameplan_options:
                    gameplan = gameplan_options[0].gameplan  # Default to first
            
            print()
            if gameplan:
                print(f"  Gameplan: {colored(format_gameplan_compact(gameplan), Colors.CYAN)}")
        
        print()
        print(colored("Fight accepted!", Colors.WIN))
        print()
        
        # Create fight record
        fight = {
            "fighter1_id": offer.fighter_id,
            "fighter2_id": offer.opponent_id,
            "fighter1_name": offer.fighter_name,
            "fighter2_name": offer.opponent_name,
            "weight_class": offer.weight_class,
            "is_title_fight": offer.is_title_fight,
            "is_main_event": offer.is_main_event,
            "rounds": 5 if offer.is_title_fight or offer.is_main_event else 3,
            "purse": offer.purse,
            "weeks_until": offer.weeks_away,
            "event_name": offer.event_name,
        }
        
        if gameplan:
            fight["gameplan"] = gameplan.to_dict() if hasattr(gameplan, 'to_dict') else None
        
        self.player_scheduled_fights.append(fight)
        self.fight_offers.remove(offer)
        
        self.news_feed.insert(0, NewsItem(
            headline=f"FIGHT ANNOUNCED: {offer.fighter_name} vs {offer.opponent_name}",
            category="fight",
            week=self.game_state.week_number,
        ))
        
        print(f"{offer.fighter_name} vs {offer.opponent_name}")
        print(f"Scheduled in {offer.weeks_away} weeks")
        print()
        
        # === TRAINING CAMP SETUP ===
        if confirm("Start training camp for this fight?"):
            fighter_data = self.fighter_data.get(offer.fighter_id)
            if fighter_data:
                self._enhanced_training_camp_setup(fighter_data, offer.weeks_away, opp_data, gameplan)
        
        pause()


    def _enhanced_training_camp_setup(
        self, 
        fighter: FighterFullData, 
        weeks_until_fight: int,
        opponent_data: Optional[FighterFullData] = None,
        gameplan: Optional[Any] = None
    ) -> None:
        """Enhanced training camp setup with focus, intensity, and coach selection."""
        
        if not self._training_system:
            print("Training started (simplified).")
            return
        
        clear_screen()
        print_header("TRAINING CAMP SETUP")
        
        camp_duration = max(4, min(weeks_until_fight - 1, 8))
        player_camp = self.game_state.get_player_camp()
        camp_id = player_camp.camp_id if player_camp else "player"
        camp_tier = self._get_camp_tier()
        
        print(f"  Fighter: {colored(fighter.name, Colors.HIGHLIGHT)}")
        print(f"  Camp Duration: {camp_duration} weeks")
        print(f"  Facility: {camp_tier}")
        if opponent_data:
            print(f"  Opponent: {opponent_data.name} ({opponent_data.overall_rating} OVR)")
        print()
        print_divider()
        
        # Build stats for module functions
        fighter_stats = {
            "boxing": fighter.boxing,
            "kicks": fighter.kicks,
            "wrestling": fighter.wrestling,
            "bjj": fighter.bjj,
            "cardio": fighter.cardio,
        }
        
        opp_stats = None
        if opponent_data:
            opp_stats = {
                "boxing": opponent_data.boxing,
                "kicks": opponent_data.kicks,
                "wrestling": opponent_data.wrestling,
                "bjj": opponent_data.bjj,
            }
        
        # === COACH SELECTION ===
        print()
        print(f"  {colored('SELECT COACH', Colors.CYAN)}")
        print()
        
        selected_coach = None
        coach_specialty = None
        coach_quality = 0
        
        if COACHES_AVAILABLE and self._coach_system:
            try:
                coaches = self._coach_system.get_camp_coaches(camp_id)
                if coaches:
                    for i, coach in enumerate(coaches[:5], 1):
                        stars = "*" * (coach.quality // 20) + "-" * (5 - coach.quality // 20)
                        specialty = coach.specialty.value if hasattr(coach.specialty, 'value') else str(coach.specialty)
                        bonus_pct = coach.quality // 10
                        
                        print(f"  [{i}] {coach.name}")
                        print(f"      {specialty} Specialist | [{stars}] | +{bonus_pct}% training bonus")
                    
                    print(f"  [0] Train solo (no coach bonus)")
                    print()
                    
                    coach_choice = get_input("Select coach: ").strip()
                    try:
                        coach_idx = int(coach_choice)
                        if 1 <= coach_idx <= len(coaches[:5]):
                            selected_coach = coaches[coach_idx - 1]
                            coach_specialty = selected_coach.specialty.value if hasattr(selected_coach.specialty, 'value') else str(selected_coach.specialty)
                            coach_quality = selected_coach.quality
                    except (ValueError, IndexError):
                        pass
                else:
                    print("  No coaches available. Training solo.")
            except Exception:
                print("  No coaches available. Training solo.")
        else:
            print("  No coaches available. Training solo.")
        
        if selected_coach:
            print(f"  {colored('[OK]', Colors.GREEN)} {selected_coach.name} assigned (+{coach_quality // 10}% bonus)")
        else:
            print(f"  Training solo (no bonus)")
        
        print()
        print_divider()
        
        # === GET RECOMMENDATION FROM MODULE ===
        try:
            from systems.training import (
                TrainingFocus, TrainingIntensity,
                get_training_focus_options, get_intensity_options,
                recommend_training_focus, estimate_camp_gains_detailed,
            )
            
            gameplan_focus = getattr(gameplan, 'focus', None) if gameplan else None
            recommended_focus, recommendation_reason = recommend_training_focus(
                fighter_stats, opp_stats, gameplan_focus
            )
            
            # === TRAINING FOCUS SELECTION (from module) ===
            print()
            print(f"  {colored('SELECT TRAINING FOCUS', Colors.CYAN)}")
            print()
            
            focus_options = get_training_focus_options(
                coach_specialty=coach_specialty,
                recommended_focus=recommended_focus,
                recommendation_reason=recommendation_reason,
            )
            
            for opt in focus_options:
                coach_match = ""
                if coach_specialty and opt.matching_specialties:
                    if opt.coach_matches:
                        coach_match = colored(" [+25% COACH MATCH]", Colors.GREEN)
                    else:
                        coach_match = colored(" [no coach match]", Colors.DIM)
                
                rec_tag = colored(" <- RECOMMENDED", Colors.YELLOW) if opt.is_recommended else ""
                
                print(f"  [{opt.key}] {opt.name} - {opt.description}{coach_match}{rec_tag}")
            
            print()
            if recommendation_reason:
                print(f"  {colored('Why recommended:', Colors.DIM)} {recommendation_reason}")
                print()
            
            focus_choice = get_input("Select focus: ").strip()
            if not focus_choice or focus_choice not in ["1", "2", "3", "4", "5", "6"]:
                focus_choice = next((o.key for o in focus_options if o.is_recommended), "4")
            
            selected_focus = next((o.focus for o in focus_options if o.key == focus_choice), TrainingFocus.BALANCED)
            selected_focus_name = next((o.name for o in focus_options if o.key == focus_choice), "Balanced")
            
            # Check specialty match
            specialty_matches = False
            for opt in focus_options:
                if opt.key == focus_choice:
                    specialty_matches = opt.coach_matches
                    break
            
            print()
            print_divider()
            
            # === INTENSITY SELECTION (from module) ===
            print()
            print(f"  {colored('SELECT TRAINING INTENSITY', Colors.CYAN)}")
            print()
            
            intensity_options = get_intensity_options()
            
            color_map = {
                "Light": Colors.GREEN,
                "Moderate": Colors.YELLOW,
                "Intense": Colors.ORANGE,
                "Extreme": Colors.RED,
            }
            
            for opt in intensity_options:
                color = color_map.get(opt.name, Colors.WHITE)
                default_tag = " [DEFAULT]" if opt.is_default else ""
                print(f"  [{opt.key}] {colored(opt.name, color)} - {opt.gains_percent}% gains, {opt.injury_risk_percent}% injury risk{default_tag}")
                print(f"      {colored(opt.description, Colors.DIM)}")
            
            print()
            
            intensity_choice = get_input("Select intensity: ").strip()
            if not intensity_choice or intensity_choice not in ["1", "2", "3", "4"]:
                intensity_choice = "2"
            
            selected_intensity = next((o.intensity for o in intensity_options if o.key == intensity_choice), TrainingIntensity.MODERATE)
            selected_intensity_name = next((o.name for o in intensity_options if o.key == intensity_choice), "Moderate")
            
            print()
            print_divider()
            
            # === ESTIMATED GAINS (from module) ===
            print()
            print(f"  {colored('CAMP SUMMARY', Colors.CYAN)}")
            print()
            
            age = getattr(fighter, 'age', 28)
            estimate = estimate_camp_gains_detailed(
                weeks=camp_duration,
                focus=selected_focus,
                intensity=selected_intensity,
                coach_quality=coach_quality,
                coach_specialty_matches=specialty_matches,
                age=age,
                camp_tier=camp_tier,
            )
            
            print(f"  Duration: {camp_duration} weeks")
            print(f"  Focus: {selected_focus_name}")
            print(f"  Intensity: {selected_intensity_name}")
            print(f"  Coach: {selected_coach.name if selected_coach else 'None'}")
            if specialty_matches:
                print(f"  {colored('Coach specialty matches focus! +25% bonus', Colors.GREEN)}")
            print(f"  Age: {age} ({estimate.age_note})")
            print()
            print(f"  {colored(f'ESTIMATED GAINS: +{estimate.estimated_min_gains}-{estimate.estimated_max_gains} attribute points', Colors.HIGHLIGHT)}")
            if estimate.injury_risk_per_week > 0:
                risk_color = Colors.YELLOW if estimate.injury_risk_per_week <= 3 else Colors.RED
                print(f"  {colored(f'Injury Risk: {estimate.injury_risk_per_week}% per week', risk_color)}")
            print()
            
            if not confirm("Start this training camp?"):
                print("Training camp cancelled.")
                return
            
            # === START CAMP ===
            self._training_system.start_camp(
                fighter_id=fighter.fighter_id,
                camp_id=camp_id,
                focus=selected_focus,
                intensity=selected_intensity,
                weeks=camp_duration,
            )
            
            print()
            print(colored(f"  {camp_duration}-WEEK TRAINING CAMP STARTED!", Colors.WIN))
            print()
            print(f"  Focus: {selected_focus.value}")
            print(f"  Intensity: {selected_intensity.name.title()}")
            if selected_coach:
                print(f"  Coach: {selected_coach.name}")
            print()
            
        except ImportError:
            print(f"Training camp started ({camp_duration} weeks).")


    def _custom_gameplan_selection(self, helper) -> 'Gameplan':
        """Custom gameplan builder."""
        clear_screen()
        print_header("CUSTOM GAMEPLAN")
        
        print("  STANCE:")
        for key, desc in helper.get_stance_menu():
            print(f"    [{key}] {desc}")
        stance_choice = get_input("  Select: ").strip()
        
        print()
        print("  FOCUS:")
        for key, desc in helper.get_focus_menu():
            print(f"    [{key}] {desc}")
        focus_choice = get_input("  Select: ").strip()
        
        print()
        print("  PRIORITY:")
        for key, desc in helper.get_priority_menu():
            print(f"    [{key}] {desc}")
        priority_choice = get_input("  Select: ").strip()
        
        print()
        print("  SPECIAL TACTICS (enter numbers separated by comma, or skip):")
        for key, desc in helper.get_tactics_menu():
            print(f"    [{key}] {desc}")
        tactics_input = get_input("  Select: ").strip()
        
        tactic_choices = []
        if tactics_input:
            tactic_choices = [t.strip() for t in tactics_input.split(",")]
        
        return helper.build_gameplan_from_choices(
            stance_choice, focus_choice, priority_choice, tactic_choices
        )


    def start_training_camp_for_fight(self, fighter: FighterFullData, weeks_until_fight: int) -> None:
        """Start training camp with coach selection and opponent analysis."""
        if not self._training_system:
            print("Training started (simplified).")
            return
        
        camp_duration = max(4, min(weeks_until_fight - 1, 8))
        player_camp = self.game_state.get_player_camp()
        camp_id = player_camp.camp_id if player_camp else "player"
        
        # === COACH SELECTION ===
        selected_coach = None
        coach_bonus = 1.0
        
        if COACHES_AVAILABLE and self._coach_system:
            try:
                coaches = self._coach_system.get_camp_coaches(camp_id)
                if coaches:
                    print()
                    print(colored("  SELECT COACH FOR THIS CAMP", Colors.CYAN))
                    print()
                    
                    for i, coach in enumerate(coaches[:5], 1):
                        # Star rating
                        stars = "*" * (coach.quality // 20) + "-" * (5 - coach.quality // 20)
                        specialty = coach.specialty.value if hasattr(coach.specialty, 'value') else str(coach.specialty)
                        bonus_pct = int(coach.quality / 10)
                        
                        print(f"    [{i}] {coach.name}")
                        print(f"        {specialty} Specialist | {stars} | +{bonus_pct}% bonus")
                    
                    print(f"    [0] No coach (train solo)")
                    print()
                    
                    coach_choice = get_input("Select coach: ")
                    try:
                        coach_idx = int(coach_choice)
                        if 1 <= coach_idx <= len(coaches[:5]):
                            selected_coach = coaches[coach_idx - 1]
                            coach_bonus = 1.0 + (selected_coach.quality / 100)
                            bonus_pct = int((coach_bonus - 1) * 100)
                            print(f"    {colored('[OK]', Colors.GREEN)} {selected_coach.name} assigned (+{bonus_pct}% training)")
                    except (ValueError, IndexError):
                        pass
                    print()
            except:
                pass
        
        # === OPPONENT ANALYSIS & RECOMMENDATION ===
        recommended_focus = None
        recommendation_reason = ""
        
        if SCOUTING_AVAILABLE:
            for fight in self.player_scheduled_fights:
                if fight.get("fighter1_id") == fighter.fighter_id:
                    opp_id = fight.get("fighter2_id")
                    opp_data = self.fighter_data.get(opp_id)
                    if not opp_data:
                        opp_data = self._create_full_fighter_data(opp_id)
                    
                    if opp_data:
                        try:
                            analysis = get_matchup_analysis(fighter, opp_data)
                            opp_name = fight.get("fighter2_name", "opponent")
                            
                            print(colored(f"  OPPONENT ANALYSIS: {opp_name}", Colors.YELLOW))
                            print()
                            
                            # Analyze their strengths to counter
                            if analysis.fighter2_advantages:
                                print(f"    Their advantages: {', '.join(analysis.fighter2_advantages[:2])}")
                                
                                # Determine recommendation based on their strengths
                                adv_text = " ".join(analysis.fighter2_advantages).lower()
                                if "grappling" in adv_text or "wrestling" in adv_text or "bjj" in adv_text:
                                    recommended_focus = "3"  # Wrestling
                                    recommendation_reason = "Shore up grappling defense"
                                elif "striking" in adv_text or "boxing" in adv_text or "kicks" in adv_text:
                                    recommended_focus = "1"  # Striking
                                    recommendation_reason = "Match their striking"
                            
                            # Or capitalize on your advantages
                            if analysis.fighter1_advantages:
                                print(f"    Your advantages: {', '.join(analysis.fighter1_advantages[:2])}")
                                
                                if not recommended_focus:
                                    adv_text = " ".join(analysis.fighter1_advantages).lower()
                                    if "grappling" in adv_text or "wrestling" in adv_text:
                                        recommended_focus = "3"
                                        recommendation_reason = "Press your grappling advantage"
                                    elif "striking" in adv_text:
                                        recommended_focus = "1"
                                        recommendation_reason = "Sharpen your striking edge"
                            
                            # Default to conditioning if no clear direction
                            if not recommended_focus:
                                recommended_focus = "4"
                                recommendation_reason = "Well-matched, focus on conditioning"
                            
                            print()
                        except:
                            pass
                    break
        
        # === TRAINING FOCUS SELECTION ===
        print(colored("  SELECT TRAINING FOCUS", Colors.CYAN))
        print()
        
        focuses = [
            ("1", "Striking", "Boxing, kicks, striking defense"),
            ("2", "Jiu-Jitsu", "BJJ, submissions, ground control"),
            ("3", "Wrestling", "Takedowns, takedown defense"),
            ("4", "Conditioning", "Cardio, recovery, stamina"),
            ("5", "Strength & Power", "Strength, speed, power"),
            ("6", "Balanced", "All attributes (smaller gains)"),
        ]
        
        for key, name, desc in focuses:
            rec_tag = ""
            if key == recommended_focus:
                rec_tag = colored(f" <- RECOMMENDED ({recommendation_reason})", Colors.GREEN)
            print(f"    [{key}] {name} - {desc}{rec_tag}")
        print()
        
        choice = get_choice(["1", "2", "3", "4", "5", "6"])
        if not choice:
            choice = recommended_focus or "6"
        
        try:
            from systems.training import TrainingFocus, TrainingIntensity
            
            focus_map = {
                "1": TrainingFocus.STRIKING,
                "2": TrainingFocus.JIUJITSU,
                "3": TrainingFocus.WRESTLING,
                "4": TrainingFocus.CONDITIONING,
                "5": TrainingFocus.STRENGTH_POWER,
                "6": TrainingFocus.BALANCED,
            }
            
            focus = focus_map.get(choice, TrainingFocus.BALANCED)
            
            self._training_system.start_camp(
                fighter_id=fighter.fighter_id,
                camp_id=camp_id,
                focus=focus,
                intensity=TrainingIntensity.MODERATE,
                weeks=camp_duration,
            )
            
            print()
            print(colored(f"  [OK] {camp_duration}-WEEK CAMP STARTED!", Colors.WIN))
            print(f"    Focus: {focus.value}")
            if selected_coach:
                print(f"    Coach: {selected_coach.name} (+{int((coach_bonus-1)*100)}% bonus)")
            else:
                print(f"    Coach: Training solo")
        except ImportError:
            print(f"Training camp started ({camp_duration} weeks).")


    def find_opponents_for_fighter(self, fighter: FighterFullData) -> None:
        """Find and request fights"""
        clear_screen()
        print_header(f"FIND OPPONENT FOR {fighter.name.upper()}")
        
        # Get basic record for opponent search
        basic = self.game_state.fighters.get(fighter.fighter_id)
        if not basic:
            print("Fighter not found.")
            pause()
            return
        
        opponents = self._find_opponents_for_fighter_basic(basic)
        
        if not opponents:
            print("No suitable opponents found.")
            pause()
            return
        
        print(f"Potential opponents ({fighter.weight_class}):")
        print()
        
        for i, opp in enumerate(opponents, 1):
            opp_data = self._create_full_fighter_data(opp.fighter_id)
            quality = self._get_matchup_quality(fighter.overall_rating, opp.overall_rating)
            champ_tag = colored(" ", Colors.GOLD) if opp.is_champion else ""
            
            print(f"  [{i}] {opp.name}{champ_tag}")
            print(f"      Record: {format_record_colored(opp.wins, opp.losses)} | Rating: {opp.overall_rating}")
            if opp_data:
                print(f"      Style: {opp_data.fighting_style}")
            print(f"      Matchup: {quality}")
            print()
        
        print(f"  [0] Back")
        print()
        
        choice = get_input("Request fight: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(opponents):
                self.request_fight(fighter, opponents[index - 1])
        except ValueError:
            pass
    
    def request_fight(self, fighter: FighterFullData, opponent) -> None:
        """Request a specific fight"""
        tier = self._get_camp_tier()
        min_weeks = MIN_WEEKS_BY_TIER.get(tier, 4)
        max_weeks = MAX_WEEKS_BY_TIER.get(tier, 8)
        
        is_title = fighter.is_champion or opponent.is_champion
        weeks_away = random.randint(min_weeks, max_weeks)
        if is_title:
            weeks_away = max(weeks_away, 8)
        
        purse = 5000 + (fighter.overall_rating + opponent.overall_rating) * 50
        if is_title:
            purse *= 3
        
        print()
        print("Fight request submitted...")
        
        # AI acceptance (70% base, higher for bigger fights)
        accept_chance = 0.70
        if is_title:
            accept_chance = 0.85
        
        if random.random() < accept_chance:
            print(colored("ACCEPTED!", Colors.WIN))
            
            offer = FightOffer(
                offer_id=f"requested_{len(self.fight_offers)}",
                fighter_id=fighter.fighter_id,
                fighter_name=fighter.name,
                opponent_id=opponent.fighter_id,
                opponent_name=opponent.name,
                opponent_record=format_record(opponent.wins, opponent.losses),
                opponent_rating=opponent.overall_rating,
                weight_class=fighter.weight_class,
                event_name="DFC Fight Night",
                event_date="TBD",
                weeks_away=weeks_away,
                purse=purse,
                is_title_fight=is_title,
            )
            
            self.accept_fight_offer(offer)
        else:
            print(colored("DECLINED", Colors.LOSS))
            print("The opponent's camp rejected the offer.")
            pause()
    
    # -------------------------------------------------------------------------
    # Week Advancement with Fight Results
    # -------------------------------------------------------------------------
    
    def advance_week(self) -> None:
        """Advance the game week with full event processing"""
        clear_screen()
        print_header("ADVANCING WEEK")
        
        game = self.game_state
        old_week = game.week_number
        
        print(f"Current: Week {old_week}")
        print()
        
        # Check for player fights this week
        fights_this_week = [f for f in self.player_scheduled_fights if f.get("weeks_until", 0) <= 1]
        
        # Check for AI fights this week
        ai_fights_this_week = [f for f in self.ai_scheduled_fights if f.get("weeks_until", 0) <= 1]
        
        if fights_this_week:
            print(colored("! YOUR FIGHTER(S) HAVE FIGHTS THIS WEEK!", Colors.ORANGE))
            print()
            for fight in fights_this_week:
                print(f"  * {fight.get('fighter1_name')} vs {fight.get('fighter2_name')}")
            print()
            
            if not confirm("Proceed to fight night?"):
                return
        
        print("Processing week...")
        print()
        
        week_events = []
        
        # Process training
        training_results = self._process_training_week()
        week_events.extend(training_results)
        
        # Process player's scheduled fights
        # Store fight results for display
        self._week_fight_results = []
        fight_results = self._process_weekly_fights()
        week_events.extend(fight_results)
        
        # Process AI fights
        ai_results = self._process_ai_fights()
        
        # Process weekly finances
        if hasattr(self, '_process_weekly_finances'):
            finance_events = self._process_weekly_finances()
            week_events.extend(finance_events)

        week_events.extend(ai_results)
        
        # Process Fight of the Night (after all fights completed)
        current_week = game.week_number  # Capture before advancing
        fotn_events = self._process_fotn(current_week)
        week_events.extend(fotn_events)
        
        # Process weekly injury healing
        healing_events = self._process_weekly_healing()
        week_events.extend(healing_events)
        
        # Process aging (check for retirements annually)
        aging_events = self._process_weekly_aging()
        week_events.extend(aging_events)
        
        # Decrement weeks on remaining player fights
        for fight in self.player_scheduled_fights:
            if "weeks_until" in fight:
                fight["weeks_until"] = max(0, fight["weeks_until"] - 1)
        
        # Decrement fighter cooldowns
        expired_cooldowns = []
        for fighter_id, weeks in self._fighter_cooldowns.items():
            self._fighter_cooldowns[fighter_id] = max(0, weeks - 1)
            if self._fighter_cooldowns[fighter_id] == 0:
                expired_cooldowns.append(fighter_id)
        for fighter_id in expired_cooldowns:
            del self._fighter_cooldowns[fighter_id]
        
        # Advance game state
        game.advance_week()
        
        # Generate new player offers periodically
        if game.week_number % 2 == 0:
            self._generate_fight_offers()
        
        # Ensure AI events are scheduled
        self._ensure_ai_events_scheduled()
        
        print(f"Advanced to: Week {game.week_number}")
        print()
        
        self._show_week_summary(week_events)
        
        autosave(game)
        self._save_extended_data("autosave")
        print(colored("(Autosaved)", Colors.DIM))
        
        # Handle pending financial situations
        if hasattr(self, '_pending_emergency_loan') and self._pending_emergency_loan:
            self._show_emergency_loan_offer()
        
        if hasattr(self, '_pending_cost_cutting') and self._pending_cost_cutting:
            self._show_cost_cutting_required()
        
        if hasattr(self, '_pending_bankruptcy') and self._pending_bankruptcy:
            self._show_bankruptcy_screen()
            return  # Exit week advancement
        
        pause()
    
    def _process_training_week(self) -> List[str]:
        """Process training for player's fighters with detailed progress display"""
        events = []
        
        if not self._training_system:
            return events
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return events
        
        # Helper to format attribute names nicely
        def format_attr_name(attr: str) -> str:
            name_map = {
                "boxing": "Boxing",
                "kicks": "Kicks",
                "wrestling": "Wrestling",
                "bjj": "BJJ",
                "cardio": "Cardio",
                "strength": "Strength",
                "speed": "Speed",
                "power": "Power",
                "chin": "Chin",
                "recovery": "Recovery",
                "td_defense": "TD Defense",
                "top_control": "Top Control",
                "submissions": "Submissions",
                "clinch": "Clinch",
                "accuracy": "Accuracy",
                "head_movement": "Head Movement",
                "footwork": "Footwork",
                "fight_iq": "Fight IQ",
                "composure": "Composure",
            }
            return name_map.get(attr, attr.replace("_", " ").title())
        
        # Helper to format gains dict as string
        def format_gains(gains_dict: dict) -> str:
            if not gains_dict:
                return "No gains"
            parts = []
            for attr, val in sorted(gains_dict.items(), key=lambda x: -x[1]):
                if val > 0:
                    parts.append(f"{format_attr_name(attr)} +{val}")
            return ", ".join(parts) if parts else "No gains"
        
        training_fighters = []
        
        for fighter_id, full_data in self.fighter_data.items():
            if full_data.camp_id != player_camp.camp_id:
                continue
            
            camp = self._training_system.get_camp(fighter_id)
            if camp and not camp.is_complete:
                # Process week
                current_attrs = {
                    "boxing": full_data.boxing,
                    "kicks": full_data.kicks,
                    "wrestling": full_data.wrestling,
                    "bjj": full_data.bjj,
                    "cardio": full_data.cardio,
                    "strength": getattr(full_data, 'strength', 50),
                    "speed": getattr(full_data, 'speed', 50),
                    "power": getattr(full_data, 'power', 50),
                    "td_defense": getattr(full_data, 'td_defense', 50),
                    "top_control": getattr(full_data, 'top_control', 50),
                    "submissions": getattr(full_data, 'submissions', 50),
                    "clinch": getattr(full_data, 'clinch', 50),
                }
                
                # Get coach bonus for this camp
                coach_bonus = self._get_camp_coach_bonus(player_camp.camp_id)
                coach_quality = int(coach_bonus * 3)  # Convert multiplier to quality (1-5)
                
                try:
                    result = self._training_system.process_training_week(
                        fighter_id=fighter_id,
                        current_attributes=current_attrs,
                        age=full_data.age,
                        camp_tier=None,
                        coach_quality=coach_quality,
                        fatigue=0,
                    )
                    
                    # Unpack tuple (gains, event) or just gains if old format
                    if isinstance(result, tuple):
                        gains, training_event = result
                    else:
                        gains = result
                        training_event = None
                    
                    # Apply coach multiplier to gains
                    if gains and coach_bonus != 1.0:
                        gains = {k: max(1, int(v * coach_bonus)) for k, v in gains.items()}
                    
                    if gains:
                        # Apply trait-based training multiplier
                        multiplier = get_training_multiplier(full_data.traits)
                        trait_note = ""
                        if multiplier != 1.0:
                            gains = {k: int(v * multiplier) for k, v in gains.items()}
                            if has_trait(full_data.traits, "Gym Rat"):
                                trait_note = colored(" [Gym Rat]", Colors.GREEN)
                        
                        # Track overall before applying gains
                        old_overall = full_data.overall_rating
                        
                        # Get camp tier for facility caps
                        camp_tier = self._get_camp_tier()
                        capped_attrs = []
                        
                        # Apply gains to fighter (with facility cap enforcement)
                        for attr, gain in gains.items():
                            if hasattr(full_data, attr):
                                old_val = getattr(full_data, attr)
                                
                                # Apply facility cap if available
                                if FACILITIES_AVAILABLE and camp_tier:
                                    new_val, actual_gain, was_capped = apply_facility_cap(
                                        old_val, gain, camp_tier, attr
                                    )
                                    if was_capped and actual_gain < gain:
                                        capped_attrs.append(attr)
                                    setattr(full_data, attr, new_val)
                                else:
                                    setattr(full_data, attr, min(100, old_val + gain))
                        
                        # Check if overall increased
                        new_overall = full_data.overall_rating
                        overall_increased = new_overall > old_overall
                        
                        # Record gains in camp for cumulative tracking
                        for attr, gain in gains.items():
                            if gain > 0:
                                camp.record_gain(attr, gain)
                        
                        # Build detailed display
                        week_num = camp.weeks_completed
                        total_weeks = camp.total_weeks
                        focus_name = camp.focus.value
                        
                        # Get coach bonus info
                        coach_note = ""
                        if coach_bonus > 1.0:
                            coach_note = colored(f" [+{int((coach_bonus-1)*100)}% coach]", Colors.CYAN)
                        
                        # Format gains for news
                        gains_parts = []
                        for attr, val in sorted(gains.items(), key=lambda x: -x[1]):
                            if val > 0:
                                gains_parts.append(f"{format_attr_name(attr)} +{val}")
                        gains_str = ", ".join(gains_parts) if gains_parts else ""
                        
                        # Add training gains to news feed
                        if gains_str:
                            news_headline = f"{full_data.name}: {gains_str}"
                            if overall_increased:
                                news_headline += f" (OVR {old_overall} -> {new_overall})"
                            self.news_feed.insert(0, NewsItem(
                                headline=news_headline,
                                category="training",
                                week=self.game_state.week_number if self.game_state else 0,
                            ))
                        
                        training_fighters.append({
                            'name': full_data.name,
                            'week': week_num,
                            'total_weeks': total_weeks,
                            'focus': focus_name,
                            'weekly_gains': gains,
                            'camp_total': camp.attribute_gains.copy(),
                            'trait_note': trait_note,
                            'coach_note': coach_note,
                            'is_complete': camp.is_complete,
                            'training_event': training_event,  # Breakthroughs, setbacks, etc.
                            'old_overall': old_overall,
                            'new_overall': new_overall,
                            'overall_increased': overall_increased,
                        })
                    
                except Exception:
                    pass
        
        # Format output
        if training_fighters:
            events.append(colored("TRAINING PROGRESS", Colors.CYAN))
            
            for tf in training_fighters:
                # Fighter header line
                header = f"  {tf['name']} (Week {tf['week']}/{tf['total_weeks']} | Focus: {tf['focus']}){tf['trait_note']}"
                events.append(header)
                
                # Training event (breakthrough, setback, etc.)
                training_event = tf.get('training_event')
                if training_event:
                    event_type = getattr(training_event, 'event_type', None)
                    headline = getattr(training_event, 'headline', '')
                    
                    # Color based on event type
                    if event_type and 'breakthrough' in str(event_type).lower():
                        events.append(f"    {colored("* BREAKTHROUGH: " + headline, Colors.GOLD)}")
                        # Add to news feed
                        self.news_feed.insert(0, NewsItem(
                            headline=f"{tf['name']} has training breakthrough!",
                            category="training",
                            week=self.game_state.week_number if self.game_state else 0,
                        ))
                    elif event_type and 'setback' in str(event_type).lower():
                        events.append(f"    {colored('! SETBACK: ' + headline, Colors.RED)}")
                    elif event_type and 'injury' in str(event_type).lower():
                        events.append(f"    {colored('+ INJURY: ' + headline, Colors.RED)}")
                    elif headline:
                        events.append(f"    {colored('> ' + headline, Colors.YELLOW)}")
                
                # This week's gains
                weekly_str = format_gains(tf['weekly_gains'])
                events.append(f"    This week: {colored(weekly_str, Colors.GREEN)}")
                
                # Overall increase notification
                if tf.get('overall_increased'):
                    old_ovr = tf.get('old_overall', 0)
                    new_ovr = tf.get('new_overall', 0)
                    events.append(f"    {colored(f' OVERALL: {old_ovr}  {new_ovr}', Colors.GOLD)}")
                
                # Camp total (only show if more than one week in)
                if tf['week'] > 1 and tf['camp_total']:
                    total_str = format_gains(tf['camp_total'])
                    events.append(f"    Camp total: {total_str}")
                
                # Camp complete notification
                if tf['is_complete']:
                    events.append(colored(f"     Camp complete! Ready to fight.", Colors.GOLD))
                
                events.append("")  # Blank line between fighters
        
        return events
    
    def _process_weekly_finances(self) -> List[str]:
        """Process weekly financial operations and check financial pressure."""
        events = []
        
        if not self._economy_manager or not ECONOMY_AVAILABLE:
            return events
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return events
        
        # Get camp data
        tier = self._get_camp_tier()
        fighters = [f for f in self.game_state.fighters.values() 
                   if f.camp_id == player_camp.camp_id]
        roster_size = len(fighters)
        fighter_ids = [f.fighter_id for f in fighters]
        
        # Get actual coach data
        coach_count = 0
        coach_salaries = 0
        coach_ids = []
        if COACHES_AVAILABLE and self._coach_system:
            try:
                coach_count = self._coach_system.get_coach_count(player_camp.camp_id)
                coach_salaries = self._coach_system.get_total_weekly_salary(player_camp.camp_id)
                coaches = self._coach_system.get_camp_coaches(player_camp.camp_id)
                coach_ids = [c.coach_id for c in coaches] if coaches else []
            except:
                coach_count = 1
                coach_salaries = 2000
        else:
            coach_count = 1
            coach_salaries = 2000
        
        # Process finances
        summary = self._economy_manager.process_weekly_finances(
            camp_id=player_camp.camp_id,
            tier=tier,
            roster_size=roster_size,
            coach_count=coach_count,
            coach_salaries=coach_salaries,
            week=self.game_state.week_number,
            date=f"Week {self.game_state.week_number}",
        )
        
        # Sync balance back to camp object
        player_camp._balance = summary.closing_balance
        
        # Add income/expense events
        if summary.total_income > 0:
            events.append(f"  [$] Weekly income: +{format_money(summary.total_income)}")
        if summary.total_expenses > 0:
            events.append(f"  [$] Weekly expenses: -{format_money(summary.total_expenses)}")
        
        # Add loan payment event
        if summary.loan_payments > 0:
            events.append(f"  [B] Loan payment: -{format_money(summary.loan_payments)}")
        
        # Check financial pressure
        pressure = self._economy_manager.check_financial_pressure(
            camp_id=player_camp.camp_id,
            tier=tier,
            fighter_ids=fighter_ids,
            coach_ids=coach_ids,
        )
        
        # Handle pressure situations
        pressure_events = self._handle_financial_pressure(pressure, player_camp, tier)
        events.extend(pressure_events)
        
        # Add standard warnings (but not debt warnings which we handle specially)
        for warning in summary.warnings:
            if "debt" not in warning.lower() and "bankruptcy" not in warning.lower():
                events.append(f"  [!] {warning}")
        
        return events
    
    def _handle_financial_pressure(
        self, 
        pressure, 
        player_camp, 
        tier: str
    ) -> List[str]:
        """Handle financial pressure situations."""
        events = []
        
        if not ECONOMY_AVAILABLE:
            return events
        
        # Import stage enum if available
        try:
            from systems.economy import FinancialPressureStage
        except ImportError:
            try:
                from economy import FinancialPressureStage
            except ImportError:
                return events
        
        if pressure.stage == FinancialPressureStage.HEALTHY:
            return events
        
        # WARNING stage
        if pressure.stage == FinancialPressureStage.WARNING:
            events.append(f"  {colored(' FINANCIAL WARNING', Colors.YELLOW)}: In debt for {pressure.weeks_in_debt} week(s)")
            return events
        
        # EMERGENCY_LOAN stage
        if pressure.stage == FinancialPressureStage.EMERGENCY_LOAN:
            events.append(f"  {colored(' EMERGENCY LOAN OFFERED', Colors.ORANGE)}")
            self._pending_emergency_loan = {
                "amount": pressure.emergency_loan_amount,
                "interest": pressure.emergency_loan_interest,
                "weeks": pressure.weeks_in_debt,
            }
            return events
        
        # COST_CUTTING stage
        if pressure.stage == FinancialPressureStage.COST_CUTTING:
            events.append(f"  {colored(' FINANCIAL CRISIS', Colors.RED)}: Cost cutting required!")
            self._pending_cost_cutting = {
                "pressure": pressure,
                "tier": tier,
            }
            return events
        
        # DOWNGRADE stage
        if pressure.stage == FinancialPressureStage.DOWNGRADE:
            events.append(f"  {colored(' FACILITY DOWNGRADE', Colors.RED)}: {pressure.current_tier}  {pressure.downgrade_tier}")
            self._process_forced_downgrade(player_camp, pressure.current_tier, pressure.downgrade_tier)
            self.news_feed.insert(0, NewsItem(
                headline=f" {player_camp.name} forced to downgrade facility amid financial crisis",
                category="alert",
                week=self.game_state.week_number,
            ))
            return events
        
        # BANKRUPTCY
        if pressure.stage == FinancialPressureStage.BANKRUPTCY:
            events.append(f"  {colored(' DYNASTY COLLAPSE', Colors.RED)}")
            self._pending_bankruptcy = True
            return events
        
        return events
    
    def _process_forced_downgrade(self, player_camp, from_tier: str, to_tier: str) -> None:
        """Process a forced facility downgrade."""
        tier_map = {"GARAGE": "garage", "LOCAL": "local", "REGIONAL": "regional", "NATIONAL": "national", "ELITE": "elite"}
        player_camp._tier = tier_map.get(to_tier, "garage")
        if self._economy_manager:
            self._economy_manager.process_forced_downgrade(player_camp.camp_id, from_tier, to_tier)
    
    def _show_emergency_loan_offer(self) -> None:
        """Show emergency loan offer after week summary."""
        if not hasattr(self, '_pending_emergency_loan') or not self._pending_emergency_loan:
            return
        offer = self._pending_emergency_loan
        self._pending_emergency_loan = None
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        print()
        print(f"  {colored('=' * 60, Colors.ORANGE)}")
        print(f"  {colored(' EMERGENCY LOAN AVAILABLE', Colors.ORANGE)}")
        print(f"  {colored('=' * 60, Colors.ORANGE)}")
        print()
        print(f"  Your camp has been in debt for {offer['weeks']} weeks.")
        print(f"  A lender is offering an emergency loan:")
        print()
        print(f"    Amount:   {colored(format_money(offer['amount']), Colors.GREEN)}")
        interest_pct = offer['interest']*100
        print(f"    Interest: {colored(f'{interest_pct:.0f}% per month', Colors.YELLOW)} (higher than normal)")
        print()
        if confirm("  Accept emergency loan?"):
            tier = self._get_camp_tier()
            success, message, loan = self._economy_manager.take_emergency_loan(
                player_camp.camp_id, offer['amount'], tier, self.game_state.week_number)
            if success:
                player_camp._balance = self._economy_manager.get_balance(player_camp.camp_id)
                print(f"\n  {colored('[OK]', Colors.GREEN)} {message}")
                print(f"  New Balance: {format_money(player_camp.balance)}")
                self.news_feed.insert(0, NewsItem(
                    headline=f" {player_camp.name} takes emergency loan to stay afloat",
                    category="business", week=self.game_state.week_number))
            else:
                print(f"\n  {colored('[!]', Colors.RED)} {message}")
        else:
            print(f"\n  {colored('Loan declined.', Colors.DIM)} Situation may worsen next week.")
    
    def _show_cost_cutting_required(self) -> None:
        """Force player to cut costs."""
        if not hasattr(self, '_pending_cost_cutting') or not self._pending_cost_cutting:
            return
        data = self._pending_cost_cutting
        self._pending_cost_cutting = None
        pressure = data['pressure']
        tier = data['tier']
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        print()
        print(f"  {colored('=' * 60, Colors.RED)}")
        print(f"  {colored(' FINANCIAL CRISIS - ACTION REQUIRED', Colors.RED)}")
        print(f"  {colored('=' * 60, Colors.RED)}")
        print()
        print(f"  Your camp has been in debt for {pressure.weeks_in_debt} weeks!")
        print(f"  You must take action to reduce costs or face facility downgrade.")
        print()
        options = []
        option_num = 1
        overhead = FIGHTER_OVERHEAD_BY_TIER.get(tier.upper(), 100) if ECONOMY_AVAILABLE else 100
        if pressure.emergency_loan_available:
            options.append(("loan", f"Take emergency loan"))
            print(f"  [{option_num}] Take emergency loan ({format_money(pressure.emergency_loan_amount)} @ 8% interest)")
            option_num += 1
        if pressure.must_release_fighter and pressure.releasable_fighters:
            options.append(("release", "Release a fighter"))
            print(f"  [{option_num}] Release a fighter (save ${overhead}/week)")
            option_num += 1
        if pressure.must_fire_coach and pressure.fireable_coaches:
            options.append(("fire", "Fire a coach"))
            print(f"  [{option_num}] Fire a coach")
            option_num += 1
        print()
        valid_choices = [str(i+1) for i in range(len(options))] if options else ["1"]
        choice = get_choice(valid_choices)
        if not choice:
            choice = "1"
        idx = int(choice) - 1
        action = options[idx][0] if idx < len(options) else "loan"
        if action == "loan":
            success, message, loan = self._economy_manager.take_emergency_loan(
                player_camp.camp_id, pressure.emergency_loan_amount, tier, self.game_state.week_number)
            if success:
                player_camp._balance = self._economy_manager.get_balance(player_camp.camp_id)
                print(f"\n  {colored('[OK]', Colors.GREEN)} Emergency loan received!")
                print(f"  New Balance: {format_money(player_camp.balance)}")
                self.news_feed.insert(0, NewsItem(
                    headline=f" {player_camp.name} takes emergency loan amid financial crisis",
                    category="business", week=self.game_state.week_number))
        elif action == "release":
            self._force_release_fighter(player_camp, pressure.releasable_fighters)
        elif action == "fire":
            self._force_fire_coach(player_camp, pressure.fireable_coaches)
    
    def _force_release_fighter(self, player_camp, fighter_ids: List[str]) -> None:
        """Force player to release a fighter."""
        print()
        print(f"  {colored('SELECT FIGHTER TO RELEASE', Colors.YELLOW)}")
        print()
        fighters = [self.fighter_data[f_id] for f_id in fighter_ids if f_id in self.fighter_data]
        if not fighters:
            print("  No fighters available to release!")
            return
        for i, f in enumerate(fighters, 1):
            rank_str = f"#{f.rank}" if hasattr(f, 'rank') and f.rank else "Unranked"
            print(f"  [{i}] {f.name} ({rank_str}, {f.wins}-{f.losses})")
        print()
        choice = get_choice([str(i+1) for i in range(len(fighters))])
        if not choice:
            choice = "1"
        idx = int(choice) - 1
        fighter = fighters[idx] if idx < len(fighters) else fighters[0]
        fighter.camp_id = None
        if fighter.fighter_id in self.game_state.fighters:
            self.game_state.fighters[fighter.fighter_id].camp_id = None
        print(f"\n  {colored('[OK]', Colors.GREEN)} {fighter.name} has been released.")
        self.news_feed.insert(0, NewsItem(
            headline=f" {player_camp.name} releases {fighter.name} in cost-cutting move",
            category="business", week=self.game_state.week_number))
    
    def _force_fire_coach(self, player_camp, coach_ids: List[str]) -> None:
        """Force player to fire a coach."""
        if not COACHES_AVAILABLE or not self._coach_system:
            print("  No coaches available to fire!")
            return
        print()
        print(f"  {colored('SELECT COACH TO FIRE', Colors.YELLOW)}")
        print()
        coaches = self._coach_system.get_camp_coaches(player_camp.camp_id)
        fireable = [c for c in coaches if c.coach_id in coach_ids]
        if not fireable:
            print("  No coaches available to fire!")
            return
        for i, c in enumerate(fireable, 1):
            specialty = c.specialty if hasattr(c, 'specialty') else "General"
            salary = c.salary if hasattr(c, 'salary') else 2000
            print(f"  [{i}] {c.name} ({specialty}) - {format_money(salary)}/month")
        print()
        choice = get_choice([str(i+1) for i in range(len(fireable))])
        if not choice:
            choice = "1"
        idx = int(choice) - 1
        coach = fireable[idx] if idx < len(fireable) else fireable[0]
        try:
            self._coach_system.fire_coach(player_camp.camp_id, coach.coach_id)
            print(f"\n  {colored('[OK]', Colors.GREEN)} {coach.name} has been let go.")
            self.news_feed.insert(0, NewsItem(
                headline=f" {player_camp.name} parts ways with coach {coach.name}",
                category="business", week=self.game_state.week_number))
        except Exception as e:
            print(f"\n  {colored('[!]', Colors.RED)} Could not fire coach: {e}")
    
    def _show_bankruptcy_screen(self) -> None:
        """Show game over screen for bankruptcy."""
        if not hasattr(self, '_pending_bankruptcy') or not self._pending_bankruptcy:
            return
        self._pending_bankruptcy = None
        player_camp = self.game_state.get_player_camp()
        clear_screen()
        print()
        print(f"  {colored('=' * 60, Colors.RED)}")
        camp_name = player_camp.name if player_camp else "Your camp"
        print(f"  {colored(' DYNASTY COLLAPSE ', Colors.RED):^70}")
        print(f"  {colored('=' * 60, Colors.RED)}")
        print()
        print(f"  {camp_name} has fallen.")
        print()
        print("  After weeks of mounting debt, creditors have seized your assets.")
        print("  Your fighters have scattered to other camps.")
        print("  Your coaches have found employment elsewhere.")
        print()
        print("  Your journey in the fight game has come to an end.")
        print()
        print(f"  {colored('=' * 60, Colors.RED)}")
        print()
        options = [("1", "Start New Game"), ("2", "Load Saved Game"), ("0", "Return to Main Menu")]
        print_menu(options)
        choice = get_choice(["1", "2", "0"])
        if choice == "1":
            self._start_new_game()
        elif choice == "2":
            self.load_menu()


    def _process_weekly_fights(self) -> List[str]:
        """Process fights happening this week"""
        events = []
        completed = []
        fight_results_to_show = []  # Store results for commentary viewing
        
        for i, fight in enumerate(self.player_scheduled_fights):
            if fight.get("weeks_until", 0) <= 1:
                result = self._execute_fight(fight)
                if result:
                    events.append(result["summary"])
                    completed.append(i)
                    # Store fight result for commentary viewing
                    if "fight_result" in result:
                        fight_results_to_show.append(result["fight_result"])
        
        # Remove completed fights
        for i in sorted(completed, reverse=True):
            self.player_scheduled_fights.pop(i)
        
        # Show each fight result with commentary option
        for fight_result in fight_results_to_show:
            self._show_player_fight_result(fight_result)
        
        return events
    
    def _show_player_fight_result(self, result: FightResult) -> None:
        """Show player fight result with option to view full commentary."""
        clear_screen()
        print_header("FIGHT RESULT")
        
        # Show basic result
        print(f"  {result.fighter1_name} vs {result.fighter2_name}")
        print()
        
        if result.method == "DRAW":
            print(f"  Result: {colored('DRAW', Colors.NEUTRAL)}")
        else:
            print(f"  Winner: {colored(result.winner_name, Colors.WIN)}")
            
            method_upper = result.method.upper()
            if "KO" in method_upper or "TKO" in method_upper:
                print(f"  Method: {colored(result.method, Colors.RED)} (Round {result.round_finished})")
            elif "SUB" in method_upper:
                print(f"  Method: {colored('Submission', Colors.MAGENTA)} (Round {result.round_finished})")
            else:
                decision_info = f" ({result.decision_type})" if result.decision_type else ""
                print(f"  Method: Decision{decision_info}")
                
                # Show judge scores
                if result.judge_scores:
                    print()
                    print(f"  {colored('SCORECARDS:', Colors.CYAN)}")
                    if hasattr(result, 'judge_names') and result.judge_names:
                        for name, (s1, s2) in zip(result.judge_names, result.judge_scores):
                            print(f"    {name}: {s1}-{s2}")
                    else:
                        for s1, s2 in result.judge_scores:
                            print(f"    {s1}-{s2}")
        
        print()
        
        # Show fight summary
        if result.fight_summary:
            print(f"  {result.fight_summary}")
            print()
        
        # Show key moments
        if result.key_moments:
            print(f"  {colored('KEY MOMENTS:', Colors.CYAN)}")
            for moment in result.key_moments[:3]:
                print(f"    * {moment}")
            print()
        
        # Stats summary
        print(f"  {colored('STATS:', Colors.BOLD)}")
        print(f"    {result.fighter1_name}: {result.fighter1_strikes} strikes, {result.fighter1_takedowns} TD")
        print(f"    {result.fighter2_name}: {result.fighter2_strikes} strikes, {result.fighter2_takedowns} TD")
        print()
        
        # Option to view full commentary
        if result.has_full_commentary and result.full_commentary:
            print(f"  [{colored('C', Colors.CYAN)}] View Full Fight Commentary")
            print(f"  [Enter] Continue")
            print()
            choice = get_input("> ").lower()
            if choice == 'c':
                self._show_full_fight_commentary(result)
        else:
            pause()
    
    def _execute_fight(self, fight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a fight and store results.
        
        Uses full narrated fight engine when available, falls back to simple simulation.
        """
        import uuid
        
        f1_id = fight.get("fighter1_id")
        f2_id = fight.get("fighter2_id")
        f1_name = fight.get("fighter1_name", "Fighter 1")
        f2_name = fight.get("fighter2_name", "Fighter 2")
        is_title = fight.get("is_title_fight", False)
        rounds = fight.get("rounds", 3)
        event_name = fight.get("event_name", "DFC Fight Night")
        is_main = fight.get("is_main_event", False)
        
        # Ensure fighter data exists
        if f1_id not in self.fighter_data:
            self._create_full_fighter_data(f1_id)
        if f2_id not in self.fighter_data:
            self._create_full_fighter_data(f2_id)
        
        # Try narrated simulation first
        sim_result = self._narrated_fight_simulation(
            f1_id, f2_id, rounds,
            is_title_fight=is_title,
            is_main_event=is_main
        )
        
        # Fall back to simple simulation if needed
        if sim_result is None:
            f1_data = self.fighter_data.get(f1_id)
            f2_data = self.fighter_data.get(f2_id)
            f1_rating = f1_data.overall_rating if f1_data else 50
            f2_rating = f2_data.overall_rating if f2_data else 50
            
            sim_result = self._simple_fight_simulation(
                f1_id, f2_id, f1_name, f2_name, f1_rating, f2_rating, rounds,
                is_title_fight=is_title,
                is_main_event=is_main
            )
        
        winner_id = sim_result["winner_id"]
        loser_id = sim_result["loser_id"]
        method = sim_result["method"]
        finish_round = sim_result["round"]
        winner_name = sim_result["winner_name"]
        loser_name = sim_result["loser_name"]
        
        # Create fight result with enhanced data
        fight_id = f"fight_{uuid.uuid4().hex[:8]}"
        result = FightResult(
            fight_id=fight_id,
            event_id=f"event_{self.game_state.week_number}",
            event_name=event_name,
            week=self.game_state.week_number,
            fighter1_id=f1_id,
            fighter1_name=f1_name,
            fighter2_id=f2_id,
            fighter2_name=f2_name,
            winner_id=winner_id,
            winner_name=winner_name,
            loser_id=loser_id,
            loser_name=loser_name,
            method=method,
            round_finished=finish_round,
            time_finished=sim_result.get("time", "5:00"),
            weight_class=fight.get("weight_class", ""),
            is_title_fight=is_title,
            is_main_event=is_main,
            rounds_scheduled=rounds,
            fighter1_strikes=sim_result.get("fighter1_strikes", 0),
            fighter2_strikes=sim_result.get("fighter2_strikes", 0),
            fighter1_takedowns=sim_result.get("fighter1_takedowns", 0),
            fighter2_takedowns=sim_result.get("fighter2_takedowns", 0),
            fighter1_sub_attempts=sim_result.get("fighter1_sub_attempts", 0),
            fighter2_sub_attempts=sim_result.get("fighter2_sub_attempts", 0),
        )
        
        # Process ranking changes FIRST
        ranking_changes = self._process_ranking_changes(
            winner_id=winner_id,
            winner_name=winner_name,
            loser_id=loser_id,
            loser_name=loser_name,
            weight_class=fight.get("weight_class", ""),
            method=method,
            was_title_fight=is_title,
        )
        
        # Store ranking changes on result for display
        result.ranking_changes = ranking_changes
        
        # Store for week summary display (after ranking changes calculated)
        if hasattr(self, '_week_fight_results'):
            self._week_fight_results.append({
                "winner_name": winner_name,
                "loser_name": loser_name,
                "winner_id": winner_id,
                "loser_id": loser_id,
                "method": method,
                "round": finish_round,
                "is_title_fight": is_title,
                "is_main_event": is_main,
                "weight_class": fight.get("weight_class", ""),
                "event_name": event_name,
                "ranking_changes": ranking_changes,
                "is_controversial": getattr(result, 'is_controversial', False),
                "controversy_reason": getattr(result, 'controversy_reason', ''),
                "judge_names": getattr(result, 'judge_names', []),
            })
        
        # Store in fight history for matchmaking
        if hasattr(self, 'fight_history'):
            self.fight_history.append(result)
            # Keep only last 100 fights
            if len(self.fight_history) > 100:
                self.fight_history = self.fight_history[-100:]
        
        # Add enhanced commentary if available from narrated simulation
        if "full_commentary" in sim_result:
            result.full_commentary = sim_result.get("full_commentary", "")
            result.fight_narrative = sim_result.get("fight_narrative", "")
            result.round_summaries = sim_result.get("round_summaries", [])
            result.key_moments = sim_result.get("key_moments", [])
            result.fighter1_round_stats = sim_result.get("fighter1_round_stats", [])
            result.fighter2_round_stats = sim_result.get("fighter2_round_stats", [])
            result.judge_scores = sim_result.get("judge_scores", [])
            result.decision_type = sim_result.get("decision_type", "")
            result.fight_of_night = sim_result.get("fight_of_night", False)
            result.performance_bonus = sim_result.get("performance_bonus", False)
            result.fighter1_final_health = sim_result.get("fighter1_final_health", 100.0)
            
            # Copy judge details
            result.judge_names = sim_result.get("judge_names", [])
            result.judge_scorecards = sim_result.get("judge_scorecards", [])
            result.is_controversial = sim_result.get("is_controversial", False)
            result.controversy_reason = sim_result.get("controversy_reason", "")
            result.decision_commentary = sim_result.get("decision_commentary", "")
            result.fighter2_final_health = sim_result.get("fighter2_final_health", 100.0)
            
            # Use narrative as summary if available
            if result.fight_narrative:
                result.fight_summary = result.fight_narrative
            else:
                # Generate summary from method
                if method == "KO":
                    result.fight_summary = f"{winner_name} knocked out {loser_name} in round {finish_round}."
                elif method == "TKO":
                    result.fight_summary = f"{winner_name} stopped {loser_name} by TKO in round {finish_round}."
                elif method == "SUB":
                    result.fight_summary = f"{winner_name} submitted {loser_name} in round {finish_round}."
                else:
                    result.fight_summary = f"{winner_name} outpointed {loser_name} over {rounds} rounds."
        else:
            # Generate basic fight summary (fallback)
            if method == "KO":
                result.fight_summary = f"{winner_name} knocked out {loser_name} with a devastating strike in round {finish_round}."
                result.key_moments = [f"Round {finish_round}: {winner_name} lands the knockout blow"]
            elif method == "TKO":
                result.fight_summary = f"{winner_name} stopped {loser_name} by TKO in round {finish_round}. The referee waved off the fight."
                result.key_moments = [f"Round {finish_round}: Referee stoppage"]
            elif method == "SUB":
                subs = ["rear naked choke", "guillotine", "armbar", "triangle", "kimura"]
                sub_type = random.choice(subs)
                result.fight_summary = f"{winner_name} submitted {loser_name} with a {sub_type} in round {finish_round}."
                result.key_moments = [f"Round {finish_round}: {winner_name} locks in the {sub_type}"]
            else:
                result.fight_summary = f"{winner_name} outpointed {loser_name} over {rounds} rounds to earn a decision victory."
                result.key_moments = ["Close fight goes to the scorecards"]
        
        # Store result
        self.all_fight_results[fight_id] = result
        
        # Update fighter records
        if winner_id in self.fighter_data:
            self.fighter_data[winner_id].wins += 1
            self.fighter_data[winner_id].win_streak += 1
            self.fighter_data[winner_id].lose_streak = 0
            if method == "KO" or method == "TKO":
                self.fighter_data[winner_id].ko_wins += 1
            elif method == "SUB":
                self.fighter_data[winner_id].sub_wins += 1
            self._sync_fighter_record(winner_id)
            # Clear cooldown on win
            if winner_id in self._fighter_cooldowns:
                del self._fighter_cooldowns[winner_id]
        
        if loser_id in self.fighter_data:
            self.fighter_data[loser_id].losses += 1
            self.fighter_data[loser_id].lose_streak += 1
            self.fighter_data[loser_id].win_streak = 0
            if method == "KO" or method == "TKO":
                self.fighter_data[loser_id].ko_losses += 1
            elif method == "SUB":
                self.fighter_data[loser_id].sub_losses += 1
            self._sync_fighter_record(loser_id)
            # Apply cooldown: 4 weeks + 2 per additional loss in streak
            lose_streak = self.fighter_data[loser_id].lose_streak
            cooldown_weeks = 4 + (lose_streak - 1) * 2
            self._fighter_cooldowns[loser_id] = cooldown_weeks
        
        # Create/update event
        event_id = f"event_{self.game_state.week_number}"
        existing_event = next((e for e in self.completed_events if e.event_id == event_id), None)
        
        if existing_event:
            existing_event.add_fight(result)
        else:
            new_event = CompletedEvent(
                event_id=event_id,
                event_name=event_name,
                week=self.game_state.week_number,
            )
            new_event.add_fight(result)
            self.completed_events.append(new_event)
        
        # News
        if method == "DEC":
            headline = f"{winner_name} defeats {loser_name} by decision"
        else:
            headline = f"{winner_name} finishes {loser_name} by {method} (R{finish_round})"
        
        self.news_feed.insert(0, NewsItem(
            headline=headline,
            category="fight",
            week=self.game_state.week_number,
        ))
        
        # Process potential injuries
        injury_summaries = self._process_fight_injuries(
            f1_id, f2_id, winner_id, method, finish_round, rounds,
            f1_name, f2_name
        )
        
        # Process rivalry detection
        rivalry_event = self._process_fight_rivalry(
            f1_id, f2_id, f1_name, f2_name,
            winner_id, method, is_title, fight_id
        )
        
        # Return summary
        summary_str = f"  [FIGHT] {headline}"
        if is_title:
            summary_str = f"  [TITLE] {colored(headline, Colors.GOLD)}"
        
        # Add injury info to summary if any
        if injury_summaries:
            summary_str += "\n" + "\n".join(injury_summaries)
        
        # Add rivalry info if detected
        if rivalry_event:
            summary_str += f"\n    {rivalry_event}"
        
        return {"summary": summary_str, "result": result, "fight_result": result}
    
    def _process_fight_injuries(
        self,
        fighter1_id: str,
        fighter2_id: str,
        winner_id: str,
        method: str,
        finish_round: int,
        rounds_fought: int,
        fighter1_name: str,
        fighter2_name: str
    ) -> List[str]:
        """Process potential injuries after a fight.
        
        Returns list of injury summary strings.
        """
        summaries = []
        
        if not INJURY_AVAILABLE or not self._injury_system:
            return summaries
        
        try:
            # Map method to FightOutcome
            outcome_map = {
                "KO": FightOutcome.KO,
                "TKO": FightOutcome.TKO,
                "SUB": FightOutcome.SUBMISSION,
                "DEC": FightOutcome.DECISION,
                "SPLIT": FightOutcome.DECISION,
            }
            outcome = outcome_map.get(method, FightOutcome.DECISION)
            
            # Process injuries for both fighters
            f1_injury, f2_injury = self._injury_system.process_fight_injuries(
                fighter1_id, fighter2_id, outcome, winner_id, rounds_fought
            )
            
            if f1_injury:
                weeks = f1_injury.recovery_weeks
                summaries.append(
                    f"    {colored('INJURY:', Colors.RED)} {fighter1_name} - "
                    f"{f1_injury.description} ({weeks} weeks)"
                )
                self.news_feed.insert(0, NewsItem(
                    headline=f"{fighter1_name} injured: {f1_injury.description}",
                    category="injury",
                    week=self.game_state.week_number,
                ))
            
            if f2_injury:
                weeks = f2_injury.recovery_weeks
                summaries.append(
                    f"    {colored('INJURY:', Colors.RED)} {fighter2_name} - "
                    f"{f2_injury.description} ({weeks} weeks)"
                )
                self.news_feed.insert(0, NewsItem(
                    headline=f"{fighter2_name} injured: {f2_injury.description}",
                    category="injury",
                    week=self.game_state.week_number,
                ))
        except Exception as e:
            pass  # Silently handle injury processing errors
        
        return summaries
    
    def _process_fight_rivalry(
        self,
        fighter1_id: str,
        fighter2_id: str,
        fighter1_name: str,
        fighter2_name: str,
        winner_id: str,
        method: str,
        is_title_fight: bool,
        fight_id: str
    ) -> Optional[str]:
        """Process rivalry detection after a fight.
        
        Returns rivalry announcement string if rivalry detected/updated.
        """
        if not RIVALRY_AVAILABLE or not self._rivalry_system:
            return None
        
        try:
            # Get fighter data for context
            f1_data = self.fighter_data.get(fighter1_id)
            f2_data = self.fighter_data.get(fighter2_id)
            
            # Create fight context
            context = FightContext(
                fight_id=fight_id,
                fighter1_id=fighter1_id,
                fighter2_id=fighter2_id,
                fighter1_name=fighter1_name,
                fighter2_name=fighter2_name,
                winner_id=winner_id,
                method=method,
                is_title_fight=is_title_fight,
                fighter1_country=f1_data.country if f1_data else None,
                fighter2_country=f2_data.country if f2_data else None,
                fighter1_style=f1_data.fighting_style if f1_data else None,
                fighter2_style=f2_data.fighting_style if f2_data else None,
            )
            
            # Check for rivalry
            rivalry = self._rivalry_system.process_fight(context)
            
            if rivalry and rivalry.intensity.value >= 2:  # NOTABLE or higher
                intensity_desc = get_rivalry_intensity_description(rivalry.intensity)
                return colored(
                    f"Rivalry Update: {fighter1_name} vs {fighter2_name} ({intensity_desc})",
                    Colors.MAGENTA
                )
        except Exception:
            pass
        
        return None
    
    def _process_weekly_healing(self) -> List[str]:
        """Process weekly injury healing for all fighters.
        
        Returns list of recovery announcement strings.
        """
        events = []
        
        if not INJURY_AVAILABLE or not self._injury_system:
            return events
        
        try:
            healed = self._injury_system.process_weekly_healing()
            
            for fighter_id, descriptions in healed.items():
                fighter_name = "Fighter"
                if fighter_id in self.fighter_data:
                    fighter_name = self.fighter_data[fighter_id].name
                elif fighter_id in self.game_state.fighters:
                    fighter_name = self.game_state.fighters[fighter_id].name
                
                for desc in descriptions:
                    events.append(
                        f"  {colored('RECOVERED:', Colors.GREEN)} {fighter_name} - {desc}"
                    )
                    self.news_feed.insert(0, NewsItem(
                        headline=f"{fighter_name} cleared to fight",
                        category="injury",
                        week=self.game_state.week_number,
                    ))
        except Exception:
            pass
        
        return events
    
    def _process_weekly_aging(self) -> List[str]:
        """Process aging effects (annually) and retirement checks.
        
        Returns list of aging/retirement announcements.
        """
        events = []
        
        if not AGING_AVAILABLE or not self._aging_system:
            return events
        
        # Only process aging on week 1 of each year (approximately every 52 weeks)
        if self.game_state.week_number % 52 != 1:
            return events
        
        current_year = self.game_state.week_number // 52 + 1
        
        try:
            retirements = []
            
            for fighter_id, fighter in list(self.game_state.fighters.items()):
                if not fighter.is_active:
                    continue
                
                # Get full data if available
                full_data = self.fighter_data.get(fighter_id)
                age = full_data.age if full_data else 25
                ko_losses = full_data.ko_losses if full_data else 0
                lose_streak = full_data.lose_streak if full_data else 0
                total_fights = (full_data.wins + full_data.losses) if full_data else 0
                is_champion = full_data.is_champion if full_data else False
                
                # Increment age annually
                if full_data:
                    full_data.age += 1
                    age = full_data.age
                
                # Skip if already processed this year
                if not self._aging_system.should_process_annual_aging(fighter_id, current_year):
                    continue
                
                # Check for retirement
                if age >= 34:  # Only check retirement for older fighters
                    should_retire = self._aging_system.check_retirement(
                        fighter_id, age, lose_streak, is_champion, total_fights
                    )
                    
                    if should_retire:
                        retirements.append((fighter_id, fighter.name, age))
                        continue
                
                # Apply aging decline
                if age >= 33:  # Start decline at 33
                    phase, changes = self._aging_system.process_birthday(
                        fighter_id, age, ko_losses
                    )
                    
                    # Apply changes to fighter data
                    if full_data and changes:
                        for attr, change in changes.items():
                            if hasattr(full_data, attr):
                                current = getattr(full_data, attr)
                                setattr(full_data, attr, max(30, current + change))
                        
                        events.append(
                            f"  {colored('AGING:', Colors.YELLOW)} {fighter.name} "
                            f"({age}) showing signs of decline"
                        )
                
                self._aging_system.mark_annual_aging_processed(fighter_id, current_year)
            
            # Process retirements
            for fighter_id, name, age in retirements:
                self.game_state.fighters[fighter_id].is_active = False
                if fighter_id in self.fighter_data:
                    self.fighter_data[fighter_id].is_active = False
                
                events.append(
                    f"  {colored('RETIREMENT:', Colors.GOLD)} {name} ({age}) "
                    f"announces retirement"
                )
                self.news_feed.insert(0, NewsItem(
                    headline=f"{name} announces retirement at age {age}",
                    category="retirement",
                    week=self.game_state.week_number,
                ))
        except Exception:
            pass
        
        return events
    
    def _is_fighter_injured(self, fighter_id: str) -> bool:
        """Check if a fighter is currently injured."""
        if not INJURY_AVAILABLE or not self._injury_system:
            return False
        return self._injury_system.has_injuries(fighter_id)
    
    def _get_fighter_recovery_weeks(self, fighter_id: str) -> int:
        """Get weeks until fighter is recovered."""
        if not INJURY_AVAILABLE or not self._injury_system:
            return 0
        return self._injury_system.get_recovery_time(fighter_id)
    
    def _get_fighter_career_phase(self, fighter_id: str) -> str:
        """Get fighter's career phase as a string."""
        if not AGING_AVAILABLE:
            return ""
        
        full_data = self.fighter_data.get(fighter_id)
        if not full_data:
            return ""
        
        try:
            phase = get_career_phase(full_data.age)
            return phase.name.title()
        except Exception:
            return ""
    
    def _get_fighter_rivalries(self, fighter_id: str) -> List[Any]:
        """Get active rivalries for a fighter."""
        if not RIVALRY_AVAILABLE or not self._rivalry_system:
            return []
        return self._rivalry_system.get_active_rivalries(fighter_id)
    
    def _process_fotn(self, current_week: int) -> List[str]:
        """Process Fight of the Night selection for this week's fights.
        
        Returns list of event strings (FOTN announcement if selected).
        """
        events = []
        
        if not FOTN_AVAILABLE:
            return events
        
        # Get all fights from this week
        this_week_fights = [
            result for result in self.all_fight_results.values()
            if result.week == current_week
        ]
        
        if len(this_week_fights) < 2:
            return events  # Need at least 2 fights for FOTN
        
        # Convert FightResult objects to dict format for FOTN scoring
        fight_dicts = []
        for fight in this_week_fights:
            fight_dict = {
                "fighter1_id": fight.fighter1_id,
                "fighter2_id": fight.fighter2_id,
                "fighter1_name": fight.fighter1_name,
                "fighter2_name": fight.fighter2_name,
                "fighter1_stats": fight.fighter1_round_stats,
                "fighter2_stats": fight.fighter2_round_stats,
                "method": fight.method,
                "finish_round": fight.round_finished if fight.method != "DEC" else None,
                "is_title_fight": fight.is_title_fight,
                "winner_id": fight.winner_id,
                "loser_id": fight.loser_id,
                "fight_id": fight.fight_id,
            }
            fight_dicts.append(fight_dict)
        
        # Select FOTN
        fotn_fight, fotn_score = select_fotn(fight_dicts)
        
        if fotn_fight:
            # Mark the original FightResult as FOTN
            fight_id = fotn_fight.get("fight_id")
            if fight_id and fight_id in self.all_fight_results:
                self.all_fight_results[fight_id].fight_of_night = True
            
            f1_name = fotn_fight.get("fighter1_name", "Fighter 1")
            f2_name = fotn_fight.get("fighter2_name", "Fighter 2")
            f1_id = fotn_fight.get("fighter1_id")
            f2_id = fotn_fight.get("fighter2_id")
            
            # Award bonuses to both fighters
            if f1_id and f1_id in self.fighter_data:
                # Track FOTN awards
                if not hasattr(self.fighter_data[f1_id], 'fotn_awards'):
                    self.fighter_data[f1_id].fotn_awards = 0
                self.fighter_data[f1_id].fotn_awards += 1
                
                # Award money (if economy available)
                if ECONOMY_AVAILABLE and self._economy_manager:
                    try:
                        self._economy_manager.process_bonus(f1_id, FOTN_BONUS, "FOTN")
                    except:
                        pass
            
            if f2_id and f2_id in self.fighter_data:
                if not hasattr(self.fighter_data[f2_id], 'fotn_awards'):
                    self.fighter_data[f2_id].fotn_awards = 0
                self.fighter_data[f2_id].fotn_awards += 1
                
                if ECONOMY_AVAILABLE and self._economy_manager:
                    try:
                        self._economy_manager.process_bonus(f2_id, FOTN_BONUS, "FOTN")
                    except:
                        pass
            
            # Create announcement
            bonus_str = f"${FOTN_BONUS:,}"
            announcement = colored(
                f"  [!] FIGHT OF THE NIGHT: {f1_name} vs {f2_name} ({bonus_str} bonus each)",
                Colors.GOLD
            )
            events.append("")
            events.append(announcement)
            
            # Add to news feed
            self.news_feed.insert(0, NewsItem(
                headline=f"Fight of the Night: {f1_name} vs {f2_name}",
                category="award",
                week=current_week,
            ))
        
        return events
    
    def _show_week_summary(self, events: List[str]) -> None:
        """Show comprehensive week summary with fight cards."""
        print_divider()
        print()
        
        # Collect all week data
        week_results = self._week_fight_results if hasattr(self, '_week_fight_results') else []
        training_updates = []
        finance_updates = []
        other_events = []
        fotn_info = None
        
        # Parse events into categories
        for event in events:
            if not event:
                continue
            event_lower = event.lower()
            if "training" in event_lower or "camp" in event_lower or ("week" in event_lower and "/" in event):
                training_updates.append(event)
            elif "$" in event or "expense" in event_lower or "balance" in event_lower:
                finance_updates.append(event)
            elif "fight of the night" in event_lower:
                fotn_info = event
            else:
                other_events.append(event)
        
        # =====================================================================
        # HEADER
        # =====================================================================
        print(f"  {colored('=' * 64, Colors.CYAN)}")
        week_text = f"WEEK {self.game_state.week_number} RECAP"
        print(f"  {colored(week_text, Colors.HIGHLIGHT):^70}")
        print(f"  {colored('=' * 64, Colors.CYAN)}")
        print()
        
        # =====================================================================
        # FINANCES
        # =====================================================================
        if finance_updates:
            print(f"  {colored('[FINANCES]', Colors.WIN)}")
            for update in finance_updates:
                clean = self._clean_garbled_text(update)
                print(f"    {clean}")
            print()
        
        # =====================================================================
        # TRAINING PROGRESS
        # =====================================================================
        if training_updates:
            print(f"  {colored('[TRAINING CAMPS]', Colors.CYAN)}")
            for update in training_updates:
                clean = self._clean_garbled_text(update)
                if clean:
                    print(f"    {clean}")
            print()
        
        # =====================================================================
        # FIGHT CARD RESULTS
        # =====================================================================
        if week_results:
            events_map = {}
            for result in week_results:
                event_name = result.get("event_name", "DFC Fight Night")
                if event_name not in events_map:
                    events_map[event_name] = []
                events_map[event_name].append(result)
            
            for event_name, fights in events_map.items():
                total_fights = len(fights)
                finishes = sum(1 for f in fights if f.get("method", "").upper() not in ["DECISION", "DEC", "UNANIMOUS DECISION", "SPLIT DECISION"])
                
                # Get weight classes involved
                weight_classes = set()
                for f in fights:
                    wc = f.get("weight_class", "")
                    if wc:
                        weight_classes.add(self._get_division_abbrev(wc))
                divisions_str = ", ".join(sorted(weight_classes)) if weight_classes else ""
                
                print(f"  {colored('=' * 64, Colors.ORANGE)}")
                print(f"  {colored(event_name.upper(), Colors.ORANGE)} ({total_fights} fights, {finishes} finishes)")
                if divisions_str:
                    print(f"  Divisions: {divisions_str}")
                print(f"  {colored('=' * 64, Colors.ORANGE)}")
                print()
                
                # Sort: Title > Main > Co-Main > Card Position
                sorted_fights = sorted(fights, key=lambda f: (
                    -int(f.get("is_title_fight", False)),
                    -int(f.get("is_main_event", False)),
                    -int(f.get("is_co_main", False)),
                    -f.get("card_position", 0)
                ))
                
                # Group into Main Card and Prelims
                main_card = []
                prelims = []
                for i, fight in enumerate(sorted_fights):
                    if fight.get("is_title_fight") or fight.get("is_main_event") or fight.get("is_co_main") or i < 5:
                        main_card.append(fight)
                    else:
                        prelims.append(fight)
                
                if main_card:
                    print(f"  {colored('MAIN CARD', Colors.HIGHLIGHT)}")
                    for fight in main_card:
                        self._display_fight_result_card(fight)
                
                if prelims:
                    print(f"  {colored('PRELIMS', Colors.DIM)}")
                    for fight in prelims:
                        self._display_fight_result_card(fight)
                
                # Legend
                print()
                print(f"  {colored('*', Colors.GOLD)} = Finish (KO/TKO/SUB)")
                print()
        
        # =====================================================================
        # FIGHT OF THE NIGHT
        # =====================================================================
        if fotn_info:
            print(f"  {colored('*' * 64, Colors.GOLD)}")
            clean_fotn = self._clean_garbled_text(fotn_info)
            print(f"  {colored('>>> FIGHT OF THE NIGHT <<<', Colors.GOLD):^70}")
            if ":" in clean_fotn:
                parts = clean_fotn.split(":")
                if len(parts) > 1:
                    fighters = parts[1].strip().split("(")[0].strip()
                    print(f"  {colored(fighters, Colors.HIGHLIGHT):^70}")
                    print(f"  {colored('$50,000 bonus to each fighter!', Colors.WIN):^70}")
            print(f"  {colored('*' * 64, Colors.GOLD)}")
            print()
        
        # =====================================================================
        # OTHER EVENTS
        # =====================================================================
        relevant_other = [e for e in other_events if e.strip() and "fight of the night" not in e.lower()]
        if relevant_other:
            print(f"  {colored('[OTHER NEWS]', Colors.MAGENTA)}")
            for event in relevant_other[:5]:
                clean = self._clean_garbled_text(event)
                if clean and len(clean) > 2:
                    print(f"    * {clean}")
            print()
        
        if not week_results and not training_updates and not other_events:
            print(f"  {colored('A quiet week in the world of MMA...', Colors.DIM)}")
            print()
            print("    * Fighters continue training")
            print("    * Preparing for upcoming bouts")
            print()
    
    def _clean_garbled_text(self, text: str) -> str:
        """Remove garbled unicode/emoji characters from text."""
        clean = text
        # Keep only printable ASCII characters
        result = []
        for c in clean:
            code = ord(c)
            if 32 <= code <= 126:
                result.append(c)
            elif c == ' ':
                result.append(' ')
        clean = ''.join(result)
        # Clean up extra whitespace
        while '  ' in clean:
            clean = clean.replace('  ', ' ')
        return clean.strip()

    def _display_fight_result_card(self, fight: dict) -> None:
        """Display a single fight result in card format."""
        winner_name = fight.get("winner_name", "Winner")
        loser_name = fight.get("loser_name", "Loser")
        method = fight.get("method", "Decision")
        round_num = fight.get("round", 3)
        is_title = fight.get("is_title_fight", False)
        is_main = fight.get("is_main_event", False)
        is_co_main = fight.get("is_co_main", False)
        weight_class = fight.get("weight_class", "")
        card_position = fight.get("card_position", 0)
        
        winner_id = fight.get("winner_id")
        loser_id = fight.get("loser_id")
        
        # Get fighter data for records and ranks
        winner_data = self.game_state.fighters.get(winner_id)
        loser_data = self.game_state.fighters.get(loser_id)
        
        winner_record = ""
        loser_record = ""
        winner_rank = ""
        loser_rank = ""
        
        if winner_data:
            winner_record = f"({winner_data.wins}-{winner_data.losses})"
            winner_rank = self._get_fighter_rank_num(winner_data)
        if loser_data:
            loser_record = f"({loser_data.wins}-{loser_data.losses})"
            loser_rank = self._get_fighter_rank_num(loser_data)
        
        # Division abbreviation
        div_abbrev = self._get_division_abbrev(weight_class) if weight_class else "??"
        
        # Card position tag
        if is_title:
            position_tag = colored("[TITLE]", Colors.GOLD)
        elif is_main:
            position_tag = colored("[MAIN]", Colors.ORANGE)
        elif is_co_main or card_position == 1:
            position_tag = colored("[CO-MAIN]", Colors.CYAN)
        else:
            position_tag = ""
        
        # Method formatting
        method_upper = method.upper()
        if "KO" in method_upper or "TKO" in method_upper:
            method_str = colored(f"{method} R{round_num}", Colors.RED)
            is_finish = True
        elif "SUB" in method_upper:
            method_str = colored(f"SUB R{round_num}", Colors.MAGENTA)
            is_finish = True
        else:
            method_str = "DEC"
            is_finish = False
        
        # Format winner and loser with ranks
        if winner_rank:
            winner_str = f"{winner_rank} {colored(winner_name, Colors.WIN)}"
        else:
            winner_str = colored(winner_name, Colors.WIN)
        
        if loser_rank:
            loser_str = f"{loser_rank} {loser_name}"
        else:
            loser_str = loser_name
        
        # Build the line
        # Format: [DIV] [TAG] Winner (rec) METHOD Loser (rec)
        finish_marker = colored("*", Colors.GOLD) if is_finish else " "
        
        line_parts = [f"  {finish_marker}"]
        line_parts.append(colored(f"[{div_abbrev}]", Colors.CYAN))
        
        if position_tag:
            line_parts.append(position_tag)
        
        line_parts.append(f"{winner_str} {winner_record}")
        line_parts.append(method_str)
        line_parts.append(f"{loser_str} {loser_record}")
        
        print(" ".join(line_parts))
        
        # Show controversy if this was a controversial decision
        is_controversial = fight.get("is_controversial", False)
        controversy_reason = fight.get("controversy_reason", "")
        if is_controversial and controversy_reason and not is_finish:
            print(f"       {colored('!', Colors.YELLOW)} {colored(controversy_reason, Colors.YELLOW)}")
        
        # Show ranking changes if significant
        ranking_changes = fight.get("ranking_changes", [])
        for rc in ranking_changes[:1]:  # Only show most significant
            moved = abs(rc.get('positions_moved', 0))
            if rc.get('new_rank') == 0:  # New champion
                print(f"       {colored('^', Colors.GREEN)} {rc.get('fighter_name', '')} is the NEW CHAMPION!")
            elif moved >= 3 and rc.get('is_promotion'):
                new_r = f"#{rc.get('new_rank')}"
                print(f"       {colored('^', Colors.GREEN)} {rc.get('fighter_name', '')} rises to {new_r}")
    
    def _get_fighter_rank_num(self, fighter) -> str:
        """Get rank number string like #5 or [C]."""
        if fighter.is_champion:
            return colored("[C]", Colors.GOLD)
        
        div_fighters = [f for f in self.game_state.fighters.values()
                       if f.weight_class == fighter.weight_class 
                       and f.is_active and not f.is_champion]
        div_fighters.sort(key=lambda f: f.overall_rating, reverse=True)
        
        for i, f in enumerate(div_fighters[:15], 1):
            if f.fighter_id == fighter.fighter_id:
                return f"#{i}"
        
        return ""


    def show_history_menu(self) -> None:
        """History and records menu"""
        while True:
            clear_screen()
            print_header("THE ARCHIVES")
            
            options = [
                ("1", "Past Events"),
                ("2", "G.O.A.T. Rankings"),
                ("3", "Record Book"),
                ("4", "Record Book by Division"),
                ("5", "Champions History"),
                ("0", "Back"),
            ]
            
            print_menu(options)
            choice = get_choice(["1", "2", "3", "4", "5", "0"])
            
            if choice == "0":
                return
            elif choice == "1":
                self.show_past_events()
            elif choice == "2":
                self.show_goat_rankings()
            elif choice == "3":
                self.show_record_book()
            elif choice == "4":
                self.show_record_book_by_division()
            elif choice == "5":
                self.show_champions_history()
    
    def show_past_events(self) -> None:
        """Display list of past events"""
        clear_screen()
        print_header("PAST EVENTS")
        
        if not self.completed_events:
            print("No events have been completed yet.")
            print()
            print("Events will appear here after fight nights conclude.")
            pause()
            return
        
        # Sort by week descending
        events = sorted(self.completed_events, key=lambda e: e.week, reverse=True)
        
        for i, event in enumerate(events[:15], 1):
            print(f"  [{i}] {event.event_name} (Week {event.week})")
            print(f"      {event.total_fights} fights | {event.finishes} finishes")
            print()
        
        print(f"  [0] Back")
        print()
        
        choice = get_input("View event: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(events):
                self.show_event_details(events[index - 1])
        except ValueError:
            pass
    
    def show_event_details(self, event: CompletedEvent) -> None:
        """Display detailed event results"""
        clear_screen()
        print_header(f"{event.event_name}")
        
        print(f"  Week {event.week} | {event.location}")
        print()
        print(f"  Total Fights: {event.total_fights}")
        print(f"  Finishes: {event.finishes} ({event.knockouts} KO, {event.submissions} SUB)")
        print(f"  Decisions: {event.decisions}")
        print()
        print_divider()
        print()
        print(colored("  RESULTS:", Colors.BOLD))
        print()
        
        for i, fight in enumerate(event.fights, 1):
            title_tag = colored(" [TITLE]", Colors.GOLD) if fight.is_title_fight else ""
            main_tag = colored(" [MAIN]", Colors.ORANGE) if fight.is_main_event and not fight.is_title_fight else ""
            
            print(f"  {i}. {fight.fighter1_name} vs {fight.fighter2_name}{title_tag}{main_tag}")
            print(f"     {colored('W', Colors.WIN)} {fight.winner_name} by {fight.method}", end="")
            if fight.method != "DEC":
                print(f" (R{fight.round_finished})")
            else:
                print()
            print()
        
        print()
        print(f"  [#] View Fight Details | [0] Back")
        print()
        
        choice = get_input("> ")
        
        if choice == "0":
            return
        
        try:
            index = int(choice)
            if 1 <= index <= len(event.fights):
                self.show_fight_details(event.fights[index - 1])
        except ValueError:
            pass
    
    def show_fight_details(self, fight: FightResult) -> None:
        """Display detailed fight result with full commentary"""
        clear_screen()
        
        title = "TITLE FIGHT" if fight.is_title_fight else "FIGHT RESULT"
        print_header(title)
        
        # Main result
        print(f"  {fight.fighter1_name} vs {fight.fighter2_name}")
        print()
        
        if fight.method == "DRAW":
            print(f"  Result: {colored('DRAW', Colors.NEUTRAL)}")
        else:
            print(f"  Winner: {colored(fight.winner_name, Colors.WIN)}")
            if fight.method == "DEC":
                decision_info = f" ({fight.decision_type})" if fight.decision_type else ""
                print(f"  Method: Decision{decision_info} ({fight.rounds_scheduled} rounds)")
                
                # Show decision commentary if available
                if hasattr(fight, 'decision_commentary') and fight.decision_commentary:
                    print()
                    print(f"  {colored('ANNOUNCEMENT:', Colors.CYAN)}")
                    # Wrap commentary lines
                    for line in fight.decision_commentary.split("\n"):
                        if line.strip():
                            print(f"    {line.strip()}")
                
                # Show judge scores with names if available
                if fight.judge_scores:
                    if hasattr(fight, 'judge_names') and fight.judge_names and len(fight.judge_names) == len(fight.judge_scores):
                        print(f"  {colored('SCORECARDS:', Colors.CYAN)}")
                        for name, (s1, s2) in zip(fight.judge_names, fight.judge_scores):
                            # Determine who this judge scored for
                            if s1 > s2:
                                score_display = f"{s1}-{s2}"
                            else:
                                score_display = f"{s2}-{s1}"
                            print(f"    {name}: {score_display}")
                    else:
                        scores_str = ", ".join([f"{s1}-{s2}" for s1, s2 in fight.judge_scores])
                        print(f"  Scores: {scores_str}")
                
                # Show controversy if present
                if hasattr(fight, 'is_controversial') and fight.is_controversial:
                    reason = getattr(fight, 'controversy_reason', '')
                    if reason:
                        print(f"  {colored('* CONTROVERSIAL:', Colors.YELLOW)} {reason}")
            else:
                time_str = f", {fight.time_finished}" if fight.time_finished != "5:00" else ""
                print(f"  Method: {fight.method} (Round {fight.round_finished}{time_str})")
        
        # Bonuses
        if fight.fight_of_night:
            print(f"  {colored('* Fight of the Night', Colors.GOLD)}")
        if fight.performance_bonus:
            print(f"  {colored('* Performance of the Night', Colors.GOLD)}")
        
        print()
        print_divider()
        print()
        
        # Fight narrative/summary
        print(colored("  FIGHT SUMMARY:", Colors.BOLD))
        print()
        
        # Wrap text for display
        summary = fight.fight_summary or fight.fight_narrative or "No summary available."
        words = summary.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 64:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        for line in lines:
            print(f"  {line}")
        print()
        
        # Key moments
        if fight.key_moments:
            print(colored("  KEY MOMENTS:", Colors.BOLD))
            print()
            for moment in fight.key_moments[:5]:  # Show top 5
                if isinstance(moment, dict):
                    moment_str = moment.get("description", str(moment))
                else:
                    moment_str = str(moment)
                print(f"  * {moment_str[:60]}")
            print()
        
        # Round-by-round stats if available
        if fight.fighter1_round_stats and fight.fighter2_round_stats:
            print(colored("  ROUND-BY-ROUND:", Colors.BOLD))
            print()
            
            for i, (f1_stats, f2_stats) in enumerate(zip(fight.fighter1_round_stats, fight.fighter2_round_stats), 1):
                f1_sig = f1_stats.get("sig_strikes_landed", 0)
                f2_sig = f2_stats.get("sig_strikes_landed", 0)
                f1_td = f1_stats.get("td_landed", 0)
                f2_td = f2_stats.get("td_landed", 0)
                
                # Determine round winner
                f1_dmg = f1_stats.get("damage", 0)
                f2_dmg = f2_stats.get("damage", 0)
                
                if f1_dmg > f2_dmg:
                    rd_winner = fight.fighter1_name.split()[-1]  # Last name
                elif f2_dmg > f1_dmg:
                    rd_winner = fight.fighter2_name.split()[-1]
                else:
                    rd_winner = "Even"
                
                print(f"  Round {i}: {colored(rd_winner, Colors.CYAN)}")
                f1_short = fight.fighter1_name.split()[-1][:8]
                f2_short = fight.fighter2_name.split()[-1][:8]
                print(f"    {f1_short}: {f1_sig} sig strikes, {f1_td} TD")
                print(f"    {f2_short}: {f2_sig} sig strikes, {f2_td} TD")
            print()
        else:
            # Basic stats
            print(colored("  STATS:", Colors.BOLD))
            print()
            print(f"  {fight.fighter1_name}:")
            print(f"    Significant Strikes: {fight.fighter1_strikes}")
            print(f"    Takedowns: {fight.fighter1_takedowns}")
            if fight.fighter1_sub_attempts:
                print(f"    Submission Attempts: {fight.fighter1_sub_attempts}")
            print()
            print(f"  {fight.fighter2_name}:")
            print(f"    Significant Strikes: {fight.fighter2_strikes}")
            print(f"    Takedowns: {fight.fighter2_takedowns}")
            if fight.fighter2_sub_attempts:
                print(f"    Submission Attempts: {fight.fighter2_sub_attempts}")
            print()
        
        # Show option to view full commentary if available
        if fight.has_full_commentary and fight.full_commentary:
            print(f"  [{colored('C', Colors.CYAN)}] View Full Commentary | Press Enter to continue")
            choice = get_input("> ").lower()
            if choice == 'c':
                self._show_full_fight_commentary(fight)
        else:
            pause()
    
    def _show_full_fight_commentary(self, fight: FightResult) -> None:
        """Display the full round-by-round commentary"""
        clear_screen()
        print_header("FULL FIGHT COMMENTARY")
        
        print(f"  {fight.fighter1_name} vs {fight.fighter2_name}")
        print()
        print_divider()
        print()
        
        # Split commentary into chunks for paging
        commentary = fight.full_commentary
        if not commentary:
            print("  No detailed commentary available.")
            pause()
            return
        
        # Display commentary line by line
        lines = commentary.split('\n')
        line_count = 0
        lines_per_page = 20
        
        for line in lines:
            # Word wrap long lines
            if len(line) > 66:
                words = line.split()
                current = ""
                for word in words:
                    if len(current) + len(word) + 1 <= 66:
                        current += (" " if current else "") + word
                    else:
                        print(f"  {current}")
                        line_count += 1
                        current = word
                if current:
                    print(f"  {current}")
                    line_count += 1
            else:
                print(f"  {line}")
                line_count += 1
            
            # Page break
            if line_count >= lines_per_page:
                print()
                choice = get_input("  -- Press Enter for more, 'q' to quit -- ")
                if choice.lower() == 'q':
                    return
                line_count = 0
                print()
        
        print()
        pause()
    
    def show_goat_rankings(self) -> None:
        """Display GOAT rankings"""
        clear_screen()
        print_header("G.O.A.T. RANKINGS")
        
        all_fighters = list(self.game_state.fighters.values())
        
        if not all_fighters:
            print("No fighters to rank.")
            pause()
            return
        
        def goat_score(f):
            score = f.wins * 10 - f.losses * 5 + f.draws * 2
            score += f.ko_wins * 5 + f.sub_wins * 5
            if f.is_champion:
                score += 50
            return max(0, score)
        
        scored = [(f, goat_score(f)) for f in all_fighters if f.wins + f.losses > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        print("  The greatest fighters in DFC history:")
        print()
        
        medals = ["[*]", "", "[*]"] + ["  "] * 20
        
        for i, (fighter, score) in enumerate(scored[:20], 1):
            medal = medals[min(i - 1, len(medals) - 1)]
            champ_tag = colored(" ", Colors.GOLD) if fighter.is_champion else ""
            
            print(f"  {medal} #{i:2} {fighter.name}{champ_tag}")
            print(f"        {format_record_colored(fighter.wins, fighter.losses)} | Score: {score}")
            print()
        
        pause()
    
    def show_record_book(self) -> None:
        """Display record book"""
        clear_screen()
        print_header("RECORD BOOK")
        
        fighters = list(self.game_state.fighters.values())
        
        if not fighters:
            print("No fighters.")
            pause()
            return
        
        records = {
            "Most Wins": sorted(fighters, key=lambda f: f.wins, reverse=True)[:5],
            "Most KO Wins": sorted(fighters, key=lambda f: f.ko_wins, reverse=True)[:5],
            "Most Submissions": sorted(fighters, key=lambda f: f.sub_wins, reverse=True)[:5],
        }
        
        for category, top_fighters in records.items():
            print(f"  {colored(category, Colors.BOLD)}:")
            print()
            
            for rank, fighter in enumerate(top_fighters, 1):
                if category == "Most Wins":
                    val = f"{fighter.wins} wins"
                elif category == "Most KO Wins":
                    val = f"{fighter.ko_wins} KOs"
                else:
                    val = f"{fighter.sub_wins} subs"
                
                print(f"    {rank}. {fighter.name[:24]:<24} {val:>12}")
            print()
        
        pause()
    
    def show_record_book_by_division(self) -> None:
        """Record book by division"""
        clear_screen()
        print_header("RECORD BOOK BY DIVISION")
        
        divisions = list(self.game_state.divisions.keys())
        
        for i, div in enumerate(divisions, 1):
            print(f"  [{i}] {div}")
        print()
        print(f"  [0] Back")
        print()
        
        choice = get_input("Select: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(divisions):
                self.show_division_record_book(divisions[index - 1])
        except ValueError:
            pass
    
    def show_division_record_book(self, division: str) -> None:
        """Show records for a division"""
        clear_screen()
        print_header(f"RECORD BOOK - {division.upper()}")
        
        fighters = [f for f in self.game_state.fighters.values() if f.weight_class == division]
        
        if not fighters:
            print("No fighters in this division.")
            pause()
            return
        
        print(f"  {colored('Most Wins:', Colors.BOLD)}")
        for rank, f in enumerate(sorted(fighters, key=lambda x: x.wins, reverse=True)[:5], 1):
            print(f"    {rank}. {f.name} - {f.wins} wins")
        print()
        
        print(f"  {colored('Most KOs:', Colors.BOLD)}")
        for rank, f in enumerate(sorted(fighters, key=lambda x: x.ko_wins, reverse=True)[:5], 1):
            print(f"    {rank}. {f.name} - {f.ko_wins} KOs")
        print()
        
        pause()
    
    def show_champions_history(self) -> None:
        """Show current champions"""
        clear_screen()
        print_header("CHAMPIONS")
        
        divisions = list(self.game_state.divisions.keys())
        
        print("  Current DFC World Champions:")
        print()
        print(f"  {'DIVISION':<20} {'CHAMPION':<25} {'RECORD':<12}")
        print(f"  {'-' * 58}")
        
        for div_name in divisions:
            champion = None
            for f in self.game_state.fighters.values():
                if f.weight_class == div_name and f.is_champion:
                    champion = f
                    break
            
            if champion:
                record = format_record_colored(champion.wins, champion.losses)
                print(f"  {div_name:<20} {colored(' ' + champion.name[:20], Colors.GOLD):<33} {record}")
            else:
                print(f"  {div_name:<20} {colored('VACANT', Colors.DIM):<25} -")
        
        print()
        pause()
    
    # -------------------------------------------------------------------------
    # Browse Menus
    # -------------------------------------------------------------------------
    
    def show_camp(self) -> None:
        """Show camp management"""
        clear_screen()
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            print("No camp found!")
            pause()
            return
        
        print_header(f"[*] {player_camp.name}")
        
        stats = []
        tier = self._get_camp_tier()
        stats.append(f"Tier: {tier}")
        stats.append(f"Balance: {format_money(player_camp.balance)}")
        
        camp_id = player_camp.camp_id
        fighters = [f for f in self.game_state.fighters.values() if f.camp_id == camp_id]
        stats.append(f"Fighters: {len(fighters)}")
        
        print_box(stats, title="CAMP STATS")
        
        if self.player_scheduled_fights:
            print()
            print("  UPCOMING FIGHTS:")
            for fight in self.player_scheduled_fights[:3]:
                print(f"   {fight.get('fighter1_name')} vs {fight.get('fighter2_name')} ({fight.get('weeks_until')} weeks)")
            print()
        
        options = [
            ("1", "My Fighters"),
            ("2", "Scout Free Agents"),
            ("3", f"Fight Offers ({len(self.fight_offers)})"),
            ("4", "[$] Finances"),
            ("5", "[U] Upgrade Camp"),
            ("0", "Back"),
        ]
        print_menu(options)
        
        choice = get_choice(["1", "2", "3", "4", "5", "0"])
        
        if choice == "1":
            self.show_fighters()
        elif choice == "2":
            self.scout_free_agent()
        elif choice == "3":
            self.show_fight_offers()
        elif choice == "4":
            self.show_finances_menu()
        elif choice == "5":
            self.show_upgrade_menu()
    
    # -------------------------------------------------------------------------
    # Upcoming Events
    # -------------------------------------------------------------------------
    
    def show_finances_menu(self) -> None:
        """Show detailed finances, sponsorships, and loan options."""
        if not self._economy_manager or not ECONOMY_AVAILABLE:
            print("Economy system not available.")
            pause()
            return
        
        while True:
            clear_screen()
            
            player_camp = self.game_state.get_player_camp()
            if not player_camp:
                print("No camp found!")
                pause()
                return
            
            camp_id = player_camp.camp_id
            tier = self._get_camp_tier()
            
            print_header("[$] FINANCES")
            
            # Get financial data
            summary = self._economy_manager.get_financial_summary(camp_id)
            finance_state = self._economy_manager.get_camp_finances(camp_id)
            
            # Balance section
            balance_color = Colors.GREEN if summary["balance"] >= 0 else Colors.RED
            print(f"\n  {colored('BALANCE', Colors.HIGHLIGHT)}")
            print(f"  {'-' * 50}")
            print(f"  Current Balance:  {colored(format_money(summary['balance']), balance_color)}")
            print(f"  Total Debt:       {colored(format_money(summary['total_debt']), Colors.RED) if summary['total_debt'] > 0 else format_money(0)}")
            print(f"  Net Worth:        {format_money(summary['net_worth'])}")
            
            # Camp Sponsorship Section
            print(f"\n  {colored('CAMP SPONSOR', Colors.GOLD)}")
            print(f"  {'-' * 50}")
            if finance_state.camp_sponsorship and finance_state.camp_sponsorship.is_active:
                sponsor = finance_state.camp_sponsorship
                print(f"  {colored(sponsor.company_name, Colors.HIGHLIGHT)}")
                print(f"  Weekly Income: {colored(f'+{format_money(sponsor.weekly_payment)}', Colors.GREEN)}")
                if sponsor.training_bonus > 0:
                    print(f"  Training Bonus: {colored(f'+{sponsor.training_bonus*100:.0f}%', Colors.CYAN)}")
            else:
                print(f"  {colored('No camp sponsor', Colors.DIM)}")
                if tier.upper() != "GARAGE":
                    print(f"  {colored('(Upgrade or seek sponsorship)', Colors.DIM)}")
            
            # Weekly costs/income breakdown
            fighters = [f for f in self.game_state.fighters.values() if f.camp_id == camp_id]
            facility_weekly = CAMP_MONTHLY_COSTS.get(tier, 5000) // 4
            
            # Get actual coach salaries
            coach_weekly = 2000
            if COACHES_AVAILABLE and self._coach_system:
                try:
                    coach_weekly = self._coach_system.get_total_weekly_salary(camp_id)
                except:
                    pass
            
            # Fighter overhead by tier
            overhead_per_fighter = FIGHTER_OVERHEAD_BY_TIER.get(tier.upper(), 100) if ECONOMY_AVAILABLE else 100
            fighter_weekly = len(fighters) * overhead_per_fighter
            
            # Camp sponsor income
            camp_sponsor_income = 0
            if finance_state.camp_sponsorship and finance_state.camp_sponsorship.is_active:
                camp_sponsor_income = finance_state.camp_sponsorship.weekly_payment
            
            total_expenses = facility_weekly + coach_weekly + fighter_weekly
            total_income = camp_sponsor_income
            
            print(f"\n  {colored('WEEKLY BREAKDOWN', Colors.BOLD)}")
            print(f"  {'-' * 50}")
            
            # Income
            if total_income > 0:
                print(f"  {colored('Income:', Colors.GREEN)}")
                if camp_sponsor_income > 0:
                    print(f"    Camp Sponsor:      +{format_money(camp_sponsor_income)}")
            
            # Expenses
            print(f"  {colored('Expenses:', Colors.RED)}")
            print(f"    Facility ({tier}):    -{format_money(facility_weekly)}")
            print(f"    Coach Salaries:     -{format_money(coach_weekly)}")
            print(f"    Fighter Overhead:   -{format_money(fighter_weekly)} ({len(fighters)}  ${overhead_per_fighter})")
            
            if finance_state.active_loans:
                min_payment = sum(l.min_weekly_payment for l in finance_state.active_loans)
                print(f"    Loan Payments:      -{format_money(min_payment)}")
                total_expenses += min_payment
            
            print(f"  {'-' * 50}")
            net_weekly = total_income - total_expenses
            net_color = Colors.GREEN if net_weekly >= 0 else Colors.RED
            print(f"  {colored('NET WEEKLY:', Colors.BOLD)}        {colored(format_money(net_weekly), net_color)}")
            
            # Runway
            if summary["balance"] > 0 and total_expenses > total_income:
                runway = summary["balance"] // (total_expenses - total_income)
                runway_color = Colors.GREEN if runway >= 12 else Colors.YELLOW if runway >= 6 else Colors.RED
                print(f"\n  Runway: {colored(f'~{runway} weeks', runway_color)} until funds depleted")
            
            # Fighter Sponsorships Summary
            sponsored_fighters = []
            for f_id in self.fighter_data:
                if self.fighter_data[f_id].camp_id == camp_id:
                    sponsor = self._economy_manager.get_fighter_sponsor(f_id)
                    if sponsor and sponsor.is_active:
                        sponsored_fighters.append((self.fighter_data[f_id].name, sponsor))
            
            if sponsored_fighters:
                print(f"\n  {colored('FIGHTER SPONSORS', Colors.CYAN)}")
                print(f"  {'-' * 50}")
                for fname, sponsor in sponsored_fighters[:5]:  # Show up to 5
                    fights_left = f"({sponsor.fights_remaining} fights left)"
                    print(f"  {fname}: {colored(sponsor.company_name, Colors.HIGHLIGHT)} {fights_left}")
                if len(sponsored_fighters) > 5:
                    print(f"  ... and {len(sponsored_fighters) - 5} more")
            
            # Loan status
            if finance_state.active_loans:
                print(f"\n  {colored('ACTIVE LOANS', Colors.RED)}")
                print(f"  {'-' * 50}")
                for loan in finance_state.active_loans:
                    emergency_tag = colored(" [EMERGENCY]", Colors.ORANGE) if loan.is_emergency else ""
                    print(f"  Balance: {colored(format_money(loan.current_balance), Colors.RED)}{emergency_tag}")
                    print(f"  Interest: {loan.interest_rate * 100:.1f}%/month | Min Payment: {format_money(loan.min_weekly_payment)}/week")
            
            print()
            options = [
                ("1", "Take Out Loan"),
                ("2", "Make Loan Payment"),
                ("3", "Transaction History"),
                ("4", "Fighter Sponsorships"),
                ("5", "Seek Camp Sponsor"),
                ("0", "Back"),
            ]
            print_menu(options)
            
            choice = get_choice(["1", "2", "3", "4", "5", "0"])
            
            if choice == "1":
                self._take_loan_menu()
            elif choice == "2":
                self._make_loan_payment_menu()
            elif choice == "3":
                self._show_transaction_history()
            elif choice == "4":
                self._show_fighter_sponsorships()
            elif choice == "5":
                self._seek_camp_sponsor()
            elif choice == "0":
                return

    def _take_loan_menu(self) -> None:
        """Menu to take out a loan."""
        if not self._economy_manager:
            return
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        clear_screen()
        print_header("[B] TAKE OUT LOAN")
        
        tier = self._get_camp_tier()
        options = self._economy_manager.get_loan_options(player_camp.camp_id, tier)
        
        print(f"\n  Loan Terms for {tier} Camp:")
        print(f"  {'-' * 40}")
        print(f"  Maximum Loan:     {format_money(options['max_loan'])}")
        print(f"  Available:        {format_money(options['available'])}")
        print(f"  Interest Rate:    {options['interest_rate_display']}")
        
        if not options['can_take_loan']:
            print(colored(f"\n  Cannot take loan: {options.get('reason', 'At max debt')}", Colors.RED))
            pause()
            return
        
        print(f"\n  Enter amount (max {format_money(options['available'])}):")
        amount_str = get_input("  Amount: $")
        if not amount_str:
            return
        
        try:
            amount = int(amount_str.replace(",", "").replace("$", ""))
        except ValueError:
            print(colored("  Invalid amount!", Colors.RED))
            pause()
            return
        
        if amount <= 0 or amount > options['available']:
            print(colored("  Invalid amount!", Colors.RED))
            pause()
            return
        
        if not confirm(f"  Take ${amount:,} loan?"):
            return
        
        success, message, loan = self._economy_manager.take_loan(
            player_camp.camp_id, amount, tier, self.game_state.week_number
        )
        
        if success:
            player_camp._balance = self._economy_manager.get_balance(player_camp.camp_id)
            print(colored(f"\n  [OK] {message}", Colors.GREEN))
            print(f"  New Balance: {format_money(player_camp.balance)}")
        else:
            print(colored(f"\n   {message}", Colors.RED))
        
        pause()

    def _make_loan_payment_menu(self) -> None:
        """Menu to make extra loan payment."""
        if not self._economy_manager:
            return
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        finance_state = self._economy_manager.get_camp_finances(player_camp.camp_id)
        
        clear_screen()
        print_header("[$] MAKE LOAN PAYMENT")
        
        if not finance_state.active_loans:
            print("\n  No active loans!")
            pause()
            return
        
        total_debt = finance_state.total_debt
        print(f"\n  Balance: {format_money(player_camp.balance)}")
        print(f"  Total Debt: {format_money(total_debt)}")
        
        max_payment = min(player_camp.balance, total_debt)
        print(f"\n  Enter payment (max {format_money(max_payment)}):")
        amount_str = get_input("  Amount: $")
        if not amount_str:
            return
        
        try:
            amount = int(amount_str.replace(",", "").replace("$", ""))
        except ValueError:
            print(colored("  Invalid!", Colors.RED))
            pause()
            return
        
        if amount <= 0 or amount > player_camp.balance:
            print(colored("  Invalid amount!", Colors.RED))
            pause()
            return
        
        success, message = self._economy_manager.make_extra_loan_payment(
            player_camp.camp_id, amount
        )
        
        if success:
            player_camp._balance = self._economy_manager.get_balance(player_camp.camp_id)
            print(colored(f"\n  [OK] {message}", Colors.GREEN))
        else:
            print(colored(f"\n   {message}", Colors.RED))
        
        pause()

    def _show_fighter_sponsorships(self) -> None:
        """Show all fighter sponsorships and offer to seek new ones."""
        if not self._economy_manager:
            return
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        while True:
            clear_screen()
            print_header("FIGHTER SPONSORSHIPS")
            
            # Get all player fighters
            camp_fighters = [f for f_id, f in self.fighter_data.items() 
                           if f.camp_id == player_camp.camp_id]
            
            if not camp_fighters:
                print("\n  No fighters in your camp!")
                pause()
                return
            
            print()
            for i, fighter in enumerate(camp_fighters, 1):
                sponsor = self._economy_manager.get_fighter_sponsor(fighter.fighter_id)
                
                # Get fighter rank
                rank = None
                if fighter.fighter_id in self.game_state.fighters:
                    rank = getattr(self.game_state.fighters[fighter.fighter_id], 'rank', None)
                
                rank_str = f"#{rank}" if rank else "Unranked"
                champ_str = colored(" [C]", Colors.GOLD) if fighter.is_champion else ""
                
                print(f"  [{i}] {colored(fighter.name, Colors.HIGHLIGHT)}{champ_str} ({rank_str})")
                
                if sponsor and sponsor.is_active:
                    tier_color = {
                        "elite": Colors.GOLD,
                        "ranked": Colors.CYAN,
                        "prospect": Colors.GREEN,
                        "local": Colors.DIM,
                    }.get(sponsor.tier.value, Colors.NEUTRAL)
                    
                    print(f"      Sponsor: {colored(sponsor.company_name, tier_color)}")
                    print(f"      Payment: {format_money(sponsor.payment_per_fight)}/fight | {sponsor.fights_remaining} fights remaining")
                    print(f"      Bonuses: Win +{format_money(sponsor.get_win_bonus())} | Finish +{format_money(sponsor.get_finish_bonus())}")
                else:
                    print(f"      {colored('No sponsor', Colors.DIM)} - {colored('[Seek Sponsorship]', Colors.CYAN)}")
                print()
            
            print(f"  [S] Seek sponsorship for a fighter")
            print(f"  [0] Back")
            print()
            
            choice = get_input("Select: ").strip().upper()
            
            if choice == "0":
                return
            elif choice == "S":
                self._seek_fighter_sponsorship(camp_fighters)
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(camp_fighters):
                    fighter = camp_fighters[idx]
                    sponsor = self._economy_manager.get_fighter_sponsor(fighter.fighter_id)
                    if not sponsor or not sponsor.is_active:
                        self._seek_fighter_sponsorship([fighter])
    
    def _seek_fighter_sponsorship(self, fighters: list) -> None:
        """Seek sponsorship offers for fighters."""
        if not self._economy_manager:
            return
        
        clear_screen()
        print_header("SEEK SPONSORSHIP")
        
        # Show eligible fighters
        eligible = []
        for fighter in fighters:
            sponsor = self._economy_manager.get_fighter_sponsor(fighter.fighter_id)
            if sponsor and sponsor.is_active:
                continue  # Already sponsored
            
            rank = None
            if fighter.fighter_id in self.game_state.fighters:
                rank = getattr(self.game_state.fighters[fighter.fighter_id], 'rank', None)
            
            eligible.append((fighter, rank))
        
        if not eligible:
            print("\n  No fighters eligible for new sponsorship!")
            print("  (All fighters are currently sponsored)")
            pause()
            return
        
        print("\n  Select a fighter to seek sponsorship for:")
        print()
        
        for i, (fighter, rank) in enumerate(eligible, 1):
            rank_str = f"#{rank}" if rank else "Unranked"
            wins = fighter.wins
            print(f"  [{i}] {fighter.name} ({rank_str}, {wins}W)")
        
        print(f"  [0] Cancel")
        
        choice = get_input("\nSelect: ").strip()
        
        if choice == "0" or not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(eligible):
            return
        
        fighter, rank = eligible[idx]
        
        # Generate offers
        offers = self._economy_manager.get_sponsorship_offers_for_fighter(
            fighter_id=fighter.fighter_id,
            rank=rank,
            is_champion=fighter.is_champion,
            wins=fighter.wins,
        )
        
        if not offers:
            print(f"\n  {colored('No sponsorship offers available.', Colors.DIM)}")
            print("  (Fighter may need more wins or a higher ranking)")
            pause()
            return
        
        clear_screen()
        print_header(f"SPONSORSHIP OFFERS FOR {fighter.name.upper()}")
        
        print()
        for i, offer in enumerate(offers, 1):
            tier_color = {
                "elite": Colors.GOLD,
                "ranked": Colors.CYAN,
                "prospect": Colors.GREEN,
                "local": Colors.DIM,
            }.get(offer.tier.value, Colors.NEUTRAL)
            
            print(f"  [{i}] {colored(offer.company_name, tier_color)} ({offer.tier.value.upper()})")
            print(f"      Payment: {colored(format_money(offer.payment_per_fight), Colors.GREEN)}/fight")
            print(f"      Contract: {offer.fights_total} fights")
            print(f"      Bonuses: Win +{format_money(offer.get_win_bonus())} | Title +{format_money(offer.get_title_win_bonus())} | Finish +{format_money(offer.get_finish_bonus())}")
            print()
        
        print(f"  [0] Decline all")
        
        choice = get_input("\nAccept offer: ").strip()
        
        if choice == "0" or not choice.isdigit():
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(offers):
            return
        
        offer = offers[idx]
        self._economy_manager.set_fighter_sponsor(fighter.fighter_id, offer)
        
        print(f"\n  {colored('[OK]', Colors.GREEN)} {fighter.name} signs with {colored(offer.company_name, Colors.HIGHLIGHT)}!")
        print(f"      {offer.fights_total}-fight deal worth {format_money(offer.payment_per_fight)}/fight")
        
        # Add news
        self.news_feed.insert(0, NewsItem(
            headline=f" {offer.company_name} signs {fighter.name} to sponsorship deal",
            category="business",
            week=self.game_state.week_number,
        ))
        
        pause()
    
    def _seek_camp_sponsor(self) -> None:
        """Seek a facility sponsor for the camp."""
        if not self._economy_manager:
            return
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        tier = self._get_camp_tier()
        finance_state = self._economy_manager.get_camp_finances(player_camp.camp_id)
        
        clear_screen()
        print_header("SEEK CAMP SPONSOR")
        
        # Check if already has sponsor
        if finance_state.camp_sponsorship and finance_state.camp_sponsorship.is_active:
            print(f"\n  Your camp is already sponsored by {colored(finance_state.camp_sponsorship.company_name, Colors.HIGHLIGHT)}!")
            print("  (Camp sponsors are long-term partnerships)")
            pause()
            return
        
        # Garage gyms can't get sponsors
        if tier.upper() == "GARAGE":
            print(f"\n  {colored('GARAGE tier camps cannot attract facility sponsors.', Colors.DIM)}")
            print("  Upgrade to LOCAL tier to become eligible.")
            pause()
            return
        
        # Generate offer
        offer = self._economy_manager.offer_camp_sponsorship(player_camp.camp_id, tier)
        
        if not offer:
            print(f"\n  {colored('No camp sponsorship offers available right now.', Colors.DIM)}")
            print("  Try again after winning some fights!")
            pause()
            return
        
        print(f"\n  {colored('SPONSORSHIP OFFER', Colors.GOLD)}")
        print(f"  {'-' * 50}")
        print(f"  Company: {colored(offer.company_name, Colors.HIGHLIGHT)}")
        print(f"  Weekly Payment: {colored(f'+{format_money(offer.weekly_payment)}', Colors.GREEN)}")
        if offer.training_bonus > 0:
            print(f"  Training Bonus: {colored(f'+{offer.training_bonus*100:.0f}%', Colors.CYAN)}")
        print()
        
        if confirm("  Accept this sponsorship?"):
            self._economy_manager.accept_camp_sponsorship(player_camp.camp_id, offer)
            
            print(f"\n  {colored('[OK]', Colors.GREEN)} Your camp is now sponsored by {colored(offer.company_name, Colors.HIGHLIGHT)}!")
            
            # Add news
            self.news_feed.insert(0, NewsItem(
                headline=f" {player_camp.name} becomes official {offer.company_name} Training Center",
                category="business",
                week=self.game_state.week_number,
            ))
        
        pause()
    
    def _offer_sponsorship_after_win(self, fighter_id: str, fighter_name: str, was_title_fight: bool = False) -> None:
        """Check and offer sponsorship after a fight win."""
        if not self._economy_manager:
            return
        
        # Check if fighter already has sponsor
        current_sponsor = self._economy_manager.get_fighter_sponsor(fighter_id)
        if current_sponsor and current_sponsor.is_active:
            return  # Already sponsored
        
        # Get fighter data
        fighter = self.fighter_data.get(fighter_id)
        if not fighter:
            return
        
        rank = None
        if fighter_id in self.game_state.fighters:
            rank = getattr(self.game_state.fighters[fighter_id], 'rank', None)
        
        # Only offer if fighter has enough wins or is ranked
        if fighter.wins < 3 and rank is None:
            return
        
        # Generate offer (30% base chance, higher for ranked/champs)
        offer = generate_sponsorship_offer(
            rank=rank,
            is_champion=fighter.is_champion,
            wins=fighter.wins,
            fighter_id=fighter_id,
            offer_chance=0.4 if was_title_fight else 0.25,
        )
        
        if not offer:
            return
        
        # Show offer to player
        print()
        print(f"  {colored('>>> SPONSORSHIP OFFER <<<', Colors.GOLD)}")
        print(f"  {offer.company_name} wants to sponsor {fighter_name}!")
        print(f"  {format_money(offer.payment_per_fight)}/fight for {offer.fights_total} fights")
        print()
        
        if confirm("  Accept sponsorship?"):
            self._economy_manager.set_fighter_sponsor(fighter_id, offer)
            print(f"  {colored('[OK]', Colors.GREEN)} Deal signed!")
            
            self.news_feed.insert(0, NewsItem(
                headline=f" {offer.company_name} signs {fighter_name} to sponsorship deal",
                category="business",
                week=self.game_state.week_number,
            ))
    
    def _show_transaction_history(self) -> None:
        """Show recent transactions."""
        if not self._economy_manager:
            return
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        clear_screen()
        print_header("[D] TRANSACTIONS")
        
        transactions = self._economy_manager.get_recent_transactions(
            player_camp.camp_id, limit=15
        )
        
        if not transactions:
            print("\n  No transactions yet.")
            pause()
            return
        
        print(f"\n  {'Type':<20} {'Amount':<12}")
        print(f"  {'-' * 35}")
        
        for t in reversed(transactions[-15:]):
            trans_type = t.transaction_type.value.replace("_", " ").title()[:18]
            if t.is_income:
                amount_str = colored(f"+{format_money(t.amount)}", Colors.GREEN)
            else:
                amount_str = colored(f"-{format_money(abs(t.amount))}", Colors.RED)
            print(f"  {trans_type:<20} {amount_str}")
        
        print()
        pause()

    def show_upgrade_menu(self) -> None:
        """Show camp upgrade options."""
        if not self._economy_manager or not ECONOMY_AVAILABLE:
            print("Economy system not available.")
            pause()
            return
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        clear_screen()
        print_header("[U] UPGRADE CAMP")
        
        current_tier = self._get_camp_tier()
        info = self._economy_manager.get_upgrade_info(current_tier)
        
        if not info:
            print(f"\n  Already at maximum tier ({current_tier})!")
            pause()
            return
        
        print(f"\n  Current: {colored(current_tier, Colors.CYAN)}")
        print(f"  Next:    {colored(info['next_tier'], Colors.GREEN)}")
        print(f"  Cost:    {format_money(info['cost'])}")
        
        # Get stats
        camp_id = player_camp.camp_id
        fighters = [f for f in self.game_state.fighters.values() if f.camp_id == camp_id]
        roster_size = len(fighters)
        reputation = getattr(player_camp, 'reputation', 50)
        championships = getattr(player_camp, 'championships_won', 0)
        
        print(f"\n  Requirements (need ONE):")
        
        rep_met = reputation >= info['reputation_needed']
        print(f"    * Rep {info['reputation_needed']}+ ", end="")
        print(colored(f"({reputation})", Colors.GREEN if rep_met else Colors.RED))
        
        champ_met = championships >= info['championships_needed']
        print(f"    * {info['championships_needed']}+ Championships ", end="")
        print(colored(f"({championships})", Colors.GREEN if champ_met else Colors.RED))
        
        roster_met = roster_size >= info['min_roster']
        print(f"    * {info['min_roster']}+ Fighters ", end="")
        print(colored(f"({roster_size})", Colors.GREEN if roster_met else Colors.RED))
        
        eligible, unmet, req = self._economy_manager.check_upgrade_eligibility(
            camp_id=player_camp.camp_id,
            current_tier=current_tier,
            reputation=reputation,
            championships=championships,
            roster_size=roster_size,
        )
        
        print()
        
        if eligible:
            if confirm(f"  Upgrade for {format_money(info['cost'])}?"):
                success, message = self._economy_manager.process_upgrade(
                    player_camp.camp_id, info['next_tier']
                )
                if success:
                    from core.types import CampTier
                    tier_map = {"LOCAL": 2, "REGIONAL": 3, "NATIONAL": 4, "ELITE": 5}
                    player_camp._tier = CampTier(tier_map.get(info['next_tier'], 2))
                    player_camp._balance = self._economy_manager.get_balance(player_camp.camp_id)
                    print(colored(f"\n  [OK] {message}", Colors.GREEN))
                else:
                    print(colored(f"\n   {message}", Colors.RED))
                pause()
        else:
            print(colored("   Requirements not met", Colors.RED))
            for u in unmet:
                print(f"    {u}")
            pause()


    def show_upcoming_events(self) -> None:
        """Show upcoming fight events"""
        while True:
            clear_screen()
            print_header("UPCOMING EVENTS")
            
            # Group fights by week
            events_by_week: Dict[int, Dict[str, List[Dict]]] = {}
            
            # Add player fights
            for fight in self.player_scheduled_fights:
                weeks = fight.get("weeks_until", 0)
                event_name = fight.get("event_name", "TBD")
                if weeks not in events_by_week:
                    events_by_week[weeks] = {}
                if event_name not in events_by_week[weeks]:
                    events_by_week[weeks][event_name] = []
                fight_copy = dict(fight)
                fight_copy["is_player_fight"] = True
                events_by_week[weeks][event_name].append(fight_copy)
            
            # Add AI fights
            for fight in self.ai_scheduled_fights:
                weeks = fight.get("weeks_until", 0)
                event_name = fight.get("event_name", "TBD")
                if weeks not in events_by_week:
                    events_by_week[weeks] = {}
                if event_name not in events_by_week[weeks]:
                    events_by_week[weeks][event_name] = []
                fight_copy = dict(fight)
                fight_copy["is_player_fight"] = False
                events_by_week[weeks][event_name].append(fight_copy)
            
            if not events_by_week:
                print("No upcoming events scheduled.")
                pause()
                return
            
            # Display events sorted by week
            sorted_weeks = sorted(events_by_week.keys())
            event_list = []
            
            for weeks in sorted_weeks[:8]:  # Show next 8 weeks max
                for event_name, fights in events_by_week[weeks].items():
                    event_list.append({
                        "weeks": weeks,
                        "name": event_name,
                        "fights": fights,
                        "fight_count": len(fights),
                    })
            
            for i, event in enumerate(event_list, 1):
                weeks = event["weeks"]
                if weeks <= 1:
                    timing = colored("THIS WEEK!", Colors.ORANGE)
                else:
                    timing = f"in {weeks} weeks"
                
                # Check for player fights
                has_player = any(f.get("is_player_fight") for f in event["fights"])
                player_marker = colored(" [*]", Colors.GOLD) if has_player else ""
                
                # Check for title fights
                has_title = any(f.get("is_title_fight") for f in event["fights"])
                title_marker = colored(" ", Colors.GOLD) if has_title else ""
                
                print(f"  [{i}] {event['name']}{player_marker}{title_marker}")
                print(f"      {event['fight_count']} fights | {timing}")
                print()
            
            print(f"  [0] Back")
            print()
            print("  [*] = Your fighter on card |  = Title fight")
            
            choice = get_input("> ")
            
            if choice == "0":
                return
            
            try:
                index = int(choice)
                if 1 <= index <= len(event_list):
                    self.show_event_card(event_list[index - 1])
            except ValueError:
                pass
    
    def show_event_card(self, event: Dict[str, Any]) -> None:
        """Show full card for an upcoming event"""
        while True:
            clear_screen()
            
            weeks = event["weeks"]
            timing = "THIS WEEK" if weeks <= 1 else f"In {weeks} weeks"
            
            print_header(event["name"])
            print(f"  {timing}")
            print()
            print_divider()
            print()
            
            fights = event["fights"]
            
            # Sort: title fights first, then by combined rating
            def fight_sort_key(f):
                is_title = 1 if f.get("is_title_fight") else 0
                f1_data = self.fighter_data.get(f.get("fighter1_id"))
                f2_data = self.fighter_data.get(f.get("fighter2_id"))
                r1 = f1_data.overall_rating if f1_data else 50
                r2 = f2_data.overall_rating if f2_data else 50
                return (is_title, r1 + r2)
            
            sorted_fights = sorted(fights, key=fight_sort_key, reverse=True)
            
            for i, fight in enumerate(sorted_fights, 1):
                f1_name = fight.get("fighter1_name", "TBD")
                f2_name = fight.get("fighter2_name", "TBD")
                wc = fight.get("weight_class", "")
                
                # Get records
                f1_data = self.fighter_data.get(fight.get("fighter1_id"))
                f2_data = self.fighter_data.get(fight.get("fighter2_id"))
                
                f1_rec = format_record(f1_data.wins, f1_data.losses) if f1_data else "0-0"
                f2_rec = format_record(f2_data.wins, f2_data.losses) if f2_data else "0-0"
                
                # Tags
                tags = []
                if fight.get("is_title_fight"):
                    tags.append(colored("[TITLE]", Colors.GOLD))
                if fight.get("is_player_fight"):
                    tags.append(colored("[YOUR FIGHT]", Colors.CYAN))
                if fight.get("is_main_event") and not fight.get("is_title_fight"):
                    tags.append(colored("[MAIN]", Colors.ORANGE))
                
                tag_str = " ".join(tags)
                if tag_str:
                    tag_str = " " + tag_str
                
                print(f"  [{i}] {f1_name} ({f1_rec}) vs {f2_name} ({f2_rec}){tag_str}")
                print(f"      {wc}")
                print()
            
            print(f"  [0] Back")
            print()
            print("  Select a fight to view fighter details")
            
            choice = get_input("> ")
            
            if choice == "0":
                return
            
            try:
                index = int(choice)
                if 1 <= index <= len(sorted_fights):
                    fight = sorted_fights[index - 1]
                    self.show_matchup_preview(fight)
            except ValueError:
                pass
    
    def show_matchup_preview(self, fight: Dict[str, Any]) -> None:
        """Show preview of a scheduled matchup"""
        clear_screen()
        
        is_title = fight.get("is_title_fight", False)
        title = "TITLE FIGHT PREVIEW" if is_title else "MATCHUP PREVIEW"
        print_header(title)
        
        f1_id = fight.get("fighter1_id")
        f2_id = fight.get("fighter2_id")
        f1_data = self.fighter_data.get(f1_id)
        f2_data = self.fighter_data.get(f2_id)
        
        if not f1_data or not f2_data:
            print("Fighter data not available.")
            pause()
            return
        
        # Fighter 1
        print(colored(f"  {f1_data.name}", Colors.BOLD))
        if f1_data.nickname:
            print(f"  \"{f1_data.nickname}\"")
        print(f"  Record: {format_record_colored(f1_data.wins, f1_data.losses)}")
        print(f"  Rating: {f1_data.overall_rating}")
        print(f"  Style: {f1_data.fighting_style}")
        if f1_data.is_champion:
            print(colored("   CHAMPION", Colors.GOLD))
        print()
        
        print("  vs")
        print()
        
        # Fighter 2
        print(colored(f"  {f2_data.name}", Colors.BOLD))
        if f2_data.nickname:
            print(f"  \"{f2_data.nickname}\"")
        print(f"  Record: {format_record_colored(f2_data.wins, f2_data.losses)}")
        print(f"  Rating: {f2_data.overall_rating}")
        print(f"  Style: {f2_data.fighting_style}")
        if f2_data.is_champion:
            print(colored("   CHAMPION", Colors.GOLD))
        print()
        
        print_divider()
        print()
        
        # Quick comparison
        print(colored("  TALE OF THE TAPE:", Colors.BOLD))
        print()
        
        def compare_stat(name: str, v1: int, v2: int):
            if v1 > v2:
                return f"  {name}: {colored(str(v1), Colors.WIN)} vs {v2}"
            elif v2 > v1:
                return f"  {name}: {v1} vs {colored(str(v2), Colors.WIN)}"
            else:
                return f"  {name}: {v1} vs {v2}"
        
        print(compare_stat("Boxing", f1_data.boxing, f2_data.boxing))
        print(compare_stat("Wrestling", f1_data.wrestling, f2_data.wrestling))
        print(compare_stat("BJJ", f1_data.bjj, f2_data.bjj))
        print(compare_stat("Cardio", f1_data.cardio, f2_data.cardio))
        print()
        
        # Prediction
        total_rating = f1_data.overall_rating + f2_data.overall_rating
        if total_rating > 0:
            f1_pct = int((f1_data.overall_rating / total_rating) * 100)
            f2_pct = 100 - f1_pct
            print(f"  Odds: {f1_data.name.split()[0]} {f1_pct}% - {f2_pct}% {f2_data.name.split()[0]}")
        
        print()
        
        options = [
            ("1", f"View {f1_data.name.split()[0]} Full Stats"),
            ("2", f"View {f2_data.name.split()[0]} Full Stats"),
            ("0", "Back"),
        ]
        print_menu(options)
        
        choice = get_choice(["1", "2", "0"])
        
        if choice == "1":
            self.show_fighter_details(f1_data)
        elif choice == "2":
            self.show_fighter_details(f2_data)
    
    def show_rankings(self) -> None:
        """Show division rankings"""
        clear_screen()
        print_header("RANKINGS")
        
        divisions = list(self.game_state.divisions.keys())
        
        for i, div in enumerate(divisions, 1):
            div_state = self.game_state.divisions.get(div)
            if div_state and div_state.champion_id:
                champ = self.game_state.fighters.get(div_state.champion_id)
                champ_name = champ.name if champ else "Unknown"
                print(f"  [{i}] {div} -  {champ_name}")
            else:
                print(f"  [{i}] {div} - VACANT")
        
        print()
        print(f"  [0] Back")
        print()
        
        choice = get_input("Select: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(divisions):
                self.show_division_rankings(divisions[index - 1])
        except ValueError:
            pass
    
    def show_division_rankings(self, division: str) -> None:
        """Show rankings for a division with full ranking data."""
        clear_screen()
        print_header(f"{division.upper()} RANKINGS")
        
        div_state = self.game_state.divisions.get(division)
        
        # Try to use real rankings system
        real_rankings = []
        champion_entry = None
        
        if RANKINGS_AVAILABLE and self._rankings_system:
            try:
                from core.types import WeightClass
                wc = WeightClass(division)
                rankings_data = self._rankings_system.get_rankings(wc)
                
                for rank, fighter_id, fighter_name in rankings_data:
                    fighter = self.game_state.fighters.get(fighter_id)
                    if fighter:
                        if rank == 0:  # Champion
                            champion_entry = fighter
                        else:
                            real_rankings.append((rank, fighter))
            except:
                pass
        
        # Champion
        if champion_entry:
            champ = champion_entry
            champ_data = self.fighter_data.get(champ.fighter_id)
            streak_str = ""
            defenses_str = ""
            
            if champ_data and champ_data.win_streak >= 2:
                streak_str = f" | W{champ_data.win_streak}"
            
            # Get title defenses if available
            if RANKINGS_AVAILABLE and self._rankings_system:
                try:
                    from core.types import WeightClass
                    wc = WeightClass(division)
                    div_obj = self._rankings_system.get_division(wc)
                    if div_obj and div_obj._champion_entry:
                        defenses = div_obj._champion_entry.title_defenses
                        if defenses > 0:
                            defenses_str = f" | {defenses} defense{'s' if defenses != 1 else ''}"
                except:
                    pass
            
            print(f"  {colored('[C] CHAMPION', Colors.GOLD)}")
            gen_star = " " if self.fighter_data.get(champ.fighter_id) and getattr(self.fighter_data[champ.fighter_id], 'is_generational', False) else ""
            print(f"      {colored(champ.name, Colors.HIGHLIGHT)}{gen_star} ({format_record_colored(champ.wins, champ.losses)}){streak_str}{defenses_str}")
            print(f"      {champ.overall_rating} OVR")
            print()
        elif div_state and div_state.champion_id:
            champ = self.game_state.fighters.get(div_state.champion_id)
            if champ:
                print(f"  {colored('[C] CHAMPION', Colors.GOLD)}")
                print(f"      {colored(champ.name, Colors.HIGHLIGHT)} ({format_record_colored(champ.wins, champ.losses)})")
                print(f"      {champ.overall_rating} OVR")
                print()
        
        print_divider()
        print(f"  {colored('TOP CONTENDERS', Colors.CYAN)}")
        print()
        
        # Use real rankings or fallback
        if real_rankings:
            for rank, f in real_rankings[:15]:
                f_data = self.fighter_data.get(f.fighter_id)
                streak_str = ""
                if f_data and f_data.win_streak >= 3:
                    streak_str = colored(f" W{f_data.win_streak}", Colors.GREEN)
                elif f_data and f_data.lose_streak >= 2:
                    streak_str = colored(f" L{f_data.lose_streak}", Colors.RED)
                
                gen_star = " " if f_data and getattr(f_data, 'is_generational', False) else ""
                print(f"  #{rank:2}  {f.name}{gen_star} ({format_record_colored(f.wins, f.losses)}) - {f.overall_rating} OVR{streak_str}")
        else:
            # Fallback
            fighters = [
                f for f in self.game_state.fighters.values()
                if f.weight_class == division and f.is_active and not f.is_champion
            ]
            fighters.sort(key=lambda f: f.overall_rating, reverse=True)
            
            for i, f in enumerate(fighters[:15], 1):
                f_data = self.fighter_data.get(f.fighter_id)
                streak_str = ""
                if f_data and f_data.win_streak >= 3:
                    streak_str = colored(f" W{f_data.win_streak}", Colors.GREEN)
                elif f_data and f_data.lose_streak >= 2:
                    streak_str = colored(f" L{f_data.lose_streak}", Colors.RED)
                
                gen_star = " " if f_data and getattr(f_data, 'is_generational', False) else ""
                print(f"  #{i:2}  {f.name}{gen_star} ({format_record_colored(f.wins, f.losses)}) - {f.overall_rating} OVR{streak_str}")
        
        print()
        
        # Show recent ranking changes
        if RANKINGS_AVAILABLE and self._rankings_system:
            try:
                from core.types import WeightClass
                wc = WeightClass(division)
                recent = self._rankings_system.get_ranking_history(weight_class=wc, limit=5)
                
                if recent:
                    print_divider()
                    print(f"  {colored('RECENT MOVEMENT', Colors.YELLOW)}")
                    print()
                    for change in recent[-5:]:
                        old = f"#{change.old_rank}" if change.old_rank else "UR"
                        new = f"#{change.new_rank}" if change.new_rank else "UR"
                        if change.new_rank == 0:
                            new = "[C]"
                        if change.old_rank == 0:
                            old = "[C]"
                        
                        if change.is_promotion:
                            arrow = colored("^", Colors.GREEN)
                        else:
                            arrow = colored("v", Colors.RED)
                        
                        print(f"    {arrow} {change.fighter_name}: {old} -> {new}")
                    print()
            except:
                pass
        
        pause()
    
    def browse_all_fighters(self) -> None:
        """Browse all fighters"""
        clear_screen()
        print_header("ALL FIGHTERS")
        
        divisions = list(self.game_state.divisions.keys())
        
        for i, wc in enumerate(divisions, 1):
            count = sum(1 for f in self.game_state.fighters.values() if f.weight_class == wc)
            print(f"  [{i}] {wc} ({count} fighters)")
        
        print()
        print(f"  [0] Back")
        print()
        
        choice = get_input("Select: ")
        
        try:
            index = int(choice)
            if index == 0:
                return
            if 1 <= index <= len(divisions):
                self.browse_division_fighters(divisions[index - 1])
        except ValueError:
            pass
    
    def browse_division_fighters(self, weight_class: str) -> None:
        """Browse fighters in a division with pagination and search."""
        all_fighters = [f for f in self.game_state.fighters.values() 
                        if f.weight_class == weight_class]
        all_fighters.sort(key=lambda f: (-int(f.is_champion), -f.overall_rating))
        
        current_fighters = all_fighters
        search_query = ""
        page = 0
        page_size = DEFAULT_PAGE_SIZE
        
        while True:
            clear_screen()
            
            total_pages = max(1, (len(current_fighters) + page_size - 1) // page_size)
            start_idx = page * page_size
            end_idx = min(start_idx + page_size, len(current_fighters))
            display_fighters = current_fighters[start_idx:end_idx]
            
            header_title = weight_class.upper()
            if search_query:
                header_title += f" (Search: '{search_query}')"
            if total_pages > 1:
                header_title += f" (Page {page + 1}/{total_pages})"
            print_header(header_title)
            
            if not display_fighters:
                if search_query:
                    print(f"  No fighters match '{search_query}'")
                else:
                    print("  No fighters in this division")
            else:
                for i, f in enumerate(display_fighters):
                    num = start_idx + i + 1
                    if f.is_champion:
                        prefix = colored("[C] C", Colors.GOLD)
                    else:
                        prefix = f"  #{num:2}"
                    print(f"  [{num:2}] {prefix}  {f.name} ({format_record_colored(f.wins, f.losses)}) - {f.overall_rating}")
            
            print()
            nav_opts = []
            if page > 0:
                nav_opts.append("[P]rev")
            if page < total_pages - 1:
                nav_opts.append("[N]ext")
            nav_opts.append("[S]earch")
            if search_query:
                nav_opts.append("[C]lear")
            nav_opts.append("[0] Back")
            print(f"  [#] View | {' | '.join(nav_opts)}")
            
            choice = get_input("> ").lower().strip()
            
            if choice == "0":
                return
            elif choice == "s":
                query = get_input("Search name: ").strip()
                if query:
                    search_query = query
                    current_fighters = search_by_name(all_fighters, query)
                    page = 0
            elif choice == "c" and search_query:
                search_query = ""
                current_fighters = all_fighters
                page = 0
            elif choice == "n" and page < total_pages - 1:
                page += 1
            elif choice == "p" and page > 0:
                page -= 1
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(current_fighters):
                        self.show_fighter_details(current_fighters[index])
                except ValueError:
                    pass


    def browse_camps(self) -> None:
        """Browse all camps"""
        clear_screen()
        print_header("TRAINING CAMPS")
        
        if not self.game_state.camps:
            print("No camps found.")
            pause()
            return
        
        tier_order = {"ELITE": 0, "NATIONAL": 1, "REGIONAL": 2, "LOCAL": 3, "GARAGE": 4}
        camps = sorted(
            self.game_state.camps.values(),
            key=lambda c: (tier_order.get(getattr(c, 'tier', 'GARAGE'), 5), -getattr(c, 'reputation', 0))
        )
        
        for i, camp in enumerate(camps[:20], 1):
            is_player = getattr(camp, 'is_player', False)
            marker = colored("[*] ", Colors.GOLD) if is_player else "  "
            tier = getattr(camp, 'tier', 'UNKNOWN')
            fighters = sum(1 for f in self.game_state.fighters.values() if f.camp_id == camp.camp_id)
            
            print(f"  [{i:2}] {marker}{camp.name}")
            print(f"       Tier: {tier} | Fighters: {fighters}")
            print()
        
        print(f"  [0] Back")
        pause()
    
    def show_news_feed(self) -> None:
        """Show news feed"""
        clear_screen()
        print_header("NEWS FEED")
        
        if not self.news_feed:
            print("No news yet.")
            pause()
            return
        
        for i, news in enumerate(self.news_feed[:20], 1):
            icons = {"fight": "", "title": "", "injury": "", "signing": "", "general": ""}
            icon = icons.get(news.category, "")
            print(f"  {icon} {news.headline}")
            if news.week > 0:
                print(f"     Week {news.week}")
            print()
        
        pause()
    
    def show_watchlist(self) -> None:
        """Show and manage the fighter watchlist."""
        if not WATCHLIST_AVAILABLE or not self._watchlist:
            print("Watchlist system not available.")
            pause()
            return
        
        while True:
            clear_screen()
            print_header("WATCHLIST")
            
            # Show summary
            count = self._watchlist.count()
            print(f"  Tracking {count} fighters")
            print()
            
            # Show entries by priority
            high_priority = self._watchlist.get_by_priority(WatchPriority.HIGH)
            if high_priority:
                print(colored("  HIGH PRIORITY:", Colors.RED))
                for entry in high_priority[:5]:
                    phase = self._get_fighter_career_phase(entry.fighter_id)
                    phase_str = f" ({phase})" if phase else ""
                    print(f"    [!!!] {entry.fighter_name} - {entry.category.value}{phase_str}")
                print()
            
            # Show by category counts
            print("  Categories:")
            for cat in WatchCategory:
                cat_entries = self._watchlist.get_by_category(cat)
                if cat_entries:
                    print(f"    {cat.value}: {len(cat_entries)}")
            
            print()
            options = [
                ("1", "View All"),
                ("2", "View by Category"),
                ("3", "Add Fighter"),
                ("4", "Remove Fighter"),
                ("5", "Change Priority"),
                ("0", "Back"),
            ]
            print_menu(options)
            
            choice = get_choice(["1", "2", "3", "4", "5", "0"])
            
            if choice == "0":
                return
            elif choice == "1":
                self._show_all_watchlist_entries()
            elif choice == "2":
                self._show_watchlist_by_category()
            elif choice == "3":
                self._add_to_watchlist()
            elif choice == "4":
                self._remove_from_watchlist()
            elif choice == "5":
                self._change_watchlist_priority()
    
    def _show_all_watchlist_entries(self) -> None:
        """Show all watchlist entries."""
        clear_screen()
        print_header("ALL WATCHED FIGHTERS")
        
        entries = self._watchlist.get_all()
        if not entries:
            print("  No fighters on watchlist.")
            pause()
            return
        
        # Sort by priority then name
        priority_order = {WatchPriority.HIGH: 0, WatchPriority.MEDIUM: 1, WatchPriority.LOW: 2, WatchPriority.NONE: 3}
        entries.sort(key=lambda e: (priority_order.get(e.priority, 3), e.fighter_name))
        
        for entry in entries:
            priority_sym = PRIORITY_SYMBOLS.get(entry.priority, "[-]")
            cat_short = entry.category.value[:4].upper()
            injured = " (INJ)" if self._is_fighter_injured(entry.fighter_id) else ""
            print(f"  {priority_sym} {entry.fighter_name} [{cat_short}]{injured}")
            if entry.record:
                print(f"      Record: {entry.record} | {entry.weight_class}")
        
        print()
        pause()
    
    def _show_watchlist_by_category(self) -> None:
        """Show watchlist filtered by category."""
        clear_screen()
        print_header("VIEW BY CATEGORY")
        
        print()
        for i, cat in enumerate(WatchCategory, 1):
            count = len(self._watchlist.get_by_category(cat))
            print(f"  [{i}] {cat.value} ({count})")
        print()
        print("  [0] Back")
        print()
        
        choice = get_input("Select: ")
        if choice == "0":
            return
        
        try:
            idx = int(choice) - 1
            categories = list(WatchCategory)
            if 0 <= idx < len(categories):
                cat = categories[idx]
                entries = self._watchlist.get_by_category(cat)
                
                clear_screen()
                print_header(f"WATCHLIST: {cat.value}")
                
                if not entries:
                    print(f"  No fighters in {cat.value} category.")
                else:
                    for entry in entries:
                        priority_sym = PRIORITY_SYMBOLS.get(entry.priority, "[-]")
                        print(f"  {priority_sym} {entry.fighter_name}")
                        if entry.record:
                            print(f"      {entry.weight_class} | {entry.record}")
                
                print()
                pause()
        except (ValueError, IndexError):
            pass
    
    def _add_to_watchlist(self) -> None:
        """Add a fighter to the watchlist."""
        clear_screen()
        print_header("ADD TO WATCHLIST")
        
        # Search for fighter
        search = get_input("Enter fighter name (partial ok): ")
        if not search:
            return
        
        matches = []
        for fid, rec in self.game_state.fighters.items():
            if search.lower() in rec.name.lower():
                matches.append(rec)
        
        if not matches:
            print("No fighters found.")
            pause()
            return
        
        print()
        for i, fighter in enumerate(matches[:10], 1):
            already = " (already watching)" if self._watchlist.contains(fighter.fighter_id) else ""
            print(f"  [{i}] {fighter.name}{already}")
        
        print()
        idx = get_input("Select fighter (number): ")
        try:
            fighter = matches[int(idx) - 1]
        except (ValueError, IndexError):
            return
        
        if self._watchlist.contains(fighter.fighter_id):
            print(f"{fighter.name} is already on your watchlist.")
            pause()
            return
        
        # Select category
        print()
        print("Category:")
        for i, cat in enumerate(WatchCategory, 1):
            print(f"  [{i}] {cat.value}")
        print()
        
        cat_idx = get_input("Select category: ")
        try:
            category = list(WatchCategory)[int(cat_idx) - 1]
        except (ValueError, IndexError):
            category = WatchCategory.SCOUT
        
        # Get full data for info
        full_data = self.fighter_data.get(fighter.fighter_id)
        
        success, msg = self._watchlist.add(
            fighter.fighter_id,
            fighter.name,
            category,
            weight_class=getattr(fighter, 'weight_class', ''),
            record=f"{fighter.wins}-{fighter.losses}",
            age=full_data.age if full_data else 0,
        )
        
        print()
        print(msg)
        pause()
    
    def _remove_from_watchlist(self) -> None:
        """Remove a fighter from the watchlist."""
        entries = self._watchlist.get_all()
        if not entries:
            print("Watchlist is empty.")
            pause()
            return
        
        clear_screen()
        print_header("REMOVE FROM WATCHLIST")
        
        for i, entry in enumerate(entries[:15], 1):
            print(f"  [{i}] {entry.fighter_name}")
        
        print()
        print("  [0] Cancel")
        print()
        
        idx = get_input("Select fighter to remove: ")
        if idx == "0":
            return
        
        try:
            entry = entries[int(idx) - 1]
            success, msg = self._watchlist.remove(entry.fighter_id)
            print()
            print(msg)
            pause()
        except (ValueError, IndexError):
            pass
    
    def _change_watchlist_priority(self) -> None:
        """Change priority of a watched fighter."""
        entries = self._watchlist.get_all()
        if not entries:
            print("Watchlist is empty.")
            pause()
            return
        
        clear_screen()
        print_header("CHANGE PRIORITY")
        
        for i, entry in enumerate(entries[:15], 1):
            priority_sym = PRIORITY_SYMBOLS.get(entry.priority, "[-]")
            print(f"  [{i}] {priority_sym} {entry.fighter_name}")
        
        print()
        idx = get_input("Select fighter: ")
        try:
            entry = entries[int(idx) - 1]
        except (ValueError, IndexError):
            return
        
        print()
        print(f"Current priority: {entry.priority.value}")
        print()
        print("  [1] HIGH (!!!)")
        print("  [2] MEDIUM (!!)")
        print("  [3] LOW (!)")
        print("  [4] NONE (-)")
        print()
        
        pri_choice = get_input("New priority: ")
        priorities = {
            "1": WatchPriority.HIGH,
            "2": WatchPriority.MEDIUM,
            "3": WatchPriority.LOW,
            "4": WatchPriority.NONE,
        }
        
        new_priority = priorities.get(pri_choice)
        if new_priority:
            success, msg = self._watchlist.update_priority(entry.fighter_id, new_priority)
            print()
            print(msg)
        pause()
    
    def save_game_menu(self) -> None:
        """Save game"""
        clear_screen()
        print_header("SAVE GAME")
        
        saves = list_saves()
        
        for i in range(1, 6):
            slot = f"slot_{i}"
            existing = next((s for s in saves if s.slot_name == slot), None)
            if existing:
                print(f"  [{i}] {existing.game_name} - Week {existing.week_number}")
            else:
                print(f"  [{i}] Empty")
        
        print()
        print(f"  [Q] Quick Save")
        print(f"  [0] Cancel")
        print()
        
        choice = get_input("Select: ").lower()
        
        if choice == "0":
            return
        elif choice == "q":
            result = quicksave(self.game_state)
            if result.success:
                self._save_extended_data("quicksave")
                print("Quick saved!")
            else:
                print(f"Failed: {result.message}")
            pause()
            return
        
        try:
            index = int(choice)
            if 1 <= index <= 5:
                slot = f"slot_{index}"
                if save_exists(slot) and not confirm("Overwrite?"):
                    return
                result = save_game(self.game_state, slot)
                if result.success:
                    self._save_extended_data(slot)
                    print("Saved!")
                else:
                    print(f"Failed: {result.message}")
                pause()
        except ValueError:
            pass
    
    def quit_to_menu(self) -> None:
        """Quit to main menu"""
        if confirm("Save before quitting?"):
            self.save_game_menu()
        
        if confirm("Quit to main menu?"):
            self.game_state = None
            self.in_game = False
            self.fighter_data = {}
            self._training_system = None
            self._matchmaking_engine = None
            self._world_simulation = None
            self._fight_simulator_available = False
            self.fight_offers = []
            self.player_scheduled_fights = []
            self.completed_events = []
            self.all_fight_results = {}
            self.news_feed = []


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Main entry point"""
    cli = CLI()
    
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\n\nThanks for playing Cage Dynasty!")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()


__all__ = [
    "CLI", "main", "FighterFullData", "FightResult", "CompletedEvent",
    "NewsItem", "FightOffer", "Colors", "colored",
]
