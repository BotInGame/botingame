"""Rules pages: each Game's illustrated rules, for the website. Their pictures are positions played with the Game's
own code; their sections are not tested (the text will change)."""
import re

import pytest

from botingame.docs import LANGS, rules_page
from botingame.docs.figures import FIGURES
from botingame.docs.fill import PLACEHOLDER
from botingame.games import GAMES

CASES = [(key, lang) for key in GAMES for lang in LANGS]
FIGURE = re.compile(r"!\[([^\]]*)\]\(figure:([\w-]+)\)")


@pytest.mark.parametrize("key,lang", CASES)
def test_every_game_has_an_illustrated_rules_page_in_every_language(key, lang):
    page = rules_page(GAMES[key], lang)
    assert page["markdown"].strip() and not PLACEHOLDER.search(page["markdown"])
    used = {name for _, name in FIGURE.findall(page["markdown"])}
    assert used == set(page["figures"]) == set(FIGURES[key]), "every picture defined is shown, and only those"
    assert all(alt.strip() for alt, _ in FIGURE.findall(page["markdown"])), "every picture is described"
    assert page["cover"] in page["figures"], "the Arena page's picture is one the rules page shows"


@pytest.mark.parametrize("key", list(GAMES))
def test_a_picture_is_a_position_reached_by_legal_moves(key):
    g = GAMES[key]
    for name, still in rules_page(g, "en")["figures"].items():
        assert set(still) == {"view", "before", "last", "lastSeat", "toMove", "showTurn", "outcome", "notes"}, name
        assert "seed" not in still["view"]
        assert (still["outcome"] is None) == bool(still["toMove"]), name  # either someone moves, or it is over
        if still["last"] is not None:
            assert still["before"] is not None and still["lastSeat"] in (0, 1)


def test_pictures_follow_the_moves_they_are_made_of():
    figures = rules_page(GAMES["connect4"], "en")["figures"]
    assert all(row[0] is not None for row in figures["full"]["view"]["board"])  # column 0 filled to the top
    assert figures["full"]["view"]["board"][0][1:] == [None] * 6
    assert rules_page(GAMES["uttt"], "en")["figures"]["match"]["outcome"] == [1.0, 0.0]


def test_battleship_pictures_show_both_fleets():
    for still in rules_page(GAMES["battleship"], "en")["figures"].values():
        assert [len(f) for f in still["view"]["fleets"]] == [5, 5]


def test_a_picture_the_page_shows_must_exist(monkeypatch):
    monkeypatch.setattr("botingame.docs.pages.source", lambda game, lang, kind="guide": "![A board](figure:nope)")
    with pytest.raises(KeyError, match="nope"):
        rules_page(GAMES["uttt"], "en")


def test_an_unsupported_language_is_refused():
    with pytest.raises(ValueError, match="de"):
        rules_page(GAMES["uttt"], "de")
