package io.github.gfvdataweb.bolaof1.data

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

/**
 * Para onde e com que chave o app envia palpites. Digitadas uma vez na tela
 * de Configurações e guardadas só no aparelho: nada disso vai dentro do APK,
 * então o mesmo APK serve para quem só consulta.
 */
data class ConfiguracoesDeEnvio(val url: String = "", val chave: String = "") {
    /** URL https do app da web do Apps Script. */
    val urlValida: Boolean get() = url.trim().toHttpUrlOrNull()?.isHttps == true
    val completas: Boolean get() = urlValida && chave.isNotBlank()
}

interface Configuracoes {
    val atuais: Flow<ConfiguracoesDeEnvio>
    suspend fun salvar(novas: ConfiguracoesDeEnvio)
}

/** [Configuracoes] guardadas no DataStore do app (sem backup: ver manifest). */
class ConfiguracoesNoAparelho(private val dataStore: DataStore<Preferences>) : Configuracoes {

    override val atuais: Flow<ConfiguracoesDeEnvio> = dataStore.data.map {
        ConfiguracoesDeEnvio(url = it[URL] ?: "", chave = it[CHAVE] ?: "")
    }

    override suspend fun salvar(novas: ConfiguracoesDeEnvio) {
        dataStore.edit {
            it[URL] = novas.url.trim()
            it[CHAVE] = novas.chave.trim()
        }
    }

    private companion object {
        val URL = stringPreferencesKey("envio_url")
        val CHAVE = stringPreferencesKey("envio_chave")
    }
}
