"""Contrato entre os JSON publicados em docs/data/ e o que o JS do site lê.

Os campos listados aqui foram extraídos de ``docs/app.js`` e ``docs/analise.js``
(quem renomear um campo no gerador precisa mexer no JS, e vice-versa). Também
confere a coerência interna dos dados de cada temporada e que ``docs/data/``
é exatamente o que o ``bolao.site`` gera a partir de ``data/`` (nada gerado à
mão, nada defasado). Tudo offline; o que grava, grava em pasta temporária.
"""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from bolao.formats import FORMATS, season_format
from bolao.site import gerar_equipes, generate

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data"
PUB = RAIZ / "docs" / "data"
JS = (RAIZ / "docs" / "app.js").read_text(encoding="utf-8") + (RAIZ / "docs" / "analise.js").read_text(
    encoding="utf-8"
)


def _json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


SEASONS = _json(PUB / "seasons.json")
ANOS = [t["ano"] for t in SEASONS["temporadas"]]

FORMAT_CAMPOS = {"top_n": int, "bonus": bool, "bonus_points": int, "compensation": bool, "max_points": int}
# Campos de standings.players[] que o JS lê (nome -> tipo) e os que só o gerador grava.
PLAYER_JS = {
    "position": int, "player_id": str, "name": str, "total": int, "bonus_total": int,
    "carry_points": int, "carry_rounds": int, "total_somado": int, "rounds_played": int,
    "avg_points": float, "per_round": dict, "compensated_rounds": list, "compensation_total": int,
}
PLAYER_GERADOR = {"total_calculado": int, "top6_total": int, "avulsos_points": int, "rounds_sem_palpite": list}
ROUND_JS = {
    "round": int, "race": str, "circuit": str, "date": str, "sprint": bool,
    "bonus_driver": str, "min_score": int, "bet_order": list,
}
BET_JS = {
    "round": int, "race": str, "top6": list, "top6_detail": list, "bonus_driver": str,
    "bonus_guess": int, "bonus_points": int, "total": int,
}
DETALHE_JS = {"pos": int, "guess": str, "real": (str, type(None)), "points": int}
CALENDAR_JS = {"round": int, "race_id": str, "race": str, "circuit": str, "date": str, "sprint": bool}


def _confere(teste, objeto: dict, campos: dict, onde: str):
    for campo, tipo in campos.items():
        teste.assertIn(campo, objeto, f"{onde}: falta o campo '{campo}'")
        valor = objeto[campo]
        if tipo is float:  # JSON pode gravar 7.0 como 7
            teste.assertIsInstance(valor, (int, float), f"{onde}.{campo}")
        else:
            teste.assertIsInstance(valor, tipo, f"{onde}.{campo} tem tipo {type(valor).__name__}")
        if tipo is int:
            teste.assertNotIsInstance(valor, bool, f"{onde}.{campo}")


class TestCamposLidosPeloJs(unittest.TestCase):
    """Cada campo do contrato é de fato lido por algum trecho do JS."""

    def test_campos_do_contrato_aparecem_no_js(self):
        todos = {*PLAYER_JS, *ROUND_JS, *BET_JS, *DETALHE_JS, *CALENDAR_JS, *FORMAT_CAMPOS}
        sem_uso = sorted(c for c in todos if not re.search(rf"\b{c}\b", JS))
        # 'race_id' e 'sprint' só estão no calendário (contrato do gerador, não lidos pelo app)
        self.assertEqual([c for c in sem_uso if c not in {"race_id", "sprint"}], [])


