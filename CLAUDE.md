# CLAUDE.md — Bolão F1

Bolão de palpites do **qualifying da F1** entre amigos. Cada um envia um palpite
(top6 + posição de um piloto da rodada) via WhatsApp; depois do quali o palpite
é pontuado e somado ao ranking da temporada. Temporada atual: **2026**; o site
também tem o histórico 2021–2025. Em produção (GitHub Pages), operado pelo celular.

> Este arquivo é um **índice**: vale para toda tarefa e aponta onde está o resto.
> O conhecimento do projeto fica em `contexto/` e é lido **sob demanda**.

## Antes de começar qualquer tarefa

1. Rode `git status`.
2. Identifique o **tema** do pedido (e a etapa, se o usuário disser) e use o mapa
   "Onde está cada tema" abaixo: leia **só** os arquivos/seções apontados.
   `etapa-4-site.md` (~750 linhas) e `etapa-7-historico.md` (~580) são grandes —
   localize o bloco com Grep (pelo título citado no mapa ou pelo termo) e leia o trecho.
3. **Antes de decidir algo que pode já ter sido decidido** (formato, regra, nome,
   comportamento de tela), busque o termo em todo o contexto:
   `grep -rn "<termo>" contexto/`. Decisões marcadas "não reabrir" estão
   espalhadas pelas etapas — o mapa aponta os lugares principais, a busca cobre o resto.
4. Tarefa que mexe em regra de pontuação, formato da mensagem ou fluxo de
   operação → leia também `contexto/visao-geral.md`.
5. Trabalhe só na etapa/tema pedido, respeitando as entradas/saídas descritas no
   arquivo da etapa. Status em `contexto/status.md`: ⬜ → 🟡 ao começar, 🟡 → ✅ ao concluir.

## Onde registrar o que for decidido

- Decisão nova → no arquivo da etapa em que se está trabalhando, no padrão já
  usado lá ("Decisões fixadas…" / "Ajuste posterior (…): …", com data).
- Mudança num **formato já usado por outra etapa** → registrar na etapa atual
  **e** deixar uma nota no arquivo da etapa que definiu o formato, apontando a mudança.
- Tema ou arquivo novo de contexto → acrescentar a linha no mapa abaixo.
- Instrução curta que só vale para uma área do código → `.claude/rules/<área>.md`
  (a explicação longa fica no arquivo da etapa, a regra só aponta).
- Manter o texto objetivo e enxuto.

## Fluxo de Git (obrigatório)

- **Commit a cada avanço concluído**, não só no fim da etapa: um passo funcional
  (ex.: "parser lê o texto", "pontuação do top6", "testes passando") = um commit.
  Commits pequenos e frequentes evitam perda de trabalho entre conversas.
- **Mensagens claras e em português**, prefixadas com a etapa. Ex.:
  `Etapa 1: pontuação do top6 + testes`.
- Mudança de status em `contexto/status.md` vai **no mesmo commit** do trabalho.
- Ao final de cada bloco de trabalho, deixe a árvore **limpa** (tudo commitado).
- Não commitar segredos nem artefatos (já cobertos pelo `.gitignore`).
- **Não fazer `push`** por conta própria — só quando o usuário pedir.
- Commits feitos pelo Claude terminam com o trailer `Co-Authored-By` que o
  Claude Code indicar na sessão.

## Decisões fixas (não reabrir sem o usuário pedir)

- **Python** para lógica; **GitHub Pages** para o site; **GitHub Actions** para
  rodar na nuvem (nada roda na máquina local — operação é pelo celular).
- Gatilho: **Google Forms → Apps Script → `repository_dispatch` → Actions**.
- Fonte de dados F1: **API Jolpica-F1** (gratuita, sem chave).
- Só conta o **qualifying principal** (sessões de sprint ignoradas; o quali
  principal de fim de semana com sprint vale).
- Pontuação 2025–2026: top6 (2 pts posição exata / 1 pt dentro do top6 real em
  outra posição) + 1 pt pela posição exata do piloto da rodada. **Máx 13
  pts/corrida.** Anos anteriores têm regras próprias (`bolao/formats.py`).

## Comandos

- `python -m pytest tests/ -q` — testes offline (~1–2 s).
- `python -m bolao.site build [--season AAAA]` — regenera `docs/data/` a partir de `data/`.
- `python -m bolao.pipeline run|retry <rodada>` — o que o Actions executa.
- `python -m bolao.jolpica calendar|drivers|result N|results [--season AAAA]` —
  ⚠ `calendar` sobrescreve os aliases manuais do `calendar.json`.
- `python -m bolao.historico build --season AAAA [--check-only]` — temporadas antigas.
- Site local: preview `docs-static` do `.claude/launch.json` (porta 8123).

## Estrutura

- `bolao/` — núcleo Python, só stdlib (parser, scoring, jolpica, site, pipeline…).
- `tests/` — `unittest.TestCase` rodados via pytest; `tests/fixtures/`.
- `data/` — entradas e intermediários por temporada (`data/<ano>/`), versionados.
- `docs/` — **o site publicado** (GitHub Pages): `index.html`, `app.js`,
  `analise.js`, `style.css`, `flags/`, `data/` (gerado). Não colocar `.md` aqui.
