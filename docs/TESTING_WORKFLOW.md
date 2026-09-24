# Testovací pracovní postup

## Cíl první laboratoře

Po schválení a instalaci budeme testovat nejprve dvě NPC přímo před hráčem.

Každé NPC bude mít:
- vlastní identitu
- vlastní paměť
- vlastní vnitřní stav
- samostatné rozhodování
- stejnou modulární kostru

## Role

### Hráč/tester
Pozoruje svět na telefonu a reportuje:
- co NPC udělalo
- co mělo podle situace k dispozici
- kde se zaseklo
- co působilo nelogicky
- zda se chování opakuje
- výkon telefonu

### Vývoj
Podle reportu se mění pouze odpovědný modul, ne celý systém.

## Diagnostika

Debug nástroje mohou ukazovat například:
- poslední vjemy
- pracovní paměť
- potřeby
- vybraný cíl
- plán
- aktuální akci
- důvod selhání

Tato data jsou pro člověka. NPC je nesmí používat jako další senzor.
