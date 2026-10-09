package io.github.gfvdataweb.bolaof1.ui

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.ui.comum.ConteudoComDados
import io.github.gfvdataweb.bolaof1.ui.corridas.CorridasTela
import io.github.gfvdataweb.bolaof1.ui.palpites.PalpitesTela
import io.github.gfvdataweb.bolaof1.ui.ranking.RankingTela
import io.github.gfvdataweb.bolaof1.ui.temporada.TemporadaViewModel
import kotlinx.serialization.Serializable

// Rotas da navegação (type-safe: cada aba é um objeto serializável).
@Serializable
object RotaRanking

@Serializable
object RotaCorridas

@Serializable
object RotaPalpites

private data class Aba(val rota: Any, @param:StringRes val rotulo: Int, val icone: ImageVector)

private val ABAS = listOf(
    Aba(RotaRanking, R.string.aba_ranking, Icons.Filled.Star),
    Aba(RotaCorridas, R.string.aba_corridas, Icons.Filled.DateRange),
    Aba(RotaPalpites, R.string.aba_palpites, Icons.AutoMirrored.Filled.List),
)

/** Raiz da interface: barra superior, abas embaixo e a tela da aba escolhida. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppBolao(temporadaViewModel: TemporadaViewModel, versao: String, build: Int) {
    val navegacao = rememberNavController()
    val estado by temporadaViewModel.estado.collectAsStateWithLifecycle()
    val entradaAtual by navegacao.currentBackStackEntryAsState()
    val rodape = stringResource(R.string.rodape_versao, versao, build)

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(estado.dados?.ano?.let { stringResource(R.string.titulo_com_ano, it) } ?: stringResource(R.string.app_titulo))
                },
            )
        },
        bottomBar = {
            NavigationBar {
                ABAS.forEach { aba ->
                    NavigationBarItem(
                        selected = entradaAtual?.destination?.hierarchy?.any { it.hasRoute(aba.rota::class) } == true,
                        onClick = {
                            navegacao.navigate(aba.rota) {
                                popUpTo(navegacao.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(aba.icone, contentDescription = null) },
                        label = { Text(stringResource(aba.rotulo)) },
                    )
                }
            }
        },
    ) { espaco ->
        NavHost(navegacao, startDestination = RotaRanking, modifier = Modifier.padding(espaco)) {
            composable<RotaRanking> {
                ConteudoComDados(estado, temporadaViewModel::atualizar) { RankingTela(it, rodape) }
            }
            composable<RotaCorridas> {
                ConteudoComDados(estado, temporadaViewModel::atualizar) { CorridasTela(it) }
            }
            composable<RotaPalpites> {
                ConteudoComDados(estado, temporadaViewModel::atualizar) { PalpitesTela(it) }
            }
        }
    }
}
