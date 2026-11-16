import random


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

    def choose_option(self, options):
        priority = {"END": 0, "KILL": 1, "SAVE": 2, "MOVE": 3}
        return min(range(len(options)), key=lambda index: priority[options[index][3]]) + 1
