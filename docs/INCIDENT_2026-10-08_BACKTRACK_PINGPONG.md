# Incident: successful motor steps masked a backtrack ping-pong loop
Date: 2026-10-08, real Android Termux Luanti + AluaBridge + Alua

## Live evidence, NOT a completed acceptance

After Alua PR #15 repaired blind resource search, user tested live
World + Bridge + Alua. The AI was observed walking forward and backward
inside a small square, not exploring meaningfully.

`alua benchmark --limit 500`, session suffix `_e5`, reported:
- 500 decisions, 499 `move` and 1 `look`;
- **496** `spatial_backtrack` goals, 3 `satisfy_thirst`,
  1 `survive_breath`;
- 499 resolved motor outcomes: 495 success, 4 failure = **99.2%**;
- mean move progress 0.7815 and only 4 low-progress moves;
- **495** consecutive movement actions;
- 500 sensory replay observations but only **5** unique perceived places;
- `front_blocked_fraction = 1.0` (100%);
- benchmark incorrectly returned `acceptance.passed=true`.

Baseline for previous session suffix `_e2` before PR #15:
38.22% real motor success, 138 low-progress moves, 59.6%
front-blocked. The two samples are from different body sessions and
are not proof of genuine navigation improvement. In the new run
motor success improved but goal achievement, coverage, revisits and
escape from the local square were plainly inadequate.

## Source-code failure mode

`Runtime._select_goal()` selects a spatial backtrack directive
before ordinary need/exploration goals when `CognitiveCore` proposes
one. This is correct for a real dead end, but requires finite recovery.

`SpatialMemory.backtrack_directive()` previously proposed the same
inverse maneuver indefinitely whenever a remembered route's
destination matched the currently perceived place. The motor can
return physical `progress_signal >= 0.55` without the next sensory
frame identifying the *remembered predecessor*. In
`SpatialMemory.finish_action()`, any such successful movement
that changed the perceived signature could append a **new outward
route edge**, including a backward move. The next backtrack goal
might then undo that freshly created edge, producing an A/B
ping-pong. Distinct places in the current perceptual hash are not
absolute locations; they can alias or drift, so motor success
cannot by itself prove arrival at the named place.

`evaluate_trace()` intentionally did not label a long successful
`move` streak as a stereotyped action. However it was blind to
the *goal* being repeated: 496 backtrack goals still passed.
This distinction is important: successful long-distance travel
should not automatically fail a benchmark.

## Implementation and safety boundary

- Route memory now treats `spatial_backtrack` motor events explicitly
  via the **existing verified action expectation goal_kind**; no
  World truth or raw coordinates are introduced.
- During unfinished backtracking, successful physical moves update
  Alua's **relative odometry** and empirical outcome learning but
  never create a fresh outward route. Only a recognized original
  predecessor percept allows route-pop and successful return.
- Bounded maximum **8 observed motor outcomes** for a single
  remembered predecessor. If it remains unrecognized, discard
  the unreliable route edge (not the world position or the entire
  long-term knowledge base) and return control to the normal
  goal arbitration; this is uncertainty management, not a
  claim that the return was completed.
- A current return plan may span multiple different sensory place
  signatures without being dropped immediately, but is bounded.
- Benchmark additionally reports `longest_backtrack_streak`,
  `spatial_backtrack_fraction`, and
  `spatial_backtrack_dominance_detected`. Sustained backtracking
  (>=64 decisions, >=32 consecutive such goals and >=90% share)
  causes the acceptance check `no_spatial_backtrack_dominance`
  to fail **even with a near-perfect physical motor score**.
  The threshold is a conservative operator quality alarm, not
  a proof of semantic understanding.
- Added regression tests for (a) unfinished return does not
  generate outward routes, (b) actual recognition of the original
  percept ends return, (c) 8 unsuccessful-to-reidentify return steps
  invalidate that edge, (d) 99% success with 496 backtrack goals
  fails benchmark, (e) a brief legitimate return stays acceptable.
- No change to Luanti World, AluaBridge, credentials or raw AI
  sensory privileges. No reset of Alua SQLite, World save or
  Bridge SQLite.

## Deployment, live acceptance STILL PENDING

After CI and merge, stop *only the brain*, pull and install
Alua in the existing Termux Python virtualenv, restart one
`python -m alua --verbose run` process with existing `.env`.

Monitor `alua mind-log --limit 5 --no-episodes` when debugging:
`rationale.goal_reason`, `rationale.cognitive_state`,
`verified_motor_outcome`, `plan_skill`, `goal_kind`.
These are observable internal records and never inject World data.

After a fresh series of real events run
`alua benchmark --limit 500` and compare goal_counts,
`longest_backtrack_streak`, `spatial_backtrack_fraction`,
`unique_perceptual_places`, front blockage and motor success.
The new acceptance check must fail when dominated by >90%
backtrack even if motor quality is high. A genuinely healthy
run needs sustained progress across meaningful perceptual
contexts, successful physical interaction and recovered autonomy;
CI does not verify that.

If the agent still paces after this patch, investigate
perceptual-place aliasing, action choice under blocked sensors,
and repeat-visit handling rather than declaring success or
clearing learned memories. Existing logs include enough trace
metadata to continue from this state.

## Source files

- `src/alua/spatial_memory.py`
- `src/alua/cognition.py`
- `src/alua/evaluation.py`
- `tests/test_spatial_memory.py`
- `tests/test_evaluation.py`
- Earlier context: `docs/INCIDENT_2026-10-08_NEED_SEARCH_STAGNATION.md`
