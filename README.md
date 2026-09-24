# Alua

Alua je projekt autonomních NPC a živého simulovaného světa pro Luanti/Mineclonia.

## Hlavní směr

Projekt odděluje:
- skutečná pravidla světa
- individuální AI agentů
- populaci
- ekonomiku
- společnost
- příběh
- vývojářskou diagnostiku

Alua sama je AI; není to obal externího LLM.

## Současná stabilní funkce

Aktuální companion stále používá přechodné `npc.lua` a `commands.lua`. Nová modulární kostra je připravená odděleně a současné chování se bude migrovat po ověření na telefonu.

## Architektura

```
core
├── world
│   └── adapter
├── ai
├── population
├── economy
├── society
├── story
└── debug
```

World zná skutečný stav simulace. AI ho nezná přímo a komunikuje se světem přes omezené senzory a povolené akce.

## Dokumentace

- [VISION.md](VISION.md) – dlouhodobá vize
- [ROADMAP.md](ROADMAP.md) – plán vývoje
- [ARCHITECTURE.md](ARCHITECTURE.md) – technická architektura
- [PERCEPTION_MODEL.md](PERCEPTION_MODEL.md) – co smí AI vnímat a vědět
- [WORLD_SCOPE.md](WORLD_SCOPE.md) – rozsah úprav světa
- [MATERIAL_SYSTEM.md](MATERIAL_SYSTEM.md) – materiály a fyzikální vlastnosti
- [CHANGE_POLICY.md](CHANGE_POLICY.md) – pravidla změn
- [DECISIONS.md](DECISIONS.md) – architektonická rozhodnutí
- [CHANGELOG.md](CHANGELOG.md) – přehled změn
- [docs/MODULES.md](docs/MODULES.md) – hranice domén
- [docs/INTERFACES.md](docs/INTERFACES.md) – world/AI rozhraní
- [docs/SIMULATION_LEVELS.md](docs/SIMULATION_LEVELS.md) – výkonová simulace populace
- [docs/TESTING_WORKFLOW.md](docs/TESTING_WORKFLOW.md) – testování dvou NPC

## Jazyk

Interní dokumentace je česky. Kódové názvy a technická API mohou být anglicky.

## Licence

MIT
