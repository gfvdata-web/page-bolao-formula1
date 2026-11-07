// Vigia do quali do Bolão F1 (Etapa 5, item (d) da trilha mínima do
// contexto/plano-futuro-cloudflare.md): substitui a vigília de até 5 h que dormia
// dentro da run do pipeline.yml, que num repositório privado gastaria minutos de Actions.
//
// A cada 5 min (Cron, wrangler.jsonc):
//   1. lê https://bolaof1.gfvdata.com/data/pendentes.json — rodadas com palpites gravados
//      e sem resultado, gerado pelo Python (bolao/site.py, gerar_pendentes);
//   2. para cada uma, a partir de pouco depois do horário do quali, consulta a Jolpica;
//   3. quando o quali sai, dispara o workflow_dispatch do pipeline.yml (round=N), que roda
//      o `pipeline retry`, pontua, commita e o Pages republica (a rodada sai da lista).
// Se o quali não sair em ALERTA_APOS_MS, dispara uma vez mesmo assim: a run termina
// vermelha (código 2 no retry manual) e o GitHub manda o e-mail, como a vigília fazia.
//
// Sem estado (sem D1/KV): o que está pendente é o arquivo publicado; um disparo repetido
// enquanto o Pages não republica só gera uma run curta que não muda nada.
// Segredo (wrangler secret put): GITHUB_TOKEN_DISPARO — fine-grained, só
// gfvdata-web/page-bolao-formula1, Actions: write.
//
// Código recuperado em 2026-11-07 do Worker publicado (source map da Cloudflare): a
// sessão de 2026-10-30 publicou o Worker mas não commitou esta pasta.

export const PENDENTES_URL = "https://bolaof1.gfvdata.com/data/pendentes.json";
export const JOLPICA = "https://api.jolpi.ca/ergast/f1";
export const WORKFLOW_DISPATCH =
  "https://api.github.com/repos/gfvdata-web/page-bolao-formula1/actions/workflows/pipeline.yml/dispatches";
const MINUTO = 60 * 1000;
/** Começa a consultar a Jolpica só depois do quali (que dura ~1 h) ter começado. */
export const INICIO_APOS_MS = 45 * MINUTO;
/** Sem resultado até aqui (contado do horário do quali) → alerta. */
export const ALERTA_APOS_MS = 6 * 60 * MINUTO;
/** Janela do alerta = intervalo do Cron, para disparar uma vez só sem guardar estado. */
export const INTERVALO_CRON_MS = 5 * MINUTO;
const USER_AGENT = "bolao-vigia (bolaof1.gfvdata.com)";

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(
      verificar(env, new Date(controller.scheduledTime), fetch).then((log) => {
        for (const linha of log) console.log(linha);
      }),
    );
  },
};

/**
 * O que fazer com uma rodada pendente agora: "cedo" (quali ainda não aconteceu),
 * "consultar" (perguntar à Jolpica) ou, depois da resposta, "disparar"/"alertar"/"esperar".
 */
export function antesDaConsulta(pendente, agora) {
  const quali = Date.parse(pendente.qualifying_utc ?? "");
  if (Number.isNaN(quali)) return "consultar"; // sem horário: consulta sempre
  return agora.getTime() < quali + INICIO_APOS_MS ? "cedo" : "consultar";
}

export function depoisDaConsulta(pendente, agora, disponivel) {
  if (disponivel) return "disparar";
  const quali = Date.parse(pendente.qualifying_utc ?? "");
  if (Number.isNaN(quali)) return "esperar";
  const limite = quali + ALERTA_APOS_MS;
  const t = agora.getTime();
  return t >= limite && t < limite + INTERVALO_CRON_MS ? "alertar" : "esperar";
}

/** Mesmo critério do bolao/jolpica.py (build_result): há posições no quali. */
export function qualiDisponivel(json) {
  const corrida = json?.MRData?.RaceTable?.Races?.[0];
  const linhas = corrida?.QualifyingResults ?? [];
  return linhas.some((r) => r?.position && (r?.Driver?.code || r?.Driver?.familyName));
}

export async function verificar(env, agora, fetchFn) {
  const log = [];
  let doc;
  try {
    const url = `${env.PENDENTES_URL || PENDENTES_URL}?t=${agora.getTime()}`;
    const r = await fetchFn(url, { cf: { cacheTtl: 0 }, headers: { "user-agent": USER_AGENT } });
    if (!r.ok) return [`pendentes.json: HTTP ${r.status}`];
    doc = await r.json();
  } catch (falha) {
    return [`pendentes.json ilegível: ${falha}`];
  }
  const pendentes = Array.isArray(doc?.pendentes) ? doc.pendentes : [];
  if (!pendentes.length) return ["nenhuma rodada pendente"];

  for (const p of pendentes) {
    if (!Number.isInteger(p?.round) || p.round < 1) {
      log.push(`entrada inválida em pendentes.json: ${JSON.stringify(p)}`);
      continue;
    }
    if (antesDaConsulta(p, agora) === "cedo") {
      log.push(`rodada ${p.round}: quali ainda não aconteceu`);
      continue;
    }
    let disponivel = false;
    try {
      const r = await fetchFn(`${JOLPICA}/${doc.temporada}/${p.round}/qualifying.json?limit=100`, {
        headers: { "user-agent": USER_AGENT },
      });
      if (!r.ok) {
        log.push(`rodada ${p.round}: Jolpica HTTP ${r.status}`);
        continue;
      }
      disponivel = qualiDisponivel(await r.json());
    } catch (falha) {
      log.push(`rodada ${p.round}: Jolpica falhou: ${falha}`);
      continue;
    }
    const acao = depoisDaConsulta(p, agora, disponivel);
    if (acao === "esperar") {
      log.push(`rodada ${p.round}: quali ainda sem resultado na Jolpica`);
      continue;
    }
    const res = await disparar(env, p.round, fetchFn);
    log.push(`rodada ${p.round}: ${acao === "disparar" ? "resultado saiu" : "ALERTA: sem resultado há 6 h"} — disparo ${res}`);
  }
  return log;
}

export async function disparar(env, round, fetchFn) {
  if (!env.GITHUB_TOKEN_DISPARO) return "sem GITHUB_TOKEN_DISPARO";
  try {
    const resposta = await fetchFn(WORKFLOW_DISPATCH, {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.GITHUB_TOKEN_DISPARO}`,
        accept: "application/vnd.github+json",
        "x-github-api-version": "2022-11-28",
        "user-agent": USER_AGENT,
      },
      body: JSON.stringify({ ref: "main", inputs: { round: String(round) } }),
    });
    if (resposta.ok) return "ok";
    return `HTTP ${resposta.status}: ${(await resposta.text()).slice(0, 200)}`;
  } catch (falha) {
    return `falha de rede: ${falha}`;
  }
}
