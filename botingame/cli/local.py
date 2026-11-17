"""Offline Matches (`botingame play`): Bots play each other through the same Game code the platform runs.

A Bot gets exactly what the platform would send it: its seat's view and its legal moves, as JSON, so tuples arrive as
lists. A move goes back through JSON too. An illegal move loses the Match at once: the platform refuses it (`422`) and
the Bot loses when its move timeout runs out, unless it sends a legal move in time.
"""
import importlib.util
import itertools
import json
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..games import Game
from ..sdk import ChooseMove


class BotFileError(Exception):
    pass


_loaded = itertools.count()  # each load is a fresh module, so a Bot can play a copy of itself


@dataclass
class Bot:
    choose_move: ChooseMove
    game: str | None = None  # the Bot file's GAME, if it declares one
    game_version: str | None = None  # its GAME_VERSION: the version of the Game's rules it was written for


def load_bot(path: str) -> Bot:
    """The `choose_move` of a Bot file (and its `GAME` and `GAME_VERSION`, if set). Its folder is importable, for
    helper modules."""
    file = Path(path).resolve()
    if not file.is_file():
        raise BotFileError(f"no Bot file at {path}")
    folder = str(file.parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    spec = importlib.util.spec_from_file_location(f"botingame_bot_{next(_loaded)}", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "choose_move", None)):
        raise BotFileError(f"{path} has no choose_move(view, legal_moves) function")
    return Bot(module.choose_move, getattr(module, "GAME", None), getattr(module, "GAME_VERSION", None))


def random_bot(rng: random.Random) -> Bot:
    return Bot(lambda view, legal_moves: rng.choice(legal_moves))


@dataclass
class Result:
    scores: list[float]  # per seat: 1 win, 0.5 draw, 0 loss
    reason: str  # "normal", or "illegal move by seat N: …" when a seat lost by one
    moves: int


def through_json(value: Any) -> Any:
    """`value` as it would cross the API: through JSON."""
    return json.loads(json.dumps(value))


def play_match(game: Game, bots: list[Bot], seed: int,
               on_move: Callable[[int, int, Any, dict], None] | None = None,
               before_move: Callable[[int, int], None] | None = None) -> Result:
    """Play one Match, `bots[i]` in seat i. `before_move(index, seat)` comes before each Bot is asked for its move
    (an exception there stops the Match), and `on_move(index, seat, move, state)` follows each accepted move."""
    state = game.initial_state(seed)
    moves = 0
    while (to_move := game.to_move(state)):
        seat = min(to_move)
        if before_move is not None:
            before_move(moves, seat)
        legal = game.legal_moves(state, seat)
        move = through_json(bots[seat].choose_move(through_json(game.view(state, seat)), through_json(legal)))
        try:
            state = game.apply(state, seat, move)
        except Exception as e:  # an IllegalMove, or a move so malformed the Game chokes on it
            scores = [1.0] * game.players
            scores[seat] = 0.0
            return Result(scores, f"illegal move by seat {seat}: {move!r} ({e})", moves)
        if on_move is not None:
            on_move(moves, seat, move, state)
        moves += 1
    return Result(game.outcome(state), "normal", moves)
