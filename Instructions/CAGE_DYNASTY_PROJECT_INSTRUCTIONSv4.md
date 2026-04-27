# CAGE DYNASTY - Project Instructions & Development Guide
# Updated: December 8, 2025
# Status: ~1,892 Tests Passing | ~43,000+ Lines of Code | Core Loop Working

---

## PROJECT VISION

**Cage Dynasty** is a text-based MMA management simulator designed to feel like a living, breathing world. Drawing inspiration from Basketball GM's statistical depth and emergent storytelling, the game creates memorable narratives through interconnected systems rather than scripted events.

### Core Philosophy
- **Organic over Scripted**: Every rivalry, upset, and dynasty emerges from simulation
- **Depth with Accessibility**: Complex systems, streamlined interface
- **History Matters**: Every fight shapes the future of the sport
- **Fair Competition**: AI camps follow the same rules as the player
- **Text is the Graphics**: Rich descriptions create immersion

### Game Identity
- **Promotion Name**: Dynasty Fighting Championship (DFC)
- **Single Promotion Model**: All fighters compete in DFC
- **Player Role**: Manage a training camp, develop fighters, compete for championships
- **Time Scale**: Weekly advancement with event-driven progression

---

## CURRENT STATE (December 8, 2025)

### What's Fully Working ✅

| Feature | Status | Notes |
|---------|--------|-------|
| New Game Setup | ✅ | Name camp, generate world |
| World Generation | ✅ | 150+ fighters, 25 AI camps, 2+ years history |
| Save/Load System | ✅ | 5 slots + quicksave + autosave |
| Hub Menu | ✅ | Status, alerts, news display |
| My Camp Display | ✅ | Balance, fighter count, tier |
| My Fighters | ✅ | Full stats, training status, scheduled fights |
| Fighter Details | ✅ | All attributes, 16 traits, record, history |
| Rankings | ✅ | All 9 divisions, champions marked |
| Browse Fighters | ✅ | Paginated, searchable by division |
| Browse Camps | ✅ | All camps with tiers |
| Fight Offers | ✅ | Generate, accept, decline with Tale of Tape |
| Upcoming Events | ✅ | Player + AI fights listed |
| Week Advancement | ✅ | Processes fights, training, generates news |
| **Fight Simulation** | ✅ | **FULL ENGINE** - Round-by-round with commentary |
| Sign Free Agents | ✅ | Browse by weight class with scouting |
| Sign Prospects | ✅ | Potential system, development projections |
| Training Camps | ✅ | 6 focuses with opponent recommendations |
| News Feed | ✅ | Fight results, signings, events |
| The Archives | ✅ | GOAT rankings, Record Book, Champions History |
| Traits System | ✅ | 16 traits with stat mods and fight mods |
| **Gameplan Selection** | ✅ | Stance, Focus, Priority before fights |
| **Scouting System** | ✅ | Fighter analysis, matchup comparisons |
| **Prospect Potential** | ✅ | Development ceilings, growth projections |

### Recently Completed (December 2025)

| System | What Was Done |
|--------|---------------|
| Fight Engine Integration | Full 1,857-line engine now powers ALL player fights |
| Commentary System | Round-by-round play-by-play displayed during fights |
| Scouting Module | 991 lines - potential assessment, matchup analysis |
| Free Agents vs Prospects | Meaningful distinction with development potential |
| Gameplan Selection | Pre-fight strategy (Stance/Focus/Priority) |
| Training Overhaul | 6 distinct focuses with smart recommendations |
| Tale of Tape | Side-by-side fighter comparison before fights |

### Systems Built But Not Yet Integrated ⚠️

| System | File | Lines | Notes |
|--------|------|-------|-------|
| Rivalry Display | rivalry_display.py | 931 | 8 types exist, UI ready |
| Aging | aging.py | 569 | Career phase transitions ready |
| Injury | injury.py | 718 | Post-fight injuries ready |
| Economy Full | economy.py | 1,985 | Sponsorships, PPV not surfaced |
| Facilities | facilities.py | 512 | Camp upgrades not in UI |

---

## DEVELOPMENT ENVIRONMENT

### System Setup
```bash
# Mac Terminal Commands
# Project Location: ~/Desktop/Games/cage_dynasty

cd ~/Desktop/Games/cage_dynasty

# Run all tests
python3 -m pytest tests/ -v

# Run specific module tests
python3 -m pytest tests/test_fighter.py -v

# Run the game
python3 main.py

# Check test count
python3 -m pytest tests/ --collect-only | tail -5
```

