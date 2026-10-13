// Testes do Apps Script (google-apps-script/Code.gs) sem rede e sem Google:
// o arquivo roda num vm com UrlFetchApp, PropertiesService, MailApp etc. falsos.
// Rodar: node --test tests/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const codigo = fs.readFileSync(path.join(raiz, 'google-apps-script', 'Code.gs'), 'utf8');

// Monta um ambiente novo do Apps Script. `opcoes.status` = código HTTP do GitHub
// (por repositório, padrão 204); `opcoes.props` = Propriedades do script.
function ambiente(opcoes = {}) {
  const props = { GITHUB_TOKEN: 'tok', APP_CHAVE: 'segredo', ALERTA_EMAIL: 'dono@example.com', ...(opcoes.props || {}) };
  const chamadas = [];
  const emails = [];
  const ctx = {
    PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => props[k] ?? null }) },
    Session: { getEffectiveUser: () => ({ getEmail: () => 'efetivo@example.com' }) },
    MailApp: { sendEmail: (m) => emails.push(m) },
    UrlFetchApp: {
      fetch: (url, init) => {
        chamadas.push({ url, init, payload: JSON.parse(init.payload) });
        const status = (opcoes.status || {})[url.split('/repos/gfvdata-web/')[1]?.split('/')[0]] ?? 204;
        return { getResponseCode: () => status, getContentText: () => 'corpo ' + status };
      },
    },
    ContentService: {
      MimeType: { JSON: 'json' },
      createTextOutput: (texto) => ({ texto, setMimeType() { return this; }, getContent() { return texto; } }),
    },
    Logger: { log() {} },
    JSON, parseInt, isNaN, Error,
  };
  vm.createContext(ctx);
  vm.runInContext(codigo, ctx);
  return { ctx, chamadas, emails };
}

const resposta = (saida) => JSON.parse(saida.texto);
const pedido = (obj) => ({ postData: { contents: JSON.stringify(obj) } });

test('Code.gs: constantes que ligam o Forms ao workflow do pipeline', () => {
  const { ctx } = ambiente();
  const yml = fs.readFileSync(path.join(raiz, '.github', 'workflows', 'pipeline.yml'), 'utf8');
  assert.match(yml, new RegExp(`types:\\s*\\[${vm.runInContext('GITHUB_EVENT_TYPE', ctx)}\\]`));
  assert.equal(vm.runInContext('GITHUB_REPO', ctx), 'page-bolao-formula1');
});

test('doPost: envio válido dispara o pipeline e avisa o painel', () => {
  const { ctx, chamadas } = ambiente();
  const r = resposta(ctx.doPost(pedido({ chave: 'segredo', texto: 'Qualify X\n...', round: '7' })));
  assert.deepEqual(r, { ok: true });
  assert.equal(chamadas.length, 2);
  assert.match(chamadas[0].url, /\/repos\/gfvdata-web\/page-bolao-formula1\/dispatches$/);
  assert.equal(chamadas[0].payload.event_type, 'novo_palpite');
  assert.deepEqual(chamadas[0].payload.client_payload, { texto: 'Qualify X\n...', round: 7 });
  assert.equal(chamadas[0].init.headers.Authorization, 'Bearer tok');
  assert.match(chamadas[1].url, /\/repos\/gfvdata-web\/painel-status\/dispatches$/);
  assert.equal(chamadas[1].payload.event_type, 'bolao_palpite');
});

test('doPost: sem rodada, o client_payload leva só o texto', () => {
  const { ctx, chamadas } = ambiente();
  ctx.doPost(pedido({ chave: 'segredo', texto: 'abc' }));
  assert.deepEqual(chamadas[0].payload.client_payload, { texto: 'abc' });
});

test('doPost: rodada que não é número é ignorada (o pipeline resolve pelo cabeçalho)', () => {
  const { ctx, chamadas } = ambiente();
  ctx.doPost(pedido({ chave: 'segredo', texto: 'abc', round: 'dez' }));
  assert.deepEqual(chamadas[0].payload.client_payload, { texto: 'abc' });
});

