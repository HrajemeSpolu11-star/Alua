# Architektura Alua AI

## Cíl

Alua je samostatná Python aplikace bez přímé závislosti na Luanti nebo AluaWorld. V1 bude běžet na stejném zařízení jako AluaBridge a komunikovat pouze přes localhost HTTP Agent API.

Navržená struktura:

    Alua/
    ├── src/alua/
    │   ├── config.py
    │   ├── runtime.py
    │   ├── bridge_client.py
    │   ├── schema.py
    │   ├── clock.py
    │   ├── persistence/
    │   ├── perception/
    │   ├── memory/
    │   ├── beliefs/
    │   ├── needs/
    │   ├── goals/
    │   ├── planning/
    │   ├── actions/
    │   ├── learning/
    │   └── diagnostics/
    ├── tests/
    ├── docs/
    └── tools/

## Hlavní kognitivní cyklus

    Bridge observation
          |
          v
    perception ingest
          |
          v
    working memory
          |
          v
    belief/world-model update
          |
          v
    needs + current context
          |
          v
    goal selection
          |
          v
    bounded planner
          |
          v
    primitive ActionRequest
          |
          v
    AluaBridge
          |
          v
    pozdější observation
          |
          v
    outcome attribution + learning

Akce sama nevrací pravdivý herní výsledek.

## Komponenty

### config

Načítá pouze provozní konfiguraci:
- ALUA_AGENT_ID;
- ALUABRIDGE_URL;
- ALUA_AGENT_TOKEN;
- ALUA_DB_PATH;
- limity kognitivních cyklů;
- diagnostické přepínače.

Token se nikdy nezapisuje do SQLite ani logů.

### bridge_client

Jediný modul, který smí komunikovat s AluaBridge.

Odpovědnosti:
- načíst session;
- číst observations po poslední zpracované sequence;
- posílat ActionRequest;
- používat stabilní client_action_id při retry;
- klasifikovat transportní chyby;
- nikdy neinterpretovat význam vjemu.

### perception

Normalizuje validní observation do interního percept formátu.

Nesmí:
- doplňovat world truth;
- překládat appearance_id na technický název;
- považovat target_ref za dlouhodobou identitu.

### working memory

Krátký kontext posledních vjemů, aktivních hypotéz a očekávaných následků akcí.

Je bounded.

### episodic memory

Ukládá zkušenosti v čase:
- co bylo vnímáno;
- jaký byl interní stav;
- co Alua udělala;
- co později pozorovala.

### beliefs / world model

Udržuje opravitelné hypotézy:
- opakující se perceptuální vzory;
- vztahy akce -> pozorovaný následek;
- pravděpodobné lokální vztahy;
- naučené užitečnosti a rizika.

Každé přesvědčení má confidence, evidenci a čas poslední aktualizace.

### needs

V1 nesmí vymýšlet fyzické potřeby, které tělo neposkytuje. Pokud World později dodá hlad, žízeň, bolest, teplotu nebo únavu jako vjem vlastního těla, needs je interpretuje pro rozhodování.

Může existovat nízká vrozená kognitivní potřeba explorace, ale musí být jasně oddělena od fyzických potřeb těla.

### goals

Vytváří krátkodobé cíle z potřeb, známého rizika, nedokončených plánů a explorace.

### planning

V1 používá malý bounded planner nad primitivními akcemi. Nemá přímý seznam world schopností mimo povolené typy Bridge session.

### learning

Aktualizuje přesvědčení až z pozorovaných následků. Udržuje vazbu mezi očekáváním a pozdější observation.

### diagnostics

Zapisuje vysvětlitelnou kognitivní stopu:
- observation sequence;
- aktivní potřeby;
- kandidátní cíle;
- vybraný cíl;
- důvody výběru akce;
- očekávaný následek;
- pozdější vyhodnocení.

Diagnostika nesmí Alua dodávat nové world truth.

## Persistence

V1: SQLite.

Oddělené logické oblasti:
- meta a schema migrations;
- processed observations;
- episodes;
- beliefs;
- learned transitions;
- active goals;
- pending expectations;
- decision trace.

Každý agent má samostatnou databázi nebo striktně izolovaný namespace. V1 preferuje jeden agent na jeden proces a jeden DB soubor.

## Session boundary

Změna Bridge session_id znamená nový runtime světa/těla.

Při změně:
- zahodit target_ref;
- zrušit čekající plány závislé na target_ref;
- zachovat dlouhodobé epizody a naučená přesvědčení;
- nevydávat starou akci proti novému runtime;
- zapsat explicitní session transition.

## Výkon

Primární vývoj probíhá i na telefonu:
- žádné neomezené embedding databáze v první verzi;
- bounded pracovní paměť;
- dávkové SQLite zápisy;
- plánovač s tvrdým limitem uzlů a času;
- žádný externí LLM v hlavním cyklu;
- nejdříve měřit, potom škálovat.

## Směr závislostí

    config/persistence
          ^
    bridge + schema
          ^
    perception + memory
          ^
    beliefs + learning
          ^
    needs + goals
          ^
    planner + actions
          ^
        runtime

Vyšší vrstva nesmí obcházet nižší hranici.
