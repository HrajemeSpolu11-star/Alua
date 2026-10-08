# Přehled změn

## 2026-10-08 – živá akceptace transportu, navigační benchmark a oprava hledání potřeb (PR #15)

- Na Android Termux potvrzen skutečný World→Bridge přenos po Bridge PR #10/#11: World byl připojen, Bridge přijímal `POST /v1/world/observations` s HTTP 202 a `alua doctor` ukazoval `last_observation_sequence=900`. Následný běh mozku prokazatelně vytvořil vlastní rozhodnutí a fyzické motorické výsledky.
- Z původního `alua benchmark --limit 500`: 226 rozhodnutí (224× move, 1× interact, 1× manipulate), 175 cílů hledání vody, 225 vyhodnocených motorických výsledků, 86 úspěchů / 139 neúspěchů (38,22 %), 138 low-progress pohybů a 59,6 % vizuálních vjemů se zablokovaným směrem vpřed. Akceptace `passed=false` kvůli stereotypii a stagnaci. Jde o **výchozí živé měření**, ne výsledek opravy.
- Identifikováno obcházení naučené navigace při `satisfy_thirst/satisfy_hunger` s `phase=search`: původní `_search_move()` trvale zadával jednoduchý krok vpřed.
- PR #15: hledání zdroje bez reálného `target_ref` nyní používá fyzickými vjemy řízený `explore_frontier`, `bypass_obstacle` či `escape_stagnation`; po skutečném nalezení zdroje zůstává interakce přes `satisfy_body_need`. Přidány 3 regresní testy; GitHub CI prošlo. Účinnost v terénu **čeká na opakovaný benchmark**, není prohlášena za potvrzenou.
- Kompletní popis incidentu, důkazů, implementace, výsledků a bezpečné instalace: `docs/INCIDENT_2026-10-08_NEED_SEARCH_STAGNATION.md`. Neodstraňovat žádné SQLite DB ani existující World.

## 2026-10-08 – podrobný lokální Cognitive V5 mind-log

- Přidán operátorský příkaz `python -m alua mind-log --limit 200 --follow --output "$HOME/alua-mind.jsonl"`. Neotevírá žádné nové HTTP API.
- Soukromý append JSONL obsahuje skutečné smyslové epizody, každý uložený cíl/rozhodnutí včetně kognitivního odůvodnění, zvolenou akci, očekávání, pozdější fyzické motor outcomes a aktuální Cognitive V5 model.
- Data se čtou výhradně z existující Alua SQLite DB, nezasahují do AI cílů a netvrdí úspěch při pouhém Bridge ACK.
- Zabezpečena práva vytvořeného souboru 0600, regresní testy a dokumentace.


## 2026-10-08 – kompletní dokumentační audit Cognitive Core V5

- přidán `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md` jako úplný krokový audit od field problému přes návrh, schema v5, všechny nové moduly, runtime integraci, CI regresi, deployment, rollback a Definition of Done;
- synchronizovány README, architektura, ADR, memory model, learning/decision, roadmap, testing, Termux operations, implementační deník a handoff pro nový chat;
- explicitně zdokumentováno, které části V5 jsou session-local a které persistentní;
- zdokumentováno přesné pořadí outcome learningu a goal arbitration;
- zdokumentován CI incident s fragmentací `inspect` goal key a důvod, proč byla opravena implementace místo oslabení testu;
- historické schema v3/v4 provozní instrukce byly označeny jako historické a aktuální deployment směřuje na schema v5;
- live field acceptance zůstává oddělena od CI: green testy samy o sobě nepotvrzují skutečný návrat ze slepé větve.

## 2026-10-07 – Cognitive Core V5

- field test slepé uličky ukázal, že lokální obstacle recovery nestačí: agent potřebuje vlastní route memory a explicitní návrat;
- SQLite schema zvýšeno na v5; přidána generická tabulka `cognitive_records` a automatický pre-v5 backup;
- přidána bounded attention se salience/surprise/uncertainty;
- přidána multisenzorová scene integrace a temporal recurrence model;
- přidána object permanence nad opaque `appearance_id`;
- přidána route memory, dead-end evidence, remembered-route backtracking, relativní odometrie a weak loop closure;
- přidán predictive action model, prediction error a bounded counterfactual deliberation;
- přidán context-sensitive risk model, empirický self-model a interventional causal hypotheses;
- přidána metakognice pro stagnaci, revisit loop, nejistotu a chybu interního modelu;
- přidány regulatory drives: safety, homeostasis, curiosity, frustration a exploration;
- přidána prospective memory, persistentní interruptible missions a aktivní safe experiments;
- přidána memory consolidation, confidence decay starých beliefs a evidence-based concept formation;
- přidán transferable strategy/meta-learning prior;
- přidány social cognition/testimony a peer-behavior hooks; bez explicitních social sensory dat zůstávají inertní;
- decision rationale nově obsahuje vysvětlitelný `cognitive_state`;
- přidán CLI `alua cognition-status`;
- přidány regresní testy pro attention, object permanence, prediction, metacognition, spatial backtracking, cognitive policy a schema v5;
- kompletní kontrakt: `docs/COGNITIVE_CORE_V5.md`.


