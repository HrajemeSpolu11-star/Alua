# Alua

Alua is an experimental autonomous companion framework for Luanti, currently tested with **Mineclonia**.

The current release is already playable: every player can spawn one persistent Alua companion, switch its behaviour, recall it, inspect its simple memory and request a basic sensor report. The long-term goal is to connect the in-game agent to a more capable external AI brain while keeping the Luanti-side actions explicit and controllable.

## Current features

- Persistent companion entity with owner binding
- Autonomous follow behaviour
- Stay / follow mode switching
- Right-click interaction
- Recall command
- Simple persistent memory of the owner's last seen position
- Local sensor report
- Status reporting
- One active companion per player
- Code-only visual using Luanti texture modifiers, so no external media pack is required

## Commands

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

### Quick test

1. Enable the mod for a Mineclonia world.
2. Join the world.
3. Run `/alua_spawn`.
4. Walk away and the companion should follow you.
5. Right-click the companion or run `/alua_stay` to make it wait.
6. Run `/alua_follow` to resume following.
7. Run `/alua_scan` or `/alua_status` to inspect its state.

## Project direction

This is the first functional layer of Alua. Planned later stages include richer perception, path planning, inventories, goals, task execution and an optional external AI bridge.

## Files

- `init.lua` - entry point
- `npc.lua` - companion entity and behaviour
- `commands.lua` - player commands
- `mod.conf` - Luanti metadata

## License

MIT
