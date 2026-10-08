# Architektura Alua AI

## Cíl

Alua je samostatná Python aplikace bez přímé závislosti na Luanti nebo AluaWorld. V1 bude běžet na stejném zařízení jako AluaBridge a komunikovat pouze přes localhost HTTP Agent API.

Navržená struktura:

    Alua/
    ├── src/alua/
    │   ├── config.py
    │   ├── runtime.py
    │   ├── bridge_client.py
    │   ├── schema.py
    │   ├── clock.py
    │   ├── persistence/
    │   ├── perception/
    │   ├── memory/
    │   ├── beliefs/
    │   ├── needs/
    │   ├── goals/
    │   ├── planning/
    │   ├── actions/
    │   ├── learning/
    │   └── diagnostics/
    ├── tests/
    ├── docs/
    └── tools/

## Hlavní kognitivní cyklus

    Bridge observation
          |
          v
    perception ingest
          |
          v
    working memory
          |
          v
    belief/world-model update
          |
          v
    needs + current context
          |
          v
    goal selection
          |
          v
    bounded planner
          |
          v
    primitive ActionRequest
          |
          v
    AluaBridge
          |
          v
    pozdější observation
          |
          v
    outcome attribution + learning

Akce sama nevrací pravdivý herní výsledek.

## Komponenty

### config

Načítá pouze provozní konfiguraci:
- ALUA_AGENT_ID;
- ALUABRIDGE_URL;
- ALUA_AGENT_TOKEN;
- ALUA_DB_PATH;
- limity kognitivních cyklů;
- diagnostické přepínače.

Token se nikdy nezapisuje do SQLite ani logů.

### bridge_client

Jediný modul, který smí komunikovat s AluaBridge.

Odpovědnosti:
- načíst session;
- číst observations po poslední zpracované sequence;
- posílat ActionRequest;
- používat stabilní client_action_id při retry;
- klasifikovat transportní chyby;
- nikdy neinterpretovat význam vjemu.

### perception

Normalizuje validní observation do interního percept formátu.

Nesmí:
- doplňovat world truth;
- překládat appearance_id na technický název;
- považovat target_ref za dlouhodobou identitu.

### working memory

Krátký kontext posledních vjemů, aktivních hypotéz a očekávaných následků akcí.

Je bounded.

### episodic memory

Ukládá zkušenosti v čase:
- co bylo vnímáno;
- jaký byl interní stav;
- co Alua udělala;
- co později pozorovala.

### beliefs / world model

Udržuje opravitelné hypotézy:
- opakující se perceptuální vzory;
- vztahy akce -> pozorovaný následek;
- pravděpodobné lokální vztahy;
- naučené užitečnosti a rizika.

Každé přesvědčení má confidence, evidenci a čas poslední aktualizace.

### needs

V1 nesmí vymýšlet fyzické potřeby, které tělo neposkytuje. Pokud World později dodá hlad, žízeň, bolest, teplotu nebo únavu jako vjem vlastního těla, needs je interpretuje pro rozhodování.

Může existovat nízká vrozená kognitivní potřeba explorace, ale musí být jasně oddělena od fyzických potřeb těla.

### goals

Vytváří krátkodobé cíle z potřeb, známého rizika, nedokončených plánů a explorace.

### planning

V1 používá malý bounded planner nad primitivními akcemi. Nemá přímý seznam world schopností mimo povolené typy Bridge session.

### learning

Aktualizuje přesvědčení až z pozorovaných následků. Udržuje vazbu mezi očekáváním a pozdější observation.

### diagnostics

Zapisuje vysvětlitelnou kognitivní stopu:
- observation sequence;
- aktivní potřeby;
- kandidátní cíle;
- vybraný cíl;
- důvody výběru akce;
- očekávaný následek;
- pozdější vyhodnocení.

Diagnostika nesmí Alua dodávat nové world truth.

## Persistence

V1: SQLite.

Oddělené logické oblasti:
- meta a schema migrations;
- processed observations;
- episodes;
- beliefs;
- learned transitions;
- active goals;
- pending expectations;
- decision trace.

Každý agent má samostatnou databázi nebo striktně izolovaný namespace. V1 preferuje jeden agent na jeden proces a jeden DB soubor.

## Session boundary

Změna Bridge session_id znamená nový runtime světa/těla.

Při změně:
- zahodit target_ref;
- zrušit čekající plány závislé na target_ref;
- zachovat dlouhodobé epizody a naučená přesvědčení;
- nevydávat starou akci proti novému runtime;
- zapsat explicitní session transition.

## Výkon

Primární vývoj probíhá i na telefonu:
- žádné neomezené embedding databáze v první verzi;
- bounded pracovní paměť;
- dávkové SQLite zápisy;
- plánovač s tvrdým limitem uzlů a času;
- žádný externí LLM v hlavním cyklu;
- nejdříve měřit, potom škálovat.

## Směr závislostí

    config/persistence
          ^
    bridge + schema
          ^
    perception + memory
          ^
    beliefs + learning
          ^
    needs + goals
          ^
    planner + actions
          ^
        runtime

Vyšší vrstva nesmí obcházet nižší hranici.

## Implementovaný Cognitive V2 – 2026-10-07

Původně navržená planning vrstva je nyní reálně implementována jako několik malých modulů:

