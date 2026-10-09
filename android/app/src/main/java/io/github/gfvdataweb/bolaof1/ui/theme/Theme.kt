package io.github.gfvdataweb.bolaof1.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
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
    surface = Color(0xFFF5F6F8),
    onSurface = Color(0xFF1A1D21),
    surfaceContainer = Color(0xFFFFFFFF),
    surfaceContainerLow = Color(0xFFFFFFFF),
    onSurfaceVariant = Color(0xFF5B6068),
    outline = Color(0xFFE1E4E8),
)

private val CoresEscuras = darkColorScheme(
    primary = AcentoEscuro,
    onPrimary = Color(0xFF14161A),
    background = Color(0xFF14161A),
    onBackground = Color(0xFFECEEF1),
    surface = Color(0xFF14161A),
    onSurface = Color(0xFFECEEF1),
    surfaceContainer = Color(0xFF1F2227),
    surfaceContainerLow = Color(0xFF1F2227),
    onSurfaceVariant = Color(0xFF9AA0A8),
    outline = Color(0xFF2C3036),
)

/**
 * Cores dos pontos 2/1/0, as mesmas do site (`--ok2`/`--ok1`/`--ok0-*`):
 * paleta única, sem vermelho para 0 pt.
 */
@Immutable
data class CoresDosPontos(
    val dois: Color,
    val doisFundo: Color,
    val um: Color,
    val umFundo: Color,
    val zeroFundo: Color,
    val zeroTexto: Color,
)

private val PontosClaros = CoresDosPontos(
    dois = Color(0xFF1E9E5A),
    doisFundo = Color(0xFFD9F4E6),
    um = Color(0xFFC99A00),
    umFundo = Color(0xFFFBF0C8),
    zeroFundo = Color(0xFFECEEF1),
    zeroTexto = Color(0xFF6B7078),
)

private val PontosEscuros = CoresDosPontos(
    dois = Color(0xFF3FD17F),
    doisFundo = Color(0xFF17352A),
    um = Color(0xFFE6BF3C),
    umFundo = Color(0xFF3A331A),
    zeroFundo = Color(0xFF2A2D32),
    zeroTexto = Color(0xFF8B9098),
)

val LocalCoresDosPontos = staticCompositionLocalOf { PontosClaros }

/** Tema do app: claro/escuro seguindo o sistema. */
@Composable
fun BolaoF1Theme(
    escuro: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    CompositionLocalProvider(LocalCoresDosPontos provides if (escuro) PontosEscuros else PontosClaros) {
        MaterialTheme(
            colorScheme = if (escuro) CoresEscuras else CoresClaras,
            content = content,
        )
    }
}
