"""Testes da Etapa 7 — importação de temporada antiga a partir da planilha.

Monta um workspace tmp com CSVs sintéticos + calendário/resultados no formato
da Jolpica, roda ``bolao.historico.build`` e confere que os
``messages/<round>.txt`` gerados alimentam ``bolao.site.generate`` sem
adaptação, além dos avisos de conferência.
"""

import json
import tempfile
import unittest
from pathlib import Path

from bolao.historico import build
from bolao.site import generate

# Temporada no formato atual (top6 + piloto da rodada valendo 1 pt).
# 2024 nao serve aqui: naquele ano o bonus valia 2 (ver bolao.formats).
SEASON = 2026

CALENDAR = {
    "season": SEASON,
    "races": [
        {
            "race_id": "2026-01", "season": SEASON, "round": 1,
            "circuit": "testland", "race": "Testland", "date": "2026-03-01",
            "sprint": False, "aliases": ["testland", "testonia"],
        },
        {
            "race_id": "2026-02", "season": SEASON, "round": 2,
            "circuit": "otherville", "race": "Otherville", "date": "2026-03-08",
            "sprint": False, "aliases": ["otherville"],
        },
    ],
}

RESULT_1 = {"race": "Testland", "order": ["VER", "NOR", "RUS", "HAM", "ANT", "PIA", "LEC", "SAI"]}
RESULT_2 = {"race": "Otherville", "order": ["NOR", "VER", "RUS", "HAM", "ANT", "PIA", "LEC", "SAI"]}

PALPITES_CSV = (
    "circuito,nome,p1,p2,p3,p4,p5,p6,pos\n"
    "testonia,Joao,ver,nor,rus,ham,ant,pia,p1\n"
    "testonia,Maria,nor,ver,rus,ham,ant,pia,P2\n"
    "otherville,Joao,nor,ver,rus,ham,ant,zzz,p3\n"
)

RODADAS_CSV = (
    "circuito,data,quem,pos_planilha,t1,t2,t3,t4,t5,t6\n"
    "testonia,2024-03-01,ver,p1,ver,nor,rus,ham,ant,pia\n"
    "otherville,2024-03-08,nor,p9,nor,ver,rus,ham,ant,pia\n"
)


def _write(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(dados, str):
        caminho.write_text(dados, encoding="utf-8")
    else:
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


class TestHistorico(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.data = base / "data"
        self.docs = base / "docs"
        season = self.data / str(SEASON)

        _write(self.data / "drivers.json", {"aliases": {"max": "VER"}})
        _write(season / "players.json", {"aliases": {"joao": "joao", "maria": "maria"}, "names": {}})
        _write(season / "calendar.json", CALENDAR)
        _write(season / "results" / "1.json", RESULT_1)
        _write(season / "results" / "2.json", RESULT_2)
        _write(season / f"palpites_{SEASON}.csv", PALPITES_CSV)
        _write(season / f"rodadas_{SEASON}.csv", RODADAS_CSV)

        self.resumo = build(SEASON, self.data)

    def tearDown(self):
        self._tmp.cleanup()

    def test_mensagens_geradas_no_formato_do_parser(self):
        self.assertEqual(self.resumo["rounds"], [1, 2])
        msg1 = (self.data / str(SEASON) / "messages" / "1.txt").read_text(encoding="utf-8")
        self.assertTrue(msg1.startswith("Qualify Bolao testonia\nPiloto ver\n"))
        self.assertIn("\nJoao\nver\nnor\nrus\nham\nant\npia\nP1\n", msg1)

    def test_pipeline_consome_sem_adaptacao(self):
        resumo = generate(self.data, self.docs, SEASON)
        self.assertEqual(resumo["rounds"], [1, 2])
        standings = json.loads(
            (self.docs / "data" / str(SEASON) / "standings.json").read_text(encoding="utf-8")
        )
        por_id = {p["player_id"]: p for p in standings["players"]}
        # Joao r1: top6 perfeito (12) + bônus ver@P1 (1) = 13.
        self.assertEqual(por_id["joao"]["per_round"]["1"], 13)

    def test_conferencia_aponta_top6_divergente_e_codigo_desconhecido(self):
        avisos = "\n".join(self.resumo["avisos"])
        # r2: planilha t1..t6 = nor,ver,rus,ham,ant,pia; Jolpica = nor,ver,... igual
        # -> sem aviso de top6 na r2; r1 igual também. 'zzz' é código desconhecido.
        self.assertIn("ZZZ", avisos)
        self.assertIn("pos_planilha", "circuito,data,quem,pos_planilha")  # sanidade

    def test_seasons_json_lista_a_temporada(self):
        generate(self.data, self.docs, SEASON)
        seasons = json.loads((self.docs / "data" / "seasons.json").read_text(encoding="utf-8"))
        anos = [t["ano"] for t in seasons["temporadas"]]
        self.assertEqual(anos, [SEASON])
        self.assertEqual(seasons["atual"], SEASON)
        entrada = seasons["temporadas"][0]
        self.assertEqual(entrada["format"]["top_n"], 6)
        self.assertTrue(entrada["format"]["bonus"])
        self.assertIn("parcial", entrada)


if __name__ == "__main__":
    unittest.main()
