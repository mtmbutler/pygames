"""Scumbags and warlords."""

import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from fire import Fire

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


class OrderedEnum(Enum):
    """Enum with ordering by value."""

    def __eq__(self, other: Any) -> Any:
        return self.value == other.value

    def __lt__(self, other: Any) -> Any:
        return self.value < other.value


class Suit(OrderedEnum):
    """Card suit."""

    __symbols__ = {
        "S": "♠",
        "C": "♣",
        "D": "♦",
        "H": "♥",
    }

    S = 4
    C = 3
    D = 2
    H = 1

    def __str__(self) -> str:
        return self.__symbols__[self.name]


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

    def __str__(self) -> str:
        return self.name[1:]


class CardParseError(Exception):
    """Error in parsing a card from a string."""


@dataclass
class Card:
    """Card."""

    number: Number
    suit: Suit

    def __str__(self) -> str:
        return f"{self.number}{self.suit}"

    def __eq__(self, other: Any) -> Any:
        return self.number == other.number

    def __lt__(self, other: Any) -> Any:
        return self.number < other.number

    def is_same(self, other: Any) -> Any:
        """Whether two cards are the same"""
        return self.number == other.number and self.suit == other.suit

    @classmethod
    def from_str(cls, s: str) -> "Card":
        """Try to parse a card from a string like "KS" for king of spades"""
        try:
            num, suit = s[:-1], s[-1]
        except IndexError as e:
            raise CardParseError(s) from e
        try:
            num_obj = getattr(Number, "_" + num.upper())
        except AttributeError as e:
            raise CardParseError(f"Couldn't parse card number from '{num}'") from e
        try:
            suit_obj = getattr(Suit, suit.upper())
        except AttributeError as e:
            raise CardParseError(f"Couldn't parse card suit from '{suit}'") from e
        return cls(number=num_obj, suit=suit_obj)


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
        deck = cls(cards=cards)
        deck.shuffle()
        return deck


@dataclass
class Move:
    """A player move."""

    cards: tuple[Card, ...]
    on: tuple[Card, ...]

    def __str__(self) -> str:
        return " ".join(str(c) for c in self.cards)

    def is_legal(self) -> bool:
        """Whether the move is legal"""
        if not self.cards:
            # Always allowed to pass
            return True
        values = [c.number.value for c in self.cards]
        if len(set(values)) > 1:
            # Can't play multiple values
            return False
        if not self.on:
            # Can play anything when starting
            return True
        if len(self.cards) != len(self.on):
            return False
        on_value = max(c.number.value for c in self.on)
        return values[0] > on_value


class IllegalMoveException(Exception):
    """Illegal move error"""


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

    def card_index(self, card: Card) -> int:
        """The index in a player's hand of a particular card."""
        for i, c in enumerate(self.hand.cards):
            if c.is_same(card):
                return i
        raise ValueError(f"{card} is not in hand")

    def play_move(self, move: Move) -> tuple[Card, ...]:
        """Plays a move and returns the associated card."""
        if not move.is_legal():
            raise IllegalMoveException(f"Illegal move: {move}")
        if not move.cards:
            return ()
        ixs: list[int] = []
        for card in move.cards:
            try:  # Make sure the card is in their hand
                ix = self.card_index(card)
            except ValueError as e:
                raise IllegalMoveException(f"Player doesn't have card {card}") from e
            ixs.append(ix)
        for ix in ixs:
            self.hand.cards.pop(ix)
        return move.cards

    def play_lowest_card(self, on: tuple[Card, ...]) -> Move:
        """Plays the lowest card that beats the provided card."""
        left = 0
        right = max(len(on), 1)
        while right <= len(self.hand.cards):
            move = Move(cards=tuple(self.hand.cards[left:right]), on=on)
            if move.is_legal():
                return move
            left += 1
            right += 1
        return Move((), on)


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


def main(num_players: int, human_players: tuple[int, ...] = (0,)) -> None:
    """Main function."""
    # Make deck
    deck = Deck.full_shuffled_deck()
    logger.info("Made deck. Cards: %s", deck)

    # Make players and deal cards
    players: list[Player] = []
    for i in range(num_players):
        players.append(Player(idno=i + 1, hand=CardCollection([])))
    deal_to_players(deck, players, -1)
    logger.info("Cards dealt.")
    for player in players:
        player.hand.sort()
        logger.info(player)
    logger.info("Cards remaining in deck: %s", len(deck.cards))

    # Game loop
    active_player_ix = 0  # todo: start with 3 of clubs
    last_played_cards: tuple[Card, ...] = ()
    last_player_no_pass: Optional[Player] = None
    while True:
        time.sleep(0.3)

        # Each iteration is one player's turn
        player = players[active_player_ix]
        if player is last_player_no_pass:
            # If everyone passed and it's your turn again, clear the stack
            last_played_cards = ()

        cards: tuple[Card, ...] = ()
        if active_player_ix in human_players:
            while True:
                logger.info("Your turn.\n%s", player)
                cards_input = input("Play which card? ")
                if not cards_input or cards_input.lower() == "pass":
                    move = Move((), last_played_cards)
                    break
                card_list: list[Card] = []
                for card_input in cards_input.split(" "):
                    try:
                        card_list.append(Card.from_str(card_input))
                    except CardParseError as e:
                        logger.info("Error parsing card: %s", e)
                        continue
                move = Move(tuple(card_list), last_played_cards)
                try:
                    cards = player.play_move(move)
                except IllegalMoveException as e:
                    logger.info("Illegal move error: %s", e)
                    continue
                break
        else:
            move = player.play_lowest_card(last_played_cards)
            cards = player.play_move(move)

        # Play a card
        if cards:
            logger.info("Player %s plays %s", player.idno, move)
            last_played_cards = cards
            last_player_no_pass = player
        else:
            logger.info("Player %s passes", player.idno)

        # Check if the player won
        if not player.hand:
            logger.info("Player %s won!", player.idno)
            break

        # Move to the next player
        active_player_ix += 1
        if active_player_ix >= len(players):
            active_player_ix -= len(players)


if __name__ == "__main__":
    Fire(main)
