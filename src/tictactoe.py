# Tic tac toe
import itertools
import random
import re
from string import ascii_lowercase

import pandas as pd

BLANK = ''


class TicTacToe:
    lines = (
        # Horizontal
        ('a1', 'b1', 'c1'),
        ('a2', 'b2', 'c2'),
        ('a3', 'b3', 'c3'),

        # Vertical
        ('a1', 'a2', 'a3'),
        ('b1', 'b2', 'b3'),
        ('c1', 'c2', 'c3'),

        # Diagonal
        ('a1', 'b2', 'c3'),
        ('a3', 'b2', 'c1'))

    def __init__(self):
        print("Welcome to TicTacToe!")
        self.board = pd.DataFrame(
            index=range(1, 4), columns=list(ascii_lowercase[:3]),
            data=BLANK)
        self.chars = ['X', 'O', 'X', 'O', 'X', 'O', 'X', 'O', 'X']

        self.next_char = 'X'
        self.play()

    def display(self):
        print(self.board)

    def place(self, row_ix, col_ix):
        self.board.loc[row_ix, col_ix] = self.chars.pop()

    def play(self):
        while self.winner is None:
            self.display()
            next_char = self.chars[-1]
            print(f"Choose a square to play (i.e. '1a', 'c3', 'B1')"
                  f" your {next_char}.")
            coord = input('> ')
            i, j = self.parse_coord(coord)
            self.board.loc[i, j] = self.chars.pop()
        self.display()
        print(f"{self.winner} wins!")

    @staticmethod
    def parse_coord(coord):
        try:
            letter = re.search(r'[A-z]+', coord).group(0).lower()
            number = int(re.search(r'[0-9]+', coord).group(0))
            return number, letter
        except AttributeError as e:
            if "has no attribute 'group'" not in str(e):
                raise
            input("Invalid input.")

    @property
    def winner(self):
        for line in self.lines:
            coords = [self.parse_coord(coord) for coord in line]
            vals = [self.board.loc[i, j] for i, j in coords]
            if all([val == 'X' for val in vals]):
                return 'X'
            elif all([val == 'O' for val in vals]):
                return 'O'
        return None


if __name__ == '__main__':
    TicTacToe()