### Folder Structure
```
~/Desktop/Games/cage_dynasty/
├── main.py                     # Game entry point
├── tests/                      # Test files, ~1,892 tests
├── core/                       # Foundation modules
│   ├── types.py               # Enums, constants, data classes
│   ├── events.py              # Event bus system
│   ├── config.py              # Configuration management
│   ├── calendar.py            # Time & date system
│   ├── game_state.py          # Central game coordinator
│   └── persistence.py         # Save/load system
├── entities/                   # Game objects
│   ├── fighter.py             # Fighter class with traits
│   ├── camp.py                # Training camp management
│   ├── promotion.py           # DFC promotion entity
│   └── contract.py            # Fighter contracts
├── systems/                    # Game mechanics
│   ├── aging.py               # Fighter aging & decline
│   ├── training.py            # Training focus system
│   ├── training_camp.py       # Camp management
│   ├── injury.py              # Injury types & recovery
│   ├── matchmaking.py         # Fight matchmaking algorithms
│   ├── rankings.py            # Division rankings
│   ├── economy.py             # Finances & sponsorships
│   ├── scouting.py            # Fighter evaluation (NEW)
│   ├── traits.py              # 16-trait system
│   └── gameplan.py            # Fight strategy system
├── simulation/                 # Fight & world simulation
│   ├── fight_engine.py        # Core fight simulation (1,857 lines)
│   ├── fight_integration.py   # NarratedFightSimulator wrapper
│   ├── rounds.py              # Round-by-round logic
│   ├── generator.py           # Fighter generation
│   ├── world.py               # AI camp behavior
│   └── world_init.py          # World initialization
├── narrative/                  # Story generation
│   ├── rivalry.py             # 8 rivalry types
│   ├── rivalry_display.py     # Rivalry UI formatting
│   └── commentary.py          # Round-by-round commentary
├── interface/                  # Player UI
│   └── cli.py                 # Text interface (~5,960 lines)
├── data/                       # Static data
│   └── name_database.py       # 17+ nationalities
└── saves/                      # Save files
```

---

## CURRENT TO-DO LIST

### Priority 1: Core Experience Polish

#### 1.1 Fight of the Night (FOTN) System
**Goal**: Award FOTN bonus after each event, track career totals

**Approach**: Score each fight based on action:
```
FOTN Score = (Knockdowns × 50) + (Sig Strikes Landed × 0.5) + 
             (Sub Attempts × 20) + Finish Bonus + Back-and-Forth Bonus
             
Finish Bonus: KO/TKO = 100, Submission = 75, Decision = 0
Back-and-Forth: If lead changed hands, +50
```

**Display**:
- In week summary: "FIGHT OF THE NIGHT: Smith vs Jones (Score: 285)"
- In fighter bio: "Fight of the Night bonuses: 3"

**Alternative (Simpler)**: Just flag exciting fights based on:
- Any fight with 2+ knockdowns
- Any finish in round 3+
- Any split decision

---

#### 1.2 Fix Balance Not Updating After Wins
**Issue**: Won a fight, but balance on status section didn't change
**Task**: Trace purse payment flow, ensure it updates player camp balance

---

#### 1.3 World History Decision Rate
**Issue**: Generated history shows too many decisions, not enough finishes
**Cause**: Simple fight simulation used for history generation
**Options**:
- A) Adjust finish probabilities in history generator
- B) Use complex engine for history (slower but more accurate)
- C) Post-process history to ensure ~60% finish rate

---

#### 1.4 AI vs AI Fights Use Full Engine
**Current**: AI fights use simple 50-line simulation
**Proposed**: Use full fight engine for ALL fights (AI and player)
**Fallback**: Keep simple engine as backup if errors occur
**Tradeoff**: Slower week advancement, but more realistic results

---

### Priority 2: Display Training Progress

#### 2.1 Show Stat Gains During Week Advancement
**Goal**: When advancing week, show training progress:
```
TRAINING PROGRESS
  Rico de Vries (Week 3/8 | Focus: Wrestling)
    This week: Wrestling +1, TD Defense +1
    Camp total: Wrestling +3, TD Defense +2, Top Control +1
```

---

### Priority 3: System Integration

#### 3.1 Aging System Integration
- Process aging during week advancement
- Trigger retirements
- Show career phase in fighter details

#### 3.2 Injury System Integration
- Apply post-fight injuries
- Prevent scheduling injured fighters
- Show injury status and recovery time

