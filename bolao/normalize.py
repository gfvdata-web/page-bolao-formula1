"""Normalização de códigos de piloto e de nomes de jogador.

O texto vindo do WhatsApp é inconsistente (`HAM`/`Ham`, nomes completos,
acentos e pontuação nos nomes dos jogadores). Este módulo transforma essas
variações em identificadores estáveis para que a soma no ranking da temporada
não se perca.

Os mapas de apelidos (`driver_aliases`, `player_aliases`) são **entradas** —
na Etapa 1 vêm de mocks em `data/`; na Etapa 2 o mapa de pilotos passa a ser
gerado da entry list real da Jolpica. O formato é estável: `chave -> canônico`,
onde a chave é sempre passada por `normalize_key`.
"""

import unicodedata


def _strip_accents(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_key(texto: str) -> str:
    """Chave canônica para comparação: sem acento, minúscula, só
    alfanumérico + espaços simples.

    Ex.: ``"Vinícius"`` -> ``"vinicius"``; ``"Caio L."`` -> ``"caio l"``.
    """
    sem_acento = _strip_accents(texto).lower()
    limpo = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in sem_acento)
    return " ".join(limpo.split())


def normalize_driver(bruto: str, driver_aliases: dict | None = None) -> str:
    """Devolve o código canônico de 3 letras de um piloto.

    Resolve pelo mapa de apelidos quando possível (cobre nomes completos e
    grafias específicas). Como fallback resiliente, usa as 3 primeiras letras
    em maiúsculo — o que funciona para a maioria dos códigos da F1.
    """
    driver_aliases = driver_aliases or {}
    chave = normalize_key(bruto)
    if chave in driver_aliases:
        return driver_aliases[chave]
    letras = "".join(ch for ch in chave if ch.isalpha())
    return letras.upper()[:3]


def normalize_player(bruto: str, player_aliases: dict | None = None) -> str:
    """Devolve o id canônico e estável de um jogador.

    Usa o mapa de apelidos para unir variantes (``"Caio"``/``"Caio L."``).
    Sem mapa, cai num id derivado do nome (espaços viram ``_``), que já é
    estável entre rodadas para grafias idênticas.
    """
    player_aliases = player_aliases or {}
    chave = normalize_key(bruto)
    if chave in player_aliases:
        return player_aliases[chave]
    return chave.replace(" ", "_")
