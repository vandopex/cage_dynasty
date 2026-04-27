# CAGE DYNASTY - Project Instructions & Development Guide
# Updated: November 29, 2025
# Status: ~1,004+ Tests Passing | ~19,500+ Lines of Code

## PROJECT VISION

**Cage Dynasty** is a text-based MMA management simulator designed to feel like a living, breathing world. Drawing inspiration from Basketball GM's statistical depth and emergent storytelling, the game creates memorable narratives through interconnected systems rather than scripted events.

### Core Philosophy
- **Organic over Scripted**: Every rivalry, upset, and dynasty emerges from simulation
- **Depth with Accessibility**: Complex systems, streamlined interface
- **History Matters**: Every fight shapes the future of the sport
- **Fair Competition**: AI camps follow the same rules as the player

### Game Identity
- **Promotion Name**: Dynasty Fighting Championship (DFC)
- **Single Promotion Model**: All fighters compete in DFC
- **Player Role**: Manage a training camp, develop fighters, compete for championships

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
```

### Current Folder Structure
```
~/Desktop/Games/cage_dynasty/
├── main.py                     # Game entry point ✅
├── tests/                      # All test files
│   ├── __init__.py
│   ├── test_types.py           ✅ 40 tests
│   ├── test_events.py          ✅ 27 tests
│   ├── test_config.py          ✅ 33 tests
│   ├── test_calendar.py        ✅ 49 tests
│   ├── test_fighter.py         ✅ 43 tests
│   ├── test_camp.py            ✅ 43 tests
│   ├── test_promotion.py       ✅ 39 tests
│   ├── test_contract.py        ✅ 39 tests
│   ├── test_aging.py           ✅ 35 tests
│   ├── test_training.py        ✅ 38 tests
│   ├── test_injury.py          ✅ 32 tests
│   ├── test_matchmaking.py     ✅ 36 tests
│   ├── test_rankings.py        ✅ 34 tests
│   ├── test_fight_engine.py    ✅ 63 tests
│   ├── test_commentary.py      ✅ 50 tests
│   ├── test_fight_integration.py ✅ 35 tests
│   ├── test_generator.py       ✅ 47 tests
│   ├── test_economy.py         ✅ 52 tests
│   ├── test_rivalry.py         ✅ 48 tests
│   ├── test_world.py           ✅ 55 tests
│   ├── test_game_state.py      ✅ 51 tests
│   ├── test_persistence.py     ✅ 45 tests
│   └── test_cli.py             ✅ 58 tests
├── core/                       # Foundation modules
│   ├── __init__.py
│   ├── types.py                ✅ ~412 lines
│   ├── events.py               ✅ ~298 lines
│   ├── config.py               ✅ ~341 lines
│   ├── calendar.py             ✅ ~387 lines
│   ├── game_state.py           ✅ ~1,100 lines
│   └── persistence.py          ✅ ~650 lines
├── entities/                   # Game objects
│   ├── __init__.py
│   ├── fighter.py              ✅ ~498 lines
│   ├── camp.py                 ✅ ~456 lines
│   ├── promotion.py            ✅ ~521 lines
│   └── contract.py             ✅ ~467 lines
├── systems/                    # Game mechanics
│   ├── __init__.py
│   ├── aging.py                ✅ ~420 lines
│   ├── training.py             ✅ ~480 lines
│   ├── injury.py               ✅ ~380 lines
│   ├── matchmaking.py          ✅ ~520 lines
│   ├── rankings.py             ✅ ~450 lines
│   └── economy.py              ✅ ~850 lines
├── simulation/                 # Fight & world simulation
│   ├── __init__.py
│   ├── fight_engine.py         ✅ ~1,857 lines
│   ├── fight_integration.py    ✅ ~999 lines
│   ├── generator.py            ✅ ~1,225 lines
│   └── world.py                ✅ ~1,255 lines
├── narrative/                  # Story generation
│   ├── __init__.py
│   ├── rivalry.py              ✅ ~996 lines
│   └── commentary.py           ✅ ~1,608 lines
├── interface/                  # Player UI
│   ├── __init__.py
│   └── cli.py                  ✅ ~1,918 lines
├── data/                       # Static data files
│   └── name_database.py        ✅ ~800 lines
├── saves/                      # Save game files
└── logs/                       # Debug logs
```

---

## COMPLETED MODULES

### Phase 1: Core Foundation ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 1 | core/types.py | ~412 | 40 | Enums, constants, data classes |
| 2 | core/events.py | ~298 | 27 | Event bus for system communication |
| 3 | core/config.py | ~341 | 33 | Game configuration management |
| 4 | core/calendar.py | ~387 | 49 | Time & date system |

### Phase 2: Entity Layer ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 5 | entities/fighter.py | ~498 | 43 | Fighter attributes, records, status |
| 6 | entities/camp.py | ~456 | 43 | Training camp management |
| 7 | entities/promotion.py | ~521 | 39 | DFC promotion entity |
| 8 | entities/contract.py | ~467 | 39 | Fighter contracts |

### Phase 3: World Systems ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 9 | systems/aging.py | ~420 | 35 | Fighter aging & degradation |
| 10 | systems/training.py | ~480 | 38 | Training camps & improvement |
| 11 | systems/injury.py | ~380 | 32 | Injury types & recovery |
| 12 | systems/matchmaking.py | ~520 | 36 | Fight matchmaking algorithms |
| 13 | systems/rankings.py | ~450 | 34 | Division rankings system |

### Phase 4: Fight Simulation ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 14 | simulation/fight_engine.py | ~1,857 | 63 | Core fight simulation (35+ positions, 30+ strikes, 25+ submissions) |
| 15 | narrative/commentary.py | ~1,608 | 50 | Round-by-round commentary with 30+ template dictionaries |
| 16 | simulation/fight_integration.py | ~999 | 35 | NarratedFightSimulator combining engine + commentary |
| 17 | simulation/generator.py | ~1,225 | 47 | Fighter generation with cultural traits |

### Phase 5: Economy ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 18 | systems/economy.py | ~850 | 52 | Fight purses, camp finances, transactions |

### Phase 6: Narrative Engine (Partial) ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 22 | narrative/rivalry.py | ~996 | 48 | 8 rivalry types, intensity tracking, decay |

### Phase 7: World Simulation ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 30 | simulation/world.py | ~1,255 | 55 | AI camp personalities, world time management |

### Phase 8: Game State & Persistence ✅ COMPLETE
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 33 | core/game_state.py | ~1,100 | 51 | Central game coordination |
| 34 | core/persistence.py | ~650 | 45 | Save/load system with slots & backups |

### Phase 9: Interface ✅ COMPLETE (Core Features)
| Module | File | Lines | Tests | Description |
|--------|------|-------|-------|-------------|
| 35 | interface/cli.py | ~1,918 | 58 | Text interface with menus |

### Data Files ✅ COMPLETE
| File | Lines | Description |
|------|-------|-------------|
| data/name_database.py | ~800 | 17+ countries, cultural fighting styles |

---

## CURRENT STATISTICS

```
Total Lines of Code:    ~19,500+
Total Tests:            ~1,004+
Test Status:            ALL PASSING ✅
Modules Complete:       24+ of 36 planned
```

---

## WHAT'S WORKING NOW

### World Generation ✅
- Creates 150-200 fighters across 9 weight classes
- Generates 25 AI camps with personalities
- Simulates 2-3 years of fight history at game start
- Establishes champions and rankings

### CLI Features ✅
- **Hub Menu**: Central navigation with 8 options
- **My Camp**: View camp details and finances
- **My Fighters**: Browse signed fighters with details
- **Rankings**: Browse all 9 divisions with rankings
- **Browse Fighters**: Search/filter free agents
- **Browse Camps**: View all camps in the world
- **History & Records**: The Archives menu
  - G.O.A.T. Rankings (all-time greats scoring)
  - Record Book (global statistics)
  - Record Book by Division
  - Champions History
- **Save/Load**: Full persistence with backup system
- **ANSI Colors**: Colored output for champions, wins/losses

### Fight Engine ✅
- 35+ fighting positions
- 30+ strike types
- 25+ submission types
- Body part damage tracking
- Intelligent action selection
- Full round-by-round simulation

---

## WHAT'S MISSING (Gameplay Loop)

### Critical Missing Features ⚠️

The modules exist but are **NOT INTEGRATED** into the CLI gameplay loop:

1. **Training Menu** ❌
   - `systems/training.py` exists but no CLI menu
   - Players can't train fighters between fights
   - No attribute improvement gameplay

2. **Fight Booking/Matchmaking** ❌
   - `systems/matchmaking.py` exists but no CLI integration
   - No fight offers system
   - Can't accept/decline matchups
   - Can't schedule fights

3. **Week Advancement Events** ❌
   - Advancing weeks does nothing meaningful
   - Scheduled fights don't execute
   - No injuries, offers, or results during advancement
   - No news feed showing what happened

4. **Fight Execution** ❌
   - `simulation/fight_integration.py` exists
   - But fights never actually happen in gameplay
   - No way to trigger or watch fights

---

## CURRENT TODO LIST

### Immediate Priority: Playable Game Loop

These need to be built/integrated to make the game playable:

1. **[ ] Fight Offers System**
   - Generate fight offers for player's fighters
   - Accept/decline matchups
   - Schedule fights with dates

2. **[ ] Training Menu Integration**
   - Add training option to My Fighters menu
   - Select training focus
   - Track training progress

3. **[ ] Week Advancement with Events**
   - Execute scheduled fights
   - Update fighter records
   - Process injuries
   - Generate news headlines

4. **[ ] News Feed System**
   - Show fight results
   - Display injuries, retirements
   - "Text is the graphics" - critical for immersion

### Secondary Priority

5. **[ ] Economy Integration**
   - Fight purses after wins
   - Camp expenses during advancement
   - Contract negotiations

6. **[ ] Contract System Integration**
   - Contract expiration
   - Free agent signing
   - Renewal negotiations

### Future Enhancements (Post-Core)

- [ ] Amateur Tournament System (designed, deferred)
- [ ] Hall of Fame System
- [ ] Press Conference Generator
- [ ] Legacy & Protégé System
- [ ] Personality System

---

## DEVELOPMENT RULES

### Code Delivery Standards

1. **Complete Modules Only**: Every module delivered must be fully functional and tested
2. **Line Count Reporting**: Each code delivery includes total lines
3. **Paste-and-Replace Preferred**: Full file replacements for clarity
4. **Terminal Commands**: Provided when file operations are needed

### Code Quality Standards

- **Type Hints**: All functions use Python type hints
- **Docstrings**: Every class and public method documented
- **No Circular Imports**: Strict dependency hierarchy
- **Event-Driven**: Systems communicate through the event bus
- **Testable**: Each module includes corresponding tests

---

## DESIGN DECISIONS LOG

### Decided ✅
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data Format | JSON | Simpler debugging, human-readable saves |
| Architecture | Event-driven | Loose coupling, emergent behavior |
| UI | Text-based CLI | Focus on simulation depth first |
| Time Scale | Weekly ticks | Balance between detail and pacing |
| Promotion | Single (DFC) | Simpler to start, can add tiers later |
| Promotion Name | Dynasty Fighting Championship | User selected |
| Amateur System | Deferred to post-core | Build after fight sim works |
| GOAT Scoring | Wins×10 - Losses×5 + Finishes×5 + Champion bonus | Implemented |

### Pending Discussion
- Training camp duration and effects (8 weeks standard)
- Fight offer frequency
- News headline variety
- Economic balance (purses vs expenses)

---

## REFERENCE MATERIALS

### Weight Classes
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

### Key Configuration Values
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

# Camp Tiers
GARAGE -> LOCAL -> REGIONAL -> NATIONAL -> ELITE

# Fight Rounds
Standard: 3 rounds
Championship: 5 rounds
```

