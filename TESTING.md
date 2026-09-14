# TESTING.md — Levantamento de testabilidade (2026-09-14)

> Sessão de LEVANTAMENTO apenas. Nenhum código foi alterado, nenhum teste foi
> escrito. Este documento registra o inventário, o estado atual e um plano de
> trabalho para sessões futuras.

## 0. Achado que muda a premissa da tarefa

O pedido partiu de "o projeto não possui suíte de testes automatizados". **Isso
não é verdade hoje.** O projeto já tem:

```
tests/
  test_calendar.py        (67 linhas)
  test_historico.py       (119 linhas)
  test_jolpica.py         (117 linhas)
  test_normalize.py       (40 linhas)
  test_parser.py          (196 linhas)
  test_pipeline.py        (196 linhas)
  test_scoring.py         (88 linhas)
  test_site.py            (183 linhas)
  test_whatsapp_import.py (268 linhas)
```

`python -m pytest tests/` → **93 passed, 4 subtests passed**, offline, ~1.5s.
São testes `unittest.TestCase` (às vezes com `subTest`), rodados via pytest.
Cobrem `normalize`, `parser`, `scoring`, `calendar`, `jolpica` (só a parte
`build_*`, pura — `fetch_*`, que faz rede, não é exercitado), `site.generate`
(com workspace `tempfile` isolado), `pipeline` (com `fetch_result` mockado) e
`historico`/`whatsapp_import` (importação de temporadas antigas).

Isso **não invalida o pedido** — o levantamento abaixo mostra que a cobertura
real tem lacunas grandes (o front-end inteiro, a CLI, os scripts do Actions,
o Apps Script) e que vale auditar se os testes existentes checam o
*comportamento pretendido* ou só "documentam o que o código faz hoje" — mas
muda o ponto de partida: não é "criar do zero", é **auditar o que existe,
preencher lacunas e proteger contra regressão no que falta**.

**Pergunta em aberto para você:** quer que a Sessão 1 do plano abaixo inclua
uma auditoria linha a linha dos 93 testes existentes contra o comportamento
descrito no `CONTEXTO.md` (para achar testes que "confirmam bug" em vez de
"provam comportamento certo")? Não fiz isso aqui — seria uma leitura extensa
e a regra crítica pede exatamente esse cuidado nas próximas sessões, então
recomendo tratar isso como o primeiro lote de trabalho, não decidir sozinho.

## 1. Inventário de funcionalidades

### Núcleo Python (`bolao/`) — o motor do bolão

