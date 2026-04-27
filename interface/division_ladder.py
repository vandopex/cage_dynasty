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
            FighterStatus.AVAILABLE: "✓",
            FighterStatus.BOOKED: "🔒",
            FighterStatus.INJURED: "🏥",
            FighterStatus.COOLDOWN: "⏳",
            FighterStatus.DECLINED: "❌",
            FighterStatus.CHAMPION: "👑",
        }
        return icons.get(self.status, "?")


@dataclass
class ChallengeOption:
    """A potential challenge the player can issue."""
    target: LadderEntry
    challenge_type: str            # "Step Up", "Lateral", "Defend", "Safe Win"
    accept_probability: float      # 0.0 to 1.0
    risk_reward: str               # "High Risk/High Reward", etc.
    ranking_impact: str            # "Win: #6 → #4, Lose: #6 → #7"


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
        rankings_system: Any,
        injury_system: Any,
        scheduled_fights: List[Dict],
        cooldowns: Dict[str, int],
        player_camp_id: str,
        division_state: Any,
    ) -> List[LadderEntry]:
        """
        Build the complete division ladder.
        
        Returns list of LadderEntry sorted by rank (champion first, then ranked, then unranked).
        """
        entries = []
        
        # Get all fighters in this division
        div_fighters = [
            f for f in fighters.values()
            if f.weight_class == weight_class and f.is_active
        ]
        
        # Get champion
        champion_id = division_state.champion_id if division_state else None
        
        # Build entries
        for fighter in div_fighters:
            fid = fighter.fighter_id
            fdata = fighter_data.get(fid)
            
            # Determine rank
            rank = self._get_fighter_rank(fighter, rankings_system, champion_id)
            
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
            
            # Determine style
            style = self._determine_style(fighter)
            
            # Check player ownership
            is_player = fighter.camp_id == player_camp_id
            
            # Get camp name
            camp_name = getattr(fighter, 'camp_name', 'Unknown Gym')
            
            # Get nickname
            nickname = getattr(fighter, 'nickname', '')
            
            # Get personality
            personality = getattr(fdata, 'personality', 'Competitor') if fdata else 'Competitor'
            
            # Check decline history
            has_declined = fid in self._challenges_declined_by_ai.get(player_camp_id, set())
            you_declined = fid in self._challenges_declined_by_player.get(player_camp_id, set())
            
            entry = LadderEntry(
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
    
    def _get_fighter_rank(
        self, 
        fighter: Any, 
        rankings_system: Any,
        champion_id: Optional[str]
    ) -> Optional[int]:
        """Get fighter's rank (0=champ, 1-15=ranked, None=unranked)."""
        if champion_id and fighter.fighter_id == champion_id:
            return 0
        
        if rankings_system:
            try:
                from core.types import WeightClass
                wc = WeightClass(fighter.weight_class)
                rankings_data = rankings_system.get_rankings(wc)
                for rank, fid, _ in rankings_data:
                    if fid == fighter.fighter_id and rank > 0:
                        return rank
            except:
                pass
        
        # Fallback: use ELO-lite to determine rank
        return None
    
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
        """Determine fighter's primary style."""
        striking = (
            getattr(fighter, 'boxing', 50) + 
            getattr(fighter, 'kicks', 50) +
            getattr(fighter, 'striking_defense', 50)
        ) / 3
        
        wrestling = (
            getattr(fighter, 'wrestling', 50) +
            getattr(fighter, 'takedown_defense', 50)
        ) / 2
        
        grappling = (
            getattr(fighter, 'bjj', 50) +
            getattr(fighter, 'submissions', 50)
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
        if challenges_used >= 1:
            return []  # Already challenged someone this week
        
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
            return f"Win: #{player_rank}→#{win_rank}, Lose: →#{lose_rank}"
        else:
            # Defending/lateral
            win_rank = player_rank
            lose_rank = min(15, player_rank + 2)
            return f"Win: Hold #{player_rank}, Lose: →#{lose_rank}"
    
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
        
        Returns result with accept/decline and details.
        """
        # Check weekly limit
        challenges_used = self._challenges_this_week.get(challenger_id, 0)
        if challenges_used >= 1:
            return ChallengeResult(
                accepted=False,
                outcome=ChallengeOutcome.DECLINED_BUSY,
                message="You've already issued a challenge this week.",
            )
        
        # Roll for acceptance
        roll = random.random()
        accepted = roll < accept_probability
        
        # Record the attempt
        self._challenges_this_week[challenger_id] = challenges_used + 1
        
        if accepted:
            # Schedule fight (6-8 weeks out)
            fight_week = week + random.randint(6, 8)
            
            # Check if title fight
            is_title = target_entry.rank == 0
            
            message = random.choice(ACCEPT_MESSAGES)
            
            return ChallengeResult(
                accepted=True,
                outcome=ChallengeOutcome.ACCEPTED,
                message=message,
                event_name=event_name,
                event_week=fight_week,
                is_title_fight=is_title,
            )
        else:
            # Determine decline reason
            outcome = self._determine_decline_reason(
                challenger_entry, target_entry, accept_probability
            )
            
            # Track that they declined
            if challenger_id not in self._challenges_declined_by_ai:
                self._challenges_declined_by_ai[challenger_id] = set()
            self._challenges_declined_by_ai[challenger_id].add(target_id)
            
            message = random.choice(DECLINE_MESSAGES.get(outcome, ["No response."]))
            
            # Find suggested alternative
            alternative = None  # Could implement: find next best option
            
            return ChallengeResult(
                accepted=False,
                outcome=outcome,
                message=message,
                suggested_alternative=alternative,
            )
    
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
    
    # Main class
    "DivisionLadder",
    
    # Helpers
    "get_path_to_title",
    "get_threat_assessment",
    
    # Constants
    "DECLINE_MESSAGES",
    "ACCEPT_MESSAGES",
]
