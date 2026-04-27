# simulation/ai_behavior.py
# Module: AI Behavior System
# Lines: ~1600
#
# Gives AI fighters and camps unique personalities with variance.
# Every decision has clear triggers and percentages.

"""
Cage Dynasty - AI Behavior System

This module defines HOW AI fighters and camps make decisions.
Every fighter is unique, every camp has its own style.

DESIGN PHILOSOPHY:
==================

1. CAMPS have organizational tendencies (who they sign, how they train)
2. FIGHTERS have individual personalities (risk tolerance, ambition, etc.)
3. DECISIONS are probability-based with clear modifiers
4. VARIANCE creates emergent storytelling

DECISION CATEGORIES:
===================

FIGHT OFFERS:
- Base acceptance: 50%
- Modified by: risk tolerance, matchup favorability, momentum, timing

TRAINING:
- Intensity selection: based on upcoming fight, personality
- Focus selection: based on camp philosophy, fighter weaknesses

ACTIVITY:
- How often fighter seeks fights
- When to take breaks

RETIREMENT:
- Age-based probability curve
- Record and injury factors

TARGETS:
- Who to call out
- Whether to avoid rematches

Each decision shows:
- Base probability
- All modifiers (+ and -)
- Final calculation
- Roll result
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math


# ============================================================================
# FIGHTER PERSONALITY TRAITS
# ============================================================================

class FighterMentality(Enum):
    """Core fighting mentality - affects all decisions."""
    WARRIOR = "warrior"           # Lives to fight, takes any challenge
    BUSINESSMAN = "businessman"   # Treats it as career, smart choices
    GLORY_SEEKER = "glory_seeker" # Wants titles and fame, big stages
    JOURNEYMAN = "journeyman"     # Steady paycheck, stays active
    KILLER = "killer"             # Wants to hurt people, aggressive
    TECHNICIAN = "technician"     # Perfects craft, careful selection


class ActivityPreference(Enum):
    """How often fighter wants to compete."""
    VERY_ACTIVE = "very_active"     # Fights every 6-8 weeks
    ACTIVE = "active"               # Fights every 10-14 weeks
    NORMAL = "normal"               # Fights every 16-20 weeks
    SELECTIVE = "selective"         # Fights every 24-30 weeks
    INACTIVE = "inactive"           # 30+ weeks, only big fights


class RiskProfile(Enum):
    """Fighter's risk tolerance."""
    RECKLESS = "reckless"           # Takes any fight, doesn't care
    AGGRESSIVE = "aggressive"       # Prefers tough fights, builds legacy
    BALANCED = "balanced"           # Weighs risk vs reward
    CAUTIOUS = "cautious"           # Protects record, avoids danger
    COWARDLY = "cowardly"           # Ducks tough fights when possible


class FinishingInstinct(Enum):
    """How fighter approaches hurt opponents."""
    KILLER_INSTINCT = "killer"      # Goes for finish immediately
    MEASURED = "measured"           # Tests waters, then finishes
    CONSERVATIVE = "conservative"   # Takes no risks, coasts
    POINT_FIGHTER = "point_fighter" # Happy to decision


class TrainingDedication(Enum):
    """How seriously fighter trains."""
    OBSESSED = "obsessed"           # Lives in gym, maximum gains
    DEDICATED = "dedicated"         # Consistent hard work
    PROFESSIONAL = "professional"   # Does what's needed
    CASUAL = "casual"               # Shows up, not intense
    LAZY = "lazy"                   # Party lifestyle


# ============================================================================
# PERSONALITY DATA CLASS
# ============================================================================

@dataclass
class FighterPersonality:
    """
    Individual fighter's personality affecting all decisions.
    
    Every fighter has unique traits that determine:
    - Fight acceptance patterns
    - Training dedication
    - Retirement timing
    - Target selection
    - Activity level
    """
    fighter_id: str
    
    # Core traits (enums)
    mentality: FighterMentality = FighterMentality.BUSINESSMAN
    activity: ActivityPreference = ActivityPreference.NORMAL
    risk_profile: RiskProfile = RiskProfile.BALANCED
    finishing: FinishingInstinct = FinishingInstinct.MEASURED
    dedication: TrainingDedication = TrainingDedication.PROFESSIONAL
    
    # Numeric traits (0-100)
    confidence: int = 50           # Self-belief, affects fight acceptance
    ego: int = 50                  # Won't take "easy" fights if high
    loyalty: int = 50              # Stays with camp, rematches rivals
    composure: int = 50            # Handles pressure, big fights
    intelligence: int = 50         # Makes smart career decisions
    heart: int = 50                # Fights through adversity
    volatility: int = 50           # Unpredictable, makes wild choices
    
    # Specific preferences
    wants_title: bool = True       # Actively pursuing championship
    will_fight_down: bool = True   # Will fight lower ranked opponents
    avoids_rematches: bool = False # Doesn't like fighting same person
    revenge_driven: bool = False   # MUST rematch people who beat them
    short_notice_fighter: bool = False  # Takes last-minute fights
    
    # Tracked state
    losses_before_breakdown: int = 3  # How many losses before crisis
    months_until_retirement_thoughts: int = 60  # When retirement enters mind
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "mentality": self.mentality.value,
            "activity": self.activity.value,
            "risk_profile": self.risk_profile.value,
            "finishing": self.finishing.value,
            "dedication": self.dedication.value,
            "confidence": self.confidence,
            "ego": self.ego,
            "loyalty": self.loyalty,
            "composure": self.composure,
            "intelligence": self.intelligence,
            "heart": self.heart,
            "volatility": self.volatility,
            "wants_title": self.wants_title,
            "will_fight_down": self.will_fight_down,
            "avoids_rematches": self.avoids_rematches,
            "revenge_driven": self.revenge_driven,
            "short_notice_fighter": self.short_notice_fighter,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FighterPersonality":
        return cls(
            fighter_id=data["fighter_id"],
            mentality=FighterMentality(data.get("mentality", "businessman")),
            activity=ActivityPreference(data.get("activity", "normal")),
            risk_profile=RiskProfile(data.get("risk_profile", "balanced")),
            finishing=FinishingInstinct(data.get("finishing", "measured")),
            dedication=TrainingDedication(data.get("dedication", "professional")),
            confidence=data.get("confidence", 50),
            ego=data.get("ego", 50),
            loyalty=data.get("loyalty", 50),
            composure=data.get("composure", 50),
            intelligence=data.get("intelligence", 50),
            heart=data.get("heart", 50),
            volatility=data.get("volatility", 50),
            wants_title=data.get("wants_title", True),
            will_fight_down=data.get("will_fight_down", True),
            avoids_rematches=data.get("avoids_rematches", False),
            revenge_driven=data.get("revenge_driven", False),
            short_notice_fighter=data.get("short_notice_fighter", False),
        )


# ============================================================================
# PERSONALITY GENERATION
# ============================================================================

def generate_fighter_personality(
    fighter_id: str,
    age: int = 25,
    wins: int = 0,
    losses: int = 0,
    is_champion: bool = False,
) -> FighterPersonality:
    """
    Generate a unique personality for a fighter.
    
    Personalities are evenly distributed for balance:
    - 17% Businessmen (smart career choices)
    - 17% Glory Seekers (ambitious types)
    - 17% Warriors (fight anyone)
    - 17% Journeymen (steady workers)
    - 16% Killers (aggressive finishers)
    - 16% Technicians (selective perfectionists)
    
    BALANCE NOTE: Even distribution ensures no mentality dominates
    the champion pool. Combat modifiers create differentiation.
    """
    # Evenly weighted mentality selection for balance
    mentality_weights = [
        (FighterMentality.BUSINESSMAN, 17),
        (FighterMentality.GLORY_SEEKER, 17),
        (FighterMentality.WARRIOR, 17),
        (FighterMentality.JOURNEYMAN, 17),
        (FighterMentality.KILLER, 16),
        (FighterMentality.TECHNICIAN, 16),
    ]
    mentality = _weighted_choice(mentality_weights)
    
    # Activity based on mentality
    if mentality == FighterMentality.WARRIOR:
        activity_weights = [
            (ActivityPreference.VERY_ACTIVE, 40),
            (ActivityPreference.ACTIVE, 35),
            (ActivityPreference.NORMAL, 20),
            (ActivityPreference.SELECTIVE, 5),
            (ActivityPreference.INACTIVE, 0),
        ]
    elif mentality == FighterMentality.JOURNEYMAN:
        activity_weights = [
            (ActivityPreference.VERY_ACTIVE, 30),
            (ActivityPreference.ACTIVE, 40),
            (ActivityPreference.NORMAL, 25),
            (ActivityPreference.SELECTIVE, 5),
            (ActivityPreference.INACTIVE, 0),
        ]
    elif mentality == FighterMentality.TECHNICIAN:
        activity_weights = [
            (ActivityPreference.VERY_ACTIVE, 5),
            (ActivityPreference.ACTIVE, 15),
            (ActivityPreference.NORMAL, 30),
            (ActivityPreference.SELECTIVE, 40),
            (ActivityPreference.INACTIVE, 10),
        ]
    else:
        activity_weights = [
            (ActivityPreference.VERY_ACTIVE, 15),
            (ActivityPreference.ACTIVE, 25),
            (ActivityPreference.NORMAL, 35),
            (ActivityPreference.SELECTIVE, 20),
            (ActivityPreference.INACTIVE, 5),
        ]
    activity = _weighted_choice(activity_weights)
    
    # Risk profile based on mentality
    if mentality == FighterMentality.WARRIOR:
        risk_weights = [
            (RiskProfile.RECKLESS, 30),
            (RiskProfile.AGGRESSIVE, 40),
            (RiskProfile.BALANCED, 25),
            (RiskProfile.CAUTIOUS, 5),
            (RiskProfile.COWARDLY, 0),
        ]
    elif mentality == FighterMentality.KILLER:
        risk_weights = [
            (RiskProfile.RECKLESS, 25),
            (RiskProfile.AGGRESSIVE, 50),
            (RiskProfile.BALANCED, 20),
            (RiskProfile.CAUTIOUS, 5),
            (RiskProfile.COWARDLY, 0),
        ]
    elif mentality in [FighterMentality.BUSINESSMAN, FighterMentality.TECHNICIAN]:
        risk_weights = [
            (RiskProfile.RECKLESS, 5),
            (RiskProfile.AGGRESSIVE, 15),
            (RiskProfile.BALANCED, 40),
            (RiskProfile.CAUTIOUS, 30),
            (RiskProfile.COWARDLY, 10),
        ]
    else:
        risk_weights = [
            (RiskProfile.RECKLESS, 10),
            (RiskProfile.AGGRESSIVE, 25),
            (RiskProfile.BALANCED, 35),
            (RiskProfile.CAUTIOUS, 25),
            (RiskProfile.COWARDLY, 5),
        ]
    risk = _weighted_choice(risk_weights)
    
    # Finishing instinct
    if mentality == FighterMentality.KILLER:
        finishing = FinishingInstinct.KILLER_INSTINCT
    elif mentality == FighterMentality.TECHNICIAN:
        finishing = random.choice([
            FinishingInstinct.CONSERVATIVE,
            FinishingInstinct.POINT_FIGHTER,
        ])
    else:
        finishing = random.choice(list(FinishingInstinct))
    
    # Dedication based on age and success
    if age < 25:
        # Young fighters can be anything
        dedication = random.choice(list(TrainingDedication))
    elif is_champion or wins > 15:
        # Successful fighters tend to be dedicated
        dedication_weights = [
            (TrainingDedication.OBSESSED, 20),
            (TrainingDedication.DEDICATED, 50),
            (TrainingDedication.PROFESSIONAL, 25),
            (TrainingDedication.CASUAL, 4),
            (TrainingDedication.LAZY, 1),
        ]
        dedication = _weighted_choice(dedication_weights)
    else:
        dedication = random.choice(list(TrainingDedication))
    
    # Numeric traits with bell curve
    confidence = _bell_curve_trait(50, 20)
    ego = _bell_curve_trait(50, 20)
    loyalty = _bell_curve_trait(50, 20)
    composure = _bell_curve_trait(50, 20)
    intelligence = _bell_curve_trait(50, 20)
    heart = _bell_curve_trait(50, 20)
    volatility = _bell_curve_trait(40, 25)  # Most not too volatile
    
    # Adjust traits based on mentality
    if mentality == FighterMentality.WARRIOR:
        heart = min(100, heart + 20)
        confidence = min(100, confidence + 10)
    elif mentality == FighterMentality.GLORY_SEEKER:
        ego = min(100, ego + 15)
        confidence = min(100, confidence + 10)
    elif mentality == FighterMentality.BUSINESSMAN:
        intelligence = min(100, intelligence + 15)
    elif mentality == FighterMentality.KILLER:
        confidence = min(100, confidence + 10)
        volatility = min(100, volatility + 15)
    
    # Champions are usually confident
    if is_champion:
        confidence = min(100, confidence + 20)
        ego = min(100, ego + 10)
    
    # Boolean preferences
    wants_title = mentality != FighterMentality.JOURNEYMAN or random.random() < 0.3
    will_fight_down = risk != RiskProfile.COWARDLY and random.random() < 0.7
    avoids_rematches = random.random() < 0.15
    revenge_driven = random.random() < 0.25
    short_notice = mentality == FighterMentality.WARRIOR or random.random() < 0.2
    
    return FighterPersonality(
        fighter_id=fighter_id,
        mentality=mentality,
        activity=activity,
        risk_profile=risk,
        finishing=finishing,
        dedication=dedication,
        confidence=confidence,
        ego=ego,
        loyalty=loyalty,
        composure=composure,
        intelligence=intelligence,
        heart=heart,
        volatility=volatility,
        wants_title=wants_title,
        will_fight_down=will_fight_down,
        avoids_rematches=avoids_rematches,
        revenge_driven=revenge_driven,
        short_notice_fighter=short_notice,
    )


