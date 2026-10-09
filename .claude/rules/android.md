---
paths:
  - "android/**"
  - ".github/workflows/android.yml"
---

# Regras do app Android (`android/`)

- **O build oficial é o do Actions** (`android.yml`: testes → lint → APK). Não
  há JDK/SDK na máquina local: mudança no app só está pronta com a **run verde**
  no GitHub (`gh run watch`). Run vermelha → corrigir antes de seguir.
- **Versões só em `gradle/libs.versions.toml`** (inclusive SDKs). Nenhum
  `build.gradle.kts` escreve número de versão. Atualizar **uma coisa por
  commit** (`Etapa 9: atualiza X de A para B`), com run verde.
- **Gradle wrapper:** trocar só com o jar oficial (checksum de
  `services.gradle.org`) e `distributionSha256Sum` atualizado; o
  `setup-gradle` valida o jar a cada run.
- **Lint e avisos do Kotlin barram o build** (`warningsAsErrors`,
  `allWarningsAsErrors`). Corrigir a causa; `@Suppress`/`lint.disable` só com
  comentário dizendo por quê. Checagens que dependem da data ficam desligadas
  (mesmo commit = mesmo resultado sempre).
- A família `androidx.test` é fixada no catálogo (o Compose puxa uma antiga
  que quebra no Android 16+). Ao subir o BOM do Compose, manter essa fixação.
- **Teste junto com o código:** tela, ViewModel ou repositório novo ganha teste
  JVM em `app/src/test` (Robolectric para telas). Nada de teste que precise de
  emulador ou rede.
- **Identidade:** `applicationId` `io.github.gfvdataweb.bolaof1` nunca muda; o
  debug usa o sufixo `.debug` e o nome "Bolão F1 (debug)".
- **`versionCode` = `github.run_number` do `android.yml`**: nunca fixar à mão,
  e **não renomear nem recriar o workflow** (a contagem recomeçaria e as
  atualizações deixariam de instalar por cima).
- **Versão oficial = tag `app-vX.Y.Z`** num commit com run verde (procedimento
  na etapa-9). O job `publicar` só aceita APK assinado pela chave oficial
  (SHA-256 em `android.yml`); nunca trocar a chave nem o nome do APK
  (`bolao-f1-vX.Y.Z-buildN.apk` é lido pelo aviso de versão do app).
- **Kotlin embutido do AGP 9:** não aplicar `org.jetbrains.kotlin.android`. O
  CI usa JDK 21 (Robolectric); o bytecode do app é Java 17.
- Textos de tela em `res/values/strings.xml` (pt-BR), não literais no Kotlin.
- **Segredos fora do app e do Git:** o PAT nunca entra no app; keystore e
  senhas só nos secrets do repositório (9b); a `APP_CHAVE` é digitada no app,
  não vai no APK (9e).
- Regras de tela em funções puras testáveis (`ui/temporada/Apresentacao.kt`);
  telas recebem estado pronto e callbacks (sem buscar dados sozinhas).
- Testes que precisam de rede usam servidor local (`apoio/SiteLocal`,
  MockWebServer); o app de teste (`BolaoAppDeTeste`) aponta para ele.
- JSON do site lido com `ignoreUnknownKeys = true`; os formatos de `docs/data/`
  só mudam de forma aditiva (o app é um segundo consumidor).

Arquitetura, sub-etapas e decisões: `contexto/etapas/etapa-9-app-android.md`.
