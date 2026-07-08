# narrative/commentary.py
# Module 15: Enhanced Commentary System
# Lines: ~1,400
#
# Building intelligent system ON TOP of comprehensive templates
# Keeps all original templates, completes the FightCommentarySystem

"""
Cage Dynasty - Enhanced Commentary System

This module provides:
- Comprehensive commentary templates for ALL fight actions
- Intelligent context-aware commentary generation
- Event logging and round tracking
- Post-fight narrative generation
- Integration with fight engine
"""

import random
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto

# --- FORWARD-REFERENCING ---
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from entities.fighter import Fighter

# ============================================================================
# FIGHT INTRO & ANNOUNCEMENT TEMPLATES (Buffer-Style)
# ============================================================================

FIGHT_INTRO_OPENING = [
    "Ladies and gentlemen... THIS IS THE MAIN EVENT OF THE EVENING!",
    "Ladies and gentlemen, we are LIVE for another incredible night of mixed martial arts!",
    "The moment you've all been waiting for... IT'S FIGHT TIME!",
    "Welcome to the Dynasty Fighting Championship! Let's get ready to RUMBLE!",
    "The cage is set, the fighters are ready... LET'S DO THIS!",
    "Fans, it's time for what you came here to see! CHAMPIONSHIP FIGHTING!",
]

FIGHT_INTRO_TITLE_OPENING = [
    "LLLLLADIES AND GENTLEMEN! THIS... IS... THE MAIN EVENT OF THE EVENING!",
    "It's CHAMPIONSHIP time! The gold is on the line!",
    "This is what it's all about! The DFC Championship is up for grabs!",
    "Championship rounds, championship stakes! Here we GO!",
    "The biggest fight of the night! TITLE ON THE LINE!",
]

FIGHTER_INTRO_RED_CORNER = [
    "Introducing first, fighting out of the RED corner...",
    "In the red corner, making his way to the octagon...",
    "From the red corner, the challenger...",
    "Red corner ready! Standing tall...",
]

FIGHTER_INTRO_BLUE_CORNER = [
    "And his opponent, fighting out of the BLUE corner...",
    "In the blue corner, the opposition...",
    "From the blue corner...",
    "Blue corner! The man looking to make a statement tonight...",
]

FIGHTER_INTRO_CHAMPION = [
    "THE REIGNING, DEFENDING, UNDISPUTED DFC {division} CHAMPION OF THE WORLD...",
    "Your current DFC {division} champion...",
    "The defending champion, putting the gold on the line...",
    "Holding the prestigious DFC {division} title...",
]

FIGHTER_INTRO_RECORD = [
    "Holding a professional record of {wins} wins, {losses} losses...",
    "With a record of {wins} and {losses}...",
    "Standing at {wins}-{losses} in professional competition...",
    "Boasting an impressive {wins}-{losses} record...",
]

FIGHTER_INTRO_STYLE_TAGS = {
    "Striker": [
        "Known for his devastating knockout power...",
        "A pure striker with hands of stone...",
        "The knockout artist...",
        "Heavy hands and bad intentions...",
    ],
    "Counter Striker": [
        "The patient assassin who counters everything...",
        "A timing specialist with sniper-like precision...",
        "The counter-puncher extraordinaire...",
    ],
    "Pressure Fighter": [
        "A relentless pressure machine...",
        "Coming forward with non-stop aggression...",
        "The human freight train...",
    ],
    "Wrestler": [
        "An absolute monster on the mat...",
        "Division I wrestling pedigree on full display...",
        "The human blanket who smothers opponents...",
        "Ground control specialist...",
    ],
    "BJJ Specialist": [
        "A submission wizard on the ground...",
        "Black belt in Brazilian Jiu-Jitsu...",
        "The human pretzel maker...",
        "Submission artist with infinite tricks...",
    ],
    "Ground and Pound": [
        "Known for vicious ground and pound...",
        "Takes you down and beats you up...",
        "The ground-and-pound specialist...",
    ],
    "Muay Thai": [
        "A Muay Thai destroyer in the clinch...",
        "Elbows and knees for days...",
        "The Thai violence specialist...",
    ],
    "Balanced": [
        "A complete mixed martial artist...",
        "Well-rounded in all aspects of the game...",
        "Dangerous everywhere the fight goes...",
    ],
}

FIGHTER_INTRO_NICKNAME_STYLE = [
    '"{nickname}"',
    'They call him "{nickname}"...',
    'Known to fans as "{nickname}"...',
]

FIGHTER_INTRO_LOCATION = [
    "Fighting out of {location}...",
    "Representing {location}...",
    "Hailing from {location}...",
    "Training out of {location}...",
]

FIGHT_INTRO_CLOSING = [
    "WHEN YOU'RE READY, REFEREE... LET'S GET IT ON!",
    "Touch gloves if you want, protect yourselves at all times... FIGHT!",
    "This is going to be ELECTRIC! HERE WE GO!",
    "The cage door is locked! It's GO TIME!",
    "And HERE... WE... GO!",
]

# ============================================================================
# COMMENTARY-ENTRANCES1 — card-position + fighter-entrance pools
# ============================================================================
# Card-position line pools, keyed by slot. One line picked per fight at
# emit_fight_open. Slot is passed in via FightContext.card_slot.
CARD_POSITION_MAIN_EVENT = [
    "This is the MAIN EVENT of the evening. The house lights come down.",
    "Coming up now — your MAIN EVENT. Everything the crowd came for.",
    "The MAIN EVENT is upon us. Prime time.",
    "Time for the MAIN EVENT. All eyes on the cage.",
]

CARD_POSITION_CO_MAIN = [
    "Your co-main event of the evening.",
    "The co-main event is next.",
    "Co-main slot — one fight before the main event.",
    "Time for the co-main.",
]

CARD_POSITION_MAIN_CARD = [
    "Next on the main card.",
    "Main card action continues.",
    "Coming up on the main card.",
    "Main card fight, coming your way.",
]

CARD_POSITION_PRELIM = [
    "Prelim fight, next.",
    "On the prelims — here we go.",
    "Preliminary bout is up.",
    "Prelim card action.",
]

CARD_POSITION_EARLY_PRELIM = [
    "Early prelims underway.",
    "Kicking off the night with an early prelim.",
    "First fight of the night — early prelim.",
]

# Main-event corner intros. Two-line ceiling (one red, one blue).
# {descriptor} folds in champion tag OR a short style-tag OR a safe
# generic default. See FightCommentarySystem._entrance_descriptor.
FIGHTER_ENTRANCE_MAIN_EVENT_RED = [
    "In the red corner — {name}{nick_clause}, {record}, {descriptor}.",
    "Making his way to the cage in red: {name}{nick_clause} — {record}, {descriptor}.",
    "The red corner belongs to {name}{nick_clause} — {record}, {descriptor}.",
]

FIGHTER_ENTRANCE_MAIN_EVENT_BLUE = [
    "And in the blue corner — {name}{nick_clause}, {record}, {descriptor}.",
    "Standing across in blue: {name}{nick_clause} — {record}, {descriptor}.",
    "Blue corner: {name}{nick_clause} — {record}, {descriptor}.",
]

# Co-main: one combined line naming both fighters + records.
FIGHTER_ENTRANCE_CO_MAIN = [
    "{f1_name}{f1_nick} ({f1_rec}) meets {f2_name}{f2_nick} ({f2_rec}) in the co-main.",
    "{f1_name} vs {f2_name} — {f1_rec} against {f2_rec}.",
    "Co-main: {f1_name} ({f1_rec}) faces {f2_name} ({f2_rec}).",
    "Set for the co-main — {f1_name}{f1_nick} takes on {f2_name}{f2_nick}.",
]

# Main-card: one short line.
FIGHTER_ENTRANCE_MAIN_CARD = [
    "{f1_name} takes on {f2_name}.",
    "{f1_name} faces {f2_name} on the main card.",
    "Tonight on the main card: {f1_name} vs {f2_name}.",
]

# Prelim / early-prelim: terse one-liner.
FIGHTER_ENTRANCE_PRELIM = [
    "Red corner {f1_name}, blue corner {f2_name}. Let's go.",
    "{f1_name} vs {f2_name} — prelim card.",
    "In the red corner {f1_name}. In the blue corner {f2_name}.",
]

# Main-event / co-main champion intro. Prepended only when a fighter's
# is_champion flag is set AND division is available. Two-line ceiling
# for main-event entrances is corner intros only — champion line is
# additional (max 3 lines at main_event with a champ present).
FIGHTER_ENTRANCE_CHAMPION_LINE = [
    "{name} carries the DFC {division} title into this one — the belt is on the line.",
    "The reigning DFC {division} champion, {name}, defends tonight.",
    "Wearing the DFC {division} gold: {name}. Defending the strap.",
]

# Short style-tag used inside entrance descriptors. Covers all 11
# canonical fighting_style display_name strings. Missing / unknown
# style → the entrance uses a safe generic descriptor.
_STYLE_ENTRANCE_TAG = {
    "Striker":          "a striker",
    "Counter Striker":  "a counter striker",
    "Pressure Fighter": "a pressure fighter",
    "Point Fighter":    "a point fighter",
    "Muay Thai":        "a Muay Thai specialist",
    "Wrestler":         "a wrestler",
    "Ground & Pound":   "a ground-and-pound specialist",
    "BJJ Specialist":   "a BJJ specialist",
    "Clinch Fighter":   "a clinch fighter",
    "Sprawl & Brawl":   "a sprawl-and-brawler",
    "Balanced":         "a well-rounded fighter",
}


# ============================================================================
# COMMENTARY-GAMEPLAN-CONTRAST1 — style-vs-plan contrast callouts
# ============================================================================
# Three contrast categories, each armed at fight open by comparing a
# fighter's style against their chosen gameplan preset/aggression/
# range_bias. Detection is one-time; the mid-fight callout fires ONCE
# per fighter per fight, tied to a real ActionType event (never on a
# non-event). Balanced style + on-type combinations stay silent —
# that's the AI-SELECT1 intent line's territory.
#
# Guard invariants (locked in Van's Step-0 approval):
#   - Trigger #2 (aggressor-going-patient) requires BOTH forward style
#     AND patient plan. A forward fighter on AGGRESSIVE who happens to
#     STAND_UP/ESCAPE fires nothing — the guard demands the plan itself
#     be patient.
#   - Callouts comment on plan CHOICE, never on winning/losing state.

# Category-1 style set (grapple-based). Category-1 fires when style is
# here AND plan preset is in {AGGRESSIVE, DEFENSIVE} (explicit
# non-grapple direction). Wrestler+MEASURED and other neutral-plan
# cases stay silent per Van's exclude list.
_CONTRAST_GRAPPLE_STYLES = {
    "Wrestler", "BJJ Specialist", "Ground & Pound",
}
_CONTRAST_C1_OFFTYPE_PRESETS = {"AGGRESSIVE", "DEFENSIVE"}

# Category-2 style set (forward stand-up). Category-2 fires when style
# is here AND aggression < 0 (DEFENSIVE/MEASURED — patient plans).
_CONTRAST_FORWARD_STYLES = {
    "Pressure Fighter", "Sprawl & Brawl", "Muay Thai",
    "Clinch Fighter", "Striker",
}

# Category-3 style set (counter/point). Category-3 fires when style is
# here AND aggression > 0 (AGGRESSIVE/GNP/CLINCH — forward plans).
_CONTRAST_COUNTER_STYLES = {"Counter Striker", "Point Fighter"}

# Style label used inside contrast pool templates. Lowercase to flow
# naturally inside sentences that start with "A {label}..." or
# "The {label}...". Balanced omitted — never has contrast.
_CONTRAST_STYLE_LABEL = {
    "Wrestler":          "wrestler",
    "BJJ Specialist":    "BJJ specialist",
    "Ground & Pound":    "ground-and-pound fighter",
    "Pressure Fighter":  "pressure fighter",
    "Sprawl & Brawl":    "sprawl-and-brawler",
    "Muay Thai":         "Muay Thai specialist",
    "Clinch Fighter":    "clinch fighter",
    "Striker":           "striker",
    "Counter Striker":   "counter striker",
    "Point Fighter":     "point fighter",
}

# Mid-fight callout pools. Fire on the actor's first matching trigger
# action (see FightCommentarySystem._maybe_emit_contrast_callout).
# Phrasing invariant: comment on plan choice, never on outcome.
CONTRAST_GRAPPLER_NOT_GRAPPLING = [
    "A {label} content to keep the fight standing? Someone left the takedowns at home.",
    "{name} is a {label} — but the plan tonight is standup. That's a choice.",
    "The takedowns were supposed to be the whole point. {name} is picking a different fight.",
    "A {label} who's decided to trade in the pocket. Not the game he trained for.",
]

CONTRAST_AGGRESSOR_GOING_PATIENT = [
    "A {label}, choosing to hang back? That's not his fight.",
    "{name} is a {label} — coming in patient tonight. Deliberate choice.",
    "The pressure was supposed to be the story. {name} decided to wait instead.",
    "Interesting plan — a {label} playing patient. Out of character.",
]

CONTRAST_COUNTER_BECOMING_AGGRESSOR = [
    "The {label} is forcing the action tonight — out of character.",
    "{name} usually waits. Not tonight — he's the one bringing it.",
    "A {label} planning to be the aggressor? That's the fight he chose.",
    "{name} is stepping outside the counter role. Deliberately.",
]

# Mode-B pre-fight setup pools. Optional "watch for this" line at
# fight open, matched by the same mid-fight callout when the trigger
# fires. Roll happens per-armed-contrast at fight open (~50/50).
CONTRAST_SETUP_GRAPPLER = [
    "One thing to watch: {name} is a {label} with a plan that isn't. See if the takedowns come.",
    "Question mark going in — a {label} on an off-type plan. Watch what he actually goes to.",
    "Watch closely: a {label} with a plan that doesn't match his identity.",
]

CONTRAST_SETUP_PATIENT = [
    "Watch for this: {name} is a {label} coming in patient. Not what we usually see.",
    "A note going in — a {label} choosing measured tonight. Off-brand for him.",
    "One thing to watch — {name} is going against his own aggression on this one.",
]

CONTRAST_SETUP_COUNTER = [
    "Watch for this — the {label} is planning to lead, not counter.",
    "Different look from {name} — a {label} choosing to be the aggressor.",
    "One thing to watch: {name} planning to force the action. Not his usual game.",
]


# ============================================================================
# RIVALRY HEAT COMMENTARY TEMPLATES
# ============================================================================

# Pre-fight heat commentary by heat stage
HEAT_PREFIGHT_TENSION = [
    "There's definitely some tension between these two.",
    "You can sense a bit of an edge in this matchup.",
    "These fighters have some history brewing.",
]

HEAT_PREFIGHT_BAD_BLOOD = [
    "There's BAD BLOOD between these two! This one is personal!",
    "These two genuinely don't like each other. You can feel the animosity.",
    "This goes beyond sport - there's real dislike here.",
    "The tension is THICK. These fighters have unfinished business.",
]

HEAT_PREFIGHT_HEATED = [
    "This is a HEATED rivalry! Both fighters are seething!",
    "The hatred is PALPABLE! This is more than a fight - it's a war!",
    "These two absolutely DESPISE each other! Expect fireworks!",
    "One of the most HEATED rivalries in the sport! This is going to be VIOLENT!",
]

HEAT_PREFIGHT_WAR = [
    "This is WAR! PURE, UNADULTERATED WAR! These fighters want to END each other!",
    "Ladies and gentlemen, this is a BLOOD FEUD! All bets are off!",
    "The ANIMOSITY is OFF THE CHARTS! This rivalry has reached LEGENDARY status!",
    "This isn't a fight - this is a VENDETTA! Years of hatred boiling over!",
    "Forget the scorecards - these two want to DESTROY each other!",
]

# During fight - heat moments
HEAT_EXCHANGE_TENSION = [
    "That one had a little extra on it!",
    "You can tell this fight means more to both of them.",
]

HEAT_EXCHANGE_BAD_BLOOD = [
    "That shot was PERSONAL! He's trying to send a message!",
    "No respect for each other in there! They're LOADING UP!",
    "The bad blood is showing! Every strike has extra venom!",
]

HEAT_EXCHANGE_HEATED = [
    "BRUTAL exchange! They're trying to HURT each other!",
    "This is getting NASTY! Neither man holding back!",
    "The hatred is fueling them! Technical gameplan out the window!",
]

HEAT_EXCHANGE_WAR = [
    "VIOLENCE! Pure VIOLENCE! They want each other DEAD!",
    "This is a WAR CRIME! Absolute CARNAGE in there!",
    "I've never seen such HATRED in a fight! They're going for the KILL!",
]

# Post-fight heat commentary
HEAT_POSTFIGHT_NO_TOUCH = [
    "{winner} refuses to touch gloves! The hatred continues!",
    "No sportsmanship here! {winner} walks away without acknowledging {loser}!",
    "The animosity isn't over! {winner} gives {loser} a death stare!",
]

HEAT_POSTFIGHT_RESPECT = [
    "After all that bad blood, {winner} shows respect! What a moment!",
    "They're embracing! Maybe this war is finally over!",
    "Incredible sportsmanship after such an emotional fight!",
]

# Touch gloves commentary based on heat level
TOUCH_GLOVES_NORMAL = [
    "Both fighters touch gloves. Good sportsmanship to start.",
    "Glove touch. Respect shown before the battle begins.",
    "They touch gloves and we're off!",
]

TOUCH_GLOVES_REFUSED_HEAT = [
    "{fighter1} offers the glove touch... {fighter2} REFUSES! This is PERSONAL!",
    "NO GLOVE TOUCH! The bad blood is REAL between these two!",
    "{fighter2} walks right past the glove touch! WAR from the opening bell!",
    "The glove touch is DENIED! You can feel the hatred in the air!",
    "{fighter1} extends the glove... {fighter2} slaps it away! HERE WE GO!",
]

TOUCH_GLOVES_RELUCTANT = [
    "A brief, tense glove touch. No love lost between these two.",
    "They barely touch gloves. The tension is THICK.",
    "Quick, dismissive glove tap. All business tonight.",
]

# ============================================================================
# FIGHT OUTRO & CELEBRATION TEMPLATES
# ============================================================================

FIGHT_OUTRO_KO = [
    "WHAT A FINISH! {winner} with a DEVASTATING knockout! The crowd is on their feet!",
    "IT'S ALL OVER! {winner} just put the lights OUT on {loser}! SPECTACULAR!",
    "GOODNIGHT EVERYBODY! {winner} leaves {loser} unconscious on the canvas!",
    "OH MY GOODNESS! Did you SEE that?! {winner} with the knockout of the YEAR!",
    "THE VIOLENCE! {winner} just FLATLINED {loser}! What a performance!",
    "SLEEP! {winner} sent {loser} to the shadow realm with that shot!",
    "BOOM! {winner} proves why they're one of the most dangerous fighters alive!",
    "UNCONSCIOUS! {loser} is out COLD! What a statement by {winner}!",
]

FIGHT_OUTRO_TKO = [
    "THE REFEREE STOPS IT! {winner} with the TKO! {loser} couldn't continue!",
    "The ref has seen enough! {winner} gets the stoppage victory!",
    "Excellent stoppage by the referee! {winner} was POURING IT ON!",
    "{loser} was getting DESTROYED and the ref made the right call!",
    "TECHNICAL KNOCKOUT! {winner} with the finish! {loser} was taking too much damage!",
    "The corner throws in the towel! They've seen enough punishment on {loser}!",
    "{winner} FINISHES the fight! The referee jumps in to save {loser}!",
]

FIGHT_OUTRO_SUBMISSION = [
    "TAP! TAP! TAP! {winner} with the SUBMISSION! Beautiful technique!",
    "IT'S OVER! {loser} had no choice but to tap! {winner} is a WIZARD on the ground!",
    "SUBMISSION VICTORY! {winner} forces the tap with that {method}!",
    "There's the tap! {winner} with textbook ground work! Masterclass performance!",
    "THE SQUEEZE! {loser} couldn't escape! {winner} is a submission MACHINE!",
    "{loser} goes to sleep in the choke! {winner} with the technical mastery!",
    "INCREDIBLE grappling display! {winner} makes it look EASY!",
]

FIGHT_OUTRO_DECISION = [
    "After {rounds} rounds of INCREDIBLE action, we go to the judges' scorecards!",
    "What a BATTLE! {rounds} rounds of non-stop warfare! Let's hear from the judges!",
    "BOTH fighters gave it their all! {rounds} rounds... let's see who takes it!",
    "A tactical chess match over {rounds} rounds! The judges will decide!",
    "They left it ALL in the cage! {rounds} rounds of HEART! Who won?",
]

FIGHT_OUTRO_WINNER_CELEBRATION = [
    "{winner} raises their hands in TRIUMPH! What a performance!",
    "The crowd ERUPTS for {winner}! WHAT A FIGHTER!",
    "{winner} doing a victory lap around the cage! Well deserved!",
    "{winner} climbs the cage to celebrate with the fans! INCREDIBLE!",
    "{winner} drops to their knees in emotion! This means EVERYTHING to them!",
    "{winner} points to the sky in victory! A star is SHINING tonight!",
]

FIGHT_OUTRO_LOSER_RESPECT = [
    "Hats off to {loser} for leaving it all in the cage. A warrior's performance.",
    "{loser} came to fight and should hold their head high despite the result.",
    "Nothing but respect for {loser} - came to compete and showed real heart.",
    "{loser} will learn from this and come back stronger. That's a true martial artist.",
]

FIGHT_OUTRO_TITLE_WIN = [
    "WE HAVE A NEW CHAMPION! {winner} captures the DFC {division} title!",
    "THE GOLD CHANGES HANDS! {winner} is the NEW {division} champion!",
    "A NEW ERA BEGINS! {winner} dethrones {loser} to become champion!",
    "{winner} makes HISTORY tonight! The new {division} king is CROWNED!",
    "THE BELT IS COMING HOME! {winner} achieves their dream! NEW CHAMPION!",
]

FIGHT_OUTRO_TITLE_DEFENSE = [
    "{winner} DEFENDS the title! The champion remains the champion!",
    "STILL THE CHAMPION! {winner} proves why they wear the gold!",
    "{winner} adds another defense to their legacy! DOMINANT performance!",
    "The challenger falls short! {winner} retains the {division} championship!",
]

# ============================================================================
# ENHANCED ROUND START TEMPLATES
# ============================================================================

