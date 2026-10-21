package io.github.gfvdataweb.bolaof1.data

import io.github.gfvdataweb.bolaof1.apoio.SiteLocal
import io.github.gfvdataweb.bolaof1.apoio.StatusDoPainel
import kotlinx.coroutines.test.runTest
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.fail
import org.junit.Test
import java.io.IOException

/** Painel principal e reserva como dois "sites" locais (MockWebServer). */
class PipelineRepositorioTest {

    private val principal = SiteLocal()
    private val reserva = SiteLocal()

    private fun repositorio() = PipelineRepositorio(
        FonteRemota(OkHttpClient(), principal.urlDoPainel, reserva.urlDoPainel),
    )

    @After
    fun encerra() {
        principal.close()
        reserva.close()
    }

    @Test
    fun leDoPainelPrincipal() = runTest {
        principal.substituicoes["painel/dados/status.json"] = StatusDoPainel.texto
        assertEquals(17, repositorio().carregar().rodada)
    }

    @Test
    fun principalForaDoArLeDaReserva() = runTest {
        principal.foraDoAr = true
        reserva.substituicoes["painel/dados/status.json"] = StatusDoPainel.texto
        assertEquals(17, repositorio().carregar().rodada)
    }

    @Test
    fun ambosFalhandoSobeIOException() = runTest {
        principal.foraDoAr = true
        reserva.foraDoAr = true
        try {
            repositorio().carregar()
            fail("devia falhar")
        } catch (e: IOException) {
            // esperado
        }
    }

    @Test
    fun painelSemOArquivoSobeIOException() = runTest {
        // Nenhum dos dois serve o status.json (404): erro de rede, não um JSON vazio.
        try {
            repositorio().carregar()
            fail("devia falhar")
        } catch (e: IOException) {
            // esperado
        }
    }
}
