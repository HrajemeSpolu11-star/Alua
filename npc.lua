local function notify(name, message)
    if name and name ~= "" then
        core.chat_send_player(name, "[Alua] " .. message)
    end
end

local function horizontal_velocity(object, x, z)
    local current = object:get_velocity() or {x = 0, y = 0, z = 0}
    object:set_velocity({x = x, y = current.y or 0, z = z})
end

local function safe_deserialize(staticdata)
    if not staticdata or staticdata == "" then
        return {}
    end

    local ok, data = pcall(core.deserialize, staticdata, true)
    if ok and type(data) == "table" then
        return data
    end

    return {}
end

function alua.find_owned(owner)
    local object = alua.active[owner]
    if object and object:get_pos() then
        local luaentity = object:get_luaentity()
        if luaentity and luaentity.name == "alua:companion" and luaentity.owner == owner then
            return object, luaentity
        end
    end

    local player = core.get_player_by_name(owner)
    if not player then
        return nil, nil
    end

    for _, candidate in ipairs(core.get_objects_inside_radius(player:get_pos(), 128)) do
        local luaentity = candidate:get_luaentity()
        if luaentity and luaentity.name == "alua:companion" and luaentity.owner == owner then
            alua.active[owner] = candidate
            return candidate, luaentity
        end
    end

    return nil, nil
end

function alua.spawn(owner)
    local player = core.get_player_by_name(owner)
    if not player then
        return nil, "Player is not online."
    end

    local existing = alua.find_owned(owner)
    if existing then
        return nil, "You already have an active Alua companion."
    end

    local pos = player:get_pos()
    local dir = player:get_look_dir()
    local spawn_pos = {
        x = pos.x + dir.x * 2,
        y = pos.y + 1,
        z = pos.z + dir.z * 2,
    }

    local staticdata = core.serialize({
        owner = owner,
        mode = "follow",
        memory = {
            last_owner_pos = vector.round(pos),
            last_seen = os.time(),
        },
    })

    local object = core.add_entity(spawn_pos, "alua:companion", staticdata)
    if not object then
        return nil, "Could not spawn the companion."
    end

    alua.active[owner] = object
    return object
end

function alua.set_mode(owner, mode)
    local object, entity = alua.find_owned(owner)
    if not object or not entity then
        return false, "No loaded Alua companion found."
    end

    entity.mode = mode
    if mode == "stay" then
        horizontal_velocity(object, 0, 0)
    end

    object:set_properties({
        infotext = "Alua companion | owner: " .. owner .. " | mode: " .. mode,
    })

    return true, "Mode changed to " .. mode .. "."
end

function alua.recall(owner)
    local player = core.get_player_by_name(owner)
    if not player then
        return false, "Player is not online."
    end

    local object, entity = alua.find_owned(owner)
    if not object or not entity then
        return false, "No loaded Alua companion found."
    end

    local pos = player:get_pos()
    local dir = player:get_look_dir()
    object:set_pos({
        x = pos.x - dir.x * 1.5,
        y = pos.y + 0.5,
        z = pos.z - dir.z * 1.5,
    })
    object:set_velocity({x = 0, y = 0, z = 0})

    entity.memory = entity.memory or {}
    entity.memory.last_owner_pos = vector.round(pos)
    entity.memory.last_seen = os.time()

    return true, "Companion recalled."
end

function alua.remove_owned(owner)
    local object = alua.find_owned(owner)
    if not object then
        return false, "No loaded Alua companion found."
    end

    alua.active[owner] = nil
    object:remove()
    return true, "Companion removed."
end

core.register_entity("alua:companion", {
    initial_properties = {
        physical = true,
        collide_with_objects = false,
        collisionbox = {-0.38, -0.7, -0.38, 0.38, 0.7, 0.38},
        selectionbox = {-0.45, -0.75, -0.45, 0.45, 0.75, 0.45},
        pointable = true,
        visual = "cube",
        visual_size = {x = 0.85, y = 1.35, z = 0.85},
        textures = {
            "[fill:1x1:#7DD3FC",
            "[fill:1x1:#0F172A",
            "[fill:1x1:#38BDF8",
            "[fill:1x1:#38BDF8",
            "[fill:1x1:#22C55E",
            "[fill:1x1:#0284C7",
        },
        stepheight = 1.1,
        automatic_face_movement_dir = 0,
        automatic_face_movement_max_rotation_per_sec = 8,
        glow = 2,
        nametag = "Alua",
        nametag_color = {r = 125, g = 211, b = 252, a = 255},
        infotext = "Alua autonomous companion",
        static_save = true,
        show_on_minimap = true,
    },

    owner = "",
    mode = "follow",
    memory = nil,
    _timer = 0,

    on_activate = function(self, staticdata)
        local data = safe_deserialize(staticdata)

        self.owner = data.owner or self.owner or ""
        self.mode = data.mode or "follow"
        self.memory = data.memory or {
            last_owner_pos = nil,
            last_seen = nil,
        }

        self.object:set_acceleration({x = 0, y = -9.81, z = 0})
        self.object:set_armor_groups({immortal = 1})
        self.object:set_properties({
            nametag = self.owner ~= "" and ("Alua • " .. self.owner) or "Alua",
            infotext = "Alua companion | owner: " .. (self.owner ~= "" and self.owner or "unbound") .. " | mode: " .. self.mode,
        })

        if self.owner ~= "" then
            alua.active[self.owner] = self.object
        end
    end,

    get_staticdata = function(self)
        return core.serialize({
            owner = self.owner,
            mode = self.mode,
            memory = self.memory,
        })
    end,

    on_step = function(self, dtime)
        self._timer = self._timer + dtime
        if self._timer < 0.20 then
            return
        end
        self._timer = 0

        if self.owner == "" then
            horizontal_velocity(self.object, 0, 0)
            return
        end

        local owner = core.get_player_by_name(self.owner)
        if not owner then
            horizontal_velocity(self.object, 0, 0)
            return
        end

        local pos = self.object:get_pos()
        local owner_pos = owner:get_pos()
        if not pos or not owner_pos then
            return
        end

        self.memory = self.memory or {}
        self.memory.last_owner_pos = vector.round(owner_pos)
        self.memory.last_seen = os.time()

        local distance = vector.distance(pos, owner_pos)

        if self.mode ~= "follow" then
            horizontal_velocity(self.object, 0, 0)
            return
        end

        if distance <= 2.25 then
            horizontal_velocity(self.object, 0, 0)
            return
        end

        if distance > 35 then
            horizontal_velocity(self.object, 0, 0)
            return
        end

        local dir = vector.direction(pos, owner_pos)
        local speed = distance > 12 and 4.8 or 3.2

        horizontal_velocity(self.object, dir.x * speed, dir.z * speed)
    end,

    on_rightclick = function(self, clicker)
        if not clicker or not clicker:is_player() then
            return
        end

        local name = clicker:get_player_name()
        if name ~= self.owner then
            notify(name, "This companion belongs to " .. (self.owner ~= "" and self.owner or "nobody") .. ".")
            return
        end

        if self.mode == "follow" then
            self.mode = "stay"
            horizontal_velocity(self.object, 0, 0)
        else
            self.mode = "follow"
        end

        self.object:set_properties({
            infotext = "Alua companion | owner: " .. self.owner .. " | mode: " .. self.mode,
        })

        notify(name, "Companion mode: " .. self.mode .. ". Right-click again to toggle.")
    end,

    on_deactivate = function(self)
        if self.owner ~= "" and alua.active[self.owner] == self.object then
            alua.active[self.owner] = nil
        end
    end,
})
