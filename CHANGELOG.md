# Changelog

Versioning: `0.NNN` (0.001, 0.002, ...) until the maintainer declares 1.0. **Every commit/push bumps the number** and adds an entry here
(newest first). The same text goes in the commit message: `v0.NNN: short title` + list of changes.
Version lives in `VERSION`; run `python tools/set_version.py` to sync it into the helper and the mod.

## v0.024 - 2026-10-15
- Adicionado: na aba Traduzir mods, ao clicar no título de uma coluna a tabela é ordenada (A a Z ou do menor para o maior) e, ao clicar de novo, na ordem inversa; a coluna ordenada mostra uma seta no título; Textos e Palavras são ordenados como números; a ordem é mantida enquanto a tabela se atualiza e quando o idioma da janela muda.
- Alterado: o botão "Ver changelog" ficou azul, arredondado e com a mesma altura dos outros botões.
- Corrigido: o botão verde "Traduzir pendentes" agora usa a altura real dos botões vizinhos (medida depois de aparecer na tela) e preenche toda a altura da fileira, para ficar do mesmo tamanho dos demais.
- Alterado: os textos das duas opções da aba Início ficaram centralizados dentro dos quadrados (a justificação continua disponível no código).
- Adicionado: teste novo para a ordenação das colunas.

## v0.023 - 2026-10-15
- Alterado: o botão "Traduzir pendentes" (e o "Ir para Traduzir mods" da aba Início) é verde, com cantos arredondados, a mesma letra e a mesma altura dos outros botões, ficando cinza quando não há nada a fazer.
- Alterado: os textos das duas opções da aba Início ficaram justificados; ao copiar, o texto vai normal, sem espaços especiais nem quebras de linha artificiais.
- Alterado: a caixa "Traduzir também os mods desativados, em segundo plano" fica travada enquanto uma tradução estiver rodando (com um aviso para parar a tradução antes de mudar a opção).
- Alterado: na aba Log, o botão "Abrir pasta de logs" ficou ao lado de "Copiar log" e "Limpar", à esquerda.
- Adicionado: testes novos para a justificação do texto, a trava da caixa de segundo plano e a posição dos botões do Log.

## v0.022 - 2026-10-15
- Alterado: a aba "Traduzir mods" do executável passa a acompanhar o que o jogo traduz sozinho: a linha de cada mod mostra o idioma de origem, os textos e as palavras já traduzidos e o estado ("Traduzindo pelo jogo..." e depois "Traduzido pelo jogo"), e o resumo soma tudo; mods traduzidos pelo jogo em outra sessão aparecem com os números do arquivo de tradução salvo.
- Alterado: o botão "Traduzir pendentes" ficou verde (cinza quando não há nada a fazer) para se destacar; os botões "Abrir pasta de dados" e "Abrir pasta do mod" ficaram só na aba Início.
- Alterado: a aba Início foi reformulada com duas opções lado a lado: jogar com o programa aberto (ele traduz sozinho) ou traduzir tudo agora pela aba Traduzir mods (mais rápido), com um botão para ir até ela; o aviso de reiniciar o jogo ficou embaixo.
- Adicionado: tradução em segundo plano de todos os mods, mesmo os desativados no jogo: com o programa aberto, depois que o jogo fica 30 segundos sem pedir tradução, ele traduz os mods que faltam, esperando entre um lote e outro enquanto o jogo estiver pedindo (os mods do jogo vão primeiro). Há uma caixa na aba Início para desligar; o botão Parar pausa por 10 minutos.
- Alterado: "Idioma de destino da tradução" e "Escolha o idioma de destino para traduzir os mods."
- Alterado: ao procurar atualização, as notas da versão não aparecem mais embaixo do número; entrou o botão "Ver changelog", que abre o CHANGELOG.md no GitHub.
- Adicionado: testes novos para a tabela que acompanha o jogo, a tradução em segundo plano, o botão de changelog e os botões de pasta.

