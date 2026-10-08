# Etapa 9 — App Android nativo (Kotlin + Jetpack Compose)

> Plano escrito em 2026-10-08. Status da etapa: ver `contexto/status.md`.

- **Objetivo:** um app Android **nativo** do Bolão, instalado por APK (fora da
  Play Store), que mostra os dados da temporada e **envia o palpite** no lugar
  do Google Forms. Serve também de **experimento de estrutura** para apps de
  outros projetos: a base tem que ser a de um app de verdade, não uma casca.
- **Pronto quando (v1):** o APK gerado e assinado pelo Actions instala no
  celular, atualiza por cima sem desinstalar, mostra Ranking/Corridas/Palpites
  da temporada atual (também sem internet, com os últimos dados) e um palpite
  enviado pelo app atualiza o site de ponta a ponta.
- **Depende de:** Etapa 3 (formatos de `docs/data/`), Etapa 5 (evento
  `novo_palpite` e payload), Etapa 6 (Apps Script e PAT).
- **Não muda:** pipeline Python, formatos de dados, site. O Forms continua
  funcionando em paralelo.

**Decisões fixadas (conversa de 2026-10-07/08, não reabrir sem o usuário pedir):**
- **Nativo em Kotlin + Jetpack Compose**, só Android. Foram descartados a PWA e
  a casca WebView/TWA ("instalado assim fica ruim"), o Capacitor (continua
  sendo um site) e o Flutter (o iPhone está fora de cogitação: não instala
  APK, exigiria conta Apple paga e um Mac).
- **Distribuição por APK** em GitHub Releases. Sem Play Store por enquanto.
- **Mesmo repositório**, na pasta `android/`. A reutilização em outros
  projetos fica para depois (o projeto pode ser extraído para um repo-modelo).
- **Não há servidor novo.** O app **lê** os JSONs publicados no GitHub Pages
  (`https://gfvdata-web.github.io/page-bolao-formula1/data/...`) e **escreve**
  pelo Apps Script, que já tem o PAT.
- **O PAT do GitHub nunca entra no app.** O app só conhece a URL do Apps
  Script e uma chave de envio.

## Arquitetura do app

```
android/
  settings.gradle.kts, build.gradle.kts, gradle/libs.versions.toml (catálogo de versões)
  app/src/main/java/.../
    data/       modelos (kotlinx.serialization), cliente HTTP, cache, repositórios
    ui/         telas Compose + ViewModels, tema, navegação
    App.kt      contêiner de dependências (manual)
  app/src/test/ testes JVM (leem os JSONs reais de ../docs/data)
```

- **Uma Activity** com Navigation Compose e **barra inferior** com as abas.
- **MVVM:** cada tela tem um `ViewModel` que expõe um `StateFlow` com os
  estados carregando, dados e erro. Os repositórios entregam os dados.
- **Rede:** OkHttp + kotlinx.serialization com `ignoreUnknownKeys = true`.
  Campos novos no JSON (sempre aditivos, regra das etapas 3/7) não quebram o app.
- **Cache offline:** cada JSON baixado é salvo em `filesDir`. A tela abre com o
  cache na hora e atualiza em segundo plano (*stale-while-revalidate*),
  mostrando "atualizado há X".
- **Injeção de dependências manual** (um `AppContainer`) na v1. Hilt fica para
  quando o app crescer, para não pesar no começo.
- **Tema Material 3**, claro/escuro seguindo o sistema. As cores das equipes
  vêm de `equipes.json`.
- **Compatibilidade:** `minSdk 26` (Android 8), `targetSdk` igual à versão
  atual. Nome: **Bolão F1**. `applicationId`: `io.github.gfvdataweb.bolaof1`
  (*a confirmar com o usuário na 9a; depois de publicado não muda*).

## Envio do palpite

O fluxo é o mesmo do Forms, com o app entrando por uma porta lateral:

```
App: tela "Palpite" (texto colado do WhatsApp + rodada opcional)
  → POST JSON {chave, texto, round?} → Apps Script doPost (app da web)
    → valida a chave → dispararRepositoryDispatch(novo_palpite) + avisarPainel
      → pipeline normal (Etapa 5)
```

- `doPost(e)` em `Code.gs` **reaproveita** `dispararRepositoryDispatch` e
  `avisarPainel`. O payload é idêntico ao do `onFormSubmit` (`texto`, `round`
  opcional). Ele responde com JSON `{ok: true}` ou `{ok: false, erro}`, e em caso
  de falha também manda o e-mail de `notificarErro`.
- **Publicação:** "Implantar como app da web", executando como o dono do
  script, com acesso "Qualquer pessoa". A proteção é a propriedade
  **`APP_CHAVE`**: uma chave aleatória longa, conferida a cada POST.
