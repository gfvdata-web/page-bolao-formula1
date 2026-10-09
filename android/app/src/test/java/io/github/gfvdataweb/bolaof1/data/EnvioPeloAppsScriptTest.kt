package io.github.gfvdataweb.bolaof1.data

import kotlinx.coroutines.test.runTest
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import okhttp3.Headers.Companion.headersOf
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Envio do palpite contra um "Apps Script" local (MockWebServer). */
class EnvioPeloAppsScriptTest {

    private val appsScript = MockWebServer().apply { start() }
    private val envio = EnvioPeloAppsScript(OkHttpClient())
    private val configuracoes = ConfiguracoesDeEnvio(url = appsScript.url("/macros/s/abc/exec").toString(), chave = "chave-certa")

    @After
    fun encerra() {
        appsScript.close()
    }

    @Test
    fun aceitoMandaChaveTextoERodadaEmJson() = runTest {
        appsScript.enqueue(MockResponse(body = """{"ok":true}"""))

        val resultado = envio.enviar(configuracoes, "Qualify Bolao\nVER\nNOR", rodada = 17)

        assertEquals(ResultadoDoEnvio.Enviado, resultado)
        val pedido = appsScript.takeRequest()
        assertEquals("POST", pedido.method)
        assertTrue(pedido.headers["Content-Type"].orEmpty().startsWith("application/json"))
        assertEquals(
            """{"chave":"chave-certa","texto":"Qualify Bolao\nVER\nNOR","round":17}""",
            pedido.body?.utf8(),
        )
    }

    @Test
    fun semRodadaNaoMandaOCampoRound() = runTest {
        appsScript.enqueue(MockResponse(body = """{"ok":true}"""))
        envio.enviar(configuracoes, "palpite", rodada = null)
        assertFalse(appsScript.takeRequest().body?.utf8().orEmpty().contains("round"))
    }

    /** O Google responde ao POST com 302; a resposta JSON vem no GET do redirect. */
    @Test
    fun segueORedirectDoGoogleParaLerAResposta() = runTest {
        val destino = appsScript.url("/macros/echo?user_content_key=xyz")
        appsScript.enqueue(MockResponse(code = 302, headers = headersOf("Location", destino.toString())))
        appsScript.enqueue(MockResponse(body = """{"ok":true}"""))

        assertEquals(ResultadoDoEnvio.Enviado, envio.enviar(configuracoes, "palpite", rodada = null))
        assertEquals("POST", appsScript.takeRequest().method)
        assertEquals("GET", appsScript.takeRequest().method)
    }

    @Test
    fun recusadoTrazOMotivoDoScript() = runTest {
        appsScript.enqueue(MockResponse(body = """{"ok":false,"erro":"Chave de envio inválida."}"""))
        assertEquals(
            ResultadoDoEnvio.Recusado("Chave de envio inválida."),
            envio.enviar(configuracoes, "palpite", rodada = null),
        )
    }

    @Test
    fun paginaDeLoginDoGoogleEhRespostaInesperada() = runTest {
        appsScript.enqueue(MockResponse(body = "<html><body>Fazer login</body></html>"))
        assertEquals(ResultadoDoEnvio.RespostaInesperada, envio.enviar(configuracoes, "palpite", rodada = null))
    }

    @Test
    fun semConexaoEhFalhaDeRede() = runTest {
        appsScript.close()
        assertEquals(ResultadoDoEnvio.FalhaDeRede, envio.enviar(configuracoes, "palpite", rodada = null))
    }

    @Test
    fun semChaveNemTentaEnviar() = runTest {
        assertEquals(
            ResultadoDoEnvio.NaoConfigurado,
            envio.enviar(configuracoes.copy(chave = " "), "palpite", rodada = null),
        )
        assertEquals(0, appsScript.requestCount)
    }
}
