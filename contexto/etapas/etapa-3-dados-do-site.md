# Etapa 3 — Geração dos dados do site

> Movido do antigo `CONTEXTO.md` (seção 8) sem alteração de conteúdo. Status da etapa: ver `contexto/status.md`.

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

> **Nota (Etapa 9c, 2026-10-08):** `docs/data/` tem um **segundo consumidor**, o
> app Android (`android/.../data/modelo/Modelos.kt`). Mudanças nesses formatos
> têm que continuar **aditivas** (campo novo pode; renomear/remover/mudar tipo
> quebra o app instalado). O CI do app (`android.yml`) lê os JSONs reais a cada
> mudança em `docs/data/**` e acusa formato incompatível.
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

**Ajuste posterior (2026-11-07): rodada com dois pilotos da rodada (Interlagos 2026, R20).**
Regra e formato da mensagem: `visao-geral.md` §2 "Exceção". Genérico para N pilotos.
- Leitor (`parser.py`): `_parse_bonus_drivers` separa a linha `Piloto ...` por
  `e`/`,`/`&`/`+`/`/`; `Sheet.bonus_drivers` (lista) e `Bet.bonus_guesses` (um
  chute por piloto). `bonus_driver`/`bonus_guess` continuam = o 1º. Os `P#`
  seguidos depois do primeiro vão para o mesmo jogador; `P#` faltando = 0; `P#`
  a mais ou piloto repetido = `ParseError`.
- Pontuação (`scoring.py`): `PlayerScore.bonus_detail` (um item por piloto);
  `bonus_points` = soma; `bonus_guess`/`bonus_real_pos` = do 1º.
- **Campos aditivos, só em rodada com 2+ pilotos** (rodadas normais ficam
  idênticas — o app Android continua lendo `bonus_guess`/`bonus_points`):
  rodada do `standings.json` ganha `bonus_drivers` e `max_points` (14);
  palpite em `bets.json` e jogador em `scores/<r>.json` ganham
  `bonus_detail:[{driver, guess, real_pos, points}]`.
- Câmara: alias manual `camara`/`rafael camara`/`rafael`/`cam` → `CAM` em
  `data/drivers.json` (a Jolpica não dá código a ele; o resultado usa as 3
  primeiras letras do sobrenome = `CAM`). ⚠ `python -m bolao.jolpica drivers`
  regrava o arquivo e apaga esses aliases.
- **Correção no mesmo dia (1º envio real falhou):** quase todos escreveram o
  piloto junto do chute (`P9 BOR`, `BOR P9`, `Cam 17`, `BOR p7`) e o leitor só
  aceitava `P#` puro, desalinhando os blocos. Agora a linha de chute aceita
  posição + nome em qualquer ordem **se o nome for de um piloto da rodada**; o
  chute vai para esse piloto (mesmo fora da ordem); os sem nome ocupam as vagas
  livres na ordem do cabeçalho; dois chutes para o mesmo piloto = `ParseError`.
  Mensagem real em `tests/fixtures/interlagos_2026_real.txt`.
- Testes: `tests/test_dois_pilotos.py` (+ fixture) e contrato em
  `test_dados_publicados.py` (máximo por rodada). Site: `etapa-4` mesma data.
