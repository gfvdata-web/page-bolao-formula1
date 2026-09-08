// Bolão F1 2026 — Etapa 4 (site estático, vanilla JS)

// Cor aproximada por equipe 2026, mapeada por código de piloto (3 letras).
// Puramente decorativo (identifica a equipe no círculo ao lado do código).
const CORES_PILOTO = {
  VER: "#3671C6", HAD: "#3671C6", TSU: "#3671C6", // Red Bull
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

// Temporada exibida. Os dados do site vivem em ./data/<ano>/ (uma pasta por
// temporada); ./data/seasons.json lista as disponíveis + o formato de cada uma,
// e ./data/hall_of_fame.json é comum a todas.
//
// Sem ?ano na URL → temporada corrente (seasons.atual). Com ?ano=YYYY de uma
// temporada anterior → "modo histórico": título vira o ano + badge HISTÓRICO,
// botão "voltar", sub-aba Simulador some, e as visualizações se adaptam ao
// formato daquele ano (FORMATO: top5 vs top6, com/sem piloto da rodada, etc.).
let TEMPORADA = "2026";
let SEASONS = null;
let FORMATO = { top_n: 6, bonus: true, bonus_points: 1, compensation: true, max_points: 13 };
let MODO_HISTORICO = false;
let calendarGlobal = null;

function anoPedido() {
  const p = new URLSearchParams(location.search).get("ano");
  return p && /^\d{4}$/.test(p) ? p : null;
}

function entradaTemporada(ano = TEMPORADA) {
  return (SEASONS?.temporadas || []).find((t) => String(t.ano) === String(ano));
}

async function carregarJson(caminho) {
  const resp = await fetch(caminho);
  if (!resp.ok) throw new Error(`Falha ao buscar ${caminho}: ${resp.status}`);
  return resp.json();
}

// Caminho de um JSON de dados da temporada ativa (ex.: caminhoDados("standings")).
function caminhoDados(nome) {
  return `./data/${TEMPORADA}/${nome}.json`;
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

const SVG_NS = "http://www.w3.org/2000/svg";

// Igual ao `el()`, mas no namespace SVG (createElement não serve para <svg>).
function svgEl(tag, props = {}, filhos = []) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [chave, valor] of Object.entries(props)) node.setAttribute(chave, valor);
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

// `max` é o teto de pontos daquele tipo de acerto (2 no top6, 1 no piloto da
// rodada) — sem ele, `pts` já corresponde ao nível de cor (comportamento do
// top6, onde 0/1/2 pt = nível 0/1/2). Com `max`, quem bate o teto vira
// nível 2 (verde) mesmo que o teto seja 1, como no piloto da rodada.
function badgePonto(pts, max) {
  const nivel = max == null ? pts : pts >= max ? 2 : pts > 0 ? 1 : 0;
  return el("span", { class: `ponto-badge ponto-${nivel}` }, [`${pts}pt`]);
}

// ---------- Ranking ----------

// Célula "Calculada": total pelo nosso motor, com a diferença para o oficial
// quando os dois não batem (temporadas finalizadas).
function celCalculada(jogador) {
  const calc = jogador.total_calculado;
  const dif = calc - jogador.total;
  const filhos = [String(calc)];
  if (dif !== 0) {
    filhos.push(
      el("span", { class: "ranking-dif" }, [` (${dif > 0 ? "+" : "−"}${Math.abs(dif)})`])
    );
  }
  return el("td", { class: "num" }, filhos);
}

function renderRanking(standings) {
  const container = document.getElementById("ranking-container");
  // Nas temporadas finalizadas o placar do grupo (oficial) pode divergir do
  // recálculo — mostramos as duas colunas para dá pra comparar.
  const mostrarCalculada = MODO_HISTORICO && standings.players.some((j) => j.total_calculado !== j.total);
  const tabela = el("table", { class: "ranking-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["#"]),
        el("th", {}, ["Jogador"]),
        el("th", { class: "num" }, [mostrarCalculada ? "Oficial" : "Pontos"]),
        mostrarCalculada ? el("th", { class: "num" }, ["Calculada"]) : null,
        el("th", { class: "num" }, ["Média/Corrida"]),
        FORMATO.bonus ? el("th", { class: "num" }, ["Pontos Extra"]) : null,
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
        mostrarCalculada ? celCalculada(jogador) : null,
        el("td", { class: "num" }, [jogador.avg_points.toFixed(1)]),
        FORMATO.bonus ? el("td", { class: "num" }, [String(jogador.bonus_total)]) : null,
        el("td", { class: "num" }, [String(jogador.rounds_played)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  container.replaceChildren(tabela);

  if (mostrarCalculada) {
    container.appendChild(
      el("p", { class: "ranking-nota-calculada" }, [
        "“Oficial” = placar final publicado pelo grupo. “Calculada” = recálculo " +
          "pelas regras da temporada; a diferença aparece entre parênteses.",
      ])
    );
  }
}

// ---------- Ranking / Corridas (última contabilizada + próxima) ----------

function formatarDataBR(dataISO) {
  if (!dataISO) return "";
  const [ano, mes, dia] = dataISO.split("-");
  return `${dia}/${mes}/${ano}`;
}

function formatarQualiBrasilia(qualiUtcISO) {
  if (!qualiUtcISO) return null;
  const data = new Date(qualiUtcISO);
  const formatado = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(data);
  return `${formatado} (horário de Brasília)`;
}

function cardCorrida(titulo, race, extra) {
  return el("div", { class: "corrida-card" }, [
    el("div", { class: "corrida-card__titulo" }, [titulo]),
    el("div", { class: "corrida-card__corrida" }, [`R${race.round} · ${race.race}`]),
    extra ? el("div", { class: "corrida-card__extra" }, [extra]) : null,
  ]);
}

function cardInfo(titulo, valor, extra) {
  return el("div", { class: "corrida-card" }, [
    el("div", { class: "corrida-card__titulo" }, [titulo]),
    el("div", { class: "corrida-card__corrida" }, [valor]),
    extra ? el("div", { class: "corrida-card__extra" }, [extra]) : null,
  ]);
}

function renderCorridas(standings, calendar) {
  const container = document.getElementById("corridas-cards");

  if (MODO_HISTORICO) {
    const entrada = entradaTemporada() || {};
    const totalTxt = entrada.rodadas_totais
      ? `de ${entrada.rodadas_totais} no calendário`
      : "";
    container.replaceChildren(
      cardInfo("Rodadas contabilizadas", String(standings.rounds.length), totalTxt),
      cardInfo("Jogadores competindo", String(standings.players.length), "no ranking da temporada")
    );
    return;
  }

  const rounds = standings.rounds.slice().sort((a, b) => a.round - b.round);
  const ultima = rounds[rounds.length - 1];
  const consolidadas = new Set(rounds.map((r) => r.round));
  const proxima = calendar.races
    .slice()
    .sort((a, b) => a.round - b.round)
    .find((r) => !consolidadas.has(r.round));

  const cards = [];
  if (ultima) {
    cards.push(cardCorrida("Última corrida contabilizada", ultima, formatarDataBR(ultima.date)));
  }
  if (proxima) {
    const horario = formatarQualiBrasilia(proxima.qualifying_utc);
    cards.push(
      cardCorrida(
        "Próxima corrida",
        proxima,
        horario ? `Quali: ${horario} — prazo para apostar` : "Data do quali ainda não divulgada"
      )
    );
  }
  container.replaceChildren(...cards);
}

function renderTabelaCorridas(standings) {
  const container = document.getElementById("corridas-tabela-container");
  const rounds = standings.rounds.slice().sort((a, b) => a.round - b.round);

  const tabela = el("table", { class: "corridas-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["Jogador"]),
        ...rounds.map((r) =>
          el("th", { class: "num" }, [
            el("span", { class: "corridas-tabela__rodada" }, [`R${r.round}`]),
            el("span", { class: "corridas-tabela__corrida" }, [r.race]),
          ])
        ),
        el("th", { class: "num" }, ["Total"]),
      ]),
    ]),
  ]);

  const tbody = el("tbody");
  for (const jogador of standings.players) {
    const celulas = rounds.map((r) => {
      const compensou = jogador.compensated_rounds.includes(r.round);
      const valor = compensou ? r.min_score : jogador.per_round[r.round];
      if (valor == null) return el("td", { class: "num" }, ["–"]);
      return el(
        "td",
        { class: compensou ? "num corridas-tabela__compensado" : "num" },
        [String(valor)]
      );
    });
    tbody.appendChild(
      el("tr", {}, [
        el("td", {}, [jogador.name]),
        ...celulas,
        el("td", { class: "num corridas-tabela__total" }, [String(jogador.total)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  container.replaceChildren(tabela);
}

// ---------- Ranking / Geral — pontuação da corrida (por jogador) ----------

function celPalpite(guess, points) {
  return el("div", { class: "corrida-detalhe-cel" }, [chipPiloto(guess), badgePonto(points)]);
}

function celBonusPalpite(pos, points) {
  return el("div", { class: "corrida-detalhe-cel" }, [
    el("span", { class: "corrida-detalhe-cel__pos" }, [`P${pos}`]),
    badgePonto(points, FORMATO.bonus_points),
  ]);
}

function celVazia() {
  return el("span", { class: "corrida-detalhe-vazio", title: "Não apostou nesta rodada" }, ["–"]);
}

function popularSelectCorridaDetalhe(standings) {
  const select = document.getElementById("select-corrida-detalhe");
  const rounds = standings.rounds.slice().sort((a, b) => a.round - b.round);
  select.replaceChildren(
    ...rounds.map((r) => el("option", { value: String(r.round) }, [`R${r.round} · ${r.race}`]))
  );
  return rounds;
}

function renderCorridaDetalhe(roundNumber, standings, bets, results) {
  const wrap = document.getElementById("corrida-detalhe-tabela-wrap");
  const roundInfo = standings.rounds.find((r) => r.round === roundNumber);
  const resultado = results.rounds[String(roundNumber)];
  if (!roundInfo || !resultado) {
    wrap.replaceChildren(el("p", { class: "status" }, ["Sem resultado para esta corrida."]));
    return;
  }

  const realTop6 = resultado.order.slice(0, FORMATO.top_n);
  const bonusDriver = roundInfo.bonus_driver;
  const bonusRealPos = resultado.order.indexOf(bonusDriver) + 1;

  const totalRodadaJogador = (jogador) =>
    jogador.compensated_rounds.includes(roundNumber)
      ? roundInfo.min_score
      : jogador.per_round[roundNumber] ?? null;

  const tabela = el("table", { class: "corrida-detalhe-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["Pos"]),
        el("th", {}, ["Resultado"]),
        ...standings.players.map((j) =>
          el("th", { title: j.name }, [
            el("span", { class: "corrida-detalhe-th__nome" }, [j.name.split(" ")[0]]),
            el("span", { class: "corrida-detalhe-th__total" }, [
              totalRodadaJogador(j) == null ? "–" : `${totalRodadaJogador(j)} pts`,
            ]),
          ])
        ),
      ]),
    ]),
  ]);

  const tbody = el("tbody");

  realTop6.forEach((codigoReal, indice) => {
    const pos = indice + 1;
    tbody.appendChild(
      el("tr", {}, [
        el("td", { class: "corrida-detalhe-rotulo" }, [`P${pos}`]),
        el("td", {}, [chipPiloto(codigoReal)]),
        ...standings.players.map((jogador) => {
          const rodada = bets.players[jogador.player_id]?.rounds[roundNumber];
          if (!rodada) return el("td", {}, [celVazia()]);
          const linha = rodada.top6_detail[indice];
          return el("td", {}, [celPalpite(linha.guess, linha.points)]);
        }),
      ])
    );
  });

  if (FORMATO.bonus) {
    tbody.appendChild(
      el("tr", {}, [
        el("td", { class: "corrida-detalhe-rotulo" }, [
          el("span", {}, ["Piloto"]),
          chipPiloto(bonusDriver),
        ]),
        el("td", {}, [`P${bonusRealPos}`]),
        ...standings.players.map((jogador) => {
          const rodada = bets.players[jogador.player_id]?.rounds[roundNumber];
          if (!rodada) return el("td", {}, [celVazia()]);
          return el("td", {}, [celBonusPalpite(rodada.bonus_guess, rodada.bonus_points)]);
        }),
      ])
    );
  }

  tabela.appendChild(tbody);
  wrap.replaceChildren(tabela);
}

// ---------- Ranking / Geral — copiar texto p/ WhatsApp ----------

// Emoji de posição: 1️⃣.. 🔟 fixos (bate com o formato clássico das mensagens);
// a partir do 11º, concatena os emojis de dígito (1️⃣1️⃣, 1️⃣2️⃣...).
const EMOJI_POSICAO_FIXA = ["", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"];
const EMOJI_DIGITO = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"];

function emojiPosicao(pos) {
  if (pos <= 10) return EMOJI_POSICAO_FIXA[pos];
  return String(pos)
    .split("")
    .map((d) => EMOJI_DIGITO[Number(d)])
    .join("");
}

// Rodada mais antiga em que o jogador tem palpite real registrado (não conta
// compensação) — usada só pra saber se ele estreou na última rodada.
function primeiraRodadaApostada(jogador) {
  const rodadas = Object.keys(jogador.per_round).map(Number);
  return rodadas.length ? Math.min(...rodadas) : null;
}

// Texto no formato clássico do WhatsApp (ver CONTEXTO.md) com a classificação
// da temporada: posição, pontos, variação de posição desde a rodada anterior
// (🆕 se estreou nela), nº de rodadas apostadas e pontos extra (piloto da
// rodada). A variação reaproveita `construirDadosTemporada` (mesmo cálculo de
// posição por rodada usado nos gráficos de Corridas).
function gerarTextoRanking(standings) {
  const dados = construirDadosTemporada(standings);
  const indiceUltima = dados.rounds.length - 1;
  const ultimaRodada = dados.rounds[indiceUltima];

  const linhas = [`Classificação Bolão ${standings.season}`, ""];

  for (const jogador of standings.players) {
    const estreouAgora = ultimaRodada && primeiraRodadaApostada(jogador) === ultimaRodada.round;
    let variacao;
    if (estreouAgora) {
      variacao = "🆕";
    } else {
      const posicoes = dados.posicoesRanking.get(jogador.player_id) || [];
      const atual = posicoes[indiceUltima];
      const anterior = posicoes[indiceUltima - 1];
      if (atual == null || anterior == null) {
        variacao = "⏸️";
      } else {
        const delta = anterior - atual;
        if (delta > 0) variacao = `🔼 ${delta}`;
        else if (delta < 0) variacao = `🔽 ${-delta}`;
        else variacao = "⏸️";
      }
    }
    linhas.push(
      `${emojiPosicao(jogador.position)} ${jogador.name} 🅿️ ${jogador.total} ${variacao} 🔄 ${jogador.rounds_played} *️⃣ ${jogador.bonus_total}`
    );
  }

  return linhas.join("\n");
}

// Texto no formato clássico do WhatsApp com a pontuação de uma corrida:
// nome + pontos, um por linha, na ordem real em que os palpites chegaram
// naquela rodada (`bet_order`, gerado pelo bolao/site.py a partir da ordem
// dos blocos no texto original — não a ordem do ranking). Só entra quem
// realmente apostou na rodada.
function gerarTextoCorrida(roundNumber, standings) {
  const roundInfo = standings.rounds.find((r) => r.round === roundNumber);
  if (!roundInfo) return "";
  const porId = new Map(standings.players.map((j) => [j.player_id, j]));
  const linhas = [`Resultado Qualify ${roundInfo.race}`, ""];
  for (const playerId of roundInfo.bet_order || []) {
    const jogador = porId.get(playerId);
    if (!jogador) continue;
    linhas.push(`${jogador.name} ${jogador.per_round[String(roundNumber)]}`);
  }
  return linhas.join("\n");
}

// Copia pro clipboard e dá feedback visual no botão (fallback com textarea
// pra navegadores/contextos sem Clipboard API, ex. alguns webviews).
async function copiarTexto(texto, botao) {
  try {
    await navigator.clipboard.writeText(texto);
  } catch (erro) {
    const area = document.createElement("textarea");
    area.value = texto;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.focus();
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
  }
  const textoOriginal = botao.textContent;
  botao.textContent = "✅ Copiado!";
  botao.classList.add("btn-copiar--copiado");
  setTimeout(() => {
    botao.textContent = textoOriginal;
    botao.classList.remove("btn-copiar--copiado");
  }, 1500);
}

// ---------- Ranking / Simulador ----------

// Estado vivo da simulação: média editável por jogador (inicia = avg_points
// real) e nº de rodadas restantes na temporada (calendar - já consolidadas).
let simuladorEstado = null;

function calcularRodadasRestantes(standings, calendar) {
  const consolidadas = new Set(standings.rounds.map((r) => r.round));
  return calendar.races.filter((r) => !consolidadas.has(r.round)).length;
}

function construirProjecoesSimulador() {
  const { standings, mediaSimulada, rodadasRestantes, rodadasJaRodadas } = simuladorEstado;
  const posicaoAtual = new Map(standings.players.map((j) => [j.player_id, j.position]));
  const totalTemporada = rodadasJaRodadas + rodadasRestantes;

  const linhas = standings.players.map((jogador) => {
    const mediaAtual = jogador.avg_points;
    const mediaFinalSimulada = mediaSimulada.get(jogador.player_id);
    // Média final pondera o que já rodou (média real) com o que falta (média
    // simulada), pelo nº de rodadas de cada lado — não é a média simulada
    // "pura", que só vale para as rodadas futuras.
    const mediaFinal =
      totalTemporada > 0
        ? (mediaAtual * rodadasJaRodadas + mediaFinalSimulada * rodadasRestantes) / totalTemporada
        : mediaAtual;
    const projecao = jogador.total + mediaFinalSimulada * rodadasRestantes;
    return { jogador, mediaAtual, mediaFinal, projecao };
  });

  linhas.sort((a, b) => b.projecao - a.projecao || a.jogador.player_id.localeCompare(b.jogador.player_id));
  linhas.forEach((linha, indice) => {
    linha.posicaoSimulada = indice + 1;
    linha.deltaPosicao = posicaoAtual.get(linha.jogador.player_id) - linha.posicaoSimulada;
  });
  return linhas;
}

function badgeDeltaPosicao(delta) {
  if (delta === 0) return el("span", { class: "delta-posicao delta-posicao--igual" }, ["="]);
  const classe = delta > 0 ? "delta-posicao--sobe" : "delta-posicao--desce";
  const seta = delta > 0 ? "▲" : "▼";
  return el("span", { class: `delta-posicao ${classe}` }, [`${seta} ${Math.abs(delta)}`]);
}

function renderTabelaSimulador() {
  const container = document.getElementById("simulador-tabela-container");
  const linhas = construirProjecoesSimulador();
  const medalhas = { 1: "🥇", 2: "🥈", 3: "🥉" };

  const tabela = el("table", { class: "ranking-tabela simulador-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["#"]),
        el("th", {}, ["Jogador"]),
        el("th", { class: "num" }, ["Pontos atuais"]),
        el("th", { class: "num" }, ["Média atual"]),
        el("th", { class: "num" }, ["Média final"]),
        el("th", { class: "num" }, ["Projeção final"]),
        el("th", { class: "num" }, ["Δ posição"]),
      ]),
    ]),
  ]);

  const tbody = el("tbody");
  for (const linha of linhas) {
    tbody.appendChild(
      el("tr", {}, [
        el("td", { class: "pos-medalha" }, [medalhas[linha.posicaoSimulada] || String(linha.posicaoSimulada)]),
        el("td", {}, [linha.jogador.name]),
        el("td", { class: "num" }, [String(linha.jogador.total)]),
        el("td", { class: "num" }, [linha.mediaAtual.toFixed(1)]),
        el("td", { class: "num" }, [linha.mediaFinal.toFixed(1)]),
        el("td", { class: "num simulador-tabela__projecao" }, [linha.projecao.toFixed(1)]),
        el("td", { class: "num" }, [badgeDeltaPosicao(linha.deltaPosicao)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  container.replaceChildren(tabela);
}

const SIMULADOR_MIN = 0;
const SIMULADOR_MAX = 13;

function clampMedia(valor) {
  if (Number.isNaN(valor)) return SIMULADOR_MIN;
  return Math.min(SIMULADOR_MAX, Math.max(SIMULADOR_MIN, Math.round(valor * 10) / 10));
}

function cardSimuladorJogador(jogador, indice) {
  const cor = corJogador(indice);
  const valorInicial = simuladorEstado.mediaSimulada.get(jogador.player_id);

  const input = el("input", {
    type: "text",
    inputmode: "decimal",
    value: valorInicial.toFixed(1),
    class: "simulador-card__input",
    style: `color:${cor}`,
  });

  const badgeSimulado = el("span", { class: "simulador-card__badge" }, ["simulado"]);

  const aplicarValor = (novoValor) => {
    const valorFinal = clampMedia(novoValor);
    simuladorEstado.mediaSimulada.set(jogador.player_id, valorFinal);
    input.value = valorFinal.toFixed(1);
    badgeSimulado.classList.toggle("simulador-card__badge--oculto", valorFinal.toFixed(1) === jogador.avg_points.toFixed(1));
    renderTabelaSimulador();
  };

  input.addEventListener("change", () => {
    aplicarValor(parseFloat(input.value.replace(",", ".")));
  });

  const botaoMenos = el(
    "button",
    { type: "button", class: "simulador-card__passo", title: "-0.1" },
    ["−"]
  );
  botaoMenos.addEventListener("click", () => {
    aplicarValor(simuladorEstado.mediaSimulada.get(jogador.player_id) - 0.1);
  });

  const botaoMais = el(
    "button",
    { type: "button", class: "simulador-card__passo", title: "+0.1" },
    ["+"]
  );
  botaoMais.addEventListener("click", () => {
    aplicarValor(simuladorEstado.mediaSimulada.get(jogador.player_id) + 0.1);
  });

  const botaoReset = el(
    "button",
    { type: "button", class: "simulador-card__reset", title: "Restaurar média atual" },
    ["↺"]
  );
  botaoReset.addEventListener("click", () => {
    aplicarValor(jogador.avg_points);
  });

  badgeSimulado.classList.toggle("simulador-card__badge--oculto", valorInicial.toFixed(1) === jogador.avg_points.toFixed(1));

  return el("div", { class: "simulador-card", style: `--cor-jogador:${cor}` }, [
    el("div", { class: "simulador-card__header" }, [
      el("span", { class: "simulador-card__nome-linha" }, [
        el("span", { class: "simulador-card__nome" }, [jogador.name]),
        badgeSimulado,
      ]),
      botaoReset,
    ]),
    el("div", { class: "simulador-card__controle" }, [botaoMenos, input, botaoMais]),
  ]);
}

function renderCardsSimulador() {
  const cardsContainer = document.getElementById("simulador-cards");
  const jogadores = simuladorEstado.standings.players;
  // Nº de colunas calculado para caber exatamente 2 linhas, qualquer que
  // seja o nº de jogadores — os cards encolhem (minmax(0, 1fr)) em vez de
  // criar rolagem horizontal.
  const colunas = Math.max(1, Math.ceil(jogadores.length / 2));
  cardsContainer.style.gridTemplateColumns = `repeat(${colunas}, minmax(0, 1fr))`;
  cardsContainer.replaceChildren(
    ...jogadores.map((jogador, indice) => cardSimuladorJogador(jogador, indice))
  );
}

function resetarTodasSimulacoes() {
  for (const jogador of simuladorEstado.standings.players) {
    simuladorEstado.mediaSimulada.set(jogador.player_id, jogador.avg_points);
  }
  renderCardsSimulador();
  renderTabelaSimulador();
}

function renderSimulador(standings, calendar) {
  const rodadasRestantes = calcularRodadasRestantes(standings, calendar);
  const rodadasJaRodadas = standings.rounds.length;
  const mediaSimulada = new Map(standings.players.map((j) => [j.player_id, j.avg_points]));
  simuladorEstado = { standings, calendar, mediaSimulada, rodadasRestantes, rodadasJaRodadas };

  const status = document.getElementById("simulador-status");
  status.textContent =
    rodadasRestantes > 0
      ? `Simulando as ${rodadasRestantes} corrida(s) que faltam na temporada — ajuste os cards para testar médias.`
      : "Temporada já concluída — não há mais corridas para simular.";

  document.getElementById("simulador-reset-geral").addEventListener("click", resetarTodasSimulacoes);

  renderCardsSimulador();
  renderTabelaSimulador();
}

// ---------- Palpites por jogador / Histórico ----------

// Matriz posição × corrida: linhas P1–P6 + piloto da rodada + total; colunas
// = corridas; célula = palpite de cada jogador selecionado + badge de pontos.
function posicoesTopN() {
  return Array.from({ length: FORMATO.top_n }, (_, i) => `P${i + 1}`);
}
let histBets = null;
let histStandings = null;
let histSelecionados = [];
let histCores = new Map();

function popularHistJogadores(bets, standings) {
  const box = document.getElementById("hist-jogadores");
  const jogadores = Object.values(bets.players).sort((a, b) =>
    a.name.localeCompare(b.name, "pt-BR")
  );
  histCores = new Map(jogadores.map((j, i) => [j.player_id, corJogador(i)]));
  box.replaceChildren(
    ...jogadores.map((j) => {
      const chip = el(
        "button",
        {
          type: "button",
          class: "hist-jogador-chip",
          "data-player": j.player_id,
          "aria-pressed": "false",
          style: `--cor-jogador:${histCores.get(j.player_id)}`,
        },
        [el("span", { class: "hist-jogador-chip__ponto" }), j.name]
      );
      chip.addEventListener("click", () => alternarHistJogador(j.player_id));
      return chip;
    })
  );
  return jogadores;
}

function alternarHistJogador(playerId) {
  const i = histSelecionados.indexOf(playerId);
  if (i >= 0) histSelecionados.splice(i, 1);
  else histSelecionados.push(playerId);
  if (!histSelecionados.length) histSelecionados.push(playerId); // nunca vazio
  sincronizarHistChips();
  renderHistMatriz();
  renderHistPorCorrida();
}

function sincronizarHistChips() {
  document.querySelectorAll("#hist-jogadores .hist-jogador-chip").forEach((chip) => {
    chip.setAttribute(
      "aria-pressed",
      histSelecionados.includes(chip.dataset.player) ? "true" : "false"
    );
  });
}

// Badge de pontos no formato curto da matriz (+2 / +1 / 0). Reaproveita as
// cores de `.ponto-badge`; `max` marca o teto (1 no piloto da rodada) para
// pintar de verde quem bate o teto — mesma lógica de `badgePonto`.
function histBadgePonto(pts, max) {
  const nivel = max == null ? pts : pts >= max ? 2 : pts > 0 ? 1 : 0;
  return el("span", { class: `ponto-badge ponto-${nivel}` }, [pts > 0 ? `+${pts}` : "0"]);
}

function histCelula(round, linhaIdx, tipo) {
  const cel = el("div", { class: "hist-cel" });
  for (const playerId of histSelecionados) {
    const jogadorBets = histBets.players[playerId];
    const rodada = jogadorBets ? jogadorBets.rounds[String(round)] : null;
    const standing = histStandings.players.find((p) => p.player_id === playerId);
    const linha = el("div", { class: "hist-cel__linha" });
    if (histSelecionados.length > 1) {
      linha.appendChild(
        el("span", {
          class: "hist-cel__ponto",
          style: `background:${histCores.get(playerId)}`,
        })
      );
    }
    if (tipo === "total") {
      let pontos = null;
      let compensada = false;
      if (rodada) {
        pontos = rodada.total;
      } else if (standing && standing.compensated_rounds.includes(round)) {
        const info = histStandings.rounds.find((r) => r.round === round);
        pontos = info ? info.min_score : null;
        compensada = true;
      }
      if (pontos == null) {
        linha.appendChild(el("span", { class: "hist-cel__vazio" }, ["—"]));
      } else {
        linha.appendChild(
          el(
            "span",
            { class: compensada ? "hist-cel__total hist-cel__total--comp" : "hist-cel__total" },
            [`${pontos} pts`]
          )
        );
      }
    } else if (!rodada) {
      linha.appendChild(el("span", { class: "hist-cel__vazio" }, ["—"]));
    } else if (tipo === "extra") {
      linha.appendChild(chipPiloto(rodada.bonus_driver));
      linha.appendChild(el("span", { class: "hist-cel__chute" }, [`P${rodada.bonus_guess}`]));
      linha.appendChild(histBadgePonto(rodada.bonus_points, FORMATO.bonus_points));
    } else {
      const detalhe = rodada.top6_detail[linhaIdx];
      linha.appendChild(chipPiloto(detalhe.guess));
      linha.appendChild(histBadgePonto(detalhe.points));
    }
    cel.appendChild(linha);
  }
  return el("td", {}, [cel]);
}

// Colunas da matriz. Numa temporada finalizada mostramos TODAS as corridas do
// calendário — inclusive as sem palpite registrado, marcadas "(sem registro)"
// e com "—" em todas as células — para a leitura ser da temporada inteira.
function rodadasMatriz() {
  const consolidadas = histStandings.rounds.slice().sort((a, b) => a.round - b.round);
  if (!MODO_HISTORICO || !calendarGlobal) {
    return consolidadas.map((r) => ({ round: r.round, race: r.race, semRegistro: false }));
  }
  const porRound = new Map(consolidadas.map((r) => [r.round, r]));
  return calendarGlobal.races
    .slice()
    .sort((a, b) => a.round - b.round)
    .map((r) =>
      porRound.has(r.round)
        ? { round: r.round, race: porRound.get(r.round).race, semRegistro: false }
        : { round: r.round, race: r.race, semRegistro: true }
    );
}

function renderHistMatriz() {
  const rodadas = rodadasMatriz();
  const thead = el("thead", {}, [
    el("tr", {}, [
      el("th", { class: "hist-matriz__pos" }, [""]),
      ...rodadas.map((r) =>
        el("th", { class: r.semRegistro ? "hist-matriz__sem-registro" : "" }, [
          el("span", { class: "hist-matriz__rlabel" }, [`R${r.round}`]),
          el("span", { class: "hist-matriz__rcorrida" }, [r.race]),
          r.semRegistro ? el("span", { class: "hist-matriz__rnota" }, ["(sem registro)"]) : null,
        ])
      ),
    ]),
  ]);
  const tbody = el("tbody");
  posicoesTopN().forEach((pos, idx) => {
    tbody.appendChild(
      el("tr", {}, [
        el("th", { class: "hist-matriz__pos" }, [pos]),
        ...rodadas.map((r) => histCelula(r.round, idx, "top6")),
      ])
    );
  });
  if (FORMATO.bonus) {
    tbody.appendChild(
      el("tr", { class: "hist-matriz__linha-extra" }, [
        el("th", { class: "hist-matriz__pos" }, ["Piloto"]),
        ...rodadas.map((r) => histCelula(r.round, null, "extra")),
      ])
    );
  }
  tbody.appendChild(
    el("tr", { class: "hist-matriz__linha-total" }, [
      el("th", { class: "hist-matriz__pos" }, ["Total"]),
      ...rodadas.map((r) => histCelula(r.round, null, "total")),
    ])
  );
  document.getElementById("hist-matriz").replaceChildren(thead, tbody);
}

function renderHistPorCorrida() {
  const primeiro = histSelecionados[0];
  renderPalpitesJogador(primeiro, histBets, histStandings);
  const nota = document.getElementById("hist-porcorrida__nota");
  if (nota) {
    nota.textContent =
      histSelecionados.length > 1
        ? `Mostrando ${histBets.players[primeiro].name} (primeiro jogador selecionado).`
        : "";
  }
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
    badgePonto(rodada.bonus_points, FORMATO.bonus_points),
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
    el("div", { class: "rodada-card__body" }, FORMATO.bonus ? [cardTop6(rodada), linhaBonus(rodada)] : [cardTop6(rodada)]),
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
// Estado do toggle "Pontos"/"Posição" do gráfico acumulado (só front-end).
let modoGraficoAcumulado = "posicao";
// Séries auxiliares usadas pelos tooltips e pelo modo "Posição".
let dadosTemporada = null;

// Traço vertical que acompanha o mouse, deixando claro qual rodada está sendo lida.
const pluginLinhaRodada = {
  id: "linhaRodada",
  afterDatasetsDraw(chart) {
    const ativos = chart.tooltip && chart.tooltip.getActiveElements ? chart.tooltip.getActiveElements() : [];
    if (!ativos.length) return;
    const x = ativos[0].element.x;
    const { top, bottom } = chart.chartArea;
    const ctx = chart.ctx;
    ctx.save();
    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = corCss("--texto-fraco");
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    ctx.stroke();
    ctx.restore();
  },
};

function construirSerieJogador(jogador, rounds, cor) {
  const compensadas = new Set(jogador.compensated_rounds);
  const porRodada = [];
  const acumulado = [];
  const pointStyle = [];
  const pointRadius = [];
  const pointBackgroundColor = [];
  const compensadoPorIndice = [];
  // O acumulado (e a posição no ranking) parte do saldo de corridas anteriores
  // às que têm palpite (2021), para bater com o `total` do standings.
  let soma = jogador.carry_points || 0;

  for (const rodada of rounds) {
    const numero = rodada.round;
    let valor; // pontos da rodada (por-rodada); null = não apostou aquela corrida
    if (compensadas.has(numero)) {
      valor = rodada.min_score;
      pointStyle.push("triangle");
      pointRadius.push(6);
      pointBackgroundColor.push("#fff");
      compensadoPorIndice.push(true);
    } else {
      const p = jogador.per_round[numero];
      valor = p ?? null;
      pointStyle.push("circle");
      // Sem palpite e sem compensação: a linha acumulada segue reta (o total
      // não muda), sem marcador — o jogador NÃO some do ranking daquela rodada.
      pointRadius.push(p == null ? 0 : 4);
      pointBackgroundColor.push(cor);
      compensadoPorIndice.push(false);
    }
    porRodada.push(valor);
    soma += valor ?? 0;
    acumulado.push(soma);
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

// Posição de cada jogador em cada rodada, calculada sobre TODOS os jogadores
// (independe de quais linhas estão ligadas nos cards). Mesmo critério de
// desempate do resto do site: pontos desc, depois player_id asc.
function calcularPosicoesPorRodada(datasets, totalRodadas) {
  const posicoes = new Map(datasets.map((d) => [d.playerId, []]));

  for (let i = 0; i < totalRodadas; i++) {
    datasets
      .map((d) => ({ playerId: d.playerId, valor: d.data[i] }))
      .filter((e) => e.valor != null)
      .sort((a, b) => b.valor - a.valor || a.playerId.localeCompare(b.playerId))
      .forEach((e, indice) => posicoes.get(e.playerId).push(indice + 1));
    for (const d of datasets) {
      if (d.data[i] == null) posicoes.get(d.playerId).push(null);
    }
  }
  return posicoes;
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

  // Posição no ranking da temporada (pelo acumulado) e ordem de pontos dentro
  // de cada corrida (pelo por-rodada) — as duas alimentam os tooltips.
  const posicoesRanking = calcularPosicoesPorRodada(datasetsAcumulado, rounds.length);
  const posicoesNaRodada = calcularPosicoesPorRodada(datasetsPorRodada, rounds.length);

  // Cópias das séries de pontos: os arrays dentro dos datasets pertencem ao
  // Chart.js e são trocados pelo toggle Pontos/Posição — os tooltips precisam
  // dos pontos originais mesmo quando o eixo Y está mostrando posição.
  const pontosAcumulados = new Map(datasetsAcumulado.map((d) => [d.playerId, d.data.slice()]));
  const pontosPorRodada = new Map(datasetsPorRodada.map((d) => [d.playerId, d.data.slice()]));

  return {
    labels: rounds.map((r) => r.race),
    rounds,
    datasetsAcumulado,
    datasetsPorRodada,
    pontosAcumulados,
    pontosPorRodada,
    posicoesRanking,
    posicoesNaRodada,
  };
}

function formatarDeltaPosicao(posicao, anterior) {
  if (posicao == null || anterior == null) return "";
  const diferenca = anterior - posicao;
  if (diferenca > 0) return `  ▲${diferenca}`;
  if (diferenca < 0) return `  ▼${-diferenca}`;
  return "  =";
}

// Eixo Y do modo "Posição": 1º no topo, um tique por posição.
// O limite vai meio tique além das pontas (0.5 / n+0.5) para a linha do 1º e a
// do último não colarem na borda do gráfico; `afterBuildTicks` garante que
// mesmo assim só apareçam tiques em posições inteiras.
function escalaPosicao(corTexto, corGrade, totalJogadores) {
  return {
    reverse: true,
    min: 0.5,
    max: totalJogadores + 0.5,
    afterBuildTicks: (eixo) => {
      eixo.ticks = Array.from({ length: totalJogadores }, (_, i) => ({ value: i + 1 }));
    },
    ticks: { color: corTexto, stepSize: 1, precision: 0 },
    grid: { color: corGrade },
    title: { display: true, text: "Posição no ranking", color: corTexto },
  };
}

function escalaPontos(corTexto, corGrade, tituloEixoY) {
  return {
    beginAtZero: true,
    ticks: { color: corTexto },
    grid: { color: corGrade },
    title: { display: true, text: tituloEixoY, color: corTexto },
  };
}

// `tipo`: "acumulado" (posição no ranking da temporada, com Δ entre rodadas) ou
// "rodada" (ordem de pontos dentro daquela corrida).
function criarGraficoTemporada(canvasId, labels, datasets, standings, tituloEixoY, tipo) {
  const corTexto = corCss("--texto-fraco");
  const corGrade = corCss("--borda");
  const ctx = document.getElementById(canvasId).getContext("2d");
  const posicoesDe = (playerId) =>
    (tipo === "acumulado" ? dadosTemporada.posicoesRanking : dadosTemporada.posicoesNaRodada).get(playerId) || [];

  return new Chart(ctx, {
    type: "line",
    plugins: [pluginLinhaRodada],
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      // "index" = passar o mouse em qualquer altura da faixa da rodada mostra
      // todos os jogadores de uma vez, para comparar rodada a rodada.
      interaction: { mode: "index", intersect: false, axis: "x" },
      plugins: {
        legend: { display: false },
        tooltip: {
          usePointStyle: true,
          bodyFont: { size: 11 },
          padding: 10,
          // Sempre na ordem do ranking (ou dos pontos da corrida), não na ordem
          // dos datasets.
          itemSort(a, b) {
            const pa = posicoesDe(a.dataset.playerId)[a.dataIndex] ?? Infinity;
            const pb = posicoesDe(b.dataset.playerId)[b.dataIndex] ?? Infinity;
            return pa - pb;
          },
          callbacks: {
            title(itens) {
              if (!itens.length) return "";
              const rodada = dadosTemporada.rounds[itens[0].dataIndex];
              return `R${rodada.round} · ${rodada.race}`;
            },
            label(item) {
              const rodada = dadosTemporada.rounds[item.dataIndex];
              const playerId = item.dataset.playerId;
              const jogador = standings.players.find((p) => p.player_id === playerId);
              const compensou = jogador && jogador.compensated_rounds.includes(rodada.round);
              const posicoes = posicoesDe(playerId);
              const posicao = posicoes[item.dataIndex];
              // Em "acumulado" o valor exibido é sempre os pontos acumulados,
              // mesmo quando o eixo Y está mostrando posição.
              const serie = (
                tipo === "acumulado" ? dadosTemporada.pontosAcumulados : dadosTemporada.pontosPorRodada
              ).get(playerId);
              const pontos = serie ? serie[item.dataIndex] : null;
              const delta = tipo === "acumulado" ? formatarDeltaPosicao(posicao, posicoes[item.dataIndex - 1]) : "";
              const prefixo = posicao == null ? "" : `${posicao}º  `;
              return `${prefixo}${item.dataset.label} — ${pontos ?? "-"} pts${delta}${compensou ? "  (mínima)" : ""}`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { color: corTexto }, grid: { color: corGrade } },
        y: escalaPontos(corTexto, corGrade, tituloEixoY),
      },
    },
  });
}

// Alterna o eixo Y do gráfico acumulado entre pontos e posição no ranking.
// Troca só o `.data` de cada dataset (preserva o `hidden` dos cards de jogador).
function aplicarModoAcumulado(modo) {
  modoGraficoAcumulado = modo;
  const chart = graficoTemporadaAcumulado;
  if (!chart || !dadosTemporada) return;

  const posicao = modo === "posicao";
  const origem = posicao ? dadosTemporada.posicoesRanking : dadosTemporada.pontosAcumulados;
  chart.data.datasets.forEach((dataset) => {
    dataset.data = (origem.get(dataset.playerId) || []).slice();
  });
  const corTexto = corCss("--texto-fraco");
  const corGrade = corCss("--borda");
  chart.options.scales.y = posicao
    ? escalaPosicao(corTexto, corGrade, Math.max(dadosTemporada.datasetsAcumulado.length, 2))
    : escalaPontos(corTexto, corGrade, "Pontos acumulados");
  chart.update();

  const titulo = document.getElementById("temporada-titulo-acumulado");
  if (titulo) titulo.textContent = posicao ? "Posição no ranking" : "Pontuação acumulada";
  document.querySelectorAll("#temporada-modo-acumulado .temporada-modo__btn").forEach((botao) => {
    const ativo = botao.dataset.modo === modo;
    botao.classList.toggle("temporada-modo__btn--ativo", ativo);
    botao.setAttribute("aria-pressed", ativo ? "true" : "false");
  });
}

function configurarModoAcumulado() {
  document.querySelectorAll("#temporada-modo-acumulado .temporada-modo__btn").forEach((botao) => {
    botao.addEventListener("click", () => aplicarModoAcumulado(botao.dataset.modo));
  });
}

function renderTemporada(standings) {
  dadosTemporada = construirDadosTemporada(standings);
  const { labels, datasetsAcumulado, datasetsPorRodada } = dadosTemporada;

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
    "temporada-grafico-acumulado", labels, datasetsAcumulado, standings, "Pontos acumulados", "acumulado"
  );
  graficoTemporadaPorRodada = criarGraficoTemporada(
    "temporada-grafico", labels, datasetsPorRodada, standings, "Pontos na rodada", "rodada"
  );
  if (modoGraficoAcumulado !== "pontos") aplicarModoAcumulado(modoGraficoAcumulado);
}

// ---------- Preferência piloto ----------

// Usado pelos filtros com opção "Todos" (Preferência piloto e Rendimento).
function popularSelectComTodos(selectId, bets) {
  const select = document.getElementById(selectId);
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

function calcularPosicaoMediaReal(results) {
  const porPiloto = new Map(); // codigo -> { soma, count }
  for (const rodada of Object.values(results.rounds)) {
    (rodada.order || []).forEach((codigo, indice) => {
      const posicao = indice + 1;
      const registro = porPiloto.get(codigo) || { soma: 0, count: 0 };
      registro.soma += posicao;
      registro.count += 1;
      porPiloto.set(codigo, registro);
    });
  }
  const medias = new Map();
  for (const [codigo, { soma, count }] of porPiloto) {
    medias.set(codigo, soma / count);
  }
  return medias;
}

function badgeDistanciaReal(media, mediaReal) {
  const diferenca = media - mediaReal;
  const seta = diferenca >= 0 ? "▲" : "▼";
  return el("span", { class: "distancia-badge" }, [seta, ` ${Math.abs(diferenca).toFixed(2)}`]);
}

function renderPreferenciaPiloto(playerId, bets, results) {
  const container = document.getElementById("preferencia-container");
  const universo = coletarPalpitesTop6(bets, "todos");
  const porPiloto = playerId === "todos" ? universo : coletarPalpitesTop6(bets, playerId);
  const posicaoMediaReal = calcularPosicaoMediaReal(results);

  const linhas = [...universo.keys()]
    .map((codigo) => {
      const registro = porPiloto.get(codigo);
      return {
        codigo,
        media: registro ? registro.soma / registro.count : null,
        count: registro ? registro.count : 0,
        mediaReal: posicaoMediaReal.get(codigo) ?? null,
      };
    })
    .sort((a, b) => {
      if (a.media !== null && b.media !== null) return a.media - b.media || a.codigo.localeCompare(b.codigo);
      if (a.media !== null) return -1;
      if (b.media !== null) return 1;
      const realA = a.mediaReal ?? Infinity;
      const realB = b.mediaReal ?? Infinity;
      return realA - realB || a.codigo.localeCompare(b.codigo);
    });

  if (!linhas.length) {
    container.replaceChildren(el("p", { class: "status" }, ["Sem palpites de top6 registrados."]));
    return;
  }

  const tabela = el("table", { class: "preferencia-tabela" }, [
    el("thead", {}, [
      el("tr", {}, [
        el("th", {}, ["Piloto"]),
        el("th", { class: "num" }, ["Posição Média REAL"]),
        el("th", { class: "num" }, ["Posição média palpite"]),
        el("th", { class: "num" }, ["Vezes apostado"]),
      ]),
    ]),
  ]);
  const tbody = el("tbody");
  for (const linha of linhas) {
    tbody.appendChild(
      el("tr", {}, [
        el("td", {}, [chipPiloto(linha.codigo)]),
        el("td", { class: "num" }, [linha.mediaReal === null ? "-" : linha.mediaReal.toFixed(2)]),
        el(
          "td",
          { class: "num" },
          linha.media === null
            ? ["-"]
            : [
                `${linha.media.toFixed(2)} `,
                ...(linha.mediaReal === null ? [] : [badgeDistanciaReal(linha.media, linha.mediaReal)]),
              ]
        ),
        el("td", { class: "num" }, [String(linha.count)]),
      ])
    );
  }
  tabela.appendChild(tbody);
  container.replaceChildren(tabela);
}

// ---------- Rendimento (top6) — por piloto ou por jogador ----------

let graficoRendimento = null;
let graficoRendimentoPorJogador = null;
let rendimentoEstado = null; // { bets, ids, linhas }
let rendimentoPorJogadorEstado = null; // { bets, codigos, linhas }

let rendimentoModo = "piloto"; // "piloto" | "jogador"
let rendimentoBets = null;
let rendimentoJogadores = []; // lista ordenada por nome (cor estável por índice)
let rendimentoPilotos = []; // códigos de piloto já apostados (ordem alfabética)
let rendimentoSelJogadores = new Set(); // filtro do modo "por piloto"
let rendimentoSelPilotos = new Set(); // filtro do modo "por jogador"

// Ordem estável dos jogadores (por nome), usada para a cor fixa de cada um.
function ordemJogadores(bets) {
  return Object.values(bets.players).sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
}

function nomeJogadorBets(bets, playerId) {
  const jogador = bets.players[playerId];
  return jogador ? jogador.name : playerId;
}

function corRendimentoJogador(playerId) {
  const indice = rendimentoJogadores.findIndex((j) => j.player_id === playerId);
  return corJogador(indice < 0 ? 0 : indice);
}

// Cada filtro devolve "todos" (tudo marcado), [] (nada) ou a lista marcada.
function rendimentoIdsJogadoresAtivos() {
  if (rendimentoSelJogadores.size === 0) return [];
  if (rendimentoSelJogadores.size === rendimentoJogadores.length) return "todos";
  return rendimentoJogadores.map((j) => j.player_id).filter((id) => rendimentoSelJogadores.has(id));
}

function rendimentoCodigosAtivos() {
  if (rendimentoSelPilotos.size === 0) return [];
  if (rendimentoSelPilotos.size === rendimentoPilotos.length) return "todos";
  return rendimentoPilotos.filter((c) => rendimentoSelPilotos.has(c));
}

function rendimentoRotuloSelecao(ids) {
  if (ids === "todos") return "todos os jogadores";
  if (ids.length === 1) return nomeJogadorBets(rendimentoBets, ids[0]);
  return `${ids.length} jogadores selecionados`;
}

function rendimentoRotuloPilotos(codigos) {
  if (codigos === "todos") return "todos os pilotos";
  if (codigos.length <= 3) return codigos.join(", ");
  return `${codigos.length} pilotos selecionados`;
}

// Quanto cada piloto rende para quem aposta nele: percorre os palpites de top6
// e soma os pontos que cada piloto escolhido gerou (2 pt posição exata, 1 pt
// dentro do top6 real, 0 fora). O piloto da rodada (bônus) fica de fora — ele é
// definido pela rodada, ninguém "aposta nele" por escolha própria.
function coletarRendimento(bets, ids) {
  const jogadores =
    ids === "todos" ? Object.values(bets.players) : ids.map((id) => bets.players[id]).filter(Boolean);
  const porPiloto = new Map(); // codigo -> { apostas, pontos, exatas, dentro, fora }

  for (const jogador of jogadores) {
    for (const rodada of Object.values(jogador.rounds)) {
      for (const detalhe of rodada.top6_detail || []) {
        const registro =
          porPiloto.get(detalhe.guess) || { apostas: 0, pontos: 0, exatas: 0, dentro: 0, fora: 0 };
        registro.apostas += 1;
        registro.pontos += detalhe.points;
        if (detalhe.points >= 2) registro.exatas += 1;
        else if (detalhe.points === 1) registro.dentro += 1;
        else registro.fora += 1;
        porPiloto.set(detalhe.guess, registro);
      }
    }
  }
  return porPiloto;
}

// Modo "por piloto": um piloto por linha, com o rendimento dos jogadores
// selecionados e a média geral (todos os jogadores) ao lado para comparar.
function construirLinhasRendimento(bets, ids) {
  const geral = coletarRendimento(bets, "todos");
  const doFiltro = coletarRendimento(bets, ids);

  return [...doFiltro.entries()]
    .map(([codigo, registro]) => {
      const registroGeral = geral.get(codigo);
      return {
        codigo,
        ...registro,
        media: registro.pontos / registro.apostas,
        apostasGeral: registroGeral ? registroGeral.apostas : 0,
        mediaGeral: registroGeral ? registroGeral.pontos / registroGeral.apostas : null,
      };
    })
    .sort((a, b) => b.media - a.media || b.apostas - a.apostas || a.codigo.localeCompare(b.codigo));
}

// Rendimento de cada jogador no top6, considerando só os pilotos em `codigos`
// ("todos" = qualquer piloto).
function coletarRendimentoPorJogador(bets, codigos) {
  const porJogador = new Map(); // playerId -> { apostas, pontos, exatas, dentro, fora }
  for (const jogador of Object.values(bets.players)) {
    for (const rodada of Object.values(jogador.rounds)) {
      for (const detalhe of rodada.top6_detail || []) {
        if (codigos !== "todos" && !codigos.includes(detalhe.guess)) continue;
        const registro =
          porJogador.get(jogador.player_id) || { apostas: 0, pontos: 0, exatas: 0, dentro: 0, fora: 0 };
        registro.apostas += 1;
        registro.pontos += detalhe.points;
        if (detalhe.points >= 2) registro.exatas += 1;
        else if (detalhe.points === 1) registro.dentro += 1;
        else registro.fora += 1;
        porJogador.set(jogador.player_id, registro);
      }
    }
  }
  return porJogador;
}

// Modo "por jogador": TODOS os jogadores aparecem; o filtro escolhe quais
// pilotos entram na conta. `mediaGeral` = rendimento do jogador somando todos os
// pilotos (base de comparação quando há filtro de piloto ativo).
function construirLinhasRendimentoPorJogador(bets, codigos) {
  const doFiltro = coletarRendimentoPorJogador(bets, codigos);
  const geral = coletarRendimentoPorJogador(bets, "todos");
  const vazio = { apostas: 0, pontos: 0, exatas: 0, dentro: 0, fora: 0 };

  return rendimentoJogadores
    .map((j) => {
      const registro = doFiltro.get(j.player_id) || vazio;
      const registroGeral = geral.get(j.player_id);
      return {
        playerId: j.player_id,
        ...registro,
        media: registro.apostas ? registro.pontos / registro.apostas : 0,
        mediaGeral: registroGeral && registroGeral.apostas ? registroGeral.pontos / registroGeral.apostas : null,
      };
    })
    .sort(
      (a, b) =>
        (a.apostas === 0) - (b.apostas === 0) ||
        b.media - a.media ||
        nomeJogadorBets(bets, a.playerId).localeCompare(nomeJogadorBets(bets, b.playerId), "pt-BR")
    );
}

// Sinaliza rendimento acima (▲) ou abaixo (▼) da média de comparação.
function badgeRendimentoGeral(media, mediaGeral) {
  const diferenca = media - mediaGeral;
  const seta = diferenca >= 0 ? "▲" : "▼";
  return el("span", { class: "distancia-badge" }, [seta, ` ${Math.abs(diferenca).toFixed(2)}`]);
}

// ----- Modo "por piloto" -----

function renderGraficoRendimento(linhas, ids, bets) {
  const canvas = document.getElementById("rendimento-grafico");
  const comparando = ids !== "todos";
  canvas.parentElement.style.height = `${Math.max(200, linhas.length * (comparando ? 34 : 26) + 56)}px`;

  const corTexto = corCss("--texto-fraco");
  const corGrade = corCss("--borda");
  const datasets = [
    {
      label: comparando ? rendimentoRotuloSelecao(ids) : "Todos os jogadores",
      data: linhas.map((linha) => linha.media),
      backgroundColor: linhas.map((linha) => corPiloto(linha.codigo)),
      borderWidth: 0,
    },
  ];
  if (comparando) {
    datasets.push({
      label: "Média geral (todos)",
      data: linhas.map((linha) => linha.mediaGeral),
      backgroundColor: corGrade,
      borderWidth: 0,
    });
  }

  if (graficoRendimento) graficoRendimento.destroy();
  graficoRendimento = new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: { labels: linhas.map((linha) => linha.codigo), datasets },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          display: comparando,
          labels: { color: corTexto, boxWidth: 12, boxHeight: 8, font: { size: 11 } },
        },
        tooltip: {
          callbacks: {
            label(item) {
              const linha = linhas[item.dataIndex];
              const geral = item.datasetIndex === 1;
              const media = geral ? linha.mediaGeral : linha.media;
              const apostas = geral ? linha.apostasGeral : linha.apostas;
              return `${item.dataset.label}: ${media.toFixed(2)} pts/aposta (${apostas} apostas)`;
            },
          },
        },
      },
      scales: {
        x: {
          min: 0,
          max: 2,
          ticks: { color: corTexto, stepSize: 0.5 },
          grid: { color: corGrade },
          title: { display: true, text: "Pontos por aposta (máx. 2)", color: corTexto },
        },
        y: { ticks: { color: corTexto, font: { size: 11 } }, grid: { display: false } },
      },
    },
  });
}

function renderTabelaRendimento(linhas, comparando) {
  const container = document.getElementById("rendimento-container");
  const cabecalho = [
    el("th", { class: "num" }, ["#"]),
    el("th", {}, ["Piloto"]),
    el("th", { class: "num" }, ["Pts/aposta"]),
    comparando ? el("th", { class: "num" }, ["Média geral"]) : null,
    el("th", { class: "num" }, ["Pontos"]),
    el("th", { class: "num" }, ["Apostas"]),
    el("th", { class: "num" }, ["2 pt"]),
    el("th", { class: "num" }, ["1 pt"]),
    el("th", { class: "num" }, ["0 pt"]),
  ].filter(Boolean);

  const tabela = el("table", { class: "rendimento-tabela" }, [el("thead", {}, [el("tr", {}, cabecalho)])]);
  const tbody = el("tbody");
  linhas.forEach((linha, indice) => {
    tbody.appendChild(
      el(
        "tr",
        {},
        [
          el("td", { class: "num rendimento-pos" }, [String(indice + 1)]),
          el("td", {}, [chipPiloto(linha.codigo)]),
          el("td", { class: "num rendimento-media" }, [
            `${linha.media.toFixed(2)} `,
            ...(comparando && linha.mediaGeral !== null ? [badgeRendimentoGeral(linha.media, linha.mediaGeral)] : []),
          ]),
          comparando ? el("td", { class: "num" }, [linha.mediaGeral === null ? "-" : linha.mediaGeral.toFixed(2)]) : null,
          el("td", { class: "num" }, [String(linha.pontos)]),
          el("td", { class: "num" }, [String(linha.apostas)]),
          el("td", { class: "num" }, [String(linha.exatas)]),
          el("td", { class: "num" }, [String(linha.dentro)]),
          el("td", { class: "num" }, [String(linha.fora)]),
        ].filter(Boolean)
      )
    );
  });
  tabela.appendChild(tbody);
  container.replaceChildren(el("div", { class: "rendimento-tabela-wrap" }, [tabela]));
}

function renderRendimento(ids, bets) {
  const titulo = document.getElementById("rendimento-titulo");
  const container = document.getElementById("rendimento-container");

  if (Array.isArray(ids) && !ids.length) {
    rendimentoEstado = { bets, ids, linhas: [] };
    titulo.textContent = "Pontos que cada piloto rende por aposta";
    container.replaceChildren(el("p", { class: "status" }, ["Selecione ao menos um jogador."]));
    if (graficoRendimento) {
      graficoRendimento.destroy();
      graficoRendimento = null;
    }
    return;
  }

  const linhas = construirLinhasRendimento(bets, ids);
  const comparando = ids !== "todos";
  rendimentoEstado = { bets, ids, linhas };

  titulo.textContent =
    ids === "todos"
      ? "Pontos que cada piloto rende por aposta"
      : `Rendimento por piloto — ${rendimentoRotuloSelecao(ids)}`;

  if (!linhas.length) {
    container.replaceChildren(el("p", { class: "status" }, ["Sem palpites de top6 registrados."]));
    if (graficoRendimento) {
      graficoRendimento.destroy();
      graficoRendimento = null;
    }
    return;
  }

  renderTabelaRendimento(linhas, comparando);
  if (rendimentoGraficoVisivel("piloto")) renderGraficoRendimento(linhas, ids, bets);
  else if (graficoRendimento) {
    graficoRendimento.destroy();
    graficoRendimento = null;
  }
}

// ----- Modo "por jogador" -----

function renderGraficoRendimentoPorJogador(linhas, codigos, bets) {
  const canvas = document.getElementById("rendimento-jogador-grafico");
  const comparando = codigos !== "todos";
  canvas.parentElement.style.height = `${Math.max(200, linhas.length * (comparando ? 34 : 30) + 56)}px`;

  const corTexto = corCss("--texto-fraco");
  const corGrade = corCss("--borda");
  const datasets = [
    {
      label: comparando ? rendimentoRotuloPilotos(codigos) : "Todos os pilotos",
      data: linhas.map((linha) => linha.media),
      backgroundColor: linhas.map((linha) => corRendimentoJogador(linha.playerId)),
      borderWidth: 0,
    },
  ];
  if (comparando) {
    datasets.push({
      label: "Média geral (todos os pilotos)",
      data: linhas.map((linha) => (linha.mediaGeral === null ? 0 : linha.mediaGeral)),
      backgroundColor: corGrade,
      borderWidth: 0,
    });
  }

  if (graficoRendimentoPorJogador) graficoRendimentoPorJogador.destroy();
  graficoRendimentoPorJogador = new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: { labels: linhas.map((linha) => nomeJogadorBets(bets, linha.playerId)), datasets },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          display: comparando,
          labels: { color: corTexto, boxWidth: 12, boxHeight: 8, font: { size: 11 } },
        },
        tooltip: {
          callbacks: {
            label(item) {
              const linha = linhas[item.dataIndex];
              if (item.datasetIndex === 1) {
                return `Média geral: ${linha.mediaGeral === null ? "–" : linha.mediaGeral.toFixed(2)} pts/aposta`;
              }
              if (!linha.apostas) return "sem apostas nesse(s) piloto(s)";
              return `${linha.media.toFixed(2)} pts/aposta (${linha.apostas} apostas)`;
            },
          },
        },
      },
      scales: {
        x: {
          min: 0,
          max: 2,
          ticks: { color: corTexto, stepSize: 0.5 },
          grid: { color: corGrade },
          title: { display: true, text: "Pontos por aposta (máx. 2)", color: corTexto },
        },
        y: { ticks: { color: corTexto, font: { size: 11 } }, grid: { display: false } },
      },
    },
  });
}

