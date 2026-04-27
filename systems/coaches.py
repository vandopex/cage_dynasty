# systems/coaches.py
# Module: Coach System v2
# Lines: ~1400
#
# Skill-based coaching system with:
# - Five skill ratings (0-100): striking, wrestling, jiu_jitsu, conditioning, strength
# - Training multipliers, decay prevention, camp building, scout accuracy
# - Regional nationality bonuses
# - Archetype-based generation (Specialist, Dual Focus, Generalist, Legend)
# - Traits and chemistry system
# - Coach progression and experience

"""
Cage Dynasty - Coach System v2

Coaches now have skill ratings in each area rather than a single specialty.
This enables nuanced training, decay prevention, and scouting accuracy.

Usage:
    from systems.coaches import (
        CoachSystem,
        Coach,
        generate_coach,
        get_training_multiplier,
        get_decay_prevention,
        get_scout_variance,
    )
    
    # Create system
    system = CoachSystem()
    
    # Generate starting pool
    system.generate_initial_pool()
    
    # Get camp's training bonus for striking
    multiplier = system.get_camp_training_multiplier(camp_id, "striking")
    
    # Get decay prevention for wrestling
    prevention = system.get_camp_decay_prevention(camp_id, "wrestling")
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class CoachArchetype(Enum):
    """Generation archetypes for coaches"""
    SPECIALIST = "Specialist"      # One skill 75-95, others 30-55
    DUAL_FOCUS = "Dual Focus"      # Two skills 65-85, others 35-55
    GENERALIST = "Generalist"      # All skills 45-65
    LEGEND = "Legend"              # One skill 88-98, two at 60-80, rest 40-55


class CoachSpecialty(Enum):
    """Coach specialization areas - for display and matching with training focuses."""
    STRIKING = "Striking"
    WRESTLING = "Wrestling"
    JIU_JITSU = "Jiu-Jitsu"
    CONDITIONING = "Conditioning"
    STRENGTH = "Strength"
    CORNERING = "Cornering"


class CoachTrait(Enum):
    """Coach traits that affect training and chemistry"""
    # Positive training traits
    MOTIVATOR = "Motivator"
    TECHNICAL_GENIUS = "Technical Genius"
    DIAMOND_POLISHER = "Diamond Polisher"
    VETERANS_TOUCH = "Veteran's Touch"
    IRON_SHARPENER = "Iron Sharpener"
    CALM_CORNER = "Calm Corner"
    EYE_FOR_TALENT = "Eye for Talent"
    TASKMASTER = "Taskmaster"
    
    # Personality traits
    DISCIPLINARIAN = "Disciplinarian"
    PLAYERS_COACH = "Player's Coach"
    INTENSE = "Intense"
    ANALYTICAL = "Analytical"
    OLD_SCHOOL = "Old School"
    MODERN_METHODS = "Modern Methods"
    
    # Negative traits
    BURNED_OUT = "Burned Out"
    PRIMA_DONNA = "Prima Donna"
    CLASHING_EGO = "Clashing Ego"
    OUTDATED = "Outdated Methods"
    INJURY_RISK = "Injury Risk"
    FAIR_WEATHER = "Fair Weather"
    
    # Special traits
    LOYAL = "Loyal"
    AMBITIOUS = "Ambitious"


class SalaryPersonality(Enum):
    """Determines salary expectations"""
    HUMBLE = "Humble"          # 0.7x - "Just happy to coach"
    MODEST = "Modest"          # 0.85x - "Fair expectations"
    STANDARD = "Standard"      # 1.0x - "Market rate"
    AMBITIOUS = "Ambitious"    # 1.15x - "Knows their worth"
    GREEDY = "Greedy"          # 1.4x - "Pay me or I walk"


# ============================================================================
# CONSTANTS
# ============================================================================

# Skill areas and the fighter attributes they affect (17-attribute system)
SKILL_ATTRIBUTES = {
    "striking": ["boxing", "kicks", "clinch_striking", "striking_defense"],
    "wrestling": ["takedowns", "takedown_defense", "top_control"],
    "jiu_jitsu": ["submissions", "guard"],
    "conditioning": ["cardio", "chin", "recovery"],
    "strength": ["strength", "speed"],
}

# All skill names
SKILL_NAMES = ["striking", "wrestling", "jiu_jitsu", "conditioning", "strength"]

# Training multipliers by skill level
TRAINING_MULTIPLIER_TIERS = [
    (90, 1.30),   # 90+ = 1.3x
    (80, 1.20),   # 80-89 = 1.2x
    (70, 1.10),   # 70-79 = 1.1x
    (60, 1.00),   # 60-69 = 1.0x (baseline)
    (50, 0.90),   # 50-59 = 0.9x
    (0, 0.80),    # <50 = 0.8x
]

# Decay prevention by skill level (percentage of decay prevented)
DECAY_PREVENTION_TIERS = [
    (90, 0.90),   # 90+ = 90% prevented
    (80, 0.80),   # 80-89 = 80% prevented
    (70, 0.65),   # 70-79 = 65% prevented
    (60, 0.50),   # 60-69 = 50% prevented
    (50, 0.35),   # 50-59 = 35% prevented
    (0, 0.20),    # <50 = 20% prevented
]

# Scout variance by skill level (Â± this amount)
SCOUT_VARIANCE_TIERS = [
    (90, 1),      # 90+ = Â±1
    (80, 2),      # 80-89 = Â±2
    (70, 3),      # 70-79 = Â±3
    (60, 5),      # 60-69 = Â±5
    (50, 7),      # 50-59 = Â±7
    (0, 10),      # <50 = Â±10
]

# Camp building chance by skill level (chance per month to gain +1 in an attribute)
CAMP_BUILDING_TIERS = [
    (90, 0.40),   # 90+ = 40% chance of +1-2
    (80, 0.30),   # 80-89 = 30% chance of +1
    (70, 0.15),   # 70-79 = 15% chance of +1
    (60, 0.05),   # 60-69 = 5% chance of +1
    (0, 0.00),    # <60 = no passive growth
]

# Regional bonuses by nationality
REGIONAL_BONUSES = {
    "Brazil": {"jiu_jitsu": 15, "striking": 5},
    "Russia": {"wrestling": 15, "conditioning": 5},
    "Dagestan": {"wrestling": 18, "conditioning": 8},
    "USA": {"wrestling": 10, "strength": 5},
    "Thailand": {"striking": 18},
    "Netherlands": {"striking": 15},
    "Japan": {"jiu_jitsu": 10, "striking": 8},
    "Cuba": {"wrestling": 12, "strength": 8},
    "Iran": {"wrestling": 15},
    "Mexico": {"striking": 10, "conditioning": 5},
    "UK": {"striking": 8, "wrestling": 5},
    "Sweden": {"wrestling": 8, "striking": 5},
    "Poland": {"striking": 10},
    "South Korea": {"striking": 8, "jiu_jitsu": 5},
    "Georgia": {"wrestling": 12},
    "Kazakhstan": {"wrestling": 10},
    "France": {"jiu_jitsu": 8, "striking": 5},
    "Australia": {"striking": 8, "wrestling": 5},
}

# Distribution of coach nationalities
NATIONALITY_WEIGHTS = {
    "USA": 25,
    "Brazil": 15,
    "Russia": 10,
    "Thailand": 8,
    "Netherlands": 5,
    "Japan": 5,
    "UK": 5,
    "Mexico": 5,
    "Dagestan": 4,
    "Cuba": 3,
    "Sweden": 3,
    "Poland": 3,
    "Iran": 2,
    "South Korea": 2,
    "Georgia": 2,
    "France": 2,
    "Australia": 1,
}

# Archetype distribution
ARCHETYPE_WEIGHTS = {
    CoachArchetype.SPECIALIST: 50,
    CoachArchetype.DUAL_FOCUS: 30,
    CoachArchetype.GENERALIST: 15,
    CoachArchetype.LEGEND: 5,
}

# Base monthly salary by overall rating
# Balanced for early-game - starter coaches are affordable
def get_base_monthly_salary(overall: int) -> int:
    """Get base monthly salary from overall rating"""
    if overall >= 85:
        return 12000    # Was 25,000 - elite coach
    elif overall >= 75:
        return 6000     # Was 15,000 - great coach
    elif overall >= 65:
        return 3500     # Was 8,000 - good coach
    elif overall >= 55:
        return 1800     # Was 4,000 - decent starter coach
    else:
        return 1000     # Was 2,000 - scrub coach

# Salary personality multipliers
SALARY_PERSONALITY_MULT = {
    SalaryPersonality.HUMBLE: 0.7,
    SalaryPersonality.MODEST: 0.85,
    SalaryPersonality.STANDARD: 1.0,
    SalaryPersonality.AMBITIOUS: 1.15,
    SalaryPersonality.GREEDY: 1.4,
}

# Salary personality distribution
SALARY_PERSONALITY_WEIGHTS = {
    SalaryPersonality.HUMBLE: 15,
    SalaryPersonality.MODEST: 25,
    SalaryPersonality.STANDARD: 30,
    SalaryPersonality.AMBITIOUS: 20,
    SalaryPersonality.GREEDY: 10,
}

# Max coaches by camp tier
MAX_COACHES_BY_TIER = {
    "GARAGE": 1,
    "LOCAL": 2,
    "REGIONAL": 3,
    "NATIONAL": 4,
    "ELITE": 5,
}

# XP required to improve skills
XP_PER_SKILL_POINT = 50

# Trait effects on training
TRAIT_TRAINING_EFFECTS: Dict[CoachTrait, Dict[str, float]] = {
    CoachTrait.MOTIVATOR: {"low_morale_bonus": 0.15},
    CoachTrait.TECHNICAL_GENIUS: {"technical_bonus": 0.15},
    CoachTrait.DIAMOND_POLISHER: {"prospect_bonus": 0.25},
    CoachTrait.VETERANS_TOUCH: {"veteran_bonus": 0.20},
    CoachTrait.IRON_SHARPENER: {"camp_sparring_bonus": 0.10},
    CoachTrait.CALM_CORNER: {"composure_bonus": 0.10, "recovery_bonus": 0.10},
    CoachTrait.TASKMASTER: {"training_bonus": 0.15, "morale_penalty": -5},
    CoachTrait.DISCIPLINARIAN: {"discipline_bonus": 0.10},
    CoachTrait.PLAYERS_COACH: {"morale_bonus": 5, "training_penalty": -0.05},
    CoachTrait.INTENSE: {"intensity_bonus": 0.10},
    CoachTrait.ANALYTICAL: {"gameplan_bonus": 0.15, "training_penalty": -0.05},
    CoachTrait.OLD_SCHOOL: {"conditioning_bonus": 0.20, "modern_penalty": -0.10},
    CoachTrait.MODERN_METHODS: {"young_fighter_bonus": 0.15},
    CoachTrait.BURNED_OUT: {"training_penalty": -0.15},
    CoachTrait.OUTDATED: {"young_fighter_penalty": -0.15},
    CoachTrait.INJURY_RISK: {"injury_chance_increase": 0.20},
    CoachTrait.FAIR_WEATHER: {"losing_penalty": -0.20},
}

# Trait salary modifiers
TRAIT_SALARY_MODS: Dict[CoachTrait, float] = {
    CoachTrait.PRIMA_DONNA: 0.5,
    CoachTrait.DIAMOND_POLISHER: 0.2,
    CoachTrait.TECHNICAL_GENIUS: 0.15,
    CoachTrait.VETERANS_TOUCH: 0.15,
    CoachTrait.EYE_FOR_TALENT: 0.1,
    CoachTrait.BURNED_OUT: -0.3,
    CoachTrait.OUTDATED: -0.2,
    CoachTrait.FAIR_WEATHER: -0.15,
}

# Chemistry synergies: (coach_trait, fighter_trait) -> bonus
TRAIT_SYNERGY: Dict[Tuple[str, str], int] = {
    # Positive synergies
    ("Disciplinarian", "Gym Rat"): 15,
    ("Motivator", "Slow Starter"): 10,
    ("Diamond Polisher", "Fast Learner"): 15,
    ("Veteran's Touch", "Veteran Savvy"): 15,
    ("Intense", "Cardio Machine"): 10,
    ("Technical Genius", "Submission Ace"): 10,
    ("Player's Coach", "Pressure Fighter"): 10,
    ("Calm Corner", "Choke Artist"): 15,
    ("Modern Methods", "Fast Starter"): 10,
    ("Analytical", "Counter Striker"): 10,
    
    # Negative synergies
    ("Disciplinarian", "Lazy"): -20,
    ("Intense", "Injury Prone"): -15,
    ("Taskmaster", "Glass Cannon"): -10,
    ("Old School", "Fast Starter"): -10,
    ("Outdated Methods", "Fast Learner"): -15,
}

# Trait pools by category
POSITIVE_TRAITS = [
    CoachTrait.MOTIVATOR,
    CoachTrait.TECHNICAL_GENIUS,
    CoachTrait.DIAMOND_POLISHER,
    CoachTrait.VETERANS_TOUCH,
    CoachTrait.IRON_SHARPENER,
    CoachTrait.CALM_CORNER,
    CoachTrait.EYE_FOR_TALENT,
    CoachTrait.TASKMASTER,
    CoachTrait.MODERN_METHODS,
]

PERSONALITY_TRAITS = [
    CoachTrait.DISCIPLINARIAN,
    CoachTrait.PLAYERS_COACH,
    CoachTrait.INTENSE,
    CoachTrait.ANALYTICAL,
    CoachTrait.OLD_SCHOOL,
]

NEGATIVE_TRAITS = [
    CoachTrait.BURNED_OUT,
    CoachTrait.PRIMA_DONNA,
    CoachTrait.CLASHING_EGO,
    CoachTrait.OUTDATED,
    CoachTrait.INJURY_RISK,
    CoachTrait.FAIR_WEATHER,
]

SPECIAL_TRAITS = [
    CoachTrait.LOYAL,
    CoachTrait.AMBITIOUS,
]


# ============================================================================
# NAME GENERATION
# ============================================================================

COACH_FIRST_NAMES_BY_NATIONALITY = {
    "USA": ["Marcus", "Mike", "Greg", "Duke", "Ray", "Trevor", "Jason", "Matt", 
            "Chris", "James", "John", "Keith", "Derrick", "Terrance", "Sarah", 
            "Angela", "Rose", "Diana", "Michelle"],
    "Brazil": ["Roberto", "Rafael", "Jorge", "Carlos", "Antonio", "Pedro", 
               "Javier", "Ricardo", "Andre", "Luis", "Maria", "Ana"],
    "Russia": ["Sergei", "Ivan", "Alexei", "Dmitri", "Viktor", "Andrei", 
               "Mikhail", "Nikolai", "Oleg"],
    "Dagestan": ["Khabib", "Islam", "Zabit", "Magomed", "Abdulmanap", "Shamil", 
                 "Rustam", "Makhach"],
    "Thailand": ["Saenchai", "Buakaw", "Yodsanklai", "Somrak", "Petchboonchu",
                 "Dieselnoi", "Namsaknoi"],
    "Netherlands": ["Cor", "Ramon", "Ernesto", "Gilbert", "Henri", "Bas", "Peter"],
    "Japan": ["Hiroshi", "Takeshi", "Kenji", "Yuki", "Kazushi", "Norifumi", "Caol"],
    "UK": ["Michael", "Ross", "Tom", "Owen", "Dan", "John", "Marc"],
    "Mexico": ["Juan", "Ricardo", "Erik", "Brandon", "Alejandro", "Cain"],
    "Cuba": ["Yoel", "Hector", "Jorge", "Yordenis", "Guillermo"],
    "Sweden": ["Alexander", "Ilir", "David", "Andreas"],
    "Poland": ["Jan", "Mateusz", "Joanna", "Karolina"],
    "Iran": ["Amir", "Mohammad", "Reza", "Hassan"],
    "South Korea": ["Chan", "Sung", "Jung", "Dong"],
    "Georgia": ["Merab", "Goga", "Levan", "Giorgi"],
    "France": ["Cyril", "Francis", "Benoit", "Cheick"],
    "Australia": ["Rob", "Alexander", "Robert", "George"],
    "Kazakhstan": ["Shavkat", "Marlen", "Gennady"],
}

COACH_LAST_NAMES_BY_NATIONALITY = {
    "USA": ["Williams", "Thompson", "Jackson", "Roufus", "Longo", "Wittman", 
            "Parillo", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Moore"],
    "Brazil": ["Silva", "Cordeiro", "Nogueira", "Pederneiras", "Santos", 
               "Oliveira", "Costa", "Almeida", "Ferreira", "Gracie"],
    "Russia": ["Nurmagomedov", "Petrov", "Volkov", "Romanov", "Emelianenko", 
               "Fedor", "Kharitonov"],
    "Dagestan": ["Nurmagomedov", "Magomedov", "Abdulkerimov", "Gadjiev"],
    "Thailand": ["Pinsinchai", "Kiatmoo9", "Sitnumnoi", "Sasiprapa", "Fairtex"],
    "Netherlands": ["Hemmers", "Dekkers", "Hoost", "Rutten", "Overeem"],
    "Japan": ["Tanaka", "Yamamoto", "Uno", "Sakuraba", "Kawajiri"],
    "UK": ["Hardy", "Sheridan", "Mayfield", "Sherrington", "Watson"],
    "Mexico": ["Moreno", "Velasquez", "Lopez", "Garcia", "Rodriguez"],
    "Cuba": ["Romero", "Lombard", "Gamboa"],
    "Sweden": ["Gustafsson", "Latifi", "Madsen", "Hermansson"],
    "Poland": ["Blachowicz", "Jedrzejczyk", "Kowalkiewicz"],
    "Iran": ["Aliabadi", "Noori", "Mousavi"],
    "South Korea": ["Kim", "Park", "Lee", "Jung", "Choi"],
    "Georgia": ["Dvalishvili", "Chikadze", "Kutateladze"],
    "France": ["Gane", "Ngannou", "Kongo", "Saint-Preux"],
    "Australia": ["Whittaker", "Volkanovski", "Crute", "Tuivasa"],
    "Kazakhstan": ["Rakhmonov", "Esparza", "Golovkin"],
}

COACH_NICKNAMES = [
    "The Professor", "Iron", "The General", "Doc", "Sensei", "Master",
    "The Wizard", "Coach", "Big", "Old", "Young", "The Machine",
    "The Technician", "Stone Cold", "The Hammer", "Lightning",
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tier_value(skill_level: int, tiers: List[Tuple[int, float]]) -> float:
    """Get value from a tiered lookup based on skill level"""
    for threshold, value in tiers:
        if skill_level >= threshold:
            return value
    return tiers[-1][1]  # Return last value as fallback


def get_training_multiplier(skill_level: int) -> float:
    """Get training multiplier for a skill level"""
    return get_tier_value(skill_level, TRAINING_MULTIPLIER_TIERS)


def get_decay_prevention(skill_level: int) -> float:
    """Get decay prevention percentage for a skill level"""
    return get_tier_value(skill_level, DECAY_PREVENTION_TIERS)


def get_scout_variance(skill_level: int) -> int:
    """Get scouting variance (Â±) for a skill level"""
    return int(get_tier_value(skill_level, SCOUT_VARIANCE_TIERS))


def get_camp_building_chance(skill_level: int) -> float:
    """Get chance of passive growth for a skill level"""
    return get_tier_value(skill_level, CAMP_BUILDING_TIERS)


def get_attributes_for_skill(skill: str) -> List[str]:
    """Get fighter attributes affected by a coach skill"""
    return SKILL_ATTRIBUTES.get(skill, [])


def get_skill_for_attribute(attribute: str) -> Optional[str]:
    """Get which coach skill affects a fighter attribute"""
    for skill, attrs in SKILL_ATTRIBUTES.items():
        if attribute in attrs:
            return skill
    return None


# ============================================================================
# COACH DATA CLASS
# ============================================================================

@dataclass
class Coach:
    """
    Represents a coach with skill-based ratings.
    
    Each skill (0-100) affects training, decay prevention, and scouting
    for the fighter attributes in that category.
    """
    coach_id: str
    name: str
    nickname: Optional[str]
    age: int
    nationality: str
    
    # Skill ratings (0-100)
    striking: int
    wrestling: int
    jiu_jitsu: int
    conditioning: int
    strength: int
    
    # Traits and personality
    traits: List[CoachTrait]
    salary_personality: SalaryPersonality
    archetype: CoachArchetype
    
    # Assignment
    camp_id: Optional[str] = None
    is_head_coach: bool = False
    is_founding_coach: bool = False  # Founding coaches work for free (believed in you from day 1)
    
    # Career tracking
    experience_xp: int = 0
    reputation: int = 50
    weeks_coaching: int = 0
    fighters_trained: int = 0
    wins_as_coach: int = 0
    titles_won: int = 0
    
    # Former fighter data (if applicable)
    former_fighter_id: Optional[str] = None
    former_fighter_name: Optional[str] = None
    
    # Pool tracking
    weeks_in_pool: int = 0
    is_retired: bool = False
    
    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------
    
    @property
    def skills(self) -> Dict[str, int]:
        """Get all skills as a dictionary"""
        return {
            "striking": self.striking,
            "wrestling": self.wrestling,
            "jiu_jitsu": self.jiu_jitsu,
            "conditioning": self.conditioning,
            "strength": self.strength,
        }
    
    @property
    def primary_skill(self) -> str:
        """Get the coach's highest skill area"""
        skills = self.skills
        return max(skills, key=skills.get)
    
    @property
    def primary_skill_value(self) -> int:
        """Get the value of the coach's highest skill"""
        return self.skills[self.primary_skill]
    
    @property
    def secondary_skill(self) -> Optional[str]:
        """Get the coach's second highest skill area"""
        skills = self.skills
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_skills) >= 2:
            return sorted_skills[1][0]
        return None
    
    @property
    def overall_rating(self) -> int:
        """Calculate overall rating (weighted average favoring top skills)"""
        skills = sorted(self.skills.values(), reverse=True)
        # Weight: top skill 40%, second 30%, others split 30%
        if len(skills) >= 5:
            weighted = (
                skills[0] * 0.40 +
                skills[1] * 0.30 +
                skills[2] * 0.15 +
                skills[3] * 0.10 +
                skills[4] * 0.05
            )
            return int(weighted)
        return int(sum(skills) / len(skills)) if skills else 50
    
    @property
    def stars(self) -> int:
        """Get star rating (1-5) from overall rating"""
        overall = self.overall_rating
        if overall >= 85:
            return 5
        elif overall >= 75:
            return 4
        elif overall >= 65:
            return 3
        elif overall >= 55:
            return 2
        else:
            return 1
    
    @property
    def display_name(self) -> str:
        """Name with optional nickname"""
        if self.nickname:
            parts = self.name.split()
            if len(parts) >= 2:
                return f'{parts[0]} "{self.nickname}" {parts[-1]}'
        return self.name
    
    @property
    def specialty_display(self) -> str:
        """Human-readable primary specialty"""
        skill_names = {
            "striking": "Striking",
            "wrestling": "Wrestling",
            "jiu_jitsu": "Jiu-Jitsu",
            "conditioning": "Conditioning",
            "strength": "Strength & Power",
        }
        return skill_names.get(self.primary_skill, "General")
    
    @property
    def quality(self) -> int:
        """Alias for overall_rating (for CLI compatibility - expects 0-100)"""
        return self.overall_rating
    
    @property
    def specialty(self) -> 'CoachSpecialty':
        """Get specialty as enum based on primary skill"""
        skill_to_specialty = {
            "striking": CoachSpecialty.STRIKING,
            "wrestling": CoachSpecialty.WRESTLING,
            "jiu_jitsu": CoachSpecialty.JIU_JITSU,
            "conditioning": CoachSpecialty.CONDITIONING,
            "strength": CoachSpecialty.STRENGTH,
        }
        return skill_to_specialty.get(self.primary_skill, CoachSpecialty.STRIKING)
    
    @property
    def quality_multiplier(self) -> float:
        """Training multiplier based on overall rating"""
        overall = self.overall_rating
        if overall >= 85:
            return 1.25
        elif overall >= 75:
            return 1.20
        elif overall >= 65:
            return 1.15
        elif overall >= 55:
            return 1.10
        elif overall >= 45:
            return 1.05
        else:
            return 1.0
    
    @property
    def monthly_salary(self) -> int:
        """Calculate monthly salary with all modifiers"""
        # Founding coaches work for free - they believed in you from day 1
        if self.is_founding_coach:
            return 0
        
        base = get_base_monthly_salary(self.overall_rating)
        
        # Personality modifier
        personality_mult = SALARY_PERSONALITY_MULT.get(self.salary_personality, 1.0)
        salary = base * personality_mult
        
        # Trait modifiers
        trait_mult = 1.0
        for trait in self.traits:
            trait_mult += TRAIT_SALARY_MODS.get(trait, 0)
        salary *= trait_mult
        
        # Reputation bonus ($100 per point above 50)
        if self.reputation > 50:
            salary += (self.reputation - 50) * 100
        
        return int(salary)
    
    @property
    def weekly_salary(self) -> int:
        """Weekly salary (monthly / 4)"""
        return self.monthly_salary // 4
    
    @property
    def is_available(self) -> bool:
        """Is this coach available for hiring?"""
        return self.camp_id is None and not self.is_retired
    
    @property
    def is_poachable(self) -> bool:
        """Can this coach be poached from current camp?"""
        if self.camp_id is None:
            return False
        if CoachTrait.LOYAL in self.traits:
            return False
        if CoachTrait.AMBITIOUS in self.traits:
            return True
        return True
    
    # -------------------------------------------------------------------------
    # Skill Methods
    # -------------------------------------------------------------------------
    
    def get_training_multiplier(self, skill: str) -> float:
        """Get training multiplier for a specific skill area"""
        skill_value = self.skills.get(skill, 50)
        return get_training_multiplier(skill_value)
    
    def get_decay_prevention(self, skill: str) -> float:
        """Get decay prevention for a specific skill area"""
        skill_value = self.skills.get(skill, 50)
        return get_decay_prevention(skill_value)
    
    def get_scout_variance(self, skill: str) -> int:
        """Get scouting variance for a specific skill area"""
        skill_value = self.skills.get(skill, 50)
        return get_scout_variance(skill_value)
    
    def get_camp_building_chance(self, skill: str) -> float:
        """Get passive growth chance for a specific skill area"""
        skill_value = self.skills.get(skill, 50)
        return get_camp_building_chance(skill_value)
    
    def get_attribute_training_multiplier(self, attribute: str) -> float:
        """Get training multiplier for a specific fighter attribute"""
        skill = get_skill_for_attribute(attribute)
        if skill:
            return self.get_training_multiplier(skill)
        return 1.0
    
    def get_attribute_decay_prevention(self, attribute: str) -> float:
        """Get decay prevention for a specific fighter attribute"""
        skill = get_skill_for_attribute(attribute)
        if skill:
            return self.get_decay_prevention(skill)
        return 0.0
    
    def get_attribute_scout_variance(self, attribute: str) -> int:
        """Get scouting variance for a specific fighter attribute"""
        skill = get_skill_for_attribute(attribute)
        if skill:
            return self.get_scout_variance(skill)
        return 10
    
    # -------------------------------------------------------------------------
    # Progression
    # -------------------------------------------------------------------------
    
    def add_xp(self, amount: int) -> bool:
        """
        Add XP and potentially improve skills.
        
        Returns True if a skill improved.
        """
        self.experience_xp += amount
        
        # Check for skill improvement
        if self.experience_xp >= XP_PER_SKILL_POINT:
            self.experience_xp -= XP_PER_SKILL_POINT
            
            # Improve a random skill (weighted toward lower ones)
            skills = self.skills
            weights = [100 - v for v in skills.values()]  # Lower skills more likely
            if sum(weights) > 0:
                skill_name = random.choices(list(skills.keys()), weights=weights)[0]
                current = getattr(self, skill_name)
                if current < 95:  # Cap at 95
                    setattr(self, skill_name, current + 1)
                    return True
        return False
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "coach_id": self.coach_id,
            "name": self.name,
            "nickname": self.nickname,
            "age": self.age,
            "nationality": self.nationality,
            "striking": self.striking,
            "wrestling": self.wrestling,
            "jiu_jitsu": self.jiu_jitsu,
            "conditioning": self.conditioning,
            "strength": self.strength,
            "traits": [t.value for t in self.traits],
            "salary_personality": self.salary_personality.value,
            "archetype": self.archetype.value,
            "camp_id": self.camp_id,
            "is_head_coach": self.is_head_coach,
            "is_founding_coach": self.is_founding_coach,
            "experience_xp": self.experience_xp,
            "reputation": self.reputation,
            "weeks_coaching": self.weeks_coaching,
            "fighters_trained": self.fighters_trained,
            "wins_as_coach": self.wins_as_coach,
            "titles_won": self.titles_won,
            "former_fighter_id": self.former_fighter_id,
            "former_fighter_name": self.former_fighter_name,
            "weeks_in_pool": self.weeks_in_pool,
            "is_retired": self.is_retired,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Coach":
        """Deserialize from dictionary. Can also handle StartingCoach data as fallback."""
        # Handle StartingCoach data format
        if data.get("_type") == "StartingCoach" or "skill_level" in data:
            # Convert StartingCoach fields to Coach fields
            skill = data.get("skill_level", 70)
            specialty = data.get("specialty", "Striking")
            
            # Map specialty to skill values
            specialty_skills = {
                "Striking": {"striking": skill, "wrestling": 40, "jiu_jitsu": 40, "conditioning": 50, "strength": 45},
                "Boxing": {"striking": skill, "wrestling": 40, "jiu_jitsu": 40, "conditioning": 50, "strength": 45},
                "Wrestling": {"striking": 40, "wrestling": skill, "jiu_jitsu": 45, "conditioning": 50, "strength": 50},
                "BJJ": {"striking": 40, "wrestling": 45, "jiu_jitsu": skill, "conditioning": 45, "strength": 40},
                "Conditioning": {"striking": 45, "wrestling": 45, "jiu_jitsu": 45, "conditioning": skill, "strength": 45},
                "Strength": {"striking": 45, "wrestling": 50, "jiu_jitsu": 40, "conditioning": 50, "strength": skill},
                "Cornering": {"striking": 50, "wrestling": 50, "jiu_jitsu": 50, "conditioning": 50, "strength": 50},
            }
            skills = specialty_skills.get(specialty, {"striking": 50, "wrestling": 50, "jiu_jitsu": 50, "conditioning": 50, "strength": 50})
            
            return cls(
                coach_id=data.get("coach_id", ""),
                name=data.get("name", "Coach"),
                nickname=None,
                age=35 + data.get("years_experience", 5),
                nationality="USA",
                striking=skills["striking"],
                wrestling=skills["wrestling"],
                jiu_jitsu=skills["jiu_jitsu"],
                conditioning=skills["conditioning"],
                strength=skills["strength"],
                traits=[],
                salary_personality=SalaryPersonality.STANDARD,
                archetype=CoachArchetype.GENERALIST,
                camp_id=data.get("camp_id"),
                is_head_coach=data.get("is_head_coach", False),
                is_founding_coach=True,
                experience_xp=0,
                reputation=50,
                weeks_coaching=0,
                fighters_trained=0,
                wins_as_coach=0,
                titles_won=0,
                former_fighter_id=None,
                former_fighter_name=None,
                weeks_in_pool=0,
                is_retired=False,
            )
        
        # Standard Coach deserialization
        return cls(
            coach_id=data["coach_id"],
            name=data["name"],
            nickname=data.get("nickname"),
            age=data.get("age", 40),
            nationality=data.get("nationality", "USA"),
            striking=data.get("striking", 50),
            wrestling=data.get("wrestling", 50),
            jiu_jitsu=data.get("jiu_jitsu", 50),
            conditioning=data.get("conditioning", 50),
            strength=data.get("strength", 50),
            traits=[CoachTrait(t) for t in data.get("traits", [])],
            salary_personality=SalaryPersonality(data.get("salary_personality", "Standard")),
            archetype=CoachArchetype(data.get("archetype", "Generalist")),
            camp_id=data.get("camp_id"),
            is_head_coach=data.get("is_head_coach", False),
            is_founding_coach=data.get("is_founding_coach", False),
            experience_xp=data.get("experience_xp", 0),
            reputation=data.get("reputation", 50),
            weeks_coaching=data.get("weeks_coaching", 0),
            fighters_trained=data.get("fighters_trained", 0),
            wins_as_coach=data.get("wins_as_coach", 0),
            titles_won=data.get("titles_won", 0),
            former_fighter_id=data.get("former_fighter_id"),
            former_fighter_name=data.get("former_fighter_name"),
            weeks_in_pool=data.get("weeks_in_pool", 0),
            is_retired=data.get("is_retired", False),
        )


# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================

def generate_coach_id() -> str:
    """Generate unique coach ID"""
    import uuid
    return f"coach_{uuid.uuid4().hex[:8]}"


def generate_nationality() -> str:
    """Generate a random nationality based on distribution"""
    nations = list(NATIONALITY_WEIGHTS.keys())
    weights = list(NATIONALITY_WEIGHTS.values())
    return random.choices(nations, weights=weights)[0]


def generate_coach_name(nationality: str) -> Tuple[str, Optional[str]]:
    """Generate coach name based on nationality"""
    # Get name pools, falling back to USA if nationality not found
    first_names = COACH_FIRST_NAMES_BY_NATIONALITY.get(
        nationality, 
        COACH_FIRST_NAMES_BY_NATIONALITY["USA"]
    )
    last_names = COACH_LAST_NAMES_BY_NATIONALITY.get(
        nationality,
        COACH_LAST_NAMES_BY_NATIONALITY["USA"]
    )
    
    first = random.choice(first_names)
    last = random.choice(last_names)
    
    # 25% chance of nickname
    nickname = None
    if random.random() < 0.25:
        nickname = random.choice(COACH_NICKNAMES)
    
    return f"{first} {last}", nickname


def generate_salary_personality() -> SalaryPersonality:
    """Generate salary personality based on distribution"""
    personalities = list(SALARY_PERSONALITY_WEIGHTS.keys())
    weights = list(SALARY_PERSONALITY_WEIGHTS.values())
    return random.choices(personalities, weights=weights)[0]


