package io.github.gfvdataweb.bolaof1.data

import io.github.gfvdataweb.bolaof1.data.modelo.SitePipeline
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * Andamento do pipeline do bolão, lido do `status.json` público do painel-status.
 * Sem cache: é um retrato do momento (o app só mostra com internet). Falhas
 * sobem como [java.io.IOException] (rede/HTTP) ou [SerializationException]
 * (JSON que o app não entende ou sem o card do Bolão F1).
 */
class PipelineRepositorio(
    private val fonte: FonteRemota,
    private val io: CoroutineDispatcher = Dispatchers.IO,
) {
    suspend fun carregar(): SitePipeline = withContext(io) {
        extrairDoBolao(fonte.baixarTexto(CAMINHO))
    }

    companion object {
        /** Relativo à raiz do painel. */
        const val CAMINHO = "dados/status.json"
        const val SLUG = "bolao_f1"

        /**
         * Acha o card do Bolão F1 em `sites` e lê só ele: os formatos dos outros
         * sites não podem derrubar o app.
         */
        fun extrairDoBolao(texto: String): SitePipeline {
            val json = TemporadaRepositorio.json
            val card = try {
                json.parseToJsonElement(texto).jsonObject["sites"]?.jsonArray
                    ?.firstOrNull { it.jsonObject["slug"]?.jsonPrimitive?.content == SLUG }
            } catch (e: IllegalArgumentException) {
                throw SerializationException("status.json inesperado", e)
            }
            return json.decodeFromJsonElement(SitePipeline.serializer(), card ?: throw SerializationException("Sem o card $SLUG"))
        }
    }
}
