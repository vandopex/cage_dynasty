"""
Cage Dynasty - Data Models and Mock Data Generator
Mirrors the structure of the actual game for seamless integration later.
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid

# =============================================================================
# CONSTANTS (matching the real game)
# =============================================================================

WEIGHT_CLASSES = [
    "Strawweight", "Flyweight", "Bantamweight", "Featherweight",
    "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
]

WEIGHT_CLASS_ABBREV = {
    "Strawweight": "STW", "Flyweight": "FLW", "Bantamweight": "BW",
    "Featherweight": "FW", "Lightweight": "LW", "Welterweight": "WW",
    "Middleweight": "MW", "Light Heavyweight": "LHW", "Heavyweight": "HW"
}

FIGHTING_STYLES = [
    "Striker", "Wrestler", "BJJ Specialist", "Muay Thai", "Boxer",
    "Ground & Pound", "Counter Striker", "Pressure Fighter", "Balanced",
    "Clinch Fighter", "Sprawl & Brawl"
]

CAMP_TIERS = ["ELITE", "NATIONAL", "REGIONAL", "LOCAL", "GARAGE"]

COUNTRIES = [
    "USA", "Brazil", "Russia", "Ireland", "Mexico", "Japan", "UK",
    "Australia", "Canada", "Poland", "Nigeria", "South Korea", "France"
]

FIRST_NAMES = [
    "Jake", "Marcus", "Chen", "Roman", "Takeshi", "Bruno", "Nathan",
    "Arthur", "Carlos", "Dmitri", "Kenji", "Patrick", "Gustavo", "Liam",
    "Noah", "Muhammad", "Antonio", "Lucas", "Gabriel", "Matheus"
]

LAST_NAMES = [
    "Anderson", "Silva", "Johnson", "Kovalev", "Yamada", "Fernandes",
    "Lee", "Barbosa", "Rodriguez", "Volkov", "Tanaka", "O'Brien",
    "Ribeiro", "Kennedy", "Walker", "Ali", "Santos", "Oliveira", "Costa", "Dias"
]

NICKNAMES = [
    "The Spider", "Bones", "The Notorious", "The Eagle", "The Last Stylebender",
    "Thug Rose", "The Lioness", "Blessed", "The Highlight", "The Nigerian Nightmare",
    "Showtime", "The Natural", "Rush", "The Iceman", "The Huntington Beach Bad Boy",
    None, None, None, None, None  # Some fighters have no nickname
]

CAMP_PREFIXES = [
    "Alpha", "Apex", "Elite", "Prime", "Supreme", "Victory", "Warrior",
    "Iron", "Steel", "Thunder", "Lightning", "Phoenix", "Dragon", "Tiger",
    "Wolf", "Eagle", "Cobra", "Viper", "Ronin", "Samurai"
]

CAMP_SUFFIXES = [
    "MMA", "Fight Team", "Academy", "Martial Arts", "Combat", "Athletics",
    "Training Center", "Gym", "Dojo", "Performance", "Warriors", "Legion"
]

NEWS_TEMPLATES = [
    ("🏆 {name} defends {division} title for the {count} time!", "title"),
    ("💥 KNOCKOUT! {winner} stops {loser} in Round {round}", "fight"),
    ("🔒 {winner} submits {loser} with a {sub_type}", "fight"),
    ("📝 SIGNED: #{rank1} {name1} vs #{rank2} {name2}", "signing"),
    ("⚔ TOP 5 CLASH: #{rank1} {name1} vs #{rank2} {name2}", "signing"),
    ("🏥 {name} ruled out {weeks} weeks with {injury}", "injury"),
    ("😱 UPSET! #{loser_rank} {loser} falls to #{winner_rank} {winner}", "fight"),
    ("📊 {name} climbs to #{rank} in {division}", "ranking"),
    ("👋 {name} announces retirement after {years} year career", "retirement"),
]

TRAITS = [
    ("Glass Cannon", "offensive", "+15 Power, -15 Chin"),
    ("Iron Chin", "defensive", "+15 Chin, -5 Speed"),
    ("Cardio Machine", "cardio", "+15 Cardio, -5 Power"),
    ("Knockout Artist", "offensive", "+10% KO chance"),
    ("Submission Ace", "offensive", "+10% Sub chance"),
    ("Wrestler's Base", "defensive", "+10 TD Defense"),
    ("Pressure Fighter", "mental", "+5 all vs Counter"),
    ("Counter Striker", "mental", "+5 all vs Pressure"),
    ("Fast Starter", "mental", "+10% Round 1"),
    ("Slow Starter", "mental", "+10% Rounds 3+"),
    ("Big Game Hunter", "mental", "+10% in title fights"),
    ("Gym Rat", "training", "+20% training gains"),
    ("Durable", "defensive", "-30% injury chance"),
    ("Veteran Savvy", "mental", "+5 IQ, +5 Composure"),
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Fighter:
    """Complete fighter data model."""
    fighter_id: str
    name: str
    nickname: Optional[str]
    age: int
    country: str
    weight_class: str
    fighting_style: str
    
    # Record
    wins: int = 0
    losses: int = 0
    draws: int = 0
    ko_wins: int = 0
    sub_wins: int = 0
    
    # Attributes (0-100)
    strength: int = 50
    speed: int = 50
    cardio: int = 50
    chin: int = 50
    recovery: int = 50
    boxing: int = 50
    kicks: int = 50
    clinch_striking: int = 50
    striking_defense: int = 50
    takedowns: int = 50
    takedown_defense: int = 50
    top_control: int = 50
    submissions: int = 50
    guard: int = 50
    heart: int = 50
    fight_iq: int = 50
    composure: int = 50
    
    # Potential (max each attribute can reach)
    potential: int = 75
    
    # Status
    is_champion: bool = False
    is_active: bool = True
    ranking: Optional[int] = None
    popularity: int = 20
    
    # Camp
    camp_id: Optional[str] = None
    camp_name: Optional[str] = None
    
    # Condition
    fatigue: int = 0
    morale: int = 75
    
    # Streaks
    win_streak: int = 0
    lose_streak: int = 0
    
    # Traits
    traits: List[str] = field(default_factory=list)
    
    # Fight history
    fight_history: List[Dict] = field(default_factory=list)
    
    # Physical
    height: str = "5'10\""
    reach: str = "72\""
    
    @property
    def overall_rating(self) -> int:
        """Calculate overall rating from attributes."""
        attrs = [
            self.strength, self.speed, self.cardio, self.chin, self.recovery,
            self.boxing, self.kicks, self.clinch_striking, self.striking_defense,
            self.takedowns, self.takedown_defense, self.top_control,
            self.submissions, self.guard, self.heart, self.fight_iq, self.composure
        ]
        return int(sum(attrs) / len(attrs))
    
    @property
    def record_str(self) -> str:
        """Format record string."""
        if self.draws > 0:
            return f"{self.wins}-{self.losses}-{self.draws}"
        return f"{self.wins}-{self.losses}"
    
    @property
    def division_abbrev(self) -> str:
        """Get weight class abbreviation."""
        return WEIGHT_CLASS_ABBREV.get(self.weight_class, "?")
    
    @property
    def rank_display(self) -> str:
        """Display rank or status."""
        if self.is_champion:
            return "C"
        elif self.ranking:
            return str(self.ranking)
        return "UR"
    
    @property
    def condition_status(self) -> str:
        """Get condition status label."""
        if self.fatigue <= 20:
            return "Fresh"
        elif self.fatigue <= 40:
            return "Rested"
        elif self.fatigue <= 60:
            return "Ready"
        elif self.fatigue <= 80:
            return "Tired"
        return "Exhausted"
    
    @property
    def condition_color(self) -> str:
        """Get CSS color class for condition."""
        if self.fatigue <= 20:
            return "success"
        elif self.fatigue <= 40:
            return "info"
        elif self.fatigue <= 60:
            return "warning"
        elif self.fatigue <= 80:
            return "danger"
        return "danger"


@dataclass
class Camp:
    """Training camp data model."""
    camp_id: str
    name: str
    tier: str
    location: str
    reputation: int
    balance: int
    is_player: bool = False
    
    # Roster
    fighter_ids: List[str] = field(default_factory=list)
    
    # Coaches
    head_coach_name: str = "Unknown"
    head_coach_specialty: str = "General"
    head_coach_rating: int = 50
    
    # Record
    total_wins: int = 0
    total_losses: int = 0
    championships: int = 0
    
    @property
    def record_str(self) -> str:
        return f"{self.total_wins}-{self.total_losses}"
    
    @property
    def win_percentage(self) -> int:
        total = self.total_wins + self.total_losses
        if total == 0:
            return 0
        return int(self.total_wins / total * 100)
    
    @property
    def tier_color(self) -> str:
        """CSS class for tier."""
        return {
            "ELITE": "gold",
            "NATIONAL": "info",
            "REGIONAL": "success",
            "LOCAL": "warning",
            "GARAGE": "secondary"
        }.get(self.tier, "secondary")
    
    @property
    def max_fighters(self) -> int:
        return {
            "ELITE": 12, "NATIONAL": 10, "REGIONAL": 8,
            "LOCAL": 5, "GARAGE": 3
        }.get(self.tier, 3)


@dataclass
class FightOffer:
    """Fight offer/contract data model."""
    offer_id: str
    fighter_id: str
    fighter_name: str
    opponent_id: str
    opponent_name: str
    opponent_record: str
    opponent_rating: int
    opponent_rank: Optional[int]
    weight_class: str
    event_name: str
    weeks_away: int
    purse: int
    win_bonus: int
    is_title_fight: bool = False
    is_main_event: bool = False
    matchup_quality: str = "Good"
    risk_level: int = 3  # 1-5 stars
    reward_level: int = 3  # 1-5 stars
    accept_chance: int = 50
    
    @property
    def total_potential(self) -> int:
        return self.purse + self.win_bonus


@dataclass
class NewsItem:
    """News feed item."""
    news_id: str
    headline: str
    category: str  # title, fight, signing, injury, ranking, retirement
    week: int
    timestamp: datetime = field(default_factory=datetime.now)
    icon: str = "📰"
    
    @property
    def category_color(self) -> str:
        return {
            "title": "gold",
            "fight": "danger",
            "signing": "info",
            "injury": "warning",
            "ranking": "success",
            "retirement": "secondary"
        }.get(self.category, "secondary")


@dataclass
class FightResult:
    """Fight result data model."""
    fight_id: str
    fighter1_id: str
    fighter1_name: str
    fighter2_id: str
    fighter2_name: str
    winner_id: str
    winner_name: str
    loser_id: str
    loser_name: str
    method: str  # KO, TKO, SUB, DEC
    round_finished: int
    time: str
    weight_class: str
    event_name: str
    event_number: int
    week: int
    is_title_fight: bool = False
    commentary: List[str] = field(default_factory=list)


@dataclass
class BeltReign:
    """Championship reign data."""
    reign_id: str
    champion_id: str
    champion_name: str
    weight_class: str
    won_week: int
    won_event: str
    won_from_name: Optional[str]
    won_method: str
    successful_defenses: int = 0
    is_active: bool = True
    lost_week: Optional[int] = None
    lost_to_name: Optional[str] = None
    lost_method: Optional[str] = None


@dataclass
class CompletedEvent:
    """Completed event data."""
    event_id: str
    event_name: str
    event_number: int
    week: int
    fights: List[FightResult] = field(default_factory=list)
    main_event: Optional[str] = None
    attendance: int = 0


# =============================================================================
# MOCK DATA GENERATOR
# =============================================================================

class MockDataGenerator:
    """
    Generates realistic mock data for the Cage Dynasty web app.
    Mirrors the structure of the actual game for easy integration.
    """
    
    def __init__(self):
        self.fighters: Dict[str, Fighter] = {}
        self.camps: Dict[str, Camp] = {}
        self.fight_offers: List[FightOffer] = []
        self.news_feed: List[NewsItem] = []
        self.completed_events: List[CompletedEvent] = []
        self.belt_history: Dict[str, List[BeltReign]] = {}
        self.player_camp_id: Optional[str] = None
        self.week_number: int = 15  # Start a few weeks in
        self.scheduled_fights: List[Dict] = []
        
        # Initialize belt history for each division
        for wc in WEIGHT_CLASSES:
            self.belt_history[wc] = []
    
    def generate_world(self):
        """Generate complete game world with all data."""
        print("Generating Cage Dynasty world...")
        
        # Generate camps first
        self._generate_camps()
        
        # Generate fighters
        self._generate_fighters(280)
        
        # Assign fighters to camps
        self._assign_fighters_to_camps()
        
        # Set rankings and champions
        self._set_rankings()
        
        # Generate fight history
        self._generate_fight_history()
        
        # Generate belt history
        self._generate_belt_history()
        
        # Generate news
        self._generate_news()
        
        # Generate fight offers for player
        self._generate_fight_offers()
        
        # Schedule some fights
        self._schedule_fights()
        
        print(f"Generated {len(self.fighters)} fighters in {len(self.camps)} camps")
    
    def _generate_camps(self):
        """Generate training camps."""
        tier_counts = {
            "ELITE": 3, "NATIONAL": 6, "REGIONAL": 10,
            "LOCAL": 14, "GARAGE": 7
        }
        
        locations = {
            "ELITE": ["Las Vegas, NV", "Miami, FL", "Los Angeles, CA"],
            "NATIONAL": ["Denver, CO", "San Diego, CA", "Dallas, TX", "Chicago, IL", "Phoenix, AZ", "Sacramento, CA"],
            "REGIONAL": ["Portland, OR", "Seattle, WA", "Austin, TX", "Atlanta, GA", "Boston, MA"],
            "LOCAL": ["Fresno, CA", "Tulsa, OK", "Milwaukee, WI", "Omaha, NE", "Boise, ID"],
            "GARAGE": ["Bakersfield, CA", "Stockton, CA", "Lubbock, TX", "Fargo, ND", "Reno, NV"],
        }
        
        used_names = set()
        
        for tier, count in tier_counts.items():
            for i in range(count):
                # Generate unique name
                while True:
                    name = f"{random.choice(CAMP_PREFIXES)} {random.choice(CAMP_SUFFIXES)}"
                    if name not in used_names:
                        used_names.add(name)
                        break
                
                camp_id = str(uuid.uuid4())[:8]
                
                # Tier-based stats
                tier_stats = {
                    "ELITE": (80, 100, 500000, 2000000),
                    "NATIONAL": (60, 85, 100000, 500000),
                    "REGIONAL": (40, 65, 50000, 150000),
                    "LOCAL": (25, 50, 20000, 75000),
                    "GARAGE": (10, 35, 5000, 30000),
                }
                rep_min, rep_max, bal_min, bal_max = tier_stats[tier]
                
                camp = Camp(
                    camp_id=camp_id,
                    name=name,
                    tier=tier,
                    location=random.choice(locations.get(tier, ["Unknown"])),
                    reputation=random.randint(rep_min, rep_max),
                    balance=random.randint(bal_min, bal_max),
                    head_coach_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    head_coach_specialty=random.choice(["Boxing", "Wrestling", "BJJ", "Muay Thai", "MMA"]),
                    head_coach_rating=random.randint(rep_min, rep_max),
                )
                
                self.camps[camp_id] = camp
        
        # Create player camp
        player_camp_id = str(uuid.uuid4())[:8]
        player_camp = Camp(
            camp_id=player_camp_id,
            name="Jackson's MMA",
            tier="GARAGE",
            location="Albuquerque, NM",
            reputation=25,
            balance=78500,
            is_player=True,
            head_coach_name="Alex Jackson",
            head_coach_specialty="Wrestling",
            head_coach_rating=72,
        )
        self.camps[player_camp_id] = player_camp
        self.player_camp_id = player_camp_id
    
    def _generate_fighters(self, count: int):
        """Generate fighters with realistic attributes."""
        used_names = set()
        
        for _ in range(count):
            # Generate unique name
            while True:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                name = f"{first} {last}"
                if name not in used_names:
                    used_names.add(name)
                    break
            
            fighter_id = str(uuid.uuid4())[:8]
            weight_class = random.choice(WEIGHT_CLASSES)
            
            # Base skill level (bell curve)
            base_skill = int(random.gauss(55, 15))
            base_skill = max(35, min(85, base_skill))
            
            # Style-based attribute distribution
            style = random.choice(FIGHTING_STYLES)
            
            # Generate attributes with variance
            def rand_attr(base, bonus=0):
                val = base + random.randint(-10, 10) + bonus
                return max(30, min(95, val))
            
            # Style bonuses
            striking_bonus = 10 if style in ["Striker", "Boxer", "Muay Thai", "Counter Striker"] else 0
            grappling_bonus = 10 if style in ["Wrestler", "BJJ Specialist", "Ground & Pound"] else 0
            
            # Age affects potential
            age = random.randint(21, 38)
            if age < 26:
                potential_mod = random.randint(5, 15)
            elif age < 32:
                potential_mod = random.randint(-5, 5)
            else:
                potential_mod = random.randint(-15, -5)
            
            # Generate record (older = more fights)
            total_fights = random.randint(3, 8) + (age - 21) // 2
            win_rate = random.uniform(0.35, 0.75)
            wins = int(total_fights * win_rate)
            losses = total_fights - wins
            
            # Physical attributes based on weight class
            height_base = {
                "Strawweight": "5'3\"", "Flyweight": "5'5\"", "Bantamweight": "5'6\"",
                "Featherweight": "5'8\"", "Lightweight": "5'9\"", "Welterweight": "5'10\"",
                "Middleweight": "6'0\"", "Light Heavyweight": "6'2\"", "Heavyweight": "6'3\""
            }
            
            fighter = Fighter(
                fighter_id=fighter_id,
                name=name,
                nickname=random.choice(NICKNAMES),
                age=age,
                country=random.choice(COUNTRIES),
                weight_class=weight_class,
                fighting_style=style,
                wins=wins,
                losses=losses,
                ko_wins=random.randint(0, wins),
                sub_wins=random.randint(0, wins - random.randint(0, wins)),
                
                # Attributes
                strength=rand_attr(base_skill),
                speed=rand_attr(base_skill),
                cardio=rand_attr(base_skill),
                chin=rand_attr(base_skill),
                recovery=rand_attr(base_skill),
                boxing=rand_attr(base_skill, striking_bonus),
                kicks=rand_attr(base_skill, striking_bonus if style == "Muay Thai" else 0),
                clinch_striking=rand_attr(base_skill),
                striking_defense=rand_attr(base_skill),
                takedowns=rand_attr(base_skill, grappling_bonus),
                takedown_defense=rand_attr(base_skill),
                top_control=rand_attr(base_skill, grappling_bonus),
                submissions=rand_attr(base_skill, 15 if style == "BJJ Specialist" else 0),
                guard=rand_attr(base_skill),
                heart=rand_attr(base_skill),
                fight_iq=rand_attr(base_skill + (age - 25) // 2),  # Experience helps
                composure=rand_attr(base_skill),
                
                potential=min(95, base_skill + 15 + potential_mod),
                popularity=random.randint(10, 60),
                fatigue=random.randint(0, 50),
                morale=random.randint(50, 90),
                win_streak=random.randint(0, 3) if wins > losses else 0,
                lose_streak=random.randint(0, 2) if losses > wins else 0,
                height=height_base.get(weight_class, "5'10\""),
                reach=f"{random.randint(64, 80)}\"",
            )
            
            # Add traits (0-2 traits per fighter)
            num_traits = random.choices([0, 1, 2], weights=[50, 35, 15])[0]
            available_traits = [t[0] for t in TRAITS]
            fighter.traits = random.sample(available_traits, min(num_traits, len(available_traits)))
            
            self.fighters[fighter_id] = fighter
        
        # Create player's starting fighter
        player_fighter = Fighter(
            fighter_id=str(uuid.uuid4())[:8],
            name="Jake Anderson",
            nickname="The Prodigy",
            age=24,
            country="USA",
            weight_class="Light Heavyweight",
            fighting_style="Striker",
            wins=0,
            losses=0,
            strength=75,
            speed=78,
            cardio=70,
            chin=68,
            recovery=72,
            boxing=80,
            kicks=75,
            clinch_striking=65,
            striking_defense=72,
            takedowns=55,
            takedown_defense=68,
            top_control=50,
            submissions=45,
            guard=55,
            heart=82,
            fight_iq=65,
            composure=70,
            potential=88,
            popularity=15,
            camp_id=self.player_camp_id,
            camp_name="Jackson's MMA",
            traits=["Fast Starter", "Knockout Artist"],
            height="6'2\"",
            reach="76\"",
        )
        self.fighters[player_fighter.fighter_id] = player_fighter
        self.camps[self.player_camp_id].fighter_ids.append(player_fighter.fighter_id)
    
    def _assign_fighters_to_camps(self):
        """Assign fighters to camps with smart distribution."""
        # Sort fighters by skill
        fighters_list = sorted(
            [f for f in self.fighters.values() if f.camp_id is None],
            key=lambda f: f.overall_rating,
            reverse=True
        )
        
        # Sort camps by tier
        tier_order = {"ELITE": 0, "NATIONAL": 1, "REGIONAL": 2, "LOCAL": 3, "GARAGE": 4}
        camps_list = sorted(
            [c for c in self.camps.values() if not c.is_player],
            key=lambda c: (tier_order[c.tier], -c.reputation)
        )
        
        # Track division counts per camp
        camp_div_counts = {c.camp_id: {} for c in camps_list}
        
        for fighter in fighters_list:
            # Find best camp (prefers camps without same division)
            best_camp = None
            for camp in camps_list:
                if len(camp.fighter_ids) >= camp.max_fighters:
                    continue
                
                div_count = camp_div_counts[camp.camp_id].get(fighter.weight_class, 0)
                if div_count < 2:  # Max 2 per division per camp
                    best_camp = camp
                    break
            
            if best_camp:
                fighter.camp_id = best_camp.camp_id
                fighter.camp_name = best_camp.name
                best_camp.fighter_ids.append(fighter.fighter_id)
                camp_div_counts[best_camp.camp_id][fighter.weight_class] = \
                    camp_div_counts[best_camp.camp_id].get(fighter.weight_class, 0) + 1
        
        # Update camp records
        for camp in self.camps.values():
            camp.total_wins = sum(self.fighters[fid].wins for fid in camp.fighter_ids if fid in self.fighters)
            camp.total_losses = sum(self.fighters[fid].losses for fid in camp.fighter_ids if fid in self.fighters)
    
    def _set_rankings(self):
        """Set rankings and champions for each division."""
        for weight_class in WEIGHT_CLASSES:
            division_fighters = [
                f for f in self.fighters.values()
                if f.weight_class == weight_class and f.is_active
            ]
            
            # Sort by win%, wins, rating
            def rank_key(f):
                total = f.wins + f.losses
                win_pct = f.wins / total if total > 0 else 0
                return (win_pct, f.wins, f.overall_rating)
            
            division_fighters.sort(key=rank_key, reverse=True)
            
            # Set champion
            if division_fighters:
                champ = division_fighters[0]
                champ.is_champion = True
                champ.ranking = 0
                champ.popularity = min(100, champ.popularity + 30)
                
                # Set contenders
                for i, fighter in enumerate(division_fighters[1:16], 1):
                    fighter.ranking = i
                    fighter.popularity = min(100, fighter.popularity + (15 - i))
    
    def _generate_fight_history(self):
        """Generate fight history for each fighter."""
        event_num = 1
        
        for week in range(1, self.week_number):
            if week % 2 == 0:  # Events every 2 weeks
                event = CompletedEvent(
                    event_id=str(uuid.uuid4())[:8],
                    event_name=f"DFC {event_num}",
                    event_number=event_num,
                    week=week,
                    attendance=random.randint(5000, 20000),
                )
                
                # Generate 8-12 fights per event
                for _ in range(random.randint(8, 12)):
                    weight_class = random.choice(WEIGHT_CLASSES)
                    fighters = [
                        f for f in self.fighters.values()
                        if f.weight_class == weight_class and f.camp_id != self.player_camp_id
                    ]
                    
                    if len(fighters) >= 2:
                        f1, f2 = random.sample(fighters, 2)
                        
                        # Determine winner
                        f1_power = f1.overall_rating + random.randint(-10, 10)
                        f2_power = f2.overall_rating + random.randint(-10, 10)
                        
                        if f1_power >= f2_power:
                            winner, loser = f1, f2
                        else:
                            winner, loser = f2, f1
                        
                        # Method
                        method = random.choices(
                            ["KO", "TKO", "SUB", "DEC"],
                            weights=[15, 20, 20, 45]
                        )[0]
                        
                        round_finished = 3 if method == "DEC" else random.randint(1, 3)
                        
                        fight = FightResult(
                            fight_id=str(uuid.uuid4())[:8],
                            fighter1_id=f1.fighter_id,
                            fighter1_name=f1.name,
                            fighter2_id=f2.fighter_id,
                            fighter2_name=f2.name,
                            winner_id=winner.fighter_id,
                            winner_name=winner.name,
                            loser_id=loser.fighter_id,
                            loser_name=loser.name,
                            method=method,
                            round_finished=round_finished,
                            time=f"{random.randint(1, 4)}:{random.randint(10, 59):02d}",
                            weight_class=weight_class,
                            event_name=event.event_name,
                            event_number=event_num,
                            week=week,
                        )
                        
                        event.fights.append(fight)
                        
                        # Add to fighter history
                        winner.fight_history.append({
                            "opponent": loser.name,
                            "result": "W",
                            "method": method,
                            "round": round_finished,
                            "event": event.event_name,
                            "week": week,
                        })
                        loser.fight_history.append({
                            "opponent": winner.name,
                            "result": "L",
                            "method": method,
                            "round": round_finished,
                            "event": event.event_name,
                            "week": week,
                        })
                
                if event.fights:
                    event.main_event = f"{event.fights[-1].fighter1_name} vs {event.fights[-1].fighter2_name}"
                
                self.completed_events.append(event)
                event_num += 1
    
    def _generate_belt_history(self):
        """Generate championship belt history."""
        for weight_class in WEIGHT_CLASSES:
            champion = next(
                (f for f in self.fighters.values() if f.weight_class == weight_class and f.is_champion),
                None
            )
            
            if champion:
                # Current reign
                reign = BeltReign(
                    reign_id=str(uuid.uuid4())[:8],
                    champion_id=champion.fighter_id,
                    champion_name=champion.name,
                    weight_class=weight_class,
                    won_week=random.randint(1, self.week_number - 5),
                    won_event=f"DFC {random.randint(1, 10)}",
                    won_from_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    won_method=random.choice(["KO", "SUB", "DEC"]),
                    successful_defenses=random.randint(0, 4),
                    is_active=True,
                )
                self.belt_history[weight_class].append(reign)
                
                # Add some historical reigns
                for i in range(random.randint(2, 5)):
                    past_champ_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                    past_reign = BeltReign(
                        reign_id=str(uuid.uuid4())[:8],
                        champion_id=str(uuid.uuid4())[:8],
                        champion_name=past_champ_name,
                        weight_class=weight_class,
                        won_week=i * 10 + 1,
                        won_event=f"DFC {i + 1}",
                        won_from_name=None if i == 0 else f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                        won_method="Inaugural" if i == 0 else random.choice(["KO", "SUB", "DEC"]),
                        successful_defenses=random.randint(1, 6),
                        is_active=False,
                        lost_week=(i + 1) * 10,
                        lost_to_name=past_champ_name if i < 4 else champion.name,
                        lost_method=random.choice(["KO", "SUB", "DEC"]),
                    )
                    self.belt_history[weight_class].insert(0, past_reign)
    
    def _generate_news(self):
        """Generate news feed items."""
        icons = {
            "title": "🏆",
            "fight": "🥊",
            "signing": "📝",
            "injury": "🏥",
            "ranking": "📊",
            "retirement": "👋"
        }
        
        # Generate various news
        for i in range(30):
            week = max(1, self.week_number - i // 3)
            category = random.choice(["title", "fight", "signing", "injury", "ranking"])
            
            fighters = list(self.fighters.values())
            f1 = random.choice(fighters)
            f2 = random.choice([f for f in fighters if f.fighter_id != f1.fighter_id])
            
            if category == "title":
                champ = next((f for f in fighters if f.is_champion), f1)
                headline = f"🏆 {champ.name} defends {champ.weight_class} title!"
            elif category == "fight":
                method = random.choice(["KO", "TKO", "SUB"])
                if method in ["KO", "TKO"]:
                    headline = f"💥 KNOCKOUT! {f1.name} stops {f2.name} in Round {random.randint(1, 3)}"
                else:
                    headline = f"🔒 {f1.name} submits {f2.name} with a rear naked choke"
            elif category == "signing":
                r1 = f1.ranking or random.randint(6, 15)
                r2 = f2.ranking or random.randint(6, 15)
                if r1 <= 5 and r2 <= 5:
                    headline = f"⚔ TOP 5 CLASH: #{r1} {f1.name} vs #{r2} {f2.name}"
                else:
                    headline = f"📝 SIGNED: #{r1} {f1.name} vs #{r2} {f2.name}"
            elif category == "injury":
                headline = f"🏥 {f1.name} ruled out {random.randint(4, 12)} weeks with {random.choice(['hand', 'knee', 'back', 'shoulder'])} injury"
            else:
                headline = f"📊 {f1.name} climbs to #{f1.ranking or random.randint(1, 10)} in {f1.weight_class}"
            
            news = NewsItem(
                news_id=str(uuid.uuid4())[:8],
                headline=headline,
                category=category,
                week=week,
                icon=icons.get(category, "📰"),
            )
            self.news_feed.append(news)
        
        # Sort by week (newest first)
        self.news_feed.sort(key=lambda n: n.week, reverse=True)
    
    def _generate_fight_offers(self):
        """Generate fight offers for player's fighters."""
        player_fighters = [
            self.fighters[fid] for fid in self.camps[self.player_camp_id].fighter_ids
            if fid in self.fighters
        ]
        
        for fighter in player_fighters:
            # Generate 3-5 offers per fighter
            for _ in range(random.randint(3, 5)):
                # Find suitable opponent
                opponents = [
                    f for f in self.fighters.values()
                    if f.weight_class == fighter.weight_class
                    and f.camp_id != self.player_camp_id
                    and f.is_active
                ]
                
                if not opponents:
                    continue
                
                # Pick opponent (prefer similar skill level)
                opponents.sort(key=lambda o: abs(o.overall_rating - fighter.overall_rating))
                opponent = random.choice(opponents[:10])
                
                # Calculate risk/reward
                rating_diff = opponent.overall_rating - fighter.overall_rating
                rank_diff = (opponent.ranking or 20) - (fighter.ranking or 20)
                
                if rating_diff > 10:
                    risk = 5
                    reward = 5
                elif rating_diff > 5:
                    risk = 4
                    reward = 4
                elif rating_diff > -5:
                    risk = 3
                    reward = 3
                elif rating_diff > -10:
                    risk = 2
                    reward = 2
                else:
                    risk = 1
                    reward = 1
                
                # Boost reward for ranked opponents
                if opponent.ranking and opponent.ranking <= 10:
                    reward = min(5, reward + 1)
                
                # Base purse
                purse = 5000 + (fighter.overall_rating + opponent.overall_rating) * 50
                
                offer = FightOffer(
                    offer_id=str(uuid.uuid4())[:8],
                    fighter_id=fighter.fighter_id,
                    fighter_name=fighter.name,
                    opponent_id=opponent.fighter_id,
                    opponent_name=opponent.name,
                    opponent_record=opponent.record_str,
                    opponent_rating=opponent.overall_rating,
                    opponent_rank=opponent.ranking,
                    weight_class=fighter.weight_class,
                    event_name=f"DFC {random.randint(self.week_number + 2, self.week_number + 10)}",
                    weeks_away=random.randint(4, 8),
                    purse=purse,
                    win_bonus=int(purse * 0.5),
                    matchup_quality=random.choice(["Excellent", "Good", "Fair", "Poor"]),
                    risk_level=risk,
                    reward_level=reward,
                    accept_chance=random.randint(40, 80),
                )
                
                self.fight_offers.append(offer)
    
    def _schedule_fights(self):
        """Schedule some upcoming AI fights."""
        for week_offset in range(1, 6):
            week = self.week_number + week_offset
            
            for _ in range(random.randint(5, 10)):
                weight_class = random.choice(WEIGHT_CLASSES)
                fighters = [
                    f for f in self.fighters.values()
                    if f.weight_class == weight_class and f.camp_id != self.player_camp_id
                ]
                
                if len(fighters) >= 2:
                    f1, f2 = random.sample(fighters, 2)
                    
                    self.scheduled_fights.append({
                        "fighter1_id": f1.fighter_id,
                        "fighter1_name": f1.name,
                        "fighter2_id": f2.fighter_id,
                        "fighter2_name": f2.name,
                        "weight_class": weight_class,
                        "week": week,
                        "event_name": f"DFC {week // 2}",
                    })
    
    # =========================================================================
    # ACCESSOR METHODS
    # =========================================================================
    
    def get_player_camp(self) -> Optional[Camp]:
        """Get the player's camp."""
        return self.camps.get(self.player_camp_id)
    
    def get_player_fighters(self) -> List[Fighter]:
        """Get all fighters in player's camp."""
        camp = self.get_player_camp()
        if not camp:
            return []
        return [self.fighters[fid] for fid in camp.fighter_ids if fid in self.fighters]
    
    def get_fighter(self, fighter_id: str) -> Optional[Fighter]:
        """Get fighter by ID."""
        return self.fighters.get(fighter_id)
    
    def get_division_rankings(self, weight_class: str) -> List[Fighter]:
        """Get ranked fighters in a division."""
        fighters = [
            f for f in self.fighters.values()
            if f.weight_class == weight_class and f.is_active
        ]
        
        # Sort: champion first, then by ranking
        def sort_key(f):
            if f.is_champion:
                return (0, 0)
            elif f.ranking:
                return (1, f.ranking)
            else:
                return (2, 100 - f.overall_rating)
        
        return sorted(fighters, key=sort_key)
    
    def get_champion(self, weight_class: str) -> Optional[Fighter]:
        """Get champion of a division."""
        for fighter in self.fighters.values():
            if fighter.weight_class == weight_class and fighter.is_champion:
                return fighter
        return None
    
    def get_offers_for_fighter(self, fighter_id: str) -> List[FightOffer]:
        """Get fight offers for a specific fighter."""
        return [o for o in self.fight_offers if o.fighter_id == fighter_id]
    
    def get_upcoming_events(self) -> List[Dict]:
        """Get upcoming scheduled events grouped by week."""
        events = {}
        for fight in self.scheduled_fights:
            week = fight["week"]
            if week not in events:
                events[week] = {
                    "week": week,
                    "event_name": fight["event_name"],
                    "fights": []
                }
            events[week]["fights"].append(fight)
        
        return sorted(events.values(), key=lambda e: e["week"])
    
    # =========================================================================
    # NEW GAME WITH PLAYER CHOICES
    # =========================================================================
    
    def generate_world_with_player(self, camp_name: str, camp_location: str, 
                                    camp_tier: str, coach_id: str, fighter_id: str):
        """Generate game world with player's custom choices."""
        print(f"Generating Cage Dynasty world with player camp: {camp_name}...")
        
        # Reset everything
        self.fighters = {}
        self.camps = {}
        self.fight_offers = []
        self.news_feed = []
        self.completed_events = []
        self.belt_history = {wc: [] for wc in WEIGHT_CLASSES}
        self.scheduled_fights = []
        self.week_number = 1
        
        # Generate AI camps first (without player)
        self._generate_camps()
        
        # Create player camp with their choices
        player_camp_id = str(uuid.uuid4())[:8]
        
        tier_balance = {
            "GARAGE": 50000,
            "LOCAL": 100000,
            "REGIONAL": 250000,
            "NATIONAL": 500000,
            "ELITE": 1000000,
        }
        
        tier_reputation = {
            "GARAGE": 15,
            "LOCAL": 30,
            "REGIONAL": 50,
            "NATIONAL": 75,
            "ELITE": 90,
        }
        
        # Coach info based on selection
        coach_data = self._get_coach_from_id(coach_id, camp_tier)
        
        player_camp = Camp(
            camp_id=player_camp_id,
            name=camp_name,
            tier=camp_tier,
            location=camp_location,
            reputation=tier_reputation.get(camp_tier, 15),
            balance=tier_balance.get(camp_tier, 50000),
            is_player=True,
            head_coach_name=coach_data.get("name", "Unknown Coach"),
            head_coach_specialty=coach_data.get("specialty", "MMA"),
            head_coach_rating=coach_data.get("rating", 50),
        )
        self.camps[player_camp_id] = player_camp
        self.player_camp_id = player_camp_id
        
        # Generate AI fighters
        self._generate_fighters(280)
        
        # Create player's fighter from selection
        fighter_data = self._get_prospect_from_id(fighter_id)
        player_fighter = self._create_player_fighter(fighter_data, player_camp_id, camp_name)
        self.fighters[player_fighter.fighter_id] = player_fighter
        self.camps[player_camp_id].fighter_ids.append(player_fighter.fighter_id)
        
        # Assign AI fighters to AI camps
        self._assign_fighters_to_camps()
        
        # Set rankings and champions
        self._set_rankings()
        
        # Generate fight history
        self._generate_fight_history()
        
        # Generate belt history
        self._generate_belt_history()
        
        # Generate news
        self._generate_news()
        
        # Generate fight offers for player
        self._generate_fight_offers()
        
        # Schedule some fights
        self._schedule_fights()
        
        print(f"Generated {len(self.fighters)} fighters in {len(self.camps)} camps")
        print(f"Player camp: {camp_name} ({camp_tier}) with fighter: {player_fighter.name}")
    
    def _get_coach_from_id(self, coach_id: str, tier: str) -> Dict:
        """Get coach data from ID (regenerate if needed)."""
        # For now, regenerate the coach based on ID
        import random
        random.seed(hash(coach_id))
        
        tier_ratings = {
            "GARAGE": (45, 65),
            "LOCAL": (55, 75),
            "REGIONAL": (65, 85),
            "NATIONAL": (75, 90),
            "ELITE": (85, 98),
        }
        min_r, max_r = tier_ratings.get(tier, (45, 65))
        
        specialties = ["Boxing", "Wrestling", "BJJ", "Muay Thai", "MMA"]
        first_names = ["Mike", "John", "Carlos", "Greg", "Dave", "Tony", "Rafael", "Alex"]
        last_names = ["Johnson", "Martinez", "Smith", "Williams", "Garcia", "Brown", "Davis", "Miller"]
        
        return {
            "name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "specialty": random.choice(specialties),
            "rating": random.randint(min_r, max_r),
        }
    
    def _get_prospect_from_id(self, fighter_id: str) -> Dict:
        """Get prospect data from ID (regenerate if needed)."""
        import random
        random.seed(hash(fighter_id))
        
        weight_classes = [
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ]
        styles = ["Striker", "Wrestler", "BJJ Specialist", "Muay Thai", "Boxer", "Balanced"]
        first_names = ["Jake", "Marcus", "Chen", "Diego", "Kenji", "Patrick", "Dmitri", "Bruno"]
        last_names = ["Anderson", "Silva", "Lee", "Rodriguez", "Tanaka", "O'Brien", "Volkov", "Costa"]
        countries = ["USA", "Brazil", "Japan", "Mexico", "Ireland", "Russia", "UK"]
        nicknames = ["The Prodigy", "Kid Dynamite", "The Natural", "Showtime", "The Answer", None]
        
        base_rating = random.randint(58, 72)
        potential = random.randint(base_rating + 10, 95)
        
        return {
            "name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "nickname": random.choice(nicknames),
            "age": random.randint(20, 26),
            "country": random.choice(countries),
            "weight_class": random.choice(weight_classes),
            "style": random.choice(styles),
            "overall": base_rating,
            "potential": potential,
        }
    
    def _create_player_fighter(self, data: Dict, camp_id: str, camp_name: str) -> Fighter:
        """Create a fighter from prospect data."""
        import random
        
        base = data.get("overall", 65)
        style = data.get("style", "Balanced")
        
        # Style bonuses
        striking_bonus = 10 if style in ["Striker", "Boxer", "Muay Thai"] else 0
        grappling_bonus = 10 if style in ["Wrestler", "BJJ Specialist"] else 0
        
        def rand_attr(bonus=0):
            return max(35, min(90, base + random.randint(-8, 8) + bonus))
        
        height_base = {
            "Strawweight": "5'3\"", "Flyweight": "5'5\"", "Bantamweight": "5'6\"",
            "Featherweight": "5'8\"", "Lightweight": "5'9\"", "Welterweight": "5'10\"",
            "Middleweight": "6'0\"", "Light Heavyweight": "6'2\"", "Heavyweight": "6'3\""
        }
        
        return Fighter(
            fighter_id=str(uuid.uuid4())[:8],
            name=data.get("name", "Unknown Fighter"),
            nickname=data.get("nickname"),
            age=data.get("age", 23),
            country=data.get("country", "USA"),
            weight_class=data.get("weight_class", "Lightweight"),
            fighting_style=style,
            wins=0,
            losses=0,
            strength=rand_attr(),
            speed=rand_attr(striking_bonus),
            cardio=rand_attr(),
            chin=rand_attr(),
            recovery=rand_attr(),
            boxing=rand_attr(striking_bonus),
            kicks=rand_attr(striking_bonus if style == "Muay Thai" else 0),
            clinch_striking=rand_attr(),
            striking_defense=rand_attr(),
            takedowns=rand_attr(grappling_bonus),
            takedown_defense=rand_attr(),
            top_control=rand_attr(grappling_bonus),
            submissions=rand_attr(15 if style == "BJJ Specialist" else 0),
            guard=rand_attr(),
            heart=rand_attr(5),  # Young fighters have heart
            fight_iq=rand_attr(-5),  # Less experience
            composure=rand_attr(),
            potential=data.get("potential", 85),
            popularity=15,
            camp_id=camp_id,
            camp_name=camp_name,
            height=height_base.get(data.get("weight_class", "Lightweight"), "5'10\""),
            reach=f"{random.randint(66, 78)}\"",
        )
    
    # =========================================================================
    # FIGHT OFFER MANAGEMENT
    # =========================================================================
    
    def accept_offer(self, offer_id: str) -> Dict[str, Any]:
        """Accept a fight offer and schedule the fight."""
        # Find the offer
        offer = next((o for o in self.fight_offers if o.offer_id == offer_id), None)
        
        if not offer:
            return {"success": False, "error": "Offer not found"}
        
        # Get fighter and opponent
        fighter = self.fighters.get(offer.fighter_id)
        opponent = self.fighters.get(offer.opponent_id)
        
        if not fighter or not opponent:
            return {"success": False, "error": "Fighter not found"}
        
        # Schedule the fight
        fight_week = self.week_number + offer.weeks_away
        scheduled_fight = {
            "fight_id": str(uuid.uuid4())[:8],
            "fighter1_id": fighter.fighter_id,
            "fighter1_name": fighter.name,
            "fighter2_id": opponent.fighter_id,
            "fighter2_name": opponent.name,
            "weight_class": offer.weight_class,
            "week": fight_week,
            "event_name": offer.event_name,
            "is_title_fight": offer.is_title_fight,
            "is_main_event": offer.is_title_fight,
            "purse": offer.purse,
            "win_bonus": offer.win_bonus,
            "is_player_fight": True,
        }
        
        self.scheduled_fights.append(scheduled_fight)
        
        # Remove the offer
        self.fight_offers = [o for o in self.fight_offers if o.offer_id != offer_id]
        
        # Add news
        self.news_feed.insert(0, NewsItem(
            news_id=str(uuid.uuid4())[:8],
            headline=f"📝 SIGNED: {fighter.name} vs {opponent.name} set for Week {fight_week}",
            category="signing",
            week=self.week_number,
            icon="📝"
        ))
        
        return {
            "success": True,
            "message": f"Fight scheduled: {fighter.name} vs {opponent.name}",
            "fight": scheduled_fight
        }
    
    def decline_offer(self, offer_id: str) -> Dict[str, Any]:
        """Decline a fight offer."""
        offer = next((o for o in self.fight_offers if o.offer_id == offer_id), None)
        
        if not offer:
            return {"success": False, "error": "Offer not found"}
        
        # Remove the offer
        self.fight_offers = [o for o in self.fight_offers if o.offer_id != offer_id]
        
        return {"success": True, "message": "Offer declined"}
    
    def get_player_scheduled_fights(self) -> List[Dict]:
        """Get scheduled fights for player's fighters."""
        player_fighter_ids = set()
        if self.player_camp_id and self.player_camp_id in self.camps:
            player_fighter_ids = set(self.camps[self.player_camp_id].fighter_ids)
        
        return [
            f for f in self.scheduled_fights
            if f.get("fighter1_id") in player_fighter_ids or f.get("fighter2_id") in player_fighter_ids
        ]
    
    # =========================================================================
    # WEEK ADVANCEMENT WITH FIGHT SIMULATION
    # =========================================================================
    
    def advance_week(self) -> Dict[str, Any]:
        """Advance the game by one week, simulating any scheduled fights."""
        self.week_number += 1
        
        results = {
            "week": self.week_number,
            "fights_completed": [],
            "news": []
        }
        
        # Find fights scheduled for this week
        fights_this_week = [f for f in self.scheduled_fights if f["week"] == self.week_number]
        
        for fight in fights_this_week:
            # Simulate the fight
            fight_result = self._simulate_fight(fight)
            results["fights_completed"].append(fight_result)
            
            # Add to completed events
            event_id = str(uuid.uuid4())[:8]
            event = {
                "event_id": event_id,
                "event_name": fight["event_name"],
                "week": self.week_number,
                "fights": [fight_result],
                "main_event": fight_result
            }
            self.completed_events.append(event)
        
        # Remove completed fights from schedule
        self.scheduled_fights = [f for f in self.scheduled_fights if f["week"] != self.week_number]
        
        # Generate new offers if player has no pending offers
        player_fighters = self.get_player_fighters()
        for fighter in player_fighters:
            offers_for_fighter = [o for o in self.fight_offers if o.fighter_id == fighter.fighter_id]
            scheduled_for_fighter = [f for f in self.scheduled_fights 
                                     if f["fighter1_id"] == fighter.fighter_id or f["fighter2_id"] == fighter.fighter_id]
            
            if len(offers_for_fighter) < 2 and not scheduled_for_fighter:
                self._generate_offers_for_fighter(fighter)
        
        return results
    
    def _simulate_fight(self, fight: Dict) -> Dict:
        """Simulate a fight and return the result."""
        fighter1 = self.fighters.get(fight["fighter1_id"])
        fighter2 = self.fighters.get(fight["fighter2_id"])
        
        if not fighter1 or not fighter2:
            return {"error": "Fighter not found"}
        
        # Simple simulation based on overall ratings
        f1_power = fighter1.overall_rating + random.randint(-15, 15)
        f2_power = fighter2.overall_rating + random.randint(-15, 15)
        
        if f1_power > f2_power:
            winner, loser = fighter1, fighter2
        else:
            winner, loser = fighter2, fighter1
        
        # Determine method
        method_roll = random.random()
        if method_roll < 0.35:
            method = "KO"
            round_finished = random.randint(1, 3)
        elif method_roll < 0.55:
            method = "TKO"
            round_finished = random.randint(1, 3)
        elif method_roll < 0.70:
            method = "SUB"
            round_finished = random.randint(1, 3)
        else:
            method = "DEC"
            round_finished = 3
        
        # Update fighter records
        winner.wins += 1
        loser.losses += 1
        
        if method in ["KO", "TKO"]:
            winner.ko_wins += 1
            winner.win_streak += 1
            loser.win_streak = 0
            loser.lose_streak += 1
        elif method == "SUB":
            winner.sub_wins += 1
            winner.win_streak += 1
            loser.win_streak = 0
            loser.lose_streak += 1
        else:
            winner.win_streak += 1
            loser.win_streak = 0
            loser.lose_streak += 1
        
        # Create result
        result = {
            "fight_id": fight.get("fight_id", str(uuid.uuid4())[:8]),
            "winner_id": winner.fighter_id,
            "winner_name": winner.name,
            "loser_id": loser.fighter_id,
            "loser_name": loser.name,
            "method": method,
            "round": round_finished,
            "time": f"{random.randint(0, 4)}:{random.randint(10, 59):02d}",
            "is_title_fight": fight.get("is_title_fight", False),
            "weight_class": fight["weight_class"],
            "event_name": fight["event_name"],
            "fighter1_id": fight["fighter1_id"],
            "fighter2_id": fight["fighter2_id"],
        }
        
        # Add news headline
        if method in ["KO", "TKO"]:
            headline = f"💥 KNOCKOUT! {winner.name} stops {loser.name} in Round {round_finished}"
        elif method == "SUB":
            headline = f"🔒 SUBMISSION! {winner.name} taps out {loser.name}"
        else:
            headline = f"📋 {winner.name} defeats {loser.name} by decision"
        
        self.news_feed.insert(0, NewsItem(
            news_id=str(uuid.uuid4())[:8],
            headline=headline,
            category="fight",
            week=self.week_number,
            icon="🥊"
        ))
        
        return result
    
    def _generate_offers_for_fighter(self, fighter):
        """Generate new fight offers for a specific fighter."""
        # Find suitable opponents
        opponents = [
            f for f in self.fighters.values()
            if f.weight_class == fighter.weight_class
            and f.camp_id != self.player_camp_id
            and f.is_active
            and f.fighter_id != fighter.fighter_id
        ]
        
        if not opponents:
            return
        
        # Sort by skill similarity
        opponents.sort(key=lambda o: abs(o.overall_rating - fighter.overall_rating))
        
        # Generate 2-3 offers
        for i in range(min(3, len(opponents))):
            opponent = opponents[i]
            
            # Calculate risk/reward
            rating_diff = opponent.overall_rating - fighter.overall_rating
            
            if rating_diff > 10:
                risk, reward = 5, 5
            elif rating_diff > 5:
                risk, reward = 4, 4
            elif rating_diff > -5:
                risk, reward = 3, 3
            elif rating_diff > -10:
                risk, reward = 2, 2
            else:
                risk, reward = 1, 1
            
            purse = 5000 + (fighter.overall_rating + opponent.overall_rating) * 50
            
            offer = FightOffer(
                offer_id=str(uuid.uuid4())[:8],
                fighter_id=fighter.fighter_id,
                fighter_name=fighter.name,
                opponent_id=opponent.fighter_id,
                opponent_name=opponent.name,
                opponent_record=opponent.record_str,
                opponent_rating=opponent.overall_rating,
                opponent_rank=opponent.ranking,
                weight_class=fighter.weight_class,
                event_name=f"DFC {self.week_number + random.randint(4, 10)}",
                weeks_away=random.randint(4, 8),
                purse=purse,
                win_bonus=int(purse * 0.5),
                matchup_quality=random.choice(["Excellent", "Good", "Fair"]),
                risk_level=risk,
                reward_level=reward,
                accept_chance=random.randint(40, 80),
            )
            
            self.fight_offers.append(offer)
