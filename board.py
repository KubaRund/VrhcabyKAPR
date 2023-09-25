from stone import Stone


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


def delete_duplicate_options(options):
    final_options = []
    for option in options:
        if option not in final_options:
            final_options.append(option)
    return final_options


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

    def move_stone(self, from_place, to_place, player):  # Pohyb kamene na desce
        stacks = self.stacks
        color = player.color
        from_place = 25 if from_place == "BAR" and color == "W" else from_place
        from_place = 26 if from_place == "BAR" and color == "K" else from_place
        to_place = 25 if to_place == "BAR" and color == "W" else to_place
        to_place = 26 if to_place == "BAR" and color == "K" else to_place
        to_place = 27 if to_place == "OFF" and color == "W" else to_place
        to_place = 28 if to_place == "OFF" and color == "K" else to_place
        stacks[to_place - 1].stack.append(stacks[from_place - 1].stack.pop())
        self.update_stones()

    def update_stones(self):
        for place_i in range(0, 28):
            bars_i = [24, 25]
            place_stack = self.stacks[place_i].stack
            for stone_object in place_stack:
                history = stone_object.place_history
                if history[-1] != place_i:
                    history.append(place_i)
                    if place_i in bars_i:
                        stone_object.deaths += 1

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

    def check_home_board(self, player):  # metoda která kontroluje zda jsou kameny hráče v ohradě
        stacks = self.stacks
        home_board = range(18, 24) if player.color == "W" else range(0, 6)
        off = stacks[26].stack if player.color == "W" else stacks[27].stack
        suma = len(off)
        for index in home_board:
            home_place = stacks[index].stack
            suma += len(home_place) if home_place and home_place[0].color == player.color else 0
        return True if suma == 15 else False

    def last_stone_index(self, player):  # vrací index nejvzdálenejšího kamene
        board = range(0, 24) if player.color == "W" else range(23, -1, -1)
        last_stone_i = board[23]
        for index in reversed(board):
            place = self.stacks[index].stack
            last_stone_i = index if place and place[0].color == player.color else last_stone_i
        return last_stone_i

    def check_options(self, player):  # generuje možnosti tahu v zavislostích
        options = []
        stacks = self.stacks
        rolls = [roll for roll in player.dices.rolls if roll != 0]
        bar = stacks[24].stack if player.color == "W" else stacks[25].stack
        board = range(0, 24) if player.color == "W" else range(23, -1, -1)

        if bar:                        # Generování možností pro vracení kamenů hráče z baru
            for roll in rolls:
                place_i = board[roll - 1]
                place = stacks[place_i].stack
                if len(place) == 1 and player.color != place[0].color:
                    options.append(["BAR", place_i + 1, roll, "Odstranit"])
                elif len(place) == 1 and player.color == place[0].color:
                    options.append(["BAR", place_i + 1, roll, "Uchránit"])
                elif not place or (place and player.color == place[0].color):
                    options.append(["BAR", place_i + 1, roll, "Běžný přesun"])
        else:


            # Generování možností pro pohyb z vrcholů na desce
            home_board_check = self.check_home_board(player)
            last_stone_i = self.last_stone_index(player)
            for num in range(1, 25):
                place_i = board[num - 1]
                place = stacks[place_i].stack
                if place and place[0].color == player.color:
                    for roll in rolls:
                        if num + roll > 24:
                            if home_board_check and (num + roll == 25 or (num + roll > 25 and place_i == last_stone_i)):
                                options.append([place_i + 1, "OFF", roll, "END"])
                        else:
                            to_place_i = board[num - 1 + roll]
                            to_place = stacks[to_place_i].stack
                            if len(to_place) == 1 and player.color != to_place[0].color:
                                options.append([place_i + 1, to_place_i + 1, roll, "Odstranit"])
                            elif (len(to_place) == 1 and player.color == to_place[0].color) \
                                    or (to_place and player.color == to_place[0].color and len(place) == 1):
                                options.append([place_i + 1, to_place_i + 1, roll, "Uchránit"])
                            elif not to_place or (to_place and to_place[0].color == player.color):
                                options.append([place_i + 1, to_place_i + 1, roll, "Běžný přesun"])



        final_options = delete_duplicate_options(options)
        player.options = final_options
        return final_options

    def print_options(self, player):
        options = self.check_options(player)
        if len(options) == 0:
            pass
        else:
            num = 1
            print(f"možnosti tahu ({player.color}):")
            print("-----------------------------------------------")
            for option in options:
                print(f"{num}:   {option[0]} -> {option[1]}, [{option[2]}], {option[3]}")
                num += 1
            print("-----------------------------------------------")
