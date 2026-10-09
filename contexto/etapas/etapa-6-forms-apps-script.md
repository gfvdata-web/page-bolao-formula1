# Etapa 6 — Google Forms + Apps Script

> Movido do antigo `CONTEXTO.md` (seção 8) sem alteração de conteúdo. Status da etapa: ver `contexto/status.md`.

- **Objetivo:** formulário no celular + Apps Script que dispara o
  `repository_dispatch` com o texto colado e a corrida.
- **Pronto quando:** enviar o formulário pelo celular atualiza o site
  ponta-a-ponta.
- **Depende de:** Etapa 5 (nome do evento e formato do payload).
- **Entregue:** `google-apps-script/Code.gs` (função `onFormSubmit` +
  `dispararRepositoryDispatch` + `notificarErro` + `testarDisparoManual`) e
  `google-apps-script/SETUP.md` (passo a passo completo: gerar o token,
  criar o Forms, vincular o Apps Script, configurar propriedades/gatilho,
  testar). Setup manual executado na conta Google real (token fine-grained
  gerado, Forms criado, Apps Script vinculado, propriedades e gatilho
  configurados). **Validado via `testarDisparoManual`**: disparo real de
  `repository_dispatch` confirmado na aba Actions do repositório (run
  iniciado corretamente pelo evento `novo_palpite`).
- **Pendência de validação (não bloqueia a etapa):** o gatilho instalável
  `onFormSubmit` (envio real pelo Google Forms, em vez do teste manual)
  ainda não foi exercitado ponta a ponta — combinado com o usuário testar
  isso no envio de palpites da próxima corrida real. Se falhar nesse
  primeiro uso real, o mais provável é os títulos das perguntas do Forms
  não baterem com `PERGUNTA_RODADA`/`PERGUNTA_TEXTO` em `Code.gs`, ou o
  gatilho ter sido criado sem a autorização completa (ver "Solução de
  problemas" em `SETUP.md`).

**Decisões fixadas na Etapa 6 (não reabrir sem o usuário pedir):**
- **Autenticação:** fine-grained PAT do GitHub (repos `page-bolao-formula1`
  e, desde 2026-10-03, `painel-status` — para o aviso ao painel; permissão `Contents: Read and write`, expiração de
  366 dias), guardado em `PropertiesService` (Propriedades do script) do
  Apps Script — nunca no código-fonte nem no repositório. **Renovado em
  2026-08-15** (o anterior já tinha expirado — o aviso por e-mail do GitHub
  chegou perto/depois da expiração, não 7 dias antes como esperado); novo
  token válido até **2026-12-31**. Lembrete de renovação agendado para
  2026-12-15 (~2 semanas antes, com folga por não confiar só no aviso do
  GitHub).
- **Campo "Rodada" do Forms:** resposta curta, **opcional** — texto livre
  ou vazio; o pipeline já resolve a rodada pelo cabeçalho da mensagem
  quando `round` vem omitido (decisão da Etapa 5).
- **Campo do texto:** um único campo "Parágrafo", obrigatório, com o bloco
  inteiro colado do WhatsApp — vai direto para `client_payload.texto`.
- **Títulos das perguntas no Forms devem bater exatamente** com
  `PERGUNTA_RODADA`/`PERGUNTA_TEXTO` no topo de `Code.gs` (`"Rodada
  (opcional)"` e `"Texto colado do WhatsApp"`).
- **Falha ao disparar:** `notificarErro` manda e-mail (via `MailApp`) para
  `ALERTA_EMAIL` (propriedade opcional) ou, na ausência, para o e-mail
  efetivo do dono do script — inclui o erro e a orientação de reenviar o
  Forms ou usar `workflow_dispatch` (retry) manualmente.
- Nenhuma mudança no pipeline Python, no workflow do Actions nem no
  front-end — a Etapa 6 só adiciona `google-apps-script/` como novo
  disparador do evento `novo_palpite` já existente.

**Nota (Etapa 9e, 2026-10-08) — envio pelo app Android:** `Code.gs` ganhou
`doPost` (app da web, acesso "Qualquer pessoa", executa como o dono) que
reaproveita `dispararRepositoryDispatch` + `avisarPainel` com o **mesmo**
`client_payload {texto, round?}` do `onFormSubmit` — o contrato com a Etapa 5
não muda. Proteção pela propriedade `APP_CHAVE` (digitada no app, nunca no
APK). Chave errada/texto vazio só voltam `{ok:false, erro}` (sem e-mail);
falha no GitHub ou `APP_CHAVE` ausente mandam o e-mail de `notificarErro`.
Implantação e troca de chave: `google-apps-script/SETUP.md`, passo 8.
Detalhes do lado do app: `etapa-9-app-android.md`.
