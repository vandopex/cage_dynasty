# systems/amateur.py
# Amateur Tournament System
# Lines: ~1150
#
# Complete amateur circuit with regional tournaments, rankings,
# and pathway to professional careers.

"""
Cage Dynasty - Amateur Tournament System

This module manages the amateur MMA circuit:
- 4 Regions: West, East, South, North
- 8 Tournaments per region per year (~every 6 weeks)
- 16-fighter brackets per weight class
- Regional rankings with points system
- National Championship (annual)
- Pro eligibility and signing pathway

POINTS SYSTEM:
    Champion:        10 points
    Finalist:         6 points
    Semifinalist:     3 points
    Quarterfinalist:  1 point
    Finish bonus:    +1 point
    FOTN bonus:      +1 point

PRO ELIGIBILITY (minimum 4 fights + age 18+):
    - Win a regional tournament
    - 8+ fights with 65%+ win rate
    - Top 5 in regional rankings
    - National Championship participant
    - Prodigy Rule: Rating 72+ (immediate)

USAGE:
    from systems.amateur import (
        AmateurSystem,
        AmateurFighter,
        Tournament,
        RegionalRankings,
    )
    
    # Initialize system
    amateur_system = AmateurSystem()
    amateur_system.initialize_pools()
    
    # Create and run tournament
    tournament = amateur_system.create_tournament("West", "Lightweight", week=8)
    results = amateur_system.simulate_tournament(tournament)
    
    # Check eligibility
    eligible = amateur_system.get_eligible_amateurs("Lightweight")
    
    # Sign amateur
    pro_fighter = amateur_system.sign_amateur(amateur_id, camp_id)
"""

import random
import uuid
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CONSTANTS
# ============================================================================

# World Regions for amateur circuit
REGIONS = ["Americas", "Europe", "Asia", "Pacific"]

# Named regional circuits — used for tournament naming so the amateur
# portal reads as a real promotion stack (city + suffix) rather than
# "Y1 Americas Regional #3". city_idx and suffix_idx cycle in
# create_tournament so every city pairs with every suffix before any
# combination repeats.
REGION_CIRCUITS = {
    "Americas": {
        "circuit": "Pan-American Combat League",
        "abbr": "PACL",
        "cities": [
            "Las Vegas", "São Paulo", "Toronto",
            "Mexico City", "Miami", "New York",
            "Los Angeles", "Chicago", "Montreal", "Houston",
        ],
    },
    "Europe": {
        "circuit": "European Fighting Championship",
        "abbr": "EFC",
        "cities": [
            "Moscow", "London", "Warsaw",
            "Amsterdam", "Dublin", "Stockholm",
            "Berlin", "Paris", "Kyiv", "Madrid",
        ],
    },
    "Asia": {
        "circuit": "Asian Combat Series",
        "abbr": "ACS",
        "cities": [
            "Tokyo", "Seoul", "Bangkok",
            "Almaty", "Osaka", "Tashkent",
            "Shanghai", "Singapore", "Baku", "Manila",
        ],
    },
    "Pacific": {
        "circuit": "Pacific Rim Championship",
        "abbr": "PRC",
        "cities": [
            "Sydney", "Lagos", "Auckland",
            "Cape Town", "Melbourne", "Nairobi",
            "Perth", "Johannesburg", "Brisbane", "Wellington",
        ],
    },
}

TOURNAMENT_SUFFIXES = [
    "Open", "Invitational", "Classic",
    "Grand Prix", "Series", "Championship",
]

WEIGHT_CLASSES = [
    "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
    "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight",
    "Heavyweight"
]

# Nationality to tournament region mapping
NATIONALITY_TO_REGION = {
    # Americas
    "United States": "Americas",
    "USA": "Americas",
    "Brazil": "Americas",
    "Canada": "Americas",
    "Mexico": "Americas",
    "Argentina": "Americas",
    
    # Europe
    "Russia": "Europe",
    "United Kingdom": "Europe",
    "UK": "Europe",
    "Ireland": "Europe",
    "Poland": "Europe",
    "Netherlands": "Europe",
    "Sweden": "Europe",
    "France": "Europe",
    "Germany": "Europe",
    "Ukraine": "Europe",
    "Italy": "Europe",
    "Spain": "Europe",
    
    # Asia
    "Japan": "Asia",
    "South Korea": "Asia",
    "China": "Asia",
    "Thailand": "Asia",
    "Uzbekistan": "Asia",
    "Kazakhstan": "Asia",
    
    # Pacific (includes Africa for roster balance)
    "Australia": "Pacific",
    "New Zealand": "Pacific",
    "Nigeria": "Pacific",
    "South Africa": "Pacific",
}

# Nationalities per region (for generation)
REGION_NATIONALITIES = {
    "Americas": ["United States", "Brazil", "Canada", "Mexico", "Argentina"],
    "Europe": ["Russia", "United Kingdom", "Ireland", "Poland", "Netherlands", 
               "Sweden", "France", "Germany", "Ukraine"],
    "Asia": ["Japan", "South Korea", "China", "Thailand", "Uzbekistan", "Kazakhstan"],
    "Pacific": ["Australia", "New Zealand", "Nigeria", "South Africa"],
}

# Regional style tendencies (from generator.py)
NATIONALITY_STYLE_TENDENCIES = {
    # Americas
    "United States": {"style": "mma_hybrid", "mods": {"wrestling": 2, "boxing": 2}},
    "Brazil": {"style": "bjj_specialist", "mods": {"bjj": 5, "composure": 2}},
    "Canada": {"style": "mma_hybrid", "mods": {"wrestling": 2, "cardio": 2}},
    "Mexico": {"style": "boxer", "mods": {"boxing": 4, "heart": 2}},
    "Argentina": {"style": "bjj_specialist", "mods": {"bjj": 3, "composure": 2}},
    
    # Europe
    "Russia": {"style": "sambo", "mods": {"wrestling": 4, "strength": 2, "chin": 2}},
    "United Kingdom": {"style": "technical_striker", "mods": {"boxing": 3, "composure": 2}},
    "Ireland": {"style": "technical_striker", "mods": {"boxing": 3, "heart": 2}},
    "Poland": {"style": "kickboxer", "mods": {"kicks": 3, "chin": 2}},
    "Netherlands": {"style": "kickboxer", "mods": {"kicks": 4, "striking_defense": 2}},
    "Sweden": {"style": "mma_hybrid", "mods": {"wrestling": 2, "strength": 2}},
    "France": {"style": "technical_striker", "mods": {"boxing": 2, "composure": 2}},
    "Germany": {"style": "kickboxer", "mods": {"kicks": 2, "strength": 2}},
    "Ukraine": {"style": "sambo", "mods": {"wrestling": 3, "strength": 2}},
    
    # Asia
    "Japan": {"style": "technical", "mods": {"speed": 2, "fight_iq": 3}},
    "South Korea": {"style": "technical", "mods": {"speed": 2, "fight_iq": 2}},
    "China": {"style": "athletic", "mods": {"speed": 2, "cardio": 2}},
    "Thailand": {"style": "muay_thai", "mods": {"kicks": 5, "clinch_striking": 4}},
    "Uzbekistan": {"style": "wrestler", "mods": {"wrestling": 6, "cardio": 2, "heart": 2}},
    "Kazakhstan": {"style": "wrestler", "mods": {"wrestling": 5, "strength": 2}},
    
    # Pacific
    "Australia": {"style": "well_rounded", "mods": {"cardio": 2, "heart": 2}},
    "New Zealand": {"style": "well_rounded", "mods": {"cardio": 2, "strength": 2}},
    "Nigeria": {"style": "athletic_striker", "mods": {"speed": 3, "strength": 3}},
    "South Africa": {"style": "athletic_striker", "mods": {"speed": 2, "strength": 2}},
}

# Pool size per region per weight class
POOL_SIZE_MIN = 20
POOL_SIZE_MAX = 25

# Tournament settings
BRACKET_SIZE = 16
TOURNAMENTS_PER_YEAR = 8  # Per region
WEEKS_BETWEEN_TOURNAMENTS = 6  # Approximate

# Points system
POINTS_CHAMPION = 10
POINTS_FINALIST = 6
POINTS_SEMIFINALIST = 3
POINTS_QUARTERFINALIST = 1
POINTS_FINISH_BONUS = 1
POINTS_FOTN_BONUS = 1

# Pro eligibility
MIN_FIGHTS_FOR_ELIGIBILITY = 8
MIN_AGE_FOR_PRO = 18
MIN_FIGHTS_FOR_RECORD_PATH = 16
MIN_WIN_RATE_FOR_RECORD_PATH = 0.70
TOP_REGIONAL_RANK_FOR_ELIGIBILITY = 3
MIN_WEEKS_FOR_ELIGIBILITY = 26  # Must be in circuit at least 6 months
PRODIGY_RATING_THRESHOLD = 82   # Harder to be an instant prodigy

# Signing costs by rating (early-game friendly)
SIGNING_COSTS = {
    (50, 59): 2000,
    (60, 69): 5000,
    (70, 79): 15000,
    (80, 100): 35000,
}

# Age constants
MIN_AMATEUR_AGE = 17
MAX_AMATEUR_AGE = 30
RETIREMENT_AGE_LOSING = 30  # Retire if losing record at this age
RETIREMENT_AGE_MAX = 33

# New amateur generation per year
NEW_AMATEURS_PER_DIVISION_PER_REGION = 3


