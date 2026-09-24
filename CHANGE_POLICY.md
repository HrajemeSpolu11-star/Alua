# Change Policy

This file defines a mandatory project rule.

## Documentation-first completion rule

A meaningful change is **not complete** until its documentation is updated in the same change set.

For every code/gameplay change, check:

- **CHANGELOG.md** - always update for implemented behaviour
- **ROADMAP.md** - update when a task changes status, scope or priority
- **ARCHITECTURE.md** - update when module boundaries, public APIs, persistence or dependencies change
- **VISION.md** - update only when the product direction or non-negotiable principles change
- **WORLD_SCOPE.md** - update when world/physics/item scope changes
- **DECISIONS.md** - record important architectural decisions and why they were made
- **README.md** - update when user-facing installation, commands or major features change

## Required change checklist

Before merging or considering work finished:

1. Does the change have a clear module owner?
2. Does it modify a public contract?
3. Does it write persistent data?
4. Can it break old saves?
5. Can it affect Mineclonia compatibility?
6. Does it alter the project vision or roadmap?
7. Were relevant documents updated?
8. Is there a rollback/disable path for a world-rule change?
9. Are secrets/tokens excluded from the repository?
10. Is the change testable through a command, scenario or diagnostic?

## No undocumented vision drift

Ideas discussed during development that are accepted as part of the project direction must be recorded in VISION.md, ROADMAP.md or DECISIONS.md. Chat history alone is not the source of truth.

## Incremental architecture rule

Do not perform large rewrites merely for cleanliness. Migrate one responsibility at a time behind stable interfaces and keep the project runnable between steps.

## Release rule

Each release should summarize:
- user-visible features
- architecture changes
- persistence/migration notes
- known limitations
