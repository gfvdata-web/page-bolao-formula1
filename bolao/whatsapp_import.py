"""Etapa 7 — importação do histórico a partir do export do WhatsApp.

As temporadas de 2021 a 2024 não têm planilha: os palpites só existem no
histórico do grupo. O export do WhatsApp é quase todo conversa fiada; este
módulo separa o que interessa, consolida o palpite final de cada corrida e
gera os arquivos que o resto da Etapa 7 consome.

**Privacidade:** os arquivos de texto gerados aqui contêm mensagens do grupo e
por isso vão para um diretório fora do Git (``historico_wpp/``, no
``.gitignore``). Só os CSV derivados (``data/<season>/palpites_<season>.csv``)
entram no repositório — mesmo formato já usado por 2025.

Formato do export::

    31/07/2021 08:04 - Vinicius: Ferrari
    Ver
    Ham
    ...

Cada mensagem começa com ``DD/MM/AAAA HH:MM - Remetente: `` e continua nas
linhas seguintes até a próxima linha com data.

Como o formato do palpite mudou ao longo dos anos (ver ``SEASONS``):

- **2021** — top5, sem piloto da rodada.
- **2022, 2023** — top6, sem piloto da rodada.
- **2024, 2025** — top6 + piloto da rodada (cabeçalho + linha ``P#``).

Uso::

    python -m bolao.whatsapp_import extract --export backupmsgs.txt
"""

import argparse
import csv
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from .calendar import load_calendar

# --------------------------------------------------------------------------
# Configuração por temporada
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class SeasonFormat:
    """Como o palpite era escrito naquele ano."""

    top_n: int  # quantos pilotos o jogador apostava
    bonus: bool  # existia palpite de piloto da rodada?


SEASONS: dict[int, SeasonFormat] = {
    2021: SeasonFormat(top_n=5, bonus=False),
    2022: SeasonFormat(top_n=6, bonus=False),
    2023: SeasonFormat(top_n=6, bonus=False),
    2024: SeasonFormat(top_n=6, bonus=True),
    2025: SeasonFormat(top_n=6, bonus=True),
}

# Apelidos de piloto que só aparecem no WhatsApp antigo (primeiro nome, sigla
# inventada, grafia torta). Não entram em data/drivers.json porque só servem
# para ler o histórico — e alguns mudam de dono conforme o ano ("kimi" é
# Räikkönen até 2021 e Antonelli em 2025).
APELIDOS_COMUNS: dict[str, str] = {
    "max": "VER",
    "mv": "VER",
    "verstappe": "VER",
    "lewis": "HAM",
    "lh": "HAM",
    "hamilto": "HAM",
    "charles": "LEC",
    "leclec": "LEC",
    "lec ": "LEC",
    "carlos": "SAI",
    "fernando": "ALO",
    "nando": "ALO",
    "sergio": "PER",
    "checo": "PER",
    "perez": "PER",
    "george": "RUS",
    "russel": "RUS",
    "lando": "NOR",
    "valtteri": "BOT",
    "bottas": "BOT",
    "esteban": "OCO",
    "pierre": "GAS",
    "daniel": "RIC",
    "danny": "RIC",
    "yuki": "TSU",
    "lance": "STR",
    "sebastian": "VET",
    "seb": "VET",
    "vettel": "VET",
    "vest": "VET",
    "alex": "ALB",
    "albon": "ALB",
    "kevin": "MAG",
    "mag": "MAG",
    "hulk": "HUL",
    "nico": "HUL",
    "oscar": "PIA",
    "logan": "SAR",
    "franco": "COL",
    "oliver": "BEA",
    "ollie": "BEA",
    "liam": "LAW",
    "guanyu": "ZHO",
    "zhou": "ZHO",
    "nyck": "DEV",
    "de vries": "DEV",
    "devries": "DEV",
    "mick": "MSC",
    "msc": "MSC",
    "schumacher": "MSC",
    "nikita": "MAZ",
    "mazepin": "MAZ",
    "mick schumacher": "MSC",
    "nicholas": "LAT",
    "latifi": "LAT",
    "antonio": "GIO",
    "giovinazzi": "GIO",
    "robert": "KUB",
    "kubica": "KUB",
    # Erros de digitacao e apelidos de brincadeira colhidos do proprio grupo.
    "vetel": "VET",
    "sains": "SAI",
    "sain": "SAI",
    "carlitos": "SAI",
    "carlin": "SAI",
    "peres": "PER",
    "piasfri": "PIA",
    "alexander": "ALB",
    "han": "HAM",
    "hem": "HAM",
    "legleg": "LEC",
    "charlin": "LEC",
    "rua": "RUS",
    "ris": "RUS",
    "lindo": "NOR",
    "mic": "MSC",
    "alon": "ALO",
    "super max": "VER",
}