def _calculate_buzz(fighter: "AmateurFighter") -> int:
    """Momentum score 0-100 derived from current state. Pure read —
    no side effects. Pulls streak / finishes / tournament wins live
    from the fighter dataclass + fight_history so no schema bump.

    Composition:
      - current win streak (max 40)
      - tournament wins (max 40)
      - finish-rate bonus (max 20)
      - loss penalty (-5 per loss)
    """
    history = getattr(fighter, 'fight_history', []) or []

    streak = 0
    for f in reversed(history):
        if (f.get('result') if isinstance(f, dict) else '') == 'W':
            streak += 1
        else:
            break

    wins = int(getattr(fighter, 'wins', 0) or 0)
    losses = int(getattr(fighter, 'losses', 0) or 0)
    t_wins = int(getattr(fighter, 'tournament_wins', 0) or 0)

    ko_wins = 0
    sub_wins = 0
    for f in history:
        if not isinstance(f, dict):
            continue
        if f.get('result') != 'W':
            continue
        m = (f.get('method') or '').lower()
        if 'ko' in m or 'tko' in m:
            ko_wins += 1
        elif 'sub' in m:
            sub_wins += 1

    score = 0
    score += min(streak * 8, 40)
    score += min(t_wins * 20, 40)
    if wins > 0:
        finish_rate = (ko_wins + sub_wins) / wins
        score += int(finish_rate * 20)
    score -= losses * 5
    return max(0, min(100, score))


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AmateurFighter:
    """An amateur fighter in the circuit"""
    fighter_id: str
    name: str
    age: int
    weight_class: str
    region: str
    nationality: str
    
    # Attributes (same structure as pro fighters)
    attributes: Dict[str, int] = field(default_factory=dict)
    overall_rating: int = 50
    
    # Hidden potential (revealed when signed or by elite scout)
    potential_ceiling: int = 70
    potential_grade: str = "Average"  # Elite, High, Average, Limited, Low
    
    # Amateur career
    wins: int = 0
    losses: int = 0
    amateur_fights: List[Dict[str, Any]] = field(default_factory=list)
    # Structured fight history (parallel to pro format) — populated
    # by tournament resolution; read by game_bridge converter for
    # amateur profile display.
    fight_history: List[Dict[str, Any]] = field(default_factory=list)

    # Tournament history
    tournament_wins: int = 0
    tournament_finals: int = 0
    tournament_semis: int = 0
    tournament_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Rankings
    regional_points: int = 0
    regional_rank: Optional[int] = None
    
    # Status
    is_pro_eligible: bool = False
    eligibility_reason: str = ""
    weeks_in_amateur: int = 0
    is_active: bool = True
    turned_pro: bool = False  # True if signed to a pro camp
    
    # Style info
    fighting_style: str = "Balanced"
    primary_skill: str = ""
    
    # Traits (can have amateur traits)
    traits: List[str] = field(default_factory=list)
    
    @property
    def record(self) -> str:
        return f"{self.wins}-{self.losses}"
    
    @property
    def total_fights(self) -> int:
        return self.wins + self.losses
    
    @property
    def win_rate(self) -> float:
        if self.total_fights == 0:
            return 0.0
        return self.wins / self.total_fights
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "age": self.age,
            "weight_class": self.weight_class,
            "region": self.region,
            "nationality": self.nationality,
            "attributes": self.attributes,
            "overall_rating": self.overall_rating,
            "potential_ceiling": self.potential_ceiling,
            "potential_grade": self.potential_grade,
            "wins": self.wins,
            "losses": self.losses,
            "amateur_fights": self.amateur_fights,
            "tournament_wins": self.tournament_wins,
            "tournament_finals": self.tournament_finals,
            "tournament_semis": self.tournament_semis,
            "tournament_history": self.tournament_history,
            "regional_points": self.regional_points,
            "regional_rank": self.regional_rank,
            "is_pro_eligible": self.is_pro_eligible,
            "eligibility_reason": self.eligibility_reason,
            "weeks_in_amateur": self.weeks_in_amateur,
            "is_active": self.is_active,
            "turned_pro": self.turned_pro,
            "fighting_style": self.fighting_style,
            "primary_skill": self.primary_skill,
            "traits": self.traits,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AmateurFighter":
        return cls(**data)


@dataclass
class TournamentFight:
    """A single fight in a tournament"""
    fight_id: str
    fighter1_id: str
    fighter2_id: str
    fighter1_name: str
    fighter2_name: str
    round_number: int  # Tournament round (1=quarters, 2=semis, 3=final)
    bracket_position: int
    
    # Result (filled after simulation)
    winner_id: Optional[str] = None
    loser_id: Optional[str] = None
    method: str = ""
    finish_round: Optional[int] = None
    is_fotn: bool = False
    
    # Stats for FOTN calculation
    fight_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tournament:
    """A single tournament event"""
    tournament_id: str
    name: str
    region: str
    weight_class: str
    week: int
    year: int

    # Bracket
    bracket_size: int = BRACKET_SIZE
    # Named-circuit branding — empty for legacy saves
    circuit_name: str = ""
    city: str = ""
    fighters: List[str] = field(default_factory=list)  # Fighter IDs
    seeding: List[str] = field(default_factory=list)  # Ordered by seed
    
    # Bracket state
    rounds: Dict[int, List[TournamentFight]] = field(default_factory=dict)
    
    # Results (filled after completion)
    is_complete: bool = False
    champion_id: Optional[str] = None
    finalist_id: Optional[str] = None
    semifinalists: List[str] = field(default_factory=list)
    quarterfinalists: List[str] = field(default_factory=list)
    
    fotn_fight: Optional[TournamentFight] = None
    all_fights: List[TournamentFight] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tournament_id": self.tournament_id,
            "name": self.name,
            "region": self.region,
            "weight_class": self.weight_class,
            "week": self.week,
            "year": self.year,
            "bracket_size": self.bracket_size,
            "fighters": self.fighters,
            "seeding": self.seeding,
            "is_complete": self.is_complete,
            "champion_id": self.champion_id,
            "finalist_id": self.finalist_id,
            "semifinalists": self.semifinalists,
            "quarterfinalists": self.quarterfinalists,
            "all_fights": [f.__dict__ for f in self.all_fights] if self.all_fights else [],
            "circuit_name": self.circuit_name,
            "city": self.city,
        }


@dataclass
class TournamentResults:
    """Results after tournament completes"""
    tournament_id: str
    tournament_name: str
    region: str
    weight_class: str
    
    champion_id: str
    champion_name: str
    finalist_id: str
    finalist_name: str
    semifinalists: List[Tuple[str, str]]  # (id, name)
    
    all_fights: List[TournamentFight] = field(default_factory=list)
    fotn: Optional[TournamentFight] = None
    
    # Point awards
    points_awarded: Dict[str, int] = field(default_factory=dict)
    
    # Rating changes
    rating_changes: Dict[str, int] = field(default_factory=dict)
    
    # Newly eligible
    newly_eligible: List[str] = field(default_factory=list)


@dataclass
class RegionalRankings:
    """Rankings for a single region/weight class"""
    region: str
    weight_class: str
    
    # Rankings: list of (fighter_id, points)
    rankings: List[Tuple[str, int]] = field(default_factory=list)
    
    # History
    tournaments_counted: int = 0
    last_updated_week: int = 0
    
    def get_rank(self, fighter_id: str) -> Optional[int]:
        """Get fighter's current rank (1-indexed)"""
        for i, (fid, _) in enumerate(self.rankings):
            if fid == fighter_id:
                return i + 1
        return None
    
    def get_top_n(self, n: int) -> List[Tuple[str, int]]:
        """Get top N fighters"""
        return self.rankings[:n]


@dataclass
class NationalChampionship:
    """Annual national championship tournament"""
    championship_id: str
    year: int
    weight_class: str
    week: int
    
    # Qualifiers: top 4 from each region = 16 fighters
    qualifiers: Dict[str, List[str]] = field(default_factory=dict)  # region -> [fighter_ids]
    
    # Tournament bracket (same as regional)
    tournament: Optional[Tournament] = None
    
    is_complete: bool = False
    national_champion_id: Optional[str] = None
    national_champion_name: str = ""


# ============================================================================
# NAME GENERATION (By nationality - matches generator.py patterns)
# ============================================================================

NAMES_BY_NATIONALITY = {
    "United States": {
        "first": ["Marcus", "Tyler", "Jake", "Ryan", "James", "Michael", "David", "Chris",
                  "Alex", "Jordan", "Brandon", "Kyle", "Derek", "Anthony", "Kevin", "Eric",
                  "Jason", "Justin", "Brian", "Daniel", "Steven", "Andrew", "Josh", "Matt",
                  "Nick", "Sean", "Patrick", "Connor", "Dylan", "Evan", "Luke", "Caleb"],
        "last": ["Rivera", "Thompson", "Williams", "Johnson", "Smith", "Brown", "Davis",
                 "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "White",
                 "Harris", "Martin", "Lee", "Clark", "Lewis", "Walker", "Hall", "Young"]
    },
    "Brazil": {
        "first": ["Gabriel", "Lucas", "Matheus", "Pedro", "Guilherme", "Gustavo", "Rafael",
                  "Felipe", "Joao", "Vinicius", "Leonardo", "Thiago", "Arthur", "Eduardo",
                  "Bruno", "Caio", "Daniel", "Igor", "Ricardo", "Rodrigo", "Alexandre"],
        "last": ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves",
                 "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho",
                 "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Nunes"]
    },
    "Russia": {
        "first": ["Alexander", "Dmitry", "Maxim", "Sergey", "Andrey", "Alexey", "Artem",
                  "Ilya", "Kirill", "Mikhail", "Nikita", "Ivan", "Roman", "Vladimir",
                  "Pavel", "Denis", "Ruslan", "Magomed", "Shamil", "Marat", "Khabib"],
        "last": ["Smirnov", "Ivanov", "Kuznetsov", "Popov", "Sokolov", "Lebedev", "Kozlov",
                 "Novikov", "Morozov", "Petrov", "Volkov", "Nurmagomedov", "Makhachev",
                 "Ankalaev", "Tsarukyan", "Fiziev", "Nemkov", "Emelianenko", "Kharitonov"]
    },
    "Mexico": {
        "first": ["Santiago", "Diego", "Daniel", "Alejandro", "Miguel", "Javier", "Carlos",
                  "Luis", "Jose", "Juan", "Ricardo", "Fernando", "Jorge", "Eduardo",
                  "Arturo", "Hector", "Raul", "Mario", "Brandon", "Erik"],
        "last": ["Hernandez", "Garcia", "Martinez", "Lopez", "Gonzalez", "Moreno", "Rodriguez",
                 "Sanchez", "Ramirez", "Cruz", "Gomez", "Flores", "Morales", "Vazquez"]
    },
    "United Kingdom": {
        "first": ["Oliver", "George", "Harry", "Jack", "Charlie", "Thomas", "James",
                  "William", "Daniel", "Michael", "David", "Paul", "Leon", "Darren", "Tom"],
        "last": ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson",
                 "Davies", "Robinson", "Wright", "Thompson", "Evans", "Walker", "Edwards"]
    },
    "Ireland": {
        "first": ["Conor", "Sean", "Patrick", "Michael", "John", "James", "Daniel",
                  "Paul", "Cathal", "Paddy", "Peter", "Ian", "Ciaran", "Brendan", "Finn"],
        "last": ["McGregor", "Murphy", "Kelly", "O'Sullivan", "Walsh", "O'Brien", "Byrne",
                 "Ryan", "O'Connor", "O'Neill", "Doyle", "McCarthy", "Gallagher", "Duffy"]
    },
    "Poland": {
        "first": ["Jan", "Mateusz", "Marcin", "Michal", "Pawel", "Krzysztof", "Mariusz",
                  "Damian", "Szymon", "Rafal", "Lukasz", "Karol", "Piotr", "Sebastian"],
        "last": ["Blachowicz", "Jedrzejczyk", "Gamrot", "Held", "Pudzianowski", "Grabowski",
                 "Jotko", "Kowalski", "Nowak", "Wisniewski", "Wojcik", "Lewandowski"]
    },
    "Netherlands": {
        "first": ["Bas", "Alistair", "Remy", "Gilbert", "Gegard", "Stefan", "Reinier",
                  "Melvin", "Rico", "Sem", "Daan", "Bram", "Lars", "Stijn"],
        "last": ["Rutten", "Overeem", "Bonjasky", "Mousasi", "Struve", "de Ridder",
                 "Manhoef", "Rozenstruik", "Verhoeven", "de Jong", "van Dijk", "de Vries"]
    },
    "Japan": {
        "first": ["Yushin", "Takanori", "Yoshihiro", "Kazushi", "Takeshi", "Shinya",
                  "Yuki", "Naoya", "Keita", "Mikuru", "Kai", "Kyoji", "Tenshin"],
        "last": ["Okami", "Gomi", "Akiyama", "Sakuraba", "Inoue", "Aoki", "Nakamura",
                 "Horiguchi", "Sasaki", "Tanaka", "Yamamoto", "Takahashi", "Ishihara"]
    },
    "South Korea": {
        "first": ["Chan", "Sung", "Dong", "Seung", "Jung", "Doo", "Hyun", "Jin", "Min"],
        "last": ["Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon", "Jang"]
    },
    "Thailand": {
        "first": ["Rodtang", "Superbon", "Sitthichai", "Buakaw", "Saenchai", "Nong-O",
                  "Tawanchai", "Prajanchai", "Sangmanee", "Dieselnoi", "Lerdsila"],
        "last": ["Jitmuangnon", "Fairtex", "Petchyindee", "Banchamek", "Sitsongpeenong",
                 "Por Pramuk", "Sor Kingstar", "Kaewsamrit", "Gaiyanghadao", "Sitjaopho"]
    },
    "Australia": {
        "first": ["Robert", "Alexander", "Tai", "Jake", "Jimmy", "Dan", "Kyle", "Tyson",
                  "Jack", "Jamie", "Josh", "Shane", "Luke", "Ben", "George", "Callan"],
        "last": ["Whittaker", "Volkanovski", "Tuivasa", "Matthews", "Crute", "Hooker",
                 "Pedro", "Jenkins", "Smith", "Hunt", "Kelly", "Mullarkey", "O'Neill"]
    },
    "Nigeria": {
        "first": ["Kamaru", "Israel", "Kennedy", "Sodiq", "Ode", "Chidi", "Abdul",
                  "Emmanuel", "Oluwale", "Tunde", "Femi", "Emeka", "Nnamdi", "Tobi"],
        "last": ["Usman", "Adesanya", "Nzechukwu", "Yusuff", "Osbourne", "Njokuani",
                 "Okonkwo", "Adeyemi", "Okafor", "Eze", "Chukwu", "Obiora"]
    },
    "China": {
        "first": ["Weili", "Li", "Yan", "Song", "Wang", "Zhang", "Wu", "Liu", "Chen"],
        "last": ["Zhang", "Jingliang", "Yadong", "Kenan", "Lipeng", "Ning", "Wei", "Jun"]
    },
    "Uzbekistan": {
        "first": ["Makhmud", "Murodjon", "Shavkat", "Bekzod", "Rustam", "Azamat",
                  "Jakhongir", "Sanjar", "Dilshod", "Nodir"],
        "last": ["Muradov", "Rakhmonov", "Azimov", "Tursunov", "Mirzaev", "Karimov",
                 "Yusupov", "Saidov", "Nematov", "Ibragimov"]
    },
    "Kazakhstan": {
        "first": ["Shavkat", "Daulet", "Arman", "Zhalgas", "Nurlan", "Serik", "Ruslan"],
        "last": ["Rakhmonov", "Zhumagulov", "Sarsenbaev", "Ospanov", "Zhumabaev"]
    },
}

