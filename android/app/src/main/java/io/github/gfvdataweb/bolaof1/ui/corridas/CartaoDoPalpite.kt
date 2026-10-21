package io.github.gfvdataweb.bolaof1.ui.corridas

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.ui.comum.Piloto
import io.github.gfvdataweb.bolaof1.ui.comum.SeloDePontos
import io.github.gfvdataweb.bolaof1.ui.comum.corDosPontos
import io.github.gfvdataweb.bolaof1.ui.temporada.PalpiteExibido

/** O palpite pontuado de um jogador na rodada: top N com selo de pontos e o piloto da rodada. */
@Composable
fun CartaoDoPalpite(palpite: PalpiteExibido, temBonus: Boolean) {
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
