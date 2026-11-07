// Worker bolao-vigia (vigia/src/index.js) rodando no Node, sem Cloudflare: fetch de mentira
// que responde pendentes.json, Jolpica e o workflow_dispatch do GitHub, e registra as chamadas.
// Cobre a janela do quali (cedo/consultar), o disparo quando o resultado sai, o alerta de 6 h
// (uma vez só, sem estado), entradas inválidas e falhas de rede/HTTP.
import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const vigia = await import(pathToFileURL(path.join(raiz, "vigia", "src", "index.js")).href);

const QUALI = "2026-11-07T18:00:00Z";
const T_QUALI = Date.parse(QUALI);
const MIN = 60 * 1000;

const comQuali = { MRData: { RaceTable: { Races: [{ QualifyingResults: [{ position: "1", Driver: { code: "ANT" } }] }] } } };
const semQuali = { MRData: { RaceTable: { Races: [] } } };

/** fetch de mentira: rotas por prefixo de URL; guarda cada chamada em `chamadas`. */
function criarFetch({ pendentes, jolpica = semQuali, github = { status: 204 }, falhar = {} }) {
  const chamadas = [];
  const fetchFn = async (url, opcoes = {}) => {
    chamadas.push({ url, opcoes });
    const resposta = (status, corpo) => ({
      ok: status >= 200 && status < 300,
      status,
      json: async () => corpo,
      text: async () => JSON.stringify(corpo ?? ""),
    });
    if (url.startsWith(vigia.PENDENTES_URL)) {
      if (falhar.pendentes) return resposta(falhar.pendentes, null);
      return resposta(200, pendentes);
    }
    if (url.startsWith(vigia.JOLPICA)) {
      if (falhar.jolpica === "rede") throw new Error("sem rede");
      if (falhar.jolpica) return resposta(falhar.jolpica, null);
      return resposta(200, jolpica);
    }
    if (url === vigia.WORKFLOW_DISPATCH) return resposta(github.status, { message: "x" });
    throw new Error(`URL inesperada: ${url}`);
  };
  return { fetchFn, chamadas };
}

const doc = (pendentes) => ({ temporada: 2026, pendentes });
const ENV = { GITHUB_TOKEN_DISPARO: "token-de-teste" };

test("sem rodada pendente: não consulta a Jolpica", async () => {
  const { fetchFn, chamadas } = criarFetch({ pendentes: doc([]) });
  const log = await vigia.verificar(ENV, new Date(T_QUALI), fetchFn);
  assert.deepEqual(log, ["nenhuma rodada pendente"]);
  assert.equal(chamadas.length, 1);
  assert.match(chamadas[0].url, /pendentes\.json\?t=\d+$/);
});

test("antes de 45 min do quali: cedo, sem consultar a Jolpica", async () => {
  const { fetchFn, chamadas } = criarFetch({ pendentes: doc([{ round: 20, qualifying_utc: QUALI }]) });
  const log = await vigia.verificar(ENV, new Date(T_QUALI + 30 * MIN), fetchFn);
  assert.deepEqual(log, ["rodada 20: quali ainda não aconteceu"]);
  assert.equal(chamadas.length, 1);
});

test("quali sem resultado ainda: espera, sem disparar", async () => {
  const { fetchFn, chamadas } = criarFetch({ pendentes: doc([{ round: 20, qualifying_utc: QUALI }]) });
  const log = await vigia.verificar(ENV, new Date(T_QUALI + 60 * MIN), fetchFn);
  assert.deepEqual(log, ["rodada 20: quali ainda sem resultado na Jolpica"]);
  assert.match(chamadas[1].url, /\/2026\/20\/qualifying\.json/);
  assert.ok(!chamadas.some((c) => c.url === vigia.WORKFLOW_DISPATCH));
});