# Fallback names for nationalities not in the dict
FALLBACK_FIRST = ["Alex", "Max", "Ivan", "Leo", "Marco", "Andre", "Victor", "Oscar"]
FALLBACK_LAST = ["Silva", "Lee", "Garcia", "Kim", "Petrov", "Schmidt", "Martin"]


def generate_amateur_name(nationality: str, existing_names: Set[str]) -> str:
    """Generate a unique amateur fighter name based on nationality"""
    
    # Get names for this nationality
    names = NAMES_BY_NATIONALITY.get(nationality, {
        "first": FALLBACK_FIRST,
        "last": FALLBACK_LAST
    })
    
    first_names = names.get("first", FALLBACK_FIRST)
    last_names = names.get("last", FALLBACK_LAST)
    
    for _ in range(100):
        first = random.choice(first_names)
        last = random.choice(last_names)
        name = f"{first} {last}"
        if name not in existing_names:
            return name
    
    # Fallback with suffix
    return f"{random.choice(first_names)} {random.choice(last_names)} Jr."


# ============================================================================
# AMATEUR FIGHTER GENERATION
# ============================================================================

def generate_amateur_attributes(
    age: int,
    potential_ceiling: int,
    nationality: str,
) -> Tuple[Dict[str, int], str, str]:
    """
    Generate attributes for an amateur fighter based on nationality.
    
    Returns:
        Tuple of (attributes dict, fighting_style, primary_skill)
    """
    
    # Base attributes lower than pros
    base_min = 30
    base_max = 57
    
    # Younger fighters start lower but have more room to grow
    age_modifier = min(14, max(0, int((age - 18) * 1.5)))  # +1.5/yr, capped at +14
    
    # Generate base attributes
    attrs = {
        "boxing": random.randint(base_min, base_max) + age_modifier,
        "kicks": random.randint(base_min, base_max) + age_modifier,
        "wrestling": random.randint(base_min, base_max) + age_modifier,
        "bjj": random.randint(base_min, base_max) + age_modifier,
        "clinch_striking": random.randint(base_min, base_max) + age_modifier,
        "clinch_control": random.randint(base_min, base_max) + age_modifier,
        "striking_defense": random.randint(base_min, base_max) + age_modifier,
        "takedown_defense": random.randint(base_min, base_max) + age_modifier,
        "strength": random.randint(base_min + 5, base_max + 10) + age_modifier,
        "speed": random.randint(base_min + 5, base_max + 10) + age_modifier,
        "cardio": random.randint(base_min + 5, base_max + 10) + age_modifier,
        "chin": random.randint(base_min, base_max + 5) + age_modifier,
        "heart": random.randint(base_min, base_max + 10) + age_modifier,
        "fight_iq": random.randint(base_min - 5, base_max) + age_modifier,  # Lower for amateurs
        "composure": random.randint(base_min - 5, base_max) + age_modifier,
    }
    
    # Apply nationality-based style modifiers
    nat_data = NATIONALITY_STYLE_TENDENCIES.get(nationality, {})
    style_name = nat_data.get("style", "balanced")
    mods = nat_data.get("mods", {})
    
    for attr, mod in mods.items():
        if attr in attrs:
            attrs[attr] = attrs[attr] + mod
    
    # Additional style-specific boosts
    if style_name in ["bjj_specialist", "grappler"]:
        attrs["bjj"] += random.randint(3, 8)
        attrs["wrestling"] += random.randint(1, 4)
    elif style_name in ["wrestler", "sambo"]:
        attrs["wrestling"] += random.randint(5, 10)
        attrs["takedown_defense"] += random.randint(3, 6)
    elif style_name in ["boxer", "technical_striker"]:
        attrs["boxing"] += random.randint(4, 8)
        attrs["striking_defense"] += random.randint(2, 5)
    elif style_name in ["kickboxer", "muay_thai"]:
        attrs["kicks"] += random.randint(4, 8)
        attrs["clinch_striking"] += random.randint(2, 5)
        attrs["clinch_control"] += random.randint(3, 6)
    # Style bonus: dedicated clinch and grappling-with-clinch styles
    if style_name in ["wrestler", "sambo"]:
        attrs["clinch_control"] += random.randint(3, 6)
    elif style_name == "athletic_striker":
        attrs["speed"] += random.randint(3, 6)
        attrs["boxing"] += random.randint(2, 5)
    
    # Clamp all values (amateurs capped at 75)
    for key in attrs:
        attrs[key] = max(28, min(72, attrs[key]))
    
    # Determine primary skill
    skill_attrs = {
        "boxing": attrs["boxing"],
        "wrestling": attrs["wrestling"],
        "bjj": attrs["bjj"],
        "kicks": attrs["kicks"],
    }
    primary_skill = max(skill_attrs, key=skill_attrs.get)
    
    # Map to fighting style label
    style_labels = {
        "bjj_specialist": "BJJ",
        "wrestler": "Wrestler",
        "sambo": "Sambo",
        "boxer": "Boxer",
        "technical_striker": "Striker",
        "kickboxer": "Kickboxer",
        "muay_thai": "Muay Thai",
        "athletic_striker": "Athlete",
        "mma_hybrid": "MMA",
        "well_rounded": "Balanced",
        "technical": "Technical",
        "athletic": "Athlete",
    }
    fighting_style = style_labels.get(style_name, "Balanced")
    
    return attrs, fighting_style, primary_skill


def calculate_potential_grade(ceiling: int) -> str:
    """Convert ceiling rating to grade"""
    if ceiling >= 90:
        return "Elite"
    elif ceiling >= 80:
        return "High"
    elif ceiling >= 65:
        return "Average"
    elif ceiling >= 55:
        return "Limited"
    else:
        return "Low"


def generate_amateur_fighter(
    weight_class: str,
    region: str,
    existing_names: Set[str],
    age: Optional[int] = None,
    force_young: bool = False,
    nationality: Optional[str] = None,
) -> AmateurFighter:
    """Generate a single amateur fighter for a region"""
    
    # Age distribution
    if age is None:
        if force_young:
            age = random.randint(18, 20)
        else:
            # Weighted toward younger
            age = random.choices(
                [18, 19, 20, 21, 22, 23, 24, 25, 26],
                weights=[15, 20, 18, 15, 12, 8, 6, 4, 2],
                k=1
            )[0]
    
    # Nationality from region if not specified
    if nationality is None:
        region_nationalities = REGION_NATIONALITIES.get(region, ["United States"])
        # Weight nationalities (some countries produce more fighters)
        if region == "Americas":
            weights = [40, 30, 10, 15, 5]  # USA, Brazil heavy
        elif region == "Europe":
            weights = [25, 15, 10, 10, 10, 8, 8, 8, 6]  # Russia, UK heavy
        elif region == "Asia":
            weights = [20, 15, 15, 20, 20, 10]  # Spread with wrestling nations
        else:  # Pacific
            weights = [35, 15, 30, 20]  # Australia, Nigeria strong
        
        # Normalize weights to match nationality list length
        if len(weights) != len(region_nationalities):
            weights = [1] * len(region_nationalities)
        
        nationality = random.choices(region_nationalities, weights=weights, k=1)[0]
    
    # Name based on nationality
    name = generate_amateur_name(nationality, existing_names)
    existing_names.add(name)
    
    # Potential (hidden)
    # Younger = wider range of potential
    if age <= 20:
        potential_ceiling = random.randint(48, 82)
    elif age <= 23:
        potential_ceiling = random.randint(45, 76)
    else:
        potential_ceiling = random.randint(42, 68)
    
    potential_grade = calculate_potential_grade(potential_ceiling)
    
    # Attributes based on nationality
    attributes, fighting_style, primary_skill = generate_amateur_attributes(
        age, potential_ceiling, nationality
    )
    
    # Calculate overall
    overall = sum(attributes.values()) // len(attributes)
    
    # Possible traits (amateurs have fewer)
    traits = []
    if random.random() < 0.15:
        amateur_traits = ["Fast Starter", "Slow Starter", "Iron Chin", "Glass Cannon", 
                         "Cardio Machine", "Gym Rat"]
        traits.append(random.choice(amateur_traits))
    
    return AmateurFighter(
        fighter_id=str(uuid.uuid4())[:8],
        name=name,
        age=age,
        weight_class=weight_class,
        region=region,
        nationality=nationality,
        attributes=attributes,
        overall_rating=overall,
        potential_ceiling=potential_ceiling,
        potential_grade=potential_grade,
        fighting_style=fighting_style,
        primary_skill=primary_skill,
        traits=traits,
    )