function renderTabelaRendimentoPorJogador(linhas, comparando, bets) {
  const container = document.getElementById("rendimento-jogador-container");
  const cabecalho = [
    el("th", { class: "num" }, ["#"]),
    el("th", {}, ["Jogador"]),
    el("th", { class: "num" }, ["Pts/aposta"]),
    comparando ? el("th", { class: "num" }, ["Média geral"]) : null,
    el("th", { class: "num" }, ["Pontos"]),
    el("th", { class: "num" }, ["Apostas"]),
    el("th", { class: "num" }, ["2 pt"]),
    el("th", { class: "num" }, ["1 pt"]),
    el("th", { class: "num" }, ["0 pt"]),
  ].filter(Boolean);

  const tabela = el("table", { class: "rendimento-tabela" }, [el("thead", {}, [el("tr", {}, cabecalho)])]);
  const tbody = el("tbody");
  linhas.forEach((linha, indice) => {
    tbody.appendChild(
      el(
        "tr",
        {},
        [
          el("td", { class: "num rendimento-pos" }, [String(indice + 1)]),
          el("td", {}, [
            el("span", { class: "piloto-chip" }, [
              el("span", {
                class: "piloto-bolinha",
                style: `background:${corRendimentoJogador(linha.playerId)}`,
              }),
              nomeJogadorBets(bets, linha.playerId),
            ]),
          ]),
          el("td", { class: "num rendimento-media" }, [
            linha.apostas ? `${linha.media.toFixed(2)} ` : "– ",
            ...(comparando && linha.apostas && linha.mediaGeral !== null
              ? [badgeRendimentoGeral(linha.media, linha.mediaGeral)]
              : []),
          ]),
          comparando
            ? el("td", { class: "num" }, [linha.mediaGeral === null ? "-" : linha.mediaGeral.toFixed(2)])
            : null,
          el("td", { class: "num" }, [String(linha.pontos)]),
          el("td", { class: "num" }, [String(linha.apostas)]),
          el("td", { class: "num" }, [String(linha.exatas)]),
          el("td", { class: "num" }, [String(linha.dentro)]),
          el("td", { class: "num" }, [String(linha.fora)]),
        ].filter(Boolean)
      )
    );
  });
  tabela.appendChild(tbody);
  container.replaceChildren(el("div", { class: "rendimento-tabela-wrap" }, [tabela]));
}

