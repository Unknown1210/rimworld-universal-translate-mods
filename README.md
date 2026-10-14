<h1 align="center">Universal Translate for RimWorld</h1>

<p align="center">
<a href="README.md"><img src="https://img.shields.io/badge/IDIOMA-PORTUGU%C3%8AS-2ea44f?style=for-the-badge" alt="Português"></a>
<a href="README.en.md"><img src="https://img.shields.io/badge/IDIOMA-ENGLISH-555555?style=for-the-badge" alt="English"></a>
<br>
<a href="https://steamcommunity.com/workshop/filedetails/?id=2009463077"><img src="https://img.shields.io/badge/REQUER-HARMONY-1b2838?style=for-the-badge&logo=steam&logoColor=white" alt="Harmony (Steam Workshop)"></a>
<a href="https://github.com/argosopentech/argos-translate"><img src="https://img.shields.io/badge/TRADU%C3%87%C3%83O-ARGOS_TRANSLATE-0366d6?style=for-the-badge&logo=github&logoColor=white" alt="Argos Translate (GitHub)"></a>
</p>

<div align="justify">

**Versão atual: 0.020** · [Baixar na aba Releases](../../releases/latest)

Traduz **automaticamente** os outros mods do seu jogo para o seu idioma, **sem precisar de um mod de tradução para cada mod**.
A tradução é feita **no seu computador e de graça**. Depois de baixar uma vez o modelo do seu idioma, **não precisa de internet**. Cada tradução fica salva, então ela só é feita uma vez.

> **Em desenvolvimento.** Este projeto foi feito com a ajuda do **Claude** (IA da Anthropic) e ainda está em fase inicial (versão atual 0.020). Veja "Estado atual" abaixo.

<h2 align="left">Compatibilidade</h2>

<table>
<tr><td width="22%"><b>Jogo</b></td><td align="justify">RimWorld <b>1.6</b> e <b>1.7</b> (a 1.7 ainda está em beta)</td></tr>
<tr><td width="22%"><b>Sistema</b></td><td align="justify"><b>Windows</b> 10/11</td></tr>
<tr><td width="22%"><b>Idioma original dos mods</b></td><td align="justify"><b>Qualquer um</b>: o mod detecta sozinho (inglês, chinês, russo, português, ...)</td></tr>
<tr><td width="22%"><b>Idioma de destino</b></td><td align="justify"><b>Somente os 30 idiomas que o próprio RimWorld oferece</b>: Alemão, Catalão, Chinês (Simplificado), Chinês (Tradicional), Coreano, Coreano (Fast Channel), Dinamarquês, Eslovaco, Espanhol (Castelhano), Espanhol (América Latina), Estoniano, Finlandês, Francês, Grego, Holandês, Húngaro, Inglês, Italiano, Japonês, Norueguês (Bokmål), Polonês, Português (Brasil), Português (Portugal), Romeno, Russo, Sueco, Tcheco, Turco, Ucraniano e Vietnamita. Qualquer outro idioma não aparece. Cada um tem o seu modelo de tradução, conferido na lista de modelos do Argos Translate (as variantes de espanhol e de coreano usam o mesmo modelo), baixado sob demanda.</td></tr>
</table>


<h2 align="left">Como funciona</h2>

1. O mod olha os textos dos seus outros mods (nomes, descrições e textos de interface) e **detecta o idioma de cada um** (por exemplo, um mod em chinês ou em português).<br><sub>────────────</sub>
2. Se o mod **já tem tradução** (dele mesmo ou de outro mod de tradução), ele **não traduz**. A tradução existente é a que vale.<br><sub>────────────</sub>
3. O que **não tem tradução** é traduzido, do idioma detectado para o seu, por um programa que roda no seu PC (o **executável**). Se o texto já está no seu idioma, não é mexido. Pares sem modelo direto (ex.: chinês → português) passam pelo inglês, o que é um pouco mais lento e pode piorar a qualidade.<br><sub>────────────</sub>
4. Se um mod der problema, **só aquele mod** é desligado. Os outros continuam normais.

<h2 align="left">Por que preciso do executável?</h2>

