# Zdroje a provenance

Tento soubor slouží jako evidence zdrojů použitých při návrhu, kompatibilitě a licenční kontrole projektu.

Nejde o náhradu `THIRD_PARTY_LICENSES.md`. Pokud skutečně převezmeme kód nebo médium, musí být zapsáno především tam.

## Oficiální technologické zdroje

### Luanti
- Oficiální repozitář: https://github.com/luanti-org/luanti
- Účel: engine API, kompatibilita, informace o licenci
- Licence enginu: LGPL-2.1-or-later

### Mineclonia
- Projekt/repozitář používaný jako testovací prostředí
- Účel: kompatibilita modu a testování ve světě Mineclonie
- Hlavní zdrojový kód: GPLv3-or-later
- Poznámka: konkrétní moduly a média mohou mít odlišné licence; vždy se kontroluje konkrétní soubor.

### ContentDB
- https://content.luanti.org/
- Účel: distribuce Alua pro Luanti
- Poznámka: ContentDB vyžaduje povolenou svobodnou/open-source licenci.

## Pravidlo

Pokud při vývoji použijeme externí článek, dokumentaci, repozitář nebo asset jako přímý podklad pro implementaci, zaznamenáme zdroj zde. Pokud z něj také převezmeme kód nebo médium, musí být současně zapsán v `THIRD_PARTY_LICENSES.md`.
