// Bolão F1 — páginas de navegação e análise entre temporadas (Etapa 8).
// Carregado depois do app.js e reaproveita os helpers globais de lá (el,
// carregarJson, SEASONS, entrarModoPagina, carregarTodas*...). O app.js só
// despacha a rota: ?menu, ?jogadores ou ?pilotos.

const ROTAS_ANALISE = {
  menu: renderPaginaMenu,
  jogadores: renderPaginaJogadores,
  pilotos: renderPaginaPilotos,
};

function rotaAnalisePedida() {
  const params = new URLSearchParams(location.search);
  return Object.keys(ROTAS_ANALISE).find((rota) => params.has(rota)) || null;
}

// Mensagem de erro padrão no status da página (o catch do main() escreve só
// nos status da temporada, que ficam escondidos aqui).
function erroPagina(statusId, erro) {
  console.error(erro);
  const status = document.getElementById(statusId);
  status.textContent = "Erro ao carregar os dados do bolão.";
  status.classList.add("erro");
}

// Card com título no visual do "Explore a temporada".
function cardAnalise(titulo, ...filhos) {
  return el("div", { class: "chamadas-card" }, [el("h2", {}, [titulo]), ...filhos]);
}

// Atalho em formato de chamada (ícone · título/descrição · seta), como link.
function chamadaLink(href, icone, titulo, texto) {
  return el("a", { class: "chamada", href }, [
    el("span", { class: "chamada__icone", "aria-hidden": "true" }, [icone]),
    el("span", { class: "chamada__texto" }, [el("strong", {}, [titulo]), el("span", {}, [texto])]),
    el("span", { class: "chamada__seta", "aria-hidden": "true" }, ["›"]),
  ]);
}

// ---------- Blocos reutilizáveis (jogadores e pilotos) ----------

// Todos os dados de todas as temporadas, carregados uma vez por página.
let _dadosAnalise = null;
async function carregarDadosAnalise() {
  if (!_dadosAnalise) {
    const [resultsPorAno, betsPorAno, standingsPorAno, hof] = await Promise.all([
      carregarTodosResults(),
      carregarTodosBets(),
      carregarTodasStandings(),
      carregarJson("./data/hall_of_fame.json"),
    ]);
    _dadosAnalise = { resultsPorAno, betsPorAno, standingsPorAno, hof };
  }
  return _dadosAnalise;
}

// Anos de seasons.json em ordem crescente.
function anosAnalise() {
  return (SEASONS?.temporadas || []).map((t) => String(t.ano)).sort();
}

// Anos do recorte: um ano, ou todos ("todos").
function anosDoRecorte(ano) {
  return ano === "todos" ? anosAnalise() : [ano];
}

const fmt1 = (n) => n.toFixed(1).replace(".", ",");
const fmt2 = (n) => n.toFixed(2).replace(".", ",");
const fmtPct = (n) => `${Math.round(n * 100)}%`;

// Re-render da página de análise aberta (a troca de tema recolore os gráficos).
let _rerenderAnalise = null;
function rerenderizarAnalise() {
  if (_rerenderAnalise) _rerenderAnalise();
}

// Grupo "Todas · 2026 · … · 2021" (visual do switch Pontos/Posição).
function seletorTemporada(valor, aoMudar) {
  const grupo = el("div", { class: "temporada-modo analise-anos", role: "group", "aria-label": "Temporada" });
  for (const op of ["todos", ...anosAnalise().reverse()]) {
    const ativo = op === valor;
    const b = el(
      "button",
      {
        type: "button",
        class: `temporada-modo__btn${ativo ? " temporada-modo__btn--ativo" : ""}`,
        "aria-pressed": String(ativo),
      },
      [op === "todos" ? "Todas" : op]
    );
    b.addEventListener("click", () => aoMudar(op));
    grupo.appendChild(b);
  }
  return grupo;
}

