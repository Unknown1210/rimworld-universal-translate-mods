# Changelog

Versioning: `0.NNN` (0.001, 0.002, ...) until the maintainer declares 1.0. **Every commit/push bumps the number** and adds an entry here
(newest first). The same text goes in the commit message: `v0.NNN: short title` + list of changes.
Version lives in `VERSION`; run `python tools/set_version.py` to sync it into the helper and the mod.

## v0.004 - 2026-10-13
- Adicionado: na aba "Traduzir mods" do executável, a lista numerada das pastas pesquisadas aparece antes da barra de progresso: as pastas padrão ("padrão") e as que o usuário adicionou ("adicionada por você", ou "não encontrada"). As pastas adicionadas ficam salvas e são pesquisadas sempre que o programa abre, todas ao mesmo tempo.
- Corrigido: com a janela de detalhes de um mod aberta, trocar o idioma da janela principal não atualizava a janela de detalhes. Agora ela é redesenhada na hora no novo idioma (título, abas, colunas, motivos e o texto selecionado), mantendo a aba e a linha escolhidas.
- Alterado: na tabela da aba "Traduzir mods", os nomes das colunas e o conteúdo ficam centralizados, exceto o nome do mod, que fica à esquerda.
- Adicionado: coluna "Pasta" depois de "Estado": clicar em "Abrir pasta" na linha de um mod abre a pasta dele no explorador de arquivos (o cursor vira mãozinha sobre ela; dois cliques nessa coluna não abrem a janela de detalhes).
- Adicionado: botão "Excluir traduções" na aba "Traduzir mods": apaga todas as traduções salvas do idioma escolhido, depois de perguntar. Os mods voltam a aparecer como novos; as correções manuais (`overrides`) são mantidas.
- Adicionado: idiomas de destino "Português (Brasil)" e "Português (Portugal)", cada um com o seu modelo de tradução (o modelo do Brasil é o `pb` do Argos) e a sua pasta de idioma do RimWorld (`PortugueseBrazilian` e `Portuguese`). Configurações antigas com "pt" viram "Português (Brasil)", e as traduções, correções e o estado já salvos são renomeados sem perder nada.
- Alterado: a lista de idiomas de destino mostra todos os idiomas com modelo de tradução (49) em vez dos 15 mais comuns, sempre por extenso. O README lista todos.
- Adicionado: o texto da tela do mod também em Português de Portugal (pasta `Languages/Portuguese`).
- Adicionado: no jogo, atalho de teclado para ativar/desativar as traduções em tempo real (uma tecla, sozinha ou com Shift, Ctrl ou Alt; ex.: Shift + Tab), escolhido em Opções → Mods → Auto Translate, com aviso na tela. Não dispara ao digitar em uma caixa de texto.
- Alterado: README e descrição do mod não falam mais "endereço 127.0.0.1": explicam que a conexão entre o jogo e o programa fica só dentro do computador (não passa pela internet nem pela rede) e exige senha; nova seção "Segurança da conexão" e a origem do modelo (Argos Translate, sem conta nem assinatura). A janela do executável mostra "Em execução (só neste computador, porta ...)".
- Corrigido: com o modo desenvolvedor ligado, textos sem tradução apareciam com acentos estranhos ("Séàrçh ànd rèsçùè") em nomes e descrições de mods. O mod agora entrega o texto original no lugar do texto marcado pelo jogo (método `Translator.PseudoTranslated`), com uma opção em Avançado para desligar isso.
- Alterado: README atualizado (pastas pesquisadas, excluir traduções, atalho, idiomas, detalhes que trocam de idioma).
- Adicionado: testes: 70 no auxiliar (eram 66), todos rodando com a janela de verdade; o teste do mod passou a cobrir as variantes do português.
- Verificado: o mod compila sem erros contra a API real do RimWorld 1.6; os testes do mod (Mono) e do auxiliar (com janela) passaram.
- Não validado ainda: o atalho de teclado e a escolha dele dentro do jogo de verdade (só compila e passa pelos testes simulados); a qualidade do modelo do português do Brasil; a janela no Windows; a correção dos acentos estranhos no jogo de verdade (o método existe na API do jogo, mas não vi quem o chama; se o texto acentuado vier de outro lugar, a opção não resolve).

## v0.003 - 2026-10-13
- Alterado: o aviso "em desenvolvimento" e a seção "Estado atual" do README, e a descrição do mod na tela de Mods (inglês e português), mostram a versão atual em vez de "0.x"; o `tools/set_version.py` atualiza esses trechos sozinho e a verificação do CI confere.
- Adicionado: no "Estado atual" do README, o que ainda não foi validado (tradução com modelos reais em mods de verdade e a tela do mod dentro do jogo).

## v0.002 - 2026-10-13
- Adicionado: o README mostra a versão atual no topo ("Versão atual") e o `tools/set_version.py` atualiza essa linha sozinho; a verificação de versão do CI falha se o README ficar desatualizado.
- Alterado: regras do projeto (`CLAUDE.md`): trabalhar direto na `main`, sem branches extras nem pull requests, e manter o README atualizado a cada versão.

## v0.001 - 2026-10-13
Início deste repositório: reúne o resultado do projeto anterior (versões 0.1 a 0.13 do protótipo; o histórico antigo não foi trazido).
- Adicionado: mod do jogo (C#, Harmony, RimWorld 1.6) que traduz automaticamente os outros mods instalados, só o que não tem tradução, detectando o idioma de cada mod; falha de um mod desliga só aquele mod.
- Adicionado: executável auxiliar (Python, modelos offline) com janela, atualização pelo próprio programa, relatório de problema e a aba "Traduzir mods", que traduz todos os mods instalados (mesmo os desativados) antes de abrir o jogo, com janela de detalhes por mod.
- Adicionado: arquivos de tradução que só repetem o texto original não contam como tradução; os 15 idiomas de destino mais comuns.
- Adicionado: CI (Linux e Windows), release automática com `.exe` e mod compilado, verificação do pacote e testes (auxiliar e mod).
- Alterado: numeração das versões passa a ter três dígitos (0.001, 0.002, ...). O atualizador e os endereços do GitHub apontam para este repositório.
- Não validado ainda: o mod dentro do RimWorld de verdade, tradução com modelos reais, e se o caso do mod "Misstall's Furniture" é o de arquivo que só repete o original.
