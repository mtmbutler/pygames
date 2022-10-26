"""Scumbags and warlords."""

import argparse
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import Any, Callable, Iterator, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

DIVIDER = "-" * 50


class OrderedEnum(Enum):
    """Enum with ordering by value."""

    def __eq__(self, other: Any) -> Any:
        return self.value == other.value

    def __lt__(self, other: Any) -> Any:
        return self.value < other.value

    def __le__(self, other: Any) -> Any:
        return self.value <= other.value


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

    def __hash__(self) -> int:
        return self.value


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

    def __hash__(self) -> int:
        return 10 * self.number.value + self.suit.value

    def is_same(self, other: Any) -> Any:
        """Whether two cards are the same"""
        return self.number == other.number and self.suit == other.suit


START_CARD = Card(Number._3, Suit.C)  # pylint: disable=protected-access


class CardCollection(list[Card]):
    """Group of cards."""

    def __str__(self) -> str:
        return " ".join(str(c) for c in self)

    def counter(self) -> dict[Number, int]:
        """Counter, keyed by card number."""
        counter: dict[Number, int] = {}
        for card in self:
            if card.number not in counter:
                counter[card.number] = 0
            counter[card.number] += 1
        return counter


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

    @property
    def count(self) -> int:
        """Card count"""
        return len(self.cards)

    @property
    def cardinality(self) -> Number:
        """Cardinality of card value."""
        c = self.counter()
        if not c:
            raise ValueError("Pass has no cardinality")
        if len(c) > 1:
            raise ValueError("Move has multiple card values")
        return list(c)[0]

    def is_legal(self, is_first_move: bool) -> bool:
        """Whether the move is legal"""
        if not self.cards and not is_first_move:
            # Always allowed to pass
            return True
        if is_first_move and not any(c.is_same(START_CARD) for c in self.cards):
            return False
        try:
            cardinality = self.cardinality
        except ValueError:
            # Can't play multiple values
            return False
        if not self.on:
            # Can play anything when starting
            return True
        if len(self.cards) != len(self.on):
            return False
        on_value = max(c.number for c in self.on)
        return cardinality > on_value

    def is_partial_for_player(self, player: "Player") -> bool:
        """Whether the move is partial."""
        hand_counter = player.hand.counter()
        is_partial = self.count < hand_counter[self.cardinality]
        logger.debug("Is move %s partial for player %s? %s", self, player, is_partial)
        return is_partial

    def counter(self) -> dict[Number, int]:
        """Card number counter. Example: {Number._5: 3} means three 5's."""
        return _move_counter(self.cards)


@cache
def _move_counter(cards: tuple[Card, ...]) -> dict[Number, int]:
    """Card number counter. Example: {Number._5: 3} means three 5's."""
    return CardCollection(cards).counter()


class IllegalMoveException(Exception):
    """Illegal move error"""


@dataclass
class Player:
    """Player."""

    idno: int
    hand: CardCollection
    strategy: "Strategy"
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
        # A partial move is one where a player doesn't play all their cards of a
        # given cardinality, e.g. they play two jacks when they have three. These
        # are usually suboptimal, so let's store them and yield them at the end.
        partials: list[Move] = []

        # Keep track of plays and don't yield redundant moves, e.g. 4c and 4s when
        # we've already yielded 4c and 4h
        redundancy_checker: set[tuple[int, Number]] = set()
        if on:
            yield Move((), on)  # Can always pass
            window_sizes = [len(on)]
        else:
            window_sizes = [4, 3, 2, 1]
        for window_size in window_sizes:
            left = 0
            right = window_size
            while right <= len(self.hand):
                move = Move(cards=tuple(self.hand[left:right]), on=on)
                if move.is_legal(is_first_move=self.is_first_player):
                    logger.debug("Checking move %s", move)
                    redundancy_class = (move.count, move.cardinality)
                    if redundancy_class not in redundancy_checker:
                        redundancy_checker.add(redundancy_class)
                        if move.is_partial_for_player(self):
                            partials.append(move)
                        else:
                            yield move
                left += 1
                right += 1

        # Yield the partial moves
        for move in partials:
            yield move

    def play_move(self, move: Move) -> None:
        """Plays a move"""
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


# A tactic is a function for selecting a move.
Tactic = Callable[[Player, tuple[Card, ...]], Move]


