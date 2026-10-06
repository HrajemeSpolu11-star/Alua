# Alua AI

Alua je samostatný kognitivní systém pro autonomní agenty žijící v AluaWorld.

Od 2026-10-06 je hlavní architektura projektu změněna: Alua už není Luanti mod a nesmí být přímo napojená na engine. AluaWorld je autoritativní fyzický svět, AluaBridge je bezpečná transportní a epistemická hranice a tento repozitář vlastní pouze kognici.

Tok systému:

    AluaWorld -> AluaBridge -> Alua AI
    Alua AI   -> AluaBridge -> AluaWorld

Alua AI smí přijímat pouze vjemy svého těla, vytvářet si vlastní paměť a přesvědčení a žádat o primitivní akce. Nesmí číst mapu, technické názvy nodů, materiály, biomy, recepty, interní objekty ani administrátorská data.

## Aktuální stav

Hotovo:
- historický Luanti companion prototyp s follow/stay/recall;
- původní modulární Lua základ a verzovaný stav;
- dlouhodobá vize učení bez vševědoucnosti;
- AluaBridge V1 na samostatném repozitáři;
- nový dokumentační základ pro samostatnou Alua AI;
- přesný kontrakt vůči AluaBridge;
- návrh kognitivní architektury, paměti, učení, testování a provozu.

Nehotovo:
- nový Python runtime Alua AI;
- Bridge klient;
- pracovní a dlouhodobá paměť v nové architektuře;
- world model;
- potřeby a cíle;
- plánování a rozhodování;
- učení z následků;
- end-to-end test s jedním tělem v AluaWorld.

Starý Lua kód zůstává zatím v repozitáři jako historický funkční prototyp. Nesmí se dále rozšiřovat jako hlavní mozek.

## Neměnné hranice

1. Alua AI nemá přímou závislost na Luanti.
2. Jediné runtime spojení se světem vede přes Agent API AluaBridge.
3. Bridge nevlastní kognici a Alua nevlastní fyziku světa.
4. Význam neznámých věcí vzniká učením, ne převodem technických ID.
5. target_ref je krátkodobý handle, ne identita objektu.
6. ACK akce není fyzický výsledek; následek se poznává až z budoucích vjemů.
7. Kognitivní paměť musí přežít restart AI a nesmí být uložená v Bridge.
8. Každé naučené tvrzení musí mít evidenci, confidence a možnost opravy.
9. Zásadní změna není hotová bez testu a dokumentace.

## Dokumentace

Nejdůležitější dokument pro nový chat:
- docs/PAMET_PRO_NOVY_CHAT.md

Dále:
- docs/PROJECT_VISION_AI.md
- docs/ARCHITECTURE.md
- docs/BRIDGE_CONTRACT.md
- docs/PERCEPTION_AND_BELIEFS.md
- docs/MEMORY_MODEL.md
- docs/LEARNING_AND_DECISION.md
- docs/REPOSITORY_BOUNDARIES.md
- docs/SECURITY_AND_DATA_POLICY.md
- docs/ROADMAP.md
- docs/TESTING.md
- docs/OPERATIONS_TERMUX.md
- docs/WORKING_RULES_FOR_FUTURE_CHATS.md
- docs/IMPLEMENTATION_LOG_AI.md
- docs/DECISIONS.md
- CHANGELOG.md

## Historický prototyp

Soubory init.lua, npc.lua, commands.lua a core/ pocházejí z období, kdy byla Alua navržena jako Luanti companion mod. Jsou důležité jako historie a referenční prototyp, ale nejsou cílovou architekturou nové Alua AI.

## Licence

MIT.
