package io.github.gfvdataweb.bolaof1.data

import okhttp3.HttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException

/**
 * Baixa os JSONs publicados pelo site (GitHub Pages). Chamada bloqueante:
 * quem usa roda fora da thread principal (ver [TemporadaRepositorio]).
 */
class FonteRemota(
    private val cliente: OkHttpClient,
    private val base: HttpUrl,
) {
    /** [caminho] relativo a `docs/data/`, ex.: `2026/standings.json`. */
    fun baixarTexto(caminho: String): String {
        val url = base.resolve(caminho) ?: throw IOException("Caminho inválido: $caminho")
        cliente.newCall(Request.Builder().url(url).build()).execute().use { resposta ->
            if (!resposta.isSuccessful) {
                throw IOException("O site respondeu ${resposta.code} para $caminho")
            }
            return resposta.body.string()
        }
    }
}
