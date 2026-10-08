package io.github.gfvdataweb.bolaof1.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Paleta alinhada aos tokens do site (docs/style.css). Sem "dynamic color" do
// Android 12+: o app mantém a identidade do Bolão em qualquer celular.
private val Acento = Color(0xFFE10600)
private val AcentoEscuro = Color(0xFFFF5A4F)

private val CoresClaras = lightColorScheme(
    primary = Acento,
    onPrimary = Color.White,
    background = Color(0xFFF5F6F8),
    onBackground = Color(0xFF1A1D21),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF1A1D21),
    onSurfaceVariant = Color(0xFF5B6068),
    outline = Color(0xFFE1E4E8),
)

private val CoresEscuras = darkColorScheme(
    primary = AcentoEscuro,
    onPrimary = Color(0xFF14161A),
    background = Color(0xFF14161A),
    onBackground = Color(0xFFECEEF1),
    surface = Color(0xFF1F2227),
    onSurface = Color(0xFFECEEF1),
    onSurfaceVariant = Color(0xFF9AA0A8),
    outline = Color(0xFF2C3036),
)

/** Tema do app: claro/escuro seguindo o sistema. */
@Composable
fun BolaoF1Theme(
    escuro: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (escuro) CoresEscuras else CoresClaras,
        content = content,
    )
}
