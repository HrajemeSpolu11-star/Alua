# Učení a rozhodování

## Základní smyčka

Alua se učí z posloupnosti:

    stav přesvědčení
      + nový vjem
      + zvolená akce
      + pozdější vjem
      = změna očekávání

HTTP odpověď není fyzický outcome.

## Outcome attribution

Při odeslání akce vznikne pending expectation:
- client_action_id;
- action type;
- kontext;
- target signature, pokud existuje;
- očekávané pozorovatelné změny;
- časové okno;
- confidence očekávání.

Budoucí observations mohou expectation:
- podpořit;
- vyvrátit;
- nechat nerozhodnuté.

## Anti-loop invariant

Informační akce nesmí samy sebe donekonečna udržovat pouze proto, že jejich motorické provedení bylo úspěšné.

Aktuální V1 proto vyžaduje:
- `scan_recovery` pouze jako reakci na novější neúspěšný exploration pokus;
- `scan_obstacle` nejvýše jednou před intervenujícím motorickým exploration pokusem;
- scan/look není reusable procedural skill;
- reusable move skill se nepoužije, pokud aktuální percept hlásí blízkou centrální překážku;
- context-specific bypass se bez explicitního precondition modelu nepromuje na generic skill.

Motor success znamená, že se primitivní akce fyzicky provedla. Není automatickým důkazem, že informační nebo navigační cíl byl strategicky dokončen.

## Exploration

Úplně neznámý agent potřebuje schopnost bezpečně zkoušet.

V1 používá omezenou exploraci:
- look před riskantnější manipulací;
- krátké move kroky;
- wait pro pozorování dynamiky;
- interact nebo manipulate pouze na aktuálně dostupném target_ref;
- risk budget podle předchozí negativní zkušenosti.

Exploration nesmí být nekonečné náhodné chování.

## Needs a utility

Fyzické potřeby pocházejí pouze z vjemů těla, které dodá AluaWorld.

Kognitivní vrstva může přidat malé interní utility:
- snížení bezprostředního známého rizika;
- dokončení aktivního cíle;
- získání informace;
- zabránění opakování známého škodlivého výsledku.

V1 nesmí obsahovat skrytou tabulku typu item X je jídlo nebo node Y je cenný.

## Goal selection

Kandidátní cíl má:
- origin;
- priority;
- expected utility;
- urgency;
- uncertainty;
- estimated cost;
- evidence.

Vybraný cíl se zapíše do decision trace.

## Planner

První planner má být malý a deterministický.

Podmínky:
- pracuje pouze s primitivními akcemi povolenými session;
- má limit hloubky;
- má limit kandidátů;
- umí bezpečně selhat;
- při nové důležité observation přeplánuje;
- nesmí generovat libovolný kód nebo shell.

## Učení vztahů

První verze se zaměří na:
- četnost pozorovaných přechodů;
- úspěšnost opakovaných akcí v podobném kontextu;
- risk score;
- novelty score;
- confidence aktualizovanou podpůrnou a rozpornou evidencí.

Pokročilé neuronové modely nejsou podmínkou V1.

## LLM

Externí LLM není součástí základního autonomního cyklu.

Později může být přidán jako volitelný diagnostický nebo jazykový modul, ale nesmí:
- dostat world truth mimo perception boundary;
- nahrazovat perzistentní kognitivní stav;
- být jediným zdrojem rozhodnutí;
- měnit beliefs bez evidence.

## Hierarchické rozhodování V2

Aktuální runtime odděluje:
1. reflex/intrinsic goal;
2. composite skill;
3. bounded plan;
4. lokální controller;
5. primitive action.

Příklad:

```text
explore
 -> bypass_obstacle
 -> navigate_lateral
 -> nový vjem/outcome
 -> navigate_frontier
```

Planner nikdy negeneruje libovolný program. Rozkládá goal pouze na známé bezpečné controller steps.

## Information gain

Runtime už nepoužívá periodický scan pouze jako pevný modulo trigger. Egocentrický world model odhaduje horizontální uncertainty a curriculum žádá information scan tehdy, když lokální model skutečně potřebuje další informaci.

## Self-critic

BehaviorCritic sleduje pouze vlastní trajectory:
- repeated look;
- action stereotype;
- opakované neúspěšné move;
- goal stagnation kombinovanou s chybějícím motorickým pokrokem.

Výsledek criticu je replan signál, nikoli belief.

