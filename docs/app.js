// Bolão F1 2026 — Etapa 4 (site estático, vanilla JS)

// Cor aproximada por equipe 2026, mapeada por código de piloto (3 letras).
// Puramente decorativo (identifica a equipe no círculo ao lado do código).
const CORES_PILOTO = {
  VER: "#3671C6", HAD: "#3671C6", // Red Bull
  NOR: "#FF8000", PIA: "#FF8000", // McLaren
  RUS: "#27F4D2", ANT: "#27F4D2", // Mercedes
  LEC: "#E8002D", HAM: "#E8002D", // Ferrari
  ALB: "#64C4FF", SAI: "#64C4FF", // Williams
  ALO: "#229971", STR: "#229971", // Aston Martin
  GAS: "#0090FF", COL: "#0090FF", // Alpine
  BEA: "#B6BABD", OCO: "#B6BABD", // Haas
  LAW: "#6692FF", LIN: "#6692FF", // Racing Bulls
  BOR: "#00E701", HUL: "#00E701", // Sauber
  PER: "#FFD100", BOT: "#FFD100", // Cadillac
};

function corPiloto(codigo) {
  return CORES_PILOTO[codigo] || "#9aa0a8";
}

// Paleta cíclica para linhas de jogador nos gráficos (decorativo, sem relação com equipes).
const PALETA_JOGADOR = [
  "#e10600", "#1e9e5a", "#3671C6", "#FF8000", "#c99a00",
  "#8e44ad", "#00b8d9", "#e91e63", "#795548", "#009688",
  "#607d8b", "#ff5722",
];

function corJogador(indice) {
  return PALETA_JOGADOR[indice % PALETA_JOGADOR.length];
}

function corCss(variavel) {
  return getComputedStyle(document.documentElement).getPropertyValue(variavel).trim();
}

async function carregarJson(caminho) {
  const resp = await fetch(caminho);
  if (!resp.ok) throw new Error(`Falha ao buscar ${caminho}: ${resp.status}`);
  return resp.json();
}

function el(tag, props = {}, filhos = []) {
  const node = document.createElement(tag);
  for (const [chave, valor] of Object.entries(props)) {
    if (chave === "class") node.className = valor;
    else if (chave === "html") node.innerHTML = valor;
    else node.setAttribute(chave, valor);
  }
  for (const filho of filhos) {
    if (filho == null) continue;
    node.appendChild(typeof filho === "string" ? document.createTextNode(filho) : filho);
  }
  return node;
}

function chipPiloto(codigo) {
  return el("span", { class: "piloto-chip" }, [
    el("span", { class: "piloto-bolinha", style: `background:${corPiloto(codigo)}` }),
    codigo,
  ]);
}

function badgePonto(pts) {
  return el("span", { class: `ponto-badge ponto-${pts}` }, [`${pts}pt`]);
}

// ---------- Ranking ----------

