"""Testes da Etapa 7 — leitura do export do WhatsApp.

Monta um export sintético (mesmo formato do backup real: cabeçalho de data +
linhas de continuação) e confere as partes que são fáceis de errar em silêncio:
o formato de cada ano, o nome de jogador que também é apelido de piloto, a
consolidação do palpite final da corrida e a leitura das classificações.
"""

import json
import tempfile
import unittest
from pathlib import Path

from bolao.whatsapp_import import (
    SEASONS,
    aliases_pilotos,
    bonus_driver,
    carrega_players,
    consolida_rodadas,
    find_blocks,
    match_player,
    parse_export,
    parse_standing,
)

CALENDAR_2022 = {
    "season": 2022,
    "races": [
        {
            "race_id": "2022-01", "season": 2022, "round": 1, "circuit": "sakhir",
            "race": "Bahrain", "date": "2022-03-20",
            "qualifying_utc": "2022-03-19T15:00:00Z", "sprint": False,
            "aliases": ["bahrain", "sakhir"],
        },
        {
            "race_id": "2022-02", "season": 2022, "round": 2, "circuit": "jeddah",
            "race": "Jeddah", "date": "2022-03-27",
            "qualifying_utc": "2022-03-26T17:00:00Z", "sprint": False,
            "aliases": ["jeddah"],
        },
    ],
}

DRIVERS_2022 = {
    "aliases": {
        "ver": "VER", "verstappen": "VER", "lec": "LEC", "leclerc": "LEC",
        "sai": "SAI", "sainz": "SAI", "per": "PER", "ham": "HAM",
        "hamilton": "HAM", "rus": "RUS", "russell": "RUS", "nor": "NOR",
        "alo": "ALO", "bot": "BOT", "mag": "MAG", "norris": "NOR",
    }
}

PLAYERS_2022 = {
    "aliases": {
        "guilherme": "guilherme", "gui": "guilherme", "ferrari": "ferrari",
        "lage": "lage", "sergio": "lage", "sergin": "lage", "dalla": "dalla",
    },
    "names": {
        "guilherme": "Guilherme", "ferrari": "Ferrari", "lage": "Lage",
        "dalla": "Dalla",
    },
}

# Duas versões da mesma corrida: a segunda é mais completa, mas "perdeu" o
# Dalla que estava na primeira — é exatamente o caso que a consolidação tem que
# recuperar. "Sergio" é jogador e também apelido do Pérez.
EXPORT = """19/03/2022 13:00 - Guilherne Viana: Bolao Qualify Bahrain

Guilherme
VER
LEC
SAI
PER
HAM
RUS

Dalla
LEC
VER
SAI
HAM
PER
NOR
19/03/2022 13:30 - Sergin: Bolao Qualify Bahrain

Guilherme
VER
LEC
SAI
PER
HAM
RUS

Ferrari
Leclerc
Verstappen
Sainz
Hamilton
Russell
Norris

Sergio
LEC
VER
PER
SAI
BOT
MAG
19/03/2022 19:00 - Guilherne Viana: Pontuacao Qualify Bahrain
Guilherme 7
Ferrari 5
Lage 4
Dalla 6
19/03/2022 19:05 - Guilherne Viana: Classificacao Bolao 2022:
1 Guilherme: 47 P 8 🏁
2 Dalla: 42 P 8 🏁
3 Ferrari: 39 P 8 🏁
4 Lage: 30 P 6 🏁
19/03/2022 20:00 - Matheus MF: nada a ver com bolao, so papo furado
"""


def _workspace(tmp: Path) -> Path:
    data = tmp / "data"
    ano = data / "2022"
    (ano / "results").mkdir(parents=True)
    (data / "drivers.json").write_text(
        json.dumps({"aliases": {}}), encoding="utf-8"
    )
    (ano / "drivers.json").write_text(json.dumps(DRIVERS_2022), encoding="utf-8")
    (ano / "players.json").write_text(json.dumps(PLAYERS_2022), encoding="utf-8")
    (ano / "calendar.json").write_text(json.dumps(CALENDAR_2022), encoding="utf-8")
    return data


class TestParseExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        (raiz / "export.txt").write_text(EXPORT, encoding="utf-8")
        self.export = raiz / "export.txt"
        self.data = _workspace(raiz)
        self.msgs = parse_export(self.export)

    def tearDown(self):
        self.tmp.cleanup()

    def test_agrupa_linhas_de_continuacao(self):
        self.assertEqual(len(self.msgs), 5)
        self.assertEqual(self.msgs[0].sender, "Guilherne Viana")
        self.assertEqual(self.msgs[0].lines[0], "Bolao Qualify Bahrain")
        self.assertEqual(self.msgs[0].season, 2022)

    def test_nome_de_jogador_que_e_apelido_de_piloto(self):
        """'Sergio' é jogador (=Lage) e apelido do Pérez: vale a posição."""
        aliases = aliases_pilotos(self.data, 2022)
        players, _ = carrega_players(self.data, 2022)
        blocos = find_blocks(
            self.msgs[1].lines, aliases, SEASONS[2022], set(players)
        )
        nomes = [b.name_raw for b in blocos]
        self.assertIn("Sergio", nomes)
        sergio = next(b for b in blocos if b.name_raw == "Sergio")
        self.assertEqual(sergio.drivers, ["LEC", "VER", "PER", "SAI", "BOT", "MAG"])

    def test_bloco_com_sobrenome_completo(self):
        aliases = aliases_pilotos(self.data, 2022)
        players, _ = carrega_players(self.data, 2022)
        blocos = find_blocks(
            self.msgs[1].lines, aliases, SEASONS[2022], set(players)
        )
        ferrari = next(b for b in blocos if b.name_raw == "Ferrari")
        self.assertEqual(
            ferrari.drivers, ["LEC", "VER", "SAI", "HAM", "RUS", "NOR"]
        )


class TestConsolidacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        (raiz / "export.txt").write_text(EXPORT, encoding="utf-8")
        self.data = _workspace(raiz)
        self.msgs = parse_export(raiz / "export.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def test_recupera_jogador_que_sumiu_da_ultima_mensagem(self):
        rodadas = consolida_rodadas(self.msgs, 2022, self.data)
        self.assertEqual(sorted(rodadas), [1])
        rodada = rodadas[1]
        self.assertEqual(
            sorted(rodada.bets), ["dalla", "ferrari", "guilherme", "lage"]
        )
        self.assertEqual(rodada.principal.stamp.hour, 13)
        self.assertEqual(rodada.principal.stamp.minute, 30)
        self.assertTrue(
            any("dalla" in a and "recuperado" in a for a in rodada.avisos),
            rodada.avisos,
        )

    def test_temporada_sem_piloto_da_rodada_nao_tem_chute(self):
        rodadas = consolida_rodadas(self.msgs, 2022, self.data)
        self.assertIsNone(rodadas[1].bonus_driver)
        self.assertTrue(all(b.guess is None for b in rodadas[1].bets.values()))


class TestClassificacoes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = Path(self.tmp.name)
        self.data = _workspace(raiz)
        (raiz / "export.txt").write_text(EXPORT, encoding="utf-8")
        self.msgs = parse_export(raiz / "export.txt")
        self.players, _ = carrega_players(self.data, 2022)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pontuacao_da_rodada(self):
        st = parse_standing(self.msgs[2], self.players)
        self.assertIsNotNone(st)
        self.assertEqual(st.kind, "rodada")
        self.assertEqual(
            {i.player_id: i.points for i in st.lines},
            {"guilherme": 7, "ferrari": 5, "lage": 4, "dalla": 6},
        )

    def test_classificacao_acumulada(self):
        st = parse_standing(self.msgs[3], self.players)
        self.assertIsNotNone(st)
        self.assertEqual(st.kind, "acumulada")
        self.assertEqual(st.lines[0].player_id, "guilherme")
        self.assertEqual(st.lines[0].points, 47)
        self.assertEqual(st.lines[0].races, 8)

    def test_conversa_fiada_nao_vira_classificacao(self):
        self.assertIsNone(parse_standing(self.msgs[4], self.players))


class TestApelidos(unittest.TestCase):
    def test_nome_com_desabafo_colado_resolve_pelo_prefixo(self):
        aliases = {k: v for k, v in PLAYERS_2022["aliases"].items()}
        self.assertEqual(
            match_player("Ferrari nessa corrida desgraçada", aliases), "ferrari"
        )
        self.assertEqual(match_player("CALIMAN", aliases), None)
        self.assertEqual(match_player("Gui", aliases), "guilherme")

    def test_piloto_da_rodada_com_enfeite_e_riscado(self):
        aliases = {"stroll": "STR", "per": "PER", "perez": "PER", "str": "STR"}
        self.assertEqual(
            bonus_driver(["Piloto Sorteado: ~Drugovich~ *Stroll*"], aliases), "STR"
        )
        self.assertEqual(
            bonus_driver(["Piloto Sorteado: _Checo Perez_"], aliases), "PER"
        )

    def test_frase_solta_com_piloto_nao_e_anuncio(self):
        aliases = {"perez": "PER"}
        self.assertIsNone(
            bonus_driver(['"4 pilotos + Perez" kkkk'], aliases, estrito=True)
        )


if __name__ == "__main__":
    unittest.main()
