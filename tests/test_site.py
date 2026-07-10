"""Testes da Etapa 3 — consolidação de várias rodadas nos dados do site.

Monta um workspace isolado (tmp) com dados sintéticos mínimos e roda
``bolao.site.generate``, verificando o acúmulo entre rodadas, a rodada sem
resultado que é ignorada, a ordenação do ranking e o nome de exibição.
"""

import json
import tempfile
import unittest
from pathlib import Path

from bolao.site import generate

SEASON = 2026

CALENDAR = {
    "season": SEASON,
    "races": [
        {
            "race_id": "2026-01", "season": SEASON, "round": 1,
            "circuit": "test_circ", "race": "Testland", "date": "2026-03-01",
            "sprint": False, "aliases": ["testland"],
        },
        {
            "race_id": "2026-02", "season": SEASON, "round": 2,
            "circuit": "other_circ", "race": "Otherville", "date": "2026-03-08",
            "sprint": True, "aliases": ["otherville"],
        },
    ],
}

PLAYERS = {"aliases": {}, "names": {"joao": "João"}}

# top6 real de cada rodada (índice 0 = P1).
RESULT_1 = {"race": "Testland", "order": ["VER", "NOR", "RUS", "HAM", "ANT", "PIA", "LEC", "SAI"]}
RESULT_2 = {"race": "Otherville", "order": ["NOR", "VER", "RUS", "HAM", "ANT", "PIA", "LEC", "SAI"]}

MSG_1 = (
    "Bolao qualify Testland\n"
    "Piloto VER\n\n"
    "Joao\nVER\nNOR\nRUS\nHAM\nANT\nPIA\nP1\n\n"
    "Maria\nNOR\nVER\nRUS\nHAM\nANT\nPIA\nP2\n"
)

# Rodada 2 exercita cabeçalho "Circuito:", enfeite no piloto, linha em branco
# após o nome (Pedro) e chute P22.
MSG_2 = (
    "Bolão Qualify 2026\n"
    "Circuito: Otherville\n"
    "Piloto escolhido: NOR\n\n"
    "Joao\nVER\nNOR\nRUS\nHAM\nANT\nPIA\nP22\n\n"
    "Pedro\n\nNOR\nVER\nRUS\nHAM\nANT\nPIA\nP1\n"
)

# Rodada 3 tem palpite mas NÃO tem resultado -> deve ser ignorada.
MSG_3 = "Bolao qualify Testland\nPiloto VER\n\nJoao\nVER\nNOR\nRUS\nHAM\nANT\nPIA\nP1\n"


def _write(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(dados, str):
        caminho.write_text(dados, encoding="utf-8")
    else:
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


class TestGenerate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.data = base / "data"
        self.docs = base / "docs"
        season = self.data / str(SEASON)

        _write(self.data / "drivers.json", {"aliases": {}})
        _write(season / "players.json", PLAYERS)
        _write(season / "calendar.json", CALENDAR)
        _write(season / "messages" / "1.txt", MSG_1)
        _write(season / "messages" / "2.txt", MSG_2)
        _write(season / "messages" / "3.txt", MSG_3)
        _write(season / "results" / "1.json", RESULT_1)
        _write(season / "results" / "2.json", RESULT_2)
        # sem results/3.json de propósito

        self.resumo = generate(self.data, self.docs, SEASON)
        self.standings = json.loads(
            (self.docs / "data" / "standings.json").read_text(encoding="utf-8")
        )
        self.bets = json.loads(
            (self.docs / "data" / "bets.json").read_text(encoding="utf-8")
        )
        self.results = json.loads(
            (self.docs / "data" / "results.json").read_text(encoding="utf-8")
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_rodada_sem_resultado_e_ignorada(self):
        self.assertEqual(self.resumo["rounds"], [1, 2])
        self.assertEqual(sorted(self.results["rounds"].keys()), ["1", "2"])

    def test_ranking_acumula_e_ordena(self):
        players = self.standings["players"]
        # r1: joao 13, maria 10 -> min_score r1 = 9 (compensa quem não apostou).
        # r2: joao 10, pedro 13 -> min_score r2 = 9.
        # Joao: 13 (r1) + 10 (r2) = 23 (apostou nas duas, sem compensação).
        # Pedro: 13 (r2) + 9 (compensação r1) = 22.
        # Maria: 10 (r1) + 9 (compensação r2) = 19.
        self.assertEqual([p["player_id"] for p in players], ["joao", "pedro", "maria"])
        self.assertEqual([p["total"] for p in players], [23, 22, 19])
        self.assertEqual([p["position"] for p in players], [1, 2, 3])

    def test_rounds_played_e_per_round(self):
        por_id = {p["player_id"]: p for p in self.standings["players"]}
        self.assertEqual(por_id["joao"]["rounds_played"], 2)
        self.assertEqual(por_id["joao"]["per_round"], {"1": 13, "2": 10})
        self.assertEqual(por_id["maria"]["rounds_played"], 1)
        self.assertEqual(por_id["pedro"]["per_round"], {"2": 13})

    def test_compensacao_pontuacao_minima(self):
        por_id = {p["player_id"]: p for p in self.standings["players"]}
        self.assertEqual(por_id["joao"]["compensated_rounds"], [])
        self.assertEqual(por_id["joao"]["compensation_total"], 0)
        self.assertEqual(por_id["pedro"]["compensated_rounds"], [1])
        self.assertEqual(por_id["pedro"]["compensation_total"], 9)
        self.assertEqual(por_id["maria"]["compensated_rounds"], [2])
        self.assertEqual(por_id["maria"]["compensation_total"], 9)
        self.assertEqual(self.standings["rounds"][0]["min_score"], 9)
        self.assertEqual(self.standings["rounds"][1]["min_score"], 9)

    def test_top6_e_bonus_totais(self):
        joao = next(p for p in self.standings["players"] if p["player_id"] == "joao")
        self.assertEqual(joao["top6_total"], 22)  # 12 + 10
        self.assertEqual(joao["bonus_total"], 1)  # acertou VER em P1 na r1

    def test_media_por_rodada_ignora_compensacao(self):
        por_id = {p["player_id"]: p for p in self.standings["players"]}
        # joao: 22 top6 + 1 bonus = 23 pontos apostados em 2 rodadas -> 11.5
        self.assertEqual(por_id["joao"]["avg_points"], 11.5)
        # pedro: apostou só na r2 (13 pts), r1 foi compensação -> não conta.
        self.assertEqual(por_id["pedro"]["rounds_played"], 1)
        self.assertEqual(por_id["pedro"]["avg_points"], 13.0)

    def test_nome_de_exibicao(self):
        por_id = {p["player_id"]: p for p in self.standings["players"]}
        self.assertEqual(por_id["joao"]["name"], "João")  # override em players.json
        self.assertEqual(por_id["maria"]["name"], "Maria")  # fallback do bruto

    def test_bets_detalhe_por_posicao(self):
        joao_r1 = self.bets["players"]["joao"]["rounds"]["1"]
        self.assertEqual(joao_r1["total"], 13)
        self.assertEqual(len(joao_r1["top6_detail"]), 6)
        self.assertTrue(all(d["points"] == 2 for d in joao_r1["top6_detail"]))
        self.assertEqual(joao_r1["bonus_driver"], "VER")

    def test_chute_p22_preservado_pontua_zero(self):
        joao_r2 = self.bets["players"]["joao"]["rounds"]["2"]
        self.assertEqual(joao_r2["bonus_guess"], 22)
        self.assertEqual(joao_r2["bonus_points"], 0)


if __name__ == "__main__":
    unittest.main()
