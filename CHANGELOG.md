# Changelog

Versioning: `0.NNN` (0.001, 0.002, ...) until the maintainer declares 1.0. **Every commit/push bumps the number** and adds an entry here
(newest first). The same text goes in the commit message: `v0.NNN: short title` + list of changes.
Version lives in `VERSION`; run `python tools/set_version.py` to sync it into the helper and the mod.

## v0.001 - 2026-10-13
Início deste repositório: reúne o resultado do projeto anterior (versões 0.1 a 0.13 do protótipo; o histórico antigo não foi trazido).
- Adicionado: mod do jogo (C#, Harmony, RimWorld 1.6) que traduz automaticamente os outros mods instalados, só o que não tem tradução, detectando o idioma de cada mod; falha de um mod desliga só aquele mod.
- Adicionado: executável auxiliar (Python, modelos offline) com janela, atualização pelo próprio programa, relatório de problema e a aba "Traduzir mods", que traduz todos os mods instalados (mesmo os desativados) antes de abrir o jogo, com janela de detalhes por mod.
- Adicionado: arquivos de tradução que só repetem o texto original não contam como tradução; os 15 idiomas de destino mais comuns.
- Adicionado: CI (Linux e Windows), release automática com `.exe` e mod compilado, verificação do pacote e testes (auxiliar e mod).
- Alterado: numeração das versões passa a ter três dígitos (0.001, 0.002, ...). O atualizador e os endereços do GitHub apontam para este repositório.
- Não validado ainda: o mod dentro do RimWorld de verdade, tradução com modelos reais, e se o caso do mod "Misstall's Furniture" é o de arquivo que só repete o original.
