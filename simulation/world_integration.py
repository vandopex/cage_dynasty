# simulation/world_integration.py
# Module: World Integration - Full AI Simulation
# Lines: ~1800
#
# The BRAIN of Cage Dynasty - connects all systems and makes the world LIVE.
# Every AI decision is documented with triggers and percentages.

"""
Cage Dynasty - World Integration

This module is the CENTRAL NERVOUS SYSTEM of the simulation.
It connects:
- AI Behavior (fighter/camp personalities)
- Week Advancement (game loop)
- Fight Offers (matchmaking)
- Training (camps and development)
- Economy (finances)

=============================================================================
DESIGN PHILOSOPHY: CONTROLLED CHAOS
=============================================================================

Every AI decision has:
1. TRIGGERS - What causes the decision to be considered
2. BASE PROBABILITY - Starting chance before modifiers
3. MODIFIERS - Factors that increase/decrease probability
4. CAPS - Minimum and maximum probability bounds
5. LOGGING - Full transparency for debugging

The goal is VARIANCE within REASON:
- No camp should behave identically to another
- But all camps should behave PLAUSIBLY
- Extreme personalities create memorable stories
- But the simulation stays grounded

=============================================================================
AI DECISION SCHEDULE (Per Week)
=============================================================================

EVERY WEEK:
- Training intensity selection for all fighters in camp
- Activity check: should each fighter seek a fight?
- Fight offer evaluation for incoming offers
- Injury recovery and status updates

EVERY 2 WEEKS:
- Camp roster evaluation (release decisions)
- Free agent scouting

EVERY 4 WEEKS:
- Retirement considerations for 33+ fighters
- Target selection / callouts

MONTHLY:
- Aging effects
- Financial review
- Prospect generation

=============================================================================
PROBABILITY REFERENCE GUIDE
=============================================================================

FIGHT ACCEPTANCE (Base: 50%)
├── WARRIOR: +20% (70% base)
├── RECKLESS risk: +25%
├── Title fight: +20%
├── Short notice: -20%
├── Tough opponent: -15%
└── Capped: 5%-95%

SEEKING FIGHTS (Base varies by activity level)
├── VERY_ACTIVE after 6 weeks: 80%
├── ACTIVE after 10 weeks: 70%
├── NORMAL after 14 weeks: 60%
├── SELECTIVE after 20 weeks: 40%
└── INACTIVE after 30 weeks: 25%

RETIREMENT (Base by age)
├── Under 30: 1%
├── 30-33: 3%
├── 34-35: 8%
├── 36-37: 15%
├── 38-39: 25%
├── 40+: 40%
└── Modified by: record, KO losses, title status

TRAINING INTENSITY (Base distribution)
├── LIGHT: 15%
├── MODERATE: 50%
├── INTENSE: 30%
├── EXTREME: 5%
└── Modified by: dedication, fatigue, fight timing

ROSTER RELEASE (Base: 0%)
├── 0-3 in last 5: +40%
├── Age 38+ and rating <60: +30%
├── Inactive 18+ months: +25%
├── Rating <45: +20%
└── Reduced by: loyalty trait

FREE AGENT SIGNING (Base: by interest)
├── Rating 80+: High interest
├── Age <24: Prospect bonus
├── Fits philosophy: +20%
├── Budget concerns: -20%
└── Capped by roster size

"""

from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import random
import math

from simulation.ai_behavior import (
    FighterPersonality, FighterMentality, ActivityPreference,
    RiskProfile, TrainingDedication, FinishingInstinct,
    AIDecisionEngine, DecisionBreakdown,
    generate_fighter_personality, create_ai_engine,
)


# ============================================================================
# DECISION TRIGGERS
# ============================================================================

class DecisionTrigger(Enum):
    """What triggered a decision to be evaluated."""
    WEEKLY_CHECK = "weekly_check"           # Regular weekly cycle
    FIGHT_OFFER_RECEIVED = "offer_received" # Someone offered a fight
    FIGHT_COMPLETED = "fight_completed"     # Just had a fight
    INJURY_HEALED = "injury_healed"         # Recovered from injury
    CONTRACT_EXPIRING = "contract_expiring" # Contract near end
    LOSING_STREAK = "losing_streak"         # Multiple losses
    WINNING_STREAK = "winning_streak"       # Multiple wins
    TITLE_OPPORTUNITY = "title_opportunity" # Title shot available
    RIVALRY_ACTIVE = "rivalry_active"       # Ongoing rivalry
    AGE_MILESTONE = "age_milestone"         # Birthday, aging effects
    CAMP_INSTRUCTION = "camp_instruction"   # Camp telling fighter what to do


# ============================================================================
# CAMP AI CONFIGURATION
# ============================================================================