ROUND_START_TEMPLATES = [
    "Round {round_num} begins!",
    "Here we go, round {round_num}!",
    "Round {round_num} is underway! Touch gloves and let's FIGHT!",
    "Touching gloves as round {round_num} starts. HERE WE GO!",
    "The fighters meet in the center for round {round_num}. WAR!",
    "Round {round_num}! Both corners have given their instructions. FIGHT!",
]

ROUND_START_ROUND_1 = [
    "HERE WE GO! Round 1! The moment we've been waiting for!",
    "The crowd is ELECTRIC as round 1 begins! Let's see what these warriors have!",
    "Round 1 is LIVE! Time to find out who wants this more!",
    "First contact coming up! Round 1 starts NOW!",
    "The opening bell sounds! Let the violence BEGIN!",
]

ROUND_START_CHAMPIONSHIP = [
    "CHAMPIONSHIP ROUNDS! Round {round_num}! This is where legends are made!",
    "Round {round_num} - we're in the deep waters now! WHO WANTS IT MORE?!",
    "Round {round_num} of the championship rounds! Dig DEEP!",
    "The championship rounds are HERE! Round {round_num}! HEART vs HEART!",
]

ROUND_START_FINAL = [
    "FINAL ROUND! Round {round_num}! IT ALL COMES DOWN TO THIS!",
    "The LAST round! Winner takes ALL! Round {round_num}!",
    "Final round! Leave NOTHING in the tank!",
    "The last round of the war! This is what you trained your whole life for!",
    "One round left! Three judges watching! WHO TAKES IT HOME?!",
]

ROUND_START_CLOSE_FIGHT = [
    "This fight is RAZOR close! Every second of round {round_num} matters!",
    "The scorecards could go EITHER way! Round {round_num} could decide it all!",
    "A pivotal round {round_num} ahead! Momentum up for grabs!",
]

# ============================================================================
# ENHANCED ROUND END & TRANSITION TEMPLATES
# ============================================================================

ROUND_END_TEMPLATES = [
    "That's the horn! End of round {round_num}.",
    "Round {round_num} comes to a close. WHAT a round!",
    "The horn sounds to end round {round_num}. Back to the corners!",
    "And that's round {round_num} in the books. The coaches are BUZZING!",
    "Time! End of round {round_num}. Both fighters taking a breather.",
]

ROUND_END_ACTION_PACKED = [
    "WOW! What a round! Round {round_num} was ELECTRIC!",
    "The crowd is on their FEET after round {round_num}! Incredible action!",
    "If you blinked, you missed something in round {round_num}! Non-stop warfare!",
    "FIREWORKS in round {round_num}! Both fighters brought it!",
]

ROUND_END_DOMINANT = [
    "A dominant round {round_num}! One fighter clearly took that!",
    "Round {round_num} goes decisively to one corner!",
    "Statement round! Round {round_num} was all ONE fighter!",
]

ROUND_TRANSITIONS = [
    "What a round of mixed martial arts! The corners have 60 seconds!",
    "Both fighters showed HEART in that round! Let's see the adjustments!",
    "The pace is picking up! Championship-level fighting here!",
    "The coaches will have PLENTY to talk about between rounds!",
    "This fight is delivering on ALL fronts! What a battle!",
    "The technical chess match continues! What adjustments will we see?",
    "These two are putting on a SHOW for the fans!",
    "Mixed martial arts at its FINEST! Back to the corners!",
]

ROUND_TRANSITION_CLOSE = [
    "This fight could go EITHER way! Every round is CRUCIAL!",
    "The judges have a tough job tonight! This is razor thin!",
    "A barnburner of a fight! Who's up on the scorecards?",
]

ROUND_TRANSITION_ONE_SIDED = [
    "One fighter is pulling away here! Can the other mount a comeback?",
    "Dominance on display! The other corner needs a big round!",
    "The fight is slipping away! Time for a desperation move?",
]

ROUND_TRANSITION_HURT = [
    "Can {hurt_fighter} recover between rounds? That was BRUTAL!",
    "The corner is working overtime on {hurt_fighter}! Are they compromised?",
    "{hurt_fighter} took serious damage! Will they come out for the next round?",
]

# ============================================================================
# CORNER ADVICE TEMPLATES
# ============================================================================

CORNER_ADVICE_GENERAL = [
    "The corner is shouting instructions! Adjustments being made!",
    "Coaches delivering crucial advice between rounds!",
    "The corner team working feverishly in the 60-second break!",
]

CORNER_ADVICE_WINNING = [
    "\"You're up on the scorecards! Stay smart, don't get wild!\"",
    "\"You're winning this fight! Just don't do anything stupid!\"",
    "\"Beautiful work! Keep doing what you're doing!\"",
    "\"The belt is coming home! Just one more round like that!\"",
    "\"You're DOMINATING! Stay focused, finish strong!\"",
]

CORNER_ADVICE_LOSING = [
    "\"You need to DIG! This fight is slipping away!\"",
    "\"MORE AGGRESSION! You need a finish or you're going to lose this!\"",
    "\"It's now or never! Leave EVERYTHING in there!\"",
    "\"You're behind on the cards! Time to let your hands GO!\"",
    "\"We need a BIG round! Channel your training!\"",
]

CORNER_ADVICE_STRIKER_VS_GRAPPLER = [
    "\"Keep it standing! Don't let them grab you!\"",
    "\"Stuff the takedowns and LIGHT THEM UP!\"",
    "\"Circle off the cage! Don't get trapped!\"",
    "\"Sprawl and BANG! Make them pay for shooting!\"",
]

CORNER_ADVICE_GRAPPLER_VS_STRIKER = [
    "\"Get inside and TAKE THEM DOWN!\"",
    "\"Close the distance! Get to the clinch!\"",
    "\"Wrestling wins fights! Shoot and control!\"",
    "\"Don't stand and trade! Get it to the ground!\"",
]

CORNER_ADVICE_HURT = [
    "\"BREATHE! Clear your head! You're okay!\"",
    "\"Grab them if you have to! Survive this moment!\"",
    "\"Smart defense! Don't let them land another one like that!\"",
    "\"Clinch up if you need to recover! Buy yourself time!\"",
]

CORNER_WATER_CUT = [
    "Water, ice, and encouragement from the corner!",
    "The cornermen working on the fighter - ice, water, adrenaline!",
    "Cutman checking for damage... looking good, they're ready to go!",
    "The stool is pulled, mouthpiece in... HERE WE GO!",
]

# ============================================================================
# POSITION TRANSITION COMMENTARY
# ============================================================================

POSITION_TRANSITION_TO_GROUND = [
    "We're going to the mat! The fight moves to the ground!",
    "DOWN THEY GO! The grappling begins!",
    "Takedown secured! This is where the chess match gets interesting!",
    "Ground game initiated! Let's see the jiu-jitsu!",
]

POSITION_TRANSITION_TO_CLINCH = [
    "They're locked up! Clinch fighting now!",
    "The distance closes! Dirty boxing time!",
    "Collar tie! Elbows and knees in the phonebooth!",
    "Into the clinch! This is Muay Thai territory!",
]

POSITION_TRANSITION_TO_STANDING = [
    "Back on the feet! Stand-up resumes!",
    "They separate! Boxing range now!",
    "Clean break! The striking exchanges continue!",
    "Back to the center! Let the hands fly!",
]

POSITION_TRANSITION_TO_DOMINANT = [
    "Ã‚Â DOMINANT POSITION! This is BAD for the bottom fighter!",
    "Ã‚Â Mount secured! The punishment is coming!",
    "Ã‚Â Back control! The rear naked choke is right there!",
    "Ã‚Â Position before submission! This is TEXTBOOK!",
]

POSITION_TRANSITION_GUARD_PULL = [
    "{actor} PULLS GUARD! They're going to the bottom on PURPOSE!",
    "Guard pull from {actor}! Taking the fight to their world!",
    "{actor} sits to guard! A bold strategy - can they submit from the bottom?",
    "Intentional guard pull! {actor} is confident in their jiu-jitsu!",
    "{actor} concedes top position to work their guard game! Interesting choice!",
]

POSITION_TRANSITION_SCRAMBLE = [
    "SCRAMBLE! Both fighters fighting for position!",
    "Wild exchange on the ground! Who comes out on top?",
    "Chaos in the grappling! Position up for grabs!",
    "A scramble ensues! Beautiful technique from both!",
]

# ============================================================================
# GUARD PULL SPECIFIC TEMPLATES
# ============================================================================

GUARD_PULL_TEMPLATES = {
    "attempt": [
        "{actor} sits down! Going for a guard pull!",
        "{actor} jumps to guard! Bold strategy!",
        "{actor} is pulling guard here! They want the fight on the ground!",
        "Guard pull attempt from {actor}! Jiu-jitsu time!",
    ],
    "success": [
        "{actor} PULLS GUARD successfully! Now let's see that ground game!",
        "Clean guard pull from {actor}! They're in their world now!",
        "{actor} accepts the bottom position to work submissions!",
        "INTO THE GUARD! {actor} is hunting from the bottom!",
        "{actor} gives up top position but has a plan - that closed guard is TIGHT!",
    ],
    "success_commentary": [
        "A calculated risk! {actor} gives away points but gains position they love!",
        "The jiu-jitsu player takes the fight to their realm! Can they submit from bottom?",
        "{actor} is playing a dangerous game - guard pulling in MMA is risky!",
        "The judges won't score that favorably, but {actor} is confident in their submissions!",
    ],
    "fail": [
        "{target} doesn't follow {actor} to the ground! Smart!",
        "{actor}'s guard pull is stuffed! {target} stays standing!",
        "{target} backs away from the guard pull attempt!",
    ],
    "consequence": [
        "{target} is now on top! They'll look to pass and smash!",
        "The wrestler is in their element now - top control secured!",
        "{target} lands in {actor}'s guard but has dominant position!",
    ],
}

# Additional grappling position commentary
GROUND_POSITION_COMMENTARY = {
    "closed_guard": [
        "Locked up in the closed guard! {bottom} controlling the posture!",
        "Full guard for {bottom}! Submission threats everywhere!",
        "The closed guard is a dangerous place! {bottom} hunting!",
    ],
    "half_guard": [
        "Half guard position! Both fighters have options here!",
        "{bottom} has the lockdown in half guard!",
        "Stuck in half guard! Can {top} pass?",
    ],
    "mount": [
        "MOUNT! The most dominant position in MMA!",
        "{top} in full mount! Ground and pound incoming!",
        "The mounted position! This is TROUBLE for {bottom}!",
    ],
    "back_mount": [
        "BACK CONTROL! The rear naked choke is RIGHT THERE!",
        "{top} has the back! Both hooks in! This is BAD!",
        "Back mount secured! {bottom} is in DEEP trouble!",
    ],
    "side_control": [
        "Side control for {top}! Crushing pressure!",
        "Heavy side control! {bottom} needs to escape!",
        "{top} is grinding from side control!",
    ],
}

# ============================================================================
# ENHANCED MOMENTUM & DAMAGE COMMENTARY
# ============================================================================

MOMENTUM_SHIFT_DRAMATIC = [
    "THE MOMENTUM IS SHIFTING! Can you feel it?!",
    "The tide is TURNING in this fight! What a swing!",
    "WHAT A TURNAROUND! The complexion of this fight just changed!",
    "This is where fights are WON and LOST! Momentum changing!",
    "The hunter becomes the HUNTED! Role reversal!",
]

MOMENTUM_BUILDING = [
    "Building momentum here! The pressure is mounting!",
    "Starting to take over! The rhythm is there!",
    "Finding their range now! Confidence growing!",
    "Settling into the fight! Here comes the offense!",
]

DAMAGE_ACCUMULATING = [
    "The damage is piling up! How much more can they take?",
    "You can see the wear and tear now! The punishment is showing!",
    "Starting to slow down from all that damage!",
    "The body work is paying dividends! Breathing heavy now!",
]

FIGHTER_HURT_BADLY = [
    "Ã‚Â {target} IS HURT! THIS COULD BE IT!",
    "Ã‚Â ROCKED! {target} is in SERIOUS trouble!",
    "Ã‚Â WOBBLED! {target} on shaky legs! Can they survive?!",
    "Ã‚Â {target} is COMPROMISED! Survival mode activated!",
    "Ã‚Â DAMAGED! {target} is running on fumes now!",
]

FIGHTER_RECOVERS = [
    "{actor} shakes it off! The chin held up!",
    "Survived that storm! {actor} is still in this!",
    "Championship heart from {actor}! Wouldn't go down!",
    "{actor} weathered the storm! Back in the fight!",
]

FIGHTER_EXHAUSTED = [
    "{actor} is GASSED! The tank is empty!",
    "Fatigue setting in HARD for {actor}! Survival mode!",
    "{actor} can barely keep their hands up! Exhaustion!",
    "The cardio is failing {actor}! Running on fumes!",
]

CROWD_REACTIONS = [
    "The crowd is going WILD!",
    "Listen to this arena! They're on their FEET!",
    "DEAFENING cheers from the fans!",
    "The energy in this building is ELECTRIC!",
    "The crowd senses a finish coming!",
]

# ============================================================================
# STATE-BASED STRIKE VARIANTS (Fatigue/Damage Context)
# ============================================================================

# These replace standard templates based on fighter state
STATE_BASED_STRIKES = {
    # FRESH - Early fight, full energy
    "fresh": {
        "punch": [
            "{actor} snaps a CRISP jab to start!",
            "{actor} fires off a lightning quick combination!",
            "Sharp, fast hands from {actor}!",
            "{actor} is fresh and letting the hands FLY!",
            "Picture-perfect technique from {actor}!",
            "{actor} looks SHARP early! Fast hands!",
        ],
        "kick": [
            "{actor} uncorks a BEAUTIFUL kick!",
            "Textbook technique on that kick from {actor}!",
            "{actor} is throwing with SNAP and POWER!",
            "Crisp kicking from a fresh {actor}!",
        ],
        "heavy": [
            "{actor} DETONATES with full power! Fresh and dangerous!",
            "THUNDEROUS shot from {actor}! Full gas tank on display!",
            "{actor} is LOADING UP early! That one had everything behind it!",
        ],
    },
    
    # FATIGUED - Mid-to-late fight, energy depleted
    "fatigued": {
        "punch": [
            "{actor} paws out a tired jab...",
            "Labored breathing as {actor} throws a slow cross.",
            "{actor}'s arms look HEAVY, pushing punches now.",
            "That punch had nothing on it. {actor} is fading.",
            "{actor} is arm-punching now. The gas tank is LOW.",
            "Sluggish output from a tired {actor}.",
            "{actor} throwing arm punches. No snap left.",
        ],
        "kick": [
            "{actor} throws a lazy kick with no zip.",
            "That kick was in slow motion. {actor} is TIRED.",
            "{actor} can barely lift the leg for that kick.",
            "Telegraphed kick from a fatigued {actor}.",
        ],
        "heavy": [
            "{actor} loads up but there's nothing left in the tank!",
            "Swinging tired leather! {actor} looking for a Hail Mary!",
            "{actor} is throwing on fumes! That punch took EVERYTHING!",
        ],
    },
    
    # DESPERATE - Behind on scorecards, needs a finish
    "desperate": {
        "punch": [
            "{actor} SWINGS WILDLY! Looking for a miracle!",
            "Throwing CAUTION to the wind! {actor} needs a finish!",
            "{actor} is EMPTYING THE TANK! All or nothing!",
            "HAYMAKERS from {actor}! Abandon all defense!",
            "{actor} is WINGING punches! Desperate for a knockout!",
            "It's do-or-die for {actor}! Throwing BOMBS!",
            "{actor} knows they need a finish! HERE IT COMES!",
        ],
        "kick": [
            "{actor} throws a WILD head kick! Going for broke!",
            "Desperate spinning attack from {actor}!",
            "{actor} loading up on kicks! Needs the finish!",
        ],
        "heavy": [
            "{actor} is SWINGING FOR THE FENCES! All or nothing!",
            "EVERYTHING behind that shot! {actor} NEEDS this!",
            "DESPERATION BOMB from {actor}! Do or die time!",
        ],
    },
    
    # DAMAGED - Hurt, cut, or compromised
    "damaged": {
        "punch": [
            "{actor} fires back THROUGH THE BLOOD!",
            "Fighting on pure INSTINCT now! {actor} still throwing!",
            "{actor} is HURT but still DANGEROUS!",
            "Wounded but not done! {actor} throws back!",
            "{actor} wipes the blood and keeps FIGHTING!",
            "Heart of a WARRIOR! {actor} won't stop throwing!",
        ],
        "kick": [
            "{actor} throws a kick on wobbly legs!",
            "Still kicking despite the damage! {actor} is a WARRIOR!",
            "{actor} refuses to quit! Kicks coming through the pain!",
        ],
        "heavy": [
            "{actor} throws a BOMB while barely standing! HEART!",
            "WARRIOR SPIRIT! {actor} unleashes despite being hurt!",
            "{actor} is DAMAGED but that shot was DANGEROUS!",
        ],
    },
    
    # DOMINANT - Winning clearly, in control
    "dominant": {
        "punch": [
            "{actor} is PICKING {target} APART!",
            "Target practice for {actor}! Landing at will!",
            "{actor} is in COMPLETE control! Another one lands!",
            "Systematic destruction from {actor}!",
            "{actor} is putting on a CLINIC!",
        ],
        "kick": [
            "{actor} kicks at will! {target} has no answer!",
            "Another kick lands! {actor} is in total control!",
            "{actor} is TEEING OFF with the kicks!",
        ],
        "heavy": [
            "{actor} PUNISHES {target} again! This is DOMINANCE!",
            "ANOTHER huge shot from {actor}! It's a masterclass!",
            "{actor} is on ANOTHER LEVEL tonight!",
        ],
    },
    
    # HURT_RECOVERY - Just recovered from being rocked
    "hurt_recovery": {
        "punch": [
            "{actor} answers back! Still in this fight!",
            "{actor} fires back! Showing they're not done!",
            "Return fire from {actor}! Surviving the storm!",
            "{actor} has recovered and is back in the fight!",
        ],
        "kick": [
            "{actor} throws a kick to create distance! Smart recovery!",
            "Back on stable legs! {actor} kicks to reestablish range!",
        ],
        "heavy": [
            "{actor} ROARS back with a counter! NOT DONE YET!",
            "CHAMPIONSHIP HEART! {actor} answers with POWER!",
        ],
    },
}

# ============================================================================
# COMBO CONNECTORS (Chain Commentary)
# ============================================================================

COMBO_CONNECTORS = {
    # Two-strike combinations
    "2_hit": [
        "...and FOLLOWS IT UP with the {strike}!",
        "...right behind it comes the {strike}!",
        "...DOUBLING UP with the {strike}!",
        "...and the {strike} lands RIGHT BEHIND IT!",
        "...ONE-TWO! The {strike} connects!",
        "...BANG BANG! The {strike} follows!",
        "...and IMMEDIATELY the {strike}!",
    ],
    
    # Three-strike combinations
    "3_hit": [
        "...AND A THIRD SHOT LANDS! Beautiful combination!",
        "...THREE-PIECE COMBO connects flush!",
        "...he is TEEING OFF on {target}!",
        "...TRIPLE UP! Three shots land clean!",
        "...AND ANOTHER! {actor} is in a RHYTHM!",
        "...THREE AND OUT! Textbook combination!",
    ],
    
    # Four+ strike flurry
    "flurry": [
        "...{actor} is UNLOADING! A FLURRY of strikes!",
        "...HE'S NOT STOPPING! POURING IT ON!",
        "...THE FLOODGATES ARE OPEN! Strike after strike!",
        "...{actor} SMELLS BLOOD! Going for the finish!",
        "...TEED OFF! {target} is getting LIT UP!",
        "...BARRAGE of strikes from {actor}!",
        "...CAN'T MISS! Everything is landing!",
    ],
    
    # Combo starters (first strike of a combo)
    "combo_start": [
        "{actor} starts the combination...",
        "{actor} opens up with a {strike}...",
        "Here comes {actor}! {strike} to start...",
        "{actor} initiates with the {strike}...",
    ],
    
    # Combo enders (finishing blow of a combo)
    "combo_finish": [
        "...and PUNCTUATES IT with a HUGE {strike}!",
        "...CAPPED OFF with a devastating {strike}!",
        "...and the EXCLAMATION POINT! {strike} lands FLUSH!",
        "...finishes the combo with AUTHORITY!",
    ],
    
    # Ground and pound combos
    "gnp_flurry": [
        "{actor} is RAINING DOWN punishment!",
        "GROUND AND POUND! Shot after shot!",
        "{actor} is UNLOADING from the top!",
        "The punishment continues! {target} is getting SMASHED!",
        "{actor} is HAMMERING away! This could be stopped!",
    ],
}

# ============================================================================
# TREND ANALYSIS / COLOR COMMENTARY (The 'Why')
# ============================================================================

