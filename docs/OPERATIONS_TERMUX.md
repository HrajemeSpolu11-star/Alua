# Provoz Alua AI v Termuxu

## Umístění

Doporučeně:
    ~/alua/Alua
    ~/alua/Aluabridge
    ~/alua/games/aluaworld

Kognitivní data:
    ~/alua/data/alua-1/

DB nesmí být uvnitř Git repozitáře.

## Instalace

    pkg install python git
    git clone <Alua repository> ~/alua/Alua
    cd ~/alua/Alua
    python -m venv .venv
    .venv/bin/pip install -e .

Připrav environment podle .env.example. Token musí být stejný agent token, který má pro alua:1 nakonfigurovaný AluaBridge.

## Environment

    ALUA_AGENT_ID=alua:1
    ALUABRIDGE_URL=http://127.0.0.1:8787
    ALUA_AGENT_TOKEN=<secret>
    ALUA_DB_PATH=$HOME/alua/data/alua-1/alua.sqlite3
    ALUA_POLL_INTERVAL=0.25
    ALUA_REQUEST_TIMEOUT=2.0

Token nesmí být commitnutý.

## Procesy

Na jednom telefonu běží odděleně:
1. Luanti server s AluaWorld;
2. AluaBridge na 127.0.0.1:8787;
3. Alua AI.

## Ověření

Po exportu environment proměnných:

    .venv/bin/python -m alua doctor
    .venv/bin/python -m alua status
    .venv/bin/python -m alua run --once

doctor kontroluje DB, /health a aktivní agent session.

## Start

    .venv/bin/python -m alua run

Alua runtime umí čekat při dočasné nedostupnosti Bridge s omezeným backoffem. Neplatná autentizace je fatální chyba a nemá se nekonečně opakovat.

## Backup

Před budoucí DB migrací:
- zastavit Alua proces;
- vytvořit timestampovanou kopii DB;
- spustit migration doctor;
- až potom start runtime.

## Testy

    bash tools/run_tests.sh

## Telefonní omezení

V1:
- nemá busy-loop;
- nemá povinný LLM inference;
- používá SQLite;
- komunikuje jen přes localhost;
- neposílá data do cloudu;
- neukládá bearer token.
