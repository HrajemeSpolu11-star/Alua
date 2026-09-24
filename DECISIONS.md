# Architektonická rozhodnutí

## ADR-001 – Alua sama je AI

**Stav:** přijato  
**Datum:** 2026-09-24

Základní inteligence vzniká uvnitř projektu Alua. Externí LLM nebo vzdálená AI služba nejsou nutné pro autonomní chování.

## ADR-002 – Mineclonia zůstává základním světem

**Stav:** přijato  
**Datum:** 2026-09-24

Necháváme Mineclonii jako základ hry a generátoru mapy. Měnit budeme pouze vybraná pravidla přes samostatné moduly.

## ADR-003 – Modulární architektura

**Stav:** přijato  
**Datum:** 2026-09-24

Nové schopnosti jsou samostatné moduly s jasnými hranicemi. Jádro poskytuje registraci, event bus a perzistentní stav.

## ADR-004 – Dokumentace je součást změny

**Stav:** přijato  
**Datum:** 2026-09-24

Přijaté změny vize, roadmapy a významného chování se zapisují do repozitáře. Chat není autoritativní dokumentace.

## ADR-005 – AI nesmí znát úplnou pravdu enginu

**Stav:** přijato  
**Datum:** 2026-09-24

Kognitivní část Alua nesmí mít přímý neomezený přístup ke kompletnímu stavu Luanti/Mineclonie. Informace procházejí přes world adapter a omezenou vjemovou vrstvu.

Důvod: cílem je agent, který svět poznává a učí se, ne skript s vševědoucím API.

## ADR-006 – Interní dokumentace je v češtině

**Stav:** přijato  
**Datum:** 2026-09-24

Veškerá interní projektová dokumentace se vede česky. Angličtina zůstává vhodná pro kódová API, technické identifikátory a veřejná mezinárodní metadata.
