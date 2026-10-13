# Universal Translate for RimWorld

Traduz **automaticamente** os outros mods do seu jogo para o seu idioma, **sem precisar de um mod de tradução para cada mod**.
A tradução é feita **no seu computador, sem internet e de graça**. Cada tradução fica salva, então ela só é feita uma vez.

> **Em desenvolvimento.** Este projeto foi feito com a ajuda do **Claude** (IA da Anthropic) e ainda está em fase inicial (versões 0.x). Veja "Estado atual" abaixo.

## Compatibilidade
| | |
|---|---|
| Jogo | RimWorld **1.6** |
| Sistema | **Windows** 10/11 |
| Idioma original dos mods | **Qualquer um**: o mod detecta sozinho (inglês, chinês, russo, português, ...) |
| Idioma de destino | Os **15 mais comuns**: Português, Inglês, Espanhol, Francês, Alemão, Italiano, Russo, Polonês, Turco, Ucraniano, Chinês, Japonês, Coreano, Holandês e Tcheco (a lista pode crescer depois). Os modelos são baixados sob demanda. |

## Como funciona
1. O mod olha os textos dos seus outros mods (nomes, descrições e textos de interface) e **detecta o idioma de cada um** (por exemplo, um mod em chinês ou em português).
2. Se o mod **já tem tradução** (dele mesmo ou de outro mod de tradução), ele **não traduz**. A tradução existente é a que vale.
3. O que **não tem tradução** é traduzido, do idioma detectado para o seu, por um programa que roda no seu PC (o **executável**). Se o texto já está no seu idioma, não é mexido. Pares sem modelo direto (ex.: chinês → português) passam pelo inglês, o que é um pouco mais lento e pode piorar a qualidade.
4. Se um mod der problema, **só aquele mod** é desligado. Os outros continuam normais.

## Por que preciso do executável?
Um mod do RimWorld é apenas um conjunto de arquivos que roda **dentro** do jogo e não tem como carregar um motor de tradução (os modelos de IA são grandes e pesados). Por isso a tradução é feita por um programa separado, o **UniversalTranslate-Helper.exe**, que roda no seu computador, usa a sua CPU, funciona **sem internet** (só baixa o modelo do seu idioma uma vez) e conversa com o mod **apenas dentro do seu PC** (endereço 127.0.0.1, protegido por senha). Sem ele aberto, o mod mostra os textos originais.

## Instalação (passo a passo)
Baixe os dois arquivos na aba **Releases** (lado direito desta página, versão mais nova):
`UniversalTranslate-Helper.exe` (o programa que traduz) e `UniversalTranslate-Mod.zip` (o mod já pronto).

1. Instale o mod **Harmony** pela Steam Workshop.
2. Extraia a pasta `AutoTranslate` do `UniversalTranslate-Mod.zip` para dentro de `RimWorld\Mods`.
3. Dê **dois cliques** em `UniversalTranslate-Helper.exe`. Vai abrir **uma janela** (sem janela preta; em português ou inglês, conforme o seu sistema, dá para trocar no canto).
4. Na primeira vez: escolha o **idioma de destino** pelo nome (ele é escolhido **aqui, no executável**, e o jogo usa o mesmo) e espere o modelo baixar. Depois **deixe a janela aberta** enquanto joga.
5. Abra o RimWorld, ative **Harmony** e depois **Auto Translate** (nessa ordem) e inicie o jogo.
6. Na primeira vez a tradução leva alguns minutos; nas próximas é instantânea. Se quiser adiantar, use a aba **Traduzir mods** do executável (veja abaixo). Os ajustes do mod ficam em **Opções → Mods → Auto Translate**.

### Aviso do Windows ao abrir o `.exe`
O executável **ainda não tem assinatura digital** (certificado de publicador), e o Windows desconfia de programas de "fornecedor desconhecido". **Isso não é detecção de vírus.** Todo o código está neste repositório e o `.exe` é gerado automaticamente pelo GitHub (pasta `.github/workflows`), então dá para conferir como ele é feito.
- **"O Windows protegeu seu computador" (SmartScreen):** clique em **Mais informações → Executar assim mesmo**.
- **"O controle inteligente de aplicativos bloqueou um aplicativo" (Smart App Control, Windows 11):** esse bloqueio **não tem botão "executar assim mesmo"**. Hoje as saídas são: desligar o Controle Inteligente de Aplicativos (Segurança do Windows → Controle de aplicativos e navegador → Configurações do Controle Inteligente de Aplicativos), ou esperar a versão assinada. **Segundo a documentação da Microsoft, depois de desligado ele não volta a ser ligado sem redefinir o Windows**, então só faça isso se entender e aceitar esse custo. Assinar o executável é a solução definitiva e **ainda não foi feita**.

**Steam Workshop:** o mod será publicado lá (planejado). O executável continuará sendo baixado aqui, na aba Releases.

