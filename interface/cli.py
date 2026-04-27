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
import time
import select

# Core imports
from core.game_state import GameState, GamePhase, GameMode, FighterRecord
from core.persistence import (
    save_game, load_game, quicksave, quickload, autosave,
    list_saves, save_exists, get_available_slots, SaveMetadata,
)
from core.events import emit, subscribe
from core.config import get_config

# CLI Data Classes (shared definitions)
CLI_DATA_AVAILABLE = False
try:
    from cli_data import (
        FighterFullData as CLIDataFighterFullData,
        FightResult as CLIDataFightResult,
        CompletedEvent as CLIDataCompletedEvent,
        NewsItem as CLIDataNewsItem,
        FightOffer as CLIDataFightOffer,
    )
    CLI_DATA_AVAILABLE = True
except ImportError:
    pass  # Will use local definitions

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

# Social Media Reactions System
MEDIA_AVAILABLE = False
try:
    from narrative.media import (
        generate_fight_reactions,
        get_random_commentators,
    )
    MEDIA_AVAILABLE = True
except ImportError:
    MEDIA_AVAILABLE = False

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

# Popularity System
POPULARITY_AVAILABLE = False
try:
    from popularity import (
        calculate_popularity_change,
        apply_popularity_decay,
        calculate_star_power,
        is_main_event_worthy,
        POPULARITY_WIN,
        POPULARITY_FINISH_BONUS,
        POPULARITY_TITLE_WIN,
        POPULARITY_TITLE_DEFENSE,
        POPULARITY_LOSS,
    )
    POPULARITY_AVAILABLE = True
except ImportError:
    # Fallback - define inline if module not available
    POPULARITY_AVAILABLE = False
    def calculate_popularity_change(won, method, was_title_fight=False, was_title_defense=False, 
                                     win_streak=0, loss_streak=0, current_popularity=10):
        """Fallback popularity calculation"""
        if won:
            change = 3
            if method in ("KO", "TKO", "SUB"):
                change += 4
            if was_title_fight:
                change += 10 if not was_title_defense else 6
            if win_streak > 3:
                change += 2
        else:
            change = -2
            if loss_streak > 2:
                change -= (loss_streak - 2) * 2
        return change

# Game Start System (New Game Flow)
GAME_START_AVAILABLE = False
GameStartManager = None
try:
    from systems.game_start import (
        GameStartManager,
        StartingProspect,
        generate_starting_prospects,
        WEIGHT_CLASSES as START_WEIGHT_CLASSES,
        REGIONS as START_REGIONS,
    )
    GAME_START_AVAILABLE = True
except ImportError:
    try:
        from game_start import (
            GameStartManager,
            StartingProspect,
            generate_starting_prospects,
            WEIGHT_CLASSES as START_WEIGHT_CLASSES,
            REGIONS as START_REGIONS,
        )
        GAME_START_AVAILABLE = True
    except ImportError:
        pass

# Amateur Circuit System
AMATEUR_AVAILABLE = False
AmateurSystem = None
try:
    from systems.amateur import (
        AmateurSystem,
        AmateurFighter,
        Tournament,
        TournamentResults,
        REGIONS as AMATEUR_REGIONS,
        WEIGHT_CLASSES as AMATEUR_WEIGHT_CLASSES,
    )
    AMATEUR_AVAILABLE = True
except ImportError:
    try:
        from amateur import (
            AmateurSystem,
            AmateurFighter,
            Tournament,
            TournamentResults,
            REGIONS as AMATEUR_REGIONS,
            WEIGHT_CLASSES as AMATEUR_WEIGHT_CLASSES,
        )
        AMATEUR_AVAILABLE = True
    except ImportError:
        pass

# Interview System
INTERVIEW_AVAILABLE = False
InterviewManager = None
WinnerResponse = None
LoserResponse = None
try:
    from systems.interviews import (
        InterviewManager,
        WinnerResponse,
        LoserResponse,
        create_interview_manager,
        WINNER_TEMPLATES,
        LOSER_TEMPLATES,
    )
    INTERVIEW_AVAILABLE = True
except ImportError:
    try:
        from interviews import (
            InterviewManager,
            WinnerResponse,
            LoserResponse,
            create_interview_manager,
            WINNER_TEMPLATES,
            LOSER_TEMPLATES,
        )
        INTERVIEW_AVAILABLE = True
    except ImportError:
        pass

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
        # Try flat module structure with core.types
        from fight_engine import FighterAttributes as FightEngineAttributes, FightConfig
        from fight_integration import NarratedFightSimulator, NarratedFightResult, simulate_narrated_fight
        from core.types import FightingStyle as FightingStyleEnum
        FIGHT_ENGINE_AVAILABLE = True
    except ImportError:
        try:
            # Try flat module structure with types.py directly
            from fight_engine import FighterAttributes as FightEngineAttributes, FightConfig
            from fight_integration import NarratedFightSimulator, NarratedFightResult, simulate_narrated_fight
            from types import FightingStyle as FightingStyleEnum
            FIGHT_ENGINE_AVAILABLE = True
        except ImportError:
            try:
                # Final fallback: fight engine without FightingStyle enum
                from fight_engine import FighterAttributes as FightEngineAttributes, FightConfig
                from fight_integration import NarratedFightSimulator, NarratedFightResult, simulate_narrated_fight
                # Create a dummy FightingStyle enum if types import fails
                from enum import Enum
                class FightingStyleEnum(Enum):
                    BALANCED = "balanced"
                    STRIKER = "striker"
                    COUNTER_STRIKER = "counter_striker"
                    PRESSURE_FIGHTER = "pressure_fighter"
                    POINT_FIGHTER = "point_fighter"
                    MUAY_THAI = "muay_thai"
                    WRESTLER = "wrestler"
                    GROUND_AND_POUND = "ground_and_pound"
                    BJJ_SPECIALIST = "bjj_specialist"
                    CLINCH_FIGHTER = "clinch_fighter"
                    SPRAWL_AND_BRAWL = "sprawl_and_brawl"
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
    try:
        from coaches import (
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

# Division Ladder System (Challenge-based matchmaking)
LADDER_AVAILABLE = False
DivisionLadder = None
try:
    from systems.division_ladder import (
        DivisionLadder,
        LadderEntry,
        ChallengeOption,
        ChallengeResult,
        IncomingChallenge,
        DeclineConsequence,
        FighterStatus,
        ChallengeOutcome,
        get_path_to_title,
        get_threat_assessment,
    )
    LADDER_AVAILABLE = True
except ImportError:
    try:
        from division_ladder import (
            DivisionLadder,
            LadderEntry,
            ChallengeOption,
            ChallengeResult,
            IncomingChallenge,
            DeclineConsequence,
            FighterStatus,
            ChallengeOutcome,
            get_path_to_title,
            get_threat_assessment,
        )
        LADDER_AVAILABLE = True
    except ImportError:
        pass

# Inbox System (Centralized notifications)
INBOX_AVAILABLE = False
InboxSystem = None
try:
    from systems.inbox import (
        InboxSystem,
        NotificationType,
        NotificationPriority,
        Notification,
        FightOfferData,
        ScoutReportData,
        NOTIFICATION_ICONS,
        PRIORITY_COLORS,
        generate_scout_report_for_coach,
    )
    INBOX_AVAILABLE = True
except ImportError:
    try:
        from inbox import (
            InboxSystem,
            NotificationType,
            NotificationPriority,
            Notification,
            FightOfferData,
            ScoutReportData,
            NOTIFICATION_ICONS,
            PRIORITY_COLORS,
            generate_scout_report_for_coach,
        )
        INBOX_AVAILABLE = True
    except ImportError:
        pass

# ============================================================================
# CONSTANTS
# ============================================================================

TERMINAL_WIDTH = 70

# Title Fight Requirements
TITLE_MIN_PRO_FIGHTS = 3  # Minimum fights to challenge for title
TITLE_MAX_CHALLENGER_RANK = 5  # Must be ranked #1-5 to get title shot

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
    """Complete fighter data with all attributes (17 total)"""
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
    
    # Physical Attributes (5)
    strength: int = 50      # Power behind strikes, clinch control
    speed: int = 50         # Hand speed, movement, reaction time
    cardio: int = 50        # Stamina, gas tank
    chin: int = 50          # Ability to absorb damage
    recovery: int = 50      # Between-round recovery, shaking off being hurt
    
    # Striking Attributes (4)
    boxing: int = 50            # Punching technique, combinations
    kicks: int = 50             # Kicking technique (head, body, leg)
    clinch_striking: int = 50   # Knees, elbows, dirty boxing
    striking_defense: int = 50  # Head movement, blocking, footwork
    
    # Grappling Attributes (5)
    takedowns: int = 50         # Ability to bring fight to ground (was wrestling)
    takedown_defense: int = 50  # Sprawl, cage wrestling defense
    top_control: int = 50       # Holding position, GnP, preventing sweeps
    submissions: int = 50       # Finishing ability - chokes/locks (was bjj)
    guard: int = 50             # Sweeps, guard retention, getting back up
    
    # Mental Attributes (3)
    heart: int = 50         # Willingness to fight through adversity
    fight_iq: int = 50      # In-fight adjustments, strategy
    composure: int = 50     # Performance under pressure
    
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
    
    # Training tracking (for hub display)
    last_camp_gains: Dict[str, int] = field(default_factory=dict)  # Gains from last completed camp
    last_camp_total: int = 0  # Total points gained in last camp
    last_camp_week: int = 0   # Week when last camp ended (for "recent" check)
    maintenance_gains: Dict[str, int] = field(default_factory=dict)  # Ongoing maintenance gains
    maintenance_week: int = 0  # Week of last maintenance gain
    
    # Condition tracking
    fatigue: int = 0  # Training fatigue (0-100)
    lost_last_fight: bool = False  # For motivation/comeback mechanics
    
    # Potential (for development tracking)
    potential_ceiling: int = 75
    
    # Ranking
    ranking: Optional[int] = None
    
    # Popularity (affects card position, sponsorships, fight offers)
    popularity: int = 10  # 0-100, star power / drawing ability
    
    # Traits (special abilities/characteristics)
    traits: List[str] = field(default_factory=list)
    
    # Fight history (list of past fights with event names, opponents, results)
    fight_history: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def overall_rating(self) -> int:
        """Calculate overall rating from attributes"""
        # Striking: boxing weighted highest
        striking = (self.boxing * 2 + self.kicks + self.clinch_striking + self.striking_defense) // 5
        # Grappling: takedowns and submissions weighted, top/guard/td_def supporting
        grappling = (self.takedowns * 2 + self.submissions * 2 + self.top_control + self.guard + self.takedown_defense) // 7
        # Physical: all contribute
        physical = (self.strength + self.speed + self.cardio + self.chin + self.recovery) // 5
        # Mental: heart weighted highest
        mental = (self.heart * 2 + self.fight_iq + self.composure) // 4
        # Final: balanced across categories
        return (striking + grappling + physical + mental) // 4
    
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
            # Physical (5)
            "strength": self.strength,
            "speed": self.speed,
            "cardio": self.cardio,
            "chin": self.chin,
            "recovery": self.recovery,
            # Striking (4)
            "boxing": self.boxing,
            "kicks": self.kicks,
            "clinch_striking": self.clinch_striking,
            "striking_defense": self.striking_defense,
            # Grappling (5)
            "takedowns": self.takedowns,
            "takedown_defense": self.takedown_defense,
            "top_control": self.top_control,
            "submissions": self.submissions,
            "guard": self.guard,
            # Mental (3)
            "heart": self.heart,
            "fight_iq": self.fight_iq,
            "composure": self.composure,
            # Record
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
            "last_camp_gains": self.last_camp_gains.copy() if self.last_camp_gains else {},
            "last_camp_total": self.last_camp_total,
            "last_camp_week": self.last_camp_week,
            "maintenance_gains": self.maintenance_gains.copy() if self.maintenance_gains else {},
            "maintenance_week": self.maintenance_week,
            "traits": self.traits,
            "popularity": self.popularity,
            "fight_history": self.fight_history.copy() if self.fight_history else [],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FighterFullData":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_fight_attributes(self) -> Optional[Any]:
        """Convert to FighterAttributes for fight engine.
        
        Returns None if fight engine not available.
        Uses new 17-attribute system directly.
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
                "Orthodox Boxer": FightingStyleEnum.STRIKER,
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
                "Submission Artist": FightingStyleEnum.BJJ_SPECIALIST,
                "Submission Grappler": FightingStyleEnum.BJJ_SPECIALIST,
                "Clinch Fighter": FightingStyleEnum.CLINCH_FIGHTER,
                "Sprawl and Brawl": FightingStyleEnum.SPRAWL_AND_BRAWL,
                "Sprawl & Brawl": FightingStyleEnum.SPRAWL_AND_BRAWL,
                "Sambo": FightingStyleEnum.WRESTLER,
                "Karate": FightingStyleEnum.STRIKER,
                "Brawler": FightingStyleEnum.PRESSURE_FIGHTER,
            }
            style_enum = style_mapping.get(self.fighting_style, FightingStyleEnum.BALANCED)
        
        # Pass all 17 attributes directly to fight engine
        return FightEngineAttributes(
            fighter_id=self.fighter_id,
            name=self.name,
            # Physical (5)
            strength=self.strength,
            speed=self.speed,
            cardio=self.cardio,
            chin=self.chin,
            recovery=self.recovery,
            # Striking (4)
            boxing=self.boxing,
            kicks=self.kicks,
            clinch_striking=self.clinch_striking,
            striking_defense=self.striking_defense,
            # Grappling (5)
            takedowns=self.takedowns,
            takedown_defense=self.takedown_defense,
            top_control=self.top_control,
            submissions=self.submissions,
            guard=self.guard,
            # Mental (3)
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
    card_slot: str = ""  # main_event, co_main, main_card, prelim, early_prelim
    
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
    full_commentary: Any = ""  # Can be str or List[str]
    fight_narrative: str = ""
    round_summaries: List[Any] = field(default_factory=list)  # Can be List[str] or List[Dict]
    
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
# NOTE: FighterFullData, FightResult, CompletedEvent, NewsItem, FightOffer
# are defined above. cli_data.py has matching definitions.
# For now, cli.py uses its own definitions for full compatibility.
# Future refactor: remove local definitions and import from cli_data.py
# ============================================================================


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
        
        # Chemistry tracking (coach_id:fighter_id -> chemistry score)
        self._chemistry_scores: Dict[str, int] = {}
        
        # Sparring quality cache (recalculated weekly)
        self._sparring_bonus: float = 0.0
        self._sparring_description: str = ""
        
        # Maintenance training system
        self._maintenance_system = None
        
        # Amateur circuit system
        self._amateur_system = None
        
        # Interview system
        self._interview_manager = None
        
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
        self._game_start_manager = None  # For new game prospect drafting

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
        
        # Division Ladder system (challenge-based matchmaking)
        self._division_ladder = None
        if LADDER_AVAILABLE:
            try:
                self._division_ladder = DivisionLadder()
            except:
                pass
        
        # Inbox system (centralized notifications)
        self._inbox = None
        if INBOX_AVAILABLE:
            try:
                self._inbox = InboxSystem()
            except:
                pass
        
        # Belt history tracking (championship lineage)
        self._belt_history = None
        
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

        # Initialize maintenance training system
        try:
            from systems.maintenance_training import MaintenanceTrainingSystem
            self._maintenance_system = MaintenanceTrainingSystem()
        except ImportError:
            self._maintenance_system = None

        # Initialize amateur circuit system
        if AMATEUR_AVAILABLE and AmateurSystem:
            try:
                self._amateur_system = AmateurSystem()
                self._amateur_system.initialize_pools()
            except Exception:
                self._amateur_system = None

        # Initialize interview system
        if INTERVIEW_AVAILABLE:
            try:
                self._interview_manager = create_interview_manager()
            except Exception:
                self._interview_manager = None

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
    
    def _sync_champion_flags(self) -> None:
        """Sync fighter.is_champion flags with division state (source of truth).
        
        This fixes any inconsistency where a fighter's is_champion flag doesn't
        match the actual division champion_id.
        """
        if not self.game_state:
            return
        
        # Build set of actual champions from division state
        actual_champions = set()
        for weight_class, div_state in self.game_state.divisions.items():
            if div_state and div_state.champion_id:
                actual_champions.add(div_state.champion_id)
        
        # Sync all fighters
        fixed_count = 0
        for fighter_id, fighter in self.game_state.fighters.items():
            should_be_champ = fighter_id in actual_champions
            if getattr(fighter, 'is_champion', False) != should_be_champ:
                fighter.is_champion = should_be_champ
                fixed_count += 1
                
                # Also sync fighter_data if present
                if fighter_id in self.fighter_data:
                    self.fighter_data[fighter_id].is_champion = should_be_champ
        
        if fixed_count > 0:
            print(f"Synced {fixed_count} champion flag(s)")
    
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
    
    def _calculate_camp_sparring_bonus(self, camp_id: str) -> Tuple[float, str]:
        """
        Calculate sparring bonus for camp based on roster composition.
        
        Boosts ALL camp fighters' training.
        
        Returns:
            Tuple of (bonus_multiplier, description)
        """
        try:
            from systems.training import calculate_sparring_bonus
        except ImportError:
            return 0.0, "Sparring system unavailable"
        
        # Get all fighters in this camp
        camp_fighters = []
        for fid, fdata in self.fighter_data.items():
            if fdata.camp_id == camp_id:
                camp_fighters.append({
                    "overall": fdata.overall_rating,
                    "fighting_style": fdata.fighting_style,
                })
        
        if len(camp_fighters) < 2:
            return 0.0, "Need 2+ fighters for sparring"
        
        # Check for Iron Sharpener coach trait
        has_iron_sharpener = False
        if COACHES_AVAILABLE and self._coach_system:
            try:
                coaches = self._coach_system.get_camp_coaches(camp_id)
                for coach in coaches:
                    coach_traits = getattr(coach, 'traits', [])
                    trait_names = [t.value if hasattr(t, 'value') else str(t) for t in coach_traits]
                    if "Iron Sharpener" in trait_names:
                        has_iron_sharpener = True
                        break
            except:
                pass
        
        bonus, description = calculate_sparring_bonus(camp_fighters, has_iron_sharpener)
        
        # Cache for display
        self._sparring_bonus = bonus
        self._sparring_description = description
        
        return bonus, description
    
    def _get_chemistry(self, coach_id: str, fighter_id: str, fighter_traits: List[str], fighter_age: int) -> int:
        """
        Get chemistry score between coach and fighter.
        
        Calculates initial chemistry if not cached, otherwise returns cached value.
        Chemistry changes over time based on fight outcomes and events.
        """
        key = f"{coach_id}:{fighter_id}"
        
        if key in self._chemistry_scores:
            return self._chemistry_scores[key]
        
        # Calculate initial chemistry
        if COACHES_AVAILABLE and self._coach_system:
            try:
                from systems.coaches import calculate_chemistry
                coach = self._coach_system._coaches.get(coach_id)
                if coach:
                    chemistry = calculate_chemistry(coach, fighter_traits, fighter_age)
                    self._chemistry_scores[key] = chemistry
                    return chemistry
            except:
                pass
        
        # Default neutral chemistry
        self._chemistry_scores[key] = 50
        return 50
    
    def _update_chemistry_on_fight(self, coach_id: str, fighter_id: str, won: bool) -> None:
        """Update chemistry after a fight result."""
        key = f"{coach_id}:{fighter_id}"
        current = self._chemistry_scores.get(key, 50)
        
        if won:
            # Win boosts chemistry (cap at 90)
            new_chem = min(90, current + 5)
        else:
            # Loss drops chemistry
            new_chem = max(20, current - 5)
        
        self._chemistry_scores[key] = new_chem
    
    def _update_chemistry_monthly(self) -> None:
        """Monthly chemistry increase for time spent together (cap at 80)."""
        for key in self._chemistry_scores:
            current = self._chemistry_scores[key]
            if current < 80:
                self._chemistry_scores[key] = current + 1
    
    def _get_head_coach_info(self, camp_id: str) -> Dict[str, Any]:
        """
        Get head coach information for a camp.
        
        Returns dict with: coach_id, name, specialty, quality, traits
        """
        default_info = {
            "coach_id": "",
            "name": "None",
            "specialty": None,
            "quality": 3,
            "traits": [],
        }
        
        if not COACHES_AVAILABLE or not self._coach_system:
            return default_info
        
        try:
            coaches = self._coach_system.get_camp_coaches(camp_id)
            head_coach = None
            
            for coach in coaches:
                if getattr(coach, 'is_head_coach', False):
                    head_coach = coach
                    break
            
            # Fallback to first coach
            if not head_coach and coaches:
                head_coach = coaches[0]
            
            if head_coach:
                # Handle different coach types (Coach vs StartingCoach)
                trait_names = []
                traits = getattr(head_coach, 'traits', [])
                for t in traits:
                    trait_names.append(t.value if hasattr(t, 'value') else str(t))
                
                # Get specialty (could be string or enum)
                specialty = getattr(head_coach, 'specialty', None)
                if specialty:
                    specialty = specialty.value if hasattr(specialty, 'value') else str(specialty)
                
                # Get quality (default to 3, or derive from skill_level if StartingCoach)
                quality = getattr(head_coach, 'quality', None)
                if quality is None:
                    skill_level = getattr(head_coach, 'skill_level', 60)
                    quality = min(5, max(1, skill_level // 20))
                
                return {
                    "coach_id": getattr(head_coach, 'coach_id', ''),
                    "name": getattr(head_coach, 'name', 'Coach'),
                    "specialty": specialty,
                    "quality": quality,
                    "traits": trait_names,
                }
        except Exception:
            pass
        
        return default_info
    
    def _get_weeks_until_fight(self, fighter_id: str) -> int:
        """Get weeks until fighter's scheduled fight, or 99 if none scheduled."""
        # Check player scheduled fights
        for fight in self.player_scheduled_fights:
            if fight.get('fighter_id') == fighter_id or fight.get('fighter1_id') == fighter_id:
                fight_week = fight.get('week', 99)
                current_week = self.game_state.week_number if self.game_state else 0
                return max(0, fight_week - current_week)
        
        return 99

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
        
        # Get heat level from rivalry system
        heat_level = self._get_heat_level(scheduled_fight.fighter1_id, scheduled_fight.fighter2_id)
        
        return self._simple_fight_simulation(
            scheduled_fight.fighter1_id, scheduled_fight.fighter2_id,
            f1.name, f2.name, f1_rating, f2_rating,
            scheduled_fight.rounds,
            is_title_fight=is_title,
            is_main_event=is_main,
            heat_level=heat_level
        )
    
    def _get_heat_level(self, fighter1_id: str, fighter2_id: str) -> int:
        """Get the heat level between two fighters from rivalry system.
        
        Returns:
            Heat level 0-100 (0 if no rivalry or system unavailable)
        """
        if not RIVALRY_AVAILABLE or not self._rivalry_system:
            return 0
        
        try:
            rivalry = self._rivalry_system.get_rivalry(fighter1_id, fighter2_id)
            if rivalry and rivalry.is_active:
                return rivalry.score
        except Exception:
            pass
        
        return 0
    
    def _fighter_has_sponsors(self, fighter_id: str) -> bool:
        """Check if a fighter has any active sponsors."""
        fighter_data = self.fighter_data.get(fighter_id)
        if not fighter_data:
            return False
        
        # Check for sponsorships attribute
        sponsorships = getattr(fighter_data, 'sponsorships', [])
        if sponsorships:
            return any(s.is_active for s in sponsorships if hasattr(s, 'is_active'))
        
        # Check in game_state
        fighter = self.game_state.fighters.get(fighter_id)
        if fighter:
            fighter_sponsorships = getattr(fighter, 'sponsorships', [])
            if fighter_sponsorships:
                return len(fighter_sponsorships) > 0
        
        return False
    
    def _get_fighter_sponsor_names(self, fighter_id: str) -> str:
        """Get comma-separated list of fighter's sponsor names."""
        sponsors = []
        
        fighter_data = self.fighter_data.get(fighter_id)
        if fighter_data:
            sponsorships = getattr(fighter_data, 'sponsorships', [])
            for s in sponsorships:
                if hasattr(s, 'company_name') and hasattr(s, 'is_active'):
                    if s.is_active:
                        sponsors.append(s.company_name)
                elif hasattr(s, 'company_name'):
                    sponsors.append(s.company_name)
        
        if not sponsors:
            # Check game_state
            fighter = self.game_state.fighters.get(fighter_id)
            if fighter:
                fighter_sponsorships = getattr(fighter, 'sponsorships', [])
                for s in fighter_sponsorships:
                    if isinstance(s, dict):
                        sponsors.append(s.get('company_name', 'Sponsor'))
                    elif hasattr(s, 'company_name'):
                        sponsors.append(s.company_name)
        
        if not sponsors:
            return "my sponsors"
        elif len(sponsors) == 1:
            return sponsors[0]
        elif len(sponsors) == 2:
            return f"{sponsors[0]} and {sponsors[1]}"
        else:
            return ", ".join(sponsors[:-1]) + f", and {sponsors[-1]}"
    
    def _get_sponsor_bonus(self, fighter_id: str) -> int:
        """Calculate sponsor bonus for thanking them in interview.
        
        Returns 15-25% of total fight payment from sponsors.
        """
        total_bonus = 0
        
        fighter_data = self.fighter_data.get(fighter_id)
        if fighter_data:
            sponsorships = getattr(fighter_data, 'sponsorships', [])
            for s in sponsorships:
                if hasattr(s, 'payment_per_fight') and hasattr(s, 'is_active'):
                    if s.is_active:
                        # 20% bonus for thanking
                        total_bonus += int(s.payment_per_fight * 0.20)
                elif hasattr(s, 'payment_per_fight'):
                    total_bonus += int(s.payment_per_fight * 0.20)
        
        # Minimum bonus if they have sponsors
        if total_bonus == 0 and self._fighter_has_sponsors(fighter_id):
            total_bonus = 500  # Minimum $500 bonus
        
        return total_bonus
    
    def _simple_fight_simulation(
        self, f1_id: str, f2_id: str, f1_name: str, f2_name: str,
        f1_rating: int, f2_rating: int, rounds: int,
        is_title_fight: bool = False, is_main_event: bool = False,
        f1_gameplan: Optional[Dict] = None, f2_gameplan: Optional[Dict] = None,
        heat_level: int = 0
    ) -> Dict[str, Any]:
        """Simple rating-based fight simulation with trait and gameplan effects.
        
        Uses systems.traits module for modifier calculations.
        Gameplans affect fighting style bonuses.
        Heat level affects finish rate and fight intensity.
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
        
        # Calculate heat modifiers
        # Heat increases finish rate and adds variance (emotional fighting)
        heat_finish_bonus = 0.0
        heat_variance = 0
        if heat_level > 80:  # WAR
            heat_finish_bonus = 0.20
            heat_variance = 8
        elif heat_level > 60:  # HEATED
            heat_finish_bonus = 0.15
            heat_variance = 6
        elif heat_level > 40:  # BAD BLOOD
            heat_finish_bonus = 0.10
            heat_variance = 4
        elif heat_level > 20:  # TENSION
            heat_finish_bonus = 0.05
            heat_variance = 2
        
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
            if winner_data.submissions >= 70:
                method_weights["SUB"] += 0.15
            if winner_data.takedowns >= 70 and winner_data.submissions < 60:
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
        
        # Apply heat level bonus (rivalry fights are more likely to end in finishes)
        if heat_finish_bonus > 0:
            method_weights["KO"] += heat_finish_bonus * 0.4
            method_weights["TKO"] += heat_finish_bonus * 0.4
            method_weights["SUB"] += heat_finish_bonus * 0.2
        
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
            "heat_level": heat_level,
        }
    
    def _narrated_fight_simulation(
        self, f1_id: str, f2_id: str, rounds: int,
        is_title_fight: bool = False, is_main_event: bool = False,
        heat_level: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Full fight simulation with round-by-round commentary.
        
        Uses the sophisticated fight engine for detailed simulation.
        Returns None if fight engine not available or fighters not found.
        
        Note: heat_level stored for compatibility but NarratedFightSimulator
        does not yet apply heat modifiers internally.
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
        # TODO: Pass heat_level to NarratedFightSimulator when it supports it
        try:
            simulator = NarratedFightSimulator(f1_attrs, f2_attrs, config, verbose=False)
            result = simulator.simulate()
        except Exception:
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
            "key_moments": [f"R{m.get('round', '?')}: {m.get('commentary', '')}" for m in result.key_moments if m.get("commentary")],
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
            
            # Map generator attributes (old names) to FighterFullData (new names)
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
                # Physical (5)
                strength=gen.strength,
                speed=gen.speed,
                cardio=gen.cardio,
                chin=gen.chin,
                recovery=gen.recovery,
                # Striking (4)
                boxing=gen.boxing,
                kicks=gen.kicks,
                clinch_striking=gen.clinch_striking,
                striking_defense=gen.striking_defense,
                # Grappling (5)
                takedowns=gen.takedowns,
                takedown_defense=gen.takedown_defense,
                top_control=gen.top_control,
                submissions=gen.submissions,
                guard=gen.guard,
                # Mental (3)
                heart=gen.heart,
                fight_iq=gen.fight_iq,
                composure=gen.composure,
                # Record
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
                # Physical (5)
                strength=max(1, min(100, base + random.randint(-variance, variance))),
                speed=max(1, min(100, base + random.randint(-variance, variance))),
                cardio=max(1, min(100, base + random.randint(-variance, variance))),
                chin=max(1, min(100, base + random.randint(-variance, variance))),
                recovery=max(1, min(100, base + random.randint(-variance, variance))),
                # Striking (4)
                boxing=max(1, min(100, base + random.randint(-variance, variance))),
                kicks=max(1, min(100, base + random.randint(-variance, variance))),
                clinch_striking=max(1, min(100, base + random.randint(-variance, variance) - 5)),
                striking_defense=max(1, min(100, base + random.randint(-variance, variance))),
                # Grappling (5)
                takedowns=max(1, min(100, base + random.randint(-variance, variance))),
                takedown_defense=max(1, min(100, base + random.randint(-variance, variance))),
                top_control=max(1, min(100, base + random.randint(-variance, variance))),
                submissions=max(1, min(100, base + random.randint(-variance, variance))),
                guard=max(1, min(100, base + random.randint(-variance, variance))),
                # Mental (3)
                heart=max(1, min(100, base + random.randint(-variance, variance))),
                fight_iq=max(1, min(100, base + random.randint(-variance, variance))),
                composure=max(1, min(100, base + random.randint(-variance, variance))),
                # Record
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
        
        # Load popularity from basic record if available
        if hasattr(basic, 'popularity'):
            full_data.popularity = basic.popularity
        
        # Load fight history from basic record if available
        if hasattr(basic, 'fight_history') and basic.fight_history:
            full_data.fight_history = basic.fight_history.copy()
        
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
        # Sync popularity if available
        if hasattr(basic, 'popularity'):
            basic.popularity = full.popularity
        # Sync fight history if available
        if hasattr(basic, 'fight_history'):
            basic.fight_history = full.fight_history.copy() if full.fight_history else []
    
    def _apply_fight_result(
        self,
        winner_id: str,
        loser_id: str,
        winner_name: str,
        loser_name: str,
        method: str,
        is_title: bool = False,
        event_name: str = "",
        generate_news: bool = True,
    ) -> None:
        """
        CONSOLIDATED: Apply fight result to both fighters.
        
        Updates:
        - Win/loss records
        - Win/loss streaks
        - KO/SUB stats
        - Popularity
        - Cooldowns
        - Chemistry (if applicable)
        - News (if generate_news=True)
        
        Called from both AI fight processing and player fight processing.
        """
        # ========================================
        # WINNER UPDATES
        # ========================================
        if winner_id in self.fighter_data:
            winner_data = self.fighter_data[winner_id]
            
            # Record
            winner_data.wins += 1
            winner_data.win_streak += 1
            winner_data.lose_streak = 0
            winner_data.lost_last_fight = False
            
            # Method-specific stats
            if method in ["KO", "TKO"]:
                winner_data.ko_wins += 1
            elif method == "SUB":
                winner_data.sub_wins += 1
            
            # Add to fight history
            fight_record = {
                "week": self.game_state.week_number,
                "event_name": event_name,
                "opponent_id": loser_id,
                "opponent_name": loser_name,
                "result": "W",
                "method": method,
                "is_title_fight": is_title,
            }
            winner_data.fight_history.append(fight_record)
            
            # Sync to game_state
            self._sync_fighter_record(winner_id)
            
            # Chemistry update (if coach system available)
            if winner_data.camp_id:
                head_coach = self._get_head_coach_info(winner_data.camp_id)
                if head_coach.get("coach_id"):
                    self._update_chemistry_on_fight(head_coach["coach_id"], winner_id, won=True)
            
            # Popularity update - use consolidated function
            was_title_defense = is_title and getattr(winner_data, 'is_champion', False)
            pop_change = calculate_popularity_change(
                won=True,
                method=method,
                was_title_fight=is_title,
                was_title_defense=was_title_defense,
                win_streak=winner_data.win_streak,
                loss_streak=0,
                current_popularity=winner_data.popularity,
            )
            winner_data.popularity = max(0, min(100, winner_data.popularity + pop_change))
            
            # Win streak milestone news
            if generate_news and hasattr(self, 'news_feed') and self.news_feed is not None:
                streak = winner_data.win_streak
                headlines = None
                if streak == 3:
                    headlines = [
                        f"{winner_name} extends win streak to 3 - momentum building",
                        f"{winner_name} makes it 3 in a row - contender status rising",
                        f"Hot streak! {winner_name} picks up third straight victory",
                    ]
                elif streak == 5:
                    headlines = [
                        f"{winner_name} wins 5 straight - title shot brewing?",
                        f"Can anyone stop {winner_name}? Five wins and counting",
                        f"{winner_name}'s dominant run continues with win #5",
                    ]
                elif streak == 7:
                    headlines = [
                        f"UNSTOPPABLE: {winner_name} extends streak to 7!",
                        f"{winner_name} is on a tear - seven consecutive victories",
                        f"Division on notice: {winner_name} wins 7th straight",
                    ]
                elif streak == 10:
                    headlines = [
                        f"HISTORIC RUN: {winner_name} reaches 10 straight wins!",
                        f"Double digits! {winner_name}'s incredible 10-fight streak",
                        f"Legendary streak: {winner_name} makes it 10 in a row",
                    ]
                
                if headlines:
                    self.news_feed.insert(0, NewsItem(
                        headline=random.choice(headlines),
                        category="streak",
                        week=self.game_state.week_number,
                    ))
        
        # Clear winner cooldown
        if winner_id in self._fighter_cooldowns:
            del self._fighter_cooldowns[winner_id]
        
        # ========================================
        # LOSER UPDATES
        # ========================================
        if loser_id in self.fighter_data:
            loser_data = self.fighter_data[loser_id]
            
            # Record
            loser_data.losses += 1
            loser_data.lose_streak += 1
            loser_data.win_streak = 0
            loser_data.lost_last_fight = True
            
            # Method-specific stats
            if method in ["KO", "TKO"]:
                loser_data.ko_losses += 1
            elif method == "SUB":
                loser_data.sub_losses += 1
            
            # Add to fight history
            fight_record = {
                "week": self.game_state.week_number,
                "event_name": event_name,
                "opponent_id": winner_id,
                "opponent_name": winner_name,
                "result": "L",
                "method": method,
                "is_title_fight": is_title,
            }
            loser_data.fight_history.append(fight_record)
            
            # Sync to game_state
            self._sync_fighter_record(loser_id)
            
            # Chemistry update
            if loser_data.camp_id:
                head_coach = self._get_head_coach_info(loser_data.camp_id)
                if head_coach.get("coach_id"):
                    self._update_chemistry_on_fight(head_coach["coach_id"], loser_id, won=False)
            
            # Popularity update - use consolidated function
            pop_change = calculate_popularity_change(
                won=False,
                method=method,
                was_title_fight=is_title,
                was_title_defense=False,
                win_streak=0,
                loss_streak=loser_data.lose_streak,
                current_popularity=loser_data.popularity,
            )
            loser_data.popularity = max(0, min(100, loser_data.popularity + pop_change))
            
            # Apply cooldown: 4 weeks + 2 per additional loss in streak
            cooldown_weeks = 4 + (loser_data.lose_streak - 1) * 2
            self._fighter_cooldowns[loser_id] = cooldown_weeks
        else:
            # AI fighter not in fighter_data - apply base cooldown
            existing_cooldown = self._fighter_cooldowns.get(loser_id, 0)
            if existing_cooldown > 0:
                cooldown_weeks = existing_cooldown + 2
            else:
                cooldown_weeks = 4
            self._fighter_cooldowns[loser_id] = cooldown_weeks
    
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
        takedowns = fighter_data.takedowns
        submissions = fighter_data.submissions
        top_control = fighter_data.top_control
        guard = fighter_data.guard
        clinch = fighter_data.clinch_striking
        
        # Check for dominant style
        striking_avg = (boxing + kicks) / 2
        grappling_avg = (takedowns + submissions) / 2
        
        # Strong BJJ/submission focus
        if submissions >= 70 and submissions > takedowns + 10:
            return "Brazilian Jiu-Jitsu"
        
        # Strong wrestling focus (takedowns + control)
        if takedowns >= 70 and top_control >= 65 and takedowns > submissions + 10:
            return "Wrestling"
        
        # Sambo style (good at both takedowns and subs)
        if takedowns >= 65 and submissions >= 65:
            return "Sambo"
        
        # Ground and Pound specialist (takedowns + top control, weak subs)
        if takedowns >= 65 and top_control >= 70 and submissions < 55:
            return "Ground & Pound"
        
        # Guard player (dangerous off back)
        if guard >= 75 and submissions >= 70:
            return "Submission Artist"
        
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
        
        # Judo (wrestling + subs but more throws)
        if takedowns >= 60 and submissions >= 60 and clinch >= 55:
            return "Judo"
        
        # Default
        return "MMA Hybrid"
    
    def _assign_traits(self, fighter_data: FighterFullData) -> None:
        """Assign random traits to a fighter based on their attributes.
        
        Uses the traits module for assignment logic and stat modifiers.
        """
        # Build attributes dict for the traits module
        # Map new attribute names to what traits module expects
        fighter_attrs = {
            "boxing": fighter_data.boxing,
            "kicks": fighter_data.kicks,
            "wrestling": fighter_data.takedowns,  # Map takedowns -> wrestling for traits
            "bjj": fighter_data.submissions,      # Map submissions -> bjj for traits
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
        """Schedule a full AI fight card with UFC-style structure.
        
        CARD STRUCTURE (12 fights total):
        - Main Event (1): Title fight or top contender clash
        - Co-Main (1): High-profile ranked fight  
        - Main Card (3): Ranked fights
        - Prelims (4): Lower ranked, gatekeeper tests
        - Early Prelims (3): Unranked prospects - GUARANTEED SLOTS
        
        SCHEDULING ORDER:
        1. Title fights (main event priority)
        2. Early prelim slots (guarantee unranked fights happen)
        3. Ranked vs ranked (fill main card and prelims)
        4. Additional unranked if slots remain
        """
        weight_classes = list(self.game_state.divisions.keys())
        
        # Card slot targets - HARD LIMITS
        MIN_CARD_SIZE = 10  # Minimum fights per card
        MAX_CARD_SIZE = 12  # Maximum fights per card
        MAIN_EVENT_MAX = 1
        CO_MAIN_MAX = 1
        MAIN_CARD_TARGET = 3
        PRELIM_TARGET = 4
        EARLY_PRELIM_TARGET = 3
        
        scheduled_this_event = set()
        card_fights = {
            "main_event": [],
            "co_main": [],
            "main_card": [],
            "prelim": [],
            "early_prelim": [],
        }
        
        def total_fights() -> int:
            return sum(len(fights) for fights in card_fights.values())
        
        def card_is_full() -> bool:
            return total_fights() >= MAX_CARD_SIZE
        
        def card_needs_more() -> bool:
            return total_fights() < MIN_CARD_SIZE
        
        # =====================================================================
        # PHASE 1: TITLE FIGHTS (Main Event)
        # =====================================================================
        if not hasattr(self, '_title_fight_cooldowns'):
            self._title_fight_cooldowns = {}
        
        title_fights_this_event = 0
        MAX_TITLE_FIGHTS_PER_EVENT = 2
        TITLE_FIGHT_COOLDOWN = 8
        
        shuffled_wcs = list(weight_classes)
        random.shuffle(shuffled_wcs)
        
        for wc in shuffled_wcs:
            if title_fights_this_event >= MAX_TITLE_FIGHTS_PER_EVENT:
                break
            
            if wc in self._title_fight_cooldowns and self._title_fight_cooldowns[wc] > 0:
                continue
            
            # Find champion
            champion = None
            for f in self.game_state.fighters.values():
                if (f.weight_class == wc and f.is_active and 
                    self._is_division_champion(f) and
                    f.fighter_id not in scheduled_this_event):
                    if self._is_fighter_available_for_scheduling(f.fighter_id):
                        champion = f
                        break
            
            if not champion:
                continue
            
            # Find challenger (top 5)
            best_challenger = None
            best_rank = 99
            
            available = self._get_available_ai_fighters(wc)
            for fid in available:
                if fid == champion.fighter_id or fid in scheduled_this_event:
                    continue
                
                challenger = self.game_state.fighters.get(fid)
                if not challenger or challenger.camp_id == champion.camp_id:
                    continue
                
                rank = self._get_fighter_division_rank(challenger)
                if not rank or rank > 5:
                    continue
                
                fdata = self.fighter_data.get(fid)
                if not fdata or (fdata.wins + fdata.losses) < 3:
                    continue
                
                if rank < best_rank:
                    best_rank = rank
                    best_challenger = challenger
            
            if best_challenger:
                f1, f2 = champion, best_challenger
                f1_id, f2_id = f1.fighter_id, f2.fighter_id
                
                # Generate gameplans
                f1_gameplan, f2_gameplan = self._generate_fight_gameplans(f1_id, f2_id, True, 5)
                
                # Determine card slot
                card_slot = "main_event" if not card_fights["main_event"] else "co_main"
                
                fight = {
                    "fighter1_id": f1_id,
                    "fighter2_id": f2_id,
                    "fighter1_name": f1.name,
                    "fighter2_name": f2.name,
                    "weight_class": wc,
                    "is_title_fight": True,
                    "is_main_event": card_slot == "main_event",
                    "rounds": 5,
                    "weeks_until": weeks_away,
                    "event_name": event_name,
                    "card_slot": card_slot,
                }
                
                if f1_gameplan:
                    fight["fighter1_gameplan"] = f1_gameplan.to_dict() if hasattr(f1_gameplan, 'to_dict') else None
                if f2_gameplan:
                    fight["fighter2_gameplan"] = f2_gameplan.to_dict() if hasattr(f2_gameplan, 'to_dict') else None
                
                self.ai_scheduled_fights.append(fight)
                card_fights[card_slot].append(fight)
                scheduled_this_event.add(f1_id)
                scheduled_this_event.add(f2_id)
                
                self._title_fight_cooldowns[wc] = TITLE_FIGHT_COOLDOWN
                title_fights_this_event += 1
                
                self.news_feed.insert(0, NewsItem(
                    headline=f"TITLE FIGHT: {f1.name} vs {f2.name} for the {wc} title!",
                    category="fight",
                    week=self.game_state.week_number,
                ))
        
        # =====================================================================
        # BUILD FIGHTER POOLS
        # =====================================================================
        division_rankings: Dict[str, List[Tuple[str, int]]] = {}
        division_unranked: Dict[str, List[str]] = {}
        
        for wc in weight_classes:
            available = self._get_available_ai_fighters(wc)
            available = [f for f in available if f not in scheduled_this_event]
            
            ranked = []
            unranked = []
            
            for fid in available:
                fighter = self.game_state.fighters.get(fid)
                if not fighter:
                    continue
                if self._is_division_champion(fighter):
                    continue
                
                rank = self._get_fighter_division_rank(fighter)
                if rank and rank > 0:
                    ranked.append((fid, rank))
                else:
                    unranked.append(fid)
            
            ranked.sort(key=lambda x: x[1])
            division_rankings[wc] = ranked
            division_unranked[wc] = unranked
        
        # =====================================================================
        # PHASE 2: EARLY PRELIMS (Unranked - GUARANTEED)
        # =====================================================================
        # Schedule unranked fights FIRST to ensure prospects get opportunities
        
        all_unranked = []
        for wc in weight_classes:
            for fid in division_unranked.get(wc, []):
                if fid not in scheduled_this_event:
                    fighter = self.game_state.fighters.get(fid)
                    fdata = self.fighter_data.get(fid)
                    # Priority: undefeated or good record fighters first
                    if fighter and fdata:
                        priority = 0
                        if fdata.losses == 0 and fdata.wins > 0:
                            priority = 100 + fdata.wins  # Undefeated bonus
                        elif fdata.wins > fdata.losses:
                            priority = 50 + fdata.wins  # Winning record
                        else:
                            priority = fdata.wins
                        all_unranked.append((fid, wc, priority))
        
        # Sort by priority (highest first), then shuffle within tiers
        all_unranked.sort(key=lambda x: -x[2])
        
        early_prelim_scheduled = 0
        
        for fid, wc, priority in all_unranked:
            if early_prelim_scheduled >= EARLY_PRELIM_TARGET:
                break
            if fid in scheduled_this_event:
                continue
            
            opp_id = self._find_unranked_opponent(fid, wc, scheduled_this_event, division_unranked)
            if opp_id:
                f1 = self.game_state.fighters.get(fid)
                f2 = self.game_state.fighters.get(opp_id)
                
                if f1 and f2:
                    f1_gameplan, f2_gameplan = self._generate_fight_gameplans(fid, opp_id, False, 3)
                    
                    fight = {
                        "fighter1_id": fid,
                        "fighter2_id": opp_id,
                        "fighter1_name": f1.name,
                        "fighter2_name": f2.name,
                        "weight_class": wc,
                        "is_title_fight": False,
                        "is_main_event": False,
                        "rounds": 3,
                        "weeks_until": weeks_away,
                        "event_name": event_name,
                        "card_slot": "early_prelim",
                        "matchup_type": "unranked",
                    }
                    
                    if f1_gameplan:
                        fight["fighter1_gameplan"] = f1_gameplan.to_dict() if hasattr(f1_gameplan, 'to_dict') else None
                    if f2_gameplan:
                        fight["fighter2_gameplan"] = f2_gameplan.to_dict() if hasattr(f2_gameplan, 'to_dict') else None
                    
                    self.ai_scheduled_fights.append(fight)
                    card_fights["early_prelim"].append(fight)
                    scheduled_this_event.add(fid)
                    scheduled_this_event.add(opp_id)
                    early_prelim_scheduled += 1
                    
                    # News for notable unranked: undefeated or 3+ wins
                    f1_data = self.fighter_data.get(fid)
                    f2_data = self.fighter_data.get(opp_id)
                    
                    notable_fighter = None
                    if f1_data and f1_data.losses == 0 and f1_data.wins >= 2:
                        notable_fighter = (f1.name, f1_data.wins, "undefeated")
                    elif f2_data and f2_data.losses == 0 and f2_data.wins >= 2:
                        notable_fighter = (f2.name, f2_data.wins, "undefeated")
                    elif f1_data and f1_data.wins >= 3 and f1_data.wins > f1_data.losses:
                        notable_fighter = (f1.name, f1_data.wins, "prospect")
                    elif f2_data and f2_data.wins >= 3 and f2_data.wins > f2_data.losses:
                        notable_fighter = (f2.name, f2_data.wins, "prospect")
                    
                    if notable_fighter:
                        name, wins, tag = notable_fighter
                        if tag == "undefeated":
                            self.news_feed.insert(0, NewsItem(
                                headline=f"Undefeated prospect {name} ({wins}-0) returns to action",
                                category="prospect",
                                week=self.game_state.week_number,
                            ))
                    
                    # Update pools
                    division_unranked[wc] = [x for x in division_unranked.get(wc, []) 
                                             if x not in scheduled_this_event]
        
        # =====================================================================
        # PHASE 3: RANKED FIGHTS (Main Card + Prelims)
        # =====================================================================
        
        all_ranked_fighters = []
        for wc in weight_classes:
            for fid, rank in division_rankings.get(wc, []):
                if fid not in scheduled_this_event:
                    all_ranked_fighters.append((fid, rank, wc))
        
        random.shuffle(all_ranked_fighters)
        # Sort by rank to prioritize higher ranked fighters
        all_ranked_fighters.sort(key=lambda x: x[1])
        
        for fid, rank, wc in all_ranked_fighters:
            # Check if card is full
            if card_is_full():
                break
            
            # Check if we have room in any ranked slot
            main_card_full = len(card_fights["main_card"]) >= MAIN_CARD_TARGET
            prelim_full = len(card_fights["prelim"]) >= PRELIM_TARGET
            main_event_full = len(card_fights["main_event"]) >= MAIN_EVENT_MAX
            co_main_full = len(card_fights["co_main"]) >= CO_MAIN_MAX
            
            if main_card_full and prelim_full and main_event_full and co_main_full:
                break
            
            if fid in scheduled_this_event:
                continue
            
            opp_id = self._find_ranked_opponent(fid, rank, wc, scheduled_this_event, division_rankings, division_unranked)
            if opp_id:
                f1 = self.game_state.fighters.get(fid)
                f2 = self.game_state.fighters.get(opp_id)
                
                if f1 and f2:
                    f1_rank = rank
                    f2_rank = self._get_fighter_division_rank(f2) or 0
                    
                    # Get popularity values for star power calculation
                    f1_data = self.fighter_data.get(fid)
                    f2_data = self.fighter_data.get(opp_id)
                    f1_pop = f1_data.popularity if f1_data else 10
                    f2_pop = f2_data.popularity if f2_data else 10
                    combined_pop = f1_pop + f2_pop
                    
                    # Determine card slot based on ranks AND popularity
                    # Main event requires: top 3 clash OR very high combined popularity
                    card_slot = None
                    
                    # Check main event eligibility (strict requirements)
                    is_main_worthy = False
                    if f1_rank <= 3 and f2_rank and f2_rank <= 3:
                        is_main_worthy = True  # Top 3 clash
                    elif combined_pop >= 120:
                        is_main_worthy = True  # Star power match
                    elif f1_rank <= 5 and f2_rank and f2_rank <= 5 and combined_pop >= 100:
                        is_main_worthy = True  # Top 5 with good popularity
                    
                    # Assign slot with proper requirements (NO #8 vs #9 as main event)
                    if is_main_worthy and not main_event_full:
                        card_slot = "main_event"
                    elif f1_rank <= 5 and f2_rank and f2_rank <= 5:
                        # Top 5 clash - co-main or main card (not main event without star power)
                        if not co_main_full:
                            card_slot = "co_main"
                        elif not main_card_full:
                            card_slot = "main_card"
                        elif not prelim_full:
                            card_slot = "prelim"
                    elif f1_rank <= 10 and f2_rank and f2_rank <= 10:
                        # Top 10 fight - main card or prelim only (NEVER main event)
                        if not main_card_full:
                            card_slot = "main_card"
                        elif not prelim_full:
                            card_slot = "prelim"
                    else:
                        # Lower ranked - prelim only
                        if not prelim_full:
                            card_slot = "prelim"
                    
                    # Skip if no slot available
                    if not card_slot:
                        continue
                    
                    is_main = card_slot == "main_event"
                    rounds = 5 if is_main else 3
                    
                    f1_gameplan, f2_gameplan = self._generate_fight_gameplans(fid, opp_id, is_main, rounds)
                    
                    fight = {
                        "fighter1_id": fid,
                        "fighter2_id": opp_id,
                        "fighter1_name": f1.name,
                        "fighter2_name": f2.name,
                        "weight_class": wc,
                        "is_title_fight": False,
                        "is_main_event": is_main,
                        "rounds": rounds,
                        "weeks_until": weeks_away,
                        "event_name": event_name,
                        "card_slot": card_slot,
                        "matchup_type": "ranked" if f2_rank else "gatekeeper",
                    }
                    
                    if f1_gameplan:
                        fight["fighter1_gameplan"] = f1_gameplan.to_dict() if hasattr(f1_gameplan, 'to_dict') else None
                    if f2_gameplan:
                        fight["fighter2_gameplan"] = f2_gameplan.to_dict() if hasattr(f2_gameplan, 'to_dict') else None
                    
                    self.ai_scheduled_fights.append(fight)
                    card_fights[card_slot].append(fight)
                    scheduled_this_event.add(fid)
                    scheduled_this_event.add(opp_id)
                    
                    # Update pools
                    division_rankings[wc] = [(x, r) for x, r in division_rankings.get(wc, []) 
                                             if x not in scheduled_this_event]
                    division_unranked[wc] = [x for x in division_unranked.get(wc, []) 
                                             if x not in scheduled_this_event]
                    
                    # Announce significant fights
                    is_top_5_fight = f1_rank <= 5 and f2_rank and f2_rank <= 5
                    is_top_10_fight = f1_rank <= 10 and f2_rank and f2_rank <= 10
                    
                    if is_top_5_fight:
                        self.news_feed.insert(0, NewsItem(
                            headline=f"TOP 5 CLASH: #{f1_rank} {f1.name} vs #{f2_rank} {f2.name}",
                            category="fight",
                            week=self.game_state.week_number,
                        ))
                    elif is_top_10_fight:
                        self.news_feed.insert(0, NewsItem(
                            headline=f"SIGNED: #{f1_rank} {f1.name} vs #{f2_rank} {f2.name}",
                            category="fight",
                            week=self.game_state.week_number,
                        ))
        
        # =====================================================================
        # PHASE 4: FILL REMAINING SLOTS
        # =====================================================================
        # If card has room, add more unranked fights
        
        all_unranked_remaining = []
        for wc in weight_classes:
            for fid in division_unranked.get(wc, []):
                if fid not in scheduled_this_event:
                    all_unranked_remaining.append((fid, wc))
        
        random.shuffle(all_unranked_remaining)
        
        for fid, wc in all_unranked_remaining:
            # Check if card is full (hard limit)
            if card_is_full():
                break
            
            # Check if we have room in any unranked slot
            prelim_has_room = len(card_fights["prelim"]) < PRELIM_TARGET
            early_has_room = len(card_fights["early_prelim"]) < EARLY_PRELIM_TARGET
            
            if not prelim_has_room and not early_has_room:
                break
            
            if fid in scheduled_this_event:
                continue
            
            opp_id = self._find_unranked_opponent(fid, wc, scheduled_this_event, division_unranked)
            if opp_id:
                f1 = self.game_state.fighters.get(fid)
                f2 = self.game_state.fighters.get(opp_id)
                
                if f1 and f2:
                    card_slot = "prelim" if prelim_has_room else "early_prelim"
                    
                    f1_gameplan, f2_gameplan = self._generate_fight_gameplans(fid, opp_id, False, 3)
                    
                    fight = {
                        "fighter1_id": fid,
                        "fighter2_id": opp_id,
                        "fighter1_name": f1.name,
                        "fighter2_name": f2.name,
                        "weight_class": wc,
                        "is_title_fight": False,
                        "is_main_event": False,
                        "rounds": 3,
                        "weeks_until": weeks_away,
                        "event_name": event_name,
                        "card_slot": card_slot,
                        "matchup_type": "unranked",
                    }
                    
                    if f1_gameplan:
                        fight["fighter1_gameplan"] = f1_gameplan.to_dict() if hasattr(f1_gameplan, 'to_dict') else None
                    if f2_gameplan:
                        fight["fighter2_gameplan"] = f2_gameplan.to_dict() if hasattr(f2_gameplan, 'to_dict') else None
                    
                    self.ai_scheduled_fights.append(fight)
                    card_fights[card_slot].append(fight)
                    scheduled_this_event.add(fid)
                    scheduled_this_event.add(opp_id)
                    
                    division_unranked[wc] = [x for x in division_unranked.get(wc, []) 
                                             if x not in scheduled_this_event]
        
        # =====================================================================
        # PHASE 5: FILL TO MINIMUM (if under 10 fights)
        # =====================================================================
        # Keep adding fights until we hit minimum, ignoring slot targets
        
        if card_needs_more():
            # Try adding more ranked fights to prelims
            for fid, rank, wc in all_ranked_fighters:
                if not card_needs_more():
                    break
                if fid in scheduled_this_event:
                    continue
                
                opp_id = self._find_ranked_opponent(fid, rank, wc, scheduled_this_event, division_rankings, division_unranked)
                if opp_id:
                    f1 = self.game_state.fighters.get(fid)
                    f2 = self.game_state.fighters.get(opp_id)
                    
                    if f1 and f2:
                        f1_gameplan, f2_gameplan = self._generate_fight_gameplans(fid, opp_id, False, 3)
                        
                        fight = {
                            "fighter1_id": fid,
                            "fighter2_id": opp_id,
                            "fighter1_name": f1.name,
                            "fighter2_name": f2.name,
                            "weight_class": wc,
                            "is_title_fight": False,
                            "is_main_event": False,
                            "rounds": 3,
                            "weeks_until": weeks_away,
                            "event_name": event_name,
                            "card_slot": "prelim",
                            "matchup_type": "ranked",
                        }
                        
                        if f1_gameplan:
                            fight["fighter1_gameplan"] = f1_gameplan.to_dict() if hasattr(f1_gameplan, 'to_dict') else None
                        if f2_gameplan:
                            fight["fighter2_gameplan"] = f2_gameplan.to_dict() if hasattr(f2_gameplan, 'to_dict') else None
                        
                        self.ai_scheduled_fights.append(fight)
                        card_fights["prelim"].append(fight)
                        scheduled_this_event.add(fid)
                        scheduled_this_event.add(opp_id)
        
        # Still need more? Add any unranked fights
        if card_needs_more():
            all_remaining_unranked = []
            for wc in weight_classes:
                for fid in division_unranked.get(wc, []):
                    if fid not in scheduled_this_event:
                        all_remaining_unranked.append((fid, wc))
            
            random.shuffle(all_remaining_unranked)
            
            for fid, wc in all_remaining_unranked:
                if not card_needs_more():
                    break
                if fid in scheduled_this_event:
                    continue
                
                opp_id = self._find_unranked_opponent(fid, wc, scheduled_this_event, division_unranked)
                if opp_id:
                    f1 = self.game_state.fighters.get(fid)
                    f2 = self.game_state.fighters.get(opp_id)
                    
                    if f1 and f2:
                        f1_gameplan, f2_gameplan = self._generate_fight_gameplans(fid, opp_id, False, 3)
                        
                        fight = {
                            "fighter1_id": fid,
                            "fighter2_id": opp_id,
                            "fighter1_name": f1.name,
                            "fighter2_name": f2.name,
                            "weight_class": wc,
                            "is_title_fight": False,
                            "is_main_event": False,
                            "rounds": 3,
                            "weeks_until": weeks_away,
                            "event_name": event_name,
                            "card_slot": "early_prelim",
                            "matchup_type": "unranked",
                        }
                        
                        if f1_gameplan:
                            fight["fighter1_gameplan"] = f1_gameplan.to_dict() if hasattr(f1_gameplan, 'to_dict') else None
                        if f2_gameplan:
                            fight["fighter2_gameplan"] = f2_gameplan.to_dict() if hasattr(f2_gameplan, 'to_dict') else None
                        
                        self.ai_scheduled_fights.append(fight)
                        card_fights["early_prelim"].append(fight)
                        scheduled_this_event.add(fid)
                        scheduled_this_event.add(opp_id)
                        
                        division_unranked[wc] = [x for x in division_unranked.get(wc, []) 
                                                 if x not in scheduled_this_event]
        
        # =====================================================================
        # PHASE 6: ENSURE MAIN EVENT & CO-MAIN (Promote best fights)
        # =====================================================================
        # If no main event, promote the best prelim fight
        # If no co-main, promote the next best prelim fight
        
        def get_fight_quality(fight: Dict) -> int:
            """Score a fight by combined fighter ratings."""
            f1_id = fight.get("fighter1_id")
            f2_id = fight.get("fighter2_id")
            f1_data = self.fighter_data.get(f1_id)
            f2_data = self.fighter_data.get(f2_id)
            f1_rating = f1_data.overall_rating if f1_data else 50
            f2_rating = f2_data.overall_rating if f2_data else 50
            return f1_rating + f2_rating
        
        # Promote to main event if empty
        if not card_fights["main_event"]:
            # Look in main_card first, then prelims
            candidates = card_fights["main_card"] + card_fights["prelim"]
            if candidates:
                # Sort by quality (best first)
                candidates.sort(key=get_fight_quality, reverse=True)
                promoted = candidates[0]
                
                # Remove from original slot
                if promoted in card_fights["main_card"]:
                    card_fights["main_card"].remove(promoted)
                elif promoted in card_fights["prelim"]:
                    card_fights["prelim"].remove(promoted)
                
                # Update fight data
                promoted["card_slot"] = "main_event"
                promoted["is_main_event"] = True
                promoted["rounds"] = 5  # Main events are 5 rounds
                card_fights["main_event"].append(promoted)
                
                # Update in ai_scheduled_fights
                for f in self.ai_scheduled_fights:
                    if (f.get("fighter1_id") == promoted.get("fighter1_id") and 
                        f.get("fighter2_id") == promoted.get("fighter2_id") and
                        f.get("event_name") == event_name):
                        f["card_slot"] = "main_event"
                        f["is_main_event"] = True
                        f["rounds"] = 5
                        break
        
        # Promote to co-main if empty
        if not card_fights["co_main"]:
            # Look in main_card first, then prelims
            candidates = card_fights["main_card"] + card_fights["prelim"]
            if candidates:
                candidates.sort(key=get_fight_quality, reverse=True)
                promoted = candidates[0]
                
                # Remove from original slot
                if promoted in card_fights["main_card"]:
                    card_fights["main_card"].remove(promoted)
                elif promoted in card_fights["prelim"]:
                    card_fights["prelim"].remove(promoted)
                
                # Update fight data
                promoted["card_slot"] = "co_main"
                promoted["is_co_main"] = True
                card_fights["co_main"].append(promoted)
                
                # Update in ai_scheduled_fights
                for f in self.ai_scheduled_fights:
                    if (f.get("fighter1_id") == promoted.get("fighter1_id") and 
                        f.get("fighter2_id") == promoted.get("fighter2_id") and
                        f.get("event_name") == event_name):
                        f["card_slot"] = "co_main"
                        f["is_co_main"] = True
                        break
    
    def _generate_fight_gameplans(self, f1_id: str, f2_id: str, is_main: bool, rounds: int):
        """Generate AI gameplans for both fighters."""
        f1_gameplan, f2_gameplan = None, None
        
        if GAMEPLAN_AVAILABLE:
            f1_data = self.fighter_data.get(f1_id) or self._create_full_fighter_data(f1_id)
            f2_data = self.fighter_data.get(f2_id) or self._create_full_fighter_data(f2_id)
            
            if f1_data and f2_data:
                f1_stats = {
                    "boxing": f1_data.boxing, "kicks": f1_data.kicks,
                    "wrestling": f1_data.takedowns, "bjj": f1_data.submissions,
                    "power": getattr(f1_data, 'strength', 50), "cardio": f1_data.cardio,
                }
                f2_stats = {
                    "boxing": f2_data.boxing, "kicks": f2_data.kicks,
                    "wrestling": f2_data.takedowns, "bjj": f2_data.submissions,
                    "power": getattr(f2_data, 'strength', 50), "cardio": f2_data.cardio,
                }
                f1_gameplan = generate_ai_gameplan(f1_stats, f2_stats, is_main, rounds)
                f2_gameplan = generate_ai_gameplan(f2_stats, f1_stats, is_main, rounds)
        
        return f1_gameplan, f2_gameplan
    
    def _find_ranked_opponent(self, fighter_id: str, fighter_rank: int, wc: str, 
                               scheduled: set, division_rankings: Dict, division_unranked: Dict) -> Optional[str]:
        """Find best ranked opponent based on UFC matchmaking rules."""
        fighter = self.game_state.fighters.get(fighter_id)
        if not fighter:
            return None
        
        # Get opponent rank range
        min_rank, max_rank, unranked_chance = self._get_opponent_rank_range(fighter_rank)
        
        # Chance to fight unranked (gatekeeper role)
        if random.random() < unranked_chance and division_unranked.get(wc):
            candidates = [f for f in division_unranked[wc] 
                         if f not in scheduled and f != fighter_id]
            if candidates:
                candidates.sort(key=lambda x: abs(
                    self.game_state.fighters.get(x, fighter).overall_rating - 
                    fighter.overall_rating
                ))
                for opp_id in candidates[:5]:
                    opp = self.game_state.fighters.get(opp_id)
                    if opp and opp.camp_id != fighter.camp_id:
                        return opp_id
        
        # Find ranked opponent in range
        ranked = division_rankings.get(wc, [])
        candidates = []
        
        for opp_id, opp_rank in ranked:
            if opp_id == fighter_id or opp_id in scheduled:
                continue
            if min_rank <= opp_rank <= max_rank:
                opp = self.game_state.fighters.get(opp_id)
                if opp and opp.camp_id != fighter.camp_id:
                    rank_diff = abs(fighter_rank - opp_rank)
                    rating_diff = abs(fighter.overall_rating - opp.overall_rating)
                    quality = 100 - (rank_diff * 5) - (rating_diff * 0.5)
                    candidates.append((opp_id, quality))
        
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidates = candidates[:3]
            if len(top_candidates) == 1:
                return top_candidates[0][0]
            
            weights = [3, 2, 1][:len(top_candidates)]
            selected = random.choices(top_candidates, weights=weights)[0]
            return selected[0]
        
        # Expand search
        for opp_id, opp_rank in ranked:
            if opp_id == fighter_id or opp_id in scheduled:
                continue
            opp = self.game_state.fighters.get(opp_id)
            if opp and opp.camp_id != fighter.camp_id:
                return opp_id
        
        return None
    
    def _find_unranked_opponent(self, fighter_id: str, wc: str, scheduled: set, 
                                 division_unranked: Dict) -> Optional[str]:
        """Find opponent for unranked fighter."""
        fighter = self.game_state.fighters.get(fighter_id)
        if not fighter:
            return None
        
        candidates = [f for f in division_unranked.get(wc, []) 
                     if f not in scheduled and f != fighter_id]
        if candidates:
            candidates.sort(key=lambda x: abs(
                self.game_state.fighters.get(x, fighter).overall_rating - 
                fighter.overall_rating
            ))
            for opp_id in candidates[:5]:
                opp = self.game_state.fighters.get(opp_id)
                if opp and opp.camp_id != fighter.camp_id:
                    return opp_id
        
        return None
    
    def _get_opponent_rank_range(self, rank: Optional[int]) -> Tuple[int, int, float]:
        """Get realistic opponent rank range based on UFC patterns.
        
        Returns: (min_rank, max_rank, unranked_chance)
        """
        if not rank or rank <= 0:
            return (11, 15, 0.70)
        elif rank <= 3:
            return (1, 6, 0.05)
        elif rank <= 5:
            return (2, 8, 0.05)
        elif rank <= 7:
            return (4, 10, 0.10)
        elif rank <= 10:
            return (5, 13, 0.15)
        elif rank <= 12:
            return (8, 15, 0.30)
        else:
            return (10, 15, 0.40)
    
    def _is_fighter_available_for_scheduling(self, fighter_id: str) -> bool:
        """Check if fighter is available for AI fight scheduling."""
        # Check cooldowns
        if self._fighter_cooldowns.get(fighter_id, 0) > 0:
            return False
        
        # Check if already scheduled
        for fight in self.player_scheduled_fights + self.ai_scheduled_fights:
            if fight.get("fighter1_id") == fighter_id or fight.get("fighter2_id") == fighter_id:
                return False
        
        # Check injuries
        if INJURY_AVAILABLE and self._injury_system:
            injury = self._injury_system.get_worst_injury(fighter_id)
            if injury and injury.weeks_remaining > 0:
                return False
        
        return True
    
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
        
        # SAFETY CHECK: Detect if either fighter is a champion
        # If so, this MUST be a title fight regardless of how it was scheduled
        f1_rec = self.game_state.fighters.get(f1_id)
        f2_rec = self.game_state.fighters.get(f2_id)
        f1_is_champ = f1_rec and self._is_division_champion(f1_rec)
        f2_is_champ = f2_rec and self._is_division_champion(f2_rec)
        
        if (f1_is_champ or f2_is_champ) and not is_title:
            # Correct the title fight flag - champion involvement = title fight
            is_title = True
            fight["is_title_fight"] = True
            fight["is_main_event"] = True  # Title fights are always main events
            fight["rounds"] = 5  # Title fights are 5 rounds
            rounds = 5
            
            # Add [C] tag to champion's name for display
            if f1_is_champ and "[C]" not in f1_name:
                f1_name = f"[C] {f1_name}"
                fight["fighter1_name"] = f1_name
            if f2_is_champ and "[C]" not in f2_name:
                f2_name = f"[C] {f2_name}"
                fight["fighter2_name"] = f2_name
        
        # Get or create fighter data
        f1_data = self._create_full_fighter_data(f1_id)
        f2_data = self._create_full_fighter_data(f2_id)
        
        f1_rating = f1_data.overall_rating if f1_data else 50
        f2_rating = f2_data.overall_rating if f2_data else 50
        
        is_main = fight.get("is_main_event", False)
        
        # Get AI gameplans if stored
        f1_gameplan = fight.get("fighter1_gameplan")
        f2_gameplan = fight.get("fighter2_gameplan")
        
        # Get heat level from rivalry
        heat_level = self._get_heat_level(f1_id, f2_id)
        
        # Use full fight engine for ALL fights for consistency
        # Simple sim only as fallback if engine unavailable
        sim_result = None
        if FIGHT_ENGINE_AVAILABLE:
            sim_result = self._narrated_fight_simulation(
                f1_id, f2_id, rounds,
                is_title_fight=is_title,
                is_main_event=is_main,
                heat_level=heat_level
            )
        
        # Fall back to simple simulation ONLY if full engine unavailable or failed
        if sim_result is None:
            sim_result = self._simple_fight_simulation(
                f1_id, f2_id, f1_name, f2_name, f1_rating, f2_rating, rounds,
                is_title_fight=is_title,
                is_main_event=is_main,
                f1_gameplan=f1_gameplan,
                f2_gameplan=f2_gameplan,
                heat_level=heat_level
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
            card_slot=fight.get("card_slot", ""),
            fighter1_strikes=sim_result.get("fighter1_strikes", 0),
            fighter2_strikes=sim_result.get("fighter2_strikes", 0),
            fighter1_takedowns=sim_result.get("fighter1_takedowns", 0),
            fighter2_takedowns=sim_result.get("fighter2_takedowns", 0),
        )
        
        # Store full commentary if available (for spectating AI fights)
        if "full_commentary" in sim_result:
            result.full_commentary = sim_result.get("full_commentary", "")
        if "key_moments" in sim_result and sim_result["key_moments"]:
            result.key_moments = sim_result["key_moments"]
        if "fight_narrative" in sim_result:
            result.fight_narrative = sim_result.get("fight_narrative", "")
        
        # Generate fight summary (only set key_moments if not already from simulation)
        has_sim_key_moments = bool(result.key_moments)
        if method == "KO":
            result.fight_summary = f"{winner_name} knocked out {loser_name} with a devastating strike in round {finish_round}."
            if not has_sim_key_moments:
                result.key_moments = [f"Round {finish_round}: {winner_name} lands the knockout blow"]
        elif method == "TKO":
            result.fight_summary = f"{winner_name} stopped {loser_name} by TKO in round {finish_round}."
            if not has_sim_key_moments:
                result.key_moments = [f"Round {finish_round}: Referee stoppage"]
        elif method == "SUB":
            subs = ["rear naked choke", "guillotine", "armbar", "triangle", "kimura"]
            sub_type = random.choice(subs)
            result.fight_summary = f"{winner_name} submitted {loser_name} with a {sub_type} in round {finish_round}."
            if not has_sim_key_moments:
                result.key_moments = [f"Round {finish_round}: {winner_name} locks in the {sub_type}"]
        else:
            result.fight_summary = f"{winner_name} outpointed {loser_name} over {rounds} rounds."
            if not has_sim_key_moments:
                result.key_moments = ["Fight goes to the scorecards"]
        
        # Store result
        self.all_fight_results[fight_id] = result
        
        # Capture pre-fight ranks and records before any updates
        winner_rec = self.game_state.fighters.get(winner_id)
        loser_rec = self.game_state.fighters.get(loser_id)
        winner_pre_rank = self._get_fighter_rank_num(winner_rec) if winner_rec else ""
        loser_pre_rank = self._get_fighter_rank_num(loser_rec) if loser_rec else ""
        winner_record = f"({winner_rec.wins}-{winner_rec.losses})" if winner_rec else ""
        loser_record = f"({loser_rec.wins}-{loser_rec.losses})" if loser_rec else ""
        
        # Process ranking changes for AI fights too
        ranking_changes = self._process_ranking_changes(
            winner_id=winner_id,
            winner_name=winner_name,
            loser_id=loser_id,
            loser_name=loser_name,
            weight_class=weight_class,
            method=method,
            was_title_fight=is_title,
        )
        
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
                "card_slot": fight.get("card_slot", ""),
                "weight_class": weight_class,
                "event_name": event_name,
                "card_position": fight.get("card_position", 0),
                "ranking_changes": ranking_changes,  # Now included!
                # Pre-fight data for accurate display
                "winner_pre_rank": winner_pre_rank,
                "loser_pre_rank": loser_pre_rank,
                "winner_record": winner_record,
                "loser_record": loser_record,
            })
        
        # Update fighter records using consolidated function
        self._apply_fight_result(
            winner_id=winner_id,
            loser_id=loser_id,
            winner_name=winner_name,
            loser_name=loser_name,
            method=method,
            is_title=is_title,
            event_name=event_name,
            generate_news=True,
        )
        
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
            
            title_changed = False
            old_champion_id = None
            old_champion_name = ""
            new_champion_id = None
            new_champion_name = ""
            
            if f1_rec and f1_rec.is_champion and loser_id == f1_id:
                # Champion (f1) lost to challenger (f2)
                title_changed = True
                old_champion_id = f1_id
                old_champion_name = f1_name
                new_champion_id = f2_id
                new_champion_name = f2_name
                
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
                # Champion (f2) lost to challenger (f1)
                title_changed = True
                old_champion_id = f2_id
                old_champion_name = f2_name
                new_champion_id = f1_id
                new_champion_name = f1_name
                
                f2_rec.is_champion = False
                if f1_rec:
                    f1_rec.is_champion = True
                if f2_id in self.fighter_data:
                    self.fighter_data[f2_id].is_champion = False
                if f1_id in self.fighter_data:
                    self.fighter_data[f1_id].is_champion = True
                if weight_class in self.game_state.divisions:
                    self.game_state.divisions[weight_class].champion_id = winner_id
            else:
                # Champion retained - record defense
                if self._belt_history:
                    self._belt_history.record_title_defense(weight_class)
            
            # Update belt history if title changed
            if title_changed and self._belt_history:
                event_name = f"DFC {self.next_event_number - 1}" if self.next_event_number > 1 else f"DFC {self.next_event_number}"
                self._belt_history.title_changes_hands(
                    new_champion_id=new_champion_id,
                    new_champion_name=new_champion_name,
                    old_champion_id=old_champion_id,
                    old_champion_name=old_champion_name,
                    weight_class=weight_class,
                    week=self.game_state.week_number,
                    event_name=event_name,
                    method=method,
                )
        
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
        
        # Tweak #4: Upset fanfare when unranked beats ranked
        # winner_pre_rank is "" for unranked, loser_pre_rank is "#X" for ranked
        is_upset = False
        if winner_pre_rank == "" and loser_pre_rank and loser_pre_rank.startswith("#"):
            is_upset = True
            try:
                loser_rank_num = int(loser_pre_rank.replace("#", "").replace("C", "0"))
                
                if loser_rank_num <= 5:  # Beat a top 5
                    upset_headlines = [
                        f"HUGE UPSET! Unranked {winner_name} stuns #{loser_rank_num} {loser_name}!",
                        f"SHOCKING! {winner_name} takes down top contender {loser_name}!",
                        f"Nobody saw this coming! {winner_name} defeats #{loser_rank_num}!",
                    ]
                elif loser_rank_num <= 10:  # Beat top 10
                    upset_headlines = [
                        f"UPSET! {winner_name} breaks into rankings with win over #{loser_rank_num}!",
                        f"Statement made! Unranked {winner_name} beats {loser_name}!",
                        f"Rising star {winner_name} upsets #{loser_rank_num} {loser_name}!",
                    ]
                else:  # Beat any ranked
                    upset_headlines = [
                        f"Upset! {winner_name} beats ranked opponent {loser_name}",
                        f"{winner_name} announces arrival with win over #{loser_rank_num}",
                        f"New face in the rankings? {winner_name} defeats {loser_name}",
                    ]
                
                self.news_feed.insert(0, NewsItem(
                    headline=random.choice(upset_headlines),
                    category="upset",
                    week=self.game_state.week_number,
                ))
            except (ValueError, AttributeError):
                pass  # Silently fail if rank parsing fails
        
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
                            "card_slot": f.card_slot,
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
            "title_fight_cooldowns": getattr(self, '_title_fight_cooldowns', {}),
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
            "training_data": self._training_system.to_dict() if self._training_system else {},
            "amateur_data": self._amateur_system.to_dict() if self._amateur_system else {},
            "interview_data": self._interview_manager.to_dict() if self._interview_manager and hasattr(self._interview_manager, 'to_dict') else {},
            "coach_data": self._coach_system.to_dict() if self._coach_system and hasattr(self._coach_system, 'to_dict') else {},
            "ladder_data": self._division_ladder.to_dict() if self._division_ladder and hasattr(self._division_ladder, 'to_dict') else {},
            "inbox_data": self._inbox.to_dict() if self._inbox and hasattr(self._inbox, 'to_dict') else {},
            "belt_history_data": self._belt_history.to_dict() if self._belt_history and hasattr(self._belt_history, 'to_dict') else {},
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
                        card_slot=f_dict.get("card_slot", ""),
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
            
            # Load title fight cooldowns
            self._title_fight_cooldowns = data.get("title_fight_cooldowns", {})
            
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
            
            # Load training data (active camps)
            if self._training_system and "training_data" in data and data["training_data"]:
                try:
                    from systems.training import TrainingSystem
                    self._training_system = TrainingSystem.from_dict(data["training_data"])
                except Exception:
                    # Keep existing training system if load fails
                    pass
            
            # Load amateur data
            if AMATEUR_AVAILABLE and "amateur_data" in data and data["amateur_data"]:
                try:
                    self._amateur_system = AmateurSystem.from_dict(data["amateur_data"])
                except Exception:
                    # Reinitialize if load fails
                    if AmateurSystem:
                        self._amateur_system = AmateurSystem()
                        self._amateur_system.initialize_pools()
            
            # Load interview data
            if INTERVIEW_AVAILABLE and "interview_data" in data and data["interview_data"]:
                try:
                    self._interview_manager = InterviewManager.from_dict(data["interview_data"])
                except Exception:
                    # Reinitialize if load fails
                    self._interview_manager = create_interview_manager() if INTERVIEW_AVAILABLE else None
            
            # Load coach data
            if COACHES_AVAILABLE and "coach_data" in data and data["coach_data"]:
                try:
                    self._coach_system = CoachSystem.from_dict(data["coach_data"])
                except Exception:
                    # Reinitialize if load fails
                    if not self._coach_system:
                        self._coach_system = CoachSystem() if COACHES_AVAILABLE else None
            
            # Load division ladder data
            if LADDER_AVAILABLE and "ladder_data" in data and data["ladder_data"]:
                try:
                    self._division_ladder = DivisionLadder.from_dict(data["ladder_data"])
                except Exception:
                    # Reinitialize if load fails
                    if not self._division_ladder:
                        self._division_ladder = DivisionLadder() if LADDER_AVAILABLE else None
            
            # Load inbox data
            if INBOX_AVAILABLE and "inbox_data" in data and data["inbox_data"]:
                try:
                    self._inbox = InboxSystem.from_dict(data["inbox_data"])
                except Exception:
                    # Reinitialize if load fails
                    if not self._inbox:
                        self._inbox = InboxSystem() if INBOX_AVAILABLE else None
            
            # Load belt history data
            if "belt_history_data" in data and data["belt_history_data"]:
                try:
                    from simulation.world_init import BeltHistory
                    self._belt_history = BeltHistory.from_dict(data["belt_history_data"])
                except Exception:
                    # Belt history is optional, don't fail if missing
                    self._belt_history = None
            
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
        """Handle new game creation with region, coach, and prospect selection."""
        clear_screen()
        print_header("NEW GAME")
        
        # Step 1: Region Selection (was step 2)
        selected_region = self._select_starting_region()
        if not selected_region:
            return
        
        # Step 2: Ranking Mode Selection
        ranking_mode = self._select_ranking_mode()
        if ranking_mode is None:
            return
        
        # Step 3: Coach selection - camp name comes from coach
        selected_coach = self._select_starting_coach()
        
        if selected_coach is None:
            print("Coach selection cancelled.")
            pause()
            return
        
        # Generate camp name from coach's last name
        coach_last_name = selected_coach.name.split()[-1] if selected_coach else "Unknown"
        camp_name = f"{coach_last_name}'s MMA"
        player_name = coach_last_name  # Use coach name as "player" name
        
        # Step 4: Prospect Draft (if game_start available)
        signed_prospects = []
        remaining_budget = 100000
        
        if GAME_START_AVAILABLE and GameStartManager:
            self._game_start_manager = GameStartManager()
            self._game_start_manager.set_camp_info(camp_name, selected_region)
            self._game_start_manager.generate_prospects()
            
            # Run the draft
            self._draft_starting_prospects()
            
            signed_prospects = self._game_start_manager.signed_prospects
            remaining_budget = self._game_start_manager.current_balance
        
        # Step 5: Confirmation
        print()
        coach_name = selected_coach.name if selected_coach else "None"
        # Handle both string specialty (StartingCoach) and enum specialty (Coach)
        if selected_coach:
            spec = selected_coach.specialty
            coach_specialty = spec.value if hasattr(spec, 'value') else str(spec)
        else:
            coach_specialty = "None"
        
        lines = [
            f"Camp: {camp_name}",
            f"Region: {selected_region}",
            f"Ranking Mode: {'Realistic (earn rankings)' if ranking_mode == 'realistic' else 'By Rating (start ranked)'}",
            f"Head Coach: {coach_name} ({coach_specialty})",
            "",
        ]
        
        if signed_prospects:
            lines.append(f"ROSTER: ({len(signed_prospects)} fighters)")
            for p in signed_prospects:
                wc_abbrev = self._get_division_abbrev(p.weight_class)
                lines.append(f"  * {p.name} ({wc_abbrev}) - {p.overall_rating} OVR")
            lines.append("")
            lines.append(f"Remaining Budget: ${remaining_budget:,}")
        else:
            lines.append("ROSTER: (empty - sign free agents after game starts)")
        
        print_box(lines, title="CONFIRM NEW GAME")
        
        if confirm("Begin your dynasty?"):
            self.start_new_game(player_name, camp_name, selected_coach, 
                               signed_prospects=signed_prospects,
                               starting_region=selected_region,
                               starting_budget=remaining_budget,
                               ranking_mode=ranking_mode)
    
    def _select_starting_region(self) -> Optional[str]:
        """Let player select their starting region."""
        clear_screen()
        print_header("SELECT YOUR REGION")
        
        print()
        print("  Your region affects which countries your prospects come from.")
        print("  You'll also have better access to fighters from your region.")
        print()
        print_divider()
        print()
        
        regions = [
            ("Americas", "[N/S America]", "USA, Brazil, Mexico, Canada", Colors.GREEN),
            ("Europe", "[Europe]", "Russia, UK, Ireland, Poland, France", Colors.BLUE),
            ("Asia-Pacific", "[Asia-Pacific]", "Japan, China, Korea, Australia, Thailand", Colors.RED),
        ]
        
        for i, (name, icon, countries, color) in enumerate(regions, 1):
            print(f"  [{i}] {icon} {colored(name, color)}")
            print(f"      {countries}")
            print()
        
        print(f"  [0] Cancel")
        print()
        
        choice = get_input("Select region: ")
        
        try:
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= 3:
                selected = regions[idx - 1][0]
                print()
                print(f"  {colored('[OK]', Colors.GREEN)} {selected} selected!")
                pause()
                return selected
        except ValueError:
            pass
        
        return "Americas"  # Default
    
    def _select_ranking_mode(self) -> Optional[str]:
        """Let player choose how rankings work at game start."""
        clear_screen()
        print_header("RANKING MODE")
        
        print()
        print("  How should fighters be ranked at the start?")
        print()
        print_divider()
        print()
        
        print(f"  [{colored('1', Colors.GREEN)}] {colored('Realistic', Colors.HIGHLIGHT)}")
        print(f"      Your drafted fighters start unranked (0-0 record).")
        print(f"      Earn your rankings through wins against the established roster.")
        print(f"      {colored('Recommended for authentic experience.', Colors.DIM)}")
        print()
        
        print(f"  [{colored('2', Colors.CYAN)}] {colored('By Rating', Colors.HIGHLIGHT)}")
        print(f"      All fighters ranked by OVR rating.")
        print(f"      Your high-rated prospects begin in contender positions.")
        print(f"      {colored('Faster path to title fights.', Colors.DIM)}")
        print()
        
        print(f"  [0] Cancel")
        print()
        
        choice = get_input("Select mode: ")
        
        try:
            idx = int(choice)
            if idx == 0:
                return None
            if idx == 1:
                print()
                print(f"  {colored('[OK]', Colors.GREEN)} Realistic mode - your fighters start unranked!")
                pause()
                return "realistic"
            if idx == 2:
                print()
                print(f"  {colored('[OK]', Colors.GREEN)} Rating mode - fighters ranked by OVR!")
                pause()
                return "by_rating"
        except ValueError:
            pass
        
        return "realistic"  # Default
    
    def _draft_starting_prospects(self) -> None:
        """Let player draft from starting prospects - 9 prospects, one per weight class."""
        if not self._game_start_manager:
            return
        
        max_roster = 3  # GARAGE tier max
        
        while True:
            clear_screen()
            print_header("DRAFT YOUR ROSTER")
            
            mgr = self._game_start_manager
            signed = len(mgr.signed_prospects)
            
            # Header info
            print()
            print(f"  {colored('[$] Budget:', Colors.GOLD)} ${mgr.current_balance:,}")
            print(f"  {colored('[*] Roster:', Colors.CYAN)} {signed}/{max_roster} fighters")
            if mgr.refreshes_used < 3:
                print(f"  {colored('[R] Refreshes:', Colors.DIM)} {3 - mgr.refreshes_used} remaining")
            print()
            print_divider()
            
            if not mgr.prospects:
                print()
                print(f"  {colored('No more prospects available!', Colors.YELLOW)}")
                print()
                if mgr.refreshes_used < 3:
                    print(f"  [R] Refresh prospect pool ({3 - mgr.refreshes_used} left)")
                print(f"  [D] Done drafting")
                print()
                
                choice = get_input("  > ").upper()
                if choice == 'R' and mgr.refreshes_used < 3:
                    mgr.refresh_prospects()
                    continue
                elif choice == 'D':
                    break
                continue
            
            # Sort by potential grade then overall (best prospects first)
            sorted_prospects = sorted(
                mgr.prospects,
                key=lambda p: (
                    {"Elite": 0, "High": 1, "Average": 2, "Limited": 3}.get(p.potential_grade, 4),
                    -p.overall_rating
                )
            )
            
            # Show prospects - one per weight class, sorted by potential
            print()
            print(f"  {colored('AVAILABLE PROSPECTS:', Colors.HIGHLIGHT)} (sorted by potential)")
            print()
            
            # Potential grade styling
            grade_icons = {
                "Elite": "[*]",
                "High": "[!]",
                "Average": "[=]",
                "Limited": "[-]",
            }
            grade_colors = {
                "Elite": Colors.GOLD,
                "High": Colors.GREEN,
                "Average": Colors.CYAN,
                "Limited": Colors.DIM,
            }
            
            # Fighting style descriptions
            style_descriptions = {
                "Orthodox Boxer": "Stand-up focus, strong hands",
                "Muay Thai": "Kicks, knees, clinch striking",
                "Wrestler": "Takedowns, control, ground & pound",
                "BJJ Specialist": "Submissions, guard work",
                "Kickboxer": "Distance striking, kicks",
                "Sambo": "Combat grappling, leg locks",
                "Karate": "Point fighting, explosive strikes",
                "Brawler": "Power punches, durability",
                "Pressure Fighter": "Forward pressure, volume",
                "Counter Striker": "Timing, precision counters",
                "Ground & Pound": "Top control, ground strikes",
                "Submission Artist": "Chokes, joint locks specialist",
            }
            
            for i, prospect in enumerate(sorted_prospects[:9], 1):
                grade_color = grade_colors.get(prospect.potential_grade, Colors.NEUTRAL)
                grade_icon = grade_icons.get(prospect.potential_grade, "")
                wc_abbrev = self._get_division_abbrev(prospect.weight_class)
                
                # Can afford indicator
                can_afford = prospect.estimated_cost <= mgr.current_balance
                afford_indicator = colored("$", Colors.GREEN) if can_afford else colored("$", Colors.RED)
                
                # Style description
                style_desc = style_descriptions.get(prospect.fighting_style, "")
                style_str = f"{prospect.fighting_style}"
                if style_desc:
                    style_str += f" - {colored(style_desc, Colors.DIM)}"
                
                # Main line
                print(f"  [{i}] {colored(prospect.name, Colors.HIGHLIGHT)} {colored(f'({wc_abbrev})', Colors.DIM)}")
                
                # Details line
                print(f"      {prospect.age}yo | {prospect.country}")
                print(f"      Style: {style_str}")
                
                # Ratings line
                potential_str = f"{grade_icon} {colored(prospect.potential_grade, grade_color)} (ceiling: {prospect.potential_ceiling})"
                print(f"      OVR: {colored(str(prospect.overall_rating), Colors.HIGHLIGHT)} | {potential_str}")
                
                # Cost line
                print(f"      {afford_indicator} Est. Cost: ${prospect.estimated_cost:,}")
                
                # Traits
                if prospect.traits:
                    traits_str = ", ".join(prospect.traits[:2])
                    print(f"      Traits: {colored(traits_str, Colors.MAGENTA)}")
                
                print()
            
            print_divider()
            
            # Navigation options
            nav_parts = []
            if signed < max_roster:
                nav_parts.append("[#] View & Sign")
            if mgr.refreshes_used < 3:
                nav_parts.append(f"[R] Refresh (${mgr.refresh_cost:,})")
            nav_parts.append("[D] Done")
            print(f"  {' | '.join(nav_parts)}")
            print()
            
            choice = get_input("  > ").upper()
            
            if choice == 'D':
                if signed == 0:
                    if confirm("  Start with no fighters? (You can sign free agents later)"):
                        break
                else:
                    break
            elif choice == 'R' and mgr.refreshes_used < 3:
                if mgr.current_balance >= mgr.refresh_cost:
                    mgr.refresh_prospects()
                else:
                    print(f"  {colored('Cannot afford refresh!', Colors.RED)}")
                    pause()
            else:
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(sorted_prospects[:9]):
                        prospect = sorted_prospects[idx - 1]
                        self._view_and_sign_prospect(prospect)
                except ValueError:
                    pass
    
    def _view_and_sign_prospect(self, prospect) -> None:
        """View prospect details and optionally sign them."""
        if not self._game_start_manager:
            return
        
        mgr = self._game_start_manager
        
        clear_screen()
        print_header(f"PROSPECT: {prospect.name.upper()}")
        
        # Grade styling
        grade_colors = {
            "Elite": Colors.GOLD,
            "High": Colors.GREEN,
            "Average": Colors.CYAN,
            "Limited": Colors.DIM,
        }
        grade_color = grade_colors.get(prospect.potential_grade, Colors.NEUTRAL)
        
        # Bio section
        print()
        print(f"  {colored('*** BIO ***', Colors.CYAN)}")
        print(f"    Age: {prospect.age}")
        print(f"    Country: {prospect.country}")
        print(f"    Weight Class: {prospect.weight_class}")
        print(f"    Style: {prospect.fighting_style}")
        print()
        
        # Ratings section
        print(f"  {colored('*** RATINGS ***', Colors.CYAN)}")
        print(f"    Overall: {colored(str(prospect.overall_rating), Colors.HIGHLIGHT)}")
        print(f"    Potential: {colored(prospect.potential_grade, grade_color)} (ceiling: {prospect.potential_ceiling})")
        print()
        
        # Attributes section (17 total)
        print(f"  {colored('*** ATTRIBUTES ***', Colors.CYAN)}")
        print(f"    {colored('Physical:', Colors.GREEN)}")
        print(f"      Strength {prospect.strength} | Speed {prospect.speed} | Cardio {prospect.cardio}")
        print(f"      Chin {prospect.chin} | Recovery {prospect.recovery}")
        print(f"    {colored('Striking:', Colors.RED)}")
        print(f"      Boxing {prospect.boxing} | Kicks {prospect.kicks} | Clinch {prospect.clinch_striking}")
        print(f"      Defense {prospect.striking_defense}")
        print(f"    {colored('Grappling:', Colors.BLUE)}")
        print(f"      Takedowns {prospect.takedowns} | TD Def {prospect.takedown_defense}")
        print(f"      Top Control {prospect.top_control} | Submissions {prospect.submissions} | Guard {prospect.guard}")
        print(f"    {colored('Mental:', Colors.MAGENTA)}")
        print(f"      Heart {prospect.heart} | IQ {prospect.fight_iq} | Composure {prospect.composure}")
        print()
        
        # Traits
        if prospect.traits:
            print(f"  {colored('*** TRAITS ***', Colors.CYAN)}")
            for trait in prospect.traits:
                print(f"    * {colored(trait, Colors.MAGENTA)}")
            print()
        
        # Contract demands
        print(f"  {colored('*** CONTRACT DEMANDS ***', Colors.CYAN)}")
        sign_min, sign_max = prospect.signing_bonus_range
        purse_min, purse_max = prospect.base_purse_range
        win_min, win_max = prospect.win_bonus_range
        
        print(f"    Signing Bonus: ${sign_min:,} - ${sign_max:,}")
        print(f"    Base Purse: ${purse_min:,} - ${purse_max:,}")
        print(f"    Win Bonus: ${win_min:,} - ${win_max:,}")
        print()
        print(f"    {colored(f'Estimated Total Cost: ${prospect.estimated_cost:,}', Colors.GOLD)}")
        print()
        
        # Check if can afford and sign
        can_afford = prospect.estimated_cost <= mgr.current_balance
        can_sign = mgr.can_sign_more()
        
        print_divider()
        
        if not can_sign:
            print(f"  {colored('[X] ROSTER FULL', Colors.RED)} - Cannot sign more fighters (max 5)")
        elif not can_afford:
            print(f"  {colored('[X] CANNOT AFFORD', Colors.RED)} - Need ${prospect.estimated_cost:,}, have ${mgr.current_balance:,}")
        else:
            print(f"  [{colored('S', Colors.GREEN)}] Sign this prospect (${prospect.estimated_cost:,})")
        
        print(f"  [{colored('0', Colors.CYAN)}] Back to list")
        print()
        
        choice = get_input("  > ").upper()
        
        if choice == 'S' and can_afford and can_sign:
            success = mgr.sign_prospect(prospect, prospect.estimated_cost)
            if success:
                print()
                print(f"  {colored('[OK] SIGNED!', Colors.GREEN)} {prospect.name} joins your camp!")
                print(f"  Remaining budget: ${mgr.current_balance:,}")
                pause()
    
    def _select_starting_coach(self):
        """Let player select their starting head coach from a varied pool."""
        clear_screen()
        print_header("SELECT YOUR HEAD COACH")
        
        print()
        print("  Every camp needs a leader. Choose your head coach wisely.")
        print("  They'll guide your fighters' development and corner them in fights.")
        print()
        
        # Generate coach options - try game_start first for varied pool
        coach_options = []
        using_starting_coaches = False
        
        try:
            from systems.game_start import generate_starting_coaches
            starting_coaches = generate_starting_coaches(num_coaches=10)
            
            if starting_coaches:
                using_starting_coaches = True
                coach_options = starting_coaches
        except ImportError:
            pass
        
        # Fallback to coaches module if game_start unavailable
        if not coach_options and COACHES_AVAILABLE:
            try:
                from systems.coaches import generate_coach, CoachSpecialty
                
                # Generate varied options with random specialties
                all_specialties = list(CoachSpecialty)
                for _ in range(8):
                    specialty = random.choice(all_specialties)
                    quality = random.choice([2, 2, 2, 3, 3])  # Mostly 2-star
                    coach = generate_coach(quality=quality, specialty=specialty)
                    coach_options.append(coach)
                    
            except Exception as e:
                print(f"  {colored('Coach generation unavailable', Colors.RED)}")
                print(f"  {colored(f'Error: {e}', Colors.DIM)}")
                pause()
                return None
        
        if not coach_options:
            print(f"  {colored('No coaches available', Colors.RED)}")
            pause()
            return None
        
        print_divider()
        print()
        
        for i, coach in enumerate(coach_options, 1):
            if using_starting_coaches:
                # StartingCoach format from game_start.py
                specialty = coach.specialty
                skill = coach.skill_level
                salary = coach.weekly_salary
                stars = skill // 20  # Convert skill to stars (55-82 -> 2-4 stars)
                stars_str = "*" * stars + "-" * (5 - stars)
                
                specialty_colors = {
                    "Striking": Colors.RED,
                    "Wrestling": Colors.BLUE,
                    "BJJ": Colors.MAGENTA,
                    "Conditioning": Colors.GREEN,
                    "Strength": Colors.ORANGE,
                    "Cornering": Colors.CYAN,
                }
                spec_color = specialty_colors.get(specialty, Colors.NEUTRAL)
                
                print(f"  [{i}] {colored(coach.name, Colors.HIGHLIGHT)}")
                print(f"      {colored(specialty, spec_color)} | Skill: {skill} | ${salary:,}/week")
                print(f"      Training: {colored(f'+{int(coach.training_bonus * 100)}%', Colors.GREEN)} {specialty.lower()} development")
                
                # Display traits (1-2 per coach)
                if hasattr(coach, 'traits') and coach.traits:
                    from systems.game_start import get_coach_trait_description
                    traits_info = []
                    for trait in coach.traits:
                        desc = get_coach_trait_description(trait)
                        traits_info.append(f"{colored(trait, Colors.CYAN)}: {desc}")
                    for trait_line in traits_info:
                        print(f"      {trait_line}")
                elif hasattr(coach, 'personality_trait') and coach.personality_trait:
                    # Legacy single trait support
                    print(f"      {colored(coach.personality_trait, Colors.CYAN)}: {getattr(coach, 'personality_desc', '')}")
            else:
                # Coach format from coaches.py
                stars = "*" * coach.stars + "-" * (5 - coach.stars)
                specialty = coach.specialty.value if hasattr(coach.specialty, 'value') else str(coach.specialty)
                salary = getattr(coach, 'weekly_salary', coach.stars * 500)
                
                # Get trait descriptions
                trait_descs = {
                    "Motivator": "Boosts fighters with low morale",
                    "Technical Genius": "+15% technique training",
                    "Diamond Polisher": "+25% bonus training prospects",
                    "Veteran's Touch": "+20% bonus training veterans",
                    "Iron Sharpener": "+10% sparring effectiveness",
                    "Calm Corner": "+10% composure & recovery between rounds",
                    "Taskmaster": "+15% training, may hurt morale",
                    "Player's Coach": "+5 morale, slightly slower training",
                    "Analytical": "+15% gameplan effectiveness",
                    "Old School": "+20% conditioning focus",
                    "Modern Methods": "+15% bonus with young fighters",
                    "Burned Out": "-15% training effectiveness",
                    "Outdated Methods": "Struggles with young fighters",
                }
                
                traits_str = ""
                if coach.traits:
                    trait_info = []
                    for t in coach.traits[:2]:
                        name = t.value if hasattr(t, 'value') else str(t)
                        desc = trait_descs.get(name, "")
                        if desc:
                            trait_info.append(f"{name} ({desc})")
                        else:
                            trait_info.append(name)
                    traits_str = " | ".join(trait_info)
                
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
                print(f"      {colored(specialty, spec_color)} | [{stars}] | ${salary:,}/week")
                
                bonus_pct = int((coach.quality_multiplier - 1) * 100)
                if bonus_pct > 0:
                    print(f"      Training: {colored(f'+{bonus_pct}%', Colors.GREEN)} {specialty.lower()} development")
                if traits_str:
                    print(f"      {colored('Traits:', Colors.DIM)} {traits_str}")
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
                name = selected.name
                print()
                print(f"  {colored('[OK]', Colors.GREEN)} {name} is ready to lead {colored('your camp', Colors.HIGHLIGHT)}!")
                pause()
                
                # StartingCoach now has to_dict() so it can be used directly
                # Coach.from_dict() can also handle StartingCoach data format
                return selected
        except ValueError:
            pass
        
        return None
    
    def start_new_game(self, player_name: str, camp_name: str, starting_coach=None,
                        signed_prospects=None, starting_region=None, starting_budget=None,
                        ranking_mode: str = "realistic") -> None:
        """Initialize and start a new game with selected coach and drafted prospects."""
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
            
            # Ensure coach system exists before assigning starting coach
            if not self._coach_system and COACHES_AVAILABLE:
                try:
                    self._coach_system = CoachSystem()
                    print(f"[OK] Initialized coach system")
                except:
                    pass
            
            # Assign starting coach to player camp
            if starting_coach and COACHES_AVAILABLE and self._coach_system:
                player_camp = self.game_state.get_player_camp()
                if player_camp:
                    import uuid
                    
                    # Ensure we have proper coach attributes
                    coach_id = getattr(starting_coach, 'coach_id', None)
                    if not coach_id:
                        coach_id = str(uuid.uuid4())[:8]
                        starting_coach.coach_id = coach_id
                    
                    coach_name = getattr(starting_coach, 'name', 'Head Coach')
                    
                    # Set required attributes
                    starting_coach.camp_id = player_camp.camp_id
                    starting_coach.is_head_coach = True
                    
                    # Add coach to system's coach registry
                    # StartingCoach now has to_dict() so it can be serialized
                    self._coach_system._coaches[coach_id] = starting_coach
                    
                    # Track in camp_coaches mapping
                    if player_camp.camp_id not in self._coach_system._camp_coaches:
                        self._coach_system._camp_coaches[player_camp.camp_id] = []
                    
                    # Only add if not already present
                    if coach_id not in self._coach_system._camp_coaches[player_camp.camp_id]:
                        self._coach_system._camp_coaches[player_camp.camp_id].append(coach_id)
                    
                    print(f"[OK] {coach_name} joins as your Head Coach")
            elif starting_coach and not self._coach_system:
                print(f"[!] Warning: Could not assign coach - coach system unavailable")
            
            # Generate full data for all fighters
            for fighter_id in self.game_state.fighters:
                self._create_full_fighter_data(fighter_id)
            
            # Get next event number from world initializer (continues DFC numbering)
            if hasattr(initializer, 'get_next_event_number'):
                self.next_event_number = initializer.get_next_event_number()
                print(f"[OK] Next event: DFC {self.next_event_number}")
            
            # Get belt history from world initializer
            if hasattr(initializer, 'get_belt_history'):
                self._belt_history = initializer.get_belt_history()
                if self._belt_history:
                    print(f"[OK] Belt history loaded")
            
        except ImportError:
            print("(Using simplified world generation)")
            counts = self.game_state.initialize_world(
                num_ai_camps=20,
                fighters_per_division=15,
                generate_history=True,
            )
            print(f"[OK] Created {counts['fighters']} fighters")
            print(f"[OK] Created {counts['camps']} AI camps")
        
        # Create fighters from signed prospects
        if signed_prospects:
            player_camp = self.game_state.get_player_camp()
            if player_camp:
                for prospect in signed_prospects:
                    self._create_fighter_from_prospect(prospect, player_camp.camp_id)
                print(f"[OK] {len(signed_prospects)} fighters signed to your roster")
        
        # Set starting budget if provided
        if starting_budget is not None and ECONOMY_AVAILABLE and self._economy_manager:
            player_camp = self.game_state.get_player_camp()
            if player_camp:
                # Adjust balance to match remaining budget from draft
                self._economy_manager.set_camp_balance(player_camp.camp_id, starting_budget)
        
        # IMPORTANT: Repopulate rankings system now that fighters exist
        # This must happen AFTER world init creates fighters but BEFORE ranking mode check
        if RANKINGS_AVAILABLE and self._rankings_system:
            self._populate_rankings_system()
        
        # Sync champion flags with division state (fixes any inconsistencies)
        self._sync_champion_flags()
        
        # Apply ranking mode
        if ranking_mode == "realistic":
            # Keep rankings only for fighters who earned them through simulated history
            # 0-0 fighters (like player's drafted prospects) start unranked
            self._apply_realistic_rankings()
            print(f"[OK] Realistic mode - your fighters start unranked, earn your way up!")
        
        print()
        pause()
        
        self._schedule_initial_events()
        
        self.in_game = True
        
        # Only run pick_starting_fighter if no prospects were drafted
        if not signed_prospects:
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
    
    def _apply_realistic_rankings(self) -> None:
        """
        Apply realistic ranking mode.
        
        In realistic mode:
        - Champions keep their spot (they earned it)
        - Rankings from simulated history are KEPT (fighters earned those too)
        - 0-0 fighters (like drafted prospects) remain unranked
        - New fighters must earn their rankings through wins
        
        This differs from "By Rating" mode which ranks by OVR regardless of record.
        """
        # In realistic mode, we keep the rankings that were built during 
        # the history simulation - those fighters EARNED their spots.
        # We only need to ensure 0-0 fighters don't get ranked.
        
        if RANKINGS_AVAILABLE and self._rankings_system:
            try:
                from core.types import WeightClass
                
                # For each division, remove any 0-0 fighters from rankings
                for wc in self._rankings_system._divisions:
                    div_rankings = self._rankings_system._divisions.get(wc)
                    if div_rankings and hasattr(div_rankings, 'rankings'):
                        # Filter out 0-0 fighters (keep champion and anyone with fights)
                        filtered = []
                        for entry in div_rankings.rankings:
                            fighter = self.game_state.fighters.get(entry.fighter_id)
                            if fighter:
                                total_fights = fighter.wins + fighter.losses
                                # Keep champion (rank 0) OR fighters with fight history
                                if entry.rank == 0 or total_fights > 0:
                                    filtered.append(entry)
                        div_rankings.rankings = filtered
                        
                        # Renumber ranks (champion stays 0, others get 1-15)
                        rank_num = 1
                        for entry in div_rankings.rankings:
                            if entry.rank != 0:  # Don't change champion rank
                                entry.rank = rank_num
                                rank_num += 1
            except Exception:
                pass
        
        # Also update division state rankings lists
        for wc, division in self.game_state.divisions.items():
            if hasattr(division, 'rankings'):
                # Filter to only fighters with fight history
                filtered = []
                for fid in division.rankings:
                    fighter = self.game_state.fighters.get(fid)
                    if fighter and (fighter.wins + fighter.losses) > 0:
                        filtered.append(fid)
                division.rankings = filtered[:15]  # Keep top 15
    
    def _create_fighter_from_prospect(self, prospect, camp_id: str) -> Optional[str]:
        """Create a FighterRecord from a StartingProspect and add to game state."""
        from core.game_state import FighterRecord
        
        # Generate unique fighter ID
        fighter_id = f"prospect_{prospect.prospect_id}"
        
        # Create FighterRecord (lightweight - only core fields)
        fighter_record = FighterRecord(
            fighter_id=fighter_id,
            name=prospect.name,
            nickname=getattr(prospect, 'nickname', None) or None,
            weight_class=prospect.weight_class,
            camp_id=camp_id,
            is_champion=False,
            is_active=True,
            overall_rating=prospect.overall_rating,
            wins=0,
            losses=0,
            draws=0,
            ko_wins=0,
            sub_wins=0,
        )
        
        # Add to game state
        self.game_state.fighters[fighter_id] = fighter_record
        
        # Create full fighter data for detailed tracking
        full_data = FighterFullData(
            fighter_id=fighter_id,
            name=prospect.name,
            nickname=getattr(prospect, 'nickname', None),
            age=prospect.age,
            country=prospect.country,
            weight_class=prospect.weight_class,
            fighting_style=prospect.fighting_style,
            camp_id=camp_id,
            is_champion=False,
            is_active=True,
            wins=0,
            losses=0,
            draws=0,
            ko_wins=0,
            sub_wins=0,
            # Physical attributes (5)
            strength=prospect.strength,
            speed=prospect.speed,
            cardio=prospect.cardio,
            chin=getattr(prospect, 'chin', 70),
            recovery=getattr(prospect, 'recovery', 65),
            # Striking (4)
            boxing=prospect.boxing,
            kicks=prospect.kicks,
            clinch_striking=getattr(prospect, 'clinch_striking', 60),
            striking_defense=prospect.striking_defense,
            # Grappling (5)
            takedowns=getattr(prospect, 'takedowns', 60),
            takedown_defense=prospect.takedown_defense,
            top_control=getattr(prospect, 'top_control', 60),
            submissions=getattr(prospect, 'submissions', 60),
            guard=getattr(prospect, 'guard', 60),
            # Mental (3)
            heart=prospect.heart,
            fight_iq=prospect.fight_iq,
            composure=prospect.composure,
            # Traits
            traits=prospect.traits if prospect.traits else [],
        )
        
        self.fighter_data[fighter_id] = full_data
        
        return fighter_id
    
    def _schedule_initial_events(self) -> None:
        """Schedule first AI events with staggered title fights."""
        # Initialize title fight cooldowns - stagger across divisions
        # This prevents all 9 title fights from happening at once
        if not hasattr(self, '_title_fight_cooldowns'):
            self._title_fight_cooldowns = {}
        
        weight_classes = list(self.game_state.divisions.keys())
        random.shuffle(weight_classes)
        
        # Stagger initial cooldowns: first 2 divisions have 0, next 2 have 2, etc.
        for i, wc in enumerate(weight_classes):
            # Spread cooldowns: 0, 0, 2, 2, 4, 4, 6, 6, 8
            cooldown = (i // 2) * 2
            self._title_fight_cooldowns[wc] = cooldown
        
        # Schedule events at weeks 2, 4, 6, 8, 10
        # With staggered cooldowns, title fights will be spread across events
        for weeks in [2, 4, 6, 8, 10]:
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
        
        # Sort by ELO-lite: win%, wins, rating
        def elo_lite_key(f):
            total = f.wins + f.losses
            win_pct = f.wins / total if total > 0 else 0
            return (win_pct, f.wins, getattr(f, 'overall_rating', 0))
        all_available.sort(key=elo_lite_key, reverse=True)
        
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
            
            # Set initial popularity based on overall rating if not already set
            fdata = self.fighter_data[fighter_id]
            if fdata.popularity <= 10:  # Default or unset
                ovr = fdata.overall_rating
                if ovr >= 80:
                    fdata.popularity = random.randint(25, 40)  # Elite
                elif ovr >= 70:
                    fdata.popularity = random.randint(15, 30)  # Top
                elif ovr >= 60:
                    fdata.popularity = random.randint(10, 20)  # Good
                else:
                    fdata.popularity = random.randint(5, 12)  # Average/developing
                self._sync_fighter_record(fighter_id)
        
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
                    # Physical (5)
                    strength=gen.strength,
                    speed=gen.speed,
                    cardio=gen.cardio,
                    chin=gen.chin,
                    recovery=gen.recovery,
                    # Striking (4)
                    boxing=gen.boxing,
                    kicks=gen.kicks,
                    clinch_striking=gen.clinch_striking,
                    striking_defense=gen.striking_defense,
                    # Grappling (5)
                    takedowns=gen.takedowns,
                    takedown_defense=gen.takedown_defense,
                    top_control=gen.top_control,
                    submissions=gen.submissions,
                    guard=gen.guard,
                    # Mental (3)
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
                    # Physical (5)
                    strength=base_rating + random.randint(-10, 10),
                    speed=base_rating + random.randint(-10, 10),
                    cardio=base_rating + random.randint(-10, 10),
                    chin=base_rating + random.randint(-10, 10),
                    recovery=base_rating + random.randint(-10, 10),
                    # Striking (4)
                    boxing=base_rating + random.randint(-10, 10),
                    kicks=base_rating + random.randint(-10, 10),
                    clinch_striking=base_rating + random.randint(-10, 10),
                    striking_defense=base_rating + random.randint(-10, 10),
                    # Grappling (5)
                    takedowns=base_rating + random.randint(-10, 10),
                    takedown_defense=base_rating + random.randint(-10, 10),
                    top_control=base_rating + random.randint(-10, 10),
                    submissions=base_rating + random.randint(-10, 10),
                    guard=base_rating + random.randint(-10, 10),
                    # Mental (3)
                    heart=base_rating + random.randint(-10, 10),
                    fight_iq=base_rating + random.randint(-10, 10),
                    composure=base_rating + random.randint(-10, 10),
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
        print(f"    Boxing:      {self._attr_bar(prospect.boxing)}")
        print(f"    Kicks:       {self._attr_bar(prospect.kicks)}")
        print(f"    Takedowns:   {self._attr_bar(prospect.takedowns)}")
        print(f"    Submissions: {self._attr_bar(prospect.submissions)}")
        print(f"    Cardio:      {self._attr_bar(prospect.cardio)}")
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
        
        # =================================================================
        # DOPAMINE: SIGNING CELEBRATION
        # =================================================================
        print()
        
        # Determine signing excitement level based on potential
        potential = getattr(prospect, 'potential_ceiling', prospect.overall_rating + 10)
        rating = prospect.overall_rating
        
        if potential >= 90:
            print(f"  {colored('*** ELITE PROSPECT SIGNED! ***', Colors.GOLD)}")
            print(f"  {colored(prospect.name, Colors.HIGHLIGHT)} joins your camp!")
            print(f"  {colored(f'Ceiling: {potential} OVR - A FUTURE STAR!', Colors.GOLD)}")
        elif potential >= 80:
            print(f"  {colored('** TOP PROSPECT SIGNED! **', Colors.CYAN)}")
            print(f"  {colored(prospect.name, Colors.HIGHLIGHT)} joins your camp!")
            print(f"  {colored(f'Ceiling: {potential} OVR - High potential!', Colors.CYAN)}")
        elif rating >= 75:
            print(f"  {colored('* VETERAN ACQUIRED! *', Colors.GREEN)}")
            print(f"  {colored(prospect.name, Colors.HIGHLIGHT)} joins your camp!")
            print(f"  {colored(f'Ready to compete immediately!', Colors.GREEN)}")
        else:
            print(f"  {colored('[OK] SIGNED!', Colors.WIN)} {prospect.name} joins your camp!")
        
        print()
        
        # Quick stats summary
        div = self._get_division_abbrev(prospect.weight_class)
        print(f"  {div} | {rating} OVR | Potential: {potential}")
        print()
        
        # Show development recommendation
        if SCOUTING_AVAILABLE:
            try:
                report = scout_fighter(prospect, is_prospect=True)
                if report.development_focus:
                    print(colored("  [#] DEVELOPMENT PLAN:", Colors.CYAN))
                    for focus in report.development_focus[:2]:
                        print(f"    ^ {focus}")
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
                self._sync_champion_flags()  # Ensure fighter.is_champion matches division state
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
                    self._sync_champion_flags()  # Ensure fighter.is_champion matches division state
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
        
        # Sync balance from economy manager (authoritative source)
        if self._economy_manager and ECONOMY_AVAILABLE and player_camp:
            try:
                balance = self._economy_manager.get_balance(player_camp.camp_id)
                player_camp._balance = balance  # Keep camp object in sync
            except:
                balance = player_camp.balance if player_camp else 0
        else:
            balance = player_camp.balance if player_camp else 0
        
        # Calculate weekly burn rate
        weekly_burn = self._calculate_weekly_burn(player_camp.camp_id if player_camp else "")
        
        # Get head coach name
        head_coach_info = self._get_head_coach_info(player_camp.camp_id) if player_camp else {}
        head_coach_name = head_coach_info.get("name", "None")
        
        # Get roster info
        camp_fighters = [f for f in game.fighters.values() 
                        if getattr(f, 'camp_id', None) == player_camp.camp_id] if player_camp else []
        max_fighters = {"GARAGE": 5, "LOCAL": 10, "REGIONAL": 20, "NATIONAL": 35, "ELITE": 50}.get(tier, 5)
        
        # Camp record
        total_wins = sum(f.wins for f in camp_fighters)
        total_losses = sum(f.losses for f in camp_fighters)
        win_pct = int(total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        
        # Championships - use division state as source of truth
        champ_count = sum(1 for f in camp_fighters if self._is_division_champion(f))
        
        # Calculate runway (weeks until broke)
        if weekly_burn > 0:
            runway_weeks = balance // weekly_burn
            if runway_weeks > 20:
                runway_color = Colors.GREEN
            elif runway_weeks > 10:
                runway_color = Colors.YELLOW
            else:
                runway_color = Colors.RED
            burn_str = colored(f"(-${weekly_burn:,}/wk)", runway_color)
        else:
            burn_str = colored("(+ve)", Colors.GREEN)
        
        # Header with coach
        print(f"  {colored('=' * 68, Colors.CYAN)}")
        header_left = colored(camp_name.upper(), Colors.HIGHLIGHT)
        header_right = f"{tier} GYM"
        print(f"  {colored('|', Colors.CYAN)}  {header_left:<40} {colored(header_right, Colors.YELLOW):>22}  {colored('|', Colors.CYAN)}")
        
        # Coach line
        coach_line = f"Head Coach: {head_coach_name}"
        print(f"  {colored('|', Colors.CYAN)}  {colored(coach_line, Colors.DIM):<64}  {colored('|', Colors.CYAN)}")
        
        print(f"  {colored('+' + '=' * 66 + '+', Colors.CYAN)}")
        print(f"  {colored('|', Colors.CYAN)}  {date_str:<32} Week {game.week_number:<20}  {colored('|', Colors.CYAN)}")
        
        # Balance with burn rate
        balance_display = f"Balance: {colored(format_money(balance), Colors.WIN)} {burn_str}"
        roster_display = f"Roster: {len(camp_fighters)}/{max_fighters}"
        print(f"  {colored('|', Colors.CYAN)}  {balance_display:<45} {roster_display:<18}  {colored('|', Colors.CYAN)}")
        
        champ_str = colored(f"[C] {champ_count}", Colors.GOLD) if champ_count > 0 else "0"
        record_str = f"{total_wins}-{total_losses} ({win_pct}%)"
        print(f"  {colored('|', Colors.CYAN)}  Championships: {champ_str:<16} Camp Record: {record_str:<14}  {colored('|', Colors.CYAN)}")
        print(f"  {colored('=' * 68, Colors.CYAN)}")
        print()
        
        # =====================================================================
        # FIGHTER ROSTER SUMMARY - VITAL SIGNS + TRAINING GAINS
        # =====================================================================
        if camp_fighters:
            print(f"  {colored('YOUR FIGHTERS', Colors.CYAN)}")
            print(f"  {'-' * 66}")
            
            # Sort by: champions first, then by ELO-lite (win%, wins, rating)
            def camp_sort_key(f):
                is_champ = 1 if self._is_division_champion(f) else 0
                total = f.wins + f.losses
                win_pct = f.wins / total if total > 0 else 0
                return (is_champ, win_pct, f.wins, f.overall_rating)
            camp_fighters.sort(key=camp_sort_key, reverse=True)
            
            for fighter in camp_fighters[:5]:  # Show top 5
                # Get ranking
                rank_str = self._get_fighter_rank_str(fighter)
                
                # Get division abbreviation
                div_abbrev = self._get_division_abbrev(fighter.weight_class)
                
                # Get full data for vital signs
                full_data = self.fighter_data.get(fighter.fighter_id)
                
                # VITAL SIGNS
                fatigue = getattr(full_data, 'fatigue', 0) if full_data else 0
                win_streak = getattr(full_data, 'win_streak', 0) if full_data else 0
                lose_streak = getattr(full_data, 'lose_streak', 0) if full_data else 0
                
                # Fatigue indicator
                if fatigue <= 20:
                    fat_label = colored("Fresh", Colors.GREEN)
                elif fatigue <= 40:
                    fat_label = colored("Rested", Colors.CYAN)
                elif fatigue <= 60:
                    fat_label = colored("Ready", Colors.YELLOW)
                elif fatigue <= 80:
                    fat_label = colored("Tired", Colors.ORANGE)
                else:
                    fat_label = colored("GASSED", Colors.RED)
                
                # Form indicator (based on streaks)
                if win_streak >= 5:
                    form_icon = colored("[!][!]", Colors.GOLD)  # On fire
                elif win_streak >= 3:
                    form_icon = colored("[!]", Colors.ORANGE)  # Hot
                elif lose_streak >= 3:
                    form_icon = colored("*", Colors.BLUE)  # Cold
                elif lose_streak >= 2:
                    form_icon = colored("v", Colors.RED)  # Slipping
                elif win_streak >= 1:
                    form_icon = colored("^", Colors.GREEN)  # Rising
                else:
                    form_icon = colored("^", Colors.DIM)  # Steady
                
                # Format main line
                is_champ = self._is_division_champion(fighter)
                champ_icon = colored("[C] ", Colors.GOLD) if is_champ else "    "
                name_colored = colored(fighter.name, Colors.GOLD) if is_champ else fighter.name
                record = f"{fighter.wins}-{fighter.losses}"
                
                line = f"  {champ_icon}{name_colored:<18} {div_abbrev:>3}  {fighter.overall_rating:>2} OVR  {record:<6} {rank_str}"
                print(line)
                
                # Get enhanced training display
                training_status, gains_line, event_line = self._get_fighter_training_display(fighter, full_data)
                
                # LINE 2: VITAL SIGNS + TRAINING STATUS
                vital_parts = []
                
                # Injury takes priority over everything
                is_injured = False
                if INJURY_AVAILABLE and self._injury_system:
                    injury = self._injury_system.get_worst_injury(fighter.fighter_id)
                    if injury and injury.weeks_remaining > 0:
                        vital_parts = [colored(f"[!] INJURED: {injury.injury_type} ({injury.weeks_remaining}wks)", Colors.RED)]
                        is_injured = True
                
                if not is_injured:
                    # Training status (if in camp or recent camp)
                    if training_status:
                        vital_parts.append(training_status)
                    
                    # Fatigue
                    vital_parts.append(f"Fat: {fatigue}% ({fat_label})")
                    
                    # Form
                    vital_parts.append(f"Form: {form_icon}")
                    
                    # Upcoming fight
                    upcoming = self._get_fighter_upcoming_fight(fighter.fighter_id)
                    if upcoming:
                        vital_parts.append(upcoming)
                
                print(f"      {' | '.join(vital_parts)}")
                
                # LINE 3: TRAINING GAINS (if in camp)
                if gains_line and not is_injured:
                    print(f"      {gains_line}")
                
                # LINE 4: BREAKTHROUGH/SETBACK (if any)
                if event_line and not is_injured:
                    print(f"      {event_line}")
            
            if len(camp_fighters) > 5:
                print(f"      {colored(f'... and {len(camp_fighters) - 5} more', Colors.DIM)}")
            
            print(f"  {'-' * 66}")
            print()
        
        # =====================================================================
        # FIGHT WEEK ANTICIPATION (fights happening next week)
        # =====================================================================
        fight_week_alerts = []
        for fight in self.player_scheduled_fights:
            weeks_until = fight.get("weeks_until", 99)
            if weeks_until == 1:  # Fight is next week!
                fighter_name = fight.get("fighter1_name", "Your fighter")
                opponent_name = fight.get("fighter2_name", "opponent")
                
                # Random flavor text for fight week
                fight_week_flavors = [
                    f"{fighter_name} looking sharp in final preparations",
                    f"Final sparring sessions underway for {fighter_name}",
                    f"{fighter_name} making weight, ready for battle",
                    f"Camp confident heading into fight week",
                    f"{fighter_name} wrapping up training camp strong",
                    f"All eyes on {fighter_name} vs {opponent_name}",
                ]
                flavor = random.choice(fight_week_flavors)
                fight_week_alerts.append((fighter_name, opponent_name, flavor))
        
        if fight_week_alerts:
            print(f"  {colored('[!] FIGHT WEEK', Colors.ORANGE)}")
            for fighter_name, opponent_name, flavor in fight_week_alerts:
                print(f"      {colored(fighter_name, Colors.HIGHLIGHT)} vs {colored(opponent_name, Colors.RED)}")
                print(f"      {colored(f'"{flavor}"', Colors.DIM)}")
            print()
        
        # =====================================================================
        # ALERTS & WARNINGS (Inbox Integration)
        # =====================================================================
        scheduled_count = len(self.player_scheduled_fights)
        
        # Inbox-based alerts
        if INBOX_AVAILABLE and self._inbox:
            unread_count = self._inbox.get_unread_count()
            offer_count = self._inbox.get_count_by_type(NotificationType.FIGHT_OFFER)
            challenge_count = self._inbox.get_count_by_type(NotificationType.INCOMING_CHALLENGE)
            scout_count = self._inbox.get_count_by_type(NotificationType.SCOUT_REPORT)
            
            if unread_count > 0 or scheduled_count > 0:
                alert_parts = []
                
                # Priority notifications first
                if offer_count > 0:
                    alert_parts.append(colored(f"[S] {offer_count} fight offer{'s' if offer_count != 1 else ''}", Colors.YELLOW))
                if challenge_count > 0:
                    alert_parts.append(colored(f"[T] {challenge_count} challenge{'s' if challenge_count != 1 else ''}", Colors.ORANGE))
                if scout_count > 0:
                    alert_parts.append(colored(f"[>] {scout_count} scout report{'s' if scout_count != 1 else ''}", Colors.GREEN))
                if scheduled_count > 0:
                    alert_parts.append(colored(f"[C] {scheduled_count} fight{'s' if scheduled_count != 1 else ''} booked", Colors.CYAN))
                
                if alert_parts:
                    print(f"  {colored('[INBOX]', Colors.WHITE)} {' | '.join(alert_parts)}")
                    print()
        else:
            # Fallback to old style if inbox not available
            offer_count = len(self.fight_offers)
            if offer_count > 0 or scheduled_count > 0:
                alert_parts = []
                if offer_count > 0:
                    alert_parts.append(colored(f"[!] {offer_count} offer(s)", Colors.YELLOW))
                if scheduled_count > 0:
                    alert_parts.append(colored(f"[*] {scheduled_count} fight(s) booked", Colors.CYAN))
                print(f"  {' | '.join(alert_parts)}")
                print()
        
        # Check for injured fighters on roster
        injured_fighters = self._get_injured_roster_fighters(camp_fighters)
        if injured_fighters:
            print(f"  {colored('[!] INJURED:', Colors.RED)} ", end="")
            injury_strs = [f"{name} ({wks}wks)" for name, wks in injured_fighters[:3]]
            print(", ".join(injury_strs))
            print()
        
        # Check for upcoming title fights in your divisions
        player_divisions = {f.weight_class for f in camp_fighters}
        title_fights = self._get_upcoming_division_title_fights(player_divisions)
        if title_fights:
            print(f"  {colored('[*] UPCOMING TITLE FIGHTS:', Colors.GOLD)}")
            for tf in title_fights[:2]:
                print(f"     {tf}")
            print()
        
        # =====================================================================
        # NEWS SECTIONS
        # =====================================================================
        self._display_dashboard_news(camp_fighters)
        
        # =====================================================================
        # MENU
        # =====================================================================
        unique_weeks = len(set(f.get("weeks_until") for f in self.ai_scheduled_fights if f.get("weeks_until", 0) > 0))
        
        # Get pending incoming challenges count
        incoming_count = 0
        if LADDER_AVAILABLE and self._division_ladder:
            for fighter in camp_fighters:
                incoming_count += len(self._division_ladder.get_pending_challenges(fighter.fighter_id))
        
        # Ladder menu text (show incoming if any)
        if LADDER_AVAILABLE and self._division_ladder:
            if incoming_count > 0:
                ladder_text = f"Division Ladder ({colored(f'{incoming_count} incoming!', Colors.ORANGE)})"
            else:
                ladder_text = "Division Ladder"
        else:
            # Fallback if ladder not available
            offer_count = len(self.fight_offers)
            ladder_text = f"Fight Offers ({offer_count})"
        
        # Inbox menu text with unread count
        if INBOX_AVAILABLE and self._inbox:
            unread = self._inbox.get_unread_count()
            if unread > 0:
                inbox_text = colored(f"[M] Inbox ({unread} new)", Colors.YELLOW)
            else:
                inbox_text = "[M] Inbox"
        else:
            offer_count = len(self.fight_offers)
            inbox_text = f"Offers ({offer_count})" if offer_count > 0 else "Offers"
        
        options = [
            ("1", "Advance Week"),
            ("2", "My Camp"),
            ("3", "My Fighters"),
            ("4", ladder_text),
            ("5", f"Upcoming Events ({unique_weeks})"),
            ("6", "Rankings"),
            ("7", "Browse Fighters"),
            ("8", "Browse Camps"),
            ("9", "News Feed"),
            ("0", "History & Records"),
            ("A", "Amateur Circuit"),
            ("W", "Watchlist"),
            ("I", inbox_text),
            ("S", "Save Game"),
            ("Q", "Quit to Menu"),
        ]
        
        print_menu(options)
        
        choice = get_choice(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "a", "w", "i", "s", "q"])
        
        if choice == "1":
            self.advance_week()
        elif choice == "2":
            self.show_camp()
        elif choice == "3":
            self.show_fighters()
        elif choice == "4":
            self.show_division_ladder()
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
        elif choice == "a":
            self.show_amateur_circuit()
        elif choice == "w":
            self.show_watchlist()
        elif choice == "i":
            self.show_inbox()
        elif choice == "s":
            self.save_game_menu()
        elif choice == "q":
            self.quit_to_menu()
    
    def _get_division_rankings_weighted(self, division: str) -> List[Tuple[int, str, str]]:
        """
        Get division rankings using weighted ELO-lite formula.
        
        This is the SINGLE SOURCE OF TRUTH for rankings throughout the game.
        Uses sample-size weighting so a 3-0 fighter doesn't outrank a 7-2 fighter.
        
        Returns:
            List of (rank, fighter_id, name) where rank=0 is champion, 1-15 are contenders
        """
        import math
        game = self.game_state
        
        # Get champion
        div_state = game.divisions.get(division)
        champion_id = div_state.champion_id if div_state else None
        
        rankings_data = []
        
        # Add champion as rank 0
        if champion_id:
            champ = game.fighters.get(champion_id)
            if champ:
                rankings_data.append((0, champion_id, champ.name))
        
        # Get all non-champion fighters in this division with fights
        div_fighters = [
            f for f in game.fighters.values()
            if f.weight_class == division and f.is_active 
            and f.fighter_id != champion_id
            and (f.wins + f.losses) > 0
        ]
        
        # Weighted ELO-lite: sample size matters
        # A 3-0 fighter (100% but small sample) should rank lower than 7-2 (78% larger sample)
        def weighted_elo_key(f):
            total = f.wins + f.losses
            win_pct = f.wins / total if total > 0 else 0
            # Sample size multiplier: sqrt(fights)/4, capped at 1.0
            # 4 fights = 0.5, 9 fights = 0.75, 16+ fights = 1.0
            sample_mult = min(1.0, math.sqrt(total) / 4)
            weighted_pct = win_pct * sample_mult
            return (weighted_pct, f.wins, f.overall_rating)
        
        div_fighters.sort(key=weighted_elo_key, reverse=True)
        
        # Assign ranks 1-15 to top fighters
        for i, f in enumerate(div_fighters[:15], 1):
            rankings_data.append((i, f.fighter_id, f.name))
        
        return rankings_data
    
    def _get_fighter_rank_from_weighted(self, fighter) -> Optional[int]:
        """
        Get a fighter's rank using weighted ELO-lite.
        Returns None if unranked, 0 if champion, 1-15 if ranked.
        """
        if not fighter:
            return None
        
        rankings = self._get_division_rankings_weighted(fighter.weight_class)
        for rank, fid, _ in rankings:
            if fid == fighter.fighter_id:
                return rank
        return None
    
    def _get_fighter_rank_str(self, fighter) -> str:
        """Get ranking string for a fighter using weighted ELO-lite."""
        if self._is_division_champion(fighter):
            return colored("CHAMPION", Colors.GOLD)
        
        # Use weighted ELO-lite (single source of truth)
        rank = self._get_fighter_rank_from_weighted(fighter)
        
        if rank is None:
            return colored("Unranked", Colors.DIM)
        elif rank == 0:
            return colored("CHAMPION", Colors.GOLD)
        elif rank == 1:
            return colored("#1 Contender", Colors.GREEN)
        elif rank <= 5:
            return colored(f"#{rank} Ranked", Colors.CYAN)
        elif rank <= 15:
            return f"#{rank} Ranked"
        else:
            return colored("Unranked", Colors.DIM)
    
    def _is_division_champion(self, fighter) -> bool:
        """Check if fighter is the champion by looking at division state (source of truth)."""
        if not fighter or not self.game_state:
            return False
        
        div_state = self.game_state.divisions.get(fighter.weight_class)
        if div_state and div_state.champion_id:
            return div_state.champion_id == fighter.fighter_id
        
        # Fallback to fighter's flag if division state unavailable
        return getattr(fighter, 'is_champion', False)
    
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
        # Skip if headline already has rank markers (avoid double-adding)
        if headline.startswith("TOP 5 CLASH:") or headline.startswith("SIGNED: #"):
            return headline
        
        # Find fighter names mentioned and add their rank
        enhanced = headline
        
        for fighter in self.game_state.fighters.values():
            if fighter.name in headline:
                # Check if this name already has a rank prefix in the headline
                # Look for patterns like "#X Name" or "[C] Name"
                name_idx = headline.find(fighter.name)
                if name_idx > 0:
                    prefix = headline[max(0, name_idx-4):name_idx]
                    if "#" in prefix or "[C]" in prefix:
                        # Already has rank info, skip
                        break
                
                # Get rank info
                div_abbrev = self._get_division_abbrev(fighter.weight_class)
                
                if self._is_division_champion(fighter):
                    enhanced_name = colored(f"[C] {div_abbrev} {fighter.name}", Colors.GOLD)
                else:
                    # Use consistent ranking system
                    rank = self._get_fighter_division_rank(fighter)
                    
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
                if self._is_division_champion(fighter):
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
    
    def _get_injured_roster_fighters(self, camp_fighters: list) -> List[tuple]:
        """Get list of injured fighters on roster as (name, weeks_remaining) tuples."""
        injured = []
        
        if not INJURY_AVAILABLE or not self._injury_system:
            return injured
        
        try:
            for fighter in camp_fighters:
                injury = self._injury_system.get_worst_injury(fighter.fighter_id)
                if injury and injury.weeks_remaining > 0:
                    injured.append((fighter.name, injury.weeks_remaining))
        except:
            pass
        
        # Sort by most severe injury first
        injured.sort(key=lambda x: -x[1])
        return injured
    
    def _get_upcoming_division_title_fights(self, player_divisions: set) -> List[str]:
        """Get upcoming title fights in player's divisions."""
        title_fights = []
        
        for fight in self.ai_scheduled_fights:
            if not fight.get("is_title_fight"):
                continue
            
            wc = fight.get("weight_class", "")
            if wc not in player_divisions:
                continue
            
            weeks = fight.get("weeks_until", 0)
            if weeks <= 0 or weeks > 8:
                continue
            
            f1_name = fight.get("fighter1_name", "Fighter")
            f2_name = fight.get("fighter2_name", "Opponent")
            div = self._get_division_abbrev(wc)
            
            # Get which one is champion
            f1_id = fight.get("fighter1_id")
            f2_id = fight.get("fighter2_id")
            
            champ_name = f1_name
            challenger_name = f2_name
            challenger_rank = ""
            
            if f2_id and f2_id in self.game_state.fighters:
                f2 = self.game_state.fighters[f2_id]
                if self._is_division_champion(f2):
                    champ_name = f2_name
                    challenger_name = f1_name
                    if f1_id and f1_id in self.game_state.fighters:
                        f1 = self.game_state.fighters[f1_id]
                        rank = self._get_fighter_division_rank(f1)
                        if rank:
                            challenger_rank = f"#{rank}"
                else:
                    rank = self._get_fighter_division_rank(f2)
                    if rank:
                        challenger_rank = f"#{rank}"
            
            title_fights.append(
                f"{colored('[C]', Colors.GOLD)} {div} {champ_name} vs {challenger_rank} {challenger_name} ({weeks}wk)"
            )
        
        return title_fights
    
    def _calculate_weekly_burn(self, camp_id: str) -> int:
        """Calculate weekly expenses (burn rate) for the camp."""
        if not self._economy_manager or not ECONOMY_AVAILABLE:
            return 0
        
        try:
            # Get tier for facility costs
            tier = self._get_camp_tier()
            
            # Facility costs (monthly / 4)
            facility_costs = {
                "GARAGE": 2000, "LOCAL": 6000, "REGIONAL": 20000,
                "NATIONAL": 60000, "ELITE": 200000
            }
            weekly_facility = facility_costs.get(tier, 2000) // 4
            
            # Coach salaries
            weekly_coach = 0
            if COACHES_AVAILABLE and self._coach_system:
                coaches = self._coach_system.get_camp_coaches(camp_id)
                for coach in coaches:
                    weekly_coach += getattr(coach, 'weekly_salary', 500)
            
            # Fighter overhead (simplified)
            player_camp = self.game_state.get_player_camp()
            if player_camp:
                roster_size = len([f for f in self.game_state.fighters.values() 
                                  if getattr(f, 'camp_id', None) == camp_id])
                overhead_per_fighter = {"GARAGE": 0, "LOCAL": 50, "REGIONAL": 100,
                                       "NATIONAL": 150, "ELITE": 200}.get(tier, 0)
                weekly_overhead = roster_size * overhead_per_fighter
            else:
                weekly_overhead = 0
            
            return weekly_facility + weekly_coach + weekly_overhead
        except:
            return 0
    
    def _format_gains_abbrev(self, gains_dict: Dict[str, int]) -> str:
        """Format gains dict with abbreviations for compact display."""
        if not gains_dict:
            return ""
        
        # Abbreviation map
        abbrev = {
            "boxing": "BOX", "kicks": "KICK", "clinch_striking": "CLIN",
            "striking_defense": "SDEF", "takedowns": "TD", "takedown_defense": "TDD",
            "top_control": "TOP", "submissions": "SUB", "guard": "GRD",
            "strength": "STR", "speed": "SPD", "cardio": "CARD",
            "chin": "CHIN", "recovery": "REC", "heart": "HRT",
            "fight_iq": "IQ", "composure": "COMP",
            # Training system names
            "wrestling": "TD", "bjj": "SUB", "clinch": "CLIN",
            "td_defense": "TDD", "power": "STR",
        }
        
        parts = []
        for attr, val in sorted(gains_dict.items(), key=lambda x: -x[1]):
            if val > 0:
                attr_abbr = abbrev.get(attr, attr[:3].upper())
                parts.append(f"+{val} {attr_abbr}")
        
        return ", ".join(parts[:4]) if parts else ""  # Max 4 attrs for space
    
    def _get_fighter_training_display(self, fighter, full_data) -> Tuple[str, str, str]:
        """Get detailed training display for hub.
        
        Returns: (status_line, gains_line, event_line)
        - status_line: "[T] Camp W3/8 (Striking) w/ Coach Smith"
        - gains_line: "[+] Total: +5 BOX, +3 KICK (+12)"
        - event_line: "* BREAKTHROUGH: Striking revelation!" (or empty)
        """
        status_line = ""
        gains_line = ""
        event_line = ""
        
        if not full_data:
            return status_line, gains_line, event_line
        
        # Check if in active training camp
        camp = None
        if self._training_system:
            camp = self._training_system.get_camp(fighter.fighter_id)
        
        if camp and not camp.is_complete:
            # IN ACTIVE CAMP
            week_str = f"W{camp.weeks_completed}/{camp.total_weeks}"
            focus_str = camp.focus.value if hasattr(camp, 'focus') else ""
            
            # Get coach info
            coach_str = ""
            player_camp = self.game_state.get_player_camp()
            if player_camp:
                head_coach = self._get_head_coach_info(player_camp.camp_id)
                if head_coach and head_coach.get("name"):
                    coach_str = f" w/ {head_coach['name']}"
            
            # Get intensity from schedule
            intensity_str = ""
            if hasattr(camp, 'schedule') and camp.schedule:
                current_week_idx = max(0, camp.weeks_completed - 1)
                if current_week_idx < len(camp.schedule):
                    intensity = camp.schedule[current_week_idx]
                    intensity_name = intensity.name if hasattr(intensity, 'name') else str(intensity)
                    intensity_colors = {
                        "REST": Colors.CYAN, "LIGHT": Colors.GREEN, 
                        "MODERATE": Colors.YELLOW, "INTENSE": Colors.ORANGE, "EXTREME": Colors.RED
                    }
                    intensity_color = intensity_colors.get(intensity_name.upper(), Colors.WHITE)
                    intensity_str = f" | {colored(intensity_name.title(), intensity_color)}"
            
            status_line = colored(f"[T] Camp {week_str} ({focus_str}){coach_str}{intensity_str}", Colors.CYAN)
            
            # Get total gains so far
            total_gains = getattr(camp, 'attribute_gains', {}) or {}
            total_str = self._format_gains_abbrev(total_gains)
            total_sum = sum(total_gains.values()) if total_gains else 0
            
            if total_str and total_sum > 0:
                gains_line = f"[+] Camp gains: {colored(total_str, Colors.GREEN)} ({colored(f'+{total_sum}', Colors.GOLD)} total)"
            
            # Check for breakthrough/setback - look at journal
            journal = getattr(camp, 'journal', None)
            if journal and hasattr(journal, 'entries'):
                # Get most recent event entry from this week
                current_game_week = self.game_state.week_number if self.game_state else 0
                for entry in reversed(journal.entries):
                    entry_week = getattr(entry, 'game_week', 0)
                    if entry_week != current_game_week:
                        continue  # Only show events from this week
                    
                    if hasattr(entry, 'entry_type'):
                        entry_type = str(entry.entry_type).lower()
                        if 'breakthrough' in entry_type:
                            headline = getattr(entry, 'headline', 'Training breakthrough!')
                            event_line = colored(f"* BREAKTHROUGH: {headline}", Colors.GOLD)
                            break
                        elif 'setback' in entry_type:
                            headline = getattr(entry, 'headline', 'Training setback')
                            event_line = colored(f"[!] SETBACK: {headline}", Colors.RED)
                            break
                        elif 'injury' in entry_type:
                            headline = getattr(entry, 'headline', 'Training injury')
                            event_line = colored(f"[+] INJURY: {headline}", Colors.RED)
                            break
        
        else:
            # NOT IN CAMP - Check for recent camp completion OR maintenance gains
            current_week = self.game_state.week_number if self.game_state else 0
            
            # Check for recent camp completion
            last_camp_week = getattr(full_data, 'last_camp_week', 0)
            last_camp_total = getattr(full_data, 'last_camp_total', 0)
            last_camp_gains = getattr(full_data, 'last_camp_gains', {})
            
            # Show camp gains if ended within last 4 weeks
            if last_camp_week > 0 and (current_week - last_camp_week) <= 4 and last_camp_total > 0:
                gains_str = self._format_gains_abbrev(last_camp_gains)
                if gains_str:
                    status_line = colored(f"Last Camp: {gains_str} (+{last_camp_total} total)", Colors.DIM)
            
            # Check for maintenance training gains
            maintenance_gains = getattr(full_data, 'maintenance_gains', {})
            maintenance_week = getattr(full_data, 'maintenance_week', 0)
            
            # Show maintenance gains if any this week
            if maintenance_week == current_week and maintenance_gains:
                maint_str = self._format_gains_abbrev(maintenance_gains)
                maint_total = sum(maintenance_gains.values())
                if maint_str:
                    # If we have a status_line from camp, put maintenance on gains_line
                    if status_line:
                        gains_line = f"[W] Maintenance: {colored(maint_str, Colors.GREEN)}"
                    else:
                        status_line = f"[W] Maintenance Training: {colored(maint_str, Colors.GREEN)} (+{maint_total})"
        
        return status_line, gains_line, event_line
    
    def _get_fighter_training_status(self, fighter) -> str:
        """Get training camp status for dashboard display."""
        # Check if in active training camp
        for fight in self.player_scheduled_fights:
            if fight.get("fighter1_id") == fighter.fighter_id:
                weeks_until = fight.get("weeks_until", 0)
                if weeks_until > 0:
                    # Get training camp info if available
                    camp = None
                    if self._training_system:
                        camp = self._training_system.get_camp(fighter.fighter_id)
                    
                    full_data = self.fighter_data.get(fighter.fighter_id)
                    focus = getattr(full_data, 'current_training_focus', None) if full_data else None
                    
                    if camp and not camp.is_complete:
                        # Show week progress and focus
                        week_str = f"W{camp.weeks_completed}/{camp.total_weeks}"
                        focus_str = camp.focus.value if hasattr(camp, 'focus') else (focus or "")
                        
                        # Show total gains so far
                        total_gains = sum(camp.attribute_gains.values()) if hasattr(camp, 'attribute_gains') else 0
                        if total_gains > 0:
                            return colored(f"[T] {week_str} {focus_str} (+{total_gains})", Colors.CYAN)
                        return colored(f"[T] {week_str} {focus_str}", Colors.CYAN)
                    elif focus:
                        return colored(f"[T] {focus}", Colors.CYAN)
                    return colored("[T] Training", Colors.CYAN)
        return ""
    
    def _get_fighter_upcoming_fight(self, fighter_id: str) -> str:
        """Get upcoming fight info for dashboard display."""
        for fight in self.player_scheduled_fights:
            if fight.get("fighter1_id") == fighter_id:
                weeks = fight.get("weeks_until", 0)
                opp_name = fight.get("fighter2_name", "Opponent")
                opp_id = fight.get("fighter2_id")
                is_title = fight.get("is_title_fight", False)
                
                # Get opponent rank using consistent method
                opp_rank = ""
                if opp_id and opp_id in self.game_state.fighters:
                    opp = self.game_state.fighters[opp_id]
                    if self._is_division_champion(opp):
                        opp_rank = "[C]"
                    else:
                        rank = self._get_fighter_division_rank(opp)
                        if rank:
                            opp_rank = f"#{rank}"
                
                # Shorten opponent name if needed
                if len(opp_name) > 12:
                    opp_name = opp_name.split()[0]  # First name only
                
                if is_title:
                    return colored(f"[T] {weeks}wk vs {opp_rank} {opp_name} [TITLE]", Colors.GOLD)
                else:
                    return colored(f"[*] {weeks}wk vs {opp_rank} {opp_name}", Colors.YELLOW)
        return ""


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
        
        # Sort by ELO-lite: champion first, then win%, wins, rating
        def elo_lite_key(f):
            is_champ = 1 if self._is_division_champion(f) else 0
            total = f.wins + f.losses
            win_pct = f.wins / total if total > 0 else 0
            return (is_champ, win_pct, f.wins, getattr(f, 'overall_rating', 0))
        all_fighters.sort(key=elo_lite_key, reverse=True)
        
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
                    is_champ = self._is_division_champion(fighter)
                    
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
            
            game = self.game_state
            player_camp = game.get_player_camp()
            is_player_fighter = (player_camp and full_data.camp_id == player_camp.camp_id)
            is_champion = self._is_division_champion(fighter_rec)
            
            # Header with name and nickname
            if full_data.nickname:
                print_header(f'{full_data.name} "{full_data.nickname}"')
            else:
                print_header(f"{full_data.name}")
            
            # === QUICK INFO LINE (Camp, Ranking, Status) ===
            quick_parts = []
            
            # Camp name
            camp = game.camps.get(full_data.camp_id)
            camp_name = camp.name if camp else "Free Agent"
            quick_parts.append(camp_name)
            
            # Division and Ranking
            rank = self._get_fighter_rank_from_weighted(fighter_rec)
            if is_champion:
                quick_parts.append(colored(f"[T] {full_data.weight_class} Champion", Colors.GOLD))
            elif rank and rank <= 15:
                quick_parts.append(f"#{rank} {full_data.weight_class}")
            else:
                quick_parts.append(f"{full_data.weight_class} (Unranked)")
            
            print(f"  {colored(' | ', Colors.DIM).join(quick_parts)}")
            print()
            
            # === BIO INFO ===
            bio_lines = []
            if is_champion:
                bio_lines.append(colored("[T] DIVISION CHAMPION", Colors.GOLD))
            if getattr(full_data, 'is_generational', False):
                bio_lines.append(colored("[*] GENERATIONAL TALENT", Colors.GOLD))
            bio_lines.append(f"Country: {full_data.country} | Age: {full_data.age}")
            bio_lines.append(f"Height: {full_data.height_display} | Reach: {full_data.reach_display}")
            
            # Style with brief description
            style = full_data.fighting_style
            style_desc = {
                "Striker": "Prefers to keep the fight standing, dangerous hands/kicks",
                "Wrestler": "Looks to control on the ground, strong takedowns",
                "Grappler": "Submission threat, dangerous off their back",
                "Balanced": "Well-rounded, adapts to any situation",
                "MMA Hybrid": "Well-rounded, adapts to any situation",
                "Counter Striker": "Timing master, waits and counters",
                "Pressure Fighter": "Relentless forward movement, breaks opponents",
                "Point Fighter": "Movement and evasion, outpoints opponents",
                "Muay Thai": "Kicks, knees, elbows, clinch mastery",
                "Ground & Pound": "Takes down and smashes, TKO on the mat",
                "BJJ Specialist": "Submission hunter, dangerous from anywhere",
                "Clinch Fighter": "Dirty boxing, cage grinding, smothering",
                "Sprawl & Brawl": "Anti-wrestler striker, refuses to go down",
                "Karate": "Point fighting, explosive kicks and movement",
                "Boxing": "Heavy hands, head movement, knockout power",
                "Kickboxing": "Balanced striking, hands and kicks combined",
                "Sambo": "Combat grappling, leg locks and throws",
                "Judo": "Throws and trips, dangerous in clinch",
                "Jiu-Jitsu": "Ground specialist, submission hunting",
            }.get(style, "")
            if style_desc:
                bio_lines.append(f"Style: {colored(style, Colors.HIGHLIGHT)} - {style_desc}")
            else:
                bio_lines.append(f"Style: {colored(style, Colors.HIGHLIGHT)}")
            print_box(bio_lines, title="BIO")
            
            # === RECORD & FORM ===
            record_lines = []
            
            # Main record
            record_str = format_record_colored(full_data.wins, full_data.losses, full_data.draws)
            record_lines.append(f"Record: {record_str}")
            
            # Win methods breakdown
            if full_data.wins > 0:
                dec_wins = full_data.wins - full_data.ko_wins - full_data.sub_wins
                ko_pct = int(full_data.ko_wins / full_data.wins * 100) if full_data.wins > 0 else 0
                sub_pct = int(full_data.sub_wins / full_data.wins * 100) if full_data.wins > 0 else 0
                record_lines.append(f"Wins: {colored(str(full_data.ko_wins), Colors.RED)} KO ({ko_pct}%) | {colored(str(full_data.sub_wins), Colors.MAGENTA)} SUB ({sub_pct}%) | {dec_wins} DEC")
            
            # Streaks
            if full_data.win_streak >= 2:
                record_lines.append(colored(f"[!] {full_data.win_streak} Win Streak", Colors.WIN))
            elif full_data.lose_streak >= 2:
                record_lines.append(colored(f"* {full_data.lose_streak} Fight Skid", Colors.LOSS))
            
            # Popularity / Star Power
            pop = getattr(full_data, 'popularity', 10)
            if pop >= 80:
                pop_label = colored("SUPERSTAR", Colors.GOLD)
                stars = "★★★★★"
            elif pop >= 60:
                pop_label = colored("Star", Colors.YELLOW)
                stars = "★★★★☆"
            elif pop >= 40:
                pop_label = colored("Known", Colors.CYAN)
                stars = "★★★☆☆"
            elif pop >= 20:
                pop_label = colored("Rising", Colors.GREEN)
                stars = "★★☆☆☆"
            else:
                pop_label = "Unknown"
                stars = "★☆☆☆☆"
            record_lines.append(f"Popularity: {pop_label} ({pop}) {stars}")
            
            # Recent form (last 5 fights)
            fighter_fights = [
                r for r in self.all_fight_results.values()
                if r.fighter1_id == fighter_id or r.fighter2_id == fighter_id
            ]
            if fighter_fights:
                fighter_fights.sort(key=lambda r: r.week, reverse=True)
                form_str = ""
                for fight in fighter_fights[:5]:
                    if fight.winner_id == fighter_id:
                        form_str += colored("W", Colors.WIN) + " "
                    else:
                        form_str += colored("L", Colors.LOSS) + " "
                if form_str:
                    record_lines.append(f"Recent Form: {form_str.strip()} (newest first)")
            
            print_box(record_lines, title="RECORD & FORM")
            
            # === CAREER & STATUS ===
            status_lines = []
            
            # Career phase
            career_phase = self._get_fighter_career_phase(fighter_id)
            if career_phase:
                phase_colors = {
                    "Prospect": Colors.GREEN,
                    "Rising": Colors.CYAN,
                    "Prime": Colors.HIGHLIGHT,
                    "Veteran": Colors.YELLOW,
                    "Twilight": Colors.ORANGE,
                }
                phase_color = phase_colors.get(career_phase, Colors.NEUTRAL)
                status_lines.append(f"Career Phase: {colored(career_phase, phase_color)}")
            
            # Injury status
            if self._is_fighter_injured(fighter_id):
                weeks = self._get_fighter_recovery_weeks(fighter_id)
                status_lines.append(colored(f"[H] INJURED - {weeks} weeks until cleared", Colors.RED))
            
            # Rivalries
            rivalries = self._get_fighter_rivalries(fighter_id)
            if rivalries:
                rival_str = ", ".join([
                    f"{r.fighter1_name if r.fighter2_id == fighter_id else r.fighter2_name}"
                    for r in rivalries[:3]
                ])
                status_lines.append(f"Rivalries: {colored(rival_str, Colors.MAGENTA)}")
            
            if status_lines:
                print_box(status_lines, title="STATUS")
            
            # === AWARDS & LEGACY ===
            awards_lines = []
            
            # Title defenses
            if full_data.title_defenses > 0:
                awards_lines.append(colored(f"[T] Title Defenses: {full_data.title_defenses}", Colors.GOLD))
            
            # FOTN awards
            if full_data.fotn_awards > 0:
                awards_lines.append(colored(f"[!] Fight of the Night: {full_data.fotn_awards}x", Colors.ORANGE))
            
            # Calculate GOAT score
            total_fights = full_data.wins + full_data.losses
            goat_score = 0
            if total_fights > 0:
                goat_score += full_data.wins * 20
                goat_score += (full_data.ko_wins * 10) if hasattr(full_data, 'ko_wins') else 0
                goat_score += (full_data.sub_wins * 8) if hasattr(full_data, 'sub_wins') else 0
                if is_champion:
                    goat_score += 300
                goat_score += full_data.title_defenses * 100
                goat_score += full_data.win_streak * 15
                if total_fights >= 15:
                    goat_score += 100
                elif total_fights >= 10:
                    goat_score += 50
                if total_fights >= 5:
                    win_pct = full_data.wins / total_fights
                    goat_score += int(win_pct * 200)
                goat_score += fighter_rec.overall_rating * 2
                goat_score -= full_data.losses * 5
                
                # Get GOAT rank
                all_scores = []
                for f in game.fighters.values():
                    fd = self.fighter_data.get(f.fighter_id)
                    if fd and (fd.wins + fd.losses) >= 3:
                        s = fd.wins * 20 + (fd.ko_wins * 10 if hasattr(fd, 'ko_wins') else 0)
                        s += (fd.sub_wins * 8 if hasattr(fd, 'sub_wins') else 0)
                        if self._is_division_champion(f):
                            s += 300
                        s += fd.title_defenses * 100 + fd.win_streak * 15
                        tf = fd.wins + fd.losses
                        if tf >= 15:
                            s += 100
                        elif tf >= 10:
                            s += 50
                        if tf >= 5:
                            s += int((fd.wins / tf) * 200)
                        s += f.overall_rating * 2 - fd.losses * 5
                        all_scores.append(s)
                all_scores.sort(reverse=True)
                goat_rank = all_scores.index(goat_score) + 1 if goat_score in all_scores else len(all_scores) + 1
                total_ranked = len(all_scores)
                
                if total_fights >= 3:
                    awards_lines.append(f"[=] GOAT Score: {colored(str(goat_score), Colors.CYAN)} (Ranked #{goat_rank} of {total_ranked})")
            
            if awards_lines:
                print_box(awards_lines, title="AWARDS & LEGACY")
            
            # === ATTRIBUTES ===
            print()
            print(f"  {colored('ATTRIBUTES', Colors.BOLD)}  (Overall: {colored(str(full_data.overall_rating), Colors.HIGHLIGHT)})")
            print()
            
            # Physical (5)
            print(f"  {colored('Physical:', Colors.CYAN)}")
            print(f"    Strength:  {stat_letter_grade(full_data.strength):>6}  ({full_data.strength})")
            print(f"    Speed:     {stat_letter_grade(full_data.speed):>6}  ({full_data.speed})")
            print(f"    Cardio:    {stat_letter_grade(full_data.cardio):>6}  ({full_data.cardio})")
            print(f"    Chin:      {stat_letter_grade(full_data.chin):>6}  ({full_data.chin})")
            print(f"    Recovery:  {stat_letter_grade(full_data.recovery):>6}  ({full_data.recovery})")
            print()
            
            # Striking (4)
            print(f"  {colored('Striking:', Colors.ORANGE)}")
            print(f"    Boxing:    {stat_letter_grade(full_data.boxing):>6}  ({full_data.boxing})")
            print(f"    Kicks:     {stat_letter_grade(full_data.kicks):>6}  ({full_data.kicks})")
            print(f"    Clinch:    {stat_letter_grade(full_data.clinch_striking):>6}  ({full_data.clinch_striking})")
            print(f"    Defense:   {stat_letter_grade(full_data.striking_defense):>6}  ({full_data.striking_defense})")
            print()
            
            # Grappling (5)
            print(f"  {colored('Grappling:', Colors.MAGENTA)}")
            print(f"    Takedowns: {stat_letter_grade(full_data.takedowns):>6}  ({full_data.takedowns})")
            print(f"    TD Def:    {stat_letter_grade(full_data.takedown_defense):>6}  ({full_data.takedown_defense})")
            print(f"    Top Ctrl:  {stat_letter_grade(full_data.top_control):>6}  ({full_data.top_control})")
            print(f"    Subs:      {stat_letter_grade(full_data.submissions):>6}  ({full_data.submissions})")
            print(f"    Guard:     {stat_letter_grade(full_data.guard):>6}  ({full_data.guard})")
            print()
            
            # Mental (3)
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
            
            # === MENU (Simplified) ===
            print()
            if is_player_fighter:
                options = [
                    ("1", "Fight History"),
                    ("2", "Release Fighter"),
                    ("0", "Back"),
                ]
                print_menu(options)
                choice = get_choice(["1", "2", "0"])
                if choice == "0":
                    return
                elif choice == "1":
                    self.show_fighter_fight_history(fighter_id)
                elif choice == "2":
                    if confirm(f"Release {full_data.name}?"):
                        self.release_fighter(fighter_id)
                        return
            else:
                options = [
                    ("1", "Fight History"),
                    ("0", "Back"),
                ]
                print_menu(options)
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
        """Start a training camp with template selection"""
        if not self._training_system:
            print("Training system not available.")
            return
        
        print()
        print(colored("SELECT TRAINING FOCUS", Colors.CYAN))
        print()
        
        focuses = [
            ("1", "[S] Striking - Improve boxing, kicks, power"),
            ("2", "[J] Jiu-Jitsu - Improve BJJ, submissions"),
            ("3", "[G] Wrestling - Improve takedowns, defense"),
            ("4", "[P] Conditioning - Improve cardio, strength"),
            ("5", "[B]  Balanced - All-around"),
        ]
        print_menu(focuses)
        
        choice = get_choice(["1", "2", "3", "4", "5"])
        if not choice:
            return
        
        print()
        print(colored("SELECT DURATION", Colors.CYAN))
        print("  [1] 4 weeks")
        print("  [2] 6 weeks")
        print("  [3] 8 weeks")
        print()
        
        dur_choice = get_choice(["1", "2", "3"])
        duration_map = {"1": 4, "2": 6, "3": 8}
        weeks = duration_map.get(dur_choice, 6)
        
        try:
            from systems.training import (
                TrainingFocus, TrainingIntensity, CampTemplate,
                TEMPLATE_INFO, estimate_template_fatigue
            )
            
            focus_map = {
                "1": TrainingFocus.STRIKING,
                "2": TrainingFocus.JIUJITSU,
                "3": TrainingFocus.WRESTLING,
                "4": TrainingFocus.CONDITIONING,
                "5": TrainingFocus.BALANCED,
            }
            
            focus = focus_map.get(choice, TrainingFocus.BALANCED)
            
            # Template selection
            print()
            print(colored("SELECT CAMP STRATEGY", Colors.CYAN))
            print()
            
            fighter_fatigue = getattr(fighter, 'fatigue', 0)
            templates = list(CampTemplate)
            
            for i, template in enumerate(templates, 1):
                info = TEMPLATE_INFO[template]
                _, expected_fat, _ = estimate_template_fatigue(template, weeks)
                risk_color = {"Low": Colors.GREEN, "Medium": Colors.YELLOW, "HIGH": Colors.RED, "None": Colors.CYAN}.get(info["risk"], Colors.WHITE)
                print(f"  [{i}] {info['icon']} {info['name']} - {info['description']}")
                print(f"      Risk: {colored(info['risk'], risk_color)} | Fatigue: +{expected_fat}")
            
            print()
            template_choice = get_input("Select strategy [1]: ").strip()
            if not template_choice or template_choice not in ["1", "2", "3", "4", "5"]:
                template_choice = "1"
            
            selected_template = templates[int(template_choice) - 1]
            
            player_camp = self.game_state.get_player_camp()
            camp_id = player_camp.camp_id if player_camp else "player_camp"
            
            self._training_system.start_camp(
                fighter_id=fighter.fighter_id,
                camp_id=camp_id,
                focus=focus,
                intensity=TrainingIntensity.MODERATE,
                weeks=weeks,
                template=selected_template,
            )
            
            print()
            print(colored("*" * 40, Colors.WIN))
            print(colored(f"  TRAINING CAMP STARTED!", Colors.WIN))
            print(colored("*" * 40, Colors.WIN))
            print()
            print(f"  Strategy: {TEMPLATE_INFO[selected_template]['icon']} {TEMPLATE_INFO[selected_template]['name']}")
            print(f"  Focus: {focus.value}")
            print(f"  Duration: {weeks} weeks")
            print()
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
            
            # SELECT FOR VARIETY - Don't just take top 6 by score
            # Group opponents by type for balanced selection
            step_up = []      # Higher rated (+5 or more)
            competitive = []  # Similar rating (within 5)
            step_down = []    # Lower rated (-5 or more)
            
            for matchup in scored_opponents:
                opp = matchup["opponent"]
                rating_diff = opp.overall_rating - fighter.overall_rating
                if rating_diff >= 5:
                    step_up.append(matchup)
                elif rating_diff <= -5:
                    step_down.append(matchup)
                else:
                    competitive.append(matchup)
            
            # Build varied offer list:
            # - 2-3 competitive matches (best scores)
            # - 1-2 step up options (challenge)
            # - 1-2 step down options (easier wins for building record)
            selected_offers = []
            
            # Add top competitive matches
            selected_offers.extend(competitive[:3])
            
            # Add step up options
            selected_offers.extend(step_up[:2])
            
            # Add step down options (cans to crush!)
            selected_offers.extend(step_down[:2])
            
            # Sort by score for display, limit to 8
            selected_offers.sort(key=lambda x: -x["score_data"]["total_score"])
            num_offers = min(len(selected_offers), 8)
            
            for matchup in selected_offers[:num_offers]:
                opp = matchup["opponent"]
                score_data = matchup["score_data"]
                
                weeks_away = random.randint(min_weeks, max_weeks)
                
                # Calculate purse based on matchup quality and ratings
                base_purse = 5000
                rating_bonus = (fighter.overall_rating + opp.overall_rating) * 50
                quality_bonus = int(score_data["total_score"] * 20)
                purse = base_purse + rating_bonus + quality_bonus
                
                # Use division state to check champion status (SOURCE OF TRUTH)
                is_title = self._is_division_champion(fighter) or self._is_division_champion(opp)
                if is_title:
                    purse *= 3
                    weeks_away = max(weeks_away, 8)
                
                # Calculate accept chance
                accept_chance = self._calculate_ai_accept_chance(fighter, opp)
                
                # Get opponent rank
                opp_rank = self._get_fighter_division_rank(opp)
                
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
                
                # Also add to inbox if available
                if INBOX_AVAILABLE and self._inbox:
                    win_bonus = int(purse * 0.5)
                    opp_style = getattr(opp, 'fighting_style', 'Balanced')
                    
                    offer_data = FightOfferData(
                        offer_id=offer.offer_id,
                        fighter_id=fighter.fighter_id,
                        fighter_name=fighter.name,
                        opponent_id=opp.fighter_id,
                        opponent_name=opp.name,
                        opponent_rank=opp_rank,
                        opponent_record=format_record(opp.wins, opp.losses),
                        opponent_rating=opp.overall_rating,
                        opponent_style=opp_style,
                        weight_class=fighter.weight_class,
                        weeks_until=weeks_away,
                        purse=purse,
                        win_bonus=win_bonus,
                        is_title_fight=is_title,
                        is_main_event=is_title or fighter.overall_rating >= 75,
                        matchup_quality=score_data["quality"],
                        accept_chance=accept_chance,
                    )
                    
                    self._inbox.add_fight_offer(offer_data, self.game_state.week_number)
    
    def _calculate_ai_accept_chance(self, player_fighter, opponent) -> int:
        """Calculate likelihood of AI accepting a fight offer."""
        # Base chance
        chance = 60
        
        # Rating difference
        rating_diff = player_fighter.overall_rating - opponent.overall_rating
        if rating_diff > 10:
            chance -= 20  # AI doesn't want to fight much higher rated
        elif rating_diff > 5:
            chance -= 10
        elif rating_diff < -10:
            chance += 15  # Easy win for them
        elif rating_diff < -5:
            chance += 5
        
        # Record quality
        player_data = self.fighter_data.get(player_fighter.fighter_id)
        opp_data = self.fighter_data.get(opponent.fighter_id)
        
        if player_data and player_data.win_streak >= 3:
            chance -= 10  # They don't want hot fighters
        
        if opp_data and opp_data.win_streak >= 3:
            chance += 10  # They're confident
        
        # Ranking considerations
        player_rank = self._get_fighter_division_rank(player_fighter)
        opp_rank = self._get_fighter_division_rank(opponent)
        
        if player_rank and opp_rank:
            if player_rank < opp_rank:
                chance += 5  # They want to beat higher ranked
            elif player_rank > opp_rank + 5:
                chance -= 15  # They don't want to give up ranking
        
        return max(10, min(95, chance))
    
    def _score_all_opponents(self, fighter) -> list:
        """Score all potential opponents using smart matchmaking."""
        game = self.game_state
        player_camp = game.get_player_camp()
        
        # Get fighter's rank
        fighter_rank = self._get_fighter_division_rank(fighter)
        fighter_data = self.fighter_data.get(fighter.fighter_id)
        fighter_streak = fighter_data.win_streak if fighter_data else 0
        
        # Check if our fighter is champion (using division state)
        fighter_is_champ = self._is_division_champion(fighter)
        
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
            
            # Check if opponent is champion (using division state - SOURCE OF TRUTH)
            opp_is_champ = self._is_division_champion(opp)
            
            # TITLE FIGHT ELIGIBILITY: Champions only fight qualified contenders
            # Requirements: Must be ranked #1-5 AND have at least 3 pro fights
            
            if opp_is_champ:
                # Check if player fighter qualifies for title shot
                fighter_total_fights = fighter.wins + fighter.losses
                if fighter_total_fights < TITLE_MIN_PRO_FIGHTS:
                    continue  # Not enough experience for title shot
                if not fighter_rank or fighter_rank > 5:
                    continue  # Can't fight for title without being top 5
            
            # If player is champion, only offer fights against qualified top 5
            if fighter_is_champ:
                opp_rank = self._get_fighter_division_rank(opp)
                opp_total_fights = opp.wins + opp.losses
                if opp_total_fights < TITLE_MIN_PRO_FIGHTS:
                    continue  # Opponent not experienced enough
                if not opp_rank or opp_rank > 5:
                    continue  # Champion only defends against top 5
            
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
                    is_title_fight=fighter_is_champ or opp_is_champ,
                    is_main_event=fighter.overall_rating >= 75,
                    weeks_out=8,
                    purse=5000 + (fighter.overall_rating + opp.overall_rating) * 50,
                )
                
                # Add acceptance info to score data
                score_data["ai_will_accept"] = will_accept
                score_data["ai_decline_reason"] = decline_reason
                score_data["ai_accept_probability"] = accept_prob
                score_data["is_title_fight"] = fighter_is_champ or opp_is_champ
                
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
        if self._is_division_champion(fighter) or self._is_division_champion(opp):
            scores["narrative"] = 10
            tags.append("TITLE FIGHT")
        elif (f_rank and f_rank <= 5) or (o_rank and o_rank <= 5):
            scores["narrative"] = 8
            if f_rank and f_rank <= 3 and not self._is_division_champion(opp):
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
            is_champion=self._is_division_champion(ai_fighter),
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
        """Get fighter's rank in their division (None if unranked).
        
        Uses weighted ELO-lite ranking:
        - Win% (weighted by sample size - more fights = more reliable)
        - Total wins (volume matters)
        - Overall rating (tiebreaker)
        
        Fighters with 1-2 fights can be ranked but their win% is discounted.
        This prevents 1-0 fighters from being #1 while allowing fast risers
        like Brock Lesnar who beat quality opponents.
        """
        if self._is_division_champion(fighter):
            return 0
        
        # Must have at least 1 fight to be ranked
        total_fights = fighter.wins + fighter.losses
        if total_fights == 0:
            return None  # 0-0 fighters are unranked
        
        # Use real rankings system if available AND it has ranked fighters
        if RANKINGS_AVAILABLE and self._rankings_system:
            try:
                from core.types import WeightClass
                wc = WeightClass(fighter.weight_class) if isinstance(fighter.weight_class, str) else fighter.weight_class
                
                # Check if rankings system has any ranked fighters for this division
                rankings = self._rankings_system.get_rankings(wc)
                has_ranked = any(rank > 0 for rank, _, _ in rankings)
                
                if has_ranked:
                    rank = self._rankings_system.get_rank(fighter.fighter_id, wc)
                    if rank is not None:
                        return rank
                    return None  # Not ranked in this populated division
                # Fall through to ELO-lite if no ranked fighters yet
            except:
                pass
        
        # Weighted ELO-lite ranking
        # Get all active fighters in division with fight history
        div_fighters = [f for f in self.game_state.fighters.values()
                       if f.weight_class == fighter.weight_class 
                       and f.is_active and not self._is_division_champion(f)
                       and (f.wins + f.losses) > 0]
        
        def weighted_elo_key(f):
            """
            ELO-lite with sample size weighting.
            
            Formula:
            - Base win% (0-1)
            - Sample multiplier: sqrt(fights) / 4 (caps at ~1.0 for 16+ fights)
            - Weighted win% = base * multiplier
            - Then wins and rating as tiebreakers
            
            This means:
            - 1-0 (100% win) * 0.25 = 0.25 effective
            - 3-0 (100% win) * 0.43 = 0.43 effective
            - 8-2 (80% win) * 0.71 = 0.57 effective
            - 15-5 (75% win) * 1.0 = 0.75 effective
            
            So experienced fighters with good records rank above flash 1-0s.
            """
            import math
            total = f.wins + f.losses
            win_pct = f.wins / total if total > 0 else 0
            
            # Sample size multiplier: sqrt(fights) / 4, capped at 1.0
            sample_mult = min(1.0, math.sqrt(total) / 4)
            
            # Weighted win percentage
            weighted_pct = win_pct * sample_mult
            
            # Return tuple for sorting: (weighted %, raw wins, rating)
            return (weighted_pct, f.wins, f.overall_rating)
        
        div_fighters.sort(key=weighted_elo_key, reverse=True)
        
        for i, f in enumerate(div_fighters[:15], 1):
            if f.fighter_id == fighter.fighter_id:
                return i
        
        return None
    
    def _populate_rankings_system(self) -> None:
        """Populate rankings system from current fighters using ELO-lite approach.
        
        ELO-lite ranking criteria (same as world_init):
        1. Champion first (rank 0)
        2. Win percentage (higher = better rank)
        3. Total wins (more wins = better tiebreaker)
        4. Overall rating (final tiebreaker)
        
        Only fighters with fight history (wins + losses > 0) are ranked.
        """
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
                import math
                
                # Weighted ELO-lite with sample size adjustment
                def weighted_elo_key(f):
                    total_fights = f.wins + f.losses
                    if total_fights == 0:
                        return (0, 0, 0, f.overall_rating)
                    
                    win_pct = f.wins / total_fights
                    sample_mult = min(1.0, math.sqrt(total_fights) / 4)
                    weighted_pct = win_pct * sample_mult
                    
                    is_champ = 1 if self._is_division_champion(f) else 0
                    return (is_champ, weighted_pct, f.wins, f.overall_rating)
                
                fighters.sort(key=weighted_elo_key, reverse=True)
                
                # Find champion
                champion = None
                for f in fighters:
                    if self._is_division_champion(f):
                        champion = f
                        break
                
                if champion:
                    self._rankings_system.set_champion(
                        champion.fighter_id,
                        champion.name,
                        wc,
                        week=self.game_state.week_number,
                        year=self.game_state.current_year,
                    )
                
                # Add top 15 to rankings (fighters with at least 1 fight)
                rank_count = 0
                for f in fighters:
                    if self._is_division_champion(f):
                        continue
                    if rank_count >= 15:
                        break
                    
                    # Only rank fighters with at least 1 fight
                    total_fights = f.wins + f.losses
                    if total_fights == 0:
                        continue
                    
                    self._rankings_system.add_to_rankings(
                        f.fighter_id,
                        f.name,
                        wc,
                        target_rank=rank_count + 1,
                        week=self.game_state.week_number,
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
        winner_pre_rank: Optional[int] = None,
        loser_pre_rank: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Process ranking changes after a fight using weighted ELO-lite."""
        changes = []
        import math
        
        winner_rec = self.game_state.fighters.get(winner_id)
        loser_rec = self.game_state.fighters.get(loser_id)
        
        if not winner_rec or not loser_rec:
            return changes
        
        # Get pre-fight rankings from weighted ELO-lite (BEFORE record update)
        if winner_pre_rank is None:
            winner_pre_rank = self._get_fighter_rank_from_weighted(winner_rec)
        if loser_pre_rank is None:
            loser_pre_rank = self._get_fighter_rank_from_weighted(loser_rec)
        
        # Get all division fighters (exclude champion for ranking calculation)
        div_fighters = [
            f for f in self.game_state.fighters.values()
            if f.weight_class == weight_class and f.is_active 
            and not self._is_division_champion(f)
            and (f.wins + f.losses) > 0
        ]
        
        if not div_fighters:
            return changes
        
        # Simulate the record changes for ranking calculation
        # This calculates what ranks WILL BE after this fight
        simulated_records = {}
        for f in div_fighters:
            total = f.wins + f.losses
            wins = f.wins
            if f.fighter_id == winner_id:
                wins += 1
                total += 1
            elif f.fighter_id == loser_id:
                total += 1  # loss (wins stays same)
            simulated_records[f.fighter_id] = (wins, total, f.overall_rating)
        
        # Weighted ELO-lite sort with simulated records
        def weighted_elo_key(f):
            wins, total, rating = simulated_records.get(f.fighter_id, (f.wins, f.wins + f.losses, f.overall_rating))
            win_pct = wins / total if total > 0 else 0
            sample_mult = min(1.0, math.sqrt(total) / 4)
            weighted_pct = win_pct * sample_mult
            return (weighted_pct, wins, rating)
        
        div_fighters.sort(key=weighted_elo_key, reverse=True)
        
        # Find new ranks (post-fight)
        winner_new_rank = None
        loser_new_rank = None
        for i, f in enumerate(div_fighters[:15], 1):
            if f.fighter_id == winner_id:
                winner_new_rank = i
            elif f.fighter_id == loser_id:
                loser_new_rank = i
        
        # Handle winners outside top 15 entering rankings
        if winner_new_rank is None:
            for i, f in enumerate(div_fighters, 1):
                if f.fighter_id == winner_id:
                    winner_new_rank = i if i <= 15 else None
                    break
        
        # Generate winner change - PROMOTIONS
        if winner_pre_rank is None and winner_new_rank is not None and winner_new_rank <= 15:
            # Entered rankings!
            changes.append({
                "fighter_id": winner_id,
                "fighter_name": winner_name,
                "old_rank": None,
                "new_rank": winner_new_rank,
                "reason": "fight_win",
                "is_promotion": True,
                "positions_moved": 0,
                "is_big_mover": True,
            })
        elif winner_pre_rank is not None and winner_new_rank is not None:
            if winner_new_rank < winner_pre_rank:
                # Moved up in rankings
                positions_moved = winner_pre_rank - winner_new_rank
                changes.append({
                    "fighter_id": winner_id,
                    "fighter_name": winner_name,
                    "old_rank": winner_pre_rank,
                    "new_rank": winner_new_rank,
                    "reason": "fight_win",
                    "is_promotion": True,
                    "positions_moved": positions_moved,
                    "is_big_mover": positions_moved >= 3,
                })
        
        # Generate loser change - DEMOTIONS  
        if loser_pre_rank is not None and loser_pre_rank <= 15:
            if loser_new_rank is None or loser_new_rank > 15:
                # Fell out of rankings
                changes.append({
                    "fighter_id": loser_id,
                    "fighter_name": loser_name,
                    "old_rank": loser_pre_rank,
                    "new_rank": None,
                    "reason": "fight_loss",
                    "is_promotion": False,
                    "positions_moved": 0,
                    "is_big_mover": True,
                })
            elif loser_new_rank > loser_pre_rank:
                # Dropped in rankings
                positions_moved = loser_new_rank - loser_pre_rank
                changes.append({
                    "fighter_id": loser_id,
                    "fighter_name": loser_name,
                    "old_rank": loser_pre_rank,
                    "new_rank": loser_new_rank,
                    "reason": "fight_loss",
                    "is_promotion": False,
                    "positions_moved": positions_moved,
                    "is_big_mover": positions_moved >= 3,
                })
        
        return changes
    
    def _get_p4p_rankings(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Get pound-for-pound rankings."""
        if not RANKINGS_AVAILABLE or not self._rankings_system:
            return []
        
        try:
            p4p = self._rankings_system.calculate_p4p_rankings(
                current_week=self.game_state.week_number,
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
        
        # Get fighter's rank for title eligibility check
        fighter_rank = self._get_fighter_division_rank(fighter)
        fighter_total_fights = fighter.wins + fighter.losses
        
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
            
            # TITLE FIGHT ELIGIBILITY: Champions only fight qualified contenders
            # Requirements: Must be ranked #1-5 AND have at least 3 pro fights
            if self._is_division_champion(opp):
                if fighter_total_fights < TITLE_MIN_PRO_FIGHTS:
                    continue  # Not enough experience for title shot
                if not fighter_rank or fighter_rank > 5:
                    continue  # Can't fight for title without being top 5
            # If player is champion, only offer fights against qualified top 5
            if self._is_division_champion(fighter):
                opp_rank = self._get_fighter_division_rank(opp)
                opp_total_fights = opp.wins + opp.losses
                if opp_total_fights < TITLE_MIN_PRO_FIGHTS:
                    continue  # Opponent not experienced enough
                if not opp_rank or opp_rank > 5:
                    continue  # Champion only defends against top 5
            
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
    
    # =========================================================================
    # DIVISION LADDER - Challenge-Based Matchmaking
    # =========================================================================
    
    def show_division_ladder(self) -> None:
        """
        Main entry point for Division Ladder.
        
        Replaces passive fight offers with active division climbing.
        See the mountain, pick your path, climb.
        """
        if not LADDER_AVAILABLE or not self._division_ladder:
            # Fallback to old fight offers
            self.show_fight_offers()
            return
        
        game = self.game_state
        player_camp = game.get_player_camp()
        
        if not player_camp:
            print("No camp found!")
            pause()
            return
        
        # Get player fighters
        camp_fighters = [
            f for f in game.fighters.values()
            if getattr(f, 'camp_id', None) == player_camp.camp_id and f.is_active
        ]
        
        if not camp_fighters:
            clear_screen()
            print_header("DIVISION LADDER")
            print("  No fighters in your camp yet.")
            print("  Sign fighters to start climbing!")
            pause()
            return
        
        # Check for incoming challenges first
        self._check_incoming_challenges()
        
        # If only one division represented, go straight to it
        divisions = set(f.weight_class for f in camp_fighters)
        
        if len(divisions) == 1:
            division = list(divisions)[0]
            self._show_ladder_for_division(division)
        else:
            # Multiple divisions - let player pick
            self._show_division_picker(camp_fighters)
    
    def _show_division_picker(self, camp_fighters: List) -> None:
        """Let player pick which division's ladder to view."""
        while True:
            clear_screen()
            print_header("DIVISION LADDER")
            
            print(f"  {colored('Select a division to view:', Colors.CYAN)}")
            print()
            
            # Group fighters by division
            by_division = {}
            for f in camp_fighters:
                wc = f.weight_class
                if wc not in by_division:
                    by_division[wc] = []
                by_division[wc].append(f)
            
            # Sort divisions by weight
            weight_order = [
                "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
                "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
            ]
            sorted_divs = sorted(by_division.keys(), key=lambda d: weight_order.index(d) if d in weight_order else 99)
            
            for i, div in enumerate(sorted_divs, 1):
                fighters = by_division[div]
                abbrev = self._get_division_abbrev(div)
                
                # Get highest ranked player fighter in this division
                best_rank = None
                best_name = None
                for f in fighters:
                    rank = self._get_fighter_division_rank(f)
                    if self._is_division_champion(f):
                        rank = 0
                    if best_rank is None or (rank is not None and rank < (best_rank or 999)):
                        best_rank = rank
                        best_name = f.name
                
                rank_str = "[C]" if best_rank == 0 else f"#{best_rank}" if best_rank else "UR"
                fighter_list = ", ".join(f.name for f in fighters[:2])
                if len(fighters) > 2:
                    fighter_list += f" +{len(fighters)-2} more"
                
                print(f"  [{i}] {colored(abbrev, Colors.CYAN)} {div}")
                print(f"      {colored(rank_str, Colors.GOLD if best_rank == 0 else Colors.GREEN)} {fighter_list}")
                print()
            
            print(f"  [0] Back")
            print()
            
            choice = get_input("Select division: ")
            
            if choice == "0":
                return
            
            try:
                idx = int(choice)
                if 1 <= idx <= len(sorted_divs):
                    self._show_ladder_for_division(sorted_divs[idx - 1])
            except ValueError:
                pass
    
    def _show_ladder_for_division(self, division: str) -> None:
        """Display the full division ladder with challenge options."""
        game = self.game_state
        player_camp = game.get_player_camp()
        
        # Get division state
        div_state = game.divisions.get(division)
        champion_id = div_state.champion_id if div_state else None
        
        # Fetch rankings data (same method as show_division_rankings)
        rankings_data = []
        if RANKINGS_AVAILABLE and self._rankings_system:
            try:
                from core.types import WeightClass
                wc = WeightClass(division)
                rankings_data = self._rankings_system.get_rankings(wc)
            except:
                pass
        
        # FALLBACK: Check if we have ranked fighters (rank > 0), not just champion
        # At Week 0, rankings system returns only champion - need ELO-lite for ranked
        has_ranked_fighters = any(rank > 0 for rank, _, _ in rankings_data)
        
        if not has_ranked_fighters:
            # Keep champion if present
            champion_entry = next(((r, fid, name) for r, fid, name in rankings_data if r == 0), None)
            rankings_data = []
            
            if champion_entry:
                rankings_data.append(champion_entry)
            elif champion_id:
                champ = game.fighters.get(champion_id)
                if champ:
                    rankings_data.append((0, champion_id, champ.name))
            
            import math
            
            # Get all non-champion fighters in this division with fights
            div_fighters = [
                f for f in game.fighters.values()
                if f.weight_class == division and f.is_active and f.fighter_id != champion_id
                and (f.wins + f.losses) > 0
            ]
            
            # Weighted ELO-lite: sample size matters
            def weighted_elo_key(f):
                total = f.wins + f.losses
                win_pct = f.wins / total if total > 0 else 0
                sample_mult = min(1.0, math.sqrt(total) / 4)
                weighted_pct = win_pct * sample_mult
                return (weighted_pct, f.wins, f.overall_rating)
            
            div_fighters.sort(key=weighted_elo_key, reverse=True)
            
            # Assign ranks 1-15 to top fighters
            for i, f in enumerate(div_fighters[:15], 1):
                rankings_data.append((i, f.fighter_id, f.name))
        
        # Build the ladder with rankings data
        ladder = self._division_ladder.build_ladder(
            weight_class=division,
            fighters=game.fighters,
            fighter_data=self.fighter_data,
            rankings_data=rankings_data,
            injury_system=self._injury_system,
            scheduled_fights=self.player_scheduled_fights + self.ai_scheduled_fights,
            cooldowns=self._fighter_cooldowns,
            player_camp_id=player_camp.camp_id if player_camp else "",
            champion_id=champion_id,
            camps=game.camps,
        )
        
        # Find player fighters in this division
        player_entries = [e for e in ladder if e.is_player_fighter]
        
        # Helper to rebuild ladder and rankings
        def rebuild_ladder():
            nonlocal ladder, player_entries, rankings_data
            rankings_data = []
            if RANKINGS_AVAILABLE and self._rankings_system:
                try:
                    from core.types import WeightClass
                    wc = WeightClass(division)
                    rankings_data = self._rankings_system.get_rankings(wc)
                except:
                    pass
            
            has_ranked_fighters = any(rank > 0 for rank, _, _ in rankings_data)
            if not has_ranked_fighters:
                champion_entry = next(((r, fid, name) for r, fid, name in rankings_data if r == 0), None)
                rankings_data = []
                if champion_entry:
                    rankings_data.append(champion_entry)
                elif champion_id:
                    champ = game.fighters.get(champion_id)
                    if champ:
                        rankings_data.append((0, champion_id, champ.name))
                
                import math
                
                div_fighters = [
                    f for f in game.fighters.values()
                    if f.weight_class == division and f.is_active and f.fighter_id != champion_id
                    and (f.wins + f.losses) > 0
                ]
                
                # Weighted ELO-lite: sample size matters
                def weighted_elo_key(f):
                    total = f.wins + f.losses
                    win_pct = f.wins / total if total > 0 else 0
                    sample_mult = min(1.0, math.sqrt(total) / 4)
                    weighted_pct = win_pct * sample_mult
                    return (weighted_pct, f.wins, f.overall_rating)
                
                div_fighters.sort(key=weighted_elo_key, reverse=True)
                for i, f in enumerate(div_fighters[:15], 1):
                    rankings_data.append((i, f.fighter_id, f.name))
            
            ladder = self._division_ladder.build_ladder(
                weight_class=division,
                fighters=game.fighters,
                fighter_data=self.fighter_data,
                rankings_data=rankings_data,
                injury_system=self._injury_system,
                scheduled_fights=self.player_scheduled_fights + self.ai_scheduled_fights,
                cooldowns=self._fighter_cooldowns,
                player_camp_id=player_camp.camp_id if player_camp else "",
                champion_id=champion_id,
                camps=game.camps,
            )
            player_entries = [e for e in ladder if e.is_player_fighter]
        
        while True:
            clear_screen()
            
            # Calculate accept percentages for display
            accept_percentages = {}
            available_player = next(
                (e for e in player_entries if e.status == FighterStatus.AVAILABLE), 
                None
            )
            
            if available_player and LADDER_AVAILABLE:
                week = game.week_number
                for entry in ladder:
                    if not entry.is_player_fighter and entry.status == FighterStatus.AVAILABLE:
                        # Calculate acceptance probability
                        accept_pct = self._division_ladder._calculate_acceptance_probability(
                            available_player, entry, week
                        )
                        accept_percentages[entry.fighter_id] = int(accept_pct * 100)
            
            # Display the ladder and get challenge map
            challenge_map = self._display_ladder(division, ladder, player_entries, accept_percentages)
            
            # Menu options
            print()
            if available_player:
                # Check remaining challenges
                challenges_used = self._division_ladder._challenges_this_week.get(available_player.fighter_id, 0)
                challenges_remaining = 2 - challenges_used  # WEEKLY_CHALLENGE_LIMIT = 2
                
                if challenges_remaining > 0:
                    print(f"  {colored(f'Enter rank # to challenge (1-15, C, U1-U5) * {challenges_remaining} challenge(s) left', Colors.GREEN)}")
                else:
                    print(f"  {colored('No challenges remaining this week', Colors.DIM)}")
            print(f"  [D] Fighter Details  [V] View Rankings  [B] Back")
            print()
            
            choice = get_input("Choice: ").strip()
            
            if choice.lower() == "b":
                return
            elif choice.lower() == "d":
                self._ladder_fighter_details(ladder)
            elif choice.lower() == "v":
                self.show_division_rankings(division)
            elif choice.upper() in challenge_map or choice in challenge_map:
                # Direct challenge by rank
                target = challenge_map.get(choice.upper()) or challenge_map.get(choice)
                
                if not available_player:
                    print(f"\n  {colored('No available fighters to issue challenges.', Colors.RED)}")
                    pause()
                    continue
                
                if target.is_player_fighter:
                    print(f"\n  {colored('Cannot challenge your own fighter!', Colors.RED)}")
                    pause()
                    continue
                
                if target.status != FighterStatus.AVAILABLE:
                    # Show specific reason for unavailability
                    reason = target.status_detail if target.status_detail else "Not available"
                    if target.status == FighterStatus.COOLDOWN:
                        print(f"\n  {colored(f'{target.name} is recovering from a recent fight.', Colors.RED)}")
                        print(f"  {colored(f'Status: {reason}', Colors.DIM)}")
                    elif target.status == FighterStatus.INJURED:
                        print(f"\n  {colored(f'{target.name} is injured and cannot fight.', Colors.RED)}")
                        print(f"  {colored(f'Status: {reason}', Colors.DIM)}")
                    elif target.status == FighterStatus.BOOKED:
                        print(f"\n  {colored(f'{target.name} already has a fight scheduled.', Colors.RED)}")
                        print(f"  {colored(f'Status: {reason}', Colors.DIM)}")
                    else:
                        print(f"\n  {colored(f'{target.name} is not available.', Colors.RED)}")
                    pause()
                    continue
                
                # Issue challenge directly
                self._issue_direct_challenge(
                    division, available_player, target, 
                    accept_percentages.get(target.fighter_id, 50)
                )
                rebuild_ladder()
    
    def _display_ladder(
        self, 
        division: str, 
        ladder: List, 
        player_entries: List,
        accept_percentages: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Render the division ladder display.
        
        Returns a mapping of input codes to ladder entries for direct challenge.
        """
        week = self.game_state.week_number
        challenge_map = {}  # Maps input (e.g. "15", "C", "U3") to entry
        
        # Find player's best rank
        player_rank = None
        for pe in player_entries:
            if pe.rank is not None:
                if player_rank is None or pe.rank < player_rank:
                    player_rank = pe.rank
        
        # Determine if we should show unranked (player is unranked or low ranked)
        show_unranked = (player_rank is None or player_rank >= 10)
        
        rank_display = ""
        if player_rank == 0:
            rank_display = colored("You are CHAMPION!", Colors.GOLD)
        elif player_rank:
            rank_display = f"Your Position: #{player_rank}"
        else:
            rank_display = colored("Unranked - climb the ladder!", Colors.DIM)
        
        # Header
        print(f"  {colored('=' * 76, Colors.CYAN)}")
        print(f"  {colored(f'{division.upper()} DIVISION LADDER', Colors.HIGHLIGHT):^76}")
        print(f"  {colored(f'Week {week}', Colors.DIM):^76}")
        print(f"  {rank_display:^76}")
        print(f"  {colored('=' * 76, Colors.CYAN)}")
        
        # Column header
        print(f"  {colored('     Name                  Record   OVR Style Camp         Accept', Colors.DIM)}")
        
        # Style legend (compact, shows icon categories)
        style_legend = f"  {colored('Style:', Colors.DIM)} [S] Striking  [G] Wrestling  [J] Submissions  [B] Balanced  {colored('[D] for details', Colors.CYAN)}"
        print(style_legend)
        
        # Champion section
        champion = next((e for e in ladder if e.rank == 0), None)
        if champion:
            print(f"  {colored('[T] CHAMPION', Colors.GOLD)}")
            accept_pct = accept_percentages.get(champion.fighter_id, 0) if accept_percentages else 0
            self._display_ladder_entry(
                champion, 
                highlight=champion.is_player_fighter,
                show_accept_pct=True,
                accept_pct=accept_pct
            )
            challenge_map["C"] = champion
            challenge_map["c"] = champion
            challenge_map["0"] = champion
            print(f"  {colored('-' * 76, Colors.DIM)}")
        
        # Title Contenders (#1-5)
        contenders = [e for e in ladder if e.rank and 1 <= e.rank <= 5]
        if contenders:
            print(f"  {colored('TITLE CONTENDERS (#1-5 can fight for title)', Colors.YELLOW)}")
            for entry in contenders:
                accept_pct = accept_percentages.get(entry.fighter_id, 0) if accept_percentages else 0
                self._display_ladder_entry(
                    entry, 
                    highlight=entry.is_player_fighter,
                    show_accept_pct=True,
                    accept_pct=accept_pct
                )
                challenge_map[str(entry.rank)] = entry
            print(f"  {colored('-' * 76, Colors.DIM)}")
        
        # Ranked Fighters (#6-15)
        ranked = [e for e in ladder if e.rank and 6 <= e.rank <= 15]
        if ranked:
            print(f"  {colored('RANKED', Colors.CYAN)}")
            for entry in ranked:
                accept_pct = accept_percentages.get(entry.fighter_id, 0) if accept_percentages else 0
                self._display_ladder_entry(
                    entry, 
                    highlight=entry.is_player_fighter,
                    show_accept_pct=True,
                    accept_pct=accept_pct
                )
                challenge_map[str(entry.rank)] = entry
            print(f"  {colored('-' * 76, Colors.DIM)}")
        
        # Unranked section
        unranked = [e for e in ladder if e.rank is None]
        unranked_available = [e for e in unranked if e.status == FighterStatus.AVAILABLE and not e.is_player_fighter]
        
        if unranked:
            # Always show player's unranked fighters
            player_unranked = [e for e in unranked if e.is_player_fighter]
            
            if show_unranked and unranked_available:
                # Show top unranked opponents (by rating)
                unranked_available.sort(key=lambda e: e.overall_rating, reverse=True)
                show_count = min(10, len(unranked_available))  # Show top 10 instead of 5
                
                print(f"  {colored(f'UNRANKED (top {show_count} of {len(unranked)})', Colors.DIM)}")
                for i, entry in enumerate(unranked_available[:show_count], 1):
                    accept_pct = accept_percentages.get(entry.fighter_id, 0) if accept_percentages else 0
                    self._display_ladder_entry(
                        entry,
                        highlight=False,
                        show_accept_pct=True,
                        accept_pct=accept_pct,
                        entry_num=f"U{i}"
                    )
                    challenge_map[f"U{i}"] = entry
                    challenge_map[f"u{i}"] = entry
            else:
                print(f"  {colored(f'UNRANKED ({len(unranked_available)} available of {len(unranked)})', Colors.DIM)}")
            
            # Always show player's unranked fighters
            for entry in player_unranked:
                self._display_ladder_entry(entry, highlight=True)
        
        print(f"  {colored('=' * 76, Colors.CYAN)}")
        
        # Path to title
        if player_entries and player_rank != 0:
            best_player = min(player_entries, key=lambda e: e.rank if e.rank else 999)
            path = get_path_to_title(best_player, ladder)
            if path:
                print()
                print(f"  {colored('[!] PATH TO TITLE:', Colors.GREEN)} {' ^ '.join(path[:3])}")
        
        # Threat assessment
        for pe in player_entries:
            if pe.status == FighterStatus.AVAILABLE:
                threat = get_threat_assessment(pe, ladder)
                if threat:
                    print(f"  {colored('[!]  INCOMING:', Colors.ORANGE)} {threat.name} may challenge {pe.name}")
                    break
        
        return challenge_map
    
    def _display_ladder_entry(
        self, 
        entry, 
        highlight: bool = False,
        show_accept_pct: bool = False,
        accept_pct: int = 0,
        entry_num: str = ""
    ) -> None:
        """Display a single ladder entry with optional challenge info."""
        # Rank/number display
        if entry_num:
            # Custom numbering (for unranked: U1, U2, etc.)
            rank_str = colored(f"{entry_num:>3}", Colors.DIM)
        elif entry.rank == 0:
            rank_str = colored("[C]", Colors.GOLD)
        elif entry.rank:
            rank_str = colored(f"#{entry.rank:>2}", Colors.CYAN)
        else:
            rank_str = colored(" UR", Colors.DIM)
        
        # Name (with player highlight)
        name_display = entry.name[:20]  # Truncate long names
        if highlight:
            name_str = colored(f"^ {name_display:<20}", Colors.HIGHLIGHT)
        else:
            name_str = f"  {name_display:<20}"
        
        # Record (compact)
        record_str = f"{entry.record:<7}"
        
        # Rating
        rating_str = f"{entry.overall_rating:>2}"
        
        # Style icon
        style_icons = {
            "Striker": "[S]",
            "Wrestler": "[G]",
            "Grappler": "[J]",
            "Balanced": "[B]",
        }
        style_icon = style_icons.get(entry.style, "[B]")
        
        # Camp name (truncated)
        camp_display = entry.camp_name[:12] if entry.camp_name else ""
        
        # Status (compact)
        if entry.status == FighterStatus.AVAILABLE:
            if show_accept_pct and not entry.is_player_fighter:
                # Show accept % instead of "Available"
                if accept_pct >= 60:
                    status_str = colored(f"{accept_pct:>2}%", Colors.GREEN)
                elif accept_pct >= 30:
                    status_str = colored(f"{accept_pct:>2}%", Colors.YELLOW)
                else:
                    status_str = colored(f"{accept_pct:>2}%", Colors.RED)
            else:
                status_str = colored("[OK]", Colors.GREEN)
        elif entry.status == FighterStatus.BOOKED:
            # Compact booked display
            detail = entry.status_detail[:15] if entry.status_detail else "Booked"
            status_str = colored(f"[!] {detail}", Colors.YELLOW)
        elif entry.status == FighterStatus.INJURED:
            # Show injury weeks if available
            if entry.status_detail and "wks" in entry.status_detail:
                # Extract weeks from "Injured (4 wks)" -> "(4 wks)"
                detail = entry.status_detail.replace("Injured ", "")
                status_str = colored(f"[H] {detail}", Colors.RED)
            else:
                status_str = colored(f"[H]", Colors.RED)
        elif entry.status == FighterStatus.COOLDOWN:
            # Show cooldown weeks - extract from "Cooldown (X wks)"
            if entry.status_detail:
                # Extract the number from status_detail
                try:
                    # "Cooldown (4 wks)" -> find the number
                    parts = entry.status_detail.split("(")
                    if len(parts) > 1:
                        weeks_part = parts[1].split()[0]  # "4" from "4 wks)"
                        status_str = colored(f"[T] {weeks_part}w", Colors.ORANGE)
                    else:
                        status_str = colored(f"[T]", Colors.ORANGE)
                except:
                    status_str = colored(f"[T]", Colors.ORANGE)
            else:
                status_str = colored(f"[T]", Colors.ORANGE)
        else:
            status_str = ""
        
        # Streak indicator (compact)
        streak_str = ""
        if entry.win_streak >= 3:
            streak_str = colored(f"W{entry.win_streak}", Colors.GREEN)
        elif entry.lose_streak >= 2:
            streak_str = colored(f"L{entry.lose_streak}", Colors.RED)
        
        # Format: Rank  Name                  Record   OVR  Style  Camp         Status
        print(f"  {rank_str} {name_str} {record_str} {rating_str} {style_icon} {camp_display:<12} {status_str} {streak_str}")
    
    def _issue_direct_challenge(
        self,
        division: str,
        challenger: Any,
        target: Any,
        accept_pct: int
    ) -> None:
        """Issue a challenge directly from the ladder screen.
        
        Now queues challenge as pending - resolution happens at end of week.
        """
        print()
        rank_str = f"#{target.rank}" if target.rank and target.rank > 0 else ("[C]" if target.rank == 0 else "UR")
        
        # Show confirmation with matchup info
        print(f"  {colored('CHALLENGE:', Colors.CYAN)} {challenger.name} -> {target.name}")
        print(f"  {colored('Target:', Colors.DIM)} {rank_str} {target.name} ({target.overall_rating} OVR, {target.style})")
        print(f"  {colored('Accept Chance:', Colors.DIM)} {accept_pct}%")
        
        # Determine risk/reward
        player_rating = challenger.overall_rating
        target_rating = target.overall_rating
        diff = target_rating - player_rating
        
        if diff > 10:
            risk = colored("High Risk / High Reward", Colors.RED)
        elif diff > 0:
            risk = colored("Even Matchup", Colors.YELLOW)
        elif diff > -10:
            risk = colored("Favorable", Colors.GREEN)
        else:
            risk = colored("Safe Win / Low Reward", Colors.DIM)
        print(f"  {colored('Risk:', Colors.DIM)} {risk}")
        
        print()
        print(f"  {colored('Note:', Colors.DIM)} Response will come when you advance the week.")
        print()
        confirm = get_input(f"  Issue challenge? [Y/N]: ").strip().lower()
        
        if confirm != "y":
            return
        
        # Issue the challenge (now queues as pending)
        week = self.game_state.week_number
        result = self._division_ladder.issue_challenge(
            challenger_id=challenger.fighter_id,
            target_id=target.fighter_id,
            challenger_entry=challenger,
            target_entry=target,
            accept_probability=accept_pct / 100.0,
            week=week,
        )
        
        if result.accepted:
            # Challenge sent successfully (pending, not yet accepted by fighter)
            print()
            print(f"  {colored('CHALLENGE SENT!', Colors.CYAN)}")
            print(f"  {colored(f'{target.name} will respond at end of week.', Colors.DIM)}")
            
            # Show pending challenges count
            pending = self._division_ladder.get_pending_challenges_for_fighter(challenger.fighter_id)
            print(f"  {colored(f'Pending challenges: {len(pending)}', Colors.DIM)}")
            
            # Show remaining challenges this week
            challenges_used = self._division_ladder._challenges_this_week.get(challenger.fighter_id, 0)
            challenges_remaining = 2 - challenges_used
            if challenges_remaining > 0:
                print(f"  {colored(f'You can send {challenges_remaining} more challenge(s) this week.', Colors.GREEN)}")
            
            print()
            
            # Note: Training camp will be offered when challenge is accepted
            print(f"  {colored('Tip: Training camp can be started after your challenge is accepted.', Colors.DIM)}")
            pause()
        else:
            # Failed to send (e.g., weekly limit reached)
            print()
            print(f"  {colored('Could not send challenge', Colors.RED)}")
            print(f"  {colored(result.message, Colors.DIM)}")
            pause()

    def _challenge_flow(
        self, 
        division: str, 
        ladder: List, 
        player_entries: List
    ) -> None:
        """Handle the challenge issuance flow."""
        # Filter to available player fighters
        available = [e for e in player_entries if e.status == FighterStatus.AVAILABLE]
        
        if not available:
            print()
            print(f"  {colored('No fighters available to issue challenges.', Colors.RED)}")
            pause()
            return
        
        # Select which fighter to issue challenge
        if len(available) == 1:
            challenger = available[0]
        else:
            print()
            print(f"  {colored('Select fighter to issue challenge:', Colors.CYAN)}")
            for i, entry in enumerate(available, 1):
                rank_str = f"#{entry.rank}" if entry.rank else "UR"
                print(f"  [{i}] {entry.name} ({rank_str})")
            print(f"  [0] Cancel")
            print()
            
            choice = get_input("Select: ")
            if choice == "0":
                return
            try:
                idx = int(choice)
                if 1 <= idx <= len(available):
                    challenger = available[idx - 1]
                else:
                    return
            except ValueError:
                return
        
        # Get challenge options
        week = self.game_state.week_number
        options = self._division_ladder.get_challenge_options(challenger, ladder, week)
        
        if not options:
            print()
            print(f"  {colored('No opponents available to challenge.', Colors.RED)}")
            print(f"  {colored('(You may have already issued a challenge this week)', Colors.DIM)}")
            pause()
            return
        
        # Display challenge options
        clear_screen()
        print_header(f"CHALLENGE OPTIONS - {challenger.name}")
        
        print(f"  {colored(challenger.name, Colors.HIGHLIGHT)} ({challenger.rank_display} | {challenger.overall_rating} OVR)")
        print()
        print(f"  {colored('Available Targets:', Colors.CYAN)}")
        print(f"  {'-' * 60}")
        print()
        
        # Group by type
        step_ups = [o for o in options if "Step Up" in o.challenge_type or o.challenge_type == "Title Shot"]
        laterals = [o for o in options if o.challenge_type in ("Lateral", "Defend")]
        safe = [o for o in options if o.challenge_type == "Safe Win"]
        
        display_options = []
        
        if step_ups:
            print(f"  {colored('CLIMB (Step Up)', Colors.GREEN)}")
            for opt in step_ups[:3]:
                display_options.append(opt)
                self._display_challenge_option(len(display_options), opt)
            print()
        
        if laterals:
            print(f"  {colored('HOLD (Defend Position)', Colors.CYAN)}")
            for opt in laterals[:2]:
                display_options.append(opt)
                self._display_challenge_option(len(display_options), opt)
            print()
        
        if safe:
            print(f"  {colored('BUILD (Safe Win)', Colors.DIM)}")
            for opt in safe[:2]:
                display_options.append(opt)
                self._display_challenge_option(len(display_options), opt)
            print()
        
        print(f"  [0] Cancel")
        print()
        
        choice = get_input("Issue challenge to: ")
        
        if choice == "0":
            return
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(display_options):
                selected = display_options[idx - 1]
                self._issue_challenge(challenger, selected, week, division)
        except ValueError:
            pass
    
    def _display_challenge_option(self, num: int, option) -> None:
        """Display a single challenge option."""
        target = option.target
        
        rank_str = f"#{target.rank}" if target.rank else "UR"
        if target.rank == 0:
            rank_str = colored("[C]", Colors.GOLD)
        
        accept_pct = int(option.accept_probability * 100)
        
        # Color accept probability
        if accept_pct >= 80:
            pct_color = Colors.GREEN
        elif accept_pct >= 50:
            pct_color = Colors.YELLOW
        else:
            pct_color = Colors.RED
        
        print(f"  [{num}] {rank_str:>4} {target.name:<20} {target.overall_rating} OVR")
        print(f"       {colored(option.challenge_type, Colors.CYAN)} | {colored(f'{accept_pct}% Accept', pct_color)} | {option.risk_reward}")
    
    def _issue_challenge(self, challenger, option, week: int, division: str) -> None:
        """Issue the challenge and handle response."""
        target = option.target
        
        # Issue the challenge (queues as pending - resolved at end of week)
        result = self._division_ladder.issue_challenge(
            challenger_id=challenger.fighter_id,
            target_id=target.fighter_id,
            challenger_entry=challenger,
            target_entry=target,
            accept_probability=option.accept_probability,
            week=week,
            event_name=f"DFC Fight Night {self.next_event_number}",
        )
        
        clear_screen()
        
        if result.accepted:
            # Challenge was successfully SENT (not yet accepted by opponent)
            # The fight will be resolved at end of week when we advance
            print_header("CHALLENGE SENT!")
            print()
            print(f"  {colored('[>]', Colors.CYAN)} Challenge sent to {target.name}!")
            print()
            
            # Show acceptance probability
            accept_pct = int(option.accept_probability * 100)
            if accept_pct >= 70:
                pct_color = Colors.GREEN
                outlook = "Very likely to accept"
            elif accept_pct >= 40:
                pct_color = Colors.YELLOW
                outlook = "May accept"
            else:
                pct_color = Colors.RED
                outlook = "Unlikely to accept"
            
            print(f"  Acceptance Chance: {colored(f'{accept_pct}%', pct_color)} ({outlook})")
            print()
            print(f"  {colored('Response will come when you advance the week.', Colors.DIM)}")
            print()
            
            # Show pending challenges count
            pending = self._division_ladder.get_pending_challenges_for_fighter(challenger.fighter_id)
            if len(pending) > 1:
                print(f"  {colored(f'[!] You have {len(pending)} pending challenges out', Colors.YELLOW)}")
                print(f"  {colored('Note: Fighters typically only accept one fight at a time.', Colors.DIM)}")
                print()
            
            # Show title fight indicator
            if result.is_title_fight:
                print(f"  {colored('[TITLE FIGHT]', Colors.GOLD)} This would be a title fight!")
                print()
            
            print(f"  {colored('Tip: Training camp can be started after your challenge is accepted.', Colors.DIM)}")
            print()
            
            pause()
        else:
            # Challenge could not be sent (limit reached, duplicate, etc.)
            print_header("CHALLENGE FAILED")
            print()
            print(f"  {colored('[X]', Colors.RED)} Could not send challenge to {target.name}.")
            print()
            print(f"  {colored(result.message, Colors.DIM)}")
            print()
            
            # Suggest alternative
            if result.suggested_alternative:
                alt = self.game_state.fighters.get(result.suggested_alternative)
                if alt:
                    print(f"  {colored('[!] TIP:', Colors.GREEN)} Try {alt.name} - more likely to accept")
            
            pause()
    
    def _check_incoming_challenges(self) -> None:
        """Check and display any incoming challenges."""
        if not self._division_ladder:
            return
        
        game = self.game_state
        player_camp = game.get_player_camp()
        if not player_camp:
            return
        
        # Get all player fighters
        player_fighters = [
            f for f in game.fighters.values()
            if getattr(f, 'camp_id', None) == player_camp.camp_id and f.is_active
        ]
        
        # Check for pending challenges for each fighter
        for fighter in player_fighters:
            challenges = self._division_ladder.get_pending_challenges(fighter.fighter_id)
            for challenge in challenges:
                self._show_incoming_challenge(challenge)
    
    def _show_incoming_challenge(self, challenge) -> None:
        """Display an incoming challenge and get player response."""
        clear_screen()
        print_header("[M] INCOMING CHALLENGE")
        print()
        
        rank_str = f"#{challenge.challenger_rank}" if challenge.challenger_rank else "Unranked"
        
        print(f"  {colored(challenge.challenger_name, Colors.YELLOW)} wants to fight your fighter:")
        print(f"  {colored(challenge.target_name, Colors.HIGHLIGHT)}")
        print()
        
        print(f"  {'-' * 50}")
        print(f"  Challenger: {rank_str} {challenge.challenger_name}")
        print(f"  Record: {challenge.challenger_record}")
        print(f"  Rating: {challenge.challenger_rating} OVR")
        print(f"  Streak: {challenge.challenger_streak}")
        print(f"  {'-' * 50}")
        print()
        
        print(f"  \"{colored(challenge.message, Colors.DIM)}\"")
        print()
        
        # Show consequences
        print(f"  {colored('If you DECLINE:', Colors.RED)}")
        print(f"    * Reputation: -{challenge.decline_reputation_cost}")
        print(f"    * Ranking freeze: {challenge.decline_ranking_freeze} weeks")
        print(f"    * Media narrative: \"ducking\" accusations")
        print()
        
        print(f"  [A] {colored('Accept Challenge', Colors.GREEN)}")
        print(f"  [D] {colored('Decline', Colors.RED)} (consequences apply)")
        print()
        
        while True:
            choice = get_input("Response: ").strip().lower()
            
            if choice == "a":
                break
            elif choice == "d":
                break
            else:
                print(f"  {colored('Invalid choice. Enter A to accept or D to decline.', Colors.DIM)}")
        
        week = self.game_state.week_number
        
        if choice == "a":
            # Accept
            success, _ = self._division_ladder.respond_to_challenge(challenge, True, week)
            
            weeks_until = random.randint(6, 8)
            
            # Schedule fight
            fight_data = {
                "fighter1_id": challenge.target_id,
                "fighter1_name": challenge.target_name,
                "fighter2_id": challenge.challenger_id,
                "fighter2_name": challenge.challenger_name,
                "weight_class": challenge.weight_class,
                "is_title_fight": False,
                "weeks_until": weeks_until,
                "event_name": f"DFC Fight Night {self.next_event_number}",  # Proper event name
                "purse": self._calculate_purse(challenge.challenger_rating, False),
            }
            self.player_scheduled_fights.append(fight_data)
            
            print()
            print(f"  {colored('[OK] Challenge accepted!', Colors.GREEN)}")
            print(f"  Fight scheduled for Week {week + weeks_until}")
            print()
            
            # Offer to start training camp
            start_camp = get_input("  Start training camp now? [Y/N]: ").strip().lower()
            if start_camp == "y":
                fighter_full = self.fighter_data.get(challenge.target_id)
                if fighter_full:
                    self.start_training_camp_for_fight(fighter_full, weeks_until)
        elif choice == "d":
            # Decline
            success, consequence = self._division_ladder.respond_to_challenge(challenge, False, week)
            
            # Apply consequences
            target_data = self.fighter_data.get(challenge.target_id)
            if target_data:
                # Reduce reputation/popularity
                if hasattr(target_data, 'reputation'):
                    target_data.reputation = max(0, target_data.reputation - consequence.reputation_loss)
                if hasattr(target_data, 'popularity'):
                    target_data.popularity = max(0, target_data.popularity - consequence.popularity_loss)
            
            # Add news
            self.news_feed.append(NewsItem(
                headline=consequence.narrative,
                details=f"{challenge.target_name} declined to fight {challenge.challenger_name}",
                category="controversy",
                week=week,
            ))
            
            print()
            print(f"  {colored('Challenge declined.', Colors.RED)}")
            print(f"  {consequence.narrative}")
            print(f"  {challenge.target_name}'s ranking is frozen for {consequence.ranking_freeze_weeks} weeks.")
            pause()
    
    def _ladder_fighter_details(self, ladder: List) -> None:
        """View details of a fighter on the ladder."""
        # Build a quick reference of who's visible
        ranked_fighters = [(e.rank, e.name) for e in ladder if e.rank is not None and e.rank > 0]
        has_champion = any(e.rank == 0 for e in ladder)
        
        print()
        if has_champion or ranked_fighters:
            print(f"  {colored('Enter:', Colors.CYAN)} [C] for Champion, [#] for rank, or fighter name")
        else:
            print(f"  {colored('Enter:', Colors.CYAN)} Fighter name to view details")
        
        choice = get_input("  View: ").strip()
        
        if not choice:
            return
        
        # Handle "C" for champion
        if choice.upper() == "C":
            for entry in ladder:
                if entry.rank == 0:
                    fighter = self.game_state.fighters.get(entry.fighter_id)
                    if fighter:
                        self.show_fighter_details(fighter)
                    return
            print(f"  {colored('No champion found.', Colors.RED)}")
            pause()
            return
        
        # Try to find by rank number
        try:
            rank_num = int(choice)
            for entry in ladder:
                if entry.rank == rank_num:
                    fighter = self.game_state.fighters.get(entry.fighter_id)
                    if fighter:
                        self.show_fighter_details(fighter)
                    return
            print(f"  {colored(f'No fighter at rank #{rank_num}.', Colors.RED)}")
            pause()
            return
        except ValueError:
            pass
        
        # Try by name (partial match)
        matches = [e for e in ladder if choice.lower() in e.name.lower()]
        
        if len(matches) == 1:
            fighter = self.game_state.fighters.get(matches[0].fighter_id)
            if fighter:
                self.show_fighter_details(fighter)
            return
        elif len(matches) > 1:
            print(f"\n  {colored('Multiple matches:', Colors.CYAN)}")
            for i, m in enumerate(matches[:5], 1):
                rank_str = f"#{m.rank}" if m.rank and m.rank > 0 else ("[C]" if m.rank == 0 else "UR")
                print(f"  [{i}] {rank_str} {m.name}")
            print()
            sub_choice = get_input("  Select: ").strip()
            try:
                idx = int(sub_choice) - 1
                if 0 <= idx < len(matches[:5]):
                    fighter = self.game_state.fighters.get(matches[idx].fighter_id)
                    if fighter:
                        self.show_fighter_details(fighter)
                    return
            except ValueError:
                pass
        else:
            print(f"  {colored('Fighter not found.', Colors.RED)}")
            pause()
    
    def _calculate_purse(self, rating: int, is_title: bool) -> int:
        """Calculate fight purse based on rating and title status."""
        base = 5000 + (rating - 60) * 500
        if is_title:
            base *= 3
        return max(5000, base)

    # -------------------------------------------------------------------------
    # Inbox System
    # -------------------------------------------------------------------------
    
    def show_inbox(self) -> None:
        """Display the unified inbox with all notifications."""
        if not INBOX_AVAILABLE or not self._inbox:
            # Fallback to old fight offers
            self.show_fight_offers()
            return
        
        while True:
            clear_screen()
            print_header("[M] INBOX")
            
            notifications = self._inbox.get_all()
            unread_count = self._inbox.get_unread_count()
            
            # Summary line
            if unread_count > 0:
                print(f"  {colored(f'{unread_count} unread notification(s)', Colors.YELLOW)}")
            else:
                print(f"  {colored('All caught up!', Colors.GREEN)}")
            print()
            
            # Category counts with color coding
            offer_count = self._inbox.get_count_by_type(NotificationType.FIGHT_OFFER)
            challenge_count = self._inbox.get_count_by_type(NotificationType.INCOMING_CHALLENGE)
            scout_count = self._inbox.get_count_by_type(NotificationType.SCOUT_REPORT)
            
            if offer_count > 0 or challenge_count > 0 or scout_count > 0:
                category_parts = []
                if offer_count > 0:
                    category_parts.append(colored(f"[S] {offer_count} Fight Offers", Colors.YELLOW))
                if challenge_count > 0:
                    category_parts.append(colored(f"[T] {challenge_count} Challenges", Colors.ORANGE))
                if scout_count > 0:
                    category_parts.append(colored(f"[>] {scout_count} Scout Reports", Colors.GREEN))
                print(f"  {' | '.join(category_parts)}")
                print()
            
            if not notifications:
                print(f"  {colored('Your inbox is empty.', Colors.DIM)}")
                print()
                print(f"  {colored('TIP:', Colors.CYAN)} Fight offers refresh every 2 weeks.")
                print(f"       Your coaches will scout promising amateurs.")
                pause()
                return
            
            print(f"  {'-' * 66}")
            
            # Display notifications grouped by priority
            displayed = 0
            max_display = 15
            
            for i, notif in enumerate(notifications[:max_display]):
                displayed += 1
                
                # Priority color
                if notif.priority == NotificationPriority.CRITICAL:
                    priority_color = Colors.RED
                    priority_marker = ""
                elif notif.priority == NotificationPriority.HIGH:
                    priority_color = Colors.ORANGE
                    priority_marker = "[!]"
                elif notif.priority == NotificationPriority.MEDIUM:
                    priority_color = Colors.YELLOW
                    priority_marker = "*"
                else:
                    priority_color = Colors.DIM
                    priority_marker = "*"
                
                # Unread indicator
                if notif.is_read:
                    read_marker = " "
                else:
                    read_marker = colored("*", Colors.CYAN)
                
                # Notification line
                icon = notif.icon
                title = notif.title[:50] + "..." if len(notif.title) > 50 else notif.title
                
                # Color based on type
                if notif.notification_type == NotificationType.FIGHT_OFFER:
                    title_colored = colored(title, Colors.YELLOW)
                elif notif.notification_type == NotificationType.INCOMING_CHALLENGE:
                    title_colored = colored(title, Colors.ORANGE)
                elif notif.notification_type == NotificationType.SCOUT_REPORT:
                    title_colored = colored(title, Colors.GREEN)
                elif notif.notification_type == NotificationType.TITLE_OPPORTUNITY:
                    title_colored = colored(title, Colors.GOLD)
                elif notif.notification_type == NotificationType.FINANCIAL_ALERT:
                    title_colored = colored(title, Colors.RED if notif.priority == NotificationPriority.CRITICAL else Colors.YELLOW)
                elif notif.notification_type == NotificationType.INJURY_UPDATE:
                    title_colored = colored(title, Colors.CYAN)
                else:
                    title_colored = title
                
                print(f"  {read_marker} [{i+1:2}] {icon} {title_colored}")
            
            if len(notifications) > max_display:
                print(f"  {colored(f'    ... and {len(notifications) - max_display} more', Colors.DIM)}")
            
            print(f"  {'-' * 66}")
            print()
            
            # Menu options
            options = [
                ("#", "View notification details"),
                ("F", f"Fight Offers ({offer_count})") if offer_count > 0 else None,
                ("S", f"Scout Reports ({scout_count})") if scout_count > 0 else None,
                ("R", "Mark all as read"),
                ("C", "Clear read notifications"),
                ("0", "Back"),
            ]
            options = [o for o in options if o is not None]
            print_menu(options)
            
            valid_choices = ["0", "r", "c"]
            if offer_count > 0:
                valid_choices.append("f")
            if scout_count > 0:
                valid_choices.append("s")
            valid_choices.extend([str(i) for i in range(1, min(displayed + 1, max_display + 1))])
            
            choice = get_choice(valid_choices).lower()
            
            if choice == "0":
                return
            elif choice == "r":
                self._inbox.mark_all_read()
                print(f"  {colored('[OK] All marked as read', Colors.GREEN)}")
                pause()
            elif choice == "c":
                # Clear read notifications
                cleared = 0
                for n in list(self._inbox.notifications):
                    if n.is_read and not n.is_actionable:
                        self._inbox.dismiss(n.notification_id)
                        cleared += 1
                print(f"  {colored(f'[OK] Cleared {cleared} notifications', Colors.GREEN)}")
                pause()
            elif choice == "f":
                self._show_inbox_fight_offers()
            elif choice == "s":
                self._show_inbox_scout_reports()
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(notifications):
                        self._view_notification_detail(notifications[idx])
                except ValueError:
                    pass
    
    def _show_inbox_fight_offers(self) -> None:
        """Show fight offers from inbox."""
        if not INBOX_AVAILABLE or not self._inbox:
            self.show_fight_offers()
            return
        
        offers = self._inbox.get_fight_offers()
        
        while True:
            clear_screen()
            print_header("[S] FIGHT OFFERS")
            
            tier = self._get_camp_tier()
            min_weeks = MIN_WEEKS_BY_TIER.get(tier, 4)
            max_weeks = MAX_WEEKS_BY_TIER.get(tier, 8)
            
            print(f"  {colored('Camp:', Colors.CYAN)} {tier} | Schedule window: {min_weeks}-{max_weeks} weeks")
            print()
            
            if not offers:
                print(f"  {colored('No fight offers at this time.', Colors.DIM)}")
                print()
                print(f"  {colored('TIP:', Colors.YELLOW)} Offers generate every 2 weeks.")
                pause()
                return
            
            # Group by fighter
            offers_by_fighter = {}
            for offer in offers:
                fid = offer.fighter_id
                if fid not in offers_by_fighter:
                    offers_by_fighter[fid] = []
                offers_by_fighter[fid].append(offer)
            
            print(f"  {colored(f'{len(offers)} Available Offers', Colors.WIN)}")
            print()
            
            idx = 0
            offer_list = []
            for fighter_id, fighter_offers in offers_by_fighter.items():
                fighter = self.game_state.fighters.get(fighter_id)
                if not fighter:
                    continue
                
                f_rank = self._get_fighter_division_rank(fighter)
                rank_str = f"#{f_rank}" if f_rank else "Unranked"
                div_abbrev = self._get_division_abbrev(fighter.weight_class)
                
                print(f"  {colored(fighter.name, Colors.CYAN)} ({rank_str} {div_abbrev}) - {fighter.wins}-{fighter.losses}")
                
                for offer in fighter_offers:
                    idx += 1
                    offer_list.append(offer)
                    
                    # Mark as read when displayed
                    self._inbox.mark_read(offer.notification_id)
                    
                    # Get offer data
                    data = offer.action_data
                    opp_name = data.get("opponent_name", "Unknown")
                    opp_rank = data.get("opponent_rank")
                    opp_record = data.get("opponent_record", "0-0")
                    opp_rating = data.get("opponent_rating", 50)
                    matchup_quality = data.get("matchup_quality", "competitive")
                    accept_chance = data.get("accept_chance", 50)
                    
                    opp_rank_str = f"#{opp_rank}" if opp_rank else "UR"
                    
                    # Quality color
                    if matchup_quality == "step_up":
                        quality_color = Colors.ORANGE
                        quality_str = ""
                    elif matchup_quality == "step_down":
                        quality_color = Colors.GREEN
                        quality_str = ""
                    else:
                        quality_color = Colors.CYAN
                        quality_str = "[T]"
                    
                    # Accept chance color
                    if accept_chance >= 70:
                        chance_color = Colors.GREEN
                    elif accept_chance >= 40:
                        chance_color = Colors.YELLOW
                    else:
                        chance_color = Colors.RED
                    
                    print(f"    [{idx}] {quality_str} vs {colored(opp_name, quality_color)} ({opp_rank_str}, {opp_record}) {opp_rating} OVR")
                    print(f"        Accept: {colored(f'{accept_chance}%', chance_color)}")
                
                print()
            
            print(f"  {'-' * 66}")
            options = [
                ("#", "Accept offer"),
                ("0", "Back"),
            ]
            print_menu(options)
            
            valid = ["0"] + [str(i) for i in range(1, idx + 1)]
            choice = get_choice(valid)
            
            if choice == "0":
                return
            
            try:
                sel_idx = int(choice) - 1
                if 0 <= sel_idx < len(offer_list):
                    selected = offer_list[sel_idx]
                    self._accept_inbox_fight_offer(selected)
                    # Refresh offers list
                    offers = self._inbox.get_fight_offers()
            except ValueError:
                pass
    
    def _show_inbox_scout_reports(self) -> None:
        """Show scout reports from inbox."""
        if not INBOX_AVAILABLE or not self._inbox:
            return
        
        reports = self._inbox.get_scout_reports()
        
        while True:
            clear_screen()
            print_header("[>] SCOUT REPORTS")
            
            print(f"  Your coaches have identified promising prospects.")
            print()
            
            if not reports:
                print(f"  {colored('No scout reports at this time.', Colors.DIM)}")
                print()
                print(f"  {colored('TIP:', Colors.YELLOW)} Coaches scout based on their specialty.")
                print(f"       A BJJ coach will find grapplers in your region.")
                pause()
                return
            
            print(f"  {colored(f'{len(reports)} Scout Reports', Colors.GREEN)}")
            print()
            
            for i, report in enumerate(reports[:10]):
                # Mark as read when displayed
                self._inbox.mark_read(report.notification_id)
                
                data = report.action_data
                name = data.get("fighter_name", "Unknown")
                age = data.get("age", 20)
                wc = data.get("weight_class", "")
                ovr = data.get("overall_rating", 50)
                potential = data.get("potential", "Average")
                ceiling = data.get("ceiling", 70)
                style = data.get("fighting_style", "Balanced")
                region = data.get("region", "")
                record = data.get("record", "0-0")
                traits = data.get("notable_traits", [])
                reason = data.get("reason", "")
                
                # Potential color
                if potential == "Elite":
                    pot_color = Colors.GOLD
                    pot_icon = "[*]"
                elif potential == "High":
                    pot_color = Colors.GREEN
                    pot_icon = "[!]"
                else:
                    pot_color = Colors.DIM
                    pot_icon = "[=]"
                
                div_abbrev = self._get_division_abbrev(wc) if wc else wc
                
                print(f"  [{i+1}] {pot_icon} {colored(name, pot_color)} ({age}yo {div_abbrev})")
                print(f"      {ovr} OVR | {colored(f'{potential} (^{ceiling})', pot_color)} | {record}")
                print(f"      Style: {style} | Region: {region}")
                if traits:
                    print(f"      Traits: {', '.join(traits[:3])}")
                print(f"      {colored(f'[N] {reason}', Colors.DIM)}")
                print()
            
            print(f"  {'-' * 66}")
            options = [
                ("#", "View in Amateur Circuit"),
                ("D", "Dismiss all reports"),
                ("0", "Back"),
            ]
            print_menu(options)
            
            valid = ["0", "d"] + [str(i) for i in range(1, min(len(reports) + 1, 11))]
            choice = get_choice(valid).lower()
            
            if choice == "0":
                return
            elif choice == "d":
                for r in reports:
                    self._inbox.dismiss(r.notification_id)
                print(f"  {colored('[OK] All scout reports dismissed', Colors.GREEN)}")
                pause()
                return
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(reports):
                        # Could open amateur details here
                        fighter_id = reports[idx].fighter_id
                        print(f"  {colored('^ View in Amateur Circuit to sign this fighter', Colors.CYAN)}")
                        pause()
                except ValueError:
                    pass
    
    def _view_notification_detail(self, notification: Notification) -> None:
        """View full details of a notification."""
        if not INBOX_AVAILABLE or not self._inbox:
            return
        
        # Mark as read
        self._inbox.mark_read(notification.notification_id)
        
        clear_screen()
        
        # Type-specific header color
        if notification.notification_type == NotificationType.FIGHT_OFFER:
            print_header("[S] FIGHT OFFER")
        elif notification.notification_type == NotificationType.INCOMING_CHALLENGE:
            print_header("[T] INCOMING CHALLENGE")
        elif notification.notification_type == NotificationType.SCOUT_REPORT:
            print_header("[>] SCOUT REPORT")
        elif notification.notification_type == NotificationType.TITLE_OPPORTUNITY:
            print_header("[T] TITLE OPPORTUNITY")
        elif notification.notification_type == NotificationType.FINANCIAL_ALERT:
            print_header("[$] FINANCIAL ALERT")
        elif notification.notification_type == NotificationType.INJURY_UPDATE:
            print_header("[H] INJURY UPDATE")
        elif notification.notification_type == NotificationType.RANKING_CHANGE:
            print_header("[=] RANKING CHANGE")
        else:
            print_header("[M] NOTIFICATION")
        
        print()
        print(f"  {colored(notification.title, Colors.WHITE)}")
        print()
        
        # Body with proper formatting
        for line in notification.body.split('\n'):
            print(f"  {line}")
        
        print()
        print(f"  {colored(f'Week {notification.week_created}', Colors.DIM)}")
        print()
        
        # Action options based on type
        if notification.notification_type == NotificationType.FIGHT_OFFER:
            options = [
                ("A", "Accept this offer"),
                ("0", "Back"),
            ]
            print_menu(options)
            choice = get_choice(["a", "0"]).lower()
            if choice == "a":
                self._accept_inbox_fight_offer(notification)
        elif notification.notification_type == NotificationType.INCOMING_CHALLENGE:
            options = [
                ("L", "View in Division Ladder"),
                ("0", "Back"),
            ]
            print_menu(options)
            choice = get_choice(["l", "0"]).lower()
            if choice == "l":
                self.show_division_ladder()
        else:
            pause()
    
    def _accept_inbox_fight_offer(self, notification: Notification) -> None:
        """Accept a fight offer from the inbox."""
        if not notification.action_data:
            print(f"  {colored('Error: No offer data available.', Colors.RED)}")
            pause()
            return
        
        data = notification.action_data
        fighter_id = data.get("fighter_id")
        opponent_id = data.get("opponent_id")
        opponent_name = data.get("opponent_name", "Unknown")
        weeks_until = data.get("weeks_until", 8)
        is_title = data.get("is_title_fight", False)
        is_main = data.get("is_main_event", False)
        purse = data.get("purse", 5000)
        win_bonus = data.get("win_bonus", 2500)
        
        fighter = self.game_state.fighters.get(fighter_id)
        opponent = self.game_state.fighters.get(opponent_id)
        
        if not fighter or not opponent:
            print(f"  {colored('Error: Fighter not found.', Colors.RED)}")
            pause()
            return
        
        # Confirm
        print()
        print(f"  {colored('CONFIRM FIGHT:', Colors.CYAN)}")
        print(f"  {fighter.name} vs {opponent_name}")
        print(f"  In {weeks_until} weeks")
        if is_title:
            print(f"  {colored('[T] TITLE FIGHT', Colors.GOLD)}")
        print(f"  Purse: ${purse:,} + ${win_bonus:,} win bonus")
        print()
        
        confirm = input("  Accept? (y/n): ").strip().lower()
        
        if confirm == 'y':
            # Schedule the fight
            event_name = f"DFC {'PPV' if is_main else 'Fight Night'} {self.game_state.week_number + weeks_until}"
            
            self.player_scheduled_fights.append({
                "fighter1_id": fighter_id,
                "fighter1_name": fighter.name,
                "fighter2_id": opponent_id,
                "fighter2_name": opponent_name,
                "weight_class": fighter.weight_class,
                "weeks_until": weeks_until,
                "is_title_fight": is_title,
                "is_main_event": is_main,
                "event_name": event_name,
                "purse": purse,
                "win_bonus": win_bonus,
            })
            
            # Remove the notification
            self._inbox.dismiss(notification.notification_id)
            
            # Start training camp flow
            print(f"  {colored('[OK] Fight scheduled!', Colors.GREEN)}")
            print()
            
            # Offer to start training camp
            start_camp = input("  Start training camp now? (y/n): ").strip().lower()
            if start_camp == 'y':
                fighter_full = self.fighter_data.get(fighter_id)
                if fighter_full:
                    self.start_training_camp_for_fight(fighter_full, weeks_until)
                else:
                    print(f"  {colored('Could not start camp - fighter data not found.', Colors.RED)}")
        else:
            print(f"  {colored('Offer declined.', Colors.DIM)}")
            pause()

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
        
        # =================================================================
        # DOPAMINE: POTENTIAL RANK GAIN - Show what's at stake!
        # =================================================================
        potential_gain = ""
        your_fighter = self.game_state.fighters.get(offer.fighter_id) if hasattr(offer, 'fighter_id') else None
        if your_fighter and opp_rank:
            your_rank = self._get_fighter_division_rank(your_fighter)
            if your_rank and opp_rank < your_rank:
                # Beating higher ranked = could take their spot
                potential_gain = colored(f"^ #{opp_rank}!", Colors.GREEN)
            elif not your_rank and opp_rank <= 15:
                # Unranked beating ranked = enter rankings
                potential_gain = colored(f"^ RANKED!", Colors.GREEN)
        
        if offer.is_title_fight:
            if your_fighter and not self._is_division_champion(your_fighter):
                potential_gain = colored("^ CHAMPION!", Colors.GOLD)
        
        # Risk/Reward stars
        risk = matchup.get("risk", 3) if matchup else 3
        reward = matchup.get("reward", 3) if matchup else 3
        risk_str = colored("*" * risk + "-" * (5-risk), Colors.RED if risk >= 4 else Colors.YELLOW if risk >= 3 else Colors.GREEN)
        reward_str = colored("*" * reward + "-" * (5-reward), Colors.GREEN if reward >= 4 else Colors.CYAN)
        
        # Print
        print()
        print(f"    [{colored(str(index), Colors.CYAN)}] vs {colored(offer.opponent_name, Colors.HIGHLIGHT)} {potential_gain}")
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
                if opp_fighter and self._is_division_champion(opp_fighter):
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
            opp_fighter = self.game_state.fighters.get(opp_data.fighter_id)
            champ_tag = colored(" CHAMPION", Colors.GOLD) if opp_fighter and self._is_division_champion(opp_fighter) else ""
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
                print(f"    Grade: {report.potential.potential_grade}")
                print(f"    Current: {report.potential.current_overall}")
                print(f"    Ceiling: {report.potential.potential_ceiling}")
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
        
        # Build stats dicts for module functions (map new names to gameplan expectations)
        fighter_stats = {}
        opp_stats = {}
        
        if your_data:
            fighter_stats = {
                "boxing": your_data.boxing,
                "kicks": your_data.kicks,
                "wrestling": your_data.takedowns,
                "bjj": your_data.submissions,
                "power": getattr(your_data, 'strength', 50),
                "cardio": your_data.cardio,
                "chin": your_data.chin,
                "strength": getattr(your_data, 'strength', 50),
                "speed": getattr(your_data, 'speed', 50),
            }
        
        if opp_data:
            opp_stats = {
                "boxing": opp_data.boxing,
                "kicks": opp_data.kicks,
                "wrestling": opp_data.takedowns,
                "bjj": opp_data.submissions,
                "power": getattr(opp_data, 'strength', 50),
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
        
        # Assign proper event name at scheduling time
        scheduled_event_name = f"DFC Fight Night {self.next_event_number}"
        
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
            "event_name": scheduled_event_name,
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
        
        # Build stats for module functions (map new names to expectations)
        fighter_stats = {
            "boxing": fighter.boxing,
            "kicks": fighter.kicks,
            "wrestling": fighter.takedowns,
            "bjj": fighter.submissions,
            "cardio": fighter.cardio,
        }
        
        opp_stats = None
        if opponent_data:
            opp_stats = {
                "boxing": opponent_data.boxing,
                "kicks": opponent_data.kicks,
                "wrestling": opponent_data.takedowns,
                "bjj": opponent_data.submissions,
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
                        # Handle both Coach and StartingCoach types
                        quality = getattr(coach, 'quality', None)
                        if quality is None:
                            skill_level = getattr(coach, 'skill_level', 60)
                            quality = min(100, max(20, skill_level))
                        
                        stars = "*" * (quality // 20) + "-" * (5 - quality // 20)
                        specialty = getattr(coach, 'specialty', 'General')
                        specialty = specialty.value if hasattr(specialty, 'value') else str(specialty)
                        bonus_pct = quality // 10
                        
                        coach_name = getattr(coach, 'name', 'Coach')
                        print(f"  [{i}] {coach_name}")
                        print(f"      {specialty} Specialist | [{stars}] | +{bonus_pct}% training bonus")
                    
                    print(f"  [0] Train solo (no coach bonus)")
                    print()
                    
                    coach_choice = get_input("Select coach: ").strip()
                    try:
                        coach_idx = int(coach_choice)
                        if 1 <= coach_idx <= len(coaches[:5]):
                            selected_coach = coaches[coach_idx - 1]
                            specialty = getattr(selected_coach, 'specialty', 'General')
                            coach_specialty = specialty.value if hasattr(specialty, 'value') else str(specialty)
                            coach_quality = getattr(selected_coach, 'quality', None)
                            if coach_quality is None:
                                coach_quality = getattr(selected_coach, 'skill_level', 60)
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
            
            # === CAMP STRATEGY SELECTION (Template) ===
            print()
            print(f"  {colored('SELECT CAMP STRATEGY', Colors.CYAN)}")
            print()
            
            # Import template functions
            from systems.training import (
                CampTemplate, TEMPLATE_INFO, generate_camp_schedule, 
                estimate_template_fatigue
            )
            
            # Get fighter's current fatigue
            fighter_fatigue = getattr(fighter, 'fatigue', 0)
            
            # Display template options
            color_map = {
                "Low": Colors.GREEN,
                "Medium": Colors.YELLOW,
                "HIGH": Colors.RED,
                "None": Colors.CYAN,
            }
            
            templates = list(CampTemplate)
            for i, template in enumerate(templates, 1):
                info = TEMPLATE_INFO[template]
                min_fat, expected_fat, max_fat = estimate_template_fatigue(template, camp_duration)
                projected_final = fighter_fatigue + expected_fat
                
                # Determine arrival condition
                if projected_final <= 20:
                    arrival = colored("Fresh", Colors.GREEN)
                elif projected_final <= 40:
                    arrival = colored("Rested", Colors.CYAN)
                elif projected_final <= 60:
                    arrival = colored("Ready", Colors.YELLOW)
                elif projected_final <= 80:
                    arrival = colored("Tired", Colors.ORANGE)
                else:
                    arrival = colored("EXHAUSTED", Colors.RED)
                
                risk_color = color_map.get(info["risk"], Colors.WHITE)
                
                # Template header
                print(f"  [{i}] {info['icon']} {colored(info['name'], Colors.HIGHLIGHT)}")
                print(f"      {info['description']}")
                print(f"      Risk: {colored(info['risk'], risk_color)} + Gains: {info['gains']} + Fatigue: +{expected_fat}")
                
                # Show schedule preview
                schedule = generate_camp_schedule(template, camp_duration)
                schedule_preview = " ^ ".join([
                    {"REST": "REST", "LIGHT": "LIGHT", "MODERATE": "MOD", "INTENSE": "INT", "EXTREME": "EXT"}.get(s.name, "?")
                    for s in schedule
                ])
                print(f"      Schedule: {colored(schedule_preview, Colors.DIM)}")
                print(f"      Arrival Condition: {arrival}")
                print()
            
            # Default to Steady Build
            default_choice = "1"
            template_choice = get_input(f"Select strategy [{default_choice}]: ").strip()
            if not template_choice or template_choice not in ["1", "2", "3", "4", "5"]:
                template_choice = default_choice
            
            selected_template = templates[int(template_choice) - 1]
            selected_template_name = TEMPLATE_INFO[selected_template]["name"]
            selected_schedule = generate_camp_schedule(selected_template, camp_duration)
            
            print()
            print_divider()
            
            # === CAMP SUMMARY ===
            print()
            print(f"  {colored('CAMP SUMMARY', Colors.CYAN)}")
            print()
            
            age = getattr(fighter, 'age', 28)
            min_fat, expected_fat, max_fat = estimate_template_fatigue(selected_template, camp_duration)
            projected_final = fighter_fatigue + expected_fat
            
            # Arrival condition
            if projected_final <= 20:
                arrival_text = colored("Fresh (100% stamina)", Colors.GREEN)
            elif projected_final <= 40:
                arrival_text = colored("Rested (95% stamina)", Colors.CYAN)
            elif projected_final <= 60:
                arrival_text = colored("Ready (88% stamina)", Colors.YELLOW)
            elif projected_final <= 80:
                arrival_text = colored("Tired (78% stamina)", Colors.ORANGE)
            else:
                arrival_text = colored("EXHAUSTED (65% stamina) [!]", Colors.RED)
            
            print(f"  +{'-' * 48}+")
            print(f"  + {'Fighter:':<15} {fighter.name:<30} +")
            print(f"  + {'Duration:':<15} {camp_duration} weeks{' ' * (27 - len(str(camp_duration)))} +")
            print(f"  + {'Focus:':<15} {selected_focus_name:<30} +")
            print(f"  + {'Strategy:':<15} {selected_template_name:<30} +")
            print(f"  + {'Coach:':<15} {(selected_coach.name if selected_coach else 'None'):<30} +")
            print(f"  -{'-' * 48}+")
            print()
            
            if specialty_matches:
                print(f"  {colored('[OK] Coach specialty matches focus! +25% bonus', Colors.GREEN)}")
            
            print(f"  Current Fatigue: {fighter_fatigue}")
            print(f"  Expected Fatigue: +{expected_fat} (range: +{min_fat} to +{max_fat})")
            print(f"  Fight Night Condition: {arrival_text}")
            print()
            
            # Warning for dangerous fatigue
            if projected_final > 80:
                print(f"  {colored('[!]  WARNING: Fighter will be exhausted for the fight!', Colors.RED)}")
                print(f"  {colored('     Consider a different strategy or wait for recovery.', Colors.DIM)}")
                print()
            elif projected_final > 60:
                print(f"  {colored('[i] Note: Fighter may arrive tired. Monitor fatigue during camp.', Colors.YELLOW)}")
                print()
            
            if not confirm("Start this training camp?"):
                print("Training camp cancelled.")
                return
            
            # === START CAMP WITH TEMPLATE ===
            self._training_system.start_camp(
                fighter_id=fighter.fighter_id,
                camp_id=camp_id,
                focus=selected_focus,
                intensity=selected_schedule[0] if selected_schedule else TrainingIntensity.MODERATE,
                weeks=camp_duration,
                template=selected_template,
            )
            
            print()
            print(colored(f"  *******************************************", Colors.WIN))
            print(colored(f"    {camp_duration}-WEEK TRAINING CAMP STARTED!", Colors.WIN))
            print(colored(f"  *******************************************", Colors.WIN))
            print()
            print(f"  Strategy: {TEMPLATE_INFO[selected_template]['icon']} {selected_template_name}")
            print(f"  Focus: {selected_focus.value}")
            if selected_coach:
                print(f"  Coach: {selected_coach.name}")
            print()
            
        except ImportError as e:
            print(f"Training camp started ({camp_duration} weeks). [Error: {e}]")


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
        """Start training camp with smart recommendations based on opponent analysis."""
        if not self._training_system:
            print("Training started (simplified).")
            return
        
        camp_duration = max(4, min(weeks_until_fight - 1, 8))
        player_camp = self.game_state.get_player_camp()
        camp_id = player_camp.camp_id if player_camp else "player"
        
        # === GATHER OPPONENT DATA ===
        opponent_data = None
        opponent_name = "Unknown"
        opponent_style = "Balanced"
        opponent_record = ""
        fight_info = None
        
        for fight in self.player_scheduled_fights:
            if fight.get("fighter1_id") == fighter.fighter_id:
                opp_id = fight.get("fighter2_id")
                opponent_name = fight.get("fighter2_name", "Unknown")
                opponent_data = self.fighter_data.get(opp_id)
                if not opponent_data:
                    opponent_data = self._create_full_fighter_data(opp_id)
                opp_basic = self.game_state.fighters.get(opp_id)
                if opp_basic:
                    opponent_record = f"{opp_basic.wins}-{opp_basic.losses}"
                if opponent_data:
                    opponent_style = getattr(opponent_data, 'fighting_style', 'Balanced')
                fight_info = fight
                break
        
        # === SMART ANALYSIS ===
        recommended_focus = "6"  # Default: Balanced
        focus_reason = "General preparation"
        recommended_strategy = "1"  # Default: Steady Build
        strategy_reason = "Safe, consistent approach"
        gameplan_preview = None
        
        if opponent_data:
            # Compare stats to find advantages/disadvantages
            your_striking = (fighter.boxing + fighter.kicks + getattr(fighter, 'striking_defense', 50)) / 3
            your_grappling = (fighter.takedowns + fighter.submissions + getattr(fighter, 'takedown_defense', 50)) / 3
            your_cardio = fighter.cardio
            
            opp_striking = (opponent_data.boxing + opponent_data.kicks + getattr(opponent_data, 'striking_defense', 50)) / 3
            opp_grappling = (opponent_data.takedowns + opponent_data.submissions + getattr(opponent_data, 'takedown_defense', 50)) / 3
            opp_cardio = opponent_data.cardio
            
            striking_gap = your_striking - opp_striking
            grappling_gap = your_grappling - opp_grappling
            cardio_gap = your_cardio - opp_cardio
            
            # Determine opponent's primary threat
            opp_primary = "striking" if opp_striking > opp_grappling else "grappling"
            
            # === TRAINING FOCUS RECOMMENDATION ===
            # Priority 1: Shore up your weakness if opponent is strong there
            if opp_grappling > 65 and grappling_gap < -10:
                recommended_focus = "3"  # Wrestling
                focus_reason = f"Opponent ({opponent_name}) has elite grappling ({int(opp_grappling)}). Shore up takedown defense."
            elif opp_striking > 65 and striking_gap < -10:
                recommended_focus = "1"  # Striking
                focus_reason = f"Opponent has dangerous hands ({int(opp_striking)} striking). Improve your striking defense."
            # Priority 2: Maximize your advantage
            elif grappling_gap > 15:
                recommended_focus = "3"  # Wrestling
                focus_reason = f"You have a +{int(grappling_gap)} grappling edge. Sharpen your wrestling to dominate."
            elif striking_gap > 15:
                recommended_focus = "1"  # Striking
                focus_reason = f"You have a +{int(striking_gap)} striking edge. Perfect your combinations."
            # Priority 3: Cardio if it's close
            elif cardio_gap < -10:
                recommended_focus = "4"  # Conditioning
                focus_reason = f"Opponent has better cardio ({opp_cardio} vs {your_cardio}). Avoid gassing late."
            elif abs(striking_gap) < 10 and abs(grappling_gap) < 10:
                recommended_focus = "4"  # Conditioning
                focus_reason = "Evenly matched fighter. Superior conditioning wins close fights."
            else:
                recommended_focus = "6"  # Balanced
                focus_reason = "Well-rounded matchup. Stay sharp everywhere."
            
            # === GAMEPLAN PREVIEW ===
            if grappling_gap > 10 and your_grappling > opp_grappling:
                gameplan_preview = ("Wrestling Heavy", "Take them down and control. Your grappling is superior.")
            elif striking_gap > 10 and your_striking > opp_striking:
                gameplan_preview = ("Keep It Standing", "Stay on the feet. You outclass them on the feet.")
            elif your_cardio > opp_cardio + 10:
                gameplan_preview = ("Pressure Fighter", "Push the pace. They'll fade in later rounds.")
            elif grappling_gap < -10:
                gameplan_preview = ("Defensive Wrestling", "Avoid the mat. Sprawl and keep it standing.")
            else:
                gameplan_preview = ("Balanced Approach", "Mix striking and grappling. Take what they give you.")
        
        # === STRATEGY RECOMMENDATION based on fighter state ===
        fighter_fatigue = getattr(fighter, 'fatigue', 0)
        fighter_age = getattr(fighter, 'age', 28)
        
        # Check for relevant traits
        has_gym_rat = False
        is_injury_prone = False
        fighter_basic = self.game_state.fighters.get(fighter.fighter_id)
        if fighter_basic and hasattr(fighter_basic, 'traits'):
            traits = fighter_basic.traits or []
            has_gym_rat = any("gym" in str(t).lower() for t in traits)
            is_injury_prone = any("injury" in str(t).lower() or "prone" in str(t).lower() for t in traits)
        
        # Strategy logic
        if fighter_fatigue > 50:
            recommended_strategy = "5"  # Recovery Camp
            strategy_reason = f"High fatigue ({fighter_fatigue}%). Recovery to avoid arriving exhausted."
        elif is_injury_prone:
            recommended_strategy = "1"  # Steady Build
            strategy_reason = "Injury prone trait. Conservative training to avoid setbacks."
        elif has_gym_rat and fighter_fatigue < 30:
            recommended_strategy = "3"  # Fast Start
            strategy_reason = "Gym Rat trait + low fatigue. Can push hard early, then taper."
        elif weeks_until_fight >= 8 and fighter_fatigue < 20:
            recommended_strategy = "2"  # Hard Finish
            strategy_reason = f"Plenty of time ({weeks_until_fight} wks) and fresh. Peak for fight week."
        elif weeks_until_fight <= 5:
            recommended_strategy = "3"  # Fast Start
            strategy_reason = f"Short camp ({weeks_until_fight} wks). Intense early, then recover."
        elif fighter_age >= 34:
            recommended_strategy = "1"  # Steady Build
            strategy_reason = f"Veteran (age {fighter_age}). Steady approach protects the body."
        else:
            recommended_strategy = "1"  # Steady Build
            strategy_reason = "Standard preparation. Consistent gains with low risk."
        
        # === DISPLAY SMART ANALYSIS ===
        if opponent_data:
            print()
            print(f"  {colored('*' * 60, Colors.CYAN)}")
            print(f"  {colored('FIGHT CAMP INTEL', Colors.HIGHLIGHT)}")
            print(f"  {colored('*' * 60, Colors.CYAN)}")
            print()
            
            # Opponent summary
            print(f"  {colored('OPPONENT:', Colors.YELLOW)} {opponent_name} ({opponent_record})")
            print(f"  {colored('Style:', Colors.DIM)} {opponent_style}")
            print()
            
            # Stat comparison
            print(f"  {colored('STAT COMPARISON:', Colors.CYAN)}")
            
            def stat_bar(your_val, opp_val, label):
                diff = your_val - opp_val
                if diff > 10:
                    indicator = colored(f"+{int(diff):>3}", Colors.GREEN)
                elif diff < -10:
                    indicator = colored(f"{int(diff):>3}", Colors.RED)
                else:
                    indicator = colored(f"{int(diff):>+3}", Colors.YELLOW)
                return f"    {label:<12} You: {int(your_val):>2}  vs  {int(opp_val):>2}  [{indicator}]"
            
            print(stat_bar(your_striking, opp_striking, "Striking"))
            print(stat_bar(your_grappling, opp_grappling, "Grappling"))
            print(stat_bar(your_cardio, opp_cardio, "Cardio"))
            print()
            
            # Gameplan preview
            if gameplan_preview:
                print(f"  {colored('SUGGESTED GAMEPLAN:', Colors.CYAN)} {gameplan_preview[0]}")
                print(f"    {colored('^', Colors.DIM)} {gameplan_preview[1]}")
                print()
        
        # === COACH SELECTION ===
        selected_coach = None
        coach_bonus = 1.0
        recommended_coach_idx = None
        
        if COACHES_AVAILABLE and self._coach_system:
            try:
                coaches = self._coach_system.get_camp_coaches(camp_id)
                if coaches:
                    # Find best coach for recommended focus
                    focus_specialty_map = {
                        "1": "Striking",
                        "2": "Jiu-Jitsu", 
                        "3": "Wrestling",
                        "4": "Conditioning",
                        "5": "Strength",
                        "6": None,  # Any coach works for balanced
                    }
                    target_specialty = focus_specialty_map.get(recommended_focus)
                    
                    if target_specialty:
                        for i, coach in enumerate(coaches[:5]):
                            specialty = coach.specialty.value if hasattr(coach.specialty, 'value') else str(coach.specialty)
                            if target_specialty.lower() in specialty.lower():
                                recommended_coach_idx = i + 1
                                break
                    
                    # If no specialty match, recommend highest quality
                    if not recommended_coach_idx and coaches:
                        best_idx = max(range(len(coaches[:5])), key=lambda i: coaches[i].quality)
                        recommended_coach_idx = best_idx + 1
                    
                    print(f"  {colored('SELECT COACH FOR THIS CAMP', Colors.CYAN)}")
                    print()
                    
                    for i, coach in enumerate(coaches[:5], 1):
                        stars = "*" * (coach.quality // 20) + "-" * (5 - coach.quality // 20)
                        specialty = coach.specialty.value if hasattr(coach.specialty, 'value') else str(coach.specialty)
                        bonus_pct = int(coach.quality / 10)
                        
                        rec_tag = ""
                        if i == recommended_coach_idx:
                            rec_tag = colored(" <- REC", Colors.GREEN)
                        
                        print(f"    [{i}] {coach.name}{rec_tag}")
                        print(f"        {specialty} Specialist | {stars} | +{bonus_pct}% bonus")
                    
                    print(f"    [0] No coach (train solo)")
                    print()
                    
                    coach_choice = get_input(f"Select coach [{recommended_coach_idx or 1}]: ").strip()
                    if not coach_choice and recommended_coach_idx:
                        coach_choice = str(recommended_coach_idx)
                    
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
        
        # === TRAINING FOCUS SELECTION ===
        print(f"  {colored('SELECT TRAINING FOCUS', Colors.CYAN)}")
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
            if key == recommended_focus:
                print(f"    [{key}] {colored(name, Colors.GREEN)} - {desc}")
                print(f"        {colored('> REC:', Colors.GREEN)} {focus_reason}")
            else:
                print(f"    [{key}] {name} - {desc}")
        print()
        
        choice = get_input(f"Choose [{recommended_focus}]: ").strip()
        if not choice:
            choice = recommended_focus
        if choice not in ["1", "2", "3", "4", "5", "6"]:
            choice = recommended_focus
        
        try:
            from systems.training import (
                TrainingFocus, TrainingIntensity, CampTemplate,
                TEMPLATE_INFO, estimate_template_fatigue
            )
            
            focus_map = {
                "1": TrainingFocus.STRIKING,
                "2": TrainingFocus.JIUJITSU,
                "3": TrainingFocus.WRESTLING,
                "4": TrainingFocus.CONDITIONING,
                "5": TrainingFocus.STRENGTH_POWER,
                "6": TrainingFocus.BALANCED,
            }
            
            focus = focus_map.get(choice, TrainingFocus.BALANCED)
            
            # === CAMP STRATEGY SELECTION ===
            print()
            print(f"  {colored('SELECT CAMP STRATEGY', Colors.CYAN)}")
            print()
            
            templates = list(CampTemplate)
            
            for i, template in enumerate(templates, 1):
                info = TEMPLATE_INFO[template]
                _, expected_fat, _ = estimate_template_fatigue(template, camp_duration)
                projected = fighter_fatigue + expected_fat
                
                # Color code risk
                risk_colors = {"Low": Colors.GREEN, "Medium": Colors.YELLOW, "HIGH": Colors.RED, "None": Colors.CYAN}
                risk_color = risk_colors.get(info["risk"], Colors.WHITE)
                
                # Arrival condition
                if projected <= 40:
                    arrival = colored("Fresh", Colors.GREEN)
                elif projected <= 60:
                    arrival = colored("Ready", Colors.YELLOW)
                elif projected <= 80:
                    arrival = colored("Tired", Colors.ORANGE)
                else:
                    arrival = colored("Exhausted", Colors.RED)
                
                rec_tag = ""
                if str(i) == recommended_strategy:
                    rec_tag = colored(" <- REC", Colors.GREEN)
                
                print(f"    [{i}] {info['icon']} {info['name']}{rec_tag}")
                print(f"        {info['description']}")
                print(f"        Risk: {colored(info['risk'], risk_color)} + +{expected_fat} fatigue + Arrival: {arrival}")
                if str(i) == recommended_strategy:
                    print(f"        {colored('>', Colors.GREEN)} {strategy_reason}")
            
            print()
            template_choice = get_input(f"Select strategy [{recommended_strategy}]: ").strip()
            if not template_choice:
                template_choice = recommended_strategy
            if template_choice not in ["1", "2", "3", "4", "5"]:
                template_choice = recommended_strategy
            
            selected_template = templates[int(template_choice) - 1]
            
            self._training_system.start_camp(
                fighter_id=fighter.fighter_id,
                camp_id=camp_id,
                focus=focus,
                intensity=TrainingIntensity.MODERATE,
                weeks=camp_duration,
                template=selected_template,
            )
            
            print()
            print(colored("  *" * 25, Colors.WIN))
            print(colored(f"    {camp_duration}-WEEK CAMP STARTED!", Colors.WIN))
            print(colored("  *" * 25, Colors.WIN))
            print()
            print(f"    Opponent: {opponent_name}")
            print(f"    Strategy: {TEMPLATE_INFO[selected_template]['icon']} {TEMPLATE_INFO[selected_template]['name']}")
            print(f"    Focus: {focus.value}")
            if selected_coach:
                print(f"    Coach: {selected_coach.name} (+{int((coach_bonus-1)*100)}% bonus)")
            else:
                print(f"    Coach: Training solo")
            if gameplan_preview:
                print(f"    Gameplan: {gameplan_preview[0]}")
            print()
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
            champ_tag = colored(" [C]", Colors.GOLD) if self._is_division_champion(opp) else ""
            
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
        
        # Use division state for title fight detection
        fighter_rec = self.game_state.fighters.get(fighter.fighter_id)
        opp_rec = self.game_state.fighters.get(opponent.fighter_id) if hasattr(opponent, 'fighter_id') else opponent
        is_title = self._is_division_champion(fighter_rec) or self._is_division_champion(opp_rec)
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
                event_name=f"DFC Fight Night {self.next_event_number}",
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
        
        # Clear tracking for newly accepted challenges
        self._newly_accepted_challenges = []
        
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
        
        # Process maintenance training (for fighters NOT in camp)
        maintenance_results = self._process_maintenance_training()
        week_events.extend(maintenance_results)
        
        # Process player's scheduled fights
        # Store fight results for display
        self._week_fight_results = []
        
        # MERGE PLAYER FIGHTS INTO AI EVENT - Find the AI event name for this week
        # so player fights appear on the same card as AI fights
        if ai_fights_this_week and fights_this_week:
            unified_event_name = ai_fights_this_week[0].get("event_name", "DFC Fight Night")
            # Update player fights to use the same event name
            for fight in self.player_scheduled_fights:
                if fight.get("weeks_until", 0) <= 1:
                    fight["event_name"] = unified_event_name
        
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
        
        # Process popularity decay for inactive fighters (every 4 weeks)
        if self.game_state.week_number % 4 == 0:
            decay_events = self._process_popularity_decay()
            week_events.extend(decay_events)
        
        # Process amateur tournaments
        amateur_events = self._process_amateur_week()
        week_events.extend(amateur_events)
        
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
        
        # Decrement title fight cooldowns per division
        if hasattr(self, '_title_fight_cooldowns'):
            for wc in list(self._title_fight_cooldowns.keys()):
                self._title_fight_cooldowns[wc] = max(0, self._title_fight_cooldowns[wc] - 1)
        
        # Advance game state
        game.advance_week()
        
        # Generate new player offers periodically
        if game.week_number % 2 == 0:
            self._generate_fight_offers()
        
        # Process inbox (clear expired, generate scout reports)
        self._process_inbox_weekly()
        
        # Process division ladder (challenges, freezes, etc.)
        ladder_events = self._process_ladder_week()
        week_events.extend(ladder_events)
        
        # Ensure AI events are scheduled
        self._ensure_ai_events_scheduled()
        
        print(f"Advanced to: Week {game.week_number}")
        print()
        
        self._show_week_summary(week_events)
        
        autosave(game)
        self._save_extended_data("autosave")
        print(colored("(Autosaved)", Colors.DIM))
        
        # === FIGHT CONFIRMATION PROMPT ===
        # When opponents accept player challenges, player must confirm before fight is scheduled
        if hasattr(self, '_pending_fight_confirmations') and self._pending_fight_confirmations:
            print()
            print_divider()
            print()
            print(colored("  === FIGHT OFFERS RECEIVED ===", Colors.GOLD))
            print()
            print(f"  {len(self._pending_fight_confirmations)} opponent(s) accepted your challenge!")
            print()
            
            confirmed_fights = []
            
            for pending in self._pending_fight_confirmations:
                challenge = pending['challenge']
                fight_data = pending['fight_data']
                
                fighter_name = fight_data.get('fighter1_name', 'Your fighter')
                opponent_name = fight_data.get('fighter2_name', 'Opponent')
                weeks_until = fight_data.get('weeks_until', 8)
                weight_class = fight_data.get('weight_class', '')
                is_title = fight_data.get('is_title_fight', False)
                
                # Get opponent info
                opponent_id = fight_data.get('fighter2_id')
                opponent = self.game_state.fighters.get(opponent_id)
                opponent_record = ""
                opponent_rank = ""
                if opponent:
                    opponent_record = f"({opponent.wins}-{opponent.losses})"
                    rank = self._get_fighter_rank_from_weighted(opponent)
                    if rank is not None:
                        opponent_rank = f"#{rank} " if rank > 0 else "[C] "
                
                # Display fight offer
                print(f"  {'-' * 56}")
                title_tag = colored(" [TITLE FIGHT]", Colors.GOLD) if is_title else ""
                print(f"  {colored(fighter_name, Colors.CYAN)} vs {opponent_rank}{opponent_name} {opponent_record}{title_tag}")
                print(f"  Division: {weight_class}")
                print(f"  Fight Week: {game.week_number + weeks_until} ({weeks_until} weeks away)")
                print()
                
                # Check if player already has a fight that week
                existing_fight_that_week = None
                for existing in self.player_scheduled_fights:
                    if existing.get('weeks_until') == weeks_until and existing.get('fighter1_id') == fight_data.get('fighter1_id'):
                        existing_fight_that_week = existing
                        break
                
                if existing_fight_that_week:
                    print(f"  {colored('[!] WARNING:', Colors.RED)} {fighter_name} already has a fight scheduled that week!")
                    print(f"      vs {existing_fight_that_week.get('fighter2_name', 'opponent')}")
                    print()
                
                # Prompt for confirmation
                accept_choice = get_input(f"  Accept this fight? [Y/N]: ").strip().lower()
                
                if accept_choice == "y":
                    # Schedule the fight
                    self.player_scheduled_fights.append(fight_data)
                    confirmed_fights.append(fight_data)
                    print(f"  {colored('[+] Fight booked!', Colors.GREEN)} {fighter_name} vs {opponent_name}")
                    
                    # Add news
                    if hasattr(self, 'news_feed') and self.news_feed is not None:
                        self.news_feed.insert(0, NewsItem(
                            headline=f"{fighter_name} vs {opponent_name} OFFICIAL!",
                            details=f"The fight is signed for Week {game.week_number + weeks_until}",
                            category="matchmaking",
                            week=game.week_number,
                        ))
                else:
                    print(f"  {colored('[-] Fight declined.', Colors.DIM)} You passed on {opponent_name}")
                    
                    # Add news about pulling out
                    if hasattr(self, 'news_feed') and self.news_feed is not None:
                        self.news_feed.insert(0, NewsItem(
                            headline=f"{fighter_name} declines fight with {opponent_name}",
                            details=f"The matchup falls through after {opponent_name} had accepted",
                            category="matchmaking",
                            week=game.week_number,
                        ))
                print()
            
            # Track confirmed fights for training camp prompt
            if confirmed_fights:
                if not hasattr(self, '_newly_accepted_challenges'):
                    self._newly_accepted_challenges = []
                self._newly_accepted_challenges.extend(confirmed_fights)
            
            # Clear pending confirmations
            self._pending_fight_confirmations = []
        
        # Prompt for training camp if fights were confirmed this week
        if hasattr(self, '_newly_accepted_challenges') and self._newly_accepted_challenges:
            print()
            print_divider()
            print()
            print(colored("  === TRAINING CAMP ===", Colors.CYAN))
            print()
            
            for fight_data in self._newly_accepted_challenges:
                fighter_id = fight_data.get('fighter1_id')
                fighter_name = fight_data.get('fighter1_name', 'Your fighter')
                opponent_name = fight_data.get('fighter2_name', 'opponent')
                weeks_until = fight_data.get('weeks_until', 8)
                
                # Check if fighter already in training camp
                fighter = self.fighter_data.get(fighter_id)
                if fighter and hasattr(fighter, 'training_camp') and fighter.training_camp:
                    print(f"  {fighter_name} vs {opponent_name} in {weeks_until} weeks")
                    print(f"  {colored('[Already in training camp]', Colors.DIM)}")
                    print()
                    continue
                
                print(f"  {fighter_name} vs {opponent_name} in {weeks_until} weeks")
                start_camp = get_input(f"  Start training camp for {fighter_name}? [Y/N]: ").strip().lower()
                if start_camp == "y":
                    if fighter:
                        self.start_training_camp_for_fight(fighter, weeks_until)
                    else:
                        print(f"  {colored('Could not find fighter data.', Colors.RED)}")
                print()
            
            # Clear after processing
            self._newly_accepted_challenges = []
        
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
                # Training system names
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
                # FighterFullData names (mapped versions)
                "takedowns": "Wrestling",
                "takedown_defense": "TD Defense",
                "clinch_striking": "Clinch",
                "guard": "Guard",
                "heart": "Heart",
                "striking_defense": "Striking Def",
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
        
        # Calculate sparring bonus for the entire camp (affects all fighters)
        sparring_bonus, sparring_desc = self._calculate_camp_sparring_bonus(player_camp.camp_id)
        
        # Get head coach info for the camp
        head_coach = self._get_head_coach_info(player_camp.camp_id)
        
        # Count fighters in active camps for this camp
        camp_fighter_count = sum(
            1 for fid, fd in self.fighter_data.items() 
            if fd.camp_id == player_camp.camp_id and self._training_system.get_camp(fid)
        )
        
        for fighter_id, full_data in self.fighter_data.items():
            if full_data.camp_id != player_camp.camp_id:
                continue
            
            camp = self._training_system.get_camp(fighter_id)
            if camp and not camp.is_complete:
                # Process week - map new attribute names to training system expectations
                current_attrs = {
                    "boxing": full_data.boxing,
                    "kicks": full_data.kicks,
                    "wrestling": full_data.takedowns,  # Map takedowns -> wrestling
                    "bjj": full_data.submissions,      # Map submissions -> bjj
                    "cardio": full_data.cardio,
                    "strength": full_data.strength,
                    "speed": full_data.speed,
                    "power": full_data.strength,       # Use strength as power
                    "td_defense": full_data.takedown_defense,
                    "top_control": full_data.top_control,
                    "submissions": full_data.submissions,
                    "clinch": full_data.clinch_striking,
                    "guard": full_data.guard,
                    "recovery": full_data.recovery,
                    "heart": full_data.heart,
                    "fight_iq": full_data.fight_iq,
                    "composure": full_data.composure,
                }
                
                # Get coach bonus for this camp
                coach_bonus = self._get_camp_coach_bonus(player_camp.camp_id)
                coach_quality = head_coach.get("quality", 3)
                
                # Get chemistry between head coach and this fighter
                chemistry = self._get_chemistry(
                    head_coach.get("coach_id", ""),
                    fighter_id,
                    full_data.traits,
                    full_data.age
                )
                
                # Get camp tier
                camp_tier_str = self._get_camp_tier()
                camp_tier = None
                if camp_tier_str:
                    try:
                        from systems.training import CampTier
                        tier_map = {
                            "GARAGE": CampTier.GARAGE,
                            "LOCAL": CampTier.LOCAL,
                            "REGIONAL": CampTier.REGIONAL,
                            "NATIONAL": CampTier.NATIONAL,
                            "ELITE": CampTier.ELITE,
                        }
                        camp_tier = tier_map.get(camp_tier_str.upper())
                    except:
                        pass
                
                # Get weeks until fight
                weeks_until_fight = self._get_weeks_until_fight(fighter_id)
                
                try:
                    result = self._training_system.process_training_week(
                        fighter_id=fighter_id,
                        current_attributes=current_attrs,
                        age=full_data.age,
                        camp_tier=camp_tier,
                        coach_quality=coach_quality,
                        fatigue=full_data.fatigue,
                        # New parameters
                        coach_specialty=head_coach.get("specialty"),
                        chemistry=chemistry,
                        coach_traits=head_coach.get("traits", []),
                        sparring_bonus=sparring_bonus,
                        camp_fighter_count=camp_fighter_count,
                        fighter_name=full_data.name,
                        coach_name=head_coach.get("name", "Coach"),
                        fighter_traits=full_data.traits,
                        lost_last_fight=full_data.lost_last_fight,
                        weeks_until_fight=weeks_until_fight,
                        fight_iq=full_data.fight_iq,
                    )
                    
                    # Unpack tuple (gains, event) or just gains if old format
                    if isinstance(result, tuple):
                        gains, training_event = result
                    else:
                        gains = result
                        training_event = None
                    
                    # Update fatigue from camp
                    if hasattr(camp, 'total_fatigue_accumulated'):
                        full_data.fatigue = camp.total_fatigue_accumulated
                    
                    # Apply coach multiplier to gains
                    if gains and coach_bonus != 1.0:
                        gains = {k: max(1, int(v * coach_bonus)) for k, v in gains.items()}
                    
                    # Apply sparring bonus to gains
                    if gains and sparring_bonus > 0:
                        gains = {k: max(v, int(v * (1 + sparring_bonus))) for k, v in gains.items()}
                    
                    # Apply chemistry bonus/penalty
                    if gains and chemistry != 50:
                        if chemistry >= 70:
                            # Good chemistry: 1-3% bonus
                            chem_bonus = 1.0 + ((chemistry - 50) / 100) * 0.06
                            gains = {k: max(v, int(v * chem_bonus)) for k, v in gains.items()}
                        elif chemistry < 40:
                            # Bad chemistry: slight penalty
                            chem_penalty = 1.0 - ((50 - chemistry) / 100) * 0.03
                            gains = {k: max(1, int(v * chem_penalty)) for k, v in gains.items()}
                    
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
                        
                        # Map training system attribute names to FighterFullData names
                        # Training system uses: wrestling, bjj, clinch, power
                        # FighterFullData uses: takedowns, submissions, clinch_striking, strength
                        attr_to_fighter_map = {
                            "wrestling": "takedowns",
                            "bjj": "submissions", 
                            "clinch": "clinch_striking",
                            "power": "strength",
                            "td_defense": "takedown_defense",
                        }
                        
                        # Apply gains to fighter (with facility cap enforcement)
                        for attr, gain in gains.items():
                            # Map attribute name to FighterFullData attribute
                            mapped_attr = attr_to_fighter_map.get(attr, attr)
                            
                            if hasattr(full_data, mapped_attr):
                                old_val = getattr(full_data, mapped_attr)
                                
                                # Apply facility cap if available
                                if FACILITIES_AVAILABLE and camp_tier:
                                    new_val, actual_gain, was_capped = apply_facility_cap(
                                        old_val, gain, camp_tier, mapped_attr
                                    )
                                    if was_capped and actual_gain < gain:
                                        capped_attrs.append(mapped_attr)
                                    setattr(full_data, mapped_attr, new_val)
                                else:
                                    setattr(full_data, mapped_attr, min(100, old_val + gain))
                        
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
                        
                        # Get current week's intensity from schedule
                        current_intensity = None
                        intensity_name = "Moderate"
                        if hasattr(camp, 'get_current_intensity'):
                            # Use the schedule-based intensity (week before completion)
                            prev_week = max(0, camp.weeks_completed - 1)
                            if hasattr(camp, 'schedule') and camp.schedule and prev_week < len(camp.schedule):
                                current_intensity = camp.schedule[prev_week]
                                intensity_name = current_intensity.name.title()
                            elif hasattr(camp, 'intensity'):
                                current_intensity = camp.intensity
                                intensity_name = current_intensity.name.title()
                        
                        # Get template name if available
                        template_name = None
                        if hasattr(camp, 'template') and camp.template:
                            template_name = camp.template.value
                        
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
                            'fighter_id': fighter_id,  # Add ID for saving gains
                            'week': week_num,
                            'total_weeks': total_weeks,
                            'focus': focus_name,
                            'intensity': intensity_name,
                            'template': template_name,
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
                        
                        # SAVE LAST CAMP GAINS when camp completes
                        if camp.is_complete and camp.attribute_gains:
                            full_data.last_camp_gains = camp.attribute_gains.copy()
                            full_data.last_camp_total = sum(camp.attribute_gains.values())
                            full_data.last_camp_week = self.game_state.week_number if self.game_state else 0
                    
                except Exception:
                    pass
        
        # Format output
        if training_fighters:
            events.append(colored("TRAINING PROGRESS", Colors.CYAN))
            
            for tf in training_fighters:
                # Intensity color coding
                intensity_colors = {
                    "Rest": Colors.CYAN,
                    "Light": Colors.GREEN,
                    "Moderate": Colors.YELLOW,
                    "Intense": Colors.ORANGE,
                    "Extreme": Colors.RED,
                }
                intensity = tf.get('intensity', 'Moderate')
                intensity_color = intensity_colors.get(intensity, Colors.WHITE)
                
                # Fighter header line with intensity
                header = f"  {tf['name']} (Week {tf['week']}/{tf['total_weeks']} | {colored(intensity, intensity_color)} | {tf['focus']}){tf['trait_note']}"
                events.append(header)
                
                # Training event (breakthrough, setback, etc.)
                training_event = tf.get('training_event')
                has_special_event = False
                if training_event:
                    event_type = getattr(training_event, 'event_type', None)
                    headline = getattr(training_event, 'headline', '')
                    
                    # Color based on event type
                    if event_type and 'breakthrough' in str(event_type).lower():
                        events.append(f"    {colored('* BREAKTHROUGH: ' + headline, Colors.GOLD)}")
                        has_special_event = True
                        # Add to news feed
                        self.news_feed.insert(0, NewsItem(
                            headline=f"{tf['name']} has training breakthrough!",
                            category="training",
                            week=self.game_state.week_number if self.game_state else 0,
                        ))
                    elif event_type and 'setback' in str(event_type).lower():
                        events.append(f"    {colored('[!] SETBACK: ' + headline, Colors.RED)}")
                        has_special_event = True
                    elif event_type and 'injury' in str(event_type).lower():
                        events.append(f"    {colored('[+] INJURY: ' + headline, Colors.RED)}")
                        has_special_event = True
                    elif headline:
                        events.append(f"    {colored('- ' + headline, Colors.YELLOW)}")
                        has_special_event = True
                
                # Tweak #5: Training camp flavor text (when no special event)
                if not has_special_event:
                    fighter_name = tf['name'].split()[-1]  # Last name
                    coach_name = head_coach.get("name", "Coach").split()[-1] if head_coach else "Coach"
                    focus = tf.get('focus', 'Balanced')
                    week_num = tf.get('week', 1)
                    total_weeks = tf.get('total_weeks', 8)
                    
                    # Different flavor based on camp phase
                    if week_num == 1:
                        flavor_pool = [
                            f"First day of camp - {fighter_name} setting the tone early",
                            f"Coach {coach_name} laying out the game plan",
                            f"Camp begins with focus on {focus.lower()}",
                            f"{fighter_name} looking motivated to start camp",
                        ]
                    elif week_num == total_weeks:
                        flavor_pool = [
                            f"Final week - {fighter_name} sharpening up",
                            f"Light work, staying sharp for fight night",
                            f"Coach {coach_name} confident heading into the fight",
                            f"{fighter_name} making weight, mentally focused",
                        ]
                    elif week_num >= total_weeks - 1:
                        flavor_pool = [
                            f"Tapering down - keeping {fighter_name} fresh",
                            f"Final sparring sessions this week",
                            f"Coach {coach_name}: 'Looking sharp, just fine-tuning now'",
                            f"{fighter_name} visualizing victory",
                        ]
                    else:
                        # Mid-camp flavor based on focus
                        if focus == "Striking":
                            flavor_pool = [
                                f"{fighter_name} working combinations on the pads",
                                f"Heavy bag work paying dividends",
                                f"Coach {coach_name} drilling head movement",
                                f"Crisp hands in sparring today",
                                f"{fighter_name}'s timing looking sharp",
                            ]
                        elif focus == "Wrestling":
                            flavor_pool = [
                                f"Grinding out wrestling drills",
                                f"{fighter_name} dominating in scrambles",
                                f"Takedown defense looking solid",
                                f"Coach {coach_name} pushing the pace on the mat",
                                f"Chain wrestling coming together",
                            ]
                        elif focus == "Jiu-Jitsu":
                            flavor_pool = [
                                f"{fighter_name} flowing through positions",
                                f"Submission setups getting slick",
                                f"Guard work looking dangerous",
                                f"Coach {coach_name} introducing new sequences",
                                f"Triangle attempts in every roll",
                            ]
                        elif focus == "Conditioning":
                            flavor_pool = [
                                f"Brutal cardio session this morning",
                                f"{fighter_name} pushing through the wall",
                                f"Recovery times improving noticeably",
                                f"Coach {coach_name}: 'Cardio wins fights'",
                                f"5 AM runs becoming routine",
                            ]
                        elif focus == "Strength & Power":
                            flavor_pool = [
                                f"Heavy lifting day - {fighter_name} putting up numbers",
                                f"Power output increasing week over week",
                                f"Explosive drills paying off",
                                f"Coach {coach_name} monitoring the gains",
                                f"{fighter_name} feeling stronger than ever",
                            ]
                        else:  # Balanced
                            flavor_pool = [
                                f"Solid all-around session today",
                                f"Mixing it up - striking to grappling transitions",
                                f"Coach {coach_name} keeping {fighter_name} well-rounded",
                                f"Good energy in the gym today",
                                f"{fighter_name} putting in the work",
                                f"Another productive day in camp",
                            ]
                    
                    # 60% chance to show flavor (don't spam every week)
                    if random.random() < 0.60:
                        flavor = random.choice(flavor_pool)
                        events.append(f"    {colored(f'> {flavor}', Colors.DIM)}")
                
                # This week's gains - include fighter name for clarity
                weekly_str = format_gains(tf['weekly_gains'])
                fighter_short = tf['name'].split()[-1]  # Last name
                events.append(f"    {fighter_short}: {colored(weekly_str, Colors.GREEN)}")
                
                # Overall increase notification
                if tf.get('overall_increased'):
                    old_ovr = tf.get('old_overall', 0)
                    new_ovr = tf.get('new_overall', 0)
                    events.append(f"    {colored(f'^ OVERALL: {old_ovr} ^ {new_ovr}', Colors.GOLD)}")
                
                # Camp total (only show if more than one week in)
                if tf['week'] > 1 and tf['camp_total']:
                    total_str = format_gains(tf['camp_total'])
                    events.append(f"    Camp total: {total_str}")
                
                # Camp complete notification
                if tf['is_complete']:
                    events.append(colored(f"    [OK] Camp complete! Ready to fight.", Colors.GOLD))
                
                events.append("")  # Blank line between fighters
        
        return events
    
    def _process_maintenance_training(self) -> List[str]:
        """Process maintenance training for fighters NOT in active camps.
        
        Coaches work with available fighters on ongoing skill development.
        """
        events = []
        
        if not self._maintenance_system:
            return events
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return events
        
        # Get fighters not in active training camps
        camp_fighters = [f for f in self.game_state.fighters.values()
                        if f.camp_id == player_camp.camp_id and f.is_active]
        
        # Filter out those in active training camps
        available_fighters = []
        for fighter in camp_fighters:
            in_camp = False
            if self._training_system:
                camp = self._training_system.get_camp(fighter.fighter_id)
                if camp and not camp.is_complete:
                    in_camp = True
            if not in_camp:
                available_fighters.append(fighter)
                # Reset maintenance gains for this week
                full_data = self.fighter_data.get(fighter.fighter_id)
                if full_data:
                    full_data.maintenance_gains = {}
        
        if not available_fighters:
            return events
        
        # Get coaches
        coaches = []
        if COACHES_AVAILABLE and self._coach_system:
            try:
                coaches = self._coach_system.get_camp_coaches(player_camp.camp_id)
            except:
                pass
        
        if not coaches:
            return events
        
        current_week = self.game_state.week_number if self.game_state else 0
        maintenance_boosts = []
        
        # Process maintenance training
        try:
            # Build fighter data list for maintenance system
            fighter_list = []
            camp_assignments = {}  # fighter_id -> camp_id
            
            for fighter in available_fighters:
                full_data = self.fighter_data.get(fighter.fighter_id)
                if full_data:
                    fighter_list.append({
                        "id": fighter.fighter_id,
                        "fighter_id": fighter.fighter_id,
                        "name": full_data.name,
                        "age": full_data.age,
                        "attributes": {
                            "boxing": full_data.boxing,
                            "kicks": full_data.kicks,
                            "wrestling": full_data.takedowns,
                            "bjj": full_data.submissions,
                            "cardio": full_data.cardio,
                            "strength": full_data.strength,
                            "speed": full_data.speed,
                            "chin": full_data.chin,
                            "recovery": full_data.recovery,
                            "td_defense": full_data.takedown_defense,
                            "top_control": full_data.top_control,
                            "clinch": full_data.clinch_striking,
                            "guard": full_data.guard,
                            "fight_iq": full_data.fight_iq,
                            "composure": full_data.composure,
                            "heart": full_data.heart,
                        }
                    })
                    camp_assignments[fighter.fighter_id] = player_camp.camp_id
            
            # Build coach data list
            coach_list = []
            for coach in coaches:
                coach_list.append({
                    "coach_id": coach.coach_id,
                    "name": coach.name,
                    "camp_id": player_camp.camp_id,
                    "striking": getattr(coach, 'striking', 50),
                    "wrestling": getattr(coach, 'wrestling', 50),
                    "jiu_jitsu": getattr(coach, 'jiu_jitsu', 50),
                    "conditioning": getattr(coach, 'conditioning', 50),
                    "strength": getattr(coach, 'strength', 50),
                    "traits": getattr(coach, 'traits', []),
                })
            
            # Map camp to coaches
            camp_coaches = {player_camp.camp_id: coach_list}
            
            # Process week through maintenance system
            boosts, decays, warnings = self._maintenance_system.process_week(
                fighters=fighter_list,
                coaches=coach_list,
                camp_assignments=camp_assignments,
                camp_coaches=camp_coaches,
                current_week=current_week,
                fighters_in_camp=set(),  # Already filtered out
            )
            
            # Apply boosts to fighter data
            attr_map = {
                "wrestling": "takedowns", "bjj": "submissions", 
                "clinch": "clinch_striking", "td_defense": "takedown_defense",
            }
            
            for boost in boosts:
                full_data = self.fighter_data.get(boost.fighter_id)
                if full_data:
                    attr = attr_map.get(boost.stat, boost.stat)
                    if hasattr(full_data, attr):
                        old_val = getattr(full_data, attr)
                        new_val = min(100, old_val + boost.amount)
                        setattr(full_data, attr, new_val)
                        
                        # Track maintenance gains
                        if not hasattr(full_data, 'maintenance_gains') or not full_data.maintenance_gains:
                            full_data.maintenance_gains = {}
                        if attr not in full_data.maintenance_gains:
                            full_data.maintenance_gains[attr] = 0
                        full_data.maintenance_gains[attr] += boost.amount
                        full_data.maintenance_week = current_week
                        
                        maintenance_boosts.append(boost)
            
            # Apply decays
            for decay in decays:
                full_data = self.fighter_data.get(decay.fighter_id)
                if full_data:
                    attr = attr_map.get(decay.stat, decay.stat)
                    if hasattr(full_data, attr):
                        old_val = getattr(full_data, attr)
                        new_val = max(30, old_val - decay.amount)  # Floor at 30
                        setattr(full_data, attr, new_val)
            
        except Exception:
            pass
        
        # Format output
        if maintenance_boosts:
            events.append(colored("MAINTENANCE TRAINING", Colors.DIM))
            
            # Group boosts by fighter
            fighter_boosts: Dict[str, List] = {}
            for boost in maintenance_boosts:
                if boost.fighter_id not in fighter_boosts:
                    fighter_boosts[boost.fighter_id] = []
                fighter_boosts[boost.fighter_id].append(boost)
            
            for fighter_id, boosts in fighter_boosts.items():
                full_data = self.fighter_data.get(fighter_id)
                if not full_data:
                    continue
                
                # Format gains
                gains_parts = []
                coach_name = boosts[0].coach_name if boosts else "Coach"
                for boost in boosts:
                    attr_abbrev = {
                        "boxing": "BOX", "kicks": "KICK", "wrestling": "TD",
                        "bjj": "SUB", "cardio": "CARD", "strength": "STR",
                        "speed": "SPD", "chin": "CHIN", "recovery": "REC",
                        "td_defense": "TDD", "top_control": "TOP",
                        "clinch": "CLIN", "guard": "GRD", "fight_iq": "IQ",
                        "composure": "COMP", "heart": "HRT",
                    }.get(boost.stat, boost.stat[:3].upper())
                    gains_parts.append(f"+{boost.amount} {attr_abbrev}")
                
                gains_str = ", ".join(gains_parts)
                events.append(f"  {full_data.name}: {colored(gains_str, Colors.GREEN)} (w/ {coach_name})")
            
            events.append("")
        
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
            # Get actual rank from fighter record
            fighter_record = self.game_state.fighters.get(f.fighter_id)
            rank = self._get_fighter_division_rank(fighter_record) if fighter_record else None
            rank_str = f"#{rank}" if rank else "Unranked"
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
            # Play auto-scroll commentary first (live fight experience)
            self._auto_scroll_fight_commentary(fight_result)
            # Then show the result screen
            self._show_player_fight_result(fight_result)
        
        return events
    
    def _auto_scroll_fight_commentary(self, result: FightResult) -> None:
        """Auto-scroll play-by-play commentary with variable timing for dramatic effect.
        
        Creates a 'watching the fight unfold' experience with:
        - Normal lines: 0.3s delay
        - Big moments (knockdowns, rocks): 0.6s delay
        - Round endings: 1.5s pause
        - Finish sequences: dramatic buildup
        - Press 's' to skip to result
        """
        commentary = result.full_commentary
        if not commentary:
            return
        
        # Convert to list if string
        if isinstance(commentary, list):
            lines = commentary
        else:
            lines = commentary.split('\n')
        
        if not lines:
            return
        
        clear_screen()
        print_header("LIVE FIGHT")
        print()
        print(f"  {colored(result.fighter1_name, Colors.CYAN)} vs {colored(result.fighter2_name, Colors.CYAN)}")
        print()
        print(f"  {colored('(Press s + Enter to skip to result)', Colors.DIM)}")
        print()
        print_divider()
        print()
        
        # Timing constants
        NORMAL_DELAY = 0.35
        BIG_MOMENT_DELAY = 0.6
        ROUND_END_DELAY = 1.5
        FINISH_BUILDUP_DELAY = 0.8
        
        # Patterns for timing adjustments
        big_moment_patterns = [
            "rocks", "rocked", "hurt", "wobble", "stagger",
            "knockdown", "knocked down", "drops", "dropped",
            "huge", "massive", "devastating", "thunderous",
            "locked in", "tight", "cranking", "sinking",
            "tap", "submission", "finish"
        ]
        
        round_end_patterns = [
            "round 1 in the books", "round 2 in the books", "round 3 in the books",
            "round 4 in the books", "round 5 in the books",
            "end round", "horn sounds", "saved by the bell"
        ]
        
        finish_patterns = [
            "it's all over", "referee stops", "that's it",
            "taps out", "the fight is over", "we have a winner"
        ]
        
        round_start_patterns = [
            "round 1!", "round 2!", "round 3!", "round 4!", "round 5!",
            "here we go"
        ]
        
        skipped = False
        current_round = 1
        
        for i, line in enumerate(lines):
            if skipped:
                break
            
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            line_lower = line_stripped.lower()
            
            # Determine delay based on content
            delay = NORMAL_DELAY
            
            # Check for round start - add header
            if any(p in line_lower for p in round_start_patterns):
                for r in range(1, 6):
                    if f"round {r}" in line_lower:
                        current_round = r
                        print()
                        print(f"  {colored(f'=== ROUND {r} ===', Colors.GOLD)}")
                        print()
                        delay = 0.5
                        break
            
            # Check for big moments
            if any(p in line_lower for p in big_moment_patterns):
                delay = BIG_MOMENT_DELAY
                # Color big moments
                print(f"  {colored(line_stripped, Colors.YELLOW)}")
            # Check for finish
            elif any(p in line_lower for p in finish_patterns):
                delay = FINISH_BUILDUP_DELAY
                print(f"  {colored(line_stripped, Colors.RED)}")
            # Check for round end
            elif any(p in line_lower for p in round_end_patterns):
                print(f"  {line_stripped}")
                print()
                print(f"  {colored('-' * 40, Colors.DIM)}")
                delay = ROUND_END_DELAY
            else:
                # Normal line
                print(f"  {line_stripped}")
            
            # Flush output
            sys.stdout.flush()
            
            # Check for skip input (non-blocking)
            # Use select to check if there's input available during delay
            try:
                # select waits up to 'delay' seconds for input
                # If input comes, we check for skip; otherwise we've waited the delay
                readable, _, _ = select.select([sys.stdin], [], [], delay)
                if readable:
                    user_input = sys.stdin.readline().strip().lower()
                    if user_input == 's':
                        skipped = True
                        print()
                        print(f"  {colored('>> Skipping to result...', Colors.DIM)}")
                        time.sleep(0.5)
                # If no input, select already waited 'delay' seconds
            except:
                # Fallback if select doesn't work (Windows, etc.)
                time.sleep(delay)
        
        # Brief pause before showing result
        if not skipped:
            print()
            print(f"  {colored('Fight complete. Loading result...', Colors.DIM)}")
            time.sleep(1.0)
    
    def _show_player_fight_result(self, result: FightResult) -> None:
        """Show player fight result with celebration messages and commentary option."""
        clear_screen()
        
        # =================================================================
        # DOPAMINE: BIG WIN CELEBRATION HEADERS
        # =================================================================
        is_title = getattr(result, 'is_title_fight', False)
        your_fighter_won = False
        your_fighter_id = None
        
        # Check if your fighter won
        player_camp = self.game_state.get_player_camp()
        if player_camp:
            winner = self.game_state.fighters.get(result.winner_id) if hasattr(result, 'winner_id') else None
            loser = self.game_state.fighters.get(result.loser_id) if hasattr(result, 'loser_id') else None
            if winner and getattr(winner, 'camp_id', None) == player_camp.camp_id:
                your_fighter_won = True
                your_fighter_id = result.winner_id
            elif loser and getattr(loser, 'camp_id', None) == player_camp.camp_id:
                your_fighter_id = result.loser_id
        
        # Determine celebration level
        if your_fighter_won:
            method_upper = result.method.upper() if result.method else ""
            finish_round = result.round_finished
            rounds_scheduled = getattr(result, 'rounds_scheduled', 3)
            
            # Check for upset victory (beating higher ranked opponent)
            # Use integer ranks for comparison
            winner_rank = self._get_fighter_rank_from_weighted(winner) if winner else None
            loser_rank = self._get_fighter_rank_from_weighted(loser) if loser else None
            # Upset if winner unranked/lower and beat someone ranked at least 3 spots higher
            is_upset = (loser_rank is not None and 
                       (winner_rank is None or winner_rank > loser_rank + 3))
            
            # Priority-based celebration headers
            if is_title and "KO" in method_upper:
                print(f"  {colored('*' * 60, Colors.GOLD)}")
                print(f"  {colored('*** CHAMPIONSHIP KO! ***', Colors.GOLD):^66}")
                print(f"  {colored('*' * 60, Colors.GOLD)}")
            elif is_title and "SUB" in method_upper:
                print(f"  {colored('*' * 60, Colors.GOLD)}")
                print(f"  {colored('*** CHAMPIONSHIP SUBMISSION! ***', Colors.GOLD):^66}")
                print(f"  {colored('*' * 60, Colors.GOLD)}")
            elif is_title:
                print(f"  {colored('*' * 60, Colors.GOLD)}")
                print(f"  {colored('*** TITLE FIGHT VICTORY! ***', Colors.GOLD):^66}")
                print(f"  {colored('*' * 60, Colors.GOLD)}")
            elif finish_round == 1 and ("KO" in method_upper or "TKO" in method_upper):
                print(f"  {colored('!' * 60, Colors.RED)}")
                print(f"  {colored('[!] FIRST ROUND KO! [!]', Colors.RED):^66}")
                print(f"  {colored('!' * 60, Colors.RED)}")
            elif finish_round == 1 and "SUB" in method_upper:
                print(f"  {colored('!' * 60, Colors.MAGENTA)}")
                print(f"  {colored('[!] FIRST ROUND SUBMISSION! [!]', Colors.MAGENTA):^66}")
                print(f"  {colored('!' * 60, Colors.MAGENTA)}")
            elif finish_round == 2 and ("KO" in method_upper or "TKO" in method_upper or "SUB" in method_upper):
                print(f"  {colored('~' * 60, Colors.ORANGE)}")
                print(f"  {colored('[i] SECOND ROUND FINISH! [i]', Colors.ORANGE):^66}")
                print(f"  {colored('~' * 60, Colors.ORANGE)}")
            elif rounds_scheduled >= 5 and finish_round >= 4 and ("KO" in method_upper or "TKO" in method_upper or "SUB" in method_upper):
                print(f"  {colored('~' * 60, Colors.CYAN)}")
                print(f"  {colored('[T] CHAMPIONSHIP ROUND FINISH! [T]', Colors.CYAN):^66}")
                print(f"  {colored('~' * 60, Colors.CYAN)}")
            elif is_upset:
                print(f"  {colored('!' * 60, Colors.YELLOW)}")
                print(f"  {colored('[!] UPSET VICTORY! [!]', Colors.YELLOW):^66}")
                print(f"  {colored('!' * 60, Colors.YELLOW)}")
            elif "KO" in method_upper or "TKO" in method_upper:
                print_header(colored("[!] KNOCKOUT VICTORY! [!]", Colors.RED))
            elif "SUB" in method_upper:
                print_header(colored("[!] SUBMISSION VICTORY! [!]", Colors.MAGENTA))
            else:
                print_header("[T] VICTORY!")
        else:
            # Your fighter lost
            if your_fighter_id:
                method_upper = result.method.upper() if result.method else ""
                if "KO" in method_upper or "TKO" in method_upper:
                    print(f"  {colored('-' * 60, Colors.RED)}")
                    print(f"  {colored('KNOCKOUT LOSS', Colors.RED):^66}")
                    print(f"  {colored('-' * 60, Colors.RED)}")
                elif "SUB" in method_upper:
                    print(f"  {colored('-' * 60, Colors.MAGENTA)}")
                    print(f"  {colored('SUBMISSION LOSS', Colors.MAGENTA):^66}")
                    print(f"  {colored('-' * 60, Colors.MAGENTA)}")
                else:
                    print_header("DEFEAT")
            else:
                print_header("FIGHT RESULT")
        
        print()
        
        # Show basic result
        print(f"  {result.fighter1_name} vs {result.fighter2_name}")
        print()
        
        if result.method == "DRAW":
            print(f"  Result: {colored('DRAW', Colors.NEUTRAL)}")
        else:
            # Winner display
            winner_display = colored(result.winner_name, Colors.WIN)
            if your_fighter_won:
                winner_display = colored(f"[T] {result.winner_name} [T]", Colors.GOLD)
            
            print(f"  Winner: {winner_display}")
            
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
        
        # =================================================================
        # DOPAMINE: MILESTONE ALERTS
        # =================================================================
        if your_fighter_won and hasattr(result, 'winner_id'):
            winner_data = self.fighter_data.get(result.winner_id)
            winner_fighter = self.game_state.fighters.get(result.winner_id)
            
            milestones = []
            
            if winner_data and winner_fighter:
                method_upper = result.method.upper() if result.method else ""
                
                # ===== FIRST-TIME ACHIEVEMENTS =====
                # First pro win
                if winner_fighter.wins == 1:
                    milestones.append(colored("[*] FIRST PRO WIN!", Colors.GREEN))
                
                # First title (check if this was a title fight and they became champion)
                if is_title and self._is_division_champion(winner_fighter):
                    if winner_data.title_defenses == 0:
                        milestones.append(colored("[T] FIRST CHAMPIONSHIP! NEW CHAMPION!", Colors.GOLD))
                
                # First KO
                if winner_data.ko_wins == 1 and ("KO" in method_upper or "TKO" in method_upper):
                    milestones.append(colored("[!] FIRST KNOCKOUT WIN!", Colors.RED))
                
                # First submission
                if winner_data.sub_wins == 1 and "SUB" in method_upper:
                    milestones.append(colored("[!] FIRST SUBMISSION WIN!", Colors.MAGENTA))
                
                # ===== WIN STREAK MILESTONES =====
                if winner_data.win_streak == 3:
                    milestones.append(colored("[!] 3-FIGHT WIN STREAK!", Colors.ORANGE))
                elif winner_data.win_streak == 5:
                    milestones.append(colored("[!][!] 5-FIGHT WIN STREAK!", Colors.ORANGE))
                elif winner_data.win_streak == 7:
                    milestones.append(colored("[!][!][!] 7-FIGHT WIN STREAK!", Colors.RED))
                elif winner_data.win_streak == 10:
                    milestones.append(colored("[!][!][!][!] 10-FIGHT WIN STREAK! UNSTOPPABLE!", Colors.GOLD))
                
                # ===== PERFECT RECORD MILESTONES =====
                if winner_fighter.losses == 0:
                    if winner_fighter.wins == 5:
                        milestones.append(colored("[=] PERFECT 5-0 RECORD!", Colors.CYAN))
                    elif winner_fighter.wins == 10:
                        milestones.append(colored("[=] PERFECT 10-0 RECORD! FLAWLESS!", Colors.GOLD))
                
                # ===== CAREER WINS MILESTONES =====
                if winner_fighter.wins == 10:
                    milestones.append(colored("[=] 10 CAREER WINS!", Colors.CYAN))
                elif winner_fighter.wins == 15:
                    milestones.append(colored("[=] 15 CAREER WINS!", Colors.CYAN))
                elif winner_fighter.wins == 20:
                    milestones.append(colored("[=] 20 CAREER WINS! VETERAN STATUS!", Colors.GOLD))
                elif winner_fighter.wins == 25:
                    milestones.append(colored("[=] 25 CAREER WINS! LEGEND!", Colors.GOLD))
                
                # ===== KO MILESTONES =====
                if winner_data.ko_wins == 5:
                    milestones.append(colored("[!] 5 KNOCKOUT WINS!", Colors.RED))
                elif winner_data.ko_wins == 10:
                    milestones.append(colored("[!][!] 10 KNOCKOUT WINS! KNOCKOUT ARTIST!", Colors.RED))
                
                # ===== SUBMISSION MILESTONES =====
                if winner_data.sub_wins == 5:
                    milestones.append(colored("[!] 5 SUBMISSION WINS!", Colors.MAGENTA))
                elif winner_data.sub_wins == 10:
                    milestones.append(colored("[!][!] 10 SUBMISSION WINS! SUBMISSION ACE!", Colors.MAGENTA))
                
                # ===== TITLE DEFENSE MILESTONES =====
                if is_title and winner_data.title_defenses > 0:
                    if winner_data.title_defenses == 1:
                        milestones.append(colored("[*] FIRST TITLE DEFENSE!", Colors.GOLD))
                    elif winner_data.title_defenses == 3:
                        milestones.append(colored("[*][*] 3 TITLE DEFENSES! DOMINANT CHAMPION!", Colors.GOLD))
                    elif winner_data.title_defenses == 5:
                        milestones.append(colored("[*][*][*] 5 TITLE DEFENSES! LEGENDARY REIGN!", Colors.GOLD))
                    elif winner_data.title_defenses == 10:
                        milestones.append(colored("[T] 10 TITLE DEFENSES! ALL-TIME GREAT!", Colors.GOLD))
                
                # ===== COMEBACK MILESTONES =====
                # Check if they were on a losing streak before this win
                if hasattr(winner_data, '_prev_lose_streak') and winner_data._prev_lose_streak >= 2:
                    milestones.append(colored("[P] COMEBACK WIN! BACK ON TRACK!", Colors.GREEN))
                
                # ===== RANKED WINS =====
                loser_fighter = self.game_state.fighters.get(result.loser_id)
                if loser_fighter:
                    loser_rank = self._get_fighter_rank_from_weighted(loser_fighter)
                    if loser_rank is not None:
                        if loser_rank == 1:
                            milestones.append(colored("[*] DEFEATED #1 CONTENDER!", Colors.YELLOW))
                        elif loser_rank <= 5:
                            milestones.append(colored(f"[*] TOP 5 WIN! (Defeated #{loser_rank})", Colors.YELLOW))
            
            if milestones:
                for m in milestones:
                    print(f"  {m}")
                print()
        
        # =================================================================
        # LOSS ALERTS (for drama and narrative)
        # =================================================================
        if not your_fighter_won and your_fighter_id:
            loser_data = self.fighter_data.get(your_fighter_id)
            loser_fighter = self.game_state.fighters.get(your_fighter_id)
            
            loss_alerts = []
            
            if loser_data and loser_fighter:
                method_upper = result.method.upper() if result.method else ""
                
                # First loss
                if loser_fighter.losses == 1 and loser_fighter.wins > 0:
                    loss_alerts.append(colored("[!] FIRST CAREER LOSS - The undefeated run ends.", Colors.DIM))
                
                # Losing streak alerts
                if loser_data.lose_streak == 2:
                    loss_alerts.append(colored("[-] 2-FIGHT LOSING STREAK - Time to regroup.", Colors.ORANGE))
                elif loser_data.lose_streak == 3:
                    loss_alerts.append(colored("[-][-] 3-FIGHT LOSING STREAK - Career crossroads.", Colors.RED))
                elif loser_data.lose_streak >= 4:
                    loss_alerts.append(colored("[-][-][-] STRUGGLING - Consider a change in approach.", Colors.RED))
                
                # Lost title
                if is_title:
                    loss_alerts.append(colored("[T][X] LOST THE CHAMPIONSHIP - The reign is over.", Colors.RED))
                
                # KO/TKO loss
                if "KO" in method_upper or "TKO" in method_upper:
                    if loser_data.ko_losses >= 3:
                        loss_alerts.append(colored("[!] 3+ KO LOSSES - Chin may be compromised.", Colors.YELLOW))
            
            if loss_alerts:
                for alert in loss_alerts:
                    print(f"  {alert}")
                print()
        
        # Show fight summary
        if result.fight_summary:
            print(f"  {result.fight_summary}")
            print()
        
        # Show key moments (only if not already in fight summary)
        if result.key_moments and "KEY MOMENTS" not in (result.fight_summary or ""):
            print(f"  {colored('KEY MOMENTS:', Colors.CYAN)}")
            for moment in result.key_moments[:3]:
                if moment:  # Skip empty moments
                    print(f"    * {moment}")
            print()
        
        # Stats summary (only if not already shown in fight_summary)
        if "FIGHT STATISTICS" not in (result.fight_summary or ""):
            print(f"  {colored('STATS:', Colors.BOLD)}")
            print(f"    {result.fighter1_name}: {result.fighter1_strikes} strikes, {result.fighter1_takedowns} TD")
            print(f"    {result.fighter2_name}: {result.fighter2_strikes} strikes, {result.fighter2_takedowns} TD")
            print()
        
        # Options menu
        options = []
        if result.has_full_commentary and result.full_commentary:
            options.append(("[C]", "View Full Fight Commentary"))
        
        # Post-fight interview for player's fighter
        player_camp = self.game_state.get_player_camp()
        player_camp_id = player_camp.camp_id if player_camp else None
        player_fighter_won = False
        player_fighter_lost = False
        player_fighter_id = None
        
        # Check if player's fighter was in this fight
        f1 = self.game_state.fighters.get(result.fighter1_id)
        f2 = self.game_state.fighters.get(result.fighter2_id)
        if f1 and getattr(f1, 'camp_id', None) == player_camp_id:
            player_fighter_id = result.fighter1_id
            player_fighter_won = result.winner_id == result.fighter1_id
            player_fighter_lost = not player_fighter_won
        elif f2 and getattr(f2, 'camp_id', None) == player_camp_id:
            player_fighter_id = result.fighter2_id
            player_fighter_won = result.winner_id == result.fighter2_id
            player_fighter_lost = not player_fighter_won
        
        if player_fighter_id and INTERVIEW_AVAILABLE and self._interview_manager:
            options.append(("[I]", "Post-Fight Interview"))
        
        options.append(("[Enter]", "Continue"))
        
        # Display options
        for key, desc in options:
            print(f"  {colored(key, Colors.CYAN)} {desc}")
        print()
        
        choice = get_input("> ").lower()
        
        if choice == 'c' and result.has_full_commentary:
            self._show_full_fight_commentary(result)
        elif choice == 'i' and player_fighter_id and INTERVIEW_AVAILABLE:
            self._show_post_fight_interview(result, player_fighter_id, player_fighter_won)
        
        # Show social media reactions after interview/commentary
        if player_fighter_id:
            self._show_social_media_reactions(result, player_fighter_id, player_fighter_won)
    
    def _show_post_fight_interview(self, result: FightResult, fighter_id: str, won: bool) -> None:
        """Show post-fight interview with response options."""
        clear_screen()
        
        fighter = self.game_state.fighters.get(fighter_id)
        fighter_name = fighter.name if fighter else "Fighter"
        opponent_name = result.loser_name if won else result.winner_name
        opponent_id = result.loser_id if won else result.winner_id
        
        print_header("POST-FIGHT INTERVIEW")
        print()
        
        # Show current heat level with opponent
        heat_level = self._get_heat_level(fighter_id, opponent_id)
        if heat_level > 20:
            heat_stage = "TENSION" if heat_level <= 40 else "BAD BLOOD" if heat_level <= 60 else "HEATED" if heat_level <= 80 else "WAR"
            heat_color = Colors.YELLOW if heat_level <= 40 else Colors.ORANGE if heat_level <= 60 else Colors.RED
            print(f"  {colored('Heat with ' + opponent_name + ':', heat_color)} {heat_stage} ({heat_level}/100)")
            print()
        
        if won:
            print(f"  {colored('WINNER:', Colors.GOLD)} {fighter_name}")
            print(f"  {colored('Defeated:', Colors.DIM)} {opponent_name} by {result.method}")
            print()
            print(f"  {colored('Interviewer:', Colors.CYAN)} \"{fighter_name}, congratulations on the victory!")
            print(f"   What are your thoughts on the fight?\"")
            print()
            
            # Winner response options
            print(f"  {colored('Choose your response:', Colors.YELLOW)}")
            print()
            print(f"  [1] {colored('HUMBLE', Colors.GREEN)} - Thank your team, show respect")
            print(f"      \"I just thank God and my team. {opponent_name} is a warrior.\"")
            print()
            print(f"  [2] {colored('TRASH TALK', Colors.RED)} - Boast about your dominance (+15 Heat)")
            print(f"      \"Nobody in this division can touch me! Who's next?!\"")
            print()
            print(f"  [3] {colored('CALL OUT', Colors.ORANGE)} - Challenge a specific opponent")
            print(f"      \"[Target], you're next! Stop ducking me!\"")
            print()
            print(f"  [4] {colored('RESPECTFUL', Colors.CYAN)} - Professional praise for opponent")
            print(f"      \"Nothing but respect for {opponent_name}. Great fight.\"")
            print()
            print(f"  [5] {colored('EMOTIONAL', Colors.MAGENTA)} - Show raw emotion")
            print(f"      \"I can't believe it... *tears up* ...this means everything.\"")
            print()
            
            # Check for sponsors - only show option if fighter has sponsors
            has_sponsors = self._fighter_has_sponsors(fighter_id)
            if has_sponsors:
                sponsor_names = self._get_fighter_sponsor_names(fighter_id)
                print(f"  [6] {colored('THANK SPONSORS', Colors.GOLD)} - Shout out your sponsors (+$ Bonus)")
                print(f"      \"Shout out to {sponsor_names} for believing in me!\"")
                print()
                choice = get_input("Response [1-6]: ")
                response_map = {
                    "1": "humble", "2": "trash_talk", "3": "call_out",
                    "4": "respectful", "5": "emotional", "6": "thank_sponsors"
                }
            else:
                choice = get_input("Response [1-5]: ")
                response_map = {
                    "1": "humble", "2": "trash_talk", "3": "call_out",
                    "4": "respectful", "5": "emotional"
                }
            
            response = response_map.get(choice, "humble")
            
            # Handle call out - let player pick target
            call_out_target = None
            if response == "call_out":
                call_out_target = self._select_call_out_target(fighter_id, fighter.weight_class if fighter else "")
            
            self._process_interview_response(result, fighter_id, opponent_id, True, response, call_out_target)
        else:
            print(f"  {colored('LOSER:', Colors.RED)} {fighter_name}")
            print(f"  {colored('Lost to:', Colors.DIM)} {opponent_name} by {result.method}")
            print()
            
            # Show heat level
            if heat_level > 20:
                print(f"  {colored('This loss will fuel the rivalry...', Colors.DIM)}")
                print()
            
            print(f"  {colored('Interviewer:', Colors.CYAN)} \"{fighter_name}, tough night.")
            print(f"   What happened out there?\"")
            print()
            
            # Loser response options
            print(f"  {colored('Choose your response:', Colors.YELLOW)}")
            print()
            print(f"  [1] {colored('ACCEPT DEFEAT', Colors.GREEN)} - Show class, vow to improve")
            print(f"      \"{opponent_name} was the better fighter. Back to the gym.\"")
            print()
            print(f"  [2] {colored('DEMAND REMATCH', Colors.ORANGE)} - Call for a do-over (+12 Heat)")
            print(f"      \"I want the rematch! That wasn't the real me!\"")
            print()
            print(f"  [3] {colored('CITE INJURY', Colors.YELLOW)} - Mention physical issues")
            print(f"      \"I wasn't 100% going in. Had some issues in camp.\"")
            print()
            print(f"  [4] {colored('QUESTION DECISION', Colors.RED)} - Dispute the result")
            print(f"      \"I thought I won that fight. Check the scorecards.\"")
            print()
            print(f"  [5] {colored('RETIREMENT HINT', Colors.DIM)} - Suggest the end may be near")
            print(f"      \"I need to think about my future... maybe it's time.\"")
            print()
            
            choice = get_input("Response [1-5]: ")
            
            response_map = {
                "1": "accept_defeat", "2": "demand_rematch", "3": "cite_injury",
                "4": "question_decision", "5": "retirement_hint"
            }
            response = response_map.get(choice, "accept_defeat")
            
            self._process_interview_response(result, fighter_id, opponent_id, False, response, None)
    
    def _select_call_out_target(self, fighter_id: str, weight_class: str) -> Optional[str]:
        """Let player select who to call out."""
        clear_screen()
        print_header("CALL OUT TARGET")
        print()
        
        # Get potential targets (ranked fighters in division, not self, not same camp)
        player_camp = self.game_state.get_player_camp()
        player_camp_id = player_camp.camp_id if player_camp else None
        
        targets = []
        for f in self.game_state.fighters.values():
            if f.fighter_id == fighter_id:
                continue
            if f.weight_class != weight_class:
                continue
            if getattr(f, 'camp_id', None) == player_camp_id:
                continue
            if not f.is_active:
                continue
            
            rank = self._get_fighter_division_rank(f)
            if rank is not None or self._is_division_champion(f):
                targets.append((f, rank if rank else 0))
        
        # Sort: champion first, then by rank
        targets.sort(key=lambda x: (0 if self._is_division_champion(x[0]) else 1, x[1]))
        
        if not targets:
            print("  No suitable targets to call out.")
            pause()
            return None
        
        print("  Who do you want to call out?")
        print()
        
        for i, (f, rank) in enumerate(targets[:10], 1):
            rank_str = colored("[C]", Colors.GOLD) if self._is_division_champion(f) else f"#{rank}"
            print(f"  [{i}] {rank_str} {f.name} ({f.wins}-{f.losses})")
        
        print()
        print(f"  [0] Cancel")
        print()
        
        choice = get_input("Target: ")
        try:
            idx = int(choice)
            if 1 <= idx <= len(targets[:10]):
                return targets[idx - 1][0].fighter_id
        except ValueError:
            pass
        
        return None
    
    def _process_interview_response(
        self, result: FightResult, fighter_id: str, opponent_id: str,
        won: bool, response: str, call_out_target: Optional[str]
    ) -> None:
        """Process the interview response and show effects."""
        clear_screen()
        
        fighter = self.game_state.fighters.get(fighter_id)
        fighter_name = fighter.name if fighter else "Fighter"
        opponent = self.game_state.fighters.get(opponent_id)
        opponent_name = opponent.name if opponent else "Opponent"
        
        print_header("INTERVIEW RESPONSE")
        print()
        
        # Get template based on response
        if won:
            # Get sponsor names for thank_sponsors template
            sponsor_names = self._get_fighter_sponsor_names(fighter_id)
            templates = {
                "humble": [f'{fighter_name}: "I just thank God and my team. {opponent_name} is a warrior, much respect."'],
                "trash_talk": [f'{fighter_name}: "I told everyone! Nobody in this division can touch me!"'],
                "call_out": [f'{fighter_name}: "{{target}}, you\'re next! Stop ducking me!"'],
                "respectful": [f'{fighter_name}: "{opponent_name} is a true professional. It was an honor to share the cage."'],
                "emotional": [f'{fighter_name}: "I can\'t believe it... *tears up* ...this means everything to me."'],
                "thank_sponsors": [f'{fighter_name}: "First off, shout out to {sponsor_names} for believing in me! Couldn\'t do this without their support."'],
            }
        else:
            templates = {
                "accept_defeat": [f'{fighter_name}: "{opponent_name} was the better fighter tonight. Back to the gym."'],
                "demand_rematch": [f'{fighter_name}: "I want the rematch! That wasn\'t the real me in there!"'],
                "cite_injury": [f'{fighter_name}: "I wasn\'t 100% going in. Had some issues in camp, but no excuses."'],
                "question_decision": [f'{fighter_name}: "I thought I won that fight. I don\'t know what the judges saw."'],
                "retirement_hint": [f'{fighter_name}: "I don\'t know... I need to think about my future. Maybe it\'s time."'],
            }
        
        template = random.choice(templates.get(response, templates.get("humble" if won else "accept_defeat", [""])))
        
        # Handle call out target substitution
        if call_out_target:
            target = self.game_state.fighters.get(call_out_target)
            target_name = target.name if target else "Champion"
            template = template.replace("{target}", target_name)
        
        print(f"  {colored(template, Colors.HIGHLIGHT)}")
        print()
        
        # Show effects based on response
        effects = []
        heat_added = 0
        sponsor_bonus = 0
        
        if won:
            if response == "humble":
                effects.append(("+", "Fan respect increased", Colors.GREEN))
            elif response == "trash_talk":
                effects.append(("+", "Hype increased - bigger purses", Colors.GOLD))
                effects.append(("-", "Some fans turned off", Colors.RED))
                effects.append(("Ã°Å¸â€Â¥", f"+15 Heat with {opponent_name}", Colors.RED))
                heat_added = 15
            elif response == "call_out" and call_out_target:
                target = self.game_state.fighters.get(call_out_target)
                target_name = target.name if target else "Target"
                effects.append(("!", f"Called out {target_name}", Colors.ORANGE))
                effects.append(("+", "Fight more likely to be booked", Colors.GREEN))
            elif response == "respectful":
                effects.append(("+", "Professional reputation boost", Colors.CYAN))
            elif response == "emotional":
                effects.append(("+", "Emotional connection with fans", Colors.MAGENTA))
            elif response == "thank_sponsors":
                sponsor_bonus = self._get_sponsor_bonus(fighter_id)
                if sponsor_bonus > 0:
                    effects.append(("$", f"Sponsor bonus: ${sponsor_bonus:,}", Colors.GOLD))
                    effects.append(("+", "Sponsors appreciate the shout-out", Colors.GREEN))
                else:
                    effects.append(("+", "Good impression on potential sponsors", Colors.GREEN))
        else:
            if response == "accept_defeat":
                effects.append(("+", "Maintained dignity", Colors.GREEN))
            elif response == "demand_rematch":
                effects.append(("!", "Rematch request noted", Colors.ORANGE))
                effects.append(("Ã°Å¸â€Â¥", f"+12 Heat with {opponent_name}", Colors.RED))
                heat_added = 12
            elif response == "cite_injury":
                effects.append(("-", "Some skepticism from media", Colors.YELLOW))
            elif response == "question_decision":
                effects.append(("-", "Judges may remember this", Colors.RED))
            elif response == "retirement_hint":
                effects.append(("?", "Retirement speculation begins", Colors.DIM))
        
        # Apply heat to rivalry system
        if heat_added > 0 and RIVALRY_AVAILABLE and self._rivalry_system:
            try:
                rivalry = self._rivalry_system.get_rivalry(fighter_id, opponent_id)
                if rivalry:
                    rivalry.add_score(
                        heat_added, "interview_disrespect",
                        f"{fighter_name}'s post-fight interview"
                    )
                else:
                    # Create new rivalry
                    from narrative.rivalry import RivalryType
                    rivalry = self._rivalry_system.create_rivalry(
                        fighter1_id=fighter_id,
                        fighter2_id=opponent_id,
                        fighter1_name=fighter_name,
                        fighter2_name=opponent_name,
                        rivalry_type=RivalryType.BAD_BLOOD,
                        initial_score=heat_added,
                    )
            except Exception:
                pass
        
        # Apply sponsor bonus
        if sponsor_bonus > 0:
            try:
                # Add to player camp funds
                if hasattr(self, 'player_camp') and self.player_camp:
                    self.player_camp.funds += sponsor_bonus
                elif hasattr(self.game_state, 'player_camp') and self.game_state.player_camp:
                    self.game_state.player_camp.funds += sponsor_bonus
            except Exception:
                pass
        
        if effects:
            print(f"  {colored('EFFECTS:', Colors.CYAN)}")
            for icon, text, color in effects:
                print(f"    [{icon}] {colored(text, color)}")
            print()
        
        # Show opponent reaction
        print(f"  {colored('OPPONENT REACTION:', Colors.YELLOW)}")
        if won and response == "trash_talk":
            print(f"    {opponent_name}: \"Big talk. We'll see if they give me a rematch.\"")
        elif won and response == "call_out" and call_out_target:
            target = self.game_state.fighters.get(call_out_target)
            if target:
                print(f"    {target.name}: \"Anytime, anywhere. Sign the contract.\"")
        elif not won and response == "demand_rematch":
            print(f"    {opponent_name}: \"I already beat them once. Happy to do it again.\"")
        elif not won and response == "question_decision":
            print(f"    {opponent_name}: \"Sore loser. Watch the tape.\"")
        else:
            print(f"    {opponent_name}: \"Good fight. Respect.\"")
        print()
        
        pause()
    
    def _show_social_media_reactions(self, result: FightResult, player_fighter_id: str, won: bool) -> None:
        """Show social media reactions to the fight."""
        clear_screen()
        print_header("SOCIAL MEDIA REACTIONS")
        print()
        
        fighter = self.game_state.fighters.get(player_fighter_id)
        fighter_name = fighter.name if fighter else "Fighter"
        opponent_name = result.loser_name if won else result.winner_name
        
        # Generate contextual reactions
        reactions = []
        
        if won:
            if result.method in ["KO", "TKO"]:
                reactions = [
                    (f"@MMAFanatic", f"HOLY SMOKES! {fighter_name} just SLEPT {opponent_name}! [!][!]", "[!] 12.4K"),
                    (f"@CageSideNews", f"BREAKING: {fighter_name} scores highlight reel finish! Title shot incoming?", "[!] 8.2K"),
                    (f"@FightAnalyst", f"That power from {fighter_name} is legit. {opponent_name} never saw it coming.", "[=] 3.1K"),
                    (f"@UFCFan2024", f"{fighter_name} is a PROBLEM in this division [P]", "[+] 5.7K"),
                ]
            elif result.method == "SUB":
                reactions = [
                    (f"@BJJWorld", f"Beautiful submission by {fighter_name}! Textbook technique [J]", "[J] 9.8K"),
                    (f"@MMADaily", f"{fighter_name} showing elite ground game. {opponent_name} had no answer.", "[!] 6.3K"),
                    (f"@GrapplingFan", f"That was SLICK! {fighter_name}'s jiu-jitsu is next level [!]", "[!] 4.2K"),
                ]
            else:  # Decision
                reactions = [
                    (f"@MMAStatGuy", f"Solid performance from {fighter_name}. Controlled the fight throughout.", "[=] 4.5K"),
                    (f"@CageWarrior", f"{fighter_name} gets the W. {opponent_name} made it competitive though.", "[+] 3.8K"),
                    (f"@FightFan99", f"Good win for {fighter_name} but I want to see them tested more.", "[?] 2.1K"),
                ]
            
            if result.is_title_fight:
                reactions.insert(0, (f"@DFCOfficial", f"AND NEW! [T] {fighter_name} is your NEW champion! #DFC", "[T] 45.2K"))
        else:
            reactions = [
                (f"@MMAHotTakes", f"Tough night for {fighter_name}. Back to the drawing board.", "[-] 3.2K"),
                (f"@FightAnalyst", f"{fighter_name} exposed? Or just a bad night? Time will tell.", "[?] 5.1K"),
                (f"@CageSideNews", f"{opponent_name} gets the upset! What's next for {fighter_name}?", "[!] 7.4K"),
            ]
            
            if result.is_title_fight:
                reactions.insert(0, (f"@DFCOfficial", f"Heartbreak for {fighter_name}. Title dreams dashed tonight. #DFC", "[!] 28.9K"))
        
        # Shuffle and display
        random.shuffle(reactions[1:])  # Keep first one if title fight
        
        for handle, text, engagement in reactions[:4]:
            print(f"  {colored(handle, Colors.CYAN)}")
            print(f"    {text}")
            print(f"    {colored(engagement + ' likes', Colors.DIM)}")
            print()
        
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
        
        # Get heat level from rivalry
        heat_level = self._get_heat_level(f1_id, f2_id)
        
        # Try narrated simulation first
        sim_result = self._narrated_fight_simulation(
            f1_id, f2_id, rounds,
            is_title_fight=is_title,
            is_main_event=is_main,
            heat_level=heat_level
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
                is_main_event=is_main,
                heat_level=heat_level
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
            card_slot=fight.get("card_slot", ""),
            fighter1_strikes=sim_result.get("fighter1_strikes", 0),
            fighter2_strikes=sim_result.get("fighter2_strikes", 0),
            fighter1_takedowns=sim_result.get("fighter1_takedowns", 0),
            fighter2_takedowns=sim_result.get("fighter2_takedowns", 0),
            fighter1_sub_attempts=sim_result.get("fighter1_sub_attempts", 0),
            fighter2_sub_attempts=sim_result.get("fighter2_sub_attempts", 0),
        )
        
        # Process ranking changes FIRST
        # But capture pre-fight ranks before processing
        winner_rec = self.game_state.fighters.get(winner_id)
        loser_rec = self.game_state.fighters.get(loser_id)
        winner_pre_rank = self._get_fighter_rank_num(winner_rec) if winner_rec else ""
        loser_pre_rank = self._get_fighter_rank_num(loser_rec) if loser_rec else ""
        winner_record = f"({winner_rec.wins}-{winner_rec.losses})" if winner_rec else ""
        loser_record = f"({loser_rec.wins}-{loser_rec.losses})" if loser_rec else ""
        
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
        
        # Store for week summary display (with pre-fight ranks)
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
                "card_slot": fight.get("card_slot", ""),
                "weight_class": fight.get("weight_class", ""),
                "event_name": event_name,
                "ranking_changes": ranking_changes,
                "is_controversial": getattr(result, 'is_controversial', False),
                "controversy_reason": getattr(result, 'controversy_reason', ''),
                "judge_names": getattr(result, 'judge_names', []),
                # Pre-fight data for accurate display
                "winner_pre_rank": winner_pre_rank,
                "loser_pre_rank": loser_pre_rank,
                "winner_record": winner_record,
                "loser_record": loser_record,
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
        
        # Update fighter records using consolidated function
        is_title = fight_info.get("is_title_fight", False)
        self._apply_fight_result(
            winner_id=winner_id,
            loser_id=loser_id,
            winner_name=winner_name,
            loser_name=loser_name,
            method=method,
            is_title=is_title,
            event_name=event_name,
            generate_news=False,  # News handled separately below with heat-flavored headlines
        )
        
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
        
        # News with heat-flavored headlines
        heat_prefix = ""
        if heat_level > 80:
            heat_prefix = "VENDETTA SETTLED! "
        elif heat_level > 60:
            heat_prefix = "RIVALRY CLASH! "
        elif heat_level > 40:
            heat_prefix = "BAD BLOOD RESOLVED! "
        
        if method == "DEC":
            headline = f"{heat_prefix}{winner_name} defeats {loser_name} by decision"
        else:
            headline = f"{heat_prefix}{winner_name} finishes {loser_name} by {method} (R{finish_round})"
        
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
                is_champion = self._is_division_champion(fighter)
                
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
                        
                        # Aging happens silently - no news displayed
                        # (retirements still shown below)
                
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
    
    def _process_popularity_decay(self) -> List[str]:
        """
        Process popularity decay for inactive fighters.
        
        Fighters who haven't fought in 6+ months lose popularity.
        Called once per month (every 4 weeks).
        """
        events = []
        current_week = self.game_state.week_number
        decay_threshold_weeks = 26  # 6 months
        
        for fighter_id, fighter_data in self.fighter_data.items():
            # Skip inactive fighters
            if not fighter_data.is_active:
                continue
            
            # Find last fight week from fight_history
            last_fight_week = 0
            if fighter_data.fight_history:
                for fight in fighter_data.fight_history:
                    fight_week = fight.get("week", 0)
                    if fight_week > last_fight_week:
                        last_fight_week = fight_week
            
            # Calculate weeks since last fight
            weeks_inactive = current_week - last_fight_week
            
            # Apply decay if inactive too long
            if weeks_inactive > decay_threshold_weeks and fighter_data.popularity > 5:
                # Decay 2 popularity per month of inactivity beyond threshold
                months_over = (weeks_inactive - decay_threshold_weeks) // 4
                if months_over > 0:
                    old_pop = fighter_data.popularity
                    fighter_data.popularity = max(5, fighter_data.popularity - 2)
                    
                    # Only sync if changed
                    if fighter_data.popularity != old_pop:
                        self._sync_fighter_record(fighter_id)
        
        return events
    
    def _process_inbox_weekly(self) -> None:
        """Process inbox weekly - clear expired, generate scout reports."""
        if not INBOX_AVAILABLE or not self._inbox:
            return
        
        current_week = self.game_state.week_number
        
        # Clear expired notifications
        self._inbox.clear_expired(current_week)
        
        # Reset weekly scout tracking
        self._inbox.reset_weekly_scouts()
        
        # Generate scout reports from coaches (every 3-4 weeks)
        if current_week % 3 == 0:
            self._generate_coach_scout_reports()
        
        # Check for financial alerts
        self._check_financial_alerts()
        
        # Check for ranking changes
        self._check_ranking_alerts()
    
    def _generate_coach_scout_reports(self) -> None:
        """Have coaches scout amateurs based on their specialty."""
        if not INBOX_AVAILABLE or not self._inbox:
            return
        
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        # Get camp's coaches
        coaches = []
        if COACHES_AVAILABLE and self._coach_system:
            try:
                coaches = self._coach_system.get_camp_coaches(player_camp.camp_id)
            except:
                pass
        
        # Get head coach specialty as fallback
        head_specialty = getattr(player_camp, 'head_coach_specialty', None)
        if not head_specialty and hasattr(player_camp, 'head_coach'):
            coach = player_camp.head_coach
            if hasattr(coach, 'specialty'):
                head_specialty = coach.specialty
        
        if not coaches and head_specialty:
            # Create fake coach entry for head coach
            coaches = [type('Coach', (), {'specialty': head_specialty, 'name': 'Head Coach'})()]
        
        if not coaches:
            return
        
        # Get camp region for regional bias
        camp_region = getattr(player_camp, 'region', 'Americas')
        
        # Get amateur fighters to scout
        amateur_fighters = []
        if AMATEUR_AVAILABLE and self._amateur_system:
            try:
                # Get all amateur fighters
                all_amateurs = self._amateur_system.get_all_fighters()
                # Filter to those with decent records
                amateur_fighters = [
                    f for f in all_amateurs
                    if getattr(f, 'wins', 0) >= 2 or getattr(f, 'potential_tier', 'Average') in ['Elite', 'High']
                ]
            except:
                pass
        
        if not amateur_fighters:
            return
        
        # Each coach has a chance to find a prospect
        current_week = self.game_state.week_number
        
        for coach in coaches[:2]:  # Max 2 scout reports per week
            specialty = getattr(coach, 'specialty', 'Balanced')
            
            # 40% chance per coach to find someone
            if random.random() > 0.40:
                continue
            
            # Use the scout generation helper
            try:
                scout_data = generate_scout_report_for_coach(
                    coach_specialty=specialty,
                    camp_region=camp_region,
                    amateur_fighters=amateur_fighters,
                    current_week=current_week,
                )
                
                if scout_data:
                    self._inbox.add_scout_report(scout_data, current_week)
            except:
                pass
    
    def _check_financial_alerts(self) -> None:
        """Generate financial alerts if needed."""
        if not INBOX_AVAILABLE or not self._inbox:
            return
        
        if not ECONOMY_AVAILABLE or not self._economy_manager:
            return
        
        try:
            balance = self._economy_manager.balance
            weekly_cost = self._economy_manager.get_weekly_cost()
            
            if weekly_cost > 0:
                weeks_until_broke = balance // weekly_cost if balance > 0 else 0
                
                if weeks_until_broke <= 4:
                    self._inbox.add_financial_alert(
                        balance=balance,
                        weekly_cost=weekly_cost,
                        weeks_until_broke=weeks_until_broke,
                        current_week=self.game_state.week_number,
                    )
        except:
            pass
    
    def _check_ranking_alerts(self) -> None:
        """Check for ranking changes and generate alerts."""
        if not INBOX_AVAILABLE or not self._inbox:
            return
        
        # This would compare previous rankings to current
        # For now, we'll generate title opportunity alerts
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            return
        
        try:
            for fighter in self.game_state.fighters.values():
                if getattr(fighter, 'camp_id', None) != player_camp.camp_id:
                    continue
                if not fighter.is_active:
                    continue
                
                rank = self._get_fighter_division_rank(fighter)
                
                # Alert if in title contention
                if rank and rank <= 5 and not self._is_division_champion(fighter):
                    # Check if we recently added this alert
                    existing = [n for n in self._inbox.get_by_type(NotificationType.TITLE_OPPORTUNITY)
                               if n.fighter_id == fighter.fighter_id]
                    
                    if not existing:
                        self._inbox.add_title_opportunity(
                            fighter_id=fighter.fighter_id,
                            fighter_name=fighter.name,
                            division=fighter.weight_class,
                            current_rank=rank,
                            current_week=self.game_state.week_number,
                        )
        except:
            pass
    
    def _process_ladder_week(self) -> List[str]:
        """Process division ladder weekly updates - challenges, freezes, incoming."""
        events = []
        
        if not LADDER_AVAILABLE or not self._division_ladder:
            return events
        
        try:
            game = self.game_state
            week = game.week_number
            player_camp = game.get_player_camp()
            
            if not player_camp:
                return events
            
            # Process weekly ladder updates (reset limits, expire old challenges)
            ladder_results = self._division_ladder.process_week(week)
            
            # Report expired challenges
            for challenger_name in ladder_results.get("expired_challenges", []):
                events.append(f"Challenge from {challenger_name} expired (no response)")
            
            # Resolve pending challenges from player
            pending_resolutions = self._division_ladder.resolve_pending_challenges(week)
            if pending_resolutions:
                events.append("")  # Blank line for separation
                events.append("=== FIGHT OFFER RESPONSES ===")
                
                accepted_fights = []
                
                for resolution in pending_resolutions:
                    challenge = resolution.challenge
                    if resolution.accepted:
                        # Fight scheduled!
                        fight_week = resolution.event_week if resolution.event_week else week + 8
                        
                        fight_data = {
                            "fighter1_id": challenge.challenger_id,
                            "fighter1_name": challenge.challenger_name,
                            "fighter2_id": challenge.target_id,
                            "fighter2_name": challenge.target_name,
                            "weeks_until": fight_week - week,
                            "current_week": week,
                            "weight_class": challenge.weight_class,
                            "is_title_fight": challenge.is_title_fight,
                        }
                        
                        accepted_fights.append((challenge, fight_data, resolution))
                        events.append(f"  [ACCEPTED] {challenge.target_name} vs {challenge.challenger_name} - Week {fight_week}")
                        
                        # Note: News about fight being OFFICIAL will be added after player confirms
                        # For now, just note that opponent accepted the challenge
                    else:
                        events.append(f"  [DECLINED] {challenge.target_name} - {resolution.message}")
                        
                        # Add news item with trash talk for the snub
                        snub_quotes = [
                            f'"{challenge.challenger_name}? Never heard of them."',
                            f'"I only fight contenders, not cans."',
                            f'"Call me when you\'ve actually beaten someone."',
                            f'"That fight does nothing for my career."',
                            f'"Maybe next year, kid."',
                            f'"I\'m focused on the title, not side shows."',
                            f'"They\'re not on my level yet."',
                            f'"Win a few more and we\'ll talk."',
                            f'"I don\'t see the point in that matchup."',
                            f'"My manager said no. Smart move."',
                        ]
                        snub_quote = random.choice(snub_quotes)
                        
                        if hasattr(self, 'news_feed') and self.news_feed is not None:
                            self.news_feed.insert(0, NewsItem(
                                headline=f"{challenge.target_name} turns down {challenge.challenger_name}'s challenge",
                                details=snub_quote,
                                category="callout",
                                week=week,
                            ))
                        
                        # Add heat for declined challenge (snub generates rivalry)
                        if RIVALRY_AVAILABLE and self._rivalry_system:
                            try:
                                # Get or create rivalry between these fighters
                                rivalry = self._rivalry_system.get_rivalry(
                                    challenge.challenger_id, challenge.target_id
                                )
                                if rivalry:
                                    rivalry.add_score(
                                        15, "snubbed_challenge",
                                        f"{challenge.target_name} declined {challenge.challenger_name}'s challenge"
                                    )
                                else:
                                    # Create new rivalry from the snub
                                    from narrative.rivalry import RivalryType
                                    rivalry = self._rivalry_system.create_rivalry(
                                        fighter1_id=challenge.challenger_id,
                                        fighter2_id=challenge.target_id,
                                        fighter1_name=challenge.challenger_name,
                                        fighter2_name=challenge.target_name,
                                        rivalry_type=RivalryType.BAD_BLOOD,
                                        initial_score=15,
                                    )
                                    if rivalry:
                                        rivalry.add_score(
                                            0, "snubbed_challenge",
                                            f"{challenge.target_name} declined {challenge.challenger_name}'s challenge"
                                        )
                            except Exception:
                                pass  # Silently fail if rivalry system has issues
                
                # Store accepted fights for player confirmation (NOT auto-scheduled)
                # Player will be prompted to confirm each fight after week summary
                if accepted_fights:
                    if not hasattr(self, '_pending_fight_confirmations'):
                        self._pending_fight_confirmations = []
                    for challenge, fight_data, resolution in accepted_fights:
                        self._pending_fight_confirmations.append({
                            'challenge': challenge,
                            'fight_data': fight_data,
                            'resolution': resolution
                        })
                
                events.append("")  # Blank line after section
            
            # Generate incoming challenges for player fighters
            # Get player fighters as ladder entries
            player_fighters = [
                f for f in game.fighters.values()
                if getattr(f, 'camp_id', None) == player_camp.camp_id and f.is_active
            ]
            
            # Group by division and generate challenges
            divisions = set(f.weight_class for f in player_fighters)
            
            for division in divisions:
                div_fighters = [f for f in player_fighters if f.weight_class == division]
                div_state = game.divisions.get(division)
                champion_id = div_state.champion_id if div_state else None
                
                # Fetch rankings data
                rankings_data = []
                if RANKINGS_AVAILABLE and self._rankings_system:
                    try:
                        from core.types import WeightClass
                        wc = WeightClass(division)
                        rankings_data = self._rankings_system.get_rankings(wc)
                    except:
                        pass
                
                # FALLBACK: Check if we have ranked fighters (rank > 0), not just champion
                has_ranked_fighters = any(rank > 0 for rank, _, _ in rankings_data)
                if not has_ranked_fighters:
                    champion_entry = next(((r, fid, name) for r, fid, name in rankings_data if r == 0), None)
                    rankings_data = []
                    if champion_entry:
                        rankings_data.append(champion_entry)
                    elif champion_id:
                        champ = game.fighters.get(champion_id)
                        if champ:
                            rankings_data.append((0, champion_id, champ.name))
                    all_div_fighters = [
                        f for f in game.fighters.values()
                        if f.weight_class == division and f.is_active and f.fighter_id != champion_id
                    ]
                    def elo_lite_key(f):
                        total = f.wins + f.losses
                        win_pct = f.wins / total if total > 0 else 0
                        return (win_pct, f.wins, f.overall_rating)
                    all_div_fighters.sort(key=elo_lite_key, reverse=True)
                    for i, f in enumerate(all_div_fighters[:15], 1):
                        rankings_data.append((i, f.fighter_id, f.name))
                
                # Build ladder for this division
                ladder = self._division_ladder.build_ladder(
                    weight_class=division,
                    fighters=game.fighters,
                    fighter_data=self.fighter_data,
                    rankings_data=rankings_data,
                    injury_system=self._injury_system,
                    scheduled_fights=self.player_scheduled_fights + self.ai_scheduled_fights,
                    cooldowns=self._fighter_cooldowns,
                    player_camp_id=player_camp.camp_id,
                    champion_id=champion_id,
                    camps=game.camps,
                )
                
                # Get player entries from ladder
                player_entries = [e for e in ladder if e.is_player_fighter]
                
                # Generate incoming challenges (happens ~15% of weeks per available fighter)
                new_challenges = self._division_ladder.generate_incoming_challenges(
                    player_entries, ladder, week
                )
                
                # Set weight class on challenges
                for challenge in new_challenges:
                    challenge.weight_class = division
                
                # Report new challenges
                for challenge in new_challenges:
                    events.append(f"[M] {challenge.challenger_name} challenges {challenge.target_name}!")
                    
                    # Add news item
                    self.news_feed.insert(0, NewsItem(
                        headline=f"{challenge.challenger_name} calls out {challenge.target_name}",
                        details=f'"{challenge.message}"',
                        category="callout",
                        week=week,
                    ))
        
        except Exception as e:
            # Don't crash week advancement on ladder errors
            pass
        
        return events
    
    def _process_amateur_week(self) -> List[str]:
        """Process amateur tournaments for this week."""
        events = []
        
        if not AMATEUR_AVAILABLE or not self._amateur_system:
            return events
        
        try:
            current_week = self.game_state.week_number if self.game_state else 1
            current_year = (current_week // 52) + 1
            
            # Schedule tournaments for the year if not done
            if not self._amateur_system.scheduled_tournaments:
                self._amateur_system.schedule_year_tournaments(current_year, start_week=current_week)
            
            # Process this week's tournaments
            result = self._amateur_system.process_week(current_week)
            
            # Report completed tournaments (key is "tournaments_run" in amateur.py)
            # Tournament results are TournamentResults dataclass objects, not dicts
            if result.get("tournaments_run"):
                for tourney_result in result["tournaments_run"]:
                    # Access dataclass attributes directly
                    region = getattr(tourney_result, 'region', 'Unknown')
                    weight_class = getattr(tourney_result, 'weight_class', 'Unknown')
                    champion = getattr(tourney_result, 'champion_name', 'Unknown')
                    
                    events.append(
                        f"  {colored('AMATEUR:', Colors.CYAN)} {region} {weight_class} - "
                        f"Champion: {colored(champion, Colors.GOLD)}"
                    )
            
            # Report new pro-eligible fighters (key is "newly_eligible" in amateur.py)
            newly_eligible_names = []
            if result.get("newly_eligible"):
                for fighter_id in result["newly_eligible"][:3]:  # These are fighter IDs
                    fighter = self._amateur_system.get_amateur(fighter_id) if hasattr(self._amateur_system, 'get_amateur') else None
                    if fighter:
                        newly_eligible_names.append(fighter.name)
                    else:
                        newly_eligible_names.append(fighter_id)
            
            for fighter_name in newly_eligible_names:
                events.append(
                    f"  {colored('PRO-READY:', Colors.GREEN)} {fighter_name} now eligible for signing"
                )
        except Exception as e:
            # Silently handle errors in amateur processing
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
        """Show enhanced Universe Recap - the 'So What?' of each week."""
        print_divider()
        print()
        
        # Collect all week data
        week_results = self._week_fight_results if hasattr(self, '_week_fight_results') else []
        training_updates = []
        finance_updates = []
        injury_events = []
        amateur_events = []
        retirement_events = []
        other_events = []
        fotn_info = None
        
        # Get player's fighter IDs for filtering training updates
        player_fighter_ids = set(self.player_fighters) if hasattr(self, 'player_fighters') else set()
        player_fighter_names = set()
        for fid in player_fighter_ids:
            f = self.game_state.fighters.get(fid)
            if f:
                player_fighter_names.add(f.name.lower())
        
        # Parse events into categories
        in_training_block = False
        current_training_is_player = False
        
        for event in events:
            if not event:
                continue
            event_lower = event.lower()
            
            # FOTN check FIRST (before $ check, since FOTN contains $50,000)
            if "fight of the night" in event_lower:
                fotn_info = event
                in_training_block = False
            # Amateur events (tournaments, pro-ready)
            elif "amateur:" in event_lower or "pro-ready:" in event_lower:
                amateur_events.append(event)
                in_training_block = False
            # Retirement events
            elif "retirement:" in event_lower:
                retirement_events.append(event)
                in_training_block = False
            # Training - check if it's for a player's fighter
            elif "training" in event_lower or "camp" in event_lower or ("week" in event_lower and "/" in event):
                # Check if this training is for a player's fighter
                is_player_training = any(name in event_lower for name in player_fighter_names)
                if is_player_training:
                    training_updates.append(event)
                    in_training_block = True
                    current_training_is_player = True
                else:
                    in_training_block = False
                    current_training_is_player = False
            elif in_training_block and current_training_is_player and event.startswith("  "):
                # This is a continuation of player's training output (indented gain lines)
                training_updates.append(event)
            elif "$" in event or "expense" in event_lower or "balance" in event_lower:
                finance_updates.append(event)
                in_training_block = False
            elif "injury" in event_lower or "injured" in event_lower or "healed" in event_lower or "recovered" in event_lower:
                injury_events.append(event)
                in_training_block = False
            else:
                other_events.append(event)
                in_training_block = False
        
        # =====================================================================
        # HEADER - Universe Recap Style
        # =====================================================================
        print(f"  {colored('=' * 64, Colors.CYAN)}")
        week_text = f"WEEK {self.game_state.week_number} RECAP"
        print(f"  {colored(week_text, Colors.HIGHLIGHT):^70}")
        print(f"  {colored('=' * 64, Colors.CYAN)}")
        print()
        
        # =====================================================================
        # TOP HEADLINES (Title changes, upsets, finishes, notable retirements)
        # =====================================================================
        headlines = self._generate_top_headlines(week_results)
        
        # Add notable retirements to top stories (high P4P/GOAT)
        notable_retirements = []
        normal_retirements = []
        for ret_event in retirement_events:
            # Extract fighter name from retirement event
            # Format: "  RETIREMENT: Name (age) announces retirement"
            is_notable = False
            try:
                # Parse name from event
                if "RETIREMENT:" in ret_event:
                    name_part = ret_event.split("RETIREMENT:")[-1].strip()
                    name = name_part.split("(")[0].strip()
                    # Check if they're notable (former champ, high ranked, etc.)
                    for fid, f in self.game_state.fighters.items():
                        if f.name == name:
                            # Check if they were ever champion or top 5
                            if hasattr(f, 'title_defenses') and f.title_defenses > 0:
                                is_notable = True
                            elif f.wins >= 10:  # Veteran with many wins
                                is_notable = True
                            break
            except:
                pass
            
            if is_notable:
                notable_retirements.append(f"[>] {name} announces retirement")
            else:
                normal_retirements.append(ret_event)
        
        # Add notable retirements to headlines
        headlines.extend(notable_retirements)
        
        if headlines:
            print(f"  {colored('[TOP STORIES]', Colors.GOLD)}")
            for headline in headlines:
                print(f"    {headline}")
            print()
        
        # =====================================================================
        # FINANCES (with milestones)
        # =====================================================================
        if finance_updates:
            print(f"  {colored('[FINANCES]', Colors.WIN)}")
            for update in finance_updates:
                clean = self._clean_garbled_text(update)
                print(f"    {clean}")
            
            # =================================================================
            # DOPAMINE: MONEY MILESTONES
            # =================================================================
            player_camp = self.game_state.get_player_camp()
            if player_camp and self._economy_manager and ECONOMY_AVAILABLE:
                try:
                    balance = self._economy_manager.get_balance(player_camp.camp_id)
                    
                    # Check for milestone crossings (would need to track previous balance)
                    # For now, just show current tier
                    if balance >= 1000000:
                        print(f"    {colored('[$] MILLIONAIRE STATUS!', Colors.GOLD)}")
                    elif balance >= 500000:
                        print(f"    {colored('[$] Half-Million Club!', Colors.CYAN)}")
                    elif balance >= 250000:
                        print(f"    {colored('[$] Quarter-Million!', Colors.GREEN)}")
                except:
                    pass
            
            print()
        
        # =====================================================================
        # FIGHT OF THE NIGHT - Pretty Box
        # =====================================================================
        if fotn_info:
            print(f"  {colored('*' * 64, Colors.GOLD)}")
            print(f"  {colored('>>> FIGHT OF THE NIGHT <<<', Colors.GOLD):^70}")
            # Parse the fighters from the event string
            clean_fotn = self._clean_garbled_text(fotn_info)
            if ":" in clean_fotn:
                parts = clean_fotn.split(":")
                if len(parts) > 1:
                    fighters = parts[1].strip().split("(")[0].strip()
                    print(f"  {colored(fighters, Colors.HIGHLIGHT):^70}")
            print(f"  {colored('$50,000 bonus to each fighter!', Colors.WIN):^70}")
            print(f"  {colored('*' * 64, Colors.GOLD)}")
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
                
                # Group fights by card_slot (UFC-style)
                card_sections = {
                    "main_event": [],
                    "co_main": [],
                    "main_card": [],
                    "prelim": [],
                    "early_prelim": [],
                }
                
                for fight in fights:
                    slot = fight.get("card_slot", "")
                    # Fallback for legacy fights without card_slot
                    if not slot or slot not in card_sections:
                        if fight.get("is_title_fight") or fight.get("is_main_event"):
                            slot = "main_event"
                        elif fight.get("is_co_main"):
                            slot = "co_main"
                        else:
                            slot = "prelim"
                    card_sections[slot].append(fight)
                
                # Sort within each section by combined rating (highest first)
                for slot in card_sections:
                    card_sections[slot].sort(key=lambda f: (
                        -int(f.get("is_title_fight", False)),
                        -(self.fighter_data.get(f.get("winner_id"), type('', (), {"overall_rating": 50})()).overall_rating +
                          self.fighter_data.get(f.get("loser_id"), type('', (), {"overall_rating": 50})()).overall_rating)
                    ))
                
                # Display each section
                if card_sections["main_event"]:
                    print(f"  {colored('=== MAIN EVENT ===', Colors.GOLD)}")
                    for fight in card_sections["main_event"]:
                        self._display_fight_result_card(fight)
                
                if card_sections["co_main"]:
                    print(f"  {colored('=== CO-MAIN EVENT ===', Colors.ORANGE)}")
                    for fight in card_sections["co_main"]:
                        self._display_fight_result_card(fight)
                
                if card_sections["main_card"]:
                    print(f"  {colored('=== MAIN CARD ===', Colors.CYAN)}")
                    for fight in card_sections["main_card"]:
                        self._display_fight_result_card(fight)
                
                if card_sections["prelim"]:
                    print(f"  === PRELIMS ===")
                    for fight in card_sections["prelim"]:
                        self._display_fight_result_card(fight)
                
                if card_sections["early_prelim"]:
                    print(f"  {colored('=== EARLY PRELIMS ===', Colors.DIM)}")
                    for fight in card_sections["early_prelim"]:
                        self._display_fight_result_card(fight)
                
                # Legend
                print()
                print(f"  {colored('*', Colors.GOLD)} = Finish (KO/TKO/SUB)")
                print()
        
        # =====================================================================
        # RANKINGS SHAKEUP
        # =====================================================================
        ranking_changes = self._get_ranking_changes(week_results)
        if ranking_changes:
            print(f"  {colored('[RANKINGS SHAKEUP]', Colors.CYAN)}")
            for change in ranking_changes[:8]:  # Limit to 8
                print(f"    {change}")
            print()
        
        # =====================================================================
        # MEDICAL SUSPENSIONS (Major injuries only)
        # =====================================================================
        major_injuries = self._get_major_injuries()
        if major_injuries:
            print(f"  {colored('[MEDICAL SUSPENSIONS]', Colors.RED)}")
            for injury in major_injuries[:5]:
                print(f"    {injury}")
            print()
        
        # =====================================================================
        # TRAINING PROGRESS (Player's fighters only)
        # =====================================================================
        if training_updates:
            print(f"  {colored('[YOUR CAMP]', Colors.CYAN)}")
            for update in training_updates:
                clean = self._clean_garbled_text(update)
                if clean:
                    print(f"    {clean}")
            print()
        
        # =====================================================================
        # COMING UP (Next week's fights)
        # =====================================================================
        upcoming = self._get_upcoming_fights()
        if upcoming:
            print(f"  {colored('[COMING UP]', Colors.MAGENTA)}")
            for fight in upcoming[:5]:
                print(f"    {fight}")
            print()
        
        # =====================================================================
        # AMATEUR CIRCUIT
        # =====================================================================
        if amateur_events:
            print(f"  {colored('[AMATEUR CIRCUIT]', Colors.CYAN)}")
            for event in amateur_events[:5]:  # Limit to 5
                clean = self._clean_garbled_text(event)
                if clean:
                    # Strip the "AMATEUR:" prefix if present since we have a header
                    display = clean.replace("AMATEUR:", "").replace("PRO-READY:", "").strip()
                    print(f"    {display}")
            print()
        
        # =====================================================================
        # SOCIAL MEDIA BUZZ (Notable fight reactions)
        # =====================================================================
        if MEDIA_AVAILABLE and week_results:
            social_reactions = []
            
            # Get reactions for notable fights (title fights, upsets, big finishes)
            for fight in week_results[:5]:  # Check top 5 fights
                is_title = fight.get("is_title_fight", False)
                is_main = fight.get("is_main_event", False)
                method = fight.get("method", "DEC")
                winner_name = fight.get("winner_name", "")
                loser_name = fight.get("loser_name", "")
                round_num = fight.get("round", 3)
                
                # Determine if upset (pre-fight ranks)
                was_upset = False
                winner_pre = fight.get("winner_pre_rank", "")
                loser_pre = fight.get("loser_pre_rank", "")
                try:
                    if winner_pre and loser_pre and "#" in str(winner_pre) and "#" in str(loser_pre):
                        w_num = int(str(winner_pre).replace("#", ""))
                        l_num = int(str(loser_pre).replace("#", ""))
                        if w_num > l_num + 4:
                            was_upset = True
                except:
                    pass
                
                # Get winner data for reactions
                winner_id = fight.get("winner_id")
                winner_data = self.game_state.fighters.get(winner_id)
                winner_full = self.fighter_data.get(winner_id)
                
                # Only generate for notable fights
                if is_title or is_main or was_upset or method in ["KO", "TKO", "SUB"]:
                    try:
                        reactions = generate_fight_reactions(
                            method=method,
                            winner_name=winner_name,
                            loser_name=loser_name,
                            round_finished=round_num,
                            is_title_fight=is_title,
                            is_main_event=is_main,
                            was_upset=was_upset,
                            winner_age=winner_data.age if winner_data else 28,
                            winner_fights=(winner_data.wins + winner_data.losses) if winner_data else 10,
                            winner_streak=winner_full.win_streak if winner_full else 0,
                            winner_wins=winner_data.wins if winner_data else 5,
                            winner_losses=winner_data.losses if winner_data else 2,
                        )
                        for r in reactions[:1]:  # One reaction per notable fight
                            social_reactions.append(r)
                    except:
                        pass
            
            if social_reactions:
                print(f"  {colored('[SOCIAL MEDIA]', Colors.MAGENTA)}")
                for reaction in social_reactions[:4]:  # Limit to 4 total
                    handle = reaction.get("handle", "@MMAFan")
                    take = reaction.get("take", "")
                    if take:
                        print(f"    {colored(handle, Colors.CYAN)}: \"{take}\"")
                print()
        
        # =====================================================================
        # OTHER NEWS (Retirements, signings, etc.)
        # =====================================================================
        # Combine non-notable retirements with other events
        all_other = []
        for ret in normal_retirements:
            # Clean up retirement text
            clean = self._clean_garbled_text(ret)
            if clean:
                all_other.append(clean)
        
        relevant_other = [e for e in other_events if e.strip() and "fight of the night" not in e.lower()]
        for event in relevant_other:
            clean = self._clean_garbled_text(event)
            if clean and len(clean) > 2:
                all_other.append(clean)
        
        if all_other:
            print(f"  {colored('[OTHER NEWS]', Colors.DIM)}")
            for event in all_other[:5]:  # Limit to 5
                print(f"    * {event}")
            print()
        
        print(f"  {colored('-' * 64, Colors.DIM)}")
        print()
        
        if not week_results and not training_updates and not other_events and not amateur_events:
            print(f"  {colored('A quiet week in the world of MMA...', Colors.DIM)}")
            print()
    
    def _generate_top_headlines(self, week_results: List[Dict]) -> List[str]:
        """Generate top headlines from fight results with priority tiers."""
        # Separate headlines by priority tier
        tier1_headlines = []  # Title changes, champion news
        tier2_headlines = []  # Upsets, rivalries, watchlist
        tier3_headlines = []  # Big finishes, ranked fighter news
        
        # Get player's watchlist for personalized stories
        watchlist_ids = set()
        if hasattr(self, '_watchlist') and self._watchlist:
            try:
                watchlist_ids = set(self._watchlist.get_all_fighter_ids())
            except:
                pass
        
        # Get active rivalries for rivalry news
        active_rivalries = {}
        if RIVALRY_AVAILABLE and self._rivalry_system:
            try:
                for rivalry in self._rivalry_system.get_active_rivalries():
                    active_rivalries[rivalry.fighter1_id] = rivalry
                    active_rivalries[rivalry.fighter2_id] = rivalry
            except:
                pass
        
        for fight in week_results:
            winner_name = fight.get("winner_name", "Fighter")
            loser_name = fight.get("loser_name", "Opponent")
            method = fight.get("method", "DEC").upper()
            round_num = fight.get("round", 3)
            is_title = fight.get("is_title_fight", False)
            weight_class = fight.get("weight_class", "")
            winner_id = fight.get("winner_id")
            loser_id = fight.get("loser_id")
            
            div = self._get_division_abbrev(weight_class)
            
            # Get rankings for context - USE PRE-FIGHT DATA, not current state!
            # By the time we display results, titles may have changed hands
            winner_rank = fight.get("winner_pre_rank", "")
            loser_rank = fight.get("loser_pre_rank", "")
            
            # Determine champion status from pre-fight ranks
            winner_was_champ = winner_rank == "[C]" or "[C]" in str(winner_rank)
            loser_was_champ = loser_rank == "[C]" or "[C]" in str(loser_rank)
            
            # Fallback to current state only if no pre-fight data available
            if not winner_rank and winner_id and winner_id in self.game_state.fighters:
                w_fighter = self.game_state.fighters[winner_id]
                rank = self._get_fighter_division_rank(w_fighter)
                if rank:
                    winner_rank = f"#{rank}"
            
            if not loser_rank and loser_id and loser_id in self.game_state.fighters:
                l_fighter = self.game_state.fighters[loser_id]
                rank = self._get_fighter_division_rank(l_fighter)
                if rank:
                    loser_rank = f"#{rank}"
            
            # Also detect if loser WAS champion before this fight (title change)
            # Check if the loser's name in fight data had [C] tag
            if "[C]" in fight.get("loser_name", "") or "[C]" in loser_name:
                loser_was_champ = True
            
            # ===== TIER 1: CHAMPION NEWS (highest priority) =====
            
            # Title change - someone beat the champion!
            if loser_was_champ and not winner_was_champ:
                tier1_headlines.append(
                    colored(f"[T] NEW CHAMPION! {winner_name} dethrones {loser_name} for {div} title ({method} R{round_num})", Colors.GOLD)
                )
            # Title defense
            elif winner_was_champ:
                tier1_headlines.append(
                    colored(f"[T] {winner_name} defends {div} title vs {loser_rank} {loser_name} ({method})", Colors.CYAN)
                )
            # Explicit title fight (is_title flag set)
            elif is_title and loser_rank == "[C]":
                tier1_headlines.append(
                    colored(f"[T] NEW CHAMPION! {winner_name} claims {div} title ({method} R{round_num})", Colors.GOLD)
                )
            elif is_title:
                tier1_headlines.append(
                    colored(f"[T] TITLE FIGHT: {winner_name} defeats {loser_name} for {div} gold", Colors.CYAN)
                )
            
            # ===== TIER 2: UPSETS, RIVALRIES, WATCHLIST =====
            
            # Rivalry result
            if winner_id in active_rivalries or loser_id in active_rivalries:
                rivalry = active_rivalries.get(winner_id) or active_rivalries.get(loser_id)
                if rivalry:
                    tier2_headlines.append(
                        colored(f"[T] RIVALRY: {winner_name} settles the score vs {loser_name}!", Colors.ORANGE)
                    )
            
            # Watchlist fighter result
            if winner_id in watchlist_ids:
                tier2_headlines.append(
                    colored(f"[>] WATCHLIST: {winner_name} wins via {method} R{round_num}", Colors.YELLOW)
                )
            elif loser_id in watchlist_ids:
                tier2_headlines.append(
                    colored(f"[>] WATCHLIST: {loser_name} falls to {winner_name} ({method})", Colors.YELLOW)
                )
            
            # Upset (lower ranked beats higher ranked by 5+ spots)
            if winner_rank and loser_rank and winner_rank != "[C]" and loser_rank != "[C]":
                try:
                    w_num = int(winner_rank.replace("#", ""))
                    l_num = int(loser_rank.replace("#", ""))
                    if w_num > l_num + 4:
                        tier2_headlines.append(
                            colored(f"[!] UPSET! {winner_rank} {div} {winner_name} stuns {loser_rank} {loser_name}!", Colors.ORANGE)
                        )
                    elif l_num <= 5 and w_num > 10:
                        # Unranked/low ranked beats top 5
                        tier2_headlines.append(
                            colored(f"[!] SHOCKER! {winner_name} upsets {loser_rank} {div} {loser_name}!", Colors.ORANGE)
                        )
                except:
                    pass
            
            # ===== TIER 3: NOTABLE FINISHES =====
            
            # Top 5 fighter news (wins or losses)
            if winner_rank and winner_rank != "[C]":
                try:
                    w_num = int(winner_rank.replace("#", ""))
                    if w_num <= 5:
                        finish_desc = f"{method} R{round_num}" if method in ["KO", "TKO", "SUB"] else method
                        loser_display = f"{loser_rank} {loser_name}" if loser_rank else loser_name
                        tier3_headlines.append(
                            colored(f"{winner_rank} {div} {winner_name} defeats {loser_display} ({finish_desc})", Colors.CYAN)
                        )
                except:
                    pass
            
            # Big finish (R1 KO/SUB) - only if not already covered above
            if round_num == 1 and method in ["KO", "TKO", "SUB"]:
                # Skip if already in higher tier
                if not any(winner_name in h for h in tier1_headlines + tier2_headlines):
                    finish_type = "KO" if "KO" in method else "submission"
                    rank_str = f"{winner_rank} {div} " if winner_rank else f"{div} "
                    loser_display = f"{loser_rank} {loser_name}" if loser_rank else loser_name
                    tier3_headlines.append(
                        colored(f"[!] {rank_str}{winner_name} with a R1 {finish_type} over {loser_display}!", Colors.RED)
                    )
        
        # Combine headlines by priority, deduplicate by fighter name
        all_headlines = tier1_headlines + tier2_headlines + tier3_headlines
        
        # Remove duplicates (same fighter appearing multiple times)
        seen_fighters = set()
        unique_headlines = []
        for headline in all_headlines:
            # Extract first fighter name from headline for dedup
            skip = False
            for seen in seen_fighters:
                if seen in headline:
                    skip = True
                    break
            if not skip:
                unique_headlines.append(headline)
                # Add winner name to seen (rough extraction)
                for fight in week_results:
                    if fight.get("winner_name", "") in headline:
                        seen_fighters.add(fight.get("winner_name", ""))
                        break
        
        return unique_headlines[:5]  # Top 5 headlines
    
    def _get_ranking_changes(self, week_results: List[Dict]) -> List[str]:
        """Get ranking changes from this week's fights."""
        changes = []
        seen_fighters = set()  # Avoid duplicates
        
        for fight in week_results:
            # Get actual ranking changes stored on the fight result
            ranking_changes = fight.get("ranking_changes", [])
            
            for change in ranking_changes:
                fighter_id = change.get("fighter_id")
                if fighter_id in seen_fighters:
                    continue
                seen_fighters.add(fighter_id)
                
                fighter_name = change.get("fighter_name", "Fighter")
                old_rank = change.get("old_rank")
                new_rank = change.get("new_rank")
                is_promotion = change.get("is_promotion", False)
                positions_moved = change.get("positions_moved", 0)
                reason = change.get("reason", "")
                
                weight_class = fight.get("weight_class", "")
                div = self._get_division_abbrev(weight_class)
                
                # Format the change message
                if new_rank == 0:  # Champion
                    changes.append(f"{colored('+', Colors.GREEN)} {fighter_name} now {colored('[C]', Colors.GOLD)} {div}")
                elif is_promotion:
                    if old_rank is None or old_rank > 15:
                        changes.append(f"{colored('+', Colors.GREEN)} {fighter_name} enters rankings at #{new_rank} {div}")
                    elif positions_moved >= 3:
                        changes.append(f"{colored('+', Colors.GREEN)} {fighter_name} jumps to #{new_rank} {div} (+{positions_moved})")
                    else:
                        changes.append(f"{colored('+', Colors.GREEN)} {fighter_name} rises to #{new_rank} {div}")
                else:  # Demotion
                    if new_rank is None or new_rank > 15:
                        changes.append(f"{colored('-', Colors.RED)} {fighter_name} falls out of {div} rankings")
                    elif old_rank == 0:  # Lost title
                        changes.append(f"{colored('-', Colors.RED)} {fighter_name} loses {div} title, now #{new_rank}")
                    elif positions_moved >= 3:
                        changes.append(f"{colored('-', Colors.RED)} {fighter_name} drops to #{new_rank} {div} (-{positions_moved})")
                    else:
                        changes.append(f"{colored('-', Colors.RED)} {fighter_name} falls to #{new_rank} {div}")
        
        # Sort: promotions first, then demotions
        promotions = [c for c in changes if '+' in c[:20]]
        demotions = [c for c in changes if '-' in c[:20]]
        
        return promotions + demotions
    
    def _get_major_injuries(self) -> List[str]:
        """Get major injuries (4+ weeks) for display."""
        injuries = []
        
        if not INJURY_AVAILABLE or not self._injury_system:
            return injuries
        
        try:
            player_camp = self.game_state.get_player_camp()
            if not player_camp:
                return injuries
            
            for fighter_id, full_data in self.fighter_data.items():
                if full_data.camp_id != player_camp.camp_id:
                    continue
                
                injury = self._injury_system.get_worst_injury(fighter_id)
                if injury and injury.weeks_remaining >= 4:
                    injuries.append(f"* {full_data.name}: {injury.injury_type} ({injury.weeks_remaining} wks)")
        except:
            pass
        
        return injuries
    
    def _get_upcoming_fights(self) -> List[str]:
        """Get preview of next week's fights."""
        upcoming = []
        
        # Helper to get rank string
        def get_rank_str(fighter_id: str) -> str:
            if not fighter_id or fighter_id not in self.game_state.fighters:
                return ""
            f = self.game_state.fighters[fighter_id]
            if self._is_division_champion(f):
                return "[C]"
            rank = self._get_fighter_division_rank(f)
            if rank:
                return f"#{rank}"
            return ""  # Truly unranked (0-0 record)
        
        # Check player scheduled fights
        for fight in self.player_scheduled_fights:
            weeks = fight.get("weeks_until", 0)
            if 1 <= weeks <= 2:
                f1 = fight.get("fighter1_name", "Fighter")
                f2 = fight.get("fighter2_name", "Opponent")
                wc = self._get_division_abbrev(fight.get("weight_class", ""))
                is_title = fight.get("is_title_fight", False)
                
                f1_rank = get_rank_str(fight.get("fighter1_id"))
                f2_rank = get_rank_str(fight.get("fighter2_id"))
                
                if is_title:
                    upcoming.insert(0, colored(f"TITLE: {f1_rank} {wc} {f1} vs {f2_rank} {f2}", Colors.GOLD))
                else:
                    upcoming.append(f"* {f1_rank} {wc} {f1} vs {f2_rank} {f2}")
        
        # Check AI scheduled fights for titles
        for fight in self.ai_scheduled_fights:
            weeks = fight.get("weeks_until", 0)
            if 1 <= weeks <= 2:
                f1 = fight.get("fighter1_name", "Fighter")
                f2 = fight.get("fighter2_name", "Opponent")
                wc = self._get_division_abbrev(fight.get("weight_class", ""))
                is_title = fight.get("is_title_fight", False)
                
                f1_rank = get_rank_str(fight.get("fighter1_id"))
                f2_rank = get_rank_str(fight.get("fighter2_id"))
                
                if is_title:
                    upcoming.insert(0, colored(f"TITLE: {f1_rank} {wc} {f1} vs {f2_rank} {f2}", Colors.GOLD))
                elif len(upcoming) < 6:  # Limit non-title
                    upcoming.append(f"* {f1_rank} {wc} {f1} vs {f2_rank} {f2}")
        
        return upcoming[:6]
        
        return upcoming[:6]
    
    def _clean_garbled_text(self, text: str) -> str:
        """Remove garbled unicode/emoji characters from text, preserving ANSI color codes."""
        clean = text
        result = []
        i = 0
        while i < len(clean):
            c = clean[i]
            code = ord(c)
            
            # Preserve ANSI escape sequences (ESC [ ... m)
            if code == 27 and i + 1 < len(clean) and clean[i + 1] == '[':
                # Found start of ANSI sequence, copy until 'm'
                result.append(c)
                i += 1
                while i < len(clean):
                    result.append(clean[i])
                    if clean[i] == 'm':
                        i += 1
                        break
                    i += 1
                continue
            
            # Keep printable ASCII characters
            if 32 <= code <= 126:
                result.append(c)
            elif c == ' ':
                result.append(' ')
            i += 1
        
        clean = ''.join(result)
        # Clean up extra whitespace
        while '  ' in clean:
            clean = clean.replace('  ', ' ')
        return clean.strip()

    def _display_fight_result_card(self, fight: dict) -> None:
        """Display a single fight result in card format with inline rank movements."""
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
        
        # Get PRE-FIGHT ranks for movement arrows
        winner_pre_rank = fight.get("winner_pre_rank", "")
        loser_pre_rank = fight.get("loser_pre_rank", "")
        
        # Get current (POST-FIGHT) data - this is what we display
        winner_data = self.game_state.fighters.get(winner_id)
        loser_data = self.game_state.fighters.get(loser_id)
        
        # POST-FIGHT records (current state after fight is processed)
        winner_record = f"({winner_data.wins}-{winner_data.losses})" if winner_data else ""
        loser_record = f"({loser_data.wins}-{loser_data.losses})" if loser_data else ""
        
        # POST-FIGHT rankings (current state - new champion shows [C], etc.)
        winner_rank = ""
        loser_rank = ""
        winner_rank_num = 999
        loser_rank_num = 999
        
        if winner_data:
            if self._is_division_champion(winner_data):
                winner_rank = "[C]"
                winner_rank_num = 0
            else:
                rank = self._get_fighter_division_rank(winner_data)
                if rank:
                    winner_rank = f"#{rank}"
                    winner_rank_num = rank
        
        if loser_data:
            if self._is_division_champion(loser_data):
                loser_rank = "[C]"
                loser_rank_num = 0
            else:
                rank = self._get_fighter_division_rank(loser_data)
                if rank:
                    loser_rank = f"#{rank}"
                    loser_rank_num = rank
        
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
        
        # =====================================================================
        # INLINE RANK MOVEMENT ARROWS - THE DOPAMINE HIT
        # =====================================================================
        movement_str = ""
        
        # Use PRE-FIGHT ranks for movement comparison
        # (we're showing where they WERE vs where they ARE now)
        loser_was_champ = "[C]" in str(loser_pre_rank)
        winner_was_champ = "[C]" in str(winner_pre_rank)
        
        # Parse pre-fight rank numbers for upset detection
        winner_pre_rank_num = 999
        loser_pre_rank_num = 999
        try:
            if winner_pre_rank and "#" in str(winner_pre_rank):
                winner_pre_rank_num = int(str(winner_pre_rank).replace("#", ""))
            elif "[C]" in str(winner_pre_rank):
                winner_pre_rank_num = 0
        except:
            pass
        try:
            if loser_pre_rank and "#" in str(loser_pre_rank):
                loser_pre_rank_num = int(str(loser_pre_rank).replace("#", ""))
            elif "[C]" in str(loser_pre_rank):
                loser_pre_rank_num = 0
        except:
            pass
        
        # Title change - NEW CHAMPION! (challenger beat the champion)
        if is_title and loser_was_champ and not winner_was_champ:
            movement_str = colored(" ^ AND NEW!", Colors.GOLD)
        # Title defense (champion beat the challenger)
        elif is_title and winner_was_champ:
            movement_str = colored(" ^ AND STILL!", Colors.CYAN)
        # Fallback for title fights where we can't determine
        elif is_title:
            # Check post-fight state - if winner is now champ, it was a title change
            if winner_rank == "[C]":
                movement_str = colored(" ^ AND NEW!", Colors.GOLD)
            else:
                movement_str = colored(" ^ [TITLE]", Colors.GOLD)
        # Upset detection (lower ranked beat higher ranked by 4+ spots) - use PRE-FIGHT ranks
        elif winner_pre_rank_num > 0 and loser_pre_rank_num > 0 and winner_pre_rank_num > loser_pre_rank_num + 3:
            movement_str = colored(f" ^ [UPSET! ^#{loser_pre_rank_num}]", Colors.ORANGE)
        # Big climb (beat top 5 when outside top 5) - use PRE-FIGHT ranks
        elif loser_pre_rank_num > 0 and loser_pre_rank_num <= 5 and winner_pre_rank_num > 5:
            movement_str = colored(f" ^ [^ TOP 5!]", Colors.GREEN)
        # Regular ranked win over another ranked fighter - use PRE-FIGHT ranks
        elif winner_pre_rank_num > 0 and loser_pre_rank_num > 0 and loser_pre_rank_num < winner_pre_rank_num:
            movement_str = colored(f" ^ [^#{loser_pre_rank_num}]", Colors.GREEN)
        
        # Build the line
        finish_marker = colored("*", Colors.GOLD) if is_finish else " "
        
        line_parts = [f"  {finish_marker}"]
        line_parts.append(colored(f"[{div_abbrev}]", Colors.CYAN))
        
        if position_tag:
            line_parts.append(position_tag)
        
        line_parts.append(f"{winner_str} {winner_record}")
        line_parts.append(method_str)
        line_parts.append(f"{loser_str} {loser_record}")
        
        # Add movement arrow at the end
        if movement_str:
            line_parts.append(movement_str)
        
        print(" ".join(line_parts))
        
        # Show controversy if this was a controversial decision
        is_controversial = fight.get("is_controversial", False)
        controversy_reason = fight.get("controversy_reason", "")
        if is_controversial and controversy_reason and not is_finish:
            print(f"       {colored('!', Colors.YELLOW)} {colored(controversy_reason, Colors.YELLOW)}")
    
    def _get_fighter_rank_num(self, fighter) -> str:
        """Get rank number string like #5 or [C]. Uses weighted ELO-lite."""
        if not fighter:
            return ""
        
        if self._is_division_champion(fighter):
            return colored("[C]", Colors.GOLD)
        
        # Use weighted ELO-lite (single source of truth)
        rank = self._get_fighter_rank_from_weighted(fighter)
        
        if rank is None:
            return ""  # Unranked
        elif rank == 0:
            return colored("[C]", Colors.GOLD)
        elif rank <= 15:
            return f"#{rank}"
        else:
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
        """Display the full round-by-round commentary with smart pagination.
        
        Pauses naturally at round endings instead of arbitrary line counts.
        """
        clear_screen()
        print_header("FULL FIGHT COMMENTARY")
        
        print(f"  {fight.fighter1_name} vs {fight.fighter2_name}")
        print()
        print_divider()
        print()
        
        commentary = fight.full_commentary
        if not commentary:
            print("  No detailed commentary available.")
            pause()
            return
        
        # full_commentary is now a List[str], not a string
        if isinstance(commentary, list):
            lines = commentary
        else:
            lines = commentary.split('\n')
        
        # Patterns that indicate end of round (pause after these)
        # NOTE: "[round X:" patterns were REMOVED - those are round SUMMARIES
        # that appear at the START of the next round, not round-ending signals
        round_end_patterns = [
            "round 1 in the books",
            "round 2 in the books",
            "round 3 in the books",
            "round 4 in the books",
            "round 5 in the books",
            "end round 1",
            "end round 2",
            "end round 3",
            "end round 4",
            "end round 5",
            "the horn sounds to end round",
        ]
        
        # Patterns that indicate fight is over (no pause needed, just finish)
        fight_end_patterns = [
            "the referee stops it",
            "referee stops the fight",
            "it's all over",
            "taps out",
            "verbal submission",
            "that's it!",
        ]
        
        # Track which round we're in for the prompt
        current_round = 1
        line_buffer = []
        fight_ended = False
        
        def print_buffered_lines():
            """Print accumulated lines with word wrapping."""
            for line in line_buffer:
                if len(line) > 66:
                    words = line.split()
                    current = ""
                    for word in words:
                        if len(current) + len(word) + 1 <= 66:
                            current += (" " if current else "") + word
                        else:
                            print(f"  {current}")
                            current = word
                    if current:
                        print(f"  {current}")
                else:
                    print(f"  {line}")
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            line_buffer.append(line)
            
            # Check for fight ending
            if any(pattern in line_lower for pattern in fight_end_patterns):
                fight_ended = True
            
            # Check for round start to track current round
            if "here we go, round" in line_lower or "round" in line_lower and "!" in line_lower:
                for r in range(1, 6):
                    if f"round {r}" in line_lower:
                        current_round = r
                        break
            
            # Check for round ending - pause here
            is_round_end = any(pattern in line_lower for pattern in round_end_patterns)
            
            # NOTE: The "[round X:" pattern check was REMOVED here
            # That pattern is a round SUMMARY that appears at the START of the next round
            # Checking for it here was causing double-pagination and wrong round numbers
            
            if is_round_end and not fight_ended:
                # Print what we have so far
                print_buffered_lines()
                line_buffer = []
                
                # Show round transition prompt
                print()
                print(f"  {colored('-' * 50, Colors.DIM)}")
                prompt = f"  -- End of Round {current_round}. Press Enter for Round {current_round + 1}, 'q' to quit -- "
                choice = get_input(prompt)
                if choice.lower() == 'q':
                    return
                
                # Clear and show header for next round
                clear_screen()
                print_header("FULL FIGHT COMMENTARY")
                print(f"  {fight.fighter1_name} vs {fight.fighter2_name}")
                print(f"  {colored(f'Round {current_round + 1}', Colors.CYAN)}")
                print()
                print_divider()
                print()
                
                current_round += 1
            
            # Safety: if we've accumulated 30+ lines without a round break, page it
            elif len(line_buffer) >= 30:
                print_buffered_lines()
                line_buffer = []
                print()
                choice = get_input("  -- Press Enter for more, 'q' to quit -- ")
                if choice.lower() == 'q':
                    return
                print()
        
        # Print any remaining lines
        if line_buffer:
            print_buffered_lines()
        
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
            if self._is_division_champion(f):
                score += 50
            return max(0, score)
        
        scored = [(f, goat_score(f)) for f in all_fighters if f.wins + f.losses > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        print("  The greatest fighters in DFC history:")
        print()
        
        medals = ["[*]", "", "[*]"] + ["  "] * 20
        
        for i, (fighter, score) in enumerate(scored[:20], 1):
            medal = medals[min(i - 1, len(medals) - 1)]
            champ_tag = colored(" [C]", Colors.GOLD) if self._is_division_champion(fighter) else ""
            
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
        """Show current champions with interactive belt history"""
        
        divisions = list(self.game_state.divisions.keys())
        
        while True:
            clear_screen()
            print_header("CHAMPIONS")
            
            print("  Current DFC World Champions:")
            print()
            print(f"  {'#':<4} {'DIVISION':<18} {'CHAMPION':<22} {'RECORD':<10} {'DEFENSES'}")
            print(f"  {'-' * 70}")
            
            champions_list = []
            for i, div_name in enumerate(divisions, 1):
                # Use division state as source of truth
                div_state = self.game_state.divisions.get(div_name)
                champion = None
                defenses = 0
                
                if div_state and div_state.champion_id:
                    champion = self.game_state.fighters.get(div_state.champion_id)
                    
                    # Get defenses from belt history if available
                    if self._belt_history:
                        reign = self._belt_history.get_current_reign(div_name)
                        if reign:
                            defenses = reign.successful_defenses
                
                if champion:
                    record = f"{champion.wins}-{champion.losses}"
                    defense_str = f"{defenses}" if defenses > 0 else "-"
                    print(f"  [{i}] {div_name:<18} {colored(champion.name[:20], Colors.GOLD):<30} {record:<10} {defense_str}")
                    champions_list.append((div_name, champion, defenses))
                else:
                    print(f"  [{i}] {div_name:<18} {colored('VACANT', Colors.DIM):<22} -")
                    champions_list.append((div_name, None, 0))
            
            print()
            print(f"  {colored('[#] Select division to view belt history', Colors.CYAN)}")
            print(f"  [0] Back")
            print()
            
            choice = get_input("Choose: ")
            
            if choice == "0":
                return
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(divisions):
                    self._show_belt_history(divisions[idx])
            except ValueError:
                pass
    
    def _show_belt_history(self, weight_class: str) -> None:
        """Show detailed belt history for a division"""
        
        while True:
            clear_screen()
            print_header(f"{weight_class.upper()} CHAMPIONSHIP HISTORY")
            
            # Get current champion info
            div_state = self.game_state.divisions.get(weight_class)
            current_champion = None
            if div_state and div_state.champion_id:
                current_champion = self.game_state.fighters.get(div_state.champion_id)
            
            # Display current champion prominently
            if current_champion:
                full_data = self.fighter_data.get(current_champion.fighter_id)
                record = f"{current_champion.wins}-{current_champion.losses}"
                
                print()
                print(f"  {colored('★ CURRENT CHAMPION ★', Colors.GOLD)}")
                print(f"  {colored(current_champion.name, Colors.GOLD)} ({record})")
                
                if self._belt_history:
                    reign = self._belt_history.get_current_reign(weight_class)
                    if reign:
                        print(f"  Defenses: {reign.successful_defenses}")
                        if reign.won_from_name:
                            print(f"  Won title from: {reign.won_from_name} ({reign.won_method})")
                        else:
                            print(f"  {colored('Inaugural Champion', Colors.CYAN)}")
                        print(f"  At: {reign.won_event}")
            else:
                print()
                print(f"  {colored('TITLE VACANT', Colors.DIM)}")
            
            print()
            
            # Show belt lineage
            if self._belt_history:
                reigns = self._belt_history.get_all_reigns(weight_class)
                
                if reigns:
                    print(f"  {colored('CHAMPIONSHIP LINEAGE', Colors.HIGHLIGHT)}")
                    print(f"  {'-' * 60}")
                    print()
                    
                    # Show in reverse chronological order (most recent first)
                    for i, reign in enumerate(reversed(reigns)):
                        reign_num = len(reigns) - i
                        
                        # Format reign info
                        if reign.is_active:
                            status = colored("[CURRENT]", Colors.GOLD)
                        else:
                            status = ""
                        
                        # How they won
                        if reign.won_from_name:
                            won_info = f"def. {reign.won_from_name}"
                        else:
                            won_info = colored("Inaugural", Colors.CYAN)
                        
                        print(f"  {reign_num}. {colored(reign.champion_name, Colors.HIGHLIGHT)} {status}")
                        print(f"     Won: {reign.won_event} - {won_info}")
                        if reign.won_method and reign.won_from_name:
                            print(f"     Method: {reign.won_method}")
                        
                        if reign.successful_defenses > 0:
                            print(f"     Defenses: {colored(str(reign.successful_defenses), Colors.GREEN)}")
                        
                        if not reign.is_active and reign.lost_to_name:
                            print(f"     Lost: {reign.lost_event} to {reign.lost_to_name} ({reign.lost_method})")
                        
                        print()
                    
                    # Stats summary
                    print(f"  {'-' * 60}")
                    print(f"  Total title changes: {len(reigns)}")
                    
                    # Most defenses
                    most_defenses = self._belt_history.get_most_defenses(weight_class)
                    if most_defenses and most_defenses.successful_defenses > 0:
                        print(f"  Most defenses: {most_defenses.champion_name} ({most_defenses.successful_defenses})")
                else:
                    print(f"  {colored('No championship history available', Colors.DIM)}")
            else:
                print(f"  {colored('Belt history not available', Colors.DIM)}")
            
            print()
            
            # Options
            if current_champion:
                print(f"  [V] View champion profile")
            print(f"  [0] Back")
            print()
            
            choice = get_input("Choose: ").lower()
            
            if choice == "0":
                return
            elif choice == "v" and current_champion:
                self.show_fighter_details(current_champion)
    
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
                fighter_rec = self.game_state.fighters.get(fighter.fighter_id)
                champ_str = colored(" [C]", Colors.GOLD) if fighter_rec and self._is_division_champion(fighter_rec) else ""
                
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
        
        eligible, unmet = self._economy_manager.check_upgrade_eligibility(
            camp_id=player_camp.camp_id,
            target_tier=info['next_tier'],
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
                player_marker = colored(" [YOUR FIGHTER]", Colors.GOLD) if has_player else ""
                
                # Check for title fights
                title_fights = [f for f in event["fights"] if f.get("is_title_fight")]
                title_marker = ""
                if title_fights:
                    title_count = len(title_fights)
                    if title_count > 1:
                        title_marker = colored(f" [{title_count} TITLE FIGHTS]", Colors.GOLD)
                    else:
                        title_marker = colored(" [TITLE FIGHT]", Colors.GOLD)
                
                # =================================================================
                # DOPAMINE: STAKES INDICATOR
                # =================================================================
                stakes_str = ""
                if has_player:
                    player_fights = [f for f in event["fights"] if f.get("is_player_fight")]
                    for pf in player_fights:
                        f1_id = pf.get("fighter1_id")
                        if f1_id and f1_id in self.game_state.fighters:
                            fighter = self.game_state.fighters[f1_id]
                            f_data = self.fighter_data.get(f1_id)
                            
                            # Title shot
                            if pf.get("is_title_fight") and not self._is_division_champion(fighter):
                                stakes_str = colored(" [*] TITLE SHOT!", Colors.GOLD)
                            # Title defense
                            elif pf.get("is_title_fight") and self._is_division_champion(fighter):
                                stakes_str = colored(" [T] TITLE DEFENSE", Colors.CYAN)
                            # Win streak on the line
                            elif f_data and f_data.win_streak >= 5:
                                stakes_str = colored(f" [!] {f_data.win_streak}-FIGHT STREAK ON THE LINE", Colors.ORANGE)
                            # Must win after losses
                            elif f_data and f_data.lose_streak >= 2:
                                stakes_str = colored(" [!] MUST WIN!", Colors.RED)
                
                print(f"  [{i}] {event['name']}{player_marker}{title_marker}")
                print(f"      {event['fight_count']} fights | {timing}{stakes_str}")
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
        """Show full card for an upcoming event with UFC-style card positions"""
        while True:
            clear_screen()
            
            weeks = event["weeks"]
            timing = "THIS WEEK" if weeks <= 1 else f"In {weeks} weeks"
            
            print_header(event["name"])
            print(f"  {timing}")
            print()
            
            fights = event["fights"]
            
            # Group fights by card slot
            card_slots = {
                "main_event": [],
                "co_main": [],
                "main_card": [],
                "prelim": [],
                "early_prelim": [],
            }
            
            for fight in fights:
                slot = fight.get("card_slot", "prelim")
                # Handle legacy fights without card_slot
                if not slot or slot not in card_slots:
                    if fight.get("is_title_fight") or fight.get("is_main_event"):
                        slot = "main_event"
                    else:
                        slot = "prelim"
                card_slots[slot].append(fight)
            
            # Sort within each slot by combined rating
            for slot in card_slots:
                card_slots[slot].sort(key=lambda f: (
                    self.fighter_data.get(f.get("fighter1_id"), type('', (), {"overall_rating": 50})()).overall_rating +
                    self.fighter_data.get(f.get("fighter2_id"), type('', (), {"overall_rating": 50})()).overall_rating
                ), reverse=True)
            
            # Display by card section
            all_fights_indexed = []
            fight_index = 1
            
            # MAIN EVENT
            if card_slots["main_event"]:
                print(colored("  === MAIN EVENT ===", Colors.GOLD))
                for fight in card_slots["main_event"]:
                    self._display_card_fight(fight, fight_index)
                    all_fights_indexed.append(fight)
                    fight_index += 1
                print()
            
            # CO-MAIN
            if card_slots["co_main"]:
                print(colored("  === CO-MAIN EVENT ===", Colors.ORANGE))
                for fight in card_slots["co_main"]:
                    self._display_card_fight(fight, fight_index)
                    all_fights_indexed.append(fight)
                    fight_index += 1
                print()
            
            # MAIN CARD
            if card_slots["main_card"]:
                print(colored("  === MAIN CARD ===", Colors.CYAN))
                for fight in card_slots["main_card"]:
                    self._display_card_fight(fight, fight_index)
                    all_fights_indexed.append(fight)
                    fight_index += 1
                print()
            
            # PRELIMS
            if card_slots["prelim"]:
                print(f"  === PRELIMS ===")
                for fight in card_slots["prelim"]:
                    self._display_card_fight(fight, fight_index)
                    all_fights_indexed.append(fight)
                    fight_index += 1
                print()
            
            # EARLY PRELIMS
            if card_slots["early_prelim"]:
                print(colored("  === EARLY PRELIMS ===", Colors.DIM))
                for fight in card_slots["early_prelim"]:
                    self._display_card_fight(fight, fight_index)
                    all_fights_indexed.append(fight)
                    fight_index += 1
                print()
            
            print(f"  [0] Back")
            print()
            print("  Select a fight to view fighter details")
            
            choice = get_input("> ")
            
            if choice == "0":
                return
            
            try:
                index = int(choice)
                if 1 <= index <= len(all_fights_indexed):
                    fight = all_fights_indexed[index - 1]
                    self.show_matchup_preview(fight)
            except ValueError:
                pass
    
    def _display_card_fight(self, fight: Dict[str, Any], index: int) -> None:
        """Display a single fight on the card"""
        f1_name = fight.get("fighter1_name", "TBD")
        f2_name = fight.get("fighter2_name", "TBD")
        wc = fight.get("weight_class", "")
        
        # Get records and ranks
        f1_id = fight.get("fighter1_id")
        f2_id = fight.get("fighter2_id")
        f1_data = self.fighter_data.get(f1_id)
        f2_data = self.fighter_data.get(f2_id)
        f1_fighter = self.game_state.fighters.get(f1_id)
        f2_fighter = self.game_state.fighters.get(f2_id)
        
        f1_rec = format_record(f1_data.wins, f1_data.losses) if f1_data else "0-0"
        f2_rec = format_record(f2_data.wins, f2_data.losses) if f2_data else "0-0"
        
        # Get ranks
        f1_rank = ""
        f2_rank = ""
        if f1_fighter:
            if self._is_division_champion(f1_fighter):
                f1_rank = "[C] "
            else:
                rank = self._get_fighter_division_rank(f1_fighter)
                if rank and rank <= 15:
                    f1_rank = f"#{rank} "
        if f2_fighter:
            if self._is_division_champion(f2_fighter):
                f2_rank = "[C] "
            else:
                rank = self._get_fighter_division_rank(f2_fighter)
                if rank and rank <= 15:
                    f2_rank = f"#{rank} "
        
        # Tags
        tags = []
        if fight.get("is_title_fight"):
            tags.append(colored("[TITLE]", Colors.GOLD))
        if fight.get("is_player_fight"):
            tags.append(colored("[YOUR FIGHT]", Colors.CYAN))
        
        tag_str = " ".join(tags)
        if tag_str:
            tag_str = " " + tag_str
        
        # Format: [1] #3 John Smith (5-1) vs #5 Mike Jones (4-2) [TITLE]
        print(f"  [{index}] {f1_rank}{f1_name} ({f1_rec}) vs {f2_rank}{f2_name} ({f2_rec}){tag_str}")
        print(f"      {wc}")
    
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
        f1_rec = self.game_state.fighters.get(f1_data.fighter_id)
        if f1_rec and self._is_division_champion(f1_rec):
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
        f2_rec = self.game_state.fighters.get(f2_data.fighter_id)
        if f2_rec and self._is_division_champion(f2_rec):
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
        print(compare_stat("Takedowns", f1_data.takedowns, f2_data.takedowns))
        print(compare_stat("Submissions", f1_data.submissions, f2_data.submissions))
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
        """Show rankings menu with divisions, P4P, and GOAT options."""
        while True:
            clear_screen()
            print_header("RANKINGS & RECORDS")
            
            print(f"  {colored('DIVISION RANKINGS', Colors.CYAN)}")
            print()
            
            divisions = list(self.game_state.divisions.keys())
            
            for i, div in enumerate(divisions, 1):
                div_state = self.game_state.divisions.get(div)
                abbrev = self._get_division_abbrev(div)
                if div_state and div_state.champion_id:
                    champ = self.game_state.fighters.get(div_state.champion_id)
                    champ_name = champ.name if champ else "Unknown"
                    champ_record = f"({champ.wins}-{champ.losses})" if champ else ""
                    print(f"  [{i}] {abbrev:>4} {colored('[C]', Colors.GOLD)} {champ_name} {champ_record}")
                else:
                    print(f"  [{i}] {abbrev:>4} {colored('VACANT', Colors.DIM)}")
            
            print()
            print(f"  {colored('SPECIAL RANKINGS', Colors.YELLOW)}")
            print(f"  [P] Pound-for-Pound Top 15")
            print(f"  [G] GOAT Rankings (All-Time)")
            print(f"  [R] Record Book (Stats & Records)")
            print()
            print(f"  [B] Browse All Fighters")
            print(f"  [0] Back")
            print()
            
            choice = get_input("Select: ").lower()
            
            if choice == '0':
                return
            elif choice == 'p':
                self._show_p4p_rankings()
            elif choice == 'g':
                self._show_goat_rankings()
            elif choice == 'r':
                self._show_record_book()
            elif choice == 'b':
                self.browse_all_fighters()
            else:
                try:
                    index = int(choice)
                    if 1 <= index <= len(divisions):
                        self.show_division_rankings(divisions[index - 1])
                except ValueError:
                    pass
    
    def _show_p4p_rankings(self) -> None:
        """Show Pound-for-Pound rankings."""
        clear_screen()
        print_header("POUND-FOR-POUND RANKINGS")
        print()
        
        # Calculate P4P based on: rating, champion status, win streak, title defenses
        p4p_scores = []
        
        for fighter in self.game_state.fighters.values():
            if not fighter.is_active:
                continue
            
            score = fighter.overall_rating * 10  # Base from rating
            
            # Champion bonus
            if self._is_division_champion(fighter):
                score += 200
            
            # Get full data for streaks
            f_data = self.fighter_data.get(fighter.fighter_id)
            if f_data:
                # Win streak bonus
                score += f_data.win_streak * 15
                
                # Title defense bonus
                score += f_data.title_defenses * 50
                
                # Record bonus (win percentage)
                total = f_data.wins + f_data.losses
                if total >= 5:
                    win_pct = f_data.wins / total
                    score += int(win_pct * 100)
            
            # Rank bonus
            rank = self._get_fighter_division_rank(fighter)
            if rank:
                score += max(0, (16 - rank) * 5)  # Top ranks get more
            
            p4p_scores.append((fighter, score, f_data))
        
        # Sort by score
        p4p_scores.sort(key=lambda x: -x[1])
        
        player_camp = self.game_state.get_player_camp()
        player_camp_id = player_camp.camp_id if player_camp else None
        
        print(f"  {colored('RK', Colors.DIM):>4}  {'FIGHTER':<22} {'DIV':>4} {'RECORD':>8} {'OVR':>4}")
        print(f"  {'-' * 50}")
        
        for i, (fighter, score, f_data) in enumerate(p4p_scores[:15], 1):
            div = self._get_division_abbrev(fighter.weight_class)
            record = f"{fighter.wins}-{fighter.losses}"
            
            # Highlight player's fighters
            is_yours = getattr(fighter, 'camp_id', None) == player_camp_id
            is_champ = self._is_division_champion(fighter)
            
            if is_champ:
                rank_str = colored(f"#{i}", Colors.GOLD)
                name_str = colored(f"[C] {fighter.name}", Colors.GOLD)
            elif is_yours:
                rank_str = colored(f"#{i}", Colors.GREEN)
                name_str = colored(fighter.name, Colors.GREEN)
            else:
                rank_str = f"#{i}"
                name_str = fighter.name
            
            # Form indicator
            form = ""
            if f_data:
                if f_data.win_streak >= 5:
                    form = colored(" [!]", Colors.GOLD)
                elif f_data.win_streak >= 3:
                    form = colored(" [!]", Colors.ORANGE)
            
            print(f"  {rank_str:>4}  {name_str:<22} {div:>4} {record:>8} {fighter.overall_rating:>4}{form}")
        
        print()
        pause()
    
    def _show_goat_rankings(self) -> None:
        """Show all-time GOAT rankings based on career achievements."""
        clear_screen()
        print_header("GOAT RANKINGS - ALL-TIME GREATS")
        print()
        
        # Calculate GOAT score based on career achievements
        goat_scores = []
        
        for fighter in self.game_state.fighters.values():
            f_data = self.fighter_data.get(fighter.fighter_id)
            if not f_data:
                continue
            
            total_fights = f_data.wins + f_data.losses
            if total_fights < 3:  # Minimum fights to qualify
                continue
            
            score = 0
            
            # Wins (weighted by quality)
            score += f_data.wins * 20
            
            # Finish bonuses
            score += f_data.ko_wins * 10 if hasattr(f_data, 'ko_wins') else 0
            score += f_data.sub_wins * 8 if hasattr(f_data, 'sub_wins') else 0
            
            # Championship achievements
            if self._is_division_champion(fighter):
                score += 300
            score += f_data.title_defenses * 100
            
            # Win streaks
            score += f_data.win_streak * 15
            
            # Longevity bonus
            if total_fights >= 15:
                score += 100
            elif total_fights >= 10:
                score += 50
            
            # Win percentage
            if total_fights >= 5:
                win_pct = f_data.wins / total_fights
                score += int(win_pct * 200)
            
            # Rating bonus
            score += fighter.overall_rating * 2
            
            # Penalty for losses
            score -= f_data.losses * 5
            
            goat_scores.append((fighter, score, f_data))
        
        # Sort by score
        goat_scores.sort(key=lambda x: -x[1])
        
        player_camp = self.game_state.get_player_camp()
        player_camp_id = player_camp.camp_id if player_camp else None
        
        print(f"  {colored('RK', Colors.DIM):>4}  {'FIGHTER':<22} {'DIV':>4} {'RECORD':>8} {'DEF':>4} {'SCORE':>6}")
        print(f"  {'-' * 58}")
        
        for i, (fighter, score, f_data) in enumerate(goat_scores[:20], 1):
            div = self._get_division_abbrev(fighter.weight_class)
            record = f"{fighter.wins}-{fighter.losses}"
            defenses = f_data.title_defenses if f_data else 0
            
            # Highlight
            is_yours = getattr(fighter, 'camp_id', None) == player_camp_id
            is_champ = self._is_division_champion(fighter)
            
            if is_champ:
                rank_str = colored(f"#{i}", Colors.GOLD)
                name_str = colored(f"[C] {fighter.name}", Colors.GOLD)
            elif is_yours:
                rank_str = colored(f"#{i}", Colors.GREEN)
                name_str = colored(fighter.name, Colors.GREEN)
            elif not fighter.is_active:
                rank_str = f"#{i}"
                name_str = colored(f"{fighter.name} (RET)", Colors.DIM)
            else:
                rank_str = f"#{i}"
                name_str = fighter.name
            
            print(f"  {rank_str:>4}  {name_str:<22} {div:>4} {record:>8} {defenses:>4} {score:>6}")
        
        print()
        print(f"  {colored('Score based on: Wins, Finishes, Title Defenses, Win%, Longevity', Colors.DIM)}")
        print()
        pause()
    
    def _show_record_book(self) -> None:
        """Show record book with various stats and records."""
        clear_screen()
        print_header("RECORD BOOK")
        print()
        
        # Collect stats
        fighters_data = [(f, self.fighter_data.get(f.fighter_id)) 
                        for f in self.game_state.fighters.values() 
                        if self.fighter_data.get(f.fighter_id)]
        
        # Most Wins
        print(f"  {colored('MOST WINS', Colors.CYAN)}")
        top_wins = sorted(fighters_data, key=lambda x: -x[0].wins if x[1] else 0)[:5]
        for i, (f, fd) in enumerate(top_wins, 1):
            print(f"    {i}. {f.name} - {f.wins} wins")
        print()
        
        # Most Title Defenses
        print(f"  {colored('MOST TITLE DEFENSES', Colors.GOLD)}")
        top_defenses = sorted(fighters_data, key=lambda x: -x[1].title_defenses if x[1] else 0)[:5]
        for i, (f, fd) in enumerate(top_defenses, 1):
            if fd and fd.title_defenses > 0:
                print(f"    {i}. {f.name} - {fd.title_defenses} defense{'s' if fd.title_defenses != 1 else ''}")
        print()
        
        # Longest Win Streak (Current)
        print(f"  {colored('LONGEST ACTIVE WIN STREAK', Colors.GREEN)}")
        top_streaks = sorted(fighters_data, key=lambda x: -x[1].win_streak if x[1] else 0)[:5]
        for i, (f, fd) in enumerate(top_streaks, 1):
            if fd and fd.win_streak > 0:
                print(f"    {i}. {f.name} - {fd.win_streak} wins")
        print()
        
        # Highest Rated
        print(f"  {colored('HIGHEST RATED FIGHTERS', Colors.YELLOW)}")
        top_rated = sorted(fighters_data, key=lambda x: -x[0].overall_rating)[:5]
        for i, (f, fd) in enumerate(top_rated, 1):
            champ = colored(" [C]", Colors.GOLD) if self._is_division_champion(f) else ""
            print(f"    {i}. {f.name}{champ} - {f.overall_rating} OVR")
        print()
        
        # Current Champions
        print(f"  {colored('CURRENT CHAMPIONS', Colors.GOLD)}")
        for div in self.game_state.divisions.keys():
            div_state = self.game_state.divisions.get(div)
            if div_state and div_state.champion_id:
                champ = self.game_state.fighters.get(div_state.champion_id)
                if champ:
                    champ_data = self.fighter_data.get(champ.fighter_id)
                    defenses = champ_data.title_defenses if champ_data else 0
                    abbrev = self._get_division_abbrev(div)
                    def_str = f" ({defenses} def)" if defenses > 0 else ""
                    print(f"    {abbrev}: {champ.name}{def_str}")
        print()
        
        pause()
    
    def show_division_rankings(self, division: str) -> None:
        """Show rankings for a division using weighted ELO-lite."""
        clear_screen()
        print_header(f"{division.upper()} RANKINGS")
        
        # Get weighted rankings (single source of truth)
        rankings_data = self._get_division_rankings_weighted(division)
        
        player_camp = self.game_state.get_player_camp()
        player_camp_id = player_camp.camp_id if player_camp else None
        
        # Display champion
        champion_entry = None
        contenders = []
        for rank, fid, name in rankings_data:
            fighter = self.game_state.fighters.get(fid)
            if fighter:
                if rank == 0:
                    champion_entry = fighter
                else:
                    contenders.append((rank, fighter))
        
        if champion_entry:
            champ = champion_entry
            champ_data = self.fighter_data.get(champ.fighter_id)
            streak_str = ""
            defenses_str = ""
            
            if champ_data and champ_data.win_streak >= 2:
                streak_str = f" | W{champ_data.win_streak}"
            
            # Get title defenses
            title_defenses = getattr(champ, 'title_defenses', 0) or 0
            if title_defenses > 0:
                defenses_str = f" | {title_defenses} defense{'s' if title_defenses != 1 else ''}"
            
            print(f"  {colored('[C] CHAMPION', Colors.GOLD)}")
            gen_star = "*" if champ_data and getattr(champ_data, 'is_generational', False) else ""
            print(f"      {colored(champ.name, Colors.HIGHLIGHT)}{gen_star} ({format_record_colored(champ.wins, champ.losses)}){streak_str}{defenses_str}")
            print(f"      {champ.overall_rating} OVR")
            print()
        
        print_divider()
        print(f"  {colored('TOP CONTENDERS', Colors.CYAN)}")
        print()
        
        # Display contenders
        for rank, f in contenders[:15]:
            f_data = self.fighter_data.get(f.fighter_id)
            
            # Hot/cold form indicators
            form_icon = ""
            streak_str = ""
            if f_data:
                if f_data.win_streak >= 5:
                    form_icon = colored("[!][!]", Colors.GOLD)
                    streak_str = colored(f" W{f_data.win_streak}", Colors.GREEN)
                elif f_data.win_streak >= 3:
                    form_icon = colored("[!]", Colors.ORANGE)
                    streak_str = colored(f" W{f_data.win_streak}", Colors.GREEN)
                elif f_data.lose_streak >= 3:
                    form_icon = colored("*", Colors.BLUE)
                    streak_str = colored(f" L{f_data.lose_streak}", Colors.RED)
                elif f_data.lose_streak >= 2:
                    streak_str = colored(f" L{f_data.lose_streak}", Colors.RED)
                elif f_data.win_streak >= 2:
                    streak_str = colored(f" W{f_data.win_streak}", Colors.GREEN)
            
            # Highlight YOUR fighters
            is_yours = getattr(f, 'camp_id', None) == player_camp_id
            gen_star = "*" if f_data and getattr(f_data, 'is_generational', False) else ""
            
            if is_yours:
                name_str = colored(f"> {f.name}", Colors.HIGHLIGHT)
                rank_str = colored(f"#{rank:2}", Colors.CYAN)
            else:
                name_str = f.name
                rank_str = f"#{rank:2}"
            
            print(f"  {rank_str}  {name_str}{gen_star} ({format_record_colored(f.wins, f.losses)}) - {f.overall_rating} OVR{streak_str} {form_icon}")
        
        print()
        pause()
    
    def show_amateur_circuit(self) -> None:
        """Show amateur circuit - tournaments, rankings, and signing opportunities."""
        if not AMATEUR_AVAILABLE or not self._amateur_system:
            clear_screen()
            print_header("AMATEUR CIRCUIT")
            print(colored("  Amateur circuit system not available.", Colors.DIM))
            pause()
            return
        
        while True:
            clear_screen()
            print_header("AMATEUR CIRCUIT")
            print()
            print("  The amateur circuit is where future stars are made.")
            print("  Scout regional tournaments, track rising prospects, and sign")
            print("  the next generation of champions to your camp.")
            print()
            
            # Show quick stats
            try:
                total_amateurs = len(self._amateur_system.amateurs) if hasattr(self._amateur_system, 'amateurs') else 0
                eligible_count = len(self._amateur_system.get_eligible_amateurs())
                recent_tourneys = len(self._amateur_system.completed_tournaments[-5:]) if hasattr(self._amateur_system, 'completed_tournaments') else 0
                
                print(f"  {colored('Circuit Overview', Colors.CYAN)}")
                print(f"  {'-' * 40}")
                print(f"  Active Amateurs: {total_amateurs}")
                print(f"  Pro-Ready Prospects: {colored(str(eligible_count), Colors.GREEN)}")
                print(f"  Recent Tournaments: {recent_tourneys}")
                print()
            except:
                pass
            
            options = [
                ("1", "View Regional Rankings"),
                ("2", "Scout Eligible Prospects"),
                ("3", "View Tournament Schedule"),
                ("4", "View Recent Tournaments"),
                ("5", "Sign Amateur Fighter"),
                ("B", "Back to Hub"),
            ]
            
            print_menu(options)
            choice = get_choice(["1", "2", "3", "4", "5", "b"])
            
            if choice == "1":
                self._show_amateur_rankings()
            elif choice == "2":
                self._scout_amateur_prospects()
            elif choice == "3":
                self._show_tournament_schedule()
            elif choice == "4":
                self._show_recent_tournaments()
            elif choice == "5":
                self._sign_amateur_fighter()
            elif choice == "b":
                return
    
    def _show_amateur_rankings(self) -> None:
        """Show amateur rankings by region and weight class."""
        clear_screen()
        print_header("AMATEUR RANKINGS")
        
        if not self._amateur_system:
            print(colored("  Amateur system not available.", Colors.DIM))
            pause()
            return
        
        # Select region
        print("  Select Region:")
        regions = AMATEUR_REGIONS if AMATEUR_AVAILABLE else ["Americas", "Europe", "Asia", "Pacific"]
        for i, region in enumerate(regions, 1):
            print(f"  [{i}] {region}")
        print()
        
        choice = get_input("Region: ")
        try:
            region_idx = int(choice) - 1
            if region_idx < 0 or region_idx >= len(regions):
                return
            selected_region = regions[region_idx]
        except:
            return
        
        # Select weight class
        clear_screen()
        print_header(f"{selected_region.upper()} RANKINGS")
        
        weight_classes = AMATEUR_WEIGHT_CLASSES if AMATEUR_AVAILABLE else [
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight", 
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ]
        
        print("  Select Weight Class:")
        for i, wc in enumerate(weight_classes, 1):
            print(f"  [{i}] {wc}")
        print()
        
        choice = get_input("Weight Class: ")
        try:
            wc_idx = int(choice) - 1
            if wc_idx < 0 or wc_idx >= len(weight_classes):
                return
            selected_wc = weight_classes[wc_idx]
        except:
            return
        
        # Display rankings
        clear_screen()
        print_header(f"{selected_region.upper()} {selected_wc.upper()} RANKINGS")
        
        try:
            rankings_obj = self._amateur_system.get_regional_rankings(selected_region, selected_wc)
            rankings = rankings_obj.rankings if hasattr(rankings_obj, 'rankings') else []
            
            if not rankings:
                print(colored("  No ranked fighters in this division.", Colors.DIM))
            else:
                print(f"  {'Rank':<5} {'Fighter':<25} {'Record':<10} {'Points':<8} {'Age':<5}")
                print(f"  {'-' * 55}")
                
                for i, (fighter_id, points) in enumerate(rankings[:15], 1):
                    # Get fighter data
                    fighter = self._amateur_system.get_amateur(fighter_id)
                    if not fighter:
                        continue
                    
                    name = fighter.name
                    record = f"{fighter.wins}-{fighter.losses}"
                    age = fighter.age
                    
                    # Highlight pro-eligible
                    is_eligible = fighter.is_pro_eligible
                    name_colored = colored(name, Colors.GREEN) if is_eligible else name
                    
                    print(f"  {i:<5} {name_colored:<25} {record:<10} {points:<8} {age:<5}")
                
                print()
                print(f"  {colored('Green = Pro-eligible', Colors.GREEN)}")
        except Exception as e:
            print(colored(f"  Error loading rankings: {e}", Colors.RED))
        
        pause()
    
    def _scout_amateur_prospects(self) -> None:
        """Scout pro-eligible amateur prospects."""
        clear_screen()
        print_header("SCOUT PROSPECTS")
        
        if not self._amateur_system:
            print(colored("  Amateur system not available.", Colors.DIM))
            pause()
            return
        
        # Optional: filter by weight class
        print("  Filter by weight class? (Enter number or press Enter for all)")
        weight_classes = AMATEUR_WEIGHT_CLASSES if AMATEUR_AVAILABLE else [
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight", 
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ]
        
        for i, wc in enumerate(weight_classes, 1):
            print(f"  [{i}] {wc}")
        print()
        
        choice = get_input("Weight Class (or Enter for all): ").strip()
        selected_wc = None
        if choice:
            try:
                wc_idx = int(choice) - 1
                if 0 <= wc_idx < len(weight_classes):
                    selected_wc = weight_classes[wc_idx]
            except:
                pass
        
        # Get eligible prospects
        try:
            prospects = self._amateur_system.get_eligible_amateurs(selected_wc)
            
            if not prospects:
                clear_screen()
                print_header("SCOUT PROSPECTS")
                print(colored("  No pro-eligible prospects found.", Colors.DIM))
                print()
                print("  Fighters become pro-eligible by:")
                print("  * Winning a regional tournament")
                print("  * 8+ fights with 65%+ win rate")
                print("  * Top 5 in regional rankings")
                print("  * National Championship participation")
                print("  * Prodigy Rule: Rating 72+ (immediate)")
                pause()
                return
            
            clear_screen()
            title = f"PRO-ELIGIBLE PROSPECTS"
            if selected_wc:
                title += f" - {selected_wc.upper()}"
            print_header(title)
            
            print(f"  {'#':<3} {'Name':<22} {'Division':<14} {'Record':<8} {'OVR':<5} {'Age':<4} {'Region':<10}")
            print(f"  {'-' * 70}")
            
            for i, prospect in enumerate(prospects[:20], 1):
                name = prospect.name
                division = prospect.weight_class
                record = f"{prospect.wins}-{prospect.losses}"
                ovr = prospect.overall_rating
                age = prospect.age
                region = getattr(prospect, 'region', 'Unknown')
                
                # Color by rating
                if ovr >= 75:
                    ovr_str = colored(str(ovr), Colors.GOLD)
                elif ovr >= 70:
                    ovr_str = colored(str(ovr), Colors.GREEN)
                elif ovr >= 65:
                    ovr_str = colored(str(ovr), Colors.CYAN)
                else:
                    ovr_str = str(ovr)
                
                print(f"  {i:<3} {name:<22} {division:<14} {record:<8} {ovr_str:<5} {age:<4} {region:<10}")
            
            if len(prospects) > 20:
                print(f"\n  ... and {len(prospects) - 20} more prospects")
            
            print()
            print("  Enter number to view prospect details, or B to go back:")
            choice = get_input("Selection: ").strip().lower()
            
            if choice == 'b':
                return
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(prospects):
                    self._view_amateur_prospect(prospects[idx])
            except:
                pass
                
        except Exception as e:
            print(colored(f"  Error: {e}", Colors.RED))
            pause()
    
    def _view_amateur_prospect(self, prospect) -> None:
        """View detailed info about an amateur prospect."""
        clear_screen()
        print_header(f"PROSPECT: {prospect.name.upper()}")
        
        print(f"\n  {colored('BIO', Colors.CYAN)}")
        print(f"  {'-' * 40}")
        print(f"  Age: {prospect.age}")
        print(f"  Weight Class: {prospect.weight_class}")
        print(f"  Region: {getattr(prospect, 'region', 'Unknown')}")
        print(f"  Nationality: {getattr(prospect, 'nationality', 'Unknown')}")
        
        print(f"\n  {colored('RECORD', Colors.CYAN)}")
        print(f"  {'-' * 40}")
        print(f"  Amateur Record: {prospect.wins}-{prospect.losses}")
        ko_wins = getattr(prospect, 'ko_wins', 0)
        sub_wins = getattr(prospect, 'sub_wins', 0)
        print(f"  Finishes: {ko_wins} KO, {sub_wins} SUB")
        
        print(f"\n  {colored('RATINGS', Colors.CYAN)}")
        print(f"  {'-' * 40}")
        print(f"  Overall: {prospect.overall_rating}")
        print(f"  Potential: {getattr(prospect, 'potential', '?')}")
        
        # Show attributes if available
        if hasattr(prospect, 'striking') and prospect.striking:
            print(f"\n  Striking: {prospect.striking}")
            print(f"  Grappling: {getattr(prospect, 'grappling', '?')}")
            print(f"  Cardio: {getattr(prospect, 'cardio', '?')}")
        
        # Eligibility reason
        print(f"\n  {colored('PRO ELIGIBILITY', Colors.GREEN)}")
        print(f"  {'-' * 40}")
        reasons = getattr(prospect, 'eligibility_reasons', [])
        if reasons:
            for reason in reasons:
                print(f"  [OK] {reason}")
        else:
            print("  [OK] Meets eligibility requirements")
        
        print()
        options = [
            ("1", "Sign to Camp"),
            ("B", "Back"),
        ]
        print_menu(options)
        
        choice = get_choice(["1", "b"])
        if choice == "1":
            self._attempt_amateur_signing(prospect)
    
    def _attempt_amateur_signing(self, prospect) -> None:
        """Attempt to sign an amateur prospect."""
        player_camp = self.game_state.get_player_camp()
        if not player_camp:
            print(colored("  No player camp found!", Colors.RED))
            pause()
            return
        
        # Check roster space
        roster_count = sum(1 for f in self.game_state.fighters.values() 
                         if getattr(f, 'camp_id', None) == player_camp.camp_id)
        tier = self._get_camp_tier()
        max_fighters = {"GARAGE": 5, "LOCAL": 10, "REGIONAL": 20, "NATIONAL": 35, "ELITE": 50}.get(tier, 5)
        
        if roster_count >= max_fighters:
            print(colored(f"\n  Roster full! ({roster_count}/{max_fighters})", Colors.RED))
            print("  Release a fighter or upgrade your camp first.")
            pause()
            return
        
        # Confirm signing
        print(f"\n  Sign {prospect.name} to {player_camp.name}?")
        print(f"  They will become a professional fighter on your roster.")
        print()
        
        confirm = get_input("Confirm? (Y/N): ").strip().lower()
        if confirm != 'y':
            print(colored("  Signing cancelled.", Colors.DIM))
            pause()
            return
        
        # Execute signing
        try:
            result = self._amateur_system.sign_amateur(prospect.fighter_id, player_camp.camp_id)
            
            if result:
                print(colored(f"\n  [OK] {prospect.name} signed to {player_camp.name}!", Colors.GREEN))
                print(f"  Welcome to the professional ranks!")
                
                # Add news
                self.news_feed.insert(0, NewsItem(
                    headline=f"{prospect.name} turns pro, signs with {player_camp.name}!",
                    category="signing",
                    week=self.game_state.week_number,
                ))
                
                # Create fighter in game state
                self._create_fighter_from_amateur(prospect, player_camp.camp_id)
            else:
                print(colored("\n  Signing failed - prospect may have signed elsewhere.", Colors.RED))
        except Exception as e:
            print(colored(f"\n  Error: {e}", Colors.RED))
        
        pause()
    
    def _create_fighter_from_amateur(self, amateur, camp_id: str) -> None:
        """Create a professional fighter from an amateur prospect."""
        from core.game_state import Fighter
        
        fighter_id = f"pro_{amateur.fighter_id}"
        
        # Create core fighter
        fighter = Fighter(
            fighter_id=fighter_id,
            name=amateur.name,
            weight_class=amateur.weight_class,
            overall_rating=amateur.overall_rating,
            wins=0,  # Pro record starts at 0
            losses=0,
            is_champion=False,
            is_active=True,
            camp_id=camp_id,
        )
        
        # Add to game state
        self.game_state.fighters[fighter_id] = fighter
        
        # Create full data
        full_data = FighterFullData(
            fighter_id=fighter_id,
            name=amateur.name,
            age=amateur.age,
            weight_class=amateur.weight_class,
            camp_id=camp_id,
            country=getattr(amateur, 'nationality', 'Unknown'),
            wins=0,
            losses=0,
            # Transfer amateur attributes
            boxing=getattr(amateur, 'boxing', 50),
            kicks=getattr(amateur, 'kicks', 50),
            takedowns=getattr(amateur, 'takedowns', 50),
            submissions=getattr(amateur, 'submissions', 50),
            cardio=getattr(amateur, 'cardio', 50),
            strength=getattr(amateur, 'strength', 50),
            speed=getattr(amateur, 'speed', 50),
            chin=getattr(amateur, 'chin', 50),
            potential_ceiling=getattr(amateur, 'potential', 80),
        )
        
        self.fighter_data[fighter_id] = full_data
    
    def _show_tournament_schedule(self) -> None:
        """Show upcoming amateur tournaments."""
        clear_screen()
        print_header("TOURNAMENT SCHEDULE")
        
        if not self._amateur_system:
            print(colored("  Amateur system not available.", Colors.DIM))
            pause()
            return
        
        try:
            current_week = self.game_state.week_number if self.game_state else 1
            upcoming = self._amateur_system.get_upcoming_tournaments(current_week, weeks_ahead=12)
            
            if not upcoming:
                print(colored("  No tournaments scheduled in the next 12 weeks.", Colors.DIM))
            else:
                print(f"  {'Week':<6} {'Region':<12} {'Division':<16} {'Fighters':<10}")
                print(f"  {'-' * 50}")
                
                for tourney in upcoming[:15]:
                    week = getattr(tourney, 'week', '?')
                    region = getattr(tourney, 'region', 'Unknown')
                    division = getattr(tourney, 'weight_class', 'Unknown')
                    count = len(getattr(tourney, 'bracket', [])) if hasattr(tourney, 'bracket') else 16
                    
                    print(f"  {week:<6} {region:<12} {division:<16} {count:<10}")
        except Exception as e:
            print(colored(f"  Error: {e}", Colors.RED))
        
        pause()
    
    def _show_recent_tournaments(self) -> None:
        """Show results of recent amateur tournaments."""
        clear_screen()
        print_header("RECENT TOURNAMENTS")
        
        if not self._amateur_system:
            print(colored("  Amateur system not available.", Colors.DIM))
            pause()
            return
        
        try:
            history = self._amateur_system.completed_tournaments[-10:] if hasattr(self._amateur_system, 'completed_tournaments') else []
            
            if not history:
                print(colored("  No tournament history available yet.", Colors.DIM))
                print()
                print("  Tournaments run every ~6 weeks per region.")
                print("  Keep advancing weeks to see results.")
            else:
                for tourney in reversed(history):
                    region = getattr(tourney, 'region', 'Unknown')
                    division = getattr(tourney, 'weight_class', 'Unknown')
                    week = getattr(tourney, 'week', '?')
                    
                    # Look up champion name from fighter ID
                    champion_id = getattr(tourney, 'champion_id', None)
                    champion_name = 'Unknown'
                    if champion_id and hasattr(self._amateur_system, 'get_amateur'):
                        champ = self._amateur_system.get_amateur(champion_id)
                        if champ:
                            champion_name = champ.name
                    
                    print(f"\n  {colored(f'{region} {division}', Colors.CYAN)} (Week {week})")
                    print(f"  Champion: {colored(champion_name, Colors.GOLD)}")
                    
                    # Show finalist if available
                    finalist_id = getattr(tourney, 'finalist_id', None)
                    if finalist_id and hasattr(self._amateur_system, 'get_amateur'):
                        finalist = self._amateur_system.get_amateur(finalist_id)
                        if finalist:
                            print(f"  Finalist: {finalist.name}")
        except Exception as e:
            print(colored(f"  Error: {e}", Colors.RED))
        
        pause()
    
    def _sign_amateur_fighter(self) -> None:
        """Direct path to sign an amateur - goes to scout first."""
        self._scout_amateur_prospects()
    
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
        
        # Sort by actual rank: Champion first, then ranked by position, then unranked by OVR
        def get_sort_key(fighter):
            if self._is_division_champion(fighter):
                return (0, 0, -fighter.overall_rating)  # Champion always first
            rank = self._get_fighter_division_rank(fighter)
            if rank is not None:
                return (1, rank, -fighter.overall_rating)  # Ranked fighters by rank
            else:
                return (2, 999, -fighter.overall_rating)  # Unranked by OVR
        
        all_fighters.sort(key=get_sort_key)
        
        # Build a rank lookup for display
        fighter_ranks = {}
        for f in all_fighters:
            fighter_ranks[f.fighter_id] = self._get_fighter_division_rank(f)
        
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
                player_camp = self.game_state.get_player_camp()
                player_camp_id = player_camp.camp_id if player_camp else None
                
                for i, f in enumerate(display_fighters):
                    num = start_idx + i + 1
                    f_data = self.fighter_data.get(f.fighter_id)
                    actual_rank = fighter_ranks.get(f.fighter_id)
                    
                    # =================================================================
                    # DOPAMINE: HOT/COLD FORM + YOUR FIGHTER HIGHLIGHT
                    # =================================================================
                    form_icon = ""
                    if f_data:
                        if f_data.win_streak >= 5:
                            form_icon = colored(" [!][!]", Colors.GOLD)
                        elif f_data.win_streak >= 3:
                            form_icon = colored(" [!]", Colors.ORANGE)
                        elif f_data.lose_streak >= 3:
                            form_icon = colored(" *", Colors.BLUE)
                    
                    # Highlight your fighters
                    is_yours = getattr(f, 'camp_id', None) == player_camp_id
                    is_champ = self._is_division_champion(f)
                    
                    # Display actual rank (not display index)
                    if is_champ:
                        prefix = colored("[C]", Colors.GOLD)
                        name_str = colored(f.name, Colors.GOLD)
                    elif is_yours:
                        # Show rank if ranked, otherwise show arrow
                        if actual_rank:
                            prefix = colored(f"#{actual_rank:2}", Colors.CYAN)
                        else:
                            prefix = colored("UR", Colors.DIM)
                        name_str = colored(f.name, Colors.HIGHLIGHT)
                    elif actual_rank:
                        prefix = f"#{actual_rank:2}"
                        name_str = f.name
                    else:
                        prefix = colored("UR", Colors.DIM)
                        name_str = f.name
                    
                    yours_marker = colored(" [YOURS]", Colors.CYAN) if is_yours else ""
                    print(f"  [{num:2}] {prefix}  {name_str} ({format_record_colored(f.wins, f.losses)}) - {f.overall_rating}{form_icon}{yours_marker}")
            
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
