"""Etapa 3 — consolidação das pontuações nos dados do site.

Junta as três camadas anteriores (mensagens do WhatsApp + calendário/resultados
da Jolpica + núcleo de parsing/pontuação) e produz:

- ``data/2026/scores/<round>.json`` — pontuação por jogador de cada rodada
  (camada intermediária, seção 6 do CONTEXTO; boa para depurar rodada a rodada).
- ``docs/data/standings.json`` — ranking acumulado da temporada.
- ``docs/data/bets.json`` — histórico de palpites por jogador (detalhe completo).
- ``docs/data/results.json`` — grid real por rodada (histórico de posições).

Uma rodada entra na consolidação quando existem **os dois** arquivos:
``messages/<round>.txt`` (palpites) e ``results/<round>.json`` (quali). Rodadas
sem um dos dois são ignoradas (ainda não ocorreram ou faltam palpites).

O nome de exibição do jogador vem de ``players.json`` (bloco ``names``); sem
entrada lá, usa-se a variante mais completa do nome vista nas mensagens.

Uso::

    python -m bolao.site build
    python -m bolao.site build --season 2026 --data data --docs docs
"""

import argparse
import json
import sys
from pathlib import Path

from .calendar import load_calendar, resolve_race
from .normalize import normalize_key
from .parser import parse_sheet
from .scoring import PlayerScore, Result, score_sheet


