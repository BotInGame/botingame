"""Each Game's documentation: its Game guide for Bot developers and its illustrated Rules page, in English and French.

The prose lives in one folder per Game (`<key>/guide.en.md`, `<key>/guide.fr.md`, `<key>/rules.en.md`,
`<key>/rules.fr.md`). `fill` fills its placeholders from the Game's code, `figures` plays the rules page's pictures,
and `pages` puts them together."""
from .pages import KINDS, LANGS, guide, prose_file, rules_page

__all__ = ["KINDS", "LANGS", "guide", "prose_file", "rules_page"]
