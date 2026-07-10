# Bolão F1 — Contexto do Projeto

> Documento vivo. Registra objetivo, regras, decisões técnicas e o plano de
> construção. Atualizar conforme o projeto evolui.

## 1. Objetivo

Automatizar e disponibilizar online um **bolão de palpites do qualifying da
Fórmula 1**. Cada participante envia um palpite antes de cada quali (via
WhatsApp). Depois do quali, o palpite é pontuado e somado ao **ranking da
temporada**, que decide o campeão no fim do ano.

Escopo atual: **temporada 2026**. Históricos de anos anteriores entram depois
(formatos diferentes — decisão adiada).

## 2. Regras de pontuação

Cada palpite tem duas partes: um **top6** e o **palpite do piloto da rodada**.

### Top6 (máximo 12 pts)
O jogador aposta 6 pilotos, em ordem (P1 a P6). Para **cada** piloto apostado:
- Piloto na **posição exata** do quali → **2 pts**
- Piloto **dentro do top6 real, mas em outra posição** → **1 pt**
- Piloto **fora do top6 real** → **0 pt**

### Piloto da rodada (máximo 1 pt)
A cada corrida, um piloto específico é escolhido (definido no cabeçalho da
mensagem). Todos chutam a **posição exata dele no grid inteiro (P1–P22)** — a
grade de 2026 tem até 22 pilotos (11 equipes). Chutes fora da grade são aceitos
como vieram (preservam o palpite), mas nunca casam com a posição real → 0 pt.
- Acertou a posição exata → **1 pt**
- Caso contrário → **0 pt**

Esse palpite é **independente** do top6 (o piloto pode aparecer no top6 do
jogador em outra posição sem conflito).

### Total
**Máximo por corrida: 13 pts.** Sem desempate definido por enquanto (adiado).

### Pontuação mínima (compensação de quem não aposta)
Nem todo jogador aposta em toda corrida. Para não penalizar demais quem falta
uma rodada (nem beneficiar quem "escapa" de uma corrida ruim), cada rodada
define uma **pontuação mínima**: 1 a menos que a menor pontuação registrada
entre quem apostou naquela rodada (ex.: pontuações de 3 a 6 → mínima = 2).

Todo jogador que **faz parte do ranking da temporada** (apostou em pelo menos
uma rodada, em qualquer momento do ano) recebe a pontuação mínima da rodada em
que não apostou — inclusive rodadas **anteriores** à sua estreia no bolão.
Essa pontuação de compensação **entra no total do ranking**, mas **não conta
como rodada apostada** (a contagem de circuitos apostados de cada jogador
continua sendo só as rodadas em que ele realmente enviou palpite).

## 3. Formato da mensagem de palpite (WhatsApp)

Exemplo real (Silverstone):

```
Qualify Bolao Silverstone      <- linha 1: identifica a corrida
Piloto Hamilton                <- linha 2: piloto da rodada (bônus)

Guilherme                      <- nome do jogador
ANT                            <- top6, um piloto por linha (P1..P6)
RUS
HAM
VER
NOR
PIA
P1                             <- chute da posição do piloto da rodada

Dalla
HAM
ANT
RUS
VER
NOR
LEC
P2

...
```

Estrutura: cabeçalho (2 linhas) + blocos por jogador separados por linha em
branco. Cada bloco = nome + 6 códigos de piloto + linha `P#`.

### Desafios de parsing (tratados no código)
- **Códigos inconsistentes:** `HAM`/`Ham`, `VER`/`Ver`, e possivelmente nomes
  completos em mensagens antigas → normalizar para código de 3 letras.
- **Nomes de jogadores com acento/pontuação:** `Vinícius`, `Caio L.`,
  `Caliman` → cada jogador precisa de um **id estável** (mapa de apelidos),
  para somar corretamente no ranking da temporada.
- **Sprints ignorados:** fins de semana com Sprint Qualifying **não contam**;
  só o qualifying principal.

## 4. Decisões técnicas

| Tema            | Decisão                                                        |
|-----------------|----------------------------------------------------------------|
| Linguagem       | **Python** (parsing, pontuação, geração dos dados do site)     |
| Hospedagem      | **GitHub Pages** (site estático, custo zero)                   |
| Execução        | **GitHub Actions** (Python roda na nuvem, não na máquina local)|
| Gatilho         | **Google Forms → Apps Script → GitHub** (operação pelo celular)|
| Fonte F1        | **API Jolpica-F1** (sucessora da Ergast, gratuita, sem chave)  |
| Sprints         | Ignorados (só quali principal)                                 |
| Desempate       | Não implementado por enquanto                                  |

### Por que essas escolhas
- **Sem PC:** o operador (Guilherme) nem sempre tem computador. Todo o
  processamento roda na nuvem (Actions); o disparo é um Google Forms no celular.
