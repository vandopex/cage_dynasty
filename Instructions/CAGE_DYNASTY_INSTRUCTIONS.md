# CAGE DYNASTY - Project Instructions & Development Guide
# Updated: December 3, 2025
# Status: ~1,004 Tests Passing | ~19,500+ Lines of Code | Core Loop Working

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

## CURRENT STATE (December 2025)

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
| Fight Offers | ✅ | Generate, accept, decline |
| Upcoming Events | ✅ | Player + AI fights listed |
| Week Advancement | ✅ | Processes fights, training, generates news |
| Fight Simulation | ✅ | Basic version - runs and updates records |
| Sign Free Agents | ✅ | Browse by weight class |
| Sign Prospects | ✅ | Generate new fighters |
| Training Camps | ✅ | Focus selection, weekly gains, trait bonuses |
| News Feed | ✅ | Fight results, signings, events |
| The Archives | ✅ | GOAT rankings, Record Book, Champions History |
| Traits System | ✅ | 16 traits with stat mods and fight mods |

### Sophisticated Systems Built But Not Yet Integrated ⚠️

| System | File | Lines | Integration Status |
|--------|------|-------|-------------------|
| Full Fight Engine | simulation/fight_engine.py | 1,857 | CLI uses simplified version |
| Commentary | narrative/commentary.py | 1,608 | Not displayed during fights |
| Matchmaking Engine | systems/matchmaking.py | 861 | CLI uses basic opponent finding |
| Economy | systems/economy.py | 1,183 | Purses only, no sponsorships/PPV |
| Rivalry | narrative/rivalry.py | 996 | 8 types exist, not surfaced in UI |
| World AI | simulation/world.py | 1,256 | AI personalities not visible |
| Aging | systems/aging.py | 420 | Not processing during week advance |
| Injury | systems/injury.py | 380 | Post-fight injuries not applied |

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
├── tests/                      # 23 test files, ~1,004 tests
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
│   ├── training.py            # Training camps & improvement
│   ├── injury.py              # Injury types & recovery
│   ├── matchmaking.py         # Fight matchmaking algorithms
│   ├── rankings.py            # Division rankings
│   ├── economy.py             # Finances & sponsorships
│   └── traits.py              # 16-trait system
├── simulation/                 # Fight & world simulation
│   ├── fight_engine.py        # Core fight simulation (1,857 lines)
│   ├── fight_integration.py   # NarratedFightSimulator
│   ├── generator.py           # Fighter generation
│   ├── world.py               # AI camp behavior
│   └── world_init.py          # World initialization
├── narrative/                  # Story generation
│   ├── rivalry.py             # 8 rivalry types
│   └── commentary.py          # Round-by-round commentary
├── interface/                  # Player UI
│   └── cli.py                 # Text interface (~4,100 lines)
├── data/                       # Static data
│   └── name_database.py       # 17+ nationalities
└── saves/                      # Save files
```

---

## CURRENT DEVELOPMENT PRIORITY

### Phase A: Complete the Loop (ACTIVE)

**Goal**: Make every fight feel meaningful with real consequences

#### Priority 1: Integrate Full Fight Engine
**Status**: 🔴 Not Started
**Files**: `simulation/fight_engine.py`, `simulation/fight_integration.py`, `narrative/commentary.py`

The CLI currently uses a ~50-line simple fight simulation. We have a sophisticated 1,857-line fight engine with:
- 35+ fighting positions
- 30+ strike types  
- 25+ submission types
- Body part damage tracking
- Intelligent action selection
- Round-by-round commentary

**Task**: Replace `_simple_fight_simulation()` in cli.py with `NarratedFightSimulator` from fight_integration.py

**Expected Outcome**: Fights display commentary, feel dynamic, show stats

---

#### Priority 2: Add Injury System
**Status**: 🔴 Not Started
**Files**: `systems/injury.py`, `entities/fighter.py`

Post-fight injuries should:
- Generate based on fight damage and traits
- Prevent scheduling fights while injured
- Heal during week advancement
- Display in fighter details and news

**Task**: Integrate injury.py into week advancement and fight results

**Expected Outcome**: Fighters get hurt, need recovery time, creates roster management decisions

---

#### Priority 3: Integrate Aging System  
**Status**: 🔴 Not Started
**Files**: `systems/aging.py`

The aging system handles:
- Prime years (26-32)
- Decline period (33+)
- Retirement triggers
- Attribute degradation

**Task**: Process aging during week advancement, trigger retirements

**Expected Outcome**: Fighters have realistic career arcs, roster turnover occurs naturally

---

#### Priority 4: Fix Title Handling
**Status**: 🟡 Partially Working
**Files**: `interface/cli.py`

Current issues:
- Belts don't always transfer correctly after title fights
- No "vacant title" fights
- Champion stripping not implemented

**Task**: Ensure title changes update all relevant data and generate appropriate news

---

#### Priority 5: Camp Finances
**Status**: 🟡 Partially Working
**Files**: `entities/camp.py`, `interface/cli.py`

Current state:
- Balance displays but doesn't decrease
- Fight purses calculated but not always paid
- No bankruptcy consequences

**Task**: Deduct weekly costs, pay purses, warn on low funds

---

### Future Phases (After Phase A)

**Phase B: Deepen Engagement**
- Rivalry system integration
- Full matchmaking engine
- Sponsorship system
- Contract expiration

**Phase C: Polish**
- Sim to next fight
- Fighter search/filter
- Camp upgrade UI
- Settings menu

**Phase D: Expand**
- Amateur tournament system
- Hall of Fame
- Legacy system
- Weight class changes

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

### Session Workflow

1. **Request**: Ask for the next feature/fix
2. **Receive**: Get complete code with line counts
3. **Download**: Get files from provided links
4. **Place**: Put files in correct locations
5. **Test**: Run `python3 -m pytest tests/test_[module].py -v`
6. **Verify**: Run all tests `python3 -m pytest tests/ -v`
7. **Confirm**: Report success before moving to next item

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

### Fighter Attributes (1-100 Scale)
**Physical**: Strength, Speed, Cardio, Chin, Recovery
**Striking**: Boxing, Kicks, Clinch, Power, Accuracy
**Grappling**: Wrestling, BJJ, Takedown Defense, Top Control, Submissions
**Mental**: Heart, IQ, Composure, Aggression

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

### Configuration Values
```python
# Aging
"prime_start": 26
"prime_end": 32
"decline_start": 33
"retirement_avg": 38

