package io.github.gfvdataweb.bolaof1

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import io.github.gfvdataweb.bolaof1.apoio.BolaoAppDeTeste
import io.github.gfvdataweb.bolaof1.apoio.TemporadaReal
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

/**
 * Abre o app de verdade (manifest, tema, Activity, ViewModel, rede e cache)
 * num Android simulado, lendo de um site local com os dados reais. Se o app
 * fecharia sozinho ao abrir no celular, este teste falha no CI.
 */
@RunWith(RobolectricTestRunner::class)
@Config(application = BolaoAppDeTeste::class)
class MainActivityTest {

    @get:Rule
    val compose = createAndroidComposeRule<MainActivity>()

    private val temporada = TemporadaReal.temporada

    private fun esperarTexto(texto: String) {
        compose.waitUntil(timeoutMillis = 15_000) {
            compose.onAllNodesWithText(texto).fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun abreNoRankingComOsDadosDoSite() {
        esperarTexto(temporada.classificacao.jogadores.first().nome)
        compose.onNodeWithText("Bolão F1 ${temporada.ano}").assertIsDisplayed()
    }

    @Test
    fun trocaParaAAbaCorridas() {
        esperarTexto(temporada.classificacao.jogadores.first().nome)
        compose.onNodeWithText("Corridas").performClick()
        val ultima = temporada.classificacao.rodadas.maxBy { it.numero }
        esperarTexto("R${ultima.numero} · ${ultima.corrida}")
    }
}