#### 3.3 Rivalry Display
- Surface existing rivalry types in UI
- Show rivalry history in fighter details
- Add rivalry-based news items

---

### Future Features (Backlog)

| Feature | Priority | Notes |
|---------|----------|-------|
| Contract Expiration | Medium | Fighters leave if not re-signed |
| Camp Upgrades UI | Medium | Facility tier progression |
| Sponsorship System | Low | Economy depth |
| Amateur Tournaments | Low | 16-fighter brackets |
| Hall of Fame | Low | Career achievements |
| Weight Class Changes | Low | Move up/down |

---

## TRAINING SYSTEM REFERENCE

### Training Focuses (6 Options)

| Focus | Attributes Improved | Best For |
|-------|---------------------|----------|
| Striking | Boxing, Kicks, Defense | Stand-up fighters |
| Wrestling | Wrestling, TD Defense, Top Control | Wrestlers, MMA fighters |
| Jiu-Jitsu | BJJ, Submissions, Guard | Grapplers |
| Conditioning | Cardio, Recovery | Everyone (gas tank) |
| Strength & Power | Strength, Speed, Power | Power punchers |
| Balanced | All (smaller gains) | Well-rounded |

### Training Effectiveness Formula
```
Gain = Base × Diminishing Returns × Age × Camp Tier × Coach × Intensity × Focus Bonus

Where:
- Diminishing Returns: 60-69 = 0.7x, 80-89 = 0.4x, 90+ = 0.2x
- Age: <22 = 1.3x, Prime = 1.0x, 35+ = 0.4x
- Camp Tier: Garage 0.9x → Elite 1.3x
- Coach Quality: 1-star 0.6x → 5-star 1.5x
- Focus Bonus: Focused attributes get 1.5x
```

### Gameplan to Training Alignment

| Gameplan Focus | Recommended Training |
|----------------|---------------------|
| STRIKING | Striking + Conditioning |
| GRAPPLING | Wrestling + Jiu-Jitsu |
| CLINCH | Wrestling + Striking |
| MIXED | Balanced |

---

## SCOUTING SYSTEM REFERENCE

### Free Agents vs Prospects

| Type | Age | Current Rating | Potential | Value |
|------|-----|----------------|-----------|-------|
| Free Agent | 24-35 | 55-85 | What you see | Immediate |
| Prospect | 18-23 | 40-65 | Hidden ceiling | Development |

### Potential Grades

| Grade | Ceiling Range | Meaning |
|-------|---------------|---------|
| Elite | 88-99 | Future champion material |
| High | 78-87 | Title contender potential |
| Average | 65-77 | Solid roster fighter |
| Limited | 55-64 | Career journeyman |
| Low | 45-54 | Limited upside |

### Development Speed by Age

| Age | Training Multiplier |
|-----|---------------------|
| 18 | 1.5x (50% faster) |
| 19 | 1.4x |
| 20 | 1.3x |
| 21-22 | 1.2x |
| 23-25 | 1.1x |
| 26-32 | 1.0x (prime baseline) |
| 33+ | 0.6x-0.4x (decline) |

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
| Garage | 5 | 0.9x | $5,000 |
| Local | 10 | 1.0x | $15,000 |
| Regional | 20 | 1.1x | $40,000 |
| National | 35 | 1.2x | $100,000 |
| Elite | 50 | 1.3x | $250,000 |

---

## FIGHT ENGINE REFERENCE

### Stats Tracked Per Fight
- Significant strikes (attempted/landed)
- Knockdowns
- Takedowns (attempted/landed)
- Submission attempts
- Control time (ground, clinch)
- Damage to body parts

### FOTN Scoring (Proposed)
```python
def calculate_fotn_score(fight_result):
    score = 0
    
    # Action scoring
    for fighter_stats in [fight_result.fighter1_stats, fight_result.fighter2_stats]:
        for round_stats in fighter_stats:
            score += round_stats.get("knockdowns", 0) * 50
            score += round_stats.get("sig_strikes_landed", 0) * 0.5
            score += round_stats.get("sub_att", 0) * 20
    
    # Finish bonus
    if "KO" in fight_result.method or "TKO" in fight_result.method:
        score += 100
    elif "Submission" in fight_result.method:
        score += 75
    
    # Late finish bonus (drama)
    if fight_result.is_finish and fight_result.finish_round >= 3:
        score += 50
    
    return score
```

---

## DEVELOPMENT RULES

### Code Standards

