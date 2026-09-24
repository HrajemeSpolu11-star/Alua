# Alua Vision

## North star

Alua is an autonomous in-world intelligence implemented directly in Luanti. It is not a shell around an external AI service. The intelligence must emerge from systems that exist inside the project itself.

## What Alua should become

Alua should be able to perceive its surroundings, remember relevant information, maintain internal needs and goals, choose actions, plan multi-step behaviour, execute actions through the same world rules that apply to players, and adapt future decisions from experience.

The project should gradually move from scripted companion behaviour toward autonomous decision-making without becoming a monolithic script.

## Non-negotiable principles

1. **Alua is the AI.** External LLMs or remote AI services are not required for core behaviour.
2. **Modularity first.** New capabilities must be addable without rewriting unrelated systems.
3. **Stable contracts.** Modules communicate through documented interfaces, events and shared context rather than arbitrary cross-file access.
4. **No magic shortcuts.** If Alua needs an item, resource or location, future systems should prefer normal world rules over spawning or teleporting resources without cause.
5. **Observable decisions.** Important internal state and decisions should be inspectable for debugging.
6. **Save safety.** Persistent data must be versioned so future updates can migrate old worlds safely.
7. **Mineclonia stays the base world.** We do not plan to replace the map generator. We may modify selected physics, item behaviour, interactions and environmental systems.
8. **Documentation is part of the implementation.** Code changes and vision changes must be reflected in repository documents.

## Long-term capability groups

- Perception
- Memory
- Needs and internal state
- Goals
- Planning and decision making
- Actions and skills
- Inventory and item interaction
- Social/player interaction
- Learning and adaptation
- Debug/inspection tools
- World rule modules

## Out of scope for now

- Replacing Mineclonia's map generator
- Requiring a remote AI API
- Hiding critical AI state in undocumented globals
- Large world changes without a reversible module boundary
