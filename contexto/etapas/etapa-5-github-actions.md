# Etapa 5 — GitHub Actions

> Movido do antigo `CONTEXTO.md` (seção 8) sem alteração de conteúdo. Status da etapa: ver `contexto/status.md`.

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

**Ajuste posterior (ainda Etapa 5): 3 bugs reais na rodada de Madrid (r14) —
parser mais tolerante + alias de calendário.**
- **Sintoma:** a Action de Madrid rodou e falhou em 8s (nada foi gravado — sem
  `messages/14.txt`, sem `results/14.json`), e ninguém percebeu até o usuário
  perguntar por que o site não tinha atualizado.
- **Bug 1 (`bolao/parser.py`):** o Igor esqueceu a linha `P#` (chute do piloto
  da rodada) e a linha em branco antes do próximo jogador. Sem terminador, o
  parser juntava o bloco dele com o do jogador seguinte e estourava
  `ParseError`. **Corrigido:** um bloco `nome + top_n pilotos` agora fecha
  sozinho ao acumular `top_n + 1` linhas assim que a linha seguinte não é um
  chute (`_fecha_bloco_sem_bonus`) — ela pertence ao próximo jogador. Jogador
  sem chute do bônus vale **0 pt** (mesma regra do `P0`), em vez de derrubar a
  rodada inteira.
- **Bug 2 (`bolao/parser.py`, `_FILLER_BONUS`):** o cabeçalho usou "Piloto **da
  vez**: Alonso" — frase nova, não reconhecida como enfeite — e o piloto da
  rodada virava `DAV` (fallback de 3 letras) em vez de `ALO`, pontuando o
  bônus da rodada **toda** errado, **sem erro nenhum** (o pior tipo de bug:
  silencioso). `"da"`/`"vez"` entraram em `_FILLER_BONUS`.
- **Bug 3 (`data/2026/calendar.json`):** o cabeçalho também tinha "**Mad
  Ring**" (com espaço — o nome oficial do circuito é uma palavra só,
  "Madring"). `resolve_race` casa por palavras em comum, e a palavra solta
  `"ring"` batia com o alias `"red bull ring"` da Áustria (rodada 8, já
  pontuada) — `"madring"` (uma palavra) não batia com `"mad"`/`"ring"`
  separados. **Sem esse alias, reenviar o palpite já corrigido teria
  sobrescrito a rodada 8 em vez de gravar a rodada 14** (falha silenciosa,
  pior que o crash do parser). Alias `"mad ring"` adicionado à rodada 14.
- **Padrão para o futuro:** falha de parser (`ParseError`) é o comportamento
  **desejado** diante de ambiguidade real (não adivinhar) — mas "jogador sem
  chute do bônus" deixou de ser ambiguidade (o bloco fecha por tamanho, não
  por adivinhação de conteúdo). Já resolução de corrida errada e piloto da
  rodada errado **não geram erro nenhum** por padrão (`resolve_race` sempre
  devolve alguma corrida se houver palavra em comum; `normalize_driver`
  sempre cai no fallback de 3 letras) — esses dois exigem **conferência manual
  do resumo antes de confiar num envio novo de cabeçalho** (variação de
  fraseado ainda não vista pode enganar os dois sem avisar).
- Testes novos em `tests/test_parser.py` (bloco sem bônus no meio/fim da
  mensagem, "Piloto da vez") — total do projeto: **93**.
