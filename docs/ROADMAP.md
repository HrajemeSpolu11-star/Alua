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

## Fáze E – první autonomní rozhodování
Stav: bezpečná embodied explorace.

Hotovo:
- cautious move;
- relative look;
- damage avoidance;
- obstacle scan;
- safe touch novelty;
- pending expectation gate;
- outcome attribution.

Zbývá:
- fyzické needs z metabolismu;
- goal selection;
- utility/risk learning;
- bounded multi-step planner;
- potom autonomní pickup/push/break.

## Fáze F – end-to-end AluaWorld

Technické části existují:
- persistentní tělo alua:1 v AluaWorld;
- body-aware AluaBridge adapter;
- Alua embodied runtime;
- E2E smoke helper.

Zbývá:
- provést smoke test na skutečném Termux/Luanti runtime;
- restartovat jednotlivě AI, Bridge a World a ověřit recovery;
- dlouhodobě měřit CPU/RAM/DB růst.

## Fáze G – učení dovedností

- procedurální memory;
- vícekrokové postupy;
- přeplánování;
- generalizace;
- risk a utility learning.

## Fáze H – jazyk a sociální chování

Až po stabilní neverbální kognici.

## Fáze I – populace

Více samostatných agentů, oddělené DB, supervisor a reprodukce až podle samostatného biology kontraktu.

## Definice hotovo

Pouhá existence třídy nebo tabulky nestačí. Fáze vyžaduje runtime chování, test, persistenci tam kde ji potřebuje, pozorovatelný následek a aktuální dokumentaci.
