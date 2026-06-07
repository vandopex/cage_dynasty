# systems/card_builder.py
# Module: Card Builder
# Lines: ~480
#
# Manages fight card structure with Main Event, Co-Main, Main Card, and Prelims.
# Assigns fights to appropriate card slots based on matchup quality and title status.

"""
Cage Dynasty - Card Builder

Creates UFC-style fight card structure:
- Main Event (1): Title fights or highest matchup score (80+)
- Co-Main (1): Second highest or score 70+
- Main Card (2-3): Score 55+
- Prelims (5-7): Everything else

Usage:
    from systems.card_builder import CardBuilder, CardSlot
    
    builder = CardBuilder()
    slot = builder.assign_slot(matchup_score=88, is_title=False, event_slots=current_slots)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# CARD SLOT DEFINITIONS
# ============================================================================

class CardSlot(Enum):
    """Card position for a fight (UFC-style structure)"""
    MAIN_EVENT = "main_event"      # Title fights, mega bouts
    CO_MAIN = "co_main"            # Top contender clashes
    MAIN_CARD = "main_card"        # Ranked fights
    PRELIM = "prelim"              # Lower ranked, gatekeeper tests
    EARLY_PRELIM = "early_prelim"  # Unranked prospects, debuts


# Slot capacity per event (UFC-style: ~12 fights)
SLOT_LIMITS = {
    CardSlot.MAIN_EVENT: 1,
    CardSlot.CO_MAIN: 1,
    CardSlot.MAIN_CARD: 3,
    CardSlot.PRELIM: 4,
    CardSlot.EARLY_PRELIM: 3,
}

# Score thresholds for slot assignment
SCORE_THRESHOLDS = {
    CardSlot.MAIN_EVENT: 80,       # 80+ for main event
    CardSlot.CO_MAIN: 70,          # 70+ for co-main
    CardSlot.MAIN_CARD: 55,        # 55+ for main card
    CardSlot.PRELIM: 35,           # 35+ for prelims
    CardSlot.EARLY_PRELIM: 0,      # Everything else (unranked)
}

# Display order (for sorting)
SLOT_ORDER = {
    CardSlot.MAIN_EVENT: 0,
    CardSlot.CO_MAIN: 1,
    CardSlot.MAIN_CARD: 2,
    CardSlot.PRELIM: 3,
    CardSlot.EARLY_PRELIM: 4,
}


# ============================================================================
# EVENT CARD STATE
# ============================================================================

@dataclass
class EventCardState:
    """
    Tracks the current state of slots on an event card.
    
    UFC-style structure:
    - Main Event (1): Title fights or mega bouts
    - Co-Main (1): Top contender clashes  
    - Main Card (3): Ranked fights
    - Prelims (4): Lower ranked, gatekeeper tests
    - Early Prelims (3): Unranked prospects, debuts
    """
    event_name: str
    weeks_until: int
    
    # Current slot counts
    main_event_count: int = 0
    co_main_count: int = 0
    main_card_count: int = 0
    prelim_count: int = 0
    early_prelim_count: int = 0
    
    # Title fight tracking (main event is reserved for titles)
    has_title_fight: bool = False
    
    @property
    def total_fights(self) -> int:
        return (self.main_event_count + self.co_main_count + 
                self.main_card_count + self.prelim_count + self.early_prelim_count)
    
    @property
    def is_full(self) -> bool:
        """Check if card has reached max capacity (12 fights)"""
        return self.total_fights >= 12
    
    @property
    def main_event_available(self) -> bool:
        return self.main_event_count < SLOT_LIMITS[CardSlot.MAIN_EVENT]
    
    @property
    def co_main_available(self) -> bool:
        return self.co_main_count < SLOT_LIMITS[CardSlot.CO_MAIN]
    
    @property
    def main_card_available(self) -> bool:
        return self.main_card_count < SLOT_LIMITS[CardSlot.MAIN_CARD]
    
    @property
    def prelim_available(self) -> bool:
        return self.prelim_count < SLOT_LIMITS[CardSlot.PRELIM]
    
    @property
    def early_prelim_available(self) -> bool:
        return self.early_prelim_count < SLOT_LIMITS[CardSlot.EARLY_PRELIM]
    
    def get_slot_count(self, slot: CardSlot) -> int:
        """Get current count for a slot type"""
        if slot == CardSlot.MAIN_EVENT:
            return self.main_event_count
        elif slot == CardSlot.CO_MAIN:
            return self.co_main_count
        elif slot == CardSlot.MAIN_CARD:
            return self.main_card_count
        elif slot == CardSlot.PRELIM:
            return self.prelim_count
        else:
            return self.early_prelim_count
    
    def is_slot_available(self, slot: CardSlot) -> bool:
        """Check if a specific slot type has room"""
        current = self.get_slot_count(slot)
        limit = SLOT_LIMITS[slot]
        return current < limit
    
    def add_fight(self, slot: CardSlot) -> None:
        """Record a fight being added to a slot"""
        if slot == CardSlot.MAIN_EVENT:
            self.main_event_count += 1
        elif slot == CardSlot.CO_MAIN:
            self.co_main_count += 1
        elif slot == CardSlot.MAIN_CARD:
            self.main_card_count += 1
        elif slot == CardSlot.PRELIM:
            self.prelim_count += 1
        else:
            self.early_prelim_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_name": self.event_name,
            "weeks_until": self.weeks_until,
            "main_event_count": self.main_event_count,
            "co_main_count": self.co_main_count,
            "main_card_count": self.main_card_count,
            "prelim_count": self.prelim_count,
            "early_prelim_count": self.early_prelim_count,
            "has_title_fight": self.has_title_fight,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventCardState":
        return cls(
            event_name=data.get("event_name", ""),
            weeks_until=data.get("weeks_until", 0),
            main_event_count=data.get("main_event_count", 0),
            co_main_count=data.get("co_main_count", 0),
            main_card_count=data.get("main_card_count", 0),
            prelim_count=data.get("prelim_count", 0),
            early_prelim_count=data.get("early_prelim_count", 0),
            has_title_fight=data.get("has_title_fight", False),
        )


# ============================================================================
# CARD BUILDER
# ============================================================================

class CardBuilder:
    """
    Handles fight card slot assignment.
    
    Ensures fights are placed in appropriate slots based on:
    - Title fight status (always main event)
    - Matchup score
    - Available slots on the card
    """
    
    def __init__(self):
        # Track card states by event name
        self._card_states: Dict[str, EventCardState] = {}
    
    def get_or_create_card_state(
        self, 
        event_name: str, 
        weeks_until: int
    ) -> EventCardState:
        """Get existing card state or create new one"""
        if event_name not in self._card_states:
            self._card_states[event_name] = EventCardState(
                event_name=event_name,
                weeks_until=weeks_until
            )
        return self._card_states[event_name]
    
    def update_card_state_from_fights(
        self,
        event_name: str,
        weeks_until: int,
        fights: List[Dict[str, Any]]
    ) -> EventCardState:
        """
        Rebuild card state from existing fights.
        
        Used when loading or syncing state.
        """
        state = EventCardState(event_name=event_name, weeks_until=weeks_until)
        
        for fight in fights:
            slot_str = fight.get("card_slot", "prelim")
            try:
                slot = CardSlot(slot_str)
            except ValueError:
                slot = CardSlot.PRELIM
            
            state.add_fight(slot)
            
            if fight.get("is_title_fight"):
                state.has_title_fight = True
        
        self._card_states[event_name] = state
        return state
    
    def calculate_matchup_score(
        self,
        fighter1_rating: int,
        fighter2_rating: int,
        fighter1_rank: Optional[int] = None,
        fighter2_rank: Optional[int] = None,
        is_title_fight: bool = False,
        is_rivalry: bool = False,
        fighter1_wins: int = 0,
        fighter1_losses: int = 0,
        fighter2_wins: int = 0,
        fighter2_losses: int = 0,
    ) -> float:
        """
        Calculate matchup score for card placement.
        Driven by rank and record — NOT overall rating.

        Score ranges 0-130.
        Factors (in order of importance):
          1. Both fighters ranked (foundation)
          2. Rank proximity (adjacent contenders = best fights)
          3. Title fight
          4. Record quality (combined fights = experience)
          5. Rivalry bonus
          6. Penalties for rank gaps and ranked-vs-unranked
        """
        f1_ranked = fighter1_rank is not None and fighter1_rank <= 15
        f2_ranked = fighter2_rank is not None and fighter2_rank <= 15
        both_ranked   = f1_ranked and f2_ranked
        both_unranked = not f1_ranked and not f2_ranked
        one_ranked    = (f1_ranked or f2_ranked) and not both_ranked

        # ── Base: both ranked = start at 40, unranked fights cap at 25 ────
        if both_ranked:
            base_score = 40.0
        elif one_ranked:
            base_score = 20.0
        else:
            base_score = 15.0  # both unranked

        # ── Rank proximity bonus (spine of the system) ────────────────────
        rank_bonus = 0.0
        if both_ranked:
            rank_diff = abs(fighter1_rank - fighter2_rank)
            if rank_diff == 0:
                rank_bonus += 25   # same rank (shouldn't happen but handle it)
            elif rank_diff <= 1:
                rank_bonus += 30   # adjacent — the gold standard
            elif rank_diff <= 3:
                rank_bonus += 22
            elif rank_diff <= 5:
                rank_bonus += 14
            elif rank_diff <= 8:
                rank_bonus += 6
            elif rank_diff <= 10:
                rank_bonus -= 5    # too far apart
            else:
                rank_bonus -= 15   # large gap, not a compelling matchup

        # ── Prestige: title fights and high contenders ────────────────────
        if is_title_fight:
            rank_bonus += 35
        elif fighter1_rank == 0 or fighter2_rank == 0:
            rank_bonus += 20  # champion involved non-title

        # Top contender bonus
        ranks = [r for r in [fighter1_rank, fighter2_rank] if r is not None]
        top_rank = min(ranks) if ranks else None
        if top_rank == 1:
            rank_bonus += 12
        elif top_rank == 2:
            rank_bonus += 8
        elif top_rank is not None and top_rank <= 5:
            rank_bonus += 4

        # ── Record quality: combined experience adds legitimacy ────────────
        combined_fights = (fighter1_wins + fighter1_losses +
                           fighter2_wins + fighter2_losses)
        if combined_fights >= 20:   record_bonus = 5.0
        elif combined_fights >= 12: record_bonus = 3.0
        elif combined_fights >= 6:  record_bonus = 1.0
        else:                       record_bonus = 0.0

        # ── Penalty: ranked vs unranked ────────────────────────────────────
        rank_penalty = 0.0
        if one_ranked and not is_title_fight:
            ranked_rank = fighter1_rank if f1_ranked else fighter2_rank
            if ranked_rank is not None and ranked_rank <= 5:
                rank_penalty = -50   # top 5 vs unranked: prelim only
            elif ranked_rank is not None and ranked_rank <= 10:
                rank_penalty = -35
            else:
                rank_penalty = -20

        # ── Rivalry bonus ──────────────────────────────────────────────────
        rivalry_bonus = 12.0 if is_rivalry else 0.0

        total = base_score + rank_bonus + rank_penalty + record_bonus + rivalry_bonus
        return max(0.0, min(130.0, total))
    
    def assign_slot(
        self,
        event_name: str,
        weeks_until: int,
        matchup_score: float,
        is_title_fight: bool,
        combined_rating: int = 0,
        min_slot: Optional[CardSlot] = None,
    ) -> Tuple[CardSlot, bool]:
        """
        Assign a card slot for a fight.
        min_slot: Hard floor — fight will never go below this slot.
        """
        state = self.get_or_create_card_state(event_name, weeks_until)

        # Title fights ALWAYS get headline placement — Ship CB2: explicit
        # never-prelim guarantee. Title cascade ME → CO_MAIN → MAIN_CARD;
        # 3rd+ title fight on a card stays at MAIN_CARD (overflowing the
        # 3-cap if needed) but NEVER falls to prelim/early-prelim.
        if is_title_fight:
            if state.main_event_available:
                state.add_fight(CardSlot.MAIN_EVENT)
                state.has_title_fight = True
                return CardSlot.MAIN_EVENT, True
            elif state.co_main_available:
                state.add_fight(CardSlot.CO_MAIN)
                return CardSlot.CO_MAIN, True
            else:
                # 3rd+ title fight — stays on card as MAIN_CARD,
                # never goes to prelim or early-prelim.
                state.add_fight(CardSlot.MAIN_CARD)
                return CardSlot.MAIN_CARD, True

        # Non-title fights: assign by score with optional floor
        target_slot = self._get_target_slot_by_score(matchup_score)
        assigned_slot = self._find_available_slot(state, target_slot, min_slot=min_slot)

        state.add_fight(assigned_slot)
        is_headline = assigned_slot in (CardSlot.MAIN_EVENT, CardSlot.CO_MAIN)
        return assigned_slot, is_headline
    
    def _get_target_slot_by_score(self, score: float) -> CardSlot:
        """Determine target slot based on matchup score.
        Ship CB2: very-low-score fights (<35) target EARLY_PRELIM
        so they don't crowd ranked PRELIM matchups."""
        if score >= SCORE_THRESHOLDS[CardSlot.MAIN_EVENT]:
            return CardSlot.MAIN_EVENT
        elif score >= SCORE_THRESHOLDS[CardSlot.CO_MAIN]:
            return CardSlot.CO_MAIN
        elif score >= SCORE_THRESHOLDS[CardSlot.MAIN_CARD]:
            return CardSlot.MAIN_CARD
        elif score >= SCORE_THRESHOLDS[CardSlot.PRELIM]:
            return CardSlot.PRELIM
        else:
            return CardSlot.EARLY_PRELIM
    
    def _find_available_slot(
        self, 
        state: EventCardState, 
        target: CardSlot,
        min_slot: Optional[CardSlot] = None,
    ) -> CardSlot:
        """
        Find an available slot, falling back to lower slots if needed.
        min_slot: Never fall below this slot (hard floor for top contenders).
        """
        # Define fallback order — Ship CB2: EARLY_PRELIM included so the
        # cascade reaches it instead of overflowing PRELIM past its cap.
        slot_priority = [
            CardSlot.MAIN_EVENT,
            CardSlot.CO_MAIN,
            CardSlot.MAIN_CARD,
            CardSlot.PRELIM,
            CardSlot.EARLY_PRELIM,
        ]

        # Hard floor index — don't fall below this
        if min_slot and min_slot in slot_priority:
            floor_idx = slot_priority.index(min_slot)
        else:
            floor_idx = len(slot_priority) - 1  # No floor = can fall to prelim

        # Find target index
        try:
            start_idx = slot_priority.index(target)
        except ValueError:
            start_idx = len(slot_priority) - 1

        # Try target and below, but never go below floor
        for slot in slot_priority[start_idx:floor_idx + 1]:
            if state.is_slot_available(slot):
                return slot

        # Floor slot is full too — return it anyway (better than prelim for contenders)
        if min_slot and not state.is_slot_available(min_slot):
            # Try below floor as last resort
            for slot in slot_priority[floor_idx + 1:]:
                if state.is_slot_available(slot):
                    return slot

        # If nothing available, force into prelims
        return CardSlot.PRELIM
    
    def find_best_event_for_fight(
        self,
        events: List[Tuple[str, int]],  # (event_name, weeks_until)
        matchup_score: float,
        is_title_fight: bool
    ) -> Optional[str]:
        """
        Find the best event for a high-profile fight.
        
        For title fights and main event caliber fights, finds an event
        where they can get an appropriate slot.
        
        Args:
            events: List of (event_name, weeks_until) tuples
            matchup_score: The fight's matchup score
            is_title_fight: Whether this is a title fight
            
        Returns:
            Event name that has room, or None if no suitable event
        """
        target_slot = CardSlot.MAIN_EVENT if is_title_fight else self._get_target_slot_by_score(matchup_score)
        
        for event_name, weeks_until in events:
            state = self.get_or_create_card_state(event_name, weeks_until)
            
            if state.is_full:
                continue
            
            # For title fights, need main event or co-main available
            if is_title_fight:
                if state.main_event_available or state.co_main_available:
                    return event_name
            else:
                # For non-title, just need room in target or lower slot
                if state.is_slot_available(target_slot):
                    return event_name
                # Check if any lower slot is available
                for slot in [CardSlot.CO_MAIN, CardSlot.MAIN_CARD, CardSlot.PRELIM]:
                    if SLOT_ORDER[slot] >= SLOT_ORDER[target_slot]:
                        if state.is_slot_available(slot):
                            return event_name
        
        return None
    
    def clear_event(self, event_name: str) -> None:
        """Clear state for a completed event"""
        if event_name in self._card_states:
            del self._card_states[event_name]
    
    def decrement_weeks(self) -> None:
        """Decrement weeks_until for all tracked events"""
        for state in self._card_states.values():
            state.weeks_until = max(0, state.weeks_until - 1)
    
    def get_card_summary(self, event_name: str) -> Dict[str, int]:
        """Get slot counts for an event"""
        if event_name not in self._card_states:
            return {
                "main_event": 0,
                "co_main": 0,
                "main_card": 0,
                "prelim": 0,
                "early_prelim": 0,
                "total": 0,
            }
        
        state = self._card_states[event_name]
        return {
            "main_event": state.main_event_count,
            "co_main": state.co_main_count,
            "main_card": state.main_card_count,
            "prelim": state.prelim_count,
            "early_prelim": state.early_prelim_count,
            "total": state.total_fights,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for saving"""
        return {
            "card_states": {
                name: state.to_dict() 
                for name, state in self._card_states.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CardBuilder":
        """Deserialize state"""
        builder = cls()
        for name, state_data in data.get("card_states", {}).items():
            builder._card_states[name] = EventCardState.from_dict(state_data)
        return builder


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_slot_display_name(slot: CardSlot) -> str:
    """Get display name for a card slot"""
    names = {
        CardSlot.MAIN_EVENT: "MAIN EVENT",
        CardSlot.CO_MAIN: "CO-MAIN EVENT",
        CardSlot.MAIN_CARD: "MAIN CARD",
        CardSlot.PRELIM: "PRELIMS",
        CardSlot.EARLY_PRELIM: "EARLY PRELIMS",
    }
    return names.get(slot, "FIGHT")


def get_slot_short_name(slot: CardSlot) -> str:
    """Get short display name for a card slot"""
    names = {
        CardSlot.MAIN_EVENT: "MAIN",
        CardSlot.CO_MAIN: "CO-MAIN",
        CardSlot.MAIN_CARD: "MAIN CARD",
        CardSlot.PRELIM: "PRELIM",
        CardSlot.EARLY_PRELIM: "EARLY",
    }
    return names.get(slot, "FIGHT")


def get_slot_from_string(slot_str: str) -> CardSlot:
    """Convert string to CardSlot enum"""
    try:
        return CardSlot(slot_str)
    except ValueError:
        return CardSlot.PRELIM


def sort_fights_by_card_position(fights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort fights by card position (main event first, prelims last).
    
    Within each slot, sorts by combined rating (higher first).
    """
    def sort_key(fight: Dict[str, Any]) -> Tuple[int, int]:
        slot_str = fight.get("card_slot", "prelim")
        try:
            slot = CardSlot(slot_str)
            order = SLOT_ORDER[slot]
        except (ValueError, KeyError):
            order = 99
        
        # Secondary sort by combined rating (negative for descending)
        combined = fight.get("combined_rating", 0)
        if combined == 0:
            # Calculate from fighter data if not stored
            f1_rating = fight.get("fighter1_rating", 50)
            f2_rating = fight.get("fighter2_rating", 50)
            combined = f1_rating + f2_rating
        
        return (order, -combined)
    
    return sorted(fights, key=sort_key)


def group_fights_by_slot(
    fights: List[Dict[str, Any]]
) -> Dict[CardSlot, List[Dict[str, Any]]]:
    """
    Group fights by their card slot.
    
    Returns dict with CardSlot keys and lists of fights.
    """
    grouped: Dict[CardSlot, List[Dict[str, Any]]] = {
        CardSlot.MAIN_EVENT: [],
        CardSlot.CO_MAIN: [],
        CardSlot.MAIN_CARD: [],
        CardSlot.PRELIM: [],
        CardSlot.EARLY_PRELIM: [],
    }
    
    for fight in fights:
        slot_str = fight.get("card_slot", "early_prelim")
        slot = get_slot_from_string(slot_str)
        grouped[slot].append(fight)
    
    return grouped


def format_card_section(
    slot: CardSlot,
    fights: List[Dict[str, Any]],
    include_header: bool = True
) -> List[str]:
    """
    Format a section of the fight card for display.
    
    Returns list of formatted strings.
    """
    lines = []
    
    if not fights:
        return lines
    
    if include_header:
        header = get_slot_display_name(slot)
        lines.append(f"  === {header} ===")
    
    for fight in fights:
        f1_name = fight.get("fighter1_name", "TBD")
        f2_name = fight.get("fighter2_name", "TBD")
        wc = fight.get("weight_class", "")
        is_title = fight.get("is_title_fight", False)
        
        if is_title:
            lines.append(f"    [TITLE] {f1_name} vs {f2_name} ({wc})")
        else:
            lines.append(f"    {f1_name} vs {f2_name} ({wc})")
    
    return lines


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "CardSlot",
    
    # Classes
    "EventCardState",
    "CardBuilder",
    
    # Constants
    "SLOT_LIMITS",
    "SCORE_THRESHOLDS",
    "SLOT_ORDER",
    
    # Functions
    "get_slot_display_name",
    "get_slot_short_name",
    "get_slot_from_string",
    "sort_fights_by_card_position",
    "group_fights_by_slot",
    "format_card_section",
]
