# Architektura Alua

## Cíl

Projekt musí zůstat rozšiřitelný. Nový senzor, typ paměti, rozhodovací strategie, akce, pravidlo předmětu nebo fyzikální modul musí jít přidat bez přepisování zbytku systému.

## Cílová struktura

```
Alua/
├── init.lua
├── core/
│   ├── module_registry.lua
│   ├── events.lua
│   ├── state.lua
│   ├── config.lua
│   └── scheduler.lua
├── agent/
│   ├── entity.lua
│   ├── controller.lua
│   ├── perception/
│   ├── memory/
│   ├── world_model/
│   ├── needs/
│   ├── goals/
│   ├── planning/
│   ├── actions/
│   └── learning/
├── world/
│   ├── adapter/
│   ├── physics/
│   ├── items/
│   ├── environment/
│   └── compatibility/
├── ui/
├── docs/
└── tests/
```

Současné `npc.lua` a `commands.lua` zatím zůstávají kvůli stabilitě. Budou se převádět postupně, ne jedním rizikovým přepisem.

## Registr modulů

Každý subsystém má unikátní ID a registruje se přes společné jádro.

Příklad:

```lua
{
    id = "perception.nearby_entities",
    init = function(ctx) end,
    shutdown = function(ctx) end,
}
```

## Interní události

Moduly mají pro oznamování změn používat event bus místo přímého sahání do soukromých struktur jiného modulu.

Příklady:

- `agent.spawned`
- `perception.updated`
- `memory.updated`
- `world_model.updated`
- `goal.changed`
- `action.started`
- `action.finished`
- `world.rule_changed`

Chyba jednoho handleru nesmí shodit ostatní.

## Perzistentní stav

Uložená data jsou verzovaná. Změna struktury musí mít migraci.

Předpokládané jmenné prostory:

- `agent:<owner>`
- `memory:<owner>`
- `world_model:<owner>`
- `world:<module>`
- `meta:schema_version`

## Zásadní hranice mezi enginem a AI

```
Luanti / Mineclonia
      │
      ▼
  world adapter
      │
      ▼
omezené vnímání
      │
      ▼
paměť + naučený model světa
      │
      ▼
cíle / plánování / akce
```

Kognitivní část AI nesmí volat libovolné API Luanti pro zjišťování skutečného stavu světa.

Pouze adapter/perception vrstva smí číst technickou realitu enginu a musí ji převést na omezené vjemy.

Diagnostické nástroje mohou vidět skutečná data, ale jejich výstup nesmí proudit do autonomního rozhodování.

Podrobnosti jsou v `PERCEPTION_MODEL.md`.

## Směr závislostí

```
core
  ↑
world adapter
  ↑
perception / memory / actions
  ↑
world model / learning
  ↑
goals / planner
  ↑
controller
```

World moduly jsou oddělené od vnitřního rozhodování AI.

## Pravidla stability

- jediný globální namespace je `alua`
- veřejné funkce musí být dokumentované
- perzistentní data musí řešit verzi schématu
- chyby inicializace modulu se logují a izolují
- moduly komunikují přes dokumentované API nebo události
- cognition nesmí obcházet perception boundary
- diagnostická vševědoucnost nesmí ovlivňovat AI
- velké refaktory se dělají postupně
- změny chování vyžadují aktualizaci dokumentace
