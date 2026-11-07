"""Rodada com dois pilotos da rodada (Interlagos 2026, rodada 20).

Cabeçalho ``Piloto da vez *Bortoleto* e *Camara*``; cada jogador manda um
``P#`` por piloto, na ordem do cabeçalho. 1 pt por piloto (máx 14 na rodada).
Rodadas com um piloto só continuam idênticas.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from bolao.parser import ParseError, parse_sheet
from bolao.scoring import Result, score_sheet
from bolao.site import generate

RAIZ = Path(__file__).resolve().parent.parent
DRIVERS = json.loads((RAIZ / "data" / "drivers.json").read_text(encoding="utf-8"))["aliases"]
PLAYERS = json.loads((RAIZ / "data" / "2026" / "players.json").read_text(encoding="utf-8"))["aliases"]
TEXTO = (RAIZ / "tests" / "fixtures" / "interlagos_2026_dois_pilotos.txt").read_text(encoding="utf-8")

# Grid fictício: BOR em P8, CAM em P20.
ORDEM = ["ANT", "LEC", "NOR", "VER", "HAM", "RUS", "PIA", "BOR", "HAD", "LAW",
         "GAS", "ALB", "SAI", "HUL", "COL", "BEA", "ALO", "STR", "LIN", "CAM", "PER", "BOT"]


class TestParserDoisPilotos(unittest.TestCase):
    def setUp(self):
        self.sheet = parse_sheet(TEXTO, DRIVERS, PLAYERS)

    def test_cabecalho_lista_os_dois(self):
        self.assertEqual(self.sheet.race, "*Interlagos*")
        self.assertEqual(self.sheet.bonus_drivers, ["BOR", "CAM"])
        self.assertEqual(self.sheet.bonus_driver, "BOR")

    def test_um_chute_por_piloto(self):
        chutes = {b.player_id: b.bonus_guesses for b in self.sheet.bets}
        self.assertEqual(chutes["guilherme"], [8, 15])
        self.assertEqual(chutes["paganini"], [10, 20])  # *P10* com negrito

    def test_segundo_chute_faltando_vale_zero(self):
        ferrari = next(b for b in self.sheet.bets if b.player_id == "ferrari")
        self.assertEqual(ferrari.bonus_guesses, [12, 0])
        self.assertEqual(ferrari.bonus_guess, 12)

    def test_separadores_aceitos(self):
        base = TEXTO.split("\n", 2)[2]
        for linha in ("Piloto da vez: Bortoleto, Camara", "Piloto Bortoleto & Câmara",
                      "Piloto da vez Bortoleto e Rafael Camara", "Piloto BOR / CAM"):
            sheet = parse_sheet(f"Bolão Interlagos\n{linha}\n{base}", DRIVERS, PLAYERS)
            self.assertEqual(sheet.bonus_drivers, ["BOR", "CAM"], linha)

    def test_p_a_mais_e_erro_com_nome(self):
        texto = TEXTO.replace("P15\n", "P15\nP3\n")
        with self.assertRaisesRegex(ParseError, "Guilherme"):
            parse_sheet(texto, DRIVERS, PLAYERS)

    def test_piloto_repetido_e_erro(self):
        texto = TEXTO.replace("*Camara*", "*Bortoleto*")
        with self.assertRaises(ParseError):
            parse_sheet(texto, DRIVERS, PLAYERS)

    def test_rodada_normal_inalterada(self):
        sheet = parse_sheet((RAIZ / "data" / "2026" / "messages" / "19.txt").read_text(encoding="utf-8"),
                            DRIVERS, PLAYERS)
        self.assertEqual(sheet.bonus_drivers, ["NOR"])
        self.assertTrue(all(len(b.bonus_guesses) == 1 for b in sheet.bets))

    def test_p_extra_em_rodada_normal_continua_erro(self):
        texto = (RAIZ / "data" / "2026" / "messages" / "19.txt").read_text(encoding="utf-8")
        with self.assertRaises(ParseError):
            parse_sheet(texto.replace("P4\n", "P4\nP5\n", 1), DRIVERS, PLAYERS)


class TestChuteComNomeDoPiloto(unittest.TestCase):
    """Mensagem real de Interlagos 2026: ``P9 BOR``, ``BOR P9``, ``Cam 17``, ``P10``."""

    def setUp(self):
        texto = (RAIZ / "tests" / "fixtures" / "interlagos_2026_real.txt").read_text(encoding="utf-8")
        self.sheet = parse_sheet(texto, DRIVERS, PLAYERS)
        self.chutes = {b.player_id: b.bonus_guesses for b in self.sheet.bets}

    def test_todos_os_jogadores_lidos(self):
        self.assertEqual(len(self.sheet.bets), 9)
        self.assertEqual(self.sheet.bonus_drivers, ["BOR", "CAM"])

    def test_formatos_do_chute(self):
        self.assertEqual(self.chutes["guilherme"], [9, 14])  # P9 BOR / P14 CAM
        self.assertEqual(self.chutes["ferrari"], [10, 15])  # P10 Bor / P15 Cam
        self.assertEqual(self.chutes["caio_l"], [9, 16])  # BOR P9 / CAM P16
        self.assertEqual(self.chutes["francez"], [7, 17])  # BOR p7 / Cam 17
        self.assertEqual(self.chutes["dalla"], [10, 17])  # P10 / P17 (sem nome)

    def test_nome_fora_de_ordem_vai_para_o_piloto(self):
        texto = TEXTO.replace("P8\nP15\n", "CAM P15\nBOR P8\n", 1)
        guilherme = parse_sheet(texto, DRIVERS, PLAYERS).bets[0]
        self.assertEqual(guilherme.bonus_guesses, [8, 15])
        self.assertEqual(guilherme.bonus_guess, 8)

    def test_so_o_segundo_com_nome(self):
        texto = TEXTO.replace("P8\nP15\n", "P15 CAM\n", 1)
        guilherme = parse_sheet(texto, DRIVERS, PLAYERS).bets[0]
        self.assertEqual(guilherme.bonus_guesses, [0, 15])

    def test_dois_chutes_para_o_mesmo_piloto_e_erro(self):
        texto = TEXTO.replace("P8\nP15\n", "P8 BOR\nP15 BOR\n", 1)
        with self.assertRaisesRegex(ParseError, "Guilherme"):
            parse_sheet(texto, DRIVERS, PLAYERS)

    def test_nome_que_nao_e_piloto_da_rodada_nao_vira_chute(self):
        texto = TEXTO.replace("P8\nP15\n", "P8 VER\nP15\n", 1)
        with self.assertRaises(ParseError):
            parse_sheet(texto, DRIVERS, PLAYERS)


class TestPontuacaoDoisPilotos(unittest.TestCase):
    def setUp(self):
        sheet = parse_sheet(TEXTO, DRIVERS, PLAYERS)
        self.scores = {s.player_id: s for s in score_sheet(sheet, Result("Interlagos", ORDEM))}

    def test_acerta_os_dois(self):
        s = self.scores["paganini"]  # chutou P10 (BOR P8) e P20 (CAM P20)
        self.assertEqual([b.points for b in s.bonus_detail], [0, 1])
        self.assertEqual(s.bonus_points, 1)

    def test_soma_por_piloto(self):
        s = self.scores["guilherme"]  # BOR P8 certo, CAM P15 errado
        self.assertEqual(s.bonus_points, 1)
        self.assertEqual(s.total, 12 + 1)
        self.assertEqual(s.bonus_guess, 8)
        self.assertEqual(s.bonus_real_pos, 8)

    def test_maximo_14(self):
        sheet = parse_sheet(TEXTO.replace("P15", "P20"), DRIVERS, PLAYERS)
        s = next(x for x in score_sheet(sheet, Result("Interlagos", ORDEM)) if x.player_id == "guilherme")
        self.assertEqual(s.bonus_points, 2)
        self.assertEqual(s.total, 14)

    def test_camara_fora_do_resultado_vale_zero(self):
        sheet = parse_sheet(TEXTO, DRIVERS, PLAYERS)
        ordem = [c for c in ORDEM if c != "CAM"]
        s = next(x for x in score_sheet(sheet, Result("Interlagos", ordem)) if x.player_id == "paganini")
        self.assertIsNone(s.bonus_detail[1].real_pos)
        self.assertEqual(s.bonus_detail[1].points, 0)


class TestSiteDoisPilotos(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.data, self.docs = base / "data", base / "docs"
        season = self.data / "2026"
        (season / "messages").mkdir(parents=True)
        (season / "results").mkdir(parents=True)
        shutil.copy(RAIZ / "data" / "drivers.json", self.data / "drivers.json")
        for nome in ("players.json", "calendar.json"):
            shutil.copy(RAIZ / "data" / "2026" / nome, season / nome)
        shutil.copy(RAIZ / "data" / "2026" / "messages" / "19.txt", season / "messages" / "19.txt")
        shutil.copy(RAIZ / "data" / "2026" / "results" / "19.json", season / "results" / "19.json")
        (season / "messages" / "20.txt").write_text(TEXTO, encoding="utf-8")
        (season / "results" / "20.json").write_text(
            json.dumps({"race": "São Paulo", "round": 20, "order": ORDEM}), encoding="utf-8")
        generate(self.data, self.docs, 2026)
        ler = lambda n: json.loads((self.docs / "data" / "2026" / n).read_text(encoding="utf-8"))
        self.standings, self.bets = ler("standings.json"), ler("bets.json")

    def tearDown(self):
        self._tmp.cleanup()

    def test_rodada_20_tem_os_dois_e_max_14(self):
        r20 = next(r for r in self.standings["rounds"] if r["round"] == 20)
        self.assertEqual(r20["bonus_drivers"], ["BOR", "CAM"])
        self.assertEqual(r20["max_points"], 14)
        self.assertEqual(r20["bonus_driver"], "BOR")

    def test_rodada_normal_sem_campos_novos(self):
        r19 = next(r for r in self.standings["rounds"] if r["round"] == 19)
        self.assertNotIn("bonus_drivers", r19)
        self.assertNotIn("max_points", r19)
        self.assertNotIn("bonus_detail", self.bets["players"]["guilherme"]["rounds"]["19"])

    def test_bets_com_detalhe_por_piloto(self):
        rd = self.bets["players"]["guilherme"]["rounds"]["20"]
        self.assertEqual(
            rd["bonus_detail"],
            [{"driver": "BOR", "guess": 8, "real_pos": 8, "points": 1},
             {"driver": "CAM", "guess": 15, "real_pos": 20, "points": 0}],
        )
        self.assertEqual(rd["bonus_points"], 1)


if __name__ == "__main__":
    unittest.main()
