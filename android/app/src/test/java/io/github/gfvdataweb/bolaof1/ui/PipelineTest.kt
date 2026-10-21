package io.github.gfvdataweb.bolaof1.ui

import io.github.gfvdataweb.bolaof1.apoio.StatusDoPainel
import io.github.gfvdataweb.bolaof1.data.PipelineRepositorio
import io.github.gfvdataweb.bolaof1.data.modelo.EtapaDoPipeline
import io.github.gfvdataweb.bolaof1.data.modelo.ExecucaoDoPipeline
import io.github.gfvdataweb.bolaof1.data.modelo.SitePipeline
import io.github.gfvdataweb.bolaof1.ui.comum.horarioLocal
import io.github.gfvdataweb.bolaof1.ui.enviar.EstadoDaEtapa
import io.github.gfvdataweb.bolaof1.ui.enviar.TomDaEtapa
import io.github.gfvdataweb.bolaof1.ui.enviar.deveContinuarAcompanhando
import io.github.gfvdataweb.bolaof1.ui.enviar.estadoDaEtapa
import io.github.gfvdataweb.bolaof1.ui.enviar.linkSeguro
import io.github.gfvdataweb.bolaof1.ui.enviar.tomDaEtapa
import kotlinx.serialization.SerializationException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.ZoneId

/** Leitura do recorte do status.json e regras de exibição/acompanhamento do pipeline. */
class PipelineTest {

    private fun etapa(estado: String) = EtapaDoPipeline(chave = "x", titulo = "X", estado = estado)

    private fun site(vararg estados: String, emVigilia: Boolean = false, status: String? = null) = SitePipeline(
        slug = "bolao_f1",
        emVigilia = emVigilia,
        execucao = status?.let { ExecucaoDoPipeline(status = it) },
        etapas = estados.map { etapa(it) },
    )

    @Test
    fun leOCardDoBolaoNaFixtureReal() {
        val site = PipelineRepositorio.extrairDoBolao(StatusDoPainel.texto)

        assertEquals("bolao_f1", site.slug)
        assertEquals(17, site.rodada)
        assertFalse(site.emVigilia)
        assertEquals("completed", site.execucao?.status)
        assertEquals("success", site.execucao?.conclusao)
        assertEquals("https://github.com/gfvdata-web/page-bolao-formula1/actions/runs/38165341232", site.execucao?.url)
        assertEquals(listOf("forms", "leitura", "resultado", "pontuacao", "pagina"), site.etapas.map { it.chave })
        assertEquals(
            listOf(EstadoDaEtapa.PULADO, EstadoDaEtapa.OK, EstadoDaEtapa.OK, EstadoDaEtapa.OK, EstadoDaEtapa.OK),
            site.etapas.map { estadoDaEtapa(it.estado) },
        )
        assertEquals("Palpites lidos e rodada identificada", site.etapas[1].titulo)
        assertEquals("", site.etapas[3].detalhe)
    }

    @Test
    fun semOCardDoBolaoOuComJsonRuimDaErroDeFormato() {
        assertThrows(SerializationException::class.java) {
            PipelineRepositorio.extrairDoBolao("""{"sites": [{"slug": "outro"}]}""")
        }
        assertThrows(SerializationException::class.java) { PipelineRepositorio.extrairDoBolao("{ isto não é json") }
        assertThrows(SerializationException::class.java) { PipelineRepositorio.extrairDoBolao("[1, 2]") }
    }

    @Test
    fun campoNovoOuAusenteNaoQuebra() {
        val site = PipelineRepositorio.extrairDoBolao("""{"sites": [{"slug": "bolao_f1", "campo_novo": [1]}]}""")
        assertNull(site.rodada)
        assertTrue(site.etapas.isEmpty())
        assertNull(site.execucao)
    }

    @Test
    fun estadosDesconhecidosViramNeutros() {
        assertEquals(EstadoDaEtapa.DESCONHECIDO, estadoDaEtapa("outra-coisa"))
        assertEquals(TomDaEtapa.NEUTRO, tomDaEtapa(EstadoDaEtapa.DESCONHECIDO))
        assertEquals(TomDaEtapa.OK, tomDaEtapa(EstadoDaEtapa.OK))
        assertEquals(TomDaEtapa.AVISO, tomDaEtapa(EstadoDaEtapa.ANDAMENTO))
        assertEquals(TomDaEtapa.AVISO, tomDaEtapa(EstadoDaEtapa.AGUARDANDO))
        assertEquals(TomDaEtapa.ERRO, tomDaEtapa(EstadoDaEtapa.ERRO))
    }

    @Test
    fun acompanhaEnquantoHouverEtapaEmCursoOuVigilia() {
        assertFalse(deveContinuarAcompanhando(null))
        assertFalse(deveContinuarAcompanhando(PipelineRepositorio.extrairDoBolao(StatusDoPainel.texto)))
        assertTrue(deveContinuarAcompanhando(site("ok", "andamento", "pendente")))
        assertTrue(deveContinuarAcompanhando(site("ok", "aguardando")))
        assertTrue(deveContinuarAcompanhando(site("ok", "pendente")))
        assertTrue(deveContinuarAcompanhando(site("ok", "ok", emVigilia = true)))
        assertTrue(deveContinuarAcompanhando(site("ok", "ok", status = "in_progress")))
        assertFalse(deveContinuarAcompanhando(site("ok", "pulado", status = "completed")))
    }

    @Test
    fun depoisDeUmErroAsPendentesNaoSeguram() {
        assertFalse(deveContinuarAcompanhando(site("ok", "erro", "pendente")))
        // Mas um erro com outra etapa ainda em curso continua sendo acompanhado.
        assertTrue(deveContinuarAcompanhando(site("erro", "andamento")))
    }

    @Test
    fun soLinksWebAbremNoNavegador() {
        assertEquals("https://github.com/x", linkSeguro("https://github.com/x"))
        assertNull(linkSeguro("javascript:alert(1)"))
        assertNull(linkSeguro(null))
    }

    @Test
    fun horarioNoFusoLocal() {
        assertEquals("11/10 15:48", horarioLocal("2026-10-11T18:48:26Z", ZoneId.of("America/Sao_Paulo")))
        assertNull(horarioLocal("ontem", ZoneId.of("UTC")))
        assertNull(horarioLocal(null, ZoneId.of("UTC")))
    }
}
