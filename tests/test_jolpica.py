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


class TestEquipesQuali(unittest.TestCase):
    """`equipes`: nome da equipe (Constructor) de cada piloto no quali."""

    def test_fixture_tem_equipe_de_todos(self):
        res = J.build_result(_fx("qualifying_2026_1.json"), 2026, 1)
        self.assertEqual(set(res["equipes"]), set(res["order"]))
        self.assertEqual(res["equipes"]["RUS"], "Mercedes")
        self.assertEqual(res["equipes"]["HAD"], "Red Bull")

    def test_nome_curto_sem_sufixo(self):
        self.assertEqual(J.nome_equipe("Alpine F1 Team"), "Alpine")
        self.assertEqual(J.nome_equipe("RB F1 Team"), "RB")
        self.assertEqual(J.nome_equipe("Ferrari"), "Ferrari")


class TestFasesQuali(unittest.TestCase):
    """`fases`: até que fase (Q1/Q2/Q3) cada piloto foi, como na sessão."""

    def test_fixture_tem_10_no_q3(self):
        res = J.build_result(_fx("qualifying_2026_1.json"), 2026, 1)
        self.assertEqual(set(res["fases"]), set(res["order"]))
        self.assertEqual(sum(1 for f in res["fases"].values() if f == 3), 10)

    def test_fase_pela_chave_da_sessao(self):
        self.assertEqual(J.fase_sessao({"Q1": "1:30", "Q2": "", "Q3": ""}), 3)
        self.assertEqual(J.fase_sessao({"Q1": "1:30", "Q2": ""}), 2)
        self.assertEqual(J.fase_sessao({"Q1": ""}), 1)
        self.assertIsNone(J.fase_sessao({}))

    def test_sem_tempo_no_q3_e_promovido(self):
        # Sainz em Imola 2022: bateu no Q3, a Jolpica não traz a chave Q3.
        order = [f"P{i:02d}" for i in range(1, 21)]
        fases = {c: (3 if i < 9 else 2 if i < 15 else 1) for i, c in enumerate(order)}
        res = J.completar_fases(order, fases, 2022)
        self.assertEqual(res["P10"], 3)
        self.assertEqual(res["P15"], 2)  # Q2 também tinha 1 faltando
        self.assertEqual(res["P16"], 1)

    def test_desclassificado_mantem_fase_da_sessao(self):
        # Correu o Q3 e foi desclassificado (último no grid): continua Q3, e
        # quem subiu para P10 sem ter ido ao Q3 continua Q2.
        order = [f"P{i:02d}" for i in range(1, 21)]
        fases = {c: (3 if i < 9 else 2 if i < 14 else 1) for i, c in enumerate(order)}
        fases["P20"] = 3
        res = J.completar_fases(order, fases, 2024)
        self.assertEqual(res["P20"], 3)
        self.assertEqual(res["P10"], 2)
        self.assertEqual(sum(1 for f in res.values() if f == 3), 10)

    def test_2026_q2_vai_ate_p16(self):
        order = [f"P{i:02d}" for i in range(1, 23)]
        fases = {c: (3 if i < 10 else 2 if i < 15 else 1) for i, c in enumerate(order)}
        res = J.completar_fases(order, fases, 2026)
        self.assertEqual(res["P16"], 2)
        self.assertEqual(res["P17"], 1)


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
