"""Scattergories"""

import random
import time
from pathlib import Path

from fire import Fire
from tqdm import tqdm

PROMPTS_PATH = Path(__file__).parent / "scattergories.txt"
LETTERS = "ABCDEFGHIJKLMNOPRSTW"
NUM_PROMPTS = 12
SECONDS_PER_ROUND = 180
SEP = "==="


def main() -> None:
    """Main function."""
    print("Welcome to Scattergories!")

    # Set up letters and prompts
    with open(PROMPTS_PATH, encoding="utf-8") as f:
        prompts = [ln.strip() for ln in f.readlines()]
    letters = list(LETTERS)
    random.shuffle(prompts)
    random.shuffle(letters)

    while True:
        input("Press enter to start a round. Press Ctrl-C to end the round early.")
        print(SEP)
        letter = letters.pop()
        print(f"Letter: {letter}")
        print("Prompts:")
        for i in range(NUM_PROMPTS):
            print(f"  {i + 1}. {prompts.pop()}")
        print("")
        try:
            for _ in tqdm(range(SECONDS_PER_ROUND)):
                time.sleep(1)
            print("Time's up!")
        except KeyboardInterrupt:
            print("Round canceled.")
        finally:
            print(SEP)


if __name__ == "__main__":
    Fire(main)
