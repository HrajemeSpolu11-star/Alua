# Vize Alua

## Hlavní směr

Alua je autonomní inteligence existující přímo uvnitř světa Luanti. Není to pouhý klient externí AI služby. Inteligence musí vznikat uvnitř projektu samotného.

## Co má Alua umět

Alua má postupně dokázat:

- vnímat okolí přes omezené smyslové vstupy
- pamatovat si zkušenosti
- vytvářet si vlastní model světa
- mít potřeby a vnitřní stav
- vytvářet a měnit cíle
- plánovat více kroků dopředu
- provádět akce stejnými pravidly jako ostatní entity
- vyhodnocovat následky
- měnit budoucí chování podle zkušeností

## Nepřekročitelná pravidla

1. **Alua sama je AI.** Externí LLM nebo vzdálená AI služba nejsou podmínkou základního fungování.
2. **Modularita má přednost.** Nové schopnosti musí jít přidávat bez přepisování nesouvisejících částí.
3. **Stabilní rozhraní.** Moduly spolu komunikují přes popsaná API, události a sdílený kontext.
4. **Žádné magické zkratky.** Pokud Alua něco potřebuje, nemá to dostat bez příčiny přímo z enginu.
5. **Žádná vševědoucnost.** Alua nesmí dostávat kompletní pravdu o světě přímo z enginu.
6. **Svět se má učit.** Význam předmětů, nebezpečí, užitečnost materiálů, trasy a účinky akcí se mají pokud možno získávat zkušeností.
7. **Rozhodování musí být pozorovatelné.** Musíme být schopni zjistit, co Alua vnímala, co si myslela a proč zvolila danou akci.
8. **Bezpečné ukládání.** Perzistentní data musí být verzovaná a migrovatelná.
9. **Mineclonia zůstává základním světem.** Generátor mapy nepředěláváme; měnit můžeme vybraná pravidla fyziky, předmětů a prostředí.
10. **Dokumentace je součást implementace.** Přijatá změna vize nebo chování musí být zapsána v repozitáři.
11. **Interní dokumentace je česky.**

## Co smí Alua vědět na začátku

Úplně prázdná entita by nebyla schopná vůbec jednat. Alua proto může mít pouze minimální vrozenou infrastrukturu:

- jak přijmout smyslový vstup
- jak provést primitivní akci
- jak ukládat paměť
- jak vnímat vlastní vnitřní stav
- základní časovou návaznost
- technická omezení nutná pro stabilitu simulace

To ale není totéž jako znalost světa.

Příklad: Alua může vnímat neznámý objekt před sebou, ale nemá automaticky vědět, že je to strom, že z něj získá dřevo a k čemu je dřevo dobré.

## Dlouhodobé skupiny schopností

- vnímání
- pracovní a dlouhodobá paměť
- naučený model světa
- potřeby a vnitřní stav
- cíle
- plánování a rozhodování
- akce a dovednosti
- inventář a práce s předměty
- sociální interakce
- učení a adaptace
- diagnostika a ladění
- modulární úpravy pravidel světa

## Co zatím není cílem

- nahrazení generátoru mapy Mineclonie
- povinné napojení na externí AI API
- přímý přístup AI k úplnému stavu světa
- automatické převádění technických ID objektů na hotové významy
- velké nevratné zásahy do světa bez migračního plánu