# Apelidos que trocam de dono conforme a temporada.
APELIDOS_POR_ANO: dict[int, dict[str, str]] = {
    2021: {"kimi": "RAI", "raikkonen": "RAI", "rai": "RAI"},
    2022: {"kimi": "RAI", "raikkonen": "RAI"},
    2023: {"vest": "VER"},  # sem Vettel na grade: "Vest" vira Verstappen
    2024: {"kimi": "ANT", "andrea": "ANT"},
    2025: {"kimi": "ANT", "andrea": "ANT"},
}


# --------------------------------------------------------------------------
# Leitura do export
# --------------------------------------------------------------------------

_MSG_RE = re.compile(
    r"^(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}) - (.*)$"
)


# Marcadores que o WhatsApp cola na linha e atrapalham o reconhecimento
# ("P5 <Mensagem editada>" tem que continuar sendo lido como P5).
_MARCADORES = re.compile(
    r"\s*<(?:Mensagem editada|Mídia oculta|Media omitted|Esta mensagem foi apagada)>\s*",
    re.I,
)


def _limpa(linha: str) -> str:
    return _MARCADORES.sub("", linha.replace("‎", "").replace("‏", ""))


@dataclass
class Message:
    """Uma mensagem do export, com as linhas de continuação já agrupadas."""

    stamp: datetime
    sender: str | None
    lines: list[str]

    @property
    def day(self) -> date:
        return self.stamp.date()

    @property
    def season(self) -> int:
        return self.stamp.year

    def text(self) -> str:
        return "\n".join(self.lines)

    def header(self) -> str:
        quem = self.sender or "(sistema)"
        return f"{self.stamp.strftime('%d/%m/%Y %H:%M')} - {quem}"


def parse_export(caminho: str | Path) -> list[Message]:
    """Lê o export do WhatsApp e devolve as mensagens agrupadas."""
    msgs: list[Message] = []
    atual: Message | None = None
    with Path(caminho).open(encoding="utf-8") as f:
        for bruta in f:
            linha = bruta.rstrip("\n").rstrip("\r")
            m = _MSG_RE.match(linha)
            if m:
                if atual is not None:
                    msgs.append(atual)
                dia, mes, ano, hora, minuto, resto = m.groups()
                stamp = datetime(int(ano), int(mes), int(dia), int(hora), int(minuto))
                if ": " in resto:
                    remetente, corpo = resto.split(": ", 1)
                else:
                    remetente, corpo = None, resto
                atual = Message(stamp=stamp, sender=remetente, lines=[_limpa(corpo)])
            elif atual is not None:
                atual.lines.append(_limpa(linha))
    if atual is not None:
        msgs.append(atual)
    return msgs


# --------------------------------------------------------------------------
# Reconhecimento de linhas
# --------------------------------------------------------------------------

# Prefixo de posição: "1.", "1-", "1)", "1 ", "- ", "P1 -" etc.
_PREFIXO_POS = re.compile(r"^\s*(?:\d{1,2}\s*[.)\-:º°]?|[-•*–])\s+|^\s*(\d{1,2})[.)\-:]\s*")
# Enfeite de negrito/itálico do WhatsApp e pontuação solta nas pontas.
_ENFEITE = re.compile(r"^[\s*_~`\-–•]+|[\s*_~`\-–•.,:;!?]+$")


