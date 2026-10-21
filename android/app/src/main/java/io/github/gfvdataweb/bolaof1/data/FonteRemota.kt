package io.github.gfvdataweb.bolaof1.data

import okhttp3.HttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException

/**
 * Baixa os JSONs publicados pelo site. Chamada bloqueante: quem usa roda fora
 * da thread principal (ver [TemporadaRepositorio]). Se a [base] falhar (rede ou
 * resposta de erro), tenta a [reserva] com o mesmo caminho; se as duas falharem,
 * vale o erro da [base].
 */
class FonteRemota(
    private val cliente: OkHttpClient,
    private val base: HttpUrl,
    private val reserva: HttpUrl? = null,
) {
    /** [caminho] relativo a `docs/data/`, ex.: `2026/standings.json`. */
    fun baixarTexto(caminho: String): String {
        try {
            return baixar(base, caminho)
        } catch (falha: IOException) {
            if (reserva == null) throw falha
            try {
                return baixar(reserva, caminho)
            } catch (outra: IOException) {
                falha.addSuppressed(outra)
                throw falha
            }
        }
    }

    private fun baixar(raiz: HttpUrl, caminho: String): String {
        val url = raiz.resolve(caminho) ?: throw IOException("Caminho inválido: $caminho")
        cliente.newCall(Request.Builder().url(url).build()).execute().use { resposta ->
            if (!resposta.isSuccessful) {
                throw IOException("O site respondeu ${resposta.code} para $caminho")
            }
            return resposta.body.string()
        }
    }
}
