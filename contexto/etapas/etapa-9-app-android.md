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
  (confirmado pelo usuário em 2026-10-08; depois de publicado não muda).

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

## Sub-etapa 9a — esqueleto (2026-10-08)

**Entregue** (primeira run verde: #7 do `android.yml`): projeto Gradle em `android/` (um módulo `:app`), tela "Bolão F1"
com a versão instalada, tema Material 3 claro/escuro com as cores do site
(`--acento` `#E10600`; sem *dynamic color*), ícone adaptável (bandeira
quadriculada, com versão monocromática), workflow `android.yml`, regras em
`.claude/rules/android.md`, entradas no `.gitignore` e no `.gitattributes`.

**Decisões fixadas (governança do esqueleto):**
- **Versões** (todas em `android/gradle/libs.versions.toml`): AGP 9.4.1,
  Kotlin 2.4.21 (Kotlin embutido do AGP 9, sem o plugin `kotlin-android`),
  Compose BOM 2026.09.00, `compileSdk`/`targetSdk` 37, `minSdk` 26, Gradle
  9.7.1 no wrapper (jar com checksum oficial conferido e
  `distributionSha256Sum` fixado). Referência usada: `android/compose-samples`.
- **Ajuste ao plano — JDK 21 no CI** (o plano dizia 17): o Robolectric só
  simula Android 15+ rodando em JDK 21. O bytecode do app continua Java 17.
- **O CI barra o que estiver errado:** ordem testes → lint → APK; o lint
  trata aviso como erro e o compilador Kotlin também. Ficam desligadas só as
  checagens que mudam com a data (`GradleDependency`, `NewerVersionAvailable`,
  `AndroidGradlePluginVersion`, `OldTargetApi`), para o mesmo commit dar
  sempre o mesmo resultado. Se a run falhar, os relatórios de teste e lint
  ficam como artefato `relatorios-buildN`.
- **Testes JVM com Robolectric** (sem emulador): `HomeScreenTest` (tela nos
  temas claro e escuro) e `MainActivityTest`, que abre o app de verdade
  (manifest + tema + Activity). Se o app fecharia ao abrir no celular, o CI
  fica vermelho.
- **Versão:** `versionCode` = `github.run_number` do `android.yml` (por isso o
  workflow não pode ser renomeado nem recriado). `versionName` no debug =
  `dev-<sha7>-debug`, que aponta o commit exato do APK; a tela mostra versão e
  build. Sem as variáveis do CI, o build local usa `1` / `0.0.0-dev`.
- **Debug ao lado do oficial:** `applicationIdSuffix ".debug"` e nome
  "Bolão F1 (debug)". **Limitação conhecida:** cada run do CI assina o debug
  com uma chave descartável diferente, então um APK de debug **não instala
  por cima** de outro. Para trocar de build de debug, desinstalar o anterior.
  A atualização por cima é papel do release assinado (9b).
- **Sem backup:** `allowBackup="false"` + `res/xml/data_extraction_rules.xml`
  (Android 12+) + `res/xml/backup_rules.xml` (Android 8–11), todos excluindo
  tudo. Os dados vêm do site e a chave de envio (9e) não deve ir para a nuvem.
  O lint exige os dois XMLs.
- **Infra de teste fixada:** o Compose puxa Espresso 3.5, que chama
  `InputManager.getInstance()` (removido no Android 16+) e derruba os testes
  Robolectric. A família `androidx.test` (core, espresso-core, ext-junit) é
  declarada no catálogo com a versão atual. Os testes também precisam das
  flags `--add-opens` recomendadas pelo Robolectric para JDK 17+ (em
  `app/build.gradle.kts`) e usam `createComposeRule` do pacote `junit4.v2`
  (o antigo é depreciado e o aviso quebra o build).
- **Artefato sem zip** (`upload-artifact` com `archive: false`): o `.apk` é
  baixado direto pelo celular, na página da run (exige estar logado no
  GitHub). Validade de 30 dias.
- **Cache do Gradle no CI** com `cache-provider: basic` do `setup-gradle`
  (open source/MIT, em vez do provedor proprietário padrão).

**Como atualizar uma dependência (procedimento):** mudar a linha no
`libs.versions.toml` → commit `Etapa 9: atualiza X de A para B` → push → run
verde. Uma dependência por commit, para saber o que quebrou se quebrar. AGP
novo pode exigir Gradle mais novo (ver a tabela nas notas de versão do AGP).

**Ponto em aberto (2026-10-08) — verificação de desenvolvedor do Android:**
desde 30/09/2026, no Brasil, celulares Android certificados só instalam
normalmente apps de **desenvolvedor verificado**. App não registrado ainda
instala por ADB ou pelo **"fluxo avançado"** (configuração única: modo
desenvolvedor, reinício e espera de 24 h; depois o aviso "desenvolvedor não
verificado" tem "Instalar mesmo assim"). O APK de debug da 9a muda de chave a
cada run, então só instala por esses caminhos. **Decidir antes da 9b** se
registra uma conta gratuita de *distribuição limitada* (até 20 aparelhos, sem
documento nem taxa), cadastrando o `applicationId` e a chave do keystore de
release, ou se cada pessoa usa o fluxo avançado. Não muda a decisão de
distribuir por APK fora da Play Store.

## Sub-etapas 9b–9f (2026-10-08)

Feitas em sequência a pedido do usuário, antes de ele validar a 9a no
celular (validação no aparelho pendente para todas). Ordem real: 9c → 9d →
9e → 9b → 9f, para a primeira versão oficial já sair com o aviso de versão.

**9c — dados** (`data/`): modelos `kotlinx.serialization` em
`data/modelo/Modelos.kt` (nomes do JSON em `@SerialName`, todo campo não
identitário com padrão, `ignoreUnknownKeys`); `FonteRemota` (OkHttp),
`CacheDeArquivos` (gravação atômica em `filesDir/dados-do-site/`, mesmo
caminho do site) e `TemporadaRepositorio` (*stale-while-revalidate*). **O
cache só é trocado quando todos os arquivos chegam e são lidos** — JSON
quebrado no site nunca apaga o último conjunto bom. Os testes leem os JSONs
reais de `docs/data` (propriedade `bolao.dadosDoSite` passada pelo Gradle) e
conferem as contas das regras atuais (total = rodadas + compensação). O
`android.yml` também roda quando `docs/data/**` muda (nota na etapa-3).

**9d — telas** (`ui/`): `AppBolao` com barra superior (⚙️ Configurações) e
barra inferior Ranking · Corridas · Palpites · Enviar; navegação type-safe
(objetos `@Serializable`). Um `TemporadaViewModel` no escopo da Activity
alimenta as três abas da temporada (um download só). Regras de exibição em
funções puras (`ui/temporada/Apresentacao.kt`): ordem de jogadores do site
(pontos desc, `player_id` asc), quem não apostou aparece com o `min_score`
em itálico "(sem palpite)", cores 2/1/0 iguais às do site, cor de equipe por
rodada. Linha "Atualizado há X" e aviso de dados salvos quando o site não
responde; tela de erro com "Tentar de novo"; puxar para atualizar. Textos de
idade sem `<plurals>` ("há 5 min", "há 3 h", data) para o app ficar em
português qualquer que seja o idioma do celular.

**9e — envio** (`data/EnvioDePalpite.kt`, `ui/enviar`, `ui/configuracoes`):
POST `{chave, texto, round?}` para o `doPost`, seguindo o 302 do Google.
Resultados distintos: enviado · recusado (motivo do script) · falha de rede ·
resposta inesperada (ex.: página de login quando a implantação não é
"Qualquer pessoa"); nos dois últimos o app avisa para conferir antes de
reenviar (o palpite pode ter entrado). Confirmação antes de enviar; rodada
opcional 1–30. URL (só https) e chave no DataStore do aparelho, nunca no
APK. A versão instalada fica na seção "Sobre" das Configurações. Lado do
Apps Script: nota na etapa-6 e `SETUP.md` passo 8.

**9b — release assinado:** keystore PKCS12 (RSA 4096, validade 100 anos,
alias `bolaof1`) gerado com `openssl` **fora do repositório**, em
`Documents/BolaoF1-assinatura-app/` na máquina do usuário (com `LEIA-ME.txt`
das senhas; **backup pendente pelo usuário**). Secrets
`ANDROID_KEYSTORE_B64`/`_SENHA`/`ANDROID_KEY_ALIAS`/`ANDROID_KEY_SENHA`
cadastrados. Certificado SHA-256 (público):
`afa06a9aba9e80c48e76f490ab437a66b61762d29c30592106889f5610319978` — o job
`publicar` recusa APK assinado por outra chave. Release sem R8 na v1 (o APK
oficial roda o mesmo código que os testes exercitam).
**Chave compartilhada (2026-10-08):** o app Android do Painel de Status
(`gfvdata-web/painel-status`, pasta `android/`, feito no molde deste) assina
com **este mesmo keystore**; os 4 secrets foram cadastrados também lá. Perder o
keystore afeta os dois apps. Detalhes do painel: README dele, "App Android".

**9f — aviso de versão:** `VerificadorDeAtualizacao` lê
`/repos/.../releases?per_page=20` sem token, considera só tags `app-v*` que
não sejam rascunho/pré-release e acha o build pelo nome do APK
(`bolao-f1-vX.Y.Z-buildN.apk`, contrato com o `android.yml`). Avisa se o
build publicado for maior que o instalado; qualquer falha = sem aviso.

**Como publicar uma versão nova (procedimento):**
1. Commit(s) no `main` com a run do `android.yml` verde.
2. `git tag -a app-vX.Y.Z -m "…"` no commit e `git push origin app-vX.Y.Z`.
3. O job `publicar` roda depois de testes e lint, assina, confere a chave e
   cria o Release. Quem tem o app vê o aviso na próxima abertura.
- Versão: X.Y.Z segue o tamanho da mudança (Z correção, Y função nova, X
  mudança grande). O versionCode é o número da run e só cresce.

**Publicadas:** `app-v0.1.0` (build 13, primeira versão oficial) e
`app-v0.1.1` (mesmo código, só para validar a atualização por cima e o
aviso de versão no celular).
