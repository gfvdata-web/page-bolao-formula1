package io.github.gfvdataweb.bolaof1.apoio

import io.github.gfvdataweb.bolaof1.AppContainer
import io.github.gfvdataweb.bolaof1.BolaoApp
import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.data.TemporadaRepositorio
import io.github.gfvdataweb.bolaof1.data.modelo.Temporadas
import kotlinx.serialization.decodeFromString
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import mockwebserver3.RecordedRequest
import okhttp3.HttpUrl
import java.io.Closeable
import java.io.File
import java.util.concurrent.ConcurrentHashMap

// Peças compartilhadas pelos testes. Nada aqui acessa a internet.

/** JSONs reais de docs/data (pasta passada pelo Gradle). */
object DadosDoSite {
    val pasta: File = File(
        checkNotNull(System.getProperty("bolao.dadosDoSite")) { "Rode pelo Gradle (propriedade bolao.dadosDoSite)" },
    )

    fun texto(caminho: String): String = File(pasta, caminho).readText()
}

/** A temporada atual montada direto dos arquivos reais (sem rede). */
object TemporadaReal {
    val temporada: Temporada by lazy {
        val ano = TemporadaRepositorio.json.decodeFromString<Temporadas>(DadosDoSite.texto(TemporadaRepositorio.SEASONS)).atual
        val caminhos = listOf(TemporadaRepositorio.SEASONS, TemporadaRepositorio.EQUIPES) +
            TemporadaRepositorio.caminhosDoAno(ano)
        TemporadaRepositorio.montar(caminhos.associateWith { DadosDoSite.texto(it) })
    }
}

/**
 * "Site" local (MockWebServer) que serve os JSONs reais em `/data/`. Os testes
 * podem trocar o conteúdo de um caminho ([substituicoes]) ou derrubar o site.
 */
class SiteLocal : Closeable {
    val substituicoes = ConcurrentHashMap<String, String>()

    @Volatile
    var foraDoAr = false

    private val servidor = MockWebServer().apply {
        dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                if (foraDoAr) return MockResponse(code = 503)
                val caminho = request.url.encodedPath.removePrefix("/data/")
                substituicoes[caminho]?.let { return MockResponse(body = it) }
                val arquivo = File(DadosDoSite.pasta, caminho)
                return if (arquivo.isFile) MockResponse(body = arquivo.readText()) else MockResponse(code = 404)
            }
        }
        start()
    }

    val urlDosDados: HttpUrl get() = servidor.url("/data/")

    /** Sem Releases publicados no site local (responde 404): o app não mostra aviso. */
    val urlDosReleases: HttpUrl get() = servidor.url("/releases")

    override fun close() = servidor.close()
}

/** Um site local para a JVM de testes inteira (o app de teste aponta para ele). */
object SiteDeTeste {
    val site: SiteLocal by lazy { SiteLocal() }
}

/** App usado nos testes Robolectric do app inteiro: lê do site local. */
class BolaoAppDeTeste : BolaoApp() {
    override fun criarContainer(): AppContainer =
        AppContainer(this, SiteDeTeste.site.urlDosDados, SiteDeTeste.site.urlDosReleases)
}
