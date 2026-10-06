# Vnímání vlastního těla a volba efektoru

Aktualizováno 2026-10-06.

## Vrozená tělesná orientace

Alua smí vědět, že její vlastní tělo má hlavu, trup, dvě ruce a dvě chodidla. Není to hotová znalost světa, ale proprioceptivní rozhraní těla dodané AluaWorld v bezpečném kanálu `body_schema`.

Kanál poskytuje přítomnost částí, jejich relativní polohu, funkční signály, kontakt, obsazenost a zatížení rukou. Neobsahuje technický název nodu, materiál, biome ani absolutní mapovou polohu.

## Volba ruky

Policy smí pro bezpečný `touch` vybrat pouze ruku, která:

- je přítomná;
- má `touch_signal`;
- není podle posledního vjemu obsazená.

Výchozí pořadí je pravá, potom levá. Vybraná ruka se odešle jako `parameters.effector`. Pokud starší World `body_schema` neposkytne, policy zachová kompatibilní action bez efektoru a výběr provede World.

Alua nepředpokládá, že action uspěla. Bridge ACK zůstává pouze potvrzení transportu. Skutečný kontakt nebo změna obsazenosti ruky se musí objevit až v některé budoucí observation.

## Hranice

- Alua vybírá ze smyslově dostupných efektorů;
- Bridge hodnotu pouze přenese;
- World ověřuje existenci ruky, fyzický dosah, sílu, obsazenost a následek;
- admin auditní pozice rukou Alua nikdy nečte.

Autonomní pickup, push a break zůstávají vypnuté, dokud nebude hotový risk/utility model. Tato změna pouze zajišťuje, že i nedestruktivní zkoumání probíhá skutečnou rukou.
