"""CLIs do projeto e dados do histórico 2021–2025, com os arquivos reais de ``data/``.

- ``python -m bolao.cli``: pontua uma mensagem real contra o resultado real.
- ``python -m bolao.site build``: gera o site num diretório temporário.
- ``python -m bolao.historico build``: as mensagens commitadas em
  ``data/<ano>/messages/`` são exatamente as sintetizadas da planilha (CSV), e os
  avisos de conferência são só os já conhecidos (qualquer aviso novo = dado novo
  suspeito, para o usuário decidir; nunca "consertar" o dado aqui).
Nada escreve em ``data/`` nem em ``docs/``: tudo em cópia temporária.
"""

import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from bolao import cli, historico, site

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"

# Avisos que a conferência da planilha já dá hoje (dados do grupo; ver etapa-7).
AVISOS_CONHECIDOS = {
    2021: [],
    2022: [
        "R12 Ferrari: código de piloto desconhecido p5='ZZZ' -> ZZZ (não está na entry list 2022)",
        "R12 Ferrari: código de piloto desconhecido p6='ZZZ' -> ZZZ (não está na entry list 2022)",
        "R12 Ferrari: top6 com piloto repetido ['LEC', 'VER', 'HAM', 'PER', 'ZZZ', 'ZZZ']",
    ],
    2023: [
        "R4 Ferrari: top6 com piloto repetido ['VER', 'PER', 'LEC', 'ALO', 'PER', 'HAM']",
        "R10 Francez: top6 com piloto repetido ['VER', 'SAI', 'HAM', 'PER', 'ALO', 'SAI']",
        "R17 FRANCEZ: código de piloto desconhecido p6='ZZZ' -> ZZZ (não está na entry list 2023)",
    ],
    2024: ["R24 (Abu Dhabi): sem piloto da rodada em rodadas_2024.csv — pontua so o top6."],
    2025: [
        "R1 (Melbourne): piloto da rodada TSU — planilha diz P17, Jolpica diz P5 (usando Jolpica).",
        "R5 Guilherme: top6 com piloto repetido ['NOR', 'PIA', 'VER', 'RUS', 'LEC', 'VER']",
        "R11 Igor: código de piloto desconhecido p4='LEV' -> LEV (não está na entry list 2025)",
    ],
}


def _roda(func, argv):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida):
        codigo = func(argv)
    return codigo, saida.getvalue()


class TestCliPontuacao(unittest.TestCase):
    def test_pontua_a_rodada_9_real(self):
        codigo, saida = _roda(cli.main, [
            str(DADOS / "2026" / "messages" / "9.txt"),
            str(DADOS / "2026" / "results" / "9.json"),
            "--drivers", str(DADOS / "drivers.json"),
            "--players", str(DADOS / "2026" / "players.json"),
        ])
        self.assertEqual(codigo, 0)
        totais = {
            m.group(1): int(m.group(2))
            for m in re.finditer(r"^\s*\d+\s+(\S+(?: \S+)*?)\s+\d+\s+\d+\s+(\d+)\s*$", saida, re.M)
        }
        # totais da rodada 9 (Silverstone), os mesmos conferidos à mão em test_scoring
        self.assertEqual(totais["Guilherme"], 6)
        self.assertEqual(totais["Dalla"], 5)
        self.assertEqual(totais["Caliman"], 7)
        self.assertEqual(len(totais), 8)

    def test_detalhe_lista_as_posicoes(self):
        codigo, saida = _roda(cli.main, [
            str(DADOS / "2026" / "messages" / "9.txt"),
            str(DADOS / "2026" / "results" / "9.json"),
            "--drivers", str(DADOS / "drivers.json"),
            "--players", str(DADOS / "2026" / "players.json"),
            "--detalhe",
        ])
        self.assertEqual(codigo, 0)
        self.assertIn("P1", saida)


