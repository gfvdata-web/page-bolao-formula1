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


# Palavras genéricas que não distinguem uma corrida de outra.
_GENERICOS = {"grand", "prix", "gp"}


def _palavras(textos: list[str]) -> set[str]:
    """Conjunto de palavras (sem os genéricos) de uma lista de aliases."""
    palavras: set[str] = set()
    for t in textos:
        palavras.update(normalize_key(t).split())
    return palavras - _GENERICOS


def resolve_race(bruto: str, calendar: dict) -> dict:
    """Devolve a entrada de corrida do calendário que casa com ``bruto``.

    Casa por **palavras em comum** entre o nome bruto e os aliases da corrida
    (circuito, cidade, país, nome oficial). Vence a corrida com mais palavras
    casadas — assim, quando há mais de uma corrida no mesmo país, basta o
    cabeçalho trazer também a cidade para desambiguar (ex.: ``"Espanha Madrid"``
    → Madrid; ``"Espanha Barcelona"`` → Barcelona).

    Levanta `RaceNotFound` se nada casar e `AmbiguousRace` num empate — ex.: só
    o país ``"Spain"`` (vale para Barcelona r7 e Madrid r14 em 2026), ou só
    ``"USA"`` (Miami/Austin/Las Vegas): aí é preciso colocar as duas informações.
    """
    header = _palavras([bruto])
    if not header:
        raise RaceNotFound("Nome de corrida vazio.")

    melhores: list[dict] = []
    melhor_score = 0
    for r in calendar.get("races", []):
        score = len(header & _palavras(r.get("aliases", [])))
        if score == 0:
            continue
        if score > melhor_score:
            melhor_score, melhores = score, [r]
        elif score == melhor_score:
            melhores.append(r)

    if not melhores:
        raise RaceNotFound(f"Corrida não encontrada no calendário: {bruto!r}")
    if len(melhores) > 1:
        rounds = ", ".join(str(r["round"]) for r in melhores)
        raise AmbiguousRace(
            f"Nome {bruto!r} casa com várias corridas (rodadas {rounds}); "
            "acrescente a cidade/circuito para desambiguar."
        )
    return melhores[0]
