import random

already_done = set()

with open("words.txt") as f:
    words = list(f.readlines())

while len(already_done) < len(words):
    word = random.choice(words)
    if word in already_done:
        continue
    already_done.add(word)
    print(word)
    input("Enter to continue")
print("Used all words")
