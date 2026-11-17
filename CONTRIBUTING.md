# Contributing to botingame

Bug reports and ideas: [GitHub Issues](https://github.com/BotInGame/botingame/issues). Pull requests are welcome.

## Licence of your contribution

Contributions come in under the licence they go out under (inbound = outbound):

- **Most of the repository** is under the [GNU GPL v3 or later](LICENSE), with the attribution term in
  [NOTICE](NOTICE). What you contribute to it is under GPL-3.0-or-later too, with that term.
- **Starter code** is under [0BSD](examples/LICENSE): the reference Bots in `examples/`, the code samples in the Game
  guides (`botingame/docs/<game>/guide.*.md`) and the starter Bot file `botingame new` writes (`TEMPLATE` in
  `botingame/cli/starter.py`). What you contribute to them is under 0BSD, so anyone can copy it into a Bot of any
  licence.

## Sign off your commits (DCO)

Each commit must be signed off, certifying the [Developer Certificate of Origin](https://developercertificate.org/):
that you wrote the change, or otherwise have the right to submit it under the licence above. Sign off with
`git commit -s`, which adds a line with your name and email to the commit message:

```
Signed-off-by: Your Name <you@example.com>
```

Forgot it? `git commit --amend -s` fixes the last commit, `git rebase --signoff main` the whole branch.

Before you open a pull request, run the checks in the README's [Development](README.md#development) section.
