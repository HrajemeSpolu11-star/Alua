# Alua AI

Alua je samostatný kognitivní systém pro autonomní agenty žijící v AluaWorld.

Od 2026-10-06 je hlavní architektura projektu změněna: Alua už není Luanti mod a nesmí být přímo napojená na engine. AluaWorld je autoritativní fyzický svět, AluaBridge je bezpečná transportní a epistemická hranice a tento repozitář vlastní pouze kognici.

Tok systému:

    AluaWorld -> AluaBridge -> Alua AI
    Alua AI   -> AluaBridge -> AluaWorld

Alua AI smí přijímat pouze vjemy svého těla, vytvářet si vlastní paměť a přesvědčení a žádat o primitivní akce. Nesmí číst mapu, technické názvy nodů, materiály, biomy, recepty, interní objekty ani administrátorská data.

## Aktuální stav

Implementováno v nové Python architektuře:
- samostatný Python 3.12+ package;
- pouze localhost konfigurace AluaBridge;
- per-agent token pouze z prostředí;
- Agent API klient pro health, session, observations a actions;
- striktní validace schema_version 1;
- druhá obrana proti world-truth klíčům na straně Alua;
- vlastní SQLite kognitivní persistence;
- session transition s resetem krátkodobého observation cursoru;
- dlouhodobé epizody bez ukládání target_ref;
- statistika známých appearance_id bez přiřazení významu;
- bootstrap kognitivní cyklus observation -> memory -> decision -> ActionRequest;
- konzervativní první policy používající pouze wait;
- deterministické client_action_id pro idempotentní retry;
- CLI doctor, status a run;
- automatické unit/contract testy;
- statický audit hranic;
- GitHub CI.

Nehotovo:
- plnohodnotná working memory;
- evidence-based belief store;
- needs a goals;
- aktivní explorace move/look/manipulate;
- outcome attribution z budoucích observations;
- planner;
- učení dovedností;
- end-to-end test se skutečným persistentním AI tělem v AluaWorld.

Starý Lua kód zůstává v repozitáři jako historický funkční prototyp. Nesmí se dále rozšiřovat jako hlavní mozek.

## Rychlý start

    python -m venv .venv
    .venv/bin/pip install -e .
    cp .env.example .env

Nastav environment proměnné z .env a potom:

    .venv/bin/python -m alua doctor
    .venv/bin/python -m alua status
    .venv/bin/python -m alua run --once
    .venv/bin/python -m alua run

Podrobnosti jsou v docs/OPERATIONS_TERMUX.md.

## Neměnné hranice

1. Alua AI nemá přímou závislost na Luanti.
2. Jediné runtime spojení se světem vede přes Agent API AluaBridge.
3. Bridge nevlastní kognici a Alua nevlastní fyziku světa.
4. Význam neznámých věcí vzniká učením, ne převodem technických ID.
5. target_ref je krátkodobý handle, ne identita objektu.
6. ACK akce není fyzický výsledek; následek se poznává až z budoucích vjemů.
7. Kognitivní paměť musí přežít restart AI a nesmí být uložená v Bridge.
8. Každé budoucí naučené tvrzení musí mít evidenci, confidence a možnost opravy.
9. Zásadní změna není hotová bez testu a dokumentace.

## Dokumentace

Nejdůležitější dokument pro nový chat:
- docs/PAMET_PRO_NOVY_CHAT.md

Dále:
- docs/PROJECT_VISION_AI.md
- docs/ARCHITECTURE.md
- docs/BRIDGE_CONTRACT.md
- docs/PERCEPTION_AND_BELIEFS.md
- docs/MEMORY_MODEL.md
- docs/LEARNING_AND_DECISION.md
- docs/REPOSITORY_BOUNDARIES.md
- docs/SECURITY_AND_DATA_POLICY.md
- docs/ROADMAP.md
- docs/TESTING.md
- docs/OPERATIONS_TERMUX.md
- docs/WORKING_RULES_FOR_FUTURE_CHATS.md
- docs/IMPLEMENTATION_LOG_AI.md
- docs/DECISIONS.md
- CHANGELOG.md

## Historický prototyp

Soubory init.lua, npc.lua, commands.lua a core/ pocházejí z období, kdy byla Alua navržena jako Luanti companion mod. Jsou důležité jako historie a referenční prototyp, ale nejsou cílovou architekturou nové Alua AI.

## Licence

MIT.
