# Rozsah úprav světa

## Základní svět

Mineclonia zůstává základní hrou a generátorem mapy. V tuto chvíli nechceme nahrazovat terén, biomy ani celkovou strukturu mapy.

## Co můžeme měnit

Přes samostatné moduly můžeme postupně upravovat:

- vlastnosti a metadata předmětů
- hmotnost a zatížení
- vybraná pravidla pohybu
- pády a nárazy
- interakci s vodou
- opotřebení a opravy nástrojů
- crafting rozšíření
- pravidla používání objektů
- environmentální podmínky
- chování vybraných živých systémů
- nové předměty a mechaniky

## Co nechceme dělat bez výslovného rozhodnutí

- nahrazovat kompletní mapgen Mineclonie
- měnit jedním modulem mnoho nesouvisejících pravidel
- přepisovat interní kód Mineclonie tam, kde lze použít adaptér nebo hook
- dělat nevratné změny save bez migrace
- vázat všechny world moduly na sebe

## Povinnosti každého world modulu

Musí být zdokumentováno:

- co přesně mění
- jestli je změna vratná
- jaká data ukládá
- na čem z Mineclonie závisí
- známé konflikty
- jak modul vypnout

## Změny mapy

Pokud někdy v budoucnu přidáme změnu, která zasahuje do vygenerovaného světa, dokumentace musí přesně uvést, zda působí jen na nové chunky, existující chunky, nebo vyžaduje migraci.
