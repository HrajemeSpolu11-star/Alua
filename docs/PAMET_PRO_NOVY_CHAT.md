# Paměť projektu Alua AI pro nový chat

## Finální validace Cognitive Core V5 – 2026-10-08

Cognitive Core V5 je sloučený do `main`.

Ověřený merge commit:
- `2da7e5c08e961e21e1e4ece36e54a1fe53339dcb`;
- short SHA `2da7e5c`;
- message `Cognitive Core V5: memory, prediction, metacognition and backtracking (#10)`.

Finální GitHub Actions na `main`:
- 121 unit/regression testů;
- všechny prošly;
- `tools/audit_repo.py` -> `AUDIT OK`;
- syntax kontrola Termux E2E helperu prošla.

SQLite schema je nyní v5. První otevření existující v4 DB po pullu provede migraci se zálohou před změnou.

V5 je implementovaná vyšší kognitivní architektura, nikoli tvrzení o hotové AGI. Aktivně běží attention, scene/temporal model, object permanence, route memory/backtracking, relative odometry, prediction/risk/self/causal models, metacognition, drives, experiments, missions, consolidation, concepts a strategy transfer. Social/testimony/peer vrstvy potřebují explicitní budoucí World sensory data, než mohou skutečně řídit sociální chování.


Aktualizováno: 2026-10-07.


## Cognitive Core V5 – aktuální kognitivní vrstva

Field test ve slepé větvi ukázal, že agent uměl poznat špatný motorický progress, ale neuměl použít vlastní historii k návratu. V5 proto přidává vyšší kognitivní vrstvu v repu **Alua**, nikoli hardcoded řešení ve Worldu.

Klíčové moduly:
- `attention.py` – salience/surprise/uncertainty;
- `scene.py` + `temporal.py` – multisensory scene a recurrence;
- `object_memory.py` – object permanence;
- `spatial_memory.py` – route stack, dead-end detection, remembered backtracking, relative odometry;
- `predictive.py` – action prediction + counterfactual ranking;
- `risk.py`, `self_model.py`, `causal.py`;
- `metacognition.py` – stagnation/loop/model-error awareness;
- `drives.py` – regulatory priorities;
- `experiments.py` – bounded safe active experiments;
- `prospective.py` + `missions.py`;
- `concepts.py` + `strategy.py`;
- `consolidation.py`;
- `social.py` + future peer-model hooks;
- `cognition.py` – orchestrator.

SQLite schema je **v5**. První Store-opening command po update vytvoří pre-v5 backup starší DB a zachová staré episodes/beliefs/goals/skills.

Nový diagnostický příkaz:

```bash
.venv/bin/python -m alua cognition-status
```

Autoritativní dokument: `docs/COGNITIVE_CORE_V5.md`.

Důležitý invariant: V5 stále nemá World XYZ, technické názvy item/node, skrytou mapu ani recepty. Návrat používá pouze vlastní route memory a perceptuální signatures.


## Navigační field fix – 2026-10-07

Po V2/V3 field testu se Alua pohybovala, ale odrážela se v malém prostoru. Nešlo pouze o planner problém.

Nalezeno:
- AluaWorld movement success byl příliš benevolentní a neověřoval směr postupu;
- left/right vision basis byl ve Worldu zrcadlený proti body locomotion;
- critic neuměl rozlišit kvalitní dlouhou chůzi od low-progress move loopu;
- escape plan neuměl reorientovat yaw.

Aktuální řešení:
- graded `progress_signal` / `slip_signal`;
- `partial_effect`;
- motor success od 55 % projected progress;
- maneuver-specific stagnation;
- `reorient_escape -> navigate_escape -> navigate_frontier`;
- scan gate respektuje každý physical look.

Pro správný field test je nutné aktualizovat **AluaWorld i Alua**. Bridge kontrakt se nemění.

## Adaptive Cognition V3 – 2026-10-07

Nad Cognitive V2 byla doplněna dlouhodobá adaptivní vrstva:
- `AdaptiveUtilityModel` rankuje intrinsic cíle podle vlastní evidence, uncertainty, novelty a damage;
- `PerceptualTopology` persistuje sensory-only place signatures a move transitions;
- LocalNavigator používá historické transition penalties;
- po úspěšném `look` se invaliduje starý egocentrický view frame;
- SQLite schema je v4 a přidává `belief_evidence`, `perceptual_places`, `perceptual_transitions`;
- beliefs mají dohledatelnou observation/decision provenance;
- `alua benchmark` umí offline sensory replay + behavior acceptance.

Existující DB se nemaže; před první migrací do v4 se automaticky vytvoří backup.

Autoritativní dokument: `docs/ADAPTIVE_COGNITION_V3.md`.


