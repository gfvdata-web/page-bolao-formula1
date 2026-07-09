"""Testes da Etapa 5 — pipeline completo acionado pelo Actions.

Workspace isolado (tmp), como em ``test_site.py``. A busca na Jolpica é
mockada (``fetch_result_if_missing``/``fetch_result``) para os testes
rodarem offline.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bolao import pipeline as P
from bolao.calendar import AmbiguousRace, RaceNotFound
from bolao.jolpica import ResultUnavailable

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
            "sprint": False, "aliases": ["otherville"],
        },
    ],
}

RESULT_1 = {"race": "Testland", "order": ["VER", "NOR", "RUS", "HAM", "ANT", "PIA", "LEC", "SAI"]}

MSG_1 = (
    "Bolao qualify Testland\n"
    "Piloto VER\n\n"
    "Joao\nVER\nNOR\nRUS\nHAM\nANT\nPIA\nP1\n\n"
    "Maria\nNOR\nVER\nRUS\nHAM\nANT\nPIA\nP2\n"
)


def _write(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(dados, str):
        caminho.write_text(dados, encoding="utf-8")
    else:
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.data = base / "data"
        self.docs = base / "docs"
        season = self.data / str(SEASON)

        _write(self.data / "drivers.json", {"aliases": {}})
        _write(season / "players.json", {"aliases": {}, "names": {}})
        _write(season / "calendar.json", CALENDAR)

    def test_resolve_round_pelo_cabecalho(self):
        rodada = P.resolve_round(MSG_1, self.data, SEASON)
        self.assertEqual(rodada, 1)

    def test_resolve_round_corrida_desconhecida(self):
        texto = "Bolao qualify Marciolandia\nPiloto VER\n\nJoao\nVER\nNOR\nRUS\nHAM\nANT\nPIA\nP1\n"
        with self.assertRaises(RaceNotFound):
            P.resolve_round(texto, self.data, SEASON)

    def test_run_com_resultado_disponivel(self):
        with mock.patch("bolao.pipeline.fetch_result", return_value=RESULT_1):
            resumo = P.run(MSG_1, None, SEASON, self.data, self.docs)

        self.assertEqual(resumo["round"], 1)
        self.assertEqual(resumo["resultado"], "gravado")
        self.assertEqual(resumo["site"]["rounds"], [1])

        msg_path = self.data / str(SEASON) / "messages" / "1.txt"
        self.assertEqual(msg_path.read_text(encoding="utf-8"), MSG_1)
        self.assertTrue((self.data / str(SEASON) / "results" / "1.json").exists())
        self.assertTrue((self.docs / "data" / "standings.json").exists())

    def test_run_com_round_explicito_ignora_cabecalho(self):
        with mock.patch("bolao.pipeline.fetch_result", return_value=RESULT_1):
            resumo = P.run(MSG_1, 1, SEASON, self.data, self.docs)
        self.assertEqual(resumo["round"], 1)

    def test_run_resultado_indisponivel_nao_falha_mas_nao_consolida(self):
        with mock.patch("bolao.pipeline.fetch_result", side_effect=ResultUnavailable("sem resultado")):
            resumo = P.run(MSG_1, None, SEASON, self.data, self.docs)

        self.assertEqual(resumo["resultado"], "indisponivel")
        self.assertEqual(resumo["site"]["rounds"], [])
        msg_path = self.data / str(SEASON) / "messages" / "1.txt"
        self.assertTrue(msg_path.exists())
        self.assertFalse((self.data / str(SEASON) / "results" / "1.json").exists())

    def test_retry_depois_de_run_indisponivel(self):
        with mock.patch("bolao.pipeline.fetch_result", side_effect=ResultUnavailable("sem resultado")):
            P.run(MSG_1, None, SEASON, self.data, self.docs)

        with mock.patch("bolao.pipeline.fetch_result", return_value=RESULT_1):
            resumo = P.retry(1, SEASON, self.data, self.docs)

        self.assertEqual(resumo["resultado"], "gravado")
        self.assertEqual(resumo["site"]["rounds"], [1])

    def test_retry_sem_mensagem_gravada_falha(self):
        with self.assertRaises(FileNotFoundError):
            P.retry(99, SEASON, self.data, self.docs)

    def test_run_resultado_ja_existente_nao_busca_de_novo(self):
        _write(self.data / str(SEASON) / "results" / "1.json", RESULT_1)
        with mock.patch("bolao.pipeline.fetch_result") as fetch_mock:
            resumo = P.run(MSG_1, None, SEASON, self.data, self.docs)
        fetch_mock.assert_not_called()
        self.assertEqual(resumo["resultado"], "ja_existia")


if __name__ == "__main__":
    unittest.main()