test('doPost: chave errada, texto vazio e corpo que não é JSON não disparam nada', () => {
  const { ctx, chamadas } = ambiente();
  assert.deepEqual(resposta(ctx.doPost(pedido({ chave: 'errada', texto: 'x' }))), { ok: false, erro: 'Chave de envio inválida.' });
  assert.deepEqual(resposta(ctx.doPost(pedido({ texto: 'x' }))), { ok: false, erro: 'Chave de envio inválida.' });
  assert.equal(resposta(ctx.doPost(pedido({ chave: 'segredo', texto: '   ' }))).ok, false);
  assert.equal(resposta(ctx.doPost({ postData: { contents: 'não é json' } })).ok, false);
  assert.equal(resposta(ctx.doPost(undefined)).ok, false);
  assert.equal(chamadas.length, 0);
});

test('doPost: sem APP_CHAVE configurada recusa e avisa por e-mail', () => {
  const { ctx, chamadas, emails } = ambiente({ props: { APP_CHAVE: null } });
  const r = resposta(ctx.doPost(pedido({ chave: 'qualquer', texto: 'x' })));
  assert.equal(r.ok, false);
  assert.match(r.erro, /APP_CHAVE/);
  assert.equal(chamadas.length, 0);
  assert.equal(emails.length, 1);
});

test('doPost: GitHub recusando (401) devolve erro ao app e manda e-mail', () => {
  const { ctx, emails, chamadas } = ambiente({ status: { 'page-bolao-formula1': 401 } });
  const r = resposta(ctx.doPost(pedido({ chave: 'segredo', texto: 'x' })));
  assert.equal(r.ok, false);
  assert.match(r.erro, /GitHub respondeu 401/);
  assert.equal(emails.length, 1);
  assert.equal(emails[0].to, 'dono@example.com');
  assert.equal(chamadas.length, 1); // não avisa o painel de um palpite que não entrou
});

test('doPost: falha só no aviso ao painel não derruba o palpite', () => {
  const { ctx, emails } = ambiente({ status: { 'painel-status': 404 } });
  assert.deepEqual(resposta(ctx.doPost(pedido({ chave: 'segredo', texto: 'x' }))), { ok: true });
  assert.equal(emails.length, 1);
  assert.match(emails[0].subject, /painel-status não foi avisado/);
});

test('onFormSubmit: lê as duas perguntas do Forms e dispara o pipeline', () => {
  const { ctx, chamadas } = ambiente();
  const item = (titulo, valor) => ({ getItem: () => ({ getTitle: () => titulo }), getResponse: () => valor });
  ctx.onFormSubmit({ response: { getItemResponses: () => [item('Rodada (opcional)', ' 12 '), item('Texto colado do WhatsApp', 'palpites')] } });
  assert.deepEqual(chamadas[0].payload.client_payload, { texto: 'palpites', round: 12 });
  assert.equal(chamadas.length, 2);
});

test('onFormSubmit: resposta sem o texto falha e avisa por e-mail', () => {
  const { ctx, emails, chamadas } = ambiente();
  const item = (titulo, valor) => ({ getItem: () => ({ getTitle: () => titulo }), getResponse: () => valor });
  assert.throws(() => ctx.onFormSubmit({ response: { getItemResponses: () => [item('Rodada (opcional)', '3')] } }), /sem o texto/);
  assert.equal(emails.length, 1);
  assert.equal(chamadas.length, 0);
});

test('token ausente: dispararRepositoryDispatch falha com mensagem clara', () => {
  const { ctx } = ambiente({ props: { GITHUB_TOKEN: null } });
  assert.throws(() => ctx.dispararRepositoryDispatch('page-bolao-formula1', 'novo_palpite', {}), /GITHUB_TOKEN/);
});

test('e-mail de alerta: ALERTA_EMAIL vence, senão usa o dono do script', () => {
  assert.equal(ambiente().ctx.obterEmailAlerta(), 'dono@example.com');
  assert.equal(ambiente({ props: { ALERTA_EMAIL: null } }).ctx.obterEmailAlerta(), 'efetivo@example.com');
});