## v0.021 - 2026-10-14
- Alterado: os READMEs foram reorganizados: o texto em português passou a ser README.br.md, o inglês continua README.en.md e o README.md virou uma página de entrada curta e bilíngue, com os botões de idioma, a versão atual e os links de licença, créditos e changelog.
- Alterado: tools/set_version.py passou a atualizar a versão nos três READMEs.
- Removido: o arquivo CLAUDE.md saiu do repositório (ficou no .gitignore e uma cópia está guardada fora do GitHub).
- Alterado: no THIRD_PARTY_NOTICES.md, a seção "Not included / Não incluídos" ficou com o parágrafo em inglês, uma linha em branco e o parágrafo em português.

## v0.020 - 2026-10-14
- Adicionado: licença MIT do código (arquivo LICENSE), com o pedido de que quem usar ou adaptar o código (inclusive em complementos) cite o autor e o link do repositório; a licença é citada nos dois READMEs e na descrição do mod.
- Adicionado: THIRD_PARTY_NOTICES.md com os créditos e as licenças de terceiros usados (Harmony, CTranslate2, SentencePiece, NumPy, PyYAML, Python, PyInstaller e o Argos Translate, cujos modelos não fazem parte do projeto); ele é citado nos dois READMEs e na descrição do mod.

## v0.019 - 2026-10-14
- Adicionado: imagem de capa do mod dentro do pacote (About/Preview.png), que o RimWorld mostra na tela de Mods e usa como capa ao publicar na Oficina da Steam; a conferência do pacote passou a exigir esse arquivo.
- Alterado: na aba Início do executável, o botão "Abrir pasta de logs" foi trocado por "Abrir pasta de dados" (a pasta principal do mod em %LOCALAPPDATA%) e "Abrir pasta do mod" (onde o mod está instalado, achado em RimWorld\Mods, na Oficina da Steam, nas pastas adicionadas ou na pasta lembrada pelo programa; se não achar, avisa onde procurou).
- Adicionado: os mesmos dois botões na aba Traduzir mods.
- Alterado: na janela de detalhes de um mod, os textos que falharam aparecem em vermelho, no topo da aba "Não traduzidos pelo mod" (com um aviso no título da aba); a janela já abre nessa aba quando algo falhou e mostra "Por que falhou" com o erro. O erro passa a ser guardado a cada falha nova.
- Alterado: README (português e inglês): o jogo é RimWorld 1.6 e 1.7 (a 1.7 ainda está em beta).
- Corrigido: a compilação da 1.7 já roda no GitHub (o pacote da v0.018 trouxe a pasta 1.7).

## v0.018 - 2026-10-14
- Adicionado: versão do mod para o RimWorld 1.7 (ainda em beta) em um projeto próprio (AutoTranslate17.csproj, .NET 10), que gera a pasta 1.7/Assemblies. O código compila contra a API pública da 1.7 alpha, mas ainda não foi testado dentro do jogo.
- Alterado: o mod declara suporte às versões 1.6 e 1.7 (About.xml e LoadFolders.xml); o CI ganhou uma compilação da 1.7 que não bloqueia as outras e a Release inclui a pasta 1.7 quando ela compila (senão o zip sai só com a 1.6, com um aviso).
- Alterado: README (português e inglês) cita a versão em teste para a 1.7; a capa do mod diz "RimWorld 1.6 / 1.7".
- Alterado: tools/set_version.py também atualiza a versão do novo projeto.

## v0.017 - 2026-10-14
- Alterado: capa do mod: faixa diagonal "Leia a descrição / Read the description" com "Instalação e downloads no GitHub", e a palavra "offline" saiu (a frase agora diz só que traduz automaticamente).
- Corrigido: README (português e inglês) e descrição do mod no jogo diziam que funciona "sem internet"/"offline"; agora dizem que a tradução é no seu computador, de graça, e que não precisa de internet depois de baixar o modelo do idioma uma vez.

