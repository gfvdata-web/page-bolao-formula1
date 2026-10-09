package io.github.gfvdataweb.bolaof1.ui.palpites

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.ui.comum.Piloto
import io.github.gfvdataweb.bolaof1.ui.comum.SeloDePontos
import io.github.gfvdataweb.bolaof1.ui.comum.corDosPontos
import io.github.gfvdataweb.bolaof1.ui.comum.dataCurta
import io.github.gfvdataweb.bolaof1.ui.temporada.PalpiteExibido
import io.github.gfvdataweb.bolaof1.ui.temporada.RodadaDosPalpites
import io.github.gfvdataweb.bolaof1.ui.temporada.palpitesDaRodada
import io.github.gfvdataweb.bolaof1.ui.temporada.rodadasPontuadas

/** Aba Palpites: escolhe a rodada e vê o palpite pontuado de cada jogador. */
@Composable
fun PalpitesTela(temporada: Temporada, modifier: Modifier = Modifier) {
    val rodadas = rodadasPontuadas(temporada)
    var escolhida by rememberSaveable { mutableStateOf(rodadas.firstOrNull()) }
    val rodada = escolhida?.let { palpitesDaRodada(temporada, it) }

    Column(modifier) {
        LazyRow(
            contentPadding = PaddingValues(horizontal = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(rodadas) { numero ->
                FilterChip(
                    selected = numero == escolhida,
                    onClick = { escolhida = numero },
                    label = { Text(stringResource(R.string.rodada_curta, numero)) },
                )
            }
        }
        if (rodada == null) {
            Text(
                stringResource(R.string.sem_rodadas),
                modifier = Modifier.padding(16.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            ListaDePalpites(rodada)
        }
    }
}

@Composable
private fun ListaDePalpites(rodada: RodadaDosPalpites) {
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Column {
                Text(
                    stringResource(R.string.rodada_titulo, rodada.numero, rodada.corrida) + " · " + dataCurta(rodada.data),
                    style = MaterialTheme.typography.titleMedium,
                )
                Spacer(Modifier.height(4.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    rodada.resultado.forEach { Piloto(it.codigo, it.corHex) }
                }
                if (rodada.temBonus && rodada.pilotoDaRodada != null) {
                    Text(
                        stringResource(R.string.piloto_da_rodada, rodada.pilotoDaRodada),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
        items(rodada.palpites, key = { it.id }) { palpite ->
            CartaoDoPalpite(palpite, rodada.temBonus)
        }
    }
}

@Composable
private fun CartaoDoPalpite(palpite: PalpiteExibido, temBonus: Boolean) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(palpite.nome, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                Text(
                    stringResource(R.string.pontos, palpite.total),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                )
            }
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                palpite.itens.forEach { item ->
                    SeloDePontos(item.pontos, Modifier.weight(1f)) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                stringResource(R.string.posicao, item.posicao),
                                style = MaterialTheme.typography.labelSmall,
                                color = corDosPontos(item.pontos),
                            )
                            Piloto(item.codigo, item.corHex, compacto = true)
                        }
                    }
                }
            }
            if (temBonus && palpite.chuteBonus != null) {
                Spacer(Modifier.height(8.dp))
                Text(
                    palpite.posicaoRealBonus?.let {
                        stringResource(R.string.bonus_com_real, palpite.chuteBonus, it, palpite.pontosBonus)
                    } ?: stringResource(R.string.bonus_sem_real, palpite.chuteBonus, palpite.pontosBonus),
                    style = MaterialTheme.typography.bodySmall,
                    color = corDosPontos(if (palpite.pontosBonus > 0) 2 else 0),
                )
            }
        }
    }
}
