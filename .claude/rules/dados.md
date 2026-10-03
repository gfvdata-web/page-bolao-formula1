---
paths:
  - "data/**"
  - "docs/data/**"
---

# Regras dos dados (`data/`, `docs/data/`)

- `docs/data/**` é **gerado** por `python -m bolao.site build` — não editar à
  mão. Exceções escritas à mão: `docs/data/hall_of_fame.json` e
  `docs/data/regras.json`.
- `data/equipes.json` é editado à mão (nome e cor **daquele ano**); equipe nova
  ou renomeada entra aqui — `tests/test_equipes.py` acusa se faltar.
- **Não inventar códigos de piloto**: vêm da entry list real (Jolpica).
- `python -m bolao.jolpica calendar` sobrescreve os aliases manuais do
  `calendar.json` — reaplicá-los depois.
- Correção de palpite antigo: editar o CSV da temporada e rodar
  `python -m bolao.historico build --season AAAA` + `python -m bolao.site build`.
- Temporadas fechadas: o placar publicado pelo grupo e o `ranking_final.json`
  mandam; `pontos_avulsos.json` só entra com `"incluir_no_ranking": true`.
  Decisões em `contexto/etapas/etapa-7-historico.md` (não reabrir).
- Export do WhatsApp e derivados ficam em `historico_wpp/`, **fora do Git**.

Formatos de cada arquivo: mapa "Onde está cada tema" no `CLAUDE.md`.
