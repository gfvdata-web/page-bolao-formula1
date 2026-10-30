// App Android do Bolão F1 na Cloudflare: o APK e o aviso de versão (Etapa 9, trilha mínima).
//
// O repositório vai ficar privado, e Release de repositório privado não baixa sem login: o
// APK sai do GitHub Releases e passa a morar aqui. O site continua no Cloudflare Pages; este
// Worker roda como route só em bolaof1.gfvdata.com/app/* e /api/app/* (wrangler.jsonc).
// Modelo: worker/src/index.ts do painel-status (mesmas rotas e validações).
//
// O job "publicar" do android.yml manda o APK assinado e depois o versao.json, com o mesmo token:
//
//   GET /app/versao.json                 D1 arquivos["app/versao.json"] — o aviso de versão do app
//   GET /app/bolao-f1-vX.Y.Z-buildN.apk  KV APKS[<nome>] (ficam só os APKS_GUARDADOS mais novos)
//   PUT /api/app/<nome do apk>           grava o APK (Authorization: Bearer TOKEN_ENVIO)
//   PUT /api/app/versao.json             só aceita se o APK citado já estiver no KV
//
// Custo: só D1, KV e Workers do plano grátis, que dão erro no limite diário em vez de
// cobrar (sem R2). Limite de valor do KV: 25 MiB por APK.

const PREFIXO_APP = "/app/";
const PREFIXO_ENVIO_APP = "/api/app/";
const VERSAO = "versao.json";
const CHAVE_VERSAO = `app/${VERSAO}`;
/** Mesmo padrão que o app lê (VerificadorDeAtualizacao) e o android.yml gera. */
const RE_APK = /^bolao-f1-v(\d+\.\d+\.\d+)-build(\d+)\.apk$/;
/** Limite de valor do KV. */
const LIMITE_APK = 25 * 1024 * 1024;
const TIPO_APK = "application/vnd.android.package-archive";
const APKS_GUARDADOS = 3;

// Secret (wrangler secret put TOKEN_ENVIO); fora do worker-configuration.d.ts, que só vê o wrangler.jsonc.
declare global {
  interface Env {
    TOKEN_ENVIO?: string;
  }
}

export default {
  async fetch(request, env): Promise<Response> {
    const { pathname } = new URL(request.url);
    if (pathname.startsWith(PREFIXO_APP)) {
      const nome = pathname.slice(PREFIXO_APP.length);
      if (!(nome === VERSAO || RE_APK.test(nome)) || !["GET", "HEAD"].includes(request.method)) {
        return erro(404, "não encontrado");
      }
      if (nome === VERSAO) {
        const arquivo = await lerArquivo(env, CHAVE_VERSAO);
        return arquivo ? servirArquivo(request, arquivo) : erro(404, "não encontrado");
      }
      return servirApk(request, env, nome);
    }
    if (pathname.startsWith(PREFIXO_ENVIO_APP)) {
      const nome = pathname.slice(PREFIXO_ENVIO_APP.length);
      if (!(nome === VERSAO || RE_APK.test(nome))) return erro(404, "caminho desconhecido");
      if (request.method !== "PUT") return erro(405, "use PUT");
      if (!(await autorizado(request, env))) return erro(401, "token inválido");
      return nome === VERSAO ? receberVersao(request, env) : receberApk(request, env, nome);
    }
    // Só chega aqui se a route do wrangler.jsonc mudar: o resto do domínio é do Pages.
    return erro(404, "não encontrado");
  },
} satisfies ExportedHandler<Env>;

// --- Armazenamento (D1) -------------------------------------------------------------

interface Arquivo {
  conteudo: string;
  etag: string;
}

function lerArquivo(env: Env, chave: string): Promise<Arquivo | null> {
  return env.BANCO.prepare("SELECT conteudo, etag FROM arquivos WHERE chave = ?").bind(chave).first<Arquivo>();
}

async function gravarArquivo(env: Env, chave: string, conteudo: string) {
  await env.BANCO.prepare(
    `INSERT INTO arquivos (chave, conteudo, etag, atualizado_em) VALUES (?, ?, ?, ?)
     ON CONFLICT (chave) DO UPDATE SET conteudo = excluded.conteudo, etag = excluded.etag,
       atualizado_em = excluded.atualizado_em`,
  )
    .bind(chave, conteudo, await sha256(conteudo), new Date().toISOString())
    .run();
}

