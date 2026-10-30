// Worker do app Android (worker/src/index.ts) rodando no Node, sem Cloudflare: o Node 24 lê o .ts
// direto (só apaga os tipos) e o ambiente do Worker é de mentira — D1 e KV em memória.
// Cobre as rotas /app/ e /api/app/, o token, o versao.json e a guarda dos APKs.
// O tsc (scripts/check) cobre os tipos. Modelo: tests/worker.test.mjs do painel-status.
import test from "node:test";
import assert from "node:assert/strict";
import nodeCrypto from "node:crypto";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

// Só o runtime do Workers tem crypto.subtle.timingSafeEqual; no Node usamos o equivalente.
if (!crypto.subtle.timingSafeEqual) {
  crypto.subtle.timingSafeEqual = (a, b) => nodeCrypto.timingSafeEqual(new Uint8Array(a), new Uint8Array(b));
}
const worker = await import(pathToFileURL(path.join(raiz, "worker", "src", "index.ts")).href);

const TOKEN = "segredo-de-teste";

/** D1 + KV em memória; só entende as consultas que o Worker faz (outra = falha o teste). */
function criarEnv({ token = TOKEN } = {}) {
  const arquivos = new Map(); // chave -> {conteudo, etag}
  const kv = new Map();
  const BANCO = {
    prepare(sql) {
      const s = sql.replace(/\s+/g, " ").trim();
      return {
        bind: (...args) => ({
          async first() {
            if (/^SELECT conteudo, etag FROM arquivos WHERE chave = \?/.test(s)) return arquivos.get(args[0]) ?? null;
            throw new Error(`consulta não prevista no teste: ${s}`);
          },
          async run() {
            if (!/^INSERT INTO arquivos/.test(s)) throw new Error(`escrita não prevista no teste: ${s}`);
            const [chave, conteudo, etag] = args;
            arquivos.set(chave, { conteudo, etag });
            return { success: true };
          },
        }),
      };
    },
  };
  const APKS = {
    async get(nome) {
      if (!kv.has(nome)) return null;
      return new Blob([kv.get(nome)]).stream(); // o KV devolve um ReadableStream
    },
    async put(nome, bytes) { kv.set(nome, new Uint8Array(bytes)); },
    async delete(nome) { kv.delete(nome); },
    async list() { return { keys: [...kv.keys()].map((name) => ({ name })) }; },
  };
  return { env: { BANCO, APKS, TOKEN_ENVIO: token }, arquivos, kv };
}

const chamar = (env, caminho, { metodo = "GET", corpo, token, cabecalhos = {} } = {}) => {
  const headers = { ...cabecalhos };
  if (token !== undefined) headers.authorization = `Bearer ${token}`;
  return worker.default.fetch(
    new Request(`https://bolaof1.teste${caminho}`, { method: metodo, body: corpo, headers }), env);
};
const enviar = (env, caminho, corpo, token = TOKEN) =>
  chamar(env, caminho, {
    metodo: "PUT", token,
    corpo: corpo instanceof Uint8Array || typeof corpo === "string" ? corpo : JSON.stringify(corpo),
  });

const UM_APK = (extra = 0) => new Uint8Array([0x50, 0x4b, 0x03, 0x04, ...new Array(10 + extra).fill(7)]);
const versao = (v = "0.3.0", build = 30) => ({
  versao: v, build, apk: `bolao-f1-v${v}-build${build}.apk`, notas: "n", publicado_em: "2026-10-30T12:00:00Z",
});

test("versao.json só entra com o APK já enviado e batendo com o nome", async () => {
  const { env } = criarEnv();
  const meta = versao();
  assert.equal((await enviar(env, "/api/app/versao.json", meta)).status, 409); // APK ainda não enviado
  assert.equal((await enviar(env, `/api/app/${meta.apk}`, UM_APK())).status, 200);
  assert.equal((await enviar(env, "/api/app/versao.json", { ...meta, build: 31 })).status, 422);
  assert.equal((await enviar(env, "/api/app/versao.json", { ...meta, versao: "9.9.9" })).status, 422);
  assert.equal((await enviar(env, "/api/app/versao.json", { ...meta, apk: "qualquer.apk" })).status, 422);
  assert.equal((await enviar(env, "/api/app/versao.json", "{quebrado")).status, 400);
  assert.equal((await enviar(env, "/api/app/versao.json", meta)).status, 200);
  const lido = await chamar(env, "/app/versao.json");
  assert.equal(lido.status, 200);
  assert.match(lido.headers.get("content-type"), /application\/json/);
  assert.deepEqual(await lido.json(), meta);
  // Resposta condicional: o mesmo ETag devolve 304 sem corpo.
  const etag = lido.headers.get("etag");
  assert.equal((await chamar(env, "/app/versao.json", { cabecalhos: { "if-none-match": etag } })).status, 304);
});

