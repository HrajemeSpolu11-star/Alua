# Provoz Alua AI v Termuxu

## Umístění

Doporučeně:

    ~/alua/Alua
    ~/alua/Aluabridge
    ~/alua/games/aluaworld
    ~/alua/data/alua-1/

Kognitivní DB nesmí být uvnitř Git repozitáře.

## Instalace

    pkg install python git
    cd ~/alua/Alua
    python -m venv .venv
    .venv/bin/pip install -e .
    cp .env.example .env

V .env nastavte agent token shodný s tokenem alua:1 v AluaBridge.

## Environment

    ALUA_AGENT_ID=alua:1
    ALUABRIDGE_URL=http://127.0.0.1:8787
    ALUA_AGENT_TOKEN=<secret>
    ALUA_DB_PATH=$HOME/alua/data/alua-1/alua.sqlite3
    ALUA_POLL_INTERVAL=0.25
    ALUA_REQUEST_TIMEOUT=2.0

## Pořadí procesů

1. AluaBridge;
2. AluaWorld;
3. při úplně prvním použití jako správce spustit /aw_alua_spawn;
4. Alua AI.

Body-aware Bridge adaptér nevytvoří agent session dřív, než ve Worldu existuje alua:1. Po prvním spawnu je tělo persistentní.

## Ověření

    set -a
    . ./.env
    set +a
    .venv/bin/python -m alua doctor
    .venv/bin/python -m alua status

## Skutečný E2E smoke test

Po spuštění Bridge a Worldu:

    bash tools/e2e_smoke_termux.sh

Helper provede několik kognitivních cyklů a skončí úspěchem pouze pokud:
- existuje aktivní World session;
- Alua přijala observation;
- vytvořila decision;
- z budoucího motorického vjemu vznikl belief.

Počet cyklů lze změnit přes ALUA_E2E_CYCLES.

## Trvalý start

    .venv/bin/python -m alua run

## SQLite migrace

Aktuální schema je v2. Při otevření schema v1 se před změnou automaticky vytvoří lokální backup. Novější neznámé schema runtime odmítne.

## Testy

    bash tools/run_tests.sh

## Telefonní omezení

V1:
- nemá busy-loop;
- nemá povinný LLM inference;
- používá bounded WorkingMemory;
- komunikuje pouze přes localhost;
- neposílá data do cloudu;
- neukládá bearer token.
