# Project rules (RimWorld Auto Translate)

## Versioning (mandatory, set by the maintainer)
- Version scheme is `0.NNN` with three digits (0.001, 0.002, 0.003 ...) with no upper limit until the maintainer explicitly says it is 1.0.
- **Every commit/push** must: bump the number in `VERSION`, run `python tools/set_version.py` (syncs helper + mod), add a
  `## v0.NNN - date` entry at the top of `CHANGELOG.md` describing what changed, and run `python tools/set_version.py --check`.
- Commit message format (simple language, in Portuguese): first line `v0.NNN: título curto`, a blank line, then a
  **bullet list of every item changed** (`- Adicionado: ...`, `- Corrigido: ...`, `- Alterado: ...`, `- Removido: ...`),
  and nothing else. The same bullet list goes in the `CHANGELOG.md` entry.
- Do not call something 1.0 unless the maintainer says so.

## Working agreements
- Write user-facing explanations in Portuguese (Brazil). Be explicit about what was NOT tested.
- Default branch: `main`. Do not open PRs unless asked.

## Privacy: this repository is PUBLIC (mandatory)
- Never put in a commit message, PR, issue, changelog, code, comment or any file: links to chat/agent sessions (claude.ai/code/session_...),
  `Co-Authored-By` trailers, `Claude-Session` trailers, or the name/version of the AI model. Credit to Claude is given only in the README and
  in the mod description, in plain words.
- Never commit personal data: the maintainer's e-mail (use the GitHub noreply address for authorship: `Unknown1210 <172444478+Unknown1210@users.noreply.github.com>`), local paths, tokens or passwords.
- Before every push: `git log -1 --format=%B` must contain only the version title and the bullet list.
- Tests: `python -I -m unittest discover -s helper/tests` and `mod/tools/run-tests.sh` (needs mono-mcs).
- The commit message and CHANGELOG entry list everything changed in that version. Check all files for private data before pushing (`git grep` for session links, e-mails, local paths).