function renderRendimentoPorJogador(codigos, bets) {
  const titulo = document.getElementById("rendimento-jogador-titulo");
  const container = document.getElementById("rendimento-jogador-container");

  if (Array.isArray(codigos) && !codigos.length) {
    rendimentoPorJogadorEstado = { bets, codigos, linhas: [] };
    titulo.textContent = "Pontos que cada jogador tira no top6";
    container.replaceChildren(el("p", { class: "status" }, ["Selecione ao menos um piloto."]));
    if (graficoRendimentoPorJogador) {
      graficoRendimentoPorJogador.destroy();
      graficoRendimentoPorJogador = null;
    }
    return;
  }

  const linhas = construirLinhasRendimentoPorJogador(bets, codigos);
  const comparando = codigos !== "todos";
  rendimentoPorJogadorEstado = { bets, codigos, linhas };

  titulo.textContent =
    codigos === "todos"
      ? "Pontos que cada jogador tira no top6"
      : `Rendimento no top6 — ${rendimentoRotuloPilotos(codigos)}`;

  renderTabelaRendimentoPorJogador(linhas, comparando, bets);
  if (rendimentoGraficoVisivel("jogador")) renderGraficoRendimentoPorJogador(linhas, codigos, bets);
  else if (graficoRendimentoPorJogador) {
    graficoRendimentoPorJogador.destroy();
    graficoRendimentoPorJogador = null;
  }
}

