"""Connect Four on a 7x6 board."""
from .base import Game, IllegalMove

ROWS, COLS, NEED = 6, 7, 4


def _line_winner(board: list[list[int | None]]) -> int | None:
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if p is None:
                continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if all(
                    0 <= r + i * dr < ROWS
                    and 0 <= c + i * dc < COLS
                    and board[r + i * dr][c + i * dc] == p
                    for i in range(NEED)
                ):
                    return p
    return None


class ConnectFour(Game):
    id, name, version = "connect4", "Connect Four", "1.0.0"
    rules = "Move = column index 0-6. Row 0 is the top. Four in a row wins."
    move_schema = {"type": "integer", "minimum": 0, "maximum": COLS - 1}
    view_schema = {
        "type": "object",
        "required": ["board", "turn", "winner"],
        "additionalProperties": False,
        "properties": {
            "board": {
                "type": "array", "minItems": ROWS, "maxItems": ROWS,
                "items": {
                    "type": "array", "minItems": COLS, "maxItems": COLS,
                    "items": {"enum": [None, 0, 1]},
                },
            },
            "turn": {"type": "integer", "minimum": 0},
            "winner": {"enum": [None, 0, 1]},
        },
    }

    def initial_state(self, seed):
        return {"seed": seed, "board": [[None] * COLS for _ in range(ROWS)], "turn": 0, "winner": None}

    def to_move(self, state):
        if self.outcome(state) is not None:
            return set()
        return {state["turn"] % 2}

    def outcome(self, state):
        if state["winner"] is not None:
            return [1.0, 0.0] if state["winner"] == 0 else [0.0, 1.0]
        if all(cell is not None for cell in state["board"][0]):
            return [0.5, 0.5]
        return None

    def legal_moves(self, state, seat):
        if seat not in self.to_move(state):
            return []
        return [c for c in range(COLS) if state["board"][0][c] is None]

    def apply(self, state, seat, move):
        if isinstance(move, bool) or move not in self.legal_moves(state, seat):
            raise IllegalMove(f"illegal move {move!r}")
        row = max(r for r in range(ROWS) if state["board"][r][move] is None)
        board = [row_[:] for row_ in state["board"]]
        board[row][move] = seat
        return {**state, "board": board, "turn": state["turn"] + 1, "winner": _line_winner(board)}
