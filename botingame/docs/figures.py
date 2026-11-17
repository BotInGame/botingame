"""The pictures of each Game's rules page: positions reached by playing legal moves with the Game's own code, plus a
few notes (labels, rings, arrows) pointing at what the text explains.

A picture is drawn by the Game's Renderer on botingame.com; a note's anchor is a place on the board in the Game's own
terms (`{"cell": [4, 2]}`), which the Renderer knows where to draw."""
import random
from dataclasses import dataclass, field
from typing import Any

from ..games import Game


@dataclass
class Figure:
    moves: list = field(default_factory=list)  # legal moves from a new Match, in order
    notes: list[dict] = field(default_factory=list)
    playout: int | None = None  # then random legal moves with this seed, to the end of the Match
    full: bool = False  # draw the full state (Battleship: both fleets), not the Public view
    turn: bool = True  # show whose turn it is (a forced board, a framed grid); off where it would distract


def label(text: Any, size: str = "m", **at) -> dict:
    return {"kind": "label", "at": at, "text": str(text), "size": size}


def ring(**at) -> dict:
    return {"kind": "ring", "at": at}


def arrow(start: dict, end: dict) -> dict:
    return {"kind": "arrow", "from": start, "to": end}


def box(start: dict, end: dict) -> dict:
    """A gold outline around everything from one anchor to the other (a ship, a row of cells)."""
    return {"kind": "box", "from": start, "to": end}


# Ultimate Tic-tac-toe

UTTT_BOARD_NUMBERS = ([label(b, "l", board=b) for b in range(9) if b != 4]  # the centre board numbers its cells
                      + [label(c, "s", cell=[4, c]) for c in range(9)])
UTTT = {
    "board": Figure(notes=UTTT_BOARD_NUMBERS),
    "first": Figure([[4, 2]], [ring(cell=[4, 2])]),
    "sent": Figure([[4, 2], [2, 6]], [arrow({"cell": [4, 2]}, {"board": 2}), arrow({"cell": [2, 6]}, {"board": 6})]),
    "won": Figure([[7, 3], [3, 7], [7, 0], [0, 7], [7, 6]], [ring(cell=[7, 6])]),
    "free": Figure([[1, 4], [4, 1], [1, 7], [7, 1], [1, 1]], [ring(cell=[1, 1])]),
    "dead": Figure([[5, 6], [6, 6], [6, 3], [3, 8], [8, 5], [5, 3], [3, 4], [4, 5], [5, 5], [5, 2], [2, 2], [2, 4],
                    [4, 4], [4, 2], [2, 5], [5, 7], [7, 8], [8, 7], [7, 3], [3, 7], [7, 5], [5, 4], [4, 6], [6, 8],
                    [8, 6], [6, 5], [5, 1], [1, 5], [5, 8], [8, 4], [4, 3], [3, 5], [5, 0]], [ring(cell=[5, 0])]),
    "match": Figure([[3, 1], [1, 0], [0, 2], [2, 4], [4, 7], [7, 5], [5, 4], [4, 3], [3, 2], [2, 8], [8, 8], [8, 1],
                     [1, 1], [1, 3], [3, 0], [0, 3], [4, 4], [4, 5], [5, 5], [5, 0], [0, 0], [0, 8], [8, 6], [6, 4],
                     [4, 1], [1, 4], [1, 7], [7, 3], [5, 3]]),
}

# Connect Four

# The waiting disc of the seat to move would hide the column labels and arrows: no turn shown. Notes are drawn in
# order: an arrow goes under the column number and ring it starts from.
C4_COLUMNS = [label(c, column=c) for c in range(7)]
CONNECT4 = {
    "board": Figure(notes=C4_COLUMNS + [label(r, row=r) for r in range(6)], turn=False),
    "drop": Figure([3, 3, 2, 3], [arrow({"column": 3}, {"cell": [2, 3]})] + C4_COLUMNS + [ring(column=3)], turn=False),
    "full": Figure([0, 0, 0, 0, 0, 0], C4_COLUMNS + [ring(column=0)], turn=False),
    "win": Figure(playout=1047),
    "draw": Figure(playout=344),
}

