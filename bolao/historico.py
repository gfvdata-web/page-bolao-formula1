"""Etapa 7 — importação de temporadas anteriores (formato planilha).

Os anos antigos do bolão não têm as mensagens brutas do WhatsApp: os palpites
foram registrados numa planilha. Este módulo lê a planilha (já exportada para
CSV e versionada em ``data/<season>/``) e **sintetiza** os arquivos
``data/<season>/messages/<round>.txt`` no mesmo formato que ``bolao.parser``
consome — assim o resto do pipeline (parser → scoring → ``bolao.site``) roda
sem nenhuma adaptação.

Entradas (por temporada, em ``data/<season>/``):

- ``palpites_<season>.csv`` — um palpite por linha:
  ``circuito,nome,p1,p2,p3,p4,p5,p6,pos`` (``pos`` = chute da posição do piloto
  da rodada; a ordem das linhas é preservada como ordem de envio).
- ``rodadas_<season>.csv`` — uma corrida por linha:
  ``circuito,data,quem,pos_planilha,t1..t6`` (``quem`` = piloto da rodada
  sorteado pelo grupo; ``t1..t6``/``pos_planilha`` só servem de conferência).
- ``calendar.json`` + ``results/<round>.json`` + ``drivers.json`` — da Jolpica
  (``python -m bolao.jolpica ... --season <season>``). O ``results`` é a fonte
  canônica do grid; a planilha é só conferida contra ele.

Uso::

    python -m bolao.historico build --season 2025
    python -m bolao.historico build --season 2025 --check-only
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from .calendar import RaceNotFound, load_calendar, resolve_race
from .normalize import normalize_driver, normalize_key, normalize_player
from .site import load_driver_aliases


def _load_json(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _read_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _pos_int(bruto: str) -> int | None:
    digitos = "".join(ch for ch in str(bruto) if ch.isdigit())
    return int(digitos) if digitos else None


def _mensagem_rodada(circuito: str, quem: str, palpites: list[dict]) -> str:
    """Monta o texto no formato de ``bolao.parser`` (cabeçalho + blocos)."""
    linhas = [f"Qualify Bolao {circuito}", f"Piloto {quem}", ""]
    for p in palpites:
        linhas.append(p["nome"])
        for i in range(1, 7):
            linhas.append(p[f"p{i}"])
        pos = _pos_int(p["pos"])
        linhas.append(f"P{pos}" if pos is not None else p["pos"])
        linhas.append("")
    return "\n".join(linhas).rstrip() + "\n"


def build(
    season: int,
    data_dir: str | Path = "data",
    check_only: bool = False,
) -> dict:
    """Sintetiza ``messages/<round>.txt`` da temporada e confere com a Jolpica.

    Devolve um resumo ``{rounds, avisos}``. Com ``check_only`` não grava nada,
    só roda a conferência.
    """
    data_dir = Path(data_dir)
    season_dir = data_dir / str(season)

    calendar = load_calendar(season_dir / "calendar.json")
    drivers = load_driver_aliases(data_dir, season)
    codigos_validos = set(drivers.values())
    players_cfg = _load_json(season_dir / "players.json")
    player_aliases = players_cfg.get("aliases", {})

    palpites = _read_csv(season_dir / f"palpites_{season}.csv")
    rodadas = _read_csv(season_dir / f"rodadas_{season}.csv")

    avisos: list[str] = []

    # circuito bruto -> rodada (via aliases do calendário)
    def _rodada(circuito: str) -> dict:
        try:
            return resolve_race(circuito, calendar)
        except RaceNotFound as exc:
            raise SystemExit(f"[erro] {exc}") from exc

    quem_por_rodada: dict[int, dict] = {}
    for linha in rodadas:
        race = _rodada(linha["circuito"])
        quem_por_rodada[race["round"]] = linha

    # Agrupa palpites por rodada preservando a ordem do CSV.
    palpites_por_rodada: dict[int, list[dict]] = {}
    for linha in palpites:
        race = _rodada(linha["circuito"])
        palpites_por_rodada.setdefault(race["round"], []).append(linha)

    messages_dir = season_dir / "messages"
    rounds_ok: list[int] = []

    for rnd in sorted(palpites_por_rodada):
        race = next(r for r in calendar["races"] if r["round"] == rnd)
        linhas_rodada = quem_por_rodada.get(rnd)
        if linhas_rodada is None:
            avisos.append(f"R{rnd} ({race['race']}): sem piloto da rodada em rodadas_{season}.csv — rodada pulada.")
            continue
        quem = linhas_rodada["quem"]
        palps = palpites_por_rodada[rnd]

        # --- conferência contra o resultado real (Jolpica) ---
        result_path = season_dir / "results" / f"{rnd}.json"
        if result_path.exists():
            order = _load_json(result_path)["order"]
            # top6 da planilha vs Jolpica
            plan_top6 = [str(linhas_rodada[f"t{i}"]).upper() for i in range(1, 7)]
            jol_top6 = [c.upper() for c in order[:6]]
            if plan_top6 != jol_top6:
                avisos.append(
                    f"R{rnd} ({race['race']}): top6 da planilha {plan_top6} "
                    f"difere da Jolpica {jol_top6} (usando Jolpica)."
                )
            # posição real do piloto da rodada
            cod_quem = normalize_driver(quem, drivers)
            pos_jol = order.index(cod_quem) + 1 if cod_quem in order else None
            pos_plan = _pos_int(linhas_rodada.get("pos_planilha", ""))
            if pos_jol != pos_plan:
                avisos.append(
                    f"R{rnd} ({race['race']}): piloto da rodada {cod_quem} — "
                    f"planilha diz P{pos_plan}, Jolpica diz "
                    f"{'P'+str(pos_jol) if pos_jol else 'fora do grid'} (usando Jolpica)."
                )
        else:
            avisos.append(f"R{rnd} ({race['race']}): sem results/{rnd}.json — não consolida ainda.")

        # --- palpites: códigos e jogadores suspeitos ---
        for p in palps:
            for i in range(1, 7):
                bruto = p[f"p{i}"]
                cod = normalize_driver(bruto, drivers)
                if cod not in codigos_validos:
                    avisos.append(
                        f"R{rnd} {p['nome']}: código de piloto desconhecido "
                        f"p{i}={bruto!r} -> {cod} (não está na entry list {season})"
                    )
            t6 = [normalize_driver(p[f"p{i}"], drivers) for i in range(1, 7)]
            if len(set(t6)) != 6:
                avisos.append(f"R{rnd} {p['nome']}: top6 com piloto repetido {t6}")
            pid = normalize_player(p["nome"], player_aliases)
            if normalize_key(p["nome"]) not in player_aliases:
                avisos.append(f"R{rnd}: jogador sem alias em players.json: {p['nome']!r} -> id {pid!r}")

        if not check_only:
            # cabeçalho usa o nome bruto do circuito da planilha (resolve_race
            # já validou que ele casa com esta rodada).
            texto = _mensagem_rodada(linhas_rodada["circuito"], quem, palps)
            messages_dir.mkdir(parents=True, exist_ok=True)
            (messages_dir / f"{rnd}.txt").write_text(texto, encoding="utf-8")
        rounds_ok.append(rnd)

    return {"rounds": rounds_ok, "avisos": avisos}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bolão F1 — importar histórico (Etapa 7)")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="sintetiza messages/<round>.txt da planilha")
    b.add_argument("--season", type=int, required=True)
    b.add_argument("--data", default="data")
    b.add_argument("--check-only", action="store_true", help="só confere, não grava")
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    resumo = build(args.season, data_dir=args.data, check_only=args.check_only)
    acao = "Conferidas" if args.check_only else "Sintetizadas"
    print(f"{acao} {len(resumo['rounds'])} rodada(s): {resumo['rounds']}")
    if resumo["avisos"]:
        print(f"\n{len(resumo['avisos'])} aviso(s) de conferência:")
        for a in resumo["avisos"]:
            print(f"  - {a}")
    else:
        print("Sem avisos de conferência.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
