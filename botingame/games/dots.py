"""Dots and Boxes on an 8x8 grid of dots (7x7 boxes): closing a box gives the same seat another move."""
from .base import Game, IllegalMove

BOXES = 7  # boxes per side; 49 in all, an odd count, so no Match finished on the board is level
DOTS = BOXES + 1


def _empty_grid(rows: int, cols: int) -> list[list]:
    return [[None] * cols for _ in range(rows)]


def _closed(h: list[list], v: list[list], r: int, c: int) -> bool:
    """Box (r, c) has all four sides drawn."""
    return None not in (h[r][c], h[r + 1][c], v[r][c], v[r][c + 1])


def _grid_schema(rows: int, cols: int) -> dict:
    """The schema of a rows x cols grid of seats (or null)."""
    row = {"type": "array", "minItems": cols, "maxItems": cols, "items": {"enum": [None, 0, 1]}}
    return {"type": "array", "minItems": rows, "maxItems": rows, "items": row}


def _boxes_of(kind: str, r: int, c: int) -> list[tuple[int, int]]:
    """The one or two boxes a line is a side of."""
    if kind == "h":  # the bottom of the box above, the top of the box below
        return [(br, c) for br in (r - 1, r) if 0 <= br < BOXES]
    return [(r, bc) for bc in (c - 1, c) if 0 <= bc < BOXES]


class DotsAndBoxes(Game):
    id, name, version = "dots", "Dots and Boxes", "1.0.0"
    rules = (
        f"A {DOTS}x{DOTS} grid of dots ({BOXES}x{BOXES} boxes); row 0 is the top, column 0 the left. "
        f'Move = ["h", row, col] for the line from dot (row, col) to dot (row, col+1) '
        f"(row 0-{BOXES}, col 0-{BOXES - 1}), "
        f'or ["v", row, col] for the line from dot (row, col) to dot (row+1, col) '
        f"(row 0-{BOXES - 1}, col 0-{BOXES}). "
        "Seat 0 moves first; each move draws one undrawn line. A line that closes the fourth side of a box (or of two "
        "boxes) scores them for the seat that drew it, and that seat moves again; otherwise the other seat moves. "
        "Once every line is drawn, the seat with more boxes wins."
    )
    move_schema = {
        "oneOf": [
            {"type": "array", "minItems": 3, "maxItems": 3, "prefixItems": [
                {"const": "h"},
                {"type": "integer", "minimum": 0, "maximum": BOXES},
                {"type": "integer", "minimum": 0, "maximum": BOXES - 1},
            ]},
            {"type": "array", "minItems": 3, "maxItems": 3, "prefixItems": [
                {"const": "v"},
                {"type": "integer", "minimum": 0, "maximum": BOXES - 1},
                {"type": "integer", "minimum": 0, "maximum": BOXES},
            ]},
        ],
    }

    view_schema = {
        "type": "object",
        "required": ["h", "v", "boxes", "scores", "next", "turn"],
        "additionalProperties": False,
        "properties": {
            "h": _grid_schema(DOTS, BOXES),
            "v": _grid_schema(BOXES, DOTS),
            "boxes": _grid_schema(BOXES, BOXES),
            "scores": {"type": "array", "minItems": 2, "maxItems": 2, "items": {"type": "integer", "minimum": 0}},
            "next": {"enum": [None, 0, 1]},
            "turn": {"type": "integer", "minimum": 0},
        },
    }

    def initial_state(self, seed):
        return {"seed": seed, "h": _empty_grid(DOTS, BOXES), "v": _empty_grid(BOXES, DOTS),
                "boxes": _empty_grid(BOXES, BOXES),
                "scores": [0, 0], "next": 0, "turn": 0}

    def to_move(self, state):
        return set() if state["next"] is None else {state["next"]}

    def outcome(self, state):
        if state["next"] is not None:
            return None
        a, b = state["scores"]
        return [1.0, 0.0] if a > b else [0.0, 1.0] if b > a else [0.5, 0.5]

    def legal_moves(self, state, seat):
        if seat not in self.to_move(state):
            return []
        return [[kind, r, c] for kind in ("h", "v") for r, row in enumerate(state[kind])
                for c, owner in enumerate(row) if owner is None]

    def apply(self, state, seat, move):
        if (not isinstance(move, list) or len(move) != 3 or any(type(x) is not int for x in move[1:])
                or move not in self.legal_moves(state, seat)):
            raise IllegalMove(f"illegal move {move!r}")
        kind, r, c = move
        lines = {k: [row[:] for row in state[k]] for k in ("h", "v")}
        lines[kind][r][c] = seat
        boxes = [row[:] for row in state["boxes"]]
        scores = state["scores"][:]
        closed = [(br, bc) for br, bc in _boxes_of(kind, r, c) if _closed(lines["h"], lines["v"], br, bc)]
        for br, bc in closed:
            boxes[br][bc] = seat
            scores[seat] += 1
        over = sum(scores) == BOXES * BOXES
        return {**state, **lines, "boxes": boxes, "scores": scores, "turn": state["turn"] + 1,
                "next": None if over else seat if closed else 1 - seat}
