# Changelog

Versioning: `0.NNN` (0.001, 0.002, ...) until the maintainer declares 1.0. **Every commit/push bumps the number** and adds an entry here
(newest first). The same text goes in the commit message: `v0.NNN: short title` + list of changes.
Version lives in `VERSION`; run `python tools/set_version.py` to sync it into the helper and the mod.

## v0.008 - 2026-10-13
- Corrigido: "Atualizar agora" falhava com "[Errno 22] Invalid argument" no arquivo `RimWorldAutoTranslate.dll` quando o RimWorld estava aberto: o Windows não deixa gravar por cima de uma DLL que o jogo carregou. Agora a DLL antiga é posta de lado (`.old`, que o jogo ignora) e a nova é gravada; o jogo usa a nova na próxima abertura. O `.old` é apagado na próxima atualização. Se mesmo assim não der para gravar algum arquivo do mod, a mensagem diz para fechar o RimWorld.
- Corrigido: quando o mod não podia ser atualizado, a janela mostrava "A atualização falhou" e NÃO reiniciava, embora o executável novo já estivesse no lugar (parecia que nada tinha sido baixado). Agora o executável novo abre e o antigo fecha mesmo assim, e a mensagem diz que só o mod ficou sem atualizar (com mais tempo para ler antes de reiniciar).
- Corrigido: um segundo clique em "Atualizar agora" depois de uma atualização que não reiniciou falhava com "[WinError 5] Acesso negado" no arquivo `.exe.old` (o programa antigo ainda rodava a partir dele e o Windows não deixa apagar um arquivo em uso). Agora, se o executável do disco já é a versão nova, ele só abre a nova sem baixar nem trocar nada; e um `.old` que não dá para apagar não impede mais a troca (o arquivo é guardado com outro nome, e os `.old` antigos são apagados quando o programa abre).
- Alterado: no README, a divisória entre os itens das listas agora vai até o fim da frase (linha de traço mais longa, ainda simples e sem espaço grande).
- Adicionado: testes do atualizador: DLL do mod em uso, mensagem clara quando não dá para gravar, segundo clique depois de uma atualização, `.old` que não pode ser apagado, e a janela reiniciando mesmo com problema no mod (76 testes no auxiliar).
- Não validado ainda: a atualização no Windows de verdade com o RimWorld aberto (a troca de uma DLL em uso foi simulada nos testes; no Windows o comportamento é o descrito pela documentação do sistema); a largura da divisória do README em telas estreitas (em uma tela estreita ela pode quebrar em duas linhas).

## v0.007 - 2026-10-13
- Alterado: no README, a linha divisória passa a separar TODOS os itens de TODAS as listas (numeradas e com marcadores), e não só os de "Como funciona", "Instalação" e "Aviso do Windows": 10 listas, 32 divisórias. A divisória ficou curta e simples (uma linha curta de traço no fim de cada item, sem o espaço grande da linha larga de antes). As listas numeradas voltam a seguir na sequência normal (1, 2, 3...).
- Não validado ainda: como o GitHub mostra as divisórias curtas (conferido só em um conversor local de Markdown).

## v0.006 - 2026-10-13
- Corrigido: a v0.005 não gerou release (nem `.exe` nem zip): o teste da janela falhou no Windows do GitHub, porque pedia uma janela de 1300 px e a tela do servidor é menor, e a release só sai se os testes passam. O teste agora usa larguras que cabem na tela (820 a 960 px). Esta versão traz tudo o que estava na v0.005, que ficou sem arquivos para baixar.
- Alterado: o README inteiro fica justificado, inclusive a tabela de compatibilidade (agora em HTML, com as células justificadas), e o título "Universal Translate for RimWorld" fica centralizado.
- Adicionado: no README, linha divisória entre os itens de "Como funciona" (1 a 4), de "Instalação" (1 a 6) e do "Aviso do Windows" (os dois itens), para ler item a item.
- Não validado ainda: como o GitHub mostra o README justificado, com a tabela em HTML e as linhas divisórias (conferido só em um conversor local de Markdown, que mantém as listas numeradas na sequência certa).

