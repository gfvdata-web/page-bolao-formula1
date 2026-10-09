# Etapa 6 — Setup do Google Forms + Apps Script

Passo a passo para deixar o disparo funcionando pelo celular. Feito uma vez só
(depois é só usar o Forms a cada rodada).

## 1. Gerar o fine-grained PAT no GitHub

1. `github.com` → foto de perfil → **Settings** → **Developer settings** →
   **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. **Token name:** `bolao-f1-forms` (ou outro nome que identifique o uso).
3. **Expiration:** 366 dias (o máximo para conta pessoal).
4. **Resource owner:** sua conta pessoal.
5. **Repository access:** "Only select repositories" → escolher
   `gfvdata-web/page-bolao-formula1` **e** `gfvdata-web/painel-status` (o
   segundo é para o painel acompanhar o pipeline ao vivo; ver "Aviso ao
   painel-status" abaixo).
6. **Permissions → Repository permissions:** `Contents` → **Read and write**
   (é o que autoriza disparar `repository_dispatch`). Não precisa de mais nada.
7. **Generate token** e copiar o valor (`github_pat_...`) — só aparece uma vez.

## 2. Criar o Google Forms

1. `forms.google.com` → **+ Em branco**. Título: `Bolão F1 — Palpite`.
2. Pergunta 1 — tipo **Resposta curta**:
   - Título exato: `Rodada (opcional)`
   - Não obrigatória (o pipeline resolve pela mensagem se ficar em branco).
3. Pergunta 2 — tipo **Parágrafo**:
   - Título exato: `Texto colado do WhatsApp`
   - Obrigatória.
4. Os títulos precisam bater **exatamente** com `PERGUNTA_RODADA` e
   `PERGUNTA_TEXTO` no topo de `Code.gs` — se mudar o texto da pergunta no
   Forms, ajustar também no script (ou vice-versa).

## 3. Criar o Apps Script vinculado ao Forms

1. No Forms, menu **⋮** (canto superior direito) → **Editor de script**
   (abre um projeto Apps Script já vinculado a este Forms).
2. Apagar o conteúdo padrão de `Code.gs` e colar o conteúdo de
   [`Code.gs`](Code.gs) deste repositório.
3. Salvar (ícone de disquete ou Ctrl+S).

## 4. Configurar as Propriedades do script

1. No editor do Apps Script: ⚙️ **Configurações do projeto** (ícone de
   engrenagem na barra lateral) → **Propriedades do script** → **Adicionar
   propriedade do script**.
2. Adicionar:
   - `GITHUB_TOKEN` = o token `github_pat_...` gerado no passo 1.
   - `ALERTA_EMAIL` (opcional) = e-mail para receber avisos de falha. Se
     omitido, usa automaticamente o e-mail da conta Google dona do script.

## 5. Criar o gatilho (trigger) de envio do Forms

1. Na barra lateral do editor: ⏰ **Gatilhos** → **Adicionar gatilho**.
2. Configurar:
   - Função a executar: `onFormSubmit`
   - Fonte do evento: **From form** (Do formulário)
   - Tipo de evento: **On form submit** (Ao enviar formulário)
3. Salvar. Na primeira vez, o Google vai pedir para autorizar o script
   (acesso a Forms/execução externa/e-mail) — autorizar com a mesma conta
   Google.

## 6. Testar

**Teste rápido (sem enviar o Forms de verdade):**
No editor do Apps Script, selecionar a função `testarDisparoManual` no
seletor de funções (topo) e clicar em **Executar**. Confirmar no GitHub
Actions (`Actions` do repo) que um workflow run apareceu para a rodada 1.

**Teste ponta a ponta:**
Preencher o Google Forms pelo celular com um bloco de palpites real (ou o
texto de teste) e enviar. Conferir:
- GitHub → aba **Actions** → run novo iniciado pelo evento `novo_palpite`.
- Site (`https://gfvdata-web.github.io/page-bolao-formula1/`) atualizado
  depois que o run terminar.

## Aviso ao painel-status

A cada envio, depois de disparar o pipeline, o script também manda um
`repository_dispatch` (`bolao_palpite`) para `gfvdata-web/painel-status`. Lá, o
job `vigiar-bolao` acompanha o pipeline etapa por etapa até terminar e atualiza
o painel (https://gfvdata-web.github.io/painel-status/). Se esse aviso falhar,
o palpite segue normal e chega um e-mail "[Bolão F1] Palpite enviado, mas o
painel-status não foi avisado".

**Token criado antes desse aviso (só com `page-bolao-formula1`):** não precisa
gerar outro. Em GitHub → Settings → Developer settings → Fine-grained tokens →
clicar no token → **Edit** → Repository access → adicionar
`gfvdata-web/painel-status` → salvar. A permissão `Contents: Read and write`
vale para os dois. O valor do token não muda.

Teste: no editor do Apps Script, executar `testarAvisoPainel` e conferir na aba
Actions do `painel-status` um run "Atualizar status" com o evento
`repository_dispatch` (ele desiste em 10 min se não houver pipeline novo).

## 7. Renovação do token (lembrete)

O fine-grained PAT expira em ~1 ano. O GitHub avisa por e-mail, mas na prática
o aviso pode chegar perto ou depois da expiração real — não confiar só nisso.
Por isso também existe um lembrete agendado com ~2 semanas de folga antes da
data de expiração (ver data atual em `contexto/visao-geral.md`, seção 10). Quando renovar:
gerar um novo token (passo 1) e atualizar só a propriedade `GITHUB_TOKEN`
(passo 4) — nada mais muda. Depois, atualizar a data de expiração e o
lembrete em `contexto/visao-geral.md`.

## 8. Envio pelo app Android (Etapa 9e)

O app manda o palpite direto para o script (função `doPost`), sem passar pelo
Forms. O Forms continua funcionando em paralelo; o payload enviado ao GitHub é
o mesmo.

1. **Criar a chave do app:** em ⚙️ Configurações do projeto → Propriedades do
   script, adicionar `APP_CHAVE` com um texto aleatório longo (40+ letras e
   números; dá para gerar no gerenciador de senhas). Quem tiver essa chave
   consegue enviar palpites — não compartilhar no grupo.
2. **Publicar como app da web:** no editor, **Implantar** → **Nova
   implantação** → ⚙️ tipo **App da Web**:
   - Descrição: `app Android`
   - Executar como: **Eu** (a conta dona do script, que tem o `GITHUB_TOKEN`)
   - Quem pode acessar: **Qualquer pessoa** (o app não faz login no Google; a
     proteção é a `APP_CHAVE`)
   - **Implantar** e autorizar, se pedir. Copiar a **URL do app da web**
     (termina em `/exec`).
3. **No app:** ⚙️ Configurações → colar a URL e a chave → **Salvar**.
4. **Testar sem disparar nada:** no editor, executar
   `testarDoPostChaveErrada` e ver no log `{"ok":false,"erro":"Chave de envio
   inválida."}`. Depois, enviar um palpite real pelo app e conferir o run
   novo na aba Actions.

**Ao mudar o `Code.gs` depois:** colar o código novo e ir em **Implantar** →
**Gerenciar implantações** → ✏️ editar a implantação `app Android` → Versão
**Nova versão** → Implantar. Assim a URL continua a mesma (uma "Nova
implantação" criaria outra URL, e o app teria que ser reconfigurado).

**Trocar a chave** (ex.: vazou): mudar `APP_CHAVE` nas Propriedades e digitar
a nova no app. Não precisa reimplantar.

## Solução de problemas

- **E-mail de falha recebido:** confira a mensagem de erro (geralmente token
  inválido/expirado ou permissão errada). Corrigir o `GITHUB_TOKEN` nas
  Propriedades do script e reenviar o Forms, ou disparar `workflow_dispatch`
  (retry) manualmente na aba Actions do GitHub para a rodada correspondente.
- **App diz "chave de envio inválida":** a chave digitada no app não é igual à
  `APP_CHAVE` (espaços sobrando contam).
- **App diz "resposta inesperada":** em geral a implantação não está com acesso
  "Qualquer pessoa" (o Google devolve uma página de login em vez do JSON) ou a
  URL não é a do app da web (`/exec`). Conferir na aba Actions se o palpite
  entrou antes de reenviar.
- **Nada acontece ao enviar o Forms:** conferir se o gatilho `onFormSubmit`
  está mesmo criado (passo 5) e se os títulos das perguntas batem com
  `Code.gs`.