def _weighted_choice(weights: List[Tuple[Any, int]]) -> Any:
    """Select from weighted options."""
    total = sum(w for _, w in weights)
    r = random.randint(1, total)
    cumulative = 0
    for item, weight in weights:
        cumulative += weight
        if r <= cumulative:
            return item
    return weights[-1][0]


def _bell_curve_trait(center: int, std_dev: int) -> int:
    """Generate a trait value with bell curve distribution."""
    value = random.gauss(center, std_dev)
    return max(5, min(95, int(value)))


# ============================================================================
# DECISION RESULT TRACKING
# ============================================================================

@dataclass
class DecisionBreakdown:
    """
    Complete breakdown of a decision for transparency.
    
    Shows exactly WHY a decision was made with all modifiers.
    """
    decision_type: str
    base_probability: float
    modifiers: List[Tuple[str, float]]  # (reason, modifier)
    final_probability: float
    roll: float
    result: bool
    result_reason: str
    
    def to_explanation(self) -> List[str]:
        """Generate human-readable explanation."""
        lines = [
            f"DECISION: {self.decision_type}",
            f"â”€" * 40,
            f"Base probability: {self.base_probability*100:.0f}%",
            "",
            "Modifiers:",
        ]
        
        for reason, mod in self.modifiers:
            sign = "+" if mod >= 0 else ""
            lines.append(f"  {reason}: {sign}{mod*100:.0f}%")
        
        lines.extend([
            "",
            f"Final probability: {self.final_probability*100:.0f}%",
            f"Roll: {self.roll*100:.0f}",
            f"Result: {'âœ… YES' if self.result else 'âŒ NO'}",
            f"Reason: {self.result_reason}",
        ])
        
        return lines


# ============================================================================
# AI DECISION ENGINE
# ============================================================================

