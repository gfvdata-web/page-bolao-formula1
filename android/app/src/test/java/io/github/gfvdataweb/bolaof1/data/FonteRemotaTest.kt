package io.github.gfvdataweb.bolaof1.data

import io.github.gfvdataweb.bolaof1.apoio.DadosDoSite
import io.github.gfvdataweb.bolaof1.apoio.SiteLocal
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test
import java.io.IOException

/** Principal + reserva com dois "sites" locais (MockWebServer). */
class FonteRemotaTest {

    private val principal = SiteLocal()
    private val reserva = SiteLocal()

    private fun fonte(comReserva: Boolean = true) =
        FonteRemota(OkHttpClient(), principal.urlDosDados, if (comReserva) reserva.urlDosDados else null)

    @After
    fun encerra() {
        principal.close()
        reserva.close()
    }

    @Test
    fun principalNoArLeDaPrincipal() {
        principal.substituicoes["seasons.json"] = "principal"
        reserva.substituicoes["seasons.json"] = "reserva"
        assertEquals("principal", fonte().baixarTexto("seasons.json"))
    }

    @Test
    fun principalForaDoArLeDaReserva() {
        principal.foraDoAr = true // responde 503
        assertEquals(DadosDoSite.texto("seasons.json"), fonte().baixarTexto("seasons.json"))
    }

    @Test
    fun principalComErroHttpLeDaReserva() {
        // 404 na principal (caminho que só a reserva tem) também cai na reserva.
        reserva.substituicoes["so-na-reserva.json"] = "{}"
        assertEquals("{}", fonte().baixarTexto("so-na-reserva.json"))
    }

    @Test
    fun ambasFalhandoRelancaOErro() {
        principal.foraDoAr = true
        reserva.foraDoAr = true
        assertThrows(IOException::class.java) { fonte().baixarTexto("seasons.json") }
    }

    @Test
    fun semReservaOErroDaPrincipalSobe() {
        principal.foraDoAr = true
        assertThrows(IOException::class.java) { fonte(comReserva = false).baixarTexto("seasons.json") }
    }
}
