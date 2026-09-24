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

## Fáze 1 – Modulární kostra

Stav: **architektonická větev hotová, čeká na pozdější začlenění**

- [x] registr modulů se závislostmi
- [x] event bus
- [x] verzovaný persistentní stav
- [x] konfigurace/feature flags
- [x] scheduler
- [x] oddělit world a AI
- [x] založit world adapter
- [x] založit domény population/economy/society/story/debug
- [x] definovat úrovně simulace populace
- [x] dokumentovat rozhraní a zakázané závislosti
- [ ] převést současný `npc.lua` po ověření na telefonu
- [ ] převést současné příkazy do nových rozhraní
- [ ] přidat kompatibilitní kontroly Mineclonie

## Fáze 2 – Dvě testovací NPC

Stav: **plán po schválení/instalaci**

- [ ] příkaz pro vytvoření dvou testovacích NPC před hráčem
- [ ] samostatná identita každého NPC
- [ ] oddělená paměť
- [ ] debug inspector pro hráče/testera
- [ ] měření výkonu telefonu
- [ ] reportovací scénáře

## Fáze 3 – Vnímání, paměť a naučený model světa

- [ ] první omezené senzory
- [ ] dohled, dosah a zakrytí
- [ ] reprezentace neznámých objektů
- [ ] nejistota
- [ ] pracovní paměť
- [ ] epizodická paměť
- [ ] naučený model objektů, míst a následků
- [ ] oddělení debug dat od AI

## Fáze 4 – Potřeby, cíle a plánování

- [ ] potřeby
- [ ] utility
- [ ] výběr cíle
- [ ] registr akcí
- [ ] vícekrokové plánování
- [ ] přeplánování po neúspěchu
- [ ] vysvětlitelná stopa rozhodnutí

## Fáze 5 – Materiální a fyzikální svět

- [x] návrh obecného systému materiálů
- [ ] registr skutečných materiálů
- [ ] hustota, objem a odvozená hmotnost
- [ ] mechanické vlastnosti
- [ ] teplota a hoření
- [ ] voda, vlhkost a vztlak
- [ ] koroze a opotřebení
- [ ] složené předměty
- [ ] zatížení inventáře
- [ ] obecné zpracování a kombinace materiálů

## Fáze 6 – Živá populace

- [x] návrh čtyř úrovní simulace
- [ ] životní cyklus NPC
- [ ] věk
- [ ] rozmnožování
- [ ] rodiny/domácnosti
- [ ] migrace
- [ ] práce a role
- [ ] aktivace a uspávání vzdálených NPC

## Fáze 7 – Ekonomika a společnost

- [ ] vlastnictví
- [ ] zásoby
- [ ] výroba a spotřeba
- [ ] obchod
- [ ] ceny podle nabídky/poptávky
- [ ] vztahy
- [ ] reputace
- [ ] frakce a osady

## Fáze 8 – Příběh a kampaň

- [ ] systém událostí
- [ ] questy
- [ ] kapitoly kampaně
- [ ] podmíněné větvení
- [ ] propojení příběhu s živou simulací bez přímého ovládání AI

## Fáze 9 – Učení a adaptace

- [ ] sledování výsledků akcí
- [ ] učení vztahů objekt–akce–výsledek
- [ ] revize chybných přesvědčení
- [ ] bezpečnostní limity adaptace
- [ ] reset naučených dat

## Fáze 10 – Stabilita

Průběžně:
- [ ] výkonové limity
- [ ] migrace save
- [ ] regresní testy
- [ ] kompatibilita Mineclonia
- [ ] release checklist