class AIDecisionEngine:
    """
    Makes decisions for AI fighters and camps.
    
    Every decision is:
    1. Calculated from base probability
    2. Modified by personality and situation
    3. Resolved with random roll
    4. Logged with full breakdown
    """
    
    def __init__(self):
        self._decision_log: List[DecisionBreakdown] = []
    
    # =========================================================================
    # FIGHT OFFER DECISIONS
    # =========================================================================
    
    def evaluate_fight_offer(
        self,
        personality: FighterPersonality,
        # Fighter state
        fighter_rating: int,
        fighter_rank: Optional[int],
        is_champion: bool,
        wins: int,
        losses: int,
        win_streak: int,
        lose_streak: int,
        weeks_since_fight: int,
        # Opponent info
        opponent_rating: int,
        opponent_rank: Optional[int],
        opponent_id: str,
        # Fight info
        is_title_fight: bool,
        is_main_event: bool,
        weeks_out: int,
        purse: int,
        # History
        fought_before: bool = False,
        lost_to_opponent: bool = False,
    ) -> Tuple[bool, DecisionBreakdown]:
        """
        Evaluate whether to accept a fight offer.
        
        BASE PROBABILITY: 50%
        
        MODIFIERS BY CATEGORY:
        
        === MATCHUP FAVORABILITY ===
        Rating advantage (per 5 pts above): +5%
        Rating disadvantage (per 5 pts below): -5%
        Fighting UP in rankings (toward #1): +10%
        Fighting DOWN in rankings: -5% to -20%
        
        === PERSONALITY ===
        WARRIOR mentality: +20%
        KILLER mentality: +15%
        GLORY_SEEKER + title fight: +25%
        JOURNEYMAN: +10% (always wants to fight)
        BUSINESSMAN: Â±0% (neutral)
        TECHNICIAN: -10% (selective)
        
        Risk RECKLESS: +25%
        Risk AGGRESSIVE: +15%
        Risk BALANCED: Â±0%
        Risk CAUTIOUS: -15%
        Risk COWARDLY: -25%
        
        High confidence (>70): +10%
        Low confidence (<30): -15%
        High ego + easier opponent: -10% ("beneath me")
        
        === MOMENTUM ===
        On 3+ win streak: +10%
        On 5+ win streak: +15%
        On 2+ lose streak: -10% if tough fight
        On 2+ lose streak: +15% if easy fight ("need a win")
        
        === TIMING ===
        Short notice (<4 weeks): -20% (unless short_notice_fighter +10%)
        Standard (6-8 weeks): Â±0%
        Long camp (10+ weeks): +5%
        Haven't fought in 6+ months: +15%
        
        === SPECIAL ===
        Title fight: +20%
        Main event: +10%
        Revenge opportunity: +25% if revenge_driven
        Rematch when avoids_rematches: -30%
        Champion fighting unranked: -40%
        """
        modifiers: List[Tuple[str, float]] = []
        base = 0.50
        
        # === MATCHUP FAVORABILITY ===
        rating_diff = fighter_rating - opponent_rating
        
        if rating_diff >= 10:
            modifiers.append(("Large rating advantage", 0.10))
        elif rating_diff >= 5:
            modifiers.append(("Rating advantage", 0.05))
        elif rating_diff <= -10:
            modifiers.append(("Large rating disadvantage", -0.15))
        elif rating_diff <= -5:
            modifiers.append(("Rating disadvantage", -0.08))
        
        # Rank considerations
        if fighter_rank and opponent_rank:
            if opponent_rank < fighter_rank:  # Fighting up
                modifiers.append(("Fighting UP in rankings", 0.10))
            elif opponent_rank > fighter_rank + 5:  # Fighting way down
                if personality.ego > 60:
                    modifiers.append(("Opponent far below rank (ego)", -0.15))
                else:
                    modifiers.append(("Fighting down in rankings", -0.05))
        
        # === PERSONALITY: MENTALITY ===
        if personality.mentality == FighterMentality.WARRIOR:
            modifiers.append(("WARRIOR mentality: lives to fight", 0.20))
        elif personality.mentality == FighterMentality.KILLER:
            modifiers.append(("KILLER mentality: wants to hurt people", 0.15))
        elif personality.mentality == FighterMentality.GLORY_SEEKER:
            if is_title_fight:
                modifiers.append(("GLORY SEEKER: title opportunity!", 0.25))
            elif is_main_event:
                modifiers.append(("GLORY SEEKER: main event spotlight", 0.15))
            else:
                modifiers.append(("GLORY SEEKER: waiting for bigger stage", -0.10))
        elif personality.mentality == FighterMentality.JOURNEYMAN:
            modifiers.append(("JOURNEYMAN: always ready to work", 0.10))
        elif personality.mentality == FighterMentality.TECHNICIAN:
            modifiers.append(("TECHNICIAN: selective about opponents", -0.10))
        
        # === PERSONALITY: RISK PROFILE ===
        if personality.risk_profile == RiskProfile.RECKLESS:
            modifiers.append(("RECKLESS: takes any fight", 0.25))
        elif personality.risk_profile == RiskProfile.AGGRESSIVE:
            modifiers.append(("AGGRESSIVE: welcomes challenges", 0.15))
        elif personality.risk_profile == RiskProfile.CAUTIOUS:
            modifiers.append(("CAUTIOUS: careful selection", -0.15))
        elif personality.risk_profile == RiskProfile.COWARDLY:
            modifiers.append(("COWARDLY: avoids risk", -0.25))
        
        # === PERSONALITY: CONFIDENCE/EGO ===
        if personality.confidence > 70:
            modifiers.append(("High confidence", 0.10))
        elif personality.confidence < 30:
            modifiers.append(("Low confidence", -0.15))
        
        if personality.ego > 70 and rating_diff > 10:
            modifiers.append(("High ego: opponent beneath me", -0.10))
        
        # === MOMENTUM ===
        if win_streak >= 5:
            modifiers.append(("On 5+ win streak", 0.15))
        elif win_streak >= 3:
            modifiers.append(("On 3+ win streak", 0.10))
        
        if lose_streak >= 2:
            if rating_diff >= 5:
                modifiers.append(("Losing streak: need easier fight", 0.15))
            else:
                modifiers.append(("Losing streak: risky fight", -0.10))
        
        # === TIMING ===
        if weeks_out < 4:
            if personality.short_notice_fighter:
                modifiers.append(("Short notice (but fine with it)", 0.05))
            else:
                modifiers.append(("Short notice concerns", -0.20))
        elif weeks_out >= 10:
            modifiers.append(("Long camp preparation", 0.05))
        
        if weeks_since_fight >= 26:  # 6+ months
            modifiers.append(("Ring rust concerns: need to fight", 0.15))
        elif weeks_since_fight >= 40:
            modifiers.append(("Extremely inactive: must fight", 0.25))
        
        # === SPECIAL SITUATIONS ===
        if is_title_fight:
            modifiers.append(("TITLE FIGHT opportunity", 0.20))
        elif is_main_event:
            modifiers.append(("Main event slot", 0.10))
        
        if fought_before:
            if personality.avoids_rematches:
                modifiers.append(("Avoids rematches", -0.30))
            elif lost_to_opponent and personality.revenge_driven:
                modifiers.append(("REVENGE opportunity!", 0.25))
            elif lost_to_opponent:
                modifiers.append(("Lost to opponent before", -0.10))
        
        # Champion special rules
        if is_champion:
            if opponent_rank is None or opponent_rank > 5:
                modifiers.append(("Champion: opponent not worthy", -0.40))
        
        # === VOLATILITY ===
        if personality.volatility > 70:
            wild_card = random.uniform(-0.15, 0.15)
            modifiers.append((f"Wild card decision", wild_card))
        
        # Calculate final probability
        final_prob = base + sum(mod for _, mod in modifiers)
        final_prob = max(0.05, min(0.95, final_prob))  # Clamp to 5%-95%
        
        # Roll
        roll = random.random()
        result = roll < final_prob
        
        # Generate reason
        if result:
            top_positives = [r for r, m in modifiers if m > 0]
            reason = top_positives[0] if top_positives else "Good opportunity"
        else:
            top_negatives = [r for r, m in modifiers if m < 0]
            reason = top_negatives[0] if top_negatives else "Not the right time"
        
        breakdown = DecisionBreakdown(
            decision_type="Fight Offer",
            base_probability=base,
            modifiers=modifiers,
            final_probability=final_prob,
            roll=roll,
            result=result,
            result_reason=reason,
        )
        
        self._decision_log.append(breakdown)
        return result, breakdown
    
    # =========================================================================
    # TRAINING INTENSITY DECISIONS
    # =========================================================================
    
    def select_training_intensity(
        self,
        personality: FighterPersonality,
        weeks_until_fight: Optional[int],
        current_fatigue: int,
        age: int,
        coming_off_loss: bool,
        coming_off_ko_loss: bool,
    ) -> Tuple[str, DecisionBreakdown]:
        """
        Select training intensity.
        
        OPTIONS:
        - LIGHT: Recovery mode (50% gains, 0% injury)
        - MODERATE: Standard (100% gains, 1% injury)
        - INTENSE: Hard push (150% gains, 3% injury)
        - EXTREME: Maximum (200% gains, 8% injury)
        
        BASE DISTRIBUTION:
        LIGHT: 15%, MODERATE: 50%, INTENSE: 30%, EXTREME: 5%
        
        MODIFIERS:
        
        === DEDICATION ===
        OBSESSED: EXTREME +25%, INTENSE +15%
        DEDICATED: INTENSE +10%
        PROFESSIONAL: no change
        CASUAL: LIGHT +15%, INTENSE -10%
        LAZY: LIGHT +30%, INTENSE -20%, EXTREME -5%
        
        === SITUATION ===
        Fight in <4 weeks: LIGHT +20% (taper)
        Fight in 4-6 weeks: INTENSE +10%
        Fight in 6-8 weeks: MODERATE +10%
        No fight scheduled: MODERATE +15%
        
        Coming off KO loss: LIGHT +20%
        High fatigue (>70): LIGHT +25%, EXTREME -5%
        Age >35: INTENSE -10%, EXTREME -5%
        
        === PERSONALITY ===
        WARRIOR mentality: INTENSE +10%
        KILLER mentality: EXTREME +10%
        """
        # Base weights
        weights = {
            "LIGHT": 15,
            "MODERATE": 50,
            "INTENSE": 30,
            "EXTREME": 5,
        }
        modifiers: List[Tuple[str, float]] = []
        
        # === DEDICATION ===
        if personality.dedication == TrainingDedication.OBSESSED:
            weights["EXTREME"] += 25
            weights["INTENSE"] += 15
            modifiers.append(("OBSESSED dedication", 0.0))
        elif personality.dedication == TrainingDedication.DEDICATED:
            weights["INTENSE"] += 10
            modifiers.append(("DEDICATED dedication", 0.0))
        elif personality.dedication == TrainingDedication.CASUAL:
            weights["LIGHT"] += 15
            weights["INTENSE"] -= 10
            modifiers.append(("CASUAL dedication", 0.0))
        elif personality.dedication == TrainingDedication.LAZY:
            weights["LIGHT"] += 30
            weights["INTENSE"] -= 20
            weights["EXTREME"] = max(0, weights["EXTREME"] - 5)
            modifiers.append(("LAZY dedication", 0.0))
        
        # === SITUATION ===
        if weeks_until_fight:
            if weeks_until_fight < 4:
                weights["LIGHT"] += 20
                modifiers.append(("Taper phase (fight soon)", 0.0))
            elif weeks_until_fight <= 6:
                weights["INTENSE"] += 10
                modifiers.append(("Peak training phase", 0.0))
            elif weeks_until_fight <= 8:
                weights["MODERATE"] += 10
                modifiers.append(("Building phase", 0.0))
        else:
            weights["MODERATE"] += 15
            modifiers.append(("No fight scheduled", 0.0))
        
        if coming_off_ko_loss:
            weights["LIGHT"] += 20
            modifiers.append(("Recovery from KO loss", 0.0))
        elif coming_off_loss:
            weights["INTENSE"] += 5
            modifiers.append(("Motivated after loss", 0.0))
        
        if current_fatigue > 70:
            weights["LIGHT"] += 25
            weights["EXTREME"] = max(0, weights["EXTREME"] - 5)
            modifiers.append(("High fatigue", 0.0))
        
        if age > 35:
            weights["INTENSE"] -= 10
            weights["EXTREME"] = max(0, weights["EXTREME"] - 5)
            modifiers.append(("Older fighter, preserving body", 0.0))
        
        # === PERSONALITY ===
        if personality.mentality == FighterMentality.WARRIOR:
            weights["INTENSE"] += 10
            modifiers.append(("WARRIOR trains hard", 0.0))
        elif personality.mentality == FighterMentality.KILLER:
            weights["EXTREME"] += 10
            modifiers.append(("KILLER pushes limits", 0.0))
        
        # Ensure non-negative
        weights = {k: max(0, v) for k, v in weights.items()}
        
        # Select
        total = sum(weights.values())
        roll = random.randint(1, total)
        cumulative = 0
        result = "MODERATE"
        for intensity, weight in weights.items():
            cumulative += weight
            if roll <= cumulative:
                result = intensity
                break
        
        # Create breakdown
        weight_str = ", ".join([f"{k}:{v}" for k, v in weights.items()])
        breakdown = DecisionBreakdown(
            decision_type="Training Intensity",
            base_probability=weights[result] / total,
            modifiers=modifiers,
            final_probability=weights[result] / total,
            roll=roll / total,
            result=True,
            result_reason=f"Selected {result} (weights: {weight_str})",
        )
        
        self._decision_log.append(breakdown)
        return result, breakdown
    
    # =========================================================================
    # RETIREMENT DECISION
    # =========================================================================
    
    def consider_retirement(
        self,
        personality: FighterPersonality,
        age: int,
        wins: int,
        losses: int,
        recent_record: Tuple[int, int],  # Last 5 fights (wins, losses)
        is_champion: bool,
        ko_losses_career: int,
        months_since_last_win: int,
        has_title_shot_coming: bool = False,
        money_secure: bool = False,
    ) -> Tuple[bool, DecisionBreakdown]:
        """
        Consider whether to retire.
        
        BASE PROBABILITY BY AGE:
        - Under 30: 1%
        - 30-33: 3%
        - 34-35: 8%
        - 36-37: 15%
        - 38-39: 25%
        - 40+: 40%
        
        MODIFIERS:
        
        === CAREER SUCCESS ===
        Retired as champion: +15% (go out on top)
        Recent record 0-3 or worse: +20%
        Recent record 4-1 or better: -10%
        Never won title (age 35+): +10%
        
        === PHYSICAL ===
        3+ KO losses career: +15%
        5+ KO losses: +30%
        Haven't won in 12+ months: +15%
        
        === PERSONALITY ===
        WARRIOR mentality: -20% (never quits)
        BUSINESSMAN + money secure: +15%
        High intelligence + declining: +10%
        High heart: -15%
        
        === OPPORTUNITIES ===
        Title shot coming: -25%
        Big money fight available: -15%
        """
        modifiers: List[Tuple[str, float]] = []
        
        # === BASE BY AGE ===
        if age < 30:
            base = 0.01
        elif age <= 33:
            base = 0.03
        elif age <= 35:
            base = 0.08
        elif age <= 37:
            base = 0.15
        elif age <= 39:
            base = 0.25
        else:
            base = 0.40
        
        modifiers.append((f"Age {age} base retirement rate", 0.0))
        
        # === CAREER SUCCESS ===
        if is_champion:
            modifiers.append(("Go out as champion?", 0.15))
        
        recent_wins, recent_losses = recent_record
        if recent_losses >= 3 and recent_wins == 0:
            modifiers.append(("On bad losing skid", 0.20))
        elif recent_losses >= 2 and recent_wins <= 1:
            modifiers.append(("Recent struggles", 0.10))
        elif recent_wins >= 4:
            modifiers.append(("Still winning consistently", -0.10))
        
        if age >= 35 and not is_champion and wins < 20:
            modifiers.append(("Never reached top, age catching up", 0.10))
        
        # === PHYSICAL ===
        if ko_losses_career >= 5:
            modifiers.append(("Many KO losses, health concerns", 0.30))
        elif ko_losses_career >= 3:
            modifiers.append(("Accumulating KO losses", 0.15))
        
        if months_since_last_win >= 18:
            modifiers.append(("Long time without winning", 0.20))
        elif months_since_last_win >= 12:
            modifiers.append(("Haven't won in over a year", 0.15))
        
        # === PERSONALITY ===
        if personality.mentality == FighterMentality.WARRIOR:
            modifiers.append(("WARRIOR: never quits", -0.20))
        elif personality.mentality == FighterMentality.BUSINESSMAN:
            if money_secure:
                modifiers.append(("Smart businessman, financially set", 0.15))
        
        if personality.intelligence > 70 and recent_losses > recent_wins:
            modifiers.append(("High IQ: knows when to stop", 0.10))
        
        if personality.heart > 70:
            modifiers.append(("Too much heart to quit", -0.15))
        
        # === OPPORTUNITIES ===
        if has_title_shot_coming:
            modifiers.append(("Title shot coming!", -0.25))
        
        # Calculate
        final_prob = base + sum(mod for _, mod in modifiers)
        final_prob = max(0.01, min(0.80, final_prob))  # Never guaranteed
        
        roll = random.random()
        result = roll < final_prob
        
        if result:
            reason = "It's time to hang up the gloves"
        else:
            top_negatives = [r for r, m in modifiers if m < 0]
            reason = top_negatives[0] if top_negatives else "Still has more to give"
        
        breakdown = DecisionBreakdown(
            decision_type="Retirement",
            base_probability=base,
            modifiers=modifiers,
            final_probability=final_prob,
            roll=roll,
            result=result,
            result_reason=reason,
        )
        
        self._decision_log.append(breakdown)
        return result, breakdown
    
    # =========================================================================
    # TARGET SELECTION (WHO TO CALL OUT)
    # =========================================================================
    
    def select_target(
        self,
        personality: FighterPersonality,
        fighter_rank: Optional[int],
        is_champion: bool,
        available_opponents: List[Dict[str, Any]],
        rival_ids: List[str],
        lost_to_ids: List[str],
    ) -> Tuple[Optional[str], DecisionBreakdown]:
        """
        Select who to call out for a fight.
        
        SCORING SYSTEM (per opponent):
        Base score: 50
        
        RANK TARGETING:
        Champion (for non-champ): +40
        Higher ranked: +20
        Similar ranked (Â±2): +10
        Lower ranked: -10 per rank below
        Unranked (for ranked): -30
        
        PERSONALITY EFFECTS:
        GLORY_SEEKER: Champion +20, Main events +15
        WARRIOR: Toughest opponent +15
        BUSINESSMAN: Most winnable +20
        KILLER: Highest ranked available +15
        
        HISTORY:
        Rival: +25
        Lost to them before (revenge): +30 if revenge_driven, else +10
        Recently beat them: -20
        
        RISK PROFILE:
        RECKLESS: Ignores difficulty, adds randomness
        AGGRESSIVE: Targets up
        CAUTIOUS: Targets similar or down
        COWARDLY: Targets significantly down
        """
        if not available_opponents:
            return None, DecisionBreakdown(
                decision_type="Target Selection",
                base_probability=0,
                modifiers=[],
                final_probability=0,
                roll=0,
                result=False,
                result_reason="No opponents available",
            )
        
        modifiers: List[Tuple[str, float]] = []
        scores: Dict[str, float] = {}
        
        for opp in available_opponents:
            opp_id = opp.get("fighter_id", "unknown")
            opp_rank = opp.get("rank")
            opp_is_champion = opp.get("is_champion", False)
            opp_rating = opp.get("rating", 50)
            
            score = 50.0
            opp_mods: List[str] = []
            
            # === RANK TARGETING ===
            if opp_is_champion and not is_champion:
                score += 40
                opp_mods.append("Title shot")
            elif fighter_rank and opp_rank:
                rank_diff = fighter_rank - opp_rank
                if rank_diff > 0:  # Opponent ranked higher (lower number)
                    score += 20
                    opp_mods.append("Higher ranked")
                elif abs(rank_diff) <= 2:
                    score += 10
                    opp_mods.append("Similar rank")
                else:
                    score -= 10 * abs(rank_diff)
                    opp_mods.append("Lower ranked")
            elif fighter_rank and not opp_rank:
                score -= 30
                opp_mods.append("Unranked")
            
            # === PERSONALITY EFFECTS ===
            if personality.mentality == FighterMentality.GLORY_SEEKER:
                if opp_is_champion:
                    score += 20
                    opp_mods.append("Glory seeker wants title")
            elif personality.mentality == FighterMentality.WARRIOR:
                if opp_rating > 75:
                    score += 15
                    opp_mods.append("Warrior wants toughest")
            elif personality.mentality == FighterMentality.BUSINESSMAN:
                # Prefers winnable fights
                if opp_rating < 70:
                    score += 20
                    opp_mods.append("Businessman prefers winnable")
            elif personality.mentality == FighterMentality.KILLER:
                if opp_rank and opp_rank <= 5:
                    score += 15
                    opp_mods.append("Killer wants top competition")
            
            # === HISTORY ===
            if opp_id in rival_ids:
                score += 25
                opp_mods.append("Rivalry")
            
            if opp_id in lost_to_ids:
                if personality.revenge_driven:
                    score += 30
                    opp_mods.append("Revenge!")
                else:
                    score += 10
                    opp_mods.append("Rematch")
            
            # === RISK PROFILE ===
            if personality.risk_profile == RiskProfile.RECKLESS:
                score += random.uniform(-20, 30)  # Wild card
            elif personality.risk_profile == RiskProfile.AGGRESSIVE:
                if opp_rank and fighter_rank and opp_rank < fighter_rank:
                    score += 15
            elif personality.risk_profile == RiskProfile.CAUTIOUS:
                if opp_rating > 80:
                    score -= 20
            elif personality.risk_profile == RiskProfile.COWARDLY:
                if opp_rating > 70:
                    score -= 30
            
            scores[opp_id] = max(1, score)
            modifiers.append((f"{opp.get('name', opp_id)}: {opp_mods}", score - 50))
        
        # Select based on scores (weighted random)
        total = sum(scores.values())
        roll = random.uniform(0, total)
        cumulative = 0
        selected = list(scores.keys())[0]
        
        for opp_id, score in scores.items():
            cumulative += score
            if roll <= cumulative:
                selected = opp_id
                break
        
        # Find selected opponent name
        selected_name = next(
            (o.get("name", selected) for o in available_opponents 
             if o.get("fighter_id") == selected),
            selected
        )
        
        breakdown = DecisionBreakdown(
            decision_type="Target Selection",
            base_probability=scores[selected] / total,
            modifiers=modifiers,
            final_probability=scores[selected] / total,
            roll=roll / total,
            result=True,
            result_reason=f"Selected {selected_name}",
        )
        
        self._decision_log.append(breakdown)
        return selected, breakdown
    
    # =========================================================================
    # ACTIVITY LEVEL (WHEN TO SEEK FIGHTS)
    # =========================================================================
    
    def should_seek_fight(
        self,
        personality: FighterPersonality,
        weeks_since_last_fight: int,
        has_scheduled_fight: bool,
        is_injured: bool,
        is_in_camp: bool,
        current_fatigue: int,
        age: int,
    ) -> Tuple[bool, DecisionBreakdown]:
        """
        Determine if fighter should actively seek a fight.
        
        BASE PROBABILITY BY ACTIVITY PREFERENCE:
        VERY_ACTIVE: Check every week, 80% if >6 weeks since fight
        ACTIVE: Check every 2 weeks, 70% if >10 weeks
        NORMAL: Check every 4 weeks, 60% if >14 weeks
        SELECTIVE: Check every 6 weeks, 40% if >20 weeks
        INACTIVE: Check every 8 weeks, 25% if >30 weeks
        
        MODIFIERS:
        Already scheduled/injured/in camp: 0% (immediate return)
        High fatigue (>60): -30%
        Age >36: -15%
        WARRIOR mentality: +20%
        JOURNEYMAN: +15%
        """
        modifiers: List[Tuple[str, float]] = []
        
        # Immediate disqualifiers
        if has_scheduled_fight:
            return False, DecisionBreakdown(
                decision_type="Seek Fight",
                base_probability=0,
                modifiers=[("Already has fight scheduled", 0)],
                final_probability=0,
                roll=0,
                result=False,
                result_reason="Already has fight scheduled",
            )
        
        if is_injured:
            return False, DecisionBreakdown(
                decision_type="Seek Fight",
                base_probability=0,
                modifiers=[("Currently injured", 0)],
                final_probability=0,
                roll=0,
                result=False,
                result_reason="Currently injured",
            )
        
        if is_in_camp:
            return False, DecisionBreakdown(
                decision_type="Seek Fight",
                base_probability=0,
                modifiers=[("In training camp", 0)],
                final_probability=0,
                roll=0,
                result=False,
                result_reason="In training camp",
            )
        
        # Base by activity preference and time since fight
        if personality.activity == ActivityPreference.VERY_ACTIVE:
            if weeks_since_last_fight >= 6:
                base = 0.80
            elif weeks_since_last_fight >= 4:
                base = 0.50
            else:
                base = 0.20
        elif personality.activity == ActivityPreference.ACTIVE:
            if weeks_since_last_fight >= 10:
                base = 0.70
            elif weeks_since_last_fight >= 6:
                base = 0.40
            else:
                base = 0.10
        elif personality.activity == ActivityPreference.NORMAL:
            if weeks_since_last_fight >= 14:
                base = 0.60
            elif weeks_since_last_fight >= 10:
                base = 0.30
            else:
                base = 0.05
        elif personality.activity == ActivityPreference.SELECTIVE:
            if weeks_since_last_fight >= 20:
                base = 0.40
            elif weeks_since_last_fight >= 14:
                base = 0.15
            else:
                base = 0.02
        else:  # INACTIVE
            if weeks_since_last_fight >= 30:
                base = 0.25
            elif weeks_since_last_fight >= 20:
                base = 0.10
            else:
                base = 0.01
        
        modifiers.append((f"{personality.activity.value}: {weeks_since_last_fight} weeks since fight", 0.0))
        
        # === MODIFIERS ===
        if current_fatigue > 60:
            modifiers.append(("High fatigue, needs rest", -0.30))
        
        if age > 36:
            modifiers.append(("Older fighter, more selective", -0.15))
        
        if personality.mentality == FighterMentality.WARRIOR:
            modifiers.append(("WARRIOR: always ready", 0.20))
        elif personality.mentality == FighterMentality.JOURNEYMAN:
            modifiers.append(("JOURNEYMAN: needs to stay busy", 0.15))
        
        # Calculate
        final_prob = base + sum(mod for _, mod in modifiers)
        final_prob = max(0.01, min(0.95, final_prob))
        
        roll = random.random()
        result = roll < final_prob
        
        reason = "Looking for a fight" if result else "Not actively seeking fights right now"
        
        breakdown = DecisionBreakdown(
            decision_type="Seek Fight",
            base_probability=base,
            modifiers=modifiers,
            final_probability=final_prob,
            roll=roll,
            result=result,
            result_reason=reason,
        )
        
        self._decision_log.append(breakdown)
        return result, breakdown
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_recent_decisions(self, count: int = 10) -> List[DecisionBreakdown]:
        """Get recent decision breakdowns."""
        return self._decision_log[-count:]
    
    def clear_log(self) -> None:
        """Clear decision log."""
        self._decision_log.clear()


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_ai_engine() -> AIDecisionEngine:
    """Create a new AI decision engine."""
    return AIDecisionEngine()


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_personality(personality: FighterPersonality) -> List[str]:
    """Format personality for display."""
    lines = [
        "â•" * 50,
        f"  FIGHTER PERSONALITY: {personality.fighter_id}",
        "â•" * 50,
        f"  Mentality: {personality.mentality.value.upper()}",
        f"  Activity: {personality.activity.value}",
        f"  Risk Profile: {personality.risk_profile.value}",
        f"  Training: {personality.dedication.value}",
        "",
        "  Traits:",
        f"    Confidence: {personality.confidence}/100",
        f"    Ego: {personality.ego}/100",
        f"    Heart: {personality.heart}/100",
        f"    Intelligence: {personality.intelligence}/100",
        f"    Composure: {personality.composure}/100",
        f"    Volatility: {personality.volatility}/100",
        "",
        "  Preferences:",
        f"    Wants title: {'Yes' if personality.wants_title else 'No'}",
        f"    Will fight down: {'Yes' if personality.will_fight_down else 'No'}",
        f"    Revenge driven: {'Yes' if personality.revenge_driven else 'No'}",
        f"    Short notice OK: {'Yes' if personality.short_notice_fighter else 'No'}",
        "â•" * 50,
    ]
    return lines


