package io.github.gfvdataweb.bolaof1.data

import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

class ConfiguracoesTest {

    @get:Rule
    val pasta = TemporaryFolder()

    private val escopo = CoroutineScope(Dispatchers.IO + SupervisorJob())

    @After
    fun encerra() {
        escopo.cancel()
    }

    @Test
    fun soAceitaUrlHttps() {
        assertTrue(ConfiguracoesDeEnvio(url = "https://script.google.com/macros/s/abc/exec").urlValida)
        assertTrue(ConfiguracoesDeEnvio(url = "  https://script.google.com/x  ").urlValida)
        assertFalse(ConfiguracoesDeEnvio(url = "http://script.google.com/x").urlValida)
        assertFalse(ConfiguracoesDeEnvio(url = "script google").urlValida)
    }

    @Test
    fun completasPrecisaDeUrlEChave() {
        val url = "https://script.google.com/macros/s/abc/exec"
        assertTrue(ConfiguracoesDeEnvio(url, "chave").completas)
        assertFalse(ConfiguracoesDeEnvio(url, "  ").completas)
        assertFalse(ConfiguracoesDeEnvio("", "chave").completas)
    }

    @Test
    fun guardaNoAparelhoSemEspacosSobrando() = runBlocking {
        val configuracoes = ConfiguracoesNoAparelho(
            PreferenceDataStoreFactory.create(scope = escopo) { File(pasta.root, "teste.preferences_pb") },
        )
        assertEquals(ConfiguracoesDeEnvio(), configuracoes.atuais.first())

        configuracoes.salvar(ConfiguracoesDeEnvio(url = " https://script.google.com/x ", chave = " segredo "))

        assertEquals(ConfiguracoesDeEnvio("https://script.google.com/x", "segredo"), configuracoes.atuais.first())
    }
}
