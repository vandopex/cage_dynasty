# core/game_state.py
# Module 33: Game State Manager
# Lines: ~1100
#
# Central coordinator for all game systems and state.
# The single source of truth for the game world.

"""
Cage Dynasty - Game State Manager

Central manager that coordinates all game systems:
- Entity registries (fighters, camps, contracts)
- System coordination (world, rankings, rivalry)
- Player state management
- Game phase tracking
- Unified data access

Usage:
    from core.game_state import GameState, get_game_state
    
    # Initialize new game
    game = GameState()
    game.new_game(player_camp_name="Alpha MMA")
    
    # Or load existing
    game = GameState()
    game.load_game("save_slot_1")
    
    # Access systems
    player_camp = game.get_player_camp()
    rankings = game.get_rankings("Lightweight")
    
    # Advance time
    report = game.advance_week()
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from enum import Enum
import random

from core.events import emit
from core.calendar import GameCalendar

# Camp name generator (optional - falls back to simple generator if not available)
CAMP_GENERATOR_AVAILABLE = False
generate_world_camps = None
generate_camp_with_location = None
CampLocation = None
try:
    from systems.camp_generator import (
        generate_world_camps,
        generate_camp_with_location,
        generate_camp_name,
        CampLocation,
        get_random_city,
    )
    CAMP_GENERATOR_AVAILABLE = True
except ImportError:
    pass


# ============================================================================
# GAME PHASES
# ============================================================================

class GamePhase(Enum):
    """Current phase of the game"""
    MAIN_MENU = "main_menu"
    NEW_GAME_SETUP = "new_game_setup"
    PLAYING = "playing"
    EVENT_DAY = "event_day"
    FIGHT_NIGHT = "fight_night"
    BETWEEN_EVENTS = "between_events"
    GAME_OVER = "game_over"


class GameMode(Enum):
    """Game mode selection"""
    CAREER = "career"           # Build from scratch
    SANDBOX = "sandbox"         # Full control, no restrictions
    CHALLENGE = "challenge"     # Specific scenarios


# ============================================================================
# ENTITY REGISTRIES
# ============================================================================

@dataclass
class FighterRecord:
    """Lightweight fighter reference for the registry"""
    fighter_id: str
    name: str
    nickname: Optional[str] = None
    weight_class: str = ""
    # Body frame relative to weight class (1=very small, 10=very large).
    # Drives cut severity in the engine and division-move alerts.
    natural_weight_class: str = ""
    body_frame: int = 5
    # Personality — drives challenge acceptance + inbound offer frequency.
    # One of: Warrior / Competitor / Calculated / Hungry / Political.
    personality: str = ""
    camp_id: Optional[str] = None
    contract_id: Optional[str] = None
    is_champion: bool = False
    is_active: bool = True
    overall_rating: int = 50
    
    # Popularity (affects card positioning, sponsorships)
    popularity: int = 10  # 0-100
    
    # Quick stats for display
    wins: int = 0
    losses: int = 0
    draws: int = 0
    ko_wins: int = 0
    sub_wins: int = 0
    best_rank: int = 99  # Best 1-based rank ever held in this division (1=best, 99=never ranked)
    # Career FOTN awards — incremented by the bridge when this fighter is
    # part of the selected Fight of the Night. Prior to FOTN-PERSIST-FIX1
    # this was set as a dynamic attribute and dropped on every save round-trip.
    career_fotn_awards: int = 0

    # Fight history (list of fight records from world gen and gameplay)
    fight_history: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def record(self) -> str:
        """Format win-loss-draw record"""
        return f"{self.wins}-{self.losses}-{self.draws}"
    
    @property
    def display_name(self) -> str:
        """Full display name with nickname"""
        if self.nickname:
            return f'{self.name} "{self.nickname}"'
        return self.name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "name": self.name,
            "nickname": self.nickname,
            "weight_class": self.weight_class,
            "natural_weight_class": self.natural_weight_class,
            "body_frame": self.body_frame,
            "personality": self.personality,
            "camp_id": self.camp_id,
            "contract_id": self.contract_id,
            "is_champion": self.is_champion,
            "is_active": self.is_active,
            "overall_rating": self.overall_rating,
            "popularity": self.popularity,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "ko_wins": self.ko_wins,
            "sub_wins": self.sub_wins,
            "best_rank": self.best_rank,
            "career_fotn_awards": self.career_fotn_awards,
            "fight_history": self.fight_history.copy() if self.fight_history else [],
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FighterRecord":
        # Handle old saves that don't have new fields
        if "popularity" not in data:
            data["popularity"] = 10  # Default
        if "fight_history" not in data:
            data["fight_history"] = []  # Default
        if "career_fotn_awards" not in data:
            data["career_fotn_awards"] = 0  # FOTN-PERSIST-FIX1: forward-only default
        return cls(**data)


@dataclass
class CampRecord:
    """Lightweight camp reference for the registry"""
    camp_id: str
    name: str
    is_player: bool = False
    tier: str = "GARAGE"
    fighter_count: int = 0
    balance: int = 0
    reputation: int = 50
    
    # Location data
    location: str = ""   # single string e.g. "Las Vegas, NV"
    city:     str = ""
    country:  str = ""
    region:   str = ""
    
    # Quick stats
    total_wins: int = 0
    total_losses: int = 0
    titles_held: int = 0

    # Ship AI-Coach: dominant coach type derived from fighter styles
    # at world-gen. Read by AI training loop for style-fit bonus.
    # Empty for legacy saves / camps without coach-type assignment.
    dominant_coach_type: str = ""

    tier_since_week: int = 0

    @property
    def location_str(self) -> str:
        """Get formatted location string"""
        if self.location:
            return self.location
        if self.city and self.country:
            return f"{self.city}, {self.country}"
        return self.city or self.country or "Unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "camp_id": self.camp_id,
            "name": self.name,
            "is_player": self.is_player,
            "tier": self.tier,
            "fighter_count": self.fighter_count,
            "balance": self.balance,
            "reputation": self.reputation,
            "location": self.location,
            "city": self.city,
            "country": self.country,
            "region": self.region,
            "total_wins": self.total_wins,
            "total_losses": self.total_losses,
            "titles_held": self.titles_held,
            "dominant_coach_type": self.dominant_coach_type,
            "tier_since_week": self.tier_since_week,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampRecord":
        # Handle old saves without location data
        valid_fields = {
            "camp_id", "name", "is_player", "tier", "fighter_count",
            "balance", "reputation", "location", "city", "country", "region",
            "total_wins", "total_losses", "titles_held",
            "dominant_coach_type", "tier_since_week",
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass 
class DivisionState:
    """State of a single weight class division"""
    weight_class: str
    champion_id: Optional[str] = None
    champion_name: Optional[str] = None
    interim_champion_id: Optional[str] = None
    rankings: List[str] = field(default_factory=list)  # Fighter IDs in order
    fighter_count: int = 0
    
    def get_top_contender(self) -> Optional[str]:
        """Get #1 ranked contender"""
        return self.rankings[0] if self.rankings else None
    
    def get_top_n(self, n: int = 5) -> List[str]:
        """Get top N ranked fighters"""
        return self.rankings[:n]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "weight_class": self.weight_class,
            "champion_id": self.champion_id,
            "champion_name": self.champion_name,
            "interim_champion_id": self.interim_champion_id,
            "rankings": self.rankings.copy(),
            "fighter_count": self.fighter_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DivisionState":
        return cls(**data)


