# Alua

Alua is an experimental autonomous companion framework for Luanti, currently tested with **Mineclonia**.

The current release is playable: every player can spawn one persistent Alua companion, switch its behaviour, recall it, inspect its simple memory and request a basic sensor report.

## Core vision

Alua itself is the AI. The project does **not** depend on an external LLM or external AI service for its core intelligence. Intelligence will be built inside the mod from modular perception, memory, needs, goals, planning, actions and learning systems.

Mineclonia remains the base world. The project does not aim to replace the map generator. World work focuses on selected rules and systems such as physics, items, interactions, environment behaviour and related gameplay mechanics.

## Current features

- Persistent companion entity with owner binding
- Autonomous follow behaviour
- Stay / follow mode switching
- Right-click interaction
- Recall command
- Simple persistent memory of the owner's last seen position
- Local sensor report
- Status reporting
- One active companion per player

## Commands

```
/alua_test
/alua_spawn
/alua_follow
/alua_stay
/alua_recall
/alua_status
/alua_scan
/alua_remove
/alua_help
```

## Documentation

The repository documentation is part of the project contract:

- [VISION.md](VISION.md) - product vision and non-negotiable direction
- [ROADMAP.md](ROADMAP.md) - implementation phases and acceptance criteria
- [ARCHITECTURE.md](ARCHITECTURE.md) - modular architecture and boundaries
- [WORLD_SCOPE.md](WORLD_SCOPE.md) - what may and may not change in Mineclonia
- [CHANGE_POLICY.md](CHANGE_POLICY.md) - mandatory documentation rules for every change
- [CHANGELOG.md](CHANGELOG.md) - chronological record of implemented changes
- [DECISIONS.md](DECISIONS.md) - important architectural decisions

## Development rule

No meaningful code or gameplay change is considered complete until the related documentation is updated. Changes that alter scope, architecture or planned work must update the relevant documents and roadmap in the same change set.

## License

MIT
