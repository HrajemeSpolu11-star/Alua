alua = rawget(_G, "alua") or {}
_G.alua = alua

alua.modname = core.get_current_modname()
alua.modpath = core.get_modpath(alua.modname)
alua.active = alua.active or {}

core.log("action", "[Alua] Loading modular autonomous world framework")

local function load(path)
    dofile(alua.modpath .. "/" .. path)
end

-- Jádro: žádná doménová logika.
load("core/module_registry.lua")
load("core/events.lua")
load("core/state.lua")
load("core/config.lua")
load("core/scheduler.lua")

alua.state.initialize()

-- Svět a jeho pravda. AI k této vrstvě nesmí přistupovat přímo.
load("world/init.lua")
load("world/adapter/init.lua")
load("world/materials/init.lua")
load("world/physics/init.lua")
load("world/items/init.lua")
load("world/environment/init.lua")
load("world/compatibility/init.lua")

-- Kognitivní vrstva.
load("ai/init.lua")
load("ai/perception/init.lua")
load("ai/memory/init.lua")
load("ai/world_model/init.lua")
load("ai/needs/init.lua")
load("ai/actions/init.lua")
load("ai/goals/init.lua")
load("ai/planning/init.lua")
load("ai/learning/init.lua")

-- Živý svět kolem jednotlivých agentů.
load("population/init.lua")
load("economy/init.lua")
load("society/init.lua")
load("story/init.lua")
load("debug/init.lua")

-- Přechodná kompatibilní vrstva současné verze.
-- Funkční companion zůstává nedotčený, dokud nebude postupně migrován.
load("npc.lua")
load("commands.lua")

alua.init_modules({
    modname = alua.modname,
    modpath = alua.modpath,
    events = alua.events,
    state = alua.state,
    config = alua.config,
    scheduler = alua.scheduler,
})

core.log("action", "[Alua] Loaded successfully")
