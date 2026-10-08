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

Aktuální kognitivní schema je v5. Store provádí podporovanou forward migraci a před změnou starší DB vytvoří backup. Pro v4 -> v5 vzniká `<db>.pre-v5-YYYYMMDD-HHMMSS.bak`. Episodes, beliefs, goals, skills a perceptual evidence se nemažou. Novější neznámé schema runtime odmítne.

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

## Historická migrace schema v4

V4 zavedla belief provenance a perceptual topology. Aktuální deployment je schema v5. Staré pre-v4 backupy lze zachovat pro audit; nové nasazení se řídí V5 postupem níže.


## Cognitive Core V5 – aktualizace a diagnostika

Po pullu V5 otevře první příkaz používající Store databázi schema v5. Před migrací starší databáze se automaticky vytvoří soubor:

```text
<db>.pre-v5-YYYYMMDD-HHMMSS.bak
```

Doporučená kontrola po update:

```bash
cd "$HOME/alua/Alua"
set -a
. ./.env
set +a

.venv/bin/python -m alua status
.venv/bin/python -m alua cognition-status
.venv/bin/python -m alua doctor
```

`cognition-status` je lokální read-only diagnostika vyšší kognice. Ukazuje počty cognitive records, aktivní missions a poslední vysvětlitelný cognitive snapshot.

Po field běhu:

```bash
.venv/bin/python -m alua evaluate --limit 2000
.venv/bin/python -m alua benchmark --limit 2000
```

Při prvním V5 testu nemažte starou DB. Migrace je navržena tak, aby episodes, beliefs, goals a skills zachovala.



## Přesný Cognitive Core V5 deployment

1. Zastavit pouze Alua AI proces.
2. Aktualizovat repo:

```bash
cd "$HOME/alua/Alua"
git pull --ff-only
git rev-parse --short HEAD
```

3. Načíst konfiguraci:

```bash
set -a
. ./.env
set +a
```

4. Otevřít Store:

```bash
.venv/bin/python -m alua status
```

Očekávat `schema_version: 5`. U starší v4 DB ověřit vznik pre-v5 backupu.

5. Zkontrolovat vyšší kognitivní stav:

```bash
.venv/bin/python -m alua cognition-status
```

6. Ověřit Bridge/World session:

```bash
.venv/bin/python -m alua doctor
```

7. Spustit runtime:

```bash
.venv/bin/python -m alua run
```

8. Po živém testu v jiné Termux session:

```bash
.venv/bin/python -m alua cognition-status
.venv/bin/python -m alua evaluate --limit 2000
.venv/bin/python -m alua benchmark --limit 2000
```

Při regresi nemažte DB. Uchovat aktuální SQLite, pre-v5 backup a diagnostické výstupy. Kompletní recovery a rollback: `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.
