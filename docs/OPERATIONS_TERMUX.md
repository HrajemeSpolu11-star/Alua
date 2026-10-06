# Provoz Alua AI v Termuxu

Tento dokument popisuje cílový provoz po implementaci Python runtime.

## Umístění

Doporučeně:
    ~/alua/Alua
    ~/alua/Aluabridge
    ~/alua/games/aluaworld

Kognitivní data:
    ~/alua/data/alua-1/

DB nesmí být uvnitř Git repozitáře.

## Procesy

Na jednom telefonu mohou běžet tři oddělené procesy:
1. Luanti server s AluaWorld;
2. AluaBridge na 127.0.0.1:8787;
3. Alua AI pro agent_id alua:1.

## Environment Alua

Plánované proměnné:
    ALUA_AGENT_ID=alua:1
    ALUABRIDGE_URL=http://127.0.0.1:8787
    ALUA_AGENT_TOKEN=<secret>
    ALUA_DB_PATH=$HOME/alua/data/alua-1/alua.sqlite3

Token nesmí být commitnutý.

## Start pořadí

1. AluaWorld;
2. AluaBridge;
3. Alua AI.

Alua AI ale musí umět bezpečně přežít:
- Bridge ještě neběží;
- World session ještě neexistuje;
- Bridge se restartuje;
- World se restartuje.

Nemá crash-loopovat agresivně; používá omezený backoff.

## Backup

Před migrací DB:
- zastavit Alua proces;
- vytvořit timestampovanou kopii DB;
- spustit migration doctor;
- až potom start runtime.

## Pozorování

Plánované CLI:
    python -m alua doctor
    python -m alua status
    python -m alua run

status má ukazovat provozní stav a kognitivní souhrn, ne tajné tokeny ani world truth.

## Telefonní omezení

V1 musí být navržena tak, aby:
- neběžela v těsném busy-loop;
- nepoužívala těžký LLM inference jako povinnou součást;
- držela bounded working memory;
- dávkovala persistence;
- neměla vysokofrekvenční web/network provoz mimo localhost.