class TestSeasonsJson(unittest.TestCase):
    def test_estrutura(self):
        self.assertIn(SEASONS["atual"], ANOS)
        self.assertEqual(ANOS, sorted(ANOS, reverse=True))
        self.assertEqual(len(ANOS), len(set(ANOS)))
        self.assertEqual(ANOS[0], max(ANOS))
        self.assertEqual(SEASONS["atual"], max(ANOS))
        for t in SEASONS["temporadas"]:
            with self.subTest(ano=t["ano"]):
                _confere(self, t["format"], FORMAT_CAMPOS, f"seasons[{t['ano']}].format")
                fmt = season_format(t["ano"])
                self.assertEqual(
                    (t["format"]["top_n"], t["format"]["bonus"], t["format"]["compensation"], t["format"]["max_points"]),
                    (fmt.top_n, fmt.bonus, fmt.compensation, fmt.max_points),
                )
                self.assertLessEqual(t["rodadas"], t["rodadas_totais"])
                self.assertIsInstance(t["parcial"], bool)
                self.assertIsInstance(t["faltando"], list)
                self.assertTrue((PUB / str(t["ano"])).is_dir())

    def test_todas_as_temporadas_conhecidas_estao_publicadas(self):
        self.assertTrue(set(FORMATS) <= set(ANOS), "temporada do formats.py sem dados publicados")


class TestPastaDeTemporada(unittest.TestCase):
    def test_quatro_arquivos_por_temporada(self):
        for ano in ANOS:
            for nome in ("standings", "bets", "results", "calendar"):
                with self.subTest(ano=ano, arquivo=nome):
                    self.assertTrue((PUB / str(ano) / f"{nome}.json").exists())

    def test_nao_ha_json_sobrando_em_docs_data(self):
        esperados = {"seasons.json", "equipes.json", "hall_of_fame.json", "regras.json"}
        soltos = {p.name for p in PUB.glob("*.json")}
        self.assertEqual(soltos, esperados)

    def test_json_sem_texto_corrompido(self):
        # U+FFFD ou UTF-8 lido como latin-1 ("Ã©") = acento quebrado no site
        for arq in PUB.rglob("*.json"):
            with self.subTest(arquivo=arq.relative_to(PUB).as_posix()):
                texto = arq.read_text(encoding="utf-8")
                self.assertNotIn("�", texto)
                self.assertIsNone(re.search("[ÃÂ][\u0080-¿]", texto))


class TestStandings(unittest.TestCase):
    def test_contrato_e_coerencia(self):
        for ano in ANOS:
            st = _json(PUB / str(ano) / "standings.json")
            with self.subTest(ano=ano):
                self.assertEqual(st["season"], ano)
                _confere(self, st["format"], FORMAT_CAMPOS, "format")
                entrada = next(t for t in SEASONS["temporadas"] if t["ano"] == ano)
                self.assertEqual(st["format"], entrada["format"])
                self.assertEqual(st["meta"]["rodadas"], len(st["rounds"]))
                self.assertTrue(st["rounds"], "temporada sem nenhuma rodada")
                self.assertTrue(st["players"], "temporada sem jogadores")
                numeros = [r["round"] for r in st["rounds"]]
                self.assertEqual(numeros, sorted(set(numeros)))
                for r in st["rounds"]:
                    _confere(self, r, ROUND_JS, f"{ano} rodada {r['round']}")
                ids = [p["player_id"] for p in st["players"]]
                self.assertEqual(len(ids), len(set(ids)), "player_id repetido")
                self.assertEqual([p["position"] for p in st["players"]], list(range(1, len(ids) + 1)))
                for p in st["players"]:
                    _confere(self, p, {**PLAYER_JS, **PLAYER_GERADOR}, f"{ano} {p['player_id']}")
                    # per_round pode ter rodada sem palpite (bloco avulso de 2022/2023), mas
                    # sempre uma rodada da temporada
                    self.assertTrue(set(p["per_round"]) <= {str(n) for n in range(1, st["meta"]["rodadas_totais"] + 1)},
                                    f"{p['player_id']}: per_round com rodada fora do calendário")
                    self.assertLessEqual(p["rounds_played"], st["meta"]["rodadas_totais"])
                    for pts in p["per_round"].values():
                        self.assertGreaterEqual(pts, 0)
                for r in st["rounds"]:
                    self.assertTrue(set(r["bet_order"]) <= set(ids), f"{ano} R{r['round']}: bet_order com jogador desconhecido")

    def test_ordem_do_ranking(self):
        # pontos desc (empate: média na 2021, id nas demais); se a temporada tem
        # ranking_final.json com 'ordem', o grupo fixou esses jogadores na frente.
        for ano in ANOS:
            st = _json(PUB / str(ano) / "standings.json")["players"]
            final = DADOS / str(ano) / "ranking_final.json"
            ordem = _json(final).get("ordem", []) if final.exists() else []
            with self.subTest(ano=ano):
                self.assertEqual([p["player_id"] for p in st[: len(ordem)]], ordem)
                totais = [p["total"] for p in st[len(ordem):]]
                self.assertEqual(totais, sorted(totais, reverse=True))

    def test_total_calculado_e_soma_das_partes(self):
        for ano in ANOS:
            for p in _json(PUB / str(ano) / "standings.json")["players"]:
                with self.subTest(ano=ano, jogador=p["player_id"]):
                    self.assertEqual(
                        p["total_calculado"],
                        p["top6_total"] + p["bonus_total"] + p["compensation_total"]
                        + p["carry_points"] + p["avulsos_points"],
                    )

    def test_temporadas_sem_placar_publicado_batem_total_e_calculado(self):
        # 2025 e 2026 não têm placar do grupo mandando sobre a conta
        for ano in (2025, 2026):
            for p in _json(PUB / str(ano) / "standings.json")["players"]:
                with self.subTest(ano=ano, jogador=p["player_id"]):
                    self.assertEqual(p["total"], p["total_calculado"])
                    self.assertEqual(p["total"], p["total_somado"])

    def test_compensacao_so_onde_o_formato_permite(self):
        for ano in ANOS:
            comp = season_format(ano).compensation
            for p in _json(PUB / str(ano) / "standings.json")["players"]:
                if not comp:
                    with self.subTest(ano=ano, jogador=p["player_id"]):
                        self.assertEqual(p["compensation_total"], 0)
                        self.assertEqual(p["compensated_rounds"], [])

    def test_pontos_por_rodada_respeitam_o_maximo_do_formato(self):
        for ano in ANOS:
            maximo = season_format(ano).max_points
            for p in _json(PUB / str(ano) / "standings.json")["players"]:
                with self.subTest(ano=ano, jogador=p["player_id"]):
                    self.assertLessEqual(max(p["per_round"].values(), default=0), maximo)


