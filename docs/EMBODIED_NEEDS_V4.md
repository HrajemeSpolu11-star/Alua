# Embodied Needs V4

## Goal

Alua uses bodily signals and its own learned evidence to decide when to rest, drink, eat, collect, traverse terrain or acquire a resource.

The cognitive layer is not given semantic labels such as "water", "food", "stone" or "ore".

## Body-driven priorities

Immediate reflexes:

- critical breath while submerged -> surface
- recent damage -> retreat

Intrinsic body needs:

- low stamina / high fatigue -> rest
- thirst -> search for, approach and experimentally drink a visible liquid
- hunger -> consume a carried unknown or learned-useful item; later seek a learned-useful appearance

## Learning food and water

Consumption and drinking are learned from bodily outcomes.

Examples of learned empirical relations:

```text
appearance:p123:consume:nutrition_effect
appearance:p456:drink:hydration_effect
```

A positive belief is created only from a positive nutrition/hydration delta. A failed experiment records contradictory evidence.

Because inventory and vision use the same opaque appearance signature scheme, an appearance that previously improved nutrition can later be recognized visually without revealing its technical item name.

## Collection and inventory experimentation

Novel reachable objects follow a bounded discovery loop:

```text
see -> inspect by touch -> collect one sample -> store -> later experiment if a body need makes it useful
```

Collection is limited by inventory load and per-appearance attempt counts.

## Need-driven mining

Mining is not a default exploration behavior.

`break_object` is selected only through the explicit `acquire_required_resource` goal. Current V4 creates that goal when:

1. hunger creates a real need,
2. Alua has learned that the appearance has a positive nutrition effect,
3. the target is reachable,
4. ordinary pickup attempts have repeatedly failed.

World physics may still reject mining because of reach, tool hardness, impact energy or protection.

## Terrain locomotion

Current bodily affordances can select:

- vault for a one-node step-up
- jump only for a gap with a verified landing
- climb when a climbable surface is sensed
- crouch/crawl for low clearance
- swim when in liquid
- surface swim on low breath
- safe drop for a bounded sensed descent
- sprint in open terrain when stamina/fatigue permit

Unknown deep drops are avoided rather than treated as jump targets.

These are motor possibilities conditioned on current perception. Contextual terrain actions are deliberately excluded from the generic reusable skill library so a successful jump cannot become a context-free "always jump forward" habit.

## Planning boundary

High-level need goals are expanded into bounded data-only skills. No generated executable code and no hidden World map are used.

World owns physical truth. Alua owns goals, utility, memory, beliefs and learned consequences.
