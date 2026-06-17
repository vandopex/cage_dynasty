"""
Corner advice content library + generation. Ship K1.

Coach speaks between rounds based on what actually happened.
Content scoped to engine vocabulary only (RoundStats fields +
fighter state). No invented mechanics.

Specialty buckets:
- striking / boxing / kickboxing / muay thai → "Striking Coach"
- wrestling / grappling / bjj / submissions → "Grappling Coach"
- conditioning / strength / cardio / s&c    → "S&C Coach"
- mma / cornering / strategy                → "MMA Head Coach" (generalist)

Rating tiers (3): low <=65, mid 66-80, high >80.

Generation flow:
1. Map coach specialty → archetype bucket
2. Determine rating tier
3. Detect situation tags from RoundStats (won/lost/close round, hurt,
   gassing, knockdowns, score gap)
4. Pick template from (archetype, situation, tier) library, with
   secondary-domain fallback at high rating
5. Substitute {fighter_name} / {opponent_name} placeholders
6. Return lines + next-round bonus info
"""

import random
from typing import Dict, List, Optional, Any, Tuple


# Constants duplicated here for module-level isolation. Keep in sync
# with game_bridge.py constants of the same name.
CORNER_BONUS_BASE              = 1.0
CORNER_BONUS_PER_RATING_POINT  = 0.04
CORNER_SECONDARY_DOMAIN_MIN    = 80
CORNER_GENERALIST_DEPTH_MIN    = 75


SPECIALTY_TO_ARCHETYPE = {
    "striking":     "striking",
    "boxing":       "striking",
    "kickboxing":   "striking",
    "muay thai":    "striking",
    "muay_thai":    "striking",
    "wrestling":    "grappling",
    "grappling":    "grappling",
    "bjj":          "grappling",
    "submissions":  "grappling",
    "conditioning": "sc",
    "strength":     "sc",
    "cardio":       "sc",
    "s&c":          "sc",
    "s and c":      "sc",
    "mma":          "mma_head",
    "head coach":   "mma_head",
    "cornering":    "mma_head",
    "strategy":     "mma_head",
}


def _archetype_from_specialty(specialty: str) -> str:
    """Bucket the coach's specialty into one of 4 archetypes."""
    return SPECIALTY_TO_ARCHETYPE.get((specialty or "").lower(), "mma_head")


def _rating_tier(rating: int) -> str:
    """Map rating to tier label."""
    if rating <= 65:
        return "low"
    if rating <= 80:
        return "mid"
    return "high"


# ── Situation detection ─────────────────────────────────────────
# Stats dicts come from RoundStats.to_dict() — keys:
#   sig_strikes_att, sig_strikes_landed, head_strikes, body_strikes,
#   leg_strikes, td_att, td_landed, sub_att, control_time, damage,
#   knockdowns, reversals

def _round_score(stats: Dict[str, Any]) -> float:
    """Lightweight per-round score proxy. Higher = won the round."""
    if not stats:
        return 0.0
    return (
        stats.get("sig_strikes_landed", 0) * 1.0
        + stats.get("knockdowns", 0) * 10.0
        + stats.get("td_landed", 0) * 2.0
        + stats.get("control_time", 0.0) / 30.0
        + stats.get("sub_att", 0) * 1.5
        + stats.get("damage", 0.0) * 0.2
    )


def _detect_situations(
    player_health: float,
    player_stamina: float,
    opponent_health: float,
    p_stats: Dict[str, Any],
    o_stats: Dict[str, Any],
    cumulative_score_gap: float,
    round_num: int,
    total_rounds: int,
) -> List[str]:
    """
    Return situation tags that apply to this between-round moment.
    Tags use ONLY engine-real vocabulary.
    """
    tags: List[str] = []

    p_score = _round_score(p_stats)
    o_score = _round_score(o_stats)
    round_diff = p_score - o_score

    # KD events take precedence
    if p_stats.get("knockdowns", 0) > 0:
        tags.append("scored_knockdown")
    if o_stats.get("knockdowns", 0) > 0:
        tags.append("fighter_dropped")

    # Health / stamina
    if player_health < 50:
        tags.append("fighter_hurt")
    if player_stamina < 40:
        tags.append("fighter_gassing")
    if opponent_health < 50:
        tags.append("opponent_hurt")

    # Round outcome
    if round_diff > 8:
        tags.append("won_round_clearly")
    elif round_diff < -8:
        tags.append("lost_round_clearly")
    else:
        tags.append("close_round")

    # Striking battle
    p_strikes = p_stats.get("sig_strikes_landed", 0)
    o_strikes = o_stats.get("sig_strikes_landed", 0)
    if p_strikes >= o_strikes + 6:
        tags.append("outstriking")
    elif o_strikes >= p_strikes + 6:
        tags.append("being_outstruck")

    # Takedown battle
    p_td_att = p_stats.get("td_att", 0)
    p_td_land = p_stats.get("td_landed", 0)
    o_td_att = o_stats.get("td_att", 0)
    o_td_land = o_stats.get("td_landed", 0)
    if p_td_att >= 2 and p_td_land > o_td_land:
        tags.append("winning_takedown_battle")
    elif o_td_att >= 2 and o_td_land > p_td_land:
        tags.append("losing_takedown_battle")

    # Control time (ground or clinch)
    if p_stats.get("control_time", 0.0) >= 60.0:
        tags.append("controlling_position")

    # Score gap going into a final round (after this round is the last)
    if round_num == total_rounds - 1:
        if cumulative_score_gap < -10:
            tags.append("need_finish")
        elif cumulative_score_gap > 10:
            tags.append("coast_on_cards")

    return tags


# ============================================================
# CONTENT LIBRARY — ~100 templates across 4 archetypes
# ============================================================
# Structure: {situation: {tier: [templates]}}
# All templates use {fighter_name} and {opponent_name} only.
# Coach picks ONE template at random from the matched bucket.
# Content references only engine-real outcomes; coaching language
# (slip, sprawl, change levels, walk him down) is voice, not
# engine assertions — Lock 15 honored.

