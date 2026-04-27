# core/week_advancement.py
# Module: Week Advancement System (Core Game Loop)
# Lines: ~1400
#
# The heartbeat of Cage Dynasty - ties all systems together
# and processes weekly game progression.

"""
Cage Dynasty - Week Advancement System

This is the CORE GAME LOOP that ties all systems together:
- Training camp progression
- Scheduled fight execution
- Fight offer generation
- Injury recovery
- Aging and degradation
- Rankings updates
- News generation
- Contract management

THE GAME LOOP:
==============

Each week when you advance time:

1. TRAINING PHASE
   - All fighters in active camps train
   - Gains applied, fatigue accumulated
   - Check for training injuries

2. FIGHT PHASE
   - Execute any fights scheduled for this week
   - Update records, rankings, championships
   - Apply post-fight injuries

3. RECOVERY PHASE
   - Injured fighters heal (weeks decrease)
   - Fatigue recovery for inactive fighters

4. OFFERS PHASE
   - AI generates fight offers for player
   - Expire old pending offers

5. BUSINESS PHASE
   - Process contracts (expirations, payments)
   - Camp expenses

6. WORLD PHASE
   - Age fighters (monthly)
   - Generate prospects (periodically)
   - Retirement checks

7. NEWS PHASE
   - Generate headlines for events
   - Track rivalries, storylines

USAGE:
    from core.week_advancement import (
        WeekAdvancementSystem,
        WeekSummary,
        create_week_system,
    )
    
    # Create system with all managers
    system = WeekAdvancementSystem()
    system.set_training_manager(training_mgr)
    system.set_fight_offers_manager(offers_mgr)
    system.set_fight_executor(fight_executor)
    
    # Advance one week
    summary = system.advance_week()
    
    # View what happened
    for headline in summary.headlines:
        print(headline)
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class EventType(Enum):
    """Types of events that can occur during week advancement."""
    FIGHT_COMPLETED = "fight_completed"
    TRAINING_PROGRESS = "training_progress"
    INJURY_OCCURRED = "injury_occurred"
    INJURY_HEALED = "injury_healed"
    TITLE_CHANGE = "title_change"
    FIGHTER_SIGNED = "fighter_signed"
    FIGHTER_RELEASED = "fighter_released"
    FIGHTER_RETIRED = "fighter_retired"
    CONTRACT_EXPIRED = "contract_expired"
    OFFER_RECEIVED = "offer_received"
    OFFER_EXPIRED = "offer_expired"
    RANKING_CHANGE = "ranking_change"
    CAMP_UPGRADED = "camp_upgraded"
    RIVALRY_STARTED = "rivalry_started"
    MILESTONE_REACHED = "milestone_reached"


class HeadlineCategory(Enum):
    """Categories for news headlines."""
    FIGHT_RESULT = "fight_result"
    TITLE_NEWS = "title_news"
    INJURY_NEWS = "injury_news"
    SIGNING_NEWS = "signing_news"
    TRAINING_NEWS = "training_news"
    RANKING_NEWS = "ranking_news"
    RETIREMENT_NEWS = "retirement_news"
    GENERAL_NEWS = "general_news"


# Week advancement settings
DEFAULT_INJURY_HEAL_WEEKS = 4
FATIGUE_RECOVERY_PER_WEEK = 15
OFFER_EXPIRATION_WEEKS = 2
AGING_CHECK_WEEK = 1  # First week of month


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class WeekEvent:
    """A single event that occurred during week advancement."""
    event_type: EventType
    description: str
    fighter_id: Optional[str] = None
    fighter_name: Optional[str] = None
    camp_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    is_player_relevant: bool = False
    headline: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "description": self.description,
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "camp_id": self.camp_id,
            "details": self.details,
            "is_player_relevant": self.is_player_relevant,
            "headline": self.headline,
        }


@dataclass
class FightResult:
    """Result of a simulated fight."""
    fight_id: str
    winner_id: str
    winner_name: str
    loser_id: str
    loser_name: str
    method: str  # KO, TKO, SUB, DEC, etc.
    round_finished: int
    time_finished: str
    weight_class: str
    was_title_fight: bool = False
    title_changed: bool = False
    winner_bonus: int = 0
    loser_bonus: int = 0
    
    @property
    def headline(self) -> str:
        """Generate headline for this fight."""
        if self.was_title_fight and self.title_changed:
            return f"👑 NEW CHAMPION! {self.winner_name} defeats {self.loser_name} via {self.method} R{self.round_finished}"
        elif self.was_title_fight:
            return f"🏆 {self.winner_name} defends title against {self.loser_name} via {self.method}"
        elif self.method in ["KO", "TKO"]:
            return f"💥 {self.winner_name} stops {self.loser_name} via {self.method} in R{self.round_finished}"
        elif self.method == "SUB":
            return f"🔒 {self.winner_name} submits {self.loser_name} in R{self.round_finished}"
        else:
            return f"🥊 {self.winner_name} defeats {self.loser_name} via {self.method}"


@dataclass
class TrainingProgress:
    """Training progress for a fighter during the week."""
    fighter_id: str
    fighter_name: str
    gains: Dict[str, int]
    total_gains: int
    week_number: int
    camp_completed: bool = False
    injury_occurred: bool = False
    injury_type: str = ""
    capped_attributes: List[str] = field(default_factory=list)


@dataclass
class InjuryUpdate:
    """Injury status update for a fighter."""
    fighter_id: str
    fighter_name: str
    injury_type: str
    weeks_remaining: int
    healed: bool = False


@dataclass
class OfferUpdate:
    """Fight offer update."""
    offer_id: str
    offering_fighter: str
    target_fighter: str
    status: str  # new, expired, accepted, declined
    is_incoming: bool = False  # To player


@dataclass
class WeekSummary:
    """Complete summary of a week's events."""
    week_number: int
    year: int
    month: int
    day: int
    date_string: str
    
    # Counts
    fights_completed: int = 0
    training_sessions: int = 0
    injuries_occurred: int = 0
    injuries_healed: int = 0
    offers_received: int = 0
    offers_expired: int = 0
    contracts_expired: int = 0
    retirements: int = 0
    
    # Details
    fight_results: List[FightResult] = field(default_factory=list)
    training_progress: List[TrainingProgress] = field(default_factory=list)
    injury_updates: List[InjuryUpdate] = field(default_factory=list)
    offer_updates: List[OfferUpdate] = field(default_factory=list)
    events: List[WeekEvent] = field(default_factory=list)
    
    # Headlines (for news feed)
    headlines: List[str] = field(default_factory=list)
    player_headlines: List[str] = field(default_factory=list)
    
    @property
    def has_player_events(self) -> bool:
        return len(self.player_headlines) > 0
    
    def add_event(self, event: WeekEvent) -> None:
        """Add an event and potentially a headline."""
        self.events.append(event)
        if event.headline:
            self.headlines.append(event.headline)
            if event.is_player_relevant:
                self.player_headlines.append(event.headline)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_number": self.week_number,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "date_string": self.date_string,
            "fights_completed": self.fights_completed,
            "training_sessions": self.training_sessions,
            "injuries_occurred": self.injuries_occurred,
            "injuries_healed": self.injuries_healed,
            "offers_received": self.offers_received,
            "offers_expired": self.offers_expired,
            "headlines": self.headlines,
            "player_headlines": self.player_headlines,
        }


