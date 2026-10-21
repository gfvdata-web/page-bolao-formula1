package io.github.gfvdataweb.bolaof1.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import io.github.gfvdataweb.bolaof1.apoio.HistoricoReal
import io.github.gfvdataweb.bolaof1.apoio.StatusDoPainel
import io.github.gfvdataweb.bolaof1.apoio.TemporadaReal
import io.github.gfvdataweb.bolaof1.data.ErroDeDados
import io.github.gfvdataweb.bolaof1.data.EstadoDados
import io.github.gfvdataweb.bolaof1.data.PipelineRepositorio
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.data.VersaoPublicada
import io.github.gfvdataweb.bolaof1.ui.comum.ConteudoComDados
import io.github.gfvdataweb.bolaof1.ui.configuracoes.ConfiguracoesTela
import io.github.gfvdataweb.bolaof1.ui.configuracoes.EstadoDasConfiguracoes
import io.github.gfvdataweb.bolaof1.ui.corridas.CorridasTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EnviarTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EstadoDoEnvio
import io.github.gfvdataweb.bolaof1.ui.enviar.EstadoDoPipeline
import io.github.gfvdataweb.bolaof1.ui.enviar.SecaoDoPipeline
import io.github.gfvdataweb.bolaof1.ui.hall.HallOfFameTela
import io.github.gfvdataweb.bolaof1.ui.ranking.RankingTela
import io.github.gfvdataweb.bolaof1.ui.rendimento.RendimentoTela
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasPorJogador
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasPorPiloto
import io.github.gfvdataweb.bolaof1.ui.temporada.palpitesDaRodada
import io.github.gfvdataweb.bolaof1.ui.temporada.rodadasPontuadas
import io.github.gfvdataweb.bolaof1.ui.theme.BolaoF1Theme
import io.github.gfvdataweb.bolaof1.ui.versao.AvisoDeNovaVersao
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
    fun corridaPassaPorPontosPalpitesEFechaACadaToque() {
        compose.setContent { BolaoF1Theme(escuro = false) { CorridasTela(temporada) } }
        val ultima = temporada.classificacao.rodadas.maxBy { it.numero }
        val titulo = "R${ultima.numero} · ${ultima.corrida}"
        val rodada = checkNotNull(palpitesDaRodada(temporada, rodadasPontuadas(temporada).first()))

        // A rodada mais recente começa nos pontos.
        compose.onNodeWithText("Toque para ver os palpites").assertExists()
        compose.onNodeWithText(titulo).performClick()

        compose.onNodeWithText("Toque para fechar").assertExists()
        compose.onNodeWithText(rodada.palpites.first().nome).assertExists()

        compose.onNodeWithText(titulo).performClick()
        compose.onNodeWithText("Toque para fechar").assertDoesNotExist()
        compose.onNodeWithText("Toque para ver os palpites").assertDoesNotExist()
    }

    @Test
    fun rendimentoMostraOsPilotosEAlternaParaJogadores() {
        compose.setContent { BolaoF1Theme(escuro = false) { RendimentoTela(temporada) } }
        val melhor = linhasPorPiloto(temporada.palpites, null).first()
        compose.onNodeWithText(melhor.codigo).assertExists()

        compose.onNodeWithText("Por jogador").performClick()
        compose.onNodeWithText(linhasPorJogador(temporada.palpites, null).first().nome).assertExists()
    }

    @Test
    fun hallDeFameAbreOAnoEscolhidoNaListaDeTemporadas() {
        var aberto: Int? = null
        compose.setContent {
            BolaoF1Theme { HallOfFameTela(HistoricoReal.historico, aoAbrirAno = { aberto = it }) }
        }
        compose.onNodeWithText("Temporadas").performClick()
        compose.onNodeWithText("2025").performClick()
        assertEquals(2025, aberto)
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
    fun pipelineMostraRodadaEtapasEOLinkDaExecucao() {
        val site = PipelineRepositorio.extrairDoBolao(StatusDoPainel.texto)
        compose.setContent {
            BolaoF1Theme {
                // A seção é mais alta que a tela padrão do Robolectric: rola como na aba Enviar.
                Column(Modifier.verticalScroll(rememberScrollState())) { SecaoDoPipeline(EstadoDoPipeline(site = site)) }
            }
        }

        compose.onNodeWithText("Última atualização").assertIsDisplayed()
        compose.onNodeWithText("Rodada 17").assertIsDisplayed()
        compose.onNodeWithText("Palpites lidos e rodada identificada").assertIsDisplayed()
        compose.onNodeWithText("Ver execução").performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("Não foi possível ver o andamento").assertDoesNotExist()
    }

    @Test
    fun pipelineComFalhaAvisaDiscretamenteSemTitulo() {
        compose.setContent { BolaoF1Theme { SecaoDoPipeline(EstadoDoPipeline(falhou = true)) } }
        compose.onNodeWithText("Não foi possível ver o andamento").assertIsDisplayed()
        compose.onNodeWithText("Última atualização").assertDoesNotExist()
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

    @Test
    fun avisoDeNovaVersaoOfereceBaixar() {
        var baixou = false
        val publicada = VersaoPublicada("0.2.0", build = 20, urlDoApk = "https://exemplo/apk", urlDaPagina = "")
        compose.setContent {
            BolaoF1Theme { AvisoDeNovaVersao(publicada, aoBaixar = { baixou = true }, aoDispensar = {}) }
        }
        compose.onNodeWithText("Nova versão 0.2.0 disponível").assertIsDisplayed()
        compose.onNodeWithText("Baixar").performClick()
        assertTrue(baixou)
    }
}