# Dots and Boxes

DOTS = {
    "grid": Figure([["h", 2, 1], ["v", 4, 5]], [label(i, row=i) for i in range(8)] + [label(i, col=i) for i in range(8)]
                   + [ring(line=["h", 2, 1]), ring(line=["v", 4, 5])], turn=False),
    "close": Figure([["h", 2, 2], ["h", 3, 2], ["v", 2, 2], ["h", 6, 6], ["v", 2, 3]], [ring(line=["v", 2, 3])]),
    "double": Figure([["h", 2, 2], ["h", 3, 2], ["v", 2, 2], ["h", 2, 3], ["h", 3, 3], ["v", 2, 4], ["v", 2, 3]],
                     [ring(line=["v", 2, 3])]),
    "end": Figure(playout=2),
}

# Battleship: seat 0's fleet touches (its Battleship and Cruiser lie side by side), seat 1's doesn't.

FLEETS = [
    [[1, 1, "h"], [3, 2, "v"], [3, 3, "v"], [8, 5, "h"], [5, 8, "v"]],
    [[0, 9, "v"], [6, 0, "h"], [2, 4, "h"], [9, 6, "h"], [4, 4, "v"]],
]
PLACEMENT = [FLEETS[seat][ship] for ship in range(5) for seat in (0, 1)]
SEAT1_SQUARES = [[r, 9] for r in range(5)] + [[6, c] for c in range(4)] + [[2, c] for c in range(4, 7)] \
    + [[9, c] for c in range(6, 9)] + [[4, 4], [5, 4]]
SEAT0_MISSES = [[0, c] for c in range(10)] + [[9, c] for c in range(6)]


def shots(seat0: list, seat1: list) -> list:
    """Seat 0's and seat 1's shots, taking turns, seat 0 first."""
    out = []
    for i, shot in enumerate(seat0):
        out.append(shot)
        if i < len(seat1):
            out.append(seat1[i])
    return out


BATTLESHIP = {
    "fleets": Figure(PLACEMENT, [label(i, "s", row=[0, i]) for i in range(10)]
                     + [label(i, "s", col=[0, i]) for i in range(10)]
                     + [ring(square=[0, 1, 1]), ring(square=[0, 3, 2])], full=True),
    "shots": Figure(PLACEMENT + shots([[2, 5], [7, 7], [6, 1]], [[0, 0], [1, 3]]), [ring(square=[1, 6, 1])], full=True),
    "sunk": Figure(PLACEMENT + shots([[4, 4], [5, 4]], [[0, 0]]),
                   [ring(square=[1, 5, 4]), box({"square": [1, 4, 4]}, {"square": [1, 5, 4]})], full=True),
    "win": Figure(PLACEMENT + shots(SEAT1_SQUARES, SEAT0_MISSES), full=True),
}

FIGURES: dict[str, dict[str, Figure]] = {"uttt": UTTT, "connect4": CONNECT4, "dots": DOTS, "battleship": BATTLESHIP}
# The picture the Arena page shows beside the Game's introduction: a board in full play, one of the rules page's.
COVERS = {"uttt": "match", "connect4": "win", "dots": "end", "battleship": "win"}


def still(game: Game, figure: Figure) -> dict:
    """The figure as the Renderer draws it: the view before its last move and after it, that move, who is to move
    next (and whether to show it), and the result once the Match is over."""
    state, before, last, last_seat = game.initial_state(0), None, None, None
    moves = list(figure.moves)
    rng = random.Random(figure.playout)
    while moves or (figure.playout is not None and game.to_move(state)):
        seat = min(game.to_move(state))
        move = moves.pop(0) if moves else rng.choice(game.legal_moves(state, seat))
        before, last, last_seat, state = state, move, seat, game.apply(state, seat, move)

    def shown(s):
        return None if s is None else {k: v for k, v in s.items() if k != "seed"} if figure.full else game.view(s, None)

    return {"view": shown(state), "before": shown(before), "last": last, "lastSeat": last_seat,
            "toMove": sorted(game.to_move(state)), "showTurn": figure.turn, "outcome": game.outcome(state),
            "notes": figure.notes}
