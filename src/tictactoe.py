"""Tic tac toe"""
import re
from string import ascii_lowercase
from typing import Optional

import pandas as pd

BLANK = ""


class TicTacToe:
    """CLI tic tac toe game."""

    lines = (
        # Horizontal
        ("a1", "b1", "c1"),
        ("a2", "b2", "c2"),
        ("a3", "b3", "c3"),
        # Vertical
        ("a1", "a2", "a3"),
        ("b1", "b2", "b3"),
        ("c1", "c2", "c3"),
        # Diagonal
        ("a1", "b2", "c3"),
        ("a3", "b2", "c1"),
    )

    def __init__(self) -> None:
        print("Welcome to TicTacToe!")
        self.board = pd.DataFrame(
            index=range(1, 4), columns=list(ascii_lowercase[:3]), data=BLANK
        )
        self.chars = ["X", "O", "X", "O", "X", "O", "X", "O", "X"]

        self.next_char = "X"
        self.play()

    def display(self) -> None:
        """Show current board state."""
        print(self.board)

    def play(self) -> None:
        """Game loop."""
        while self.winner is None:
            self.display()
            next_char = self.chars[-1]
            print(
                f"Choose a square to play (i.e. '1a', 'c3', 'B1')" f" your {next_char}."
            )
            coord = input("> ")
            i, j = self.parse_coord(coord)
            self.board.loc[i, j] = self.chars.pop()
        self.display()
        print(f"{self.winner} wins!")

    @staticmethod
    def parse_coord(
        coord: str,
    ) -> tuple[int, str]:
        """Parse a coordinate from an input string."""
        match_letter = re.search(r"[A-z]+", coord)
        if match_letter:
            letter = match_letter.group(0).lower()
        else:
            raise Exception(f"No letter match found for input: {coord}")
        match_number = re.search(r"[0-9]+", coord)
        if match_number:
            number = int(match_number.group(0))
        else:
            raise Exception(f"No number match found for input: {coord}")
        return number, letter

    @property
    def winner(self) -> Optional[str]:
        """The winning player, if the board has a won position."""
        for line in self.lines:
            coords = [self.parse_coord(coord) for coord in line]
            vals = [self.board.loc[i, j] for i, j in coords]
            if all(val == "X" for val in vals):
                return "X"
            if all(val == "O" for val in vals):
                return "O"
        return None


if __name__ == "__main__":
    TicTacToe()
