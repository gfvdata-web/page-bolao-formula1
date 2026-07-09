import json
import unittest
from pathlib import Path

from bolao.parser import parse_sheet
from bolao.scoring import Result, score_sheet

RAIZ = Path(__file__).resolve().parent.parent
DRIVERS = json.loads((RAIZ / "data" / "drivers.json").read_text(encoding="utf-8"))["aliases"]
PLAYERS = json.loads((RAIZ / "data" / "2026" / "players.json").read_text(encoding="utf-8"))["aliases"]
TEXTO = (RAIZ / "examples" / "silverstone.txt").read_text(encoding="utf-8")
RESULTADO = json.loads((RAIZ / "examples" / "silverstone_result.json").read_text(encoding="utf-8"))

# Conferência manual (ver CONTEXTO.md, seção 2).
ESPERADO = {
    "vinicius": {"top6": 12, "bonus": 1, "total": 13},
    "guilherme": {"top6": 7, "bonus": 0, "total": 7},
    "dalla": {"top6": 6, "bonus": 0, "total": 6},
    "caio_l": {"top6": 3, "bonus": 0, "total": 3},
}


class TestScoreSilverstone(unittest.TestCase):
    def setUp(self):
        sheet = parse_sheet(TEXTO, DRIVERS, PLAYERS)
        result = Result.from_dict(RESULTADO)
        self.scores = {s.player_id: s for s in score_sheet(sheet, result)}

    def test_totais_batem_com_conferencia_manual(self):
        for pid, esp in ESPERADO.items():
            with self.subTest(jogador=pid):
                s = self.scores[pid]
                self.assertEqual(s.top6_points, esp["top6"])
                self.assertEqual(s.bonus_points, esp["bonus"])
                self.assertEqual(s.total, esp["total"])

    def test_palpite_perfeito_bate_no_maximo(self):
        self.assertEqual(self.scores["vinicius"].total, 13)

    def test_ordenacao_por_total(self):
        sheet = parse_sheet(TEXTO, DRIVERS, PLAYERS)
        ordenado = score_sheet(sheet, Result.from_dict(RESULTADO))
        totais = [s.total for s in ordenado]
        self.assertEqual(totais, sorted(totais, reverse=True))


class TestRegrasIsoladas(unittest.TestCase):
    def _score_de(self, top6, bonus_guess, bonus_driver="HAM"):
        texto = "Corrida\nPiloto {}\n\nJoao\n{}\nP{}\n".format(
            bonus_driver, "\n".join(top6), bonus_guess
        )
        sheet = parse_sheet(texto, DRIVERS)
        return score_sheet(sheet, Result.from_dict(RESULTADO))[0]

    def test_posicao_exata_vale_2(self):
        s = self._score_de(["VER", "NOR", "RUS", "HAM", "ANT", "PIA"], 4)
        self.assertEqual(s.top6_points, 12)

    def test_dentro_do_top6_vale_1(self):
        # Todos no top6 real, mas nenhum na posição exata.
        s = self._score_de(["NOR", "VER", "HAM", "RUS", "PIA", "ANT"], 4)
        self.assertEqual(s.top6_points, 6)

    def test_fora_do_top6_vale_0(self):
        s = self._score_de(["LEC", "SAI", "ALO", "GAS", "ALB", "OCO"], 4)
        self.assertEqual(s.top6_points, 0)

    def test_bonus_exato_vale_1(self):
        s = self._score_de(["LEC", "SAI", "ALO", "GAS", "ALB", "OCO"], 4)
        self.assertEqual(s.bonus_points, 1)  # HAM real em P4

    def test_bonus_errado_vale_0(self):
        s = self._score_de(["LEC", "SAI", "ALO", "GAS", "ALB", "OCO"], 5)
        self.assertEqual(s.bonus_points, 0)


if __name__ == "__main__":
    unittest.main()
