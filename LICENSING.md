# Licenční strategie projektu Alua

## Stav k 24. 9. 2026

Současný repozitář Alua je zveřejněn pod licencí **MIT**. Přesné znění je v souboru `LICENSE`.

To znamená, že již zveřejněné verze Alua lze používat podle podmínek MIT. Případná budoucí změna licence se týká pouze verzí a částí, ke kterým máme potřebná práva; nemění zpětně podmínky kopií, které už byly vydané pod MIT.

## Základní pravidlo

Licenční čistota je součást architektury projektu.

Cíl je dlouhodobě zachovat možnost:
- používat Mineclonii jako testovací prostředí,
- přenést naše systémy do vlastní hry,
- oddělit náš kód a obsah od cizího kódu a médií,
- případně později zvolit jiný licenční model pro nové verze nebo samostatnou hru.

## Luanti

Luanti je engine, který používáme jako technologický základ.

Aktuální zdrojový kód Luanti používá licenci **LGPL-2.1-or-later**.

Pravidlo projektu:
- Luanti nepovažujeme za náš kód,
- jeho licenci a oznámení zachováváme,
- pokud někdy budeme distribuovat vlastní sestavení enginu, před vydáním provedeme samostatný licenční audit.

## Mineclonia

Mineclonia je pro Alua **testovací herní prostředí**, ne náš budoucí vlastní světový obsah.

Zdrojový kód Mineclonie je obecně zveřejněn pod **GPLv3 nebo novější**, přičemž jednotlivé moduly nebo média mohou mít vlastní nebo duální licenci.

Pravidlo projektu:
- nekopírovat zdrojový kód Mineclonie do Alua bez předchozího licenčního posouzení,
- nekopírovat textury, zvuky, modely ani jiné assety bez ověření konkrétní licence,
- preferovat veřejná API, callbacky, názvy uzlů/předmětů a kompatibilitní adaptéry,
- každý převzatý externí soubor nebo významnější úryvek musí být zapsán v `THIRD_PARTY_LICENSES.md`,
- před distribucí kombinovaného balíčku znovu zkontrolovat kompatibilitu licencí.

## ContentDB

ContentDB vyžaduje pro zveřejněné balíčky svobodnou/open-source licenci umožňující distribuci a úpravy.

Proto:
- během distribuce přes ContentDB nepoužíváme vlastní uzavřenou licenci,
- nevymýšlíme vlastní právní text licence bez odborné právní kontroly,
- metadata v `.cdb.json` musí odpovídat skutečnému souboru `LICENSE`.

## Naše vlastní hra v budoucnu

Pokud se Alua později oddělí od Mineclonie do vlastní hry na Luanti, mají být naše systémy přenositelné bez nutnosti kopírovat Mineclonia obsah.

Pro vlastní hru chceme postupně vytvořit:
- vlastní bloky a předměty,
- vlastní textury a modely,
- vlastní zvuky,
- vlastní herní mechaniky,
- vlastní příběh a postavy,
- vlastní world/game obsah.

Před komerčním nebo samostatným vydáním se vytvoří přesná licenční matice všech komponent.

## Budoucí licence Alua

Dlouhodobý licenční model zatím není definitivně uzavřen.

Možnosti, které lze později vyhodnotit:
- zachovat MIT,
- přejít pro nové verze na copyleft licenci, například GPLv3 nebo AGPLv3,
- oddělit otevřené technologické jádro a vlastní herní obsah,
- případně použít více licencí pro různé části, pokud to bude právně a technicky čisté.

Změna licence je zásadní projektové rozhodnutí a musí být:
1. výslovně schválena vlastníkem projektu,
2. zapsána do `DECISIONS.md`,
3. promítnuta do `LICENSE`, `.cdb.json`, dokumentace a release poznámek,
4. provedena pouze u obsahu, ke kterému máme potřebná práva.

## Externí příspěvky

Než projekt začne přijímat větší cizí code contributions, musí být znovu vyhodnoceno, zda současná pravidla příspěvků zachovávají možnost budoucího relicencování.

Do té doby musí být u každého významného externího příspěvku jasný původ a licence.

## Upozornění

Tento dokument je interní licenční politika projektu, nikoli právní stanovisko. Před komerčním vydáním nebo zásadní změnou licenčního modelu je vhodná odborná právní kontrola.
