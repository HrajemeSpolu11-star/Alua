# Cognitive V5 – podrobný letový záznam mozku

Datum: 2026-10-08.

## Proč nestačí Bridge trace

Bridge má skutečnou transportní stopu: kterou observation přijal,
co předal AI, jakou akci AI poslala a co World ACKoval.
Bridge však **nezná** výběr cílů, vlastní predikce, paměť, strategii,
metakognici ani vnitřní důvod, proč se agent rozhodl.
Tyto informace vlastní pouze `Alua`.

`src/alua/flight_recorder.py` je operátorský čtecí nástroj nad
existující SQLite v5, nikoli změna mozku nebo privilegovaný senzor.
Každá položka JSONL představuje skutečný persistovaný záznam.

## Co přesně je uvnitř

- `sensory_episode`: kompletní uložená `PerceptionFrame`
  epizoda z databáze, včetně původních fyzických smyslových
  signálů, bez skrytých World souřadnic.
- `cognitive_decision`: původní `decision_id`, session,
  `observation_sequence`, vybraný goal kind/key, skill, zvolená
  primitivní akce a parametry, původní `rationale`
  včetně diagnostického `cognitive_state`.
- Očekávání: `bridge_action_sequence`,
  `expectation_state`, `verified_motor_outcome`,
  `outcome_success`, `progress_signal`. Odmítání,
  stagnace, nízký pokrok a slepé uličky tak lze párovat
  na konkrétní rozhodnutí a fyzický výsledek.
- `cognitive_model_snapshot`: poslední persistovaný
  `cognition:last-state`, např. drive, metakognice,
  navigační paměť a aktuální prediktivní stav, pokud
  jej V5 uložila.

Při běžícím `--follow` se stejný decision_id vypíše znovu
pouze tehdy, pokud se reálně změnil jeho persistovaný
status nebo outcome. Žádné potichu vytvořené falešné
úspěchy. `--no-episodes` pro menší soubor; limit 1..2000.

## Příkazy v Termuxu

V druhém Termux okně, zatímco AI běží:

```bash
cd "$HOME/alua/Alua"
set -a; . ./.env; set +a
.venv/bin/python -m alua mind-log --limit 200 --follow --output "$HOME/alua-mind.jsonl"
```

Pro jednorázový audit posledních záznamů:

```bash
.venv/bin/python -m alua mind-log --limit 200
```

Pro čtení souboru za běhu (třetí session):

```bash
tail -f "$HOME/alua-mind.jsonl"
```

## Bezpečnost, limity a provoz

- Výstup zůstává **jen lokálně u správce**, nikdy se neodesílá
  do Agent API ani nemění runtime.
- Operátorský JSONL může obsahovat cenné soukromé
  vzorce a dlouhé smyslové záznamy. Soubor je vytvářen
  v append režimu s Unix právy 0600. Pravidelně
  archivovat / rotovat, při dlouhém provozu může být velký.
- `mind-log` nečte neuložené myšlenky a nepředstírá
  vědomí nebo nepozorované vnitřní stavy. Ukazuje
  důvody a data, která V5 skutečně zapsala.
- `--follow` periodicky čte SQLite, nemodifikuje ji;
  přímo nasazená Alua může pokračovat v učení.
- Síťové odmítnutí, auth, target expiration a payload
  sanitizaci vyšetřit samostatně přes
  `AluaBridge: python -m aluabridge trace --agent alua:1`.
- Plný mezirepo bezpečnostní audit:
  `Aluabridge/docs/SECURITY_AUDIT_V5_2026-10-08.md`.

## Acceptance

`python -m unittest discover -s tests -v` včetně
`test_flight_recorder.py`; poté živě ověřit růst nových
episode/decision událostí, párování `source_sequence`,
backtracking a náhradní strategii po slepé uličce.
