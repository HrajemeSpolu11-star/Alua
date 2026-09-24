# Pravidla změn projektu

Tento dokument je závazný pro další vývoj.

## Jazyk

Veškerá interní dokumentace, poznámky, roadmapa, changelog, rozhodnutí a popisy architektury jsou vedené **česky**.

Výjimkou jsou:
- názvy funkcí, modulů, API a technické identifikátory v kódu
- veřejná metadata určená mezinárodnímu publiku, například ContentDB

## Dokumentace je součást hotové změny

Významná změna není dokončená, dokud nejsou ve stejném change setu aktualizované příslušné dokumenty.

Kontroluje se zejména:

- `CHANGELOG.md` – vždy při skutečně implementované změně
- `ROADMAP.md` – při změně stavu, priority nebo rozsahu úkolu
- `ARCHITECTURE.md` – při změně modulů, API, persistence nebo závislostí
- `VISION.md` – při změně základní vize
- `PERCEPTION_MODEL.md` – při změně toho, co Alua smí vnímat nebo vědět
- `WORLD_SCOPE.md` – při změně pravidel světa
- `DECISIONS.md` – při zásadním architektonickém rozhodnutí
- `README.md` – při změně uživatelsky viditelných funkcí

## Povinný checklist

Před dokončením změny:

1. Má změna jasného vlastníka/modul?
2. Mění veřejné rozhraní?
3. Ukládá nová data?
4. Může poškodit starý save?
5. Mění kompatibilitu s Mineclonií?
6. Mění vizi nebo roadmapu?
7. Neobchází perception boundary?
8. Byly aktualizovány potřebné dokumenty?
9. Existuje cesta k vypnutí/rollbacku world změny?
10. Neobsahuje repo tokeny nebo jiná tajemství?
11. Lze změnu ověřit testem, příkazem nebo scénářem?

## Žádné nezapsané posouvání vize

Rozhodnutí přijaté během vývoje musí být zapsané do repozitáře. Historie chatu není zdroj pravdy projektu.

## Postupná architektura

Velké přepisy se nedělají jen kvůli čistotě. Převádíme vždy jednu zodpovědnost za druhou a mezi kroky musí projekt zůstat spustitelný.