## Atualizar
Abra o `UniversalTranslate-Helper.exe` e clique em **Procurar atualização**. Se houver versão nova, clique em **Atualizar agora**: ele baixa do GitHub, confere o arquivo, atualiza o executável **e o mod** (se achar a pasta do RimWorld; **feche o jogo antes**) e reinicia sozinho. Ele também procura atualização quando abre.
- Só são aceitos arquivos do GitHub, e o arquivo baixado precisa bater com o hash (SHA-256) publicado na Release. Isso protege contra download corrompido, mas você continua confiando no repositório.
- Sem a janela: `UniversalTranslate-Helper.exe update` (use `--check` para só verificar).
- Se o repositório estiver **privado**, a verificação não funciona sem um token do GitHub (variável `RWTRANSLATE_GITHUB_TOKEN`). Com o repositório público funciona sem nada.

## Traduzir todos os mods de uma vez (aba "Traduzir mods", sem abrir o jogo)
Na aba **Traduzir mods** do executável:
- Ele procura os mods instalados (pasta `Mods` do RimWorld e a pasta da Oficina da Steam; dá para **adicionar outra pasta**), **mesmo os que não estão ativados no jogo**.
- **Traduzir pendentes:** traduz o que ainda não foi traduzido, com **barra de progresso**, "X de N mods (%)" e uma **tabela por mod** (idioma de origem, textos, palavras e estado). No fim mostra o **resumo** com a quantidade de textos e de palavras traduzidas.
- **Procurar mods:** se você instalou mods novos (ou atualizou algum) depois, ele reconhece quais estão **novos** ou **alterados** e traduz só esses. **Refazer tudo** confere todos de novo (o que já está salvo não é traduzido outra vez).
- **Parar:** interrompe; o que já foi traduzido fica salvo.
- **Dois cliques em um mod** abrem uma janela com **o que foi traduzido** (original e tradução; o texto completo aparece ao selecionar) e **o que ficou de fora e por quê** ("já tem tradução", "já está no seu idioma", "sem suporte", "falhou").
- As traduções ficam no mesmo cache que o jogo usa, então ao jogar elas já estão prontas. É um adiantamento: ele lê os arquivos XML dos mods; textos que só existem durante o jogo (ou que dependem de outros mods) são traduzidos pelo mod na hora, como sempre.

## Opções do mod
Em **Opções → Mods → Auto Translate** (a tela segue o idioma do seu jogo):
- **Desativar traduções:** um botão que mostra os textos originais **na hora, sem reiniciar**, para você comparar. Clique de novo para voltar às traduções.
- **Idioma de destino:** é escolhido **no executável**; aqui só aparece qual está em uso. Se você trocar no executável com o jogo aberto, o mod percebe e recarrega sozinho.
- **Lista de mods:** para cada mod você vê o que está acontecendo e se há **suporte** para o idioma escolhido ("com suporte", "SEM SUPORTE" ou "desconhecido" se o programa tradutor estiver fechado). Cada mod tem um interruptor **Ativado** e a escolha de qual tradução usar: automática (recomendada), a do próprio mod, a de outro mod de tradução, ou sempre a automática.
- **Avançado** (recolhido): o que traduzir (itens, interface, descrições), log detalhado, pasta de logs, relatório de problema e limpar o cache.

## O que ele traduz (e o que não)
- **Traduz:** nomes, descrições e textos de interface dos mods, e a **descrição de cada mod na tela de Mods** (dos mods ativos).
- **Não traduz:** textos escritos diretamente no código de alguns mods, textos que já estão no seu idioma, e o conteúdo oficial do jogo.
- **Arquivos de "tradução" que só repetem o texto original** (comum: a própria ferramenta do RimWorld cria arquivos assim) **não contam como tradução**: esses textos são traduzidos. Uma tradução de verdade, feita pelo autor do mod ou por outro mod, é respeitada.
- **Detecção de idioma:** funciona bem com textos longos e com idiomas de alfabeto próprio (chinês, japonês, coreano, russo...). Em mods com poucos textos curtos em alfabeto latino ela assume inglês e pode errar (se acontecer, mande um relatório de problema).
- É tradução **automática**: pode ter erros. Você pode corrigir qualquer texto no arquivo `overrides` (veja abaixo) e a sua correção sempre vence.

## Privacidade e arquivos
- **Nada é enviado pela internet.** A única coisa baixada é o modelo de tradução, uma vez (e as atualizações, se você clicar).
- Tudo fica em `%LOCALAPPDATA%\RimWorldAutoTranslate`: modelos, traduções salvas (`cache`), suas correções (`overrides`) e logs (`logs`).

## Estado atual (transparência)
Esta é uma **versão inicial** (0.x), feita com a ajuda do Claude. O mod compila contra a API do RimWorld 1.6 e o código passou nos testes automáticos (inclusive o teste da janela do executável no Windows do GitHub), mas **ainda não foi testado a fundo dentro do RimWorld** nem com muitos mods reais. Podem aparecer erros, principalmente com mods que mexem nos mesmos textos. A tradução automática pode errar.

## Deu problema ou conflito com um mod?
1. No jogo: **Opções → Mods → Auto Translate → Avançado → Criar relatório de problema** (ou o botão **Relatório de problema** do executável).
2. Vai abrir uma página do GitHub e a pasta do relatório. **Arraste o arquivo** para a página e envie.

O relatório mostra qual mod causou o problema e o que aconteceu. Seu nome de usuário e suas pastas pessoais são removidos. Nada é enviado sem você anexar.

---
Histórico de mudanças: [CHANGELOG.md](CHANGELOG.md)
