package io.github.gfvdataweb.bolaof1.ui.rendimento

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.ui.comum.Piloto
import io.github.gfvdataweb.bolaof1.ui.comum.SeletorDeModo
import io.github.gfvdataweb.bolaof1.ui.comum.argbDeHex
import io.github.gfvdataweb.bolaof1.ui.comum.corDosPontos
import io.github.gfvdataweb.bolaof1.ui.temporada.LinhaPorJogador
import io.github.gfvdataweb.bolaof1.ui.temporada.LinhaPorPiloto
import io.github.gfvdataweb.bolaof1.ui.temporada.RegistroRendimento
import io.github.gfvdataweb.bolaof1.ui.temporada.diferencaParaGeral
import io.github.gfvdataweb.bolaof1.ui.temporada.jogadoresDoRendimento
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasPorJogador
import io.github.gfvdataweb.bolaof1.ui.temporada.linhasPorPiloto
import io.github.gfvdataweb.bolaof1.ui.temporada.pilotosApostados

/** Pontos máximos por aposta de top N (posição exata): a barra cheia. */
private const val MEDIA_MAXIMA = 2.0

private enum class ModoDoRendimento { PILOTO, JOGADOR }

/** Aba Rendimento: quanto cada piloto (ou cada jogador) rende por aposta. */
@OptIn(ExperimentalLayoutApi::class) // FlowRow
@Composable
fun RendimentoTela(temporada: Temporada, modifier: Modifier = Modifier) {
    val palpites = temporada.palpites
    val jogadores = jogadoresDoRendimento(palpites)
    val pilotos = pilotosApostados(palpites)
    // As seleções dos filtros recomeçam a cada ano.
    var modo by rememberSaveable { mutableStateOf(ModoDoRendimento.PILOTO) }
    val jogadoresEscolhidos = rememberSaveable(temporada.ano) { mutableStateOf(ArrayList(jogadores.map { it.first })) }
    val pilotosEscolhidos = rememberSaveable(temporada.ano) { mutableStateOf(ArrayList(pilotos)) }

    val porPiloto = modo == ModoDoRendimento.PILOTO
    val todos = if (porPiloto) jogadores.map { it.first } else pilotos
    val escolhidos = if (porPiloto) jogadoresEscolhidos else pilotosEscolhidos
    // Filtro "todos" (nulo) = sem comparação com a média geral.
    val filtro: Set<String>? = escolhidos.value.toSet().takeIf { it.size < todos.size }

    LazyColumn(modifier, contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            SeletorDeModo(
                opcoes = listOf(stringResource(R.string.rendimento_por_piloto), stringResource(R.string.rendimento_por_jogador)),
                selecionado = modo.ordinal,
                aoEscolher = { modo = ModoDoRendimento.entries[it] },
            )
        }
        item {
            Text(
                if (porPiloto) {
                    stringResource(R.string.rendimento_explicacao_piloto, temporada.classificacao.formato.topN)
                } else {
                    stringResource(R.string.rendimento_explicacao_jogador)
                },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        item {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = escolhidos.value.size == todos.size,
                    onClick = { escolhidos.value = ArrayList(todos) },
                    label = { Text(stringResource(R.string.rendimento_filtro_todos)) },
                )
                val rotulos = if (porPiloto) jogadores.toMap() else pilotos.associateWith { it }
                todos.forEach { chave ->
                    FilterChip(
                        selected = chave in escolhidos.value,
                        onClick = {
                            escolhidos.value = ArrayList(
                                if (chave in escolhidos.value) escolhidos.value - chave else escolhidos.value + chave,
                            )
                        },
                        label = { Text(rotulos[chave] ?: chave) },
                    )
                }
            }
        }
        if (escolhidos.value.isEmpty()) {
            item { Aviso(R.string.rendimento_sem_selecao) }
        } else if (porPiloto) {
            val linhas = linhasPorPiloto(palpites, filtro)
            if (linhas.isEmpty()) item { Aviso(R.string.rendimento_sem_apostas) }
            items(linhas, key = { it.codigo }) { linha -> LinhaDoPiloto(linha, temporada, comparando = filtro != null) }
        } else {
            val linhas = linhasPorJogador(palpites, filtro)
            items(linhas, key = { it.id }) { linha -> LinhaDoJogador(linha, comparando = filtro != null) }
        }
    }
}

@Composable
private fun Aviso(texto: Int) {
    Text(stringResource(texto), color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(vertical = 8.dp))
}

@Composable
private fun LinhaDoPiloto(linha: LinhaPorPiloto, temporada: Temporada, comparando: Boolean) {
    val cor = temporada.equipes.corDoPiloto(linha.codigo)
    LinhaDeRendimento(
        registro = linha.registro,
        mediaGeral = linha.mediaGeral,
        comparando = comparando,
        corDaBarra = argbDeHex(cor)?.let { Color(it) } ?: MaterialTheme.colorScheme.outline,
    ) { Piloto(linha.codigo, cor) }
}

@Composable
private fun LinhaDoJogador(linha: LinhaPorJogador, comparando: Boolean) {
    LinhaDeRendimento(
        registro = linha.registro,
        mediaGeral = linha.mediaGeral,
        comparando = comparando,
        corDaBarra = MaterialTheme.colorScheme.primary,
    ) { Text(linha.nome, style = MaterialTheme.typography.titleSmall, maxLines = 1) }
}

/** Linha comum aos dois modos: título, média (com ▲/▼ contra a geral), barra, contagens 2/1/0 e apostas. */
@Composable
private fun LinhaDeRendimento(
    registro: RegistroRendimento,
    mediaGeral: Double?,
    comparando: Boolean,
    corDaBarra: Color,
    titulo: @Composable () -> Unit,
) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.weight(1f)) { titulo() }
                if (registro.apostas > 0) {
                    Text(
                        stringResource(R.string.rendimento_media, registro.media),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                    )
                    if (comparando && mediaGeral != null) {
                        val diferenca = diferencaParaGeral(registro.media, mediaGeral)
                        Spacer(Modifier.width(8.dp))
                        Text(
                            if (diferenca >= 0) {
                                stringResource(R.string.rendimento_diferenca_acima, diferenca)
                            } else {
                                stringResource(R.string.rendimento_diferenca_abaixo, -diferenca)
                            },
                            style = MaterialTheme.typography.labelMedium,
                            color = if (diferenca >= 0) corDosPontos(2) else MaterialTheme.colorScheme.error,
                        )
                    }
                }
            }
            Spacer(Modifier.height(6.dp))
            Box(
                Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .background(MaterialTheme.colorScheme.outline, RoundedCornerShape(3.dp)),
            ) {
                Box(
                    Modifier
                        .fillMaxWidth((registro.media / MEDIA_MAXIMA).toFloat().coerceIn(0f, 1f))
                        .fillMaxHeight()
                        .background(corDaBarra, RoundedCornerShape(3.dp)),
                )
            }
            Spacer(Modifier.height(6.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(registro.exatas.toString(), style = MaterialTheme.typography.labelLarge, color = corDosPontos(2))
                Text(" · ", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(registro.dentro.toString(), style = MaterialTheme.typography.labelLarge, color = corDosPontos(1))
                Text(" · ", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(registro.fora.toString(), style = MaterialTheme.typography.labelLarge, color = corDosPontos(0))
                Spacer(Modifier.weight(1f))
                Text(
                    stringResource(R.string.rendimento_apostas, registro.apostas),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