TREND_ANALYSIS = {
    # Leg damage accumulating
    "leg_damage": [
        "Color: \"Those leg kicks are ADDING UP. {target} is having trouble planting that lead foot.\"",
        "Color: \"He's chopping the tree down. That leg is turning PURPLE.\"",
        "Color: \"{target}'s movement has been COMPROMISED. Those calf kicks are brutal.\"",
        "Color: \"The leg is GONE. {target} can barely put weight on it.\"",
        "Color: \"This is the leg kick strategy in full effect. {target} is limping bad.\"",
    ],
    
    # Body work paying off
    "body_damage": [
        "Color: \"All that body work is paying off. {target}'s arms are DROPPING.\"",
        "Color: \"The body shots are STEALING his gas tank. Watch the breathing.\"",
        "Color: \"{target}'s mouth is WIDE open. Those body shots hurt.\"",
        "Color: \"The liver is COMPROMISED. Every shot to the body now is agony.\"",
        "Color: \"Can't throw when you can't breathe. The body work is GENIUS.\"",
    ],
    
    # Fighter gassing out
    "gassing_out": [
        "Color: \"{actor}'s mouth is wide open. Spent too much energy in that first round.\"",
        "Color: \"The pace has slowed SIGNIFICANTLY here. Someone is fading.\"",
        "Color: \"{actor} is hitting a wall. The output has dropped off a CLIFF.\"",
        "Color: \"You can see the fatigue. {actor}'s punches have no SNAP anymore.\"",
        "Color: \"The gas tank is EMPTY. {actor} is surviving, not thriving.\"",
        "Color: \"This is where conditioning wins fights. {actor} looks SPENT.\"",
    ],
    
    # Wrestling dominance
    "wrestling_dominance": [
        "Color: \"{target} has NO answer for the takedown. Looks discouraged.\"",
        "Color: \"This is a wrestling CLINIC. Wash, rinse, repeat.\"",
        "Color: \"Every time {target} gets up, right back down. Demoralizing.\"",
        "Color: \"The wrestling differential is MASSIVE. {actor} is having his way.\"",
        "Color: \"{target} is getting MAULED. Can't stop the takedowns.\"",
    ],
    
    # Striking differential
    "striking_outclassed": [
        "Color: \"{target} is getting OUT-STRUCK badly. The differential is huge.\"",
        "Color: \"Landing at will. {target} can't find the range.\"",
        "Color: \"The boxing is LEVELS apart. {actor} is picking them apart.\"",
        "Color: \"{target} hasn't landed a clean shot in minutes. Outclassed.\"",
        "Color: \"This is a striking MASTERCLASS from {actor}.\"",
    ],
    
    # Submission threats
    "submission_danger": [
        "Color: \"{target} is in DEEP trouble on the ground. The submission game is real.\"",
        "Color: \"Every time they grapple, {actor} is hunting. Dangerous.\"",
        "Color: \"{target} needs to stay AWAY from the ground. The BJJ is too good.\"",
        "Color: \"It's a matter of TIME before {actor} catches something.\"",
    ],
    
    # Counter punching working
    "counter_timing": [
        "Color: \"{actor} has the TIMING down. Every time {target} throws, they pay.\"",
        "Color: \"Beautiful counter work. {target} is walking into shots.\"",
        "Color: \"The counter puncher has SOLVED the puzzle. {target} is hesitant.\"",
        "Color: \"{actor} is making {target} PAY for every attempt.\"",
    ],
    
    # Clinch control
    "clinch_dominance": [
        "Color: \"{actor} is OWNING the clinch. Knees and elbows all day.\"",
        "Color: \"{target} can't get off the cage. The clinch work is suffocating.\"",
        "Color: \"Every time they get close, {actor} controls. Masterful.\"",
    ],
    
    # Octagon control / pressure
    "pressure_overwhelming": [
        "Color: \"{actor} is walking them down RELENTLESSLY. No escape.\"",
        "Color: \"The pressure is SUFFOCATING. {target} can't breathe.\"",
        "Color: \"{target} is on the back foot all night. The octagon is shrinking.\"",
        "Color: \"Volume and pressure. {actor} is OVERWHELMING them.\"",
    ],
    
    # Fighter has adjusted
    "adjustment_made": [
        "Color: \"Big adjustment there. {actor} has figured something out.\"",
        "Color: \"The corner advice is WORKING. Different fighter this round.\"",
        "Color: \"{actor} made a tactical change. This is a different fight now.\"",
        "Color: \"Smart adaptation. {actor} has found the answer.\"",
    ],
    
    # Scorecards discussion
    "close_scorecards": [
        "Color: \"This is RAZOR thin. Every second matters.\"",
        "Color: \"The judges have a TOUGH job tonight. Could go either way.\"",
        "Color: \"I've got it close. This final round is EVERYTHING.\"",
        "Color: \"We might see a split decision here. It's that close.\"",
    ],
    
    # One fighter pulling ahead
    "pulling_ahead": [
        "Color: \"{actor} is BANKING rounds. {target} needs a finish.\"",
        "Color: \"The scorecards are getting away from {target}.\"",
        "Color: \"{actor} is building a LEAD. Time is running out.\"",
        "Color: \"Unless something changes, {actor} is taking this.\"",
    ],
}

# ============================================================================
# STYLE-TAGGED STRIKE TEMPLATES
# ============================================================================

# Style-specific commentary adds flavor based on fighting style
STYLE_STRIKES = {
    # Brawler / Power Puncher style
    "Brawler": {
        "punch_light": [
            "{actor} pumps the jab looking to set up the BOMB.",
            "{actor} measures the distance... the power shot is coming.",
            "Feeling out punch from {actor}. You know the big one is loading.",
        ],
        "punch_heavy": [
            "{actor} lands a BOMBSHELL right hand! THUNDER!",
            "SLEDGEHAMMER shot from {actor}! That's VIOLENT!",
            "{actor} with the EQUALIZER! One shot can change everything!",
            "MASSIVE power shot lands! {actor} is a DANGEROUS man!",
            "{actor} throws LEATHER! That one RATTLED {target}!",
            "HUGE SHOT from the power puncher! {target} felt THAT one!",
        ],
        "ko_shot": [
            "{actor} lands the KILL SHOT! GOODNIGHT!",
            "THE BOMB LANDS! {actor} just FLATLINED {target}!",
            "ONE PUNCH KNOCKOUT! {actor} is a DESTROYER!",
        ],
    },
    
    # Technician / Point Fighter style
    "Technician": {
        "punch_light": [
            "{actor} SNIPES with a laser-precise jab.",
            "Textbook technique from {actor}. Clean and crisp.",
            "{actor} picks the shot perfectly. Surgical.",
            "Beautiful timing on that strike from {actor}.",
        ],
        "punch_heavy": [
            "{actor} finds the opening with PRECISION! Textbook!",
            "SURGICAL strike from {actor}! Perfect placement!",
            "{actor} with the SNIPER shot! Right down the pipe!",
            "Technical BRILLIANCE! {actor} found the gap!",
            "{actor} threads the needle! Masterful striking!",
        ],
        "ko_shot": [
            "{actor} with the PERFECT shot! Technical knockout!",
            "The sweet science on display! {actor} finds the button PRECISELY!",
            "FLAWLESS execution! {actor} shuts the lights off CLEAN!",
        ],
    },
    
    # Pressure Fighter / Volume style
    "Pressure Fighter": {
        "punch_light": [
            "{actor} walks forward throwing! Non-stop pressure!",
            "Jab to close the distance! {actor} keeps coming!",
            "{actor} is RELENTLESS! Pawing and pressuring!",
        ],
        "punch_heavy": [
            "{actor} BULLDOZES forward with a huge shot!",
            "PRESSURE and POWER! {actor} is a FREIGHT TRAIN!",
            "{actor} walks through the fire and lands HEAVY!",
            "No retreat! {actor} BULLS forward with violence!",
        ],
        "combo": [
            "{actor} is SWARMING! Volume overload!",
            "NON-STOP offense from {actor}! Overwhelming!",
            "{actor} is throwing in BUNCHES! Can't stop the pressure!",
        ],
    },
    
    # Counter Striker style
    "Counter Striker": {
        "punch_light": [
            "{actor} times the counter BEAUTIFULLY!",
            "Slick counter from {actor}! Patience pays off!",
            "{actor} makes {target} pay for coming in.",
        ],
        "punch_heavy": [
            "{actor} TIMES THE COUNTER PERFECTLY! BOOM!",
            "CAUGHT coming in! {actor} with the counter BOMB!",
            "{actor} plays MATADOR! Counter lands FLUSH!",
            "BEAUTIFUL counter! {actor} was waiting for that!",
            "{actor} with the KILL COUNTER! {target} walked into it!",
        ],
        "ko_shot": [
            "{actor} TIMES IT PERFECTLY! Counter knockout!",
            "{target} walked RIGHT INTO IT! The counter striker strikes!",
            "THE TRAP IS SPRUNG! {actor} with the counter KO!",
        ],
    },
    
    # Wrestler style
    "Wrestler": {
        "gnp_light": [
            "{actor} is grinding from the top. Methodical.",
            "Short shots from {actor}. Wearing them down.",
            "{actor} controls and chips away. Wrestler's gameplan.",
        ],
        "gnp_heavy": [
            "{actor} BOMBS from the top! Brutal ground and pound!",
            "HAMMER FISTS from {actor}! The wrestling is paying off!",
            "{actor} is MAULING {target} on the ground!",
            "Devastating ground and pound! {actor} is a BEAST on top!",
        ],
        "control": [
            "{actor} is SMOTHERING {target}. Complete control.",
            "The wrestling is SUFFOCATING. {target} can't escape.",
            "{actor} makes it look EASY. Wrestling dominance.",
        ],
    },
    
    # BJJ Specialist style  
    "BJJ Specialist": {
        "ground_offense": [
            "{actor} is HUNTING from the guard. Dangerous position.",
            "Active off the back! {actor} is always threatening.",
            "{actor} creates angles looking for the submission.",
            "The jiu-jitsu is ON DISPLAY. {actor} is a wizard.",
        ],
        "sweep": [
            "BEAUTIFUL sweep from {actor}! Technical mastery!",
            "{actor} reverses with textbook jiu-jitsu!",
            "The ground game advantage is CLEAR. {actor} takes over.",
        ],
        "submission_attempt": [
            "{actor} is working for the submission! TIGHT!",
            "The squeeze is ON! {actor} hunting the tap!",
            "{actor} transitions BEAUTIFULLY! Submission incoming!",
        ],
    },
    
    # Muay Thai style
    "Muay Thai": {
        "kick_light": [
            "{actor} chops with a Thai kick. Nasty.",
            "Traditional Muay Thai kick from {actor}. Heavy.",
            "{actor} throws with Thai technique. THUD.",
        ],
        "kick_heavy": [
            "{actor} with a DEVASTATING Thai kick! BASEBALL BAT!",
            "MUAY THAI VIOLENCE! {actor} lands the bomb!",
            "{actor} with the traditional Thai DESTROYER!",
            "BRUTAL Thai kick! {actor}'s shins are WEAPONS!",
        ],
        "clinch": [
            "{actor} drags them into the THAI CLINCH! Here come the knees!",
            "Muay Thai MASTERY in the clinch from {actor}!",
            "{actor} with the plum! ELBOWS AND KNEES incoming!",
        ],
        "elbow": [
            "{actor} with a SLICING elbow! Muay Thai special!",
            "The 8 LIMBS on display! Elbow lands CLEAN!",
            "{actor} opens up {target} with a NASTY elbow!",
        ],
    },
    
    # Balanced / MMA style
    "Balanced": {
        "punch_light": [
            "{actor} finds a home for the jab.",
            "Clean striking from {actor}. Well-rounded.",
            "{actor} is comfortable everywhere. Strike lands.",
        ],
        "punch_heavy": [
            "{actor} lands a CLEAN shot! Complete fighter!",
            "The well-rounded attack from {actor} lands heavy!",
            "{actor} shows their VERSATILITY with that shot!",
        ],
        "transition": [
            "{actor} transitions smoothly! Complete MMA fighter!",
            "Seamless transition from {actor}. Dangerous everywhere.",
            "{actor} is comfortable in ALL areas. Nightmare matchup.",
        ],
    },
}

# Generic style fallbacks (used when style not specifically defined)
STYLE_STRIKES["Kickboxer"] = STYLE_STRIKES["Technician"]
STYLE_STRIKES["Point Fighter"] = STYLE_STRIKES["Technician"]
STYLE_STRIKES["Ground and Pound"] = STYLE_STRIKES["Wrestler"]
STYLE_STRIKES["Clinch Fighter"] = STYLE_STRIKES["Muay Thai"]
STYLE_STRIKES["Sprawl and Brawl"] = STYLE_STRIKES["Brawler"]

# ============================================================================
# FINISH SEQUENCE COMMENTARY (KO/TKO Build-up)
# ============================================================================

FINISH_SEQUENCE = {
    # When a fighter is hurt and being finished
    "hurt_followup": [
        "{target} IS HURT! {actor} SMELLS BLOOD!",
        "{target} WOBBLES! {actor} POUNCES!",
        "THE LEGS ARE GONE! {actor} going for the KILL!",
        "{target} IS IN TROUBLE! Here comes the finish!",
    ],
    
    "swarming": [
        "{actor} is ALL OVER {target}! This could be IT!",
        "POURING IT ON! {actor} wants the stoppage!",
        "{actor} UNLOADS! {target} is just SURVIVING!",
        "THE FINISH IS NEAR! {actor} won't let up!",
    ],
    
    "referee_watching": [
        "The referee is watching CLOSELY! How much more?!",
        "Mario Yamasaki would have stopped this by now!",
        "The ref is READY to step in! Is {target} still there?!",
        "How much more can {target} take?! The ref is deciding!",
    ],
    
    "final_blow": [
        "AND THAT'S THE ONE! {actor} gets the FINISH!",
        "LIGHTS OUT! The final blow lands!",
        "THE KILL SHOT! It's ALL OVER!",
        "{actor} ENDS IT! What a PERFORMANCE!",
    ],
}

# Basic Strike Commentary
PUNCH_TEMPLATES = {
    "attempt": [
        "{actor} lets his hands go!",
        "{actor} steps in with a combination.",
        "{actor} fires off a quick punch.",
        "{actor} looks to establish the jab.",
        "{actor} comes forward with the hands."
    ],
    "success_light": [
        "{actor} lands a sharp jab to the head.",
        "{actor} pops {target} with a straight right.",
        "{actor} connects with a crisp one-two combination.",
        "A stiff jab from {actor} finds the mark.",
        "{actor} tags {target} with a quick left hook.",
        "Clean straight left lands for {actor}.",
        "{actor} snaps the head back with a jab."
    ],
    "success_heavy": [
        "{actor} connects with a MASSIVE overhand right!",
        "OH! A huge left hook from {actor} rocks {target}!",
        "WHAT A SHOT! {actor} lands a crushing uppercut!",
        "A BOMB of an overhand right from {actor} lands flush!",
        "{actor} drops a SLEDGEHAMMER right hand on {target}!",
        "BRUTAL power shot from {actor} staggers {target}!",
        "A VICIOUS left hook from {actor} wobbles {target}!",
        "{target} is HURT BAD from that shot by {actor}!"
    ],
    "miss": [
        "{actor} throws a wild haymaker that misses the target.",
        "{target} slips beautifully away from the punch.",
        "{actor}'s punch just grazes the air as {target} evades.",
        "{target} ducks under the looping punch nicely.",
        "{actor} overcommits and comes up empty.",
        "Good head movement from {target} avoids the strike."
    ],
    "fail": [
        "{target} blocks the punch effectively.",
        "{actor}'s punch is deflected by {target}'s guard.",
        "{target} covers up well to absorb the impact."
    ]
}

KICK_TEMPLATES = {
    "attempt": [
        "{actor} throws a kick.",
        "{actor} looks to land a kick.",
    ],
    "success_light": [
        "{actor} lands a quick kick.",
        "A kick from {actor} finds its mark.",
    ],
    "success_heavy": [
        "HUGE kick from {actor}!",
        "{actor} lands a devastating kick!",
    ],
    "miss": [
        "{actor} misses with the kick.",
        "{target} avoids the kick.",
    ],
    "fail": [
        "{target} blocks the kick.",
        "{actor}'s kick is defended.",
    ]
}

LEG_KICK_TEMPLATES = {
    "attempt": [
        "{actor} launches a leg kick to the calf.",
        "{actor} looks to chop down the legs.",
        "{actor} throws a low kick.",
    ],
    "success_light": [
        "{actor} lands a sharp leg kick to the thigh.",
        "{actor} connects with a snapping low kick.",
        "{actor} digs a leg kick into the calf of {target}.",
        "Nice calf kick lands for {actor}.",
    ],
    "success_heavy": [
        "BRUTAL leg kick from {actor} buckles {target}'s knee!",
        "That leg kick from {actor} had THUNDER behind it!",
        "{actor} CHOPS the leg! {target} is limping!",
        "DEVASTATING low kick! {target}'s leg is compromised!",
    ],
    "miss": [
        "{target} checks the leg kick perfectly.",
        "{actor}'s leg kick is avoided.",
        "Beautiful timing from {target} to avoid that low kick.",
    ],
    "fail": [
        "{target} checks the leg kick perfectly.",
        "{target} absorbs the low kick on his shin.",
    ]
}

HEAD_KICK_TEMPLATES = {
    "attempt": [
        "{actor} attempts a high kick to the head.",
        "{actor} throws a head kick.",
        "{actor} fires off a high kick.",
    ],
    "success_light": [
        "{actor} lands a head kick.",
        "A quick head kick from {actor} connects.",
        "{actor} catches {target} with a high kick.",
    ],
    "success_heavy": [
        "OH MY! A MASSIVE head kick from {actor}!",
        "VICIOUS head kick from {actor}! {target} is in serious trouble!",
        "{actor} lands a HEAD KICK flush on the chin!",
        "DEVASTATING high kick from {actor} rocks {target}!",
    ],
    "miss": [
        "{target} ducks under the head kick.",
        "{actor}'s kick sails harmlessly over {target}'s head.",
        "{target} leans back to avoid the high kick.",
    ],
    "fail": [
        "{target} blocks the head kick with his guard.",
        "{actor}'s head kick is caught on {target}'s shoulder.",
    ]
}

BODY_KICK_TEMPLATES = {
    "attempt": [
        "{actor} fires off a body kick.",
        "{actor} throws a kick to the body.",
        "{actor} looks to land to the midsection.",
    ],
    "success_light": [
        "A quick body kick from {actor} finds its mark.",
        "Nice front kick to the body lands for {actor}.",
        "{actor} lands a kick to the ribs.",
    ],
    "success_heavy": [
        "{actor} lands a CRUSHING body kick that folds {target}!",
        "A spinning back kick from {actor} lands FLUSH to the liver!",
        "BRUTAL body kick from {actor}! {target} is hurt!",
        "{actor} SINKS a kick into the liver!",
    ],
    "miss": [
        "{actor} misses with the body kick.",
        "{target} moves away from the body kick.",
    ],
    "fail": [
        "{target} absorbs the body kick on his elbow.",
        "{actor}'s body kick is blocked.",
    ]
}

# Soccer kick templates (for ground strikes when attacker standing over downed opponent)
SOCCER_KICK_TEMPLATES = {
    "attempt": [
        "{actor} looks to land soccer kicks.",
        "{actor} lines up kicks to the downed {target}.",
    ],
    "success_light": [
        "{actor} lands a kick to the downed {target}.",
        "Kicks to the body of the grounded {target}.",
        "{actor} connects with a kick to {target} on the ground.",
    ],
    "success": [
        "{actor} lands SOLID kicks to the downed {target}!",
        "Hard kicks to the grounded fighter from {actor}!",
        "{actor} delivers punishing kicks to {target} on the mat!",
        "The grounded {target} absorbs kicks from {actor}!",
    ],
    "success_heavy": [
        "{actor} lands VICIOUS kicks to the downed {target}!",
        "BRUTAL kicks to the grounded fighter!",
        "{actor} unloads on the downed {target}!",
    ],
    "miss": [
        "{target} covers up and avoids the kick.",
        "{actor}'s kick misses the downed {target}.",
    ],
    "fail": [
        "{target} blocks from the ground.",
    ]
}

# Grappling Commentary
TAKEDOWN_TEMPLATES = {
    "attempt": [
        "{actor} shoots in for a takedown!",
        "{actor} changes levels for a double leg!",
        "{actor} drives in for a single leg takedown.",
        "{actor} looks to close the distance and take it down!",
        "Here comes the wrestling from {actor}!"
    ],
    "success": [
        "{actor} secures a BEAUTIFUL double-leg takedown!",
        "PERFECT level change from {actor} puts {target} on his back!",
        "{actor} completes the single leg and gets the takedown!",
        "TEXTBOOK takedown! {actor} dumps {target} to the canvas!",
        "Excellent wrestling from {actor} gets the fight to the ground!",
        "{actor} shows his superior grappling with that takedown!"
    ],
    "success_light": [
        "{actor} secures a solid takedown.",
        "{actor} gets {target} to the ground.",
        "Nice wrestling from {actor} gets the takedown."
    ],
    "success_heavy": [
        "{actor} with a DOMINANT takedown!",
        "EXPLOSIVE takedown from {actor}!",
        "{actor} SLAMS {target} to the canvas!"
    ],
    "fail": [
        "{target} sprawls perfectly to defend the takedown attempt.",
        "Excellent takedown defense from {target}!",
        "{target} shows great balance, stuffing the shot beautifully.",
        "{target} frames against the neck and defends expertly.",
        "Good underhooks from {target} to stuff the takedown.",
        "{target}'s wrestling defense is on point!"
    ]
}

SUBMISSION_ATTEMPT_TEMPLATES = {
    "attempt": [
        "{actor} is looking for a submission!",
        "{actor} is hunting for something here!",
        "{actor} transitions into a submission setup.",
        "The grappling wizard {actor} is at work!",
        "{actor} smells blood and goes for the finish!"
    ]
}

SUB_ENTRY_TEMPLATES = {
    "success": [
        "OH! {actor} is going for a {move}!",
        "{actor} transitions to a {move}! This looks TIGHT!",
        "It's a {move} attempt from {actor}! {target} is in big trouble!",
        "{actor} locks up a DEEP {move}!",
        "Beautiful technique! {actor} secures the {move}!",
        "The submission specialist {actor} has the {move} locked in!"
    ],
    "fail": [
        "{target} defends the {move} attempt brilliantly.",
        "{actor} can't quite secure the position for the {move}.",
        "Great hand-fighting from {target} prevents the {move}.",
        "Excellent defense from {target} against the {move} attempt.",
        "{target} shows great submission awareness to escape."
    ]
}

SUB_ESCAPE_DRAMATIC_TEMPLATES = [
    "INCREDIBLE escape! {actor} slips out of the {move} at the last second!",
    "{actor} ESCAPES! That was as close to tapping as you can get!",
    "HOW?! {actor} somehow gets out of the {move}! The crowd is on its feet!",
    "MIRACULOUS! {actor} survives the {move}! {target} can't believe it!",
    "{actor} JUST escapes — that was a millisecond from over!",
    "The {move} was IN — and somehow {actor} got out! Unreal heart!",
]

SUB_ESCAPE_TIGHT_TEMPLATES = [
    "{actor} fights free of the {move}! It was getting tight!",
    "Big escape from {actor} — that {move} was a problem!",
    "{actor} works out of the {move}! {target} had it deep!",
    "{actor} grits through it and escapes the {move}!",
    "{target} loses the {move} as {actor} battles to safety!",
]