def generate_archetype() -> CoachArchetype:
    """Generate a coach archetype based on distribution"""
    archetypes = list(ARCHETYPE_WEIGHTS.keys())
    weights = list(ARCHETYPE_WEIGHTS.values())
    return random.choices(archetypes, weights=weights)[0]


def generate_skills(
    archetype: CoachArchetype, 
    nationality: str,
    primary_skill: Optional[str] = None,
) -> Dict[str, int]:
    """
    Generate skill ratings based on archetype and nationality.
    
    Args:
        archetype: The coach's archetype
        nationality: Coach's nationality for regional bonuses
        primary_skill: Force this skill to be primary (for specialty generation)
        
    Returns:
        Dictionary of skill ratings
    """
    skills = {
        "striking": 50,
        "wrestling": 50,
        "jiu_jitsu": 50,
        "conditioning": 50,
        "strength": 50,
    }
    
    skill_list = list(skills.keys())
    random.shuffle(skill_list)
    
    # If primary_skill specified, move it to front
    if primary_skill and primary_skill in skill_list:
        skill_list.remove(primary_skill)
        skill_list.insert(0, primary_skill)
    
    if archetype == CoachArchetype.SPECIALIST:
        # One skill 75-95, others 30-55
        primary = skill_list[0]
        skills[primary] = random.randint(75, 95)
        for skill in skill_list[1:]:
            skills[skill] = random.randint(30, 55)
            
    elif archetype == CoachArchetype.DUAL_FOCUS:
        # Two skills 65-85, others 35-55
        primary = skill_list[0]
        secondary = skill_list[1]
        skills[primary] = random.randint(70, 85)
        skills[secondary] = random.randint(65, 80)
        for skill in skill_list[2:]:
            skills[skill] = random.randint(35, 55)
            
    elif archetype == CoachArchetype.GENERALIST:
        # All skills 45-65
        for skill in skill_list:
            skills[skill] = random.randint(45, 65)
            
    elif archetype == CoachArchetype.LEGEND:
        # One skill 88-98, two at 60-80, rest 40-55
        primary = skill_list[0]
        secondary = skill_list[1]
        tertiary = skill_list[2]
        skills[primary] = random.randint(88, 98)
        skills[secondary] = random.randint(65, 80)
        skills[tertiary] = random.randint(60, 75)
        for skill in skill_list[3:]:
            skills[skill] = random.randint(40, 55)
    
    # Apply regional bonuses
    bonuses = REGIONAL_BONUSES.get(nationality, {})
    for skill, bonus in bonuses.items():
        if skill in skills:
            skills[skill] = min(99, skills[skill] + bonus)
    
    return skills


