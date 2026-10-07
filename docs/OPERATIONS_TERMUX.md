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

Aktualizace 2026-10-06: bod 3 už není ruční krok. První připojený tester vytvoří chybějící `alua:1` automaticky. Samostatný proces Alua se tím ale nespustí; stále je nutné provést bod 4. V panelu má být následně `tělo aktivní`, `Bridge session aktivní` a `mozek připojen`.

## Ověření

    set -a
    . ./.env
    set +a
    .venv/bin/python -m alua doctor
    .venv/bin/python -m alua status

Před spuštěním `alua run` musí `doctor` ukázat aktivní session a `last_observation_sequence > 0`. Pokud je sequence 0, neopravovat policy naslepo; problém je před kognitivní vrstvou.

`status` lze bezpečně spustit v jiné Termux session i za běhu Alua. Pouze čte lokální SQLite a nespouští druhý kognitivní runtime.

Aktuální runtime považuje `409 target_expired` za recoverable stale-handle stav. Konkrétní decision označí `stale_target` a pokračuje dalším čerstvým vjemem; proces se na této chybě nesmí ukončit.

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

Historický text této fáze uváděl schema v2. Aktuální kognitivní schema je v3; migrace v1 i v2 před změnou vytváří lokální backup. Novější neznámé schema runtime odmítne.

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

## Behaviorální report Cognitive V2

Report nevyžaduje běžící Bridge ani World. Čte pouze lokální kognitivní DB:

```bash
cd "$HOME/alua/Alua"
set -a
. ./.env
set +a
.venv/bin/python -m alua evaluate
```

Pro delší vzorek:

```bash
.venv/bin/python -m alua evaluate --limit 2000
```

Po nasazení V2 se doporučuje nejprve několik minut normálně nechat Alua autonomně běžet a potom report zkontrolovat. `look_loop_detected=true` nebo `action_stereotype_detected=true` je důvod otevřít decision rationale a neřešit problém pouze vizuálním pozorováním entity.

## Aktualizace na SQLite schema v4

Po aktualizaci Alua není potřeba mazat kognitivní DB.

První start příkazu, který otevře Store, provede migraci a vytvoří soubor ve tvaru:

```text
alua.sqlite3.pre-v4-YYYYMMDD-HHMMSS.bak
```

Potom lze ověřit:

```bash
.venv/bin/python -m alua status
```

Očekávané `schema_version` je `4`.

Po několika minutách live běhu:

```bash
.venv/bin/python -m alua benchmark --limit 2000
```

Benchmark nevyžaduje běžící Bridge ani World; čte vlastní SQLite Alua.
