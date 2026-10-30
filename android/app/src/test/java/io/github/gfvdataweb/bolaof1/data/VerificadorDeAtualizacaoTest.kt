package io.github.gfvdataweb.bolaof1.data

import kotlinx.coroutines.test.runTest
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Aviso de nova versão contra um `app/versao.json` local (o do Worker do app, 9f). */
class VerificadorDeAtualizacaoTest {

    private val worker = MockWebServer().apply { start() }
    private val urlDaVersao = worker.url("/app/versao.json")
    private val verificador = VerificadorDeAtualizacao(OkHttpClient(), urlDaVersao)

    @After
    fun encerra() {
        worker.close()
    }

    private fun versao(apk: String) = """
        {"versao": "0.2.0", "build": 20, "apk": "$apk", "notas": "Notas da versão.",
         "publicado_em": "2026-10-30T12:00:00Z", "campo_novo": 1}
    """.trimIndent()

    @Test
    fun leVersaoEBuildDoNomeDoApkEMontaOEnderecoAoLadoDoVersaoJson() = runTest {
        worker.enqueue(MockResponse(body = versao("bolao-f1-v0.2.0-build20.apk")))

        val publicada = verificador.maisRecente()

        assertEquals("0.2.0", publicada?.versao)
        assertEquals(20, publicada?.build)
        assertEquals(worker.url("/app/bolao-f1-v0.2.0-build20.apk").toString(), publicada?.urlDoApk)
        assertEquals("Notas da versão.", publicada?.notas)
        assertEquals("/app/versao.json", worker.takeRequest().url.encodedPath)
    }

    @Test
    fun apkForaDoPadraoOuLinkDeForaNaoViramAviso() = runTest {
        worker.enqueue(MockResponse(body = versao("nome-fora-do-padrao.apk")))
        assertNull(verificador.maisRecente())
        worker.enqueue(MockResponse(body = versao("https://outro.site/bolao-f1-v9.9.9-build99.apk")))
        assertNull(verificador.maisRecente())
    }

    @Test
    fun falhaNaConsultaNaoAtrapalha() = runTest {
        worker.enqueue(MockResponse(code = 404))
        assertNull(verificador.maisRecente())
        worker.enqueue(MockResponse(body = "isto não é json"))
        assertNull(verificador.maisRecente())
        worker.close()
        assertNull(verificador.maisRecente())
    }

    @Test
    fun soAvisaQuandoOBuildPublicadoEMaior() {
        val publicada = VersaoPublicada("0.2.0", build = 20, urlDoApk = "", notas = "")
        assertTrue(haAtualizacao(publicada, buildInstalado = 12))
        assertFalse(haAtualizacao(publicada, buildInstalado = 20))
        assertFalse(haAtualizacao(publicada, buildInstalado = 31))
        assertFalse(haAtualizacao(null, buildInstalado = 1))
    }
}