class TestSiteBuildCli(unittest.TestCase):
    def test_build_gera_os_quatro_json_da_temporada(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, docs = Path(tmp) / "data", Path(tmp) / "docs"
            data.mkdir()
            shutil.copy(DADOS / "drivers.json", data / "drivers.json")
            shutil.copytree(DADOS / "2026", data / "2026")
            codigo, saida = _roda(site.main, ["build", "--season", "2026", "--data", str(data), "--docs", str(docs)])
            self.assertEqual(codigo, 0)
            self.assertIn("Consolidado:", saida)
            for nome in ("standings", "bets", "results", "calendar"):
                self.assertTrue((docs / "data" / "2026" / f"{nome}.json").exists(), nome)
            self.assertTrue((docs / "data" / "seasons.json").exists())


class TestHistorico(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="bolao_hist_"))
        shutil.copytree(DADOS, cls.tmp / "data")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_avisos_de_conferencia_sao_so_os_conhecidos(self):
        for ano, esperado in AVISOS_CONHECIDOS.items():
            with self.subTest(ano=ano):
                resumo = historico.build(ano, data_dir=DADOS, check_only=True)
                self.assertEqual(resumo["avisos"], esperado)

    def test_conferencia_nao_grava_nada(self):
        antes = sorted(p.relative_to(DADOS).as_posix() for p in DADOS.rglob("*") if p.is_file())
        historico.build(2025, data_dir=DADOS, check_only=True)
        depois = sorted(p.relative_to(DADOS).as_posix() for p in DADOS.rglob("*") if p.is_file())
        self.assertEqual(antes, depois)

    def test_mensagens_commitadas_batem_com_a_planilha(self):
        for ano in AVISOS_CONHECIDOS:
            with self.subTest(ano=ano):
                historico.build(ano, data_dir=self.tmp / "data")
                gerados = sorted((self.tmp / "data" / str(ano) / "messages").glob("*.txt"))
                self.assertTrue(gerados)
                for gerado in gerados:
                    original = DADOS / str(ano) / "messages" / gerado.name
                    self.assertTrue(original.exists(), f"{ano}/messages/{gerado.name} não está commitado")
                    self.assertEqual(
                        gerado.read_bytes(), original.read_bytes(),
                        f"{ano}/messages/{gerado.name} diverge da planilha: rode `python -m bolao.historico build --season {ano}`",
                    )

    def test_cli_do_historico_imprime_resumo(self):
        codigo, saida = _roda(historico.main, ["build", "--season", "2021", "--data", str(DADOS), "--check-only"])
        self.assertEqual(codigo, 0)
        self.assertIn("Conferidas 12 rodada(s)", saida)
        self.assertIn("Sem avisos de conferência", saida)


class TestDadosDeEntrada(unittest.TestCase):
    """data/ (entrada do gerador): cadastros e arquivos de cada temporada."""

    def _json(self, caminho):
        return json.loads(caminho.read_text(encoding="utf-8"))

    def test_toda_temporada_tem_os_cadastros(self):
        for pasta in sorted(p for p in DADOS.iterdir() if p.name.isdigit()):
            with self.subTest(ano=pasta.name):
                for nome in ("calendar.json", "players.json"):
                    self.assertTrue((pasta / nome).exists(), nome)
                self.assertTrue(list((pasta / "results").glob("*.json")))
                self._json(pasta / "players.json")["aliases"]

    def test_players_json_bem_formado(self):
        for pasta in sorted(p for p in DADOS.iterdir() if p.name.isdigit()):
            cfg = self._json(pasta / "players.json")
            with self.subTest(ano=pasta.name):
                self.assertIsInstance(cfg["aliases"], dict)
                self.assertTrue(all(isinstance(v, str) and v for v in cfg["aliases"].values()))
                self.assertIsInstance(cfg.get("names", {}), dict)

    def test_resultados_com_ordem_valida(self):
        for arq in sorted(DADOS.glob("*/results/*.json")):
            dados = self._json(arq)
            with self.subTest(arquivo=arq.relative_to(DADOS).as_posix()):
                ordem = dados["order"]
                self.assertEqual(len(ordem), len(set(ordem)))
                self.assertTrue(all(len(c) == 3 and c.isupper() for c in ordem))
                self.assertEqual(dados["round"], int(arq.stem))

    def test_mensagens_tem_resultado_ou_estao_pendentes_so_na_ultima(self):
        # mensagem sem resultado = quali ainda não saiu (pipeline em vigília): no máximo 1
        for pasta in sorted(p for p in DADOS.iterdir() if p.name.isdigit()):
            msgs = {p.stem for p in (pasta / "messages").glob("*.txt")}
            res = {p.stem for p in (pasta / "results").glob("*.json")}
            with self.subTest(ano=pasta.name):
                self.assertLessEqual(len(msgs - res), 1, f"rodadas sem resultado: {sorted(msgs - res)}")

    def test_cadastro_de_pilotos(self):
        aliases = self._json(DADOS / "drivers.json")["aliases"]
        self.assertTrue(aliases)
        for chave, codigo in aliases.items():
            with self.subTest(alias=chave):
                self.assertRegex(codigo, r"^[A-Z]{3}$")


if __name__ == "__main__":
    unittest.main()