def _sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def chave(texto: str) -> str:
    """Normaliza uma linha para comparação (sem acento, minúscula, sem enfeite)."""
    limpo = _ENFEITE.sub("", _sem_acento(texto)).strip()
    limpo = re.sub(r"\s+", " ", limpo)
    return limpo.lower()


def aliases_pilotos(data_dir: Path, season: int) -> dict[str, str]:
    """Mapa apelido -> código, para ler o WhatsApp daquele ano.

    Camadas, da mais fraca para a mais forte: ``data/drivers.json`` (base) →
    entry list do ano (``data/<season>/drivers.json``) → apelidos comuns do
    WhatsApp → apelidos específicos do ano.
    """
    mapa: dict[str, str] = {}
    for caminho in (data_dir / "drivers.json", data_dir / str(season) / "drivers.json"):
        if caminho.exists():
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            mapa.update({chave(k): v for k, v in dados.get("aliases", {}).items()})
    grid = set(mapa.values())
    for apelido, codigo in APELIDOS_COMUNS.items():
        if codigo in grid:
            mapa[chave(apelido)] = codigo
    for apelido, codigo in APELIDOS_POR_ANO.get(season, {}).items():
        if codigo in grid:
            mapa[chave(apelido)] = codigo
    return mapa


def driver_code(linha: str, aliases: dict[str, str]) -> str | None:
    """Devolve o código do piloto se a linha for um item de top6, senão None.

    Aceita ``VER``, ``Ver``, ``Verstappen``, ``Max``, ``1. LEC``, ``- Bottas``.
    """
    bruto = linha.strip()
    if not bruto or len(bruto) > 40:
        return None
    candidatos = [bruto]
    sem_prefixo = _PREFIXO_POS.sub("", bruto, count=1)
    if sem_prefixo != bruto:
        candidatos.append(sem_prefixo)
    for cand in candidatos:
        k = chave(cand)
        if not k:
            continue
        if k in aliases:
            return aliases[k]
        if len(k) == 3 and k.upper() in set(aliases.values()):
            return k.upper()
    return None


# Linha do chute do piloto da rodada: "P4", "p4", "*P14*", "4".
_GUESS_RE = re.compile(r"^[\s*_~]*[pP]\s*(\d{1,2})[\s*_~.]*$")


def bonus_guess(linha: str) -> int | None:
    m = _GUESS_RE.match(linha.strip())
    return int(m.group(1)) if m else None


@dataclass
class Block:
    """Bloco de um jogador dentro de uma mensagem de palpite."""

    name_raw: str
    drivers: list[str]
    guess: int | None
    line_index: int  # onde o nome aparece na mensagem (para ordem de envio)


def find_blocks(
    lines: list[str],
    aliases: dict[str, str],
    fmt: SeasonFormat,
    players: set[str] | None = None,
) -> list[Block]:
    """Acha os blocos jogador→pilotos numa mensagem.

    Estratégia: procurar **sequências** de linhas de piloto com tamanho
    compatível com o ano; a linha não-vazia imediatamente anterior é o nome do
    jogador. Isso resolve o caso em que o nome do jogador também é nome de
    piloto (``Sergio``, ``Ferrari``) — o que manda é a posição, não o texto.
    """
    codigos = [driver_code(l, aliases) for l in lines]
    players = players or set()
    blocos: list[Block] = []
    i = 0
    minimo = max(3, fmt.top_n - 2)
    while i < len(lines):
        if codigos[i] is None:
            i += 1
            continue
        j = i
        seq: list[str] = []
        while j < len(lines) and codigos[j] is not None:
            seq.append(codigos[j])
            j += 1
        # O nome do jogador pode ser apelido de piloto ("Sergio", "Ferrari") e
        # ter sido engolido pela sequência. Nesse caso a sequência começa com o
        # nome: devolve a primeira linha para fora dela.
        inicio = i
        if (
            len(seq) > fmt.top_n
            and chave(lines[i]) in players
            and len(seq) - 1 >= minimo
        ):
            seq = seq[1:]
            inicio = i + 1
        if len(seq) < minimo:
            i = max(j, i + 1)
            continue
        # Nome do jogador: última linha não-vazia antes da sequência.
        k = inicio - 1
        while k >= 0 and not lines[k].strip():
            k -= 1
        nome = lines[k].strip() if k >= 0 else ""
        # Chute do bônus: primeira linha "P#" depois da sequência.
        chute = None
        if fmt.bonus:
            for l in lines[j : j + 3]:
                if not l.strip():
                    continue
                chute = bonus_guess(l)
                break
        if nome and not bonus_guess(nome):
            blocos.append(Block(nome, seq, chute, k))
        i = max(j, i + 1)
    return blocos


