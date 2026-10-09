package io.github.gfvdataweb.bolaof1.ui.ranking

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.ui.comum.proximoQuali
import io.github.gfvdataweb.bolaof1.ui.temporada.LinhaRanking
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasDoRanking
import java.time.Instant
import java.time.ZoneId

/** Aba Ranking (Geral): resumo da temporada e a classificação. */
@Composable
fun RankingTela(temporada: Temporada, rodape: String, modifier: Modifier = Modifier) {
    val linhas = linhasDoRanking(temporada)
    LazyColumn(modifier, contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item { ResumoDaTemporada(temporada) }
        item {
            Card(Modifier.fillMaxWidth()) {
                linhas.forEachIndexed { indice, linha ->
                    if (indice > 0) HorizontalDivider(color = MaterialTheme.colorScheme.outline)
                    LinhaDoRanking(linha)
                }
            }
        }
        items(listOf(rodape)) {
            Text(
                it,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}

@Composable
private fun ResumoDaTemporada(temporada: Temporada) {
    val info = temporada.info
    val proximo = proximoQuali(temporada.calendario, Instant.now(), ZoneId.systemDefault())
    Column(Modifier.fillMaxWidth()) {
        if (info != null) {
            Text(
                stringResource(R.string.resumo_corridas, info.rodadas, info.rodadasTotais),
                style = MaterialTheme.typography.titleMedium,
            )
        }
        if (proximo != null) {
            Text(
                stringResource(R.string.proximo_quali, proximo.numero, proximo.corrida, proximo.quandoFormatado),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun LinhaDoRanking(linha: LinhaRanking) {
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            linha.posicao.toString(),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = if (linha.posicao <= 3) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(32.dp),
        )
        Column(Modifier.weight(1f)) {
            Text(linha.nome, style = MaterialTheme.typography.titleMedium)
            val detalhe = stringResource(R.string.ranking_detalhe, linha.media, linha.rodadasJogadas)
            Text(
                if (linha.pontosCompensacao > 0) {
                    detalhe + stringResource(R.string.ranking_compensacao, linha.pontosCompensacao)
                } else {
                    detalhe
                },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Text(
            stringResource(R.string.pontos, linha.total),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
        )
    }
}
