package io.github.gfvdataweb.bolaof1.data

import io.github.gfvdataweb.bolaof1.data.modelo.Classificacao
import io.github.gfvdataweb.bolaof1.data.modelo.HallOfFame
import io.github.gfvdataweb.bolaof1.data.modelo.Temporadas
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerializationException
import kotlinx.serialization.decodeFromString
import java.io.IOException

/** O que a aba Hall of Fame precisa: o pódio de cada ano e o ranking final de todas as temporadas. */
data class Historico(
    /** Temporada atual do site (`seasons.json`): ainda sem pódio. */
    val atual: Int,
    /** Ranking final (`standings.json`) de cada ano publicado. */
    val classificacoes: Map<Int, Classificacao>,
    val hall: HallOfFame,
)

/**
 * Histórico de todas as temporadas, com a mesma regra do [TemporadaRepositorio]:
 * entrega o cache na hora, baixa tudo de novo e só troca o cache quando todos os
 * arquivos chegaram e foram lidos sem erro. Usa a mesma fonte e o mesmo cache.
 */
class HistoricoRepositorio(
    private val fonte: FonteRemota,
    private val cache: CacheDeArquivos,
    private val relogio: () -> Long = System::currentTimeMillis,
    private val io: CoroutineDispatcher = Dispatchers.IO,
) {
    fun observar(): Flow<EstadoDados<Historico>> = flow {
        val guardado = withContext(io) { lerDoCache() }
        emit(EstadoDados(guardado?.first, guardado?.second, atualizando = true, erro = null))

        // O emit fica fora do try: exceções de quem coleta não podem ser engolidas aqui.
        val estado = try {
            val (historico, baixadoEm) = withContext(io) { baixarESalvar() }
            EstadoDados(historico, baixadoEm, atualizando = false, erro = null)
        } catch (e: CancellationException) {
            throw e
        } catch (e: IOException) {
            EstadoDados(guardado?.first, guardado?.second, atualizando = false, erro = ErroDeDados.FALHA_NO_DOWNLOAD)
        } catch (e: SerializationException) {
            EstadoDados(guardado?.first, guardado?.second, atualizando = false, erro = ErroDeDados.FORMATO_INESPERADO)
        } catch (e: IllegalArgumentException) {
            EstadoDados(guardado?.first, guardado?.second, atualizando = false, erro = ErroDeDados.FORMATO_INESPERADO)
        }
        emit(estado)
    }

    private fun lerDoCache(): Pair<Historico, Long>? = try {
        val textos = mutableMapOf<String, String>()
        var maisAntigo = Long.MAX_VALUE
        val ler = { caminho: String ->
            val guardado = cache.ler(caminho) ?: throw NoSuchElementException(caminho)
            maisAntigo = minOf(maisAntigo, guardado.salvoEm)
            textos[caminho] = guardado.texto
            guardado.texto
        }
        val anos = TemporadaRepositorio.json.decodeFromString<Temporadas>(ler(TemporadaRepositorio.SEASONS)).temporadas.map { it.ano }
        ler(HALL_OF_FAME)
        anos.forEach { ler(caminhoDoRanking(it)) }
        montar(textos) to maisAntigo
    } catch (e: NoSuchElementException) {
        null // cache incompleto: ainda não houve um download completo
    } catch (e: SerializationException) {
        null
    } catch (e: IllegalArgumentException) {
        null
    }

    private suspend fun baixarESalvar(): Pair<Historico, Long> = coroutineScope {
        val textoSeasons = fonte.baixarTexto(TemporadaRepositorio.SEASONS)
        val anos = TemporadaRepositorio.json.decodeFromString<Temporadas>(textoSeasons).temporadas.map { it.ano }
        val caminhos = listOf(HALL_OF_FAME) + anos.map { caminhoDoRanking(it) }
        val baixados = caminhos.map { caminho -> async { caminho to fonte.baixarTexto(caminho) } }
        val textos = mapOf(TemporadaRepositorio.SEASONS to textoSeasons) + baixados.map { it.await() }
        val historico = montar(textos) // valida tudo antes de mexer no cache
        val agora = relogio()
        textos.forEach { (caminho, texto) -> cache.salvar(caminho, texto, agora) }
        historico to agora
    }

    companion object {
        const val HALL_OF_FAME = "hall_of_fame.json"

        fun caminhoDoRanking(ano: Int) = "$ano/${TemporadaRepositorio.STANDINGS}"

        /** Lê e confere o conjunto de textos (caminho → JSON) do histórico. */
        internal fun montar(textos: Map<String, String>): Historico {
            val json = TemporadaRepositorio.json
            val temporadas = json.decodeFromString<Temporadas>(textos.getValue(TemporadaRepositorio.SEASONS))
            return Historico(
                atual = temporadas.atual,
                classificacoes = temporadas.temporadas.associate { info ->
                    info.ano to json.decodeFromString<Classificacao>(textos.getValue(caminhoDoRanking(info.ano)))
                },
                hall = json.decodeFromString(textos.getValue(HALL_OF_FAME)),
            )
        }
    }
}