// ----- Filtro (chips) + switch de modo -----

function rendimentoGraficoVisivel(modo) {
  if (document.getElementById("secao-palpites").hidden) return false;
  if (document.getElementById("subsecao-rendimento").hidden) return false;
  return !document.getElementById(`rendimento-view-${modo}`).hidden;
}

function chipRendimento(rotulo, cor, dataAttr, valor, selecao) {
  const chip = el(
    "button",
    {
      type: "button",
      class: "rendimento-chip",
      [dataAttr]: valor,
      "aria-pressed": "false",
      style: `--cor-chip:${cor}`,
    },
    [el("span", { class: "rendimento-chip__ponto" }), rotulo]
  );
  chip.addEventListener("click", () => {
    if (selecao.has(valor)) selecao.delete(valor);
    else selecao.add(valor);
    atualizarRendimento();
  });
  return chip;
}

// A tira de chips muda de conteúdo conforme o modo: no modo "por piloto" são os
// jogadores (quem entra na conta); no modo "por jogador" são os pilotos (quais
// pilotos considerar) e todos os jogadores aparecem no gráfico.
function popularRendimentoChips() {
  const box = document.getElementById("rendimento-jogadores");
  const dica = document.getElementById("rendimento-chips-dica");
  if (rendimentoModo === "piloto") {
    box.setAttribute("aria-label", "Jogadores na conta");
    dica.textContent = "Jogadores incluídos na média de cada piloto:";
    box.replaceChildren(
      ...rendimentoJogadores.map((j) =>
        chipRendimento(j.name, corRendimentoJogador(j.player_id), "data-player", j.player_id, rendimentoSelJogadores)
      )
    );
  } else {
    box.setAttribute("aria-label", "Pilotos considerados");
    dica.textContent = "Pilotos considerados (todos os jogadores aparecem no gráfico):";
    box.replaceChildren(
      ...rendimentoPilotos.map((c) => chipRendimento(c, corPiloto(c), "data-piloto", c, rendimentoSelPilotos))
    );
  }
  sincronizarRendimentoChips();
}