_BONUS_HEADER = re.compile(r"piloto(?:\s+(?:da\s+rodada|escolhid[oa]|sortead[oa]))?\s*[:\-]?\s*(.+)", re.I)


def bonus_driver(lines: list[str], aliases: dict[str, str]) -> str | None:
    """Extrai o piloto da rodada do cabeçalho da mensagem (2024+)."""
    for linha in lines[:6]:
        m = _BONUS_HEADER.match(chave(linha))
        if m:
            codigo = driver_code(m.group(1), aliases)
            if codigo:
                return codigo
    return None


# --------------------------------------------------------------------------
# Jogadores
# --------------------------------------------------------------------------

def carrega_players(data_dir: Path, season: int) -> tuple[dict[str, str], dict[str, str]]:
    """Devolve (aliases jogador->id, id->nome de exibição) da temporada."""
    caminho = data_dir / str(season) / "players.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    aliases = {chave(k): v for k, v in dados.get("aliases", {}).items()}
    return aliases, dados.get("names", {})


def match_player(nome_bruto: str, aliases: dict[str, str]) -> str | None:
    """Resolve o nome do bloco no id canônico do jogador.

    Tolera o que aparece de verdade: caixa e acento (``CALIMAN``, ``Vinícius``),
    dois-pontos no fim (``Francez:``) e desabafo colado no nome (``Ferrari
    nessa corrida desgraçada...``) — nesse caso vale o prefixo.
    """
    k = chave(nome_bruto)
    if not k:
        return None
    if k in aliases:
        return aliases[k]
    primeira = k.split(" ", 1)[0]
    if primeira in aliases:
        return aliases[primeira]
    for apelido in sorted(aliases, key=len, reverse=True):
        if k.startswith(apelido + " "):
            return aliases[apelido]
    return None


# --------------------------------------------------------------------------
# Classificações / pontuações reportadas
# --------------------------------------------------------------------------

# "Guilherme 2", "Guilherme: 61 🅿️ 12 🏁", "1️⃣ Lage - 30 🅿️"
_LINHA_PONTOS = re.compile(
    r"^[^A-Za-zÀ-ÿ]{0,10}([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' .]{1,24}?)\s*[:\-–]?\s+(\d{1,3})\b(.*)$"
)
_RODADAS_RE = re.compile(r"(\d{1,3})\s*🏁")


@dataclass
class StandingLine:
    player_id: str
    name_raw: str
    points: int
    races: int | None


@dataclass
class Standing:
    """Uma mensagem de pontuação (da rodada) ou classificação (acumulada)."""

    message: Message
    kind: str  # "rodada" | "acumulada"
    title: str
    lines: list[StandingLine]


