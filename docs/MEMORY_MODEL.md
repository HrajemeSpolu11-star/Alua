# Model paměti Alua AI

## Cíl

Paměť musí umožnit učení a kontinuitu identity, ale nesmí růst bez omezení ani zaměnit transportní data za zkušenost.

## 1. Working memory

Obsahuje pouze krátký aktivní kontext:
- poslední observations;
- aktuální percepty;
- aktivní target_ref;
- současný cíl;
- rozpracovaný plán;
- očekávané následky posledních akcí;
- krátkodobé signály nebezpečí.

Working memory je bounded a po restartu ji lze částečně rekonstruovat pouze z perzistentního stavu.

## 2. Episodic memory

Epizoda popisuje zkušenost v čase.

Minimálně:
- agent_id;
- session_id;
- simulation_time;
- observation sequence;
- percept summary;
- interní stav;
- zvolený cíl;
- action intent;
- client_action_id;
- pozdější outcome evidence;
- odkazy na vzniklé nebo změněné beliefs.

Neukládá tajné tokeny.

## 3. Semantic / belief memory

Obsahuje naučené vztahy a zobecnění.

Příklad:
- perceptual signature -> typické reakce;
- akce v kontextu -> distribuce následků;
- signál -> odhad rizika;
- lokální vzorec -> pravděpodobný přechod.

Každý záznam je opravovatelný.

## 4. Procedural memory

Pozdější vrstva pro naučené postupy:
- sekvence akcí, které často vedou k cíli;
- podmínky použití;
- úspěšnost;
- náklady;
- známé failure modes.

Procedura nikdy nesmí obejít Bridge primitivní akce.

## Retence

V1:
- raw observations: omezená nebo časově řízená retence;
- epizody: dlouhodobé, ale s budoucí kompresí;
- beliefs: dlouhodobé;
- decision trace: omezená retence pro diagnostiku;
- target_ref: pouze krátkodobě;
- transportní retry metadata: pouze dokud jsou relevantní.

## Identita

Stabilní agent_id určuje identitu kognitivního agenta.

Restart procesu:
- nesmí resetovat dlouhodobou paměť;
- nesmí změnit agent_id;
- musí navázat na poslední bezpečně commitnutou observation sequence.

Nová Bridge session:
- neznamená novou osobnost;
- znamená nový krátkodobý World runtime kontext.

## Migrace

SQLite schema má explicitní integer verzi.

Každá změna:
- má forward migraci;
- nesmí tiše zahodit beliefs;
- zálohuje nebo odmítne neznámou novější verzi;
- má unit test migrace.

## Izolace

V1 preferuje:
    jedna Alua = jeden proces = jedna SQLite databáze.

Až později lze přidat supervisor více agentů. Sdílená DB nesmí být zavedena jen kvůli pohodlí.
