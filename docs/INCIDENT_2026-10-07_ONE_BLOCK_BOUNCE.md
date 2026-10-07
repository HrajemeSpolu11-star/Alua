# Incident 2026-10-07 – Alua se pohybovala, ale prakticky neopouštěla jednu kostku

## Pozorování z terénu

Po nasazení Cognitive V2 / Adaptive V3 už nebyl hlavním problémem `look` loop. Živý log ukázal dlouhé série `move`:

```text
seq=30 move success
dráha ~0.25 m
seq=31 move success
dráha ~0.33 m
...
```

Vizuálně se ale tělo pouze odráželo / přeposouvalo kolem stejného malého prostoru.

To znamenalo, že vyšší kognice dostávala chybný signál „postup funguje“.

## Root causes

### 1. World poskytoval příliš optimistický motorický success

World původně považoval za úspěch prakticky jakýkoli horizontální displacement nad velmi nízkým prahem. Neověřoval, zda displacement nastal skutečně v požadovaném směru.

Oprava je v AluaWorld:
- projected directional progress;
- progress ratio;
- slip ratio;
- `partial_effect`;
- přísnější success threshold.

Alua nově čte `progress_signal` a motorický success vyžaduje skutečný kvalitní postup.

### 2. World boční vision ray byl zrcadlený proti locomotion frame

AI world model interpretoval ray 1 jako left a ray 2 jako right. World ale horizontální ray basis používal s opačným znaménkem než locomotion basis.

Mozek tedy mohl bezpečně naplánovat pohyb na stranu, kterou ve skutečnosti neviděl jako volnou.

Oprava je v AluaWorld a zachovává současné pořadí rayů.

### 3. Critic nerozlišoval „move pořád dobře“ a „move pořád bez pokroku“

V2 critic používal action type streak. Dlouhá rovná chůze i neúspěšné poskakování tedy vypadaly podobně.

Nyní critic používá:
- graded move progress;
- repeated maneuver;
- recent average quality.

Úspěšná dlouhá cesta není chyba. Opakovaný manévr s malým progressem je stagnace.

### 4. Escape plan neměnil orientaci těla

Původní `escape_stagnation` obsahoval pouze:

```text
navigate_escape
navigate_frontier
```

Pokud lokální pohyb nestačil, tělo nikdy nezměnilo yaw a mohlo pouze přepínat forward/strafe/back kolem stejné překážky.

Nyní:

```text
reorient_escape
navigate_escape
navigate_frontier
```

První krok je skutečný `look` s yaw změnou. Teprve z nového směru a nového sensory frame se provede escape move.

### 5. Critic mohl okamžitě zrušit plán, který sám vyvolal

Pokud `force_replan` zůstával true, active escape plan se při každém frame nahradil novým escape planem a mohl zůstat na prvním kroku.

Aktivní `escape_stagnation` je nyní chráněn před stejným critic signálem, dokud:
- krok fyzicky uspěje a plán pokračuje;
- nebo krok selže a plán se zahodí.

### 6. Escape reorientation nebyl zahrnut do scan gate

`look` může vzniknout nejen z `scan_*` goalu, ale nově i uvnitř explore escape plánu.

Intrinsic curriculum proto blokuje nový scan podle skutečného předchozího `action_type == look`, ne pouze podle předchozího goal kindu.

## Nový motorický invariant

```text
World ACK
!= motorický úspěch

horizontální displacement
!= navigační úspěch

navigační úspěch
= dostatečný projected progress v požadovaném směru
```

Alua se učí a přeplánuje podle tohoto posledního signálu.

## Benchmark

Offline evaluator nově reportuje:
- `mean_move_progress`;
- `low_progress_moves`;
- `navigation_stagnation_detected`;
- `longest_move_streak`.

Dlouhý `move` streak není sám o sobě chyba, pokud má kvalitní progress. To je důležité, aby benchmark netrestal normální delší chůzi po otevřeném prostoru.

## Field acceptance

Po nasazení obou repozitářů:
1. malý odraz nebo collision slide nesmí být plný success;
2. několik slabých move outcomes musí vytvořit critic stagnation;
3. Alua musí vložit fyzickou reorientaci;
4. po reorientaci musí z nového sensory frame zvolit escape směr;
5. `alua benchmark` nesmí hlásit navigation stagnation při normálním dlouhodobém pohybu.
