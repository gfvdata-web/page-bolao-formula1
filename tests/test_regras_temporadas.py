"""Regras de pontuação por temporada, com valores esperados fixos.

Fixa em teste o que o ``bolao/formats.py`` e o ``bolao/site.py`` decidiram para
cada ano (ver contexto/etapas/etapa-7-historico.md): top5 sem bônus em 2021 com
desempate por média, bônus de 2 pts em 2024, compensação só em 2025+, placar
publicado mandando sobre a conta, ``ranking_final`` fixando a classificação e
saldo inicial/pontos avulsos. Tudo em workspace temporário.
"""

import json
import tempfile
import unittest
from pathlib import Path

from bolao.formats import ATUAL, FORMATS, season_format
from bolao.parser import parse_sheet
from bolao.scoring import Result, score_bet, score_sheet
from bolao.site import generate

ORDER = ["VER", "NOR", "RUS", "HAM", "ANT", "PIA", "LEC", "SAI", "ALO", "GAS"]


def _w(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        dados if isinstance(dados, str) else json.dumps(dados, ensure_ascii=False), encoding="utf-8"
    )


class TestFormatos(unittest.TestCase):
    def test_maximo_por_temporada(self):
        esperado = {2021: 10, 2022: 12, 2023: 12, 2024: 14, 2025: 13, 2026: 13}
        self.assertEqual({a: season_format(a).max_points for a in esperado}, esperado)

    def test_top_n_bonus_e_compensacao(self):
        self.assertEqual((season_format(2021).top_n, season_format(2021).bonus), (5, False))
        for ano in (2022, 2023):
            self.assertEqual((season_format(ano).top_n, season_format(ano).bonus), (6, False))
        self.assertEqual(season_format(2024).bonus_points, 2)
        for ano in (2021, 2022, 2023, 2024):
            self.assertFalse(season_format(ano).compensation, ano)
        for ano in (2025, 2026):
            self.assertTrue(season_format(ano).compensation, ano)

    def test_desempate_por_media_so_em_2021(self):
        self.assertEqual(season_format(2021).tiebreak, "media")
        self.assertTrue(all(f.tiebreak == "player_id" for a, f in FORMATS.items() if a != 2021))

    def test_ano_desconhecido_usa_o_formato_atual(self):
        self.assertIs(season_format(2031), ATUAL)
        self.assertEqual(ATUAL.max_points, 13)


class TestPontuacaoPorFormato(unittest.TestCase):
    RESULT = Result(race="Fixture", order=ORDER)

    def _bet(self, top, guess, piloto="HAM"):
        texto = "Corrida\nPiloto {}\n\nJoao\n{}\nP{}\n".format(piloto, "\n".join(top), guess)
        return parse_sheet(texto, {}, top_n=len(top)).bets[0], piloto

    def test_top5_2021_perfeito_vale_10(self):
        bet, _ = self._bet(ORDER[:5], 4)
        s = score_bet(bet, self.RESULT, bonus_driver="", bonus_points=0)
        self.assertEqual((s.top6_points, s.bonus_points, s.total), (10, 0, 10))

    def test_top5_ignora_a_sexta_posicao_real(self):
        # PIA é P6 real: fora do top5 que vale em 2021 -> 0 pt
        bet, _ = self._bet(["VER", "NOR", "RUS", "HAM", "PIA"], 1)
        s = score_bet(bet, self.RESULT, bonus_driver="", bonus_points=0)
        self.assertEqual(s.total, 8)

    def test_bonus_de_2024_vale_2(self):
        bet, piloto = self._bet(ORDER[:6], 4)  # HAM é P4
        s = score_bet(bet, self.RESULT, bonus_driver=piloto, bonus_points=2)
        self.assertEqual((s.top6_points, s.bonus_points, s.total), (12, 2, 14))

    def test_bonus_de_2025_vale_1(self):
        bet, piloto = self._bet(ORDER[:6], 4)
        s = score_bet(bet, self.RESULT, bonus_driver=piloto, bonus_points=1)
        self.assertEqual(s.total, 13)

    def test_bonus_errado_ou_piloto_fora_do_grid_vale_0(self):
        bet, piloto = self._bet(ORDER[:6], 3)
        self.assertEqual(score_bet(bet, self.RESULT, piloto, 2).bonus_points, 0)
        self.assertEqual(score_bet(bet, self.RESULT, "ZZZ", 2).bonus_points, 0)
        self.assertIsNone(score_bet(bet, self.RESULT, "ZZZ", 2).bonus_real_pos)

    def test_resultado_curto_nao_quebra(self):
        bet, piloto = self._bet(ORDER[:6], 4)
        curto = Result(race="x", order=ORDER[:3])
        s = score_bet(bet, curto, piloto, 1)
        self.assertEqual(s.top6_points, 6)  # 3 exatas, o resto fora

    def test_resultado_sem_order_e_erro(self):
        with self.assertRaises(ValueError):
            Result.from_dict({"race": "x"})

    def test_ordenacao_desempata_por_player_id(self):
        texto = "Corrida\nPiloto HAM\n\nZe\n{0}\nP4\n\nAna\n{0}\nP4\n".format("\n".join(ORDER[:6]))
        scores = score_sheet(parse_sheet(texto, {}), self.RESULT)
        self.assertEqual([s.player_id for s in scores], sorted(s.player_id for s in scores))


