"""Integração com a API Jolpica-F1 (Etapa 2).

Jolpica-F1 (https://api.jolpi.ca) é a sucessora da Ergast: gratuita, sem chave,
compatível com o formato de dados da Ergast. Este módulo busca os dados reais de
uma temporada e os grava **nos formatos estáveis que a Etapa 1 já consome**
(ver seção 8 do CONTEXTO.md), sem adaptação manual depois:

    calendar  ->  data/<season>/calendar.json     (corridas da temporada)
    drivers   ->  data/drivers.json                (entry list -> código 3 letras)
    result R  ->  data/<season>/results/<R>.json   (resultado de um quali)

O módulo separa **rede** (`fetch_json`) de **transformação** (`build_*`): as
funções `build_*` recebem o JSON já parseado, então os testes rodam offline com
fixtures salvas (nunca chamam a API no CI).

Identificação da corrida (fixada na Etapa 2): ``race_id = "{season}-{round:02d}"``
(ex.: ``"2026-12"``) — chave única que une temporada + rodada em todo o projeto.

Só o **qualifying principal** conta. Fins de semana com Sprint são apenas
marcados (`"sprint": true`) no calendário — o quali principal continua valendo
(por isso nunca buscamos a sessão de Sprint, só ``/qualifying``).

CLI:
    python -m bolao.jolpica calendar
    python -m bolao.jolpica drivers
    python -m bolao.jolpica result <round>
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .normalize import normalize_key

BASE_URL = "https://api.jolpi.ca/ergast/f1"
SEASON = 2026
USER_AGENT = "bolao-f1/1.0 (+https://github.com/; Etapa 2 Jolpica)"


class JolpicaError(RuntimeError):
    """Falha ao buscar ou interpretar dados da Jolpica."""


class ResultUnavailable(JolpicaError):
    """O quali pedido ainda não tem resultado na Jolpica (re-rodar depois)."""


def race_id(season: int, rnd: int) -> str:
    """Chave única da corrida: ``"{season}-{round:02d}"`` (ex.: ``"2026-12"``)."""
    return f"{season}-{rnd:02d}"


# ---------------------------------------------------------------------------
# Rede
# ---------------------------------------------------------------------------

def fetch_json(url: str, timeout: float = 20.0) -> dict:
    """Busca uma URL e devolve o JSON parseado. Levanta `JolpicaError` em falha."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise JolpicaError(f"HTTP {exc.code} ao buscar {url}") from exc
    except urllib.error.URLError as exc:
        raise JolpicaError(f"Falha de rede ao buscar {url}: {exc.reason}") from exc
    try:
        return json.loads(dados)
    except json.JSONDecodeError as exc:
        raise JolpicaError(f"Resposta não-JSON de {url}") from exc


def season_url(season: int, base_url: str = BASE_URL) -> str:
    return f"{base_url}/{season}.json?limit=100"


def drivers_url(season: int, base_url: str = BASE_URL) -> str:
    return f"{base_url}/{season}/drivers.json?limit=100"


def qualifying_url(season: int, rnd: int, base_url: str = BASE_URL) -> str:
    return f"{base_url}/{season}/{rnd}/qualifying.json?limit=100"


# ---------------------------------------------------------------------------
# Transformação (testável offline com fixtures)
# ---------------------------------------------------------------------------

def _race_aliases(race: dict) -> list[str]:
    """Nomes normalizados que resolvem o nome solto do cabeçalho -> esta corrida.

    Reúne circuitId, nome do circuito, cidade (locality), país, nome oficial da
    corrida e o nome oficial sem "grand prix". Tudo passa por `normalize_key`.
    """
    circuit = race.get("Circuit", {})
    local = circuit.get("Location", {})
    nome_corrida = race.get("raceName", "")
    brutos = [
        circuit.get("circuitId", ""),
        circuit.get("circuitName", ""),
        local.get("locality", ""),
        local.get("country", ""),
        nome_corrida,
        normalize_key(nome_corrida).replace("grand prix", ""),
    ]
    aliases: list[str] = []
    for bruto in brutos:
        chave = normalize_key(bruto)
        if chave and chave not in aliases:
            aliases.append(chave)
    return aliases


def build_calendar(season_json: dict, season: int) -> dict:
    """Monta o `calendar.json` a partir da resposta de ``/<season>.json``."""
    races = season_json.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    if not races:
        raise JolpicaError(f"Calendário vazio para {season} (temporada existe?).")

    saida = []
    for race in races:
        rnd = int(race["round"])
        circuit = race.get("Circuit", {})
        local = circuit.get("Location", {})
        saida.append(
            {
                "race_id": race_id(season, rnd),
                "season": season,
                "round": rnd,
                "circuit": circuit.get("circuitId", ""),
                "race": local.get("locality") or race.get("raceName", ""),
                "date": race.get("date", ""),
                "sprint": "Sprint" in race,
                "aliases": _race_aliases(race),
            }
        )
    saida.sort(key=lambda r: r["round"])
    return {"season": season, "races": saida}


