# interface/archives.py
# Archives and history display for Cage Dynasty CLI
# Lines: 486

"""
Archives and history display module.

Handles display of:
- GOAT rankings
- Record books (overall and by division)
- Champions history
- Fight details and replay
- Past events
"""

from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass

from interface.display import (
    Colors,
    colored,
    format_record,
    format_record_colored,
    clear_screen,
    print_header,
    print_divider,
    print_box,
    print_menu,
    get_input,
    get_choice,
    pause,
    TERMINAL_WIDTH,
)
from interface.cli_data import (
    FighterFullData,
    FightResult,
    CompletedEvent,
)


# ============================================================================
# GOAT RANKINGS
# ============================================================================

def calculate_goat_score(fighter: Any) -> int:
    """Calculate GOAT score for a fighter.
    
    Formula: WinsÃ—10 - LossesÃ—5 + DrawsÃ—2 + FinishesÃ—5 + Champion bonus
    
    Args:
        fighter: Fighter object with wins, losses, ko_wins, sub_wins, is_champion
        
    Returns:
        GOAT score (minimum 0)
    """
    score = getattr(fighter, 'wins', 0) * 10
    score -= getattr(fighter, 'losses', 0) * 5
    score += getattr(fighter, 'draws', 0) * 2
    score += getattr(fighter, 'ko_wins', 0) * 5
    score += getattr(fighter, 'sub_wins', 0) * 5
    
    if getattr(fighter, 'is_champion', False):
        score += 50
    
    # Title defenses bonus
    score += getattr(fighter, 'title_defenses', 0) * 10
    
    return max(0, score)


def display_goat_rankings(
    fighters: List[Any],
    title: str = "G.O.A.T. RANKINGS",
    max_display: int = 20
) -> None:
    """Display GOAT rankings screen.
    
    Args:
        fighters: List of fighter objects
        title: Screen title
        max_display: Maximum fighters to display
    """
    clear_screen()
    print_header(title)
    
    if not fighters:
        print("  No fighters to rank.")
        pause()
        return
    
    # Filter to fighters with at least one fight
    active_fighters = [f for f in fighters if getattr(f, 'wins', 0) + getattr(f, 'losses', 0) > 0]
    
    if not active_fighters:
        print("  No fighters with recorded fights yet.")
        pause()
        return
    
    # Calculate and sort by GOAT score
    scored = [(f, calculate_goat_score(f)) for f in active_fighters]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    print("  The greatest fighters in DFC history:")
    print()
    
    medals = {1: colored("[1st]", Colors.GOLD), 2: colored("[2nd]", Colors.WHITE), 3: colored("[3rd]", Colors.ORANGE)}
    
    for rank, (fighter, score) in enumerate(scored[:max_display], 1):
        medal = medals.get(rank, f" #{rank:2}")
        champ_tag = colored(" [C]", Colors.GOLD) if getattr(fighter, 'is_champion', False) else ""
        
        wins = getattr(fighter, 'wins', 0)
        losses = getattr(fighter, 'losses', 0)
        name = getattr(fighter, 'name', 'Unknown')
        
        print(f"  {medal} {name}{champ_tag}")
        print(f"        {format_record_colored(wins, losses)} | GOAT Score: {score}")
        print()
    
    pause()


# ============================================================================
# RECORD BOOK
# ============================================================================

