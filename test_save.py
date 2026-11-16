import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from board import OFF, Board
from main import HUMAN, Game
from player import Player


class SaveGameTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.save_path = Path(temporary.name) / "partie.json"
        self.game = Game(Board(), self.save_path)
        self.game.players = [Player(HUMAN, "Bílý", "W"), Player(HUMAN, "Černý", "K")]

    def launch(self, keys):
        return subprocess.run(
            [sys.executable, "-X", "utf8", str(Path(__file__).with_name("main.py")), "--uloha", str(self.save_path)],
            input=keys, capture_output=True, encoding="utf-8", timeout=10, check=True,
        ).stdout

    def test_cli_restores_move_and_remaining_die(self):
        self.game.opening_rolls = [6, 1]
        self.game.save_game()

        self.assertIn("Bílý: ", self.launch("2\n1\n"))
        self.game.load_game()
        first_move, = self.game.progress
        end = first_move["move"][1]
        self.assertEqual((self.game.next_player, self.game.remaining_rolls), (0, [1]))
        self.assertEqual(self.game.board.stacks[end].stack[-1].color, "W")

        self.assertIn("Zbývající kostky: 1", self.launch("2\n1\n"))
        self.game.load_game()
        self.assertEqual(self.game.next_player, 1)
        self.assertEqual(len(self.game.progress), 2)
        self.assertEqual(self.game.progress[0], first_move)

    def test_interrupted_doubles_keep_unused_moves(self):
        with redirect_stdout(io.StringIO()), patch("player.random.randint", return_value=5):
            with patch("main.choose_num", side_effect=[1, KeyboardInterrupt]):
                with self.assertRaises(KeyboardInterrupt):
                    self.game.play()
        self.game.load_game()
        self.assertEqual(self.game.remaining_rolls, [5, 5, 5])
        self.assertEqual(len(self.game.progress), 1)

    def test_save_from_previous_version_starts_at_turn_boundary(self):
        self.game.next_player = 1
        self.game.save_game()
        data = json.loads(self.save_path.read_text(encoding="utf-8"))
        del data["remaining_rolls"]
        self.save_path.write_text(json.dumps(data), encoding="utf-8")

        self.game.load_game()
        self.assertEqual(self.game.next_player, 1)
        self.assertIsNone(self.game.remaining_rolls)

    def test_save_retries_when_windows_temporarily_locks_file(self):
        original_replace = Path.replace
        file_busy = PermissionError("The save is temporarily locked")
        file_busy.winerror = 32
        attempts = []

        def replace(source, target):
            attempts.append(target)
            if len(attempts) == 1:
                raise file_busy
            original_replace(source, target)

        with patch.object(Path, "replace", replace), patch("main.sleep"):
            self.game.save_game()
        self.assertEqual(attempts, [self.save_path, self.save_path])
        self.game.load_game()

    def test_play_ends_when_last_checker_is_borne_off(self):
        white = self.game.board.stones["W"]
        for stone in white[:-1]:
            stone.place_history = [OFF["W"]]
        white[-1].place_history = [22]
        self.game.board.stacks = self.game.board.make_stacks()
        self.game.opening_rolls = [6, 1]

        with redirect_stdout(io.StringIO()) as output, patch("main.choose_num", return_value=1):
            self.game.play()
        self.assertIn("Vyhrává Bílý", output.getvalue())
        self.assertNotIn("Žádný další tah", output.getvalue())
        self.game.load_game()
        self.assertEqual(self.game.winner().color, "W")


if __name__ == "__main__":
    unittest.main()
