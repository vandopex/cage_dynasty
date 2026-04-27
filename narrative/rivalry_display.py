# narrative/rivalry_display.py
# Module: Rivalry Display & Integration
# Lines: ~680
#
# Enhanced rivalry display with CLI integration helpers.
# Works with existing rivalry.py for core logic.

"""
Cage Dynasty - Rivalry Display & Integration

This module provides enhanced rivalry features for the CLI:
- Fight preview rivalry hints
- Post-fight rivalry detection and display
- Rivalry news generation
- Fighter rivalry summaries
- Division rivalry overview

The core rivalry logic is in rivalry.py - this module
handles display and CLI integration.

USAGE:
    from narrative.rivalry_display import (
        RivalryDisplayHelper,
        get_fight_rivalry_preview,
        process_fight_for_rivalry,
        format_rivalry_news,
        get_fighter_rivalries_display,
    )
    
    # Before a fight - show rivalry context
    preview = get_fight_rivalry_preview(fighter1_id, fighter2_id, system)
    if preview:
        print(preview)
    
    # After a fight - detect and display rivalry changes
    news = process_fight_for_rivalry(fight_context, system)
    for item in news:
        print(item)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# IMPORTS FROM RIVALRY.PY
# ============================================================================

# These would normally import from narrative.rivalry
# For standalone testing, we define minimal versions here

class RivalryType(Enum):
    """Types of rivalries that can form"""
    COMPETITIVE = "competitive"
    BAD_BLOOD = "bad_blood"
    TITLE_DISPUTE = "title_dispute"
    GYM_WAR = "gym_war"
    NATIONAL_PRIDE = "national_pride"
    STYLE_CLASH = "style_clash"
    GENERATIONAL = "generational"
    REVENGE = "revenge"


class RivalryIntensity(Enum):
    """Intensity levels of rivalries"""
    BUDDING = 1
    NOTABLE = 2
    HEATED = 3
    FIERCE = 4
    LEGENDARY = 5


# Intensity thresholds
INTENSITY_THRESHOLDS = {
    RivalryIntensity.BUDDING: (10, 29),
    RivalryIntensity.NOTABLE: (30, 49),
    RivalryIntensity.HEATED: (50, 69),
    RivalryIntensity.FIERCE: (70, 89),
    RivalryIntensity.LEGENDARY: (90, 100),
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RivalryPreview:
    """Preview of rivalry context before a fight."""
    has_rivalry: bool
    fighter1_name: str
    fighter2_name: str
    rivalry_type: Optional[str] = None
    intensity: Optional[str] = None
    score: int = 0
    head_to_head: str = "0-0-0"
    series_leader: Optional[str] = None
    is_rematch: bool = False
    is_trilogy: bool = False
    key_events: List[str] = field(default_factory=list)
    narrative_hook: str = ""


@dataclass
class RivalryNewsItem:
    """A rivalry-related news item."""
    headline: str
    category: str  # "rivalry_new", "rivalry_escalate", "rivalry_update"
    fighters: List[str]
    intensity_change: int = 0  # Score change
    is_major: bool = False  # Headline-worthy
    description: str = ""


@dataclass
class FighterRivalrySummary:
    """Summary of a fighter's rivalries."""
    fighter_name: str
    fighter_id: str
    total_rivalries: int
    active_rivalries: int
    biggest_rival: Optional[str] = None
    biggest_rivalry_score: int = 0
    legendary_rivalries: int = 0
    heated_rivalries: int = 0
    rivalry_list: List[Tuple[str, str, int]] = field(default_factory=list)  # (name, type, score)


# ============================================================================
# INTENSITY DESCRIPTIONS AND EMOJIS
# ============================================================================

INTENSITY_EMOJIS = {
    "BUDDING": "🌱",
    "NOTABLE": "⚡",
    "HEATED": "🔥",
    "FIERCE": "💥",
    "LEGENDARY": "👑",
}

INTENSITY_DESCRIPTIONS = {
    "BUDDING": "A rivalry beginning to take shape",
    "NOTABLE": "A notable rivalry that fans are watching",
    "HEATED": "A heated rivalry with real animosity",
    "FIERCE": "A fierce rivalry that captivates the sport",
    "LEGENDARY": "A legendary rivalry for the ages",
}

