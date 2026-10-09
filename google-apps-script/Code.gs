/**
 * Bolão F1 — Etapa 6
 * Dispara um repository_dispatch no GitHub a cada resposta do Google Forms,
 * repassando o texto colado do WhatsApp para o pipeline (bolao/pipeline.py).
 *
 * Também avisa o painel-status (outro repositório), que acompanha o pipeline ao
 * vivo até terminar. Falha nesse aviso não afeta o palpite: só gera e-mail.
 *
 * Configuração necessária (Extensões > Propriedades do projeto > Propriedades do script):
 *   GITHUB_TOKEN  — fine-grained PAT, repos page-bolao-formula1 e painel-status,
 *                   "Contents: Read and write"
 *   ALERTA_EMAIL  — (opcional) e-mail para avisos de falha; sem isso usa o dono do script
 *   APP_CHAVE     — (app Android, Etapa 9e) chave longa aleatória exigida no doPost
 *
 * Trigger necessário (Extensões > Gatilhos): onFormSubmit, do tipo "From form" / "On form submit".
 *
 * App Android (Etapa 9e): o doPost recebe o palpite pelo app, com o MESMO
 * client_payload do Forms. Exige "Implantar > App da Web" (executar como você,
 * acesso "Qualquer pessoa"); a proteção é a APP_CHAVE. Ver SETUP.md, passo 8.
 */

const GITHUB_OWNER = 'gfvdata-web';
const GITHUB_REPO = 'page-bolao-formula1';
const GITHUB_EVENT_TYPE = 'novo_palpite';
const PAINEL_REPO = 'painel-status';
const PAINEL_EVENT_TYPE = 'bolao_palpite';

// Precisam bater com o título exato das perguntas no Google Forms.
const PERGUNTA_RODADA = 'Rodada (opcional)';
const PERGUNTA_TEXTO = 'Texto colado do WhatsApp';

function onFormSubmit(e) {
  try {
    const respostas = e.response.getItemResponses();
    let rodadaBruta = '';
    let texto = '';

    respostas.forEach(function (resposta) {
      const titulo = resposta.getItem().getTitle();
      if (titulo === PERGUNTA_RODADA) {
        rodadaBruta = resposta.getResponse().trim();
      } else if (titulo === PERGUNTA_TEXTO) {
        texto = resposta.getResponse();
      }
    });

    if (!texto) {
      throw new Error('Resposta do Forms sem o texto colado do WhatsApp.');
    }

    const clientPayload = { texto: texto };
    if (rodadaBruta) {
      const rodadaNum = parseInt(rodadaBruta, 10);
      if (!isNaN(rodadaNum)) {
        clientPayload.round = rodadaNum;
      }
    }

    dispararRepositoryDispatch(GITHUB_REPO, GITHUB_EVENT_TYPE, clientPayload);
  } catch (erro) {
    notificarErro(erro);
    throw erro;
  }
  avisarPainel();
}

/**
 * Envio pelo app Android (Etapa 9e). Corpo JSON: {chave, texto, round?}.
 * Responde JSON {ok: true} ou {ok: false, erro}. Chave errada ou texto vazio
 * só voltam o erro para o app (sem e-mail); falha ao avisar o GitHub manda o
 * mesmo e-mail do Forms.
 */
function doPost(e) {
  let pedido;
  try {
    pedido = JSON.parse((e && e.postData && e.postData.contents) || '');
  } catch (erro) {
    return responderJson({ ok: false, erro: 'O pedido não veio em JSON.' });
  }

  const chaveEsperada = PropertiesService.getScriptProperties().getProperty('APP_CHAVE');
  if (!chaveEsperada) {
    const erro = new Error('Propriedade APP_CHAVE não configurada (Propriedades do script).');
    notificarErro(erro);
    return responderJson({ ok: false, erro: erro.message });
  }
  if (!pedido || typeof pedido.chave !== 'string' || pedido.chave !== chaveEsperada) {
    return responderJson({ ok: false, erro: 'Chave de envio inválida.' });
  }

  const texto = typeof pedido.texto === 'string' ? pedido.texto : '';
  if (!texto.trim()) {
    return responderJson({ ok: false, erro: 'O texto do palpite está vazio.' });
  }

  // Mesmo client_payload do onFormSubmit (contrato com o pipeline, Etapa 5).
  const clientPayload = { texto: texto };
  if (pedido.round !== undefined && pedido.round !== null && pedido.round !== '') {
    const rodadaNum = parseInt(pedido.round, 10);
    if (!isNaN(rodadaNum)) {
      clientPayload.round = rodadaNum;
    }
  }

  try {
    dispararRepositoryDispatch(GITHUB_REPO, GITHUB_EVENT_TYPE, clientPayload);
  } catch (erro) {
    notificarErro(erro);
    return responderJson({ ok: false, erro: 'Falha ao avisar o GitHub: ' + erro.message });
  }
  avisarPainel();
  return responderJson({ ok: true });
}