- `.github/` — workflow do pipeline e scripts.
- `google-apps-script/` — `Code.gs` + `SETUP.md`.
- `android/` — app Android nativo (Etapa 9; ainda a criar na sub-etapa 9a).
- `contexto/` — documentação do projeto (este índice aponta para ela).
- `historico_wpp/` — export do WhatsApp, **fora do Git** (privacidade).

## Onde está cada tema

Todos em `contexto/`. "§" = seção; títulos entre aspas = bloco em negrito no arquivo.

| Tema | Onde ler |
|------|----------|
| Objetivo, regras de pontuação e compensação (atual) | `visao-geral.md` §1–2 |
| Formato da mensagem do WhatsApp | `visao-geral.md` §3; tolerâncias do parser: `etapa-3` "Parser fortalecido", `etapa-5` "3 bugs reais na rodada de Madrid" |
| Decisões técnicas, fluxo pelo celular, setup/PAT | `visao-geral.md` §4, §5, §10 |
| Status das etapas e o que está em aberto | `status.md` |
| Regras por temporada 2021–2025 (top5, bônus 2 pts em 2024, compensação, desempate) | `etapa-7` "Regras por temporada", "Fechamento do histórico" |
| Identidade de jogador, apelidos (`players.json`) | `etapa-3` "Decisões fixadas"; `etapa-7` "Decisões de identidade de jogador" |
| Corrida → rodada (`resolve_race`), aliases do calendário | `etapa-2` "Resolução por palavras"; `etapa-5` Madrid; `etapa-4` "sub-abas Geral/Corridas" (re-download do calendário) |
| `results/<rodada>.json`, `drivers.json` (+ `fases`, `equipes`) | `etapa-1` "Formatos estáveis"; `etapa-2` "Decisões fixadas" |
| `calendar.json` (+ `qualifying_utc`) | `etapa-2`; `etapa-4` "sub-abas Geral/Corridas" |
| `scores/`, `standings.json`, `bets.json`, `results.json` do site | `etapa-3` "Formatos novos"; campos aditivos: `bet_order` (`etapa-4` "botões Copiar"), `format`/`meta`/`seasons.json`/`total_calculado`/`avg_points` (`etapa-7` "Sub-etapa 2026-09-08d" e ajustes) |
| Dados do histórico (CSVs, `placar_publicado`, `ranking_final`, `pontos_avulsos`, `saldo_inicial`) | `etapa-7` "Base 2021–2024", "Fechamento do histórico" |
| `hall_of_fame.json`, `regras.json` (escritos à mão) | `etapa-4` "aba Hall of Fame"; `etapa-7` "Ajustes 2026-09-08d" |
| Equipes por piloto/ano (nome e cor) | `etapa-8` "Base de equipes" |
| Jolpica-F1 (API, `fetch_*`/`build_*`) | `etapa-2` |
| Pipeline, workflow, códigos de saída 0/1/2, verificador | `etapa-5` |
| Google Forms, Apps Script, token | `etapa-6`; `google-apps-script/SETUP.md` |
| Front-end: arquitetura, helpers, tema claro/escuro | `etapa-4` "Mapa do front-end" (visão inicial, desatualizada nos detalhes), "switch de tema"; Chart.js: `etapa-4` "Importante (bug de layout" |
| Abas da temporada (Ranking: Geral/Corridas/Palpites/Simulador; Rendimento; Pilotos) | `etapa-4` (blocos "Ajuste posterior"); estado mais recente das abas: `etapa-4` "abas padronizadas" e "Ajustes seguintes (2026-09-27)" |
| Hall of Fame | `etapa-4` "aba Hall of Fame"; `etapa-7` "Hall of Fame — switch", "Sub-etapa 2026-09-08e/f" |
| Modo histórico `?ano`, faixa de bandeiras | `etapa-7` "Sub-etapa 2026-09-08d", "Ajustes 2026-09-08g" |
| Perfis `?jogador` / `?piloto`, "Ir para" | `etapa-7` "Sub-etapa 2026-09-08e" e ajustes; `etapa-4` "bloco \"Ir para\""; `etapa-8` |
| Navegação `?menu`, `?jogadores`, `?pilotos`, `analise.js` | `etapa-8` |
| App Android (Kotlin/Compose): arquitetura, envio de palpite via `doPost`, build/assinatura, sub-etapas | `etapa-9` |
| Testes: levantamento e plano em lotes | `testes.md` |

## Regras sob demanda (carregadas sozinhas ao abrir arquivos da área)

- `.claude/rules/frontend.md` — `docs/` (JS, CSS, HTML)
- `.claude/rules/python.md` — `bolao/`, `tests/`
- `.claude/rules/dados.md` — `data/`, `docs/data/`
- `.claude/rules/automacao.md` — `.github/`, `google-apps-script/`, `bolao/pipeline.py`

## Convenções

- Código e comentários podem ser em português (contexto do projeto é PT-BR).
- Manter os **formatos de dados estáveis** entre etapas (ver "Onde registrar").
