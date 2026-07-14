"""STAGE 1 — MULTI-SEED OUTCOME MATRIX. READ-ONLY.

10 seeds, 12 weeks each, PYTHONHASHSEED=0. For each seed, fully
build a save-level fixture-equivalent capture, compute live-play +
pre-gen matrices, then pool and report both aggregate and per-seed.

Per the uuid finding — different seeds are different WORLDS, not
resamples of the same world. So "pooled" means "combined across 10
distinct populations." Reported alongside per-seed distribution so
the reader can see whether the same-family-vs-cross-family
asymmetry is structural or a single-world artifact.

No engine touched. No tuning proposed. No commit.
"""
import _common  # noqa: F401
import io
import os
import random
import contextlib
import sys
import json
import subprocess
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = _common.REPO_ROOT

# ── Style family taxonomy (from cage_dynasty_web/styles.py:517-527) ──
STRIKER_STYLES = {"Striker", "Counter Striker", "Pressure Fighter",
                  "Point Fighter", "Muay Thai"}
GRAPPLER_STYLES = {"Wrestler", "Ground & Pound", "BJJ Specialist",
                   "Clinch Fighter"}
HYBRID_STYLES = {"Sprawl & Brawl", "Balanced"}

def style_bucket(s):
    if s in STRIKER_STYLES: return "S"
    if s in GRAPPLER_STYLES: return "G"
    return "H"

def matchup(s1, s2):
    b1, b2 = style_bucket(s1), style_bucket(s2)
    key = tuple(sorted([b1, b2]))
    return {("S","S"):"SxS", ("G","G"):"GxG", ("G","S"):"SxG",
            ("H","S"):"SxH", ("G","H"):"GxH", ("H","H"):"HxH"}[key]

def classify_method(method):
    if not method:
        return "OTHER"
    m = method.strip()
    if m == "Draw":
        return "DRAW"
    if m.startswith("Decision") or m == "DEC" or "DEC" in m.upper():
        return "DEC"
    if m.startswith("Submission") or m == "SUB":
        return "SUB"
    if m.startswith("TKO") or m == "TKO":
        if "Doctor" in m or "Cut" in m:
            return "TKO_DOCTOR"
        return "TKO_STRIKES"
    if m.startswith("KO") or m == "KO":
        return "KO"
    return "OTHER"