Um mod do RimWorld é apenas um conjunto de arquivos que roda **dentro** do jogo e não tem como carregar um motor de tradução (os modelos de IA são grandes e pesados). Por isso a tradução é feita por um programa separado, o **UniversalTranslate-Helper.exe**, que roda no seu computador, usa a sua CPU, funciona **sem internet** (só baixa o modelo do seu idioma uma vez) e conversa com o mod **só dentro do seu próprio computador** (não passa pela internet nem pela rede da sua casa) e só atende pedidos que tragam uma senha. **Ele só precisa estar aberto enquanto há algo novo para traduzir.** O que já foi traduzido fica salvo e o jogo mostra sem o programa; o que ainda não foi traduzido aparece no idioma original até você abrir o programa.

<h2 align="left">Instalação (passo a passo)</h2>

Baixe os dois arquivos na aba **Releases** (lado direito desta página, versão mais nova):
`UniversalTranslate-Helper.exe` (o programa que traduz) e `UniversalTranslate-Mod.zip` (o mod já pronto).

1. Instale o mod **Harmony** pela [Steam Workshop](https://steamcommunity.com/workshop/filedetails/?id=2009463077).<br><sub>────────────</sub>
2. Extraia a pasta `AutoTranslate` do `UniversalTranslate-Mod.zip` para dentro de `RimWorld\Mods`.<br><sub>────────────</sub>
3. Dê **dois cliques** em `UniversalTranslate-Helper.exe`. Vai abrir **uma janela**.<br><sub>────────────</sub>
4. Na primeira vez: escolha o **idioma de destino** pelo nome (ele é escolhido **aqui, no executável**, e o jogo usa o mesmo) e espere o modelo baixar. **Deixe a janela aberta enquanto joga RimWorld.** Ela só é necessária enquanto algo estiver sendo traduzido durante o jogo: **se tudo já estiver traduzido, você não precisa mais dela e pode jogar com o programa fechado**. Atenção: textos que só existem dentro do jogo (como os botões de ações da aba Ordens que alguns mods criam em código) **não dá para traduzir antes**; para eles, abra o programa **antes** de iniciar o RimWorld e jogue com ele aberto, para que ele traduza e salve no cache. Nas próximas vezes já fica pronto. **Se você traduzir ou atualizar os mods com o jogo aberto e não vir a tradução aplicada, reinicie o jogo** para que ela seja aplicada. Abra de novo quando instalar mods novos ou atualizar algum.<br><sub>────────────</sub>
5. Abra o RimWorld, ative [**Harmony**](https://steamcommunity.com/workshop/filedetails/?id=2009463077) e depois **Auto Translate** (nessa ordem) e inicie o jogo.<br><sub>────────────</sub>
6. Na primeira vez a tradução leva alguns minutos; nas próximas é instantânea. Se quiser adiantar, use a aba **Traduzir mods** do executável (veja abaixo). Os ajustes do mod ficam em **Opções → Mods → Auto Translate**.

<h3 align="left">Aviso do Windows ao abrir o <code>.exe</code></h3>

O executável **ainda não tem assinatura digital** (certificado de publicador), e o Windows desconfia de programas de "fornecedor desconhecido". **Isso não é detecção de vírus.** Todo o código está neste repositório e o `.exe` é gerado automaticamente pelo GitHub (pasta `.github/workflows`), então dá para conferir como ele é feito.
- **"O Windows protegeu seu computador" (SmartScreen):** clique em **Mais informações → Executar assim mesmo**.<br><sub>────────────</sub>
- **"O controle inteligente de aplicativos bloqueou um aplicativo" (Smart App Control, Windows 11):** esse bloqueio **não tem botão "executar assim mesmo"**. Hoje as saídas são: desligar o Controle Inteligente de Aplicativos (Segurança do Windows → Controle de aplicativos e navegador → Configurações do Controle Inteligente de Aplicativos), ou esperar a versão assinada. **Segundo a documentação da Microsoft, depois de desligado ele não volta a ser ligado sem redefinir o Windows**, então só faça isso se entender e aceitar esse custo. Assinar o executável é a solução definitiva e **ainda não foi feita**.

**Steam Workshop:** o mod será publicado lá (planejado). O executável continuará sendo baixado aqui, na aba Releases.

<h2 align="left">Atualizar</h2>

Abra o `UniversalTranslate-Helper.exe` e clique em **Procurar atualização**. Se houver versão nova, clique em **Atualizar agora**: ele baixa do GitHub, confere o arquivo, atualiza o executável **e o mod** (se achar a pasta do RimWorld; **feche o jogo antes**) e reinicia sozinho. Ele também procura atualização quando abre.
- Só são aceitos arquivos do GitHub, e o arquivo baixado precisa bater com o hash (SHA-256) publicado na Release. Isso protege contra download corrompido, mas você continua confiando no repositório.

<h2 align="left">Traduzir todos os mods de uma vez (aba "Traduzir mods", sem abrir o jogo)</h2>

Na aba **Traduzir mods** do executável:
- Ele procura os mods instalados, **mesmo os que não estão ativados no jogo**. Logo acima dos botões aparece a **lista numerada das pastas pesquisadas**: as pastas padrão (`Mods` do RimWorld e Oficina da Steam, marcadas como "padrão") e as que você adicionou com **Adicionar pasta** (marcadas como "adicionada por você"; ficam salvas e são pesquisadas sempre que você abre o programa, junto com as outras). Dá para ter várias pastas ao mesmo tempo.<br><sub>────────────</sub>
- **Traduzir pendentes:** traduz o que ainda não foi traduzido, com **barra de progresso**, "X de N mods (%)" e o **tempo restante estimado** e uma **tabela por mod** (idioma de origem, textos, palavras e estado). No fim mostra o **resumo** com a quantidade de textos e de palavras traduzidas.<br><sub>────────────</sub>
- **Procurar mods:** se você instalou mods novos (ou atualizou algum) depois, ele reconhece quais estão **novos** ou **alterados** e traduz só esses. **Refazer tudo** confere todos de novo (o que já está salvo não é traduzido outra vez).<br><sub>────────────</sub>
- **Parar:** interrompe; o que já foi traduzido fica salvo.<br><sub>────────────</sub>
- **Excluir traduções:** apaga todas as traduções salvas do idioma escolhido (pergunta antes de apagar). Os mods voltam a aparecer como novos. Suas correções manuais (`overrides`) são mantidas.<br><sub>────────────</sub>
- **Coluna "Pasta":** clique em "Abrir pasta" na linha de um mod para abrir a pasta dele no explorador de arquivos.<br><sub>────────────</sub>
- **Dois cliques em um mod** (fora da coluna "Pasta") abrem uma janela com três abas: **Textos traduzidos** (original e tradução; o texto completo aparece ao selecionar), **Palavras traduzidas** (os mesmos textos com o número de palavras de cada um) e **Não traduzidos pelo mod** (original, **tradução existente** e o motivo: "já tem tradução", "já está no seu idioma", "sem suporte", "falhou"). Se você trocar o idioma da janela com essa tela aberta, ela muda de idioma na hora.<br><sub>────────────</sub>
- As traduções ficam no mesmo cache que o jogo usa, então ao jogar elas já estão prontas. **Se o jogo já estiver aberto**, ele aplica as traduções **em tempo real, mod por mod**: assim que o programa termina de traduzir um mod, o jogo aplica só o que mudou naquele mod, sem reiniciar e sem recarregar os outros. **Sem pesar o jogo:** enquanto o programa não está traduzindo, o jogo só olha um arquivo-sinal minúsculo a cada 5 segundos (custo quase zero); só enquanto o sinal existe ele confere os arquivos, a cada segundo e meio; quando o programa termina, o jogo faz uma conferência final e volta a ficar quieto. Por exemplo, ao traduzir um mod de paletes, o nome e a descrição dos paletes mudam na tela em instantes. É um adiantamento: ele lê os arquivos XML dos mods; textos que só existem durante o jogo (ou que dependem de outros mods) são traduzidos pelo mod na hora, como sempre. **Para esses, abra o programa antes de iniciar o RimWorld e jogue com ele aberto**: o jogo pede a tradução, o programa traduz e salva no cache, e nas próximas vezes já fica pronto. Se a tradução não aparecer no jogo, reinicie o jogo.

<h2 align="left">Aba Log (o que o programa está fazendo)</h2>

- **Tudo o que o jogo pede:** cada pedido de tradução do jogo aparece com o nome do mod e a quantidade de textos. Ao clicar na linha, os detalhes mostram **cada texto original com a sua tradução** (por exemplo, o botão "Search and rescue" e a tradução que ele recebeu).<br><sub>────────────</sub>
- **Tradução em lote:** o começo, cada mod (quantos textos, quantos traduzidos agora, do cache, já com tradução, já no seu idioma, falhas, palavras e se não há suporte) e as traduções novas gravadas.<br><sub>────────────</sub>
- **Modelos, atualizações, avisos e erros:** downloads de modelos, procura e instalação de atualização, e os avisos e erros do programa, com os detalhes técnicos.<br><sub>────────────</sub>
- **Filtro, "Copiar log", "Limpar" e "Abrir pasta de logs".** O texto de cada linha muda de idioma junto com a janela.<br><sub>────────────</sub>
- **Limites:** a lista da aba guarda as últimas 3000 linhas e some quando o programa fecha (o histórico técnico fica no arquivo `helper.log`, na pasta de logs). O jogo só aparece aqui enquanto o programa está aberto.

<h2 align="left">Opções do mod</h2>

Em **Opções → Mods → Auto Translate** (a tela segue o idioma do seu jogo):
- **Desativar traduções:** um botão que mostra os textos originais **na hora, sem reiniciar**, para você comparar. Clique de novo para voltar às traduções.<br><sub>────────────</sub>
- **Atalho de teclado:** clique em "Definir atalho" e aperte a tecla que quiser, sozinha ou com Shift, Ctrl ou Alt (por exemplo, Shift + Tab). Em qualquer momento do jogo, esse atalho liga e desliga as traduções **em tempo real**, com um aviso na tela. Escolha uma combinação que o jogo ainda não use. Não dispara enquanto você escreve em uma caixa de texto.<br><sub>────────────</sub>
- **Idioma de destino:** é escolhido **no executável**; aqui só aparece qual está em uso. Se você trocar no executável com o jogo aberto, o mod percebe e recarrega sozinho.<br><sub>────────────</sub>
- **Lista de mods:** para cada mod você vê o que está acontecendo e se há **suporte** para o idioma escolhido ("com suporte", "SEM SUPORTE" ou "desconhecido" se o programa tradutor estiver fechado). Cada mod tem um interruptor **Ativado** e a escolha de qual tradução usar: automática (recomendada), preferir a do próprio mod, preferir a de outro mod de tradução, ou sempre a automática. Nas opções "preferir", o que o mod escolhido não traz é traduzido automaticamente: nenhum texto fica em inglês por causa do modo.<br><sub>────────────</sub>
- **Pesquisar mod:** uma caixa acima da lista filtra os mods pelo nome ou pelo identificador (o contador mostra, por exemplo, 3/64).<br><sub>────────────</sub>
- **Aplicar a todos os exibidos:** um botão com menu para escolher de uma vez a tradução de todos os mods que aparecem na lista (use a pesquisa para escolher só um grupo): automática (recomendada), preferir a do próprio mod, preferir a de outro mod de tradução ou sempre a automática. Mods que você desligou, ou que foram desligados por problemas, não são mexidos. Vale quando você fecha a janela de opções.<br><sub>────────────</sub>
- **Diagnóstico:** um botão em cada mod que copia um relatório curto (o estado do mod, quantos textos estão traduzidos e aplicados, quais estão esperando, se o arquivo de tradução tem aquele texto e se há um texto quase igual). Cole numa mensagem para descobrir por que um mod não está mostrando a tradução. Há também um botão que reúne o diagnóstico de todos os mods e salva num arquivo de texto.<br><sub>────────────</sub>
- **Avançado** (recolhido): o que traduzir (itens, interface, descrições), esconder os textos com acentos estranhos do modo desenvolvedor (veja abaixo), log detalhado, pasta de logs, relatório de problema e limpar o cache.

<h2 align="left">O que ele traduz (e o que não)</h2>

- **Traduz:** nomes, descrições e textos de interface dos mods (inclusive os botões da aba Ordens que alguns mods criam em código), e a **descrição de cada mod na tela de Mods** (dos mods ativos).<br><sub>────────────</sub>
- **Não traduz:** textos escritos diretamente no código de alguns mods, textos que já estão no seu idioma, e o conteúdo oficial do jogo.<br><sub>────────────</sub>
- **Arquivos de "tradução" que só repetem o texto original** (comum: a própria ferramenta do RimWorld cria arquivos assim) **não contam como tradução**: esses textos são traduzidos. Uma tradução de verdade, feita pelo autor do mod ou por outro mod, é respeitada.<br><sub>────────────</sub>
- **Detecção de idioma:** funciona bem com textos longos e com idiomas de alfabeto próprio (chinês, japonês, coreano, russo...). Em mods com poucos textos curtos em alfabeto latino ela assume inglês e pode errar (se acontecer, mande um relatório de problema).<br><sub>────────────</sub>
- É tradução **automática**: pode ter erros. Você pode corrigir qualquer texto no arquivo `overrides` (veja abaixo) e a sua correção sempre vence.

<h2 align="left">Textos com acentos estranhos no modo desenvolvedor</h2>

Com o **modo desenvolvedor** do RimWorld ligado, o próprio jogo marca os textos que não têm tradução no idioma do jogo colocando acentos nas letras ("Séàrçh ànd rèsçùè"). É um recurso para tradutores, mas atrapalha quem só quer jogar. O mod esconde isso e mostra o texto original (ou a tradução automática, quando existe). Dá para desligar em Opções → Mods → Auto Translate → Avançado. Se algum mod guardar o texto no início do jogo, reinicie o jogo depois de mudar a opção ou o modo desenvolvedor.

<h2 align="left">Segurança da conexão entre o jogo e o programa</h2>

- O programa só "escuta" dentro do próprio computador (o endereço técnico `127.0.0.1` significa "este computador"; ele **não é o seu IP** e não é acessível pela internet nem por outros aparelhos da sua rede).<br><sub>────────────</sub>
- Cada pedido precisa de uma **senha aleatória** guardada na sua pasta de dados; pedidos de páginas da internet abertas no navegador são recusados.<br><sub>────────────</sub>
- O programa só sabe traduzir texto e baixar modelos de tradução: **não lê, apaga nem executa arquivos** a pedido de ninguém.<br><sub>────────────</sub>
- Limite honesto: um programa malicioso que já esteja rodando na sua conta do Windows poderia ler a senha, mas esse programa já teria acesso a tudo, com ou sem este mod. Este código não passou por auditoria independente.

<h2 align="left">Privacidade e arquivos</h2>

- **Nada é enviado pela internet.** A única coisa baixada é o modelo de tradução, uma vez (e as atualizações, se você clicar).<br><sub>────────────</sub>
- **De onde vem o modelo:** do projeto aberto [**Argos Translate**](https://github.com/argosopentech/argos-translate). A lista de modelos fica no GitHub dele e os arquivos são baixados de `argos-net.com`. É um download anônimo: **sem conta, sem login, sem chave e sem assinatura de nenhum serviço** (o programa não usa nenhuma IA online; quem traduz é o modelo, rodando no seu computador). Limite honesto: a lista do Argos não traz uma impressão digital (hash) dos modelos, então eles não são conferidos depois de baixados, só protegidos pela conexão segura (https).<br><sub>────────────</sub>
- Tudo fica em `%LOCALAPPDATA%\RimWorldAutoTranslate`: modelos, traduções salvas (`cache`), suas correções (`overrides`) e logs (`logs`).<br><sub>────────────</sub>
- **Licença:** o código é livre, sob a [licença MIT](LICENSE): você pode usar, copiar, modificar e redistribuir, inclusive em outros projetos, mantendo o aviso de direitos autorais; o programa é fornecido "como está", sem garantia. **Se você usar ou adaptar este código (inclusive em complementos), cite o autor, peraquetocosta, e o link deste repositório.**<br><sub>────────────</sub>
- **Créditos e licenças de terceiros** (Harmony, CTranslate2, SentencePiece, Argos Translate e outros): veja [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

<h2 align="left">Estado atual (transparência)</h2>

Esta é uma **versão inicial** (versão atual 0.020), feita com a ajuda do Claude. O mod compila contra a API do RimWorld 1.6 e o código passou nos testes automáticos (inclusive o teste da janela do executável no Windows do GitHub), mas **ainda não foi testado a fundo dentro do RimWorld** nem com muitos mods reais. Podem aparecer erros, principalmente com mods que mexem nos mesmos textos. **A tradução automática não é 100% perfeita**, mas é bem melhor do que jogar com um mod que não está no seu idioma. **Se você encontrar qualquer erro, por favor reporte** (veja "Deu problema ou conflito com um mod?" abaixo): isso ajuda a melhorar o projeto para todo mundo.

<h2 align="left">Deu problema ou conflito com um mod?</h2>

1. No jogo: **Opções → Mods → Auto Translate → Avançado → Criar relatório de problema** (ou o botão **Relatório de problema** do executável).<br><sub>────────────</sub>
2. Vai abrir uma página do GitHub e a pasta do relatório. **Arraste o arquivo** para a página e envie.

O relatório mostra qual mod causou o problema e o que aconteceu. Seu nome de usuário e suas pastas pessoais são removidos. Nada é enviado sem você anexar.

---
Histórico de mudanças: [CHANGELOG.md](CHANGELOG.md)

</div>
