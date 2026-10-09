package io.github.gfvdataweb.bolaof1

import android.app.Application
import android.content.Context
import io.github.gfvdataweb.bolaof1.data.CacheDeArquivos
import io.github.gfvdataweb.bolaof1.data.FonteRemota
import io.github.gfvdataweb.bolaof1.data.TemporadaRepositorio
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import java.io.File
import java.util.concurrent.TimeUnit

/** Endereços externos que o app conhece. O PAT do GitHub nunca entra aqui. */
object Enderecos {
    /** JSONs publicados pelo site (GitHub Pages), mesma pasta que o site lê. */
    const val DADOS_DO_SITE = "https://gfvdata-web.github.io/page-bolao-formula1/data/"
}

/**
 * Contêiner de dependências manual (sem Hilt na v1): cria cada peça uma vez e
 * entrega para as telas. Nos testes, as peças são montadas à mão com dublês.
 */
class AppContainer(contexto: Context) {
    val clienteHttp: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    val temporadaRepositorio = TemporadaRepositorio(
        fonte = FonteRemota(clienteHttp, Enderecos.DADOS_DO_SITE.toHttpUrl()),
        cache = CacheDeArquivos(File(contexto.filesDir, "dados-do-site")),
    )
}

class BolaoApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
