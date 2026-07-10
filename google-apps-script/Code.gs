/**
 * Bolão F1 — Etapa 6
 * Dispara um repository_dispatch no GitHub a cada resposta do Google Forms,
 * repassando o texto colado do WhatsApp para o pipeline (bolao/pipeline.py).
 *
 * Configuração necessária (Extensões > Propriedades do projeto > Propriedades do script):
 *   GITHUB_TOKEN  — fine-grained PAT, só repo page-bolao-formula1, "Contents: Read and write"
 *   ALERTA_EMAIL  — (opcional) e-mail para avisos de falha; sem isso usa o dono do script
 *
 * Trigger necessário (Extensões > Gatilhos): onFormSubmit, do tipo "From form" / "On form submit".
 */

const GITHUB_OWNER = 'gfvdata-web';
const GITHUB_REPO = 'page-bolao-formula1';
const GITHUB_EVENT_TYPE = 'novo_palpite';

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

    dispararRepositoryDispatch(clientPayload);
  } catch (erro) {
    notificarErro(erro);
    throw erro;
  }
}

function dispararRepositoryDispatch(clientPayload) {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    throw new Error('Propriedade GITHUB_TOKEN não configurada (Propriedades do script).');
  }

  const url = 'https://api.github.com/repos/' + GITHUB_OWNER + '/' + GITHUB_REPO + '/dispatches';
  const payload = {
    event_type: GITHUB_EVENT_TYPE,
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
  dispararRepositoryDispatch({
    texto: 'Qualify Bolao Teste\nPiloto Verstappen\n\nTeste\nVER\nHAM\nNOR\nLEC\nPIA\nRUS\nP1',
    round: 1
  });
}