def generate_coach_traits(overall_rating: int) -> List[CoachTrait]:
    """
    Generate traits for a coach.
    
    Higher rated coaches get better trait distribution.
    """
    traits = []
    
    # Determine number of traits (1-2)
    num_traits = 1 if random.random() < 0.6 else 2
    
    # Overall rating affects trait distribution
    # Higher overall = more likely positive, less likely negative
    positive_weight = 35 + int(overall_rating * 0.4)  # 55-75%
    personality_weight = 25
    negative_weight = max(5, 40 - int(overall_rating * 0.4))  # 0-20%
    special_weight = 10
    
    for _ in range(num_traits):
        roll = random.randint(1, 100)
        
        if roll <= positive_weight:
            pool = [t for t in POSITIVE_TRAITS if t not in traits]
        elif roll <= positive_weight + personality_weight:
            pool = [t for t in PERSONALITY_TRAITS if t not in traits]
        elif roll <= positive_weight + personality_weight + negative_weight:
            pool = [t for t in NEGATIVE_TRAITS if t not in traits]
        else:
            pool = [t for t in SPECIAL_TRAITS if t not in traits]
        
        if pool:
            traits.append(random.choice(pool))
    
    return traits


def generate_coach(
    archetype: Optional[CoachArchetype] = None,
    nationality: Optional[str] = None,
    age: Optional[int] = None,
    min_overall: Optional[int] = None,
    max_overall: Optional[int] = None,
    quality: Optional[int] = None,
    specialty: Optional['CoachSpecialty'] = None,
) -> Coach:
    """
    Generate a random coach.
    
    Args:
        archetype: Force specific archetype, or None for random
        nationality: Force nationality, or None for random
        age: Force age, or None for random
        min_overall: Minimum overall rating (regenerates if below)
        max_overall: Maximum overall rating (regenerates if above)
        quality: Star rating 1-5 (converted to min/max overall)
        specialty: CoachSpecialty to emphasize (converted to archetype)
        
    Returns:
        New Coach instance
    """
    # Convert quality (1-5 stars) to overall range
    if quality is not None:
        quality_ranges = {
            1: (30, 45),
            2: (45, 55),
            3: (55, 70),
            4: (70, 82),
            5: (82, 95),
        }
        min_o, max_o = quality_ranges.get(quality, (50, 65))
        if min_overall is None:
            min_overall = min_o
        if max_overall is None:
            max_overall = max_o
    
    # Convert specialty to archetype preference
    if specialty is not None and archetype is None:
        # Use SPECIALIST archetype for specific specialty
        archetype = CoachArchetype.SPECIALIST
    
    # Generate archetype if not specified
    if archetype is None:
        archetype = generate_archetype()
    
    # Generate nationality if not specified
    if nationality is None:
        nationality = generate_nationality()
    
    # Generate age if not specified (most coaches 35-55)
    if age is None:
        age = random.randint(32, 58)
    
    # Convert specialty to primary skill name
    primary_skill = None
    if specialty is not None:
        specialty_to_skill = {
            CoachSpecialty.STRIKING: "striking",
            CoachSpecialty.WRESTLING: "wrestling",
            CoachSpecialty.JIU_JITSU: "jiu_jitsu",
            CoachSpecialty.CONDITIONING: "conditioning",
            CoachSpecialty.STRENGTH: "strength",
            CoachSpecialty.CORNERING: "conditioning",  # Cornering maps to conditioning
        }
        primary_skill = specialty_to_skill.get(specialty)
    
    # Generate skills (may retry for overall constraints)
    max_attempts = 10
    for _ in range(max_attempts):
        skills = generate_skills(archetype, nationality, primary_skill)
        
        # Calculate overall to check constraints
        skill_values = sorted(skills.values(), reverse=True)
        overall = int(
            skill_values[0] * 0.40 +
            skill_values[1] * 0.30 +
            skill_values[2] * 0.15 +
            skill_values[3] * 0.10 +
            skill_values[4] * 0.05
        )
        
        # Check constraints
        if min_overall and overall < min_overall:
            continue
        if max_overall and overall > max_overall:
            continue
        break
    
    # Generate name
    name, nickname = generate_coach_name(nationality)
    
    # Generate traits based on overall
    traits = generate_coach_traits(overall)
    
    # Generate salary personality
    salary_personality = generate_salary_personality()
    
    # Generate reputation based on overall
    base_rep = int(overall * 0.6)
    reputation = base_rep + random.randint(-10, 15)
    reputation = max(10, min(90, reputation))
    
    return Coach(
        coach_id=generate_coach_id(),
        name=name,
        nickname=nickname,
        age=age,
        nationality=nationality,
        striking=skills["striking"],
        wrestling=skills["wrestling"],
        jiu_jitsu=skills["jiu_jitsu"],
        conditioning=skills["conditioning"],
        strength=skills["strength"],
        traits=traits,
        salary_personality=salary_personality,
        archetype=archetype,
        reputation=reputation,
    )


