# Etapa 8 — Navegação + análises entre temporadas

> Movido do antigo `CONTEXTO.md` (seção 8) sem alteração de conteúdo. Status da etapa: ver `contexto/status.md`.

- **Objetivo:** dar acesso fácil às temporadas antigas e criar análises entre
  temporadas por jogador e por piloto, **sem mexer** nas abas da temporada
  (Ranking, Rendimento, Pilotos, Hall of Fame, "Ir para" ficam como estão).
- **Depende de:** Etapas 4 e 7 (dados de todas as temporadas em `docs/data/`).
- **Mapa de páginas** (mesmo `index.html`, rotas por `?`, recarrega a página):
  ```
  /               temporada atual (sempre; intocada)
  ?menu           hub: Temporadas (atual → /, antigas → ?ano) · Jogadores · Pilotos
  ?jogadores      comparativo do grupo (chips: começa com os da temporada atual)
    ?jogador=id   perfil individual (o existente)
  ?pilotos        todos os pilotos 2021–atual, filtros temporada/equipe
    ?piloto=COD   perfil do piloto (existente, ampliado: equipes, ano a ano)
  ?ano=YYYY       temporada antiga (intocada)
  ```
- **Botão 🧭 Menu** no topo, ao lado do switch claro/escuro, em todas as páginas.
- **Voltar (regra única):** "←" sobe um nível na árvore, independente da
  origem: `?menu`→`/`; `?jogadores`/`?pilotos`/`?ano`→`?menu`;
  `?jogador`→`?jogadores`; `?piloto`→`?pilotos`. Sem diferença desktop/celular.
- **Links entre perfis:** código do piloto em "Apostas por piloto" (`?jogador`)
  → `?piloto`; nome em "Quem mais aposta" (`?piloto`) → `?jogador`.
- **Recorte de tempo:** por padrão ano a ano; somar só onde fizer sentido.
- **Equipes:** gravar a equipe de cada piloto por rodada no `results.json`
  (vem do quali na Jolpica), preenchendo 2021–atual.
- **Código:** páginas novas em `docs/analise.js` (carregado depois do
  `app.js`, reaproveita seus helpers globais); `app.js` só ganha o roteamento.
- **Links das tabelas da temporada para os perfis:** aprovados e entregues em
  2026-10-03 (ver "Ajuste posterior: links para perfis" no fim).
- **Entregue v1 (2026-10-03), aguardando revisão do usuário:**
  - Topo: um único `#btn-voltar` (`mostrarVoltar`) + `#btn-menu`
    (`<a href="?menu">`). `entrarModoPagina()` (app.js) monta toda página fora
    da temporada. `main()` roda no `DOMContentLoaded` e despacha
    `ROTAS_ANALISE` (analise.js) antes de `?jogador`/`?piloto`/`?ano`.
  - `?menu`: lista de temporadas (`renderListaAnosHall(..., aqui=null)`),
    atalhos Jogadores/Pilotos e busca rápida (`escolherJogador/escolherPiloto`,
    também usados pelo "Ir para").
  - `?pilotos` (`agregarPilotos`): filtros temporada/equipe (equipe por
    rodada), tabela ordenável, bolinha = compara no gráfico (posição média por
    ano, ou por corrida num ano). Linha → `?piloto`.
  - `?jogadores` (`agregarJogadores`): chips (início = temporada atual),
    gráfico por temporada (Posição/Acerto/Pts por corrida), comparativo com
    filtro de ano, matriz "em quem cada um aposta". Nome → `?jogador`.
  - `?piloto`: card Equipes, violino rotulado pela equipe real, tabela
    "Temporada a temporada"; nomes em "Quem mais aposta" → `?jogador`.
    `?jogador`: código do piloto em "Apostas por piloto" → `?piloto`.
  - Blocos comuns em analise.js: `tabelaOrdenavel`, `seletorTemporada`,
    `criarSelecaoCores`, `graficoLinhasAnalise`, `rerenderizarAnalise` (tema).
  - Estatísticas de piloto contam só as corridas do bolão
    (`docs/data/<ano>/results.json`).
- **Base de equipes (fonte única de nome/cor):**
  - `data/equipes.json` (editado à mão): `{ano: {chaveJolpica: {nome, cor}}}` —
    nome e cor **daquele ano** (ex.: 2025 `RB` → "Racing Bulls", 2026 `Audi`).
    Equipe nova/renomeada = adicionar aqui; `tests/test_equipes.py` falha se
    alguma equipe dos resultados ficar sem nome/cor.
  - `site.py` → `gerar_equipes()` gera `docs/data/equipes.json` em todo build:
    `{ano: {equipes: {chave: {nome, cor}}, pilotos: {cod: {chave: qualis}}}}`,
    contando **todas** as rodadas de `data/<ano>/results` (ordem cronológica;
    troca no meio do ano = duas chaves).
  - `app.js` carrega em `EQUIPES` no início do `main()`. Helpers:
    `infoEquipe`, `chavesEquipesPiloto`, `equipePilotoNoAno` /
    `corPilotoNoAno` (equipe principal = mais qualis no ano), `corPiloto`
    (temporada exibida), `coresEquipesPiloto` (uma bolinha por nome de equipe).
    Os antigos mapas fixos `CORES_PILOTO(_ANO)`/`EQUIPE_PILOTO(_ANO)` saíram.

**Ajuste posterior: links para perfis nas tabelas da temporada (2026-10-03).**
- Helpers em `app.js`: `linkJogador(id, filhos)` e `chipPilotoLink(cod)`
  (classe `.link-perfil`: cor do texto, destaque + sublinhado no hover).
- Piloto só vira link se estiver no grid real da temporada exibida
  (`pilotoTemPerfil`, sobre `resultsGlobais`) — código de palpite com erro de
  digitação (ex.: `LEV` em 2025) continua texto, sem levar a perfil inválido.
- Onde: nome do jogador em Ranking/Geral, Corridas (tabela e matriz),
  Simulador, cabeçalho da Pontuação da corrida e Rendimento (modo jogador);
  piloto na coluna Resultado/piloto da rodada da Pontuação da corrida,
  Preferência piloto, Rendimento (modo piloto) e aba Pilotos (código no SVG,
  `.link-perfil-svg`). Chips de filtro e cards dos gráficos **não** viram link
  (servem para ligar/desligar séries). Vale também no modo histórico (`?ano`).
