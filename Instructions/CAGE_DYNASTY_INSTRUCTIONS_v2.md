# CAGE DYNASTY - Project Instructions & Development Guide
# Updated: Session in Progress
# Status: 313 Tests Passing | 3,380 Lines of Code

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

# Run the game (when ready)
python3 main.py
```

### Current Folder Structure
```
~/Desktop/Games/cage_dynasty/
├── main.py                 # Game entry point (TODO)
├── tests/                  # All test files
│   ├── __init__.py
│   ├── test_types.py       ✅ 40 tests
│   ├── test_events.py      ✅ 27 tests
│   ├── test_config.py      ✅ 33 tests
│   ├── test_calendar.py    ✅ 49 tests
│   ├── test_fighter.py     ✅ 43 tests
│   ├── test_camp.py        ✅ 43 tests
│   ├── test_promotion.py   ✅ 39 tests
│   └── test_contract.py    ✅ 39 tests
├── core/                   # Foundation modules
│   ├── __init__.py
│   ├── types.py            ✅ 412 lines
│   ├── events.py           ✅ 298 lines
│   ├── config.py           ✅ 341 lines
│   └── calendar.py         ✅ 387 lines
├── entities/               # Game objects
│   ├── __init__.py
│   ├── fighter.py          ✅ 498 lines
│   ├── camp.py             ✅ 456 lines
│   ├── promotion.py        ✅ 521 lines
│   └── contract.py         ✅ 467 lines
├── systems/                # Game mechanics (IN PROGRESS)
│   ├── __init__.py
│   ├── aging.py            ⬜ Next up
│   ├── training.py         ⬜ Pending
│   ├── injury.py           ⬜ Pending
│   ├── matchmaking.py      ⬜ Pending
│   └── rankings.py         ⬜ Pending
├── simulation/             # Fight & world simulation
│   ├── __init__.py
│   ├── fight_engine.py     ⬜ Pending
│   └── generator.py        ⬜ Pending
├── narrative/              # Story generation
│   ├── __init__.py
│   ├── rivalry.py          ⬜ Pending
│   └── commentary.py       ⬜ Pending
├── data/                   # Static data files
├── saves/                  # Save game files
└── logs/                   # Debug logs
```

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

## MODULE DEVELOPMENT ORDER

### Phase 1: Core Foundation ✅ COMPLETE
- [x] Module 1: Core Data Types (`core/types.py`) - 412 lines, 40 tests
- [x] Module 2: Event Bus System (`core/events.py`) - 298 lines, 27 tests
- [x] Module 3: Configuration Manager (`core/config.py`) - 341 lines, 33 tests
- [x] Module 4: Time & Calendar System (`core/calendar.py`) - 387 lines, 49 tests

### Phase 2: Entity Layer ✅ COMPLETE
- [x] Module 5: Fighter Entity (`entities/fighter.py`) - 498 lines, 43 tests
- [x] Module 6: Camp Entity (`entities/camp.py`) - 456 lines, 43 tests
- [x] Module 7: Promotion Entity (`entities/promotion.py`) - 521 lines, 39 tests
- [x] Module 8: Contract System (`entities/contract.py`) - 467 lines, 39 tests

### Phase 3: World Systems ⬜ IN PROGRESS
- [ ] Module 9: Aging & Degradation (`systems/aging.py`)
- [ ] Module 10: Training System (`systems/training.py`)
- [ ] Module 11: Injury System (`systems/injury.py`)
- [ ] Module 12: Matchmaking Engine (`systems/matchmaking.py`)
- [ ] Module 13: Rankings System (`systems/rankings.py`)

### Phase 4: Fight Simulation ⬜ PENDING
- [ ] Module 14: Fight Engine Core (`simulation/fight_engine.py`)
- [ ] Module 15: Round-by-Round Simulation (`simulation/rounds.py`)
- [ ] Module 16: Fight Outcomes & Statistics (`simulation/outcomes.py`)
- [ ] Module 17: Judge Scoring (`simulation/judging.py`)

### Phase 5: Economy ⬜ PENDING
- [ ] Module 18: Financial Core (`systems/economy.py`)
- [ ] Module 19: Contract Negotiation (`systems/negotiation.py`)
- [ ] Module 20: Sponsorship System (`systems/sponsorship.py`)
- [ ] Module 21: Event Revenue (`systems/revenue.py`)

### Phase 6: Narrative Engine ⬜ PENDING
- [ ] Module 22: Personality System (`narrative/personality.py`)
- [ ] Module 23: Rivalry Detection (`narrative/rivalry.py`)
- [ ] Module 24: Legacy & Protégé System (`narrative/legacy.py`)
- [ ] Module 25: Commentary Generator (`narrative/commentary.py`)
- [ ] Module 26: Press Conference Generator (`narrative/press.py`)

### Phase 7: History & Analytics ⬜ PENDING
- [ ] Module 27: Statistics Tracker (`systems/statistics.py`)
- [ ] Module 28: Record Books (`systems/records.py`)
- [ ] Module 29: Hall of Fame (`systems/hall_of_fame.py`)

### Phase 8: World Simulation ⬜ PENDING
- [ ] Module 30: Fighter Generator (`simulation/generator.py`)
- [ ] Module 31: Camp AI (`simulation/camp_ai.py`)
- [ ] Module 32: World Simulation Loop (`simulation/world.py`)

### Phase 9: Interface & Polish ⬜ PENDING
- [ ] Module 33: Game State Manager (`core/game_state.py`)
- [ ] Module 34: Save/Load System (`core/persistence.py`)
- [ ] Module 35: Command Interface (`interface/cli.py`)
- [ ] Module 36: Main Game Loop (`main.py`)

---

## CURRENT PROGRESS

### Statistics
- **Total Lines of Code**: 3,380
- **Total Tests**: 313
- **Test Status**: ALL PASSING ✅
- **Modules Complete**: 8 of 36

### What's Built

| Layer | Components | Status |
|-------|------------|--------|
| **Core** | Types, Events, Config, Calendar | ✅ Complete |
| **Entities** | Fighter, Camp, Promotion (DFC), Contract | ✅ Complete |
| **Systems** | Aging, Training, Injury, Matchmaking, Rankings | ⬜ Next |
| **Simulation** | Fight Engine, Generator | ⬜ Pending |
| **Narrative** | Rivalry, Commentary | ⬜ Pending |
| **Interface** | CLI, Save/Load | ⬜ Pending |

---

## CURRENT TODO LIST

### Immediate (This Session)
- [ ] Module 9: Aging & Degradation System
- [ ] Module 10: Training System
- [ ] Module 11: Injury System

### Next Up
- [ ] Module 12: Matchmaking Engine
- [ ] Module 13: Rankings System
- [ ] Begin Phase 4: Fight Simulation

### Backlog
- [ ] Fight engine and round simulation
- [ ] Economy and financial systems
- [ ] Narrative/rivalry systems
- [ ] Fighter generator
- [ ] Main game loop and CLI

---

## DESIGN DECISIONS LOG

### Decided
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data Format | JSON | Simpler debugging, human-readable saves |
| Architecture | Event-driven | Loose coupling, emergent behavior |
| UI | Text-based CLI | Focus on simulation depth first |
| Time Scale | Weekly ticks | Balance between detail and pacing |
| Promotion | Single (DFC) | Simpler to start, can add tiers later |
| Promotion Name | Dynasty Fighting Championship | User selected |

### Pending Discussion
- Fighter generation probability distributions
- Exact aging curve parameters
- Training camp duration and effects
- Rivalry threshold values

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

### Key Configuration Values (from config.py)
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

1. **Request**: Ask for the next module
2. **Receive**: Get complete code with line counts
3. **Download**: Get files from provided links
4. **Place**: Put files in correct locations
5. **Test**: Run `python3 -m pytest tests/test_[module].py -v`
6. **Verify**: Run all tests `python3 -m pytest tests/ -v`
7. **Confirm**: Report success before moving to next module

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

---

*Last Updated: Phase 2 Complete*
*Current Module: Ready for Module 9 (Aging System)*
*Tests: 313 passing*
