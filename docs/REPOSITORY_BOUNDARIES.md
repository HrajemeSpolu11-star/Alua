# Hranice repozitářů

## Alua

Vlastní:
- kognitivní runtime;
- konfiguraci agenta;
- kognitivní persistence;
- paměť;
- beliefs;
- cíle;
- planner;
- learning;
- decision trace;
- Agent API klienta.

Nevlastní:
- Luanti entity;
- fyziku;
- mapu;
- material catalog;
- world sensors;
- spawn těla;
- provedení manipulace;
- admin UI světa.

## AluaBridge

Vlastní:
- bezpečný transport;
- session;
- authentication;
- action/observation fronty;
- target_ref;
- lease a ACK;
- idempotence transportu;
- audit transportní hranice.

Nevlastní:
- kognitivní paměť;
- goals;
- planner;
- reward;
- world physics.

## AluaWorld

Vlastní:
- svět;
- Luanti runtime;
- těla;
- smysly;
- fyziku;
- environment;
- manipulaci;
- metabolismus;
- objektivní world truth;
- lidské administrátorské nástroje.

## Historický Lua kód v Alua

init.lua, npc.lua, commands.lua a core/ jsou historický prototyp z doby před oddělením tří repozitářů.

Do dokončení migrace:
- nemažou se bez samostatného rozhodnutí;
- nepoužívají se jako nový kognitivní základ;
- nesmí být závislostí nového Python runtime;
- jejich funkce se posuzují pouze jako reference minulého chování.

## Pravidlo jednoho vlastníka

Každé nové pole nebo mechanika musí mít právě jednoho autoritativního vlastníka.

Pokud není jasné, komu patří:
1. nejdřív rozhodnutí zapsat;
2. potom implementovat.

Duplicitní pravda mezi repozitáři je chyba architektury.
