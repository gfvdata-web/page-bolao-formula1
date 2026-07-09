"""CLI da Etapa 5: pipeline completo acionado pelo GitHub Actions.

Uso:
    python -m bolao.pipeline run --round 10 < mensagem.txt
    python -m bolao.pipeline run < mensagem.txt      # rodada resolvida pelo cabeçalho
    python -m bolao.pipeline retry 10                # re-tenta buscar resultado + gera site

Fluxo (repository_dispatch -> Actions), um comando só (`run`):
    1. grava data/<season>/messages/<round>.txt com o texto recebido
    2. busca o resultado do quali na Jolpica-F1 (pula, sem falhar, se ainda
       estiver indisponível — ver `retry`)
    3. regenera os dados do site (docs/data/*.json)
"""

import argparse
import json
import sys
from pathlib import Path

from .calendar import AmbiguousRace, RaceNotFound, load_calendar, resolve_race
from .jolpica import JolpicaError, ResultUnavailable, fetch_result
from .parser import ParseError, parse_sheet
from .site import generate


def _load_aliases(caminho: Path) -> dict:
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8")).get("aliases", {})


def _write_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def resolve_round(texto: str, data_dir: Path, season: int) -> int:
    """Descobre a rodada a partir do cabeçalho da mensagem (sem tocar rede)."""
    drivers = _load_aliases(data_dir / "drivers.json")
    players = _load_aliases(data_dir / str(season) / "players.json")
    sheet = parse_sheet(texto, drivers, players)
    calendar = load_calendar(data_dir / str(season) / "calendar.json")
    race = resolve_race(sheet.race, calendar)
    return race["round"]


def fetch_result_if_missing(round_: int, season: int, data_dir: Path) -> str:
    """Busca o resultado na Jolpica se ainda não existir. Devolve o status."""
    destino = data_dir / str(season) / "results" / f"{round_}.json"
    if destino.exists():
        return "ja_existia"
    try:
        dados = fetch_result(round_, season)
    except ResultUnavailable:
        return "indisponivel"
    _write_json(destino, dados)
    return "gravado"


def run(
    texto: str,
    round_: int | None,
    season: int = 2026,
    data_dir: str | Path = "data",
    docs_dir: str | Path = "docs",
) -> dict:
    data_dir = Path(data_dir)
    if round_ is None:
        round_ = resolve_round(texto, data_dir, season)

    msg_path = data_dir / str(season) / "messages" / f"{round_}.txt"
    msg_path.parent.mkdir(parents=True, exist_ok=True)
    msg_path.write_text(texto, encoding="utf-8")

    status_resultado = fetch_result_if_missing(round_, season, data_dir)
    resumo_site = generate(data_dir, docs_dir, season)
    return {"round": round_, "resultado": status_resultado, "site": resumo_site}


def retry(
    round_: int,
    season: int = 2026,
    data_dir: str | Path = "data",
    docs_dir: str | Path = "docs",
) -> dict:
    """Re-tenta buscar o resultado de uma rodada cuja mensagem já foi gravada."""
    data_dir = Path(data_dir)
    msg_path = data_dir / str(season) / "messages" / f"{round_}.txt"
    if not msg_path.exists():
        raise FileNotFoundError(
            f"Rodada {round_} ainda não tem mensagem gravada ({msg_path})."
        )
    status_resultado = fetch_result_if_missing(round_, season, data_dir)
    resumo_site = generate(data_dir, docs_dir, season)
    return {"round": round_, "resultado": status_resultado, "site": resumo_site}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bolão F1 — pipeline completo (Etapa 5)")
    p.add_argument("--season", type=int, default=2026)
    p.add_argument("--data", default="data")
    p.add_argument("--docs", default="docs")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_run = sub.add_parser("run", help="grava o palpite recebido e roda o pipeline")
    sp_run.add_argument("--round", type=int, default=None, help="omitir para resolver pelo cabeçalho")
    sp_run.add_argument("--texto-file", help="arquivo com o texto (padrão: stdin)")

    sp_retry = sub.add_parser(
        "retry", help="re-tenta buscar resultado de uma rodada já gravada"
    )
    sp_retry.add_argument("round", type=int)

    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.cmd == "run":
            if args.texto_file:
                texto = Path(args.texto_file).read_text(encoding="utf-8")
            else:
                texto = sys.stdin.read()
            resumo = run(texto, args.round, args.season, args.data, args.docs)
        else:
            resumo = retry(args.round, args.season, args.data, args.docs)
    except (ParseError, RaceNotFound, AmbiguousRace, JolpicaError, FileNotFoundError) as exc:
        print(f"[erro] {exc}", file=sys.stderr)
        return 1

    print(f"Rodada {resumo['round']}: resultado {resumo['resultado']}.")
    if resumo["resultado"] == "indisponivel":
        print(
            "Quali ainda sem resultado na Jolpica — re-rode depois com "
            f"`python -m bolao.pipeline retry {resumo['round']}`."
        )
    print(f"Site regenerado ({len(resumo['site']['rounds'])} rodadas consolidadas).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
