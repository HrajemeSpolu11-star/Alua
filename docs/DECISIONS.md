# Architektonická rozhodnutí Alua AI

## ADR-A001 – Alua je samostatný kognitivní proces

Stav: přijato
Datum: 2026-10-06

Alua AI neběží jako Luanti mod. Je oddělená od AluaWorld procesu.

Důvod:
- silnější epistemická hranice;
- vlastní lifecycle;
- vlastní persistence;
- možnost více nezávislých mozků;
- svět nemusí důvěřovat kognitivnímu kódu.

## ADR-A002 – Jediné runtime rozhraní je AluaBridge Agent API

Stav: přijato
Datum: 2026-10-06

Alua nesmí přímo používat Luanti, World API, databázi AluaWorld ani interní katalogy.

## ADR-A003 – Python pro nový runtime

Stav: přijato
Datum: 2026-10-06

V1 bude Python 3.12+.

Důvod:
- kompatibilita s Termux;
- jednoduché SQLite;
- snadné testování;
- stejný provozní ekosystém jako AluaBridge;
- rychlá iterace kognitivních modulů.

## ADR-A004 – SQLite vlastní kognitivní paměť

Stav: přijato
Datum: 2026-10-06

Bridge SQLite není paměť Alua. Alua má vlastní verzovanou databázi.

## ADR-A005 – Jeden agent na jeden proces ve V1

Stav: přijato
Datum: 2026-10-06

V1 nezavádí supervisor ani sdílený multi-agent runtime. Každá Alua má vlastní proces, token a DB.

## ADR-A006 – Žádný povinný LLM

Stav: přijato
Datum: 2026-10-06

Základní autonomní chování musí fungovat bez externího LLM nebo cloud AI.

## ADR-A007 – Beliefs jsou evidence-based a opravitelné

Stav: přijato
Datum: 2026-10-06

Empirická znalost nesmí být jednorázově zapsána jako absolutní fakt bez provenance.

## ADR-A008 – target_ref není dlouhodobá identita

Stav: přijato
Datum: 2026-10-06

target_ref patří pouze do krátkodobého kontextu a po změně session nebo expiraci se zahazuje.

## ADR-A009 – ACK není outcome

Stav: přijato
Datum: 2026-10-06

Transportní přijetí akce nesmí přímo měnit world belief jako potvrzený fyzický výsledek.

## ADR-A010 – Starý Lua companion se zatím zachovává

Stav: přijato
Datum: 2026-10-06

Původní Luanti prototyp se nemaže v první migrační změně. Nový Python runtime na něm ale nesmí záviset.

## ADR-A011 – agent_id je dlouhodobá identita Alua

Stav: přijato
Datum: 2026-10-06

Restart procesu, Bridge ani Worldu nesmí sám o sobě vytvořit novou osobnost.

agent_id je dlouhodobá identita kognitivního agenta. Přesná biologická semantika smrti těla a případného nového těla bude rozhodnuta samostatně.

## ADR-A012 – změna session invaliduje ephemeral stav, ne automaticky dlouhodobou zkušenost

Stav: přijato
Datum: 2026-10-06

Nový session_id:
- zahazuje target_ref;
- ruší krátkodobé world-specific plány;
- resetuje observation cursor;
- nesmí automaticky vymazat epizodickou paměť a beliefs stejného agent_id.

Před aktivní manipulací musí runtime umět reconciliovat pending/planned decisions ze staré session.

## Historická rozhodnutí

Původní ADR z 2026-09-24 jsou zachována v Git historii. Část principů zůstává platná:
- modularita;
- dokumentace jako součást změny;
- zákaz vševědoucnosti;
- čeština interní dokumentace.

Jejich původní předpoklad, že Alua běží uvnitř Luanti, je nahrazen ADR-A001 a ADR-A002.
