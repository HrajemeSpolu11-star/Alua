from __future__ import annotations

import unittest

from alua.embodiment import (
    inventory_load,
    inventory_slot_by_appearance,
    inventory_slots,
    locomotion_signals,
    vital_signals,
)
from alua.perception import build_frame


def frame():
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": 1,
        "simulation_time": 1.0,
        "channels": {
            "vitals": {
                "health_fraction": 0.8,
                "stamina_fraction": 0.35,
                "hunger_signal": 0.6,
                "thirst_signal": 0.7,
                "fatigue_signal": 0.4,
                "breath_fraction": 0.9,
            },
            "inventory": {
                "slot_count": 12,
                "occupied_slots": 1,
                "load_fraction": 0.25,
                "slots": [{
                    "slot_index": 2,
                    "appearance_id": "pfood",
                    "count": 3,
                    "mass_fraction": 0.1,
                }],
            },
            "locomotion": {
                "grounded_signal": 1,
                "step_up_signal": 1,
                "gap_ahead_signal": 1,
                "jump_gap_signal": 1,
                "safe_drop_signal": 0,
                "climbable_signal": 0,
                "feet_in_liquid_signal": 0,
                "head_submerged_signal": 0,
                "posture": "standing",
                "active_mode": "idle",
            },
        },
    })


class EmbodimentTests(unittest.TestCase):
    def test_vital_signals_are_read_without_world_truth(self) -> None:
        vitals = vital_signals(frame())
        self.assertAlmostEqual(vitals.stamina, 0.35)
        self.assertAlmostEqual(vitals.hunger, 0.6)
        self.assertAlmostEqual(vitals.thirst, 0.7)

    def test_inventory_uses_only_opaque_appearance(self) -> None:
        current = frame()
        slots = inventory_slots(current)
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].appearance_id, "pfood")
        self.assertEqual(slots[0].count, 3)
        self.assertAlmostEqual(inventory_load(current), 0.25)
        self.assertEqual(
            inventory_slot_by_appearance(current, "pfood").slot_index,
            2,
        )

    def test_jump_gap_affordance_is_preserved(self) -> None:
        signals = locomotion_signals(frame())
        self.assertEqual(signals["grounded_signal"], 1.0)
        self.assertEqual(signals["jump_gap_signal"], 1.0)
        self.assertEqual(signals["posture"], "standing")


if __name__ == "__main__":
    unittest.main()