def display_record_book(fighters: List[Any], max_per_category: int = 5) -> None:
    """Display overall record book.
    
    Args:
        fighters: List of fighter objects
        max_per_category: Number of fighters to show per category
    """
    clear_screen()
    print_header("RECORD BOOK")
    
    if not fighters:
        print("  No fighters.")
        pause()
        return
    
    # Define record categories
    categories = [
        ("Most Wins", lambda f: getattr(f, 'wins', 0), lambda f: f"{getattr(f, 'wins', 0)} wins"),
        ("Most KO Wins", lambda f: getattr(f, 'ko_wins', 0), lambda f: f"{getattr(f, 'ko_wins', 0)} KOs"),
        ("Most Submissions", lambda f: getattr(f, 'sub_wins', 0), lambda f: f"{getattr(f, 'sub_wins', 0)} subs"),
        ("Longest Win Streak", lambda f: getattr(f, 'win_streak', 0), lambda f: f"{getattr(f, 'win_streak', 0)} straight"),
        ("Most Title Defenses", lambda f: getattr(f, 'title_defenses', 0), lambda f: f"{getattr(f, 'title_defenses', 0)} defenses"),
    ]
    
    for cat_name, sort_key, display_fn in categories:
        top = sorted(fighters, key=sort_key, reverse=True)[:max_per_category]
        
        # Only show category if there are relevant records
        if sort_key(top[0]) == 0:
            continue
        
        print(f"  {colored(cat_name, Colors.BOLD)}:")
        print()
        
        for rank, fighter in enumerate(top, 1):
            name = getattr(fighter, 'name', 'Unknown')[:24]
            value = display_fn(fighter)
            print(f"    {rank}. {name:<24} {value:>12}")
        print()
    
    pause()


def display_record_book_by_division(
    fighters: List[Any],
    divisions: List[str],
    on_select: Optional[Callable[[str], None]] = None
) -> None:
    """Display division selection for record book.
    
    Args:
        fighters: List of fighter objects
        divisions: List of division names
        on_select: Callback when a division is selected
    """
    clear_screen()
    print_header("RECORD BOOK BY DIVISION")
    
    for i, div in enumerate(divisions, 1):
        count = sum(1 for f in fighters if getattr(f, 'weight_class', '') == div)
        print(f"  [{i}] {div} ({count} fighters)")
    
    print()
    print(f"  [0] Back")
    print()
    
    choice = get_input("Select: ")
    
    try:
        index = int(choice)
        if index == 0:
            return
        if 1 <= index <= len(divisions) and on_select:
            on_select(divisions[index - 1])
    except ValueError:
        pass


def display_division_records(fighters: List[Any], division: str) -> None:
    """Display records for a specific division.
    
    Args:
        fighters: List of fighter objects
        division: Division name to filter by
    """
    clear_screen()
    print_header(f"{division.upper()} RECORDS")
    
    div_fighters = [f for f in fighters if getattr(f, 'weight_class', '') == division]
    
    if not div_fighters:
        print(f"  No fighters in {division}.")
        pause()
        return
    
    categories = [
        ("Most Wins", lambda f: getattr(f, 'wins', 0), lambda f: f"{getattr(f, 'wins', 0)} wins"),
        ("Most KOs", lambda f: getattr(f, 'ko_wins', 0), lambda f: f"{getattr(f, 'ko_wins', 0)} KOs"),
        ("Most Subs", lambda f: getattr(f, 'sub_wins', 0), lambda f: f"{getattr(f, 'sub_wins', 0)} subs"),
    ]
    
    for cat_name, sort_key, display_fn in categories:
        top = sorted(div_fighters, key=sort_key, reverse=True)[:3]
        
        if sort_key(top[0]) == 0:
            continue
        
        print(f"  {colored(cat_name, Colors.BOLD)}:")
        for rank, fighter in enumerate(top, 1):
            name = getattr(fighter, 'name', 'Unknown')[:20]
            value = display_fn(fighter)
            print(f"    {rank}. {name:<20} {value}")
        print()
    
    pause()


# ============================================================================
# CHAMPIONS HISTORY
# ============================================================================

def display_champions_history(
    divisions: Dict[str, Any],
    fighters: Dict[str, Any]
) -> None:
    """Display current champions across all divisions.
    
    Args:
        divisions: Dictionary of division states
        fighters: Dictionary of fighter objects
    """
    clear_screen()
    print_header("CHAMPIONS HISTORY")
    
    print("  CURRENT CHAMPIONS:")
    print()
    
    for weight_class, div_state in divisions.items():
        champ_id = getattr(div_state, 'champion_id', None)
        
        if champ_id and champ_id in fighters:
            champ = fighters[champ_id]
            name = getattr(champ, 'name', 'Unknown')
            wins = getattr(champ, 'wins', 0)
            losses = getattr(champ, 'losses', 0)
            defenses = getattr(champ, 'title_defenses', 0)
            
            print(f"  {colored(weight_class, Colors.GOLD)}")
            print(f"    {name} ({format_record_colored(wins, losses)})")
            if defenses > 0:
                print(f"    {defenses} successful defense{'s' if defenses != 1 else ''}")
            print()
        else:
            print(f"  {colored(weight_class, Colors.DIM)}")
            print(f"    {colored('VACANT', Colors.ORANGE)}")
            print()
    
    pause()