def generate_starting_coach_options(count: int = 3) -> List[Coach]:
    """
    Generate coach options for player to choose from at game start.
    
    Returns coaches with varied specialties and moderate overall ratings.
    """
    coaches = []
    used_primaries: Set[str] = set()
    
    # Preferred primary skills for diversity
    preferred = ["striking", "wrestling", "jiu_jitsu"]
    
    for i in range(count):
        # Try to get diverse primaries
        target_primary = preferred[i] if i < len(preferred) else None
        
        max_attempts = 20
        for _ in range(max_attempts):
            # Generate 2-3 star coach
            coach = generate_coach(
                archetype=CoachArchetype.SPECIALIST,
                min_overall=55,
                max_overall=70,
            )
            
            # Check diversity
            if target_primary and coach.primary_skill != target_primary:
                continue
            if coach.primary_skill in used_primaries:
                continue
            
            used_primaries.add(coach.primary_skill)
            coaches.append(coach)
            break
        else:
            # Fallback - just add any coach
            coach = generate_coach(min_overall=55, max_overall=70)
            coaches.append(coach)
    
    return coaches


def convert_fighter_to_coach(
    fighter_id: str,
    fighter_name: str,
    fighter_stats: Dict[str, int],
    was_champion: bool,
    age: int,
    nationality: str = "USA",
) -> Optional[Coach]:
    """
    Convert a retiring fighter into a coach.
    
    Args:
        fighter_id: Fighter's ID
        fighter_name: Fighter's name
        fighter_stats: Dictionary of fighter's stats
        was_champion: Did fighter hold a title
        age: Fighter's age at retirement
        nationality: Fighter's nationality
        
    Returns:
        New Coach or None if fighter doesn't qualify
    """
    # Calculate what their coaching skills would be based on fighter stats
    # Coaches get about 70-80% of their fighter stats as coaching ability
    coach_mult = random.uniform(0.70, 0.85)
    
    # Map fighter stats to coach skills (support both old and new attribute names)
    striking = int(((fighter_stats.get("boxing", 50) + fighter_stats.get("kicks", 50)) / 2) * coach_mult)
    takedowns_val = fighter_stats.get("takedowns", fighter_stats.get("wrestling", 50))
    td_def_val = fighter_stats.get("takedown_defense", fighter_stats.get("td_defense", 50))
    wrestling = int(((takedowns_val + td_def_val) / 2) * coach_mult)
    subs_val = fighter_stats.get("submissions", fighter_stats.get("bjj", 50))
    guard_val = fighter_stats.get("guard", subs_val)
    jiu_jitsu = int(((subs_val + guard_val) / 2) * coach_mult)
    conditioning = int(((fighter_stats.get("cardio", 50) + fighter_stats.get("chin", 50)) / 2) * coach_mult)
    strength_val = int(((fighter_stats.get("strength", 50) + fighter_stats.get("speed", 50)) / 2) * coach_mult)
    
    # Champions get a bonus
    if was_champion:
        striking = min(95, striking + 5)
        wrestling = min(95, wrestling + 5)
        jiu_jitsu = min(95, jiu_jitsu + 5)
        conditioning = min(95, conditioning + 5)
        strength_val = min(95, strength_val + 5)
    
    # Minimum quality check
    skills = [striking, wrestling, jiu_jitsu, conditioning, strength_val]
    if max(skills) < 55:
        return None  # Not good enough to coach
    
    # Determine archetype from skill distribution
    sorted_skills = sorted(skills, reverse=True)
    if sorted_skills[0] - sorted_skills[1] >= 15:
        archetype = CoachArchetype.SPECIALIST
    elif sorted_skills[1] >= 60:
        archetype = CoachArchetype.DUAL_FOCUS
    else:
        archetype = CoachArchetype.GENERALIST
    
    # Generate traits (former fighters get better traits)
    overall = int(sorted_skills[0] * 0.4 + sorted_skills[1] * 0.3 + sum(sorted_skills[2:]) / 3 * 0.3)
    traits = generate_coach_traits(overall)
    
    # Former fighters tend to have calm corner trait
    if random.random() < 0.3:
        if CoachTrait.CALM_CORNER not in traits and len(traits) < 3:
            traits.append(CoachTrait.CALM_CORNER)
    
    # Reputation based on champion status
    reputation = 55 + random.randint(0, 15)
    if was_champion:
        reputation += 20
    reputation = min(90, reputation)
    
    # Salary personality - former fighters tend to be modest
    personality = random.choices(
        [SalaryPersonality.HUMBLE, SalaryPersonality.MODEST, SalaryPersonality.STANDARD],
        weights=[25, 45, 30]
    )[0]
    
    return Coach(
        coach_id=generate_coach_id(),
        name=fighter_name,
        nickname=None,
        age=age,
        nationality=nationality,
        striking=striking,
        wrestling=wrestling,
        jiu_jitsu=jiu_jitsu,
        conditioning=conditioning,
        strength=strength_val,
        traits=traits,
        salary_personality=personality,
        archetype=archetype,
        reputation=reputation,
        former_fighter_id=fighter_id,
        former_fighter_name=fighter_name,
    )


