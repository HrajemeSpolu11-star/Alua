# Cognitive Core V5

Datum: 2026-10-07

## Cíl

Cognitive Core V5 rozšiřuje Alua z lokálně reaktivního agenta na systém, který má vlastní pozornost, prostorovou paměť, predikce, model sebe sama, metakognici, dlouhodobější záměry a evidence-based abstrakce.

V5 nemění základní hranici projektu:

- AluaWorld vlastní fyzickou pravdu;
- AluaBridge pouze přenáší omezené observations/actions;
- Alua vlastní paměť, beliefs, cíle, plánování, predikce a učení;
- Alua nesmí dostat absolutní mapu, technické názvy node/itemů ani privilegované World souřadnice.

## Hlavní pipeline

```text
Bridge observation
      |
      v
PerceptionFrame
      |
      +--> multisensory scene fusion
      +--> attention / surprise
      +--> object permanence
      +--> temporal recurrence
      +--> egocentric world model
      +--> perceptual topology
      +--> spatial route memory + relative odometry
      |
      v
Metacognition
      |
      +--> stagnation
      +--> revisit loop
      +--> uncertainty
      +--> prediction error
      |
      v
Drives + needs + missions
      |
      v
Goal selection
      |
      +--> remembered-route backtracking
      +--> active experiment
      +--> ordinary intrinsic/reflex goals
      +--> model-based counterfactual navigation
      |
      v
Executive / planner / policy
      |
      v
Bridge action
      |
      v
Future motor outcome
      |
      +--> prediction learning
      +--> risk learning
      +--> self-model learning
      +--> causal evidence
      +--> strategy transfer learning
      +--> existing beliefs/goals/skills
```

## 1. Attention

`attention.py` vybírá senzoricky významné podněty.

Používá pouze:
- novelty appearance signature;
- blízkost;
- blokování pohybu;
- změnu proti předchozímu frame;
- omezenou sensory uncertainty.

Výstup:
- focus signature;
- focus ray;
- salience;
- surprise;
- uncertainty.

Attention nic neprohlašuje za World truth.

## 2. Multisensory scene

`scene.py` spojuje zrak, sluch, kontakt a tělesný tlak do jednoho scene signature.

Scene signature je interní rozpoznávací klíč. Není to fyzická pozice ani technické ID lokace.

## 3. Object permanence

`object_memory.py` udržuje krátko/střednědobé perceptuální tracky podle appearance signature.

Když objekt zmizí ze zorného pole, okamžitě se nemaže. Track má:
- first/last sequence;
- sightings;
- poslední ray/distance;
- blocks_motion/liquid evidence;
- persistence confidence.

`target_ref` se nikdy nepoužívá jako dlouhodobá identita.

## 4. Prostorová paměť a návrat

`spatial_memory.py` řeší zásadní problém field testu: agent nesmí ve slepé uličce pouze náhodně koukat.

Udržuje:
- route stack vlastních úspěšných přechodů;
- heading;
- relativní odometrii X/Z;
- uncertainty odometrie;
- failure count na rozpoznaném place;
- weak loop closure při návratu do známého perceptuálního kontextu.

Když evidence ukazuje slepou větev nebo silnou stagnaci:

```text
současné místo
-> najdi poslední zapamatovaný route edge
-> vrať heading do orientace při příchodu
-> použij inverse maneuver
-> po návratu route edge odstraň
-> pokračuj k jiné větvi
```

To je explicitní návratová navigace, ne náhodný escape.

## 5. Relativní self-localization

Alua nemá World XYZ.

V5 udržuje pouze interní relativní pose:

```text
x
z
heading_rad
uncertainty
```

Pose vzniká z vlastních motorických akcí a jejich ověřeného progressu.

Opětovné rozpoznání známého perceptuálního místa snižuje odometry uncertainty.

## 6. Predictive model

`predictive.py` ukládá model:

```text
perceptual context + action
-> expected progress
-> expected success
-> confidence
```

Po skutečném outcome se počítá prediction error a surprise.

Predikce jsou opravitelné a vznikají pouze z vlastních intervencí.

## 7. Model-based counterfactual deliberation

Při stagnaci nebo velkém prediction error může V5 porovnat několik fyzických alternativ:

- forward;
- left;
- right;
- back.

Každá alternativa dostane:
- expected progress;
- expected success;
- model confidence;
- learned risk;
- information bonus;
- transferable strategy prior.

Vybraná alternativa se provede pouze jako jeden bounded krok a potom se znovu replánuje z čerstvých vjemů.

## 8. Risk model

`risk.py` se učí kontextový risk podle:
- failure;
- nízkého progressu;
- slip;
- recent damage.

Risk není globální label typu „jump je nebezpečný“. Je vázaný na action + perceptual context.

## 9. Self model

`self_model.py` vytváří empirický model vlastních schopností.

Příklad:

```text
move:jump
attempts = 18
success_rate = ...
mean_progress = ...
mean_effort = ...
confidence = ...
```

Tělo tedy poskytuje capability, ale Alua si zároveň buduje vlastní zkušenost s tím, jak jí daná capability skutečně funguje.

## 10. Causal evidence

`causal.py` ukládá interventional hypothesis:

```text
context + action
-> progress effect
-> nutrition effect
-> hydration effect
-> inventory effect
...
```

Je to „po mojí akci tento efekt opakovaně následoval“, nikoli absolutní kauzální pravda.

