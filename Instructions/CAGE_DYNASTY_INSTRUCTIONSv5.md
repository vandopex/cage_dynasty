# CAGE DYNASTY - Project Instructions
Updated: December 23, 2024
Status: ~1,900+ Tests | ~51,500+ Lines of Code | PRE-RELEASE FEATURE EVALUATION

---

## PROJECT VISION

Cage Dynasty is a text-based MMA management simulator designed to feel like a living, breathing world. Drawing inspiration from Basketball GM's statistical depth and emergent storytelling, the game creates memorable narratives through interconnected systems rather than scripted events.

### Core Philosophy
- **Organic over Scripted:** Every rivalry, upset, and dynasty emerges from simulation
- **Depth with Accessibility:** Complex systems, streamlined interface
- **History Matters:** Every fight shapes the future of the sport
- **Fair Competition:** AI camps follow the same rules as the player
- **Text is the Graphics:** Rich descriptions create immersion

### Game Identity
- **Promotion Name:** Dynasty Fighting Championship (DFC)
- **Single Promotion Model:** All fighters compete in DFC
- **Player Role:** Manage a training camp, develop fighters, compete for championships
- **Time Scale:** Weekly advancement with event-driven progression

---

## CURRENT STATE: PRE-RELEASE FEATURE EVALUATION

The game is fully functional with all major systems integrated. Currently evaluating which features to add/tweak before public release.

### All Systems Working

| Category | Systems |
|----------|---------|
| Core Loop | New game, save/load, week advancement, hub dashboard |
| Fighter Management | Stats, training camps, aging, injuries, career phases |
| Fight Simulation | Full narrated engine, play-by-play, round summaries, judges |
| Matchmaking | Smart AI scheduling, cooldowns, ranked vs ranked preference |
| Economy | Purses, sponsorships, loans, camp upgrades, facilities |
| Narrative | News feed, rivalries (8 types), post-fight interviews, commentary |
| Rankings | Division rankings, title fights, contender system |
| Scouting | Fighter evaluation, tale of tape, prospect potential |
| Strategy | Gameplan selection, coach specialties, training focuses |
| History | Archives, GOAT rankings, Record Book, Champions History |
| Awards | Fight of the Night with bonuses |
| Traits | 16 traits with stat/fight modifiers |
| Condition | Fighter fatigue, fight readiness, stamina penalties (NEW) |

---

## RECENT CHANGES (December 2024)

### REST Intensity Added
Fighters can now take full rest weeks during training camp:

| Intensity | Gains | Fatigue | Injury Risk |
|-----------|-------|---------|-------------|
| **REST** | 0% | **-15** (recovery!) | 0% |
| LIGHT | 50% | +2 | 0% |
| MODERATE | 100% | +5 | 1% |
| INTENSE | 150% | +10 | 3% |
| EXTREME | 200% | +18 | 8% |

### Fatigue → Fight Performance System
New `condition.py` module connects training fatigue to fight performance:

| Fatigue Level | Category | Starting Stamina |
|---------------|----------|------------------|
| 0-20 | Fresh | 100% |
| 21-40 | Rested | 95% |
| 41-60 | Ready | 88% |
| 61-80 | Tired | 78% |
| 81-100 | Exhausted | 65% |

Creates meaningful decisions: Train hard = better skills but start fights gassed.

---

## DEVELOPMENT ENVIRONMENT

### System Setup
```bash
# Mac Terminal Commands
# Project Location: ~/Desktop/Games/cage_dynasty

cd ~/Desktop/Games/cage_dynasty

# Run all tests
python3 -m pytest tests/ -v

# Run the game
python3 main.py

# Check test count
python3 -m pytest tests/ --collect-only | tail -5
```

### Key Directories
```
~/Desktop/Games/cage_dynasty/
├── main.py                 # Game entry point
├── tests/                  # ~1,900+ tests
├── core/                   # Foundation (game_state, persistence, events, calendar)
├── entities/               # Fighter, Camp, Promotion, Contract
├── systems/                # Training, economy, rankings, matchmaking, condition, etc.
├── simulation/             # Fight engine, world generation
├── narrative/              # Rivalry, commentary, news
├── interface/              # cli.py (~11,400 lines)
└── saves/                  # Save files
```

