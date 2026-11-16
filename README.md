# Vrhcáby

Terminálové vrhcáby od Moura a Runda. Projekt vznikl v předmětu KAPR2 na UJEP v letech 2022/2023.

## Spuštění

Stačí Python 3.10 nebo novější. Ve složce projektu spusť `python main.py`. Každou stranu může hrát člověk nebo počítač označený jako „Parní stroj“. Čísla tahů a jejich popis se zobrazí pod deskou.

Hra se ukládá do `save_file.json` na konci každého tahu hráče. Pro jiný soubor použij například `python main.py --uloha partie.json`. V menu lze pokračovat z posledního uloženého tahu. Starší platná uložení můžeš otevřít výběrem stejného souboru. `python progress.py` vypíše uložené tahy. Podporuje i výslovnou cestu, například `python progress.py partie.json`.

Pro rychlejší hru počítačů spusť `python main.py --rychle`.

## Pravidla

Hraje se jedna partie. Kameny na baru se vracejí před všemi ostatními tahy. Musí se využít co nejvíc kostek. Pokud z běžného hodu jde využít jen jednu z obou hodnot, hraje se vyšší dostupná hodnota. Dvojice stejné hodnoty se hraje až čtyřikrát. Vyhrává hráč, který vynese všech 15 kamenů. Hra rozlišuje běžnou výhru, gammon a backgammon.

[Pravidla vrhcábů](https://cs.wikipedia.org/wiki/Vrhc%C3%A1by)
