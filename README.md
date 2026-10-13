<h1 align="center">Universal Translate for RimWorld</h1>

<div align="justify">

**Versão atual: 0.007** · [Baixar na aba Releases](../../releases/latest)

Traduz **automaticamente** os outros mods do seu jogo para o seu idioma, **sem precisar de um mod de tradução para cada mod**.
A tradução é feita **no seu computador, sem internet e de graça**. Cada tradução fica salva, então ela só é feita uma vez.

> **Em desenvolvimento.** Este projeto foi feito com a ajuda do **Claude** (IA da Anthropic) e ainda está em fase inicial (versão atual 0.007). Veja "Estado atual" abaixo.

## Compatibilidade

<table>
<tr><td width="22%"><b>Jogo</b></td><td align="justify">RimWorld <b>1.6</b></td></tr>
<tr><td width="22%"><b>Sistema</b></td><td align="justify"><b>Windows</b> 10/11</td></tr>
<tr><td width="22%"><b>Idioma original dos mods</b></td><td align="justify"><b>Qualquer um</b>: o mod detecta sozinho (inglês, chinês, russo, português, ...)</td></tr>
<tr><td width="22%"><b>Idioma de destino</b></td><td align="justify"><b>Todos os idiomas que têm modelo de tradução</b> (49): Português (Brasil), Português (Portugal), Inglês, Espanhol, Francês, Alemão, Italiano, Russo, Polonês, Turco, Ucraniano, Chinês, Japonês, Coreano, Holandês, Tcheco, Árabe, Azerbaijano, Búlgaro, Bengali, Catalão, Dinamarquês, Grego, Esperanto, Estoniano, Basco, Persa, Finlandês, Irlandês, Galego, Hebraico, Hindi, Húngaro, Indonésio, Quirguiz, Lituano, Letão, Malaio, Norueguês, Romeno, Eslovaco, Esloveno, Albanês, Sueco, Suaíli, Tailandês, Tagalo, Urdu, Vietnamita. O Português tem duas opções, <b>Português (Brasil)</b> e <b>Português (Portugal)</b>, cada uma com o seu próprio modelo. Os modelos são baixados sob demanda.</td></tr>
</table>


## Como funciona
1. O mod olha os textos dos seus outros mods (nomes, descrições e textos de interface) e **detecta o idioma de cada um** (por exemplo, um mod em chinês ou em português).<br><sub>────────────────────────</sub>
2. Se o mod **já tem tradução** (dele mesmo ou de outro mod de tradução), ele **não traduz**. A tradução existente é a que vale.<br><sub>────────────────────────</sub>
3. O que **não tem tradução** é traduzido, do idioma detectado para o seu, por um programa que roda no seu PC (o **executável**). Se o texto já está no seu idioma, não é mexido. Pares sem modelo direto (ex.: chinês → português) passam pelo inglês, o que é um pouco mais lento e pode piorar a qualidade.<br><sub>────────────────────────</sub>
4. Se um mod der problema, **só aquele mod** é desligado. Os outros continuam normais.

## Por que preciso do executável?
Um mod do RimWorld é apenas um conjunto de arquivos que roda **dentro** do jogo e não tem como carregar um motor de tradução (os modelos de IA são grandes e pesados). Por isso a tradução é feita por um programa separado, o **UniversalTranslate-Helper.exe**, que roda no seu computador, usa a sua CPU, funciona **sem internet** (só baixa o modelo do seu idioma uma vez) e conversa com o mod **só dentro do seu próprio computador** (não passa pela internet nem pela rede da sua casa) e só atende pedidos que tragam uma senha. **Ele só precisa estar aberto enquanto há algo novo para traduzir.** O que já foi traduzido fica salvo e o jogo mostra sem o programa; o que ainda não foi traduzido aparece no idioma original até você abrir o programa.

## Instalação (passo a passo)
Baixe os dois arquivos na aba **Releases** (lado direito desta página, versão mais nova):
`UniversalTranslate-Helper.exe` (o programa que traduz) e `UniversalTranslate-Mod.zip` (o mod já pronto).

