# Architektonická rozhodnutí Alua AI

## ADR-A001 – Alua je samostatný kognitivní proces
Přijato 2026-10-06. Alua neběží jako Luanti mod.

## ADR-A002 – Jediné runtime rozhraní je AluaBridge Agent API
Přijato 2026-10-06. Přímý World/Luanti přístup je zakázán.

## ADR-A003 – Python pro nový runtime
Přijato 2026-10-06. V1 používá Python 3.12+.

## ADR-A004 – SQLite vlastní kognitivní paměť
Přijato 2026-10-06. Bridge SQLite není paměť Alua.

## ADR-A005 – Jeden agent na jeden proces ve V1
Přijato 2026-10-06. Každá Alua má vlastní proces, token a DB.

## ADR-A006 – Žádný povinný LLM
Přijato 2026-10-06. Základní autonomie musí fungovat bez cloud LLM.

## ADR-A007 – Beliefs jsou evidence-based a opravitelné
Přijato 2026-10-06. Empirická znalost není absolutní fakt bez evidence.

## ADR-A008 – target_ref není dlouhodobá identita
Přijato 2026-10-06. target_ref patří pouze do krátkodobého kontextu.

## ADR-A009 – ACK není outcome
Přijato 2026-10-06. Transportní přijetí akce nesmí přímo změnit world belief.

## ADR-A010 – Starý Lua companion se zatím zachovává
Přijato 2026-10-06. Historický prototyp zůstává, nový runtime na něm nezávisí.

## ADR-A011 – agent_id je dlouhodobá identita Alua
Přijato 2026-10-06. Restart procesu, Bridge ani Worldu sám nevytváří novou osobnost.

## ADR-A012 – změna session invaliduje ephemeral stav
Přijato 2026-10-06. Nový session_id resetuje krátkodobý World kontext, ne dlouhodobé epizody a beliefs.

## ADR-A013 – aktivní explorace začíná nedestruktivně
Přijato 2026-10-06.

Po definici autoritativního move/look kontraktu smí Alua autonomně použít move a look. Manipulace V1 používá pouze touch. Pickup, push a break čekají na naučený risk/utility model.

## ADR-A014 – outcome se koreluje Bridge action sequence
Přijato 2026-10-06.

Decision ukládá Bridge action_sequence. World ji vrací pouze jako omezený motorický source_sequence. Belief update vzniká až po budoucí observation, ne z HTTP ACK.

## ADR-A015 – kognitivní SQLite schema v2 migruje se zálohou
Přijato 2026-10-06.

Před upgrade schema v1 se vytvoří SQLite backup. Session transition invaliduje nedokončené World-specific decisions a expectations, ale nemaže epizody ani beliefs.

## ADR-A016 – Znalost vlastních částí těla není World truth cheat

Přijato 2026-10-06.

Alua může z `body_schema` znát vlastní hlavu, trup, ruce a chodidla a vybírat dostupný efektor. Nesmí z toho odvozovat význam externích objektů. Ruku vybírá kognice, fyzickou platnost a následek vždy ověřuje World, Bridge pouze přenáší parametr.

## Historická rozhodnutí

Původní ADR z 2026-09-24 jsou zachována v Git historii. Jejich předpoklad, že Alua běží uvnitř Luanti, je nahrazen ADR-A001 a ADR-A002.

## ADR-A017 – Hierarchická kognice nad primitivními akcemi

Přijato 2026-10-07.

High-level goal se už nemá přímo rovnat jedné motorické primitivě. Alua používá data-only SkillGraph, bounded planner a executive controller. World primitive action zůstává nejnižší výstupní vrstvou.

Důvod: dlouhé série `look` ukázaly, že řízení pouze na úrovni jednotlivých primitiv vede k lokálním oscilacím a ad-hoc opravám.

## ADR-A018 – Navigace je lokální a epistemicky omezená

Přijato 2026-10-07.

Alua používá cost-based receding-horizon navigaci inspirovanou pathfindery, ale nesmí číst globální mapu. Lokální world model vzniká pouze ze smyslů a je session-local.

## ADR-A019 – Self-critic nesmí vytvářet world truth

Přijato 2026-10-07.

BehaviorCritic smí vyhodnotit pouze vlastní action/outcome historii. Může vyžádat replan, ale nesmí sám vytvářet empirické beliefs o externím světě.

## ADR-A020 – Open-source reference se přebírá jako architektonický princip

Přijato 2026-10-07.

Voyager, Odyssey, luanti-voyager, Mineflayer Pathfinder, Baritone, Craftium, MineStudio, OpenHA a Mindcraft byly použity jako referenční architektury. Minecraft-specific knowledge, privileged map state, generated executable code a cizí world truth se nepřenášejí.

Baritone kód se kvůli LGPL-3.0 do MIT jádra Alua nekopíruje. Používá se pouze obecná algoritmická inspirace.

## ADR-A021 – Perceptuální topologie místo privilegované mapy

Přijato 2026-10-07.

Alua smí dlouhodobě ukládat pouze perceptuální place signatures a empirické přechody po vlastních motorických akcích. Signature není považována za unikátní fyzickou lokaci a nesmí obsahovat absolutní World pozici ani technické identity.

## ADR-A022 – Goal utility je evidence-weighted, nikoli sémanticky předprogramovaná

Přijato 2026-10-07.

Intrinsic goal ranking kombinuje base prioritu s vlastní success/failure evidencí, informační nejistotou, novelty a tělesným damage. Utility model nesmí obsahovat skryté významy objektů.