STRIKING_COACH = {
    "won_round_clearly": {
        "low":  [
            "{fighter_name}, that's your round. Keep doing what you're doing.",
            "Good work. Stay on him.",
        ],
        "mid":  [
            "Round's yours, {fighter_name}. He doesn't like that body work — keep going downstairs.",
            "You're landing clean. Don't get fancy, stay disciplined behind the jab.",
        ],
        "high": [
            "Round's yours, {fighter_name}. He's covering high — every clean cross, dig the left hook to the body. He won't last another round of that.",
            "You're up. He's reaching for the counter every time you step in. Change levels next combo — make him hesitate, then come back upstairs.",
        ],
    },
    "lost_round_clearly": {
        "low":  [
            "{fighter_name}, you gave that one away. Get back to basics.",
            "Tighten up. We need this round.",
        ],
        "mid":  [
            "You're getting picked apart, {fighter_name}. Close the distance with combinations, don't square up.",
            "Reset. He's beating you to the punch. Cut the angle, don't trade in straight lines.",
        ],
        "high": [
            "He's reading your jab, {fighter_name}. Triple it next time, or change levels off the second one. Make him bite on something that isn't coming.",
            "You're losing exchanges standing in front of him. Move off the centerline, throw the cross, then circle out. Don't stay there.",
        ],
    },
    "close_round": {
        "low":  [
            "{fighter_name}, that one's a toss-up. Make the next round yours.",
            "Close round. We need to take the next one clean.",
        ],
        "mid":  [
            "Coin flip round, {fighter_name}. Open up earlier next round — first clean combo sets the tone.",
            "Even round. He's trading with you — break that with movement and lead-foot kicks.",
        ],
        "high": [
            "That one could go either way, {fighter_name}. The judges remember the last 30 seconds — finish strong, even if it's just volume on the jab to close.",
            "He's matching your pace, not your output. Throw two-piece combos and step out — make him chase the exchange, not match it.",
        ],
    },
    "fighter_hurt": {
        "low":  [
            "{fighter_name}, hands up. Survive this round.",
            "Cover up. We need the next round.",
        ],
        "mid":  [
            "You're hurt, {fighter_name}. Clinch up when he comes in, ride out the round. Don't engage in the pocket.",
            "Hands up high, chin tucked. He smells blood — don't give him the angle on the right hand.",
        ],
        "high": [
            "He smells the kill, {fighter_name} — he's loading up. Slip the first shot, tie him up, eat the clock. Your head clears in 60 seconds.",
            "You're hurt and he knows it. He'll swing wild for the finish — that's your shot. First overcommit, slip, counter with the cross. He won't expect it.",
        ],
    },
    "fighter_gassing": {
        "low":  [
            "{fighter_name}, breathe. Pace yourself.",
            "Slow down. Pick your shots.",
        ],
        "mid":  [
            "You're gassing, {fighter_name}. Stop throwing in volume — one big shot per exchange and reset.",
            "Tired? Use the cage. Get him backing up so YOU set the pace, not him.",
        ],
        "high": [
            "You're gassed and he's not — change the geometry. Push him to the cage, lean on him, steal 30 seconds. Then break with a knee and reset center.",
            "Cardio's dropping. Switch to counter mode — let him come, slip, two-piece, circle out. Stop chasing.",
        ],
    },
    "fighter_dropped": {
        "low":  [
            "{fighter_name}, shake it off. Stay long, stay safe.",
            "He cracked you. Hands up, head off the centerline.",
        ],
        "mid":  [
            "You got dropped, {fighter_name}. He'll come hunting that same shot — see it coming, slip outside, counter with the lead hook.",
            "He's got your timing on the right hand. Change your level once before you throw — break that read.",
        ],
        "high": [
            "He found that shot once, he'll go back to the well. Fake the entry, draw the counter, then YOU counter HIS counter. Bait him.",
            "He's confident now. Use it. He'll commit early — slip, pivot off, come back with the cross. Confidence is the opening.",
        ],
    },
    "scored_knockdown": {
        "low":  [
            "{fighter_name}, you cracked him! Finish it!",
            "He's hurt! Don't let him recover!",
        ],
        "mid":  [
            "You hurt him, {fighter_name} — but don't dive in wild. Combinations, then back out. He's dangerous desperate.",
            "He felt that. Same setup again — he's still seeing the right hand. Go to the body once, then back upstairs.",
        ],
        "high": [
            "You wobbled him. Careful — wounded fighters throw bombs. Walk him down with the jab, force him to commit first, then unload.",
            "His legs aren't right. Don't go headhunting — chop the lead leg with kicks, take the base out, then come up with the cross when he's flat-footed.",
        ],
    },
    "opponent_hurt": {
        "low":  [
            "{fighter_name}, he's fading. Stay on him.",
            "He's hurt. Keep the pressure on.",
        ],
        "mid":  [
            "He's banged up, {fighter_name}. Don't let him reset — keep him moving backward.",
            "He's hurt. Same combo that landed — go to it again. He's seeing stars, not punches.",
        ],
        "high": [
            "He's hurt but trying to hide it. Watch the breathing — every clinch he calls for, deny it. Stay in striking range and make him work.",
            "He's diminished. The body shots are landing harder than they should. Keep digging — one more clean to the liver and he folds.",
        ],
    },
    "outstriking": {
        "low":  [
            "{fighter_name}, you're landing. Keep it up.",
            "Volume is the difference. Don't stop.",
        ],
        "mid":  [
            "You're out-landing him, {fighter_name} — don't get greedy. Pick your shots and don't trade.",
            "Striking numbers are yours. He'll start looking for the takedown — be ready to sprawl.",
        ],
        "high": [
            "You're winning the striking numbers and he knows it. He'll change levels next round — when his weight drops, that's your knee. Don't get caught celebrating.",
            "Striking's yours, but he's setting traps. He's eating the jab to bait the cross — throw the jab clean and circle out, don't follow it with the right yet.",
        ],
    },
    "being_outstruck": {
        "low":  [
            "{fighter_name}, you're getting hit too much. Move.",
            "Defense! Hands up!",
        ],
        "mid":  [
            "He's landing cleaner, {fighter_name}. Stop trading in the pocket — out-angle, in-and-out.",
            "You're square to him. Turn the lead foot, slip the jab, come back with the hook.",
        ],
        "high": [
            "He's beating you to the punch because you're telegraphing — weight's on the front foot before you throw. Sit back, let him commit first, counter off the slip.",
            "Every shot he lands, you're reaching to throw back. That's how he sets the next one. Take the hit, RESET, then throw. Don't trade in anger.",
        ],
    },
    "need_finish": {
        "low":  [
            "{fighter_name}, you need this round! Go!",
            "Finish or lose. Empty the tank.",
        ],
        "mid":  [
            "You need the finish, {fighter_name}. Forget points. Pressure him to the cage and unload.",
            "We're down on the cards. Open up — leave it all out there.",
        ],
        "high": [
            "No points left, {fighter_name}. Walk him down, close the cage, force him to engage. He'll grab the clinch to kill time — knee the body when he ties up.",
            "We need the stoppage. He's been backing up all fight — that's predictable. Cut him off, force him to plant his feet, then unload.",
        ],
    },
    "coast_on_cards": {
        "low":  [
            "{fighter_name}, you've got this. Don't get reckless.",
            "Smart round. Don't give it away.",
        ],
        "mid":  [
            "You're up on the cards, {fighter_name}. He needs the finish — be smart, don't trade.",
            "Coast this one. Move, jab, circle. Don't get caught swinging for the fences.",
        ],
        "high": [
            "You're up. He's desperate — he'll headhunt and he'll shoot. Stay long, jab to maintain distance, sprawl on anything below the waist.",
            "He has to chase. That's your fight — counter shots all day. Don't engage offensively unless it's safe. Let him make the mistake.",
        ],
    },
}


