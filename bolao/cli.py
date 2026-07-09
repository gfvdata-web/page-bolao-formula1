"""CLI da Etapa 1: parseia uma mensagem e imprime a pontuação por jogador.

Uso:
    python -m bolao.cli data/2026/messages/9.txt data/2026/results/9.json

Opcionais:
    --drivers data/drivers.json
    --players data/2026/players.json
    --detalhe   (mostra o detalhamento posição a posição)
"""

import argparse
import json
import sys
from pathlib import Path

from .parser import parse_sheet
from .scoring import Result, score_sheet


def _load_aliases(caminho: str | None) -> dict:
    if not caminho:
        return {}
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return dados.get("aliases", dados)


def _print_ranking(sheet, scores) -> None:
    print(f"Corrida: {sheet.race}  |  Piloto da rodada: {sheet.bonus_driver}")
    print("-" * 52)
    print(f"{'#':>2}  {'Jogador':<16}{'top6':>6}{'bonus':>7}{'total':>7}")
    print("-" * 52)
    for i, s in enumerate(scores, 1):
        print(
            f"{i:>2}  {s.player_raw:<16}{s.top6_points:>6}{s.bonus_points:>7}{s.total:>7}"
        )


def _print_detalhe(sheet, scores) -> None:
    for s in scores:
        print()
        print(f"== {s.player_raw}  (total {s.total})")
        for item in s.top6_detail:
            marca = {2: "++", 1: "+", 0: " "}[item.points]
            print(
                f"   P{item.pos}  apostou {item.guess:<4} real {item.real or '--':<4}"
                f" {item.points} pt {marca}  ({item.reason})"
            )
        pos = s.bonus_real_pos if s.bonus_real_pos is not None else "--"
        print(
            f"   bônus {sheet.bonus_driver}: chutou P{s.bonus_guess}, real P{pos}"
            f"  {s.bonus_points} pt"
        )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bolão F1 — pontuação (Etapa 1)")
    p.add_argument("mensagem", help="arquivo .txt com a mensagem do WhatsApp")
    p.add_argument("resultado", help="arquivo .json com o resultado do quali")
    p.add_argument("--drivers", default="data/drivers.json")
    p.add_argument("--players", default="data/2026/players.json")
    p.add_argument("--detalhe", action="store_true", help="mostra detalhamento")
    args = p.parse_args(argv)

    # Saída em UTF-8 (nomes com acento) mesmo em terminal Windows cp1252.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    driver_aliases = _load_aliases(args.drivers)
    player_aliases = _load_aliases(args.players)

    texto = Path(args.mensagem).read_text(encoding="utf-8")
    sheet = parse_sheet(texto, driver_aliases, player_aliases)

    dados_result = json.loads(Path(args.resultado).read_text(encoding="utf-8"))
    result = Result.from_dict(dados_result)

    scores = score_sheet(sheet, result)
    _print_ranking(sheet, scores)
    if args.detalhe:
        _print_detalhe(sheet, scores)
    return 0


if __name__ == "__main__":
    sys.exit(main())
