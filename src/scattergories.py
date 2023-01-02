"""Scattergories"""

import datetime
import random
import time
import timeit
from pathlib import Path

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
        prompts = [ln.title() for ln in set(ln.strip().lower() for ln in f.readlines())]
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
            print(f"  {i + 1}.\t{prompts.pop()}")
        print("")
        try:
            start = current = timeit.default_timer()
            target = start + SECONDS_PER_ROUND
            while current < target:
                delta = int(target - current)
                print(f"\rRemaining time: {delta // 60}m{delta % 60}s", end="")
                time.sleep(0.1)
                current = timeit.default_timer()
            print("Time's up!")
        except KeyboardInterrupt:
            print("Round canceled.")
        finally:
            print(SEP)


if __name__ == "__main__":
    main()
