"""Pontuação de um palpite contra o resultado real do qualifying.

Regras (seção 2 de contexto/visao-geral.md):

Top6 (máx 12 pts) — para cada um dos 6 pilotos apostados, em ordem:
  * posição exata no quali .............. 2 pts
  * dentro do top6 real, outra posição .. 1 pt
  * fora do top6 real ................... 0 pt

Piloto da rodada (máx 1 pt; **2 pts em 2024**, ver ``bolao.formats``):
  * posição exata no grid (P1..P20) ..... 1 pt
  * caso contrário ...................... 0 pt

Rodada com **mais de um piloto da rodada** (Interlagos 2026): cada piloto é
pontuado à parte pela mesma regra (1 pt por posição exata) e os pontos somam —
com dois pilotos o máximo da rodada vai a 14.

Total máximo por corrida: 13 pts (14 em 2024; 10 em 2021, que era top5 e não
tinha piloto da rodada).
"""

from dataclasses import dataclass, field

from .parser import Bet, Sheet


@dataclass
class Top6Item:
    """Detalhe da pontuação de uma das 6 posições apostadas."""

    pos: int  # 1..6
    guess: str  # código apostado
    real: str | None  # código que realmente ficou nessa posição
    points: int  # 0, 1 ou 2
    reason: str  # "exata" | "no top6" | "fora"


@dataclass
class BonusItem:
    """Detalhe da pontuação de um dos pilotos da rodada."""

    driver: str  # código do piloto da rodada
    guess: int  # posição chutada (0 = não chutou)
    real_pos: int | None  # posição real no quali (None = não largou/ausente)
    points: int


@dataclass
class PlayerScore:
    player_id: str
    player_raw: str
    top6_points: int
    top6_detail: list[Top6Item]
    bonus_points: int
    bonus_guess: int
    bonus_real_pos: int | None  # posição real do piloto da rodada (ou None)
    total: int
    # Quando o placar publicado pelo grupo manda (Etapa 7), `total` passa a ser
    # o publicado e este campo guarda o que a regra da temporada daria.
    total_recalculado: int | None = None
    # Um item por piloto da rodada (vazio nas temporadas sem bônus).
    # ``bonus_points`` é a soma; ``bonus_guess``/``bonus_real_pos`` são do 1º.
    bonus_detail: list[BonusItem] = field(default_factory=list)


@dataclass
class Result:
    """Resultado do quali no formato consumido pela pontuação.

    ``order`` é a lista de códigos canônicos por posição: índice 0 = P1.
    Este é o formato estável que a Etapa 2 (Jolpica) deve produzir.
    """

    race: str
    order: list[str]

    @property
    def top6(self) -> list[str]:
        return self.order[:6]

    def position_of(self, code: str) -> int | None:
        """Posição (1-based) de um piloto, ou None se não estiver na lista."""
        try:
            return self.order.index(code) + 1
        except ValueError:
            return None

    @classmethod
    def from_dict(cls, dados: dict) -> "Result":
        order = dados.get("order") or dados.get("results")
        if not order:
            raise ValueError("Resultado sem lista 'order'/'results'.")
        return cls(race=dados.get("race", ""), order=list(order))


def score_bet(
    bet: Bet,
    result: Result,
    bonus_driver: str,
    bonus_points: int = 1,
    bonus_drivers: list[str] | None = None,
) -> PlayerScore:
    """Pontua um palpite individual contra o resultado.

    ``bonus_points`` é quanto vale acertar a posição do piloto da rodada: 1 hoje,
    mas 2 em 2024 (ver ``bolao.formats``). ``bonus_drivers`` lista os pilotos
    da rodada quando há mais de um (cada um com seu chute em
    ``bet.bonus_guesses``, na mesma ordem); ausente = só ``bonus_driver``.
    """
    # Referência = as primeiras N posições reais, com N = tamanho do palpite
    # (6 hoje; 5 na temporada de 2021 — ver bolao.formats).
    real_top6 = result.order[: len(bet.top6)]
    detalhe: list[Top6Item] = []
    top6_pts = 0

    for i, guess in enumerate(bet.top6):
        pos = i + 1
        real_aqui = result.order[i] if i < len(result.order) else None
        if guess == real_aqui:
            pts, motivo = 2, "exata"
        elif guess in real_top6:
            pts, motivo = 1, "no top6"
        else:
            pts, motivo = 0, "fora"
        top6_pts += pts
        detalhe.append(Top6Item(pos=pos, guess=guess, real=real_aqui, points=pts, reason=motivo))

    # Temporadas sem piloto da rodada (2021-2023) chegam com bonus_driver vazio.
    if bonus_drivers is None:
        bonus_drivers = [bonus_driver] if bonus_driver else []
    chutes = list(bet.bonus_guesses) if len(bonus_drivers) > 1 else [bet.bonus_guess]
    chutes += [0] * (len(bonus_drivers) - len(chutes))
    bonus_detail: list[BonusItem] = []
    for piloto, chute in zip(bonus_drivers, chutes):
        real = result.position_of(piloto)
        acertou = real is not None and real == chute
        bonus_detail.append(
            BonusItem(driver=piloto, guess=chute, real_pos=real,
                      points=bonus_points if acertou else 0)
        )
    bonus_pts = sum(b.points for b in bonus_detail)
    real_bonus_pos = bonus_detail[0].real_pos if bonus_detail else None

    return PlayerScore(
        player_id=bet.player_id,
        player_raw=bet.player_raw,
        top6_points=top6_pts,
        top6_detail=detalhe,
        bonus_points=bonus_pts,
        bonus_guess=bet.bonus_guess,
        bonus_real_pos=real_bonus_pos,
        total=top6_pts + bonus_pts,
        bonus_detail=bonus_detail,
    )


def score_sheet(
    sheet: Sheet, result: Result, bonus_points: int = 1
) -> list[PlayerScore]:
    """Pontua todos os jogadores de uma mensagem, ordenados por total desc."""
    scores = [
        score_bet(bet, result, sheet.bonus_driver, bonus_points, sheet.bonus_drivers)
        for bet in sheet.bets
    ]
    scores.sort(key=lambda s: (-s.total, s.player_id))
    return scores
