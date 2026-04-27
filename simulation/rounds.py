# simulation/rounds.py
# Module 15: Round-by-Round Commentary System
# Lines: ~950
#
# Detailed round tracking, play-by-play events, and commentary generation
# for immersive fight narratives.

"""
Cage Dynasty - Round-by-Round Commentary System

This module provides:
- Detailed event logging for every exchange
- Round summaries with key moments
- Commentary generation (play-by-play and color)
- Fight momentum tracking
- Dramatic narrative moments
- Post-fight analysis
"""

from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import random

from simulation.fight_engine import (
    Position, StrikeType, SubmissionType, GrapplingAction,
    FighterAttributes, FighterState, FightState, RoundStats,
    STANDING_POSITIONS, CLINCH_POSITIONS, DOMINANT_POSITIONS,
    STRIKE_PROPERTIES
)


# ============================================================================
# EVENT TYPES
# ============================================================================

class FightEventType(Enum):
    """Types of events that occur during a fight"""
    # Striking events
    STRIKE_LANDED = "strike_landed"
    STRIKE_MISSED = "strike_missed"
    STRIKE_BLOCKED = "strike_blocked"
    COUNTER_STRIKE = "counter_strike"
    COMBINATION = "combination"
    
    # Big moments
    KNOCKDOWN = "knockdown"
    ROCKED = "rocked"
    CUT = "cut"
    FLASH_KO = "flash_ko"
    
    # Grappling events
    TAKEDOWN_SUCCESS = "takedown_success"
    TAKEDOWN_STUFFED = "takedown_stuffed"
    SLAM = "slam"
    POSITION_ADVANCE = "position_advance"
    SWEEP = "sweep"
    ESCAPE = "escape"
    STAND_UP = "stand_up"
    
    # Clinch events
    CLINCH_INITIATED = "clinch_initiated"
    CLINCH_BREAK = "clinch_break"
    CAGE_PRESS = "cage_press"
    
    # Submission events
    SUBMISSION_ATTEMPT = "submission_attempt"
    SUBMISSION_LOCKED = "submission_locked"
    SUBMISSION_ESCAPE = "submission_escape"
    SUBMISSION_FINISH = "submission_finish"
    
    # Control events
    GROUND_CONTROL = "ground_control"
    GNP_FLURRY = "gnp_flurry"
    
    # Fight flow events
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    REFEREE_STANDUP = "referee_standup"
    DOCTOR_CHECK = "doctor_check"
    TIMEOUT = "timeout"
    
    # Finish events
    KO_FINISH = "ko_finish"
    TKO_FINISH = "tko_finish"
    SUBMISSION_WIN = "submission_win"
    DECISION = "decision"


class EventSignificance(Enum):
    """How significant an event is for commentary"""
    ROUTINE = 1       # Normal action, minimal commentary
    NOTABLE = 2       # Worth mentioning
    SIGNIFICANT = 3   # Key moment in round
    DRAMATIC = 4      # Fight-changing moment
    HISTORIC = 5      # Career/legacy moment


# ============================================================================
# FIGHT EVENT
# ============================================================================

@dataclass
class FightEvent:
    """A single event during a fight"""
    event_type: FightEventType
    round_num: int
    exchange_num: int
    time_str: str
    
    # Participants
    actor_id: str
    actor_name: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    
    # Event details
    action: Optional[str] = None  # Specific strike/submission/grappling action
    success: bool = True
    damage: float = 0.0
    position: Optional[Position] = None
    new_position: Optional[Position] = None
    
    # Significance
    significance: EventSignificance = EventSignificance.ROUTINE
    
    # Generated commentary
    commentary: str = ""
    color_commentary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "round": self.round_num,
            "exchange": self.exchange_num,
            "time": self.time_str,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "action": self.action,
            "success": self.success,
            "damage": self.damage,
            "significance": self.significance.value,
            "commentary": self.commentary
        }


# ============================================================================
# ROUND SUMMARY
# ============================================================================

@dataclass
class RoundSummary:
    """Summary of a single round"""
    round_num: int
    
    # Stats
    fighter1_stats: RoundStats
    fighter2_stats: RoundStats
    
    # Scoring
    fighter1_score: int = 10
    fighter2_score: int = 10
    round_winner_id: Optional[str] = None
    
    # Key moments
    key_events: List[FightEvent] = field(default_factory=list)
    knockdowns: Dict[str, int] = field(default_factory=dict)
    
    # Control
    position_control: Dict[str, float] = field(default_factory=dict)
    dominant_fighter_id: Optional[str] = None
    
    # Narrative
    round_description: str = ""
    momentum_shift: bool = False
    
    def add_key_event(self, event: FightEvent) -> None:
        """Add a significant event to round summary"""
        if event.significance.value >= EventSignificance.SIGNIFICANT.value:
            self.key_events.append(event)
    
    def generate_description(
        self,
        fighter1_name: str,
        fighter2_name: str
    ) -> str:
        """Generate narrative description of the round"""
        descriptions = []
        
        # Determine round character
        total_strikes = (
            self.fighter1_stats.significant_strikes_landed +
            self.fighter2_stats.significant_strikes_landed
        )
        total_control = (
            self.fighter1_stats.control_time +
            self.fighter2_stats.control_time
        )
        total_takedowns = (
            self.fighter1_stats.takedowns_landed +
            self.fighter2_stats.takedowns_landed
        )
        total_sub_attempts = (
            self.fighter1_stats.submission_attempts +
            self.fighter2_stats.submission_attempts
        )
        
        # Opening - prioritize knockdowns, then compare grappling vs striking
        if self.knockdowns:
            kd_fighter = max(self.knockdowns.keys(), key=lambda k: self.knockdowns[k])
            kd_count = self.knockdowns[kd_fighter]
            if kd_count > 1:
                descriptions.append(f"A dominant round with {kd_count} knockdowns")
            else:
                descriptions.append("A round punctuated by a knockdown")
        else:
            # Calculate grappling score vs striking score
            grappling_score = total_control + (total_takedowns * 3) + (total_sub_attempts * 2)
            striking_score = total_strikes
            
            # Determine what characterized the round
            if grappling_score > striking_score * 1.5 and total_control > 10:
                if total_sub_attempts > 0:
                    descriptions.append("A grappling-heavy round with submission threats")
                elif total_takedowns > 0:
                    descriptions.append("A wrestling-dominant round")
                else:
                    descriptions.append("A grappling-heavy round")
            elif striking_score > grappling_score * 1.5 and total_strikes > 15:
                descriptions.append("A striking battle")
            elif total_strikes > 30:
                descriptions.append("A high-action round")
            elif total_control > 20:
                descriptions.append("A grinding, control-focused round")
            elif total_strikes < 10 and total_control < 10:
                descriptions.append("A slow, tactical round")
            else:
                descriptions.append("A competitive round with mixed action")
        
        # Winner description
        if self.round_winner_id:
            winner_name = fighter1_name if self.round_winner_id == "fighter1" else fighter2_name
            score_diff = abs(self.fighter1_score - self.fighter2_score)
            
            if score_diff >= 2:
                descriptions.append(f"clearly won by {winner_name}")
            else:
                descriptions.append(f"edged by {winner_name}")
        else:
            descriptions.append("that could go either way")
        
        self.round_description = " - ".join(descriptions) + "."
        return self.round_description
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "fighter1_stats": self.fighter1_stats.to_dict(),
            "fighter2_stats": self.fighter2_stats.to_dict(),
            "fighter1_score": self.fighter1_score,
            "fighter2_score": self.fighter2_score,
            "round_winner_id": self.round_winner_id,
            "key_events": [e.to_dict() for e in self.key_events],
            "knockdowns": self.knockdowns,
            "round_description": self.round_description
        }


