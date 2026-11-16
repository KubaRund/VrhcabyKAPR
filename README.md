# Vrhcáby

Vrhcáby od Moura a Runda pro dva hráče nebo hru proti počítači. Projekt vznikl v předmětu KAPR2 na UJEP v letech 2022/2023.

## Grafická hra

Přenosný balíček pro 64bitové Windows rozbal a otevři `Spustit-vrhcaby.cmd`. Z tohoto repozitáře lze hru spustit příkazem `python web.py` s nainstalovaným Pythonem 3.10 nebo novějším. V prohlížeči se otevře `http://127.0.0.1:8765`. Hra funguje i bez připojení k internetu.

Po hodu vyber kámen přímo na desce a klepni na zvýrazněný bod. Stejný přesun jde vybrat v seznamu povolených tahů. Tlačítko **Nápověda** označí tah navržený počítačem. V panelu hráče vidíš počet vynesených kamenů i součet kroků, které ještě zbývají do cíle.

## Terminál a uložené partie

Ve složce projektu spusť `python main.py`. Čísla tahů a jejich popis se zobrazí pod deskou. Pro rychlejší hru počítačů použij `python main.py --rychle`.

Obě verze používají `save_file.json`. Po načtení se obnoví pozice, hráč na řadě i zbývající kostky. Grafická verze poslední partii otevře automaticky. V terminálu zvol **Načíst hru**. Pro souběžné partie použij různé soubory, například `python web.py --uloha partie.json`.

Uložení starších verzí se načtou od začátku příslušného tahu. `python progress.py partie.json` vypíše uložené přesuny.

## Pravidla

Hraje se jedna partie. Kameny na baru se vracejí před všemi ostatními tahy. Musí se využít co nejvíc kostek. Pokud z běžného hodu jde využít jen jednu z obou hodnot, hraje se vyšší dostupná hodnota. Dvojice stejné hodnoty se hraje až čtyřikrát. Vyhrává hráč, který vynese všech 15 kamenů. Hra rozlišuje běžnou výhru, gammon a backgammon.

[Pravidla vrhcábů](https://cs.wikipedia.org/wiki/Vrhc%C3%A1by)

## Ověření

`python -m unittest` spustí testy ukládání a herních kroků.