GRAPPLING_COACH = {
    "won_round_clearly": {
        "low":  [
            "{fighter_name}, you took that round. Stay technical.",
            "Good work. Keep him guessing.",
        ],
        "mid":  [
            "You're winning the grappling exchanges, {fighter_name}. He doesn't want to be on the mat — every time he stands, level change again.",
            "Control time's yours. Don't let him scramble out. Heavy hips, work the ground game.",
        ],
        "high": [
            "Round's yours on the mat. He's defending the same way every time — posting on the elbow. That's your kimura grip on the trapped arm. Take it.",
            "You're up. He's stuffing the single — switch to the double off the cage next time, cut the angle, drive through.",
        ],
    },
    "lost_round_clearly": {
        "low":  [
            "{fighter_name}, that one got away. Reset.",
            "He's keeping you off him. Get inside.",
        ],
        "mid":  [
            "He's keeping it standing, {fighter_name}. You need a better setup — strike to set up the shot, don't telegraph the level change.",
            "Sprawl-and-brawl is killing you. Chain the takedown — single to double to body lock.",
        ],
        "high": [
            "Every shot you took was off your back foot, {fighter_name}. Hand-fight first, get him reacting to your grips, THEN drop the level. He's reading the entry.",
            "You're committing to the takedown too early. Touch him with the jab first, get the head down, then shoot. He's never not seeing it coming.",
        ],
    },
    "close_round": {
        "low":  [
            "{fighter_name}, close one. Tighten up.",
            "Even round. Find the takedown next.",
        ],
        "mid":  [
            "Coin flip, {fighter_name}. Get one clean takedown next round — even 60 seconds of top control swings the judges.",
            "Close one. Push the clinch, force him to defend grips. He doesn't want to grapple — make him.",
        ],
        "high": [
            "That round's a toss-up, but you owned the clinch exchanges. Build on it — pummel for underhooks, drag him down off the cage.",
            "Even round. He's defending shots well but tiring on the cage breaks. Stay in his face, pummel constantly. He'll concede the body lock by minute two.",
        ],
    },
    "fighter_hurt": {
        "low":  [
            "{fighter_name}, hands up, get the clinch. Survive.",
            "Cover up. Get the takedown if you can.",
        ],
        "mid":  [
            "You're hurt, {fighter_name}. Clinch up, drag him down — fight goes to the mat where you're safe.",
            "Tie him up. He can't strike from there. Drop the level, take him down, eat the clock.",
        ],
        "high": [
            "You're hurt. Don't trade — first opportunity, change levels and shoot the double. Even a failed shot ties him up and resets the clock.",
            "Hurt fighter on the feet is a target. Get him to the mat — even half-guard from your back beats standing right now. Cover and pull guard if you have to.",
        ],
    },
    "fighter_gassing": {
        "low":  [
            "{fighter_name}, breathe. Use the clinch.",
            "Slow down. Get a tie-up.",
        ],
        "mid":  [
            "You're gassing, {fighter_name}. Get the clinch, lean on him, recover. Don't try to wrestle from out wide.",
            "Tired? Drag him down and ride out the round. Top control buys you breath.",
        ],
        "high": [
            "Cardio's slipping. Get the clinch on the cage — lean your weight on him, breathe, force HIM to do the work. He'll quit before you do.",
            "You're gassed. Don't waste shots from distance — get the body lock, drag him down, ground-and-pound from top. Conserve, then explode.",
        ],
    },
    "fighter_dropped": {
        "low":  [
            "{fighter_name}, shake it off. Tie him up.",
            "He cracked you. Get the clinch, slow it down.",
        ],
        "mid":  [
            "You got dropped, {fighter_name}. He'll come hunting — shoot a double when he plants his feet. He won't see it coming.",
            "He's looking for the followup. Change levels — drop and grab anything. Get the fight off the feet.",
        ],
        "high": [
            "He hurt you on the feet. Don't give him a second one — fake the entry, draw the cross, shoot under it. Get him to the mat, get on top, kill the round.",
            "He's confident now and confidence overextends. Bait the kill shot — short entry, head down, double leg. He'll be off-balance and over-committed.",
        ],
    },
    "scored_knockdown": {
        "low":  [
            "{fighter_name}, you cracked him! Go!",
            "He's hurt! Take him down!",
        ],
        "mid":  [
            "You hurt him, {fighter_name}. Get on top before he recovers — fight's over once you pass guard.",
            "He felt that. Don't dive in wild — set up the shot off another combo, drag him down on top.",
        ],
        "high": [
            "You wobbled him. Now close the deal on the mat — short entry, get the body lock, drop him. Mount, ground-and-pound, finish.",
            "His legs are gone. Don't headhunt — chop the lead leg with the low kick, take his base out, then shoot. He's a sitting duck flat-footed.",
        ],
    },
    "opponent_hurt": {
        "low":  [
            "{fighter_name}, he's fading. Stay on him.",
            "He's hurt. Get the takedown.",
        ],
        "mid":  [
            "He's banged up, {fighter_name}. Drag him down — gas tanks die faster on bottom.",
            "He's hurt. Get on top — every second of control drains him further.",
        ],
        "high": [
            "He's hurt and trying to recover in the clinch. Don't let him — drag him down, pass to mount, work the ground-and-pound. Finish or strangle.",
            "He's diminished. He'll grab anything to slow it down — when he reaches, take the limb. Kimura, armbar — whatever he gives you.",
        ],
    },
    "winning_takedown_battle": {
        "low":  [
            "{fighter_name}, he can't stop you. Keep at it.",
            "Takedowns are landing. Stay on him.",
        ],
        "mid":  [
            "Your shots are getting through, {fighter_name}. He's gassing trying to defend — chain takedowns now, don't give him space.",
            "You own the takedown game. Get him down, work for the back. He's defending wrong.",
        ],
        "high": [
            "He's reactive on the sprawl, not proactive — that's why your singles land. Switch to the double next time, he'll over-rotate and you'll dump him.",
            "Every takedown is costing him gas. Don't celebrate from top — pass guard immediately. Side control to mount. Keep the pressure constant.",
        ],
    },
    "losing_takedown_battle": {
        "low":  [
            "{fighter_name}, shots aren't landing. Set them up.",
            "He's sprawling well. Mix it up.",
        ],
        "mid":  [
            "Your level changes are telegraphed, {fighter_name}. Throw the jab first, get the head moving, THEN shoot.",
            "He's reading the takedown. Try the body lock off the clinch — drag him sideways, don't fight him head-on.",
        ],
        "high": [
            "He's stopping the shot at the hips, {fighter_name}. Change angle on entry — drop step instead of straight in, attack a single from his weak leg.",
            "You're shooting from too far out. Get into the clinch first, hand-fight, drop the level off the underhook — he can't sprawl from a tie-up.",
        ],
    },
    "controlling_position": {
        "low":  [
            "{fighter_name}, you've got top control. Stay heavy.",
            "Heavy hips. Don't let him scramble out.",
        ],
        "mid":  [
            "You're controlling, {fighter_name}. Pass to side control — half-guard's eating clock but mount wins it.",
            "Stay heavy. Work small ground-and-pound to make him expose. Don't get fancy with submissions yet.",
        ],
        "high": [
            "Control's yours. He's defending his guard well — climb to mount with the high knee on the bicep. Trap the arm, mount, then arm-triangle.",
            "You're stalling on top — that won't win it. Posture up, throw the ground-and-pound, force him to open guard to scramble. THEN take the back.",
        ],
    },
    "outstriking": {
        "low":  [
            "{fighter_name}, you're landing on the feet too. Use it.",
            "Striking's working. Set up the takedown.",
        ],
        "mid":  [
            "You're winning the striking, {fighter_name} — disguise the shot. He'll keep his hands high expecting punches. Drop the level, take him down.",
            "Striking's yours. Now mix it — strike, strike, shoot. He won't see the takedown coming.",
        ],
        "high": [
            "You're out-landing him. Now bait it — throw the cross, deliberately leave the hip exposed, when he counters with the kick you catch and dump him.",
            "Striking's working but the takedown's where you win. Punch combo to set the level change — he's covering high, perfect time to drop and double-leg.",
        ],
    },
    "being_outstruck": {
        "low":  [
            "{fighter_name}, you're getting hit. Get inside.",
            "Tie him up. Take it to the mat.",
        ],
        "mid":  [
            "He's picking you apart on the feet, {fighter_name}. Close the distance and clinch — fight's not here, it's on the mat.",
            "Stop trading on the feet. Drop the level on his next combo — he'll over-commit and you'll have his legs.",
        ],
        "high": [
            "Striking is HIS game right now. Don't fight on his terms — shoot off his combos, change levels under his cross, get this fight to the mat.",
            "Every exchange on the feet is points for him. Stop engaging at striking range — close the gap with the clinch, drag him down, kill the striking game.",
        ],
    },
    "need_finish": {
        "low":  [
            "{fighter_name}, we need this round! Take him down!",
            "Finish or lose. Get on top.",
        ],
        "mid":  [
            "You need the finish, {fighter_name}. Get him down, isolate an arm. Submission is your finish.",
            "We're down on the cards. Drop the level on the first opening, drag him down, work for the back.",
        ],
        "high": [
            "No points left. Get the takedown, pass to mount, attack the choke. He's been defending sub attempts all fight — he's tired. Now he gives one up.",
            "We need the stoppage and you're a finisher off the back. Get the takedown, take his back when he turtles, lock the body triangle. Choke or strangle, end it.",
        ],
    },
    "coast_on_cards": {
        "low":  [
            "{fighter_name}, you've got it. Stay safe.",
            "Smart round. Don't get fancy.",
        ],
        "mid":  [
            "You're up, {fighter_name}. Get one more takedown, ride top position, eat the clock.",
            "Coast this one. Takedown, control, ground-and-pound to stay busy. Don't give the judges a reason to swing.",
        ],
        "high": [
            "You're up. He needs the finish — he'll shoot wild. Sprawl, take the back when he ducks under, ride out the round in top control.",
            "Cards are yours. Don't get reckless going for a submission — control the position, work GnP enough to keep the ref happy, stay heavy.",
        ],
    },
}


