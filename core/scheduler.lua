alua.scheduler = alua.scheduler or {
    jobs = {},
}

function alua.scheduler.register(id, interval, fn)
    assert(type(id) == "string" and id ~= "", "Scheduler job id is required")
    assert(type(interval) == "number" and interval > 0, "Scheduler interval must be > 0")
    assert(type(fn) == "function", "Scheduler callback must be a function")

    if alua.scheduler.jobs[id] then
        error("Scheduler job already registered: " .. id)
    end

    alua.scheduler.jobs[id] = {
        interval = interval,
        elapsed = 0,
        fn = fn,
    }
end

function alua.scheduler.unregister(id)
    alua.scheduler.jobs[id] = nil
end

core.register_globalstep(function(dtime)
    for id, job in pairs(alua.scheduler.jobs) do
        job.elapsed = job.elapsed + dtime

        if job.elapsed >= job.interval then
            job.elapsed = job.elapsed % job.interval

            local ok, err = pcall(job.fn, job.interval)
            if not ok then
                core.log("error", "[Alua] Scheduler job failed (" .. id .. "): " .. tostring(err))
            end
        end
    end
end)
