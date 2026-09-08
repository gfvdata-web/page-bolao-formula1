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

**Ajuste posterior (ainda Etapa 4): sub-abas "Geral"/"Corridas" no Ranking, com
cards de última/próxima corrida.**
- **Dado novo (pequena extensão da Etapa 2):** `calendar.json` ganhou o campo
  `"qualifying_utc"` (ISO 8601 em UTC, ex. `"2026-07-18T14:00:00Z"`), vindo do
  bloco `Qualifying.date`/`Qualifying.time` que a Jolpica já retorna por
  rodada (`bolao/jolpica.py: build_calendar`); `None` se a Jolpica ainda não
  divulgou o horário do quali daquela rodada. `data/2026/calendar.json` foi
  **re-baixado da Jolpica** para preencher esse campo em todas as rodadas
  (o alias manual `"japao"` da rodada 3, ver Etapa 3, foi reaplicado depois —
  cuidado ao rodar `python -m bolao.jolpica calendar` de novo: ele sobrescreve
  aliases manuais, que precisam ser reaplicados).
- **Novo arquivo `docs/data/calendar.json`:** cópia enxuta do calendário
  completo da temporada (`round`, `race_id`, `race`, `circuit`, `date`,
  `qualifying_utc`, `sprint` por corrida), gerada por `bolao/site.py:generate`
  a partir de `data/<season>/calendar.json` — sem gerador Python novo, só mais
  uma saída de `generate()`.
- **Ranking virou sub-abas** (`button.subaba[data-subaba="geral|corridas"]`
  dentro de `#secao-ranking`, mesmo padrão de `id`/`data-*` das sub-abas de
  Palpites):
  - **Geral** = dois cards pequenos informativos (`#corridas-cards` →
    `renderCorridas` em `app.js`) **acima** da tabela de ranking + regras de
    pontuação (sem mudança na tabela/regras em si). Card 1 = última rodada em
    `standings.json.rounds` (maior `round`, é sempre a última consolidada).
    Card 2 = a rodada de menor `round` do `calendar.json` que **ainda não**
    aparece em `standings.json.rounds` (não depende da data do navegador) —
    mostra local + horário do quali convertido para **America/Sao_Paulo** via
    `Intl.DateTimeFormat` (`formatarQualiBrasilia`), com nota "prazo para
    apostar"; se `qualifying_utc` for `null`, mostra "Data do quali ainda não
    divulgada".
  - **Corridas** = tabela matriz (`#corridas-tabela-container` →
    `renderTabelaCorridas` em `app.js`): uma linha por jogador (mesma ordem de
    `standings.json.players`), uma coluna por rodada (`R{round}` + nome da
    corrida no cabeçalho) mostrando os pontos daquela rodada
    (`per_round[round]`), coluna `Total` no fim. Rodada compensada (jogador
    não apostou) mostra o `min_score` em itálico/estilo apagado
    (`.corridas-tabela__compensado`) em vez do valor de `per_round`. Sem
    filtro/seleção — a tabela inteira é sempre exibida (rola horizontalmente
    em telas pequenas, `overflow-x: auto` no container).
- **Como a Ranking e a Palpites agora têm sub-abas com a mesma classe
  `button.subaba`**, `configurarSubAbas()` (Palpites) e a nova
  `configurarSubAbasRanking()` escopam a busca a `#secao-palpites`/
  `#secao-ranking` respectivamente (`querySelectorAll` com prefixo do `id` da
  seção) — não usar `document.querySelectorAll("button.subaba")` sem escopo se
  uma 3ª aba principal ganhar sub-abas no futuro.
- Nenhuma mudança em `bets.json`/`results.json`/`hall_of_fame.json` nem nos
  formatos já consumidos por eles.

**Ajuste posterior (ainda Etapa 4): gráficos da Temporada movidos para
Ranking/Corridas; sub-aba "Temporada" removida.**
- Os dois gráficos de linha (`#temporada-grafico-acumulado`,
  `#temporada-grafico`) e os mini cards de filtro por jogador
  (`#temporada-cards`) saíram da sub-aba **Temporada** (que deixou de existir,
  junto com `#subsecao-temporada`) e foram para dentro de
  `#subsecao-ranking-corridas`, **acima** da tabela matriz
  (`#corridas-tabela-container`). Aba **Palpites por jogador** agora só tem 2
  sub-abas: `historico|preferencia`.
- IDs/funções internos (`temporada-cards`, `renderTemporada`,
  `construirDadosTemporada`, `garantirGraficosTemporada`,
  `standingsParaTemporada` etc.) **não foram renomeados** — só o HTML em volta
  mudou de seção. Não estranhar o prefixo "temporada" em código que hoje vive
  em Ranking/Corridas.
- O gatilho da inicialização preguiçosa dos gráficos (ver bug de layout do
  Chart.js explicado acima) mudou de lugar: `garantirGraficosTemporada()`
  agora é chamado ao clicar na sub-aba **Corridas** do Ranking
  (`configurarSubAbasRanking()`) e ao clicar na aba principal **Ranking**
  enquanto a sub-aba **Corridas** já estiver ativa (`configurarAbas()`) — o
  equivalente do que antes disparava em Palpites/Temporada.
  `standingsParaTemporada` também passou a ser preenchida logo após carregar
  `standings.json` em `main()` (antes só era preenchida no fim, depois de
  `bets.json`/`results.json`), já que agora pode ser necessária mais cedo (o
  Ranking é a aba padrão ao abrir o site).

**Mapa do front-end (desatualizado nos detalhes — ver também Hall of Fame e
sub-abas Ranking/Corridas acima; mantido como visão geral inicial):**
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

**Ajuste posterior (ainda Etapa 4): card "Pontuação da corrida" na sub-aba
Geral do Ranking.**
- Fica em `#subsecao-ranking-geral`, **abaixo** da tabela de ranking
  (`#ranking-container`) e **acima** do bloco de regras (`.regras-pontuacao`):
  `.corrida-detalhe-card` com um `<select id="select-corrida-detalhe">`
  (filtro de rodada — **sempre uma rodada específica, sem opção "todos"**,
  por padrão a última consolidada em `standings.json.rounds`) e uma tabela
  matriz (`#corrida-detalhe-tabela-wrap` → `renderCorridaDetalhe` em
  `app.js`): linhas P1–P6 + linha "Piloto" (bônus), colunas Pos/Resultado +
  uma por jogador (nome abreviado ao primeiro nome no cabeçalho, nome
  completo no `title` do `<th>`), célula = `chipPiloto` do palpite +
  `badgePonto` com os pontos daquela posição (`top6_detail[i]` /
  `bonus_guess`+`bonus_points` de `bets.json`); jogador sem palpite na
  rodada mostra "–" (`.corrida-detalhe-vazio`). Coluna "Resultado" vem do
  grid completo em `docs/data/results.json` (`rounds[round].order`, primeiro
  uso desse arquivo no front-end — antes só `standings.json`/`bets.json`
  eram carregados), não de um palpite específico.
- **Cores:** reaproveita a paleta de pontos já existente (`--ok2`/`--ok1`/
  `--ok0-bg`, mesma escala de `badgePonto`) — decisão explícita do usuário
  de **não** introduzir vermelho para 0 pt, para manter uma paleta única de
  "pontos" em todo o site.
- **Tabela larga (muitos jogadores) rola horizontalmente** dentro de
  `.corrida-detalhe-tabela-wrap` (mesmo padrão de `.corridas-tabela`), com
  as duas primeiras colunas (Pos/Resultado) fixas via `position: sticky`
  (`left: 0` / `left: 3.6rem`, largura da 1ª coluna hardcoded em
  `style.css` para bater com o offset da 2ª) — decisão explícita do usuário,
  para poder comparar o resultado real com os palpites mesmo rolando.
- Nenhuma mudança em `bolao/site.py` nem nos formatos de `docs/data/*.json`
  — `results.json` já existia, só passou a ser consumido no front-end.
- **Ajuste posterior:** cabeçalho de cada coluna de jogador ganhou o total de
  pontos da rodada, abaixo do nome (`.corrida-detalhe-th__total`). Mesmo
  cálculo de `renderTabelaCorridas`: `jogador.compensated_rounds.includes(round)
  ? roundInfo.min_score : jogador.per_round[round]` — cobre também quem
  recebeu pontuação mínima por não ter apostado na rodada.
- **Ajuste posterior (bug de cor corrigido):** `badgePonto(pts)` reaproveitava
  `pts` como nível de cor (0/1/2 → cinza/amarelo/verde), o que é certo pro
  top6 (teto 2 pts) mas fazia o piloto da rodada (teto 1 pt) mostrar 1pt em
  amarelo em vez de verde — 1pt já é o máximo ali. `badgePonto` ganhou um 2º
  parâmetro opcional `max`: sem ele, comportamento antigo (`nivel = pts`,
  usado no top6); com `max`, quem bate o teto vira nível verde mesmo que o
  teto seja 1 (`nivel = pts >= max ? 2 : pts > 0 ? 1 : 0`). Todo lugar que
  pontua o piloto da rodada passa `max: 1` — `celBonusPalpite` (card novo) e
  `linhaBonus` (cards de rodada da aba Palpites, que tinha o mesmo bug).
- **Ajuste posterior:** o total de pontos no cabeçalho (`.corrida-detalhe-th__total`)
  virou uma pill própria (fundo `--bg`, borda `--borda`, `border-radius: 999px`,
  espaçamento acima do nome) em vez de texto solto colado no nome — também
  corrige um bug de especificidade CSS em que `.corrida-detalhe-tabela th`
  (maiúsculas) vencia o `text-transform: none` do total, deixando "pts" em
  caixa alta; a regra do total agora é escopada como
  `.corrida-detalhe-tabela th .corrida-detalhe-th__total` para ganhar a
  cascata.
- **Ajuste posterior: coluna "Posição Média REAL" na tabela de Preferência
  piloto** (`renderPreferenciaPiloto`).
  - Nova coluna com a posição média que o piloto **realmente** faz nas
    corridas (`docs/data/results.json`, `rounds[].order`, índice + 1),
    calculada uma única vez a partir de todas as rodadas já disputadas —
    **independe do filtro de jogador** (mesmo valor em "Todos" e em cada
    jogador).
  - **Universo fixo de pilotos:** as linhas da tabela deixaram de vir só do
    filtro ativo — agora são sempre a união de todos os pilotos que já
    apareceram no top6 de **qualquer** jogador (mesmo cálculo do filtro
    "Todos"). Isso garante que os mesmos pilotos apareçam em todos os
    filtros, na mesma "identidade" de linha.
  - Piloto que o jogador do filtro ativo nunca apostou no top6: aparece no
    **fim da lista**, com "-" na Posição média e 0 em "Vezes apostado", mas
    com a Posição Média REAL preenchida normalmente.
  - **Ordenação:** pilotos com aposta no filtro ativo primeiro (por Posição
    média crescente, como antes); pilotos sem aposta depois, entre si por
    Posição Média REAL crescente (decisão do usuário, para ordem estável e
    útil mesmo sem dado de aposta).
  - Nenhuma mudança nos geradores Python nem nos formatos de
    `docs/data/*.json` — `results.json` já existia (já usado no card
    "Pontuação da corrida"), só passou a ser carregado também por
    `renderPreferenciaPiloto` (nova assinatura recebe `results`).
