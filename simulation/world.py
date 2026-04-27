# simulation/world.py
# Module 30: World Simulation
# Lines: ~1650
#
# The heartbeat of Cage Dynasty - handles weekly progression,
# AI decisions, event scheduling, and world state management.

"""
Cage Dynasty - World Simulation

Manages the living, breathing MMA world:
- Weekly time progression
- AI camp decision-making with personality variance
- Event scheduling and execution
- Fighter lifecycle (aging, injuries, retirements)
- Prospect generation
- Year-End Awards (Fighter/Fight/KO/Prospect of the Year)

Usage:
    from simulation.world import (
        WorldSimulation,
        CampAI,
        CampPersonality,
        YearEndAwards,
    )
    
    world = WorldSimulation()
    world.initialize_world(num_fighters=150)
    
    # Advance one week
    events = world.advance_week()
    
    # Record fight result for yearly tracking
    world.record_fight_result(
        winner_id="f1", winner_name="Jones",
        loser_id="f2", loser_name="Smith",
        method="KO", round_ended=2,
        event_name="DFC 100",
    )
    
    # Get year-end awards (after week 52)
    awards = world.get_year_end_awards(2025)
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from enum import Enum

from core.events import emit
from core.calendar import GameCalendar, GameDate


# ============================================================================
# AI PERSONALITY SYSTEM
# ============================================================================

class CampPhilosophy(Enum):
    """Core training philosophy of a camp"""
    STRIKER_FACTORY = "striker_factory"      # Develops elite strikers
    GRAPPLING_ACADEMY = "grappling_academy"  # Wrestling/BJJ focused
    WELL_ROUNDED = "well_rounded"            # Balanced development
    CARDIO_KINGS = "cardio_kings"            # Endurance specialists
    POWER_HOUSE = "power_house"              # Heavy hitters


class RiskTolerance(Enum):
    """How much risk a camp is willing to take"""
    CONSERVATIVE = "conservative"  # Safe matchups, protect fighters
    MODERATE = "moderate"          # Balanced approach
    AGGRESSIVE = "aggressive"      # Chase big fights, take risks
    RECKLESS = "reckless"          # Will fight anyone, anytime


class TalentStrategy(Enum):
    """How camp approaches talent acquisition"""
    PROSPECT_DEVELOPER = "prospect_developer"  # Signs young, develops
    VETERAN_COLLECTOR = "veteran_collector"    # Signs experienced fighters
    ELITE_HUNTER = "elite_hunter"              # Only wants top talent
    OPPORTUNIST = "opportunist"                # Takes any good deal
    HOMETOWN_HERO = "hometown_hero"            # Prefers local/regional fighters


class NegotiationStyle(Enum):
    """How camp negotiates contracts"""
    GENEROUS = "generous"        # Pays above market
    FAIR = "fair"                # Market rate
    FRUGAL = "frugal"            # Below market, quantity focus
    HARDBALL = "hardball"        # Aggressive negotiation


@dataclass
class CampPersonality:
    """
    Defines an AI camp's unique personality and decision-making tendencies.
    
    Each camp has distinct traits that affect how they:
    - Sign and develop fighters
    - Accept/reject fight offers
    - Manage finances
    - Build their roster
    """
    camp_id: str
    
    # Core traits
    philosophy: CampPhilosophy = CampPhilosophy.WELL_ROUNDED
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    talent_strategy: TalentStrategy = TalentStrategy.OPPORTUNIST
    negotiation_style: NegotiationStyle = NegotiationStyle.FAIR
    
    # Numeric traits (0-100)
    aggression: int = 50          # How quickly they push fighters
    patience: int = 50            # Willingness to develop slowly
    loyalty: int = 50             # Sticks with losing fighters
    ambition: int = 50            # Pursues title shots
    financial_savvy: int = 50     # Money management
    scouting_ability: int = 50    # Finding good prospects
    
    # Preferences
    preferred_weight_classes: List[str] = field(default_factory=list)
    rival_camps: List[str] = field(default_factory=list)
    
    # Behavioral modifiers
    activity_level: float = 1.0   # How often they book fights (0.5-1.5)
    title_focus: float = 1.0      # Priority on title shots (0.5-2.0)
    prospect_interest: float = 1.0  # Interest in young fighters (0.5-2.0)
    
    def get_fight_acceptance_modifier(self, is_favorable: bool) -> float:
        """Get modifier for accepting fight offers"""
        base = 0.5
        
        # Risk tolerance affects acceptance
        if self.risk_tolerance == RiskTolerance.AGGRESSIVE:
            base += 0.2
        elif self.risk_tolerance == RiskTolerance.RECKLESS:
            base += 0.35
        elif self.risk_tolerance == RiskTolerance.CONSERVATIVE:
            base -= 0.15
        
        # Favorable fights more likely accepted
        if is_favorable:
            base += 0.25
        
        # Ambition affects title fight acceptance
        base += (self.ambition - 50) / 200
        
        return min(0.95, max(0.1, base))
    
    def get_signing_interest(self, fighter_age: int, fighter_rating: int) -> float:
        """Get interest level in signing a fighter"""
        interest = 0.5
        
        # Strategy affects age preference
        if self.talent_strategy == TalentStrategy.PROSPECT_DEVELOPER:
            if fighter_age <= 24:
                interest += 0.3
            elif fighter_age >= 32:
                interest -= 0.3
        elif self.talent_strategy == TalentStrategy.VETERAN_COLLECTOR:
            if fighter_age >= 30:
                interest += 0.2
            elif fighter_age <= 23:
                interest -= 0.2
        elif self.talent_strategy == TalentStrategy.ELITE_HUNTER:
            if fighter_rating >= 80:
                interest += 0.4
            elif fighter_rating < 65:
                interest -= 0.4
        
        # Scouting ability affects prospect evaluation
        if fighter_age <= 24:
            interest += (self.scouting_ability - 50) / 200
        
        return min(1.0, max(0.0, interest))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "camp_id": self.camp_id,
            "philosophy": self.philosophy.value,
            "risk_tolerance": self.risk_tolerance.value,
            "talent_strategy": self.talent_strategy.value,
            "negotiation_style": self.negotiation_style.value,
            "aggression": self.aggression,
            "patience": self.patience,
            "loyalty": self.loyalty,
            "ambition": self.ambition,
            "financial_savvy": self.financial_savvy,
            "scouting_ability": self.scouting_ability,
            "preferred_weight_classes": self.preferred_weight_classes.copy(),
            "rival_camps": self.rival_camps.copy(),
            "activity_level": self.activity_level,
            "title_focus": self.title_focus,
            "prospect_interest": self.prospect_interest,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampPersonality":
        """Deserialize from dictionary"""
        return cls(
            camp_id=data["camp_id"],
            philosophy=CampPhilosophy(data.get("philosophy", "well_rounded")),
            risk_tolerance=RiskTolerance(data.get("risk_tolerance", "moderate")),
            talent_strategy=TalentStrategy(data.get("talent_strategy", "opportunist")),
            negotiation_style=NegotiationStyle(data.get("negotiation_style", "fair")),
            aggression=data.get("aggression", 50),
            patience=data.get("patience", 50),
            loyalty=data.get("loyalty", 50),
            ambition=data.get("ambition", 50),
            financial_savvy=data.get("financial_savvy", 50),
            scouting_ability=data.get("scouting_ability", 50),
            preferred_weight_classes=data.get("preferred_weight_classes", []),
            rival_camps=data.get("rival_camps", []),
            activity_level=data.get("activity_level", 1.0),
            title_focus=data.get("title_focus", 1.0),
            prospect_interest=data.get("prospect_interest", 1.0),
        )


def generate_camp_personality(camp_id: str, camp_name: str = "") -> CampPersonality:
    """
    Generate a unique personality for an AI camp.
    
    Creates variance so each camp behaves differently.
    """
    # Randomly select core traits
    philosophy = random.choice(list(CampPhilosophy))
    risk_tolerance = random.choice(list(RiskTolerance))
    talent_strategy = random.choice(list(TalentStrategy))
    negotiation_style = random.choice(list(NegotiationStyle))
    
    # Generate numeric traits with variance
    def trait_value() -> int:
        # Bell curve around 50, but allow extremes
        base = random.gauss(50, 20)
        return max(10, min(90, int(base)))
    
    # Generate activity modifiers
    activity = random.uniform(0.6, 1.4)
    title_focus = random.uniform(0.5, 2.0)
    prospect_interest = random.uniform(0.5, 2.0)
    
    # Adjust based on strategy for coherence
    if talent_strategy == TalentStrategy.PROSPECT_DEVELOPER:
        prospect_interest = max(prospect_interest, 1.3)
    elif talent_strategy == TalentStrategy.ELITE_HUNTER:
        prospect_interest = min(prospect_interest, 0.8)
        title_focus = max(title_focus, 1.3)
    
    if risk_tolerance == RiskTolerance.AGGRESSIVE:
        activity = max(activity, 1.1)
    elif risk_tolerance == RiskTolerance.CONSERVATIVE:
        activity = min(activity, 1.0)
    
    # Random weight class preferences (1-3 classes)
    all_classes = [
        "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
        "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
    ]
    num_preferred = random.randint(1, 3)
    preferred = random.sample(all_classes, num_preferred)
    
    return CampPersonality(
        camp_id=camp_id,
        philosophy=philosophy,
        risk_tolerance=risk_tolerance,
        talent_strategy=talent_strategy,
        negotiation_style=negotiation_style,
        aggression=trait_value(),
        patience=trait_value(),
        loyalty=trait_value(),
        ambition=trait_value(),
        financial_savvy=trait_value(),
        scouting_ability=trait_value(),
        preferred_weight_classes=preferred,
        activity_level=activity,
        title_focus=title_focus,
        prospect_interest=prospect_interest,
    )


# ============================================================================
# AI CAMP DECISION MAKER
# ============================================================================

@dataclass
class FightOffer:
    """Represents a fight offer to evaluate"""
    opponent_id: str
    opponent_name: str
    opponent_rating: int
    opponent_rank: Optional[int]
    is_title_fight: bool
    is_main_event: bool
    weeks_until_fight: int
    purse: int
    
    @property
    def is_favorable(self) -> bool:
        """Quick check if offer seems favorable"""
        return self.purse > 0 and self.weeks_until_fight >= 6


@dataclass
class CampAI:
    """
    AI decision maker for a training camp.
    
    Makes decisions about:
    - Accepting/rejecting fight offers
    - Which fighters to sign
    - Training priorities
    - Financial management
    """
    personality: CampPersonality
    
    # State tracking
    recent_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    def evaluate_fight_offer(
        self,
        fighter_id: str,
        fighter_rating: int,
        fighter_rank: Optional[int],
        offer: FightOffer,
        fighter_is_champion: bool = False,
        current_win_streak: int = 0,
        current_lose_streak: int = 0,
        weeks_since_last_fight: int = 0
    ) -> Tuple[bool, str]:
        """
        Evaluate whether to accept a fight offer.
        
        Returns:
            Tuple of (accept: bool, reason: str)
        """
        # Calculate matchup favorability
        rating_diff = fighter_rating - offer.opponent_rating
        is_favorable = rating_diff >= -5
        
        # Base acceptance from personality
        acceptance_chance = self.personality.get_fight_acceptance_modifier(is_favorable)
        
        # Adjust for specific circumstances
        reasons = []
        
        # Title fight bonus
        if offer.is_title_fight:
            acceptance_chance += 0.2 * self.personality.title_focus
            reasons.append("title opportunity")
        
        # Main event prestige
        if offer.is_main_event:
            acceptance_chance += 0.1
            reasons.append("main event slot")
        
        # Momentum considerations
        if current_win_streak >= 3:
            if is_favorable:
                acceptance_chance += 0.15
                reasons.append("riding momentum")
            else:
                # Protect streak if conservative
                if self.personality.risk_tolerance == RiskTolerance.CONSERVATIVE:
                    acceptance_chance -= 0.2
        
        if current_lose_streak >= 2:
            if is_favorable:
                acceptance_chance += 0.2  # Need a win
                reasons.append("need bounce-back")
            else:
                acceptance_chance -= 0.15  # Risky to fight tough opponent
        
        # Activity consideration
        if weeks_since_last_fight > 20:
            acceptance_chance += 0.15 * self.personality.activity_level
            reasons.append("ring rust concern")
        
        # Preparation time
        if offer.weeks_until_fight < 6:
            acceptance_chance -= 0.2
            if self.personality.risk_tolerance != RiskTolerance.RECKLESS:
                reasons.append("short notice concern")
        
        # Tough opponent adjustment
        if rating_diff < -10:
            if self.personality.risk_tolerance == RiskTolerance.CONSERVATIVE:
                acceptance_chance -= 0.25
                reasons.append("tough matchup")
            elif self.personality.risk_tolerance == RiskTolerance.RECKLESS:
                acceptance_chance += 0.1
                reasons.append("welcomes challenge")
        
        # Champion behavior
        if fighter_is_champion:
            # More selective about opponents
            if offer.opponent_rank is None or offer.opponent_rank > 5:
                acceptance_chance -= 0.2
                reasons.append("opponent not ranked high enough")
        
        # Make decision
        accept = random.random() < acceptance_chance
        
        if accept:
            reason = f"Accepted: {', '.join(reasons) if reasons else 'good opportunity'}"
        else:
            reason = f"Declined: {', '.join(reasons) if reasons else 'not the right time'}"
        
        # Log decision
        self.recent_decisions.append({
            "type": "fight_offer",
            "fighter_id": fighter_id,
            "opponent_id": offer.opponent_id,
            "accepted": accept,
            "reason": reason,
        })
        
        return accept, reason
    
    def evaluate_signing(
        self,
        fighter_name: str,
        fighter_age: int,
        fighter_rating: int,
        asking_price: int,
        camp_budget: int,
        current_roster_size: int,
        max_roster_size: int
    ) -> Tuple[bool, int, str]:
        """
        Evaluate whether to sign a free agent.
        
        Returns:
            Tuple of (sign: bool, offer_amount: int, reason: str)
        """
        # Check roster space
        if current_roster_size >= max_roster_size:
            return False, 0, "Roster full"
        
        # Get base interest
        interest = self.personality.get_signing_interest(fighter_age, fighter_rating)
        
        # Budget consideration
        if asking_price > camp_budget * 0.3:
            if self.personality.financial_savvy > 60:
                interest -= 0.2
        
        # Calculate offer based on negotiation style
        if self.personality.negotiation_style == NegotiationStyle.GENEROUS:
            offer_multiplier = random.uniform(1.0, 1.2)
        elif self.personality.negotiation_style == NegotiationStyle.FAIR:
            offer_multiplier = random.uniform(0.9, 1.1)
        elif self.personality.negotiation_style == NegotiationStyle.FRUGAL:
            offer_multiplier = random.uniform(0.7, 0.9)
        else:  # HARDBALL
            offer_multiplier = random.uniform(0.6, 0.85)
        
        offer_amount = int(asking_price * offer_multiplier * interest)
        offer_amount = min(offer_amount, int(camp_budget * 0.25))  # Cap at 25% of budget
        
        # Decision
        sign = interest > 0.4 and offer_amount > 0 and random.random() < interest
        
        if sign:
            reason = f"Interested in {fighter_name}'s potential"
        else:
            if interest < 0.4:
                reason = "Not the right fit"
            elif offer_amount <= 0:
                reason = "Budget constraints"
            else:
                reason = "Passed on opportunity"
        
        return sign, offer_amount, reason
    
    def get_training_focus(self, fighter_strengths: Dict[str, int]) -> str:
        """
        Determine training focus based on camp philosophy.
        
        Returns:
            Training focus area
        """
        if self.personality.philosophy == CampPhilosophy.STRIKER_FACTORY:
            return random.choice(["striking", "boxing", "kicks"])
        elif self.personality.philosophy == CampPhilosophy.GRAPPLING_ACADEMY:
            return random.choice(["grappling", "wrestling", "bjj"])
        elif self.personality.philosophy == CampPhilosophy.CARDIO_KINGS:
            return "cardio"
        elif self.personality.philosophy == CampPhilosophy.POWER_HOUSE:
            return random.choice(["strength", "striking"])
        else:  # WELL_ROUNDED
            # Shore up weaknesses
            weakest = min(fighter_strengths, key=fighter_strengths.get)
            return weakest
    
    def should_release_fighter(
        self,
        fighter_age: int,
        fighter_rating: int,
        recent_record: Tuple[int, int],  # (wins, losses)
        months_without_fight: int
    ) -> Tuple[bool, str]:
        """
        Decide whether to release a fighter.
        
        Returns:
            Tuple of (release: bool, reason: str)
        """
        wins, losses = recent_record
        
        # Loyalty affects decision
        loyalty_factor = self.personality.loyalty / 100
        
        release_score = 0
        reasons = []
        
        # Losing streak
        if losses >= 3 and wins == 0:
            release_score += 0.4
            reasons.append("losing streak")
        
        # Age and decline
        if fighter_age >= 38 and fighter_rating < 60:
            release_score += 0.3
            reasons.append("age and decline")
        
        # Inactivity
        if months_without_fight >= 18:
            release_score += 0.25
            reasons.append("inactivity")
        
        # Low rating
        if fighter_rating < 45:
            release_score += 0.2
            reasons.append("low skill level")
        
        # Apply loyalty modifier
        release_score *= (1 - loyalty_factor * 0.5)
        
        release = random.random() < release_score
        
        if release:
            reason = f"Released: {', '.join(reasons)}"
        else:
            reason = "Retained on roster"
        
        return release, reason


# ============================================================================
# WORLD STATE
# ============================================================================

@dataclass
class ScheduledFight:
    """A fight scheduled for an upcoming event"""
    fighter1_id: str
    fighter2_id: str
    fighter1_name: str
    fighter2_name: str
    weight_class: str
    is_title_fight: bool = False
    is_main_event: bool = False
    rounds: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter1_id": self.fighter1_id,
            "fighter2_id": self.fighter2_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_name": self.fighter2_name,
            "weight_class": self.weight_class,
            "is_title_fight": self.is_title_fight,
            "is_main_event": self.is_main_event,
            "rounds": self.rounds,
        }


@dataclass
class ScheduledEvent:
    """A scheduled fight card"""
    event_id: str
    event_name: str
    date: str  # ISO format
    location: str
    fights: List[ScheduledFight] = field(default_factory=list)
    is_completed: bool = False
    
    @property
    def fight_count(self) -> int:
        return len(self.fights)
    
    @property
    def has_title_fight(self) -> bool:
        return any(f.is_title_fight for f in self.fights)
    
    def add_fight(self, fight: ScheduledFight) -> None:
        self.fights.append(fight)
    
    def get_main_event(self) -> Optional[ScheduledFight]:
        for fight in self.fights:
            if fight.is_main_event:
                return fight
        return self.fights[-1] if self.fights else None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "date": self.date,
            "location": self.location,
            "fights": [f.to_dict() for f in self.fights],
            "is_completed": self.is_completed,
        }


@dataclass
class WeeklyReport:
    """Summary of a week's events"""
    week_number: int
    date: str
    events_held: List[str] = field(default_factory=list)
    fights_completed: int = 0
    knockouts: int = 0
    submissions: int = 0
    decisions: int = 0
    title_changes: int = 0
    retirements: List[str] = field(default_factory=list)
    injuries: List[Dict[str, Any]] = field(default_factory=list)
    signings: List[Dict[str, Any]] = field(default_factory=list)
    releases: List[Dict[str, Any]] = field(default_factory=list)
    new_prospects: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "week_number": self.week_number,
            "date": self.date,
            "events_held": self.events_held.copy(),
            "fights_completed": self.fights_completed,
            "knockouts": self.knockouts,
            "submissions": self.submissions,
            "decisions": self.decisions,
            "title_changes": self.title_changes,
            "retirements": self.retirements.copy(),
            "injuries": self.injuries.copy(),
            "signings": self.signings.copy(),
            "releases": self.releases.copy(),
            "new_prospects": self.new_prospects.copy(),
        }