// Tabela que ordena ao tocar no cabeçalho. `colunas`: [{ chave, titulo, num,
// valor(l) (para ordenar; null vai sempre ao fim; sem valor = não ordena),
// celula(l), asc (sentido ao escolher a coluna; padrão crescente) }].
// `ordem` = { chave, asc } é alterado pelo clique, que chama `aoMudar`.
function tabelaOrdenavel(colunas, linhas, ordem, aoMudar, aoClicarLinha) {
  const col = colunas.find((c) => c.chave === ordem.chave) || colunas.find((c) => c.valor);
  const ordenadas = linhas.slice().sort((a, b) => {
    const va = col.valor(a);
    const vb = col.valor(b);
    if (va == null || vb == null) return (va == null) - (vb == null);
    const cmp = typeof va === "string" ? va.localeCompare(vb, "pt-BR") : va - vb;
    return ordem.asc ? cmp : -cmp;
  });

  const cabecalho = el(
    "tr",
    {},
    colunas.map((c) => {
      if (!c.valor) return el("th", { class: c.num ? "num" : "" }, [c.titulo]);
      const ativa = c === col;
      const th = el(
        "th",
        {
          class: `analise-th${c.num ? " num" : ""}${ativa ? " analise-th--ativa" : ""}`,
          "aria-sort": ativa ? (ordem.asc ? "ascending" : "descending") : "none",
          tabindex: "0",
        },
        [c.titulo, ativa ? (ordem.asc ? " ▲" : " ▼") : ""]
      );
      const ordenar = () => {
        if (ativa) ordem.asc = !ordem.asc;
        else Object.assign(ordem, { chave: c.chave, asc: c.asc !== false });
        aoMudar();
      };
      th.addEventListener("click", ordenar);
      th.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          ordenar();
        }
      });
      return th;
    })
  );

  const tbody = el("tbody");
  for (const l of ordenadas) {
    const tr = el(
      "tr",
      aoClicarLinha ? { class: "analise-linha", tabindex: "0" } : {},
      colunas.map((c) => el("td", { class: c.num ? "num" : "" }, [c.celula(l)]))
    );
    if (aoClicarLinha) {
      tr.addEventListener("click", (e) => {
        if (!e.target.closest("button, a")) aoClicarLinha(l);
      });
      tr.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && e.target === tr) aoClicarLinha(l);
      });
    }
    tbody.appendChild(tr);
  }
  return el("div", { class: "rendimento-tabela-wrap" }, [
    el("table", { class: "corridas-tabela analise-tabela" }, [el("thead", {}, [cabecalho]), tbody]),
  ]);
}

// Itens marcados para comparar no gráfico, com cor estável enquanto o item
// segue marcado (primeira cor livre da paleta dos jogadores).
function criarSelecaoCores() {
  const cores = new Map(); // item -> índice da paleta
  return {
    tem: (item) => cores.has(item),
    cor: (item) => corJogador(cores.get(item)),
    itens: () => [...cores.keys()],
    alternar(item) {
      if (cores.has(item)) {
        cores.delete(item);
        return;
      }
      const usados = new Set(cores.values());
      let i = 0;
      while (usados.has(i)) i++;
      cores.set(item, i);
    },
    limpar: () => cores.clear(),
  };
}

// Bolinha da coluna "comparar": liga/desliga o item no gráfico.
function botaoComparar(selecao, item, aoMudar) {
  const ligado = selecao.tem(item);
  const rotulo = ligado ? "Tirar do gráfico" : "Pôr no gráfico";
  const b = el(
    "button",
    {
      type: "button",
      class: "analise-comparar",
      "aria-pressed": String(ligado),
      "aria-label": rotulo,
      title: rotulo,
      style: ligado ? `--cor-chip:${selecao.cor(item)}` : "",
    },
    [el("span", { class: "rendimento-chip__ponto" })]
  );
  b.addEventListener("click", () => {
    selecao.alternar(item);
    aoMudar();
  });
  return b;
}