- **Integridade social:** os palpites já ficam travados no grupo do WhatsApp
  antes do quali. Por isso a transcrição pode acontecer **depois** do quali,
  numa única submissão (palpites + gatilho de cálculo juntos).
- **Custo zero:** GitHub Pages + Actions + Jolpica + Google Forms são gratuitos.

## 5. Fluxo de operação (pelo celular)

```
Você (celular)
  → Google Forms: cola o bloco do WhatsApp + identifica a corrida → envia
    → Apps Script (onFormSubmit): POST repository_dispatch para o GitHub
      → GitHub Actions (Python):
          1. parseia os palpites do texto
          2. busca o resultado do quali na Jolpica-F1
          3. normaliza códigos e nomes
          4. calcula pontuação (top6 + bônus) por jogador
          5. atualiza ranking da temporada e dados do site
          6. commit dos resultados
      → GitHub Pages: publica o site atualizado
```

Se o resultado ainda não estiver na API na hora do envio, o cálculo pode ser
re-disparado (re-run da Action) sem reenviar os palpites.

## 6. Modelo de dados (rascunho)

```
data/
  drivers.json              # grid 2026: alias/nome -> código 3 letras
  2026/
    players.json            # jogadores: id canônico + apelidos + nomes
    calendar.json           # corridas 2026: round, circuito, data, piloto-bônus
    messages/<round>.txt    # texto bruto do WhatsApp por rodada (entrada da Etapa 3)
    results/<round>.json    # resultado do quali (da Jolpica)
    scores/<round>.json     # pontuação por jogador na rodada (gerado na Etapa 3)
docs/                       # site estático servido pelo GitHub Pages
  index.html                # ranking + palpites por jogador (com filtro)
  data/                     # dados que o front-end lê (gerados na Etapa 3)
    standings.json          # ranking acumulado da temporada
    bets.json               # histórico de palpites por jogador (detalhe)
    results.json            # grid real por rodada (histórico de posições)
```

Decisões de modelagem a fechar na implementação:
- `drivers.json` e o mapa de apelidos de jogadores serão construídos a partir
  dos dados reais de 2026 (entry list via Jolpica) — **não inventar códigos**.
- Resolver `circuito → round` via `calendar.json` (buscar o calendário 2026 da
  Jolpica uma vez).

## 7. Site (versão inicial)

Prioridade: **fazer funcionar** antes de enfeitar. Entregar:
- **Ranking da temporada** (tabela: posição, jogador, pontos, nº de rodadas).
- **Palpites por jogador**, com filtro (ver o que cada um apostou por corrida
  e quanto pontuou).

Melhorias futuras (backlog): evolução por rodada (gráfico), pódio por corrida,
melhor palpiteiro, média de pontos, acertos de pole, sequências, histórico de
anos anteriores.

## 8. Plano de construção (etapas)

Cada etapa é pensada para ser desenvolvida em **uma conversa focada**. Toda
conversa deve ler este `CONTEXTO.md` inteiro (o `CLAUDE.md` já orienta isso) e
então trabalhar **apenas** na etapa indicada, respeitando as entradas/saídas
abaixo para não invadir as etapas vizinhas.

Status: ⬜ não iniciada · 🟡 em andamento · ✅ concluída

---

### Etapa 1 — Parser + pontuação (núcleo Python) ✅
- **Objetivo:** módulo Python puro que recebe (a) o texto do WhatsApp e (b) o
  resultado do quali, e devolve a pontuação por jogador (top6 + bônus).
- **Entradas:** texto de exemplo (Silverstone, na seção 3); resultado do quali
  (mock no começo); mapa inicial de apelidos de piloto/jogador.
- **Saídas:** funções/CLI que imprimem a pontuação por jogador e o detalhamento;
  testes automatizados usando o exemplo de Silverstone.
- **Pronto quando:** a pontuação bate com conferência manual e os testes passam.
- **Depende de:** nada externo (roda 100% offline). É a base de tudo.
- **Entregue:** pacote `bolao/` (`normalize`, `parser`, `scoring`, `cli`) +
  testes offline. Rodar: `python -m unittest discover -s tests`. CLI de uma
  rodada: `python -m bolao.cli <mensagem.txt> <resultado.json> --detalhe`.
  (O mock de Silverstone foi removido na Etapa 3; os testes usam os dados reais
  de 2026 em `data/2026/`.)

**Formatos estáveis definidos aqui (a Etapa 2 deve produzir isto):**
- **Resultado do quali** (o que `scoring.Result.from_dict` consome):
  `{"race": "<nome>", "order": ["VER","NOR", ...]}` — `order` = códigos de 3
  letras por posição, **índice 0 = P1** (aceita também a chave `results`).
- **drivers.json:** `{"aliases": {"<chave normalizada>": "<COD3>"}}`. Chave
  passada por `normalize.normalize_key` (sem acento, minúscula). Etapa 2 gera
  da entry list real (não inventar códigos); o formato do arquivo não muda.
