package io.github.gfvdataweb.bolaof1.ui.temporada

import io.github.gfvdataweb.bolaof1.data.Temporada
import io.github.gfvdataweb.bolaof1.data.modelo.ResultadoRodada
import io.github.gfvdataweb.bolaof1.data.modelo.Rodada

// Transforma os dados da temporada no que cada tela mostra. Funções puras (sem
// Android): as regras de exibição ficam testadas em JVM puro. Ordenação de
// jogadores igual à do site: pontos desc, depois player_id asc.

data class LinhaRanking(
    val posicao: Int,
    val id: String,
    val nome: String,
    val total: Int,
    val media: Double,
    val rodadasJogadas: Int,
    val pontosCompensacao: Int,
)

fun linhasDoRanking(temporada: Temporada): List<LinhaRanking> =
    temporada.classificacao.jogadores.map {
        LinhaRanking(it.posicao, it.id, it.nome, it.total, it.media, it.rodadasJogadas, it.pontosCompensacao)
    }

/** Piloto com a cor da equipe (#RRGGBB). [posicao] é null se ele não aparece no grid. */
data class PilotoNoGrid(val posicao: Int?, val codigo: String, val corHex: String?)

data class PontosNaRodada(val id: String, val nome: String, val pontos: Int, val compensado: Boolean)

data class CartaoCorrida(
    val numero: Int,
    val corrida: String,
    val data: String,
    val sprint: Boolean,
    val topN: List<PilotoNoGrid>,
    val pilotoDaRodada: PilotoNoGrid?,
    val pontos: List<PontosNaRodada>,
)

/** Uma entrada por rodada pontuada, da mais recente para a mais antiga. */
fun cartoesDasCorridas(temporada: Temporada): List<CartaoCorrida> {
    val topN = temporada.classificacao.formato.topN
    return temporada.classificacao.rodadas
        .sortedByDescending { it.numero }
        .map { rodada ->
            val grid = gridDaRodada(temporada, temporada.resultados.rodadas[rodada.numero.toString()])
            CartaoCorrida(
                numero = rodada.numero,
                corrida = rodada.corrida,
                data = rodada.data,
                sprint = rodada.sprint,
                topN = grid.take(topN),
                pilotoDaRodada = rodada.pilotoDaRodada?.let { codigo ->
                    grid.firstOrNull { it.codigo == codigo } ?: PilotoNoGrid(null, codigo, temporada.equipes.corDoPiloto(codigo))
                },
                pontos = pontosDaRodada(temporada, rodada),
            )
        }
}

/**
 * Pontos de cada jogador na rodada. Quem não apostou mas tem a rodada
 * compensada recebe a pontuação mínima dela ([PontosNaRodada.compensado]).
 */
fun pontosDaRodada(temporada: Temporada, rodada: Rodada): List<PontosNaRodada> =
    temporada.classificacao.jogadores
        .mapNotNull { jogador ->
            val apostado = jogador.pontosPorRodada[rodada.numero.toString()]
            when {
                apostado != null -> PontosNaRodada(jogador.id, jogador.nome, apostado, compensado = false)
                rodada.numero in jogador.rodadasCompensadas ->
                    PontosNaRodada(jogador.id, jogador.nome, rodada.pontuacaoMinima, compensado = true)
                else -> null
            }
        }
        .sortedWith(compareByDescending<PontosNaRodada> { it.pontos }.thenBy { it.id })

data class ItemExibido(val posicao: Int, val codigo: String, val pontos: Int, val corHex: String?)

data class PalpiteExibido(
    val id: String,
    val nome: String,
    val total: Int,
    val itens: List<ItemExibido>,
    val chuteBonus: Int?,
    val posicaoRealBonus: Int?,
    val pontosBonus: Int,
)

data class RodadaDosPalpites(
    val numero: Int,
    val corrida: String,
    val data: String,
    val temBonus: Boolean,
    val pilotoDaRodada: String?,
    val resultado: List<PilotoNoGrid>,
    val palpites: List<PalpiteExibido>,
)

/** Números das rodadas pontuadas, da mais recente para a mais antiga. */
fun rodadasPontuadas(temporada: Temporada): List<Int> =
    temporada.classificacao.rodadas.map { it.numero }.sortedDescending()

fun palpitesDaRodada(temporada: Temporada, numero: Int): RodadaDosPalpites? {
    val rodada = temporada.classificacao.rodadas.firstOrNull { it.numero == numero } ?: return null
    val chave = numero.toString()
    val resultado = temporada.resultados.rodadas[chave]
    val palpites = temporada.palpites.jogadores.values
        .mapNotNull { jogador ->
            val palpite = jogador.rodadas[chave] ?: return@mapNotNull null
            PalpiteExibido(
                id = jogador.id,
                nome = jogador.nome,
                total = palpite.total,
                itens = palpite.itens.map { item ->
                    ItemExibido(item.posicao, item.chute, item.pontos, corNaRodada(temporada, resultado, item.chute))
                },
                chuteBonus = palpite.chuteBonus,
                posicaoRealBonus = palpite.posicaoRealBonus,
                pontosBonus = palpite.pontosBonus,
            )
        }
        .sortedWith(compareByDescending<PalpiteExibido> { it.total }.thenBy { it.id })
    return RodadaDosPalpites(
        numero = numero,
        corrida = rodada.corrida,
        data = rodada.data,
        temBonus = temporada.classificacao.formato.bonus,
        pilotoDaRodada = rodada.pilotoDaRodada,
        resultado = gridDaRodada(temporada, resultado).take(temporada.classificacao.formato.topN),
        palpites = palpites,
    )
}

private fun gridDaRodada(temporada: Temporada, resultado: ResultadoRodada?): List<PilotoNoGrid> =
    resultado?.grid.orEmpty().mapIndexed { indice, codigo ->
        PilotoNoGrid(indice + 1, codigo, corNaRodada(temporada, resultado, codigo))
    }

/** Cor da equipe do piloto naquela rodada; sem a informação, a equipe principal do ano. */
private fun corNaRodada(temporada: Temporada, resultado: ResultadoRodada?, codigo: String): String? =
    resultado?.equipes?.get(codigo)?.let { temporada.equipes.equipes[it]?.cor }
        ?: temporada.equipes.corDoPiloto(codigo)