# ============================================================================
# NICKNAMES — earned, not assigned. Pool is applied via the threshold gate in
# game_bridge._apply_post_fight_camp_record (post-fight earning) and the
# one-shot backfill in web_load (legacy saves). New fighters start with
# nickname=None and earn one upon reaching ≥2 wins AND ≥3 total fights —
# "you earn it by performing." The threshold IS the no-nickname gate, so
# the pool itself is pure positives (no None entries). Generic nicknames
# only — no culturally-bound entries so AI country diversity doesn't feel
# weird (no "El Toro" on a Russian, no "Shogun" on a Brazilian).
# ============================================================================

NICKNAMES_POOL = [
    # ── Originals (dramatic + understated mix) ─────────────────────────────
    "The Reaper",     "Diesel",          "The Hammer",
    "The Pitbull",    "The Phoenix",     "The Beast",
    "Thunder",        "Lightning",       "The Bull",
    "Bones",          "Ice",             "Showtime",
    "Steel",          "Quicksilver",     "The Natural",
    "The Surgeon",    "The Technician",  "The Sniper",
    "The Predator",   "The Anvil",

    # ── Warrior / Weapon (25) ──────────────────────────────────────────────
    "The Gladiator",  "The Spartan",     "The Viking",
    "The Samurai",    "The Centurion",   "The Arsenal",
    "The Artillery",  "Howitzer",        "The Missile",
    "The Cannon",     "The Sword",       "The Axe",
    "The Mace",       "The Dagger",      "The Spear",
    "The Wrecking Ball", "The Sledgehammer", "The Jackhammer",
    "The Chainsaw",   "The Hatchet",     "The Bazooka",
    "The Grenade",    "The Caliber",     "The Roundhouse",
    "The Haymaker",

    # ── Animal Kingdom (35) ────────────────────────────────────────────────
    "The Wolf",       "The Coyote",      "The Fox",
    "The Hyena",      "The Jackal",      "The Panther",
    "The Leopard",    "The Cheetah",     "The Lynx",
    "The Cougar",     "The Rhino",       "The Hippo",
    "The Buffalo",    "The Bison",       "The Ox",
    "The Eagle",      "The Hawk",        "The Falcon",
    "The Vulture",    "The Owl",         "The Shark",
    "The Barracuda",  "The Pike",        "The Stingray",
    "The Octopus",    "The Spider",      "The Scorpion",
    "The Centipede",  "The Wasp",        "The Hornet",
    "The Wolverine",  "The Badger",      "The Weasel",
    "The Ferret",     "The Mongoose",

    # ── Natural Phenomena (25) ─────────────────────────────────────────────
    "The Hurricane",  "The Typhoon",     "The Cyclone",
    "The Tornado",    "The Twister",     "The Tsunami",
    "The Tide",       "The Current",     "The Whirlpool",
    "The Riptide",    "The Avalanche",   "The Landslide",
    "The Quake",      "The Tremor",      "The Volcano",
    "The Blizzard",   "The Hailstorm",   "The Thunderstorm",
    "The Monsoon",    "The Dust Storm",  "The Eclipse",
    "The Comet",      "The Meteor",      "The Gravity",
    "The Void",

    # ── Personality / Traits (29) ──────────────────────────────────────────
    "The Menace",     "The Scourge",     "The Plague",
    "The Pestilence", "The Ruin",        "The Enforcer",
    "The Executioner","The Judge",       "The Jury",
    "The Verdict",    "The Ghost",       "The Shadow",
    "The Spectre",    "The Phantom",     "The Wraith",
    "The Prodigy",    "The Phenom",      "The Sensation",
    "The Marvel",     "The Wonder",      "The Savage",
    "The Barbarian",  "The Brute",       "The Monster",
    "The Silent One", "The Quiet Storm", "The Calm",
    "The Serpent",    "The Viper",

    # ── Physical Attribute (23) ────────────────────────────────────────────
    # ("Pitbull" dropped — stylistic dup with original "The Pitbull")
    "Tower",          "The Giant",       "The Colossus",
    "The Mountain",   "The Boulder",     "The Rock",
    "The Stone",      "The Granite",     "The Marble",
    "The Concrete",   "Stretch",         "The Lanky",
    "The Spider Monkey", "The Rubber Band", "Bulldog",
    "Rottweiler",     "Doberman",        "Mastiff",
    "The Hulk",       "The Tank",        "The Bulldozer",
    "The Freight Train", "The Locomotive",

    # ── Technical / Skill-Based (24) ───────────────────────────────────────
    "The Matador",    "The Dancer",      "The Artist",
    "The Sculptor",   "The Architect",   "The Mechanic",
    "The Engineer",   "The Professor",   "The Doctor",
    "The Chess Master", "The Strategist", "The General",
    "The Admiral",    "The Commander",   "The Clinch",
    "The Grappler",   "The Mat Shark",   "The Ground King",
    "The Ceiling",    "The Stick",       "The Move",
    "The Flow",       "The Rhythm",      "The Tempo",

    # ── Mysterious / Intimidating (24) ─────────────────────────────────────
    "The Omen",       "The Harbinger",   "The Prophet",
    "The Seer",       "The Oracle",      "The Revenant",
    "The Abomination","The Aberration",  "The Anomaly",
    "The Paradox",    "The Abyss",       "The Depths",
    "The Below",      "The Hollow",      "The Crypt",
    "The Tomb",       "The Grave",       "The Cemetery",
    "The Epitaph",    "Chains",          "Shackles",
    "The Cage",       "The Cell",        "The Prisoner",

    # ── Short / Flavor (25) ────────────────────────────────────────────────
    "Razor",          "Blade",           "Edge",
    "Cut",            "Slice",           "Smash",
    "Crush",          "Slam",            "Bash",
    "Clash",          "Swift",           "Quick",
    "Flash",          "Blink",           "Flicker",
    "Grim",           "Grit",            "Grind",
    "Gravel",         "Gristle",         "Clutch",
    "Clamp",          "Crimp",           "Crank",
    "Crack",
]