TYPE_DESCRIPTIONS = {
    "competitive": "Mutual respect, fierce competition",
    "bad_blood": "Personal animosity and genuine dislike",
    "title_dispute": "Championship stakes drive this rivalry",
    "gym_war": "Former teammates turned enemies",
    "national_pride": "Countries clash through these fighters",
    "style_clash": "Striker vs grappler defines this matchup",
    "generational": "Old guard vs new generation",
    "revenge": "One fighter seeks redemption",
}

TYPE_EMOJIS = {
    "competitive": "🤝",
    "bad_blood": "😤",
    "title_dispute": "🏆",
    "gym_war": "🏋️",
    "national_pride": "🌍",
    "style_clash": "⚔️",
    "generational": "👴👶",
    "revenge": "🔄",
}


# ============================================================================
# NARRATIVE HOOKS
# ============================================================================

RIVALRY_HOOKS = {
    "rematch": [
        "The rematch everyone wanted is finally here!",
        "Round two in this growing rivalry.",
        "Can the loser even the score?",
    ],
    "trilogy": [
        "The trilogy fight to end all debates!",
        "1-1 going into the deciding fight.",
        "The rubber match of an epic rivalry.",
    ],
    "revenge": [
        "{loser} seeks revenge for the devastating loss.",
        "Redemption is on the line for {loser}.",
        "{loser} wants to avenge that defeat.",
    ],
    "title": [
        "Championship gold adds fuel to the fire.",
        "The belt is on the line in this rivalry fight.",
        "Title implications in this heated matchup.",
    ],
    "bad_blood": [
        "These two genuinely don't like each other.",
        "The animosity is palpable.",
        "Personal beef drives this fight.",
    ],
    "gym_war": [
        "Former training partners collide.",
        "They know each other's secrets.",
        "Gym loyalty tested in the cage.",
    ],
    "legendary": [
        "A rivalry for the history books.",
        "Two legends write another chapter.",
        "The greatest rivalry in the sport.",
    ],
}


# ============================================================================
# PREVIEW FUNCTIONS
# ============================================================================

def get_fight_rivalry_preview(
    fighter1_id: str,
    fighter2_id: str,
    fighter1_name: str,
    fighter2_name: str,
    rivalry_data: Optional[Dict[str, Any]] = None,
    is_title_fight: bool = False,
) -> RivalryPreview:
    """
    Generate a rivalry preview for an upcoming fight.
    
    Args:
        fighter1_id: First fighter's ID
        fighter2_id: Second fighter's ID
        fighter1_name: First fighter's name
        fighter2_name: Second fighter's name
        rivalry_data: Existing rivalry data dict (from Rivalry.to_dict())
        is_title_fight: Whether this is a title fight
        
    Returns:
        RivalryPreview with context for display
    """
    if rivalry_data is None:
        # No existing rivalry
        preview = RivalryPreview(
            has_rivalry=False,
            fighter1_name=fighter1_name,
            fighter2_name=fighter2_name,
        )
        
        if is_title_fight:
            preview.narrative_hook = "Championship stakes could spark a rivalry."
        
        return preview
    
    # Extract rivalry info
    score = rivalry_data.get("score", 0)
    fights = rivalry_data.get("fights", 0)
    f1_wins = rivalry_data.get("fighter1_wins", 0)
    f2_wins = rivalry_data.get("fighter2_wins", 0)
    draws = rivalry_data.get("draws", 0)
    rivalry_type = rivalry_data.get("rivalry_type", "competitive")
    
    # Determine intensity
    intensity = "BUDDING"
    for int_level, (min_s, max_s) in INTENSITY_THRESHOLDS.items():
        if min_s <= score <= max_s:
            intensity = int_level.name
            break
    if score >= 90:
        intensity = "LEGENDARY"
    
    # Head to head
    head_to_head = f"{f1_wins}-{f2_wins}-{draws}"
    
    # Series leader
    series_leader = None
    if f1_wins > f2_wins:
        series_leader = fighter1_name
    elif f2_wins > f1_wins:
        series_leader = fighter2_name
    
    # Key events (last 3)
    key_events = []
    history = rivalry_data.get("history", [])
    for event in history[-3:]:
        key_events.append(event.get("description", ""))
    
    # Generate narrative hook
    narrative_hook = _generate_narrative_hook(
        rivalry_type=rivalry_type,
        intensity=intensity,
        fights=fights,
        f1_wins=f1_wins,
        f2_wins=f2_wins,
        fighter1_name=fighter1_name,
        fighter2_name=fighter2_name,
        is_title_fight=is_title_fight,
    )
    
    return RivalryPreview(
        has_rivalry=True,
        fighter1_name=fighter1_name,
        fighter2_name=fighter2_name,
        rivalry_type=rivalry_type,
        intensity=intensity,
        score=score,
        head_to_head=head_to_head,
        series_leader=series_leader,
        is_rematch=(fights == 1),
        is_trilogy=(fights == 2),
        key_events=key_events,
        narrative_hook=narrative_hook,
    )