def parse_standing(msg: Message, players: dict[str, str]) -> Standing | None:
    """Reconhece uma mensagem de pontuação/classificação do bolão.

    Exige pelo menos 3 linhas ``jogador conhecido + número`` e que a maioria
    das linhas com texto seja desse tipo — o que descarta tabela de horários,
    idade de piloto e outras listas numéricas do grupo.
    """
    itens: list[StandingLine] = []
    corpo = [l for l in msg.lines if l.strip()]
    for linha in corpo:
        m = _LINHA_PONTOS.match(linha.strip())
        if not m:
            continue
        pid = match_player(m.group(1), players)
        if not pid:
            continue
        rodadas = _RODADAS_RE.search(m.group(3))
        itens.append(
            StandingLine(pid, m.group(1).strip(), int(m.group(2)),
                         int(rodadas.group(1)) if rodadas else None)
        )
    if len(itens) < 3:
        return None
    ids = {i.player_id for i in itens}
    if len(ids) < 3 or len(itens) < 0.5 * len(corpo):
        return None
    # Acumulada: alguém com mais pontos do que cabe numa rodada, ou com 🏁.
    acumulada = any(i.races is not None for i in itens) or max(
        i.points for i in itens
    ) > 13
    titulo = ""
    primeira = corpo[0].strip()
    if not _LINHA_PONTOS.match(primeira) or not match_player(
        _LINHA_PONTOS.match(primeira).group(1), players
    ):
        titulo = primeira
    return Standing(msg, "acumulada" if acumulada else "rodada", titulo, itens)


# --------------------------------------------------------------------------
# Rodada de cada mensagem
# --------------------------------------------------------------------------

_PALAVRAS_HEADER = {"bolao", "qualify", "quali", "qualy", "apostas", "aposta"}


def parece_header(linha: str) -> bool:
    """Diz se a linha é o cabeçalho da mensagem ('Bolão Qualify Baku')."""
    palavras = set(chave(linha).replace("-", " ").split())
    return bool(palavras & _PALAVRAS_HEADER)


def _dia_quali(corrida: dict) -> date:
    bruto = corrida.get("qualifying_utc") or corrida.get("date")
    return datetime.fromisoformat(bruto.replace("Z", "+00:00")).date()


def resolve_round(msg: Message, calendar: dict, janela: int = 6) -> int | None:
    """Descobre a rodada pela data da mensagem (janela de ±``janela`` dias).

    As mensagens de palpite circulam entre a véspera e o dia seguinte ao quali,
    e as cópias continuam depois — a proximidade da data resolve sem depender
    do cabeçalho, que nem sempre existe (2022 não tinha).
    """
    melhor, menor = None, None
    for corrida in calendar["races"]:
        delta = abs((msg.day - _dia_quali(corrida)).days)
        if delta <= janela and (menor is None or delta < menor):
            melhor, menor = corrida["round"], delta
    return melhor


# --------------------------------------------------------------------------
# Consolidação: o palpite final de cada corrida
# --------------------------------------------------------------------------

@dataclass
class BetRecord:
    """Palpite de um jogador numa rodada, já resolvido."""

    player_id: str
    name_raw: str
    drivers: list[str]
    guess: int | None
    origem: Message
    ordem: int  # posição do bloco na mensagem (ordem de envio)


@dataclass
class RoundBets:
    season: int
    rnd: int
    principal: Message | None = None  # mensagem mais completa da rodada
    bonus_driver: str | None = None
    bets: dict[str, BetRecord] = field(default_factory=dict)
    mensagens: list[Message] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _blocos_da_mensagem(
    msg: Message,
    aliases: dict[str, str],
    players: dict[str, str],
    fmt: SeasonFormat,
) -> list[tuple[str, Block]]:
    """Blocos da mensagem já com o jogador resolvido (descarta o que não é bloco)."""
    saida: list[tuple[str, Block]] = []
    for bloco in find_blocks(msg.lines, aliases, fmt, set(players)):
        pid = match_player(bloco.name_raw, players)
        if pid is None and parece_header(bloco.name_raw) and msg.sender:
            # 1º bloco da mensagem original: quem escreveu não repetiu o nome.
            pid = match_player(msg.sender, players)
        if pid is not None:
            saida.append((pid, bloco))
    return saida


