from time import sleep
import os_comands as os
import json
import colorama as cl


def set_color(line, move_type):
    cl.init()
    match move_type:
        case "KILL":
            line = cl.Fore.LIGHTRED_EX + line
        case "SAVE":
            line = cl.Fore.GREEN + line
        case "END":
            line = cl.Fore.YELLOW + line
        case "move":
            line = cl.Fore.WHITE + line
    return line


def show_data():
    print("PROGRESS:\ntoto je progres hry vrhcáby \n\n---------------------\n")
    data = read_progress()
    for index in range(0, len(data)):
        line = data[index]
        player_name = line[0]
        option = line[1]
        line = "\n" if index > 0 and data[index - 1][0] != player_name else ""
        line += f"{player_name}: {option[0]} -> {option[1]}, [{option[2]}] - {option[3]}"
        line = set_color(line, option[3])
        print(line)


def show_last_line():
    data = read_progress()
    line = data[-1]
    player_name = line[0]
    option = line[1]
    line = "\n" if len(data) > 1 and player_name != data[-2][0] else ""
    line += f"{player_name}: {option[0]} -> {option[1]}, [{option[2]}] - {option[3]}"
    line = set_color(line, option[3])
    print(line)


def check_exit():
    with open('exit.json', 'r') as file:
        status = json.load(file)
    return True if status else False


def read_progress():
    with open("progress.json", "r") as file:
        read = json.load(file)
    return read


show_data()
progress = read_progress()
while not check_exit():
    sleep(1)
    if progress != read_progress():
        show_last_line()
        progress = read_progress()
os.kill_window()