# ============================================================================
# FIGHT DETAILS AND REPLAY
# ============================================================================

def display_fight_details(fight: FightResult) -> None:
    """Display detailed information about a fight.
    
    Args:
        fight: FightResult object
    """
    while True:
        clear_screen()
        print_header("FIGHT DETAILS")
        
        # Basic info
        print(f"  {fight.event_name} - Week {fight.week}")
        print()
        print(f"  {colored(fight.fighter1_name, Colors.CYAN)} vs {colored(fight.fighter2_name, Colors.MAGENTA)}")
        print()
        
        # Result
        if fight.method == "DRAW":
            print(f"  Result: {colored('DRAW', Colors.NEUTRAL)}")
        else:
            print(f"  Winner: {colored(fight.winner_name, Colors.WIN)}")
            method_str = fight.method
            if fight.is_finish:
                method_str = f"{fight.method} (R{fight.round_finished}, {fight.time_finished})"
            print(f"  Method: {method_str}")
        
        if fight.is_title_fight:
            print(f"  {colored('[TITLE FIGHT]', Colors.GOLD)}")
        
        print()
        
        # Summary
        if fight.fight_summary:
            print(f"  {fight.fight_summary}")
            print()
        
        # Options
        has_round_data = fight.round_by_round or fight.full_narrative
        
        options = []
        if has_round_data:
            options.append(("1", "Watch Full Fight"))
        if fight.key_moments:
            options.append(("2", "Key Moments"))
        options.append(("3", "Fight Stats"))
        if fight.judge_scores:
            options.append(("4", "Scorecards"))
        options.append(("0", "Back"))
        
        print_menu(options)
        
        valid_choices = [o[0] for o in options]
        choice = get_input("> ")
        
        if choice == "0":
            return
        elif choice == "1" and has_round_data:
            replay_fight_round_by_round(fight)
        elif choice == "2" and fight.key_moments:
            display_key_moments(fight)
        elif choice == "3":
            display_fight_stats(fight)
        elif choice == "4" and fight.judge_scores:
            display_scorecards(fight)


def replay_fight_round_by_round(fight: FightResult) -> None:
    """Replay fight with round-by-round commentary.
    
    Args:
        fight: FightResult object with round_by_round data
    """
    total_rounds = fight.round_finished if fight.method not in ("DEC", "UD", "SD", "MD") else fight.rounds_scheduled
    
    for round_num in range(1, total_rounds + 1):
        clear_screen()
        
        # Round header
        print()
        print(colored("=" * 70, Colors.CYAN))
        print(colored(f"                         ROUND {round_num}", Colors.BOLD))
        print(colored("=" * 70, Colors.CYAN))
        print()
        
        # Get round commentary
        round_text = ""
        if fight.round_by_round and len(fight.round_by_round) >= round_num:
            round_text = fight.round_by_round[round_num - 1]
        elif fight.full_narrative and round_num == 1:
            round_text = fight.full_narrative
        
        if round_text:
            lines = round_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Color code actions
                if any(x in line.upper() for x in ['KO', 'KNOCKOUT', 'DROPPED', 'HURT', 'ROCKED']):
                    print(f"  {colored(line, Colors.RED)}")
                elif any(x in line.upper() for x in ['TAKEDOWN', 'GROUND', 'MOUNT', 'CONTROL']):
                    print(f"  {colored(line, Colors.CYAN)}")
                elif any(x in line.upper() for x in ['SUBMISSION', 'CHOKE', 'ARMBAR', 'LOCK']):
                    print(f"  {colored(line, Colors.MAGENTA)}")
                elif any(x in line.upper() for x in ['LANDS', 'CONNECTS', 'STRIKES']):
                    print(f"  {colored(line, Colors.YELLOW)}")
                else:
                    print(f"  {line}")
            print()
        else:
            print(f"  The fighters engage in round {round_num}...")
            print()
        
        # Round summary
        if fight.round_summaries and len(fight.round_summaries) >= round_num:
            print(colored("  Round Summary:", Colors.BOLD))
            print(f"  {fight.round_summaries[round_num - 1]}")
            print()
        
        # Check for finish
        if round_num == fight.round_finished and fight.is_finish:
            print(colored("=" * 70, Colors.RED))
            print(colored(f"         FIGHT OVER! {fight.winner_name} wins by {fight.method}!", Colors.WIN))
            print(colored(f"                    Time: {fight.time_finished}", Colors.DIM))
            print(colored("=" * 70, Colors.RED))
            print()
            pause()
            return
        
        # Navigation
        print_divider()
        if round_num < total_rounds:
            print(f"  [Enter] Next Round | [0] Exit Replay")
        else:
            print(f"  [Enter] View Result | [0] Exit Replay")
        
        choice = get_input("> ")
        if choice == "0":
            return
    
    # Decision result
    _display_decision_result(fight)


