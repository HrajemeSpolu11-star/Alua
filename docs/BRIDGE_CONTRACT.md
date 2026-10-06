# Kontrakt Alua AI <-> AluaBridge V1

## Zásada

Alua AI používá pouze Agent API AluaBridge. World API je pro Alua nepřístupné a jeho token nesmí být dostupný procesu Alua.

Výchozí endpoint V1:
    http://127.0.0.1:8787

Autentizace:
    Authorization: Bearer <agent token>

## Session

Alua čte:
    GET /v1/agent/session?agent_id=<agent_id>

Session slouží k detekci restartu nebo výměny World runtime.

Změna session_id:
- invaliduje krátkodobé target_ref;
- ruší staré čekající world-specific plány;
- nevymazává dlouhodobou kognitivní paměť.

## Observations

Alua čte:
    GET /v1/agent/observations?agent_id=<agent_id>&after_sequence=<n>

Pravidla:
- zpracovávat pouze rostoucí sequence;
- poslední zpracovanou sequence uložit perzistentně;
- observation je vjem, nikoli kompletní stav světa;
- chybějící informace se nesmí dopočítat jako jistý fakt;
- appearance_id je perceptuální podpis, ne technická identita;
- target_ref je krátkodobý handle použitelný jen pro aktuální interakci.

Bridge aktuálně drží bounded frontu nejvýše čtyř observations. Alua proto nesmí předpokládat, že po dlouhém výpadku dostane úplnou historii.

## ActionRequest

Alua odesílá:
    POST /v1/agent/actions

Základ:
    schema_version: 1
    agent_id: stabilní ID
    client_action_id: stabilní ID pokusu
    type: wait | move | look | interact | manipulate
    target_ref: pouze pokud jej akce potřebuje
    parameters: primitivní parametry

Retry stejné logické akce musí použít stejné client_action_id.

## Povolené typy V1

- wait;
- move;
- look;
- interact;
- manipulate.

Manipulate vyžaduje platný target_ref.

## Co odpověď na action znamená

Přijetí ActionRequest Bridge znamená pouze zařazení do transportní fronty.

Ani Bridge request_id ani World ACK nesmí být v kognitivní paměti interpretovány jako:
- akce se povedla;
- objekt byl zvednut;
- cesta byla volná;
- cíl byl dosažen.

Fyzický následek se potvrzuje až budoucí observation.

## Chyby

Transportní chyba a zkušenost ze světa jsou dvě různé věci.

Například:
- 403 agent_auth_failed = provozní chyba;
- 409 target_expired = transportní/časová hranice targetu;
- 429 action_queue_full = backpressure;
- budoucí bolest, kontakt nebo změna polohy = world experience.

Alua se nesmí učit fyziku z HTTP status kódu.

## Idempotence

Každý zamýšlený pokus má vlastní client_action_id.

Při timeoutu:
- nejprve zopakovat tentýž request se stejným client_action_id;
- nevytvářet nové ID, dokud není známo, že jde o nový kognitivní pokus.

## Izolace agenta

Token je vázán na jediný agent_id.

Alua nesmí:
- měnit agent_id podle dat v observation;
- číst jiného agenta;
- používat jednu DB pro různé identity bez explicitního namespacingu;
- sdílet target_ref mezi agenty.

## Zdroj pravdy

Tento dokument musí zůstat synchronizovaný s:
- AluaBridge docs/PROTOCOL.md;
- AluaBridge docs/CONTRACTS.md;
- AluaBridge docs/DATA_OWNERSHIP.md;
- AluaWorld docs/AGENT_WORLD_CONTRACT.md.

Při změně Bridge schema se nejdřív mění verzovaný kontrakt a testy, teprve potom runtime Alua.

## Tělesný efektor v schema v1

`parameters.effector` je volitelné kompatibilní pole. Alua jej volí pouze podle vlastního kanálu `body_schema`. Bridge hodnotu transparentně přenese a World ji fyzicky ověří.

Příklad:

```text
type: manipulate
target_ref: krátkodobý handle
parameters: {verb: touch, effector: hand_right}
```

World-only `/v1/world/agents/status` není dostupný Alua tokenem. Slouží výhradně panelu testera pro rozlišení aktivní session od nedávno běžícího procesu Alua.