def play_from_input(player: Player, on: tuple[Card, ...]) -> Move:
    """Play moves from user input. Use this tactic for human players."""
    while True:
        partial_index = -1  # The first partial move, so we can mark
        moves: dict[str, Move] = {}
        for i, move in enumerate(player.legal_moves(on=on)):
            if (
                partial_index == -1
                and move.cards
                and move.is_partial_for_player(player)
            ):
                partial_index = i
            moves[str(i)] = move
        if len(moves) == 1:
            return moves["0"]

        logger.info("Your turn.\nHand: %s\nAvailable moves:", player.hand)
        for ix, move in moves.items():
            if ix == str(partial_index):
                logger.info("  ---")
            logger.info("  (%s) %s", ix, move)

        move_input = input("Play which move? ")
        if move_input not in moves:
            logger.info("Invalid input: %s", move_input)
            continue
        return moves[move_input]


def play_first_legal_option(player: Player, on: tuple[Card, ...]) -> Move:
    """A simple tactic that plays the first legal move.

    Efficacy is highly dependent on the ordering of legal moves.
    """
    for move in player.legal_moves(on=on):
        if move:
            return move
    return Move((), on)


def maintain_balance(player: Player, on: tuple[Card, ...]) -> Move:
    """Play first legal, but pass to hold onto high cards.

    This is called maintain balance because the idea is to keep the number of low
    cards in one's hand roughly equal to the number of high cards.
    """
    middle_val = Number._9  # pylint: disable=protected-access
    num_low_cards = 0
    for card in player.hand:
        if card.number <= middle_val:
            num_low_cards += 1
    do_hold = num_low_cards >= len(player.hand) // 2
    logger.debug("Player %s has %s low cards, hold=%s", player, num_low_cards, do_hold)
    hold_override_move: Optional[Move] = None
    for move in player.legal_moves(on=on):
        if move:
            if not do_hold or (move.cardinality <= middle_val):
                return move
            if hold_override_move is None:
                logger.debug(
                    "Player %s hold override move: %s", player, hold_override_move
                )
                hold_override_move = move
    if not on and hold_override_move:
        logger.debug(
            "Player %s playing hold override move: %s", player, hold_override_move
        )
        return hold_override_move
    return Move((), on)


class Strategy:
    """A strategy for choosing moves for a whole game."""

    def __init__(self, tactics: list[tuple[Tactic, float]]):
        self.tactics = [t for t, _ in tactics]
        self.weights = [w for _, w in tactics]

    def choose_tactic(self) -> Tactic:
        """Select a tactic for a given turn"""
        return random.choices(self.tactics, weights=self.weights)[0]


STRATEGIES = {
    "human": Strategy([(play_from_input, 1)]),
    "cpu": Strategy([(maintain_balance, 2), (play_first_legal_option, 1)]),
}


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

        # Make deck
        self.deck = Deck.full_shuffled_deck()
        logger.info("Made deck. Cards: %s", self.deck)

        # Make players and deal cards
        self.players: list[Player] = []
        for i in range(num_players):
            if i in human_players:
                strategy = STRATEGIES["human"]
            else:
                strategy = STRATEGIES["cpu"]
            self.players.append(
                Player(idno=i + 1, hand=CardCollection([]), strategy=strategy)
            )
        deal_to_players(self.deck, self.players, -1)
        logger.info("Cards dealt.")
        for player in self.players:
            player.hand.sort()
            logger.info(player)
        logger.info("Cards remaining in deck: %s", len(self.deck))
        logger.info(DIVIDER)

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
            tactic = player.strategy.choose_tactic()
            logger.debug("Chose tactic `%s` for player %s", tactic.__name__, player)
            move = tactic(player, last_played_cards)
            player.play_move(move)
            last_played_cards = move.cards or last_played_cards
            last_player_no_pass = player if move else last_player_no_pass

            # Check if the player won
            if not player.hand:
                logger.info("%s won!", player)
                logger.info(DIVIDER)
                logger.info("Final hands:")
                for p in self.players:
                    logger.info("%s: %s", p, p.hand)
                break

            # Move to the next player
            self.active_player_ix += 1
            if self.active_player_ix >= len(self.players):
                logger.info(DIVIDER)
                self.active_player_ix -= len(self.players)


def main() -> None:
    """Main"""
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