SUBMISSION_TEMPLATES = {
    "success": [
        "IT'S OVER! {actor} locks in the {move} and {target} TAPS OUT!",
        "SUBMISSION VICTORY! {actor} gets the tap with a beautiful {move}!",
        "The {move} is FULLY LOCKED! {target} has no choice but to submit!",
        "{actor} forces the tapout with a PICTURE-PERFECT {move}!",
        "AND THAT'S IT! {actor} gets the submission with the {move}!"
    ],
    "success_light": [
        "{actor} applies a {move} successfully!",
        "{actor} gets the submission with the {move}!",
        "It's all over! {actor} with the {move}!"
    ],
    "success_heavy": [
        "DOMINANT submission! {actor} with the {move}!",
        "INCREDIBLE technique! {actor} finishes with the {move}!",
        "{actor} forces the tap with a DEVASTATING {move}!"
    ],
    "fail": [
        "{target} defends the {move} attempt brilliantly.",
        "{actor} can't quite secure the position for the {move}.",
        "Great hand-fighting from {target} prevents the {move}.",
        "Excellent defense from {target} against the {move} attempt.",
        "{target} shows great submission awareness to escape."
    ]
}

# Ground Fighting
GNP_TEMPLATES = {
    "attempt": [
        "{actor} looks to rain down some ground and pound.",
        "{actor} postures up to unleash strikes from the top.",
        "{actor} prepares to open up with ground strikes.",
        "Here comes the ground and pound from {actor}.",
        "{actor} looks to capitalize with strikes from the top position."
    ],
    "success_light": [
        "{actor} lands a solid shot from the top position.",
        "A clean elbow gets through for {actor} on the ground.",
        "{actor} connects with short punches on the ground.",
        "Good ground strikes from {actor} accumulate damage."
    ],
    "success_heavy": [
        "A BIG shot gets through for {actor} on the ground!",
        "{actor} lands a VICIOUS elbow that opens up {target}!",
        "CRUSHING ground and pound from {actor} connects clean!",
        "BRUTAL strikes from {actor} on the ground!",
        "{actor} is dealing SERIOUS damage to {target} on the ground!"
    ],
    "fail": [
        "{target} does an excellent job of tying up {actor}.",
        "{target} controls the wrists expertly to neutralize the attack.",
        "{target} frames against the neck, limiting striking opportunities.",
        "Smart defensive work from {target} on the bottom."
    ]
}

GNP_PUNCH_TEMPLATES = {
    "attempt": [
        "{actor} looks to rain down punches from the top.",
        "{actor} postures up to unleash punches from the top.",
        "{actor} prepares to open up with ground punches.",
        "Here comes the ground and pound from {actor}.",
        "{actor} looks to capitalize with punches from the top position."
    ],
    "success_light": [
        "{actor} lands a solid punch from the top position.",
        "A clean punch gets through for {actor} on the ground.",
        "{actor} connects with short punches on the ground.",
        "Good ground punches from {actor} accumulate damage."
    ],
    "success_heavy": [
        "A BIG punch gets through for {actor} on the ground!",
        "CRUSHING ground punches from {actor} connect clean!",
        "BRUTAL punches from {actor} on the ground!",
        "{actor} is HAMMERING {target} with ground strikes!"
    ],
    "fail": [
        "{target} does an excellent job of tying up {actor}.",
        "{target} controls the wrists expertly to neutralize the attack.",
        "{target} frames against the neck, limiting striking opportunities.",
        "Smart defensive work from {target} on the bottom."
    ]
}

GNP_ELBOW_TEMPLATES = {
    "attempt": [
        "{actor} looks for a sharp elbow strike from the top!",
        "{actor} creates space for a cutting elbow!",
        "{actor} postures up to throw a vicious elbow.",
        "Here comes an elbow attempt from {actor}!"
    ],
    "success_light": [
        "{actor} lands a solid elbow from the top position.",
        "A sharp elbow connects for {actor}.",
        "{actor} finds the mark with a short elbow."
    ],
    "success_heavy": [
        "A NASTY elbow from {actor} connects and cuts {target}!",
        "SLICING elbow lands for {actor}! {target} is bleeding!",
        "{actor} lands a VICIOUS elbow from the top!",
        "BRUTAL elbow strike opens up {target}!",
        "What a CUTTING elbow from {actor}!"
    ],
    "fail": [
        "{target} smothers the elbow attempt expertly.",
        "{target} tucks the chin to avoid elbow damage.",
        "Smart defensive work neutralizes the elbow strike."
    ]
}

# ============================================================================
# POSITION-SPECIFIC GNP TEMPLATES
# These are used instead of generic templates when position is known
# ============================================================================

GNP_BACK_MOUNT_TEMPLATES = {
    "success_light": [
        "{actor} lands short punches to the side of {target}'s head!",
        "{actor} digs in punches while controlling the back.",
        "Short shots connect from {actor} with the back taken.",
        "{actor} punishes {target} from behind.",
    ],
    "success_heavy": [
        "{actor} UNLOADS punches from back control!",
        "VICIOUS shots from {actor} with the hooks in!",
        "{actor} is TEEING OFF from back mount!",
        "{target} is getting HAMMERED from behind!",
    ],
    "fail": [
        "{target} defends the punches while fighting the hooks.",
        "Solid defensive work from {target}.",
        "{target} protects the head well despite the bad position.",
    ]
}

GNP_MOUNT_TEMPLATES = {
    "success_light": [
        "{actor} drops punches from the mount.",
        "{actor} lands shots from full mount.",
        "Ground and pound from mount position by {actor}.",
        "{actor} works the strikes from mount.",
    ],
    "success_heavy": [
        "{actor} is TEEING OFF from full mount!",
        "DEVASTATING ground and pound from mount!",
        "{actor} RAINS DOWN punishment from the mount!",
        "Mount punishment from {actor}!",
    ],
    "fail": [
        "{target} bucks and disrupts the strikes.",
        "{target} covers up to limit damage from mount.",
        "Good defensive awareness from {target} in a bad spot.",
    ]
}

GNP_SIDE_CONTROL_TEMPLATES = {
    "success_light": [
        "{actor} lands from side control.",
        "Short strikes connect from {actor} in side control.",
        "{actor} finds the mark from the top position.",
        "Ground strikes land from {actor} in side control.",
    ],
    "success_heavy": [
        "{actor} drops BOMBS from side control!",
        "HEAVY shots from {actor} in side control!",
        "{actor} is doing DAMAGE from side control!",
        "Side control punishment from {actor}!",
    ],
    "fail": [
        "{target} uses the underhook to disrupt the strikes.",
        "{target} frames well to limit the damage.",
        "Good defensive work from {target} in side control.",
    ]
}

GNP_GUARD_TEMPLATES = {
    "success_light": [
        "A clean punch gets through for {actor} in the guard.",
        "{actor} connects with short punches inside the guard.",
        "Good ground punches from {actor} inside the guard.",
        "{actor} lands shots from inside {target}'s guard.",
    ],
    "success_heavy": [
        "A BIG punch gets through for {actor} in the guard!",
        "BRUTAL punches from {actor} in the guard!",
        "{actor} is doing damage from inside the guard!",
        "{target} is taking shots inside their own guard!",
    ],
    "fail": [
        "{target} does an excellent job of tying up {actor}.",
        "{target} controls the wrists expertly.",
        "{target} maintains the guard excellently.",
        "Smart defensive work from {target} on the bottom.",
    ]
}

GNP_HALF_GUARD_TEMPLATES = {
    "success_light": [
        "{actor} lands from half guard.",
        "Short strikes connect from {actor} in half guard.",
        "{actor} finds openings in half guard.",
        "Ground strikes land in half guard.",
    ],
    "success_heavy": [
        "{actor} lands HEAVY from half guard!",
        "SOLID ground and pound in half guard!",
        "{actor} is doing work from half guard!",
    ],
    "fail": [
        "{target} frames effectively to maintain guard position.",
        "Solid defensive work from {target} prevents the pass.",
        "{target} uses the knee shield to limit damage.",
    ]
}

GNP_ELBOW_POSITION_TEMPLATES = {
    "mount": {
        "success_light": [
            "{actor} lands a solid elbow from the mount.",
            "A sharp elbow connects from mount position.",
            "{actor} digs in an elbow from full mount.",
        ],
        "success_heavy": [
            "SLICING elbow from mount by {actor}!",
            "A VICIOUS elbow from mount opens up {target}!",
            "NASTY elbow strike from mount!",
        ],
    },
    "side_control": {
        "success_light": [
            "{actor} lands a solid elbow from side control.",
            "A sharp elbow connects from side control.",
            "{actor} finds the mark with an elbow from side control.",
        ],
        "success_heavy": [
            "CUTTING elbow from {actor} in side control!",
            "A NASTY elbow from side control!",
            "BRUTAL elbow from {actor} in side control!",
        ],
    },
    "guard": {
        "success_light": [
            "A sharp elbow connects for {actor} inside the guard.",
            "{actor} finds the mark with a short elbow in guard.",
            "{actor} lands an elbow from inside the guard.",
        ],
        "success_heavy": [
            "A NASTY elbow from {actor} inside the guard!",
            "{actor} splits the guard with a VICIOUS elbow!",
            "SLICING elbow lands in the guard!",
        ],
    },
}

# TKO Sequences
GNP_FINISH_ATTEMPT_TEMPLATES = {
    "attempt": [
        "{actor} smells blood and swarms for the finish!",
        "{actor} senses {target} is hurt and pounces!",
        "{actor} isn't letting {target} recover - going for the TKO!",
        "This could be it! {actor} is looking to finish!",
        "{actor} is all over {target} looking for the stoppage!"
    ]
}

TKO_FINISH_TEMPLATES = {
    "success": [
        "STOP THE FIGHT! The referee has seen enough!",
        "IT'S ALL OVER! A devastating TKO victory for {actor}!",
        "THE REFEREE STOPS IT! Vicious ground and pound ends the fight!",
        "THAT'S IT! The fight is stopped! {actor} gets the TKO!",
        "MERCY STOPPAGE! {actor} was unleashing too much punishment!"
    ]
}

KNOCKDOWN_TEMPLATES = {
    "success": [
        "{target} GOES DOWN! What a shot from {actor}!",
        "OH MY GOODNESS! {actor} drops {target} with that strike!",
        "DOWN GOES {target}! A massive blow from {actor}!",
        "{target} hits the canvas HARD from that power shot!",
        "KNOCKDOWN! {actor} just planted {target} with that strike!",
        "THE POWER OF {actor}! {target} is down!"
    ]
}

# Clinch Work
CLINCH_TEMPLATES = {
    "attempt": [
        "{actor} tries to close the distance and clinch up.",
        "{actor} presses forward looking to tie up with {target}.",
        "{actor} initiates the clinch against the cage.",
        "{actor} looks to get into the phone booth with {target}."
    ],
    "success": [
        "{actor} secures the clinch and presses {target} to the fence!",
        "Good clinch work from {actor} as he ties up {target}!",
        "{actor} gets double underhooks in the clinch position!",
        "Excellent clinch control from {actor} against the cage!"
    ],
    "success_light": [
        "{actor} secures the clinch.",
        "{actor} ties up with {target}.",
        "Good clinch work from {actor}."
    ],
    "success_heavy": [
        "{actor} DOMINATES the clinch!",
        "POWERFUL clinch work from {actor}!",
        "{actor} overwhelms {target} in the clinch!"
    ],
    "fail": [
        "{target} circles away beautifully to avoid the clinch.",
        "{target} uses excellent footwork to stay at distance.",
        "Smart movement from {target} keeps the fight at range."
    ]
}

CLINCH_KNEE_TEMPLATES = {
    "attempt": [
        "{actor} looks for a knee to the body from the clinch.",
        "{actor} drives a knee toward the midsection.",
        "{actor} looks to punish {target} with knees in close.",
        "Knees in the clinch coming from {actor}."
    ],
    "success": [
        "A HARD knee lands to the ribs of {target}!",
        "CRUSHING knee to the body from {actor} in the clinch!",
        "{actor} digs a DEEP knee into {target}'s solar plexus!",
        "VICIOUS knee strike from {actor} finds the mark!",
        "That knee from {actor} doubled {target} over!"
    ],
    "success_light": [
        "{actor} lands a solid knee to the body.",
        "A good knee connects for {actor} in the clinch.",
        "{actor} finds the mark with a knee strike."
    ],
    "success_heavy": [
        "A DEVASTATING knee from {actor} to the body!",
        "CRUSHING knee strike doubles {target} over!",
        "VICIOUS knee from {actor} lands flush!"
    ],
    "fail": [
        "{target} manages to block the knee attempt.",
        "{target} angles out nicely to avoid the knee strike.",
        "Good defensive positioning from {target} negates the knee."
    ]
}

CLINCH_ELBOW_TEMPLATES = {
    "attempt": [
        "{actor} looks for a sharp elbow strike in the clinch!",
        "{actor} creates space for a cutting elbow!",
        "{actor} tries to land a vicious elbow up close.",
        "Here comes an elbow attempt from {actor}!"
    ],
    "success_light": [
        "{actor} lands a solid elbow in the clinch.",
        "A sharp elbow connects for {actor}.",
        "{actor} finds success with a short elbow."
    ],
    "success_heavy": [
        "A NASTY elbow from {actor} connects in the clinch!",
        "SLICING elbow lands for {actor}! {target} is cut!",
        "{actor} lands a VICIOUS elbow!",
        "BRUTAL elbow strike opens up {target}!",
        "What a CUTTING elbow from {actor}!"
    ],
    "fail": [
        "{target} smothers the elbow attempt.",
        "{target} tucks his chin to avoid the elbow.",
        "Good defensive work neutralizes the elbow."
    ]
}

ELBOW_TEMPLATES = {
    "attempt": [
        "{actor} looks for a sharp elbow strike!",
        "{actor} creates space for a cutting elbow!",
        "{actor} postures up to throw a vicious elbow.",
        "Here comes an elbow attempt from {actor}!"
    ],
    "success": [
        "A NASTY elbow from {actor} connects and cuts {target}!",
        "SLICING elbow lands for {actor}! {target} is bleeding!",
        "{actor} splits the guard with a VICIOUS elbow!",
        "BRUTAL elbow strike opens up {target}!",
        "What a CUTTING elbow from {actor}!"
    ],
    "success_light": [
        "{actor} lands a solid elbow strike.",
        "A sharp elbow connects for {actor}.",
        "{actor} finds the mark with an elbow."
    ],
    "success_heavy": [
        "DEVASTATING elbow from {actor}!",
        "BRUTAL cutting elbow opens up {target}!",
        "VICIOUS elbow strike lands flush!"
    ],
    "fail": [
        "{target} smothers the elbow attempt expertly.",
        "{target} tucks the chin to avoid elbow damage.",
        "Smart defensive work neutralizes the elbow strike."
    ]
}

# Defensive Actions
SWEEP_TEMPLATES = {
    "attempt": [
        "{actor} is looking for a sweep from the bottom position!",
        "{actor} creates angles to set up a sweep attempt.",
        "{actor} tries to off-balance {target} for a reversal.",
        "Sweep attempt coming from {actor} on the bottom!"
    ],
    "success": [
        "BEAUTIFUL sweep from {actor} to reverse position!",
        "{actor} sweeps {target} and gets top control!",
        "INCREDIBLE technique! {actor} sweeps into the dominant position!",
        "What a slick sweep reversal from {actor}!",
        "TEXTBOOK sweep gives {actor} the top position!"
    ],
    "success_light": [
        "{actor} executes a nice sweep.",
        "{actor} reverses position with a sweep.",
        "Good technique from {actor} to get on top."
    ],
    "success_heavy": [
        "EXPLOSIVE sweep from {actor}!",
        "SPECTACULAR reversal by {actor}!",
        "{actor} with a DOMINANT sweep!"
    ],
    "fail": [
        "{target} feels the sweep coming and maintains his base.",
        "Good balance from {target} prevents the sweep attempt.",
        "{target} sprawls his weight to shut down the sweep."
    ]
}

STAND_UP_TEMPLATES = {
    "attempt": [
        "{actor} is trying to get back to his feet.",
        "{actor} works against the cage to stand up.",
        "{actor} attempts a wall-walk to get vertical.",
        "{actor} doesn't want to be on his back and works to stand."
    ],
    "success": [
        "Excellent scramble! {actor} gets back to his feet!",
        "{actor} successfully returns to the standing position!",
        "Great technique from {actor} to stand back up!",
        "Back to the feet they go! {actor} gets up successfully!"
    ],
    "success_light": [
        "{actor} gets back to his feet.",
        "{actor} stands up successfully.",
        "Good work from {actor} to get vertical."
    ],
    "success_heavy": [
        "EXPLOSIVE standup from {actor}!",
        "{actor} powers back to his feet!",
        "ATHLETIC scramble by {actor} to stand!"
    ],
    "fail": [
        "{target} maintains excellent top control to keep {actor} grounded.",
        "Heavy pressure from {target} prevents {actor} from standing.",
        "{target} uses his weight advantage to keep the fight on the mat."
    ],
    "ref_standup": [
        "The referee stands them up due to inactivity.",
        "Referee calls for a standup - not enough action on the ground.",
        "The ref brings them back to the feet after a stalemate.",
        "Stand up! Referee wants to see more action.",
    ]
}

# Advanced Position Work - GENERIC templates (not guard-specific)
# These are used for various position advances, not just guard passes
ADVANCE_POSITION_TEMPLATES = {
    "attempt": [
        "{actor} is working to improve position.",
        "{actor} methodically works to advance position.",
        "{actor} looks to gain better control.",
        "Position before submission - {actor} looks to improve."
    ],
    "success": [
        "Excellent positional grappling from {actor}!",
        "SMOOTH transition to a more dominant position for {actor}!",
        "{actor} improves position beautifully!",
        "{actor} advances to a better position!",
        "Great positional awareness from {actor}!"
    ],
    "fail": [
        "{target} defends the position change well.",
        "Solid defensive work from {target}.",
        "{target} maintains position excellently."
    ]
}

# Guard-specific pass templates - only used when actually in guard
PASS_GUARD_TEMPLATES = {
    "attempt": [
        "{actor} is working to pass the guard.",
        "{actor} looks to pass and advance.",
        "{actor} pressures the guard looking to pass.",
        "Position before submission - {actor} looks to improve."
    ],
    "success": [
        "BEAUTIFUL guard pass! {actor} moves to side control!",
        "{actor} slices through the guard!",
        "Excellent guard passing from {actor}!",
        "SMOOTH transition past the guard for {actor}!",
        "{actor} passes the guard with beautiful technique!"
    ],
    "success_light": [
        "{actor} successfully passes the guard.",
        "Good positioning from {actor} to advance.",
        "{actor} works past the guard nicely."
    ],
    "success_heavy": [
        "DOMINANT guard pass from {actor}!",
        "{actor} SLICES through the guard!",
        "TEXTBOOK guard passing from {actor}!"
    ],
    "fail": [
        "{target} maintains the guard excellently.",
        "Solid defensive work from {target} prevents the pass.",
        "{target} frames effectively to maintain guard position."
    ]
}

POSTURE_UP_TEMPLATES = {
    "attempt": [
        "{actor} tries to posture up in the guard.",
        "{actor} pushes off the hips to create striking distance.",
        "{actor} looks to break the guard and create space.",
        "{actor} attempts to posture for ground strikes."
    ],
    "success": [
        "{actor} postures up and creates space for strikes!",
        "Good posture from {actor} gives him room to work!",
        "{actor} breaks the guard and postures up successfully!",
        "Excellent posture control from {actor} in the guard!"
    ],
    "fail": [
        "{target} controls the posture beautifully from the guard.",
        "{target} pulls {actor} back down into his guard.",
        "Good guard control from {target} prevents the posture."
    ]
}

# Miscellaneous Actions
DIRTY_BOXING_TEMPLATES = {
    "attempt": [
        "{actor} works some dirty boxing on the inside.",
        "{actor} looks for short punches in tight quarters.",
        "{actor} tries to create damage in close range.",
        "Close-quarters striking from {actor} in the clinch."
    ],
    "success": [
        "Short, POWERFUL punches from {actor} in the clinch!",
        "{actor} lands a BRUTAL uppercut on the inside!",
        "Excellent dirty boxing from {actor} finds its mark!",
        "NASTY inside work from {actor} hurts {target}!"
    ],
    "success_light": [
        "{actor} lands some solid shots in close.",
        "Good dirty boxing from {actor}.",
        "{actor} connects with short punches."
    ],
    "success_heavy": [
        "DEVASTATING inside work from {actor}!",
        "BRUTAL dirty boxing lands flush!",
        "VICIOUS short punches from {actor}!"
    ],
    "fail": [
        "{target} ties up the arms to neutralize the dirty boxing.",
        "Smart clinch work from {target} prevents the inside strikes.",
        "{target} controls the wrists to shut down the attack."
    ]
}

STALLING_TEMPLATES = {
    "attempt": [
        "{actor} applies pressure against the fence to slow the pace.",
        "{actor} uses his weight to lean on {target} and drain energy.",
        "{actor} controls the position to wear down his opponent.",
        "Grinding pressure from {actor} against the cage."
    ],
    "success": [
        "The grinding pressure from {actor} is taking its toll!",
        "{actor} is draining {target}'s energy with this cage control!",
        "Excellent pressure fighting from {actor} is wearing down {target}!",
        "This grinding style from {actor} is visibly exhausting {target}!"
    ],
    "fail": [
        "{target} creates space and breaks away from the pressure.",
        "{target} frames and pivots away from the cage nicely.",
        "Good movement from {target} prevents the grinding."
    ]
}

# Back Control
BACK_CONTROL_TEMPLATES = {
    "success": [
        "{actor} has the back! This is the worst position to be in!",
        "{actor} secures back control with hooks in!",
        "BACK MOUNT! {actor} is in a dominant position!",
        "{actor} takes the back - {target} is in big trouble!"
    ],
    "attempt": [
        "{actor} is working to take the back.",
        "{actor} looks to secure back control.",
        "Here comes the back take attempt from {actor}!"
    ],
    "fail": [
        "{target} defends the back take attempt.",
        "{target} turns into {actor} to prevent the back take.",
        "Good awareness from {target} stops the back take."
    ]
}

ESCAPE_TEMPLATES = {
    "success": [
        "{actor} escapes from the bad position!",
        "Great escape! {actor} works free!",
        "{actor} scrambles out of danger!",
        "Beautiful escape technique from {actor}!"
    ],
    "fail": [
        "{target} maintains the position despite the escape attempt.",
        "{actor} can't find a way out.",
        "{target}'s control is too tight for {actor} to escape."
    ]
}