test("envio exige token e o nome do APK segue o padrão que o app lê", async () => {
  const { env } = criarEnv();
  assert.equal((await enviar(env, "/api/app/bolao-f1-v1.0.0-build1.apk", UM_APK(), "errado")).status, 401);
  assert.equal((await enviar(env, "/api/app/bolao-f1.apk", UM_APK())).status, 404);
  assert.equal((await enviar(env, "/api/app/bolao-f1-v1.0-build1.apk", UM_APK())).status, 404);
  assert.equal((await enviar(env, "/api/app/painel-status-v1.0.0-build1.apk", UM_APK())).status, 404);
  assert.equal((await chamar(env, "/api/app/versao.json", { token: TOKEN })).status, 405);
  // Sem o secret configurado, nada é aceito (nem token vazio).
  const semSegredo = criarEnv({ token: "" }).env;
  assert.equal((await enviar(semSegredo, "/api/app/bolao-f1-v1.0.0-build1.apk", UM_APK(), "")).status, 401);
});

test("só aceita zip (começa com PK) e limita o tamanho a 25 MiB", async () => {
  const { env } = criarEnv();
  const nome = "bolao-f1-v1.0.0-build1.apk";
  assert.equal((await enviar(env, `/api/app/${nome}`, "texto qualquer")).status, 422);
  assert.equal((await enviar(env, `/api/app/${nome}`, new Uint8Array([0x50, 0x4b]))).status, 422);
  assert.equal((await enviar(env, `/api/app/${nome}`, new Uint8Array(25 * 1024 * 1024 + 1))).status, 413);
  assert.equal((await enviar(env, `/api/app/${nome}`, UM_APK())).status, 200);
});

test("guarda só os 3 APKs mais novos (pelo build) e serve o download", async () => {
  const { env, kv } = criarEnv();
  for (const build of [1, 2, 3, 4]) {
    const r = await enviar(env, `/api/app/bolao-f1-v1.0.0-build${build}.apk`, UM_APK(build));
    assert.equal(r.status, 200);
  }
  assert.deepEqual([...kv.keys()].sort(), [2, 3, 4].map((b) => `bolao-f1-v1.0.0-build${b}.apk`));
  const apk = await chamar(env, "/app/bolao-f1-v1.0.0-build4.apk");
  assert.equal(apk.status, 200);
  assert.equal(apk.headers.get("content-type"), "application/vnd.android.package-archive");
  assert.match(apk.headers.get("content-disposition"), /attachment; filename="bolao-f1-v1\.0\.0-build4\.apk"/);
  assert.match(apk.headers.get("cache-control"), /immutable/);
  assert.equal((await apk.arrayBuffer()).byteLength, 4 + 14);
  const head = await chamar(env, "/app/bolao-f1-v1.0.0-build4.apk", { metodo: "HEAD" });
  assert.equal(head.status, 200);
  assert.equal((await chamar(env, "/app/bolao-f1-v1.0.0-build1.apk")).status, 404); // já apagado
});

test("/app/ só serve versao.json e APK com nome válido, só por GET/HEAD; fora disso, 404", async () => {
  const { env } = criarEnv();
  assert.equal((await chamar(env, "/app/versao.json")).status, 404); // nada publicado ainda
  assert.equal((await chamar(env, "/app/outra-coisa")).status, 404);
  assert.equal((await chamar(env, "/app/versao.json", { metodo: "POST", corpo: "{}" })).status, 404);
  assert.equal((await chamar(env, "/")).status, 404); // o resto do domínio é do Pages
});
