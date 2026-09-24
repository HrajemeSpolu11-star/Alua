# Evidence licencí třetích stran

Tento soubor eviduje externí software, kód a média, která Alua používá, na kterých běží nebo která mohou ovlivnit distribuci.

## Aktuální stav

| Komponenta | Role | Licence | Je kopírována do Alua? | Poznámka |
|---|---|---|---|---|
| Luanti | engine | LGPL-2.1-or-later | Ne | Runtime/engine základ. Vlastní sestavení enginu vyžaduje před distribucí samostatný audit. |
| Mineclonia | testovací hra/prostředí | GPLv3-or-later pro hlavní zdrojový kód; jednotlivé části mohou mít jiné/duální licence | Ne | Používáme jako testovací prostředí. Kód a assety se do Alua nekopírují bez kontroly konkrétní licence. |

## Externí kód v repozitáři

K 24. 9. 2026 není v tomto seznamu evidován žádný záměrně převzatý zdrojový soubor z Mineclonie nebo jiného cizího modu.

Pokud se to změní, musí být doplněno:
- název komponenty,
- autor,
- přesný zdroj/URL,
- verze nebo commit,
- licence,
- cesta k souboru v Alua,
- zda byl soubor upraven,
- požadované copyright/attribution oznámení,
- poznámka ke kompatibilitě s licencí Alua.

## Média

Každá textura, zvuk, model, font nebo jiné médium musí mít dohledatelný původ.

Doporučený záznam:

```
Soubor:
Autor:
Zdroj:
Licence:
Původní název/verze:
Úpravy:
Použití v projektu:
```

Žádný asset nalezený pouze přes běžné vyhledávání na internetu se nepovažuje automaticky za volně použitelný.

## Pravidlo před přidáním

Před přidáním externího kódu nebo média se nejdříve ověří licence. Teprve potom se soubor přidá do repozitáře.
