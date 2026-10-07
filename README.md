# Alua AI

Alua je samostatný kognitivní systém pro autonomní agenty žijící v AluaWorld.

Architektura má tři autority:

    AluaWorld -> AluaBridge -> Alua AI
    Alua AI   -> AluaBridge -> AluaWorld

- AluaWorld vlastní fyzický svět, tělo, smysly, fyziku a skutečné následky akcí.
- AluaBridge vlastní bezpečný localhost transport, session, bounded fronty, target_ref, lease a ACK.
- Alua vlastní kognici: pracovní a dlouhodobou paměť, beliefs, rozhodování a učení.

Alua nesmí číst mapu, interní názvy nodů, materiály, biomy, recepty, ObjectRef ani administrátorská data. Význam věcí si vytváří pouze ze zkušenosti.

## Aktuální stav

Implementováno:
- samostatný Python 3.12+ runtime;
- loopback-only AluaBridge klient;
- per-agent token pouze z prostředí;
- striktní schema_version 1 validace a druhá world-truth obrana;
- SQLite kognitivní schema v3;
- automatická záloha existující DB před migrací v1/v2 -> v3;
- epizodická paměť bez target_ref;
- bounded WorkingMemory posledních 32 frame v RAM;
- krátkodobé vazby target_ref <-> appearance_id pouze v RAM;
- decisions, expectations a beliefs;
- session recovery s invalidací starých pending world akcí;
- motorický outcome attribution podle Bridge action sequence;
- evidence-based confidence ze support/contradiction;
- bezpečná autonomní ExplorationPolicy;
- Cognitive Architecture V2: egocentrický world model, behavior critic, hierarchical skill graph, bounded planner a receding-horizon local navigator;
- information scan řízený skutečnou nejistotou lokálního modelu místo pevného časového vzoru;
- learned-skill gating proti aktuálním překážkám a stagnaci;
- offline trajectory evaluator přes `alua evaluate`;
- move a look podle kontraktu, který vlastní AluaWorld;
- nedestruktivní touch blízkého neznámého cíle;
- vnímání vlastních částí těla a volba volné levé/pravé ruky pro touch;
- ústup při damage signálu;
- CLI doctor, status a run;
- unit/contract testy a GitHub CI;
- Termux E2E smoke helper.

AluaWorld už obsahuje persistentní fyzické tělo alua:1 a motorický sensory channel. AluaBridge má body-aware Luanti adaptér.

Od 2026-10-07 je celý embodied loop ověřen v reálném běhu na Android/Termux: Alua přijímá observations, vytváří decisions, posílá actions, fyzické tělo je vykonává a pozdější sensory outcome vytváří beliefs a skills. Ověřený stav dosáhl 482 episodes, 235 decisions, 9 beliefs, 12 skills a 6 reusable skills. Podrobnosti jsou v `docs/E2E_RUNTIME_2026-10-07.md`.

Následný audit mozku odhalil a opravil deterministický `look` loop, ztrátu zrakového perceptu po expiraci `target_ref` a několik kontextových chyb reusable skills. Přesné nálezy a invarianty jsou v `docs/AUDIT_BRAIN_2026-10-07.md`.

Záměrně zatím není autonomně zapnuto:
- pickup;
- push;
- break_object;
- fyzické needs/metabolismus;
- sociální chování.

World tyto fyzické manipulace může umět, ale mozek je nezačne používat bez naučeného risk/utility modelu.

## Rychlý start

    python -m venv .venv
    .venv/bin/pip install -e .
    cp .env.example .env

Po nastavení environment proměnných:

    .venv/bin/python -m alua doctor
    .venv/bin/python -m alua status
    .venv/bin/python -m alua evaluate
    .venv/bin/python -m alua run

Pro skutečný lokální test celého řetězce:

    bash tools/e2e_smoke_termux.sh

Smoke test vyžaduje aktivní session, observations, alespoň jedno rozhodnutí a alespoň jeden belief vzniklý z pozdějšího sensory outcome.

## Neměnné hranice

1. Alua nemá přímou závislost na Luanti.
2. Jediné runtime spojení se světem vede přes Agent API AluaBridge.
3. Bridge nevlastní kognici a Alua nevlastní fyziku světa.
4. Význam neznámých věcí vzniká učením, ne převodem technických ID.
5. target_ref je krátkodobý handle, ne identita objektu.
6. ACK akce není fyzický výsledek.
7. Fyzický outcome se učí až z budoucí observation.
8. Kognitivní paměť musí přežít restart AI.
9. Empirický belief musí být opravitelný další zkušeností.
10. Zásadní změna není hotová bez testu a dokumentace.

## Dokumentace

Nejdůležitější dokument pro nový chat:
- docs/PAMET_PRO_NOVY_CHAT.md

Dále:
- docs/E2E_RUNTIME_2026-10-07.md
- docs/AUDIT_BRAIN_2026-10-07.md
- docs/COGNITIVE_ARCHITECTURE_V2.md
- docs/OPEN_SOURCE_REFERENCE_AUDIT_2026-10-07.md
- docs/PROJECT_VISION_AI.md
- docs/ARCHITECTURE.md
- docs/BRIDGE_CONTRACT.md
- docs/IDENTITY_SESSION_RECOVERY.md
- docs/PERCEPTION_AND_BELIEFS.md
- docs/MEMORY_MODEL.md
- docs/LEARNING_AND_DECISION.md
- docs/EMBODIED_LEARNING_V1.md
- docs/BODY_SCHEMA.md
- docs/REPOSITORY_BOUNDARIES.md
- docs/SECURITY_AND_DATA_POLICY.md
- docs/ROADMAP.md
- docs/TESTING.md
- docs/AUDIT_2026-10-06.md
- docs/OPERATIONS_TERMUX.md
- docs/WORKING_RULES_FOR_FUTURE_CHATS.md
- docs/IMPLEMENTATION_LOG_AI.md
- docs/DECISIONS.md
- CHANGELOG.md

## Historický prototyp

Soubory init.lua, npc.lua, commands.lua a core/ pocházejí z období, kdy byla Alua Luanti companion mod. Zůstávají jako historie, nový Python runtime na nich nezávisí.

## Licence

MIT.