SC_COACH = {
    "won_round_clearly": {
        "low":  [
            "{fighter_name}, that's your round. Pace is yours.",
            "Good work. Stay in your tank.",
        ],
        "mid":  [
            "Round's yours, {fighter_name}. Your conditioning's showing — he's slowing already. Keep the pressure.",
            "You took it. He's breathing through his mouth — the engine work is paying off.",
        ],
        "high": [
            "You took that one because you're fresher. His shoulders are dropping when he punches — strike economy gone. Make him pay for every exchange.",
            "Round's yours. He's loading up to compensate for fatigue — that's predictable. Time the counter on his next big shot.",
        ],
    },
    "lost_round_clearly": {
        "low":  [
            "{fighter_name}, gassed already? Pace it.",
            "You're burning hot. Slow it down.",
        ],
        "mid":  [
            "You're throwing in volume but it's costing you, {fighter_name}. Quality over quantity — fewer, harder shots.",
            "Pace is killing you. Pick your moments — explode in bursts, recover in clinch.",
        ],
        "high": [
            "Your output cratered late in the round, {fighter_name}. Cardio's the issue. Throw 2-shot combos max next round, recover between exchanges in the clinch.",
            "You're burning through your tank with no payoff. Cut the volume in half, double the precision. He's been waiting for you to gas.",
        ],
    },
    "close_round": {
        "low":  [
            "{fighter_name}, even round. Stay smart.",
            "Close one. Pace it.",
        ],
        "mid":  [
            "Coin flip, {fighter_name}. He'll fade before you do — make him work, then capitalize.",
            "Even round. Your engine is the difference late — be patient, his pace drops in 3 minutes.",
        ],
        "high": [
            "Round's even but the math is yours. He's working harder for the same output — you'll separate in rounds 3 and 4. Don't force it now.",
            "Close one. He's spending energy you're not. Stay patient — when his combos drop from 4 to 2, that's your window.",
        ],
    },
    "fighter_hurt": {
        "low":  [
            "{fighter_name}, hands up. Breathe through it.",
            "Cover up. Walk it off.",
        ],
        "mid":  [
            "You're hurt, {fighter_name} — drop the volume, regulate breathing. Clinch when he closes, recover.",
            "Survive the round. Slow breathing, body relaxed. Adrenaline burns fast — don't waste any.",
        ],
        "high": [
            "You're hurt but your conditioning will carry you out of this round. Don't panic-throw — that burns oxygen you need. Slow breathing, deep clinches, ride it out.",
            "He's hurt you and he knows it — he'll come hunting. Your gas tank is the difference. Make him chase, make him miss, his lungs will tap before your chin does.",
        ],
    },
    "fighter_gassing": {
        "low":  [
            "{fighter_name}, breathe deep. You trained for this.",
            "Pace. Don't burn the tank.",
        ],
        "mid":  [
            "Your cardio's slipping, {fighter_name}. Drop the volume — fewer, harder shots.",
            "Heart rate's spiking. Use the clinch to recover — tie him up for 10 seconds, breathe.",
        ],
        "high": [
            "You're cardio-dropping faster than expected. Switch to economy mode — every shot counts. Stop throwing 4-punch combos when 2 do the job.",
            "Gas tank's dropping but his is too. This is the round conditioning wins — control the pace, force HIM to chase. He'll quit before you do.",
        ],
    },
    "fighter_dropped": {
        "low":  [
            "{fighter_name}, shake it off. Breathe.",
            "Cover. Get your wind back.",
        ],
        "mid":  [
            "You got cracked, {fighter_name}. Adrenaline dump now — control breathing, don't sprint into the next exchange.",
            "He hurt you. Don't try to prove you're fine by trading — that'll get you finished. Smart pace.",
        ],
        "high": [
            "You got dropped and your heart rate just spiked 30 BPM. Recovery is your priority — clinch, breathe, slow it. Don't chase a return shot until your tank refills.",
            "Adrenaline's masking damage right now. Use the next 90 seconds to assess — slow breathing, light footwork, no committing. When the dump fades, your real fitness carries.",
        ],
    },
    "scored_knockdown": {
        "low":  [
            "{fighter_name}, you cracked him! Don't burn out chasing!",
            "He's hurt! Smart pace!",
        ],
        "mid":  [
            "You hurt him, {fighter_name} — don't sprint to the finish and gas yourself. Walk him down, controlled pressure.",
            "He's wobbled. Conserve — pick your shots, don't burn the tank trying for the highlight.",
        ],
        "high": [
            "You wobbled him. Don't dump your gas tank chasing — controlled pressure, force him to defend while you pace. He'll fold from fatigue, not just damage.",
            "Hurt fighter recovers faster than gassed fighter. Don't sprint — walk-down pace, force him to retreat, make HIM burn the tank. Then close.",
        ],
    },
    "opponent_hurt": {
        "low":  [
            "{fighter_name}, he's fading. Press the pace.",
            "He's gassing. Stay on him.",
        ],
        "mid":  [
            "He's done, {fighter_name}. Press the pace — he can't recover at fight rhythm.",
            "He's gassed AND hurt. Force the pace — every 10 seconds you press, he loses more.",
        ],
        "high": [
            "He's gassed and his recovery rate is dropping each round. Press the pace ALL round — no breaks, force him to fight at YOUR rhythm. He won't last.",
            "His gas tank is shot and his composure's slipping. Stay on him every second — clinch when he reaches, knee the body, drain him to nothing.",
        ],
    },
    "outstriking": {
        "low":  [
            "{fighter_name}, output is yours. Keep going.",
            "Volume's working. Stay on it.",
        ],
        "mid":  [
            "You're out-landing him on volume, {fighter_name}. Your engine's the difference — keep the pressure.",
            "Output's yours. He's matching pace now but won't in round 3 — pay forward.",
        ],
        "high": [
            "You're out-working him. Sustainability is the question — your training says yes, he's the unknown. Maintain this pace, watch his shoulders drop, then double down.",
            "Volume's yours and he's burning gas to keep up. Keep the rhythm — when his combos shorten from 4 to 2, you press harder. Math is on your side.",
        ],
    },
    "being_outstruck": {
        "low":  [
            "{fighter_name}, output's down. Pace better.",
            "Stay in your tank. Don't burn out.",
        ],
        "mid":  [
            "He's out-throwing you, {fighter_name}. Counter pace — let him empty his tank, then capitalize.",
            "Your output's dropping. Sharper shots, fewer combos. Quality wins the cards too.",
        ],
        "high": [
            "He's out-landing on volume because you're pacing wrong, {fighter_name}. Don't try to match — counter rhythm. Let him punch himself out, then strike when he resets.",
            "Volume is his game right now. Don't trade it — pace is yours. Stick and move, recover in clinch, save the tank. He's burning faster than he knows.",
        ],
    },
    "need_finish": {
        "low":  [
            "{fighter_name}, last round! Empty the tank!",
            "Finish or lose. Go!",
        ],
        "mid":  [
            "You need the finish, {fighter_name}. No reserve — empty everything you have this round.",
            "Down on the cards. Burn every drop — there's no next round to pace for.",
        ],
        "high": [
            "No points left, no reason to conserve. Open the tank — every conditioning rep was for this 5 minutes. Pressure non-stop, force the finish.",
            "Last round, full burn. You trained for this — pace doesn't matter, only output. Walk him down, never let him reset, force the stoppage on cardio alone.",
        ],
    },
    "coast_on_cards": {
        "low":  [
            "{fighter_name}, you've got it. Smart pace.",
            "Cards are yours. Don't burn out.",
        ],
        "mid":  [
            "You're up, {fighter_name}. He needs the finish — let him chase, let him gas. Counter-pace him.",
            "Coast this one. Sharp counters, don't engage offensively. Make HIM empty the tank.",
        ],
        "high": [
            "You're up and he has to chase. Counter-pace is your friend — light volume, stay defensively responsible, let him empty his tank trying to land the kill shot.",
            "Cards are yours. Don't fight emotionally — pace is the win condition. Counter shots only, recover in clinch, eat the clock. He gasses first.",
        ],
    },
}