# Commentary Flow and Color Commentary
MOMENTUM_SHIFTS = [
    "The momentum is shifting here!",
    "The tide is turning in this fight!",
    "What a turnaround we're seeing!",
    "The complexion of this fight is changing!",
    "This is where fights are won and lost!"
]

# (ROUND_TRANSITIONS moved to enhanced templates section above)

FIGHT_IQ_COMMENTS = [
    "Great fight IQ being displayed here!",
    "You can see the chess match unfolding!",
    "The mental aspect of MMA is so important!",
    "Both fighters are showing veteran awareness!",
    "The tactical adjustments are paying off!"
]

DAMAGE_ASSESSMENT = {
    "light": [
        "{target} felt that one but he's still in good shape.",
        "That landed clean but {target} absorbed it well.",
        "{target} is starting to show some wear.",
        "The damage is starting to accumulate on {target}."
    ],
    "moderate": [
        "{target} is starting to look hurt!",
        "You can see the damage building up on {target}!",
        "{target} needs to be careful here!",
        "The punishment is taking its toll on {target}!"
    ],
    "heavy": [
        "{target} is in SERIOUS trouble!",
        "{target} looks badly hurt!",
        "{target} is on unsteady legs!",
        "This could be over soon if {target} doesn't recover!",
        "{target} is hanging on by a thread!"
    ]
}

# Enhanced Fighter Identification
FIGHTER_REFERENCES = {
    "formal": ["{name}"],
    "nickname": ["'{nickname}'", "{name} '{nickname}'"],
    "respectful": ["the veteran {name}", "the experienced {name}"],
    "descriptive": ["the striker {name}", "the grappler {name}", "the wrestler {name}"],
    "geographic": ["the {country} native {name}", "{name} from {country}"],
    "stylistic": ["the {style} specialist {name}"],
    "ranking": ["the #{rank} ranked {name}", "#{rank} {name}"],
    "champion": ["champion {name}", "the defending champion {name}"]
}

# Title fight and late round context
TITLE_FIGHT_CONTEXT = [
    "Championship rounds here!",
    "The title is on the line!",
    "This is what championship fights are all about!",
    "Gold on the line in this title bout!",
    "The championship hangs in the balance!"
]

LATE_ROUND_CONTEXT = [
    "We're in the championship rounds now!",
    "This is where conditioning pays off!",
    "The later rounds separate the contenders from the pretenders!",
    "Deep waters - who wants it more?",
    "Championship heart being tested here!"
]

FINISH_TEMPLATES = {
    "ko": [
        "IT'S ALL OVER! What a knockout!",
        "LIGHTS OUT! {winner} gets the finish!",
        "GOODNIGHT! Spectacular knockout!",
        "BOOM! {winner} with the knockout victory!",
        "OH MY GOODNESS! {winner} just put {loser} to sleep!",
        "DEVASTATING knockout! {winner} ends it in spectacular fashion!"
    ],
    "tko": [
        "THAT'S IT! The referee stops it!",
        "TKO victory for {winner}!",
        "The referee has seen enough!",
        "Excellent stoppage by the referee!",
        "STOP THE FIGHT! {winner} gets the TKO!",
        "The referee jumps in to save {loser}!"
    ],
    "submission": [
        "TAP! TAP! TAP! It's over!",
        "{winner} gets the submission victory!",
        "Beautiful submission finish!",
        "Technical superiority on display!",
        "The submission specialist gets it done!",
        "{winner} forces the tap!"
    ],
    "decision": [
        "After {rounds} rounds, we go to the judges!",
        "This one goes to the scorecards!",
        "A hard-fought battle goes to the judges!",
        "Let's see what the judges have!"
    ]
}

# (ROUND_START_TEMPLATES and ROUND_END_TEMPLATES moved to enhanced templates section above)


# ============================================================================
# INTELLIGENT SYSTEM (Enhanced)
# ============================================================================

class ActionType(Enum):
    """Types of actions that can occur in a fight"""
    STRIKE = "strike"
    KICK = "kick"
    TAKEDOWN = "takedown"
    SUBMISSION = "submission"
    CLINCH = "clinch"
    CLINCH_STRIKE = "clinch_strike"
    GROUND_STRIKE = "ground_strike"
    POSITION_ADVANCE = "position_advance"
    SWEEP = "sweep"
    ESCAPE = "escape"
    STAND_UP = "stand_up"
    KNOCKDOWN = "knockdown"
    FINISH = "finish"


class DamageLevel(Enum):
    """Damage/impact level for commentary selection"""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    DEVASTATING = "devastating"


class EventSignificance(Enum):
    """How significant an event is"""
    ROUTINE = 1
    NOTABLE = 2
    SIGNIFICANT = 3
    DRAMATIC = 4
    HISTORIC = 5


@dataclass
class FightContext:
    """Context information for intelligent commentary"""
    fighter1_name: str
    fighter2_name: str
    fighter1_id: str = ""
    fighter2_id: str = ""
    round_number: int = 1
    total_rounds: int = 3
    is_title_fight: bool = False
    is_main_event: bool = False
    exchanges_per_round: int = 55  # Must match FightConfig default

    # COMMENTARY-ENTRANCES1: card-position + per-fighter intro data.
    # card_slot values: "main_event", "co_main", "main_card",
    # "prelim", "early_prelim". fighter1_data / fighter2_data are
    # dicts with optional keys nickname, record, fighting_style,
    # is_champion, division — silently skipped when missing.
    card_slot: str = "prelim"
    fighter1_data: Dict[str, Any] = field(default_factory=dict)
    fighter2_data: Dict[str, Any] = field(default_factory=dict)

    # COMMENTARY-GAMEPLAN-CONTRAST1: per-fighter gameplan snapshot
    # (preset, aggression, range_bias). Consumed by emit_gameplan_setup
    # + the log_event contrast-firing hook. Empty dict = no gameplan,
    # no contrast possible (silent).
    fighter1_gameplan: Dict[str, Any] = field(default_factory=dict)
    fighter2_gameplan: Dict[str, Any] = field(default_factory=dict)

    # Fight state tracking
    current_damage: Dict[str, float] = field(default_factory=dict)
    knockdowns: Dict[str, int] = field(default_factory=dict)
    momentum: str = "even"  # "fighter1", "fighter2", "even"
    last_significant_action: Optional[str] = None
    
    def __post_init__(self):
        if not self.current_damage:
            self.current_damage = {self.fighter1_name: 0.0, self.fighter2_name: 0.0}
        if not self.knockdowns:
            self.knockdowns = {self.fighter1_name: 0, self.fighter2_name: 0}
        if not self.fighter1_id:
            self.fighter1_id = self.fighter1_name.lower().replace(" ", "_")
        if not self.fighter2_id:
            self.fighter2_id = self.fighter2_name.lower().replace(" ", "_")


@dataclass
class FightEvent:
    """A single event during a fight"""
    event_type: ActionType
    round_num: int
    exchange_num: int
    time_str: str
    
    actor_name: str
    target_name: str
    
    action: str = ""
    success: bool = True
    damage: float = 0.0
    damage_level: DamageLevel = DamageLevel.LIGHT
    significance: EventSignificance = EventSignificance.ROUTINE
    
    commentary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "round": self.round_num,
            "exchange": self.exchange_num,
            "time": self.time_str,
            "actor": self.actor_name,
            "target": self.target_name,
            "action": self.action,
            "success": self.success,
            "damage": self.damage,
            "significance": self.significance.value,
            "commentary": self.commentary
        }


@dataclass
class RoundSummary:
    """Summary of a single round"""
    round_num: int
    fighter1_name: str
    fighter2_name: str
    
    # Stats
    strikes_landed: Dict[str, int] = field(default_factory=dict)
    takedowns: Dict[str, int] = field(default_factory=dict)
    damage_dealt: Dict[str, float] = field(default_factory=dict)
    control_time: Dict[str, float] = field(default_factory=dict)
    knockdowns: Dict[str, int] = field(default_factory=dict)
    
    # Scoring
    score1: int = 10
    score2: int = 10
    round_winner: Optional[str] = None
    
    # Key events
    key_events: List[FightEvent] = field(default_factory=list)
    
    # Narrative
    description: str = ""
    
    def generate_description(self) -> str:
        """Generate round summary narrative"""
        parts = []
        
        # Determine round type
        total_kd = sum(self.knockdowns.values())
        total_td = sum(self.takedowns.values())
        total_control = sum(self.control_time.values())
        
        if total_kd > 0:
            kd_winner = max(self.knockdowns.keys(), key=lambda k: self.knockdowns.get(k, 0))
            parts.append(f"A round marked by {self.knockdowns[kd_winner]} knockdown(s) from {kd_winner}")
        elif total_control > 12:
            control_winner = max(self.control_time.keys(), key=lambda k: self.control_time.get(k, 0))
            parts.append(f"A grappling-heavy round controlled by {control_winner}")
        elif total_td > 2:
            parts.append("A wrestling-focused round")
        else:
            parts.append("A striking battle")
        
        # Winner
        if self.round_winner:
            diff = abs(self.score1 - self.score2)
            if diff >= 2:
                parts.append(f"- clearly won by {self.round_winner}")
            else:
                parts.append(f"- edged by {self.round_winner}")
        else:
            parts.append("- could go either way")
        
        self.description = " ".join(parts) + "."
        return self.description
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            "round_num": self.round_num,
            "fighter1_name": self.fighter1_name,
            "fighter2_name": self.fighter2_name,
            "strikes_landed": self.strikes_landed,
            "takedowns": self.takedowns,
            "damage_dealt": self.damage_dealt,
            "control_time": self.control_time,
            "knockdowns": self.knockdowns,
            "score1": self.score1,
            "score2": self.score2,
            "round_winner": self.round_winner,
            "key_events": [e.to_dict() for e in self.key_events],
            "description": self.description or self.generate_description()
        }


# ============================================================================
# MAIN COMMENTARY ENGINE
# ============================================================================

