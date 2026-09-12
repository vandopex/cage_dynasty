#!/usr/bin/env python3
"""WEEK-AXIS1 (c) PREDICATE discrimination probe.

Builds a bridge via new_game + advance_week, then renders
fighter_profile.html via Flask's test_client for selected fighters and
cross-references every rendered badge against the reign windows carried
by get_fighter_reigns. Optional --against <git-ref> writes that ref's
copy of fighter_profile.html over the live path, renders the SAME
context, and prints NEW-vs-ref badge counts plus differing rows.

Why this exists: the R03 harness reads reign dicts and fight-history
rows straight out of the dump (BeltHistory.to_dict + FighterRecord.
fight_history). Neither passes through _convert_real_fighter — that's
the bridge → WebFighter converter on the render path, which cherry-
picks 8 of ~12 keys (ROW-SCHEMA1). Any template change that reads
fields the converter drops will pass the harness and render nothing.
This probe catches that class of bug; the harness cannot.

Usage:
  claude/tools/render_probe.py                        # all fighters, no comparator
  claude/tools/render_probe.py --against HEAD~2       # discrimination vs earlier ref
  claude/tools/render_probe.py --fighter-select founding
  claude/tools/render_probe.py --fighter-id <fid>

Exit non-zero on:
  - template restore hash mismatch (loud message)
  - probe error (bridge build failure, missing fighter under --fighter-id)
"""
import argparse
import hashlib
import os
import random
import re
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

# _harness_env sits alongside this file; use dirname(__file__) so CWD
# doesn't matter (save_invariants uses a bare 'claude/tools' insert
# which requires CWD == repo root).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness_env  # noqa: F401  — side-effect: sys.path + chdir

WEB = _harness_env._WEB
REPO = _harness_env._REPO
LIVE_TPL = os.path.join(WEB, 'templates', 'fighter_profile.html')


# ─────────────────────────────────────────────────────────────────────
# BRIDGE BUILD (mirrors save_invariants.load_from_seed)
# ─────────────────────────────────────────────────────────────────────
def build_bridge(seed: int, weeks: int):
    random.seed(seed)
    from game_bridge import GameBridge
    from game_start import generate_starting_prospects

    prospects = generate_starting_prospects(player_region="Americas")
    p = prospects[0]
    fighter_dict = {
        "id": p.prospect_id, "name": p.name,
        "nickname": getattr(p, "nickname", None),
        "age": p.age, "country": p.country,
        "weight_class": p.weight_class, "style": p.fighting_style,
        "overall": p.overall_rating, "potential": p.potential_ceiling,
        "traits": getattr(p, "traits", []),
        "strength": p.strength, "speed": p.speed, "cardio": p.cardio,
        "chin": p.chin, "recovery": p.recovery,
        "boxing": p.boxing, "kicks": p.kicks,
        "clinch_striking": p.clinch_striking,
        "striking_defense": p.striking_defense,
        "takedowns": p.takedowns, "takedown_defense": p.takedown_defense,
        "top_control": p.top_control, "submissions": p.submissions,
        "guard": p.guard, "clinch_control": p.clinch_control,
        "heart": p.heart, "fight_iq": p.fight_iq,
        "composure": p.composure,
    }
    coach_dict = {"id": "coach_1", "name": "Test Coach",
                  "specialty": "boxing", "rating": 65,
                  "traits": [], "cost": 500}

    b = GameBridge()
    b._user_id = f"render_probe_seed{seed}"
    b.new_game("Render Probe Camp", "Las Vegas, NV",
               "GARAGE", coach_dict, fighter_dict)
    for _ in range(int(weeks)):
        b.advance_week()
    return b


# ─────────────────────────────────────────────────────────────────────
# FIGHTER SELECTION
# ─────────────────────────────────────────────────────────────────────
def is_founding(reigns: List[Dict[str, Any]]) -> bool:
    return any('Founding' in (r.get('won_event') or '') for r in reigns)


