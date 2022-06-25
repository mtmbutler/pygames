"""Scumbags and warlords."""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from fire import Fire


class OrderedEnum(Enum):
    """Enum with ordering by value."""

    def __eq__(self, other: Any) -> Any:
        return self.value == other.value

    def __lt__(self, other: Any) -> Any:
        return self.value < other.value


class Suit(OrderedEnum):
    """Card suit."""

    S = 4
    C = 3
    D = 2
    H = 1

    def __hash__(self) -> int:
        return hash(self.name)


SUIT_SYMBOLS = {
    Suit.S: "♠",
    Suit.C: "♣",
    Suit.D: "♦",
    Suit.H: "♥",
}


class Number(OrderedEnum):
    """Card number. 2 is high in S&W."""

    _3 = 3
    _4 = 4
    _5 = 5
    _6 = 6
    _7 = 7
    _8 = 8
    _9 = 9
    _10 = 10
    _J = 11
    _Q = 12
    _K = 13
    _A = 14
    _2 = 15


@dataclass
class Card:
    """Card."""

    number: Number
    suit: Suit

    def __str__(self) -> str:
        return f"{self.number.name[1:]}{SUIT_SYMBOLS[self.suit]}"

    def __eq__(self, other: Any) -> Any:
        return self.number == other.number

    def __lt__(self, other: Any) -> Any:
        return self.number < other.number


@dataclass
class CardCollection:
    """Group of cards."""

    cards: list[Card]

    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards)

    def __len__(self) -> int:
        return len(self.cards)

    def __bool__(self) -> bool:
        return bool(self.cards)

    def shuffle(self) -> None:
        """Shuffles cards in place."""
        random.shuffle(self.cards)

    def sort(self) -> None:
        """Sorts cards lowest to highest."""
        self.cards = sorted(self.cards)

    def add(self, card: Card) -> None:
        """Add card to top."""
        self.cards.append(card)

    def draw(self) -> Card:
        """Draw the top card."""
        return self.cards.pop()


class Deck(CardCollection):
    """Deck of cards."""

    @classmethod
    def full_shuffled_deck(cls) -> "Deck":
        """Generates a full, shuffled deck."""
        cards: list[Card] = []
        for suit in Suit:
            for number in Number:
                cards.append(Card(number, suit))
        random.shuffle(cards)
        return cls(cards=cards)


@dataclass
class Player:
    """Player."""

    idno: int
    hand: CardCollection

    def __str__(self) -> str:
        return f"{self.idno}: {self.hand}"

    def deal(self, card: Card) -> None:
        """Give the player a card."""
        self.hand.add(card)

    def play_lowest_card(self, on: Optional[Card] = None) -> Optional[Card]:
        """Plays the lowest card that beats the provided card."""
        for i, card in enumerate(self.hand.cards):
            if not on or card > on:
                return self.hand.cards.pop(i)
        return None


def deal_to_players(deck: Deck, players: list[Player], hand_size: int) -> None:
    """Deals hand_size cards to each player from the deck.

    If hand_size is <= 0, deal the whole deck.
    """
    if hand_size <= 0:
        hand_size = len(deck.cards) + 1
    cards_dealt_to_each = 0
    while cards_dealt_to_each < hand_size:
        for player in players:
            if not deck:
                return
            player.deal(deck.draw())
        cards_dealt_to_each += 1


def main(num_players: int) -> None:
    """Main function."""
    # Make deck
    deck = Deck.full_shuffled_deck()
    print(f"Made deck. Cards: {deck}")

    # Make players and deal cards
    players: list[Player] = []
    for i in range(num_players):
        players.append(Player(idno=i + 1, hand=CardCollection([])))
    deal_to_players(deck, players, -1)
    print("Cards dealt.")
    for player in players:
        player.hand.sort()
        print(player)
    print(f"Cards remaining in deck: {len(deck.cards)}")

    # Game loop
    active_player_ix = 0  # todo: start with 3 of clubs
    last_played_card: Optional[Card] = None
    last_player_no_pass: Optional[Player] = None
    while True:
        # Each iteration is one player's turn
        player = players[active_player_ix]
        if player is last_player_no_pass:
            # If everyone passed and it's your turn again, clear the stack
            last_played_card = None

        # Play a card
        card = player.play_lowest_card(last_played_card)
        if card:
            print(f"Player {player.idno} plays {card}")
            last_played_card = card
            last_player_no_pass = player
        else:
            print(f"Player {player.idno} passes")

        # Check if the player won
        if not player.hand:
            print(f"Player {player.idno} won!")
            break

        # Move to the next player
        active_player_ix += 1
        if active_player_ix >= len(players):
            active_player_ix -= len(players)


if __name__ == "__main__":
    Fire(main)
