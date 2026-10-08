# Implementační deník Alua AI

## 2026-10-07 – Cognitive Core V5 po field testu slepé uličky

Reálný běh ukázal zásadní omezení V2/V3/V4: lokální critic poznal nulový progress a uměl reorientovat, ale agent si nepamatoval, kudy do slepé větve přišel. Výsledkem bylo zmatené lokální rozhlížení místo smysluplného návratu.

Implementován Cognitive Core V5:
- attention/surprise;
- scene + temporal integration;
- object permanence;
- route memory a explicitní remembered-route backtracking;
- relativní odometrie bez World XYZ;
- predictive model + prediction error;
- risk/self/causal models;
- metacognition;
- regulatory drives;
- active experiments;
- prospective memory a missions;
- consolidation/forgetting;
- concept formation a strategy transfer;
- social/testimony hooks;
- explainable cognitive state v decision rationale.

SQLite schema je v5 a před migrací starší DB vytváří backup. Nové higher-cognition persistence používá sanitized `cognitive_records`.

Cílem této změny není přidat další skriptované „když překážka, udělej X“, ale dát executive mechanismy, které poznají stagnaci, vzpomenou si na vlastní cestu, porovnají alternativy a učí se z prediction error.

Autoritativní popis: `docs/COGNITIVE_CORE_V5.md`.


## 2026-10-07 – field fix: move success nebyl skutečný navigační pokrok

Po nasazení V2/V3 se v živém testu objevila dlouhá série `move`, ale tělo se drželo kolem jedné kostky. World přitom hlásil úspěch.

Oprava proběhla na obou stranách kontraktu:
- World měří projected progress vůči intended direction a rozlišuje `partial_effect`;
- Alua zachovává graded progress/slip;
- motor success, goal evidence, skills a topology používají stejný přísnější success invariant;
- critic hledá low-progress maneuver stagnation;
- escape plan fyzicky změní yaw pomocí `reorient_escape`;
- dlouhá kvalitní chůze už není sama o sobě action stereotype.

Současně byl nalezen a ve Worldu opraven zrcadlený left/right vision basis proti locomotion basis.

Detail: `docs/INCIDENT_2026-10-07_ONE_BLOCK_BOUNCE.md`.


## 2026-10-07 – Adaptive Cognition V3

Po V2 byla implementována druhá část principů vytěžených z referenčních agentů: dlouhodobé cost evidence, trajectory replay a evidence-driven utility.

Přidáno:
- `utility.py`: adaptive goal ranking bez předprogramované sémantiky;
- `topology.py`: persistentní sensory-only perceptual places a transitions;
- schema v4 s `belief_evidence`, `perceptual_places`, `perceptual_transitions`;
- LocalNavigator přijímá persistentní maneuver penalties;
- úspěšný `look` invaliduje staré egocentrické sektory před ingestem nového view;
- `session_episodes()` + sensory replay;
- `alua benchmark` jako offline acceptance gate.

Tato změna záměrně nerozšiřuje Bridge ani World a zachovává stávající embodied kontrakt.


## 2026-10-07 – Cognitive Architecture V2 podle open-source reference auditu

Po stabilizaci embodied loopu nebyl další krok řešen další sérií lokálních `look/move` záplat. Byl proveden referenční audit Voyager, Odyssey, luanti-voyager, Mineflayer Pathfinder, Baritone, Craftium, MineStudio, OpenHA a Mindcraft.

Do Alua byly implementovány obecné principy, které neporušují epistemickou hranici:
- egocentrický world model místo skryté globální mapy;
- cost-based receding-horizon navigation;
- self-critic nad vlastní action/outcome historií;
- hierarchy goal -> composite skill -> bounded plan -> controller -> primitive action;
- explicitní replan;
- gating naučených primitive skillů čerstvým perceptem;
- offline trajectory metrics;
- information scan podle uncertainty místo pevného časového patternu.

Stávající Bridge contract, SQLite beliefs/episodes, target_ref pravidla a future-observation learning byly zachovány.

Implementace: `world_model.py`, `navigation.py`, `critic.py`, `skill_graph.py`, `planning.py`, `executive.py`, `evaluation.py`.