## Lokální navigační učení

LocalNavigator udržuje session-local failure penalty pro konkrétní manévry. Neúspěšný fyzický outcome zvýší cenu stejného manévru; úspěch ji sníží. Po každém novém vjemu se směry znovu ohodnotí.

Dlouhodobé empirické skills zůstávají v SQLite a používají se pouze pokud neodporují aktuálnímu smyslovému kontextu.

## Adaptive utility V3

Intrinsic kandidáti jsou po vytvoření hodnoceni `AdaptiveUtilityModel`.

Skóre obsahuje pouze epistemicky dovolené veličiny:
- base priority;
- Beta-smoothed empirical success/failure;
- current information need;
- novelty;
- recent bodily damage;
- malý prior náklad akce.

Reflex survival zůstává mimo tuto soutěž a preemptuje intrinsic cíle.

## Persistentní transition learning

Po move se uloží pouze:

```text
vjemový kontext před akcí
+ typ manévru
+ vjemový kontext po akci
+ sensory outcome success/failure
```

LocalNavigator z této zkušenosti odvozuje persistentní penalty. Agent se tak může po restartu vyhnout manévru, který ve stejném perceptuálním kontextu opakovaně selhával, aniž by znal mapu nebo materiál.

## Belief evidence

Každý motoricky naučený belief může být zpětně spojen s observation sequence a decision ID, které jej podpořily nebo vyvrátily. Confidence zůstává Beta-smoothed a další zkušenost jej může změnit.


## Cognitive Core V5 – prediction, causality a meta-learning

V5 přidává několik typů učení, které jsou záměrně oddělené:

### Context-specific prediction

```text
perceptual context + action
-> expected progress
-> expected success
-> confidence
```

Po outcome se uloží prediction error. Vysoká chyba zvyšuje metakognitivní pressure na přehodnocení modelu.

### Risk learning

Risk se učí z:
- failure;
- nízkého progressu;
- slip;
- recent damage.

Risk je kontextový. Úspěšný jump v jednom kontextu nevytváří globální „jump je bezpečný“.

### Self-model learning

Alua si vede empirickou statistiku vlastních capabilities:
- attempts;
- success rate;
- mean progress;
- mean effort;
- confidence.

### Interventional causal hypotheses

Vztah akce -> pozdější bodily/motor effect se ukládá jako hypothesis. Korelace bez vlastní intervence není automaticky kauzální belief.

### Counterfactual deliberation

Při stagnaci lze porovnat bounded množinu alternativ podle:
- expected progress;
- expected success;
- learned risk;
- model confidence/information value;
- weak transferable strategy prior.

Vybere se jeden krok a potom se znovu replánuje z čerstvé observation.

### Strategy meta-learning

`strategy.py` udržuje slabší prior přes podobné cíle a action patterns. Je to transfer hint, nikoli náhrada context-specific prediction.

### Active experiments

Když je uncertainty vysoká a safety/homeostasis dovolí, může `ExperimentPlanner` vytvořit nízkorizikový informační experiment. První povolená primitive je touch.

### Concept formation

Concept vzniká pouze ze společných evidence-backed relations více opaque appearances. Žádný technický název objektu se do abstraction vrstvy nepřenáší.



## V5 – úplný outcome learning chain

ACK nikdy není world outcome. Až budoucí motor event korelovaný přes `source_sequence` uzavírá intervention cycle.

Po resolved outcome se aktualizují:
1. PerceptualTopology transition;
2. PredictiveModel a prediction error;
3. SelfModel capability evidence;
4. RiskModel;
5. CausalLearner;
6. StrategyLearner, pokud expectation zná goal kind;
7. SpatialMemory route/odometry/backtracking evidence;
8. Metacognition progress/prediction error;
9. Executive navigator + critic;
10. původní belief learning;
11. goal success/failure stats;
12. reusable skill evidence.

Tím se drží oddělené:
- přijetí požadavku;
- fyzický následek;
- kognitivní interpretace.

### V5 priorita goal arbitration

1. reflexní survival goal;
2. evidence-backed `spatial_backtrack`;
3. `deliberate_navigation` při silné stagnaci/model error;
4. low-risk active experiment;
5. standardní intrinsic/need goals rankované utility modelem;
6. mission/drive bonusy pouze jako úprava score.

Vyšší cognition nikdy neobchází fresh perception, pending-expectation gate ani World physical constraints.

Kompletní postup: `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.
