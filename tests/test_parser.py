import json
import unittest
from pathlib import Path

from bolao.parser import ParseError, parse_sheet

RAIZ = Path(__file__).resolve().parent.parent
DRIVERS = json.loads((RAIZ / "data" / "drivers.json").read_text(encoding="utf-8"))["aliases"]
PLAYERS = json.loads((RAIZ / "data" / "2026" / "players.json").read_text(encoding="utf-8"))["aliases"]
TEXTO = (RAIZ / "examples" / "silverstone.txt").read_text(encoding="utf-8")


class TestParseSilverstone(unittest.TestCase):
    def setUp(self):
        self.sheet = parse_sheet(TEXTO, DRIVERS, PLAYERS)

    def test_cabecalho(self):
        self.assertEqual(self.sheet.race, "Silverstone")
        self.assertEqual(self.sheet.bonus_driver, "HAM")

    def test_quantidade_de_jogadores(self):
        self.assertEqual(len(self.sheet.bets), 4)

    def test_normaliza_top6(self):
        vini = next(b for b in self.sheet.bets if b.player_id == "vinicius")
        self.assertEqual(vini.top6, ["VER", "NOR", "RUS", "HAM", "ANT", "PIA"])

    def test_nomes_completos_viram_codigo(self):
        caio = next(b for b in self.sheet.bets if b.player_id == "caio_l")
        self.assertEqual(caio.top6, ["HAM", "VER", "PIA", "LEC", "SAI", "ALO"])

    def test_chute_bonus(self):
        gui = next(b for b in self.sheet.bets if b.player_id == "guilherme")
        self.assertEqual(gui.bonus_guess, 1)


class TestParseErros(unittest.TestCase):
    def test_bloco_incompleto(self):
        texto = "Corrida\nPiloto Hamilton\n\nJoao\nVER\nNOR\nP1\n"
        with self.assertRaises(ParseError):
            parse_sheet(texto, DRIVERS)

    def test_bonus_invalido(self):
        texto = "Corrida\nPiloto Hamilton\n\nJoao\nVER\nNOR\nRUS\nHAM\nANT\nPIA\nPX\n"
        with self.assertRaises(ParseError):
            parse_sheet(texto, DRIVERS)


if __name__ == "__main__":
    unittest.main()