test("resultado saiu: dispara o pipeline.yml com round e token", async () => {
  const { fetchFn, chamadas } = criarFetch({ pendentes: doc([{ round: 20, qualifying_utc: QUALI }]), jolpica: comQuali });
  const log = await vigia.verificar(ENV, new Date(T_QUALI + 70 * MIN), fetchFn);
  assert.deepEqual(log, ["rodada 20: resultado saiu — disparo ok"]);
  const disparo = chamadas.find((c) => c.url === vigia.WORKFLOW_DISPATCH);
  assert.equal(disparo.opcoes.method, "POST");
  assert.equal(disparo.opcoes.headers.authorization, "Bearer token-de-teste");
  assert.deepEqual(JSON.parse(disparo.opcoes.body), { ref: "main", inputs: { round: "20" } });
});

test("alerta de 6 h: dispara uma vez só (janela de um Cron)", () => {
  const p = { round: 20, qualifying_utc: QUALI };
  const limite = T_QUALI + vigia.ALERTA_APOS_MS;
  assert.equal(vigia.depoisDaConsulta(p, new Date(limite - MIN), false), "esperar");
  assert.equal(vigia.depoisDaConsulta(p, new Date(limite), false), "alertar");
  assert.equal(vigia.depoisDaConsulta(p, new Date(limite + vigia.INTERVALO_CRON_MS - 1), false), "alertar");
  assert.equal(vigia.depoisDaConsulta(p, new Date(limite + vigia.INTERVALO_CRON_MS), false), "esperar");
  assert.equal(vigia.depoisDaConsulta(p, new Date(limite), true), "disparar");
});

test("sem horário do quali: consulta sempre e nunca alerta", () => {
  assert.equal(vigia.antesDaConsulta({ round: 3 }, new Date(0)), "consultar");
  assert.equal(vigia.depoisDaConsulta({ round: 3 }, new Date(), false), "esperar");
});

test("qualiDisponivel: só com posição e piloto", () => {
  assert.equal(vigia.qualiDisponivel(comQuali), true);
  assert.equal(vigia.qualiDisponivel(semQuali), false);
  assert.equal(vigia.qualiDisponivel({ MRData: { RaceTable: { Races: [{ QualifyingResults: [{ position: "1" }] }] } } }), false);
  assert.equal(vigia.qualiDisponivel(null), false);
});

test("sem token: não chama o GitHub", async () => {
  const { fetchFn, chamadas } = criarFetch({ pendentes: doc([{ round: 20, qualifying_utc: QUALI }]), jolpica: comQuali });
  const log = await vigia.verificar({}, new Date(T_QUALI + 70 * MIN), fetchFn);
  assert.deepEqual(log, ["rodada 20: resultado saiu — disparo sem GITHUB_TOKEN_DISPARO"]);
  assert.ok(!chamadas.some((c) => c.url === vigia.WORKFLOW_DISPATCH));
});

test("falhas: pendentes.json HTTP, Jolpica fora do ar, GitHub recusa, entrada inválida", async () => {
  let r = criarFetch({ pendentes: null, falhar: { pendentes: 404 } });
  assert.deepEqual(await vigia.verificar(ENV, new Date(), r.fetchFn), ["pendentes.json: HTTP 404"]);

  const pend = doc([{ round: 0 }, { round: 20, qualifying_utc: QUALI }]);
  r = criarFetch({ pendentes: pend, falhar: { jolpica: "rede" } });
  const log = await vigia.verificar(ENV, new Date(T_QUALI + 70 * MIN), r.fetchFn);
  assert.match(log[0], /entrada inválida/);
  assert.match(log[1], /rodada 20: Jolpica falhou/);

  r = criarFetch({ pendentes: doc([{ round: 20, qualifying_utc: QUALI }]), jolpica: comQuali, github: { status: 403 } });
  const [linha] = await vigia.verificar(ENV, new Date(T_QUALI + 70 * MIN), r.fetchFn);
  assert.match(linha, /disparo HTTP 403/);
});

test("usa PENDENTES_URL do env quando definido", async () => {
  const chamadas = [];
  const fetchFn = async (url) => {
    chamadas.push(url);
    return { ok: true, status: 200, json: async () => doc([]) };
  };
  await vigia.verificar({ PENDENTES_URL: "https://exemplo.test/p.json" }, new Date(5), fetchFn);
  assert.equal(chamadas[0], "https://exemplo.test/p.json?t=5");
});