class FightCommentarySystem:
    """
    Enhanced intelligent commentary system using comprehensive templates.
    
    Features:
    - Context-aware commentary selection
    - Repetition avoidance
    - Event logging and round tracking
    - Post-fight narrative generation
    """
    
    def __init__(self, context: Optional[FightContext] = None):
        self.context = context
        self.events: List[FightEvent] = []
        self.round_summaries: List[RoundSummary] = []
        self.commentary_log: List[str] = []
        
        # Repetition avoidance
        self.recent_templates: Set[str] = set()
        self.template_cooldown = 5  # Don't repeat within 5 uses
        self.recent_queue: List[str] = []
        
        # Current round tracking
        self.current_round = 1
        self.current_exchange = 0
        self.round_stats: Dict[str, Dict] = {}
        
        # Initialize round stats
        self._init_round_stats()
    
    def _init_round_stats(self):
        """Initialize stats for current round"""
        if self.context:
            self.round_stats = {
                self.context.fighter1_name: {
                    "strikes_landed": 0, "takedowns": 0, 
                    "damage": 0.0, "control": 0.0, "knockdowns": 0
                },
                self.context.fighter2_name: {
                    "strikes_landed": 0, "takedowns": 0,
                    "damage": 0.0, "control": 0.0, "knockdowns": 0
                }
            }
    
    def set_context(self, context: FightContext):
        """Set or update fight context"""
        self.context = context
        self._init_round_stats()
    
    def get_time_str(self, exchange: int, exchanges_per_round: Optional[int] = None) -> str:
        """Convert exchange to time string (MM:SS)"""
        # Use provided value, or context value, or default to 55
        if exchanges_per_round is None:
            if self.context and self.context.exchanges_per_round:
                exchanges_per_round = self.context.exchanges_per_round
            else:
                exchanges_per_round = 55  # Default matches FightConfig
        
        total_seconds = int((exchange / exchanges_per_round) * 300)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def _select_template(
        self, 
        templates: List[str], 
        avoid_repeats: bool = True
    ) -> str:
        """Select a template with repetition avoidance"""
        if not templates:
            return ""
        
        if avoid_repeats and len(templates) > 1:
            available = [t for t in templates if t not in self.recent_templates]
            if not available:
                # All used recently, clear oldest
                self.recent_templates.clear()
                available = templates
            selected = random.choice(available)
        else:
            selected = random.choice(templates)
        
        # Track for cooldown
        self.recent_queue.append(selected)
        self.recent_templates.add(selected)
        if len(self.recent_queue) > self.template_cooldown:
            old = self.recent_queue.pop(0)
            self.recent_templates.discard(old)
        
        return selected
    
    def _get_damage_level(self, damage: float) -> DamageLevel:
        """Determine damage level from damage value"""
        if damage >= 15:
            return DamageLevel.DEVASTATING
        elif damage >= 10:
            return DamageLevel.HEAVY
        elif damage >= 5:
            return DamageLevel.MODERATE
        return DamageLevel.LIGHT
    
    def _get_template_key(self, damage_level: DamageLevel, success: bool) -> str:
        """Get template dictionary key based on damage and success"""
        if not success:
            return "fail"
        
        if damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING):
            return "success_heavy"
        elif damage_level == DamageLevel.MODERATE:
            return "success"
        return "success_light"
    
    # ========================================================================
    # FIGHTER STATE DETECTION
    # ========================================================================
    
    def _get_fighter_state(
        self,
        stamina: float = 100.0,
        health: float = 100.0,
        is_hurt: bool = False,
        is_losing: bool = False,
        round_num: int = 1,
        total_rounds: int = 3,
        just_recovered: bool = False,
        is_dominant: bool = False,
    ) -> str:
        """
        Determine fighter's current state for commentary selection.
        
        Returns one of: 'fresh', 'fatigued', 'desperate', 'damaged', 
                       'dominant', 'hurt_recovery'
        """
        # Priority order matters here
        
        # Just recovered from being hurt
        if just_recovered:
            return "hurt_recovery"
        
        # Currently hurt or very damaged
        if is_hurt or health < 40:
            return "damaged"
        
        # Dominating the fight
        if is_dominant:
            return "dominant"
        
        # Desperate - losing in late rounds
        if is_losing and round_num >= (total_rounds - 1):
            return "desperate"
        
        # Fatigued - low stamina or accumulated damage
        if stamina < 50 or health < 60:
            return "fatigued"
        
        # Fresh - good stamina and health
        return "fresh"
    
    # ========================================================================
    # STATE-BASED STRIKE COMMENTARY
    # ========================================================================
    
    def generate_state_based_strike(
        self,
        actor: str,
        target: str,
        strike_type: str = "punch",
        damage: float = 0.0,
        stamina: float = 100.0,
        health: float = 100.0,
        is_hurt: bool = False,
        is_losing: bool = False,
        round_num: int = 1,
        total_rounds: int = 3,
        just_recovered: bool = False,
        is_dominant: bool = False,
    ) -> str:
        """
        Generate strike commentary based on fighter's physical state.
        
        A tired fighter's jab sounds different than a fresh fighter's jab.
        """
        # Determine fighter state
        state = self._get_fighter_state(
            stamina=stamina,
            health=health,
            is_hurt=is_hurt,
            is_losing=is_losing,
            round_num=round_num,
            total_rounds=total_rounds,
            just_recovered=just_recovered,
            is_dominant=is_dominant,
        )
        
        # Get state-specific templates
        state_templates = STATE_BASED_STRIKES.get(state, STATE_BASED_STRIKES["fresh"])
        
        # Determine strike category
        strike_lower = strike_type.lower()
        damage_level = self._get_damage_level(damage)
        
        if damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING):
            category = "heavy"
        elif "kick" in strike_lower:
            category = "kick"
        else:
            category = "punch"
        
        # Get templates for this category
        templates = state_templates.get(category, state_templates.get("punch", []))
        
        if not templates:
            # Fallback to fresh templates
            templates = STATE_BASED_STRIKES["fresh"].get(category, [])
        
        if not templates:
            return f"{actor} throws a {strike_type}."
        
        template = self._select_template(templates)
        commentary = template.format(actor=actor, target=target)
        
        self.commentary_log.append(commentary)
        return commentary
    
    # ========================================================================
    # COMBO COMMENTARY SYSTEM
    # ========================================================================
    
    def generate_combo_commentary(
        self,
        actor: str,
        target: str,
        combo_count: int,
        current_strike: str = "punch",
        is_ground: bool = False,
    ) -> str:
        """
        Generate commentary for strike combinations.
        
        Args:
            actor: Fighter throwing the combo
            target: Fighter receiving
            combo_count: How many strikes in this combo (2, 3, 4+)
            current_strike: The current strike being thrown
            is_ground: Whether this is ground and pound
        
        Returns:
            Combo connector commentary
        """
        if is_ground and combo_count >= 3:
            # Ground and pound flurry
            templates = COMBO_CONNECTORS.get("gnp_flurry", [])
        elif combo_count >= 4:
            # Big flurry
            templates = COMBO_CONNECTORS.get("flurry", [])
        elif combo_count == 3:
            templates = COMBO_CONNECTORS.get("3_hit", [])
        elif combo_count == 2:
            templates = COMBO_CONNECTORS.get("2_hit", [])
        else:
            # Single strike - use combo starter
            templates = COMBO_CONNECTORS.get("combo_start", [])
        
        if not templates:
            return ""
        
        template = self._select_template(templates)
        commentary = template.format(
            actor=actor, 
            target=target, 
            strike=current_strike.replace("_", " ")
        )
        
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_combo_start(
        self,
        actor: str,
        strike: str = "jab",
    ) -> str:
        """Generate the opening of a combination."""
        templates = COMBO_CONNECTORS.get("combo_start", [])
        if not templates:
            return f"{actor} opens up..."
        
        template = self._select_template(templates)
        commentary = template.format(actor=actor, strike=strike.replace("_", " "))
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_combo_finish(
        self,
        actor: str,
        strike: str = "cross",
    ) -> str:
        """Generate the finishing blow of a combination."""
        templates = COMBO_CONNECTORS.get("combo_finish", [])
        if not templates:
            return f"...finishes with the {strike}!"
        
        template = self._select_template(templates)
        commentary = template.format(actor=actor, strike=strike.replace("_", " "))
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_full_combo(
        self,
        actor: str,
        target: str,
        strikes: List[str],
        damage_values: Optional[List[float]] = None,
    ) -> str:
        """
        Generate complete combo commentary from a list of strikes.
        
        Example: ["jab", "cross", "hook"] produces:
        "Actor opens with a jab... and follows with the cross!... 
         AND A THIRD SHOT LANDS! Beautiful combination!"
        """
        if not strikes:
            return ""
        
        lines = []
        
        # First strike - combo start
        first_strike = strikes[0]
        lines.append(self.generate_combo_start(actor, first_strike))
        
        # Middle strikes - connectors
        for i, strike in enumerate(strikes[1:], start=2):
            if i >= 4:
                # Flurry for 4+
                connector = self.generate_combo_commentary(
                    actor, target, i, strike, is_ground=False
                )
            else:
                # Normal connector
                connector = self.generate_combo_commentary(
                    actor, target, i, strike, is_ground=False
                )
            lines.append(connector)
        
        # Combine into flowing commentary
        full_commentary = " ".join(lines)
        return full_commentary
    
    # ========================================================================
    # TREND ANALYSIS / COLOR COMMENTARY
    # ========================================================================
    
    def generate_trend_analysis(
        self,
        trend_type: str,
        actor: str = "",
        target: str = "",
    ) -> str:
        """
        Generate color commentary about fight trends.
        
        Args:
            trend_type: One of the TREND_ANALYSIS keys:
                - 'leg_damage', 'body_damage', 'gassing_out'
                - 'wrestling_dominance', 'striking_outclassed'
                - 'submission_danger', 'counter_timing'
                - 'clinch_dominance', 'pressure_overwhelming'
                - 'adjustment_made', 'close_scorecards', 'pulling_ahead'
            actor: Fighter causing the trend (dominant one)
            target: Fighter suffering from the trend
        
        Returns:
            Color commentary string
        """
        templates = TREND_ANALYSIS.get(trend_type, [])
        
        if not templates:
            return ""
        
        template = self._select_template(templates)
        commentary = template.format(actor=actor, target=target)
        
        self.commentary_log.append(commentary)
        return commentary
    
    def analyze_fight_state(
        self,
        fighter1_name: str,
        fighter2_name: str,
        fighter1_stats: Dict[str, Any],
        fighter2_stats: Dict[str, Any],
        round_num: int = 1,
    ) -> Optional[str]:
        """
        Analyze fight state and generate appropriate trend commentary.
        
        Args:
            fighter1_stats: Dict with keys like 'leg_damage', 'body_damage', 
                           'stamina', 'strikes_landed', 'takedowns', etc.
            fighter2_stats: Same structure
        
        Returns:
            Trend analysis commentary or None if no significant trend
        """
        # Check for leg damage trend
        f1_leg = fighter1_stats.get('leg_damage', 0)
        f2_leg = fighter2_stats.get('leg_damage', 0)
        
        if f1_leg >= 30:
            return self.generate_trend_analysis('leg_damage', 
                                               actor=fighter2_name, 
                                               target=fighter1_name)
        elif f2_leg >= 30:
            return self.generate_trend_analysis('leg_damage',
                                               actor=fighter1_name,
                                               target=fighter2_name)
        
        # Check for body damage trend
        f1_body = fighter1_stats.get('body_damage', 0)
        f2_body = fighter2_stats.get('body_damage', 0)
        
        if f1_body >= 25:
            return self.generate_trend_analysis('body_damage',
                                               actor=fighter2_name,
                                               target=fighter1_name)
        elif f2_body >= 25:
            return self.generate_trend_analysis('body_damage',
                                               actor=fighter1_name,
                                               target=fighter2_name)
        
        # Check for gassing
        f1_stamina = fighter1_stats.get('stamina', 100)
        f2_stamina = fighter2_stats.get('stamina', 100)
        
        if f1_stamina < 40:
            return self.generate_trend_analysis('gassing_out',
                                               actor=fighter1_name,
                                               target=fighter2_name)
        elif f2_stamina < 40:
            return self.generate_trend_analysis('gassing_out',
                                               actor=fighter2_name,
                                               target=fighter1_name)
        
        # Check for wrestling dominance
        f1_td = fighter1_stats.get('takedowns', 0)
        f2_td = fighter2_stats.get('takedowns', 0)
        
        if f1_td >= 3 and f2_td == 0:
            return self.generate_trend_analysis('wrestling_dominance',
                                               actor=fighter1_name,
                                               target=fighter2_name)
        elif f2_td >= 3 and f1_td == 0:
            return self.generate_trend_analysis('wrestling_dominance',
                                               actor=fighter2_name,
                                               target=fighter1_name)
        
        # Check for striking differential
        f1_strikes = fighter1_stats.get('strikes_landed', 0)
        f2_strikes = fighter2_stats.get('strikes_landed', 0)
        
        if f1_strikes >= 3 * max(f2_strikes, 1) and f1_strikes >= 15:
            return self.generate_trend_analysis('striking_outclassed',
                                               actor=fighter1_name,
                                               target=fighter2_name)
        elif f2_strikes >= 3 * max(f1_strikes, 1) and f2_strikes >= 15:
            return self.generate_trend_analysis('striking_outclassed',
                                               actor=fighter2_name,
                                               target=fighter1_name)
        
        # Check for close fight in late rounds
        if round_num >= 3:
            score_diff = abs(
                fighter1_stats.get('score', 0) - fighter2_stats.get('score', 0)
            )
            if score_diff <= 1:
                return self.generate_trend_analysis('close_scorecards',
                                                   actor=fighter1_name,
                                                   target=fighter2_name)
        
        return None
    
    # ========================================================================
    # STYLE-TAGGED STRIKE COMMENTARY
    # ========================================================================
    
    def generate_style_strike(
        self,
        actor: str,
        target: str,
        style: str = "Balanced",
        strike_type: str = "punch",
        damage: float = 0.0,
        is_ko: bool = False,
    ) -> str:
        """
        Generate style-specific strike commentary.
        
        A Brawler landing heavy sounds different than a Technician landing heavy.
        
        Args:
            actor: Fighter throwing
            target: Fighter receiving
            style: Fighter's style (Brawler, Technician, etc.)
            strike_type: Type of strike
            damage: Damage dealt
            is_ko: Whether this is a knockout blow
        """
        # Normalize style name
        style_key = style.replace("_", " ").title()
        
        # Get style-specific templates
        style_templates = STYLE_STRIKES.get(style_key, STYLE_STRIKES.get("Balanced", {}))
        
        # Determine category
        damage_level = self._get_damage_level(damage)
        strike_lower = strike_type.lower()
        
        if is_ko:
            category = "ko_shot"
        elif damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING):
            if "kick" in strike_lower:
                category = "kick_heavy"
            else:
                category = "punch_heavy"
        elif "kick" in strike_lower:
            category = "kick_light"
        elif "elbow" in strike_lower:
            category = "elbow"
        elif "gnp" in strike_lower or "ground" in strike_lower:
            if damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING):
                category = "gnp_heavy"
            else:
                category = "gnp_light"
        else:
            category = "punch_light"
        
        # Try to get templates for this category
        templates = style_templates.get(category)
        
        # Fallback cascade
        if not templates:
            if "heavy" in category:
                templates = style_templates.get("punch_heavy")
            elif "light" in category:
                templates = style_templates.get("punch_light")
        
        if not templates:
            # Ultimate fallback to Balanced style
            balanced = STYLE_STRIKES.get("Balanced", {})
            templates = balanced.get(category, balanced.get("punch_light", []))
        
        if not templates:
            return f"{actor} lands a {strike_type}."
        
        template = self._select_template(templates)
        commentary = template.format(actor=actor, target=target)
        
        self.commentary_log.append(commentary)
        return commentary
    
    # ========================================================================
    # FINISH SEQUENCE COMMENTARY
    # ========================================================================
    
    def generate_finish_sequence(
        self,
        actor: str,
        target: str,
        phase: str = "hurt_followup",
    ) -> str:
        """
        Generate commentary for finish sequences (when a fighter is being finished).
        
        Args:
            phase: One of 'hurt_followup', 'swarming', 'referee_watching', 'final_blow'
        """
        templates = FINISH_SEQUENCE.get(phase, [])
        
        if not templates:
            return ""
        
        template = self._select_template(templates)
        commentary = template.format(actor=actor, target=target)
        
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_full_finish_sequence(
        self,
        actor: str,
        target: str,
    ) -> List[str]:
        """Generate a complete finish sequence with multiple phases."""
        sequence = []
        
        # Phase 1: Target is hurt
        sequence.append(self.generate_finish_sequence(actor, target, "hurt_followup"))
        
        # Phase 2: Attacker swarming
        sequence.append(self.generate_finish_sequence(actor, target, "swarming"))
        
        # Phase 3: Referee watching
        if random.random() < 0.5:  # 50% chance for ref commentary
            sequence.append(self.generate_finish_sequence(actor, target, "referee_watching"))
        
        # Phase 4: Final blow
        sequence.append(self.generate_finish_sequence(actor, target, "final_blow"))
        
        return [s for s in sequence if s]  # Filter empty strings
    
    # ========================================================================
    # ENHANCED STRIKE COMMENTARY (MASTER METHOD)
    # ========================================================================
    
    def generate_enhanced_strike_commentary(
        self,
        actor: str,
        target: str,
        strike_type: str = "punch",
        damage: float = 0.0,
        success: bool = True,
        # State parameters
        actor_stamina: float = 100.0,
        actor_health: float = 100.0,
        actor_is_hurt: bool = False,
        actor_is_losing: bool = False,
        actor_is_dominant: bool = False,
        actor_just_recovered: bool = False,
        # Fight context
        round_num: int = 1,
        total_rounds: int = 3,
        # Combo tracking
        combo_count: int = 1,
        # Style
        actor_style: str = "Balanced",
        # Special flags
        is_ko_shot: bool = False,
        is_ground: bool = False,
    ) -> str:
        """
        Master method that combines all enhanced commentary systems.
        
        This is the recommended method to call for strike commentary.
        It automatically selects the best commentary based on all context.
        """
        if not success:
            # Miss - use standard templates
            return self.generate_strike_commentary(
                actor, target, False, damage, strike_type, is_ground
            )
        
        commentary_parts = []
        
        # 1. If it's part of a combo, use combo connectors
        if combo_count > 1:
            combo_comm = self.generate_combo_commentary(
                actor, target, combo_count, strike_type, is_ground
            )
            if combo_comm:
                return combo_comm  # Combo connectors are complete on their own
        
        # 2. For KO shots, use style-specific KO templates
        if is_ko_shot:
            return self.generate_style_strike(
                actor, target, actor_style, strike_type, damage, is_ko=True
            )
        
        # 3. Determine which system to use based on damage and state
        damage_level = self._get_damage_level(damage)
        state = self._get_fighter_state(
            stamina=actor_stamina,
            health=actor_health,
            is_hurt=actor_is_hurt,
            is_losing=actor_is_losing,
            round_num=round_num,
            total_rounds=total_rounds,
            just_recovered=actor_just_recovered,
            is_dominant=actor_is_dominant,
        )
        
        # For heavy damage, prefer style-specific commentary
        if damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING):
            return self.generate_style_strike(
                actor, target, actor_style, strike_type, damage, is_ko=False
            )
        
        # For non-fresh states, use state-based commentary
        if state != "fresh":
            return self.generate_state_based_strike(
                actor=actor,
                target=target,
                strike_type=strike_type,
                damage=damage,
                stamina=actor_stamina,
                health=actor_health,
                is_hurt=actor_is_hurt,
                is_losing=actor_is_losing,
                round_num=round_num,
                total_rounds=total_rounds,
                just_recovered=actor_just_recovered,
                is_dominant=actor_is_dominant,
            )
        
        # Default: Use standard fresh templates with style flavor
        # Randomly choose between state-based and style-based for variety
        if random.random() < 0.4:  # 40% chance for style commentary
            return self.generate_style_strike(
                actor, target, actor_style, strike_type, damage, is_ko=False
            )
        else:
            return self.generate_state_based_strike(
                actor=actor,
                target=target,
                strike_type=strike_type,
                damage=damage,
                stamina=actor_stamina,
                health=actor_health,
                is_hurt=actor_is_hurt,
                is_losing=actor_is_losing,
                round_num=round_num,
                total_rounds=total_rounds,
                just_recovered=actor_just_recovered,
                is_dominant=actor_is_dominant,
            )
    
    # ========================================================================
    # COMMENTARY GENERATION
    # ========================================================================
    
    def generate_strike_commentary(
        self,
        actor: str,
        target: str,
        success: bool,
        damage: float = 0.0,
        strike_type: str = "punch",
        is_ground: bool = False,
        position: str = ""
    ) -> str:
        """Generate commentary for a strike"""
        damage_level = self._get_damage_level(damage)
        key = self._get_template_key(damage_level, success)
        
        # Select appropriate template dict based on specific strike type
        strike_lower = strike_type.lower()
        position_lower = position.lower() if position else ""
        
        if strike_lower in ("leg_kick", "calf_kick", "low_kick"):
            # Soccer kicks ONLY from knockdown_standing (standing over downed opponent)
            # NOT from guard, mount, or other ground positions
            if "knockdown_standing" in position_lower:
                templates = SOCCER_KICK_TEMPLATES
            else:
                templates = LEG_KICK_TEMPLATES
        elif strike_lower in ("head_kick", "high_kick", "wheel_kick", "spinning_back_kick"):
            templates = HEAD_KICK_TEMPLATES
        elif strike_lower in ("body_kick", "front_kick", "side_kick"):
            templates = BODY_KICK_TEMPLATES
        elif strike_lower == "kick":
            # Generic kick - use generic templates
            templates = KICK_TEMPLATES
        else:
            templates = PUNCH_TEMPLATES
        
        # Get templates for this outcome
        template_list = templates.get(key, templates.get("success_light", []))
        if not template_list and not success:
            template_list = templates.get("miss", [])
        
        if not template_list:
            return f"{actor} {'lands' if success else 'misses with'} a strike."
        
        template = self._select_template(template_list)
        return template.format(actor=actor, target=target)
    
    def generate_takedown_commentary(
        self,
        actor: str,
        target: str,
        success: bool,
        damage: float = 0.0
    ) -> str:
        """Generate commentary for a takedown"""
        damage_level = self._get_damage_level(damage)
        
        if success:
            key = "success_heavy" if damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING) else "success"
            if key not in TAKEDOWN_TEMPLATES:
                key = "success"
        else:
            key = "fail"
        
        template_list = TAKEDOWN_TEMPLATES.get(key, [])
        if not template_list:
            return f"{actor} {'completes' if success else 'fails with'} a takedown."
        
        template = self._select_template(template_list)
        return template.format(actor=actor, target=target)
    
    def generate_submission_commentary(
        self,
        actor: str,
        target: str,
        move: str,
        stage: str = "attempt"  # "attempt", "locked", "escape", "finish"
    ) -> str:
        """Generate commentary for submission"""
        move_clean = move.replace("_", " ").title()
        
        if stage == "attempt":
            template_list = SUB_ENTRY_TEMPLATES.get("success", [])
        elif stage == "locked":
            template_list = [
                "{actor} has the {move} locked in tight!",
                "The {move} is sunk in deep!",
                "{target} is fighting the {move}!"
            ]
        elif stage == "escape_dramatic":
            template_list = SUB_ESCAPE_DRAMATIC_TEMPLATES
        elif stage == "escape_tight":
            template_list = SUB_ESCAPE_TIGHT_TEMPLATES
        elif stage == "escape":
            template_list = SUB_ENTRY_TEMPLATES.get("fail", [])
        else:  # finish
            template_list = SUBMISSION_TEMPLATES.get("success", [])
        
        if not template_list:
            return f"{actor} attempts a {move_clean}."
        
        template = self._select_template(template_list)
        return template.format(actor=actor, target=target, move=move_clean)
    
    def generate_gnp_commentary(
        self,
        actor: str,
        target: str,
        success: bool,
        damage: float = 0.0,
        strike_type: str = "punch",
        position: str = ""
    ) -> str:
        """Generate ground and pound commentary with position-awareness"""
        damage_level = self._get_damage_level(damage)
        key = self._get_template_key(damage_level, success)
        
        strike_lower = strike_type.lower() if strike_type else "punch"
        position_lower = position.lower() if position else ""
        
        # Route to position-specific templates based on position
        if "elbow" in strike_lower:
            # Check for position-specific elbow templates
            if "back_mount" in position_lower or "back mount" in position_lower:
                # Back mount uses punch templates for elbows (limited elbow options)
                templates = GNP_BACK_MOUNT_TEMPLATES
            elif "mount" in position_lower and "back" not in position_lower:
                pos_templates = GNP_ELBOW_POSITION_TEMPLATES.get("mount", {})
                template_list = pos_templates.get(key, pos_templates.get("success_light", []))
                if template_list:
                    template = self._select_template(template_list)
                    return template.format(actor=actor, target=target)
                templates = GNP_ELBOW_TEMPLATES
            elif "side_control" in position_lower or "side control" in position_lower:
                pos_templates = GNP_ELBOW_POSITION_TEMPLATES.get("side_control", {})
                template_list = pos_templates.get(key, pos_templates.get("success_light", []))
                if template_list:
                    template = self._select_template(template_list)
                    return template.format(actor=actor, target=target)
                templates = GNP_ELBOW_TEMPLATES
            elif "guard" in position_lower and "half" not in position_lower:
                pos_templates = GNP_ELBOW_POSITION_TEMPLATES.get("guard", {})
                template_list = pos_templates.get(key, pos_templates.get("success_light", []))
                if template_list:
                    template = self._select_template(template_list)
                    return template.format(actor=actor, target=target)
                templates = GNP_ELBOW_TEMPLATES
            else:
                templates = GNP_ELBOW_TEMPLATES
        else:
            # Punches/hammer fists - use position-specific templates
            if "back_mount" in position_lower or "back mount" in position_lower:
                templates = GNP_BACK_MOUNT_TEMPLATES
            elif "mount" in position_lower and "back" not in position_lower:
                templates = GNP_MOUNT_TEMPLATES
            elif "side_control" in position_lower or "side control" in position_lower:
                templates = GNP_SIDE_CONTROL_TEMPLATES
            elif "half_guard" in position_lower or "half guard" in position_lower:
                templates = GNP_HALF_GUARD_TEMPLATES
            elif "guard" in position_lower:
                # full_guard, closed_guard, butterfly_guard, etc.
                templates = GNP_GUARD_TEMPLATES
            else:
                # Fallback to generic templates (but remove guard-specific text)
                templates = GNP_PUNCH_TEMPLATES
        
        template_list = templates.get(key, templates.get("success_light", []))
        if not template_list:
            return f"{actor} lands ground strikes."
        
        template = self._select_template(template_list)
        return template.format(actor=actor, target=target)
    
    def generate_clinch_commentary(
        self,
        actor: str,
        target: str,
        action: str,
        success: bool,
        damage: float = 0.0
    ) -> str:
        """Generate clinch work commentary"""
        damage_level = self._get_damage_level(damage)
        key = self._get_template_key(damage_level, success)
        
        if action in ("knee", "clinch_knee"):
            templates = CLINCH_KNEE_TEMPLATES
        elif action in ("elbow", "clinch_elbow"):
            templates = CLINCH_ELBOW_TEMPLATES
        elif action == "dirty_boxing":
            templates = DIRTY_BOXING_TEMPLATES
        else:
            templates = CLINCH_TEMPLATES
        
        template_list = templates.get(key, [])
        if not template_list:
            template_list = templates.get("success" if success else "fail", [])
        if not template_list:
            return f"{actor} works in the clinch."
        
        template = self._select_template(template_list)
        return template.format(actor=actor, target=target)
    
    def generate_position_commentary(
        self,
        actor: str,
        target: str,
        action: str,
        success: bool
    ) -> str:
        """Generate position change commentary"""
        action_lower = action.lower() if action else ""
        
        # Sweeps and reversals
        if action_lower in ("sweep", "reversal", "scissor_sweep", "flower_sweep", 
                           "hip_bump", "elevator_sweep", "butterfly_sweep"):
            templates = SWEEP_TEMPLATES
        # Referee standup
        elif action_lower == "ref_standup":
            template_list = STAND_UP_TEMPLATES.get("ref_standup", [])
            if template_list:
                template = self._select_template(template_list)
                return template.format(actor=actor, target=target)
            return "The referee stands them up."
        # Fighter getting up
        elif action_lower in ("stand_up", "standup", "get_up"):
            templates = STAND_UP_TEMPLATES
        # Guard passes - use guard-specific templates
        elif action_lower in ("pass_to_side", "pass_to_mount", "pass_to_half", 
                             "knee_slice", "torreando", "guard_pass"):
            templates = PASS_GUARD_TEMPLATES
        # Escapes
        elif action_lower in ("escape", "reguard", "pop_head_out", "escape_legs",
                             "granby_roll"):
            templates = ESCAPE_TEMPLATES
        # Back takes
        elif action_lower in ("back_take", "back_control", "take_back"):
            templates = BACK_CONTROL_TEMPLATES
        # All other position advances - use GENERIC templates
        else:
            templates = ADVANCE_POSITION_TEMPLATES
        
        key = "success" if success else "fail"
        template_list = templates.get(key, [])
        
        if not template_list:
            if success:
                return f"{actor} improves position."
            else:
                return f"{target} defends the position change."
        
        template = self._select_template(template_list)
        return template.format(actor=actor, target=target)

    
    def generate_knockdown_commentary(
        self,
        actor: str,
        target: str
    ) -> str:
        """Generate knockdown commentary"""
        template_list = KNOCKDOWN_TEMPLATES.get("success", [])
        if not template_list:
            return f"{actor} drops {target}!"
        
        template = self._select_template(template_list)
        return template.format(actor=actor, target=target)
    
    def generate_finish_commentary(
        self,
        winner: str,
        loser: str,
        method: str
    ) -> str:
        """Generate finish commentary"""
        method_lower = method.lower()
        
        if "ko" in method_lower and "tko" not in method_lower:
            templates = FINISH_TEMPLATES.get("ko", [])
        elif "tko" in method_lower:
            templates = FINISH_TEMPLATES.get("tko", [])
        elif "sub" in method_lower:
            templates = FINISH_TEMPLATES.get("submission", [])
        else:
            templates = FINISH_TEMPLATES.get("decision", [])
        
        if not templates:
            return f"{winner} wins by {method}!"
        
        template = self._select_template(templates)
        return template.format(winner=winner, loser=loser, rounds=self.current_round)
    
    def generate_damage_assessment(
        self,
        target: str,
        damage_level: DamageLevel
    ) -> str:
        """Generate damage assessment commentary"""
        key = damage_level.value
        if key == "devastating":
            key = "heavy"
        
        templates = DAMAGE_ASSESSMENT.get(key, [])
        if not templates:
            return ""
        
        template = self._select_template(templates)
        return template.format(target=target)
    
    # ========================================================================
    # EVENT LOGGING
    # ========================================================================
    
    def log_event(
        self,
        action_type: ActionType,
        actor: str,
        target: str,
        action: str = "",
        success: bool = True,
        damage: float = 0.0,
        exchange_num: Optional[int] = None,
        is_ground: bool = False,
        new_position: Optional[str] = None,
        target_health: Optional[float] = None,
        position: str = ""
    ) -> FightEvent:
        """Log a fight event and generate commentary"""
        if exchange_num is not None:
            self.current_exchange = exchange_num
        
        damage_level = self._get_damage_level(damage)
        
        # Determine significance
        significance = EventSignificance.ROUTINE
        if action_type == ActionType.KNOCKDOWN:
            significance = EventSignificance.DRAMATIC
        elif action_type == ActionType.FINISH:
            significance = EventSignificance.HISTORIC
        elif damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING):
            significance = EventSignificance.SIGNIFICANT
        elif action_type in (ActionType.TAKEDOWN, ActionType.SUBMISSION):
            significance = EventSignificance.NOTABLE
        
        # Generate commentary based on action type
        commentary = self._generate_commentary_for_action(
            action_type, actor, target, action, success, damage, is_ground, position
        )
        
        event = FightEvent(
            event_type=action_type,
            round_num=self.current_round,
            exchange_num=self.current_exchange,
            time_str=self.get_time_str(self.current_exchange),
            actor_name=actor,
            target_name=target,
            action=action,
            success=success,
            damage=damage,
            damage_level=damage_level,
            significance=significance,
            commentary=commentary
        )
        
        self.events.append(event)
        
        # Log commentary - include more events for better play-by-play
        # The key is logging enough action to make the fight feel alive
        should_log = False
        
        if significance.value >= EventSignificance.NOTABLE.value:
            # Always log notable, significant, dramatic, historic events
            # (takedowns, submissions, knockdowns, finishes, etc.)
            should_log = True
        elif success and damage > 0:
            # Log ALL successful strikes that deal damage - this is the fight action!
            should_log = True
        elif action_type in (ActionType.STRIKE, ActionType.KICK, ActionType.CLINCH_STRIKE, ActionType.GROUND_STRIKE):
            # Log some missed strikes for variety (roughly every 3rd one)
            if len(self.commentary_log) % 3 == 0:
                should_log = True
        elif action_type in (ActionType.CLINCH, ActionType.POSITION_ADVANCE, ActionType.SWEEP, ActionType.ESCAPE, ActionType.STAND_UP):
            # Sample grappling transitions like missed strikes —
            # was always-on, caused grappling to crowd out striking.
            if len(self.commentary_log) % 3 == 0:
                should_log = True
        elif action_type == ActionType.TAKEDOWN:
            # Always log takedown attempts (success or fail)
            should_log = True

        if should_log and commentary:
            self.commentary_log.append(commentary)

        # COMMENTARY-GAMEPLAN-CONTRAST1: fire the once-per-fighter
        # style-vs-plan contrast callout when the current event matches
        # the armed contrast's real-action trigger. Silent when actor
        # has no armed contrast, has already fired, or event doesn't
        # match. Never asserts an outcome — plan/intent observation
        # prose only.
        self._maybe_emit_contrast_callout(actor, action_type, damage_level, success)

        # === Position announcement when position changes ===
        # Suppress when action_type already mentioned position
        # (TAKEDOWN / CLINCH / POSITION_ADVANCE) to avoid the
        # triple-log pattern: action line + position-change line +
        # this announcement all firing for one grappling event.
        _grapple_already_logged = action_type in (
            ActionType.TAKEDOWN, ActionType.CLINCH,
            ActionType.POSITION_ADVANCE,
        )
        if new_position and success and not _grapple_already_logged:
            pos_commentary = self._generate_position_announcement(actor, target, new_position)
            if pos_commentary:
                self.commentary_log.append(pos_commentary)
        
        # === NEW: Pre-finish buildup when target health is critical ===
        if target_health is not None and target_health < 25 and success and damage > 0:
            buildup = self._generate_hurt_buildup(actor, target, target_health)
            if buildup:
                self.commentary_log.append(buildup)
        
        # Update round stats
        self._update_round_stats(actor, action_type, success, damage)
        
        return event
    
    def _generate_position_announcement(
        self,
        actor: str,
        target: str,
        position: str
    ) -> str:
        """Generate announcement for new ground position"""
        # Position-specific announcements
        position_lower = position.lower() if position else ""
        
        if "mount" in position_lower and "back" not in position_lower:
            templates = [
                f"{actor} is in full mount!",
                f"{actor} has mounted {target}!",
                f"Mount position! {target} is in BIG trouble!",
            ]
        elif "back_mount" in position_lower or "back mount" in position_lower:
            templates = [
                f"{actor} has the back! Hooks are in!",
                f"Back control for {actor}! This is DANGEROUS!",
                f"{actor} takes the back! Rear naked choke is RIGHT THERE!",
            ]
        elif "side_control" in position_lower or "side control" in position_lower:
            templates = [
                f"{actor} settles into side control.",
                f"Side control for {actor}. Heavy top pressure.",
                f"{actor} has side control. Looking to advance or strike.",
            ]
        elif "half_guard" in position_lower or "half guard" in position_lower:
            templates = [
                f"Half guard position.",
                f"{actor} is in half guard, working to pass.",
            ]
        elif "full_guard" in position_lower or "full guard" in position_lower:
            templates = [
                f"Full guard position. {target} controlling from bottom.",
                f"{actor} is in {target}'s full guard.",
            ]
        elif "turtle" in position_lower:
            templates = [
                f"{target} turtles up. {actor} looking for openings.",
                f"Turtle position. {actor} working for the back.",
            ]
        elif "crucifix" in position_lower:
            templates = [
                f"{actor} has the CRUCIFIX! This is a nightmare!",
                f"Crucifix position! Unanswered strikes incoming!",
            ]
        elif "truck" in position_lower:
            templates = [
                f"{actor} enters the TRUCK position! Calf slicer or twister incoming!",
                f"TRUCK POSITION! {actor} is hunting for a leg attack!",
                f"{actor} rolls into the truck! {target} is in serious danger!",
                f"The truck position! {actor} looking for the calf slicer or twister!",
            ]
        elif "north_south" in position_lower or "north south" in position_lower:
            templates = [
                f"{actor} transitions to north-south.",
                f"North-south position. Kimura is there.",
            ]
        elif "knockdown" in position_lower:
            templates = [
                f"{actor} standing over the downed {target}!",
                f"{target} is on the canvas! {actor} looking to finish!",
            ]
        elif "clinch" in position_lower:
            templates = [
                f"They're clinched up!",
                f"Into the clinch!",
            ]
        elif "standing" in position_lower:
            # Don't announce standing - it's obvious
            return ""
        else:
            # Generic position change
            return ""
        
        return random.choice(templates) if templates else ""
    
    def _generate_hurt_buildup(
        self,
        actor: str,
        target: str,
        target_health: float
    ) -> str:
        """Generate pre-finish buildup commentary when fighter is badly hurt"""
        # Only generate buildup commentary sometimes to avoid spam
        if random.random() > 0.4:  # 40% chance
            return ""
        
        if target_health < 10:
            # Critical - about to be finished
            templates = [
                f"{target} is in SERIOUS trouble! How much more can they take?!",
                f"The referee is watching CLOSELY! {target} may not survive much longer!",
                f"{target} is DONE! Just a matter of time!",
                f"This could be stopped at ANY MOMENT!",
                f"{actor} smells blood! {target} is barely standing!",
            ]
        elif target_health < 18:
            # Very hurt
            templates = [
                f"{target} is HURT! {actor} pouncing!",
                f"{target}'s legs are GONE! They're in survival mode!",
                f"{actor} is ALL OVER {target}! The finish is NEAR!",
                f"How much more can {target} take?!",
                f"{target} is getting PIECED UP!",
            ]
        else:
            # Hurt but surviving
            templates = [
                f"{target} is in trouble!",
                f"{actor} has {target} hurt!",
                f"{target} is absorbing SERIOUS damage!",
                f"The damage is accumulating on {target}!",
            ]
        
        return random.choice(templates)
    
    def _generate_commentary_for_action(
        self,
        action_type: ActionType,
        actor: str,
        target: str,
        action: str,
        success: bool,
        damage: float,
        is_ground: bool = False,
        position: str = ""
    ) -> str:
        """Generate appropriate commentary for an action type"""
        if action_type == ActionType.STRIKE:
            return self.generate_strike_commentary(actor, target, success, damage, action, is_ground, position)
        elif action_type == ActionType.KICK:
            # Pass the actual kick type (leg_kick, head_kick, etc.) and ground state
            return self.generate_strike_commentary(actor, target, success, damage, action, is_ground, position)
        elif action_type == ActionType.TAKEDOWN:
            return self.generate_takedown_commentary(actor, target, success, damage)
        elif action_type == ActionType.SUBMISSION:
            return self.generate_submission_commentary(actor, target, action, "attempt")
        elif action_type == ActionType.CLINCH:
            return self.generate_clinch_commentary(actor, target, "clinch", success, damage)
        elif action_type == ActionType.CLINCH_STRIKE:
            return self.generate_clinch_commentary(actor, target, action, success, damage)
        elif action_type == ActionType.GROUND_STRIKE:
            return self.generate_gnp_commentary(actor, target, success, damage, action, position)
        elif action_type in (ActionType.POSITION_ADVANCE, ActionType.SWEEP, ActionType.ESCAPE, ActionType.STAND_UP):
            return self.generate_position_commentary(actor, target, action, success)
        elif action_type == ActionType.KNOCKDOWN:
            return self.generate_knockdown_commentary(actor, target)
        elif action_type == ActionType.FINISH:
            return self.generate_finish_commentary(actor, target, action)
        
        return f"{actor} {'succeeds' if success else 'fails'} with {action}."
    
    def _update_round_stats(
        self,
        actor: str,
        action_type: ActionType,
        success: bool,
        damage: float
    ):
        """Update round statistics"""
        if actor not in self.round_stats:
            return
        
        if success:
            if action_type in (ActionType.STRIKE, ActionType.KICK, ActionType.CLINCH_STRIKE, ActionType.GROUND_STRIKE):
                self.round_stats[actor]["strikes_landed"] += 1
                self.round_stats[actor]["damage"] += damage
            elif action_type == ActionType.TAKEDOWN:
                self.round_stats[actor]["takedowns"] += 1
            elif action_type == ActionType.KNOCKDOWN:
                self.round_stats[actor]["knockdowns"] += 1

    # ========================================================================
    # COMMENTARY-ENTRANCES1 — fight-open surface
    # ========================================================================

    def _entrance_descriptor(self, fdata: Dict[str, Any]) -> str:
        """Return the descriptor clause used inside main-event entrance
        lines: 'the DFC {division} champion' if that fighter carries the
        belt AND division is known, else a short style-tag, else a safe
        generic fallback. Never returns an empty string."""
        if fdata.get("is_champion") and fdata.get("division"):
            return f"the DFC {fdata['division']} champion"
        style = fdata.get("fighting_style") or ""
        tag = _STYLE_ENTRANCE_TAG.get(style)
        return tag or "with something to prove"

    def _nick_clause(self, fdata: Dict[str, Any]) -> str:
        """Return ' \"The Nickname\"' if a nickname exists, else empty."""
        n = fdata.get("nickname")
        return f' "{n}"' if n else ""

    def emit_fight_open(self) -> None:
        """Append card-position line + slot-scaled fighter entrances to
        the log. Called once at fight open, BEFORE the first
        start_round. Idempotent — subsequent calls no-op. Silent when
        context or fighter data is missing (safe additive contract).

        Emits, in order:
          1. one card-position line, keyed by card_slot
          2. optional champion line (main_event / co_main only, if
             either fighter has is_champion + division)
          3. entrance lines: two lines at main_event (one per corner),
             one combined line at co_main, one short line at main_card,
             one terse line at prelim / early_prelim
        Callers that don't opt in (no fighter data, default slot) get
        the default prelim card-position + terse entrance line.
        """
        if getattr(self, '_fight_open_emitted', False):
            return
        self._fight_open_emitted = True
        if not self.context:
            return

        slot = (self.context.card_slot or "prelim").lower()
        f1_data = self.context.fighter1_data or {}
        f2_data = self.context.fighter2_data or {}
        f1_name = self.context.fighter1_name
        f2_name = self.context.fighter2_name

        # 1. Card-position line
        if slot == "main_event":
            self.commentary_log.append(random.choice(CARD_POSITION_MAIN_EVENT))
        elif slot == "co_main":
            self.commentary_log.append(random.choice(CARD_POSITION_CO_MAIN))
        elif slot == "main_card":
            self.commentary_log.append(random.choice(CARD_POSITION_MAIN_CARD))
        elif slot == "early_prelim":
            self.commentary_log.append(random.choice(CARD_POSITION_EARLY_PRELIM))
        else:
            self.commentary_log.append(random.choice(CARD_POSITION_PRELIM))

        # 2. Optional champion line — main_event / co_main only
        if slot in ("main_event", "co_main"):
            champ_name = champ_div = ""
            if f1_data.get("is_champion") and f1_data.get("division"):
                champ_name = f1_name
                champ_div = f1_data["division"]
            elif f2_data.get("is_champion") and f2_data.get("division"):
                champ_name = f2_name
                champ_div = f2_data["division"]
            if champ_name:
                self.commentary_log.append(
                    random.choice(FIGHTER_ENTRANCE_CHAMPION_LINE).format(
                        name=champ_name, division=champ_div))

        # 3. Entrance lines — scaled by slot
        if slot == "main_event":
            self.commentary_log.append(
                random.choice(FIGHTER_ENTRANCE_MAIN_EVENT_RED).format(
                    name=f1_name,
                    nick_clause=self._nick_clause(f1_data),
                    record=f1_data.get("record") or "0-0",
                    descriptor=self._entrance_descriptor(f1_data),
                ))
            self.commentary_log.append(
                random.choice(FIGHTER_ENTRANCE_MAIN_EVENT_BLUE).format(
                    name=f2_name,
                    nick_clause=self._nick_clause(f2_data),
                    record=f2_data.get("record") or "0-0",
                    descriptor=self._entrance_descriptor(f2_data),
                ))
        elif slot == "co_main":
            self.commentary_log.append(
                random.choice(FIGHTER_ENTRANCE_CO_MAIN).format(
                    f1_name=f1_name,
                    f1_nick=self._nick_clause(f1_data),
                    f1_rec=f1_data.get("record") or "0-0",
                    f2_name=f2_name,
                    f2_nick=self._nick_clause(f2_data),
                    f2_rec=f2_data.get("record") or "0-0",
                ))
        elif slot == "main_card":
            self.commentary_log.append(
                random.choice(FIGHTER_ENTRANCE_MAIN_CARD).format(
                    f1_name=f1_name, f2_name=f2_name,
                ))
        else:  # prelim, early_prelim, or unknown → terse
            self.commentary_log.append(
                random.choice(FIGHTER_ENTRANCE_PRELIM).format(
                    f1_name=f1_name, f2_name=f2_name,
                ))

    # ========================================================================
    # COMMENTARY-GAMEPLAN-CONTRAST1 — style-vs-plan contrast callouts
    # ========================================================================

    def _detect_contrast(self, style: str, gp: Dict[str, Any]) -> Optional[str]:
        """Return a contrast tag ('grappler_not_grappling',
        'aggressor_going_patient', 'counter_becoming_aggressor') or
        None if no contrast is armed for this style/plan pair.

        Category-1 (grappler_not_grappling): grapple-based style AND
        preset in {AGGRESSIVE, DEFENSIVE}. Wrestler+MEASURED and
        neutral cases stay silent per Van's exclude list.

        Category-2 (aggressor_going_patient): forward stand-up style
        AND aggression < 0. Van's guard: BOTH conditions required —
        a forward fighter on AGGRESSIVE who's forced to disengage
        fires nothing.

        Category-3 (counter_becoming_aggressor): counter/point style
        AND aggression > 0.
        """
        if not style or not gp:
            return None
        preset = str(gp.get("preset", "") or "").upper()
        aggression = int(gp.get("aggression", 0) or 0)
        if style in _CONTRAST_GRAPPLE_STYLES and preset in _CONTRAST_C1_OFFTYPE_PRESETS:
            return "grappler_not_grappling"
        if style in _CONTRAST_FORWARD_STYLES and aggression < 0:
            return "aggressor_going_patient"
        if style in _CONTRAST_COUNTER_STYLES and aggression > 0:
            return "counter_becoming_aggressor"
        return None

    def _actor_to_key(self, actor_name: str) -> Optional[str]:
        """Match actor name to 'f1'/'f2' or None."""
        if not self.context or not actor_name:
            return None
        if actor_name == self.context.fighter1_name:
            return "f1"
        if actor_name == self.context.fighter2_name:
            return "f2"
        return None

    def _init_contrast_state(self) -> None:
        """One-time init of contrast tracking state. Called lazily so
        older callers that don't invoke emit_gameplan_setup still get
        safe defaults (all fighters unarmed → no fires).
        """
        if getattr(self, '_contrast_state_ready', False):
            return
        self._contrast_state_ready = True
        self._contrast_armed = {"f1": None, "f2": None}
        self._contrast_fired = {"f1": False, "f2": False}
        # Mode B setup emitted at fight open — flag is just for
        # bookkeeping / verification; doesn't gate the mid-fight callout.
        self._contrast_setup_emitted = {"f1": False, "f2": False}

    def emit_gameplan_setup(self) -> None:
        """Detect contrast for both sides and, per armed side, roll
        Mode A / Mode B (~50/50). If Mode B, append a pre-fight setup
        line to the log. Called ONCE at fight open, AFTER
        emit_fight_open and AFTER the AGGRESSION-NARRATION1 intent
        block. Silent when a fighter has no contrast armed (default).
        """
        self._init_contrast_state()
        if not self.context:
            return

        for key, name, data_field, gp_field in (
            ("f1", self.context.fighter1_name,
             self.context.fighter1_data, self.context.fighter1_gameplan),
            ("f2", self.context.fighter2_name,
             self.context.fighter2_data, self.context.fighter2_gameplan),
        ):
            style = str((data_field or {}).get("fighting_style", "") or "")
            tag = self._detect_contrast(style, gp_field or {})
            if tag is None:
                continue
            self._contrast_armed[key] = tag
            # Roll Mode A / Mode B. Mode B → emit a setup line now.
            if random.random() < 0.5:
                setup_pool = {
                    "grappler_not_grappling":     CONTRAST_SETUP_GRAPPLER,
                    "aggressor_going_patient":    CONTRAST_SETUP_PATIENT,
                    "counter_becoming_aggressor": CONTRAST_SETUP_COUNTER,
                }[tag]
                self.commentary_log.append(
                    random.choice(setup_pool).format(
                        name=name,
                        label=_CONTRAST_STYLE_LABEL.get(style, "fighter"),
                    ))
                self._contrast_setup_emitted[key] = True

    def _contrast_trigger_matches(self, tag: str, event_type: 'ActionType',
                                   damage_level: 'DamageLevel',
                                   success: bool) -> bool:
        """Return True if this event is the real-action trigger for
        the given contrast tag. Only successful actions count for
        triggers 1 and 3 (an air-swing miss isn't an observation of
        the plan behavior).
        """
        if tag == "grappler_not_grappling":
            # Actor engaged on the feet with a strike.
            return success and event_type in (
                ActionType.STRIKE, ActionType.KICK, ActionType.CLINCH_STRIKE)
        if tag == "aggressor_going_patient":
            # Actor explicitly disengaged. STAND_UP / ESCAPE fire even
            # without success — the intent to disengage IS the signal.
            return event_type in (ActionType.STAND_UP, ActionType.ESCAPE)
        if tag == "counter_becoming_aggressor":
            # Actor committed hard: TAKEDOWN attempt (any) or a
            # HEAVY/DEVASTATING successful strike.
            if event_type == ActionType.TAKEDOWN:
                return True
            if success and event_type in (
                ActionType.STRIKE, ActionType.KICK, ActionType.CLINCH_STRIKE,
                ActionType.GROUND_STRIKE,
            ):
                return damage_level in (DamageLevel.HEAVY, DamageLevel.DEVASTATING)
        return False

    def _maybe_emit_contrast_callout(self, actor_name: str,
                                      event_type: 'ActionType',
                                      damage_level: 'DamageLevel',
                                      success: bool) -> None:
        """Called from log_event AFTER the base commentary append.
        Fires the mid-fight contrast callout ONCE per fighter per
        fight when the trigger matches. Silent when the actor has no
        armed contrast, has already fired, or the event doesn't
        match the tag's trigger."""
        self._init_contrast_state()
        key = self._actor_to_key(actor_name)
        if key is None:
            return
        tag = self._contrast_armed.get(key)
        if tag is None:
            return
        if self._contrast_fired.get(key):
            return
        if not self._contrast_trigger_matches(tag, event_type, damage_level, success):
            return

        # Resolve style label + name for template format
        data_field = (self.context.fighter1_data if key == "f1"
                      else self.context.fighter2_data) or {}
        style = str(data_field.get("fighting_style", "") or "")
        label = _CONTRAST_STYLE_LABEL.get(style, "fighter")
        name = actor_name

        pool = {
            "grappler_not_grappling":     CONTRAST_GRAPPLER_NOT_GRAPPLING,
            "aggressor_going_patient":    CONTRAST_AGGRESSOR_GOING_PATIENT,
            "counter_becoming_aggressor": CONTRAST_COUNTER_BECOMING_AGGRESSOR,
        }[tag]
        self.commentary_log.append(random.choice(pool).format(name=name, label=label))
        self._contrast_fired[key] = True

    # ========================================================================
    # ROUND MANAGEMENT
    # ========================================================================

    def start_round(self, round_num: int) -> str:
        """Start a new round"""
        self.current_round = round_num
        self.current_exchange = 0
        self._init_round_stats()

        # COMMENTARY-CHAMPIONSHIP-FIX1 — read total_rounds so we pick
        # the right pool. Final round of ANY fight → FINAL. Championship
        # rounds (4-5) only exist in 5-round fights → CHAMPIONSHIP.
        # R3 of a 3-round fight IS the final round, never championship.
        # Everything else falls through to the generic mid-round pool.
        # The prior addendum block (TITLE_FIGHT_CONTEXT / LATE_ROUND_
        # CONTEXT) was a workaround for the old always-generic pool
        # selection; now redundant since FINAL and CHAMPIONSHIP pools
        # already carry that voice.
        total = self.context.total_rounds if self.context else 3
        if round_num == total:
            template = random.choice(ROUND_START_FINAL)
        elif total == 5 and round_num >= 4:
            template = random.choice(ROUND_START_CHAMPIONSHIP)
        else:
            template = self._select_template(ROUND_START_TEMPLATES)
        commentary = template.format(round_num=round_num)

        self.commentary_log.append(commentary)
        return commentary
    
    def end_round(
        self, 
        score1: int = 10, 
        score2: int = 10,
        control_time_data: Optional[Dict[str, float]] = None
    ) -> RoundSummary:
        """End the current round and create summary"""
        template = self._select_template(ROUND_END_TEMPLATES)
        commentary = template.format(round_num=self.current_round)
        self.commentary_log.append(commentary)
        
        # Create summary
        if self.context:
            f1, f2 = self.context.fighter1_name, self.context.fighter2_name
        else:
            f1, f2 = "Fighter 1", "Fighter 2"
        
        # Use control_time_data if provided, otherwise empty
        control_time = control_time_data if control_time_data else {}
        
        summary = RoundSummary(
            round_num=self.current_round,
            fighter1_name=f1,
            fighter2_name=f2,
            strikes_landed={f1: self.round_stats.get(f1, {}).get("strikes_landed", 0),
                          f2: self.round_stats.get(f2, {}).get("strikes_landed", 0)},
            takedowns={f1: self.round_stats.get(f1, {}).get("takedowns", 0),
                      f2: self.round_stats.get(f2, {}).get("takedowns", 0)},
            damage_dealt={f1: self.round_stats.get(f1, {}).get("damage", 0.0),
                        f2: self.round_stats.get(f2, {}).get("damage", 0.0)},
            knockdowns={f1: self.round_stats.get(f1, {}).get("knockdowns", 0),
                       f2: self.round_stats.get(f2, {}).get("knockdowns", 0)},
            control_time=control_time,
            score1=score1,
            score2=score2,
            round_winner=f1 if score1 > score2 else (f2 if score2 > score1 else None)
        )
        
        # Add key events
        for event in self.events:
            if event.round_num == self.current_round and event.significance.value >= EventSignificance.SIGNIFICANT.value:
                summary.key_events.append(event)
        
        summary.generate_description()
        self.round_summaries.append(summary)
        
        # Add round summary to commentary
        self.commentary_log.append(f"[Round {self.current_round}: {summary.description}]")
        
        # Add transition commentary
        if self.current_round < (self.context.total_rounds if self.context else 3):
            self.commentary_log.append(random.choice(ROUND_TRANSITIONS))
        
        return summary
    
    # ========================================================================
    # ANALYSIS AND OUTPUT
    # ========================================================================
    
    def get_full_commentary(self) -> str:
        """Get complete commentary log as string"""
        return "\n".join(self.commentary_log)
    
    def get_key_moments(self) -> List[FightEvent]:
        """Get significant events from the fight"""
        return [e for e in self.events if e.significance.value >= EventSignificance.SIGNIFICANT.value]
    
    def get_fight_narrative(self, winner: Optional[str] = None, method: str = "") -> str:
        """Generate post-fight narrative summary"""
        lines = []
        
        if winner:
            lines.append(f"WINNER: {winner} by {method}")
            lines.append("")
        
        # Round summaries
        lines.append("ROUND-BY-ROUND:")
        for summary in self.round_summaries:
            score_str = f"({summary.score1}-{summary.score2})"
            lines.append(f"  Round {summary.round_num} {score_str}: {summary.description}")
        
        # Key moments
        key_moments = self.get_key_moments()
        if key_moments:
            lines.append("")
            lines.append("KEY MOMENTS:")
            for event in key_moments[:5]:
                lines.append(f"  R{event.round_num} {event.time_str}: {event.commentary}")
        
        # Stats summary
        if self.context and self.round_summaries:
            lines.append("")
            lines.append("FIGHT STATISTICS:")
            
            f1, f2 = self.context.fighter1_name, self.context.fighter2_name
            
            total_strikes = {f1: 0, f2: 0}
            total_td = {f1: 0, f2: 0}
            total_kd = {f1: 0, f2: 0}
            
            for s in self.round_summaries:
                total_strikes[f1] += s.strikes_landed.get(f1, 0)
                total_strikes[f2] += s.strikes_landed.get(f2, 0)
                total_td[f1] += s.takedowns.get(f1, 0)
                total_td[f2] += s.takedowns.get(f2, 0)
                total_kd[f1] += s.knockdowns.get(f1, 0)
                total_kd[f2] += s.knockdowns.get(f2, 0)
            
            lines.append(f"  Significant Strikes: {f1} {total_strikes[f1]} - {total_strikes[f2]} {f2}")
            lines.append(f"  Takedowns: {f1} {total_td[f1]} - {total_td[f2]} {f2}")
            if sum(total_kd.values()) > 0:
                lines.append(f"  Knockdowns: {f1} {total_kd[f1]} - {total_kd[f2]} {f2}")
        
        return "\n".join(lines)
    
    # ========================================================================
    # FIGHT INTRO GENERATION
    # ========================================================================
    
    def generate_fight_intro(
        self,
        fighter1_data: Optional[Dict[str, Any]] = None,
        fighter2_data: Optional[Dict[str, Any]] = None,
        division: str = "",
        is_main_event: bool = False,
        heat_level: int = 0,
    ) -> List[str]:
        """
        Generate a Buffer-style fight introduction.
        
        Args:
            fighter1_data: Dict with keys like 'name', 'nickname', 'wins', 'losses', 
                          'location', 'style', 'is_champion'
            fighter2_data: Same structure for opponent
            division: Weight class name
            is_main_event: If this is the main event of the card
            heat_level: Rivalry heat level 0-100 (affects intro tone)
        
        Returns:
            List of intro lines for display
        """
        lines = []
        
        # Opening
        if self.context and self.context.is_title_fight:
            lines.append(random.choice(FIGHT_INTRO_TITLE_OPENING))
        elif is_main_event:
            lines.append(random.choice(FIGHT_INTRO_OPENING))
        else:
            lines.append("Ladies and gentlemen, the following contest is scheduled for "
                        f"{self.context.total_rounds if self.context else 3} rounds!")
        
        lines.append("")
        
        # Add heat commentary if there's significant heat
        if heat_level > 80:
            lines.append(random.choice(HEAT_PREFIGHT_WAR))
            lines.append("")
        elif heat_level > 60:
            lines.append(random.choice(HEAT_PREFIGHT_HEATED))
            lines.append("")
        elif heat_level > 40:
            lines.append(random.choice(HEAT_PREFIGHT_BAD_BLOOD))
            lines.append("")
        elif heat_level > 20:
            lines.append(random.choice(HEAT_PREFIGHT_TENSION))
            lines.append("")
        
        # Fighter 1 (Red corner)
        lines.append(random.choice(FIGHTER_INTRO_RED_CORNER))
        lines.extend(self._generate_fighter_intro(fighter1_data, division, is_champion=False))
        lines.append("")
        
        # Fighter 2 (Blue corner) - often the favorite/champion
        lines.append(random.choice(FIGHTER_INTRO_BLUE_CORNER))
        is_champ = fighter2_data.get('is_champion', False) if fighter2_data else False
        if is_champ and self.context and self.context.is_title_fight:
            lines.append(random.choice(FIGHTER_INTRO_CHAMPION).format(division=division))
        lines.extend(self._generate_fighter_intro(fighter2_data, division, is_champion=is_champ))
        lines.append("")
        
        # Closing
        lines.append(random.choice(FIGHT_INTRO_CLOSING))
        
        # Add to commentary log
        for line in lines:
            if line:
                self.commentary_log.append(line)
        
        return lines
    
    def _generate_fighter_intro(
        self,
        fighter_data: Optional[Dict[str, Any]],
        division: str,
        is_champion: bool = False
    ) -> List[str]:
        """Generate intro lines for a single fighter."""
        if not fighter_data:
            return ["[Fighter]"]
        
        lines = []
        name = fighter_data.get('name', 'Unknown Fighter')
        nickname = fighter_data.get('nickname', '')
        wins = fighter_data.get('wins', 0)
        losses = fighter_data.get('losses', 0)
        location = fighter_data.get('location', '')
        style = fighter_data.get('style', 'Balanced')
        
        # Style-based intro
        style_key = style.replace("_", " ").title()
        if style_key in FIGHTER_INTRO_STYLE_TAGS:
            lines.append(random.choice(FIGHTER_INTRO_STYLE_TAGS[style_key]))
        
        # Record
        lines.append(random.choice(FIGHTER_INTRO_RECORD).format(wins=wins, losses=losses))
        
        # Location (if available)
        if location:
            lines.append(random.choice(FIGHTER_INTRO_LOCATION).format(location=location))
        
        # Name with nickname
        if nickname:
            nick_line = random.choice(FIGHTER_INTRO_NICKNAME_STYLE).format(nickname=nickname)
            lines.append(f"{name} {nick_line}!")
        else:
            lines.append(f"{name.upper()}!")
        
        return lines
    
    def generate_touch_gloves_moment(
        self,
        fighter1_name: str,
        fighter2_name: str,
        heat_level: int = 0
    ) -> str:
        """Generate commentary for the touch gloves moment based on heat level.
        
        Args:
            fighter1_name: First fighter's name
            fighter2_name: Second fighter's name
            heat_level: Rivalry heat level 0-100
        
        Returns:
            Commentary string for the touch gloves moment
        """
        if heat_level > 80:
            # WAR - High chance of refusing
            if random.random() < 0.85:
                template = random.choice(TOUCH_GLOVES_REFUSED_HEAT)
                return template.format(fighter1=fighter1_name, fighter2=fighter2_name)
            else:
                return random.choice(TOUCH_GLOVES_RELUCTANT)
        elif heat_level > 60:
            # HEATED - Moderate chance of refusing
            if random.random() < 0.60:
                template = random.choice(TOUCH_GLOVES_REFUSED_HEAT)
                return template.format(fighter1=fighter1_name, fighter2=fighter2_name)
            else:
                return random.choice(TOUCH_GLOVES_RELUCTANT)
        elif heat_level > 40:
            # BAD BLOOD - Small chance of refusing
            if random.random() < 0.30:
                template = random.choice(TOUCH_GLOVES_REFUSED_HEAT)
                return template.format(fighter1=fighter1_name, fighter2=fighter2_name)
            else:
                return random.choice(TOUCH_GLOVES_RELUCTANT)
        elif heat_level > 20:
            # TENSION - Reluctant touch
            return random.choice(TOUCH_GLOVES_RELUCTANT)
        else:
            # NEUTRAL - Normal touch
            return random.choice(TOUCH_GLOVES_NORMAL)
    
    def generate_postfight_respect_moment(
        self,
        winner_name: str,
        loser_name: str,
        heat_level: int = 0
    ) -> Optional[str]:
        """Generate commentary for post-fight respect (or lack thereof).
        
        Args:
            winner_name: Winner's name
            loser_name: Loser's name
            heat_level: Rivalry heat level 0-100
        
        Returns:
            Commentary string or None if no special moment
        """
        if heat_level <= 40:
            # Not enough heat for a special moment
            return None
        
        if heat_level > 80:
            # WAR - Usually no respect shown
            if random.random() < 0.85:
                template = random.choice(HEAT_POSTFIGHT_NO_TOUCH)
                return template.format(winner=winner_name, loser=loser_name)
            else:
                # Rare touching moment after war
                template = random.choice(HEAT_POSTFIGHT_RESPECT)
                return template.format(winner=winner_name, loser=loser_name)
        elif heat_level > 60:
            # HEATED - 50/50
            if random.random() < 0.50:
                template = random.choice(HEAT_POSTFIGHT_NO_TOUCH)
            else:
                template = random.choice(HEAT_POSTFIGHT_RESPECT)
            return template.format(winner=winner_name, loser=loser_name)
        else:
            # BAD BLOOD - Usually show respect after
            if random.random() < 0.70:
                template = random.choice(HEAT_POSTFIGHT_RESPECT)
                return template.format(winner=winner_name, loser=loser_name)
            return None
    
    # ========================================================================
    # FIGHT OUTRO GENERATION
    # ========================================================================
    
    def generate_fight_outro(
        self,
        winner: str,
        loser: str,
        method: str,
        division: str = "",
        rounds: int = 3,
        is_title_fight: bool = False,
        title_changed: bool = False,
        submission_type: str = "",
    ) -> List[str]:
        """
        Generate post-fight celebration/announcement.
        
        Args:
            winner: Winner's name
            loser: Loser's name  
            method: 'KO', 'TKO', 'Submission', 'Decision'
            division: Weight class
            rounds: Total rounds fought
            is_title_fight: Was this for a belt
            title_changed: Did the belt change hands
            submission_type: If sub, what type
        """
        lines = []
        method_lower = method.lower()
        
        # Method-specific outro
        if method_lower == 'ko':
            lines.append(random.choice(FIGHT_OUTRO_KO).format(winner=winner, loser=loser))
        elif method_lower == 'tko':
            lines.append(random.choice(FIGHT_OUTRO_TKO).format(winner=winner, loser=loser))
        elif 'submission' in method_lower or 'sub' in method_lower:
            outro = random.choice(FIGHT_OUTRO_SUBMISSION)
            lines.append(outro.format(winner=winner, loser=loser, method=submission_type or "submission"))
        else:  # Decision
            lines.append(random.choice(FIGHT_OUTRO_DECISION).format(rounds=rounds))
        
        lines.append("")
        
        # Title fight specific
        if is_title_fight:
            if title_changed:
                lines.append(random.choice(FIGHT_OUTRO_TITLE_WIN).format(
                    winner=winner, loser=loser, division=division
                ))
            else:
                lines.append(random.choice(FIGHT_OUTRO_TITLE_DEFENSE).format(
                    winner=winner, division=division
                ))
            lines.append("")
        
        # Winner celebration
        lines.append(random.choice(FIGHT_OUTRO_WINNER_CELEBRATION).format(winner=winner))
        
        # Respect for loser (sometimes)
        if random.random() < 0.6:
            lines.append(random.choice(FIGHT_OUTRO_LOSER_RESPECT).format(loser=loser))
        
        # Add to log
        for line in lines:
            if line:
                self.commentary_log.append(line)
        
        return lines
    
    # ========================================================================
    # CORNER COMMENTARY
    # ========================================================================
    
    def generate_corner_commentary(
        self,
        fighter_name: str,
        is_winning: bool = True,
        is_hurt: bool = False,
        opponent_style: str = "",
        fighter_style: str = "",
    ) -> str:
        """Generate corner advice between rounds."""
        
        if is_hurt:
            advice = random.choice(CORNER_ADVICE_HURT)
        elif is_winning:
            advice = random.choice(CORNER_ADVICE_WINNING)
        else:
            advice = random.choice(CORNER_ADVICE_LOSING)
        
        # Style-specific advice
        style_advice = ""
        fighter_style_lower = fighter_style.lower() if fighter_style else ""
        opponent_style_lower = opponent_style.lower() if opponent_style else ""
        
        if any(s in fighter_style_lower for s in ['striker', 'boxing', 'muay']):
            if any(s in opponent_style_lower for s in ['wrestler', 'grappl', 'bjj']):
                style_advice = random.choice(CORNER_ADVICE_STRIKER_VS_GRAPPLER)
        elif any(s in fighter_style_lower for s in ['wrestler', 'grappl', 'bjj']):
            if any(s in opponent_style_lower for s in ['striker', 'boxing', 'muay']):
                style_advice = random.choice(CORNER_ADVICE_GRAPPLER_VS_STRIKER)
        
        # Build commentary
        lines = [random.choice(CORNER_ADVICE_GENERAL)]
        lines.append(advice)
        if style_advice:
            lines.append(style_advice)
        lines.append(random.choice(CORNER_WATER_CUT))
        
        commentary = " ".join(lines)
        self.commentary_log.append(f"[CORNER] {commentary}")
        return commentary
    
    # ========================================================================
    # POSITION TRANSITION COMMENTARY
    # ========================================================================
    
    def generate_position_transition(
        self,
        actor: str,
        from_position: str,
        to_position: str,
        action_type: str = "",
    ) -> str:
        """Generate commentary for position changes."""
        
        from_lower = from_position.lower() if from_position else ""
        to_lower = to_position.lower() if to_position else ""
        action_lower = action_type.lower() if action_type else ""
        
        # Detect transition type
        if 'standing' in from_lower and 'guard' in to_lower:
            # Takedown or guard pull
            if 'pull_guard' in action_lower:
                template = random.choice(POSITION_TRANSITION_GUARD_PULL)
                commentary = template.format(actor=actor)
            else:
                commentary = random.choice(POSITION_TRANSITION_TO_GROUND)
        elif 'standing' in from_lower and 'clinch' in to_lower:
            commentary = random.choice(POSITION_TRANSITION_TO_CLINCH)
        elif 'standing' in to_lower:
            commentary = random.choice(POSITION_TRANSITION_TO_STANDING)
        elif any(pos in to_lower for pos in ['mount', 'back', 'side_control', 'crucifix']):
            commentary = random.choice(POSITION_TRANSITION_TO_DOMINANT)
        elif 'scramble' in action_lower:
            commentary = random.choice(POSITION_TRANSITION_SCRAMBLE)
        else:
            commentary = f"{actor} transitions to {to_position}."
        
        self.commentary_log.append(commentary)
        return commentary
    
    # ========================================================================
    # GUARD PULL COMMENTARY
    # ========================================================================
    
    def generate_guard_pull_commentary(
        self,
        actor: str,
        target: str,
        success: bool = True,
    ) -> str:
        """Generate commentary for guard pull attempts."""
        if success:
            main = random.choice(GUARD_PULL_TEMPLATES["success"]).format(actor=actor, target=target)
            extra = random.choice(GUARD_PULL_TEMPLATES["success_commentary"]).format(actor=actor, target=target)
            consequence = random.choice(GUARD_PULL_TEMPLATES["consequence"]).format(
                actor=actor, target=target, 
                bottom=actor, top=target
            )
            commentary = f"{main} {extra} {consequence}"
        else:
            commentary = random.choice(GUARD_PULL_TEMPLATES["fail"]).format(actor=actor, target=target)
        
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_ground_position_commentary(
        self,
        position: str,
        top_fighter: str,
        bottom_fighter: str,
    ) -> str:
        """Generate position-specific ground commentary."""
        position_lower = position.lower().replace(" ", "_")
        
        templates = GROUND_POSITION_COMMENTARY.get(position_lower)
        if templates:
            template = random.choice(templates)
            commentary = template.format(top=top_fighter, bottom=bottom_fighter)
        else:
            commentary = f"{top_fighter} in {position} over {bottom_fighter}."
        
        self.commentary_log.append(commentary)
        return commentary
    
    # ========================================================================
    # ENHANCED MOMENTUM COMMENTARY
    # ========================================================================
    
    def generate_momentum_shift(self, gaining_fighter: str) -> str:
        """Generate dramatic momentum shift commentary."""
        commentary = random.choice(MOMENTUM_SHIFT_DRAMATIC)
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_hurt_commentary(self, hurt_fighter: str) -> str:
        """Generate commentary when a fighter is badly hurt."""
        template = random.choice(FIGHTER_HURT_BADLY)
        commentary = template.format(target=hurt_fighter)
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_recovery_commentary(self, recovering_fighter: str) -> str:
        """Generate commentary when a fighter recovers from being hurt."""
        template = random.choice(FIGHTER_RECOVERS)
        commentary = template.format(actor=recovering_fighter)
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_exhaustion_commentary(self, tired_fighter: str) -> str:
        """Generate commentary for exhausted fighter."""
        template = random.choice(FIGHTER_EXHAUSTED)
        commentary = template.format(actor=tired_fighter)
        self.commentary_log.append(commentary)
        return commentary
    
    def generate_crowd_reaction(self) -> str:
        """Generate crowd reaction commentary."""
        commentary = random.choice(CROWD_REACTIONS)
        self.commentary_log.append(commentary)
        return commentary
    
    # ========================================================================
    # ENHANCED ROUND MANAGEMENT
    # ========================================================================
    
    def start_round_enhanced(
        self,
        round_num: int,
        total_rounds: int = 3,
        is_close_fight: bool = False,
        fighter1_hurt: bool = False,
        fighter2_hurt: bool = False,
    ) -> str:
        """Enhanced round start with context-aware commentary."""
        self.current_round = round_num
        self.current_exchange = 0
        self._init_round_stats()
        
        # Select appropriate template based on round
        if round_num == 1:
            template = random.choice(ROUND_START_ROUND_1)
            commentary = template
        elif round_num == total_rounds:
            template = random.choice(ROUND_START_FINAL)
            commentary = template.format(round_num=round_num)
        elif round_num >= 4:  # Championship rounds
            template = random.choice(ROUND_START_CHAMPIONSHIP)
            commentary = template.format(round_num=round_num)
        else:
            template = self._select_template(ROUND_START_TEMPLATES)
            commentary = template.format(round_num=round_num)
        
        # Add context
        if is_close_fight and round_num > 1:
            commentary += " " + random.choice(ROUND_START_CLOSE_FIGHT).format(round_num=round_num)
        
        # Title fight context
        if self.context and self.context.is_title_fight and round_num >= 4:
            commentary += " " + random.choice(TITLE_FIGHT_CONTEXT)
        elif round_num >= 3:
            commentary += " " + random.choice(LATE_ROUND_CONTEXT)
        
        self.commentary_log.append(commentary)
        return commentary
    
    def end_round_enhanced(
        self,
        round_num: int,
        total_rounds: int,
        score1: int = 10,
        score2: int = 10,
        was_action_packed: bool = False,
        was_dominant: bool = False,
        hurt_fighter: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Enhanced round end with state-based transitions.
        
        Returns:
            Tuple of (end_commentary, transition_commentary)
        """
        # Select end template
        if was_action_packed:
            end_template = random.choice(ROUND_END_ACTION_PACKED)
        elif was_dominant:
            end_template = random.choice(ROUND_END_DOMINANT)
        else:
            end_template = self._select_template(ROUND_END_TEMPLATES)
        
        end_commentary = end_template.format(round_num=round_num)
        self.commentary_log.append(end_commentary)
        
        # Transition commentary (if not final round)
        transition = ""
        if round_num < total_rounds:
            # Select based on fight state
            score_diff = abs(score1 - score2)
            
            if hurt_fighter:
                transition = random.choice(ROUND_TRANSITION_HURT).format(hurt_fighter=hurt_fighter)
            elif score_diff >= 3:  # One-sided fight
                transition = random.choice(ROUND_TRANSITION_ONE_SIDED)
            elif score_diff == 0:  # Close fight
                transition = random.choice(ROUND_TRANSITION_CLOSE)
            else:
                transition = random.choice(ROUND_TRANSITIONS)
            
            self.commentary_log.append(transition)
        
        return end_commentary, transition
    
    def to_dict(self) -> Dict[str, Any]:
        """Export fight data as dictionary"""
        return {
            "context": {
                "fighter1": self.context.fighter1_name if self.context else "",
                "fighter2": self.context.fighter2_name if self.context else "",
                "rounds": self.context.total_rounds if self.context else 3,
                "is_title_fight": self.context.is_title_fight if self.context else False
            },
            "events": [e.to_dict() for e in self.events],
            "round_summaries": [
                {
                    "round": s.round_num,
                    "score1": s.score1,
                    "score2": s.score2,
                    "winner": s.round_winner,
                    "description": s.description
                }
                for s in self.round_summaries
            ],
            "commentary_lines": len(self.commentary_log),
            "key_moments": len(self.get_key_moments())
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_commentary_system(
    fighter1_name: str,
    fighter2_name: str,
    total_rounds: int = 3,
    is_title_fight: bool = False,
    exchanges_per_round: int = 55,
    card_slot: str = "prelim",
    is_main_event: bool = False,
    fighter1_data: Optional[Dict[str, Any]] = None,
    fighter2_data: Optional[Dict[str, Any]] = None,
    fighter1_gameplan: Optional[Dict[str, Any]] = None,
    fighter2_gameplan: Optional[Dict[str, Any]] = None,
) -> FightCommentarySystem:
    """Create a new commentary system with context.

    COMMENTARY-ENTRANCES1 kwargs are additive and default to safe
    values (prelim slot, no per-fighter intro data). Callers that
    don't opt in get byte-identical behavior on every hook other
    than the new emit_fight_open (which stays silent without
    fighter1_data / fighter2_data).
    """
    context = FightContext(
        fighter1_name=fighter1_name,
        fighter2_name=fighter2_name,
        total_rounds=total_rounds,
        is_title_fight=is_title_fight,
        exchanges_per_round=exchanges_per_round,
        card_slot=card_slot,
        is_main_event=is_main_event,
        fighter1_data=fighter1_data or {},
        fighter2_data=fighter2_data or {},
        fighter1_gameplan=fighter1_gameplan or {},
        fighter2_gameplan=fighter2_gameplan or {},
    )
    return FightCommentarySystem(context)


def generate_quick_commentary(
    action_type: str,
    actor: str,
    target: str,
    success: bool = True,
    damage: float = 0.0
) -> str:
    """Generate one-off commentary without full system"""
    system = FightCommentarySystem()
    
    type_map = {
        "strike": ActionType.STRIKE,
        "punch": ActionType.STRIKE,
        "kick": ActionType.KICK,
        "takedown": ActionType.TAKEDOWN,
        "submission": ActionType.SUBMISSION,
        "clinch": ActionType.CLINCH,
        "gnp": ActionType.GROUND_STRIKE,
        "knockdown": ActionType.KNOCKDOWN
    }
    
    action = type_map.get(action_type.lower(), ActionType.STRIKE)
    return system._generate_commentary_for_action(action, actor, target, action_type, success, damage)
