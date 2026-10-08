# Paměť projektu Alua AI pro nový chat

## AKTUÁLNÍ HANDOFF – NOVÝ BACKTRACK PING-PONG INCIDENT (2026-10-08, 12:02 CEST)

- Po opravě need-search PR #15 agent ve světě **stále chodil v malém čtverci**. Nová relace těla `alua:1` (suffix `_e5`) měla v živém `benchmark --limit 500` **496 `spatial_backtrack` / 500 rozhodnutí**, 499 akcí `move`, 495 fyzických úspěchů z 499 (99,2 %), přitom 5 percepčních míst, 100 % předních snímků označených jako blocked, max 495 `move` za sebou. Starý evaluator **chybně PASS**. Nezaměňovat úspěšný motor krok s pokrokem v průzkumu!
- Zdroj: `SpatialMemory.finish_action` uměl při fyzicky úspěšném backtracku bez rozpoznání očekávaného predecessor perceptu uložit krok jako **novou odchozí trasu**, což dovolilo střídání opačných backtrack směrů. `Runtime` dával existujícímu `spatial_backtrack` vždy prioritu.
- Připravené řešení: `SpatialMemory` nyní nerozšiřuje outward route při probíhajícím backtracku, rozpoznané předchozí místo jedině ukončí návrat a max 8 **skutečně ověřených motorických pokusů** dovoluje opustit nedůvěryhodnou hranu. `evaluation.py` testuje dominantní goal-kind loop i při high motor success; regresní testy + full incident `docs/INCIDENT_2026-10-08_BACKTRACK_PINGPONG.md`. **Po CI/merge je potřeba nový živý Termux test; zatím nelze tvrdit vyřešený pohyb.**
- Jak dál: uživatel si přeje postupovat **po jednom příkazu**, všechny chyby a opravy zapisovat do GitHub text docs. Stop pouze proces `alua run`, World a Bridge mohou běžet, pak pull Alua, pip install -e ., spustit AI; nepřepisovat ani nemažte SQLite / uložený svět. Sledujte `spatial_backtrack_fraction`, `longest_backtrack_streak`, unique perceptual places a skutečné splněné potřeby, nikoli jen `outcome_success_rate`. V případě dalšího kroužení zkontrolujte aliased place signatures a multi-ray blokování.

## AKTUÁLNÍ HANDOFF – ŽIVÁ TERMUX AKCEPTACE A PŘETRVÁVAJÍCÍ NAVIGAČNÍ SLABINA (2026-10-08, 11:10 CEST)

