# Bezpečnost a datová politika

## Chráněné hranice

- Agent token;
- izolace agent_id;
- epistemická hranice;
- integrita kognitivní paměti;
- nemožnost provádět libovolný kód přes world action;
- nemožnost číst World API;
- nemožnost vydávat transportní ACK za fyzickou pravdu.

## Tokeny

ALUA_AGENT_TOKEN:
- pouze environment proměnná;
- nikdy Git;
- nikdy SQLite;
- nikdy decision trace;
- nikdy exception dump v čistém textu.

World token nesmí být procesu Alua vůbec dostupný.

## Síť

V1:
- pouze loopback;
- ALUABRIDGE_URL musí být localhost/127.0.0.1;
- žádné otevření Agent API do internetu;
- žádná automatická cloud synchronizace kognitivní DB.

## Data provenance

Každá empirická znalost musí být odvoditelná od:
- jedné nebo více epizod;
- definovaného learning rule;
- explicitního interního rozhodnutí.

Ruční developer edit belief DB je diagnostický zásah a musí být označen, nikoli vydáván za zkušenost agenta.

## World truth contamination

Zakázané:
- importovat AluaWorld katalogy do Alua;
- parsovat AluaWorld zdrojový kód za běhu;
- volat GitHub/web pro identifikaci věcí, které Alua právě vnímá;
- mapovat appearance_id podle interních World tabulek;
- používat admin telemetry k plánování.

## Externí nástroje

Kognitivní runtime V1 nemá:
- shell tool;
- filesystem tool mimo vlastní datový adresář;
- web browser;
- GitHub API;
- libovolné pluginy.

Budoucí schopnost práce s externími systémy musí být samostatný fyzický nebo simulační kontrakt.

## Poškozená databáze

Runtime musí:
- používat transakce;
- kontrolovat schema_version;
- vytvořit bezpečnou zálohu před migrací;
- při neznámé novější verzi raději odmítnout start než tiše přepsat data.

## Logování

Log smí obsahovat:
- agent_id;
- session transition;
- observation sequence;
- action type;
- client_action_id;
- interní decision IDs;
- error code.

Nemá obsahovat:
- bearer token;
- kompletní raw payload bez potřeby;
- cizí agent data.

## Budoucí více agentů

Oddělení pamětí je default. Sdílení znalosti musí probíhat skrze světovou komunikaci nebo explicitně navržený experiment, ne společnou tabulkou beliefs.