@dataclass
class YearEndAwards:
    """
    Year-End Awards ceremony results.
    
    Calculated at the end of each calendar year (week 52).
    """
    year: int
    
    # Fighter of the Year
    fighter_of_year_id: Optional[str] = None
    fighter_of_year_name: str = ""
    fighter_of_year_wins: int = 0
    fighter_of_year_finishes: int = 0
    fighter_of_year_reason: str = ""
    
    # Fight of the Year
    fight_of_year_fighter1: str = ""
    fight_of_year_fighter2: str = ""
    fight_of_year_event: str = ""
    fight_of_year_method: str = ""
    fight_of_year_score: float = 0.0
    
    # Knockout of the Year
    ko_of_year_winner: str = ""
    ko_of_year_loser: str = ""
    ko_of_year_event: str = ""
    ko_of_year_round: int = 0
    
    # Prospect of the Year (fighter under 25 with best record)
    prospect_of_year_id: Optional[str] = None
    prospect_of_year_name: str = ""
    prospect_of_year_wins: int = 0
    prospect_of_year_age: int = 0
    
    # Submission of the Year
    sub_of_year_winner: str = ""
    sub_of_year_loser: str = ""
    sub_of_year_event: str = ""
    sub_of_year_method: str = ""
    
    # Stats summary
    total_fights: int = 0
    total_knockouts: int = 0
    total_submissions: int = 0
    title_changes: int = 0
    new_champions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "year": self.year,
            "fighter_of_year_id": self.fighter_of_year_id,
            "fighter_of_year_name": self.fighter_of_year_name,
            "fighter_of_year_wins": self.fighter_of_year_wins,
            "fighter_of_year_finishes": self.fighter_of_year_finishes,
            "fighter_of_year_reason": self.fighter_of_year_reason,
            "fight_of_year_fighter1": self.fight_of_year_fighter1,
            "fight_of_year_fighter2": self.fight_of_year_fighter2,
            "fight_of_year_event": self.fight_of_year_event,
            "fight_of_year_method": self.fight_of_year_method,
            "fight_of_year_score": self.fight_of_year_score,
            "ko_of_year_winner": self.ko_of_year_winner,
            "ko_of_year_loser": self.ko_of_year_loser,
            "ko_of_year_event": self.ko_of_year_event,
            "ko_of_year_round": self.ko_of_year_round,
            "prospect_of_year_id": self.prospect_of_year_id,
            "prospect_of_year_name": self.prospect_of_year_name,
            "prospect_of_year_wins": self.prospect_of_year_wins,
            "prospect_of_year_age": self.prospect_of_year_age,
            "sub_of_year_winner": self.sub_of_year_winner,
            "sub_of_year_loser": self.sub_of_year_loser,
            "sub_of_year_event": self.sub_of_year_event,
            "sub_of_year_method": self.sub_of_year_method,
            "total_fights": self.total_fights,
            "total_knockouts": self.total_knockouts,
            "total_submissions": self.total_submissions,
            "title_changes": self.title_changes,
            "new_champions": self.new_champions.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "YearEndAwards":
        awards = cls(year=data["year"])
        for key, value in data.items():
            if hasattr(awards, key):
                setattr(awards, key, value)
        return awards