def _display_decision_result(fight: FightResult) -> None:
    """Display decision result screen."""
    clear_screen()
    print()
    print(colored("=" * 70, Colors.GOLD))
    print(colored("                    FIGHT GOES TO DECISION", Colors.BOLD))
    print(colored("=" * 70, Colors.GOLD))
    print()
    
    if fight.judge_scores:
        print(colored("  OFFICIAL SCORECARDS:", Colors.BOLD))
        print()
        for i, (f1_score, f2_score) in enumerate(fight.judge_scores, 1):
            print(f"  Judge {i}: {fight.fighter1_name} {f1_score} - {f2_score} {fight.fighter2_name}")
        print()
    
    print(colored("  WINNER:", Colors.BOLD))
    print(f"  {colored(fight.winner_name, Colors.WIN)} by {fight.method}")
    print()
    
    pause()


def display_key_moments(fight: FightResult) -> None:
    """Display key moments from a fight.
    
    Args:
        fight: FightResult object with key_moments
    """
    clear_screen()
    print_header("KEY MOMENTS")
    print()
    print(f"  {fight.fighter1_name} vs {fight.fighter2_name}")
    print()
    print_divider()
    print()
    
    for i, moment in enumerate(fight.key_moments, 1):
        if any(x in moment.upper() for x in ['KO', 'KNOCKOUT', 'FINISH', 'STOPPAGE']):
            color = Colors.RED
        elif any(x in moment.upper() for x in ['TAKEDOWN', 'SUBMISSION']):
            color = Colors.CYAN
        else:
            color = Colors.WHITE
        
        print(f"  {i}. {colored(moment, color)}")
        print()
    
    pause()


def display_fight_stats(fight: FightResult) -> None:
    """Display fight statistics.
    
    Args:
        fight: FightResult object
    """
    clear_screen()
    print_header("FIGHT STATISTICS")
    print()
    print(f"  {fight.fighter1_name} vs {fight.fighter2_name}")
    print()
    print_divider()
    print()
    
    # Stat comparison table
    print(f"  {'':20} {fight.fighter1_name:^15} {fight.fighter2_name:^15}")
    print(f"  {'-'*50}")
    print(f"  {'Sig. Strikes':20} {fight.fighter1_strikes:^15} {fight.fighter2_strikes:^15}")
    print(f"  {'Takedowns':20} {fight.fighter1_takedowns:^15} {fight.fighter2_takedowns:^15}")
    print(f"  {'Sub Attempts':20} {fight.fighter1_sub_attempts:^15} {fight.fighter2_sub_attempts:^15}")
    print()
    
    # Strike differential
    strike_diff = fight.fighter1_strikes - fight.fighter2_strikes
    if strike_diff > 0:
        print(f"  Strike Differential: {fight.fighter1_name} +{strike_diff}")
    elif strike_diff < 0:
        print(f"  Strike Differential: {fight.fighter2_name} +{abs(strike_diff)}")
    else:
        print(f"  Strike Differential: Even")
    
    print()
    pause()