// Gráfico de linhas das páginas de análise. `series`: [{ rotulo, cor, dados }].
function graficoLinhasAnalise(canvas, labels, series, opcoes) {
  const corTexto = corCss("--texto-fraco");
  const corGrade = corCss("--borda");
  return new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: series.map((s) => ({
        label: s.rotulo,
        data: s.dados,
        borderColor: s.cor,
        backgroundColor: s.cor,
        tension: 0.2,
        spanGaps: true,
        pointRadius: 3,
        pointHoverRadius: 5,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: corTexto, usePointStyle: true, pointStyle: "circle", boxWidth: 8, boxHeight: 8 },
        },
        tooltip: {
          callbacks: {
            title: (itens) => (opcoes.tituloTooltip ? opcoes.tituloTooltip(itens[0].dataIndex) : itens[0].label),
            label: (ctx) => `${ctx.dataset.label}: ${opcoes.formatar(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: corTexto }, grid: { color: corGrade } },
        y: {
          reverse: !!opcoes.inverter,
          min: opcoes.min,
          max: opcoes.max,
          ticks: { color: corTexto, stepSize: opcoes.passo },
          grid: { color: corGrade },
          title: { display: true, text: opcoes.tituloY, color: corTexto },
        },
      },
    },
  });
}

// ---------- ?menu ----------

async function renderPaginaMenu() {
  const atual = String(SEASONS.atual);
  entrarModoPagina("secao-menu", "🧭", "Menu", location.pathname, atual);
  document.getElementById("btn-menu")?.classList.add("topo-menu--ativo");

  const status = document.getElementById("menu-status");
  const container = document.getElementById("menu-container");
  status.textContent = "Carregando…";
  try {
    const [hof, standingsPorAno] = await Promise.all([
      carregarJson("./data/hall_of_fame.json"),
      carregarTodasStandings(),
    ]);

    const botaoBusca = (rotulo, acao) => {
      const b = el("button", { type: "button", class: "ir-para-botao" }, [rotulo]);
      b.addEventListener("click", acao);
      return b;
    };

    status.textContent = "";
    container.replaceChildren(
      cardAnalise("Temporadas", renderListaAnosHall(hof, SEASONS, standingsPorAno, null)),
      cardAnalise(
        "Análises entre temporadas",
        el("div", { class: "chamadas-lista" }, [
          chamadaLink("?jogadores", "👥", "Jogadores", "Compare o desempenho dos jogadores, temporada a temporada"),
          chamadaLink("?pilotos", "🏎️", "Pilotos", "Rendimento, equipes e palpites de cada piloto desde 2021"),
        ]),
        el("div", { class: "menu-busca" }, [
          botaoBusca("👤 Ir para um jogador", escolherJogador),
          botaoBusca("🏎️ Ir para um piloto", escolherPiloto),
        ])
      )
    );
  } catch (erro) {
    erroPagina("menu-status", erro);
  }
}

// ---------- ?jogadores ----------

const estadoJogadores = {
  selecao: criarSelecaoCores(), // jogadores comparados (chips): tabela, gráfico e matriz
  metrica: "posicao", // gráfico: "posicao" | "acerto" | "media"
  ano: "todos", // recorte da tabela e da matriz
  ordem: { chave: "pontos", asc: false },
  grafico: null,
};

const METRICAS_JOGADOR = {
  posicao: { rotulo: "Posição", titulo: "Posição final no ranking, por temporada" },
  acerto: { rotulo: "Acerto", titulo: "Acerto (% do máximo possível), por temporada" },
  media: { rotulo: "Pts/corrida", titulo: "Pontos por corrida palpitada, por temporada" },
};

// Estatísticas por jogador no recorte de anos. Base de "acerto" e "pts/corrida"
// igual à do Hall of Fame (universoJogadores): só as corridas palpitadas, sem
// compensação. Palpites (exatas, no top6, piloto da rodada, favoritos) vêm do
// bets.json; ranking e pontos do standings.json; medalhas do hall_of_fame.json.
function agregarJogadores(dados, anos) {
  const mapa = new Map();
  const registro = (id, nome) => {
    if (!mapa.has(id)) {
      mapa.set(id, {
        id, nome, anos: [], ouro: 0, prata: 0, bronze: 0, pontos: 0,
        corridas: 0, feitos: 0, teto: 0, posicoes: [],
        palpites: 0, exatas: 0, noTop: 0, bonusN: 0, bonusAcertos: 0,
        rodadasBets: 0, porPiloto: new Map(),
      });
    }
    const r = mapa.get(id);
    r.nome = nome || r.nome;
    return r;
  };
  for (const a of anos) {
    const st = dados.standingsPorAno.get(a);
    if (!st) continue;
    const maxPts = Number(st.format?.max_points) || 0;
    for (const p of st.players || []) {
      const r = registro(p.player_id, p.name);
      r.anos.push(a);
      r.pontos += Number(p.total ?? p.total_somado ?? 0) || 0;
      r.posicoes.push({ ano: a, pos: p.position, de: st.players.length });
      let feitos = Number(p.carry_points) || 0;
      let corridas = Number(p.carry_rounds) || 0;
      for (const v of Object.values(p.per_round || {})) {
        feitos += Number(v) || 0;
        corridas++;
      }
      r.feitos += feitos;
      r.corridas += corridas;
      r.teto += corridas * maxPts;
    }
    const podio = dados.hof.anos.find((h) => String(h.ano) === a);
    if (podio) for (const m of ["ouro", "prata", "bronze"]) if (mapa.has(podio[m])) mapa.get(podio[m])[m]++;

    for (const jogador of Object.values(dados.betsPorAno.get(a)?.players || {})) {
      if (!mapa.has(jogador.player_id)) continue;
      const r = mapa.get(jogador.player_id);
      for (const rodada of Object.values(jogador.rounds || {})) {
        r.rodadasBets++;
        for (const det of rodada.top6_detail || []) {
          if (!det.guess) continue;
          r.palpites++;
          if (det.points >= 2) r.exatas++;
          if (det.points >= 1) r.noTop++;
          r.porPiloto.set(det.guess, (r.porPiloto.get(det.guess) || 0) + 1);
        }
        if (rodada.bonus_driver && rodada.bonus_guess != null) {
          r.bonusN++;
          if (rodada.bonus_points > 0) r.bonusAcertos++;
        }
      }
    }
  }
  for (const r of mapa.values()) {
    r.acerto = r.teto ? r.feitos / r.teto : null;
    r.media = r.corridas ? r.feitos / r.corridas : null;
    r.posMedia = r.posicoes.length ? r.posicoes.reduce((s, p) => s + p.pos, 0) / r.posicoes.length : null;
    r.medalhas = r.ouro + r.prata + r.bronze;
    r.favorito = [...r.porPiloto.entries()].sort((x, y) => y[1] - x[1] || x[0].localeCompare(y[0]))[0] || null;
  }
  return mapa;
}

async function renderPaginaJogadores() {
  entrarModoPagina("secao-jogadores", "👥", "Jogadores", "?menu", "Menu");
  const status = document.getElementById("jogadores-status");
  status.textContent = "Carregando…";
  try {
    const dados = await carregarDadosAnalise();
    // Começa comparando quem joga a temporada atual.
    const atual = dados.standingsPorAno.get(String(SEASONS.atual));
    for (const p of atual?.players || []) estadoJogadores.selecao.alternar(p.player_id);
    status.textContent = "";
    _rerenderAnalise = () => atualizarPaginaJogadores(dados);
    atualizarPaginaJogadores(dados);
  } catch (erro) {
    erroPagina("jogadores-status", erro);
  }
}

function atualizarPaginaJogadores(dados) {
  const est = estadoJogadores;
  const container = document.getElementById("jogadores-container");
  const atualizar = () => atualizarPaginaJogadores(dados);
  const anos = anosAnalise();
  const todos = agregarJogadores(dados, anos);
  const porAno = new Map(anos.map((a) => [a, agregarJogadores(dados, [a])]));
  const ids = [...todos.keys()].sort((x, y) => todos.get(x).nome.localeCompare(todos.get(y).nome, "pt-BR"));
  const comparados = est.selecao.itens();

  // --- chips: quem entra na comparação ---
  const chips = el("div", { class: "rendimento-jogadores" });
  for (const id of ids) {
    const ligado = est.selecao.tem(id);
    const chip = el(
      "button",
      {
        type: "button",
        class: "rendimento-chip",
        "aria-pressed": String(ligado),
        style: ligado ? `--cor-chip:${est.selecao.cor(id)}` : "",
      },
      [el("span", { class: "rendimento-chip__ponto" }), todos.get(id).nome]
    );
    chip.addEventListener("click", () => {
      est.selecao.alternar(id);
      atualizar();
    });
    chips.appendChild(chip);
  }
  const acao = (rotulo, fn) => {
    const b = el("button", { type: "button", class: "rendimento-jogadores__acao" }, [rotulo]);
    b.addEventListener("click", () => {
      fn();
      atualizar();
    });
    return b;
  };
  const acoes = el("div", { class: "rendimento-jogadores-acoes" }, [
    acao("Todos", () => ids.forEach((id) => est.selecao.tem(id) || est.selecao.alternar(id))),
    acao(`Só ${SEASONS.atual}`, () => {
      est.selecao.limpar();
      for (const p of dados.standingsPorAno.get(String(SEASONS.atual))?.players || []) est.selecao.alternar(p.player_id);
    }),
    acao("Limpar", () => est.selecao.limpar()),
  ]);

  const intro = el("div", { class: "secao-intro" }, [
    el("h3", {}, ["Comparativo entre jogadores"]),
    el("p", {}, [
      "Escolha nos chips quem entra na comparação (começa com quem joga ",
      String(SEASONS.atual),
      "). Toque no nome de um jogador na tabela para abrir o perfil dele.",
    ]),
  ]);

  // --- gráfico: evolução por temporada (independe do filtro de ano) ---
  const metrica = METRICAS_JOGADOR[est.metrica];
  const valorMetrica = (r) =>
    !r ? null : est.metrica === "posicao" ? r.posicoes[0]?.pos ?? null : est.metrica === "acerto" ? (r.acerto == null ? null : r.acerto * 100) : r.media;
  const series = comparados.map((id) => ({
    rotulo: todos.get(id).nome,
    cor: est.selecao.cor(id),
    dados: anos.map((a) => valorMetrica(porAno.get(a).get(id))),
  }));
  const trocaMetrica = el("div", { class: "temporada-modo", role: "group", "aria-label": "Métrica do gráfico" });
  for (const [chave, m] of Object.entries(METRICAS_JOGADOR)) {
    const ativo = chave === est.metrica;
    const b = el(
      "button",
      { type: "button", class: `temporada-modo__btn${ativo ? " temporada-modo__btn--ativo" : ""}`, "aria-pressed": String(ativo) },
      [m.rotulo]
    );
    b.addEventListener("click", () => {
      est.metrica = chave;
      atualizar();
    });
    trocaMetrica.appendChild(b);
  }
  const canvas = el("canvas");
  const wrapGrafico = el("div", { class: "rendimento-grafico-wrap" }, [
    el("div", { class: "temporada-grafico-cabecalho" }, [
      el("h3", { class: "temporada-grafico-titulo" }, [metrica.titulo]),
      trocaMetrica,
    ]),
    series.length
      ? el("div", { class: "temporada-grafico-canvas analise-grafico" }, [canvas])
      : el("p", { class: "status" }, ["Escolha ao menos um jogador nos chips."]),
  ]);

  // --- tabela comparativa (recorte de ano) ---
  const umAno = est.ano !== "todos";
  const recorte = umAno ? porAno.get(est.ano) : todos;
  const linhas = comparados.map((id) => recorte.get(id)).filter(Boolean);
  const pct = (n, d) => (d ? n / d : null);
  const celPct = (v) => (v == null ? "—" : fmtPct(v));
  const colunas = [
    {
      chave: "nome",
      titulo: "Jogador",
      valor: (l) => l.nome,
      celula: (l) =>
        el("a", { class: "analise-jogador", href: `?jogador=${encodeURIComponent(l.id)}`, style: `--cor-chip:${est.selecao.cor(l.id)}` }, [
          el("span", { class: "rendimento-chip__ponto" }),
          l.nome,
        ]),
    },
    {
      chave: "medalhas",
      titulo: "Medalhas",
      asc: false,
      valor: (l) => l.ouro * 1e4 + l.prata * 1e2 + l.bronze,
      celula: (l) =>
        l.medalhas ? ["🥇".repeat(l.ouro), "🥈".repeat(l.prata), "🥉".repeat(l.bronze)].join("") : "—",
    },
    umAno
      ? { chave: "posicao", titulo: "Posição", num: true, valor: (l) => l.posMedia, celula: (l) => `${l.posicoes[0].pos}º de ${l.posicoes[0].de}` }
      : { chave: "posicao", titulo: "Pos. média", num: true, valor: (l) => l.posMedia, celula: (l) => fmt1(l.posMedia) },
    ...(umAno ? [] : [{ chave: "anos", titulo: "Temp.", num: true, asc: false, valor: (l) => l.anos.length, celula: (l) => String(l.anos.length) }]),
    { chave: "corridas", titulo: "Corridas", num: true, asc: false, valor: (l) => l.corridas, celula: (l) => String(l.corridas) },
    { chave: "pontos", titulo: "Pontos", num: true, asc: false, valor: (l) => l.pontos, celula: (l) => String(l.pontos) },
    { chave: "media", titulo: "Pts/corrida", num: true, asc: false, valor: (l) => l.media, celula: (l) => (l.media == null ? "—" : fmt2(l.media)) },
    { chave: "acerto", titulo: "Acerto", num: true, asc: false, valor: (l) => l.acerto, celula: (l) => celPct(l.acerto) },
    { chave: "exatas", titulo: "Exatas", num: true, asc: false, valor: (l) => pct(l.exatas, l.palpites), celula: (l) => celPct(pct(l.exatas, l.palpites)) },
    { chave: "noTop", titulo: "No top6", num: true, asc: false, valor: (l) => pct(l.noTop, l.palpites), celula: (l) => celPct(pct(l.noTop, l.palpites)) },
    { chave: "bonus", titulo: "Piloto rodada", num: true, asc: false, valor: (l) => pct(l.bonusAcertos, l.bonusN), celula: (l) => celPct(pct(l.bonusAcertos, l.bonusN)) },
    {
      chave: "favorito",
      titulo: "Mais apostado",
      valor: (l) => (l.favorito ? l.favorito[0] : null),
      celula: (l) => (l.favorito ? el("span", {}, [chipPilotoEquipes(l.favorito[0], l.anos), ` ${l.favorito[1]}×`]) : "—"),
    },
  ];
  const blocoTabela = el("div", {}, [
    el("div", { class: "analise-filtros" }, [
      seletorTemporada(est.ano, (ano) => {
        est.ano = ano;
        atualizar();
      }),
    ]),
    linhas.length
      ? tabelaOrdenavel(colunas, linhas, est.ordem, atualizar)
      : el("p", { class: "status" }, ["Nenhum jogador escolhido disputou essa temporada."]),
    el("p", { class: "analise-nota" }, [
      "Acerto e pts/corrida contam só as corridas palpitadas (sem compensação). Exatas = palpites do top6 na posição certa; ",
      "no top6 = palpites que caíram no top6 real (exata ou não); piloto rodada = acertos da posição exata do piloto da rodada.",
    ]),
  ]);

  container.replaceChildren(
    intro,
    chips,
    acoes,
    wrapGrafico,
    cardAnalise(umAno ? `Comparativo — ${est.ano}` : "Comparativo — todas as temporadas", blocoTabela),
    cardAnalise("Em quem cada um aposta", matrizFavoritos(linhas, est.selecao))
  );

  if (est.grafico) est.grafico.destroy();
  est.grafico = null;
  if (series.length) {
    const posicao = est.metrica === "posicao";
    const maxPos = Math.max(1, ...series.flatMap((s) => s.dados.filter((v) => v != null)));
    est.grafico = graficoLinhasAnalise(canvas, anos, series, {
      inverter: posicao,
      min: posicao ? 1 : undefined,
      max: posicao ? maxPos + 1 : undefined,
      passo: posicao ? 1 : undefined,
      tituloY: metrica.rotulo,
      formatar: (v) => (posicao ? `${v}º` : est.metrica === "acerto" ? `${fmt1(v)}%` : fmt2(v)),
    });
  }
}

// Matriz jogador × pilotos mais apostados: % das corridas palpitadas em que o
// jogador pôs o piloto no top6 (fundo mais forte = aposta mais). Mostra onde os
// palpites do grupo divergem.
function matrizFavoritos(linhas, selecao) {
  if (!linhas.length) return el("p", { class: "status" }, ["Escolha ao menos um jogador nos chips."]);
  const total = new Map();
  for (const l of linhas) for (const [cod, n] of l.porPiloto) total.set(cod, (total.get(cod) || 0) + n);
  const pilotos = [...total.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10).map(([cod]) => cod);
  const tabela = el("table", { class: "corridas-tabela analise-matriz" }, [
    el("thead", {}, [el("tr", {}, [el("th", {}, ["Jogador"]), ...pilotos.map((cod) => el("th", { class: "num" }, [cod]))])]),
    el(
      "tbody",
      {},
      linhas
        .slice()
        .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
        .map((l) =>
          el("tr", {}, [
            el("td", {}, [
              el("span", { class: "analise-jogador", style: `--cor-chip:${selecao.cor(l.id)}` }, [
                el("span", { class: "rendimento-chip__ponto" }),
                l.nome,
              ]),
            ]),
            ...pilotos.map((cod) => {
              const v = l.rodadasBets ? (l.porPiloto.get(cod) || 0) / l.rodadasBets : 0;
              return el(
                "td",
                { class: "num analise-matriz__cel", style: `--intensidade:${Math.round(v * 55)}%` },
                [v ? fmtPct(v) : "—"]
              );
            }),
          ])
        )
    ),
  ]);
  return el("div", {}, [
    el("div", { class: "rendimento-tabela-wrap" }, [tabela]),
    el("p", { class: "analise-nota" }, [
      "% das corridas palpitadas em que o jogador colocou o piloto no top6. Colunas: os 10 pilotos mais apostados pelos jogadores escolhidos, no recorte de temporada acima.",
    ]),
  ]);
}

// ---------- ?pilotos ----------

const estadoPilotos = {
  ano: "todos",
  equipe: "todas",
  ordem: { chave: "posMedia", asc: true },
  selecao: criarSelecaoCores(),
  grafico: null,
};

// Equipe de um piloto numa rodada: dado da Jolpica (results.equipes), com o
// mapa fixo do app.js como reserva.
function equipeNaRodada(rodada, cod, ano) {
  return (rodada && rodada.equipes && rodada.equipes[cod]) || equipePilotoNoAno(cod, ano);
}

// Estatísticas por piloto no recorte (ano ou "todos"; equipe ou "todas").
// Conta só as corridas do bolão (as de docs/data/<ano>/results.json). Com
// filtro de equipe, entram só as rodadas em que o piloto corria por ela.
// `serie`: posição média por ano (recorte "todos") ou por rodada (um ano).
function agregarPilotos(dados, ano, equipe) {
  const mapa = new Map();
  const registro = (cod) => {
    if (!mapa.has(cod)) {
      mapa.set(cod, {
        cod, qualis: 0, somaPos: 0, melhor: null, poles: 0, q3: 0,
        equipes: [], anos: [], apostas: 0, pontos: 0, serie: new Map(),
      });
    }
    return mapa.get(cod);
  };
  const vale = (rodada, cod, a) => equipe === "todas" || equipeNaRodada(rodada, cod, a) === equipe;

  for (const a of anosDoRecorte(ano)) {
    const res = dados.resultsPorAno.get(a);
    if (!res) continue;
    for (const [rnd, rodada] of Object.entries(res.rounds || {})) {
      (rodada.order || []).forEach((cod, i) => {
        if (!vale(rodada, cod, a)) return;
        const r = registro(cod);
        const pos = i + 1;
        r.qualis++;
        r.somaPos += pos;
        r.melhor = r.melhor == null ? pos : Math.min(r.melhor, pos);
        if (pos === 1) r.poles++;
        if ((rodada.fases ? rodada.fases[cod] : pos <= 10 ? 3 : 1) === 3) r.q3++;
        const eq = equipeNaRodada(rodada, cod, a);
        if (eq && !r.equipes.includes(eq)) r.equipes.push(eq);
        if (!r.anos.includes(a)) r.anos.push(a);
        const chave = ano === "todos" ? a : rnd;
        const ponto = r.serie.get(chave) || { soma: 0, n: 0 };
        ponto.soma += pos;
        ponto.n++;
        r.serie.set(chave, ponto);
      });
    }
    const bets = dados.betsPorAno.get(a);
    for (const jogador of Object.values((bets && bets.players) || {})) {
      for (const [rnd, rodada] of Object.entries(jogador.rounds || {})) {
        for (const det of rodada.top6_detail || []) {
          if (!det.guess || !mapa.has(det.guess) || !vale(res.rounds[rnd], det.guess, a)) continue;
          const r = mapa.get(det.guess);
          r.apostas++;
          r.pontos += det.points || 0;
        }
      }
    }
  }
  for (const r of mapa.values()) r.posMedia = r.somaPos / r.qualis;
  return [...mapa.values()];
}

// Equipes e tamanho máximo do grid no recorte de anos (filtro e eixo).
function equipesEGridNoRecorte(dados, ano) {
  const nomes = new Set();
  let maxGrid = 0;
  for (const a of anosDoRecorte(ano)) {
    for (const rodada of Object.values(dados.resultsPorAno.get(a)?.rounds || {})) {
      const order = rodada.order || [];
      maxGrid = Math.max(maxGrid, order.length);
      for (const cod of order) {
        const eq = equipeNaRodada(rodada, cod, a);
        if (eq) nomes.add(eq);
      }
    }
  }
  return { equipes: [...nomes].sort((x, y) => x.localeCompare(y, "pt-BR")), maxGrid };
}

async function renderPaginaPilotos() {
  entrarModoPagina("secao-pilotos-analise", "🏎️", "Pilotos", "?menu", "Menu");
  const status = document.getElementById("pilotos-analise-status");
  status.textContent = "Carregando…";
  try {
    const dados = await carregarDadosAnalise();
    status.textContent = "";
    _rerenderAnalise = () => atualizarPaginaPilotos(dados);
    atualizarPaginaPilotos(dados);
  } catch (erro) {
    erroPagina("pilotos-analise-status", erro);
  }
}

function atualizarPaginaPilotos(dados) {
  const est = estadoPilotos;
  const container = document.getElementById("pilotos-analise-container");
  const atualizar = () => atualizarPaginaPilotos(dados);
  const umAno = est.ano !== "todos";

  const { equipes, maxGrid } = equipesEGridNoRecorte(dados, est.ano);
  if (est.equipe !== "todas" && !equipes.includes(est.equipe)) est.equipe = "todas";
  const linhas = agregarPilotos(dados, est.ano, est.equipe);

  // Gráfico: mantém quem segue no recorte; se não sobrar ninguém, marca os 5
  // de melhor posição média (com 3+ qualis, para não puxar reserva de 1 corrida).
  const presentes = new Set(linhas.map((l) => l.cod));
  for (const cod of est.selecao.itens()) if (!presentes.has(cod)) est.selecao.alternar(cod);
  if (!est.selecao.itens().length) {
    linhas
      .filter((l) => l.qualis >= 3)
      .sort((a, b) => a.posMedia - b.posMedia)
      .slice(0, 5)
      .forEach((l) => est.selecao.alternar(l.cod));
  }

  const selectEquipe = el("select", { "aria-label": "Equipe" }, [
    el("option", { value: "todas" }, ["Todas as equipes"]),
    ...equipes.map((eq) => el("option", { value: eq }, [eq])),
  ]);
  selectEquipe.value = est.equipe;
  selectEquipe.addEventListener("change", () => {
    est.equipe = selectEquipe.value;
    est.selecao.limpar();
    atualizar();
  });

  const intro = el("div", { class: "secao-intro" }, [
    el("h3", {}, ["Pilotos no quali e nos palpites"]),
    el("p", {}, [
      "Desempenho real de cada piloto nos qualis do bolão e quanto ele rendeu nos palpites de top6 do grupo. ",
      "Toque no cabeçalho para ordenar, na bolinha para comparar no gráfico e na linha para abrir o perfil do piloto.",
    ]),
  ]);
  const filtros = el("div", { class: "analise-filtros" }, [
    seletorTemporada(est.ano, (ano) => {
      est.ano = ano;
      atualizar();
    }),
    el("div", { class: "filtro-jogador analise-filtro-select" }, [selectEquipe]),
  ]);

  // Eixo x: temporadas (recorte "todos") ou rodadas do ano.
  let chaves;
  let labels;
  let tituloTooltip = null;
  if (umAno) {
    const rounds = Object.values(dados.resultsPorAno.get(est.ano)?.rounds || {}).sort((a, b) => a.round - b.round);
    chaves = rounds.map((r) => String(r.round));
    labels = rounds.map((r) => `R${r.round}`);
    tituloTooltip = (i) => `R${rounds[i].round} · ${rounds[i].race}`;
  } else {
    chaves = anosAnalise();
    labels = chaves;
  }
  const porCod = new Map(linhas.map((l) => [l.cod, l]));
  const series = est.selecao.itens().map((cod) => {
    const serie = porCod.get(cod).serie;
    return {
      rotulo: cod,
      cor: est.selecao.cor(cod),
      dados: chaves.map((k) => (serie.has(k) ? serie.get(k).soma / serie.get(k).n : null)),
    };
  });
  // Eixo y justo nos dados (posições médias ficam espremidas num eixo até P22).
  const pior = Math.max(1, ...series.flatMap((s) => s.dados.filter((v) => v != null)));
  const canvas = el("canvas");
  const wrapGrafico = el("div", { class: "rendimento-grafico-wrap" }, [
    el("h3", { class: "rendimento-grafico-titulo" }, [
      umAno ? `Posição no quali, corrida a corrida — ${est.ano}` : "Posição média no quali, por temporada",
    ]),
    series.length
      ? el("div", { class: "temporada-grafico-canvas analise-grafico" }, [canvas])
      : el("p", { class: "status" }, ["Marque a bolinha de um piloto na tabela para vê-lo aqui."]),
  ]);

  const colunas = [
    { chave: "cmp", titulo: "", celula: (l) => botaoComparar(est.selecao, l.cod, atualizar) },
    { chave: "cod", titulo: "Piloto", valor: (l) => l.cod, celula: (l) => chipPilotoEquipes(l.cod, l.anos) },
    { chave: "equipes", titulo: "Equipe", valor: (l) => l.equipes.join(" · "), celula: (l) => l.equipes.join(" · ") },
    ...(umAno
      ? []
      : [{ chave: "anos", titulo: "Temp.", num: true, asc: false, valor: (l) => l.anos.length, celula: (l) => String(l.anos.length) }]),
    { chave: "qualis", titulo: "Qualis", num: true, asc: false, valor: (l) => l.qualis, celula: (l) => String(l.qualis) },
    { chave: "posMedia", titulo: "Pos. média", num: true, valor: (l) => l.posMedia, celula: (l) => fmt1(l.posMedia) },
    { chave: "melhor", titulo: "Melhor", num: true, valor: (l) => l.melhor, celula: (l) => `P${l.melhor}` },
    { chave: "poles", titulo: "Poles", num: true, asc: false, valor: (l) => l.poles, celula: (l) => String(l.poles) },
    { chave: "q3", titulo: "Q3", num: true, asc: false, valor: (l) => l.q3 / l.qualis, celula: (l) => fmtPct(l.q3 / l.qualis) },
    { chave: "apostas", titulo: "Apostas top6", num: true, asc: false, valor: (l) => l.apostas, celula: (l) => String(l.apostas) },
    { chave: "pontos", titulo: "Pts no top6", num: true, asc: false, valor: (l) => l.pontos, celula: (l) => String(l.pontos) },
    {
      chave: "ptsAposta",
      titulo: "Pts / aposta",
      num: true,
      asc: false,
      valor: (l) => (l.apostas ? l.pontos / l.apostas : null),
      celula: (l) => (l.apostas ? fmt2(l.pontos / l.apostas) : "—"),
    },
  ];
  const tabela = tabelaOrdenavel(colunas, linhas, est.ordem, atualizar, (l) => {
    location.href = `${location.pathname}?piloto=${encodeURIComponent(l.cod)}`;
  });

  if (est.grafico) est.grafico.destroy();
  est.grafico = null;
  container.replaceChildren(intro, filtros, wrapGrafico, tabela);
  if (series.length) {
    est.grafico = graficoLinhasAnalise(canvas, labels, series, {
      inverter: true,
      min: 1,
      max: Math.min(maxGrid, Math.ceil(pior) + 1),
      passo: 1,
      tituloY: umAno ? "Posição" : "Posição média",
      formatar: (v) => (umAno ? `P${v}` : `P${fmt1(v)}`),
      tituloTooltip,
    });
  }
}

// ---------- Complementos do perfil do piloto (?piloto, app.js) ----------

// ano -> equipes do piloto naquele ano, na ordem em que apareceram (troca no
// meio da temporada vira duas). Fonte: results.equipes de cada rodada.
function equipesDoPilotoPorAno(resultsPorAno, codigo) {
  const porAno = new Map();
  for (const ano of anosAnalise()) {
    const rounds = Object.values(resultsPorAno.get(ano)?.rounds || {}).sort((a, b) => a.round - b.round);
    for (const rodada of rounds) {
      if (!(rodada.order || []).includes(codigo)) continue;
      const eq = equipeNaRodada(rodada, codigo, ano);
      if (!eq) continue;
      if (!porAno.has(ano)) porAno.set(ano, []);
      if (!porAno.get(ano).includes(eq)) porAno.get(ano).push(eq);
    }
  }
  return porAno;
}

// "Ferrari 2021–2024 · Mercedes 2025–2026": anos seguidos na mesma equipe
// viram um intervalo.
function resumoEquipes(equipesPorAno) {
  const trechos = [];
  for (const [ano, equipes] of equipesPorAno) {
    for (const eq of equipes) {
      const ultimo = trechos[trechos.length - 1];
      if (ultimo && ultimo.eq === eq && Number(ano) - Number(ultimo.fim) <= 1) ultimo.fim = ano;
      else trechos.push({ eq, ini: ano, fim: ano });
    }
  }
  return trechos.map((t) => `${t.eq} ${t.ini === t.fim ? t.ini : `${t.ini}–${t.fim}`}`).join(" · ") || "—";
}

// Tabela temporada a temporada do piloto: quali real + palpites do grupo.
function tabelaPilotoAnoAno(codigo, dados) {
  const linhas = anosAnalise()
    .map((ano) => ({ ano, ...agregarPilotos(dados, ano, "todas").find((l) => l.cod === codigo) }))
    .filter((l) => l.qualis)
    .reverse();
  const td = (v, num = true) => el("td", { class: num ? "num" : "" }, [v]);
  const tabela = el("table", { class: "corridas-tabela analise-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["Temporada"]),
        el("th", {}, ["Equipe"]),
        ...["Qualis", "Pos. média", "Melhor", "Poles", "Q3", "Apostas top6", "Pts no top6", "Pts / aposta"].map((t) =>
          el("th", { class: "num" }, [t])
        ),
      ]),
    ]),
    el(
      "tbody",
      {},
      linhas.map((l) =>
        el("tr", {}, [
          td(l.ano, false),
          td(l.equipes.join(" / "), false),
          td(String(l.qualis)),
          td(fmt1(l.posMedia)),
          td(`P${l.melhor}`),
          td(String(l.poles)),
          td(fmtPct(l.q3 / l.qualis)),
          td(String(l.apostas)),
          td(String(l.pontos)),
          td(l.apostas ? fmt2(l.pontos / l.apostas) : "—"),
        ])
      )
    ),
  ]);
  return el("div", { class: "rendimento-grafico-wrap" }, [
    el("h3", { class: "rendimento-grafico-titulo" }, ["Temporada a temporada"]),
    el("div", { class: "rendimento-tabela-wrap" }, [tabela]),
    el("p", { class: "analise-nota" }, [
      "Só as corridas do bolão. Apostas/pontos: quantas vezes o grupo pôs o piloto no top6 e quanto isso rendeu.",
    ]),
  ]);
}