## Cognitive Architecture V2 – 2026-10-07

Po porovnání s Voyager, Odyssey, luanti-voyager, Mineflayer Pathfinder, Baritone, Craftium, MineStudio, OpenHA a Mindcraft byla nad funkční V1 přidána hierarchická vrstva bez bourání embodied kontraktu.

Nově existuje:
- egocentrický `EgocentricWorldModel`;
- cost-based `LocalNavigator`;
- `BehaviorCritic` pro loop/stagnation detection;
- data-only `SkillGraph` s composite behavior skills;
- `BoundedPlanner`;
- `ExecutiveController` pro plan lifecycle a replanning;
- uncertainty-driven information scan;
- learned-skill gating proti čerstvému perceptu;
- `Store.session_trace()` a `alua evaluate` pro behaviorální benchmark.

Session-local V2 stav se při změně World session resetuje. Episodes, beliefs a learned skills se zachovávají.

Autoritativní dokumenty:
- `docs/COGNITIVE_ARCHITECTURE_V2.md`;
- `docs/OPEN_SOURCE_REFERENCE_AUDIT_2026-10-07.md`.


## Co projekt je

Alua je samostatný mozek autonomního agenta pro AluaWorld.

## Audit chování po prvním E2E běhu – 2026-10-07

Dlouhá série `look` v živém logu byla potvrzena jako chyba rozhodovací vrstvy, nikoli jako smysluplná emergentní strategie. `scan_recovery` a `scan_obstacle` mohly trvale vyhladovět exploration. Oprava vyžaduje mezi dvěma scany skutečný exploration pokus a recovery se už neopírá pouze o historické failures.

Současně:
- vizuální percept přežije expiraci `target_ref`;
- scan actions nejsou reusable skills;
- touch skill nepersistuje konkrétní ruku;
- reusable explore skill neobchází aktuální obstacle check;
- context-specific strafe se nezobecňuje bez precondition modelu;
- distance 0.0 je korektně nejbližší.

Autoritativní audit: `docs/AUDIT_BRAIN_2026-10-07.md`.

## Nejnovější ověřený stav

2026-10-07 proběhl první skutečně úspěšný mobilní E2E běh všech tří repozitářů. `alua:1` přijímala observations, autonomně vykonávala fyzické akce a z budoucích motorických vjemů vznikaly beliefs a skills.

Ověřený snapshot:

- `last_observation_sequence = 474`;
- `episodes = 482`;
- `known_appearance_signatures = 13`;
- `decisions = 235`;
- `beliefs = 9`;
- `pending_expectations = 1`;
- `goals = 10`;
- `skills = 12`;
- `reusable_skills = 6`;
- `schema_version = 3`.

Původní hlavní blocker byl ve World body adapteru, nikoli v AI. Druhý blocker byl recoverable `target_expired` závod. Oba jsou opravené. Úplný runbook je v `docs/E2E_RUNTIME_2026-10-07.md`.


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
- SQLite schema v3;
- automatický backup při migraci v1/v2 -> v3;
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

1. audit skutečného rozhodování za běhu – zejména dlouhé série `look`;
2. vypsat a analyzovat current goals, beliefs a reusable skills;
3. ověřit, zda reusable skills skutečně mění budoucí volbu akcí;
4. restart/recovery a delší soak test všech tří procesů;
5. metabolismus/needs ve Worldu;
6. goal/utility a risk learning v Alua;
7. multi-step planner;
8. až potom destruktivnější autonomní manipulace.

## Oprava CI 2026-10-06

Aktivní ověřování nejistých zkušeností mělo konflikt priorit: `scan_obstacle` přebíjel `inspect_object`. Priorita ověřovacího cíle byla opravena tak, aby první dva kontrolní pokusy proběhly a po třetím se cíl dál nenabízel. Tato oprava nemění Bridge ani World kontrakt.

## Vlastní tělo a efektory – 2026-10-06

- World observation má bezpečný `body_schema` pro hlavu, trup, dvě ruce a dvě chodidla;
- Alua smí znát vlastní anatomii, ale ne význam externích objektů;
- ExplorationPolicy při `touch` vybírá volnou `hand_right`, případně `hand_left`;
- volba je v `parameters.effector` a v decision rationale;
- Bridge efektor pouze přenáší, World ověřuje jeho existenci, obsazenost, sílu a dosah;
- ACK stále není fyzický výsledek;
- autonomní pickup/push/break zůstává vypnutý;
- chybějící tělo `alua:1` nově vytvoří první tester automaticky, ale samostatný Python proces Alua se musí stále spustit zvlášť;
- panel Worldu rozlišuje tělo, Bridge session a nedávnou skutečnou aktivitu tohoto procesu.
