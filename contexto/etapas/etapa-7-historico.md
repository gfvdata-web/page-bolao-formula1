# Etapa 7 — Histórico

> Movido do antigo `CONTEXTO.md` (seção 8) sem alteração de conteúdo. Status da etapa: ver `contexto/status.md`.

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
  de piloto usam as cores da equipe **daquele ano**. Todos os gráficos passam
  por `corPiloto()`. (Os mapas fixos por piloto foram substituídos pela base de
  equipes da Etapa 8.)

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
- **Bandeiras versionadas no repo:** `docs/flags/<iso2>.svg` (26 arquivos,
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