- **Ajuste posterior: sub-aba "Simulador" no Ranking (projeção do fim de
  temporada).**
  - **3ª sub-aba** de `#secao-ranking` (`data-subaba="simulador"`, ao lado de
    Geral/Corridas), mesmo padrão de `configurarSubAbasRanking()`.
  - **Sem cálculo novo no Python** — tudo client-side em `app.js`, a partir de
    `standings.json` (`total`, `avg_points`, `position` de cada jogador) e
    `calendar.json` (total de corridas da temporada). Rodadas restantes =
    corridas do `calendar.json` cujo `round` ainda não está em
    `standings.rounds` (mesmo padrão de `renderCorridas`).
  - **Cards por jogador** (`#simulador-cards` → `cardSimuladorJogador`): um
    slider (`input[type=range]`, 0–13, passo 0.1) inicia na `avg_points` real
    do jogador; arrastar atualiza `simuladorEstado.mediaSimulada` (um `Map`
    em memória, estado só de front-end) e re-renderiza a tabela a cada
    evento `input` (`renderTabelaSimulador`) — daí o efeito dinâmico. Botão
    `↺` por card restaura a média real.
  - **Tabela de projeção** (`#simulador-tabela-container` →
    `renderTabelaSimulador`/`construirProjecoesSimulador`): projeção final =
    `total atual + média simulada × rodadas restantes`; reordenada por
    projeção desc a cada re-render (empate por `player_id` asc, mesmo padrão
    do resto do site). Coluna `Δ posição` compara a posição simulada com a
    posição atual em `standings.players[].position` (badge ▲/▼/`=`,
    `badgeDeltaPosicao`).
  - Nenhuma mudança em `bolao/site.py` nem nos formatos de
    `docs/data/*.json` — consumido como já estava.
  - **Ajuste posterior (correção de matemática pedida pelo usuário):
    "Média simulada" virou duas colunas na tabela — "Média atual" (fixa,
    `avg_points` real) e "Média final"** (ponderada, decisão confirmada com o
    usuário): `mediaFinal = (mediaAtual × rodadasJaRodadas + mediaSimulada ×
    rodadasRestantes) / (rodadasJaRodadas + rodadasRestantes)`, onde
    `rodadasJaRodadas = standings.rounds.length` (progresso da temporada como
    um todo, igual para todos os jogadores — não o `rounds_played` individual
    de cada um, que pode ser menor por causa de rodadas puladas). A coluna
    "Projeção final" (pontos) **não muda** — já usava `total` real + média
    simulada × restantes, que é exata independente dessa ponderação. Estado
    (`simuladorEstado`) ganhou o campo `rodadasJaRodadas`.
  - **Cards compactados para caber em 2 linhas** (`.simulador-card`,
    `.simulador-card__nome`, `.simulador-card__valor` etc. com
    paddings/fontes reduzidos).
  - **Ajuste posterior: sem rolagem horizontal, nº de colunas calculado em
    JS.** A 1ª versão usava `grid-auto-flow: column` + `overflow-x: auto`
    (rolagem lateral); o usuário pediu **sem scroll**, os cards devem só
    encolher. `renderCardsSimulador()` agora calcula
    `colunas = Math.ceil(nº de jogadores / 2)` e seta
    `cardsContainer.style.gridTemplateColumns = "repeat(colunas, minmax(0,
    1fr))"` antes de montar os cards — sempre exatamente 2 linhas
    (`grid-template-rows: repeat(2, auto)`, `grid-auto-flow: row` no CSS),
    qualquer que seja o nº de jogadores; os cards encolhem
    (`minmax(0, 1fr)`) em vez de vazar da tela. Testado com até 20
    jogadores simulados sem quebrar o layout.
  - Slider de cada card **já iniciava exatamente na média atual do jogador**
    desde a versão original (`mediaSimulada` = `Map` inicializado com
    `j.avg_points`) — confirmado que é o comportamento correto (ao abrir a
    página, projeção = mesma média atual até o fim da temporada, `Δ posição`
    = "=" pra todo mundo).
  - **Ajuste posterior: slider trocado por botões −/+ e campo digitável.**
    O `input[type=range]` de cada card virou `input[type=text]`
    (`.simulador-card__input`, `inputmode="decimal"` para teclado numérico no
    celular) ladeado por dois botões (`.simulador-card__passo`, `−`/`+`) que
    somam/subtraem exatamente 0.1 por clique. O valor também pode ser apagado
    e digitado direto (aceita vírgula ou ponto decimal, evento `change` —
    só aplica ao sair do campo, não a cada tecla). Toda entrada passa por
    `clampMedia()` (arredonda a 1 casa, limita a `[0, 13]` — os mesmos
    limites do slider antigo; texto inválido vira `0.0`). Mantém o botão `↺`
    de restaurar a média real.
  - **Ajuste posterior: botão "↺ Restaurar todas as médias"**
    (`#simulador-reset-geral`, no topo da sub-aba, ao lado do texto de
    status) — `resetarTodasSimulacoes()` zera `simuladorEstado.mediaSimulada`
    de todos os jogadores de volta a `avg_points` e re-renderiza cards +
    tabela de uma vez (`renderCardsSimulador()` extraído de `renderSimulador`
    para ser reutilizável nesse reset e na carga inicial).
  - **Ajuste posterior: badge "simulado" no card + botão de reset geral
    menor.** Cada card ganhou um badge (`.simulador-card__badge`, pílula
    colorida com a cor do jogador) ao lado do nome, visível **só quando a
    média simulada do jogador difere da média real** (comparação por
    `toFixed(1)`, mesma precisão do `clampMedia`) — escondido via classe
    `.simulador-card__badge--oculto` (`display: none`), alternada em
    `aplicarValor()` (dentro de `cardSimuladorJogador`) a cada mudança de
    valor. `.simulador-reset-geral` ficou com padding/fonte menores.

- **Ajuste posterior: coluna renomeada + badge de distância na Preferência
  piloto.**
  - "Posição média" → **"Posição média palpite"** (deixa explícito que é a
    média do palpite, para não confundir com a REAL ao lado).
  - Ao lado do valor de posição média palpite (mesma célula), badge cinza
    (`badgeDistanciaReal`/`.distancia-badge`: fundo `var(--bg)`, borda
    `var(--borda)`, texto `var(--texto-fraco)`, sempre cinza independente do
    sinal) com seta + distância até a posição média REAL, no máx. 2 casas
    decimais: `diferenca = mediaPalpite - mediaReal`; seta **▲** quando
    `diferenca >= 0` (palpite "pior", número maior que o real), **▼** quando
    negativa (palpite "melhor" que o real); valor exibido é
    `Math.abs(diferenca)`. Só aparece quando a linha tem palpite (não nas
    linhas "-" de piloto não apostado pelo filtro ativo).

**Ajuste posterior (ainda Etapa 4): leitura rodada a rodada nos gráficos de
Ranking/Corridas.**
- **Tooltip compartilhado:** o `interaction` dos dois gráficos passou de
  `mode: "nearest"` para `mode: "index"` (`intersect: false`, `axis: "x"`) — o
  mouse em qualquer altura da faixa da rodada mostra **todos** os jogadores de
  uma vez, para comparar corrida a corrida.
- Linhas do tooltip ordenadas por posição (`itemSort`) e numeradas
  (`1º  Nome — 87 pts`): no gráfico acumulado a numeração é a **posição no
  ranking da temporada**, com a **variação em relação à rodada anterior**
  (`▲2`/`▼1`/`=`); no gráfico por corrida é a ordem de pontos **daquela
  corrida** (sem Δ). Título do tooltip = `R{round} · {corrida}`. As posições vêm
  de `calcularPosicoesPorRodada` (sobre **todos** os jogadores; critério pontos
  desc + `player_id` asc, igual ao resto do site) — desligar jogadores nos cards
  só omite linhas do tooltip, não renumera.
- **Linha vertical tracejada** na rodada sob o mouse: plugin inline
  `pluginLinhaRodada`, registrado só nesses dois gráficos (`plugins: []` do
  `new Chart`), desenhado em `afterDatasetsDraw` a partir de
  `chart.tooltip.getActiveElements()`.
- **Toggle "Pontos"/"Posição"** no cabeçalho do gráfico acumulado
  (`#temporada-modo-acumulado`, `.temporada-modo__btn[data-modo]`;
  `configurarModoAcumulado`/`aplicarModoAcumulado`): troca o eixo Y entre pontos
  acumulados e **posição no ranking** (eixo invertido, 1º no topo,
  `stepSize: 1`) — é o mesmo gráfico, só o `.data` de cada dataset e
  `options.scales.y` mudam (preserva o `hidden` dos cards de jogador). O `<h3>`
  acompanha (`#temporada-titulo-acumulado`).
- **Padrão = "Posição"** (`modoGraficoAcumulado = "posicao"` em `app.js`; o
  `<button data-modo="posicao">` e o `<h3>` já nascem nesse estado no
  `index.html`). O gráfico abre no modo posição e `renderTemporada` chama
  `aplicarModoAcumulado` na criação; o toggle "Pontos" volta ao eixo de pontos.
- **Cuidado:** os arrays em `chart.data.datasets[i].data` são os mesmos objetos
  de `datasetsAcumulado`, e o toggle os substitui; por isso
  `construirDadosTemporada` guarda cópias (`pontosAcumulados`/`pontosPorRodada`,
  `Map` por `player_id`) — é delas que o tooltip lê os pontos, senão em modo
  "Posição" ele mostraria a posição como se fossem pontos.
- Nenhuma mudança em `bolao/site.py` nem nos formatos de `docs/data/*.json`.

**Ajuste posterior (ainda Etapa 4): sub-aba "Rendimento" em Palpites por
jogador (quanto cada piloto rende para quem aposta nele).**
- **3ª sub-aba** de `#secao-palpites` (`data-subaba="rendimento"` →
  `#subsecao-rendimento`, ao lado de Histórico/Preferência piloto), mesmo
  padrão de `configurarSubAbas()`.