| Módulo | O que faz | Onde mora | Criticidade |
|---|---|---|---|
| `normalize.py` | Normaliza chaves/nomes de piloto e jogador (acento, caixa, alias → fallback 3 letras) | `bolao/normalize.py` (59 linhas) | **Crítica** — todo o resto depende de nomes/códigos corretos |
| `parser.py` | Parseia o texto colado do WhatsApp em `Sheet`/`Bet` (cabeçalho + blocos por jogador); tolera variações de formato, fecha blocos sem bônus, filler de enfeite | `bolao/parser.py` (333 linhas) | **Crítica** — é a porta de entrada de todo palpite |
| `scoring.py` | Pontua um palpite contra o resultado real (regra 2/1/0 do top6 + bônus do piloto da rodada) | `bolao/scoring.py` (130 linhas) | **Crítica** — é a regra de negócio central (seção 2 do CONTEXTO.md) |
| `calendar.py` | Resolve nome solto de corrida → rodada (`resolve_race`, casamento por palavras, `AmbiguousRace`/`RaceNotFound`) | `bolao/calendar.py` (85 linhas) | **Crítica** — grava no round errado é uma falha silenciosa grave (já aconteceu, ver Etapa 5/Madrid no CONTEXTO.md) |
| `jolpica.py` | Busca calendário/entry list/resultado na API Jolpica-F1; separa `fetch_*` (rede) de `build_*` (transformação pura) | `bolao/jolpica.py` (334 linhas) | **Crítica** (dado de resultado) — mas a parte de rede (`fetch_*`) é a única dependência externa viva do projeto |
| `site.py` | Consolida rodadas em `standings.json`/`bets.json`/`results.json`/`calendar.json`/`seasons.json`; regras de compensação, `avg_points`, `format`/`meta` por temporada | `bolao/site.py` (549 linhas) | **Crítica** — é o que o site de fato lê |
| `pipeline.py` | Orquestra `run`/`retry`: grava mensagem → busca resultado (se faltando) → gera site; códigos de saída 0/1/2 | `bolao/pipeline.py` (179 linhas) | **Crítica** — é o que o GitHub Actions chama de ponta a ponta |
| `formats.py` | `SeasonFormat` (top_n, bonus, pontos, compensação) por ano — fonte única da verdade sobre regras que mudaram 2021→2026 | `bolao/formats.py` (64 linhas) | **Secundária** hoje (2026 não muda), mas **crítica** para não quebrar o histórico se formatos mudarem de novo |
| `cli.py` | CLI manual de uma rodada (`python -m bolao.cli msg.txt result.json`) | `bolao/cli.py` (86 linhas) | **Periférica** — ferramenta de conferência manual, não roda em produção (o pipeline não a usa) |
| `historico.py` | Importa temporada 2025 de CSV (`palpites_2025.csv`) + Jolpica, com relatório de conferência | `bolao/historico.py` (222 linhas) | **Periférica** hoje — já rodou, dados já estão versionados; só volta a rodar se o usuário corrigir uma linha do CSV |
| `whatsapp_import.py` | Importa temporadas 2021-2024 do export bruto do WhatsApp (reconhecimento de blocos por sequência, resolução de rodada por data, geração de CSV) | `bolao/whatsapp_import.py` (1224 linhas!) | **Periférica** — é uma migração one-off já concluída (dados congelados nos CSV); mas é o módulo **maior e mais complexo** do projeto, e ninguém revisita a lógica com frequência |

### Site estático (`docs/`) — **sem nenhum teste hoje**

| Componente | O que faz | Onde mora | Criticidade |
|---|---|---|---|
| `docs/app.js` | Client-side puro: renderiza ranking, palpites por jogador, gráficos (Chart.js), simulador de projeção, matriz posição×corrida, Hall of Fame, página de jogador, modo histórico por `?ano=`, cálculos de média/compensação/posição | `docs/app.js` (**3823 linhas**) | **Crítica de exibição** — é a única coisa que o usuário final (grupo do WhatsApp) realmente vê; bugs aqui são silenciosos (número errado na tela, ninguém percebe) |
| `docs/index.html` / `docs/style.css` | Esqueleto/estilo | `docs/` (245 / 1958 linhas) | Secundária/periférica |
| `docs/data/*.json` | Dados gerados por `bolao/site.py` (contrato estável documentado no CONTEXTO.md) | `docs/data/<ano>/*.json` | Crítica como **contrato**, não como "funcionalidade" própria |

`docs/app.js` reimplementa cálculos que já existem em Python e testados
(médias, compensação, projeção do simulador, agregação de pontos por piloto)
— **sem nenhuma rede de proteção**. É o maior ponto cego do projeto hoje.

### Infraestrutura de disparo (fora do pytest, plataformas externas)

| Componente | O que faz | Onde mora | Criticidade |
|---|---|---|---|
| `.github/workflows/pipeline.yml` | Workflow: `repository_dispatch`/`workflow_dispatch` → roda `bolao.pipeline` → commit/push; laço "verificador" (retry a cada 30min até 5h se quali não saiu) | `.github/workflows/pipeline.yml` (95 linhas) | **Crítica** — é o que faz o site atualizar sozinho; já teve 2 falhas reais (Etapa 5: Spa/parse, Hungaroring/verificador) |
| `.github/scripts/commit-push.sh`, `registra-estado.sh` | Commit condicional + rebase/push; tradução de código de saída → variáveis de ambiente do workflow | `.github/scripts/` (29 + 30 linhas) | Secundária, mas roda dentro do caminho crítico do workflow |
| `google-apps-script/Code.gs` | `onFormSubmit` do Google Forms → `repository_dispatch` no GitHub; notificação de erro por e-mail | `google-apps-script/Code.gs` (118 linhas) | **Crítica** para o fluxo operacional (é o gatilho pelo celular), mas roda no runtime do Google Apps Script — **fora de qualquer suíte Python** |

