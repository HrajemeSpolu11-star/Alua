# Adaptive Cognition V3

Aktualizováno: 2026-10-07.

## Proč vznikla V3

Cognitive Architecture V2 oddělila goal, planner, skill a lokální motorický controller. V3 přidává to, co chybělo k dlouhodobě adaptivnímu chování:

- výběr cílů podle evidence, rizika a informační hodnoty;
- dlouhodobou perceptuální topologii bez přístupu ke skryté mapě;
- persistentní zkušenost s tím, které manévry v podobném vjemovém kontextu fungují;
- dohledatelnou provenance každého nově naučeného beliefu;
- offline sensory replay a behaviorální acceptance gate;
- korektní invalidaci egocentrického modelu po otočení hlavy.

V3 zachovává celé funkční V1/V2 rozhraní AluaWorld -> AluaBridge -> Alua.

## AdaptiveUtilityModel

Soubor: `src/alua/utility.py`.

Intrinsic goal už není hodnocen pouze pevnou prioritou. Utility model kombinuje:

- intrinsic base priority;
- vlastní historickou úspěšnost goalu;
- vlastní failure evidence;
- informační nejistotu;
- perceptuální novelty;
- nedávný damage signal;
- malý action-cost prior.

Historická úspěšnost používá Beta(1,1) prior. Řídká zkušenost proto nikdy nevytvoří absolutní jistotu po jednom pokusu.

Utility model nezná význam objektů. Neobsahuje pravidla typu „dřevo je užitečné“ nebo „toto je nepřítel“. Hodnotí pouze zkušenost Alua.

Reflex `survive_damage` zůstává nad intrinsic utility vrstvou a má bezpečnostní přednost.

## PerceptualTopology

Soubor: `src/alua/topology.py`.

V3 vytváří dlouhodobou mapu přechodů mezi rozpoznanými perceptuálními kontexty.

Nejde o mapu souřadnic.

```text
sensory frame
 -> perceptual place signature
 -> move maneuver
 -> future sensory frame
 -> next perceptual place signature
 -> supported / contradicted transition evidence
```

Place signature vzniká pouze z:
- appearance signatures;
- hrubých vzdálenostních bucketů;
- blocks-motion/liquid signálů;
- bezpečných contact signálů;
- omezených hearing signatures.

Do podpisu nevstupuje:
- target_ref;
- node name;
- material ID;
- absolutní poloha;
- admin telemetry;
- World katalog.

Podpis není tvrzení, že jde o unikátní fyzické místo. Je to pouze znovu rozpoznatelný perceptuální kontext.

### Persistentní transitions

SQLite ukládá evidenci:

```text
from perceptual context
+ maneuver
-> resulting perceptual context
+ success/failure evidence
```

LocalNavigator používá tuto historickou evidenci jako penalty prior.

Výsledek:
- když `left` ve stejném perceptuálním kontextu opakovaně fyzicky selhává, budoucí volba `left` je dražší;
- úspěšná zkušenost penalty postupně snižuje;
- zkušenost přežije restart AI;
- změna World session nemaže naučenou topologii, ale zruší pouze pending session-local přechod.

## View-frame invalidation

Egocentrický model používá sektory `front/left/right/up/down`.

Úspěšný `look` změní referenční rámec hlavy. Staré „front“ po otočení už není stejné „front“.

V3 proto po potvrzeném look outcome zahodí směrový cache world modelu ještě před ingestem nového frame.

Tím se zabrání míchání senzorických dat z různých orientací.

## Belief provenance

SQLite schema V4 přidává `belief_evidence`.

Každá aktualizace beliefu vzniklá z motorického outcome může nést:
- agent_id;
- belief_key;
- World session_id;
- observation_sequence;
- decision_id;
- supported / contradicted;
- timestamp.

To umožňuje zpětně odpovědět:

> Z jakých skutečných zkušeností Alua vytvořila tento belief?

Belief stále zůstává opravitelný další evidencí.

## SQLite schema V4

Nové tabulky:

- `belief_evidence`;
- `perceptual_places`;
- `perceptual_transitions`.

Při prvním startu nad starší DB Store automaticky vytvoří SQLite backup ve stejném adresáři před migrací.

