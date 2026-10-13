"""Inventário "Cobertura:" do scripts/check em dia com os arquivos do repo.

Falha quando entra um módulo, uma página ou um arquivo de teste que o inventário
não cita (funcionalidade nova sem teste = dívida) e confere a automação ligada
(pre-commit versionado, regra no CLAUDE.md).
"""

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CHECK = (RAIZ / "scripts" / "check").read_text(encoding="utf-8")
CLAUDE = (RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
INVENTARIO = CHECK.split("cd \"$(dirname")[0]  # só o cabeçalho com "Cobertura:"


def _fonte_dos_testes() -> str:
    partes = [p.read_text(encoding="utf-8") for p in (RAIZ / "tests").glob("test_*.py")]
    partes += [p.read_text(encoding="utf-8") for p in (RAIZ / "tests").glob("*.test.mjs")]
    return "\n".join(partes)


class TestInventario(unittest.TestCase):
    def test_cabecalho_tem_cobertura_e_o_que_ficou_sem_teste(self):
        self.assertIn("Cobertura", INVENTARIO)
        self.assertIn("(sem teste: build só no Actions", INVENTARIO)  # app Android
        self.assertIn("(sem teste: exige navegador", INVENTARIO)

    def test_todo_arquivo_de_teste_esta_no_inventario(self):
        arquivos = [p.name for p in (RAIZ / "tests").glob("test_*.py")] + [
            p.name for p in (RAIZ / "tests").glob("*.test.mjs")
        ]
        for nome in arquivos:
            with self.subTest(teste=nome):
                self.assertIn(nome.replace(".py", ""), INVENTARIO)

    def test_todo_modulo_do_bolao_tem_teste(self):
        fontes = _fonte_dos_testes()
        for modulo in (RAIZ / "bolao").glob("*.py"):
            if modulo.stem == "__init__":
                continue
            with self.subTest(modulo=modulo.stem):
                self.assertRegex(
                    fontes, rf"(from bolao(\.{modulo.stem})? import .*\b{modulo.stem}\b|bolao\.{modulo.stem}\b)",
                    f"bolao/{modulo.name} não é importado por nenhum teste",
                )

    def test_toda_pagina_do_site_tem_teste(self):
        fontes = _fonte_dos_testes()
        for arquivo in ("index.html", "app.js", "analise.js", "style.css"):
            with self.subTest(arquivo=arquivo):
                self.assertTrue((RAIZ / "docs" / arquivo).exists())
                self.assertIn(arquivo, fontes + CHECK)

    def test_check_roda_no_modo_rapido_para_cada_extensao_do_repo(self):
        for padrao in ("bolao/*.py", "tests/test_*.py", "docs/app.js|docs/analise.js", "docs/data/*.json",
                       "google-apps-script/Code.gs", "android/*"):
            with self.subTest(padrao=padrao):
                self.assertIn(padrao, CHECK)

    def test_todo_modulo_do_bolao_tem_regra_no_modo_rapido(self):
        for modulo in (RAIZ / "bolao").glob("*.py"):
            if modulo.stem == "__init__":
                continue
            with self.subTest(modulo=modulo.stem):
                self.assertTrue(
                    re.search(rf"bolao/(\w+\|bolao/)*{modulo.stem}\.py", CHECK),
                    f"scripts/check não mapeia bolao/{modulo.name} para testes específicos",
                )


class TestAutomacaoLigada(unittest.TestCase):
    def test_pre_commit_versionado_roda_o_check_completo(self):
        hook = (RAIZ / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("scripts/check", hook)

    def test_fim_de_linha_lf_fixado(self):
        attrs = (RAIZ / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("scripts/* text eol=lf", attrs)
        self.assertIn(".githooks/* text eol=lf", attrs)

    def test_claude_md_tem_a_regra_de_teste(self):
        self.assertIn("Funcionalidade nova ou alterada entra com teste", CLAUDE)
        self.assertIn("bash scripts/check", CLAUDE)


if __name__ == "__main__":
    unittest.main()
