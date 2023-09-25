import random
from time import sleep


class Player:
    def __init__(self, player_type, player_name, player_color):
        self.name = player_name
        self.color = player_color
        self.type = player_type
        self.dices = self.Dices()
        self.options = []

    class Dices:
        def __init__(self):
            self.rolls = [0, 0]
            self.double = False

        def roll(self):
            dice_1 = random.randint(1, 6)
            dice_2 = random.randint(1, 6)
            self.rolls = [dice_1, dice_2, 0, 0]
            self.double = False
            if dice_1 == dice_2:
                self.double = True
                self.rolls = [dice_1, dice_2, dice_1, dice_2]

        def show(self):
            if self.double:
                print(f"┌───┐ ┌───┐ ┌───┐ ┌───┐")
                print(f"│ {self.rolls[0]} │ │ {self.rolls[1]} │ │ {self.rolls[2]} │ │ {self.rolls[3]} │")
                print(f"└───┘ └───┘ └───┘ └───┘")
            else:
                print(f"┌───┐ ┌───┐")
                print(f"│ {self.rolls[0]} │ │ {self.rolls[1]} │")
                print(f"└───┘ └───┘")

    def choose_option(self, text, options):
        if self.type == "Parní stroj":
            sleep(1)
            found = False
            for i in range(0, len(options)):
                if "END" in options[i]:
                    choose = i + 1
                    found = True
                    break
            if not found:
                for i in range(0, len(options)):
                    if "SAVE" in options[i]:
                        choose = i + 1
                        found = True
            if not found:
                for i in range(0, len(options)):
                    if "KILL" in options[i]:
                        choose = i + 1
                        found = True
                        break
            if not found:
                choose = 1
        else:
            while True:
                user_input = input(text)
                if user_input.isdigit():
                    choose = int(user_input)
                    if 1 <= choose <= len(options):
                        break
                    else:
                        print("špatně zkus znovu")
                else:
                    print("vyber číslo")
        return choose








