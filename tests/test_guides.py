"""Game guides: one per Game and language, filled from the Game's code. Their sections are not tested: the template
will change."""
import json
import re

import pytest

from botingame.docs import LANGS, guide
from botingame.docs.fill import PLACEHOLDER, example
from botingame.games import GAMES

CASES = [(key, lang) for key in GAMES for lang in LANGS]


@pytest.mark.parametrize("key,lang", CASES)
def test_every_game_has_a_guide_in_every_language(key, lang):
    assert guide(GAMES[key], lang).strip()


def test_an_unsupported_language_is_refused():
    with pytest.raises(ValueError, match="de"):
        guide(GAMES["uttt"], "de")


def table_fields(markdown: str) -> set[str]:
    """The `names` in the first cell of every Markdown table row."""
    return {name for line in markdown.splitlines() if line.lstrip().startswith("|")
            for name in re.findall(r"`([^`]+)`", line.strip().strip("|").split("|")[0])}


@pytest.mark.parametrize("key,lang", CASES)
@pytest.mark.parametrize("schema", ["view_schema", "move_schema"])
def test_the_field_tables_explain_every_top_level_property(key, lang, schema):
    properties = getattr(GAMES[key], schema).get("properties", {})
    missing = set(properties) - table_fields(guide(GAMES[key], lang))
    assert not missing, f"{key} ({lang}): no table row for {sorted(missing)}"


def test_a_field_missing_from_the_tables_is_caught():
    assert table_fields("| `board` | the board |\n| --- | --- |\n| `turn`, `x` | moves |") == {"board", "turn", "x"}
    assert "winner" not in table_fields("The `winner` field.\n| `board` | `winner` |")


@pytest.mark.parametrize("key,lang", CASES)
def test_the_guide_shows_the_schemas_and_an_example_from_the_games_code(key, lang):
    g = GAMES[key]
    text = guide(g, lang)
    ex = example(g)
    assert not PLACEHOLDER.search(text)  # no placeholder left
    for value in (g.view_schema, g.move_schema, ex.view):
        assert json.loads(json.dumps(value)) in json_blocks(text), (key, lang)
    assert json.dumps(ex.move) in text


def json_blocks(markdown: str) -> list:
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)```", markdown, re.S)]


@pytest.mark.parametrize("key", list(GAMES))
def test_the_example_is_mid_match_and_its_move_is_legal(key):
    g = GAMES[key]
    ex = example(g)
    assert ex.turn > 0 and ex.view["turn"] == ex.turn
    assert ex.move in ex.legal_moves
    assert example(g) == ex  # the same every time


def test_the_battleship_example_hides_the_opponents_fleet():
    ex = example(GAMES["battleship"])
    assert set(ex.view) == set(GAMES["battleship"].view_schema["properties"])  # its own `fleet`, no `fleets`
    assert len(ex.view["fleet"]) == 5 and ex.view["phase"] == "shooting"
    assert all(ex.view["sunk"])  # a sunk ship on each side, the only enemy ships a view shows


def test_an_unknown_placeholder_fails_loudly(monkeypatch):
    monkeypatch.setattr("botingame.docs.pages.source", lambda game, lang, kind="guide": "{{view_schema}} {{nope}}")
    with pytest.raises(KeyError, match="nope"):
        guide(GAMES["uttt"])