## 2026-10-07 – oprava one-block navigation stagnation

- terénní test odhalil, že dlouhá série `move` mohla vypadat úspěšně, přestože tělo prakticky neopouštělo jeden malý prostor;
- Alua nově zachovává `progress_signal` a `slip_signal` z World motor feedbacku;
- `motor_success` vyžaduje alespoň 55 % skutečného projected progress a odmítá `partial_effect`;
- LocalNavigator penalizuje manévry podle kvality skutečného progressu, ne pouze binárního outcome;
- BehaviorCritic rozlišuje normální dlouhou chůzi od low-progress stagnace a sleduje repeated maneuver místo samotného action type `move`;
- `escape_stagnation` nyní začíná fyzickou reorientací těla před escape pohybem;
- aktivní escape plan se nezruší okamžitě stejným critic signálem, který jej vytvořil;
- jakýkoli předchozí fyzický `look` blokuje okamžitý další scan;
- offline evaluator reportuje `mean_move_progress`, `low_progress_moves` a `navigation_stagnation_detected`;
- detail: `docs/INCIDENT_2026-10-07_ONE_BLOCK_BOUNCE.md`.


## 2026-10-07 – Adaptive Cognition V3

- SQLite schema zvýšeno na v4; před migrací starší DB se automaticky vytváří backup;
- přidán `AdaptiveUtilityModel` pro evidence-weighted ranking intrinsic goals;
- přidána persistentní `PerceptualTopology` bez absolutních souřadnic a bez World truth;
- ukládají se perceptuální place signatures a transition evidence pro `forward/left/right/back`;
- LocalNavigator používá persistentní maneuver penalties z vlastních předchozích outcomes;
- po úspěšném `look` se invaliduje starý egocentrický directional cache;
- beliefs dostaly samostatnou `belief_evidence` provenance s session/observation/decision vazbou;
- přidán bounded sensory replay z uložených episodes;
- přidán CLI `alua benchmark` s nenulovým exit code při behaviorální regresi;
- summary nově ukazuje počty belief evidence, perceptual places a transitions;
- doplněny unit testy a dokumentace V3.


## 2026-10-07 – Cognitive Architecture V2

- přidán bounded egocentrický world model pouze z vlastních sensory frames;
- přidán cost-based receding-horizon LocalNavigator s failure a repetition penalty;
- přidán BehaviorCritic pro repeated look, action stereotype a repeated move failures;
- přidán data-only SkillGraph s composite behavior skills;
- přidán BoundedPlanner a ExecutiveController s multi-step plan lifecycle;
- learned explore skill se použije pouze pokud neodporuje aktuálnímu local modelu/criticu;
- information scan je v live runtime řízen horizontální uncertainty místo pevného observation modulo patternu;
- přidán bounded `Store.session_trace()` a CLI `alua evaluate`;
- přidány behaviorální metriky pro look-loop, action streak, outcome success a move success;
- session transition resetuje V2 local model, critic, planner a navigation penalties, ale zachovává long-term cognition;
- přidán open-source reference audit a kompletní Cognitive V2 dokumentace;
- přidány unit testy pro world model, navigator, critic, planner, executive, evaluator a trajectory trace.


## 2026-10-07 – globální scan gate po terénním retestu

- reálný retest ukázal, že různé scan cíle mohly stále řetězit `look` za sebou, i když každý jednotlivý scan typ měl vlastní anti-loop bránu;
- `scan_obstacle`, `scan_recovery` a `scan_periodic` nyní sdílejí jednu globální scan gate;
- po libovolném scanu musí následovat jiný přijatý goal/action, než lze znovu zvolit další scan;
- anti-loop stav se odvozuje z posledního Bridge přijatého rozhodnutí v aktuální `session_id`;
- odstraněno porovnávání `goal_stats.last_sequence` mezi sessions, protože observation sequence se při nové World session resetuje;
- přidány regresní testy pro chaining různých scan kindů a izolaci historie podle session.


## 2026-10-07 – audit mozku a odstranění look loopu

