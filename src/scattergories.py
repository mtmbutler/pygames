"""Scattergories"""

import random
import time

from fire import Fire
from tqdm import tqdm

LETTERS = "ABCDEFGHIJKLMNOPRSTW"


def main(seconds: int) -> None:
    """Main function."""
    print("Generating a letter")
    for _ in tqdm(range(3)):
        time.sleep(1)
    letter = random.choice(LETTERS)
    print(f"Letter: {letter}")
    for _ in tqdm(range(seconds)):
        time.sleep(1)
    print("Time's up!")


if __name__ == "__main__":
    Fire(main)
