# Systém materiálů a fyzikálních vlastností

## Cíl

Předměty a bloky nemají být jen seznamem pevně naprogramovaných výjimek. Mají mít obecné vlastnosti, ze kterých se odvozují jejich fyzikální projevy, možné použití a kombinace s jinými materiály.

Tento dokument zatím popisuje návrh. Implementace se provede až po výslovném pokynu.

## Základní princip

Každý objekt může být složen z jednoho nebo více materiálů.

Příklad:

```
dřevěné dveře
├── hlavní materiál: dřevo
├── menší části: kov
└── tvar/funkce: dveře
```

Materiál nese fyzikální vlastnosti. Objekt nese tvar, objem, funkci, stav a složení.

## Navrhované vlastnosti materiálu

### Mechanické
- hustota
- hmotnost odvozená z objemu a hustoty
- tvrdost
- pevnost v tlaku a tahu
- pružnost
- křehkost
- houževnatost
- tření
- odolnost proti nárazu

### Tepelné
- tepelná vodivost
- tepelná kapacita
- teplota
- bod vznícení
- hořlavost
- rychlost hoření
- bod tání
- bod varu

### Prostředí
- nasákavost
- propustnost
- vztlak
- reakce na vodu
- koroze a rezivění
- rozklad
- odolnost proti počasí

### Elektrické a praktické
- elektrická vodivost a odpor
- izolace
- opracovatelnost
- řezatelnost
- štípatelnost
- tavitelnost
- svařitelnost
- lepitelnost
- použitelnost jako palivo

## Odvozené vlastnosti

Pokud lze vlastnost vypočítat, nemá se ručně zapisovat pro každý předmět.

```
hmotnost = objem × hustota
```

Další možné vztahy:

- pádové poškození podle hmotnosti, rychlosti a materiálu
- rychlost hoření podle hořlavosti, vlhkosti a prostředí
- opotřebení podle tvrdosti nástroje a cíle
- vztlak podle průměrné hustoty objektu vůči kapalině
- změna teploty podle tepelné kapacity a okolí

## Skládání materiálů

Objekt může mít více částí. Například meč může mít železnou čepel, dřevěnou rukojeť a spojovací materiál. Výsledné chování pak může vycházet z vlastností jednotlivých částí.

## Kombinace materiálů

Chceme postupně používat obecnější vztahy místo nekonečného seznamu zvláštních pravidel.

Příklady:

- dřevo + řezání -> prkna
- prkna + spojení -> konstrukce
- ruda + teplo -> zpracovaný kov
- vlákno + tkaní -> textilie
- mokrý materiál + čas/teplo -> sušší materiál

Existující recepty Mineclonie mohou zůstat kvůli kompatibilitě.

## Stav konkrétního kusu

Konkrétní předmět může mít vlastní:

- teplotu
- vlhkost
- opotřebení
- poškození
- ostrost
- korozi
- čistotu
- kvalitu

Dva stejné typy předmětu tedy nemusí být ve stejném stavu.

## Napojení na Alua

Alua nesmí dostat materiálové hodnoty jako hotovou znalost.

Engine může vědět, že určitý materiál má vysokou hustotu nebo hořlavost. Kognitivní vrstva Alua má nejprve vnímat pouze projevy: hmotnost, odpor při práci, reakci na oheň, vodu, náraz nebo nástroj.

Zkušenost se pak ukládá do jejího vlastního modelu světa.

## Výkon

Detailní fyzika se nebude počítat stále pro každý blok mapy. Aktivní objekty mohou mít detailní stav, zatímco statické a vzdálené objekty využijí předpočítané nebo zjednodušené chování.

## Kompatibilita

Systém má být vrstva nad Mineclonií, ne masivní přepis jejího kódu. Jednotlivé world moduly musí jít vypnout.

## Stav

Návrh architektury. Není zatím implementováno.
