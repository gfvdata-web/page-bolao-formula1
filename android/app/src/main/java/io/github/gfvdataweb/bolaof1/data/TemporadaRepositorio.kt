package io.github.gfvdataweb.bolaof1.data

import io.github.gfvdataweb.bolaof1.data.modelo.Calendario
import io.github.gfvdataweb.bolaof1.data.modelo.Classificacao
import io.github.gfvdataweb.bolaof1.data.modelo.EquipesDoAno
import io.github.gfvdataweb.bolaof1.data.modelo.InfoTemporada
import io.github.gfvdataweb.bolaof1.data.modelo.Palpites
import io.github.gfvdataweb.bolaof1.data.modelo.Resultados
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
import kotlinx.serialization.json.Json
import java.io.IOException

/** Tudo o que as telas de uma temporada precisam, já lido e conferido. */
data class Temporada(
    val ano: Int,
    /** Temporada atual do site (`seasons.json`); [ano] menor que ela = temporada passada. */
    val atual: Int,
    /** Anos publicados, do mais novo para o mais antigo. */
    val anos: List<Int>,
    val info: InfoTemporada?,
    val classificacao: Classificacao,
    val resultados: Resultados,
    val palpites: Palpites,
    val calendario: Calendario,
    val equipes: EquipesDoAno,
)

/** O que a tela mostra: dados (talvez do cache), idade deles e situação da atualização. */
data class EstadoDados<T>(
    val dados: T?,
    /** Quando os dados exibidos foram baixados (epoch ms); null se não há dados. */
    val atualizadoEm: Long?,
    val atualizando: Boolean,
    val erro: ErroDeDados?,
)

/** Por que a atualização falhou: sem internet/site fora do ar, ou JSON que o app não entende. */
enum class ErroDeDados { FALHA_NO_DOWNLOAD, FORMATO_INESPERADO }

/**
 * Dados de uma temporada (por padrão a atual) com *stale-while-revalidate*: entrega o cache na
 * hora e depois tenta baixar tudo de novo. O cache só é substituído quando
 * **todos** os arquivos chegaram e foram lidos sem erro — um JSON quebrado no
 * site nunca apaga o último conjunto bom. Temporada passada com cache completo
 * não é baixada de novo (os dados de um ano fechado não mudam).
 */
class TemporadaRepositorio(
    private val fonte: FonteRemota,
    private val cache: CacheDeArquivos,
    private val relogio: () -> Long = System::currentTimeMillis,
    private val io: CoroutineDispatcher = Dispatchers.IO,
) {
    /** [ano] null = a temporada atual de `seasons.json`. */
    fun observar(ano: Int? = null): Flow<EstadoDados<Temporada>> = flow {
        val guardado = withContext(io) { lerDoCache(ano) }
        if (ano != null && guardado != null && ano < guardado.first.atual) {
            emit(EstadoDados(guardado.first, guardado.second, atualizando = false, erro = null))
            return@flow
        }
        emit(EstadoDados(guardado?.first, guardado?.second, atualizando = true, erro = null))

        // O emit fica fora do try: exceções de quem coleta não podem ser engolidas aqui.
        val estado = try {
            val (temporada, baixadoEm) = withContext(io) { baixarESalvar(ano) }
            EstadoDados(temporada, baixadoEm, atualizando = false, erro = null)
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

    private fun lerDoCache(anoPedido: Int?): Pair<Temporada, Long>? = try {
        val textos = mutableMapOf<String, String>()
        var maisAntigo = Long.MAX_VALUE
        val ler = { caminho: String ->
            val guardado = cache.ler(caminho) ?: throw NoSuchElementException(caminho)
            maisAntigo = minOf(maisAntigo, guardado.salvoEm)
            textos[caminho] = guardado.texto
            guardado.texto
        }
        val temporadas = json.decodeFromString<Temporadas>(ler(SEASONS))
        val ano = anoPedido ?: temporadas.atual
        caminhosDoAno(ano).forEach { ler(it) }
        ler(EQUIPES)
        montar(textos, ano) to maisAntigo
    } catch (e: NoSuchElementException) {
        null // cache incompleto: ainda não houve um download completo
    } catch (e: SerializationException) {
        null
    } catch (e: IllegalArgumentException) {
        null
    }

    private suspend fun baixarESalvar(anoPedido: Int?): Pair<Temporada, Long> = coroutineScope {
        val textoSeasons = fonte.baixarTexto(SEASONS)
        val ano = anoPedido ?: json.decodeFromString<Temporadas>(textoSeasons).atual
        val caminhos = caminhosDoAno(ano) + EQUIPES
        val baixados = caminhos.map { caminho -> async { caminho to fonte.baixarTexto(caminho) } }
        val textos = mapOf(SEASONS to textoSeasons) + baixados.map { it.await() }
        val temporada = montar(textos, ano) // valida tudo antes de mexer no cache
        val agora = relogio()
        textos.forEach { (caminho, texto) -> cache.salvar(caminho, texto, agora) }
        temporada to agora
    }

    companion object {
        /** Campos novos nos JSONs do site não podem quebrar o app. */
        val json = Json { ignoreUnknownKeys = true }

        const val SEASONS = "seasons.json"
        const val EQUIPES = "equipes.json"
        const val STANDINGS = "standings.json"
        const val RESULTS = "results.json"
        const val BETS = "bets.json"
        const val CALENDAR = "calendar.json"

        /** Lê e confere o conjunto de textos (caminho → JSON) de uma temporada ([anoPedido] null = a atual). */
        internal fun montar(textos: Map<String, String>, anoPedido: Int? = null): Temporada {
            val temporadas = json.decodeFromString<Temporadas>(textos.getValue(SEASONS))
            val ano = anoPedido ?: temporadas.atual
            val equipesPorAno = json.decodeFromString<Map<String, EquipesDoAno>>(textos.getValue(EQUIPES))
            return Temporada(
                ano = ano,
                atual = temporadas.atual,
                anos = temporadas.temporadas.map { it.ano }.sortedDescending(),
                info = temporadas.temporadas.firstOrNull { it.ano == ano },
                classificacao = json.decodeFromString(textos.getValue("$ano/$STANDINGS")),
                resultados = json.decodeFromString(textos.getValue("$ano/$RESULTS")),
                palpites = json.decodeFromString(textos.getValue("$ano/$BETS")),
                calendario = json.decodeFromString(textos.getValue("$ano/$CALENDAR")),
                equipes = equipesPorAno[ano.toString()] ?: EquipesDoAno(),
            )
        }

        fun caminhosDoAno(ano: Int) = listOf(STANDINGS, RESULTS, BETS, CALENDAR).map { "$ano/$it" }
    }
}