# ============================================================================
# CHEMISTRY CALCULATIONS
# ============================================================================

def calculate_chemistry(coach: Coach, fighter_traits: List[str], fighter_age: int) -> int:
    """
    Calculate chemistry score between coach and fighter.
    
    Args:
        coach: The coach
        fighter_traits: List of fighter trait names
        fighter_age: Fighter's age
        
    Returns:
        Chemistry score 0-100
    """
    score = 50  # Base neutral
    
    # Trait synergies
    for coach_trait in coach.traits:
        coach_trait_name = coach_trait.value
        for fighter_trait in fighter_traits:
            synergy = TRAIT_SYNERGY.get((coach_trait_name, fighter_trait), 0)
            score += synergy
    
    # Age-based chemistry
    is_young = fighter_age < 26
    is_veteran = fighter_age >= 33
    
    if CoachTrait.DIAMOND_POLISHER in coach.traits and is_young:
        score += 10
    if CoachTrait.VETERANS_TOUCH in coach.traits and is_veteran:
        score += 10
    if CoachTrait.MODERN_METHODS in coach.traits and is_young:
        score += 5
    if CoachTrait.OLD_SCHOOL in coach.traits and is_veteran:
        score += 5
    if CoachTrait.OUTDATED in coach.traits and is_young:
        score -= 10
    
    # Clamp to valid range
    return max(0, min(100, score))


def get_chemistry_description(chemistry_score: int) -> str:
    """Get human-readable chemistry description"""
    if chemistry_score >= 80:
        return "Excellent"
    elif chemistry_score >= 65:
        return "Good"
    elif chemistry_score >= 50:
        return "Neutral"
    elif chemistry_score >= 35:
        return "Poor"
    else:
        return "Terrible"


# ============================================================================
# COACH SYSTEM
# ============================================================================

