---
paths:
  - "docs/**/*.js"
  - "docs/**/*.css"
  - "docs/**/*.html"
---

# Regras do front-end (`docs/`)

- **Vanilla JS, sem build e sem dependências.** Única exceção: Chart.js 4 via
  CDN em `index.html`. Gráficos novos sem Chart.js são SVG à mão (`svgEl`).
- DOM com o helper `el(tag, props, filhos)` (ou `svgEl`), não `innerHTML` solto.
- Abas/sub-abas seguem o padrão `id` + `data-aba`/`data-subaba`; buscas por
  `button.subaba` sempre **escopadas** à seção (`#secao-…`).
- **Chart.js em canvas escondido trava em 0×0:** criar o gráfico só quando o
  container estiver visível (padrão `garantirGraficos…`), e destruir/recriar na
  troca de tema (`rerenderizarGraficos`; nas páginas de análise,
  `rerenderizarAnalise`).
- Cores pelos tokens de `style.css` (`:root` claro; escuro duplicado em
  `@media (prefers-color-scheme: dark) :root:not([data-theme="light"])` e
  `:root[data-theme="dark"]`). Pontos 2/1/0 usam uma paleta única
  (`--ok2`/`--ok1`/`--ok0-bg`) — sem vermelho para 0 pt.
- Cor/equipe de piloto **só** via `EQUIPES` e seus helpers (`corPiloto`,
  `corPilotoNoAno`, `coresEquipesPiloto`…) — não recriar mapas fixos.
- Ordenação padrão de jogadores: pontos desc, depois `player_id` asc.
- Telas se adaptam ao formato da temporada (`FORMATO`: `top_n`, bônus,
  compensação): o que não existe no ano é **omitido**, nunca mostrado vazio.
- Rotas por `?parâmetro` com recarga de página (sem SPA). Páginas fora da
  temporada ficam em `analise.js` (carregado depois do `app.js`, reaproveita
  seus helpers); o `app.js` só ganha o roteamento. As abas da temporada atual
  ficam como estão, salvo pedido do usuário.
- Antes de mudar o gerador Python, confirme se o dado já existe em `docs/data/`.
- Não há teste automatizado do front: verifique no preview `docs-static`
  (claro/escuro e largura de celular quando mexer em layout).

Detalhes e histórico das telas: mapa "Onde está cada tema" no `CLAUDE.md`
(`contexto/etapas/etapa-4-site.md`, `etapa-7-historico.md`, `etapa-8-navegacao-analises.md`).