class _Workspace(unittest.TestCase):
    """Monta data/ sintético de UMA temporada e gera o site em tmp."""

    ANO = 2021

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.data, self.docs = base / "data", base / "docs"
        self.season = self.data / str(self.ANO)
        _w(self.data / "drivers.json", {"aliases": {}})
        _w(self.season / "players.json", {"aliases": {}, "names": {}})
        _w(self.season / "calendar.json", {
            "season": self.ANO,
            "races": [
                {"race_id": f"{self.ANO}-0{n}", "season": self.ANO, "round": n, "circuit": f"c{n}",
                 "race": nome, "date": f"{self.ANO}-03-0{n}", "sprint": False, "aliases": [nome.lower()]}
                for n, nome in ((1, "Alfaville"), (2, "Betaburgo"))
            ],
        })
        for n, nome in ((1, "Alfaville"), (2, "Betaburgo")):
            _w(self.season / "results" / f"{n}.json", {"race": nome, "order": ORDER})

    def tearDown(self):
        self._tmp.cleanup()

    def gerar(self):
        generate(self.data, self.docs, self.ANO)
        saida = self.docs / "data" / str(self.ANO)
        self.standings = json.loads((saida / "standings.json").read_text(encoding="utf-8"))
        self.por_id = {p["player_id"]: p for p in self.standings["players"]}
        return self.standings

    def mensagem(self, rodada, nome, corpos):
        _w(self.season / "messages" / f"{rodada}.txt", f"Qualify {nome}\n\n" + "\n\n".join(corpos) + "\n")