class CoachSystem:
    """
    Central coach management system.
    
    Handles coach pool, hiring, firing, progression, and AI management.
    """
    
    def __init__(self):
        # All coaches in the game
        self._coaches: Dict[str, Coach] = {}
        
        # Coaches by camp
        self._camp_coaches: Dict[str, List[str]] = {}  # camp_id -> [coach_ids]
        
        # Free agent pool
        self._available_pool: List[str] = []
        
        # Stats
        self.total_coaches_generated: int = 0
        self.total_hires: int = 0
        self.total_fires: int = 0
    
    def generate_initial_pool(self, count: int = 30) -> None:
        """
        Generate the initial coach pool with varied ratings.
        
        Distribution aims for realistic spread of quality.
        """
        # Generate by archetype distribution naturally
        for _ in range(count):
            coach = generate_coach()
            self._coaches[coach.coach_id] = coach
            self._available_pool.append(coach.coach_id)
            self.total_coaches_generated += 1
    
    def generate_ai_starting_coaches(self, camp_id: str, tier: str, nationality_hint: str = None) -> List[Coach]:
        """
        Generate starting coaches for an AI camp.
        
        Args:
            camp_id: Camp ID
            tier: Camp tier (GARAGE, LOCAL, etc.)
            nationality_hint: Optional nationality preference
            
        Returns:
            List of coaches assigned to camp
        """
        max_coaches = MAX_COACHES_BY_TIER.get(tier, 1)
        coaches = []
        
        # Head coach quality based on tier
        tier_overall = {
            "GARAGE": (50, 65),
            "LOCAL": (55, 70),
            "REGIONAL": (60, 75),
            "NATIONAL": (70, 85),
            "ELITE": (75, 92),
        }.get(tier, (50, 65))
        
        # Generate head coach
        head_coach = generate_coach(
            nationality=nationality_hint,
            min_overall=tier_overall[0],
            max_overall=tier_overall[1],
        )
        head_coach.camp_id = camp_id
        head_coach.is_head_coach = True
        self._coaches[head_coach.coach_id] = head_coach
        coaches.append(head_coach)
        self.total_coaches_generated += 1
        
        # Generate assistant coaches (slightly lower quality)
        for _ in range(max_coaches - 1):
            assistant = generate_coach(
                nationality=nationality_hint if random.random() < 0.5 else None,
                min_overall=max(40, tier_overall[0] - 10),
                max_overall=tier_overall[1] - 5,
            )
            assistant.camp_id = camp_id
            self._coaches[assistant.coach_id] = assistant
            coaches.append(assistant)
            self.total_coaches_generated += 1
        
        # Track camp coaches
        self._camp_coaches[camp_id] = [c.coach_id for c in coaches]
        
        return coaches
    
    def get_coach(self, coach_id: str) -> Optional[Coach]:
        """Get a coach by ID"""
        return self._coaches.get(coach_id)
    
    def get_available_coaches(self) -> List[Coach]:
        """Get all coaches in the free agent pool"""
        return [self._coaches[cid] for cid in self._available_pool 
                if cid in self._coaches and self._coaches[cid].is_available]
    
    def get_camp_coaches(self, camp_id: str) -> List[Coach]:
        """Get all coaches for a camp"""
        coach_ids = self._camp_coaches.get(camp_id, [])
        return [self._coaches[cid] for cid in coach_ids if cid in self._coaches]
    
    def get_head_coach(self, camp_id: str) -> Optional[Coach]:
        """Get head coach for a camp"""
        for coach in self.get_camp_coaches(camp_id):
            if coach.is_head_coach:
                return coach
        return None
    
    def get_camp_coach_count(self, camp_id: str) -> int:
        """Get number of coaches at a camp"""
        return len(self._camp_coaches.get(camp_id, []))
    
    def get_max_coaches(self, tier: str) -> int:
        """Get max coaches allowed for a tier"""
        return MAX_COACHES_BY_TIER.get(tier, 1)
    
    def can_hire(self, camp_id: str, tier: str) -> bool:
        """Check if camp can hire another coach"""
        current = self.get_camp_coach_count(camp_id)
        max_allowed = self.get_max_coaches(tier)
        return current < max_allowed
    
    def hire_coach(self, camp_id: str, coach_id: str, as_head: bool = False) -> bool:
        """
        Hire a coach from the pool.
        
        Args:
            camp_id: Camp hiring the coach
            coach_id: Coach to hire
            as_head: Should this be the head coach?
            
        Returns:
            True if hired successfully
        """
        coach = self._coaches.get(coach_id)
        if not coach or not coach.is_available:
            return False
        
        # Remove from pool
        if coach_id in self._available_pool:
            self._available_pool.remove(coach_id)
        
        # Assign to camp
        coach.camp_id = camp_id
        coach.weeks_in_pool = 0
        
        # Add to camp roster
        if camp_id not in self._camp_coaches:
            self._camp_coaches[camp_id] = []
        self._camp_coaches[camp_id].append(coach_id)
        
        # Handle head coach
        if as_head or not self.get_head_coach(camp_id):
            # Demote current head if exists
            current_head = self.get_head_coach(camp_id)
            if current_head:
                current_head.is_head_coach = False
            coach.is_head_coach = True
        
        self.total_hires += 1
        return True
    
    def fire_coach(self, camp_id: str, coach_id: str) -> bool:
        """
        Fire a coach from a camp.
        
        Args:
            camp_id: Camp firing the coach
            coach_id: Coach to fire
            
        Returns:
            True if fired successfully
        """
        coach = self._coaches.get(coach_id)
        if not coach or coach.camp_id != camp_id:
            return False
        
        # Remove from camp
        if camp_id in self._camp_coaches:
            if coach_id in self._camp_coaches[camp_id]:
                self._camp_coaches[camp_id].remove(coach_id)
        
        # Promote new head if this was head
        if coach.is_head_coach:
            remaining = self.get_camp_coaches(camp_id)
            if remaining:
                remaining[0].is_head_coach = True
        
        # Reset coach
        coach.camp_id = None
        coach.is_head_coach = False
        
        # Add back to pool
        self._available_pool.append(coach_id)
        
        self.total_fires += 1
        return True
    
    def set_head_coach(self, camp_id: str, coach_id: str) -> bool:
        """Set a coach as head coach (demoting current head)."""
        coach = self._coaches.get(coach_id)
        if not coach or coach.camp_id != camp_id:
            return False
        
        # Demote current head
        current_head = self.get_head_coach(camp_id)
        if current_head:
            current_head.is_head_coach = False
        
        # Promote new head
        coach.is_head_coach = True
        return True
    
    def add_coach_to_pool(self, coach: Coach) -> None:
        """Add a coach to the system and pool"""
        self._coaches[coach.coach_id] = coach
        if coach.is_available:
            self._available_pool.append(coach.coach_id)
    
    # -------------------------------------------------------------------------
    # Camp Skill Calculations
    # -------------------------------------------------------------------------
    
    def get_camp_skill(self, camp_id: str, skill: str) -> int:
        """
        Get the effective skill level for a camp in an area.
        
        Head coach contributes 100%, assistants contribute 50%.
        """
        coaches = self.get_camp_coaches(camp_id)
        if not coaches:
            return 40  # Baseline for no coaches
        
        head = self.get_head_coach(camp_id)
        assistants = [c for c in coaches if not c.is_head_coach]
        
        # Head coach primary contribution
        if head:
            base_skill = head.skills.get(skill, 50)
        else:
            base_skill = 50
        
        # Assistants add 50% of their skill above 50
        assistant_bonus = 0
        for assistant in assistants:
            ass_skill = assistant.skills.get(skill, 50)
            if ass_skill > 50:
                assistant_bonus += (ass_skill - 50) * 0.5
        
        return min(99, int(base_skill + assistant_bonus))
    
    def get_camp_training_multiplier(self, camp_id: str, skill: str) -> float:
        """Get the training multiplier for a camp in a skill area"""
        camp_skill = self.get_camp_skill(camp_id, skill)
        return get_training_multiplier(camp_skill)
    
    def get_camp_decay_prevention(self, camp_id: str, skill: str) -> float:
        """Get decay prevention for a camp in a skill area"""
        camp_skill = self.get_camp_skill(camp_id, skill)
        return get_decay_prevention(camp_skill)
    
    def get_camp_scout_variance(self, camp_id: str, skill: str) -> int:
        """Get scouting variance for a camp in a skill area"""
        camp_skill = self.get_camp_skill(camp_id, skill)
        return get_scout_variance(camp_skill)
    
    def get_camp_building_chance(self, camp_id: str, skill: str) -> float:
        """Get passive growth chance for a camp in a skill area"""
        camp_skill = self.get_camp_skill(camp_id, skill)
        return get_camp_building_chance(camp_skill)
    
    def get_camp_training_bonus(self, camp_id: str) -> float:
        """
        Get overall training bonus for a camp (average of all skills).
        
        Returns multiplier (1.0 = baseline).
        """
        multipliers = []
        for skill in SKILL_NAMES:
            multipliers.append(self.get_camp_training_multiplier(camp_id, skill))
        return sum(multipliers) / len(multipliers) if multipliers else 0.9
    
    # -------------------------------------------------------------------------
    # Weekly/Monthly Processing
    # -------------------------------------------------------------------------
    
    def process_weekly_xp(self, camp_id: str, roster_size: int) -> None:
        """Process weekly XP gains for camp coaches."""
        for coach in self.get_camp_coaches(camp_id):
            coach.weeks_coaching += 1
            xp_gain = 1
            
            # Bonus for larger rosters
            if roster_size >= 5:
                xp_gain += 1
            
            coach.add_xp(xp_gain)
    
    def record_fight_result(self, camp_id: str, won: bool, was_title: bool = False) -> None:
        """Record fight result for coach XP."""
        for coach in self.get_camp_coaches(camp_id):
            if won:
                coach.wins_as_coach += 1
                coach.add_xp(3)
                if was_title:
                    coach.titles_won += 1
                    coach.add_xp(22)  # 25 total for title win
            else:
                coach.add_xp(1)  # Learn from losses too
    
    def process_camp_building(self, camp_id: str, fighters: List[Any]) -> List[str]:
        """
        Process monthly passive growth for fighters in a camp.
        
        Args:
            camp_id: Camp ID
            fighters: List of fighter data objects with attribute access
            
        Returns:
            List of growth event descriptions
        """
        events = []
        
        for skill in SKILL_NAMES:
            chance = self.get_camp_building_chance(camp_id, skill)
            if chance <= 0:
                continue
            
            # Check each fighter
            for fighter in fighters:
                if random.random() < chance:
                    # Pick a random attribute in this skill area
                    attributes = get_attributes_for_skill(skill)
                    if attributes:
                        attr = random.choice(attributes)
                        current = getattr(fighter, attr, 50)
                        if current < 90:  # Cap passive growth
                            # Growth amount based on coach skill
                            camp_skill = self.get_camp_skill(camp_id, skill)
                            growth = 2 if camp_skill >= 90 else 1
                            setattr(fighter, attr, min(99, current + growth))
                            
                            skill_display = skill.replace("_", " ").title()
                            events.append(
                                f"{getattr(fighter, 'name', 'Fighter')} +{growth} {attr} (camp training in {skill_display})"
                            )
        
        return events
    
    def process_monthly_pool(self) -> List[str]:
        """
        Process monthly pool updates.
        
        - Add 1-2 new coaches
        - Remove coaches in pool too long
        
        Returns:
            List of event descriptions
        """
        events = []
        
        # Add new coaches (1-2)
        num_new = random.randint(1, 2)
        for _ in range(num_new):
            coach = generate_coach()
            self.add_coach_to_pool(coach)
            self.total_coaches_generated += 1
            events.append(
                f"New coach available: {coach.display_name} ({coach.stars}â˜… {coach.specialty_display})"
            )
        
        # Age coaches in pool
        for coach_id in list(self._available_pool):
            coach = self._coaches.get(coach_id)
            if coach:
                coach.weeks_in_pool += 4  # Monthly
                
                # Retire after 2 years in pool (rare)
                if coach.weeks_in_pool > 104:
                    if random.random() < 0.2:
                        coach.is_retired = True
                        self._available_pool.remove(coach_id)
                        events.append(f"Coach {coach.name} has retired from coaching")
        
        return events
    
    def get_total_weekly_salary(self, camp_id: str) -> int:
        """Get total weekly salary for all camp coaches"""
        return sum(c.weekly_salary for c in self.get_camp_coaches(camp_id))
    
    def get_total_monthly_salary(self, camp_id: str) -> int:
        """Get total monthly salary for all camp coaches"""
        return sum(c.monthly_salary for c in self.get_camp_coaches(camp_id))
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "coaches": {cid: c.to_dict() for cid, c in self._coaches.items()},
            "camp_coaches": self._camp_coaches,
            "available_pool": self._available_pool,
            "total_coaches_generated": self.total_coaches_generated,
            "total_hires": self.total_hires,
            "total_fires": self.total_fires,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoachSystem":
        """Deserialize from dictionary"""
        system = cls()
        
        for cid, coach_data in data.get("coaches", {}).items():
            # Check for type marker to handle StartingCoach
            if coach_data.get("_type") == "StartingCoach":
                try:
                    from systems.game_start import StartingCoach
                    system._coaches[cid] = StartingCoach.from_dict(coach_data)
                except ImportError:
                    # Fallback: convert to Coach
                    system._coaches[cid] = Coach.from_dict(coach_data)
            else:
                system._coaches[cid] = Coach.from_dict(coach_data)
        
        system._camp_coaches = data.get("camp_coaches", {})
        system._available_pool = data.get("available_pool", [])
        system.total_coaches_generated = data.get("total_coaches_generated", 0)
        system.total_hires = data.get("total_hires", 0)
        system.total_fires = data.get("total_fires", 0)
        
        return system


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def format_coach_stars(stars: int) -> str:
    """Format star rating as string"""
    return "â˜…" * stars + "â˜†" * (5 - stars)


