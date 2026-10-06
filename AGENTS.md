# Pravidla pro práci na Alua AI

Před jakoukoli významnou změnou přečíst:
1. docs/PAMET_PRO_NOVY_CHAT.md
2. docs/PROJECT_VISION_AI.md
3. docs/BRIDGE_CONTRACT.md
4. docs/ARCHITECTURE.md
5. docs/SECURITY_AND_DATA_POLICY.md
6. nejnovější část CHANGELOG.md
7. dokument příslušné domény.

Povinné zásady:
- Alua AI nikdy nevolá Luanti nebo AluaWorld API přímo.
- Jediná runtime cesta do světa je Agent API AluaBridge.
- Nepřidávat do kognice world truth jen proto, že by zjednodušila implementaci.
- Nepřevádět appearance_id nebo target_ref na skrytý význam mimo naučenou paměť.
- target_ref se nesmí ukládat jako dlouhodobá identita objektu.
- ACK transportu se nesmí zapisovat jako úspěch fyzické akce.
- Každé přesvědčení musí být opravitelné další zkušeností.
- Jeden agent nesmí číst databázi jiného agenta.
- Tajné tokeny nepatří do repozitáře ani logů.
- Nová schopnost musí mít vlastníka, API, persistenci, test a dokumentaci.
- Starý Lua companion kód se nerozšiřuje jako hlavní AI.

Před zápisem změny:
- spustit dostupné unit testy;
- spustit integrační test s falešným Bridge serverem;
- ověřit, že cognition neimportuje transportní tajemství ani world adapter;
- zkontrolovat migrace databáze;
- aktualizovat CHANGELOG.md;
- při změně architektury aktualizovat docs/DECISIONS.md a docs/PAMET_PRO_NOVY_CHAT.md.

Preferovat jeden ucelený commit místo série drobných mezikroků.
