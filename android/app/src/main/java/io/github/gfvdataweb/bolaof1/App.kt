package io.github.gfvdataweb.bolaof1

import android.app.Application
import android.content.Context
import androidx.datastore.preferences.core.PreferenceDataStoreFactory
import androidx.datastore.preferences.preferencesDataStoreFile
import io.github.gfvdataweb.bolaof1.data.CacheDeArquivos
import io.github.gfvdataweb.bolaof1.data.Configuracoes
import io.github.gfvdataweb.bolaof1.data.ConfiguracoesNoAparelho
import io.github.gfvdataweb.bolaof1.data.EnviaPalpite
import io.github.gfvdataweb.bolaof1.data.EnvioPeloAppsScript
import io.github.gfvdataweb.bolaof1.data.FonteRemota
import io.github.gfvdataweb.bolaof1.data.TemporadaRepositorio
import io.github.gfvdataweb.bolaof1.data.VerificadorDeAtualizacao
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import java.io.File
import java.util.concurrent.TimeUnit

/** Endereços externos que o app conhece. O PAT do GitHub nunca entra aqui. */
object Enderecos {
    /** JSONs publicados pelo site (GitHub Pages), mesma pasta que o site lê. */
    const val DADOS_DO_SITE = "https://gfvdata-web.github.io/page-bolao-formula1/data/"

    /** API pública dos Releases (aviso de nova versão, 9f). */
    const val RELEASES = "https://api.github.com/repos/gfvdata-web/page-bolao-formula1/releases?per_page=20"
}

/**
 * Contêiner de dependências manual (sem Hilt na v1): cria cada peça uma vez e
 * entrega para as telas. Nos testes, as peças são montadas à mão com dublês.
 */
class AppContainer(
    contexto: Context,
    urlDosDados: HttpUrl = Enderecos.DADOS_DO_SITE.toHttpUrl(),
    urlDosReleases: HttpUrl = Enderecos.RELEASES.toHttpUrl(),
) {
    private val contextoDoApp = contexto.applicationContext

    val clienteHttp: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    val temporadaRepositorio = TemporadaRepositorio(
        fonte = FonteRemota(clienteHttp, urlDosDados),
        cache = CacheDeArquivos(File(contexto.filesDir, "dados-do-site")),
    )

    /** URL e chave do envio, guardadas no aparelho (criado só quando usado: um DataStore por arquivo). */
    val configuracoes: Configuracoes by lazy {
        ConfiguracoesNoAparelho(
            PreferenceDataStoreFactory.create { contextoDoApp.preferencesDataStoreFile("configuracoes") },
        )
    }

    val envio: EnviaPalpite = EnvioPeloAppsScript(clienteHttp)

    val verificadorDeAtualizacao = VerificadorDeAtualizacao(clienteHttp, urlDosReleases)
}

/** Os testes trocam o contêiner (ex.: site local) sobrescrevendo [criarContainer]. */
open class BolaoApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = criarContainer()
    }

    protected open fun criarContainer(): AppContainer = AppContainer(this)
}
