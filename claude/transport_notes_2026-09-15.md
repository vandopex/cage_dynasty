# TRANSPORT NOTES — 2026-09-15 (architect thread, post-7d789d0)

Rationale behind the three "Commits and handoffs" rules in CLAUDE.md, plus the
instrument lessons from the arc that produced them. History, not status.

## What happened

An architect thread was asked to copy claude/handoff_post_rematch_cooldown1.md
from the claude.ai project store into the repo and commit it. The expected
transport — a mounted copy under /mnt/project/ — did not exist in that container
at all. The store itself offers no download path: all 126 entries are
API-written text docs with no file-upload entry. The bytes reached disk only by
an architect thread reading the doc and re-typing it. Landed as 7d789d0, blob
sha256 ff51d67a…, verified against the committed object rather than the working
tree.

## Rule 1 — trailers name the tool, not the model

`Co-Authored-By: Claude Code <noreply@anthropic.com>`. A model-version string is
a durable factual claim in a permanent log: it cannot be corrected without
rewriting history and it goes stale by definition. Found this arc: 9faeba8 /
6d7abc2 / a1fd40c carry a model-version trailer that entered without a release.
A grep of the last 20 commits showed trailers "present" — all three instances
were that same session's own. Matching a recent pattern is not following a
convention. Those three stay as history; do not rewrite.

## Rule 2 — handoffs land in the repo first

The project store is a mirror, not a source. It accepts writes and offers no
readback; the only path out is transcription, which cannot self-verify. A hash
taken on a transcribed copy covers the transcription, not the source object, and
a systematic transcription error survives it intact. 51 filings currently sit
there with no verified repo copy — see HANDOFF-TRANSPORT1.

## Rule 3 — a handoff never asserts its own HEAD

handoff_post_rematch_cooldown1.md states "HEAD: a1fd40c, pushed, remote matches"
and instructs the next thread to confirm that on first paste. The moment it
committed as 7d789d0 the assertion was false, and the instructed check now fails
against its own document. Name the last CODE commit and the PA SHA — neither
moves when the handoff is filed.

## Instrument lessons

1. An instrument that cannot discriminate does not get run. Three proposed
   checks (byte count, EOL, head -4) were each logically entailed by a sha256
   match already in hand: guaranteed PASS, zero information. Cancelled.
2. GNU-only flags fail on this Mac — BSD `cat` has no `-A`. Worse, a tool that
   errors into a pipe leaves the next command reading empty stdin, and `grep -c`
   returns 0: a gate reporting PASS while measuring nothing. cc caught it
   unprompted. Use `LC_ALL=C grep -c $'\r' file`.
3. Numbered pastes are a checksum on the architect→cc relay. Two steps were lost
   in transit and were noticed only because the lettering had a gap.
4. Send bytes, not edit instructions. Three corrections to a commit body were
   issued as prose and all three came back reverted; one heredoc fixed it.
5. Completeness is a marker, not a count. The handoff was expected at ~150 lines
   and measured 198 — not truncated, verified by its terminal marker.
6. Never write an unmeasured cause into a permanent record. A MISMATCH shows two
   copies differ, not which one drifted.
7. A grep answers only the question its scope allows. This arc's board
   "contradiction" was investigated by grepping CLAUDE.md, which named
   backlog.md three times and the P3 scope doc zero times; the architect
   concluded the P3 reference was stale and recommended editing the standing
   instructions. Wrong. The P3 doc's canonical status is declared in
   backlog.md line 3 ("same status as"), not in CLAUDE.md. The two are
   canonical peers with different scopes. The grep was scoped to the wrong file
   to answer the question, and an omission was read as staleness. Before
   calling a reference stale, search where the claim would be declared, not
   only where you expected to find it.
