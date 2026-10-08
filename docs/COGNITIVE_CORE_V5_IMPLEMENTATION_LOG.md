# Cognitive Core V5 – kompletní implementační deník

Datum implementace: 2026-10-07 až 2026-10-08  
Repozitář: `HrajemeSpolu11-star/Alua`  
Vývojová větev: `feat/cognitive-core-v5-20261007`  
Pull request: #10 `Cognitive Core V5`

Tento dokument zachycuje celý postup V5 od důvodu změny přes návrh, jednotlivé moduly, integraci runtime, migraci databáze, testy, CI, provoz na telefonu a podmínky field acceptance. Je určen jako auditní stopa pro další chat i pro budoucí debugging.

## 1. Výchozí problém

Před V5 už Alua měla:
- embodied runtime přes AluaBridge;
- WorkingMemory;
- episodes, beliefs, goals a skills;
- Cognitive Architecture V2;
- adaptive utility a perceptual topology V3;
- Embodied Needs V4;
- graded motor progress;
- lokální navigation penalties;
- anti-look-loop a stagnation critic.

Field test ale ukázal zásadní omezení: když se agent dostal do slepé větve, uměl poznat nízký progress a lokálně přeplánovat, ale neměl dostatečně silný koncept „přišel jsem sem odtud, tady už nic není, vrať se po vlastní známé trase“. Výsledkem mohlo být zmatené lokální rozhlížení nebo escape manévry bez skutečné prostorové paměti.

Cíl V5 proto nebyl přidat další hardcoded pravidlo typu „když narazíš, udělej back“. Cílem bylo doplnit vyšší kognitivní vrstvy tak, aby návrat, volba alternativy, risk, nejistota a učení vznikaly z vlastních zkušeností agenta.

## 2. Zachované systémové hranice

Před implementací byly potvrzeny invarianty:

1. AluaWorld vlastní fyzickou pravdu.
2. AluaBridge vlastní transport, session, queue a ephemeral `target_ref`.
3. Alua vlastní kognici.
4. Alua nesmí číst absolutní World XYZ.
5. Alua nesmí číst interní názvy node/itemů, recepty ani administrátorská data.
6. `target_ref` není dlouhodobá identita.
7. ACK akce není outcome.
8. Každý belief/prediction/risk model musí být opravitelný budoucí evidencí.
9. Motorické rozhodnutí zůstává bounded a po jednom kroku se znovu replánuje.
10. Vyšší kognice nesmí obejít Bridge ani generovat přímo World stav.

## 3. Nová persistence – schema v5

Soubor: `src/alua/store.py`

`SCHEMA_VERSION` byl zvýšen z 4 na 5.

Přidána tabulka:

```text
cognitive_records
- agent_id
- record_key
- record_kind
- payload_json
- confidence
- support_count
- contradiction_count
- first_sequence
- last_sequence
- created_at
- updated_at
```

Důvod generického namespaced store:
- vyšší modely mají různý payload;
- není vhodné vytvářet pro každý model další jednoúčelovou tabulku;
- pořád je nutná per-agent izolace, confidence a evidence counts;
- payload prochází `strip_ephemeral`, takže se nepersistuje `target_ref`.

Přidané API Store:
- `upsert_cognitive_record(...)`;
- `cognitive_record(...)`;
- `cognitive_records(...)`;
- `belief_rows(...)`;
- `decay_stale_beliefs(...)`.

`Store.summary()` nově reportuje `cognitive_records`.

Migrace:
- při otevření starší DB se před změnou vytvoří `*.pre-v5-YYYYMMDD-HHMMSS.bak`;
- staré episodes, beliefs, goals, skills, perceptual places a transitions se nemažou;
- neznámé novější schema je stále odmítnuto.

## 4. AttentionSystem

Nový soubor: `src/alua/attention.py`

Úkol:
- vybrat aktuálně nejvýznamnější percept;
- odlišit novelty, blízkost a změnu proti minulému frame;
- odhadnout sensory uncertainty;
- vytvořit bounded surprise.

Vstup:
- pouze `PerceptionFrame`;
- set nových `appearance_id`.

Výstup:
- focus kind;
- focus appearance signature;
- focus ray;
- salience;
- surprise;
- uncertainty.

Attention nic neprohlašuje za externí fakt. Je to pouze priorita zpracování.

## 5. ObjectMemory – object permanence

Nový soubor: `src/alua/object_memory.py`

Přidána bounded paměť perceptuálních objektů podle `appearance_id`.