- Android Luanti 5.17.0 World běží na portu 30000, lokální AluaBridge na 8787; po Bridge PR #10 a #11 je skutečný stav `/v1/world/observations = HTTP 202`, místo dřívějších 422. Na zařízení změněno `ALUABRIDGE_OBSERVATION_QUEUE` z 4 na 64, `ALUABRIDGE_REQUESTS_PER_MINUTE=1200`.
- `alua doctor` ověřil funkční konfiguraci, SQLite a Bridge session; před spuštěním AI hlásil 900 přijatých pozorování a 0 akcí. Později skutečný mozek spustil přes 200 akcí a získal motorické outcomes. `cognition-status` ukázal mimo jiné 348 kauzálních hypotéz, 49 prostorových míst, 73 přechodů, 58 prediktivních a 58 rizikových modelů. Počet uložených modelů není dokladem jejich správnosti.
- **Kritický živý baseline:** `alua benchmark --limit 500` vyhodnotil 226 rozhodnutí, 225 fyzických outcomes, 86 úspěchů (38,22 %), 139 neúspěchů, 224 pohybů, 175 cílů `satisfy_thirst`, 138 low-progress moves a 59,6 % zablokovaných předních vizuálních vzorků. `acceptance.passed=false`, `action_stereotype_detected=true`, `navigation_stagnation_detected=true`, `low_move_success=true`.
- **Oprava právě stažena na zařízení (`git pull`)**: Alua PR #15, main `605c82485fff773f17b94f85271a15526accdceb`. Zabraňuje tomu, aby hledání vody/potravy bez viditelného zdroje obcházelo lokální navigaci a stereotypně volilo `forward=1`. Regression CI green; **žádný opakovaný live test opravené verze zatím není**. Uživatelská relace mozku byla zastavena přes Ctrl+C; World a Bridge mají zůstat běžet.
- **PŘÍŠTÍ KROK PRO TERMUX, jen jeden po druhém:** ve složce Alua `.venv/bin/python -m pip install -e .`, pak spustit jediný `alua --verbose run`, sledovat reálné outcomes a znovu `alua benchmark --limit 500`. Porovnat s baseline, nevyvozovat z CI živou úspěšnost. Uživatel vyžaduje **jeden krok na zprávu**, screenshot, kontrola a další krok.
- Úplné zdroje incidentu a příčin: `docs/INCIDENT_2026-10-08_NEED_SEARCH_STAGNATION.md` (Alua), `Aluabridge/docs/INCIDENT_WORLD_OBSERVATIONS_422_2026-10-08.md` (Bridge); shrnutí všech tří repo v `AluaWorld/docs/TRI_REPO_AUDIT_2026-10-08.md`. Nikdy neprovádět reset dat. World poskytuje pouze smysly a fyzické důsledky, žádnou skrytou mapu ani názvy interních uzlů Alua AI.

## AKTUÁLNÍ HANDOFF – SOUKROMÝ KOGNITIVNÍ LETOVÝ ZÁZNAMNÍK (2026-10-08)

Na žádost vlastníka přidán příkaz `alua mind-log` pro velmi podrobnou diagnostiku mozku. `--follow` sleduje skutečně uložená rozhodnutí a další jejich fyzické výsledky, `--limit 200` omezuje sledované okno a `--output "$HOME/alua-mind.jsonl"` bezpečně přidává řádky do soukromého souboru 0600. Dle uložených dat vytváří `sensory_episode` (vjem), `cognitive_decision` (goal, action, rationale, `cognitive_state`, expectation a verified motor outcome) a `cognitive_model_snapshot`. Vše jsou skutečné persisted evidences, nikoli domýšlené vědomé myšlenky. Detail: `docs/COGNITIVE_FLIGHT_RECORDER.md`. World ani Bridge nesmějí získat nový API endpoint pro interní AI memory. Změna neovlivňuje samotné rozhodování agenta.


## MEZIREPO AUDIT – 2026-10-08 (současný stav)

