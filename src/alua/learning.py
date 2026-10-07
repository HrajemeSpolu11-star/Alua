from __future__ import annotations

from typing import Any

from .store import Store


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


def learn_from_motor_outcome(
    store: Store,
    agent_id: str,
    expectation: dict[str, Any],
    event: dict[str, Any],
    observation_sequence: int,
) -> None:
    succeeded = motor_success(event)
    action_type = expectation["action_type"]
    store.update_binary_belief(
        agent_id=agent_id,
        belief_key=f"action:{action_type}:motor_effect",
        kind="procedural",
        subject_signature=action_type,
        relation="motor_effect",
        value={"expected": True},
        supported=succeeded,
        sequence=observation_sequence,
        evidence_session_id=expectation.get("session_id"),
        evidence_decision_id=expectation.get("decision_id"),
    )

    target_signature = expectation.get("target_signature")
    if target_signature and action_type == "manipulate":
        action = expectation.get("action", {})
        verb = action.get("parameters", {}).get("verb")
        if isinstance(verb, str) and verb:
            store.update_binary_belief(
                agent_id=agent_id,
                belief_key=f"appearance:{target_signature}:{verb}:effect",
                kind="empirical",
                subject_signature=target_signature,
                relation=f"{verb}_effect",
                value={"expected": True},
                supported=succeeded,
                sequence=observation_sequence,
                evidence_session_id=expectation.get("session_id"),
                evidence_decision_id=expectation.get("decision_id"),
            )
