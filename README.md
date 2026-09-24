# Alua

Alua je experimentální autonomní inteligence pro Luanti, aktuálně testovaná s hrou **Mineclonia**.

Současná verze je už hratelná: hráč může vyvolat jednoho trvalého společníka Alua, přepínat jeho chování, přivolat ho, zobrazit jednoduchou paměť a spustit diagnostický scan.

## Hlavní vize

Alua sama je AI. Projekt nemá být jen obal kolem externího LLM nebo vzdálené AI služby. Inteligence se bude postupně skládat z vlastních modulů pro vnímání, paměť, potřeby, cíle, plánování, akce a učení.

Mineclonia zůstává základním světem. Nechceme předělávat generátor mapy, ale budeme postupně upravovat vybraná pravidla světa: fyziku, předměty, interakce, prostředí a další mechaniky.

## Aktuální funkce

- trvalá entita společníka navázaná na vlastníka
- následování hráče
- režim následovat / čekat
- interakce pravým kliknutím
- přivolání
- jednoduchá perzistentní paměť poslední známé pozice vlastníka
- diagnostický scan okolí
- stavový výpis
- jeden aktivní společník na hráče

## Příkazy

```
/alua_test
/alua_spawn
/alua_follow
/alua_stay
/alua_recall
/alua_status
/alua_scan
/alua_remove
/alua_help
```

## Dokumentace

- [VISION.md](VISION.md) – dlouhodobá vize a nepřekročitelná pravidla
- [ROADMAP.md](ROADMAP.md) – fáze vývoje a podmínky dokončení
- [ARCHITECTURE.md](ARCHITECTURE.md) – modulární architektura a hranice systémů
- [PERCEPTION_MODEL.md](PERCEPTION_MODEL.md) – pravidla vnímání, neznalosti a učení
- [WORLD_SCOPE.md](WORLD_SCOPE.md) – co ve světě měníme a co ne
- [CHANGE_POLICY.md](CHANGE_POLICY.md) – povinná pravidla pro změny a dokumentaci
- [CHANGELOG.md](CHANGELOG.md) – historie skutečně provedených změn
- [DECISIONS.md](DECISIONS.md) – důležitá architektonická rozhodnutí

## Jazyk dokumentace

Interní dokumentace projektu je vedena **česky**. Kódové názvy modulů, funkcí a rozhraní mohou být anglicky.

## Povinné pravidlo vývoje

Významná změna kódu nebo herního chování není považována za dokončenou, dokud nejsou ve stejné změně aktualizované příslušné dokumenty.

## Licence

MIT