def _generate_narrative_hook(
    rivalry_type: str,
    intensity: str,
    fights: int,
    f1_wins: int,
    f2_wins: int,
    fighter1_name: str,
    fighter2_name: str,
    is_title_fight: bool,
) -> str:
    """Generate a compelling narrative hook for the rivalry."""
    import random
    
    # Legendary rivalries get special treatment
    if intensity == "LEGENDARY":
        return random.choice(RIVALRY_HOOKS["legendary"])
    
    # Trilogy
    if fights == 2:
        if f1_wins == 1 and f2_wins == 1:
            return random.choice(RIVALRY_HOOKS["trilogy"])
    
    # Rematch
    if fights == 1:
        hooks = RIVALRY_HOOKS["rematch"]
        loser = fighter2_name if f1_wins > f2_wins else fighter1_name
        return random.choice(hooks).format(loser=loser)
    
    # Title fight
    if is_title_fight:
        return random.choice(RIVALRY_HOOKS["title"])
    
    # Type-specific
    if rivalry_type == "bad_blood":
        return random.choice(RIVALRY_HOOKS["bad_blood"])
    elif rivalry_type == "gym_war":
        return random.choice(RIVALRY_HOOKS["gym_war"])
    elif rivalry_type == "revenge":
        hooks = RIVALRY_HOOKS["revenge"]
        # Determine who needs revenge (fewer wins)
        loser = fighter2_name if f1_wins > f2_wins else fighter1_name
        return random.choice(hooks).format(loser=loser)
    
    # Default based on intensity
    if intensity in ["HEATED", "FIERCE"]:
        return "Bad blood boils over in this matchup."
    elif intensity == "NOTABLE":
        return "These two have history."
    else:
        return "A rivalry beginning to simmer."


# ============================================================================
# FORMATTING FUNCTIONS
# ============================================================================

def format_rivalry_preview(preview: RivalryPreview) -> str:
    """
    Format rivalry preview for display before a fight.
    
    Args:
        preview: RivalryPreview object
        
    Returns:
        Formatted string for display
    """
    if not preview.has_rivalry:
        if preview.narrative_hook:
            return f"📋 First meeting: {preview.narrative_hook}"
        return ""
    
    lines = []
    
    # Header with intensity
    emoji = INTENSITY_EMOJIS.get(preview.intensity, "")
    type_emoji = TYPE_EMOJIS.get(preview.rivalry_type, "")
    
    lines.append(f"═══ {emoji} RIVALRY ALERT {emoji} ═══")
    lines.append(f"{preview.fighter1_name} vs {preview.fighter2_name}")
    lines.append("")
    
    # Type and intensity
    type_desc = TYPE_DESCRIPTIONS.get(preview.rivalry_type, preview.rivalry_type)
    lines.append(f"{type_emoji} {type_desc}")
    lines.append(f"Intensity: {preview.intensity} ({preview.score}/100)")
    lines.append(f"Head-to-Head: {preview.head_to_head}")
    
    if preview.series_leader:
        lines.append(f"Series Leader: {preview.series_leader}")
    
    # Special labels
    labels = []
    if preview.is_trilogy:
        labels.append("🏆 TRILOGY FIGHT")
    elif preview.is_rematch:
        labels.append("🔄 REMATCH")
    
    if labels:
        lines.append(" | ".join(labels))
    
    # Narrative hook
    if preview.narrative_hook:
        lines.append("")
        lines.append(f'"{preview.narrative_hook}"')
    
    return "\n".join(lines)


