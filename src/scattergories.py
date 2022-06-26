"""Scattergories"""

import random
import time

from fire import Fire
from tqdm import tqdm

LETTERS = "ABCDEFGHIJKLMNOPRSTW"
already_done: set[str] = set()


def main() -> None:
    """Main function."""
    while True:
        print("Welcome to Scattergories! Enter # of seconds and press enter to start.")
        try:
            seconds = int(input("Seconds: "))
        except ValueError:
            print("Invalid input.")
            continue
        letter = random.choice(list(set(LETTERS) - already_done))
        already_done.add(letter)
        print(f"Letter: {letter}")
        try:
            for _ in tqdm(range(seconds)):
                time.sleep(1)
            print("Time's up!")
        except KeyboardInterrupt:
            print("Round canceled.")


if __name__ == "__main__":
    Fire(main)
