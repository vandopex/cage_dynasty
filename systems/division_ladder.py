# systems/division_ladder.py
# Module: Division Ladder & Challenge System
# Lines: ~850
#
# Replaces passive fight offers with active division climbing.
# See the mountain, pick your path, climb.

"""
Cage Dynasty - Division Ladder System

Core features:
- Division ladder view showing all fighters and their status
- Player-initiated challenges with AI acceptance logic
- Incoming challenges from AI fighters
- Consequences for declining (reputation, rankings, popularity)
- Path to title visualization

USAGE:
    from systems.division_ladder import (
        DivisionLadder,
        LadderEntry,
        ChallengeResult,
        IncomingChallenge,
    )
"""

from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import random


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

# Challenge system settings
WEEKLY_CHALLENGE_LIMIT = 2  # Max challenges per fighter per week

class FighterStatus(Enum):
    """Status of a fighter on the ladder."""
    AVAILABLE = "available"
    BOOKED = "booked"           # Has scheduled fight
    INJURED = "injured"         # Out with injury
    COOLDOWN = "cooldown"       # Post-fight cooldown
    DECLINED = "declined"       # Recently declined your challenge
    CHAMPION = "champion"       # Special status for champ


class ChallengeOutcome(Enum):
    """Result of issuing a challenge."""
    ACCEPTED = "accepted"
    DECLINED_RANK = "declined_rank"         # "Fighting down"
    DECLINED_PRIDE = "declined_pride"       # You declined them before
    DECLINED_BUSY = "declined_busy"         # About to sign other fight
    DECLINED_RIVALRY = "declined_rivalry"   # Bad blood, wants bigger stage
    DECLINED_SCARED = "declined_scared"     # Actually ducking (rare)


# Decline messages by outcome
DECLINE_MESSAGES = {
    ChallengeOutcome.DECLINED_RANK: [
        "I'm not fighting down. Beat someone in the top 5 first.",
        "You want my spot? Earn it against someone else.",
        "Come back when you've got a real ranking.",
        "I've got bigger fish to fry.",
    ],
    ChallengeOutcome.DECLINED_PRIDE: [
        "You ducked me before. Now you want to fight? No thanks.",
        "Should've taken the fight when I offered.",
        "Funny how you want it now. Answer's no.",
    ],
    ChallengeOutcome.DECLINED_BUSY: [
        "Already in talks for another fight. Bad timing.",
        "Got something cooking. Maybe next time.",
        "My manager's working on something bigger.",
    ],
    ChallengeOutcome.DECLINED_RIVALRY: [
        "When we fight, it'll be for something bigger.",
        "I want that fight on a big card, not a random Tuesday.",
        "Let's build this up first. The fans deserve better.",
    ],
    ChallengeOutcome.DECLINED_SCARED: [
        "...no response from their camp.",
        "Their team is 'evaluating options' indefinitely.",
        "Suddenly unavailable. Interesting timing.",
    ],
}

