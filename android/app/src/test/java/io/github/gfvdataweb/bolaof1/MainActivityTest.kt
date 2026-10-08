package io.github.gfvdataweb.bolaof1

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

/**
 * Abre o app de verdade (manifest, tema e Activity) num Android simulado no
 * JVM: se o app fecharia sozinho ao abrir no celular, este teste falha no CI.
 */
@RunWith(RobolectricTestRunner::class)
class MainActivityTest {

    @get:Rule
    val compose = createAndroidComposeRule<MainActivity>()

    @Test
    fun abreNaTelaInicialComAVersaoDoBuild() {
        compose.onNodeWithText("Bolão F1").assertIsDisplayed()
        compose
            .onNodeWithText("Versão ${BuildConfig.VERSION_NAME} · build ${BuildConfig.VERSION_CODE}")
            .assertIsDisplayed()
    }
}
