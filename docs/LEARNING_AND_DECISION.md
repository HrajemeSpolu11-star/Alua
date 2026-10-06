# Učení a rozhodování

## Základní smyčka

Alua se učí z posloupnosti:

    stav přesvědčení
      + nový vjem
      + zvolená akce
      + pozdější vjem
      = změna očekávání

HTTP odpověď není fyzický outcome.

## Outcome attribution

Při odeslání akce vznikne pending expectation:
- client_action_id;
- action type;
- kontext;
- target signature, pokud existuje;
- očekávané pozorovatelné změny;
- časové okno;
- confidence očekávání.

Budoucí observations mohou expectation:
- podpořit;
- vyvrátit;
- nechat nerozhodnuté.

## Exploration

Úplně neznámý agent potřebuje schopnost bezpečně zkoušet.

V1 používá omezenou exploraci:
- look před riskantnější manipulací;
- krátké move kroky;
- wait pro pozorování dynamiky;
- interact nebo manipulate pouze na aktuálně dostupném target_ref;
- risk budget podle předchozí negativní zkušenosti.

Exploration nesmí být nekonečné náhodné chování.

## Needs a utility

Fyzické potřeby pocházejí pouze z vjemů těla, které dodá AluaWorld.

Kognitivní vrstva může přidat malé interní utility:
- snížení bezprostředního známého rizika;
- dokončení aktivního cíle;
- získání informace;
- zabránění opakování známého škodlivého výsledku.

V1 nesmí obsahovat skrytou tabulku typu item X je jídlo nebo node Y je cenný.

## Goal selection

Kandidátní cíl má:
- origin;
- priority;
- expected utility;
- urgency;
- uncertainty;
- estimated cost;
- evidence.

Vybraný cíl se zapíše do decision trace.

## Planner

První planner má být malý a deterministický.

Podmínky:
- pracuje pouze s primitivními akcemi povolenými session;
- má limit hloubky;
- má limit kandidátů;
- umí bezpečně selhat;
- při nové důležité observation přeplánuje;
- nesmí generovat libovolný kód nebo shell.

## Učení vztahů

První verze se zaměří na:
- četnost pozorovaných přechodů;
- úspěšnost opakovaných akcí v podobném kontextu;
- risk score;
- novelty score;
- confidence aktualizovanou podpůrnou a rozpornou evidencí.

Pokročilé neuronové modely nejsou podmínkou V1.

## LLM

Externí LLM není součástí základního autonomního cyklu.

Později může být přidán jako volitelný diagnostický nebo jazykový modul, ale nesmí:
- dostat world truth mimo perception boundary;
- nahrazovat perzistentní kognitivní stav;
- být jediným zdrojem rozhodnutí;
- měnit beliefs bez evidence.
