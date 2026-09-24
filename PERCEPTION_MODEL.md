# Model vnímání a znalostí

## Účel

Alua má svět poznávat přes řízenou vrstvu vnímání. Engine zná skutečný stav simulace, ale Alua ho nesmí znát celý.

## Tři oddělené vrstvy

### 1. Pravda enginu

Luanti/Mineclonia interně zná například:

- přesná technická ID bloků a entit
- skryté vlastnosti
- vzdálené objekty mimo dohled
- kompletní recepty
- interní metadata
- přesný stav mapy

Tyto informace nesmí být automaticky předány kognitivní vrstvě Alua.

### 2. Vjemová vrstva

Převádí technickou realitu enginu na omezené pozorování.

Příklady:

- překážka je přibližně 2 metry přede mnou
- vlevo se pohybuje neznámý objekt
- po kontaktu s objektem mi kleslo zdraví
- v této kapalině se pohybuji pomaleji
- po použití akce X vznikl předmět Y
- poblíž proběhla slyšitelná událost

Později se přidá dohled, zakrytí, vzdálenost, šum a nejistota.

### 3. Naučený model světa

Alua si ukládá hypotézy a vztahy získané zkušeností:

- typ objektu A často dává materiál B
- akce C je proti objektu D účinnější
- entita E bývá nebezpečná
- cesta F bývá bezpečná
- určitý předmět pomáhá s konkrétní činností

Tyto znalosti mohou být neúplné nebo chybné a musí jít opravit další zkušeností.

## Pravidlo „nejdřív neznámé“

Nové věci začínají jako neznámé, pokud nemáme jasný důvod, proč je Alua má znát.

Nevhodně:

```
mcl_core:tree -> strom -> dřevo -> užitečný materiál
```

Správný směr:

```
neznámý objekt -> pokus/interakce -> výsledek -> zkušenost -> naučený význam
```

Technické ID může adaptér používat interně kvůli stabilnímu sledování objektu, ale samo o sobě nesmí dát Alua jeho význam.

## Diagnostická výjimka

Vývojářské příkazy smějí zobrazit skutečná data enginu, protože je potřebujeme pro ladění. Tato data ale nesmí být použita autonomním rozhodovacím systémem.

Současný příkaz `/alua_scan` je proto **diagnostická pomůcka**, ne finální senzorický systém AI.

## Zdroje znalostí

Do modelu světa se informace mohou dostat například:

- přímým pozorováním
- následkem vlastní akce
- opakovanou zkušeností
- výukou od hráče, pokud ji později přidáme
- odvozením z dříve naučených vztahů

## Co se nemá přednačítat

Ve výchozím stavu nechceme Alua dát hotové:

- crafting recepty
- význam všech materiálů
- seznam nepřátelských mobů
- rozmístění zdrojů
- nejlepší nástroje
- bezpečné trasy
- kompletní fyzikální konstanty světa
- skryté vlastnosti předmětů

## Cíl

Alua si má vlastní použitelný model Mineclonie postupně vybudovat sama.