# ============================================================================
# WORLD SIMULATION
# ============================================================================

class WorldSimulation:
    """
    Core world simulation engine.
    
    Manages the passage of time and all world events.
    """
    
    def __init__(self, calendar: Optional[GameCalendar] = None):
        # Time management
        self.calendar = calendar or GameCalendar()
        self.week_number: int = 0
        
        # Entity registries (IDs only - actual objects managed elsewhere)
        self.fighter_ids: Set[str] = set()
        self.camp_ids: Set[str] = set()
        self.free_agent_ids: Set[str] = set()
        self.retired_ids: Set[str] = set()
        self.injured_ids: Dict[str, int] = {}  # fighter_id -> weeks remaining
        
        # AI personalities for camps
        self.camp_personalities: Dict[str, CampPersonality] = {}
        self.camp_ais: Dict[str, CampAI] = {}
        
        # Scheduled events
        self.upcoming_events: List[ScheduledEvent] = []
        self.completed_events: List[ScheduledEvent] = []
        self.event_counter: int = 0
        
        # Booked fighters (can't be double-booked)
        self.booked_fighters: Set[str] = set()
        
        # Weekly reports
        self.weekly_reports: List[WeeklyReport] = []
        
        # Callbacks for external systems
        self._fight_simulator: Optional[Callable] = None
        self._fighter_getter: Optional[Callable] = None
        self._camp_getter: Optional[Callable] = None
        
        # Configuration
        self.events_per_month: int = 2
        self.fights_per_event: int = 12
        self.prospect_spawn_chance: float = 0.15  # Per week
        self.min_weeks_between_fights: int = 6
        
        # === YEAR-END AWARDS TRACKING ===
        # Current year stats (reset each year)
        self.current_year: int = self.calendar.current_date.year if self.calendar else 2025
        self.yearly_fighter_wins: Dict[str, int] = {}  # fighter_id -> wins this year
        self.yearly_fighter_finishes: Dict[str, int] = {}  # fighter_id -> finishes (KO+SUB)
        self.yearly_fighter_title_wins: Dict[str, int] = {}  # fighter_id -> title wins
        self.yearly_prospect_wins: Dict[str, Tuple[int, int]] = {}  # fighter_id -> (wins, age)
        
        # Best fights of the year (for Fight of Year selection)
        self.yearly_best_fights: List[Dict[str, Any]] = []  # Top scored fights
        self.yearly_best_kos: List[Dict[str, Any]] = []  # Best KOs
        self.yearly_best_subs: List[Dict[str, Any]] = []  # Best Submissions
        
        # Accumulated stats
        self.yearly_total_fights: int = 0
        self.yearly_total_kos: int = 0
        self.yearly_total_subs: int = 0
        self.yearly_title_changes: int = 0
        self.yearly_new_champions: List[str] = []
        
        # Historical awards
        self.year_end_awards_history: List[YearEndAwards] = []
    
    # -------------------------------------------------------------------------
    # Setup and Registration
    # -------------------------------------------------------------------------
    
    def register_fighter(self, fighter_id: str, camp_id: Optional[str] = None) -> None:
        """Register a fighter in the world"""
        self.fighter_ids.add(fighter_id)
        if camp_id is None:
            self.free_agent_ids.add(fighter_id)
        else:
            self.free_agent_ids.discard(fighter_id)
    
    def register_camp(self, camp_id: str, personality: Optional[CampPersonality] = None) -> None:
        """Register a camp with optional personality"""
        self.camp_ids.add(camp_id)
        
        if personality is None:
            personality = generate_camp_personality(camp_id)
        
        self.camp_personalities[camp_id] = personality
        self.camp_ais[camp_id] = CampAI(personality=personality)
    
    def set_fighter_getter(self, getter: Callable[[str], Any]) -> None:
        """Set callback to get fighter objects"""
        self._fighter_getter = getter
    
    def set_camp_getter(self, getter: Callable[[str], Any]) -> None:
        """Set callback to get camp objects"""
        self._camp_getter = getter
    
    def set_fight_simulator(self, simulator: Callable) -> None:
        """Set callback to simulate fights"""
        self._fight_simulator = simulator
    
    # -------------------------------------------------------------------------
    # Time Management
    # -------------------------------------------------------------------------
    
    def advance_week(self) -> WeeklyReport:
        """
        Advance the simulation by one week.
        
        Returns:
            WeeklyReport summarizing the week's events
        """
        self.week_number += 1
        self.calendar.advance_week()
        
        report = WeeklyReport(
            week_number=self.week_number,
            date=self.calendar.current_date.format("iso"),
        )
        
        # Process scheduled events for this week
        self._process_weekly_events(report)
        
        # Process injuries (heal fighters)
        self._process_injuries(report)
        
        # AI camp decisions (weekly)
        self._process_camp_decisions(report)
        
        # Check for new prospects
        self._check_prospect_spawn(report)
        
        # Monthly processing (first week of month)
        if self.calendar.current_date.day <= 7:
            self._process_monthly(report)
        
        # Year-end processing (last week of year / week 52)
        if self.week_number > 0 and self.week_number % 52 == 0:
            self._process_year_end()
        
        # Clear weekly booked fighters for completed events
        self._clear_completed_bookings()
        
        # Store report
        self.weekly_reports.append(report)
        
        # Emit event
        emit("week_advanced", {
            "week": self.week_number,
            "date": report.date,
            "events_held": len(report.events_held),
            "fights": report.fights_completed,
        })
        
        return report
    
    def advance_weeks(self, count: int) -> List[WeeklyReport]:
        """Advance multiple weeks"""
        return [self.advance_week() for _ in range(count)]
    
    def advance_to_date(self, target_date: GameDate) -> List[WeeklyReport]:
        """Advance to a specific date"""
        reports = []
        while self.calendar.current_date < target_date:
            reports.append(self.advance_week())
        return reports
    
    # -------------------------------------------------------------------------
    # Event Scheduling
    # -------------------------------------------------------------------------
    
    def schedule_event(
        self,
        weeks_from_now: int,
        event_name: Optional[str] = None,
        location: str = "Las Vegas, NV"
    ) -> ScheduledEvent:
        """
        Schedule a new event.
        
        Args:
            weeks_from_now: Weeks until the event
            event_name: Optional custom name
            location: Event location
            
        Returns:
            The scheduled event
        """
        self.event_counter += 1
        
        event_date = self.calendar.current_date.add_weeks(weeks_from_now)
        
        if event_name is None:
            event_name = f"DFC {self.event_counter}"
        
        event = ScheduledEvent(
            event_id=f"event_{self.event_counter}",
            event_name=event_name,
            date=event_date.format("iso"),
            location=location,
        )
        
        self.upcoming_events.append(event)
        
        # Sort by date
        self.upcoming_events.sort(key=lambda e: e.date)
        
        emit("event_scheduled", {
            "event_id": event.event_id,
            "event_name": event.event_name,
            "date": event.date,
        })
        
        return event
    
    def book_fight(
        self,
        event_id: str,
        fighter1_id: str,
        fighter2_id: str,
        fighter1_name: str,
        fighter2_name: str,
        weight_class: str,
        is_title_fight: bool = False,
        is_main_event: bool = False
    ) -> bool:
        """
        Book a fight on an event.
        
        Returns:
            True if fight was booked successfully
        """
        # Find the event
        event = None
        for e in self.upcoming_events:
            if e.event_id == event_id:
                event = e
                break
        
        if event is None:
            return False
        
        # Check availability
        if fighter1_id in self.booked_fighters or fighter2_id in self.booked_fighters:
            return False
        
        if fighter1_id in self.injured_ids or fighter2_id in self.injured_ids:
            return False
        
        # Create and add fight
        rounds = 5 if is_title_fight or is_main_event else 3
        
        fight = ScheduledFight(
            fighter1_id=fighter1_id,
            fighter2_id=fighter2_id,
            fighter1_name=fighter1_name,
            fighter2_name=fighter2_name,
            weight_class=weight_class,
            is_title_fight=is_title_fight,
            is_main_event=is_main_event,
            rounds=rounds,
        )
        
        event.add_fight(fight)
        
        # Mark fighters as booked
        self.booked_fighters.add(fighter1_id)
        self.booked_fighters.add(fighter2_id)
        
        emit("fight_booked", {
            "event_id": event_id,
            "fighter1_id": fighter1_id,
            "fighter2_id": fighter2_id,
            "is_title_fight": is_title_fight,
        })
        
        return True
    
    def get_next_event(self) -> Optional[ScheduledEvent]:
        """Get the next upcoming event"""
        if not self.upcoming_events:
            return None
        return self.upcoming_events[0]
    
    def get_events_in_range(self, weeks: int) -> List[ScheduledEvent]:
        """Get all events scheduled within N weeks"""
        cutoff = self.calendar.current_date.add_weeks(weeks)
        return [
            e for e in self.upcoming_events
            if e.date <= cutoff.format("iso")
        ]
    
    # -------------------------------------------------------------------------
    # Internal Processing
    # -------------------------------------------------------------------------
    
    def _process_weekly_events(self, report: WeeklyReport) -> None:
        """Process any events scheduled for this week"""
        current_date = self.calendar.current_date.format("iso")
        
        events_this_week = [
            e for e in self.upcoming_events
            if e.date <= current_date and not e.is_completed
        ]
        
        for event in events_this_week:
            self._run_event(event, report)
            event.is_completed = True
            report.events_held.append(event.event_name)
        
        # Move completed events
        self.upcoming_events = [e for e in self.upcoming_events if not e.is_completed]
        self.completed_events.extend(events_this_week)
    
    def _run_event(self, event: ScheduledEvent, report: WeeklyReport) -> None:
        """Execute all fights on an event"""
        emit("event_started", {
            "event_id": event.event_id,
            "event_name": event.event_name,
            "fight_count": len(event.fights),
        })
        
        for fight in event.fights:
            result = self._simulate_fight(fight)
            
            if result:
                report.fights_completed += 1
                
                method = result.get("method", "DEC")
                if method in ["KO", "TKO"]:
                    report.knockouts += 1
                elif method == "SUB":
                    report.submissions += 1
                else:
                    report.decisions += 1
                
                if result.get("title_changed"):
                    report.title_changes += 1
                
                # Record injury if any
                if result.get("injury"):
                    report.injuries.append(result["injury"])
        
        emit("event_completed", {
            "event_id": event.event_id,
            "fights_completed": report.fights_completed,
        })
    
    def _simulate_fight(self, fight: ScheduledFight) -> Optional[Dict[str, Any]]:
        """Simulate a single fight"""
        if self._fight_simulator is None:
            # Return mock result if no simulator set
            return {
                "winner_id": random.choice([fight.fighter1_id, fight.fighter2_id]),
                "method": random.choice(["KO", "TKO", "SUB", "DEC"]),
                "round": random.randint(1, fight.rounds),
            }
        
        # Use external simulator
        return self._fight_simulator(fight)
    
    def _process_injuries(self, report: WeeklyReport) -> None:
        """Process injury recovery"""
        healed = []
        
        for fighter_id, weeks_remaining in list(self.injured_ids.items()):
            weeks_remaining -= 1
            if weeks_remaining <= 0:
                healed.append(fighter_id)
            else:
                self.injured_ids[fighter_id] = weeks_remaining
        
        for fighter_id in healed:
            del self.injured_ids[fighter_id]
            emit("fighter_healed", {"fighter_id": fighter_id})
    
    def _process_camp_decisions(self, report: WeeklyReport) -> None:
        """Process AI camp weekly decisions"""
        for camp_id in self.camp_ids:
            if camp_id not in self.camp_ais:
                continue
            
            ai = self.camp_ais[camp_id]
            
            # Random chance of activity based on personality
            if random.random() > ai.personality.activity_level * 0.3:
                continue
            
            # Could look for signings, etc.
            # This would need actual fighter/camp data callbacks
    
    def _check_prospect_spawn(self, report: WeeklyReport) -> None:
        """Check if new prospects should spawn"""
        if random.random() < self.prospect_spawn_chance:
            # Signal that a new prospect should be generated
            emit("prospect_spawn_requested", {
                "week": self.week_number,
            })
            report.new_prospects.append(f"Prospect generated week {self.week_number}")
    
    def _process_monthly(self, report: WeeklyReport) -> None:
        """Process monthly events (aging, finances, etc.)"""
        emit("month_started", {
            "month": self.calendar.current_date.month,
            "year": self.calendar.current_date.year,
        })
    
    def _clear_completed_bookings(self) -> None:
        """Clear bookings for fighters whose events have completed"""
        # Get all fighters still in upcoming fights
        still_booked = set()
        for event in self.upcoming_events:
            for fight in event.fights:
                still_booked.add(fight.fighter1_id)
                still_booked.add(fight.fighter2_id)
        
        self.booked_fighters = still_booked
    
    # -------------------------------------------------------------------------
    # Fighter Status
    # -------------------------------------------------------------------------
    
    def injure_fighter(self, fighter_id: str, weeks: int) -> None:
        """Mark a fighter as injured"""
        self.injured_ids[fighter_id] = weeks
        self.booked_fighters.discard(fighter_id)
        
        emit("fighter_injured", {
            "fighter_id": fighter_id,
            "weeks": weeks,
        })
    
    def retire_fighter(self, fighter_id: str) -> None:
        """Mark a fighter as retired"""
        self.fighter_ids.discard(fighter_id)
        self.free_agent_ids.discard(fighter_id)
        self.booked_fighters.discard(fighter_id)
        self.injured_ids.pop(fighter_id, None)
        self.retired_ids.add(fighter_id)
        
        emit("fighter_retired", {"fighter_id": fighter_id})
    
    def is_fighter_available(self, fighter_id: str) -> bool:
        """Check if a fighter can be booked"""
        if fighter_id in self.booked_fighters:
            return False
        if fighter_id in self.injured_ids:
            return False
        if fighter_id in self.retired_ids:
            return False
        return fighter_id in self.fighter_ids
    
    def get_available_fighters(self, exclude: Optional[Set[str]] = None) -> List[str]:
        """Get all available fighters"""
        exclude = exclude or set()
        return [
            fid for fid in self.fighter_ids
            if self.is_fighter_available(fid) and fid not in exclude
        ]
    
    # -------------------------------------------------------------------------
    # Year-End Awards System
    # -------------------------------------------------------------------------
    
    def record_fight_result(
        self,
        winner_id: str,
        winner_name: str,
        loser_id: str,
        loser_name: str,
        method: str,
        round_ended: int,
        event_name: str,
        is_title_fight: bool = False,
        is_title_change: bool = False,
        fotn_score: float = 0.0,
        winner_age: int = 30,
    ) -> None:
        """
        Record a fight result for year-end awards tracking.
        
        Should be called after each fight is simulated.
        """
        # Track wins
        self.yearly_fighter_wins[winner_id] = self.yearly_fighter_wins.get(winner_id, 0) + 1
        
        # Track finishes
        is_finish = method.upper() in ["KO", "TKO", "SUBMISSION", "SUB"]
        is_ko = method.upper() in ["KO", "TKO"]
        is_sub = method.upper() in ["SUBMISSION", "SUB"]
        
        if is_finish:
            self.yearly_fighter_finishes[winner_id] = self.yearly_fighter_finishes.get(winner_id, 0) + 1
        
        # Track title wins
        if is_title_fight and is_title_change:
            self.yearly_fighter_title_wins[winner_id] = self.yearly_fighter_title_wins.get(winner_id, 0) + 1
            self.yearly_title_changes += 1
            if winner_name not in self.yearly_new_champions:
                self.yearly_new_champions.append(winner_name)
        
        # Track prospect wins (under 25)
        if winner_age < 25:
            current = self.yearly_prospect_wins.get(winner_id, (0, winner_age))
            self.yearly_prospect_wins[winner_id] = (current[0] + 1, winner_age)
        
        # Track best fights (keep top 10)
        fight_record = {
            "fighter1": winner_name,
            "fighter2": loser_name,
            "event": event_name,
            "method": method,
            "round": round_ended,
            "score": fotn_score,
        }
        
        if fotn_score > 0:
            self.yearly_best_fights.append(fight_record)
            self.yearly_best_fights.sort(key=lambda x: x["score"], reverse=True)
            self.yearly_best_fights = self.yearly_best_fights[:10]
        
        # Track best KOs
        if is_ko:
            self.yearly_total_kos += 1
            ko_record = {
                "winner": winner_name,
                "loser": loser_name,
                "event": event_name,
                "round": round_ended,
                "method": method,
            }
            self.yearly_best_kos.append(ko_record)
            # Keep early round KOs as best
            self.yearly_best_kos.sort(key=lambda x: x["round"])
            self.yearly_best_kos = self.yearly_best_kos[:10]
        
        # Track best submissions
        if is_sub:
            self.yearly_total_subs += 1
            sub_record = {
                "winner": winner_name,
                "loser": loser_name,
                "event": event_name,
                "method": method,
            }
            self.yearly_best_subs.append(sub_record)
            self.yearly_best_subs = self.yearly_best_subs[:10]
        
        self.yearly_total_fights += 1
    
    def _process_year_end(self) -> Optional[YearEndAwards]:
        """
        Process year-end awards ceremony.
        
        Called when week % 52 == 0.
        """
        awards = YearEndAwards(year=self.current_year)
        
        # === FIGHTER OF THE YEAR ===
        # Score = wins * 2 + finishes + title_wins * 3
        fighter_scores: Dict[str, int] = {}
        for fid, wins in self.yearly_fighter_wins.items():
            finishes = self.yearly_fighter_finishes.get(fid, 0)
            title_wins = self.yearly_fighter_title_wins.get(fid, 0)
            fighter_scores[fid] = wins * 2 + finishes + title_wins * 3
        
        if fighter_scores:
            best_fighter_id = max(fighter_scores, key=fighter_scores.get)
            awards.fighter_of_year_id = best_fighter_id
            awards.fighter_of_year_wins = self.yearly_fighter_wins.get(best_fighter_id, 0)
            awards.fighter_of_year_finishes = self.yearly_fighter_finishes.get(best_fighter_id, 0)
            
            # Get fighter name via callback if available
            if self._fighter_getter:
                try:
                    fighter = self._fighter_getter(best_fighter_id)
                    if fighter:
                        awards.fighter_of_year_name = getattr(fighter, 'name', best_fighter_id)
                except:
                    awards.fighter_of_year_name = best_fighter_id
            else:
                awards.fighter_of_year_name = best_fighter_id
            
            # Build reason
            reasons = []
            if awards.fighter_of_year_wins >= 4:
                reasons.append(f"{awards.fighter_of_year_wins} wins")
            if awards.fighter_of_year_finishes >= 2:
                reasons.append(f"{awards.fighter_of_year_finishes} finishes")
            if self.yearly_fighter_title_wins.get(best_fighter_id, 0) > 0:
                reasons.append("title victory")
            awards.fighter_of_year_reason = ", ".join(reasons) if reasons else "dominant performance"
        
        # === FIGHT OF THE YEAR ===
        if self.yearly_best_fights:
            best_fight = self.yearly_best_fights[0]
            awards.fight_of_year_fighter1 = best_fight["fighter1"]
            awards.fight_of_year_fighter2 = best_fight["fighter2"]
            awards.fight_of_year_event = best_fight["event"]
            awards.fight_of_year_method = best_fight["method"]
            awards.fight_of_year_score = best_fight["score"]
        
        # === KNOCKOUT OF THE YEAR ===
        if self.yearly_best_kos:
            best_ko = self.yearly_best_kos[0]
            awards.ko_of_year_winner = best_ko["winner"]
            awards.ko_of_year_loser = best_ko["loser"]
            awards.ko_of_year_event = best_ko["event"]
            awards.ko_of_year_round = best_ko["round"]
        
        # === SUBMISSION OF THE YEAR ===
        if self.yearly_best_subs:
            best_sub = self.yearly_best_subs[0]
            awards.sub_of_year_winner = best_sub["winner"]
            awards.sub_of_year_loser = best_sub["loser"]
            awards.sub_of_year_event = best_sub["event"]
            awards.sub_of_year_method = best_sub.get("method", "Submission")
        
        # === PROSPECT OF THE YEAR ===
        if self.yearly_prospect_wins:
            # Find prospect with most wins
            best_prospect_id = max(self.yearly_prospect_wins, key=lambda x: self.yearly_prospect_wins[x][0])
            wins, age = self.yearly_prospect_wins[best_prospect_id]
            awards.prospect_of_year_id = best_prospect_id
            awards.prospect_of_year_wins = wins
            awards.prospect_of_year_age = age
            
            # Get name via callback
            if self._fighter_getter:
                try:
                    fighter = self._fighter_getter(best_prospect_id)
                    if fighter:
                        awards.prospect_of_year_name = getattr(fighter, 'name', best_prospect_id)
                except:
                    awards.prospect_of_year_name = best_prospect_id
            else:
                awards.prospect_of_year_name = best_prospect_id
        
        # === YEARLY STATS ===
        awards.total_fights = self.yearly_total_fights
        awards.total_knockouts = self.yearly_total_kos
        awards.total_submissions = self.yearly_total_subs
        awards.title_changes = self.yearly_title_changes
        awards.new_champions = self.yearly_new_champions.copy()
        
        # Store in history
        self.year_end_awards_history.append(awards)
        
        # Emit year-end event
        emit("year_end_awards", {
            "year": self.current_year,
            "fighter_of_year": awards.fighter_of_year_name,
            "fight_of_year": f"{awards.fight_of_year_fighter1} vs {awards.fight_of_year_fighter2}",
            "total_fights": awards.total_fights,
            "total_kos": awards.total_knockouts,
        })
        
        # Reset yearly tracking for new year
        self._reset_yearly_tracking()
        self.current_year += 1
        
        return awards
    
    def _reset_yearly_tracking(self) -> None:
        """Reset all yearly tracking for the new year."""
        self.yearly_fighter_wins.clear()
        self.yearly_fighter_finishes.clear()
        self.yearly_fighter_title_wins.clear()
        self.yearly_prospect_wins.clear()
        self.yearly_best_fights.clear()
        self.yearly_best_kos.clear()
        self.yearly_best_subs.clear()
        self.yearly_total_fights = 0
        self.yearly_total_kos = 0
        self.yearly_total_subs = 0
        self.yearly_title_changes = 0
        self.yearly_new_champions.clear()
    
    def get_current_year_stats(self) -> Dict[str, Any]:
        """Get stats for the current year so far."""
        return {
            "year": self.current_year,
            "total_fights": self.yearly_total_fights,
            "total_kos": self.yearly_total_kos,
            "total_subs": self.yearly_total_subs,
            "title_changes": self.yearly_title_changes,
            "top_winners": sorted(
                [(fid, wins) for fid, wins in self.yearly_fighter_wins.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }
    
    def get_year_end_awards(self, year: Optional[int] = None) -> Optional[YearEndAwards]:
        """Get year-end awards for a specific year."""
        if not self.year_end_awards_history:
            return None
        
        if year is None:
            return self.year_end_awards_history[-1]
        
        for awards in self.year_end_awards_history:
            if awards.year == year:
                return awards
        
        return None

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def get_world_stats(self) -> Dict[str, Any]:
        """Get world simulation statistics"""
        return {
            "week_number": self.week_number,
            "current_date": self.calendar.current_date.format("long"),
            "total_fighters": len(self.fighter_ids),
            "free_agents": len(self.free_agent_ids),
            "injured_fighters": len(self.injured_ids),
            "retired_fighters": len(self.retired_ids),
            "active_camps": len(self.camp_ids),
            "upcoming_events": len(self.upcoming_events),
            "completed_events": len(self.completed_events),
            "total_events": self.event_counter,
            "booked_fighters": len(self.booked_fighters),
        }
    
    def get_camp_personality_summary(self, camp_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a camp's personality"""
        if camp_id not in self.camp_personalities:
            return None
        
        p = self.camp_personalities[camp_id]
        return {
            "philosophy": p.philosophy.value.replace("_", " ").title(),
            "risk_tolerance": p.risk_tolerance.value.title(),
            "talent_strategy": p.talent_strategy.value.replace("_", " ").title(),
            "negotiation_style": p.negotiation_style.value.title(),
            "activity_level": f"{p.activity_level:.1%}",
            "key_traits": {
                "aggression": p.aggression,
                "patience": p.patience,
                "loyalty": p.loyalty,
                "ambition": p.ambition,
            },
            "preferred_divisions": p.preferred_weight_classes,
        }
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize world state"""
        return {
            "week_number": self.week_number,
            "calendar": self.calendar.to_dict(),
            "fighter_ids": list(self.fighter_ids),
            "camp_ids": list(self.camp_ids),
            "free_agent_ids": list(self.free_agent_ids),
            "retired_ids": list(self.retired_ids),
            "injured_ids": dict(self.injured_ids),
            "booked_fighters": list(self.booked_fighters),
            "camp_personalities": {
                cid: p.to_dict() for cid, p in self.camp_personalities.items()
            },
            "upcoming_events": [e.to_dict() for e in self.upcoming_events],
            "event_counter": self.event_counter,
            "events_per_month": self.events_per_month,
            "fights_per_event": self.fights_per_event,
            # Year-end awards tracking
            "current_year": self.current_year,
            "yearly_fighter_wins": dict(self.yearly_fighter_wins),
            "yearly_fighter_finishes": dict(self.yearly_fighter_finishes),
            "yearly_fighter_title_wins": dict(self.yearly_fighter_title_wins),
            "yearly_prospect_wins": {k: list(v) for k, v in self.yearly_prospect_wins.items()},
            "yearly_best_fights": self.yearly_best_fights.copy(),
            "yearly_best_kos": self.yearly_best_kos.copy(),
            "yearly_best_subs": self.yearly_best_subs.copy(),
            "yearly_total_fights": self.yearly_total_fights,
            "yearly_total_kos": self.yearly_total_kos,
            "yearly_total_subs": self.yearly_total_subs,
            "yearly_title_changes": self.yearly_title_changes,
            "yearly_new_champions": self.yearly_new_champions.copy(),
            "year_end_awards_history": [a.to_dict() for a in self.year_end_awards_history],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldSimulation":
        """Deserialize world state"""
        calendar = GameCalendar.from_dict(data["calendar"])
        world = cls(calendar=calendar)
        
        world.week_number = data["week_number"]
        world.fighter_ids = set(data["fighter_ids"])
        world.camp_ids = set(data["camp_ids"])
        world.free_agent_ids = set(data["free_agent_ids"])
        world.retired_ids = set(data["retired_ids"])
        world.injured_ids = dict(data["injured_ids"])
        world.booked_fighters = set(data["booked_fighters"])
        world.event_counter = data["event_counter"]
        world.events_per_month = data.get("events_per_month", 2)
        world.fights_per_event = data.get("fights_per_event", 12)
        
        # Restore camp personalities and AIs
        for cid, p_data in data.get("camp_personalities", {}).items():
            personality = CampPersonality.from_dict(p_data)
            world.camp_personalities[cid] = personality
            world.camp_ais[cid] = CampAI(personality=personality)
        
        # Restore upcoming events
        for e_data in data.get("upcoming_events", []):
            event = ScheduledEvent(
                event_id=e_data["event_id"],
                event_name=e_data["event_name"],
                date=e_data["date"],
                location=e_data["location"],
                is_completed=e_data.get("is_completed", False),
            )
            for f_data in e_data.get("fights", []):
                event.fights.append(ScheduledFight(
                    fighter1_id=f_data["fighter1_id"],
                    fighter2_id=f_data["fighter2_id"],
                    fighter1_name=f_data["fighter1_name"],
                    fighter2_name=f_data["fighter2_name"],
                    weight_class=f_data["weight_class"],
                    is_title_fight=f_data.get("is_title_fight", False),
                    is_main_event=f_data.get("is_main_event", False),
                    rounds=f_data.get("rounds", 3),
                ))
            world.upcoming_events.append(event)
        
        # Restore year-end awards tracking
        world.current_year = data.get("current_year", world.calendar.current_date.year if world.calendar else 2025)
        world.yearly_fighter_wins = dict(data.get("yearly_fighter_wins", {}))
        world.yearly_fighter_finishes = dict(data.get("yearly_fighter_finishes", {}))
        world.yearly_fighter_title_wins = dict(data.get("yearly_fighter_title_wins", {}))
        world.yearly_prospect_wins = {k: tuple(v) for k, v in data.get("yearly_prospect_wins", {}).items()}
        world.yearly_best_fights = list(data.get("yearly_best_fights", []))
        world.yearly_best_kos = list(data.get("yearly_best_kos", []))
        world.yearly_best_subs = list(data.get("yearly_best_subs", []))
        world.yearly_total_fights = data.get("yearly_total_fights", 0)
        world.yearly_total_kos = data.get("yearly_total_kos", 0)
        world.yearly_total_subs = data.get("yearly_total_subs", 0)
        world.yearly_title_changes = data.get("yearly_title_changes", 0)
        world.yearly_new_champions = list(data.get("yearly_new_champions", []))
        
        # Restore awards history
        for awards_data in data.get("year_end_awards_history", []):
            world.year_end_awards_history.append(YearEndAwards.from_dict(awards_data))
        
        return world


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_world_simulation: Optional[WorldSimulation] = None


def get_world_simulation() -> WorldSimulation:
    """Get global world simulation instance"""
    global _world_simulation
    if _world_simulation is None:
        _world_simulation = WorldSimulation()
    return _world_simulation


def reset_world_simulation() -> None:
    """Reset global world simulation"""
    global _world_simulation
    _world_simulation = WorldSimulation()


def generate_personality_description(personality: CampPersonality) -> str:
    """Generate human-readable personality description"""
    philosophy_desc = {
        CampPhilosophy.STRIKER_FACTORY: "specializes in developing elite strikers",
        CampPhilosophy.GRAPPLING_ACADEMY: "focuses on wrestling and submission arts",
        CampPhilosophy.WELL_ROUNDED: "develops well-rounded fighters",
        CampPhilosophy.CARDIO_KINGS: "builds fighters with elite cardio",
        CampPhilosophy.POWER_HOUSE: "produces heavy-handed knockout artists",
    }
    
    risk_desc = {
        RiskTolerance.CONSERVATIVE: "plays it safe with matchmaking",
        RiskTolerance.MODERATE: "takes calculated risks",
        RiskTolerance.AGGRESSIVE: "actively seeks tough challenges",
        RiskTolerance.RECKLESS: "will fight anyone, anywhere, anytime",
    }
    
    talent_desc = {
        TalentStrategy.PROSPECT_DEVELOPER: "prefers signing young prospects",
        TalentStrategy.VETERAN_COLLECTOR: "targets experienced veterans",
        TalentStrategy.ELITE_HUNTER: "only signs elite talent",
        TalentStrategy.OPPORTUNIST: "takes opportunities as they come",
        TalentStrategy.HOMETOWN_HERO: "favors local fighters",
    }
    
    parts = [
        f"This camp {philosophy_desc[personality.philosophy]}",
        f"and {risk_desc[personality.risk_tolerance]}.",
        f"Management {talent_desc[personality.talent_strategy]}.",
    ]
    
    if personality.ambition > 70:
        parts.append("Known for aggressive title pursuits.")
    elif personality.ambition < 30:
        parts.append("Content with steady development over glory.")
    
    if personality.loyalty > 70:
        parts.append("Extremely loyal to their fighters.")
    elif personality.loyalty < 30:
        parts.append("Quick to cut underperformers.")
    
    return " ".join(parts)