async function sha256(texto: string): Promise<string> {
  const resumo = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return [...new Uint8Array(resumo)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// --- Leitura -------------------------------------------------------------------------

function servirArquivo(request: Request, arquivo: Arquivo): Response {
  const headers = new Headers({
    "content-type": "application/json; charset=utf-8",
    // Pode guardar, mas confere sempre (ETag): o aviso de versão precisa do mais novo.
    "cache-control": "no-cache",
    "access-control-allow-origin": "*",
  });
  const etag = `"${arquivo.etag}"`;
  headers.set("etag", etag);
  if (request.headers.get("if-none-match") === etag) return new Response(null, { status: 304, headers });
  return new Response(request.method === "HEAD" ? null : arquivo.conteudo, { headers });
}

async function servirApk(request: Request, env: Env, nome: string): Promise<Response> {
  const apk = await env.APKS.get(nome, "stream");
  if (apk === null) return erro(404, "não encontrado");
  const headers = new Headers({
    "content-type": TIPO_APK,
    "content-disposition": `attachment; filename="${nome}"`,
    // O nome traz versão e build: um arquivo nunca muda depois de publicado.
    "cache-control": "public, max-age=31536000, immutable",
  });
  if (request.method === "HEAD") {
    await apk.cancel();
    return new Response(null, { headers });
  }
  return new Response(apk, { headers });
}

// --- Envio ---------------------------------------------------------------------------

async function autorizado(request: Request, env: Env): Promise<boolean> {
  const recebido = request.headers.get("authorization") ?? "";
  if (!env.TOKEN_ENVIO) return false;
  return iguais(recebido, `Bearer ${env.TOKEN_ENVIO}`);
}

/** Compara os hashes em tempo constante (os dois têm o mesmo tamanho). */
async function iguais(x: string, y: string): Promise<boolean> {
  const codificar = (texto: string) => crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  const [a, b] = await Promise.all([codificar(x), codificar(y)]);
  return crypto.subtle.timingSafeEqual(a, b);
}

async function receberApk(request: Request, env: Env, nome: string): Promise<Response> {
  const corpo = await request.arrayBuffer();
  if (corpo.byteLength > LIMITE_APK) return erro(413, "APK grande demais");
  // Todo APK é um zip: começa com os bytes 50 4B 03 04 ("PK").
  const inicio = new Uint8Array(corpo.slice(0, 4));
  if (inicio.length < 4 || inicio[0] !== 0x50 || inicio[1] !== 0x4b || inicio[2] !== 0x03 || inicio[3] !== 0x04) {
    return erro(422, "não é um APK");
  }
  await env.APKS.put(nome, corpo);
  // Guarda só os mais novos (pelo build): o KV grátis tem 1 GB.
  const { keys } = await env.APKS.list();
  const antigos = keys
    .map((k) => ({ nome: k.name, build: Number(RE_APK.exec(k.name)?.[2] ?? -1) }))
    .sort((a, b) => b.build - a.build)
    .slice(APKS_GUARDADOS);
  await Promise.all(antigos.map((a) => env.APKS.delete(a.nome)));
  return Response.json({ ok: true, apk: nome, bytes: corpo.byteLength, apagados: antigos.map((a) => a.nome) });
}

interface Versao {
  versao: string;
  build: number;
  apk: string;
  notas: string;
  publicado_em: string;
}

/** versao.json: versao e build têm de bater com o nome do APK, e o APK já tem de estar no KV. */
async function receberVersao(request: Request, env: Env): Promise<Response> {
  const texto = await request.text();
  if (texto.length > 64 * 1024) return erro(413, "versao.json grande demais");
  let dados: Partial<Versao>;
  try {
    dados = JSON.parse(texto);
  } catch {
    return erro(400, "JSON inválido");
  }
  const nomeDoApk = typeof dados?.apk === "string" ? dados.apk : "";
  const achado = RE_APK.exec(nomeDoApk);
  if (!achado) return erro(422, "apk ausente ou fora do padrão");
  if (dados.versao !== achado[1] || dados.build !== Number(achado[2])) {
    return erro(422, "versao/build não batem com o nome do APK");
  }
  // Leitura direta (a listagem do KV pode demorar a mostrar uma chave recém-gravada).
  const apk = await env.APKS.get(nomeDoApk, "stream");
  if (apk === null) return erro(409, `o APK ${nomeDoApk} ainda não foi enviado`);
  await apk.cancel();
  await gravarArquivo(env, CHAVE_VERSAO, texto);
  return Response.json({ ok: true, chave: CHAVE_VERSAO, apk: nomeDoApk });
}

function erro(status: number, mensagem: string): Response {
  return Response.json({ ok: false, erro: mensagem }, { status });
}