Track obsahuje:
- first/last sequence;
- sightings;
- last ray;
- last distance;
- blocks_motion;
- liquid;
- persistence confidence.

Když objekt na chvíli zmizí ze zorného pole, track se okamžitě nemaže. Confidence postupně klesá.

Do persistence se ukládá `object_concept`, ale bez ephemeral `target_ref`.

## 6. SpatialMemory – route memory, dead ends a návrat

Nový soubor: `src/alua/spatial_memory.py`

Jde o hlavní opravu field problému.

Udržuje:
- aktuální perceptual place signature;
- route stack úspěšných přechodů;
- relative heading;
- relativní odometrii X/Z;
- odometry uncertainty;
- počet failed moves v místě;
- visit counts;
- stav backtracking.

Každý úspěšný přesun může vytvořit:

```text
origin place
-> maneuver
-> destination place
```

Route step si pamatuje i heading při odchodu a inverse maneuver.

Dead-end evidence kombinuje:
- lokálně blokovaný front/left/right;
- failed progress;
- revisit ratio;
- existenci známé návratové route.

Když je dead-end/stagnation dostatečně silný, vznikne `SpatialDirective`:
- `turn` – srovnat heading;
- nebo `move` – použít inverse maneuver a vrátit se.

Pokud agent rozpozná návrat do předchozího place, route edge se popne a uncertainty odometrie se sníží jako weak loop closure.

Důležité: X/Z jsou interní relativní souřadnice, nikoli World XYZ.

## 7. PredictiveModel

Nový soubor: `src/alua/predictive.py`

Modeluje:

```text
context signature + action signature
-> expected progress
-> expected success
-> confidence
```

Po outcome:
- aktualizuje mean progress;
- aktualizuje success rate;
- počítá prediction error;
- počítá surprise.

Action signature je sanitizovaný typ akce/manévru, ne celý ephemeral request.

## 8. Counterfactual deliberation

Implementováno přes `PredictiveModel.counterfactual_scores()` a `CognitiveCore._deliberate()`.

Při stagnaci lze porovnat bounded kandidáty:
- forward;
- left;
- right;
- back.

Score kombinuje:
- expected progress;
- expected success;
- information bonus při nízké confidence;
- learned risk;
- transferable strategy prior.

Vybere se jediný fyzický krok. Po jeho outcome se znovu vnímá a replánuje.

Žádný neomezený tree search ani generovaný executable code.

## 9. RiskModel

Nový soubor: `src/alua/risk.py`

Risk se učí z:
- failure;
- low progress;
- slip;
- damage signal.

Risk je vázaný na:
- perceptual context;
- action signature.

Tím se předchází chybnému zobecnění typu „jump je vždy nebezpečný“.

## 10. SelfModel

Nový soubor: `src/alua/self_model.py`

Agent si vede empirický model vlastních capabilities.

Příklad recordu:
- capability `move:jump`;
- attempts;
- successes;
- success_rate;
- mean_progress;
- mean_effort;
- confidence.

SelfModel také reportuje aktuální body state:
- health;
- stamina;
- hunger;
- thirst;
- fatigue;
- breath;
- inventory load.

## 11. CausalLearner

Nový soubor: `src/alua/causal.py`

Ukládá interventional hypotheses:

```text
context + moje action
-> pozdější effect
```

Sledované outcome kanály:
- progress;
- vertical progress;
- nutrition delta;
- hydration delta;
- stamina delta;
- inventory delta.

Hypotéza má samples, mean effect a confidence.

Nejde o absolutní kauzalitu. Jde o evidence „po mojí intervenci tento efekt následoval“.

## 12. Metacognition

Nový soubor: `src/alua/metacognition.py`

Monitoruje:
- recent progress;
- revisit loop;
- action repetition;
- prediction errors;
- sensory uncertainty;
- dead-end score.

Výstupní režimy:
- `continue`;
- `explore`;
- `seek_information`;
- `reconsider_model`;
- `backtrack`.

Důvod je zásadní: agent musí odlišit „nevím“, „nehýbu se“, „můj model je špatný“ a „jsem ve slepé větvi“.

## 13. DriveSystem

Nový soubor: `src/alua/drives.py`

Funkční regulační drives:
- safety;
- homeostasis;
- curiosity;
- frustration;
- exploration.

Nejde o antropomorfní emoce. Jsou to priority nad již existujícími tělesnými potřebami a kognitivním stavem.

