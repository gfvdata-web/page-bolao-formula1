"""Páginas do site (docs/): HTML, JS e CSS batem entre si. Sem navegador.

Cobre: referências locais do index.html, ids usados pelo JS, abas e sub-abas,
rotas por ``?parâmetro``, bandeiras das corridas, tokens de cor do CSS e
sintaxe de CSS/JS (a checagem de sintaxe do JS com ``node --check`` roda no
``scripts/check``; aqui ficam as conferências de estrutura).
"""

import json
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"

HTML = (DOCS / "index.html").read_text(encoding="utf-8")
APP = (DOCS / "app.js").read_text(encoding="utf-8")
ANALISE = (DOCS / "analise.js").read_text(encoding="utf-8")
CSS = (DOCS / "style.css").read_text(encoding="utf-8")
JS = APP + "\n" + ANALISE

IDS_HTML = re.findall(r'\bid="([^"]+)"', HTML)

# Rotas por ?parâmetro (recarga de página, sem SPA) que o app.js/analise.js tratam.
ROTAS = {"ano", "jogador", "piloto", "menu", "jogadores", "pilotos"}


def _ids_criados_pelo_js() -> set[str]:
    achados = set(re.findall(r'\bid:\s*["\']([^"\']+)["\']', JS))
    achados |= set(re.findall(r'\.id\s*=\s*["\']([^"\']+)["\']', JS))
    return achados


class TestReferenciasDoHtml(unittest.TestCase):
    def test_arquivos_locais_referenciados_existem(self):
        refs = re.findall(r'\b(?:href|src)="([^"]+)"', HTML)
        locais = [r for r in refs if not re.match(r"(https?:)?//|#|\?|mailto:|data:", r)]
        self.assertIn("./style.css", locais)
        self.assertIn("./app.js", locais)
        self.assertIn("./analise.js", locais)
        for ref in locais:
            with self.subTest(ref=ref):
                alvo = (DOCS / ref.split("?")[0].split("#")[0]).resolve()
                if ref in ("./", "."):
                    alvo = DOCS
                self.assertTrue(alvo.exists(), f"index.html aponta para {ref}, que não existe")

    def test_ids_do_html_sao_unicos(self):
        repetidos = sorted({i for i in IDS_HTML if IDS_HTML.count(i) > 1})
        self.assertEqual(repetidos, [], f"ids duplicados no index.html: {repetidos}")

    def test_app_carrega_antes_da_analise(self):
        self.assertLess(HTML.index('src="./app.js"'), HTML.index('src="./analise.js"'))

    def test_chartjs_com_versao_fixa(self):
        self.assertRegex(HTML, r"cdn\.jsdelivr\.net/npm/chart\.js@4\.\d+\.\d+/")


class TestIdsDoJs(unittest.TestCase):
    def test_getelementbyid_literal_tem_id_no_html(self):
        usados = set(re.findall(r'getElementById\(\s*["\']([^"\']+)["\']', JS))
        self.assertGreater(len(usados), 50)  # a regex achou o que devia
        faltando = sorted(usados - set(IDS_HTML) - _ids_criados_pelo_js())
        self.assertEqual(faltando, [], f"o JS usa ids que não existem no HTML: {faltando}")

    def test_queryselector_por_id_tem_id_no_html(self):
        usados = set(re.findall(r'querySelector(?:All)?\(\s*["\'`][^"\'`]*?#([\w-]+)', JS))
        usados = {i for i in usados if not i.endswith("-")}  # '#secao-${...}' é dinâmico
        faltando = sorted(usados - set(IDS_HTML) - _ids_criados_pelo_js())
        self.assertEqual(faltando, [], f"querySelector com id inexistente: {faltando}")

    def test_visoes_do_rendimento_existem(self):
        # getElementById(`rendimento-view-${modo}`) com modo piloto/jogador
        bloco = HTML[HTML.index('id="rendimento-modo"'):HTML.index('id="rendimento-chips-dica"')]
        modos = re.findall(r'data-modo="(\w+)"', bloco)
        self.assertEqual(modos, ["piloto", "jogador"])
        for modo in modos:
            with self.subTest(modo=modo):
                self.assertIn(f"rendimento-view-{modo}", IDS_HTML)