- nalezena hlavní příčina dlouhých sérií `look`: `scan_recovery` mohl po historických exploration failures trvale přebíjet další pohyb;
- `scan_recovery` i `scan_obstacle` nyní vyžadují intervenující exploration pokus před dalším scanem;
- staré failures už nevynucují recovery, pokud successes znovu převažují;
- scan direction už není odvozena z parity observation sequence a nevytváří jednoduchý levá/pravá oscilátor;
- zrakový percept přežije expiraci `target_ref`; handle je nyní volitelný motorický capability, nikoli podmínka existence perceptu;
- scan akce se již neučí jako reusable skills;
- reusable touch skill neukládá konkrétní ruku a při použití znovu vybere aktuálně dostupný effector;
- generic explore skill nesmí přebít aktuální blízkou překážku;
- kontextový obstacle-bypass se nepromuje na univerzální explore skill;
- opravena chyba řazení distance `0.0`;
- přidány regresní testy a `docs/AUDIT_BRAIN_2026-10-07.md`.


## 2026-10-07 – Alua přežije expirovaný target_ref

- `409 target_expired` už neukončí celý kognitivní runtime;
- rozhodnutí vytvořené nad stale handle se uloží jako `stale_target`, nevytvoří expectation ani falešný goal attempt a runtime čeká na čerstvý vjem;
- přidán regresní test, že stejný zastaralý handle se po posunu observation cursoru neopakuje.


## Nezveřejněno

### 2026-10-06 – vnímání vlastního těla a volba ruky

- Alua umí číst bezpečný observation kanál `body_schema` bez importu World katalogů;
- ExplorationPolicy vybírá pro `touch` skutečně dostupnou a volnou `hand_right` nebo `hand_left`;
- vybraný efektor se ukládá do vysvětlitelné rationale a odesílá v `parameters.effector`;
- obsazená pravá ruka způsobí výběr levé ruky;
- při starším observation bez body schema zůstává kompatibilní action bez explicitního efektoru;
- úspěch ruky se stále neučí z ACK, ale až z budoucího motorického/tělesného vjemu;
- doplněny policy testy a dokumentace.

### 2026-10-06 – oprava priority ověřování nejistého objektu

- opraven konflikt intrinsic curriculum, kdy `scan_obstacle` přebíjel `inspect_object` u známého objektu s nedostatečnou evidencí;
- první dva ověřovací pokusy mají nyní vyšší informační prioritu než obecný scan překážky;
- po dosažení tří pokusů se `inspect_object` stále přestane nabízet podle původního pravidla `needs_verification`.

### 2026-10-06 – embodied learning V1

- SQLite kognitivní schema zvýšeno na v2;
- před migrací schema v1 se automaticky vytváří lokální SQLite backup;
- přidány expectations, beliefs a bridge_action_sequence;
- změna World session invaliduje staré pending/planned world akce a expectations;
- přidána bounded WorkingMemory s kapacitou 32 frame;
- target_ref vazby existují pouze krátkodobě v RAM;
- motorický sensory channel koreluje World výsledek s Bridge action sequence;
- belief update vzniká až budoucím motorickým vjemem, nikoli HTTP ACK;
- beliefs mají support_count, contradiction_count a confidence;
- ExplorationPolicy používá Worldem definované move/look a pouze nedestruktivní manipulate/touch;
- damage signal vyvolá ústup, blízká překážka rozhlédnutí a volný prostor opatrný pohyb;
- další aktivní akce čeká na vyřešení, invalidaci nebo expiraci předchozí expectation;
- testy pokrývají migraci, backup, session invalidaci, working memory, policy, target_ref sanitizaci a learning;
- přidán tools/e2e_smoke_termux.sh pro skutečný tříprocesový smoke test.

### 2026-10-06 – audit dokumentace a recovery kontrakt

- proveden audit skutečné implementace proti dokumentované architektuře;
- přidán docs/AUDIT_2026-10-06.md;
- přidán docs/IDENTITY_SESSION_RECOVERY.md;
- přesně oddělen agent_id, session_id, observation sequence, decision_id, request_id a target_ref;
- zdokumentovány restarty a transportní failure modes.

### 2026-10-06 – první samostatný Alua AI runtime

- Python 3.12+ package src/alua;
- bezpečná localhost konfigurace;
- AluaBridge Agent API klient;
- schema validation;
- vlastní SQLite persistence;
- target_ref odstraněn z dlouhodobého uložení;
- epizodická evidence a appearance statistiky;
- session transition;
- deterministické client_action_id;
- první bezpečná wait policy;
- CLI doctor/status/run;
- testy, boundary audit a GitHub CI.

### 2026-10-06 – přechod na samostatnou Alua AI

- Alua oddělena od Luanti do samostatného kognitivního procesu;
- jediným runtime rozhraním je AluaBridge Agent API;
- starý Lua companion označen jako historický prototyp;
- založena dokumentace po vzoru AluaWorld.

## 0.2.0 – 2026-09-24

- Luanti companion follow/stay/recall;
- jednoduchá paměť;
- diagnostický scan;
- modulární Lua základ.

## 0.1.0 – 2026-09-24

- první kostra Luanti modu;
- diagnostický příkaz;
- ContentDB metadata a MIT licence.
