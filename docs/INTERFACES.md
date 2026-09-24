# Rozhraní mezi světem a AI

## Základní tok

```
Luanti / Mineclonia
      ↓
world
      ↓
world.adapter
      ↓
omezený vjem
      ↓
ai.perception
      ↓
memory + world_model
      ↓
goals + planning
      ↓
ai.actions
      ↓
world.adapter
      ↓
svět
```

## Sensor API

World adapter registruje pouze explicitně povolené senzory. AI může požádat o vjem podle ID senzoru, ale nedostává přímý přístup k enginu.

Aktuální kostra:

```lua
alua.world_adapter.register_sensor(id, fn)
alua.ai.sense(id, agent_context, request)
```

Konkrétní senzory se teprve navrhnou.

## Action API

Akce jsou stejně explicitní:

```lua
alua.world_adapter.register_action(id, fn)
alua.ai.act(id, agent_context, request)
```

Agent tedy nežádá engine o libovolnou změnu. Může provést jen akci, kterou world vrstva skutečně nabízí.

## Důsledek

Stejný world systém může později používat:
- hráč
- Alua
- další AI NPC
- jednoduchá NPC bez plné AI
- skriptované příběhové entity

A AI lze vyměnit nebo přepsat bez změny fyzikálních pravidel světa.
