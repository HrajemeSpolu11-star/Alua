# Audit mozku Alua – 2026-10-07

Tento audit vznikl po prvním skutečně úspěšném embodied E2E běhu, ve kterém se `alua:1` začala autonomně pohybovat, ale živý log ukázal dlouhé série akcí `look`.

Rozsah auditu:
- perception;
- working memory;
- intrinsic goals;
- reflex goals;
- ExplorationPolicy;
- expectations a motor outcome attribution;
- beliefs;
- procedural skills a jejich reuse;
- vazba rozhodnutí na aktuální percept.

Audit se záměrně netýká fyziky AluaWorld ani transportních internals AluaBridge.

## Výsledek

Zjištěná dlouhá série `look` nebyla emergentní inteligentní strategie. Byla způsobena několika deterministickými chybami v kognitivní vrstvě.

## A-01 P0 – recovery scan mohl trvale vyhladovět exploration

### Původní logika

Jakmile měl `explore:open` alespoň dva failures, vznikal vždy kandidát:

```text
scan:recovery priority ~= 0.84
```

Běžný exploration měl přibližně:

```text
explore:open priority ~= 0.50
```

Úspěšný `look` přidal recovery scanu success, ale success jeho prioritu nesnižoval. Po jednou dosažené podmínce tak mohl `scan_recovery` vítězit donekonečna.

### Důsledek

Agent:
1. měl několik neúspěšných pohybů;
2. vybral recovery scan;
3. úspěšně otočil hlavu;
4. další frame znovu vybral recovery scan;
5. opakoval `look` bez následného pokusu změnit situaci.

To odpovídá pozorovanému živému logu s dlouhou sérií po sobě jdoucích `look` akcí.

### Oprava

Recovery scan je nyní jednorázová reakce na novější exploration pokus:

- porovnává `last_sequence` exploration a posledního recovery scanu;
- po jednom recovery scanu musí přijít další motorický pokus;
- nový recovery scan je povolen až po novějším exploration pokusu;
- staré historické failures už nestačí: recovery se aktivuje pouze pokud failures stále převažují nad successes.

Tím se recovery mění z dominantního trvalého cíle na skutečný mezikrok.

## A-02 P0 – obstacle scan měl stejný starvation vzor

`scan_obstacle` měl vyšší prioritu než exploration a při stále viditelné překážce mohl být zvolen v každém cyklu.

Oprava používá stejnou bránu:

```text
scan -> musí následovat exploration/motorický pokus -> teprve potom lze znovu scan
```

Pokud je centrální směr stále blokovaný, následný exploration už nejde slepě rovně, ale použije opatrný boční bypass.

## A-03 P1 – směr look byl odvozen z parity observation sequence

Původní policy:

```python
direction = 1 if frame.sequence % 2 == 0 else -1
```

Při pravidelném toku observations mohl agent vytvořit přesný oscilátor:

```text
+0.45 rad
-0.45 rad
+0.45 rad
-0.45 rad
...
```

Agent se tak mohl opakovaně vracet ke stejné orientaci místo systematického průzkumu.

### Oprava

Směr scanu je odvozen od čísla skutečného scan pokusu, nikoli od globální observation sequence. Dva pokusy drží stejný směr a až potom se strana mění. Tím se zabrání jednoduchému levá/pravá oscilátoru.

## A-04 P1 – po expiraci target_ref Alua zahodila i samotný zrakový vjem

Bridge správně od 2026-10-07 odstraňuje expirovaný `target_ref`, ale zachovává:
- appearance;
- distance;
- blocks_motion;
- liquid.

Původní `PerceptionFrame._targets()` však celý ray zahodil, pokud neměl `target_ref`.

To znamenalo, že oprava stale targetu mohla vytvořit novou navigační slepotu: objekt byl stále viditelný, ale cognition ho přestala považovat za target percept.

### Oprava

`TargetPercept.target_ref` je nyní `str | None`.

Zrakový percept přežije expiraci motorického handle. Alua může stále:
- vidět překážku;
- odhadovat distance;
- používat appearance signature;
- navigovat kolem ní.

Pouze `inspect_object/touch` vyžaduje platný aktuální `target_ref`.

## A-05 P1 – reusable scan skill mohl zamknout stále stejný look

Původně se i `scan_obstacle`, `scan_recovery` a `scan_periodic` učily jako reusable skills.

Po třech úspěšných motorických otočeních mohl vzniknout skill typu:

```text
look yaw_delta_rad=+0.45
```

Při dalších scan cílech se pak místo aktuální policy znovu používal přesně tento motorický template.

To zesilovalo stereotypní otáčení.

### Oprava

Informační scan akce se nyní:
- nepromují do reusable skills;
- staré scan skills se runtime retrieval cestou ignorují.

Procedurální reuse V1 zůstává pouze pro:
- bezpečný generic exploration move;
- target-specific `inspect_object/touch`.

## A-06 P1 – touch skill ukládal konkrétní ruku jako přenositelnou dovednost

Původní skill mohl obsahovat:

```json
{"verb":"touch","effector":"hand_right"}
```

Pokud se pravá ruka později zaplnila, reusable skill stále žádal `hand_right`, i když aktuální body_schema správně nabízelo levou.

### Oprava

`effector` už není součástí persistentního skill template.

Při každém použití touch skillu se ruka znovu vybere z aktuálního `body_schema`:
- pravá, pokud je přítomná, touch-capable a volná;
- jinak levá;
- jinak bez explicitního efektoru a konečnou validaci provede World.

