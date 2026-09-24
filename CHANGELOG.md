# Přehled změn

## Nezveřejněno

### Architektura
- připravena oddělená doménová struktura `core/world/ai/population/economy/society/story/debug`
- registr modulů rozšířen o explicitní závislosti a detekci cyklů
- přidána konfigurace a lehký scheduler
- založen world adapter se samostatnými registry senzorů a akcí
- založen registr materiálů
- definovány čtyři úrovně simulace populace
- přidán diagnostický příkaz `/alua_modules`
- současné `npc.lua` a `commands.lua` ponechány jako kompatibilní vrstva

### Licence a provenance
- zdokumentována současná MIT licence a pravidla případné budoucí změny
- Mineclonia výslovně označena jako testovací prostředí
- přidána evidence třetích stran a externích zdrojů
- přidána evidence AI asistence
- licenční kontrola přidána do povinného checklistu změn

### Dokumentace
- popsány hranice jednotlivých modulů
- popsáno rozhraní mezi světem a AI
- popsány úrovně simulace
- popsán pracovní postup testování dvou NPC
- zaznamenáno rozhodnutí ponechat jeden repo/jeden mod a oddělit domény uvnitř

### Návrh světa
- navržen obecný materiálový systém pro hustotu, hmotnost a fyzikální vlastnosti
- potvrzeno, že AI nesmí dostávat materiálové hodnoty jako hotovou znalost

## 0.2.0 – 2026-09-24

### Přidáno
- trvalý společník navázaný na vlastníka
- follow a stay
- recall
- přepnutí pravým kliknutím
- jednoduchá paměť pozice vlastníka
- stavový a diagnostický scan příkaz
- odstranění společníka a nápověda

## 0.1.0 – 2026-09-24

### Přidáno
- první kostra Luanti modu
- diagnostický příkaz `/alua_test`
- ContentDB metadata a MIT licence