---

## KEY SYSTEMS REFERENCE

### Weight Classes (9 Divisions)

| Class | Min (lbs) | Max (lbs) |
|-------|-----------|-----------|
| Strawweight | 106 | 115 |
| Flyweight | 116 | 125 |
| Bantamweight | 126 | 135 |
| Featherweight | 136 | 145 |
| Lightweight | 146 | 155 |
| Welterweight | 156 | 170 |
| Middleweight | 171 | 185 |
| Light Heavyweight | 186 | 205 |
| Heavyweight | 206 | 265 |

### 16 Fighter Traits

| Trait | Category | Effect |
|-------|----------|--------|
| Glass Cannon | Physical | +15 Power, -15 Chin |
| Iron Chin | Physical | +15 Chin, -5 Speed |
| Cardio Machine | Physical | +15 Cardio, -5 Power |
| Knockout Artist | Striking | +10% KO chance |
| Submission Ace | Grappling | +10% Sub chance |
| Wrestler's Base | Grappling | +10 TD Defense |
| Pressure Fighter | Mental | +5 all vs Counter |
| Counter Striker | Mental | +5 all vs Pressure |
| Fast Starter | Mental | +10% Round 1 |
| Slow Starter | Mental | +10% Rounds 3+ |
| Big Game Hunter | Mental | +10% in title fights |
| Choke Artist | Mental | -15% in title fights |
| Gym Rat | Training | +20% training gains |
| Injury Prone | Health | +50% injury chance |
| Durable | Health | -30% injury chance |
| Veteran Savvy | Mental | +5 IQ, +5 Composure |

### Camp Tiers

| Tier | Max Fighters | Training Bonus | Monthly Cost |
|------|--------------|----------------|--------------|
| Garage | 3 | 0.9x | $2,000 |
| Local | 5 | 1.0x | $6,000 |
| Regional | 8 | 1.1x | $20,000 |
| National | 12 | 1.2x | $60,000 |
| Elite | 20 | 1.3x | $200,000 |

### Training Focuses (6 Options)

| Focus | Attributes Improved | Best For |
|-------|---------------------|----------|
| Striking | Boxing, Kicks, Defense | Stand-up fighters |
| Wrestling | Wrestling, TD Defense, Top Control | Wrestlers |
| Jiu-Jitsu | BJJ, Submissions, Guard | Grapplers |
| Conditioning | Cardio, Recovery | Everyone |
| Strength & Power | Strength, Speed, Power | Power punchers |
| Balanced | All (smaller gains) | Well-rounded |

### Title Fight Rules
- Champions only fight top 5 contenders
- All champion fights are title defenses
- Challengers must be ranked #1-5 to get title shot

---

## UNDER CONSIDERATION

Features being evaluated for possible redesign before release:

### Training Camp Flow
**Current:** Set intensity once at camp start, runs 8 weeks automatically.
**Question:** Should intensity be a week-to-week decision for more engagement?

**Options Under Consideration:**
1. **Keep Current + Auto-Taper** - System auto-switches to LIGHT/REST in final weeks
2. **Weekly Intensity Selection** - More control, but 8 decisions per camp
3. **Key Weeks Only** - Prompt at Week 1, 4, 7 only (3 decisions)
4. **Camp Plan Templates** - Choose pattern ("Start Hard, Taper Late") that auto-adjusts

**What's Working:** Stats changing week-to-week feels good. Camp Journal narrative is engaging.

---

## BACKLOG

### High Priority (Before Release)
- [ ] Wire FOTN module to UI (built but not integrated)
- [ ] Evaluate training camp flow (see "Under Consideration")
- [ ] Fight readiness display in pre-fight UI (use new condition.py)

### Medium Priority
- [ ] **Overcrowding Penalty** - Allow signing over roster cap but apply -20% training gains
- [ ] **Watchlist Auto-Tagging** - Auto-add fighters with context tags: `#ROBBERY`, `#HURT_MY_BOY`, `#EX_ROSTER`
- [ ] Interviews and media systems (press conferences, face-offs, hype)
- [ ] Scouting enhancements (tiered costs, film study, scout personnel)
- [ ] Tale of the tape improvements

