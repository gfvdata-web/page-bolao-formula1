package io.github.gfvdataweb.bolaof1.ui.corridas

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.ui.comum.Piloto
import io.github.gfvdataweb.bolaof1.ui.comum.dataCurta
import io.github.gfvdataweb.bolaof1.ui.temporada.CartaoCorrida
import io.github.gfvdataweb.bolaof1.ui.temporada.cartoesDasCorridas

/** Aba Corridas: resultado do quali e pontos de cada jogador, por rodada. */
@Composable
fun CorridasTela(temporada: Temporada, modifier: Modifier = Modifier) {
    val cartoes = cartoesDasCorridas(temporada)
    // A rodada mais recente começa aberta; o toque abre/fecha as outras.
    var abertas by rememberSaveable { mutableStateOf(listOfNotNull(cartoes.firstOrNull()?.numero)) }
    LazyColumn(modifier, contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        items(cartoes, key = { it.numero }) { cartao ->
            val aberta = cartao.numero in abertas
            CartaoDaCorrida(cartao, aberta) {
                abertas = if (aberta) abertas - cartao.numero else abertas + cartao.numero
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class) // FlowRow
@Composable
private fun CartaoDaCorrida(cartao: CartaoCorrida, aberta: Boolean, aoTocar: () -> Unit) {
    Card(Modifier.fillMaxWidth().clickable(onClick = aoTocar)) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    stringResource(R.string.rodada_titulo, cartao.numero, cartao.corrida),
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f),
                )
                Text(
                    if (cartao.sprint) stringResource(R.string.data_sprint, dataCurta(cartao.data)) else dataCurta(cartao.data),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Spacer(Modifier.height(8.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                cartao.topN.forEach { piloto ->
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            stringResource(R.string.posicao, piloto.posicao ?: 0),
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Spacer(Modifier.width(4.dp))
                        Piloto(piloto.codigo, piloto.corHex)
                    }
                }
            }
            cartao.pilotoDaRodada?.let { piloto ->
                Spacer(Modifier.height(8.dp))
                Text(
                    piloto.posicao?.let { stringResource(R.string.piloto_da_rodada_pos, piloto.codigo, it) }
                        ?: stringResource(R.string.piloto_da_rodada_sem_pos, piloto.codigo),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (aberta) {
                Spacer(Modifier.height(8.dp))
                HorizontalDivider(color = MaterialTheme.colorScheme.outline)
                cartao.pontos.forEach { jogador ->
                    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Text(
                            if (jogador.compensado) stringResource(R.string.sem_palpite, jogador.nome) else jogador.nome,
                            style = MaterialTheme.typography.bodyMedium,
                            fontStyle = if (jogador.compensado) FontStyle.Italic else FontStyle.Normal,
                            color = if (jogador.compensado) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.weight(1f),
                        )
                        Text(
                            stringResource(R.string.pontos, jogador.pontos),
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Medium,
                        )
                    }
                }
            } else {
                Spacer(Modifier.height(4.dp))
                Text(
                    stringResource(R.string.toque_para_ver_pontos),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }
    }
}