# Accept messages
ACCEPT_MESSAGES = [
    "Let's do this. I've been waiting for a real challenge.",
    "You want it? You got it. Don't back out now.",
    "Finally, someone with guts. I accept.",
    "I'll fight anyone, anytime. You're on.",
    "This is the fight game. Let's fight.",
    "Your funeral. I accept.",
    "Been looking for a chance to prove myself. Let's go.",
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class LadderEntry:
    """A single entry on the division ladder."""
    fighter_id: str
    name: str
    nickname: str
    record: str                    # "12-3-0"
    record_with_kos: str           # "12(8)-3-0" 
    overall_rating: int
    rank: Optional[int]            # None = unranked, 0 = champion
    status: FighterStatus
    status_detail: str             # "vs #3 Chen (Wk 48)" or "Injured (4 wks)"
    is_player_fighter: bool
    camp_name: str
    win_streak: int
    lose_streak: int
    style: str                     # "Striker", "Wrestler", "Grappler", "Balanced"
    
    # For challenge logic
    personality: str = "Competitor"
    has_declined_you: bool = False  # They declined your challenge recently
    you_declined_them: bool = False # You declined their challenge recently
    
    @property
    def rank_display(self) -> str:
        """Get display string for rank."""
        if self.rank == 0:
            return "[C]"
        elif self.rank is None:
            return "UR"
        else:
            return f"#{self.rank}"
    
    @property
    def status_icon(self) -> str:
        """Get status icon."""
        icons = {
            FighterStatus.AVAILABLE: "âœ“",
            FighterStatus.BOOKED: "ðŸ”’",
            FighterStatus.INJURED: "ðŸ¥",
            FighterStatus.COOLDOWN: "â³",
            FighterStatus.DECLINED: "âŒ",
            FighterStatus.CHAMPION: "ðŸ‘‘",
        }
        return icons.get(self.status, "?")


@dataclass
class ChallengeOption:
    """A potential challenge the player can issue."""
    target: LadderEntry
    challenge_type: str            # "Step Up", "Lateral", "Defend", "Safe Win"
    accept_probability: float      # 0.0 to 1.0
    risk_reward: str               # "High Risk/High Reward", etc.
    ranking_impact: str            # "Win: #6 â†’ #4, Lose: #6 â†’ #7"


@dataclass 
class ChallengeResult:
    """Result of issuing a challenge."""
    accepted: bool
    outcome: ChallengeOutcome
    message: str
    
    # If accepted
    event_name: Optional[str] = None
    event_week: Optional[int] = None
    is_title_fight: bool = False
    
    # If declined
    suggested_alternative: Optional[str] = None  # Fighter ID of easier target


@dataclass
class IncomingChallenge:
    """A challenge from an AI fighter to a player's fighter."""
    challenge_id: str
    challenger_id: str
    challenger_name: str
    challenger_rank: Optional[int]
    challenger_record: str
    challenger_rating: int
    challenger_streak: str         # "2W" or "1L"
    
    target_id: str
    target_name: str
    
    weight_class: str
    week_issued: int
    
    message: str                   # Trash talk / call out
    expires_week: int              # Must respond by this week
    
    # Consequence preview
    decline_reputation_cost: int   # -5 to -15
    decline_ranking_freeze: int    # Weeks frozen if declined


@dataclass
class DeclineConsequence:
    """Consequences for declining a challenge."""
    reputation_loss: int
    popularity_loss: int  
    ranking_freeze_weeks: int
    narrative: str                 # News headline about ducking


@dataclass
class PendingChallenge:
    """A challenge that is pending resolution at end of week."""
    challenge_id: str
    challenger_id: str
    challenger_name: str
    challenger_rank: Optional[int]
    target_id: str
    target_name: str
    target_rank: Optional[int]
    weight_class: str
    week_issued: int
    accept_probability: float
    is_title_fight: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "challenger_id": self.challenger_id,
            "challenger_name": self.challenger_name,
            "challenger_rank": self.challenger_rank,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "target_rank": self.target_rank,
            "weight_class": self.weight_class,
            "week_issued": self.week_issued,
            "accept_probability": self.accept_probability,
            "is_title_fight": self.is_title_fight,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PendingChallenge":
        return cls(
            challenge_id=data["challenge_id"],
            challenger_id=data["challenger_id"],
            challenger_name=data["challenger_name"],
            challenger_rank=data.get("challenger_rank"),
            target_id=data["target_id"],
            target_name=data["target_name"],
            target_rank=data.get("target_rank"),
            weight_class=data["weight_class"],
            week_issued=data["week_issued"],
            accept_probability=data["accept_probability"],
            is_title_fight=data.get("is_title_fight", False),
        )


@dataclass
class ChallengeResolution:
    """Result of resolving a pending challenge at end of week."""
    challenge: PendingChallenge
    accepted: bool
    outcome: ChallengeOutcome
    message: str
    event_week: Optional[int] = None
    
    # For when player must choose between accepted challenges
    requires_player_choice: bool = False


# ============================================================================
# MAIN CLASS
# ============================================================================

class DivisionLadder:
    """
    Manages division ladder view and challenge system.
    
    Replaces passive fight offers with active challenge system.
    """
    
    def __init__(self):
        # Track challenge history
        self._challenges_issued: Dict[str, List[str]] = {}  # fighter_id -> [target_ids this week]
        self._challenges_declined_by_player: Dict[str, Set[str]] = {}  # fighter_id -> {challenger_ids}
        self._challenges_declined_by_ai: Dict[str, Set[str]] = {}  # fighter_id -> {target_ids}
        
        # Incoming challenges
        self._incoming_challenges: List[IncomingChallenge] = []
        
        # Pending challenges (resolve at end of week)
        self._pending_challenges: List[PendingChallenge] = []
        self._pending_challenge_counter: int = 0
        
        # Snubbed fighters (player accepted multiple, had to choose one)
        self._snubbed_fighters: Dict[str, Set[str]] = {}  # challenger_id -> {target_ids who were snubbed}
        
        # Reputation/ranking penalties
        self._ranking_freezes: Dict[str, int] = {}  # fighter_id -> weeks remaining
        self._decline_counts: Dict[str, int] = {}   # fighter_id -> times declined this month
        
        # Weekly limits
        self._challenges_this_week: Dict[str, int] = {}  # fighter_id -> count
    
    # -------------------------------------------------------------------------
    # LADDER BUILDING
    # -------------------------------------------------------------------------
    
    def build_ladder(
        self,
        weight_class: str,
        fighters: Dict[str, Any],
        fighter_data: Dict[str, Any],
        rankings_data: List[Tuple[int, str, str]],  # (rank, fighter_id, name) from rankings system
        injury_system: Any,
        scheduled_fights: List[Dict],
        cooldowns: Dict[str, int],
        player_camp_id: str,
        champion_id: Optional[str],
        camps: Dict[str, Any] = None,  # camp_id -> CampRecord for name lookup
    ) -> List[LadderEntry]:
        """
        Build the complete division ladder.
        
        Args:
            weight_class: Division name (e.g. "Lightweight")
            fighters: Dict of fighter_id -> fighter record
            fighter_data: Dict of fighter_id -> FighterFullData
            rankings_data: List of (rank, fighter_id, name) tuples from rankings system
                          rank 0 = champion, 1-15 = ranked
            injury_system: Injury system for checking injuries
            scheduled_fights: List of scheduled fight dicts
            cooldowns: Dict of fighter_id -> weeks remaining
            player_camp_id: ID of player's camp
            champion_id: ID of current champion (or None)
            camps: Dict of camp_id -> CampRecord for camp name lookup
        
        Returns:
            List of LadderEntry sorted by rank (champion first, then ranked, then unranked).
        """
        entries = []
        ranked_fighter_ids = set()
        camps = camps or {}
        
        # STEP 1: Build entries for all ranked fighters from rankings_data
        for rank, fid, fname in rankings_data:
            fighter = fighters.get(fid)
            if not fighter or not fighter.is_active:
                continue
            
            ranked_fighter_ids.add(fid)
            fdata = fighter_data.get(fid)
            
            entry = self._build_entry(
                fighter, fdata, rank, injury_system, 
                scheduled_fights, cooldowns, champion_id, player_camp_id, camps
            )
            entries.append(entry)
        
        # STEP 2: Add champion if not already in entries (fallback if rankings_data didn't include)
        if champion_id and champion_id not in ranked_fighter_ids:
            fighter = fighters.get(champion_id)
            if fighter and fighter.is_active:
                ranked_fighter_ids.add(champion_id)
                fdata = fighter_data.get(champion_id)
                entry = self._build_entry(
                    fighter, fdata, 0, injury_system,
                    scheduled_fights, cooldowns, champion_id, player_camp_id, camps
                )
                entries.append(entry)
        
        # STEP 3: Add all unranked fighters in this division
        div_fighters = [
            f for f in fighters.values()
            if f.weight_class == weight_class and f.is_active and f.fighter_id not in ranked_fighter_ids
        ]
        
        for fighter in div_fighters:
            fid = fighter.fighter_id
            fdata = fighter_data.get(fid)
            
            entry = self._build_entry(
                fighter, fdata, None, injury_system,
                scheduled_fights, cooldowns, champion_id, player_camp_id, camps
            )
            entries.append(entry)
        
        # Sort: Champion (0) -> Ranked (1-15) -> Unranked (by rating)
        def sort_key(e: LadderEntry):
            if e.rank == 0:  # Champion
                return (0, 0, -e.overall_rating)
            elif e.rank is not None:  # Ranked
                return (1, e.rank, -e.overall_rating)
            else:  # Unranked
                return (2, 999, -e.overall_rating)
        
        entries.sort(key=sort_key)
        return entries
    
    def _build_entry(
        self,
        fighter: Any,
        fdata: Any,
        rank: Optional[int],
        injury_system: Any,
        scheduled_fights: List[Dict],
        cooldowns: Dict[str, int],
        champion_id: Optional[str],
        player_camp_id: str,
        camps: Dict[str, Any] = None,
    ) -> LadderEntry:
        """Build a single ladder entry for a fighter."""
        fid = fighter.fighter_id
        camps = camps or {}
        
        # Determine status
        status, status_detail = self._get_fighter_status(
            fighter, fdata, injury_system, scheduled_fights, cooldowns, champion_id
        )
        
        # Build record strings
        wins, losses = fighter.wins, fighter.losses
        draws = getattr(fighter, 'draws', 0)
        ko_wins = getattr(fdata, 'ko_wins', 0) if fdata else 0
        sub_wins = getattr(fdata, 'sub_wins', 0) if fdata else 0
        finishes = ko_wins + sub_wins
        
        record = f"{wins}-{losses}-{draws}"
        record_with_kos = f"{wins}({finishes})-{losses}-{draws}"
        
        # Get streaks
        win_streak = getattr(fdata, 'win_streak', 0) if fdata else 0
        lose_streak = getattr(fdata, 'lose_streak', 0) if fdata else 0
        
        # Determine style (use fdata which has full attributes)
        style = self._determine_style(fdata) if fdata else "Balanced"
        
        # Check player ownership
        is_player = fighter.camp_id == player_camp_id
        
        # Get camp name from camps dict
        camp_name = "Unknown Gym"
        if fighter.camp_id and fighter.camp_id in camps:
            camp_record = camps[fighter.camp_id]
            camp_name = getattr(camp_record, 'name', 'Unknown Gym')
        
        # Get nickname
        nickname = getattr(fighter, 'nickname', '') or ''
        
        # Get personality
        personality = getattr(fdata, 'personality', 'Competitor') if fdata else 'Competitor'
        
        # Check decline history
        has_declined = fid in self._challenges_declined_by_ai.get(player_camp_id, set())
        you_declined = fid in self._challenges_declined_by_player.get(player_camp_id, set())
        
        return LadderEntry(
            fighter_id=fid,
            name=fighter.name,
            nickname=nickname,
            record=record,
            record_with_kos=record_with_kos,
            overall_rating=fighter.overall_rating,
            rank=rank,
            status=status,
            status_detail=status_detail,
            is_player_fighter=is_player,
            camp_name=camp_name,
            win_streak=win_streak,
            lose_streak=lose_streak,
            style=style,
            personality=personality,
            has_declined_you=has_declined,
            you_declined_them=you_declined,
        )
    
    def _get_fighter_status(
        self,
        fighter: Any,
        fighter_data: Any,
        injury_system: Any,
        scheduled_fights: List[Dict],
        cooldowns: Dict[str, int],
        champion_id: Optional[str],
    ) -> Tuple[FighterStatus, str]:
        """Determine fighter's availability status."""
        fid = fighter.fighter_id
        
        # Check if champion
        if champion_id and fid == champion_id:
            # Check if champ has scheduled defense
            for fight in scheduled_fights:
                if fight.get("fighter1_id") == fid or fight.get("fighter2_id") == fid:
                    opp_name = fight.get("fighter2_name") if fight.get("fighter1_id") == fid else fight.get("fighter1_name")
                    week = fight.get("weeks_until", 0) + fight.get("current_week", 0)
                    return FighterStatus.BOOKED, f"vs {opp_name} (Wk {week})"
            return FighterStatus.CHAMPION, "Awaiting challenger"
        
        # Check injury
        if injury_system:
            try:
                injury = injury_system.get_fighter_injury(fid)
                if injury and injury.weeks_remaining > 0:
                    return FighterStatus.INJURED, f"Injured ({injury.weeks_remaining} wks)"
            except:
                pass
        
        # Check scheduled fights
        for fight in scheduled_fights:
            if fight.get("fighter1_id") == fid or fight.get("fighter2_id") == fid:
                opp_name = fight.get("fighter2_name") if fight.get("fighter1_id") == fid else fight.get("fighter1_name")
                opp_id = fight.get("fighter2_id") if fight.get("fighter1_id") == fid else fight.get("fighter1_id")
                week = fight.get("weeks_until", 0)
                
                # Try to get opponent rank
                opp_rank = ""
                return FighterStatus.BOOKED, f"vs {opp_name} (Wk {week})"
        
        # Check cooldown
        if fid in cooldowns and cooldowns[fid] > 0:
            return FighterStatus.COOLDOWN, f"Cooldown ({cooldowns[fid]} wks)"
        
        return FighterStatus.AVAILABLE, "Available"
    
    def _determine_style(self, fighter: Any) -> str:
        """Determine fighter's primary style based on FighterFullData attributes."""
        if not fighter:
            return "Balanced"
        
        striking = (
            getattr(fighter, 'boxing', 50) + 
            getattr(fighter, 'kicks', 50) +
            getattr(fighter, 'striking_defense', 50)
        ) / 3
        
        wrestling = (
            getattr(fighter, 'takedowns', 50) +
            getattr(fighter, 'takedown_defense', 50) +
            getattr(fighter, 'top_control', 50)
        ) / 3
        
        grappling = (
            getattr(fighter, 'submissions', 50) +
            getattr(fighter, 'guard', 50)
        ) / 2
        
        scores = {
            "Striker": striking,
            "Wrestler": wrestling,
            "Grappler": grappling,
        }
        
        best = max(scores, key=scores.get)
        best_score = scores[best]
        
        # Check if balanced (all within 10 points)
        if max(scores.values()) - min(scores.values()) < 10:
            return "Balanced"
        
        return best
    
    # -------------------------------------------------------------------------
    # CHALLENGE LOGIC
    # -------------------------------------------------------------------------
    
    def get_challenge_options(
        self,
        player_fighter: LadderEntry,
        ladder: List[LadderEntry],
        week: int,
    ) -> List[ChallengeOption]:
        """
        Get available challenge options for a player's fighter.
        
        Returns fighters who are AVAILABLE and can be challenged.
        """
        options = []
        player_rank = player_fighter.rank
        
        # Check weekly limit
        challenges_used = self._challenges_this_week.get(player_fighter.fighter_id, 0)
        if challenges_used >= WEEKLY_CHALLENGE_LIMIT:
            return []  # Used all challenges this week
        
        for entry in ladder:
            # Skip self
            if entry.fighter_id == player_fighter.fighter_id:
                continue
            
            # Skip unavailable
            if entry.status != FighterStatus.AVAILABLE:
                continue
            
            # Skip other player fighters (can't fight your own guys)
            if entry.is_player_fighter:
                continue
            
            # Determine challenge type
            challenge_type = self._get_challenge_type(player_rank, entry.rank)
            
            # Calculate acceptance probability
            accept_prob = self._calculate_acceptance_probability(
                player_fighter, entry, week
            )
            
            # Determine risk/reward
            risk_reward = self._get_risk_reward(player_rank, entry.rank, entry.overall_rating, player_fighter.overall_rating)
            
            # Calculate ranking impact
            ranking_impact = self._get_ranking_impact(player_rank, entry.rank)
            
            option = ChallengeOption(
                target=entry,
                challenge_type=challenge_type,
                accept_probability=accept_prob,
                risk_reward=risk_reward,
                ranking_impact=ranking_impact,
            )
            options.append(option)
        
        # Sort by rank (higher ranked = better opportunity)
        options.sort(key=lambda o: (o.target.rank if o.target.rank else 999))
        
        return options
    
    def _get_challenge_type(
        self, 
        player_rank: Optional[int], 
        target_rank: Optional[int]
    ) -> str:
        """Determine the type of challenge."""
        # Handle champion
        if target_rank == 0:
            return "Title Shot"
        
        if player_rank is None:
            # Unranked challenging ranked
            return "Debut" if target_rank and target_rank >= 10 else "Step Up"
        
        if target_rank is None:
            return "Safe Win"
        
        diff = player_rank - target_rank  # Positive = challenging up
        
        if diff >= 3:
            return "Big Step Up"
        elif diff >= 1:
            return "Step Up"
        elif diff == 0:
            return "Lateral"
        elif diff >= -2:
            return "Defend"
        else:
            return "Safe Win"
    
    def _calculate_acceptance_probability(
        self,
        challenger: LadderEntry,
        target: LadderEntry,
        week: int,
    ) -> float:
        """
        Calculate probability that AI fighter accepts challenge.
        
        Key principle: Lower ranked fighters are MORE likely to accept.
        """
        base_prob = 0.50
        
        challenger_rank = challenger.rank if challenger.rank else 20
        target_rank = target.rank if target.rank else 20
        
        # Champion special case
        if target_rank == 0:
            # Champions only accept from top 5
            if challenger_rank is None or challenger_rank > 5:
                return 0.0
            return 0.80  # Champions generally defend
        
        # Rank-based modifier
        rank_diff = challenger_rank - target_rank  # Positive = challenger is lower ranked
        
        if rank_diff > 0:
            # Challenger is LOWER ranked (target fighting down)
            # Target less likely to accept
            base_prob -= rank_diff * 0.05
        else:
            # Challenger is HIGHER ranked (target fighting up)  
            # Target MORE likely to accept - step up opportunity!
            base_prob += abs(rank_diff) * 0.08
        
        # Bottom of rankings bonus (desperate for opportunity)
        if target_rank and target_rank >= 10:
            base_prob += 0.15
        
        # Unranked fighters accept almost anything from ranked
        if target.rank is None and challenger.rank is not None:
            base_prob += 0.25
        
        # Personality modifiers
        personality_mods = {
            "Journeyman": 0.20,
            "Competitor": 0.05,
            "Glory Seeker": -0.10,
            "Gate Keeper": 0.15,
            "Veteran": 0.10,
            "Prospect": 0.05,
        }
        base_prob += personality_mods.get(target.personality, 0)
        
        # Streak modifiers
        if target.lose_streak >= 2:
            base_prob += 0.15  # Need a win, more open
        if target.win_streak >= 3:
            base_prob -= 0.10  # Feeling selective
        
        # Pride modifier - you declined them before
        if target.you_declined_them:
            base_prob -= 0.25  # They remember
        
        # Clamp
        return max(0.05, min(0.99, base_prob))
    
    def _get_risk_reward(
        self,
        player_rank: Optional[int],
        target_rank: Optional[int],
        target_rating: int,
        player_rating: int,
    ) -> str:
        """Get risk/reward assessment."""
        rating_diff = target_rating - player_rating
        
        if target_rank == 0:
            return "Championship Stakes"
        
        if rating_diff >= 10:
            return "High Risk / High Reward"
        elif rating_diff >= 5:
            return "Moderate Risk / Good Reward"
        elif rating_diff >= -5:
            return "Even Matchup"
        elif rating_diff >= -10:
            return "Favorable / Low Reward"
        else:
            return "Safe Win / Minimal Reward"
    
    def _get_ranking_impact(
        self,
        player_rank: Optional[int],
        target_rank: Optional[int],
    ) -> str:
        """Estimate ranking impact of win/loss."""
        if target_rank == 0:
            return "Win: Become Champion!"
        
        if player_rank is None:
            if target_rank and target_rank <= 15:
                return f"Win: Enter rankings (~#{target_rank + 1})"
            return "Win: Build record"
        
        if target_rank is None:
            return f"Win: Stay #{player_rank}, Lose: Drop"
        
        # Simplified ranking prediction
        if player_rank > target_rank:
            # Challenging up
            win_rank = max(1, target_rank + 1)
            lose_rank = min(15, player_rank + 1)
            return f"Win: #{player_rank}â†’#{win_rank}, Lose: â†’#{lose_rank}"
        else:
            # Defending/lateral
            win_rank = player_rank
            lose_rank = min(15, player_rank + 2)
            return f"Win: Hold #{player_rank}, Lose: â†’#{lose_rank}"
    
    def issue_challenge(
        self,
        challenger_id: str,
        target_id: str,
        challenger_entry: LadderEntry,
        target_entry: LadderEntry,
        accept_probability: float,
        week: int,
        event_name: str = "DFC Fight Night",
    ) -> ChallengeResult:
        """
        Issue a challenge from player's fighter to target.
        
        Now queues challenge for resolution at end of week instead of
        resolving immediately. This allows fighter to receive multiple
        offers and choose the best one.
        
        Returns result indicating challenge is pending.
        """
        # Check weekly limit
        challenges_used = self._challenges_this_week.get(challenger_id, 0)
        if challenges_used >= WEEKLY_CHALLENGE_LIMIT:
            return ChallengeResult(
                accepted=False,
                outcome=ChallengeOutcome.DECLINED_BUSY,
                message=f"You've used all {WEEKLY_CHALLENGE_LIMIT} challenges this week.",
            )
        
        # Check if target already has pending challenge from this challenger
        for pending in self._pending_challenges:
            if pending.challenger_id == challenger_id and pending.target_id == target_id:
                return ChallengeResult(
                    accepted=False,
                    outcome=ChallengeOutcome.DECLINED_BUSY,
                    message="You already have a pending challenge to this fighter.",
                )
        
        # Check if target already has a pending challenge (can only accept one)
        # Note: We allow multiple pending TO same target - they'll pick one at resolution
        
        # Record the attempt count
        self._challenges_this_week[challenger_id] = challenges_used + 1
        
        # Create pending challenge
        self._pending_challenge_counter += 1
        challenge_id = f"pending_{self._pending_challenge_counter}_{week}"
        
        is_title = target_entry.rank == 0
        
        pending = PendingChallenge(
            challenge_id=challenge_id,
            challenger_id=challenger_id,
            challenger_name=challenger_entry.name,
            challenger_rank=challenger_entry.rank,
            target_id=target_id,
            target_name=target_entry.name,
            target_rank=target_entry.rank,
            weight_class=target_entry.camp_name,  # We'll fix this in CLI
            week_issued=week,
            accept_probability=accept_probability,
            is_title_fight=is_title,
        )
        self._pending_challenges.append(pending)
        
        # Return pending status
        return ChallengeResult(
            accepted=True,  # True means "successfully sent", not "accepted by fighter"
            outcome=ChallengeOutcome.ACCEPTED,  # Will be re-evaluated at week end
            message="Challenge sent! Response will come at end of week.",
            event_name=event_name,
            event_week=None,  # Will be set at resolution
            is_title_fight=is_title,
        )
    
    def resolve_pending_challenges(self, week: int) -> List[ChallengeResolution]:
        """
        Resolve all pending challenges at end of week.
        
        Each target fighter evaluates all offers they received and picks
        the best one (or declines all).
        
        Returns list of resolutions for display to player.
        """
        resolutions = []
        
        if not self._pending_challenges:
            return resolutions
        
        # Group challenges by target fighter
        by_target: Dict[str, List[PendingChallenge]] = {}
        for challenge in self._pending_challenges:
            if challenge.target_id not in by_target:
                by_target[challenge.target_id] = []
            by_target[challenge.target_id].append(challenge)
        
        # Resolve each target's offers
        for target_id, offers in by_target.items():
            # For now, just process player's offers (AI offers handled separately)
            # Roll for each offer
            for challenge in offers:
                roll = random.random()
                accepted = roll < challenge.accept_probability
                
                if accepted:
                    # Schedule fight (6-8 weeks out)
                    fight_week = week + random.randint(6, 8)
                    message = random.choice(ACCEPT_MESSAGES)
                    
                    resolution = ChallengeResolution(
                        challenge=challenge,
                        accepted=True,
                        outcome=ChallengeOutcome.ACCEPTED,
                        message=message,
                        event_week=fight_week,
                    )
                else:
                    # Determine decline reason
                    outcome = self._determine_decline_reason_from_pending(challenge)
                    
                    # Track that they declined
                    if challenge.challenger_id not in self._challenges_declined_by_ai:
                        self._challenges_declined_by_ai[challenge.challenger_id] = set()
                    self._challenges_declined_by_ai[challenge.challenger_id].add(target_id)
                    
                    message = random.choice(DECLINE_MESSAGES.get(outcome, ["No response."]))
                    
                    resolution = ChallengeResolution(
                        challenge=challenge,
                        accepted=False,
                        outcome=outcome,
                        message=message,
                    )
                
                resolutions.append(resolution)
        
        # Clear pending challenges
        self._pending_challenges = []
        
        return resolutions
    
    def _determine_decline_reason_from_pending(
        self,
        challenge: PendingChallenge,
    ) -> ChallengeOutcome:
        """Determine why a pending challenge was declined."""
        # Check rank difference
        c_rank = challenge.challenger_rank if challenge.challenger_rank else 20
        t_rank = challenge.target_rank if challenge.target_rank else 20
        
        if c_rank > t_rank + 3:
            return ChallengeOutcome.DECLINED_RANK
        
        # Low accept prob = scared
        if challenge.accept_probability < 0.20:
            return ChallengeOutcome.DECLINED_SCARED
        
        # Random between busy and other
        return random.choice([
            ChallengeOutcome.DECLINED_BUSY,
            ChallengeOutcome.DECLINED_RANK,
        ])
    
    def get_pending_challenges_for_fighter(self, fighter_id: str) -> List[PendingChallenge]:
        """Get all pending challenges issued by a fighter."""
        return [c for c in self._pending_challenges if c.challenger_id == fighter_id]
    
    def get_all_pending_challenges(self) -> List[PendingChallenge]:
        """Get all pending challenges."""
        return self._pending_challenges.copy()
    
    def record_snub(self, challenger_id: str, snubbed_target_id: str) -> None:
        """
        Record when a player had to choose between accepted challenges,
        leaving one fighter 'snubbed'. Creates minor rivalry seed.
        """
        if challenger_id not in self._snubbed_fighters:
            self._snubbed_fighters[challenger_id] = set()
        self._snubbed_fighters[challenger_id].add(snubbed_target_id)
    
    def was_snubbed_by(self, fighter_id: str, potential_snubber_id: str) -> bool:
        """Check if fighter was previously snubbed by another fighter."""
        return fighter_id in self._snubbed_fighters.get(potential_snubber_id, set())
    
    def _determine_decline_reason(
        self,
        challenger: LadderEntry,
        target: LadderEntry,
        accept_prob: float,
    ) -> ChallengeOutcome:
        """Determine why a challenge was declined."""
        # Check if pride issue
        if target.you_declined_them:
            return ChallengeOutcome.DECLINED_PRIDE
        
        # Check rank difference
        c_rank = challenger.rank if challenger.rank else 20
        t_rank = target.rank if target.rank else 20
        
        if c_rank > t_rank + 3:
            return ChallengeOutcome.DECLINED_RANK
        
        # Low accept prob = scared
        if accept_prob < 0.20:
            return ChallengeOutcome.DECLINED_SCARED
        
        # Random between busy and other
        return random.choice([
            ChallengeOutcome.DECLINED_BUSY,
            ChallengeOutcome.DECLINED_RANK,
        ])
    
    # -------------------------------------------------------------------------
    # INCOMING CHALLENGES
    # -------------------------------------------------------------------------
    
    def generate_incoming_challenges(
        self,
        player_fighters: List[LadderEntry],
        ladder: List[LadderEntry],
        week: int,
    ) -> List[IncomingChallenge]:
        """
        Generate incoming challenges from AI fighters.
        
        AI fighters will challenge player fighters who are:
        - Within 3 ranks above them
        - Available
        - Not already being challenged
        """
        challenges = []
        
        for player_entry in player_fighters:
            # Skip if player fighter is unavailable
            if player_entry.status != FighterStatus.AVAILABLE:
                continue
            
            # Find potential challengers (AI fighters below who want to move up)
            for ai_entry in ladder:
                # Skip player fighters
                if ai_entry.is_player_fighter:
                    continue
                
                # Skip unavailable
                if ai_entry.status != FighterStatus.AVAILABLE:
                    continue
                
                # Check if AI is below player and within range
                if not self._should_ai_challenge(ai_entry, player_entry):
                    continue
                
                # Random chance to issue challenge
                challenge_chance = self._get_ai_challenge_chance(ai_entry, player_entry)
                if random.random() > challenge_chance:
                    continue
                
                # Generate the challenge
                challenge = self._create_incoming_challenge(
                    ai_entry, player_entry, week
                )
                challenges.append(challenge)
                break  # Only one incoming challenge per player fighter per week
        
        self._incoming_challenges.extend(challenges)
        return challenges
    
    def _should_ai_challenge(
        self,
        ai: LadderEntry,
        player: LadderEntry,
    ) -> bool:
        """Check if AI should consider challenging player."""
        ai_rank = ai.rank if ai.rank else 20
        player_rank = player.rank if player.rank else 20
        
        # AI only challenges UP (to fighters ranked higher)
        if ai_rank <= player_rank:
            return False
        
        # Within 5 ranks
        if ai_rank - player_rank > 5:
            return False
        
        # Don't challenge champion unless top 5
        if player_rank == 0 and ai_rank > 5:
            return False
        
        return True
    
    def _get_ai_challenge_chance(
        self,
        ai: LadderEntry,
        player: LadderEntry,
    ) -> float:
        """Get probability AI issues challenge this week."""
        base = 0.15  # 15% base chance per week
        
        # Streak modifiers
        if ai.win_streak >= 2:
            base += 0.10  # Confident
        if ai.lose_streak >= 2:
            base -= 0.05  # Less aggressive
        
        # Personality
        personality_mods = {
            "Glory Seeker": 0.15,
            "Competitor": 0.05,
            "Journeyman": -0.05,
        }
        base += personality_mods.get(ai.personality, 0)
        
        # You declined them before - revenge!
        if ai.you_declined_them:
            base += 0.20
        
        return max(0.05, min(0.40, base))
    
    def _create_incoming_challenge(
        self,
        challenger: LadderEntry,
        target: LadderEntry,
        week: int,
    ) -> IncomingChallenge:
        """Create an incoming challenge."""
        import uuid
        
        # Generate call-out message
        messages = [
            f"I've been watching {target.name}. I know I can beat them.",
            f"Time to prove I belong in the top {target.rank or 10}!",
            f"{target.name} is ducking the real competition. Fight me!",
            f"I'm coming for that spot. {target.name}, let's do this!",
            f"Everyone's scared of me. {target.name}, don't be next.",
        ]
        
        # Streak display
        if challenger.win_streak > 0:
            streak = f"{challenger.win_streak}W"
        elif challenger.lose_streak > 0:
            streak = f"{challenger.lose_streak}L"
        else:
            streak = "0"
        
        # Calculate consequences for declining
        rank_diff = (target.rank or 20) - (challenger.rank or 20)
        rep_cost = min(15, max(5, 5 + abs(rank_diff)))
        freeze_weeks = 2 if rank_diff <= 2 else 1
        
        return IncomingChallenge(
            challenge_id=str(uuid.uuid4())[:8],
            challenger_id=challenger.fighter_id,
            challenger_name=challenger.name,
            challenger_rank=challenger.rank,
            challenger_record=challenger.record,
            challenger_rating=challenger.overall_rating,
            challenger_streak=streak,
            target_id=target.fighter_id,
            target_name=target.name,
            weight_class="",  # Set by caller
            week_issued=week,
            message=random.choice(messages),
            expires_week=week + 2,
            decline_reputation_cost=rep_cost,
            decline_ranking_freeze=freeze_weeks,
        )
    
    def respond_to_challenge(
        self,
        challenge: IncomingChallenge,
        accepted: bool,
        week: int,
    ) -> Tuple[bool, Optional[DeclineConsequence]]:
        """
        Respond to an incoming challenge.
        
        Returns: (success, decline_consequence if declined)
        """
        # Remove from pending
        self._incoming_challenges = [
            c for c in self._incoming_challenges 
            if c.challenge_id != challenge.challenge_id
        ]
        
        if accepted:
            return True, None
        
        # Apply decline consequences
        target_id = challenge.target_id
        
        # Track that player declined this AI
        if target_id not in self._challenges_declined_by_player:
            self._challenges_declined_by_player[target_id] = set()
        self._challenges_declined_by_player[target_id].add(challenge.challenger_id)
        
        # Apply ranking freeze
        self._ranking_freezes[target_id] = challenge.decline_ranking_freeze
        
        # Track decline count
        self._decline_counts[target_id] = self._decline_counts.get(target_id, 0) + 1
        
        consequence = DeclineConsequence(
            reputation_loss=challenge.decline_reputation_cost,
            popularity_loss=challenge.decline_reputation_cost // 2,
            ranking_freeze_weeks=challenge.decline_ranking_freeze,
            narrative=f"{challenge.target_name} accused of ducking {challenge.challenger_name}",
        )
        
        return False, consequence
    
    def get_pending_challenges(self, fighter_id: str) -> List[IncomingChallenge]:
        """Get pending incoming challenges for a fighter."""
        return [c for c in self._incoming_challenges if c.target_id == fighter_id]
    
    # -------------------------------------------------------------------------
    # WEEKLY PROCESSING
    # -------------------------------------------------------------------------
    
    def process_week(self, week: int) -> Dict[str, Any]:
        """
        Process weekly updates.
        
        - Reset challenge limits
        - Expire old challenges
        - Decrement ranking freezes
        """
        results = {
            "expired_challenges": [],
            "freezes_expired": [],
        }
        
        # Reset weekly challenge limits
        self._challenges_this_week = {}
        
        # Expire old incoming challenges
        expired = [c for c in self._incoming_challenges if c.expires_week <= week]
        for challenge in expired:
            results["expired_challenges"].append(challenge.challenger_name)
            # Auto-decline has lighter consequences
            if challenge.target_id not in self._challenges_declined_by_player:
                self._challenges_declined_by_player[challenge.target_id] = set()
            self._challenges_declined_by_player[challenge.target_id].add(challenge.challenger_id)
        
        self._incoming_challenges = [
            c for c in self._incoming_challenges if c.expires_week > week
        ]
        
        # Decrement ranking freezes
        for fid in list(self._ranking_freezes.keys()):
            self._ranking_freezes[fid] -= 1
            if self._ranking_freezes[fid] <= 0:
                del self._ranking_freezes[fid]
                results["freezes_expired"].append(fid)
        
        return results
    
    def is_ranking_frozen(self, fighter_id: str) -> bool:
        """Check if fighter's ranking is frozen due to declining."""
        return fighter_id in self._ranking_freezes
    
    # -------------------------------------------------------------------------
    # SERIALIZATION
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "challenges_issued": self._challenges_issued,
            "challenges_declined_by_player": {
                k: list(v) for k, v in self._challenges_declined_by_player.items()
            },
            "challenges_declined_by_ai": {
                k: list(v) for k, v in self._challenges_declined_by_ai.items()
            },
            "incoming_challenges": [
                {
                    "challenge_id": c.challenge_id,
                    "challenger_id": c.challenger_id,
                    "challenger_name": c.challenger_name,
                    "challenger_rank": c.challenger_rank,
                    "challenger_record": c.challenger_record,
                    "challenger_rating": c.challenger_rating,
                    "challenger_streak": c.challenger_streak,
                    "target_id": c.target_id,
                    "target_name": c.target_name,
                    "weight_class": c.weight_class,
                    "week_issued": c.week_issued,
                    "message": c.message,
                    "expires_week": c.expires_week,
                    "decline_reputation_cost": c.decline_reputation_cost,
                    "decline_ranking_freeze": c.decline_ranking_freeze,
                }
                for c in self._incoming_challenges
            ],
            "pending_challenges": [c.to_dict() for c in self._pending_challenges],
            "pending_challenge_counter": self._pending_challenge_counter,
            "snubbed_fighters": {
                k: list(v) for k, v in self._snubbed_fighters.items()
            },
            "ranking_freezes": self._ranking_freezes,
            "decline_counts": self._decline_counts,
            "challenges_this_week": self._challenges_this_week,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DivisionLadder":
        """Deserialize from dictionary."""
        ladder = cls()
        
        ladder._challenges_issued = data.get("challenges_issued", {})
        ladder._challenges_declined_by_player = {
            k: set(v) for k, v in data.get("challenges_declined_by_player", {}).items()
        }
        ladder._challenges_declined_by_ai = {
            k: set(v) for k, v in data.get("challenges_declined_by_ai", {}).items()
        }
        
        # Reconstruct incoming challenges
        for c_data in data.get("incoming_challenges", []):
            challenge = IncomingChallenge(
                challenge_id=c_data["challenge_id"],
                challenger_id=c_data["challenger_id"],
                challenger_name=c_data["challenger_name"],
                challenger_rank=c_data["challenger_rank"],
                challenger_record=c_data["challenger_record"],
                challenger_rating=c_data["challenger_rating"],
                challenger_streak=c_data["challenger_streak"],
                target_id=c_data["target_id"],
                target_name=c_data["target_name"],
                weight_class=c_data["weight_class"],
                week_issued=c_data["week_issued"],
                message=c_data["message"],
                expires_week=c_data["expires_week"],
                decline_reputation_cost=c_data["decline_reputation_cost"],
                decline_ranking_freeze=c_data["decline_ranking_freeze"],
            )
            ladder._incoming_challenges.append(challenge)
        
        # Reconstruct pending challenges
        for p_data in data.get("pending_challenges", []):
            pending = PendingChallenge.from_dict(p_data)
            ladder._pending_challenges.append(pending)
        
        ladder._pending_challenge_counter = data.get("pending_challenge_counter", 0)
        ladder._snubbed_fighters = {
            k: set(v) for k, v in data.get("snubbed_fighters", {}).items()
        }
        
        ladder._ranking_freezes = data.get("ranking_freezes", {})
        ladder._decline_counts = data.get("decline_counts", {})
        ladder._challenges_this_week = data.get("challenges_this_week", {})
        
        return ladder


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_path_to_title(
    player_entry: LadderEntry,
    ladder: List[LadderEntry],
) -> List[str]:
    """
    Calculate optimal path to title shot.
    
    Returns list of steps like ["Beat #4", "Beat #2", "Title Shot"]
    """
    path = []
    current_rank = player_entry.rank
    
    if current_rank is None:
        path.append("Enter rankings (beat ranked opponent)")
        current_rank = 15
    
    if current_rank == 0:
        return ["You are the champion!"]
    
    # Simplified path: need to reach top 5 for title shot
    if current_rank > 5:
        # Find available fighters to step up against
        steps_needed = (current_rank - 5) // 2 + 1
        path.append(f"Win {steps_needed} fights to reach top 5")
    
    path.append("Title Shot vs Champion")
    
    return path


def get_threat_assessment(
    player_entry: LadderEntry,
    ladder: List[LadderEntry],
) -> Optional[LadderEntry]:
    """
    Find the most likely fighter to challenge player.
    
    Returns the AI fighter most likely to issue a challenge.
    """
    player_rank = player_entry.rank if player_entry.rank else 20
    
    threats = []
    for entry in ladder:
        if entry.is_player_fighter:
            continue
        if entry.status != FighterStatus.AVAILABLE:
            continue
        
        entry_rank = entry.rank if entry.rank else 20
        
        # Only fighters below are threats
        if entry_rank <= player_rank:
            continue
        
        # Within striking distance
        if entry_rank - player_rank > 5:
            continue
        
        # Calculate threat score
        threat_score = 0
        threat_score += entry.win_streak * 2
        threat_score += 5 if entry.you_declined_them else 0
        threat_score += 3 if entry.personality == "Glory Seeker" else 0
        
        threats.append((entry, threat_score))
    
    if threats:
        threats.sort(key=lambda x: -x[1])
        return threats[0][0]
    
    return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "FighterStatus",
    "ChallengeOutcome",
    
    # Data classes
    "LadderEntry",
    "ChallengeOption",
    "ChallengeResult",
    "IncomingChallenge",
    "DeclineConsequence",
    "PendingChallenge",
    "ChallengeResolution",
    
    # Main class
    "DivisionLadder",
    
    # Helpers
    "get_path_to_title",
    "get_threat_assessment",
    
    # Constants
    "DECLINE_MESSAGES",
    "ACCEPT_MESSAGES",
]
