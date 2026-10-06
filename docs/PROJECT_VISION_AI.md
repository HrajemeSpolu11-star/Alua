# Projektová vize Alua AI

## Hlavní cíl

Alua má být autonomní inteligence, která žije uvnitř fyzického světa AluaWorld, ale její mozek je samostatný proces a samostatný repozitář.

Nemá být skript, který zná mapu. Nemá být obal kolem vševědoucího LLM. Nemá dostat hotové recepty, názvy materiálů ani seznam správných rozhodnutí.

Má dostávat omezené vjemy svého těla, pamatovat si zkušenosti, vytvářet si vlastní přesvědčení, zkoušet akce, pozorovat následky a podle zkušenosti měnit budoucí chování.

## Tři oddělené autority

### AluaWorld

Jediný vlastník:
- fyzického světa;
- těl;
- skutečné polohy;
- materiálů a katalogů;
- fyziky;
- smyslového původu signálu;
- metabolismu těla;
- skutečného provedení akcí;
- smrti, zranění a dalších fyzických následků.

### AluaBridge

Jediný vlastník:
- transportní session;
- autentizace;
- bounded front;
- pořadových čísel;
- krátkodobých target_ref;
- lease a ACK;
- transportní idempotence;
- bezpečnostního auditu hranice.

### Alua AI

Jediný vlastník:
- interpretace vjemů;
- pracovní paměti;
- dlouhodobé epizodické paměti;
- přesvědčení a hypotéz;
- naučeného world modelu;
- preferencí;
- cílů;
- plánování;
- rozhodování;
- učení;
- vysvětlitelné stopy kognice.

## Co Alua smí mít vrozené

Minimální infrastrukturu nutnou k tomu, aby vůbec mohla existovat:
- přijmout observation;
- rozlišit časové pořadí;
- uložit zkušenost;
- provést jednu z povolených primitivních akcí;
- rozlišit vlastní interní stav od externího vjemu;
- pracovat s nejistotou;
- chránit konzistenci své paměti;
- základní mechanismus explorace.

Vrozená infrastruktura není znalost světa.

## Co Alua nesmí dostat hotové

- technické názvy nodů a itemů;
- materiálové identity;
- biome;
- katalogové ID;
- absolutní mapu;
- recepty;
- seznam nepřátel;
- seznam jedlých věcí;
- nejlepší nástroje;
- ideální trasy;
- skryté statistiky objektů;
- výsledek akce, který nebyl pozorován smysly.

## Učení místo tabulek pravdy

Alua může například zjistit:
1. vidím opakující se vzhledový podpis;
2. pokusím se s ním manipulovat;
3. pozoruji odpor nebo změnu;
4. po opakovaných zkušenostech vznikne hypotéza;
5. confidence hypotézy roste nebo klesá;
6. nová zkušenost může staré přesvědčení opravit.

Nikdy nevznikne přímá zkratka appearance_id -> strom -> dřevo -> nástroj bez zkušenosti.

## Dlouhodobý cíl

Po jedné stabilní Alua:
- více nezávislých Alua;
- oddělené paměti a zkušenosti;
- komunikace pouze fyzickými nebo světovými kanály;
- sociální učení;
- spolupráce a konflikty;
- technologie vznikající zkušeností;
- reprodukce a dědičnost až po samostatném biologickém kontraktu;
- populace schopná dlouhodobě existovat bez lidského řízení.

## Měřítko úspěchu

Projekt není úspěšný tím, že agent umí předem napsaný úkol.

Úspěch je, když neznámou situaci dokáže:
- vnímat;
- zapamatovat;
- vytvořit hypotézu;
- zvolit bezpečný pokus;
- vyhodnotit pozdější následek;
- upravit přesvědčení;
- použít zkušenost v nové situaci.