@dataclass
class CampAIConfig:
    """
    Configuration for how a camp's AI makes decisions.
    
    Every camp has unique tendencies within reasonable bounds.
    """
    camp_id: str
    camp_name: str = ""
    
    # === MATCHMAKING TENDENCIES ===
    # How aggressively camp books fights
    booking_aggression: float = 1.0      # 0.5 (passive) to 1.5 (aggressive)
    
    # Preferred matchup rating differential
    preferred_rating_diff: int = 0       # -10 (challenges) to +10 (favorable)
    
    # Will accept short notice fights
    short_notice_tolerance: float = 0.5  # 0.0 to 1.0
    
    # === ROSTER MANAGEMENT ===
    # How patient with losing fighters
    roster_patience: float = 0.5         # 0.0 (quick to cut) to 1.0 (very patient)
    
    # Preference for prospects vs veterans
    prospect_focus: float = 0.5          # 0.0 (veterans) to 1.0 (prospects)
    
    # Target roster size (relative to max)
    target_roster_fullness: float = 0.8  # 0.5 to 1.0
    
    # === TRAINING PHILOSOPHY ===
    # How hard camp pushes fighters
    training_intensity_bias: float = 0.0  # -0.3 (lighter) to +0.3 (harder)
    
    # Focus areas (weights sum to 1.0)
    striking_focus: float = 0.33
    grappling_focus: float = 0.33
    conditioning_focus: float = 0.34
    
    # === FINANCIAL APPROACH ===
    # How much willing to spend on fighters
    spending_willingness: float = 0.5    # 0.0 (frugal) to 1.0 (generous)
    
    # Minimum ROI expected from fighters
    roi_threshold: float = 1.0           # Lower = more patient with investment
    
    # === PERSONALITY MODIFIERS ===
    # Camp culture affects fighter personality expression
    culture_aggression_mod: float = 0.0  # Added to fighter aggression
    culture_discipline_mod: float = 0.0  # Added to fighter dedication
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "camp_name": self.camp_name,
            "booking_aggression": self.booking_aggression,
            "preferred_rating_diff": self.preferred_rating_diff,
            "short_notice_tolerance": self.short_notice_tolerance,
            "roster_patience": self.roster_patience,
            "prospect_focus": self.prospect_focus,
            "target_roster_fullness": self.target_roster_fullness,
            "training_intensity_bias": self.training_intensity_bias,
            "striking_focus": self.striking_focus,
            "grappling_focus": self.grappling_focus,
            "conditioning_focus": self.conditioning_focus,
            "spending_willingness": self.spending_willingness,
            "roi_threshold": self.roi_threshold,
            "culture_aggression_mod": self.culture_aggression_mod,
            "culture_discipline_mod": self.culture_discipline_mod,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampAIConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def generate_camp_ai_config(camp_id: str, camp_name: str = "") -> CampAIConfig:
    """
    Generate unique AI configuration for a camp.
    
    DISTRIBUTION OF CAMP ARCHETYPES:
    ================================
    
    30% - BALANCED CAMPS
    - All values near defaults
    - Moderate in all approaches
    
    20% - AGGRESSIVE CAMPS
    - High booking_aggression (1.2-1.5)
    - Negative preferred_rating_diff (take challenges)
    - Higher training intensity
    
    15% - CONSERVATIVE CAMPS
    - Low booking_aggression (0.6-0.9)
    - Positive preferred_rating_diff (favorable fights)
    - More patient with roster
    
    15% - PROSPECT FACTORIES
    - High prospect_focus (0.7-1.0)
    - More patient roster management
    - Lower spending (develop cheap talent)
    
    10% - VETERAN COLLECTORS
    - Low prospect_focus (0.0-0.3)
    - High spending willingness
    - Less patient (expect immediate results)
    
    10% - SPECIALIST CAMPS
    - Extreme focus on one area (striking/grappling)
    - Strong culture modifiers
    """
    archetype_roll = random.random()
    
    if archetype_roll < 0.30:
        # BALANCED
        return CampAIConfig(
            camp_id=camp_id,
            camp_name=camp_name,
            booking_aggression=random.uniform(0.9, 1.1),
            preferred_rating_diff=random.randint(-3, 3),
            short_notice_tolerance=random.uniform(0.4, 0.6),
            roster_patience=random.uniform(0.4, 0.6),
            prospect_focus=random.uniform(0.4, 0.6),
            target_roster_fullness=random.uniform(0.7, 0.9),
            training_intensity_bias=random.uniform(-0.1, 0.1),
            striking_focus=0.33,
            grappling_focus=0.33,
            conditioning_focus=0.34,
            spending_willingness=random.uniform(0.4, 0.6),
            roi_threshold=random.uniform(0.9, 1.1),
        )
    
    elif archetype_roll < 0.50:
        # AGGRESSIVE
        return CampAIConfig(
            camp_id=camp_id,
            camp_name=camp_name,
            booking_aggression=random.uniform(1.2, 1.5),
            preferred_rating_diff=random.randint(-10, -3),
            short_notice_tolerance=random.uniform(0.6, 0.9),
            roster_patience=random.uniform(0.3, 0.5),
            prospect_focus=random.uniform(0.3, 0.6),
            target_roster_fullness=random.uniform(0.8, 1.0),
            training_intensity_bias=random.uniform(0.1, 0.3),
            striking_focus=random.uniform(0.35, 0.45),
            grappling_focus=random.uniform(0.25, 0.35),
            conditioning_focus=random.uniform(0.25, 0.35),
            spending_willingness=random.uniform(0.5, 0.8),
            roi_threshold=random.uniform(0.7, 0.9),
            culture_aggression_mod=random.uniform(0.05, 0.15),
        )
    
    elif archetype_roll < 0.65:
        # CONSERVATIVE
        return CampAIConfig(
            camp_id=camp_id,
            camp_name=camp_name,
            booking_aggression=random.uniform(0.6, 0.9),
            preferred_rating_diff=random.randint(3, 10),
            short_notice_tolerance=random.uniform(0.1, 0.4),
            roster_patience=random.uniform(0.6, 0.8),
            prospect_focus=random.uniform(0.4, 0.6),
            target_roster_fullness=random.uniform(0.6, 0.8),
            training_intensity_bias=random.uniform(-0.2, 0.0),
            striking_focus=0.30,
            grappling_focus=0.35,
            conditioning_focus=0.35,
            spending_willingness=random.uniform(0.3, 0.5),
            roi_threshold=random.uniform(1.1, 1.3),
            culture_discipline_mod=random.uniform(0.05, 0.15),
        )
    
    elif archetype_roll < 0.80:
        # PROSPECT FACTORY
        return CampAIConfig(
            camp_id=camp_id,
            camp_name=camp_name,
            booking_aggression=random.uniform(0.8, 1.1),
            preferred_rating_diff=random.randint(0, 5),
            short_notice_tolerance=random.uniform(0.4, 0.7),
            roster_patience=random.uniform(0.7, 0.9),
            prospect_focus=random.uniform(0.7, 1.0),
            target_roster_fullness=random.uniform(0.8, 1.0),
            training_intensity_bias=random.uniform(0.0, 0.2),
            striking_focus=0.33,
            grappling_focus=0.33,
            conditioning_focus=0.34,
            spending_willingness=random.uniform(0.2, 0.4),
            roi_threshold=random.uniform(0.6, 0.8),
        )
    
    elif archetype_roll < 0.90:
        # VETERAN COLLECTOR
        return CampAIConfig(
            camp_id=camp_id,
            camp_name=camp_name,
            booking_aggression=random.uniform(1.0, 1.3),
            preferred_rating_diff=random.randint(-5, 0),
            short_notice_tolerance=random.uniform(0.5, 0.8),
            roster_patience=random.uniform(0.2, 0.4),
            prospect_focus=random.uniform(0.0, 0.3),
            target_roster_fullness=random.uniform(0.7, 0.9),
            training_intensity_bias=random.uniform(-0.1, 0.1),
            striking_focus=0.33,
            grappling_focus=0.33,
            conditioning_focus=0.34,
            spending_willingness=random.uniform(0.7, 1.0),
            roi_threshold=random.uniform(1.2, 1.5),
        )
    
    else:
        # SPECIALIST
        specialty = random.choice(["striking", "grappling", "conditioning"])
        if specialty == "striking":
            striking, grappling, conditioning = 0.55, 0.25, 0.20
            culture_mod = random.uniform(0.05, 0.15)
        elif specialty == "grappling":
            striking, grappling, conditioning = 0.20, 0.55, 0.25
            culture_mod = random.uniform(-0.05, 0.10)
        else:
            striking, grappling, conditioning = 0.25, 0.25, 0.50
            culture_mod = random.uniform(0.0, 0.10)
        
        return CampAIConfig(
            camp_id=camp_id,
            camp_name=camp_name,
            booking_aggression=random.uniform(0.8, 1.2),
            preferred_rating_diff=random.randint(-5, 5),
            short_notice_tolerance=random.uniform(0.3, 0.6),
            roster_patience=random.uniform(0.4, 0.7),
            prospect_focus=random.uniform(0.4, 0.7),
            target_roster_fullness=random.uniform(0.7, 0.9),
            training_intensity_bias=random.uniform(-0.1, 0.2),
            striking_focus=striking,
            grappling_focus=grappling,
            conditioning_focus=conditioning,
            spending_willingness=random.uniform(0.4, 0.7),
            roi_threshold=random.uniform(0.9, 1.1),
            culture_aggression_mod=culture_mod,
        )


