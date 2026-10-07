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

Zbývá:
- fyzické needs z metabolismu;
- explicitní harm/risk model pro jednotlivé manipulace;
- explicitní preconditions pro naučené composite skills;
- potom autonomní pickup/push/break.

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
- generalizace;
- risk a utility learning.

## Fáze H – jazyk a sociální chování

Až po stabilní neverbální kognici.

## Fáze I – populace

Více samostatných agentů, oddělené DB, supervisor a reprodukce až podle samostatného biology kontraktu.

## Definice hotovo

Pouhá existence třídy nebo tabulky nestačí. Fáze vyžaduje runtime chování, test, persistenci tam kde ji potřebuje, pozorovatelný následek a aktuální dokumentaci.