# Training
"weeks_per_camp": 8
"max_gain_per_week": 2
"max_gain_per_camp": 5

# Fight Rounds
Standard: 3 rounds
Championship: 5 rounds
```

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
| Amateur System | Deferred | Build core first |
| GOAT Scoring | Wins×10 - Losses×5 + Finishes×5 + Champion bonus | Implemented |

### Open Questions
- Training camp duration options (currently 4/6/8 weeks)
- Fight offer frequency (currently every 2 weeks)
- Economic balance (purses vs expenses)
- Difficulty settings

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

### Key Files for Current Priority
```
# Fight Engine Integration
simulation/fight_engine.py      # The real engine
simulation/fight_integration.py # NarratedFightSimulator wrapper
narrative/commentary.py         # Commentary templates
interface/cli.py               # Where to integrate (line ~3100)

# Injury System
systems/injury.py              # Injury logic
entities/fighter.py            # Fighter.add_injury(), injuries property

# Aging System
systems/aging.py               # Aging logic
interface/cli.py               # advance_week() method
```

---

## NOTES FOR DEVELOPMENT

- Van uses Mac with `python3` command
- Project path: `~/Desktop/Games/cage_dynasty/`
- Prefer paste-and-replace over incremental edits
- Always report line counts
- Provide downloadable file links
- The game IS playable - we're enhancing, not building from scratch
- Priority is making fights feel REAL with the existing sophisticated engine
- 1,857 lines of fight simulation exist - use them!

---

## MODULE STATISTICS

| Category | Files | Lines | Tests |
|----------|-------|-------|-------|
| Core | 6 | ~3,200 | ~230 |
| Entities | 4 | ~2,000 | ~165 |
| Systems | 7 | ~4,400 | ~260 |
| Simulation | 5 | ~5,500 | ~200 |
| Narrative | 2 | ~2,600 | ~100 |
| Interface | 1 | ~4,100 | ~58 |
| Data | 1 | ~800 | - |
| **TOTAL** | **26** | **~22,600** | **~1,004** |

---

*Last Updated: December 3, 2025*
*Current Focus: Phase A - Integrate Full Fight Engine*
*Next Task: Replace simple fight simulation with NarratedFightSimulator*
