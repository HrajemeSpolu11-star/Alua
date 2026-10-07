# Přehled změn

## 2026-10-07 – audit mozku a odstranění look loopu

- nalezena hlavní příčina dlouhých sérií `look`: `scan_recovery` mohl po historických exploration failures trvale přebíjet další pohyb;
- `scan_recovery` i `scan_obstacle` nyní vyžadují intervenující exploration pokus před dalším scanem;
- staré failures už nevynucují recovery, pokud successes znovu převažují;
- scan direction už není odvozena z parity observation sequence a nevytváří jednoduchý levá/pravá oscilátor;
- zrakový percept přežije expiraci `target_ref`; handle je nyní volitelný motorický capability, nikoli podmínka existence perceptu;
- scan akce se již neučí jako reusable skills;
- reusable touch skill neukládá konkrétní ruku a při použití znovu vybere aktuálně dostupný effector;
- generic explore skill nesmí přebít aktuální blízkou překážku;
- kontextový obstacle-bypass se nepromuje na univerzální explore skill;
- opravena chyba řazení distance `0.0`;
- přidány regresní testy a `docs/AUDIT_BRAIN_2026-10-07.md`.


## 2026-10-07 – Alua přežije expirovaný target_ref

- `409 target_expired` už neukončí celý kognitivní runtime;
- rozhodnutí vytvořené nad stale handle se uloží jako `stale_target`, nevytvoří expectation ani falešný goal attempt a runtime čeká na čerstvý vjem;
- přidán regresní test, že stejný zastaralý handle se po posunu observation cursoru neopakuje.


## Nezveřejněno

### 2026-10-06 – vnímání vlastního těla a volba ruky

- Alua umí číst bezpečný observation kanál `body_schema` bez importu World katalogů;
- ExplorationPolicy vybírá pro `touch` skutečně dostupnou a volnou `hand_right` nebo `hand_left`;
- vybraný efektor se ukládá do vysvětlitelné rationale a odesílá v `parameters.effector`;
- obsazená pravá ruka způsobí výběr levé ruky;
- při starším observation bez body schema zůstává kompatibilní action bez explicitního efektoru;
- úspěch ruky se stále neučí z ACK, ale až z budoucího motorického/tělesného vjemu;
- doplněny policy testy a dokumentace.

### 2026-10-06 – oprava priority ověřování nejistého objektu

- opraven konflikt intrinsic curriculum, kdy `scan_obstacle` přebíjel `inspect_object` u známého objektu s nedostatečnou evidencí;
- první dva ověřovací pokusy mají nyní vyšší informační prioritu než obecný scan překážky;
- po dosažení tří pokusů se `inspect_object` stále přestane nabízet podle původního pravidla `needs_verification`.

### 2026-10-06 – embodied learning V1

- SQLite kognitivní schema zvýšeno na v2;
- před migrací schema v1 se automaticky vytváří lokální SQLite backup;
- přidány expectations, beliefs a bridge_action_sequence;
- změna World session invaliduje staré pending/planned world akce a expectations;
- přidána bounded WorkingMemory s kapacitou 32 frame;
- target_ref vazby existují pouze krátkodobě v RAM;
- motorický sensory channel koreluje World výsledek s Bridge action sequence;
- belief update vzniká až budoucím motorickým vjemem, nikoli HTTP ACK;
- beliefs mají support_count, contradiction_count a confidence;
- ExplorationPolicy používá Worldem definované move/look a pouze nedestruktivní manipulate/touch;
- damage signal vyvolá ústup, blízká překážka rozhlédnutí a volný prostor opatrný pohyb;
- další aktivní akce čeká na vyřešení, invalidaci nebo expiraci předchozí expectation;
- testy pokrývají migraci, backup, session invalidaci, working memory, policy, target_ref sanitizaci a learning;
- přidán tools/e2e_smoke_termux.sh pro skutečný tříprocesový smoke test.

### 2026-10-06 – audit dokumentace a recovery kontrakt

- proveden audit skutečné implementace proti dokumentované architektuře;
- přidán docs/AUDIT_2026-10-06.md;
- přidán docs/IDENTITY_SESSION_RECOVERY.md;
- přesně oddělen agent_id, session_id, observation sequence, decision_id, request_id a target_ref;
- zdokumentovány restarty a transportní failure modes.

### 2026-10-06 – první samostatný Alua AI runtime

- Python 3.12+ package src/alua;
- bezpečná localhost konfigurace;
- AluaBridge Agent API klient;
- schema validation;
- vlastní SQLite persistence;
- target_ref odstraněn z dlouhodobého uložení;
- epizodická evidence a appearance statistiky;
- session transition;
- deterministické client_action_id;
- první bezpečná wait policy;
- CLI doctor/status/run;
- testy, boundary audit a GitHub CI.

### 2026-10-06 – přechod na samostatnou Alua AI

- Alua oddělena od Luanti do samostatného kognitivního procesu;
- jediným runtime rozhraním je AluaBridge Agent API;
- starý Lua companion označen jako historický prototyp;
- založena dokumentace po vzoru AluaWorld.

## 0.2.0 – 2026-09-24

- Luanti companion follow/stay/recall;
- jednoduchá paměť;
- diagnostický scan;
- modulární Lua základ.

## 0.1.0 – 2026-09-24

- první kostra Luanti modu;
- diagnostický příkaz;
- ContentDB metadata a MIT licence.
