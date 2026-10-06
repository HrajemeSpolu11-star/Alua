# Přehled změn

## Nezveřejněno

### 2026-10-06 – první samostatný Alua AI runtime

Implementováno:
- Python 3.12+ package src/alua;
- bezpečná localhost konfigurace;
- AluaBridge Agent API klient;
- validace session a observations proti schema_version 1;
- vlastní SQLite persistence;
- očištění target_ref před dlouhodobým uložením;
- epizodická evidence a appearance statistiky;
- session transition;
- deterministické client_action_id;
- první bezpečná bootstrap policy;
- runtime step a dlouhodobá smyčka s backoffem;
- CLI doctor/status/run;
- unit a contract testy;
- statický boundary audit;
- GitHub CI.

Po prvním CI běhu byl zpřesněn boundary audit: čisté parsování URL přes urllib.parse je povolené, zatímco skutečný síťový přístup zůstává mimo bridge_client.py zakázaný. Všech 11 runtime testů prošlo už v prvním běhu.

Bootstrap policy záměrně používá jen wait. Aktivní move/look/manipulate se zapne až po přesném end-to-end kontraktu persistentního AI těla v AluaWorld; nechceme vymýšlet význam parametrů pohybu uvnitř mozku.

### 2026-10-06 – přechod na samostatnou Alua AI

Architektura:
- Alua je nově definována jako samostatný kognitivní proces mimo Luanti;
- jediným runtime rozhraním ke světu je AluaBridge Agent API;
- AluaWorld vlastní fyziku, tělo, smyslový původ signálu a následky akcí;
- AluaBridge vlastní transport, session, bounded fronty, target_ref, lease a ACK;
- Alua vlastní paměť, přesvědčení, cíle, plánování, rozhodování a učení;
- starý Lua companion je označen jako historický prototyp, ne cílový mozek.

Dokumentace:
- založen dokumentační standard po vzoru AluaWorld;
- přidána projektová paměť pro další chaty;
- přidán přesný Bridge kontrakt;
- přidána cílová kognitivní architektura;
- popsán model vnímání, přesvědčení, paměti a učení;
- přidána pravidla bezpečnosti, testování, provozu a budoucí práce;
- aktualizována roadmapa a architektonická rozhodnutí.

## 0.2.0 – 2026-09-24

- trvalý Luanti companion navázaný na vlastníka;
- follow, stay a recall;
- jednoduchá paměť pozice vlastníka;
- diagnostický scan;
- modulární Lua základ: registry, events, verzovaný state;
- dokumentace původní perception boundary.

## 0.1.0 – 2026-09-24

- první kostra Luanti modu;
- diagnostický příkaz;
- ContentDB metadata a MIT licence.
