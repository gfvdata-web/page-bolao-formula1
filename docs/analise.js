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

async function renderPaginaJogadores() {
  entrarModoPagina("secao-jogadores", "👥", "Jogadores", "?menu", "Menu");
  document.getElementById("jogadores-status").textContent = "Em construção.";
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
