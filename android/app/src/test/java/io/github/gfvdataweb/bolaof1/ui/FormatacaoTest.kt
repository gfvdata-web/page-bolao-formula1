package io.github.gfvdataweb.bolaof1.ui

import io.github.gfvdataweb.bolaof1.data.modelo.Calendario
import io.github.gfvdataweb.bolaof1.data.modelo.CorridaDoCalendario
import io.github.gfvdataweb.bolaof1.ui.comum.Idade
import io.github.gfvdataweb.bolaof1.ui.comum.argbDeHex
import io.github.gfvdataweb.bolaof1.ui.comum.dataCurta
import io.github.gfvdataweb.bolaof1.ui.comum.idadeDosDados
import io.github.gfvdataweb.bolaof1.ui.comum.proximoQuali
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.Instant
import java.time.ZoneId
import java.time.ZoneOffset

class FormatacaoTest {

    private val utc: ZoneId = ZoneOffset.UTC
    private val minuto = 60_000L

    @Test
    fun dataCurtaNoFormatoDiaMes() {
        assertEquals("13/09", dataCurta("2026-09-13"))
        assertEquals("sem data", dataCurta("sem data"))
    }

    @Test
    fun idadeDosDadosPorFaixa() {
        val agora = 1_800_000_000_000L
        assertEquals(Idade.AgoraMesmo, idadeDosDados(agora, agora - 30_000, utc))
        assertEquals(Idade.Minutos(5), idadeDosDados(agora, agora - 5 * minuto, utc))
        assertEquals(Idade.Horas(3), idadeDosDados(agora, agora - 3 * 60 * minuto, utc))
        val doisDias = agora - 2 * 24 * 60 * minuto
        val esperado = Instant.ofEpochMilli(doisDias).atZone(utc)
        assertEquals(
            Idade.EmData("%02d/%02d %02d:%02d".format(esperado.dayOfMonth, esperado.monthValue, esperado.hour, esperado.minute)),
            idadeDosDados(agora, doisDias, utc),
        )
    }

    @Test
    fun relogioAdiantadoNaoDaIdadeNegativa() {
        assertEquals(Idade.AgoraMesmo, idadeDosDados(1_000_000, 5_000_000, utc))
    }

    @Test
    fun proximoQualiEOPrimeiroDepoisDeAgora() {
        val calendario = Calendario(
            temporada = 2026,
            corridas = listOf(
                CorridaDoCalendario(1, "Melbourne", qualiUtc = "2026-03-07T05:00:00Z"),
                CorridaDoCalendario(2, "Sem horário", qualiUtc = null),
                CorridaDoCalendario(3, "Suzuka", qualiUtc = "2026-03-28T06:00:00Z"),
                CorridaDoCalendario(4, "Miami", qualiUtc = "2026-05-02T20:00:00Z"),
            ),
        )
        val proximo = proximoQuali(calendario, Instant.parse("2026-03-10T00:00:00Z"), utc)
        assertEquals(3, proximo?.numero)
        assertEquals("Suzuka", proximo?.corrida)
        assertNull(proximoQuali(calendario, Instant.parse("2026-12-31T00:00:00Z"), utc))
    }

    @Test
    fun corDeHex() {
        assertEquals(0xFFE8002DL, argbDeHex("#E8002D"))
        assertEquals(0xFF00A19CL, argbDeHex("00A19C"))
        assertNull(argbDeHex("vermelho"))
        assertNull(argbDeHex(null))
    }
}
