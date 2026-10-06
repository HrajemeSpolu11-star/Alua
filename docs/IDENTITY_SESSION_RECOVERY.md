# Identita, session a recovery Alua AI

## Účel

Tento dokument přesně odděluje dlouhodobou identitu Alua od krátkodobého runtime stavu Bridge a Worldu.

## Identifikátory

### agent_id

Dlouhodobá identita kognitivního agenta.

Příklad:
    alua:1

V1 platí:
- jeden agent_id = jeden AI proces;
- jeden agent_id = jeden Agent token;
- jeden agent_id = jedna kognitivní SQLite DB.

Restart procesu Alua nesmí agent_id změnit.

### session_id

Identita aktuálního World/Bridge runtime kontextu těla.

Session je krátkodobější než osobnost Alua.

Změna session:
- neznamená automaticky novou Alua;
- invaliduje target_ref;
- ruší world-specific krátkodobé předpoklady;
- resetuje observation cursor pro novou session;
- zachovává dlouhodobé epizody a beliefs, pokud nejsou výslovně session-local.

### observation sequence

Monotónní pořadí vjemů uvnitř aktuální session.

Persistuje se poslední bezpečně zpracovaná sequence.

### decision_id

Deterministické ID kognitivního rozhodnutí.

V současné V1 je zároveň použito jako client_action_id, takže retry stejného rozhodnutí nevytvoří druhou logickou akci.

### request_id

Transportní ID přidělené AluaBridge.

Není kognitivní identita akce a nesmí být používáno jako význam fyzického výsledku.

### target_ref

Krátkodobý opaque handle pro aktuálně vnímaný cíl.

Nesmí:
- přežít session;
- stát se dlouhodobým object ID;
- být sdílen mezi agenty.

## Typy restartů

### 1. Restart pouze Alua procesu

Očekávání:
- agent_id stejné;
- DB stejná;
- Bridge session může zůstat stejná;
- runtime pokračuje od poslední commitnuté observation sequence;
- již uložené epizody se neduplikují.

### 2. Restart AluaBridge

Pokud World runtime zůstane stejný, konkrétní session semantics určuje Bridge kontrakt.

Alua musí vždy znovu načíst session endpoint a nesmí předpokládat kontinuitu pouze podle lokálního času.

### 3. Restart AluaWorld / nové tělo runtime

Nový session_id znamená:
- zahodit target_ref;
- invalidovat krátkodobé plány navázané na předchozí tělo/runtime;
- neodesílat starou world-specific akci do nové session;
- zachovat dlouhodobou kognitivní historii stejného agent_id;
- zapsat session transition.

### 4. Smrt těla

Semantika zatím není finálně definovaná.

Před implementací musí být výslovně rozhodnuto:
- zda agent_id přežívá smrt těla;
- zda nové tělo znamená novou session stejné osobnosti;
- co z propriocepce a body-specific memory se invaliduje;
- jak se řeší dědictví, potomci a nové identity.

AI repo tuto biologickou politiku nesmí samo vymyslet.

## Recovery pravidla

### Nedostupný Bridge

- zachovat DB;
- exponenciální backoff v omezeném rozsahu;
- nevytvářet nové rozhodnutí bez nového vjemu;
- neodhadovat, co se ve světě stalo.

### 401/403

Fatální konfigurační nebo autorizační chyba.

Runtime nemá nekonečně retryovat s chybným tokenem.

### 409 target_expired

- zrušit konkrétní ephemeral target;
- neoznačit to jako fyzický neúspěch objektu;
- počkat na nový vjem a nový target_ref.

### 429

- respektovat backoff;
- retry stejného client_action_id, pokud jde o stejné logické rozhodnutí;
- nevytvářet paralelně novou kopii téže akce.

### Timeout po odeslání akce

Stav je nejednoznačný.

Správně:
- nepředpokládat, že akce nebyla přijata;
- retry se stejným client_action_id;
- spolehnout se na idempotenci Bridge.

## Atomická hranice zpracování observation

Cílově musí platit:

    observation -> episode/belief update -> cursor commit

jako jedna logická transakce nebo bezpečně replayovatelný postup.

Po pádu nesmí nastat stav, kdy cursor říká „zpracováno“, ale epizoda nebo belief update chybí.

## Co přežívá session

Přežívá:
- agent identity;
- dlouhodobé epizody;
- empirické beliefs s platnou provenance;
- naučené procedury, pokud nejsou vázané na konkrétní target_ref;
- dlouhodobé preference/osobnost.

Nepřežívá bez nové validace:
- target_ref;
- okamžitá poloha neznámého objektu;
- aktivní kontakt;
- krátkodobý pohyb cíle;
- pending action závislá na staré session;
- přesvědčení označená jako session-local.

## Více Alua

V1:
- žádná společná DB;
- žádný společný observation cursor;
- žádný společný token;
- žádné sdílené target_ref.

Přenos znalosti mezi agenty musí v budoucnu probíhat jako pozorovatelná komunikace nebo explicitně schválený mechanismus, ne skrytým databázovým sdílením.