## 11. Metacognition

`metacognition.py` monitoruje vlastní chování.

Sleduje:
- recent progress;
- place revisit loop;
- repeated strategy;
- prediction error;
- sensory uncertainty;
- dead-end evidence.

Výstupní režimy:
- continue;
- explore;
- seek_information;
- reconsider_model;
- backtrack.

Tím se odlišuje:
- „nevím“;
- „můj model je chybný“;
- „nehýbu se“;
- „jsem ve slepé větvi“.

## 12. Regulatory drives

`drives.py` vytváří funkční regulační signály:
- safety;
- homeostasis;
- curiosity;
- frustration;
- exploration.

Nejde o simulaci lidských emocí. Jsou to priority pro rozhodování.

## 13. Aktivní experimentování

`experiments.py` umožňuje cíleně získávat informace.

Pokud je podnět významný, dosažitelný a jeho affordance není ověřená, může Alua vytvořit nízkorizikový experiment.

První bezpečná experimentální primitive je `touch`.

Experiment jde stále přes normální goal/planner/action/outcome řetězec.

## 14. Prospective memory

`prospective.py` ukládá budoucí záměry:

```text
až nastane trigger X
-> připomeň záměr Y
```

Intent může být vázaný na rozpoznané perceptuální místo a přežívá restart procesu.

## 15. Long-horizon missions

`missions.py` ukládá dlouhodobější, přerušitelné cíle.

V5 obsahuje základní autonomní mission:
- `understand-environment`.

Homeostatic pressure ji může suspendovat. Po odeznění akutních potřeb zůstává v persistence a může pokračovat.

Mission není jeden motorický příkaz.

## 16. Temporal model

`temporal.py` se učí:
- occurrence count;
- recency;
- přibližné opakující se intervaly sensory scene.

Nevytváří kalendářní znalosti; používá vlastní simulation time z observation.

## 17. Concept formation

`concepts.py` hledá appearance signatures se společnými evidence-backed relations.

Například dvě různé appearance mohou později patřit do jednoho interního konceptu, pokud mají opakovaně podobné affordances.

Technické názvy objektů nejsou použity.

## 18. Transfer a meta-learning

`strategy.py` vytváří slabší kontextově obecný prior:

```text
goal kind + action pattern
-> mean progress
-> success rate
-> strategy score
```

V novém kontextu může fungovat jako transfer hint, ale nesmí přebít čerstvou sensory evidence a context-specific model.

## 19. Consolidation a zapomínání

`consolidation.py` periodicky:
- vytvoří bounded episodic summary;
- provede pomalý confidence decay starých beliefs;
- spustí concept formation.

Raw history tedy není jediný způsob dlouhodobé paměti.

## 20. Social cognition

`social.py` je připraven na explicitní social sensory channel.

Bez tohoto kanálu je inertní a nikdy nehádá, že obyčejný objekt je jiný agent.

Umí:
- familiarity;
- evidence-based trust;
- testimony records;
- oddělení cizího tvrzení od vlastní zkušenosti.

`social_modeling.py` umí nad explicitně pozorovaným peer action signal budovat behavior prior.

Dokud World takové smyslové signály neposkytuje, tato vrstva neovlivňuje běžné rozhodování.

## 21. Explainability

Každé nové rozhodnutí může do decision rationale uložit `cognitive_state`:

- attention;
- scene;
- metacognition;
- drives;
- spatial directive;
- model-based deliberation;
- mission;
- self-state.

Tím lze zpětně zjistit, proč agent zvolil konkrétní akci.

## 22. Persistence schema v5

SQLite schema v5 přidává `cognitive_records`.

Je to namespaced evidence store pro:
- object concepts;
- spatial state;
- route evidence;
- predictions;
- risk;
- self model;
- causal hypotheses;
- temporal patterns;
- prospective intentions;
- missions;
- abstract concepts;
- strategy models;
- social models;
- metacognitive snapshot.

Při migraci starší DB se stejně jako dříve vytvoří backup.

## 23. Co V5 záměrně nedělá

V5 není tvrzení, že jsme vytvořili AGI.

Bez odpovídající sensory/action evidence z Worldu nelze pravdivě aktivovat:
- skutečný jazyk;
- komunikaci mezi více agenty;
- plnou theory-of-mind;
- imitaci druhého fyzického agenta;
- kulturu/populační dynamiku.

AI-side persistence a social hooks jsou připravené, ale World se podle zadání doladí až později.

## 24. Acceptance pro field test

Field test V5 má ověřit minimálně:

1. agent při slepé uličce nevytváří nekonečný look loop;
2. po ověřené cestě do slepé větve vytvoří spatial backtrack;
3. vrací se směrem k poslednímu route place;
4. opakovaný nulový progress zvyšuje stagnation;
5. context-specific prediction se mění podle skutečných outcomes;
6. risky/failed akce dostávají vyšší risk;
7. object track přežije krátké zmizení ze zorného pole;
8. cognitive-state je dohledatelný v decision rationale;
9. schema migration zachová staré beliefs/episodes;
10. CI, benchmark a repository audit zůstanou green.

## CLI

Lokální diagnostika:

```bash
.venv/bin/python -m alua cognition-status
```

Ukazuje:
- počty cognitive recordů podle typu;
- aktivní missions;
- poslední metacognitive/cognitive snapshot.
