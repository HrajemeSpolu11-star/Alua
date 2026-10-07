# Kognitivní architektura V2

Aktualizováno: 2026-10-07.

## Cíl

V2 odděluje rozhodování na více úrovní, aby Alua nepřemýšlela pouze v primitivách `look/move/touch`.

Zachovaný embodied kontrakt:

```text
AluaWorld
  -> observation
AluaBridge
  -> validated Agent API
Alua
  perception
  -> working memory
  -> egocentric world model
  -> intrinsic/reflex goal
  -> bounded planner
  -> skill graph
  -> local controller/navigation
  -> primitive ActionRequest
AluaBridge
  -> World
  -> future sensory outcome
Alua
  -> critic + beliefs + skill evidence
```

V2 nemění autoritu Worldu ani Bridge. Nezavádí skrytou mapu, technické názvy nodů ani externí LLM do hlavního cyklu.

## Moduly

### `world_model.py`

Vlastník krátkodobého lokálního modelu okolí.

Model je egocentrický a bounded. Sektory:
- front;
- left;
- right;
- down;
- up.

Pro každý sektor drží pouze smyslově odvozené:
- openness;
- blocked probability;
- novelty;
- confidence;
- poslední observation sequence;
- poslední appearance signature.

Neukládá absolutní mapovou polohu ani technickou identitu objektu.

### `navigation.py`

Receding-horizon lokální navigace.

Princip:
1. z aktuálního world modelu ohodnotí bezpečné kandidátní manévry;
2. penalizuje blokovaný směr;
3. penalizuje manévr, který opakovaně fyzicky selhal;
4. penalizuje stereotypní opakování;
5. zvýhodní aktuálně otevřený / informačně zajímavý směr;
6. provede pouze jeden krátký fyzický krok;
7. po novém vjemu znovu plánuje.

Nejde o vševědoucí A* nad mapou. Jde o lokální obdobu cost-based pathfindingu z dat, která Alua skutečně vnímá.

### `critic.py`

Deterministický self-critic.

Sleduje:
- opakované `look`;
- příliš dlouhý stejný action stereotyp;
- tři po sobě neúspěšné move outcomes;
- dlouhé setrvání na jednom goalu pouze tehdy, pokud současně chybí motorický pokrok.

Critic nepřepisuje beliefs a nečte world truth. Dává executive pouze signál k přeplánování.

### `skill_graph.py`

Bezpečná hierarchie behaviorálních skillů.

Vestavěné V2 makro-skills:
- `survive_retreat`;
- `inspect_by_touch`;
- `scan_environment`;
- `explore_frontier`;
- `bypass_obstacle`;
- `escape_stagnation`.

Skill graph je data-only. Negeneruje ani nespouští Python/JavaScript kód.

Existující `SkillLibrary` zůstává vlastníkem empiricky naučených primitivních reusable skillů.

### `planning.py`

Bounded hierarchical planner.

High-level goal mapuje na krátký skill plán s tvrdým limitem kroků.

Příklad:

```text
goal: explore
front blocked
  ->
skill: bypass_obstacle
  ->
step 0: navigate_lateral
step 1: navigate_frontier
```

Po každém skutečném outcome může být plán:
- posunut na další krok;
- zrušen;
- přeplánován podle nového vjemu.

### `executive.py`

Orchestruje:
- world model;
- navigator;
- critic;
- planner;
- původní bezpečnou ExplorationPolicy.

Executive také rozhoduje, zda je bezpečné použít starý naučený reusable skill. Explore skill není použit, pokud:
- critic požaduje replan;
- před agentem je překážka;
- aktuální lokální model doporučuje jiný směr než forward.

Tím se naučená motorická rutina nesmí stát silnější než nový smyslový důkaz.

### `evaluation.py`

Offline behaviorální metriky nad existujícím decision/outcome trace.

CLI:

```bash
.venv/bin/python -m alua evaluate
.venv/bin/python -m alua evaluate --limit 2000
```

Metriky:
- počty action a goal kindů;
- nejdelší streak stejné akce;
- nejdelší `look` streak;
- počet sousedních `look -> look`;
- outcome success rate;
- move success rate;
- stale target count;
- quality flags pro look loop, action stereotype a nízkou úspěšnost pohybu.

Tato diagnostika používá pouze lokální Alua SQLite.

## Curriculum V2

Periodický scan už v hlavním runtime nevzniká pouze podle parity/modula observation sequence.

Executive world model poskytuje `horizontal_uncertainty`. Intrinsic curriculum provede information scan pouze při dostatečné nejistotě. Starý modulo trigger zůstává pouze jako kompatibilní fallback pro izolované testy/starší volající.

Tím se informační akce vážou na skutečnou potřebu informace.

## Persistence

V2 nepřidává nové SQLite tabulky.

Dlouhodobě se dál ukládají:
- episodes;
- decisions;
- expectations;
- beliefs;
- goal stats;
- learned skills.

World model, critic, aktivní planner a failure penalties jsou session-local RAM stav. Po změně `session_id` se resetují, protože obsahují lokální kontext konkrétního těla/world runtime.

Decision rationale ukládá:
- `plan_id`;
- `plan_skill`;
- `plan_step`;
- `plan_step_index`;
- critic reasons;
- sanitizovaný world-model diagnostic summary;
- candidate navigation scores.

Díky tomu lze chování zpětně analyzovat bez přidávání world truth.

## Failure modes

### Planner se zasekne

Critic zruší aktivní plán a `escape_stagnation` zvolí jiný lokální manévr.

### Naučený forward skill přestane být vhodný

Executive jej nedovolí, pokud aktuální model doporučuje jiný směr nebo hlásí překážku.

### Nová World session

WorkingMemory i celý V2 session-local executive stav se resetují. Epizodická a empirická dlouhodobá paměť zůstává.

### Chybí některé vision ray

World model sníží confidence a chybějící sektor považuje za nejistý, nikoli za jistě volný.

## Co V2 záměrně stále nedělá

- nepoužívá skrytou globální mapu;
- negeneruje spustitelný kód;
- nemá cloud LLM v hlavním loopu;
- neprovádí autonomní destruktivní manipulaci;
- nesdílí paměť mezi agenty;
- nepovažuje HTTP ACK za fyzický úspěch.

Další rozšíření má navázat risk/utility learningem, explicitními preconditions naučených composite skills a dlouhodobou topologickou pamětí odvozenou pouze z vlastních senzorických zkušeností.
