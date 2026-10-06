# Paměť projektu Alua AI pro nový chat

Aktualizováno: 2026-10-06.

## Co projekt je

Alua je samostatný mozek autonomního agenta pro AluaWorld.

Tři repozitáře:
- AluaWorld = fyzický svět, tělo, smysly, fyzika a následky;
- AluaBridge = bezpečný most a transport;
- Alua = kognice, paměť, beliefs, rozhodování a učení.

## Aktuální architektura

Původní Lua companion je historický prototyp.

Aktuální mozek:
- není Luanti mod;
- neběží uvnitř World procesu;
- je samostatná Python aplikace;
- používá pouze AluaBridge Agent API.

## Stav Alua

Existuje:
- Python runtime;
- BridgeClient;
- strict schema/perception boundary;
- SQLite schema v2;
- automatický backup při migraci v1 -> v2;
- episodes, appearance_stats, decisions, expectations, beliefs a session_events;
- WorkingMemory max 32 frame;
- session recovery;
- motor outcome attribution;
- evidence-based confidence;
- aktivní ExplorationPolicy;
- testy a CI;
- E2E Termux smoke helper.

## Embodied V1

Cyklus:
1. observation;
2. WorkingMemory;
3. přiřazení motorického source_sequence k dřívější akci;
4. belief update až z budoucího smyslového následku;
5. další bezpečná akce pouze bez pending expectation.

Policy:
- damage -> ústup;
- nový blízký cíl -> touch;
- blízká překážka -> look;
- periodický scan;
- jinak pomalý move.

Automatický pickup/push/break je vypnutý.

## target_ref

target_ref:
- je krátkodobý opaque handle;
- existuje pouze v aktuálním RAM PerceptionFrame a odchozím ActionRequest;
- není dlouhodobá identita;
- Store jej odstraňuje z epizod, decisions i expectations.

## Outcome

Bridge ACK není fyzický výsledek.

World action_result je sanitizován do motorického sensory eventu se source_sequence, success_signal, feedback_signal, effort_signal a age_fraction. Teprve tento budoucí vjem může změnit belief.

## Stav Worldu a Bridge

AluaWorld:
- má persistentní LuaEntity tělo alua:1;
- tělo má kolizi, gravitaci, move/look kontrakt, omezenou sílu a motor feedback;
- fyzická manipulace ověřuje skutečný dosah těla.

AluaBridge:
- má World/Agent API;
- body-aware aw_bridge adaptér;
- session vzniká jen pro skutečně aktivní tělo;
- má instalační helper pro synchronizaci adaptéru do AluaWorld.

## E2E smoke

Po spuštění Worldu a Bridge:

    bash tools/e2e_smoke_termux.sh

Úspěch vyžaduje session, observation epizodu, decision a learned belief.

## Bezprostřední další práce

1. skutečný E2E smoke na telefonu;
2. restart/recovery test všech tří procesů;
3. metabolismus/needs ve Worldu;
4. goal/utility vrstva v Alua;
5. risk learning;
6. multi-step planner;
7. až potom destruktivnější autonomní manipulace.