function renderRanking(standings) {
  const container = document.getElementById("ranking-container");
  const tabela = el("table", { class: "ranking-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["#"]),
        el("th", {}, ["Jogador"]),
        el("th", { class: "num" }, ["Pontos"]),
        el("th", { class: "num" }, ["Média/Corrida"]),
        el("th", { class: "num" }, ["Pontos Extra"]),
        el("th", { class: "num" }, ["Rodadas"]),
      ]),
    ]),
  ]);

  const tbody = el("tbody");
  const medalhas = { 1: "🥇", 2: "🥈", 3: "🥉" };

  for (const jogador of standings.players) {
    const nomeCell = el("td", {}, [jogador.name]);
    if (jogador.compensation_total) {
      nomeCell.appendChild(
        el("span", { class: "compensacao-nota" }, [
          `+${jogador.compensation_total} pt de compensação (${jogador.compensated_rounds.length} rodada(s) sem palpite)`,
        ])
      );
    }
    tbody.appendChild(
      el("tr", {}, [
        el("td", { class: "pos-medalha" }, [medalhas[jogador.position] || String(jogador.position)]),
        nomeCell,
        el("td", { class: "num" }, [String(jogador.total)]),
        el("td", { class: "num" }, [jogador.avg_points.toFixed(1)]),
        el("td", { class: "num" }, [String(jogador.bonus_total)]),
        el("td", { class: "num" }, [String(jogador.rounds_played)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  container.replaceChildren(tabela);
}

// ---------- Palpites por jogador ----------

function popularSelectJogadores(bets) {
  const select = document.getElementById("select-jogador");
  const jogadores = Object.values(bets.players).sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  select.replaceChildren(
    ...jogadores.map((j) => el("option", { value: j.player_id }, [j.name]))
  );
  return jogadores;
}

function cardTop6(rodada) {
  const tabela = el("table", { class: "top6-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["Pos"]),
        el("th", {}, ["Palpite"]),
        el("th", {}, ["Real"]),
        el("th", {}, ["Pts"]),
      ]),
    ]),
  ]);
  const tbody = el("tbody");
  for (const linha of rodada.top6_detail) {
    tbody.appendChild(
      el("tr", {}, [
        el("td", { class: "pos-col" }, [`P${linha.pos}`]),
        el("td", {}, [chipPiloto(linha.guess)]),
        el("td", {}, [chipPiloto(linha.real)]),
        el("td", {}, [badgePonto(linha.points)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  return tabela;
}

function linhaBonus(rodada) {
  return el("div", { class: "bonus-linha" }, [
    el("span", { class: "bonus-linha__label" }, ["Piloto da rodada:"]),
    chipPiloto(rodada.bonus_driver),
    el("span", { class: "bonus-linha__label" }, [`· chute P${rodada.bonus_guess} · real P${rodada.bonus_real_pos} ·`]),
    badgePonto(rodada.bonus_points),
  ]);
}

function cardRodada(rodada, data) {
  return el("div", { class: "rodada-card" }, [
    el("div", { class: "rodada-card__header" }, [
      el("div", {}, [
        el("span", { class: "rodada-card__titulo" }, [`R${rodada.round} · ${rodada.race}`]),
        el("span", { class: "rodada-card__data" }, [data || ""]),
      ]),
      el("div", { class: "rodada-card__total" }, [`${rodada.total} pts`]),
    ]),
    el("div", { class: "rodada-card__body" }, [cardTop6(rodada), linhaBonus(rodada)]),
  ]);
}

function cardSemPalpite(roundInfo, compensacao) {
  return el("div", { class: "rodada-card rodada-card--sem-palpite" }, [
    el("div", { class: "rodada-card__header" }, [
      el("div", {}, [
        el("span", { class: "rodada-card__titulo" }, [`R${roundInfo.round} · ${roundInfo.race}`]),
        el("span", { class: "rodada-card__data" }, [roundInfo.date || ""]),
      ]),
      el("div", { class: "rodada-card__total" }, [`${compensacao} pts`]),
    ]),
    el("div", { class: "rodada-card__body" }, [
      "Não apostou nesta rodada — recebeu pontuação de compensação.",
    ]),
  ]);
}

function renderPalpitesJogador(playerId, bets, standings) {
  const container = document.getElementById("palpites-container");
  const jogadorBets = bets.players[playerId];
  const jogadorStanding = standings.players.find((p) => p.player_id === playerId);

  const roundsPorNumero = new Map(standings.rounds.map((r) => [r.round, r]));
  const compensadas = new Set(jogadorStanding ? jogadorStanding.compensated_rounds : []);

  const todasRodadas = standings.rounds.map((r) => r.round).sort((a, b) => a - b);

  const cards = todasRodadas.map((numRodada) => {
    if (jogadorBets.rounds[numRodada]) {
      const info = roundsPorNumero.get(numRodada);
      return cardRodada(jogadorBets.rounds[numRodada], info ? info.date : "");
    }
    if (compensadas.has(numRodada)) {
      const info = roundsPorNumero.get(numRodada);
      return cardSemPalpite(info, info.min_score);
    }
    return null;
  }).filter(Boolean);

  container.replaceChildren(...cards);
}

// ---------- Temporada (gráficos acumulado e por corrida) ----------

let graficoTemporadaAcumulado = null;
let graficoTemporadaPorRodada = null;
let standingsParaTemporada = null;

function construirSerieJogador(jogador, rounds, cor) {
  const compensadas = new Set(jogador.compensated_rounds);
  const porRodada = [];
  const acumulado = [];
  const pointStyle = [];
  const pointRadius = [];
  const pointBackgroundColor = [];
  const compensadoPorIndice = [];
  let soma = 0;

  for (const rodada of rounds) {
    const numero = rodada.round;
    let valor;
    if (compensadas.has(numero)) {
      valor = rodada.min_score;
      pointStyle.push("triangle");
      pointRadius.push(6);
      pointBackgroundColor.push("#fff");
      compensadoPorIndice.push(true);
    } else {
      valor = jogador.per_round[numero] ?? null;
      pointStyle.push("circle");
      pointRadius.push(4);
      pointBackgroundColor.push(cor);
      compensadoPorIndice.push(false);
    }
    porRodada.push(valor);
    soma += valor ?? 0;
    acumulado.push(valor == null ? null : soma);
  }

  const base = {
    label: jogador.name,
    playerId: jogador.player_id,
    borderColor: cor,
    backgroundColor: cor,
    pointStyle,
    pointRadius,
    pointBackgroundColor,
    pointBorderColor: cor,
    pointBorderWidth: 2,
    borderWidth: 2,
    tension: 0.15,
    spanGaps: false,
    segment: {
      borderDash: (ctx) => (compensadoPorIndice[ctx.p1DataIndex] ? [6, 4] : undefined),
    },
  };

  return {
    datasetAcumulado: { ...base, data: acumulado },
    datasetPorRodada: { ...base, data: porRodada },
  };
}

function construirDadosTemporada(standings) {
  const rounds = standings.rounds.slice().sort((a, b) => a.round - b.round);
  const datasetsAcumulado = [];
  const datasetsPorRodada = [];

  standings.players.forEach((jogador, indice) => {
    const cor = corJogador(indice);
    const { datasetAcumulado, datasetPorRodada } = construirSerieJogador(jogador, rounds, cor);
    datasetsAcumulado.push(datasetAcumulado);
    datasetsPorRodada.push(datasetPorRodada);
  });

  return { labels: rounds.map((r) => r.race), datasetsAcumulado, datasetsPorRodada };
}

function criarGraficoTemporada(canvasId, labels, datasets, standings, tituloEixoY) {
  const corTexto = corCss("--texto-fraco");
  const corGrade = corCss("--borda");
  const ctx = document.getElementById(canvasId).getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(item) {
              const numero = standings.rounds.slice().sort((a, b) => a.round - b.round)[item.dataIndex].round;
              const jogador = standings.players.find((p) => p.player_id === item.dataset.playerId);
              const compensou = jogador && jogador.compensated_rounds.includes(numero);
              return `${item.dataset.label}: ${item.formattedValue} pts${compensou ? " (mínima — não apostou)" : ""}`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { color: corTexto }, grid: { color: corGrade } },
        y: {
          beginAtZero: true,
          ticks: { color: corTexto },
          grid: { color: corGrade },
          title: { display: true, text: tituloEixoY, color: corTexto },
        },
      },
    },
  });
}

function renderTemporada(standings) {
  const { labels, datasetsAcumulado, datasetsPorRodada } = construirDadosTemporada(standings);

  const cardsContainer = document.getElementById("temporada-cards");
  cardsContainer.replaceChildren(
    ...datasetsAcumulado.map((dataset, indice) => {
      const card = el(
        "button",
        { class: "jogador-card", type: "button", style: `--cor-jogador:${dataset.borderColor}` },
        [el("span", { class: "jogador-card__bolinha" }), dataset.label]
      );
      card.addEventListener("click", () => {
        const desligado = card.classList.toggle("jogador-card--desligado");
        graficoTemporadaAcumulado.data.datasets[indice].hidden = desligado;
        graficoTemporadaPorRodada.data.datasets[indice].hidden = desligado;
        graficoTemporadaAcumulado.update();
        graficoTemporadaPorRodada.update();
      });
      return card;
    })
  );

  if (graficoTemporadaAcumulado) graficoTemporadaAcumulado.destroy();
  if (graficoTemporadaPorRodada) graficoTemporadaPorRodada.destroy();
  graficoTemporadaAcumulado = criarGraficoTemporada(
    "temporada-grafico-acumulado", labels, datasetsAcumulado, standings, "Pontos acumulados"
  );
  graficoTemporadaPorRodada = criarGraficoTemporada(
    "temporada-grafico", labels, datasetsPorRodada, standings, "Pontos na rodada"
  );
}

// ---------- Preferência piloto ----------

function popularSelectPreferencia(bets) {
  const select = document.getElementById("select-preferencia-jogador");
  const jogadores = Object.values(bets.players).sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  select.replaceChildren(
    el("option", { value: "todos" }, ["Todos"]),
    ...jogadores.map((j) => el("option", { value: j.player_id }, [j.name]))
  );
}

function coletarPalpitesTop6(bets, playerId) {
  const jogadoresAlvo = playerId === "todos" ? Object.values(bets.players) : [bets.players[playerId]].filter(Boolean);
  const porPiloto = new Map(); // codigo -> { soma, count }

  for (const jogador of jogadoresAlvo) {
    for (const rodada of Object.values(jogador.rounds)) {
      rodada.top6.forEach((codigo, indice) => {
        const posicao = indice + 1;
        const registro = porPiloto.get(codigo) || { soma: 0, count: 0 };
        registro.soma += posicao;
        registro.count += 1;
        porPiloto.set(codigo, registro);
      });
    }
  }
  return porPiloto;
}

function renderPreferenciaPiloto(playerId, bets) {
  const container = document.getElementById("preferencia-container");
  const porPiloto = coletarPalpitesTop6(bets, playerId);

  const linhas = [...porPiloto.entries()]
    .map(([codigo, { soma, count }]) => ({ codigo, media: soma / count, count }))
    .sort((a, b) => a.media - b.media || a.codigo.localeCompare(b.codigo));

  if (!linhas.length) {
    container.replaceChildren(el("p", { class: "status" }, ["Sem palpites de top6 registrados."]));
    return;
  }

  const tabela = el("table", { class: "preferencia-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["Piloto"]),
        el("th", { class: "num" }, ["Posição média"]),
        el("th", { class: "num" }, ["Vezes apostado"]),
      ]),
    ]),
  ]);
  const tbody = el("tbody");
  for (const linha of linhas) {
    tbody.appendChild(
      el("tr", {}, [
        el("td", {}, [chipPiloto(linha.codigo)]),
        el("td", { class: "num" }, [linha.media.toFixed(2)]),
        el("td", { class: "num" }, [String(linha.count)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  container.replaceChildren(tabela);
}

// ---------- Hall of Fame ----------

function nomeHall(hof, id) {
  return hof.nomes[id] || id;
}

function construirRankingHall(hof) {
  const contagem = new Map(); // id -> { ouro, prata, bronze }
  const registrar = (id, medalha) => {
    if (!id) return;
    if (!contagem.has(id)) contagem.set(id, { ouro: 0, prata: 0, bronze: 0 });
    contagem.get(id)[medalha]++;
  };
  for (const ano of hof.anos) {
    registrar(ano.ouro, "ouro");
    registrar(ano.prata, "prata");
    registrar(ano.bronze, "bronze");
  }
  return [...contagem.entries()]
    .map(([id, m]) => ({ id, nome: nomeHall(hof, id), ...m }))
    .sort((a, b) => b.ouro - a.ouro || b.prata - a.prata || b.bronze - a.bronze || a.nome.localeCompare(b.nome, "pt-BR"));
}

function renderRankingHall(hof) {
  const linhas = construirRankingHall(hof);
  const tabela = el("table", { class: "hall-ranking-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["Jogador"]),
        el("th", { class: "num" }, ["🥇"]),
        el("th", { class: "num" }, ["🥈"]),
        el("th", { class: "num" }, ["🥉"]),
      ]),
    ]),
  ]);
  const tbody = el("tbody");
  for (const linha of linhas) {
    tbody.appendChild(
      el("tr", {}, [
        el("td", {}, [linha.nome]),
        el("td", { class: "num" }, [String(linha.ouro)]),
        el("td", { class: "num" }, [String(linha.prata)]),
        el("td", { class: "num" }, [String(linha.bronze)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  return tabela;
}

function renderListaAnosHall(hof) {
  const medalhas = { ouro: "🥇", prata: "🥈", bronze: "🥉" };
  const anos = hof.anos.slice().sort((a, b) => b.ano - a.ano);
  const lista = el("ul", { class: "hall-anos-lista" });
  for (const ano of anos) {
    lista.appendChild(
      el("li", { class: "hall-ano-item" }, [
        el("span", { class: "hall-ano-item__ano" }, [String(ano.ano)]),
        el("span", { class: "hall-ano-item__medalha" }, [`${medalhas.ouro} ${nomeHall(hof, ano.ouro)}`]),
        el("span", { class: "hall-ano-item__medalha" }, [`${medalhas.prata} ${nomeHall(hof, ano.prata)}`]),
        el("span", { class: "hall-ano-item__medalha" }, [`${medalhas.bronze} ${nomeHall(hof, ano.bronze)}`]),
      ])
    );
  }
  return lista;
}

function renderHallOfFame(hof) {
  const container = document.getElementById("hall-container");
  container.replaceChildren(
    el("div", { class: "hall-grid" }, [
      el("div", { class: "hall-coluna" }, [el("h2", {}, ["Ranking de vitórias"]), renderRankingHall(hof)]),
      el("div", { class: "hall-coluna" }, [el("h2", {}, ["Pódios por ano"]), renderListaAnosHall(hof)]),
    ])
  );
}

// ---------- Abas ----------

// Chart.js não recupera bem de ser inicializado num canvas ainda escondido
// (0x0) — resize() sozinho não corrige. Por isso os gráficos da Temporada só
// são criados na primeira vez que a sub-aba fica visível (garantirGraficosTemporada).
function garantirGraficosTemporada() {
  if (!standingsParaTemporada) return;
  if (graficoTemporadaAcumulado && graficoTemporadaPorRodada) {
    graficoTemporadaAcumulado.resize();
    graficoTemporadaPorRodada.resize();
  } else {
    renderTemporada(standingsParaTemporada);
  }
}

function configurarAbas() {
  const botoes = document.querySelectorAll("button.aba");
  const secoes = {
    ranking: document.getElementById("secao-ranking"),
    palpites: document.getElementById("secao-palpites"),
    hall: document.getElementById("secao-hall"),
  };
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      botoes.forEach((b) => b.setAttribute("aria-selected", "false"));
      botao.setAttribute("aria-selected", "true");
      for (const [nome, secao] of Object.entries(secoes)) {
        secao.hidden = nome !== botao.dataset.aba;
      }
      const subabaAtiva = document.querySelector("button.subaba[aria-selected=\"true\"]");
      if (botao.dataset.aba === "palpites" && subabaAtiva && subabaAtiva.dataset.subaba === "temporada") {
        garantirGraficosTemporada();
      }
    });
  });
}

function configurarSubAbas() {
  const botoes = document.querySelectorAll("button.subaba");
  const secoes = {
    historico: document.getElementById("subsecao-historico"),
    temporada: document.getElementById("subsecao-temporada"),
    preferencia: document.getElementById("subsecao-preferencia"),
  };
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      botoes.forEach((b) => b.setAttribute("aria-selected", "false"));
      botao.setAttribute("aria-selected", "true");
      for (const [nome, secao] of Object.entries(secoes)) {
        secao.hidden = nome !== botao.dataset.subaba;
      }
      if (botao.dataset.subaba === "temporada") {
        garantirGraficosTemporada();
      }
    });
  });
}

