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

// ---------- Abas ----------

function configurarAbas() {
  const botoes = document.querySelectorAll("button.aba");
  const secoes = {
    ranking: document.getElementById("secao-ranking"),
    palpites: document.getElementById("secao-palpites"),
  };
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      botoes.forEach((b) => b.setAttribute("aria-selected", "false"));
      botao.setAttribute("aria-selected", "true");
      for (const [nome, secao] of Object.entries(secoes)) {
        secao.hidden = nome !== botao.dataset.aba;
      }
    });
  });
}

async function main() {
  configurarAbas();

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
  } catch (erro) {
    console.error(erro);
    document.getElementById("ranking-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("ranking-status").classList.add("erro");
    document.getElementById("palpites-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("palpites-status").classList.add("erro");
  }
}

main();
