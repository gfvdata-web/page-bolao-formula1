"""Etapa 3 — consolidação das pontuações nos dados do site.

Junta as três camadas anteriores (mensagens do WhatsApp + calendário/resultados
da Jolpica + núcleo de parsing/pontuação) e produz:

- ``data/2026/scores/<round>.json`` — pontuação por jogador de cada rodada
  (camada intermediária, seção 6 do CONTEXTO; boa para depurar rodada a rodada).
- ``docs/data/standings.json`` — ranking acumulado da temporada.
- ``docs/data/bets.json`` — histórico de palpites por jogador (detalhe completo).
- ``docs/data/results.json`` — grid real por rodada (histórico de posições).
- ``docs/data/calendar.json`` — calendário completo da temporada (cópia enxuta
  de ``data/<season>/calendar.json``, para os cards de última/próxima corrida).

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
from .formats import season_format
from .normalize import normalize_key
from .parser import parse_sheet
from .scoring import PlayerScore, Result, score_sheet

# Temporada corrente do projeto (a que o site abre por padrão). As temporadas
# anteriores são acessadas via ?ano=YYYY e entram em "modo histórico".
TEMPORADA_ATUAL = 2026


def _load_json(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _dump_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_driver_aliases(data_dir: str | Path, season: int) -> dict:
    """Mapa de apelidos de piloto para a temporada.

    ``data/drivers.json`` é a camada base (apelidos manuais e grafias — ex.
    ``max``→VER, ``kimi``→ANT). ``data/<season>/drivers.json``, quando existe
    (gerado da entry list real daquele ano pela Jolpica), é sobreposto por cima
    — assim cada temporada usa a sua grade sem perder os apelidos manuais.
    """
    data_dir = Path(data_dir)
    aliases = dict(_load_json(data_dir / "drivers.json")["aliases"])
    season_file = data_dir / str(season) / "drivers.json"
    if season_file.exists():
        aliases.update(_load_json(season_file)["aliases"])
    return aliases


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
        # Presente só quando o placar publicado pelo grupo diverge da regra da
        # temporada — o site pode mostrar a diferença em vez de escondê-la.
        "total_recalculado": s.total_recalculado,
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
    docs_data = docs_dir / "data" / str(season)

    fmt = season_format(season)
    drivers = load_driver_aliases(data_dir, season)
    players_cfg = _load_json(season_dir / "players.json")
    player_aliases = players_cfg.get("aliases", {})
    names = _NameResolver(players_cfg.get("names", {}))
    calendar = load_calendar(season_dir / "calendar.json")

    messages_dir = season_dir / "messages"
    results_dir = season_dir / "results"

    # O placar que o grupo publicou manda sobre a recalculação (decisão do
    # usuário): ele é o registro da temporada, seja qual for a conta que o
    # grupo fez na época. A recalculação preenche as rodadas sem placar.
    placar_path = season_dir / "placar_publicado.json"
    placar_pub = (
        _load_json(placar_path).get("rounds", {}) if placar_path.exists() else {}
    )

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
        sheet = parse_sheet(
            texto, drivers, player_aliases, top_n=fmt.top_n, bonus=fmt.bonus
        )
        race = resolve_race(sheet.race, calendar)
        if race["round"] != rnd:
            raise ValueError(
                f"messages/{rnd}.txt resolve para a rodada {race['round']} "
                f"({race['race']}); confira o cabeçalho ou o nome do arquivo."
            )
        result = Result.from_dict(_load_json(results_dir / f"{rnd}.json"))
        scores = score_sheet(sheet, result, fmt.bonus_points)

        publicado = placar_pub.get(str(rnd), {}).get("players", {})
        for s in scores:
            if s.player_id in publicado:
                s.total_recalculado = s.total
                s.total = publicado[s.player_id]
        scores.sort(key=lambda s: (-s.total, s.player_id))

        for s in scores:
            names.observe(s.player_id, s.player_raw)

        # Pontuação mínima da rodada: 1 a menos que a menor pontuação
        # registrada por quem apostou (compensação de quem não apostou).
        min_score = min(s.total for s in scores) - 1 if scores else 0

        # Ordem de envio dos palpites no texto do WhatsApp (antes do score_sheet
        # reordenar por pontuação) — usada pelo site pra gerar o texto de
        # "pontuação da corrida" na mesma ordem que os palpites chegaram.
        bet_order = [bet.player_id for bet in sheet.bets]

        round_infos.append(
            {
                **_round_meta(race),
                "bonus_driver": sheet.bonus_driver,
                "min_score": min_score,
                "bet_order": bet_order,
            }
        )
        round_scores[rnd] = scores
        round_bonus[rnd] = sheet.bonus_driver
        round_order[rnd] = result.order
        round_min_score[rnd] = min_score

    # Jogadores do ranking = todo mundo que apostou em pelo menos uma rodada
    # da temporada. Quem não aposta numa rodada recebe a pontuação mínima
    # daquela rodada (compensação), mas isso não conta como rodada apostada.
    ranking_players = {s.player_id for scores in round_scores.values() for s in scores}

    # Saldo inicial (Etapa 7): rodadas anteriores às que temos palpite, cujo
    # placar só sobrevive nos rankings que o grupo publicou no WhatsApp
    # (2021 começa na rodada 11 aqui, mas o bolão rodou o ano inteiro). Entra
    # como um bloco de pontos + rodadas jogadas, sem detalhe por corrida.
    saldo_path = season_dir / "saldo_inicial.json"
    saldo = _load_json(saldo_path).get("players", {}) if saldo_path.exists() else {}
    ranking_players |= set(saldo)

    # Rodadas que existem só como PLACAR publicado no grupo: sabemos quanto
    # cada jogador fez, mas não de quais pilotos veio. Contam no total e como
    # rodada disputada; o site sinaliza que não há palpite para mostrar.
    avulsos_path = season_dir / "pontos_avulsos.json"
    # Entram no ranking só com "incluir_no_ranking": true — a inclusão muda o
    # campeonato (em 2025 a R19 empata o 1º lugar), então é decisão explícita,
    # nunca efeito colateral de o arquivo existir.
    avulsos = {}
    if avulsos_path.exists():
        bruto = _load_json(avulsos_path)
        if bruto.get("incluir_no_ranking"):
            avulsos = bruto.get("rounds", {})
    for bloco in avulsos.values():
        ranking_players |= set(bloco.get("players", {}))

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
        if fmt.compensation:
            for pid in ranking_players - apostaram:
                ac = acumulado[pid]
                ac["total"] += round_min_score[rnd]
                ac["compensation_total"] += round_min_score[rnd]
                ac["compensated_rounds"].append(rnd)

    for chave_rnd, bloco in avulsos.items():
        rnd_av = int(chave_rnd)
        cobertas = bloco.get("covers") or [rnd_av]
        for pid, pontos in bloco.get("players", {}).items():
            ac = acumulado[pid]
            ac["total"] += pontos
            ac["per_round"][str(rnd_av)] = pontos
            ac.setdefault("rounds_sem_palpite", []).extend(cobertas)
            ac["avulsos_points"] = ac.get("avulsos_points", 0) + pontos
            # Um bloco pode cobrir mais de uma corrida (ex.: 2022 R4+R5, que só
            # dá para separar do acumulado como um bloco só).
            ac["avulsos_extra_rounds"] = ac.get("avulsos_extra_rounds", 0) + len(cobertas) - 1

    for pid, bloco in saldo.items():
        ac = acumulado[pid]
        ac["carry_points"] = int(bloco.get("pontos", 0))
        ac["carry_rounds"] = int(bloco.get("rodadas", 0))
        ac["total"] += ac["carry_points"]

    def _media(ac: dict) -> float:
        rodadas = len(ac["per_round"]) + ac.get("carry_rounds", 0)
        pontos = ac["top6_total"] + ac["bonus_total"] + ac.get("carry_points", 0)
        return pontos / rodadas if rodadas else 0.0

    # Desempate: por padrão só a ordem estável do id (o critério "de verdade"
    # nunca foi definido para 2026 — ver seção 9). 2021 desempatava por média.
    if fmt.tiebreak == "media":
        chave = lambda a: (-a["total"], -_media(a), a["player_id"])
    else:
        chave = lambda a: (-a["total"], a["player_id"])
    # Ranking final publicado pelo grupo: `pontos` substitui o total somado e
    # `ordem` fixa a classificação oficial (inclusive o desempate, que o grupo
    # resolvia por critério interno não registrado). Ver data/<ano>/.
    final_path = season_dir / "ranking_final.json"
    final = _load_json(final_path) if final_path.exists() else {}
    pontos_oficiais = final.get("pontos", {})
    ordem_oficial = final.get("ordem", [])
    for pid, pontos in pontos_oficiais.items():
        if pid in acumulado:
            acumulado[pid]["total_somado"] = acumulado[pid]["total"]
            acumulado[pid]["total"] = pontos

    ordenados = sorted(acumulado.values(), key=chave)
    if ordem_oficial:
        posicao = {pid: i for i, pid in enumerate(ordem_oficial)}
        ordenados.sort(key=lambda a: (posicao.get(a["player_id"], len(posicao)),))
    standings_players = []
    for pos, ac in enumerate(ordenados, 1):
        carry_pts = ac.get("carry_points", 0)
        carry_rnd = ac.get("carry_rounds", 0)
        rounds_played = (
            len(ac["per_round"]) + carry_rnd + ac.get("avulsos_extra_rounds", 0)
        )
        # Média por corrida: os mesmos pontos que aparecem na coluna "Pontos"
        # (o total oficial da temporada), menos a pontuação mínima de
        # compensação (que não foi de fato apostada), divididos pelas rodadas
        # realmente apostadas. Usar o `total` — e não o recálculo top6+bônus —
        # garante que dois jogadores com o mesmo total mostrem a mesma média
        # (o placar publicado pode divergir do recálculo rodada a rodada).
        pontos_avaliados = ac["total"] - ac["compensation_total"]
        avg_points = round(pontos_avaliados / rounds_played, 1) if rounds_played else 0.0
        # Total pelo nosso motor de pontuação, ignorando as correções do grupo
        # (`placar_publicado.json` rodada a rodada e `ranking_final.pontos` no
        # fechamento). `top6_total`/`bonus_total` já são sempre o recálculo.
        total_calculado = (
            ac["top6_total"]
            + ac["bonus_total"]
            + carry_pts
            + ac.get("avulsos_points", 0)
            + ac["compensation_total"]
        )
        standings_players.append(
            {
                "position": pos,
                "player_id": ac["player_id"],
                "name": names.resolve(ac["player_id"]),
                "total": ac["total"],
                "total_calculado": total_calculado,
                "top6_total": ac["top6_total"],
                "bonus_total": ac["bonus_total"],
                "carry_points": carry_pts,
                "carry_rounds": carry_rnd,
                "avulsos_points": ac.get("avulsos_points", 0),
                "total_somado": ac.get("total_somado", ac["total"]),
                "rounds_sem_palpite": sorted(set(ac.get("rounds_sem_palpite", []))),
                "rounds_played": rounds_played,
                "avg_points": avg_points,
                "per_round": ac["per_round"],
                "compensated_rounds": sorted(ac["compensated_rounds"]),
                "compensation_total": ac["compensation_total"],
            }
        )
    # Formato da temporada (top_n / piloto da rodada / compensação) — o
    # front-end lê isto para adaptar as visualizações (2021 = top5 sem bônus,
    # 2024 = bônus vale 2, etc.).
    fmt_doc = {
        "top_n": fmt.top_n,
        "bonus": fmt.bonus,
        "bonus_points": fmt.bonus_points if fmt.bonus else 0,
        "compensation": fmt.compensation,
        "max_points": fmt.max_points,
    }

    # Cobertura da temporada: o que falta para o site avisar numa faixa quando
    # uma temporada antiga está incompleta.
    consolidadas = {info["round"] for info in round_infos}
    nome_por_rodada = {r["round"]: r["race"] for r in calendar["races"]}
    # Fins de semana de Sprint contam (o quali principal vale) — ver CONTEXTO.
    total_rodadas = len(calendar["races"])
    carry_ate = int(_load_json(saldo_path).get("ate_rodada", 0)) if saldo_path.exists() else 0
    faltando: list[str] = []
    if carry_ate:
        faltando.append(
            f"Rodadas 1–{carry_ate}: só o saldo acumulado, sem detalhe por corrida"
        )
    if consolidadas:
        ultima = max(consolidadas)
        for r in sorted(nome_por_rodada):
            if carry_ate < r < ultima and r not in consolidadas:
                faltando.append(f"Rodada {r} ({nome_por_rodada[r]}): sem palpites recuperados")
    if avulsos_path.exists():
        bruto_av = _load_json(avulsos_path)
        if not bruto_av.get("incluir_no_ranking"):
            for rstr in sorted(bruto_av.get("rounds", {}), key=int):
                nome = nome_por_rodada.get(int(rstr), f"R{rstr}")
                faltando.append(
                    f"Rodada {rstr} ({nome}): placar publicado, ainda fora do ranking"
                )
    meta_doc = {
        "rodadas": len(consolidadas),
        "rodadas_totais": total_rodadas,
        "parcial": bool(faltando),
        "faltando": faltando,
    }

    standings = {
        "season": season,
        "format": fmt_doc,
        "meta": meta_doc,
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

    # --- docs/data/calendar.json (calendário completo, p/ cards de rodada) ---
    calendar_doc = {
        "season": season,
        "races": [
            {
                "round": race["round"],
                "race_id": race["race_id"],
                "race": race["race"],
                "circuit": race["circuit"],
                "date": race.get("date"),
                "qualifying_utc": race.get("qualifying_utc"),
                "sprint": race.get("sprint", False),
            }
            for race in calendar["races"]
        ],
    }
    _dump_json(docs_data / "calendar.json", calendar_doc)

    # --- docs/data/seasons.json (índice das temporadas disponíveis) ---
    # Varre as pastas irmãs com standings.json — assim gerar uma temporada não
    # apaga as outras do índice. O seletor de temporada do site lê este arquivo.
    entradas = []
    for p in (docs_dir / "data").glob("*/standings.json"):
        if not p.parent.name.isdigit():
            continue
        st = _load_json(p)
        entradas.append(
            {
                "ano": int(p.parent.name),
                "format": st.get("format", {}),
                **st.get("meta", {}),
            }
        )
    entradas.sort(key=lambda e: e["ano"], reverse=True)
    _dump_json(
        docs_dir / "data" / "seasons.json",
        {"atual": TEMPORADA_ATUAL, "temporadas": entradas},
    )

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
