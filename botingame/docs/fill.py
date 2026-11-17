"""Filling a Game's prose: its `{{placeholders}}` get their text from the Game's code, so the schemas and examples a
guide shows are always the ones the Game runs. The example is a seeded Match, seen by the seat about to move."""
import json
import random
import re
from dataclasses import dataclass
from typing import Any

from ..games import Game

EXAMPLE_SEED = 0
# How many moves the example Match has played: far enough in that both seats' marks are on the board.
EXAMPLE_MOVES = {"uttt": 43, "connect4": 9, "dots": 60, "battleship": 110}
EXAMPLE_PLAYERS = ("alpha", "beta")
WIDTH = 100  # the widest line a JSON example packs short arrays into


@dataclass
class Example:
    """A seat about to move in a seeded Match: what `choose_move` gets, and a move it may return."""
    seat: int
    turn: int  # moves played so far, the `turn` the Bot API sends and expects back
    view: dict
    legal_moves: list
    move: Any


def example(game: Game) -> Example:
    """A Match `EXAMPLE_MOVES` moves in, played with seeded random moves, from the side of the seat to move."""
    rng = random.Random(EXAMPLE_SEED)
    state = game.initial_state(EXAMPLE_SEED)
    played = 0
    while played < EXAMPLE_MOVES.get(game.id, 6):
        seat = min(game.to_move(state))
        after = game.apply(state, seat, rng.choice(game.legal_moves(state, seat)))
        if not game.to_move(after):  # never show a finished Match
            break
        state, played = after, played + 1
    seat = min(game.to_move(state))
    legal = game.legal_moves(state, seat)
    return Example(seat, played, game.view(state, seat), legal, rng.choice(legal))


def _scalar(x: Any) -> bool:
    return not isinstance(x, (dict, list))


def _tuple(x: Any) -> bool:
    """A short array of scalars, like a move: several fit on a line."""
    return isinstance(x, list) and len(x) <= 3 and all(map(_scalar, x))


def _grid(value: list) -> bool:
    """Rows of scalars, all as long: a board, shown one row per line with its columns aligned."""
    return (len(value) > 1 and all(isinstance(r, list) and r and all(map(_scalar, r)) for r in value)
            and len({len(r) for r in value}) == 1 and len(value[0]) > 3)


def readable_json(value: Any, indent: int = 0) -> str:
    """JSON for a reader: indented by 2, a board one aligned row per line, short arrays and objects on one line,
    and lists of scalars or moves packed onto lines of at most WIDTH."""
    pad, inner = " " * indent, " " * (indent + 2)
    flat = json.dumps(value)
    if _scalar(value) or not value:
        return flat
    if isinstance(value, list) and _grid(value):
        cells = [[json.dumps(x) for x in row] for row in value]
        width = max(len(c) for row in cells for c in row)
        rows = ["[" + ", ".join(c.rjust(width) for c in row) + "]" for row in cells]
        return "[\n" + ",\n".join(inner + r for r in rows) + f"\n{pad}]"
    if len(flat) + indent <= WIDTH and (isinstance(value, dict) or all(_scalar(x) or _tuple(x) for x in value)):
        return flat
    if isinstance(value, dict):
        items = [f"{inner}{json.dumps(k)}: {readable_json(v, indent + 2)}" for k, v in value.items()]
        return "{\n" + ",\n".join(items) + f"\n{pad}}}"
    if all(_scalar(x) or _tuple(x) for x in value):
        lines, line = [], ""
        for part in (json.dumps(x) for x in value):
            if line and len(inner) + len(line) + len(part) + 2 > WIDTH:
                lines.append(line + ",")
                line = ""
            line = f"{line}, {part}" if line else part
        lines.append(line)
        return "[\n" + "\n".join(inner + x for x in lines) + f"\n{pad}]"
    return "[\n" + ",\n".join(inner + readable_json(x, indent + 2) for x in value) + f"\n{pad}]"


def match_response(game: Game, ex: Example) -> dict:
    """What `GET /v1/matches/{id}` returns to the seat to move in the example (ids and times are made up)."""
    return {
        "match_id": "3f9c2a7d1e4b", "arena": f"{game.id}-elo", "game": game.id,
        "players": [{"seat": i, "bot_id": f"b{i + 1}", "name": name, "removed": False}
                    for i, name in enumerate(EXAMPLE_PLAYERS)],
        "status": "active", "state": ex.view, "to_move": [ex.seat], "result": None, "reason": None,
        "turn": ex.turn, "deadline": "2026-11-12T18:30:20Z", "timeout_s": game.default_move_timeout_s,
        "series": {"id": "8d1e0b6c2f5a", "best_of": 1, "match_number": 1, "status": "active",
                   "score": {"b1": 0, "b2": 0}, "result": None},
        "your_seat": ex.seat, "your_turn": True, "legal_moves": ex.legal_moves, "time_left_s": 19.42,
    }


def placeholders(game: Game) -> dict[str, str]:
    """Each placeholder's text, from the Game's code."""
    ex = example(game)
    return {
        "key": game.id, "name": game.name, "version": game.version, "arena": f"{game.id}-elo",
        "timeout_s": f"{game.default_move_timeout_s:g}",
        "view_schema": readable_json(game.view_schema), "move_schema": readable_json(game.move_schema),
        "example_seat": str(ex.seat), "example_turn": str(ex.turn),
        "example_view": readable_json(ex.view), "example_move": json.dumps(ex.move),
        "example_legal_moves": readable_json(ex.legal_moves),
        "example_match": readable_json(match_response(game, ex)),
        "example_post": readable_json({"turn": ex.turn, "move": ex.move}),
    }


PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def fill(text: str, game: Game, where: str) -> str:
    """`text` with each placeholder replaced by its text; `where` names the page in the error for an unknown one."""
    values = placeholders(game)

    def value(m: re.Match) -> str:
        if m.group(1) not in values:
            raise KeyError(f"{where}: unknown placeholder {m.group(0)}")
        return values[m.group(1)]

    return PLACEHOLDER.sub(value, text)