# ============================================================================
# COMMENTARY TEMPLATES
# ============================================================================

# Strike commentary templates
STRIKE_TEMPLATES = {
    StrikeType.JAB: {
        "landed": [
            "{actor} lands a sharp jab.",
            "{actor} pumps the jab.",
            "Quick jab connects for {actor}.",
            "{actor} touches {target} with the jab.",
        ],
        "missed": [
            "{target} slips the jab.",
            "Jab falls short.",
            "{actor}'s jab misses the mark.",
        ],
        "significant": [
            "{actor} snaps {target}'s head back with a stiff jab!",
            "That jab had some pop on it!",
        ]
    },
    StrikeType.CROSS: {
        "landed": [
            "{actor} lands the straight right!",
            "Cross connects for {actor}.",
            "{actor} finds a home for the two.",
            "Right hand lands clean.",
        ],
        "missed": [
            "{target} makes {actor} miss the cross.",
            "The right hand sails past.",
        ],
        "significant": [
            "BIG right hand by {actor}!",
            "{actor} CRACKS {target} with the cross!",
            "That cross landed flush!",
        ]
    },
    StrikeType.HOOK: {
        "landed": [
            "{actor} hooks to the head.",
            "Left hook finds the target.",
            "{actor} wraps the hook around {target}'s guard.",
        ],
        "missed": [
            "{target} ducks under the hook.",
            "Hook swings wide.",
        ],
        "significant": [
            "HUGE hook by {actor}!",
            "{actor} ROCKS {target} with that hook!",
            "What a hook! {target} is in trouble!",
        ]
    },
    StrikeType.HEAD_KICK: {
        "landed": [
            "Head kick lands for {actor}!",
            "{actor} catches {target} with the high kick.",
        ],
        "missed": [
            "{target} blocks the head kick.",
            "High kick misses.",
        ],
        "significant": [
            "HEAD KICK! {target} is HURT!",
            "{actor} BLASTS {target} with a head kick!",
            "OH! That head kick connected flush!",
        ]
    },
    StrikeType.LEG_KICK: {
        "landed": [
            "{actor} chops the lead leg.",
            "Leg kick connects.",
            "{actor} targets the calf.",
        ],
        "missed": [
            "{target} checks the leg kick.",
            "Leg kick partially blocked.",
        ],
        "significant": [
            "{target}'s leg is compromised!",
            "That leg kick buckled {target}!",
        ]
    },
    StrikeType.BODY_KICK: {
        "landed": [
            "{actor} digs a kick to the body.",
            "Body kick thuds home.",
        ],
        "missed": [
            "{target} catches the body kick.",
        ],
        "significant": [
            "{target} winces from that body kick!",
            "That kick to the liver had {target} grimacing!",
        ]
    },
    StrikeType.KNEE_BODY: {
        "landed": [
            "{actor} drives a knee to the body.",
            "Knee connects in the clinch.",
        ],
        "significant": [
            "VICIOUS knee to the body!",
        ]
    },
    StrikeType.KNEE_HEAD: {
        "landed": [
            "{actor} brings up the knee!",
        ],
        "significant": [
            "DEVASTATING knee to the head!",
            "{actor} LANDS THE KNEE! {target} IS HURT!",
        ]
    },
    StrikeType.FLYING_KNEE: {
        "landed": [
            "{actor} launches a flying knee!",
        ],
        "significant": [
            "FLYING KNEE! WHAT A SHOT!",
            "{actor} LANDS THE FLYING KNEE! THIS COULD BE IT!",
        ]
    },
    StrikeType.GNP_PUNCH: {
        "landed": [
            "{actor} fires punches from the top.",
            "Ground and pound from {actor}.",
        ],
        "significant": [
            "{actor} is UNLOADING with ground and pound!",
            "The referee is watching closely!",
        ]
    },
    StrikeType.GNP_ELBOW: {
        "landed": [
            "{actor} drops elbows from top position.",
            "Elbow from the top by {actor}.",
        ],
        "significant": [
            "NASTY elbow opens up a cut!",
            "{actor} is raining down elbows!",
        ]
    },
}

# Grappling commentary templates
GRAPPLING_TEMPLATES = {
    GrapplingAction.DOUBLE_LEG: {
        "success": [
            "{actor} completes the double leg!",
            "{actor} drives through with the double!",
            "Beautiful double leg takedown by {actor}.",
            "{actor} gets the fight to the ground!",
        ],
        "failed": [
            "{target} sprawls and stuffs the shot.",
            "{actor}'s takedown attempt is denied.",
            "Good takedown defense from {target}.",
        ]
    },
    GrapplingAction.SINGLE_LEG: {
        "success": [
            "{actor} finishes the single leg.",
            "Single leg converts for {actor}.",
        ],
        "failed": [
            "{target} hops free from the single.",
            "Single leg attempt stuffed.",
        ]
    },
    GrapplingAction.PASS_TO_SIDE: {
        "success": [
            "{actor} passes to side control!",
            "Guard pass! {actor} advances position.",
        ],
        "failed": [
            "{target} retains guard.",
        ]
    },
    GrapplingAction.MOUNT_TRANSITION: {
        "success": [
            "{actor} transitions to mount!",
            "{actor} takes the mount! Bad spot for {target}!",
        ],
        "failed": [
            "{target} prevents the mount.",
        ]
    },
    GrapplingAction.TAKE_BACK: {
        "success": [
            "{actor} takes the back!",
            "Back control for {actor}! This is dangerous!",
        ],
        "failed": [
            "{target} defends the back take.",
        ]
    },
    GrapplingAction.STAND_UP: {
        "success": [
            "{actor} works back to the feet.",
            "{actor} gets back up!",
            "Back standing after a scramble.",
        ],
        "failed": [
            "{target} keeps {actor} grounded.",
        ]
    },
    GrapplingAction.SCISSOR_SWEEP: {
        "success": [
            "{actor} hits the scissor sweep!",
            "Beautiful sweep! {actor} reverses position!",
        ],
        "failed": [
            "Sweep attempt fails.",
        ]
    },
    GrapplingAction.BUTTERFLY_SWEEP: {
        "success": [
            "{actor} elevates with the butterfly sweep!",
            "Sweep! {actor} is now on top!",
        ],
        "failed": [
            "{target} bases out and prevents the sweep.",
        ]
    },
}

