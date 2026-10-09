package io.github.gfvdataweb.bolaof1.data

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerializationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException

sealed interface ResultadoDoEnvio {
    /** O Apps Script aceitou e disparou o pipeline. */
    data object Enviado : ResultadoDoEnvio

    /** O Apps Script respondeu que não (chave errada, texto vazio, falha no GitHub…). */
    data class Recusado(val motivo: String) : ResultadoDoEnvio

    /** Sem resposta (internet). O palpite pode ou não ter chegado. */
    data object FalhaDeRede : ResultadoDoEnvio

    /** Resposta que não é o JSON esperado (ex.: página de login do Google). */
    data object RespostaInesperada : ResultadoDoEnvio

    /** URL ou chave ainda não configuradas. */
    data object NaoConfigurado : ResultadoDoEnvio
}

fun interface EnviaPalpite {
    suspend fun enviar(configuracoes: ConfiguracoesDeEnvio, texto: String, rodada: Int?): ResultadoDoEnvio
}

/** Corpo do POST: o `doPost` do Code.gs repassa `texto`/`round` ao pipeline. */
@Serializable
internal data class PedidoDeEnvio(val chave: String, val texto: String, val round: Int? = null)

@Serializable
internal data class RespostaDoEnvio(val ok: Boolean, val erro: String? = null)

/**
 * Envia o palpite para o `doPost` do Apps Script (Etapa 9e). O Google
 * responde ao POST com um redirect 302 para `script.googleusercontent.com`;
 * o script já rodou nesse ponto, e o OkHttp segue o redirect (com GET) para
 * ler a resposta JSON.
 */
class EnvioPeloAppsScript(
    private val cliente: OkHttpClient,
    private val io: CoroutineDispatcher = Dispatchers.IO,
) : EnviaPalpite {

    override suspend fun enviar(configuracoes: ConfiguracoesDeEnvio, texto: String, rodada: Int?): ResultadoDoEnvio {
        // A exigência de https fica na tela de Configurações (urlValida); aqui
        // basta a URL fazer sentido, o que permite testar com um servidor local.
        if (configuracoes.chave.isBlank()) return ResultadoDoEnvio.NaoConfigurado
        val url = configuracoes.url.trim().toHttpUrlOrNull() ?: return ResultadoDoEnvio.NaoConfigurado
        val corpo = json.encodeToString(PedidoDeEnvio(configuracoes.chave.trim(), texto, rodada))
        val pedido = Request.Builder()
            .url(url)
            .post(corpo.toRequestBody("application/json; charset=utf-8".toMediaType()))
            .build()
        return withContext(io) {
            try {
                cliente.newCall(pedido).execute().use { resposta ->
                    val lida = try {
                        json.decodeFromString<RespostaDoEnvio>(resposta.body.string())
                    } catch (e: SerializationException) {
                        null
                    } catch (e: IllegalArgumentException) {
                        null
                    }
                    when {
                        lida == null -> ResultadoDoEnvio.RespostaInesperada
                        lida.ok -> ResultadoDoEnvio.Enviado
                        else -> ResultadoDoEnvio.Recusado(lida.erro ?: "sem motivo informado")
                    }
                }
            } catch (e: IOException) {
                ResultadoDoEnvio.FalhaDeRede
            }
        }
    }

    private companion object {
        val json = Json { ignoreUnknownKeys = true }
    }
}