def display_scorecards(fight: FightResult) -> None:
    """Display judge scorecards for a decision.
    
    Args:
        fight: FightResult object with judge_scores
    """
    clear_screen()
    print_header("OFFICIAL SCORECARDS")
    print()
    print(f"  {fight.fighter1_name} vs {fight.fighter2_name}")
    print()
    print_divider()
    print()
    
    f1_total = 0
    f2_total = 0
    
    for i, (f1_score, f2_score) in enumerate(fight.judge_scores, 1):
        f1_total += f1_score
        f2_total += f2_score
        
        if f1_score > f2_score:
            f1_display = colored(str(f1_score), Colors.WIN)
            f2_display = str(f2_score)
        elif f2_score > f1_score:
            f1_display = str(f1_score)
            f2_display = colored(str(f2_score), Colors.WIN)
        else:
            f1_display = str(f1_score)
            f2_display = str(f2_score)
        
        print(f"  Judge {i}: {f1_display} - {f2_display}")
    
    print()
    print(f"  {'-'*30}")
    print(f"  Total:   {f1_total} - {f2_total}")
    print()
    
    # Decision type
    judges_for_f1 = sum(1 for f1, f2 in fight.judge_scores if f1 > f2)
    judges_for_f2 = sum(1 for f1, f2 in fight.judge_scores if f2 > f1)
    
    if judges_for_f1 == 3 or judges_for_f2 == 3:
        decision_type = "Unanimous"
    elif judges_for_f1 == 2 or judges_for_f2 == 2:
        decision_type = "Split"
    else:
        decision_type = "Majority"
    
    print(f"  Decision: {decision_type}")
    print()
    
    pause()


# ============================================================================
# PAST EVENTS
# ============================================================================

def display_past_events(
    events: List[CompletedEvent],
    on_select: Optional[Callable[[CompletedEvent], None]] = None,
    page_size: int = 10
) -> None:
    """Display list of past events with pagination.
    
    Args:
        events: List of CompletedEvent objects
        on_select: Callback when an event is selected
        page_size: Number of events per page
    """
    if not events:
        clear_screen()
        print_header("PAST EVENTS")
        print("  No events recorded yet.")
        pause()
        return
    
    page = 0
    total_pages = (len(events) + page_size - 1) // page_size
    
    while True:
        clear_screen()
        print_header(f"PAST EVENTS (Page {page + 1}/{total_pages})")
        
        start = page * page_size
        end = min(start + page_size, len(events))
        page_events = events[start:end]
        
        for i, event in enumerate(page_events, start + 1):
            finishes = event.knockouts + event.submissions
            print(f"  [{i:2}] {event.event_name} (Week {event.week})")
            print(f"       {event.total_fights} fights | {finishes} finishes")
            print()
        
        print(f"  [N] Next | [P] Prev | [0] Back")
        print()
        
        choice = get_input("> ").lower()
        
        if choice == "0":
            return
        elif choice == "n" and page < total_pages - 1:
            page += 1
        elif choice == "p" and page > 0:
            page -= 1
        else:
            try:
                index = int(choice)
                if 1 <= index <= len(events) and on_select:
                    on_select(events[index - 1])
            except ValueError:
                pass


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # GOAT
    "calculate_goat_score",
    "display_goat_rankings",
    
    # Record book
    "display_record_book",
    "display_record_book_by_division",
    "display_division_records",
    
    # Champions
    "display_champions_history",
    
    # Fight details
    "display_fight_details",
    "replay_fight_round_by_round",
    "display_key_moments",
    "display_fight_stats",
    "display_scorecards",
    
    # Past events
    "display_past_events",
    
    # Yearly Awards
    "YearlyFighterStats",
    "calculate_yearly_stats",
    "calculate_foty_score",
    "get_fighter_of_the_year",
    "get_young_fighter_of_the_year",
    "display_yearly_awards",
]


# ============================================================================
# YEARLY AWARDS SYSTEM
# ============================================================================

