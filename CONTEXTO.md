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
  - **Cards compactados para caber em 2 linhas** (`.simulador-cards`:
    `grid-auto-flow: column` + `grid-template-rows: repeat(2, auto)` +
    `overflow-x: auto` — mais jogadores viram colunas extras, rolagem
    horizontal, nunca 3ª linha), com paddings/fontes reduzidos
    (`.simulador-card`, `.simulador-card__nome`, `.simulador-card__valor`
    etc.).
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
