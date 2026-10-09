# 2026-10-09 – Jeden voxelový stupínek je překonatelný terén, ne slepá ulička

## Požadavek a důvod

Uživatel výslovně žádá: "hlavně aby jednu kostku nebral jako
překážku". Alua žije ve voxelovém Luanti světě a stále dostává
jednoblokové fyzické bariéry. Nesmí ale zaměňovat *neprůchodnost běžné
chůze* s *neprůchodností trasy*, pokud má tělo reálnou schopnost
překonat jednu kostku fyzickým výskokem (`vault`).

Původní chyba: `vision.rays[].blocks_motion=true` správně signalizoval
kolizi se stěnou i s **jednou** krychlí. `EgocentricWorldModel`
na základě této informace nastavil `front_is_blocked=true` a výrazně
penalizoval přední sektor. `SpatialMemory._dead_end_from_model`
přímo četla raw `blocked_probability`, takže ignorovala paralelní
skutečný tělesný vjem `locomotion.step_up_signal=1`.
Proto i po opravě motorického `vault` mohl systém stupínek vnímat
jako slepou uličku a upřednostňovat obcházení či návrat.

## Nový kontrakt mezi tělem, navigací a mozkem

- Fyzikální kolize zůstává pravdivá: `vision.blocks_motion` je stále
  true. **Nikam neteleportujeme ani neprocházíme zdí.**
- Přední stupeň je **traversable / vaultable** pouze ve stejné aktuální
  vlastní smyslové observation, když tělo hlásí:
  `locomotion.grounded_signal >= 0.5`,
  `locomotion.step_up_signal >= 0.5`,
  `locomotion.front_head_blocked_signal < 0.5`,
  `locomotion.overhead_blocked_signal < 0.5`,
  a `vitals.stamina_fraction >= 0.14` (skutečný min. limit
  AluaWorld `vault`). Všechny klíče musejí existovat a mít číselnou
  hodnotu. Starý vjem, chybějící kanál, nízká stamina nebo strop
  **nedovolí** chybně označit zeď jako překonatelnou.
- `EgocentricWorldModel.front_is_blocked()` je v tomto případě false;
  `sector_score(front)` dává stupínku rozumnou dostupnost namísto
  obrovské penalizace od jedné kolizní vision-ray.
- `SpatialMemory._dead_end_from_model()` neoznačí úsek za slepou
  uličku, pokud je vpředu čerstvě doložený překonatelný stupeň.
- `ExecutiveController.choose()` používá **stejnou metodu**
  `front_step_traversable()` a pro relevantní hledání/průzkum
  vybere existující fyzickou akci `embodied_vault`. Samotné
  `ExplorationPolicy.terrain_intent()` také vyžaduje body podporu,
  headroom a stamina, jinak nesmí poslat nerealizovatelný `vault`.
- Když `vault` fyzicky neuspěje, zpětnou vazbu smí hodnotit
  kritik a navigátor; naopak **představa**, že stupeň je
  překonatelný, nesmí být započítána jako již fyzicky vykonaná akce.
- Vyšší stěna, strop, únava a skutečné nepřekonatelné prostředí
  zůstávají legitimními překážkami. Změna neřeší automaticky
  všechny příčiny zacyklení a netvrdí, že se Alua stala chytřejší
  pouze díky klasifikaci.

## Repozitáře a rozsah

Mění se pouze `Alua` Python (`src/alua/world_model.py`,
`src/alua/spatial_memory.py`, `src/alua/executive.py`,
`src/alua/policy.py`). AluaWorld již fyzicky vytváří
`locomotion.step_up_signal` a provádí `vault` s kolizemi,
Bridge již přenáší `locomotion` a `vitals` přes striktní V5
allowlist. **Žádná změna AluaWorld/Bridge protokolu, databází, mapy,
World pravdy ani JSON schema.** Žádné předané tajné pozice.

## Regresní testy a akceptace

`tests/test_world_model.py`: plná kostka je raw vizuálně blokující,
ale s čerstvým smyslovým potvrzením fyzicky překonatelného stupně
`front_is_blocked=false`; nereportovat dead end. Pro vysokou zeď,
nízký strop, neuzemněné tělo, nedostatečnou energii, chybějící
locomotion a po otočení zůstane blokace aktivní.

`tests/test_executive.py`: hledání vody s reálným stupněm dává
`explore_frontier + embodied_vault` namísto `bypass_obstacle`
a běžného kroku. `tests/test_policy.py`: vault jen při
dostatečné fyzické připravenosti.

CI: `bash tools/run_tests.sh`. GitHub CI passing není důkaz, že
skutečný Luanti 1m blok agent na telefonu dokončil. Live akceptace:
spustit AluaWorld + Bridge + jediný Alua mozek, ověřit mind-log
`plan_skill`, `mode=vault`, **World motor outcome** s kladným
`vertical_progress_signal` a skutečné postavení na další krychli
(i když benchmark vykazuje úspěšný horizontální pohyb).
Využít běžnou uloženou mapu nebo izolovanou testovací scénu,
nikdy nemažeme existující svět nebo Alua SQLite.

## Další známá rizika

World `locomotion.probe` vzorkuje terén hlavně ve směru natočení
těla a omezeným počtem punktů; boční pohyb a diagonální hrany
mohou být chybně vyhodnoceny. `vault` motorický feedback navíc
nemusí správně odlišovat dokončené překonání výšky od krátkého
výskoku proti stěně. Budoucí pohybový kontroler by měl vzorkovat
skutečný zamýšlený směr, ověřovat dosednutí a dlouhodobý vertikální
pokrok a měřit zacyklení přes měřitelný průchod mezi buňkami.

**Status: změna kódu a testů, reálná akceptace dosud NEPOTVRZENA.**
