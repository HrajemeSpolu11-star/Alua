alua.ai = alua.ai or {}

alua.register_module({
    id = "ai.core",
    requires = {"world.adapter"},
    enabled = function()
        return alua.config.get_bool("ai")
    end,
    init = function()
        alua.ai.enabled = true
        alua.ai.sense = function(sensor_id, agent_context, request)
            return alua.world_adapter.sense(sensor_id, agent_context, request)
        end
        alua.ai.act = function(action_id, agent_context, request)
            return alua.world_adapter.act(action_id, agent_context, request)
        end
    end,
})
