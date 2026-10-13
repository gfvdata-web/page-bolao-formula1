"""Camada de rede da Jolpica (``fetch_*`` e CLI) com a rede trocada por mock.

O ``test_jolpica.py`` cobre as funções ``build_*`` (puras). Aqui entram o que
faltava: ``fetch_json`` com os erros de HTTP/rede/JSON, ``fetch_result`` e
``fetch_all_results`` (rodadas futuras não derrubam a busca) e os códigos de
saída da CLI (0 ok, 1 erro, 2 quali ainda indisponível). Nenhuma chamada real:
``urllib.request.urlopen`` e ``fetch_json`` são sempre substituídos.
"""

import contextlib
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from bolao import jolpica as J

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "jolpica"


def _fx(nome: str) -> dict:
    return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))


class _Resposta:
    """Imita o objeto devolvido por urlopen (context manager com .read())."""

    def __init__(self, corpo: bytes):
        self._corpo = corpo

    def read(self) -> bytes:
        return self._corpo

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _roteador(quali_por_rodada: dict[int, str] | None = None):
    """Substituto de ``fetch_json`` que serve as fixtures conforme a URL pedida."""
    quali_por_rodada = quali_por_rodada if quali_por_rodada is not None else {1: "qualifying_2026_1.json"}
    chamadas: list[str] = []

    def falso(url: str, timeout: float = 20.0) -> dict:
        chamadas.append(url)
        if url == J.season_url(2026):
            return _fx("season_2026.json")
        if url == J.drivers_url(2026):
            return _fx("drivers_2026.json")
        for rnd in range(1, 40):
            if url == J.qualifying_url(2026, rnd):
                return _fx(quali_por_rodada.get(rnd, "qualifying_2026_empty.json"))
        raise AssertionError(f"URL inesperada: {url}")

    falso.chamadas = chamadas  # type: ignore[attr-defined]
    return falso


class TestUrls(unittest.TestCase):
    def test_urls_da_api(self):
        self.assertEqual(J.season_url(2026), "https://api.jolpi.ca/ergast/f1/2026.json?limit=100")
        self.assertEqual(J.drivers_url(2026), "https://api.jolpi.ca/ergast/f1/2026/drivers.json?limit=100")
        self.assertEqual(
            J.qualifying_url(2026, 9), "https://api.jolpi.ca/ergast/f1/2026/9/qualifying.json?limit=100"
        )

    def test_url_base_customizada(self):
        self.assertTrue(J.season_url(2025, "http://x/f1").startswith("http://x/f1/2025.json"))


class TestFetchJson(unittest.TestCase):
    def test_devolve_json_e_manda_user_agent(self):
        with mock.patch("urllib.request.urlopen", return_value=_Resposta(b'{"a": 1}')) as uo:
            self.assertEqual(J.fetch_json("http://exemplo/x"), {"a": 1})
        requisicao = uo.call_args.args[0]
        self.assertEqual(requisicao.get_header("User-agent"), J.USER_AGENT)

    def test_http_com_erro_vira_jolpicaerror(self):
        erro = urllib.error.HTTPError("http://x", 503, "Unavailable", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=erro):
            with self.assertRaisesRegex(J.JolpicaError, "HTTP 503"):
                J.fetch_json("http://x")

    def test_rede_fora_do_ar_vira_jolpicaerror(self):
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("sem rede")):
            with self.assertRaisesRegex(J.JolpicaError, "Falha de rede"):
                J.fetch_json("http://x")

    def test_resposta_que_nao_e_json_vira_jolpicaerror(self):
        with mock.patch("urllib.request.urlopen", return_value=_Resposta(b"<html>erro</html>")):
            with self.assertRaisesRegex(J.JolpicaError, "não-JSON"):
                J.fetch_json("http://x")

    def test_resultado_indisponivel_e_um_tipo_de_jolpicaerror(self):
        self.assertTrue(issubclass(J.ResultUnavailable, J.JolpicaError))


class TestFetch(unittest.TestCase):
    def test_fetch_result_monta_o_resultado_da_fixture(self):
        with mock.patch.object(J, "fetch_json", _roteador()):
            res = J.fetch_result(1, 2026)
        self.assertEqual(res["round"], 1)
        self.assertEqual(res["race_id"], "2026-01")
        self.assertGreaterEqual(len(res["order"]), 6)
        self.assertEqual(len(res["order"]), len(set(res["order"])))

    def test_fetch_result_sem_quali_levanta_resultunavailable(self):
        with mock.patch.object(J, "fetch_json", _roteador()):
            with self.assertRaises(J.ResultUnavailable):
                J.fetch_result(22, 2026)

    def test_fetch_calendar_e_drivers(self):
        with mock.patch.object(J, "fetch_json", _roteador()):
            cal = J.fetch_calendar(2026)
            drivers = J.fetch_drivers(2026)
        self.assertEqual(len(cal["races"]), 22)
        self.assertEqual([c["round"] for c in cal["races"]], list(range(1, 23)))
        self.assertTrue(drivers["aliases"])

    def test_fetch_all_results_pula_rodadas_futuras(self):
        falso = _roteador({1: "qualifying_2026_1.json"})
        with mock.patch.object(J, "fetch_json", falso):
            gravaveis, indisponiveis = J.fetch_all_results(2026, pausa=0)
        self.assertEqual([r["round"] for r in gravaveis], [1])
        self.assertEqual(indisponiveis, list(range(2, 23)))

    def test_fetch_all_results_erro_de_rede_nao_e_engolido(self):
        def falso(url, timeout=20.0):
            if url == J.season_url(2026):
                return _fx("season_2026.json")
            raise J.JolpicaError("Falha de rede")

        with mock.patch.object(J, "fetch_json", falso):
            with self.assertRaises(J.JolpicaError):
                J.fetch_all_results(2026, pausa=0)


