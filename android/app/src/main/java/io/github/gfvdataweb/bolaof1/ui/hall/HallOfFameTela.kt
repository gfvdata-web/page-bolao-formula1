package io.github.gfvdataweb.bolaof1.ui.hall

import androidx.compose.foundation.clickable
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
import io.github.gfvdataweb.bolaof1.data.Historico
import io.github.gfvdataweb.bolaof1.ui.comum.SeletorDeModo
import io.github.gfvdataweb.bolaof1.ui.temporada.CartaoDoAno
import io.github.gfvdataweb.bolaof1.ui.temporada.LinhaDoHall
import io.github.gfvdataweb.bolaof1.ui.temporada.cartoesDosAnos
import io.github.gfvdataweb.bolaof1.ui.temporada.rankingDoHall

private enum class ModoDoHall { JOGADORES, TEMPORADAS }

/**
 * Aba Hall of Fame: ranking de medalhas dos jogadores e um cartão por temporada.
 * Tocar num cartão abre aquela temporada ([aoAbrirAno]).
 */
@Composable
fun HallOfFameTela(historico: Historico, aoAbrirAno: (Int) -> Unit, modifier: Modifier = Modifier) {
    var modo by rememberSaveable { mutableStateOf(ModoDoHall.JOGADORES) }
    LazyColumn(modifier, contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            SeletorDeModo(
                opcoes = listOf(stringResource(R.string.hall_jogadores), stringResource(R.string.hall_temporadas)),
                selecionado = modo.ordinal,
                aoEscolher = { modo = ModoDoHall.entries[it] },
            )
        }
        when (modo) {
            ModoDoHall.JOGADORES -> {
                val linhas = rankingDoHall(historico.hall, historico.classificacoes)
                if (linhas.isEmpty()) item { Text(stringResource(R.string.hall_vazio)) }
                items(linhas, key = { it.id }) { LinhaDoHallDeFama(it) }
            }
            ModoDoHall.TEMPORADAS ->
                items(cartoesDosAnos(historico), key = { it.ano }) { CartaoDaTemporada(it, aoAbrirAno) }
        }
    }
}

@Composable
private fun LinhaDoHallDeFama(linha: LinhaDoHall) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    linha.nome,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f),
                )
                Text(
                    stringResource(R.string.hall_medalhas, linha.ouro, linha.prata, linha.bronze),
                    style = MaterialTheme.typography.titleSmall,
                )
            }
            val acerto = linha.acerto?.let { stringResource(R.string.hall_acerto, it) } ?: stringResource(R.string.hall_sem_acerto)
            Text(
                stringResource(R.string.hall_detalhe, linha.participacoes, linha.pontos, acerto),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun CartaoDaTemporada(cartao: CartaoDoAno, aoAbrirAno: (Int) -> Unit) {
    Card(Modifier.fillMaxWidth().clickable { aoAbrirAno(cartao.ano) }) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    cartao.ano.toString(),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.width(72.dp),
                )
                Text(
                    stringResource(R.string.hall_numero_jogadores, cartao.jogadores),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.weight(1f),
                )
                if (cartao.emAndamento) {
                    Text(
                        stringResource(R.string.hall_em_andamento),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
            if (cartao.ouro != null) {
                Text(
                    stringResource(R.string.hall_podio, cartao.ouro, cartao.prata.orEmpty(), cartao.bronze.orEmpty()),
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}
