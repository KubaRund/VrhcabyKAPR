from os import system, name


def clear():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


def start(app):
    if name == 'nt':
        system(f'start cmd /K "color D && python {app}"')
    else:
        system(f'gnome-terminal -- bash -c "python3 {app}"')
        system("osascript -e 'tell application" + '"Terminal"' + 'to do script' + f'"python3 {app}"' + "'")


def set_color(color):
    if name == 'nt':
        system(f'color {color}')

def kill_window():
    if name == 'nt':
        system('title kill_window')
        system('taskkill /f /fi "WINDOWTITLE eq kill_window"')
