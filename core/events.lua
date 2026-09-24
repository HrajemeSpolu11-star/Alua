alua.events = alua.events or {
    handlers = {},
}

function alua.events.subscribe(event_name, module_id, fn)
    assert(type(event_name) == "string" and event_name ~= "", "event_name is required")
    assert(type(module_id) == "string" and module_id ~= "", "module_id is required")
    assert(type(fn) == "function", "event handler must be a function")

    local list = alua.events.handlers[event_name]
    if not list then
        list = {}
        alua.events.handlers[event_name] = list
    end

    table.insert(list, {
        module_id = module_id,
        fn = fn,
    })
end

function alua.events.emit(event_name, payload)
    local list = alua.events.handlers[event_name]
    if not list then
        return
    end

    for _, handler in ipairs(list) do
        local ok, err = pcall(handler.fn, payload)
        if not ok then
            core.log(
                "error",
                "[Alua] Event handler failed (" .. handler.module_id .. ", " .. event_name .. "): " .. tostring(err)
            )
        end
    end
end