@dataclass
class YearlyFighterStats:
    """Stats for a fighter within a single year."""
    fighter_id: str
    fighter_name: str
    year: int
    
    # Fight record this year
    wins: int = 0
    losses: int = 0
    draws: int = 0
    
    # Finish types this year
    ko_wins: int = 0
    tko_wins: int = 0
    sub_wins: int = 0
    decision_wins: int = 0
    
    # Quality metrics
    ranked_wins: int = 0  # Wins over ranked opponents
    title_wins: int = 0   # Title fights won (became champ or defended)
    title_defenses: int = 0  # Successful title defenses
    fotn_bonuses: int = 0  # Fight of the Night awards
    
    # Current status
    is_champion: bool = False
    current_win_streak: int = 0
    age: int = 0
    weight_class: str = ""
    overall_rating: int = 0
    
    @property
    def total_fights(self) -> int:
        return self.wins + self.losses + self.draws
    
    @property
    def finish_wins(self) -> int:
        return self.ko_wins + self.tko_wins + self.sub_wins


def calculate_yearly_stats(
    fighter_id: str,
    fighter_name: str,
    fight_results: List[Any],
    year: int,
    fighter_data: Any = None,
    weeks_per_year: int = 52,
) -> YearlyFighterStats:
    """
    Calculate a fighter's stats for a specific year.
    
    Args:
        fighter_id: Fighter's ID
        fighter_name: Fighter's name
        fight_results: List of FightResult objects
        year: Year number (1-based, calculated as week // 52 + 1)
        fighter_data: Optional fighter object for current status
        weeks_per_year: Weeks per year (default 52)
        
    Returns:
        YearlyFighterStats for this fighter/year
    """
    stats = YearlyFighterStats(
        fighter_id=fighter_id,
        fighter_name=fighter_name,
        year=year,
    )
    
    # Calculate week range for this year
    year_start_week = (year - 1) * weeks_per_year + 1
    year_end_week = year * weeks_per_year
    
    # Filter fights for this fighter in this year
    for fight in fight_results:
        fight_week = getattr(fight, 'week', 0)
        
        # Check if fight is in target year
        if not (year_start_week <= fight_week <= year_end_week):
            continue
        
        # Check if fighter was involved
        winner_id = getattr(fight, 'winner_id', None)
        loser_id = getattr(fight, 'loser_id', None)
        
        if fighter_id == winner_id:
            stats.wins += 1
            
            method = getattr(fight, 'method', '').upper()
            if 'KO' in method and 'TKO' not in method:
                stats.ko_wins += 1
            elif 'TKO' in method:
                stats.tko_wins += 1
            elif 'SUB' in method:
                stats.sub_wins += 1
            else:
                stats.decision_wins += 1
            
            # Title fight win
            if getattr(fight, 'is_title_fight', False):
                stats.title_wins += 1
                # If fighter was already champion, this is a defense
                # We'll infer this from the fight data
                stats.title_defenses += 1
            
            # FOTN bonus
            if getattr(fight, 'fight_of_night', False):
                stats.fotn_bonuses += 1
                
        elif fighter_id == loser_id:
            stats.losses += 1
            
            # FOTN can go to loser too
            if getattr(fight, 'fight_of_night', False):
                stats.fotn_bonuses += 1
    
    # Get current status from fighter data
    if fighter_data:
        stats.is_champion = getattr(fighter_data, 'is_champion', False)
        stats.current_win_streak = getattr(fighter_data, 'win_streak', 0)
        stats.age = getattr(fighter_data, 'age', 0)
        stats.weight_class = getattr(fighter_data, 'weight_class', '')
        stats.overall_rating = getattr(fighter_data, 'overall_rating', 0)
    
    return stats


