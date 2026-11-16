import random

from board import BAR, OFF, apply_option, opponent


def position_score(points, color):
    direction = 1 if color == "W" else -1
    enemy = opponent(color)
    home = range(18, 24) if color == "W" else range(6)
    score = points[OFF[color]] * direction * 36 - points[BAR[enemy]] * direction * 18
    for point, count in enumerate(points[:24]):
        own = count * direction
        if own > 0:
            score += own * (point + 1 if direction > 0 else 24 - point)
        if own >= 2 and point in home:
            score += 3
        if own == 1:
            incoming = range(point + direction, point + 7 * direction, direction)
            threats = sum(points[index] * direction < 0 for index in incoming if 0 <= index < 24)
            if points[BAR[enemy]] and point in home:
                threats += 1
            score -= 6 * threats
    return score


def choose_num(prompt, count):
    choices = {str(index): index for index in range(1, count + 1)}
    while True:
        value = input(prompt).strip()
        if value in choices:
            return choices[value]
        print(f"Zadej číslo od 1 do {count}.")


class Dice:
    def __init__(self):
        self.rolls = []

    def roll(self, opening_rolls=()):
        first, second = opening_rolls or (random.randint(1, 6), random.randint(1, 6))
        self.rolls = [first] * 4 if first == second else [first, second]


class Player:
    def __init__(self, player_type, player_name, player_color):
        self.name = player_name
        self.color = player_color
        self.type = player_type
        self.dices = Dice()

    def choose_option(self, options, board):
        position = board.position()
        choice = max(
            range(len(options)),
            key=lambda index: position_score(apply_option(position, options[index], self.color), self.color),
        )
        return choice + 1