## v0.016 - 2026-10-14
- Alterado: descrição do mod no jogo (inglês e português): "EM DESENVOLVIMENTO" em uma linha própria, "Feito com a ajuda do Claude Code", aviso de erros e bugs de tradução para reportar, uma linha em branco entre os blocos, e sem o link do Harmony (a dependência já mostra o botão de assinar); a versão saiu da descrição.
- Alterado: o mod agora se chama "Auto Translate Mods" e o autor é "peraquetocosta".
- Alterado: tools/set_version.py não atualiza mais a versão dentro do About.xml, porque ela saiu da descrição.
- Alterado: capa do mod: a frase de apoio diz que a tradução é automática ("Automatically translates..." e "Traduz seus OUTROS mods para o seu idioma, automaticamente.").

## v0.015 - 2026-10-14
- Alterado: capa do mod para a Steam: título "Auto Translate Mods", autor "peraquetocosta", requisitos (Harmony, Auto Translate Mods e Helper .exe) e a mensagem "Baixe no GitHub" centralizada no quadro do programa.

## v0.014 - 2026-10-14
- Adicionado: capa do mod para a Steam (pasta assets): imagem de 1920x1080, versão pequena de 640x360 e o arquivo cover.html para editar o texto e as cores.

## v0.013 - 2026-10-14
- Corrigido: as receitas das bancadas ("Fazer repair kit", "Fazer throwing dagger Belt") ficavam com o nome do item em inglês, porque o jogo monta a receita antes da tradução. Agora, ao traduzir o nome do item, o mod refaz o nome e o texto de trabalho da receita ("Fazer X", "Fazendo X.") com as palavras do próprio jogo.
- Corrigido: receitas em inglês criadas por outros mods ("Make medicine x5", "Make any stone blocks x3") são traduzidas e ficam com o "Fazer" do jogo na frente.
- Corrigido: arquivos de "tradução" que são cópia do inglês (por exemplo, da mobília da Misstall, com nomes como "MF Large Generator") agora são avaliados como um todo: se o conjunto dos textos é claramente inglês, todas as entradas, inclusive os nomes curtos, contam como cópia do original e são traduzidas.
- Corrigido: nunca traduzir uma tradução. Se o jogo roda em outro idioma e já aplicou a tradução de um mod, o mod recupera o inglês original guardado pelo jogo e traduz a partir dele para o idioma escolhido.
- Corrigido: ao baixar um modelo de idioma que vem com outro formato de arquivos (por exemplo, source.spm e target.spm), o programa agora o aceita; uma pasta de modelo incompleta é apagada para ser baixada de novo, e a mensagem de erro lista o que há na pasta.
- Alterado: os textos "Idioma da janela", "Idioma de destino", o filtro do Log e o aviso do topo da janela do executável podem ser selecionados e copiados.
- Alterado: a descrição do mod no jogo ficou bem mais curta, em inglês e depois em português, com o aviso de que o Harmony e o programa tradutor são obrigatórios e os links da oficina do Harmony e do GitHub.
- Adicionado: testes novos para as receitas "Fazer X", para arquivos de tradução que são cópia, para a regra de nunca traduzir uma tradução e para os formatos de pasta dos modelos.

## v0.012 - 2026-10-14
- Adicionado: botões no topo dos dois READMEs (idioma Português / English, Harmony na Steam e Argos Translate no GitHub).
- Adicionado: botão "Página no GitHub" na aba Início do executável.
- Adicionado: os textos da janela do executável podem ser selecionados e copiados (mouse, Ctrl+C, Ctrl+A e botão direito); nas tabelas, Ctrl+C copia as linhas selecionadas. Serve para colar um texto em um tradutor e conferir.
- Alterado: a janela do executável se adapta ao idioma: as caixas de seleção, os botões e os cabeçalhos das colunas crescem com o texto e a janela se alarga sozinha, para nada ficar cortado.
- Alterado: a caixa de idioma da janela mostra só o nome nativo de cada idioma; as linhas "Em execução..." e "Modelos instalados..." saíram da aba Início; o aviso ao preparar um idioma ficou curto e mostra o motivo se falhar.
- Corrigido: nomes curtos que o modelo devolvia sem traduzir ou traduzia errado. "mine" agora é "mina" (e não "meu."), e frases devolvidas iguais ao original (por exemplo, em Title Case ou nomes com possessivo) ganham uma segunda tentativa, em minúsculas e, nos nomes curtos, como "a ...".
- Corrigido: traduções antigas já salvas ("Seguro." para "safe", "Meu." para "mine" e ponto final em nomes curtos) são consertadas sozinhas pelo executável ao abrir ou ao escolher o idioma, sem precisar excluir as traduções.
- Alterado: os 30 idiomas do RimWorld foram conferidos na lista de modelos do Argos Translate (todos têm modelo); um teste garante isso. README em português e inglês com texto novo no estado atual, links do Harmony e do Argos Translate e sem os itens de atualização sem janela e de token do GitHub.

