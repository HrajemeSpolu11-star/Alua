# Paměť projektu Alua AI pro nový chat

Aktualizováno: 2026-10-06.

## Co projekt je

Alua je samostatný mozek autonomního agenta pro AluaWorld.

Tři repozitáře:
- AluaWorld = fyzický svět, tělo, smysly, fyzika a následky;
- AluaBridge = bezpečný most a transport;
- Alua = kognice, paměť, cíle, plánování a učení.

## Kritická změna směru

Původní Alua z 2026-09-24 byla Luanti companion mod s npc.lua, commands.lua a core Lua základem.

Tento návrh je překonán.

Od 2026-10-06:
- nový mozek nebude Luanti mod;
- nebude běžet uvnitř World procesu;
- nebude volat core.*;
- bude samostatná Python aplikace;
- jediný runtime vstup/výstup je AluaBridge Agent API.

Starý Lua prototyp se zatím nemaže, protože je součást historie a může sloužit jako reference.

## Stav AluaBridge

Bridge V1 existuje a má:
- localhost HTTP;
- per-agent token;
- session;
- observations;
- actions;
- target_ref;
- idempotentní client_action_id;
- lease/ACK;
- SQLite transport state;
- bezpečnostní limity.

Agent endpointy:
- GET /v1/agent/session
- GET /v1/agent/observations
- POST /v1/agent/actions

Povolené action types:
- wait;
- move;
- look;
- interact;
- manipulate.

## Nejvyšší pravidlo

Alua nesmí znát world truth, kterou sama nevnímala nebo neodvodila.

Zakázané zkratky zahrnují:
- node_name;
- item_name;
- material;
- biome;
- catalog_id;
- internal_id;
- absolute_position;
- přímý World katalog;
- admin telemetry.

## target_ref

Je krátkodobý opaque handle.
Není objektová identita.
Nesmí do long-term memory jako ID věci.

## Action outcome

Přijetí akce nebo ACK není fyzický úspěch.
Výsledek se učí až z budoucí observation.

## Cílová technologie V1

- Python 3.12+;
- standard library pokud rozumně stačí;
- SQLite;
- jeden agent na jeden proces;
- jeden DB soubor na agenta;
- žádný povinný externí LLM;
- bounded working memory;
- malý deterministický planner;
- důraz na replay a explainability.

## Co je už hotové v tomto repozitáři

- dokumentační základ nové architektury;
- starý funkční Lua companion prototyp;
- historie původních architektonických úvah.

## Co se má implementovat jako první

1. pyproject + src/alua package;
2. config;
3. schema;
4. SQLite store + migrations;
5. BridgeClient;
6. runtime session/poll loop;
7. safe wait/look policy;
8. unit/contract testy;
9. CI;
10. až potom perception/memory/belief learning.

## Co nedělat jako první

- jazykový model;
- neuronové sítě;
- multi-agent supervisor;
- reprodukci;
- sociální systém;
- crafting knowledge;
- velký planner.

Nejdřív musí být spolehlivý percepce-paměť-akce loop jedné Alua.
