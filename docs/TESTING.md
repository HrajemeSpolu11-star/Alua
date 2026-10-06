# Testování Alua AI

## Cíl

Testy musí dokazovat nejen funkčnost, ale i epistemickou čistotu.

## Unit testy

### Bridge client
- správná Authorization hlavička;
- token se neobjeví v logu;
- after_sequence navazuje na uloženou hodnotu;
- timeout retry zachová client_action_id;
- změna session vyvolá invalidaci krátkodobého stavu.

### Perception
- neznámá pole se neinterpretují jako fakta;
- appearance_id zůstane neprůhledné;
- target_ref se nedostane do long-term identity;
- pořadí sequence je monotónní.

### Memory
- bounded working memory;
- epizoda přežije restart;
- migration;
- rollback při chybě migrace;
- agent isolation.

### Beliefs
- evidence zvýší confidence;
- contradiction confidence sníží;
- belief lze revidovat;
- nepřítomnost observation není automaticky negativní důkaz.

### Decision
- planner respektuje povolené typy akcí;
- risk budget;
- pevný limit plánování;
- stejné vstupy a seed dávají deterministický výsledek tam, kde je to požadováno.

## Contract test s falešným Bridge

Lokální fake server simuluje:
- session;
- observations;
- 403;
- 409 target_expired;
- 429 queue full;
- timeout po přijetí akce;
- restart session.

Test ověří, že transportní chyba nezmění world belief jako fyzický outcome.

## Replay test

Uložená série observations má jít znovu přehrát do čisté dočasné DB.

Výsledek:
- stejné epizody;
- stejné beliefs pro deterministickou V1;
- stejné rozhodovací stopy s výjimkou explicitně nestabilních časových metadat.

## End-to-end smoke test

Po spojení s AluaBridge:
1. načíst session;
2. přijmout observation;
3. uložit sequence;
4. vybrat bezpečnou akci;
5. odeslat ActionRequest;
6. čekat na další observation;
7. vytvořit epizodu a outcome evidence.

## Negativní testy

- žádný import Luanti;
- žádný AluaWorld source import;
- žádný World token;
- žádný bearer token v DB;
- žádná absolute_position v belief test fixture, pokud by prošla přes Bridge boundary;
- žádný přímý překlad technického world ID.

## Výkonové testy

Měřit:
- čas jednoho kognitivního cyklu;
- RAM po dlouhém běhu;
- růst SQLite;
- čas startu po velké paměti;
- počet planner uzlů;
- počet DB zápisů na observation.

## CI

Před merge:
- syntax/compile;
- unit tests;
- contract tests;
- migration tests;
- static boundary audit;
- git diff --check.

Po vytvoření runtime bude přesný příkazový checklist přidán sem i do AGENTS.md.