def _run_seed_subprocess(seed):
    """Run one seed as a subprocess with a fresh interpreter. Returns
    dict with live + pregen matchup counters."""
    _here_abs = os.path.abspath(_HERE)
    _repo_abs = os.path.abspath(_REPO)
    script = f"""
import sys, os
sys.path.insert(0, {_here_abs!r})
import _common as c
if {_here_abs!r} not in sys.path:
    sys.path.insert(0, {_here_abs!r})
c.SEED = {seed}
import random, uuid
c._uuid_rng = random.Random({seed})
def _seeded_uuid4():
    return uuid.UUID(int=c._uuid_rng.getrandbits(128))
uuid.uuid4 = _seeded_uuid4
random.seed({seed})

import io, contextlib, json
import fixture_generator as fg
fg._captured_fights.clear()
fx, _ = fg.build_fixture()

# Pre-gen: re-run each fight through fight_engine.simulate_fight
import fight_engine as fe
from dataclasses import fields as dc_fields, replace
try:
    from styles import FightingStyle
except Exception:
    FightingStyle = None

def rebuild_fa(fa_dict):
    valid = {{f.name for f in dc_fields(fe.FighterAttributes)}}
    kw = {{k: v for k, v in fa_dict.items() if k in valid}}
    style = kw.get('fighting_style')
    if style and isinstance(style, str) and FightingStyle is not None:
        for m in FightingStyle:
            if m.value == style:
                kw['fighting_style'] = m
                break
        else:
            kw['fighting_style'] = None
    try:
        return fe.FighterAttributes(**kw)
    except Exception:
        return None

results = {{'live': [], 'pregen': []}}
for i, f in enumerate(fx['fights']):
    er = f.get('engine_result', {{}})
    fa1 = f.get('fa1', {{}}) or {{}}
    fa2 = f.get('fa2', {{}}) or {{}}
    s1 = fa1.get('fighting_style'); s2 = fa2.get('fighting_style')
    if not s1 or not s2: continue
    rounds = f.get('rounds', 3)
    is_title = f.get('source_is_title_fight', False)
    row = {{
        'style1': s1, 'style2': s2, 'rounds': rounds, 'is_title': is_title,
        'method': er.get('method', ''), 'finish_round': er.get('finish_round', 0),
        'sub_atts': sum(int(s.get('sub_att', 0) or 0)
                        for lst in (er.get('fighter1_stats') or [],
                                    er.get('fighter2_stats') or []) for s in lst),
    }}
    results['live'].append(row)

    # Pre-gen — same matchup
    obj1 = rebuild_fa(fa1); obj2 = rebuild_fa(fa2)
    if not obj1 or not obj2: continue
    cfg = fe.FightConfig.championship_fight() if is_title else fe.FightConfig.standard_fight()
    if rounds == 5 and not is_title:
        cfg = replace(cfg, scheduled_rounds=5)
    random.seed({seed} * 10000 + i)
    with contextlib.redirect_stdout(io.StringIO()):
        r = fe.simulate_fight(obj1, obj2, cfg, heat_level=0)
    pg_atts = 0
    for lst in (r.fighter1_stats or [], r.fighter2_stats or []):
        for rs in lst:
            if isinstance(rs, dict):
                pg_atts += int(rs.get('sub_att', 0) or 0)
            else:
                pg_atts += int(getattr(rs, 'submission_attempts', 0) or 0)
    results['pregen'].append({{
        'style1': s1, 'style2': s2, 'rounds': rounds, 'is_title': is_title,
        'method': r.method or '', 'finish_round': r.finish_round or 0,
        'sub_atts': pg_atts,
    }})

print(json.dumps({{'seed': {seed}, 'results': results}}))
"""
    env = dict(os.environ)
    env['PYTHONHASHSEED'] = '0'
    env['HOME'] = '/tmp'
    p = subprocess.run([sys.executable, '-c', script], env=env,
                       capture_output=True, text=True, timeout=300)
    for line in reversed(p.stdout.split('\n')):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                return json.loads(line)
            except Exception:
                pass
    return {'seed': seed, 'error': p.stderr[-300:] if p.stderr else 'no_json'}

def compute_matchup_stats(results_list):
    """Bucket by matchup. Returns {mb: {n, methods, sub_atts, sub_landed, finish_n}}."""
    cells = defaultdict(lambda: {'n': 0, 'methods': Counter(),
                                  'sub_atts_total': 0, 'sub_landed': 0,
                                  'finish_rounds': Counter()})
    for r in results_list:
        mb = matchup(r['style1'], r['style2'])
        cls = classify_method(r['method'])
        c = cells[mb]
        c['n'] += 1
        c['methods'][cls] += 1
        c['sub_atts_total'] += r['sub_atts']
        if cls == 'SUB':
            c['sub_landed'] += 1
        if cls in ('KO', 'TKO_STRIKES', 'TKO_DOCTOR', 'SUB'):
            c['finish_rounds'][r['finish_round']] += 1
    return cells

def cell_finish_pct(cell):
    if cell['n'] == 0:
        return None
    fin = sum(cell['methods'].get(m, 0) for m in ('KO', 'TKO_STRIKES', 'TKO_DOCTOR', 'SUB'))
    return 100 * fin / cell['n']

def cell_method_pct(cell, method):
    if cell['n'] == 0:
        return None
    return 100 * cell['methods'].get(method, 0) / cell['n']