### Dados versionados (não é "funcionalidade", mas é dependência de todos os testes acima)

`data/<ano>/` (calendário, drivers, mensagens brutas, resultados, scores) e
`docs/data/<ano>/` (saída gerada) para as temporadas 2021-2026. Vários testes
já existentes (`test_scoring.py`, por exemplo) leem arquivos reais de
`data/2026/` como fixture — funciona hoje, mas acopla o teste ao estado atual
dos dados de produção (ver seção 4).

## 2. Caminho crítico

A menor cadeia que precisa funcionar para o bolão cumprir seu propósito
(pontuar um quali e refletir no ranking) é:

```
texto do WhatsApp
  → parser.parse_sheet          (texto → Sheet/Bet)
  → jolpica.fetch_result        (rede → resultado real do quali)
  → scoring.score_sheet         (Sheet + Result → pontuação por jogador)
  → site.generate                (rodadas → standings/bets/results.json)
  → docs/app.js: renderRanking   (JSON → tela)
```

`pipeline.run`/`retry` é a orquestração desse caminho, e
`.github/workflows/pipeline.yml` + `Code.gs` são os dois jeitos de dispará-lo
(retry manual e Forms). Se qualquer elo quebrar **sem erro visível**, o
ranking fica errado e ninguém percebe até alguém contar pontos na mão — já
aconteceu 2x (parser silencioso na Etapa 5, cabeçalho ambíguo em Madrid). Por
isso o plano abaixo prioriza justamente as falhas *silenciosas* desse caminho,
não só as que já têm cobertura.

`calendar.resolve_race` merece menção à parte: é o único elo do caminho
crítico cuja falha **nunca lança erro** (sempre devolve alguma corrida por
"palavra em comum") — é o ponto de maior risco de dado errado sem aviso.

## 3. Estado atual e stack

- **Já existe:** `unittest`/pytest, 93 testes, offline, ~1.5s, sem
  configuração de projeto (nenhum `pytest.ini`/`pyproject.toml`/`setup.cfg` —
  roda por convenção de descoberta).
- **Stack recomendada para continuar (sem introduzir nada exótico):**
  manter `unittest` + `pytest` como executor (já funciona, zero dependência
  nova). Não há motivo para trocar de framework.
- **O que precisaria ser simulado, por módulo:**
  - **Rede** (`bolao/jolpica.py: fetch_*`): já isolado de `build_*`; os testes
    de rede propriamente ditos (URL montada certa, timeout, erro HTTP) **não
    existem** — só a transformação `build_*` é testada. Precisaria de
    mock de `urllib`/`http.client` ou fixtures gravadas (o projeto já tem
    `tests/fixtures/jolpica/*.json` para isso).
  - **Sistema de arquivos** (`site.generate`, `pipeline.run/retry`,
    `historico.build`): já tratado com `tempfile`/workspace isolado nos
    testes existentes — padrão a repetir.
  - **Relógio/data** (`whatsapp_import._dia_quali`, `resolve_round(...,
    passado=True)`): datas reais de calendário são usadas como fixture; não
    há teste que congele "hoje" — hoje isso não é problema porque a lógica
    não olha o relógio do sistema, só compara datas de dados, mas vale
    confirmar se alguma função usa `datetime.now()`/`date.today()` sem
    injeção (não vi nenhuma nos módulos lidos).
  - **Git/GitHub Actions** (`commit-push.sh`, o workflow em si): não dá para
    testar com pytest — precisaria de um ambiente de shell/act (`nektos/act`)
    ou aceitar que esse pedaço só é validado em produção (como já vem sendo).
  - **Google Apps Script** (`Code.gs`): roda no runtime do Google, fora do
    alcance de qualquer teste Python; só é testável com o
    `testarDisparoManual` que já existe dentro do próprio script (validação
    manual, documentada no CONTEXTO.md).
  - **Front-end** (`docs/app.js`): hoje **zero infraestrutura de teste** —
    nem test runner, nem DOM simulado (jsdom), nem bundler. Precisaria decidir
    uma stack (ex.: Node + `node:test` ou Vitest + jsdom, sem framework de UI
    porque o código é vanilla) — decisão a tomar com você, não vou escolher
    sozinho.

