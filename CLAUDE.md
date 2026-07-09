# CLAUDE.md — Bolão F1

> Este arquivo é carregado automaticamente em toda conversa. Ele orienta o
> **todo** do projeto; o detalhe completo está em `CONTEXTO.md`.

## Antes de começar qualquer tarefa

1. **Leia o `CONTEXTO.md` inteiro.** Ele tem objetivo, regras de pontuação,
   formato da mensagem, decisões técnicas, modelo de dados e o plano de etapas.
2. Identifique **em qual etapa (1–7)** esta conversa está focada (o usuário diz
   no primeiro prompt). Trabalhe **apenas** nessa etapa, respeitando as
   entradas/saídas descritas na seção 8 do `CONTEXTO.md`, para não invadir as
   etapas vizinhas.
3. **Atualize o status na seção 8 do `CONTEXTO.md` conforme a etapa avança:**
   marque ⬜ → 🟡 ao **começar** a etapa e 🟡 → ✅ ao **concluí-la**. Registre no
   arquivo qualquer decisão nova que as próximas etapas precisem conhecer.

## Fluxo de Git (obrigatório em todas as etapas)

O projeto é um repositório Git. Mantê-lo sempre versionado e limpo:

- **Commit a cada avanço concluído**, não só no fim da etapa: um passo funcional
  (ex.: "parser lê o texto", "pontuação do top6", "testes passando") = um commit.
  Commits pequenos e frequentes evitam perda de trabalho entre conversas.
- **Mensagens claras e em português**, prefixadas com a etapa. Ex.:
  `Etapa 1: pontuação do top6 + testes`.
- Ao mudar o status na seção 8 do `CONTEXTO.md`, **inclua essa alteração no
  mesmo commit** do trabalho correspondente.
- Antes de começar a trabalhar, rode `git status` para ver o estado. Ao final de
  cada bloco de trabalho, deixe a árvore **limpa** (tudo commitado).
- Não commitar segredos nem artefatos (já cobertos pelo `.gitignore`).
- **Não fazer `push`** por conta própria — só quando o usuário pedir (o remote no
  GitHub entra na Etapa 5). Trabalhar em commits locais até lá.
- Ao final de commits feitos pelo Claude, usar o trailer:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`

## Resumo do projeto

Bolão de palpites do **qualifying da F1** entre amigos. Cada um envia um palpite
(top6 + posição de um piloto da rodada) via WhatsApp; depois do quali o palpite
é pontuado e somado ao ranking da temporada. Escopo atual: **2026**.

## Decisões fixas (não reabrir sem o usuário pedir)

- **Python** para lógica; **GitHub Pages** para o site; **GitHub Actions** para
  rodar na nuvem (nada roda na máquina local — operação é pelo celular).
- Gatilho: **Google Forms → Apps Script → `repository_dispatch` → Actions**.
- Fonte de dados F1: **API Jolpica-F1** (gratuita, sem chave).
- Só conta o **qualifying principal** (sprints ignorados).
- Pontuação: top6 (2 pts posição exata / 1 pt dentro do top6 real em outra
  posição) + 1 pt pela posição exata do piloto da rodada. **Máx 13 pts/corrida.**

## Etapas (detalhe e status na seção 8 do `CONTEXTO.md`)

1. Parser + pontuação (núcleo Python) — base, roda offline
2. Integração Jolpica-F1 (calendário, resultado, entry list)
3. Geração dos dados do site
4. Site estático (ranking + filtro por jogador)
5. GitHub Actions (pipeline via `repository_dispatch`)
6. Google Forms + Apps Script (gatilho pelo celular)
7. Histórico (adiado)

Desenvolver na ordem — cada etapa depende das anteriores.

## Convenções

- Código e comentários podem ser em português (contexto do projeto é PT-BR).
- Manter os **formatos de dados estáveis** entre etapas: se uma etapa precisar
  mudar um formato já usado por outra, registrar a mudança no `CONTEXTO.md`.