function sincronizarRendimentoChips() {
  document.querySelectorAll("#rendimento-jogadores .rendimento-chip").forEach((chip) => {
    const marcado = chip.dataset.player
      ? rendimentoSelJogadores.has(chip.dataset.player)
      : rendimentoSelPilotos.has(chip.dataset.piloto);
    chip.setAttribute("aria-pressed", marcado ? "true" : "false");
  });
}

function atualizarRendimento() {
  sincronizarRendimentoChips();
  if (rendimentoModo === "piloto") renderRendimento(rendimentoIdsJogadoresAtivos(), rendimentoBets);
  else renderRendimentoPorJogador(rendimentoCodigosAtivos(), rendimentoBets);
}

function configurarRendimento() {
  document.querySelectorAll("#rendimento-modo .rendimento-modo__btn").forEach((botao) => {
    botao.addEventListener("click", () => {
      rendimentoModo = botao.dataset.modo;
      document.querySelectorAll("#rendimento-modo .rendimento-modo__btn").forEach((b) => {
        const ativo = b === botao;
        b.classList.toggle("rendimento-modo__btn--ativo", ativo);
        b.setAttribute("aria-pressed", ativo ? "true" : "false");
      });
      document.getElementById("rendimento-view-piloto").hidden = rendimentoModo !== "piloto";
      document.getElementById("rendimento-view-jogador").hidden = rendimentoModo !== "jogador";
      // Descarta o gráfico do modo que saiu de cena (evita canvas 0×0 preso).
      if (rendimentoModo === "piloto" && graficoRendimentoPorJogador) {
        graficoRendimentoPorJogador.destroy();
        graficoRendimentoPorJogador = null;
      }
      if (rendimentoModo === "jogador" && graficoRendimento) {
        graficoRendimento.destroy();
        graficoRendimento = null;
      }
      popularRendimentoChips();
      atualizarRendimento();
    });
  });

  document.querySelectorAll("#rendimento-jogadores-acoes .rendimento-jogadores__acao").forEach((botao) => {
    botao.addEventListener("click", () => {
      const marcarTudo = botao.dataset.acao === "todos";
      if (rendimentoModo === "piloto") {
        rendimentoSelJogadores.clear();
        if (marcarTudo) rendimentoJogadores.forEach((j) => rendimentoSelJogadores.add(j.player_id));
      } else {
        rendimentoSelPilotos.clear();
        if (marcarTudo) rendimentoPilotos.forEach((c) => rendimentoSelPilotos.add(c));
      }
      atualizarRendimento();
    });
  });
}

