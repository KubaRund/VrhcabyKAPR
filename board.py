from functools import cache

from stone import Stone


BAR = {"W": 24, "K": 25}
OFF = {"W": 26, "K": 27}
MOVE_LABELS = {
    "KILL": "Vyhození na bar",
    "SAVE": "Zajištění bodu",
    "END": "Vynesení kamene",
    "MOVE": "Běžný přesun",
}


def opponent(color):
    return "K" if color == "W" else "W"


def single_moves(points, color, roll):
    direction = 1 if color == "W" else -1
    order = range(24) if direction == 1 else range(23, -1, -1)
    bar, off = BAR[color], OFF[color]
    if points[bar]:
        start_points = (bar,)
    else:
        start_points = [point for point in order if points[point] * direction > 0]
    for start in start_points:
        end = order[roll - 1] if start == bar else start + direction * roll
        if not 0 <= end < 24:
            if start_points[0] in order[18:] and (end in (-1, 24) or start == start_points[0]):
                yield (start, off, roll, "END")
            continue
        occupants = points[end] * direction
        if occupants < -1:
            continue
        kind = "KILL" if occupants == -1 else "SAVE" if occupants == 1 else "MOVE"
        yield (start, end, roll, kind)


def apply_option(points, option, color):
    start, end, _, kind = option
    direction = 1 if color == "W" else -1
    updated = list(points)
    if kind == "KILL":
        updated[end] = 0
        updated[BAR[opponent(color)]] -= direction
    updated[start] -= direction
    updated[end] += direction
    return tuple(updated)


def allowed_turn_options(points, color, rolls):
    @cache
    def max_moves(position, remaining):
        best = 0
        for die in dict.fromkeys(remaining):
            rest = without_roll(remaining, die)
            for move in single_moves(position, color, die):
                best = max(best, 1 + max_moves(apply_option(position, move, color), rest))
                if best == len(remaining):
                    return best
        return best

    scored = []
    for die in dict.fromkeys(rolls):
        rest = without_roll(rolls, die)
        for move in single_moves(points, color, die):
            total = 1 + max_moves(apply_option(points, move, color), rest)
            scored.append(((total, die if total == 1 else 0), move))
    if not scored:
        return []
    best = max(score for score, _ in scored)
    return [move for score, move in scored if score == best]


def without_roll(rolls, die):
    index = rolls.index(die)
    return rolls[:index] + rolls[index + 1:]


def load_stone_objects(stones):
    objects = {
        "W": [],
        "K": []
    }
    for color in ["W", "K"]:
        for stone_data in stones[color]:
            objects[color].append(Stone(color, stone_data[0], stone_data[1]))
    return objects


def new_stones():  # Vytvoří novou sadu kamenů s jejich pozicemi
    stones = {
        "W": [Stone("W", [0], 0), Stone("W", [0], 0), Stone("W", [11], 0), Stone("W", [11], 0), Stone("W", [11], 0),
              Stone("W", [11], 0), Stone("W", [11], 0), Stone("W", [16], 0), Stone("W", [16], 0), Stone("W", [16], 0),
              Stone("W", [18], 0), Stone("W", [18], 0), Stone("W", [18], 0), Stone("W", [18], 0), Stone("W", [18], 0)],
        "K": [Stone("K", [5], 0), Stone("K", [5], 0), Stone("K", [5], 0), Stone("K", [5], 0), Stone("K", [5], 0),
              Stone("K", [7], 0), Stone("K", [7], 0), Stone("K", [7], 0), Stone("K", [12], 0), Stone("K", [12], 0),
              Stone("K", [12], 0), Stone("K", [12], 0), Stone("K", [12], 0), Stone("K", [23], 0), Stone("K", [23], 0)]
    }
    return stones


class Board:
    def __init__(self):
        self.stones = new_stones()
        self.stacks = self.make_stacks()

    class Place:
        def __init__(self, stack):
            self.stack = stack

    def reset(self):  # Reset celé desky
        self.stones = new_stones()
        self.stacks = self.make_stacks()

    def make_stacks(self):  # Vytvoří novou sadu vrcholů
        places = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [],
                  [], [], [], []]
        stones = self.stones
        for color in ["W", "K"]:
            for stone_object in stones[color]:
                places[stone_object.place_history[-1]].append(stone_object)
        stacks = []
        for place in places:
            stacks.append(self.Place(place))
        return stacks

    def move_stone(self, start, end):
        stone = self.stacks[start].stack.pop()
        self.stacks[end].stack.append(stone)
        stone.place_history.append(end)
        if end == BAR[stone.color]:
            stone.deaths += 1

    def play_option(self, option, color):
        start, end, _, kind = option
        if kind == "KILL":
            self.move_stone(end, BAR[opponent(color)])
        self.move_stone(start, end)

    def show(self, player_1, player_2):  # metoda která vypisuje aktuální stav desky
        print(f"\n {player_1.name if player_1.color == 'W' else player_2.name} BAR: {self.stacks[24].stack}")
        print(" ---------------------------------------")
        print(" | 12 11 10  9  8  7  6  5  4  3  2  1 |")
        print(f" |-------------------------------------| {player_1.name if player_1.color == 'K' else player_2.name}"
              f" Domeček: {self.stacks[27].stack}")
        max_num = 5
        for i in range(0, 12):
            if len(self.stacks[i].stack) > max_num:
                max_num = len(self.stacks[i].stack)
        for i in range(0, max_num):
            layer = " "
            for j in range(11, -1, -1):
                place = self.stacks[j].stack
                if len(place) >= i + 1:
                    layer += (" " + str(place[i]) + " ")
                elif j in range(11, 0, -2):
                    layer += " - "
                else:
                    layer += "   "
            print(f" |{layer}|")
        print(" |                                     |")
        max_num = 5
        for i in range(12, 24):
            if len(self.stacks[i].stack) > max_num:
                max_num = len(self.stacks[i].stack)
        for i in range(max_num - 1, -1, -1):
            layer = " "
            for j in range(12, 24):
                place = self.stacks[j].stack
                if len(place) >= i + 1:
                    layer += (" " + str(place[i]) + " ")
                elif j in range(13, 24, 2):
                    layer += " - "
                else:
                    layer += "   "
            print(f" |{layer}|")
        print(
            f" |-------------------------------------| {player_1.name if player_1.color == 'W' else player_2.name}"
            f" Domeček: {self.stacks[26].stack}")
        print(" | 13 14 15 16 17 18 19 20 21 22 23 24 |")
        print(" ---------------------------------------")
        print(f" {player_1.name if player_1.color == 'K' else player_2.name} BAR: {self.stacks[25].stack}\n")

    def check_options(self, player):
        points = tuple(
            0 if not place.stack else len(place.stack) * (1 if place.stack[0].color == "W" else -1)
            for place in self.stacks
        )
        return allowed_turn_options(points, player.color, tuple(player.dices.rolls))
