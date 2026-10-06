# Přehled změn

## Nezveřejněno

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

### Předchozí historie

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