## 2026-10-07 – druhý field fix: globální scan gate

Po nasazení prvního brain auditu živý log stále ukázal několik po sobě jdoucích `look`. Důvodem bylo, že anti-loop logika byla oddělená pro `scan_obstacle`, `scan_recovery` a `scan_periodic`; různé scan kindy se tedy mohly střídat. Současně se používal `last_sequence` z dlouhodobých goal stats, přestože observation sequence se při nové World session resetuje.

Runtime nyní načítá poslední Bridge přijatý goal pouze z aktuální session a curriculum používá jednu globální scan gate pro všechny scan kindy. Po libovolném scanu musí přijít non-scan goal, než může vzniknout další `look`.


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


## 2026-10-08 – Cognitive Core V5 – kompletní implementační návaznost

Důvod změny: field chování ukázalo, že V2/V3 uměly lokálně detekovat stagnaci a přepínat manévr, ale agent neměl dostatečně explicitní paměť vlastní cesty a návratovou strategii. Ve slepé větvi proto mohl stále lokálně přeplánovávat bez skutečného „vrať se po cestě, kterou jsem právě prošel“.

Implementace byla provedena po vrstvách:

1. **Persistence** – schema v5, automatický pre-v5 backup a namespaced `cognitive_records`.
2. **Pozornost** – salience, novelty, surprise a uncertainty bez vytváření World truth.
3. **Object permanence** – bounded tracky opaque appearances i po krátkém zmizení.
4. **Spatial memory** – route stack, heading, dead-end evidence a remembered-route backtracking.
5. **Relative odometry** – interní X/Z pouze z vlastních ověřených pohybů, s uncertainty.
6. **Prediction** – context+action -> expected progress/success.
7. **Risk** – kontextový risk z failure, slip, low progress a damage.
8. **Self model** – empirická úspěšnost a effort vlastních capabilities.
9. **Causal learning** – interventional hypotheses z vlastních actions a budoucích bodily/motor outcomes.
10. **Metacognition** – rozlišení stagnation, loop, uncertainty a model prediction error.
11. **Drives** – safety, homeostasis, curiosity, frustration a exploration.
12. **Active experiments** – nízkorizikové informační experimenty přes existující goal/action pipeline.
13. **Prospective memory** – persistentní budoucí záměry.
14. **Missions** – přerušitelné long-horizon cíle s fresh-perception replan po každé akci.
15. **Scene + temporal model** – multisensory context a recurrence evidence.
16. **Concept formation** – abstrakce pouze ze společných evidence-backed affordances.
17. **Strategy transfer** – slabý meta-learning prior, který nikdy nepřebíjí fresh sensory evidence.
18. **Consolidation** – trajectory summaries, confidence decay a concept formation.
19. **Social hooks** – testimony/trust/peer behavior pouze při explicitním social sensory kanálu.
20. **Runtime integration** – CognitiveCore vložen mezi perception/world model a goal arbitration; future outcomes aktualizují prediction/risk/self/causal/strategy/spatial modely.
21. **Planner/policy integration** – přidány `spatial_backtrack` a `deliberate_navigation`.
22. **Explainability** – decision rationale dostává `cognitive_state`.
23. **CLI** – přidán read-only `alua cognition-status`.
24. **Regression testy** – přidány nové testy a zachovány všechny staré invarianty.
25. **CI incident** – aktivní experiment původně vytvořil nový goal key `experiment:touch:...`; existující runtime testy správně zachytily fragmentaci evidence. Opravena implementace na kanonický `inspect:<appearance>`, testy nebyly oslabeny.
26. **Dokumentace** – aktualizovány všechny autoritativní projektové texty a vytvořen samostatný kompletní auditní deník.

Nejpodrobnější kroková evidence včetně migration, runtime lifecycle, testů, CI incidentu, deploymentu, rollbacku a Definition of Done:
`docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.

Architektonický popis:
`docs/COGNITIVE_CORE_V5.md`.

Důležité: CI green neznamená field acceptance. V5 musí ještě v živém AluaWorld potvrdit skutečný návrat ze slepé větve, stabilitu dlouhého běhu a přijatelné CPU/RAM/DB chování.
