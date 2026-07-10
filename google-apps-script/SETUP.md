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
   `gfvdata-web/page-bolao-formula1`.
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

## 7. Renovação do token (lembrete)

O fine-grained PAT expira em ~1 ano. O GitHub já avisa por e-mail 7 dias antes
e no dia da expiração; também foi criado um lembrete agendado separado para
essa data. Quando renovar: gerar um novo token (passo 1) e atualizar só a
propriedade `GITHUB_TOKEN` (passo 4) — nada mais muda.

## Solução de problemas

- **E-mail de falha recebido:** confira a mensagem de erro (geralmente token
  inválido/expirado ou permissão errada). Corrigir o `GITHUB_TOKEN` nas
  Propriedades do script e reenviar o Forms, ou disparar `workflow_dispatch`
  (retry) manualmente na aba Actions do GitHub para a rodada correspondente.
- **Nada acontece ao enviar o Forms:** conferir se o gatilho `onFormSubmit`
  está mesmo criado (passo 5) e se os títulos das perguntas batem com
  `Code.gs`.
