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

async function renderPaginaPilotos() {
  entrarModoPagina("secao-pilotos-analise", "🏎️", "Pilotos", "?menu", "Menu");
  document.getElementById("pilotos-analise-status").textContent = "Em construção.";
}
