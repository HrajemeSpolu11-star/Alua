# World Scope

## Base world

Mineclonia remains the base game and map generator for Alua. We are not currently replacing terrain generation, biomes or the overall world map.

## What we may change

Selected systems around the world can evolve through independent modules:

- item metadata and properties
- weight/load effects
- selected movement physics
- falling and impact behaviour
- water interaction
- tool wear and repair
- crafting extensions
- object interaction rules
- environmental conditions
- selected mob/environment behaviour
- new items or mechanics that fit the world

## What we avoid by default

- replacing the complete Mineclonia map generator
- globally changing unrelated physics from one module
- directly editing many Mineclonia internals when an adapter/hook is possible
- irreversible save changes without migration
- requiring all world modules to be enabled together

## Compatibility rule

World changes should be implemented as feature-isolated modules. Each module should declare:

- what default behaviour it changes
- whether the change is reversible
- persisted data it writes
- Mineclonia APIs/nodes/items it depends on
- known conflicts
- how to disable it

## Map migration rule

If a future change ever touches generated map content, the documentation must state whether it affects only new chunks, existing chunks, or requires a migration. No map-altering feature may be introduced silently.