Existující:
- episodes;
- decisions;
- expectations;
- beliefs;
- goals;
- skills

se nemažou.

## Offline replay a benchmark

V3 umí znovu projet uložené sensory episodes přes lokální world model bez běžící hry:

```text
persisted episode
 -> PerceptionFrame
 -> EgocentricWorldModel
 -> uncertainty / blocked-front / perceptual-place metrics
```

Behaviorální trace se současně vyhodnotí z decisions + sensory outcomes.

### Report

```bash
.venv/bin/python -m alua evaluate --limit 2000
```

### Acceptance benchmark

```bash
.venv/bin/python -m alua benchmark --limit 2000
```

Benchmark kontroluje:
- žádný opakovaný `look -> look` loop;
- žádný dlouhý action stereotype;
- přijatelnou move success rate, pokud je dost vzorků;
- existenci rozhodnutí;
- existenci skutečných resolved outcomes;
- existenci sensory replay;
- že sensory data časově pokrývají rozhodovací stopu.

Při nesplnění vrací CLI nenulový exit code.

## Co bylo převzato jako princip

### Voyager
- evidence-driven curriculum;
- dlouhodobé skills;
- critic/self-improvement loop.

### Odyssey / OpenHA
- hierarchie primitivní -> kompozitní behaviorální schopnost;
- oddělení high-level záměru od motorického controlleru.

### Mineflayer Pathfinder / Baritone
- cost-based movement;
- replanning;
- penalizace neúspěšných cest.

Alua ale nečte globální mapu. Cost vzniká pouze z vlastního perceptu a vlastní transition evidence.

### Craftium / MineStudio
- trajectories jako první třída diagnostiky;
- offline replay;
- benchmark/acceptance oddělený od live runtime.

### luanti-voyager
- potvrzení architektury externího Python agenta;
- memory a testovatelný agent lifecycle.

### Mindcraft
- modulární oddělení behaviorálního řízení, memory a budoucí multi-agent vrstvy.

## Co záměrně nebylo převzato

### Externí LLM jako hlavní mozek

Nepřevzato. Alua musí být autonomní i offline a na telefonu. LLM může být v budoucnu jazykový nebo deliberativní modul, ne jediný vlastník kognice.

### Generování a spouštění libovolného kódu

Nepřevzato. SkillGraph je data-only a execution jde pouze přes povolené primitive actions.

### Minecraft world knowledge

Nepřevzato. Žádné recepty, názvy bloků, biome, globální souřadnice ani hotové významy.

### Globální pathfinder nad World mapou

Nepřevzato. Porušil by epistemickou hranici.

### Sdílená databáze více agentů

Nepřevzato. Budoucí Alua se budou učit a komunikovat přes explicitní world mechanismus, nikoli čtením cizí paměti.

## Další logická vrstva

Po V3 je správné pořadí:
1. terénní soak test V2/V3;
2. explicitní harm/risk learning pro jednotlivé manipulace;
3. bezpečný experimentální ladder `touch -> pickup -> release -> push`;
4. automatická indukce composite skillů z opakovaně úspěšných trajectories;
5. needs/metabolismus z fyzického těla;
6. dlouhodobější deliberativní planner;
7. fyzická komunikace více agentů.

Destruktivní `break_object` zůstává vypnutý, dokud Alua nemá dostatečně vyspělý risk/utility a recovery model.

## Terénní korekce motorického učení

Field test po V3 ukázal, že persistentní transition learning je pouze tak dobrý jako motorická evidence z Worldu.

V3 proto nyní používá graded locomotion quality:
- `progress_signal` = normalizovaný projected postup v požadovaném směru;
- `slip_signal` = podíl pohybu mimo požadovaný směr;
- `partial_effect` = fyzický efekt, který nestačí jako navigační success.

Persistentní transition evidence, goal outcome, skill evidence i local navigation penalty používají stejný motor-success invariant.

Stagnation recovery už není jen další pohybový manévr. Composite skill nejprve fyzicky změní orientaci těla a potom z nového sensory frame pokračuje escape pohybem.

Detail: `docs/INCIDENT_2026-10-07_ONE_BLOCK_BOUNCE.md`.
