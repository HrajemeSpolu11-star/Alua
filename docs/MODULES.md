# Moduly projektu Alua

## Účel

Projekt zůstává v jednom repozitáři a jednom Luanti modu, ale vnitřně je rozdělen na samostatné domény. Tím nezměníme typ balíčku v ContentDB a přitom získáme skutečné architektonické hranice.

## Domény

### core
Technické služby bez znalosti herního světa:
- registr modulů a závislostí
- event bus
- perzistentní stav
- konfigurace
- scheduler

### world
Autoritativní pravidla simulace:
- adapter mezi enginem a ostatními systémy
- materiály
- fyzika
- předměty
- prostředí
- kompatibilita Mineclonie

### ai
Kognice jednotlivého agenta:
- perception
- memory
- world model
- needs
- goals
- planning
- actions
- learning

AI nesmí číst interní stav world vrstvy přímo.

### population
Životní cyklus populace:
- existence NPC
- aktivace/deaktivace
- úrovně simulace
- později věk, rozmnožování, migrace a domácnosti

Populace není totéž co AI. Vzdálené NPC může být simulované bez plné kognice.

### economy
Zásoby, výroba, spotřeba, obchod, vlastnictví a ceny.

### society
Vztahy, rodiny, reputace, frakce, role a osady.

### story
Příběhové události, questy a kampaň. Story vrstva nesmí přímo přepisovat myšlenky AI; má používat veřejná rozhraní a události.

### debug
Nástroje pro nás jako vývojáře. Debug smí vidět více než AI, ale debug data nesmí protékat do rozhodování agentů.

## Zakázané zkratky

- AI nesmí volat libovolné Luanti API pro získání úplné pravdy o světě.
- Story nesmí přímo zapisovat do soukromé paměti agenta.
- Economy nesmí řídit fyziku.
- Population nesmí předpokládat, že každé NPC má plnou AI.
- Debug nesmí být zdrojem znalostí pro AI.
- World nesmí obsahovat rozhodovací logiku konkrétního agenta.

## Přechod ze současné verze

Současné `npc.lua` a `commands.lua` jsou dočasná kompatibilní vrstva. Budou se rozdělovat po částech až po funkčních testech na telefonu.
