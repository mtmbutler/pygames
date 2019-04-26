# Minesweeper

# Board, max size 24 x 30
# Each square can be a mine, a number, or blank
# The numbered squares count the adjacent mines
import itertools
import random
from string import ascii_lowercase

import pandas as pd

MINE = 'X'
BLANK = ''
HIDDEN = '-'


class Board:
    MAX_ROWS = 30
    MAX_COLS = 24
    MAX_MINE_PCT = .9
    WIN_MSG = "Congratulations!"
    LOSE_MSG = "Oh no, a mine! Game over!"
    PROG_MSG = "The game's still going!"

    def __init__(self, rows, cols, pct_mines):
        rows = min(rows, self.MAX_ROWS)
        cols = min(cols, self.MAX_COLS)

        self.arr = pd.DataFrame(
            index=range(rows), columns=list(ascii_lowercase[:cols]),
            data=BLANK)
        self.mask = pd.DataFrame(
            index=range(rows), columns=list(ascii_lowercase[:cols]),
            data=HIDDEN)
        self.game_over = False
        self.msg = self.PROG_MSG

        self.populate(pct_mines)  # Generate mines and counts

        self.played_this_round = []

    def __str__(self):
        return str(self.mask)

    def display(self):
        print(self.__str__())

    def play(self, row_ix, col_ix):
        # Get underlying value of specified square and pin to mask
        val = self.arr.loc[row_ix, col_ix]
        self.mask.loc[row_ix, col_ix] = val
        if val == MINE:
            print(self.arr)
            self.game_over = True
            self.msg = self.LOSE_MSG
        elif self.won:
            print(self.arr)
            self.game_over = True
            self.msg = self.WIN_MSG

        # Propagate, automatically play adjacent blank squares
        if val == BLANK:
            i = row_ix
            j = ascii_lowercase.index(col_ix)
            self.played_this_round.append((i, j))
            for ii, jj in itertools.product(
                    range(max(i, 1) - 1, i + 2),
                    range(max(j, 1) - 1, j + 2)):
                if (ii, jj) in itertools.chain([(i, j)], self.played_this_round):
                    continue  # Current square, skip
                try:
                    val = self.arr.iloc[ii, jj]
                    if val != MINE:
                        self.play(ii, ascii_lowercase[jj])
                except IndexError:
                    continue

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
    print(
        "Welcome to Minesweeper! Please specify the following:")
    nrows = int(input(f"Number of rows (max {Board.MAX_ROWS})"))
    ncols = int(input(f"Number of cols (max {Board.MAX_COLS})"))
    pct = float(input(
        f"Percentage of tiles to have mines (between 0 and 1,"
        f" max {Board.MAX_MINE_PCT}):"))
    b = Board(nrows, ncols, pct)
    while not b.game_over:
        b.display()
        print("Choose a square to reveal (i.e. '1a').")
        sq = input('> ')
        b.play(int(sq[0]), sq[1])
    print(b.msg)
