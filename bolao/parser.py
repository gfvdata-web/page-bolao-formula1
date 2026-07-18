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

Robustez p/ mensagens reais (Etapa 3): as transcrições do WhatsApp variam mais
que o exemplo acima. O parser tolera, **sem mudar o formato de saída**:

- **Cabeçalho `Circuito: X`** numa linha própria (nome da corrida ali, não na 1ª).
- **Palavras de enfeite** na linha do piloto: ``Piloto escolhido:``,
  ``Piloto Sorteado``, ``Piloto  Bearman`` (espaços/pontuação extras).
- **Linha em branco logo após o nome** do jogador (o bloco é reconhecido pela
  linha ``P#`` que o encerra, não pela separação em branco).
- **Chute até P22** (grid 2026 tem até 22 pilotos).
- **Linha do chute com enfeite** de negrito/itálico do WhatsApp (``*P14*``,
  ``_P14_``) — ignora ``*``/``_`` ao redor ao reconhecer o fim do bloco.
"""

import re
from dataclasses import dataclass, field

from .normalize import normalize_driver, normalize_key, normalize_player


@dataclass
class Bet:
    """Palpite de um jogador numa rodada."""

    player_id: str
    player_raw: str
    top6: list[str]  # 6 códigos canônicos, P1..P6
    bonus_guess: int  # posição chutada do piloto da rodada (1..22)


@dataclass
class Sheet:
    """Mensagem inteira parseada: cabeçalho + palpites."""

    race: str  # nome bruto da corrida (ex.: "Silverstone")
    header_raw: str  # linha de identificação da corrida, para rastreabilidade
    bonus_driver: str  # código canônico do piloto da rodada
    bets: list[Bet] = field(default_factory=list)


class ParseError(ValueError):
    """Erro de formato na mensagem de palpites."""


# Palavras de enfeite que aparecem na linha do piloto da rodada e não fazem
# parte do nome do piloto (ex.: "Piloto escolhido: Hadjar").
_FILLER_BONUS = {
    "piloto",
    "escolhido",
    "escolhida",
    "sorteado",
    "sorteada",
    "sorteio",
}

# Palavras de enfeite no começo da linha da corrida ("Bolão Qualify <Corrida>").
_FILLER_RACE = {"bolao", "qualify", "quali"}

# Uma linha de chute do bônus é algo como "P8", "P22" ou só "8".
_GUESS_RE = re.compile(r"^[pP]?\d{1,2}$")

# Grade máxima de 2026 (11 equipes x 2). Acima disso o chute nunca casa (0 pt),
# mas ainda é aceito para preservar o palpite original do jogador.
_MAX_GRID = 22


def _is_guess_line(linha: str) -> bool:
    """True se a linha é um chute de posição (encerra o bloco de um jogador).

    Ignora ``*``/``_`` de negrito/itálico que o WhatsApp às vezes deixa em
    volta do número (ex.: ``*P14*``) — sem isso, a linha não bate com
    ``_GUESS_RE`` e o bloco não fecha, misturando o jogador seguinte.
    """
    return bool(_GUESS_RE.match(linha.strip().strip("*_")))


def _parse_bonus_guess(linha: str, player_raw: str) -> int:
    """Converte a linha do chute do bônus (ex.: ``"P1"``) num inteiro 1..22."""
    digitos = "".join(ch for ch in linha if ch.isdigit())
    if not digitos:
        raise ParseError(
            f"Chute do piloto da rodada inválido para '{player_raw}': {linha!r}"
        )
    pos = int(digitos)
    if not 1 <= pos <= _MAX_GRID:
        raise ParseError(
            f"Posição fora de P1..P{_MAX_GRID} para '{player_raw}': {linha!r}"
        )
    return pos


def _parse_bonus_driver(linha: str, driver_aliases: dict) -> str:
    """Extrai o código do piloto da rodada da linha ``"Piloto escolhido: X"``."""
    partes = [t for t in normalize_key(linha).split() if t not in _FILLER_BONUS]
    if not partes:
        raise ParseError(f"Cabeçalho do piloto da rodada inválido: {linha!r}")
    return normalize_driver(" ".join(partes), driver_aliases)


def _resolve_race_line(header_lines: list[str]) -> tuple[str, str]:
    """Devolve ``(race, header_raw)`` a partir das linhas de cabeçalho.

    Prefere uma linha ``Circuito: X`` (nome da corrida ali). Caso contrário,
    usa a primeira linha, removendo o enfeite inicial ``Bolão/Qualify``.
    """
    if not header_lines:
        raise ParseError("Cabeçalho sem identificação da corrida.")

    for linha in header_lines:
        if normalize_key(linha).split()[:1] == ["circuito"]:
            resto = linha.split(":", 1)[1] if ":" in linha else " ".join(linha.split()[1:])
            resto = resto.strip()
            if resto:
                return resto, linha

    header_raw = header_lines[0]
    race_tokens: list[str] = []
    comecou = False
    for tok in header_raw.split():
        if not comecou and normalize_key(tok) in _FILLER_RACE | {""}:
            continue
        comecou = True
        race_tokens.append(tok)
    race = " ".join(race_tokens) or header_raw
    return race, header_raw


def _parse_players(
    corpo: list[str], driver_aliases: dict, player_aliases: dict
) -> list[Bet]:
    """Agrupa o corpo em jogadores usando a linha ``P#`` como terminador.

    Ignora linhas em branco (já removidas) e é tolerante a uma linha vazia logo
    após o nome — cada jogador é ``nome + 6 pilotos + P#`` (8 linhas úteis).
    """
    bets: list[Bet] = []
    buffer: list[str] = []
    for linha in corpo:
        if not _is_guess_line(linha):
            buffer.append(linha)
            continue
        bloco = buffer + [linha]
        buffer = []
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
    if buffer:
        raise ParseError(f"Bloco de jogador incompleto (sem linha P#): {buffer!r}")
    return bets


def parse_sheet(
    texto: str,
    driver_aliases: dict | None = None,
    player_aliases: dict | None = None,
) -> Sheet:
    """Parseia a mensagem completa do WhatsApp numa :class:`Sheet`."""
    driver_aliases = driver_aliases or {}
    player_aliases = player_aliases or {}

    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not linhas:
        raise ParseError("Mensagem vazia.")

    # Cabeçalho = linhas do topo até (inclusive) a linha do "Piloto ...".
    idx_piloto = next(
        (i for i, l in enumerate(linhas) if normalize_key(l).split()[:1] == ["piloto"]),
        None,
    )
    if idx_piloto is None:
        raise ParseError(
            "Cabeçalho sem a linha do piloto da rodada ('Piloto ...')."
        )

    race, header_raw = _resolve_race_line(linhas[:idx_piloto])
    bonus_driver = _parse_bonus_driver(linhas[idx_piloto], driver_aliases)

    corpo = linhas[idx_piloto + 1:]
    if not corpo:
        raise ParseError("Mensagem sem palpites de jogadores.")

    bets = _parse_players(corpo, driver_aliases, player_aliases)
    if not bets:
        raise ParseError("Nenhum palpite de jogador encontrado.")

    return Sheet(
        race=race,
        header_raw=header_raw,
        bonus_driver=bonus_driver,
        bets=bets,
    )