Dovednost tedy uchovává „dotkni se tohoto typu perceptu“, nikoli „vždy použij pravou ruku“.

## A-07 P1 – generic explore skill mohl přebít aktuální překážku

Reusable explore skill byl context-free. Naučený `forward=1` se mohl použít i ve frame, kde aktuální centrální zrak hlásil blízkou blokující překážku.

### Oprava

Pokud aktuální frame hlásí blízkou centrální překážku:
- generic reusable explore skill se nepoužije;
- řízení se vrátí aktuální policy;
- policy provede opatrný boční bypass.

## A-08 P2 – obstacle-bypass se mohl omylem naučit jako univerzální explore skill

Boční úhyb je kontextová reakce na překážku. Bez modelu preconditions se nesmí zobecnit na „takto se vždy exploruje“.

### Oprava

Do generic `explore` skill library se nyní přijímá pouze dostatečně dopředný, téměř bez-strafe pohyb.

Kontextový bypass se vykoná a vyhodnotí, ale není uložen jako univerzální dovednost.

## A-09 P2 – distance 0.0 nebyla při hledání nejbližšího cíle skutečně nejbližší

Původní sort používal:

```python
item.distance_fraction or 1.0
```

Platná hodnota `0.0` je v Pythonu falsy a proto byla nahrazena `1.0`.

Objekt v bezprostředním kontaktu tak mohl být řazen jako nejvzdálenější.

### Oprava

Používá se explicitní kontrola `is not None`.

## Bezpečnostní invarianty po opravě

1. scan nesmí bez intervenujícího motorického pokusu sám sebe trvale znovu volit;
2. expirovaný target_ref nesmí odstranit bezpečný vizuální percept;
3. touch bez platného target_ref se nikdy neprovádí;
4. reusable skill nesmí přebít aktuální blízkou překážku;
5. reusable touch skill nesmí fixovat starý tělesný efektor;
6. context-specific obstacle bypass nesmí být bez precondition modelu zobecněn jako generic skill;
7. World outcome se stále učí pouze z budoucí observation, nikdy z HTTP ACK.

## Regresní testy

Přidány testy pro:
- visual percept bez target_ref;
- obstacle scan -> povinný intervenující exploration;
- recovery scan -> povinný intervenující exploration;
- historické failures po převaze successes už neaktivují permanentní recovery;
- distance 0.0 jako skutečně nejbližší cíl;
- scan direction nezávislou na parity observation sequence;
- obstacle bypass;
- scan akce se nestávají reusable skills;
- touch skill znovu váže aktuálně volnou ruku;
- generic explore skill se nepoužije proti aktuální překážce;
- obstacle bypass se neukládá jako generic explore skill.

## Co audit vědomě ještě neřeší

Nejde o chyby aktuálního V1, ale o další fáze:
- více-krokový planner;
- explicitní utility/risk model;
- needs/metabolismus;
- evidence links beliefs -> konkrétní episodes;
- confidence decay;
- kontextové preconditions pro obecné procedurální skills;
- dlouhodobá komprese episodic memory;
- sociální a jazyková vrstva.

Další acceptance test má sledovat, že po aktualizaci už v běžném prostředí nevzniká neomezená série `look` bez intervenujících pohybových pokusů.

## Dodatek – terénní retest po první opravě

První oprava odstranila hlavní starvation chybu, ale živý retest ukázal další sérii několika `look` akcí za sebou.

Příčina byla dvojí:

1. anti-loop brána byla per-goal, takže různé scan cíle se mohly řetězit:
   `scan_obstacle -> scan_recovery -> scan_periodic`;
2. brána porovnávala `goal_stats.last_sequence`, ale observation sequence je monotónní pouze uvnitř jedné World session a po nové session se resetuje.

Finální invariant je proto globální a session-scoped:

```text
poslední přijatý goal v aktuální session je scan
=> žádný další scan goal není kandidát
=> musí přijít jiná fyzická/behaviorální akce
=> teprve potom se scan gate znovu otevře
```

Zdroj posledního goalu je tabulka `decisions` filtrovaná na aktuální `session_id` a pouze řádky s přiděleným `bridge_action_sequence`, tedy akce skutečně přijaté Bridge.

Tím se anti-loop logika už neopírá o sequence hodnoty z jiné session a zároveň blokuje chaining mezi různými druhy scanů.

## Dodatek – one-block bounce po Cognitive V2/V3

Další field test ukázal opačný problém než původní look-loop: Alua téměř výhradně posílala `move`, World je potvrzoval jako úspěšné, ale fyzicky se pouze odrážela v malém prostoru.

Audit odhalil kombinaci chyby sensory/motor contractu a kognitivní recovery:
- World hodnotil displacement příliš benevolentně a bez projekce na intended direction;
- vision left/right basis byl proti body locomotion basis zrcadlený;
- critic používal action type streak místo skutečné move quality;
- escape plan neuměl změnit yaw;
- aktivní escape plan mohl být opakovaně přepsán stejným force-replan signálem.

Kognitivní oprava nyní používá graded progress, maneuver-specific stagnation a explicitní `reorient_escape`.

World-side oprava je samostatně dokumentována v AluaWorld `docs/INCIDENT_2026-10-07_NAVIGATION_STAGNATION.md`.

Kompletní AI-side detail: `docs/INCIDENT_2026-10-07_ONE_BLOCK_BOUNCE.md`.