## 14. ExperimentPlanner

Nový soubor: `src/alua/experiments.py`

Když:
- safety není kritická;
- homeostasis není kritická;
- uncertainty/curiosity je vysoká;
- existuje blízký neověřený percept;

může navrhnout low-risk experiment.

První explicitní experiment:
- `touch`.

Experiment používá normální `inspect_object` goal, takže neobchází existující learning/skill evidence ani testy.

Původně experiment použil nový key `experiment:touch:<appearance>`. CI odhalilo regresi proti invariantům goal evidence, protože stávající testy správně očekávaly kanonický `inspect:<appearance>`. Oprava zachovala experiment jako nový selector/reason, ale goal key zůstal `inspect:<appearance>`.

Tento CI failure byl užitečný: zabránil fragmentaci stejné zkušenosti do dvou různých goal statistik.

## 15. ProspectiveMemory

Nový soubor: `src/alua/prospective.py`

Umožňuje persistentní záměr:

```text
až trigger Y nastane
-> připomeň X
```

Record může obsahovat:
- trigger place;
- priority;
- payload;
- active/completed state.

## 16. MissionManager

Nový soubor: `src/alua/missions.py`

Mission je dlouhodobější persistentní cíl, který není motorická sekvence.

V5 zavádí základ:
- `understand-environment`.

Mission může být:
- active;
- suspended;
- completed;
- failed.

Homeostatic pressure ji může suspendovat. Po odeznění potřeby ji lze obnovit.

Každá fyzická akce z mission stále prochází fresh perception -> goal -> planner -> action.

## 17. SceneIntegrator

Nový soubor: `src/alua/scene.py`

Spojuje:
- vision;
- hearing;
- contact;
- body pressure.

Vytváří `scene-...` signature pro cross-modal context.

Scene signature není fyzická lokace.

## 18. TemporalModel

Nový soubor: `src/alua/temporal.py`

Sleduje:
- occurrences sensory scene;
- last simulation time;
- přibližný mean recurrence interval;
- confidence.

Nepoužívá kalendář ani externí časové znalosti.

## 19. ConceptLearner

Nový soubor: `src/alua/concepts.py`

Vyhledává různé appearance signatures se společnými evidence-backed relations.

Pokud více objektů sdílí podobné naučené affordances, může vzniknout abstraktní interní concept.

Do konceptu se nedostává technický node/item název.

## 20. StrategyLearner – transfer/meta-learning

Nový soubor: `src/alua/strategy.py`

Učí slabší prior:

```text
goal kind + action pattern
-> mean progress
-> success rate
-> strategy score
```

V novém contextu funguje jen jako transfer bonus.

Context-specific prediction a fresh sensory evidence mají vyšší autoritu.

## 21. MemoryConsolidator

Nový soubor: `src/alua/consolidation.py`

Po bounded intervalu:
- vytvoří trajectory summary;
- uloží mean progress/success rate/action/goal counts;
- provede pomalý confidence decay velmi starých beliefs směrem k nejistotě;
- spustí concept formation.

Cílem je odlišit:
- raw episodic history;
- dlouhodobou abstrakci;
- zapomínání jako pokles jistoty, nikoli tiché přepsání evidence.

## 22. Social cognition

Nový soubor: `src/alua/social.py`

Aktivuje se pouze pokud World explicitně poskytne social sensory channel.

Model:
- familiarity;
- trust;
- encounters;
- social testimony.

Cizí tvrzení se ukládá jako `social_testimony`, ne jako vlastní empirical belief.

Nový soubor `src/alua/social_modeling.py` přidává slabý behavioral prior pro explicitně pozorovaného peer agenta.

Bez explicitních World social dat jsou obě vrstvy inertní.

## 23. CognitiveCore orchestrátor

Nový soubor: `src/alua/cognition.py`

Koordinuje:
- SceneIntegrator;
- TemporalModel;
- AttentionSystem;
- ObjectMemory;
- SpatialMemory;
- PredictiveModel;
- RiskModel;
- SelfModel;
- CausalLearner;
- Metacognition;
- DriveSystem;
- ProspectiveMemory;
- MissionManager;
- ExperimentPlanner;
- SocialCognition;
- StrategyLearner;
- MemoryConsolidator.

`CognitiveSnapshot` obsahuje vysvětlitelný stav vyšší kognice.

Snapshot se ukládá jako:
- `record_key = cognition:last-state`;
- `record_kind = metacognitive_state`.

