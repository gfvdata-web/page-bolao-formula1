"""Equipes por temporada: base curada (data/equipes.json) + docs/data/equipes.json."""

import json
import re
import tempfile
import unittest
from pathlib import Path

from bolao.site import gerar_equipes

RAIZ = Path(__file__).resolve().parent.parent
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


class TestBaseCurada(unittest.TestCase):
    """Toda equipe que aparece nos resultados reais tem nome e cor no ano."""

    def test_toda_equipe_dos_resultados_tem_nome_e_cor(self):
        curadas = json.loads((RAIZ / "data" / "equipes.json").read_text(encoding="utf-8"))
        faltando = []
        for arq in sorted((RAIZ / "data").glob("20*/results/*.json")):
            ano = arq.parent.parent.name
            for equipe in json.loads(arq.read_text(encoding="utf-8")).get("equipes", {}).values():
                info = curadas.get(ano, {}).get(equipe)
                if not info or not info.get("nome") or not HEX.match(info.get("cor", "")):
                    faltando.append((ano, equipe))
        self.assertEqual(sorted(set(faltando)), [])


class TestGerarEquipes(unittest.TestCase):
    def test_conta_qualis_por_equipe_e_usa_nome_curado(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, docs = Path(tmp) / "data", Path(tmp) / "docs"
            res = data / "2025" / "results"
            res.mkdir(parents=True)
            for rnd, eq in [(1, "Red Bull"), (2, "Red Bull"), (3, "RB")]:
                (res / f"{rnd}.json").write_text(
                    json.dumps({"order": ["LAW"], "equipes": {"LAW": eq}}), encoding="utf-8"
                )
            (data / "equipes.json").write_text(
                json.dumps({"2025": {"RB": {"nome": "Racing Bulls", "cor": "#6692FF"}}}),
                encoding="utf-8",
            )
            saida = gerar_equipes(data, docs)
            self.assertEqual(saida["2025"]["pilotos"]["LAW"], {"Red Bull": 2, "RB": 1})
            self.assertEqual(saida["2025"]["equipes"]["RB"]["nome"], "Racing Bulls")
            # sem curadoria: nome da Jolpica + cor padrão
            self.assertEqual(saida["2025"]["equipes"]["Red Bull"]["nome"], "Red Bull")
            self.assertTrue((docs / "data" / "equipes.json").exists())


if __name__ == "__main__":
    unittest.main()