# ============================================================================
# AMATEUR SYSTEM MAIN CLASS
# ============================================================================

class AmateurSystem:
    """
    Manages the entire amateur circuit.
    
    Handles:
    - Amateur pools by region and weight class
    - Tournament creation and simulation
    - Regional rankings
    - Pro eligibility tracking
    - Signing mechanics
    - National Championship
    """
    
    def __init__(self):
        # Amateur pools: region -> weight_class -> [AmateurFighter]
        self.pools: Dict[str, Dict[str, List[AmateurFighter]]] = {}
        
        # All amateurs by ID for quick lookup
        self.amateurs: Dict[str, AmateurFighter] = {}
        
        # Regional rankings: region -> weight_class -> RegionalRankings
        self.rankings: Dict[str, Dict[str, RegionalRankings]] = {}
        
        # Tournament schedule: week -> [Tournament]
        self.scheduled_tournaments: Dict[int, List[Tournament]] = {}
        
        # Completed tournaments
        self.completed_tournaments: List[Tournament] = []
        
        # National championships
        self.national_championships: Dict[int, Dict[str, NationalChampionship]] = {}  # year -> weight_class -> NC
        
        # Current year/week tracking
        self.current_week: int = 0
        self.current_year: int = 1
        
        # Names used (for uniqueness)
        self._used_names: Set[str] = set()
    
    def initialize_pools(self) -> None:
        """Initialize all amateur pools for all regions and weight classes"""
        
        for region in REGIONS:
            self.pools[region] = {}
            self.rankings[region] = {}
            
            for weight_class in WEIGHT_CLASSES:
                pool_size = random.randint(POOL_SIZE_MIN, POOL_SIZE_MAX)
                
                fighters = []
                for _ in range(pool_size):
                    fighter = generate_amateur_fighter(
                        weight_class=weight_class,
                        region=region,
                        existing_names=self._used_names,
                    )
                    fighters.append(fighter)
                    self.amateurs[fighter.fighter_id] = fighter
                
                self.pools[region][weight_class] = fighters
                
                # Initialize empty rankings
                self.rankings[region][weight_class] = RegionalRankings(
                    region=region,
                    weight_class=weight_class,
                )
    
    def get_pool(self, region: str, weight_class: str) -> List[AmateurFighter]:
        """Get amateur pool for a region/weight class"""
        return self.pools.get(region, {}).get(weight_class, [])
    
    def get_amateur(self, fighter_id: str) -> Optional[AmateurFighter]:
        """Get an amateur by ID"""
        return self.amateurs.get(fighter_id)
    
    def get_active_amateurs(self, region: str, weight_class: str) -> List[AmateurFighter]:
        """Get active (non-signed) amateurs for a region/weight class"""
        pool = self.get_pool(region, weight_class)
        return [f for f in pool if f.is_active]
    
    # ========================================================================
    # TOURNAMENT CREATION
    # ========================================================================
    
    def create_tournament(
        self,
        region: str,
        weight_class: str,
        week: int,
        year: int = 1,
    ) -> Optional[Tournament]:
        """Create a tournament for a region/weight class"""
        
        pool = self.get_active_amateurs(region, weight_class)
        
        if len(pool) < BRACKET_SIZE:
            # Not enough fighters - generate more
            needed = BRACKET_SIZE - len(pool)
            for _ in range(needed):
                fighter = generate_amateur_fighter(
                    weight_class=weight_class,
                    region=region,
                    existing_names=self._used_names,
                    force_young=True,
                )
                self.pools[region][weight_class].append(fighter)
                self.amateurs[fighter.fighter_id] = fighter
                pool.append(fighter)
        
        # Select 16 fighters for bracket
        # Prioritize by: regional rank, then overall rating, then random
        sorted_pool = sorted(
            pool,
            key=lambda f: (f.regional_rank or 999, -f.overall_rating),
        )
        
        selected = sorted_pool[:BRACKET_SIZE]
        random.shuffle(selected)  # Randomize bracket positions
        
        # Create seeding (by rating for initial seeding)
        seeded = sorted(selected, key=lambda f: -f.overall_rating)
        seeding = [f.fighter_id for f in seeded]
        
        # Tournament name — city + suffix from named regional circuit
        tournament_num = len([t for t in self.completed_tournaments
                            if t.region == region and t.weight_class == weight_class and t.year == year]) + 1
        circuit_info = REGION_CIRCUITS.get(region, {})
        cities = circuit_info.get("cities", [region])
        suffixes = TOURNAMENT_SUFFIXES
        city = cities[tournament_num % len(cities)]
        suffix = suffixes[(tournament_num // len(cities)) % len(suffixes)]
        name = f"{city} {suffix} — {weight_class}"
        circuit_name = circuit_info.get("circuit", region)

        tournament = Tournament(
            tournament_id=str(uuid.uuid4())[:8],
            name=name,
            region=region,
            weight_class=weight_class,
            week=week,
            year=year,
            fighters=[f.fighter_id for f in selected],
            seeding=seeding,
            circuit_name=circuit_name,
            city=city,
        )
        
        # Create bracket
        self._create_bracket(tournament, selected)
        
        return tournament
    
    def _create_bracket(self, tournament: Tournament, fighters: List[AmateurFighter]) -> None:
        """Create the 16-fighter bracket structure"""
        
        # Standard 16-fighter bracket seeding
        # Seed 1 vs 16, 8 vs 9, 5 vs 12, 4 vs 13, 3 vs 14, 6 vs 11, 7 vs 10, 2 vs 15
        seed_matchups = [
            (0, 15), (7, 8), (4, 11), (3, 12),
            (2, 13), (5, 10), (6, 9), (1, 14)
        ]
        
        # Sort by rating for seeding
        seeded = sorted(fighters, key=lambda f: -f.overall_rating)
        
        # Create quarterfinal fights
        qf_fights = []
        for i, (seed1, seed2) in enumerate(seed_matchups):
            f1 = seeded[seed1]
            f2 = seeded[seed2]
            
            fight = TournamentFight(
                fight_id=str(uuid.uuid4())[:8],
                fighter1_id=f1.fighter_id,
                fighter2_id=f2.fighter_id,
                fighter1_name=f1.name,
                fighter2_name=f2.name,
                round_number=1,  # Quarterfinals
                bracket_position=i,
            )
            qf_fights.append(fight)
        
        tournament.rounds[1] = qf_fights
        # Semis and finals will be created during simulation
    
    # ========================================================================
    # TOURNAMENT SIMULATION
    # ========================================================================
    
    def simulate_tournament(self, tournament: Tournament) -> TournamentResults:
        """Simulate an entire tournament and return results"""
        
        all_fights = []
        
        # Simulate quarterfinals
        qf_winners = []
        for fight in tournament.rounds[1]:
            self._simulate_fight(fight, tournament)
            all_fights.append(fight)
            qf_winners.append(fight.winner_id)
        
        # Create and simulate semifinals
        sf_fights = []
        for i in range(0, len(qf_winners), 2):
            f1 = self.get_amateur(qf_winners[i])
            f2 = self.get_amateur(qf_winners[i + 1])
            
            fight = TournamentFight(
                fight_id=str(uuid.uuid4())[:8],
                fighter1_id=f1.fighter_id,
                fighter2_id=f2.fighter_id,
                fighter1_name=f1.name,
                fighter2_name=f2.name,
                round_number=2,
                bracket_position=i // 2,
            )
            self._simulate_fight(fight, tournament)
            sf_fights.append(fight)
            all_fights.append(fight)
        
        tournament.rounds[2] = sf_fights
        
        sf_winners = [f.winner_id for f in sf_fights]
        sf_losers = [f.loser_id for f in sf_fights]
        
        # Create and simulate final
        f1 = self.get_amateur(sf_winners[0])
        f2 = self.get_amateur(sf_winners[1])
        
        final = TournamentFight(
            fight_id=str(uuid.uuid4())[:8],
            fighter1_id=f1.fighter_id,
            fighter2_id=f2.fighter_id,
            fighter1_name=f1.name,
            fighter2_name=f2.name,
            round_number=3,
            bracket_position=0,
        )
        self._simulate_fight(final, tournament)
        all_fights.append(final)
        
        tournament.rounds[3] = [final]
        
        # Determine placements
        champion_id = final.winner_id
        finalist_id = final.loser_id
        semifinalists = sf_losers
        quarterfinalists = [f.loser_id for f in tournament.rounds[1]]
        
        # Select FOTN
        fotn_fight = self._select_fotn(all_fights)
        if fotn_fight:
            fotn_fight.is_fotn = True
        
        # Update tournament
        tournament.is_complete = True
        tournament.champion_id = champion_id
        tournament.finalist_id = finalist_id
        tournament.semifinalists = semifinalists
        tournament.quarterfinalists = quarterfinalists
        tournament.fotn_fight = fotn_fight
        tournament.all_fights = all_fights
        
        self.completed_tournaments.append(tournament)
        
        # Award points and update fighters
        points_awarded = self._award_points(tournament, fotn_fight)
        rating_changes = self._process_fighter_updates(tournament)
        newly_eligible = self._check_eligibility_updates(tournament)
        
        # Update rankings
        self._update_rankings(tournament.region, tournament.weight_class)
        
        # Create results
        champion = self.get_amateur(champion_id)
        finalist = self.get_amateur(finalist_id)
        
        return TournamentResults(
            tournament_id=tournament.tournament_id,
            tournament_name=tournament.name,
            region=tournament.region,
            weight_class=tournament.weight_class,
            champion_id=champion_id,
            champion_name=champion.name if champion else "Unknown",
            finalist_id=finalist_id,
            finalist_name=finalist.name if finalist else "Unknown",
            semifinalists=[(sid, self.get_amateur(sid).name if self.get_amateur(sid) else "Unknown") 
                          for sid in semifinalists],
            all_fights=all_fights,
            fotn=fotn_fight,
            points_awarded=points_awarded,
            rating_changes=rating_changes,
            newly_eligible=newly_eligible,
        )
    
    def _composite_score(self, fighter: "AmateurFighter") -> Tuple[float, float, float, float]:
        """
        Break a fighter into four composite dimensions.
        Returns (striking, grappling, physical, mental).
        """
        a = fighter.attributes
        striking  = (a.get("boxing", 50) * 2 + a.get("kicks", 50) +
                     a.get("clinch_striking", 50) + a.get("striking_defense", 50) +
                     a.get("clinch_control", 50) * 0.5) / 5.5
        grappling = (a.get("wrestling", 50) * 2 + a.get("bjj", 50) +
                     a.get("takedown_defense", 50)) / 4
        physical  = (a.get("strength", 50) + a.get("speed", 50) +
                     a.get("cardio", 50) + a.get("chin", 50)) / 4
        mental    = (a.get("heart", 50) + a.get("fight_iq", 50) +
                     a.get("composure", 50)) / 3
        return striking, grappling, physical, mental

    def _simulate_fight(self, fight: "TournamentFight",
                        tournament: Optional["Tournament"] = None) -> None:
        """
        Simulate a single amateur fight using attribute-based matchup scoring.

        Win probability reflects:
        - Striking vs striking defense
        - Grappling vs takedown defense
        - Physical edge (strength/speed/chin)
        - Mental edge (heart/composure under pressure)
        
        Finish method uses winner's dominant dimension.
        """
        f1 = self.get_amateur(fight.fighter1_id)
        f2 = self.get_amateur(fight.fighter2_id)

        if not f1 or not f2:
            fight.winner_id = fight.fighter1_id
            fight.loser_id  = fight.fighter2_id
            fight.method    = "Decision"
            return

        s1, g1, ph1, m1 = self._composite_score(f1)
        s2, g2, ph2, m2 = self._composite_score(f2)

        # Effective scores: striking lands against opponent's defense
        f1_effective = (
            s1 * 0.35 +          # striker output
            g1 * 0.30 +          # grappling output
            ph1 * 0.20 +         # physical edge
            m1 * 0.15            # mental edge
        ) - (
            f2.attributes.get("striking_defense", 50) * 0.15 +
            f2.attributes.get("takedown_defense", 50) * 0.10
        )
        f2_effective = (
            s2 * 0.35 +
            g2 * 0.30 +
            ph2 * 0.20 +
            m2 * 0.15
        ) - (
            f1.attributes.get("striking_defense", 50) * 0.15 +
            f1.attributes.get("takedown_defense", 50) * 0.10
        )

        diff = f1_effective - f2_effective
        f1_win_prob = 0.5 + (diff / 120.0)
        f1_win_prob = max(0.10, min(0.90, f1_win_prob))

        if random.random() < f1_win_prob:
            winner, loser = f1, f2
            ws, wg = s1, g1
        else:
            winner, loser = f2, f1
            ws, wg = s2, g2

        fight.winner_id = winner.fighter_id
        fight.loser_id  = loser.fighter_id

        # ── Method: driven by winner's dominant dimension ─────────
        method_roll  = random.random()
        finish_round = None
        chin_loser   = loser.attributes.get("chin", 50)
        sub_def      = loser.attributes.get("bjj", 50)  # resists submissions

        # KO/TKO probability scales with striking advantage & loser's chin
        ko_prob  = 0.10 + (ws - 50) / 200 + (50 - chin_loser) / 200
        ko_prob  = max(0.05, min(0.45, ko_prob))
        # Sub probability scales with grappling advantage
        sub_prob = 0.08 + (wg - 50) / 250 + (50 - sub_def) / 300
        sub_prob = max(0.03, min(0.25, sub_prob))

        if method_roll < ko_prob:
            fight.method = "KO" if random.random() < 0.35 else "TKO"
            finish_round = random.choices([1, 2, 3], weights=[35, 40, 25], k=1)[0]
        elif method_roll < ko_prob + sub_prob:
            fight.method = "Submission"
            finish_round = random.choices([1, 2, 3], weights=[15, 40, 45], k=1)[0]
        else:
            fight.method = random.choices(
                ["Unanimous Decision", "Split Decision", "Majority Decision"],
                weights=[55, 30, 15], k=1
            )[0]

        fight.finish_round = finish_round

        fight.fight_stats = {
            "winner_rating":  winner.overall_rating,
            "loser_rating":   loser.overall_rating,
            "rating_diff":    abs(f1.overall_rating - f2.overall_rating),
            "was_finish":     finish_round is not None,
            "finish_round":   finish_round,
            "method":         fight.method,
        }

        # Update records
        winner.wins += 1
        winner.amateur_fights.append({
            "opponent": loser.name, "result": "W",
            "method": fight.method, "tournament": True,
        })
        loser.losses += 1
        loser.amateur_fights.append({
            "opponent": winner.name, "result": "L",
            "method": fight.method, "tournament": True,
        })

        # Structured fight history — parallel to pro format
        _week = getattr(tournament, 'week', 0) or 0
        _tname = getattr(tournament, 'name', 'Tournament')
        winner.fight_history.append({
            "result": "W",
            "opponent_id": loser.fighter_id,
            "opponent_name": getattr(loser, 'name', ''),
            "week": _week,
            "tournament": _tname,
            "method": fight.method,
        })
        loser.fight_history.append({
            "result": "L",
            "opponent_id": winner.fighter_id,
            "opponent_name": getattr(winner, 'name', ''),
            "week": _week,
            "tournament": _tname,
            "method": fight.method,
        })

        # Per-tournament-fight stat development. Higher-potential
        # grades gain faster; winners get a 20% bonus. Stats live in
        # the AmateurFighter.attributes dict — keys must match the
        # amateur schema (wrestling/bjj, NOT takedowns/submissions).
        import random as _rnd
        _POTENTIAL_GAINS = {
            "Elite":   (1.5, 0.5),
            "High":    (1.0, 0.3),
            "Average": (0.6, 0.2),
            "Limited": (0.3, 0.1),
        }
        _STYLE_PRIMARY_AMATEUR = {
            "BJJ Specialist":   "bjj",
            "Submission Artist":"bjj",
            "Wrestler":         "wrestling",
            "Sambo":            "wrestling",
            "Ground & Pound":   "wrestling",
            "Muay Thai":        "kicks",
            "Kickboxer":        "kicks",
            "Striker":          "boxing",
            "Orthodox Boxer":   "boxing",
            "Clinch Fighter":   "clinch_striking",
            "Counter Striker":  "striking_defense",
            "Sprawl & Brawl":   "takedown_defense",
            "Pressure Fighter": "cardio",
            "Karate":           "fight_iq",
            "Point Fighter":    "speed",
            "Brawler":          "strength",
        }
        _AMATEUR_SECONDARY_POOL = [
            "boxing", "kicks", "clinch_striking", "striking_defense",
            "takedown_defense", "wrestling", "bjj",
            "strength", "speed", "cardio", "chin", "heart",
            "fight_iq", "composure"
        ]
        _AMATEUR_TRAINABLE = [
            "boxing", "kicks", "wrestling", "bjj", "clinch_striking",
            "striking_defense", "takedown_defense", "strength", "speed",
            "cardio", "chin", "heart", "fight_iq", "composure"
        ]

        for participant, did_win in [(winner, True), (loser, False)]:
            grade = getattr(participant, 'potential_grade', 'Average')
            primary_gain, secondary_gain = _POTENTIAL_GAINS.get(grade, (0.6, 0.2))
            if did_win:
                primary_gain *= 1.2
                secondary_gain *= 1.2

            style = getattr(participant, 'fighting_style', 'Balanced')
            primary_stat = _STYLE_PRIMARY_AMATEUR.get(style, 'boxing')
            secondary_candidates = [s for s in _AMATEUR_SECONDARY_POOL
                                    if s != primary_stat]
            secondary_stat = _rnd.choice(secondary_candidates)

            for stat, gain in [(primary_stat, primary_gain),
                               (secondary_stat, secondary_gain)]:
                current = participant.attributes.get(stat, 45)
                participant.attributes[stat] = round(min(72.0, current + gain), 2)

            # Recalculate OVR from attributes dict
            vals = [participant.attributes.get(s, 0) for s in _AMATEUR_TRAINABLE
                    if s in participant.attributes]
            if vals:
                participant.overall_rating = int(sum(vals) / len(vals))
    
    def _select_fotn(self, fights: List[TournamentFight]) -> Optional[TournamentFight]:
        """Select Fight of the Night from tournament fights"""
        
        if not fights:
            return None
        
        scored = []
        for fight in fights:
            score = 0.0
            stats = fight.fight_stats
            
            # Close fight bonus
            rating_diff = stats.get("rating_diff", 0)
            if rating_diff < 5:
                score += 50  # Very close matchup
            elif rating_diff < 10:
                score += 30
            
            # Finish bonus
            if stats.get("was_finish"):
                score += 40
                if stats.get("finish_round", 0) >= 3:
                    score += 30  # Late finish
            
            # Method bonus
            method = stats.get("method", "")
            if "KO" in method:
                score += 25
            elif "Submission" in method:
                score += 20
            elif "Split" in method:
                score += 40  # Close decisions are exciting
            
            # Final round bonus
            if fight.round_number == 3:
                score += 20
            
            scored.append((fight, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None
    
    def _award_points(self, tournament: Tournament, fotn: Optional[TournamentFight]) -> Dict[str, int]:
        """Award points based on tournament placement"""
        
        points = {}
        
        # Champion
        if tournament.champion_id:
            champ = self.get_amateur(tournament.champion_id)
            if champ:
                pts = POINTS_CHAMPION
                champ.regional_points += pts
                champ.tournament_wins += 1
                points[tournament.champion_id] = pts
        
        # Finalist
        if tournament.finalist_id:
            fin = self.get_amateur(tournament.finalist_id)
            if fin:
                pts = POINTS_FINALIST
                fin.regional_points += pts
                fin.tournament_finals += 1
                points[tournament.finalist_id] = pts
        
        # Semifinalists
        for sid in tournament.semifinalists:
            semi = self.get_amateur(sid)
            if semi:
                pts = POINTS_SEMIFINALIST
                semi.regional_points += pts
                semi.tournament_semis += 1
                points[sid] = pts
        
        # Quarterfinalists
        for qid in tournament.quarterfinalists:
            quarter = self.get_amateur(qid)
            if quarter:
                pts = POINTS_QUARTERFINALIST
                quarter.regional_points += pts
                points[qid] = pts
        
        # Finish bonuses
        for fight in tournament.all_fights:
            if fight.finish_round:  # Was a finish
                winner = self.get_amateur(fight.winner_id)
                if winner and fight.winner_id in points:
                    points[fight.winner_id] += POINTS_FINISH_BONUS
                    winner.regional_points += POINTS_FINISH_BONUS
        
        # FOTN bonus
        if fotn:
            for fid in [fotn.fighter1_id, fotn.fighter2_id]:
                fighter = self.get_amateur(fid)
                if fighter:
                    if fid in points:
                        points[fid] += POINTS_FOTN_BONUS
                    else:
                        points[fid] = POINTS_FOTN_BONUS
                    fighter.regional_points += POINTS_FOTN_BONUS
        
        return points
    
    def _process_fighter_updates(self, tournament: Tournament) -> Dict[str, int]:
        """Process rating changes based on tournament performance"""
        
        changes = {}
        
        for fight in tournament.all_fights:
            winner = self.get_amateur(fight.winner_id)
            loser = self.get_amateur(fight.loser_id)
            
            if winner:
                # Growth from winning
                gain = self._calculate_growth(winner, won=True, fight=fight)
                self._apply_growth(winner, gain)
                changes[winner.fighter_id] = changes.get(winner.fighter_id, 0) + gain
            
            if loser:
                # Smaller growth from losing (still learning)
                gain = self._calculate_growth(loser, won=False, fight=fight)
                self._apply_growth(loser, gain)
                changes[loser.fighter_id] = changes.get(loser.fighter_id, 0) + gain
        
        return changes
    
    def _calculate_growth(self, fighter: AmateurFighter, won: bool, fight: TournamentFight) -> int:
        """Calculate rating growth from a fight"""
        
        base = 3 if won else 1
        
        # Age multiplier
        if fighter.age <= 19:
            mult = 1.5
        elif fighter.age <= 22:
            mult = 1.25
        elif fighter.age <= 25:
            mult = 1.0
        else:
            mult = 0.7
        
        # Performance bonus
        if won and fight.finish_round:
            base += 1
        if fight.round_number == 3:  # Made it to finals
            base += 1
        
        return int(base * mult)
    
    def _apply_growth(self, fighter: AmateurFighter, growth: int) -> None:
        """Apply growth to fighter's attributes"""
        
        if growth <= 0:
            return
        
        # Distribute growth among attributes
        # Primary skill gets more
        primary = fighter.primary_skill
        if primary in fighter.attributes:
            fighter.attributes[primary] = min(75, fighter.attributes[primary] + growth)
        
        # Random secondary attribute
        secondaries = [k for k in fighter.attributes.keys() if k != primary]
        if secondaries and growth > 1:
            sec = random.choice(secondaries)
            fighter.attributes[sec] = min(75, fighter.attributes[sec] + (growth // 2))
        
        # Recalculate overall
        fighter.overall_rating = sum(fighter.attributes.values()) // len(fighter.attributes)
    
    # ========================================================================
    # ELIGIBILITY
    # ========================================================================
    
    def _check_eligibility_updates(self, tournament: Tournament) -> List[str]:
        """Check if any fighters became pro eligible"""
        
        newly_eligible = []
        
        for fid in tournament.fighters:
            fighter = self.get_amateur(fid)
            if not fighter or fighter.is_pro_eligible:
                continue
            
            eligible, reason = self.check_pro_eligibility(fighter)
            if eligible:
                fighter.is_pro_eligible = True
                fighter.eligibility_reason = reason
                newly_eligible.append(fid)
        
        return newly_eligible
    
    def check_pro_eligibility(self, fighter: AmateurFighter) -> Tuple[bool, str]:
        """Check if a fighter is eligible to turn pro"""
        
        # Minimum requirements
        if fighter.total_fights < MIN_FIGHTS_FOR_ELIGIBILITY:
            return False, f"Need {MIN_FIGHTS_FOR_ELIGIBILITY}+ fights"

        if fighter.age < MIN_AGE_FOR_PRO:
            return False, f"Must be {MIN_AGE_FOR_PRO}+"

        if fighter.weeks_in_amateur < MIN_WEEKS_FOR_ELIGIBILITY:
            return False, f"Need {MIN_WEEKS_FOR_ELIGIBILITY}+ weeks in circuit"
        
        # Prodigy rule
        if fighter.overall_rating >= PRODIGY_RATING_THRESHOLD:
            return True, "Prodigy (rating 72+)"
        
        # Tournament win
        if fighter.tournament_wins >= 1:
            return True, "Regional Tournament Champion"
        
        # Record path
        if fighter.total_fights >= MIN_FIGHTS_FOR_RECORD_PATH:
            if fighter.win_rate >= MIN_WIN_RATE_FOR_RECORD_PATH:
                return True, f"Experienced ({fighter.record}, {fighter.win_rate:.0%} win rate)"
        
        # Regional ranking
        if fighter.regional_rank and fighter.regional_rank <= TOP_REGIONAL_RANK_FOR_ELIGIBILITY:
            return True, f"Top {TOP_REGIONAL_RANK_FOR_ELIGIBILITY} Regional Ranking"
        
        return False, "Not yet eligible"
    
    def get_eligible_amateurs(self, weight_class: Optional[str] = None) -> List[AmateurFighter]:
        """Get all pro-eligible amateurs"""
        
        eligible = []
        for fighter in self.amateurs.values():
            if fighter.is_pro_eligible and fighter.is_active:
                if weight_class is None or fighter.weight_class == weight_class:
                    eligible.append(fighter)
        
        return sorted(eligible, key=lambda f: -f.overall_rating)
    
    # ========================================================================
    # RANKINGS
    # ========================================================================
    
    def _update_rankings(self, region: str, weight_class: str) -> None:
        """Update regional rankings after a tournament"""
        
        pool = self.get_active_amateurs(region, weight_class)
        
        # Sort by points, then by overall rating
        sorted_fighters = sorted(
            pool,
            key=lambda f: (-f.regional_points, -f.overall_rating)
        )
        
        # Update rankings
        rankings = self.rankings[region][weight_class]
        rankings.rankings = [(f.fighter_id, f.regional_points) for f in sorted_fighters]
        rankings.tournaments_counted += 1
        rankings.last_updated_week = self.current_week
        
        # Update fighter ranks
        for i, fighter in enumerate(sorted_fighters):
            fighter.regional_rank = i + 1
    
    def get_regional_rankings(self, region: str, weight_class: str) -> RegionalRankings:
        """Get current regional rankings"""
        return self.rankings.get(region, {}).get(weight_class, RegionalRankings(region, weight_class))
    
    # ========================================================================
    # SIGNING
    # ========================================================================
    
    def get_signing_cost(self, fighter: AmateurFighter) -> int:
        """Get the cost to sign an amateur"""
        
        rating = fighter.overall_rating
        
        for (low, high), cost in SIGNING_COSTS.items():
            if low <= rating <= high:
                return cost
        
        return 10000  # Default
    
    # ========================================================================
    # ATTRIBUTE TRANSLATION
    # ========================================================================

    @staticmethod
    def translate_attrs_to_pro(amateur_attrs: Dict[str, int]) -> Dict[str, int]:
        """
        Translate amateur attribute keys to the canonical 17-attribute pro system.

        Amateur keys              → Pro keys
        ──────────────────────────────────────────────────────────
        boxing                   → boxing          (1:1)
        kicks                    → kicks            (1:1)
        clinch_striking          → clinch_striking  (1:1)
        striking_defense         → striking_defense (1:1)
        wrestling                → takedowns        (primary)
                                 → top_control      (derived: wrestling * 0.8)
        bjj                      → submissions      (primary)
                                 → guard            (derived: bjj * 0.85)
        takedown_defense         → takedown_defense (1:1)
        strength                 → strength         (1:1)
        speed                    → speed            (1:1)
        cardio                   → cardio           (1:1)
        chin                     → chin             (1:1)
        heart                    → heart            (1:1)
        fight_iq                 → fight_iq         (1:1)
        composure                → composure        (1:1)
        (derived)                → recovery         = cardio * 0.6 + heart * 0.4
        """
        a = amateur_attrs
        wrestling = a.get("wrestling", 50)
        bjj       = a.get("bjj", 50)
        cardio    = a.get("cardio", 50)
        heart     = a.get("heart", 50)

        pro = {
            # Physical
            "strength":          a.get("strength", 50),
            "speed":             a.get("speed", 50),
            "cardio":            cardio,
            "chin":              a.get("chin", 50),
            "recovery":          int(cardio * 0.60 + heart * 0.40),
            # Striking
            "boxing":            a.get("boxing", 50),
            "kicks":             a.get("kicks", 50),
            "clinch_striking":   a.get("clinch_striking", 50),
            "clinch_control":    a.get("clinch_control", 50),
            "striking_defense":  a.get("striking_defense", 50),
            # Grappling — translate wrestling/bjj
            "takedowns":         wrestling,
            "takedown_defense":  a.get("takedown_defense", 50),
            "top_control":       max(30, int(wrestling * 0.80)),
            "submissions":       bjj,
            "guard":             max(30, int(bjj * 0.85)),
            # Mental
            "heart":             heart,
            "fight_iq":          a.get("fight_iq", 50),
            "composure":         a.get("composure", 50),
        }
        # Cap all at 80 for amateurs entering pro ranks
        return {k: min(80, v) for k, v in pro.items()}

    def sign_amateur(self, fighter_id: str, camp_id: str) -> Optional[Dict[str, Any]]:
        """
        Sign an amateur to a pro contract.
        
        Returns dict with pro fighter data to be used by the game state,
        or None if signing fails.
        """
        
        fighter = self.get_amateur(fighter_id)
        
        if not fighter:
            return None
        
        if not fighter.is_pro_eligible:
            return None
        
        if not fighter.is_active:
            return None
        
        # Mark as signed (no longer active in amateur)
        fighter.is_active = False
        
        # Remove from pool
        if fighter.region in self.pools and fighter.weight_class in self.pools[fighter.region]:
            pool = self.pools[fighter.region][fighter.weight_class]
            self.pools[fighter.region][fighter.weight_class] = [
                f for f in pool if f.fighter_id != fighter_id
            ]
        
        # Create pro fighter data — translate amateur attrs to pro system
        pro_attrs = self.translate_attrs_to_pro(fighter.attributes)
        pro_overall = sum(pro_attrs.values()) // len(pro_attrs)

        pro_data = {
            "fighter_id": str(uuid.uuid4())[:8],  # New ID for pro career
            "name": fighter.name,
            "age": fighter.age,
            "weight_class": fighter.weight_class,
            "nationality": fighter.nationality,
            "camp_id": camp_id,

            # Translated 17-attribute pro system
            "attributes": pro_attrs,
            "overall_rating": pro_overall,

            # Pro record starts fresh, but we track amateur
            "pro_wins": 0,
            "pro_losses": 0,
            "amateur_wins": fighter.wins,
            "amateur_losses": fighter.losses,
            "amateur_record": fighter.record,

            # Potential (revealed on signing)
            "potential_ceiling": fighter.potential_ceiling,
            "potential_grade": fighter.potential_grade,

            # Style
            "fighting_style": fighter.fighting_style,
            "traits": fighter.traits,

            # Origin tracking
            "signed_from_amateur": True,
            "amateur_region": fighter.region,
            "amateur_tournament_wins": fighter.tournament_wins,
        }
        
        return pro_data
    
    # ========================================================================
    # WEEKLY PROCESSING
    # ========================================================================
    
    def process_week(self, week: int) -> Dict[str, Any]:
        """Process a week in the amateur system"""

        self.current_week = week

        # Tick weeks_in_amateur weekly — single source of truth
        for fighter in self.amateurs.values():
            if fighter.is_active and not fighter.turned_pro:
                fighter.weeks_in_amateur += 1

        events = {
            "tournaments_run": [],
            "newly_eligible": [],
            "retirements": [],
            "new_amateurs": [],
        }
        
        # Check for scheduled tournaments this week
        if week in self.scheduled_tournaments:
            for tournament in self.scheduled_tournaments[week]:
                results = self.simulate_tournament(tournament)
                events["tournaments_run"].append(results)
                events["newly_eligible"].extend(results.newly_eligible)
        
        # Age all amateurs (once per year)
        if week % 52 == 0:
            self._process_yearly_aging()
            events["retirements"] = self._process_retirements()
            events["new_amateurs"] = self._generate_new_amateurs()
        
        return events
    
    def _process_yearly_aging(self) -> None:
        """Age all amateurs by 1 year"""
        for fighter in self.amateurs.values():
            if fighter.is_active:
                fighter.age += 1
    
    def _process_retirements(self) -> List[str]:
        """Process retirements based on age and record"""
        
        retired = []
        
        for fighter in list(self.amateurs.values()):
            if not fighter.is_active:
                continue
            
            should_retire = False
            
            # Max age
            if fighter.age >= RETIREMENT_AGE_MAX:
                should_retire = True
            
            # Losing record at retirement age
            elif fighter.age >= RETIREMENT_AGE_LOSING:
                if fighter.losses > fighter.wins:
                    should_retire = True
            
            if should_retire:
                fighter.is_active = False
                retired.append(fighter.fighter_id)
                
                # Remove from pool
                if fighter.region in self.pools and fighter.weight_class in self.pools[fighter.region]:
                    self.pools[fighter.region][fighter.weight_class] = [
                        f for f in self.pools[fighter.region][fighter.weight_class]
                        if f.fighter_id != fighter.fighter_id
                    ]
        
        return retired
    
    def _generate_new_amateurs(self) -> List[str]:
        """Generate new amateur fighters each year (new talent entering the scene)"""
        
        new_fighters = []
        
        for region in REGIONS:
            for weight_class in WEIGHT_CLASSES:
                # Generate 2-4 new amateurs per division per region
                count = random.randint(2, NEW_AMATEURS_PER_DIVISION_PER_REGION + 1)
                
                for _ in range(count):
                    fighter = generate_amateur_fighter(
                        weight_class=weight_class,
                        region=region,
                        existing_names=self._used_names,
                        force_young=True,  # New amateurs are young
                    )
                    
                    self.pools[region][weight_class].append(fighter)
                    self.amateurs[fighter.fighter_id] = fighter
                    new_fighters.append(fighter.fighter_id)
        
        return new_fighters
    
    # ========================================================================
    # TOURNAMENT SCHEDULING
    # ========================================================================
    
    def schedule_year_tournaments(self, year: int, start_week: int = 1) -> None:
        """Schedule all tournaments for a year"""
        
        # 8 tournaments per region, spread across ~48 weeks
        # Each region gets tournaments every ~6 weeks
        
        for region_idx, region in enumerate(REGIONS):
            # Stagger regions so not all tournaments on same week
            region_offset = region_idx * 1  # 1 week apart
            
            for t_num in range(TOURNAMENTS_PER_YEAR):
                week = start_week + (t_num * WEEKS_BETWEEN_TOURNAMENTS) + region_offset
                
                # Schedule for all weight classes
                for weight_class in WEIGHT_CLASSES:
                    tournament = self.create_tournament(
                        region=region,
                        weight_class=weight_class,
                        week=week,
                        year=year,
                    )
                    
                    if tournament:
                        if week not in self.scheduled_tournaments:
                            self.scheduled_tournaments[week] = []
                        self.scheduled_tournaments[week].append(tournament)
    
    def get_upcoming_tournaments(self, current_week: int, weeks_ahead: int = 8) -> List[Tournament]:
        """Get tournaments scheduled in the next N weeks"""
        
        upcoming = []
        for week in range(current_week, current_week + weeks_ahead + 1):
            if week in self.scheduled_tournaments:
                upcoming.extend(self.scheduled_tournaments[week])
        
        return upcoming
    
    def get_tournaments_for_week(self, week: int) -> List[Tournament]:
        """Get all tournaments scheduled for a specific week"""
        return self.scheduled_tournaments.get(week, [])
    
    # ========================================================================
    # NATIONAL CHAMPIONSHIP
    # ========================================================================
    
    def create_national_championship(
        self,
        year: int,
        weight_class: str,
        week: int,
    ) -> Optional[NationalChampionship]:
        """Create the annual National Championship for a weight class"""
        
        # Get top 4 from each region
        qualifiers = {}
        all_qualified = []
        
        for region in REGIONS:
            rankings = self.get_regional_rankings(region, weight_class)
            top_4 = rankings.get_top_n(4)
            
            region_qualifiers = []
            for fighter_id, points in top_4:
                fighter = self.get_amateur(fighter_id)
                if fighter and fighter.is_active:
                    region_qualifiers.append(fighter_id)
                    all_qualified.append(fighter)
            
            qualifiers[region] = region_qualifiers
        
        if len(all_qualified) < 16:
            # Not enough qualifiers - shouldn't happen normally
            return None
        
        # Create the championship tournament
        nc = NationalChampionship(
            championship_id=str(uuid.uuid4())[:8],
            year=year,
            weight_class=weight_class,
            week=week,
            qualifiers=qualifiers,
        )
        
        # Create underlying tournament
        tournament = Tournament(
            tournament_id=f"NC-{nc.championship_id}",
            name=f"Year {year} National Championship - {weight_class}",
            region="National",  # Special designation
            weight_class=weight_class,
            week=week,
            year=year,
            fighters=[f.fighter_id for f in all_qualified[:16]],
            seeding=[f.fighter_id for f in sorted(all_qualified[:16], key=lambda x: -x.regional_points)],
        )
        
        # Create bracket
        self._create_bracket(tournament, all_qualified[:16])
        nc.tournament = tournament
        
        # Store
        if year not in self.national_championships:
            self.national_championships[year] = {}
        self.national_championships[year][weight_class] = nc
        
        return nc
    
    def simulate_national_championship(self, nc: NationalChampionship) -> Optional[TournamentResults]:
        """Simulate the National Championship"""
        
        if not nc.tournament:
            return None
        
        results = self.simulate_tournament(nc.tournament)
        
        nc.is_complete = True
        nc.national_champion_id = results.champion_id
        
        champion = self.get_amateur(results.champion_id)
        if champion:
            nc.national_champion_name = champion.name
            # National champion is automatically pro eligible
            if not champion.is_pro_eligible:
                champion.is_pro_eligible = True
                champion.eligibility_reason = "National Champion"
                results.newly_eligible.append(champion.fighter_id)
        
        return results
    
    def schedule_national_championships(self, year: int, week: int) -> None:
        """Schedule all National Championships for a year"""
        
        for weight_class in WEIGHT_CLASSES:
            nc = self.create_national_championship(year, weight_class, week)
            if nc and nc.tournament:
                if week not in self.scheduled_tournaments:
                    self.scheduled_tournaments[week] = []
                self.scheduled_tournaments[week].append(nc.tournament)
    
    # ========================================================================
    # SCOUTING (For player interaction)
    # ========================================================================
    
    def scout_amateur(
        self,
        fighter_id: str,
        scout_rating: int = 50,
    ) -> Dict[str, Any]:
        """
        Generate a scouting report for an amateur.
        
        Args:
            fighter_id: The amateur to scout
            scout_rating: Quality of scout (affects accuracy)
        
        Returns:
            Dict with scouting report data
        """
        
        fighter = self.get_amateur(fighter_id)
        if not fighter:
            return {}
        
        # Calculate projection error based on scout quality
        if scout_rating >= 90:
            error_range = 2
            confidence = "High"
        elif scout_rating >= 75:
            error_range = 5
            confidence = "Good"
        elif scout_rating >= 60:
            error_range = 10
            confidence = "Medium"
        else:
            error_range = 15
            confidence = "Low"
        
        error = random.randint(-error_range, error_range)
        
        # Projected values (with error)
        projected_overall = fighter.overall_rating + random.randint(-3, 3)
        projected_ceiling = fighter.potential_ceiling + error
        
        # Clamp projections
        projected_overall = max(40, min(85, projected_overall))
        projected_ceiling = max(50, min(99, projected_ceiling))
        
        # Determine what grade the scout sees
        if scout_rating >= 80:
            # Good scouts see true grade
            seen_grade = fighter.potential_grade
        else:
            # Lesser scouts might misjudge
            seen_grade = calculate_potential_grade(projected_ceiling)
        
        report = {
            "fighter_id": fighter.fighter_id,
            "name": fighter.name,
            "age": fighter.age,
            "weight_class": fighter.weight_class,
            "region": fighter.region,
            "nationality": fighter.nationality,
            "record": fighter.record,
            "fighting_style": fighter.fighting_style,
            
            # Visible stats
            "current_overall": fighter.overall_rating,
            
            # Projections (affected by scout quality)
            "projected_overall": projected_overall,
            "projected_ceiling": projected_ceiling,
            "projected_grade": seen_grade,
            "confidence": confidence,
            
            # Tournament history
            "tournament_wins": fighter.tournament_wins,
            "tournament_finals": fighter.tournament_finals,
            "regional_rank": fighter.regional_rank,
            "regional_points": fighter.regional_points,
            
            # Eligibility
            "is_pro_eligible": fighter.is_pro_eligible,
            "eligibility_reason": fighter.eligibility_reason,
            
            # Signing info
            "signing_cost": self.get_signing_cost(fighter),
            
            # Scout notes
            "strengths": self._get_strengths(fighter),
            "weaknesses": self._get_weaknesses(fighter),
        }
        
        # Elite scouts see traits
        if scout_rating >= 85 and fighter.traits:
            report["known_traits"] = fighter.traits
        
        return report
    
    def _get_strengths(self, fighter: AmateurFighter) -> List[str]:
        """Identify fighter's top 3 attributes"""
        
        attrs = fighter.attributes
        sorted_attrs = sorted(attrs.items(), key=lambda x: x[1], reverse=True)
        
        strengths = []
        for attr, value in sorted_attrs[:3]:
            if value >= 55:
                label = attr.replace("_", " ").title()
                strengths.append(f"{label}: {value}")
        
        return strengths
    
    def _get_weaknesses(self, fighter: AmateurFighter) -> List[str]:
        """Identify fighter's bottom 3 attributes"""
        
        attrs = fighter.attributes
        sorted_attrs = sorted(attrs.items(), key=lambda x: x[1])
        
        weaknesses = []
        for attr, value in sorted_attrs[:3]:
            if value <= 50:
                label = attr.replace("_", " ").title()
                weaknesses.append(f"{label}: {value}")
        
        return weaknesses
    
    # ========================================================================
    # HISTORY SIMULATION (For World Init)
    # ========================================================================
    
    def simulate_history(
        self,
        num_months: int = 12,
        start_week: int = 1,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Simulate amateur tournament history for world generation.
        
        This creates a realistic amateur scene with:
        - Tournament results over the specified period
        - Established rankings
        - Fighters with varied experience (1-8 fights)
        - Some graduates to pro (removed from pools)
        
        Args:
            num_months: Number of months of history (6-12 recommended)
            start_week: Starting week number
            verbose: Print progress updates
        
        Returns:
            Dict with summary of simulated history
        """
        if not self.pools:
            self.initialize_pools()
        
        # Calculate tournaments to run
        # 8 tournaments per year = ~1 every 6.5 weeks
        weeks_per_tournament = 52 // TOURNAMENTS_PER_YEAR  # ~6 weeks
        num_weeks = num_months * 4
        tournaments_per_region = max(1, num_weeks // weeks_per_tournament)
        
        total_tournaments = 0
        total_fights = 0
        pro_graduates = []
        
        if verbose:
            print(f"Simulating {num_months} months of amateur history...")
            print(f"Running ~{tournaments_per_region} tournaments per region")
        
        current_week = start_week
        
        # Run tournaments for each region
        for region in REGIONS:
            for t_num in range(tournaments_per_region):
                # Calculate which week this tournament is
                tournament_week = start_week + (t_num * weeks_per_tournament)
                
                # Run tournament for each weight class
                for weight_class in WEIGHT_CLASSES:
                    # Check if we have enough fighters
                    pool = self.pools.get(region, {}).get(weight_class, [])
                    if len(pool) < 16:
                        # Replenish pool
                        self._replenish_pool(region, weight_class)
                        pool = self.pools[region][weight_class]
                    
                    if len(pool) < 16:
                        continue
                    
                    # Create and run tournament
                    try:
                        tournament = self.create_tournament(
                            region=region,
                            weight_class=weight_class,
                            week=tournament_week,
                            year=1,  # Year is calculated internally based on week
                        )
                        
                        results = self.simulate_tournament(tournament)
                        total_tournaments += 1
                        total_fights += len(results.all_fights)
                        
                        # Track pro graduates
                        for fighter_id in results.newly_eligible:
                            fighter = self.get_amateur(fighter_id)
                            if fighter and fighter.is_pro_eligible:
                                # Ceiling-based departure — elite prospects
                                # leave faster than mid-tier ones.
                                _ceiling = getattr(fighter,
                                    'potential_ceiling', 70) or 70
                                if _ceiling >= 90:
                                    _depart_chance = 0.25
                                elif _ceiling >= 80:
                                    _depart_chance = 0.20
                                elif _ceiling >= 70:
                                    _depart_chance = 0.12
                                else:
                                    _depart_chance = 0.08
                                if random.random() < _depart_chance:
                                    pro_graduates.append({
                                        "fighter_id": fighter_id,
                                        "name": fighter.name,
                                        "region": region,
                                        "weight_class": weight_class,
                                        "rating": fighter.overall_rating,
                                        "record": f"{fighter.wins}-{fighter.losses}",
                                        "week": tournament_week,
                                    })
                                    # Don't remove yet - they can still compete
                                    fighter.turned_pro = True
                    except Exception as e:
                        if verbose:
                            print(f"  Error in {region} {weight_class}: {e}")
                        continue
                
                current_week = tournament_week
        
        # Update system week
        self.current_week = current_week
        
        # Set year based on weeks simulated
        if num_weeks >= 52:
            self.current_year = num_weeks // 52 + 1
        
        if verbose:
            print(f"  Completed {total_tournaments} tournaments")
            print(f"  Simulated {total_fights} fights")
            print(f"  {len(pro_graduates)} fighters turned pro")
        
        return {
            "tournaments_run": total_tournaments,
            "fights_simulated": total_fights,
            "pro_graduates": pro_graduates,
            "final_week": current_week,
            "regions_active": list(REGIONS),
        }
    
    def _replenish_pool(self, region: str, weight_class: str, target_size: int = 25) -> None:
        """Add new fighters to a depleted pool."""
        pool = self.pools.get(region, {}).get(weight_class, [])
        current_size = len(pool)
        
        if current_size >= target_size:
            return
        
        # Get region nationalities
        nationalities = REGION_NATIONALITIES.get(region, ["United States"])
        
        # Generate new amateurs
        for _ in range(target_size - current_size):
            nationality = random.choice(nationalities)
            fighter = generate_amateur_fighter(
                weight_class=weight_class,
                nationality=nationality,
            )
            
            # Check name uniqueness
            if fighter.name in self._used_names:
                # Regenerate with different name
                for _ in range(3):
                    fighter = generate_amateur_fighter(
                        weight_class=weight_class,
                        nationality=nationality,
                    )
                    if fighter.name not in self._used_names:
                        break
            
            self._used_names.add(fighter.name)
            fighter.region = region
            
            self.pools[region][weight_class].append(fighter)
            self.amateurs[fighter.fighter_id] = fighter
    
    def get_recent_graduates(self, num_months: int = 3) -> List[Dict[str, Any]]:
        """
        Get amateurs who recently turned pro (for AI camp signing).
        
        Args:
            num_months: Look back this many months
        
        Returns:
            List of pro-eligible fighters who turned pro
        """
        graduates = []
        cutoff_week = self.current_week - (num_months * 4)
        
        for fighter in self.amateurs.values():
            if hasattr(fighter, 'turned_pro') and fighter.turned_pro:
                # Check if they turned pro recently
                if fighter.is_pro_eligible:
                    graduates.append({
                        "fighter_id": fighter.fighter_id,
                        "name": fighter.name,
                        "region": fighter.region,
                        "weight_class": fighter.weight_class,
                        "rating": fighter.overall_rating,
                        "record": f"{fighter.wins}-{fighter.losses}",
                        "potential": fighter.potential,
                    })
        
        return graduates
    
    def get_top_prospects(
        self,
        weight_class: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 10,
    ) -> List['AmateurFighter']:
        """
        Get top amateur prospects (for scouting/news).
        
        Args:
            weight_class: Filter by division (optional)
            region: Filter by region (optional)
            limit: Max prospects to return
        
        Returns:
            List of top-rated eligible amateurs
        """
        prospects = []
        
        for fighter in self.amateurs.values():
            if not fighter.is_pro_eligible:
                continue
            
            if weight_class and fighter.weight_class != weight_class:
                continue
            
            if region and fighter.region != region:
                continue
            
            if hasattr(fighter, 'turned_pro') and fighter.turned_pro:
                continue
            
            prospects.append(fighter)
        
        # Sort by rating and potential
        prospects.sort(
            key=lambda f: (f.overall_rating * 0.6 + f.potential * 0.4),
            reverse=True
        )
        
        return prospects[:limit]
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the amateur system state"""
        
        return {
            "pools": {
                region: {
                    wc: [f.to_dict() for f in fighters]
                    for wc, fighters in weight_classes.items()
                }
                for region, weight_classes in self.pools.items()
            },
            "rankings": {
                region: {
                    wc: {
                        "rankings": rankings.rankings,
                        "tournaments_counted": rankings.tournaments_counted,
                        "last_updated_week": rankings.last_updated_week,
                    }
                    for wc, rankings in weight_classes.items()
                }
                for region, weight_classes in self.rankings.items()
            },
            "completed_tournaments": [t.to_dict() for t in self.completed_tournaments],
            "current_week": self.current_week,
            "current_year": self.current_year,
            "used_names": list(self._used_names),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AmateurSystem":
        """Deserialize amateur system state"""
        
        system = cls()
        
        # Restore pools
        for region, weight_classes in data.get("pools", {}).items():
            system.pools[region] = {}
            for wc, fighters in weight_classes.items():
                system.pools[region][wc] = []
                for f_data in fighters:
                    fighter = AmateurFighter.from_dict(f_data)
                    system.pools[region][wc].append(fighter)
                    system.amateurs[fighter.fighter_id] = fighter
        
        # Restore rankings
        for region, weight_classes in data.get("rankings", {}).items():
            system.rankings[region] = {}
            for wc, r_data in weight_classes.items():
                rankings = RegionalRankings(region=region, weight_class=wc)
                rankings.rankings = r_data.get("rankings", [])
                rankings.tournaments_counted = r_data.get("tournaments_counted", 0)
                rankings.last_updated_week = r_data.get("last_updated_week", 0)
                system.rankings[region][wc] = rankings
        
        system.current_week = data.get("current_week", 0)
        system.current_year = data.get("current_year", 1)
        system._used_names = set(data.get("used_names", []))

        # Restore completed tournaments — only the display-relevant
        # fields (champion/finalist/semis/quarters/circuit branding).
        # Bracket state and fight blow-by-blow are not restored since
        # they're not surfaced post-completion.
        for t_data in data.get("completed_tournaments", []) or []:
            try:
                t = Tournament(
                    tournament_id=t_data.get('tournament_id', ''),
                    name=t_data.get('name', ''),
                    region=t_data.get('region', ''),
                    weight_class=t_data.get('weight_class', ''),
                    week=t_data.get('week', 0),
                    year=t_data.get('year', 1),
                    circuit_name=t_data.get('circuit_name', ''),
                    city=t_data.get('city', ''),
                    is_complete=True,
                    champion_id=t_data.get('champion_id'),
                    finalist_id=t_data.get('finalist_id'),
                    semifinalists=list(t_data.get('semifinalists', []) or []),
                    quarterfinalists=list(t_data.get('quarterfinalists', []) or []),
                )
                system.completed_tournaments.append(t)
            except Exception:
                pass

        return system


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_amateur_system() -> AmateurSystem:
    """Create and initialize a new amateur system"""
    system = AmateurSystem()
    system.initialize_pools()
    return system


def get_region_for_nationality(nationality: str) -> str:
    """Get the tournament region for a nationality"""
    return NATIONALITY_TO_REGION.get(nationality, "Americas")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Constants
    "REGIONS",
    "WEIGHT_CLASSES",
    "NATIONALITY_TO_REGION",
    "REGION_NATIONALITIES",
    "BRACKET_SIZE",
    "TOURNAMENTS_PER_YEAR",
    
    # Data Classes
    "AmateurFighter",
    "Tournament",
    "TournamentFight",
    "TournamentResults",
    "RegionalRankings",
    "NationalChampionship",
    
    # Main System
    "AmateurSystem",
    
    # Functions
    "generate_amateur_fighter",
    "create_amateur_system",
    "get_region_for_nationality",
    "calculate_potential_grade",
]