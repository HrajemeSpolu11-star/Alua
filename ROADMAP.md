# Roadmapa Alua

Tento soubor je hlavní plán projektu.

## Fáze 0 – Funkční základ společníka

Stav: **implementováno / stabilizace**

- [x] spawn společníka
- [x] vlastník
- [x] follow
- [x] stay
- [x] recall
- [x] základní stavový výpis
- [x] diagnostický scan
- [x] jednoduchá perzistentní paměť
- [ ] test přímo v Luanti + Mineclonia na telefonu
- [ ] schválení ContentDB

Poznámka: `/alua_scan` je pouze diagnostika, ne finální smysl AI.

## Fáze 1 – Modulární jádro

Stav: **probíhá**

- [x] definovat architekturu
- [x] registr modulů
- [x] event bus
- [x] verzovaný persistentní stav
- [x] definovat hranici mezi enginem a vnímáním AI
- [ ] převést současný NPC kód do modulů
- [ ] konfigurace a feature flags
- [ ] diagnostika načtených modulů
- [ ] kontroly kompatibility

## Fáze 2 – Vnímání, paměť a naučený model světa

Stav: **plán**

- [ ] world adapter oddělující engine truth
- [ ] omezené smyslové snapshoty
- [ ] dohled, dosah a zakrytí
- [ ] reprezentace neznámých objektů
- [ ] nejistota a confidence
- [ ] pozorování následků vlastních akcí
- [ ] pracovní paměť
- [ ] dlouhodobá epizodická paměť
- [ ] naučené vztahy mezi objekty a materiály
- [ ] naučená místa a trasy
- [ ] oddělit debug senzory od AI senzorů
- [ ] limity a čištění paměti
- [ ] migrace uloženého stavu

Podmínka dokončení: Alua dokáže budovat vlastní omezený model okolí bez přímého přístupu ke kompletní sémantické pravdě enginu.

## Fáze 3 – Potřeby, cíle a rozhodování

- [ ] model potřeb
- [ ] utility scoring
- [ ] výběr cíle
- [ ] arbitráž rozhodnutí
- [ ] přerušení při nebezpečí
- [ ] rozhodování podle vlastních přesvědčení, ne podle engine truth
- [ ] vysvětlitelná stopa rozhodnutí

## Fáze 4 – Plánování a dovednosti

- [ ] registr schopností
- [ ] vícekrokový plánovač
- [ ] pohybové akce
- [ ] práce s předměty
- [ ] inventář
- [ ] objevování a používání craftingu
- [ ] získávání zdrojů
- [ ] bezpečné selhání a přeplánování

## Fáze 5 – Modulární úpravy světa

Generátor mapy zůstává beze změny.

- [x] navrhnout obecný systém materiálových a fyzikálních vlastností
- [ ] registr materiálů
- [ ] skládání objektů z více materiálů
- [ ] hustota, objem a odvozená hmotnost
- [ ] mechanické, tepelné a environmentální vlastnosti
- [ ] stav konkrétního kusu předmětu
- [ ] obecné vztahy pro zpracování a kombinace materiálů
- [ ] hmotnost a zatížení
- [ ] vybraná pravidla pohybu a fyziky
- [ ] pády a nárazy
- [ ] voda a prostředí
- [ ] opotřebení a opravy
- [ ] environmentální stavy
- [ ] kompatibilitní vrstva pro změny Mineclonie

## Fáze 6 – Učení a adaptace

- [ ] sledování výsledků akcí
- [ ] učení vztahů objekt–akce–výsledek
- [ ] učení užitečnosti materiálů a nástrojů
- [ ] úprava preferencí
- [ ] úprava utility podle zkušeností
- [ ] revize chybných přesvědčení
- [ ] bezpečnostní limity adaptace
- [ ] možnost resetu naučených dat

## Fáze 7 – Stabilita a nástroje

Průběžně:

- [ ] výkonové limity
- [ ] migrační framework
- [ ] debug HUD/logging
- [ ] regresní scénáře
- [ ] matice kompatibility Mineclonia
- [ ] release checklist
