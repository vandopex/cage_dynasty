# systems/game_start.py
# Module: New Game Flow & Prospect Generation
# Lines: ~650
#
# Handles the new game experience including camp setup,
# prospect generation, and coach selection.

"""
Cage Dynasty - Game Start System

This module handles the new game flow:
- Camp creation and naming
- Region selection
- Starting prospect generation (9 fighters, 1 per weight class)
- Starting coach selection
- Initial roster building with negotiation

USAGE:
    from systems.game_start import (
        GameStartManager,
        StartingProspect,
        StartingCoach,
        generate_starting_prospects,
        generate_starting_coaches,
    )
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import uuid


# ============================================================================
# CONSTANTS
# ============================================================================

WEIGHT_CLASSES = [
    "Strawweight",
    "Flyweight", 
    "Bantamweight",
    "Featherweight",
    "Lightweight",
    "Welterweight",
    "Middleweight",
    "Light Heavyweight",
    "Heavyweight",
]

REGIONS = {
    "Americas": {
        "countries": ["United States", "Brazil", "Mexico", "Canada", "Argentina", "Colombia"],
        "weights": [0.35, 0.30, 0.15, 0.10, 0.05, 0.05],
    },
    "Europe": {
        "countries": ["Russia", "United Kingdom", "Ireland", "Poland", "France", "Germany", "Netherlands", "Sweden"],
        "weights": [0.25, 0.20, 0.15, 0.10, 0.10, 0.08, 0.07, 0.05],
    },
    "Asia-Pacific": {
        "countries": ["Japan", "China", "South Korea", "Australia", "Philippines", "Thailand", "Kazakhstan"],
        "weights": [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05],
    },
}

FIGHTING_STYLES = [
    "Orthodox Boxer",
    "Muay Thai",
    "Wrestler",
    "BJJ Specialist",
    "Kickboxer",
    "Sambo",
    "Karate",
    "Brawler",
    "Pressure Fighter",
    "Counter Striker",
    "Ground & Pound",
    "Submission Artist",
]

# First names by region
FIRST_NAMES = {
    "Americas": {
        "male": ["Marcus", "James", "Carlos", "Diego", "Miguel", "Antonio", "Luis", "David", "Michael", "Brandon", "Tyler", "Jake", "Ryan", "Alex", "Chris"],
        "female": ["Maria", "Jessica", "Sarah", "Amanda", "Sofia", "Isabella", "Valentina", "Camila", "Ana", "Gabriela"],
    },
    "Europe": {
        "male": ["Ivan", "Dmitri", "Sergei", "Conor", "Sean", "Paddy", "Kamil", "Mateusz", "Pierre", "Hans", "Lars", "Erik", "Aleksander", "Nikita", "Viktor"],
        "female": ["Olga", "Natasha", "Katya", "Sinead", "Aoife", "Agnieszka", "Marie", "Ingrid", "Helga", "Svetlana"],
    },
    "Asia-Pacific": {
        "male": ["Kenji", "Takeshi", "Hiroshi", "Wei", "Jun", "Min-Jun", "Sung", "Tao", "Raj", "Arjun", "Batu", "Timur", "Danilo", "Manny", "Mark"],
        "female": ["Yuki", "Sakura", "Mei", "Li", "Soo-Min", "Hana", "Priya", "Aiko", "Rina", "Chie"],
    },
}

LAST_NAMES = {
    "United States": ["Johnson", "Williams", "Smith", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin"],
    "Brazil": ["Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Ferreira", "Almeida", "Ribeiro", "Carvalho", "Gomes", "Martins", "Rocha", "Barbosa"],
    "Mexico": ["Garcia", "Rodriguez", "Martinez", "Lopez", "Hernandez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Reyes"],
    "Canada": ["Smith", "Brown", "Wilson", "Thompson", "Martin", "Anderson", "Taylor", "Campbell", "Stewart", "MacDonald"],
    "Russia": ["Petrov", "Ivanov", "Volkov", "Popov", "Kuznetsov", "Sokolov", "Morozov", "Kozlov", "Lebedev", "Smirnov", "Fedorov", "Zaitsev", "Orlov", "Belov", "Kovalev"],
    "United Kingdom": ["Smith", "Jones", "Williams", "Brown", "Taylor", "Davies", "Wilson", "Evans", "Thomas", "Roberts", "Walker", "Wright", "Robinson", "Thompson", "White"],
    "Ireland": ["Murphy", "Kelly", "O'Brien", "Ryan", "O'Sullivan", "Walsh", "O'Connor", "Byrne", "O'Neill", "Doyle", "McCarthy", "Gallagher", "Doherty", "Kennedy", "Lynch"],
    "Japan": ["Tanaka", "Suzuki", "Yamamoto", "Watanabe", "Takahashi", "Kobayashi", "Nakamura", "Saito", "Kato", "Yoshida", "Matsumoto", "Inoue", "Kimura", "Hayashi", "Shimizu"],
    "China": ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou", "Xu", "Sun", "Ma", "Zhu", "Hu"],
    "South Korea": ["Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon", "Jang", "Lim", "Han", "Shin", "Seo", "Kwon", "Ko"],
    "Australia": ["Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Johnson", "White", "Martin", "Anderson", "Thompson", "Walker", "Harris", "Lewis", "Robinson"],
    "Poland": ["Kowalski", "Nowak", "Wisniewski", "Wojcik", "Kowalczyk", "Kaminski", "Lewandowski", "Zielinski", "Szymanski", "Wozniak"],
    "France": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau"],
    "Germany": ["Muller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann"],
    "Netherlands": ["De Jong", "Jansen", "De Vries", "Van den Berg", "Van Dijk", "Bakker", "Janssen", "Visser", "Smit", "Meijer"],
    "Sweden": ["Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson", "Svensson", "Gustafsson"],
    "Philippines": ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza", "Torres", "Ramos", "Dela Cruz"],
    "Thailand": ["Saengthong", "Srisuk", "Jaidee", "Wongsawat", "Thongdee", "Prasert", "Chaiyasit", "Suwannapong", "Kittisak", "Panyawong"],
    "Kazakhstan": ["Nursultan", "Akhmetov", "Omarov", "Sultanov", "Rakhimov", "Bekzhan", "Sarsenbayev", "Tulegenov", "Abilov", "Zhaksylyk"],
    "Argentina": ["Gonzalez", "Rodriguez", "Fernandez", "Lopez", "Martinez", "Garcia", "Perez", "Sanchez", "Romero", "Diaz"],
    "Colombia": ["Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Hernandez", "Sanchez", "Ramirez", "Torres", "Flores"],
}

# Potential grades and their ceiling ranges
POTENTIAL_GRADES = {
    "Elite": (85, 95),      # Future champion material
    "High": (78, 87),       # Contender potential
    "Average": (70, 80),    # Solid roster fighter
    "Limited": (65, 74),    # Journeyman ceiling
}

# Base demand ranges by potential (signing_bonus, base_purse, win_bonus)
# Contract demands: (sign_min, sign_max, purse_min, purse_max, win_min, win_max)
# Signing bonus is the upfront cost - purse/win are per-fight (not included in estimated_cost)
PROSPECT_DEMANDS = {
    "Elite": (18_000, 25_000, 10_000, 15_000, 5_000, 8_000),
    "High": (12_000, 18_000, 8_000, 12_000, 4_000, 6_000),
    "Average": (8_000, 14_000, 6_000, 10_000, 3_000, 5_000),
    "Limited": (5_000, 10_000, 5_000, 8_000, 2_000, 4_000),
}

# Coach specialties (all 6 from coaches.py)
COACH_SPECIALTIES = ["Striking", "Wrestling", "BJJ", "Conditioning", "Strength", "Cornering"]

COACH_TRAITS = {
    # Positive Training Traits
    "Motivator": "Excellent at building confidence and mental game",
    "Technical Genius": "Focuses on precise technique over raw power",
    "Diamond Polisher": "Exceptional at developing young prospects",
    "Veteran's Touch": "Knows how to maintain aging fighters",
    "Iron Sharpener": "Camp sparring produces better results",
    "Calm Corner": "Improves composure and between-round recovery",
    "Eye for Talent": "Better at scouting and evaluating fighters",
    "Taskmaster": "Intense training (+15%) but can hurt morale",
    
    # Personality Traits
    "Disciplinarian": "Works well with disciplined fighters",
    "Player's Coach": "Boosts morale but slightly less effective training",
    "Intense": "High-energy training style, fast results",
    "Analytical": "Excellent game planning, methodical approach",
    "Old School": "Traditional methods, proven conditioning results",
    "Modern Methods": "Cutting-edge techniques for young fighters",
    "Patient": "Good with fighters who need fundamentals",
    "Supportive": "Creates positive training environment",
}

# For backwards compatibility
COACH_PERSONALITIES = [(k, v) for k, v in COACH_TRAITS.items()]


def get_coach_trait_description(trait: str) -> str:
    """Get description for a coach trait."""
    return COACH_TRAITS.get(trait, "Unknown trait")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class StartingProspect:
    """A prospect available for signing at game start (17 attributes)."""
    prospect_id: str
    name: str
    nickname: str = ""
    
    # Bio
    age: int = 22
    country: str = "United States"
    region: str = "Americas"
    weight_class: str = "Lightweight"
    fighting_style: str = "Orthodox Boxer"
    
    # Ratings
    overall_rating: int = 65
    potential_grade: str = "Average"
    potential_ceiling: int = 75
    
    # Physical Attributes (5)
    strength: int = 60      # Power behind strikes, clinch control
    speed: int = 60         # Hand speed, movement, reaction time
    cardio: int = 60        # Stamina, gas tank
    chin: int = 60          # Ability to absorb damage
    recovery: int = 60      # Between-round recovery, shaking off being hurt
    
    # Striking Attributes (4)
    boxing: int = 60            # Punching technique, combinations
    kicks: int = 55             # Kicking technique
    clinch_striking: int = 55   # Knees, elbows, dirty boxing
    striking_defense: int = 55  # Head movement, blocking
    
    # Grappling Attributes (5)
    takedowns: int = 55         # Ability to bring fight to ground
    takedown_defense: int = 55  # Sprawl, cage defense
    top_control: int = 55       # Holding position, GnP, preventing sweeps
    submissions: int = 55       # Finishing ability - chokes/locks
    guard: int = 55             # Sweeps, guard retention, getting back up
    
    # Mental Attributes (3)
    heart: int = 65         # Willingness to fight through adversity
    fight_iq: int = 55      # In-fight adjustments, strategy
    composure: int = 60     # Performance under pressure
    
    # Traits
    traits: List[str] = field(default_factory=list)
    
    # Contract demands
    estimated_cost: int = 35000
    signing_bonus_range: Tuple[int, int] = (25000, 40000)
    base_purse_range: Tuple[int, int] = (10000, 15000)
    win_bonus_range: Tuple[int, int] = (5000, 8000)
    
    def to_fighter_dict(self) -> Dict[str, Any]:
        """Convert to fighter data dict for game state."""
        return {
            "fighter_id": self.prospect_id,
            "name": self.name,
            "nickname": self.nickname,
            "age": self.age,
            "country": self.country,
            "weight_class": self.weight_class,
            "fighting_style": self.fighting_style,
            "overall_rating": self.overall_rating,
            "potential_ceiling": self.potential_ceiling,
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
            # Other
            "traits": self.traits,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "ko_wins": 0,
            "sub_wins": 0,
            "is_champion": False,
            "is_active": True,
            "camp_id": None,
        }


@dataclass
class StartingCoach:
    """A coach available for hiring at game start."""
    coach_id: str
    name: str
    
    # Specialty
    specialty: str = "Boxing"  # Boxing, Wrestling, BJJ, Conditioning
    skill_level: int = 70  # 60-80 for starting coaches
    
    # Traits (1-2 traits per coach)
    traits: List[str] = field(default_factory=list)
    
    # Experience
    years_experience: int = 5
    
    # Contract terms (for after free period)
    weekly_salary: int = 1500
    annual_cost: int = 78000
    
    # Training bonuses
    training_bonus: float = 0.10  # +10% to specialty training
    fight_bonus: float = 0.05    # +5% to related fight stats
    
    @property
    def traits_display(self) -> str:
        """Get formatted traits string."""
        if not self.traits:
            return "None"
        return ", ".join(self.traits)
    
    @property
    def traits_with_descriptions(self) -> List[Tuple[str, str]]:
        """Get traits with their descriptions."""
        return [(t, get_coach_trait_description(t)) for t in self.traits]
    
    def get_bonus_description(self) -> str:
        """Get description of what this coach provides."""
        specialty_map = {
            "Striking": ("Boxing/Kicks/Defense", "striking accuracy"),
            "Boxing": ("Boxing/Striking", "striking accuracy"),  # Legacy alias
            "Wrestling": ("Wrestling/TD Defense", "takedown success"),
            "BJJ": ("BJJ/Submissions", "submission rate"),
            "Conditioning": ("Cardio/Recovery", "late-round performance"),
            "Strength": ("Strength/Speed/Power", "knockout power"),
            "Cornering": ("Fight IQ/Composure", "in-fight adjustments"),
        }
        train_area, fight_area = specialty_map.get(self.specialty, ("General", "overall"))
        
        train_pct = int(self.training_bonus * 100)
        fight_pct = int(self.fight_bonus * 100)
        
        return f"+{train_pct}% to {train_area} development, +{fight_pct}% {fight_area} in fights"


@dataclass
class CoachContract:
    """Contract for a coach."""
    contract_id: str
    coach_id: str
    coach_name: str
    camp_id: str
    specialty: str
    
    # Terms
    weekly_salary: int = 1500
    total_weeks: int = 52
    signing_bonus: int = 0
    
    # Progress
    weeks_completed: int = 0
    
    # Status
    is_active: bool = True
    is_free: bool = False  # True for starting free coach
    
    @property
    def weeks_remaining(self) -> int:
        return max(0, self.total_weeks - self.weeks_completed)
    
    @property
    def is_expiring(self) -> bool:
        return self.weeks_remaining <= 4
    
    @property
    def is_expired(self) -> bool:
        return self.weeks_remaining == 0
    
    @property
    def total_value(self) -> int:
        return self.signing_bonus + (self.weekly_salary * self.total_weeks)
    
    @property
    def remaining_cost(self) -> int:
        return self.weekly_salary * self.weeks_remaining
    
    def advance_week(self) -> None:
        """Advance contract by one week."""
        self.weeks_completed += 1
        if self.weeks_completed >= self.total_weeks:
            self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "coach_id": self.coach_id,
            "coach_name": self.coach_name,
            "camp_id": self.camp_id,
            "specialty": self.specialty,
            "weekly_salary": self.weekly_salary,
            "total_weeks": self.total_weeks,
            "signing_bonus": self.signing_bonus,
            "weeks_completed": self.weeks_completed,
            "is_active": self.is_active,
            "is_free": self.is_free,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoachContract':
        return cls(
            contract_id=data.get("contract_id", str(uuid.uuid4())[:8]),
            coach_id=data["coach_id"],
            coach_name=data.get("coach_name", "Unknown"),
            camp_id=data["camp_id"],
            specialty=data.get("specialty", "Boxing"),
            weekly_salary=data.get("weekly_salary", 1500),
            total_weeks=data.get("total_weeks", 52),
            signing_bonus=data.get("signing_bonus", 0),
            weeks_completed=data.get("weeks_completed", 0),
            is_active=data.get("is_active", True),
            is_free=data.get("is_free", False),
        )


# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================

def generate_prospect_name(country: str, region: str) -> str:
    """Generate a fighter name based on country."""
    # Get first name from region
    first_names = FIRST_NAMES.get(region, FIRST_NAMES["Americas"])
    # Mostly male for now (can expand)
    first = random.choice(first_names["male"])
    
    # Get last name from country
    last_names = LAST_NAMES.get(country, ["Smith", "Johnson", "Williams"])
    last = random.choice(last_names)
    
    return f"{first} {last}"


def generate_prospect_attributes(
    overall: int,
    fighting_style: str,
) -> Dict[str, int]:
    """Generate attributes based on overall rating and style (17 total)."""
    # Base variance around overall
    def vary(base: int, variance: int = 8) -> int:
        return max(40, min(95, base + random.randint(-variance, variance)))
    
    # Start with base attributes (17 total)
    attrs = {
        # Physical (5)
        "strength": vary(overall),
        "speed": vary(overall),
        "cardio": vary(overall),
        "chin": vary(overall),
        "recovery": vary(overall),
        # Striking (4)
        "boxing": vary(overall - 3),
        "kicks": vary(overall - 5),
        "clinch_striking": vary(overall - 5),
        "striking_defense": vary(overall - 3),
        # Grappling (5)
        "takedowns": vary(overall - 5),
        "takedown_defense": vary(overall - 3),
        "top_control": vary(overall - 5),
        "submissions": vary(overall - 5),
        "guard": vary(overall - 5),
        # Mental (3)
        "heart": vary(overall + 2),
        "fight_iq": vary(overall - 5),
        "composure": vary(overall),
    }
    
    # Style bonuses - each style has distinct strengths
    style_bonuses = {
        "Orthodox Boxer": {
            "boxing": 12, "striking_defense": 8, "speed": 5
        },
        "Muay Thai": {
            "kicks": 12, "clinch_striking": 10, "striking_defense": 5
        },
        "Wrestler": {
            "takedowns": 15, "top_control": 12, "takedown_defense": 8
        },
        "BJJ Specialist": {
            "submissions": 15, "guard": 12, "takedown_defense": 5
        },
        "Kickboxer": {
            "kicks": 10, "boxing": 8, "striking_defense": 5
        },
        "Sambo": {
            "takedowns": 10, "submissions": 8, "top_control": 8
        },
        "Karate": {
            "kicks": 8, "speed": 10, "striking_defense": 8
        },
        "Brawler": {
            "strength": 10, "chin": 10, "heart": 10
        },
        "Pressure Fighter": {
            "cardio": 12, "heart": 10, "top_control": 5
        },
        "Counter Striker": {
            "striking_defense": 12, "fight_iq": 10, "composure": 5
        },
        "Ground & Pound": {
            "takedowns": 10, "top_control": 12, "strength": 8
        },
        "Submission Artist": {
            "submissions": 15, "guard": 10, "composure": 5
        },
    }
    
    bonuses = style_bonuses.get(fighting_style, {})
    for attr, bonus in bonuses.items():
        attrs[attr] = min(95, attrs[attr] + bonus)
    
    return attrs


def generate_starting_prospects(
    player_region: str,
    num_prospects: int = 9,
) -> List[StartingProspect]:
    """
    Generate starting prospects for new game.
    
    Args:
        player_region: Player's selected region
        num_prospects: Number to generate (default 9, one per weight class)
    
    Returns:
        List of StartingProspect objects
    """
    prospects = []
    
    # Distribute potential grades: 1 Elite, 3 High, 3 Average, 2 Limited
    potential_distribution = ["Elite"] + ["High"] * 3 + ["Average"] * 3 + ["Limited"] * 2
    random.shuffle(potential_distribution)
    
    for i, weight_class in enumerate(WEIGHT_CLASSES[:num_prospects]):
        # Get potential grade for this prospect
        potential_grade = potential_distribution[i] if i < len(potential_distribution) else "Average"
        
        # Determine ceiling based on potential
        ceiling_min, ceiling_max = POTENTIAL_GRADES[potential_grade]
        potential_ceiling = random.randint(ceiling_min, ceiling_max)
        
        # Current overall is lower than ceiling (room to grow)
        growth_room = random.randint(8, 18)
        overall = max(60, potential_ceiling - growth_room)
        
        # Country - 40% chance from player's region
        if random.random() < 0.4:
            region = player_region
        else:
            region = random.choice(list(REGIONS.keys()))
        
        region_data = REGIONS[region]
        country = random.choices(
            region_data["countries"],
            weights=region_data["weights"],
            k=1
        )[0]
        
        # Generate name
        name = generate_prospect_name(country, region)
        
        # Fighting style
        fighting_style = random.choice(FIGHTING_STYLES)
        
        # Age (younger for higher potential)
        if potential_grade == "Elite":
            age = random.randint(20, 23)
        elif potential_grade == "High":
            age = random.randint(21, 24)
        elif potential_grade == "Average":
            age = random.randint(22, 25)
        else:
            age = random.randint(23, 26)
        
        # Generate attributes
        attrs = generate_prospect_attributes(overall, fighting_style)
        
        # Generate traits (1-2 per prospect)
        available_traits = [
            "Knockout Artist", "Submission Ace", "Iron Chin", "Glass Cannon",
            "Cardio Machine", "Fast Starter", "Slow Starter", "Gym Rat",
            "Pressure Fighter", "Counter Striker", "Durable", "Veteran Savvy",
            "Killer Instinct", "Southpaw",
        ]
        num_traits = random.randint(1, 2)
        traits = random.sample(available_traits, num_traits)
        
        # Contract demands based on potential
        demands = PROSPECT_DEMANDS[potential_grade]
        sign_min, sign_max = demands[0], demands[1]
        purse_min, purse_max = demands[2], demands[3]
        win_min, win_max = demands[4], demands[5]
        
        # Estimated cost is just the signing bonus (purse/win paid per fight later)
        estimated_cost = (sign_min + sign_max) // 2
        
        prospect = StartingProspect(
            prospect_id=str(uuid.uuid4())[:12],
            name=name,
            age=age,
            country=country,
            region=region,
            weight_class=weight_class,
            fighting_style=fighting_style,
            overall_rating=overall,
            potential_grade=potential_grade,
            potential_ceiling=potential_ceiling,
            # Physical (5)
            strength=attrs["strength"],
            speed=attrs["speed"],
            cardio=attrs["cardio"],
            chin=attrs["chin"],
            recovery=attrs["recovery"],
            # Striking (4)
            boxing=attrs["boxing"],
            kicks=attrs["kicks"],
            clinch_striking=attrs["clinch_striking"],
            striking_defense=attrs["striking_defense"],
            # Grappling (5)
            takedowns=attrs["takedowns"],
            takedown_defense=attrs["takedown_defense"],
            top_control=attrs["top_control"],
            submissions=attrs["submissions"],
            guard=attrs["guard"],
            # Mental (3)
            heart=attrs["heart"],
            fight_iq=attrs["fight_iq"],
            composure=attrs["composure"],
            # Other
            traits=traits,
            estimated_cost=estimated_cost,
            signing_bonus_range=(sign_min, sign_max),
            base_purse_range=(purse_min, purse_max),
            win_bonus_range=(win_min, win_max),
        )
        
        prospects.append(prospect)
    
    return prospects


def generate_starting_coaches(num_coaches: int = 10) -> List[StartingCoach]:
    """
    Generate starting coaches for selection.
    
    Creates a diverse pool of coaches with weighted random specialties.
    Player picks from more options for varied starts.
    
    Args:
        num_coaches: Number of coaches to generate (default 10)
    
    Returns:
        List of StartingCoach objects
    """
    coaches = []
    
    # Weighted specialties - Striking/Wrestling/BJJ more common
    specialty_weights = {
        "Striking": 25,
        "Wrestling": 20,
        "BJJ": 20,
        "Conditioning": 15,
        "Strength": 10,
        "Cornering": 10,
    }
    specialties = list(specialty_weights.keys())
    weights = list(specialty_weights.values())
    
    # Track used names to avoid duplicates
    used_names = set()
    
    for i in range(num_coaches):
        # Random weighted specialty
        specialty = random.choices(specialties, weights=weights, k=1)[0]
        
        # Generate unique name
        attempts = 0
        while attempts < 20:
            first = random.choice(FIRST_NAMES["Americas"]["male"])
            last = random.choice(LAST_NAMES["United States"])
            name = f"{first} {last}"
            if name not in used_names:
                used_names.add(name)
                break
            attempts += 1
        
        # Skill level varies more (55-82 for starting coaches)
        # Creates meaningful choice between cheap/weak vs expensive/strong
        skill = random.randint(55, 82)
        
        # Generate traits (1-2 traits per coach, 40% chance for 2)
        available_traits = list(COACH_TRAITS.keys())
        num_traits = 1 if random.random() < 0.6 else 2
        coach_traits = random.sample(available_traits, num_traits)
        
        # Experience based on skill
        years = skill // 10 + random.randint(0, 5)
        
        # Salary based on skill (steeper curve)
        if skill >= 75:
            base_salary = 1500 + (skill - 75) * 100  # $1500-$2200/week for elite
        elif skill >= 65:
            base_salary = 1000 + (skill - 65) * 50   # $1000-$1500/week for good
        else:
            base_salary = 600 + (skill - 55) * 40    # $600-$1000/week for budget
        annual = base_salary * 52
        
        # Training bonuses based on skill
        train_bonus = 0.06 + (skill - 55) * 0.004  # 6-17%
        fight_bonus = 0.02 + (skill - 55) * 0.002  # 2-7%
        
        coach = StartingCoach(
            coach_id=str(uuid.uuid4())[:8],
            name=name,
            specialty=specialty,
            skill_level=skill,
            traits=coach_traits,
            years_experience=years,
            weekly_salary=base_salary,
            annual_cost=annual,
            training_bonus=round(train_bonus, 2),
            fight_bonus=round(fight_bonus, 2),
        )
        
        coaches.append(coach)
    
    # Sort by skill (highest first) for easier viewing
    coaches.sort(key=lambda c: c.skill_level, reverse=True)
    
    return coaches


# ============================================================================
# GAME START MANAGER
# ============================================================================

class GameStartManager:
    """
    Manages the new game flow and initial setup.
    """
    
    def __init__(self):
        self.camp_name: str = ""
        self.camp_region: str = "Americas"
        self.starting_balance: int = 100_000
        self.refresh_cost: int = 10_000
        self.refreshes_used: int = 0
        
        # Generated options
        self.prospects: List[StartingProspect] = []
        self.coaches: List[StartingCoach] = []
        
        # Selected items
        self.signed_prospects: List[StartingProspect] = []
        self.selected_coach: Optional[StartingCoach] = None
        self.current_balance: int = 100_000
    
    def set_camp_info(self, name: str, region: str) -> None:
        """Set camp name and region."""
        self.camp_name = name
        self.camp_region = region
    
    def generate_prospects(self) -> List[StartingProspect]:
        """Generate or regenerate prospects."""
        self.prospects = generate_starting_prospects(self.camp_region)
        return self.prospects
    
    def refresh_prospects(self) -> bool:
        """
        Refresh prospect pool for a cost.
        
        Returns:
            True if refresh successful, False if can't afford
        """
        if self.current_balance < self.refresh_cost:
            return False
        
        self.current_balance -= self.refresh_cost
        self.refreshes_used += 1
        self.generate_prospects()
        return True
    
    def generate_coaches(self) -> List[StartingCoach]:
        """Generate starting coach options."""
        self.coaches = generate_starting_coaches()
        return self.coaches
    
    def select_coach(self, coach: StartingCoach) -> CoachContract:
        """
        Select a starting coach (free for first year).
        
        Args:
            coach: The selected coach
        
        Returns:
            CoachContract for the coach
        """
        self.selected_coach = coach
        
        # Create free 1-year contract
        contract = CoachContract(
            contract_id=str(uuid.uuid4())[:8],
            coach_id=coach.coach_id,
            coach_name=coach.name,
            camp_id="",  # Will be set when camp is created
            specialty=coach.specialty,
            weekly_salary=coach.weekly_salary,
            total_weeks=52,
            signing_bonus=0,
            is_free=True,
        )
        
        return contract
    
    def sign_prospect(self, prospect: StartingProspect, signing_cost: int) -> bool:
        """
        Sign a prospect.
        
        Args:
            prospect: The prospect to sign
            signing_cost: Total signing bonus cost
        
        Returns:
            True if signed successfully
        """
        if signing_cost > self.current_balance:
            return False
        
        self.current_balance -= signing_cost
        self.signed_prospects.append(prospect)
        
        # Remove from available prospects
        self.prospects = [p for p in self.prospects if p.prospect_id != prospect.prospect_id]
        
        return True
    
    def get_roster_count(self) -> int:
        """Get number of signed prospects."""
        return len(self.signed_prospects)
    
    def can_sign_more(self) -> bool:
        """Check if can sign more prospects (max 5 for GARAGE tier)."""
        return len(self.signed_prospects) < 5
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of game start selections."""
        return {
            "camp_name": self.camp_name,
            "camp_region": self.camp_region,
            "starting_balance": self.starting_balance,
            "final_balance": self.current_balance,
            "refreshes_used": self.refreshes_used,
            "coach": self.selected_coach.name if self.selected_coach else None,
            "coach_specialty": self.selected_coach.specialty if self.selected_coach else None,
            "roster_count": len(self.signed_prospects),
            "roster": [p.name for p in self.signed_prospects],
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export for potential saving."""
        return self.get_summary()


# ============================================================================
# COACH MANAGEMENT
# ============================================================================

class CoachManager:
    """
    Manages coach contracts and hiring.
    """
    
    def __init__(self):
        self.contracts: Dict[str, CoachContract] = {}  # contract_id -> contract
        self.coach_contracts: Dict[str, str] = {}  # coach_id -> contract_id
        self.available_coaches: List[StartingCoach] = []  # Free agent coaches
        self.pending_renewals: List[str] = []  # contract_ids needing renewal decision
    
    def add_contract(self, contract: CoachContract) -> None:
        """Add a coach contract."""
        self.contracts[contract.contract_id] = contract
        self.coach_contracts[contract.coach_id] = contract.contract_id
    
    def get_camp_coaches(self, camp_id: str) -> List[CoachContract]:
        """Get all coach contracts for a camp."""
        return [c for c in self.contracts.values() 
                if c.camp_id == camp_id and c.is_active]
    
    def get_expiring_contracts(self, camp_id: str) -> List[CoachContract]:
        """Get expiring coach contracts for a camp."""
        return [c for c in self.get_camp_coaches(camp_id) if c.is_expiring]
    
    def get_pending_renewals(self, camp_id: str) -> List[CoachContract]:
        """Get contracts that need renewal decisions."""
        return [self.contracts[cid] for cid in self.pending_renewals 
                if cid in self.contracts and self.contracts[cid].camp_id == camp_id]
    
    def advance_week(self, camp_id: str) -> List[CoachContract]:
        """
        Advance all coach contracts by one week.
        
        Returns:
            List of contracts that expired this week
        """
        expired = []
        newly_expiring = []
        
        for contract in self.get_camp_coaches(camp_id):
            was_active = contract.is_active
            was_expiring = contract.is_expiring
            
            contract.advance_week()
            
            # Check if just became expiring (4 weeks warning)
            if not was_expiring and contract.is_expiring and contract.is_active:
                newly_expiring.append(contract)
            
            if was_active and not contract.is_active:
                expired.append(contract)
                # Remove from pending renewals if there
                if contract.contract_id in self.pending_renewals:
                    self.pending_renewals.remove(contract.contract_id)
        
        # Add newly expiring to pending renewals
        for contract in newly_expiring:
            if contract.contract_id not in self.pending_renewals:
                self.pending_renewals.append(contract.contract_id)
        
        return expired
    
    def calculate_renewal_demands(
        self,
        contract: CoachContract,
        coach_quality: int = 2,
        coach_reputation: int = 50,
        wins_as_coach: int = 0,
        titles_won: int = 0,
    ) -> Dict[str, Any]:
        """
        Calculate what a coach will demand for contract renewal.
        
        Args:
            contract: Current contract
            coach_quality: Coach's star rating (1-5)
            coach_reputation: Coach's reputation (0-100)
            wins_as_coach: Total wins as cornerman
            titles_won: Championships won
            
        Returns:
            Dict with salary demands, duration options, mood, etc.
        """
        # Base salary by quality
        base_salaries = {
            1: 800,
            2: 1500,
            3: 3000,
            4: 5000,
            5: 8000,
        }
        base_salary = base_salaries.get(coach_quality, 1500)
        
        # Modifiers
        rep_modifier = 1.0 + (coach_reputation - 50) * 0.01  # +/- 50%
        success_modifier = 1.0 + (wins_as_coach * 0.002) + (titles_won * 0.05)  # Up to +50%
        
        # Did they like their time? (based on camp success)
        mood = "neutral"
        mood_modifier = 1.0
        
        if titles_won >= 2:
            mood = "happy"
            mood_modifier = 0.95
        elif titles_won >= 1 or wins_as_coach >= 20:
            mood = "satisfied"
            mood_modifier = 0.98
        elif wins_as_coach < 5:
            mood = "disappointed"
            mood_modifier = 1.1
        
        # Was contract free? They'll want real money now
        if contract.is_free:
            free_multiplier = 1.2  # 20% premium for "finally getting paid"
        else:
            free_multiplier = 1.0
        
        # Calculate demanded salary
        demanded_salary = int(
            base_salary * 
            rep_modifier * 
            success_modifier * 
            mood_modifier * 
            free_multiplier
        )
        
        # Round to nearest 100
        demanded_salary = (demanded_salary // 100) * 100
        
        # Minimum/maximum ranges
        min_acceptable = int(demanded_salary * 0.85)  # Will accept 15% less
        max_demand = int(demanded_salary * 1.15)  # Might ask for 15% more
        
        # Duration options (years)
        durations = [
            {"years": 1, "weeks": 52, "discount": 0},
            {"years": 2, "weeks": 104, "discount": 5},  # 5% discount
            {"years": 3, "weeks": 156, "discount": 10},  # 10% discount
        ]
        
        # Signing bonus expectation
        signing_bonus = demanded_salary * 4 if coach_quality >= 3 else demanded_salary * 2
        
        return {
            "base_salary": base_salary,
            "demanded_salary": demanded_salary,
            "min_acceptable": min_acceptable,
            "max_demand": max_demand,
            "mood": mood,
            "mood_description": self._get_mood_description(mood),
            "durations": durations,
            "signing_bonus": signing_bonus,
            "is_from_free": contract.is_free,
            "previous_salary": contract.weekly_salary if not contract.is_free else 0,
        }
    
    def _get_mood_description(self, mood: str) -> str:
        """Get description of coach's negotiation mood."""
        descriptions = {
            "happy": "thrilled with camp success, willing to negotiate",
            "satisfied": "content with experience, open to fair deal",
            "neutral": "businesslike, focused on fair market value",
            "disappointed": "underwhelmed by results, may demand premium",
            "frustrated": "unhappy, likely to walk unless overpaid",
        }
        return descriptions.get(mood, "ready to negotiate")
    
    def evaluate_offer(
        self,
        contract: CoachContract,
        demands: Dict[str, Any],
        offered_salary: int,
        offered_weeks: int,
        offered_bonus: int,
    ) -> Dict[str, Any]:
        """
        Evaluate a renewal offer and determine acceptance probability.
        
        Returns:
            Dict with acceptance probability, coach reaction, etc.
        """
        demanded = demands["demanded_salary"]
        min_acceptable = demands["min_acceptable"]
        
        # Salary evaluation
        if offered_salary >= demanded:
            salary_score = 100 + (offered_salary - demanded) / demanded * 20
        elif offered_salary >= min_acceptable:
            salary_score = 50 + (offered_salary - min_acceptable) / (demanded - min_acceptable) * 50
        else:
            salary_score = max(0, 50 * (offered_salary / min_acceptable))
        
        # Duration evaluation (longer = slight bonus)
        duration_bonus = 0
        for d in demands["durations"]:
            if d["weeks"] == offered_weeks:
                duration_bonus = d["discount"]
                break
        
        # Bonus evaluation
        expected_bonus = demands["signing_bonus"]
        if offered_bonus >= expected_bonus:
            bonus_score = 100
        else:
            bonus_score = 50 + (offered_bonus / expected_bonus) * 50 if expected_bonus > 0 else 100
        
        # Combined score
        total_score = (salary_score * 0.6) + (bonus_score * 0.2) + (duration_bonus * 2)
        
        # Convert to acceptance probability
        if total_score >= 100:
            accept_prob = min(98, 75 + (total_score - 100) * 0.5)
        elif total_score >= 70:
            accept_prob = 40 + (total_score - 70) * 1.1
        else:
            accept_prob = max(5, total_score * 0.6)
        
        # Mood modifier
        mood_mods = {"happy": 10, "satisfied": 5, "neutral": 0, "disappointed": -10, "frustrated": -20}
        accept_prob += mood_mods.get(demands["mood"], 0)
        
        accept_prob = max(5, min(98, accept_prob))
        
        # Reaction text
        if accept_prob >= 80:
            reaction = "looks very interested"
        elif accept_prob >= 60:
            reaction = "seems receptive"
        elif accept_prob >= 40:
            reaction = "is considering it"
        elif accept_prob >= 25:
            reaction = "looks hesitant"
        else:
            reaction = "seems unlikely to accept"
        
        return {
            "acceptance_probability": int(accept_prob),
            "salary_score": int(salary_score),
            "bonus_score": int(bonus_score),
            "duration_bonus": duration_bonus,
            "reaction": reaction,
            "is_lowball": offered_salary < min_acceptable,
            "is_generous": offered_salary > demanded * 1.1,
        }
    
    def attempt_renewal(
        self,
        contract: CoachContract,
        demands: Dict[str, Any],
        offered_salary: int,
        offered_weeks: int,
        offered_bonus: int,
    ) -> Tuple[bool, str, Optional[CoachContract]]:
        """
        Attempt to renew a coach contract with offered terms.
        
        Returns:
            Tuple of (accepted, message, new_contract or None)
        """
        evaluation = self.evaluate_offer(
            contract, demands, offered_salary, offered_weeks, offered_bonus
        )
        
        # Roll for acceptance
        roll = random.randint(1, 100)
        accepted = roll <= evaluation["acceptance_probability"]
        
        if accepted:
            # Create new contract
            new_contract = CoachContract(
                contract_id=str(uuid.uuid4())[:8],
                coach_id=contract.coach_id,
                coach_name=contract.coach_name,
                camp_id=contract.camp_id,
                specialty=contract.specialty,
                weekly_salary=offered_salary,
                total_weeks=offered_weeks,
                signing_bonus=offered_bonus,
                weeks_completed=0,
                is_active=True,
                is_free=False,
            )
            
            # Deactivate old contract
            contract.is_active = False
            if contract.contract_id in self.pending_renewals:
                self.pending_renewals.remove(contract.contract_id)
            
            # Add new contract
            self.add_contract(new_contract)
            
            message = f"{contract.coach_name} accepts the offer and signs a new {offered_weeks // 52}-year deal!"
            return True, message, new_contract
        else:
            # Rejected
            if evaluation["is_lowball"]:
                message = f"{contract.coach_name} is insulted by the lowball offer and refuses."
            elif evaluation["acceptance_probability"] < 30:
                message = f"{contract.coach_name} declines, saying the terms don't work for them."
            else:
                message = f"{contract.coach_name} thinks about it but ultimately decides to decline."
            
            return False, message, None
    
    def let_contract_expire(self, contract: CoachContract) -> None:
        """Mark contract as expired and remove from pending renewals."""
        contract.is_active = False
        if contract.contract_id in self.pending_renewals:
            self.pending_renewals.remove(contract.contract_id)
    
    def release_coach(self, coach_id: str) -> Optional[CoachContract]:
        """Release a coach from their contract."""
        contract_id = self.coach_contracts.get(coach_id)
        if not contract_id:
            return None
        
        contract = self.contracts.get(contract_id)
        if contract:
            contract.is_active = False
            if contract_id in self.pending_renewals:
                self.pending_renewals.remove(contract_id)
            del self.coach_contracts[coach_id]
        
        return contract
    
    def to_dict(self) -> Dict[str, Any]:
        """Export for saving."""
        return {
            "contracts": {cid: c.to_dict() for cid, c in self.contracts.items()},
            "coach_contracts": self.coach_contracts.copy(),
            "pending_renewals": self.pending_renewals.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CoachManager':
        """Create from saved data."""
        manager = cls()
        
        for cid, cdata in data.get("contracts", {}).items():
            contract = CoachContract.from_dict(cdata)
            manager.contracts[cid] = contract
        
        manager.coach_contracts = data.get("coach_contracts", {}).copy()
        manager.pending_renewals = data.get("pending_renewals", []).copy()
        
        return manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "StartingProspect",
    "StartingCoach",
    "CoachContract",
    
    # Generation functions
    "generate_starting_prospects",
    "generate_starting_coaches",
    "generate_prospect_name",
    "generate_prospect_attributes",
    
    # Manager classes
    "GameStartManager",
    "CoachManager",
    
    # Constants
    "WEIGHT_CLASSES",
    "REGIONS",
    "FIGHTING_STYLES",
    "POTENTIAL_GRADES",
    "COACH_SPECIALTIES",
]