def calculate_foty_score(stats: YearlyFighterStats) -> int:
    """
    Calculate Fighter of the Year score.
    
    Formula prioritizes:
    - Activity and winning (wins × 20)
    - Finishing fights (KO/TKO/SUB bonuses)
    - Quality wins (ranked opponents, title fights)
    - Entertainment value (FOTN bonuses)
    - Momentum (active win streak)
    - Penalizes losses heavily
    
    Args:
        stats: YearlyFighterStats for the year
        
    Returns:
        FOTY score (can be negative for bad years)
    """
    score = 0
    
    # Base points for wins
    score += stats.wins * 20
    
    # Heavy penalty for losses
    score -= stats.losses * 15
    
    # Finish bonuses (on top of win points)
    score += stats.ko_wins * 12      # KOs are exciting
    score += stats.tko_wins * 10     # TKOs too
    score += stats.sub_wins * 10     # Subs show skill
    
    # Title achievements (major boost)
    score += stats.title_wins * 50    # Winning a title fight
    score += stats.title_defenses * 25  # Extra for defenses
    
    # Quality wins (we don't track ranked wins yet, but ready for it)
    score += stats.ranked_wins * 8
    
    # Entertainment value
    score += stats.fotn_bonuses * 15  # FOTN shows exciting style
    
    # Current momentum
    score += min(stats.current_win_streak, 5) * 5  # Cap at 5 for scoring
    
    # Champion bonus (being champ at year end)
    if stats.is_champion:
        score += 30
    
    # Activity requirement - need at least 2 fights to qualify
    if stats.total_fights < 2:
        score = score // 2  # Halve score for inactive fighters
    
    return score


def get_fighter_of_the_year(
    fighters: List[Any],
    fight_results: List[Any],
    year: int,
    min_fights: int = 2,
) -> Optional[Tuple[Any, YearlyFighterStats, int]]:
    """
    Determine Fighter of the Year.
    
    Args:
        fighters: List of fighter objects (or dict)
        fight_results: List of FightResult objects
        year: Year to evaluate
        min_fights: Minimum fights required to qualify
        
    Returns:
        Tuple of (fighter, yearly_stats, score) or None if no qualifiers
    """
    candidates = []
    
    # Handle both list and dict of fighters
    if isinstance(fighters, dict):
        fighter_list = list(fighters.values())
    else:
        fighter_list = fighters
    
    for fighter in fighter_list:
        fighter_id = getattr(fighter, 'fighter_id', None) or getattr(fighter, 'id', None)
        fighter_name = getattr(fighter, 'name', 'Unknown')
        
        if not fighter_id:
            continue
        
        stats = calculate_yearly_stats(
            fighter_id=fighter_id,
            fighter_name=fighter_name,
            fight_results=fight_results,
            year=year,
            fighter_data=fighter,
        )
        
        # Must have minimum fights
        if stats.total_fights < min_fights:
            continue
        
        # Must have positive record (more wins than losses)
        if stats.wins <= stats.losses:
            continue
        
        score = calculate_foty_score(stats)
        candidates.append((fighter, stats, score))
    
    if not candidates:
        return None
    
    # Sort by score descending
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    return candidates[0]


def get_young_fighter_of_the_year(
    fighters: List[Any],
    fight_results: List[Any],
    year: int,
    max_age: int = 25,
    min_fights: int = 2,
) -> Optional[Tuple[Any, YearlyFighterStats, int]]:
    """
    Determine Young Fighter of the Year (25 and under).
    
    Args:
        fighters: List of fighter objects
        fight_results: List of FightResult objects
        year: Year to evaluate
        max_age: Maximum age to qualify (default 25)
        min_fights: Minimum fights required
        
    Returns:
        Tuple of (fighter, yearly_stats, score) or None
    """
    candidates = []
    
    # Handle both list and dict of fighters
    if isinstance(fighters, dict):
        fighter_list = list(fighters.values())
    else:
        fighter_list = fighters
    
    for fighter in fighter_list:
        # Age check first
        age = getattr(fighter, 'age', 99)
        if age > max_age:
            continue
        
        fighter_id = getattr(fighter, 'fighter_id', None) or getattr(fighter, 'id', None)
        fighter_name = getattr(fighter, 'name', 'Unknown')
        
        if not fighter_id:
            continue
        
        stats = calculate_yearly_stats(
            fighter_id=fighter_id,
            fighter_name=fighter_name,
            fight_results=fight_results,
            year=year,
            fighter_data=fighter,
        )
        
        # Must have minimum fights
        if stats.total_fights < min_fights:
            continue
        
        # Must have positive record
        if stats.wins <= stats.losses:
            continue
        
        score = calculate_foty_score(stats)
        candidates.append((fighter, stats, score))
    
    if not candidates:
        return None
    
    # Sort by score descending
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    return candidates[0]