# ============================================================================
# WORLD STATE TRACKING
# ============================================================================

@dataclass
class FighterWorldState:
    """
    Tracks a fighter's state in the world simulation.
    
    This is the AI's view of the fighter for decision-making.
    """
    fighter_id: str
    name: str
    age: int
    
    # Camp association
    camp_id: Optional[str] = None
    is_player_fighter: bool = False
    
    # Current status
    is_active: bool = True
    is_injured: bool = False
    injury_weeks_remaining: int = 0
    is_retired: bool = False
    
    # Fight status
    has_scheduled_fight: bool = False
    scheduled_fight_week: Optional[int] = None
    weeks_since_last_fight: int = 0
    
    # Training status
    in_training_camp: bool = False
    training_week: int = 0
    training_intensity: str = "MODERATE"
    
    # Performance stats
    rating: int = 50
    rank: Optional[int] = None
    is_champion: bool = False
    
    # Record
    wins: int = 0
    losses: int = 0
    win_streak: int = 0
    lose_streak: int = 0
    ko_wins: int = 0
    ko_losses: int = 0
    
    # Recent performance (last 5 fights)
    recent_wins: int = 0
    recent_losses: int = 0
    
    # Fatigue and condition
    fatigue: int = 0
    
    # AI personality
    personality: Optional[FighterPersonality] = None
    
    # Relationships
    rival_ids: List[str] = field(default_factory=list)
    lost_to_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "age": self.age,
            "camp_id": self.camp_id,
            "is_player_fighter": self.is_player_fighter,
            "is_active": self.is_active,
            "is_injured": self.is_injured,
            "injury_weeks_remaining": self.injury_weeks_remaining,
            "is_retired": self.is_retired,
            "has_scheduled_fight": self.has_scheduled_fight,
            "scheduled_fight_week": self.scheduled_fight_week,
            "weeks_since_last_fight": self.weeks_since_last_fight,
            "in_training_camp": self.in_training_camp,
            "training_week": self.training_week,
            "training_intensity": self.training_intensity,
            "rating": self.rating,
            "rank": self.rank,
            "is_champion": self.is_champion,
            "wins": self.wins,
            "losses": self.losses,
            "win_streak": self.win_streak,
            "lose_streak": self.lose_streak,
            "ko_wins": self.ko_wins,
            "ko_losses": self.ko_losses,
            "recent_wins": self.recent_wins,
            "recent_losses": self.recent_losses,
            "fatigue": self.fatigue,
            "personality": self.personality.to_dict() if self.personality else None,
            "rival_ids": self.rival_ids.copy(),
            "lost_to_ids": self.lost_to_ids.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FighterWorldState":
        personality_data = data.pop("personality", None)
        instance = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if personality_data:
            instance.personality = FighterPersonality.from_dict(personality_data)
        return instance


