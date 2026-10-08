# Roadmapa Alua AI

Roadmapa určuje pořadí závislostí, ne kalendář.

## Fáze A – dokumentační a kontraktní základ
Stav: hotovo.

## Fáze B – samostatný runtime
Stav: implementováno.

Hotovo:
- Python runtime a CLI;
- BridgeClient;
- SQLite schema v2;
- migrace v1 -> v2 s backupem;
- idempotentní ActionRequest;
- session recovery;
- testy a CI.

Zbývá:
- dlouhodobý restart test na skutečném telefonu.

## Fáze C – perception + working memory
Stav: implementovaný základ.

Hotovo:
- strict perception boundary;
- PerceptionFrame;
- ephemeral target association;
- WorkingMemory max 32 frame;
- motor events;
- appearance novelty.

Zbývá:
- více-modalitní novelty;
- sensory gaps;
- obecnější uncertainty;
- potvrdit stabilitu appearance_id přes session nebo zavést signature epoch.

## Fáze D – episodic memory + beliefs
Stav: první evidence-based vrstva implementována.

Hotovo:
- epizody;
- appearance evidence;
- expectations;
- belief store;
- support/contradiction;
- confidence;
- action -> motor effect learning;
- appearance + touch -> effect learning.

Zbývá:
- explicitní evidence links;
- decay;
- obecnější transition model a generalizace.

## Fáze E – autonomní rozhodování
Stav: embodied explorace + Cognitive Architecture V2.

Hotovo:
- cautious move;
- relative look;
- damage avoidance;
- obstacle scan;
- safe touch novelty;
- pending expectation gate;
- outcome attribution.

Hotovo navíc:
- intrinsic/reflex goal selection;
- egocentrický local world model;
- behavior critic;
- bounded multi-step planner;
- hierarchical data-only skill graph;
- receding-horizon local navigation;
- uncertainty-driven information scan;
- trajectory evaluation;
- adaptive utility ranking;
- persistentní perceptuální topologie;
- belief evidence provenance;
- offline sensory replay + acceptance benchmark.

Stav po Embodied Needs V4 a Cognitive Core V5:
- fyzické needs/metabolismus jsou zapojené;
- kontextový risk model je implementovaný a učí se z outcome evidence;
- inventory/pickup a need-driven resource acquisition jsou zapojené bounded policy;
- dead-end backtracking, prediction, self-model a metakognice jsou implementované.

Zbývá:
- explicitní preconditions pro automaticky indukované composite skills;
- širší risk evidence pro složitější tool-use/manipulace;
- dlouhý field/soak acceptance místo dalšího hardcoded rozšiřování.

## Fáze F – end-to-end AluaWorld

Technické části existují:
- persistentní tělo alua:1 v AluaWorld;
- body-aware AluaBridge adapter;
- Alua embodied runtime;
- E2E smoke helper.

Hotovo:
- skutečný Termux/Luanti E2E embodied loop;
- observations -> decisions -> actions -> sensory outcomes -> beliefs/skills.

Zbývá:
- restartovat jednotlivě AI, Bridge a World v delším soak testu;
- dlouhodobě měřit CPU/RAM/DB růst;
- po V2 provést nový behaviorální field test přes `alua evaluate`.

## Fáze G – učení dovedností

Stav: základ aktivní.

Hotovo:
- procedurální primitive memory;
- reusable skill gating;
- vestavěné composite behavior skills;
- vícekrokové bounded postupy;
- runtime přeplánování.

Zbývá:
- automatická indukce composite skillů z úspěšných trajectories;
- explicitní preconditions;
- bezpečná generalizace composite postupů.

Hotovo od V3/V5:
- adaptive utility;
- context-sensitive risk;
- prediction;
- strategy transfer/meta-learning;
- concept formation.

## Fáze H – jazyk a sociální chování

Až po stabilní neverbální kognici.

## Fáze I – populace

Více samostatných agentů, oddělené DB, supervisor a reprodukce až podle samostatného biology kontraktu.

## Definice hotovo

Pouhá existence třídy nebo tabulky nestačí. Fáze vyžaduje runtime chování, test, persistenci tam kde ji potřebuje, pozorovatelný následek a aktuální dokumentaci.


## Cognitive Core V5 – stav 2026-10-07

Implementováno:
- attention/surprise;
- multisensory scene fusion;
- object permanence;
- temporal recurrence;
- route memory a dead-end backtracking;
- relative odometry s uncertainty;
- predictive action model;
- context-sensitive risk;
- self capability model;
- interventional causal evidence;
- metacognition;
- regulatory drives;
- active experiments;
- prospective memory;
- persistent interruptible missions;
- concept formation;
- strategy transfer/meta-learning;
- bounded consolidation a confidence decay;
- explainable cognitive snapshot;
- social/testimony hooks pro budoucí explicitní sensory data.

Nejbližší acceptance práce už není přidávání dalších hardcoded pravidel. Je to:
1. dlouhý field test v různých typech terénu;
2. ověřit návrat ze slepé větve;
3. replay/benchmark V5 trajectories;
4. měřit DB růst, CPU a RAM;
5. ladit thresholdy pouze z evidence;
6. až podle chyb doplnit World sensory/action kontrakty;
7. social/multi-agent vrstvu aktivovat až po explicitních World signálech.

Dlouhodobě otevřené:
- robustnější landmark/loop-closure inference;
- automatická indukce více-krokových composite skills s explicitními preconditions;
- richer tool-use experimenty;
- obecnější sequence/temporal abstraction;
- explicitní komunikace mezi agenty;
- imitation a observational learning;
- multi-agent supervisor/population;
- volitelná high-level language/reasoning vrstva, která nikdy nebude přímo řídit motoriku.



Autoritativní V5 postup:
- `docs/COGNITIVE_CORE_V5.md`;
- `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.