1. Instale o mod **Harmony** pela Steam Workshop.<br><sub>────────────────────────</sub>
2. Extraia a pasta `AutoTranslate` do `UniversalTranslate-Mod.zip` para dentro de `RimWorld\Mods`.<br><sub>────────────────────────</sub>
3. Dê **dois cliques** em `UniversalTranslate-Helper.exe`. Vai abrir **uma janela** (sem janela preta; em português ou inglês, conforme o seu sistema, dá para trocar no canto).<br><sub>────────────────────────</sub>
4. Na primeira vez: escolha o **idioma de destino** pelo nome (ele é escolhido **aqui, no executável**, e o jogo usa o mesmo) e espere o modelo baixar. **Deixe a janela aberta enquanto joga RimWorld.** Ela só é necessária enquanto algo estiver sendo traduzido durante o jogo: **se tudo já estiver traduzido, você não precisa mais dela e pode jogar com o programa fechado**. Abra de novo quando instalar mods novos ou atualizar algum.<br><sub>────────────────────────</sub>
5. Abra o RimWorld, ative **Harmony** e depois **Auto Translate** (nessa ordem) e inicie o jogo.<br><sub>────────────────────────</sub>
6. Na primeira vez a tradução leva alguns minutos; nas próximas é instantânea. Se quiser adiantar, use a aba **Traduzir mods** do executável (veja abaixo). Os ajustes do mod ficam em **Opções → Mods → Auto Translate**.

### Aviso do Windows ao abrir o `.exe`
O executável **ainda não tem assinatura digital** (certificado de publicador), e o Windows desconfia de programas de "fornecedor desconhecido". **Isso não é detecção de vírus.** Todo o código está neste repositório e o `.exe` é gerado automaticamente pelo GitHub (pasta `.github/workflows`), então dá para conferir como ele é feito.
- **"O Windows protegeu seu computador" (SmartScreen):** clique em **Mais informações → Executar assim mesmo**.<br><sub>────────────────────────</sub>
- **"O controle inteligente de aplicativos bloqueou um aplicativo" (Smart App Control, Windows 11):** esse bloqueio **não tem botão "executar assim mesmo"**. Hoje as saídas são: desligar o Controle Inteligente de Aplicativos (Segurança do Windows → Controle de aplicativos e navegador → Configurações do Controle Inteligente de Aplicativos), ou esperar a versão assinada. **Segundo a documentação da Microsoft, depois de desligado ele não volta a ser ligado sem redefinir o Windows**, então só faça isso se entender e aceitar esse custo. Assinar o executável é a solução definitiva e **ainda não foi feita**.

**Steam Workshop:** o mod será publicado lá (planejado). O executável continuará sendo baixado aqui, na aba Releases.

## Atualizar
Abra o `UniversalTranslate-Helper.exe` e clique em **Procurar atualização**. Se houver versão nova, clique em **Atualizar agora**: ele baixa do GitHub, confere o arquivo, atualiza o executável **e o mod** (se achar a pasta do RimWorld; **feche o jogo antes**) e reinicia sozinho. Ele também procura atualização quando abre.
- Só são aceitos arquivos do GitHub, e o arquivo baixado precisa bater com o hash (SHA-256) publicado na Release. Isso protege contra download corrompido, mas você continua confiando no repositório.<br><sub>────────────────────────</sub>
- Sem a janela: `UniversalTranslate-Helper.exe update` (use `--check` para só verificar).<br><sub>────────────────────────</sub>
- Se o repositório estiver **privado**, a verificação não funciona sem um token do GitHub (variável `RWTRANSLATE_GITHUB_TOKEN`). Com o repositório público funciona sem nada.