class TestAbas(unittest.TestCase):
    def test_cada_aba_tem_sua_secao(self):
        abas = re.findall(r'data-aba="(\w+)"', HTML)
        self.assertEqual(abas, ["ranking", "palpites", "pilotos", "hall"])
        for aba in abas:
            with self.subTest(aba=aba):
                self.assertIn(f"secao-{aba}", IDS_HTML)

    def test_cada_subaba_do_ranking_tem_sua_subsecao(self):
        bloco = HTML[HTML.index('id="secao-ranking"'):HTML.index('id="secao-palpites"')]
        subabas = re.findall(r'data-subaba="(\w+)"', bloco)
        self.assertEqual(subabas, ["geral", "corridas", "palpites", "pontoextra", "simulador", "regras"])
        for sub in subabas:
            with self.subTest(subaba=sub):
                self.assertIn(f"subsecao-ranking-{sub}", IDS_HTML)
                # e o JS conhece o mapeamento (configurarSubAbasRanking)
                self.assertIn(f'document.getElementById("subsecao-ranking-{sub}")', APP)

    def test_cada_subaba_de_palpites_tem_sua_subsecao(self):
        bloco = HTML[HTML.index('id="secao-palpites"'):HTML.index('id="secao-pilotos"')]
        subabas = re.findall(r'data-subaba="(\w+)"', bloco)
        self.assertEqual(subabas, ["preferencia", "rendimento"])
        for sub in subabas:
            with self.subTest(subaba=sub):
                self.assertIn(f"subsecao-{sub}", IDS_HTML)

    def test_paginas_de_perfil_e_analise_tem_secao(self):
        for sec in ("secao-jogador", "secao-piloto", "secao-menu",
                    "secao-jogadores", "secao-pilotos-analise"):
            with self.subTest(secao=sec):
                self.assertIn(sec, IDS_HTML)
                self.assertIn(sec, JS)  # o JS abre essa seção
        for dialogo in ("jogador-modal", "ir-para-modal"):
            self.assertIn(dialogo, IDS_HTML)


class TestRotas(unittest.TestCase):
    def test_rotas_de_analise_declaradas(self):
        rotas = set(re.findall(r"^\s+(\w+):\s*renderPagina\w+", ANALISE, re.M))
        self.assertEqual(rotas, {"menu", "jogadores", "pilotos"})

    def test_entrar_modo_pagina_aponta_para_secao_existente(self):
        for sec, voltar in re.findall(r'entrarModoPagina\(\s*"([\w-]+)"[^;]*?"(\?\w+)"', JS):
            with self.subTest(secao=sec):
                self.assertIn(sec, IDS_HTML)
                self.assertIn(voltar.lstrip("?"), ROTAS)

    def test_links_internos_usam_rotas_conhecidas(self):
        parametros = set(re.findall(r'href:\s*`\?(\w+)=', JS))
        parametros |= set(re.findall(r'href=\s*"\?(\w+)', HTML))
        parametros |= set(re.findall(r'mostrarVoltar\(\s*"\?(\w+)', JS))
        self.assertTrue(parametros)
        self.assertLessEqual(parametros, ROTAS, f"rota desconhecida: {parametros - ROTAS}")

    def test_cada_rota_tem_leitor_de_parametro(self):
        self.assertIn("function anoPedido", APP)
        self.assertIn("function jogadorPedido", APP)
        self.assertIn("function pilotoPedido", APP)
        self.assertIn("function rotaAnalisePedida", ANALISE)


