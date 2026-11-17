"""A Game's pages: its Game guide and its Rules page, read from the prose shipped in this package and filled."""
import re
from importlib.resources import files

from ..games import Game
from .figures import COVERS, FIGURES, still
from .fill import fill

LANGS = ("en", "fr")
KINDS = ("guide", "rules")  # the Game guide (Bot developers, `botingame game`) and the rules page (the website)


def prose_file(key: str, lang: str, kind: str = "guide") -> str:
    """Where a Game's guide or rules page in `lang` lives, inside the `botingame.docs` package: in the Game's own
    folder, named by kind and language (`<key>/guide.en.md`, `<key>/rules.fr.md`)."""
    if lang not in LANGS:
        raise ValueError(f"no guides in {lang!r}: the languages are {', '.join(LANGS)}")
    return f"{key}/{kind}.{lang}.md"


def source(game: Game, lang: str, kind: str = "guide") -> str:
    """The prose, placeholders unfilled."""
    return files("botingame.docs").joinpath(*prose_file(game.id, lang, kind).split("/")).read_text("utf-8")


def filled(game: Game, lang: str, kind: str) -> str:
    """The prose, placeholders filled."""
    return fill(source(game, lang, kind), game, f"{game.id} {kind} ({lang})")


def guide(game: Game, lang: str = "en") -> str:
    """The Game's guide for Bot developers in `lang`, as Markdown, its placeholders filled from the Game's code."""
    return filled(game, lang, "guide")


FIGURE = re.compile(r"!\[[^\]]*\]\(figure:([\w-]+)\)")


def rules_page(game: Game, lang: str = "en") -> dict:
    """The Game's illustrated rules page in `lang`: its Markdown, whose pictures are images with a `figure:<name>`
    source, each picture's position for the Renderer to draw (see figures.py), and the `cover`: the picture the Arena
    page shows."""
    markdown = filled(game, lang, "rules")
    defined = FIGURES.get(game.id, {})
    names = dict.fromkeys(FIGURE.findall(markdown))
    if missing := [n for n in names if n not in defined]:
        raise KeyError(f"{game.id} rules ({lang}): no picture named {', '.join(missing)}")
    return {"markdown": markdown, "figures": {n: still(game, defined[n]) for n in names}, "cover": COVERS[game.id]}