def format_rivalry_preview_compact(preview: RivalryPreview) -> str:
    """Format rivalry preview in a single line."""
    if not preview.has_rivalry:
        return ""
    
    emoji = INTENSITY_EMOJIS.get(preview.intensity, "")
    
    parts = [emoji]
    
    if preview.is_trilogy:
        parts.append("TRILOGY")
    elif preview.is_rematch:
        parts.append("REMATCH")
    else:
        parts.append(preview.intensity)
    
    parts.append(f"({preview.head_to_head})")
    
    return " ".join(parts)


def format_rivalry_display(
    rivalry_data: Dict[str, Any],
    detailed: bool = False
) -> str:
    """
    Format a rivalry for display.
    
    Args:
        rivalry_data: Rivalry dict from Rivalry.to_dict()
        detailed: Whether to show full history
        
    Returns:
        Formatted string
    """
    score = rivalry_data.get("score", 0)
    fights = rivalry_data.get("fights", 0)
    f1_name = rivalry_data.get("fighter1_name", "Fighter 1")
    f2_name = rivalry_data.get("fighter2_name", "Fighter 2")
    f1_wins = rivalry_data.get("fighter1_wins", 0)
    f2_wins = rivalry_data.get("fighter2_wins", 0)
    draws = rivalry_data.get("draws", 0)
    rivalry_type = rivalry_data.get("rivalry_type", "competitive")
    
    # Determine intensity
    intensity = "BUDDING"
    for int_level, (min_s, max_s) in INTENSITY_THRESHOLDS.items():
        if min_s <= score <= max_s:
            intensity = int_level.name
            break
    if score >= 90:
        intensity = "LEGENDARY"
    
    emoji = INTENSITY_EMOJIS.get(intensity, "")
    type_emoji = TYPE_EMOJIS.get(rivalry_type, "")
    
    lines = []
    lines.append(f"{emoji} {f1_name} vs {f2_name}")
    lines.append(f"   {type_emoji} {rivalry_type.replace('_', ' ').title()}")
    lines.append(f"   Intensity: {intensity} ({score}/100)")
    lines.append(f"   Record: {f1_wins}-{f2_wins}-{draws} ({fights} fights)")
    
    if detailed:
        history = rivalry_data.get("history", [])
        if history:
            lines.append("   Recent Events:")
            for event in history[-5:]:
                desc = event.get("description", "")[:50]
                change = event.get("score_change", 0)
                lines.append(f"     • {desc} (+{change})")
    
    return "\n".join(lines)


# ============================================================================
# NEWS GENERATION
# ============================================================================

