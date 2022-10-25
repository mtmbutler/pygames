"""Scumbags and warlords."""

import argparse
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator, Optional

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


START_CARD = Card.from_str("3c")


class CardCollection(list[Card]):
    """Group of cards."""

    def __str__(self) -> str:
        return " ".join(str(c) for c in self)


class Deck(CardCollection):
    """Deck of cards."""

    @classmethod
    def full_shuffled_deck(cls) -> "Deck":
        """Generates a full, shuffled deck."""
        deck = cls()
        for suit in Suit:
            for number in Number:
                deck.append(Card(number, suit))
        random.shuffle(deck)
        return deck


@dataclass
class Move:
    """A player move."""

    cards: tuple[Card, ...]
    on: tuple[Card, ...]

    def __str__(self) -> str:
        if not self.cards:
            return "pass"
        return " ".join(str(c) for c in self.cards)

    def __bool__(self) -> bool:
        return bool(self.cards)

    def is_legal(self, is_first_move: bool) -> bool:
        """Whether the move is legal"""
        if not self.cards:
            # Always allowed to pass
            return True
        if is_first_move and not any(c.is_same(START_CARD) for c in self.cards):
            return False
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
    is_first_player: bool = False

    def __str__(self) -> str:
        return f"Player {self.idno} ({len(self.hand)})"

    def deal(self, card: Card) -> None:
        """Give the player a card."""
        self.hand.append(card)

    def card_index(self, card: Card) -> int:
        """The index in a player's hand of a particular card."""
        for i, c in enumerate(self.hand):
            if c.is_same(card):
                return i
        raise ValueError(f"{card} is not in hand")

    def has_card(self, card: Card) -> bool:
        """Whether a player has a particular card."""
        try:
            self.card_index(card)
            return True
        except ValueError:
            return False

    def legal_moves(self, on: tuple[Card, ...]) -> Iterator[Move]:
        """All legal moves"""
        if on:
            window_sizes = [len(on)]
        else:
            window_sizes = [4, 3, 2, 1]
        for window_size in window_sizes:
            left = 0
            right = window_size
            while right <= len(self.hand):
                move = Move(cards=tuple(self.hand[left:right]), on=on)
                if move.is_legal(is_first_move=self.is_first_player):
                    yield move
                left += 1
                right += 1
        yield Move((), on)

    def play_move(self, move: Move) -> None:
        """Plays a move and returns the associated card."""
        if not move.is_legal(is_first_move=self.is_first_player):
            raise IllegalMoveException(f"Illegal move: {move}")
        ixs: list[int] = []
        for card in move.cards:
            try:  # Make sure the card is in their hand
                ix = self.card_index(card)
            except ValueError as e:
                raise IllegalMoveException(f"Player doesn't have card {card}") from e
            ixs.append(ix)
        for ix in sorted(ixs)[::-1]:
            self.hand.pop(ix)
        if self.is_first_player:
            self.is_first_player = False
        logger.info("%s plays: %s", self, move)

    def play_lowest_card(self, on: tuple[Card, ...]) -> Move:
        """Plays the lowest card that beats the provided card."""
        for move in self.legal_moves(on=on):
            return move
        return Move((), on)

    def play_from_input(self, on: tuple[Card, ...]) -> Move:
        """Play a move specified by user input."""
        while True:
            logger.info("Your turn.\n%s", self.hand)
            cards_input = input("Play which card? ")
            if not cards_input or cards_input.lower() == "pass":
                return Move((), on)
            card_list: list[Card] = []
            for card_input in cards_input.split(" "):
                try:
                    card_list.append(Card.from_str(card_input))
                except CardParseError as e:
                    logger.info("Error parsing card: %s", e)
                    continue
            move = Move(tuple(card_list), on)
            if not move.is_legal(is_first_move=self.is_first_player):
                logger.info("Illegal move")
                continue
            return move


def deal_to_players(deck: Deck, players: list[Player], hand_size: int) -> None:
    """Deals hand_size cards to each player from the deck.

    If hand_size is <= 0, deal the whole deck.
    """
    if hand_size <= 0:
        hand_size = len(deck) + 1
    cards_dealt_to_each = 0
    while cards_dealt_to_each < hand_size:
        for player in players:
            if not deck:
                return
            player.deal(deck.pop())
        cards_dealt_to_each += 1


class Game:
    """A game of scumbags and warlords."""

    def __init__(self, num_players: int, human_players: tuple[int, ...] = (0,)):
        self.num_players = num_players
        self.human_players = human_players

        # Make deck
        self.deck = Deck.full_shuffled_deck()
        logger.info("Made deck. Cards: %s", self.deck)

        # Make players and deal cards
        self.players: list[Player] = []
        for i in range(num_players):
            self.players.append(Player(idno=i + 1, hand=CardCollection([])))
        deal_to_players(self.deck, self.players, -1)
        logger.info("Cards dealt.")
        for player in self.players:
            player.hand.sort()
            logger.info(player)
        logger.info("Cards remaining in deck: %s", len(self.deck))

        # Determine first player
        self.active_player_ix = 0
        for i, p in enumerate(self.players):
            if p.has_card(START_CARD):
                p.is_first_player = True
                self.active_player_ix = i
                break

    def start(self) -> None:
        """Start the game loop."""
        last_played_cards: tuple[Card, ...] = ()
        last_player_no_pass: Optional[Player] = None
        while True:
            time.sleep(0.3)

            # Each iteration is one player's turn
            player = self.players[self.active_player_ix]
            if player is last_player_no_pass:
                # If everyone passed and it's your turn again, clear the stack
                last_played_cards = ()

            legal_moves = list(player.legal_moves(on=last_played_cards))
            if not legal_moves:
                raise Exception(f"{player} has no legal moves")
            if len(legal_moves) == 1:
                move = legal_moves[0]
            elif self.active_player_ix in self.human_players:
                move = player.play_from_input(last_played_cards)
            else:
                move = player.play_lowest_card(last_played_cards)
            player.play_move(move)
            last_played_cards = move.cards or last_played_cards
            last_player_no_pass = player if move else last_player_no_pass

            # Check if the player won
            if not player.hand:
                logger.info("%s won!", player)
                logger.info("Final hands:")
                for p in self.players:
                    logger.info("%s: %s", p, p.hand)
                break

            # Move to the next player
            self.active_player_ix += 1
            if self.active_player_ix >= len(self.players):
                self.active_player_ix -= len(self.players)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "num_players", type=int, action="store", help="Number of players."
    )
    parser.add_argument(
        "human_players",
        nargs="*",
        type=int,
        action="store",
        default=[0],
        help="Which players should be controlled by human input.",
    )
    args = parser.parse_args()

    g = Game(args.num_players, tuple(args.human_players))
    g.start()


if __name__ == "__main__":
    main()
