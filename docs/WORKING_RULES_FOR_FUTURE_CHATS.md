# Pravidla práce pro každý další chat

## Povinný kontext

Před změnou Alua AI přečíst:
1. docs/PAMET_PRO_NOVY_CHAT.md;
2. docs/PROJECT_VISION_AI.md;
3. docs/BRIDGE_CONTRACT.md;
4. docs/ARCHITECTURE.md;
5. docs/SECURITY_AND_DATA_POLICY.md;
6. nejnovější CHANGELOG.md;
7. dokument měněné domény.

Pokud se mění Bridge schema, ověřit také aktuální dokumentaci repozitáře AluaBridge.

Pokud se mění význam smyslu nebo těla, ověřit AluaWorld docs/AGENT_WORLD_CONTRACT.md.

## Local-first

Stejně jako AluaWorld:
- GitHub použít k získání aktuálního zdroje;
- další editace a testy dělat v jedné pracovní kopii, pokud je dostupná;
- nečíst opakovaně stejné soubory;
- změny seskupovat;
- na GitHub zapisovat ucelenou ověřenou změnu;
- před update main ověřit HEAD;
- po zápisu ověřit CI.

## Historie

- CHANGELOG se doplňuje;
- zásadní rozhodnutí se přidává do docs/DECISIONS.md;
- aktuální stav se přepisuje v docs/PAMET_PRO_NOVY_CHAT.md;
- implementační průběh se zapisuje do docs/IMPLEMENTATION_LOG_AI.md;
- staré rozhodnutí se nemaže bez vysvětlení; novější ADR jej může nahradit.

## Před novým modulem určit

- jediného vlastníka;
- vstupní data;
- výstup;
- persistence;
- epistemickou úroveň dat;
- chování po restartu;
- výkonový limit;
- test;
- failure mode;
- dokumentaci.

## Zakázané zkratky

- přímý Luanti přístup;
- World API z Alua;
- načtení katalogu AluaWorld;
- ruční slovník appearance_id -> význam;
- učení fyziky z HTTP error kódu;
- společná paměť všech agentů bez explicitního rozhodnutí;
- schování velké heuristiky do jednoho controller souboru bez dokumentovaného modulu.

## Povinná definice hotovo

Změna je hotová, když:
- kód běží;
- test prochází;
- persistence je řešená;
- hranice dat je jasná;
- dokumentace odpovídá;
- rollback nebo migrace je známá.
