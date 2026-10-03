---
paths:
  - "bolao/**/*.py"
  - "tests/**/*.py"
---

# Regras do núcleo Python (`bolao/`, `tests/`)

- **Só biblioteca padrão** (não há `requirements.txt`; o workflow não faz
  `pip install`). Rede via `urllib`.
- Na Jolpica, `fetch_*` (rede) fica separado de `build_*` (transformação pura);
  testes exercitam o `build_*` com fixtures, sem rede.
- Testes: `unittest.TestCase` rodados com `python -m pytest tests/ -q`, sempre
  offline e com workspace isolado (`tempfile`) quando gravam arquivos.
- Formato de cada temporada (top N, bônus, pontos, compensação) vem **só** de
  `bolao/formats.py` (`SeasonFormat`) — não espalhar `if ano == …`.
- `race_id = "{season}-{round:02d}"` em todo o projeto.
- JSON gerado é **determinístico** (sem timestamp), para diffs limpos.
- `ParseError` diante de ambiguidade real é o comportamento desejado (não
  adivinhar). `resolve_race` e `normalize_driver` **não** falham sozinhos
  (sempre devolvem algo) — cabeçalho com fraseado novo exige conferir o resumo.
- Mudança em formato consumido por outra etapa: registrar conforme
  "Onde registrar o que for decidido" no `CLAUDE.md`.

Formatos e decisões por módulo: mapa "Onde está cada tema" no `CLAUDE.md`.
