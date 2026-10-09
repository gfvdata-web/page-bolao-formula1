package io.github.gfvdataweb.bolaof1.data

import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import mockwebserver3.RecordedRequest
import okhttp3.OkHttpClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

/**
 * Stale-while-revalidate com um "site" local (MockWebServer) servindo os
 * JSONs reais de docs/data. Sem internet de verdade.
 */
class TemporadaRepositorioTest {

    @get:Rule
    val pasta = TemporaryFolder()

    private val site = MockWebServer()

    /** Troca o conteúdo servido para um caminho (ex.: JSON quebrado). */
    private val substituicoes = mutableMapOf<String, String>()
    private var siteForaDoAr = false
    private var agora = 1_000_000L

    private lateinit var repositorio: TemporadaRepositorio

    @Before
    fun prepara() {
        site.dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                if (siteForaDoAr) return MockResponse(code = 503)
                val caminho = request.url.encodedPath.removePrefix("/data/")
                substituicoes[caminho]?.let { return MockResponse(body = it) }
                val arquivo = File(DadosDoSite.pasta, caminho)
                return if (arquivo.isFile) MockResponse(body = arquivo.readText()) else MockResponse(code = 404)
            }
        }
        site.start()
        repositorio = TemporadaRepositorio(
            fonte = FonteRemota(OkHttpClient(), site.url("/data/")),
            cache = CacheDeArquivos(File(pasta.root, "cache")),
            relogio = { agora },
        )
    }

    @After
    fun encerra() {
        site.close()
    }

    @Test
    fun semCache_entregaCarregandoEDepoisOsDados() = runTest {
        val estados = repositorio.observar().toList()

        assertEquals(2, estados.size)
        assertNull(estados[0].dados)
        assertTrue(estados[0].atualizando)

        val final = estados[1]
        assertFalse(final.atualizando)
        assertNull(final.erro)
        assertEquals(agora, final.atualizadoEm)
        val temporada = checkNotNull(final.dados)
        assertTrue(temporada.classificacao.jogadores.isNotEmpty())
        assertEquals(temporada.ano, temporada.classificacao.temporada)
        assertEquals(temporada.ano, temporada.info?.ano)
    }

    @Test
    fun semInternet_mostraOCacheComAvisoDeFalha() = runTest {
        repositorio.observar().toList() // primeiro uso, com internet
        siteForaDoAr = true
        agora = 9_000_000L

        val estados = repositorio.observar().toList()

        assertNotNull(estados[0].dados)
        assertTrue(estados[0].atualizando)
        assertEquals(1_000_000L, estados[0].atualizadoEm)
        val final = estados[1]
        assertEquals(ErroDeDados.FALHA_NO_DOWNLOAD, final.erro)
        assertEquals(1_000_000L, final.atualizadoEm)
        assertNotNull(final.dados)
    }

    @Test
    fun semInternetESemCache_avisaSemDados() = runTest {
        siteForaDoAr = true
        val final = repositorio.observar().toList().last()
        assertNull(final.dados)
        assertEquals(ErroDeDados.FALHA_NO_DOWNLOAD, final.erro)
    }

    @Test
    fun jsonQuebradoNoSite_naoEstragaOCache() = runTest {
        val primeiro = checkNotNull(repositorio.observar().toList().last().dados)
        substituicoes["${primeiro.ano}/standings.json"] = "{ isto não é json"
        agora = 9_000_000L

        val comErro = repositorio.observar().toList().last()
        assertEquals(ErroDeDados.FORMATO_INESPERADO, comErro.erro)
        assertEquals(1_000_000L, comErro.atualizadoEm)

        siteForaDoAr = true
        val doCache = repositorio.observar().toList().first()
        assertEquals(primeiro, doCache.dados)
    }

    @Test
    fun campoNovoNoJson_naoQuebraOApp() = runTest {
        val ano = checkNotNull(repositorio.observar().toList().last().dados).ano
        val original = File(DadosDoSite.pasta, "$ano/standings.json").readText()
        substituicoes["$ano/standings.json"] = original.replaceFirst("{", "{\"campo_que_ainda_nao_existe\": [1, 2],")

        val final = repositorio.observar().toList().last()
        assertNull(final.erro)
        assertTrue(checkNotNull(final.dados).classificacao.jogadores.isNotEmpty())
    }
}