// ---------- Pilotos (distribuição da posição real no quali) ----------

// Junta, por piloto, todas as posições em que ele largou nos quali já disputados
// (results.json, rounds[].order — índice 0 = P1). `maxGrid` = maior grid visto.
function coletarPosicoesReais(results) {
  const porPiloto = new Map(); // codigo -> number[]
  let maxGrid = 0;
  for (const rodada of Object.values(results.rounds)) {
    const order = rodada.order || [];
    maxGrid = Math.max(maxGrid, order.length);
    order.forEach((codigo, indice) => {
      if (!porPiloto.has(codigo)) porPiloto.set(codigo, []);
      porPiloto.get(codigo).push(indice + 1);
    });
  }
  return { porPiloto, maxGrid };
}

// Densidade por kernel gaussiano (para o contorno do violino). Amostras poucas
// e discretas (posições 1..22), então a banda suaviza o histograma.
function densidadeGaussiana(amostras, xs, banda) {
  const n = amostras.length;
  const norm = 1 / (n * banda * Math.sqrt(2 * Math.PI));
  return xs.map((x) => {
    let soma = 0;
    for (const a of amostras) {
      const u = (x - a) / banda;
      soma += Math.exp(-0.5 * u * u);
    }
    return soma * norm;
  });
}

function mediaLista(valores) {
  return valores.reduce((s, v) => s + v, 0) / valores.length;
}

function medianaLista(valores) {
  const ord = valores.slice().sort((a, b) => a - b);
  const meio = Math.floor(ord.length / 2);
  return ord.length % 2 ? ord[meio] : (ord[meio - 1] + ord[meio]) / 2;
}

// cont[p] = quantas vezes o piloto largou exatamente na posição p.
function contagemPorPosicao(posicoes, maxGrid) {
  const cont = new Array(maxGrid + 1).fill(0);
  for (const p of posicoes) cont[p] += 1;
  return cont;
}

// Um "violino" horizontal por piloto (uma linha cada), ordenados pela posição
// média real crescente (quem larga melhor no topo). Cada violino é normalizado
// para a mesma espessura máxima — a dispersão aparece pela largura da forma no
// eixo X, não pela altura.
function renderPilotos(results) {
  const container = document.getElementById("pilotos-container");
  const { porPiloto, maxGrid } = coletarPosicoesReais(results);

  const pilotos = [...porPiloto.entries()]
    .map(([codigo, posicoes]) => ({
      codigo,
      posicoes,
      media: mediaLista(posicoes),
      mediana: medianaLista(posicoes),
      melhor: Math.min(...posicoes),
      pior: Math.max(...posicoes),
    }))
    .sort((a, b) => a.media - b.media || a.codigo.localeCompare(b.codigo));

  if (!pilotos.length) {
    container.replaceChildren(el("p", { class: "status" }, ["Sem resultados de quali ainda."]));
    return;
  }

  const margemEsq = 54;
  const margemDir = 62;
  const margemTopo = 26;
  const margemBase = 28;
  const larguraPlot = 560;
  const alturaLinha = 30;
  const larguraTotal = margemEsq + larguraPlot + margemDir;
  const alturaTotal = margemTopo + pilotos.length * alturaLinha + margemBase;

  const xMin = 0.5;
  const xMax = maxGrid + 0.5;
  const escalaX = (pos) => margemEsq + ((pos - xMin) / (xMax - xMin)) * larguraPlot;

  const xs = [];
  for (let x = xMin; x <= xMax + 1e-9; x += 0.2) xs.push(x);
  const banda = 1.1;

  const corGrade = corCss("--borda");
  const corTexto = corCss("--texto-fraco");
  const corTextoForte = corCss("--texto");
  const corAcento = corCss("--acento");

  // Popup de contagem por classificação (mesmo estilo dos tooltips dos gráficos).
  const tooltip = el("div", { class: "pilotos-tooltip" });
  tooltip.hidden = true;

  function montarTooltip(piloto) {
    const cont = contagemPorPosicao(piloto.posicoes, maxGrid);
    const maxC = Math.max(...cont) || 1;
    const linhas = [];
    for (let p = 1; p <= maxGrid; p++) {
      if (!cont[p]) continue;
      linhas.push(
        el("div", { class: "pilotos-tooltip__linha" }, [
          el("span", { class: "pilotos-tooltip__pos" }, [`P${p}`]),
          el("span", { class: "pilotos-tooltip__barra-wrap" }, [
            el("span", {
              class: "pilotos-tooltip__barra",
              style: `width:${(cont[p] / maxC) * 100}%;background:${corPiloto(piloto.codigo)}`,
            }),
          ]),
          el("span", { class: "pilotos-tooltip__n" }, [String(cont[p])]),
        ])
      );
    }
    return [
      el("div", { class: "pilotos-tooltip__titulo" }, [`${piloto.codigo} · ${piloto.posicoes.length} quali`]),
      el("div", { class: "pilotos-tooltip__sub" }, [
        `média P${piloto.media.toFixed(1)} · mediana P${piloto.mediana} · melhor P${piloto.melhor} · pior P${piloto.pior}`,
      ]),
      ...linhas,
    ];
  }

  function posicionarTooltip(evento) {
    const rect = container.getBoundingClientRect();
    let x = evento.clientX - rect.left + 14;
    const y = evento.clientY - rect.top + 14;
    if (x + tooltip.offsetWidth > container.clientWidth - 4) {
      x = evento.clientX - rect.left - tooltip.offsetWidth - 14;
    }
    tooltip.style.left = `${Math.max(4, x)}px`;
    tooltip.style.top = `${y}px`;
  }

  function ligarTooltip(alvo, piloto) {
    alvo.addEventListener("pointerenter", (evento) => {
      tooltip.replaceChildren(...montarTooltip(piloto));
      tooltip.hidden = false;
      posicionarTooltip(evento);
    });
    alvo.addEventListener("pointermove", posicionarTooltip);
    alvo.addEventListener("pointerleave", () => {
      tooltip.hidden = true;
    });
  }

  const svg = svgEl("svg", {
    class: "pilotos-svg",
    width: larguraTotal,
    height: alturaTotal,
    viewBox: `0 0 ${larguraTotal} ${alturaTotal}`,
    role: "img",
    "aria-label": "Distribuição da posição real de largada no quali por piloto",
  });

  // Faixa do topN (leve destaque de fundo).
  svg.appendChild(
    svgEl("rect", {
      x: escalaX(0.5),
      y: margemTopo,
      width: escalaX(FORMATO.top_n + 0.5) - escalaX(0.5),
      height: alturaTotal - margemTopo - margemBase,
      fill: corAcento,
      opacity: 0.06,
    })
  );

  // Gridlines verticais + rótulos P# no topo e na base.
  for (let p = 1; p <= maxGrid; p++) {
    const x = escalaX(p);
    const destaque = p === 1 || p % 5 === 0;
    svg.appendChild(
      svgEl("line", {
        x1: x,
        y1: margemTopo,
        x2: x,
        y2: alturaTotal - margemBase,
        stroke: corGrade,
        "stroke-width": destaque ? 1 : 0.5,
        "stroke-dasharray": destaque ? "0" : "2 3",
      })
    );
    if (destaque) {
      for (const y of [margemTopo - 9, alturaTotal - margemBase + 16]) {
        svg.appendChild(
          svgEl("text", { x, y, "text-anchor": "middle", "font-size": 10, fill: corTexto }, [`P${p}`])
        );
      }
    }
  }

  pilotos.forEach((piloto, i) => {
    const cy = margemTopo + i * alturaLinha + alturaLinha / 2;
    const cor = corPiloto(piloto.codigo);
    const meiaAltura = alturaLinha * 0.42;
    // A gaussiana nunca zera de verdade, então limitamos o contorno à janela
    // onde o piloto realmente largou (± folga) — sem isso o violino vira um
    // fio de cabelo esticado até o fim do eixo.
    const janelaMin = Math.max(xMin, piloto.melhor - 1.5);
    const janelaMax = Math.min(xMax, piloto.pior + 1.5);
    const xsJanela = xs.filter((x) => x >= janelaMin && x <= janelaMax);
    const densidades = densidadeGaussiana(piloto.posicoes, xsJanela, banda);
    const maxDens = Math.max(...densidades) || 1;

    svg.appendChild(
      svgEl("line", {
        x1: margemEsq,
        y1: cy,
        x2: margemEsq + larguraPlot,
        y2: cy,
        stroke: corGrade,
        "stroke-width": 0.5,
      })
    );

    const topo = xsJanela.map(
      (x, k) => `${escalaX(x).toFixed(1)},${(cy - (densidades[k] / maxDens) * meiaAltura).toFixed(1)}`
    );
    const base = xsJanela
      .map((x, k) => `${escalaX(x).toFixed(1)},${(cy + (densidades[k] / maxDens) * meiaAltura).toFixed(1)}`)
      .reverse();
    const violino = svgEl("path", {
      d: `M ${topo.join(" L ")} L ${base.join(" L ")} Z`,
      fill: cor,
      "fill-opacity": 0.35,
      stroke: cor,
      "stroke-width": 1,
    });
    svg.appendChild(violino);

    // Cada quali como um ponto (jitter vertical determinístico p/ não empilhar).
    piloto.posicoes.forEach((pos, k) => {
      const jitter = (((k % 5) - 2) / 2) * (meiaAltura / 3);
      svg.appendChild(
        svgEl("circle", { cx: escalaX(pos), cy: cy + jitter, r: 1.8, fill: cor, "fill-opacity": 0.55 })
      );
    });

    svg.appendChild(svgEl("circle", { cx: 11, cy, r: 4, fill: cor }));
    svg.appendChild(
      svgEl("text", { x: 21, y: cy + 3.5, "font-size": 11, "font-weight": 700, fill: corTextoForte }, [
        piloto.codigo,
      ])
    );
    svg.appendChild(
      svgEl("text", { x: margemEsq + larguraPlot + 8, y: cy + 3.5, "font-size": 10.5, fill: corTexto }, [
        `P${piloto.media.toFixed(1)}`,
      ])
    );

    // Área invisível cobrindo a linha inteira do piloto — alvo do popup.
    const alvo = svgEl("rect", {
      x: margemEsq,
      y: cy - alturaLinha / 2,
      width: larguraPlot,
      height: alturaLinha,
      fill: "transparent",
    });
    alvo.style.cursor = "crosshair";
    ligarTooltip(alvo, piloto);
    svg.appendChild(alvo);
  });

  const legenda = el("p", { class: "preferencia-legenda" }, [
    "Cada linha é um piloto (ordenados pela posição média real crescente, mostrada à direita). A forma " +
      "mostra em que posições ele mais larga nos quali já disputados; cada ponto é um quali. " +
      `A faixa clara à esquerda é o top${FORMATO.top_n}. Passe o mouse numa linha para ver a contagem por posição.`,
  ]);

  container.replaceChildren(el("div", { class: "pilotos-scroll" }, [svg]), tooltip, legenda);
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

function renderListaAnosHall(hof, seasons) {
  const medalhas = { ouro: "🥇", prata: "🥈", bronze: "🥉" };
  const anos = hof.anos.slice().sort((a, b) => b.ano - a.ano);
  const disponiveis = new Set((seasons?.temporadas || []).map((t) => String(t.ano)));
  const atual = String(seasons?.atual ?? "");
  const lista = el("ul", { class: "hall-anos-lista" });
  for (const ano of anos) {
    const jaAtiva = String(ano.ano) === atual || String(ano.ano) === String(TEMPORADA);
    const acessar =
      disponiveis.has(String(ano.ano)) && !jaAtiva
        ? el("a", { class: "hall-acessar", href: `?ano=${ano.ano}` }, ["Acessar"])
        : String(ano.ano) === String(TEMPORADA)
        ? el("span", { class: "hall-acessar hall-acessar--ativa" }, ["Você está aqui"])
        : null;
    lista.appendChild(
      el("li", { class: "hall-ano-item" }, [
        el("span", { class: "hall-ano-item__ano" }, [String(ano.ano)]),
        el("span", { class: "hall-ano-item__medalha" }, [`${medalhas.ouro} ${nomeHall(hof, ano.ouro)}`]),
        el("span", { class: "hall-ano-item__medalha" }, [`${medalhas.prata} ${nomeHall(hof, ano.prata)}`]),
        el("span", { class: "hall-ano-item__medalha" }, [`${medalhas.bronze} ${nomeHall(hof, ano.bronze)}`]),
        acessar,
      ])
    );
  }
  return lista;
}

function renderHallOfFame(hof, seasons) {
  const container = document.getElementById("hall-container");
  container.replaceChildren(
    el("div", { class: "hall-grid" }, [
      el("div", { class: "hall-coluna" }, [el("h2", {}, ["Ranking de vitórias"]), renderRankingHall(hof)]),
      el("div", { class: "hall-coluna" }, [el("h2", {}, ["Pódios por ano"]), renderListaAnosHall(hof, seasons)]),
    ])
  );
}

// ---------- Abas ----------

// Chart.js não recupera bem de ser inicializado num canvas ainda escondido
// (0x0) — resize() sozinho não corrige. Por isso os gráficos da Temporada só
// são criados na primeira vez que a sub-aba Corridas fica visível (garantirGraficosTemporada).
function garantirGraficosTemporada() {
  if (!standingsParaTemporada) return;
  if (graficoTemporadaAcumulado && graficoTemporadaPorRodada) {
    graficoTemporadaAcumulado.resize();
    graficoTemporadaPorRodada.resize();
  } else {
    renderTemporada(standingsParaTemporada);
  }
}

// Mesmo problema de layout do Chart.js descrito acima: o gráfico de rendimento
// só é criado quando a sub-aba Rendimento fica de fato visível.
function garantirGraficoRendimento() {
  if (rendimentoModo === "piloto" && rendimentoEstado && rendimentoEstado.linhas.length) {
    if (graficoRendimento) graficoRendimento.resize();
    else renderGraficoRendimento(rendimentoEstado.linhas, rendimentoEstado.ids, rendimentoEstado.bets);
  }
  if (rendimentoModo === "jogador" && rendimentoPorJogadorEstado && rendimentoPorJogadorEstado.linhas.length) {
    if (graficoRendimentoPorJogador) graficoRendimentoPorJogador.resize();
    else
      renderGraficoRendimentoPorJogador(
        rendimentoPorJogadorEstado.linhas,
        rendimentoPorJogadorEstado.codigos,
        rendimentoPorJogadorEstado.bets
      );
  }
}

function configurarAbas() {
  const botoes = document.querySelectorAll("button.aba");
  const secoes = {
    ranking: document.getElementById("secao-ranking"),
    palpites: document.getElementById("secao-palpites"),
    pilotos: document.getElementById("secao-pilotos"),
    hall: document.getElementById("secao-hall"),
  };
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      botoes.forEach((b) => b.setAttribute("aria-selected", "false"));
      botao.setAttribute("aria-selected", "true");
      for (const [nome, secao] of Object.entries(secoes)) {
        secao.hidden = nome !== botao.dataset.aba;
      }
      const subabaRanking = document.querySelector("#secao-ranking button.subaba[aria-selected=\"true\"]");
      if (botao.dataset.aba === "ranking" && subabaRanking && subabaRanking.dataset.subaba === "corridas") {
        garantirGraficosTemporada();
      }
      const subabaPalpites = document.querySelector("#secao-palpites button.subaba[aria-selected=\"true\"]");
      if (botao.dataset.aba === "palpites" && subabaPalpites && subabaPalpites.dataset.subaba === "rendimento") {
        garantirGraficoRendimento();
      }
    });
  });
}