def consolida_rodadas(
    msgs: list[Message],
    season: int,
    data_dir: Path,
) -> dict[int, RoundBets]:
    """Junta as mensagens de palpite de cada rodada num palpite final.

    Base = a mensagem **mais completa** da rodada (mais jogadores; empate
    resolvido pela mais recente, que é a versão final da corrente). Jogador que
    apareceu numa mensagem anterior e sumiu da final é **recuperado** da última
    mensagem em que apareceu, e a recuperação vai para ``avisos``.
    """
    fmt = SEASONS[season]
    aliases = aliases_pilotos(data_dir, season)
    players, _ = carrega_players(data_dir, season)
    calendar = load_calendar(data_dir / str(season) / "calendar.json")

    por_rodada: dict[int, RoundBets] = {}
    for msg in msgs:
        if msg.season != season:
            continue
        blocos = _blocos_da_mensagem(msg, aliases, players, fmt)
        if len(blocos) < 2:
            continue
        rnd = resolve_round(msg, calendar)
        if rnd is None:
            continue
        alvo = por_rodada.setdefault(rnd, RoundBets(season, rnd))
        alvo.mensagens.append(msg)

    for rnd, alvo in por_rodada.items():
        principal = max(
            alvo.mensagens,
            key=lambda m: (len(_blocos_da_mensagem(m, aliases, players, fmt)), m.stamp),
        )
        alvo.principal = principal
        if fmt.bonus:
            alvo.bonus_driver = bonus_driver(principal.lines, aliases)
            if alvo.bonus_driver is None:
                for m in sorted(alvo.mensagens, key=lambda m: m.stamp, reverse=True):
                    alvo.bonus_driver = bonus_driver(m.lines, aliases)
                    if alvo.bonus_driver:
                        alvo.avisos.append(
                            f"piloto da rodada veio de outra mensagem ({m.header()})"
                        )
                        break
        for ordem, (pid, bloco) in enumerate(
            _blocos_da_mensagem(principal, aliases, players, fmt)
        ):
            alvo.bets[pid] = BetRecord(
                pid, bloco.name_raw, bloco.drivers, bloco.guess, principal, ordem
            )
        # Recupera quem apareceu antes e sumiu da mensagem final.
        for msg in sorted(alvo.mensagens, key=lambda m: m.stamp):
            for pid, bloco in _blocos_da_mensagem(msg, aliases, players, fmt):
                if pid in alvo.bets:
                    continue
                alvo.bets[pid] = BetRecord(
                    pid, bloco.name_raw, bloco.drivers, bloco.guess, msg,
                    len(alvo.bets),
                )
                alvo.avisos.append(
                    f"'{pid}' recuperado de {msg.header()} (sumiu da mensagem final)"
                )
        for pid, reg in alvo.bets.items():
            if len(reg.drivers) != fmt.top_n:
                alvo.avisos.append(
                    f"'{pid}' com {len(reg.drivers)} pilotos (esperado {fmt.top_n}): "
                    f"{reg.drivers}"
                )
            if len(set(reg.drivers[: fmt.top_n])) != len(reg.drivers[: fmt.top_n]):
                alvo.avisos.append(f"'{pid}' repetiu piloto no top{fmt.top_n}: {reg.drivers}")
            if fmt.bonus and reg.guess is None:
                alvo.avisos.append(f"'{pid}' sem chute do piloto da rodada")
    return por_rodada


# --------------------------------------------------------------------------
# Saídas
# --------------------------------------------------------------------------

_CABECALHO_PRIVACIDADE = (
    "# Gerado por `python -m bolao.whatsapp_import` a partir do export do WhatsApp.\n"
    "# Contém mensagens do grupo — este diretório NÃO é versionado (ver .gitignore).\n"
)


def _bloco_mensagem(msg: Message) -> str:
    return f"{msg.header()}:\n" + "\n".join(msg.lines)


