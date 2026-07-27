#!/usr/bin/env bash
# Traduz o resultado da CLI do pipeline para variáveis do workflow.
#
# Uso: bash .github/scripts/registra-estado.sh <codigo-de-saida> <resumo-json>
#
# Publica em $GITHUB_ENV:
#   RODADA   — a rodada que o pipeline processou (resolvida pelo cabeçalho se
#              não veio no payload do Forms)
#   PENDENTE — "1" se a rodada ficou sem resultado (liga o verificador), "0" se
#              já foi pontuada
#
# Erro de verdade (parse, corrida não resolvida, rede) derruba o job aqui.
set -euo pipefail

CODIGO="$1"
RESUMO="${2:-}"

# 0 = pontuada, 2 = quali ainda não publicado (ver bolao/pipeline.py).
if [ "$CODIGO" -ne 0 ] && [ "$CODIGO" -ne 2 ]; then
  exit "$CODIGO"
fi

RODADA=$(printf '%s' "$RESUMO" | python -c "import json,sys; print(json.load(sys.stdin)['round'])")

echo "RODADA=$RODADA" >> "$GITHUB_ENV"
if [ "$CODIGO" -eq 2 ]; then
  echo "PENDENTE=1" >> "$GITHUB_ENV"
else
  echo "PENDENTE=0" >> "$GITHUB_ENV"
fi
