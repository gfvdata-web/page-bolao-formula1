# Plano futuro — backend na Cloudflare (Workers + D1)

> Avaliado em 2026-10-12/13 e **adiado** pelo usuário: o sistema atual
> (Forms/app → Apps Script → Actions → `data/` → site) continua. Este arquivo
> guarda a avaliação para quando a ideia voltar. **Nada foi criado** na
> Cloudflare (nem Worker nem D1).

## Premissa fixada pelo usuário (2026-10-13, não reabrir sem ele pedir)

Se a migração acontecer, o **funcionamento do bolão não muda**:
- O palpite continua chegando como o **bloco do WhatsApp colado** pelo
  operador (Guilherme), pelo Forms ou pelo app. O envio dispara a busca do
  resultado oficial e o cálculo, como hoje.
- **Sem prazo** de envio, **sem código individual** por jogador, **sem
  palpite avulso** de jogador. O app é **só do operador**.
- Regra de pontuação e resultados do histórico 2021–2025 idênticos.

O pedido original da avaliação incluía código individual, prazo e palpite por
jogador via API. Com essa premissa, essas partes saem do plano.

## Por que foi adiado

Com o funcionamento igual, o ganho é pequeno:
- **Ganharia:**
  - Resposta imediata no app ("rodada N, X palpites lidos, pontuado/aguardando"),
    em vez de só "enviado ao GitHub". Hoje o resultado aparece no site minutos depois.
  - Erro de leitura da mensagem mostrado no app, e não por e-mail de falha do Actions.
  - Fim do PAT anual (vence 2026-12-31), da vigília de 5 h e do commit do bot.
    O Apps Script continua enquanto o Forms existir.
- **Custaria:**
  - Reescrever parser + pontuação + gerador do site em TypeScript (o usuário programa em Python).
  - Montar a conferência de paridade com o histórico.
  - Mudar o app e o painel-status.
  - Risco no meio da temporada.

**Alternativa barata registrada:** resolver a confirmação só no app. Depois do
envio, o app consulta o site até a rodada aparecer pontuada e avisa
"pontuado" ou "aguardando resultado oficial". Não precisa de servidor novo.

## Se for retomado — o que já foi avaliado

**Linguagem: TypeScript no Worker, Python como auditor.**
- O plano grátis tem **10 ms de CPU por chamada**, inclusive no Cron.
- O `site.generate` de 2026 levou ~94 ms em CPython nativo (medido em
  2026-10-12, com leitura de arquivos). Python Workers (Pyodide) só caberia no
  **Paid (US$ 5/mês)** e tem partida a frio de ~1 s.
- O Python continua gerando **gabaritos** a partir de `data/`: os 119 textos de
  2021–2026 parseados, os pontos de cada palpite e os JSON do site. O TS só
  passa no CI se bater exatamente.

**Onde mora:** um **Worker separado** (`bolao-api`, TS + D1 + Cron), em
subdomínio de um nível (ex.: `bolaof1-api.gfvdata.com`), com ambiente `teste`
e D1 próprio.
- Pages Functions não têm Cron Trigger.
- Migrar o site do Pages para Worker com assets mexe no que funciona sem ganho.
  Fica como passo opcional no fim.
- O site segue no Pages (`bolao-formula1`), com a mesma aparência.

**Esquema D1 (adaptado à premissa):**

| Tabela | Conteúdo |
|---|---|
| `temporadas` | espelho de `formats.py` |
| `rodadas` | calendário + aliases + piloto da rodada vindo do cabeçalho + estado `recebida`/`pontuada` |
| `pilotos` | entry list por ano |
| `participantes`, `apelidos` | `players.json` |
| `mensagens` | texto colado por rodada, com histórico de reenvios (substitui `messages/N.txt`) |
| `palpites` | parseados por rodada/jogador |
| `resultados` | por posição, com fase e equipe |
| `pontuacoes` | com `total_recalculado` |
| `ajustes` | `placar_publicado`, `saldo_inicial`, `pontos_avulsos`, `ranking_final` em JSON |
| `documentos` | JSON prontos no formato de `docs/data/`; temporadas fechadas servidas como o Python gerou |
| `eventos` | log do cron, para o painel-status |

**Rotas:**
- `GET /api/v1/saude`
- `GET /api/v1/data/<ano>/<arquivo>.json`: mesmos JSON de `docs/data/`; o app só troca a URL base.
- `POST /api/v1/mensagem`: texto + rodada opcional, com a chave do operador
  (`wrangler secret`). Responde já com o resumo do parse e o estado da pontuação.
- `GET /api/v1/status`: para o painel-status.

**Cron `*/5`:** rodada recebida e ainda sem resultado → consulta a Jolpica →
grava, pontua e regenera `documentos`. Substitui o verificador de 5 h.

**Fases (cada uma testável no celular, com o APK debug ao lado do oficial):**
0. Registro das decisões.
1. Worker + D1 + `/saude`.
2. Pontuação/gerador em TS + gabaritos + importação 2021–2026 + rotas `/data`
   (paridade no CI; o app debug lendo a API).
3. Parser em TS + `POST /mensagem` (em `teste`).
4. Cron + Jolpica, **em sombra** ao lado do Actions por 2–3 quali reais.
5. Virada: Apps Script/app enviam para a API; o espelho D1 → `data/` +
   `docs/data/` (Action, por `repository_dispatch`) mantém as URLs antigas
   vivas e roda o `site.py` como auditoria.
6. Limpeza.

**Rollback:** até a virada, nada depende do sistema novo. Depois dela, religar o
gatilho do `pipeline.yml`: o espelho mantém `data/` no formato do Python. Há
ainda o Time Travel do D1 (7 dias no grátis) e o Git como cópia de segurança.

**Limites do plano grátis (conferidos em 2026-10-12):**
- 100 mil requisições/dia.
- D1: 5 GB; 5 mi linhas lidas e 100 mil escritas/dia, bloqueando de fato
  desde 2026-09-01. O histórico inteiro tem menos de 20 mil linhas.
- 5 Cron Triggers por conta.
- 50 subrequests por chamada.
- CPU de 10 ms: **único risco real**. O `bets.json` de 2026 tem 212 KB. Medir
  com `wrangler tail` na fase 2.

**Painel-status (mudaria lá, não aqui):**
- `src/vigia_bolao.py` e `src/etapas_bolao.py` leem as runs do `pipeline.yml` e
  o deploy do Pages. Passariam a ler `/api/v1/status`.
- O aviso `bolao_palpite` do Apps Script sai, ou o Worker passa a dispará-lo
  (PAT como secret).
- O job `vigiar-bolao` do `atualizar-status.yml` precisa ser revisto.
- O card e a `BolaoTela` do app do painel mudam de modelo de etapas.

**Play Store (fora de escopo):** a autoatualização pelo GitHub Releases não é
permitida lá. Seria preciso a In-App Updates API e o Play App Signing.
