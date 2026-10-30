"""Publicação do app Android (job "publicar" do android.yml) no Worker do app.

Sem Actions e sem rede: o workflow é conferido como texto. O APK vai para o
Worker (worker/src/index.ts, testado em tests/worker.test.mjs), não para o
GitHub Releases; o nome do APK é o mesmo no workflow, no Worker e no app.
"""

import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestPublicacaoDoApp(unittest.TestCase):
    """Job "publicar" do android.yml: APK assinado + versao.json no Worker (worker/src/index.ts)."""

    YML = (RAIZ / ".github" / "workflows" / "android.yml").read_text(encoding="utf-8")
    WORKER = (RAIZ / "worker" / "src" / "index.ts").read_text(encoding="utf-8")
    APP_KT = (RAIZ / "android" / "app" / "src" / "main" / "java" / "io" / "github" / "gfvdataweb"
              / "bolaof1" / "App.kt").read_text(encoding="utf-8")

    def test_publica_no_worker_e_nao_no_releases(self):
        self.assertNotIn("gh release", self.YML)
        self.assertNotIn("contents: write", self.YML)  # nenhum job escreve no repositório
        self.assertIn("BASE: https://bolaof1.gfvdata.com", self.YML)
        self.assertIn('"$BASE/api/app/$APK"', self.YML)
        self.assertIn('"$BASE/api/app/versao.json"', self.YML)
        self.assertIn("secrets.BOLAO_TOKEN_ENVIO", self.YML)

    def test_confere_a_assinatura_antes_de_enviar(self):
        self.assertLess(self.YML.index("Confere a assinatura"), self.YML.index("$BASE/api/app/$APK"))
        # o APK vai antes do versao.json (o Worker recusa versao.json sem o APK no KV)
        self.assertLess(self.YML.index('"$BASE/api/app/$APK"'), self.YML.index('"$BASE/api/app/versao.json"'))

    def test_nome_do_apk_igual_no_workflow_no_worker_e_no_app(self):
        self.assertIn('APK=bolao-f1-v$VERSAO-build$GITHUB_RUN_NUMBER.apk', self.YML)
        self.assertIn(r"/^bolao-f1-v(\d+\.\d+\.\d+)-build(\d+)\.apk$/", self.WORKER)
        self.assertIn('"https://bolaof1.gfvdata.com/app/versao.json"', self.APP_KT)

    def test_versao_json_tem_os_campos_que_o_worker_confere(self):
        for campo in ("versao:", "build:", "apk:", "notas:", "publicado_em:"):
            with self.subTest(campo=campo):
                self.assertIn(campo, self.YML)



if __name__ == "__main__":
    unittest.main()