# Submission commentary templates
SUBMISSION_TEMPLATES = {
    SubmissionType.REAR_NAKED_CHOKE: {
        "attempt": [
            "{actor} is looking for the rear naked choke!",
            "{actor} sinks in the hooks and goes for the choke!",
            "RNC attempt! {target} is in deep trouble!",
        ],
        "locked": [
            "{actor} has it locked in!",
            "The choke is TIGHT!",
            "This could be it! The RNC is sunk in!",
        ],
        "escaped": [
            "{target} fights out of the choke!",
            "Great defense! {target} escapes!",
        ],
        "finish": [
            "{target} TAPS! It's over by rear naked choke!",
            "{actor} gets the submission! RNC!",
        ]
    },
    SubmissionType.GUILLOTINE: {
        "attempt": [
            "{actor} wraps up the guillotine!",
            "Guillotine attempt from {actor}!",
        ],
        "locked": [
            "{actor} is cranking on that guillotine!",
        ],
        "escaped": [
            "{target} pops the head free!",
        ],
        "finish": [
            "IT'S OVER! Guillotine choke!",
        ]
    },
    SubmissionType.TRIANGLE_CHOKE: {
        "attempt": [
            "{actor} throws up the triangle!",
            "Triangle locked! {target} is in trouble!",
        ],
        "locked": [
            "{actor} is squeezing tight on that triangle!",
        ],
        "escaped": [
            "{target} stacks and escapes!",
        ],
        "finish": [
            "TAP! Triangle choke gets the finish!",
        ]
    },
    SubmissionType.ARMBAR: {
        "attempt": [
            "{actor} goes for the armbar!",
            "Armbar attempt! The arm is extended!",
        ],
        "locked": [
            "{actor} has the arm fully extended!",
            "The armbar is locked in tight!",
        ],
        "escaped": [
            "{target} stacks out of the armbar!",
            "{target} rips the arm free!",
        ],
        "finish": [
            "TAP! {actor} gets the armbar!",
            "It's over! Armbar submission!",
        ]
    },
    SubmissionType.KIMURA: {
        "attempt": [
            "{actor} locks up the kimura grip!",
        ],
        "locked": [
            "{actor} is rotating that shoulder!",
        ],
        "finish": [
            "KIMURA! {target} taps to the shoulder lock!",
        ]
    },
    SubmissionType.HEEL_HOOK: {
        "attempt": [
            "{actor} has the heel! This is dangerous!",
            "Heel hook! {target} needs to escape NOW!",
        ],
        "locked": [
            "{actor} is twisting that heel!",
        ],
        "finish": [
            "TAP! Heel hook gets the finish! What technique!",
        ]
    },
}

# Position commentary
POSITION_COMMENTARY = {
    # === DOMINANT POSITIONS ===
    Position.MOUNT: [
        "{actor} is in full mount!",
        "{actor} has mounted {target}!",
        "Mount position for {actor}! This is BAD for {target}!",
        "{actor} takes the mount! Complete control!",
    ],
    Position.BACK_MOUNT: [
        "{actor} has the back with hooks in!",
        "Back control for {actor}! The most dangerous position in MMA!",
        "{actor} has full back mount! The choke is RIGHT THERE!",
        "{actor} takes the back! {target} is in DEEP trouble!",
    ],
    Position.SIDE_CONTROL_TOP: [
        "{actor} settles into side control.",
        "Heavy top pressure from {actor} in side control.",
        "Side control for {actor}. {target} needs to escape.",
        "{actor} has side control. Working for submissions or ground strikes.",
    ],
    Position.NORTH_SOUTH_TOP: [
        "{actor} transitions to north-south.",
        "North-south position! {actor} is smothering {target}.",
        "{actor} in north-south. Kimura is available from here.",
    ],
    Position.CRUCIFIX_TOP: [
        "{actor} has the CRUCIFIX! This is a nightmare position!",
        "CRUCIFIX! {target} cannot defend the strikes!",
        "{actor} traps the arm in the crucifix! Unanswered shots coming!",
    ],
    Position.TURTLE_TOP: [
        "{actor} is on top of {target}'s turtle.",
        "{target} is turtled up. {actor} looking for openings.",
        "Turtle position. {actor} hunting for the back or strikes.",
    ],
    Position.KNOCKDOWN_STANDING: [
        "{actor} standing over {target}! Finish mode!",
        "{target} is down! {actor} looking to finish!",
        "{actor} smells blood! {target} is on the canvas!",
    ],
    
    # === GUARD POSITIONS ===
    Position.FULL_GUARD_TOP: [
        "{actor} is in {target}'s full guard.",
        "Full guard position. {target} controlling from the bottom.",
        "{actor} in the guard. Looking to pass or land strikes.",
    ],
    Position.FULL_GUARD_BOTTOM: [
        "{target} has {actor} in full guard.",
        "Full guard for {target}. Submissions are available.",
    ],
    Position.CLOSED_GUARD_TOP: [
        "{actor} is in {target}'s closed guard.",
        "Closed guard. {target} has the legs locked around {actor}.",
    ],
    Position.CLOSED_GUARD_BOTTOM: [
        "{target} has closed guard. {actor} needs to open the legs to pass.",
    ],
    Position.HALF_GUARD_TOP: [
        "{actor} is in half guard.",
        "Half guard position. {actor} working to pass.",
        "{actor} in the half guard. Looking for the underhook.",
    ],
    Position.HALF_GUARD_BOTTOM: [
        "{target} has half guard. One leg trapped.",
        "Half guard for {target}. Looking to recover full guard or sweep.",
    ],
    Position.BUTTERFLY_GUARD_TOP: [
        "{actor} is in {target}'s butterfly guard.",
        "Butterfly guard. {target} looking for sweeps.",
    ],
    Position.BUTTERFLY_GUARD_BOTTOM: [
        "{target} has butterfly hooks in. Sweep attempts coming.",
    ],
    
    # === CLINCH POSITIONS ===
    Position.CLINCH_DOUBLE_COLLAR: [
        "Thai clinch! {actor} has double collar ties!",
        "Plum position! Knees incoming!",
        "{actor} in the Thai clinch! This is Muay Thai territory!",
    ],
    Position.CLINCH_OVER_UNDER: [
        "Over-under clinch. Both fighters working for position.",
        "{actor} and {target} in the 50-50 clinch.",
    ],
    Position.CLINCH_BODY_LOCK: [
        "{actor} has a body lock! Takedown coming!",
        "Bear hug from {actor}! Looking to take this to the mat!",
    ],
    Position.CLINCH_CAGE: [
        "Clinched up against the cage.",
        "Cage clinch. Dirty boxing and knees available.",
        "Working in the clinch against the fence.",
    ],
    
    # === LEG ENTANGLEMENT POSITIONS ===
    Position.SINGLE_LEG_X: [
        "{actor} has single leg X! Heel hook danger!",
        "Ashi garami for {actor}! The leg is trapped!",
    ],
    Position.FIFTY_FIFTY: [
        "Fifty-fifty position! Both fighters can attack!",
        "50-50 guard. Leg lock battle brewing.",
    ],
    Position.INSIDE_SANKAKU: [
        "{actor} in the inside sankaku! Honey hole position!",
        "Inside heel hook position! This is DANGEROUS!",
    ],
    Position.TRUCK: [
        "{actor} has the truck! Twister or back take available!",
        "Truck position! {target} is in trouble!",
    ],
    
    # === FRONT HEADLOCK POSITIONS ===
    Position.FRONT_HEADLOCK: [
        "{actor} has a front headlock. Guillotine available.",
        "Front headlock position. D'arce and anaconda are there.",
    ],
    
    # === STANDING POSITIONS (for completeness) ===
    Position.STANDING_OPEN: [
        "Back on the feet. Open stance.",
        "Both fighters standing. Center of the cage.",
    ],
    Position.STANDING_CAGE: [
        "Backed up against the cage.",
        "Fighting near the fence.",
    ],
}

