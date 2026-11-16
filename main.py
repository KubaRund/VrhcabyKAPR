import argparse
import json
import random
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

from board import BAR, OFF, Board, load_stone_objects, opponent
from player import Player, choose_num
from progress import DEFAULT_SAVE, format_move


HUMAN = "Člověk"
COMPUTER = "Parní stroj"


class Game:
    def __init__(self, board, save_path=DEFAULT_SAVE, delay=0.25):
        self.board = board
        self.save_path = save_path
        self.delay = delay
        self.players = []
        self.progress = []
        self.next_player = 0
        self.opening_rolls = []

    def winner(self):
        return next(
            (player for player in self.players if len(self.board.stacks[OFF[player.color]].stack) == 15),
            None,
        )

    def win_type(self, winner):
        loser_color = opponent(winner.color)
        stacks = self.board.stacks
        if stacks[OFF[loser_color]].stack:
            return "běžná výhra"
        winner_home = range(18, 24) if winner.color == "W" else range(6)
        if stacks[BAR[loser_color]].stack or any(
            stacks[point].stack and stacks[point].stack[0].color == loser_color for point in winner_home
        ):
            return "backgammon"
        return "gammon"

    def player_round(self, player, opening_rolls=()):
        player.dices.roll(opening_rolls)
        print(f"\nNa řadě je {player.name}. Hod: {', '.join(map(str, player.dices.rolls))}")
        while player.dices.rolls:
            options = self.board.check_options(player)
            if not options:
                print("Žádný další tah není možný.")
                break
            if player.type == HUMAN:
                self.board.show(*self.players)
                for index, move in enumerate(options, 1):
                    print(f"{index}. {format_move(move)}")
                choice = choose_num("Vyber tah: ", len(options))
            else:
                choice = player.choose_option(options)
                sleep(self.delay)
            move = options[choice - 1]
            self.board.play_option(move, player.color)
            self.progress.append({"player": player.name, "move": list(move)})
            player.dices.rolls.remove(move[2])
            print(f"{player.name}: {format_move(move)}")

    def new_game(self):
        self.board.reset()
        self.players = []
        for index in range(2):
            print(f"\nHráč {index + 1}")
            kind = choose_num("1. Člověk, 2. Parní stroj: ", 2)
            name = input("Jméno hráče: ").strip() or f"Hráč {index + 1}"
            if index == 0:
                color = "W" if choose_num("1. Bílá, 2. Černá: ", 2) == 1 else "K"
            else:
                color = opponent(self.players[0].color)
            self.players.append(Player(HUMAN if kind == 1 else COMPUTER, name, color))
        self.progress = []
        rolls = [0, 0]
        while rolls[0] == rolls[1]:
            rolls = [random.randint(1, 6), random.randint(1, 6)]
        self.next_player = int(rolls[1] > rolls[0])
        self.opening_rolls = sorted(rolls, reverse=True)
        self.save_game()

    def save_game(self):
        data = {
            "progress": self.progress,
            "stones": {
                color: [[stone.place_history, stone.deaths] for stone in stones]
                for color, stones in self.board.stones.items()
            },
            "next_player": self.next_player,
            "opening_rolls": self.opening_rolls,
        }
        for index, player in enumerate(self.players, 1):
            data[f"player_{index}"] = {"name": player.name, "type": player.type, "color": player.color}

        pending = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.save_path.parent,
                prefix=f".{self.save_path.name}.", suffix=".tmp", delete=False,
            ) as stream:
                pending = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False)
            pending.replace(self.save_path)
        finally:
            if pending is not None:
                pending.unlink(missing_ok=True)

    def load_game(self):
        data = json.loads(self.save_path.read_text(encoding="utf-8"))
        stones = load_stone_objects(data["stones"])
        for color, collection in stones.items():
            if len(collection) != 15:
                raise ValueError("Uložená partie musí obsahovat 15 kamenů každé barvy.")
            valid_positions = (*range(24), BAR[color], OFF[color])
            for stone in collection:
                if not stone.place_history or any(
                    type(point) is not int or point not in valid_positions for point in stone.place_history
                ) or type(stone.deaths) is not int or stone.deaths < 0:
                    raise ValueError("Uložená partie obsahuje neplatnou pozici nebo historii kamene.")
        board = Board()
        board.stones = stones
        board.stacks = board.make_stacks()
        if any(len({stone.color for stone in place.stack}) > 1 for place in board.stacks):
            raise ValueError("Uložená partie obsahuje kameny obou barev na stejném bodě.")
        players = []
        for key in ("player_1", "player_2"):
            row = data[key]
            if row["type"] not in (HUMAN, COMPUTER) or not isinstance(row["name"], str):
                raise ValueError("Uložená partie obsahuje neplatného hráče.")
            players.append(Player(row["type"], row["name"], row["color"]))
        if {player.color for player in players} != {"W", "K"}:
            raise ValueError("Každý hráč musí mít jinou barvu.")

        turn = data.get("next_player", 0)
        opening = data.get("opening_rolls", [])
        progress = data["progress"]
        if type(turn) is not int or turn not in (0, 1) or not isinstance(opening, list):
            raise ValueError("Uložená partie obsahuje neplatný tah.")
        if opening and (len(opening) != 2 or opening[0] == opening[1] or any(
            type(die) is not int or not 1 <= die <= 6 for die in opening
        )):
            raise ValueError("Uložená partie obsahuje neplatný zahajovací hod.")
        if not isinstance(progress, list):
            raise ValueError("Uložená partie obsahuje neplatnou historii tahů.")
        self.board = board
        self.players = players
        self.progress = progress
        self.next_player = turn
        self.opening_rolls = opening

    def play(self):
        while not (winner := self.winner()):
            self.player_round(self.players[self.next_player], self.opening_rolls)
            self.opening_rolls = []
            self.next_player = 1 - self.next_player
            self.save_game()
        self.board.show(*self.players)
        print(f"Vyhrává {winner.name} – {self.win_type(winner)}.")
        for player in self.players:
            stones = self.board.stones[player.color]
            hits = sum(stone.deaths > 0 for stone in stones)
            print(f"{player.name}: {hits} vyhozených kamenů, celkem {sum(stone.deaths for stone in stones)} vyhození.")

    def start(self):
        while True:
            print("\nVrhcáby podle Moura a Runda · KAPR2, UJEP 2022/2023")
            choice = choose_num("1. Nová hra\n2. Načíst hru\n3. Konec\nVyber možnost: ", 3)
            if choice == 3:
                return
            try:
                if choice == 1:
                    self.new_game()
                else:
                    self.load_game()
                self.play()
            except FileNotFoundError:
                print(f"Uloženou partii nebo její složku se nepodařilo najít ({self.save_path}).")
            except (OSError, ValueError, IndexError, KeyError, TypeError) as error:
                print(f"S uloženou partií se nepodařilo pracovat: {error}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Vrhcáby pro dva hráče v terminálu.")
    parser.add_argument("--uloha", type=Path, default=DEFAULT_SAVE, help="cesta k uložené partii")
    parser.add_argument("--rychle", action="store_true", help="vynechá prodlevu tahů počítače")
    args = parser.parse_args(argv)
    try:
        Game(Board(), args.uloha, delay=0 if args.rychle else 0.25).start()
    except (EOFError, KeyboardInterrupt):
        print("\nKonec hry. Uložená partie obsahuje poslední dokončený tah hráče.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