def is_defended(reigns: List[Dict[str, Any]]) -> bool:
    return any((r.get('successful_defenses') or 0) >= 1
               and 'Founding' not in (r.get('won_event') or '')
               for r in reigns)


def is_multi_reign(reigns: List[Dict[str, Any]]) -> bool:
    return len(reigns) >= 2


def select_fighters(bridge, mode: str) -> List[Tuple[str, Any, List[Dict]]]:
    """Return [(fid, WebFighter-ish record, reigns)] matching mode."""
    out = []
    for fid, fr in bridge._game_state.fighters.items():
        reigns = bridge.get_fighter_reigns(fid)
        if not reigns:
            continue
        if mode == 'all':
            out.append((fid, fr, reigns))
        elif mode == 'founding' and is_founding(reigns):
            out.append((fid, fr, reigns))
        elif mode == 'defended' and is_defended(reigns):
            out.append((fid, fr, reigns))
        elif mode == 'multi-reign' and is_multi_reign(reigns):
            out.append((fid, fr, reigns))
    return out


# ─────────────────────────────────────────────────────────────────────
# TEMPLATE SWAP (SAFE, sha-checked)
# ─────────────────────────────────────────────────────────────────────
def _sha256_of(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


class TemplateSwap:
    """Context manager: write ref's fighter_profile.html over the live
    path on __enter__; restore + sha-check on __exit__. Loud abort
    when restored hash differs from pre-swap hash."""

    def __init__(self, ref: Optional[str]):
        self.ref = ref
        self.pre_sha: Optional[str] = None
        self.backup: Optional[str] = None

    def __enter__(self):
        if self.ref is None:
            return self
        self.pre_sha = _sha256_of(LIVE_TPL)
        with open(LIVE_TPL, 'r') as f:
            self.backup = f.read()
        r = subprocess.run(
            ['git', 'show', f'{self.ref}:cage_dynasty_web/templates/fighter_profile.html'],
            capture_output=True, text=True, cwd=REPO,
        )
        if r.returncode != 0:
            raise RuntimeError(
                f"render_probe: git show {self.ref}:cage_dynasty_web/"
                f"templates/fighter_profile.html failed:\n{r.stderr}"
            )
        with open(LIVE_TPL, 'w') as f:
            f.write(r.stdout)
        return self

    def __exit__(self, *exc):
        if self.ref is None or self.backup is None:
            return False
        with open(LIVE_TPL, 'w') as f:
            f.write(self.backup)
        post_sha = _sha256_of(LIVE_TPL)
        if post_sha != self.pre_sha:
            sys.stderr.write(
                "\n\n"
                "*** render_probe: LIVE TEMPLATE HASH MISMATCH AFTER RESTORE ***\n"
                f"    pre_sha  = {self.pre_sha}\n"
                f"    post_sha = {post_sha}\n"
                f"    path     = {LIVE_TPL}\n"
                "    The template swap failed to restore correctly; the working\n"
                "    tree is now in an unexpected state. Investigate before\n"
                "    running any downstream harness or commit.\n\n"
            )
            os._exit(2)  # loud, non-zero, do not chain
        return False


# ─────────────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────────────
def render_fighter(bridge, fighter_id: str) -> str:
    """Render fighter_profile.html for fighter_id, return HTML string."""
    from app import app
    if not hasattr(app, 'game_bridges'):
        app.game_bridges = {}
    app.game_bridges[bridge._user_id] = bridge
    app.jinja_env.cache = {}
    app.config['TESTING'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    with app.test_client() as c:
        with c.session_transaction() as s:
            s['user_id'] = bridge._user_id
        resp = c.get(f'/fighter/{fighter_id}')
        return resp.get_data(as_text=True)


def fight_row_blocks(html: str) -> List[str]:
    """Return substrings, one per fight-row div (border-left blocks
    containing a WIN/LOSS/DRAW badge)."""
    parts = re.split(r'border-left:3px solid[^"]*"[^>]*>', html)
    return [b for b in parts[1:]
            if re.search(r'>\s*(?:WIN|LOSS|DRAW)\s*<', b)]


# ─────────────────────────────────────────────────────────────────────
# REIGN-WINDOW VALIDATION
# ─────────────────────────────────────────────────────────────────────
def within_reign(en: Optional[int], reigns: List[Dict], wc: str
                 ) -> Tuple[Optional[str], Optional[Dict]]:
    """Return ('WON', reign) if en == reign.won_event_number;
    ('IN', reign) if won < en < lost (or lost is None);
    (None, None) otherwise. Division-gated by wc."""
    if en is None:
        return (None, None)
    for r in reigns:
        if r['weight_class'] != wc:
            continue
        won = r.get('won_event_number')
        lost = r.get('lost_event_number')
        if won is None:
            continue
        if won == en:
            return ('WON', r)
        if won < en and (lost is None or en < lost):
            return ('IN', r)
    return (None, None)


def validate_row(row: Dict[str, Any], block: str,
                 reigns: List[Dict], fighter_wc: str
                 ) -> Tuple[bool, bool, Optional[str], List[str]]:
    """Return (has_shield, has_trophy, window_status, violations)."""
    has_shield = '🛡️' in block
    has_trophy = '🏆' in block
    en = row.get('event_number')
    wc = row.get('weight_class') or fighter_wc
    res = row.get('result', '')
    status, hit_reign = within_reign(en, reigns, wc)
    violations = []
    # (a) Retained badges must fall inside/on a reign window in-division.
    if has_trophy and status != 'WON':
        violations.append(f"🏆 but not WON (status={status})")
    if has_shield and status != 'IN':
        violations.append(f"🛡️ but not IN reign window (status={status})")
    # (b) Every W inside a window must carry a badge.
    if res == 'W' and status == 'WON' and not has_trophy:
        violations.append("W at WON boundary but no 🏆")
    if res == 'W' and status == 'IN' and not has_shield:
        violations.append("W inside reign window but no 🛡️")
    return has_shield, has_trophy, status, violations


# ─────────────────────────────────────────────────────────────────────
# ROW COUNTING (for --against)
# ─────────────────────────────────────────────────────────────────────
def count_badges(html: str) -> Tuple[int, int, int]:
    """Return (n_rows, shields, trophies) across all fight rows."""
    blocks = fight_row_blocks(html)
    return (len(blocks),
            sum(1 for b in blocks if '🛡️' in b),
            sum(1 for b in blocks if '🏆' in b))


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────
def per_fighter(bridge, fid: str, fr: Any, reigns: List[Dict],
                ref: Optional[str]) -> Tuple[int, int]:
    """Print one fighter's section. Return (n_rows, n_violations)."""
    header = f"{fr.name} ({fid[:8]}) — {fr.weight_class}"
    print(f"\n{'='*80}\n{header}\n{'='*80}")
    print("REIGNS:")
    for r in reigns:
        print(f"  wc={r['weight_class']}  won_en={r.get('won_event_number')}"
              f"  lost_en={r.get('lost_event_number')}"
              f"  active={r['is_active']}  defenses={r.get('successful_defenses')}")

    # NEW render (live template, no swap)
    new_html = render_fighter(bridge, fid)
    wf = bridge.get_fighter(fid)
    hist_reversed = list(reversed(wf.fight_history))
    new_blocks = fight_row_blocks(new_html)
    n = min(len(hist_reversed), len(new_blocks), 10)

    print("\nROWS (template shows history|reverse, first 10):")
    print(f"  {'idx':>3s}  {'event_name':38s} {'en':>4s} {'wc':18s}"
          f" {'res':4s} 🛡  🏆  {'window':16s} VIOLATION")
    total_viol = 0
    for i in range(n):
        row = hist_reversed[i]
        block = new_blocks[i]
        sh, tr, status, violations = validate_row(row, block, reigns, fr.weight_class)
        en = row.get('event_number')
        wc = row.get('weight_class') or fr.weight_class
        res = row.get('result', '')
        window_lbl = "-" if status is None else f"{status}"
        v_lbl = ("; ".join(violations)) if violations else "-"
        print(f"  {i:>3d}  {row.get('event_name',''):38s}"
              f" {str(en):>4s} {wc:18s} {res:4s}"
              f" {'Y' if sh else '-'}   {'Y' if tr else '-'}"
              f"   {window_lbl:16s} {v_lbl}")
        total_viol += len(violations)

    # --against: render the same context through ref's template + compare
    if ref is not None:
        with TemplateSwap(ref):
            old_html = render_fighter(bridge, fid)
        n_new, sh_new, tr_new = count_badges(new_html)
        n_old, sh_old, tr_old = count_badges(old_html)
        old_blocks = fight_row_blocks(old_html)
        print(f"\n  NEW: rows={n_new} 🛡️={sh_new} 🏆={tr_new}")
        print(f"  ref {ref}: rows={n_old} 🛡️={sh_old} 🏆={tr_old}")
        print(f"  Δ 🛡️={sh_new - sh_old}  Δ 🏆={tr_new - tr_old}")
        # Per-row diffs
        for i in range(min(len(new_blocks), len(old_blocks), 10)):
            n_sh = '🛡️' in new_blocks[i]; o_sh = '🛡️' in old_blocks[i]
            n_tr = '🏆' in new_blocks[i]; o_tr = '🏆' in old_blocks[i]
            if n_sh != o_sh or n_tr != o_tr:
                row = hist_reversed[i]
                print(f"    row[{i}] {row.get('event_name','')} (en={row.get('event_number')} res={row.get('result')}): "
                      f"NEW 🛡={n_sh}/🏆={n_tr}  ref 🛡={o_sh}/🏆={o_tr}")

    return n, total_viol


def main():
    ap = argparse.ArgumentParser(
        description="WEEK-AXIS1 (c) render discrimination probe.")
    ap.add_argument("--seed", type=int, default=20260907)
    ap.add_argument("--weeks", type=int, default=14)
    ap.add_argument("--fighter-select",
                    choices=['founding', 'defended', 'multi-reign', 'all'],
                    default='all')
    ap.add_argument("--against", default=None,
                    help="git ref whose fighter_profile.html to render alongside "
                         "(swap-in with sha-checked restore)")
    ap.add_argument("--fighter-id", default=None,
                    help="Render only this fighter_id (overrides --fighter-select)")
    args = ap.parse_args()

    print(f"render_probe: seed={args.seed} weeks={args.weeks} "
          f"select={args.fighter_select} against={args.against or '(none)'}")
    print(f"HEAD sha: "
          f"{subprocess.check_output(['git','rev-parse','--short','HEAD'], cwd=REPO).decode().strip()}")
    print(f"live template sha256 (pre-run): {_sha256_of(LIVE_TPL)}")

    bridge = build_bridge(args.seed, args.weeks)

    if args.fighter_id:
        fr = bridge._game_state.fighters.get(args.fighter_id)
        if fr is None:
            print(f"render_probe: --fighter-id {args.fighter_id} not found",
                  file=sys.stderr)
            sys.exit(1)
        reigns = bridge.get_fighter_reigns(args.fighter_id)
        selection = [(args.fighter_id, fr, reigns)]
    else:
        selection = select_fighters(bridge, args.fighter_select)

    print(f"\nselected fighters: {len(selection)}")

    total_rows = 0
    total_viol = 0
    for fid, fr, reigns in selection:
        n_rows, n_viol = per_fighter(bridge, fid, fr, reigns, args.against)
        total_rows += n_rows
        total_viol += n_viol

    print(f"\nrender_probe: fighters={len(selection)} rows={total_rows} "
          f"violations={total_viol}")
    print(f"live template sha256 (post-run): {_sha256_of(LIVE_TPL)}")


if __name__ == "__main__":
    main()
