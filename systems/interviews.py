# systems/interviews.py
# Post-Fight Interview System
# Lines: ~650
#
# Fighters react to wins and losses, creating storylines and rivalries.
# Every choice has tradeoffs - no "always pick X" strategy.

"""
Cage Dynasty - Post-Fight Interview System

This module provides:
- Winner and loser interview responses with real consequences
- AI interview selection based on fighter personality
- Reputation tracking and trait emergence
- Call-out system with matchup probability boosts
- Rivalry creation and escalation from trash talk
- Motivation boosts for called-out/rival fighters
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto


# ============================================================================
# INTERVIEW RESPONSE TYPES
# ============================================================================

class WinnerResponse(Enum):
    """Responses available to fight winners"""
    HUMBLE = "humble"
    TRASH_TALK = "trash_talk"
    CALL_OUT = "call_out"
    RESPECTFUL = "respectful"
    EMOTIONAL = "emotional"
    THANK_SPONSORS = "thank_sponsors"


class LoserResponse(Enum):
    """Responses available to fight losers"""
    ACCEPT_DEFEAT = "accept_defeat"
    DEMAND_REMATCH = "demand_rematch"
    CITE_INJURY = "cite_injury"
    QUESTION_DECISION = "question_decision"
    RETIREMENT_HINT = "retirement_hint"
    BLAME_CAMP = "blame_camp"


class ReputationTrait(Enum):
    """Reputation traits that emerge from interview patterns"""
    NONE = "none"
    CLASS_ACT = "class_act"           # Consistently humble/respectful
    HEEL = "heel"                      # Consistent trash talker
    DRAMA_QUEEN = "drama_queen"        # Overuses emotional responses
    CRYBABY = "crybaby"               # Questions decisions repeatedly
    PROFESSIONAL = "professional"      # Consistently respectful
    COMPANY_MAN = "company_man"        # Too humble, seen as soft
    OBSESSED = "obsessed"             # Demands rematch too much vs same opponent


# ============================================================================
# INTERVIEW DATA STRUCTURES
# ============================================================================

@dataclass
class InterviewRecord:
    """Record of a single interview"""
    week: int
    fight_id: str
    opponent_id: str
    opponent_name: str
    was_winner: bool
    response: str  # Response enum value
    call_out_target_id: Optional[str] = None
    call_out_target_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "week": self.week,
            "fight_id": self.fight_id,
            "opponent_id": self.opponent_id,
            "opponent_name": self.opponent_name,
            "was_winner": self.was_winner,
            "response": self.response,
            "call_out_target_id": self.call_out_target_id,
            "call_out_target_name": self.call_out_target_name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewRecord":
        return cls(**data)


@dataclass
class InterviewHistory:
    """Complete interview history for a fighter"""
    fighter_id: str
    records: List[InterviewRecord] = field(default_factory=list)
    
    # Response counts for pattern detection
    humble_count: int = 0
    trash_talk_count: int = 0
    emotional_count: int = 0
    call_out_count: int = 0
    respectful_count: int = 0
    thank_sponsors_count: int = 0
    accept_defeat_count: int = 0
    demand_rematch_count: int = 0
    cite_injury_count: int = 0
    question_decision_count: int = 0
    retirement_hint_count: int = 0
    blame_camp_count: int = 0
    
    # Consecutive counts for penalty tracking
    consecutive_emotional: int = 0
    consecutive_humble: int = 0
    consecutive_question_decision: int = 0
    
    # Active effects
    current_call_out_target_id: Optional[str] = None
    current_call_out_target_name: Optional[str] = None
    retirement_hinted: bool = False
    retirement_hint_week: int = 0
    
    # Reputation
    reputation_trait: str = "none"
    popularity_modifier: int = 0  # -50 to +50
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fighter_id": self.fighter_id,
            "records": [r.to_dict() for r in self.records],
            "humble_count": self.humble_count,
            "trash_talk_count": self.trash_talk_count,
            "emotional_count": self.emotional_count,
            "call_out_count": self.call_out_count,
            "respectful_count": self.respectful_count,
            "thank_sponsors_count": self.thank_sponsors_count,
            "accept_defeat_count": self.accept_defeat_count,
            "demand_rematch_count": self.demand_rematch_count,
            "cite_injury_count": self.cite_injury_count,
            "question_decision_count": self.question_decision_count,
            "retirement_hint_count": self.retirement_hint_count,
            "blame_camp_count": self.blame_camp_count,
            "consecutive_emotional": self.consecutive_emotional,
            "consecutive_humble": self.consecutive_humble,
            "consecutive_question_decision": self.consecutive_question_decision,
            "current_call_out_target_id": self.current_call_out_target_id,
            "current_call_out_target_name": self.current_call_out_target_name,
            "retirement_hinted": self.retirement_hinted,
            "retirement_hint_week": self.retirement_hint_week,
            "reputation_trait": self.reputation_trait,
            "popularity_modifier": self.popularity_modifier,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InterviewHistory":
        records_data = data.pop("records", [])
        history = cls(**{k: v for k, v in data.items() if k != "records"})
        history.records = [InterviewRecord.from_dict(r) for r in records_data]
        return history


@dataclass
class InterviewResult:
    """Result of processing an interview response"""
    headline: str
    sub_headlines: List[str] = field(default_factory=list)
    popularity_change: int = 0
    rivalry_created: bool = False
    rivalry_target_id: Optional[str] = None
    rivalry_intensity: int = 0  # 1-10
    heat_added: int = 0  # Direct heat score addition to rivalry
    call_out_active: bool = False
    call_out_target_id: Optional[str] = None
    reputation_changed: bool = False
    new_reputation: str = "none"
    opponent_response: Optional[str] = None  # AI opponent's reaction
    
    # Effects for future fights
    motivation_boost_target_id: Optional[str] = None  # Who gets boosted against this fighter
    motivation_boost_amount: int = 0  # +5 or +8
    
    # Sponsor effects
    sponsor_bonus_earned: int = 0  # Bonus cash from thanking sponsors
    sponsor_names_thanked: List[str] = field(default_factory=list)


# ============================================================================
# INTERVIEW TEMPLATES
# ============================================================================

WINNER_TEMPLATES = {
    WinnerResponse.HUMBLE: [
        "{name}: \"I just thank God and my team. {opponent} is a warrior, much respect.\"",
        "{name}: \"Blessed to get the win. All glory to my coaches and training partners.\"",
        "{name}: \"I'm just grateful. {opponent} brought out the best in me tonight.\"",
        "{name}: \"Hard work pays off. I couldn't do this without my camp.\"",
    ],
    WinnerResponse.TRASH_TALK: [
        "{name}: \"I told everyone! Nobody in this division can touch me!\"",
        "{name}: \"{opponent} was supposed to be a challenge? Please. Next!\"",
        "{name}: \"That's what happens when you step in with greatness. Who's next?!\"",
        "{name}: \"Easy work! They keep feeding me cans. Give me a REAL fight!\"",
        "{name}: \"I'm the baddest in this division and everyone knows it!\"",
    ],
    WinnerResponse.CALL_OUT: [
        "{name}: \"{target}, you're next! Stop ducking me!\"",
        "{name}: \"Hey {target}! I just handled your boy. You want some of this?!\"",
        "{name}: \"{target}, I've been asking for this fight. Let's make it happen!\"",
        "{name}: \"DFC, give me {target}. The fans deserve that fight!\"",
    ],
    WinnerResponse.RESPECTFUL: [
        "{name}: \"{opponent} is a true professional. It was an honor to share the cage.\"",
        "{name}: \"Great fight. {opponent} will be back, no doubt about it.\"",
        "{name}: \"Nothing but respect for {opponent}. We both left it all in there.\"",
        "{name}: \"Two warriors went to battle tonight. Respect to {opponent}.\"",
    ],
    WinnerResponse.EMOTIONAL: [
        "{name}: \"I can't believe it... *tears up* ...this means everything to me.\"",
        "{name}: \"Mom, Dad, we did it! *crying* All those sacrifices...\"",
        "{name}: \"I've been through so much to get here... *voice breaking* ...wow.\"",
        "{name}: \"For everyone who doubted me... *emotional* ...look at me now!\"",
    ],
    WinnerResponse.THANK_SPONSORS: [
        "{name}: \"First off, shout out to {sponsors} for believing in me! Couldn't do this without their support.\"",
        "{name}: \"Big thanks to my sponsors - {sponsors}! They've been with me through everything.\"",
        "{name}: \"I gotta thank {sponsors} for making this possible. Best sponsors in the game!\"",
        "{name}: \"Can't forget {sponsors}! If you need quality, check them out. They keep me ready to compete!\"",
        "{name}: \"Shout out to the team and my sponsors {sponsors}! We're building something special.\"",
    ],
}

LOSER_TEMPLATES = {
    LoserResponse.ACCEPT_DEFEAT: [
        "{name}: \"He was the better man tonight. I'll be back stronger.\"",
        "{name}: \"No excuses. {opponent} got the win. Back to the gym.\"",
        "{name}: \"Credit to {opponent}. I need to go back and work on some things.\"",
        "{name}: \"It happens. I'll learn from this and come back better.\"",
    ],
    LoserResponse.DEMAND_REMATCH: [
        "{name}: \"I want the rematch! That wasn't the real me in there!\"",
        "{name}: \"{opponent}, I'm calling you out! Run it back!\"",
        "{name}: \"One fight doesn't define me. I NEED that rematch!\"",
        "{name}: \"This isn't over. {opponent}, let's do it again!\"",
    ],
    LoserResponse.CITE_INJURY: [
        "{name}: \"I wasn't 100% going in. Had some issues in camp, but no excuses.\"",
        "{name}: \"I don't want to make excuses, but I was dealing with an injury.\"",
        "{name}: \"My body let me down tonight. I couldn't perform how I wanted.\"",
        "{name}: \"Camp was rough, had some setbacks. It is what it is.\"",
    ],
    LoserResponse.QUESTION_DECISION: [
        "{name}: \"I thought I won that fight. I don't know what the judges saw.\"",
        "{name}: \"Robbery. Clear robbery. Watch the tape.\"",
        "{name}: \"I'm not sure those judges were watching the same fight.\"",
        "{name}: \"I'll let the fans decide who really won that fight.\"",
    ],
    LoserResponse.RETIREMENT_HINT: [
        "{name}: \"I don't know... I need to think about my future. Maybe it's time.\"",
        "{name}: \"I've given everything to this sport. Maybe I have nothing left.\"",
        "{name}: \"At this point in my career... I need to have some conversations.\"",
        "{name}: \"The fire might be going out. I need to be honest with myself.\"",
    ],
    LoserResponse.BLAME_CAMP: [
        "{name}: \"The gameplan was wrong. We need to look at our preparation.\"",
        "{name}: \"I wasn't prepared properly. Something needs to change in camp.\"",
        "{name}: \"We didn't have the right strategy. That's on my corner.\"",
        "{name}: \"I did what I was told to do. Maybe I need new advice.\"",
    ],
}

# Opponent reaction templates (AI responses to player interviews)
OPPONENT_REACTIONS = {
    "trash_talk_response_angry": [
        "{opponent}: \"All talk. Let's see that energy when we run it back.\"",
        "{opponent}: \"Keep my name out your mouth. You got lucky.\"",
        "{opponent}: \"Big words for someone who barely survived. I'll be back.\"",
    ],
    "trash_talk_response_dismissive": [
        "{opponent}: \"Whatever. I'll let my fists do the talking next time.\"",
        "{opponent}: \"Not even worth responding to. Back to work.\"",
    ],
    "call_out_response_accept": [
        "{target}: \"You want it? You got it. Sign the contract.\"",
        "{target}: \"Finally someone with some guts. Let's do this.\"",
        "{target}: \"I accept. Don't back out now.\"",
    ],
    "call_out_response_decline": [
        "{target}: \"You're not even ranked high enough. Earn it.\"",
        "{target}: \"I've got bigger fish to fry. Get in line.\"",
        "{target}: \"Beat someone in the top 5 first, then we'll talk.\"",
    ],
    "rematch_demand_response": [
        "{opponent}: \"I already beat you. Move on.\"",
        "{opponent}: \"Rematch? I'd just do the same thing again.\"",
        "{opponent}: \"If the money's right, I'll take the easy win again.\"",
    ],
    "question_decision_response": [
        "{opponent}: \"Sore loser. The judges got it right.\"",
        "{opponent}: \"Watch the fight again. I clearly won.\"",
        "{opponent}: \"Can't accept a loss like a man? Pathetic.\"",
    ],
}


# ============================================================================
# INTERVIEW PROCESSING
# ============================================================================

class InterviewManager:
    """
    Manages post-fight interviews and their consequences.
    
    Tracks interview history, applies effects, manages rivalries,
    and handles AI interview generation.
    """
    
    def __init__(self):
        self.histories: Dict[str, InterviewHistory] = {}
    
    def get_history(self, fighter_id: str) -> InterviewHistory:
        """Get or create interview history for a fighter"""
        if fighter_id not in self.histories:
            self.histories[fighter_id] = InterviewHistory(fighter_id=fighter_id)
        return self.histories[fighter_id]
    
    def process_winner_response(
        self,
        fighter_id: str,
        fighter_name: str,
        opponent_id: str,
        opponent_name: str,
        response: WinnerResponse,
        fight_id: str,
        week: int,
        was_title_fight: bool = False,
        call_out_target_id: Optional[str] = None,
        call_out_target_name: Optional[str] = None,
    ) -> InterviewResult:
        """Process a winner's interview response and return effects"""
        history = self.get_history(fighter_id)
        
        # Create record
        record = InterviewRecord(
            week=week,
            fight_id=fight_id,
            opponent_id=opponent_id,
            opponent_name=opponent_name,
            was_winner=True,
            response=response.value,
            call_out_target_id=call_out_target_id,
            call_out_target_name=call_out_target_name,
        )
        history.records.append(record)
        
        # Process based on response type
        result = InterviewResult(headline="")
        
        if response == WinnerResponse.HUMBLE:
            result = self._process_humble_winner(
                history, fighter_name, opponent_name, was_title_fight
            )
        elif response == WinnerResponse.TRASH_TALK:
            result = self._process_trash_talk_winner(
                history, fighter_id, fighter_name, opponent_id, opponent_name
            )
        elif response == WinnerResponse.CALL_OUT:
            result = self._process_call_out(
                history, fighter_id, fighter_name, 
                call_out_target_id, call_out_target_name
            )
        elif response == WinnerResponse.RESPECTFUL:
            result = self._process_respectful_winner(
                history, fighter_name, opponent_name
            )
        elif response == WinnerResponse.EMOTIONAL:
            result = self._process_emotional_winner(
                history, fighter_name, opponent_name, was_title_fight
            )
        elif response == WinnerResponse.THANK_SPONSORS:
            result = self._process_thank_sponsors_winner(
                history, fighter_id, fighter_name, opponent_name
            )
        
        # Update reputation
        self._update_reputation(history)
        
        return result
    
    def process_loser_response(
        self,
        fighter_id: str,
        fighter_name: str,
        opponent_id: str,
        opponent_name: str,
        response: LoserResponse,
        fight_id: str,
        week: int,
        method: str,  # KO, TKO, SUB, DEC
    ) -> InterviewResult:
        """Process a loser's interview response and return effects"""
        history = self.get_history(fighter_id)
        
        # Create record
        record = InterviewRecord(
            week=week,
            fight_id=fight_id,
            opponent_id=opponent_id,
            opponent_name=opponent_name,
            was_winner=False,
            response=response.value,
        )
        history.records.append(record)
        
        # Process based on response type
        result = InterviewResult(headline="")
        
        if response == LoserResponse.ACCEPT_DEFEAT:
            result = self._process_accept_defeat(
                history, fighter_name, opponent_name
            )
        elif response == LoserResponse.DEMAND_REMATCH:
            result = self._process_demand_rematch(
                history, fighter_id, fighter_name, opponent_id, opponent_name
            )
        elif response == LoserResponse.CITE_INJURY:
            result = self._process_cite_injury(
                history, fighter_name, opponent_name
            )
        elif response == LoserResponse.QUESTION_DECISION:
            result = self._process_question_decision(
                history, fighter_name, opponent_name, method
            )
        elif response == LoserResponse.RETIREMENT_HINT:
            result = self._process_retirement_hint(
                history, fighter_name, week
            )
        elif response == LoserResponse.BLAME_CAMP:
            result = self._process_blame_camp(
                history, fighter_name, opponent_name
            )
        
        # Update reputation
        self._update_reputation(history)
        
        return result
    
    # ========================================================================
    # WINNER RESPONSE PROCESSORS
    # ========================================================================
    
    def _process_humble_winner(
        self, history: InterviewHistory, name: str, opponent: str, was_title: bool
    ) -> InterviewResult:
        """Process humble winner response"""
        history.humble_count += 1
        history.consecutive_humble += 1
        history.consecutive_emotional = 0
        
        template = random.choice(WINNER_TEMPLATES[WinnerResponse.HUMBLE])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        result.popularity_change = 3
        
        # Check for "company man" penalty (too humble)
        if history.consecutive_humble >= 4:
            result.sub_headlines.append(
                f"Fans starting to see {name} as predictable, 'company man' type"
            )
            result.popularity_change = 0
            if history.reputation_trait != ReputationTrait.COMPANY_MAN.value:
                result.reputation_changed = True
                result.new_reputation = ReputationTrait.COMPANY_MAN.value
        
        return result
    
    def _process_trash_talk_winner(
        self, history: InterviewHistory, fighter_id: str, name: str, 
        opponent_id: str, opponent: str
    ) -> InterviewResult:
        """Process trash talk winner response"""
        history.trash_talk_count += 1
        history.consecutive_humble = 0
        history.consecutive_emotional = 0
        
        template = random.choice(WINNER_TEMPLATES[WinnerResponse.TRASH_TALK])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        
        # Creates rivalry with direct heat addition
        result.rivalry_created = True
        result.rivalry_target_id = opponent_id
        result.rivalry_intensity = 5  # Medium intensity
        result.heat_added = 15  # Direct heat score addition
        
        # Opponent gets motivated
        result.motivation_boost_target_id = opponent_id
        result.motivation_boost_amount = 5
        
        # Polarizing - can gain or lose popularity
        if random.random() < 0.6:
            result.popularity_change = 5  # Fans love drama
        else:
            result.popularity_change = -3  # Some find it classless
        
        # Opponent reacts
        if random.random() < 0.7:
            reaction_templates = OPPONENT_REACTIONS["trash_talk_response_angry"]
        else:
            reaction_templates = OPPONENT_REACTIONS["trash_talk_response_dismissive"]
        result.opponent_response = random.choice(reaction_templates).format(opponent=opponent)
        
        # Check for heel reputation
        if history.trash_talk_count >= 3:
            if history.reputation_trait != ReputationTrait.HEEL.value:
                result.reputation_changed = True
                result.new_reputation = ReputationTrait.HEEL.value
                result.sub_headlines.append(f"{name} embracing villain role")
        
        return result
    
    def _process_call_out(
        self, history: InterviewHistory, fighter_id: str, name: str,
        target_id: Optional[str], target_name: Optional[str]
    ) -> InterviewResult:
        """Process call-out response"""
        history.call_out_count += 1
        history.consecutive_humble = 0
        history.consecutive_emotional = 0
        
        if not target_id or not target_name:
            # Generic call out
            headline = f"{name}: \"I'll fight anyone! Give me the best!\""
            return InterviewResult(headline=headline, popularity_change=2)
        
        template = random.choice(WINNER_TEMPLATES[WinnerResponse.CALL_OUT])
        headline = template.format(name=name, target=target_name)
        
        result = InterviewResult(headline=headline)
        result.call_out_active = True
        result.call_out_target_id = target_id
        
        # Store active call out
        history.current_call_out_target_id = target_id
        history.current_call_out_target_name = target_name
        
        # Target gets motivated (+8, higher than trash talk)
        result.motivation_boost_target_id = target_id
        result.motivation_boost_amount = 8
        
        result.popularity_change = 4  # Fans love call-outs
        
        # Target response (50/50 accept or decline)
        if random.random() < 0.5:
            reaction = random.choice(OPPONENT_REACTIONS["call_out_response_accept"])
            result.sub_headlines.append(f"Fight likely to happen!")
        else:
            reaction = random.choice(OPPONENT_REACTIONS["call_out_response_decline"])
        result.opponent_response = reaction.format(target=target_name)
        
        return result
    
    def _process_respectful_winner(
        self, history: InterviewHistory, name: str, opponent: str
    ) -> InterviewResult:
        """Process respectful winner response"""
        history.respectful_count += 1
        history.consecutive_humble = 0
        history.consecutive_emotional = 0
        
        template = random.choice(WINNER_TEMPLATES[WinnerResponse.RESPECTFUL])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        result.popularity_change = 2
        
        # Check for professional reputation
        if history.respectful_count + history.humble_count >= 5:
            if history.reputation_trait not in (
                ReputationTrait.PROFESSIONAL.value,
                ReputationTrait.CLASS_ACT.value
            ):
                result.reputation_changed = True
                result.new_reputation = ReputationTrait.PROFESSIONAL.value
        
        return result
    
    def _process_emotional_winner(
        self, history: InterviewHistory, name: str, opponent: str, was_title: bool
    ) -> InterviewResult:
        """Process emotional winner response"""
        history.emotional_count += 1
        history.consecutive_emotional += 1
        history.consecutive_humble = 0
        
        template = random.choice(WINNER_TEMPLATES[WinnerResponse.EMOTIONAL])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        
        # Big popularity boost for emotional moments... at first
        if history.consecutive_emotional <= 2:
            result.popularity_change = 8 if was_title else 5
            result.sub_headlines.append(f"Fans love {name}'s genuine emotion")
        elif history.consecutive_emotional == 3:
            result.popularity_change = 2
            result.sub_headlines.append(f"Fans starting to tire of {name}'s emotional displays")
        else:
            # Penalty kicks in after 3 in a row
            result.popularity_change = -5
            result.sub_headlines.append(f"\"Crying again?\" - Fans and media mock {name}'s act")
            if history.reputation_trait != ReputationTrait.DRAMA_QUEEN.value:
                result.reputation_changed = True
                result.new_reputation = ReputationTrait.DRAMA_QUEEN.value
        
        return result
    
    def _process_thank_sponsors_winner(
        self, history: InterviewHistory, fighter_id: str, name: str, opponent: str
    ) -> InterviewResult:
        """Process thank sponsors winner response
        
        Gives bonus cash from sponsors and slight popularity boost.
        Sponsors appreciate being thanked publicly.
        """
        history.thank_sponsors_count += 1
        history.consecutive_humble = 0
        history.consecutive_emotional = 0
        
        # Get fighter's sponsors (passed via kwargs or looked up)
        # For now, we'll return placeholder info - CLI will fill in actual sponsors
        result = InterviewResult(headline="")
        result.popularity_change = 1  # Neutral, slightly positive
        
        # The actual sponsor names and bonus will be filled in by CLI
        # which has access to the fighter's sponsorship data
        # This function just sets up the response type
        
        # Template will be filled when we have sponsor names
        result.sponsor_names_thanked = []  # Will be filled by CLI
        result.sponsor_bonus_earned = 0    # Will be calculated by CLI
        
        # Headline placeholder - CLI will format with actual sponsor names
        result.headline = f"{name}: \"Shout out to my sponsors for believing in me!\""
        
        return result
    
    # ========================================================================
    # LOSER RESPONSE PROCESSORS
    # ========================================================================
    
    def _process_accept_defeat(
        self, history: InterviewHistory, name: str, opponent: str
    ) -> InterviewResult:
        """Process accept defeat response"""
        history.accept_defeat_count += 1
        history.consecutive_question_decision = 0
        
        template = random.choice(LOSER_TEMPLATES[LoserResponse.ACCEPT_DEFEAT])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        result.popularity_change = 2  # Respect for graciousness
        
        # Risk: labeled as "gatekeeper" if always accepting defeat
        if history.accept_defeat_count >= 3:
            result.sub_headlines.append(
                f"Some question if {name} still has the killer instinct"
            )
        
        return result
    
    def _process_demand_rematch(
        self, history: InterviewHistory, fighter_id: str, name: str,
        opponent_id: str, opponent: str
    ) -> InterviewResult:
        """Process demand rematch response"""
        history.demand_rematch_count += 1
        history.consecutive_question_decision = 0
        
        template = random.choice(LOSER_TEMPLATES[LoserResponse.DEMAND_REMATCH])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        
        # Creates rivalry with heat
        result.rivalry_created = True
        result.rivalry_target_id = opponent_id
        result.rivalry_intensity = 4
        result.heat_added = 12  # Direct heat score addition
        
        result.popularity_change = 3  # Shows fire
        
        # Check if already demanded rematch from this opponent
        same_opponent_demands = sum(
            1 for r in history.records 
            if r.opponent_id == opponent_id and r.response == LoserResponse.DEMAND_REMATCH.value
        )
        
        if same_opponent_demands >= 2:
            result.popularity_change = -5
            result.sub_headlines.append(f"{name} becoming obsessed with {opponent}")
            if history.reputation_trait != ReputationTrait.OBSESSED.value:
                result.reputation_changed = True
                result.new_reputation = ReputationTrait.OBSESSED.value
        
        # Opponent response
        result.opponent_response = random.choice(
            OPPONENT_REACTIONS["rematch_demand_response"]
        ).format(opponent=opponent)
        
        return result
    
    def _process_cite_injury(
        self, history: InterviewHistory, name: str, opponent: str
    ) -> InterviewResult:
        """Process cite injury response"""
        history.cite_injury_count += 1
        history.consecutive_question_decision = 0
        
        template = random.choice(LOSER_TEMPLATES[LoserResponse.CITE_INJURY])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        
        # Neutral to slightly negative
        if history.cite_injury_count <= 1:
            result.popularity_change = 0  # Benefit of the doubt
            result.sub_headlines.append(f"Fans sympathetic to {name}'s injury claims")
        elif history.cite_injury_count <= 2:
            result.popularity_change = -2
            result.sub_headlines.append(f"Some skeptical of {name}'s injury history")
        else:
            result.popularity_change = -5
            result.sub_headlines.append(f"\"Always injured\" - Credibility questioned for {name}")
        
        return result
    
    def _process_question_decision(
        self, history: InterviewHistory, name: str, opponent: str, method: str
    ) -> InterviewResult:
        """Process question decision response"""
        history.question_decision_count += 1
        history.consecutive_question_decision += 1
        
        template = random.choice(LOSER_TEMPLATES[LoserResponse.QUESTION_DECISION])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        
        # Only makes sense for decisions
        if method != "DEC":
            result.popularity_change = -8
            result.sub_headlines.append(
                f"Bizarre: {name} questions result despite being finished"
            )
            return result
        
        # First time or two - fans might agree
        if history.consecutive_question_decision <= 1:
            result.popularity_change = 0
            result.sub_headlines.append(f"Controversy swirls around {name}'s loss")
        else:
            result.popularity_change = -5
            result.sub_headlines.append(f"{name} developing reputation as sore loser")
            if history.consecutive_question_decision >= 3:
                if history.reputation_trait != ReputationTrait.CRYBABY.value:
                    result.reputation_changed = True
                    result.new_reputation = ReputationTrait.CRYBABY.value
        
        # Opponent fires back
        result.opponent_response = random.choice(
            OPPONENT_REACTIONS["question_decision_response"]
        ).format(opponent=opponent)
        
        return result
    
    def _process_retirement_hint(
        self, history: InterviewHistory, name: str, week: int
    ) -> InterviewResult:
        """Process retirement hint response"""
        history.retirement_hint_count += 1
        history.retirement_hinted = True
        history.retirement_hint_week = week
        history.consecutive_question_decision = 0
        
        template = random.choice(LOSER_TEMPLATES[LoserResponse.RETIREMENT_HINT])
        headline = template.format(name=name)
        
        result = InterviewResult(headline=headline)
        result.popularity_change = 5  # Sympathy
        
        result.sub_headlines.append(f"Is this the end for {name}?")
        
        # Note: If they DON'T retire within ~52 weeks, credibility takes a hit
        # (handled elsewhere)
        
        return result
    
    def _process_blame_camp(
        self, history: InterviewHistory, name: str, opponent: str
    ) -> InterviewResult:
        """Process blame camp response"""
        history.blame_camp_count += 1
        history.consecutive_question_decision = 0
        
        template = random.choice(LOSER_TEMPLATES[LoserResponse.BLAME_CAMP])
        headline = template.format(name=name, opponent=opponent)
        
        result = InterviewResult(headline=headline)
        
        # Deflects blame but damages relationships
        if history.blame_camp_count <= 1:
            result.popularity_change = -2
            result.sub_headlines.append(f"Tension brewing at {name}'s camp?")
        else:
            result.popularity_change = -5
            result.sub_headlines.append(
                f"{name} burning bridges - coaches reluctant to work with blame-shifter"
            )
        
        return result
    
    # ========================================================================
    # REPUTATION MANAGEMENT
    # ========================================================================
    
    def _update_reputation(self, history: InterviewHistory) -> None:
        """Update reputation trait based on interview patterns"""
        total = len(history.records)
        if total < 3:
            return
        
        # Calculate percentages
        humble_pct = history.humble_count / total if total > 0 else 0
        respectful_pct = history.respectful_count / total if total > 0 else 0
        trash_pct = history.trash_talk_count / total if total > 0 else 0
        
        # Class act: consistently humble + respectful
        if humble_pct + respectful_pct >= 0.7 and total >= 5:
            if history.reputation_trait == ReputationTrait.NONE.value:
                history.reputation_trait = ReputationTrait.CLASS_ACT.value
        
        # Heel: lots of trash talk
        if trash_pct >= 0.5 and history.trash_talk_count >= 3:
            history.reputation_trait = ReputationTrait.HEEL.value
    
    # ========================================================================
    # AI INTERVIEW GENERATION
    # ========================================================================
    
    def generate_ai_interview(
        self,
        fighter_id: str,
        fighter_name: str,
        opponent_id: str,
        opponent_name: str,
        was_winner: bool,
        fight_id: str,
        week: int,
        method: str = "DEC",
        personality: str = "Methodical",
        is_champion: bool = False,
        age: int = 28,
        losses: int = 0,
    ) -> InterviewResult:
        """Generate an AI fighter's interview response based on personality"""
        
        if was_winner:
            response = self._select_ai_winner_response(
                personality, is_champion, losses
            )
            # AI doesn't do specific call-outs (too complex)
            return self.process_winner_response(
                fighter_id, fighter_name, opponent_id, opponent_name,
                response, fight_id, week, is_champion
            )
        else:
            response = self._select_ai_loser_response(
                personality, method, age, losses
            )
            return self.process_loser_response(
                fighter_id, fighter_name, opponent_id, opponent_name,
                response, fight_id, week, method
            )
    
    def _select_ai_winner_response(
        self, personality: str, is_champion: bool, losses: int
    ) -> WinnerResponse:
        """Select winner response based on AI personality"""
        personality_lower = personality.lower()
        
        # Aggressive personalities trash talk
        if personality_lower in ("aggressive", "wild", "showman", "cocky"):
            weights = {
                WinnerResponse.HUMBLE: 0.1,
                WinnerResponse.TRASH_TALK: 0.5,
                WinnerResponse.RESPECTFUL: 0.1,
                WinnerResponse.EMOTIONAL: 0.1,
                WinnerResponse.CALL_OUT: 0.2,  # Generic call out
            }
        # Methodical/analytical personalities are respectful
        elif personality_lower in ("methodical", "analytical", "technical", "calculated"):
            weights = {
                WinnerResponse.HUMBLE: 0.3,
                WinnerResponse.TRASH_TALK: 0.05,
                WinnerResponse.RESPECTFUL: 0.5,
                WinnerResponse.EMOTIONAL: 0.1,
                WinnerResponse.CALL_OUT: 0.05,
            }
        # Emotional personalities
        elif personality_lower in ("emotional", "passionate", "intense"):
            weights = {
                WinnerResponse.HUMBLE: 0.2,
                WinnerResponse.TRASH_TALK: 0.15,
                WinnerResponse.RESPECTFUL: 0.15,
                WinnerResponse.EMOTIONAL: 0.4,
                WinnerResponse.CALL_OUT: 0.1,
            }
        else:
            # Default balanced
            weights = {
                WinnerResponse.HUMBLE: 0.3,
                WinnerResponse.TRASH_TALK: 0.15,
                WinnerResponse.RESPECTFUL: 0.3,
                WinnerResponse.EMOTIONAL: 0.15,
                WinnerResponse.CALL_OUT: 0.1,
            }
        
        # Champions slightly more likely to be respectful or trash talk
        if is_champion:
            weights[WinnerResponse.TRASH_TALK] += 0.1
            weights[WinnerResponse.HUMBLE] -= 0.05
            weights[WinnerResponse.EMOTIONAL] -= 0.05
        
        return self._weighted_choice(weights)
    
    def _select_ai_loser_response(
        self, personality: str, method: str, age: int, losses: int
    ) -> LoserResponse:
        """Select loser response based on AI personality and context"""
        personality_lower = personality.lower()
        
        # Base weights
        weights = {
            LoserResponse.ACCEPT_DEFEAT: 0.35,
            LoserResponse.DEMAND_REMATCH: 0.2,
            LoserResponse.CITE_INJURY: 0.15,
            LoserResponse.QUESTION_DECISION: 0.1,
            LoserResponse.RETIREMENT_HINT: 0.1,
            LoserResponse.BLAME_CAMP: 0.1,
        }
        
        # Aggressive personalities demand rematches
        if personality_lower in ("aggressive", "wild", "cocky"):
            weights[LoserResponse.DEMAND_REMATCH] += 0.2
            weights[LoserResponse.ACCEPT_DEFEAT] -= 0.15
            weights[LoserResponse.QUESTION_DECISION] += 0.1
        
        # Methodical accept defeat gracefully
        if personality_lower in ("methodical", "analytical", "professional"):
            weights[LoserResponse.ACCEPT_DEFEAT] += 0.25
            weights[LoserResponse.QUESTION_DECISION] -= 0.1
            weights[LoserResponse.BLAME_CAMP] -= 0.05
        
        # Can only question decision if it was a decision
        if method != "DEC":
            weights[LoserResponse.ACCEPT_DEFEAT] += weights[LoserResponse.QUESTION_DECISION]
            weights[LoserResponse.QUESTION_DECISION] = 0
        
        # Older fighters with losses more likely to hint retirement
        if age >= 35 and losses >= 3:
            weights[LoserResponse.RETIREMENT_HINT] += 0.15
        elif age < 30:
            weights[LoserResponse.RETIREMENT_HINT] = 0.02
        
        return self._weighted_choice(weights)
    
    def _weighted_choice(self, weights: Dict[Any, float]) -> Any:
        """Make a weighted random choice"""
        total = sum(weights.values())
        r = random.random() * total
        cumulative = 0
        for choice, weight in weights.items():
            cumulative += weight
            if r <= cumulative:
                return choice
        return list(weights.keys())[0]
    
    # ========================================================================
    # MATCHUP EFFECTS
    # ========================================================================
    
    def get_call_out_probability_boost(
        self, fighter_id: str, opponent_id: str
    ) -> float:
        """Get probability boost for a matchup if there's an active call-out"""
        history = self.histories.get(fighter_id)
        if not history:
            return 0.0
        
        if history.current_call_out_target_id == opponent_id:
            return 0.7  # 70% more likely
        return 0.0
    
    def get_motivation_boost(
        self, fighter_id: str, opponent_id: str
    ) -> int:
        """Get motivation boost for fighter against specific opponent"""
        # Check if opponent called them out or trash talked them
        opponent_history = self.histories.get(opponent_id)
        if not opponent_history:
            return 0
        
        # Called out specifically
        if opponent_history.current_call_out_target_id == fighter_id:
            return 8
        
        # Trash talked after beating them
        for record in opponent_history.records[-5:]:  # Last 5 interviews
            if (record.opponent_id == fighter_id and 
                record.response == WinnerResponse.TRASH_TALK.value):
                return 5
        
        return 0
    
    def clear_call_out(self, fighter_id: str) -> None:
        """Clear a fighter's active call-out (after fight happens)"""
        history = self.histories.get(fighter_id)
        if history:
            history.current_call_out_target_id = None
            history.current_call_out_target_name = None
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize all interview data"""
        return {
            "histories": {
                fid: h.to_dict() for fid, h in self.histories.items()
            }
        }
    
    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load interview data from dict"""
        histories_data = data.get("histories", {})
        self.histories = {
            fid: InterviewHistory.from_dict(h) 
            for fid, h in histories_data.items()
        }


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================

