import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from web import GameSession


class WebGameTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.save = Path(temporary.name) / "partie.json"
        self.session = GameSession(self.save)

    def step(self, action, **extra):
        return self.session.dispatch({"action": action, "revision": self.session.revision, **extra})

    def begin(self, kind):
        players = [{"name": "Bílý", "kind": kind}, {"name": "Černý", "kind": "human"}]
        with patch("main.random.randint", side_effect=[6, 1]):
            self.assertEqual(self.step("new", players=players), 200)

    def test_move_changes_board_and_restores_remaining_die(self):
        self.begin("human")
        self.assertEqual(self.step("roll"), 200)
        before = self.session.snapshot()
        self.assertEqual(before["rolls"], [6, 1])
        with self.assertRaises(ValueError):
            self.step("move", move=-1)
        self.assertEqual(self.step("move", move=0), 200)
        restored = GameSession(self.save).snapshot()
        self.assertEqual(restored["rolls"], [1])
        self.assertNotEqual(restored["points"], before["points"])
        self.assertEqual(restored["turn"], 0)
        self.assertEqual(len(restored["history"]), 1)
        self.assertEqual(before["rolls"], [6, 1])

    def test_stale_tabs_cannot_replay_a_move(self):
        self.begin("human")
        self.step("roll")
        request = {"action": "move", "move": 0, "revision": self.session.revision}
        self.assertEqual(self.session.dispatch(request), 200)
        self.assertEqual(self.session.dispatch(request), 409)
        self.assertEqual(len(self.session.snapshot()["history"]), 1)

    def test_computer_moves_then_passes_to_human(self):
        self.begin("computer")
        with self.assertRaises(ValueError):
            self.step("roll")
        for _ in range(4):
            self.assertEqual(self.step("computer"), 200)
        after = self.session.snapshot()
        self.assertEqual(after["turn"], 1)
        self.assertIsNone(after["rolls"])
        self.assertEqual(len(after["history"]), 2)


if __name__ == "__main__":
    unittest.main()