class TestTemporada2021(_Workspace):
    ANO = 2021

    def test_top5_sem_bonus_sem_compensacao(self):
        perfeito = "\n".join(ORDER[:5])
        pior = "\n".join(["ALO", "GAS", "AAA", "BBB", "CCC"])
        self.mensagem(1, "Alfaville", [f"Ana\n{perfeito}", f"Bia\n{pior}"])
        self.mensagem(2, "Betaburgo", [f"Ana\n{perfeito}"])
        st = self.gerar()
        self.assertEqual(st["format"]["top_n"], 5)
        self.assertFalse(st["format"]["bonus"])
        self.assertEqual(self.por_id["ana"]["total"], 20)
        # Bia faltou à rodada 2 e NÃO ganha compensação em 2021
        self.assertEqual(self.por_id["bia"]["total"], 0)
        self.assertEqual(self.por_id["bia"]["compensation_total"], 0)

    def test_empate_desempata_pela_media(self):
        cheio = "\n".join(ORDER[:5])  # 10 pts
        quatro = "\n".join(["VER", "NOR", "ZZZ", "YYY", "XXX"])  # 4 pts
        seis = "\n".join(["VER", "NOR", "RUS", "YYY", "XXX"])  # 6 pts
        self.mensagem(1, "Alfaville", [f"Ana\n{cheio}", f"Bia\n{quatro}"])
        self.mensagem(2, "Betaburgo", [f"Bia\n{seis}", f"Cai\n{cheio}"])
        # Todos fecham com 10: Ana e Cai em 1 rodada (média 10), Bia em 2 (média 5).
        # Pelo id, Bia viria antes de Cai; pela média (regra de 2021), Cai vem antes.
        st = self.gerar()
        self.assertEqual([p["total"] for p in st["players"]], [10, 10, 10])
        self.assertEqual([p["player_id"] for p in st["players"]], ["ana", "cai", "bia"])

    def test_saldo_inicial_soma_pontos_e_rodadas(self):
        self.mensagem(1, "Alfaville", [f"Ana\n" + "\n".join(ORDER[:5])])
        _w(self.season / "saldo_inicial.json", {"players": {"ana": {"pontos": 50, "rodadas": 10}, "bia": {"pontos": 30, "rodadas": 9}}})
        self.gerar()
        self.assertEqual(self.por_id["ana"]["total"], 60)
        self.assertEqual(self.por_id["ana"]["carry_points"], 50)
        self.assertEqual(self.por_id["ana"]["carry_rounds"], 10)
        self.assertEqual(self.por_id["bia"]["total"], 30)
        self.assertEqual([p["player_id"] for p in self.standings["players"]], ["ana", "bia"])

    def test_placar_publicado_manda_sobre_a_conta(self):
        self.mensagem(1, "Alfaville", [f"Ana\n" + "\n".join(ORDER[:5])])
        _w(self.season / "placar_publicado.json", {"rounds": {"1": {"players": {"ana": 7}}}})
        self.gerar()
        self.assertEqual(self.por_id["ana"]["total"], 7)
        # o intermediário scores/<rodada>.json guarda o que a regra da temporada daria
        score = json.loads((self.season / "scores" / "1.json").read_text(encoding="utf-8"))["players"][0]
        self.assertEqual((score["total"], score["total_recalculado"]), (7, 10))

    def test_ranking_final_fixa_ordem_e_pontos(self):
        a = "\n".join(ORDER[:5])
        self.mensagem(1, "Alfaville", [f"Ana\n{a}", f"Bia\n{a}"])
        _w(self.season / "ranking_final.json", {"ordem": ["bia", "ana"], "pontos": {"ana": 99}})
        self.gerar()
        self.assertEqual([p["player_id"] for p in self.standings["players"]], ["bia", "ana"])
        self.assertEqual(self.por_id["ana"]["total"], 99)
        self.assertEqual(self.por_id["ana"]["total_somado"], 10)

    def test_pontos_avulsos_so_entram_quando_autorizados(self):
        self.mensagem(1, "Alfaville", [f"Ana\n" + "\n".join(ORDER[:5])])
        avulso = {"rounds": {"2": {"players": {"ana": 6}}}}
        _w(self.season / "pontos_avulsos.json", {"incluir_no_ranking": False, **avulso})
        self.gerar()
        self.assertEqual(self.por_id["ana"]["total"], 10)
        _w(self.season / "pontos_avulsos.json", {"incluir_no_ranking": True, **avulso})
        self.gerar()
        self.assertEqual(self.por_id["ana"]["total"], 16)
        self.assertEqual(self.por_id["ana"]["avulsos_points"], 6)
        self.assertEqual(self.por_id["ana"]["per_round"]["2"], 6)

    def test_cabecalho_que_resolve_outra_rodada_e_erro(self):
        self.mensagem(2, "Alfaville", [f"Ana\n" + "\n".join(ORDER[:5])])  # arquivo 2, corrida da rodada 1
        with self.assertRaisesRegex(ValueError, "resolve para a rodada 1"):
            self.gerar()


class TestTemporada2024(_Workspace):
    ANO = 2024

    def test_bonus_de_2_pontos_e_maximo_14(self):
        corpo = "Ana\n" + "\n".join(ORDER[:6]) + "\nP4"
        _w(self.season / "messages" / "1.txt", "Qualify Alfaville\nPiloto HAM\n\n" + corpo + "\n")
        st = self.gerar()
        self.assertEqual(st["format"]["max_points"], 14)
        self.assertEqual(self.por_id["ana"]["total"], 14)
        self.assertEqual(self.por_id["ana"]["bonus_total"], 2)
        self.assertEqual(self.por_id["ana"]["avg_points"], 14.0)

    def test_sem_compensacao_quem_falta_nao_pontua(self):
        c = "\n".join(ORDER[:6])
        _w(self.season / "messages" / "1.txt", f"Qualify Alfaville\nPiloto HAM\n\nAna\n{c}\nP4\n\nBia\n{c}\nP4\n")
        _w(self.season / "messages" / "2.txt", f"Qualify Betaburgo\nPiloto HAM\n\nAna\n{c}\nP4\n")
        self.gerar()
        self.assertEqual(self.por_id["bia"]["total"], 14)
        self.assertEqual(self.por_id["bia"]["compensated_rounds"], [])


if __name__ == "__main__":
    unittest.main()
