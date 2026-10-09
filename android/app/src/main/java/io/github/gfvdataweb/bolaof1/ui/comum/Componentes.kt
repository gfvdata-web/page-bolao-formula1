package io.github.gfvdataweb.bolaof1.ui.comum

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.data.ErroDeDados
import io.github.gfvdataweb.bolaof1.data.EstadoDados
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.ui.theme.LocalCoresDosPontos
import java.time.ZoneId

/**
 * Moldura comum das abas da temporada: carregando, erro sem dados, ou o
 * conteúdo com "puxar para atualizar" e a linha de quando os dados são.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConteudoComDados(
    estado: EstadoDados<Temporada>,
    aoAtualizar: () -> Unit,
    modifier: Modifier = Modifier,
    agora: () -> Long = System::currentTimeMillis,
    conteudo: @Composable (Temporada) -> Unit,
) {
    val temporada = estado.dados
    when {
        temporada == null && estado.atualizando -> Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        temporada == null -> SemDados(estado.erro, aoAtualizar, modifier)
        else -> PullToRefreshBox(
            isRefreshing = estado.atualizando,
            onRefresh = aoAtualizar,
            modifier = modifier.fillMaxSize(),
        ) {
            Column(Modifier.fillMaxSize()) {
                LinhaDeAtualizacao(estado, agora())
                Box(Modifier.weight(1f)) { conteudo(temporada) }
            }
        }
    }
}

@Composable
private fun SemDados(erro: ErroDeDados?, aoTentarDeNovo: () -> Unit, modifier: Modifier) {
    Column(
        modifier.fillMaxSize().padding(32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(
                if (erro == ErroDeDados.FORMATO_INESPERADO) R.string.erro_formato else R.string.erro_sem_dados,
            ),
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(16.dp))
        Button(onClick = aoTentarDeNovo) { Text(stringResource(R.string.tentar_de_novo)) }
    }
}

@Composable
private fun LinhaDeAtualizacao(estado: EstadoDados<Temporada>, agora: Long) {
    val quando = estado.atualizadoEm ?: return
    val idade = when (val idade = idadeDosDados(agora, quando, ZoneId.systemDefault())) {
        Idade.AgoraMesmo -> stringResource(R.string.idade_agora)
        is Idade.Minutos -> stringResource(R.string.idade_minutos, idade.quantos)
        is Idade.Horas -> stringResource(R.string.idade_horas, idade.quantas)
        is Idade.EmData -> stringResource(R.string.idade_data, idade.texto)
    }
    val (texto, cor) = when (estado.erro) {
        null -> stringResource(R.string.atualizado, idade) to MaterialTheme.colorScheme.onSurfaceVariant
        ErroDeDados.FALHA_NO_DOWNLOAD -> stringResource(R.string.offline_dados_salvos, idade) to MaterialTheme.colorScheme.error
        ErroDeDados.FORMATO_INESPERADO -> stringResource(R.string.formato_dados_salvos, idade) to MaterialTheme.colorScheme.error
    }
    Text(
        text = texto,
        style = MaterialTheme.typography.labelSmall,
        color = cor,
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
    )
}

/** Código do piloto com a bolinha da cor da equipe ([compacto] cabe 6 numa linha). */
@Composable
fun Piloto(codigo: String, corHex: String?, modifier: Modifier = Modifier, compacto: Boolean = false) {
    Row(modifier, verticalAlignment = Alignment.CenterVertically) {
        Box(
            Modifier
                .size(if (compacto) 6.dp else 8.dp)
                .background(argbDeHex(corHex)?.let { Color(it) } ?: MaterialTheme.colorScheme.outline, CircleShape),
        )
        Spacer(Modifier.size(if (compacto) 2.dp else 4.dp))
        Text(
            codigo,
            style = if (compacto) MaterialTheme.typography.labelMedium else MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Medium,
            maxLines = 1,
        )
    }
}

/** Selo de pontos de um item do palpite: 2 (verde), 1 (amarelo), 0 (cinza). */
@Composable
fun SeloDePontos(pontos: Int, modifier: Modifier = Modifier, conteudo: @Composable () -> Unit) {
    val cores = LocalCoresDosPontos.current
    val fundo = when (pontos) {
        2 -> cores.doisFundo
        1 -> cores.umFundo
        else -> cores.zeroFundo
    }
    Box(
        modifier
            .background(fundo, RoundedCornerShape(6.dp))
            .padding(horizontal = 4.dp, vertical = 6.dp),
        contentAlignment = Alignment.Center,
    ) { conteudo() }
}

/** Cor do texto de pontos (2/1/0), na paleta do site. */
@Composable
fun corDosPontos(pontos: Int): Color {
    val cores = LocalCoresDosPontos.current
    return when (pontos) {
        2 -> cores.dois
        1 -> cores.um
        else -> cores.zeroTexto
    }
}
