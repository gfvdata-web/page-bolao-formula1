package io.github.gfvdataweb.bolaof1.data

import io.github.gfvdataweb.bolaof1.apoio.SiteLocal
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
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

/** Stale-while-revalidate do histórico (Hall of Fame) com um site local servindo os JSONs reais. */
class HistoricoRepositorioTest {

    @get:Rule
    val pasta = TemporaryFolder()

    private val site = SiteLocal()
    private var agora = 1_000_000L

    private lateinit var repositorio: HistoricoRepositorio

    @Before
    fun prepara() {
        repositorio = HistoricoRepositorio(
            fonte = FonteRemota(OkHttpClient(), site.urlDosDados),
            cache = CacheDeArquivos(File(pasta.root, "cache")),
            relogio = { agora },
        )
    }

    @After
    fun encerra() {
        site.close()
    }

    @Test
    fun semCache_entregaCarregandoEDepoisTodosOsAnos() = runTest {
        val estados = repositorio.observar().toList()

        assertEquals(2, estados.size)
        assertNull(estados[0].dados)
        assertTrue(estados[0].atualizando)
        val final = estados[1]
        assertFalse(final.atualizando)
        assertNull(final.erro)
        assertEquals(agora, final.atualizadoEm)
        val historico = checkNotNull(final.dados)
        assertTrue(historico.classificacoes.keys.containsAll((2021..2026).toList()))
        assertTrue(historico.hall.anos.isNotEmpty())
        assertTrue(historico.atual in historico.classificacoes.keys)
    }

    @Test
    fun semInternet_mostraOCacheComAvisoDeFalha() = runTest {
        repositorio.observar().toList()
        site.foraDoAr = true
        agora = 9_000_000L

        val estados = repositorio.observar().toList()

        assertNotNull(estados[0].dados)
        assertEquals(1_000_000L, estados[0].atualizadoEm)
        assertEquals(ErroDeDados.FALHA_NO_DOWNLOAD, estados[1].erro)
        assertNotNull(estados[1].dados)
    }

    @Test
    fun hallQuebradoNoSite_naoEstragaOCache() = runTest {
        val primeiro = checkNotNull(repositorio.observar().toList().last().dados)
        site.substituicoes["hall_of_fame.json"] = "{ isto não é json"

        val comErro = repositorio.observar().toList().last()
        assertEquals(ErroDeDados.FORMATO_INESPERADO, comErro.erro)

        site.foraDoAr = true
        assertEquals(primeiro, repositorio.observar().toList().first().dados)
    }
}
