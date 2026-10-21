package io.github.gfvdataweb.bolaof1.ui.enviar

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.data.modelo.EtapaDoPipeline
import io.github.gfvdataweb.bolaof1.ui.comum.horarioLocal
import io.github.gfvdataweb.bolaof1.ui.theme.LocalCoresDosPontos
import java.time.ZoneId

/**
 * "Última atualização": a rodada e o passo a passo do pipeline que o palpite
 * dispara, lidos do painel. Falha na consulta aparece como um texto discreto.
 */
@Composable
fun SecaoDoPipeline(estado: EstadoDoPipeline, modifier: Modifier = Modifier) {
    val site = estado.site
    if (site == null && !estado.falhou) return
    val navegador = LocalUriHandler.current
    Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        if (site != null) {
            Text(stringResource(R.string.pipeline_titulo), style = MaterialTheme.typography.titleMedium)
            site.rodada?.let {
                Text(
                    stringResource(R.string.pipeline_rodada, it),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            site.etapas.forEach { LinhaDaEtapa(it) }
            linkSeguro(site.execucao?.url)?.let { url ->
                TextButton(onClick = { navegador.openUri(url) }) { Text(stringResource(R.string.pipeline_ver_execucao)) }
            }
        }
        if (estado.falhou) {
            Text(
                stringResource(R.string.pipeline_falha),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun LinhaDaEtapa(etapa: EtapaDoPipeline) {
    val estado = estadoDaEtapa(etapa.estado)
    val cor = corDoTom(tomDaEtapa(estado))
    val rotulo = rotuloDaEtapa(estado) ?: etapa.estado
    val quando = horarioLocal(etapa.quando, ZoneId.systemDefault())
    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp), verticalAlignment = Alignment.Top) {
        Text(marcaDaEtapa(estado), color = cor, fontWeight = FontWeight.Bold, modifier = Modifier.width(24.dp))
        Column(Modifier.weight(1f)) {
            Text(etapa.titulo, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
            Text(
                if (quando != null) stringResource(R.string.etapa_quando, rotulo, quando) else rotulo,
                style = MaterialTheme.typography.bodySmall,
                color = cor,
            )
            if (etapa.detalhe.isNotBlank()) {
                Text(
                    etapa.detalhe,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Spacer(Modifier.width(4.dp))
    }
}

@Composable
private fun corDoTom(tom: TomDaEtapa): Color {
    val cores = LocalCoresDosPontos.current
    return when (tom) {
        TomDaEtapa.OK -> cores.dois
        TomDaEtapa.AVISO -> cores.um
        TomDaEtapa.ERRO -> MaterialTheme.colorScheme.error
        TomDaEtapa.NEUTRO -> cores.zeroTexto
    }
}

@Composable
private fun rotuloDaEtapa(estado: EstadoDaEtapa): String? = when (estado) {
    EstadoDaEtapa.OK -> stringResource(R.string.etapa_ok)
    EstadoDaEtapa.ANDAMENTO -> stringResource(R.string.etapa_andamento)
    EstadoDaEtapa.AGUARDANDO -> stringResource(R.string.etapa_aguardando)
    EstadoDaEtapa.ERRO -> stringResource(R.string.etapa_erro)
    EstadoDaEtapa.PENDENTE -> stringResource(R.string.etapa_pendente)
    EstadoDaEtapa.PULADO -> stringResource(R.string.etapa_pulado)
    EstadoDaEtapa.DESCONHECIDO -> null
}

/** ✓ … ⏳ ✕ – como no painel; etapa não iniciada (ou desconhecida) fica com o ponto. */
@Composable
private fun marcaDaEtapa(estado: EstadoDaEtapa): String = when (estado) {
    EstadoDaEtapa.OK -> stringResource(R.string.marca_ok)
    EstadoDaEtapa.ANDAMENTO -> stringResource(R.string.marca_andamento)
    EstadoDaEtapa.AGUARDANDO -> stringResource(R.string.marca_aguardando)
    EstadoDaEtapa.ERRO -> stringResource(R.string.marca_erro)
    EstadoDaEtapa.PULADO -> stringResource(R.string.marca_pulado)
    EstadoDaEtapa.PENDENTE, EstadoDaEtapa.DESCONHECIDO -> "·"
}
