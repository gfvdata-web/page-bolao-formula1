package io.github.gfvdataweb.bolaof1.ui.home

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import io.github.gfvdataweb.bolaof1.ui.theme.BolaoF1Theme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

/** A tela inicial mostra o nome do app e a versão recebida (claro e escuro). */
@RunWith(RobolectricTestRunner::class)
class HomeScreenTest {

    @get:Rule
    val compose = createComposeRule()

    @Test
    fun mostraTituloEVersao_temaClaro() {
        compose.setContent {
            BolaoF1Theme(escuro = false) { HomeScreen(versao = "1.2.3", build = 42) }
        }
        compose.onNodeWithText("Bolão F1").assertIsDisplayed()
        compose.onNodeWithText("Versão 1.2.3 · build 42").assertIsDisplayed()
    }

    @Test
    fun mostraTituloEVersao_temaEscuro() {
        compose.setContent {
            BolaoF1Theme(escuro = true) { HomeScreen(versao = "1.2.3", build = 42) }
        }
        compose.onNodeWithText("Bolão F1").assertIsDisplayed()
        compose.onNodeWithText("Versão 1.2.3 · build 42").assertIsDisplayed()
    }
}