```text
PerceptionFrame
  -> WorkingMemory
  -> EgocentricWorldModel
  -> ReflexGoalSelector / IntrinsicCurriculum
  -> ExecutiveController
       -> BehaviorCritic
       -> SkillGraph
       -> BoundedPlanner
       -> LocalNavigator / ExplorationPolicy
  -> ActionRequest
```

### Vlastnictví

- `world_model.py`: pouze lokální smyslově odvozený stav, žádná globální mapa;
- `critic.py`: loop/stagnation evidence a replan signál;
- `skill_graph.py`: data-only composite behavior skills;
- `planning.py`: bounded rozklad high-level goalu na controller steps;
- `navigation.py`: cost-based lokální movement selection;
- `executive.py`: lifecycle aktivního plánu a koordinace modulů;
- `evaluation.py`: read-only hodnocení decision/outcome trajectory.

### Session boundary

World model, active plan, critic history a navigation failure penalties jsou lokální stav konkrétní session. Při změně `session_id` se resetují spolu s WorkingMemory.

Long-term SQLite episodes, beliefs, goal evidence a learned skills se zachovávají.

### Naučené skills vs. aktuální plán

Empiricky naučený primitive skill je pouze kandidát. Executive jej nepovolí, pokud nový percept hlásí překážku, critic stagnaci nebo lokální navigator doporučuje jiný směr. Dlouhodobá zkušenost tedy nesmí přebít čerstvou senzorickou evidenci.

Podrobný kontrakt: `docs/COGNITIVE_ARCHITECTURE_V2.md`.

## Adaptive Cognition V3 – persistentní zkušenost bez globální mapy

Nad V2 je implementována další evidence vrstva:

```text
PerceptionFrame
  -> PerceptualTopology
       -> persistent place-like signature
       -> maneuver transition evidence
       -> navigation prior
  -> AdaptiveUtilityModel
       -> empirical goal success/failure
       -> uncertainty / novelty / damage
  -> V2 planner + executive
```

`PerceptualTopology` není world map. Je to graf opakujících se perceptuálních kontextů odvozených pouze z vlastních vjemů.

Beliefs mají od schema v4 samostatné `belief_evidence`, takže lze auditovat konkrétní observation/decision evidence.

Offline `benchmark` kombinuje decision/outcome trajectory s replay uložených sensory episodes.

Podrobnosti: `docs/ADAPTIVE_COGNITION_V3.md`.


## Cognitive Core V5 – vyšší kognitivní smyčka

V5 rozšiřuje V2/V3, ale nemění autoritu vrstev.

```text
PerceptionFrame
  -> SceneIntegrator + TemporalModel
  -> AttentionSystem
  -> ObjectMemory
  -> EgocentricWorldModel + PerceptualTopology
  -> SpatialMemory (route + relative odometry)
  -> Metacognition
  -> DriveSystem
  -> Missions / ProspectiveMemory / ExperimentPlanner
  -> Reflex + curriculum + cognitive goal arbitration
  -> BoundedPlanner / ExecutiveController
  -> PredictiveModel + RiskModel counterfactual scoring
  -> primitive action
  -> future sensory outcome
  -> Prediction/Risk/Self/Causal/Strategy learning
  -> periodic Consolidation + Concepts
```

### Nové invarianty

- prostorová paměť používá pouze vlastní perceptuální signatures a relativní odometrii, nikdy World XYZ;
- dead-end recovery má preferovat zapamatovaný návrat před náhodným rozhlížením;
- prediction není fakt; je confidence-weighted hypotéza opravovaná outcome evidencí;
- metakognice smí změnit strategii, ale nesmí sama vytvářet externí world truth;
- social testimony je oddělené od self-verified belief;
- mission může přežít krátkodobé přerušení potřebou, ale každá fyzická akce zůstává bounded a znovu ověřená čerstvým perceptem;
- contextual terrain/motor zkušenost se nesmí promovat do univerzálního skillu bez preconditions.

Autoritativní detail: `docs/COGNITIVE_CORE_V5.md`.

## Cognitive Core V5 – 2026-10-08

Nad V2/V3 a Embodied Needs V4 je nově jedna koordinovaná vyšší kognitivní vrstva:

```text
PerceptionFrame
  -> SceneIntegrator
  -> AttentionSystem
  -> ObjectMemory
  -> TemporalModel
  -> EgocentricWorldModel
  -> PerceptualTopology
  -> SpatialMemory
  -> Metacognition
  -> DriveSystem
  -> MissionManager / ProspectiveMemory / ExperimentPlanner
  -> PredictiveModel + RiskModel + SelfModel + StrategyLearner
  -> Goal selection
  -> BoundedPlanner / ExecutiveController
  -> primitive action
  -> future sensory outcome
  -> prediction/risk/self/causal/strategy learning
```

V5 nepřidává privilegovanou mapu ani World truth. Prostorový model používá pouze vlastní perceptuální place signatures, relativní heading a odometrii odvozenou z vlastních potvrzených pohybů.

Hlavní behaviorální změna: stagnace a slepé větve už nemusí být řešeny lokálním random-like escape. Pokud existuje ověřená route history, cognitive core preferuje explicitní návrat na předchozí známé místo.

Persistentní vyšší kognice je uložená v schema v5 přes namespaced `cognitive_records`.

Autoritativní popis: `docs/COGNITIVE_CORE_V5.md`.


Kompletní kroková implementační stopa: `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.