def format_decision_breakdown(breakdown: DecisionBreakdown) -> List[str]:
    """Format decision breakdown for display."""
    return breakdown.to_explanation()


def describe_mentality(mentality: FighterMentality) -> str:
    """Get description of mentality type."""
    descriptions = {
        FighterMentality.WARRIOR: "Lives to fight. Takes any challenge. Never backs down.",
        FighterMentality.BUSINESSMAN: "Treats fighting as a career. Makes smart, calculated choices.",
        FighterMentality.GLORY_SEEKER: "Chases titles and fame. Wants the big stage.",
        FighterMentality.JOURNEYMAN: "Steady worker. Stays active. Reliable opponent.",
        FighterMentality.KILLER: "Violent. Wants to hurt opponents. Aggressive finisher.",
        FighterMentality.TECHNICIAN: "Perfectionist. Selective about opponents. Studies the game.",
    }
    return descriptions.get(mentality, "Unknown mentality")


# ============================================================================
# PERSONALITY ARCHETYPES (Pre-built common types)
# ============================================================================

def create_warrior_personality(fighter_id: str) -> FighterPersonality:
    """Create a warrior archetype - takes any fight."""
    return FighterPersonality(
        fighter_id=fighter_id,
        mentality=FighterMentality.WARRIOR,
        activity=ActivityPreference.VERY_ACTIVE,
        risk_profile=RiskProfile.RECKLESS,
        finishing=FinishingInstinct.KILLER_INSTINCT,
        dedication=TrainingDedication.DEDICATED,
        confidence=75,
        ego=40,
        heart=90,
        intelligence=45,
        short_notice_fighter=True,
        will_fight_down=True,
    )