- **players.json:** `{"aliases": {"<chave normalizada>": "<id canônico>"}}`,
  para unir variantes de nome no mesmo id do ranking.
- Sem alias, o fallback é: piloto = 3 primeiras letras maiúsculas; jogador =
  nome normalizado com espaços → `_`. Cada bloco de jogador = 8 linhas
  (nome + 6 pilotos + `P#`).

### Etapa 2 — Integração Jolpica-F1 ✅
- **Objetivo:** buscar dados reais de 2026 na API Jolpica.
- **Saídas:** `calendar.json` (corridas 2026), `drivers.json` (entry list →
  código de 3 letras) e `results/<round>.json` no **formato que a Etapa 1
  consome**.
- **Pronto quando:** consegue puxar um quali real de 2026 e alimentar a
  pontuação da Etapa 1 sem adaptação manual.
- **Depende de:** Etapa 1 (o formato de resultado esperado pelo pontuador).
- **Entregue:** `bolao/jolpica.py` (fetch + build + CLI) e `bolao/calendar.py`
  (resolvedor nome→rodada, offline). Gerados dos dados reais de 2026:
  `data/2026/calendar.json`, `data/drivers.json`, `data/2026/results/1.json`.
  Fixtures reais da Jolpica em `tests/fixtures/jolpica/`; testes offline
  (`tests/test_jolpica.py`, `tests/test_calendar.py`) — total do projeto: 39.
  CLI: `python -m bolao.jolpica {calendar|drivers|result <round>|results}`
  (`--season`, `--base-url`, `--out`). `results` baixa todos os qualis já
  ocorridos do ano de uma vez (pula rodadas futuras). Um quali real (Melbourne,
  rodada 1) alimenta a pontuação da Etapa 1 e dá 13 num palpite perfeito.
  **Baixados e conferidos** os qualis já ocorridos de 2026: rodadas 1–9 em
  `data/2026/results/` (top6 batendo com a Jolpica).

**Decisões fixadas na Etapa 2 (não reabrir sem o usuário pedir):**
- **API:** base `https://api.jolpi.ca/ergast/f1` (compatível Ergast), sem chave.
  Rede via `urllib` (stdlib, sem dependências). `fetch_*` (rede) é separado de
  `build_*` (transformação pura) — os testes exercitam só `build_*`, offline.
- **`race_id = "{season}-{round:02d}"`** (ex.: `"2026-12"`) — chave única
  temporada+rodada em todo o projeto.
- **`calendar.json`:** `{"season", "races":[{race_id, season, round, circuit
  (slug=circuitId), race (exibição=locality), date, sprint (bool), aliases:[]}]}`.
  `aliases` = nomes normalizados (circuito/cidade/país/nome oficial) para
  resolver o nome solto do cabeçalho → rodada.
- **Sprint:** só marcado (`"sprint": true`); **não exclui** a corrida. O quali
  **principal** de fim de semana de Sprint continua valendo (ex.: Silverstone
  2026 = rodada 9 é Sprint, e ainda assim conta). Nunca buscamos a sessão de
  Sprint — só `/qualifying`.
- **`results/<round>.json`:** além de `race`+`order` (o que a Etapa 1 usa),
  grava metadados `race_id`, `season`, `round`, `circuit` (Etapas 3+ usam).
- **`drivers.json` agora é real** (entry list 2026), não mock. Pilotos reserva
  sem código oficial na Jolpica são ignorados (não inventar código). O mock de
  Silverstone (Etapa 1) segue passando porque todos os códigos que usa estão na
  entry list real. Obs.: uma rodada pode ter menos de 20 pilotos no quali (ex.:
  a rodada 1/Melbourne teve 19); `order` grava o grid como veio.
