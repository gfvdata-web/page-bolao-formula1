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
from datetime import date, datetime, timedelta
from pathlib import Path

from .calendar import load_calendar
from .formats import FORMATS, SeasonFormat

# --------------------------------------------------------------------------
# Configuração por temporada
# --------------------------------------------------------------------------

# O formato de cada ano vive em bolao/formats.py (compartilhado com o parser,
# a pontuação e a síntese das mensagens).
SEASONS: dict[int, SeasonFormat] = {
    ano: fmt for ano, fmt in FORMATS.items() if ano <= 2025
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
    #   (espaço não-quebrável) aparece em "Checo Perez" e quebra o
    # reconhecimento do piloto se não virar espaço normal.
    limpa = linha.replace("‎", "").replace("‏", "").replace(" ", " ")
    return _MARCADORES.sub("", limpa)


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


# "Piloto da rodada: Sainz", "Piloto Sorteado: Checo Perez", "Piloto Hadjar".
# O (?=[\s:-]) impede que "pilotos" (plural, em frase solta) case como anúncio.
_BONUS_HEADER = re.compile(
    r"piloto(?=[\s:\-])(?:\s*(da\s+rodada|escolhid[oa]|sortead[oa]))?\s*(:)?\s*(.+)",
    re.I,
)


def bonus_driver(
    lines: list[str], aliases: dict[str, str], estrito: bool = False
) -> str | None:
    """Extrai o piloto da rodada do cabeçalho da mensagem (2024+).

    A linha vem cheia de enfeite no histórico real: ``Piloto ~Sorteado~:
    *Bortoleto*🇧🇷``, ``Piloto Sorteado: _Checo Perez_``. Limpa a marcação e o
    emoji e procura o piloto em qualquer par/palavra do que sobrou.
    """
    for linha in lines[:6]:
        # ~Riscado~ no WhatsApp e correcao ("Piloto Sorteado: ~Drugovich~
        # Stroll") — o nome riscado foi cancelado e nao pode ganhar do certo.
        limpo = re.sub(r"~[^~]+~", " ", linha)
        limpo = re.sub(r"[*_~`]+", " ", limpo)
        limpo = "".join(c for c in limpo if c.isalpha() or c.isspace() or c in ":-")
        m = _BONUS_HEADER.match(chave(limpo))
        if not m:
            continue
        # Fora do bloco de palpites, só vale como anúncio se estiver escrito
        # como anúncio ("Piloto sorteado:", "Piloto da rodada") — senão
        # qualquer frase com "piloto" e um sobrenome viraria falso positivo.
        if estrito and not (m.group(1) or m.group(2)):
            continue
        resto = m.group(3)
        codigo = driver_code(resto, aliases)
        if codigo:
            return codigo
        palavras = resto.split()
        for tamanho in (2, 1):
            for i in range(len(palavras) - tamanho + 1):
                codigo = driver_code(" ".join(palavras[i : i + tamanho]), aliases)
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
    """Dia do quali. O calendario de 2021 da Jolpica nao traz horario de
    sessao: sem ``qualifying_utc``, usa a vespera da corrida (o quali e no
    sabado). Sem esse ajuste, um placar publicado no dia do quali parece ser
    de uma corrida que ainda nao aconteceu."""
    bruto = corrida.get("qualifying_utc")
    if bruto:
        return datetime.fromisoformat(bruto.replace("Z", "+00:00")).date()
    return datetime.fromisoformat(corrida["date"]).date() - timedelta(days=1)


def resolve_round(
    msg: Message, calendar: dict, janela: int = 6, passado: bool = False
) -> int | None:
    """Descobre a rodada pela data da mensagem (janela de ±``janela`` dias).

    As mensagens de palpite circulam entre a véspera e o dia seguinte ao quali,
    e as cópias continuam depois — a proximidade da data resolve sem depender
    do cabeçalho, que nem sempre existe (2022 não tinha).

    Com ``passado=True`` só considera qualis que **já aconteceram**: é o caso
    das mensagens de pontuação e classificação, que só podem falar de corrida
    já disputada. Sem isso, um placar publicado na semana da corrida seguinte
    é atribuído à corrida errada (aconteceu no fim de 2024).
    """
    melhor, menor = None, None
    for corrida in calendar["races"]:
        dias = (msg.day - _dia_quali(corrida)).days
        if passado and dias < 0:
            continue
        delta = abs(dias)
        if (passado or delta <= janela) and (menor is None or delta < menor):
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
    # O piloto da rodada nem sempre vem junto dos palpites: às vezes é anunciado
    # numa mensagem só de aviso ("Bolão Qualify Interlagos / Piloto Sorteado:
    # Stroll"). Guarda o anúncio mais recente de cada rodada como reserva.
    anuncios: dict[int, tuple[datetime, str]] = {}
    for msg in msgs:
        if msg.season != season:
            continue
        blocos = _blocos_da_mensagem(msg, aliases, players, fmt)
        rnd = resolve_round(msg, calendar)
        if rnd is None:
            continue
        if fmt.bonus and len(blocos) < 2 and len(msg.lines) <= 6:
            piloto = bonus_driver(msg.lines, aliases, estrito=True)
            if piloto and (rnd not in anuncios or anuncios[rnd][0] < msg.stamp):
                anuncios[rnd] = (msg.stamp, piloto)
        if len(blocos) < 2:
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
            if alvo.bonus_driver is None and rnd in anuncios:
                quando, alvo.bonus_driver = anuncios[rnd]
                alvo.avisos.append(
                    f"piloto da rodada ({alvo.bonus_driver}) veio do anúncio "
                    f"avulso de {quando:%d/%m/%Y %H:%M}"
                )
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
            rnd = resolve_round(msg, cal, passado=True)
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

    aliases_jog, exibicao = carrega_players(data_dir, season)
    palpites = dir_ano / f"palpites_{season}.csv"
    with palpites.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["circuito", "nome", "p1", "p2", "p3", "p4", "p5", "p6", "pos"])
        for rnd in sorted(rodadas):
            rb = rodadas[rnd]
            for _pid, reg in sorted(rb.bets.items(), key=lambda kv: kv[1].ordem):
                # O nome vai bruto (rastreabilidade), menos quando ele não bate
                # com nenhum alias — aí vai o nome canônico, senão o resto do
                # pipeline criaria um jogador novo a partir do desabafo colado.
                nome = reg.name_raw.strip()
                if chave(nome) not in aliases_jog:
                    nome = exibicao.get(reg.player_id, reg.player_id)
                # Bloco curto (o jogador listou menos pilotos que o normal):
                # completa com ZZZ, um código que nunca casa — assim o palpite
                # fica do tamanho certo e as posições que faltaram valem 0.
                pilotos = list(reg.drivers[: fmt.top_n])
                pilotos += ["ZZZ"] * (fmt.top_n - len(pilotos))
                pilotos += [""] * (6 - fmt.top_n)
                wr.writerow(
                    [nome_corrida.get(rnd, str(rnd)), nome, *pilotos,
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


def _pontos_recalculados(
    rodadas: dict[int, RoundBets], season: int, data_dir: Path
) -> dict[int, dict[str, int]]:
    """Pontuação por rodada recalculada, mesma regra do :mod:`bolao.scoring`."""
    fmt = SEASONS[season]
    saida: dict[int, dict[str, int]] = {}
    for rnd, rb in rodadas.items():
        caminho = data_dir / str(season) / "results" / f"{rnd}.json"
        if not caminho.exists():
            continue
        order = json.loads(caminho.read_text(encoding="utf-8"))["order"]
        alvo = order[: fmt.top_n]
        do_round: dict[str, int] = {}
        for pid, reg in rb.bets.items():
            total = 0
            for i, guess in enumerate(reg.drivers[: fmt.top_n]):
                if i < len(order) and guess == order[i]:
                    total += 2
                elif guess in alvo:
                    total += 1
            if (
                fmt.bonus
                and reg.guess
                and rb.bonus_driver
                and rb.bonus_driver in order
                and order.index(rb.bonus_driver) + 1 == reg.guess
            ):
                total += 1
            do_round[pid] = total
        saida[rnd] = do_round
    return saida


def escreve_conferencia(
    msgs: list[Message],
    todas: dict[int, dict[int, RoundBets]],
    data_dir: Path,
    destino: Path,
) -> None:
    """``conferencia.txt``: recálculo × pontuação publicada no grupo.

    É o controle de qualidade do import: se a regra de pontuação e a leitura
    dos palpites estiverem certas, o recálculo tem que bater com o placar que
    o próprio grupo divulgou na época.
    """
    partes = [
        _CABECALHO_PRIVACIDADE,
        "# conferencia — pontuação recalculada vs. a publicada no grupo.\n"
        "# 'ok' = bate. 'calc!=rep' = diverge (o recálculo é o que vale nos\n"
        "# dados; a divergência fica registrada aqui para conferência humana).\n",
    ]
    for season in sorted(todas):
        rodadas = todas[season]
        fmt = SEASONS[season]
        players, exibicao = carrega_players(data_dir, season)
        calendar = load_calendar(data_dir / str(season) / "calendar.json")
        pontos = _pontos_recalculados(rodadas, season, data_dir)
        saldo_path = data_dir / str(season) / "saldo_inicial.json"
        saldo = (
            json.loads(saldo_path.read_text(encoding="utf-8"))["players"]
            if saldo_path.exists()
            else {}
        )
        partes.append(
            f"\n\n{'=' * 70}\nTEMPORADA {season} — top{fmt.top_n}"
            f"{' + piloto da rodada' if fmt.bonus else ' (sem piloto da rodada)'}"
            f", máx {fmt.max_points} pts/corrida\n{'=' * 70}\n"
        )
        acertos = divergencias = 0
        linhas_por_rodada: list[str] = []
        linhas_acumuladas: list[str] = []
        for msg in msgs:
            if msg.season != season:
                continue
            st = parse_standing(msg, players)
            if not st:
                continue
            rnd = resolve_round(msg, calendar, passado=True)
            if rnd is None:
                continue
            def acumulado_ate(limite: int, pid: str) -> int:
                return saldo.get(pid, {}).get("pontos", 0) + sum(
                    v.get(pid, 0) for r, v in pontos.items() if r <= limite
                )

            def calcula(r: int, pid: str) -> int | None:
                if st.kind == "rodada":
                    return pontos.get(r, {}).get(pid)
                return acumulado_ate(r, pid)

            def batem(r: int) -> int:
                return sum(calcula(r, i.player_id) == i.points for i in st.lines)

            # A mensagem nem sempre é do fim de semana que a data sugere: o
            # grupo publicava atrasado, repostava tabela antiga e às vezes
            # mandava várias rodadas seguidas pra pôr em dia. Procura a rodada
            # que realmente encaixa; se nenhuma encaixa, mantém a da data e
            # marca — divergência de verdade tem que aparecer.
            alvo, nota = rnd, ""
            candidatas = [r for r in sorted(pontos) if r <= rnd + 1]
            if candidatas:
                melhor = max(candidatas, key=batem)
                if batem(melhor) > batem(rnd) and batem(melhor) >= 0.6 * len(st.lines):
                    alvo, nota = melhor, f" [reflete R{melhor}]"
                elif batem(rnd) < 0.6 * len(st.lines):
                    nota = " [sem encaixe]"

            itens = []
            for item in st.lines:
                calc = calcula(alvo, item.player_id)
                if calc is None:
                    itens.append(f"{item.player_id}:sem-palpite")
                    continue
                if calc == item.points:
                    acertos += 1
                    itens.append(f"{item.player_id}:ok")
                else:
                    divergencias += 1
                    itens.append(f"{item.player_id}:{calc}!={item.points}")
            linha = (
                f"  R{rnd:2d} {msg.stamp:%d/%m %H:%M}{nota}  " + " ".join(itens) + "\n"
            )
            (linhas_por_rodada if st.kind == "rodada" else linhas_acumuladas).append(linha)
        partes.append(f"\n-- pontuação por rodada --\n")
        partes.extend(linhas_por_rodada or ["  (nenhuma publicada)\n"])
        partes.append(f"\n-- classificação acumulada --\n")
        partes.extend(linhas_acumuladas or ["  (nenhuma publicada)\n"])
        total = acertos + divergencias
        pct = (100 * acertos / total) if total else 0
        partes.append(
            f"\n  Resumo {season}: {acertos}/{total} conferências batem ({pct:.0f}%).\n"
        )
    destino.write_text("".join(partes), encoding="utf-8")


def escreve_saldo_inicial(
    msgs: list[Message],
    rodadas: dict[int, RoundBets],
    season: int,
    data_dir: Path,
) -> dict | None:
    """Recupera o placar das rodadas **anteriores** à primeira com palpite.

    O bolão de 2021 rodou o ano inteiro, mas o WhatsApp só tem palpite a partir
    da rodada 11. O que sobrou das rodadas 1–10 é a **classificação acumulada**
    que o grupo publicava: subtraindo dela as rodadas que sabemos recalcular,
    sobra um saldo (pontos + rodadas jogadas) por jogador.

    Devolve ``None`` quando a temporada começa na rodada 1 (nada a recuperar).
    """
    if not rodadas or min(rodadas) == 1:
        return None

    fmt = SEASONS[season]
    players, _ = carrega_players(data_dir, season)
    calendar = load_calendar(data_dir / str(season) / "calendar.json")

    # Pontuação por rodada recalculada (mesma regra do bolao.scoring).
    pontos: dict[int, dict[str, int]] = {}
    for rnd, rb in rodadas.items():
        caminho = data_dir / str(season) / "results" / f"{rnd}.json"
        if not caminho.exists():
            continue
        order = json.loads(caminho.read_text(encoding="utf-8"))["order"]
        alvo = order[: fmt.top_n]
        do_round: dict[str, int] = {}
        for pid, reg in rb.bets.items():
            total = 0
            for i, guess in enumerate(reg.drivers[: fmt.top_n]):
                if i < len(order) and guess == order[i]:
                    total += 2
                elif guess in alvo:
                    total += 1
            if (
                fmt.bonus
                and reg.guess
                and rb.bonus_driver
                and rb.bonus_driver in order
                and order.index(rb.bonus_driver) + 1 == reg.guess
            ):
                total += 1
            do_round[pid] = total
        pontos[rnd] = do_round

    # Primeira classificação acumulada publicada depois da 1ª rodada com palpite.
    primeira = min(rodadas)
    escolhida: tuple[int, Message, Standing] | None = None
    for msg in msgs:
        if msg.season != season:
            continue
        st = parse_standing(msg, players)
        if not st or st.kind != "acumulada":
            continue
        rnd = resolve_round(msg, calendar, passado=True)
        if rnd is None or rnd < primeira:
            continue
        if escolhida is None or rnd < escolhida[0]:
            escolhida = (rnd, msg, st)
    if escolhida is None:
        return None

    ate, msg, st = escolhida
    saldo = {}
    for item in st.lines:
        conhecidos = {r: p[item.player_id] for r, p in pontos.items()
                      if r <= ate and item.player_id in p}
        saldo[item.player_id] = {
            "pontos": item.points - sum(conhecidos.values()),
            "rodadas": max(0, (item.races or 0) - len(conhecidos)),
        }

    dados = {
        "_comment": (
            f"Saldo das rodadas anteriores a R{primeira} de {season}, que nao tem "
            "palpite no historico do WhatsApp. Derivado da classificacao "
            f"acumulada de {msg.stamp:%d/%m/%Y %H:%M} (apos R{ate}) menos as "
            "rodadas que sabemos recalcular. Entra no ranking como bloco de "
            "pontos + rodadas jogadas, sem detalhe por corrida."
        ),
        "ate_rodada": primeira - 1,
        "fonte": msg.header(),
        "players": dict(sorted(saldo.items())),
    }
    destino = data_dir / str(season) / "saldo_inicial.json"
    destino.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return dados


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
            saldo = escreve_saldo_inicial(msgs, rodadas, s, data_dir)
            if saldo:
                resumo = ", ".join(
                    f"{pid} {v['pontos']}pts/{v['rodadas']}r"
                    for pid, v in saldo["players"].items()
                )
                print(
                    f"     saldo_inicial.json (rodadas 1-{saldo['ate_rodada']}): {resumo}"
                )
    escreve_conferencia(msgs, todas, data_dir, out_dir / "conferencia.txt")
    print(f"palpitesfinais.txt e demais saídas em {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
