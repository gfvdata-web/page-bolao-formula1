"""Formato do palpite em cada temporada (Etapa 7).

O bolão não nasceu com o formato de hoje. O que muda entre os anos é quantos
pilotos cada jogador aposta e se existe o palpite do **piloto da rodada** —
e isso muda a pontuação máxima por corrida. A regra de pontos em si (2 pts na
posição exata, 1 pt dentro do top N real, 0 fora) é a mesma em todos os anos.

Conferido contra as pontuações que o próprio grupo publicou no WhatsApp
(ver seção 8 do CONTEXTO.md, Etapa 7).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SeasonFormat:
    """Como o palpite era escrito e pontuado numa temporada."""

    top_n: int  # quantos pilotos o jogador aposta (P1..Pn)
    bonus: bool  # existe palpite da posição do piloto da rodada?
    bonus_points: int = 1  # quanto vale acertar a posição exata dele

    @property
    def max_points(self) -> int:
        return self.top_n * 2 + (self.bonus_points if self.bonus else 0)


# Temporada -> formato. Anos não listados usam o formato atual.
FORMATS: dict[int, SeasonFormat] = {
    2021: SeasonFormat(top_n=5, bonus=False),  # máx 10
    2022: SeasonFormat(top_n=6, bonus=False),  # máx 12
    2023: SeasonFormat(top_n=6, bonus=False),  # máx 12
    # 2024 pagava 2 pts no acerto do piloto da rodada (máx 14). Confirmado
    # pela R2 (Jeddah): o sorteado foi o VER, os 10 jogadores cravaram P1 e ele
    # fez a pole — o placar publicado bate 10/10 com 2 pts e 0/10 com 1 pt.
    2024: SeasonFormat(top_n=6, bonus=True, bonus_points=2),  # máx 14
    2025: SeasonFormat(top_n=6, bonus=True),
    2026: SeasonFormat(top_n=6, bonus=True),
}

ATUAL = SeasonFormat(top_n=6, bonus=True)


def season_format(season: int) -> SeasonFormat:
    return FORMATS.get(season, ATUAL)
