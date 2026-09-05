"""P3-4b — WINDOW MECHANISM registry (Stage 1 restatement).

Restates fi's existing style-mechanic sites as rows through one
common dispatch path. This module is DOCUMENTARY + DISPATCH:

  - WINDOW_TABLE lists every recognised window as a WindowSpec row
    (name, trigger, duration, effect, commentary hook).
  - dispatch_window_event() is a single logging hook fi.py calls at
    each window trigger/consume site. When WINDOWS_LOG_ENABLED is
    False (default) the hook is a no-op — byte-equivalence gate for
    Stage 1 holds trivially: adding a call to a no-op function does
    not perturb the RNG stream.
  - When WINDOWS_LOG_ENABLED is True the hook appends to a per-
    simulator buffer that the sample-fight-log report in Stage 5
    reads.

Stage 2 additions (each togglable):
  - FI_CUT_WRITER_ENABLED: elbow-to-head cut writer + between-round
    cut-doctor check, ported verbatim from fe. Default False —
    OFF-state byte-identical to Stage 1.
  - FI_SPRAWL_PUNISH_ENABLED: strike-attack scaler while
    _sprawl_counter live. Consumer for a state flag that had none.
    Default False — OFF-state byte-identical to Stage 1.

Heat is param-driven (fi.simulate_narrated_fight gains heat_level);
level=0 default is byte-inert per the tiered branches (all >20/>40/
>60/>80 checks fail).

Line numbers in this file's docstrings are current-HEAD; identifier
names are the primary key (line numbers drift).
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional


# ── Stage 1: dispatch toggle (default OFF for byte-identity) ────
WINDOWS_LOG_ENABLED: bool = False

# ── Stage 2: per-piece toggles ──────────────────────────────────
FI_CUT_WRITER_ENABLED: bool = False
FI_SPRAWL_PUNISH_ENABLED: bool = False

# ── P3-4c: chin + composure wiring toggles.
# C22: FLIPPED ON. Van-approved with C22 paste based on verify.md
# T4 sensitivity readings (kd_mean -18% relative for CHIN;
# mean rock_duration -32% relative for COMPOSURE at N=1000/cell,
# seed block 981000+, positive controls proven-discriminating).
# HEART wiring is not gated (was always alive — direct read at
# fe:3522/3536 with no flag). §5a submission model is a
# REPLACEMENT (no toggle) — old renamed
# _legacy_process_submission_progress and preserved on disk;
# the entry point uses the new logic.
FI_CHIN_WIRING_ENABLED: bool = True
FI_COMPOSURE_WIRING_ENABLED: bool = True

# ── P3-4d: POWER wiring toggle.
# C23: FLIPPED ON. Van-approved with C23 paste based on G2
# separability reading (POWER+20 → KO+TKO +3.0pp ±2.4pp ALIVE;
# STRENGTH+20 → KO+TKO +0.1pp FLAT; positive controls proven-
# discriminating at N=1000/cell, seed base 983000). Per C22 rule (a):
# no wiring-flag flips without a defining-instrument sensitivity
# reading in a prior verify pass.
# When ON, strike-damage lanes at fe:2833/2837 and the flash-KO
# branch at fi:1328 read attacker.power instead of attacker.strength.
# Strength keeps grappling-physicality (throws/slams/clinch break/
# escape assist).
FI_POWER_WIRING_ENABLED: bool = True

# ── P3-4e: AGGRESSION rules table + IQ execution lane.
# Default OFF for byte-identity no-op gate G1. When ON:
#  - FI_AGGRESSION_RULES_ENABLED: 4-rule circumstance table adjusts
#    aggression mid-fight (R1 behind on cards → up, R2 chin vs power
#    → down, R3 opponent gassed → up, R4 cruising with lead → coast).
#  - FI_IQ_EXECUTION_ENABLED: plan adherence — low-IQ fighters drift
#    toward tendency when rocked/dropped; high-IQ fighters stick.
# Van decision post-G2/G3 verify.
FI_AGGRESSION_RULES_ENABLED: bool = False
FI_IQ_EXECUTION_ENABLED: bool = False

# ── STYLECOHERENCE1 (P5-B2, 2026-09-05): world-gen style-based
# attribute bonuses. Pre-P5-B2 these blocks read
# `getattr(fighter, 'fighting_style', ...)` on a GeneratedFighter
# whose attribute is `.style` — the read returned '' and the
# bonus never applied (BF-1 finding). P5-B2 fixes the attribute
# read but leaves the behavior BEHIND FLAGS so styles becoming
# real doesn't silently activate world-gen attribute biases
# alongside AI-plan coherence. Van rule (a) — no wiring-flag flips
# without a defining-instrument sensitivity reading in a prior
# verify pass.
#
# When ON:
#  - STYLE_CLINCH_BONUS_ENABLED: world_init:3136 (was 3128 pre-D18)
#    applies +8/+6/+6/+5/+4/+4 to clinch_control for Clinch
#    Fighter / Muay Thai / Judo / Sambo / Wrestler / Pressure
#    Fighter respectively.
#  - STYLE_TDD_BONUS_ENABLED: world_init:3150 (was 3142 pre-D18)
#    applies +6/+4/+3 to takedown_defense for Muay Thai / Sprawl
#    & Brawl / Karate respectively. [P5-B1 filing labeled this
#    "training modifier" — corrected here: the code is a TDD
#    bonus at world-gen, not a training modifier.]
STYLE_CLINCH_BONUS_ENABLED: bool = False
STYLE_TDD_BONUS_ENABLED: bool = False

# ── Stage 2c constants ──────────────────────────────────────────
SPRAWL_PUNISH_DAMAGE_MULT: float = 1.25  # P3-5 calibrates

# ── Stage 2a constants (from fe:3625-3634, fe:4422-4434) ────────
CUT_ELBOW_STRIKE_VALUES = frozenset({
    "elbow_horizontal", "elbow_vertical",
    "elbow_spinning", "elbow_upward",
    "gnp_elbow", "clinch_elbow",
})
CUT_BASE_CHANCE: float = 0.25       # per-strike prior
CUT_STRENGTH_DIVISOR: float = 400.0  # + attacker.strength / divisor
CUT_DOCTOR_STOP_STEP: float = 0.08   # per cut above (threshold-1)
CUT_DOCTOR_STOP_MAX: float = 0.35
CUT_DOCTOR_HEART_DIVISOR: float = 200.0
CUT_DOCTOR_HEART_FLOOR: float = 0.4


@dataclass
class WindowSpec:
    """One row of the registry."""
    name: str
    trigger_summary: str
    duration: str
    effect_summary: str
    rng_draws_on_write: int
    rng_draws_on_consume: int
    write_site: str           # symbol path, e.g. "fight_integration._execute_grappling"
    consume_site: str
    commentary_hook: str      # dispatch event name, or "" if silent
    new_in_p3_4b: bool = False


# Registry rows — one per mechanic. Order matches the census
# document under outputs/sm1/fight_model/p3_4b/census.md.
WINDOW_TABLE: List[WindowSpec] = [
    # ── EXISTING (Stage 1 restatement, zero behavior change) ──
    WindowSpec(
        name="karate_patience",
        trigger_summary="actor style KARATE and strikes_landed==0 this round",
        duration="one head strike",
        effect_summary="damage *= 1.40 on next landed head strike",
        rng_draws_on_write=0, rng_draws_on_consume=0,
        write_site="fight_engine.select_action (~:2148-2156)",
        consume_site="fight_integration._execute_strike (~:948-953)",
        commentary_hook="karate_patience_land",
    ),
    WindowSpec(
        name="point_fighter_movement",
        trigger_summary="attacker style contains POINT (write on landed strike)",
        duration="2 exchanges post-set",
        effect_summary="incoming damage *= 0.80 on defender for the window",
        rng_draws_on_write=0, rng_draws_on_consume=0,
        write_site="fight_integration._execute_strike (~:981-986)",
        consume_site="fight_integration._execute_strike (~:955-960)",
        commentary_hook="point_fighter_slip",
    ),
    WindowSpec(
        name="brawler_walkthrough",
        trigger_summary="landed head strike vs defender style contains BRAWLER; chin-tiered chance",
        duration="until next strike attempt",
        effect_summary="damage in ×0.75; arm counter ∈ {1.2, 1.3, 1.4}× on return shot",
        rng_draws_on_write=1, rng_draws_on_consume=0,
        write_site="fight_integration._execute_strike (~:962-979)",
        consume_site="fight_integration._execute_strike (~:850-856 + ~:944-946)",
        commentary_hook="brawler_walkthrough",
    ),
    WindowSpec(
        name="counter_striker",
        trigger_summary="MISS vs defender: style COUNTER (always) or IQ-tiered chance",
        duration="one exchange",
        effect_summary="damage *= (IQ-tiered mult × speed-tiered mod) on return",
        rng_draws_on_write=1,  # only when style != 'COUNTER'
        rng_draws_on_consume=0,
        write_site="fight_integration._execute_strike (~:875-889)",
        consume_site="fight_integration._execute_strike (~:832-848)",
        commentary_hook="counter_strike",
    ),
    WindowSpec(
        name="adrenaline_surge",
        trigger_summary="fighter's is_rocked clears; 12% chance",
        duration="3 exchanges",
        effect_summary="momentum +30 on write; decays to 50 floor on expire",
        rng_draws_on_write=1,  # gated behind rock clear
        rng_draws_on_consume=0,
        write_site="fight_integration._simulate_exchange (~:1720-1740)",
        consume_site="fight_integration._execute_strike (~:818-822)",
        commentary_hook="adrenaline_surge",
    ),
    WindowSpec(
        name="sambo_chain",
        trigger_summary="successful sambo TD to dominant position + submissions>=65; TD/IQ-tiered chance",
        duration="single exchange (immediate next actor turn)",
        effect_summary="force action_type='submission' with pos-appropriate SubmissionType",
        rng_draws_on_write=1, rng_draws_on_consume=0,
        write_site="fight_integration._execute_grappling (~:1428-1439)",
        consume_site="fight_integration._simulate_exchange (~:767-783)",
        commentary_hook="sambo_chain",
    ),
    WindowSpec(
        name="sprawl_counter_momentum",
        trigger_summary="defender style SPRAWL stuffs a single/double leg",
        duration="2 exchanges post-set",
        effect_summary="attacker momentum +20 per exchange while live (MOMENTUM-ONLY today)",
        rng_draws_on_write=0, rng_draws_on_consume=0,
        write_site="fight_integration._execute_grappling (~:1444-1451)",
        consume_site="fight_integration._execute_strike (~:824-830)",
        commentary_hook="sprawl_counter",
    ),

    # ── STAGE 2 additions (each behind its own toggle) ──
    WindowSpec(
        name="elbow_cut_writer",
        trigger_summary="landed head strike ∈ CUT_ELBOW_STRIKE_VALUES (Stage 2a)",
        duration="single strike",
        effect_summary="defender_state.damage.cuts += 1 with p = 0.25 + str/400",
        rng_draws_on_write=1, rng_draws_on_consume=0,
        write_site="fight_integration._execute_strike (Stage 2a: new)",
        consume_site="fight_integration._between_round_stoppages (Stage 2a: new)",
        commentary_hook="elbow_cut",
        new_in_p3_4b=True,
    ),
    WindowSpec(
        name="doctor_cut_stoppage",
        trigger_summary="between-round + damage.cuts >= config.doctor_check_cut_threshold (Stage 2a)",
        duration="one between-round check",
        effect_summary="TKO (Doctor Stoppage - Cuts) with p = min(0.35, (cuts-thr+1)*0.08) * heart_scaler",
        rng_draws_on_write=1, rng_draws_on_consume=0,
        write_site="fight_integration._simulate_round (between-round block; new)",
        consume_site="(same site, fires stoppage inline)",
        commentary_hook="doctor_cut_stoppage",
        new_in_p3_4b=True,
    ),
    WindowSpec(
        name="sprawl_punish_attack",
        trigger_summary="attacker._sprawl_counter live AND strike landed (Stage 2c NEW consumer)",
        duration="up to 2 exchanges (piggybacks _sprawl_counter)",
        effect_summary="damage *= SPRAWL_PUNISH_DAMAGE_MULT (1.25 provisional; P3-5 calibrates)",
        rng_draws_on_write=0, rng_draws_on_consume=0,
        write_site="(reuses existing sprawl_counter write at ~:1444-1451)",
        consume_site="fight_integration._execute_strike (Stage 2c: new)",
        commentary_hook="sprawl_punish",
        new_in_p3_4b=True,
    ),
]


def dispatch_window_event(sim, name: str, phase: str,
                          actor_name: Optional[str] = None,
                          target_name: Optional[str] = None,
                          exchange_num: Optional[int] = None,
                          extra: Optional[dict] = None) -> None:
    """Single dispatch path for every window event.

    fi.py calls this at each window trigger/consume site with the
    window's registry name and phase ∈ {"write", "consume",
    "decrement", "expire", "fire"}. When WINDOWS_LOG_ENABLED is
    False (default) this returns immediately — no RNG, no state
    mutation, byte-equivalence preserved. When True, appends the
    event to sim._window_events (a list on the simulator instance;
    created lazily). Stage 5 also emits to commentary if the
    simulator's commentary object has log_window_event().
    """
    if not WINDOWS_LOG_ENABLED:
        return
    ev = {"name": name, "phase": phase}
    if actor_name is not None: ev["actor"] = actor_name
    if target_name is not None: ev["target"] = target_name
    if exchange_num is not None: ev["exchange"] = exchange_num
    if extra: ev["extra"] = extra
    if not hasattr(sim, "_window_events"):
        sim._window_events = []
    sim._window_events.append(ev)
    _cmt = getattr(sim, "commentary", None)
    _hook = getattr(_cmt, "log_window_event", None)
    if callable(_hook):
        try: _hook(name=name, phase=phase, actor=actor_name,
                   target=target_name, exchange_num=exchange_num,
                   extra=extra)
        except Exception: pass