# Knockdown commentary
KNOCKDOWN_COMMENTARY = [
    "{actor} DROPS {target}!",
    "DOWN GOES {target}!",
    "{target} IS HURT AND DOWN!",
    "KNOCKDOWN! {actor} scores a huge knockdown!",
    "{target} hits the canvas! {actor} smells blood!",
    "HUGE shot puts {target} on the mat!",
]

# Finish commentary
FINISH_COMMENTARY = {
    "KO": [
        "IT'S ALL OVER! {actor} wins by KNOCKOUT!",
        "SPECTACULAR KO! {actor} finishes {target}!",
        "{target} IS OUT! What a knockout by {actor}!",
        "THE REFEREE HAS SEEN ENOUGH! KO victory for {actor}!",
    ],
    "TKO": [
        "THE REFEREE STOPS IT! TKO victory for {actor}!",
        "{actor} finishes {target} by TKO!",
        "STOPPAGE! {actor} wins by TKO!",
        "The referee jumps in! It's over! TKO!",
    ],
}

# Round announcements
ROUND_START_COMMENTARY = [
    "Round {round_num} begins!",
    "Here we go, round {round_num}!",
    "Round {round_num} is underway.",
    "Touching gloves as round {round_num} starts.",
]

ROUND_END_COMMENTARY = [
    "That's the horn! End of round {round_num}.",
    "Round {round_num} comes to a close.",
    "The horn sounds to end round {round_num}.",
]

# ============================================================================
# CORNER DIALOGUE TEMPLATES
# ============================================================================

CORNER_ADVICE_WINNING = [
    'CORNER: "You\'re up on the cards! Stay smart, don\'t get wild!"',
    'CORNER: "Beautiful work! Keep doing what you\'re doing!"',
    'CORNER: "You\'re winning this fight! Control the center!"',
    'CORNER: "Great round! Stay disciplined, stick to the game plan!"',
    'CORNER: "You\'re in control! Don\'t let him back in this!"',
]

CORNER_ADVICE_LOSING = [
    'CORNER: "You need to DIG! This fight is slipping away!"',
    'CORNER: "More aggression! You need to let your hands go!"',
    'CORNER: "You\'re behind! It\'s now or never!"',
    'CORNER: "We need a big round! Show me some urgency!"',
    'CORNER: "Pick up the pace! You\'ve got to take this round!"',
]

CORNER_ADVICE_CLOSE = [
    'CORNER: "This fight is CLOSE! Win this next round clearly!"',
    'CORNER: "Could go either way! Make a statement this round!"',
    'CORNER: "Judges have it tight! Leave no doubt!"',
    'CORNER: "Big round coming up! Take it to him!"',
]

CORNER_ADVICE_STRIKER_VS_GRAPPLER = [
    'CORNER: "Keep it standing! Don\'t let him grab you!"',
    'CORNER: "Stuff the takedowns and light him up!"',
    'CORNER: "Circle off the cage! Stay in the center!"',
]

CORNER_ADVICE_GRAPPLER_VS_STRIKER = [
    'CORNER: "Get inside and take him DOWN!"',
    'CORNER: "Close the distance! Get to the clinch!"',
    'CORNER: "Don\'t trade with him! Take the fight to the mat!"',
]

CORNER_ADVICE_HURT_FIGHTER = [
    'CORNER: "Breathe! Clear your head! You\'re okay!"',
    'CORNER: "Move! Don\'t let him close the distance!"',
    'CORNER: "You survived! Now show him you\'re still in this!"',
]

CORNER_ADVICE_DOMINANT = [
    'CORNER: "You\'re breaking him! Keep the pressure on!"',
    'CORNER: "He\'s fading! Finish this!"',
    'CORNER: "Don\'t let him off the hook! Pour it on!"',
]

ROUND_TRANSITION_COMMENTARY = [
    "The coaches are working frantically in the corner!",
    "Both fighters catch their breath as the corners give instructions.",
    "60 seconds to recover before we go again.",
    "The cutman is working while the coach delivers instructions.",
]


# ============================================================================
# COMMENTARY ENGINE
# ============================================================================