MMA_HEAD_COACH = {
    "won_round_clearly": {
        "low":  [
            "{fighter_name}, you took it. Keep going.",
            "Good round. Stay focused.",
        ],
        "mid":  [
            "That round's yours, {fighter_name}. He's not solving you — make him keep guessing.",
            "Round in the bank. Don't change what's working.",
        ],
        "high": [
            "Round's yours. He's adjusting between exchanges — you saw him reset his stance twice. Next time, combo, then immediately change levels. He won't have time.",
            "You're up. He's been hunting one shot all round — anticipate it. Slip, two-piece, circle out. He'll start to doubt himself.",
        ],
    },
    "lost_round_clearly": {
        "low":  [
            "{fighter_name}, you gave that one away. Reset.",
            "Tighten up. We need the next round.",
        ],
        "mid":  [
            "He's reading you, {fighter_name}. Switch up the rhythm — break your patterns.",
            "You're a step behind. Take a breath, reset the game plan, don't force exchanges.",
        ],
        "high": [
            "He's adjusted to your A-game, {fighter_name}. Go to your B-game — if you've been hunting the cross, hide it behind kicks. If you've been wrestling, strike first.",
            "You're losing the chess match. He's two moves ahead — disrupt his rhythm. Change tempo, change stance, change levels. Anything to break his read.",
        ],
    },
    "close_round": {
        "low":  [
            "{fighter_name}, close one. Stay sharp.",
            "Even round. Focus up.",
        ],
        "mid":  [
            "Coin flip, {fighter_name}. Win the next 30-second windows — first and last of each minute. Judges score memory.",
            "Even round. You need a signature moment — one clean combo, one heavy takedown. Something they remember.",
        ],
        "high": [
            "That round's a toss-up. The judges remember the last 30 seconds — finish every round with intent, even a flurry. Make sure the final image is yours.",
            "Even round but you're outworking him in patches. Sustain it for the full 5 minutes next time — no dead air. Judges don't reward potential, they reward output.",
        ],
    },
    "fighter_hurt": {
        "low":  [
            "{fighter_name}, hands up. Be smart.",
            "Cover up. Survive.",
        ],
        "mid":  [
            "You're hurt, {fighter_name}. Don't be a hero — clinch, tie him up, ride out the round.",
            "Smart fighter. Slow it down — clinch, retreat, no exchanges in the pocket.",
        ],
        "high": [
            "You're hurt but you're not broken. The IQ play is to deny him the followup — clinch immediately, eat 30 seconds, reset center. Don't let him build momentum.",
            "He's hunting the finish. Take that off the table — clinch, control, force the ref to break, walk back to center, repeat. Eat the clock. We win the next round.",
        ],
    },
    "fighter_gassing": {
        "low":  [
            "{fighter_name}, breathe. Pace it.",
            "Slow down. Pick spots.",
        ],
        "mid":  [
            "You're gassing, {fighter_name}. Drop the volume — pick spots, recover in clinch.",
            "Tired. Be smart — fewer exchanges, but make them count. Don't chase.",
        ],
        "high": [
            "You're gassing — switch to counter mode. Let him commit, slip, two-piece, circle out. Conserve, pick spots, win the chess match while you recover.",
            "Cardio's a constraint right now. The IQ play is to make him fight at YOUR pace — clinch when he closes, drag him to the mat if you can, force the ref to reset.",
        ],
    },
    "fighter_dropped": {
        "low":  [
            "{fighter_name}, shake it off. Reset.",
            "He cracked you. Tighten up.",
        ],
        "mid":  [
            "You got dropped, {fighter_name}. He'll come hunting — change your patterns, don't give him the same look twice.",
            "He found that shot once. Don't give him a second one — change levels, change angle, break the read.",
        ],
        "high": [
            "He found the timing once — he'll go back to it. Anticipate. Fake the same setup that got you caught, draw the counter, then YOU counter HIS counter.",
            "He's confident now. Use it against him. Confident fighters overextend — bait the kill shot, slip, pivot off, make him pay for the boldness.",
        ],
    },
    "scored_knockdown": {
        "low":  [
            "{fighter_name}, you got him! Finish!",
            "He's hurt! Press!",
        ],
        "mid":  [
            "You wobbled him, {fighter_name} — don't dive in wild. Smart pressure — combinations, then back out.",
            "He felt that. Hunt the finish but stay disciplined — desperate fighters throw bombs.",
        ],
        "high": [
            "You hurt him. The trap is wading in for the finish — that's where you eat a desperation counter. Pressure smart: jab, force the commit, then strike.",
            "His legs went. Don't try to finish with one bomb — go to the body, drain the gas, then upstairs when he drops the hands. Calculated kill.",
        ],
    },
    "opponent_hurt": {
        "low":  [
            "{fighter_name}, he's fading. Press.",
            "He's hurt. Stay on him.",
        ],
        "mid":  [
            "He's banged up, {fighter_name}. Don't let him reset — keep him moving backward, no breathing room.",
            "He's hurt. Pick your domain — wherever he's defending worst, attack there.",
        ],
        "high": [
            "He's hurt but trying to hide it. Watch his eyes between exchanges — that's the tell. When the focus drifts, that's your moment to commit.",
            "He's compromised. The smart play is sustained pressure — never let him reset to center, never give him 5 seconds to breathe. Drown him.",
        ],
    },
    "outstriking": {
        "low":  [
            "{fighter_name}, you're landing. Keep it up.",
            "Output's working. Stay on it.",
        ],
        "mid":  [
            "You're out-landing him, {fighter_name}. He'll change tactics — be ready. Shoot's coming next round.",
            "Striking's yours. Watch the level changes — when he shoots, sprawl heavy.",
        ],
        "high": [
            "You're winning the striking. Now anticipate the pivot — he'll try to grapple. Be ready to sprawl on the shot, deny the body lock in clinch, force him back to striking range.",
            "Striking's yours but he's setting traps. He's eating shots to bait your habits — every clean cross, his hand drops. Stay disciplined, throw the cross clean, circle out before the counter.",
        ],
    },
    "being_outstruck": {
        "low":  [
            "{fighter_name}, you're getting hit. Move.",
            "Defense! Reset!",
        ],
        "mid":  [
            "He's landing cleaner, {fighter_name}. Change your fight — if striking's losing, level change. If clinch is losing, kick from range.",
            "You're losing the striking exchanges. Don't fight on his terms — drag him to your domain. Wrestling, clinch, kicks — whatever shifts the matchup.",
        ],
        "high": [
            "He's winning the striking because you're fighting his fight. Change the equation — if he's a boxer, kick. If he's a kickboxer, clinch. Don't trade in his strength.",
            "Every exchange on the feet is points for him. The IQ play is to deny him the range he wants — close to clinch or kick from outside. Stop standing where he's effective.",
        ],
    },
    "need_finish": {
        "low":  [
            "{fighter_name}, you need this round!",
            "Finish or lose. Go!",
        ],
        "mid":  [
            "You need the finish, {fighter_name}. Forget points. Pick your highest-percentage finish and commit.",
            "Down on the cards. Open up — pressure, force the engagement, force the mistake.",
        ],
        "high": [
            "No points left. Pick your highest-percentage finish — strikes if you're a striker, sub if you're a grappler — and chase it ruthlessly. Don't fight his fight.",
            "We need the stoppage. He's been managing the fight all round — disrupt that. High pressure, weird angles, anything that breaks his rhythm. Force him to react, not plan.",
        ],
    },
    "coast_on_cards": {
        "low":  [
            "{fighter_name}, you've got it. Stay smart.",
            "Don't get reckless.",
        ],
        "mid":  [
            "You're up, {fighter_name}. He needs the finish — let him chase, counter the desperation.",
            "Coast this one. Movement, jabs, counters. Don't get drawn into his fight.",
        ],
        "high": [
            "You're up and he has to chase. The IQ play is patience — counter shots, smart angles, no offensive risks. He'll get reckless trying to finish — punish each mistake.",
            "Cards are yours. He'll throw the kitchen sink — be the calm one. Defend first, counter second, make him miss until the horn. Don't get drawn into a brawl trying to put a bow on it.",
        ],
    },
}