def create_businessman_personality(fighter_id: str) -> FighterPersonality:
    """Create a businessman archetype - smart career choices."""
    return FighterPersonality(
        fighter_id=fighter_id,
        mentality=FighterMentality.BUSINESSMAN,
        activity=ActivityPreference.NORMAL,
        risk_profile=RiskProfile.CAUTIOUS,
        finishing=FinishingInstinct.MEASURED,
        dedication=TrainingDedication.PROFESSIONAL,
        confidence=60,
        ego=55,
        intelligence=80,
        will_fight_down=False,
    )


def create_glory_seeker_personality(fighter_id: str) -> FighterPersonality:
    """Create a glory seeker - wants titles and fame."""
    return FighterPersonality(
        fighter_id=fighter_id,
        mentality=FighterMentality.GLORY_SEEKER,
        activity=ActivityPreference.SELECTIVE,
        risk_profile=RiskProfile.AGGRESSIVE,
        finishing=FinishingInstinct.KILLER_INSTINCT,
        dedication=TrainingDedication.OBSESSED,
        confidence=80,
        ego=85,
        wants_title=True,
    )


def create_journeyman_personality(fighter_id: str) -> FighterPersonality:
    """Create a journeyman - reliable, active fighter."""
    return FighterPersonality(
        fighter_id=fighter_id,
        mentality=FighterMentality.JOURNEYMAN,
        activity=ActivityPreference.ACTIVE,
        risk_profile=RiskProfile.BALANCED,
        finishing=FinishingInstinct.CONSERVATIVE,
        dedication=TrainingDedication.PROFESSIONAL,
        confidence=50,
        ego=30,
        wants_title=False,
        will_fight_down=True,
    )


# ============================================================================
# CAMP PHILOSOPHY SYSTEM
# ============================================================================

class CampPhilosophy(Enum):
    """
    Camp training philosophy - defines identity and decision-making.
    
    Each philosophy affects:
    - Training focus defaults
    - Prospect signing preferences
    - Fight acceptance patterns
    - Fighter development priorities
    """
    STRIKING_FACTORY = "striking"      # ATT, Blackzilians - knockout artists
    GRAPPLING_ACADEMY = "grappling"    # AKA, Team Alpha Male - submission hunters
    WRESTLING_HEAVY = "wrestling"      # MMA Lab - control and ground-pound
    WELL_ROUNDED = "balanced"          # Jackson-Wink, Tristar - complete fighters
    KILLER_FACTORY = "killer"          # Chute Boxe style - ultra aggressive
    TECHNICAL = "technical"            # Firas Zahabi style - cerebral, patient
    VOLUME_HOUSE = "volume"            # High activity, always fighting
    CHAMPIONSHIP = "championship"      # Elite only, title-focused


class SigningStrategy(Enum):
    """How camp approaches signing new fighters."""
    PROSPECT_HUNTER = "prospect"       # Signs young, high-potential fighters
    VETERAN_COLLECTOR = "veteran"      # Signs experienced fighters
    BALANCED_ROSTER = "balanced"       # Mix of both
    ELITE_ONLY = "elite"               # Only signs proven talent
    QUANTITY = "quantity"              # Signs many, sees who develops


class MatchmakingStyle(Enum):
    """How camp approaches fight selection."""
    AGGRESSIVE = "aggressive"          # Seeks tough fights, builds legacy
    PROTECTIVE = "protective"          # Careful matchmaking, protects record
    OPPORTUNISTIC = "opportunistic"    # Takes advantageous fights
    RANKING_FOCUSED = "ranking"        # Prioritizes climbing rankings
    ACTIVITY_FOCUSED = "activity"      # Keeps fighters active


@dataclass
class CampPersonality:
    """
    Complete personality profile for an AI camp.
    
    Affects all camp-level decisions:
    - Who to sign
    - How to train
    - Which fights to take
    - Development priorities
    """
    camp_id: str
    camp_name: str = ""
    
    # Core identity
    philosophy: CampPhilosophy = CampPhilosophy.WELL_ROUNDED
    signing_strategy: SigningStrategy = SigningStrategy.BALANCED_ROSTER
    matchmaking_style: MatchmakingStyle = MatchmakingStyle.RANKING_FOCUSED
    
    # Training preferences (0-100, affects focus selection)
    striking_emphasis: int = 50        # How much camp values striking
    grappling_emphasis: int = 50       # How much camp values grappling
    wrestling_emphasis: int = 50       # How much camp values wrestling
    conditioning_emphasis: int = 50    # How much camp values cardio
    
    # Signing preferences (0-100)
    prefers_strikers: int = 50         # Preference for striking-based fighters
    prefers_grapplers: int = 50        # Preference for grappling-based fighters
    prefers_athletes: int = 50         # Preference for athletic specimens
    prefers_young: int = 50            # Preference for young prospects
    prefers_experienced: int = 50      # Preference for veterans
    risk_tolerance: int = 50           # Willingness to sign unproven talent
    minimum_potential: int = 60        # Minimum potential rating to consider
    
    # Fight selection preferences
    seeks_rankings: bool = True        # Prioritizes ranked fights
    avoids_bad_matchups: bool = False  # Protects fighters from stylistic nightmares
    allows_fighting_down: bool = True  # Lets ranked fighters fight unranked
    title_focused: bool = False        # Only takes fights leading to title
    
    # Activity preferences
    target_fights_per_year: int = 3    # How often camp wants fighters active
    minimum_camp_weeks: int = 6        # Minimum prep time required
    takes_short_notice: bool = False   # Accepts last-minute fights
    
    # Camp culture
    intensity_default: str = "moderate"  # LIGHT, MODERATE, INTENSE, EXTREME
    loyalty_culture: int = 50          # How loyal fighters tend to be
    pressure_handling: int = 50        # How well camp handles big moments
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "camp_name": self.camp_name,
            "philosophy": self.philosophy.value,
            "signing_strategy": self.signing_strategy.value,
            "matchmaking_style": self.matchmaking_style.value,
            "striking_emphasis": self.striking_emphasis,
            "grappling_emphasis": self.grappling_emphasis,
            "wrestling_emphasis": self.wrestling_emphasis,
            "conditioning_emphasis": self.conditioning_emphasis,
            "prefers_strikers": self.prefers_strikers,
            "prefers_grapplers": self.prefers_grapplers,
            "prefers_athletes": self.prefers_athletes,
            "prefers_young": self.prefers_young,
            "prefers_experienced": self.prefers_experienced,
            "risk_tolerance": self.risk_tolerance,
            "minimum_potential": self.minimum_potential,
            "seeks_rankings": self.seeks_rankings,
            "avoids_bad_matchups": self.avoids_bad_matchups,
            "allows_fighting_down": self.allows_fighting_down,
            "title_focused": self.title_focused,
            "target_fights_per_year": self.target_fights_per_year,
            "minimum_camp_weeks": self.minimum_camp_weeks,
            "takes_short_notice": self.takes_short_notice,
            "intensity_default": self.intensity_default,
            "loyalty_culture": self.loyalty_culture,
            "pressure_handling": self.pressure_handling,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampPersonality":
        return cls(
            camp_id=data["camp_id"],
            camp_name=data.get("camp_name", ""),
            philosophy=CampPhilosophy(data.get("philosophy", "balanced")),
            signing_strategy=SigningStrategy(data.get("signing_strategy", "balanced")),
            matchmaking_style=MatchmakingStyle(data.get("matchmaking_style", "ranking")),
            striking_emphasis=data.get("striking_emphasis", 50),
            grappling_emphasis=data.get("grappling_emphasis", 50),
            wrestling_emphasis=data.get("wrestling_emphasis", 50),
            conditioning_emphasis=data.get("conditioning_emphasis", 50),
            prefers_strikers=data.get("prefers_strikers", 50),
            prefers_grapplers=data.get("prefers_grapplers", 50),
            prefers_athletes=data.get("prefers_athletes", 50),
            prefers_young=data.get("prefers_young", 50),
            prefers_experienced=data.get("prefers_experienced", 50),
            risk_tolerance=data.get("risk_tolerance", 50),
            minimum_potential=data.get("minimum_potential", 60),
            seeks_rankings=data.get("seeks_rankings", True),
            avoids_bad_matchups=data.get("avoids_bad_matchups", False),
            allows_fighting_down=data.get("allows_fighting_down", True),
            title_focused=data.get("title_focused", False),
            target_fights_per_year=data.get("target_fights_per_year", 3),
            minimum_camp_weeks=data.get("minimum_camp_weeks", 6),
            takes_short_notice=data.get("takes_short_notice", False),
            intensity_default=data.get("intensity_default", "moderate"),
            loyalty_culture=data.get("loyalty_culture", 50),
            pressure_handling=data.get("pressure_handling", 50),
        )


