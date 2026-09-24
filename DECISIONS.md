# Architektonická rozhodnutí

## ADR-001 – Alua sama je AI
**Stav:** přijato  
**Datum:** 2026-09-24

Základní inteligence vzniká uvnitř projektu Alua. Externí LLM nebo vzdálená AI služba nejsou nutné pro autonomní chování.

## ADR-002 – Mineclonia zůstává základním světem
**Stav:** přijato  
**Datum:** 2026-09-24

Mineclonia zůstává základní hrou a generátorem mapy. Vybraná pravidla měníme přes vlastní moduly.

## ADR-003 – Modulární architektura
**Stav:** přijato  
**Datum:** 2026-09-24

Nové schopnosti jsou samostatné moduly s jasnými hranicemi.

## ADR-004 – Dokumentace je součást změny
**Stav:** přijato  
**Datum:** 2026-09-24

Přijaté změny vize, roadmapy a významného chování se zapisují do repozitáře.

## ADR-005 – AI nesmí znát úplnou pravdu enginu
**Stav:** přijato  
**Datum:** 2026-09-24

Kognitivní část Alua nesmí mít přímý neomezený přístup ke kompletnímu stavu Luanti/Mineclonie.

## ADR-006 – Interní dokumentace je v češtině
**Stav:** přijato  
**Datum:** 2026-09-24

Interní projektová dokumentace se vede česky.

## ADR-007 – Vlastnosti objektů mají vycházet z materiálů
**Stav:** návrh přijatý k budoucí implementaci  
**Datum:** 2026-09-24

Objekty mají postupně používat obecné materiálové vlastnosti. AI tyto hodnoty nezná přímo.

## ADR-008 – Jeden repozitář, oddělené domény
**Stav:** přijato  
**Datum:** 2026-09-24

Projekt zatím zůstává jedním repozitářem a jedním Luanti modem.

Uvnitř jsou oddělené domény `core`, `world`, `ai`, `population`, `economy`, `society`, `story` a `debug`.

Důvod:
- nezměníme typ současného ContentDB balíčku
- jednodušší instalace na telefonu
- společné verzování a dokumentace
- skutečné hranice lze vynutit rozhraními i bez více repozitářů

Samostatné repozitáře dávají smysl až tehdy, pokud některá doména začne mít vlastní životní cyklus a použití mimo Alua.

## ADR-009 – Populace a AI jsou rozdílné systémy
**Stav:** přijato  
**Datum:** 2026-09-24

NPC může existovat v populační simulaci bez spuštěné plné AI. Detailní kognice se používá hlavně u aktivních NPC poblíž hráče.

## ADR-010 – Story systém neovládá myšlenky NPC
**Stav:** přijato  
**Datum:** 2026-09-24

Kampaň a questy mohou vytvářet situace a události, ale nemají přímo přepisovat soukromou paměť nebo rozhodnutí agenta.