def build_drivers(drivers_json: dict) -> dict:
    """Monta o `drivers.json` (alias -> código 3 letras) da entry list.

    Cadastra, para cada piloto: o código de 3 letras, o sobrenome e o nome
    completo. Pilotos sem código oficial (reservas) são ignorados — não se
    inventa código (ver CONTEXTO.md, seção 6).
    """
    pilotos = drivers_json.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])
    if not pilotos:
        raise JolpicaError("Entry list vazia (temporada sem pilotos?).")

    aliases: dict[str, str] = {}
    for p in pilotos:
        code = (p.get("code") or "").strip().upper()
        if not code:
            continue  # reserva sem código oficial: não inventar
        nome = p.get("givenName", "")
        sobrenome = p.get("familyName", "")
        for bruto in (code, sobrenome, f"{nome} {sobrenome}"):
            chave = normalize_key(bruto)
            if chave:
                aliases[chave] = code

    if not aliases:
        raise JolpicaError("Nenhum piloto com código oficial na entry list.")

    ordenado = {k: aliases[k] for k in sorted(aliases)}
    return {"aliases": ordenado}


def build_result(quali_json: dict, season: int, rnd: int) -> dict:
    """Monta o `results/<round>.json` (formato da Etapa 1) de um quali.

    Levanta `ResultUnavailable` quando o quali ainda não tem resultado na
    Jolpica (para poder re-rodar depois sem gravar lixo).
    """
    races = quali_json.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    if not races:
        raise ResultUnavailable(
            f"Quali de {season} rodada {rnd} ainda não disponível na Jolpica. "
            "Re-rode este fetch quando o resultado sair."
        )

    race = races[0]
    resultados = race.get("QualifyingResults", [])
    if not resultados:
        raise ResultUnavailable(
            f"Quali de {season} rodada {rnd} sem posições ainda. Re-rode depois."
        )

    resultados = sorted(resultados, key=lambda r: int(r["position"]))
    order: list[str] = []
    for r in resultados:
        drv = r.get("Driver", {})
        code = (drv.get("code") or "").strip().upper()
        if not code:  # fallback resiliente: 3 primeiras letras do sobrenome
            code = normalize_key(drv.get("familyName", "")).replace(" ", "")[:3].upper()
        order.append(code)

    if not order:
        raise ResultUnavailable(f"Quali de {season} rodada {rnd} sem grid utilizável.")

    circuit = race.get("Circuit", {})
    local = circuit.get("Location", {})
    return {
        "race_id": race_id(season, rnd),
        "season": season,
        "round": rnd,
        "circuit": circuit.get("circuitId", ""),
        "race": local.get("locality") or race.get("raceName", ""),
        "order": order,
    }


# ---------------------------------------------------------------------------
# Fetch (rede + transformação)
# ---------------------------------------------------------------------------

def fetch_calendar(season: int = SEASON, base_url: str = BASE_URL) -> dict:
    return build_calendar(fetch_json(season_url(season, base_url)), season)


def fetch_drivers(season: int = SEASON, base_url: str = BASE_URL) -> dict:
    return build_drivers(fetch_json(drivers_url(season, base_url)))


def fetch_result(rnd: int, season: int = SEASON, base_url: str = BASE_URL) -> dict:
    return build_result(fetch_json(qualifying_url(season, rnd, base_url)), season, rnd)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _write_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bolão F1 — fetch Jolpica (Etapa 2)")
    p.add_argument("--season", type=int, default=SEASON)
    p.add_argument("--base-url", default=BASE_URL)
    p.add_argument("--out", help="caminho de saída (sobrescreve o padrão)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("calendar", help="grava o calendário da temporada")
    sub.add_parser("drivers", help="grava o drivers.json da entry list")
    sp = sub.add_parser("result", help="grava o resultado de um quali")
    sp.add_argument("round", type=int, help="número da rodada")
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.cmd == "calendar":
            dados = fetch_calendar(args.season, args.base_url)
            destino = Path(args.out or f"data/{args.season}/calendar.json")
        elif args.cmd == "drivers":
            dados = fetch_drivers(args.season, args.base_url)
            destino = Path(args.out or "data/drivers.json")
        else:  # result
            dados = fetch_result(args.round, args.season, args.base_url)
            destino = Path(args.out or f"data/{args.season}/results/{args.round}.json")
    except ResultUnavailable as exc:
        print(f"[indisponível] {exc}", file=sys.stderr)
        return 2
    except JolpicaError as exc:
        print(f"[erro] {exc}", file=sys.stderr)
        return 1

    _write_json(destino, dados)
    print(f"Gravado: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
