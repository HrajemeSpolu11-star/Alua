# Architectural Decisions

This document records important decisions so future development does not accidentally reverse them.

## ADR-001 - Alua is the AI

**Status:** Accepted  
**Date:** 2026-09-24

Core intelligence is implemented inside the Alua project. An external LLM or remote AI API is not required for normal autonomous behaviour.

Reason: the goal is to build an autonomous agent, not a game client for another AI service.

## ADR-002 - Mineclonia remains the base map/world

**Status:** Accepted  
**Date:** 2026-09-24

We keep Mineclonia as the base world and map generator. Development may change selected physics, items, interactions and environmental rules through modules.

Reason: the project focuses on Alua intelligence and selected world rules, not rebuilding terrain generation.

## ADR-003 - Modular architecture over monolithic scripts

**Status:** Accepted  
**Date:** 2026-09-24

New capabilities are split into modules with documented boundaries. Core services provide registration, events and persistent-state facilities.

Reason: perception, memory, planning, actions and world rules will grow independently and must remain replaceable.

## ADR-004 - Documentation is part of every change

**Status:** Accepted  
**Date:** 2026-09-24

Accepted vision, roadmap changes and meaningful implementation changes must be written to repository documents. Chat history is not the authoritative project record.

Reason: the project is intended to evolve over a long period without losing prior decisions or repeatedly rediscovering architecture.
