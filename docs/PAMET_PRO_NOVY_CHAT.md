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

Od 2026-10-06:
- nový mozek není Luanti mod;
- neběží uvnitř World procesu;
- nevolá core.*;
- je samostatná Python aplikace;
- jediný runtime vstup/výstup je AluaBridge Agent API.

Starý Lua prototyp se zatím nemaže, protože je součást historie a může sloužit jako reference.

## Stav nové implementace

Existuje:
- pyproject.toml;
- src/alua Python package;
- Config s vynuceným loopback Bridge URL;
- BridgeClient;
- schema validation;
- PerceptionFrame;
- SQLite Store;
- session transitions;
- epizody bez target_ref;
- appearance familiarity;
- decision persistence;
- bootstrap wait policy;
- Runtime.step a run_forever;
- CLI doctor/status/run;
- testy;
- boundary audit;
- GitHub CI.

Bootstrap policy zatím neposílá move/look/manipulate. Je to záměr: AluaWorld ještě nemá zdokumentované a end-to-end ověřené parametry persistentního AI body adapteru. Mozek nesmí parametry těla vymyslet sám.

## Poslední ověřený audit

Dne 2026-10-06 byl proti commitu ab0d119 ověřen skutečný runtime a zelené GitHub CI.

Audit je v:
- docs/AUDIT_2026-10-06.md

Přesná pravidla identity, session a restartů:
- docs/IDENTITY_SESSION_RECOVERY.md

Hlavní otevřené technické body:
- skutečný end-to-end běh ještě chybí;
- před schema v2 je nutný migrační framework;
- před aktivními akcemi je nutná reconciliation decisions při změně session;
- belief store a outcome attribution ještě nejsou implementované;
- stabilita appearance_id napříč session musí být smluvně potvrzena.

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

## Nejvyšší pravidlo

Alua nesmí znát world truth, kterou sama nevnímala nebo neodvodila.

## target_ref

Je krátkodobý opaque handle.
V runtime PerceptionFrame může krátce existovat v RAM.
Do persistentního percept_json se odstraňuje.

## Action outcome

Přijetí akce nebo ACK není fyzický úspěch.
Výsledek se bude učit až z budoucí observation.

## Technologie V1

- Python 3.12+;
- standard library;
- SQLite;
- jeden agent na jeden proces;
- jeden DB soubor na agenta;
- žádný povinný externí LLM;
- důraz na replay, provenance a explainability.

## Bezprostřední další práce

1. ověřit skutečný AluaBridge + Alua runtime;
2. v AluaWorld vytvořit persistentní AI body adapter s přesným move/look kontraktem;
3. udělat restart/recovery E2E scénář;
4. doplnit SQLite migrace;
5. bounded working memory;
6. belief store + evidence;
7. pending expectations a outcome attribution;
8. aktivní exploraci;
9. až potom planner.
