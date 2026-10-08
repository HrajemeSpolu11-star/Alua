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

## Adaptive V3 persistence a replay

Unit testy navíc ověřují:
- belief provenance;
- perceptual place persistence;
- transition success/failure evidence;
- persistent navigation penalty;
- utility rozdíl mezi opakovaně úspěšným a neúspěšným golem;
- damage vliv na intrinsic utility;
- invalidaci egocentrického view po look;
- sensory replay.

Po live testu použít:

```bash
.venv/bin/python -m alua benchmark --limit 2000
```

Exit code `0` znamená, že aktuální uložená session prošla acceptance checks. Nenulový exit code znamená behaviorální regresi nebo nedostatek evidence; JSON výstup přesně ukáže neúspěšné checks.

Migrace schema v3 -> v4 musí zachovat staré episodes/beliefs/skills a vytvořit pre-v4 backup.

## One-block stagnation acceptance

Po opravě motor progress kontraktu je behaviorální acceptance přísnější.

`evaluate` / `benchmark` nyní rozlišuje:
- dlouhou kvalitní cestu tvořenou mnoha `move` akcemi;
- dlouhou low-progress sérii, kdy se tělo pouze odráží nebo posouvá bez cíleného postupu.

Nové metriky:
- `mean_move_progress`;
- `low_progress_moves`;
- `navigation_stagnation_detected`;
- `longest_move_streak`.

Unit testy navíc kontrolují:
- `partial_effect` není motor success;
- low-progress maneuver dostane vyšší navigation cost;
- repeated successful forward travel není falešný stereotype;
- stagnation vytvoří `reorient_escape -> navigate_escape -> navigate_frontier`;
- force-replan nezničí právě probíhající escape plan;
- libovolný předchozí physical `look` blokuje okamžitý scan.

Field test musí používat současně odpovídající AluaWorld i Alua commit. Starý World neposkytuje graded progress a není validním testem této opravy.


## Cognitive Core V5 acceptance

Nové unit testy pokrývají:
- attention focus a sensory surprise;
- object permanence po krátkém zmizení z pohledu;
- persistent object concept bez target_ref;
- predictive progress learning a růst confidence;
- dead-end route backtracking;
- heading correction před návratem;
- metacognitive stagnation/loop detection;
- cognitive snapshot persistence;
- policy pro remembered-route return a model-selected move;
- schema v5 `cognitive_records`;
- v4 -> v5 backup migraci.

Povinné kontroly před merge zůstávají:

```bash
python -m compileall -q src tests tools
python -m unittest discover -s tests -v
python tools/audit_repo.py
```

Po nasazení:

```bash
.venv/bin/python -m alua cognition-status
.venv/bin/python -m alua evaluate --limit 2000
.venv/bin/python -m alua benchmark --limit 2000
```

Field acceptance V5:
- ve známé slepé větvi vznikne `spatial_backtrack` místo neomezeného look loopu;
- návrat používá poslední vlastní route transition, ne World souřadnici;
- opakovaný low progress zvyšuje metacognitive stagnation;
- prediction confidence se mění pouze podle sensory outcomes;
- action risk roste po failure/slip/damage;
- object memory krátce přetrvá mimo zorné pole;
- decision rationale obsahuje `cognitive_state`;
- schema migration zachová starší dlouhodobou paměť;
- benchmark nesmí regresovat staré anti-loop invarianty.



### V5 CI regresní incident

Během PR #10 nové active-experiment rozhodování původně vracelo goal key `experiment:touch:pabc`. Dva existující runtime testy očekávaly kanonický `inspect:pabc` a selhaly.

Testy nebyly upraveny tak, aby nový key přijaly. Opravena byla implementace:
- experiment zůstává samostatný selector/reason;
- fyzický goal i evidence namespace zůstávají `inspect:<appearance>`.

Tím se zachovaly staré invarianty goal statistics a skill learning.

### Povinné V5 field test artifacts

Při reportu chyby uložit:
- výstup `alua status`;
- výstup `alua cognition-status`;
- `alua evaluate --limit 2000`;
- `alua benchmark --limit 2000`;
- World log s action/motor outcome;
- Bridge log pouze pro korelaci transportu;
- přesný Alua commit;
- existenci pre-v5 backupu;
- screenshot/pozorování behavioru jako doplněk, nikoli jediný důkaz.

Kompletní postup a rollback: `docs/COGNITIVE_CORE_V5_IMPLEMENTATION_LOG.md`.