- **A chave vai na tela de Configurações do app**, digitada uma vez e salva no
  DataStore. Ela **não vai dentro do APK**, então o mesmo APK pode ser dado aos
  amigos só para consulta, sem permitir envio.
- **Atenção técnica:** o Apps Script responde ao POST com um redirect 302 para
  `script.googleusercontent.com`. O `doPost` já rodou quando o redirect chega;
  o cliente segue o redirect com GET para ler a resposta, e o OkHttp faz isso
  por padrão. Testar esse comportamento na 9e.
- A v1 só tem o campo de texto livre, espelhando o Forms. Validar o palpite
  antes do envio (campos separados de top6 e piloto) fica para depois.

## Build, assinatura e atualização

- **Workflow novo `.github/workflows/android.yml`:** roda em push que mexe em
  `android/**`, ou manualmente (`workflow_dispatch`). Usa JDK 17 + Gradle e
  roda os testes antes de montar o APK. O `pipeline.yml` não é afetado, porque
  só dispara por `repository_dispatch`/`workflow_dispatch`.
- **Assinatura:** um keystore gerado **uma única vez** (`keytool`), guardado
  como secrets em base64: `ANDROID_KEYSTORE_B64`, `ANDROID_KEYSTORE_SENHA`,
  `ANDROID_KEY_ALIAS` e `ANDROID_KEY_SENHA`. **Fazer backup do keystore fora do
  Git** (gerenciador de senhas ou Drive). Se ele for perdido, nenhuma
  atualização instala por cima e todo mundo precisa reinstalar.
- **Versão:** `versionCode` = `github.run_number`. `versionName` vem da tag
  (`app-v1.0.0`). Uma tag `app-v*` publica o APK assinado em um Release.
- **Aviso de nova versão:** ao abrir, o app consulta a API pública de Releases
  (sem token) e, se houver `versionCode` maior, mostra um aviso com o link de
  download. O Android pede confirmação e instala por cima.
- **`.gitignore`:** acrescentar `*.jks`, `*.keystore`, `android/local.properties`,
  `android/.gradle/`, `android/**/build/`.
- **Desenvolvimento:** o build oficial é o do Actions, coerente com a operação
  pelo celular. O Android Studio no PC é opcional, para quem quiser rodar e
  depurar localmente.

## Sub-etapas (cada uma = um ou mais commits)

| # | Entrega | Validação |
|---|---------|-----------|
| 9a | Esqueleto do projeto Gradle (catálogo de versões, tema, uma tela "Bolão F1"), workflow que gera o APK de debug como artefato, `.gitignore`, `.claude/rules/android.md` | APK baixado do Actions instala e abre no celular |
| 9b | Keystore + secrets + build de release assinado + Release por tag | Instalar `app-v0.1.0` e depois `app-v0.1.1` **por cima**, sem desinstalar |
| 9c | Camada de dados: modelos de `seasons`/`standings`/`results`/`bets`/`calendar`/`equipes`, cliente, cache offline, repositórios. Testes JVM lendo `docs/data/` real | Testes verdes no Actions |
| 9d | Telas v1 da temporada atual: **Ranking** (Geral), **Corridas** (resultado e pontos por rodada), **Palpites** (por rodada), barra inferior, puxar para atualizar | Uso real no celular, com e sem internet |
| 9e | `doPost` + `APP_CHAVE` no Apps Script (com `SETUP.md` atualizado), tela **Palpite**, tela **Configurações** (chave) | Palpite enviado pelo app atualiza o site (ponta a ponta) |
| 9f | Aviso de nova versão via Releases | Publicar uma versão nova e ver o aviso aparecer |

**Depois da v1 (fora do escopo agora, em ordem provável):** Rendimento (os
gráficos exigem uma biblioteca Compose, como Vico, ou desenho em Canvas),
Pilotos, Hall of Fame, temporadas antigas e perfis (`?ano`, `?jogador`,
`?piloto`, menu da Etapa 8), Simulador, validação do palpite antes do envio,
**notificação push** (Firebase Cloud Messaging com tópico único, disparado
pelo fim do `pipeline.yml`: "quali pontuado, você fez X pts") e o
acompanhamento do pipeline dentro do app.

**Notas para registrar quando acontecer:**
- Na 9c: nota em `etapa-3`. `docs/data/` passa a ter um segundo consumidor
  (o app), e mudanças nesses formatos têm que continuar aditivas.
- Na 9e: nota em `etapa-6` e em `SETUP.md` sobre o `doPost`, a `APP_CHAVE` e
  a implantação como app da web.