# ============================================================================
# GAME SETTINGS
# ============================================================================

@dataclass
class GameSettings:
    """Player-configurable game settings"""
    # Difficulty
    difficulty: str = "normal"  # easy, normal, hard, legendary
    
    # Simulation speed
    auto_advance: bool = False
    weeks_per_advance: int = 1
    
    # Display options
    show_fighter_ratings: bool = True
    show_fight_predictions: bool = True
    detailed_fight_commentary: bool = True
    
    # AI behavior
    ai_aggression: float = 1.0  # 0.5-1.5
    prospect_frequency: float = 1.0
    injury_frequency: float = 1.0
    
    # Game rules
    allow_cross_division: bool = False
    realistic_aging: bool = True
    permadeath: bool = False  # Fighters can die from damage
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "difficulty": self.difficulty,
            "auto_advance": self.auto_advance,
            "weeks_per_advance": self.weeks_per_advance,
            "show_fighter_ratings": self.show_fighter_ratings,
            "show_fight_predictions": self.show_fight_predictions,
            "detailed_fight_commentary": self.detailed_fight_commentary,
            "ai_aggression": self.ai_aggression,
            "prospect_frequency": self.prospect_frequency,
            "injury_frequency": self.injury_frequency,
            "allow_cross_division": self.allow_cross_division,
            "realistic_aging": self.realistic_aging,
            "permadeath": self.permadeath,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameSettings":
        return cls(**data)


# ============================================================================
# GAME STATE MANAGER
# ============================================================================