Související autoritativní audit všech tří součástí je v
[`AluaWorld/docs/TRI_REPO_AUDIT_2026-10-08.md`](https://github.com/HrajemeSpolu11-star/AluaWorld/blob/main/docs/TRI_REPO_AUDIT_2026-10-08.md).
Kontrolovaná rozhraní: Alua interní Cognitive Core V5 + SQLite v5,
Agent/Bridge/World síťové `schema_version=1`,
smysly body_schema/inventory/vision/hearing/motor a původní fyzický
`source_sequence`. Bridge poskytuje bounded vjemy, World skutečné
motor outcomes, AI teprve z nich vytváří beliefs a kognitivní modely.

AluaWorld zavádí šest odlišně strukturovaných stromů (dub, borovice,
bříza, vrba, jeřáb, mohutný veterán) s odlišnou fyzikou druhového
dřeva a bez restartu uložené mapy. Změny v Worldu **automaticky
neprokazují učení AI**. Než označíme Cognitive V5 za funkční,
vyžadujeme živé `cognition-status`, `evaluate` a `benchmark` s
resolved motor outcomes, backtracking a fyzickou interakci
`pickup→consume` a `drink`.

Stále nehotové: skutečný `social` kanál pro jiné tělo, doménové
`contain/pour` v Worldu a dlouhodobě potvrzované doručení všech
motorických událostí v Bridge. Nezavádět world-truth do AI.
Toto je dokumentační synchronizace, nikoli změna AI runtime.


## AKTUÁLNÍ HANDOFF PRO NOVÝ CHAT – 2026-10-08

### Úplný krokový postup V5

Pro rekonstrukci celé práce nepoužívat jen tento handoff. Autoritativní podrobný postup je:
- `docs/COGNITIVE_CORE_V5.md` – architektonický kontrakt;
- `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md` – úplný krok za krokem audit implementace, CI, deploymentu, rollbacku a acceptance.

Historické sekce níže mohou obsahovat starší stav schema/policy a nesmí přebít aktuální handoff nahoře.

Toto je nejdůležitější souhrn současného stavu. Nový chat má pokračovat **odtud**, ne z historických sekcí níže.

### Stav repozitáře Alua

- Cognitive Core V5 je sloučený do `main`.
- Merge V5: `2da7e5c` – `Cognitive Core V5: memory, prediction, metacognition and backtracking (#10)`.
- Následná dokumentační/validační aktualizace je také v `main`; aktuální ověřený `main` při handoffu: `918aa6f` – `Document final Cognitive Core V5 validation (#11)`.
- Finální validace: **121/121 testů OK**, `tools/audit_repo.py -> AUDIT OK`, Termux E2E shell syntax OK.
- SQLite schema je **v5**. První otevření starší v4 DB udělá automatický pre-v5 backup.

### Co jsme během poslední práce opravili

1. **Look-loop / nekonečné rozhlížení**
   - `scan_recovery`, `scan_obstacle` a `scan_periodic` už nemohou řetězit nekonečné `look`;
   - po scanu musí přijít jiný fyzický pokus;
   - scan direction není jednoduchý parity oscilátor;
   - staré failures samy o sobě už neudržují recovery.

2. **Stale `target_ref`**
   - `409 target_expired` už neshodí runtime;
   - stale decision se označí jako `stale_target`;
   - nevytvoří falešný goal outcome ani expectation;
   - vizuální percept zůstává použitelný i bez čerstvého `target_ref`.

3. **Falešný pohybový úspěch / one-block bounce**
   - motor success už není jen binární ACK;
   - Alua používá `progress_signal` a `slip_signal`;
   - skutečný move success vyžaduje alespoň cca 55 % zamýšleného directional progressu;
   - `partial_effect` není success;
   - LocalNavigator penalizuje manévry podle skutečné kvality pohybu;
   - BehaviorCritic rozlišuje dlouhou normální chůzi od low-progress stagnace;
   - escape plan umí fyzicky reorientovat yaw;
   - ve Worldu byl opraven i zrcadlený left/right vision basis proti locomotion basis.

4. **Slepá ulička**
   - původní V2/V3 uměl poznat problém, ale neuměl se vrátit;
   - V5 přidává vlastní route memory, dead-end evidence, remembered-route backtracking a relativní odometrii;
   - agent při stagnaci může hledat poslední zapamatovaný route edge a vrátit se vlastní cestou místo zmateného lokálního rozhlížení.

5. **Paměť a učení**
   - beliefs mají provenance;
   - perceptuální místa a přechody se persistují;
   - object permanence drží objekt v paměti i po krátkém zmizení ze zorného pole;
   - staré beliefs pomalu decayují místo toho, aby byly navždy absolutní;
   - vznikají bounded episodic summaries;
   - koncepty se tvoří jen z vlastní evidence.

### Co Cognitive Core V5 nyní obsahuje

- `attention.py`: salience, surprise, uncertainty;
- `scene.py` + `temporal.py`: multisenzorová scéna a recurrence;
- `object_memory.py`: object permanence;
- `spatial_memory.py`: route stack, dead-end detection, remembered backtracking, relative X/Z + heading + uncertainty;
- `predictive.py`: action prediction a prediction error;
- bounded counterfactual deliberation: forward / left / right / back;
- `risk.py`: context-sensitive learned risk;
- `self_model.py`: zkušenost s vlastními capabilities;
- `causal.py`: intervention-based causal hypotheses;
- `metacognition.py`: stagnation, loop risk, uncertainty, model error;
- `drives.py`: safety, homeostasis, curiosity, frustration, exploration;
- `experiments.py`: bezpečné aktivní experimenty;
- `prospective.py`: „až nastane X, udělej/připomeň Y“;
- `missions.py`: persistentní přerušitelné dlouhodobější cíle;
- `consolidation.py`: summaries, forgetting/decay, concept consolidation;
- `concepts.py`: evidence-based abstraction;
- `strategy.py`: transferable strategy/meta-learning prior;
- `social.py` + peer-model hooks: připravené, ale bez explicitních social sensory dat z Worldu zatím nemají řídit sociální chování;
- `cognition.py`: orchestrátor celé vyšší vrstvy;
- decision rationale obsahuje `cognitive_state`, takže lze zpětně zjistit, proč agent něco udělal.

### Co už měl agent z Embodied Needs V4 před V5

AI-side rozhodování už umí pracovat s:
- health;
- stamina/výdrží;
- hunger;
- thirst;
- fatigue;
- breath;
- vlastním inventářem;
- pickup/consume/drink/break pouze když to vychází z potřeby/cíle a dostupné evidence;
- terrain locomotion podle signálů těla: walk, sprint, crouch, crawl, jump, vault, climb, swim, controlled drop.

Důležité: World vlastní fyzickou pravdu a capability. AI se neučí z ACK, ale až z budoucího sensory outcome.

### Neměnné epistemické hranice

Alua **nemá a nesmí mít**:
- absolutní World XYZ jako tajnou mapu;
- technické názvy node/item jako hotový význam;
- skryté recepty;
- privilegovanou globální mapu;
- dlouhodobý `target_ref`;
- falešný „success“ pouze z HTTP ACK.

Význam věcí, riziko, užitečnost i schopnosti se mají tvořit z vlastní zkušenosti.

### Tři repozitáře

- **AluaWorld** = fyzika, tělo, smysly, materiály a skutečné následky;
- **AluaBridge** = transport/session/target handles;
- **Alua** = mozek, paměť, cíle, plánování, predikce a učení.

Cognitive Core V5 měnil primárně **Alua**. World se má dolaďovat podle toho, jaké chybějící sensory/action signály AI při field testu skutečně potřebuje.

### Co má nový chat udělat jako první

Na telefonu aktualizovat Alua z `main`, potom:

```bash
cd "$HOME/alua/Alua"
git pull --ff-only
git rev-parse --short HEAD

set -a
. ./.env
set +a

.venv/bin/python -m alua status
.venv/bin/python -m alua cognition-status
```

Očekávání:
- HEAD má odpovídat aktuálnímu `main`;
- `schema_version = 5`;
- stará DB se zachová a při migraci má vzniknout backup.

Pak spustit World + Bridge + AI a udělat nový field test. Tentokrát sledovat hlavně:
- zda při slepé uličce vznikne `spatial_backtrack`;
- zda agent skutečně vrací route, ne jen náhodně kouká;
- `metacognition.recommended_mode`;
- `stagnation`, `loop_risk`, `prediction_surprise`;
- route depth / relative pose;
- learned prediction/risk/self/causal/strategy records;
- zda dlouhá kvalitní chůze není falešně označena jako stagnace.

Po několika minutách:

```bash
.venv/bin/python -m alua evaluate --limit 2000
.venv/bin/python -m alua benchmark --limit 2000
.venv/bin/python -m alua cognition-status
```

### Nejbližší technický cíl

Nezačínat dalším velkým přepisem. Nejprve **živě ověřit V5**. Pokud se agent znovu zasekne, nový chat má analyzovat konkrétní `cognitive_state`, route memory, metacognition a motor outcomes a opravit příčinu. World se má měnit až podle prokázané chybějící fyzické/senzorické informace, ne preventivně.


## Finální validace Cognitive Core V5 – 2026-10-08

Cognitive Core V5 je sloučený do `main`.

Ověřený merge commit:
- `2da7e5c08e961e21e1e4ece36e54a1fe53339dcb`;
- short SHA `2da7e5c`;
- message `Cognitive Core V5: memory, prediction, metacognition and backtracking (#10)`.

Finální GitHub Actions na `main`:
- 121 unit/regression testů;
- všechny prošly;
- `tools/audit_repo.py` -> `AUDIT OK`;
- syntax kontrola Termux E2E helperu prošla.

SQLite schema je nyní v5. První otevření existující v4 DB po pullu provede migraci se zálohou před změnou.

V5 je implementovaná vyšší kognitivní architektura, nikoli tvrzení o hotové AGI. Aktivně běží attention, scene/temporal model, object permanence, route memory/backtracking, relative odometry, prediction/risk/self/causal models, metacognition, drives, experiments, missions, consolidation, concepts a strategy transfer. Social/testimony/peer vrstvy potřebují explicitní budoucí World sensory data, než mohou skutečně řídit sociální chování.


Aktualizováno: 2026-10-07.


## Cognitive Core V5 – aktuální kognitivní vrstva

Field test ve slepé větvi ukázal, že agent uměl poznat špatný motorický progress, ale neuměl použít vlastní historii k návratu. V5 proto přidává vyšší kognitivní vrstvu v repu **Alua**, nikoli hardcoded řešení ve Worldu.

Klíčové moduly:
- `attention.py` – salience/surprise/uncertainty;
- `scene.py` + `temporal.py` – multisensory scene a recurrence;
- `object_memory.py` – object permanence;
- `spatial_memory.py` – route stack, dead-end detection, remembered backtracking, relative odometry;
- `predictive.py` – action prediction + counterfactual ranking;
- `risk.py`, `self_model.py`, `causal.py`;
- `metacognition.py` – stagnation/loop/model-error awareness;
- `drives.py` – regulatory priorities;
- `experiments.py` – bounded safe active experiments;
- `prospective.py` + `missions.py`;
- `concepts.py` + `strategy.py`;
- `consolidation.py`;
- `social.py` + future peer-model hooks;
- `cognition.py` – orchestrator.

SQLite schema je **v5**. První Store-opening command po update vytvoří pre-v5 backup starší DB a zachová staré episodes/beliefs/goals/skills.

Nový diagnostický příkaz:

```bash
.venv/bin/python -m alua cognition-status
```

Autoritativní dokument: `docs/COGNITIVE_CORE_V5.md`.

Důležitý invariant: V5 stále nemá World XYZ, technické názvy item/node, skrytou mapu ani recepty. Návrat používá pouze vlastní route memory a perceptuální signatures.


## Navigační field fix – 2026-10-07

Po V2/V3 field testu se Alua pohybovala, ale odrážela se v malém prostoru. Nešlo pouze o planner problém.

Nalezeno:
- AluaWorld movement success byl příliš benevolentní a neověřoval směr postupu;
- left/right vision basis byl ve Worldu zrcadlený proti body locomotion;
- critic neuměl rozlišit kvalitní dlouhou chůzi od low-progress move loopu;
- escape plan neuměl reorientovat yaw.

Aktuální řešení:
- graded `progress_signal` / `slip_signal`;
- `partial_effect`;
- motor success od 55 % projected progress;
- maneuver-specific stagnation;
- `reorient_escape -> navigate_escape -> navigate_frontier`;
- scan gate respektuje každý physical look.

Pro správný field test je nutné aktualizovat **AluaWorld i Alua**. Bridge kontrakt se nemění.

## Adaptive Cognition V3 – 2026-10-07

Nad Cognitive V2 byla doplněna dlouhodobá adaptivní vrstva:
- `AdaptiveUtilityModel` rankuje intrinsic cíle podle vlastní evidence, uncertainty, novelty a damage;
- `PerceptualTopology` persistuje sensory-only place signatures a move transitions;
- LocalNavigator používá historické transition penalties;
- po úspěšném `look` se invaliduje starý egocentrický view frame;
- SQLite schema je v4 a přidává `belief_evidence`, `perceptual_places`, `perceptual_transitions`;
- beliefs mají dohledatelnou observation/decision provenance;
- `alua benchmark` umí offline sensory replay + behavior acceptance.

Existující DB se nemaže; před první migrací do v4 se automaticky vytvoří backup.

Autoritativní dokument: `docs/ADAPTIVE_COGNITION_V3.md`.


## Cognitive Architecture V2 – 2026-10-07

Po porovnání s Voyager, Odyssey, luanti-voyager, Mineflayer Pathfinder, Baritone, Craftium, MineStudio, OpenHA a Mindcraft byla nad funkční V1 přidána hierarchická vrstva bez bourání embodied kontraktu.

Nově existuje:
- egocentrický `EgocentricWorldModel`;
- cost-based `LocalNavigator`;
- `BehaviorCritic` pro loop/stagnation detection;
- data-only `SkillGraph` s composite behavior skills;
- `BoundedPlanner`;
- `ExecutiveController` pro plan lifecycle a replanning;
- uncertainty-driven information scan;
- learned-skill gating proti čerstvému perceptu;
- `Store.session_trace()` a `alua evaluate` pro behaviorální benchmark.

Session-local V2 stav se při změně World session resetuje. Episodes, beliefs a learned skills se zachovávají.

Autoritativní dokumenty:
- `docs/COGNITIVE_ARCHITECTURE_V2.md`;
- `docs/OPEN_SOURCE_REFERENCE_AUDIT_2026-10-07.md`.


## Co projekt je

Alua je samostatný mozek autonomního agenta pro AluaWorld.

## Audit chování po prvním E2E běhu – 2026-10-07

Dlouhá série `look` v živém logu byla potvrzena jako chyba rozhodovací vrstvy, nikoli jako smysluplná emergentní strategie. `scan_recovery` a `scan_obstacle` mohly trvale vyhladovět exploration. Oprava vyžaduje mezi dvěma scany skutečný exploration pokus a recovery se už neopírá pouze o historické failures.

Současně:
- vizuální percept přežije expiraci `target_ref`;
- scan actions nejsou reusable skills;
- touch skill nepersistuje konkrétní ruku;
- reusable explore skill neobchází aktuální obstacle check;
- context-specific strafe se nezobecňuje bez precondition modelu;
- distance 0.0 je korektně nejbližší.

Autoritativní audit: `docs/AUDIT_BRAIN_2026-10-07.md`.

## Nejnovější ověřený stav

2026-10-07 proběhl první skutečně úspěšný mobilní E2E běh všech tří repozitářů. `alua:1` přijímala observations, autonomně vykonávala fyzické akce a z budoucích motorických vjemů vznikaly beliefs a skills.

Ověřený snapshot:

- `last_observation_sequence = 474`;
- `episodes = 482`;
- `known_appearance_signatures = 13`;
- `decisions = 235`;
- `beliefs = 9`;
- `pending_expectations = 1`;
- `goals = 10`;
- `skills = 12`;
- `reusable_skills = 6`;
- `schema_version = 3`.

Původní hlavní blocker byl ve World body adapteru, nikoli v AI. Druhý blocker byl recoverable `target_expired` závod. Oba jsou opravené. Úplný runbook je v `docs/E2E_RUNTIME_2026-10-07.md`.


Tři repozitáře:
- AluaWorld = fyzický svět, tělo, smysly, fyzika a následky;
- AluaBridge = bezpečný most a transport;
- Alua = kognice, paměť, beliefs, rozhodování a učení.

## Aktuální architektura

Původní Lua companion je historický prototyp.

Aktuální mozek:
- není Luanti mod;
- neběží uvnitř World procesu;
- je samostatná Python aplikace;
- používá pouze AluaBridge Agent API.

## Stav Alua

Existuje:
- Python runtime;
- BridgeClient;
- strict schema/perception boundary;
- SQLite schema v3;
- automatický backup při migraci v1/v2 -> v3;
- episodes, appearance_stats, decisions, expectations, beliefs a session_events;
- WorkingMemory max 32 frame;
- session recovery;
- motor outcome attribution;
- evidence-based confidence;
- aktivní ExplorationPolicy;
- testy a CI;
- E2E Termux smoke helper.

## Embodied V1

Cyklus:
1. observation;
2. WorkingMemory;
3. přiřazení motorického source_sequence k dřívější akci;
4. belief update až z budoucího smyslového následku;
5. další bezpečná akce pouze bez pending expectation.

Policy:
- damage -> ústup;
- nový blízký cíl -> touch;
- blízká překážka -> look;
- periodický scan;
- jinak pomalý move.

Automatický pickup/push/break je vypnutý.

## target_ref

target_ref:
- je krátkodobý opaque handle;
- existuje pouze v aktuálním RAM PerceptionFrame a odchozím ActionRequest;
- není dlouhodobá identita;
- Store jej odstraňuje z epizod, decisions i expectations.

## Outcome

Bridge ACK není fyzický výsledek.

World action_result je sanitizován do motorického sensory eventu se source_sequence, success_signal, feedback_signal, effort_signal a age_fraction. Teprve tento budoucí vjem může změnit belief.

## Stav Worldu a Bridge

AluaWorld:
- má persistentní LuaEntity tělo alua:1;
- tělo má kolizi, gravitaci, move/look kontrakt, omezenou sílu a motor feedback;
- fyzická manipulace ověřuje skutečný dosah těla.

AluaBridge:
- má World/Agent API;
- body-aware aw_bridge adaptér;
- session vzniká jen pro skutečně aktivní tělo;
- má instalační helper pro synchronizaci adaptéru do AluaWorld.

## E2E smoke

Po spuštění Worldu a Bridge:

    bash tools/e2e_smoke_termux.sh

Úspěch vyžaduje session, observation epizodu, decision a learned belief.

## Bezprostřední další práce

1. audit skutečného rozhodování za běhu – zejména dlouhé série `look`;
2. vypsat a analyzovat current goals, beliefs a reusable skills;
3. ověřit, zda reusable skills skutečně mění budoucí volbu akcí;
4. restart/recovery a delší soak test všech tří procesů;
5. metabolismus/needs ve Worldu;
6. goal/utility a risk learning v Alua;
7. multi-step planner;
8. až potom destruktivnější autonomní manipulace.

## Oprava CI 2026-10-06

Aktivní ověřování nejistých zkušeností mělo konflikt priorit: `scan_obstacle` přebíjel `inspect_object`. Priorita ověřovacího cíle byla opravena tak, aby první dva kontrolní pokusy proběhly a po třetím se cíl dál nenabízel. Tato oprava nemění Bridge ani World kontrakt.

## Vlastní tělo a efektory – 2026-10-06

- World observation má bezpečný `body_schema` pro hlavu, trup, dvě ruce a dvě chodidla;
- Alua smí znát vlastní anatomii, ale ne význam externích objektů;
- ExplorationPolicy při `touch` vybírá volnou `hand_right`, případně `hand_left`;
- volba je v `parameters.effector` a v decision rationale;
- Bridge efektor pouze přenáší, World ověřuje jeho existenci, obsazenost, sílu a dosah;
- ACK stále není fyzický výsledek;
- autonomní pickup/push/break zůstává vypnutý;
- chybějící tělo `alua:1` nově vytvoří první tester automaticky, ale samostatný Python proces Alua se musí stále spustit zvlášť;
- panel Worldu rozlišuje tělo, Bridge session a nedávnou skutečnou aktivitu tohoto procesu.