def generate_rivalry_news(
    fighter1_name: str,
    fighter2_name: str,
    old_score: int,
    new_score: int,
    rivalry_type: str,
    is_new_rivalry: bool,
    fight_method: str = "",
    is_title_fight: bool = False,
) -> List[RivalryNewsItem]:
    """
    Generate news items from rivalry changes.
    
    Args:
        fighter1_name: First fighter's name
        fighter2_name: Second fighter's name
        old_score: Previous rivalry score
        new_score: New rivalry score
        rivalry_type: Type of rivalry
        is_new_rivalry: Whether this is a new rivalry
        fight_method: How the fight ended
        is_title_fight: Whether it was a title fight
        
    Returns:
        List of news items
    """
    news = []
    score_change = new_score - old_score
    
    # Determine old and new intensity
    def get_intensity(score):
        for int_level, (min_s, max_s) in INTENSITY_THRESHOLDS.items():
            if min_s <= score <= max_s:
                return int_level.name
        return "LEGENDARY" if score >= 90 else "BUDDING"
    
    old_intensity = get_intensity(old_score) if not is_new_rivalry else None
    new_intensity = get_intensity(new_score)
    
    # New rivalry
    if is_new_rivalry:
        headlines = [
            f"Rivalry Born: {fighter1_name} and {fighter2_name}",
            f"Bad Blood? {fighter1_name} vs {fighter2_name} rivalry emerges",
            f"New Feud: {fighter1_name}-{fighter2_name} rivalry begins",
        ]
        import random
        news.append(RivalryNewsItem(
            headline=random.choice(headlines),
            category="rivalry_new",
            fighters=[fighter1_name, fighter2_name],
            intensity_change=new_score,
            is_major=new_score >= 30,
            description=f"A {rivalry_type.replace('_', ' ')} rivalry has formed.",
        ))
    
    # Intensity escalation
    elif old_intensity != new_intensity:
        intensity_headlines = {
            "NOTABLE": f"Rivalry Heating Up: {fighter1_name} vs {fighter2_name}",
            "HEATED": f"🔥 Rivalry Explodes: {fighter1_name}-{fighter2_name} feud intensifies",
            "FIERCE": f"💥 FIERCE RIVALRY: {fighter1_name} vs {fighter2_name} reaches new heights",
            "LEGENDARY": f"👑 LEGENDARY: {fighter1_name}-{fighter2_name} rivalry enters history",
        }
        
        if new_intensity in intensity_headlines:
            news.append(RivalryNewsItem(
                headline=intensity_headlines[new_intensity],
                category="rivalry_escalate",
                fighters=[fighter1_name, fighter2_name],
                intensity_change=score_change,
                is_major=True,
                description=INTENSITY_DESCRIPTIONS.get(new_intensity, ""),
            ))
    
    # Significant score change without intensity change
    elif score_change >= 15:
        news.append(RivalryNewsItem(
            headline=f"Rivalry Update: {fighter1_name} vs {fighter2_name} tension grows",
            category="rivalry_update",
            fighters=[fighter1_name, fighter2_name],
            intensity_change=score_change,
            is_major=False,
            description=f"Rivalry score increased by {score_change}.",
        ))
    
    return news


def format_rivalry_news(news_item: RivalryNewsItem) -> str:
    """Format a rivalry news item for display."""
    prefix = "🔥 " if news_item.is_major else ""
    return f"{prefix}{news_item.headline}"


# ============================================================================
# FIGHTER RIVALRY SUMMARY
# ============================================================================

def get_fighter_rivalries_summary(
    fighter_id: str,
    fighter_name: str,
    rivalries_data: List[Dict[str, Any]],
) -> FighterRivalrySummary:
    """
    Generate a summary of a fighter's rivalries.
    
    Args:
        fighter_id: Fighter's ID
        fighter_name: Fighter's name
        rivalries_data: List of rivalry dicts involving this fighter
        
    Returns:
        FighterRivalrySummary
    """
    total = len(rivalries_data)
    active = 0
    legendary = 0
    heated = 0
    biggest_rival = None
    biggest_score = 0
    rivalry_list = []
    
    for rivalry in rivalries_data:
        if rivalry.get("is_active", True):
            active += 1
        
        score = rivalry.get("score", 0)
        
        # Determine intensity
        if score >= 90:
            legendary += 1
        elif score >= 50:
            heated += 1
        
        # Track biggest rival
        if score > biggest_score:
            biggest_score = score
            # Find opponent name
            if rivalry.get("fighter1_id") == fighter_id:
                biggest_rival = rivalry.get("fighter2_name")
            else:
                biggest_rival = rivalry.get("fighter1_name")
        
        # Build rivalry list
        opponent = rivalry.get("fighter2_name") if rivalry.get("fighter1_id") == fighter_id else rivalry.get("fighter1_name")
        rtype = rivalry.get("rivalry_type", "competitive")
        rivalry_list.append((opponent, rtype, score))
    
    # Sort by score
    rivalry_list.sort(key=lambda x: x[2], reverse=True)
    
    return FighterRivalrySummary(
        fighter_name=fighter_name,
        fighter_id=fighter_id,
        total_rivalries=total,
        active_rivalries=active,
        biggest_rival=biggest_rival,
        biggest_rivalry_score=biggest_score,
        legendary_rivalries=legendary,
        heated_rivalries=heated,
        rivalry_list=rivalry_list[:5],  # Top 5
    )