def create_interview_manager() -> InterviewManager:
    """Create a new interview manager"""
    return InterviewManager()


def get_winner_response_options() -> List[Tuple[WinnerResponse, str, str]]:
    """Get winner response options with descriptions
    
    Returns: List of (response, display_name, description)
    """
    return [
        (WinnerResponse.HUMBLE, "ðŸ™ Humble", 
         "Thank God and your team. Steady popularity, but opponents may see you as soft."),
        (WinnerResponse.TRASH_TALK, "ðŸ˜¤ Trash Talk", 
         "Talk trash about your opponent. Polarizing, creates rivalry, opponent gets +5 boost."),
        (WinnerResponse.CALL_OUT, "ðŸ“¢ Call Out", 
         "Call out a specific fighter. +70% matchup chance, but they get +8 boost against you."),
        (WinnerResponse.RESPECTFUL, "ðŸ¤ Respectful", 
         "Show respect to opponent. No drama, but no enemies. Professional reputation."),
        (WinnerResponse.EMOTIONAL, "ðŸ˜­ Emotional", 
         "Get emotional, tear up. Big popularity boost - but overuse becomes mockery."),
    ]


def get_loser_response_options(method: str) -> List[Tuple[LoserResponse, str, str]]:
    """Get loser response options with descriptions
    
    Args:
        method: Fight result method (DEC, KO, TKO, SUB)
    
    Returns: List of (response, display_name, description)
    """
    options = [
        (LoserResponse.ACCEPT_DEFEAT, "ðŸ™ Accept Defeat", 
         "Credit opponent, vow to improve. Graceful, but risk 'gatekeeper' label."),
        (LoserResponse.DEMAND_REMATCH, "ðŸ˜  Demand Rematch", 
         "Demand a rematch. Creates rivalry, shows fire. Don't overdo it vs same opponent."),
        (LoserResponse.CITE_INJURY, "ðŸ¥ Cite Injury", 
         "Mention you weren't 100%. Protects reputation once, loses credibility if repeated."),
    ]
    
    # Only show question decision for decisions
    if method == "DEC":
        options.append(
            (LoserResponse.QUESTION_DECISION, "âš–ï¸ Question Decision", 
             "Claim you won. Controversy = attention, but judges may remember.")
        )
    
    options.extend([
        (LoserResponse.RETIREMENT_HINT, "ðŸ’­ Hint Retirement", 
         "Hint you might retire. Big sympathy, but must follow through or lose credibility."),
        (LoserResponse.BLAME_CAMP, "ðŸ”„ Blame Camp", 
         "Blame the gameplan/corner. Deflects blame but damages coach relationships."),
    ])
    
    return options