## 4. Obstáculos de testabilidade (só aponto — não refatorei nada)

1. **`docs/app.js` é um arquivo único de 3823 linhas, sem módulos, sem build.**
   Todas as funções são globais no escopo do `<script>`; não há
   `export`/`import`. Para testar qualquer função (`construirProjecoesSimulador`,
   `calcularPosicoesPorRodada`, `agregarApostasPorPiloto`, etc.) fora do
   navegador, seria preciso carregar o arquivo inteiro num ambiente que
   entenda `fetch`/`DOM`/`Chart` global — ou extrair funções puras para um
   módulo separado (decisão de arquitetura, não cabe eu tomar aqui).
2. **`site.generate()` mistura leitura de disco, transformação e escrita de
   disco numa função só** (549 linhas no arquivo, a função `generate` é o
   grosso dele). Os testes atuais contornam isso com workspace `tempfile`
   inteiro — funciona, mas é lento/verboso comparado a testar a transformação
   pura isoladamente. Não é um bloqueador (já é testado), é um atrito.
3. **`pipeline.run`/`retry` têm efeito colateral (escreve arquivo, chama rede)
   embutido na função de orquestração**, sem uma camada que devolva "o que
   faria" sem fazer. Os testes existentes mockeiam `fetch_result` diretamente
   (acoplado à implementação, não a uma interface) — funciona porque o projeto
   é pequeno, mas qualquer refatoração de `pipeline.py` arrisca quebrar teste
   por motivo errado.