# ============================================================================
# FIGHTER STATE (For Week Processing)
# ============================================================================

@dataclass
class FighterWeekState:
    """Fighter state needed for week processing."""
    fighter_id: str
    name: str
    age: int
    camp_id: Optional[str] = None
    is_player_fighter: bool = False
    
    # Status
    is_active: bool = True
    is_injured: bool = False
    injury_type: str = ""
    injury_weeks_remaining: int = 0
    
    # Training
    in_training_camp: bool = False
    scheduled_fight_date: Optional[str] = None
    scheduled_fight_weeks: int = 0
    
    # Stats for update
    fatigue: int = 0
    wins: int = 0
    losses: int = 0
    win_streak: int = 0
    ko_streak: int = 0
    
    # Record keeping
    last_fight_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "age": self.age,
            "camp_id": self.camp_id,
            "is_player_fighter": self.is_player_fighter,
            "is_active": self.is_active,
            "is_injured": self.is_injured,
            "injury_type": self.injury_type,
            "injury_weeks_remaining": self.injury_weeks_remaining,
            "in_training_camp": self.in_training_camp,
            "scheduled_fight_date": self.scheduled_fight_date,
            "scheduled_fight_weeks": self.scheduled_fight_weeks,
            "fatigue": self.fatigue,
        }


@dataclass 
class ScheduledFight:
    """A fight scheduled to occur."""
    fight_id: str
    fighter1_id: str
    fighter1_name: str
    fighter2_id: str
    fighter2_name: str
    weight_class: str
    scheduled_week: int  # Week number when fight occurs
    scheduled_date: str
    is_title_fight: bool = False
    is_main_event: bool = False
    involves_player: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fight_id": self.fight_id,
            "fighter1_id": self.fighter1_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_id": self.fighter2_id,
            "fighter2_name": self.fighter2_name,
            "weight_class": self.weight_class,
            "scheduled_week": self.scheduled_week,
            "scheduled_date": self.scheduled_date,
            "is_title_fight": self.is_title_fight,
            "is_main_event": self.is_main_event,
            "involves_player": self.involves_player,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledFight":
        return cls(**data)