def escreve_raw(
    msgs: list[Message], seasons: list[int], data_dir: Path, destino: Path
) -> int:
    """``historico_raw.txt``: só as mensagens de palpite e de classificação."""
    partes = [_CABECALHO_PRIVACIDADE, "# historico_raw — palpites e classificações, na ordem original.\n"]
    n = 0
    ctx = {}
    for s in seasons:
        ctx[s] = (
            aliases_pilotos(data_dir, s),
            carrega_players(data_dir, s)[0],
            SEASONS[s],
        )
    for msg in msgs:
        if msg.season not in ctx:
            continue
        aliases, players, fmt = ctx[msg.season]
        tipo = None
        if len(_blocos_da_mensagem(msg, aliases, players, fmt)) >= 2:
            tipo = "PALPITES"
        else:
            st = parse_standing(msg, players)
            if st:
                tipo = "PONTUACAO" if st.kind == "rodada" else "CLASSIFICACAO"
        if tipo:
            partes.append(f"\n----- [{tipo}] -----\n{_bloco_mensagem(msg)}\n")
            n += 1
    destino.write_text("".join(partes), encoding="utf-8")
    return n


def escreve_palpites_finais(
    todas: dict[int, dict[int, RoundBets]], data_dir: Path, destino: Path
) -> None:
    """``palpitesfinais.txt``: o palpite consolidado de cada corrida."""
    partes = [_CABECALHO_PRIVACIDADE, "# palpitesfinais — palpite consolidado por corrida.\n"]
    for season in sorted(todas):
        cal = load_calendar(data_dir / str(season) / "calendar.json")
        nomes = {c["round"]: c["race"] for c in cal["races"]}
        _, exibicao = carrega_players(data_dir, season)
        partes.append(f"\n\n{'=' * 70}\nTEMPORADA {season}\n{'=' * 70}\n")
        for rnd in sorted(todas[season]):
            rb = todas[season][rnd]
            partes.append(
                f"\n--- {season} R{rnd} — {nomes.get(rnd, '?')} "
                f"(mensagem final: {rb.principal.header()}; "
                f"{len(rb.mensagens)} versões na rodada)\n"
            )
            if rb.bonus_driver:
                partes.append(f"Piloto da rodada: {rb.bonus_driver}\n")
            for pid, reg in sorted(rb.bets.items(), key=lambda kv: kv[1].ordem):
                chute = f"  P{reg.guess}" if reg.guess is not None else ""
                partes.append(
                    f"  {exibicao.get(pid, pid):16s} {' '.join(reg.drivers)}{chute}\n"
                )
            for aviso in rb.avisos:
                partes.append(f"  [aviso] {aviso}\n")
    destino.write_text("".join(partes), encoding="utf-8")


def escreve_classificacoes(
    msgs: list[Message], seasons: list[int], data_dir: Path, destino: Path
) -> int:
    """``classificacoes.txt``: pontuações de rodada e classificações acumuladas."""
    partes = [
        _CABECALHO_PRIVACIDADE,
        "# classificacoes — pontuação por rodada e classificação acumulada,\n"
        "# como foram reportadas no grupo (fonte para conferir o recálculo).\n",
    ]
    n = 0
    for season in seasons:
        players, exibicao = carrega_players(data_dir, season)
        cal = load_calendar(data_dir / str(season) / "calendar.json")
        partes.append(f"\n\n{'=' * 70}\nTEMPORADA {season}\n{'=' * 70}\n")
        for msg in msgs:
            if msg.season != season:
                continue
            st = parse_standing(msg, players)
            if not st:
                continue
            rnd = resolve_round(msg, cal)
            partes.append(
                f"\n--- [{st.kind}] {msg.header()}"
                f"{f' (rodada ~{rnd})' if rnd else ''}"
                f"{f' — {st.title}' if st.title else ''}\n"
            )
            for item in st.lines:
                extra = f"  ({item.races} rodadas)" if item.races is not None else ""
                partes.append(
                    f"  {exibicao.get(item.player_id, item.player_id):16s} "
                    f"{item.points:4d}{extra}\n"
                )
            n += 1
    destino.write_text("".join(partes), encoding="utf-8")
    return n


