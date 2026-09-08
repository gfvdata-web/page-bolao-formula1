"""Testes da Etapa 5 — pipeline completo acionado pelo Actions.

Workspace isolado (tmp), como em ``test_site.py``. A busca na Jolpica é
mockada (``fetch_result_if_missing``/``fetch_result``) para os testes
rodarem offline.
"""

import contextlib
import io
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
        self.assertTrue((self.docs / "data" / str(SEASON) / "standings.json").exists())

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


class TestPipelineCLI(unittest.TestCase):
    """Contrato que o workflow do Actions consome: código de saída + --json.

    O "verificador" do `.github/workflows/pipeline.yml` decide se fica de
    vigília olhando o código 2, e descobre a rodada lendo o JSON do stdout.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.data = base / "data"
        self.docs = base / "docs"
        season = self.data / str(SEASON)

        _write(self.data / "drivers.json", {"aliases": {}})
        _write(season / "players.json", {"aliases": {}, "names": {}})
        _write(season / "calendar.json", CALENDAR)

        self.msg_file = base / "mensagem.txt"
        self.msg_file.write_text(MSG_1, encoding="utf-8")

    def _cli(self, *extra: str) -> tuple[int, str, str]:
        argv = ["--season", str(SEASON), "--data", str(self.data), "--docs", str(self.docs)]
        argv.extend(extra)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            codigo = P.main(argv)
        return codigo, out.getvalue(), err.getvalue()

    def test_run_pontuado_sai_com_zero(self):
        with mock.patch("bolao.pipeline.fetch_result", return_value=RESULT_1):
            codigo, _, _ = self._cli("run", "--texto-file", str(self.msg_file))
        self.assertEqual(codigo, 0)

    def test_run_indisponivel_sai_com_dois(self):
        with mock.patch("bolao.pipeline.fetch_result", side_effect=ResultUnavailable("sem resultado")):
            codigo, _, _ = self._cli("run", "--texto-file", str(self.msg_file))
        self.assertEqual(codigo, 2)

    def test_erro_de_parse_sai_com_um(self):
        ruim = Path(self._tmp.name) / "ruim.txt"
        ruim.write_text("Bolao qualify Marciolandia\nPiloto VER\n\nJoao\nVER\nP1\n", encoding="utf-8")
        codigo, _, _ = self._cli("run", "--texto-file", str(ruim))
        self.assertEqual(codigo, 1)

    def test_json_traz_a_rodada_no_stdout(self):
        with mock.patch("bolao.pipeline.fetch_result", side_effect=ResultUnavailable("sem resultado")):
            codigo, out, err = self._cli("--json", "run", "--texto-file", str(self.msg_file))

        self.assertEqual(codigo, 2)
        resumo = json.loads(out)  # stdout tem só o JSON — o workflow faz json.load nele
        self.assertEqual(resumo["round"], 1)
        self.assertEqual(resumo["resultado"], "indisponivel")
        self.assertIn("Rodada 1", err)  # texto legível continua no log, via stderr

    def test_retry_indisponivel_sai_com_dois_e_depois_zero(self):
        with mock.patch("bolao.pipeline.fetch_result", side_effect=ResultUnavailable("sem resultado")):
            self._cli("run", "--texto-file", str(self.msg_file))
            codigo, _, _ = self._cli("retry", "1")
        self.assertEqual(codigo, 2)

        # Segunda volta do laço do verificador: o quali saiu.
        with mock.patch("bolao.pipeline.fetch_result", return_value=RESULT_1):
            codigo, _, _ = self._cli("retry", "1")
        self.assertEqual(codigo, 0)
        self.assertTrue((self.docs / "data" / str(SEASON) / "standings.json").exists())


if __name__ == "__main__":
    unittest.main()