function configurarSubAbas() {
  const botoes = document.querySelectorAll("#secao-palpites button.subaba");
  const secoes = {
    historico: document.getElementById("subsecao-historico"),
    preferencia: document.getElementById("subsecao-preferencia"),
    rendimento: document.getElementById("subsecao-rendimento"),
  };
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      botoes.forEach((b) => b.setAttribute("aria-selected", "false"));
      botao.setAttribute("aria-selected", "true");
      for (const [nome, secao] of Object.entries(secoes)) {
        secao.hidden = nome !== botao.dataset.subaba;
      }
      if (botao.dataset.subaba === "rendimento") {
        garantirGraficoRendimento();
      }
    });
  });
}

function configurarSubAbasRanking() {
  const botoes = document.querySelectorAll("#secao-ranking button.subaba");
  const secoes = {
    geral: document.getElementById("subsecao-ranking-geral"),
    corridas: document.getElementById("subsecao-ranking-corridas"),
    simulador: document.getElementById("subsecao-ranking-simulador"),
    regras: document.getElementById("subsecao-ranking-regras"),
  };
  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      botoes.forEach((b) => b.setAttribute("aria-selected", "false"));
      botao.setAttribute("aria-selected", "true");
      for (const [nome, secao] of Object.entries(secoes)) {
        secao.hidden = nome !== botao.dataset.subaba;
      }
      if (botao.dataset.subaba === "corridas") {
        garantirGraficosTemporada();
      }
    });
  });
}

// ---------- Tema claro/escuro ----------

// Guardadas para re-renderizar os gráficos (canvas/SVG leem a cor do tema na
// hora do desenho — CSS puro se atualiza sozinho, Chart.js e o SVG não).
let resultsGlobais = null;

function temaEfetivo() {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "dark" || attr === "light") return attr;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function sincronizarSwitchTema() {
  const efetivo = temaEfetivo();
  document.querySelectorAll("#tema-switch .tema-switch__btn").forEach((botao) => {
    const ativo = botao.dataset.tema === efetivo;
    botao.classList.toggle("tema-switch__btn--ativo", ativo);
    botao.setAttribute("aria-pressed", ativo ? "true" : "false");
  });
}

// Redesenha o que não reage sozinho à troca de tema.
function rerenderizarGraficos() {
  if (resultsGlobais) renderPilotos(resultsGlobais);

  const rankingVisivel = !document.getElementById("secao-ranking").hidden;
  const corridasVisivel =
    rankingVisivel && !document.getElementById("subsecao-ranking-corridas").hidden;

  // Chart.js: destrói tudo; recria já o que está visível, o resto volta pela
  // inicialização preguiçosa das abas (garantir*), agora com a cor nova.
  [
    graficoTemporadaAcumulado,
    graficoTemporadaPorRodada,
    graficoRendimento,
    graficoRendimentoPorJogador,
  ].forEach((c) => c && c.destroy());
  graficoTemporadaAcumulado = null;
  graficoTemporadaPorRodada = null;
  graficoRendimento = null;
  graficoRendimentoPorJogador = null;
  dadosTemporada = null;

  if (corridasVisivel && standingsParaTemporada) renderTemporada(standingsParaTemporada);
  if (rendimentoEstado) renderRendimento(rendimentoEstado.ids, rendimentoEstado.bets);
  if (rendimentoPorJogadorEstado) {
    renderRendimentoPorJogador(rendimentoPorJogadorEstado.codigos, rendimentoPorJogadorEstado.bets);
  }
}

function aplicarTema(tema) {
  document.documentElement.setAttribute("data-theme", tema);
  try {
    localStorage.setItem("tema", tema);
  } catch (e) {
    /* modo privado / storage bloqueado — segue sem persistir */
  }
  sincronizarSwitchTema();
  rerenderizarGraficos();
}

function configurarTema() {
  sincronizarSwitchTema();
  document.querySelectorAll("#tema-switch .tema-switch__btn").forEach((botao) => {
    botao.addEventListener("click", () => aplicarTema(botao.dataset.tema));
  });
  // Sem escolha explícita, acompanha a mudança de tema do sistema.
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (!document.documentElement.getAttribute("data-theme")) {
      sincronizarSwitchTema();
      rerenderizarGraficos();
    }
  });
}

// Regras de pontuação (bloco em Ranking/Geral) montadas a partir de FORMATO —
// o texto muda por temporada (top5 vs top6, com/sem piloto da rodada, etc.).
function renderRegras() {
  const ul = document.getElementById("regras-lista");
  if (!ul) return;
  const n = FORMATO.top_n;
  const bp = FORMATO.bonus_points;
  const itens = [
    el("li", {}, [
      el("strong", {}, [`Top${n}`]),
      ` (máx. ${n * 2} pts): cada piloto apostado vale 2 pts na posição exata, ` +
        `1 pt se estiver no top${n} real em outra posição, 0 pt se estiver fora do top${n} real.`,
    ]),
  ];
  if (FORMATO.bonus) {
    itens.push(
      el("li", {}, [
        el("strong", {}, ["Piloto da rodada"]),
        ` (máx. ${bp} pt${bp > 1 ? "s" : ""}): ${bp} pt${bp > 1 ? "s" : ""} por acertar a ` +
          `posição exata dele no grid inteiro; 0 pt caso contrário.`,
      ]),
      el("li", {}, [
        el("strong", {}, ["Total por corrida:"]),
        ` máximo ${FORMATO.max_points} pts (${n * 2} do top${n} + ${bp} do piloto da rodada).`,
      ])
    );
  } else {
    itens.push(
      el("li", {}, [el("strong", {}, ["Total por corrida:"]), ` máximo ${FORMATO.max_points} pts.`])
    );
  }
  if (FORMATO.compensation) {
    itens.push(
      el("li", {}, [
        el("strong", {}, ["Pontuação mínima:"]),
        " quem não aposta numa rodada recebe a pontuação mínima daquela rodada " +
          "(1 a menos que a menor pontuação de quem apostou nela).",
      ])
    );
  }
  ul.replaceChildren(...itens);
}

// Ajusta os textos estáticos das legendas quando a temporada não é top6/2026.
function adaptarTextosEstaticos() {
  const n = FORMATO.top_n;
  const seletores = [
    ".hist-legenda",
    "#subsecao-preferencia .secao-intro",
    "#subsecao-preferencia .legenda-bloco",
    "#subsecao-rendimento .secao-intro",
  ];
  if (n !== 6 || TEMPORADA !== "2026") {
    for (const sel of seletores) {
      document.querySelectorAll(sel).forEach((elm) => {
        elm.innerHTML = elm.innerHTML
          .replace(/top6/g, `top${n}`)
          .replace(/P1[–-]P6/g, `P1–P${n}`)
          .replace(/qualis de 2026/g, `qualis de ${TEMPORADA}`);
      });
    }
  }
  const legBonus = document.getElementById("hist-legenda-bonus");
  if (legBonus) legBonus.hidden = !FORMATO.bonus;
  const rendBonus = document.getElementById("rendimento-intro-bonus");
  if (rendBonus) rendBonus.hidden = !FORMATO.bonus;
}

// Sub-aba "Regras" (só temporadas passadas): formato da temporada + esquema
// visual da regra 2/1/0 + decisões de cálculo (docs/data/regras.json).
function blocoRegra(titulo, ...filhos) {
  return el("section", { class: "regras-bloco" }, [el("h3", {}, [titulo]), ...filhos]);
}

function linhaEsquema(chip, texto, badge) {
  return el("div", { class: "regras-esquema__linha" }, [
    chip,
    el("span", { class: "regras-esquema__texto" }, [texto]),
    badge,
  ]);
}

