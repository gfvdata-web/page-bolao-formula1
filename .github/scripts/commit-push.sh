#!/usr/bin/env bash
# Commita e empurra os dados gerados pelo pipeline (data/ e docs/data/).
#
# Usado duas vezes pelo workflow: logo depois do palpite novo chegar e, de novo,
# quando o "verificador" finalmente consegue o resultado do quali. Sai em 0 sem
# fazer nada se não houver mudança (retry idempotente).
#
# Uso: bash .github/scripts/commit-push.sh "mensagem do commit"
set -euo pipefail

MSG="${1:-Etapa 5: atualiza dados via Actions}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add data docs/data

if git diff --cached --quiet; then
  echo "Nada para commitar."
  exit 0
fi

git commit -m "$MSG

Co-Authored-By: github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"

# O verificador pode ficar horas dormindo; nesse meio tempo outro disparo pode
# ter empurrado algo. Rebase antes do push para não bater de frente.
git pull --rebase origin "${GITHUB_REF_NAME:-main}"
git push
