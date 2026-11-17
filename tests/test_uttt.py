"""Ultimate Tic-tac-toe rules, through the Game interface."""
import pytest

from botingame.games import GAMES, IllegalMove

game = GAMES["uttt"]


def play(moves, seed=0):
    state = game.initial_state(seed)
    for move in moves:
        (seat,) = game.to_move(state)
        state = game.apply(state, seat, move)
    return state


def test_first_move_is_free_and_x_moves_first():
    s = game.initial_state(0)
    assert game.to_move(s) == {0}
    assert len(game.legal_moves(s, 0)) == 81


def test_next_move_goes_to_the_board_matching_the_last_cell():
    s = play([[4, 2]])
    assert game.to_move(s) == {1}
    assert game.legal_moves(s, 1) == [[2, c] for c in range(9)]
    with pytest.raises(IllegalMove):
        game.apply(s, 1, [3, 0])


# X takes the top row of board 0 while O sends it back there: [0,1] [1,0] [0,2] [2,0] [0,0]
X_WINS_BOARD_0 = [[0, 1], [1, 0], [0, 2], [2, 0], [0, 0]]


def test_three_in_a_line_wins_the_sub_board():
    s = play(X_WINS_BOARD_0)
    assert game.view(s, None)["boards"] == [0, None, None, None, None, None, None, None, None]
    assert game.outcome(s) is None


def test_sent_to_a_decided_board_the_mover_chooses_any_undecided_board():
    s = play(X_WINS_BOARD_0)  # X's last cell is 0, but board 0 is won
    moves = game.legal_moves(s, 1)
    assert {b for b, _ in moves} == {1, 2, 3, 4, 5, 6, 7, 8}
    assert len(moves) == 9 * 8 - 2  # O's two marks in boards 1 and 2
    assert game.view(s, None)["forced"] is None
    with pytest.raises(IllegalMove):
        game.apply(s, 1, [0, 5])  # the empty cells of a won board are closed


# X wins boards 0 (middle row), 1 (bottom row) and 2 (middle row): the top row of boards.
# O only answers with cells that send X back to the board X is filling.
X_WINS_TOP_ROW = [
    [0, 3], [3, 0], [0, 4], [4, 0], [0, 5],
    [5, 1], [1, 6], [6, 1], [1, 7], [7, 1], [1, 8],
    [8, 2], [2, 3], [3, 2], [2, 4], [4, 2], [2, 5],
]


def test_three_won_boards_in_a_line_win_the_match():
    s = play(X_WINS_TOP_ROW)
    view = game.view(s, None)
    assert view["boards"][:3] == [0, 0, 0]
    assert view["winner"] == 0
    assert game.outcome(s) == [1.0, 0.0]
    assert game.to_move(s) == set()
    assert game.legal_moves(s, 1) == []


def test_o_wins_the_match_with_the_same_plan_after_an_opening_x_move():
    # X opens [8, 0], sending O to board 0; O then plays X's plan above, X answering as O did
    s = play([[8, 0], *X_WINS_TOP_ROW])
    assert game.view(s, None)["winner"] == 1
    assert game.outcome(s) == [0.0, 1.0]


# A random playout (seed 14) where every board ends decided, the centre one full with no line:
#   O X X
#   X - O
#   O X X
DRAWN_MATCH = [
    [1, 4], [4, 8], [8, 3], [3, 4], [4, 4], [4, 2], [2, 1], [1, 8], [8, 5], [5, 7], [7, 6], [6, 6], [6, 1],
    [1, 2], [2, 4], [4, 3], [3, 6], [6, 8], [8, 2], [2, 3], [3, 8], [8, 8], [8, 7], [7, 2], [2, 2], [2, 8],
    [8, 4], [4, 1], [1, 0], [0, 1], [1, 1], [1, 6], [6, 0], [0, 2], [2, 6], [6, 3], [3, 3], [3, 5], [5, 8],
    [0, 8], [1, 5], [5, 4], [4, 6], [6, 4], [4, 0], [0, 7], [7, 8], [5, 2], [5, 5], [5, 1], [1, 7], [7, 4],
    [4, 5], [7, 3], [3, 2], [4, 7], [7, 0], [0, 0], [3, 1], [6, 7], [7, 5], [3, 0], [3, 7], [7, 1], [7, 7],
]


def test_a_full_sub_board_without_a_line_is_dead():
    view = game.view(play(DRAWN_MATCH), None)
    assert None not in view["cells"][4]
    assert view["boards"][4] == "draw"


def test_no_undecided_board_left_and_no_line_of_boards_is_a_draw():
    s = play(DRAWN_MATCH)
    assert game.view(s, None)["boards"] == [1, 0, 0, 0, "draw", 1, 1, 0, 0]
    assert any(None in cells for cells in game.view(s, None)["cells"])  # empty cells remain, but in decided boards
    assert game.outcome(s) == [0.5, 0.5]
    assert game.to_move(s) == set()
    assert game.view(s, None)["winner"] is None


def test_booleans_are_not_cells():
    with pytest.raises(IllegalMove):
        game.apply(game.initial_state(0), 0, [True, 0])