- **Resolução por palavras:** `resolve_race` (em `bolao/calendar.py`) casa o
  nome bruto com a corrida por **palavras em comum** com os aliases (não por
  igualdade exata) — vence quem tem mais palavras casadas. Assim, corridas no
  mesmo país se distinguem só acrescentando a cidade no cabeçalho (ex.: "Espanha
  Madrid" → r14; "Spain Barcelona" → r7; "USA Las Vegas" → r20). Só o país
  (ex.: "Spain", "USA") dá empate → `AmbiguousRace` (colocar as duas
  informações); nome desconhecido → `RaceNotFound`.
- **Indisponível:** quali sem resultado na Jolpica levanta `ResultUnavailable`
  (CLI retorna código 2, **não grava arquivo**) — pode re-rodar depois.

### Etapa 3 — Geração dos dados do site ✅
- **Objetivo:** consolidar as pontuações por rodada no ranking da temporada e
  nos dados de palpites por jogador.
- **Saídas:** `standings.json` + JSONs de palpites em `docs/data/`.
- **Pronto quando:** os JSONs do site refletem corretamente várias rodadas
  acumuladas.
- **Depende de:** Etapas 1 e 2.
- **Entregue:** `bolao/site.py` (consolidação + CLI). Entrada: os textos brutos
  do WhatsApp em `data/2026/messages/<round>.txt` (as 9 rodadas reais de 2026 já
  transcritas). Gera `data/2026/scores/<round>.json` (intermediário) e os dados
  do site em `docs/data/`. CLI: `python -m bolao.site build`
  (`--season`, `--data`, `--docs`). Testes offline: `tests/test_site.py`
  (acúmulo de várias rodadas, rodada sem resultado ignorada, ordenação, nome de
  exibição, pontuação mínima/compensação) + casos novos em `tests/test_parser.py`
  — total do projeto: **53**.

**Formatos novos definidos aqui (a Etapa 4 consome estes; não reabrir):**
- **`messages/<round>.txt`:** texto bruto do WhatsApp, um arquivo por rodada. O
  nome do arquivo é a rodada; a Etapa 3 confere batendo com `resolve_race` do
  cabeçalho. Uma rodada só entra na consolidação se tiver **messages + results**.
- **`scores/<round>.json`:** `{round, race_id, season?, race, circuit, date,
  sprint, bonus_driver, result_order:[...], players:[{player_id, player_raw,
  name, top6:[6], top6_detail:[{pos,guess,real,points,reason}], top6_points,
  bonus_guess, bonus_real_pos, bonus_points, total}]}`. Jogadores ordenados por
  total desc, `player_id` asc. **Não inclui compensação** (ver abaixo) — é a
  pontuação bruta de quem apostou naquela rodada.
- **`docs/data/standings.json`:** `{season, rounds:[{round, race_id, race,
  circuit, date, sprint, bonus_driver, min_score}], players:[{position,
  player_id, name, total, top6_total, bonus_total, rounds_played, avg_points,
  per_round:{"<round>":pts}, compensated_rounds:[...], compensation_total}]}`.
  Ordenado por total desc, `player_id` asc (desempate adiado → ordem estável).
  `min_score` = pontuação mínima da rodada (1 a menos que a menor pontuação de
  quem apostou nela). `total`/`compensation_total` já incluem a compensação de
  rodadas não apostadas; `rounds_played`/`per_round` continuam refletindo só as
  rodadas realmente apostadas (compensação não conta como rodada apostada).
  `avg_points` = `(top6_total + bonus_total) / rounds_played` arredondado a 1
  casa decimal (0.0 se não apostou em nenhuma rodada) — também não conta
  compensação, só o que foi de fato apostado. `bonus_total` funciona também
  como "quantas vezes acertou o piloto da rodada", já que o bônus vale no
  máximo 1 pt por corrida. Colunas do ranking no site (nessa ordem): jogador,
  pontos (`total`), média por corrida (`avg_points`), pontos extra
  (`bonus_total`), rodadas (`rounds_played`).
- **`docs/data/bets.json`:** `{season, players:{"<id>":{player_id, name,
  rounds:{"<round>":{round, race_id, race, top6:[6], top6_detail:[...],
  top6_points, bonus_driver, bonus_guess, bonus_real_pos, bonus_points,
  total}}}}}`. Chaveado por id (útil p/ o filtro por jogador do site).
- **`docs/data/results.json`:** `{season, rounds:{"<round>":{round, race_id,
  race, circuit, date, sprint, bonus_driver, order:[...]}}}` — grid real por
  rodada (base p/ histórico de posições por piloto).

**Decisões fixadas na Etapa 3 (não reabrir sem o usuário pedir):**
- **Identidade do jogador auto-descoberta** das mensagens: nome novo = jogador
  novo (id pelo fallback = nome normalizado com `_`). Variantes do mesmo nome se
  unem pelos aliases de `players.json`, que é a **correção manual** (ex.: `caio`,
  `caio l`, `caio lopes` → `caio_l`). Nome de exibição: `players.json.names[id]`
  se houver; senão a variante mais completa vista nas mensagens.
- **Parser fortalecido** (mesmo formato de saída Sheet/Bet): tolera cabeçalho
  `Circuito: X`, enfeites na linha do piloto (`escolhido`/`sorteado`/`:`), linha
  em branco logo após o nome do jogador (bloco reconhecido pela linha `P#`) e
  chute até P22. Os 39 testes anteriores seguem passando.
- **Aliases estendidos** (dados, não formato): `drivers.json` ganhou `max`→VER,
  `kimi`→ANT, `russel`→RUS, `l ecole`→LEC; `calendar.json` r3 ganhou o alias PT
  `japao`. Nomes de corrida em PT que diferem do EN podem precisar de alias novo
  no `calendar.json` conforme surgirem no cabeçalho.
- **Pontuação mínima/compensação** (ver seção 2): "jogador do ranking" =
  qualquer `player_id` que apareça em pelo menos uma rodada consolidada da
  temporada (`ranking_players` em `generate()`), calculado **depois** de
  processar todas as rodadas — por isso a compensação vale até para rodadas
  **anteriores** à estreia do jogador. `min_score` de uma rodada é calculado
  sobre quem apostou nela; se ninguém apostou, `min_score = 0` (caso que não
  deve ocorrer na prática, já que a rodada só entra com `messages/<round>.txt`).
- **Sem timestamp** nos JSONs gerados (saída determinística → diffs limpos e
  testes estáveis).

### Etapa 4 — Site estático ✅
- **Objetivo:** `docs/index.html` que lê os JSONs e mostra **ranking da
  temporada** + **palpites por jogador (com filtro)**.
- **Pronto quando:** abre no navegador (e no GitHub Pages) mostrando ranking e
  filtro funcionando.
- **Depende de:** Etapa 3 (formato dos JSONs).
- **Entregue:** `docs/index.html` + `docs/style.css` + `docs/app.js` (vanilla
  JS, sem build, sem dependências). Fetch relativo (`./data/...json`) — testar
  local com `python -m http.server` a partir de `docs/` (não abrir via
  `file://`). Duas abas: **Ranking** (tabela: posição, jogador, pontos,
  rodadas apostadas; nota de compensação quando houver) e **Palpites por
  jogador** (seletor de jogador; lista todas as rodadas da temporada como
  cards empilhados — top6 apostado vs. grid real por posição com badge de
  pontos 2/1/0 colorido, linha do piloto-bônus com chute/real/pontos, total da
  rodada). Rodadas em que o jogador não apostou (presentes em
  `compensated_rounds` do `standings.json`) aparecem como card "não apostou"
  com a pontuação de compensação (`min_score` da rodada). Códigos de piloto
  exibidos com um círculo de cor por equipe (mapa fixo `CORES_PILOTO` em
  `app.js`, decorativo — não vem dos dados). Tema claro/escuro via
  `prefers-color-scheme`, layout responsivo (mobile-first, cards).

**Decisões fixadas na Etapa 4 (não reabrir sem o usuário pedir):**
- Consumido **sem alterações** o formato atual de `docs/data/*.json` (inclui
  os campos de compensação `compensated_rounds`/`compensation_total`/
  `min_score` já entregues na Etapa 3).
- Cores de equipe são só estética do front-end (não um dado do projeto);
  ficam hardcoded em `docs/app.js`, mapeadas por código de piloto (2 pilotos
  por equipe, grid 2026 com 11 equipes).

**Ajuste posterior (ainda Etapa 4): regras de pontuação + sub-abas em
Palpites por jogador.**
- Aba **Ranking** ganhou um bloco `.regras-pontuacao` (HTML estático, sem
  JS/dado) logo abaixo da tabela, resumindo a seção 2 deste documento.
- Aba **Palpites por jogador** virou um `nav.subabas` com 3 sub-abas
  (`button.subaba[data-subaba="historico|temporada|preferencia"]` +
  `#subsecao-historico|temporada|preferencia`), no mesmo padrão
  `id`/`data-*` das abas principais. `configurarSubAbas()` em `app.js`
  replica a lógica de `configurarAbas()`.
  - **Histórico** = a visão de palpites por jogador já existente (sem
    mudança de comportamento).
  - **Temporada**: **dois** gráficos de linha empilhados via **Chart.js 4
    (CDN, `<script>` em `index.html`)** — exceção pontual à decisão de
    "zero dependências" da Etapa 4, pedida explicitamente pelo usuário.
    Em cima, **pontuação acumulada** (`#temporada-grafico-acumulado`); embaixo,
    **pontuação por corrida sem acumular** (`#temporada-grafico`, o
    original). Os dois compartilham os mesmos mini cards de jogador
    (`#temporada-cards`, um por jogador, todos ligados por padrão) —
    clicar num card liga/desliga a linha daquele jogador **nos dois
    gráficos ao mesmo tempo** (`renderTemporada` em `app.js` monta ambos
    os `Chart` a partir de `construirDadosTemporada`/
    `construirSerieJogador`, que gera os dois datasets — acumulado e por
    rodada — a partir da mesma série de pontos por jogador, então o
    toggle seta `hidden` nos dois `chart.data.datasets[indice]` e chama
    `update()` nos dois). Cor cíclica por jogador em `PALETA_JOGADOR`
    (`app.js`, decorativa, sem relação com equipes). Rodada em que o
    jogador não apostou usa o `min_score` da rodada (via
    `compensated_rounds`/`standings.rounds`) e é destacada nos dois
    gráficos com marcador triangular + segmento tracejado
    (`segment.borderDash`), com nota "mínima — não apostou" no tooltip;
    no gráfico acumulado o `min_score` também entra na soma corrida a
    corrida (mesmo cálculo de `total` do `standings.json`). Fonte de
    dados: só `standings.json` (`per_round`, `compensated_rounds`,
    `rounds[].min_score`) — nenhuma mudança em `bolao/site.py`.
  - **Importante (bug de layout já corrigido):** os dois gráficos da
    Temporada só são criados (`new Chart(...)`) na **primeira vez** que a
    sub-aba fica visível (`garantirGraficosTemporada()`, chamada tanto no
    clique da aba principal quanto da sub-aba) — Chart.js, ao ser
    inicializado num `<canvas>` ainda `hidden` (0×0), trava nesse tamanho
    e **não recupera** com `resize()` depois. Por isso `main()` não
    renderiza mais a Temporada de cara; só guarda `standingsParaTemporada`
    e o primeiro `renderTemporada()` roda sob demanda, com o container já
    visível (`.temporada-grafico-canvas` tem `height: 260px` fixo em
    `style.css`, para o container ter altura mesmo antes do Chart.js
    medir). Se essa sub-aba ganhar mais gráficos no futuro, seguir o
    mesmo padrão de inicialização preguiçosa.
  - **Preferência piloto**: tabela (não gráfico) com a posição média de
    aposta de cada piloto no top6, calculada só a partir de `bets.json`
    (`top6` array, índice 0 = P1). Filtro "Jogador" com opção "Todos"
    (padrão) = **uma média única sobre todos os palpites de todos os
    jogadores juntos** (não é média das médias por jogador). Só lista
    pilotos que já apareceram em algum top6 apostado (do filtro ativo).
    Ordenada por média crescente.
  - Nenhuma mudança nos geradores Python nem nos formatos de
    `docs/data/*.json` — tudo consumido como já estava.

**Mapa do front-end (para ajustes futuros de HTML/CSS/JS sem reler tudo):**
- `docs/index.html`: esqueleto fixo — `header.topo` com as 2 abas
  (`button.aba[data-aba="ranking|palpites"]`), `#secao-ranking` (contém
  `#ranking-status` + `#ranking-container`) e `#secao-palpites` (contém
  `#select-jogador` + `#palpites-status` + `#palpites-container`). Novas
  seções/abas devem seguir esse mesmo padrão `id`/`data-aba`.
- `docs/app.js` (funções puras, sem framework):
  - `CORES_PILOTO` — mapa código→hex de cor de equipe (editar aqui para
    trocar cores/adicionar piloto novo).
  - `carregarJson(caminho)` — fetch genérico dos JSONs em `docs/data/`.
  - `el(tag, props, filhos)` — helper de criação de DOM (evita template
    strings/innerHTML solto).
  - `chipPiloto`, `badgePonto` — átomos visuais reutilizados nas duas abas.
  - `renderRanking(standings)` — monta `#ranking-container`.
  - `popularSelectJogadores(bets)`, `cardTop6`, `linhaBonus`, `cardRodada`,
    `cardSemPalpite`, `renderPalpitesJogador` — pipeline da aba de palpites.
  - `configurarAbas()` — alterna `hidden`/`aria-selected` entre as seções.
  - `main()` — ponto de entrada: carrega `standings.json` e `bets.json`,
    popula a UI; **não usa `results.json` ainda** (grid completo da rodada
    fica disponível para uma visão futura, ex. pódio ou grid inteiro).
- `docs/style.css`: variáveis de tema em `:root` (claro) e
  `@media (prefers-color-scheme: dark)` (escuro) — `--bg`, `--bg-card`,
  `--texto`, `--texto-fraco`, `--borda`, `--acento`, `--ok2`/`--ok2-bg`
  (2 pts), `--ok1`/`--ok1-bg` (1 pt), `--ok0-bg`/`--ok0-texto` (0 pt),
  `--sombra`. Trocar uma cor de status = editar só a variável, não procurar
  por classes espalhadas. Breakpoint mobile único em `max-width: 480px`.
- **Preview local:** `.claude/launch.json` define o server `docs-static`
  (`python -m http.server 8123 --directory docs`) — usar a tool de preview
  com esse nome em vez de subir servidor manualmente.
- Ajustes futuros de **conteúdo/dado exibido** (ex. novo campo, nova métrica)
  quase sempre exigem tocar `docs/app.js` (o que é lido/renderizado) e às
  vezes `bolao/site.py` (o que é gerado) — checar se o dado já existe em
  `docs/data/*.json` antes de assumir que precisa mudar o gerador.

**Ajuste posterior (ainda Etapa 4): aba "Hall of Fame" (vencedores de
temporadas anteriores, 2021–2025).**
- **Não é a Etapa 7** (histórico completo de apostas/corridas — segue adiada).
  É só uma aba simples e estática com quem ficou em 1º/2º/3º em cada temporada
  passada, pedida pelo usuário fora da ordem das etapas.
- **Dado novo, sem gerador Python:** `docs/data/hall_of_fame.json`, escrito à
  mão (`{"anos":[{"ano","ouro","prata","bronze"}], "nomes":{"<id>":"<nome>"}}`,
  `id` reaproveita os ids de `players.json` quando o jogador segue ativo em
  2026; jogador antigo sem id atual ganha um novo, ex.: `"arthur"`).
- **3ª aba principal** `data-aba="hall"` em `docs/index.html`
  (`#secao-hall` → `#hall-status` + `#hall-container`), ao lado de
  Ranking/Palpites — segue o mesmo padrão de `configurarAbas()`.
- **`docs/app.js`:** `renderHallOfFame(hof)` monta duas colunas
  (`.hall-grid`) — esquerda `renderRankingHall` (tabela ordenada por
  🥇 desc, 🥈 desc, 🥉 desc, calculada em JS a partir de `hof.anos`, não
  hardcoded) e direita `renderListaAnosHall` (lista por ano, mais recente
  primeiro, 🥇🥈🥉 + nome). Carregado em `main()` junto dos outros JSONs.
- **`docs/style.css`:** bloco `/* Hall of Fame */` (`.hall-grid` 2 colunas
  → 1 coluna em `max-width: 480px`, reaproveita variáveis de tema
  existentes).

### Etapa 5 — GitHub Actions ✅
- **Objetivo:** workflow acionado por `repository_dispatch` que roda o pipeline
  completo (parse → buscar resultado → pontuar → gerar dados → commit).
- **Pronto quando:** disparar o evento atualiza o site sozinho.
- **Depende de:** Etapas 1–4.
- **Entregue:** `bolao/pipeline.py` (`run`/`retry` + CLI) e
  `.github/workflows/pipeline.yml`. Testes offline em `tests/test_pipeline.py`
  (mock de `fetch_result`, sem rede) — total do projeto: **61**. Repositório
  remoto criado (`gfvdata-web/page-bolao-formula1`, público), primeiro `push`
  feito, Pages ativado. **Validado de ponta a ponta em produção**: disparo real
  de `repository_dispatch` (evento `novo_palpite`, com e sem `round` explícito
  no `client_payload`) e de `workflow_dispatch` (`retry`) na rodada 9
  (idempotente — resultado já existia, "Nada para commitar", sem push
  indevido); confirmado também que a rodada é resolvida corretamente pelo
  cabeçalho quando `round` é omitido. Site publicado e no ar em
  `https://gfvdata-web.github.io/page-bolao-formula1/` (conferido via fetch,
  mostra ranking/palpites/regras corretamente).

**Decisões fixadas na Etapa 5 (não reabrir sem o usuário pedir):**
- **Repositório remoto:** `https://github.com/gfvdata-web/page-bolao-formula1`,
  **público** (necessário para GitHub Pages gratuito em conta pessoal).
- **Pages:** a partir da pasta `docs/` na branch `main` (sem Action de deploy
  separada) — ativar isso nas configurações do repo após o primeiro push.
- **Novo módulo `bolao/pipeline.py`** (não altera `bolao/jolpica.py`,
  `bolao/calendar.py`, `bolao/site.py` nem `bolao/parser.py` — só orquestra):
  - `run(texto, round=None, ...)`: grava `messages/<round>.txt`; se `round` for
    omitido, resolve pelo cabeçalho (`parse_sheet` + `resolve_race`); busca o
    resultado na Jolpica só se `results/<round>.json` ainda não existir;
    **não falha** se `ResultUnavailable` (grava a mensagem, pula o resultado,
    `site.generate` simplesmente não consolida a rodada ainda); sempre roda
    `site.generate` no final.
  - `retry(round, ...)`: para re-disparo manual quando o quali ainda não tinha
    resultado — exige que `messages/<round>.txt` já exista; busca o resultado
    (se faltando) e regenera o site. Levanta `FileNotFoundError` se a rodada
    nunca recebeu mensagem.
  - CLI: `python -m bolao.pipeline run [--round N] [--texto-file F]` (lê stdin
    se `--texto-file` omitido) e `python -m bolao.pipeline retry <round>`.
- **Workflow `.github/workflows/pipeline.yml`:**
  - Gatilho 1 — `repository_dispatch`, evento **`novo_palpite`**,
    `client_payload: {texto: <bloco colado do WhatsApp, obrigatório>, round:
    <int, opcional — se omitido, o pipeline resolve pelo cabeçalho>}`. Chama
    `bolao.pipeline run`.
  - Gatilho 2 — `workflow_dispatch` com input `round` (obrigatório): re-tenta
    buscar resultado de uma rodada cuja mensagem já foi gravada (equivalente ao
    "re-disparo" citado na seção 5). Chama `bolao.pipeline retry`.
  - Ambos os gatilhos terminam com um passo que `git add data docs/data`,
    commita (só se houver mudanças) e dá `push`.
  - **Commit automático como `github-actions[bot]`** (usa o `GITHUB_TOKEN`
    padrão da Action, sem PAT/secret extra) — não conta como contribuição na
    conta pessoal, mas deixa claro o que foi automático vs. manual.
  - Sem `requirements.txt` (projeto usa só stdlib) — o workflow só precisa de
    `actions/setup-python`, sem passo de `pip install`.

### Etapa 6 — Google Forms + Apps Script ✅
- **Objetivo:** formulário no celular + Apps Script que dispara o
  `repository_dispatch` com o texto colado e a corrida.
- **Pronto quando:** enviar o formulário pelo celular atualiza o site
  ponta-a-ponta.
- **Depende de:** Etapa 5 (nome do evento e formato do payload).
- **Entregue:** `google-apps-script/Code.gs` (função `onFormSubmit` +
  `dispararRepositoryDispatch` + `notificarErro` + `testarDisparoManual`) e
  `google-apps-script/SETUP.md` (passo a passo completo: gerar o token,
  criar o Forms, vincular o Apps Script, configurar propriedades/gatilho,
  testar). Setup manual executado na conta Google real (token fine-grained
  gerado, Forms criado, Apps Script vinculado, propriedades e gatilho
  configurados). **Validado via `testarDisparoManual`**: disparo real de
  `repository_dispatch` confirmado na aba Actions do repositório (run
  iniciado corretamente pelo evento `novo_palpite`).
- **Pendência de validação (não bloqueia a etapa):** o gatilho instalável
  `onFormSubmit` (envio real pelo Google Forms, em vez do teste manual)
  ainda não foi exercitado ponta a ponta — combinado com o usuário testar
  isso no envio de palpites da próxima corrida real. Se falhar nesse
  primeiro uso real, o mais provável é os títulos das perguntas do Forms
  não baterem com `PERGUNTA_RODADA`/`PERGUNTA_TEXTO` em `Code.gs`, ou o
  gatilho ter sido criado sem a autorização completa (ver "Solução de
  problemas" em `SETUP.md`).

**Decisões fixadas na Etapa 6 (não reabrir sem o usuário pedir):**
- **Autenticação:** fine-grained PAT do GitHub (repo único
  `page-bolao-formula1`, permissão `Contents: Read and write`, expiração de
  366 dias), guardado em `PropertiesService` (Propriedades do script) do
  Apps Script — nunca no código-fonte nem no repositório. Lembrete de
  renovação agendado para 2027-06-25 (a própria GitHub também avisa por
  e-mail antes de expirar).
- **Campo "Rodada" do Forms:** resposta curta, **opcional** — texto livre
  ou vazio; o pipeline já resolve a rodada pelo cabeçalho da mensagem
  quando `round` vem omitido (decisão da Etapa 5).
- **Campo do texto:** um único campo "Parágrafo", obrigatório, com o bloco
  inteiro colado do WhatsApp — vai direto para `client_payload.texto`.
- **Títulos das perguntas no Forms devem bater exatamente** com
  `PERGUNTA_RODADA`/`PERGUNTA_TEXTO` no topo de `Code.gs` (`"Rodada
  (opcional)"` e `"Texto colado do WhatsApp"`).
- **Falha ao disparar:** `notificarErro` manda e-mail (via `MailApp`) para
  `ALERTA_EMAIL` (propriedade opcional) ou, na ausência, para o e-mail
  efetivo do dono do script — inclui o erro e a orientação de reenviar o
  Forms ou usar `workflow_dispatch` (retry) manualmente.
- Nenhuma mudança no pipeline Python, no workflow do Actions nem no
  front-end — a Etapa 6 só adiciona `google-apps-script/` como novo
  disparador do evento `novo_palpite` já existente.

### Etapa 7 — Histórico ⬜
- **Objetivo:** importar temporadas anteriores para o site.
- **Depende de:** Etapas 1–4; formato dos dados antigos a definir. **Adiada.**

## 9. Pendências / decisões adiadas

- Formato e importação dos **históricos** de anos anteriores.
- Critério de **desempate** no ranking.
- **Estatísticas** extras do site (backlog do item 7).

## 10. Setup

- ✅ Repositório Git **inicializado** com `.gitignore` (Python) e commit inicial.
  Fluxo de Git obrigatório descrito no `CLAUDE.md` — commits pequenos e
  frequentes, status atualizado no mesmo commit, sem `push` até a Etapa 5.
- ✅ Remote no GitHub **criado e publicado** (`origin` →
  `https://github.com/gfvdata-web/page-bolao-formula1`, público, via `gh repo
  create`). Pages ativo (`docs/` na branch `main`):
  `https://gfvdata-web.github.io/page-bolao-formula1/`.
- ✅ Conta/projeto do Google para o Forms + Apps Script (Etapa 6) — Forms +
  Apps Script criados e configurados, código em `google-apps-script/`.
- ✅ Token/permissão para o Apps Script disparar o `repository_dispatch`
  (Etapa 6) — fine-grained PAT gerado e configurado; renovação em ~1 ano
  (lembrete agendado para 2027-06-25).
