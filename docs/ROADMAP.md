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
- testing plan;
- provozní plán pro Termux;
- pravidla dalších chatů;
- projektová paměť.

## Fáze B – samostatný runtime

- Python package;
- config z environmentu;
- CLI;
- SQLite schema a migrations;
- BridgeClient;
- čtení session;
- polling observations;
- perzistence last processed sequence;
- idempotentní submit action;
- graceful shutdown;
- health/doctor příkaz;
- unit testy a CI.

Podmínka dokončení:
Alua proces se připojí k testovacímu Bridge, bezpečně přečte observation, přežije restart a umí odeslat wait/look bez přímé vazby na World.

## Fáze C – perception + working memory

- normalizace observations;
- bounded working memory;
- session transition handling;
- target_ref lifecycle;
- novelty tracking;
- perceptual signatures;
- čisté testy proti world-truth contamination.

Podmínka:
Alua umí popsat pouze to, co obdržela jako vjem, a nepřidá skrytou sémantiku.

## Fáze D – episodic memory + beliefs

- epizody;
- evidence links;
- belief store;
- confidence;
- contradiction handling;
- decay;
- jednoduché learned transition statistics.

Podmínka:
opakovaná zkušenost mění přesvědčení a rozporná zkušenost je umí opravit.

## Fáze E – první autonomní rozhodování

- exploration policy;
- need inputs;
- goal candidates;
- utility scoring;
- bounded planner;
- pending expectations;
- outcome attribution;
- decision trace.

Podmínka:
jedna Alua dokáže bez ručního příkazu provést cyklus pozoruj -> rozhodni -> jednej -> pozoruj následek -> uprav zkušenost.

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
