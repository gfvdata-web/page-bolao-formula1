package io.github.gfvdataweb.bolaof1.ui

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import io.github.gfvdataweb.bolaof1.apoio.TemporadaReal
import io.github.gfvdataweb.bolaof1.data.ErroDeDados
import io.github.gfvdataweb.bolaof1.data.EstadoDados
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.ui.comum.ConteudoComDados
import io.github.gfvdataweb.bolaof1.ui.configuracoes.ConfiguracoesTela
import io.github.gfvdataweb.bolaof1.ui.configuracoes.EstadoDasConfiguracoes
import io.github.gfvdataweb.bolaof1.ui.corridas.CorridasTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EnviarTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EstadoDoEnvio
import io.github.gfvdataweb.bolaof1.ui.palpites.PalpitesTela
import io.github.gfvdataweb.bolaof1.ui.ranking.RankingTela
import io.github.gfvdataweb.bolaof1.ui.temporada.palpitesDaRodada
import io.github.gfvdataweb.bolaof1.ui.temporada.rodadasPontuadas
import io.github.gfvdataweb.bolaof1.ui.theme.BolaoF1Theme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
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
        compose.setContent { BolaoF1Theme(escuro = false) { RankingTela(temporada) } }
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
            BolaoF1Theme { ConteudoComDados(estado, aoAtualizar = {}, agora = { agora }) { RankingTela(it) } }
        }
        compose.onNodeWithText("Sem conexão com o site · dados salvos há 5 min").assertIsDisplayed()
    }

    @Test
    fun enviarSemConfiguracaoLevaParaAsConfiguracoes() {
        var abriu = false
        compose.setContent {
            BolaoF1Theme {
                EnviarTela(EstadoDoEnvio(configurado = false), {}, {}, {}, aoAbrirConfiguracoes = { abriu = true })
            }
        }
        compose.onNodeWithText("Enviar palpite").assertIsNotEnabled()
        compose.onNodeWithText("Abrir configurações").performClick()
        assertTrue(abriu)
    }

    @Test
    fun enviarPedeConfirmacaoAntes() {
        var enviou = 0
        compose.setContent {
            BolaoF1Theme {
                EnviarTela(EstadoDoEnvio(texto = "palpite", configurado = true), {}, {}, aoEnviar = { enviou++ }, {})
            }
        }
        compose.onNodeWithText("Enviar palpite").performClick()
        assertEquals(0, enviou)
        compose.onNodeWithText("Enviar este palpite?").assertIsDisplayed()
        compose.onNodeWithText("Enviar").performClick()
        assertEquals(1, enviou)
    }

    @Test
    fun configuracoesMostraAVersaoEAlternaAChave() {
        compose.setContent {
            BolaoF1Theme {
                ConfiguracoesTela(
                    EstadoDasConfiguracoes(url = "https://script.google.com/x", chave = "segredo", carregado = true),
                    {}, {}, {}, versao = "1.2.3", build = 42,
                )
            }
        }
        compose.onNodeWithText("Versão 1.2.3 · build 42").assertIsDisplayed()
        // A chave começa mascarada (o mascaramento é visual; a semântica guarda o texto).
        compose.onNodeWithText("Mostrar").performClick()
        compose.onNodeWithText("Ocultar").assertIsDisplayed()
    }
}
