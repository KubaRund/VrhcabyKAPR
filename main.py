from time import sleep
import os_comands as os
import board as bd
import player as pl
import json


def exit_apps():
    with open('exit.json', 'w') as f:
        data = True
        json.dump(data, f)
    sleep(1)
    with open('exit.json', 'w') as f:
        data = False
        json.dump(data, f)
    os.set_color("0E")
    os.clear()

def write_progress(player, option):
    with open("progress.json", "r") as file:
        data = json.load(file)
    data.append([player.name, option])
    with open("progress.json", "w") as file:

        json.dump(data, file)


def reset_progress():
    with open("progress.json", "w") as file:
        json.dump([], file)


def choose_num(text, options):
    while True:
        user_input = input(text)
        if user_input.isdigit():
            choose = int(user_input)
            if 1 <= choose <= len(options):
                break
            else:
                print("Špatná možnost")
        else:
            print("Vyber číslo")
    return choose


class Game:
    def __init__(self, game_board):
        self.player_1 = None
        self.player_2 = None
        self.board = game_board

    def won(self):
        if len(self.board.stacks[26].stack) == 15 or len(self.board.stacks[27].stack) == 15:
            return True
        return False

    def winner(self):
        off_w = self.board.stacks[26].stack
        off_k = self.board.stacks[27].stack
        win_type = None
        if self.won():
            win_off = off_w if len(off_w) == 15 else off_k
            winner = self.player_1 if win_off[0].color == self.player_1.color else self.player_2
            loser = self.player_1 if winner == self.player_2 else self.player_2
            lose_off = off_k if len(off_w) == 15 else off_w
            if lose_off:
                win_type = "běžná výhra !"
            elif not lose_off and self.board.check_home_board(loser):
                win_type = "Gammon!"  #dvojnásobná výhra.
            else:
                win_type = "Backgammon!!"  #trojnásobná výhra
            os.clear()
            self.board.show(self.player_1, self.player_2)
            print(f"{winner.name} won -> {win_type}.\n")
            self.statistics()

    def player_round(self, player):
        player.dices.roll()
        while True:
            if max(player.dices.rolls) == 0:
                break
            os.clear()
            print(f"na řadě je {player.name}.")
            self.board.show(self.player_1, self.player_2)
            sleep(0.5)
            player.dices.show()
            self.board.print_options(player)
            if len(player.options) > 0:
                choose = player.choose_option("vyber možnost: ", player.options)
            else:
                print(f"žádné možnosti nejsou pro: {player.name}")
                sleep(2)
                break
            print(f"{player.name} vybral: {choose}")
            sleep(1) if player.type == "Parní stroj" else sleep(1)
            move_type = player.options[choose - 1][3]
            if move_type == "KILL":
                self.board.move_stone(player.options[choose - 1][1], "BAR",
                                      self.player_2 if player == self.player_1 else
                                      self.player_1)
            self.board.move_stone(player.options[choose - 1][0], player.options[choose - 1][1], player)
            write_progress(player, player.options[choose - 1])
            rolls = player.dices.rolls
            roll = player.options[choose - 1][2]
            rolls[rolls.index(roll)] = 0

    def set_player(self, num_of_player):
        print(f"Hráč číslo {num_of_player}.\n")
        p_type_num = choose_num(f"vyber si postavu {num_of_player} zadej buď (1-Člověk, 2-Parní stroj): ", [1, 2])
        p_type = "Člověk" if p_type_num == 1 else "Parní stroj"
        p_name = input("vyber jméno parního stroje: ")
        if num_of_player == 1:
            p_color_num = choose_num(f"vyber barvu postavy {num_of_player}  (1-Bílá(W), 2-Černá(K)): ", [1, 2])
            p_color = "W" if p_color_num == 1 else "K"
        else:
            p_color = "W" if self.player_1.color == "K" else "K"
        new_player = pl.Player(p_type, p_name, p_color)
        return new_player

    def save_game(self):
        stones = self.board.stones
        with open("progress.json", "r") as file:
            progress = json.load(file)
        data = {
            "progress": progress,
            "stones": {
                "W": [],
                "K": []
            },
            "player_1": {
                "name": self.player_1.name,
                "type": self.player_1.type,
                "color": self.player_1.color
            },
            "player_2": {
                "name": self.player_2.name,
                "type": self.player_2.type,
                "color": self.player_2.color
            }
        }
        for color in ["W", "K"]:
            for stone_object in stones[color]:
                data["stones"][color].append([stone_object.place_history, stone_object.deaths])
        with open('save_file.json', 'w') as file:
            json.dump(data, file)

    def load_game(self):
        os.clear()
        os.set_color("0F")
        with open('save_file.json', 'r') as file:
            data = json.load(file)
        progress = data["progress"]
        with open('progress.json', 'w') as file:
            json.dump(progress, file)
        self.board.stones = bd.load_stone_objects(data["stones"])
        self.board.stacks = self.board.make_stacks()
        self.player_1 = pl.Player(data["player_1"]["type"], data["player_1"]["name"], data["player_1"]["color"])
        self.player_2 = pl.Player(data["player_2"]["type"], data["player_2"]["name"], data["player_2"]["color"])

    def new_game(self):
        os.clear()
        reset_progress()
        self.board.reset()
        self.player_1 = self.set_player(1)
        self.player_2 = self.set_player(2)

    def play(self):
        os.clear()
        os.set_color("F0")
        os.start("progress.py")
        while not game.won():
            self.player_round(self.player_1)
            if not game.won():
                self.player_round(self.player_2)
            self.save_game()
        self.winner()

    def statistics(self):
        os.set_color("B2")
        print("    Statistika\n   ------------")
        for player in [self.player_1, self.player_2]:
            player_deaths = 0
            killed_stones = 0
            player_averages = []
            for stone in self.board.stones[player.color]:
                stone_moves = len(stone.place_history) - 1
                killed_stones += 1 if stone.deaths > 0 else 0
                player_deaths += stone.deaths
                player_averages.append(stone_moves / (stone.deaths + 1))
            print(f" {player.name} ({player.color}):\n"
                  f"   smrti: {player_deaths}\n"
                  f"   zabité kameny: {killed_stones}\n"
                  f"   průměrná životnost : {int(sum(player_averages)/len(player_averages))}\n"
                  )
        input("\nZmáčkni ENTER ")

    def start(self):
        try:
            while True:
                exit_apps()
                print("\nVrhcáby podle Moura a Runda předmět KAPR2 na UJEP 2022/2023\ndélka hry 5-30min\ndoporučený věk od 5 let\n\n 1. Nová hra\n 2. Nahraj Hru\n 3. Odejdi\n")
                choose = choose_num("vyber možnost: ", [1, 2, 3])
                match choose:
                    case 1:
                        self.new_game()
                        self.play()
                    case 2:
                        self.load_game()
                        self.play()
                    case 3:
                        exit_apps()
                        exit()
        except KeyboardInterrupt:
            self.start()


if __name__ == '__main__':
    board = bd.Board()
    game = Game(board)
    game.start()
