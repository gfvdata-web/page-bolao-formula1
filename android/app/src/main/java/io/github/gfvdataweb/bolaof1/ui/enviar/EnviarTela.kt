package io.github.gfvdataweb.bolaof1.ui.enviar

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.data.ResultadoDoEnvio
import io.github.gfvdataweb.bolaof1.ui.theme.LocalCoresDosPontos

/** Aba Enviar: cola o palpite do WhatsApp e manda para o bolão (pede confirmação). */
@Composable
fun EnviarTela(
    estado: EstadoDoEnvio,
    aoMudarTexto: (String) -> Unit,
    aoMudarRodada: (String) -> Unit,
    aoEnviar: () -> Unit,
    aoAbrirConfiguracoes: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var confirmando by rememberSaveable { mutableStateOf(false) }

    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (!estado.configurado) {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(stringResource(R.string.envio_nao_configurado), color = MaterialTheme.colorScheme.onErrorContainer)
                    Button(onClick = aoAbrirConfiguracoes) { Text(stringResource(R.string.abrir_configuracoes)) }
                }
            }
        }
        OutlinedTextField(
            value = estado.texto,
            onValueChange = aoMudarTexto,
            label = { Text(stringResource(R.string.envio_texto)) },
            placeholder = { Text(stringResource(R.string.envio_texto_dica)) },
            minLines = 8,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = estado.rodada,
            onValueChange = aoMudarRodada,
            label = { Text(stringResource(R.string.envio_rodada)) },
            supportingText = {
                Text(
                    if (estado.rodadaValida) {
                        stringResource(R.string.envio_rodada_dica)
                    } else {
                        stringResource(R.string.envio_rodada_invalida, EstadoDoEnvio.RODADA_MAXIMA)
                    },
                )
            },
            isError = !estado.rodadaValida,
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = { confirmando = true }, enabled = estado.podeEnviar, modifier = Modifier.fillMaxWidth()) {
            if (estado.enviando) {
                CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
            } else {
                Text(stringResource(R.string.envio_botao))
            }
        }
        estado.resultado?.let { MensagemDoResultado(it) }
    }

    if (confirmando) {
        AlertDialog(
            onDismissRequest = { confirmando = false },
            title = { Text(stringResource(R.string.envio_confirmar_titulo)) },
            text = { Text(stringResource(R.string.envio_confirmar_texto)) },
            confirmButton = {
                TextButton(onClick = {
                    confirmando = false
                    aoEnviar()
                }) { Text(stringResource(R.string.envio_confirmar_sim)) }
            },
            dismissButton = {
                TextButton(onClick = { confirmando = false }) { Text(stringResource(R.string.cancelar)) }
            },
        )
    }
}

@Composable
private fun MensagemDoResultado(resultado: ResultadoDoEnvio) {
    val sucesso = resultado == ResultadoDoEnvio.Enviado
    val texto = when (resultado) {
        ResultadoDoEnvio.Enviado -> stringResource(R.string.envio_ok)
        is ResultadoDoEnvio.Recusado -> stringResource(R.string.envio_recusado, resultado.motivo)
        ResultadoDoEnvio.FalhaDeRede -> stringResource(R.string.envio_falha_rede)
        ResultadoDoEnvio.RespostaInesperada -> stringResource(R.string.envio_resposta_inesperada)
        ResultadoDoEnvio.NaoConfigurado -> stringResource(R.string.envio_nao_configurado)
    }
    val cores = LocalCoresDosPontos.current
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (sucesso) cores.doisFundo else MaterialTheme.colorScheme.errorContainer,
        ),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(
            texto,
            color = if (sucesso) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onErrorContainer,
            modifier = Modifier.padding(16.dp),
        )
    }
}