@dataclass
class CampWorldState:
    """
    Tracks a camp's state in the world simulation.
    """
    camp_id: str
    name: str
    is_player_camp: bool = False
    
    # Roster
    fighter_ids: List[str] = field(default_factory=list)
    max_roster_size: int = 15
    
    # Finances
    budget: int = 100000
    monthly_expenses: int = 10000
    
    # AI configuration
    ai_config: Optional[CampAIConfig] = None
    
    # Performance tracking
    total_wins: int = 0
    total_losses: int = 0
    champions: List[str] = field(default_factory=list)
    
    # Scouting
    scouted_prospects: List[str] = field(default_factory=list)
    
    @property
    def roster_size(self) -> int:
        return len(self.fighter_ids)
    
    @property
    def has_roster_space(self) -> bool:
        return self.roster_size < self.max_roster_size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "name": self.name,
            "is_player_camp": self.is_player_camp,
            "fighter_ids": self.fighter_ids.copy(),
            "max_roster_size": self.max_roster_size,
            "budget": self.budget,
            "monthly_expenses": self.monthly_expenses,
            "ai_config": self.ai_config.to_dict() if self.ai_config else None,
            "total_wins": self.total_wins,
            "total_losses": self.total_losses,
            "champions": self.champions.copy(),
            "scouted_prospects": self.scouted_prospects.copy(),
        }


# ============================================================================
# DECISION LOGGING
# ============================================================================

@dataclass
class AIDecisionLog:
    """
    Detailed log of an AI decision for debugging and transparency.
    """
    timestamp: int  # Week number
    decision_type: str
    actor_id: str  # Camp or fighter making decision
    actor_name: str
    trigger: DecisionTrigger
    
    # Decision details
    subject: str  # What the decision is about
    base_probability: float
    modifiers: List[Tuple[str, float]]
    final_probability: float
    roll: float
    result: bool
    result_description: str
    
    def format(self) -> List[str]:
        """Format log entry for display."""
        lines = [
            f"╔══ DECISION LOG (Week {self.timestamp}) ══╗",
            f"║ Actor: {self.actor_name} ({self.actor_id})",
            f"║ Type: {self.decision_type}",
            f"║ Trigger: {self.trigger.value}",
            f"║ Subject: {self.subject}",
            f"╟─────────────────────────────────╢",
            f"║ Base: {self.base_probability*100:.0f}%",
        ]
        
        for reason, mod in self.modifiers:
            sign = "+" if mod >= 0 else ""
            lines.append(f"║   {reason}: {sign}{mod*100:.0f}%")
        
        lines.extend([
            f"╟─────────────────────────────────╢",
            f"║ Final: {self.final_probability*100:.0f}%",
            f"║ Roll: {self.roll*100:.0f}",
            f"║ Result: {'✅ YES' if self.result else '❌ NO'}",
            f"║ {self.result_description}",
            f"╚═════════════════════════════════╝",
        ])
        
        return lines


# ============================================================================
# WORLD INTEGRATION ENGINE
# ============================================================================