class CommentaryEngine:
    """
    Generates play-by-play and color commentary for fights.
    """
    
    def __init__(
        self,
        fighter1: FighterAttributes,
        fighter2: FighterAttributes,
        verbose: bool = True
    ):
        self.fighter1 = fighter1
        self.fighter2 = fighter2
        self.verbose = verbose
        
        # Event tracking
        self.events: List[FightEvent] = []
        self.round_summaries: List[RoundSummary] = []
        
        # Current state
        self.current_round = 0
        self.current_exchange = 0
        self.last_significant_event: Optional[FightEvent] = None
        
        # Commentary log
        self.commentary_log: List[str] = []
        
        # Momentum tracking
        self.momentum: Dict[str, float] = {
            fighter1.fighter_id: 50.0,
            fighter2.fighter_id: 50.0
        }
        
        # Combination tracking
        self._combo_count = 0
        self._last_striker = None
    
    def get_fighter_name(self, fighter_id: str) -> str:
        """Get fighter name from ID"""
        if fighter_id == self.fighter1.fighter_id:
            return self.fighter1.name
        return self.fighter2.name
    
    def get_time_str(self, exchange: int, exchanges_per_round: int = 25) -> str:
        """Convert exchange number to time string"""
        total_seconds = int((exchange / exchanges_per_round) * 300)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def log_round_start(self, round_num: int) -> FightEvent:
        """Log the start of a round"""
        self.current_round = round_num
        self.current_exchange = 0
        
        commentary = random.choice(ROUND_START_COMMENTARY).format(round_num=round_num)
        
        event = FightEvent(
            event_type=FightEventType.ROUND_START,
            round_num=round_num,
            exchange_num=0,
            time_str="0:00",
            actor_id="",
            actor_name="",
            commentary=commentary,
            significance=EventSignificance.NOTABLE
        )
        
        self.events.append(event)
        self._add_commentary(commentary)
        
        return event
    
    def log_round_end(
        self,
        round_num: int,
        stats1: RoundStats,
        stats2: RoundStats,
        score1: int,
        score2: int
    ) -> RoundSummary:
        """Log the end of a round and create summary with corner dialogue"""
        commentary = random.choice(ROUND_END_COMMENTARY).format(round_num=round_num)
        
        event = FightEvent(
            event_type=FightEventType.ROUND_END,
            round_num=round_num,
            exchange_num=self.current_exchange,
            time_str="5:00",
            actor_id="",
            actor_name="",
            commentary=commentary,
            significance=EventSignificance.NOTABLE
        )
        
        self.events.append(event)
        self._add_commentary(commentary)
        
        # Create round summary
        winner_id = None
        if score1 > score2:
            winner_id = self.fighter1.fighter_id
        elif score2 > score1:
            winner_id = self.fighter2.fighter_id
        
        summary = RoundSummary(
            round_num=round_num,
            fighter1_stats=stats1,
            fighter2_stats=stats2,
            fighter1_score=score1,
            fighter2_score=score2,
            round_winner_id=winner_id
        )
        
        # Add key events from this round
        for e in self.events:
            if e.round_num == round_num:
                summary.add_key_event(e)
        
        summary.generate_description(self.fighter1.name, self.fighter2.name)
        self.round_summaries.append(summary)
        
        # Add round summary commentary
        self._add_commentary(f"[Round {round_num}: {summary.round_description}]")
        
        # Generate corner dialogue (not for final round)
        corner_dialogue = self._generate_corner_dialogue(round_num, score1, score2)
        if corner_dialogue:
            self._add_commentary(corner_dialogue)
        
        return summary
    
    def _generate_corner_dialogue(
        self,
        round_num: int,
        this_round_score1: int,
        this_round_score2: int
    ) -> str:
        """Generate corner advice between rounds based on fight state.
        
        Shows the losing corner's advice (more dramatic/urgent).
        Returns empty string for final round (no next round to prepare for).
        """
        # Don't generate corner dialogue after round 3+ (likely final round)
        if round_num >= 3:
            return ""
        
        # Calculate cumulative scores
        total_score1 = sum(s.fighter1_score for s in self.round_summaries)
        total_score2 = sum(s.fighter2_score for s in self.round_summaries)
        
        # Determine fight state
        score_diff = total_score1 - total_score2
        
        dialogue_lines = []
        
        # Add transition line
        dialogue_lines.append(random.choice(ROUND_TRANSITION_COMMENTARY))
        
        # Generate corner advice - prioritize showing the losing corner (more dramatic)
        if abs(score_diff) <= 1:
            # Close fight - urgent advice
            dialogue_lines.append(random.choice(CORNER_ADVICE_CLOSE))
        elif abs(score_diff) >= 3:
            # Dominant performance - show losing corner's desperation
            dialogue_lines.append(random.choice(CORNER_ADVICE_LOSING))
            dialogue_lines.append(random.choice(CORNER_ADVICE_DOMINANT))
        else:
            # One fighter ahead - show losing corner's advice
            dialogue_lines.append(random.choice(CORNER_ADVICE_LOSING))
        
        return "\n".join(dialogue_lines)
    
    def log_strike(
        self,
        attacker_id: str,
        target_id: str,
        strike: StrikeType,
        landed: bool,
        damage: float,
        was_counter: bool = False,
        caused_knockdown: bool = False,
        caused_rock: bool = False,
        exchange_num: int = 0
    ) -> FightEvent:
        """Log a strike attempt"""
        self.current_exchange = exchange_num
        
        attacker_name = self.get_fighter_name(attacker_id)
        target_name = self.get_fighter_name(target_id)
        
        # Determine significance
        significance = EventSignificance.ROUTINE
        if caused_knockdown:
            significance = EventSignificance.DRAMATIC
        elif caused_rock:
            significance = EventSignificance.SIGNIFICANT
        elif damage > 12:
            significance = EventSignificance.SIGNIFICANT
        elif damage > 8:
            significance = EventSignificance.NOTABLE
        
        # Generate commentary
        commentary = self._generate_strike_commentary(
            strike, attacker_name, target_name, landed, damage, 
            was_counter, caused_knockdown, caused_rock
        )
        
        event_type = FightEventType.STRIKE_LANDED if landed else FightEventType.STRIKE_MISSED
        if was_counter:
            event_type = FightEventType.COUNTER_STRIKE
        if caused_knockdown:
            event_type = FightEventType.KNOCKDOWN
        
        event = FightEvent(
            event_type=event_type,
            round_num=self.current_round,
            exchange_num=exchange_num,
            time_str=self.get_time_str(exchange_num),
            actor_id=attacker_id,
            actor_name=attacker_name,
            target_id=target_id,
            target_name=target_name,
            action=strike.value,
            success=landed,
            damage=damage,
            significance=significance,
            commentary=commentary
        )
        
        self.events.append(event)
        
        if significance.value >= EventSignificance.NOTABLE.value:
            self._add_commentary(commentary)
            self.last_significant_event = event
        
        # Track combinations
        if landed and attacker_id == self._last_striker:
            self._combo_count += 1
            if self._combo_count == 3:
                self._add_commentary(f"{attacker_name} is putting together combinations!")
        else:
            self._combo_count = 1 if landed else 0
            self._last_striker = attacker_id if landed else None
        
        return event
    
    def log_takedown(
        self,
        attacker_id: str,
        target_id: str,
        action: GrapplingAction,
        success: bool,
        new_position: Optional[Position] = None,
        exchange_num: int = 0
    ) -> FightEvent:
        """Log a takedown attempt"""
        attacker_name = self.get_fighter_name(attacker_id)
        target_name = self.get_fighter_name(target_id)
        
        significance = EventSignificance.SIGNIFICANT if success else EventSignificance.NOTABLE
        
        # Generate commentary
        commentary = self._generate_grappling_commentary(
            action, attacker_name, target_name, success
        )
        
        event_type = FightEventType.TAKEDOWN_SUCCESS if success else FightEventType.TAKEDOWN_STUFFED
        
        event = FightEvent(
            event_type=event_type,
            round_num=self.current_round,
            exchange_num=exchange_num,
            time_str=self.get_time_str(exchange_num),
            actor_id=attacker_id,
            actor_name=attacker_name,
            target_id=target_id,
            target_name=target_name,
            action=action.value,
            success=success,
            new_position=new_position,
            significance=significance,
            commentary=commentary
        )
        
        self.events.append(event)
        self._add_commentary(commentary)
        
        return event
    
    def log_position_change(
        self,
        actor_id: str,
        action: GrapplingAction,
        old_position: Position,
        new_position: Position,
        exchange_num: int = 0
    ) -> FightEvent:
        """Log a position change"""
        actor_name = self.get_fighter_name(actor_id)
        target_id = self.fighter2.fighter_id if actor_id == self.fighter1.fighter_id else self.fighter1.fighter_id
        target_name = self.get_fighter_name(target_id)
        
        # Determine significance based on position
        significance = EventSignificance.NOTABLE
        if new_position in DOMINANT_POSITIONS:
            significance = EventSignificance.SIGNIFICANT
        
        commentary = self._generate_grappling_commentary(
            action, actor_name, target_name, True
        )
        
        event = FightEvent(
            event_type=FightEventType.POSITION_ADVANCE,
            round_num=self.current_round,
            exchange_num=exchange_num,
            time_str=self.get_time_str(exchange_num),
            actor_id=actor_id,
            actor_name=actor_name,
            target_id=target_id,
            target_name=target_name,
            action=action.value,
            success=True,
            position=old_position,
            new_position=new_position,
            significance=significance,
            commentary=commentary
        )
        
        self.events.append(event)
        self._add_commentary(commentary)
        
        # Add position description
        if new_position in POSITION_COMMENTARY:
            pos_comment = random.choice(POSITION_COMMENTARY[new_position])
            self._add_commentary(pos_comment.format(actor=actor_name, target=target_name))
        
        return event
    
    def log_submission_attempt(
        self,
        attacker_id: str,
        target_id: str,
        submission: SubmissionType,
        stage: str,  # "attempt", "locked", "escaped", "finish"
        exchange_num: int = 0
    ) -> FightEvent:
        """Log a submission attempt or outcome"""
        attacker_name = self.get_fighter_name(attacker_id)
        target_name = self.get_fighter_name(target_id)
        
        significance = EventSignificance.SIGNIFICANT
        if stage == "finish":
            significance = EventSignificance.DRAMATIC
        elif stage == "locked":
            significance = EventSignificance.SIGNIFICANT
        
        event_type = {
            "attempt": FightEventType.SUBMISSION_ATTEMPT,
            "locked": FightEventType.SUBMISSION_LOCKED,
            "escaped": FightEventType.SUBMISSION_ESCAPE,
            "finish": FightEventType.SUBMISSION_FINISH
        }.get(stage, FightEventType.SUBMISSION_ATTEMPT)
        
        # Generate commentary
        commentary = self._generate_submission_commentary(
            submission, attacker_name, target_name, stage
        )
        
        event = FightEvent(
            event_type=event_type,
            round_num=self.current_round,
            exchange_num=exchange_num,
            time_str=self.get_time_str(exchange_num),
            actor_id=attacker_id,
            actor_name=attacker_name,
            target_id=target_id,
            target_name=target_name,
            action=submission.value,
            success=(stage != "escaped"),
            significance=significance,
            commentary=commentary
        )
        
        self.events.append(event)
        self._add_commentary(commentary)
        
        return event
    
    def log_knockdown(
        self,
        attacker_id: str,
        target_id: str,
        strike: StrikeType,
        exchange_num: int = 0
    ) -> FightEvent:
        """Log a knockdown"""
        attacker_name = self.get_fighter_name(attacker_id)
        target_name = self.get_fighter_name(target_id)
        
        commentary = random.choice(KNOCKDOWN_COMMENTARY).format(
            actor=attacker_name, target=target_name
        )
        
        event = FightEvent(
            event_type=FightEventType.KNOCKDOWN,
            round_num=self.current_round,
            exchange_num=exchange_num,
            time_str=self.get_time_str(exchange_num),
            actor_id=attacker_id,
            actor_name=attacker_name,
            target_id=target_id,
            target_name=target_name,
            action=strike.value,
            success=True,
            significance=EventSignificance.DRAMATIC,
            commentary=commentary
        )
        
        self.events.append(event)
        self._add_commentary(commentary)
        
        return event
    
    def log_finish(
        self,
        winner_id: str,
        loser_id: str,
        method: str,
        round_num: int,
        exchange_num: int
    ) -> FightEvent:
        """Log a fight finish"""
        winner_name = self.get_fighter_name(winner_id)
        loser_name = self.get_fighter_name(loser_id)
        
        if "KO" in method and "TKO" not in method:
            commentary = random.choice(FINISH_COMMENTARY["KO"])
            event_type = FightEventType.KO_FINISH
        elif "TKO" in method:
            commentary = random.choice(FINISH_COMMENTARY["TKO"])
            event_type = FightEventType.TKO_FINISH
        else:
            commentary = f"{winner_name} wins by {method}!"
            event_type = FightEventType.SUBMISSION_WIN
        
        commentary = commentary.format(actor=winner_name, target=loser_name)
        
        event = FightEvent(
            event_type=event_type,
            round_num=round_num,
            exchange_num=exchange_num,
            time_str=self.get_time_str(exchange_num),
            actor_id=winner_id,
            actor_name=winner_name,
            target_id=loser_id,
            target_name=loser_name,
            action=method,
            success=True,
            significance=EventSignificance.HISTORIC,
            commentary=commentary
        )
        
        self.events.append(event)
        self._add_commentary(f"\n*** {commentary} ***\n")
        
        return event
    
    def log_decision(
        self,
        winner_id: Optional[str],
        decision_type: str,
        scores: List[Tuple[int, int]]
    ) -> FightEvent:
        """Log a decision outcome"""
        if winner_id:
            winner_name = self.get_fighter_name(winner_id)
            loser_id = self.fighter2.fighter_id if winner_id == self.fighter1.fighter_id else self.fighter1.fighter_id
            loser_name = self.get_fighter_name(loser_id)
            
            score_str = ", ".join([f"{s1}-{s2}" for s1, s2 in scores])
            commentary = f"After {len(self.round_summaries)} rounds, we go to the judges' scorecards... "
            commentary += f"({score_str})... Your winner by {decision_type} Decision... {winner_name}!"
        else:
            score_str = ", ".join([f"{s1}-{s2}" for s1, s2 in scores])
            commentary = f"This fight is declared a DRAW! ({score_str})"
            winner_name = "Draw"
            loser_name = ""
            loser_id = ""
        
        event = FightEvent(
            event_type=FightEventType.DECISION,
            round_num=self.current_round,
            exchange_num=self.current_exchange,
            time_str="5:00",
            actor_id=winner_id or "",
            actor_name=winner_name,
            target_id=loser_id,
            target_name=loser_name,
            action=f"{decision_type} Decision",
            success=True,
            significance=EventSignificance.HISTORIC,
            commentary=commentary
        )
        
        self.events.append(event)
        self._add_commentary(f"\n*** {commentary} ***\n")
        
        return event
    
    def _generate_strike_commentary(
        self,
        strike: StrikeType,
        attacker: str,
        target: str,
        landed: bool,
        damage: float,
        was_counter: bool,
        caused_knockdown: bool,
        caused_rock: bool
    ) -> str:
        """Generate commentary for a strike"""
        templates = STRIKE_TEMPLATES.get(strike, {})
        
        if caused_knockdown:
            return random.choice(KNOCKDOWN_COMMENTARY).format(actor=attacker, target=target)
        
        if caused_rock:
            if "significant" in templates:
                return random.choice(templates["significant"]).format(actor=attacker, target=target)
            return f"{attacker} ROCKS {target}!"
        
        if landed:
            if damage > 10 and "significant" in templates:
                return random.choice(templates["significant"]).format(actor=attacker, target=target)
            if "landed" in templates:
                return random.choice(templates["landed"]).format(actor=attacker, target=target)
            return f"{attacker} lands a {strike.value.replace('_', ' ')}."
        else:
            if "missed" in templates:
                return random.choice(templates["missed"]).format(actor=attacker, target=target)
            return f"{attacker} misses with the {strike.value.replace('_', ' ')}."
    
    def _generate_grappling_commentary(
        self,
        action: GrapplingAction,
        attacker: str,
        target: str,
        success: bool
    ) -> str:
        """Generate commentary for grappling"""
        templates = GRAPPLING_TEMPLATES.get(action, {})
        
        if success:
            if "success" in templates:
                return random.choice(templates["success"]).format(actor=attacker, target=target)
            return f"{attacker} completes the {action.value.replace('_', ' ')}."
        else:
            if "failed" in templates:
                return random.choice(templates["failed"]).format(actor=attacker, target=target)
            return f"{target} defends the {action.value.replace('_', ' ')}."
    
    def _generate_submission_commentary(
        self,
        submission: SubmissionType,
        attacker: str,
        target: str,
        stage: str
    ) -> str:
        """Generate commentary for submissions"""
        templates = SUBMISSION_TEMPLATES.get(submission, {})
        
        if stage in templates:
            return random.choice(templates[stage]).format(actor=attacker, target=target)
        
        sub_name = submission.value.replace("_", " ").title()
        if stage == "attempt":
            return f"{attacker} is going for the {sub_name}!"
        elif stage == "locked":
            return f"{attacker} has the {sub_name} locked in!"
        elif stage == "escaped":
            return f"{target} escapes the {sub_name}!"
        else:
            return f"{attacker} gets the tap with the {sub_name}!"
    
    def _add_commentary(self, text: str) -> None:
        """Add commentary to the log"""
        if self.verbose:
            self.commentary_log.append(text)
    
    def get_full_commentary(self) -> str:
        """Get the complete commentary as a string"""
        return "\n".join(self.commentary_log)
    
    def get_key_moments(self) -> List[FightEvent]:
        """Get all significant events from the fight"""
        return [
            e for e in self.events 
            if e.significance.value >= EventSignificance.SIGNIFICANT.value
        ]
    
    def get_fight_summary(self) -> Dict[str, Any]:
        """Get complete fight summary"""
        return {
            "rounds": [s.to_dict() for s in self.round_summaries],
            "key_moments": [e.to_dict() for e in self.get_key_moments()],
            "total_events": len(self.events),
            "commentary_lines": len(self.commentary_log)
        }