- **Métrica: `pts/aposta`** — para cada piloto, a média de pontos que ele gerou
  nos palpites de top6 em que foi escolhido (`bets.json`, `top6_detail[].guess`
  + `.points`; 2 pt exata / 1 pt dentro do top6 / 0 fora). Máx. 2. O **piloto da
  rodada (bônus) não entra** na conta — ele é definido pela rodada, não é uma
  escolha do jogador (dito na legenda da tabela).
- **Filtro "Jogador" com opção "Todos"** (padrão), igual ao da Preferência
  piloto — `popularSelectPreferencia` virou `popularSelectComTodos(selectId,
  bets)`, usada pelos dois filtros. Só entram os pilotos que o filtro ativo
  realmente apostou (diferente da Preferência piloto, que usa universo fixo:
  rendimento sem aposta não existe).
- **Gráfico** (`#rendimento-grafico`, Chart.js barras horizontais,
  `indexAxis: "y"`, eixo X fixo em 0–2): uma barra por piloto, ordenado por
  `pts/aposta` desc (melhor no topo), colorida pela equipe (`corPiloto`, mesmo
  mapa dos chips). Com um jogador no filtro, entra uma **2ª barra cinza com a
  média geral** daquele piloto (a comparação "esse jogador tira mais ou menos
  desse piloto que a média"). Altura do canvas calculada em JS
  (`linhas × 26px`, ou 34px comparando) — o `height` do
  `.rendimento-grafico-canvas` no CSS é só fallback.
- **Tabela** (`renderTabelaRendimento`): `#`, piloto, `Pts/aposta`, `Pontos`,
  `Apostas`, `2 pt`, `1 pt`, `0 pt`; com jogador no filtro ganha a coluna
  `Média geral` e um `.distancia-badge` (▲/▼, cinza) ao lado do `Pts/aposta`
  com a diferença para a média geral. Rola horizontalmente dentro de
  `.rendimento-tabela-wrap`. O CSS da tabela é o mesmo bloco da
  `.preferencia-tabela` (seletores agrupados em `style.css`).
- **Mesma inicialização preguiçosa dos gráficos da Temporada** (bug do Chart.js
  em canvas escondido): `renderRendimento()` sempre monta a tabela mas só cria o
  `Chart` se a sub-aba estiver visível; `garantirGraficoRendimento()` é chamada
  ao clicar na sub-aba **Rendimento** e ao clicar na aba principal **Palpites**
  com essa sub-aba já ativa (`configurarSubAbas`/`configurarAbas`). Estado em
  `rendimentoEstado = { bets, playerId, linhas }`.
- Nenhuma mudança em `bolao/site.py` nem nos formatos de `docs/data/*.json` —
  `bets.json` já tinha tudo (`top6_detail`).

**Ajuste posterior (ainda Etapa 4): botões "Copiar" no formato clássico do
WhatsApp (Ranking/Geral).**
- **Motivo:** antes da automação, o usuário divulgava ranking e pontuação por
  corrida como texto simples no grupo do WhatsApp, num formato próprio (emojis
  de posição/variação/rotativas). O site ganhou dois botões (`📋 Copiar`) em
  `#subsecao-ranking-geral` que geram esse texto e copiam pro clipboard (sem
  alterar as tabelas já existentes).
- **`bet_order` — novo campo em `standings.json`/`scores/<round>.json`/
  `results.json` (`rounds[]`), gerado por `bolao/site.py: generate`:** lista de
  `player_id` na **ordem real em que os blocos apareceram no texto do
  WhatsApp daquela rodada** (`[bet.player_id for bet in sheet.bets]`, capturada
  **antes** de `score_sheet` reordenar por pontuação total). Campo aditivo, só
  usado pelo botão de pontuação da corrida — não muda nenhum campo existente.
- **Botão "Copiar" do Ranking** (`#btn-copiar-ranking`, ao lado do título
  "Classificação", acima da tabela): gera (`gerarTextoRanking` em `app.js`)
  ```
  Classificação Bolão <season>

  <emoji posição> <nome> 🅿️ <total> <variação> 🔄 <rounds_played> *️⃣ <bonus_total>
  ...
  ```
  um jogador por linha, na ordem já existente de `standings.players` (por
  posição). **Emoji de posição:** 1️⃣.. 🔟 fixos (1º–10º); a partir do 11º,
  concatena os emojis de dígito (ex. 1️⃣1️⃣). **Variação** compara a posição do
  jogador na última rodada consolidada com a rodada anterior — reaproveita
  `construirDadosTemporada`/`posicoesRanking` (o mesmo cálculo já usado nos
  gráficos de Corridas, sem duplicar lógica): `🔼 N`/`🔽 N` (subiu/desceu N
  posições) ou `⏸️` (sem variação); **`🆕`** substitui a variação quando a
  última rodada consolidada é a **primeira rodada em que o jogador tem palpite
  real registrado** (`min(per_round)`) — decisão prática por causa da
  compensação retroativa (ver seção 2: um jogador do ranking recebe pontuação
  mínima desde a rodada 1, mesmo antes de estrear, então "teve posição
  calculada antes" nunca é `null` para comparar — o critério de estreia usa a
  1ª rodada **apostada de fato**, não a 1ª com posição no ranking).
- **Botão "Copiar" da Pontuação da corrida** (`#btn-copiar-corrida`, dentro de
  `.corrida-detalhe-card__header`, ao lado do `<select>` de rodada): gera
  (`gerarTextoCorrida` em `app.js`)
  ```
  Resultado Qualify <race>

  <nome> <pontos>
  ...
  ```
  para a rodada selecionada no `<select>` já existente, na ordem de
  `bet_order` (ordem real de envio, **não** a ordem do ranking). **Só entram
  jogadores que apostaram naquela rodada** (não usa `bet_order` fora, então
  quem recebeu compensação por não apostar fica de fora do texto — decisão
  explícita do usuário, diferente do botão de Ranking que sempre lista todos).
  `race` usa o mesmo campo já exibido em outros lugares do site (nome da
  localidade, ex. `"Melbourne"`, não o nome oficial do GP).
- **`copiarTexto(texto, botao)`** (helper genérico): `navigator.clipboard.
  writeText`, com fallback via `<textarea>` + `document.execCommand("copy")`
  pra contextos sem Clipboard API (ex. alguns webviews no celular); dá feedback
  visual no botão (`✅ Copiado!` por 1.5 s, classe `.btn-copiar--copiado`).
- Nenhuma mudança em `bolao/parser.py`, `bolao/scoring.py` nem nos formatos já
  consumidos — `bet_order` é a única adição, aditiva, em `bolao/site.py`.

**Ajuste posterior (ainda Etapa 4): aba "Pilotos" — violino da posição real de
largada no quali.**
- **4ª aba principal** `data-aba="pilotos"` (`#secao-pilotos` → `#pilotos-status`
  + `#pilotos-container`), no mesmo padrão de `configurarAbas()`.
- **Gráfico de violino horizontal feito à mão em SVG** (sem Chart.js nem lib
  nova): `renderPilotos(results)` em `app.js`, uma linha por piloto, ordenadas
  pela **posição média real crescente**. Fonte: só `docs/data/results.json`
  (`rounds[].order`, índice 0 = P1) — nenhuma mudança em `bolao/site.py`.
  - Contorno = densidade por kernel gaussiano (`densidadeGaussiana`, banda 1.1),
    **normalizado por piloto** (mesma espessura máxima em todos — a dispersão
    aparece pela largura no eixo X). Recortado à janela `[melhor-1.5, pior+1.5]`
    porque a gaussiana nunca zera e o violino viraria um fio até o fim do eixo.
  - Cada quali = um ponto (jitter vertical determinístico); faixa clara à
    esquerda = top6; eixo P1..maior grid visto. **Sem barra de média** (só o
    sombreado + os pontos — pedido do usuário); a média fica só no número à
    direita da linha.
  - Helper novo `svgEl()` (namespace SVG, espelha `el()`). `CORES_PILOTO` ganhou
    `TSU`→Red Bull (Tsunoda entrou na r12; decorativo, como o resto do mapa).
  - **Popup ao passar o mouse numa linha** (`.pilotos-tooltip`, HTML absoluto
    dentro de `#pilotos-container` que tem `position: relative`): mostra a
    contagem por posição do piloto como mini-histograma de barras (mesmo visual
    escuro dos tooltips do Chart.js), + média/mediana/melhor/pior. Alvo = um
    `<rect fill="transparent">` por linha; eventos `pointerenter/move/leave`
    (`ligarTooltip`), então funciona também no toque.
- SVG não sofre o bug de canvas escondido do Chart.js → sem init preguiçosa,
  `renderPilotos` roda direto no `main()`.

**Ajuste posterior (ainda Etapa 4): switch de tema claro/escuro no topo.**
- Segmented switch `#tema-switch` (dois `button.tema-switch__btn`
  `data-tema="light|dark"`, ☀️ Claro / 🌙 Escuro, mesmo visual do
  `.temporada-modo`) no `.topo__linha` do header, à direita do `<h1>`; no
  mobile (`max-width: 480px`) some o rótulo, fica só o ícone. Escolha
  explícita grava `data-theme="light|dark"` no `<html>` + `localStorage["tema"]`;
  sem escolha, segue `prefers-color-scheme` (e acompanha mudança do sistema
  via `matchMedia(...).addEventListener("change")`).
- **CSS:** tokens escuros duplicados em dois seletores —
  `@media (prefers-color-scheme: dark) :root:not([data-theme="light"])` e
  `:root[data-theme="dark"]` (o `:root` base continua sendo o claro). Script
  inline no `<head>` (antes do CSS) aplica o `data-theme` salvo sem flash.
- **`app.js`:** `configurarTema`/`aplicarTema`/`temaEfetivo`/`sincronizarSwitchTema`
  + `rerenderizarGraficos()` — CSS reage sozinho, mas Chart.js e o SVG de
  Pilotos leem a cor na hora do desenho, então a troca destrói/recria os
  gráficos (os de Chart.js só os visíveis; o resto volta pela init preguiçosa).
  `resultsGlobais` guardado no `main()` para o re-render do SVG.

**Ajuste posterior (ainda Etapa 4): sub-aba Histórico repensada — matriz
posição × corrida.**
- O `<select id="select-jogador">` sumiu. A sub-aba Histórico agora abre com um
  **strip de chips** (`#hist-jogadores` → `.hist-jogador-chip[data-player]`,
  `aria-pressed`, bolinha na cor de `corJogador(indice alfabético)`) — clicar
  liga/desliga o jogador da comparação; `histSelecionados` (array, nunca vazio).
- **Tabela matriz** (`#hist-matriz` → `renderHistMatriz`): eixo Y = `P1`–`P6` +
  linha `Piloto` (o palpite do piloto da rodada) + linha `Total` (pontuação da
  rodada); eixo X = todas as rodadas de `standings.rounds`. Cada célula empilha
  uma linha por jogador selecionado (com >1 jogador aparece a bolinha de cor):
  chip do piloto apostado + badge curta `histBadgePonto` (`+2`/`+1`/`0`, mesma
  paleta `.ponto-badge`; piloto da rodada usa `max: 1` → acerto vira verde). A
  linha `Total` usa `rodada.total`; se o jogador não apostou mas é compensado
  (`compensated_rounds`), mostra o `min_score` em itálico/apagado
  (`.hist-cel__total--comp`); senão `—`. 1ª coluna e cabeçalho `sticky`, rola na
  horizontal em `.hist-matriz-wrap`.
- **"Por corrida"** = os cards antigos (`renderPalpitesJogador`, **sem mudança**)
  dentro de um `<details class="hist-porcorrida">` recolhido por padrão; mostra o
  **primeiro** jogador selecionado (nota `#hist-porcorrida__nota` quando há mais
  de um). `renderHistPorCorrida` orquestra os dois.
- `popularSelectJogadores` foi substituída por `popularHistJogadores`. Nenhuma
  mudança em `bolao/site.py` nem nos formatos de `docs/data/*.json` — tudo já
  vinha de `bets.json`/`standings.json`.

**Ajuste posterior (ainda Etapa 4): Preferência piloto ganha intro/legenda;
Rendimento vira switch de modo + chips de jogador.**
- **Preferência piloto:** bloco `.secao-intro` (HTML estático) no topo explicando
  o que a tabela compara, e `.legenda-bloco` (HTML estático, `<h4>` + `<ul>`)
  abaixo da tabela explicando cada coluna e a badge ▲/▼ (▲ = apostado pior do que
  larga = subestimado; ▼ = melhor = superestimado). A `<p class="preferencia-legenda">`
  que era montada em `renderPreferenciaPiloto` saiu (a função só monta a tabela
  agora). Filtro "Jogador" (select) **inalterado**.
- **Rendimento:** os dois selects (`select-rendimento-jogador`,
  `select-rendimento-piloto`) e o `<hr>` sumiram. Agora:
  - `.secao-intro` no topo + **switch `#rendimento-modo`** (`.rendimento-modo__btn`
    `data-modo="piloto|jogador"`) logo abaixo da sub-aba — compacto, centralizado
    (`width: fit-content; margin: 0 auto`), botão ativo com fundo
    `color-mix(--acento 14%, transparent)` + texto `--acento` (nada de fundo
    vermelho sólido). Mostra **um** dos dois gráficos por vez
    (`#rendimento-view-piloto` / `#rendimento-view-jogador`, `hidden` alternado).
  - **Filtro = chips** (`#rendimento-jogadores` → `.rendimento-chip`, agrupado no
    CSS com `.hist-jogador-chip`; var de cor própria `--cor-chip`) + `Todos`/`Limpar`
    (`#rendimento-jogadores-acoes`) + `#rendimento-chips-dica` (texto que muda por
    modo). **O conteúdo da tira muda conforme o modo:** modo "piloto" → chips de
    **jogador** (`rendimentoSelJogadores`); modo "jogador" → chips de **piloto**
    (`rendimentoSelPilotos`, cor da equipe). `popularRendimentoChips()` reconstrói
    a tira no clique do switch. `rendimentoIdsJogadoresAtivos()` /
    `rendimentoCodigosAtivos()` devolvem `"todos"` / `[]` / lista.
  - **Modo "piloto"** (`renderRendimento(ids)`): pool dos jogadores marcados, uma
    barra por piloto (cor da equipe); subconjunto → 2ª barra cinza "Média geral
    (todos)" + coluna "Média geral". Perdeu o filtro por piloto (o recorte é sempre
    jogador).
  - **Modo "jogador"** (`renderRendimentoPorJogador(codigos)`): **todos** os
    jogadores aparecem sempre (uma barra cada, cor do jogador). O filtro escolhe
    **quais pilotos** entram na conta; com subconjunto de pilotos entra a barra/
    coluna cinza "Média geral (todos os pilotos)" = rendimento do jogador somando
    tudo. Jogador sem aposta nos pilotos do filtro aparece com `–`/0 e vai ao fim.
  - `garantirGraficoRendimento`/`rerenderizarGraficos`/`configurarRendimento`
    tratam só o gráfico do modo ativo; trocar de modo destrói o gráfico do modo
    que saiu (evita canvas 0×0 preso do Chart.js). `rendimentoEstado` guarda `ids`;
    `rendimentoPorJogadorEstado` guarda `codigos`.