def main():
    SEEDS = [42, 100, 200, 300, 1000, 1001, 1002, 1003, 1004, 1005]
    print("=" * 100)
    print(f"STAGE 1 MULTI-SEED — {len(SEEDS)} worlds, 12 weeks each")
    print(f"Per uuid finding: each seed is a distinct WORLD, not resamples")
    print("=" * 100)
    print()

    per_seed = {}
    all_live = []
    all_pregen = []
    for s in SEEDS:
        print(f"  ...seed {s}", file=sys.stderr, flush=True)
        r = _run_seed_subprocess(s)
        if 'error' in r:
            print(f"  seed {s}: ERROR — {r['error'][:100]}")
            continue
        per_seed[s] = r['results']
        all_live.extend(r['results']['live'])
        all_pregen.extend(r['results']['pregen'])

    # ── Per-seed table: aggregate finish rate + matchup breakdown ──
    print("\n" + "=" * 100)
    print(f"{'PER-SEED':<12} {'live_agg':>10} {'pregen_agg':>10} {'SxS_live':>10} {'SxS_pg':>10} "
          f"{'GxG_live':>10} {'GxG_pg':>10} {'SxG_live':>10} {'SxG_pg':>10}")
    print("=" * 100)
    for s in SEEDS:
        if s not in per_seed: continue
        live_cells = compute_matchup_stats(per_seed[s]['live'])
        pg_cells = compute_matchup_stats(per_seed[s]['pregen'])
        agg_live = compute_matchup_stats([{'style1':'Balanced','style2':'Balanced',
                                            'rounds':3,'is_title':False,
                                            'method':r['method'],'finish_round':r['finish_round'],
                                            'sub_atts':r['sub_atts']} for r in per_seed[s]['live']])
        # Wait — aggregate needs different — just compute directly
        live_agg = 0; live_n = 0
        for r in per_seed[s]['live']:
            live_n += 1
            if classify_method(r['method']) in ('KO','TKO_STRIKES','TKO_DOCTOR','SUB'):
                live_agg += 1
        pg_agg = 0; pg_n = 0
        for r in per_seed[s]['pregen']:
            pg_n += 1
            if classify_method(r['method']) in ('KO','TKO_STRIKES','TKO_DOCTOR','SUB'):
                pg_agg += 1
        def fmt(cell):
            if cell['n'] == 0: return f"—       "
            fin = cell_finish_pct(cell)
            marker = "*" if cell['n'] < 5 else " "
            return f"{fin:5.1f}%N{cell['n']:<3}{marker}"
        live_a = f"{100*live_agg/live_n:5.1f}%N{live_n:<3}" if live_n else "—"
        pg_a = f"{100*pg_agg/pg_n:5.1f}%N{pg_n:<3}" if pg_n else "—"
        print(f"seed={s:<7}  {live_a:>10} {pg_a:>10} "
              f"{fmt(live_cells['SxS']):>10} {fmt(pg_cells['SxS']):>10} "
              f"{fmt(live_cells['GxG']):>10} {fmt(pg_cells['GxG']):>10} "
              f"{fmt(live_cells['SxG']):>10} {fmt(pg_cells['SxG']):>10}")
    print("\n(N<5 marked *; cell finish pct on N<5 is direction not target)")

    # ── Pooled table ──
    print("\n" + "=" * 100)
    print("POOLED across 10 distinct worlds — this is 'combined N=~780 pool', NOT '78 resamples'")
    print("=" * 100)
    live_pool = compute_matchup_stats(all_live)
    pg_pool = compute_matchup_stats(all_pregen)

    def pool_agg(rows):
        n = len(rows); fin = 0; deccnt = 0; drwcnt = 0; ko = 0; tkos = 0; tkod = 0; sub = 0
        for r in rows:
            cls = classify_method(r['method'])
            if cls in ('KO','TKO_STRIKES','TKO_DOCTOR','SUB'): fin += 1
            if cls == 'DEC': deccnt += 1
            if cls == 'DRAW': drwcnt += 1
            if cls == 'KO': ko += 1
            if cls == 'TKO_STRIKES': tkos += 1
            if cls == 'TKO_DOCTOR': tkod += 1
            if cls == 'SUB': sub += 1
        return {'n':n, 'fin':fin, 'dec':deccnt, 'drw':drwcnt,
                'ko':ko, 'tkos':tkos, 'tkod':tkod, 'sub':sub}

    lp = pool_agg(all_live)
    pp = pool_agg(all_pregen)
    def pct(a, b): return f"{100*a/b:5.1f}%" if b else "  —  "
    print(f"                    N   KO    TKO   DOC   SUB   DEC   DRW   FINISH")
    print(f"  LIVE-PLAY   {lp['n']:>6}  {pct(lp['ko'],lp['n'])}  {pct(lp['tkos'],lp['n'])}  "
          f"{pct(lp['tkod'],lp['n'])}  {pct(lp['sub'],lp['n'])}  {pct(lp['dec'],lp['n'])}  "
          f"{pct(lp['drw'],lp['n'])}  {pct(lp['fin'],lp['n'])}")
    print(f"  PRE-GEN     {pp['n']:>6}  {pct(pp['ko'],pp['n'])}  {pct(pp['tkos'],pp['n'])}  "
          f"{pct(pp['tkod'],pp['n'])}  {pct(pp['sub'],pp['n'])}  {pct(pp['dec'],pp['n'])}  "
          f"{pct(pp['drw'],pp['n'])}  {pct(pp['fin'],pp['n'])}")
    if lp['n'] and pp['n']:
        delta = 100*lp['fin']/lp['n'] - 100*pp['fin']/pp['n']
        print(f"  Δ (live - pregen finish): {delta:+.1f}pp")

    print()
    print("Pooled by matchup:")
    order = [('SxS','striker-v-striker'), ('GxG','grappler-v-grappler'),
             ('SxG','striker-v-grappler'), ('SxH','striker-v-hybrid'),
             ('GxH','grappler-v-hybrid'), ('HxH','hybrid-v-hybrid')]
    print(f"  {'matchup':<24} {'live_N':>7} {'live_fin%':>10} {'pg_N':>7} {'pg_fin%':>10} {'Δ':>8}")
    for mb, name in order:
        lc = live_pool.get(mb, {'n':0, 'methods':Counter()})
        pc = pg_pool.get(mb, {'n':0, 'methods':Counter()})
        lf = cell_finish_pct(lc); pf = cell_finish_pct(pc)
        lf_s = f"{lf:5.1f}%" if lf is not None else "  —  "
        pf_s = f"{pf:5.1f}%" if pf is not None else "  —  "
        d_s = f"{lf-pf:+.1f}pp" if lf is not None and pf is not None else "  —  "
        print(f"  {name:<24} {lc['n']:>7} {lf_s:>10} {pc['n']:>7} {pf_s:>10} {d_s:>8}")

    # ── Per-seed distribution — variance across worlds ──
    print()
    print("=" * 100)
    print("VARIANCE across worlds (aggregate finish rate per seed)")
    print("=" * 100)
    live_finishes = []; pg_finishes = []
    for s in SEEDS:
        if s not in per_seed: continue
        rows = per_seed[s]['live']
        n = len(rows); fin = sum(1 for r in rows if classify_method(r['method']) in ('KO','TKO_STRIKES','TKO_DOCTOR','SUB'))
        if n: live_finishes.append(100*fin/n)
        rows = per_seed[s]['pregen']
        n = len(rows); fin = sum(1 for r in rows if classify_method(r['method']) in ('KO','TKO_STRIKES','TKO_DOCTOR','SUB'))
        if n: pg_finishes.append(100*fin/n)
    def dist(vals, label):
        if not vals:
            return f"  {label}: (empty)"
        vs = sorted(vals)
        return (f"  {label}: n={len(vs)} min={vs[0]:.1f}% median={vs[len(vs)//2]:.1f}% "
                f"max={vs[-1]:.1f}% spread={vs[-1]-vs[0]:.1f}pp")
    print(dist(live_finishes, "live-play"))
    print(dist(pg_finishes,   "pre-gen  "))

    # ── The specific asymmetry Van flagged ──
    print()
    print("=" * 100)
    print("SAME-FAMILY vs CROSS-FAMILY DIVERGENCE (Van's structural hypothesis)")
    print("=" * 100)
    print()
    print("Hypothesis: same-family matchups (SxS, GxG) show ~50pp live-vs-pregen gap")
    print("while cross-family (SxG) shows only ~16pp. Test: does this hold across worlds?")
    print()
    # Per-seed same-family Δ vs cross-family Δ
    print(f"  {'seed':>6}  {'SxS_Δ':>10}  {'GxG_Δ':>10}  {'SxG_Δ':>10}  {'SxS+GxG_avg':>14}  {'diff_cross_vs_same':>20}")
    same_family_gaps = []
    cross_family_gaps = []
    for s in SEEDS:
        if s not in per_seed: continue
        lc = compute_matchup_stats(per_seed[s]['live'])
        pc = compute_matchup_stats(per_seed[s]['pregen'])
        def gap(mb):
            l = cell_finish_pct(lc.get(mb, {'n':0,'methods':Counter()}))
            p = cell_finish_pct(pc.get(mb, {'n':0,'methods':Counter()}))
            if l is None or p is None: return None
            return l - p
        sxs = gap('SxS'); gxg = gap('GxG'); sxg = gap('SxG')
        sxs_n = lc.get('SxS',{'n':0})['n']; gxg_n = lc.get('GxG',{'n':0})['n']; sxg_n = lc.get('SxG',{'n':0})['n']
        def fmt(v, n):
            if v is None: return "  —      "
            marker = "*" if n < 5 else " "
            return f"{v:+6.1f}pp{marker}N{n:<3}"
        same_avg_str = "  —      "
        if sxs is not None and gxg is not None:
            same_avg = (sxs + gxg) / 2
            same_family_gaps.append(same_avg)
            same_avg_str = f"{same_avg:+6.1f}pp   "
        if sxg is not None:
            cross_family_gaps.append(sxg)
        diff_str = "  —"
        if sxs is not None and gxg is not None and sxg is not None:
            same_avg = (sxs + gxg) / 2
            diff_str = f"{same_avg - sxg:+6.1f}pp"
        print(f"  {s:>6}  {fmt(sxs, sxs_n):>10}  {fmt(gxg, gxg_n):>10}  {fmt(sxg, sxg_n):>10}  "
              f"{same_avg_str:>14}  {diff_str:>18}")
    print("\n  (* = cell N<5 — direction only)")
    if same_family_gaps and cross_family_gaps:
        sfg = sorted(same_family_gaps); cfg = sorted(cross_family_gaps)
        print()
        print(f"  same-family (SxS+GxG avg) gap: median {sfg[len(sfg)//2]:+.1f}pp, "
              f"range [{sfg[0]:+.1f}, {sfg[-1]:+.1f}], N={len(sfg)}")
        print(f"  cross-family (SxG) gap:        median {cfg[len(cfg)//2]:+.1f}pp, "
              f"range [{cfg[0]:+.1f}, {cfg[-1]:+.1f}], N={len(cfg)}")
        # Structural test: does same-family gap exceed cross-family gap in every world?
        both = []
        for s in SEEDS:
            if s not in per_seed: continue
            lc = compute_matchup_stats(per_seed[s]['live'])
            pc = compute_matchup_stats(per_seed[s]['pregen'])
            sxs = None; gxg = None; sxg = None
            for mb, ref in [('SxS','sxs'),('GxG','gxg'),('SxG','sxg')]:
                l = cell_finish_pct(lc.get(mb, {'n':0,'methods':Counter()}))
                p = cell_finish_pct(pc.get(mb, {'n':0,'methods':Counter()}))
                v = None if (l is None or p is None) else (l - p)
                if ref == 'sxs': sxs = v
                elif ref == 'gxg': gxg = v
                elif ref == 'sxg': sxg = v
            if sxs is not None and gxg is not None and sxg is not None:
                same = (sxs + gxg) / 2
                both.append((s, same, sxg, same > sxg))
        exceeded = sum(1 for x in both if x[3])
        print(f"  worlds where same-family gap > cross-family gap: {exceeded}/{len(both)}")
        print(f"  (structural signature confirmed if ≥8/10)")

if __name__ == "__main__":
    main()
