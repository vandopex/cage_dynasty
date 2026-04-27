# narrative/media.py
# Module: Media Personalities System
# Lines: ~520
#
# Defines MMA media personalities with distinct biases and voices.
# Generates biased social media reactions based on fight results.

"""
Cage Dynasty - Media Personalities System

7 fictional MMA media personalities who react to fights based on their biases:
- @TheSalSantinoShow - Pro-Knockout, hates decisions
- @MatSideWithMarco - Pro-Grappling/BJJ snob
- @TakedownTedShow - Pro-Wrestling, blunt
- @CageStoryWithCass - Loves underdogs and narratives
- @TheVinceVecchioShow - Pro-Veteran, respects experience
- @TheRickyRavensShow - Contrarian hot takes
- @FightMathWithFelix - Stats and milestones only

USAGE:
    from narrative.media import (
        get_commentator,
        get_all_commentators,
        generate_post_fight_take,
        generate_media_reactions,
        should_generate_reactions,
        select_commentators_for_fight,
    )
    
    # Check if fight warrants reactions
    if should_generate_reactions(fight_context):
        # Get appropriate commentators based on fight type
        commentators = select_commentators_for_fight(fight_context)
        reactions = generate_media_reactions(fight_result, commentators)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
import random


# ============================================================================
# ENUMS
# ============================================================================

class CommentatorBias(Enum):
    """Core bias that shapes commentary perspective."""
    PRO_KNOCKOUT = "pro_knockout"
    PRO_GRAPPLING = "pro_grappling"
    PRO_WRESTLING = "pro_wrestling"
    LOVES_UNDERDOGS = "loves_underdogs"
    PRO_VETERAN = "pro_veteran"
    CONTRARIAN = "contrarian"
    STATS_ANALYTICS = "stats_analytics"


class FightSignificance(Enum):
    """How significant a fight is for media coverage."""
    TITLE_FIGHT = "title_fight"
    MAIN_EVENT = "main_event"
    UPSET = "upset"
    KNOCKOUT = "knockout"
    SUBMISSION = "submission"
    STREAK = "streak"
    DEBUT_FINISH = "debut_finish"
    VETERAN_WIN = "veteran_win"
    PROSPECT_BREAKOUT = "prospect_breakout"
    NORMAL = "normal"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Commentator:
    """A media personality with distinct voice and bias."""
    handle: str
    name: str
    bias: CommentatorBias
    one_liner: str
    
    # What types of fights they're most likely to comment on
    preferred_topics: List[FightSignificance] = field(default_factory=list)
    
    # Phrase libraries
    ko_win: List[str] = field(default_factory=list)
    sub_win: List[str] = field(default_factory=list)
    decision_win: List[str] = field(default_factory=list)
    upset_win: List[str] = field(default_factory=list)
    dominant_win: List[str] = field(default_factory=list)
    close_fight: List[str] = field(default_factory=list)
    veteran_win: List[str] = field(default_factory=list)
    veteran_loss: List[str] = field(default_factory=list)
    prospect_win: List[str] = field(default_factory=list)
    title_fight: List[str] = field(default_factory=list)
    streak: List[str] = field(default_factory=list)
    generic: List[str] = field(default_factory=list)
    
    def get_phrase(self, category: str) -> str:
        """Get a random phrase from a category."""
        phrases = getattr(self, category, None)
        if phrases:
            return random.choice(phrases)
        return random.choice(self.generic) if self.generic else ""
    
    def wants_to_comment(self, significance: FightSignificance) -> float:
        """Return probability (0-1) that this commentator wants to react."""
        if significance in self.preferred_topics:
            return 0.9
        # Base probability for non-preferred topics
        return 0.3


# ============================================================================
# THE 7 PERSONALITIES
# ============================================================================

SAL_SANTINO = Commentator(
    handle="@TheSalSantinoShow",
    name="Sal Santino",
    bias=CommentatorBias.PRO_KNOCKOUT,
    one_liner="SLEEP! Hates decisions.",
    preferred_topics=[
        FightSignificance.KNOCKOUT, 
        FightSignificance.TITLE_FIGHT,
        FightSignificance.MAIN_EVENT,
    ],
    
    ko_win=[
        "SLEEEEEEP! That man has a FAMILY!",
        "GOODNIGHT! That's what this sport is ABOUT!",
        "VIOLENCE! Beautiful, beautiful violence!",
        "OUT COLD! Don't even need to check, he's done!",
        "FLATLINED! That's the knockout of the year candidate right there!",
        "TIMBER! He fell like a tree!",
        "Send that one to the highlight reel IMMEDIATELY!",
        "BOOM! That's why we watch, people!",
        "LIGHTS OUT! That's the fight game!",
        "STIFF! Absolutely stiff! What a shot!",
    ],
    sub_win=[
        "Submission win. Fine. At least it didn't go to the scorecards.",
        "Tap or snap. He made the right call. Still would've preferred a knockout.",
        "Got the finish. I'll take it.",
        "Choke was tight. But imagine if he'd just CRACKED him instead.",
    ],
    decision_win=[
        "Decision. Wake me up when someone throws with bad intentions.",
        "Went to the scorecards. Another nap for me.",
        "Three rounds and nobody got finished? Waste of everyone's time.",
        "Congrats on the win, I guess. Fans wanted a finish.",
        "A 'dominant' decision is still a decision. Be better.",
        "Point fighting isn't fighting. It's jogging with punches.",
    ],
    upset_win=[
        "UPSET CITY! And he did it with his HANDS!",
        "Nobody saw that coming! Well, the knockout gods did!",
        "Ranked fighters getting SLEPT! You love to see it!",
    ],
    dominant_win=[
        "DESTRUCTION! That wasn't a fight, that was an execution!",
        "He didn't just beat him, he BROKE him!",
    ],
    close_fight=[
        "Close fight that should've been a FINISH! Both guys too passive!",
        "Back and forth but neither guy could close the show. Disappointing.",
    ],
    veteran_win=[
        "Old man still got that POWER! Age ain't nothing but a number when you can crack!",
        "Experience and KNOCKOUT POWER! That's the combo!",
    ],
    veteran_loss=[
        "Tough to see. But father time doesn't care about your highlight reel.",
        "The chin goes first. It always does. Sad to watch.",
    ],
    prospect_win=[
        "Young gun with DYNAMITE in his hands! We got a future star!",
        "That's a prospect who FINISHES! Finally, someone who gets it!",
    ],
    title_fight=[
        "Title fight KNOCKOUT! That's how you make a statement!",
        "Championship violence! This is what the belt is for!",
    ],
    streak=[
        "Another knockout! This guy is appointment viewing!",
        "The streak continues with VIOLENCE! Book him again!",
    ],
    generic=[
        "It is what it is. Needed more violence.",
        "Another fight in the books. Moving on.",
    ],
)

MARCO = Commentator(
    handle="@MatSideWithMarco",
    name="Marco",
    bias=CommentatorBias.PRO_GRAPPLING,
    one_liner="Calm jiu-jitsu snob.",
    preferred_topics=[
        FightSignificance.SUBMISSION,
        FightSignificance.TITLE_FIGHT,
    ],
    
    ko_win=[
        "Knockout. Congrats on the lottery ticket. That's not a skill, that's a dice roll.",
        "He got the knockout. Let's see him do that against someone who can grapple.",
        "Standing knockout against another striker. Wake me when he fights a real threat.",
        "Lucky punch. Ground game would've been the safer path to victory.",
    ],
    sub_win=[
        "Beautiful. THIS is martial arts.",
        "Textbook submission. That setup was gorgeous.",
        "The ground game prevails. As it should.",
        "Exquisite technique. He made it look effortless.",
        "That transition to the finish was poetry. Pure jiu-jitsu.",
        "Back take, hooks in, submission. Fundamentals win fights.",
        "Finally, a real fighter showing real technique.",
        "That's high-level grappling on display. Masterful.",
    ],
    decision_win=[
        "Controlled the fight with superior grappling. Smart fighter.",
        "Ground control won that fight. The judges saw what mattered.",
        "Position before submission. He understood the assignment.",
    ],
    upset_win=[
        "The better grappler won. 'Upset' is what casuals call it.",
        "Superior technique beats hype. Every time.",
    ],
    dominant_win=[
        "Complete grappling clinic. That's mastery.",
        "He made a professional fighter look like a white belt.",
    ],
    close_fight=[
        "Close because he abandoned the ground game. Should've been easy.",
        "If he'd committed to the takedowns, this wouldn't have been close.",
    ],
    veteran_win=[
        "Experience on the mat matters. He's seen every position.",
        "Veteran savvy. Knew exactly when to engage.",
    ],
    veteran_loss=[
        "The body slows down. Unfortunately, technique can't overcome everything.",
        "Tough to see. His ground game is still there, body just couldn't keep up.",
    ],
    prospect_win=[
        "Young talent with real fundamentals. Rare these days.",
        "A prospect who actually trains jiu-jitsu? Refreshing.",
    ],
    title_fight=[
        "Championship grappling. That's how you cement a legacy.",
        "Submitted him for the title. That's a real champion.",
    ],
    streak=[
        "Another submission. The ground game doesn't lie.",
        "Consistent excellence on the mat. That's a real martial artist.",
    ],
    generic=[
        "Adequate performance. Could've been more technical.",
        "He won. Let's see him against someone with a ground game.",
    ],
)

TAKEDOWN_TED = Commentator(
    handle="@TakedownTedShow",
    name="Takedown Ted",
    bias=CommentatorBias.PRO_WRESTLING,
    one_liner="Blunt, told-you-so energy.",
    preferred_topics=[
        FightSignificance.TITLE_FIGHT,
        FightSignificance.MAIN_EVENT,
    ],
    
    ko_win=[
        "Got the knockout. Good for him. Now try that against a wrestler.",
        "Flashy finish. Would've been safer to take him down and control.",
        "KO'd a non-wrestler. Color me shocked.",
        "Lucky he didn't get taken down. That gameplan won't work twice.",
    ],
    sub_win=[
        "Wrestling got him there. The submission was just cleanup.",
        "Takedown, control, finish. Wrestling wins fights.",
        "Ground and pound threat opened up the submission. Blueprint stuff.",
    ],
    decision_win=[
        "Controlled where the fight took place. That's wrestling.",
        "Takedowns, top control, easy rounds. Simple game.",
        "Wrestle, control, win. It's not complicated.",
        "Cage wrestling masterclass. That's how you get Ws.",
    ],
    upset_win=[
        "Upset? He wrestled. The other guy couldn't stop it. Math.",
        "Wrestled his way to a win nobody expected. Classic.",
    ],
    dominant_win=[
        "Ragdolled him for three rounds. Wrestling is king.",
        "7 takedowns, 12 minutes of control. That's dominance.",
    ],
    close_fight=[
        "Close because he stopped wrestling in the third. Bad decision.",
        "Should've been easy if he'd stuck to the gameplan. Take. Him. Down.",
    ],
    veteran_win=[
        "Experience matters when you've been wrestling your whole life.",
        "Old wrestler beats young athlete. Technique over hype.",
    ],
    veteran_loss=[
        "Couldn't get the takedowns anymore. Wrestling bases erode with age.",
        "Legs went. Can't shoot without legs. Simple as that.",
    ],
    prospect_win=[
        "Young wrestler with a future. Finally, a prospect with fundamentals.",
        "Kid can wrestle. That means he can win. Simple.",
    ],
    title_fight=[
        "Wrestled his way to a championship. That's the blueprint.",
        "Champion-level wrestling. Can't beat what you can't stop.",
    ],
    streak=[
        "Another win built on wrestling. Sustainable success.",
        "Wrestling wins again. Shocking absolutely nobody.",
    ],
    generic=[
        "Wrestling wins fights. Always has. Always will.",
        "Everyone's a killer until someone shoots a double.",
    ],
)

CASS = Commentator(
    handle="@CageStoryWithCass",
    name="Cass",
    bias=CommentatorBias.LOVES_UNDERDOGS,
    one_liner="Emotional, narrative-first.",
    preferred_topics=[
        FightSignificance.UPSET,
        FightSignificance.VETERAN_WIN,
        FightSignificance.PROSPECT_BREAKOUT,
        FightSignificance.DEBUT_FINISH,
        FightSignificance.STREAK,
    ],
    
    ko_win=[
        "WHAT A MOMENT! This is why we love this sport!",
        "The heart, the determination, the FINISH! Incredible!",
        "That knockout will be remembered FOREVER!",
    ],
    sub_win=[
        "What a finish! The emotion in that moment!",
        "Submitted him and then broke down in tears. This sport, man.",
        "That submission was years in the making. Beautiful.",
    ],
    decision_win=[
        "Three hard rounds but he EARNED that win!",
        "The journey to get here... and now this. What a story.",
    ],
    upset_win=[
        "NOBODY GAVE THEM A CHANCE! I'm not crying, you're crying!",
        "This is the greatest upset I've ever seen! THE STORY!",
        "Counted out by EVERYONE! And now look! LOOK!",
        "Two years ago he was released. Tonight? WINNER! This sport, man!",
        "Against all odds! AGAINST ALL ODDS!",
        "The rankings said no. His heart said YES!",
    ],
    dominant_win=[
        "Complete performance, but the story of how he got here? Even better.",
        "Dominant, yes. But remember the struggles that built this fighter.",
    ],
    close_fight=[
        "Heart from BOTH fighters! This is what competition is about!",
        "Neither would quit! Both warriors! What a battle!",
        "That fight told a story. Drama in every round.",
    ],
    veteran_win=[
        "They said he was done. DONE! And he just proved everyone WRONG!",
        "The old lion still has it! What a story!",
        "Experience, heart, and a POINT TO PROVE! Legend!",
    ],
    veteran_loss=[
        "End of an era. But what a career. What a journey.",
        "He gave everything. Sometimes the story doesn't have a happy ending.",
        "Passing of the torch. Tough to watch, but beautiful in its own way.",
    ],
    prospect_win=[
        "A STAR IS BORN! Remember this moment! Remember where you were!",
        "The future just announced itself! What a debut!",
        "This kid is going to be SPECIAL! Mark my words!",
    ],
    title_fight=[
        "CHAMPION OF THE WORLD! Dreams really do come true!",
        "From nothing to EVERYTHING! This is the greatest story in sports!",
        "Title fight victory! The culmination of EVERYTHING!",
    ],
    streak=[
        "The streak continues! This is a story being written in real time!",
        "Another chapter in an incredible journey! Can't stop, won't stop!",
    ],
    generic=[
        "Every fight tells a story. This one was...",
        "There's always a narrative. You just have to find it.",
    ],
)

VINCE_VECCHIO = Commentator(
    handle="@TheVinceVecchioShow",
    name="Vince Vecchio",
    bias=CommentatorBias.PRO_VETERAN,
    one_liner="Grumpy, respects experience.",
    preferred_topics=[
        FightSignificance.VETERAN_WIN,
        FightSignificance.TITLE_FIGHT,
    ],
    
    ko_win=[
        "That's experience. Knew exactly when to pull the trigger.",
        "Veteran instincts. You can't teach that timing.",
        "Been there before. Stayed calm, found the opening, finished.",
    ],
    sub_win=[
        "Felt the submission coming from a mile away. Veteran awareness.",
        "That's a setup he's hit a hundred times. Experience matters.",
    ],
    decision_win=[
        "Smart fight. Didn't take unnecessary risks. That's how you have a long career.",
        "Knew what he needed to do to win. No more, no less. Professional.",
    ],
    upset_win=[
        "Upset? He's been fighting killers for a decade. The 'favorite' has 6 fights.",
        "Experience beats hype. Tale as old as time.",
    ],
    dominant_win=[
        "Masterclass from a guy who's seen everything.",
        "That's 50 fights of experience on display. Dominant.",
    ],
    close_fight=[
        "Close fight, but the veteran made fewer mistakes. That's the difference.",
        "Experience showed in the championship rounds.",
    ],
    veteran_win=[
        "Old man school'd the young gun. You LOVE to see it.",
        "He's 'washed' huh? Tell that to his opponent's face.",
        "37 years old and still teaching lessons. Respect the craft.",
        "Experience is the best teacher. And he just gave a masterclass.",
        "You can't simulate 50 fights. That knowledge won tonight.",
    ],
    veteran_loss=[
        "Father Time is undefeated. But what a career.",
        "Tough to see. But he went out like a warrior.",
        "The body quits before the mind does. Happens to everyone.",
        "Time catches up. Doesn't diminish what he accomplished.",
    ],
    prospect_win=[
        "He won. Let's see him do it against someone with a Wikipedia page.",
        "Beat a prospect. Congrats. Now fight someone who's been tested.",
        "4-0 against nobodies. Call me when the resume means something.",
    ],
    title_fight=[
        "Championship experience matters. He's been here before.",
        "Title fights are different. Veterans understand that.",
    ],
    streak=[
        "Building a resume. That's how you earn respect in this game.",
        "Streak is nice. Let's see him do it against someone who's been around.",
    ],
    generic=[
        "Let's see the resume before we crown anyone.",
        "Experience matters. Always has. Always will.",
    ],
)

RICKY_RAVENS = Commentator(
    handle="@TheRickyRavensShow",
    name="Ricky Ravens",
    bias=CommentatorBias.CONTRARIAN,
    one_liner="Always against the consensus.",
    preferred_topics=[
        FightSignificance.UPSET,
        FightSignificance.TITLE_FIGHT,
        FightSignificance.MAIN_EVENT,
    ],
    
    ko_win=[
        "I've been saying he had that power. Nobody listened.",
        "Knockout everyone's shocked by. Except me. I called it.",
        "NOW everyone sees it. I've been saying this for months.",
    ],
    sub_win=[
        "Submitted him like I predicted. But sure, keep doubting me.",
        "Called the submission. Check the receipts.",
    ],
    decision_win=[
        "Boring decision everyone's praising? Overrated performance.",
        "He won but let's not pretend that was impressive.",
        "Close fight they're calling dominant? Watch it again.",
    ],
    upset_win=[
        "UPSET? I had him winning! It's only an upset if you weren't paying attention!",
        "Been telling everyone the favorite was overrated. Now you see it.",
        "Not an upset. The betting line was wrong. I was right.",
        "Everyone picked the chalk. I picked the winner. As usual.",
    ],
    dominant_win=[
        "Dominant against a guy I've been saying is overrated. Means nothing.",
        "Beat up a hype job. Let's see him fight someone real.",
    ],
    close_fight=[
        "Close fight? Nah, I had the other guy winning clearly.",
        "Robbery. I've been saying these judges are terrible.",
    ],
    veteran_win=[
        "Everyone wrote him off. I didn't. Check my timeline.",
        "Called the veteran upset. Nobody wanted to hear it.",
    ],
    veteran_loss=[
        "I've been saying he's washed. Finally everyone agrees.",
        "Predictable. I called this decline months ago.",
    ],
    prospect_win=[
        "The prospect everyone's hyping? I'm off the bandwagon already.",
        "Won against a nobody. Let's pump the brakes.",
        "Beating cans doesn't make you a star. I'll believe it when I see it.",
    ],
    title_fight=[
        "New champion everyone's celebrating? He'll lose the belt in two fights. Mark it.",
        "Title win against a paper champion. Doesn't count.",
    ],
    streak=[
        "Streak against who exactly? Check the opposition.",
        "Everyone's hyping the streak. I'm not buying it.",
    ],
    generic=[
        "Nobody wants to hear this, but...",
        "I'll be here when everyone realizes I was right.",
        "The hype train is about to crash. Just watch.",
    ],
)

FELIX = Commentator(
    handle="@FightMathWithFelix",
    name="Felix",
    bias=CommentatorBias.STATS_ANALYTICS,
    one_liner="Percentages and milestones only.",
    preferred_topics=[
        FightSignificance.TITLE_FIGHT,
        FightSignificance.STREAK,
    ],
    
    ko_win=[
        "KO in round {round}. Career knockout rate: {ko_rate}%.",
        "First round finish. He's now {wins}-{losses} in R1 finishes.",
        "Knockout #{ko_num} of his career.",
    ],
    sub_win=[
        "Submission #{sub_num}. Ground game conversion rate: {sub_rate}%.",
        "Submission finish in round {round}. Average fight time: {avg_time}.",
        "Career submission #{sub_num}.",
    ],
    decision_win=[
        "Decision win. Lifetime decision record: {dec_record}.",
        "Goes to the scorecards. Decision rate: {dec_rate}%.",
        "Another decision victory. Now {dec_wins} career decisions.",
    ],
    upset_win=[
        "Underdog wins. Upsets happen {upset_rate}% of the time at this level.",
        "Lower-ranked fighter takes it. Form doesn't always hold.",
    ],
    dominant_win=[
        "Dominant performance. One of the most lopsided wins this year.",
        "Complete control throughout. Elite-level showing.",
    ],
    close_fight=[
        "Close fight. Could have gone either way statistically.",
        "Narrow margin of victory. Essentially a coin flip.",
    ],
    veteran_win=[
        "At {age}, he's among the older winners this year in the division.",
        "Win #{wins} of his career. Veteran presence.",
    ],
    veteran_loss=[
        "Age {age}. Win rate declines significantly past 35.",
        "Fighters at this age are {vet_record} over the past year.",
    ],
    prospect_win=[
        "Now {wins}-{losses}. On pace for title contention in {years} years.",
        "Win #{wins}. Finish rate of {finish_rate}% ranks among top prospects.",
    ],
    title_fight=[
        "Title defense #{defenses}. Enters elite company.",
        "New champion. Average reign length: {avg_reign} defenses.",
    ],
    streak=[
        "Win streak at {streak}. Historically, streaks of {streak}+ lead to title shots {title_rate}% of the time.",
        "Now {streak} straight. Momentum metrics climbing.",
    ],
    generic=[
        "Updating the database.",
        "The numbers tell the story.",
    ],
)


# ============================================================================
# COMMENTATOR REGISTRY
# ============================================================================

COMMENTATORS: Dict[str, Commentator] = {
    "sal": SAL_SANTINO,
    "marco": MARCO,
    "ted": TAKEDOWN_TED,
    "cass": CASS,
    "vince": VINCE_VECCHIO,
    "ricky": RICKY_RAVENS,
    "felix": FELIX,
}


def get_commentator(name: str) -> Optional[Commentator]:
    """Get a commentator by short name."""
    return COMMENTATORS.get(name.lower())


def get_all_commentators() -> List[Commentator]:
    """Get all commentators."""
    return list(COMMENTATORS.values())


def get_random_commentators(count: int = 3) -> List[Commentator]:
    """Get a random selection of commentators."""
    return random.sample(get_all_commentators(), min(count, len(COMMENTATORS)))


# ============================================================================
# FIGHT SIGNIFICANCE DETECTION
# ============================================================================

def determine_fight_significance(
    method: str,
    is_title_fight: bool = False,
    is_main_event: bool = False,
    was_upset: bool = False,
    winner_age: int = 28,
    winner_fights: int = 10,
    winner_streak: int = 0,
    is_debut: bool = False,
    loser_rank: Optional[int] = None,
) -> List[FightSignificance]:
    """Determine what makes this fight significant for media coverage."""
    significance = []
    
    method_upper = method.upper()
    
    # Title fight is always significant
    if is_title_fight:
        significance.append(FightSignificance.TITLE_FIGHT)
    
    # Main event
    if is_main_event:
        significance.append(FightSignificance.MAIN_EVENT)
    
    # Method-based
    if "KO" in method_upper or "TKO" in method_upper:
        significance.append(FightSignificance.KNOCKOUT)
    elif "SUB" in method_upper:
        significance.append(FightSignificance.SUBMISSION)
    
    # Upset
    if was_upset:
        significance.append(FightSignificance.UPSET)
    
    # Veteran win (35+)
    if winner_age >= 35:
        significance.append(FightSignificance.VETERAN_WIN)
    
    # Prospect breakout (young, early career, beat ranked opponent)
    if winner_age <= 26 and winner_fights <= 8 and loser_rank and loser_rank <= 10:
        significance.append(FightSignificance.PROSPECT_BREAKOUT)
    
    # Debut finish
    if is_debut and ("KO" in method_upper or "TKO" in method_upper or "SUB" in method_upper):
        significance.append(FightSignificance.DEBUT_FINISH)
    
    # Win streak
    if winner_streak >= 3:
        significance.append(FightSignificance.STREAK)
    
    # If nothing special, mark as normal
    if not significance:
        significance.append(FightSignificance.NORMAL)
    
    return significance


def should_generate_reactions(significance: List[FightSignificance]) -> bool:
    """Determine if a fight warrants social media reactions."""
    # Normal fights don't get reactions
    if significance == [FightSignificance.NORMAL]:
        return False
    return True


def get_reaction_count(significance: List[FightSignificance]) -> int:
    """Determine how many reactions to generate based on significance."""
    count = 3  # Base count
    
    if FightSignificance.TITLE_FIGHT in significance:
        count = 5
    elif FightSignificance.MAIN_EVENT in significance:
        count = 4
    elif FightSignificance.UPSET in significance:
        count = 4
    
    # Bonus for multiple significance factors
    if len(significance) >= 3:
        count = min(count + 1, 5)
    
    return count


# ============================================================================
# COMMENTATOR SELECTION
# ============================================================================

def select_commentators_for_fight(
    significance: List[FightSignificance],
    count: int = 3,
) -> List[Commentator]:
    """Select commentators most likely to react to this fight type."""
    all_comms = get_all_commentators()
    
    # Calculate weights based on preferences
    weighted = []
    for comm in all_comms:
        weight = 0.3  # Base weight
        for sig in significance:
            if sig in comm.preferred_topics:
                weight += 0.4
        weighted.append((comm, weight))
    
    # Sort by weight, then randomize within similar weights
    weighted.sort(key=lambda x: (-x[1], random.random()))
    
    # Take top weighted, but ensure some variety
    selected = []
    for comm, weight in weighted:
        if len(selected) >= count:
            break
        # Higher weight = more likely to be included
        if random.random() < weight:
            selected.append(comm)
    
    # Fill remaining slots randomly if needed
    remaining = [c for c, _ in weighted if c not in selected]
    while len(selected) < count and remaining:
        selected.append(remaining.pop(0))
    
    return selected[:count]


# ============================================================================
# COMMENTARY GENERATION
# ============================================================================

def _determine_context(
    fight_result: Dict[str, Any],
    winner_data: Optional[Dict] = None,
    loser_data: Optional[Dict] = None,
) -> List[str]:
    """Determine which phrase categories apply to this fight."""
    contexts = []
    
    method = fight_result.get("method", "").upper()
    
    # Method-based context
    if "KO" in method or "TKO" in method:
        contexts.append("ko_win")
    elif "SUB" in method:
        contexts.append("sub_win")
    elif "DEC" in method or "DECISION" in method:
        contexts.append("decision_win")
    
    # Upset detection
    if fight_result.get("was_upset", False):
        contexts.append("upset_win")
    
    # Dominant win detection
    if fight_result.get("dominant", False):
        contexts.append("dominant_win")
    round_ended = fight_result.get("round", 3)
    if round_ended == 1 and ("KO" in method or "TKO" in method or "SUB" in method):
        contexts.append("dominant_win")
    
    # Veteran context
    winner_age = winner_data.get("age", 28) if winner_data else 28
    loser_age = loser_data.get("age", 28) if loser_data else 28
    
    if winner_age >= 35:
        contexts.append("veteran_win")
    if loser_age >= 35:
        contexts.append("veteran_loss")
    
    # Prospect context
    winner_fights = winner_data.get("total_fights", 10) if winner_data else 10
    if winner_age <= 26 and winner_fights <= 8:
        contexts.append("prospect_win")
    
    # Title fight
    if fight_result.get("is_title_fight", False):
        contexts.append("title_fight")
    
    # Streak
    winner_streak = winner_data.get("win_streak", 0) if winner_data else 0
    if winner_streak >= 3:
        contexts.append("streak")
    
    # Close fight
    if fight_result.get("close_fight", False):
        contexts.append("close_fight")
    
    return contexts


def _fill_stat_placeholders(
    phrase: str,
    fight_result: Dict[str, Any],
    winner_data: Optional[Dict] = None,
) -> str:
    """Fill in statistical placeholders for Felix's commentary."""
    
    # Get actual stats where available
    wins = winner_data.get("wins", random.randint(5, 15)) if winner_data else random.randint(5, 15)
    losses = winner_data.get("losses", random.randint(1, 5)) if winner_data else random.randint(1, 5)
    age = winner_data.get("age", random.randint(26, 34)) if winner_data else random.randint(26, 34)
    streak = winner_data.get("win_streak", random.randint(2, 6)) if winner_data else random.randint(2, 6)
    
    replacements = {
        "{round}": str(fight_result.get("round", random.randint(1, 3))),
        "{ko_rate}": str(random.randint(45, 75)),
        "{ko_num}": str(random.randint(min(3, wins), wins)),
        "{sub_num}": str(random.randint(2, max(2, wins // 2))),
        "{sub_rate}": str(random.randint(30, 60)),
        "{wins}": str(wins),
        "{losses}": str(losses),
        "{dec_record}": f"{random.randint(2, 6)}-{random.randint(0, 2)}",
        "{dec_rate}": str(random.randint(25, 50)),
        "{dec_wins}": str(random.randint(3, 8)),
        "{avg_time}": f"{random.randint(8, 14)}:{random.randint(10, 59):02d}",
        "{upset_rate}": str(random.randint(20, 35)),
        "{age}": str(age),
        "{vet_record}": f"{random.randint(40, 55)}%",
        "{finish_rate}": str(random.randint(50, 85)),
        "{years}": str(random.randint(2, 4)),
        "{defenses}": str(random.randint(1, 5)),
        "{avg_reign}": str(random.randint(2, 4)),
        "{streak}": str(streak),
        "{title_rate}": str(random.randint(60, 80)),
    }
    
    for placeholder, value in replacements.items():
        phrase = phrase.replace(placeholder, value)
    
    return phrase


def generate_post_fight_take(
    commentator: Commentator,
    fight_result: Dict[str, Any],
    winner_data: Optional[Dict] = None,
    loser_data: Optional[Dict] = None,
) -> str:
    """Generate a post-fight take from a specific commentator."""
    
    contexts = _determine_context(fight_result, winner_data, loser_data)
    
    # Bias-based priority ordering
    priority_map = {
        CommentatorBias.PRO_KNOCKOUT: ["ko_win", "dominant_win", "decision_win"],
        CommentatorBias.PRO_GRAPPLING: ["sub_win", "decision_win", "ko_win"],
        CommentatorBias.PRO_WRESTLING: ["decision_win", "sub_win", "dominant_win"],
        CommentatorBias.LOVES_UNDERDOGS: ["upset_win", "veteran_win", "close_fight", "prospect_win", "streak"],
        CommentatorBias.PRO_VETERAN: ["veteran_win", "veteran_loss", "prospect_win"],
        CommentatorBias.CONTRARIAN: ["upset_win", "decision_win", "prospect_win", "streak"],
        CommentatorBias.STATS_ANALYTICS: ["streak", "title_fight", "dominant_win", "ko_win"],
    }
    
    priorities = priority_map.get(commentator.bias, [])
    
    # Find best matching context based on bias priority
    selected_context = None
    for priority in priorities:
        if priority in contexts:
            selected_context = priority
            break
    
    # Fallback to first available context or generic
    if not selected_context:
        selected_context = contexts[0] if contexts else "generic"
    
    phrase = commentator.get_phrase(selected_context)
    
    # For Felix, fill in stat placeholders
    if commentator.bias == CommentatorBias.STATS_ANALYTICS:
        phrase = _fill_stat_placeholders(phrase, fight_result, winner_data)
    
    return phrase


def generate_media_reactions(
    fight_result: Dict[str, Any],
    commentators: Optional[List[Commentator]] = None,
    winner_data: Optional[Dict] = None,
    loser_data: Optional[Dict] = None,
    num_reactions: int = 3,
) -> List[Dict[str, str]]:
    """Generate reactions from commentators."""
    
    if commentators is None:
        commentators = get_random_commentators(num_reactions)
    
    reactions = []
    
    for comm in commentators[:num_reactions]:
        take = generate_post_fight_take(comm, fight_result, winner_data, loser_data)
        reactions.append({
            "handle": comm.handle,
            "name": comm.name,
            "take": take,
            "bias": comm.bias.value,
        })
    
    return reactions


# ============================================================================
# CONVENIENCE FUNCTION FOR CLI INTEGRATION
# ============================================================================

def generate_fight_reactions(
    method: str,
    winner_name: str,
    loser_name: str,
    round_finished: int = 3,
    is_title_fight: bool = False,
    is_main_event: bool = False,
    was_upset: bool = False,
    winner_age: int = 28,
    winner_fights: int = 10,
    winner_streak: int = 0,
    winner_wins: int = 10,
    winner_losses: int = 2,
    loser_rank: Optional[int] = None,
    is_debut: bool = False,
) -> List[Dict[str, str]]:
    """
    Main entry point for generating social media reactions.
    
    Returns list of reaction dicts with 'handle' and 'take' keys,
    or empty list if fight doesn't warrant reactions.
    """
    # Determine significance
    significance = determine_fight_significance(
        method=method,
        is_title_fight=is_title_fight,
        is_main_event=is_main_event,
        was_upset=was_upset,
        winner_age=winner_age,
        winner_fights=winner_fights,
        winner_streak=winner_streak,
        is_debut=is_debut,
        loser_rank=loser_rank,
    )
    
    # Check if reactions warranted
    if not should_generate_reactions(significance):
        return []
    
    # Get reaction count and select commentators
    count = get_reaction_count(significance)
    commentators = select_commentators_for_fight(significance, count)
    
    # Build fight result dict
    fight_result = {
        "method": method,
        "winner_name": winner_name,
        "loser_name": loser_name,
        "round": round_finished,
        "is_title_fight": is_title_fight,
        "was_upset": was_upset,
    }
    
    # Build winner data dict
    winner_data = {
        "age": winner_age,
        "total_fights": winner_fights,
        "win_streak": winner_streak,
        "wins": winner_wins,
        "losses": winner_losses,
    }
    
    return generate_media_reactions(
        fight_result=fight_result,
        commentators=commentators,
        winner_data=winner_data,
        num_reactions=count,
    )