def format_fighter_rivalries(summary: FighterRivalrySummary) -> str:
    """Format a fighter's rivalry summary for display."""
    lines = []
    
    lines.append(f"═══ {summary.fighter_name}'s Rivalries ═══")
    lines.append(f"Total: {summary.total_rivalries} | Active: {summary.active_rivalries}")
    
    if summary.legendary_rivalries > 0:
        lines.append(f"👑 Legendary Rivalries: {summary.legendary_rivalries}")
    if summary.heated_rivalries > 0:
        lines.append(f"🔥 Heated Rivalries: {summary.heated_rivalries}")
    
    if summary.biggest_rival:
        lines.append(f"\nBiggest Rival: {summary.biggest_rival} ({summary.biggest_rivalry_score}/100)")
    
    if summary.rivalry_list:
        lines.append("\nTop Rivalries:")
        for opponent, rtype, score in summary.rivalry_list:
            emoji = TYPE_EMOJIS.get(rtype, "")
            lines.append(f"  {emoji} vs {opponent}: {score}/100")
    
    return "\n".join(lines)


# ============================================================================
# CLI INTEGRATION HELPER
# ============================================================================

class RivalryDisplayHelper:
    """
    Helper class for CLI rivalry integration.
    
    Provides simplified methods for common rivalry display needs.
    """
    
    def __init__(self, rivalry_system_data: Optional[Dict[str, Any]] = None):
        """
        Initialize with optional rivalry system data.
        
        Args:
            rivalry_system_data: Dict from RivalrySystem.to_dict()
        """
        self._rivalries: Dict[str, Dict] = {}
        self._fighter_rivalries: Dict[str, List[str]] = {}
        
        if rivalry_system_data:
            self._load_data(rivalry_system_data)
    
    def _load_data(self, data: Dict[str, Any]) -> None:
        """Load rivalry data from system dict."""
        self._rivalries = data.get("rivalries", {})
        
        # Build fighter lookup
        for key, rivalry in self._rivalries.items():
            f1_id = rivalry.get("fighter1_id")
            f2_id = rivalry.get("fighter2_id")
            
            if f1_id:
                if f1_id not in self._fighter_rivalries:
                    self._fighter_rivalries[f1_id] = []
                self._fighter_rivalries[f1_id].append(key)
            
            if f2_id:
                if f2_id not in self._fighter_rivalries:
                    self._fighter_rivalries[f2_id] = []
                self._fighter_rivalries[f2_id].append(key)
    
    def get_rivalry(self, fighter1_id: str, fighter2_id: str) -> Optional[Dict]:
        """Get rivalry between two fighters."""
        key1 = f"{fighter1_id}_{fighter2_id}"
        key2 = f"{fighter2_id}_{fighter1_id}"
        
        return self._rivalries.get(key1) or self._rivalries.get(key2)
    
    def get_fight_preview(
        self,
        fighter1_id: str,
        fighter2_id: str,
        fighter1_name: str,
        fighter2_name: str,
        is_title_fight: bool = False,
    ) -> str:
        """
        Get formatted rivalry preview for a fight.
        
        Returns empty string if no significant rivalry context.
        """
        rivalry = self.get_rivalry(fighter1_id, fighter2_id)
        
        preview = get_fight_rivalry_preview(
            fighter1_id=fighter1_id,
            fighter2_id=fighter2_id,
            fighter1_name=fighter1_name,
            fighter2_name=fighter2_name,
            rivalry_data=rivalry,
            is_title_fight=is_title_fight,
        )
        
        if preview.has_rivalry or preview.narrative_hook:
            return format_rivalry_preview(preview)
        return ""
    
    def get_fight_preview_compact(
        self,
        fighter1_id: str,
        fighter2_id: str,
        fighter1_name: str,
        fighter2_name: str,
    ) -> str:
        """Get compact rivalry indicator for fight listings."""
        rivalry = self.get_rivalry(fighter1_id, fighter2_id)
        
        if not rivalry:
            return ""
        
        preview = get_fight_rivalry_preview(
            fighter1_id, fighter2_id, fighter1_name, fighter2_name, rivalry
        )
        
        return format_rivalry_preview_compact(preview)
    
    def get_fighter_rivalries(
        self,
        fighter_id: str,
        fighter_name: str,
    ) -> str:
        """Get formatted rivalry summary for a fighter."""
        rivalry_keys = self._fighter_rivalries.get(fighter_id, [])
        rivalries = [self._rivalries[k] for k in rivalry_keys if k in self._rivalries]
        
        if not rivalries:
            return f"{fighter_name} has no active rivalries."
        
        summary = get_fighter_rivalries_summary(fighter_id, fighter_name, rivalries)
        return format_fighter_rivalries(summary)
    
    def get_heated_rivalries(self) -> List[Tuple[str, str, int]]:
        """Get list of heated rivalries (fighter1, fighter2, score)."""
        heated = []
        
        for rivalry in self._rivalries.values():
            if rivalry.get("is_active", True) and rivalry.get("score", 0) >= 50:
                heated.append((
                    rivalry.get("fighter1_name", ""),
                    rivalry.get("fighter2_name", ""),
                    rivalry.get("score", 0)
                ))
        
        return sorted(heated, key=lambda x: x[2], reverse=True)
    
    def format_heated_rivalries_list(self) -> str:
        """Format list of all heated rivalries."""
        heated = self.get_heated_rivalries()
        
        if not heated:
            return "No heated rivalries currently."
        
        lines = ["═══ 🔥 HEATED RIVALRIES 🔥 ═══"]
        
        for f1, f2, score in heated[:10]:
            intensity = "LEGENDARY" if score >= 90 else "FIERCE" if score >= 70 else "HEATED"
            emoji = INTENSITY_EMOJIS.get(intensity, "🔥")
            lines.append(f"{emoji} {f1} vs {f2} ({score}/100)")
        
        if len(heated) > 10:
            lines.append(f"  ... and {len(heated) - 10} more")
        
        return "\n".join(lines)