# ============================================================================
# INTEGRATED ROUND SIMULATOR
# ============================================================================

def simulate_round_with_commentary(
    fighter1: FighterAttributes,
    fighter2: FighterAttributes,
    fighter1_state: FighterState,
    fighter2_state: FighterState,
    fight_state: FightState,
    round_num: int,
    exchanges_per_round: int,
    commentary: CommentaryEngine
) -> Tuple[Optional[Tuple[str, str]], RoundStats, RoundStats]:
    """
    Simulate a single round with full commentary.
    
    Returns:
        (finish_result, f1_stats, f2_stats) where finish_result is None
        if the round completed normally, or (winner_id, method) if finished.
    """
    from simulation.fight_engine import (
        simulate_exchange, RoundStats, FightConfig
    )
    
    commentary.log_round_start(round_num)
    
    round_stats = {
        fighter1.fighter_id: RoundStats(),
        fighter2.fighter_id: RoundStats()
    }
    
    config = FightConfig()
    
    for exchange in range(1, exchanges_per_round + 1):
        result = simulate_exchange(
            fighter1, fighter2,
            fighter1_state, fighter2_state,
            fight_state, config,
            round_stats
        )
        
        if result:
            winner_id, method = result
            commentary.log_finish(
                winner_id,
                fighter2.fighter_id if winner_id == fighter1.fighter_id else fighter1.fighter_id,
                method,
                round_num,
                exchange
            )
            return (result, round_stats[fighter1.fighter_id], round_stats[fighter2.fighter_id])
    
    # Round completed - score it
    from simulation.fight_engine import score_round
    
    s1, s2 = score_round(
        round_stats[fighter1.fighter_id],
        round_stats[fighter2.fighter_id],
        fighter1_state.knockdowns_this_round,
        fighter2_state.knockdowns_this_round
    )
    
    commentary.log_round_end(
        round_num,
        round_stats[fighter1.fighter_id],
        round_stats[fighter2.fighter_id],
        s1, s2
    )
    
    return (None, round_stats[fighter1.fighter_id], round_stats[fighter2.fighter_id])


