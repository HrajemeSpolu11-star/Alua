# Embodied learning V1

## Účel

Tato vrstva je první okamžik, kdy Alua není jen transportní klient, ale samostatně provádí bezpečný cyklus vnímání, akce a učení.

## Bezpečný rozsah akcí

Autonomní policy V1 používá:
- move podle přesného World kontraktu;
- look podle přesného World kontraktu;
- manipulate/touch pouze na krátkodobý target_ref;
- žádný automatický pickup, push nebo break.

World může mít širší fyzické schopnosti těla. To neznamená, že je mozek musí okamžitě používat.

## Working memory

Posledních 32 PerceptionFrame je pouze v RAM.

Obsahuje mimo jiné krátkodobé target_ref. Při restartu procesu, změně session nebo explicitním clear tyto vazby zaniknou.

## Expectations

Po úspěšném transportním submitu vznikne pending expectation s:
- decision_id;
- session_id;
- Bridge action sequence;
- action type;
- případným appearance signature cíle;
- očištěnou action bez target_ref;
- observation sequence vzniku.

Alua neposílá další aktivní akci, dokud jedna expectation čeká.

## Motor outcome

AluaWorld vydá bezpečný sensory event:
- source_sequence;
- success_signal;
- feedback_signal;
- effort_signal;
- age_fraction.

source_sequence se spáruje s expectation. Teprve potom se provede learning update.

## Beliefs

Binary belief používá prior odpovídající Beta(1,1):

    confidence = (support + 1) / (support + contradiction + 2)

První úspěch proto není absolutní jistota a rozpor confidence snižuje.

## První naučené vztahy

- action:<type>:motor_effect
- appearance:<signature>:touch:effect

Neříkají „tohle je kámen“ nebo „tohle je dřevo“. Ukládají pouze vztah, který agent skutečně zažil.

## Expirace

Pokud motorický výsledek nedorazí, expectation po omezeném počtu observations expiruje.

Expirace není fyzický neúspěch. Znamená pouze nedostatek spolehlivé evidence.

## Skutečný E2E test

Na telefonu se po spuštění všech tří částí používá:

    bash tools/e2e_smoke_termux.sh

Test vyžaduje aktivní World session a po několika cyklech kontroluje, že vznikla observation epizoda, decision a alespoň jeden belief odvozený z budoucího motorického vjemu.
