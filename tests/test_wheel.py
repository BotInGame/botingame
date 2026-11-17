"""The built wheel ships what the package reads at run time: every Game guide and rules page."""
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from botingame.docs import KINDS, LANGS, prose_file
from botingame.games import GAMES

PACKAGE = Path(__file__).resolve().parents[1]


def test_a_games_prose_lives_in_its_own_folder_named_by_kind_and_language():
    assert prose_file("connect4", "en") == "connect4/guide.en.md"
    assert prose_file("dots", "fr", "rules") == "dots/rules.fr.md"


@pytest.mark.skipif(shutil.which("uv") is None, reason="needs uv to build the wheel")
def test_the_wheel_contains_every_game_guide_and_rules_page(tmp_path):
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(tmp_path), str(PACKAGE)], check=True,
                   capture_output=True)
    [wheel] = tmp_path.glob("botingame-*.whl")
    names = set(zipfile.ZipFile(wheel).namelist())
    assert not [n for n in names if n.startswith("botingame/games/") and n.endswith(".md")], "games/ holds only code"
    for key in GAMES:
        for lang in LANGS:
            for kind in KINDS:
                assert f"botingame/docs/{prose_file(key, lang, kind)}" in names, (key, lang, kind)