- Nenhuma mudança em `bolao/site.py` nem nos formatos de `docs/data/*.json`.

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

**Ajuste posterior (ainda Etapa 5): "verificador" — re-tentativa automática
enquanto a Jolpica não publica o quali.**
- **Motivo (falha real da rodada 11, Hungaroring):** o Forms foi enviado ~1h15
  depois do quali, a Jolpica ainda não tinha o resultado, o pipeline gravou só a
  mensagem e a run terminou **verde** — ninguém percebeu que a rodada não tinha
  sido pontuada e o site ficou parado. (Na rodada 10/Spa o sintoma foi outro:
  run **vermelha** por bug de parse. Nos dois casos faltou o pipeline se
  resolver sozinho.)
- **Códigos de saída da CLI `bolao.pipeline`** (mesma convenção do
  `bolao.jolpica`): `0` rodada pontuada · `1` erro real · **`2` mensagem
  gravada mas quali ainda indisponível**. Antes o caso `2` também saía `0`.
- **`--json`** (flag global, antes do subcomando): imprime o resumo no stdout e
  manda o texto legível para o stderr — é como o workflow descobre a rodada
  quando ela foi resolvida pelo cabeçalho.
- **Workflow:** o passo que commita roda **antes** do verificador (a mensagem
  do WhatsApp fica salva na hora, aconteça o que acontecer). Se a CLI saiu `2`,
  o passo *Verificador* entra num laço: dorme `INTERVALO_SEGUNDOS` (1800 = 30
  min), chama `pipeline retry <rodada>` e sai do laço commitando assim que
  conseguir; até `MAX_TENTATIVAS` (10) → **5 h de vigília** dentro da própria
  run disparada pelo Forms (`timeout-minutes: 330`). Esgotou sem resultado →
  `::error::` e job **vermelho de propósito**, para o GitHub mandar e-mail.
- **Por que dentro da run e não um `schedule:` (cron):** cron do GitHub atrasa
  10–30 min, pode pular execução e é **desativado após 60 dias** sem atividade
  no repo. Minutos de Actions são gratuitos em repositório público, então
  dormir dentro do job não custa nada.
- **Scripts novos em `.github/scripts/`** (chamados com `bash script.sh`, sem
  depender de bit de execução, que o Windows não versiona):
  `commit-push.sh` (commit + `git pull --rebase` + push; sai em 0 se não houver
  mudança — usado pelos dois passos) e `registra-estado.sh` (traduz código de
  saída + JSON em `RODADA`/`PENDENTE` no `$GITHUB_ENV`).
- O `workflow_dispatch` (retry manual) continua existindo e **também** liga o
  verificador se ainda estiver cedo demais.
- Testes novos em `tests/test_pipeline.py` (classe `TestPipelineCLI`, cobre os
  códigos 0/1/2 e o `--json`) — total do projeto: **68**.

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
  Apps Script — nunca no código-fonte nem no repositório. **Renovado em
  2026-08-15** (o anterior já tinha expirado — o aviso por e-mail do GitHub
  chegou perto/depois da expiração, não 7 dias antes como esperado); novo
  token válido até **2026-12-31**. Lembrete de renovação agendado para
  2026-12-15 (~2 semanas antes, com folga por não confiar só no aviso do
  GitHub).
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

### Etapa 7 — Histórico 🟡
- **Objetivo:** importar temporadas anteriores para o site.
- **Depende de:** Etapas 1–4; formato dos dados antigos a definir.
- **Em andamento (2026-09-08):** temporadas 2021–2025 importadas, publicadas em
  `docs/data/<ano>/` e acessíveis no site via `?ano=YYYY` (seletor pelo card
  "Pódios por ano" — ver sub-etapa 2026-09-08d). Falta a sinalização por rodada
  das corridas sem palpite (`rounds_sem_palpite` etc.).
- **2026-09-08 (Austin):** palpites da R19/2025 recuperados do grupo e anexados
  aos CSV de 2025; `pontos_avulsos.json` de 2025 removido. 2025 fecha 24/24
  rodadas. Ver "R19 Austin — palpites recuperados" mais abaixo.
- **2026-09-08 (Hall of Fame — switch + colunas):** a aba Hall of Fame agora
  tem um switch **Jogadores / Temporadas** (estilo `.rendimento-modo`). Em
  "Jogadores" o Ranking de vitórias ganhou as colunas **Participações**,
  **Pontos** (somatório de `total` de todas as temporadas) e **Acerto** (% =
  pontos feitos ÷ máximo possível, só nas corridas palpitadas, teto por
  temporada `format.max_points`); o botão Acessar foi para o fim da linha. Em
  "Temporadas" (antigo "Pódios por ano") cada ano mostra a contagem de
  jogadores. Base do cálculo em `universoJogadores()` (`acertoNum/acertoDen`).
- **2026-09-08 (cores por temporada):** em modo histórico as bolinhas/gráficos
  de piloto usam as cores da equipe **daquele ano**, não as de 2026. Novo mapa
  `CORES_PILOTO_ANO` em `docs/app.js` (`{ "2021".."2025": {cod: hex} }`);
  `corPiloto()` consulta `CORES_PILOTO_ANO[TEMPORADA]` quando `MODO_HISTORICO`,
  senão cai em `CORES_PILOTO` (2026) e depois no cinza. Único ponto de troca —
  todos os gráficos passam por `corPiloto()`. Cores decorativas (aproximadas),
  não vêm dos dados. 2026 permanece inalterado.

**Análise do `f12025bolao.xlsx` (fonte dos palpites 2025):**
- **Aba 1 "Página1"** — 138 palpites, colunas `circuito, nome, p1..p6, pos`
  (`pos` = chute da posição do piloto da rodada). Cobre **15 corridas**
  (Austrália → Zandvoort = rodadas 1–15 de 2025). Ordem das linhas = ordem de
  envio (serve de `bet_order`). Sem palpites duplicados (circuito+jogador).
- **Aba 2 "Cópia de Página1"** — 1 linha por corrida, colunas `circuito, data,
  p1..p6 (top6 real do quali PRINCIPAL), pos, quem`. `quem` = piloto da rodada
  (sorteio do grupo, **só existe aqui**, não na Jolpica). Colunas M/N são um
  lookup `circuito→quem` redundante (ignorar). Monza (r16) só tem top6, sem
  `quem`/`pos` e sem palpites → **fora do bolão 2025**.
