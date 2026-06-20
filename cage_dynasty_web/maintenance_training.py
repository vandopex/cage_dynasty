# systems/maintenance_training.py
# Module: Coach Maintenance Training & Stat Decay System
# Lines: ~750
#
# Handles passive fighter development between fight camps:
# - Coaches boost stats based on their SKILL RATINGS (not quality)
# - Decay prevention based on coach skill in each area
# - Stats that go too long without training/boosting decay
# - Creates ongoing value for skilled coaches

"""
Cage Dynasty - Maintenance Training & Stat Decay System (v2)

Updated to work with skill-based coach system.

COACH MAINTENANCE BOOSTS:
- Coaches work with fighters based on their skill ratings
- Higher skill in an area = more frequent/better boosts
- Coaches naturally focus on their strong areas

DECAY PREVENTION:
- Coach skill in an area prevents decay in those stats
- 90+ skill = 90% of decay prevented
- 50 skill = 35% of decay prevented
- Creates value for coaching coverage

STAT DECAY:
- Stats not trained/boosted in X weeks start decaying
- Physical stats decay faster than mental
- Coach skill reduces decay chance

USAGE:
    from systems.maintenance_training import (
        MaintenanceTrainingSystem,
        check_stat_decay,
    )
    
    system = MaintenanceTrainingSystem()
    boosts, decays, warnings = system.process_week(fighters, coaches, camps, current_week)
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import random


# ============================================================================
# COACH SYSTEM INTEGRATION
# ============================================================================

# Try to import from coaches module
COACHES_INTEGRATION_AVAILABLE = False
try:
    from systems.coaches import (
        SKILL_ATTRIBUTES,
        get_training_multiplier,
        get_decay_prevention,
        get_skill_for_attribute,
    )
    COACHES_INTEGRATION_AVAILABLE = True
except ImportError:
    # Fallback definitions — values use canonical fighter-stat names from
    # game_bridge.py:_TRAINABLE (M1 Phase 2a). Earlier versions used ghost
    # names (clinch/accuracy/wrestling/bjj/td_defense/power) that don't
    # exist on FighterRecord, silently breaking coach-skill→stat lookups.
    SKILL_ATTRIBUTES = {
        "striking": ["boxing", "kicks", "clinch_striking",
                     "clinch_control", "striking_defense"],
        "wrestling": ["takedowns", "takedown_defense", "top_control"],
        "jiu_jitsu": ["submissions", "guard"],
        "conditioning": ["cardio", "chin", "recovery"],
        "strength": ["strength", "speed"],
    }
    
    def get_skill_for_attribute(attribute: str) -> Optional[str]:
        """Get which coach skill affects a fighter attribute"""
        for skill, attrs in SKILL_ATTRIBUTES.items():
            if attribute in attrs:
                return skill
        return None
    
    def get_training_multiplier(skill_level: int) -> float:
        """Get training multiplier for a skill level"""
        if skill_level >= 90: return 1.30
        if skill_level >= 80: return 1.20
        if skill_level >= 70: return 1.10
        if skill_level >= 60: return 1.00
        if skill_level >= 50: return 0.90
        return 0.80
    
    def get_decay_prevention(skill_level: int) -> float:
        """Get decay prevention percentage for a skill level"""
        if skill_level >= 90: return 0.90
        if skill_level >= 80: return 0.80
        if skill_level >= 70: return 0.65
        if skill_level >= 60: return 0.50
        if skill_level >= 50: return 0.35
        return 0.20


# ============================================================================
# CONSTANTS
# ============================================================================

# Boost chance by coach skill level (replaces quality-based)
def get_boost_chance(skill_level: int) -> float:
    """Get boost chance based on coach skill in the relevant area."""
    if skill_level >= 90:
        return 0.18   # 18% per week
    elif skill_level >= 80:
        return 0.14   # 14% per week
    elif skill_level >= 70:
        return 0.10   # 10% per week
    elif skill_level >= 60:
        return 0.07   # 7% per week
    elif skill_level >= 50:
        return 0.05   # 5% per week
    else:
        return 0.03   # 3% per week


def get_boost_amount(skill_level: int) -> Tuple[int, int]:
    """Get boost amount range based on coach skill."""
    if skill_level >= 90:
        return (2, 4)
    elif skill_level >= 80:
        return (2, 3)
    elif skill_level >= 70:
        return (1, 3)
    elif skill_level >= 60:
        return (1, 2)
    else:
        return (1, 1)


# Legacy support - map old quality to approximate skill
QUALITY_TO_SKILL = {
    1: 45,
    2: 55,
    3: 65,
    4: 78,
    5: 90,
}

# Decay thresholds (weeks since last activity on INDIVIDUAL stat)
# Decay is gentle at first, becomes significant if truly neglected
DECAY_THRESHOLD_START = 8       # Start checking for decay after 8 weeks idle
DECAY_THRESHOLD_MODERATE = 10   # Moderate decay risk
DECAY_THRESHOLD_HIGH = 14       # Higher decay risk
DECAY_THRESHOLD_SIGNIFICANT = 18  # Significant decay - stat truly neglected
DECAY_THRESHOLD_SEVERE = 24     # Severe decay - major skill loss

# Decay chances per week once threshold is reached
DECAY_CHANCE = {
    "start": 0.12,        # 12% per week at 6-10 weeks
    "moderate": 0.20,     # 20% per week at 10-14 weeks  
    "high": 0.30,         # 30% per week at 14-18 weeks
    "significant": 0.45,  # 45% per week at 18-24 weeks
    "severe": 0.60,       # 60% per week at 24+ weeks
}

# Decay amounts (min, max) - weighted toward lower end for early tiers
# Early decay: 1-3 (mostly 1s)
# Significant decay: 5-8 (truly neglected stats)
DECAY_AMOUNT = {
    "start": (1, 2),        # 6-10 weeks: mostly 1, sometimes 2
    "moderate": (1, 3),     # 10-14 weeks: 1-3, weighted low
    "high": (2, 4),         # 14-18 weeks: 2-4
    "significant": (5, 8),  # 18-24 weeks: significant drop
    "severe": (6, 10),      # 24+ weeks: major skill loss
}

# Weighted decay - early tiers favor lower amounts
DECAY_WEIGHT_LOW = {
    "start": 0.70,       # 70% chance of minimum amount
    "moderate": 0.60,    # 60% chance of minimum amount
    "high": 0.40,        # 40% chance of minimum amount
    "significant": 0.30, # 30% chance of minimum amount
    "severe": 0.20,      # 20% chance of minimum amount
}

# Physical stats decay 50% faster
PHYSICAL_DECAY_MULTIPLIER = 1.5

# Mental stats decay 50% slower
MENTAL_DECAY_MULTIPLIER = 0.5

# Stat categories
# M1 Phase 2a: aligned to canonical 17-stat schema in game_bridge.py:_TRAINABLE.
# Earlier versions used ghost names (wrestling/bjj/accuracy/iq/power/td_defense/
# clinch) that don't exist on FighterRecord — decay rolled and printed warnings
# but setattr() silently no-op'd. Critical real stats (takedown_defense,
# striking_defense, guard) were entirely untracked.
PHYSICAL_STATS = {"strength", "speed", "cardio", "chin", "recovery"}
STRIKING_STATS = {"boxing", "kicks", "clinch_striking",
                   "clinch_control", "striking_defense"}
GRAPPLING_STATS = {"takedowns", "takedown_defense", "top_control", "submissions", "guard"}
MENTAL_STATS = {"heart", "fight_iq", "composure"}

# All trainable stats
ALL_STATS = PHYSICAL_STATS | STRIKING_STATS | GRAPPLING_STATS | MENTAL_STATS

# Minimum stat value (can't decay below this)
MIN_STAT_VALUE = 25

# Maximum stat value (can't boost above this)
MAX_STAT_VALUE = 99


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class StatActivity:
    """Tracks when each stat was last trained or boosted."""
    last_activity_week: Dict[str, int] = field(default_factory=dict)
    
    def record_activity(self, stat: str, week: int) -> None:
        """Record that a stat was trained/boosted this week."""
        self.last_activity_week[stat] = week
    
    def record_multiple(self, stats: List[str], week: int) -> None:
        """Record activity for multiple stats."""
        for stat in stats:
            self.last_activity_week[stat] = week
    
    def weeks_since_activity(self, stat: str, current_week: int) -> int:
        """Get weeks since this stat was last active."""
        last_week = self.last_activity_week.get(stat, 0)
        if last_week == 0:
            return 999  # Never trained - but we'll initialize on first use
        return current_week - last_week
    
    def get_idle_stats(self, current_week: int, threshold: int = DECAY_THRESHOLD_START) -> List[str]:
        """Get stats that have been idle longer than threshold."""
        idle = []
        for stat in ALL_STATS:
            if self.weeks_since_activity(stat, current_week) >= threshold:
                idle.append(stat)
        return idle
    
    def to_dict(self) -> Dict[str, Any]:
        return {"last_activity_week": self.last_activity_week.copy()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatActivity':
        activity = cls()
        activity.last_activity_week = data.get("last_activity_week", {})
        return activity


@dataclass
class MaintenanceBoost:
    """Record of a coach maintenance boost."""
    fighter_id: str
    fighter_name: str
    coach_id: str
    coach_name: str
    stat: str
    amount: int
    week: int
    specialty_match: bool = False
    coach_skill: int = 50  # New: track the coach skill level used
    
    @property
    def headline(self) -> str:
        """Generate news headline for this boost."""
        if self.amount >= 3:
            return f"ðŸ’ª {self.coach_name} breakthrough session with {self.fighter_name} (+{self.amount} {self.stat})"
        elif self.specialty_match:
            return f"ðŸ“ˆ {self.coach_name} refining {self.fighter_name}'s {self.stat}"
        else:
            return f"ðŸ‹ï¸ {self.fighter_name} improving {self.stat} under {self.coach_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "coach_id": self.coach_id,
            "coach_name": self.coach_name,
            "stat": self.stat,
            "amount": self.amount,
            "week": self.week,
            "specialty_match": self.specialty_match,
            "coach_skill": self.coach_skill,
        }


@dataclass
class StatDecay:
    """Record of stat decay."""
    fighter_id: str
    fighter_name: str
    stat: str
    amount: int
    weeks_idle: int
    week: int
    prevented_amount: int = 0  # New: how much was prevented by coaches
    
    @property
    def headline(self) -> str:
        """Generate news headline for decay."""
        if self.weeks_idle >= DECAY_THRESHOLD_SEVERE:
            return f"âš ï¸ {self.fighter_name}'s {self.stat} deteriorating from inactivity"
        else:
            return f"ðŸ“‰ {self.fighter_name}'s {self.stat} getting rusty (-{self.amount})"
    
    @property
    def warning_message(self) -> str:
        """Generate warning for player."""
        return f"{self.fighter_name}'s {self.stat} declined by {self.amount} due to lack of training"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "stat": self.stat,
            "amount": self.amount,
            "weeks_idle": self.weeks_idle,
            "week": self.week,
            "prevented_amount": self.prevented_amount,
        }


@dataclass  
class DecayWarning:
    """Warning about upcoming stat decay."""
    fighter_id: str
    fighter_name: str
    stat: str
    weeks_idle: int
    weeks_until_decay: int
    
    @property
    def warning_message(self) -> str:
        """Generate warning message."""
        return f"âš ï¸ {self.fighter_name}'s {self.stat} at risk - {self.weeks_until_decay} weeks until decay"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "fighter_name": self.fighter_name,
            "stat": self.stat,
            "weeks_idle": self.weeks_idle,
            "weeks_until_decay": self.weeks_until_decay,
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_decay_tier(weeks_idle: int) -> Optional[str]:
    """Determine decay tier based on weeks idle."""
    if weeks_idle >= DECAY_THRESHOLD_SEVERE:
        return "severe"
    elif weeks_idle >= DECAY_THRESHOLD_SIGNIFICANT:
        return "significant"
    elif weeks_idle >= DECAY_THRESHOLD_HIGH:
        return "high"
    elif weeks_idle >= DECAY_THRESHOLD_MODERATE:
        return "moderate"
    elif weeks_idle >= DECAY_THRESHOLD_START:
        return "start"
    return None


def get_decay_multiplier(stat: str) -> float:
    """Get decay rate multiplier for a stat category.

    Athletic base persists (physiology); technical skills rust fast.
    Flipped from original: physical was 1.5x (decayed fastest), now 0.3x.
    Mental was 0.5x — fight_iq/composure are now under TECHNICAL at 1.2x
    because ring IQ rusts without live training, while heart stays under
    ATHLETIC at 0.3x as a stand-in for grit/conditioning capacity.
    """
    if stat in {"strength", "speed", "cardio", "chin", "recovery", "heart"}:
        return 0.3
    elif stat in {"boxing", "kicks", "clinch_striking", "clinch_control",
                  "striking_defense",
                  "takedowns", "takedown_defense", "top_control",
                  "submissions", "guard", "fight_iq", "composure"}:
        return 1.2
    return 0.8  # defensive default for any unmapped stat


def get_coach_skill_for_stat(coach: Dict[str, Any], stat: str) -> int:
    """
    Get the relevant coach skill level for a given stat.
    
    Supports both new skill-based coaches and legacy quality-based.
    """
    # Determine which skill category this stat belongs to
    skill_name = get_skill_for_attribute(stat)
    
    if skill_name:
        # New skill-based coach
        if skill_name in coach:
            return coach.get(skill_name, 50)
        
        # Try skill name variations
        skill_variations = {
            "jiu_jitsu": ["jiu_jitsu", "bjj_skill", "grappling"],
            "striking": ["striking", "boxing_skill"],
            "wrestling": ["wrestling", "wrestling_skill"],
            "conditioning": ["conditioning", "cardio_skill"],
            "strength": ["strength", "strength_skill", "power_skill"],
        }
        
        for variation in skill_variations.get(skill_name, []):
            if variation in coach:
                return coach.get(variation, 50)
    
    # Legacy fallback: convert quality to skill
    quality = coach.get("quality", 3)
    return QUALITY_TO_SKILL.get(quality, 65)


def get_camp_skill_for_stat(
    coaches: List[Dict[str, Any]], 
    stat: str,
    is_head_coach_idx: int = 0
) -> int:
    """
    Calculate effective camp skill for a stat.
    
    Head coach contributes 100%, assistants contribute 50%.
    """
    if not coaches:
        return 40
    
    # Find head coach
    head_coach = None
    assistants = []
    
    for i, coach in enumerate(coaches):
        if coach.get("is_head_coach", False) or i == is_head_coach_idx:
            head_coach = coach
        else:
            assistants.append(coach)
    
    if not head_coach and coaches:
        head_coach = coaches[0]
        assistants = coaches[1:]
    
    # Head coach skill
    base_skill = get_coach_skill_for_stat(head_coach, stat) if head_coach else 50
    
    # Assistants add 50% of skill above 50
    assistant_bonus = 0
    for assistant in assistants:
        ass_skill = get_coach_skill_for_stat(assistant, stat)
        if ass_skill > 50:
            assistant_bonus += (ass_skill - 50) * 0.5
    
    return min(99, int(base_skill + assistant_bonus))


def select_boost_stat(
    coaches: List[Dict[str, Any]],
    fighter_attributes: Dict[str, int],
    stat_activity: StatActivity,
    current_week: int
) -> Tuple[str, int, bool]:
    """
    Select which stat the coach will boost.
    
    Prioritizes:
    1. Stats where coaches have high skill
    2. Stats that have been idle longer
    3. Stats below 80 (more room to grow)
    
    Returns:
        Tuple of (stat_name, coach_skill_level, is_high_skill)
    """
    # Build weighted candidate list
    candidates = []
    
    for stat in ALL_STATS:
        current_value = fighter_attributes.get(stat, 50)
        
        # Skip maxed out stats
        if current_value >= MAX_STAT_VALUE:
            continue
        
        # Get camp skill for this stat
        camp_skill = get_camp_skill_for_stat(coaches, stat)
        
        # Base weight from coach skill
        weight = camp_skill // 5  # 0-20 base weight
        
        # High skill = higher weight
        if camp_skill >= 80:
            weight += 25
        elif camp_skill >= 70:
            weight += 15
        elif camp_skill >= 60:
            weight += 5
        
        # Idle stats = higher weight
        weeks_idle = stat_activity.weeks_since_activity(stat, current_week)
        if weeks_idle >= 12:
            weight += 20
        elif weeks_idle >= 8:
            weight += 10
        
        # Lower stats = higher weight (more room to grow)
        if current_value < 60:
            weight += 15
        elif current_value < 70:
            weight += 10
        elif current_value < 80:
            weight += 5
        
        is_high_skill = camp_skill >= 70
        candidates.append((stat, camp_skill, weight, is_high_skill))
    
    if not candidates:
        # Fallback to random stat
        stat = random.choice(list(ALL_STATS))
        return stat, 50, False
    
    # Weighted random selection
    total_weight = sum(c[2] for c in candidates)
    if total_weight <= 0:
        selected = random.choice(candidates)
        return selected[0], selected[1], selected[3]
    
    roll = random.uniform(0, total_weight)
    
    cumulative = 0
    for stat, skill, weight, is_high in candidates:
        cumulative += weight
        if roll <= cumulative:
            return stat, skill, is_high
    
    # Fallback
    return candidates[0][0], candidates[0][1], candidates[0][3]


def calculate_boost_amount(
    coach_skill: int,
    is_high_skill: bool,
    fighter_age: int,
    current_stat_value: int
) -> int:
    """Calculate how much a stat boost should be."""
    min_boost, max_boost = get_boost_amount(coach_skill)
    
    # Base amount
    amount = random.randint(min_boost, max_boost)
    
    # High skill bonus
    if is_high_skill and random.random() < 0.3:
        amount += 1
    
    # Age modifier (young fighters learn faster)
    if fighter_age < 25:
        if random.random() < 0.3:  # 30% chance of +1
            amount += 1
    elif fighter_age > 34:
        if random.random() < 0.3:  # 30% chance of -1
            amount = max(1, amount - 1)
    
    # Diminishing returns at high stat values
    if current_stat_value >= 90:
        amount = 1
    elif current_stat_value >= 85:
        amount = max(1, amount - 1)
    
    # Cap at max
    final_value = current_stat_value + amount
    if final_value > MAX_STAT_VALUE:
        amount = MAX_STAT_VALUE - current_stat_value
    
    return max(0, amount)


def check_stat_decay(
    stat: str,
    current_value: int,
    weeks_idle: int,
    decay_prevention: float = 0.0
) -> Tuple[bool, int, int]:
    """
    Check if a stat should decay and by how much.
    
    Decay rules:
    - 6+ weeks idle: 1-3 decay (weighted toward 1)
    - 18+ weeks idle: 5-8 significant decay
    - 24+ weeks idle: 6-10 severe decay
    
    Args:
        stat: The stat name
        current_value: Current stat value
        weeks_idle: Weeks since last activity
        decay_prevention: Percentage of decay to prevent (0.0-1.0)
    
    Returns:
        Tuple of (should_decay, decay_amount, prevented_amount)
    """
    tier = get_decay_tier(weeks_idle)
    
    if tier is None:
        return False, 0, 0
    
    # Don't decay below minimum
    if current_value <= MIN_STAT_VALUE:
        return False, 0, 0
    
    # Get decay chance with category multiplier
    base_chance = DECAY_CHANCE[tier]
    multiplier = get_decay_multiplier(stat)
    
    # Apply decay prevention from coaching
    prevention_mult = 1.0 - decay_prevention
    final_chance = base_chance * multiplier * prevention_mult
    
    # Roll for decay
    if random.random() >= final_chance:
        return False, 0, 0
    
    # Calculate decay amount with weighting
    min_decay, max_decay = DECAY_AMOUNT[tier]
    
    # Use weighted selection - favor lower amounts for early tiers
    weight_low = DECAY_WEIGHT_LOW.get(tier, 0.5)
    if random.random() < weight_low:
        # Favor minimum amount
        raw_amount = min_decay
    else:
        # Random from range
        raw_amount = random.randint(min_decay, max_decay)
    
    # Apply category multiplier to amount (rounded)
    raw_amount = max(1, int(raw_amount * multiplier))
    
    # Calculate how much coaching prevents
    prevented = int(raw_amount * decay_prevention)
    actual_amount = raw_amount - prevented
    
    # Don't decay below minimum
    if current_value - actual_amount < MIN_STAT_VALUE:
        actual_amount = current_value - MIN_STAT_VALUE
    
    if actual_amount <= 0:
        return False, 0, prevented
    
    return True, actual_amount, prevented


# ============================================================================
# MAINTENANCE TRAINING SYSTEM
# ============================================================================

class MaintenanceTrainingSystem:
    """
    Manages coach maintenance training and stat decay.
    
    Now uses skill-based coaching for boosts and decay prevention.
    """
    
    def __init__(self):
        # Track stat activity per fighter
        self._fighter_activity: Dict[str, StatActivity] = {}
        
        # History of boosts and decays
        self._boost_history: List[MaintenanceBoost] = []
        self._decay_history: List[StatDecay] = []
    
    def get_fighter_activity(self, fighter_id: str) -> StatActivity:
        """Get or create stat activity tracker for a fighter."""
        if fighter_id not in self._fighter_activity:
            self._fighter_activity[fighter_id] = StatActivity()
        return self._fighter_activity[fighter_id]
    
    def initialize_fighter(self, fighter_id: str, current_week: int) -> None:
        """Initialize a new fighter's activity tracking."""
        activity = self.get_fighter_activity(fighter_id)
        for stat in ALL_STATS:
            if stat not in activity.last_activity_week:
                activity.last_activity_week[stat] = current_week
    
    def record_training_camp_activity(
        self,
        fighter_id: str,
        trained_stats: List[str],
        current_week: int
    ) -> None:
        """Record that stats were trained in a fight camp."""
        activity = self.get_fighter_activity(fighter_id)
        activity.record_multiple(trained_stats, current_week)
    
    def process_week(
        self,
        fighters: List[Dict[str, Any]],
        coaches: List[Dict[str, Any]],
        camp_assignments: Dict[str, str],
        camp_coaches: Dict[str, List[Dict[str, Any]]],
        current_week: int,
        fighters_in_camp: Set[str] = None
    ) -> Tuple[List[MaintenanceBoost], List[StatDecay], List[DecayWarning]]:
        """
        Process weekly maintenance for all fighters.
        
        Args:
            fighters: List of fighter dicts with 'id', 'name', 'attributes', 'age'
            coaches: List of all coaches (for reference)
            camp_assignments: Mapping of fighter_id to camp_id
            camp_coaches: Mapping of camp_id to list of coach dicts
            current_week: Current game week
            fighters_in_camp: Set of fighter IDs currently in training camp
            
        Returns:
            Tuple of (boosts, decays, warnings)
        """
        boosts = []
        decays = []
        warnings = []
        
        fighters_in_camp = fighters_in_camp or set()
        
        for fighter in fighters:
            fighter_id = fighter.get("id") or fighter.get("fighter_id")
            fighter_name = fighter.get("name", "Unknown")
            attributes = fighter.get("attributes", {})
            fighter_age = fighter.get("age", 25)
            
            if not fighter_id:
                continue
            
            # Get or create activity tracker
            activity = self.get_fighter_activity(fighter_id)
            
            # Initialize if new
            if not activity.last_activity_week:
                self.initialize_fighter(fighter_id, current_week)
            
            # Skip fighters currently in training camp
            if fighter_id in fighters_in_camp:
                continue
            
            # Get camp and coaches for this fighter
            camp_id = camp_assignments.get(fighter_id)
            fighter_coaches = camp_coaches.get(camp_id, []) if camp_id else []
            
            # Process coach maintenance boosts
            if fighter_coaches:
                # Select a stat to potentially boost
                stat, coach_skill, is_high_skill = select_boost_stat(
                    fighter_coaches, attributes, activity, current_week
                )
                
                # Check if boost happens (based on coach skill)
                boost_chance = get_boost_chance(coach_skill)
                
                # Apply trait modifiers
                for coach in fighter_coaches:
                    coach_traits = coach.get("traits", [])
                    if isinstance(coach_traits, list):
                        trait_names = [t if isinstance(t, str) else getattr(t, 'value', str(t)) for t in coach_traits]
                    else:
                        trait_names = []
                    
                    if "Motivator" in trait_names:
                        boost_chance *= 1.2
                    if "Diamond Polisher" in trait_names and fighter_age < 25:
                        boost_chance *= 1.3
                    if "Veteran's Touch" in trait_names and fighter_age > 32:
                        boost_chance *= 1.25
                    if "Burned Out" in trait_names:
                        boost_chance *= 0.5
                
                if random.random() < boost_chance:
                    current_value = attributes.get(stat, 50)
                    
                    amount = calculate_boost_amount(
                        coach_skill, is_high_skill, fighter_age, current_value
                    )
                    
                    if amount > 0:
                        # Find the coach who gave the boost (highest skill in this area)
                        best_coach = max(fighter_coaches, 
                                        key=lambda c: get_coach_skill_for_stat(c, stat))
                        
                        boost = MaintenanceBoost(
                            fighter_id=fighter_id,
                            fighter_name=fighter_name,
                            coach_id=best_coach.get("id") or best_coach.get("coach_id", ""),
                            coach_name=best_coach.get("name", "Coach"),
                            stat=stat,
                            amount=amount,
                            week=current_week,
                            specialty_match=is_high_skill,
                            coach_skill=coach_skill
                        )
                        boosts.append(boost)
                        self._boost_history.append(boost)
                        
                        # Record activity
                        activity.record_activity(stat, current_week)
            
            # Process stat decay
            boosted_stats = {b.stat for b in boosts if b.fighter_id == fighter_id}
            
            for stat in ALL_STATS:
                if stat in boosted_stats:
                    continue
                
                current_value = attributes.get(stat, 50)
                weeks_idle = activity.weeks_since_activity(stat, current_week)
                
                # Calculate decay prevention from coaches
                if fighter_coaches:
                    camp_skill = get_camp_skill_for_stat(fighter_coaches, stat)
                    decay_prevention = get_decay_prevention(camp_skill)
                else:
                    decay_prevention = 0.0
                
                # Check for decay
                should_decay, decay_amount, prevented = check_stat_decay(
                    stat, current_value, weeks_idle, decay_prevention
                )
                
                if should_decay and decay_amount > 0:
                    decay = StatDecay(
                        fighter_id=fighter_id,
                        fighter_name=fighter_name,
                        stat=stat,
                        amount=decay_amount,
                        weeks_idle=weeks_idle,
                        week=current_week,
                        prevented_amount=prevented
                    )
                    decays.append(decay)
                    self._decay_history.append(decay)
                
                # Generate warnings for approaching decay
                elif weeks_idle >= DECAY_THRESHOLD_START - 4:
                    weeks_until = DECAY_THRESHOLD_START - weeks_idle
                    if weeks_until > 0:
                        warning = DecayWarning(
                            fighter_id=fighter_id,
                            fighter_name=fighter_name,
                            stat=stat,
                            weeks_idle=weeks_idle,
                            weeks_until_decay=weeks_until
                        )
                        warnings.append(warning)
        
        return boosts, decays, warnings
    
    def get_fighter_decay_risk(
        self,
        fighter_id: str,
        current_week: int
    ) -> Dict[str, Dict[str, Any]]:
        """Get decay risk assessment for all stats of a fighter."""
        activity = self.get_fighter_activity(fighter_id)
        risks = {}
        
        for stat in ALL_STATS:
            weeks_idle = activity.weeks_since_activity(stat, current_week)
            tier = get_decay_tier(weeks_idle)
            
            if tier:
                risk_level = {
                    "start": "Low",
                    "moderate": "Medium",
                    "high": "High",
                    "severe": "Critical"
                }[tier]
            elif weeks_idle >= DECAY_THRESHOLD_START - 4:
                risk_level = "Warning"
            else:
                risk_level = "Safe"
            
            risks[stat] = {
                "weeks_idle": weeks_idle,
                "risk_level": risk_level,
                "decay_tier": tier,
            }
        
        return risks
    
    def get_camp_coverage_report(
        self,
        camp_coaches: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate a report of camp coaching coverage.
        
        Shows skill level, training mult, and decay prevention for each area.
        """
        report = {}
        
        skill_areas = ["striking", "wrestling", "jiu_jitsu", "conditioning", "strength"]
        
        for skill in skill_areas:
            # Get a representative stat for this skill
            representative_stats = SKILL_ATTRIBUTES.get(skill, [])
            stat = representative_stats[0] if representative_stats else skill
            
            camp_skill = get_camp_skill_for_stat(camp_coaches, stat)
            train_mult = get_training_multiplier(camp_skill)
            decay_prev = get_decay_prevention(camp_skill)
            boost_chance = get_boost_chance(camp_skill)
            
            report[skill] = {
                "skill_level": camp_skill,
                "training_multiplier": train_mult,
                "decay_prevention": decay_prev,
                "boost_chance_per_week": boost_chance,
                "rating": self._get_skill_rating(camp_skill),
            }
        
        return report
    
    def _get_skill_rating(self, skill: int) -> str:
        """Get letter rating for skill level."""
        if skill >= 90:
            return "Elite"
        elif skill >= 80:
            return "Excellent"
        elif skill >= 70:
            return "Good"
        elif skill >= 60:
            return "Average"
        elif skill >= 50:
            return "Below Avg"
        else:
            return "Poor"
    
    def get_recent_boosts(self, fighter_id: str, count: int = 10) -> List[MaintenanceBoost]:
        """Get recent boosts for a fighter."""
        fighter_boosts = [b for b in self._boost_history if b.fighter_id == fighter_id]
        return sorted(fighter_boosts, key=lambda b: b.week, reverse=True)[:count]
    
    def get_recent_decays(self, fighter_id: str, count: int = 10) -> List[StatDecay]:
        """Get recent decays for a fighter."""
        fighter_decays = [d for d in self._decay_history if d.fighter_id == fighter_id]
        return sorted(fighter_decays, key=lambda d: d.week, reverse=True)[:count]
    
    def get_boost_stats(self) -> Dict[str, Any]:
        """Get statistics about boosts."""
        total = len(self._boost_history)
        if total == 0:
            return {"total": 0}
        
        specialty_matches = sum(1 for b in self._boost_history if b.specialty_match)
        avg_amount = sum(b.amount for b in self._boost_history) / total
        
        by_stat = {}
        for boost in self._boost_history:
            by_stat[boost.stat] = by_stat.get(boost.stat, 0) + 1
        
        return {
            "total": total,
            "specialty_match_rate": specialty_matches / total if total else 0,
            "average_amount": avg_amount,
            "by_stat": by_stat,
        }
    
    def get_decay_stats(self) -> Dict[str, Any]:
        """Get statistics about decays."""
        total = len(self._decay_history)
        if total == 0:
            return {"total": 0}
        
        avg_amount = sum(d.amount for d in self._decay_history) / total
        avg_prevented = sum(d.prevented_amount for d in self._decay_history) / total
        
        by_stat = {}
        for decay in self._decay_history:
            by_stat[decay.stat] = by_stat.get(decay.stat, 0) + 1
        
        return {
            "total": total,
            "average_amount": avg_amount,
            "average_prevented": avg_prevented,
            "by_stat": by_stat,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "fighter_activity": {
                fid: act.to_dict() 
                for fid, act in self._fighter_activity.items()
            },
            "boost_history": [b.to_dict() for b in self._boost_history[-500:]],
            "decay_history": [d.to_dict() for d in self._decay_history[-500:]],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaintenanceTrainingSystem':
        """Deserialize from dictionary."""
        system = cls()
        
        for fid, act_data in data.get("fighter_activity", {}).items():
            system._fighter_activity[fid] = StatActivity.from_dict(act_data)
        
        for b_data in data.get("boost_history", []):
            boost = MaintenanceBoost(
                fighter_id=b_data["fighter_id"],
                fighter_name=b_data["fighter_name"],
                coach_id=b_data["coach_id"],
                coach_name=b_data["coach_name"],
                stat=b_data["stat"],
                amount=b_data["amount"],
                week=b_data["week"],
                specialty_match=b_data.get("specialty_match", False),
                coach_skill=b_data.get("coach_skill", 50),
            )
            system._boost_history.append(boost)
        
        for d_data in data.get("decay_history", []):
            decay = StatDecay(
                fighter_id=d_data["fighter_id"],
                fighter_name=d_data["fighter_name"],
                stat=d_data["stat"],
                amount=d_data["amount"],
                weeks_idle=d_data["weeks_idle"],
                week=d_data["week"],
                prevented_amount=d_data.get("prevented_amount", 0),
            )
            system._decay_history.append(decay)
        
        return system


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def process_weekly_maintenance(
    system: MaintenanceTrainingSystem,
    fighters: List[Dict[str, Any]],
    camp_assignments: Dict[str, str],
    camp_coaches: Dict[str, List[Dict[str, Any]]],
    current_week: int,
    fighters_in_camp: Set[str] = None
) -> Tuple[List[MaintenanceBoost], List[StatDecay], List[DecayWarning]]:
    """
    Convenience function to process weekly maintenance.
    
    Args:
        system: The MaintenanceTrainingSystem
        fighters: List of fighter dicts
        camp_assignments: fighter_id -> camp_id mapping
        camp_coaches: camp_id -> list of coach dicts
        current_week: Current week number
        fighters_in_camp: Set of fighter IDs in training camp
        
    Returns:
        Tuple of (boosts, decays, warnings)
    """
    return system.process_week(
        fighters=fighters,
        coaches=[],  # Not used directly anymore
        camp_assignments=camp_assignments,
        camp_coaches=camp_coaches,
        current_week=current_week,
        fighters_in_camp=fighters_in_camp
    )


def format_coverage_report(report: Dict[str, Dict[str, Any]]) -> List[str]:
    """Format camp coverage report for display."""
    lines = []
    lines.append("COACHING COVERAGE")
    lines.append("-" * 50)
    
    for skill, data in report.items():
        skill_display = skill.replace("_", " ").title()
        rating = data["rating"]
        level = data["skill_level"]
        train = data["training_multiplier"]
        decay = data["decay_prevention"]
        
        lines.append(f"  {skill_display:15} {level:3} [{rating:10}]")
        lines.append(f"    Training: {train:.2f}x | Decay Prev: {decay*100:.0f}%")
    
    return lines

# Backward compatibility constants
COACH_BOOST_BASE_CHANCE = 0.3  # Base 30% chance
COACH_BOOST_AMOUNT = 1  # Base boost amount

# Backward compatibility functions
def check_coach_specialty_match(coach_specialty: str, stat: str) -> bool:
    """Check if coach specialty matches the stat category."""
    specialty_stats = {
        "striking": {"boxing", "kicks", "clinch_striking",
                      "clinch_control", "defense"},
        "wrestling": {"takedowns", "takedown_defense", "top_control"},
        "bjj": {"submissions", "guard", "recovery"},
        "conditioning": {"cardio", "strength", "speed", "chin"},
    }
    return stat in specialty_stats.get(coach_specialty.lower(), set())

def format_maintenance_summary(boosts: list, decays: list, warnings: list) -> str:
    """Format a summary of maintenance results."""
    lines = []
    if boosts:
        lines.append(f"Boosts: {len(boosts)}")
    if decays:
        lines.append(f"Decays: {len(decays)}")
    if warnings:
        lines.append(f"Warnings: {len(warnings)}")
    return ", ".join(lines) if lines else "No changes"

def get_stat_category(stat: str) -> str:
    """Get the category of a stat."""
    if stat in PHYSICAL_STATS:
        return "physical"
    if stat in MENTAL_STATS:
        return "mental"
    if stat in STRIKING_STATS:
        return "striking"
    if stat in GRAPPLING_STATS:
        return "grappling"
    return "other"
