# narrative/news.py
# Module: News & Rumor Mill System
# Lines: ~1,650
#
# Living sports media simulation with breaking news, rumors,
# analysis, and fictional MMA media personalities.

"""
Cage Dynasty - News & Rumor Mill

Creates a living sports media environment:
- Fight results with context (record, rank)
- Breaking news and upsets
- Rumor mill with varying accuracy
- Fictional media personalities
- Smart filtering by relevance
- News archive

MEDIA PERSONALITIES:
===================
- @MMAInsiderMike - Reliable insider, 80% accurate
- @CageSideCarla - Fan favorite, dramatic takes
- @FightGameFrank - Old school analyst, measured
- @RumorMillRicky - Wild speculation, 40% accurate
- @ChampionshipChloe - Title picture focused
- DFC Official - Promotion announcements

USAGE:
    from narrative.news import (
        NewsSystem, generate_fight_news, generate_rumor,
        format_fighter_context, NewsFilter
    )
    
    news_system = NewsSystem()
    news_system.generate_weekly_news(game_state)
    display = news_system.get_filtered_news(NewsFilter.MY_CAMP)
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import random


# ============================================================================
# ENUMS
# ============================================================================

class NewsPriority(Enum):
    """Priority levels for news items."""
    CRITICAL = 4    # Your fighters, title changes, major upsets
    HIGH = 3        # Your divisions, top 10 fights
    MEDIUM = 2      # Other notable results
    LOW = 1         # Minor fights, minor moves


class NewsCategory(Enum):
    """Categories of news items."""
    RESULT = "result"
    TITLE = "title"
    UPSET = "upset"
    SIGNING = "signing"
    RELEASE = "release"
    RETIREMENT = "retirement"
    INJURY = "injury"
    RUMOR = "rumor"
    RANKING = "ranking"
    MILESTONE = "milestone"
    CONTRACT = "contract"
    ANALYSIS = "analysis"
    ANNOUNCEMENT = "announcement"


class RumorType(Enum):
    """Types of rumors."""
    TRANSFER = "transfer"           # Fighter unhappy, looking to move
    FIGHT_TALKS = "fight_talks"     # Potential matchup discussions
    INJURY = "injury"               # Undisclosed injury
    RETIREMENT = "retirement"       # Considering hanging up gloves
    WEIGHT_CHANGE = "weight_change" # Moving divisions
    TITLE_SHOT = "title_shot"       # Next in line speculation
    CAMP_DRAMA = "camp_drama"       # Internal issues
    SUPERFIGHT = "superfight"       # Cross-division matchup
    COMEBACK = "comeback"           # Return from layoff
    CONTRACT = "contract"           # Contract negotiations


class NewsFilter(Enum):
    """Filter options for news display."""
    HEADLINES = "headlines"         # Top 5 stories
    MY_CAMP = "my_camp"            # Your fighters only
    MY_DIVISIONS = "my_divisions"  # Weight classes you compete in
    ALL_NEWS = "all"               # Everything
    RUMORS_ONLY = "rumors"         # Just speculation
    RESULTS_ONLY = "results"       # Just fight outcomes


# ============================================================================
# MEDIA PERSONALITIES
# ============================================================================

@dataclass
class MediaPersonality:
    """A fictional MMA media personality."""
    name: str
    handle: str
    style: str              # How they write
    accuracy: float         # How often their rumors are true (0-1)
    focus: List[str]        # What they cover
    catchphrases: List[str]
    emoji: str
    
    def get_attribution(self) -> str:
        """Get a random attribution style."""
        styles = [
            f"- {self.handle}",
            f"— {self.name} ({self.handle})",
            f"[{self.handle}]",
            f"via {self.handle}",
        ]
        return random.choice(styles)


# Our cast of fictional MMA media personalities
MEDIA_PERSONALITIES = {
    "insider_mike": MediaPersonality(
        name="Mike Reeves",
        handle="@MMAInsiderMike",
        style="insider",
        accuracy=0.80,
        focus=["transfers", "contracts", "breaking"],
        catchphrases=[
            "BREAKING:",
            "Sources tell me...",
            "I'm hearing...",
            "Multiple sources confirm...",
            "Can confirm:",
            "Per sources close to the situation...",
        ],
        emoji="🎯",
    ),
    "carla": MediaPersonality(
        name="Carla Martinez",
        handle="@CageSideCarla",
        style="dramatic",
        accuracy=0.60,
        focus=["drama", "rivalries", "upsets"],
        catchphrases=[
            "OH MY GOD!!!",
            "I CANNOT believe what I just saw!",
            "This changes EVERYTHING!",
            "Are you KIDDING me?!",
            "The MMA world is SHOOK!",
            "I'm literally shaking rn",
        ],
        emoji="🔥",
    ),
    "frank": MediaPersonality(
        name="Frank Morrison",
        handle="@FightGameFrank",
        style="analytical",
        accuracy=0.75,
        focus=["analysis", "rankings", "technique"],
        catchphrases=[
            "Interesting development here.",
            "From a technical standpoint...",
            "The numbers don't lie:",
            "Let's break this down.",
            "Historically speaking...",
            "Worth noting:",
        ],
        emoji="📊",
    ),
    "ricky": MediaPersonality(
        name="Ricky Diaz",
        handle="@RumorMillRicky",
        style="speculative",
        accuracy=0.40,
        focus=["rumors", "speculation", "hot_takes"],
        catchphrases=[
            "Heard whispers that...",
            "Don't quote me but...",
            "Word on the street is...",
            "My guy told me...",
            "This might be nothing BUT...",
            "You didn't hear this from me...",
        ],
        emoji="👀",
    ),
    "chloe": MediaPersonality(
        name="Chloe Park",
        handle="@ChampionshipChloe",
        style="title_focused",
        accuracy=0.70,
        focus=["titles", "contenders", "rankings"],
        catchphrases=[
            "Title implications:",
            "Championship picture update:",
            "Next in line?",
            "The path to gold just got clearer.",
            "Contender alert!",
            "Title shot incoming?",
        ],
        emoji="🏆",
    ),
    "dfc_official": MediaPersonality(
        name="DFC Official",
        handle="@DFCOfficial",
        style="official",
        accuracy=1.0,
        focus=["announcements", "official", "events"],
        catchphrases=[
            "OFFICIAL:",
            "The DFC is proud to announce...",
            "It's official!",
            "Mark your calendars:",
            "ANNOUNCEMENT:",
            "Breaking news from DFC HQ:",
        ],
        emoji="📢",
    ),
}

def get_personality_for_news(category: NewsCategory, rumor_type: RumorType = None) -> MediaPersonality:
    """Select appropriate personality for news type."""
    if category == NewsCategory.ANNOUNCEMENT:
        return MEDIA_PERSONALITIES["dfc_official"]
    elif category == NewsCategory.TITLE:
        return MEDIA_PERSONALITIES["chloe"]
    elif category == NewsCategory.UPSET:
        return MEDIA_PERSONALITIES["carla"]
    elif category == NewsCategory.ANALYSIS or category == NewsCategory.RANKING:
        return MEDIA_PERSONALITIES["frank"]
    elif category == NewsCategory.RUMOR:
        if rumor_type in [RumorType.TRANSFER, RumorType.CONTRACT]:
            return MEDIA_PERSONALITIES["insider_mike"]
        elif rumor_type in [RumorType.RETIREMENT, RumorType.COMEBACK]:
            return random.choice([MEDIA_PERSONALITIES["frank"], MEDIA_PERSONALITIES["insider_mike"]])
        else:
            return random.choice([MEDIA_PERSONALITIES["ricky"], MEDIA_PERSONALITIES["insider_mike"]])
    else:
        # General news - rotate personalities
        return random.choice([
            MEDIA_PERSONALITIES["insider_mike"],
            MEDIA_PERSONALITIES["carla"],
            MEDIA_PERSONALITIES["frank"],
        ])


# ============================================================================
# DIVISION ABBREVIATIONS
# ============================================================================

DIVISION_ABBREV = {
    "Strawweight": "STW",
    "Flyweight": "FLW",
    "Bantamweight": "BW",
    "Featherweight": "FW",
    "Lightweight": "LW",
    "Welterweight": "WW",
    "Middleweight": "MW",
    "Light Heavyweight": "LHW",
    "Heavyweight": "HW",
}

def get_division_abbrev(division: str) -> str:
    """Get division abbreviation."""
    return DIVISION_ABBREV.get(division, division[:3].upper())


# ============================================================================
# FIGHTER CONTEXT FORMATTING
# ============================================================================

def format_fighter_context(
    name: str,
    wins: int,
    losses: int,
    rank: Optional[int],
    division: str,
    include_division: bool = True,
    draws: int = 0,
) -> str:
    """
    Format fighter name with record and rank context.
    
    Format D: "Marcus Jones (12-3, #5 WW)" or "Tommy Chen (8-5, Unranked)"
    
    Args:
        name: Fighter's name
        wins: Career wins
        losses: Career losses
        rank: Current ranking (1-15) or None if unranked
        division: Weight class
        include_division: Whether to show division abbreviation
        draws: Career draws (optional)
    
    Returns:
        Formatted string like "Marcus Jones (12-3, #5 WW)"
    """
    # Build record string
    if draws > 0:
        record = f"{wins}-{losses}-{draws}"
    else:
        record = f"{wins}-{losses}"
    
    # Build rank string
    if rank is not None and 1 <= rank <= 15:
        if include_division:
            rank_str = f"#{rank} {get_division_abbrev(division)}"
        else:
            rank_str = f"#{rank}"
    else:
        rank_str = "Unranked"
    
    return f"{name} ({record}, {rank_str})"


def format_fighter_brief(
    name: str,
    rank: Optional[int] = None,
) -> str:
    """
    Brief format for tight spaces: "Marcus Jones [#5]" or just "Marcus Jones"
    """
    if rank is not None and 1 <= rank <= 15:
        return f"{name} [#{rank}]"
    return name


def format_champion(name: str, wins: int, losses: int, division: str) -> str:
    """Format champion with title."""
    record = f"{wins}-{losses}"
    return f"🏆 {name} ({record}, {get_division_abbrev(division)} Champ)"


# ============================================================================
# NEWS ITEM
# ============================================================================

@dataclass
class NewsItem:
    """A single news item."""
    news_id: str
    category: NewsCategory
    priority: NewsPriority
    headline: str
    body: str
    week: int
    year: int
    
    # Context
    fighter_ids: List[str] = field(default_factory=list)
    division: Optional[str] = None
    camp_id: Optional[str] = None
    
    # Media
    personality: Optional[str] = None  # personality key
    attribution: str = ""
    emoji: str = ""
    
    # For rumors
    rumor_type: Optional[RumorType] = None
    rumor_accuracy: float = 0.5
    rumor_resolved: bool = False
    rumor_came_true: Optional[bool] = None
    
    # Flags
    is_player_relevant: bool = False
    is_read: bool = False
    
    @property
    def full_display(self) -> str:
        """Full news item with attribution."""
        lines = []
        if self.emoji:
            lines.append(f"{self.emoji} {self.headline}")
        else:
            lines.append(self.headline)
        
        if self.body:
            lines.append(f"   {self.body}")
        
        if self.attribution:
            lines.append(f"   {self.attribution}")
        
        return "\n".join(lines)
    
    @property
    def compact_display(self) -> str:
        """Compact single-line display."""
        emoji = f"{self.emoji} " if self.emoji else ""
        return f"{emoji}{self.headline}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "news_id": self.news_id,
            "category": self.category.value,
            "priority": self.priority.value,
            "headline": self.headline,
            "body": self.body,
            "week": self.week,
            "year": self.year,
            "fighter_ids": self.fighter_ids,
            "division": self.division,
            "camp_id": self.camp_id,
            "personality": self.personality,
            "attribution": self.attribution,
            "emoji": self.emoji,
            "rumor_type": self.rumor_type.value if self.rumor_type else None,
            "rumor_accuracy": self.rumor_accuracy,
            "rumor_resolved": self.rumor_resolved,
            "rumor_came_true": self.rumor_came_true,
            "is_player_relevant": self.is_player_relevant,
            "is_read": self.is_read,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsItem':
        return cls(
            news_id=data["news_id"],
            category=NewsCategory(data["category"]),
            priority=NewsPriority(data["priority"]),
            headline=data["headline"],
            body=data.get("body", ""),
            week=data["week"],
            year=data["year"],
            fighter_ids=data.get("fighter_ids", []),
            division=data.get("division"),
            camp_id=data.get("camp_id"),
            personality=data.get("personality"),
            attribution=data.get("attribution", ""),
            emoji=data.get("emoji", ""),
            rumor_type=RumorType(data["rumor_type"]) if data.get("rumor_type") else None,
            rumor_accuracy=data.get("rumor_accuracy", 0.5),
            rumor_resolved=data.get("rumor_resolved", False),
            rumor_came_true=data.get("rumor_came_true"),
            is_player_relevant=data.get("is_player_relevant", False),
            is_read=data.get("is_read", False),
        )


# ============================================================================
# NEWS GENERATORS
# ============================================================================

def generate_fight_result_news(
    winner_name: str,
    winner_record: Tuple[int, int],
    winner_rank: Optional[int],
    loser_name: str,
    loser_record: Tuple[int, int],
    loser_rank: Optional[int],
    division: str,
    method: str,
    round_num: int,
    is_title_fight: bool = False,
    is_upset: bool = False,
    winner_id: str = "",
    loser_id: str = "",
    week: int = 1,
    year: int = 1,
    player_camp_id: str = "",
    winner_camp_id: str = "",
    loser_camp_id: str = "",
) -> NewsItem:
    """Generate news item for a fight result."""
    
    winner_ctx = format_fighter_context(
        winner_name, winner_record[0], winner_record[1], 
        winner_rank, division
    )
    loser_ctx = format_fighter_context(
        loser_name, loser_record[0], loser_record[1],
        loser_rank, division
    )
    
    # Determine category and priority
    if is_title_fight:
        category = NewsCategory.TITLE
        priority = NewsPriority.CRITICAL
        personality = MEDIA_PERSONALITIES["chloe"]
    elif is_upset:
        category = NewsCategory.UPSET
        priority = NewsPriority.HIGH
        personality = MEDIA_PERSONALITIES["carla"]
    else:
        category = NewsCategory.RESULT
        # Priority based on ranks
        if winner_rank and winner_rank <= 5:
            priority = NewsPriority.HIGH
        elif winner_rank and winner_rank <= 10:
            priority = NewsPriority.MEDIUM
        else:
            priority = NewsPriority.LOW
        personality = random.choice([
            MEDIA_PERSONALITIES["insider_mike"],
            MEDIA_PERSONALITIES["frank"],
        ])
    
    # Check player relevance
    is_player_relevant = (
        winner_camp_id == player_camp_id or 
        loser_camp_id == player_camp_id
    )
    if is_player_relevant:
        priority = NewsPriority.CRITICAL
    
    # Generate headline and body
    if is_title_fight:
        catchphrase = random.choice(personality.catchphrases)
        headline = f"{catchphrase} {winner_ctx} claims {get_division_abbrev(division)} gold!"
        body = f"Defeats {loser_ctx} via {method} in round {round_num}"
    elif is_upset:
        catchphrase = random.choice(personality.catchphrases)
        headline = f"UPSET! {winner_ctx} defeats {loser_ctx}!"
        body = f"{method} in round {round_num}. {catchphrase}"
    else:
        headline = f"{winner_ctx} defeats {loser_ctx}"
        body = f"{method}, Round {round_num}"
    
    return NewsItem(
        news_id=f"fight_{week}_{year}_{winner_id}",
        category=category,
        priority=priority,
        headline=headline,
        body=body,
        week=week,
        year=year,
        fighter_ids=[winner_id, loser_id],
        division=division,
        camp_id=winner_camp_id,
        personality=personality.handle if hasattr(personality, 'handle') else None,
        attribution=personality.get_attribution() if personality else "",
        emoji="🏆" if is_title_fight else ("⚡" if is_upset else "🥊"),
        is_player_relevant=is_player_relevant,
    )


def generate_signing_news(
    fighter_name: str,
    fighter_record: Tuple[int, int],
    fighter_rank: Optional[int],
    division: str,
    camp_name: str,
    camp_id: str,
    fighter_id: str,
    week: int,
    year: int,
    player_camp_id: str = "",
    is_prospect: bool = False,
    potential_grade: str = "",
) -> NewsItem:
    """Generate news for a fighter signing."""
    
    is_player = camp_id == player_camp_id
    
    if is_prospect:
        fighter_ctx = f"{fighter_name} ({fighter_record[0]}-{fighter_record[1]})"
        if potential_grade:
            body = f"Potential: {potential_grade}. {get_division_abbrev(division)} division."
        else:
            body = f"Young prospect joins the {get_division_abbrev(division)} division."
    else:
        fighter_ctx = format_fighter_context(
            fighter_name, fighter_record[0], fighter_record[1],
            fighter_rank, division
        )
        body = ""
    
    if is_player:
        personality = MEDIA_PERSONALITIES["dfc_official"]
        headline = f"SIGNED: {camp_name} adds {fighter_ctx}"
        priority = NewsPriority.CRITICAL
    elif fighter_rank and fighter_rank <= 10:
        personality = MEDIA_PERSONALITIES["insider_mike"]
        catchphrase = random.choice(personality.catchphrases)
        headline = f"{catchphrase} {camp_name} signs {fighter_ctx}"
        priority = NewsPriority.HIGH
    else:
        personality = MEDIA_PERSONALITIES["frank"]
        headline = f"{camp_name} signs {fighter_ctx}"
        priority = NewsPriority.LOW
    
    return NewsItem(
        news_id=f"sign_{week}_{year}_{fighter_id}",
        category=NewsCategory.SIGNING,
        priority=priority,
        headline=headline,
        body=body,
        week=week,
        year=year,
        fighter_ids=[fighter_id],
        division=division,
        camp_id=camp_id,
        personality=personality.handle,
        attribution=personality.get_attribution(),
        emoji="✍️",
        is_player_relevant=is_player,
    )


def generate_retirement_news(
    fighter_name: str,
    fighter_record: Tuple[int, int],
    division: str,
    fighter_id: str,
    week: int,
    year: int,
    career_highlights: List[str] = None,
    was_champion: bool = False,
) -> NewsItem:
    """Generate retirement announcement."""
    
    personality = MEDIA_PERSONALITIES["frank"]
    fighter_ctx = f"{fighter_name} ({fighter_record[0]}-{fighter_record[1]})"
    
    if was_champion:
        headline = f"End of an era: Former champion {fighter_ctx} retires"
        priority = NewsPriority.HIGH
    else:
        headline = f"{fighter_ctx} announces retirement"
        priority = NewsPriority.MEDIUM
    
    if career_highlights:
        body = f"Career highlights: {', '.join(career_highlights[:3])}"
    else:
        body = f"Competed in the {division} division."
    
    return NewsItem(
        news_id=f"retire_{week}_{year}_{fighter_id}",
        category=NewsCategory.RETIREMENT,
        priority=priority,
        headline=headline,
        body=body,
        week=week,
        year=year,
        fighter_ids=[fighter_id],
        division=division,
        personality=personality.handle,
        attribution=personality.get_attribution(),
        emoji="👋",
    )


def generate_ranking_news(
    fighter_name: str,
    fighter_record: Tuple[int, int],
    division: str,
    old_rank: Optional[int],
    new_rank: Optional[int],
    fighter_id: str,
    week: int,
    year: int,
) -> NewsItem:
    """Generate ranking movement news."""
    
    personality = MEDIA_PERSONALITIES["chloe"]
    
    if old_rank is None and new_rank is not None:
        # Entered rankings
        headline = f"NEW CONTENDER: {fighter_name} enters {get_division_abbrev(division)} rankings at #{new_rank}"
        emoji = "📈"
        priority = NewsPriority.MEDIUM
    elif new_rank is None and old_rank is not None:
        # Dropped out
        headline = f"{fighter_name} falls out of {get_division_abbrev(division)} rankings"
        emoji = "📉"
        priority = NewsPriority.LOW
    elif old_rank and new_rank and new_rank < old_rank:
        # Moved up
        spots = old_rank - new_rank
        fighter_ctx = format_fighter_context(
            fighter_name, fighter_record[0], fighter_record[1],
            new_rank, division
        )
        if spots >= 5:
            catchphrase = random.choice(personality.catchphrases)
            headline = f"{catchphrase} {fighter_ctx} jumps {spots} spots!"
            priority = NewsPriority.HIGH
        else:
            headline = f"{fighter_ctx} climbs {spots} spot{'s' if spots > 1 else ''}"
            priority = NewsPriority.LOW
        emoji = "📈"
    else:
        # Moved down
        spots = new_rank - old_rank if new_rank and old_rank else 0
        headline = f"{fighter_name} drops {spots} spot{'s' if spots > 1 else ''} to #{new_rank}"
        emoji = "📉"
        priority = NewsPriority.LOW
    
    return NewsItem(
        news_id=f"rank_{week}_{year}_{fighter_id}",
        category=NewsCategory.RANKING,
        priority=priority,
        headline=headline,
        body="",
        week=week,
        year=year,
        fighter_ids=[fighter_id],
        division=division,
        personality=personality.handle,
        attribution=personality.get_attribution(),
        emoji=emoji,
    )


def generate_contract_news(
    fighter_name: str,
    fighter_record: Tuple[int, int],
    fighter_rank: Optional[int],
    division: str,
    fighter_id: str,
    camp_name: str,
    camp_id: str,
    weeks_remaining: int,
    week: int,
    year: int,
    player_camp_id: str = "",
) -> NewsItem:
    """Generate contract expiration warning."""
    
    is_player = camp_id == player_camp_id
    fighter_ctx = format_fighter_context(
        fighter_name, fighter_record[0], fighter_record[1],
        fighter_rank, division
    )
    
    if weeks_remaining <= 2:
        headline = f"⚠️ CONTRACT EXPIRING: {fighter_ctx}"
        body = f"Deal with {camp_name} expires in {weeks_remaining} week{'s' if weeks_remaining > 1 else ''}!"
        priority = NewsPriority.CRITICAL if is_player else NewsPriority.MEDIUM
        personality = MEDIA_PERSONALITIES["insider_mike"]
    else:
        headline = f"Contract watch: {fighter_ctx}"
        body = f"{weeks_remaining} weeks remaining with {camp_name}"
        priority = NewsPriority.HIGH if is_player else NewsPriority.LOW
        personality = MEDIA_PERSONALITIES["frank"]
    
    return NewsItem(
        news_id=f"contract_{week}_{year}_{fighter_id}",
        category=NewsCategory.CONTRACT,
        priority=priority,
        headline=headline,
        body=body,
        week=week,
        year=year,
        fighter_ids=[fighter_id],
        division=division,
        camp_id=camp_id,
        personality=personality.handle,
        attribution=personality.get_attribution(),
        emoji="📋",
        is_player_relevant=is_player,
    )


def generate_milestone_news(
    fighter_name: str,
    fighter_record: Tuple[int, int],
    fighter_rank: Optional[int],
    division: str,
    fighter_id: str,
    milestone_type: str,
    milestone_detail: str,
    week: int,
    year: int,
) -> NewsItem:
    """Generate milestone achievement news."""
    
    fighter_ctx = format_fighter_context(
        fighter_name, fighter_record[0], fighter_record[1],
        fighter_rank, division
    )
    
    milestones = {
        "debut_win": ("🌟", f"Successful debut! {fighter_ctx} wins first pro fight"),
        "10_wins": ("🔟", f"Double digits! {fighter_ctx} reaches 10 career wins"),
        "first_title_shot": ("🎯", f"Title shot earned! {fighter_ctx} gets championship opportunity"),
        "ko_streak": ("💥", f"Knockout artist! {fighter_ctx} extends KO streak to {milestone_detail}"),
        "win_streak": ("🔥", f"On fire! {fighter_ctx} extends win streak to {milestone_detail}"),
        "comeback": ("💪", f"The comeback! {fighter_ctx} returns with a victory"),
        "revenge": ("⚔️", f"Revenge! {fighter_ctx} avenges previous loss"),
    }
    
    emoji, headline = milestones.get(milestone_type, ("⭐", f"Milestone: {fighter_ctx} - {milestone_detail}"))
    
    personality = MEDIA_PERSONALITIES["carla"]
    
    return NewsItem(
        news_id=f"mile_{week}_{year}_{fighter_id}",
        category=NewsCategory.MILESTONE,
        priority=NewsPriority.MEDIUM,
        headline=headline,
        body=milestone_detail if milestone_type not in milestones else "",
        week=week,
        year=year,
        fighter_ids=[fighter_id],
        division=division,
        personality=personality.handle,
        attribution=personality.get_attribution(),
        emoji=emoji,
    )


# ============================================================================
# RUMOR GENERATION
# ============================================================================

# Rumor accuracy by type
RUMOR_ACCURACY = {
    RumorType.TRANSFER: 0.60,
    RumorType.FIGHT_TALKS: 0.50,
    RumorType.INJURY: 0.70,
    RumorType.RETIREMENT: 0.40,
    RumorType.WEIGHT_CHANGE: 0.50,
    RumorType.TITLE_SHOT: 0.65,
    RumorType.CAMP_DRAMA: 0.45,
    RumorType.SUPERFIGHT: 0.30,
    RumorType.COMEBACK: 0.55,
    RumorType.CONTRACT: 0.70,
}

# Rumor templates by type
RUMOR_TEMPLATES = {
    RumorType.TRANSFER: [
        "Sources say {fighter} is unhappy at {camp} and exploring options",
        "Multiple camps have inquired about {fighter}'s availability",
        "Hearing {fighter} could be on the move soon",
        "{fighter} reportedly 'looking for a change of scenery'",
        "Contract talks between {fighter} and {camp} have stalled",
    ],
    RumorType.FIGHT_TALKS: [
        "Talks underway for {fighter1} vs {fighter2}",
        "{fighter1} and {fighter2} have agreed in principle to fight",
        "Hearing {fighter1} vs {fighter2} is close to being finalized",
        "{fighter1} has called out {fighter2}, and {fighter2}'s camp is interested",
        "Sources: {fighter1} vs {fighter2} targeted for upcoming card",
    ],
    RumorType.INJURY: [
        "{fighter} reportedly dealing with an undisclosed injury",
        "Hearing {fighter} may be nursing a {body_part} issue",
        "{fighter}'s camp denies injury rumors, but sources say otherwise",
        "{fighter} has been limited in training due to minor injury",
    ],
    RumorType.RETIREMENT: [
        "Sources close to {fighter} say retirement is being considered",
        "{fighter} reportedly 'evaluating future' after recent fights",
        "Whispers that {fighter} may be ready to hang up the gloves",
        "{fighter}'s camp denies retirement talk, but sources aren't sure",
    ],
    RumorType.WEIGHT_CHANGE: [
        "{fighter} eyeing move to {division}",
        "Sources say {fighter} has been training at {division} weight",
        "Hearing {fighter} wants to test themselves at {division}",
        "{fighter} reportedly interested in two-division run",
    ],
    RumorType.TITLE_SHOT: [
        "Inside sources say {fighter} is next in line for title shot",
        "{fighter} has been promised next title shot, per sources",
        "DFC brass high on {fighter} for championship opportunity",
        "Title shot for {fighter}? Sources say it's being discussed",
    ],
    RumorType.CAMP_DRAMA: [
        "Tension reported between {fighter} and coaching staff",
        "Sources say {camp} dealing with internal issues",
        "Hearing {fighter} and teammates not seeing eye to eye",
        "Camp shake-up? {fighter}'s situation at {camp} 'fluid'",
    ],
    RumorType.SUPERFIGHT: [
        "Superfight talks: {fighter1} vs {fighter2} being discussed",
        "Cross-division superfight in the works? {fighter1} vs {fighter2}",
        "Dream matchup {fighter1} vs {fighter2} gaining traction",
    ],
    RumorType.COMEBACK: [
        "{fighter} reportedly planning return to competition",
        "Sources say {fighter} has resumed training",
        "Hearing {fighter} targeting return in coming months",
    ],
    RumorType.CONTRACT: [
        "{fighter}'s contract negotiations 'progressing well'",
        "Hearing {fighter} seeking significant raise in new deal",
        "{fighter} and {camp} 'far apart' on new contract terms",
        "Sources: {fighter} has multiple offers on the table",
    ],
}

BODY_PARTS = ["knee", "shoulder", "back", "hand", "foot", "ankle", "elbow", "hip"]


def generate_rumor(
    rumor_type: RumorType,
    fighter_name: str,
    fighter_id: str,
    division: str,
    week: int,
    year: int,
    camp_name: str = "",
    fighter2_name: str = "",
    fighter2_id: str = "",
    target_division: str = "",
) -> NewsItem:
    """Generate a rumor news item."""
    
    # Select personality based on rumor type
    personality = get_personality_for_news(NewsCategory.RUMOR, rumor_type)
    
    # Get template
    templates = RUMOR_TEMPLATES.get(rumor_type, ["{fighter} rumor"])
    template = random.choice(templates)
    
    # Fill in template
    body_part = random.choice(BODY_PARTS)
    target_div = target_division or "higher weight class"
    
    headline = template.format(
        fighter=fighter_name,
        fighter1=fighter_name,
        fighter2=fighter2_name or "a top contender",
        camp=camp_name or "their camp",
        body_part=body_part,
        division=target_div,
    )
    
    # Add personality catchphrase
    catchphrase = random.choice(personality.catchphrases)
    
    # Determine priority
    accuracy = RUMOR_ACCURACY.get(rumor_type, 0.5)
    if accuracy >= 0.7:
        priority = NewsPriority.MEDIUM
    else:
        priority = NewsPriority.LOW
    
    fighter_ids = [fighter_id]
    if fighter2_id:
        fighter_ids.append(fighter2_id)
    
    return NewsItem(
        news_id=f"rumor_{week}_{year}_{fighter_id}_{rumor_type.value}",
        category=NewsCategory.RUMOR,
        priority=priority,
        headline=f"{catchphrase} {headline}",
        body="",
        week=week,
        year=year,
        fighter_ids=fighter_ids,
        division=division,
        personality=personality.handle,
        attribution=personality.get_attribution(),
        emoji="💬",
        rumor_type=rumor_type,
        rumor_accuracy=accuracy * personality.accuracy,  # Combined accuracy
    )


# ============================================================================
# NEWS SYSTEM
# ============================================================================

class NewsSystem:
    """
    Manages all news and rumors for the game.
    """
    
    def __init__(self):
        self._news_archive: List[NewsItem] = []
        self._current_week_news: List[NewsItem] = []
        self._active_rumors: List[NewsItem] = []
        self._news_counter = 0
        self._default_filter = NewsFilter.HEADLINES
        
        # Player context
        self._player_camp_id: str = ""
        self._player_divisions: Set[str] = set()
        self._player_fighter_ids: Set[str] = set()
    
    def set_player_context(
        self,
        camp_id: str,
        divisions: List[str],
        fighter_ids: List[str],
    ) -> None:
        """Set player's context for relevance filtering."""
        self._player_camp_id = camp_id
        self._player_divisions = set(divisions)
        self._player_fighter_ids = set(fighter_ids)
    
    def add_news(self, news: NewsItem) -> None:
        """Add a news item."""
        self._news_counter += 1
        if not news.news_id:
            news.news_id = f"news_{self._news_counter}"
        
        # Check player relevance
        if any(fid in self._player_fighter_ids for fid in news.fighter_ids):
            news.is_player_relevant = True
            news.priority = NewsPriority.CRITICAL
        elif news.camp_id == self._player_camp_id:
            news.is_player_relevant = True
            news.priority = NewsPriority.CRITICAL
        elif news.division in self._player_divisions:
            if news.priority.value < NewsPriority.HIGH.value:
                news.priority = NewsPriority.HIGH
        
        self._current_week_news.append(news)
        
        if news.category == NewsCategory.RUMOR:
            self._active_rumors.append(news)
    
    def end_week(self) -> None:
        """Archive current week's news and prepare for next week."""
        self._news_archive.extend(self._current_week_news)
        self._current_week_news = []
    
    def get_filtered_news(
        self,
        filter_type: NewsFilter = None,
        max_items: int = 20,
    ) -> List[NewsItem]:
        """Get news filtered by type."""
        filter_type = filter_type or self._default_filter
        news = self._current_week_news.copy()
        
        if filter_type == NewsFilter.HEADLINES:
            # Top stories by priority
            news = sorted(news, key=lambda n: (-n.priority.value, -n.is_player_relevant))
            return news[:5]
        
        elif filter_type == NewsFilter.MY_CAMP:
            return [n for n in news if n.is_player_relevant][:max_items]
        
        elif filter_type == NewsFilter.MY_DIVISIONS:
            return [
                n for n in news 
                if n.division in self._player_divisions or n.is_player_relevant
            ][:max_items]
        
        elif filter_type == NewsFilter.RUMORS_ONLY:
            return [n for n in news if n.category == NewsCategory.RUMOR][:max_items]
        
        elif filter_type == NewsFilter.RESULTS_ONLY:
            return [
                n for n in news 
                if n.category in [NewsCategory.RESULT, NewsCategory.TITLE, NewsCategory.UPSET]
            ][:max_items]
        
        else:  # ALL_NEWS
            return sorted(news, key=lambda n: (-n.priority.value,))[:max_items]
    
    def get_condensed_results(self) -> Dict[str, Dict[str, int]]:
        """Get condensed fight results by division."""
        results = {}
        
        for news in self._current_week_news:
            if news.category in [NewsCategory.RESULT, NewsCategory.TITLE, NewsCategory.UPSET]:
                div = news.division or "Unknown"
                if div not in results:
                    results[div] = {"total": 0, "finishes": 0, "decisions": 0}
                
                results[div]["total"] += 1
                
                # Check method in body
                body_lower = news.body.lower() if news.body else ""
                if any(x in body_lower for x in ["ko", "tko", "submission"]):
                    results[div]["finishes"] += 1
                else:
                    results[div]["decisions"] += 1
        
        return results
    
    def resolve_rumors(self, week: int, year: int) -> List[NewsItem]:
        """
        Check if any rumors should be resolved.
        Returns list of follow-up news items.
        """
        follow_ups = []
        still_active = []
        
        for rumor in self._active_rumors:
            # Rumors resolve after 2-6 weeks
            weeks_old = (year - rumor.year) * 52 + (week - rumor.week)
            
            if weeks_old >= random.randint(2, 6):
                # Time to resolve
                came_true = random.random() < rumor.rumor_accuracy
                rumor.rumor_resolved = True
                rumor.rumor_came_true = came_true
                
                # Generate follow-up if it came true
                if came_true and rumor.rumor_type:
                    follow_up = self._generate_rumor_resolution(rumor, week, year)
                    if follow_up:
                        follow_ups.append(follow_up)
            else:
                still_active.append(rumor)
        
        self._active_rumors = still_active
        return follow_ups
    
    def _generate_rumor_resolution(
        self,
        rumor: NewsItem,
        week: int,
        year: int,
    ) -> Optional[NewsItem]:
        """Generate follow-up news when a rumor comes true."""
        # This would be expanded based on rumor type
        # For now, just acknowledge the rumor was accurate
        personality = MEDIA_PERSONALITIES["insider_mike"]
        
        return NewsItem(
            news_id=f"resolved_{rumor.news_id}",
            category=NewsCategory.ANNOUNCEMENT,
            priority=NewsPriority.MEDIUM,
            headline=f"CONFIRMED: Earlier rumors prove accurate",
            body=f"As reported: {rumor.headline.split(': ', 1)[-1] if ': ' in rumor.headline else rumor.headline}",
            week=week,
            year=year,
            fighter_ids=rumor.fighter_ids,
            division=rumor.division,
            personality=personality.handle,
            attribution=personality.get_attribution(),
            emoji="✅",
        )
    
    def set_default_filter(self, filter_type: NewsFilter) -> None:
        """Set the default news filter."""
        self._default_filter = filter_type
    
    def get_news_archive(
        self,
        weeks_back: int = 4,
        current_week: int = 1,
        current_year: int = 1,
    ) -> List[NewsItem]:
        """Get archived news from recent weeks."""
        cutoff_week = current_week - weeks_back
        cutoff_year = current_year
        if cutoff_week <= 0:
            cutoff_week += 52
            cutoff_year -= 1
        
        return [
            n for n in self._news_archive
            if (n.year > cutoff_year) or (n.year == cutoff_year and n.week >= cutoff_week)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "news_archive": [n.to_dict() for n in self._news_archive[-200:]],  # Keep last 200
            "current_week_news": [n.to_dict() for n in self._current_week_news],
            "active_rumors": [n.to_dict() for n in self._active_rumors],
            "news_counter": self._news_counter,
            "default_filter": self._default_filter.value,
            "player_camp_id": self._player_camp_id,
            "player_divisions": list(self._player_divisions),
            "player_fighter_ids": list(self._player_fighter_ids),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsSystem':
        system = cls()
        system._news_archive = [NewsItem.from_dict(n) for n in data.get("news_archive", [])]
        system._current_week_news = [NewsItem.from_dict(n) for n in data.get("current_week_news", [])]
        system._active_rumors = [NewsItem.from_dict(n) for n in data.get("active_rumors", [])]
        system._news_counter = data.get("news_counter", 0)
        system._default_filter = NewsFilter(data.get("default_filter", "headlines"))
        system._player_camp_id = data.get("player_camp_id", "")
        system._player_divisions = set(data.get("player_divisions", []))
        system._player_fighter_ids = set(data.get("player_fighter_ids", []))
        return system


# ============================================================================
# DISPLAY FORMATTING
# ============================================================================

def format_news_display(
    news_items: List[NewsItem],
    week: int,
    year: int,
    show_attribution: bool = True,
    max_width: int = 65,
) -> List[str]:
    """Format news items for display."""
    lines = []
    
    lines.append("═" * max_width)
    lines.append(f"📰 NEWS & RUMORS".center(max_width))
    lines.append(f"Week {week}, Year {year}".center(max_width))
    lines.append("═" * max_width)
    
    # Group by category for display
    critical = [n for n in news_items if n.priority == NewsPriority.CRITICAL]
    high = [n for n in news_items if n.priority == NewsPriority.HIGH and n not in critical]
    other = [n for n in news_items if n not in critical and n not in high]
    
    if critical:
        lines.append("")
        lines.append("🔴 BREAKING")
        for news in critical:
            lines.append(f"  {news.compact_display}")
            if news.body:
                lines.append(f"     {news.body}")
            if show_attribution and news.attribution:
                lines.append(f"     {news.attribution}")
    
    if high:
        lines.append("")
        lines.append("🟠 TOP STORIES")
        for news in high:
            lines.append(f"  {news.compact_display}")
            if news.body:
                lines.append(f"     {news.body}")
    
    # Separate player-relevant news
    player_news = [n for n in news_items if n.is_player_relevant and n not in critical]
    if player_news:
        lines.append("")
        lines.append("👤 YOUR CAMP")
        for news in player_news:
            lines.append(f"  {news.compact_display}")
    
    # Rumors section
    rumors = [n for n in news_items if n.category == NewsCategory.RUMOR]
    if rumors:
        lines.append("")
        lines.append("💬 RUMOR MILL")
        for news in rumors[:4]:  # Max 4 rumors shown
            lines.append(f"  {news.compact_display}")
            if show_attribution and news.attribution:
                lines.append(f"     {news.attribution}")
    
    lines.append("")
    lines.append("─" * max_width)
    
    return lines


def format_condensed_results(
    results: Dict[str, Dict[str, int]],
) -> List[str]:
    """Format condensed results for minor fights."""
    lines = []
    
    if not results:
        return lines
    
    lines.append("📋 OTHER RESULTS THIS WEEK")
    
    for division, counts in sorted(results.items()):
        total = counts["total"]
        finishes = counts["finishes"]
        decisions = counts["decisions"]
        
        if finishes and decisions:
            detail = f"{finishes} finish{'es' if finishes > 1 else ''}, {decisions} decision{'s' if decisions > 1 else ''}"
        elif finishes:
            detail = f"{finishes} finish{'es' if finishes > 1 else ''}"
        else:
            detail = f"{decisions} decision{'s' if decisions > 1 else ''}"
        
        lines.append(f"  {division}: {total} fight{'s' if total > 1 else ''} ({detail})")
    
    return lines


def format_filter_menu() -> List[str]:
    """Format the news filter menu."""
    return [
        "",
        "NEWS FILTER",
        "  [1] Headlines Only (top 5 stories)",
        "  [2] My Camp (your fighters)",
        "  [3] My Divisions (weight classes you compete in)",
        "  [4] All News (everything)",
        "  [5] Rumors Only",
        "  [6] Results Only",
        "",
        "  [S] Set as default filter",
        "  [Enter] Back",
        "",
    ]


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "NewsPriority", "NewsCategory", "RumorType", "NewsFilter",
    
    # Data classes
    "NewsItem", "MediaPersonality",
    
    # System
    "NewsSystem",
    
    # Generators
    "generate_fight_result_news", "generate_signing_news",
    "generate_retirement_news", "generate_ranking_news",
    "generate_contract_news", "generate_milestone_news",
    "generate_rumor",
    
    # Formatting
    "format_fighter_context", "format_fighter_brief", "format_champion",
    "format_news_display", "format_condensed_results", "format_filter_menu",
    "get_division_abbrev",
    
    # Constants
    "MEDIA_PERSONALITIES", "DIVISION_ABBREV", "RUMOR_ACCURACY",
]
