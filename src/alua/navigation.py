from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from .world_model import EgocentricWorldModel


@dataclass(frozen=True, slots=True)
class NavigationChoice:
    maneuver: str
    forward: float
    strafe: float
    duration_s: float
    speed_fraction: float
    score: float
    reason: dict[str, Any]


class LocalNavigator:
    """Cost-based receding-horizon navigator over Alua's egocentric model.

    This intentionally does not use a hidden map. It borrows the useful idea
    from mature pathfinders -- score candidate moves and replan after each
    observation -- but the graph is made only from currently perceived space.
    """

    def __init__(self) -> None:
        self._failure_penalty = {
            "forward": 0.0,
            "left": 0.0,
            "right": 0.0,
            "back": 0.0,
        }
        self._recent: deque[str] = deque(maxlen=6)

    def reset(self) -> None:
        for key in self._failure_penalty:
            self._failure_penalty[key] = 0.0
        self._recent.clear()

    @staticmethod
    def maneuver_from_parameters(parameters: dict[str, Any]) -> str:
        forward = parameters.get("forward", 0.0)
        strafe = parameters.get("strafe", 0.0)
        if not isinstance(forward, (int, float)) or isinstance(forward, bool):
            forward = 0.0
        if not isinstance(strafe, (int, float)) or isinstance(strafe, bool):
            strafe = 0.0
        forward = float(forward)
        strafe = float(strafe)
        if forward < -0.25 and abs(strafe) < 0.35:
            return "back"
        if strafe > 0.25:
            return "right"
        if strafe < -0.25:
            return "left"
        return "forward"

    def observe_outcome(self, action: dict[str, Any], supported: bool) -> None:
        if action.get("type") != "move":
            return
        parameters = action.get("parameters")
        if not isinstance(parameters, dict):
            return
        maneuver = self.maneuver_from_parameters(parameters)
        if supported:
            self._failure_penalty[maneuver] *= 0.35
        else:
            self._failure_penalty[maneuver] = min(
                2.0,
                self._failure_penalty[maneuver] + 0.65,
            )
        for key in self._failure_penalty:
            if key != maneuver:
                self._failure_penalty[key] *= 0.92

    def record_maneuver(self, maneuver: str) -> None:
        if maneuver in self._failure_penalty:
            self._recent.append(maneuver)

    def _repetition_penalty(self, maneuver: str) -> float:
        if not self._recent:
            return 0.0
        trailing = 0
        for item in reversed(self._recent):
            if item != maneuver:
                break
            trailing += 1
        return 0.14 * max(0, trailing - 1)

    def _score(
        self,
        maneuver: str,
        sector_score: float,
        *,
        mode: str,
    ) -> float:
        score = sector_score
        score -= self._failure_penalty[maneuver]
        score -= self._repetition_penalty(maneuver)
        if maneuver == "back":
            score -= 0.12
        if mode == "lateral":
            score += 0.30 if maneuver in {"left", "right"} else -0.35
        elif mode == "escape":
            score += 0.20 if maneuver in {"left", "right", "back"} else -0.25
        elif mode == "frontier":
            score += 0.10 if maneuver == "forward" else 0.0
        return score

    def choose(
        self,
        model: EgocentricWorldModel,
        *,
        mode: str = "frontier",
        persistent_penalties: dict[str, float] | None = None,
    ) -> NavigationChoice:
        if mode not in {"frontier", "lateral", "escape"}:
            raise ValueError("unknown navigation mode")

        sector_scores = {
            "forward": model.sector_score("front"),
            "left": model.sector_score("left"),
            "right": model.sector_score("right"),
            # Back is intentionally treated as partly unknown because Alua has
            # no rear-facing ray in the current sensory contract.
            "back": 0.22,
        }
        if model.front_is_blocked():
            sector_scores["forward"] -= 0.80

        priors = persistent_penalties or {}
        scores = {
            maneuver: self._score(maneuver, base, mode=mode)
            - max(0.0, float(priors.get(maneuver, 0.0)))
            for maneuver, base in sector_scores.items()
        }
        order = ("forward", "left", "right", "back")
        maneuver = max(order, key=lambda item: (scores[item], -order.index(item)))

        if maneuver == "forward":
            forward, strafe = 1.0, 0.0
        elif maneuver == "left":
            forward, strafe = 0.18, -0.78
        elif maneuver == "right":
            forward, strafe = 0.18, 0.78
        else:
            forward, strafe = -0.65, 0.0

        conservative = mode in {"lateral", "escape"} or model.front_is_blocked()
        speed = 0.42 if conservative else 0.58
        duration = 0.32 if conservative else 0.38

        return NavigationChoice(
            maneuver=maneuver,
            forward=forward,
            strafe=strafe,
            duration_s=duration,
            speed_fraction=speed,
            score=scores[maneuver],
            reason={
                "navigator": "receding_horizon_v1",
                "mode": mode,
                "candidate_scores": {
                    key: round(value, 4)
                    for key, value in scores.items()
                },
                "failure_penalty": {
                    key: round(value, 4)
                    for key, value in self._failure_penalty.items()
                },
                "persistent_penalty": {
                    key: round(max(0.0, float(priors.get(key, 0.0))), 4)
                    for key in ("forward", "left", "right", "back")
                },
            },
        )

    def prefers_forward(
        self,
        model: EgocentricWorldModel,
        *,
        persistent_penalties: dict[str, float] | None = None,
    ) -> bool:
        return self.choose(
            model,
            mode="frontier",
            persistent_penalties=persistent_penalties,
        ).maneuver == "forward"
