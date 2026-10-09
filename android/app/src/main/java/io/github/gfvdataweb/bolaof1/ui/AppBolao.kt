package io.github.gfvdataweb.bolaof1.ui

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.compose.collectAsStateWithLifecycle
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
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.ui.comum.ConteudoComDados
import io.github.gfvdataweb.bolaof1.ui.configuracoes.ConfiguracoesTela
import io.github.gfvdataweb.bolaof1.ui.configuracoes.ConfiguracoesViewModel
import io.github.gfvdataweb.bolaof1.ui.corridas.CorridasTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EnviarTela
import io.github.gfvdataweb.bolaof1.ui.enviar.EnviarViewModel
import io.github.gfvdataweb.bolaof1.ui.palpites.PalpitesTela
import io.github.gfvdataweb.bolaof1.ui.ranking.RankingTela
import io.github.gfvdataweb.bolaof1.ui.temporada.TemporadaViewModel
import io.github.gfvdataweb.bolaof1.ui.versao.AvisoDeNovaVersao
import io.github.gfvdataweb.bolaof1.ui.versao.SituacaoDaVersao
import io.github.gfvdataweb.bolaof1.ui.versao.VersaoViewModel
import kotlinx.serialization.Serializable

// Rotas da navegação (type-safe: cada tela é um objeto serializável).
@Serializable
object RotaRanking

@Serializable
object RotaCorridas

@Serializable
object RotaPalpites

@Serializable
object RotaEnviar

@Serializable
object RotaConfiguracoes

private data class Aba(val rota: Any, @param:StringRes val rotulo: Int, val icone: ImageVector)

private val ABAS = listOf(
    Aba(RotaRanking, R.string.aba_ranking, Icons.Filled.Star),
    Aba(RotaCorridas, R.string.aba_corridas, Icons.Filled.DateRange),
    Aba(RotaPalpites, R.string.aba_palpites, Icons.AutoMirrored.Filled.List),
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
    val entradaAtual by navegacao.currentBackStackEntryAsState()
    val emConfiguracoes = entradaAtual?.destination?.hasRoute(RotaConfiguracoes::class) == true
    val versaoViewModel: VersaoViewModel = viewModel(factory = VersaoViewModel.fabrica(container.verificadorDeAtualizacao, build))
    val estadoDaVersao by versaoViewModel.estado.collectAsStateWithLifecycle()
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
                composable<RotaPalpites> {
                    ConteudoComDados(estado, temporadaViewModel::atualizar) { PalpitesTela(it) }
                }
                composable<RotaEnviar> {
                    val enviar: EnviarViewModel = viewModel(factory = EnviarViewModel.fabrica(container.envio, container.configuracoes))
                    val estadoDoEnvio by enviar.estado.collectAsStateWithLifecycle()
                    EnviarTela(
                        estado = estadoDoEnvio,
                        aoMudarTexto = enviar::mudarTexto,
                        aoMudarRodada = enviar::mudarRodada,
                        aoEnviar = enviar::enviar,
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

/** Troca de aba sem empilhar telas (o "voltar" sai do app a partir de qualquer aba). */
private fun NavHostController.irParaAba(rota: Any) {
    navigate(rota) {
        popUpTo(graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}
