"""Parsing da mensagem de palpites do WhatsApp.

Formato esperado (ver seção 3 do CONTEXTO.md):

    Qualify Bolao Silverstone      <- linha 1: identifica a corrida
    Piloto Hamilton                <- linha 2: piloto da rodada (bônus)

    Guilherme                      <- nome do jogador
    ANT                            <- top6, um piloto por linha (P1..P6)
    RUS
    HAM
    VER
    NOR
    PIA
    P1                             <- chute da posição do piloto da rodada

    <bloco em branco separa jogadores>
    ...
"""

from dataclasses import dataclass, field

from .normalize import normalize_driver, normalize_key, normalize_player


@dataclass
class Bet:
    """Palpite de um jogador numa rodada."""

    player_id: str
    player_raw: str
    top6: list[str]  # 6 códigos canônicos, P1..P6
    bonus_guess: int  # posição chutada do piloto da rodada (1..20)


@dataclass
class Sheet:
    """Mensagem inteira parseada: cabeçalho + palpites."""

    race: str  # nome bruto da corrida (ex.: "Silverstone")
    header_raw: str  # linha 1 completa, para rastreabilidade
    bonus_driver: str  # código canônico do piloto da rodada
    bets: list[Bet] = field(default_factory=list)


class ParseError(ValueError):
    """Erro de formato na mensagem de palpites."""


def _split_blocks(linhas: list[str]) -> list[list[str]]:
    """Agrupa linhas em blocos separados por uma ou mais linhas em branco."""
    blocos: list[list[str]] = []
    atual: list[str] = []
    for linha in linhas:
        if linha.strip():
            atual.append(linha.strip())
        elif atual:
            blocos.append(atual)
            atual = []
    if atual:
        blocos.append(atual)
    return blocos


def _parse_bonus_guess(linha: str, player_raw: str) -> int:
    """Converte a linha do chute do bônus (ex.: ``"P1"``) num inteiro 1..20."""
    digitos = "".join(ch for ch in linha if ch.isdigit())
    if not digitos:
        raise ParseError(
            f"Chute do piloto da rodada inválido para '{player_raw}': {linha!r}"
        )
    pos = int(digitos)
    if not 1 <= pos <= 20:
        raise ParseError(
            f"Posição fora de P1..P20 para '{player_raw}': {linha!r}"
        )
    return pos


def _parse_bonus_driver(linha: str, driver_aliases: dict) -> str:
    """Extrai o código do piloto da rodada da linha ``"Piloto Hamilton"``."""
    partes = normalize_key(linha).split()
    if partes and partes[0] == "piloto":
        partes = partes[1:]
    if not partes:
        raise ParseError(f"Cabeçalho do piloto da rodada inválido: {linha!r}")
    return normalize_driver(" ".join(partes), driver_aliases)


def parse_sheet(
    texto: str,
    driver_aliases: dict | None = None,
    player_aliases: dict | None = None,
) -> Sheet:
    """Parseia a mensagem completa do WhatsApp numa :class:`Sheet`.

    Cada bloco de jogador deve ter exatamente 8 linhas:
    nome + 6 pilotos + linha ``P#``.
    """
    driver_aliases = driver_aliases or {}
    player_aliases = player_aliases or {}

    blocos = _split_blocks(texto.splitlines())
    if len(blocos) < 2:
        raise ParseError(
            "Mensagem sem cabeçalho e/ou palpites (esperado cabeçalho + blocos)."
        )

    # O cabeçalho pode vir colado num bloco só (corrida + piloto) ou separado.
    cabecalho = blocos[0]
    if len(cabecalho) >= 2:
        header_raw, linha_piloto = cabecalho[0], cabecalho[1]
        blocos_jogadores = blocos[1:]
    else:
        header_raw = cabecalho[0]
        linha_piloto = blocos[1][0]
        blocos_jogadores = blocos[2:]

    # Nome da corrida: remove um prefixo tipo "Qualify Bolao " se presente.
    race = header_raw
    chave = normalize_key(header_raw).split()
    for marcador in ("bolao", "bolão"):
        if marcador in chave:
            idx = chave.index("bolao") if "bolao" in chave else chave.index("bolão")
            race = " ".join(header_raw.split()[idx + 1:]) or header_raw
            break

    bonus_driver = _parse_bonus_driver(linha_piloto, driver_aliases)

    bets: list[Bet] = []
    for bloco in blocos_jogadores:
        if len(bloco) != 8:
            raise ParseError(
                f"Bloco de jogador com {len(bloco)} linhas (esperado 8): {bloco!r}"
            )
        nome = bloco[0]
        top6 = [normalize_driver(c, driver_aliases) for c in bloco[1:7]]
        bonus_guess = _parse_bonus_guess(bloco[7], nome)
        bets.append(
            Bet(
                player_id=normalize_player(nome, player_aliases),
                player_raw=nome,
                top6=top6,
                bonus_guess=bonus_guess,
            )
        )

    return Sheet(
        race=race,
        header_raw=header_raw,
        bonus_driver=bonus_driver,
        bets=bets,
    )