## 24. Integrace do Runtime

Soubor: `src/alua/runtime.py`

Do `Runtime.__init__` přidán `CognitiveCore`.

Při session change:
- WorkingMemory clear;
- Executive reset;
- PerceptualTopology reset;
- CognitiveCore session-local stav reset.

Při každé nové observation:
1. frame se validuje;
2. vyřeší se staré motor outcomes;
3. uloží se episode;
4. aktualizuje WorkingMemory;
5. aktualizuje Executive world model;
6. aktualizuje PerceptualTopology;
7. aktualizují se persistent nav priors;
8. spustí se CognitiveCore.observe();
9. uloží se latest cognitive snapshot.

Goal arbitration:
1. reflex má absolutní prioritu;
2. pokud CognitiveCore vrátí známý backtrack directive, vznikne `spatial_backtrack`;
3. při silné stagnaci může vzniknout `deliberate_navigation`;
4. aktivní low-risk experiment používá kanonický `inspect_object`;
5. jinak běží běžný intrinsic curriculum a utility ranking;
6. drives/missions upravují ranking, ale neobcházejí safety.

Decision rationale nově obsahuje:
- `cognitive_state`;
- metacognition;
- drives;
- scene;
- spatial directive;
- deliberation;
- active missions.

Při submitu:
- Executive dostane submission;
- PerceptualTopology začne transition;
- CognitiveCore si uloží pending context/action.

Při budoucím motor outcome:
- expectation se koreluje přes Bridge action sequence;
- Topology dokončí transition;
- CognitiveCore aktualizuje prediction/risk/self/causal/strategy/spatial/meta modely;
- Executive dostane outcome;
- původní learning aktualizuje beliefs;
- goal stats a skills se aktualizují.

## 25. Planner a SkillGraph

Soubor: `src/alua/skill_graph.py`

Přidány data-only skills:
- `cognitive_backtrack`;
- `model_based_navigation`.

Soubor: `src/alua/executive.py`

Přidány nové bounded controller steps:
- `backtrack`;
- `deliberate`.

Tyto kroky delegují fyzickou podobu akce do policy; planner sám nevytváří World pravdu.

## 26. ExplorationPolicy

Soubor: `src/alua/policy.py`

Nové goal kinds:

### spatial_backtrack

`phase=turn`:
- vyšle bounded relative look.

`phase=move`:
- mapuje remembered inverse maneuver na bounded move.

### deliberate_navigation

Vykoná pouze předem omezenou candidate move z CognitiveCore counterfactual deliberation.

## 27. CLI

Soubor: `src/alua/cli.py`

Přidán:

```bash
.venv/bin/python -m alua cognition-status
```

Reportuje:
- schema version;
- počty cognitive records podle kind;
- active missions;
- poslední `cognition:last-state`.

Je to read-only diagnostika. Nespouští druhý runtime.

## 28. Testy přidané pro V5

Nové testovací soubory:
- `tests/test_attention.py`;
- `tests/test_object_memory.py`;
- `tests/test_predictive.py`;
- `tests/test_spatial_memory.py`;
- `tests/test_metacognition.py`;
- `tests/test_cognition.py`;
- `tests/test_cognitive_policy.py`.

Rozšířen:
- `tests/test_store.py`.

Pokrytí:
- novel target focus;
- sensory surprise;
- object permanence;
- persistent object concept bez target_ref;
- prediction learning;
- dead-end backtracking;
- heading correction před návratem;
- metacognitive backtrack režim;
- cognitive snapshot persistence;
- schema v5 round-trip;
- v4 -> v5 backup migrace;
- policy execution remembered-route turn/move;
- model-selected move.

Staré testy zůstaly aktivní a fungují jako regression guard.

## 29. CI incident během implementace

PR #10 měl během vývoje několik průběžných CI runů.

První nové moduly prošly.

Po integraci ExperimentPlanneru selhaly dva existující runtime testy:

```text
expected: inspect:pabc
actual:   experiment:touch:pabc
```

Interpretace:
- fyzické chování bylo kompatibilní;
- evidence namespace kompatibilní nebyl;
- nový experiment rozděloval stejný inspect goal na nový key.

Oprava:
- experiment zůstává nový selector/reason;
- kanonický goal key je znovu `inspect:<appearance>`.

Následující CI runy byly green.

To je důležitá součást auditní historie; chyba nebyla skryta změnou testu, ale opravena implementace.

## 30. GitHub/CI stav implementační větve

