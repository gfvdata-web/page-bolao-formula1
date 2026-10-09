package io.github.gfvdataweb.bolaof1.ui

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import io.github.gfvdataweb.bolaof1.apoio.TemporadaReal
import io.github.gfvdataweb.bolaof1.data.ErroDeDados
import io.github.gfvdataweb.bolaof1.data.EstadoDados
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.ui.comum.ConteudoComDados
import io.github.gfvdataweb.bolaof1.ui.corridas.CorridasTela
import io.github.gfvdataweb.bolaof1.ui.palpites.PalpitesTela
import io.github.gfvdataweb.bolaof1.ui.ranking.RankingTela
import io.github.gfvdataweb.bolaof1.ui.temporada.palpitesDaRodada
import io.github.gfvdataweb.bolaof1.ui.temporada.rodadasPontuadas
import io.github.gfvdataweb.bolaof1.ui.theme.BolaoF1Theme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

/** Cada aba desenhada com a temporada real, nos temas claro e escuro. */
@RunWith(RobolectricTestRunner::class)
class TelasTest {

    @get:Rule
    val compose = createComposeRule()

    private val temporada = TemporadaReal.temporada

    @Test
    fun rankingMostraOLider() {
        compose.setContent { BolaoF1Theme(escuro = false) { RankingTela(temporada, rodape = "rodapé") } }
        compose.onNodeWithText(temporada.classificacao.jogadores.first().nome).assertIsDisplayed()
    }

    @Test
    fun corridasMostraARodadaMaisRecente() {
        compose.setContent { BolaoF1Theme(escuro = true) { CorridasTela(temporada) } }
        val ultima = temporada.classificacao.rodadas.maxBy { it.numero }
        compose.onNodeWithText("R${ultima.numero} · ${ultima.corrida}").assertIsDisplayed()
    }

    @Test
    fun palpitesMostraQuemMaisPontuouNaRodadaMaisRecente() {
        compose.setContent { BolaoF1Theme(escuro = false) { PalpitesTela(temporada) } }
        val rodada = checkNotNull(palpitesDaRodada(temporada, rodadasPontuadas(temporada).first()))
        compose.onNodeWithText(rodada.palpites.first().nome).assertIsDisplayed()
    }

    @Test
    fun semDadosESemInternetOfereceTentarDeNovo() {
        var tentativas = 0
        val estado = EstadoDados<Temporada>(dados = null, atualizadoEm = null, atualizando = false, erro = ErroDeDados.FALHA_NO_DOWNLOAD)
        compose.setContent {
            BolaoF1Theme { ConteudoComDados(estado, aoAtualizar = { tentativas++ }) { } }
        }
        compose.onNodeWithText("Tentar de novo").performClick()
        assertEquals(1, tentativas)
    }

    @Test
    fun comDadosSalvosESemInternetAvisaNoTopo() {
        val agora = 1_800_000_000_000L
        val estado = EstadoDados(
            dados = temporada,
            atualizadoEm = agora - 5 * 60_000,
            atualizando = false,
            erro = ErroDeDados.FALHA_NO_DOWNLOAD,
        )
        compose.setContent {
            BolaoF1Theme { ConteudoComDados(estado, aoAtualizar = {}, agora = { agora }) { RankingTela(it, rodape = "") } }
        }
        compose.onNodeWithText("Sem conexão com o site · dados salvos há 5 min").assertIsDisplayed()
    }
}
