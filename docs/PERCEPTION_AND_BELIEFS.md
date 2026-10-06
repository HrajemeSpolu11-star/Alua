# Vnímání, neznalost a přesvědčení

## Základní pravidlo

Alua nesmí zaměnit vjem za pravdu světa.

Observation je to, co tělo za daných podmínek zaznamenalo. Může být neúplná, zastaralá, šumová nebo lokální.

## Tři vrstvy

### Percept

Krátkodobá interní reprezentace jednoho bezpečného signálu.

Příklad:
- přede mnou je vizuální vzor P;
- je relativně blízko;
- blokuje pohyb;
- existuje krátkodobý target_ref.

### Hypotéza

Opravitelné tvrzení vytvořené zkušeností.

Příklad:
- vzor P často reaguje podobně na dotyk;
- pokus o zvednutí P opakovaně selhává;
- poblíž P se často objevuje jiný vjem.

### Přesvědčení

Hypotéza s dostatečnou evidencí, ale stále ne absolutní world truth.

Každé přesvědčení nese:
- vlastní ID;
- typ tvrzení;
- subject signature;
- relation;
- object/value;
- confidence;
- počet podpůrných evidencí;
- počet rozporů;
- created_at;
- updated_at;
- odkazy na epizody.

## appearance_id

appearance_id smí sloužit jako stabilní perceptuální podpis pouze v rozsahu, který garantuje kontrakt World/Bridge.

Alua nesmí automaticky tvrdit:
- že dva stejné appearance_id jsou tentýž fyzický objekt;
- že appearance_id je materiál;
- že appearance_id je druh známý z kódu.

Může tvrdit:
- tento vizuální vzor jsem už dříve zažila;
- zkušenosti s tímto vzorem mají určitou statistiku.

## target_ref

target_ref:
- je krátkodobý;
- váže se na jednoho agenta;
- může expirovat;
- nesmí být uložen jako dlouhodobá identita;
- může být dočasně uložen ve working memory pro okamžitou akci.

## Absolutní jistota

V1 se absolutní confidence nepoužívá pro empirická tvrzení.

Pouze interní technické invarianty programu mohou být jisté, například:
- schema_version observation byla validní;
- tato epizoda má lokální ID.

World znalost musí zůstat opravovatelná.

## Negativní evidence

Nepozorování není automaticky důkaz neexistence.

Například:
- neviděla jsem objekt neznamená objekt neexistuje;
- akce bez viditelného následku neznamená jistě nulový účinek.

## Zapomínání a zastarávání

Některá přesvědčení musí stárnout:
- lokální poloha;
- přítomnost pohybujícího se objektu;
- aktuální nebezpečí.

Jiná mohou být dlouhodobá:
- opakovaně naučený vztah perceptuálního vzoru a následku akce.

Typ belief určuje decay politiku.

## Diagnostická hranice

Vývojář může vidět interní databázi Alua a rozhodovací stopu.

Diagnostika ale nesmí přidat do belief store informaci, kterou Alua sama nevnímala nebo neodvodila definovaným učením.
