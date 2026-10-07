from __future__ import annotations

from typing import Any

from .store import Store


def _signal(event: dict[str, Any], key: str) -> float:
    value = event.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0.0
    return max(-1.0, min(1.0, float(value)))


def motor_quality(event: dict[str, Any]) -> float:
    progress = event.get("progress_signal", event.get("success_signal"))
    if not isinstance(progress, (int, float)) or isinstance(progress, bool):
        return 0.0
    return max(0.0, min(1.0, float(progress)))


def motor_success(event: dict[str, Any]) -> bool:
    feedback = event.get("feedback_signal")
    return motor_quality(event) >= 0.55 and feedback not in {
        "partial_effect",
        "no_effect",
        "resistance",
        "impact_resisted",
        "containment_failed",
    }


def _belief(
    store: Store,
    *,
    agent_id: str,
    expectation: dict[str, Any],
    sequence: int,
    belief_key: str,
    kind: str,
    subject_signature: str | None,
    relation: str,
    value: dict[str, Any],
    supported: bool,
) -> None:
    store.update_binary_belief(
        agent_id=agent_id,
        belief_key=belief_key,
        kind=kind,
        subject_signature=subject_signature,
        relation=relation,
        value=value,
        supported=supported,
        sequence=sequence,
        evidence_session_id=expectation.get("session_id"),
        evidence_decision_id=expectation.get("decision_id"),
    )


def learn_from_motor_outcome(
    store: Store,
    agent_id: str,
    expectation: dict[str, Any],
    event: dict[str, Any],
    observation_sequence: int,
) -> None:
    succeeded = motor_success(event)
    action_type = expectation["action_type"]
    _belief(
        store,
        agent_id=agent_id,
        expectation=expectation,
        sequence=observation_sequence,
        belief_key=f"action:{action_type}:motor_effect",
        kind="procedural",
        subject_signature=action_type,
        relation="motor_effect",
        value={"expected": True},
        supported=succeeded,
    )

    action = expectation.get("action")
    parameters = action.get("parameters") if isinstance(action, dict) else None
    parameters = parameters if isinstance(parameters, dict) else {}

    if action_type == "move":
        mode = parameters.get("mode", "walk")
        if isinstance(mode, str) and mode:
            _belief(
                store,
                agent_id=agent_id,
                expectation=expectation,
                sequence=observation_sequence,
                belief_key=f"locomotion:{mode}:motor_effect",
                kind="procedural",
                subject_signature=mode,
                relation="motor_effect",
                value={"expected": True},
                supported=succeeded,
            )

    verb = parameters.get("verb")
    if action_type == "interact" and isinstance(verb, str) and verb:
        _belief(
            store,
            agent_id=agent_id,
            expectation=expectation,
            sequence=observation_sequence,
            belief_key=f"interaction:{verb}:effect",
            kind="procedural",
            subject_signature=verb,
            relation=f"{verb}_effect",
            value={"expected": True},
            supported=succeeded,
        )

    target_signature = expectation.get("target_signature")
    if not isinstance(target_signature, str) or not target_signature:
        return
    if not isinstance(verb, str) or not verb:
        return

    _belief(
        store,
        agent_id=agent_id,
        expectation=expectation,
        sequence=observation_sequence,
        belief_key=f"appearance:{target_signature}:{verb}:effect",
        kind="empirical",
        subject_signature=target_signature,
        relation=f"{verb}_effect",
        value={"expected": True},
        supported=succeeded,
    )

    if verb == "consume":
        nutrition_delta = _signal(event, "nutrition_delta_signal")
        hydration_delta = _signal(event, "hydration_delta_signal")
        _belief(
            store,
            agent_id=agent_id,
            expectation=expectation,
            sequence=observation_sequence,
            belief_key=f"appearance:{target_signature}:consume:nutrition_effect",
            kind="empirical",
            subject_signature=target_signature,
            relation="nutrition_effect",
            value={"positive_effect": True},
            supported=nutrition_delta > 0.005,
        )
        _belief(
            store,
            agent_id=agent_id,
            expectation=expectation,
            sequence=observation_sequence,
            belief_key=f"appearance:{target_signature}:consume:hydration_effect",
            kind="empirical",
            subject_signature=target_signature,
            relation="hydration_effect",
            value={"positive_effect": True},
            supported=hydration_delta > 0.005,
        )

    elif verb == "drink":
        hydration_delta = _signal(event, "hydration_delta_signal")
        _belief(
            store,
            agent_id=agent_id,
            expectation=expectation,
            sequence=observation_sequence,
            belief_key=f"appearance:{target_signature}:drink:hydration_effect",
            kind="empirical",
            subject_signature=target_signature,
            relation="hydration_effect",
            value={"positive_effect": True},
            supported=hydration_delta > 0.005,
        )

    elif verb == "pickup":
        inventory_delta = _signal(event, "inventory_delta_signal")
        _belief(
            store,
            agent_id=agent_id,
            expectation=expectation,
            sequence=observation_sequence,
            belief_key=f"appearance:{target_signature}:pickup:inventory_effect",
            kind="empirical",
            subject_signature=target_signature,
            relation="inventory_effect",
            value={"stored": True},
            supported=inventory_delta > 0.005,
        )
