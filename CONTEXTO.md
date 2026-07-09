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
- **Entregue:** pacote `bolao/` (`normalize`, `parser`, `scoring`, `cli`),
  mocks em `data/`, exemplo em `examples/silverstone.*`, 21 testes (unittest).
  Rodar: `python -m unittest discover -s tests`. CLI:
  `python -m bolao.cli examples/silverstone.txt examples/silverstone_result.json --detalhe`.
  Conferência manual bateu: Vinícius 13 (máx), Guilherme 7, Dalla 6, Caio L. 3.

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
  exibição) + casos novos em `tests/test_parser.py` — total do projeto: **52**.

**Formatos novos definidos aqui (a Etapa 4 consome estes; não reabrir):**
- **`messages/<round>.txt`:** texto bruto do WhatsApp, um arquivo por rodada. O
  nome do arquivo é a rodada; a Etapa 3 confere batendo com `resolve_race` do
  cabeçalho. Uma rodada só entra na consolidação se tiver **messages + results**.
- **`scores/<round>.json`:** `{round, race_id, season?, race, circuit, date,
  sprint, bonus_driver, result_order:[...], players:[{player_id, player_raw,
  name, top6:[6], top6_detail:[{pos,guess,real,points,reason}], top6_points,
  bonus_guess, bonus_real_pos, bonus_points, total}]}`. Jogadores ordenados por
  total desc, `player_id` asc.
- **`docs/data/standings.json`:** `{season, rounds:[{round, race_id, race,
  circuit, date, sprint, bonus_driver}], players:[{position, player_id, name,
  total, top6_total, bonus_total, rounds_played, per_round:{"<round>":pts}}]}`.
  Ordenado por total desc, `player_id` asc (desempate adiado → ordem estável).
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
- **Sem timestamp** nos JSONs gerados (saída determinística → diffs limpos e
  testes estáveis).

### Etapa 4 — Site estático ⬜
- **Objetivo:** `docs/index.html` que lê os JSONs e mostra **ranking da
  temporada** + **palpites por jogador (com filtro)**.
- **Pronto quando:** abre no navegador (e no GitHub Pages) mostrando ranking e
  filtro funcionando.
- **Depende de:** Etapa 3 (formato dos JSONs).

### Etapa 5 — GitHub Actions ⬜
- **Objetivo:** workflow acionado por `repository_dispatch` que roda o pipeline
  completo (parse → buscar resultado → pontuar → gerar dados → commit).
- **Pronto quando:** disparar o evento atualiza o site sozinho.
- **Depende de:** Etapas 1–4.

### Etapa 6 — Google Forms + Apps Script ⬜
- **Objetivo:** formulário no celular + Apps Script que dispara o
  `repository_dispatch` com o texto colado e a corrida.
- **Pronto quando:** enviar o formulário pelo celular atualiza o site
  ponta-a-ponta.
- **Depende de:** Etapa 5 (nome do evento e formato do payload).

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
- ⬜ Remote no GitHub (entra na Etapa 5, junto com o Actions/Pages).
- ⬜ Conta/projeto do Google para o Forms + Apps Script (Etapa 6).
- ⬜ Token/permissão para o Apps Script disparar o `repository_dispatch` (Etapa 6).
