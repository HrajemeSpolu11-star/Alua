alua = rawget(_G, "alua") or {}
_G.alua = alua

alua.modname = core.get_current_modname()
alua.modpath = core.get_modpath(alua.modname)
alua.active = alua.active or {}

core.log("action", "[Alua] Loading autonomous companion framework")

dofile(alua.modpath .. "/npc.lua")
dofile(alua.modpath .. "/commands.lua")

core.log("action", "[Alua] Loaded successfully")