class GameState:
    """
    Central game state manager.
    
    Coordinates all game systems and provides unified access to game data.
    This is the single source of truth for the game world.
    """
    
    # Weight classes in order
    WEIGHT_CLASSES = [
        "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
        "Lightweight", "Welterweight", "Middleweight", 
        "Light Heavyweight", "Heavyweight"
    ]
    
    def __init__(self):
        # Game metadata
        self.game_id: str = ""
        self.game_name: str = ""
        self.created_date: str = ""
        self.last_played: str = ""
        self.play_time_minutes: int = 0
        
        # Game state
        self.phase: GamePhase = GamePhase.MAIN_MENU
        self.mode: GameMode = GameMode.CAREER
        self.settings: GameSettings = GameSettings()
        
        # Calendar
        self.calendar: GameCalendar = GameCalendar()
        self.week_number: int = 0
        
        # Player state
        self.player_camp_id: Optional[str] = None
        self.player_name: str = ""
        
        # Entity registries (lightweight references)
        self.fighters: Dict[str, FighterRecord] = {}
        self.camps: Dict[str, CampRecord] = {}
        self.divisions: Dict[str, DivisionState] = {}
        
        # ID tracking
        self._next_fighter_id: int = 1
        self._next_camp_id: int = 1
        self._next_event_id: int = 1
        self._next_contract_id: int = 1
        
        # Free agents pool
        self.free_agents: Set[str] = set()
        
        # Retired fighters (for hall of fame, history)
        self.retired_fighters: Set[str] = set()
        
        # Active contracts (fighter_id -> contract_id)
        self.active_contracts: Dict[str, str] = {}
        
        # Scheduled events (simplified - full events in world simulation)
        self.upcoming_event_ids: List[str] = []
        
        # Statistics tracking
        self.total_fights_simulated: int = 0
        self.total_events_held: int = 0
        self.title_changes: int = 0
        
        # System references (set during initialization)
        self._world_simulation: Optional[Any] = None
        self._ranking_system: Optional[Any] = None
        self._rivalry_system: Optional[Any] = None
        self._economy_system: Optional[Any] = None
        
        # Full entity data storage (for detailed operations)
        # These store the complete objects, not just references
        self._fighter_data: Dict[str, Dict[str, Any]] = {}
        self._camp_data: Dict[str, Dict[str, Any]] = {}
        self._contract_data: Dict[str, Dict[str, Any]] = {}
        
        # Initialize divisions
        self._initialize_divisions()
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def _initialize_divisions(self) -> None:
        """Initialize all weight class divisions"""
        for wc in self.WEIGHT_CLASSES:
            self.divisions[wc] = DivisionState(weight_class=wc)
    
    def new_game(
        self,
        player_camp_name: str,
        player_name: str = "Player",
        mode: GameMode = GameMode.CAREER,
        settings: Optional[GameSettings] = None,
        starting_year: int = 2025,
    ) -> None:
        """
        Initialize a new game.
        
        Args:
            player_camp_name: Name of the player's camp
            player_name: Player's name/handle
            mode: Game mode
            settings: Optional custom settings
            starting_year: Year to start the game
        """
        import uuid
        from datetime import datetime
        
        # Generate game ID
        self.game_id = str(uuid.uuid4())[:8]
        self.game_name = f"{player_camp_name} - {starting_year}"
        self.created_date = datetime.now().isoformat()
        self.last_played = self.created_date
        
        # Set mode and settings
        self.mode = mode
        if settings:
            self.settings = settings
        
        # Initialize calendar
        from datetime import date as dt_date
        self.calendar = GameCalendar(start_date=dt_date(starting_year, 1, 1))
        self.week_number = 0
        
        # Store player info
        self.player_name = player_name
        
        # Create player camp
        self.player_camp_id = self._create_camp(
            name=player_camp_name,
            is_player=True,
            tier="GARAGE",
            balance=50000,  # Starting balance for player camp
        )
        
        # Set game phase
        self.phase = GamePhase.PLAYING
        
        emit("game_started", {
            "game_id": self.game_id,
            "player_camp": player_camp_name,
            "mode": mode.value,
        })
    
    def initialize_world(
        self,
        num_ai_camps: int = 10,
        fighters_per_division: int = 15,
        generate_history: bool = False,
    ) -> Dict[str, int]:
        """
        Populate the world with AI camps and fighters.
        
        Args:
            num_ai_camps: Number of AI camps to create
            fighters_per_division: Fighters per weight class
            generate_history: Whether to simulate past history
            
        Returns:
            Dictionary of creation counts
        """
        counts = {
            "camps": 0,
            "fighters": 0,
            "contracts": 0,
        }
        
        # Create AI camps with varied personalities and locations
        if CAMP_GENERATOR_AVAILABLE and generate_world_camps:
            # Use the new camp generator with real cities
            camp_data = generate_world_camps(num_ai_camps)
            for name, location in camp_data:
                self._create_camp(
                    name=name,
                    is_player=False,
                    tier=random.choice(["LOCAL", "REGIONAL", "NATIONAL"]),
                    balance=random.randint(30000, 200000),
                    city=location.city,
                    country=location.country,
                    region=location.region,
                )
                counts["camps"] += 1
        else:
            # Fallback to simple name generator
            camp_names = self._generate_camp_names(num_ai_camps)
            for name in camp_names:
                self._create_camp(
                    name=name,
                    is_player=False,
                    tier=random.choice(["LOCAL", "REGIONAL", "NATIONAL"]),
                    balance=random.randint(30000, 200000),
                )
                counts["camps"] += 1
        
        # Generate fighters for each division
        for weight_class in self.WEIGHT_CLASSES:
            for _ in range(fighters_per_division):
                fighter_id = self._generate_fighter(weight_class)
                counts["fighters"] += 1
                
                # Randomly assign some to camps
                if random.random() < 0.7:  # 70% signed
                    # Pick a random camp (including player for sandbox)
                    camp_ids = list(self.camps.keys())
                    if self.mode == GameMode.CAREER:
                        # Don't give player free fighters in career
                        camp_ids = [c for c in camp_ids 
                                   if c != self.player_camp_id]
                    
                    if camp_ids:
                        camp_id = random.choice(camp_ids)
                        self._sign_fighter_to_camp(fighter_id, camp_id)
                        counts["contracts"] += 1
                else:
                    self.free_agents.add(fighter_id)
        
        # Set initial rankings
        self._initialize_rankings()
        
        # Generate some initial history if requested
        if generate_history:
            self._generate_initial_history()
        
        emit("world_initialized", counts)
        
        return counts
    
    def _generate_camp_names(self, count: int) -> List[str]:
        """Generate unique AI camp names"""
        prefixes = [
            "Iron", "Steel", "Elite", "Prime", "Alpha", "Apex", "Victory",
            "Champion", "Thunder", "Storm", "Tiger", "Dragon", "Phoenix",
            "Black", "Red", "Golden", "Silver", "Diamond", "Platinum",
            "Ultimate", "Supreme", "Royal", "Imperial", "Warrior", "Legend",
        ]
        suffixes = [
            "MMA", "Fight Team", "Combat Club", "Academy", "Gym",
            "Training Center", "Athletics", "Martial Arts", "Fighting",
            "Performance", "Combat Sports", "Fight Factory", "Dojo",
        ]
        
        names = []
        used = set()
        
        while len(names) < count:
            name = f"{random.choice(prefixes)} {random.choice(suffixes)}"
            if name not in used:
                used.add(name)
                names.append(name)
        
        return names
    
    def _generate_fighter(self, weight_class: str) -> str:
        """Generate a new fighter and return their ID"""
        fighter_id = f"fighter_{self._next_fighter_id}"
        self._next_fighter_id += 1
        
        # Name generation — single source of truth: name_database.py
        # Fallback pool is large enough to handle 225 fighters with near-zero collisions
        _FALLBACK_FIRST = [
            "Alex","Mike","John","Chris","Jake","Ryan","Tyler","Brandon","Nick","Matt",
            "Dan","James","Carlos","Diego","Rafael","Paulo","Jose","Luis","David","Marcus",
            "Kevin","Brian","Sean","Andre","Victor","Roberto","Felipe","Eduardo","Rodrigo",
            "Alexander","Dmitri","Ivan","Nikita","Sergei","Anton","George","Patrick",
            "Connor","Shavkat","Arman","Islam","Kamaru","Israel","Francis","Tai","Robert",
            "Jacob","Luke","Tyson","Jan","Magomed","Khamzat","Dricus","Jairzinho","Cyril",
            "Santiago","Lautaro","Lucas","Thiago","Gabriel","Leonardo","Vitor","Anderson",
            "Caio","Jerome","Cory","Julian","Dominick","Aljamain","Merab","Henry","Eric",
        ]
        _FALLBACK_LAST = [
            "Smith","Johnson","Williams","Brown","Jones","Garcia","Martinez","Rodriguez",
            "Davis","Miller","Silva","Santos","Costa","Oliveira","Ferreira","Lima",
            "Pereira","Wilson","Anderson","Taylor","Moore","Jackson","Harris","Clark",
            "Lewis","Robinson","Walker","Young","Volkov","Makhachev","Thompson","White",
            "Nelson","Baker","Rivera","Campbell","Usman","Adesanya","Tuivasa","Whittaker",
            "Blachowicz","Ankalaev","Chimaev","Rozenstruik","Gane","Almeida","Carvalho",
            "Machado","Barbosa","Nogueira","Rakhmonov","Mirzaev","Volkanovski","Vettori",
            "Romero","Weidman","Rockhold","Gastelum","Souza","Mousasi","Overeem","Arlovski",
        ]
        country = "United States"
        first   = random.choice(_FALLBACK_FIRST)
        last    = random.choice(_FALLBACK_LAST)
        try:
            from name_database import COUNTRY_NAMES as _ND, get_random_country as _GRC
            country = _GRC()
            _pool   = _ND.get(country, _ND.get("United States", {}))
            if _pool.get("first") and _pool.get("last"):
                first = random.choice(_pool["first"])
                last  = random.choice(_pool["last"])
        except Exception:
            pass  # Fallback values already set above
        name = f"{first} {last}"
        rating = random.gauss(60, 15)
        rating = max(35, min(95, int(rating)))
        
        # Create record
        record = FighterRecord(
            fighter_id=fighter_id,
            name=name,
            weight_class=weight_class,
            overall_rating=rating,
        )
        
        self.fighters[fighter_id] = record
        
        # Store full data
        self._fighter_data[fighter_id] = {
            "id": fighter_id,
            "name": name,
            "weight_class": weight_class,
            "rating": rating,
            "age": random.randint(21, 35),
            "country":      country,
        }
        
        emit("fighter_created", {"fighter_id": fighter_id, "name": name})
        
        return fighter_id
    
    def _create_camp(
        self,
        name: str,
        is_player: bool = False,
        tier: str = "GARAGE",
        balance: int = 50000,
        city: str = "",
        country: str = "",
        region: str = "",
    ) -> str:
        """Create a new camp and return its ID"""
        camp_id = f"camp_{self._next_camp_id}"
        self._next_camp_id += 1
        
        record = CampRecord(
            camp_id=camp_id,
            name=name,
            is_player=is_player,
            tier=tier,
            balance=balance,
            city=city,
            country=country,
            region=region,
        )
        
        self.camps[camp_id] = record
        
        # Store full data
        self._camp_data[camp_id] = {
            "id": camp_id,
            "name": name,
            "is_player": is_player,
            "tier": tier,
            "balance": balance,
            "city": city,
            "country": country,
            "region": region,
            "fighters": [],
        }
        
        emit("camp_created", {"camp_id": camp_id, "name": name})
        
        return camp_id
    
    def _sign_fighter_to_camp(
        self,
        fighter_id: str,
        camp_id: str,
        salary: Optional[int] = None,
    ) -> Optional[str]:
        """Sign a fighter to a camp, return contract ID"""
        if fighter_id not in self.fighters:
            return None
        if camp_id not in self.camps:
            return None
        
        fighter = self.fighters[fighter_id]
        camp = self.camps[camp_id]
        
        # Create contract
        contract_id = f"contract_{self._next_contract_id}"
        self._next_contract_id += 1
        
        if salary is None:
            # Base salary on rating
            salary = fighter.overall_rating * 100
        
        # Update records
        fighter.camp_id = camp_id
        fighter.contract_id = contract_id
        camp.fighter_count += 1
        
        # Remove from free agents
        self.free_agents.discard(fighter_id)
        
        # Store contract
        self.active_contracts[fighter_id] = contract_id
        self._contract_data[contract_id] = {
            "id": contract_id,
            "fighter_id": fighter_id,
            "camp_id": camp_id,
            "salary": salary,
            "fights_remaining": random.randint(3, 6),
        }
        
        # Update camp data
        if camp_id in self._camp_data:
            self._camp_data[camp_id]["fighters"].append(fighter_id)
        
        return contract_id
    
    def _initialize_rankings(self) -> None:
        """Set initial rankings for all divisions"""
        for weight_class in self.WEIGHT_CLASSES:
            division = self.divisions[weight_class]
            
            # Get fighters in this division
            division_fighters = [
                f for f in self.fighters.values()
                if f.weight_class == weight_class and f.is_active
            ]
            
            # Sort by rating
            division_fighters.sort(
                key=lambda x: x.overall_rating,
                reverse=True
            )
            
            # Set champion (top rated)
            if division_fighters:
                champion = division_fighters[0]
                champion.is_champion = True
                division.champion_id = champion.fighter_id
                division.champion_name = champion.name
                
                # Set rankings (exclude champion)
                division.rankings = [
                    f.fighter_id for f in division_fighters[1:16]
                ]
            
            division.fighter_count = len(division_fighters)
    
    def _generate_initial_history(self) -> None:
        """Generate some fight history for realism"""
        # Simplified - give random records to fighters
        for fighter in self.fighters.values():
            if random.random() < 0.8:  # 80% have some history
                total_fights = random.randint(1, 15)
                win_rate = random.uniform(0.3, 0.8)
                
                fighter.wins = int(total_fights * win_rate)
                fighter.losses = total_fights - fighter.wins
                fighter.ko_wins = int(fighter.wins * random.uniform(0.2, 0.5))
                fighter.sub_wins = int(fighter.wins * random.uniform(0.1, 0.3))
    
    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------
    
    def _on_fighter_retired(self, data: Dict[str, Any]) -> None:
        """Handle fighter retirement"""
        fighter_id = data.get("fighter_id")
        if fighter_id and fighter_id in self.fighters:
            self.fighters[fighter_id].is_active = False
            self.retired_fighters.add(fighter_id)
            self.free_agents.discard(fighter_id)
    
    def _on_title_changed(self, data: Dict[str, Any]) -> None:
        """Handle title change"""
        self.title_changes += 1
        
        weight_class = data.get("weight_class")
        new_champion_id = data.get("new_champion_id")
        old_champion_id = data.get("old_champion_id")
        
        if weight_class in self.divisions:
            division = self.divisions[weight_class]
            
            # Update old champion
            if old_champion_id and old_champion_id in self.fighters:
                self.fighters[old_champion_id].is_champion = False
            
            # Update new champion
            if new_champion_id and new_champion_id in self.fighters:
                self.fighters[new_champion_id].is_champion = True
                division.champion_id = new_champion_id
                division.champion_name = self.fighters[new_champion_id].name
    
    def _on_fight_completed(self, data: Dict[str, Any]) -> None:
        """Handle fight completion"""
        self.total_fights_simulated += 1
        
        winner_id = data.get("winner_id")
        loser_id = data.get("loser_id")
        method = data.get("method", "DEC")
        
        # Update records
        if winner_id and winner_id in self.fighters:
            self.fighters[winner_id].wins += 1
            if method in ["KO", "TKO"]:
                self.fighters[winner_id].ko_wins += 1
            elif method == "SUB":
                self.fighters[winner_id].sub_wins += 1
        
        if loser_id and loser_id in self.fighters:
            self.fighters[loser_id].losses += 1
    
    # -------------------------------------------------------------------------
    # Time Management
    # -------------------------------------------------------------------------
    
    def advance_week(self) -> Dict[str, Any]:
        """
        Advance the game by one week.
        
        Returns:
            Summary of the week's events
        """
        self.week_number += 1
        new_date = self.calendar.advance_week()
        
        summary = {
            "week": self.week_number,
            "date": f"Week {self.week_number}",
            "events": [],
            "fights": 0,
            "signings": 0,
            "releases": 0,
            "injuries": 0,
            "retirements": 0,
        }
        
        # Process world simulation if available
        if self._world_simulation:
            report = self._world_simulation.advance_week()
            summary["fights"] = report.fights_completed
            summary["events"] = report.events_held
        
        # Monthly processing (first week of month)
        if self.calendar.current_date.day <= 7:
            self._process_monthly()
        
        emit("week_advanced", summary)
        
        return summary
    
    def advance_to_event(self) -> List[Dict[str, Any]]:
        """Advance to the next scheduled event"""
        summaries = []
        
        # Would check world simulation for next event
        # For now, advance 4 weeks
        for _ in range(4):
            summaries.append(self.advance_week())
        
        return summaries
    
    def _process_monthly(self) -> None:
        """Process monthly events"""
        emit("month_started", {
            "month": self.calendar.current_date.month,
            "year": self.calendar.current_date.year,
        })
        
        # Could process:
        # - Aging
        # - Contract payments
        # - Ranking updates
        # - Camp expenses
    
    # -------------------------------------------------------------------------
    # Data Access - Player
    # -------------------------------------------------------------------------
    
    def get_player_camp(self) -> Optional[CampRecord]:
        """Get the player's camp record"""
        if self.player_camp_id:
            return self.camps.get(self.player_camp_id)
        return None
    
    def get_player_fighters(self) -> List[FighterRecord]:
        """Get all fighters in player's camp"""
        if not self.player_camp_id:
            return []
        return [
            f for f in self.fighters.values()
            if f.camp_id == self.player_camp_id and f.is_active
        ]
    
    def is_player_camp(self, camp_id: str) -> bool:
        """Check if a camp is the player's"""
        return camp_id == self.player_camp_id
    
    # -------------------------------------------------------------------------
    # Data Access - Fighters
    # -------------------------------------------------------------------------
    
    def get_fighter(self, fighter_id: str) -> Optional[FighterRecord]:
        """Get a fighter by ID"""
        return self.fighters.get(fighter_id)
    
    def get_fighter_data(self, fighter_id: str) -> Optional[Dict[str, Any]]:
        """Get full fighter data"""
        return self._fighter_data.get(fighter_id)
    
    def get_fighters_by_weight_class(self, weight_class: str) -> List[FighterRecord]:
        """Get all fighters in a weight class"""
        return [
            f for f in self.fighters.values()
            if f.weight_class == weight_class and f.is_active
        ]
    
    def get_free_agents(self, weight_class: Optional[str] = None) -> List[FighterRecord]:
        """Get available free agents"""
        agents = [
            self.fighters[fid] for fid in self.free_agents
            if fid in self.fighters and self.fighters[fid].is_active
        ]
        
        if weight_class:
            agents = [f for f in agents if f.weight_class == weight_class]
        
        return sorted(agents, key=lambda x: x.overall_rating, reverse=True)
    
    def search_fighters(
        self,
        name: Optional[str] = None,
        weight_class: Optional[str] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        camp_id: Optional[str] = None,
        free_agent_only: bool = False,
    ) -> List[FighterRecord]:
        """Search fighters with filters"""
        results = list(self.fighters.values())
        
        if name:
            name_lower = name.lower()
            results = [f for f in results if name_lower in f.name.lower()]
        
        if weight_class:
            results = [f for f in results if f.weight_class == weight_class]
        
        if min_rating is not None:
            results = [f for f in results if f.overall_rating >= min_rating]
        
        if max_rating is not None:
            results = [f for f in results if f.overall_rating <= max_rating]
        
        if camp_id:
            results = [f for f in results if f.camp_id == camp_id]
        
        if free_agent_only:
            results = [f for f in results if f.fighter_id in self.free_agents]
        
        return results
    
    # -------------------------------------------------------------------------
    # Data Access - Camps
    # -------------------------------------------------------------------------
    
    def get_camp(self, camp_id: str) -> Optional[CampRecord]:
        """Get a camp by ID"""
        return self.camps.get(camp_id)
    
    def get_camp_fighters(self, camp_id: str) -> List[FighterRecord]:
        """Get all fighters in a camp"""
        return [
            f for f in self.fighters.values()
            if f.camp_id == camp_id and f.is_active
        ]
    
    def get_all_camps(self, include_player: bool = True) -> List[CampRecord]:
        """Get all camps"""
        camps = list(self.camps.values())
        if not include_player and self.player_camp_id:
            camps = [c for c in camps if c.camp_id != self.player_camp_id]
        return camps
    
    # -------------------------------------------------------------------------
    # Data Access - Divisions
    # -------------------------------------------------------------------------
    
    def get_division(self, weight_class: str) -> Optional[DivisionState]:
        """Get division state"""
        return self.divisions.get(weight_class)
    
    def get_champion(self, weight_class: str) -> Optional[FighterRecord]:
        """Get champion of a division"""
        division = self.divisions.get(weight_class)
        if division and division.champion_id:
            return self.fighters.get(division.champion_id)
        return None
    
    def get_rankings(self, weight_class: str, top_n: int = 15) -> List[FighterRecord]:
        """Get ranked fighters in a division"""
        division = self.divisions.get(weight_class)
        if not division:
            return []
        
        return [
            self.fighters[fid] for fid in division.rankings[:top_n]
            if fid in self.fighters
        ]
    
    def get_all_champions(self) -> Dict[str, FighterRecord]:
        """Get all current champions"""
        champions = {}
        for wc, division in self.divisions.items():
            if division.champion_id and division.champion_id in self.fighters:
                champions[wc] = self.fighters[division.champion_id]
        return champions
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def get_game_stats(self) -> Dict[str, Any]:
        """Get overall game statistics"""
        active_fighters = sum(1 for f in self.fighters.values() if f.is_active)
        
        return {
            "game_id": self.game_id,
            "week_number": self.week_number,
            "current_date": self.calendar.current_date.format("long"),
            "total_fighters": len(self.fighters),
            "active_fighters": active_fighters,
            "retired_fighters": len(self.retired_fighters),
            "free_agents": len(self.free_agents),
            "total_camps": len(self.camps),
            "total_fights": self.total_fights_simulated,
            "total_events": self.total_events_held,
            "title_changes": self.title_changes,
            "play_time_minutes": self.play_time_minutes,
        }
    
    def get_division_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all divisions"""
        summary = {}
        for wc, division in self.divisions.items():
            champion = None
            if division.champion_id:
                champ_record = self.fighters.get(division.champion_id)
                if champ_record:
                    champion = champ_record.display_name
            
            summary[wc] = {
                "champion": champion,
                "fighter_count": division.fighter_count,
                "has_interim": division.interim_champion_id is not None,
            }
        return summary
    
    # -------------------------------------------------------------------------
    # System Registration
    # -------------------------------------------------------------------------
    
    def register_world_simulation(self, world_sim: Any) -> None:
        """Register world simulation system"""
        self._world_simulation = world_sim
    
    def register_ranking_system(self, ranking_sys: Any) -> None:
        """Register ranking system"""
        self._ranking_system = ranking_sys
    
    def register_rivalry_system(self, rivalry_sys: Any) -> None:
        """Register rivalry system"""
        self._rivalry_system = rivalry_sys
    
    def register_economy_system(self, economy_sys: Any) -> None:
        """Register economy system"""
        self._economy_system = economy_sys
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize full game state"""
        return {
            # Metadata
            "game_id": self.game_id,
            "game_name": self.game_name,
            "created_date": self.created_date,
            "last_played": self.last_played,
            "play_time_minutes": self.play_time_minutes,
            
            # State
            "phase": self.phase.value,
            "mode": self.mode.value,
            "settings": self.settings.to_dict(),
            
            # Time - save calendar state simply
            "calendar_year": self.calendar.current_year,
            "calendar_total_weeks": self.calendar.total_weeks,
            "week_number": self.week_number,
            
            # Player
            "player_camp_id": self.player_camp_id,
            "player_name": self.player_name,
            
            # Entities
            "fighters": {fid: f.to_dict() for fid, f in self.fighters.items()},
            "camps": {cid: c.to_dict() for cid, c in self.camps.items()},
            "divisions": {wc: d.to_dict() for wc, d in self.divisions.items()},
            
            # IDs
            "next_fighter_id": self._next_fighter_id,
            "next_camp_id": self._next_camp_id,
            "next_event_id": self._next_event_id,
            "next_contract_id": self._next_contract_id,
            
            # Sets/mappings
            "free_agents": list(self.free_agents),
            "retired_fighters": list(self.retired_fighters),
            "active_contracts": dict(self.active_contracts),
            
            # Stats
            "total_fights_simulated": self.total_fights_simulated,
            "total_events_held": self.total_events_held,
            "title_changes": self.title_changes,
            
            # Full data
            "fighter_data": self._fighter_data,
            "camp_data": self._camp_data,
            "contract_data": self._contract_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Deserialize game state"""
        game = cls()
        
        # Metadata
        game.game_id = data["game_id"]
        game.game_name = data["game_name"]
        game.created_date = data["created_date"]
        game.last_played = data["last_played"]
        game.play_time_minutes = data.get("play_time_minutes", 0)
        
        # State
        game.phase = GamePhase(data["phase"])
        game.mode = GameMode(data["mode"])
        game.settings = GameSettings.from_dict(data["settings"])
        
        # Time - restore calendar
        from datetime import date as dt_date
        calendar_year = data.get("calendar_year", 2025)
        game.calendar = GameCalendar(start_date=dt_date(calendar_year, 1, 1))
        # Advance calendar to saved position
        saved_total_weeks = data.get("calendar_total_weeks", 0)
        for _ in range(saved_total_weeks):
            game.calendar.advance_week()
        game.week_number = data["week_number"]
        
        # Player
        game.player_camp_id = data["player_camp_id"]
        game.player_name = data["player_name"]
        
        # Entities
        game.fighters = {
            fid: FighterRecord.from_dict(f)
            for fid, f in data["fighters"].items()
        }
        game.camps = {
            cid: CampRecord.from_dict(c)
            for cid, c in data["camps"].items()
        }
        game.divisions = {
            wc: DivisionState.from_dict(d)
            for wc, d in data["divisions"].items()
        }
        
        # IDs
        game._next_fighter_id = data["next_fighter_id"]
        game._next_camp_id = data["next_camp_id"]
        game._next_event_id = data["next_event_id"]
        game._next_contract_id = data["next_contract_id"]
        
        # Sets/mappings
        game.free_agents = set(data["free_agents"])
        game.retired_fighters = set(data["retired_fighters"])
        game.active_contracts = dict(data["active_contracts"])
        
        # Stats
        game.total_fights_simulated = data.get("total_fights_simulated", 0)
        game.total_events_held = data.get("total_events_held", 0)
        game.title_changes = data.get("title_changes", 0)
        
        # Full data
        game._fighter_data = data.get("fighter_data", {})
        game._camp_data = data.get("camp_data", {})
        game._contract_data = data.get("contract_data", {})
        
        return game


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_game_state: Optional[GameState] = None


def get_game_state() -> GameState:
    """Get global game state instance"""
    global _game_state
    if _game_state is None:
        _game_state = GameState()
    return _game_state


def reset_game_state() -> None:
    """Reset global game state"""
    global _game_state
    _game_state = GameState()


def new_game(
    player_camp_name: str,
    player_name: str = "Player",
    mode: GameMode = GameMode.CAREER,
) -> GameState:
    """Quick start a new game"""
    reset_game_state()
    game = get_game_state()
    game.new_game(player_camp_name, player_name, mode)
    return game


def get_current_date() -> str:
    """Get current game date as string"""
    game = get_game_state()
    return game.calendar.current_date.format("long")


def get_current_week() -> int:
    """Get current week number"""
    return get_game_state().week_number
