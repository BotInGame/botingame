"""Ultimate Tic-tac-toe: nine tic-tac-toe sub-boards in a 3x3 grid."""
from .base import Game, IllegalMove

LINES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))
SEATS = (0, 1)


def _line_owner(marks: list) -> int | None:
    """The seat holding three in a line of a 3x3 grid (row-major), if any."""
    for a, b, c in LINES:
        if marks[a] in SEATS and marks[a] == marks[b] == marks[c]:
            return marks[a]
    return None


class UltimateTicTacToe(Game):
    id, name, version = "uttt", "Ultimate Tic-tac-toe", "1.0.0"
    rules = (
        "Move = [board, cell], both 0-8 row-major (board 0 is the top-left sub-board, cell 0 its top-left cell). "
        "Seat 0 (X) moves first, anywhere. Each move sends the next seat to the sub-board matching its cell; "
        "if that sub-board is decided (won or full), it may play in any undecided sub-board. Three in a line "
        "wins a sub-board; a full sub-board with no line is dead. Three won sub-boards in a line win the Match; "
        "once no undecided sub-board is left without such a line, the Match is a draw."
    )
    move_schema = {
        "type": "array", "minItems": 2, "maxItems": 2,
        "items": {"type": "integer", "minimum": 0, "maximum": 8},
    }
    _grid = {"type": "array", "minItems": 9, "maxItems": 9}
    view_schema = {
        "type": "object",
        "required": ["cells", "boards", "forced", "turn", "winner"],
        "additionalProperties": False,
        "properties": {
            "cells": {**_grid, "items": {**_grid, "items": {"enum": [None, 0, 1]}}},
            "boards": {**_grid, "items": {"enum": [None, 0, 1, "draw"]}},
            "forced": {"oneOf": [{"type": "null"}, {"type": "integer", "minimum": 0, "maximum": 8}]},
            "turn": {"type": "integer", "minimum": 0},
            "winner": {"enum": [None, 0, 1]},
        },
    }

    def initial_state(self, seed):
        return {"seed": seed, "cells": [[None] * 9 for _ in range(9)], "boards": [None] * 9,
                "forced": None, "turn": 0, "winner": None}

    def to_move(self, state):
        if self.outcome(state) is not None:
            return set()
        return {state["turn"] % 2}

    def outcome(self, state):
        if state["winner"] is not None:
            return [1.0, 0.0] if state["winner"] == 0 else [0.0, 1.0]
        if None not in state["boards"]:
            return [0.5, 0.5]
        return None

    def legal_moves(self, state, seat):
        if seat not in self.to_move(state):
            return []
        boards = range(9) if state["forced"] is None else [state["forced"]]
        return [[b, c] for b in boards if state["boards"][b] is None
                for c in range(9) if state["cells"][b][c] is None]

    def apply(self, state, seat, move):
        if (not isinstance(move, list) or any(type(x) is not int for x in move)
                or move not in self.legal_moves(state, seat)):
            raise IllegalMove(f"illegal move {move!r}")
        board, cell = move
        cells = [row[:] for row in state["cells"]]
        cells[board][cell] = seat
        boards = state["boards"][:]
        owner = _line_owner(cells[board])
        boards[board] = owner if owner is not None else ("draw" if None not in cells[board] else None)
        return {**state, "cells": cells, "boards": boards, "forced": cell if boards[cell] is None else None,
                "turn": state["turn"] + 1, "winner": _line_owner(boards)}