- **Conferência do top6 da aba 2 = quali principal** (não sprint): validado em
  China/Miami/Spa. A coluna `pos` da aba 2 (posição do piloto da rodada) bate
  com o quali na maioria, mas **diverge em Australia** (`quem=tsu`, aba diz
  `p17`, quali foi P5) — a fonte canônica da posição real será a **Jolpica**
  (`order` do `/qualifying`, mesmo critério de 2026), a aba 2 vira conferência.
- **Erros de digitação no xlsx a tratar:** `austria/Igor` P4 = `LEV` (→ LEC?);
  `jeddah/Guilherme` top6 = `[NOR,PIA,VER,RUS,LEC,VER]` (VER repetido em P3 e
  P6); `jeddah/Guilherme` `pos` = `p4` minúsculo (parser tolera). Códigos de
  piloto vêm em CAIXA/minúscula/Título misturados e `Max`/`Tsu` — o
  `normalize_driver` já resolve (alias + fallback de 3 letras).
- **Jogadores (13 grafias → ~12 pessoas):** acentos/caixa se unem sozinhos
  (`Vinícius`=`vinicius`); **`bernardo` vs `Bernardo Lavôr`** precisa de alias
  (`bernardo lavor`→id). Roster o ano todo: caliman, cintia, dalla, ferrari,
  francez, guilherme, igor, lage, vinicius. Parciais: `arthur` (r2,4,5),
  `bernardo` (r1,2,4,5), `caio` (r15). `cintia`/`bernardo`/`arthur` **não estão**
  em `data/2026/players.json`.

**Decisões da Etapa 7 (fechadas com o usuário em 2026-09-08 — não reabrir):**
- **Identidade de jogador entre temporadas:** reusar o `player_id` de 2026
  quando é a mesma pessoa (`caio`→`caio_l`); ids novos para quem não joga em
  2026 (`cintia`, `bernardo`, `arthur` — este bate com o id do `hall_of_fame`).
- Fonte do resultado do quali 2025 = **Jolpica** (`--season 2025`, grid
  completo); xlsx aba 2 = conferência + piloto da rodada (`quem`).
- `messages/<round>.txt` de 2025 são **sintetizados** do xlsx no formato que
  `bolao/parser.py` já consome → `parser`→`scoring`→`site.generate` rodam **sem
  alteração de lógica**.
- Fonte crua versionada no repo como CSV (`data/2025/palpites_2025.csv`,
  `rodadas_2025.csv`), **sem** dependência de `openpyxl` no projeto/CI.
- **Migração `docs/data/` agora:** 2026 saiu de `docs/data/*.json` para
  `docs/data/2026/*.json`; 2025 em `docs/data/2025/`. O seletor visível de
  temporada é a **sub-etapa seguinte**.

**Entregue nesta sub-etapa (2026-09-08) — base 2025 + geração multi-temporada:**
- **`bolao/site.py`:**
  - `load_driver_aliases(data_dir, season)` — `data/drivers.json` (camada base
    de apelidos manuais: `max`→VER, `kimi`→ANT, typos) + overlay opcional de
    `data/<season>/drivers.json` (entry list real do ano, da Jolpica).
  - `generate()` grava em `docs/data/<season>/` (era `docs/data/`) e escreve
    `docs/data/seasons.json` `{temporadas:[...desc], atual}` varrendo as pastas
    irmãs com `standings.json` (gerar uma temporada não apaga o índice das
    outras). `docs/data/hall_of_fame.json` continua na raiz (comum a todas).
- **`bolao/historico.py` (novo, Etapa 7):** `build(season, data_dir, check_only)`
  + CLI `python -m bolao.historico build --season 2025 [--check-only]`. Lê os
  CSVs + `calendar.json` + `results/<round>.json`, resolve `circuito→rodada` por
  `resolve_race`, sintetiza `data/<season>/messages/<round>.txt` e imprime um
  **relatório de conferência** (top6 planilha × Jolpica; posição real do piloto
  da rodada planilha × Jolpica; código de piloto fora da entry list; top6 com
  piloto repetido; jogador sem alias). Depende de `bolao.site` (Etapa 7 ⊃ 3).
- **`data/2025/`:** `calendar.json`, `drivers.json`, `results/1..15.json` (da
  Jolpica); `players.json`; `palpites_2025.csv` + `rodadas_2025.csv` (do xlsx);
  `messages/1..15.txt` + `scores/1..15.json` (gerados).
- **`docs/app.js`:** `const TEMPORADA = "2026"` + `caminhoDados(nome)` →
  `./data/2026/<nome>.json`. **Cuidado:** já existe `let dadosTemporada` (dados
  dos gráficos da aba Ranking/Corridas) — o helper novo teve que se chamar
  `caminhoDados`. `hall_of_fame.json` continua em `./data/`.
- Testes: `tests/test_historico.py` (4) + ajuste de caminho em
  `test_site.py`/`test_pipeline.py` — total do projeto: **72**.
- **Validado:** site abre com 2025 e 2026 (trocando `TEMPORADA`) sem nenhuma
  mudança nos renderizadores; ranking, cards de corrida, compensação, gráficos.

**Conferência do xlsx 2025 (`python -m bolao.historico build --season 2025`):**
- **Top6 da planilha == Jolpica nas 15 rodadas** (dado limpo).
- 3 avisos: (1) R1/Melbourne — piloto da rodada TSU: planilha diz P17, quali foi
  P5 (usa Jolpica); (2) R5/Jeddah/Guilherme — top6 com `VER` repetido (P3 e P6),
  preservado como veio → P6 conta 0; (3) R11/Áustria/Igor — `LEV` no P4 (typo de
  `LEC`?), preservado → conta 0. **Correções pontuais, se quiseres, editam o
  CSV** e re-rodam `historico build` + `site build`.

**Sub-etapa 2026-09-08c — rodadas 16–24 de 2025 (export do WhatsApp):**
Fonte: `backupguimsgs.txt` (mesmo tipo de export do grupo). Importadas **8
rodadas** (16 Monza, 17 Baku, 18 Singapura, 20 México, 21 Interlagos, 22 Las
Vegas, 23 Qatar, 24 Abu Dhabi) via `bolao.whatsapp_import.consolida_rodadas`
→ linhas anexadas em `data/2025/palpites_2025.csv` / `rodadas_2025.csv` (as
colunas de conferência `pos_planilha,t1..t6` ficam **vazias** nessas rodadas;
`historico.py` passou a tratar coluna vazia como "sem cross-check", não como
divergência). Site vai de 15 → **23/24 rodadas**; ranking final bate com o
`hall_of_fame` (🥇 vinícius 139 · 🥈 guilherme 138 · 🥉 igor 137).
- Correções pontuais na leitura do WhatsApp (typos/emoji que o parser derrubou):
  R21 Lage `ATN`→`ANT` + `P13`; R21 Francez `P 7 😵‍💫`→`P7`; R22 Caio `VES`→`VER`
  (bloco tinha sumido); R24 Francez (bloco com emoji no meio, tinha sumido).
- **Divergências recálculo × placar publicado no grupo** (o recálculo pela
  Jolpica é o que vale nos dados, igual às outras rodadas): R20 México — o grupo
  publicou o placar às pressas 13 dias depois ("não atualizei a pontuação do
  México"), todos ~1–2 pts abaixo do recálculo; R16 Caio (+1); R21 Caliman (o
  grupo somou "+1" à mão).
- **R19 Austin — palpites recuperados em 2026-09-08:** os 8 blocos vieram do
  grupo e foram anexados a `palpites_2025.csv`/`rodadas_2025.csv` (piloto da
  rodada: OCO). `pontos_avulsos.json` de 2025 foi removido; a rodada roda pelo
  pipeline normal (`messages/19.txt` sintetizado). O placar que o grupo publicara
  às pressas **não reconcilia** com o recálculo 2/1/0 — o recálculo prevalece.
  2025 agora é 24/24 rodadas no site.

**Pendências para fechar 2025 (decisão do usuário):**
- ~~**R19 Austin no ranking**~~ — **resolvido em 2026-09-08** (palpites
  recuperados, ver acima).
- ~~**Semântica da compensação retroativa no histórico**~~ — **resolvido em
  2026-09-08**: a compensação **não existia** em 2021–2024 (medido nas
  classificações publicadas, ver "Regras por temporada" abaixo) e foi desligada
  nessas temporadas. **2025 continua com compensação ligada** — a evidência no
  export desta conversa é fraca (3 casos sem ganho contra 1 com) e o pódio de
  2025 bate dos dois jeitos, então a decisão fica com o usuário / com a sessão
  que fechou 2025.

**Sub-etapa 2026-09-08b — histórico 2021–2024 (export do WhatsApp):**

Fonte: backup `.txt` do grupo (48.990 mensagens, 04/2021→09/2026). O arquivo
**não entra no repositório** e os `.txt` derivados vão para `historico_wpp/`
(no `.gitignore`) — decisão de privacidade do usuário. Só os CSV estruturados
(`data/<ano>/palpites_<ano>.csv`, `rodadas_<ano>.csv`) são versionados, no
mesmo formato que 2025 já usa.

**O formato do palpite mudou ao longo dos anos** (`SEASONS` em
`bolao/whatsapp_import.py`) — isso muda a pontuação máxima por corrida:

| Ano  | Top | Piloto da rodada | Máx/corrida |
|------|-----|------------------|-------------|
| 2021 | 5   | não existia      | 10          |
| 2022 | 6   | não existia      | 12          |
| 2023 | 6   | não existia      | 12          |
| 2024 | 6   | sim (desde R1)   | **14** (bônus vale 2) |
| 2025 | 6   | sim              | 13          |

A regra 2/1/0 (exata / dentro do top N real / fora) vale em **todos** os anos —
**validada** contra as pontuações que o próprio grupo publicou: 2021 bate em
65/65 palpites conferidos; 2023 bate exatamente em vários checkpoints
acumulados (r9: 9 de 10 jogadores; r11: 8 de 10 — os que divergem são sempre
quem faltou rodadas, ou seja, compensação).

**Cobertura por temporada** (rodadas com palpite / total):
- **2021: 12/22** (rodadas 11–22, Hungria→Abu Dhabi). As rodadas 1–10 existiram
  no bolão mas **não estão** no WhatsApp — o ranking de 11/12/2021 fecha com
  `Guilherme 111 pts / 22 🏁`. O saldo das rodadas 1–10 só é recuperável pelos
  rankings acumulados (`historico_wpp/classificacoes.txt`).
- **2022: 20/22** (faltam R4 Imola e R5 Miami).
- **2023: 22/22** e **2024: 24/24** — completas.
- **2025:** fora deste import (já vem do xlsx, r1–15). O export do WhatsApp
  **não tem nenhuma mensagem entre 08/2025 e 12/2025**, então as rodadas 16–24
  de 2025 continuam sem fonte.