ARCHETYPE_LIBRARIES = {
    "striking":  STRIKING_COACH,
    "grappling": GRAPPLING_COACH,
    "sc":        SC_COACH,
    "mma_head":  MMA_HEAD_COACH,
}


# Which next-round bonus does each archetype's advice nudge?
BONUS_TYPE_MAP = {
    "striking":  "striking_bonus",
    "grappling": "grappling_bonus",
    "sc":        "stamina_bonus",
    "mma_head":  "composure_bonus",
}


# Priority order for situation tags — when multiple match, we pick
# the highest-priority one that has content at this tier.
SITUATION_PRIORITY = [
    "fighter_dropped",
    "fighter_hurt",
    "scored_knockdown",
    "need_finish",
    "fighter_gassing",
    "lost_round_clearly",
    "won_round_clearly",
    "being_outstruck",
    "outstriking",
    "winning_takedown_battle",
    "losing_takedown_battle",
    "controlling_position",
    "opponent_hurt",
    "coast_on_cards",
    "close_round",
]


def _pick_template(
    archetype: str,
    situations: List[str],
    tier: str,
    rating: int,
    seen_templates: Optional[set] = None,
) -> Optional[Tuple[str, str]]:
    """
    Returns (chosen_situation, chosen_template) or None.

    Lookup order:
    1. Archetype's own library at (situation, tier) — primary domain
    2. Generalist (mma_head) library at (situation, tier) — only if
       rating >= CORNER_SECONDARY_DOMAIN_MIN (cross-specialty read)
    3. Fall back to "close_round" at tier in primary library

    seen_templates: if provided, filters out already-used templates
    from each pool; only falls back to the full pool when all entries
    have been seen (so repeats are inevitable). Prevents the same
    line from echoing across rounds when the pool is small.
    """
    primary = ARCHETYPE_LIBRARIES.get(archetype, MMA_HEAD_COACH)
    _seen = seen_templates if seen_templates is not None else set()

    def _pick(pool: List[str]) -> str:
        # Prefer unseen entries; fall back to full pool if exhausted.
        unseen = [t for t in pool if t not in _seen]
        return random.choice(unseen if unseen else pool)

    for sit in SITUATION_PRIORITY:
        if sit not in situations:
            continue
        if sit in primary and tier in primary[sit]:
            return sit, _pick(primary[sit][tier])

    # Secondary domain fallback at high rating
    if rating >= CORNER_SECONDARY_DOMAIN_MIN and archetype != "mma_head":
        for sit in SITUATION_PRIORITY:
            if sit not in situations:
                continue
            if sit in MMA_HEAD_COACH and tier in MMA_HEAD_COACH[sit]:
                return sit, _pick(MMA_HEAD_COACH[sit][tier])

    # Final fallback — close_round at tier in primary
    if "close_round" in primary and tier in primary["close_round"]:
        return "close_round", _pick(primary["close_round"][tier])

    return None