### Lower Priority
- [ ] **Facility Modules** - Small upgrades within tiers ($2k-$10k): Heavy Bags, Ice Bath, Video Room
- [ ] **Watchlist Intel System** - Knowledge level grows over weeks watched, reveals hidden info
- [ ] Signature moves based on skill thresholds
- [ ] Dual fighting styles
- [ ] Weight cutting mechanics
- [ ] Corner dialogue between rounds

### Future Considerations
- [ ] Contract expiration (fighters leave if not re-signed)
- [ ] Amateur tournaments (16-fighter brackets)
- [ ] Hall of Fame (career achievements)
- [ ] Weight class changes (move up/down divisions)
- [ ] AI full fight engine (performance trade-off)

---

## MODULE STATISTICS

| Category | Files | Lines |
|----------|-------|-------|
| Core | 7 | ~5,400 |
| Entities | 4 | ~3,100 |
| Systems | 13 | ~13,150 |
| Simulation | 8 | ~10,600 |
| Narrative | 4 | ~4,850 |
| Interface | 3 | ~11,400+ |
| **TOTAL** | **51+** | **~51,500+** |

### New Module
- `systems/condition.py` (~340 lines) - Fighter fatigue, readiness ratings, stamina penalties

---

## DEVELOPMENT RULES

### Code Standards
- **Complete Modules:** Every delivery must be fully functional
- **Line Count Reporting:** Include total lines in each code block
- **Paste-and-Replace:** Full file replacements preferred over patches
- **Type Hints:** All functions use Python type hints
- **Graceful Fallbacks:** If a module fails to import, use simple fallback

### Session Workflow
1. **Request:** Ask for a feature/fix/enhancement
2. **Receive:** Get complete code with line counts
3. **Download:** Get files from provided links
4. **Place:** Put files in correct locations
5. **Test:** Run the game, verify it works
6. **Confirm:** Report success or issues

---

## COMMUNICATION GUIDE

### How Van Works
- Uses Mac with `python3` command
- Project path: `~/Desktop/Games/cage_dynasty/`
- Prefers paste-and-replace over incremental edits
- Wants line counts reported for verification
- Tests after each change before proceeding
- Will interrupt if going in wrong direction - that's good, saves time

### Communication Tips
- **Be direct:** Van gives concise feedback, respond in kind
- **Don't over-explain:** If something is wrong, Van will say so simply
- **Ask clarifying questions early:** Better to confirm intent than rebuild
- **When Van says "fix":** Focus on the specific issue, not tangential improvements
- **Screenshots/pastes of game output:** These show exactly what's wrong - use them
- **"What's next?":** Van likes momentum, be ready with the fix or next step

### What Van Values
- Systems that connect (not orphaned code)
- Clean UI that shows relevant info
- Realism in MMA mechanics
- Code that actually runs (test before delivering)
- Respecting existing architecture

---

## FILES TO SHARE FOR TRAINING SYSTEM REVIEW

When getting external feedback on training camp design, share these files:

1. **`training.py`** (~2,200 lines) - Core training system, formulas, events
2. **`training_camp.py`** (~1,100 lines) - Camp integration, journal, week processing  
3. **`condition.py`** (~340 lines) - Fatigue/readiness system

### Key Formulas Reference

```python
# Intensity effects
INTENSITY_MULTIPLIERS = {
    REST: 0.0, LIGHT: 0.5, MODERATE: 1.0, INTENSE: 1.5, EXTREME: 2.0
}

INTENSITY_FATIGUE = {
    REST: -15, LIGHT: 2, MODERATE: 5, INTENSE: 10, EXTREME: 18
}

# Age modifiers  
AGE_GAIN_MODIFIER = {
    "young": 1.3,    # Under 26
    "prime": 1.0,    # 26-32
    "veteran": 0.7,  # 33-35
    "old": 0.4,      # 36+
}

# Facility stat caps
FACILITY_STAT_CAPS = {
    "GARAGE": 65, "LOCAL": 72, "REGIONAL": 80, "NATIONAL": 90, "ELITE": 100
}
```

---

**Last Updated:** December 23, 2024
**Status:** Pre-Release Feature Evaluation
**Next Steps:** Evaluate training camp flow, wire FOTN to UI, add readiness display
