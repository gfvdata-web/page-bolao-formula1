"""Testes do resolvedor de corrida (nome do cabeçalho -> rodada/race_id).

Offline: usa o `calendar.json` gerado da fixture da Jolpica, sem rede.
"""

import unittest
from pathlib import Path

from bolao import jolpica as J
from bolao.calendar import AmbiguousRace, RaceNotFound, resolve_race
from bolao.parser import parse_sheet

RAIZ = Path(__file__).resolve().parent.parent
FIXTURES = RAIZ / "tests" / "fixtures" / "jolpica"


class TestResolveRace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json

        season = json.loads((FIXTURES / "season_2026.json").read_text(encoding="utf-8"))
        cls.cal = J.build_calendar(season, 2026)

    def test_por_circuito(self):
        r = resolve_race("Silverstone", self.cal)
        self.assertEqual(r["round"], 9)
        self.assertEqual(r["race_id"], "2026-09")

    def test_por_cidade_e_variacoes(self):
        self.assertEqual(resolve_race("Interlagos", self.cal)["round"], 19)
        self.assertEqual(resolve_race("Sao Paulo", self.cal)["round"], 19)
        self.assertEqual(resolve_race("São Paulo", self.cal)["round"], 19)

    def test_por_pais(self):
        self.assertEqual(resolve_race("Monaco", self.cal)["round"], 6)

    def test_nome_ambiguo_falha(self):
        # "Spain" serve para Barcelona (7) e Madrid (14) em 2026.
        with self.assertRaises(AmbiguousRace):
            resolve_race("Spain", self.cal)

    def test_nome_desconhecido_falha(self):
        with self.assertRaises(RaceNotFound):
            resolve_race("Nurburgring", self.cal)

    def test_integracao_com_o_parser(self):
        # O parser da Etapa 1 já isola o nome ("Qualify Bolao X" -> "X").
        texto = "Qualify Bolao Monaco\nPiloto Leclerc\n\nJoao\nLEC\nHAM\nRUS\nNOR\nPIA\nALO\nP3\n"
        sheet = parse_sheet(texto)
        r = resolve_race(sheet.race, self.cal)
        self.assertEqual(r["round"], 6)
        self.assertEqual(r["race_id"], "2026-06")


if __name__ == "__main__":
    unittest.main()