1. **Complete Modules**: Every delivery must be fully functional with tests
2. **Line Count Reporting**: Include total lines in each code block
3. **Paste-and-Replace**: Full file replacements preferred over patches
4. **Type Hints**: All functions use Python type hints
5. **Docstrings**: Every class and public method documented
6. **No Circular Imports**: Strict dependency hierarchy
7. **Event-Driven**: Systems communicate through the event bus
8. **Test Coverage**: Each module has corresponding test file
9. **Graceful Fallbacks**: If a module fails to import, use simple fallback

### Session Workflow

1. **Request**: Ask for the next feature/fix
2. **Receive**: Get complete code with line counts
3. **Download**: Get files from provided links
4. **Place**: Put files in correct locations
5. **Test**: Run `python3 -m pytest tests/test_[module].py -v`
6. **Verify**: Run all tests `python3 -m pytest tests/ -v`
7. **Confirm**: Report success before moving to next item

---

## COMMUNICATION PREFERENCES

### How Van Works
- Uses Mac with `python3` command
- Project path: `~/Desktop/Games/cage_dynasty/`
- Prefers paste-and-replace over incremental edits
- Wants line counts reported for verification
- Downloads files from provided links
- Tests after each change before proceeding
- Asks "what's next?" to maintain momentum

### Response Style
- Explain the "why" behind technical decisions
- Teach how developers think about problems
- Offer multiple approaches when relevant (simple vs complex)
- Be direct about tradeoffs
- Keep code complete and working

### What Van Appreciates
- When things "just work" after paste-and-replace
- Visual improvements in the game UI
- Systems that create emergent storytelling
- Understanding the reasoning behind choices
- Getting excited about progress together

### Van's Development Philosophy
- Build upon existing sophisticated systems rather than replacing them
- Modular development: build and test each component individually
- Priority-based approach: confirm one thing works before moving to next
- "Garage gym to empire" progression creates better gameplay than starting with full resources

---

## MODULE STATISTICS

| Category | Files | Lines | Tests |
|----------|-------|-------|-------|
| Core | 6 | ~4,500 | ~280 |
| Entities | 4 | ~3,200 | ~200 |
| Systems | 10 | ~8,500 | ~400 |
| Simulation | 6 | ~8,200 | ~300 |
| Narrative | 3 | ~3,500 | ~150 |
| Interface | 1 | ~5,960 | ~60 |
| Data | 1 | ~850 | - |
| **TOTAL** | **46** | **~43,000** | **~1,892** |

---

## DESIGN DECISIONS LOG

### Confirmed Decisions ✅
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data Format | JSON | Human-readable saves, easy debugging |
| Architecture | Event-driven | Loose coupling, emergent behavior |
| UI | Text-based CLI | Focus on simulation depth |
| Time Scale | Weekly ticks | Balance detail and pacing |
| Promotion | Single (DFC) | Cleaner scope |
| Trait Count | 16 | Balanced variety |
| Training Focuses | 6 | Clear, distinct options (Striking/Wrestling/BJJ/Conditioning/Power/Balanced) |
| Free Agent vs Prospect | Distinct systems | Creates meaningful roster decisions |
| Fight Engine | Full for player, considering full for AI | Realism over speed |

### Recent Decisions
| Decision | Choice | Date |
|----------|--------|------|
| Removed "Grappling" training | Replaced with Wrestling + Jiu-Jitsu | Dec 8, 2025 |
| Scouting in separate module | Not embedded in CLI | Dec 8, 2025 |
| Gameplan stored with fight | Foundation for future engine use | Dec 8, 2025 |

---

## QUICK REFERENCE

### Test Commands
```bash
# All tests
python3 -m pytest tests/ -v

# Specific module
python3 -m pytest tests/test_fighter.py -v

# With coverage
python3 -m pytest tests/ --cov=. --cov-report=term-missing

# Fast (no output)
python3 -m pytest tests/ -q
```

### Key Files for Current Priorities
```
# FOTN System (new)
simulation/fight_engine.py      # Has stats we need
interface/cli.py               # Week summary display

# Balance Fix
interface/cli.py               # Check purse payment
entities/camp.py               # Balance updates
systems/economy.py             # Payment logic

# AI Fight Engine
simulation/fight_integration.py # NarratedFightSimulator
interface/cli.py               # advance_week() method

# Training Progress Display
interface/cli.py               # Week advancement section
systems/training.py            # Gain tracking
```

---

*Last Updated: December 8, 2025*
*Current Focus: FOTN System, Balance Fix, AI Fights Full Engine*
*Next Session: Pick a priority from the to-do list*
