# Alua Architecture

## Objective

Alua must remain extensible as the project grows. A new sensor, memory type, decision strategy, action, item rule or physics rule should be addable without rewriting the rest of the project.

## Target structure

```
Alua/
├── init.lua
├── core/
│   ├── module_registry.lua
│   ├── events.lua
│   ├── state.lua
│   ├── config.lua              # planned
│   └── scheduler.lua           # planned
├── agent/
│   ├── entity.lua              # planned migration from npc.lua
│   ├── controller.lua          # planned
│   ├── perception/
│   ├── memory/
│   ├── needs/
│   ├── goals/
│   ├── planning/
│   ├── actions/
│   └── learning/
├── world/
│   ├── physics/
│   ├── items/
│   ├── environment/
│   └── compatibility/
├── ui/
│   ├── commands.lua
│   └── debug.lua
├── docs/
└── tests/
```

The current `npc.lua` and `commands.lua` remain in place while functionality is migrated incrementally. We do not perform a risky big-bang rewrite.

## Core contracts

### Module registry

Subsystems register themselves by a unique ID. Initialization is ordered and failure-isolated. A module should expose only documented capabilities.

Conceptual module definition:

```lua
{
    id = "perception.nearby_entities",
    init = function(ctx) end,
    shutdown = function(ctx) end,
}
```

### Event bus

Modules should prefer events for notifications that do not require direct ownership.

Examples:

- `agent.spawned`
- `agent.mode_changed`
- `perception.updated`
- `goal.changed`
- `action.started`
- `action.finished`
- `world.rule_changed`

Event handlers must be failure-isolated so one module cannot crash unrelated handlers.

### Persistent state

Persistent state is versioned. New schemas must include migrations instead of assuming old saves match the newest structure.

Suggested namespaces:

- `agent:<owner>`
- `memory:<owner>`
- `world:<module>`
- `meta:schema_version`

## Dependency rule

A high-level module may depend on a lower-level contract, but unrelated modules must not reach into each other's private tables.

Preferred direction:

```
core
  ↑
perception / memory / actions
  ↑
goals / planner
  ↑
controller
```

World-rule modules depend on `core` and Mineclonia compatibility adapters, not directly on AI decision internals.

## World modifications

Every world modification must be isolated behind its own module and feature flag. Disabling one world module should restore default Mineclonia behaviour as closely as technically possible.

## Stability rules

- No new global namespace except `alua`.
- Public functions require documentation.
- Persistent data requires schema/version consideration.
- Module initialization errors are logged and isolated.
- Cross-module communication must use a documented API/event.
- Large refactors are incremental.
- Behaviour changes require CHANGELOG and ROADMAP updates.