4. **Testes acoplados a dados de produção reais** (`test_scoring.py` lê
   `data/2026/messages/9.txt` e `data/2026/results/9.json` direto do repo).
   Isso é uma escolha deliberada e documentada ("conferência manual contra o
   grid real") — é uma boa forma de regressão, mas significa que **editar um
   dado de produção pode quebrar um teste sem ninguém perceber a relação**.
   Vale marcar esses casos claramente como "regressão contra dado real" vs.
   "teste de regra isolada" (o arquivo já faz isso, só reforçando).
5. **`resolve_race` nunca falha "para o lado seguro"** — sempre devolve uma
   corrida por "mais palavras em comum". Isso é uma decisão de produto
   registrada no CONTEXTO.md (não é bug), mas do ponto de vista de teste é um
   obstáculo real: é fácil escrever um teste que "prova" que a função
   funciona com os alias atuais e nunca testar o caso feio (cabeçalho novo,
   ambíguo de verdade) que é justamente o que já causou incidente em produção
   (Madrid).
6. **`whatsapp_import.py` (1224 linhas) depende de um arquivo fora do
   repositório** (`historico_wpp/` está no `.gitignore`, por privacidade). Os
   11 testes existentes usam fixtures sintéticas menores — o comportamento
   real (recuperação de bloco cortado, resolução por data em anos sem
   cabeçalho) só foi validado uma vez, manualmente, contra o export real, e
   não é reproduzível por quem não tem esse arquivo. Isso é aceitável para um
   script one-off já concluído, mas significa que qualquer teste novo aqui
   testa a *lógica*, nunca o *dado real* de novo.
7. **Sem tipo de contrato formal entre `bolao/site.py` e `docs/app.js`** —
   o "formato estável" é só documentação em prosa no CONTEXTO.md. Um teste de
   contrato (schema/snapshot dos JSONs gerados) não existe; hoje a única
   proteção é os testes Python de `site.generate` + inspeção visual do site.

## 5. Plano em lotes (cada lote = 1 sessão, termina com suíte verde + commit)

Ordenado pelo que mais dói se quebrar em produção (o grupo depende do
ranking estar certo toda corrida), não pela ordem das etapas do projeto.

1. **Lote 0 — Auditoria dos 93 testes existentes contra o comportamento
   pretendido.** Antes de escrever teste novo, confirmar que os testes atuais
   provam a regra do CONTEXTO.md (seção 2) e não só "o que o código faz hoje".
   Foco: `test_scoring.py` (regra 2/1/0 + bônus), `test_parser.py` (formato
   da mensagem), `test_site.py` (compensação/mínima). Qualquer divergência
   encontrada é reportada como achado, sem corrigir nada nesta sessão.
2. **Lote 1 — `calendar.resolve_race` e o caso ambíguo/desconhecido.** É o
   elo que já causou incidente real e nunca lança erro por padrão; testes que
   cubram exatamente o cenário de cabeçalho novo/ambíguo (não só os aliases
   já cadastrados) valem mais aqui do que em qualquer outro módulo.
3. **Lote 2 — `pipeline.run`/`retry`, os 3 códigos de saída (0/1/2) e a
   idempotência.** É o que o Actions chama; já tem testes (Etapa 5), mas vale
   fechar o caso "rodada já pontuada, roda de novo, não duplica/sobrescreve
   errado" e o caso "`ResultUnavailable` não derruba o pipeline".
4. **Lote 3 — `parser.parse_sheet`, tolerância a formato malformado.** Cobrir
   os 3 bugs reais já documentados no CONTEXTO.md (bloco sem `P#`, filler de
   frase nova tipo "piloto da vez", jogador cortado) como testes de
   regressão nomeados pelo incidente, não só pela regra.
5. **Lote 4 — `site.generate`: compensação/mínima e `avg_points`.** Regra com
   mais nuance de negócio (seção 2 do CONTEXTO.md) e que já teve um bug de
   cálculo corrigido (média usando total errado, ver ajuste 2026-09-08d).
6. **Lote 5 — decidir e montar a stack de teste do `docs/app.js`.** Sessão de
   decisão + setup mínimo (escolher runner, extrair 2-3 funções puras de
   cálculo como prova de conceito: `calcularPosicoesPorRodada`,
   `construirProjecoesSimulador`, a lógica de compensação no front). Esse
   lote é o maior risco do projeto hoje por estar em zero, mas também o mais
   caro — não force para o início só por estar arriscado; discutir com você
   se vale a pena versus aceitar o risco.
7. **Lote 6 — `jolpica.fetch_*` com mocks de rede reais** (não só o `build_*`
   que já é testado): URL montada certa por temporada/rodada, timeout,
   erro HTTP, `ResultUnavailable` disparado nas condições certas.
8. **Lote 7 — `historico.build`/`whatsapp_import`, teste de regra pura.**
   Menor prioridade — são scripts one-off já concluídos; testar aqui é mais
   sobre não quebrar se algum dado precisar de correção pontual no futuro do
   que sobre risco atual.
9. **Fora do escopo de pytest (registrar, não agendar como lote):** o
   workflow do GitHub Actions e o `Code.gs` continuam validados manualmente
   em produção, como documentado no CONTEXTO.md — não há stack de teste
   automatizado óbvia e barata para eles que valha a pena montar agora.

Cada lote deve, como sempre nesse projeto, terminar com `git status` limpo e
um commit próprio (`Etapa X: ...`), e — pela regra crítica desta tarefa —
qualquer teste que revele divergência entre código e comportamento
pretendido deve ser reportado como achado, não silenciosamente ajustado para
passar.