class WorldIntegrationEngine:
    """
    The central AI brain that makes the world simulation run.
    
    This engine:
    1. Tracks all fighters and camps
    2. Makes AI decisions each week
    3. Logs all decisions with full transparency
    4. Connects all game systems together
    
    DECISION SCHEDULE:
    =================
    
    EVERY WEEK:
    - Process pending fight offers (for AI camps)
    - Select training intensity for fighters in camp
    - Check if fighters should seek fights
    
    BI-WEEKLY (weeks 2, 4, 6...):
    - Roster evaluation (release decisions)
    - Free agent scouting
    
    MONTHLY (week 1 of each month):
    - Retirement checks for 33+ fighters
    - Age-based degradation
    - Target selection / callouts
    
    QUARTERLY:
    - Camp strategy review
    - Long-term planning
    """
    
    def __init__(self):
        # State tracking
        self.fighters: Dict[str, FighterWorldState] = {}
        self.camps: Dict[str, CampWorldState] = {}
        self.player_camp_id: Optional[str] = None
        
        # AI engine for decisions
        self.decision_engine = create_ai_engine()
        
        # Pending offers
        self.pending_offers: Dict[str, List[Dict[str, Any]]] = {}  # fighter_id -> offers
        
        # Decision log
        self.decision_log: List[AIDecisionLog] = []
        self.log_decisions: bool = True  # Toggle for performance
        
        # Week tracking
        self.current_week: int = 0
        
        # Callbacks
        self._on_fight_accepted: Optional[Callable] = None
        self._on_fighter_released: Optional[Callable] = None
        self._on_fighter_signed: Optional[Callable] = None
        self._on_retirement: Optional[Callable] = None
        self._on_training_selected: Optional[Callable] = None
    
    # =========================================================================
    # REGISTRATION
    # =========================================================================
    
    def register_fighter(
        self,
        fighter_id: str,
        name: str,
        age: int,
        rating: int = 50,
        camp_id: Optional[str] = None,
        is_player_fighter: bool = False,
        wins: int = 0,
        losses: int = 0,
        **kwargs
    ) -> FighterWorldState:
        """
        Register a fighter in the world.
        
        Generates personality if not provided.
        """
        personality = kwargs.pop("personality", None)
        if personality is None:
            personality = generate_fighter_personality(
                fighter_id=fighter_id,
                age=age,
                wins=wins,
                losses=losses,
            )
        
        state = FighterWorldState(
            fighter_id=fighter_id,
            name=name,
            age=age,
            rating=rating,
            camp_id=camp_id,
            is_player_fighter=is_player_fighter,
            wins=wins,
            losses=losses,
            personality=personality,
            **kwargs
        )
        
        self.fighters[fighter_id] = state
        
        # Add to camp roster if applicable
        if camp_id and camp_id in self.camps:
            if fighter_id not in self.camps[camp_id].fighter_ids:
                self.camps[camp_id].fighter_ids.append(fighter_id)
        
        return state
    
    def register_camp(
        self,
        camp_id: str,
        name: str,
        is_player_camp: bool = False,
        budget: int = 100000,
        max_roster: int = 15,
        ai_config: Optional[CampAIConfig] = None,
    ) -> CampWorldState:
        """
        Register a camp in the world.
        
        Generates AI config if not provided.
        """
        if ai_config is None and not is_player_camp:
            ai_config = generate_camp_ai_config(camp_id, name)
        
        state = CampWorldState(
            camp_id=camp_id,
            name=name,
            is_player_camp=is_player_camp,
            budget=budget,
            max_roster_size=max_roster,
            ai_config=ai_config,
        )
        
        self.camps[camp_id] = state
        
        if is_player_camp:
            self.player_camp_id = camp_id
        
        return state
    
    def set_player_camp(self, camp_id: str) -> None:
        """Set which camp is player-controlled."""
        self.player_camp_id = camp_id
        if camp_id in self.camps:
            self.camps[camp_id].is_player_camp = True
    
    # =========================================================================
    # OFFER MANAGEMENT
    # =========================================================================
    
    def add_fight_offer(
        self,
        target_fighter_id: str,
        opponent_id: str,
        opponent_name: str,
        opponent_rating: int,
        opponent_rank: Optional[int],
        is_title_fight: bool,
        is_main_event: bool,
        weeks_out: int,
        purse: int,
        offer_id: Optional[str] = None,
    ) -> None:
        """Add a fight offer for an AI to evaluate."""
        if target_fighter_id not in self.pending_offers:
            self.pending_offers[target_fighter_id] = []
        
        self.pending_offers[target_fighter_id].append({
            "offer_id": offer_id or f"offer_{len(self.decision_log)}",
            "opponent_id": opponent_id,
            "opponent_name": opponent_name,
            "opponent_rating": opponent_rating,
            "opponent_rank": opponent_rank,
            "is_title_fight": is_title_fight,
            "is_main_event": is_main_event,
            "weeks_out": weeks_out,
            "purse": purse,
        })
    
    # =========================================================================
    # WEEKLY PROCESSING
    # =========================================================================
    
    def process_week(self, week_number: int) -> List[AIDecisionLog]:
        """
        Process all AI decisions for a week.
        
        Returns list of decision logs from this week.
        """
        self.current_week = week_number
        week_logs: List[AIDecisionLog] = []
        
        # Get all AI camps (not player)
        ai_camps = [c for c in self.camps.values() if not c.is_player_camp]
        
        # === PROCESS PENDING FIGHT OFFERS ===
        for camp in ai_camps:
            for fighter_id in camp.fighter_ids:
                if fighter_id in self.pending_offers:
                    logs = self._process_fight_offers(fighter_id, camp)
                    week_logs.extend(logs)
        
        # === TRAINING INTENSITY SELECTION ===
        for camp in ai_camps:
            for fighter_id in camp.fighter_ids:
                fighter = self.fighters.get(fighter_id)
                if fighter and fighter.in_training_camp:
                    log = self._select_training_intensity(fighter, camp)
                    if log:
                        week_logs.append(log)
        
        # === ACTIVITY CHECKS (should fighter seek fight?) ===
        for camp in ai_camps:
            for fighter_id in camp.fighter_ids:
                fighter = self.fighters.get(fighter_id)
                if fighter and not fighter.has_scheduled_fight and not fighter.is_injured:
                    log = self._check_fighter_activity(fighter, camp)
                    if log:
                        week_logs.append(log)
        
        # === BI-WEEKLY: Roster and scouting ===
        if week_number % 2 == 0:
            for camp in ai_camps:
                logs = self._evaluate_roster(camp)
                week_logs.extend(logs)
        
        # === MONTHLY: Retirement and targets ===
        if week_number % 4 == 1:  # First week of month
            for fighter in self.fighters.values():
                if fighter.age >= 33 and not fighter.is_retired:
                    log = self._check_retirement(fighter)
                    if log:
                        week_logs.append(log)
        
        # Store logs
        if self.log_decisions:
            self.decision_log.extend(week_logs)
        
        return week_logs
    
    # =========================================================================
    # FIGHT OFFER PROCESSING
    # =========================================================================
    
    def _process_fight_offers(
        self,
        fighter_id: str,
        camp: CampWorldState
    ) -> List[AIDecisionLog]:
        """
        Process pending fight offers for a fighter.
        
        TRIGGER: Fight offer received
        
        BASE PROBABILITY: 50%
        
        MODIFIERS FROM AI BEHAVIOR:
        - Personality (mentality, risk profile)
        - Matchup (rating diff, ranking)
        - Timing (weeks out, activity)
        - Special (title, revenge, etc.)
        
        CAMP MODIFIERS:
        - booking_aggression: ±10%
        - preferred_rating_diff: affects "favorable" calculation
        - short_notice_tolerance: ±15% for short notice fights
        """
        logs: List[AIDecisionLog] = []
        
        fighter = self.fighters.get(fighter_id)
        if not fighter or not fighter.personality:
            return logs
        
        offers = self.pending_offers.get(fighter_id, [])
        if not offers:
            return logs
        
        config = camp.ai_config
        
        for offer in offers:
            # Check if already scheduled
            if fighter.has_scheduled_fight:
                break
            
            # Get decision from AI engine
            result, breakdown = self.decision_engine.evaluate_fight_offer(
                personality=fighter.personality,
                fighter_rating=fighter.rating,
                fighter_rank=fighter.rank,
                is_champion=fighter.is_champion,
                wins=fighter.wins,
                losses=fighter.losses,
                win_streak=fighter.win_streak,
                lose_streak=fighter.lose_streak,
                weeks_since_fight=fighter.weeks_since_last_fight,
                opponent_rating=offer["opponent_rating"],
                opponent_rank=offer["opponent_rank"],
                opponent_id=offer["opponent_id"],
                is_title_fight=offer["is_title_fight"],
                is_main_event=offer["is_main_event"],
                weeks_out=offer["weeks_out"],
                purse=offer["purse"],
                fought_before=offer["opponent_id"] in fighter.lost_to_ids,
                lost_to_opponent=offer["opponent_id"] in fighter.lost_to_ids,
            )
            
            # Apply camp modifiers
            camp_mods: List[Tuple[str, float]] = []
            
            if config:
                # Booking aggression
                aggression_mod = (config.booking_aggression - 1.0) * 0.10
                if abs(aggression_mod) > 0.01:
                    camp_mods.append(("Camp booking aggression", aggression_mod))
                
                # Short notice adjustment
                if offer["weeks_out"] < 4:
                    sn_mod = (config.short_notice_tolerance - 0.5) * 0.15
                    camp_mods.append(("Camp short notice policy", sn_mod))
            
            # Recalculate with camp mods
            adjusted_prob = breakdown.final_probability + sum(m for _, m in camp_mods)
            adjusted_prob = max(0.05, min(0.95, adjusted_prob))
            
            # New roll with camp adjustment
            final_result = result
            if camp_mods:
                new_roll = random.random()
                final_result = new_roll < adjusted_prob
            
            # Log the decision
            log = AIDecisionLog(
                timestamp=self.current_week,
                decision_type="Fight Offer",
                actor_id=camp.camp_id,
                actor_name=f"{camp.name} / {fighter.name}",
                trigger=DecisionTrigger.FIGHT_OFFER_RECEIVED,
                subject=f"vs {offer['opponent_name']}",
                base_probability=breakdown.base_probability,
                modifiers=breakdown.modifiers + camp_mods,
                final_probability=adjusted_prob,
                roll=breakdown.roll,
                result=final_result,
                result_description=f"{'Accepted' if final_result else 'Declined'} fight vs {offer['opponent_name']}",
            )
            logs.append(log)
            
            # Handle acceptance
            if final_result:
                fighter.has_scheduled_fight = True
                fighter.scheduled_fight_week = self.current_week + offer["weeks_out"]
                
                if self._on_fight_accepted:
                    self._on_fight_accepted(fighter_id, offer)
        
        # Clear processed offers
        self.pending_offers[fighter_id] = []
        
        return logs
    
    # =========================================================================
    # TRAINING INTENSITY
    # =========================================================================
    
    def _select_training_intensity(
        self,
        fighter: FighterWorldState,
        camp: CampWorldState
    ) -> Optional[AIDecisionLog]:
        """
        Select training intensity for a fighter in camp.
        
        TRIGGER: Weekly check (fighter in training camp)
        
        BASE DISTRIBUTION:
        - LIGHT: 15%
        - MODERATE: 50%
        - INTENSE: 30%
        - EXTREME: 5%
        
        MODIFIERS:
        - Dedication (OBSESSED: +25% EXTREME, LAZY: +30% LIGHT)
        - Fight timing (taper vs peak)
        - Fatigue level
        - Age
        - Camp culture
        """
        if not fighter.personality:
            return None
        
        # Calculate weeks until fight
        weeks_until = None
        if fighter.scheduled_fight_week:
            weeks_until = fighter.scheduled_fight_week - self.current_week
        
        # Coming off loss?
        coming_off_loss = fighter.lose_streak > 0
        coming_off_ko = fighter.ko_losses > 0 and fighter.lose_streak > 0  # Simplified check
        
        intensity, breakdown = self.decision_engine.select_training_intensity(
            personality=fighter.personality,
            weeks_until_fight=weeks_until,
            current_fatigue=fighter.fatigue,
            age=fighter.age,
            coming_off_loss=coming_off_loss,
            coming_off_ko_loss=coming_off_ko,
        )
        
        # Apply camp culture modifier
        camp_mods: List[Tuple[str, float]] = []
        config = camp.ai_config
        
        if config and abs(config.training_intensity_bias) > 0.01:
            camp_mods.append((
                f"Camp training culture",
                config.training_intensity_bias
            ))
        
        # Update fighter state
        fighter.training_intensity = intensity
        
        if self._on_training_selected:
            self._on_training_selected(fighter.fighter_id, intensity)
        
        return AIDecisionLog(
            timestamp=self.current_week,
            decision_type="Training Intensity",
            actor_id=camp.camp_id,
            actor_name=f"{camp.name} / {fighter.name}",
            trigger=DecisionTrigger.WEEKLY_CHECK,
            subject=f"Training week {fighter.training_week}",
            base_probability=0.0,  # N/A for selection
            modifiers=breakdown.modifiers + camp_mods,
            final_probability=0.0,
            roll=0.0,
            result=True,
            result_description=f"Selected {intensity} intensity",
        )
    
    # =========================================================================
    # ACTIVITY CHECK
    # =========================================================================
    
    def _check_fighter_activity(
        self,
        fighter: FighterWorldState,
        camp: CampWorldState
    ) -> Optional[AIDecisionLog]:
        """
        Check if a fighter should actively seek a fight.
        
        TRIGGER: Weekly check (no scheduled fight, not injured)
        
        BASE PROBABILITY (by activity preference):
        - VERY_ACTIVE: 80% after 6 weeks
        - ACTIVE: 70% after 10 weeks
        - NORMAL: 60% after 14 weeks
        - SELECTIVE: 40% after 20 weeks
        - INACTIVE: 25% after 30 weeks
        
        MODIFIERS:
        - Fatigue: -30% if high
        - Age: -15% if 36+
        - WARRIOR mentality: +20%
        - Camp booking aggression: ±15%
        """
        if not fighter.personality:
            return None
        
        result, breakdown = self.decision_engine.should_seek_fight(
            personality=fighter.personality,
            weeks_since_last_fight=fighter.weeks_since_last_fight,
            has_scheduled_fight=fighter.has_scheduled_fight,
            is_injured=fighter.is_injured,
            is_in_camp=fighter.in_training_camp,
            current_fatigue=fighter.fatigue,
            age=fighter.age,
        )
        
        if not result:
            return None  # Not seeking, no need to log
        
        # Apply camp modifier
        camp_mods: List[Tuple[str, float]] = []
        config = camp.ai_config
        
        if config:
            booking_mod = (config.booking_aggression - 1.0) * 0.15
            if abs(booking_mod) > 0.01:
                camp_mods.append(("Camp booking style", booking_mod))
        
        return AIDecisionLog(
            timestamp=self.current_week,
            decision_type="Seek Fight",
            actor_id=camp.camp_id,
            actor_name=f"{camp.name} / {fighter.name}",
            trigger=DecisionTrigger.WEEKLY_CHECK,
            subject=f"Activity check ({fighter.weeks_since_last_fight} weeks since fight)",
            base_probability=breakdown.base_probability,
            modifiers=breakdown.modifiers + camp_mods,
            final_probability=breakdown.final_probability,
            roll=breakdown.roll,
            result=result,
            result_description="Actively looking for opponents",
        )
    
    # =========================================================================
    # ROSTER EVALUATION
    # =========================================================================
    
    def _evaluate_roster(self, camp: CampWorldState) -> List[AIDecisionLog]:
        """
        Evaluate roster for potential releases.
        
        TRIGGER: Bi-weekly check
        
        RELEASE PROBABILITY (base: 0%):
        - 0-3 in last 5 fights: +40%
        - Age 38+ and rating <60: +30%
        - Inactive 18+ months: +25%
        - Rating <45: +20%
        
        MODIFIERS:
        - Camp loyalty/patience: -50% max
        - Prospect (age <25): -20%
        - Champion: -100% (never release)
        """
        logs: List[AIDecisionLog] = []
        config = camp.ai_config
        
        for fighter_id in camp.fighter_ids[:]:  # Copy list to allow modification
            fighter = self.fighters.get(fighter_id)
            if not fighter:
                continue
            
            # Never release champions
            if fighter.is_champion:
                continue
            
            # Calculate release probability
            base = 0.0
            modifiers: List[Tuple[str, float]] = []
            
            # Poor recent record
            if fighter.recent_losses >= 3 and fighter.recent_wins == 0:
                modifiers.append(("0-3 in last 5 fights", 0.40))
            elif fighter.recent_losses >= 2:
                modifiers.append(("Losing record recently", 0.20))
            
            # Age and decline
            if fighter.age >= 38 and fighter.rating < 60:
                modifiers.append(("Age 38+ with low rating", 0.30))
            elif fighter.age >= 40:
                modifiers.append(("Age 40+", 0.20))
            
            # Inactivity (convert weeks to months approximation)
            months_inactive = fighter.weeks_since_last_fight // 4
            if months_inactive >= 18:
                modifiers.append(("Inactive 18+ months", 0.25))
            elif months_inactive >= 12:
                modifiers.append(("Inactive 12+ months", 0.15))
            
            # Low rating
            if fighter.rating < 45:
                modifiers.append(("Rating below 45", 0.20))
            elif fighter.rating < 55:
                modifiers.append(("Rating below 55", 0.10))
            
            # Camp patience modifier
            if config:
                patience_reduction = config.roster_patience * 0.50
                modifiers.append(("Camp patience", -patience_reduction))
            
            # Prospect protection
            if fighter.age < 25:
                modifiers.append(("Prospect protection", -0.20))
            
            # Calculate final probability
            final_prob = base + sum(m for _, m in modifiers)
            final_prob = max(0.0, min(0.80, final_prob))
            
            # Roll
            roll = random.random()
            release = roll < final_prob
            
            if final_prob > 0.05:  # Only log if there was meaningful consideration
                log = AIDecisionLog(
                    timestamp=self.current_week,
                    decision_type="Roster Release",
                    actor_id=camp.camp_id,
                    actor_name=camp.name,
                    trigger=DecisionTrigger.WEEKLY_CHECK,
                    subject=fighter.name,
                    base_probability=base,
                    modifiers=modifiers,
                    final_probability=final_prob,
                    roll=roll,
                    result=release,
                    result_description=f"{'Released' if release else 'Retained'} {fighter.name}",
                )
                logs.append(log)
            
            if release:
                # Execute release
                camp.fighter_ids.remove(fighter_id)
                fighter.camp_id = None
                fighter.is_active = True  # Becomes free agent
                
                if self._on_fighter_released:
                    self._on_fighter_released(fighter_id, camp.camp_id)
        
        return logs
    
    # =========================================================================
    # RETIREMENT CHECK
    # =========================================================================
    
    def _check_retirement(self, fighter: FighterWorldState) -> Optional[AIDecisionLog]:
        """
        Check if a fighter should retire.
        
        TRIGGER: Monthly check (age 33+)
        
        BASE PROBABILITY BY AGE:
        - 33-35: 3-8%
        - 36-37: 15%
        - 38-39: 25%
        - 40+: 40%
        
        MODIFIERS:
        - Current champion: +15% (go out on top)
        - Recent losses (0-3): +20%
        - Many KO losses (5+): +30%
        - WARRIOR mentality: -20%
        - High heart: -15%
        - Title shot coming: -25%
        """
        if not fighter.personality:
            return None
        
        if fighter.age < 33 or fighter.is_retired:
            return None
        
        result, breakdown = self.decision_engine.consider_retirement(
            personality=fighter.personality,
            age=fighter.age,
            wins=fighter.wins,
            losses=fighter.losses,
            recent_record=(fighter.recent_wins, fighter.recent_losses),
            is_champion=fighter.is_champion,
            ko_losses_career=fighter.ko_losses,
            months_since_last_win=fighter.weeks_since_last_fight // 4,  # Approximation
            has_title_shot_coming=fighter.has_scheduled_fight and fighter.is_champion,
        )
        
        log = AIDecisionLog(
            timestamp=self.current_week,
            decision_type="Retirement",
            actor_id=fighter.fighter_id,
            actor_name=fighter.name,
            trigger=DecisionTrigger.AGE_MILESTONE,
            subject=f"Age {fighter.age} retirement check",
            base_probability=breakdown.base_probability,
            modifiers=breakdown.modifiers,
            final_probability=breakdown.final_probability,
            roll=breakdown.roll,
            result=result,
            result_description=f"{'Retired' if result else 'Continues fighting'} at age {fighter.age}",
        )
        
        if result:
            fighter.is_retired = True
            fighter.is_active = False
            
            if self._on_retirement:
                self._on_retirement(fighter.fighter_id)
        
        return log
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def on_fight_accepted(self, callback: Callable) -> None:
        """Set callback for when AI accepts a fight."""
        self._on_fight_accepted = callback
    
    def on_fighter_released(self, callback: Callable) -> None:
        """Set callback for when AI releases a fighter."""
        self._on_fighter_released = callback
    
    def on_fighter_signed(self, callback: Callable) -> None:
        """Set callback for when AI signs a fighter."""
        self._on_fighter_signed = callback
    
    def on_retirement(self, callback: Callable) -> None:
        """Set callback for when fighter retires."""
        self._on_retirement = callback
    
    def on_training_selected(self, callback: Callable) -> None:
        """Set callback for training intensity selection."""
        self._on_training_selected = callback
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    def get_fighter(self, fighter_id: str) -> Optional[FighterWorldState]:
        """Get fighter state."""
        return self.fighters.get(fighter_id)
    
    def get_camp(self, camp_id: str) -> Optional[CampWorldState]:
        """Get camp state."""
        return self.camps.get(camp_id)
    
    def get_ai_camps(self) -> List[CampWorldState]:
        """Get all AI-controlled camps."""
        return [c for c in self.camps.values() if not c.is_player_camp]
    
    def get_active_fighters(self) -> List[FighterWorldState]:
        """Get all active (not retired) fighters."""
        return [f for f in self.fighters.values() if not f.is_retired]
    
    def get_free_agents(self) -> List[FighterWorldState]:
        """Get all unsigned fighters."""
        return [f for f in self.fighters.values() 
                if f.camp_id is None and not f.is_retired]
    
    def get_decision_log(
        self,
        count: int = 50,
        decision_type: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> List[AIDecisionLog]:
        """Get recent decision logs with optional filtering."""
        logs = self.decision_log
        
        if decision_type:
            logs = [l for l in logs if l.decision_type == decision_type]
        
        if actor_id:
            logs = [l for l in logs if l.actor_id == actor_id]
        
        return logs[-count:]
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Export state."""
        return {
            "fighters": {k: v.to_dict() for k, v in self.fighters.items()},
            "camps": {k: v.to_dict() for k, v in self.camps.items()},
            "player_camp_id": self.player_camp_id,
            "current_week": self.current_week,
            "pending_offers": self.pending_offers,
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restore state."""
        self.fighters = {
            k: FighterWorldState.from_dict(v) 
            for k, v in data.get("fighters", {}).items()
        }
        # Restore camps (simplified - would need full implementation)
        self.player_camp_id = data.get("player_camp_id")
        self.current_week = data.get("current_week", 0)
        self.pending_offers = data.get("pending_offers", {})


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_world_integration_engine() -> WorldIntegrationEngine:
    """Create a new world integration engine."""
    return WorldIntegrationEngine()


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_camp_config(config: CampAIConfig) -> List[str]:
    """Format camp AI configuration for display."""
    lines = [
        f"═══ CAMP AI PROFILE: {config.camp_name} ═══",
        "",
        "MATCHMAKING:",
        f"  Booking Aggression: {config.booking_aggression:.1f}x",
        f"  Preferred Rating Diff: {config.preferred_rating_diff:+d}",
        f"  Short Notice Tolerance: {config.short_notice_tolerance*100:.0f}%",
        "",
        "ROSTER MANAGEMENT:",
        f"  Patience: {config.roster_patience*100:.0f}%",
        f"  Prospect Focus: {config.prospect_focus*100:.0f}%",
        f"  Target Fullness: {config.target_roster_fullness*100:.0f}%",
        "",
        "TRAINING PHILOSOPHY:",
        f"  Intensity Bias: {config.training_intensity_bias:+.1f}",
        f"  Striking Focus: {config.striking_focus*100:.0f}%",
        f"  Grappling Focus: {config.grappling_focus*100:.0f}%",
        f"  Conditioning: {config.conditioning_focus*100:.0f}%",
        "",
        "FINANCIAL:",
        f"  Spending Willingness: {config.spending_willingness*100:.0f}%",
        f"  ROI Threshold: {config.roi_threshold:.1f}x",
    ]
    return lines


def format_decision_summary(logs: List[AIDecisionLog]) -> List[str]:
    """Format a summary of recent decisions."""
    if not logs:
        return ["No decisions logged."]
    
    lines = [
        "═══ DECISION SUMMARY ═══",
        f"Total decisions: {len(logs)}",
        "",
    ]
    
    # Count by type
    by_type: Dict[str, int] = {}
    accepted = 0
    declined = 0
    
    for log in logs:
        by_type[log.decision_type] = by_type.get(log.decision_type, 0) + 1
        if log.result:
            accepted += 1
        else:
            declined += 1
    
    lines.append("By Type:")
    for dtype, count in sorted(by_type.items()):
        lines.append(f"  {dtype}: {count}")
    
    lines.extend([
        "",
        f"Accepted: {accepted}",
        f"Declined/Failed: {declined}",
    ])
    
    return lines


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Triggers
    "DecisionTrigger",
    
    # Camp config
    "CampAIConfig", "generate_camp_ai_config",
    
    # State tracking
    "FighterWorldState", "CampWorldState",
    
    # Logging
    "AIDecisionLog",
    
    # Engine
    "WorldIntegrationEngine", "create_world_integration_engine",
    
    # Display
    "format_camp_config", "format_decision_summary",
]