Během implementace byly ověřeny green workflow runs na pozdějších commits, včetně:
- spatial relative odometry;
- scene/temporal integration;
- strategy transfer;
- cognitive policy tests;
- hlavní V5 dokumentace.

Před merge je povinné znovu ověřit CI přes aktuální HEAD větve.

## 31. Dokumentace aktualizovaná spolu s V5

Autoritativní dokument:
- `docs/COGNITIVE_CORE_V5.md`.

Dále musí být synchronizované:
- `README.md`;
- `CHANGELOG.md`;
- `docs/ARCHITECTURE.md`;
- `docs/DECISIONS.md`;
- `docs/MEMORY_MODEL.md`;
- `docs/LEARNING_AND_DECISION.md`;
- `docs/ROADMAP.md`;
- `docs/TESTING.md`;
- `docs/OPERATIONS_TERMUX.md`;
- `docs/IMPLEMENTATION_LOG_AI.md`;
- `docs/PAMET_PRO_NOVY_CHAT.md`.

Tento soubor je detailní krokový audit. Ostatní dokumenty mají příslušnou oblast shrnout, ne duplikovat celý deník.

## 32. Deployment na Termux

Po merge/pullu:

```bash
cd "$HOME/alua/Alua"
git pull --ff-only
git rev-parse --short HEAD

set -a
. ./.env
set +a

.venv/bin/python -m alua status
```

První otevření Store migruje DB do schema v5 a vytvoří pre-v5 backup.

Očekávat:
- `schema_version: 5`.

Dále:

```bash
.venv/bin/python -m alua cognition-status
.venv/bin/python -m alua doctor
```

`doctor` musí ukázat aktivní Bridge session a rostoucí observation sequence.

Potom:

```bash
.venv/bin/python -m alua run
```

Po několika minutách:

```bash
.venv/bin/python -m alua cognition-status
.venv/bin/python -m alua evaluate --limit 2000
.venv/bin/python -m alua benchmark --limit 2000
```

## 33. Field acceptance

V5 není považována za hotovou pouze proto, že CI je green.

Povinné živé ověření:

1. agent projde do větve, kterou později rozpozná jako slepou;
2. route stack obsahuje cestu dovnitř;
3. stagnation/dead-end evidence překročí threshold;
4. goal se změní na `spatial_backtrack`;
5. agent provede případnou heading correction;
6. následně se pokusí vrátit inverse maneuver;
7. po rozpoznání předchozího place se route edge popne;
8. nesmí vzniknout nekonečný look loop;
9. prediction/risk/self/causal records musí přibývat pouze po sensory outcome;
10. `cognition-status` musí ukázat srozumitelný snapshot;
11. `evaluate` nesmí hlásit staré behaviorální regrese;
12. `benchmark` musí mít dost evidence a projít acceptance.

## 34. Co zatím není možné pravdivě označit za dokončené

Bez dalšího World kontraktu nelze tvrdit, že Alua už má:
- skutečný jazyk;
- plnohodnotnou komunikaci mezi více agenty;
- plnou theory-of-mind;
- observational imitation;
- kulturu;
- reprodukční/populační dynamiku.

AI-side hooks existují, ale zůstávají inertní bez autoritativních sensory dat.

## 35. Rollback/recovery

Pokud field test odhalí kritickou regresi:

1. zastavit pouze Alua runtime;
2. nechat World/Bridge data beze změny, pokud nejsou zdrojem chyby;
3. zachovat aktuální SQLite a pre-v5 backup;
4. uložit `cognition-status`, `evaluate`, `benchmark` a relevantní logs;
5. nepřepisovat chybný stav ručními DB zásahy;
6. opravit branch kódem + regression testem;
7. zopakovat CI;
8. až potom znovu nasadit.

Starou DB nemažte jen proto, že agent udělal špatné rozhodnutí. Právě tato evidence je potřebná pro diagnostiku.

## 36. Definition of Done pro V5

V5 je připravena k označení za stabilní až když současně platí:

- schema v5 migrace je ověřená na reálné starší DB;
- všechny unit/regression testy jsou green;
- repository audit je green;
- PR CI na finálním HEAD je green;
- Termux doctor je green;
- živé observations/actions/outcomes běží;
- dead-end backtracking funguje ve skutečném světě;
- anti-loop benchmark neregresuje;
- DB růst, CPU a RAM jsou přijatelné při delším soak testu;
- dokumentace odpovídá přesně nasazenému commitu.