def format_coach_salary(salary: int) -> str:
    """Format salary as money string"""
    return f"${salary:,}/mo"


def format_coach_skills(coach: Coach) -> str:
    """Format coach skills as compact display"""
    skills = [
        f"STR:{coach.striking}",
        f"WRS:{coach.wrestling}",
        f"BJJ:{coach.jiu_jitsu}",
        f"CND:{coach.conditioning}",
        f"PWR:{coach.strength}",
    ]
    return " | ".join(skills)


def format_coach_display(coach: Coach) -> str:
    """Format coach for display"""
    stars = format_coach_stars(coach.stars)
    traits_str = ", ".join(t.value for t in coach.traits) if coach.traits else "None"
    
    return (
        f"{stars} {coach.display_name} ({coach.nationality})\n"
        f"   Primary: {coach.specialty_display} ({coach.primary_skill_value})\n"
        f"   Skills: {format_coach_skills(coach)}\n"
        f"   Traits: {traits_str}\n"
        f"   Salary: {format_coach_salary(coach.monthly_salary)}"
    )


def get_trait_description(trait: CoachTrait) -> str:
    """Get human-readable description of a coach trait"""
    descriptions = {
        CoachTrait.MOTIVATOR: "Boosts training for fighters with low morale",
        CoachTrait.TECHNICAL_GENIUS: "Excels at teaching technical skills",
        CoachTrait.DIAMOND_POLISHER: "Exceptional at developing young prospects",
        CoachTrait.VETERANS_TOUCH: "Knows how to maintain veteran fighters",
        CoachTrait.IRON_SHARPENER: "Camp sparring produces better results",
        CoachTrait.CALM_CORNER: "Improves composure and between-round recovery",
        CoachTrait.EYE_FOR_TALENT: "Better at scouting and evaluating fighters",
        CoachTrait.TASKMASTER: "Intense training (+15%) but hurts morale",
        CoachTrait.DISCIPLINARIAN: "Works well with disciplined fighters",
        CoachTrait.PLAYERS_COACH: "Boosts morale but slightly less effective training",
        CoachTrait.INTENSE: "High-energy training style",
        CoachTrait.ANALYTICAL: "Excellent game planning, methodical training",
        CoachTrait.OLD_SCHOOL: "Great conditioning, less modern techniques",
        CoachTrait.MODERN_METHODS: "Cutting-edge techniques for young fighters",
        CoachTrait.BURNED_OUT: "Reduced training effectiveness",
        CoachTrait.PRIMA_DONNA: "Demands higher salary",
        CoachTrait.CLASHING_EGO: "Conflicts with other high-quality coaches",
        CoachTrait.OUTDATED: "Less effective with young fighters",
        CoachTrait.INJURY_RISK: "Training has higher injury risk",
        CoachTrait.FAIR_WEATHER: "Less effective when camp is losing",
        CoachTrait.LOYAL: "Won't leave for other camps",
        CoachTrait.AMBITIOUS: "May be tempted by better offers",
    }
    return descriptions.get(trait, "Unknown trait")


def get_skill_description(skill: str) -> str:
    """Get description of what a skill improves"""
    descriptions = {
        "striking": "Boxing, kicks, clinch, accuracy",
        "wrestling": "Wrestling, takedown defense, top control",
        "jiu_jitsu": "BJJ, submissions",
        "conditioning": "Cardio, chin, recovery",
        "strength": "Strength, speed, power",
    }
    return descriptions.get(skill, "General training")
