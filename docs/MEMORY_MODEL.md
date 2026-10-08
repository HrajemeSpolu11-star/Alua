# Model paměti Alua AI

## Cíl

Paměť musí umožnit učení a kontinuitu identity, ale nesmí růst bez omezení ani zaměnit transportní data za zkušenost.

## 1. Working memory

Obsahuje pouze krátký aktivní kontext:
- poslední observations;
- aktuální percepty;
- aktivní target_ref;
- současný cíl;
- rozpracovaný plán;
- očekávané následky posledních akcí;
- krátkodobé signály nebezpečí.

Working memory je bounded a po restartu ji lze částečně rekonstruovat pouze z perzistentního stavu.

## 2. Episodic memory

Epizoda popisuje zkušenost v čase.

Minimálně:
- agent_id;
- session_id;
- simulation_time;
- observation sequence;
- percept summary;
- interní stav;
- zvolený cíl;
- action intent;
- client_action_id;
- pozdější outcome evidence;
- odkazy na vzniklé nebo změněné beliefs.

Neukládá tajné tokeny.

## 3. Semantic / belief memory

Obsahuje naučené vztahy a zobecnění.

Příklad:
- perceptual signature -> typické reakce;
- akce v kontextu -> distribuce následků;
- signál -> odhad rizika;
- lokální vzorec -> pravděpodobný přechod.

Každý záznam je opravovatelný.

## 4. Procedural memory

Pozdější vrstva pro naučené postupy:
- sekvence akcí, které často vedou k cíli;
- podmínky použití;
- úspěšnost;
- náklady;
- známé failure modes.

Procedura nikdy nesmí obejít Bridge primitivní akce.

## Retence

V1:
- raw observations: omezená nebo časově řízená retence;
- epizody: dlouhodobé, ale s budoucí kompresí;
- beliefs: dlouhodobé;
- decision trace: omezená retence pro diagnostiku;
- target_ref: pouze krátkodobě;
- transportní retry metadata: pouze dokud jsou relevantní.

## Identita

Stabilní agent_id určuje identitu kognitivního agenta.

Restart procesu:
- nesmí resetovat dlouhodobou paměť;
- nesmí změnit agent_id;
- musí navázat na poslední bezpečně commitnutou observation sequence.

Nová Bridge session:
- neznamená novou osobnost;
- znamená nový krátkodobý World runtime kontext.

## Migrace

SQLite schema má explicitní integer verzi.

Každá změna:
- má forward migraci;
- nesmí tiše zahodit beliefs;
- zálohuje nebo odmítne neznámou novější verzi;
- má unit test migrace.

## Izolace

V1 preferuje:
    jedna Alua = jeden proces = jedna SQLite databáze.

Až později lze přidat supervisor více agentů. Sdílená DB nesmí být zavedena jen kvůli pohodlí.

## V3 – perceptuální topologie a provenance

Dlouhodobá paměť nyní obsahuje také:

### `perceptual_places`

Rozpoznané perceptuální kontexty. Nejde o absolutní pozice. Signature vzniká pouze ze smyslových signálů a může být nejednoznačná.

### `perceptual_transitions`

Evidence přechodu:

```text
place_signature A
+ maneuver
-> place_signature B
+ support / contradiction
```

Používá se jako prior pro budoucí lokální navigaci.

### `belief_evidence`

Auditní vazba beliefu na konkrétní zkušenost:
- session;
- observation sequence;
- decision;
- support/contradiction.

Schema v4 před migrací starší DB automaticky vytváří backup. Stávající epizody, beliefs, goals a skills se zachovávají.


## V5 – rozšířená kognitivní paměť

Schema v5 přidává `cognitive_records`, generický namespaced store pro vyšší modely.

Používané record kinds zahrnují:
- `object_concept`;
- `spatial_place` a `spatial_transition`;
- `predictive_model`;
- `risk_model`;
- `self_model`;
- `causal_hypothesis`;
- `temporal_pattern`;
- `prospective_intent`;
- `mission`;
- `abstract_concept`;
- `strategy_model`;
- `social_model`, `social_testimony` a budoucí peer model;
- `episodic_summary`;
- `metacognitive_state`.

### Paměť prostoru

Route memory je session-local pracovní struktura, ale place/transition evidence se může persistovat jako perceptuální zkušenost. Relativní odometrie má uncertainty a není World souřadnice.

### Object permanence

Opaque `appearance_id` může mít bounded track i po krátkém zmizení ze zorného pole. `target_ref` se jako identita nepoužívá.

### Prospective a mission memory

Prospective record uchovává „později udělat X při triggeru Y“. Mission je dlouhodobější přerušitelný záměr.

### Konsolidace

Po bounded intervalu:
- vytvoří summary poslední trajectory;
- starým beliefs pomalu posune confidence směrem k nejistotě;
- vytvoří concept candidates ze společných evidence-backed affordances.

Cílem je dlouhodobá paměť bez nutnosti držet každý raw frame jako stejně významný.



### Session-local vs. persistentní V5 stav

Session-local:
- current attention history;
- route stack;
- relative heading/odometry;
- metacognitive short windows;
- pending CognitiveCore action/context;
- active perceptual target handles.

Persistentní:
- object concepts;
- spatial place/transition evidence;
- prediction/risk/self/causal/strategy records;
- temporal patterns;
- missions;
- prospective intents;
- abstract concepts;
- episodic summaries;
- poslední cognitive snapshot.

Při změně Bridge session se session-local motorický kontext resetuje. Dlouhodobá evidence zůstává, ale nesmí obsahovat starý `target_ref`.

### Schema v5 migration invariant

Forward migrace:
- před změnou vytvoří backup;
- nesmí mazat legacy episodes/beliefs/goals/skills;
- nesmí retroaktivně vymýšlet evidence;
- nový `cognitive_records` store začíná prázdný, pokud stará DB taková data neměla;
- nový runtime si vyšší modely znovu buduje pouze z budoucích zkušeností.

Detailní krokový audit: `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.
