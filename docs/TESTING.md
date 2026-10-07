# Testování Alua AI

## Povinné lokální kontroly

    python -m compileall -q src tests tools
    python -m unittest discover -s tests -v
    python tools/audit_repo.py

V Termuxu lze použít:
    bash tools/run_tests.sh

## Co aktuální testy pokrývají

### Config
- loopback Bridge je povolen;
- vzdálený Bridge endpoint je odmítnut.

### Schema
- nested world truth je odmítnut;
- session jiného agenta je odmítnuta.

### Perception
- target_ref zůstane ephemeral;
- persistentní percept target_ref neobsahuje;
- appearance_id se zachová jako neprůhledný podpis.

### Store
- změna session resetuje observation cursor;
- dlouhodobá appearance zkušenost zůstává;
- persistentní epizoda neobsahuje target_ref.

### Runtime
- observation se uloží;
- vznikne decision;
- bootstrap odešle bezpečný wait;
- bez nové observation se neposílá další akce.

### Bridge client
- Agent endpoint dostane správný bearer token;
- veřejný health endpoint agent token nedostane.

## Contract test s falešným Bridge

Další rozšíření má simulovat:
- 403;
- 409 target_expired;
- 429 queue full;
- timeout po přijetí akce;
- restart session.

Transportní chyba nesmí měnit world belief jako fyzický outcome.

## Replay test

Bude přidán spolu s belief store.

## Negativní audit

tools/audit_repo.py kontroluje mimo jiné:
- žádný přímý Luanti/Minetest import;
- žádné aw_agents/aw_materials/aw_world_senses vazby;
- žádný World token;
- síťový import pouze v bridge_client.py;
- žádné subprocess/os.system v kognitivním runtime.

## CI

GitHub Actions:
- Python 3.12;
- editable install;
- compileall;
- unittest;
- boundary audit.

Po každém commitu na main se musí CI ověřit.


## Embodied learning V1

Testy navíc ověřují:
- bounded WorkingMemory a clear při session resetu;
- runtime asociaci target_ref s appearance_id bez persistence target_ref;
- parsování motorického feedbacku;
- bezpečný touch pouze u blízkého nového cíle;
- obstacle scan, cautious move a damage avoidance;
- schema v1 -> v2 migraci;
- automatický backup staré SQLite;
- invalidaci pending expectation při změně session;
- odstranění target_ref z decision i expectation persistence;
- korelaci source_sequence -> expectation;
- vznik evidence-based belief po budoucím motorickém vjemu.

Skutečný lokální E2E test:
    bash tools/e2e_smoke_termux.sh

E2E helper vyžaduje aktivní session, epizodu, decision a alespoň jeden learned belief.

## Body schema

`tests/test_policy.py` ověřuje, že touch používá `hand_right`, a při její obsazenosti `hand_left`. Chybějící či neplatný signál nesmí shodit runtime. Test neposuzuje fyzický úspěch z ACK; ten nadále patří do pozdější sensory attribution.

## Cognitive V2 behaviorální kontrola

Po live běhu lze bez dalšího přístupu do Worldu vyhodnotit aktuální session:

```bash
cd "$HOME/alua/Alua"
set -a
. ./.env
set +a
.venv/bin/python -m alua evaluate --limit 2000
```

Minimální acceptance po stabilizačním běhu:
- `consecutive_look_pairs = 0` v běžné exploraci;
- `longest_look_streak <= 1`, pokud nebyl explicitní jiný non-scan look mechanismus;
- `action_stereotype_detected = false`;
- při alespoň pěti resolved moves nemá být `low_move_success = true`;
- stale target může vzniknout, ale nesmí ukončit runtime.

Nové unit testy pokrývají:
- egocentrický world model;
- blocked-front frontier selection;
- navigation failure penalty;
- repeated-look critic;
- repeated-move-failure critic;
- composite obstacle plan;
- plan advance po skutečném sensory outcome;
- session reset V2 state;
- uncertainty-driven scan;
- decision/outcome trajectory join;
- evaluator quality flags.
