"""Automação do pipeline na nuvem: workflow, scripts do Actions e CLI.

Sem Actions e sem rede: o workflow é conferido como texto (referências que
existem, tipo de evento igual ao do Apps Script) e os scripts ``.sh`` rodam de
verdade em pasta temporária (``registra-estado.sh`` com ``GITHUB_ENV`` falso;
``commit-push.sh`` contra um repositório git local usado como "origin").
O app Android (``android.yml``) não é testado aqui: build só no Actions.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = (RAIZ / ".github" / "workflows" / "pipeline.yml").read_text(encoding="utf-8")
SCRIPTS = RAIZ / ".github" / "scripts"
CODE_GS = (RAIZ / "google-apps-script" / "Code.gs").read_text(encoding="utf-8")


def _bash() -> str | None:
    """bash utilizável (Git Bash no Windows; o bash.exe do WSL não serve)."""
    candidatos = [shutil.which("bash")]
    git = shutil.which("git")
    if git:
        candidatos.append(str(Path(git).resolve().parents[1] / "bin" / "bash.exe"))
        candidatos.append(str(Path(git).resolve().parents[1] / "usr" / "bin" / "bash.exe"))
    for c in candidatos:
        if not c or not Path(c).exists() or "system32" in c.lower():
            continue
        try:
            if subprocess.run([c, "-c", "echo ok"], capture_output=True, text=True, timeout=20).stdout.strip() == "ok":
                return c
        except (OSError, subprocess.SubprocessError):
            continue
    return None


BASH = _bash()


def _env(**extra) -> dict:
    """Ambiente sem as variáveis GIT_* (no pre-commit elas apontam para o repo real)."""
    base = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return {**base, **extra}


class TestWorkflowDoPipeline(unittest.TestCase):
    def test_gatilho_e_o_mesmo_do_apps_script(self):
        tipo = re.search(r"GITHUB_EVENT_TYPE\s*=\s*'(\w+)'", CODE_GS).group(1)
        self.assertRegex(WORKFLOW, rf"repository_dispatch:\s*\n\s*types:\s*\[{tipo}\]")

    def test_retry_manual_pede_a_rodada(self):
        self.assertRegex(WORKFLOW, r"workflow_dispatch:\s*\n\s*inputs:\s*\n\s*round:")
        self.assertIn("required: true", WORKFLOW)

    def test_scripts_e_modulos_citados_existem(self):
        for script in set(re.findall(r"bash (\.github/scripts/[\w.-]+\.sh)", WORKFLOW)):
            with self.subTest(script=script):
                self.assertTrue((RAIZ / script).exists())
        for modulo in set(re.findall(r"python -m (bolao\.\w+)", WORKFLOW)):
            with self.subTest(modulo=modulo):
                self.assertTrue((RAIZ / (modulo.replace(".", "/") + ".py")).exists())

    def test_yaml_sem_tabs_e_com_permissao_de_escrita(self):
        self.assertNotIn("\t", WORKFLOW)
        self.assertIn("contents: write", WORKFLOW)  # o job commita os dados
        self.assertRegex(WORKFLOW, r'python-version:\s*"3\.13"')

    def test_verificador_usa_as_variaveis_que_o_registra_estado_publica(self):
        publicadas = set(re.findall(r'echo "(\w+)=', (SCRIPTS / "registra-estado.sh").read_text(encoding="utf-8")))
        self.assertEqual(publicadas, {"RODADA", "PENDENTE"})
        self.assertIn("env.PENDENTE == '1'", WORKFLOW)
        self.assertIn("$RODADA", WORKFLOW)

    def test_verificador_trata_codigo_2_como_ainda_indisponivel(self):
        self.assertRegex(WORKFLOW, r'-ne 2')
        self.assertIn("MAX_TENTATIVAS", WORKFLOW)
        self.assertIn("INTERVALO_SEGUNDOS", WORKFLOW)

    def test_timeout_cobre_a_vigilia(self):
        intervalo = int(re.search(r"INTERVALO_SEGUNDOS:\s*(\d+)", WORKFLOW).group(1))
        tentativas = int(re.search(r"MAX_TENTATIVAS:\s*(\d+)", WORKFLOW).group(1))
        timeout_min = int(re.search(r"timeout-minutes:\s*(\d+)", WORKFLOW).group(1))
        self.assertGreater(timeout_min, intervalo * tentativas / 60)

    def test_android_tem_workflow(self):
        # só a existência: o build do app roda apenas no Actions (sem JDK local)
        self.assertTrue((RAIZ / ".github" / "workflows" / "android.yml").exists())


@unittest.skipUnless(BASH, "bash (Git Bash) não encontrado")
class TestScriptsShell(unittest.TestCase):
    def test_sintaxe_dos_scripts(self):
        for sh in [*SCRIPTS.glob("*.sh"), RAIZ / "scripts" / "check"]:
            with self.subTest(script=sh.name):
                r = subprocess.run([BASH, "-n", sh.as_posix()], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_scripts_usam_fim_de_linha_lf(self):
        for sh in [*SCRIPTS.glob("*.sh"), RAIZ / "scripts" / "check"]:
            with self.subTest(script=sh.name):
                self.assertNotIn(b"\r\n", sh.read_bytes())

    def _registra(self, codigo: int, resumo: str):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / "github_env"
            env_file.write_text("", encoding="utf-8")
            env = _env(GITHUB_ENV=env_file.as_posix())
            r = subprocess.run(
                [BASH, (SCRIPTS / "registra-estado.sh").as_posix(), str(codigo), resumo],
                capture_output=True, text=True, env=env,
            )
            return r.returncode, env_file.read_text(encoding="utf-8").split()

    def test_registra_estado_rodada_pontuada(self):
        codigo, linhas = self._registra(0, json.dumps({"round": 17}))
        self.assertEqual(codigo, 0)
        self.assertEqual(linhas, ["RODADA=17", "PENDENTE=0"])

    def test_registra_estado_quali_ainda_indisponivel(self):
        codigo, linhas = self._registra(2, json.dumps({"round": 18}))
        self.assertEqual(codigo, 0)
        self.assertEqual(linhas, ["RODADA=18", "PENDENTE=1"])

    def test_registra_estado_erro_derruba_o_job_sem_publicar(self):
        codigo, linhas = self._registra(1, "")
        self.assertEqual(codigo, 1)
        self.assertEqual(linhas, [])

    def _git(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=_env())

    def _repo_com_origin(self, tmp: Path):
        origin, trabalho = tmp / "origin.git", tmp / "trabalho"
        self._git(tmp, "init", "--bare", "-b", "main", origin.name)
        self._git(tmp, "clone", origin.as_posix(), trabalho.name)
        self._git(trabalho, "config", "user.name", "teste")
        self._git(trabalho, "config", "user.email", "teste@example.com")
        self._git(trabalho, "config", "commit.gpgsign", "false")
        (trabalho / "data").mkdir()
        (trabalho / "data" / "a.json").write_text("{}", encoding="utf-8")
        (trabalho / "docs" / "data").mkdir(parents=True)  # o script faz `git add data docs/data`
        (trabalho / "docs" / "data" / "a.json").write_text("{}", encoding="utf-8")
        self._git(trabalho, "add", "-A")
        self._git(trabalho, "commit", "-m", "inicial")
        self._git(trabalho, "branch", "-M", "main")
        self._git(trabalho, "push", "-u", "origin", "main")
        return origin, trabalho

    @unittest.skipUnless(shutil.which("git"), "git não encontrado")
    def test_commit_push_sem_mudanca_nao_faz_nada(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin, trabalho = self._repo_com_origin(Path(tmp))
            antes = self._git(origin, "rev-parse", "main").stdout
            r = subprocess.run([BASH, (SCRIPTS / "commit-push.sh").as_posix(), "msg"], cwd=trabalho,
                               capture_output=True, text=True, env=_env(GITHUB_REF_NAME="main"))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Nada para commitar", r.stdout)
            self.assertEqual(self._git(origin, "rev-parse", "main").stdout, antes)

    @unittest.skipUnless(shutil.which("git"), "git não encontrado")
    def test_commit_push_envia_so_data_e_docs_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            origin, trabalho = self._repo_com_origin(Path(tmp))
            (trabalho / "data" / "b.json").write_text("{}", encoding="utf-8")
            (trabalho / "docs" / "data" / "c.json").write_text("{}", encoding="utf-8")
            (trabalho / "fora.txt").write_text("não pertence ao commit do robô", encoding="utf-8")
            r = subprocess.run([BASH, (SCRIPTS / "commit-push.sh").as_posix(), "Etapa 5: teste"], cwd=trabalho,
                               capture_output=True, text=True, env=_env(GITHUB_REF_NAME="main"))
            self.assertEqual(r.returncode, 0, r.stderr)
            arquivos = self._git(origin, "show", "--name-only", "--format=%s%n%b", "main").stdout
            self.assertIn("Etapa 5: teste", arquivos)
            self.assertIn("github-actions[bot]", arquivos)
            self.assertIn("data/b.json", arquivos)
            self.assertIn("docs/data/c.json", arquivos)
            self.assertNotIn("fora.txt", arquivos)


if __name__ == "__main__":
    unittest.main()