## Traduzir todos os mods de uma vez (aba "Traduzir mods", sem abrir o jogo)
Na aba **Traduzir mods** do executável:
- Ele procura os mods instalados, **mesmo os que não estão ativados no jogo**. Logo acima dos botões aparece a **lista numerada das pastas pesquisadas**: as pastas padrão (`Mods` do RimWorld e Oficina da Steam, marcadas como "padrão") e as que você adicionou com **Adicionar pasta** (marcadas como "adicionada por você"; ficam salvas e são pesquisadas sempre que você abre o programa, junto com as outras). Dá para ter várias pastas ao mesmo tempo.<br><sub>────────────────────────</sub>
- **Traduzir pendentes:** traduz o que ainda não foi traduzido, com **barra de progresso**, "X de N mods (%)" e o **tempo restante estimado** e uma **tabela por mod** (idioma de origem, textos, palavras e estado). No fim mostra o **resumo** com a quantidade de textos e de palavras traduzidas.<br><sub>────────────────────────</sub>
- **Procurar mods:** se você instalou mods novos (ou atualizou algum) depois, ele reconhece quais estão **novos** ou **alterados** e traduz só esses. **Refazer tudo** confere todos de novo (o que já está salvo não é traduzido outra vez).<br><sub>────────────────────────</sub>
- **Parar:** interrompe; o que já foi traduzido fica salvo.<br><sub>────────────────────────</sub>
- **Excluir traduções:** apaga todas as traduções salvas do idioma escolhido (pergunta antes de apagar). Os mods voltam a aparecer como novos. Suas correções manuais (`overrides`) são mantidas.<br><sub>────────────────────────</sub>
- **Coluna "Pasta":** clique em "Abrir pasta" na linha de um mod para abrir a pasta dele no explorador de arquivos.<br><sub>────────────────────────</sub>
- **Dois cliques em um mod** (fora da coluna "Pasta") abrem uma janela com três abas: **Traduzidos** (original e tradução; o texto completo aparece ao selecionar), **Palavras traduzidas** (os mesmos textos com o número de palavras de cada um) e **Não traduzidos por nós** (original, **tradução existente** e o motivo: "já tem tradução", "já está no seu idioma", "sem suporte", "falhou"). Se você trocar o idioma da janela com essa tela aberta, ela muda de idioma na hora.<br><sub>────────────────────────</sub>
- As traduções ficam no mesmo cache que o jogo usa, então ao jogar elas já estão prontas. **Se o jogo já estiver aberto**, ele percebe as traduções novas e as aplica sozinho em poucos segundos, sem reiniciar. É um adiantamento: ele lê os arquivos XML dos mods; textos que só existem durante o jogo (ou que dependem de outros mods) são traduzidos pelo mod na hora, como sempre.

## Opções do mod
Em **Opções → Mods → Auto Translate** (a tela segue o idioma do seu jogo):
- **Desativar traduções:** um botão que mostra os textos originais **na hora, sem reiniciar**, para você comparar. Clique de novo para voltar às traduções.<br><sub>────────────────────────</sub>
- **Atalho de teclado:** clique em "Definir atalho" e aperte a tecla que quiser, sozinha ou com Shift, Ctrl ou Alt (por exemplo, Shift + Tab). Em qualquer momento do jogo, esse atalho liga e desliga as traduções **em tempo real**, com um aviso na tela. Escolha uma combinação que o jogo ainda não use. Não dispara enquanto você escreve em uma caixa de texto.<br><sub>────────────────────────</sub>
- **Idioma de destino:** é escolhido **no executável**; aqui só aparece qual está em uso. Se você trocar no executável com o jogo aberto, o mod percebe e recarrega sozinho.<br><sub>────────────────────────</sub>
- **Lista de mods:** para cada mod você vê o que está acontecendo e se há **suporte** para o idioma escolhido ("com suporte", "SEM SUPORTE" ou "desconhecido" se o programa tradutor estiver fechado). Cada mod tem um interruptor **Ativado** e a escolha de qual tradução usar: automática (recomendada), a do próprio mod, a de outro mod de tradução, ou sempre a automática.<br><sub>────────────────────────</sub>
- **Avançado** (recolhido): o que traduzir (itens, interface, descrições), esconder os textos com acentos estranhos do modo desenvolvedor (veja abaixo), log detalhado, pasta de logs, relatório de problema e limpar o cache.