def display_yearly_awards(
    fighters: List[Any],
    fight_results: List[Any],
    year: int,
    year_display: str = None,
) -> None:
    """
    Display Fighter of the Year and Young Fighter of the Year awards.
    
    Args:
        fighters: List of fighter objects
        fight_results: List of FightResult objects
        year: Year number
        year_display: Optional display string for year (e.g., "2025")
    """
    clear_screen()
    
    year_str = year_display or f"Year {year}"
    print_header(f"DFC AWARDS - {year_str}")
    
    print()
    
    # Fighter of the Year
    print(colored("  🏆 FIGHTER OF THE YEAR", Colors.GOLD))
    print(colored("  " + "=" * 40, Colors.GOLD))
    print()
    
    foty = get_fighter_of_the_year(fighters, fight_results, year)
    
    if foty:
        fighter, stats, score = foty
        name = getattr(fighter, 'name', 'Unknown')
        
        champ_tag = colored(" [C]", Colors.GOLD) if stats.is_champion else ""
        
        print(f"    {colored(name, Colors.WIN)}{champ_tag}")
        print(f"    {stats.weight_class}")
        print()
        print(f"    Year Record: {colored(f'{stats.wins}-{stats.losses}', Colors.CYAN)}")
        
        if stats.finish_wins > 0:
            finishes = []
            if stats.ko_wins > 0:
                finishes.append(f"{stats.ko_wins} KO")
            if stats.tko_wins > 0:
                finishes.append(f"{stats.tko_wins} TKO")
            if stats.sub_wins > 0:
                finishes.append(f"{stats.sub_wins} SUB")
            print(f"    Finishes: {', '.join(finishes)}")
        
        if stats.title_wins > 0:
            print(f"    Title Fights Won: {colored(str(stats.title_wins), Colors.GOLD)}")
        
        if stats.fotn_bonuses > 0:
            print(f"    Fight of the Night: {stats.fotn_bonuses}x")
        
        print(f"    FOTY Score: {colored(str(score), Colors.CYAN)}")
    else:
        print("    No qualifying fighters this year.")
        print("    (Requires 2+ fights with winning record)")
    
    print()
    print()
    
    # Young Fighter of the Year
    print(colored("  🌟 YOUNG FIGHTER OF THE YEAR (25 & Under)", Colors.CYAN))
    print(colored("  " + "=" * 40, Colors.CYAN))
    print()
    
    yfoty = get_young_fighter_of_the_year(fighters, fight_results, year)
    
    if yfoty:
        fighter, stats, score = yfoty
        name = getattr(fighter, 'name', 'Unknown')
        age = getattr(fighter, 'age', 0)
        
        champ_tag = colored(" [C]", Colors.GOLD) if stats.is_champion else ""
        
        print(f"    {colored(name, Colors.WIN)}{champ_tag} (Age {age})")
        print(f"    {stats.weight_class}")
        print()
        print(f"    Year Record: {colored(f'{stats.wins}-{stats.losses}', Colors.CYAN)}")
        
        if stats.finish_wins > 0:
            finishes = []
            if stats.ko_wins > 0:
                finishes.append(f"{stats.ko_wins} KO")
            if stats.tko_wins > 0:
                finishes.append(f"{stats.tko_wins} TKO")
            if stats.sub_wins > 0:
                finishes.append(f"{stats.sub_wins} SUB")
            print(f"    Finishes: {', '.join(finishes)}")
        
        if stats.title_wins > 0:
            print(f"    Title Fights Won: {colored(str(stats.title_wins), Colors.GOLD)}")
        
        if stats.fotn_bonuses > 0:
            print(f"    Fight of the Night: {stats.fotn_bonuses}x")
        
        print(f"    YFOTY Score: {colored(str(score), Colors.CYAN)}")
    else:
        print("    No qualifying young fighters this year.")
        print("    (Requires age 25 or under, 2+ fights, winning record)")
    
    print()
    pause()