function responderJson(objeto) {
  return ContentService.createTextOutput(JSON.stringify(objeto))
    .setMimeType(ContentService.MimeType.JSON);
}

function avisarPainel() {
  try {
    dispararRepositoryDispatch(PAINEL_REPO, PAINEL_EVENT_TYPE, {});
  } catch (erro) {
    notificarErroPainel(erro);
  }
}

function dispararRepositoryDispatch(repo, eventType, clientPayload) {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    throw new Error('Propriedade GITHUB_TOKEN não configurada (Propriedades do script).');
  }

  const url = 'https://api.github.com/repos/' + GITHUB_OWNER + '/' + repo + '/dispatches';
  const payload = {
    event_type: eventType,
    client_payload: clientPayload
  };

  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github+json'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const status = response.getResponseCode();
  if (status !== 204) {
    throw new Error('GitHub respondeu ' + status + ': ' + response.getContentText());
  }
}

function notificarErro(erro) {
  const destinatario = obterEmailAlerta();
  if (!destinatario) {
    return;
  }
  MailApp.sendEmail({
    to: destinatario,
    subject: '[Bolão F1] Falha ao disparar palpite',
    body:
      'O Apps Script falhou ao enviar o palpite para o GitHub.\n\n' +
      'Erro: ' + erro.message + '\n\n' +
      'O que fazer: confira o GITHUB_TOKEN (validade/permissão) em Propriedades do ' +
      'script, e depois reenvie o palpite (novo envio do Forms) ou dispare o ' +
      'workflow_dispatch (retry) manualmente no GitHub Actions.'
  });
}

function notificarErroPainel(erro) {
  const destinatario = obterEmailAlerta();
  if (!destinatario) {
    return;
  }
  MailApp.sendEmail({
    to: destinatario,
    subject: '[Bolão F1] Palpite enviado, mas o painel-status não foi avisado',
    body:
      'O palpite chegou ao pipeline normalmente; só o aviso ao painel-status falhou, ' +
      'então o painel vai mostrar o andamento só na rotina de 3 em 3 horas.\n\n' +
      'Erro: ' + erro.message + '\n\n' +
      'O que fazer: confira se o GITHUB_TOKEN tem acesso também ao repositório ' +
      'painel-status (Contents: Read and write).'
  });
}

function obterEmailAlerta() {
  const propriedade = PropertiesService.getScriptProperties().getProperty('ALERTA_EMAIL');
  if (propriedade) {
    return propriedade;
  }
  return Session.getEffectiveUser().getEmail() || null;
}

/**
 * Função de teste manual: roda no editor do Apps Script (sem precisar
 * enviar o Forms de verdade) para validar token e conectividade.
 */
function testarDisparoManual() {
  dispararRepositoryDispatch(GITHUB_REPO, GITHUB_EVENT_TYPE, {
    texto: 'Qualify Bolao Teste\nPiloto Verstappen\n\nTeste\nVER\nHAM\nNOR\nLEC\nPIA\nRUS\nP1',
    round: 1
  });
}

/**
 * Teste só do aviso ao painel-status: roda o job que acompanha o pipeline
 * (sem execução nova do Bolão, ele desiste em 10 min).
 */
function testarAvisoPainel() {
  dispararRepositoryDispatch(PAINEL_REPO, PAINEL_EVENT_TYPE, {});
}

/**
 * Teste do doPost sem disparar nada: simula um pedido com chave errada e
 * mostra a resposta no log (deve ser ok: false, "Chave de envio inválida.").
 */
function testarDoPostChaveErrada() {
  const resposta = doPost({ postData: { contents: JSON.stringify({ chave: 'errada', texto: 'teste' }) } });
  Logger.log(resposta.getContent());
}