# ============================================================================
# POST-FIGHT ANALYSIS
# ============================================================================

@dataclass
class FightAnalysis:
    """Post-fight analysis and narrative"""
    winner_id: Optional[str]
    winner_name: str
    loser_name: str
    method: str
    
    # Key stats
    total_strikes_landed: Dict[str, int] = field(default_factory=dict)
    takedowns_landed: Dict[str, int] = field(default_factory=dict)
    control_time: Dict[str, float] = field(default_factory=dict)
    knockdowns: Dict[str, int] = field(default_factory=dict)
    
    # Narrative elements
    key_moments: List[str] = field(default_factory=list)
    turning_point: Optional[str] = None
    fight_of_night_worthy: bool = False
    performance_bonus_worthy: bool = False
    
    def generate_narrative(self) -> str:
        """Generate a narrative summary of the fight"""
        lines = []
        
        if self.winner_id:
            lines.append(f"{self.winner_name} defeated {self.loser_name} by {self.method}.")
        else:
            lines.append(f"The fight between {self.winner_name} and {self.loser_name} ended in a draw.")
        
        # Add key moments
        if self.key_moments:
            lines.append("\nKey moments:")
            for moment in self.key_moments[:5]:
                lines.append(f"  ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ {moment}")
        
        # Stats summary
        if self.winner_id and self.winner_id in self.total_strikes_landed:
            winner_strikes = self.total_strikes_landed.get(self.winner_id, 0)
            winner_td = self.takedowns_landed.get(self.winner_id, 0)
            winner_kd = self.knockdowns.get(self.winner_id, 0)
            
            stat_parts = []
            if winner_strikes > 20:
                stat_parts.append(f"{winner_strikes} significant strikes")
            if winner_td > 0:
                stat_parts.append(f"{winner_td} takedowns")
            if winner_kd > 0:
                stat_parts.append(f"{winner_kd} knockdowns")
            
            if stat_parts:
                lines.append(f"\n{self.winner_name} landed {', '.join(stat_parts)}.")
        
        if self.turning_point:
            lines.append(f"\nTurning point: {self.turning_point}")
        
        if self.fight_of_night_worthy:
            lines.append("\nÃƒÂ°Ã…Â¸Ã‚ÂÃ¢â‚¬Â  This fight is a candidate for Fight of the Night!")
        
        if self.performance_bonus_worthy:
            lines.append(f"\nÃƒÂ°Ã…Â¸Ã‚ÂÃ¢â‚¬Â  {self.winner_name} is a candidate for Performance of the Night!")
        
        return "\n".join(lines)


