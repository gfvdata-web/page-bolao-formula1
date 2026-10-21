package io.github.gfvdataweb.bolaof1.ui

import androidx.activity.compose.BackHandler
import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.TextButton
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import io.github.gfvdataweb.bolaof1.AppContainer
import io.github.gfvdataweb.bolaof1.data.ResultadoDoEnvio
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.ui.comum.ConteudoComDados
import io.github.gfvdataweb.bolaof1.ui.configuracoes.ConfiguracoesTela
import io.github.gfvdataweb.bolaof1.ui.configuracoes.ConfiguracoesViewModel
import io.github.gfvdataweb.bolaof1.ui.corridas.CorridasTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EnviarTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EnviarViewModel
import io.github.gfvdataweb.bolaof1.ui.enviar.PipelineViewModel
import io.github.gfvdataweb.bolaof1.ui.enviar.deveContinuarAcompanhando
import io.github.gfvdataweb.bolaof1.ui.hall.HallOfFameTela
import io.github.gfvdataweb.bolaof1.ui.hall.HistoricoViewModel
import io.github.gfvdataweb.bolaof1.ui.rendimento.RendimentoTela
import io.github.gfvdataweb.bolaof1.ui.ranking.RankingTela
import io.github.gfvdataweb.bolaof1.ui.temporada.TemporadaViewModel
import io.github.gfvdataweb.bolaof1.ui.temporada.deveOferecerVoltarParaAtual
import io.github.gfvdataweb.bolaof1.ui.versao.AvisoDeNovaVersao
import io.github.gfvdataweb.bolaof1.ui.versao.SituacaoDaVersao
import io.github.gfvdataweb.bolaof1.ui.versao.VersaoViewModel
import kotlinx.coroutines.delay
import kotlinx.serialization.Serializable

// Rotas da navegação (type-safe: cada tela é um objeto serializável).
@Serializable
object RotaRanking

@Serializable
object RotaCorridas

@Serializable
object RotaRendimento

@Serializable
object RotaHall

@Serializable
object RotaEnviar

@Serializable
object RotaConfiguracoes

private data class Aba(val rota: Any, @param:StringRes val rotulo: Int, val icone: ImageVector)

private val ABAS = listOf(
    Aba(RotaRanking, R.string.aba_ranking, Icons.Filled.Star),
    Aba(RotaCorridas, R.string.aba_corridas, Icons.Filled.DateRange),
    Aba(RotaRendimento, R.string.aba_rendimento, Icons.Filled.Check),
    Aba(RotaHall, R.string.aba_hall, Icons.Filled.Favorite),
    Aba(RotaEnviar, R.string.aba_enviar, Icons.AutoMirrored.Filled.Send),
)

