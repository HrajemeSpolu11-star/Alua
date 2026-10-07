from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.causal import CausalLearner
from alua.consolidation import MemoryConsolidator
from alua.missions import MissionManager
from alua.predictive import PredictiveModel
from alua.prospective import ProspectiveMemory
from alua.risk import RiskModel
from alua.self_model import SelfModel
from alua.store import Store
from alua.strategy import StrategyLearner


ACTION = {
    "type": "move",
    "parameters": {
        "mode": "walk",
        "forward": 1.0,
        "strafe": 0.0,
    },
}


class AdvancedCognitionTests(unittest.TestCase):
    def test_risk_self_causal_and_strategy_learn_from_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                risk = RiskModel().learn(
                    store,
                    agent_id="alua:1",
                    context_signature="place-a",
                    action=ACTION,
                    supported=False,
                    progress=0.1,
                    slip=0.6,
                    damage_signal=0.2,
                    sequence=1,
                )
                self.assertGreater(risk.score, 0.18)

                self_estimate = SelfModel().learn(
                    store,
                    agent_id="alua:1",
                    action=ACTION,
                    supported=True,
                    progress=0.8,
                    effort=0.3,
                    sequence=2,
                )
                self.assertEqual(self_estimate.attempts, 1)
                self.assertGreater(self_estimate.mean_progress, 0.7)

                hypotheses = CausalLearner().record_intervention(
                    store,
                    agent_id="alua:1",
                    context_signature="place-a",
                    action=ACTION,
                    event={
                        "progress_signal": 0.8,
                        "inventory_delta_signal": 0.0,
                    },
                    sequence=3,
                )
                self.assertTrue(
                    any(item.outcome == "progress_signal" for item in hypotheses)
                )

                strategy = StrategyLearner().learn(
                    store,
                    agent_id="alua:1",
                    goal_kind="explore",
                    action=ACTION,
                    supported=True,
                    progress=0.85,
                    sequence=4,
                )
                self.assertGreater(strategy.score, 0.5)
            finally:
                store.close()

    def test_mission_and_prospective_memory_persist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                missions = MissionManager()
                missions.ensure(
                    store,
                    agent_id="alua:1",
                    key="learn-world",
                    kind="open_world_learning",
                    priority=0.7,
                    sequence=1,
                )
                self.assertEqual(len(missions.active(store, agent_id="alua:1")), 1)

                future = ProspectiveMemory()
                future.remember(
                    store,
                    agent_id="alua:1",
                    key="inspect-later",
                    kind="inspect",
                    trigger_place="place-a",
                    priority=0.8,
                    sequence=2,
                )
                self.assertEqual(
                    len(
                        future.due(
                            store,
                            agent_id="alua:1",
                            current_place="place-a",
                        )
                    ),
                    1,
                )
                self.assertEqual(
                    len(
                        future.due(
                            store,
                            agent_id="alua:1",
                            current_place="place-b",
                        )
                    ),
                    0,
                )
            finally:
                store.close()

    def test_consolidation_creates_bounded_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                store.apply_session("alua:1", "s1")
                consolidator = MemoryConsolidator(interval=64)
                report = consolidator.consolidate(
                    store,
                    agent_id="alua:1",
                    session_id="s1",
                    sequence=64,
                )
                self.assertEqual(report.sequence, 64)
                # An empty session has nothing to summarize, but consolidation
                # must still complete without inventing data.
                self.assertFalse(report.episode_summary_created)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
