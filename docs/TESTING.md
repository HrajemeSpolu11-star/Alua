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
