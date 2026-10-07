# Audit open-source referencí pro Alua Cognitive V2

Datum: 2026-10-07.

## Účel

Před V2 byl porovnán současný Alua runtime s veřejnými agentními projekty. Cílem nebylo vložit cizí herní znalosti ani přepsat funkční AluaWorld/AluaBridge architekturu. Převzaty byly pouze obecné architektonické principy, které respektují epistemickou hranici Alua.

V implementaci V2 nebyl přímo zkopírován zdrojový kód uvedených projektů. Baritone je LGPL-3.0, proto z něj byla použita pouze algoritmická inspirace. MIT projekty zůstávají uvedeny jako reference.

## Reference a převzatý princip

### Voyager / MineDojo
Repository: https://github.com/MineDojo/Voyager
Licence: MIT.

Relevantní principy:
- automatic curriculum;
- iterative feedback / critic;
- growing skill library;
- retrieval dříve úspěšných postupů;
- oddělení task selection, action generation a skill memory.

Implementace v Alua:
- `IntrinsicCurriculum` zůstává world-truth-free;
- nový `BehaviorCritic`;
- existující `SkillLibrary` je zachována;
- nový `SkillGraph` skládá behaviorální makro-skills;
- planner a controller jsou oddělené vrstvy.

Nepřevzato:
- Minecraft názvy itemů/bloků;
- externí QA databáze;
- LLM jako povinný rozhodovací motor;
- generování JavaScript programů.

### Odyssey
Repository: https://github.com/zju-vipa/Odyssey
Licence kódu: MIT.

Relevantní princip:
- rozdělení primitive a composite skills;
- dlouhodobější plánování pomocí opakovaně použitelných schopností.

Implementace v Alua:
- `SkillGraph` s bounded composite behavior skills;
- `BoundedPlanner` rozkládá goal na několik abstraktních controller steps.

Nepřevzato:
- Minecraft knowledge base;
- datasety nebo herní recepty;
- hotové skill skripty.

### luanti-voyager
Repository: https://github.com/toddllm/luanti-voyager
Licence: MIT.

Relevantní principy:
- oddělený Python agent pro Luanti;
- agent state / memory;
- viewer a testovatelnost;
- více-agentní směr vývoje.

Implementace v Alua:
- potvrzuje vhodnost samostatného procesu;
- offline evaluator a jasná session-local diagnostika;
- zachován vlastní bezpečnější Bridge boundary místo file-command zkratek.

Nepřevzato:
- teleport/generate fallbacky;
- technické node names jako přímé world state;
- file-based command transport.

### Mineflayer Pathfinder
Repository: https://github.com/PrismarineJS/mineflayer-pathfinder
Licence: MIT.

Relevantní princip:
- goals + cost-based movement;
- průběžné replanning;
- oddělení high-level cíle od lokálního movement controlleru.

Implementace v Alua:
- `LocalNavigator`;
- candidate maneuver costs;
- failure penalty;
- replan po každé nové observation.

Rozdíl:
- Alua navigator nečte globální mapu. Používá pouze svůj egocentrický sensory world model.

### Baritone
Repository: https://github.com/cabaletta/baritone
Licence: LGPL-3.0.

Relevantní principy:
- A* / cost-based pathfinding;
- movement costs;
- path execution a replanning;
- avoidance.

Implementace v Alua:
- pouze obecný princip cost-based výběru a replanningu;
- žádný Baritone kód ani LGPL soubor nebyl vložen do Alua.

### Craftium
Repository: https://github.com/mikelma/craftium

Relevantní principy:
- agent/environment boundary;
- synchronizované agentní kroky;
- reproducibilní evaluation prostředí;
- multi-agent výzkumné testy.

Implementace v Alua:
- decision/outcome trace je explicitně vyhodnotitelný;
- `alua evaluate` poskytuje reproducibilní metriky nad aktuální session;
- session-local planner/world model se resetuje odděleně od long-term memory.

Budoucí kandidát:
- deterministický replay sandbox nad uloženými epizodami.

### MineStudio
Repository: https://github.com/CraftJarvis/MineStudio

Relevantní principy:
- trajectories;
- benchmark/evaluation;
- oddělení training/evaluation od live runtime.

Implementace v Alua:
- `Store.session_trace()`;
- `evaluation.py`;
- quality flags nad skutečnými embodied trajectories.

### OpenHA
Repository: https://github.com/CraftJarvis/OpenHA

Relevantní princip:
- hierarchie high-level action -> grounding -> motion control.

Implementace v Alua:
- goal -> SkillGraph -> PlanStep -> LocalNavigator/ExplorationPolicy -> primitive Bridge action.

### Mindcraft
Repository: https://github.com/mindcraft-bots/mindcraft
Licence: MIT.

Relevantní principy:
- více agentů;
- profily/role;
- koordinace;
- oddělení action manageru, memory a behavior modes.

Implementace nyní:
- modulární executive je připraven pro samostatné agent procesy.

Záměrně odloženo:
- přímé sdílení paměti mezi agenty. Projektová politika vyžaduje, aby budoucí komunikace probíhala přes explicitní světový komunikační kontrakt.

## Co bylo zachováno z Alua V1

Beze změny zůstává:
- AluaWorld jako autorita fyziky;
- AluaBridge jako jediná transportní cesta;
- strict observation schema;
- zákaz world truth;
- ephemeral `target_ref`;
- WorkingMemory;
- SQLite episodes/decisions/expectations/beliefs;
- future-observation outcome attribution;
- session recovery;
- empirical learned skills;
- bezpečný `touch`;
- zákaz autonomního pickup/push/break bez risk modelu.

## Výsledek

V2 nepřepisuje fungující systém. Přidává vrstvu, která v původním V1 chyběla:

```text
perception
 -> local world model
 -> curriculum/reflex goal
 -> hierarchical skill
 -> bounded plan
 -> local navigation/controller
 -> action
 -> sensory outcome
 -> critic + learning
```

Tím se loop prevention přesouvá z jednotlivých ad-hoc podmínek na strukturální řízení chování.

## Druhá implementační vlna – Adaptive Cognition V3

Po první V2 implementaci byly z referencí vytěženy další principy, které jsou kompatibilní s filosofií Alua:

- Voyager: curriculum není pevný seznam; V3 přidává evidence-weighted adaptive utility;
- Mineflayer Pathfinder / Baritone: náklad směru se má měnit zkušeností; V3 persistuje maneuver success/failure evidence v perceptuálním kontextu;
- Craftium / MineStudio: uložené trajectories mají být replayovatelné a benchmarkovatelné; V3 přidává sensory replay a `alua benchmark`;
- výzkumné agentní systémy obecně: interní model musí mít provenance; schema v4 přidává `belief_evidence`.

Nadále nebyl kopírován cizí zdrojový kód ani Minecraft-specific knowledge.

### Funkce, které nebyly implementovány úmyslně

Následující reference obsahují schopnosti, které jsou technicky zajímavé, ale pro současnou Alua by byly kontraproduktivní:

- generování spustitelného kódu LLM agentem – porušuje bezpečný primitive-action model;
- přímý globální map/pathfinder přístup – porušuje epistemickou hranici;
- hotové Minecraft recipes/block semantics – ruší učení významu ze zkušenosti;
- teleport/generate recovery – obchází fyzické tělo;
- sdílená memory multi-agentů – obchází budoucí fyzickou komunikaci.

Tyto body nejsou „zapomenutý backlog“, ale vědomě odmítnuté zkratky.