---

## SESSION WORKFLOW

1. **Request**: Ask for the next feature/fix
2. **Receive**: Get complete code with line counts
3. **Download**: Get files from provided links
4. **Place**: Put files in correct locations
5. **Test**: Run `python3 -m pytest tests/test_[module].py -v`
6. **Verify**: Run all tests `python3 -m pytest tests/ -v`
7. **Confirm**: Report success before moving to next item

---

## NOTES FOR CLAUDE

- Van uses Mac with `python3` command
- Project path: `~/Desktop/Games/cage_dynasty/`
- Prefer paste-and-replace over incremental edits
- Always report line counts
- Provide downloadable file links
- Update TODO list as items are completed
- Flag any design decisions that need Van's input
- DFC = Dynasty Fighting Championship (single promotion model)
- All modules exist but gameplay loop needs integration
- Priority is making the game PLAYABLE, not adding more systems

---

## TRANSCRIPT REFERENCES

For detailed implementation history, see transcripts in `/mnt/transcripts/`:
- `2025-11-28-08-48-14-cage-dynasty-module-1-2-setup.txt` - Initial setup
- `2025-11-28-19-32-54-cage-dynasty-modules-5-6-promotion-naming.txt` - Fighter/Camp entities
- `2025-11-28-19-48-04-cage-dynasty-modules-9-10-aging-training.txt` - Aging/Training systems
- `2025-11-28-20-24-15-cage-dynasty-modules-11-12-injury-matchmaking.txt` - Injury/Matchmaking
- `2025-11-28-21-24-31-module-14-fight-engine-implementation.txt` - Fight engine
- `2025-11-28-21-51-38-module-15-commentary-system-rebuild.txt` - Commentary
- `2025-11-28-22-08-11-module-16-fight-integration-complete.txt` - Fight integration
- `2025-11-28-22-40-35-module-17-fighter-generator-complete.txt` - Generator
- `2025-11-29-00-06-03-module-22-rivalry-system-complete.txt` - Rivalry system
- `2025-11-29-00-39-04-module-30-33-world-sim-game-state.txt` - World sim & game state
- `2025-11-29-03-05-04-module-35-cli-world-init-integration.txt` - CLI & world init
- `2025-11-29-03-30-50-module-35-goat-rankings-record-book.txt` - GOAT rankings & records

---

*Last Updated: November 29, 2025*
*Current Focus: Integrating gameplay loop (training, matchmaking, fight execution)*
*Tests: ~1,004+ passing*
