# Implementační deník Alua AI

Tento dokument doplňuje changelog. Changelog říká co se změnilo; tento deník zachycuje technický důvod a návaznosti.

## 2026-10-06 – oddělení mozku od světa

Po dokončení AluaBridge V1 byl zkontrolován původní repozitář Alua.

Zjištění:
- aktuální kód je Luanti companion;
- entity přímo čte PlayerRef, pozice a okolní objekty;
- diagnostický scan čte node_name a absolutní pozici;
- modulární core existuje, ale skutečné perception, memory, world model, needs, goals, planner a learning zatím ne;
- původní dokumentace správně požadovala perception boundary, ale technické umístění mozku uvnitř Luanti už neodpovídá nové třírepo architektuře.

Rozhodnutí:
- Alua se mění na externí kognitivní proces;
- Bridge je jediný runtime port do světa;
- původní Lua companion se zachová jako historický prototyp;
- nový runtime bude v Pythonu a bude mít vlastní SQLite kognitivní paměť.

## 2026-10-06 – dokumentační základ

Podle standardu používaného v AluaWorld byly vytvořeny:
- projektová vize;
- architektura;
- Bridge kontrakt;
- perception/belief model;
- memory model;
- learning/decision model;
- repository boundaries;
- security/data policy;
- roadmap;
- testing;
- Termux provoz;
- working rules;
- paměť pro další chat;
- ADR.

Bezprostřední další implementační krok:
- založit nový Python runtime, aniž by se zatím mazal historický Lua prototyp.
