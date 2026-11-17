"""Dots and Boxes rules, through the Game interface."""
import pytest

from botingame.games import GAMES, IllegalMove

game = GAMES["dots"]


def play(moves, seed=0):
    state = game.initial_state(seed)
    for move in moves:
        (seat,) = game.to_move(state)
        state = game.apply(state, seat, move)
    return state


def test_seat_0_moves_first_and_may_draw_any_of_the_112_lines():
    s = game.initial_state(0)
    assert game.to_move(s) == {0}
    moves = game.legal_moves(s, 0)
    assert len(moves) == 112  # 8 rows of 7 across, 7 rows of 8 down
    assert ["h", 7, 6] in moves and ["v", 6, 7] in moves
    assert game.legal_moves(s, 1) == []


def test_a_line_that_completes_no_box_passes_the_move():
    s = play([["h", 0, 0]])
    assert game.to_move(s) == {1}
    assert game.view(s, None)["h"][0][0] == 0
    assert ["h", 0, 0] not in game.legal_moves(s, 1)


# The top-left box: its top, bottom and left sides, then seat 1 closes it with its right side.
CLOSE_TOP_LEFT = [["h", 0, 0], ["h", 1, 0], ["v", 0, 0], ["v", 0, 1]]


def test_completing_a_box_scores_it_and_gives_the_same_seat_another_move():
    s = play(CLOSE_TOP_LEFT)
    view = game.view(s, None)
    assert view["boxes"][0][0] == 1
    assert view["scores"] == [0, 1]
    assert game.to_move(s) == {1}
    assert view["next"] == 1
    assert game.outcome(s) is None


def test_the_extra_move_is_a_full_move_and_passes_on_if_it_completes_nothing():
    s = play([*CLOSE_TOP_LEFT, ["h", 5, 4]])
    assert game.to_move(s) == {0}
    assert game.view(s, None)["turn"] == 5


# Two boxes side by side, each with three sides drawn; their shared side closes both.
DOUBLE = [["h", 0, 0], ["h", 1, 0], ["v", 0, 0], ["h", 0, 1], ["h", 1, 1], ["v", 0, 2], ["v", 0, 1]]


def test_a_line_shared_by_two_three_sided_boxes_scores_both_and_moves_again():
    s = play(DOUBLE)
    view = game.view(s, None)
    assert view["boxes"][0][:2] == [0, 0]
    assert view["scores"] == [2, 0]
    assert game.to_move(s) == {0}


# Every horizontal line row by row, then every vertical one: the 56 horizontals close nothing (28 each), so seat 0
# starts the verticals; each row's first vertical closes nothing, and the next seat then takes that whole row.
ALL_ROWS = [["h", r, c] for r in range(8) for c in range(7)] + [["v", r, c] for r in range(7) for c in range(8)]


def test_the_match_ends_when_every_box_is_taken_and_the_most_boxes_win():
    s = play(ALL_ROWS)
    view = game.view(s, None)
    assert view["boxes"] == [[1] * 7, [0] * 7, [1] * 7, [0] * 7, [1] * 7, [0] * 7, [1] * 7]
    assert view["scores"] == [21, 28]
    assert game.outcome(s) == [0.0, 1.0]
    assert game.to_move(s) == set()
    assert view["next"] is None
    assert game.legal_moves(s, 1) == []


def test_one_line_before_the_end_the_match_is_still_on():
    s = play(ALL_ROWS[:-1])
    assert game.outcome(s) is None
    assert game.legal_moves(s, 1) == [["v", 6, 7]]


@pytest.mark.parametrize("move", [
    ["h", 0, 0],  # already drawn
    ["h", 8, 0], ["h", 0, 7], ["v", 7, 0], ["v", 0, 8], ["h", -1, 0],  # off the board
    ["d", 0, 0], ["h", True, 1], ["h", 1.0, 1], ["h", 1], "h00", None,
])
def test_illegal_moves_are_rejected(move):
    s = play([["h", 0, 0]])
    with pytest.raises(IllegalMove):
        game.apply(s, 1, move)


def test_only_the_seat_to_move_may_move():
    with pytest.raises(IllegalMove):
        game.apply(game.initial_state(0), 1, ["h", 0, 0])
