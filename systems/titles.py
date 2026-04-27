"""
Title Management System for Cage Dynasty

Handles all championship title logic including:
- Vacant title detection and scheduling
- Title transfers after fights
- Champion stripping
- Title fight validation

This module contains business logic only - no UI code.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class TitleChangeType(Enum):
    """Types of title changes that can occur."""
    NEW_CHAMPION = "new_champion"           # Challenger wins title
    VACANT_CLAIMED = "vacant_claimed"       # Winner claims vacant title
    SUCCESSFUL_DEFENSE = "defense"          # Champion retains
    TITLE_STRIPPED = "stripped"             # Champion stripped (injury, etc.)
    TITLE_VACATED = "vacated"               # Champion retires/leaves


@dataclass
class TitleChangeResult:
    """Result of a title change operation."""
    change_type: TitleChangeType
    weight_class: str
    new_champion_id: Optional[str] = None
    new_champion_name: Optional[str] = None
    former_champion_id: Optional[str] = None
    former_champion_name: Optional[str] = None
    headline: str = ""
    details: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "weight_class": self.weight_class,
            "new_champion_id": self.new_champion_id,
            "new_champion_name": self.new_champion_name,
            "former_champion_id": self.former_champion_id,
            "former_champion_name": self.former_champion_name,
            "headline": self.headline,
            "details": self.details,
        }


@dataclass
class VacantTitleFight:
    """Data for a vacant title fight to be scheduled."""
    weight_class: str
    fighter1_id: str
    fighter1_name: str
    fighter2_id: str
    fighter2_name: str
    weeks_until: int = 4
    event_name: str = ""
    headline: str = ""
    details: str = ""
    
    def to_fight_dict(self) -> Dict[str, Any]:
        """Convert to fight dictionary format used by CLI."""
        return {
            "fighter1_id": self.fighter1_id,
            "fighter1_name": self.fighter1_name,
            "fighter2_id": self.fighter2_id,
            "fighter2_name": self.fighter2_name,
            "weight_class": self.weight_class,
            "is_title_fight": True,
            "is_vacant_title": True,
            "is_main_event": True,
            "rounds": 5,
            "weeks_until": self.weeks_until,
            "event_name": self.event_name,
        }


class TitleSystem:
    """
    Manages championship titles across all weight classes.
    
    This system handles:
    - Detecting vacant titles
    - Finding contenders for title shots
    - Processing title changes after fights
    - Stripping champions when needed
    """
    
    def __init__(self):
        """Initialize the title system."""
        pass
    
    def get_vacant_divisions(
        self,
        divisions: Dict[str, Any],
    ) -> List[str]:
        """
        Get list of weight classes with vacant titles.
        
        Args:
            divisions: Dictionary of division states keyed by weight class
            
        Returns:
            List of weight class names with vacant titles
        """
        vacant = []
        for weight_class, div_state in divisions.items():
            champion_id = getattr(div_state, 'champion_id', None)
            if champion_id is None:
                vacant.append(weight_class)
        return vacant
    
    def is_title_vacant(
        self,
        divisions: Dict[str, Any],
        weight_class: str,
    ) -> bool:
        """
        Check if a specific division's title is vacant.
        
        Args:
            divisions: Dictionary of division states
            weight_class: Weight class to check
            
        Returns:
            True if title is vacant, False otherwise
        """
        div_state = divisions.get(weight_class)
        if div_state is None:
            return True
        return getattr(div_state, 'champion_id', None) is None
    
    def is_title_fight_scheduled(
        self,
        weight_class: str,
        scheduled_fights: List[Dict[str, Any]],
    ) -> bool:
        """
        Check if a title fight is already scheduled for a division.
        
        Args:
            weight_class: Weight class to check
            scheduled_fights: List of all scheduled fights
            
        Returns:
            True if a title fight is scheduled for this division
        """
        for fight in scheduled_fights:
            if (fight.get("is_title_fight") and 
                fight.get("weight_class") == weight_class):
                return True
        return False
    
    def get_title_contenders(
        self,
        weight_class: str,
        fighters: Dict[str, Any],
        exclude_ids: Optional[set] = None,
        count: int = 2,
    ) -> List[Any]:
        """
        Get top contenders for a title shot in a division.
        
        Args:
            weight_class: Weight class to find contenders for
            fighters: Dictionary of all fighters
            exclude_ids: Fighter IDs to exclude (already scheduled, etc.)
            count: Number of contenders to return
            
        Returns:
            List of fighter objects sorted by rating (best first)
        """
        if exclude_ids is None:
            exclude_ids = set()
        
        contenders = []
        for fighter_id, fighter in fighters.items():
            # Check weight class
            if getattr(fighter, 'weight_class', '') != weight_class:
                continue
            # Check active
            if not getattr(fighter, 'is_active', True):
                continue
            # Check not champion
            if getattr(fighter, 'is_champion', False):
                continue
            # Check not excluded
            if fighter_id in exclude_ids:
                continue
            
            contenders.append(fighter)
        
        # Sort by overall rating
        contenders.sort(
            key=lambda f: getattr(f, 'overall_rating', 0),
            reverse=True
        )
        
        return contenders[:count]
    
    def is_valid_challenger(
        self,
        challenger_id: str,
        weight_class: str,
        fighters: Dict[str, Any],
        fighter_records: Optional[Dict[str, Any]] = None,
        top_n: int = 5,
        min_win_streak: int = 5,
    ) -> bool:
        """
        Check if a fighter is a valid title challenger.
        
        A fighter qualifies for a title shot if they meet ANY of these criteria:
        1. Ranked in top N of their division (default top 5)
        2. On a significant win streak (default 5+)
        3. Is a champion themselves (superfight scenario)
        
        Args:
            challenger_id: Fighter ID to check
            weight_class: Weight class for the title
            fighters: Dictionary of all fighters
            fighter_records: Optional dict of fighter_id -> record data with win_streak
            top_n: How many top contenders qualify (default 5)
            min_win_streak: Minimum win streak to qualify (default 5)
            
        Returns:
            True if fighter is a valid title challenger
        """
        fighter = fighters.get(challenger_id)
        if not fighter:
            return False
        
        # Champions can always challenge other champions (superfights)
        if getattr(fighter, 'is_champion', False):
            return True
        
        # Must be in the same weight class
        if getattr(fighter, 'weight_class', '') != weight_class:
            return False
        
        # Must be active
        if not getattr(fighter, 'is_active', True):
            return False
        
        # Get division fighters sorted by rating (excluding champion)
        div_fighters = []
        for fid, f in fighters.items():
            if getattr(f, 'weight_class', '') != weight_class:
                continue
            if not getattr(f, 'is_active', True):
                continue
            if getattr(f, 'is_champion', False):
                continue
            div_fighters.append((fid, f))
        
        div_fighters.sort(
            key=lambda x: getattr(x[1], 'overall_rating', 0),
            reverse=True
        )
        
        # Check if ranked in top N
        for i, (fid, f) in enumerate(div_fighters[:top_n]):
            if fid == challenger_id:
                return True
        
        # Check for significant win streak
        if fighter_records:
            record = fighter_records.get(challenger_id)
            if record:
                win_streak = getattr(record, 'win_streak', 0)
                if win_streak >= min_win_streak:
                    return True
        
        # Also check fighter object directly for win_streak
        win_streak = getattr(fighter, 'win_streak', 0)
        if win_streak >= min_win_streak:
            return True
        
        return False
    
    def should_be_title_fight(
        self,
        fighter1_id: str,
        fighter2_id: str,
        weight_class: str,
        fighters: Dict[str, Any],
        divisions: Dict[str, Any],
        fighter_records: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Determine if a fight between two fighters should be a title fight.
        
        Rules:
        - If title is vacant: both must be valid challengers (top contenders)
        - If champion involved: opponent must be valid challenger
        - Otherwise: not a title fight
        
        Args:
            fighter1_id: First fighter ID
            fighter2_id: Second fighter ID  
            weight_class: Weight class
            fighters: Dictionary of all fighters
            divisions: Dictionary of division states
            fighter_records: Optional fighter record data
            
        Returns:
            True if this should be a title fight
        """
        f1 = fighters.get(fighter1_id)
        f2 = fighters.get(fighter2_id)
        
        if not f1 or not f2:
            return False
        
        f1_is_champ = getattr(f1, 'is_champion', False)
        f2_is_champ = getattr(f2, 'is_champion', False)
        
        # Check if title is vacant
        is_vacant = self.is_title_vacant(divisions, weight_class)
        
        if is_vacant:
            # For vacant title: both should be top contenders
            f1_valid = self.is_valid_challenger(
                fighter1_id, weight_class, fighters, fighter_records
            )
            f2_valid = self.is_valid_challenger(
                fighter2_id, weight_class, fighters, fighter_records
            )
            return f1_valid and f2_valid
        
        # Champion vs challenger
        if f1_is_champ and f1.weight_class == weight_class:
            return self.is_valid_challenger(
                fighter2_id, weight_class, fighters, fighter_records
            )
        
        if f2_is_champ and f2.weight_class == weight_class:
            return self.is_valid_challenger(
                fighter1_id, weight_class, fighters, fighter_records
            )
        
        return False
    
    def create_vacant_title_fight(
        self,
        weight_class: str,
        fighters: Dict[str, Any],
        scheduled_fights: List[Dict[str, Any]],
        event_number: int,
        weeks_until: int = 4,
    ) -> Optional[VacantTitleFight]:
        """
        Create a vacant title fight between top contenders.
        
        Args:
            weight_class: Weight class for the title fight
            fighters: Dictionary of all fighters
            scheduled_fights: Current scheduled fights (to check exclusions)
            event_number: Event number for naming
            weeks_until: Weeks until the fight
            
        Returns:
            VacantTitleFight if enough contenders, None otherwise
        """
        # Get fighters already scheduled for title fights in this division
        scheduled_ids = set()
        for fight in scheduled_fights:
            if (fight.get("is_title_fight") and 
                fight.get("weight_class") == weight_class):
                scheduled_ids.add(fight.get("fighter1_id"))
                scheduled_ids.add(fight.get("fighter2_id"))
        
        # Get top 2 available contenders
        contenders = self.get_title_contenders(
            weight_class, fighters, scheduled_ids, count=2
        )
        
        if len(contenders) < 2:
            return None
        
        f1 = contenders[0]
        f2 = contenders[1]
        
        event_name = f"DFC Championship Night {event_number}"
        
        return VacantTitleFight(
            weight_class=weight_class,
            fighter1_id=f1.fighter_id,
            fighter1_name=f1.name,
            fighter2_id=f2.fighter_id,
            fighter2_name=f2.name,
            weeks_until=weeks_until,
            event_name=event_name,
            headline=f"VACANT TITLE: {f1.name} vs {f2.name} for {weight_class} championship!",
            details=f"With the {weight_class} title vacant, #1 {f1.name} faces #2 {f2.name} for the gold.",
        )
    
    def check_and_create_vacant_fights(
        self,
        divisions: Dict[str, Any],
        fighters: Dict[str, Any],
        scheduled_fights: List[Dict[str, Any]],
        event_number: int,
    ) -> List[VacantTitleFight]:
        """
        Check all divisions for vacant titles and create fights as needed.
        
        Args:
            divisions: Dictionary of division states
            fighters: Dictionary of all fighters
            scheduled_fights: Current scheduled fights
            event_number: Starting event number for naming
            
        Returns:
            List of VacantTitleFight objects to be scheduled
        """
        fights_to_schedule = []
        current_event_num = event_number
        
        for weight_class in self.get_vacant_divisions(divisions):
            if not self.is_title_fight_scheduled(weight_class, scheduled_fights):
                fight = self.create_vacant_title_fight(
                    weight_class,
                    fighters,
                    scheduled_fights + [f.to_fight_dict() for f in fights_to_schedule],
                    current_event_num,
                )
                if fight:
                    fights_to_schedule.append(fight)
                    current_event_num += 1
        
        return fights_to_schedule
    
    def process_title_fight_result(
        self,
        fight: Dict[str, Any],
        winner_id: str,
        loser_id: str,
        winner_name: str,
        loser_name: str,
        divisions: Dict[str, Any],
        fighters: Dict[str, Any],
    ) -> Optional[TitleChangeResult]:
        """
        Process the result of a title fight and update state.
        
        Args:
            fight: Fight data dictionary
            winner_id: ID of the winning fighter
            loser_id: ID of the losing fighter
            winner_name: Name of the winner
            loser_name: Name of the loser
            divisions: Dictionary of division states (will be modified)
            fighters: Dictionary of fighters (will be modified)
            
        Returns:
            TitleChangeResult describing what happened, or None if not a title fight
        """
        if not fight.get("is_title_fight"):
            return None
        
        weight_class = fight.get("weight_class", "")
        if not weight_class or weight_class not in divisions:
            return None
        
        div_state = divisions[weight_class]
        is_vacant = fight.get("is_vacant_title", False) or div_state.champion_id is None
        
        # Case 1: Vacant title fight
        if is_vacant:
            return self._process_vacant_title_win(
                weight_class, winner_id, winner_name, div_state, fighters
            )
        
        # Case 2: Champion lost
        if div_state.champion_id == loser_id:
            return self._process_title_change(
                weight_class, winner_id, winner_name,
                loser_id, loser_name, div_state, fighters
            )
        
        # Case 3: Champion won (successful defense)
        if div_state.champion_id == winner_id:
            return TitleChangeResult(
                change_type=TitleChangeType.SUCCESSFUL_DEFENSE,
                weight_class=weight_class,
                new_champion_id=winner_id,
                new_champion_name=winner_name,
                headline=f"{winner_name} defends {weight_class} title!",
                details=f"{winner_name} successfully defends against {loser_name}.",
            )
        
        return None
    
    def _process_vacant_title_win(
        self,
        weight_class: str,
        winner_id: str,
        winner_name: str,
        div_state: Any,
        fighters: Dict[str, Any],
    ) -> TitleChangeResult:
        """Process a vacant title being claimed."""
        # Update division state
        div_state.champion_id = winner_id
        if hasattr(div_state, 'champion_name'):
            div_state.champion_name = winner_name
        
        # Update fighter
        if winner_id in fighters:
            fighters[winner_id].is_champion = True
        
        return TitleChangeResult(
            change_type=TitleChangeType.VACANT_CLAIMED,
            weight_class=weight_class,
            new_champion_id=winner_id,
            new_champion_name=winner_name,
            headline=f"NEW CHAMPION! {winner_name} wins the vacant {weight_class} title!",
            details=f"{winner_name} claims the vacant {weight_class} championship.",
        )
    
    def _process_title_change(
        self,
        weight_class: str,
        winner_id: str,
        winner_name: str,
        loser_id: str,
        loser_name: str,
        div_state: Any,
        fighters: Dict[str, Any],
    ) -> TitleChangeResult:
        """Process a title changing hands."""
        # Update division state
        div_state.champion_id = winner_id
        if hasattr(div_state, 'champion_name'):
            div_state.champion_name = winner_name
        
        # Update fighters
        if winner_id in fighters:
            fighters[winner_id].is_champion = True
        if loser_id in fighters:
            fighters[loser_id].is_champion = False
        
        return TitleChangeResult(
            change_type=TitleChangeType.NEW_CHAMPION,
            weight_class=weight_class,
            new_champion_id=winner_id,
            new_champion_name=winner_name,
            former_champion_id=loser_id,
            former_champion_name=loser_name,
            headline=f"NEW CHAMPION! {winner_name} dethrones {loser_name} for the {weight_class} title!",
            details=f"{winner_name} defeats {loser_name} to become the new {weight_class} champion.",
        )
    
    def strip_champion(
        self,
        weight_class: str,
        reason: str,
        divisions: Dict[str, Any],
        fighters: Dict[str, Any],
    ) -> Optional[TitleChangeResult]:
        """
        Strip the champion of a division.
        
        Args:
            weight_class: Weight class to strip
            reason: Reason for stripping (e.g., "injury", "retirement")
            divisions: Dictionary of division states (will be modified)
            fighters: Dictionary of fighters (will be modified)
            
        Returns:
            TitleChangeResult describing the strip, or None if no champion
        """
        if weight_class not in divisions:
            return None
        
        div_state = divisions[weight_class]
        if div_state.champion_id is None:
            return None
        
        former_champ_id = div_state.champion_id
        former_champ_name = getattr(div_state, 'champion_name', None)
        
        # Get name from fighters if not in div_state
        if former_champ_name is None and former_champ_id in fighters:
            former_champ_name = getattr(fighters[former_champ_id], 'name', 'Unknown')
        
        # Update division
        div_state.champion_id = None
        if hasattr(div_state, 'champion_name'):
            div_state.champion_name = None
        
        # Update fighter
        if former_champ_id in fighters:
            fighters[former_champ_id].is_champion = False
        
        return TitleChangeResult(
            change_type=TitleChangeType.TITLE_STRIPPED if reason != "retirement" else TitleChangeType.TITLE_VACATED,
            weight_class=weight_class,
            former_champion_id=former_champ_id,
            former_champion_name=former_champ_name,
            headline=f"{weight_class} title vacated following {former_champ_name}'s {reason}",
            details=f"The {weight_class} championship is now vacant.",
        )
    
    def get_champion_info(
        self,
        weight_class: str,
        divisions: Dict[str, Any],
        fighters: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about the current champion of a division.
        
        Args:
            weight_class: Weight class to check
            divisions: Dictionary of division states
            fighters: Dictionary of fighters
            
        Returns:
            Dictionary with champion info, or None if vacant
        """
        if weight_class not in divisions:
            return None
        
        div_state = divisions[weight_class]
        if div_state.champion_id is None:
            return None
        
        champ = fighters.get(div_state.champion_id)
        if champ is None:
            return None
        
        return {
            "fighter_id": div_state.champion_id,
            "name": champ.name,
            "record": f"{champ.wins}-{champ.losses}",
            "overall_rating": champ.overall_rating,
            "weight_class": weight_class,
        }
    
    def get_all_champions(
        self,
        divisions: Dict[str, Any],
        fighters: Dict[str, Any],
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get champion info for all divisions.
        
        Args:
            divisions: Dictionary of division states
            fighters: Dictionary of fighters
            
        Returns:
            Dictionary mapping weight class to champion info (or None if vacant)
        """
        result = {}
        for weight_class in divisions:
            result[weight_class] = self.get_champion_info(
                weight_class, divisions, fighters
            )
        return result
    
    def validate_title_fight(
        self,
        fight: Dict[str, Any],
        divisions: Dict[str, Any],
        fighters: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Validate that a title fight is properly set up.
        
        Args:
            fight: Fight data to validate
            divisions: Dictionary of division states
            fighters: Dictionary of fighters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not fight.get("is_title_fight"):
            return True, ""  # Not a title fight, nothing to validate
        
        weight_class = fight.get("weight_class", "")
        if not weight_class:
            return False, "Title fight missing weight class"
        
        if weight_class not in divisions:
            return False, f"Unknown weight class: {weight_class}"
        
        f1_id = fight.get("fighter1_id")
        f2_id = fight.get("fighter2_id")
        
        if not f1_id or not f2_id:
            return False, "Title fight missing fighter IDs"
        
        f1 = fighters.get(f1_id)
        f2 = fighters.get(f2_id)
        
        if not f1 or not f2:
            return False, "Title fight has invalid fighter IDs"
        
        # Check at least one is champion OR title is vacant
        div_state = divisions[weight_class]
        is_vacant = div_state.champion_id is None
        has_champion = f1_id == div_state.champion_id or f2_id == div_state.champion_id
        
        if not is_vacant and not has_champion:
            return False, "Title fight must include the champion or be for a vacant title"
        
        return True, ""


# Module-level instance for convenience
_title_system = None


def get_title_system() -> TitleSystem:
    """Get or create the global TitleSystem instance."""
    global _title_system
    if _title_system is None:
        _title_system = TitleSystem()
    return _title_system