## ADR-A023 – Každý nový belief má dohledatelnou evidence stopu

Přijato 2026-10-07.

Schema v4 ukládá `belief_evidence` s session, observation sequence, decision ID a support/contradiction signálem. Belief bez možnosti dohledat původ není cílový stav projektu.

## ADR-A024 – Behavioral quality musí být měřitelná offline

Přijato 2026-10-07.

Persistované episodes a decision/outcome trace musí jít vyhodnotit bez běžícího Worldu. `alua benchmark` slouží jako acceptance gate proti regresím typu look-loop a action stereotype.


## ADR-A025 – Prostorová paměť smí používat relativní odometrii, ne World XYZ

Přijato 2026-10-07.

Alua smí z vlastních ověřených motorických outcomes integrovat interní relativní pose `x/z/heading` s explicitní uncertainty. Tento pose není fyzická World souřadnice a nesmí být inicializován ani opravován privilegovanou pozicí z AluaWorld.

Opětovné rozpoznání perceptuálního místa smí fungovat jako weak loop closure a snížit uncertainty.

## ADR-A026 – Slepá ulička se řeší návratovou pamětí před náhodným escape

Přijato 2026-10-07.

Úspěšné přechody vytvářejí bounded route stack. Pokud lokální sensory evidence, failed progress a revisit evidence ukazují dead end, executive dostane `spatial_backtrack` goal a pokusí se vrátit přes inverse maneuver k předchozímu zapamatovanému place.

Random/lateral escape zůstává fallback, nikoli první strategie při známé návratové cestě.

## ADR-A027 – Predikce, risk a kauzalita jsou opravitelné modely

Přijato 2026-10-07.

`PredictiveModel`, `RiskModel` a `CausalLearner` ukládají pouze evidence-weighted hypotézy odvozené z vlastních actions a pozdějších outcomes.

Prediction, causal hypothesis ani strategy prior nejsou World truth. Čerstvá sensory evidence má přednost.

## ADR-A028 – Model-based deliberation je bounded a receding-horizon

Přijato 2026-10-07.

Při stagnaci může Alua porovnat několik fyzických alternativ podle expected progress, expected success, risk, uncertainty a weak strategy transfer prioru. Vybere se nejvýše jeden bounded krok; po něm se znovu vnímá a replánuje.

V hlavní motorické smyčce není povolen generovaný executable code ani neomezené search tree.

## ADR-A029 – SQLite schema v5 používá namespaced cognitive records

Přijato 2026-10-07.

Vyšší kognitivní modely používají tabulku `cognitive_records` s:
- record key/kind;
- sanitized JSON payload;
- confidence;
- support/contradiction;
- first/last sequence.

Před migrací starší DB se vytvoří backup. `target_ref` se i z tohoto payloadu sanitizuje.

## ADR-A030 – Metakognice monitoruje cognition, nevytváří externí fakta

Přijato 2026-10-07.

Metakognice smí diagnostikovat stagnaci, loop, prediction error, nejistotu a vyžádat změnu strategie. Nesmí prohlásit, co externí objekt „je“.

## ADR-A031 – Konsolidace používá kompresi a confidence decay, ne tiché mazání znalostí

Přijato 2026-10-07.

Periodická konsolidace může vytvářet episodic summaries, abstrahovat concepts a posouvat confidence dlouho neověřených beliefs směrem k nejistotě. Empirická evidence se nesmí svévolně přepsat administrativní pravdou.

## ADR-A032 – Cizí tvrzení není vlastní belief

Přijato 2026-10-07.

Budoucí social testimony se ukládá odděleně se source identity/trust/confidence. Teprve vlastní evidence může tvrzení převést do běžného empirical belief.

## ADR-A033 – Dlouhodobé missions jsou přerušitelné tělesnými potřebami

Přijato 2026-10-07.

Mission je perzistentní záměr vyšší úrovně, nikoli fixní motorická sekvence. Safety a homeostasis ji mohou suspendovat. Po každém motorickém kroku zůstává povinný fresh-perception replan.



## ADR-A034 – Aktivní experiment nesmí fragmentovat goal evidence

Přijato 2026-10-08.

ExperimentPlanner může změnit důvod, proč byl zvolen `inspect_object`, ale nesmí pro stejný fyzický záměr vytvářet paralelní goal namespace. Touch experiment proto používá kanonický key `inspect:<appearance>`.

Důvod: goal success/failure evidence, skill learning a regression testy musí zůstat spojeny s jedním významem cíle. Tento invariant byl potvrzen CI regresí během PR #10.

## ADR-A035 – Scene signature není fyzická lokace

Přijato 2026-10-08.

`SceneIntegrator` smí sloučit více sensory modalit do interní scene signature. Scene signature je kontext pro pozornost, temporal recurrence a learning; nesmí být interpretována jako absolutní pozice ani jako unikátní objekt Worldu.

## ADR-A036 – Strategy transfer je slabší prior než context-specific evidence

Přijato 2026-10-08.

`StrategyLearner` může přenášet zkušenost mezi podobnými goal/action patterns, ale jeho score je pouze bounded bonus. Čerstvá sensory evidence, risk, context-specific prediction a safety/homeostasis mají vyšší autoritu.

## ADR-A037 – Social cognition je inertní bez explicitního sensory kontraktu

Přijato 2026-10-08.

Alua nesmí z běžného visual appearance sama usoudit, že jde o jiného agenta. Social trust, testimony a peer behavior model se smějí aktivovat pouze z explicitního social sensory kanálu vlastněného Worldem.

Kompletní implementační stopa V5: `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.