# Philosophy templates - defines the "feel" of each camp type
PHILOSOPHY_TEMPLATES: Dict[CampPhilosophy, Dict[str, Any]] = {
    CampPhilosophy.STRIKING_FACTORY: {
        "striking_emphasis": 85,
        "grappling_emphasis": 35,
        "wrestling_emphasis": 45,
        "conditioning_emphasis": 60,
        "prefers_strikers": 80,
        "prefers_grapplers": 30,
        "prefers_athletes": 70,
        "default_focus": "striking",
        "intensity_default": "intense",
        "matchmaking_style": MatchmakingStyle.AGGRESSIVE,
        "description": "Known for producing knockout artists with heavy hands",
    },
    CampPhilosophy.GRAPPLING_ACADEMY: {
        "striking_emphasis": 40,
        "grappling_emphasis": 85,
        "wrestling_emphasis": 60,
        "conditioning_emphasis": 55,
        "prefers_strikers": 30,
        "prefers_grapplers": 85,
        "prefers_athletes": 50,
        "default_focus": "jiu_jitsu",
        "intensity_default": "moderate",
        "matchmaking_style": MatchmakingStyle.RANKING_FOCUSED,
        "description": "Submission specialists who hunt for finishes on the ground",
    },
    CampPhilosophy.WRESTLING_HEAVY: {
        "striking_emphasis": 45,
        "grappling_emphasis": 55,
        "wrestling_emphasis": 90,
        "conditioning_emphasis": 70,
        "prefers_strikers": 40,
        "prefers_grapplers": 60,
        "prefers_athletes": 80,
        "default_focus": "wrestling",
        "intensity_default": "intense",
        "matchmaking_style": MatchmakingStyle.AGGRESSIVE,
        "description": "Control-based fighters who dominate with wrestling",
    },
    CampPhilosophy.WELL_ROUNDED: {
        "striking_emphasis": 60,
        "grappling_emphasis": 60,
        "wrestling_emphasis": 60,
        "conditioning_emphasis": 65,
        "prefers_strikers": 50,
        "prefers_grapplers": 50,
        "prefers_athletes": 60,
        "default_focus": "balanced",
        "intensity_default": "moderate",
        "matchmaking_style": MatchmakingStyle.RANKING_FOCUSED,
        "description": "Develops complete mixed martial artists",
    },
    CampPhilosophy.KILLER_FACTORY: {
        "striking_emphasis": 75,
        "grappling_emphasis": 50,
        "wrestling_emphasis": 55,
        "conditioning_emphasis": 80,
        "prefers_strikers": 70,
        "prefers_grapplers": 40,
        "prefers_athletes": 75,
        "default_focus": "striking",
        "intensity_default": "extreme",
        "matchmaking_style": MatchmakingStyle.AGGRESSIVE,
        "avoids_bad_matchups": False,
        "takes_short_notice": True,
        "description": "Ultra-aggressive fighters who always bring violence",
    },
    CampPhilosophy.TECHNICAL: {
        "striking_emphasis": 65,
        "grappling_emphasis": 70,
        "wrestling_emphasis": 55,
        "conditioning_emphasis": 60,
        "prefers_strikers": 45,
        "prefers_grapplers": 55,
        "prefers_athletes": 40,
        "default_focus": "balanced",
        "intensity_default": "moderate",
        "matchmaking_style": MatchmakingStyle.PROTECTIVE,
        "avoids_bad_matchups": True,
        "minimum_camp_weeks": 8,
        "description": "Cerebral approach, masters of technique and strategy",
    },
    CampPhilosophy.VOLUME_HOUSE: {
        "striking_emphasis": 55,
        "grappling_emphasis": 50,
        "wrestling_emphasis": 50,
        "conditioning_emphasis": 75,
        "prefers_strikers": 50,
        "prefers_grapplers": 50,
        "prefers_athletes": 65,
        "default_focus": "conditioning",
        "intensity_default": "moderate",
        "matchmaking_style": MatchmakingStyle.ACTIVITY_FOCUSED,
        "target_fights_per_year": 4,
        "minimum_camp_weeks": 4,
        "takes_short_notice": True,
        "description": "Keeps fighters busy, believes in learning through competition",
    },
    CampPhilosophy.CHAMPIONSHIP: {
        "striking_emphasis": 70,
        "grappling_emphasis": 70,
        "wrestling_emphasis": 70,
        "conditioning_emphasis": 75,
        "prefers_strikers": 50,
        "prefers_grapplers": 50,
        "prefers_athletes": 70,
        "default_focus": "balanced",
        "intensity_default": "intense",
        "matchmaking_style": MatchmakingStyle.RANKING_FOCUSED,
        "title_focused": True,
        "minimum_potential": 75,
        "signing_strategy": SigningStrategy.ELITE_ONLY,
        "avoids_bad_matchups": True,
        "description": "Elite-focused camp that only deals in championship-level talent",
    },
}


def generate_camp_personality(
    camp_id: str,
    camp_name: str = "",
    tier: str = "LOCAL",
    philosophy: Optional[CampPhilosophy] = None,
) -> CampPersonality:
    """
    Generate a unique camp personality.
    
    Higher tier camps tend toward more refined philosophies.
    Each camp has variance even within their philosophy.
    """
    # Select philosophy based on tier if not specified
    if philosophy is None:
        if tier == "ELITE":
            weights = {
                CampPhilosophy.CHAMPIONSHIP: 30,
                CampPhilosophy.WELL_ROUNDED: 25,
                CampPhilosophy.TECHNICAL: 20,
                CampPhilosophy.STRIKING_FACTORY: 10,
                CampPhilosophy.GRAPPLING_ACADEMY: 10,
                CampPhilosophy.WRESTLING_HEAVY: 5,
            }
        elif tier == "NATIONAL":
            weights = {
                CampPhilosophy.WELL_ROUNDED: 25,
                CampPhilosophy.STRIKING_FACTORY: 20,
                CampPhilosophy.GRAPPLING_ACADEMY: 15,
                CampPhilosophy.WRESTLING_HEAVY: 15,
                CampPhilosophy.TECHNICAL: 15,
                CampPhilosophy.CHAMPIONSHIP: 10,
            }
        elif tier == "REGIONAL":
            weights = {
                CampPhilosophy.WELL_ROUNDED: 20,
                CampPhilosophy.STRIKING_FACTORY: 20,
                CampPhilosophy.GRAPPLING_ACADEMY: 15,
                CampPhilosophy.WRESTLING_HEAVY: 15,
                CampPhilosophy.VOLUME_HOUSE: 15,
                CampPhilosophy.KILLER_FACTORY: 15,
            }
        else:  # LOCAL, GARAGE
            weights = {
                CampPhilosophy.WELL_ROUNDED: 25,
                CampPhilosophy.VOLUME_HOUSE: 20,
                CampPhilosophy.STRIKING_FACTORY: 20,
                CampPhilosophy.KILLER_FACTORY: 15,
                CampPhilosophy.GRAPPLING_ACADEMY: 10,
                CampPhilosophy.WRESTLING_HEAVY: 10,
            }
        
        philosophies = list(weights.keys())
        probs = list(weights.values())
        philosophy = random.choices(philosophies, weights=probs)[0]
    
    # Get base template
    template = PHILOSOPHY_TEMPLATES.get(philosophy, PHILOSOPHY_TEMPLATES[CampPhilosophy.WELL_ROUNDED])
    
    # Create personality with variance
    def vary(base: int, variance: int = 15) -> int:
        return max(10, min(95, base + random.randint(-variance, variance)))
    
    # Select signing strategy based on philosophy
    if philosophy == CampPhilosophy.CHAMPIONSHIP:
        signing = SigningStrategy.ELITE_ONLY
    elif philosophy == CampPhilosophy.VOLUME_HOUSE:
        signing = SigningStrategy.QUANTITY
    elif philosophy in [CampPhilosophy.STRIKING_FACTORY, CampPhilosophy.GRAPPLING_ACADEMY]:
        signing = random.choice([SigningStrategy.PROSPECT_HUNTER, SigningStrategy.BALANCED_ROSTER])
    else:
        signing = random.choice(list(SigningStrategy))
    
    matchmaking = template.get("matchmaking_style", MatchmakingStyle.RANKING_FOCUSED)
    
    return CampPersonality(
        camp_id=camp_id,
        camp_name=camp_name,
        philosophy=philosophy,
        signing_strategy=signing,
        matchmaking_style=matchmaking,
        striking_emphasis=vary(template["striking_emphasis"]),
        grappling_emphasis=vary(template["grappling_emphasis"]),
        wrestling_emphasis=vary(template["wrestling_emphasis"]),
        conditioning_emphasis=vary(template["conditioning_emphasis"]),
        prefers_strikers=vary(template["prefers_strikers"]),
        prefers_grapplers=vary(template["prefers_grapplers"]),
        prefers_athletes=vary(template["prefers_athletes"]),
        prefers_young=vary(60 if signing == SigningStrategy.PROSPECT_HUNTER else 50),
        prefers_experienced=vary(70 if signing == SigningStrategy.VETERAN_COLLECTOR else 50),
        risk_tolerance=vary(70 if signing == SigningStrategy.PROSPECT_HUNTER else 40),
        minimum_potential=template.get("minimum_potential", 60),
        seeks_rankings=True,
        avoids_bad_matchups=template.get("avoids_bad_matchups", False),
        allows_fighting_down=philosophy != CampPhilosophy.CHAMPIONSHIP,
        title_focused=template.get("title_focused", False),
        target_fights_per_year=template.get("target_fights_per_year", 3),
        minimum_camp_weeks=template.get("minimum_camp_weeks", 6),
        takes_short_notice=template.get("takes_short_notice", False),
        intensity_default=template.get("intensity_default", "moderate"),
        loyalty_culture=vary(50),
        pressure_handling=vary(50 + (10 if tier in ["ELITE", "NATIONAL"] else 0)),
    )


def get_camp_philosophy_description(philosophy: CampPhilosophy) -> str:
    """Get human-readable description of camp philosophy."""
    template = PHILOSOPHY_TEMPLATES.get(philosophy)
    if template:
        return template.get("description", "A standard MMA training camp")
    return "A standard MMA training camp"


# ============================================================================
# TRAINING FOCUS SELECTION
# ============================================================================

# Training focus options
TRAINING_FOCUSES = ["striking", "wrestling", "jiu_jitsu", "conditioning", "strength", "balanced"]

# What stats each focus improves
FOCUS_ATTRIBUTES = {
    "striking": ["boxing", "kicks", "striking_defense", "head_movement"],
    "wrestling": ["wrestling", "takedown_defense", "top_control", "clinch"],
    "jiu_jitsu": ["bjj", "submissions", "guard", "sweeps"],
    "conditioning": ["cardio", "recovery", "chin"],
    "strength": ["strength", "power", "speed"],
    "balanced": ["boxing", "wrestling", "bjj", "cardio", "strength"],
}


