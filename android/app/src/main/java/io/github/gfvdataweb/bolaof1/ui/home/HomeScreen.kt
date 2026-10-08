package io.github.gfvdataweb.bolaof1.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import io.github.gfvdataweb.bolaof1.R
import io.github.gfvdataweb.bolaof1.ui.theme.BolaoF1Theme

/**
 * Tela inicial provisória (sub-etapa 9a): nome do app e a versão instalada,
 * para conferir no celular qual build está rodando. Na 9d dá lugar às abas.
 */
@Composable
fun HomeScreen(
    versao: String,
    build: Int,
    modifier: Modifier = Modifier,
) {
    Scaffold(modifier = modifier.fillMaxSize()) { espaco ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(espaco)
                .padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = stringResource(R.string.home_titulo),
                style = MaterialTheme.typography.displaySmall,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = stringResource(R.string.home_subtitulo),
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center,
            )
            Spacer(Modifier.height(32.dp))
            Text(
                text = stringResource(R.string.home_versao, versao, build),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Preview(name = "Claro", showBackground = true)
@Composable
private fun HomeScreenClaroPreview() {
    BolaoF1Theme(escuro = false) { HomeScreen(versao = "0.0.0-dev", build = 1) }
}

@Preview(name = "Escuro", showBackground = true)
@Composable
private fun HomeScreenEscuroPreview() {
    BolaoF1Theme(escuro = true) { HomeScreen(versao = "0.0.0-dev", build = 1) }
}