## v0.011 - 2026-10-14
- Corrigido: nomes curtos como "safe" (cofre) saíam como "Seguro." na tradução. Agora o tradutor não coloca ponto final em nome curto que no original não tem, e um pequeno glossário traduz "safe" como "cofre" (e equivalentes nos outros idiomas). Traduções antigas já salvas só mudam depois de "Excluir traduções" e de traduzir de novo.
- Corrigido: mods em modo "do próprio mod" ou "de outro mod de tradução" ficavam inteiros em inglês quando não havia essa tradução (ex.: Vanilla Furniture Expanded - Security). Agora esses modos são "preferir": o que o mod escolhido não traz é traduzido automaticamente.
- Alterado: os modos por mod se chamam "Preferir a tradução do próprio mod" e "Preferir a tradução de outro mod".
- Alterado: a tela de opções do mod ficou mais compacta para a lista de mods ganhar espaço: o atalho (texto, "Definir atalho" e "Remover atalho") ocupa uma linha só, e o idioma, o estado e o erro do programa tradutor viram um parágrafo só, com o erro encurtado.
- Alterado: o idioma de destino, o seletor de idioma da janela do executável e o mod passam a oferecer somente os 30 idiomas do RimWorld (Catalão, Chinês Simplificado e Tradicional, Tcheco, Dinamarquês, Holandês, Inglês, Estoniano, Finlandês, Francês, Alemão, Grego, Húngaro, Italiano, Japonês, Coreano, Coreano Fast Channel, Norueguês Bokmål, Polonês, Português Portugal e Brasil, Romeno, Russo, Eslovaco, Espanhol Castelhano e América Latina, Sueco, Turco, Ucraniano e Vietnamita). Os outros idiomas saíram da lista.
- Adicionado: a janela do executável pode ficar em qualquer um dos 30 idiomas. Português e inglês são escritos à mão; os outros são traduzidos do inglês, na primeira vez, com os modelos do próprio programa (baixando o modelo se precisar), salvos numa pasta "ui" e usados nas próximas vezes. Enquanto isso a janela fica em inglês, com um aviso.
- Adicionado: o mod e o programa reconhecem Chinês Tradicional (zh-Hant), Espanhol da América Latina (es-419) e Coreano Fast Channel (ko-FC), usando os modelos de chinês tradicional, espanhol e coreano.
- Adicionado: aviso no diagnóstico de cada mod e testes novos (glossário, ponto final, idiomas da janela, modos "preferir").
- Adicionado: README em inglês (README.en.md), com links de troca de idioma no topo dos dois; a versão é atualizada nos dois por tools/set_version.py.
- Alterado: README: link da oficina da Steam do Harmony e do GitHub do Argos Translate; tabela de idiomas com os 30 do RimWorld; texto do estado atual diz que a tradução automática não é 100% perfeita e pede para reportar erros; removidos itens sobre atualizar sem janela e token do GitHub e a frase sobre janela preta.