def select_ai_training_focus(
    fighter_stats: Dict[str, int],
    opponent_stats: Optional[Dict[str, int]],
    camp_personality: CampPersonality,
    fighter_personality: Optional[FighterPersonality] = None,
) -> Tuple[str, List[Tuple[str, float]]]:
    """
    Select training focus for AI fighter based on multiple factors.
    
    Returns:
        Tuple of (selected_focus, reasoning_list)
    
    Decision factors:
    1. Camp philosophy (what camp is known for)
    2. Fighter's weaknesses (shore up gaps)
    3. Opponent's strengths (counter-train)
    4. Fighter personality (dedication affects choices)
    """
    scores: Dict[str, float] = {focus: 50.0 for focus in TRAINING_FOCUSES}
    reasoning: List[Tuple[str, float]] = []
    
    # === CAMP PHILOSOPHY (Base preference) ===
    philosophy = camp_personality.philosophy
    template = PHILOSOPHY_TEMPLATES.get(philosophy, {})
    default_focus = template.get("default_focus", "balanced")
    
    # Strong boost to camp's preferred focus
    scores[default_focus] += 25
    reasoning.append((f"Camp philosophy ({philosophy.value}): +25 to {default_focus}", 25))
    
    # Secondary emphasis based on camp training emphasis
    if camp_personality.striking_emphasis >= 70:
        scores["striking"] += 15
        reasoning.append(("Camp striking emphasis: +15 to striking", 15))
    if camp_personality.grappling_emphasis >= 70:
        scores["jiu_jitsu"] += 15
        reasoning.append(("Camp grappling emphasis: +15 to jiu_jitsu", 15))
    if camp_personality.wrestling_emphasis >= 70:
        scores["wrestling"] += 15
        reasoning.append(("Camp wrestling emphasis: +15 to wrestling", 15))
    if camp_personality.conditioning_emphasis >= 70:
        scores["conditioning"] += 10
        reasoning.append(("Camp conditioning emphasis: +10 to conditioning", 10))
    
    # === FIGHTER WEAKNESSES (Shore up gaps) ===
    if fighter_stats:
        # Find weakest areas
        striking_avg = (fighter_stats.get("boxing", 50) + fighter_stats.get("kicks", 50)) / 2
        grappling_avg = (fighter_stats.get("bjj", 50) + fighter_stats.get("wrestling", 50)) / 2
        cardio = fighter_stats.get("cardio", 50)
        
        # Boost weak areas
        if striking_avg < 55:
            scores["striking"] += 20
            reasoning.append(("Fighter weak at striking: +20", 20))
        if grappling_avg < 55:
            scores["jiu_jitsu"] += 10
            scores["wrestling"] += 10
            reasoning.append(("Fighter weak at grappling: +10 each", 10))
        if cardio < 55:
            scores["conditioning"] += 15
            reasoning.append(("Fighter has poor cardio: +15 to conditioning", 15))
    
    # === OPPONENT ANALYSIS (Counter-train) ===
    if opponent_stats:
        opp_striking = (opponent_stats.get("boxing", 50) + opponent_stats.get("kicks", 50)) / 2
        opp_wrestling = opponent_stats.get("wrestling", 50)
        opp_bjj = opponent_stats.get("bjj", 50)
        opp_cardio = opponent_stats.get("cardio", 50)
        
        # If opponent is a striker, improve takedown defense
        if opp_striking >= 70:
            scores["wrestling"] += 15
            reasoning.append(("Opponent is a striker, train wrestling: +15", 15))
        
        # If opponent is a wrestler, improve takedown defense
        if opp_wrestling >= 70:
            scores["wrestling"] += 20
            reasoning.append(("Opponent is a wrestler, train TDD: +20", 20))
        
        # If opponent has great BJJ, avoid ground or train wrestling to stay standing
        if opp_bjj >= 70:
            scores["wrestling"] += 10
            scores["jiu_jitsu"] += 10
            reasoning.append(("Opponent has dangerous BJJ: +10 wrestling, +10 BJJ", 10))
        
        # If opponent has poor cardio, train conditioning to push pace
        if opp_cardio < 55 and fighter_stats and fighter_stats.get("cardio", 50) >= 60:
            scores["conditioning"] += 15
            reasoning.append(("Opponent has poor cardio, push pace: +15 conditioning", 15))
    
    # === FIGHTER PERSONALITY ===
    if fighter_personality:
        if fighter_personality.dedication == TrainingDedication.OBSESSED:
            # Obsessed fighters focus on their main skill
            if fighter_stats:
                striking_avg = (fighter_stats.get("boxing", 50) + fighter_stats.get("kicks", 50)) / 2
                grappling_avg = (fighter_stats.get("bjj", 50) + fighter_stats.get("wrestling", 50)) / 2
                if striking_avg > grappling_avg + 10:
                    scores["striking"] += 10
                    reasoning.append(("OBSESSED striker doubles down: +10 striking", 10))
                elif grappling_avg > striking_avg + 10:
                    scores["jiu_jitsu"] += 10
                    reasoning.append(("OBSESSED grappler doubles down: +10 BJJ", 10))
        
        if fighter_personality.mentality == FighterMentality.KILLER:
            scores["striking"] += 10
            reasoning.append(("KILLER wants knockouts: +10 striking", 10))
        
        if fighter_personality.mentality == FighterMentality.TECHNICIAN:
            scores["balanced"] += 15
            reasoning.append(("TECHNICIAN prefers balance: +15 balanced", 15))
    
    # Add small randomness
    for focus in scores:
        scores[focus] += random.uniform(-5, 5)
    
    # Select highest scoring focus
    selected = max(scores, key=scores.get)
    
    return selected, reasoning


# ============================================================================
# AI TRAINING CAMP SYSTEM
# ============================================================================

@dataclass
class AITrainingCamp:
    """
    Training camp for an AI fighter preparing for a fight.
    
    Same system as player camps - weekly stat gains leading to fight.
    """
    camp_id: str
    fighter_id: str
    fighter_name: str
    opponent_id: str
    opponent_name: str
    
    focus: str                         # Training focus
    intensity: str = "moderate"        # LIGHT, MODERATE, INTENSE, EXTREME
    
    weeks_total: int = 6               # Total camp duration
    weeks_completed: int = 0           # Weeks done
    
    # Cumulative gains
    stat_gains: Dict[str, int] = field(default_factory=dict)
    total_gain_points: int = 0
    
    # Injury risk tracking
    injury_occurred: bool = False
    injury_type: str = ""
    
    @property
    def is_complete(self) -> bool:
        return self.weeks_completed >= self.weeks_total
    
    @property
    def weeks_remaining(self) -> int:
        return max(0, self.weeks_total - self.weeks_completed)
    
    def process_week(self, camp_quality_mult: float = 1.0) -> Dict[str, int]:
        """
        Process one week of training.
        
        Returns dict of stat gains for this week.
        """
        if self.is_complete:
            return {}
        
        self.weeks_completed += 1
        week_gains: Dict[str, int] = {}
        
        # Base gain chance based on intensity
        intensity_mults = {
            "light": 0.5,
            "moderate": 1.0,
            "intense": 1.5,
            "extreme": 2.0,
        }
        mult = intensity_mults.get(self.intensity.lower(), 1.0) * camp_quality_mult
        
        # Determine which stats can improve based on focus
        focus_stats = FOCUS_ATTRIBUTES.get(self.focus, FOCUS_ATTRIBUTES["balanced"])
        
        # Each stat has chance to gain 1 point
        base_chance = 0.15 * mult  # 15% base chance per stat
        
        for stat in focus_stats:
            if random.random() < base_chance:
                gain = 1
                if self.intensity.lower() == "extreme" and random.random() < 0.3:
                    gain = 2  # Extra gain chance on extreme
                week_gains[stat] = week_gains.get(stat, 0) + gain
                self.stat_gains[stat] = self.stat_gains.get(stat, 0) + gain
                self.total_gain_points += gain
        
        # Injury check for intense/extreme training
        if self.intensity.lower() == "intense" and random.random() < 0.02:
            self.injury_occurred = True
            self.injury_type = "minor strain"
        elif self.intensity.lower() == "extreme" and random.random() < 0.05:
            self.injury_occurred = True
            self.injury_type = random.choice(["muscle strain", "minor ligament sprain", "bruised rib"])
        
        return week_gains
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "opponent_id": self.opponent_id,
            "opponent_name": self.opponent_name,
            "focus": self.focus,
            "intensity": self.intensity,
            "weeks_total": self.weeks_total,
            "weeks_completed": self.weeks_completed,
            "stat_gains": self.stat_gains,
            "total_gain_points": self.total_gain_points,
            "injury_occurred": self.injury_occurred,
            "injury_type": self.injury_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AITrainingCamp":
        camp = cls(
            camp_id=data["camp_id"],
            fighter_id=data["fighter_id"],
            fighter_name=data.get("fighter_name", ""),
            opponent_id=data["opponent_id"],
            opponent_name=data.get("opponent_name", ""),
            focus=data.get("focus", "balanced"),
            intensity=data.get("intensity", "moderate"),
            weeks_total=data.get("weeks_total", 6),
            weeks_completed=data.get("weeks_completed", 0),
            injury_occurred=data.get("injury_occurred", False),
            injury_type=data.get("injury_type", ""),
        )
        camp.stat_gains = data.get("stat_gains", {})
        camp.total_gain_points = data.get("total_gain_points", 0)
        return camp


def create_ai_training_camp(
    fighter_id: str,
    fighter_name: str,
    fighter_stats: Dict[str, int],
    opponent_id: str,
    opponent_name: str,
    opponent_stats: Dict[str, int],
    camp_personality: CampPersonality,
    fighter_personality: Optional[FighterPersonality] = None,
    weeks_until_fight: int = 8,
) -> AITrainingCamp:
    """
    Create a training camp for an AI fighter.
    
    Automatically selects focus and intensity based on personalities.
    """
    import uuid
    
    # Select training focus
    focus, _ = select_ai_training_focus(
        fighter_stats=fighter_stats,
        opponent_stats=opponent_stats,
        camp_personality=camp_personality,
        fighter_personality=fighter_personality,
    )
    
    # Select intensity based on camp and fighter personality
    intensity = camp_personality.intensity_default
    if fighter_personality:
        if fighter_personality.dedication == TrainingDedication.OBSESSED:
            intensity = "extreme" if random.random() < 0.4 else "intense"
        elif fighter_personality.dedication == TrainingDedication.DEDICATED:
            intensity = "intense" if random.random() < 0.5 else "moderate"
        elif fighter_personality.dedication == TrainingDedication.LAZY:
            intensity = "light" if random.random() < 0.4 else "moderate"
    
    # Camp duration is based on weeks until fight (min 4, max weeks available - 1)
    camp_weeks = max(4, min(weeks_until_fight - 1, 8))
    
    return AITrainingCamp(
        camp_id=f"aicamp_{uuid.uuid4().hex[:8]}",
        fighter_id=fighter_id,
        fighter_name=fighter_name,
        opponent_id=opponent_id,
        opponent_name=opponent_name,
        focus=focus,
        intensity=intensity,
        weeks_total=camp_weeks,
    )


# ============================================================================
# PROSPECT EVALUATION
# ============================================================================

