# Paměť projektu Alua AI pro nový chat

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

## Stav Alua – aktuální k 2026-10-08

Aktuální AI branch pro Cognitive Core V5:
- `feat/cognitive-core-v5-20261007`;
- PR #10 `Cognitive Core V5`;
- schema v5;
- před migrací starší DB vzniká automatický pre-v5 backup.

Aktuální kognitivní stack:
- Python runtime + BridgeClient;
- strict schema/perception boundary;
- WorkingMemory;
- episodes, expectations, beliefs, goals a skills;
- Cognitive Architecture V2;
- Adaptive Cognition V3;
- Embodied Needs V4;
- Cognitive Core V5.

Cognitive Core V5 obsahuje:
- attention/surprise;
- multisensory scene integration;
- object permanence;
- temporal recurrence;
- route memory;
- relative odometry s uncertainty;
- dead-end detection a remembered-route backtracking;
- predictive action model;
- bounded counterfactual deliberation;
- learned context-sensitive risk;
- empirical self model;
- interventional causal hypotheses;
- metacognition;
- regulatory drives;
- active low-risk experiments;
- prospective memory;
- persistent interruptible missions;
- concept formation;
- strategy transfer/meta-learning;
- bounded consolidation a confidence decay;
- social/testimony/peer hooks pro budoucí explicitní social sensory data;
- `alua cognition-status`;
- vysvětlitelný `cognitive_state` v decision rationale.

Nejdůležitější behaviorální změna V5:
pokud Alua rozezná, že se dostala do slepé větve a má vlastní route history, má preferovat návrat k předchozímu známému perceptual place před náhodným look/escape chováním.

Autoritativní dokumenty:
- `docs/COGNITIVE_CORE_V5.md`;
- `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`;
- `docs/TESTING.md`;
- `docs/OPERATIONS_TERMUX.md`.

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

Embodied Needs V4 už umožňuje bounded pickup/break podle potřeby a evidence; nejde o plošně automatické destruktivní chování.

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

1. dokončit/merge PR #10 až po green CI na finálním HEAD;
2. na Termuxu pullnout aktuální Alua a otevřít Store, čímž proběhne migrace do schema v5;
3. ověřit `alua status`, `alua cognition-status` a `alua doctor`;
4. spustit AI ve skutečném světě;
5. připravit situaci se slepou větví a ověřit `spatial_backtrack`;
6. zkontrolovat, že route return nevytváří nový look loop;
7. ověřit prediction/risk/self/causal/strategy records z reálných outcomes;
8. po delším běhu spustit `evaluate --limit 2000` a `benchmark --limit 2000`;
9. provést delší soak/restart test a měřit CPU/RAM/DB růst;
10. teprve podle field evidence upravovat thresholdy nebo doplňovat World sensory/action kontrakty;
11. social/multi-agent chování aktivovat až po explicitních World social signálech.

## Oprava CI 2026-10-06

Aktivní ověřování nejistých zkušeností mělo konflikt priorit: `scan_obstacle` přebíjel `inspect_object`. Priorita ověřovacího cíle byla opravena tak, aby první dva kontrolní pokusy proběhly a po třetím se cíl dál nenabízel. Tato oprava nemění Bridge ani World kontrakt.

## Vlastní tělo a efektory – 2026-10-06

- World observation má bezpečný `body_schema` pro hlavu, trup, dvě ruce a dvě chodidla;
- Alua smí znát vlastní anatomii, ale ne význam externích objektů;
- ExplorationPolicy při `touch` vybírá volnou `hand_right`, případně `hand_left`;
- volba je v `parameters.effector` a v decision rationale;
- Bridge efektor pouze přenáší, World ověřuje jeho existenci, obsazenost, sílu a dosah;
- ACK stále není fyzický výsledek;
- pickup/break se používají pouze přes need-driven a evidence-gated policy;
- chybějící tělo `alua:1` nově vytvoří první tester automaticky, ale samostatný Python proces Alua se musí stále spustit zvlášť;
- panel Worldu rozlišuje tělo, Bridge session a nedávnou skutečnou aktivitu tohoto procesu.