**Decisões de identidade de jogador (fechadas com o usuário em 2026-09-08):**
- `pedro` (rankings de 2021) = **`francez`** (Pedro Francez).
- `sergio` / `Sergin` = **`lage`** (mesma pessoa; a grafia mudou no meio de 2022
  — nunca aparecem juntos numa mesma mensagem).
- O `Bernardo` dos rankings de 2021 é **Bernardo Viana** (`bernardo_v`), pessoa
  diferente do `Bernardo Lavôr` (`bernardo`) que jogou em 2025.
- `DRU` (2023, Bahrein) apostou uma única vez e foi **removido** dos registros
  a pedido do usuário (2026-09-08d); `Leo`, `Lex`, `Vest`, `MASSA 2008` e
  afins são ruído/piada e são descartados.
- `gui`→`guilherme`, `rod`→`rodrigo`.

**`bolao/whatsapp_import.py` (novo):** lê o export, reconhece blocos
jogador→pilotos por **sequência** (não por texto do nome — resolve `Sergio` e
`Ferrari`, que também são apelidos de piloto), resolve a rodada pela **data**
(±6 dias do quali; 2022 não tinha cabeçalho), consolida o palpite final de cada
corrida (mensagem mais completa + recuperação de quem sumiu da versão final) e
grava `historico_raw.txt`, `palpitesfinais.txt`, `classificacoes.txt` e os CSV.
Apelidos de piloto colhidos do próprio grupo (`vetel`, `sains`, `charlin`,
`rua`, `lindo`, `han`…) ficam em `APELIDOS_COMUNS`/`APELIDOS_POR_ANO`.

Total: **636 palpites** importados (75 + 150 + 182 + 229) com **21 avisos**
(bloco com número de pilotos fora do padrão, piloto repetido, jogador
recuperado de mensagem anterior). **R24 de 2024 (Abu Dhabi) não teve piloto da
rodada** — ninguém mandou `P#` e o cabeçalho não traz o piloto.

**Base 2021–2024 construída (mesma sub-etapa):**

- **`bolao/formats.py` (novo):** `SeasonFormat(top_n, bonus)` + `FORMATS` por
  ano — a única fonte da verdade sobre o formato de cada temporada, usada pelo
  `whatsapp_import`, pelo `parser`, pelo `scoring` (via `parse_sheet`) e pelo
  `historico`.
- **`bolao/parser.py`:** `parse_sheet(..., top_n=6, bonus=True)`. Com
  `bonus=False` os blocos são separados por **linha em branco** (não existe a
  linha `P#` para fechar). `P0` = "não chutou" e `Piloto (nenhum)` = rodada sem
  piloto da rodada (Abu Dhabi 2024 trocou o bônus por "equipe campeã"). Sem
  esses dois marcadores o histórico não passa pelo parser.
- **`bolao/scoring.py`:** a referência do top passou a ser
  `result.order[:len(bet.top6)]` (5 em 2021, 6 no resto) e o bônus é 0 quando
  `bonus_driver` vem vazio. Comportamento de 2025/2026 inalterado.
- **`bolao/site.py`:** lê o formato do ano e, se existir, o
  **`data/<ano>/saldo_inicial.json`** — pontos e rodadas de corridas anteriores
  às que têm palpite. Entram no ranking como `carry_points`/`carry_rounds`
  (bloco sem detalhe por corrida) e o jogador que **só** tem saldo (Bernardo
  Viana, 2021) passa a existir no ranking.
- **`data/2021..2024/`:** `calendar.json`, `drivers.json`, `results/*.json`
  (Jolpica), `players.json`, `palpites_<ano>.csv`, `rodadas_<ano>.csv`,
  `messages/*.txt` e `scores/*.json`. `data/2021/saldo_inicial.json` cobre as
  rodadas 1–10.
- Testes: `tests/test_whatsapp_import.py` (11) + formatos antigos em
  `test_parser.py` (5) — total do projeto: **88**.

**As duas versões do total** (decisão do usuário: gravar as duas) já cabem no
schema do `standings.json`: `total` = com compensação; **bruto** =
`top6_total + bonus_total + carry_points`.

**Conferência do recálculo contra o placar publicado no grupo**
(`historico_wpp/conferencia.txt`, gerado junto com o import):

| Ano  | Confere | O que explica o resto |
|------|---------|-----------------------|
| 2021 | **154/154 (100%)** | nada a explicar: reproduz a temporada inteira, incluindo o pódio do `hall_of_fame` |
| 2023 | 240/262 (92%) | as pontuações **por rodada** batem quase todas (5 linhas de ±1). No acumulado, o único divergente sistemático é o **dalla**, sempre exatamente **+7** — ele não apostou na R1 e o grupo lhe deu 7 pts de compensação daquela rodada |
| 2022 | 146/266 (55%) | 7 das 13 rodadas publicadas batem 100%, o resto por ±1–2. O rombo é todo no acumulado, e é **uniforme (~8 a 16 pts para todos, a partir da R6)**: são as **rodadas 4 (Imola) e 5 (Miami)**, que não existem no export — a média de 2022 é 6,2 pts/palpite, ou seja ~12 pts por jogador |
| 2024 | 109/355 (31%) | ver abaixo |

Ou seja: **2022 e 2023 não têm problema de pontuação** — 2022 tem buraco de
cobertura (2 corridas) e 2023 tem uma compensação que o recálculo não conhece.

**2024 — o piloto da rodada valia 2 pontos** (decidido com o usuário em
2026-09-08, aplicado em `bolao/formats.py`). Prova: na **R2 (Jeddah)** o
sorteado foi o VER, os **10 jogadores cravaram P1** e ele fez a pole — o placar
publicado bate **10/10 com 2 pts e 0/10 com 1 pt**.

**O "+1 por palpitar" de 2024 NÃO é regra oficial** (decidido com o usuário em
2026-09-08 — não reabrir). Nas rodadas 1 a 5 de 2024 o placar publicado dá 1
ponto a mais a cada jogador que mandou um chute do piloto da rodada, mesmo
errando; ajustar o modelo para isso levaria a conferência de 48% para 80% das
linhas. **O usuário não reconhece essa regra**, então ela fica registrada
apenas como observação — provavelmente erro de conta do grupo na época. Os
dados usam a regra oficial: **acerto = 2 pts em 2024, erro = 0**.

| regra do bônus testada | linhas que batem | rodadas exatas |
|------------------------|------------------|----------------|
| acerto 1, erro 0 | 49/114 (43%) | 0/12 |
| acerto 2, erro 0 (**oficial, em uso**) | 55/114 (48%) | 1/12 |
| acerto 2, erro 1 até a R5; depois 1 e 0 (*descartada*) | 91/114 (80%) | 3/12 |

**Correções de atribuição de rodada (2026-09-08):** `resolve_round` ganhou
`passado=True` — mensagem de **pontuação/classificação** só pode falar de
corrida já disputada. Sem isso, os placares do fim de 2024 caíam na corrida
seguinte. E `_dia_quali` passou a usar a **véspera** da corrida quando o
calendário não traz `qualifying_utc` (é o caso de 2021 inteiro na Jolpica) —
essa correção sozinha levou 2021 de 92% para **100%**.

**Regras por temporada (decisão do usuário em 2026-09-08 — não reabrir):** as
regras do bolão mudaram ao longo dos anos e **cada temporada usa as suas**. Uma
regra só entra num ano se o padrão aparecer nas pontuações que o grupo
publicou. Tudo vive em `bolao/formats.py` (`SeasonFormat`).

| ano | top | piloto da rodada | máx | compensação | desempate |
|-----|-----|------------------|-----|-------------|-----------|
| 2021 | 5 | não existia | 10 | **não** | **média** |
| 2022 | 6 | não existia | 12 | **não** | — |
| 2023 | 6 | não existia | 12 | **não** | — |
| 2024 | 6 | sim, vale **2 pts** | 14 | **não** | — |
| 2025 | 6 | sim, 1 pt | 13 | sim | — |
| 2026 | 6 | sim, 1 pt | 13 | sim | — |

**Como a compensação foi medida (não foi arbitrada):** pegando duas
classificações acumuladas publicadas em sequência e olhando o salto de cada
jogador, quem faltou rodada **ficou parado** — 10 casos em 2021, 14 em 2022, 12
em 2023 e 5 em 2024, contra 1, 5, 3 e 1 casos de ganho (esses explicáveis por
rodada ausente na fonte). Eleazar e Luciano faltaram meia temporada de 2023 sem
ganhar nada; Lage faltou a R3 de 2024 e não ganhou nada. Isso também tira do
ranking a distorção do `dru`, que apostou **uma vez** em 2023 e ganhava 62 pts
de compensação.

**Desempate por média só em 2021:** Ferrari e Vinícius fecharam os dois com
**96 pontos** e o grupo pôs o Vinícius em 2º — ele fez 96 em 20 rodadas (4,8)
contra 96 em 22 do Ferrari (4,4). Para 2026 o desempate continua indefinido
(seção 9); o padrão é só a ordem estável por id, que não é critério de verdade.

**Rodadas sem palpite mas com placar (`data/<ano>/pontos_avulsos.json`)** —
decisão do usuário em 2026-09-08: rodada que falta na fonte **não pode custar
pontos**. Quando dá para arbitrar quanto cada jogador fez pela classificação
publicada, o valor é registrado (sem saber de quais pilotos veio), conta no
total e como rodada disputada; o site depois mostra o total completo e
**sinaliza** que ali não há palpite. Só entra no ranking com
`"incluir_no_ranking": true` — a inclusão muda campeonato, então é decisão
explícita, nunca efeito de o arquivo existir.

- **2023 R1** — Dalla `7`. Ele não está no palpite nem no placar da rodada, mas
  a acumulada de 19/03 o traz com 12 e a R2 dele foi 5. Confirmado por
  exclusão: as outras 9 rodadas com placar batem 9/9.
- **2022 R4+R5** — Imola e Miami não existem no export (nem palpite nem
  placar). Só dá para atribuir como **bloco**, do salto entre as acumuladas de
  09/04 e 21/05 menos o placar da R6. Para Igor e Rodrigo o bloco cobre também
  a R6, que eles não jogaram (entrada separada).
- **2025 R19 (Austin)** — **resolvido em 2026-09-08**: os palpites foram
  recuperados (8 jogadores) e anexados a `palpites_2025.csv`/`rodadas_2025.csv`;
  `pontos_avulsos.json` de 2025 foi removido e a rodada agora tem
  `messages/19.txt` como qualquer outra. Recálculo 2/1/0: Dalla 10, Francez 10,
  Vinícius 9, Ferrari 8, Igor 8, Guilherme 7, Lage 7, Caliman 6 (**não
  reconcilia** com o placar que o grupo publicara às pressas: 5/6/6/5/5/6/5/7 —
  o recálculo prevalece, igual às outras rodadas).

