"""Template compile sweep — deploy-time standing gate.

Iterates every .html file under cage_dynasty_web/templates/ through the
running Flask app's jinja_env.get_template and reports every
TemplateSyntaxError as file:line. Exit code 0 = clean, 1 = at least
one broken template.

Constitutional role (CLAUDE.md § Deploy workflow standing gates,
2026-09-07 filing): every deploy MUST run this sweep and require
N/N clean before pull. Introduced 2026-09-07 after TPLFIX (f113004):
C23 a8c4847 landed two Jinja `{# #}` comments inside `{% for %}`
expression bodies which broke fight_camp.html and compare.html but
were caught only in production 5e via a 500. No prior deploy had a
per-template compile check.

Run: from repo root or anywhere:
  PYTHONPATH="<repo>/narrative:<repo>/systems:<repo>/cage_dynasty_web" \\
      python3 -u <repo>/claude/tools/template_compile_sweep.py

Or bare (the script derives paths from __file__ and adds them itself):
  python3 -u <repo>/claude/tools/template_compile_sweep.py

Output: stdout only. Errors go with a nonzero exit code so shell
callers can gate on it (`&&` chains work naturally). No files
written.

Paths auto-derive from __file__:
  <repo>/claude/tools/template_compile_sweep.py  →  <repo>
Runs unchanged on dev / PA / any deploy target.
"""
import os, sys, contextlib, io

# Repo-relative sys.path setup — same shape as
# claude/tools/config_observe_harness.py (C47). __file__ resolves to
# <repo>/claude/tools/template_compile_sweep.py; walk up 3 levels to
# <repo>.
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
for p in (os.path.join(_REPO, "narrative"),
          os.path.join(_REPO, "systems"),
          os.path.join(_REPO, "cage_dynasty_web")):
    if p not in sys.path:
        sys.path.insert(0, p)

# Suppress app-load noise on BOTH streams — pre-uWSGI shim prints go
# to stderr (CLAUDE.md L482-484), IMPORT-PATH-PROOF etc. to stdout.
# We only care about template compile results.
_null_out, _null_err = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(_null_out), \
        contextlib.redirect_stderr(_null_err):
    import game_bridge  # noqa: F401 — triggers sys.path fixup + app deps
    from app import app

env = app.jinja_env
tmpl_dir = os.path.join(_REPO, "cage_dynasty_web", "templates")

files = []
for root, dirs, fnames in os.walk(tmpl_dir):
    for f in fnames:
        if f.endswith(".html"):
            rel = os.path.relpath(os.path.join(root, f), tmpl_dir)
            files.append(rel)

errors = []
for rel in sorted(files):
    try:
        env.get_template(rel)
    except Exception as e:
        cls = type(e).__name__
        line = getattr(e, "lineno", "?")
        msg = str(e)
        errors.append((rel, line, cls, msg))
        print(f"FAIL  {rel}:{line}  {cls}: {msg[:120]}")

n = len(files)
if errors:
    print()
    print(f"=== TEMPLATE COMPILE SWEEP: {len(errors)} broken of {n} ===")
    sys.exit(1)
else:
    print(f"=== TEMPLATE COMPILE SWEEP: {n}/{n} clean ===")
    sys.exit(0)
