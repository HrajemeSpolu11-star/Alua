# Implementační deník Alua AI

## 2026-10-07 – audit mozku po prvním E2E běhu

Živý World log po úspěšném propojení odhalil dlouhou sérii `look`. Audit ukázal, že nešlo o naučenou strategii, ale o starvation chybu intrinsic curriculum: po dostatečném počtu exploration failures mohl `scan_recovery` s prioritou kolem 0.84 trvale vítězit nad exploration kolem 0.50. Stejný vzor mohl vzniknout i u centrální překážky.

Oba scan cíle jsou nyní edge-triggered vůči novějšímu exploration pokusu, historické failures samy o sobě recovery neudržují a následný pohyb u centrální překážky používá opatrný boční bypass. Scan direction už není parity-based.

Audit současně opravil perception/skill chyby: ray bez čerstvého `target_ref` zůstává vizuálním perceptem, scan akce se nepromují do procedural memory, touch skill znovu váže aktuálně volnou ruku a generic explore skill se proti aktuální překážce nepoužije.

Detail: `docs/AUDIT_BRAIN_2026-10-07.md`.


## 2026-10-07 – první skutečně uzavřený embodied loop

Mobilní běh potvrdil celý řetězec od observation až po fyzický outcome a learning. Po opravě World body adapteru začal `last_observation_sequence` růst ze 0 na stovky frame. Druhý runtime blocker byl `409 target_expired`: krátkodobý opaque handle mohl korektně vypršet, ale Alua tento stav považovala za fatální.

Runtime nyní stale target decision označí jako `stale_target`, nevytvoří expectation ani falešný goal outcome a pokračuje dalším čerstvým vjemem. Bridge zároveň expirovaný handle z observation odstraňuje a World má bezpečnostní TTL rezervu.

Po opravách se `alua:1` skutečně autonomně pohybovala ve světě. World potvrzoval úspěšné `look` sequence přes 100 a kognitivní stav obsahoval 482 episodes, 235 decisions, 9 beliefs, 10 goals, 12 skills a 6 reusable skills. Tím je transportní/embodied E2E blocker uzavřen.

Kompletní reprodukce, diagnostika a runbook: `docs/E2E_RUNTIME_2026-10-07.md`.


Tento dokument doplňuje changelog. Changelog říká co se změnilo; tento deník zachycuje technický důvod a návaznosti.

## 2026-10-06 – oddělení mozku od světa

Po dokončení AluaBridge V1 byl zkontrolován původní repozitář Alua.

Zjištění:
- aktuální kód byl Luanti companion;
- entity přímo četla PlayerRef, pozice a okolní objekty;
- diagnostický scan četl node_name a absolutní pozici;
- modulární core existoval, ale skutečné perception, memory, world model, needs, goals, planner a learning ne;
- původní dokumentace správně požadovala perception boundary, ale technické umístění mozku uvnitř Luanti už neodpovídalo nové třírepo architektuře.

Rozhodnutí:
- Alua je externí kognitivní proces;
- Bridge je jediný runtime port do světa;
- původní Lua companion se zachová jako historický prototyp;
- nový runtime je v Pythonu a má vlastní SQLite kognitivní paměť.

## 2026-10-06 – dokumentační základ

Podle standardu AluaWorld vznikla projektová vize, architektura, Bridge kontrakt, perception/belief model, memory model, learning/decision model, repository boundaries, security policy, roadmap, testing, Termux provoz, working rules, paměť pro další chat a ADR.

## 2026-10-06 – první Python runtime

Implementován vertikální základ:
- strict loopback Config;
- BridgeClient bez externích knihoven;
- schema validator;
- druhá epistemická kontrola;
- PerceptionFrame oddělující ephemeral target_ref od persistentních dat;
- SQLite runtime_state, episodes, appearance_stats, decisions a session_events;
- session reset observation cursoru bez ztráty dlouhodobé zkušenosti;
- deterministické client_action_id;
- bootstrap policy;
- jeden runtime cycle;
- reconnect/backoff;
- CLI;
- unit/HTTP contract testy;
- static boundary audit;
- GitHub Actions.

Důležité rozhodnutí:
první policy používá pouze wait. Přímé move/look/manipulate nebude zapnuto, dokud AluaWorld nebude mít persistentní AI tělo a přesný parametrický kontrakt těchto akcí. To zabraňuje tomu, aby si Alua repo samo vytvořilo skrytou fyziku těla.

## 2026-10-06 – audit, identita a recovery

Po zeleném CI byl nový runtime porovnán s dokumentací.

Potvrzeno:
- loopback-only Bridge konfigurace;
- Agent token pouze v prostředí;
- síť pouze přes bridge_client.py;
- druhá world-truth kontrola;
- odstranění target_ref z dlouhodobé persistence;
- samostatná SQLite kognitivní paměť;
- bezpečný bootstrap pouze přes wait.

Doplněno:
- datovaný audit docs/AUDIT_2026-10-06.md;
- kontrakt docs/IDENTITY_SESSION_RECOVERY.md;
- ADR pro dlouhodobé agent_id a session transition.

Audit zároveň záměrně ponechal jako otevřené blokery:
- skutečný E2E běh;
- DB migrace;
- reconciliation decisions po změně session;
- belief/outcome vrstvu;
- ověření stability appearance_id přes session.


## 2026-10-06 – embodied learning V1

Po dokončení persistentního těla a motorického sensory kontraktu v AluaWorld byla odstraněna wait-only brzda.

Implementováno:
- SQLite schema v2 a automatický backup před migrací;
- expectations korelované Bridge action_sequence;
- beliefs se support/contradiction a confidence;
- invalidace starých pending world akcí při změně session;
- bounded WorkingMemory;
- target_ref association pouze v RAM;
- motor outcome attribution;
- první learning rules;
- bezpečná ExplorationPolicy pro move/look/touch;
- E2E smoke helper pro skutečný tříprocesový běh.

Destruktivní pickup/push/break nejsou v autonomní policy používány. Nejdříve musí vzniknout risk/utility model.

## 2026-10-06 – oprava priority aktivního ověřování

CI odhalilo, že nová evidence-driven kontrola známého, ale nejistého objektu byla v reálném výběru cílů přebita obecnou prioritou `scan_obstacle`. Nešlo o transportní ani world kontrakt, ale o pořadí intrinsic goals. Ověřovací `inspect_object` má nyní po první a druhé zkušenosti dočasně vyšší prioritu; po třetím pokusu dál zaniká. Tím zůstává chování bounded a agent se nezacyklí v dotýkání stejného objektu.

## 2026-10-06 – rozhodování konkrétní rukou

Po zavedení autoritativní morfologie ve Worldu byla ExplorationPolicy rozšířena o bezpečné čtení `body_schema`. Pro nedestruktivní touch vybere přítomnou, touch-capable a volnou ruku. Test pokrývá výchozí pravou ruku i přepnutí na levou při obsazené pravé. Fyzický výsledek se dál učí pouze z budoucí observation.
