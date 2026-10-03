---
paths:
  - ".github/**"
  - "google-apps-script/**"
  - "bolao/pipeline.py"
---

# Regras da automação (Actions, Apps Script, pipeline)

- CLI do pipeline: saída `0` pontuada · `1` erro real · `2` mensagem gravada
  mas quali ainda indisponível (liga o verificador). Não mudar o significado.
- O workflow commita a mensagem **antes** do verificador; o verificador re-tenta
  dentro da própria run (não usar `schedule:`/cron). Esgotado → job vermelho de
  propósito, para o GitHub mandar e-mail.
- Scripts de `.github/scripts/` são chamados com `bash script.sh` (o Windows
  não versiona bit de execução).
- Commit automático como `github-actions[bot]` com o `GITHUB_TOKEN` padrão.
- Apps Script: títulos das perguntas do Forms batem **exatamente** com
  `PERGUNTA_RODADA`/`PERGUNTA_TEXTO`; o PAT fica nas Propriedades do script,
  **nunca** no código nem no repositório.
- Evento `novo_palpite` + `client_payload {texto, round?}` é contrato entre
  Etapas 5 e 6 — mudar dos dois lados ou não mudar.

Detalhes: `contexto/etapas/etapa-5-github-actions.md`,
`contexto/etapas/etapa-6-forms-apps-script.md`, `google-apps-script/SETUP.md`.
