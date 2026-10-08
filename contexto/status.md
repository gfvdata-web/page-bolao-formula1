# Status das etapas

> Fonte única do status de cada etapa (era a seção 8 do antigo `CONTEXTO.md`).
> Ao começar uma etapa: ⬜ → 🟡. Ao concluí-la: 🟡 → ✅. Mudança de status vai
> no mesmo commit do trabalho correspondente.

Status: ⬜ não iniciada · 🟡 em andamento · ✅ concluída

Cada etapa é pensada para ser desenvolvida em **uma conversa focada**: ler o
arquivo da etapa indicada (e o que o mapa do `CLAUDE.md` apontar para o tema) e
trabalhar **apenas** nela, respeitando as entradas/saídas descritas no arquivo,
para não invadir as etapas vizinhas.

| Etapa | Status | Arquivo | Resumo |
|-------|--------|---------|--------|
| 1 | ✅ | `etapas/etapa-1-parser-pontuacao.md` | Parser do WhatsApp + pontuação; formatos de resultado, `drivers.json`, `players.json` |
| 2 | ✅ | `etapas/etapa-2-jolpica.md` | Jolpica-F1: calendário, entry list, resultado; `race_id`, `resolve_race`, `fases`/`equipes` |
| 3 | ✅ | `etapas/etapa-3-dados-do-site.md` | `site.py`: `scores/`, `standings.json`, `bets.json`, `results.json`; compensação |
| 4 | ✅ | `etapas/etapa-4-site.md` | Site estático (todas as abas/sub-abas da temporada) e seus ajustes posteriores |
| 5 | ✅ | `etapas/etapa-5-github-actions.md` | `pipeline.py` + workflow; códigos de saída 0/1/2; verificador; bugs de Madrid |
| 6 | ✅ | `etapas/etapa-6-forms-apps-script.md` | Forms + Apps Script → `repository_dispatch`; PAT |
| 7 | 🟡 | `etapas/etapa-7-historico.md` | Temporadas 2021–2025, regras por ano, modo histórico `?ano`, página `?jogador` |
| 8 | ✅ | `etapas/etapa-8-navegacao-analises.md` | Menu, `?jogadores`, `?pilotos`, perfis, base de equipes |
| 9 | 🟡 | `etapas/etapa-9-app-android.md` | App Android nativo (Kotlin/Compose), APK via Releases, envio de palpite pelo app |

## Em aberto

- **Etapa 7:** falta exibir a sinalização por rodada (`rounds_sem_palpite`,
  `total_recalculado`, `total_somado` no `standings.json`). Ver "Pendência" na
  sub-etapa 2026-09-08d.
- **Etapa 8:** concluída em 2026-10-03 (v1 revisada e aprovada pelo usuário,
  links das tabelas da temporada para os perfis incluídos).
- **Etapa 9:** plano escrito em 2026-10-08; próxima é a sub-etapa 9a (esqueleto
  + APK de debug). Confirmar o `applicationId` antes.
- Pendências gerais e decisões adiadas: seção 9 de `visao-geral.md`.
