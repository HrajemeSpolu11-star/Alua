# Architektonická rozhodnutí Alua AI

## ADR-A001 – Alua je samostatný kognitivní proces
Přijato 2026-10-06. Alua neběží jako Luanti mod.

## ADR-A002 – Jediné runtime rozhraní je AluaBridge Agent API
Přijato 2026-10-06. Přímý World/Luanti přístup je zakázán.

## ADR-A003 – Python pro nový runtime
Přijato 2026-10-06. V1 používá Python 3.12+.

## ADR-A004 – SQLite vlastní kognitivní paměť
Přijato 2026-10-06. Bridge SQLite není paměť Alua.

## ADR-A005 – Jeden agent na jeden proces ve V1
Přijato 2026-10-06. Každá Alua má vlastní proces, token a DB.

## ADR-A006 – Žádný povinný LLM
Přijato 2026-10-06. Základní autonomie musí fungovat bez cloud LLM.

## ADR-A007 – Beliefs jsou evidence-based a opravitelné
Přijato 2026-10-06. Empirická znalost není absolutní fakt bez evidence.

## ADR-A008 – target_ref není dlouhodobá identita
Přijato 2026-10-06. target_ref patří pouze do krátkodobého kontextu.

## ADR-A009 – ACK není outcome
Přijato 2026-10-06. Transportní přijetí akce nesmí přímo změnit world belief.

## ADR-A010 – Starý Lua companion se zatím zachovává
Přijato 2026-10-06. Historický prototyp zůstává, nový runtime na něm nezávisí.

## ADR-A011 – agent_id je dlouhodobá identita Alua
Přijato 2026-10-06. Restart procesu, Bridge ani Worldu sám nevytváří novou osobnost.

## ADR-A012 – změna session invaliduje ephemeral stav
Přijato 2026-10-06. Nový session_id resetuje krátkodobý World kontext, ne dlouhodobé epizody a beliefs.

## ADR-A013 – aktivní explorace začíná nedestruktivně
Přijato 2026-10-06.

Po definici autoritativního move/look kontraktu smí Alua autonomně použít move a look. Manipulace V1 používá pouze touch. Pickup, push a break čekají na naučený risk/utility model.

## ADR-A014 – outcome se koreluje Bridge action sequence
Přijato 2026-10-06.

Decision ukládá Bridge action_sequence. World ji vrací pouze jako omezený motorický source_sequence. Belief update vzniká až po budoucí observation, ne z HTTP ACK.

## ADR-A015 – kognitivní SQLite schema v2 migruje se zálohou
Přijato 2026-10-06.

Před upgrade schema v1 se vytvoří SQLite backup. Session transition invaliduje nedokončené World-specific decisions a expectations, ale nemaže epizody ani beliefs.

## Historická rozhodnutí

Původní ADR z 2026-09-24 jsou zachována v Git historii. Jejich předpoklad, že Alua běží uvnitř Luanti, je nahrazen ADR-A001 a ADR-A002.