## v0.005 - 2026-10-13
- Alterado: na lista de pastas pesquisadas (aba "Traduzir mods"), a marca "[padrão]" fica alinhada na borda direita da linha; as marcas "[adicionada por você]" e "[não encontrada]" continuam logo depois do caminho.
- Alterado: o texto do README fica justificado (como no Word), com `align="justify"` em volta dos parágrafos e listas; título e tabela de compatibilidade ficam fora.
- Corrigido: na tela de opções do mod no jogo, o bloco de cima (botões, atalho, mensagens e opções avançadas) podia passar da altura da janela e a lista de mods era desenhada por cima dele, bagunçando tudo (visto ao abrir as opções avançadas com o programa tradutor fechado). Agora o bloco tem a sua própria rolagem (no máximo 55% da janela), em uma coluna só, e a lista usa o espaço que sobra.
- Alterado: README, descrição do mod e aviso da janela explicam que o programa tradutor só precisa ficar aberto enquanto há algo novo para traduzir; o que já foi traduzido fica salvo e o jogo mostra sem ele (antes dizia para deixar sempre aberto). A janela do executável diz "Deixe esta janela aberta enquanto joga RimWorld" e, logo abaixo, que ela só é necessária enquanto algo estiver sendo traduzido durante o jogo; se tudo já estiver traduzido, dá para jogar com o programa fechado.
- Corrigido: botões da aba Ordens / Arquitetar criados em código por alguns mods (ex.: "Search and rescue", "Rescue all", "Rearm traps", "Remove overhanging mountains") ficavam em inglês. O jogo cria esses botões ao carregar, antes do mod, e guarda o texto no próprio botão; agora o mod traduz o texto do botão (nome e descrição) e o devolve ao original ao desativar as traduções. Botões de construção continuam sendo traduzidos pela tradução do item.
- Adicionado: o jogo percebe sozinho quando o executável grava traduções novas com o jogo aberto (aba "Traduzir mods") e as aplica em poucos segundos, sem reiniciar o jogo. Antes o jogo só lia o que estava salvo ao iniciar, e um mod traduzido com o jogo aberto continuava em inglês na tela, apesar de constar como traduzido no executável.
- Adicionado: na janela de detalhes de um mod, nova aba "Palavras traduzidas (N)", com os textos traduzidos, a tradução e o número de palavras de cada um (maiores primeiro).
- Adicionado: na aba "Não traduzidos por nós", nova coluna "Tradução existente" entre "Original" e "Motivo", mostrando como o texto está hoje (a tradução que já existe, ou o próprio texto quando já está no seu idioma). Rodadas de tradução feitas antes desta versão não guardam esse texto; use "Refazer tudo" para preenchê-lo.
- Corrigido: o botão "Traduzir pendentes" aparecia cortado na abertura. Os botões da aba "Traduzir mods" agora têm largura pelo tamanho do texto (o "Parar" ficava largo demais) e a janela abre um pouco mais larga (880 px, mínimo 800 px).
- Adicionado: "tempo restante estimado" na linha de progresso ("X de N mods (P%) - tempo restante estimado: 3 min 20 s"), calculado pelo tempo já gasto; só aparece depois de alguns segundos, e a barra anda também com o avanço dentro de cada mod.
- Corrigido: durante a tradução em lote, a célula "Abrir pasta" sumia da linha do mod que estava sendo traduzido ou que acabava de terminar.
- Adicionado: testes da lista de pastas com a marca "[padrão]" à direita, dos botões sem corte e do tempo estimado (71 testes no auxiliar; o teste do mod ganhou os cenários dos botões e das traduções gravadas com o jogo aberto).
- Não validado ainda: o visual no Windows (o teste da janela em Linux confere a posição da marca e que nenhum botão fica cortado); a precisão do tempo estimado com traduções reais (é uma estimativa simples: mods muito diferentes em tamanho podem fazer o tempo variar).

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
- Não validado ainda: o atalho de teclado e a escolha dele dentro do jogo de verdade (só compila e passa pelos testes simulados); a qualidade do modelo do português do Brasil; a janela no Windows; a nova tela de opções (rolagem do bloco de cima), a tradução dos botões da aba Ordens e a aplicação automática de traduções novas no jogo de verdade (só testados com o jogo simulado e compilados contra a API real); a correção dos acentos estranhos no jogo de verdade (o método existe na API do jogo, mas não vi quem o chama; se o texto acentuado vier de outro lugar, a opção não resolve).

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