class TestBandeiras(unittest.TestCase):
    CIRCUITOS = re.findall(r'^\s+(\w+):\s*\{\s*pais:\s*"[^"]*",\s*iso:\s*"(\w+)"', APP, re.M)

    def test_mapa_de_circuitos_foi_lido(self):
        self.assertGreater(len(self.CIRCUITOS), 25)

    def test_todo_iso_do_mapa_tem_svg(self):
        faltando = sorted({iso for _, iso in self.CIRCUITOS if not (DOCS / "flags" / f"{iso}.svg").exists()})
        self.assertEqual(faltando, [], f"bandeiras ausentes em docs/flags/: {faltando}")

    def test_todo_circuito_dos_calendarios_esta_no_mapa(self):
        conhecidos = {c for c, _ in self.CIRCUITOS}
        usados: dict[str, str] = {}
        for cal in sorted((DOCS / "data").glob("*/calendar.json")):
            for corrida in json.loads(cal.read_text(encoding="utf-8"))["races"]:
                usados[corrida["circuit"]] = cal.parent.name
        faltando = {c: ano for c, ano in usados.items() if c not in conhecidos}
        self.assertEqual(faltando, {}, f"circuito sem bandeira no CIRCUITOS (app.js): {faltando}")

    def test_svgs_sao_validos(self):
        for svg in (DOCS / "flags").glob("*.svg"):
            with self.subTest(svg=svg.name):
                self.assertIn("<svg", svg.read_text(encoding="utf-8")[:500])


class TestCss(unittest.TestCase):
    def test_chaves_balanceadas(self):
        sem_comentarios = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
        self.assertEqual(sem_comentarios.count("{"), sem_comentarios.count("}"))

    def test_tokens_usados_estao_definidos(self):
        definidos = set(re.findall(r"(--[\w-]+)\s*:", CSS + JS + HTML))
        usados = set(re.findall(r"var\((--[\w-]+)", CSS + JS + HTML))
        self.assertEqual(sorted(usados - definidos), [])

    def test_tema_escuro_duplicado_nos_dois_seletores(self):
        # regra do frontend.md: tokens do escuro no @media e em [data-theme="dark"]
        self.assertIn('prefers-color-scheme: dark', CSS)
        self.assertIn(':root:not([data-theme="light"])', CSS)
        self.assertIn(':root[data-theme="dark"]', CSS)

    def test_paleta_unica_de_pontos(self):
        for token in ("--ok2", "--ok1", "--ok0-bg"):
            self.assertRegex(CSS, re.escape(token) + r"\s*:")

    def test_tema_inicial_lido_do_localstorage_no_head(self):
        self.assertIn('localStorage.getItem("tema")', HTML)


class TestCodigoJs(unittest.TestCase):
    def test_sem_texto_de_conflito_de_merge(self):
        for nome, texto in (("app.js", APP), ("analise.js", ANALISE), ("style.css", CSS), ("index.html", HTML)):
            with self.subTest(arquivo=nome):
                self.assertNotRegex(texto, r"^(<<<<<<<|>>>>>>>) ", "marca de conflito de merge")

    def test_dados_lidos_pelo_js_existem_no_site(self):
        # todo ./data/<arquivo>.json citado de forma fixa no JS existe em docs/data
        for nome in set(re.findall(r'carregarJson\("\./data/([\w-]+\.json)"\)', JS)):
            with self.subTest(arquivo=nome):
                self.assertTrue((DOCS / "data" / nome).exists())
        for nome in set(re.findall(r"carregarJson\(`\./data/\$\{\w+\}/(\w+)\.json`\)", JS)):
            with self.subTest(arquivo=nome):
                self.assertTrue(list((DOCS / "data").glob(f"*/{nome}.json")))
        for nome in set(re.findall(r'caminhoDados\("(\w+)"\)', JS)):
            with self.subTest(arquivo=nome):
                self.assertTrue(list((DOCS / "data").glob(f"*/{nome}.json")))

    def test_nao_ha_md_em_docs(self):
        # regra do CLAUDE.md: não colocar .md em docs/
        self.assertEqual([p.name for p in DOCS.rglob("*.md")], [])


if __name__ == "__main__":
    unittest.main()