# ============================================================================
# POST-FIGHT RIVALRY PROCESSING
# ============================================================================

def analyze_fight_for_rivalry(
    winner_name: str,
    loser_name: str,
    method: str,
    is_title_fight: bool,
    is_close: bool,
    existing_score: int = 0,
) -> Tuple[int, List[str]]:
    """
    Analyze a fight result for rivalry implications.
    
    Args:
        winner_name: Winner's name
        loser_name: Loser's name
        method: Fight ending method (KO, TKO, SUB, DEC, etc.)
        is_title_fight: Whether it was a title fight
        is_close: Whether the fight was competitive
        existing_score: Current rivalry score
        
    Returns:
        Tuple of (score_change, list of trigger descriptions)
    """
    score_change = 0
    triggers = []
    
    # Method-based triggers
    if method in ["KO", "TKO"]:
        score_change += 10
        triggers.append(f"Knockout loss fuels {loser_name}'s desire for revenge")
    elif method == "SUB":
        score_change += 8
        triggers.append(f"Submission loss stings {loser_name}'s ego")
    elif method == "SPLIT":
        score_change += 20
        triggers.append("Split decision leaves questions unanswered")
    elif method == "DEC" and is_close:
        score_change += 15
        triggers.append("Close decision could have gone either way")
    
    # Context triggers
    if is_title_fight:
        score_change += 15
        triggers.append("Championship implications raise the stakes")
    
    if is_close:
        score_change += 5
        triggers.append("Competitive fight shows they're evenly matched")
    
    return score_change, triggers


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "RivalryPreview",
    "RivalryNewsItem",
    "FighterRivalrySummary",
    
    # Constants
    "RivalryType",
    "RivalryIntensity",
    "INTENSITY_EMOJIS",
    "INTENSITY_DESCRIPTIONS",
    "TYPE_DESCRIPTIONS",
    "TYPE_EMOJIS",
    
    # Preview functions
    "get_fight_rivalry_preview",
    "format_rivalry_preview",
    "format_rivalry_preview_compact",
    
    # Display functions
    "format_rivalry_display",
    
    # News functions
    "generate_rivalry_news",
    "format_rivalry_news",
    
    # Fighter summary
    "get_fighter_rivalries_summary",
    "format_fighter_rivalries",
    
    # CLI helper
    "RivalryDisplayHelper",
    
    # Post-fight analysis
    "analyze_fight_for_rivalry",
]
