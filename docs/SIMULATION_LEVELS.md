# Úrovně simulace živého světa

## Proč

Telefon nemůže počítat plnou fyziku a plnou kognici stovek NPC každou desetinu sekundy. Populace proto používá různé úrovně detailu.

## ACTIVE

NPC je blízko hráče:
- skutečná entita
- fyzika
- smysly
- časté reakce
- detailní AI

## NEAR

NPC je v širší aktivní oblasti:
- entita může zůstat načtená
- senzory a rozhodování běží méně často
- zjednodušené detaily

## BACKGROUND

NPC je daleko:
- nemusí mít fyzickou entitu
- simuluje se stav, činnost, cesta, spotřeba a vztahy
- aktualizace probíhá v delších intervalech

## DORMANT

Dlouhodobě neaktivní oblast:
- ukládá se pouze nutný stav
- žádné průběžné fyzikální kroky
- při probuzení se dopočítají relevantní změny

## Pravidlo konzistence

Přechod mezi úrovněmi nesmí vytvářet zdroje, mazat majetek nebo měnit identitu NPC. Abstraktní simulace musí být kompatibilní s detailní simulací.