def generate_corner_advice(
    coach_dict: Dict[str, Any],
    fighter_name: str,
    opponent_name: str,
    player_health: float,
    player_stamina: float,
    opponent_health: float,
    round_stats_player: Dict[str, Any],
    round_stats_opponent: Dict[str, Any],
    cumulative_score_gap: float,
    round_num: int,
    total_rounds: int,
    seen_templates: Optional[set] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build corner advice for a single between-round moment.

    Returns None if:
    - No coach (vacant)
    - Final round (no "next round" to advise for)

    Otherwise returns:
    {
        "coach_name":   str,
        "lines":        [str],
        "bonus_type":   str,
        "bonus_amount": float,
        "situation":    str,
    }
    """
    if round_num >= total_rounds:
        return None
    if not coach_dict or coach_dict.get("name") in (None, "", "Vacant"):
        return None

    rating = int(coach_dict.get("rating", 60) or 60)
    archetype = _archetype_from_specialty(coach_dict.get("specialty", "mma"))
    tier = _rating_tier(rating)

    situations = _detect_situations(
        player_health, player_stamina, opponent_health,
        round_stats_player, round_stats_opponent,
        cumulative_score_gap, round_num, total_rounds,
    )

    pick = _pick_template(archetype, situations, tier, rating, seen_templates)
    if not pick:
        return None
    chosen_situation, template = pick
    # Record so caller's future picks avoid this template.
    if seen_templates is not None:
        seen_templates.add(template)

    line = template.format(
        fighter_name=fighter_name,
        opponent_name=opponent_name,
    )

    bonus_amount = CORNER_BONUS_BASE + max(0, rating - 60) * CORNER_BONUS_PER_RATING_POINT
    bonus_type = BONUS_TYPE_MAP.get(archetype, "composure_bonus")

    return {
        "coach_name":   coach_dict.get("name", "Coach"),
        "lines":        [line],
        "bonus_type":   bonus_type,
        "bonus_amount": bonus_amount,
        "situation":    chosen_situation,
    }


# ── Pre-fight buff (Path α mechanical approximation) ──────────
# The fight runs all rounds in one engine call, so per-round
# reactive bonuses need engine surgery. Ship K1 approximates:
# "having a coach helps" via a small pre-fight attribute buff on
# the player fighter. The advice TEXT is reactive per-round; the
# mechanic is a single flat buff. Acceptable trade for this ship.

# Which attributes each archetype boosts pre-fight.
ARCHETYPE_BUFF_ATTRS = {
    "striking":  ("boxing", "kicks", "striking_defense"),
    "grappling": ("takedowns", "takedown_defense", "submissions"),
    "sc":        ("cardio", "recovery", "heart"),
    "mma_head":  ("fight_iq", "composure"),
}


def compute_prefight_buff(coach_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compute pre-fight attribute buff from coach. Returns None if vacant.
    Caller is responsible for applying the buff to the engine fighter
    attributes object.
    """
    if not coach_dict or coach_dict.get("name") in (None, "", "Vacant"):
        return None
    rating = int(coach_dict.get("rating", 60) or 60)
    archetype = _archetype_from_specialty(coach_dict.get("specialty", "mma"))
    bonus = CORNER_BONUS_BASE + max(0, rating - 60) * CORNER_BONUS_PER_RATING_POINT
    # CORNER_MAN trait boosts the pre-fight buff
    if 'CORNER_MAN' in (coach_dict.get('traits', []) or []):
        bonus += 0.10
    return {
        "archetype":  archetype,
        "attrs":      ARCHETYPE_BUFF_ATTRS.get(archetype, ("fight_iq",)),
        "amount":     bonus,
    }