function esquemaPontuacao() {
  const n = FORMATO.top_n;
  const linhas = [
    el("p", { class: "regras-esquema__intro" }, [
      "Exemplo: você apostou ",
      chipPiloto("HAM"),
      ` na posição P2 do seu top${n}.`,
    ]),
    linhaEsquema(chipPiloto("HAM"), "largou em P2 no quali → posição exata", badgePonto(2)),
    linhaEsquema(
      chipPiloto("HAM"),
      `largou em P5 → outra posição, mas dentro do top${n} real do quali`,
      badgePonto(1)
    ),
    linhaEsquema(chipPiloto("HAM"), `largou em P11 → fora do top${n} real`, badgePonto(0)),
  ];
  if (FORMATO.bonus) {
    linhas.push(
      el("p", { class: "regras-esquema__intro" }, [
        "Piloto da rodada (sorteado do grupo): ",
        chipPiloto("LEC"),
        ". Todos chutam a posição exata dele no grid inteiro. Você chutou P3.",
      ]),
      linhaEsquema(
        chipPiloto("LEC"),
        "largou exatamente em P3 → acerto",
        badgePonto(FORMATO.bonus_points, FORMATO.bonus_points)
      ),
      linhaEsquema(chipPiloto("LEC"), "largou em qualquer outra posição", badgePonto(0))
    );
  }
  return el("div", { class: "regras-esquema" }, linhas);
}

function renderRegrasHistorico(standings, entrada, regrasData) {
  const alvo = document.getElementById("regras-conteudo");
  if (!alvo) return;
  const n = FORMATO.top_n;
  const bp = FORMATO.bonus_points;
  const partes = [el("h2", {}, [`Regras da temporada ${TEMPORADA}`])];

  partes.push(
    blocoRegra(
      "Formato",
      el("ul", {}, [
        el("li", {}, [`Cada jogador aposta um top${n} (P1 a P${n}) em ordem.`]),
        FORMATO.bonus
          ? el("li", {}, [
              `Além do top${n}, um piloto sorteado pelo grupo é o "piloto da rodada": ` +
                `todos chutam a posição exata dele no grid inteiro, valendo ${bp} pt` +
                `${bp > 1 ? "s" : ""} no acerto.`,
            ])
          : el("li", {}, ["Não havia o palpite do piloto da rodada nesta temporada."]),
        el("li", {}, [`Máximo por corrida: ${FORMATO.max_points} pts.`]),
      ]),
      esquemaPontuacao()
    )
  );

  partes.push(
    blocoRegra(
      "Rodada sem palpite",
      FORMATO.compensation
        ? el("p", {}, [
            "Quem não aposta numa rodada recebe a pontuação mínima daquela rodada " +
              "(1 a menos que a menor pontuação de quem apostou nela). Esse valor entra " +
              "no total do ranking, mas não conta como rodada apostada — por isso a " +
              "média por corrida não considera essas rodadas.",
          ])
        : el("p", {}, [
            "Não havia pontuação mínima nesta temporada: quem faltava uma rodada " +
              "simplesmente não pontuava nela.",
          ])
    )
  );

  partes.push(
    blocoRegra(
      "Desempate",
      FORMATO.tiebreak === "media" || TEMPORADA === "2021"
        ? el("p", {}, [
            "Por média de pontos por rodada — foi assim que o grupo separou Ferrari e " +
              "Vinícius, os dois com 96 pts em 2021.",
          ])
        : el("p", {}, [
            "A ordem final segue a classificação que o grupo publicou no WhatsApp no " +
              "fim da temporada (o critério de desempate do grupo nunca foi escrito).",
          ])
    )
  );

  const temDivergencia = standings.players.some((j) => j.total_calculado !== j.total);
  partes.push(
    blocoRegra(
      "Oficial × Calculada",
      el("p", {}, [
        el("strong", {}, ["Oficial"]),
        " é o placar que o grupo publicou — o registro da temporada. ",
        el("strong", {}, ["Calculada"]),
        " é o recálculo por estas regras. ",
        temDivergencia
          ? "Nesta temporada os dois divergem; a coluna “Calculada” no ranking mostra a " +
            "diferença entre parênteses. As divergências vêm de contas do grupo na época " +
            "(placar publicado às pressas, somas que não fecham) e não de mudança de regra."
          : "Nesta temporada o recálculo bate 100% com o placar do grupo.",
      ])
    )
  );

  if (entrada && (entrada.faltando || []).length) {
    partes.push(
      blocoRegra(
        "Cobertura",
        el("p", {}, ["O que falta nos dados desta temporada:"]),
        el(
          "ul",
          {},
          entrada.faltando.map((f) => el("li", {}, [f]))
        )
      )
    );
  }

  const notas = (regrasData && regrasData.por_ano && regrasData.por_ano[TEMPORADA]) || [];
  if (notas.length) {
    partes.push(
      blocoRegra(
        "Decisões desta temporada",
        el(
          "ul",
          {},
          notas.map((t) => el("li", {}, [t]))
        )
      )
    );
  }

  const comuns = (regrasData && regrasData.comum) || [];
  if (comuns.length) {
    partes.push(
      blocoRegra(
        "Regras gerais (todos os anos)",
        el(
          "ul",
          {},
          comuns.map((t) => el("li", {}, [t]))
        )
      )
    );
  }

  alvo.replaceChildren(...partes);
}

// Título / badge / botão voltar / faixa de avisos + esconde o Simulador.
function aplicarModoHistorico() {
  const titulo = document.getElementById("topo-titulo");
  const badge = document.getElementById("hist-badge");
  if (titulo && titulo.firstChild) titulo.firstChild.textContent = `🏁 Bolão F1 ${TEMPORADA} `;
  document.title = `Bolão F1 ${TEMPORADA}`;
  if (badge) badge.hidden = !MODO_HISTORICO;

  const atual = String(SEASONS?.atual ?? "2026");
  const voltar = document.getElementById("btn-voltar-atual");
  if (voltar) {
    voltar.hidden = !MODO_HISTORICO;
    voltar.textContent = `← Voltar para ${atual}`;
    voltar.addEventListener("click", () => {
      location.href = location.pathname;
    });
  }

  const avisos = document.getElementById("hist-avisos");
  const entrada = entradaTemporada();
  if (avisos && MODO_HISTORICO && entrada && entrada.parcial && (entrada.faltando || []).length) {
    avisos.replaceChildren(
      el("strong", {}, ["Temporada com dados incompletos:"]),
      el(
        "ul",
        {},
        entrada.faltando.map((f) => el("li", {}, [f]))
      )
    );
    avisos.hidden = false;
  } else if (avisos) {
    avisos.hidden = true;
  }

  if (MODO_HISTORICO) {
    const btnSim = document.querySelector('#secao-ranking button.subaba[data-subaba="simulador"]');
    const secSim = document.getElementById("subsecao-ranking-simulador");
    if (btnSim) btnSim.hidden = true;
    if (secSim) secSim.hidden = true;
    if (btnSim && btnSim.getAttribute("aria-selected") === "true") {
      const geral = document.querySelector('#secao-ranking button.subaba[data-subaba="geral"]');
      if (geral) geral.click();
    }

    // Sub-aba "Regras" (só nas temporadas passadas). O bloco resumido de regras
    // que fica na sub-aba Geral vira redundante — some.
    const btnRegras = document.querySelector('#secao-ranking button.subaba[data-subaba="regras"]');
    if (btnRegras) btnRegras.hidden = false;
    const regrasGeral = document.querySelector("#subsecao-ranking-geral .regras-pontuacao");
    if (regrasGeral) regrasGeral.hidden = true;

    // Temporada finalizada: a leitura corrida-a-corrida ("Pontuação da corrida")
    // dá lugar à matriz de todas as corridas, que sai de Palpites/Histórico para
    // Ranking/Geral. A sub-aba Histórico deixa de existir (Preferência vira o
    // padrão de Palpites).
    const historico = document.getElementById("subsecao-historico");
    const geralSec = document.getElementById("subsecao-ranking-geral");
    const detalheCard = document.querySelector("#subsecao-ranking-geral .corrida-detalhe-card");
    const regras = geralSec && geralSec.querySelector(".regras-pontuacao");
    if (historico && geralSec && detalheCard && regras) {
      detalheCard.hidden = true;
      if (!document.getElementById("hist-matriz-titulo")) {
        geralSec.insertBefore(
          el("h2", { id: "hist-matriz-titulo" }, ["Palpites por corrida"]),
          regras
        );
      }
      geralSec.insertBefore(historico, regras);
      historico.hidden = false;
    }
    const btnHist = document.querySelector('#secao-palpites button.subaba[data-subaba="historico"]');
    const btnPref = document.querySelector('#secao-palpites button.subaba[data-subaba="preferencia"]');
    const secPref = document.getElementById("subsecao-preferencia");
    if (btnHist) btnHist.hidden = true;
    if (btnHist && btnHist.getAttribute("aria-selected") === "true" && btnPref && secPref) {
      btnPref.setAttribute("aria-selected", "true");
      secPref.hidden = false;
    }
  }
}

async function main() {
  configurarTema();
  configurarAbas();
  configurarSubAbas();
  configurarSubAbasRanking();
  configurarModoAcumulado();

  try {
    SEASONS = await carregarJson("./data/seasons.json");
    const atual = String(SEASONS.atual);
    const anos = SEASONS.temporadas.map((t) => String(t.ano));
    const pedido = anoPedido();
    if (pedido && pedido !== atual && !anos.includes(pedido)) {
      location.replace(location.pathname);
      return;
    }
    if (pedido && pedido !== atual && anos.includes(pedido)) {
      TEMPORADA = pedido;
      MODO_HISTORICO = true;
    } else {
      TEMPORADA = atual;
    }

    const standings = await carregarJson(caminhoDados("standings"));
    FORMATO = standings.format || FORMATO;
    aplicarModoHistorico();
    renderRegras();
    adaptarTextosEstaticos();
    renderRanking(standings);
    document.getElementById("ranking-status").textContent = "";
    standingsParaTemporada = standings;

    if (MODO_HISTORICO) {
      const regrasData = await carregarJson("./data/regras.json").catch(() => null);
      renderRegrasHistorico(standings, entradaTemporada(), regrasData);
    }

    document.getElementById("btn-copiar-ranking").addEventListener("click", (evento) => {
      copiarTexto(gerarTextoRanking(standings), evento.currentTarget);
    });

    const calendar = await carregarJson(caminhoDados("calendar"));
    calendarGlobal = calendar;
    renderCorridas(standings, calendar);
    renderTabelaCorridas(standings);
    if (!MODO_HISTORICO) renderSimulador(standings, calendar);

    const results = await carregarJson(caminhoDados("results"));
    const bets = await carregarJson(caminhoDados("bets"));
    resultsGlobais = results;

    renderPilotos(results);
    document.getElementById("pilotos-status").textContent = "";

    const roundsDetalhe = popularSelectCorridaDetalhe(standings);
    const selectCorridaDetalhe = document.getElementById("select-corrida-detalhe");
    selectCorridaDetalhe.addEventListener("change", () => {
      renderCorridaDetalhe(Number(selectCorridaDetalhe.value), standings, bets, results);
    });
    if (roundsDetalhe.length) {
      const ultimaRodada = roundsDetalhe[roundsDetalhe.length - 1];
      selectCorridaDetalhe.value = String(ultimaRodada.round);
      renderCorridaDetalhe(ultimaRodada.round, standings, bets, results);
    }

    document.getElementById("btn-copiar-corrida").addEventListener("click", (evento) => {
      copiarTexto(gerarTextoCorrida(Number(selectCorridaDetalhe.value), standings), evento.currentTarget);
    });

    histBets = bets;
    histStandings = standings;
    const jogadoresHist = popularHistJogadores(bets, standings);
    document.getElementById("palpites-status").textContent = "";

    if (jogadoresHist.length) {
      histSelecionados = [jogadoresHist[0].player_id];
      sincronizarHistChips();
      renderHistMatriz();
      renderHistPorCorrida();
    }

    popularSelectComTodos("select-preferencia-jogador", bets);
    const selectPreferencia = document.getElementById("select-preferencia-jogador");
    selectPreferencia.addEventListener("change", () => {
      renderPreferenciaPiloto(selectPreferencia.value, bets, results);
    });
    renderPreferenciaPiloto("todos", bets, results);

    rendimentoBets = bets;
    rendimentoJogadores = ordemJogadores(bets);
    rendimentoPilotos = [...coletarRendimento(bets, "todos").keys()].sort((a, b) => a.localeCompare(b));
    rendimentoSelJogadores = new Set(rendimentoJogadores.map((j) => j.player_id));
    rendimentoSelPilotos = new Set(rendimentoPilotos);
    popularRendimentoChips();
    configurarRendimento();
    atualizarRendimento();

    const hof = await carregarJson("./data/hall_of_fame.json");
    renderHallOfFame(hof, SEASONS);
    document.getElementById("hall-status").textContent = "";
  } catch (erro) {
    console.error(erro);
    document.getElementById("ranking-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("ranking-status").classList.add("erro");
    document.getElementById("palpites-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("palpites-status").classList.add("erro");
    document.getElementById("hall-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("hall-status").classList.add("erro");
    document.getElementById("pilotos-status").textContent = "Erro ao carregar os dados do bolão.";
    document.getElementById("pilotos-status").classList.add("erro");
  }
}

main();
