package io.github.gfvdataweb.bolaof1.ui

import io.github.gfvdataweb.bolaof1.data.Configuracoes
import io.github.gfvdataweb.bolaof1.data.ConfiguracoesDeEnvio
import io.github.gfvdataweb.bolaof1.data.EnviaPalpite
import io.github.gfvdataweb.bolaof1.data.ResultadoDoEnvio
import io.github.gfvdataweb.bolaof1.ui.enviar.EnviarViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class EnviarViewModelTest {

    private class ConfiguracoesEmMemoria(inicial: ConfiguracoesDeEnvio) : Configuracoes {
        override val atuais = MutableStateFlow(inicial)
        override suspend fun salvar(novas: ConfiguracoesDeEnvio) {
            atuais.value = novas
        }
    }

    private data class Envio(val texto: String, val rodada: Int?)

    private val enviados = mutableListOf<Envio>()
    private var resposta: ResultadoDoEnvio = ResultadoDoEnvio.Enviado
    private val envioFalso = EnviaPalpite { _, texto, rodada ->
        enviados += Envio(texto, rodada)
        resposta
    }
    private val completas = ConfiguracoesDeEnvio("https://script.google.com/macros/s/abc/exec", "chave")

    @Before
    fun prepara() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun encerra() {
        Dispatchers.resetMain()
    }

    @Test
    fun semConfiguracaoNaoEnvia() {
        val vm = EnviarViewModel(envioFalso, ConfiguracoesEmMemoria(ConfiguracoesDeEnvio()))
        vm.mudarTexto("palpite")
        assertFalse(vm.estado.value.podeEnviar)
        vm.enviar()
        assertTrue(enviados.isEmpty())
    }

    @Test
    fun enviadoLimpaOFormulario() {
        val vm = EnviarViewModel(envioFalso, ConfiguracoesEmMemoria(completas))
        vm.mudarTexto("palpite do WhatsApp")
        vm.mudarRodada("17")
        vm.enviar()

        assertEquals(listOf(Envio("palpite do WhatsApp", 17)), enviados)
        assertEquals(ResultadoDoEnvio.Enviado, vm.estado.value.resultado)
        assertEquals("", vm.estado.value.texto)
        assertFalse(vm.estado.value.enviando)
    }

    @Test
    fun recusadoMantemOTextoParaCorrigir() {
        resposta = ResultadoDoEnvio.Recusado("Chave de envio inválida.")
        val vm = EnviarViewModel(envioFalso, ConfiguracoesEmMemoria(completas))
        vm.mudarTexto("palpite")
        vm.enviar()
        assertEquals("palpite", vm.estado.value.texto)
        assertEquals(resposta, vm.estado.value.resultado)
    }

    @Test
    fun rodadaAceitaSoNumerosDe1a30() {
        val vm = EnviarViewModel(envioFalso, ConfiguracoesEmMemoria(completas))
        vm.mudarTexto("palpite")
        vm.mudarRodada("1a7")
        assertEquals("17", vm.estado.value.rodada)
        vm.mudarRodada("45")
        assertFalse(vm.estado.value.rodadaValida)
        assertFalse(vm.estado.value.podeEnviar)
        vm.mudarRodada("")
        assertTrue(vm.estado.value.podeEnviar)
    }

    @Test
    fun configurarDepoisLiberaOEnvio() {
        val configuracoes = ConfiguracoesEmMemoria(ConfiguracoesDeEnvio())
        val vm = EnviarViewModel(envioFalso, configuracoes)
        vm.mudarTexto("palpite")
        assertFalse(vm.estado.value.configurado)
        configuracoes.atuais.value = completas
        assertTrue(vm.estado.value.podeEnviar)
    }
}