def evaluate_prospect_for_camp(
    camp_personality: CampPersonality,
    prospect_data: Dict[str, Any],
) -> Tuple[float, List[Tuple[str, float]]]:
    """
    Evaluate how desirable a prospect is for a specific camp.
    
    Returns:
        Tuple of (score 0-100, reasoning_list)
    
    Considers:
    - Camp signing strategy
    - Camp philosophy alignment
    - Prospect attributes and potential
    """
    score = 50.0
    reasoning: List[Tuple[str, float]] = []
    
    # Extract prospect data
    age = prospect_data.get("age", 22)
    potential = prospect_data.get("potential", 60)
    overall = prospect_data.get("overall", 50)
    
    # Skill averages
    striking = (prospect_data.get("boxing", 50) + prospect_data.get("kicks", 50)) / 2
    grappling = (prospect_data.get("bjj", 50) + prospect_data.get("wrestling", 50)) / 2
    athleticism = (prospect_data.get("speed", 50) + prospect_data.get("strength", 50) + 
                   prospect_data.get("cardio", 50)) / 3
    
    # === MINIMUM THRESHOLD ===
    if potential < camp_personality.minimum_potential:
        score -= 30
        reasoning.append((f"Below minimum potential ({potential} < {camp_personality.minimum_potential}): -30", -30))
    else:
        bonus = (potential - camp_personality.minimum_potential) * 0.5
        score += bonus
        reasoning.append((f"Above minimum potential: +{bonus:.0f}", bonus))
    
    # === SIGNING STRATEGY ===
    strategy = camp_personality.signing_strategy
    
    if strategy == SigningStrategy.PROSPECT_HUNTER:
        if age <= 23:
            score += 20
            reasoning.append(("Prospect hunter loves young talent: +20", 20))
        if potential >= 75:
            score += 15
            reasoning.append(("High potential prospect: +15", 15))
    
    elif strategy == SigningStrategy.VETERAN_COLLECTOR:
        if age >= 26:
            score += 15
            reasoning.append(("Veteran collector prefers experience: +15", 15))
        if age <= 22:
            score -= 10
            reasoning.append(("Too young for veteran collector: -10", -10))
    
    elif strategy == SigningStrategy.ELITE_ONLY:
        if overall >= 70:
            score += 25
            reasoning.append(("Elite-only camp impressed: +25", 25))
        else:
            score -= 20
            reasoning.append(("Not elite enough: -20", -20))
    
    elif strategy == SigningStrategy.QUANTITY:
        score += 10  # Signs almost anyone
        reasoning.append(("Volume signing camp: +10", 10))
    
    # === PHILOSOPHY ALIGNMENT ===
    philosophy = camp_personality.philosophy
    
    if philosophy in [CampPhilosophy.STRIKING_FACTORY, CampPhilosophy.KILLER_FACTORY]:
        if striking >= 65:
            score += 20
            reasoning.append(("Striking camp loves striker: +20", 20))
        elif striking < 50:
            score -= 10
            reasoning.append(("Striking camp dislikes non-striker: -10", -10))
    
    elif philosophy == CampPhilosophy.GRAPPLING_ACADEMY:
        if grappling >= 65:
            score += 20
            reasoning.append(("Grappling camp loves grappler: +20", 20))
        elif grappling < 50:
            score -= 10
            reasoning.append(("Grappling camp dislikes non-grappler: -10", -10))
    
    elif philosophy == CampPhilosophy.WRESTLING_HEAVY:
        wrestling = prospect_data.get("wrestling", 50)
        if wrestling >= 65:
            score += 20
            reasoning.append(("Wrestling camp loves wrestler: +20", 20))
    
    # === PREFERENCE ATTRIBUTES ===
    if camp_personality.prefers_strikers > 60 and striking >= 60:
        bonus = (camp_personality.prefers_strikers - 50) * 0.2
        score += bonus
        reasoning.append((f"Camp prefers strikers: +{bonus:.0f}", bonus))
    
    if camp_personality.prefers_grapplers > 60 and grappling >= 60:
        bonus = (camp_personality.prefers_grapplers - 50) * 0.2
        score += bonus
        reasoning.append((f"Camp prefers grapplers: +{bonus:.0f}", bonus))
    
    if camp_personality.prefers_athletes > 60 and athleticism >= 65:
        bonus = (camp_personality.prefers_athletes - 50) * 0.2
        score += bonus
        reasoning.append((f"Camp prefers athletes: +{bonus:.0f}", bonus))
    
    if camp_personality.prefers_young > 60 and age <= 23:
        bonus = (camp_personality.prefers_young - 50) * 0.2
        score += bonus
        reasoning.append((f"Camp prefers youth: +{bonus:.0f}", bonus))
    
    # === RISK TOLERANCE ===
    # High potential but low current = risky
    is_risky = potential >= 70 and overall < 55
    if is_risky:
        if camp_personality.risk_tolerance >= 60:
            score += 10
            reasoning.append(("Camp willing to take risk on upside: +10", 10))
        else:
            score -= 10
            reasoning.append(("Camp avoids risky signings: -10", -10))
    
    # Clamp score
    score = max(0, min(100, score))
    
    return score, reasoning


def should_camp_sign_prospect(
    camp_personality: CampPersonality,
    prospect_data: Dict[str, Any],
    camp_budget: int,
    roster_size: int,
    max_roster: int,
    signing_cost: int = 20000,
) -> Tuple[bool, str]:
    """
    Determine if camp should sign a prospect.
    
    Returns:
        Tuple of (should_sign, reason)
    """
    # Check roster space
    if roster_size >= max_roster:
        return False, "Roster full"
    
    # Check budget
    if camp_budget < signing_cost:
        return False, "Insufficient budget"
    
    # Evaluate prospect
    score, _ = evaluate_prospect_for_camp(camp_personality, prospect_data)
    
    # Decision threshold varies by signing strategy
    thresholds = {
        SigningStrategy.PROSPECT_HUNTER: 45,
        SigningStrategy.VETERAN_COLLECTOR: 50,
        SigningStrategy.BALANCED_ROSTER: 55,
        SigningStrategy.ELITE_ONLY: 70,
        SigningStrategy.QUANTITY: 35,
    }
    threshold = thresholds.get(camp_personality.signing_strategy, 55)
    
    if score >= threshold:
        return True, f"Prospect scored {score:.0f} (threshold: {threshold})"
    else:
        return False, f"Prospect scored {score:.0f} (below threshold: {threshold})"


# ============================================================================
# FIGHT ACCEPTANCE FOR CAMPS
# ============================================================================

def evaluate_fight_for_camp(
    camp_personality: CampPersonality,
    fighter_rank: Optional[int],
    fighter_is_champion: bool,
    opponent_rank: Optional[int],
    opponent_is_champion: bool,
    opponent_rating: int,
    fighter_rating: int,
    is_title_fight: bool = False,
    weeks_notice: int = 8,
) -> Tuple[bool, float, List[Tuple[str, float]]]:
    """
    Evaluate if camp would approve a fight.
    
    Returns:
        Tuple of (approve, probability, reasoning)
    
    Camp-level considerations beyond fighter personality.
    """
    probability = 0.60  # Base 60% approval
    reasoning: List[Tuple[str, float]] = []
    reasoning.append(("Base approval rate", 0.60))
    
    matchmaking = camp_personality.matchmaking_style
    
    # === MATCHMAKING STYLE ===
    if matchmaking == MatchmakingStyle.AGGRESSIVE:
        probability += 0.15
        reasoning.append(("Aggressive camp: +15%", 0.15))
    elif matchmaking == MatchmakingStyle.PROTECTIVE:
        if opponent_rating > fighter_rating + 10:
            probability -= 0.20
            reasoning.append(("Protective camp avoids tough fights: -20%", -0.20))
    elif matchmaking == MatchmakingStyle.OPPORTUNISTIC:
        if opponent_rating < fighter_rating - 5:
            probability += 0.15
            reasoning.append(("Opportunistic camp likes easy wins: +15%", 0.15))
    elif matchmaking == MatchmakingStyle.ACTIVITY_FOCUSED:
        probability += 0.10
        reasoning.append(("Activity-focused camp: +10%", 0.10))
    
    # === RANKING IMPLICATIONS ===
    if camp_personality.seeks_rankings:
        # Fighting up
        if opponent_rank and fighter_rank and opponent_rank < fighter_rank:
            probability += 0.15
            reasoning.append(("Ranking climb opportunity: +15%", 0.15))
        # Champion fighting unranked
        elif fighter_is_champion and not opponent_rank:
            probability -= 0.30
            reasoning.append(("Champion vs unranked rejected: -30%", -0.30))
    
    # === TITLE FOCUS ===
    if camp_personality.title_focused:
        if is_title_fight or opponent_is_champion:
            probability += 0.25
            reasoning.append(("Title-focused camp loves title implications: +25%", 0.25))
        elif not opponent_rank:
            probability -= 0.25
            reasoning.append(("Title-focused camp rejects non-ranked: -25%", -0.25))
    
    # === BAD MATCHUP AVOIDANCE ===
    if camp_personality.avoids_bad_matchups:
        if opponent_rating > fighter_rating + 10:
            probability -= 0.15
            reasoning.append(("Camp avoids stylistically tough: -15%", -0.15))
    
    # === FIGHTING DOWN ===
    if not camp_personality.allows_fighting_down:
        if fighter_rank and opponent_rank and opponent_rank > fighter_rank + 3:
            probability -= 0.20
            reasoning.append(("Camp doesn't fight down: -20%", -0.20))
        elif fighter_rank and not opponent_rank:
            probability -= 0.25
            reasoning.append(("Camp won't fight unranked: -25%", -0.25))
    
    # === NOTICE PERIOD ===
    if weeks_notice < camp_personality.minimum_camp_weeks:
        if camp_personality.takes_short_notice:
            probability -= 0.05
            reasoning.append(("Short notice but camp accepts: -5%", -0.05))
        else:
            probability -= 0.25
            reasoning.append((f"Insufficient notice ({weeks_notice} < {camp_personality.minimum_camp_weeks}): -25%", -0.25))
    
    # Clamp probability
    probability = max(0.05, min(0.95, probability))
    
    # Roll
    approve = random.random() < probability
    
    return approve, probability, reasoning


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "FighterMentality", "ActivityPreference", "RiskProfile",
    "FinishingInstinct", "TrainingDedication",
    "CampPhilosophy", "SigningStrategy", "MatchmakingStyle",
    
    # Data classes
    "FighterPersonality", "DecisionBreakdown",
    "CampPersonality", "AITrainingCamp",
    
    # Engine
    "AIDecisionEngine", "create_ai_engine",
    
    # Generation
    "generate_fighter_personality",
    "generate_camp_personality",
    "get_camp_philosophy_description",
    
    # Training
    "select_ai_training_focus",
    "create_ai_training_camp",
    "TRAINING_FOCUSES",
    "FOCUS_ATTRIBUTES",
    
    # Prospect evaluation
    "evaluate_prospect_for_camp",
    "should_camp_sign_prospect",
    
    # Fight acceptance
    "evaluate_fight_for_camp",
    
    # Archetypes
    "create_warrior_personality", "create_businessman_personality",
    "create_glory_seeker_personality", "create_journeyman_personality",
    
    # Display
    "format_personality", "format_decision_breakdown", "describe_mentality",
    
    # Constants
    "PHILOSOPHY_TEMPLATES",
]