class TestCli(unittest.TestCase):
    def _roda(self, *argv, falso=None):
        saida, erro = io.StringIO(), io.StringIO()
        with mock.patch.object(J, "fetch_json", falso or _roteador()):
            with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
                codigo = J.main(list(argv))
        return codigo, saida.getvalue(), erro.getvalue()

    def test_result_grava_arquivo_e_sai_com_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "r" / "1.json"
            codigo, saida, _ = self._roda("result", "1", "--out", str(destino))
            self.assertEqual(codigo, 0)
            self.assertEqual(json.loads(destino.read_text(encoding="utf-8"))["round"], 1)
            self.assertIn("Gravado", saida)

    def test_result_indisponivel_sai_com_dois_e_nao_grava(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "22.json"
            codigo, _, erro = self._roda("result", "22", "--out", str(destino))
            self.assertEqual(codigo, 2)
            self.assertFalse(destino.exists())
            self.assertIn("indispon", erro)

    def test_erro_de_rede_sai_com_um(self):
        def falso(url, timeout=20.0):
            raise J.JolpicaError("HTTP 500")

        with tempfile.TemporaryDirectory() as tmp:
            codigo, _, erro = self._roda("result", "1", "--out", str(Path(tmp) / "1.json"), falso=falso)
        self.assertEqual(codigo, 1)
        self.assertIn("[erro]", erro)

    def test_calendar_e_drivers_gravam_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            cal, drv = Path(tmp) / "calendar.json", Path(tmp) / "drivers.json"
            self.assertEqual(self._roda("calendar", "--out", str(cal))[0], 0)
            self.assertEqual(self._roda("drivers", "--out", str(drv))[0], 0)
            self.assertEqual(len(json.loads(cal.read_text(encoding="utf-8"))["races"]), 22)
            self.assertIn("aliases", json.loads(drv.read_text(encoding="utf-8")))

    def test_results_grava_so_os_disponiveis(self):
        with mock.patch("time.sleep"):
            with tempfile.TemporaryDirectory() as tmp:
                codigo, saida, _ = self._roda("results", "--out", tmp)
                self.assertEqual(codigo, 0)
                self.assertEqual(sorted(p.name for p in Path(tmp).glob("*.json")), ["1.json"])
        self.assertIn("Gravados 1", saida)
        self.assertIn("Ainda sem resultado", saida)


class TestPipelineComRedeFalsa(unittest.TestCase):
    """Pipeline inteiro (grava mensagem, busca na "Jolpica", gera o site) com ``fetch_json`` falso."""

    def setUp(self):
        from bolao import pipeline as P

        self.P = P
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.data, self.docs = base / "data", base / "docs"
        cal = J.build_calendar(_fx("season_2026.json"), 2026)
        for nome, dados in (
            (self.data / "drivers.json", {"aliases": {}}),
            (self.data / "2026" / "players.json", {"aliases": {}, "names": {}}),
            (self.data / "2026" / "calendar.json", cal),
        ):
            nome.parent.mkdir(parents=True, exist_ok=True)
            nome.write_text(json.dumps(dados), encoding="utf-8")
        real = J.build_result(_fx("qualifying_2026_1.json"), 2026, 1)
        self.top6 = real["order"][:6]
        self.texto = "Bolao qualify Melbourne\nPiloto {}\n\nJoao\n{}\nP1\n".format(
            real["order"][0], "\n".join(self.top6)
        )

    def tearDown(self):
        self._tmp.cleanup()

    def _roda(self, falso, *argv):
        err = io.StringIO()
        with mock.patch.object(J, "fetch_json", falso), contextlib.redirect_stdout(io.StringIO()),                 contextlib.redirect_stderr(err):
            codigo = self.P.main(["--data", str(self.data), "--docs", str(self.docs), *argv])
        return codigo, err.getvalue()

    def test_ponta_a_ponta_pontua_o_palpite_perfeito(self):
        texto = self.data.parent / "msg.txt"
        texto.write_text(self.texto, encoding="utf-8")
        codigo, _ = self._roda(_roteador(), "run", "--round", "1", "--texto-file", str(texto))
        self.assertEqual(codigo, 0)
        standings = json.loads((self.docs / "data" / "2026" / "standings.json").read_text(encoding="utf-8"))
        self.assertEqual(standings["players"][0]["player_id"], "joao")
        self.assertEqual(standings["players"][0]["top6_total"], 12)

    def test_erro_de_rede_sai_com_um_mas_guarda_a_mensagem(self):
        def sem_rede(url, timeout=20.0):
            raise J.JolpicaError("Falha de rede ao buscar " + url)

        texto = self.data.parent / "msg.txt"
        texto.write_text(self.texto, encoding="utf-8")
        codigo, err = self._roda(sem_rede, "run", "--round", "1", "--texto-file", str(texto))
        self.assertEqual(codigo, 1)
        self.assertIn("[erro]", err)
        self.assertFalse((self.data / "2026" / "results" / "1.json").exists())
        # a mensagem já tinha sido gravada: o retry manual depois funciona
        self.assertTrue((self.data / "2026" / "messages" / "1.txt").exists())
        codigo, _ = self._roda(_roteador(), "retry", "1")
        self.assertEqual(codigo, 0)

    def test_quali_ainda_sem_resultado_sai_com_dois(self):
        texto = self.data.parent / "msg.txt"
        texto.write_text(self.texto, encoding="utf-8")
        codigo, _ = self._roda(_roteador({}), "run", "--round", "1", "--texto-file", str(texto))
        self.assertEqual(codigo, 2)


if __name__ == "__main__":
    unittest.main()
