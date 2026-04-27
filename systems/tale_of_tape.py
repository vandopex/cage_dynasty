# systems/tale_of_tape.py
# Module: Tale of the Tape Display
# Lines: ~650
#
# Pre-fight comparison display showing two fighters side-by-side.
# Visual stat comparisons with advantage indicators.

"""
Cage Dynasty - Tale of the Tape Display

This module creates visual pre-fight comparisons:
- Side-by-side fighter stats
- Advantage indicators
- Record comparisons
- Style matchup analysis

CONCEPT:
    Before each fight, display a "Tale of the Tape" like real MMA broadcasts.
    Shows physical attributes, records, key stats, and fighting styles.
    Highlights advantages for each fighter.

USAGE:
    from systems.tale_of_tape import (
        generate_tale_of_tape,
        print_tale_of_tape,
        get_stat_comparison,
    )
    
    # Generate and print tale of tape
    tape = generate_tale_of_tape(fighter1_data, fighter2_data)
    print_tale_of_tape(tape)
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CONSTANTS
# ============================================================================

DISPLAY_WIDTH = 70
STAT_BAR_WIDTH = 10

# ANSI Colors
class Colors:
    """ANSI color codes for display."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GOLD = "\033[93m"
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{cls.RESET}"


# Box drawing characters
BOX_H = "─"
BOX_V = "│"
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_T = "┬"
BOX_B = "┴"
BOX_CROSS = "┼"
BOX_L = "├"
BOX_R = "┤"

# Stat categories for display
PHYSICAL_STATS = ["age", "height", "weight", "reach"]
STRIKING_STATS = ["boxing", "kicks", "clinch", "power", "accuracy"]
GRAPPLING_STATS = ["wrestling", "bjj", "takedown_defense", "top_control", "submissions"]
DEFENSE_STATS = ["chin", "cardio", "recovery", "striking_defense", "grappling_defense"]
MENTAL_STATS = ["heart", "fight_iq", "composure", "aggression"]

# Stat display names (prettier versions)
STAT_DISPLAY_NAMES = {
    "boxing": "Boxing",
    "kicks": "Kicks",
    "clinch": "Clinch",
    "power": "Power",
    "accuracy": "Accuracy",
    "wrestling": "Wrestling",
    "bjj": "BJJ",
    "takedown_defense": "TD Defense",
    "top_control": "Top Control",
    "submissions": "Submissions",
    "chin": "Chin",
    "cardio": "Cardio",
    "recovery": "Recovery",
    "striking_defense": "Str. Defense",
    "grappling_defense": "Grp. Defense",
    "heart": "Heart",
    "fight_iq": "Fight IQ",
    "composure": "Composure",
    "aggression": "Aggression",
    "strength": "Strength",
    "speed": "Speed",
    "age": "Age",
    "height": "Height",
    "weight": "Weight",
    "reach": "Reach",
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FighterTapeData:
    """Fighter data for tale of tape display."""
    name: str
    nickname: str = ""
    age: int = 0
    height: int = 0  # in inches
    weight: int = 0  # in lbs
    reach: int = 0   # in inches
    
    # Record
    wins: int = 0
    losses: int = 0
    draws: int = 0
    ko_wins: int = 0
    sub_wins: int = 0
    dec_wins: int = 0
    
    # Current status
    is_champion: bool = False
    ranking: int = 0  # 0 = unranked, 1-15 = ranked
    win_streak: int = 0
    lose_streak: int = 0
    
    # Stats (all 1-100)
    stats: Dict[str, int] = field(default_factory=dict)
    
    # Style info
    fighting_style: str = ""
    camp_name: str = ""
    nationality: str = ""
    
    # Traits
    traits: List[str] = field(default_factory=list)
    
    def get_record_string(self) -> str:
        """Get formatted record string."""
        if self.draws > 0:
            return f"{self.wins}-{self.losses}-{self.draws}"
        return f"{self.wins}-{self.losses}"
    
    def get_height_string(self) -> str:
        """Get formatted height (e.g., 5'11\")."""
        feet = self.height // 12
        inches = self.height % 12
        return f"{feet}'{inches}\""
    
    def get_finish_rate(self) -> float:
        """Get finish rate as percentage."""
        if self.wins == 0:
            return 0.0
        return ((self.ko_wins + self.sub_wins) / self.wins) * 100


@dataclass
class StatComparison:
    """Comparison result for a single stat."""
    stat_name: str
    display_name: str
    value1: int
    value2: int
    advantage: int  # -1 = fighter1, 0 = even, 1 = fighter2
    difference: int


@dataclass
class TaleOfTape:
    """Complete tale of tape data."""
    fighter1: FighterTapeData
    fighter2: FighterTapeData
    is_title_fight: bool = False
    is_main_event: bool = False
    weight_class: str = ""
    
    # Calculated comparisons
    stat_comparisons: List[StatComparison] = field(default_factory=list)
    
    # Overall analysis
    striking_advantage: int = 0  # -1, 0, 1
    grappling_advantage: int = 0
    physical_advantage: int = 0
    experience_advantage: int = 0


# ============================================================================
# COMPARISON FUNCTIONS
# ============================================================================

def compare_stat(
    stat_name: str,
    value1: int,
    value2: int,
    threshold: int = 5,
) -> StatComparison:
    """
    Compare a single stat between two fighters.
    
    Args:
        stat_name: Name of the stat
        value1: Fighter 1's value
        value2: Fighter 2's value
        threshold: Minimum difference for advantage
        
    Returns:
        StatComparison object
    """
    diff = value1 - value2
    
    if abs(diff) < threshold:
        advantage = 0
    elif diff > 0:
        advantage = -1  # Fighter 1 advantage
    else:
        advantage = 1   # Fighter 2 advantage
    
    return StatComparison(
        stat_name=stat_name,
        display_name=STAT_DISPLAY_NAMES.get(stat_name, stat_name.title()),
        value1=value1,
        value2=value2,
        advantage=advantage,
        difference=abs(diff),
    )


def get_stat_comparison(
    fighter1: FighterTapeData,
    fighter2: FighterTapeData,
    stat_names: List[str],
) -> List[StatComparison]:
    """
    Compare multiple stats between fighters.
    
    Args:
        fighter1: First fighter's data
        fighter2: Second fighter's data
        stat_names: List of stat names to compare
        
    Returns:
        List of StatComparison objects
    """
    comparisons = []
    
    for stat in stat_names:
        v1 = fighter1.stats.get(stat, 50)
        v2 = fighter2.stats.get(stat, 50)
        comparisons.append(compare_stat(stat, v1, v2))
    
    return comparisons


def calculate_category_advantage(comparisons: List[StatComparison]) -> int:
    """
    Calculate overall advantage for a category of stats.
    
    Returns:
        -1 if fighter1 has advantage, 0 if even, 1 if fighter2 has advantage
    """
    total = sum(c.value1 - c.value2 for c in comparisons)
    
    if abs(total) < len(comparisons) * 3:  # Need significant total difference
        return 0
    return -1 if total > 0 else 1


def analyze_matchup(
    fighter1: FighterTapeData,
    fighter2: FighterTapeData,
) -> Dict[str, int]:
    """
    Analyze overall matchup advantages.
    
    Returns:
        Dict with advantage scores for each category
    """
    # Striking comparison
    striking_stats = ["boxing", "kicks", "power", "accuracy"]
    striking_comps = get_stat_comparison(fighter1, fighter2, striking_stats)
    striking_adv = calculate_category_advantage(striking_comps)
    
    # Grappling comparison
    grappling_stats = ["wrestling", "bjj", "takedown_defense", "submissions"]
    grappling_comps = get_stat_comparison(fighter1, fighter2, grappling_stats)
    grappling_adv = calculate_category_advantage(grappling_comps)
    
    # Physical comparison
    physical_comps = [
        compare_stat("reach", fighter1.reach, fighter2.reach, threshold=2),
        compare_stat("height", fighter1.height, fighter2.height, threshold=2),
    ]
    physical_comps.extend(get_stat_comparison(fighter1, fighter2, ["strength", "speed", "cardio"]))
    physical_adv = calculate_category_advantage(physical_comps)
    
    # Experience comparison
    exp1 = fighter1.wins + fighter1.losses
    exp2 = fighter2.wins + fighter2.losses
    if abs(exp1 - exp2) < 5:
        exp_adv = 0
    else:
        exp_adv = -1 if exp1 > exp2 else 1
    
    return {
        "striking": striking_adv,
        "grappling": grappling_adv,
        "physical": physical_adv,
        "experience": exp_adv,
    }


# ============================================================================
# TALE OF TAPE GENERATION
# ============================================================================

def generate_tale_of_tape(
    fighter1: FighterTapeData,
    fighter2: FighterTapeData,
    is_title_fight: bool = False,
    is_main_event: bool = False,
    weight_class: str = "",
) -> TaleOfTape:
    """
    Generate complete tale of tape data.
    
    Args:
        fighter1: Red corner fighter data
        fighter2: Blue corner fighter data
        is_title_fight: Whether this is a title fight
        is_main_event: Whether this is the main event
        weight_class: Weight class name
        
    Returns:
        TaleOfTape object with all comparison data
    """
    # Get all stat comparisons
    all_stats = (
        STRIKING_STATS + GRAPPLING_STATS + 
        DEFENSE_STATS[:3] +  # chin, cardio, recovery
        MENTAL_STATS[:2]  # heart, fight_iq
    )
    stat_comparisons = get_stat_comparison(fighter1, fighter2, all_stats)
    
    # Analyze matchup
    advantages = analyze_matchup(fighter1, fighter2)
    
    return TaleOfTape(
        fighter1=fighter1,
        fighter2=fighter2,
        is_title_fight=is_title_fight,
        is_main_event=is_main_event,
        weight_class=weight_class,
        stat_comparisons=stat_comparisons,
        striking_advantage=advantages["striking"],
        grappling_advantage=advantages["grappling"],
        physical_advantage=advantages["physical"],
        experience_advantage=advantages["experience"],
    )


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def _create_stat_bar(value: int, width: int = STAT_BAR_WIDTH) -> str:
    """Create a visual bar for a stat value (1-100)."""
    filled = int((value / 100) * width)
    empty = width - filled
    return "█" * filled + "░" * empty


def _create_comparison_bar(value1: int, value2: int) -> str:
    """Create side-by-side comparison bars."""
    bar1 = _create_stat_bar(value1, 8)
    bar2 = _create_stat_bar(value2, 8)
    return f"{bar1}  {bar2}"


def _format_centered(text: str, width: int) -> str:
    """Center text within width."""
    return text.center(width)


def _format_vs_row(left: str, center: str, right: str, width: int = DISPLAY_WIDTH) -> str:
    """Format a row with left, center, and right aligned text."""
    side_width = (width - len(center) - 4) // 2
    left_part = left.rjust(side_width)
    right_part = right.ljust(side_width)
    return f"{left_part}  {center}  {right_part}"


def _advantage_indicator(advantage: int) -> str:
    """Get advantage indicator arrow."""
    if advantage == -1:
        return Colors.colorize("◄", Colors.GREEN)
    elif advantage == 1:
        return Colors.colorize("►", Colors.GREEN)
    return " "


def _format_stat_row(comp: StatComparison, show_bars: bool = True) -> str:
    """Format a single stat comparison row."""
    name = comp.display_name.center(14)
    
    # Color the values based on advantage
    if comp.advantage == -1:
        v1 = Colors.colorize(str(comp.value1), Colors.GREEN)
        v2 = str(comp.value2)
    elif comp.advantage == 1:
        v1 = str(comp.value1)
        v2 = Colors.colorize(str(comp.value2), Colors.GREEN)
    else:
        v1 = str(comp.value1)
        v2 = str(comp.value2)
    
    adv1 = _advantage_indicator(comp.advantage) if comp.advantage == -1 else " "
    adv2 = _advantage_indicator(comp.advantage) if comp.advantage == 1 else " "
    
    if show_bars:
        bar1 = _create_stat_bar(comp.value1, 6)
        bar2 = _create_stat_bar(comp.value2, 6)
        return f"  {adv1} {v1:>3} {bar1} {name} {bar2} {v2:<3} {adv2}"
    else:
        return f"  {adv1} {v1:>3}        {name}        {v2:<3} {adv2}"


def format_tale_of_tape(tape: TaleOfTape, use_colors: bool = True) -> List[str]:
    """
    Format tale of tape as list of strings for display.
    
    Args:
        tape: TaleOfTape object
        use_colors: Whether to use ANSI colors
        
    Returns:
        List of formatted strings
    """
    lines = []
    f1, f2 = tape.fighter1, tape.fighter2
    w = DISPLAY_WIDTH
    
    # Header
    lines.append(BOX_TL + BOX_H * (w - 2) + BOX_TR)
    
    # Fight type
    if tape.is_title_fight:
        title_text = f"★ {tape.weight_class.upper()} CHAMPIONSHIP ★"
        lines.append(BOX_V + Colors.colorize(title_text.center(w - 2), Colors.GOLD) + BOX_V)
    elif tape.is_main_event:
        lines.append(BOX_V + f"MAIN EVENT - {tape.weight_class}".center(w - 2) + BOX_V)
    else:
        lines.append(BOX_V + f"{tape.weight_class}".center(w - 2) + BOX_V)
    
    lines.append(BOX_V + "TALE OF THE TAPE".center(w - 2) + BOX_V)
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Fighter names
    name1 = f1.name.upper()
    name2 = f2.name.upper()
    if f1.is_champion:
        name1 = f"★ {name1} (C)"
    if f2.is_champion:
        name2 = f"(C) {name2} ★"
    
    if f1.ranking > 0 and not f1.is_champion:
        name1 = f"#{f1.ranking} {name1}"
    if f2.ranking > 0 and not f2.is_champion:
        name2 = f"{name2} #{f2.ranking}"
    
    lines.append(BOX_V + _format_vs_row(name1, "VS", name2, w - 2) + BOX_V)
    
    # Nicknames
    if f1.nickname or f2.nickname:
        nick1 = f'"{f1.nickname}"' if f1.nickname else ""
        nick2 = f'"{f2.nickname}"' if f2.nickname else ""
        lines.append(BOX_V + _format_vs_row(nick1, "", nick2, w - 2) + BOX_V)
    
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Records
    rec1 = f1.get_record_string()
    rec2 = f2.get_record_string()
    lines.append(BOX_V + _format_vs_row(rec1, "RECORD", rec2, w - 2) + BOX_V)
    
    # Finish rates
    fin1 = f"{f1.get_finish_rate():.0f}%"
    fin2 = f"{f2.get_finish_rate():.0f}%"
    lines.append(BOX_V + _format_vs_row(fin1, "FINISH RATE", fin2, w - 2) + BOX_V)
    
    # Win/lose streaks
    if f1.win_streak > 0 or f2.win_streak > 0:
        streak1 = f"{f1.win_streak}W" if f1.win_streak > 0 else "-"
        streak2 = f"{f2.win_streak}W" if f2.win_streak > 0 else "-"
        if f1.lose_streak > 0:
            streak1 = f"{f1.lose_streak}L"
        if f2.lose_streak > 0:
            streak2 = f"{f2.lose_streak}L"
        lines.append(BOX_V + _format_vs_row(streak1, "STREAK", streak2, w - 2) + BOX_V)
    
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Physical attributes
    lines.append(BOX_V + "PHYSICAL".center(w - 2) + BOX_V)
    
    age1, age2 = str(f1.age), str(f2.age)
    lines.append(BOX_V + _format_vs_row(age1, "AGE", age2, w - 2) + BOX_V)
    
    ht1, ht2 = f1.get_height_string(), f2.get_height_string()
    lines.append(BOX_V + _format_vs_row(ht1, "HEIGHT", ht2, w - 2) + BOX_V)
    
    wt1, wt2 = f"{f1.weight} lbs", f"{f2.weight} lbs"
    lines.append(BOX_V + _format_vs_row(wt1, "WEIGHT", wt2, w - 2) + BOX_V)
    
    reach1, reach2 = f'{f1.reach}"', f'{f2.reach}"'
    lines.append(BOX_V + _format_vs_row(reach1, "REACH", reach2, w - 2) + BOX_V)
    
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Striking stats
    lines.append(BOX_V + "STRIKING".center(w - 2) + BOX_V)
    for stat in STRIKING_STATS:
        comp = compare_stat(stat, f1.stats.get(stat, 50), f2.stats.get(stat, 50))
        lines.append(BOX_V + _format_stat_row(comp) + " " * (w - 48) + BOX_V)
    
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Grappling stats
    lines.append(BOX_V + "GRAPPLING".center(w - 2) + BOX_V)
    for stat in GRAPPLING_STATS:
        comp = compare_stat(stat, f1.stats.get(stat, 50), f2.stats.get(stat, 50))
        lines.append(BOX_V + _format_stat_row(comp) + " " * (w - 48) + BOX_V)
    
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Defense/Conditioning
    lines.append(BOX_V + "CONDITIONING".center(w - 2) + BOX_V)
    for stat in ["chin", "cardio", "recovery"]:
        comp = compare_stat(stat, f1.stats.get(stat, 50), f2.stats.get(stat, 50))
        lines.append(BOX_V + _format_stat_row(comp) + " " * (w - 48) + BOX_V)
    
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Styles and camps
    lines.append(BOX_V + "STYLE & CAMP".center(w - 2) + BOX_V)
    style1 = f1.fighting_style or "Mixed"
    style2 = f2.fighting_style or "Mixed"
    lines.append(BOX_V + _format_vs_row(style1, "STYLE", style2, w - 2) + BOX_V)
    
    camp1 = f1.camp_name or "Independent"
    camp2 = f2.camp_name or "Independent"
    lines.append(BOX_V + _format_vs_row(camp1, "CAMP", camp2, w - 2) + BOX_V)
    
    # Traits
    if f1.traits or f2.traits:
        lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
        lines.append(BOX_V + "TRAITS".center(w - 2) + BOX_V)
        traits1 = ", ".join(f1.traits[:2]) if f1.traits else "-"
        traits2 = ", ".join(f2.traits[:2]) if f2.traits else "-"
        lines.append(BOX_V + _format_vs_row(traits1, "", traits2, w - 2) + BOX_V)
    
    lines.append(BOX_L + BOX_H * (w - 2) + BOX_R)
    
    # Matchup analysis
    lines.append(BOX_V + "MATCHUP ANALYSIS".center(w - 2) + BOX_V)
    
    def advantage_text(adv: int, cat: str) -> str:
        if adv == -1:
            return f"◄ {f1.name} has the {cat} advantage"
        elif adv == 1:
            return f"{f2.name} has the {cat} advantage ►"
        return f"{cat.title()} is even"
    
    if tape.striking_advantage != 0:
        text = advantage_text(tape.striking_advantage, "striking")
        lines.append(BOX_V + text.center(w - 2) + BOX_V)
    
    if tape.grappling_advantage != 0:
        text = advantage_text(tape.grappling_advantage, "grappling")
        lines.append(BOX_V + text.center(w - 2) + BOX_V)
    
    if tape.physical_advantage != 0:
        text = advantage_text(tape.physical_advantage, "physical")
        lines.append(BOX_V + text.center(w - 2) + BOX_V)
    
    if tape.experience_advantage != 0:
        text = advantage_text(tape.experience_advantage, "experience")
        lines.append(BOX_V + text.center(w - 2) + BOX_V)
    
    if (tape.striking_advantage == 0 and tape.grappling_advantage == 0 and 
        tape.physical_advantage == 0 and tape.experience_advantage == 0):
        lines.append(BOX_V + "This is an evenly matched fight!".center(w - 2) + BOX_V)
    
    # Footer
    lines.append(BOX_BL + BOX_H * (w - 2) + BOX_BR)
    
    return lines


def print_tale_of_tape(tape: TaleOfTape, use_colors: bool = True) -> None:
    """Print tale of tape to console."""
    lines = format_tale_of_tape(tape, use_colors)
    for line in lines:
        print(line)


def format_tale_of_tape_compact(tape: TaleOfTape) -> List[str]:
    """
    Format a compact version of tale of tape.
    
    Returns shorter output for quick display.
    """
    lines = []
    f1, f2 = tape.fighter1, tape.fighter2
    
    # Header
    lines.append("=" * 50)
    lines.append(f"{f1.name} vs {f2.name}".center(50))
    lines.append(f"{f1.get_record_string()}  vs  {f2.get_record_string()}".center(50))
    lines.append("=" * 50)
    
    # Key stats only
    key_stats = ["boxing", "wrestling", "cardio", "chin"]
    for stat in key_stats:
        v1 = f1.stats.get(stat, 50)
        v2 = f2.stats.get(stat, 50)
        name = STAT_DISPLAY_NAMES.get(stat, stat).center(12)
        lines.append(f"  {v1:3d}  {name}  {v2:3d}")
    
    lines.append("=" * 50)
    
    return lines


def print_tale_of_tape_compact(tape: TaleOfTape) -> None:
    """Print compact tale of tape."""
    lines = format_tale_of_tape_compact(tape)
    for line in lines:
        print(line)


# ============================================================================
# QUICK COMPARISON FUNCTIONS
# ============================================================================

def get_quick_comparison(
    fighter1: FighterTapeData,
    fighter2: FighterTapeData,
) -> Dict[str, Any]:
    """
    Get quick comparison summary as dictionary.
    
    Returns dict with key matchup info for programmatic use.
    """
    advantages = analyze_matchup(fighter1, fighter2)
    
    # Calculate overall favorite
    adv_sum = sum(advantages.values())
    if adv_sum < -1:
        favorite = fighter1.name
        confidence = "strong"
    elif adv_sum == -1:
        favorite = fighter1.name
        confidence = "slight"
    elif adv_sum == 0:
        favorite = "Even"
        confidence = "pick'em"
    elif adv_sum == 1:
        favorite = fighter2.name
        confidence = "slight"
    else:
        favorite = fighter2.name
        confidence = "strong"
    
    return {
        "fighter1": fighter1.name,
        "fighter2": fighter2.name,
        "striking_advantage": advantages["striking"],
        "grappling_advantage": advantages["grappling"],
        "physical_advantage": advantages["physical"],
        "experience_advantage": advantages["experience"],
        "favorite": favorite,
        "confidence": confidence,
    }


def get_prediction_text(comparison: Dict[str, Any]) -> str:
    """Generate prediction text from comparison."""
    fav = comparison["favorite"]
    conf = comparison["confidence"]
    
    if fav == "Even":
        return "This looks like an even fight - could go either way."
    elif conf == "strong":
        return f"{fav} has significant advantages and should be favored."
    else:
        return f"{fav} has a slight edge but this should be competitive."


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_fighter_tape_data(
    name: str,
    stats: Dict[str, int],
    record: Tuple[int, int, int] = (0, 0, 0),  # wins, losses, draws
    finishes: Tuple[int, int] = (0, 0),  # ko_wins, sub_wins
    physical: Dict[str, int] = None,
    **kwargs
) -> FighterTapeData:
    """
    Helper to create FighterTapeData from common formats.
    
    Args:
        name: Fighter name
        stats: Dict of stat_name -> value
        record: Tuple of (wins, losses, draws)
        finishes: Tuple of (ko_wins, sub_wins)
        physical: Dict with age, height, weight, reach
        **kwargs: Additional FighterTapeData fields
        
    Returns:
        FighterTapeData object
    """
    wins, losses, draws = record
    ko_wins, sub_wins = finishes
    dec_wins = wins - ko_wins - sub_wins
    
    physical = physical or {}
    
    return FighterTapeData(
        name=name,
        wins=wins,
        losses=losses,
        draws=draws,
        ko_wins=ko_wins,
        sub_wins=sub_wins,
        dec_wins=dec_wins,
        age=physical.get("age", 28),
        height=physical.get("height", 70),
        weight=physical.get("weight", 170),
        reach=physical.get("reach", 72),
        stats=stats,
        **kwargs
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Data classes
    "FighterTapeData",
    "StatComparison",
    "TaleOfTape",
    
    # Constants
    "STAT_DISPLAY_NAMES",
    "STRIKING_STATS",
    "GRAPPLING_STATS",
    "DEFENSE_STATS",
    "MENTAL_STATS",
    
    # Comparison functions
    "compare_stat",
    "get_stat_comparison",
    "calculate_category_advantage",
    "analyze_matchup",
    
    # Tale of tape generation
    "generate_tale_of_tape",
    
    # Display functions
    "format_tale_of_tape",
    "print_tale_of_tape",
    "format_tale_of_tape_compact",
    "print_tale_of_tape_compact",
    
    # Quick comparison
    "get_quick_comparison",
    "get_prediction_text",
    
    # Helpers
    "create_fighter_tape_data",
]