def _load_json(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _dump_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _detail_to_dict(item) -> dict:
    return {
        "pos": item.pos,
        "guess": item.guess,
        "real": item.real,
        "points": item.points,
        "reason": item.reason,
    }


def _score_to_dict(s: PlayerScore, name: str) -> dict:
    """Serializa um :class:`PlayerScore` (com o nome de exibição resolvido)."""
    return {
        "player_id": s.player_id,
        "player_raw": s.player_raw,
        "name": name,
        "top6": [item.guess for item in s.top6_detail],
        "top6_detail": [_detail_to_dict(item) for item in s.top6_detail],
        "top6_points": s.top6_points,
        "bonus_guess": s.bonus_guess,
        "bonus_real_pos": s.bonus_real_pos,
        "bonus_points": s.bonus_points,
        "total": s.total,
    }


def _completeness(raw: str) -> tuple[int, int]:
    """Chave para escolher a variante 'mais completa' de um nome bruto."""
    return (len(normalize_key(raw).replace(" ", "")), len(raw))


class _NameResolver:
    """Resolve o nome de exibição: override em players.json ou melhor bruto."""

    def __init__(self, names: dict):
        self._names = names
        self._seen: dict[str, str] = {}

    def observe(self, player_id: str, raw: str) -> None:
        atual = self._seen.get(player_id)
        if atual is None or _completeness(raw) > _completeness(atual):
            self._seen[player_id] = raw

    def resolve(self, player_id: str) -> str:
        if player_id in self._names:
            return self._names[player_id]
        return self._seen.get(player_id, player_id)


def _round_meta(race: dict) -> dict:
    """Metadados enxutos da corrida usados em todos os arquivos do site."""
    return {
        "round": race["round"],
        "race_id": race["race_id"],
        "race": race["race"],
        "circuit": race["circuit"],
        "date": race.get("date"),
        "sprint": race.get("sprint", False),
    }


def generate(
    data_dir: str | Path = "data",
    docs_dir: str | Path = "docs",
    season: int = 2026,
) -> dict:
    """Gera os arquivos intermediários e os dados do site. Devolve um resumo."""
    data_dir = Path(data_dir)
    docs_dir = Path(docs_dir)
    season_dir = data_dir / str(season)
    docs_data = docs_dir / "data"

    drivers = _load_json(data_dir / "drivers.json")["aliases"]
    players_cfg = _load_json(season_dir / "players.json")
    player_aliases = players_cfg.get("aliases", {})
    names = _NameResolver(players_cfg.get("names", {}))
    calendar = load_calendar(season_dir / "calendar.json")

    messages_dir = season_dir / "messages"
    results_dir = season_dir / "results"

    # Rodadas com mensagem + resultado, em ordem crescente de rodada.
    rounds: list[int] = sorted(
        int(p.stem)
        for p in messages_dir.glob("*.txt")
        if p.stem.isdigit() and (results_dir / f"{p.stem}.json").exists()
    )

    round_infos: list[dict] = []  # meta por rodada, ordenado
    round_scores: dict[int, list[PlayerScore]] = {}
    round_bonus: dict[int, str] = {}
    round_order: dict[int, list[str]] = {}
    round_min_score: dict[int, int] = {}

    for rnd in rounds:
        texto = (messages_dir / f"{rnd}.txt").read_text(encoding="utf-8")
        sheet = parse_sheet(texto, drivers, player_aliases)
        race = resolve_race(sheet.race, calendar)
        if race["round"] != rnd:
            raise ValueError(
                f"messages/{rnd}.txt resolve para a rodada {race['round']} "
                f"({race['race']}); confira o cabeçalho ou o nome do arquivo."
            )
        result = Result.from_dict(_load_json(results_dir / f"{rnd}.json"))
        scores = score_sheet(sheet, result)

        for s in scores:
            names.observe(s.player_id, s.player_raw)

        # Pontuação mínima da rodada: 1 a menos que a menor pontuação
        # registrada por quem apostou (compensação de quem não apostou).
        min_score = min(s.total for s in scores) - 1 if scores else 0

        round_infos.append(
            {**_round_meta(race), "bonus_driver": sheet.bonus_driver, "min_score": min_score}
        )
        round_scores[rnd] = scores
        round_bonus[rnd] = sheet.bonus_driver
        round_order[rnd] = result.order
        round_min_score[rnd] = min_score

    # Jogadores do ranking = todo mundo que apostou em pelo menos uma rodada
    # da temporada. Quem não aposta numa rodada recebe a pontuação mínima
    # daquela rodada (compensação), mas isso não conta como rodada apostada.
    ranking_players = {s.player_id for scores in round_scores.values() for s in scores}

    # --- data/2026/scores/<round>.json (intermediário) ---
    for info in round_infos:
        rnd = info["round"]
        conteudo = {
            **info,
            "result_order": round_order[rnd],
            "players": [
                _score_to_dict(s, names.resolve(s.player_id))
                for s in round_scores[rnd]
            ],
        }
        _dump_json(season_dir / "scores" / f"{rnd}.json", conteudo)

    # --- docs/data/standings.json (ranking acumulado) ---
    acumulado: dict[str, dict] = {
        pid: {
            "player_id": pid,
            "total": 0,
            "top6_total": 0,
            "bonus_total": 0,
            "per_round": {},
            "compensated_rounds": [],
            "compensation_total": 0,
        }
        for pid in ranking_players
    }
    for info in round_infos:
        rnd = info["round"]
        apostaram = {s.player_id for s in round_scores[rnd]}
        for s in round_scores[rnd]:
            ac = acumulado[s.player_id]
            ac["total"] += s.total
            ac["top6_total"] += s.top6_points
            ac["bonus_total"] += s.bonus_points
            ac["per_round"][str(rnd)] = s.total
        for pid in ranking_players - apostaram:
            ac = acumulado[pid]
            ac["total"] += round_min_score[rnd]
            ac["compensation_total"] += round_min_score[rnd]
            ac["compensated_rounds"].append(rnd)

    ordenados = sorted(
        acumulado.values(), key=lambda a: (-a["total"], a["player_id"])
    )
    standings_players = []
    for pos, ac in enumerate(ordenados, 1):
        rounds_played = len(ac["per_round"])
        # Média por corrida: só considera o que foi de fato apostado, sem
        # contar a pontuação mínima de compensação.
        pontos_apostados = ac["top6_total"] + ac["bonus_total"]
        avg_points = round(pontos_apostados / rounds_played, 1) if rounds_played else 0.0
        standings_players.append(
            {
                "position": pos,
                "player_id": ac["player_id"],
                "name": names.resolve(ac["player_id"]),
                "total": ac["total"],
                "top6_total": ac["top6_total"],
                "bonus_total": ac["bonus_total"],
                "rounds_played": rounds_played,
                "avg_points": avg_points,
                "per_round": ac["per_round"],
                "compensated_rounds": sorted(ac["compensated_rounds"]),
                "compensation_total": ac["compensation_total"],
            }
        )
    standings = {
        "season": season,
        "rounds": round_infos,
        "players": standings_players,
    }
    _dump_json(docs_data / "standings.json", standings)

    # --- docs/data/bets.json (histórico de palpites por jogador) ---
    bets_players: dict[str, dict] = {}
    for info in round_infos:
        rnd = info["round"]
        for s in round_scores[rnd]:
            jogador = bets_players.setdefault(
                s.player_id,
                {
                    "player_id": s.player_id,
                    "name": names.resolve(s.player_id),
                    "rounds": {},
                },
            )
            jogador["rounds"][str(rnd)] = {
                "round": rnd,
                "race_id": info["race_id"],
                "race": info["race"],
                "top6": [item.guess for item in s.top6_detail],
                "top6_detail": [_detail_to_dict(item) for item in s.top6_detail],
                "top6_points": s.top6_points,
                "bonus_driver": round_bonus[rnd],
                "bonus_guess": s.bonus_guess,
                "bonus_real_pos": s.bonus_real_pos,
                "bonus_points": s.bonus_points,
                "total": s.total,
            }
    bets = {
        "season": season,
        "players": {pid: bets_players[pid] for pid in sorted(bets_players)},
    }
    _dump_json(docs_data / "bets.json", bets)

    # --- docs/data/results.json (grid real por rodada) ---
    results_doc = {
        "season": season,
        "rounds": {
            str(info["round"]): {
                **info,
                "order": round_order[info["round"]],
            }
            for info in round_infos
        },
    }
    _dump_json(docs_data / "results.json", results_doc)

    return {
        "rounds": [info["round"] for info in round_infos],
        "players": len(standings_players),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bolão F1 — dados do site (Etapa 3)")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="gera scores/, standings.json e docs/data/")
    b.add_argument("--season", type=int, default=2026)
    b.add_argument("--data", default="data")
    b.add_argument("--docs", default="docs")
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    resumo = generate(data_dir=args.data, docs_dir=args.docs, season=args.season)
    print(
        f"Consolidado: {len(resumo['rounds'])} rodada(s) "
        f"{resumo['rounds']} | {resumo['players']} jogadores."
    )
    print(f"  data/{args.season}/scores/<round>.json")
    print("  docs/data/standings.json, bets.json, results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
