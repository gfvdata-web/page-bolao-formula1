import unittest

from bolao.normalize import normalize_driver, normalize_key, normalize_player

DRIVERS = {"hamilton": "HAM", "max verstappen": "VER"}
PLAYERS = {"caio": "caio_l", "caio l": "caio_l"}


class TestNormalizeKey(unittest.TestCase):
    def test_remove_acento_e_pontuacao(self):
        self.assertEqual(normalize_key("Vinícius"), "vinicius")
        self.assertEqual(normalize_key("Caio L."), "caio l")
        self.assertEqual(normalize_key("  RUS  "), "rus")


class TestNormalizeDriver(unittest.TestCase):
    def test_codigo_com_case_variado(self):
        self.assertEqual(normalize_driver("Ham"), "HAM")
        self.assertEqual(normalize_driver("ham"), "HAM")
        self.assertEqual(normalize_driver("HAM"), "HAM")

    def test_nome_completo_via_alias(self):
        self.assertEqual(normalize_driver("Hamilton", DRIVERS), "HAM")
        self.assertEqual(normalize_driver("Max Verstappen", DRIVERS), "VER")

    def test_fallback_tres_letras(self):
        self.assertEqual(normalize_driver("Norris"), "NOR")


class TestNormalizePlayer(unittest.TestCase):
    def test_variantes_mesmo_id(self):
        self.assertEqual(normalize_player("Caio", PLAYERS), "caio_l")
        self.assertEqual(normalize_player("Caio L.", PLAYERS), "caio_l")

    def test_sem_mapa_id_estavel(self):
        self.assertEqual(normalize_player("Vinícius"), "vinicius")


if __name__ == "__main__":
    unittest.main()
