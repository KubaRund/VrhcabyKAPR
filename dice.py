import random
from typing import Iterator

class Dice:
    def __init__(self) -> None:
        self.rolls = []
        self.total_rolls = 0
    
    def roll(self) -> int:
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6)
        self.total_rolls += 1
        if roll1 == roll2:
            self.rolls.append((roll1, roll1, roll1, roll1))
            roll = roll1 * 4
            return roll
        else:
            self.rolls.append((roll1, roll2))
            roll = roll1 + roll2
            return roll
    
    def __repr__(self) -> str:
        return f'Dice[rolls={self.rolls},total_rolls={self.total_rolls}]'

    def __str__(self) -> str:
        return f'Hozeno {self.rolls[-1]}'
    
    def __len__(self) -> int:
        return self.total_rolls
    
    def __iter__(self) -> Iterator:
        return iter(self.rolls)