def escreve_csvs(
    rodadas: dict[int, RoundBets], season: int, data_dir: Path
) -> tuple[Path, Path]:
    """Grava os CSV versionados, no mesmo formato que 2025 (``bolao.historico``).

    ``palpites_<season>.csv`` tem ``p1..p6`` para todos os anos; em 2021 (top5)
    a coluna ``p6`` fica vazia. ``pos`` fica vazia nos anos sem piloto da rodada.
    """
    fmt = SEASONS[season]
    cal = load_calendar(data_dir / str(season) / "calendar.json")
    nome_corrida = {c["round"]: c["race"] for c in cal["races"]}
    dir_ano = data_dir / str(season)

    palpites = dir_ano / f"palpites_{season}.csv"
    with palpites.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["circuito", "nome", "p1", "p2", "p3", "p4", "p5", "p6", "pos"])
        for rnd in sorted(rodadas):
            rb = rodadas[rnd]
            for _pid, reg in sorted(rb.bets.items(), key=lambda kv: kv[1].ordem):
                pilotos = list(reg.drivers[: fmt.top_n]) + [""] * (6 - fmt.top_n)
                pilotos = (pilotos + [""] * 6)[:6]
                wr.writerow(
                    [nome_corrida.get(rnd, str(rnd)), reg.name_raw.strip(), *pilotos,
                     f"P{reg.guess}" if reg.guess is not None else ""]
                )

    corridas = dir_ano / f"rodadas_{season}.csv"
    with corridas.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["circuito", "rodada", "data", "quem"])
        for rnd in sorted(rodadas):
            corrida = next(c for c in cal["races"] if c["round"] == rnd)
            wr.writerow(
                [corrida["race"], rnd, corrida["date"], rodadas[rnd].bonus_driver or ""]
            )
    return palpites, corridas


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Bolão F1 — importa o histórico do export do WhatsApp (Etapa 7)"
    )
    p.add_argument("--export", required=True, help="caminho do backup .txt do WhatsApp")
    p.add_argument("--data-dir", default="data")
    p.add_argument(
        "--out-dir",
        default="historico_wpp",
        help="onde gravar os .txt (fora do Git — contém mensagens do grupo)",
    )
    p.add_argument(
        "--seasons",
        default="2021,2022,2023,2024",
        help="temporadas a importar, separadas por vírgula",
    )
    p.add_argument(
        "--no-csv", action="store_true", help="não regravar os CSV em data/<ano>/"
    )
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    seasons = [int(s) for s in args.seasons.split(",") if s.strip()]
    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    msgs = parse_export(args.export)
    print(f"Export: {len(msgs)} mensagens.")

    todas = {s: consolida_rodadas(msgs, s, data_dir) for s in seasons}

    n_raw = escreve_raw(msgs, seasons, data_dir, out_dir / "historico_raw.txt")
    escreve_palpites_finais(todas, data_dir, out_dir / "palpitesfinais.txt")
    n_cls = escreve_classificacoes(msgs, seasons, data_dir, out_dir / "classificacoes.txt")
    print(f"historico_raw.txt: {n_raw} mensagens relevantes.")
    print(f"classificacoes.txt: {n_cls} relatórios.")

    for s in seasons:
        rodadas = todas[s]
        palpites = sum(len(r.bets) for r in rodadas.values())
        avisos = sum(len(r.avisos) for r in rodadas.values())
        print(
            f"{s}: {len(rodadas)} rodadas com palpite, {palpites} palpites, "
            f"{avisos} avisos."
        )
        if not args.no_csv:
            a, b = escreve_csvs(rodadas, s, data_dir)
            print(f"     {a} / {b}")
    print(f"palpitesfinais.txt e demais saídas em {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
