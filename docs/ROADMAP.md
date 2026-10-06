# Roadmapa Alua AI

Roadmapa určuje pořadí závislostí, ne kalendář.

## Fáze A – dokumentační a kontraktní základ

Stav: hotovo 2026-10-06.

- role Alua / Bridge / World;
- Bridge Agent API kontrakt;
- kognitivní architektura;
- memory model;
- belief boundary;
- security/data policy;
- identity/session/recovery contract;
- testing plan;
- provozní plán pro Termux;
- pravidla dalších chatů;
- projektová paměť;
- datovaný audit skutečné implementace.

## Fáze B – samostatný runtime

Stav: implementováno / čeká na skutečný end-to-end test.

Hotovo:
- Python package;
- config z environmentu;
- CLI;
- SQLite schema;
- BridgeClient;
- čtení session;
- polling observations;
- perzistence last processed sequence;
- deterministické client_action_id;
- idempotentně opakovatelný ActionRequest;
- graceful KeyboardInterrupt;
- reconnect/backoff pro dočasnou nedostupnost;
- doctor/status/run;
- unit testy;
- contract test HTTP klienta;
- CI;
- statický audit hranic.

Zbývá:
- ověřit proti skutečně běžícímu AluaBridge;
- dlouhodobý restart test na telefonu;
- reconciliation decisions při změně session;
- migrační framework před schema v2.

## Fáze C – perception + working memory

Stav: částečně implementováno.

Hotovo:
- strict observation validation;
- druhá rekurzivní world-truth kontrola;
- PerceptionFrame;
- oddělení persistentní části a ephemeral target_ref;
- appearance_id familiarity statistics.

Zbývá:
- plná bounded working memory;
- novelty tracking přes více modalit;
- časové události a sensory gaps;
- aktivní target lifecycle;
- explicitní uncertainty representation;
- potvrdit stabilitu appearance_id přes session nebo zavést signature epoch.

## Fáze D – episodic memory + beliefs

Stav: základ epizod implementován.

Hotovo:
- dlouhodobá epizoda očištěná od target_ref;
- session + simulation time + observation sequence;
- appearance evidence.

Zbývá:
- belief store;
- confidence;
- contradiction handling;
- decay;
- evidence links;
- learned transition statistics.

## Fáze E – první autonomní rozhodování

Stav: bootstrap pouze.

Hotovo:
- decision persistence;
- rationale;
- bezpečná wait policy;
- ActionRequest přes Bridge.

Zbývá:
- exploration policy;
- need inputs;
- goal candidates;
- utility scoring;
- bounded planner;
- pending expectations;
- outcome attribution;
- aktivní move/look/interact/manipulate po dokončení body kontraktu.

## Fáze F – end-to-end AluaWorld

- jedno persistentní tělo;
- Bridge V1;
- Alua runtime;
- dlouhodobý test;
- restarty všech tří komponent;
- žádný přímý Luanti přístup;
- replay rozhodnutí;
- měření CPU/RAM/DB růstu.

## Fáze G – učení dovedností

- procedurální memory;
- vícekrokové postupy;
- přeplánování;
- generalizace podobných situací;
- risk learning;
- utility learning.

## Fáze H – jazyk a sociální chování

Až po stabilní neverbální kognici:
- světový komunikační kanál;
- učení symbolů;
- předávání informací mezi Alua;
- důvěra a provenance sdělení;
- žádná telepatická společná DB.

## Fáze I – populace

- více procesů/agentů;
- supervisor;
- oddělené DB;
- výkonové budgety;
- dlouhodobé experimenty;
- reprodukce až podle samostatného biology kontraktu.

## Co se nesmí označit za hotové

Pouhá existence třídy nebo tabulky nestačí.

Každá fáze vyžaduje:
- runtime chování;
- persistenci, pokud ji potřebuje;
- automatický test;
- pozorovatelný výsledek;
- dokumentaci.