class TestBets(unittest.TestCase):
    def test_contrato_e_coerencia(self):
        for ano in ANOS:
            bets = _json(PUB / str(ano) / "bets.json")
            st = _json(PUB / str(ano) / "standings.json")
            res = _json(PUB / str(ano) / "results.json")
            fmt = season_format(ano)
            with self.subTest(ano=ano):
                self.assertEqual(bets["season"], ano)
                self.assertTrue(bets["players"])
                for pid, jogador in bets["players"].items():
                    self.assertEqual(jogador["player_id"], pid)
                    self.assertIsInstance(jogador["name"], str)
                    for rnd, aposta in jogador["rounds"].items():
                        onde = f"{ano} {pid} R{rnd}"
                        _confere(self, aposta, BET_JS, onde)
                        self.assertEqual(str(aposta["round"]), rnd)
                        self.assertIn(rnd, res["rounds"], f"{onde}: aposta em rodada sem resultado")
                        self.assertEqual(len(aposta["top6"]), fmt.top_n, onde)
                        self.assertEqual(len(aposta["top6_detail"]), fmt.top_n, onde)
                        for i, det in enumerate(aposta["top6_detail"], start=1):
                            _confere(self, det, DETALHE_JS, onde)
                            self.assertIsInstance(det["reason"], str, onde)
                            self.assertEqual(det["pos"], i)
                            self.assertIn(det["points"], (0, 1, 2))
                            self.assertEqual(det["guess"], aposta["top6"][i - 1])
                            self.assertEqual(det["points"], {"exata": 2, "no top6": 1, "fora": 0}[det["reason"]], onde)
                        self.assertLessEqual(aposta["total"], fmt.max_points, onde)
                        self.assertGreaterEqual(aposta["total"], 0, onde)
                        self.assertIn(aposta["bonus_points"], (0, fmt.bonus_points if fmt.bonus else 0), onde)
                nomes_standings = {p["player_id"] for p in st["players"]}
                self.assertTrue(set(bets["players"]) <= nomes_standings)

    def test_total_do_palpite_e_top6_mais_bonus(self):
        for ano in ANOS:
            bets = _json(PUB / str(ano) / "bets.json")
            for pid, jogador in bets["players"].items():
                for rnd, a in jogador["rounds"].items():
                    if "top6_points" not in a:
                        continue
                    with self.subTest(ano=ano, jogador=pid, rodada=rnd):
                        self.assertEqual(a["top6_points"], sum(d["points"] for d in a["top6_detail"]))
                        # com placar publicado pelo grupo, o total é o do grupo (regra do histórico)
                        if not (DADOS / str(ano) / "placar_publicado.json").exists():
                            self.assertEqual(a["total"], a["top6_points"] + a["bonus_points"])

    def test_soma_dos_palpites_bate_com_o_ranking_nas_temporadas_recalculadas(self):
        for ano in (2021, 2025, 2026):
            bets = _json(PUB / str(ano) / "bets.json")["players"]
            for p in _json(PUB / str(ano) / "standings.json")["players"]:
                if p["player_id"] not in bets:
                    continue
                soma = sum(a["total"] for a in bets[p["player_id"]]["rounds"].values())
                with self.subTest(ano=ano, jogador=p["player_id"]):
                    self.assertEqual(soma, p["top6_total"] + p["bonus_total"])