async function main() {
  configurarAbas();
  configurarSubAbas();

  try {
    const standings = await carregarJson("./data/standings.json");
    renderRanking(standings);
    document.getElementById("ranking-status").textContent = "";

    const bets = await carregarJson("./data/bets.json");
    const jogadores = popularSelectJogadores(bets);
    document.getElementById("palpites-status").textContent = "";

    const select = document.getElementById("select-jogador");
    select.addEventListener("change", () => {
      renderPalpitesJogador(select.value, bets, standings);
    });

    if (jogadores.length) {
      select.value = jogadores[0].player_id;
      renderPalpitesJogador(jogadores[0].player_id, bets, standings);
    }

    standingsParaTemporada = standings;

    popularSelectPreferencia(bets);
    const selectPreferencia = document.getElementById("select-preferencia-jogador");
    selectPreferencia.addEventListener("change", () => {
      renderPreferenciaPiloto(selectPreferencia.value, bets);
    });
    renderPreferenciaPiloto("todos", bets);

    const hof = await carregarJson("./data/hall_of_fame.json");
    renderHallOfFame(hof);
    document.getElementById("hall-status").textContent = "";
  } catch (erro) {
    console.error(erro);
    document.getElementById("ranking-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("ranking-status").classList.add("erro");
    document.getElementById("palpites-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("palpites-status").classList.add("erro");
    document.getElementById("hall-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("hall-status").classList.add("erro");
  }
}

main();
