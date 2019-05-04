# Minesweeper

# Board, max size 24 x 30
# Each square can be a mine, a number, or blank
# The numbered squares count the adjacent mines
import itertools
import random
import re
from string import ascii_lowercase

import pandas as pd

MINE = 'X'
BLANK = ''
HIDDEN = '-'


class Minesweeper:
    MAX_ROWS = 30
    MAX_COLS = 24
    MAX_MINE_PCT = .9
    WIN_MSG = "Congratulations!"
    LOSE_MSG = "Oh no, a mine! Game over!"
    PROG_MSG = "The game's still going!"

    def __init__(self):
        print("Welcome to Minesweeper! Please specify the following:")
        rows = min(
            int(input(f"Number of rows (max {self.MAX_ROWS}) > ")),
            self.MAX_ROWS)
        cols = min(
            int(input(f"Number of cols (max {self.MAX_COLS}) > ")),
            self.MAX_COLS)
        pct_mines = min(
            float(input(
                f"Percentage of tiles to have mines (between 0 and 1,"
                f" max {self.MAX_MINE_PCT}) > ")),
            self.MAX_MINE_PCT)

        self.arr = pd.DataFrame(
            index=range(rows), columns=list(ascii_lowercase[:cols]),
            data=BLANK)
        self.mask = pd.DataFrame(
            index=range(rows), columns=list(ascii_lowercase[:cols]),
            data=HIDDEN)
        self.game_over = False
        self.msg = self.PROG_MSG

        self.populate(pct_mines)  # Generate mines and counts

        self.already_revealed = []

        self.play()

    def display(self):
        print(self.mask)

    def reveal(self, row_ix, col_ix):
        # Get underlying value of specified square and pin to mask
        val = self.arr.loc[row_ix, col_ix]
        self.mask.loc[row_ix, col_ix] = val
        if val == MINE:
            print(self.arr)
            self.game_over = True
            self.msg = self.LOSE_MSG
        # Propagate, automatically play adjacent blank squares
        elif val == BLANK:
            i = row_ix
            j = ascii_lowercase.index(col_ix)
            self.already_revealed.append((i, j))
            for ii, jj in itertools.product(
                    range(max(i, 1) - 1, i + 2),
                    range(max(j, 1) - 1, j + 2)):
                if (ii, jj) in self.already_revealed:
                    continue  # Current square, skip
                try:
                    val = self.arr.iloc[ii, jj]
                    if val != MINE:
                        self.reveal(ii, ascii_lowercase[jj])
                except IndexError:
                    continue
        if self.won:
            print(self.arr)
            self.game_over = True
            self.msg = self.WIN_MSG

    def play(self):
        while not self.game_over:
            self.display()
            print("Choose a square to reveal (i.e. '1a', 'j15', 'B4').")
            sq = input('> ')
            try:
                letter = re.search(r'[A-z]+', sq).group(0).lower()
                number = int(re.search(r'[0-9]+', sq).group(0))
                self.reveal(number, letter)
            except AttributeError as e:
                if "has no attribute 'group'" not in str(e):
                    raise
                input("Invalid input.")
        print(self.msg)

    def populate(self, pct_mines):
        # Calculate the number of mines to place
        nrows = self.arr.shape[0]
        ncols = self.arr.shape[1]
        nmines = int(nrows * ncols * pct_mines)

        # Place mines
        for mine in range(nmines):
            while True:
                i = random.choice(self.arr.index)
                j = random.choice(self.arr.columns)
                if self.arr.loc[i, j] != MINE:
                    self.arr.loc[i, j] = MINE
                    break

        # Place numbers
        for i, j in itertools.product(self.arr.index, range(len(self.arr.columns))):
            # Count mines in adjacent 8 squares
            if self.arr.iloc[i, j] == MINE:
                continue
            adj_sqs = []
            for ii, jj in itertools.product(
                    range(max(i-1, 0), min(i+2, nrows)),
                    range(max(j-1, 0), min(j+2, nrows))):
                if i == ii and j == jj:
                    continue  # Current square, skip
                try:
                    adj_sqs.append(self.arr.iloc[ii, jj])
                except IndexError:
                    continue
            adj_mines = adj_sqs.count(MINE)
            if adj_mines > 0:
                self.arr.iloc[i, j] = adj_mines

    @property
    def won(self):
        # Check each square of the mask against the real board
        for i, j in itertools.product(self.arr.index, range(len(self.arr.columns))):
            real_val = self.arr.iloc[i, j]
            if self.mask.iloc[i, j] != real_val and real_val != MINE:
                return False
        return True


if __name__ == '__main__':
    Minesweeper()