**Fechamento do histórico (decisões do usuário em 2026-09-08 — não reabrir):**

1. **O placar publicado no grupo manda**, seja qual for a regra que ele seguiu
   na época. `data/<ano>/placar_publicado.json` (extraído do export por
   `bolao.whatsapp_import`, versionado) tem a pontuação por rodada como o grupo
   divulgou; `bolao.site` usa esse valor e guarda o que a regra da temporada
   daria em `total_recalculado`. Rodada que o grupo não publicou continua vindo
   da recalculação. Quando a mesma rodada tem mais de um placar publicado vale
   o **mais próximo da data do quali** (foi assim que a mensagem de brincadeira
   de 17/10/2021 parou de sobrescrever a Turquia).
2. **`data/<ano>/ranking_final.json`** guarda o fechamento oficial: `ordem`
   fixa a classificação final — inclusive o **desempate, que o grupo resolvia
   por critério interno nunca escrito** — e `pontos`, quando presente,
   substitui o total somado (o somado continua visível em `total_somado`).
3. **Rodada sem palpite conta pelos pontos que dá para inferir** (item 1 acima).
   A R19 de 2025 (Austin) foi assim até 2026-09-08, quando os palpites foram
   recuperados: virou `messages/19.txt` e o bloco avulso saiu (não sobra nenhum
   `pontos_avulsos.json` em 2025).

Onde cada mecanismo foi preciso:

| ano | por quê |
|-----|---------|
| 2021 | desempate por média (Ferrari e Vinícius fecharam os dois com 96) |
| 2022 | bloco avulso R4+R5 + placar publicado + `ordem` (Caliman e Dalla empatam em 139) |
| 2023 | avulso da R1 do Dalla + placar publicado + `ordem` (Igor e Ferrari empatam em 118) |
| 2024 | `pontos` da tabela final: os placares por rodada do grupo **não somam** a tabela final dele (Caliman fecha 148 lá, mas os relatórios por rodada somam 152) — não existe regra por rodada que a reproduza. Arthur e Dalla empatam em 162 e `ordem` dá o título ao Arthur |
| 2025 | com Austin (palpites recuperados) Vinícius fecha 148, Guilherme 145; `ordem` fixa os 4 primeiros (Dalla soma 143, mas o grupo registrou Caliman em 4º) |

**Pódios calculados × `hall_of_fame`: os 5 batem.**

| ano | pódio | pontos |
|-----|-------|--------|
| 2021 | guilherme, vinicius, ferrari | 111, 96, 96 |
| 2022 | caliman, dalla, vinicius | 139, 139, 132 |
| 2023 | dalla, lage, igor | 126, 121, 118 |
| 2024 | arthur, dalla, lage | 162, 162, 150 |
| 2025 | vinicius, guilherme, igor | 144, 144, 143 |

**Publicado:** `docs/data/2021..2026/` + `docs/data/seasons.json` com as seis
temporadas.

**Sub-etapa 2026-09-08d — seletor de temporada no site (modo histórico).**
- **Acesso via `?ano=YYYY`** (recarrega a página; sem SPA). Sem `?ano` → a
  temporada `atual` de `seasons.json` (fixa em `TEMPORADA_ATUAL = 2026` no
  `bolao/site.py`). `?ano` de um ano válido e anterior → **modo histórico**;
  `?ano` inválido → redireciona para a URL limpa.
- **Ponto de entrada:** aba **Hall of Fame → card "Pódios por ano"** ganhou um
  botão **"Acessar"** por temporada (todas as de `seasons.temporadas` menos a
  atual). Não há outro seletor visível por enquanto.
- **Modo histórico (só quando `?ano` ≠ atual):** `<h1>` vira `Bolão F1 <ano>` +
  badge **HISTÓRICO**, botão **"← Voltar para 2026"** (ambos no `<header>`, logo
  visíveis em todas as abas), e uma **faixa `#hist-avisos`** abaixo do header
  listando `seasons.temporadas[].faltando` quando `parcial`. A sub-aba
  **Simulador** some (botão + seção + `renderSimulador` pulado); os cards de
  última/próxima corrida (Ranking/Geral) viram **"Rodadas contabilizadas"** +
  **"Jogadores competindo"**. **2026 fica idêntica ao que era.**
- **Novos campos gerados por `bolao/site.py` (aditivos):**
  - `standings.json` → `format` (`{top_n, bonus, bonus_points, compensation,
    max_points}`, de `season_format()`) e `meta` (`{rodadas, rodadas_totais,
    parcial, faltando}`).
  - `seasons.json` mudou de shape: `{atual, temporadas:[{ano, format,
    rodadas, rodadas_totais, parcial, faltando}]}` (era `{temporadas:[int],
    atual}`). Agregado varrendo os `docs/data/<ano>/standings.json` irmãos.
- **Visualizações adaptativas no `docs/app.js`** — estado global `FORMATO`
  (setado de `standings.format`) e `MODO_HISTORICO`. Onde não há top6 / piloto
  da rodada / compensação, a linha/coluna/bloco **é omitida** (nunca campo
  vazio). Pontos tocados: `renderRanking` (coluna "Pontos Extra"),
  `renderRegras` (novo — remonta `.regras-pontuacao` por temporada),
  `renderCorridaDetalhe` (`slice(0, top_n)` + linha do bônus condicional),
  `renderHistMatriz`/`histCelula` (P1..P`top_n`, linha "Piloto" condicional),
  `cardRodada`/`linhaBonus`/`celBonusPalpite` (teto do bônus = `bonus_points`),
  `renderPilotos` (faixa do top`top_n`), `posicoesTopN()` (substituiu
  `HIST_POSICOES`), `adaptarTextosEstaticos()` (troca "top6"/"P1–P6"/"de 2026"
  nas legendas estáticas). CSS novo: `.hist-badge`, `.hist-voltar`,
  `.hist-avisos`, `.hall-acessar`, `[hidden]{display:none!important}` (as
  legendas tinham `display:flex` vencendo o `[hidden]`).
- Testes: `test_site.py` e `test_historico.py` cobrem `format`/`meta`/novo
  `seasons.json` — total do projeto: **89**.
- **Pendência:** a sinalização por rodada (`rounds_sem_palpite`,
  `total_recalculado`, `total_somado` no `standings.json`) ainda **não** é
  exibida — segue como sub-etapa seguinte.

**Ajustes 2026-09-08d (mesma sub-etapa):**
- **Bug do gráfico "Posição no ranking" (Ranking/Corridas):** em temporada sem
  compensação, o jogador que não apostava uma rodada sumia da linha acumulada
  (e da posição daquela rodada). `construirSerieJogador` passou a empurrar o
  acumulado **sempre** (`soma` não vira `null` — o total só não cresce) e o
  marcador some (`pointRadius 0`) nas rodadas sem palpite; o gráfico "por
  corrida" continua com o buraco (correto). O acumulado agora **parte de
  `carry_points`** (2021), então bate com o `total` do `standings.json`.
- **Matriz posição × corrida movida para Ranking/Geral nas temporadas
  finalizadas** (`MODO_HISTORICO`): `aplicarModoHistorico()` realoca o nó
  `#subsecao-historico` para dentro de `#subsecao-ranking-geral` (com um
  `<h2 id="hist-matriz-titulo">`), esconde o card `.corrida-detalhe-card`
  ("Pontuação da corrida" — leitura corrida-a-corrida não serve p/ ano
  fechado) e a sub-aba **Histórico** (Preferência vira o padrão de Palpites).
  Só relocação de DOM — nenhuma função de render mudou de assinatura.
- **`total_calculado` novo em `standings.json`** (`top6_total + bonus_total +
  carry + avulsos + compensação`) = total pelo nosso motor, **ignorando as
  correções do grupo** (`placar_publicado.json` rodada a rodada e
  `ranking_final.pontos`). Nas temporadas finalizadas com divergência o site
  mostra as colunas **"Oficial"** e **"Calculada"** (com a diferença entre
  parênteses) — `renderRanking`/`celCalculada`. 2021 e 2025 batem 100% (coluna
  não aparece); 2022–2024 divergem.
- **2026-09-08 — coluna "Calculada" removida (decisão do usuário: "o que vale é
  a oficial").** O ranking das temporadas passadas mostra só **Pontos** (=
  total oficial) + Média/Corrida (= `avg_points` = total oficial / rodadas
  jogadas). Saíram do `docs/app.js`: `celCalculada`, o header "Oficial", a
  coluna "Calculada", a nota `.ranking-nota-calculada` e o bloco de regras
  "Oficial × Calculada" (virou bloco "Pontuação"). `regras.json.comum` teve o
  item Oficial/Calculada reescrito. O campo `total_calculado` **continua** em
  `standings.json` (gerado por `site.py`), só não é mais exibido. CSS
  `.ranking-dif`/`.ranking-nota-calculada` ficaram órfãos (inofensivos).
- **`avg_points` agora sai do `total`, não do recálculo:**
  `avg_points = (total - compensation_total) / rounds_played`. Antes usava
  `top6_total + bonus_total + carry + avulsos` (o recálculo), que **diverge do
  `total`** quando `placar_publicado.json` corrige a pontuação por rodada — daí
  Caliman e Dalla, ambos com 139 pts em 2022, apareciam com médias 6,5 e 6,4.
  Agora dois jogadores com o mesmo `total` e as mesmas `rounds_played` mostram
  a mesma média (2021/2025/2026 não mudaram; 2022–2024 sim).
- **Jogador `dru` removido de 2023** (decisão do usuário — reverte a nota antiga
  "DRU é jogador"): tirado de `data/2023/palpites_2023.csv`,
  `players.json` (alias + nome) e `ranking_final.json` (`ordem`);
  `messages/1.txt` + `scores/1.json` + `docs/data/2023/` regenerados.
- **Sub-aba "Regras" no Ranking (só temporadas passadas):** `data-subaba="regras"`
  (`hidden` no HTML, revelada em `aplicarModoHistorico`). Conteúdo montado por
  `renderRegrasHistorico`: formato da temporada (de `FORMATO`) + **esquema
  visual** da regra 2/1/0 e do piloto da rodada (`esquemaPontuacao`, reusa
  `chipPiloto`/`badgePonto`), rodada sem palpite (compensação on/off),
  desempate, "Oficial × Calculada", cobertura (`meta.faltando`) e as decisões
  de cálculo por ano. O bloco `.regras-pontuacao` da sub-aba Geral fica
  `hidden` no modo histórico (redundante). Em 2026 nada muda.
