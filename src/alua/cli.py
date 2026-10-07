from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
import sys

from .bridge_client import BridgeClient
from .config import Config
from .errors import AluaError
from .evaluation import acceptance_report, evaluate_sensory_replay, evaluate_trace
from .runtime import Runtime
from .store import Store


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alua", description="Alua AI cognitive runtime")
    parser.add_argument("--verbose", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("doctor", help="Ověří konfiguraci, DB a spojení s AluaBridge")
    commands.add_parser("status", help="Vypíše lokální stav kognitivní persistence")
    commands.add_parser("cognition-status", help="Vypíše stav Cognitive Core V5 a jeho dlouhodobé modely")
    evaluate = commands.add_parser("evaluate", help="Vyhodnotí chování v aktuální World session")
    evaluate.add_argument("--limit", type=int, default=500, help="Maximální počet posledních rozhodnutí")
    benchmark = commands.add_parser("benchmark", help="Provede offline behaviorální a sensory acceptance test")
    benchmark.add_argument("--limit", type=int, default=2000, help="Maximální počet posledních rozhodnutí a vjemů")
    run = commands.add_parser("run", help="Spustí kognitivní runtime")
    run.add_argument("--once", action="store_true", help="Provede právě jeden cyklus")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        config = Config.from_env()
        store = Store(config.database_path)
        try:
            if args.command == "status":
                print(json.dumps(store.summary(config.agent_id), ensure_ascii=False, indent=2))
                return 0

            if args.command == "cognition-status":
                records = store.cognitive_records(
                    config.agent_id,
                    limit=5000,
                )
                kinds: dict[str, int] = {}
                for record in records:
                    kind = str(record.get("record_kind") or "unknown")
                    kinds[kind] = kinds.get(kind, 0) + 1
                last_state = store.cognitive_record(
                    config.agent_id,
                    "cognition:last-state",
                )
                missions = [
                    record
                    for record in records
                    if record.get("record_kind") == "mission"
                    and record.get("payload", {}).get("active") is True
                ]
                result = {
                    "agent_id": config.agent_id,
                    "session_id": store.state(config.agent_id).get("session_id"),
                    "schema_version": store.summary(config.agent_id)["schema_version"],
                    "record_counts": dict(sorted(kinds.items())),
                    "active_missions": [
                        {
                            "key": item["payload"].get("key"),
                            "kind": item["payload"].get("kind"),
                            "priority": item["payload"].get("priority"),
                            "stage": item["payload"].get("stage"),
                            "confidence": item.get("confidence"),
                        }
                        for item in missions[:16]
                    ],
                    "last_cognitive_state": (
                        last_state.get("payload")
                        if last_state
                        else None
                    ),
                }
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0

            if args.command == "evaluate":
                trace = store.session_trace(config.agent_id, limit=args.limit)
                result = {
                    "agent_id": config.agent_id,
                    "session_id": store.state(config.agent_id).get("session_id"),
                    "trace_limit": max(1, min(5000, int(args.limit))),
                    "metrics": evaluate_trace(trace),
                }
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0

            if args.command == "benchmark":
                state = store.state(config.agent_id)
                session_id = state.get("session_id")
                trace = store.session_trace(
                    config.agent_id,
                    session_id,
                    limit=args.limit,
                )
                episodes = store.session_episodes(
                    config.agent_id,
                    session_id,
                    limit=args.limit,
                )
                behavior = evaluate_trace(trace)
                sensory = evaluate_sensory_replay(episodes)
                acceptance = acceptance_report(behavior, sensory)
                result = {
                    "agent_id": config.agent_id,
                    "session_id": session_id,
                    "behavior": behavior,
                    "sensory_replay": sensory,
                    "acceptance": acceptance,
                }
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0 if acceptance["passed"] else 3

            bridge = BridgeClient(config)
            if args.command == "doctor":
                result = {
                    "config": "ok",
                    "database": "ok",
                    "health": bridge.health(),
                    "session": bridge.session(),
                }
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0

            runtime = Runtime(config, store, bridge)
            if args.once:
                print(json.dumps(asdict(runtime.step()), ensure_ascii=False, indent=2))
                return 0
            runtime.run_forever()
            return 0
        finally:
            store.close()
    except KeyboardInterrupt:
        return 130
    except AluaError as exc:
        print(f"Alua chyba: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Neočekávaná chyba: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
