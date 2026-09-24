# Architektura Alua

## Cíl

Alua je jeden repozitář a jeden Luanti mod, ale uvnitř je rozdělený na nezávislé domény. Důvodem je zachovat jednoduchou instalaci a současný ContentDB balíček, přitom oddělit svět, AI, populaci, ekonomiku, společnost, příběh a debug.

## Aktuální cílová struktura

```
Alua/
├── core/
│   ├── module_registry.lua
│   ├── events.lua
│   ├── state.lua
│   ├── config.lua
│   └── scheduler.lua
├── world/
│   ├── adapter/
│   ├── materials/
│   ├── physics/
│   ├── items/
│   ├── environment/
│   └── compatibility/
├── ai/
│   ├── perception/
│   ├── memory/
│   ├── world_model/
│   ├── needs/
│   ├── goals/
│   ├── planning/
│   ├── actions/
│   └── learning/
├── population/
├── economy/
├── society/
├── story/
├── debug/
├── docs/
├── npc.lua
└── commands.lua
```

`npc.lua` a `commands.lua` jsou zatím kompatibilní vrstva současného bota. Nemigrují se násilně před testem.

## Závislosti

Registr modulů umí explicitní `requires` závislosti a odmítne spustit modul, pokud jeho nutná závislost selhala.

Preferovaný směr:

```
core
  ↓
world
  ↓
world.adapter
  ↓
ai
  ↓
population / economy / society / story
```

Domény navíc komunikují přes event bus, pokud nepotřebují přímé volání.

## Hranice world ↔ AI

World je autoritativní simulace. AI má vlastní neúplnou představu.

AI smí svět kontaktovat pouze přes explicitně registrované senzory a akce ve `world.adapter`.

```
engine truth
   ↓
world
   ↓
adapter
   ↓
omezené vjemy
   ↓
AI
   ↓
povolená akce
   ↓
adapter
   ↓
world
```

## Modulární živý svět

- `world` = fyzikální a materiálová realita
- `population` = kdo existuje a na jaké úrovni simulace
- `economy` = zdroje, výroba, spotřeba, obchod
- `society` = vztahy, rodiny, frakce, osady
- `story` = události, questy, kampaň
- `ai` = individuální vnímání a rozhodování

Žádný z těchto systémů není „bůh světa“.

## Výkon

Různé subsystémy poběží různou frekvencí. Scheduler umožňuje oddělit rychlé reakce od pomalé ekonomiky nebo populačních změn.

Podrobnosti k populaci jsou v `docs/SIMULATION_LEVELS.md`.

## Materiály

Materiálový systém je samostatná world doména. Podrobný návrh je v `MATERIAL_SYSTEM.md`.

## Dokumentace rozhraní

- `docs/MODULES.md`
- `docs/INTERFACES.md`
- `docs/SIMULATION_LEVELS.md`
- `docs/TESTING_WORKFLOW.md`

## Pravidla stability

- jediný globální namespace je `alua`
- moduly mají explicitní odpovědnost
- AI neobchází perception boundary
- debug není senzor AI
- persistentní data jsou verzovaná
- velké refaktory jsou postupné
- významné změny aktualizují českou dokumentaci