## O que ele traduz (e o que não)
- **Traduz:** nomes, descrições e textos de interface dos mods (inclusive os botões da aba Ordens que alguns mods criam em código), e a **descrição de cada mod na tela de Mods** (dos mods ativos).<br><sub>────────────────────────</sub>
- **Não traduz:** textos escritos diretamente no código de alguns mods, textos que já estão no seu idioma, e o conteúdo oficial do jogo.<br><sub>────────────────────────</sub>
- **Arquivos de "tradução" que só repetem o texto original** (comum: a própria ferramenta do RimWorld cria arquivos assim) **não contam como tradução**: esses textos são traduzidos. Uma tradução de verdade, feita pelo autor do mod ou por outro mod, é respeitada.<br><sub>────────────────────────</sub>
- **Detecção de idioma:** funciona bem com textos longos e com idiomas de alfabeto próprio (chinês, japonês, coreano, russo...). Em mods com poucos textos curtos em alfabeto latino ela assume inglês e pode errar (se acontecer, mande um relatório de problema).<br><sub>────────────────────────</sub>
- É tradução **automática**: pode ter erros. Você pode corrigir qualquer texto no arquivo `overrides` (veja abaixo) e a sua correção sempre vence.

## Textos com acentos estranhos no modo desenvolvedor
Com o **modo desenvolvedor** do RimWorld ligado, o próprio jogo marca os textos que não têm tradução no idioma do jogo colocando acentos nas letras ("Séàrçh ànd rèsçùè"). É um recurso para tradutores, mas atrapalha quem só quer jogar. O mod esconde isso e mostra o texto original (ou a tradução automática, quando existe). Dá para desligar em Opções → Mods → Auto Translate → Avançado. Se algum mod guardar o texto no início do jogo, reinicie o jogo depois de mudar a opção ou o modo desenvolvedor.

## Segurança da conexão entre o jogo e o programa
- O programa só "escuta" dentro do próprio computador (o endereço técnico `127.0.0.1` significa "este computador"; ele **não é o seu IP** e não é acessível pela internet nem por outros aparelhos da sua rede).<br><sub>────────────────────────</sub>
- Cada pedido precisa de uma **senha aleatória** guardada na sua pasta de dados; pedidos de páginas da internet abertas no navegador são recusados.<br><sub>────────────────────────</sub>
- O programa só sabe traduzir texto e baixar modelos de tradução: **não lê, apaga nem executa arquivos** a pedido de ninguém.<br><sub>────────────────────────</sub>
- Limite honesto: um programa malicioso que já esteja rodando na sua conta do Windows poderia ler a senha, mas esse programa já teria acesso a tudo, com ou sem este mod. Este código não passou por auditoria independente.

## Privacidade e arquivos
- **Nada é enviado pela internet.** A única coisa baixada é o modelo de tradução, uma vez (e as atualizações, se você clicar).<br><sub>────────────────────────</sub>
- **De onde vem o modelo:** do projeto aberto **Argos Translate**. A lista de modelos fica no GitHub dele e os arquivos são baixados de `argos-net.com`. É um download anônimo: **sem conta, sem login, sem chave e sem assinatura de nenhum serviço** (o programa não usa nenhuma IA online; quem traduz é o modelo, rodando no seu computador). Limite honesto: a lista do Argos não traz uma impressão digital (hash) dos modelos, então eles não são conferidos depois de baixados, só protegidos pela conexão segura (https).<br><sub>────────────────────────</sub>
- Tudo fica em `%LOCALAPPDATA%\RimWorldAutoTranslate`: modelos, traduções salvas (`cache`), suas correções (`overrides`) e logs (`logs`).

## Estado atual (transparência)
Esta é uma **versão inicial** (versão atual 0.007), feita com a ajuda do Claude. O mod compila contra a API do RimWorld 1.6 e o código passou nos testes automáticos (inclusive o teste da janela do executável no Windows do GitHub), mas **ainda não foi testado a fundo dentro do RimWorld** nem com muitos mods reais. Podem aparecer erros, principalmente com mods que mexem nos mesmos textos. A tradução automática pode errar. Ainda **não foi validado**: a tradução com os modelos reais em mods de verdade (os testes usam tradutores falsos) e a tela do mod dentro do jogo.

## Deu problema ou conflito com um mod?
1. No jogo: **Opções → Mods → Auto Translate → Avançado → Criar relatório de problema** (ou o botão **Relatório de problema** do executável).<br><sub>────────────────────────</sub>
2. Vai abrir uma página do GitHub e a pasta do relatório. **Arraste o arquivo** para a página e envie.

O relatório mostra qual mod causou o problema e o que aconteceu. Seu nome de usuário e suas pastas pessoais são removidos. Nada é enviado sem você anexar.

---
Histórico de mudanças: [CHANGELOG.md](CHANGELOG.md)

</div>
