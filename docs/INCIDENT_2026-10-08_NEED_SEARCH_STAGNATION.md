# Incident 2026-10-08: blind resource search overwhelms learning-based navigation

## Evidence from live Termux test

AluaWorld -> AluaBridge works after Bridge PR #10 and #11: repeated
`POST /v1/world/observations` HTTP **202**, and `alua doctor` returned
`last_observation_sequence=900` before the brain started.

Real `alua benchmark --limit 500` reported 226 decisions:
- 224 `move`, 1 `interact`, 1 `manipulate`;
- 175 goals `satisfy_thirst`, 44 `deliberate_navigation`,
  5 `spatial_backtrack`, 1 `satisfy_hunger`, 1 `inspect_object`;
- 225 resolved physical outcomes: 86 successes, 139 failures,
  **38.22%** success, 38.12% movement success, mean progress 0.4228;
- 138 low-progress moves, maximum run of the same motor type 96;
- 500 sensory frames, 59.6% front blocked, 45 self-derived
  perceptual places;
- acceptance FAILED: action stereotype and poor movement quality,
  even though 500 observations covered the decisions.

These are **observed measurements**, not values invented by the AI.
A body-need goal does NOT count as satisfied until its real sensory
effect (e.g. hydration increase) is verified. Code review and CI cannot
promise a higher rate; the same physical environment must be tested
after the patch.

## Root cause in Alua cognitive code

`IntrinsicCurriculum.choose()` correctly gives high urgency to
`satisfy_thirst` when the body perceives thirst, including a
`phase="search"` goal when no valid visible liquid target exists.

However, `SkillGraph.resolve()` unconditionally maps that goal to the
one-step `satisfy_body_need` skill, whose `need` step executes
`ExplorationPolicy.choose()`. When search has no visible target,
`ExplorationPolicy._search_move()` falls back to a fixed
`forward=1.0, strafe=0.0` move. This bypasses the `LocalNavigator`,
persistent failure penalties, obstacle bypass and multi-step
stagnation escape planning used by the regular `explore` goal.

Under repeated thirst with no reachable water, the agent could
recognize `front_blocked`, revisit loops, and backtrack advice,
yet resume blindly pushing into a bad sector on the next need-search
decision. The bridge/world correctly reported those failures.

## Repair

For `satisfy_thirst` and `satisfy_hunger` goals **only** when
`phase == "search"` and no `target_ref` exists:
- Choose `explore_frontier` when local front is passable;
- Choose `bypass_obstacle` when the actual embodied perception marks
  the front obstructed;
- Choose `escape_stagnation` when the self-critic has **verified
  low-progress movement evidence** and requests replanning.

The matching hierarchical navigation skills explicitly list the
resource-search goal kinds. Their implementation chooses the best
self-perceived sector and incorporates actual motor-outcome penalties.
The need goal and its urgency remain unchanged; only the motor
subroutine during searching uses real feedback.

When a real liquid or edible target becomes visible,
`phase="approach"/"drink"/"pickup_required"/"consume_inventory"`
continues through the existing `satisfy_body_need` process.
No resource identity, water location, map data, directions or success
are injected; no bypass of AluaBridge. The AI must find resources
using bodily observations and learn effects by actual outcomes.

## Regression checks

New `tests/test_executive.py` tests require:
1. Thirst search with front physically blocked uses lateral navigation
   instead of a fixed forward primitive.
2. Hunger search with three confirmed low-progress movements chooses
   reorientation followed by a navigation escape step.
3. A thirst goal with a currently visible, referenced target still
   uses the actual `satisfy_body_need` skill.

Run full `bash tools/run_tests.sh` in CI. This is a structural
regression fix. **No on-device improvement has been verified yet**.

## Safe deployment and live acceptance

1. Stop only the Alua Python brain process. Leave Luanti World and
   AluaBridge running.
2. Pull the new Alua main branch without deleting files:
   `git -C "$HOME/alua/Alua" pull --ff-only`.
3. Install into the existing virtual environment:
   `cd "$HOME/alua/Alua" && .venv/bin/python -m pip install -e .`.
4. Load the existing `Alua/.env`; start only one
   `.venv/bin/python -m alua --verbose run`.
5. Let several hundred **real** motor results accrue. Compare
   `alua evaluate --limit 200` / `alua benchmark --limit 500`
   against this baseline, including movement success, stagnation,
   goal diversity and physical hydration delta.
6. If improvement is not supported by live data, mark failed and
   investigate, rather than claiming success or resetting history.

Never delete `~/alua/worlds/AluaWorld`, Bridge SQLite or Alua
SQLite. Operator mind-log can be read in a separate Termux session.
