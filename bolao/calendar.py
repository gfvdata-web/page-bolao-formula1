"""Resolução do nome bruto da corrida (cabeçalho do WhatsApp) -> rodada/race_id.

O cabeçalho da mensagem traz a corrida por um nome solto (ex.: ``"Silverstone"``,
``"Monaco"``, ``"Interlagos"``). Esta camada — offline, sem rede — casa esse nome
com o `calendar.json` gerado por `bolao.jolpica` usando os **aliases normalizados**
de cada corrida (circuito, cidade, país, nome oficial).

Uso típico (junto do parser da Etapa 1)::

    from bolao.parser import parse_sheet
    from bolao.calendar import load_calendar, resolve_race

    sheet = parse_sheet(texto, drivers, players)
    corrida = resolve_race(sheet.race, load_calendar("data/2026/calendar.json"))
    corrida["round"], corrida["race_id"]
"""

import json
from pathlib import Path

from .normalize import normalize_key


class RaceNotFound(ValueError):
    """Nenhuma corrida do calendário casou com o nome bruto."""


class AmbiguousRace(ValueError):
    """O nome bruto casou com mais de uma corrida (precisa ser mais específico)."""


def load_calendar(caminho: str | Path) -> dict:
    """Carrega o `calendar.json` gerado por `bolao.jolpica`."""
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def resolve_race(bruto: str, calendar: dict) -> dict:
    """Devolve a entrada de corrida do calendário que casa com ``bruto``.

    Casa por alias normalizado exato. Levanta `RaceNotFound` se nada casar e
    `AmbiguousRace` se um mesmo nome servir a mais de uma corrida (ex.: o país
    "Spain", que em 2026 vale para Barcelona e Madrid) — nesses casos o nome
    precisa ser mais específico (a cidade/circuito).
    """
    chave = normalize_key(bruto)
    if not chave:
        raise RaceNotFound("Nome de corrida vazio.")

    casadas = [r for r in calendar.get("races", []) if chave in r.get("aliases", [])]
    if not casadas:
        raise RaceNotFound(f"Corrida não encontrada no calendário: {bruto!r}")
    if len(casadas) > 1:
        rounds = ", ".join(str(r["round"]) for r in casadas)
        raise AmbiguousRace(
            f"Nome {bruto!r} casa com várias corridas (rodadas {rounds}); "
            "use um nome mais específico (cidade/circuito)."
        )
    return casadas[0]