/** Raiz da interface: barra superior, abas embaixo e a tela escolhida. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppBolao(container: AppContainer, versao: String, build: Int) {
    val navegacao = rememberNavController()
    // Escopo da Activity: as três abas da temporada dividem um único download.
    val temporadaViewModel: TemporadaViewModel = viewModel(factory = TemporadaViewModel.fabrica(container.temporadaRepositorio))
    val estado by temporadaViewModel.estado.collectAsStateWithLifecycle()
    // Também no escopo da Activity: o histórico é baixado uma vez, para a aba Hall of Fame.
    val historicoViewModel: HistoricoViewModel = viewModel(factory = HistoricoViewModel.fabrica(container.historicoRepositorio))
    val estadoDoHistorico by historicoViewModel.estado.collectAsStateWithLifecycle()
    val anoEscolhido by temporadaViewModel.anoEscolhido.collectAsStateWithLifecycle()
    val entradaAtual by navegacao.currentBackStackEntryAsState()
    val emConfiguracoes = entradaAtual?.destination?.hasRoute(RotaConfiguracoes::class) == true
    val versaoViewModel: VersaoViewModel = viewModel(factory = VersaoViewModel.fabrica(container.verificadorDeAtualizacao, build))
    val estadoDaVersao by versaoViewModel.estado.collectAsStateWithLifecycle()
    val oferecerVoltar = deveOferecerVoltarParaAtual(estado.dados, anoEscolhido)
    // Sem isto, o "voltar" do sistema sairia do app em vez de voltar à temporada atual.
    BackHandler(enabled = oferecerVoltar && !emConfiguracoes) { temporadaViewModel.voltarParaAtual() }
    val navegador = LocalUriHandler.current
    val baixarNovaVersao = { estadoDaVersao.publicada?.let { navegador.openUri(it.urlDoApk) } }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        when {
                            emConfiguracoes -> stringResource(R.string.config_titulo)
                            estado.dados != null -> stringResource(R.string.titulo_com_ano, estado.dados?.ano ?: 0)
                            else -> stringResource(R.string.app_titulo)
                        },
                    )
                },
                navigationIcon = {
                    if (emConfiguracoes) {
                        IconButton(onClick = { navegacao.popBackStack() }) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(R.string.voltar))
                        }
                    }
                },
                actions = {
                    if (oferecerVoltar && !emConfiguracoes) {
                        TextButton(onClick = temporadaViewModel::voltarParaAtual) {
                            val atual = estado.dados?.atual
                            Text(
                                if (atual != null) stringResource(R.string.voltar_para_ano, atual)
                                else stringResource(R.string.voltar_para_atual),
                            )
                        }
                    }
                    if (!emConfiguracoes) {
                        IconButton(onClick = { navegacao.navigate(RotaConfiguracoes) { launchSingleTop = true } }) {
                            Icon(Icons.Filled.Settings, contentDescription = stringResource(R.string.config_titulo))
                        }
                    }
                },
            )
        },
        bottomBar = {
            NavigationBar {
                ABAS.forEach { aba ->
                    NavigationBarItem(
                        selected = entradaAtual?.destination?.hierarchy?.any { it.hasRoute(aba.rota::class) } == true,
                        onClick = { navegacao.irParaAba(aba.rota) },
                        icon = { Icon(aba.icone, contentDescription = null) },
                        label = { Text(stringResource(aba.rotulo)) },
                    )
                }
            }
        },
    ) { espaco ->
        Column(Modifier.padding(espaco)) {
            val publicada = estadoDaVersao.publicada
            if (estadoDaVersao.mostrarAviso && publicada != null) {
                AvisoDeNovaVersao(publicada, aoBaixar = { baixarNovaVersao() }, aoDispensar = versaoViewModel::dispensar)
            }
            NavHost(navegacao, startDestination = RotaRanking, modifier = Modifier.weight(1f)) {
                composable<RotaRanking> {
                    ConteudoComDados(estado, temporadaViewModel::atualizar) { RankingTela(it) }
                }
                composable<RotaCorridas> {
                    ConteudoComDados(estado, temporadaViewModel::atualizar) { CorridasTela(it) }
                }
                composable<RotaRendimento> {
                    ConteudoComDados(estado, temporadaViewModel::atualizar) { RendimentoTela(it) }
                }
                composable<RotaHall> {
                    ConteudoComDados(estadoDoHistorico, historicoViewModel::atualizar) { historico ->
                        HallOfFameTela(
                            historico,
                            aoAbrirAno = { ano ->
                                if (ano == historico.atual) temporadaViewModel.voltarParaAtual() else temporadaViewModel.abrirAno(ano)
                                navegacao.irParaAba(RotaRanking)
                            },
                        )
                    }
                }
                composable<RotaEnviar> {
                    val enviar: EnviarViewModel = viewModel(factory = EnviarViewModel.fabrica(container.envio, container.configuracoes))
                    val estadoDoEnvio by enviar.estado.collectAsStateWithLifecycle()
                    val pipeline: PipelineViewModel = viewModel(factory = PipelineViewModel.fabrica(container.pipelineRepositorio))
                    val estadoDoPipeline by pipeline.estado.collectAsStateWithLifecycle()
                    AcompanharPipeline(pipeline, enviado = estadoDoEnvio.resultado == ResultadoDoEnvio.Enviado)
                    EnviarTela(
                        estado = estadoDoEnvio,
                        aoMudarTexto = enviar::mudarTexto,
                        aoMudarRodada = enviar::mudarRodada,
                        aoEnviar = enviar::enviar,
                        pipeline = estadoDoPipeline,
                        aoAbrirConfiguracoes = { navegacao.navigate(RotaConfiguracoes) { launchSingleTop = true } },
                    )
                }
                composable<RotaConfiguracoes> {
                    val configuracoes: ConfiguracoesViewModel = viewModel(factory = ConfiguracoesViewModel.fabrica(container.configuracoes))
                    val estadoDasConfiguracoes by configuracoes.estado.collectAsStateWithLifecycle()
                    ConfiguracoesTela(
                        estado = estadoDasConfiguracoes,
                        aoMudarUrl = configuracoes::mudarUrl,
                        aoMudarChave = configuracoes::mudarChave,
                        aoSalvar = configuracoes::salvar,
                        versao = versao,
                        build = build,
                        extras = { SituacaoDaVersao(estadoDaVersao, aoBaixar = { baixarNovaVersao() }) },
                    )
                }
            }
        }
    }
}

/** Pausa entre as consultas ao painel enquanto o pipeline está em curso. */
private const val INTERVALO_DO_PIPELINE_MS = 60_000L

/** Consultas extras depois de um envio com sucesso (o pipeline demora a aparecer como em curso). */
private const val CONSULTAS_APOS_ENVIO = 5

/**
 * Consulta o painel ao entrar na aba e logo após um envio com sucesso; depois, a
 * cada 60 s enquanto o pipeline estiver em curso. Só roda com a tela visível
 * (a aba na composição e o app em primeiro plano).
 */
@Composable
private fun AcompanharPipeline(pipeline: PipelineViewModel, enviado: Boolean) {
    val ciclo = LocalLifecycleOwner.current.lifecycle
    LaunchedEffect(enviado) {
        ciclo.repeatOnLifecycle(Lifecycle.State.STARTED) {
            pipeline.atualizar()
            var extras = if (enviado) CONSULTAS_APOS_ENVIO else 0
            while (true) {
                delay(INTERVALO_DO_PIPELINE_MS)
                if (deveContinuarAcompanhando(pipeline.estado.value.site) || extras > 0) pipeline.atualizar()
                if (extras > 0) extras--
            }
        }
    }
}

/** Troca de aba sem empilhar telas (o "voltar" sai do app a partir de qualquer aba). */
private fun NavHostController.irParaAba(rota: Any) {
    navigate(rota) {
        popUpTo(graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
