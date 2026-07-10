"""Testes da Etapa 2 (integração Jolpica) — offline, com fixtures.

As fixtures em ``tests/fixtures/jolpica/`` são respostas reais da Jolpica-F1
salvas em arquivo. Assim os testes rodam sem rede (e sem chamar a API no CI):
exercitam só as funções de transformação `build_*`, não a camada `fetch_*`.
"""

import json
import unittest
from pathlib import Path

from bolao import jolpica as J
from bolao.parser import parse_sheet
from bolao.scoring import Result, score_sheet

RAIZ = Path(__file__).resolve().parent.parent
FIXTURES = RAIZ / "tests" / "fixtures" / "jolpica"


def _fx(nome: str) -> dict:
    return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))


class TestRaceId(unittest.TestCase):
    def test_formato_zero_a_esquerda(self):
        self.assertEqual(J.race_id(2026, 1), "2026-01")
        self.assertEqual(J.race_id(2026, 12), "2026-12")


class TestBuildCalendar(unittest.TestCase):
    def setUp(self):
        self.cal = J.build_calendar(_fx("season_2026.json"), 2026)
        self.by_round = {r["round"]: r for r in self.cal["races"]}

    def test_todas_as_corridas(self):
        self.assertEqual(len(self.cal["races"]), 22)
        self.assertEqual(self.cal["season"], 2026)

    def test_campos_obrigatorios_e_race_id(self):
        r1 = self.by_round[1]
        self.assertEqual(r1["race_id"], "2026-01")
        self.assertEqual(r1["circuit"], "albert_park")
        self.assertEqual(r1["race"], "Melbourne")
        self.assertEqual(r1["date"], "2026-03-08")
        self.assertEqual(r1["qualifying_utc"], "2026-03-07T05:00:00Z")

    def test_flag_de_sprint(self):
        # Fins de semana de Sprint em 2026: 2, 4, 5, 9, 12, 16 (o resto não).
        sprints = {r["round"] for r in self.cal["races"] if r["sprint"]}
        self.assertEqual(sprints, {2, 4, 5, 9, 12, 16})

    def test_aliases_normalizados(self):
        # Silverstone é fim de semana de Sprint, mas o quali principal conta.
        r9 = self.by_round[9]
        self.assertIn("silverstone", r9["aliases"])
        self.assertIn("british grand prix", r9["aliases"])


class TestBuildDrivers(unittest.TestCase):
    def setUp(self):
        self.drivers = J.build_drivers(_fx("drivers_2026.json"))
        self.aliases = self.drivers["aliases"]

    def test_codigo_sobrenome_e_nome_completo(self):
        self.assertEqual(self.aliases["ham"], "HAM")
        self.assertEqual(self.aliases["hamilton"], "HAM")
        self.assertEqual(self.aliases["lewis hamilton"], "HAM")
        self.assertEqual(self.aliases["george russell"], "RUS")

    def test_reservas_sem_codigo_sao_ignorados(self):
        # 'paul_aron' e outros reservas não têm código oficial -> não entram.
        self.assertNotIn("paul aron", self.aliases)
        self.assertNotIn("aron", self.aliases)

    def test_chaves_normalizadas(self):
        for chave in self.aliases:
            self.assertEqual(chave, chave.lower())
            self.assertNotIn("  ", chave)


class TestBuildResult(unittest.TestCase):
    def test_formato_da_etapa1(self):
        res = J.build_result(_fx("qualifying_2026_1.json"), 2026, 1)
        self.assertEqual(res["race_id"], "2026-01")
        self.assertEqual(res["season"], 2026)
        self.assertEqual(res["round"], 1)
        self.assertEqual(res["circuit"], "albert_park")
        self.assertEqual(res["race"], "Melbourne")
        self.assertEqual(res["order"][0], "RUS")  # pole em Melbourne
        self.assertTrue(all(len(c) == 3 for c in res["order"]))

    def test_quali_indisponivel_falha_claro(self):
        with self.assertRaises(J.ResultUnavailable):
            J.build_result(_fx("qualifying_2026_empty.json"), 2026, 22)


class TestContratoComEtapa1(unittest.TestCase):
    """O resultado gerado alimenta a pontuação da Etapa 1 sem adaptação."""

    def test_palpite_perfeito_pontua_13(self):
        res = J.build_result(_fx("qualifying_2026_1.json"), 2026, 1)
        drivers = J.build_drivers(_fx("drivers_2026.json"))["aliases"]
        top6 = res["order"][:6]
        # Palpite perfeito: top6 = grid real + bônus certo (pole em P1).
        texto = (
            "Qualify Bolao Melbourne\nPiloto Russell\n\n"
            "Teste\n" + "\n".join(top6) + "\nP1\n"
        )
        sheet = parse_sheet(texto, drivers)
        score = score_sheet(sheet, Result.from_dict(res))[0]
        self.assertEqual(score.top6_points, 12)
        self.assertEqual(score.bonus_points, 1)
        self.assertEqual(score.total, 13)


if __name__ == "__main__":
    unittest.main()
