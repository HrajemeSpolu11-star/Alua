from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.predictive import PredictiveModel
from alua.store import Store


ACTION = {
    "type": "move",
    "parameters": {
        "mode": "walk",
        "forward": 1.0,
        "strafe": 0.0,
    },
}


class PredictiveTests(unittest.TestCase):
    def test_prediction_learns_progress_and_reduces_uncertainty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                model = PredictiveModel()
                before = model.predict(store, "alua:1", "place-a", ACTION)
                for sequence in range(1, 6):
                    model.learn(
                        store,
                        agent_id="alua:1",
                        context_signature="place-a",
                        action=ACTION,
                        supported=True,
                        progress=0.9,
                        sequence=sequence,
                    )
                after = model.predict(store, "alua:1", "place-a", ACTION)
                self.assertGreater(after.expected_progress, before.expected_progress)
                self.assertGreater(after.confidence, before.confidence)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
