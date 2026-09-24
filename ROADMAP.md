# Alua Roadmap

This roadmap is the canonical plan for the project. Status must be updated whenever implementation priorities change.

## Phase 0 - Functional companion foundation

Status: **Implemented / stabilizing**

- [x] Spawnable persistent companion
- [x] Owner binding
- [x] Follow mode
- [x] Stay mode
- [x] Recall
- [x] Basic status reporting
- [x] Basic local sensor report
- [x] Simple persistent memory
- [ ] Device testing in Luanti + Mineclonia
- [ ] ContentDB approval

Acceptance: the current companion can be installed, spawned, controlled and saved without errors.

## Phase 1 - Modular core

Status: **In progress**

- [x] Define project architecture
- [x] Add module registry foundation
- [x] Add internal event bus foundation
- [x] Add versioned persistent-state foundation
- [ ] Move existing companion behaviour behind module boundaries
- [ ] Add configuration/feature flags
- [ ] Add diagnostics for loaded modules
- [ ] Add compatibility checks

Acceptance: adding a new subsystem does not require editing unrelated subsystems.

## Phase 2 - Perception and memory

Status: **Planned**

- [ ] Structured perception snapshots
- [ ] Nearby blocks/entities/items
- [ ] Threat and obstacle detection
- [ ] Short-term working memory
- [ ] Long-term episodic memory
- [ ] Known places/objects
- [ ] Memory limits and cleanup
- [ ] Save-schema migration tests

Acceptance: Alua can build and update a bounded internal representation of relevant surroundings.

## Phase 3 - Needs, goals and decisions

Status: **Planned**

- [ ] Needs model
- [ ] Utility scoring
- [ ] Goal selection
- [ ] Decision arbitration
- [ ] Interrupts for danger/critical states
- [ ] Explainable decision trace

Acceptance: Alua chooses between competing goals without hard-coding one fixed response for every situation.

## Phase 4 - Planning and skills

Status: **Planned**

- [ ] Skill/capability registry
- [ ] Multi-step planner
- [ ] Movement/path actions
- [ ] Item pickup/use
- [ ] Inventory operations
- [ ] Crafting actions
- [ ] Resource gathering
- [ ] Safe failure/replanning

Acceptance: Alua can compose several primitive actions into a meaningful task.

## Phase 5 - Selected world-rule modules

Status: **Planned**

Map generation remains unchanged. Work focuses on opt-in gameplay systems:

- [ ] Item properties and metadata
- [ ] Weight/load effects
- [ ] Selected movement/physics rules
- [ ] Fall/impact behaviour
- [ ] Water/environment interactions
- [ ] Tool wear/repair extensions
- [ ] Environmental state hooks
- [ ] Compatibility layer for Mineclonia updates

Acceptance: each world change can be enabled/disabled independently and does not silently modify unrelated systems.

## Phase 6 - Learning and adaptation

Status: **Research / planned**

- [ ] Outcome tracking
- [ ] Preference adjustment
- [ ] Experience-based utility tuning
- [ ] Safety limits on adaptation
- [ ] Persistence and reset controls

Acceptance: prior outcomes can influence future choices without allowing uncontrolled mutation of core rules.

## Phase 7 - Stability and tooling

Status: **Continuous**

- [ ] Performance budgets
- [ ] Save migration framework
- [ ] Debug HUD/logging
- [ ] Regression test scenarios
- [ ] Mineclonia compatibility matrix
- [ ] Release checklist