## v0.010 - 2026-10-14
- Corrigido: nomes e descrições de itens que ficavam em inglês no jogo mesmo com a tradução pronta no cache (ex.: Electric stonecutter's table, Drug cabinet, Military turret). Causa: textos gerados pelo próprio jogo (plantas de construção/molduras, já no idioma do jogo) faziam o mod achar que o mod traduzido já estava em português e descartar os textos curtos; agora esses textos gerados são ignorados na detecção de idioma do mod.
- Corrigido: ao recarregar o jogo, o texto original em inglês é mantido como fonte da tradução.
- Corrigido: receitas geradas pelo jogo não são mais tratadas como texto de mod quando o jogo já está no idioma de destino.
- Alterado: o marcador de "aplicando traduções" interrompido só desativa um mod de forma permanente na segunda vez seguida; na primeira vale só na sessão.
- Alterado: na janela de detalhes do mod, as abas agora se chamam "Textos traduzidos", "Palavras traduzidas" e "Não traduzidos pelo mod".
- Alterado: na tela de opções do jogo, a seção de mods ficou em um cartão separado, com busca e botão "Aplicar a todos (N)..." mais bonitos e botões alinhados; o Diagnóstico fica na mesma linha do botão de modo.
- Adicionado: botão "Diagnóstico de todos", que copia o diagnóstico de todos os mods e salva um arquivo .txt na pasta de dados do mod (diagnostics), mantendo os últimos 10.
- Adicionado: diagnóstico de cada mod mostra se o texto em espera já está no arquivo de tradução e não foi aplicado.
- Adicionado: testes de integração para designadores, aplicação ao vivo do cache, diagnóstico e detecção de idioma com itens gerados.

## v0.009 - 2026-10-13
- Alterado: no README, a divisória entre os itens das listas ficou bem curta (12 traços): a versão longa quebrava em quase três linhas no celular.
- Alterado: no README, os títulos das seções (Compatibilidade, Como funciona, Instalação, Aviso do Windows, Atualizar, Traduzir todos os mods, Opções do mod, O que ele traduz, textos com acentos, Segurança da conexão, Privacidade, Estado atual, Deu problema...) ficam alinhados à esquerda, sem justificar; o texto e as listas continuam justificados e o título principal continua centralizado.
- Alterado: a janela do executável, o README e a descrição do mod avisam também que, se você traduzir ou atualizar os mods com o jogo aberto e não vir a tradução aplicada, é preciso reiniciar o jogo.
- Alterado: a janela do executável, o README e a descrição do mod avisam que textos que só existem dentro do jogo (como os botões de ações da aba Ordens que alguns mods criam em código) não dá para traduzir antes: é preciso abrir o programa ANTES de iniciar o RimWorld e jogar com ele aberto, para ele traduzir e salvar no cache; nas próximas vezes já fica pronto.
- Adicionado: tradução em tempo real, mod por mod, e leve para o jogo. Enquanto a aba "Traduzir mods" do executável traduz com o jogo aberto, o jogo aplica na hora, mod por mod, só o que mudou no arquivo de tradução de cada mod (nomes e descrições de itens, textos de interface, descrições de mods, botões), sem reiniciar o jogo, sem recarregar tudo e sem mexer nos outros mods. Sem pesar o jogo: o executável mantém um arquivo-sinal (`bulk-running.flag`, atualizado a cada 2 segundos) enquanto traduz; fora disso o jogo só olha esse arquivo a cada 5 segundos (uma consulta mínima); só confere os arquivos de tradução (a cada 1,5 segundo) enquanto o sinal está fresco e faz uma conferência final quando ele some; um sinal parado há mais de 10 segundos (programa fechado à força) é ignorado. Com as traduções desligadas, o texto novo espera e entra quando elas voltam.
- Adicionado: nas opções do mod, caixa "Pesquisar mod" que filtra a lista pelo nome ou identificador (com contador, por exemplo 3/64).
- Adicionado: nas opções do mod, botão "Aplicar a todos os exibidos (N)..." com menu para escolher de uma vez a tradução de todos os mods da lista: automática, a do próprio mod, a de outro mod de tradução ou sempre a automática; e a opção de religar os mods exibidos que foram desligados por problemas. Vale só para os mods exibidos (a pesquisa escolhe um grupo), não mexe nos mods desligados pelo jogador, e aplica ao fechar a janela, com uma recarga só.
- Adicionado: botão "Diagnóstico" em cada mod da lista: copia para a área de transferência (e grava no log) um relatório com o estado do mod (ativo, modo, se foi desligado por problemas e por quê), quantos textos estão traduzidos e aplicados e quantos esperam, se o arquivo de tradução tem o texto de cada um que espera ("tem o texto mas não foi aplicado") e um texto quase igual no arquivo, se houver, os primeiros textos que o mod deixou em paz porque um arquivo de tradução de algum mod já os tem (um arquivo que só repete o original deixaria o texto em inglês na tela) e os problemas registrados. Serve para achar por que um mod não mostra a tradução.
- Corrigido: um mod inteiro podia ficar SEM TRADUÇÃO PARA SEMPRE, de uma versão para outra, só porque o jogo foi fechado (ou encerrado à força) enquanto as traduções dele estavam sendo aplicadas: a sessão seguinte o desligava e gravava isso. Agora, na primeira vez ele só fica desligado naquela sessão e nada é gravado; só se acontecer duas vezes seguidas, sem nenhuma saída normal do jogo entre elas, é que fica gravado. Uma saída normal zera a contagem. É uma causa suspeita do que foi visto nos mods do Vanilla Expanded; não foi confirmada.
- Corrigido: um texto longo que já está no idioma de destino (por exemplo a descrição de um mod que já aparecia em português) nunca é traduzido de novo, no jogo e no executável: o idioma dele é julgado sozinho, em vez de seguir o idioma geral do mod. Nos arquivos de tradução dos módulos do Vanilla Furniture Expanded havia descrições já em português usadas como texto de origem e traduzidas de novo, saindo piores.
- Corrigido: receitas que o próprio jogo gera já no idioma de destino (por exemplo "Fazer ISR2G", "Fazendo ISR2G.") eram traduzidas de novo como se fossem inglês e saíam errados ("Fazenda ISR2G.", "FAZER ISR2G"). Agora ficam como estão quando o jogo já roda no idioma de destino. Os nomes de projeto e construção ("caixa de plantador (projeto)") continuam sendo traduzidos.
- Investigado: nos arquivos de tradução do Roads of the Rim e de cinco módulos do Vanilla Furniture Expanded (Farming, Medical, Power, Production, Security) os textos estão traduzidos e as chaves batem exatamente com o texto que aparece no jogo (inclusive "large tailoring table" e a descrição com "33% of normal speed"); a falta de tradução na tela vem da aplicação no jogo. Nenhuma causa única foi confirmada: as candidatas são o jogo aberto antes de a tradução existir com uma versão do mod sem aplicação ao vivo, e o mod ter sido desligado (veja o item do mod desligado acima); o botão "Diagnóstico" mostra qual é o caso em cada mod.
- Alterado: README: as opções do mod (pesquisa, aplicar a todos, religar, diagnóstico) e a aba Log.
- Adicionado: terceira aba "Log" no executável, com tudo o que o programa faz: cada pedido de tradução do jogo (com o nome do mod; ao clicar, cada texto original e a sua tradução, inclusive botões como "Search and rescue"), a tradução em lote (início, cada mod com os totais e as traduções novas, interrupção, fim), downloads de modelos, procura e instalação de atualização, e avisos e erros do programa com os detalhes técnicos. Tem filtro (tudo, jogo, lote, modelos, atualização, sistema, só avisos e erros), "Copiar log", "Limpar" e "Abrir pasta de logs"; cada linha muda de idioma junto com a janela. Guarda as últimas 3000 linhas e some ao fechar o programa (o histórico técnico continua no `helper.log`).
- Alterado: o mod do jogo passa a enviar o nome do mod em cada pedido de tradução, só para o log do executável (o protocolo continua compatível: versões antigas sem o nome aparecem como "?").
- Adicionado: testes da tradução em tempo real (sem sinal o jogo não confere nada; com sinal aplica só o mod que mudou; conferência final; sinal velho ignorado; traduções desligadas; o sinal do executável existe só durante a tradução em lote) e testes do log (registro de atividades, pedido do jogo no log, a aba na janela com filtro, idioma, detalhes, copiar e limpar): 83 testes no auxiliar.
- Não validado ainda: a aba Log no Windows de verdade e com o jogo real (o pedido do jogo foi testado com o programa e com um jogo simulado); como o GitHub mostra o README (conferido só em um conversor local de Markdown: 14 títulos, 10 listas, 32 divisórias).

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