- **`docs/data/regras.json` (novo, escrito à mão, sem gerador — como
  `hall_of_fame.json`):** `{comum:[...], por_ano:{"<ano>":[...]}}` com as
  decisões de cálculo de cada temporada (desempate, placar publicado, DRU,
  R19 Austin, "+1 por palpitar" de 2024, etc.). Carregado em `main()` só no
  modo histórico.
- **`rodadasMatriz()` (nova):** em `MODO_HISTORICO` as colunas da matriz vêm do
  **calendário inteiro** (`calendarGlobal`), não só de `standings.rounds`.
  Rodada sem palpite → coluna com cabeçalho `(sem registro)`
  (`.hist-matriz__sem-registro`/`.hist-matriz__rnota`) e `—` em todas as
  células (o `histCelula` já devolvia `—` para rodada ausente). 2026 (não
  finalizada) segue mostrando só as rodadas consolidadas.

**Sub-etapa 2026-09-08e — página de histórico por jogador (Hall of Fame).**
- **Tabela "Ranking de vitórias"** (`renderRankingHall`): ganhou uma coluna
  **"Total"** no fim (🥇+🥈+🥉) e um botão **"Acessar"** (`a.hall-acessar`,
  `?jogador=<id>`) entre o nome e a coluna 🥇. A ordem das linhas não mudou
  (🥇 desc, 🥈 desc, 🥉 desc, nome).
- **Rota nova `?jogador=<id>`** (recarrega a página, sem SPA — igual a `?ano`).
  `id` tem que ser um medalhista (aparecer em `construirRankingHall`); inválido
  → redireciona para a URL limpa. Estado global `MODO_JOGADOR`. Quando ativo,
  `main()` chama `renderPaginaJogador(id, hof)` e **retorna** (pula todo o
  pipeline de temporada).
- **`renderPaginaJogador`** (`docs/app.js`): esconde `.abas` + todas as `.secao`,
  mostra `#secao-jogador`, troca o `<h1>` para `👤 Jogador <nome> — Histórico`,
  revela `#btn-voltar-temporadas` (→ `location.pathname + "#hall"`). Carrega
  `data/<ano>/standings.json` + `bets.json` de **todas** as temporadas de
  `seasons.json` (client-side, `Promise.all`, `.catch(()=>null)`). Sem gerador
  Python novo, sem mudança em `bolao/site.py` nem nos formatos de
  `docs/data/*.json`.
- **Conteúdo (sem sub-abas — "sem segregação" por enquanto):**
  1. Card **Medalhas** — total + legenda `N 🥇   N 🥈   N 🥉`.
  2. Card **Temporadas disputadas** — nº de temporadas em que o `player_id`
     aparece no `standings.players` + lista dos anos.
  3. Gráfico **Posição no ranking por temporada** (Chart.js, eixo Y invertido,
     `jogador.position` por ano) — `renderGraficoPosicaoJogador`. Canvas criado
     com a seção já visível (sem init preguiçoso).
  4. **Apostas por piloto** (`renderApostasPorPiloto` + `agregarApostasPorPiloto`)
     — tabela piloto × (vezes apostado, pontos ganhos no top6, pts/aposta),
     agregada de `bets.players[id].rounds[*].top6_detail` de todas as
     temporadas, ordenada por vezes desc. Clicar/Enter numa linha abre
     **`<dialog id="jogador-modal">`** (`abrirModalPilotoAno`) com a separação
     por ano daquele piloto. Só o top6 entra nessa conta (piloto da rodada
     fora). Fecha no ✕, no Esc ou clicando fora.
- **`#hall` no hash:** `main()` (fluxo normal) clica a aba Hall of Fame quando
  `location.hash === "#hall"` — é como o botão "Voltar para temporadas" volta
  já na aba certa.
- **HTML novo:** `#btn-voltar-temporadas` no header, `#secao-jogador`
  (`#jogador-status` + `#jogador-container`), `<dialog id="jogador-modal">`.
  **CSS novo:** bloco `/* Página do jogador */` (`.jogador-card__valor`,
  `.jogador-pilotos-tabela`, `.jogador-modal`/`::backdrop`).
- Testes Python inalterados (90, nenhum toca no front-end).

**Ajustes 2026-09-08e (mesma sub-etapa):**
- **Gráfico "Posição no ranking por temporada":** plugin inline
  `pluginRotulos` (`afterDatasetsDraw`) desenha o **emoji da medalha** (🥇/🥈/🥉)
  no ponto dos pódios (`pointRadius: 0` nesses pontos) e o **número da posição**
  como rótulo limpo (cor `--texto-fraco`, acima do ponto) no resto. Eixo Y com
  `min: 0` (era 1) e `max = jogadores + 1` — folga em cima/embaixo pra não
  cortar o círculo/emoji; tick `0` escondido no `callback`.
- **Linha 2025→2026 pontilhada** quando a última temporada do jogador é a
  `SEASONS.atual` (`parcialFinal`): `segment.borderDash` no último segmento +
  2º dataset só-legenda (`data` toda `null`, `borderDash`) com label
  `"<ano> parcial"`; `legend` ligada só nesse caso, `tooltip.filter` ignora o
  dataset fantasma.
- **`chipPilotoEquipes(cod)` / `coresEquipesPiloto(cod)`:** no card "Apostas por
  piloto" o chip mostra **uma bolinha por equipe** pela qual o piloto passou
  nas temporadas do site (não só a cor de 2026). Cores são agrupadas por
  distância RGB ≤ 130 (`_distCor`) — ajuste fino de tom da mesma equipe de um
  ano pro outro conta como uma só; troca real de equipe vira cor nova.
  Heurística **decorativa e imperfeita** (ex.: AlphaTauri→Alpine do Gasly
  colapsa; se incomodar, criar um mapa de override por piloto). CSS novo
  `.piloto-bolinhas` (wrapper flex, gap 0.15rem).
- **Gráfico:** legenda removida; o "Parcial" agora vai **no rótulo do eixo X**
  ao lado do ano atual (`scales.x.ticks.callback`), o dataset-fantasma de
  legenda saiu.
- **Card Medalhas:** contagem em `.jogador-medalhas` (flex `space-between`,
  largura total) — `🥇 N` / `🥈 N` / `🥉 N` espaçados pra não confundir número
  com emoji.
- **Colisão de classe corrigida:** já existia `.jogador-card` (chips de filtro
  dos gráficos de Ranking/Corridas). Os cards da página do jogador passaram a
  usar **`.jogador-hist-card`** / `.jogador-hist-card__valor`.

**Ajustes 2026-09-08f (mesma sub-etapa):**
- **"Ranking de vitórias" agora lista TODOS os jogadores** que já disputaram uma
  temporada (não só medalhistas) — `construirTabelaVitorias(hof, universo)`:
  medalhistas primeiro (ordem 🥇/🥈/🥉), depois o resto em ordem alfabética com
  0/0/0. Todos ganham botão **Acessar** → página do jogador liberada pra todos.
- **Universo de jogadores:** `carregarTodasStandings()` +
  `universoJogadores(map)` (id → `{nome, anos}`) varrendo os
  `docs/data/<ano>/standings.json`. Carregado em `main()` (fluxo normal, junto
  do `hof`) e reaproveitado na validação de `?jogador=` e dentro de
  `renderPaginaJogador` (que agora recebe `standingsPreload` + `universo` e só
  busca os `bets.json`). Nome de exibição do não-medalhista vem do `standings`.
- **Dois badges "Maior trunfo" / "Maior decepção"** (`badgesTrunfoDecepcao`,
  `.jogador-destaque`) entre o título "Apostas por piloto" e a tabela: melhor e
  pior `pts/aposta` de um par **(piloto, temporada)**, considerando só pares em
  que o jogador apostou nesse piloto **≥ 5 vezes** naquela temporada. Fonte:
  `agregado.porAno`. Some se nenhum par qualifica.
- **Pop-up de apostas por piloto/ano** ganhou coluna **"Pts / aposta"**.
- **Jogadores sem medalha no "Ranking de vitórias"** agora ordenados pelo
  **somatório de pontos** de todas as temporadas (desc), não alfabético;
  linha com fundo sombreado (`tr.hall-linha--sem-medalha`). `universoJogadores`
  acumula `pontos` (`p.total ?? p.total_somado`).

**Ajustes 2026-09-08g (mesma sub-etapa) — faixa de bandeiras no Ranking/Geral:**
- **Faixa fina de círculos** (`#corridas-flags` → `renderFaixaCalendario`),
  **acima** de `#corridas-cards` na sub-aba **Geral** do Ranking: um círculo por
  corrida do calendário (`calendar.races`), da borda esquerda à direita
  (`display:flex; justify-content:space-between; flex-wrap`). Cada círculo tem a
  bandeira do país do circuito. Na temporada atual, as corridas já em
  `standings.rounds` ficam **escurecidas** (`--passada`, grayscale+opacity); em
  `MODO_HISTORICO` **nenhuma** escurece.
- **Bandeiras versionadas no repo:** `docs/flags/<iso2>.svg` (25 arquivos,
  **Twemoji, CC-BY 4.0**, `docs/flags/ATTRIBUTION.txt`) — sem CDN/rede em
  runtime, ~37 KB somando todas, cache do navegador. `<img loading="lazy">`
  dentro do círculo (`object-fit: cover`).
- **`CIRCUITOS`** (`app.js`): mapa `circuitId` (slug da Jolpica) → `{pais, iso,
  nome}` para os 29 circuitos que já apareceram em algum calendário 2021–2026.
  Circuito fora do mapa cai num 🏁 genérico.
- **Tooltip próprio** (`.faixa-tooltip`, `mostrarFaixaTooltip`/`esconder…`, um
  único nó reaproveitado, posicionado acima do círculo) no hover/foco:
  `R{n} · {país}` / `{circuito}` / `Quali: {qualifying_utc→America/Sao_Paulo}`
  (ou "fim de semana de {data}" quando não há horário).
- Sem gerador Python, sem mudança em `docs/data/*.json`.
- **Sempre 1 linha:** `.corridas-flags` é `flex-wrap: nowrap`; os itens são
  `flex: 1 1 0; min-width: 0; max-width: 1.05rem; aspect-ratio: 1/1` — encolhem
  no celular para caber todas as corridas numa linha só (no desktop batem o teto
  de 1.05rem e o `space-between` distribui a folga).
- **Rodapé:** 2ª linha "Todos os horários referidos nesta página são relativos
  ao horário oficial de Brasília"; as marcações "(horário de Brasília)" saíram
  dos cards e do tooltip (`formatarQualiBrasilia` só formata, sem sufixo).

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
  (Etapa 6) — fine-grained PAT renovado em 2026-08-15, válido até
  2026-12-31 (lembrete de renovação agendado para 2026-12-15).