def analyze_fight(
    commentary: CommentaryEngine,
    winner_id: Optional[str],
    method: str
) -> FightAnalysis:
    """Generate post-fight analysis from commentary data"""
    
    winner_name = commentary.get_fighter_name(winner_id) if winner_id else "N/A"
    loser_id = (
        commentary.fighter2.fighter_id 
        if winner_id == commentary.fighter1.fighter_id 
        else commentary.fighter1.fighter_id
    ) if winner_id else None
    loser_name = commentary.get_fighter_name(loser_id) if loser_id else "N/A"
    
    # Aggregate stats
    total_strikes = {commentary.fighter1.fighter_id: 0, commentary.fighter2.fighter_id: 0}
    takedowns = {commentary.fighter1.fighter_id: 0, commentary.fighter2.fighter_id: 0}
    control = {commentary.fighter1.fighter_id: 0.0, commentary.fighter2.fighter_id: 0.0}
    knockdowns = {commentary.fighter1.fighter_id: 0, commentary.fighter2.fighter_id: 0}
    
    for summary in commentary.round_summaries:
        total_strikes[commentary.fighter1.fighter_id] += summary.fighter1_stats.significant_strikes_landed
        total_strikes[commentary.fighter2.fighter_id] += summary.fighter2_stats.significant_strikes_landed
        takedowns[commentary.fighter1.fighter_id] += summary.fighter1_stats.takedowns_landed
        takedowns[commentary.fighter2.fighter_id] += summary.fighter2_stats.takedowns_landed
        control[commentary.fighter1.fighter_id] += summary.fighter1_stats.control_time
        control[commentary.fighter2.fighter_id] += summary.fighter2_stats.control_time
    
    # Count knockdowns from events
    for event in commentary.events:
        if event.event_type == FightEventType.KNOCKDOWN:
            knockdowns[event.actor_id] = knockdowns.get(event.actor_id, 0) + 1
    
    # Extract key moments
    key_moments = []
    for event in commentary.get_key_moments():
        if event.commentary:
            key_moments.append(event.commentary)
    
    # Find turning point
    turning_point = None
    for event in commentary.events:
        if event.significance == EventSignificance.DRAMATIC:
            turning_point = event.commentary
            break
    
    # Determine bonuses
    total_action = sum(total_strikes.values()) + sum(knockdowns.values()) * 10
    fight_of_night = total_action > 60 and len(commentary.round_summaries) >= 3
    
    performance_bonus = False
    if winner_id:
        winner_kd = knockdowns.get(winner_id, 0)
        if winner_kd >= 2 or "KO" in method or "Submission" in method:
            if len(commentary.round_summaries) <= 2:  # Early finish
                performance_bonus = True
    
    return FightAnalysis(
        winner_id=winner_id,
        winner_name=winner_name,
        loser_name=loser_name,
        method=method,
        total_strikes_landed=total_strikes,
        takedowns_landed=takedowns,
        control_time=control,
        knockdowns=knockdowns,
        key_moments=key_moments,
        turning_point=turning_point,
        fight_of_night_worthy=fight_of_night,
        performance_bonus_worthy=performance_bonus
    )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_commentary_engine(
    fighter1: FighterAttributes,
    fighter2: FighterAttributes,
    verbose: bool = True
) -> CommentaryEngine:
    """Create a new commentary engine for a fight"""
    return CommentaryEngine(fighter1, fighter2, verbose)


def get_round_summary(
    commentary: CommentaryEngine,
    round_num: int
) -> Optional[RoundSummary]:
    """Get summary for a specific round"""
    for summary in commentary.round_summaries:
        if summary.round_num == round_num:
            return summary
    return None
