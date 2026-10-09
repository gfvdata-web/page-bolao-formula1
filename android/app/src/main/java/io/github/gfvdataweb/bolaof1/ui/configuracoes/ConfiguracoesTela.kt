package io.github.gfvdataweb.bolaof1.ui.configuracoes

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R

/**
 * Configurações: endereço e chave do envio de palpites, e a versão instalada.
 * [extras] recebe blocos de outras partes do app (ex.: aviso de nova versão).
 */
@Composable
fun ConfiguracoesTela(
    estado: EstadoDasConfiguracoes,
    aoMudarUrl: (String) -> Unit,
    aoMudarChave: (String) -> Unit,
    aoSalvar: () -> Unit,
    versao: String,
    build: Int,
    modifier: Modifier = Modifier,
    extras: @Composable () -> Unit = {},
) {
    var mostrarChave by rememberSaveable { mutableStateOf(false) }

    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(stringResource(R.string.config_envio_titulo), style = MaterialTheme.typography.titleMedium)
        Text(
            stringResource(R.string.config_envio_explicacao),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        OutlinedTextField(
            value = estado.url,
            onValueChange = aoMudarUrl,
            label = { Text(stringResource(R.string.config_url)) },
            isError = !estado.urlValida,
            supportingText = if (estado.urlValida) null else { { Text(stringResource(R.string.config_url_invalida)) } },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = estado.chave,
            onValueChange = aoMudarChave,
            label = { Text(stringResource(R.string.config_chave)) },
            singleLine = true,
            visualTransformation = if (mostrarChave) VisualTransformation.None else PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            trailingIcon = {
                TextButton(onClick = { mostrarChave = !mostrarChave }) {
                    Text(stringResource(if (mostrarChave) R.string.ocultar else R.string.mostrar))
                }
            },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = aoSalvar, enabled = estado.podeSalvar) { Text(stringResource(R.string.salvar)) }
        if (estado.salvo) {
            Text(stringResource(R.string.config_salvo), color = MaterialTheme.colorScheme.primary)
        }

        HorizontalDivider(color = MaterialTheme.colorScheme.outline)
        Text(stringResource(R.string.config_sobre), style = MaterialTheme.typography.titleMedium)
        Text(stringResource(R.string.config_versao, versao, build), style = MaterialTheme.typography.bodyMedium)
        extras()
    }
}