# ============================================================================
# WEEK ADVANCEMENT SYSTEM
# ============================================================================

class WeekAdvancementSystem:
    """
    Core game loop manager that processes weekly advancement.
    
    This is the central orchestrator that ties all systems together:
    - Training
    - Fights
    - Offers
    - Injuries
    - Aging
    - Contracts
    - News
    """
    
    def __init__(self):
        # State
        self._current_week = 1
        self._current_year = 2025
        self._current_month = 1
        self._current_day = 1
        
        # Fighter states
        self._fighters: Dict[str, FighterWeekState] = {}
        self._player_camp_id: Optional[str] = None
        
        # Scheduled events
        self._scheduled_fights: Dict[str, ScheduledFight] = {}
        self._pending_offers: Dict[str, Dict[str, Any]] = {}
        
        # Pluggable managers (set externally)
        self._training_manager: Optional[Any] = None
        self._fight_offers_manager: Optional[Any] = None
        self._fight_executor: Optional[Callable] = None
        self._rankings_manager: Optional[Any] = None
        self._aging_processor: Optional[Callable] = None
        
        # Callbacks for external systems
        self._on_fight_completed: List[Callable] = []
        self._on_training_completed: List[Callable] = []
        self._on_injury: List[Callable] = []
        
        # History
        self._week_history: List[WeekSummary] = []
        self._fight_counter = 0
    
    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    
    def set_player_camp(self, camp_id: str) -> None:
        """Set the player's camp ID."""
        self._player_camp_id = camp_id
    
    def set_training_manager(self, manager: Any) -> None:
        """Set the training camp manager."""
        self._training_manager = manager
    
    def set_fight_offers_manager(self, manager: Any) -> None:
        """Set the fight offers manager."""
        self._fight_offers_manager = manager
    
    def set_fight_executor(self, executor: Callable) -> None:
        """Set the fight execution function."""
        self._fight_executor = executor
    
    def set_rankings_manager(self, manager: Any) -> None:
        """Set the rankings manager."""
        self._rankings_manager = manager
    
    def set_aging_processor(self, processor: Callable) -> None:
        """Set the aging processor function."""
        self._aging_processor = processor
    
    def add_fight_callback(self, callback: Callable) -> None:
        """Add callback for fight completion."""
        self._on_fight_completed.append(callback)
    
    def add_training_callback(self, callback: Callable) -> None:
        """Add callback for training completion."""
        self._on_training_completed.append(callback)
    
    def add_injury_callback(self, callback: Callable) -> None:
        """Add callback for injuries."""
        self._on_injury.append(callback)
    
    # -------------------------------------------------------------------------
    # Fighter Management
    # -------------------------------------------------------------------------
    
    def register_fighter(self, fighter: FighterWeekState) -> None:
        """Register a fighter for week processing."""
        self._fighters[fighter.fighter_id] = fighter
    
    def get_fighter(self, fighter_id: str) -> Optional[FighterWeekState]:
        """Get fighter state."""
        return self._fighters.get(fighter_id)
    
    def update_fighter(self, fighter_id: str, **updates) -> bool:
        """Update fighter state."""
        if fighter_id not in self._fighters:
            return False
        fighter = self._fighters[fighter_id]
        for key, value in updates.items():
            if hasattr(fighter, key):
                setattr(fighter, key, value)
        return True
    
    # -------------------------------------------------------------------------
    # Fight Scheduling
    # -------------------------------------------------------------------------
    
    def schedule_fight(
        self,
        fighter1_id: str,
        fighter2_id: str,
        weeks_from_now: int = 8,
        is_title_fight: bool = False,
        is_main_event: bool = False,
    ) -> Optional[ScheduledFight]:
        """Schedule a fight for a future week."""
        f1 = self._fighters.get(fighter1_id)
        f2 = self._fighters.get(fighter2_id)
        
        if not f1 or not f2:
            return None
        
        self._fight_counter += 1
        fight_id = f"fight_{self._fight_counter}"
        
        scheduled_week = self._current_week + weeks_from_now
        
        fight = ScheduledFight(
            fight_id=fight_id,
            fighter1_id=fighter1_id,
            fighter1_name=f1.name,
            fighter2_id=fighter2_id,
            fighter2_name=f2.name,
            weight_class="",  # Would get from fighter
            scheduled_week=scheduled_week,
            scheduled_date=f"Week {scheduled_week}",
            is_title_fight=is_title_fight,
            is_main_event=is_main_event,
            involves_player=f1.is_player_fighter or f2.is_player_fighter,
        )
        
        self._scheduled_fights[fight_id] = fight
        
        # Update fighter states
        f1.scheduled_fight_weeks = weeks_from_now
        f2.scheduled_fight_weeks = weeks_from_now
        
        return fight
    
    def get_scheduled_fights(self, week: Optional[int] = None) -> List[ScheduledFight]:
        """Get scheduled fights, optionally filtered by week."""
        if week is None:
            return list(self._scheduled_fights.values())
        return [
            f for f in self._scheduled_fights.values()
            if f.scheduled_week == week
        ]
    
    def get_player_scheduled_fights(self) -> List[ScheduledFight]:
        """Get fights involving player's fighters."""
        return [f for f in self._scheduled_fights.values() if f.involves_player]
    
    # -------------------------------------------------------------------------
    # CORE: Week Advancement
    # -------------------------------------------------------------------------
    
    def advance_week(self) -> WeekSummary:
        """
        CORE GAME LOOP - Advance the game by one week.
        
        Processes all systems in order:
        1. Advance date (move to next week)
        2. Training
        3. Fights (execute fights scheduled for this week)
        4. Recovery
        5. Offers
        6. Business
        7. World (aging, etc.)
        8. News
        
        Returns complete summary of the week.
        """
        # Advance time FIRST so we're at the new week
        self._advance_date()
        
        # Create summary for the new week
        summary = WeekSummary(
            week_number=self._current_week,
            year=self._current_year,
            month=self._current_month,
            day=self._current_day,
            date_string=f"Week {self._current_week}, Year {self._current_year}",
        )
        
        # === PHASE 1: TRAINING ===
        self._process_training(summary)
        
        # === PHASE 2: FIGHTS ===
        # Now fights scheduled for current_week will execute
        self._process_fights(summary)
        
        # === PHASE 3: RECOVERY ===
        self._process_recovery(summary)
        
        # === PHASE 4: OFFERS ===
        self._process_offers(summary)
        
        # === PHASE 5: BUSINESS ===
        self._process_business(summary)
        
        # === PHASE 6: WORLD ===
        self._process_world(summary)
        
        # === PHASE 7: NEWS ===
        self._generate_news(summary)
        
        # Store history
        self._week_history.append(summary)
        
        return summary
    
    def advance_weeks(self, num_weeks: int) -> List[WeekSummary]:
        """Advance multiple weeks."""
        summaries = []
        for _ in range(num_weeks):
            summaries.append(self.advance_week())
        return summaries
    
    # -------------------------------------------------------------------------
    # Phase 1: Training
    # -------------------------------------------------------------------------
    
    def _process_training(self, summary: WeekSummary) -> None:
        """Process training for all fighters in camps."""
        if not self._training_manager:
            return
        
        # Get all fighters in training
        for fighter_id, fighter in self._fighters.items():
            if not fighter.in_training_camp:
                continue
            if fighter.is_injured:
                continue
            
            # Process week of training
            result = self._training_manager.process_week(fighter_id)
            
            if result:
                progress = TrainingProgress(
                    fighter_id=fighter_id,
                    fighter_name=fighter.name,
                    gains=result.gains if hasattr(result, 'gains') else {},
                    total_gains=result.total_gains if hasattr(result, 'total_gains') else 0,
                    week_number=result.week_number if hasattr(result, 'week_number') else 1,
                    injury_occurred=result.injury_occurred if hasattr(result, 'injury_occurred') else False,
                )
                
                summary.training_progress.append(progress)
                summary.training_sessions += 1
                
                # Handle training injury
                if progress.injury_occurred:
                    self._handle_training_injury(fighter, progress, summary)
                
                # Check if camp completed
                camp = self._training_manager.get_camp(fighter_id)
                if camp and camp.is_complete:
                    progress.camp_completed = True
                    
                    event = WeekEvent(
                        event_type=EventType.TRAINING_PROGRESS,
                        description=f"{fighter.name} completed training camp",
                        fighter_id=fighter_id,
                        fighter_name=fighter.name,
                        is_player_relevant=fighter.is_player_fighter,
                        headline=f"📈 {fighter.name} completes training camp (+{camp.sum_total_gains} pts)",
                    )
                    summary.add_event(event)
                    
                    # Callback
                    for callback in self._on_training_completed:
                        callback(fighter_id, camp)
    
    def _handle_training_injury(
        self,
        fighter: FighterWeekState,
        progress: TrainingProgress,
        summary: WeekSummary,
    ) -> None:
        """Handle a training injury."""
        injury_type = progress.injury_type or "Training injury"
        weeks = random.randint(1, 3)  # Training injuries are minor
        
        fighter.is_injured = True
        fighter.injury_type = injury_type
        fighter.injury_weeks_remaining = weeks
        fighter.in_training_camp = False
        
        summary.injuries_occurred += 1
        
        update = InjuryUpdate(
            fighter_id=fighter.fighter_id,
            fighter_name=fighter.name,
            injury_type=injury_type,
            weeks_remaining=weeks,
        )
        summary.injury_updates.append(update)
        
        event = WeekEvent(
            event_type=EventType.INJURY_OCCURRED,
            description=f"{fighter.name} injured in training: {injury_type}",
            fighter_id=fighter.fighter_id,
            fighter_name=fighter.name,
            is_player_relevant=fighter.is_player_fighter,
            headline=f"🏥 {fighter.name} suffers {injury_type} in training ({weeks} weeks)",
        )
        summary.add_event(event)
        
        # Callback
        for callback in self._on_injury:
            callback(fighter.fighter_id, injury_type, weeks)
    
    # -------------------------------------------------------------------------
    # Phase 2: Fights
    # -------------------------------------------------------------------------
    
    def _process_fights(self, summary: WeekSummary) -> None:
        """Execute fights scheduled for this week."""
        fights_this_week = self.get_scheduled_fights(self._current_week)
        
        for scheduled in fights_this_week:
            result = self._execute_fight(scheduled, summary)
            if result:
                summary.fight_results.append(result)
                summary.fights_completed += 1
                
                # Remove from schedule
                if scheduled.fight_id in self._scheduled_fights:
                    del self._scheduled_fights[scheduled.fight_id]
    
    def _execute_fight(
        self,
        scheduled: ScheduledFight,
        summary: WeekSummary,
    ) -> Optional[FightResult]:
        """Execute a single fight."""
        f1 = self._fighters.get(scheduled.fighter1_id)
        f2 = self._fighters.get(scheduled.fighter2_id)
        
        if not f1 or not f2:
            return None
        
        # Check for injuries/cancellations
        if f1.is_injured or f2.is_injured:
            event = WeekEvent(
                event_type=EventType.FIGHT_COMPLETED,
                description=f"Fight cancelled: {f1.name} vs {f2.name}",
                is_player_relevant=scheduled.involves_player,
                headline=f"❌ Fight cancelled: {f1.name} vs {f2.name} (injury)",
            )
            summary.add_event(event)
            return None
        
        # Execute fight (using executor or simulate)
        if self._fight_executor:
            raw_result = self._fight_executor(f1, f2, scheduled.is_title_fight)
        else:
            raw_result = self._simulate_fight(f1, f2, scheduled.is_title_fight)
        
        # Create result
        result = FightResult(
            fight_id=scheduled.fight_id,
            winner_id=raw_result["winner_id"],
            winner_name=raw_result["winner_name"],
            loser_id=raw_result["loser_id"],
            loser_name=raw_result["loser_name"],
            method=raw_result["method"],
            round_finished=raw_result["round"],
            time_finished=raw_result.get("time", "5:00"),
            weight_class=scheduled.weight_class,
            was_title_fight=scheduled.is_title_fight,
            title_changed=raw_result.get("title_changed", False),
        )
        
        # Update fighter records
        self._update_fighter_after_fight(result, summary)
        
        # Add event
        event = WeekEvent(
            event_type=EventType.FIGHT_COMPLETED,
            description=result.headline,
            fighter_id=result.winner_id,
            is_player_relevant=scheduled.involves_player,
            headline=result.headline,
        )
        summary.add_event(event)
        
        # Callbacks
        for callback in self._on_fight_completed:
            callback(result)
        
        return result
    
    def _simulate_fight(
        self,
        f1: FighterWeekState,
        f2: FighterWeekState,
        is_title: bool,
    ) -> Dict[str, Any]:
        """Simple fight simulation (fallback if no executor set)."""
        # Random winner based on records
        f1_score = f1.wins - f1.losses + random.randint(-5, 5)
        f2_score = f2.wins - f2.losses + random.randint(-5, 5)
        
        if f1_score >= f2_score:
            winner, loser = f1, f2
        else:
            winner, loser = f2, f1
        
        # Random method
        methods = ["KO", "TKO", "SUB", "DEC", "DEC", "DEC"]
        method = random.choice(methods)
        
        rounds = 5 if is_title else 3
        if method in ["KO", "TKO", "SUB"]:
            fight_round = random.randint(1, rounds)
        else:
            fight_round = rounds
        
        return {
            "winner_id": winner.fighter_id,
            "winner_name": winner.name,
            "loser_id": loser.fighter_id,
            "loser_name": loser.name,
            "method": method,
            "round": fight_round,
            "title_changed": is_title and winner.fighter_id == f2.fighter_id,
        }
    
    def _update_fighter_after_fight(
        self,
        result: FightResult,
        summary: WeekSummary,
    ) -> None:
        """Update fighter states after a fight."""
        winner = self._fighters.get(result.winner_id)
        loser = self._fighters.get(result.loser_id)
        
        if winner:
            winner.wins += 1
            winner.win_streak += 1
            if result.method in ["KO", "TKO"]:
                winner.ko_streak += 1
            else:
                winner.ko_streak = 0
            winner.scheduled_fight_date = None
            winner.scheduled_fight_weeks = 0
            winner.in_training_camp = False
            winner.last_fight_date = summary.date_string
            winner.fatigue += 30  # Post-fight fatigue
        
        if loser:
            loser.losses += 1
            loser.win_streak = 0
            loser.ko_streak = 0
            loser.scheduled_fight_date = None
            loser.scheduled_fight_weeks = 0
            loser.in_training_camp = False
            loser.last_fight_date = summary.date_string
            loser.fatigue += 40  # More fatigue for losing
            
            # Check for post-fight injury
            if result.method in ["KO", "TKO"]:
                if random.random() < 0.3:  # 30% injury chance after KO
                    self._apply_post_fight_injury(loser, summary)
    
    def _apply_post_fight_injury(
        self,
        fighter: FighterWeekState,
        summary: WeekSummary,
    ) -> None:
        """Apply post-fight injury."""
        injuries = [
            ("Concussion protocol", 4),
            ("Broken hand", 8),
            ("Fractured orbital", 12),
            ("Knee injury", 10),
            ("Rib injury", 6),
        ]
        injury_type, weeks = random.choice(injuries)
        
        fighter.is_injured = True
        fighter.injury_type = injury_type
        fighter.injury_weeks_remaining = weeks
        
        summary.injuries_occurred += 1
        
        update = InjuryUpdate(
            fighter_id=fighter.fighter_id,
            fighter_name=fighter.name,
            injury_type=injury_type,
            weeks_remaining=weeks,
        )
        summary.injury_updates.append(update)
        
        event = WeekEvent(
            event_type=EventType.INJURY_OCCURRED,
            description=f"{fighter.name} injured: {injury_type}",
            fighter_id=fighter.fighter_id,
            fighter_name=fighter.name,
            is_player_relevant=fighter.is_player_fighter,
            headline=f"🏥 {fighter.name} out {weeks} weeks with {injury_type}",
        )
        summary.add_event(event)
    
    # -------------------------------------------------------------------------
    # Phase 3: Recovery
    # -------------------------------------------------------------------------
    
    def _process_recovery(self, summary: WeekSummary) -> None:
        """Process injury recovery and fatigue."""
        for fighter_id, fighter in self._fighters.items():
            # Injury recovery
            if fighter.is_injured and fighter.injury_weeks_remaining > 0:
                fighter.injury_weeks_remaining -= 1
                
                if fighter.injury_weeks_remaining <= 0:
                    fighter.is_injured = False
                    fighter.injury_type = ""
                    summary.injuries_healed += 1
                    
                    update = InjuryUpdate(
                        fighter_id=fighter_id,
                        fighter_name=fighter.name,
                        injury_type="",
                        weeks_remaining=0,
                        healed=True,
                    )
                    summary.injury_updates.append(update)
                    
                    event = WeekEvent(
                        event_type=EventType.INJURY_HEALED,
                        description=f"{fighter.name} recovered from injury",
                        fighter_id=fighter_id,
                        fighter_name=fighter.name,
                        is_player_relevant=fighter.is_player_fighter,
                        headline=f"✅ {fighter.name} cleared to fight after injury",
                    )
                    summary.add_event(event)
            
            # Fatigue recovery (if not in camp)
            if not fighter.in_training_camp and fighter.fatigue > 0:
                fighter.fatigue = max(0, fighter.fatigue - FATIGUE_RECOVERY_PER_WEEK)
            
            # Decrement scheduled fight weeks
            if fighter.scheduled_fight_weeks > 0:
                fighter.scheduled_fight_weeks -= 1
    
    # -------------------------------------------------------------------------
    # Phase 4: Offers
    # -------------------------------------------------------------------------
    
    def _process_offers(self, summary: WeekSummary) -> None:
        """Process fight offers - generate new, expire old."""
        if not self._fight_offers_manager:
            return
        
        # Generate AI offers for player
        if self._player_camp_id:
            new_offers = self._fight_offers_manager.generate_ai_offers_for_player(
                self._player_camp_id,
                summary.date_string,
                max_offers=2,
            )
            
            for offer in new_offers:
                summary.offers_received += 1
                
                update = OfferUpdate(
                    offer_id=offer.offer_id if hasattr(offer, 'offer_id') else "unknown",
                    offering_fighter=offer.offering_fighter_name if hasattr(offer, 'offering_fighter_name') else "Unknown",
                    target_fighter=offer.target_fighter_name if hasattr(offer, 'target_fighter_name') else "Unknown",
                    status="new",
                    is_incoming=True,
                )
                summary.offer_updates.append(update)
                
                event = WeekEvent(
                    event_type=EventType.OFFER_RECEIVED,
                    description=f"Fight offer received for {update.target_fighter}",
                    is_player_relevant=True,
                    headline=f"📨 Fight offer: {update.offering_fighter} wants to fight {update.target_fighter}",
                )
                summary.add_event(event)
        
        # Expire old offers
        pending = self._fight_offers_manager.get_pending_offers()
        for offer in pending:
            # Would check expiration date
            # For now, offers last 2 weeks
            pass
    
    # -------------------------------------------------------------------------
    # Phase 5: Business
    # -------------------------------------------------------------------------
    
    def _process_business(self, summary: WeekSummary) -> None:
        """Process contracts, payments, expenses."""
        # Contract expirations would be checked here
        # Camp expenses would be processed here
        pass
    
    # -------------------------------------------------------------------------
    # Phase 6: World
    # -------------------------------------------------------------------------
    
    def _process_world(self, summary: WeekSummary) -> None:
        """Process aging, retirements, prospect generation."""
        # Monthly aging check
        if self._current_day <= 7 and self._aging_processor:
            for fighter_id, fighter in self._fighters.items():
                result = self._aging_processor(fighter)
                if result and result.get("retired"):
                    summary.retirements += 1
                    
                    event = WeekEvent(
                        event_type=EventType.FIGHTER_RETIRED,
                        description=f"{fighter.name} has retired",
                        fighter_id=fighter_id,
                        fighter_name=fighter.name,
                        is_player_relevant=fighter.is_player_fighter,
                        headline=f"👋 {fighter.name} announces retirement",
                    )
                    summary.add_event(event)
    
    # -------------------------------------------------------------------------
    # Phase 7: News
    # -------------------------------------------------------------------------
    
    def _generate_news(self, summary: WeekSummary) -> None:
        """Generate additional news headlines."""
        # Add any ranking change headlines
        # Add milestone headlines
        # Add general world news
        
        # Ensure fight results are in headlines
        for result in summary.fight_results:
            if result.headline not in summary.headlines:
                summary.headlines.append(result.headline)
    
    # -------------------------------------------------------------------------
    # Date Management
    # -------------------------------------------------------------------------
    
    def _advance_date(self) -> None:
        """Advance the date by one week."""
        self._current_week += 1
        self._current_day += 7
        
        # Handle month rollover (simplified)
        if self._current_day > 28:
            self._current_day = self._current_day - 28
            self._current_month += 1
            
            if self._current_month > 12:
                self._current_month = 1
                self._current_year += 1
    
    def get_current_date(self) -> Dict[str, int]:
        """Get current date."""
        return {
            "week": self._current_week,
            "year": self._current_year,
            "month": self._current_month,
            "day": self._current_day,
        }
    
    def set_date(self, week: int, year: int, month: int = 1, day: int = 1) -> None:
        """Set the current date."""
        self._current_week = week
        self._current_year = year
        self._current_month = month
        self._current_day = day
    
    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------
    
    def get_upcoming_fights(self, weeks_ahead: int = 8) -> List[ScheduledFight]:
        """Get fights scheduled in the next N weeks."""
        max_week = self._current_week + weeks_ahead
        return [
            f for f in self._scheduled_fights.values()
            if f.scheduled_week <= max_week
        ]
    
    def get_injured_fighters(self) -> List[FighterWeekState]:
        """Get all currently injured fighters."""
        return [f for f in self._fighters.values() if f.is_injured]
    
    def get_available_fighters(self) -> List[FighterWeekState]:
        """Get all available fighters (not injured, not scheduled)."""
        return [
            f for f in self._fighters.values()
            if f.is_active and not f.is_injured and f.scheduled_fight_weeks == 0
        ]
    
    def get_week_history(self, num_weeks: int = 10) -> List[WeekSummary]:
        """Get recent week history."""
        return self._week_history[-num_weeks:]
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Export system state."""
        return {
            "current_week": self._current_week,
            "current_year": self._current_year,
            "current_month": self._current_month,
            "current_day": self._current_day,
            "player_camp_id": self._player_camp_id,
            "fighters": {
                fid: f.to_dict() for fid, f in self._fighters.items()
            },
            "scheduled_fights": {
                fid: f.to_dict() for fid, f in self._scheduled_fights.items()
            },
            "fight_counter": self._fight_counter,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeekAdvancementSystem":
        """Create system from saved data."""
        system = cls()
        system._current_week = data.get("current_week", 1)
        system._current_year = data.get("current_year", 2025)
        system._current_month = data.get("current_month", 1)
        system._current_day = data.get("current_day", 1)
        system._player_camp_id = data.get("player_camp_id")
        system._fight_counter = data.get("fight_counter", 0)
        
        # Load fighters
        for fid, fdata in data.get("fighters", {}).items():
            system._fighters[fid] = FighterWeekState(**fdata)
        
        # Load scheduled fights
        for fid, fdata in data.get("scheduled_fights", {}).items():
            system._scheduled_fights[fid] = ScheduledFight.from_dict(fdata)
        
        return system


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_week_system() -> WeekAdvancementSystem:
    """Create a new week advancement system."""
    return WeekAdvancementSystem()


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_week_summary(summary: WeekSummary) -> List[str]:
    """Format week summary for display."""
    lines = [
        "",
        "╔" + "═" * 58 + "╗",
        f"║  📅 WEEK {summary.week_number} SUMMARY".ljust(59) + "║",
        f"║  {summary.date_string}".ljust(59) + "║",
        "╠" + "═" * 58 + "╣",
    ]
    
    # Stats row
    stats = []
    if summary.fights_completed:
        stats.append(f"⚔️ {summary.fights_completed} fights")
    if summary.training_sessions:
        stats.append(f"💪 {summary.training_sessions} training")
    if summary.injuries_occurred:
        stats.append(f"🏥 {summary.injuries_occurred} injuries")
    if summary.injuries_healed:
        stats.append(f"✅ {summary.injuries_healed} healed")
    if summary.offers_received:
        stats.append(f"📨 {summary.offers_received} offers")
    
    if stats:
        stats_str = " | ".join(stats)
        lines.append(f"║  {stats_str}".ljust(59) + "║")
        lines.append("╠" + "═" * 58 + "╣")
    
    # Headlines
    if summary.headlines:
        lines.append("║  📰 NEWS".ljust(59) + "║")
        lines.append("║" + " " * 58 + "║")
        for headline in summary.headlines[:8]:
            # Truncate long headlines
            if len(headline) > 54:
                headline = headline[:51] + "..."
            lines.append(f"║  • {headline}".ljust(59) + "║")
    else:
        lines.append("║  (Quiet week - no major news)".ljust(59) + "║")
    
    lines.append("╚" + "═" * 58 + "╝")
    lines.append("")
    
    return lines


def format_upcoming_fights(fights: List[ScheduledFight], current_week: int) -> List[str]:
    """Format upcoming fights for display."""
    lines = [
        "",
        "═" * 50,
        "  📋 UPCOMING FIGHTS",
        "═" * 50,
    ]
    
    if not fights:
        lines.append("  No fights scheduled")
    else:
        for fight in sorted(fights, key=lambda f: f.scheduled_week):
            weeks_away = fight.scheduled_week - current_week
            title = "👑 " if fight.is_title_fight else ""
            player = "⭐ " if fight.involves_player else ""
            
            lines.append(f"  {player}{title}{fight.fighter1_name} vs {fight.fighter2_name}")
            lines.append(f"      Week {fight.scheduled_week} ({weeks_away} weeks away)")
            lines.append("")
    
    lines.append("═" * 50)
    return lines


def format_injury_report(injuries: List[InjuryUpdate]) -> List[str]:
    """Format injury report for display."""
    lines = [
        "",
        "═" * 50,
        "  🏥 INJURY REPORT",
        "═" * 50,
    ]
    
    if not injuries:
        lines.append("  No injuries to report")
    else:
        for injury in injuries:
            if injury.healed:
                lines.append(f"  ✅ {injury.fighter_name} - CLEARED")
            else:
                lines.append(f"  🏥 {injury.fighter_name} - {injury.injury_type}")
                lines.append(f"      {injury.weeks_remaining} weeks remaining")
    
    lines.append("═" * 50)
    return lines


def format_training_report(progress: List[TrainingProgress]) -> List[str]:
    """Format training progress for display."""
    lines = [
        "",
        "═" * 50,
        "  💪 TRAINING REPORT",
        "═" * 50,
    ]
    
    if not progress:
        lines.append("  No training this week")
    else:
        for p in progress:
            status = "✅ CAMP COMPLETE" if p.camp_completed else f"Week {p.week_number}"
            injury = " ⚠️ INJURED" if p.injury_occurred else ""
            lines.append(f"  {p.fighter_name} - {status}{injury}")
            lines.append(f"      +{p.total_gains} attribute points")
    
    lines.append("═" * 50)
    return lines


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "EventType", "HeadlineCategory",
    
    # Data classes
    "WeekEvent", "FightResult", "TrainingProgress", "InjuryUpdate",
    "OfferUpdate", "WeekSummary", "FighterWeekState", "ScheduledFight",
    
    # System
    "WeekAdvancementSystem", "create_week_system",
    
    # Display
    "format_week_summary", "format_upcoming_fights",
    "format_injury_report", "format_training_report",
]
