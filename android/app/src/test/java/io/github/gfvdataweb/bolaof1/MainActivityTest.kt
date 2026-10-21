package io.github.gfvdataweb.bolaof1

import androidx.compose.ui.test.assertDoesNotExist
import androidx.compose.ui.test.assertIsDisplayed
import androidx.lifecycle.ViewModelProvider
import androidx.compose.ui.test.junit4.v2.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import io.github.gfvdataweb.bolaof1.apoio.BolaoAppDeTeste
import io.github.gfvdataweb.bolaof1.apoio.TemporadaReal
import io.github.gfvdataweb.bolaof1.ui.temporada.TemporadaViewModel
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

    /** O mesmo ViewModel (escopo da Activity) que o AppBolao usa. */
    private fun viewModelDaTemporada(): TemporadaViewModel {
        val container = (compose.activity.application as BolaoApp).container
        return ViewModelProvider(compose.activity, TemporadaViewModel.fabrica(container.temporadaRepositorio))[TemporadaViewModel::class.java]
    }

    @Test
    fun anoPassadoMostraOAnoEOfereceVoltarParaAtual() {
        esperarTexto(temporada.classificacao.jogadores.first().nome)
        compose.onNodeWithText("Voltar a ${temporada.atual}").assertDoesNotExist()

        compose.runOnUiThread { viewModelDaTemporada().abrirAno(2025) }
        esperarTexto("Bolão F1 2025")
        esperarTexto("Voltar a ${temporada.atual}")

        compose.onNodeWithText("Voltar a ${temporada.atual}").performClick()
        esperarTexto("Bolão F1 ${temporada.atual}")
        compose.onNodeWithText("Voltar a ${temporada.atual}").assertDoesNotExist()
    }

    @Test
    fun voltarDoSistemaLevaDeVoltaParaAtual() {
        esperarTexto(temporada.classificacao.jogadores.first().nome)
        compose.runOnUiThread { viewModelDaTemporada().abrirAno(2025) }
        esperarTexto("Bolão F1 2025")

        compose.runOnUiThread { compose.activity.onBackPressedDispatcher.onBackPressed() }
        esperarTexto("Bolão F1 ${temporada.atual}")
    }

    @Test
    fun hallDeFameLevaParaORankingDoAnoEscolhido() {
        esperarTexto(temporada.classificacao.jogadores.first().nome)
        compose.onNodeWithText("Hall of Fame").performClick()
        esperarTexto("Temporadas")
        compose.onNodeWithText("Temporadas").performClick()
        esperarTexto("2025")
        compose.onNodeWithText("2025").performClick()

        esperarTexto("Bolão F1 2025")
        esperarTexto("Voltar a ${temporada.atual}")
    }

    @Test
    fun trocaParaAAbaCorridas() {
        esperarTexto(temporada.classificacao.jogadores.first().nome)
        compose.onNodeWithText("Corridas").performClick()
        val ultima = temporada.classificacao.rodadas.maxBy { it.numero }
        esperarTexto("R${ultima.numero} · ${ultima.corrida}")
    }

    @Test
    fun configuracoesMostraAVersaoInstalada() {
        esperarTexto(temporada.classificacao.jogadores.first().nome)
        compose.onNodeWithContentDescription("Configurações").performClick()
        esperarTexto("Versão ${BuildConfig.VERSION_NAME} · build ${BuildConfig.VERSION_CODE}")
    }
}