class TestResultsECalendario(unittest.TestCase):
    def test_results(self):
        for ano in ANOS:
            res = _json(PUB / str(ano) / "results.json")
            st = _json(PUB / str(ano) / "standings.json")
            with self.subTest(ano=ano):
                self.assertEqual(res["season"], ano)
                self.assertEqual(sorted(map(int, res["rounds"])), [r["round"] for r in st["rounds"]])
                for rnd, r in res["rounds"].items():
                    onde = f"{ano} R{rnd}"
                    _confere(self, r, ROUND_JS, onde)
                    self.assertEqual(str(r["round"]), rnd)
                    self.assertGreaterEqual(len(r["order"]), season_format(ano).top_n, onde)
                    self.assertEqual(len(r["order"]), len(set(r["order"])), f"{onde}: piloto repetido no grid")
                    self.assertIsInstance(r["fases"], dict)
                    self.assertIsInstance(r["equipes"], dict)
                    if ano == SEASONS["atual"]:  # histórico tem rodada "Piloto (nenhum)"
                        self.assertTrue(r["bonus_driver"], f"{onde}: sem piloto da rodada")

    def test_calendario(self):
        for ano in ANOS:
            cal = _json(PUB / str(ano) / "calendar.json")
            res = _json(PUB / str(ano) / "results.json")
            with self.subTest(ano=ano):
                self.assertEqual(cal["season"], ano)
                rodadas = [c["round"] for c in cal["races"]]
                self.assertEqual(rodadas, list(range(1, len(rodadas) + 1)), "rodadas fora de sequência")
                for c in cal["races"]:
                    _confere(self, c, CALENDAR_JS, f"{ano} calendário R{c['round']}")
                    self.assertEqual(c["race_id"], f"{ano}-{c['round']:02d}")
                    self.assertRegex(c["date"], r"^\d{4}-\d{2}-\d{2}$")
                    if c.get("qualifying_utc"):  # temporadas antigas gravam null
                        self.assertRegex(c["qualifying_utc"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
                self.assertTrue(set(map(int, res["rounds"])) <= set(rodadas))

    def test_temporada_atual_tem_horario_do_quali(self):
        # a faixa do calendário e os cards "próxima corrida" usam qualifying_utc
        cal = _json(PUB / str(SEASONS["atual"]) / "calendar.json")
        self.assertTrue(all("qualifying_utc" in c for c in cal["races"]))


class TestHallRegrasEquipes(unittest.TestCase):
    def test_hall_of_fame(self):
        hof = _json(PUB / "hall_of_fame.json")
        self.assertEqual(sorted(a["ano"] for a in hof["anos"]), sorted(a for a in ANOS if a != SEASONS["atual"]))
        for a in hof["anos"]:
            with self.subTest(ano=a["ano"]):
                podio = [a["ouro"], a["prata"], a["bronze"]]
                self.assertEqual(len(set(podio)), 3, "pódio com jogador repetido")
                self.assertTrue(set(podio) <= set(hof["nomes"]), "pódio com id sem nome em 'nomes'")
        self.assertTrue(all(isinstance(n, str) and n for n in hof["nomes"].values()))

    def test_hall_bate_com_o_ranking_final_dos_anos(self):
        hof = _json(PUB / "hall_of_fame.json")
        for a in hof["anos"]:
            st = _json(PUB / str(a["ano"]) / "standings.json")["players"]
            with self.subTest(ano=a["ano"]):
                self.assertEqual([p["player_id"] for p in st[:3]], [a["ouro"], a["prata"], a["bronze"]])

    def test_regras(self):
        regras = _json(PUB / "regras.json")
        self.assertTrue(regras["comum"] and all(isinstance(t, str) and t for t in regras["comum"]))
        anos_passados = {str(a) for a in ANOS if a != SEASONS["atual"]}
        self.assertTrue(anos_passados <= set(regras["por_ano"]))
        for ano, linhas in regras["por_ano"].items():
            with self.subTest(ano=ano):
                self.assertTrue(linhas and all(isinstance(t, str) and t for t in linhas))

    def test_equipes(self):
        eq = _json(PUB / "equipes.json")
        for ano in ANOS:
            with self.subTest(ano=ano):
                self.assertIn(str(ano), eq)
                info = eq[str(ano)]
                for nome, e in info["equipes"].items():
                    self.assertTrue(e["nome"], nome)
                    self.assertRegex(e["cor"], r"^#[0-9a-fA-F]{6}$", f"cor inválida de {nome}")
                for piloto, times in info["pilotos"].items():
                    self.assertRegex(piloto, r"^[A-Z]{3}$")
                    self.assertTrue(set(times) <= set(info["equipes"]), f"{piloto}: equipe sem cadastro")
                    self.assertTrue(all(isinstance(n, int) and n > 0 for n in times.values()))
        # todo piloto de todo grid de results.json tem equipe no ano
        for ano in ANOS:
            res = _json(PUB / str(ano) / "results.json")["rounds"]
            codigos = {c for r in res.values() for c in r["order"]}
            sem_equipe = sorted(codigos - set(eq[str(ano)]["pilotos"]))
            with self.subTest(ano=ano):
                self.assertEqual(sem_equipe, [], f"{ano}: piloto no grid sem equipe em equipes.json")


class TestPublicadoIgualAoGerado(unittest.TestCase):
    """docs/data/ tem de ser exatamente o que o gerador produz a partir de data/."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="bolao_check_"))
        shutil.copytree(DADOS, cls.tmp / "data")
        (cls.tmp / "docs").mkdir()
        for ano in ANOS:
            generate(cls.tmp / "data", cls.tmp / "docs", ano)
        gerar_equipes(cls.tmp / "data", cls.tmp / "docs")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_cada_json_gerado_igual_ao_publicado(self):
        gerados = sorted((self.tmp / "docs" / "data").rglob("*.json"))
        self.assertGreaterEqual(len(gerados), 4 * len(ANOS) + 2)
        for gerado in gerados:
            rel = gerado.relative_to(self.tmp / "docs" / "data")
            with self.subTest(arquivo=rel.as_posix()):
                publicado = PUB / rel
                self.assertTrue(publicado.exists(), f"docs/data/{rel.as_posix()} não existe")
                self.assertEqual(
                    _json(publicado), _json(gerado),
                    f"docs/data/{rel.as_posix()} está defasado: rode `python -m bolao.site build --season {ANOS[0]}`",
                )

    def test_geracao_e_deterministica(self):
        outra = Path(tempfile.mkdtemp(prefix="bolao_check_"))
        try:
            shutil.copytree(self.tmp / "data", outra / "data")
            (outra / "docs").mkdir()
            generate(outra / "data", outra / "docs", SEASONS["atual"])
            for nome in ("standings", "bets", "results", "calendar"):
                a = (self.tmp / "docs/data" / str(SEASONS["atual"]) / f"{nome}.json").read_text(encoding="utf-8")
                b = (outra / "docs/data" / str(SEASONS["atual"]) / f"{nome}.json").read_text(encoding="utf-8")
                self.assertEqual(a, b, nome)
        finally:
            shutil.rmtree(outra, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
